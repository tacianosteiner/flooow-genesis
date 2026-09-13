package io.flooow.marketplace.operations.economics.readiness

import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessment
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationSide
import java.util.Collections

/**
 * Binds the canonical reconciliation assessment into the same authority object
 * consumed by EconomicTruthReadiness and EconomicLeakageGovernanceMapper.
 *
 * This bridge creates no new reconciliation truth and performs no persistence.
 */
object EconomicTruthReconciliationAuthorityBridge {
    fun bind(
        authorities: EconomicTruthAuthorityAssessment,
        reconciliation: FinancialReconciliationAssessment
    ): EconomicTruthAuthorityAssessment {
        require(
            authorities.reconciliation == null ||
                authorities.reconciliation == reconciliation.status
        ) {
            "Existing reconciliation authority conflicts with governed reconciliation assessment"
        }

        val references = linkedSetOf<String>()

        references += authorities.reconciliationEvidenceReferences

        references +=
            "financial-trace:${reconciliation.traceId.value}"

        references +=
            "marketplace-order:${reconciliation.orderId.value}"

        references +=
            "reconciliation-policy:${reconciliation.policyVersion.value}"

        reconciliation.lines.forEach { line ->
            val expected =
                line.expected as? FinancialReconciliationSide.Observed

            val actual =
                line.actual as? FinancialReconciliationSide.Observed

            expected?.effectiveEntryIds?.forEach { entryId ->
                references +=
                    "financial-ledger-entry:${entryId.value}"
            }

            actual?.effectiveEntryIds?.forEach { entryId ->
                references +=
                    "financial-ledger-entry:${entryId.value}"
            }
        }

        return authorities.copy(
            reconciliation = reconciliation.status,
            reconciliationEvidenceReferences =
                Collections.unmodifiableSet(references)
        )
    }
}