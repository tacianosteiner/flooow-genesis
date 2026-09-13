package io.flooow.marketplace.operations.economics.readiness

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.reconciliation.EconomicLeakageGovernanceBlockingReason
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessment
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationDifference
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationLine
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicyVersion
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationSide
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationStatus
import io.flooow.organization.OrganizationId
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class EconomicTruthReconciliationAuthorityBridgeTest {
    private val organizationId =
        OrganizationId.parse(
            "10000000-0000-0000-0000-000000000001"
        )

    private val traceId =
        FinancialTraceId.parse(
            "20000000-0000-0000-0000-000000000001"
        )

    private val orderId =
        MarketplaceOrderId.parse(
            "30000000-0000-0000-0000-000000000001"
        )

    private val expectedEntryId =
        FinancialLedgerEntryId.parse(
            "40000000-0000-0000-0000-000000000001"
        )

    private val actualEntryId =
        FinancialLedgerEntryId.parse(
            "40000000-0000-0000-0000-000000000002"
        )

    private val brl = MarketplaceCurrency("BRL")

    @Test
    fun `canonical reconciliation becomes the readiness reconciliation authority`() {
        val reconciliation =
            reconciliation(
                FinancialReconciliationStatus.FULLY_RECONCILED
            )

        val bound =
            EconomicTruthReconciliationAuthorityBridge.bind(
                authorities = authorities(),
                reconciliation = reconciliation
            )

        assertEquals(
            FinancialReconciliationStatus.FULLY_RECONCILED,
            bound.reconciliation
        )

        assertEquals(
            EconomicTruthAuthorityState.CANONICAL,
            bound.identity.state
        )

        assertEquals(
            EconomicTruthAuthorityState.CANONICAL,
            bound.currency.state
        )

        assertEquals(
            EconomicTruthAuthorityState.CANONICAL,
            bound.allocation.state
        )

        assertEquals(
            EconomicTruthAuthorityState.CANONICAL,
            bound.currentness.state
        )
    }

    @Test
    fun `bridge preserves and extends reconciliation provenance`() {
        val bound =
            EconomicTruthReconciliationAuthorityBridge.bind(
                authorities = authorities(
                    reconciliationReferences =
                        setOf("upstream-reconciliation:test")
                ),
                reconciliation =
                    reconciliation(
                        FinancialReconciliationStatus.DIVERGENCE
                    )
            )

        assertTrue(
            "upstream-reconciliation:test" in
                bound.reconciliationEvidenceReferences
        )

        assertTrue(
            "financial-trace:${traceId.value}" in
                bound.reconciliationEvidenceReferences
        )

        assertTrue(
            "marketplace-order:${orderId.value}" in
                bound.reconciliationEvidenceReferences
        )

        assertTrue(
            "reconciliation-policy:financial-test/1" in
                bound.reconciliationEvidenceReferences
        )

        assertTrue(
            "financial-ledger-entry:${expectedEntryId.value}" in
                bound.reconciliationEvidenceReferences
        )

        assertTrue(
            "financial-ledger-entry:${actualEntryId.value}" in
                bound.reconciliationEvidenceReferences
        )
    }

    @Test
    fun `same bound authority drives leakage governance mapper`() {
        val bound =
            EconomicTruthReconciliationAuthorityBridge.bind(
                authorities = authorities(),
                reconciliation =
                    reconciliation(
                        FinancialReconciliationStatus.DIVERGENCE
                    )
            )

        val governance =
            EconomicLeakageGovernanceMapper.from(bound)

        assertTrue(governance.permitted)

        assertTrue(
            "financial-trace:${traceId.value}" in
                governance.evidenceReferences
        )

        assertTrue(
            "financial-ledger-entry:${expectedEntryId.value}" in
                governance.evidenceReferences
        )

        assertTrue(
            "financial-ledger-entry:${actualEntryId.value}" in
                governance.evidenceReferences
        )
    }

    @Test
    fun `upstream unresolved identity remains blocked after reconciliation binding`() {
        val bound =
            EconomicTruthReconciliationAuthorityBridge.bind(
                authorities =
                    authorities(
                        identity =
                            EconomicTruthAuthorityState.UNRESOLVED
                    ),
                reconciliation =
                    reconciliation(
                        FinancialReconciliationStatus.DIVERGENCE
                    )
            )

        val governance =
            EconomicLeakageGovernanceMapper.from(bound)

        assertFalse(governance.permitted)

        assertTrue(
            EconomicLeakageGovernanceBlockingReason.IDENTITY_UNRESOLVED in
                governance.blockingReasons
        )
    }

    @Test
    fun `conflicting preexisting reconciliation authority fails closed`() {
        val existing =
            authorities().copy(
                reconciliation =
                    FinancialReconciliationStatus.FULLY_RECONCILED
            )

        assertFailsWith<IllegalArgumentException> {
            EconomicTruthReconciliationAuthorityBridge.bind(
                authorities = existing,
                reconciliation =
                    reconciliation(
                        FinancialReconciliationStatus.DIVERGENCE
                    )
            )
        }
    }

    @Test
    fun `matching preexisting reconciliation authority is idempotent`() {
        val existing =
            authorities().copy(
                reconciliation =
                    FinancialReconciliationStatus.DIVERGENCE,
                reconciliationEvidenceReferences =
                    setOf("existing:test")
            )

        val bound =
            EconomicTruthReconciliationAuthorityBridge.bind(
                authorities = existing,
                reconciliation =
                    reconciliation(
                        FinancialReconciliationStatus.DIVERGENCE
                    )
            )

        assertEquals(
            FinancialReconciliationStatus.DIVERGENCE,
            bound.reconciliation
        )

        assertTrue(
            "existing:test" in
                bound.reconciliationEvidenceReferences
        )
    }

    private fun authorities(
        identity: EconomicTruthAuthorityState =
            EconomicTruthAuthorityState.CANONICAL,
        currency: EconomicTruthAuthorityState =
            EconomicTruthAuthorityState.CANONICAL,
        allocation: EconomicTruthAuthorityState =
            EconomicTruthAuthorityState.CANONICAL,
        currentness: EconomicTruthAuthorityState =
            EconomicTruthAuthorityState.CANONICAL,
        reconciliationReferences: Set<String> =
            emptySet()
    ): EconomicTruthAuthorityAssessment =
        EconomicTruthAuthorityAssessment(
            identity =
                EconomicTruthAuthorityEvidence(
                    identity,
                    setOf("identity:test")
                ),
            currency =
                EconomicTruthAuthorityEvidence(
                    currency,
                    setOf("currency:test")
                ),
            allocation =
                EconomicTruthAuthorityEvidence(
                    allocation,
                    setOf("allocation:test")
                ),
            currentness =
                EconomicTruthAuthorityEvidence(
                    currentness,
                    setOf("currentness:test")
                ),
            reconciliation = null,
            reconciliationEvidenceReferences =
                reconciliationReferences
        )

    private fun reconciliation(
        status: FinancialReconciliationStatus
    ): FinancialReconciliationAssessment {
        val expected =
            FinancialReconciliationSide.Observed(
                MarketplaceMoney.parse(brl, "-10"),
                listOf(expectedEntryId)
            )

        val actualAmount =
            when (status) {
                FinancialReconciliationStatus.FULLY_RECONCILED ->
                    "-10"

                FinancialReconciliationStatus.DIVERGENCE ->
                    "-12"

                FinancialReconciliationStatus.PARTIALLY_RECONCILED ->
                    "-8"

                FinancialReconciliationStatus.PENDING ->
                    null
            }

        val actual =
            actualAmount?.let {
                FinancialReconciliationSide.Observed(
                    MarketplaceMoney.parse(brl, it),
                    listOf(actualEntryId)
                )
            } ?: FinancialReconciliationSide.NotObserved

        val difference =
            if (actual is FinancialReconciliationSide.Observed) {
                val signed =
                    actual.netAmount - expected.netAmount

                FinancialReconciliationDifference.Compared(
                    signedDifference = signed,
                    absoluteDifference =
                        MarketplaceMoney.parse(
                            brl,
                            signed.amount.abs().toPlainString()
                        ),
                    tolerance =
                        MarketplaceMoney.parse(brl, "0")
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
                    "financial-test/1"
                ),
            lines = listOf(line),
            status = status
        )
    }
}