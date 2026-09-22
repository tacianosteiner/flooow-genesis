package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.reconciliation.DurableReconciliationCase
import io.flooow.marketplace.operations.economics.reconciliation.EconomicDecisionRoomReconciliationAssessmentBinding
import io.flooow.marketplace.operations.economics.reconciliation.EconomicDecisionRoomReconciliationAssessmentRead
import io.flooow.marketplace.operations.economics.reconciliation.EconomicDecisionRoomReconciliationAssessmentSource
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentFingerprint
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentSnapshot
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentSnapshotCodec
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseStageDifference
import io.flooow.organization.OrganizationId
import java.sql.SQLException
import java.time.Instant
import javax.sql.DataSource

/** Read-only, exact current-revision reconciliation assessment lineage reader. */
class PostgresEconomicDecisionRoomReconciliationAssessmentSource(
    private val dataSource: DataSource
) : EconomicDecisionRoomReconciliationAssessmentSource {
    override fun read(
        organizationId: OrganizationId,
        case: DurableReconciliationCase
    ): EconomicDecisionRoomReconciliationAssessmentRead {
        if (organizationId != case.organizationId) {
            return EconomicDecisionRoomReconciliationAssessmentRead.IntegrityFailure
        }

        return try {
            dataSource.connection.use { connection ->
                connection.prepareStatement(SQL).use { statement ->
                    statement.setObject(1, case.organizationId.value)
                    statement.setObject(2, case.caseId.valueForPersistence())
                    statement.setLong(3, case.revision)
                    statement.executeQuery().use { rows ->
                        if (!rows.next()) return EconomicDecisionRoomReconciliationAssessmentRead.Unavailable
                        val row = Row(
                            rows.getInt("assessment_fingerprint_version"),
                            rows.getString("assessment_fingerprint"),
                            rows.getInt("assessment_snapshot_schema_version"),
                            rows.getString("assessment_snapshot"),
                            rows.getTimestamp("accepted_at").toInstant()
                        )
                        if (rows.next()) return EconomicDecisionRoomReconciliationAssessmentRead.IntegrityFailure
                        verify(row, case)
                    }
                }
            }
        } catch (_: SQLException) {
            EconomicDecisionRoomReconciliationAssessmentRead.Unavailable
        } catch (_: RuntimeException) {
            EconomicDecisionRoomReconciliationAssessmentRead.IntegrityFailure
        }
    }

    private fun verify(
        row: Row,
        case: DurableReconciliationCase
    ): EconomicDecisionRoomReconciliationAssessmentRead {
        val fingerprint = FinancialReconciliationAssessmentFingerprint.parsePersisted(
            row.fingerprintVersion,
            row.fingerprint
        )
        val snapshot = FinancialReconciliationAssessmentSnapshot.parse(
            row.snapshotSchemaVersion,
            row.snapshot
        )
        val assessment = FinancialReconciliationAssessmentSnapshotCodec.verify(snapshot, fingerprint).assessment
        if (
            assessment.organizationId != case.organizationId ||
            assessment.orderId != case.orderId ||
            assessment.traceId != case.traceId ||
            assessment.policyVersion != case.policyVersion ||
            assessment.currency != case.currency ||
            row.acceptedAt != case.lastObservedAt
        ) return EconomicDecisionRoomReconciliationAssessmentRead.IntegrityFailure

        val reconstructed = DurableReconciliationCase.fromAssessment(
            caseId = case.caseId,
            assessment = assessment,
            openedAt = case.openedAt,
            observedAt = case.lastObservedAt,
            revision = case.revision,
            status = case.status,
            resolvedAt = case.resolvedAt
        )
        if (!sameProjection(case, reconstructed)) {
            return EconomicDecisionRoomReconciliationAssessmentRead.IntegrityFailure
        }
        return EconomicDecisionRoomReconciliationAssessmentRead.Available(
            EconomicDecisionRoomReconciliationAssessmentBinding(case.caseId, case.revision, assessment)
        )
    }

    private fun sameProjection(left: DurableReconciliationCase, right: DurableReconciliationCase): Boolean =
        left.absoluteDifferenceSummary == right.absoluteDifferenceSummary &&
            left.evidenceEntryIds == right.evidenceEntryIds &&
            left.stages.size == right.stages.size &&
            left.stages.zip(right.stages).all(::sameStage)

    private fun sameStage(pair: Pair<ReconciliationCaseStageDifference, ReconciliationCaseStageDifference>): Boolean {
        val (left, right) = pair
        return left.stage == right.stage &&
            left.expected == right.expected && left.actual == right.actual &&
            left.signedDifference == right.signedDifference &&
            left.absoluteDifference == right.absoluteDifference && left.tolerance == right.tolerance &&
            left.expectedEntryIds == right.expectedEntryIds && left.actualEntryIds == right.actualEntryIds
    }

    private data class Row(
        val fingerprintVersion: Int,
        val fingerprint: String,
        val snapshotSchemaVersion: Int,
        val snapshot: String,
        val acceptedAt: Instant
    )

    private companion object {
        const val SQL = """
            SELECT assessment_fingerprint_version, assessment_fingerprint,
                   assessment_snapshot_schema_version, assessment_snapshot::text, accepted_at
              FROM marketplace_reconciliation_case_revision_assessment
             WHERE organization_id = ? AND case_id = ? AND case_revision = ?
        """
    }
}
