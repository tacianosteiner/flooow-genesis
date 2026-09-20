package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.organization.OrganizationId
import java.time.Instant

/**
 * Explicit acceptance marker.
 *
 * Assessment identity is computed inside the acceptance boundary; callers
 * cannot inject a fingerprint independently from the accepted assessment.
 */
class AcceptedFinancialReconciliationAssessment private constructor(
    val assessment: FinancialReconciliationAssessment,
    val assessmentFingerprint: FinancialReconciliationAssessmentFingerprint,
    val acceptedAt: Instant
) {
    init {
        require(acceptedAt.nano % 1_000 == 0) {
            "Accepted assessment timestamp must have microsecond precision"
        }
    }

    companion object {
        fun accept(
            assessment: FinancialReconciliationAssessment,
            acceptedAt: Instant
        ): AcceptedFinancialReconciliationAssessment =
            AcceptedFinancialReconciliationAssessment(
                assessment = assessment,
                assessmentFingerprint =
                    FinancialReconciliationAssessmentFingerprinter
                        .fingerprint(assessment),
                acceptedAt = acceptedAt
            )
    }
}

enum class ReconciliationCaseOrchestrationFailure {
    ORGANIZATION_MISMATCH,
    CONFLICT,
    INTEGRITY_FAILURE,
    UNAVAILABLE,

    /**
     * Unexpected failure before/after the governed commit boundary, normally
     * from the case reader or systemic-analysis adapter.
     */
    PERSISTENCE
}

sealed interface ReconciliationCaseOrchestrationResult {
    data class Created(
        val value: DurableReconciliationCase
    ) : ReconciliationCaseOrchestrationResult

    data class Revised(
        val value: DurableReconciliationCase
    ) : ReconciliationCaseOrchestrationResult

    data class Unchanged(
        val value: DurableReconciliationCase
    ) : ReconciliationCaseOrchestrationResult

    data object NotEligible :
        ReconciliationCaseOrchestrationResult

    data class Rejected(
        val failure: ReconciliationCaseOrchestrationFailure
    ) : ReconciliationCaseOrchestrationResult

    data class Failed(
        val failure: ReconciliationCaseOrchestrationFailure
    ) : ReconciliationCaseOrchestrationResult
}

fun interface SystemicDivergenceAnalysisTrigger {
    fun analyze(
        organizationId: OrganizationId,
        evaluatedAt: Instant
    )
}

/**
 * Governed productive seam from an accepted reconciliation assessment to the
 * durable reconciliation case.
 *
 * Projection equivalence is deliberately NOT the idempotence authority.
 * Every eligible accepted assessment is presented to the governed atomic
 * commit store. That store verifies durable lineage and decides whether the
 * assessment is ALREADY_APPLIED or requires the next revision.
 */
class GovernedReconciliationCaseOrchestrator(
    private val repository: DurableReconciliationCaseRepository,
    private val commitStore: GovernedReconciliationCaseRevisionCommitStore,
    private val systemicAnalysis: SystemicDivergenceAnalysisTrigger? = null
) {
    fun process(
        accepted: AcceptedFinancialReconciliationAssessment,
        organizationId: OrganizationId
    ): ReconciliationCaseOrchestrationResult {
        val assessment = accepted.assessment

        if (assessment.organizationId != organizationId) {
            return ReconciliationCaseOrchestrationResult.Rejected(
                ReconciliationCaseOrchestrationFailure.ORGANIZATION_MISMATCH
            )
        }

        if (assessment.status != FinancialReconciliationStatus.DIVERGENCE) {
            return ReconciliationCaseOrchestrationResult.NotEligible
        }

        val caseId =
            DurableReconciliationCase.deterministicId(assessment)

        return try {
            val existing =
                repository.find(
                    organizationId,
                    caseId
                )

            /*
             * Important:
             *
             * For an existing case we ALWAYS prepare N+1.
             *
             * We do not ask DurableReconciliationCaseProcessor whether the
             * lossy divergence projection changed. A non-divergent assessment
             * line can change exact assessment identity while leaving the case
             * projection identical.
             *
             * If the exact fingerprint is already current, commitStore returns
             * AlreadyApplied(N) before it considers the proposed N+1.
             */
            val candidate =
                if (existing == null) {
                    DurableReconciliationCase.fromAssessment(
                        caseId = caseId,
                        assessment = assessment,
                        openedAt = accepted.acceptedAt,
                        observedAt = accepted.acceptedAt,
                        revision = 1L
                    )
                } else {
                    DurableReconciliationCase.fromAssessment(
                        caseId = caseId,
                        assessment = assessment,
                        openedAt = existing.openedAt,
                        observedAt = accepted.acceptedAt,
                        revision = existing.revision + 1L,
                        status = existing.status,
                        resolvedAt = existing.resolvedAt
                    )
                }

            val command =
                GovernedReconciliationCaseRevisionCommit.create(
                    candidate,
                    accepted
                )

            when (val committed = commitStore.commit(command)) {
                is GovernedReconciliationCaseCommitResult.Applied -> {
                    if (
                        committed.caseRevision != candidate.revision
                    ) {
                        return ReconciliationCaseOrchestrationResult.Failed(
                            ReconciliationCaseOrchestrationFailure
                                .INTEGRITY_FAILURE
                        )
                    }

                    /*
                     * The governed durable commit is authoritative.
                     *
                     * Systemic analysis is a derived projection. A failure in
                     * that projection must never relabel an already-committed
                     * revision as a failed persistence operation.
                     */
                    try {
                        systemicAnalysis?.analyze(
                            organizationId,
                            accepted.acceptedAt
                        )
                    } catch (_: RuntimeException) {
                        // Derived projection failure is isolated from the
                        // authoritative case + assessment-lineage commit.
                    }

                    if (existing == null) {
                        ReconciliationCaseOrchestrationResult.Created(
                            candidate
                        )
                    } else {
                        ReconciliationCaseOrchestrationResult.Revised(
                            candidate
                        )
                    }
                }

                is GovernedReconciliationCaseCommitResult.AlreadyApplied -> {
                    val current =
                        if (
                            existing != null &&
                            existing.revision == committed.caseRevision
                        ) {
                            existing
                        } else {
                            repository.find(
                                organizationId,
                                caseId
                            )
                        }

                    if (
                        current == null ||
                        current.revision != committed.caseRevision
                    ) {
                        ReconciliationCaseOrchestrationResult.Failed(
                            ReconciliationCaseOrchestrationFailure
                                .INTEGRITY_FAILURE
                        )
                    } else {
                        ReconciliationCaseOrchestrationResult.Unchanged(
                            current
                        )
                    }
                }

                is GovernedReconciliationCaseCommitResult.Failed ->
                    ReconciliationCaseOrchestrationResult.Failed(
                        when (committed.failure) {
                            GovernedReconciliationCaseCommitFailure.CONFLICT ->
                                ReconciliationCaseOrchestrationFailure.CONFLICT

                            GovernedReconciliationCaseCommitFailure.INTEGRITY_FAILURE ->
                                ReconciliationCaseOrchestrationFailure
                                    .INTEGRITY_FAILURE

                            GovernedReconciliationCaseCommitFailure.UNAVAILABLE ->
                                ReconciliationCaseOrchestrationFailure.UNAVAILABLE
                        }
                    )
            }
        } catch (_: RuntimeException) {
            ReconciliationCaseOrchestrationResult.Failed(
                ReconciliationCaseOrchestrationFailure.PERSISTENCE
            )
        }
    }
}
