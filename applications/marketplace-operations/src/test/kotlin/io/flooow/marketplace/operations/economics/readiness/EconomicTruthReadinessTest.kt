package io.flooow.marketplace.operations.economics.readiness

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationStatus
import io.flooow.organization.OrganizationId
import java.math.BigDecimal
import java.time.Instant
import kotlin.test.*

class EconomicTruthReadinessTest {
    private val subject = MarketplaceEconomicEvidenceSubject(
        OrganizationId.parse("10000000-0000-0000-0000-000000000001"),
        MarketplaceOrderId.parse("20000000-0000-0000-0000-000000000001"),
        MarketplaceKey("mercado-livre"),
        MarketplaceExternalOrderId("order-1"),
        MarketplaceCurrency("BRL")
    )
    private val evaluatedAt = Instant.parse("2026-09-12T12:00:00.000000Z")

    @Test
    fun `unit economics is ready with required current governed evidence`() {
        val result = evaluate(unitEvidence(), canonicalAuthorities(), EconomicTruthDecisionProfile.UNIT_ECONOMICS)
        assertEquals(EconomicTruthReadinessStatus.READY, result.status)
        assertEquals(EconomicTruthCompletenessStatus.PARTIAL, result.overallEconomicCompleteness)
        assertTrue(result.blockingReasons.isEmpty())
        assertTrue(result.requiredDimensions.all { it in result.satisfiedDimensions })
    }

    @Test
    fun `missing product cost is not ready and is not represented as zero`() {
        val result = evaluate(
            evidence(component(1, EconomicComponentType.REVENUE, "100"), component(2, EconomicComponentType.MARKETPLACE_FEE, "10")),
            canonicalAuthorities()
        )
        val cost = result.dimensions.getValue(EconomicTruthDimension.PRODUCT_COST)
        assertEquals(EconomicTruthDimensionState.MISSING, cost.state)
        assertTrue(cost.supportedFacts.isEmpty())
        assertBlocked(result, EconomicTruthDimension.PRODUCT_COST, EconomicTruthBlockingReasonCode.REQUIRED_EVIDENCE_MISSING)
    }

    @Test
    fun `observed zero product cost is a valid satisfied fact`() {
        val result = evaluate(unitEvidence(cost = "0"), canonicalAuthorities())
        val cost = result.dimensions.getValue(EconomicTruthDimension.PRODUCT_COST)
        assertEquals(EconomicTruthReadinessStatus.READY, result.status)
        assertEquals(EconomicTruthDimensionState.CANONICAL, cost.state)
        assertEquals(BigDecimal.ZERO, cost.supportedFacts.single().magnitude.amount)
    }

    @Test
    fun `currency contradiction fails closed`() {
        val result = evaluate(unitEvidence(), canonicalAuthorities(currency = EconomicTruthAuthorityState.CONTRADICTORY))
        assertBlocked(result, EconomicTruthDimension.CURRENCY_CONSISTENCY, EconomicTruthBlockingReasonCode.CONTRADICTORY_EVIDENCE)
    }

    @Test
    fun `quantity allocation contradiction fails closed`() {
        val result = evaluate(unitEvidence(), canonicalAuthorities(allocation = EconomicTruthAuthorityState.CONTRADICTORY))
        assertBlocked(result, EconomicTruthDimension.QUANTITY_ALLOCATION_CONSISTENCY, EconomicTruthBlockingReasonCode.CONTRADICTORY_EVIDENCE)
    }

    @Test
    fun `unconfirmed cross-system identity fails closed`() {
        val result = evaluate(unitEvidence(), canonicalAuthorities(identity = EconomicTruthAuthorityState.UNRESOLVED))
        assertBlocked(result, EconomicTruthDimension.IDENTITY, EconomicTruthBlockingReasonCode.IDENTITY_UNRESOLVED)
    }

    @Test
    fun `superseded product cost does not satisfy current readiness`() {
        val original = component(10, EconomicComponentType.PRODUCT_COST, "7")
        var evidence = evidence(component(11, EconomicComponentType.REVENUE, "100"), component(12, EconomicComponentType.MARKETPLACE_FEE, "10"), original)
        val replacement = component(13, EconomicComponentType.SHIPPING, "7")
        evidence = corrected(evidence, original, replacement, 14)
        val result = evaluate(evidence, canonicalAuthorities())
        assertEquals(EconomicTruthDimensionState.STALE, result.dimensions.getValue(EconomicTruthDimension.PRODUCT_COST).state)
        assertBlocked(result, EconomicTruthDimension.PRODUCT_COST, EconomicTruthBlockingReasonCode.STALE_OR_SUPERSEDED_EVIDENCE)
    }

    @Test
    fun `contradictory active economic evidence fails closed`() {
        val result = evaluate(
            evidence(
                component(20, EconomicComponentType.REVENUE, "100"),
                component(21, EconomicComponentType.REVENUE, "101"),
                component(22, EconomicComponentType.PRODUCT_COST, "7"),
                component(23, EconomicComponentType.MARKETPLACE_FEE, "10")
            ),
            canonicalAuthorities()
        )
        assertBlocked(result, EconomicTruthDimension.REVENUE, EconomicTruthBlockingReasonCode.CONTRADICTORY_EVIDENCE)
    }

    @Test
    fun `complete advertising profile without reconciliation is not ready`() {
        val result = evaluate(
            evidence(*unitComponents().toTypedArray(), component(30, EconomicComponentType.ADVERTISING, "5")),
            canonicalAuthorities(reconciliation = FinancialReconciliationStatus.PENDING),
            EconomicTruthDecisionProfile.ADS_PROFITABILITY
        )
        assertBlocked(result, EconomicTruthDimension.RECONCILIATION, EconomicTruthBlockingReasonCode.RECONCILIATION_UNRESOLVED)
    }

    @Test
    fun `same evidence is ready for narrow profile and not ready for broader profile`() {
        val evidence = unitEvidence()
        assertEquals(EconomicTruthReadinessStatus.READY, evaluate(evidence, canonicalAuthorities()).status)
        assertEquals(
            EconomicTruthReadinessStatus.NOT_READY,
            evaluate(evidence, canonicalAuthorities(), EconomicTruthDecisionProfile.EXECUTIVE_ECONOMIC_HEALTH).status
        )
    }

    @Test
    fun `optional missing dimensions do not block unit economics`() {
        val result = evaluate(unitEvidence(), canonicalAuthorities())
        assertEquals(EconomicTruthDimensionState.MISSING, result.dimensions.getValue(EconomicTruthDimension.ADVERTISING).state)
        assertTrue(EconomicTruthDimension.ADVERTISING in result.optionalDimensions)
        assertEquals(EconomicTruthReadinessStatus.READY, result.status)
    }

    @Test
    fun `required missing dimensions block the declared profile`() {
        val result = evaluate(unitEvidence(), canonicalAuthorities(), EconomicTruthDecisionProfile.ADS_PROFITABILITY)
        assertBlocked(result, EconomicTruthDimension.ADVERTISING, EconomicTruthBlockingReasonCode.REQUIRED_EVIDENCE_MISSING)
    }

    @Test
    fun `readiness emits neither recommendation nor action nor execution authority`() {
        val result = evaluate(unitEvidence(), canonicalAuthorities())
        val publicShape = result.javaClass.declaredFields.map { it.name.lowercase() }
        assertTrue(publicShape.none { "recommend" in it || "action" in it || "execution" in it })
        assertEquals("[REDACTED]", result.toString())
    }

    @Test
    fun `economic and authority provenance is preserved for audit`() {
        val result = evaluate(unitEvidence(), canonicalAuthorities())
        val cost = result.dimensions.getValue(EconomicTruthDimension.PRODUCT_COST)
        assertEquals(observationId(2), cost.evidenceReferences.single().observationId)
        assertTrue(cost.evidenceReferences.single().active)
        assertEquals(setOf("identity-decision-1"), result.dimensions.getValue(EconomicTruthDimension.IDENTITY).authorityEvidenceReferences)
        assertEquals(setOf("currency-authority-1"), result.dimensions.getValue(EconomicTruthDimension.CURRENCY_CONSISTENCY).authorityEvidenceReferences)
    }

    private fun unitEvidence(cost: String = "7") = evidence(*unitComponents(cost).toTypedArray())

    private fun unitComponents(cost: String = "7") = listOf(
        component(1, EconomicComponentType.REVENUE, "100"),
        component(2, EconomicComponentType.PRODUCT_COST, cost),
        component(3, EconomicComponentType.MARKETPLACE_FEE, "10")
    )

    private fun canonicalAuthorities(
        identity: EconomicTruthAuthorityState = EconomicTruthAuthorityState.CANONICAL,
        currency: EconomicTruthAuthorityState = EconomicTruthAuthorityState.CANONICAL,
        allocation: EconomicTruthAuthorityState = EconomicTruthAuthorityState.CANONICAL,
        currentness: EconomicTruthAuthorityState = EconomicTruthAuthorityState.CANONICAL,
        reconciliation: FinancialReconciliationStatus? = FinancialReconciliationStatus.FULLY_RECONCILED
    ) = EconomicTruthAuthorityAssessment(
        EconomicTruthAuthorityEvidence(identity, setOf("identity-decision-1")),
        EconomicTruthAuthorityEvidence(currency, setOf("currency-authority-1")),
        EconomicTruthAuthorityEvidence(allocation, setOf("allocation-authority-1")),
        EconomicTruthAuthorityEvidence(currentness, setOf("freshness-policy-1")),
        reconciliation,
        setOf("reconciliation-1")
    )

    private fun evaluate(
        evidence: MarketplaceIndependentEconomicEvidence,
        authorities: EconomicTruthAuthorityAssessment,
        profile: EconomicTruthDecisionProfile = EconomicTruthDecisionProfile.UNIT_ECONOMICS
    ) = EconomicTruthReadinessEvaluator.evaluate(evidence, authorities, profile, evaluatedAt)

    private fun assertBlocked(result: EconomicTruthReadiness, dimension: EconomicTruthDimension, code: EconomicTruthBlockingReasonCode) {
        assertEquals(EconomicTruthReadinessStatus.NOT_READY, result.status)
        assertTrue(EconomicTruthBlockingReason(dimension, code) in result.blockingReasons)
    }

    private fun evidence(vararg facts: MarketplaceIndependentEconomicFact): MarketplaceIndependentEconomicEvidence =
        facts.fold(MarketplaceIndependentEconomicEvidence.empty(subject)) { current, fact -> applied(current, MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(fact)) }

    private fun corrected(
        current: MarketplaceIndependentEconomicEvidence,
        original: MarketplaceIndependentEconomicFact.Component,
        replacement: MarketplaceIndependentEconomicFact.Component,
        id: Int
    ) = applied(
        current,
        MarketplaceIndependentEconomicEvidenceUpdate.Correct(
            MarketplaceEconomicEvidenceCorrection(
                observationId(id), subject, replacement, original.id,
                MarketplaceEconomicEvidenceCorrectionReason.SOURCE_CORRECTION,
                evaluatedAt.minusSeconds(10)
            )
        )
    )

    private fun applied(current: MarketplaceIndependentEconomicEvidence, update: MarketplaceIndependentEconomicEvidenceUpdate) =
        assertIs<MarketplaceIndependentEconomicEvidenceResult.Applied>(MarketplaceIndependentEconomicEvidenceMerger.apply(current, update)).evidence

    private fun component(
        id: Int,
        type: EconomicComponentType,
        amount: String,
        quality: EconomicEvidenceQuality = EconomicEvidenceQuality.CONFIRMED,
        coverage: EconomicComponentCoverage = EconomicComponentCoverage.COMPLETE
    ): MarketplaceIndependentEconomicFact.Component {
        val family = when (type) {
            EconomicComponentType.REVENUE,
            EconomicComponentType.MARKETPLACE_COMMISSION,
            EconomicComponentType.MARKETPLACE_FEE -> MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER
            EconomicComponentType.PRODUCT_COST -> MarketplaceEconomicEvidenceFamily.PRODUCT_COST
            EconomicComponentType.SHIPPING -> MarketplaceEconomicEvidenceFamily.MARKETPLACE_SHIPPING
            EconomicComponentType.TAX -> MarketplaceEconomicEvidenceFamily.FISCAL_TAX
            EconomicComponentType.ADVERTISING -> MarketplaceEconomicEvidenceFamily.ADS_ALLOCATION
            EconomicComponentType.FINANCIAL_COST,
            EconomicComponentType.OTHER_ADJUSTMENT -> error("No governed evidence family currently supports $type")
        }
        val observedAt = evaluatedAt.minusSeconds(60L - id.coerceAtMost(50))
        return MarketplaceIndependentEconomicFact.Component(
            MarketplaceEconomicComponentObservation(
                observationId(id), subject, family,
                EconomicComponent(
                    subject.organizationId,
                    EconomicComponentId.parse("30000000-0000-0000-0000-${id.toString().padStart(12, '0')}"),
                    subject.orderId,
                    type,
                    if (type == EconomicComponentType.REVENUE) EconomicDirection.ADDITION else EconomicDirection.DEDUCTION,
                    MarketplaceMoney.parse(subject.currency, amount),
                    EconomicSource(
                        EconomicSourceKind.MARKETPLACE,
                        EconomicSourceSystemKey("source-$id"),
                        EconomicExternalReferenceState.Present(EconomicExternalReference("fact-$id"))
                    ),
                    observedAt.minusSeconds(1),
                    quality
                ),
                coverage,
                observedAt
            )
        )
    }

    private fun observationId(id: Int) = MarketplaceEconomicEvidenceObservationId.parse(
        "00000000-0000-0000-0000-${id.toString().padStart(12, '0')}"
    )
}
