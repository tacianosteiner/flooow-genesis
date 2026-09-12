package io.flooow.marketplace.operations.economics.readiness

import io.flooow.marketplace.operations.economics.EconomicComponent
import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceFamily
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidence
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicFact
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationStatus
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.Collections
import java.util.EnumMap

enum class EconomicTruthDecisionProfile {
    UNIT_ECONOMICS,
    ADS_PROFITABILITY,
    ORDER_MARGIN,
    EXECUTIVE_ECONOMIC_HEALTH
}

enum class EconomicTruthDimension {
    IDENTITY,
    REVENUE,
    PRODUCT_COST,
    MARKETPLACE_COMMISSION,
    MARKETPLACE_FEE,
    SHIPPING,
    TAX,
    ADVERTISING,
    FINANCIAL_COST,
    OTHER_ADJUSTMENT,
    CURRENCY_CONSISTENCY,
    QUANTITY_ALLOCATION_CONSISTENCY,
    EVIDENCE_CURRENTNESS,
    RECONCILIATION
}

enum class EconomicTruthDimensionState {
    OBSERVED,
    CANONICAL,
    RECONCILED,
    MISSING,
    CONTRADICTORY,
    STALE,
    UNRESOLVED,
    NOT_APPLICABLE
}

enum class EconomicTruthReadinessStatus { READY, NOT_READY }

enum class EconomicTruthCompletenessStatus { COMPLETE, PARTIAL, EMPTY, CONTRADICTORY }

enum class EconomicTruthBlockingReasonCode {
    REQUIRED_EVIDENCE_MISSING,
    REQUIRED_EVIDENCE_ONLY_OBSERVED,
    REQUIRED_COVERAGE_PARTIAL,
    CONTRADICTORY_EVIDENCE,
    STALE_OR_SUPERSEDED_EVIDENCE,
    IDENTITY_UNRESOLVED,
    CURRENCY_UNRESOLVED,
    ALLOCATION_UNRESOLVED,
    RECONCILIATION_UNRESOLVED
}

enum class EconomicTruthAuthorityState {
    CANONICAL,
    RECONCILED,
    UNRESOLVED,
    CONTRADICTORY,
    STALE,
    NOT_APPLICABLE
}

data class EconomicTruthAuthorityEvidence(
    val state: EconomicTruthAuthorityState,
    val evidenceReferences: Set<String> = emptySet()
) {
    init {
        require(evidenceReferences.all { it.isNotBlank() && it == it.trim() })
    }
}

data class EconomicTruthAuthorityAssessment(
    val identity: EconomicTruthAuthorityEvidence,
    val currency: EconomicTruthAuthorityEvidence,
    val allocation: EconomicTruthAuthorityEvidence,
    val currentness: EconomicTruthAuthorityEvidence,
    val reconciliation: FinancialReconciliationStatus?,
    val reconciliationEvidenceReferences: Set<String> = emptySet()
)

data class EconomicTruthEvidenceReference(
    val observationId: MarketplaceEconomicEvidenceObservationId,
    val family: MarketplaceEconomicEvidenceFamily,
    val active: Boolean
)

data class EconomicTruthDimensionAssessment(
    val dimension: EconomicTruthDimension,
    val state: EconomicTruthDimensionState,
    val coverage: EconomicComponentCoverage?,
    val supportedFacts: List<EconomicComponent>,
    val evidenceReferences: List<EconomicTruthEvidenceReference>,
    val authorityEvidenceReferences: Set<String> = emptySet()
)

data class EconomicTruthBlockingReason(
    val dimension: EconomicTruthDimension,
    val code: EconomicTruthBlockingReasonCode
)

class EconomicTruthReadiness internal constructor(
    val organizationId: OrganizationId,
    val subject: MarketplaceEconomicEvidenceSubject,
    val evaluatedAt: Instant,
    val decisionProfile: EconomicTruthDecisionProfile,
    val status: EconomicTruthReadinessStatus,
    val overallEconomicCompleteness: EconomicTruthCompletenessStatus,
    dimensions: Map<EconomicTruthDimension, EconomicTruthDimensionAssessment>,
    val requiredDimensions: Set<EconomicTruthDimension>,
    val optionalDimensions: Set<EconomicTruthDimension>,
    val blockingReasons: Set<EconomicTruthBlockingReason>
) {
    val dimensions: Map<EconomicTruthDimension, EconomicTruthDimensionAssessment> =
        Collections.unmodifiableMap(EnumMap<EconomicTruthDimension, EconomicTruthDimensionAssessment>(EconomicTruthDimension::class.java).apply { putAll(dimensions) })
    val satisfiedDimensions: Set<EconomicTruthDimension> = immutableDimensions(EconomicTruthDimensionState.CANONICAL, EconomicTruthDimensionState.RECONCILED)
    val missingDimensions: Set<EconomicTruthDimension> = immutableDimensions(EconomicTruthDimensionState.MISSING)
    val contradictoryDimensions: Set<EconomicTruthDimension> = immutableDimensions(EconomicTruthDimensionState.CONTRADICTORY)
    val staleOrSupersededDimensions: Set<EconomicTruthDimension> = immutableDimensions(EconomicTruthDimensionState.STALE)
    val unresolvedDimensions: Set<EconomicTruthDimension> = immutableDimensions(EconomicTruthDimensionState.UNRESOLVED)
    val evidenceCoverage: Map<EconomicTruthDimension, EconomicComponentCoverage?> = Collections.unmodifiableMap(
        EnumMap<EconomicTruthDimension, EconomicComponentCoverage?>(EconomicTruthDimension::class.java).apply {
            dimensions.forEach { (dimension, assessment) -> put(dimension, assessment.coverage) }
        }
    )

    init {
        require(subject.organizationId == organizationId)
        require(evaluatedAt.nano % 1_000 == 0) { "Economic truth evaluation time must use microsecond precision" }
        require(dimensions.keys == EconomicTruthDimension.entries.toSet())
        require(requiredDimensions.intersect(optionalDimensions).isEmpty())
        require(requiredDimensions + optionalDimensions == EconomicTruthDimension.entries.toSet())
        require((status == EconomicTruthReadinessStatus.READY) == blockingReasons.isEmpty())
    }

    private fun immutableDimensions(vararg states: EconomicTruthDimensionState): Set<EconomicTruthDimension> =
        Collections.unmodifiableSet(dimensions.values.filter { it.state in states }.mapTo(linkedSetOf()) { it.dimension })

    override fun toString(): String = "[REDACTED]"
}

private data class EconomicTruthReadinessProfile(
    val required: Set<EconomicTruthDimension>,
    val minimumCoverage: EconomicComponentCoverage,
    val acceptsNotApplicable: Set<EconomicTruthDimension> = emptySet()
)

object EconomicTruthReadinessEvaluator {
    fun evaluate(
        evidence: MarketplaceIndependentEconomicEvidence,
        authorities: EconomicTruthAuthorityAssessment,
        decisionProfile: EconomicTruthDecisionProfile,
        evaluatedAt: Instant
    ): EconomicTruthReadiness {
        val profile = profiles.getValue(decisionProfile)
        val dimensions = EnumMap<EconomicTruthDimension, EconomicTruthDimensionAssessment>(EconomicTruthDimension::class.java)
        componentDimensions.forEach { (type, dimension) -> dimensions[dimension] = componentDimension(evidence, type, dimension) }
        dimensions[EconomicTruthDimension.IDENTITY] = authorityDimension(EconomicTruthDimension.IDENTITY, authorities.identity)
        dimensions[EconomicTruthDimension.CURRENCY_CONSISTENCY] = authorityDimension(EconomicTruthDimension.CURRENCY_CONSISTENCY, authorities.currency)
        dimensions[EconomicTruthDimension.QUANTITY_ALLOCATION_CONSISTENCY] = authorityDimension(EconomicTruthDimension.QUANTITY_ALLOCATION_CONSISTENCY, authorities.allocation)
        dimensions[EconomicTruthDimension.EVIDENCE_CURRENTNESS] = authorityDimension(EconomicTruthDimension.EVIDENCE_CURRENTNESS, authorities.currentness)
        dimensions[EconomicTruthDimension.RECONCILIATION] = reconciliationDimension(authorities)

        val reasons = linkedSetOf<EconomicTruthBlockingReason>()
        profile.required.forEach { dimension ->
            val assessment = dimensions.getValue(dimension)
            blockingReason(dimension, assessment, profile)?.let(reasons::add)
        }
        dimensions.values.filter { it.state == EconomicTruthDimensionState.CONTRADICTORY }.forEach {
            reasons += EconomicTruthBlockingReason(it.dimension, EconomicTruthBlockingReasonCode.CONTRADICTORY_EVIDENCE)
        }

        val allDimensions = EconomicTruthDimension.entries.toSet()
        return EconomicTruthReadiness(
            evidence.subject.organizationId,
            evidence.subject,
            evaluatedAt,
            decisionProfile,
            if (reasons.isEmpty()) EconomicTruthReadinessStatus.READY else EconomicTruthReadinessStatus.NOT_READY,
            overallCompleteness(dimensions),
            dimensions,
            Collections.unmodifiableSet(profile.required),
            Collections.unmodifiableSet(allDimensions - profile.required),
            Collections.unmodifiableSet(reasons)
        )
    }

    private fun componentDimension(
        evidence: MarketplaceIndependentEconomicEvidence,
        type: EconomicComponentType,
        dimension: EconomicTruthDimension
    ): EconomicTruthDimensionAssessment {
        val active = evidence.activeFacts.componentFacts(type)
        val historical = evidence.historicalFacts.componentFacts(type)
        val activeIds = active.mapTo(hashSetOf()) { it.id }
        val references = historical.map { EconomicTruthEvidenceReference(it.id, it.observation.family, it.id in activeIds) }
        if (active.isEmpty()) {
            return EconomicTruthDimensionAssessment(
                dimension,
                if (historical.isEmpty()) EconomicTruthDimensionState.MISSING else EconomicTruthDimensionState.STALE,
                null,
                emptyList(),
                references
            )
        }
        val completeConfirmedMeanings = active.filter {
            it.observation.coverageClaim == EconomicComponentCoverage.COMPLETE &&
                it.observation.component.quality == EconomicEvidenceQuality.CONFIRMED
        }.map { Triple(it.observation.component.direction, it.observation.component.magnitude, it.observation.component.occurredAt) }.toSet()
        val contradictory = completeConfirmedMeanings.size > 1
        val state = when {
            contradictory -> EconomicTruthDimensionState.CONTRADICTORY
            active.any { it.observation.component.quality == EconomicEvidenceQuality.CONFIRMED } -> EconomicTruthDimensionState.CANONICAL
            else -> EconomicTruthDimensionState.OBSERVED
        }
        val coverage = if (active.any { it.observation.coverageClaim == EconomicComponentCoverage.COMPLETE }) {
            EconomicComponentCoverage.COMPLETE
        } else {
            EconomicComponentCoverage.PARTIAL
        }
        return EconomicTruthDimensionAssessment(dimension, state, coverage, active.map { it.observation.component }, references)
    }

    private fun authorityDimension(
        dimension: EconomicTruthDimension,
        authority: EconomicTruthAuthorityEvidence
    ) = EconomicTruthDimensionAssessment(
        dimension,
        when (authority.state) {
            EconomicTruthAuthorityState.CANONICAL -> EconomicTruthDimensionState.CANONICAL
            EconomicTruthAuthorityState.RECONCILED -> EconomicTruthDimensionState.RECONCILED
            EconomicTruthAuthorityState.UNRESOLVED -> EconomicTruthDimensionState.UNRESOLVED
            EconomicTruthAuthorityState.CONTRADICTORY -> EconomicTruthDimensionState.CONTRADICTORY
            EconomicTruthAuthorityState.STALE -> EconomicTruthDimensionState.STALE
            EconomicTruthAuthorityState.NOT_APPLICABLE -> EconomicTruthDimensionState.NOT_APPLICABLE
        },
        null,
        emptyList(),
        emptyList(),
        Collections.unmodifiableSet(authority.evidenceReferences)
    )

    private fun reconciliationDimension(authorities: EconomicTruthAuthorityAssessment): EconomicTruthDimensionAssessment {
        val state = when (authorities.reconciliation) {
            FinancialReconciliationStatus.FULLY_RECONCILED -> EconomicTruthDimensionState.RECONCILED
            FinancialReconciliationStatus.DIVERGENCE -> EconomicTruthDimensionState.CONTRADICTORY
            FinancialReconciliationStatus.PENDING,
            FinancialReconciliationStatus.PARTIALLY_RECONCILED,
            null -> EconomicTruthDimensionState.UNRESOLVED
        }
        return EconomicTruthDimensionAssessment(
            EconomicTruthDimension.RECONCILIATION,
            state,
            null,
            emptyList(),
            emptyList(),
            Collections.unmodifiableSet(authorities.reconciliationEvidenceReferences)
        )
    }

    private fun blockingReason(
        dimension: EconomicTruthDimension,
        assessment: EconomicTruthDimensionAssessment,
        profile: EconomicTruthReadinessProfile
    ): EconomicTruthBlockingReason? {
        val code = when (assessment.state) {
            EconomicTruthDimensionState.MISSING -> EconomicTruthBlockingReasonCode.REQUIRED_EVIDENCE_MISSING
            EconomicTruthDimensionState.OBSERVED -> EconomicTruthBlockingReasonCode.REQUIRED_EVIDENCE_ONLY_OBSERVED
            EconomicTruthDimensionState.CONTRADICTORY -> EconomicTruthBlockingReasonCode.CONTRADICTORY_EVIDENCE
            EconomicTruthDimensionState.STALE -> EconomicTruthBlockingReasonCode.STALE_OR_SUPERSEDED_EVIDENCE
            EconomicTruthDimensionState.UNRESOLVED -> when (dimension) {
                EconomicTruthDimension.IDENTITY -> EconomicTruthBlockingReasonCode.IDENTITY_UNRESOLVED
                EconomicTruthDimension.CURRENCY_CONSISTENCY -> EconomicTruthBlockingReasonCode.CURRENCY_UNRESOLVED
                EconomicTruthDimension.QUANTITY_ALLOCATION_CONSISTENCY -> EconomicTruthBlockingReasonCode.ALLOCATION_UNRESOLVED
                EconomicTruthDimension.RECONCILIATION -> EconomicTruthBlockingReasonCode.RECONCILIATION_UNRESOLVED
                else -> EconomicTruthBlockingReasonCode.REQUIRED_EVIDENCE_MISSING
            }
            EconomicTruthDimensionState.NOT_APPLICABLE -> if (dimension in profile.acceptsNotApplicable) {
                null
            } else {
                EconomicTruthBlockingReasonCode.REQUIRED_EVIDENCE_MISSING
            }
            EconomicTruthDimensionState.CANONICAL,
            EconomicTruthDimensionState.RECONCILED -> if (
                assessment.coverage == EconomicComponentCoverage.PARTIAL &&
                profile.minimumCoverage == EconomicComponentCoverage.COMPLETE
            ) EconomicTruthBlockingReasonCode.REQUIRED_COVERAGE_PARTIAL else null
        }
        return code?.let { EconomicTruthBlockingReason(dimension, it) }
    }

    private val componentDimensions = mapOf(
        EconomicComponentType.REVENUE to EconomicTruthDimension.REVENUE,
        EconomicComponentType.PRODUCT_COST to EconomicTruthDimension.PRODUCT_COST,
        EconomicComponentType.MARKETPLACE_COMMISSION to EconomicTruthDimension.MARKETPLACE_COMMISSION,
        EconomicComponentType.MARKETPLACE_FEE to EconomicTruthDimension.MARKETPLACE_FEE,
        EconomicComponentType.SHIPPING to EconomicTruthDimension.SHIPPING,
        EconomicComponentType.TAX to EconomicTruthDimension.TAX,
        EconomicComponentType.ADVERTISING to EconomicTruthDimension.ADVERTISING,
        EconomicComponentType.FINANCIAL_COST to EconomicTruthDimension.FINANCIAL_COST,
        EconomicComponentType.OTHER_ADJUSTMENT to EconomicTruthDimension.OTHER_ADJUSTMENT
    )

    private val base = setOf(
        EconomicTruthDimension.IDENTITY,
        EconomicTruthDimension.REVENUE,
        EconomicTruthDimension.PRODUCT_COST,
        EconomicTruthDimension.MARKETPLACE_FEE,
        EconomicTruthDimension.CURRENCY_CONSISTENCY,
        EconomicTruthDimension.QUANTITY_ALLOCATION_CONSISTENCY,
        EconomicTruthDimension.EVIDENCE_CURRENTNESS
    )
    private val profiles = mapOf(
        EconomicTruthDecisionProfile.UNIT_ECONOMICS to EconomicTruthReadinessProfile(base, EconomicComponentCoverage.PARTIAL),
        EconomicTruthDecisionProfile.ADS_PROFITABILITY to EconomicTruthReadinessProfile(base + EconomicTruthDimension.ADVERTISING + EconomicTruthDimension.RECONCILIATION, EconomicComponentCoverage.PARTIAL),
        EconomicTruthDecisionProfile.ORDER_MARGIN to EconomicTruthReadinessProfile(
            base + setOf(EconomicTruthDimension.MARKETPLACE_COMMISSION, EconomicTruthDimension.SHIPPING, EconomicTruthDimension.TAX, EconomicTruthDimension.OTHER_ADJUSTMENT, EconomicTruthDimension.RECONCILIATION),
            EconomicComponentCoverage.COMPLETE,
            setOf(EconomicTruthDimension.SHIPPING, EconomicTruthDimension.TAX, EconomicTruthDimension.OTHER_ADJUSTMENT)
        ),
        EconomicTruthDecisionProfile.EXECUTIVE_ECONOMIC_HEALTH to EconomicTruthReadinessProfile(
            EconomicTruthDimension.entries.toSet(),
            EconomicComponentCoverage.COMPLETE,
            emptySet()
        )
    )

    private fun overallCompleteness(
        dimensions: Map<EconomicTruthDimension, EconomicTruthDimensionAssessment>
    ): EconomicTruthCompletenessStatus {
        val economic = componentDimensions.values.map(dimensions::getValue)
        return when {
            economic.any { it.state == EconomicTruthDimensionState.CONTRADICTORY } -> EconomicTruthCompletenessStatus.CONTRADICTORY
            economic.all {
                it.state in setOf(EconomicTruthDimensionState.CANONICAL, EconomicTruthDimensionState.RECONCILED, EconomicTruthDimensionState.NOT_APPLICABLE) &&
                    (it.coverage == null || it.coverage == EconomicComponentCoverage.COMPLETE)
            } -> EconomicTruthCompletenessStatus.COMPLETE
            economic.any { it.supportedFacts.isNotEmpty() } -> EconomicTruthCompletenessStatus.PARTIAL
            else -> EconomicTruthCompletenessStatus.EMPTY
        }
    }
}

private fun List<MarketplaceIndependentEconomicFact>.componentFacts(type: EconomicComponentType) =
    filterIsInstance<MarketplaceIndependentEconomicFact.Component>().filter { it.observation.component.type == type }
