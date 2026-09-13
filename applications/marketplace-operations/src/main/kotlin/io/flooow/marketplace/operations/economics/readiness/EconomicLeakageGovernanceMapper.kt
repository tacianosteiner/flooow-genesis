package io.flooow.marketplace.operations.economics.readiness

import io.flooow.marketplace.operations.economics.reconciliation.EconomicLeakageGovernance
import io.flooow.marketplace.operations.economics.reconciliation.EconomicLeakageGovernanceBlockingReason

object EconomicLeakageGovernanceMapper {
    fun from(
        authorities: EconomicTruthAuthorityAssessment
    ): EconomicLeakageGovernance {
        val blockers = linkedSetOf<EconomicLeakageGovernanceBlockingReason>()
        val references = linkedSetOf<String>()

        evaluateAuthority(
            authority = authorities.identity,
            unresolvedReason = EconomicLeakageGovernanceBlockingReason.IDENTITY_UNRESOLVED,
            blockers = blockers,
            references = references
        )

        evaluateAuthority(
            authority = authorities.currency,
            unresolvedReason = EconomicLeakageGovernanceBlockingReason.CURRENCY_UNRESOLVED,
            blockers = blockers,
            references = references
        )

        evaluateAuthority(
            authority = authorities.allocation,
            unresolvedReason = EconomicLeakageGovernanceBlockingReason.ALLOCATION_UNRESOLVED,
            blockers = blockers,
            references = references
        )

        evaluateAuthority(
            authority = authorities.currentness,
            unresolvedReason = EconomicLeakageGovernanceBlockingReason.EVIDENCE_CURRENTNESS_UNRESOLVED,
            blockers = blockers,
            references = references
        )

        references += authorities.reconciliationEvidenceReferences

        return if (blockers.isEmpty()) {
            EconomicLeakageGovernance.permitted(references)
        } else {
            EconomicLeakageGovernance.blocked(blockers, references)
        }
    }

    private fun evaluateAuthority(
        authority: EconomicTruthAuthorityEvidence,
        unresolvedReason: EconomicLeakageGovernanceBlockingReason,
        blockers: MutableSet<EconomicLeakageGovernanceBlockingReason>,
        references: MutableSet<String>
    ) {
        references += authority.evidenceReferences

        when (authority.state) {
            EconomicTruthAuthorityState.CANONICAL,
            EconomicTruthAuthorityState.RECONCILED -> Unit

            EconomicTruthAuthorityState.UNRESOLVED,
            EconomicTruthAuthorityState.NOT_APPLICABLE ->
                blockers += unresolvedReason

            EconomicTruthAuthorityState.CONTRADICTORY ->
                blockers += EconomicLeakageGovernanceBlockingReason.CONTRADICTORY_AUTHORITY

            EconomicTruthAuthorityState.STALE ->
                blockers += EconomicLeakageGovernanceBlockingReason.STALE_AUTHORITY
        }
    }
}