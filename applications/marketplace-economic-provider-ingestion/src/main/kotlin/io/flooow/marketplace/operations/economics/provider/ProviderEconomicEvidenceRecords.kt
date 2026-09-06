package io.flooow.marketplace.operations.economics.provider

import io.flooow.integration.connector.ConnectorCapability
import io.flooow.integration.connector.ConnectorRecord
import java.math.BigDecimal
import java.time.Instant
import java.time.LocalDate
import java.text.Normalizer

object MarketplaceEconomicProductCostCapability {
    const val VALUE = "marketplace-economic.product-cost"
    val KEY: ConnectorCapability = ConnectorCapability.of(VALUE)
}

sealed class ProviderSourceText protected constructor(
    private val encoded: String,
    maximumBytes: Int
) {
    init {
        require(encoded.isNotEmpty() && encoded == encoded.trim()) {
            "Invalid provider source text"
        }
        require(encoded.none(Char::isISOControl)) { "Invalid provider source text" }
        require(encoded.toByteArray(Charsets.UTF_8).size <= maximumBytes) {
            "Invalid provider source text"
        }
    }

    fun encodedForPersistence(): String = encoded

    override fun equals(other: Any?): Boolean =
        other != null && javaClass == other.javaClass &&
            other is ProviderSourceText && encoded == other.encoded

    override fun hashCode(): Int = 31 * javaClass.hashCode() + encoded.hashCode()
    override fun toString(): String = "[REDACTED]"

    companion object {
        fun normalize(value: String): String =
            Normalizer.normalize(value, Normalizer.Form.NFC)
    }
}

class OmieProductReference private constructor(value: String) :
    ProviderSourceText(value, 64) {
    companion object {
        fun of(value: String) = OmieProductReference(normalize(value))
    }
}

class OmieIntegrationReference private constructor(value: String) :
    ProviderSourceText(value, 60) {
    companion object {
        fun of(value: String) = OmieIntegrationReference(normalize(value))
    }
}

class OmieDisplayedProductCode private constructor(value: String) :
    ProviderSourceText(value, 60) {
    companion object {
        fun of(value: String) = OmieDisplayedProductCode(normalize(value))
    }
}

class OmieLocationReference private constructor(value: String) :
    ProviderSourceText(value, 64) {
    companion object {
        fun of(value: String) = OmieLocationReference(normalize(value))
    }
}

class ProviderSourceDecimal private constructor(private val value: BigDecimal) {
    fun valueForPersistence(): BigDecimal = value
    fun canonicalValue(): String = value.toPlainString()

    override fun equals(other: Any?): Boolean =
        other is ProviderSourceDecimal && value.compareTo(other.value) == 0

    override fun hashCode(): Int = value.stripTrailingZeros().hashCode()
    override fun toString(): String = "[REDACTED]"

    companion object {
        private val canonical = Regex("-?(0|[1-9][0-9]*)(\\.[0-9]{1,6})?")
        private val maximumMagnitude = BigDecimal("1000000000000000000")

        fun parse(value: String): ProviderSourceDecimal {
            require(canonical.matches(value)) { "Invalid provider decimal" }
            var normalized = BigDecimal(value).stripTrailingZeros()
            if (normalized.scale() < 0) normalized = normalized.setScale(0)
            if (normalized.compareTo(BigDecimal.ZERO) == 0) normalized = BigDecimal.ZERO
            require(normalized.scale() <= 6 && normalized.abs() < maximumMagnitude) {
                "Invalid provider decimal"
            }
            return ProviderSourceDecimal(normalized)
        }
    }
}

class OmieProductCostSourceRecord(
    val productReference: OmieProductReference,
    val integrationReference: OmieIntegrationReference?,
    val displayedProductCode: OmieDisplayedProductCode?,
    val locationReference: OmieLocationReference,
    val unitCmc: ProviderSourceDecimal?,
    val stockBalance: ProviderSourceDecimal?,
    val physicalStock: ProviderSourceDecimal?,
    val reservedStock: ProviderSourceDecimal?,
    val positionDate: LocalDate,
    val observedAt: Instant
) : ConnectorRecord {
    override fun toString(): String = "OmieProductCostSourceRecord([REDACTED])"
}