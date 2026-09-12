package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.promotion.GovernedProductCostPromotionAuthority
import io.flooow.marketplace.operations.economics.promotion.GovernedProductCostPromotionRequest
import io.flooow.marketplace.operations.economics.promotion.GovernedProductCostSourceRead
import java.sql.DriverManager
import java.util.UUID

/** Read-only proof that exact provider, item, subject, currency, and quantity evidence agree. */
class PostgresGovernedProductCostPromotionAuthority(
    private val configuration: PostgresConfiguration
) : GovernedProductCostPromotionAuthority {
    override fun read(request: GovernedProductCostPromotionRequest): GovernedProductCostSourceRead = try {
        val currencyAuthority = request.currencyAuthority
            ?: return GovernedProductCostSourceRead.CurrencyUnavailable
        if (currencyAuthority != request.subject.currency) {
            return GovernedProductCostSourceRead.CurrencyUnavailable
        }
        DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { connection ->
            val relation = request.relation
            val source = request.sourceObservation
            connection.prepareStatement(
                "SELECT cost.unit_cmc,cost.observed_at,item.quantity,item.currency AS item_currency," +
                    "orders.currency AS order_currency,identity.currency AS subject_currency " +
                    "FROM integration_omie_product_cost_source_observation cost " +
                    "JOIN integration_mercado_livre_order_item_source_observation item " +
                    "ON item.organization_id=cost.organization_id " +
                    "JOIN integration_mercado_livre_order_source_observation orders " +
                    "ON orders.organization_id=item.organization_id AND orders.connection_id=item.connection_id " +
                    "AND orders.capability=item.capability AND orders.input_progress_version=item.input_progress_version " +
                    "AND orders.record_ordinal=item.record_ordinal " +
                    "JOIN marketplace_order_identity_registry identity " +
                    "ON identity.organization_id=orders.organization_id AND identity.marketplace_key='mercado-livre' " +
                    "AND identity.external_order_id=orders.external_order_ref " +
                    "WHERE cost.organization_id=? AND cost.connection_id=? AND cost.capability=? " +
                    "AND cost.input_progress_version=? AND cost.record_ordinal=? AND cost.source_product_ref=? " +
                    "AND item.connection_id=? AND item.item_ref=? AND item.seller_sku=? " +
                    "AND identity.marketplace_order_id=? AND identity.external_order_id=?"
            ).use { statement ->
                statement.setObject(1, relation.scope.organizationId.value)
                statement.setObject(2, UUID.fromString(source.connectionId))
                statement.setString(3, source.capability)
                statement.setLong(4, source.inputProgressVersion)
                statement.setInt(5, source.recordOrdinal)
                statement.setString(6, relation.omie.providerProductId)
                statement.setObject(7, UUID.fromString(relation.scope.mercadoLivreConnectionId))
                statement.setString(8, relation.mercadoLivre.itemId)
                statement.setString(9, relation.mercadoLivre.sellerSku)
                statement.setObject(10, request.subject.orderId.value)
                statement.setString(11, request.subject.externalOrderId.value)
                statement.executeQuery().use { result ->
                    if (!result.next()) return GovernedProductCostSourceRead.SubjectUnresolved
                    val subjectCurrency = result.getString("subject_currency").trimEnd()
                    val itemCurrency = result.getString("item_currency").trimEnd()
                    val orderCurrency = result.getString("order_currency").trimEnd()
                    if (itemCurrency != orderCurrency || orderCurrency != subjectCurrency) {
                        return GovernedProductCostSourceRead.IntegrityFailure
                    }
                    if (subjectCurrency != request.subject.currency.code ||
                        subjectCurrency != currencyAuthority.code) {
                        return GovernedProductCostSourceRead.CurrencyUnavailable
                    }
                    val allocation = request.allocation ?: return GovernedProductCostSourceRead.AllocationUnavailable
                    if (result.getBigDecimal("quantity").compareTo(allocation.quantity) != 0) {
                        return GovernedProductCostSourceRead.IntegrityFailure
                    }
                    val cost = result.getBigDecimal("unit_cmc") ?: return GovernedProductCostSourceRead.CostMissing
                    val observedAt = result.getTimestamp("observed_at").toInstant()
                    if (result.next()) return GovernedProductCostSourceRead.IntegrityFailure
                    GovernedProductCostSourceRead.Available(cost, observedAt)
                }
            }
        }
    } catch (_: Exception) {
        GovernedProductCostSourceRead.IntegrityFailure
    }
}
