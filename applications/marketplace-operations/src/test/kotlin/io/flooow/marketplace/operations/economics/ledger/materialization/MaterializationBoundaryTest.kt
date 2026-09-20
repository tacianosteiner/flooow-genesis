package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.organization.OrganizationId
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import kotlin.test.assertTrue

class GovernedFinancialLedgerComponentMaterializationBoundaryTest {
    @Test
    fun `authorized source is internally verified and preserves payload`() {
        val o = observation()
        val result = GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(
            o.subject.organizationId, o, authorized(o, FinancialLedgerBasis.EXPECTED)
        )
        val plan = assertIs<GovernedFinancialLedgerComponentMaterializationResult.Eligible>(result).plan
        assertEquals(o.id, plan.sourceAuthorityIdentity)
        assertEquals(o.subject, plan.subject)
        assertEquals(FinancialLedgerStage.SALE, plan.stage)
        assertEquals(FinancialLedgerBasis.EXPECTED, plan.basis)
        assertEquals(o.component.direction, plan.direction)
        assertEquals(o.component.magnitude, plan.magnitude)
        assertEquals(o.component.source, plan.source)
        assertEquals(o.component.occurredAt, plan.occurredAt)
        assertEquals(FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(o), plan.verifiedSourceFingerprint)
    }

    @Test
    fun `quality never selects basis`() {
        val confirmed = observation(EconomicEvidenceQuality.CONFIRMED)
        val estimated = observation(EconomicEvidenceQuality.ESTIMATED)
        val expectedPlan = assertIs<GovernedFinancialLedgerComponentMaterializationResult.Eligible>(
            GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(
                confirmed.subject.organizationId, confirmed, authorized(confirmed, FinancialLedgerBasis.EXPECTED)
            )
        ).plan
        val actualPlan = assertIs<GovernedFinancialLedgerComponentMaterializationResult.Eligible>(
            GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(
                estimated.subject.organizationId, estimated, authorized(estimated, FinancialLedgerBasis.ACTUAL)
            )
        ).plan
        assertEquals(FinancialLedgerBasis.EXPECTED, expectedPlan.basis)
        assertEquals(FinancialLedgerBasis.ACTUAL, actualPlan.basis)
    }

    @Test
    fun `typed authority outcomes remain distinct`() {
        val o = observation()
        assertIs<GovernedFinancialLedgerComponentMaterializationResult.NotEligible>(
            GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(
                o.subject.organizationId, o,
                FinancialLedgerComponentMaterializationAuthorityDecision.NotAuthorized(
                    FinancialLedgerComponentMaterializationNotAuthorizedReason.BASIS_AUTHORITY_UNAVAILABLE
                )
            )
        )
        assertIs<GovernedFinancialLedgerComponentMaterializationResult.Failed.Unavailable>(
            GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(
                o.subject.organizationId, o, FinancialLedgerComponentMaterializationAuthorityDecision.Unavailable
            )
        )
        assertFailure(
            o.subject.organizationId,
            o,
            FinancialLedgerComponentMaterializationAuthorityDecision.IntegrityFailure,
            FinancialLedgerComponentMaterializationIntegrityFailureReason.AUTHORITY_INTEGRITY_FAILURE
        )
    }

    @Test
    fun `identity fingerprint policy and tenant mismatches fail closed`() {
        val o = observation()

        val identity = authorized(o, FinancialLedgerBasis.ACTUAL).copy(
            sourceAuthorityIdentity = MarketplaceEconomicEvidenceObservationId.parse(
                "00000000-0000-0000-0000-000000000099"
            )
        )
        assertFailure(o.subject.organizationId, o, identity,
            FinancialLedgerComponentMaterializationIntegrityFailureReason.SOURCE_AUTHORITY_IDENTITY_MISMATCH)

        val fingerprint = authorized(o, FinancialLedgerBasis.ACTUAL).copy(
            expectedSourceFingerprint = FinancialLedgerMaterializationSourceFingerprint(1, "0".repeat(64))
        )
        assertFailure(o.subject.organizationId, o, fingerprint,
            FinancialLedgerComponentMaterializationIntegrityFailureReason.SOURCE_FINGERPRINT_MISMATCH)

        val policy = authorized(o, FinancialLedgerBasis.ACTUAL).copy(
            materializationPolicyVersion =
                FinancialLedgerMaterializationPolicyVersion("marketplace-financial-ledger-materialization/2")
        )
        assertFailure(o.subject.organizationId, o, policy,
            FinancialLedgerComponentMaterializationIntegrityFailureReason.MATERIALIZATION_POLICY_VERSION_UNSUPPORTED)

        assertFailure(
            OrganizationId.parse("00000000-0000-0000-0000-000000000777"), o,
            FinancialLedgerComponentMaterializationAuthorityDecision.NotAuthorized(
                FinancialLedgerComponentMaterializationNotAuthorizedReason.FINANCIAL_OCCURRENCE_AUTHORITY_UNAVAILABLE
            ),
            FinancialLedgerComponentMaterializationIntegrityFailureReason.OPERATIONAL_ORGANIZATION_MISMATCH
        )
    }

    @Test
    fun `stage compatibility is exhaustive and excludes occurrence-only stages`() {
        val expected = mapOf(
            EconomicComponentType.REVENUE to FinancialLedgerStage.SALE,
            EconomicComponentType.MARKETPLACE_COMMISSION to FinancialLedgerStage.MARKETPLACE_COMMISSION,
            EconomicComponentType.MARKETPLACE_FEE to FinancialLedgerStage.MARKETPLACE_FEE,
            EconomicComponentType.SHIPPING to FinancialLedgerStage.SHIPPING,
            EconomicComponentType.ADVERTISING to FinancialLedgerStage.ADVERTISING,
            EconomicComponentType.TAX to FinancialLedgerStage.TAX,
            EconomicComponentType.PRODUCT_COST to FinancialLedgerStage.PRODUCT_COST,
            EconomicComponentType.FINANCIAL_COST to FinancialLedgerStage.FINANCIAL_COST,
            EconomicComponentType.OTHER_ADJUSTMENT to FinancialLedgerStage.OTHER_ADJUSTMENT
        )
        assertEquals(EconomicComponentType.entries.toSet(), expected.keys)
        val actual = expected.keys.associateWith(FinancialLedgerComponentStageCompatibility::stageFor)
        assertEquals(expected, actual)
        assertTrue(FinancialLedgerStage.SETTLEMENT !in actual.values)
        assertTrue(FinancialLedgerStage.PAYMENT_ACCOUNT !in actual.values)
        assertTrue(FinancialLedgerStage.BANK !in actual.values)
    }

    @Test
    fun `not authorized reasons are frozen to controlled version one literals`() {
        assertEquals(
            setOf(
                FinancialLedgerComponentMaterializationNotAuthorizedReason.BASIS_AUTHORITY_UNAVAILABLE,
                FinancialLedgerComponentMaterializationNotAuthorizedReason.UNSUPPORTED_SOURCE_KIND,
                FinancialLedgerComponentMaterializationNotAuthorizedReason.UNSUPPORTED_FINANCIAL_STAGE,
                FinancialLedgerComponentMaterializationNotAuthorizedReason.FINANCIAL_OCCURRENCE_AUTHORITY_UNAVAILABLE
            ),
            FinancialLedgerComponentMaterializationNotAuthorizedReason.entries.toSet()
        )
        assertTrue(
            VerifiedFinancialLedgerComponentMaterializationPlan::class.java.declaredMethods.none {
                it.name == "copy" || it.name.startsWith("copy$")
            }
        )
    }

    @Test
    fun `semantic version grammar is frozen`() {
        assertEquals(
            "marketplace-economic-component/1",
            FinancialLedgerSourceAuthoritySemanticVersion("marketplace-economic-component/1").value
        )
        listOf("", "Marketplace/1", "marketplace component/1", "a".repeat(65)).forEach {
            assertFailsWith<IllegalArgumentException> { FinancialLedgerSourceAuthoritySemanticVersion(it) }
        }
    }

    private fun assertFailure(
        organizationId: OrganizationId,
        observation: MarketplaceEconomicComponentObservation,
        decision: FinancialLedgerComponentMaterializationAuthorityDecision,
        reason: FinancialLedgerComponentMaterializationIntegrityFailureReason
    ) {
        val failure = assertIs<GovernedFinancialLedgerComponentMaterializationResult.Failed.IntegrityFailure>(
            GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(organizationId, observation, decision)
        )
        assertEquals(reason, failure.reason)
    }

    private fun authorized(
        o: MarketplaceEconomicComponentObservation,
        basis: FinancialLedgerBasis
    ) = FinancialLedgerComponentMaterializationAuthorityDecision.Authorized(
        o.id,
        FinancialLedgerSourceAuthoritySemanticVersion("marketplace-economic-component/1"),
        FinancialLedgerMaterializationPolicyVersion.V1,
        FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(o),
        basis
    )

    private fun observation(
        quality: EconomicEvidenceQuality = EconomicEvidenceQuality.CONFIRMED
    ): MarketplaceEconomicComponentObservation {
        val organizationId = OrganizationId.parse("00000000-0000-0000-0000-000000000003")
        val orderId = MarketplaceOrderId.parse("00000000-0000-0000-0000-000000000004")
        val currency = MarketplaceCurrency("BRL")
        val subject = MarketplaceEconomicEvidenceSubject(
            organizationId, orderId, MarketplaceKey("mercado-livre"), MarketplaceExternalOrderId("MLB-123"), currency
        )
        val component = EconomicComponent(
            organizationId,
            EconomicComponentId.parse("00000000-0000-0000-0000-000000000002"),
            orderId,
            EconomicComponentType.REVENUE,
            EconomicDirection.ADDITION,
            MarketplaceMoney.parse(currency, "123.45"),
            EconomicSource(
                EconomicSourceKind.MARKETPLACE,
                EconomicSourceSystemKey("mercado-livre"),
                EconomicExternalReferenceState.Present(EconomicExternalReference("order-123"))
            ),
            Instant.parse("2026-09-13T10:00:00.123456Z"),
            quality
        )
        return MarketplaceEconomicComponentObservation(
            MarketplaceEconomicEvidenceObservationId.parse("00000000-0000-0000-0000-000000000001"),
            subject, MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER, component,
            EconomicComponentCoverage.COMPLETE, Instant.parse("2026-09-13T10:01:00.654321Z")
        )
    }
}
