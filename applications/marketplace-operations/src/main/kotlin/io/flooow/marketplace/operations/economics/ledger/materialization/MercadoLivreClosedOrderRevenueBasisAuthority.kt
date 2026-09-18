package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceFamily
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.organization.OrganizationId
import java.time.Instant

enum class MercadoLivreClosedOrderRevenuePromotionOutcome {
    PROMOTED,
    DUPLICATE,
    IDENTITY_CONFLICT,
    EVIDENCE_CONFLICT
}

data class MercadoLivreClosedOrderRevenueProviderProof(
    val durableObservation: MarketplaceEconomicComponentObservation,
    val organizationId: OrganizationId,
    val marketplaceOrderId: MarketplaceOrderId,
    val identityMarketplace: MarketplaceKey,
    val identityExternalOrderId: MarketplaceExternalOrderId,
    val identityCurrency: MarketplaceCurrency,
    val sourceCapability: String,
    val sourceExternalOrderId: MarketplaceExternalOrderId,
    val sourceCurrency: MarketplaceCurrency,
    val sourceTotalAmount: MarketplaceMoney,
    val sourceDateClosed: Instant,
    val sourceObservedAt: Instant,
    val outcome: MercadoLivreClosedOrderRevenuePromotionOutcome
) {
    override fun toString(): String = "[REDACTED]"
}

sealed interface MercadoLivreClosedOrderRevenueAuthoritySourceResult {
    data object NotFound : MercadoLivreClosedOrderRevenueAuthoritySourceResult

    data class Found(
        val proofs: List<MercadoLivreClosedOrderRevenueProviderProof>
    ) : MercadoLivreClosedOrderRevenueAuthoritySourceResult {
        init {
            require(proofs.isNotEmpty()) {
                "Found provider proof result must contain at least one proof"
            }
        }

        override fun toString(): String = "[REDACTED]"
    }

    data object IntegrityFailure :
        MercadoLivreClosedOrderRevenueAuthoritySourceResult

    data object Unavailable :
        MercadoLivreClosedOrderRevenueAuthoritySourceResult
}

fun interface MercadoLivreClosedOrderRevenueAuthoritySource {
    fun findProofs(
        organizationId: OrganizationId,
        observationId: MarketplaceEconomicEvidenceObservationId,
        marketplaceOrderId: MarketplaceOrderId
    ): MercadoLivreClosedOrderRevenueAuthoritySourceResult
}

class MercadoLivreClosedOrderRevenueBasisAuthority(
    private val source: MercadoLivreClosedOrderRevenueAuthoritySource
) {
    fun resolve(
        operationalOrganizationId: OrganizationId,
        observation: MarketplaceEconomicComponentObservation
    ): FinancialLedgerComponentMaterializationAuthorityDecision {
        if (operationalOrganizationId != observation.subject.organizationId) {
            return FinancialLedgerComponentMaterializationAuthorityDecision.IntegrityFailure
        }

        if (!matchesVersionOneCandidateShape(observation)) {
            return FinancialLedgerComponentMaterializationAuthorityDecision.NotAuthorized(
                FinancialLedgerComponentMaterializationNotAuthorizedReason.BASIS_AUTHORITY_UNAVAILABLE
            )
        }

        val sourceResult =
            try {
                source.findProofs(
                    operationalOrganizationId,
                    observation.id,
                    observation.subject.orderId
                )
            } catch (_: Exception) {
                return FinancialLedgerComponentMaterializationAuthorityDecision.Unavailable
            }

        return when (sourceResult) {
            MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound ->
                notAuthorized()

            MercadoLivreClosedOrderRevenueAuthoritySourceResult.Unavailable ->
                FinancialLedgerComponentMaterializationAuthorityDecision.Unavailable

            MercadoLivreClosedOrderRevenueAuthoritySourceResult.IntegrityFailure ->
                FinancialLedgerComponentMaterializationAuthorityDecision.IntegrityFailure

            is MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found ->
                resolveFoundProofs(observation, sourceResult.proofs)
        }
    }

    private fun resolveFoundProofs(
        observation: MarketplaceEconomicComponentObservation,
        proofs: List<MercadoLivreClosedOrderRevenueProviderProof>
    ): FinancialLedgerComponentMaterializationAuthorityDecision {
        if (
            proofs.any {
                it.outcome ==
                    MercadoLivreClosedOrderRevenuePromotionOutcome.IDENTITY_CONFLICT ||
                    it.outcome ==
                    MercadoLivreClosedOrderRevenuePromotionOutcome.EVIDENCE_CONFLICT
            }
        ) {
            return FinancialLedgerComponentMaterializationAuthorityDecision.IntegrityFailure
        }

        val successful = proofs.filter {
            it.outcome == MercadoLivreClosedOrderRevenuePromotionOutcome.PROMOTED ||
                it.outcome == MercadoLivreClosedOrderRevenuePromotionOutcome.DUPLICATE
        }

        if (successful.isEmpty()) {
            return FinancialLedgerComponentMaterializationAuthorityDecision.IntegrityFailure
        }

        if (successful.any { !matchesExactProof(it, observation) }) {
            return FinancialLedgerComponentMaterializationAuthorityDecision.IntegrityFailure
        }

        return FinancialLedgerComponentMaterializationAuthorityDecision.Authorized(
            sourceAuthorityIdentity = observation.id,
            sourceAuthoritySemanticVersion = AUTHORITY_SEMANTIC_VERSION,
            materializationPolicyVersion =
                FinancialLedgerMaterializationPolicyVersion.V1,
            expectedSourceFingerprint =
                FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(
                    observation
                ),
            basis = FinancialLedgerBasis.ACTUAL
        )
    }

    private fun matchesVersionOneCandidateShape(
        observation: MarketplaceEconomicComponentObservation
    ): Boolean {
        val subject = observation.subject
        val component = observation.component

        val externalReference =
            when (val state = component.source.externalReference) {
                is io.flooow.marketplace.operations.economics
                    .EconomicExternalReferenceState.Present ->
                    state.reference.value

                is io.flooow.marketplace.operations.economics
                    .EconomicExternalReferenceState.Absent ->
                    return false
            }

        return subject.marketplace == MARKETPLACE &&
            observation.family ==
                MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER &&
            component.type == EconomicComponentType.REVENUE &&
            component.direction == EconomicDirection.ADDITION &&
            component.quality == EconomicEvidenceQuality.CONFIRMED &&
            observation.coverageClaim == EconomicComponentCoverage.PARTIAL &&
            component.source.kind == EconomicSourceKind.MARKETPLACE &&
            component.source.systemKey == SOURCE_SYSTEM &&
            externalReference == subject.externalOrderId.value
    }

    private fun matchesExactProof(
        proof: MercadoLivreClosedOrderRevenueProviderProof,
        observation: MarketplaceEconomicComponentObservation
    ): Boolean {
        val subject = observation.subject
        val component = observation.component

        return proof.durableObservation == observation &&
            proof.organizationId == subject.organizationId &&
            proof.marketplaceOrderId == subject.orderId &&
            proof.identityMarketplace == MARKETPLACE &&
            proof.identityMarketplace == subject.marketplace &&
            proof.identityExternalOrderId == subject.externalOrderId &&
            proof.identityCurrency == subject.currency &&
            proof.sourceCapability == SOURCE_CAPABILITY &&
            proof.sourceExternalOrderId == subject.externalOrderId &&
            proof.sourceCurrency == subject.currency &&
            proof.sourceTotalAmount == component.magnitude &&
            proof.sourceDateClosed == component.occurredAt &&
            proof.sourceObservedAt == observation.observedAt
    }

    private fun notAuthorized() =
        FinancialLedgerComponentMaterializationAuthorityDecision.NotAuthorized(
            FinancialLedgerComponentMaterializationNotAuthorizedReason.BASIS_AUTHORITY_UNAVAILABLE
        )

    companion object {
        const val SOURCE_CAPABILITY =
            "marketplace-economic.order-source"

        val MARKETPLACE =
            MarketplaceKey("mercado-livre")

        val SOURCE_SYSTEM =
            EconomicSourceSystemKey("br.com.mercadolivre")

        val AUTHORITY_SEMANTIC_VERSION =
            FinancialLedgerSourceAuthoritySemanticVersion(
                "mercado-livre.closed-order-revenue/1"
            )
    }
}