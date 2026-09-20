package io.flooow.marketplace.operations.economics.provider

import io.flooow.integration.connector.ConnectorCapability
import io.flooow.integration.connector.ConnectorRecord
import java.time.Instant
import java.time.LocalDateTime

object OmieTransactionEvidenceV3Capability {
    const val VALUE =
        "marketplace-economic.omie-transaction-evidence.reacquisition-v3"
    val KEY: ConnectorCapability = ConnectorCapability.of(VALUE)
}

class OmieOrderOrigin private constructor(value: String) :
    ProviderSourceText(value, 16) {
    companion object {
        fun of(value: String) = OmieOrderOrigin(normalize(value))
    }
}

class OmieOrderEndReason private constructor(value: String) :
    ProviderSourceText(value, 100) {
    companion object {
        fun of(value: String) = OmieOrderEndReason(normalize(value))
    }
}

class OmieDiscountType private constructor(value: String) :
    ProviderSourceText(value, 16) {
    companion object {
        fun of(value: String) = OmieDiscountType(normalize(value))
    }
}

class OmieOrderItemReference private constructor(value: String) :
    ProviderSourceText(value, 64) {
    companion object {
        fun of(value: String) = OmieOrderItemReference(normalize(value))
    }
}

class OmieOrderItemIntegrationReference private constructor(value: String) :
    ProviderSourceText(value, 30) {
    companion object {
        fun of(value: String) = OmieOrderItemIntegrationReference(normalize(value))
    }
}

class OmieTransactionEvidenceV3Line(
    val internalItemReference: OmieOrderItemReference?,
    val integrationItemReference: OmieOrderItemIntegrationReference?,
    productIdentifiers: Collection<OmieTransactionProductIdentifier>,
    val quantity: ProviderSourceDecimal?,
    val unitValue: ProviderSourceDecimal?,
    val discountType: OmieDiscountType?,
    val discountPercent: ProviderSourceDecimal?,
    val discountValue: ProviderSourceDecimal?,
    val deductionValue: ProviderSourceDecimal?,
    val merchandiseValue: ProviderSourceDecimal?,
    val totalValue: ProviderSourceDecimal?,
    val doNotGenerateFinancial: Boolean?,
    val doNotSumTotal: Boolean?,
    val kit: Boolean?,
    val kitComponent: Boolean?,
    val kitParentItemReference: OmieOrderItemReference?
) {
    val productIdentifiers: List<OmieTransactionProductIdentifier> =
        productIdentifiers.distinct().sortedWith(
            compareBy(
                { it.kind.name },
                { it.encodedForPersistence() }
            )
        )

    init {
        require(this.productIdentifiers.size <= 8) {
            "Too many product identifiers for one Omie order line"
        }
    }

    override fun toString(): String =
        "OmieTransactionEvidenceV3Line([REDACTED])"
}

class OmieTransactionEvidenceV3Record(
    val orderReference: OmieOrderReference,
    val integrationOrderReference: OmieIntegrationReference?,
    val customerOrderReference: OmieCustomerOrderReference?,
    val sourceOrderOrigin: OmieOrderOrigin?,
    val status: OmieOrderStatus?,
    val currency: MercadoLivreSourceCurrency?,
    val providerCreatedLocal: LocalDateTime?,
    val providerModifiedLocal: LocalDateTime?,
    val cancelled: Boolean?,
    val cancelledLocal: LocalDateTime?,
    val invoiced: Boolean?,
    val invoicedLocal: LocalDateTime?,
    val authorized: Boolean?,
    val denied: Boolean?,
    val returned: Boolean?,
    val partiallyReturned: Boolean?,
    val orderEnded: Boolean?,
    val orderEndedReason: OmieOrderEndReason?,
    val orderEndedLocal: LocalDateTime?,
    val orderDiscountType: OmieDiscountType?,
    val orderDiscountPercent: ProviderSourceDecimal?,
    val orderDiscountAmount: ProviderSourceDecimal?,
    val totalOrderAmount: ProviderSourceDecimal?,
    val merchandiseAmount: ProviderSourceDecimal?,
    val discountAmount: ProviderSourceDecimal?,
    val deductionAmount: ProviderSourceDecimal?,
    val freightAmount: ProviderSourceDecimal?,
    val insuranceAmount: ProviderSourceDecimal?,
    val otherExpenseAmount: ProviderSourceDecimal?,
    val marketplaceFeeAmount: ProviderSourceDecimal?,
    val marketplaceShippingAmount: ProviderSourceDecimal?,
    additionalOrderTotals: Map<String, ProviderSourceDecimal>,
    lines: Collection<OmieTransactionEvidenceV3Line>,
    val observedAt: Instant,
    val sourceFingerprint: String,
    val sourceEvidenceSemanticFingerprint: String
) : ConnectorRecord {
    val additionalOrderTotals: Map<String, ProviderSourceDecimal> =
        additionalOrderTotals.toSortedMap()

    val lines: List<OmieTransactionEvidenceV3Line> = lines.toList()

    init {
        require(this.additionalOrderTotals.size <= 128) {
            "Too many Omie additional order totals"
        }
        require(this.lines.size <= 1000) {
            "Too many Omie order lines"
        }
        require(
            providerCreatedLocal == null ||
                providerModifiedLocal == null ||
                !providerModifiedLocal.isBefore(providerCreatedLocal)
        ) {
            "Omie provider modification time precedes creation time"
        }
        require(observedAt.nano % 1_000 == 0) {
            "Provider observation time must use microsecond precision"
        }
        require(Regex("[0-9a-f]{64}").matches(sourceFingerprint)) {
            "Invalid raw provider source fingerprint"
        }
        require(Regex("[0-9a-f]{64}").matches(sourceEvidenceSemanticFingerprint)) {
            "Invalid V3 semantic evidence fingerprint"
        }
    }

    override fun toString(): String =
        "OmieTransactionEvidenceV3Record([REDACTED])"
}
