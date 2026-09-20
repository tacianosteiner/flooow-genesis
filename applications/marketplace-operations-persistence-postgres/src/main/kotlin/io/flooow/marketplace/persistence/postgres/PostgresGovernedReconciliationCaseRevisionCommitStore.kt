package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.reconciliation.DurableReconciliationCase
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessment
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentFingerprint
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentSnapshot
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentSnapshotCodec
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicyVersion
import io.flooow.marketplace.operations.economics.reconciliation.GovernedReconciliationCaseCommitFailure
import io.flooow.marketplace.operations.economics.reconciliation.GovernedReconciliationCaseCommitResult
import io.flooow.marketplace.operations.economics.reconciliation.GovernedReconciliationCaseRevisionCommit
import io.flooow.marketplace.operations.economics.reconciliation.GovernedReconciliationCaseRevisionCommitStore
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseId
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseStageDifference
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseStatus
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.ResultSet
import java.sql.SQLException
import java.sql.Timestamp
import java.sql.Types
import java.time.Instant
import java.util.UUID
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject

/**
 * Atomic durable commit boundary for governed reconciliation-case revisions.
 *
 * This store never derives assessment identity. It receives a command whose
 * authority and exact snapshot were established by the application domain,
 * verifies any existing durable lineage before idempotence, serializes
 * existing revisions with SELECT ... FOR UPDATE, performs a revision CAS,
 * and commits case + lineage in one JDBC transaction.
 */
class PostgresGovernedReconciliationCaseRevisionCommitStore(
    private val configuration: PostgresConfiguration
) : GovernedReconciliationCaseRevisionCommitStore {

    override fun commit(
        command: GovernedReconciliationCaseRevisionCommit
    ): GovernedReconciliationCaseCommitResult {
        val connection = try {
            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            )
        } catch (_: SQLException) {
            return unavailable()
        }

        return try {
            connection.use { currentConnection ->
                try {
                    currentConnection.autoCommit = false

                    verifyCommand(command)

                    val result =
                        commitWithinTransaction(
                            currentConnection,
                            command
                        )

                    when (result) {
                        is GovernedReconciliationCaseCommitResult.Applied,
                        is GovernedReconciliationCaseCommitResult.AlreadyApplied ->
                            currentConnection.commit()

                        is GovernedReconciliationCaseCommitResult.Failed ->
                            currentConnection.rollback()
                    }

                    result
                } catch (_: PersistedIntegrityException) {
                    safeRollback(currentConnection)
                    integrityFailure()
                } catch (failure: SQLException) {
                    safeRollback(currentConnection)
                    GovernedReconciliationCaseCommitResult.Failed(
                        mapSqlFailure(failure)
                    )
                }
            }
        } catch (_: SQLException) {
            unavailable()
        }
    }

    private fun commitWithinTransaction(
        connection: Connection,
        command: GovernedReconciliationCaseRevisionCommit
    ): GovernedReconciliationCaseCommitResult {
        val organizationId = command.caseValue.organizationId
        val caseId = command.caseValue.caseId

        val current =
            lockCurrentCase(
                connection,
                organizationId,
                caseId
            )

        if (current != null) {
            return commitAgainstCurrent(
                connection,
                command,
                current
            )
        }

        if (!isValidFirstRevision(command)) {
            return conflict()
        }

        val inserted =
            insertCaseIfAbsent(
                connection,
                command.caseValue
            )

        if (inserted == 1) {
            insertLineage(connection, command)

            return GovernedReconciliationCaseCommitResult.Applied(
                command.caseValue.revision
            )
        }

        val raced =
            lockCurrentCase(
                connection,
                organizationId,
                caseId
            )

        if (raced == null) {
            throw PersistedIntegrityException(
                "Case identity conflict did not resolve to deterministic case"
            )
        }

        return commitAgainstCurrent(
            connection,
            command,
            raced
        )
    }

    private fun commitAgainstCurrent(
        connection: Connection,
        command: GovernedReconciliationCaseRevisionCommit,
        current: CurrentCase
    ): GovernedReconciliationCaseCommitResult {
        verifyCurrentContext(current, command)

        val lineage =
            readVerifiedCurrentLineage(
                connection,
                current
            )

        if (lineage != null) {
            val incomingFingerprint =
                command.acceptedAssessment.assessmentFingerprint

            if (lineage.fingerprint == incomingFingerprint) {
                if (
                    lineage.assessment !=
                    command.acceptedAssessment.assessment
                ) {
                    throw PersistedIntegrityException(
                        "Matching fingerprint resolved to different semantic snapshot"
                    )
                }

                return GovernedReconciliationCaseCommitResult.AlreadyApplied(
                    current.revision
                )
            }
        }

        val expectedRevision = current.revision + 1

        if (command.caseValue.revision != expectedRevision) {
            return conflict()
        }

        if (
            command.caseValue.openedAt != current.openedAt ||
            command.caseValue.status != current.status ||
            command.caseValue.resolvedAt != current.resolvedAt
        ) {
            return conflict()
        }

        if (
            command.acceptedAssessment.acceptedAt <
            current.lastObservedAt
        ) {
            return conflict()
        }

        val updated =
            updateCaseWithCas(
                connection,
                command.caseValue,
                expectedCurrentRevision = current.revision
            )

        if (updated != 1) {
            return conflict()
        }

        insertLineage(connection, command)

        return GovernedReconciliationCaseCommitResult.Applied(
            command.caseValue.revision
        )
    }

    private fun verifyCommand(
        command: GovernedReconciliationCaseRevisionCommit
    ) {
        try {
            val verified =
                FinancialReconciliationAssessmentSnapshotCodec.verify(
                    command.assessmentSnapshot,
                    command.acceptedAssessment.assessmentFingerprint
                )

            if (
                verified.assessment !=
                command.acceptedAssessment.assessment
            ) {
                throw PersistedIntegrityException(
                    "Command snapshot differs from accepted assessment"
                )
            }
        } catch (failure: PersistedIntegrityException) {
            throw failure
        } catch (failure: RuntimeException) {
            throw PersistedIntegrityException(
                "Command assessment identity is invalid",
                failure
            )
        }
    }

    private fun isValidFirstRevision(
        command: GovernedReconciliationCaseRevisionCommit
    ): Boolean =
        command.caseValue.revision == 1L &&
            command.caseValue.openedAt ==
                command.acceptedAssessment.acceptedAt &&
            command.caseValue.status ==
                ReconciliationCaseStatus.OPEN &&
            command.caseValue.resolvedAt == null

    private fun verifyCurrentContext(
        current: CurrentCase,
        command: GovernedReconciliationCaseRevisionCommit
    ) {
        val value = command.caseValue

        if (
            current.organizationId != value.organizationId ||
            current.caseId != value.caseId ||
            current.orderId != value.orderId ||
            current.traceId != value.traceId ||
            current.policyVersion != value.policyVersion ||
            current.currency != value.currency
        ) {
            throw PersistedIntegrityException(
                "Persisted case context differs from governed command"
            )
        }
    }

    /**
     * Returns null only for an intentionally legacy current revision.
     * A present lineage is fully verified before any idempotence decision.
     */
    private fun readVerifiedCurrentLineage(
        connection: Connection,
        current: CurrentCase
    ): VerifiedCurrentLineage? =
        connection.prepareStatement(CURRENT_LINEAGE_SQL).use { statement ->
            statement.setObject(
                1,
                current.organizationId.value
            )
            statement.setObject(
                2,
                current.caseId.valueForPersistence()
            )
            statement.setLong(
                3,
                current.revision
            )

            statement.executeQuery().use { result ->
                if (!result.next()) {
                    return@use null
                }

                try {
                    val fingerprint =
                        FinancialReconciliationAssessmentFingerprint
                            .parsePersisted(
                                result.getInt(
                                    "assessment_fingerprint_version"
                                ),
                                result.getString(
                                    "assessment_fingerprint"
                                )
                            )

                    val snapshot =
                        FinancialReconciliationAssessmentSnapshot.parse(
                            result.getInt(
                                "assessment_snapshot_schema_version"
                            ),
                            result.getString(
                                "assessment_snapshot"
                            )
                        )

                    val verified =
                        FinancialReconciliationAssessmentSnapshotCodec
                            .verify(
                                snapshot,
                                fingerprint
                            )

                    val acceptedAt =
                        result.getTimestamp(
                            "accepted_at"
                        ).toInstant()

                    verifyPersistedLineageContext(
                        current,
                        verified.assessment,
                        acceptedAt
                    )

                    verifyCurrentProjection(
                        current,
                        verified.assessment
                    )

                    VerifiedCurrentLineage(
                        fingerprint =
                            fingerprint,
                        assessment =
                            verified.assessment
                    )
                } catch (failure: PersistedIntegrityException) {
                    throw failure
                } catch (failure: RuntimeException) {
                    throw PersistedIntegrityException(
                        "Persisted current lineage failed verification",
                        failure
                    )
                }
            }
        }

    private fun verifyPersistedLineageContext(
        current: CurrentCase,
        assessment: FinancialReconciliationAssessment,
        acceptedAt: Instant
    ) {
        if (
            assessment.organizationId != current.organizationId ||
            assessment.orderId != current.orderId ||
            assessment.traceId != current.traceId ||
            assessment.policyVersion != current.policyVersion ||
            assessment.currency != current.currency ||
            acceptedAt != current.lastObservedAt
        ) {
            throw PersistedIntegrityException(
                "Persisted lineage context does not match current case"
            )
        }
    }

    private fun verifyCurrentProjection(
        current: CurrentCase,
        assessment: FinancialReconciliationAssessment
    ) {
        val expected =
            DurableReconciliationCase.fromAssessment(
                caseId = current.caseId,
                assessment = assessment,
                openedAt = current.openedAt,
                observedAt = current.lastObservedAt,
                revision = current.revision,
                status = current.status,
                resolvedAt = current.resolvedAt
            )

        if (
            current.absoluteDifferenceSummary !=
            expected.absoluteDifferenceSummary
        ) {
            throw PersistedIntegrityException(
                "Current case summary differs from verified assessment"
            )
        }

        if (
            !jsonEquivalent(
                current.stageDetails,
                encodeStages(expected.stages)
            )
        ) {
            throw PersistedIntegrityException(
                "Current case stages differ from verified assessment"
            )
        }

        if (
            !jsonEquivalent(
                current.evidenceEntryIds,
                encodeEvidence(expected.evidenceEntryIds)
            )
        ) {
            throw PersistedIntegrityException(
                "Current case evidence differs from verified assessment"
            )
        }
    }

    private fun lockCurrentCase(
        connection: Connection,
        organizationId: OrganizationId,
        caseId: ReconciliationCaseId
    ): CurrentCase? =
        connection.prepareStatement(LOCK_CURRENT_CASE_SQL).use { statement ->
            statement.setObject(
                1,
                organizationId.value
            )
            statement.setObject(
                2,
                caseId.valueForPersistence()
            )

            statement.executeQuery().use { result ->
                if (result.next()) {
                    result.toCurrentCase()
                } else {
                    null
                }
            }
        }

    private fun insertCaseIfAbsent(
        connection: Connection,
        value: DurableReconciliationCase
    ): Int =
        connection.prepareStatement(INSERT_CASE_SQL).use { statement ->
            bindCase(statement, value)
            statement.executeUpdate()
        }

    private fun updateCaseWithCas(
        connection: Connection,
        value: DurableReconciliationCase,
        expectedCurrentRevision: Long
    ): Int =
        connection.prepareStatement(UPDATE_CASE_CAS_SQL).use { statement ->
            statement.setTimestamp(
                1,
                Timestamp.from(value.lastObservedAt)
            )
            statement.setLong(
                2,
                value.revision
            )
            statement.setBigDecimal(
                3,
                value.absoluteDifferenceSummary.amount
            )
            statement.setString(
                4,
                encodeStages(value.stages)
            )
            statement.setString(
                5,
                encodeEvidence(value.evidenceEntryIds)
            )
            statement.setObject(
                6,
                value.organizationId.value
            )
            statement.setObject(
                7,
                value.caseId.valueForPersistence()
            )
            statement.setLong(
                8,
                expectedCurrentRevision
            )

            statement.executeUpdate()
        }

    private fun insertLineage(
        connection: Connection,
        command: GovernedReconciliationCaseRevisionCommit
    ) {
        val fingerprint =
            command.acceptedAssessment.assessmentFingerprint

        connection.prepareStatement(INSERT_LINEAGE_SQL).use { statement ->
            statement.setObject(
                1,
                command.caseValue.organizationId.value
            )
            statement.setObject(
                2,
                command.caseValue.caseId.valueForPersistence()
            )
            statement.setLong(
                3,
                command.caseValue.revision
            )
            statement.setInt(
                4,
                fingerprint.canonicalizationVersion
            )
            statement.setString(
                5,
                fingerprint.sha256
            )
            statement.setInt(
                6,
                command.assessmentSnapshot.schemaVersion
            )
            statement.setString(
                7,
                command.assessmentSnapshot.json
            )
            statement.setTimestamp(
                8,
                Timestamp.from(
                    command.acceptedAssessment.acceptedAt
                )
            )

            val inserted = statement.executeUpdate()

            if (inserted != 1) {
                throw PersistedIntegrityException(
                    "Assessment lineage insert did not affect exactly one row"
                )
            }
        }
    }

    private fun bindCase(
        statement: java.sql.PreparedStatement,
        value: DurableReconciliationCase
    ) {
        statement.setObject(
            1,
            value.organizationId.value
        )
        statement.setObject(
            2,
            value.caseId.valueForPersistence()
        )
        statement.setObject(
            3,
            value.orderId.value
        )
        statement.setObject(
            4,
            value.traceId.valueForPersistence()
        )
        statement.setString(
            5,
            value.policyVersion.value
        )
        statement.setString(
            6,
            value.currency.code
        )
        statement.setString(
            7,
            value.status.name
        )
        statement.setTimestamp(
            8,
            Timestamp.from(value.openedAt)
        )
        statement.setTimestamp(
            9,
            Timestamp.from(value.lastObservedAt)
        )

        if (value.resolvedAt == null) {
            statement.setNull(
                10,
                Types.TIMESTAMP_WITH_TIMEZONE
            )
        }

        if (value.resolvedAt != null) {
            statement.setTimestamp(
                10,
                Timestamp.from(value.resolvedAt)
            )
        }

        statement.setLong(
            11,
            value.revision
        )
        statement.setBigDecimal(
            12,
            value.absoluteDifferenceSummary.amount
        )
        statement.setString(
            13,
            encodeStages(value.stages)
        )
        statement.setString(
            14,
            encodeEvidence(value.evidenceEntryIds)
        )
    }

    private fun ResultSet.toCurrentCase(): CurrentCase {
        val currency =
            MarketplaceCurrency(
                getString("currency")
            )

        return CurrentCase(
            organizationId =
                OrganizationId(
                    getObject(
                        "organization_id",
                        UUID::class.java
                    )
                ),
            caseId =
                ReconciliationCaseId.of(
                    getObject(
                        "case_id",
                        UUID::class.java
                    )
                ),
            orderId =
                MarketplaceOrderId(
                    getObject(
                        "marketplace_order_id",
                        UUID::class.java
                    )
                ),
            traceId =
                FinancialTraceId.of(
                    getObject(
                        "financial_trace_id",
                        UUID::class.java
                    )
                ),
            policyVersion =
                FinancialReconciliationPolicyVersion(
                    getString("policy_version")
                ),
            currency = currency,
            status =
                ReconciliationCaseStatus.valueOf(
                    getString("status")
                ),
            openedAt =
                getTimestamp(
                    "opened_at"
                ).toInstant(),
            lastObservedAt =
                getTimestamp(
                    "last_observed_at"
                ).toInstant(),
            resolvedAt =
                getTimestamp(
                    "resolved_at"
                )?.toInstant(),
            revision =
                getLong("revision"),
            absoluteDifferenceSummary =
                MarketplaceMoney.parse(
                    currency,
                    getBigDecimal(
                        "absolute_difference_summary"
                    ).toPlainString()
                ),
            stageDetails =
                getString("stage_details"),
            evidenceEntryIds =
                getString("evidence_entry_ids")
        )
    }

    private fun encodeStages(
        stages: List<ReconciliationCaseStageDifference>
    ): String =
        buildJsonArray {
            stages.forEach { stage ->
                add(
                    buildJsonObject {
                        put(
                            "stage",
                            JsonPrimitive(stage.stage.name)
                        )
                        putMoney(
                            "expected",
                            stage.expected
                        )
                        putMoney(
                            "actual",
                            stage.actual
                        )
                        putMoney(
                            "signedDifference",
                            stage.signedDifference
                        )
                        putMoney(
                            "absoluteDifference",
                            stage.absoluteDifference
                        )
                        putMoney(
                            "tolerance",
                            stage.tolerance
                        )
                        put(
                            "expectedEntryIds",
                            buildJsonArray {
                                stage.expectedEntryIds.forEach {
                                    add(
                                        JsonPrimitive(
                                            it.value.toString()
                                        )
                                    )
                                }
                            }
                        )
                        put(
                            "actualEntryIds",
                            buildJsonArray {
                                stage.actualEntryIds.forEach {
                                    add(
                                        JsonPrimitive(
                                            it.value.toString()
                                        )
                                    )
                                }
                            }
                        )
                    }
                )
            }
        }.toString()

    private fun kotlinx.serialization.json.JsonObjectBuilder.putMoney(
        name: String,
        value: MarketplaceMoney?
    ) {
        if (value == null) {
            put(
                name,
                JsonNull
            )
        }

        if (value != null) {
            put(
                name,
                buildJsonObject {
                    put(
                        "currency",
                        JsonPrimitive(
                            value.currency.code
                        )
                    )
                    put(
                        "amount",
                        JsonPrimitive(
                            value.amount.toPlainString()
                        )
                    )
                }
            )
        }
    }

    private fun encodeEvidence(
        values: List<FinancialLedgerEntryId>
    ): String =
        buildJsonArray {
            values.forEach {
                add(
                    JsonPrimitive(
                        it.value.toString()
                    )
                )
            }
        }.toString()

    private fun jsonEquivalent(
        left: String,
        right: String
    ): Boolean =
        Json.parseToJsonElement(left) ==
            Json.parseToJsonElement(right)

    private fun safeRollback(
        connection: Connection
    ) {
        try {
            connection.rollback()
        } catch (_: SQLException) {
            // Original failure classification remains authoritative.
        }
    }

    private fun mapSqlFailure(
        failure: SQLException
    ): GovernedReconciliationCaseCommitFailure {
        val state = failure.sqlState.orEmpty()

        if (
            state == "40001" ||
            state == "40P01" ||
            state == "23505"
        ) {
            return GovernedReconciliationCaseCommitFailure.CONFLICT
        }

        if (
            state == "P0001" ||
            state == "23502" ||
            state == "23503" ||
            state == "23514" ||
            state == "22P02"
        ) {
            return GovernedReconciliationCaseCommitFailure.INTEGRITY_FAILURE
        }

        return GovernedReconciliationCaseCommitFailure.UNAVAILABLE
    }

    private fun conflict():
        GovernedReconciliationCaseCommitResult =
        GovernedReconciliationCaseCommitResult.Failed(
            GovernedReconciliationCaseCommitFailure.CONFLICT
        )

    private fun integrityFailure():
        GovernedReconciliationCaseCommitResult =
        GovernedReconciliationCaseCommitResult.Failed(
            GovernedReconciliationCaseCommitFailure.INTEGRITY_FAILURE
        )

    private fun unavailable():
        GovernedReconciliationCaseCommitResult =
        GovernedReconciliationCaseCommitResult.Failed(
            GovernedReconciliationCaseCommitFailure.UNAVAILABLE
        )

    private data class CurrentCase(
        val organizationId: OrganizationId,
        val caseId: ReconciliationCaseId,
        val orderId: MarketplaceOrderId,
        val traceId: FinancialTraceId,
        val policyVersion: FinancialReconciliationPolicyVersion,
        val currency: MarketplaceCurrency,
        val status: ReconciliationCaseStatus,
        val openedAt: Instant,
        val lastObservedAt: Instant,
        val resolvedAt: Instant?,
        val revision: Long,
        val absoluteDifferenceSummary: MarketplaceMoney,
        val stageDetails: String,
        val evidenceEntryIds: String
    )

    private data class VerifiedCurrentLineage(
        val fingerprint:
            FinancialReconciliationAssessmentFingerprint,
        val assessment:
            FinancialReconciliationAssessment
    )

    private class PersistedIntegrityException(
        message: String,
        cause: Throwable? = null
    ) : RuntimeException(message, cause)

    companion object {
        private const val LOCK_CURRENT_CASE_SQL = """
            SELECT *
              FROM marketplace_reconciliation_case
             WHERE organization_id=?
               AND case_id=?
             FOR UPDATE
        """

        private const val CURRENT_LINEAGE_SQL = """
            SELECT
                assessment_fingerprint_version,
                assessment_fingerprint,
                assessment_snapshot_schema_version,
                assessment_snapshot::text AS assessment_snapshot,
                accepted_at
              FROM marketplace_reconciliation_case_revision_assessment
             WHERE organization_id=?
               AND case_id=?
               AND case_revision=?
        """

        private const val INSERT_CASE_SQL = """
            INSERT INTO marketplace_reconciliation_case
                (
                    organization_id,
                    case_id,
                    marketplace_order_id,
                    financial_trace_id,
                    policy_version,
                    currency,
                    status,
                    opened_at,
                    last_observed_at,
                    resolved_at,
                    revision,
                    absolute_difference_summary,
                    stage_details,
                    evidence_entry_ids
                )
            VALUES
                (
                    ?,?,?,?,?,?,?,?,?,?,?,?,
                    ?::jsonb,
                    ?::jsonb
                )
            ON CONFLICT DO NOTHING
        """

        private const val UPDATE_CASE_CAS_SQL = """
            UPDATE marketplace_reconciliation_case
               SET last_observed_at=?,
                   revision=?,
                   absolute_difference_summary=?,
                   stage_details=?::jsonb,
                   evidence_entry_ids=?::jsonb
             WHERE organization_id=?
               AND case_id=?
               AND revision=?
        """

        private const val INSERT_LINEAGE_SQL = """
            INSERT INTO marketplace_reconciliation_case_revision_assessment
                (
                    organization_id,
                    case_id,
                    case_revision,
                    assessment_fingerprint_version,
                    assessment_fingerprint,
                    assessment_snapshot_schema_version,
                    assessment_snapshot,
                    accepted_at
                )
            VALUES
                (?,?,?,?,?,?,?::jsonb,?)
        """
    }
}
