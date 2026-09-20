package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceAbsenceReason
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceFamily
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.time.format.DateTimeFormatterBuilder

data class FinancialLedgerMaterializationSourceFingerprint(
    val canonicalizationVersion: Int,
    val sha256: String
) {
    init {
        require(canonicalizationVersion == 1) { "Unsupported source fingerprint canonicalization version" }
        require(Regex("[0-9a-f]{64}").matches(sha256)) {
            "Source fingerprint must be lowercase SHA-256 hexadecimal"
        }
    }
    override fun toString(): String = "[REDACTED]"
}

object FinancialLedgerMaterializationSourceFingerprintV1 {
    const val CANONICALIZATION_VERSION = 1
    private val instantFormatter = DateTimeFormatterBuilder().appendInstant(6).toFormatter()

    fun fingerprint(observation: MarketplaceEconomicComponentObservation): FinancialLedgerMaterializationSourceFingerprint {
        val bytes = canonicalJson(observation).toByteArray(StandardCharsets.UTF_8)
        val hash = MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it.toInt() and 0xff) }
        return FinancialLedgerMaterializationSourceFingerprint(CANONICALIZATION_VERSION, hash)
    }

    internal fun canonicalJson(observation: MarketplaceEconomicComponentObservation): String {
        val s = observation.subject
        val c = observation.component
        return buildString {
            append("{\"canonicalizationVersion\":1,\"observationId\":"); json(observation.id.value.toString())
            append(",\"subject\":{\"organizationId\":"); json(s.organizationId.value.toString())
            append(",\"orderId\":"); json(s.orderId.value.toString())
            append(",\"marketplace\":"); json(s.marketplace.value)
            append(",\"externalOrderId\":"); json(s.externalOrderId.value)
            append(",\"currency\":"); json(s.currency.code); append("}")
            append(",\"family\":"); json(family(observation.family))
            append(",\"component\":{\"id\":"); json(c.id.value.toString())
            append(",\"type\":"); json(type(c.type))
            append(",\"direction\":"); json(direction(c.direction))
            append(",\"magnitude\":{\"currency\":"); json(c.magnitude.currency.code)
            append(",\"amount\":"); json(c.magnitude.amount.toPlainString()); append("}")
            append(",\"source\":{\"kind\":"); json(sourceKind(c.source.kind))
            append(",\"systemKey\":"); json(c.source.systemKey.value)
            append(",\"externalReference\":"); externalReference(c.source.externalReference); append("}")
            append(",\"occurredAt\":"); json(instantFormatter.format(c.occurredAt))
            append(",\"quality\":"); json(quality(c.quality)); append("}")
            append(",\"coverageClaim\":"); json(coverage(observation.coverageClaim))
            append(",\"observedAt\":"); json(instantFormatter.format(observation.observedAt)); append("}")
        }
    }

    private fun StringBuilder.externalReference(state: EconomicExternalReferenceState) {
        when (state) {
            is EconomicExternalReferenceState.Present -> {
                append("{\"state\":\"PRESENT\",\"value\":"); json(state.reference.value); append("}")
            }
            is EconomicExternalReferenceState.Absent -> {
                require(state.reason == EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN)
                append("{\"state\":\"ABSENT\",\"reason\":\"INTERNAL_ORIGIN\"}")
            }
        }
    }

    private fun StringBuilder.json(value: String) {
        append('"')
        value.forEach {
            when (it) {
                '"' -> append("\\\""); '\\' -> append("\\\\"); '\b' -> append("\\b")
                '\u000C' -> append("\\f"); '\n' -> append("\\n"); '\r' -> append("\\r"); '\t' -> append("\\t")
                else -> if (it.code < 0x20) append("\\u${it.code.toString(16).padStart(4, '0')}") else append(it)
            }
        }
        append('"')
    }

    private fun family(v: MarketplaceEconomicEvidenceFamily) = when (v) {
        MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER -> "MARKETPLACE_ORDER"
        MarketplaceEconomicEvidenceFamily.MARKETPLACE_PAYMENT -> "MARKETPLACE_PAYMENT"
        MarketplaceEconomicEvidenceFamily.MARKETPLACE_SHIPPING -> "MARKETPLACE_SHIPPING"
        MarketplaceEconomicEvidenceFamily.PRODUCT_COST -> "PRODUCT_COST"
        MarketplaceEconomicEvidenceFamily.FISCAL_INVOICE -> "FISCAL_INVOICE"
        MarketplaceEconomicEvidenceFamily.FISCAL_TAX -> "FISCAL_TAX"
        MarketplaceEconomicEvidenceFamily.ADS_IDENTITY -> "ADS_IDENTITY"
        MarketplaceEconomicEvidenceFamily.ADS_ALLOCATION -> "ADS_ALLOCATION"
    }

    private fun type(v: EconomicComponentType) = when (v) {
        EconomicComponentType.REVENUE -> "REVENUE"
        EconomicComponentType.MARKETPLACE_COMMISSION -> "MARKETPLACE_COMMISSION"
        EconomicComponentType.MARKETPLACE_FEE -> "MARKETPLACE_FEE"
        EconomicComponentType.SHIPPING -> "SHIPPING"
        EconomicComponentType.ADVERTISING -> "ADVERTISING"
        EconomicComponentType.TAX -> "TAX"
        EconomicComponentType.PRODUCT_COST -> "PRODUCT_COST"
        EconomicComponentType.FINANCIAL_COST -> "FINANCIAL_COST"
        EconomicComponentType.OTHER_ADJUSTMENT -> "OTHER_ADJUSTMENT"
    }

    private fun direction(v: EconomicDirection) = when (v) {
        EconomicDirection.ADDITION -> "ADDITION"; EconomicDirection.DEDUCTION -> "DEDUCTION"
    }

    private fun quality(v: EconomicEvidenceQuality) = when (v) {
        EconomicEvidenceQuality.CONFIRMED -> "CONFIRMED"; EconomicEvidenceQuality.ESTIMATED -> "ESTIMATED"
    }

    private fun coverage(v: EconomicComponentCoverage) = when (v) {
        EconomicComponentCoverage.COMPLETE -> "COMPLETE"
        EconomicComponentCoverage.PARTIAL -> "PARTIAL"
        EconomicComponentCoverage.NOT_APPLICABLE, EconomicComponentCoverage.MISSING ->
            error("Ineligible component observation coverage")
    }

    private fun sourceKind(v: EconomicSourceKind) = when (v) {
        EconomicSourceKind.MARKETPLACE -> "MARKETPLACE"; EconomicSourceKind.ERP -> "ERP"
        EconomicSourceKind.MANUAL -> "MANUAL"; EconomicSourceKind.CALCULATED -> "CALCULATED"
    }
}
