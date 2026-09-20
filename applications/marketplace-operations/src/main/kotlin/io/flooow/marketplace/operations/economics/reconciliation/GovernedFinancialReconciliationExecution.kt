package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceReadResult
import io.flooow.marketplace.operations.economics.ledger.MarketplaceFinancialLedgerRepository
import io.flooow.organization.OrganizationId
import java.time.Clock
import java.time.temporal.ChronoUnit

/**
 * Explicit policy authority for one reconciliation execution.
 *
 * The caller of the execution service cannot provide a policy inline.
 * Policy selection remains a separate governed authority.
 */
sealed interface FinancialReconciliationPolicySelection {
    class Selected(
        val policy: FinancialReconciliationPolicy
    ) : FinancialReconciliationPolicySelection {
        override fun toString(): String = "[REDACTED]"
    }

    data object Unavailable :
        FinancialReconciliationPolicySelection {
        override fun toString(): String = "[REDACTED]"
    }

    data object ReadFailure :
        FinancialReconciliationPolicySelection {
        override fun toString(): String = "[REDACTED]"
    }

    data object IntegrityFailure :
        FinancialReconciliationPolicySelection {
        override fun toString(): String = "[REDACTED]"
    }
}

class FinancialReconciliationPolicyContext(
    val organizationId: OrganizationId,
    val marketplace: MarketplaceKey,
    val currency: MarketplaceCurrency
) {
    override fun toString(): String = "[REDACTED]"
}

fun interface FinancialReconciliationPolicySource {
    fun select(
        context: FinancialReconciliationPolicyContext
    ): FinancialReconciliationPolicySelection
}

enum class GovernedFinancialReconciliationExecutionFailure {
    TRACE_READ_FAILURE,
    TRACE_INTEGRITY_FAILURE,
    POLICY_READ_FAILURE,
    POLICY_INTEGRITY_FAILURE,
    EXECUTION_FAILURE
}

sealed interface GovernedFinancialReconciliationExecutionResult {
    class Orchestrated(
        val assessmentStatus: FinancialReconciliationStatus,
        val orchestration: ReconciliationCaseOrchestrationResult
    ) : GovernedFinancialReconciliationExecutionResult {
        override fun toString(): String = "[REDACTED]"
    }

    class NotAssessable(
        val reason: FinancialReconciliationNotAssessableReason
    ) : GovernedFinancialReconciliationExecutionResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object TraceNotFound :
        GovernedFinancialReconciliationExecutionResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object PolicyUnavailable :
        GovernedFinancialReconciliationExecutionResult {
        override fun toString(): String = "[REDACTED]"
    }

    class Failed(
        val failure: GovernedFinancialReconciliationExecutionFailure
    ) : GovernedFinancialReconciliationExecutionResult {
        override fun toString(): String = "[REDACTED]"
    }
}

/**
 * Governed boundary from a durable financial trace to the durable
 * reconciliation-case authority.
 *
 * Caller-controlled input is intentionally restricted to:
 *
 *   organizationId + traceId
 *
 * The caller cannot inject:
 * - FinancialTrace
 * - FinancialReconciliationPolicy
 * - FinancialReconciliationAssessment
 * - assessment fingerprint
 * - acceptedAt
 * - case revision
 *
 * Those values are obtained or produced inside their owning boundaries.
 */
class GovernedFinancialReconciliationExecutionService(
    private val ledger: MarketplaceFinancialLedgerRepository,
    private val policySource: FinancialReconciliationPolicySource,
    private val orchestrator: GovernedReconciliationCaseOrchestrator,
    private val clock: Clock = Clock.systemUTC()
) {
    fun execute(
        organizationId: OrganizationId,
        traceId: FinancialTraceId
    ): GovernedFinancialReconciliationExecutionResult {
        val trace =
            when (
                val read =
                    try {
                        ledger.find(
                            organizationId,
                            traceId
                        )
                    } catch (_: RuntimeException) {
                        return failed(
                            GovernedFinancialReconciliationExecutionFailure
                                .TRACE_READ_FAILURE
                        )
                    }
            ) {
                is FinancialTraceReadResult.Found ->
                    read.trace

                FinancialTraceReadResult.NotFound ->
                    return GovernedFinancialReconciliationExecutionResult
                        .TraceNotFound

                FinancialTraceReadResult.Unavailable ->
                    return failed(
                        GovernedFinancialReconciliationExecutionFailure
                            .TRACE_READ_FAILURE
                    )

                FinancialTraceReadResult.IntegrityFailure ->
                    return failed(
                        GovernedFinancialReconciliationExecutionFailure
                            .TRACE_INTEGRITY_FAILURE
                    )
            }

        if (
            trace.organizationId != organizationId ||
            trace.id != traceId
        ) {
            return failed(
                GovernedFinancialReconciliationExecutionFailure
                    .TRACE_INTEGRITY_FAILURE
            )
        }

        val policyContext =
            FinancialReconciliationPolicyContext(
                organizationId = trace.organizationId,
                marketplace = trace.marketplace,
                currency = trace.currency
            )

        val selection =
            try {
                policySource.select(
                    policyContext
                )
            } catch (_: RuntimeException) {
                return failed(
                    GovernedFinancialReconciliationExecutionFailure
                        .POLICY_READ_FAILURE
                )
            }

        val policy =
            when (selection) {
                is FinancialReconciliationPolicySelection.Selected ->
                    selection.policy

                FinancialReconciliationPolicySelection.Unavailable ->
                    return GovernedFinancialReconciliationExecutionResult
                        .PolicyUnavailable

                FinancialReconciliationPolicySelection.ReadFailure ->
                    return failed(
                        GovernedFinancialReconciliationExecutionFailure
                            .POLICY_READ_FAILURE
                    )

                FinancialReconciliationPolicySelection.IntegrityFailure ->
                    return failed(
                        GovernedFinancialReconciliationExecutionFailure
                            .POLICY_INTEGRITY_FAILURE
                    )
            }

        if (policy.currency != trace.currency) {
            return failed(
                GovernedFinancialReconciliationExecutionFailure
                    .POLICY_INTEGRITY_FAILURE
            )
        }

        val reconciliation =
            try {
                MarketplaceFinancialReconciliation.assess(
                    trace,
                    policy
                )
            } catch (_: RuntimeException) {
                return failed(
                    GovernedFinancialReconciliationExecutionFailure
                        .EXECUTION_FAILURE
                )
            }

        return when (reconciliation) {
            is FinancialReconciliationResult.NotAssessable ->
                GovernedFinancialReconciliationExecutionResult
                    .NotAssessable(
                        reconciliation.reason
                    )

            FinancialReconciliationResult.PolicyCurrencyMismatch ->
                failed(
                    GovernedFinancialReconciliationExecutionFailure
                        .POLICY_INTEGRITY_FAILURE
                )

            is FinancialReconciliationResult.Assessed ->
                orchestrate(
                    organizationId,
                    reconciliation.assessment
                )
        }
    }

    private fun orchestrate(
        organizationId: OrganizationId,
        assessment: FinancialReconciliationAssessment
    ): GovernedFinancialReconciliationExecutionResult {
        val accepted =
            try {
                AcceptedFinancialReconciliationAssessment.accept(
                    assessment,
                    clock.instant()
                        .truncatedTo(
                            ChronoUnit.MICROS
                        )
                )
            } catch (_: RuntimeException) {
                return failed(
                    GovernedFinancialReconciliationExecutionFailure
                        .EXECUTION_FAILURE
                )
            }

        val orchestration =
            try {
                orchestrator.process(
                    accepted,
                    organizationId
                )
            } catch (_: RuntimeException) {
                return failed(
                    GovernedFinancialReconciliationExecutionFailure
                        .EXECUTION_FAILURE
                )
            }

        /*
         * Because the assessment was derived from a trace already verified
         * against organizationId, ORGANIZATION_MISMATCH is impossible unless
         * an internal invariant has been violated.
         */
        if (
            orchestration
                is ReconciliationCaseOrchestrationResult.Rejected &&
            orchestration.failure ==
                ReconciliationCaseOrchestrationFailure
                    .ORGANIZATION_MISMATCH
        ) {
            return failed(
                GovernedFinancialReconciliationExecutionFailure
                    .TRACE_INTEGRITY_FAILURE
            )
        }

        return GovernedFinancialReconciliationExecutionResult
            .Orchestrated(
                assessment.status,
                orchestration
            )
    }

    private fun failed(
        failure: GovernedFinancialReconciliationExecutionFailure
    ): GovernedFinancialReconciliationExecutionResult =
        GovernedFinancialReconciliationExecutionResult.Failed(
            failure
        )
}
