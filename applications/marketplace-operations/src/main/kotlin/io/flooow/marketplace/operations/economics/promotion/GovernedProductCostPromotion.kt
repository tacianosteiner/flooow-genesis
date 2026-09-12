package io.flooow.marketplace.operations.economics.promotion

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.identity.*
import java.math.BigDecimal
import java.nio.charset.StandardCharsets
import java.time.Clock
import java.time.Instant
import java.time.temporal.ChronoUnit
import java.util.UUID

/**
 * The only write performed by this boundary is an append to independent economic evidence.
 * Provider observations, identity decisions, and currency authority are all read-only inputs.
 */
data class GovernedProductCostPromotionRequest(
    val subject: MarketplaceEconomicEvidenceSubject,
    val relation: CrossSystemProductIdentityRelation,
    val sourceObservation: OmieProductCostSourceObservationKey,
    val allocation: ProductCostQuantityAllocation?,
    val currencyAuthority: MarketplaceCurrency?
) {
    init { require(subject.organizationId == relation.scope.organizationId) }
}

data class OmieProductCostSourceObservationKey(
    val connectionId: String,
    val capability: String,
    val inputProgressVersion: Long,
    val recordOrdinal: Int
) {
    init {
        require(UUID.fromString(connectionId).toString() == connectionId)
        require(capability == "marketplace-economic.product-cost")
        require(inputProgressVersion >= 0)
        require(recordOrdinal in 0..999)
    }
}

data class ProductCostQuantityAllocation(val quantity: BigDecimal) {
    init { require(quantity > BigDecimal.ZERO && quantity.scale() <= 6) }
}

sealed interface GovernedProductCostSourceRead {
    data class Available(val unitCost: BigDecimal, val observedAt: Instant) : GovernedProductCostSourceRead
    data object CostMissing : GovernedProductCostSourceRead
    data object CurrencyUnavailable : GovernedProductCostSourceRead
    data object SubjectUnresolved : GovernedProductCostSourceRead
    data object AllocationUnavailable : GovernedProductCostSourceRead
    data object StaleOrSuperseded : GovernedProductCostSourceRead
    data object IntegrityFailure : GovernedProductCostSourceRead
}

/** Validates immutable provider and marketplace source rows by their durable coordinates. */
interface GovernedProductCostPromotionAuthority {
    fun read(request: GovernedProductCostPromotionRequest): GovernedProductCostSourceRead
}

sealed interface GovernedProductCostPromotionResult {
    data object Promoted : GovernedProductCostPromotionResult
    data object AlreadyPromoted : GovernedProductCostPromotionResult
    data object IdentityUnconfirmed : GovernedProductCostPromotionResult
    data object IdentityRejected : GovernedProductCostPromotionResult
    data object IdentityConflict : GovernedProductCostPromotionResult
    data object CostMissing : GovernedProductCostPromotionResult
    data object CurrencyUnavailable : GovernedProductCostPromotionResult
    data object SubjectUnresolved : GovernedProductCostPromotionResult
    data object AllocationUnavailable : GovernedProductCostPromotionResult
    data object EvidenceStaleOrSuperseded : GovernedProductCostPromotionResult
    data object IntegrityFailure : GovernedProductCostPromotionResult
}

class GovernedProductCostPromotionService(
    private val authority: GovernedProductCostPromotionAuthority,
    private val identities: CrossSystemProductIdentityConfirmationService,
    private val evidence: MarketplaceIndependentEconomicEvidenceRepository,
    private val clock: Clock = Clock.systemUTC()
) {
    fun promote(request: GovernedProductCostPromotionRequest): GovernedProductCostPromotionResult {
        if (request.currencyAuthority == null || request.currencyAuthority != request.subject.currency) {
            return GovernedProductCostPromotionResult.CurrencyUnavailable
        }
        if (request.relation.scope.omieConnectionId != request.sourceObservation.connectionId) {
            return GovernedProductCostPromotionResult.IntegrityFailure
        }
        val confirmedDecision = when (val identity = identities.resolve(request.relation)) {
            is CrossSystemProductIdentityResolution.Confirmed -> identity.decision
            is CrossSystemProductIdentityResolution.Rejected -> return GovernedProductCostPromotionResult.IdentityRejected
            CrossSystemProductIdentityResolution.Unresolved -> return GovernedProductCostPromotionResult.IdentityUnconfirmed
            CrossSystemProductIdentityResolution.Conflict -> return GovernedProductCostPromotionResult.IdentityConflict
        }
        val source = when (val result = authority.read(request)) {
            is GovernedProductCostSourceRead.Available -> result
            GovernedProductCostSourceRead.CostMissing -> return GovernedProductCostPromotionResult.CostMissing
            GovernedProductCostSourceRead.CurrencyUnavailable -> return GovernedProductCostPromotionResult.CurrencyUnavailable
            GovernedProductCostSourceRead.SubjectUnresolved -> return GovernedProductCostPromotionResult.SubjectUnresolved
            GovernedProductCostSourceRead.AllocationUnavailable -> return GovernedProductCostPromotionResult.AllocationUnavailable
            GovernedProductCostSourceRead.StaleOrSuperseded -> return GovernedProductCostPromotionResult.EvidenceStaleOrSuperseded
            GovernedProductCostSourceRead.IntegrityFailure -> return GovernedProductCostPromotionResult.IntegrityFailure
        }
        val allocation = request.allocation ?: return GovernedProductCostPromotionResult.AllocationUnavailable
        val amount = source.unitCost.multiply(allocation.quantity)
            .stripTrailingZeros()
            .takeUnless { it.signum() == 0 }
            ?: BigDecimal.ZERO
        if (source.unitCost.signum() < 0 || source.unitCost.scale() > 6 || amount.scale() > 6 ||
            amount.abs() >= BigDecimal("1000000000000000000")) return GovernedProductCostPromotionResult.AllocationUnavailable
        return persist(request, source, amount, confirmedDecision)
    }

    private fun persist(request: GovernedProductCostPromotionRequest, source: GovernedProductCostSourceRead.Available, amount: BigDecimal, decision: CrossSystemProductIdentityDecision): GovernedProductCostPromotionResult {
        val externalReference = sourceReference(request, decision)
        val component = EconomicComponent(
            request.subject.organizationId, EconomicComponentId(deterministicUuid("component:$externalReference")),
            request.subject.orderId, EconomicComponentType.PRODUCT_COST, EconomicDirection.DEDUCTION,
            MarketplaceMoney.parse(request.subject.currency, amount.toPlainString()),
            EconomicSource(EconomicSourceKind.ERP, EconomicSourceSystemKey("omie"), EconomicExternalReferenceState.Present(EconomicExternalReference(externalReference))),
            source.observedAt, EconomicEvidenceQuality.CONFIRMED
        )
        val fact = MarketplaceIndependentEconomicFact.Component(MarketplaceEconomicComponentObservation(
            MarketplaceEconomicEvidenceObservationId.parse(deterministicUuid("observation:$externalReference").toString()), request.subject,
            MarketplaceEconomicEvidenceFamily.PRODUCT_COST, component, EconomicComponentCoverage.PARTIAL,
            clock.instant().truncatedTo(ChronoUnit.MICROS)
        ))
        repeat(3) {
            val version = when (val current = evidence.find(request.subject)) {
                MarketplaceIndependentEconomicEvidenceReadResult.NotFound -> MarketplaceEconomicEvidenceVersion.ZERO
                MarketplaceIndependentEconomicEvidenceReadResult.IntegrityFailure -> return GovernedProductCostPromotionResult.IntegrityFailure
                is MarketplaceIndependentEconomicEvidenceReadResult.Found -> current.versionedEvidence.version
            }
            when (evidence.apply(version, MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(fact))) {
                is MarketplaceIndependentEconomicEvidencePersistResult.Applied -> return GovernedProductCostPromotionResult.Promoted
                is MarketplaceIndependentEconomicEvidencePersistResult.Duplicate -> return GovernedProductCostPromotionResult.AlreadyPromoted
                is MarketplaceIndependentEconomicEvidencePersistResult.StaleVersion -> Unit
                MarketplaceIndependentEconomicEvidencePersistResult.OrganizationUnavailable -> return GovernedProductCostPromotionResult.IntegrityFailure
                else -> return GovernedProductCostPromotionResult.IntegrityFailure
            }
        }
        return GovernedProductCostPromotionResult.IntegrityFailure
    }

    private fun sourceReference(request: GovernedProductCostPromotionRequest, decision: CrossSystemProductIdentityDecision): String {
        val source = request.sourceObservation
        return "omie-product-cost/${source.connectionId}/${source.inputProgressVersion}/${source.recordOrdinal}/" +
            decision.request.id.value
    }
}

private fun deterministicUuid(value: String): UUID = UUID.nameUUIDFromBytes(value.toByteArray(StandardCharsets.UTF_8))
