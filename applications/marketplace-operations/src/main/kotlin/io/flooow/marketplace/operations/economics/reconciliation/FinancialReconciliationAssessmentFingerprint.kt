package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.util.UUID

const val FINANCIAL_RECONCILIATION_ASSESSMENT_CANONICALIZATION_VERSION = 1

class FinancialReconciliationAssessmentFingerprint private constructor(
    val canonicalizationVersion: Int,
    val sha256: String
) {
    init {
        require(canonicalizationVersion == FINANCIAL_RECONCILIATION_ASSESSMENT_CANONICALIZATION_VERSION) {
            "Unsupported financial reconciliation assessment canonicalization version"
        }
        require(SHA256_PATTERN.matches(sha256)) {
            "Financial reconciliation assessment fingerprint must be lowercase SHA-256 hex"
        }
    }

    override fun equals(other: Any?): Boolean =
        other is FinancialReconciliationAssessmentFingerprint &&
            canonicalizationVersion == other.canonicalizationVersion &&
            sha256 == other.sha256

    override fun hashCode(): Int = 31 * canonicalizationVersion + sha256.hashCode()

    override fun toString(): String = "[REDACTED]"

    companion object {
        internal fun computedV1(sha256: String): FinancialReconciliationAssessmentFingerprint =
            FinancialReconciliationAssessmentFingerprint(
                FINANCIAL_RECONCILIATION_ASSESSMENT_CANONICALIZATION_VERSION,
                sha256
            )

        /**
         * Rehydrates a validated persisted fingerprint value.
         *
         * This is not an acceptance boundary and does not confer governed
         * authority on caller-supplied content.
         */
        fun parsePersisted(
            canonicalizationVersion: Int,
            sha256: String
        ): FinancialReconciliationAssessmentFingerprint =
            FinancialReconciliationAssessmentFingerprint(
                canonicalizationVersion,
                sha256
            )
    }
}

object FinancialReconciliationAssessmentFingerprinter {
    fun fingerprint(
        assessment: FinancialReconciliationAssessment
    ): FinancialReconciliationAssessmentFingerprint {
        val digest = MessageDigest.getInstance("SHA-256").digest(
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalBytes(assessment)
        )
        return FinancialReconciliationAssessmentFingerprint.computedV1(lowercaseHex(digest))
    }
}

internal object FinancialReconciliationAssessmentCanonicalizerV1 {
    private val stageOrder: Map<FinancialLedgerStage, Int> = listOf(
        FinancialLedgerStage.SALE,
        FinancialLedgerStage.MARKETPLACE_COMMISSION,
        FinancialLedgerStage.MARKETPLACE_FEE,
        FinancialLedgerStage.SHIPPING,
        FinancialLedgerStage.ADVERTISING,
        FinancialLedgerStage.TAX,
        FinancialLedgerStage.PRODUCT_COST,
        FinancialLedgerStage.FINANCIAL_COST,
        FinancialLedgerStage.OTHER_ADJUSTMENT,
        FinancialLedgerStage.SETTLEMENT,
        FinancialLedgerStage.PAYMENT_ACCOUNT,
        FinancialLedgerStage.BANK
    ).withIndex().associate { (index, stage) -> stage to index }

    fun canonicalBytes(assessment: FinancialReconciliationAssessment): ByteArray =
        canonicalJson(assessment).toByteArray(StandardCharsets.UTF_8)

    internal fun canonicalJson(assessment: FinancialReconciliationAssessment): String =
        buildString {
            append('{')
            append("\"canonicalizationVersion\":1")
            append(",\"organizationId\":")
            appendCanonicalJsonString(assessment.organizationId.value.toString())
            append(",\"traceId\":")
            appendCanonicalJsonString(assessment.traceId.valueForPersistence().toString())
            append(",\"orderId\":")
            appendCanonicalJsonString(assessment.orderId.value.toString())
            append(",\"currency\":")
            appendCanonicalJsonString(assessment.currency.code)
            append(",\"policyVersion\":")
            appendCanonicalJsonString(assessment.policyVersion.value)
            append(",\"status\":")
            appendCanonicalJsonString(canonicalStatus(assessment.status))
            append(",\"lines\":[")
            assessment.lines
                .sortedBy { line -> canonicalStageOrder(line.stage) }
                .forEachIndexed { index, line ->
                    if (index > 0) append(',')
                    appendLine(line)
                }
            append("]}")
        }

    internal fun canonicalMoneyText(value: MarketplaceMoney): String {
        val amount = value.amount
        return if (amount.signum() == 0) {
            "0"
        } else {
            amount.stripTrailingZeros().toPlainString()
        }
    }

    internal fun canonicalJsonString(value: String): String =
        buildString { appendCanonicalJsonString(value) }

    internal fun canonicalEntryIdStrings(
        values: Collection<FinancialLedgerEntryId>
    ): List<String> =
        values.sortedWith(FINANCIAL_LEDGER_ENTRY_ID_V1_COMPARATOR)
            .map { it.valueForPersistence().toString() }

    internal fun canonicalStageNames(): List<String> =
        stageOrder.entries.sortedBy { it.value }.map { canonicalStageName(it.key) }

    private fun canonicalStageOrder(stage: FinancialLedgerStage): Int =
        stageOrder[stage]
            ?: error("Financial ledger stage is unsupported by canonicalization v1")

    private fun StringBuilder.appendLine(line: FinancialReconciliationLine) {
        append('{')
        append("\"stage\":")
        appendCanonicalJsonString(canonicalStageName(line.stage))
        append(",\"status\":")
        appendCanonicalJsonString(canonicalStatus(line.status))
        append(",\"expected\":")
        appendSide(line.expected)
        append(",\"actual\":")
        appendSide(line.actual)
        append(",\"difference\":")
        appendDifference(line.difference)
        append('}')
    }

    private fun StringBuilder.appendSide(side: FinancialReconciliationSide) {
        when (side) {
            FinancialReconciliationSide.NotObserved -> append("{\"kind\":\"NOT_OBSERVED\"}")
            is FinancialReconciliationSide.Observed -> {
                append("{\"kind\":\"OBSERVED\",\"netAmount\":")
                appendMoney(side.netAmount)
                append(",\"effectiveEntryIds\":[")
                canonicalEntryIdStrings(side.effectiveEntryIds).forEachIndexed { index, value ->
                    if (index > 0) append(',')
                    appendCanonicalJsonString(value)
                }
                append("]}")
            }
        }
    }

    private fun StringBuilder.appendDifference(difference: FinancialReconciliationDifference) {
        when (difference) {
            FinancialReconciliationDifference.NotComparable ->
                append("{\"kind\":\"NOT_COMPARABLE\"}")
            is FinancialReconciliationDifference.Compared -> {
                append("{\"kind\":\"COMPARED\",\"signedDifference\":")
                appendMoney(difference.signedDifference)
                append(",\"absoluteDifference\":")
                appendMoney(difference.absoluteDifference)
                append(",\"tolerance\":")
                appendMoney(difference.tolerance)
                append('}')
            }
        }
    }

    private fun StringBuilder.appendMoney(value: MarketplaceMoney) {
        append("{\"currency\":")
        appendCanonicalJsonString(value.currency.code)
        append(",\"amount\":")
        appendCanonicalJsonString(canonicalMoneyText(value))
        append('}')
    }
}

private fun canonicalStageName(stage: FinancialLedgerStage): String = when (stage) {
    FinancialLedgerStage.SALE -> "SALE"
    FinancialLedgerStage.MARKETPLACE_COMMISSION -> "MARKETPLACE_COMMISSION"
    FinancialLedgerStage.MARKETPLACE_FEE -> "MARKETPLACE_FEE"
    FinancialLedgerStage.SHIPPING -> "SHIPPING"
    FinancialLedgerStage.ADVERTISING -> "ADVERTISING"
    FinancialLedgerStage.TAX -> "TAX"
    FinancialLedgerStage.PRODUCT_COST -> "PRODUCT_COST"
    FinancialLedgerStage.FINANCIAL_COST -> "FINANCIAL_COST"
    FinancialLedgerStage.OTHER_ADJUSTMENT -> "OTHER_ADJUSTMENT"
    FinancialLedgerStage.SETTLEMENT -> "SETTLEMENT"
    FinancialLedgerStage.PAYMENT_ACCOUNT -> "PAYMENT_ACCOUNT"
    FinancialLedgerStage.BANK -> "BANK"
}

private fun canonicalStatus(status: FinancialReconciliationStatus): String = when (status) {
    FinancialReconciliationStatus.PENDING -> "PENDING"
    FinancialReconciliationStatus.PARTIALLY_RECONCILED -> "PARTIALLY_RECONCILED"
    FinancialReconciliationStatus.DIVERGENCE -> "DIVERGENCE"
    FinancialReconciliationStatus.FULLY_RECONCILED -> "FULLY_RECONCILED"
}

private fun StringBuilder.appendCanonicalJsonString(value: String) {
    append('"')
    var index = 0
    while (index < value.length) {
        val char = value[index]
        when (char) {
            '"' -> append("\\\"")
            '\\' -> append("\\\\")
            '\b' -> append("\\b")
            '\u000C' -> append("\\f")
            '\n' -> append("\\n")
            '\r' -> append("\\r")
            '\t' -> append("\\t")
            else -> when {
                char.code in 0x00..0x1F -> {
                    append("\\u00")
                    append(LOWER_HEX[(char.code ushr 4) and 0xF])
                    append(LOWER_HEX[char.code and 0xF])
                }
                Character.isHighSurrogate(char) -> {
                    require(index + 1 < value.length && Character.isLowSurrogate(value[index + 1])) {
                        "Canonical JSON string contains an unpaired UTF-16 surrogate"
                    }
                    append(char)
                    append(value[index + 1])
                    index += 1
                }
                Character.isLowSurrogate(char) -> {
                    throw IllegalArgumentException(
                        "Canonical JSON string contains an unpaired UTF-16 surrogate"
                    )
                }
                else -> append(char)
            }
        }
        index += 1
    }
    append('"')
}

private fun lowercaseHex(bytes: ByteArray): String = buildString(bytes.size * 2) {
    bytes.forEach { byte ->
        val value = byte.toInt() and 0xFF
        append(LOWER_HEX[value ushr 4])
        append(LOWER_HEX[value and 0xF])
    }
}

private val FINANCIAL_LEDGER_ENTRY_ID_V1_COMPARATOR =
    Comparator<FinancialLedgerEntryId> { left, right ->
        compareUuidUnsignedV1(left.valueForPersistence(), right.valueForPersistence())
    }

private fun compareUuidUnsignedV1(left: UUID, right: UUID): Int {
    val most = java.lang.Long.compareUnsigned(left.mostSignificantBits, right.mostSignificantBits)
    return if (most != 0) {
        most
    } else {
        java.lang.Long.compareUnsigned(left.leastSignificantBits, right.leastSignificantBits)
    }
}

private const val LOWER_HEX = "0123456789abcdef"
private val SHA256_PATTERN = Regex("[0-9a-f]{64}")
