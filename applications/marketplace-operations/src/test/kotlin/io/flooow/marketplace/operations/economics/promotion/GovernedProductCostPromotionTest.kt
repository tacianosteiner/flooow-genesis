package io.flooow.marketplace.operations.economics.promotion

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.identity.*
import io.flooow.organization.OrganizationId
import java.math.BigDecimal
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs

class GovernedProductCostPromotionTest {
    private val organization = OrganizationId(UUID.fromString("11111111-1111-4111-8111-111111111111"))
    private val scope = CrossSystemProductIdentityScope(organization, "22222222-2222-4222-8222-222222222222", "33333333-3333-4333-8333-333333333333")
    private val relation = CrossSystemProductIdentityRelation(scope, MercadoLivreProductIdentity("MLB-1", "SKU-1"), OmieProviderProductIdentity("OMIE-1"))
    private val subject = MarketplaceEconomicEvidenceSubject(organization, MarketplaceOrderId(UUID.fromString("44444444-4444-4444-8444-444444444444")), MarketplaceKey("mercado-livre"), MarketplaceExternalOrderId("ORDER-1"), MarketplaceCurrency("USD"))
    private val request = GovernedProductCostPromotionRequest(subject, relation, OmieProductCostSourceObservationKey(scope.omieConnectionId, "marketplace-economic.product-cost", 1, 0), ProductCostQuantityAllocation(BigDecimal("2")), MarketplaceCurrency("USD"))

    @Test fun `current confirmed identity and available durable authority allow promotion`() {
        val evidence = RecordingEvidence(subject)
        val service = service(confirmedIdentity(), GovernedProductCostSourceRead.Available(BigDecimal.ZERO, Instant.parse("2026-09-11T18:00:00Z")), evidence)
        assertEquals(GovernedProductCostPromotionResult.Promoted, service.promote(request))
        assertEquals(GovernedProductCostPromotionResult.AlreadyPromoted, service.promote(request))
        assertEquals(BigDecimal.ZERO, evidence.amount)
    }

    @Test fun `missing currency and cost fail closed`() {
        assertEquals(GovernedProductCostPromotionResult.CurrencyUnavailable, service(confirmedIdentity(), GovernedProductCostSourceRead.Available(BigDecimal.ONE, Instant.EPOCH), RecordingEvidence(subject)).promote(request.copy(currencyAuthority = null)))
        assertEquals(GovernedProductCostPromotionResult.CostMissing, service(confirmedIdentity(), GovernedProductCostSourceRead.CostMissing, RecordingEvidence(subject)).promote(request))
    }

    @Test fun `candidate-only identity is blocked`() {
        assertIdentityBlocked(GovernedProductCostPromotionResult.IdentityUnconfirmed, emptyList())
    }

    @Test fun `current rejected identity is blocked`() {
        assertIdentityBlocked(
            GovernedProductCostPromotionResult.IdentityRejected,
            listOf(identityDecision(kind = CrossSystemProductIdentityDecisionKind.REJECTED))
        )
    }

    @Test fun `earlier confirmed identity followed by current rejection is blocked`() {
        val confirmed = identityDecision()
        val rejected = identityDecision(
            id = "77777777-7777-4777-8777-777777777777",
            kind = CrossSystemProductIdentityDecisionKind.REJECTED,
            supersedes = confirmed.request.id
        )
        assertIdentityBlocked(
            GovernedProductCostPromotionResult.IdentityRejected,
            listOf(confirmed, rejected)
        )
    }

    @Test fun `conflicting effective identity fails closed`() {
        val competingRelation = relation.copy(omie = OmieProviderProductIdentity("OMIE-2"))
        assertIdentityBlocked(
            GovernedProductCostPromotionResult.IdentityConflict,
            listOf(
                identityDecision(),
                identityDecision(
                    relation = competingRelation,
                    id = "77777777-7777-4777-8777-777777777777"
                )
            )
        )
    }

    @Test fun `identity authority from wrong organization is blocked`() {
        val wrongScope = scope.copy(
            organizationId = OrganizationId(UUID.fromString("77777777-7777-4777-8777-777777777777"))
        )
        assertIdentityBlocked(
            GovernedProductCostPromotionResult.IdentityUnconfirmed,
            listOf(identityDecision(relation = relation.copy(scope = wrongScope)))
        )
    }

    @Test fun `identity authority from wrong Mercado Livre connection is blocked`() {
        val wrongScope = scope.copy(
            mercadoLivreConnectionId = "77777777-7777-4777-8777-777777777777"
        )
        assertIdentityBlocked(
            GovernedProductCostPromotionResult.IdentityUnconfirmed,
            listOf(identityDecision(relation = relation.copy(scope = wrongScope)))
        )
    }

    @Test fun `identity authority from wrong Omie connection is blocked`() {
        val wrongScope = scope.copy(
            omieConnectionId = "77777777-7777-4777-8777-777777777777"
        )
        assertIdentityBlocked(
            GovernedProductCostPromotionResult.IdentityUnconfirmed,
            listOf(identityDecision(relation = relation.copy(scope = wrongScope)))
        )
    }

    @Test fun `sellerSku text equality alone does not authorize promotion`() {
        val sameSkuDifferentItem = relation.copy(
            mercadoLivre = MercadoLivreProductIdentity("MLB-OTHER", relation.mercadoLivre.sellerSku)
        )
        assertIdentityBlocked(
            GovernedProductCostPromotionResult.IdentityUnconfirmed,
            listOf(identityDecision(relation = sameSkuDifferentItem))
        )
    }

    @Test fun `exact within-Omie identity alone does not transitively authorize promotion`() {
        assertIdentityBlocked(GovernedProductCostPromotionResult.IdentityUnconfirmed, emptyList())
    }

    private fun service(decisions: List<CrossSystemProductIdentityDecision>, source: GovernedProductCostSourceRead, evidence: RecordingEvidence) = GovernedProductCostPromotionService(
        object : GovernedProductCostPromotionAuthority { override fun read(request: GovernedProductCostPromotionRequest) = source },
        CrossSystemProductIdentityConfirmationService(IdentityRepository(decisions)), evidence,
        Clock.fixed(Instant.parse("2026-09-11T18:01:00Z"), ZoneOffset.UTC)
    )
    private fun assertIdentityBlocked(
        expected: GovernedProductCostPromotionResult,
        decisions: List<CrossSystemProductIdentityDecision>
    ) {
        val evidence = RecordingEvidence(subject)
        val result = service(
            decisions,
            GovernedProductCostSourceRead.Available(BigDecimal.ONE, Instant.EPOCH),
            evidence
        ).promote(request)
        assertEquals(expected, result)
        assertEquals(false, evidence.inserted)
    }

    private fun confirmedIdentity(): List<CrossSystemProductIdentityDecision> =
        listOf(identityDecision())

    private fun identityDecision(
        relation: CrossSystemProductIdentityRelation = this.relation,
        id: String = "55555555-5555-4555-8555-555555555555",
        kind: CrossSystemProductIdentityDecisionKind = CrossSystemProductIdentityDecisionKind.CONFIRMED,
        supersedes: CrossSystemProductIdentityDecisionId? = null
    ): CrossSystemProductIdentityDecision {
        val reason = when {
            supersedes != null -> CrossSystemProductIdentityDecisionReason.CORRECTION
            kind == CrossSystemProductIdentityDecisionKind.CONFIRMED ->
                CrossSystemProductIdentityDecisionReason.EXPLICIT_CONFIRMATION
            else -> CrossSystemProductIdentityDecisionReason.EXPLICIT_REJECTION
        }
        return CrossSystemProductIdentityDecision(
            CrossSystemProductIdentityDecisionRequest(
                CrossSystemProductIdentityDecisionId(UUID.fromString(id)), relation, kind,
                CrossSystemProductIdentityPrincipal.of("test"), reason,
                CrossSystemProductIdentityProvenance.of("test"),
                CrossSystemProductIdentityCorrelationId(UUID.fromString("66666666-6666-4666-8666-666666666666")),
                supersedes
            ),
            if (supersedes == null) 1 else 2,
            if (supersedes == null) Instant.EPOCH else Instant.EPOCH.plusSeconds(1)
        )
    }

    private class IdentityRepository(private val decisions: List<CrossSystemProductIdentityDecision>) : CrossSystemProductIdentityDecisionRepository {
        override fun record(request: CrossSystemProductIdentityDecisionRequest, decidedAt: Instant) = CrossSystemProductIdentityWriteResult.IntegrityFailure
        override fun find(organizationId: OrganizationId, id: CrossSystemProductIdentityDecisionId) = decisions.singleOrNull { it.request.id == id }
        override fun history(relation: CrossSystemProductIdentityRelation) = decisions
        override fun currentForMarketplaceIdentity(
            scope: CrossSystemProductIdentityScope,
            identity: MercadoLivreProductIdentity
        ) = decisions.filter { candidate ->
            candidate.request.relation.scope == scope &&
                candidate.request.relation.mercadoLivre == identity &&
                decisions.none { it.request.supersedesDecisionId == candidate.request.id }
        }
    }
    private class RecordingEvidence(private val subject: MarketplaceEconomicEvidenceSubject) : MarketplaceIndependentEconomicEvidenceRepository {
        var inserted = false; var amount: BigDecimal? = null
        override fun find(subject: MarketplaceEconomicEvidenceSubject) = MarketplaceIndependentEconomicEvidenceReadResult.NotFound
        override fun apply(expectedVersion: MarketplaceEconomicEvidenceVersion, update: MarketplaceIndependentEconomicEvidenceUpdate): MarketplaceIndependentEconomicEvidencePersistResult {
            val fact = (update as MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact).fact as MarketplaceIndependentEconomicFact.Component
            amount = fact.observation.component.magnitude.amount
            val versioned = VersionedMarketplaceIndependentEconomicEvidence(MarketplaceIndependentEconomicEvidence.empty(subject), MarketplaceEconomicEvidenceVersion.ZERO)
            return if (inserted) MarketplaceIndependentEconomicEvidencePersistResult.Duplicate(versioned) else MarketplaceIndependentEconomicEvidencePersistResult.Applied(versioned).also { inserted = true }
        }
    }
}
