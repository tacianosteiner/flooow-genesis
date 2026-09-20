package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.EconomicComponent
import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentId
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.EconomicExternalReference
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceAbsenceReason
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceFamily
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.evidence.valueForPersistence
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerAppendRequestId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerAppendResult
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryDraft
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceOpenRequestId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceOpenResult
import io.flooow.marketplace.operations.economics.ledger.OpenFinancialTrace
import io.flooow.marketplace.operations.economics.ledger.materialization.FinancialLedgerComponentStageCompatibility
import io.flooow.marketplace.operations.economics.ledger.materialization.FinancialLedgerMaterializationPolicyVersion
import io.flooow.marketplace.operations.economics.ledger.materialization.FinancialLedgerMaterializationSourceFingerprintV1
import io.flooow.marketplace.operations.economics.ledger.materialization.GovernedFinancialLedgerMaterializationCommitFailure
import io.flooow.marketplace.operations.economics.ledger.materialization.GovernedFinancialLedgerMaterializationCommitResult
import io.flooow.marketplace.operations.economics.ledger.materialization.GovernedFinancialLedgerMaterializationCommitStore
import io.flooow.marketplace.operations.economics.ledger.materialization.VerifiedFinancialLedgerComponentMaterializationPlan
import io.flooow.organization.OrganizationId
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.sql.Connection
import java.sql.DriverManager
import java.sql.ResultSet
import java.sql.SQLException
import java.util.UUID

/**
 * B3-B2B durable commit implementation.
 *
 * The verified B3-A plan is never treated as durable source proof. This store
 * locks and reconstructs the canonical source observation, recomputes its
 * fingerprint, and only then performs trace + entry + lineage in one JDBC
 * transaction.
 *
 * Correction materialization is deliberately not implemented in this slice.
 */
class PostgresGovernedFinancialLedgerMaterializationCommitStore internal constructor(
    private val ledger: PostgresMarketplaceFinancialLedgerRepository,
    private val connectionFactory: () -> Connection
) : GovernedFinancialLedgerMaterializationCommitStore {

    constructor(
        configuration: PostgresConfiguration,
        ledger: PostgresMarketplaceFinancialLedgerRepository =
            PostgresMarketplaceFinancialLedgerRepository(configuration)
    ) : this(
        ledger,
        {
            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            )
        }
    )

    override fun commit(
        plan: VerifiedFinancialLedgerComponentMaterializationPlan
    ): GovernedFinancialLedgerMaterializationCommitResult {
        var provisional: GovernedFinancialLedgerMaterializationCommitResult.Materialized? = null
        var commitAttempted = false

        try {
            connectionFactory().use { connection ->
                connection.autoCommit = false
                try {
                    val outcome = commitWithinTransaction(connection, plan)
                    if (outcome is GovernedFinancialLedgerMaterializationCommitResult.Materialized) {
                        provisional = outcome
                        commitAttempted = true
                        connection.commit()
                        return outcome
                    }
                    connection.rollback()
                    return outcome
                } catch (error: Exception) {
                    try {
                        connection.rollback()
                    } catch (_: Exception) {
                        Unit
                    }
                    if (commitAttempted && provisional != null) {
                        return classifyUncertainCommit(plan, provisional!!)
                    }
                    return classifyFailure(error)
                }
            }
        } catch (error: Exception) {
            if (commitAttempted && provisional != null) {
                return classifyUncertainCommit(plan, provisional!!)
            }
            return classifyFailure(error)
        }
    }

    private fun commitWithinTransaction(
        connection: Connection,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan
    ): GovernedFinancialLedgerMaterializationCommitResult {
        check(!connection.autoCommit) {
            "Governed financial materialization requires autoCommit=false"
        }

        val subject = lockSubject(connection, plan)
            ?: return integrityFailure()

        if (subject != plan.subject) {
            return integrityFailure()
        }

        val observation = loadSourceObservation(connection, plan)
            ?: return integrityFailure()

        if (!planMatchesObservation(plan, observation)) {
            return integrityFailure()
        }

        loadLineage(connection, plan)?.let { lineage ->
            return verifyReplay(connection, plan, observation, lineage)
        }

        if (participatesInCorrection(connection, plan)) {
            return integrityFailure()
        }

        val deterministic = deterministicIdentities(plan)

        val openResult = ledger.openWithinTransaction(
            connection = connection,
            command = OpenFinancialTrace(
                organizationId = plan.subject.organizationId,
                requestId = deterministic.openRequestId,
                orderId = plan.subject.orderId,
                marketplace = plan.subject.marketplace,
                externalOrderId = plan.subject.externalOrderId,
                currency = plan.subject.currency
            ),
            traceId = deterministic.traceId
        )

        val traceId = when (openResult) {
            is FinancialTraceOpenResult.Opened -> openResult.traceId
            is FinancialTraceOpenResult.AlreadyOpen -> openResult.traceId
            is FinancialTraceOpenResult.OrderAlreadyTraced -> openResult.traceId
            FinancialTraceOpenResult.OrganizationUnavailable ->
                return unavailableFailure()
            FinancialTraceOpenResult.Conflict ->
                return conflictFailure()
            FinancialTraceOpenResult.IntegrityFailure ->
                return integrityFailure()
        }

        val appendResult = ledger.appendWithinTransaction(
            connection = connection,
            draft = FinancialLedgerEntryDraft(
                organizationId = plan.subject.organizationId,
                requestId = deterministic.appendRequestId,
                traceId = traceId,
                stage = plan.stage,
                basis = plan.basis,
                direction = plan.direction,
                magnitude = plan.magnitude,
                source = plan.source,
                occurredAt = plan.occurredAt,
                correctsEntryId = null
            ),
            entryId = deterministic.entryId
        )

        val entryId = when (appendResult) {
            is FinancialLedgerAppendResult.Appended -> appendResult.entryId
            is FinancialLedgerAppendResult.AlreadyAppended -> {
                // B3-B2B never adopts an unbound historical entry.
                return integrityFailure()
            }
            FinancialLedgerAppendResult.TraceUnavailable ->
                return integrityFailure()
            FinancialLedgerAppendResult.OrganizationUnavailable ->
                return unavailableFailure()
            FinancialLedgerAppendResult.CorrectionTargetUnavailable ->
                return integrityFailure()
            FinancialLedgerAppendResult.Conflict ->
                return conflictFailure()
            FinancialLedgerAppendResult.IntegrityFailure ->
                return integrityFailure()
        }

        insertLineage(
            connection = connection,
            plan = plan,
            traceId = traceId,
            entryId = entryId
        )

        return GovernedFinancialLedgerMaterializationCommitResult.Materialized(
            traceId,
            entryId
        )
    }

    private fun lockSubject(
        connection: Connection,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan
    ): MarketplaceEconomicEvidenceSubject? =
        connection.prepareStatement(
            "SELECT organization_id,marketplace_order_id,marketplace_key," +
                "external_order_id,currency " +
                "FROM marketplace_economic_evidence_subject " +
                "WHERE organization_id=? AND marketplace_order_id=? FOR UPDATE"
        ).use { statement ->
            statement.setObject(1, plan.subject.organizationId.value)
            statement.setObject(2, plan.subject.orderId.value)
            statement.executeQuery().use { result ->
                if (!result.next()) {
                    null
                } else {
                    MarketplaceEconomicEvidenceSubject(
                        organizationId = OrganizationId.parse(
                            result.getObject("organization_id", UUID::class.java).toString()
                        ),
                        orderId = MarketplaceOrderId.parse(
                            result.getObject("marketplace_order_id", UUID::class.java).toString()
                        ),
                        marketplace = MarketplaceKey(result.getString("marketplace_key")),
                        externalOrderId = MarketplaceExternalOrderId(
                            result.getString("external_order_id")
                        ),
                        currency = MarketplaceCurrency(result.getString("currency").trim())
                    )
                }
            }
        }

    private fun loadSourceObservation(
        connection: Connection,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan
    ): MarketplaceEconomicComponentObservation? =
        connection.prepareStatement(
            "SELECT subject.organization_id,subject.marketplace_order_id," +
                "subject.marketplace_key,subject.external_order_id,subject.currency AS subject_currency," +
                "fact.fact_id,fact.family,fact.observed_at," +
                "component.component_id,component.component_type,component.direction," +
                "component.magnitude,component.currency AS component_currency," +
                "component.source_kind,component.source_system_key," +
                "component.source_external_reference," +
                "component.source_external_reference_absence_reason," +
                "component.occurred_at,component.quality,component.coverage " +
                "FROM marketplace_economic_evidence_subject subject " +
                "JOIN marketplace_economic_evidence_fact fact " +
                "ON fact.organization_id=subject.organization_id " +
                "AND fact.marketplace_order_id=subject.marketplace_order_id " +
                "JOIN marketplace_economic_evidence_component_fact component " +
                "ON component.organization_id=fact.organization_id " +
                "AND component.marketplace_order_id=fact.marketplace_order_id " +
                "AND component.fact_id=fact.fact_id " +
                "WHERE subject.organization_id=? " +
                "AND subject.marketplace_order_id=? AND fact.fact_id=?"
        ).use { statement ->
            statement.setObject(1, plan.subject.organizationId.value)
            statement.setObject(2, plan.subject.orderId.value)
            statement.setObject(3, plan.sourceAuthorityIdentity.valueForPersistence())
            statement.executeQuery().use { result ->
                if (!result.next()) null else sourceObservation(result)
            }
        }

    private fun sourceObservation(result: ResultSet): MarketplaceEconomicComponentObservation {
        val organizationId = OrganizationId.parse(
            result.getObject("organization_id", UUID::class.java).toString()
        )
        val orderId = MarketplaceOrderId.parse(
            result.getObject("marketplace_order_id", UUID::class.java).toString()
        )
        val subjectCurrency = MarketplaceCurrency(result.getString("subject_currency").trim())
        val subject = MarketplaceEconomicEvidenceSubject(
            organizationId = organizationId,
            orderId = orderId,
            marketplace = MarketplaceKey(result.getString("marketplace_key")),
            externalOrderId = MarketplaceExternalOrderId(result.getString("external_order_id")),
            currency = subjectCurrency
        )

        val componentCurrency = MarketplaceCurrency(
            result.getString("component_currency").trim()
        )
        val externalReference = result.getString("source_external_reference")
        val absenceReason = result.getString(
            "source_external_reference_absence_reason"
        )
        val sourceState = if (externalReference != null) {
            EconomicExternalReferenceState.Present(
                EconomicExternalReference(externalReference)
            )
        } else {
            require(absenceReason == EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN.name) {
                "Persisted source absence reason is invalid"
            }
            EconomicExternalReferenceState.Absent(
                EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN
            )
        }

        val magnitude = result.getBigDecimal("magnitude")
        val canonicalMagnitude = if (magnitude.signum() == 0) {
            "0"
        } else {
            magnitude.stripTrailingZeros().toPlainString()
        }

        val component = EconomicComponent(
            organizationId = organizationId,
            id = EconomicComponentId.parse(
                result.getObject("component_id", UUID::class.java).toString()
            ),
            orderId = orderId,
            type = EconomicComponentType.valueOf(result.getString("component_type")),
            direction = EconomicDirection.valueOf(result.getString("direction")),
            magnitude = MarketplaceMoney.parse(componentCurrency, canonicalMagnitude),
            source = EconomicSource(
                kind = EconomicSourceKind.valueOf(result.getString("source_kind")),
                systemKey = EconomicSourceSystemKey(result.getString("source_system_key")),
                externalReference = sourceState
            ),
            occurredAt = result.getTimestamp("occurred_at").toInstant(),
            quality = EconomicEvidenceQuality.valueOf(result.getString("quality"))
        )

        return MarketplaceEconomicComponentObservation(
            id = MarketplaceEconomicEvidenceObservationId.parse(
                result.getObject("fact_id", UUID::class.java).toString()
            ),
            subject = subject,
            family = MarketplaceEconomicEvidenceFamily.valueOf(result.getString("family")),
            component = component,
            coverageClaim = EconomicComponentCoverage.valueOf(result.getString("coverage")),
            observedAt = result.getTimestamp("observed_at").toInstant()
        )
    }

    private fun planMatchesObservation(
        plan: VerifiedFinancialLedgerComponentMaterializationPlan,
        observation: MarketplaceEconomicComponentObservation
    ): Boolean {
        if (plan.sourceAuthorityIdentity != observation.id) return false
        if (plan.subject != observation.subject) return false
        if (plan.materializationPolicyVersion != FinancialLedgerMaterializationPolicyVersion.V1) {
            return false
        }
        if (plan.stage != FinancialLedgerComponentStageCompatibility.stageFor(observation.component.type)) {
            return false
        }
        if (plan.direction != observation.component.direction) return false
        if (plan.magnitude != observation.component.magnitude) return false
        if (plan.source != observation.component.source) return false
        if (plan.occurredAt != observation.component.occurredAt) return false

        val recomputed = FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation)
        return recomputed == plan.verifiedSourceFingerprint
    }

    private fun loadLineage(
        connection: Connection,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan
    ): StoredLineage? =
        connection.prepareStatement(
            "SELECT source_fingerprint_canonicalization_version," +
                "source_fingerprint_sha256,source_authority_semantic_version," +
                "materialization_policy_version,stage,basis,trace_id,ledger_entry_id " +
                "FROM marketplace_financial_ledger_materialization_lineage " +
                "WHERE organization_id=? AND source_order_id=? " +
                "AND source_authority_identity=?"
        ).use { statement ->
            statement.setObject(1, plan.subject.organizationId.value)
            statement.setObject(2, plan.subject.orderId.value)
            statement.setObject(3, plan.sourceAuthorityIdentity.valueForPersistence())
            statement.executeQuery().use { result ->
                if (!result.next()) {
                    null
                } else {
                    StoredLineage(
                        fingerprintCanonicalizationVersion =
                            result.getInt("source_fingerprint_canonicalization_version"),
                        fingerprintSha256 = result.getString("source_fingerprint_sha256"),
                        semanticVersion = result.getString("source_authority_semantic_version"),
                        policyVersion = result.getString("materialization_policy_version"),
                        stage = result.getString("stage"),
                        basis = result.getString("basis"),
                        traceId = FinancialTraceId.of(
                            result.getObject("trace_id", UUID::class.java)
                        ),
                        entryId = FinancialLedgerEntryId.of(
                            result.getObject("ledger_entry_id", UUID::class.java)
                        )
                    )
                }
            }
        }

    private fun verifyReplay(
        connection: Connection,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan,
        observation: MarketplaceEconomicComponentObservation,
        lineage: StoredLineage
    ): GovernedFinancialLedgerMaterializationCommitResult {
        if (
            lineage.fingerprintCanonicalizationVersion !=
                plan.verifiedSourceFingerprint.canonicalizationVersion ||
            lineage.fingerprintSha256 != plan.verifiedSourceFingerprint.sha256 ||
            lineage.semanticVersion != plan.sourceAuthoritySemanticVersion.value ||
            lineage.policyVersion != plan.materializationPolicyVersion.value ||
            lineage.stage != plan.stage.name ||
            lineage.basis != plan.basis.name
        ) {
            return integrityFailure()
        }

        val recomputed = FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation)
        if (recomputed != plan.verifiedSourceFingerprint) {
            return integrityFailure()
        }

        if (!traceAndEntryMatch(connection, plan, lineage)) {
            return integrityFailure()
        }

        return GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized(
            lineage.traceId,
            lineage.entryId
        )
    }

    private fun traceAndEntryMatch(
        connection: Connection,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan,
        lineage: StoredLineage
    ): Boolean =
        connection.prepareStatement(
            "SELECT trace.order_id,trace.marketplace_key,trace.external_order_id,trace.currency," +
                "entry.trace_id,entry.stage,entry.basis,entry.direction,entry.magnitude," +
                "entry.source_kind,entry.source_system_key,entry.external_reference," +
                "entry.external_reference_absence_reason,entry.occurred_at,entry.corrects_entry_id " +
                "FROM marketplace_financial_trace trace " +
                "JOIN marketplace_financial_ledger_entry entry " +
                "ON entry.organization_id=trace.organization_id AND entry.trace_id=trace.trace_id " +
                "WHERE trace.organization_id=? AND trace.trace_id=? AND entry.entry_id=?"
        ).use { statement ->
            statement.setObject(1, plan.subject.organizationId.value)
            statement.setObject(2, lineage.traceId.valueForPersistence())
            statement.setObject(3, lineage.entryId.valueForPersistence())
            statement.executeQuery().use { result ->
                if (!result.next()) {
                    false
                } else {
                    storedTraceAndEntryMatch(result, plan, lineage)
                }
            }
        }

    private fun storedTraceAndEntryMatch(
        result: ResultSet,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan,
        lineage: StoredLineage
    ): Boolean {
        if (
            result.getObject("order_id", UUID::class.java) != plan.subject.orderId.value ||
            result.getString("marketplace_key") != plan.subject.marketplace.value ||
            result.getString("external_order_id") != plan.subject.externalOrderId.value ||
            result.getString("currency").trim() != plan.subject.currency.code ||
            result.getObject("trace_id", UUID::class.java) != lineage.traceId.valueForPersistence() ||
            result.getString("stage") != plan.stage.name ||
            result.getString("basis") != plan.basis.name ||
            result.getString("direction") != plan.direction.name ||
            result.getBigDecimal("magnitude").compareTo(plan.magnitude.amount) != 0 ||
            result.getString("source_kind") != plan.source.kind.name ||
            result.getString("source_system_key") != plan.source.systemKey.value ||
            result.getTimestamp("occurred_at").toInstant() != plan.occurredAt ||
            result.getObject("corrects_entry_id") != null
        ) {
            return false
        }

        return persistedExternalReferenceMatches(result, plan.source.externalReference)
    }

    private fun persistedExternalReferenceMatches(
        result: ResultSet,
        expected: EconomicExternalReferenceState
    ): Boolean {
        val storedReference = result.getString("external_reference")
        val storedAbsence = result.getString("external_reference_absence_reason")

        return when (expected) {
            is EconomicExternalReferenceState.Present ->
                storedReference == expected.reference.value && storedAbsence == null
            is EconomicExternalReferenceState.Absent ->
                storedReference == null && storedAbsence == expected.reason.name
        }
    }

    private fun participatesInCorrection(
        connection: Connection,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan
    ): Boolean =
        connection.prepareStatement(
            "SELECT 1 FROM marketplace_economic_evidence_correction " +
                "WHERE organization_id=? AND marketplace_order_id=? " +
                "AND (superseded_fact_id=? OR replacement_fact_id=?) LIMIT 1"
        ).use { statement ->
            val sourceId = plan.sourceAuthorityIdentity.valueForPersistence()
            statement.setObject(1, plan.subject.organizationId.value)
            statement.setObject(2, plan.subject.orderId.value)
            statement.setObject(3, sourceId)
            statement.setObject(4, sourceId)
            statement.executeQuery().use { it.next() }
        }

    private fun insertLineage(
        connection: Connection,
        plan: VerifiedFinancialLedgerComponentMaterializationPlan,
        traceId: FinancialTraceId,
        entryId: FinancialLedgerEntryId
    ) {
        connection.prepareStatement(
            "INSERT INTO marketplace_financial_ledger_materialization_lineage " +
                "(organization_id,source_order_id,source_authority_identity," +
                "source_fingerprint_canonicalization_version,source_fingerprint_sha256," +
                "source_authority_semantic_version,materialization_policy_version," +
                "stage,basis,trace_id,ledger_entry_id) " +
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)"
        ).use { statement ->
            statement.setObject(1, plan.subject.organizationId.value)
            statement.setObject(2, plan.subject.orderId.value)
            statement.setObject(3, plan.sourceAuthorityIdentity.valueForPersistence())
            statement.setInt(4, plan.verifiedSourceFingerprint.canonicalizationVersion)
            statement.setString(5, plan.verifiedSourceFingerprint.sha256)
            statement.setString(6, plan.sourceAuthoritySemanticVersion.value)
            statement.setString(7, plan.materializationPolicyVersion.value)
            statement.setString(8, plan.stage.name)
            statement.setString(9, plan.basis.name)
            statement.setObject(10, traceId.valueForPersistence())
            statement.setObject(11, entryId.valueForPersistence())
            check(statement.executeUpdate() == 1)
        }
    }

    private fun deterministicIdentities(
        plan: VerifiedFinancialLedgerComponentMaterializationPlan
    ): DeterministicIdentities {
        val organization = plan.subject.organizationId.value.toString()
        val order = plan.subject.orderId.value.toString()
        val source = plan.sourceAuthorityIdentity.valueForPersistence().toString()

        return DeterministicIdentities(
            traceId = FinancialTraceId.of(uuidV5("trace|$organization|$order")),
            openRequestId = FinancialTraceOpenRequestId.of(
                uuidV5("trace-open|$organization|$order")
            ),
            entryId = FinancialLedgerEntryId.of(
                uuidV5("entry|$organization|$order|$source")
            ),
            appendRequestId = FinancialLedgerAppendRequestId.of(
                uuidV5("append|$organization|$order|$source")
            )
        )
    }

    private fun uuidV5(name: String): UUID {
        val digest = MessageDigest.getInstance("SHA-1")
        digest.update(uuidBytes(MATERIALIZATION_NAMESPACE))
        val bytes = digest.digest(name.toByteArray(StandardCharsets.UTF_8))
        bytes[6] = ((bytes[6].toInt() and 0x0f) or 0x50).toByte()
        bytes[8] = ((bytes[8].toInt() and 0x3f) or 0x80).toByte()
        val buffer = ByteBuffer.wrap(bytes, 0, 16)
        return UUID(buffer.getLong(), buffer.getLong())
    }

    private fun uuidBytes(value: UUID): ByteArray =
        ByteBuffer.allocate(16)
            .putLong(value.mostSignificantBits)
            .putLong(value.leastSignificantBits)
            .array()

    private fun classifyUncertainCommit(
        plan: VerifiedFinancialLedgerComponentMaterializationPlan,
        provisional: GovernedFinancialLedgerMaterializationCommitResult.Materialized
    ): GovernedFinancialLedgerMaterializationCommitResult {
        return try {
            connectionFactory().use { connection ->
                val observation = loadSourceObservation(connection, plan)
                    ?: return GovernedFinancialLedgerMaterializationCommitResult.Failed(
                        GovernedFinancialLedgerMaterializationCommitFailure.UNAVAILABLE
                    )
                if (!planMatchesObservation(plan, observation)) {
                    return integrityFailure()
                }
                val lineage = loadLineage(connection, plan)
                    ?: return GovernedFinancialLedgerMaterializationCommitResult.Failed(
                        GovernedFinancialLedgerMaterializationCommitFailure.UNAVAILABLE
                    )
                val replay = verifyReplay(connection, plan, observation, lineage)
                if (
                    replay is GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized &&
                    replay.traceId == provisional.traceId &&
                    replay.entryId == provisional.entryId
                ) {
                    provisional
                } else {
                    integrityFailure()
                }
            }
        } catch (_: Exception) {
            GovernedFinancialLedgerMaterializationCommitResult.Failed(
                GovernedFinancialLedgerMaterializationCommitFailure.UNAVAILABLE
            )
        }
    }

    private fun classifyFailure(error: Exception): GovernedFinancialLedgerMaterializationCommitResult {
        val sqlState = sqlState(error)
        if (sqlState == "23505") {
            return conflictFailure()
        }
        if (
            sqlState == "P0001" ||
            (sqlState != null && sqlState.startsWith("22")) ||
            (sqlState != null && sqlState.startsWith("23"))
        ) {
            return integrityFailure()
        }
        if (error is IllegalArgumentException || error is IllegalStateException) {
            return integrityFailure()
        }
        return GovernedFinancialLedgerMaterializationCommitResult.Failed(
            GovernedFinancialLedgerMaterializationCommitFailure.UNAVAILABLE
        )
    }

    private fun sqlState(error: Throwable): String? {
        var current: Throwable? = error
        while (current != null) {
            if (current is SQLException && current.sqlState != null) {
                return current.sqlState
            }
            current = current.cause
        }
        return null
    }

    private fun integrityFailure(): GovernedFinancialLedgerMaterializationCommitResult =
        GovernedFinancialLedgerMaterializationCommitResult.Failed(
            GovernedFinancialLedgerMaterializationCommitFailure.INTEGRITY_FAILURE
        )

    private fun conflictFailure(): GovernedFinancialLedgerMaterializationCommitResult =
        GovernedFinancialLedgerMaterializationCommitResult.Failed(
            GovernedFinancialLedgerMaterializationCommitFailure.CONFLICT
        )

    private fun unavailableFailure(): GovernedFinancialLedgerMaterializationCommitResult =
        GovernedFinancialLedgerMaterializationCommitResult.Failed(
            GovernedFinancialLedgerMaterializationCommitFailure.UNAVAILABLE
        )

    private data class StoredLineage(
        val fingerprintCanonicalizationVersion: Int,
        val fingerprintSha256: String,
        val semanticVersion: String,
        val policyVersion: String,
        val stage: String,
        val basis: String,
        val traceId: FinancialTraceId,
        val entryId: FinancialLedgerEntryId
    )

    private data class DeterministicIdentities(
        val traceId: FinancialTraceId,
        val openRequestId: FinancialTraceOpenRequestId,
        val entryId: FinancialLedgerEntryId,
        val appendRequestId: FinancialLedgerAppendRequestId
    )

    private companion object {
        val MATERIALIZATION_NAMESPACE: UUID =
            UUID.fromString("81a1e4a0-40b2-5f34-95bb-6bcfd8db5f62")
    }
}
