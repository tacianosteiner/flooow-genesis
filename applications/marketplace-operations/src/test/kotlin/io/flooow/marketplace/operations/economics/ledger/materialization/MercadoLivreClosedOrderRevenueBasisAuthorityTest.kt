package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.EconomicComponent
import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentId
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.EconomicExternalReference
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
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
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.organization.OrganizationId
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs

class MercadoLivreClosedOrderRevenueBasisAuthorityTest {
    @Test
    fun `exact durable closed order proof authorizes actual with exact B3A identity`() {
        val observation = observation()
        val decision = resolve(
            observation,
            MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(
                listOf(proof(observation))
            )
        )

        val authorized =
            assertIs<
                FinancialLedgerComponentMaterializationAuthorityDecision.Authorized
            >(decision)

        assertEquals(observation.id, authorized.sourceAuthorityIdentity)
        assertEquals(
            MercadoLivreClosedOrderRevenueBasisAuthority.AUTHORITY_SEMANTIC_VERSION,
            authorized.sourceAuthoritySemanticVersion
        )
        assertEquals(
            FinancialLedgerMaterializationPolicyVersion.V1,
            authorized.materializationPolicyVersion
        )
        assertEquals(
            FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(
                observation
            ),
            authorized.expectedSourceFingerprint
        )
        assertEquals(FinancialLedgerBasis.ACTUAL, authorized.basis)
    }

    @Test
    fun `authorized decision cannot select stage and B3A derives sale actual`() {
        val observation = observation()

        val authorityDecision = resolve(
            observation,
            MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(
                listOf(proof(observation))
            )
        )

        val result =
            GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(
                observation.subject.organizationId,
                observation,
                authorityDecision
            )

        val plan =
            assertIs<
                GovernedFinancialLedgerComponentMaterializationResult.Eligible
            >(result).plan

        assertEquals(FinancialLedgerStage.SALE, plan.stage)
        assertEquals(FinancialLedgerBasis.ACTUAL, plan.basis)
        assertEquals(
            MercadoLivreClosedOrderRevenueBasisAuthority.AUTHORITY_SEMANTIC_VERSION,
            plan.sourceAuthoritySemanticVersion
        )
    }

    @Test
    fun `missing durable provider proof is basis authority unavailable`() {
        val observation = observation()

        val decision = resolve(
            observation,
            MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound
        )

        val notAuthorized =
            assertIs<
                FinancialLedgerComponentMaterializationAuthorityDecision.NotAuthorized
            >(decision)

        assertEquals(
            FinancialLedgerComponentMaterializationNotAuthorizedReason
                .BASIS_AUTHORITY_UNAVAILABLE,
            notAuthorized.reason
        )
    }

    @Test
    fun `identity and evidence conflict outcomes fail closed`() {
        val observation = observation()

        listOf(
            MercadoLivreClosedOrderRevenuePromotionOutcome.IDENTITY_CONFLICT,
            MercadoLivreClosedOrderRevenuePromotionOutcome.EVIDENCE_CONFLICT
        ).forEach { outcome ->
            val decision = resolve(
                observation,
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(
                    listOf(
                        proof(
                            observation = observation,
                            outcome = outcome
                        )
                    )
                )
            )

            assertIs<
                FinancialLedgerComponentMaterializationAuthorityDecision
                    .IntegrityFailure
            >(decision)
        }
    }

    @Test
    fun `source unavailability and source exception remain unavailable`() {
        val observation = observation()

        assertIs<
            FinancialLedgerComponentMaterializationAuthorityDecision.Unavailable
        >(
            resolve(
                observation,
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.Unavailable
            )
        )

        val throwingSource =
            MercadoLivreClosedOrderRevenueAuthoritySource { _, _, _ ->
                throw IllegalStateException("sensitive persistence detail")
            }

        val decision =
            MercadoLivreClosedOrderRevenueBasisAuthority(throwingSource).resolve(
                observation.subject.organizationId,
                observation
            )

        assertIs<
            FinancialLedgerComponentMaterializationAuthorityDecision.Unavailable
        >(decision)
    }

    @Test
    fun `confirmed marketplace source shape alone never authorizes basis`() {
        var calls = 0

        val source =
            MercadoLivreClosedOrderRevenueAuthoritySource { _, _, _ ->
                calls++
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound
            }

        val authority =
            MercadoLivreClosedOrderRevenueBasisAuthority(source)

        val exactShape = observation()

        val exactDecision = authority.resolve(
            exactShape.subject.organizationId,
            exactShape
        )

        assertIs<
            FinancialLedgerComponentMaterializationAuthorityDecision.NotAuthorized
        >(exactDecision)

        assertEquals(1, calls)

        val unsupportedSourceSystem =
            observation(systemKey = "marketplace-shape-only")

        val unsupportedDecision = authority.resolve(
            unsupportedSourceSystem.subject.organizationId,
            unsupportedSourceSystem
        )

        assertIs<
            FinancialLedgerComponentMaterializationAuthorityDecision.NotAuthorized
        >(unsupportedDecision)

        assertEquals(
            1,
            calls,
            "Unsupported source shape must fail before durable proof lookup"
        )
    }

    @Test
    fun `cross organization context fails before provider proof lookup`() {
        val observation = observation()
        var calls = 0

        val source =
            MercadoLivreClosedOrderRevenueAuthoritySource { _, _, _ ->
                calls++
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(
                    listOf(proof(observation))
                )
            }

        val otherOrganization =
            OrganizationId.parse(
                "00000000-0000-0000-0000-000000000099"
            )

        val decision =
            MercadoLivreClosedOrderRevenueBasisAuthority(source).resolve(
                otherOrganization,
                observation
            )

        assertIs<
            FinancialLedgerComponentMaterializationAuthorityDecision
                .IntegrityFailure
        >(decision)

        assertEquals(0, calls)
    }

    @Test
    fun `caller observation absent from exact durable canonical evidence fails closed`() {
        val observation = observation()

        val differentDurableObservation =
            observation(
                externalOrderId = "MLB-DIFFERENT"
            )

        val decision = resolve(
            observation,
            MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(
                listOf(
                    proof(
                        observation = observation,
                        durableObservation = differentDurableObservation
                    )
                )
            )
        )

        assertIs<
            FinancialLedgerComponentMaterializationAuthorityDecision
                .IntegrityFailure
        >(decision)
    }

    @Test
    fun `provider semantic tuple mismatches fail closed`() {
        val observation = observation()
        val base = proof(observation)

        val otherOrderId =
            MarketplaceOrderId.parse(
                "00000000-0000-0000-0000-000000000099"
            )

        val mismatches =
            listOf(
                base.copy(
                    sourceCapability = "other-capability"
                ),
                base.copy(
                    sourceTotalAmount =
                        MarketplaceMoney.parse(
                            observation.subject.currency,
                            "124.45"
                        )
                ),
                base.copy(
                    sourceDateClosed =
                        observation.component.occurredAt.plusSeconds(1)
                ),
                base.copy(
                    sourceObservedAt =
                        observation.observedAt.plusSeconds(1)
                ),
                base.copy(
                    sourceCurrency = MarketplaceCurrency("USD")
                ),
                base.copy(
                    identityCurrency = MarketplaceCurrency("USD")
                ),
                base.copy(
                    sourceExternalOrderId =
                        MarketplaceExternalOrderId("MLB-OTHER")
                ),
                base.copy(
                    identityExternalOrderId =
                        MarketplaceExternalOrderId("MLB-OTHER")
                ),
                base.copy(
                    marketplaceOrderId = otherOrderId
                ),
                base.copy(
                    identityMarketplace = MarketplaceKey("other-marketplace")
                )
            )

        mismatches.forEach { mismatch ->
            val decision = resolve(
                observation,
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(
                    listOf(mismatch)
                )
            )

            assertIs<
                FinancialLedgerComponentMaterializationAuthorityDecision
                    .IntegrityFailure
            >(decision)
        }
    }

    @Test
    fun `equivalent promoted and duplicate proofs converge but competing successful proof fails`() {
        val observation = observation()

        val equivalent = resolve(
            observation,
            MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(
                listOf(
                    proof(
                        observation,
                        MercadoLivreClosedOrderRevenuePromotionOutcome.PROMOTED
                    ),
                    proof(
                        observation,
                        MercadoLivreClosedOrderRevenuePromotionOutcome.DUPLICATE
                    )
                )
            )
        )

        val authorized =
            assertIs<
                FinancialLedgerComponentMaterializationAuthorityDecision.Authorized
            >(equivalent)

        assertEquals(FinancialLedgerBasis.ACTUAL, authorized.basis)

        val competing = proof(observation).copy(
            sourceTotalAmount =
                MarketplaceMoney.parse(
                    observation.subject.currency,
                    "999.99"
                )
        )

        val conflicting = resolve(
            observation,
            MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(
                listOf(
                    proof(observation),
                    competing
                )
            )
        )

        assertIs<
            FinancialLedgerComponentMaterializationAuthorityDecision
                .IntegrityFailure
        >(conflicting)
    }

    private fun resolve(
        observation: MarketplaceEconomicComponentObservation,
        result: MercadoLivreClosedOrderRevenueAuthoritySourceResult
    ): FinancialLedgerComponentMaterializationAuthorityDecision {
        val source =
            MercadoLivreClosedOrderRevenueAuthoritySource { _, _, _ ->
                result
            }

        return MercadoLivreClosedOrderRevenueBasisAuthority(source).resolve(
            observation.subject.organizationId,
            observation
        )
    }

    private fun proof(
        observation: MarketplaceEconomicComponentObservation,
        outcome: MercadoLivreClosedOrderRevenuePromotionOutcome =
            MercadoLivreClosedOrderRevenuePromotionOutcome.PROMOTED,
        durableObservation: MarketplaceEconomicComponentObservation =
            observation
    ): MercadoLivreClosedOrderRevenueProviderProof =
        MercadoLivreClosedOrderRevenueProviderProof(
            durableObservation = durableObservation,
            organizationId = observation.subject.organizationId,
            marketplaceOrderId = observation.subject.orderId,
            identityMarketplace = observation.subject.marketplace,
            identityExternalOrderId = observation.subject.externalOrderId,
            identityCurrency = observation.subject.currency,
            sourceCapability =
                MercadoLivreClosedOrderRevenueBasisAuthority.SOURCE_CAPABILITY,
            sourceExternalOrderId = observation.subject.externalOrderId,
            sourceCurrency = observation.subject.currency,
            sourceTotalAmount = observation.component.magnitude,
            sourceDateClosed = observation.component.occurredAt,
            sourceObservedAt = observation.observedAt,
            outcome = outcome
        )

    private fun observation(
        externalOrderId: String = "MLB-123",
        systemKey: String = "br.com.mercadolivre"
    ): MarketplaceEconomicComponentObservation {
        val organizationId =
            OrganizationId.parse(
                "00000000-0000-0000-0000-000000000003"
            )

        val orderId =
            MarketplaceOrderId.parse(
                "00000000-0000-0000-0000-000000000004"
            )

        val currency = MarketplaceCurrency("BRL")

        val subject =
            MarketplaceEconomicEvidenceSubject(
                organizationId,
                orderId,
                MarketplaceKey("mercado-livre"),
                MarketplaceExternalOrderId(externalOrderId),
                currency
            )

        val component =
            EconomicComponent(
                organizationId,
                EconomicComponentId.parse(
                    "00000000-0000-0000-0000-000000000002"
                ),
                orderId,
                EconomicComponentType.REVENUE,
                EconomicDirection.ADDITION,
                MarketplaceMoney.parse(currency, "123.45"),
                EconomicSource(
                    EconomicSourceKind.MARKETPLACE,
                    EconomicSourceSystemKey(systemKey),
                    EconomicExternalReferenceState.Present(
                        EconomicExternalReference(externalOrderId)
                    )
                ),
                Instant.parse("2026-09-17T10:00:00.123456Z"),
                EconomicEvidenceQuality.CONFIRMED
            )

        return MarketplaceEconomicComponentObservation(
            MarketplaceEconomicEvidenceObservationId.parse(
                "00000000-0000-0000-0000-000000000001"
            ),
            subject,
            MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
            component,
            EconomicComponentCoverage.PARTIAL,
            Instant.parse("2026-09-17T10:01:00.654321Z")
        )
    }
}