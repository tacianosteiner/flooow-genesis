package io.flooow.research.exp0016

import java.math.BigDecimal
import java.time.Instant

enum class ConfidenceBand {
    HIGH,
    MEDIUM,
    LOW,
    INSUFFICIENT,
}

enum class GapReason {
    MISSING_EVIDENCE,
    UNRESOLVED_CONTRADICTION,
    TEMPORAL_STALENESS,
    LOW_MEASUREMENT_QUALITY,
    DERIVATION_DEPTH,
    UNKNOWN_CAUSAL_EFFECT,
    UNKNOWN_FORECAST_PARAMETER,
}

enum class AcquisitionMethodKind {
    READ_ONLY_CONNECTOR_QUERY,
    MARKETPLACE_OBSERVATION,
    CONTROLLED_EXPERIMENT,
    HUMAN_VERIFICATION,
    EXTERNAL_DATASET,
}

data class Money(
    val amount: BigDecimal,
    val currency: String,
) {
    init {
        require(amount >= BigDecimal.ZERO)
        require(currency.isNotBlank())
    }

    operator fun plus(other: Money): Money {
        require(currency == other.currency)
        return Money(amount + other.amount, currency)
    }
}

data class SignedMoney(
    val amount: BigDecimal,
    val currency: String,
) {
    init {
        require(currency.isNotBlank())
    }
}

data class InformationGap(
    val gapId: String,
    val organizationId: String,
    val subjectId: String,
    val decisionContext: String,
    val unknownVariable: String,
    val confidenceBand: ConfidenceBand,
    val reasons: Set<GapReason>,
    val deadline: Instant?,
)

data class AcquisitionMethod(
    val methodId: String,
    val kind: AcquisitionMethodKind,
    val requiredEvidenceKinds: Set<String>,
    val acquisitionCost: Money,
    val delayCost: Money,
    val executionRiskReserve: Money,
    val earliestAvailableAt: Instant,
)

data class DecisionImpactEstimate(
    val expectedImprovementFloor: Money,
    val expectedImprovementCeiling: Money,
) {
    init {
        require(expectedImprovementCeiling.amount >= expectedImprovementFloor.amount)
        require(expectedImprovementFloor.currency == expectedImprovementCeiling.currency)
    }
}

enum class InformationAcquisitionDecision {
    ACQUIRE_INFORMATION,
    DEFER,
    DO_NOT_ACQUIRE,
    INSUFFICIENT_BASIS,
}

enum class InformationReasonCode {
    GAP_NOT_ACTIONABLE,
    NO_REQUIRED_EVIDENCE_DECLARED,
    DEADLINE_MISSED,
    NON_POSITIVE_VALUE_OF_INFORMATION,
    POSITIVE_VALUE_OF_INFORMATION,
    INSUFFICIENT_IMPACT_BASIS,
}

data class ValueOfInformationAssessment(
    val decision: InformationAcquisitionDecision,
    val conservativeNetValue: SignedMoney?,
    val reasonCodes: Set<InformationReasonCode>,
) {
    val canonicalTruth: Boolean = false
    val executable: Boolean = false
}
