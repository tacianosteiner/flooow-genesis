package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.organization.OrganizationId
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class EconomicLeakageInterpretationTest {
    private val organizationId =
        OrganizationId.parse("10000000-0000-0000-0000-000000000001")

    private val traceId =
        FinancialTraceId.parse("20000000-0000-0000-0000-000000000001")

    private val orderId =
        MarketplaceOrderId.parse("30000000-0000-0000-0000-000000000001")

    private val brl = MarketplaceCurrency("BRL")

    @Test
    fun `equal governed expected and actual produces zero material leakage`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.SALE,
                expected = "100",
                actual = "100",
                status = FinancialReconciliationStatus.FULLY_RECONCILED
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.NO_MATERIAL_VARIANCE,
            interpreted.interpretation
        )
        assertNull(interpreted.quantifiedLeakage)
        assertEquals(money("0"), result.totalQuantifiedLeakage)
    }

    @Test
    fun `higher governed product cost is quantified unfavorable leakage`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.PRODUCT_COST,
                expected = "-10",
                actual = "-12",
                status = FinancialReconciliationStatus.DIVERGENCE
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.UNFAVORABLE_LEAKAGE,
            interpreted.interpretation
        )
        assertEquals(money("-2"), interpreted.signedVariance)
        assertEquals(money("2"), interpreted.absoluteVariance)
        assertEquals(money("2"), interpreted.quantifiedLeakage)
        assertEquals(money("2"), result.totalQuantifiedLeakage)
    }

    @Test
    fun `partial product cost cannot be called favorable before reconciliation closes`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.PRODUCT_COST,
                expected = "-10",
                actual = "-8",
                status = FinancialReconciliationStatus.PARTIALLY_RECONCILED
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.UNQUANTIFIED,
            interpreted.interpretation
        )
        assertEquals(
            EconomicLeakageBlockingReason.RECONCILIATION_INCOMPLETE,
            interpreted.blockingReason
        )
        assertEquals(money("2"), interpreted.signedVariance)
        assertEquals(money("2"), interpreted.absoluteVariance)
        assertNull(interpreted.quantifiedLeakage)
        assertNull(result.totalQuantifiedLeakage)
    }

    @Test
    fun `partial revenue shortfall remains unquantified until reconciliation closes`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.SALE,
                expected = "100",
                actual = "90",
                status = FinancialReconciliationStatus.PARTIALLY_RECONCILED
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.UNQUANTIFIED,
            interpreted.interpretation
        )
        assertEquals(
            EconomicLeakageBlockingReason.RECONCILIATION_INCOMPLETE,
            interpreted.blockingReason
        )
        assertEquals(money("-10"), interpreted.signedVariance)
        assertNull(interpreted.quantifiedLeakage)
        assertNull(result.totalQuantifiedLeakage)
    }

    @Test
    fun `closed favorable sale divergence remains favorable and never becomes leakage`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.SALE,
                expected = "100",
                actual = "110",
                status = FinancialReconciliationStatus.DIVERGENCE
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.FAVORABLE_VARIANCE,
            interpreted.interpretation
        )
        assertEquals(money("10"), interpreted.signedVariance)
        assertNull(interpreted.quantifiedLeakage)
        assertEquals(money("0"), result.totalQuantifiedLeakage)
    }

    @Test
    fun `missing actual is blocked and never converted into zero`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.SHIPPING,
                expected = "-10",
                actual = null,
                status = FinancialReconciliationStatus.PENDING
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.UNQUANTIFIED,
            interpreted.interpretation
        )
        assertEquals(
            EconomicLeakageBlockingReason.MISSING_ACTUAL,
            interpreted.blockingReason
        )
        assertEquals(money("-10"), interpreted.expected)
        assertNull(interpreted.actual)
        assertNull(interpreted.quantifiedLeakage)
        assertNull(result.totalQuantifiedLeakage)
    }

    @Test
    fun `missing expected is blocked and unexpected actual is not invented as leakage`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.MARKETPLACE_FEE,
                expected = null,
                actual = "-3",
                status = FinancialReconciliationStatus.DIVERGENCE
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.UNQUANTIFIED,
            interpreted.interpretation
        )
        assertEquals(
            EconomicLeakageBlockingReason.MISSING_EXPECTED,
            interpreted.blockingReason
        )
        assertNull(interpreted.quantifiedLeakage)
        assertNull(result.totalQuantifiedLeakage)
    }

    @Test
    fun `tax divergence remains unquantified because economic semantics are unsupported`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.TAX,
                expected = "-5",
                actual = "-7",
                status = FinancialReconciliationStatus.DIVERGENCE
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.UNQUANTIFIED,
            interpreted.interpretation
        )
        assertEquals(
            EconomicLeakageBlockingReason.UNSUPPORTED_STAGE,
            interpreted.blockingReason
        )
        assertNull(interpreted.quantifiedLeakage)
        assertNull(result.totalQuantifiedLeakage)
    }

    @Test
    fun `advertising variance is not silently called leakage`() {
        val result = interpret(
            line(
                stage = FinancialLedgerStage.ADVERTISING,
                expected = "-10",
                actual = "-30",
                status = FinancialReconciliationStatus.DIVERGENCE
            )
        )

        assertEquals(
            EconomicLeakageInterpretationStatus.UNQUANTIFIED,
            result.lines.single().interpretation
        )
        assertEquals(
            EconomicLeakageBlockingReason.UNSUPPORTED_STAGE,
            result.lines.single().blockingReason
        )
    }

    @Test
    fun `governance blocker prevents mathematically closed divergence from becoming leakage`() {
        val line = line(
            stage = FinancialLedgerStage.PRODUCT_COST,
            expected = "-10",
            actual = "-12",
            status = FinancialReconciliationStatus.DIVERGENCE
        )

        val assessment = FinancialReconciliationAssessment(
            organizationId = organizationId,
            traceId = traceId,
            orderId = orderId,
            currency = brl,
            policyVersion = FinancialReconciliationPolicyVersion("leakage-test/1"),
            lines = listOf(line),
            status = line.status
        )

        val result = MarketplaceEconomicLeakageInterpretation.interpret(
            assessment,
            EconomicLeakageGovernance.blocked(
                setOf(EconomicLeakageGovernanceBlockingReason.IDENTITY_UNRESOLVED),
                setOf("identity:unresolved")
            )
        )

        val interpreted = result.lines.single()

        assertEquals(
            EconomicLeakageInterpretationStatus.UNQUANTIFIED,
            interpreted.interpretation
        )
        assertEquals(
            EconomicLeakageBlockingReason.GOVERNANCE_NOT_SATISFIED,
            interpreted.blockingReason
        )
        assertNull(interpreted.quantifiedLeakage)
        assertNull(result.totalQuantifiedLeakage)
        assertEquals(
            setOf(EconomicLeakageGovernanceBlockingReason.IDENTITY_UNRESOLVED),
            result.governance.blockingReasons
        )
    }

    @Test
    fun `expected and actual evidence identifiers survive interpretation`() {
        val expectedId = id(11)
        val actualId = id(12)

        val result = interpret(
            line(
                stage = FinancialLedgerStage.MARKETPLACE_COMMISSION,
                expected = "-10",
                actual = "-12",
                status = FinancialReconciliationStatus.DIVERGENCE,
                expectedId = expectedId,
                actualId = actualId
            )
        )

        val interpreted = result.lines.single()

        assertEquals(listOf(expectedId), interpreted.expectedEntryIds)
        assertEquals(listOf(actualId), interpreted.actualEntryIds)
    }

    private fun interpret(
        line: FinancialReconciliationLine
    ): EconomicLeakageAssessment =
        MarketplaceEconomicLeakageInterpretation.interpret(
            FinancialReconciliationAssessment(
                organizationId = organizationId,
                traceId = traceId,
                orderId = orderId,
                currency = brl,
                policyVersion = FinancialReconciliationPolicyVersion("leakage-test/1"),
                lines = listOf(line),
                status = line.status
            ),
            EconomicLeakageGovernance.permitted(
                setOf(
                    "identity:test",
                    "currency:test",
                    "allocation:test",
                    "currentness:test"
                )
            )
        )

    private fun line(
        stage: FinancialLedgerStage,
        expected: String?,
        actual: String?,
        status: FinancialReconciliationStatus,
        expectedId: FinancialLedgerEntryId = id(1),
        actualId: FinancialLedgerEntryId = id(2)
    ): FinancialReconciliationLine {
        val expectedSide = expected?.let {
            FinancialReconciliationSide.Observed(money(it), listOf(expectedId))
        } ?: FinancialReconciliationSide.NotObserved

        val actualSide = actual?.let {
            FinancialReconciliationSide.Observed(money(it), listOf(actualId))
        } ?: FinancialReconciliationSide.NotObserved

        val difference =
            if (
                expectedSide is FinancialReconciliationSide.Observed &&
                actualSide is FinancialReconciliationSide.Observed
            ) {
                val signed = actualSide.netAmount - expectedSide.netAmount
                FinancialReconciliationDifference.Compared(
                    signedDifference = signed,
                    absoluteDifference = MarketplaceMoney.parse(
                        brl,
                        signed.amount.abs().toPlainString()
                    ),
                    tolerance = money("0")
                )
            } else {
                FinancialReconciliationDifference.NotComparable
            }

        return FinancialReconciliationLine(
            stage = stage,
            expected = expectedSide,
            actual = actualSide,
            difference = difference,
            status = status
        )
    }

    private fun money(value: String): MarketplaceMoney =
        MarketplaceMoney.parse(brl, value)

    private fun id(suffix: Int): FinancialLedgerEntryId =
        FinancialLedgerEntryId.parse(
            "40000000-0000-0000-0000-${suffix.toString().padStart(12, '0')}"
        )
}