package io.flooow.marketplace.operations.economics.readiness

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessment
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationDifference
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationLine
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicyVersion
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationSide
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationStatus
import io.flooow.organization.OrganizationId
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class EconomicTruthAuthorityAssemblerTest {
    private val brl = MarketplaceCurrency("BRL")

    @Test
    fun `complete governed inputs assemble without reconciliation`() {
        val result =
            EconomicTruthAuthorityAssembler.assemble(
                inputs = completeInputs(),
                reconciliation = null
            )

        val assembled =
            assertIs<EconomicTruthAuthorityAssemblyResult.Assembled>(result)

        assertEquals(
            EconomicTruthAuthorityState.CANONICAL,
            assembled.authorities.identity.state
        )

        assertNull(assembled.authorities.reconciliation)
    }

    @Test
    fun `missing authority input fails closed instead of inventing unresolved evidence`() {
        val result =
            EconomicTruthAuthorityAssembler.assemble(
                inputs =
                    completeInputs().copy(
                        currency = null,
                        allocation = null
                    ),
                reconciliation = null
            )

        val failed =
            assertIs<EconomicTruthAuthorityAssemblyResult.NotAssembled>(result)

        assertEquals(
            setOf(
                EconomicTruthAuthorityAssemblyFailureReason.CURRENCY_AUTHORITY_UNAVAILABLE,
                EconomicTruthAuthorityAssemblyFailureReason.ALLOCATION_AUTHORITY_UNAVAILABLE
            ),
            failed.reasons
        )
    }

    @Test
    fun `explicit unresolved authority is preserved and is not treated as unavailable`() {
        val result =
            EconomicTruthAuthorityAssembler.assemble(
                inputs =
                    completeInputs().copy(
                        identity =
                            authority(
                                EconomicTruthAuthorityState.UNRESOLVED,
                                "identity:unresolved"
                            )
                    ),
                reconciliation = null
            )

        val assembled =
            assertIs<EconomicTruthAuthorityAssemblyResult.Assembled>(result)

        assertEquals(
            EconomicTruthAuthorityState.UNRESOLVED,
            assembled.authorities.identity.state
        )
    }

    @Test
    fun `real reconciliation assessment is bound through canonical bridge`() {
        val result =
            EconomicTruthAuthorityAssembler.assemble(
                inputs = completeInputs(),
                reconciliation =
                    reconciliation(
                        FinancialReconciliationStatus.DIVERGENCE
                    )
            )

        val assembled =
            assertIs<EconomicTruthAuthorityAssemblyResult.Assembled>(result)

        assertEquals(
            FinancialReconciliationStatus.DIVERGENCE,
            assembled.authorities.reconciliation
        )

        assertTrue(
            assembled.authorities.reconciliationEvidenceReferences.any {
                it.startsWith("financial-trace:")
            }
        )

        assertTrue(
            assembled.authorities.reconciliationEvidenceReferences.any {
                it.startsWith("financial-ledger-entry:")
            }
        )
    }

    private fun completeInputs() =
        EconomicTruthAuthorityInputs(
            identity =
                authority(
                    EconomicTruthAuthorityState.CANONICAL,
                    "identity:test"
                ),
            currency =
                authority(
                    EconomicTruthAuthorityState.CANONICAL,
                    "currency:test"
                ),
            allocation =
                authority(
                    EconomicTruthAuthorityState.CANONICAL,
                    "allocation:test"
                ),
            currentness =
                authority(
                    EconomicTruthAuthorityState.CANONICAL,
                    "currentness:test"
                )
        )

    private fun authority(
        state: EconomicTruthAuthorityState,
        reference: String
    ) =
        EconomicTruthAuthorityEvidence(
            state = state,
            evidenceReferences = setOf(reference)
        )

    private fun reconciliation(
        status: FinancialReconciliationStatus
    ): FinancialReconciliationAssessment {
        val organizationId =
            OrganizationId.parse(
                "10000000-0000-0000-0000-000000000001"
            )

        val traceId =
            FinancialTraceId.parse(
                "20000000-0000-0000-0000-000000000001"
            )

        val orderId =
            MarketplaceOrderId.parse(
                "30000000-0000-0000-0000-000000000001"
            )

        val expectedId =
            FinancialLedgerEntryId.parse(
                "40000000-0000-0000-0000-000000000001"
            )

        val actualId =
            FinancialLedgerEntryId.parse(
                "40000000-0000-0000-0000-000000000002"
            )

        val expected =
            FinancialReconciliationSide.Observed(
                MarketplaceMoney.parse(brl, "-10"),
                listOf(expectedId)
            )

        val actualAmount =
            when (status) {
                FinancialReconciliationStatus.FULLY_RECONCILED -> "-10"
                FinancialReconciliationStatus.DIVERGENCE -> "-12"
                FinancialReconciliationStatus.PARTIALLY_RECONCILED -> "-8"
                FinancialReconciliationStatus.PENDING -> null
            }

        val actual =
            actualAmount?.let {
                FinancialReconciliationSide.Observed(
                    MarketplaceMoney.parse(brl, it),
                    listOf(actualId)
                )
            } ?: FinancialReconciliationSide.NotObserved

        val difference =
            if (actual is FinancialReconciliationSide.Observed) {
                val signed = actual.netAmount - expected.netAmount

                FinancialReconciliationDifference.Compared(
                    signedDifference = signed,
                    absoluteDifference =
                        MarketplaceMoney.parse(
                            brl,
                            signed.amount.abs().toPlainString()
                        ),
                    tolerance = MarketplaceMoney.parse(brl, "0")
                )
            } else {
                FinancialReconciliationDifference.NotComparable
            }

        val line =
            FinancialReconciliationLine(
                stage = FinancialLedgerStage.PRODUCT_COST,
                expected = expected,
                actual = actual,
                difference = difference,
                status = status
            )

        return FinancialReconciliationAssessment(
            organizationId = organizationId,
            traceId = traceId,
            orderId = orderId,
            currency = brl,
            policyVersion =
                FinancialReconciliationPolicyVersion(
                    "authority-assembly-test/1"
                ),
            lines = listOf(line),
            status = status
        )
    }
}