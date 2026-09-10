package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.provider.MarketplaceEconomicOrderSourceCapability
import io.flooow.marketplace.operations.identity.*
import io.flooow.organization.OrganizationId
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.math.BigDecimal
import java.sql.DriverManager
import java.sql.ResultSet
import java.time.Instant

/** Read-only reconstruction of the existing V026 Omie evidence table. */
class PostgresOmieIdentityEvidenceReader(
    private val configuration: PostgresConfiguration,
    private val connectionId: IntegrationConnectionId? = null
) : OmieIdentityEvidenceReader {
    override fun read(organizationId: OrganizationId, limit: Int): OmieIdentityEvidenceRead {
        require(limit in 1..10_000)
        val rows = mutableListOf<OmieRow>()
        DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { c ->
            c.prepareStatement(
                "SELECT source_order_ref,source_integration_ref,source_customer_order_ref,occurred_at," +
                    "currency,total_amount,product_refs,observed_at,source_fingerprint " +
                    "FROM integration_omie_transaction_evidence WHERE organization_id=? " +
                    "AND capability=? AND (? IS NULL OR connection_id=?) " +
                    "ORDER BY source_order_ref,observed_at DESC,input_progress_version DESC,record_ordinal " +
                    "LIMIT ?"
            ).use { s ->
                s.setObject(1, organizationId.value)
                s.setString(2, "marketplace-economic.omie-transaction-evidence")
                s.setObject(3, connectionId?.value)
                s.setObject(4, connectionId?.value)
                s.setInt(5, limit)
                s.executeQuery().use { rs -> while (rs.next()) rows += readRow(rs) }
            }
        }
        val distinctRows = rows.distinctBy { it.orderRef to it.fingerprint }
        val records = distinctRows.mapNotNull { it.toDomain(organizationId) }
        return OmieIdentityEvidenceRead(records, distinctRows.size, distinctRows.size - records.size)
    }

    private fun readRow(rs: ResultSet) = OmieRow(
        rs.getString("source_order_ref").trim(),
        rs.getString("source_integration_ref")?.trim()?.takeIf { it.isNotEmpty() },
        rs.getString("source_customer_order_ref")?.trim()?.takeIf { it.isNotEmpty() },
        rs.getTimestamp("occurred_at")?.toInstant(),
        rs.getString("currency")?.trim(),
        rs.getBigDecimal("total_amount"),
        rs.getString("product_refs"),
        rs.getTimestamp("observed_at").toInstant(),
        rs.getString("source_fingerprint")
    )

    internal data class OmieRow(
        val orderRef: String, val integration: String?, val customer: String?, val occurred: Instant?,
        val currency: String?, val amount: BigDecimal?, val products: String, val observed: Instant,
        val fingerprint: String
    ) {
        fun toDomain(org: OrganizationId): OmieSalesOrderEvidence? {
            val productQuantities = Json.parseToJsonElement(products).jsonArray.mapNotNull { element ->
                val obj = element.jsonObject
                val code = obj["code"]?.jsonPrimitive?.content?.trim()
                val quantity = obj["quantity"]?.jsonPrimitive?.content?.toBigDecimalOrNull()
                if (code.isNullOrBlank() || quantity == null) null else code to quantity
            }.toMap()
            val at = occurred ?: return null
            if (integration.isNullOrBlank() && customer.isNullOrBlank() && productQuantities.isEmpty()) return null
            val money = if (currency != null && amount != null) CommerceIdentityAmount(currency, amount) else null
            return OmieSalesOrderEvidence(
                org, productQuantities.keys, productQuantities, integration, customer, money, at,
                setOf("omie:$orderRef:$fingerprint"), emptySet()
            )
        }
    }
}

/** Read-only reconstruction of Mercado Livre source evidence already persisted by V021. */
class PostgresMercadoLivreIdentityEvidenceReader(
    private val configuration: PostgresConfiguration,
    private val connectionId: IntegrationConnectionId? = null
) : MercadoLivreIdentityEvidenceReader {
    override fun read(organizationId: OrganizationId, limit: Int): List<MercadoLivreTransactionEvidence> {
        require(limit in 1..10_000)
        val rows = mutableListOf<MlRow>()
        DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { c ->
            c.prepareStatement(
                "SELECT DISTINCT ON (external_order_ref) organization_id,external_order_ref,pack_ref,shipping_ref," +
                    "date_created,currency,total_amount,observed_at,connection_id,input_progress_version,record_ordinal " +
                    "FROM integration_mercado_livre_order_source_observation WHERE organization_id=? " +
                    "AND capability=? AND (? IS NULL OR connection_id=?) " +
                    "ORDER BY external_order_ref,date_last_updated DESC,observed_at DESC,input_progress_version DESC,record_ordinal " +
                    "LIMIT ?"
            ).use { s ->
                s.setObject(1, organizationId.value)
                s.setString(2, MarketplaceEconomicOrderSourceCapability.KEY.value)
                s.setObject(3, connectionId?.value)
                s.setObject(4, connectionId?.value)
                s.setInt(5, limit)
                s.executeQuery().use { rs -> while (rs.next()) rows += readRow(c, rs) }
            }
        }
        return rows.map { it.toDomain(organizationId) }
    }

    private fun readRow(c: java.sql.Connection, rs: ResultSet): MlRow {
        val organizationId = rs.getObject("connection_id")
        val items = mutableListOf<Pair<String, BigDecimal>>()
        c.prepareStatement(
            "SELECT item_ref,quantity FROM integration_mercado_livre_order_item_source_observation " +
                "WHERE organization_id=? AND connection_id=? AND capability=? AND input_progress_version=? " +
                "AND record_ordinal=? ORDER BY item_ordinal"
        ).use { s ->
            s.setObject(1, rs.getObject("organization_id") ?: error("organization column unavailable"))
            s.setObject(2, organizationId)
            s.setString(3, MarketplaceEconomicOrderSourceCapability.KEY.value)
            s.setLong(4, rs.getLong("input_progress_version"))
            s.setInt(5, rs.getInt("record_ordinal"))
            s.executeQuery().use { itemRs -> while (itemRs.next()) items += itemRs.getString("item_ref") to itemRs.getBigDecimal("quantity") }
        }
        return MlRow(rs.getString("external_order_ref"), rs.getString("pack_ref"), rs.getString("shipping_ref"), rs.getTimestamp("date_created").toInstant(), rs.getString("currency").trim(), rs.getBigDecimal("total_amount"), rs.getTimestamp("observed_at").toInstant(), items)
    }

    private data class MlRow(val order: String, val pack: String?, val shipping: String?, val occurred: Instant, val currency: String, val amount: BigDecimal, val observed: Instant, val items: List<Pair<String, BigDecimal>>) {
        fun toDomain(org: OrganizationId) = MercadoLivreTransactionEvidence(
            org, order, pack, shipping, items.map { it.first }.toSet(), emptySet(), emptyMap(),
            CommerceIdentityAmount(currency, amount), occurred, setOf("mercadolivre:$order:$observed")
        )
    }
}
