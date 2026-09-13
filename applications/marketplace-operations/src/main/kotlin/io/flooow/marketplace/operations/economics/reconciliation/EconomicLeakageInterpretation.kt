package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import java.util.Collections

/**
 * Economic interpretation is downstream from financial reconciliation.
 *
 * A financial variance is not automatically economic leakage.
 * Only stages with explicit net-economic semantics are interpreted.
 */
enum class EconomicLeakageInterpretationStatus {
    NO_MATERIAL_VARIANCE,
    UNFAVORABLE_LEAKAGE,
    FAVORABLE_VARIANCE,
    UNQUANTIFIED
}

enum class EconomicLeakageBlockingReason {
    GOVERNANCE_NOT_SATISFIED,
    MISSING_EXPECTED,
    MISSING_ACTUAL,
    RECONCILIATION_INCOMPLETE,
    UNSUPPORTED_STAGE
}

class EconomicLeakageLine internal constructor(
    val stage: FinancialLedgerStage,
    val reconciliationStatus: FinancialReconciliationStatus,
    val interpretation: EconomicLeakageInterpretationStatus,
    val expected: MarketplaceMoney?,
    val actual: MarketplaceMoney?,
    val signedVariance: MarketplaceMoney?,
    val absoluteVariance: MarketplaceMoney?,
    val quantifiedLeakage: MarketplaceMoney?,
    val blockingReason: EconomicLeakageBlockingReason?,
    expectedEntryIds: Collection<FinancialLedgerEntryId>,
    actualEntryIds: Collection<FinancialLedgerEntryId>
) {
    val expectedEntryIds: List<FinancialLedgerEntryId> =
        Collections.unmodifiableList(expectedEntryIds.toList())

    val actualEntryIds: List<FinancialLedgerEntryId> =
        Collections.unmodifiableList(actualEntryIds.toList())

    init {
        require(
            (interpretation == EconomicLeakageInterpretationStatus.UNQUANTIFIED) ==
                (blockingReason != null)
        ) {
            "Unquantified leakage interpretation requires exactly one blocking reason"
        }

        require(
            (interpretation == EconomicLeakageInterpretationStatus.UNFAVORABLE_LEAKAGE) ==
                (quantifiedLeakage != null)
        ) {
            "Only unfavorable leakage may expose quantified leakage"
        }

        if (quantifiedLeakage != null) {
            require(quantifiedLeakage.amount.signum() >= 0) {
                "Quantified leakage must not be negative"
            }
        }

        if (signedVariance != null && absoluteVariance != null) {
            require(signedVariance.currency == absoluteVariance.currency) {
                "Leakage variance currencies must match"
            }
            require(absoluteVariance.amount.compareTo(signedVariance.amount.abs()) == 0) {
                "Absolute leakage variance must match signed variance"
            }
        }
    }

    override fun toString(): String = "[REDACTED]"
}

class EconomicLeakageAssessment internal constructor(
    val reconciliation: FinancialReconciliationAssessment,
    val governance: EconomicLeakageGovernance,
    lines: Collection<EconomicLeakageLine>,
    val totalQuantifiedLeakage: MarketplaceMoney?
) {
    val lines: List<EconomicLeakageLine> = Collections.unmodifiableList(
        lines.sortedBy { it.stage.ordinal }
    )

    init {
        require(lines.size == reconciliation.lines.size) {
            "Economic leakage interpretation must preserve every reconciliation line"
        }
        require(lines.map { it.stage } == reconciliation.lines.map { it.stage }) {
            "Economic leakage interpretation must preserve reconciliation stage ordering"
        }

        val quantified = lines.mapNotNull { it.quantifiedLeakage }
        if (quantified.isEmpty()) {
            require(totalQuantifiedLeakage == null || totalQuantifiedLeakage.amount.signum() == 0) {
                "Leakage aggregate without quantified leakage must be zero or absent"
            }
        } else {
            require(totalQuantifiedLeakage != null) {
                "Quantified leakage lines require aggregate leakage"
            }
            require(quantified.all { it.currency == reconciliation.currency }) {
                "Leakage aggregate currency must match reconciliation currency"
            }
        }
    }

    override fun toString(): String = "[REDACTED]"
}

object MarketplaceEconomicLeakageInterpretation {
    /**
     * Interprets the already-governed financial reconciliation.
     *
     * No provider access, persistence mutation, recommendation, recovery authority,
     * causal claim, currency inference, identity inference, or allocation inference
     * occurs here.
     */
    fun interpret(
        assessment: FinancialReconciliationAssessment,
        governance: EconomicLeakageGovernance
    ): EconomicLeakageAssessment {
        if (!governance.permitted) {
            return EconomicLeakageAssessment(
                reconciliation = assessment,
                governance = governance,
                lines = assessment.lines.map { line ->
                    val expected = line.expected as? FinancialReconciliationSide.Observed
                    val actual = line.actual as? FinancialReconciliationSide.Observed

                    blocked(
                        line = line,
                        expected = expected,
                        actual = actual,
                        reason = EconomicLeakageBlockingReason.GOVERNANCE_NOT_SATISFIED
                    )
                },
                totalQuantifiedLeakage = null
            )
        }

        val lines = assessment.lines.map(::interpretLine)

        val quantified = lines.mapNotNull { it.quantifiedLeakage }
        val total = when {
            quantified.isNotEmpty() ->
                quantified.reduce { accumulated, value -> accumulated + value }

            lines.any {
                it.stage in supportedEconomicStages &&
                    it.interpretation != EconomicLeakageInterpretationStatus.UNQUANTIFIED
            } ->
                MarketplaceMoney.parse(assessment.currency, "0")

            else -> null
        }

        return EconomicLeakageAssessment(
            reconciliation = assessment,
            governance = governance,
            lines = lines,
            totalQuantifiedLeakage = total
        )
    }

    private fun interpretLine(
        line: FinancialReconciliationLine
    ): EconomicLeakageLine {
        val expected = line.expected as? FinancialReconciliationSide.Observed
        val actual = line.actual as? FinancialReconciliationSide.Observed

        if (expected == null) {
            return blocked(
                line = line,
                expected = null,
                actual = actual,
                reason = EconomicLeakageBlockingReason.MISSING_EXPECTED
            )
        }

        if (actual == null) {
            return blocked(
                line = line,
                expected = expected,
                actual = null,
                reason = EconomicLeakageBlockingReason.MISSING_ACTUAL
            )
        }

        if (line.stage !in supportedEconomicStages) {
            return blocked(
                line = line,
                expected = expected,
                actual = actual,
                reason = EconomicLeakageBlockingReason.UNSUPPORTED_STAGE
            )
        }

        if (line.status == FinancialReconciliationStatus.PARTIALLY_RECONCILED) {
            return blocked(
                line = line,
                expected = expected,
                actual = actual,
                reason = EconomicLeakageBlockingReason.RECONCILIATION_INCOMPLETE
            )
        }

        val difference = line.difference as FinancialReconciliationDifference.Compared

        val interpretation = when {
            difference.absoluteDifference.amount <= difference.tolerance.amount ->
                EconomicLeakageInterpretationStatus.NO_MATERIAL_VARIANCE

            difference.signedDifference.amount.signum() < 0 &&
                line.status == FinancialReconciliationStatus.DIVERGENCE ->
                EconomicLeakageInterpretationStatus.UNFAVORABLE_LEAKAGE

            difference.signedDifference.amount.signum() > 0 &&
                line.status == FinancialReconciliationStatus.DIVERGENCE ->
                EconomicLeakageInterpretationStatus.FAVORABLE_VARIANCE

            else ->
                EconomicLeakageInterpretationStatus.NO_MATERIAL_VARIANCE
        }

        return EconomicLeakageLine(
            stage = line.stage,
            reconciliationStatus = line.status,
            interpretation = interpretation,
            expected = expected.netAmount,
            actual = actual.netAmount,
            signedVariance = difference.signedDifference,
            absoluteVariance = difference.absoluteDifference,
            quantifiedLeakage = if (
                interpretation == EconomicLeakageInterpretationStatus.UNFAVORABLE_LEAKAGE
            ) {
                difference.absoluteDifference
            } else {
                null
            },
            blockingReason = null,
            expectedEntryIds = expected.effectiveEntryIds,
            actualEntryIds = actual.effectiveEntryIds
        )
    }

    private fun blocked(
        line: FinancialReconciliationLine,
        expected: FinancialReconciliationSide.Observed?,
        actual: FinancialReconciliationSide.Observed?,
        reason: EconomicLeakageBlockingReason
    ): EconomicLeakageLine {
        val difference = line.difference as? FinancialReconciliationDifference.Compared

        return EconomicLeakageLine(
            stage = line.stage,
            reconciliationStatus = line.status,
            interpretation = EconomicLeakageInterpretationStatus.UNQUANTIFIED,
            expected = expected?.netAmount,
            actual = actual?.netAmount,
            signedVariance = difference?.signedDifference,
            absoluteVariance = difference?.absoluteDifference,
            quantifiedLeakage = null,
            blockingReason = reason,
            expectedEntryIds = expected?.effectiveEntryIds.orEmpty(),
            actualEntryIds = actual?.effectiveEntryIds.orEmpty()
        )
    }

    private val supportedEconomicStages = setOf(
        FinancialLedgerStage.SALE,
        FinancialLedgerStage.MARKETPLACE_COMMISSION,
        FinancialLedgerStage.MARKETPLACE_FEE,
        FinancialLedgerStage.SHIPPING,
        FinancialLedgerStage.PRODUCT_COST,
        FinancialLedgerStage.FINANCIAL_COST
    )
}