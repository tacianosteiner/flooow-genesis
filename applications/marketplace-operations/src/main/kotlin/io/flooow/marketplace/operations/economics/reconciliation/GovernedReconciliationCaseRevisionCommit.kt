package io.flooow.marketplace.operations.economics.reconciliation

enum class GovernedReconciliationCaseCommitFailure {
    CONFLICT,
    INTEGRITY_FAILURE,
    UNAVAILABLE
}

sealed interface GovernedReconciliationCaseCommitResult {
    data class Applied(
        val caseRevision: Long
    ) : GovernedReconciliationCaseCommitResult

    data class AlreadyApplied(
        val caseRevision: Long
    ) : GovernedReconciliationCaseCommitResult

    data class Failed(
        val failure: GovernedReconciliationCaseCommitFailure
    ) : GovernedReconciliationCaseCommitResult
}

/**
 * Application-owned atomic persistence command.
 *
 * It binds one durable case revision to the exact accepted reconciliation
 * assessment identity and to its complete semantic snapshot.
 *
 * Constructing this command does not persist anything. The persistence
 * adapter owns only the atomic durable commit, never assessment identity.
 */
class GovernedReconciliationCaseRevisionCommit private constructor(
    val caseValue: DurableReconciliationCase,
    val acceptedAssessment: AcceptedFinancialReconciliationAssessment,
    val assessmentSnapshot: FinancialReconciliationAssessmentSnapshot
) {
    init {
        val assessment = acceptedAssessment.assessment

        require(caseValue.organizationId == assessment.organizationId) {
            "Case organization must match accepted assessment organization"
        }
        require(caseValue.orderId == assessment.orderId) {
            "Case order must match accepted assessment order"
        }
        require(caseValue.traceId == assessment.traceId) {
            "Case trace must match accepted assessment trace"
        }
        require(caseValue.policyVersion == assessment.policyVersion) {
            "Case policy must match accepted assessment policy"
        }
        require(caseValue.currency == assessment.currency) {
            "Case currency must match accepted assessment currency"
        }
        require(caseValue.lastObservedAt == acceptedAssessment.acceptedAt) {
            "Case observation time must equal assessment acceptance time"
        }
        require(assessment.status == FinancialReconciliationStatus.DIVERGENCE) {
            "Only divergent accepted assessments may bind to reconciliation cases"
        }
        require(caseValue.caseId == DurableReconciliationCase.deterministicId(assessment)) {
            "Case identity must be the deterministic identity of the accepted assessment"
        }

        val exactProjection = DurableReconciliationCase.fromAssessment(
            caseId = caseValue.caseId,
            assessment = assessment,
            openedAt = caseValue.openedAt,
            observedAt = caseValue.lastObservedAt,
            revision = caseValue.revision,
            status = caseValue.status,
            resolvedAt = caseValue.resolvedAt
        )

        require(
            caseValue.hasSameObservation(exactProjection) &&
                caseValue.evidenceEntryIds == exactProjection.evidenceEntryIds
        ) {
            "Case economic projection must match the exact accepted assessment"
        }

        val verified = FinancialReconciliationAssessmentSnapshotCodec.verify(
            assessmentSnapshot,
            acceptedAssessment.assessmentFingerprint
        )

        require(verified.assessment == assessment) {
            "Snapshot must represent the exact accepted assessment"
        }
    }

    companion object {
        fun create(
            caseValue: DurableReconciliationCase,
            acceptedAssessment: AcceptedFinancialReconciliationAssessment
        ): GovernedReconciliationCaseRevisionCommit {
            val snapshot =
                FinancialReconciliationAssessmentSnapshot.capture(
                    acceptedAssessment.assessment
                )

            return GovernedReconciliationCaseRevisionCommit(
                caseValue = caseValue,
                acceptedAssessment = acceptedAssessment,
                assessmentSnapshot = snapshot
            )
        }
    }
}

fun interface GovernedReconciliationCaseRevisionCommitStore {
    fun commit(
        command: GovernedReconciliationCaseRevisionCommit
    ): GovernedReconciliationCaseCommitResult
}
