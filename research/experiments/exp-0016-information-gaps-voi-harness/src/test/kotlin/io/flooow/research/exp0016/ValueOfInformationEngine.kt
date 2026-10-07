package io.flooow.research.exp0016

class ValueOfInformationEngine {
    fun assess(
        gap: InformationGap,
        method: AcquisitionMethod,
        impact: DecisionImpactEstimate?,
    ): ValueOfInformationAssessment {
        if (gap.reasons.isEmpty()) {
            return ValueOfInformationAssessment(
                decision = InformationAcquisitionDecision.INSUFFICIENT_BASIS,
                conservativeNetValue = null,
                reasonCodes = setOf(InformationReasonCode.GAP_NOT_ACTIONABLE),
            )
        }

        if (method.requiredEvidenceKinds.isEmpty()) {
            return ValueOfInformationAssessment(
                decision = InformationAcquisitionDecision.INSUFFICIENT_BASIS,
                conservativeNetValue = null,
                reasonCodes = setOf(InformationReasonCode.NO_REQUIRED_EVIDENCE_DECLARED),
            )
        }

        val deadline = gap.deadline
        if (deadline != null && method.earliestAvailableAt.isAfter(deadline)) {
            return ValueOfInformationAssessment(
                decision = InformationAcquisitionDecision.DO_NOT_ACQUIRE,
                conservativeNetValue = null,
                reasonCodes = setOf(InformationReasonCode.DEADLINE_MISSED),
            )
        }

        if (impact == null) {
            return ValueOfInformationAssessment(
                decision = InformationAcquisitionDecision.DEFER,
                conservativeNetValue = null,
                reasonCodes = setOf(InformationReasonCode.INSUFFICIENT_IMPACT_BASIS),
            )
        }

        val currency = impact.expectedImprovementFloor.currency
        require(method.acquisitionCost.currency == currency)
        require(method.delayCost.currency == currency)
        require(method.executionRiskReserve.currency == currency)

        val totalCost =
            method.acquisitionCost +
                method.delayCost +
                method.executionRiskReserve

        val net =
            SignedMoney(
                amount =
                    impact.expectedImprovementFloor.amount -
                        totalCost.amount,
                currency = currency,
            )

        return if (net.amount > java.math.BigDecimal.ZERO) {
            ValueOfInformationAssessment(
                decision = InformationAcquisitionDecision.ACQUIRE_INFORMATION,
                conservativeNetValue = net,
                reasonCodes = setOf(InformationReasonCode.POSITIVE_VALUE_OF_INFORMATION),
            )
        } else {
            ValueOfInformationAssessment(
                decision = InformationAcquisitionDecision.DO_NOT_ACQUIRE,
                conservativeNetValue = net,
                reasonCodes = setOf(InformationReasonCode.NON_POSITIVE_VALUE_OF_INFORMATION),
            )
        }
    }
}
