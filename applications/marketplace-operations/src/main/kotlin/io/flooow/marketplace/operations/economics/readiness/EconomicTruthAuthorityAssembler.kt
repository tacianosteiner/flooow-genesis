package io.flooow.marketplace.operations.economics.readiness

import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessment
import java.util.Collections

enum class EconomicTruthAuthorityAssemblyFailureReason {
    IDENTITY_AUTHORITY_UNAVAILABLE,
    CURRENCY_AUTHORITY_UNAVAILABLE,
    ALLOCATION_AUTHORITY_UNAVAILABLE,
    CURRENTNESS_AUTHORITY_UNAVAILABLE
}

sealed interface EconomicTruthAuthorityAssemblyResult {
    data class Assembled(
        val authorities: EconomicTruthAuthorityAssessment
    ) : EconomicTruthAuthorityAssemblyResult

    data class NotAssembled(
        val reasons: Set<EconomicTruthAuthorityAssemblyFailureReason>
    ) : EconomicTruthAuthorityAssemblyResult {
        init {
            require(reasons.isNotEmpty()) {
                "NotAssembled requires at least one explicit failure reason"
            }
        }
    }
}

data class EconomicTruthAuthorityInputs(
    val identity: EconomicTruthAuthorityEvidence?,
    val currency: EconomicTruthAuthorityEvidence?,
    val allocation: EconomicTruthAuthorityEvidence?,
    val currentness: EconomicTruthAuthorityEvidence?
)

/**
 * Pure assembly boundary for production-governed authority inputs.
 *
 * This object does not read repositories, providers, credentials, or caller text.
 * Infrastructure adapters must obtain each authority from server-governed sources.
 */
object EconomicTruthAuthorityAssembler {
    fun assemble(
        inputs: EconomicTruthAuthorityInputs,
        reconciliation: FinancialReconciliationAssessment?
    ): EconomicTruthAuthorityAssemblyResult {
        val failures =
            linkedSetOf<EconomicTruthAuthorityAssemblyFailureReason>()

        if (inputs.identity == null) {
            failures +=
                EconomicTruthAuthorityAssemblyFailureReason.IDENTITY_AUTHORITY_UNAVAILABLE
        }

        if (inputs.currency == null) {
            failures +=
                EconomicTruthAuthorityAssemblyFailureReason.CURRENCY_AUTHORITY_UNAVAILABLE
        }

        if (inputs.allocation == null) {
            failures +=
                EconomicTruthAuthorityAssemblyFailureReason.ALLOCATION_AUTHORITY_UNAVAILABLE
        }

        if (inputs.currentness == null) {
            failures +=
                EconomicTruthAuthorityAssemblyFailureReason.CURRENTNESS_AUTHORITY_UNAVAILABLE
        }

        if (failures.isNotEmpty()) {
            return EconomicTruthAuthorityAssemblyResult.NotAssembled(
                Collections.unmodifiableSet(failures)
            )
        }

        val base =
            EconomicTruthAuthorityAssessment(
                identity = requireNotNull(inputs.identity),
                currency = requireNotNull(inputs.currency),
                allocation = requireNotNull(inputs.allocation),
                currentness = requireNotNull(inputs.currentness),
                reconciliation = null,
                reconciliationEvidenceReferences = emptySet()
            )

        val authorities =
            if (reconciliation == null) {
                base
            } else {
                EconomicTruthReconciliationAuthorityBridge.bind(
                    authorities = base,
                    reconciliation = reconciliation
                )
            }

        return EconomicTruthAuthorityAssemblyResult.Assembled(authorities)
    }
}