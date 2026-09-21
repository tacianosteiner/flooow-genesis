package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.EconomicComponent
import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentId
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.EconomicExternalReference
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceFamily
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.evidence.valueForPersistence
import io.flooow.marketplace.operations.economics.ledger.materialization.MercadoLivreClosedOrderRevenueAuthoritySource
import io.flooow.marketplace.operations.economics.ledger.materialization.MercadoLivreClosedOrderRevenueAuthoritySourceResult
import io.flooow.marketplace.operations.economics.ledger.materialization.MercadoLivreClosedOrderRevenuePromotionOutcome
import io.flooow.marketplace.operations.economics.ledger.materialization.MercadoLivreClosedOrderRevenueProviderProof
import io.flooow.organization.OrganizationId
import java.util.UUID
import javax.sql.DataSource

/** Read-only resolution of already-governed Mercado Livre revenue lineage. */
class PostgresMercadoLivreClosedOrderRevenueAuthoritySource(
    private val dataSource: DataSource
) : MercadoLivreClosedOrderRevenueAuthoritySource {
    constructor(configuration: PostgresConfiguration) : this(PostgresDataSources.create(configuration))
    override fun findProofs(
        organizationId: OrganizationId,
        observationId: MarketplaceEconomicEvidenceObservationId,
        marketplaceOrderId: MarketplaceOrderId
    ): MercadoLivreClosedOrderRevenueAuthoritySourceResult = try {
        dataSource.connection.use { connection ->
            connection.prepareStatement(SQL).use { statement ->
                statement.setObject(1, organizationId.value)
                statement.setObject(2, marketplaceOrderId.value)
                statement.setObject(3, observationId.valueForPersistence())
                statement.executeQuery().use { rows ->
                    if (!rows.next()) return MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound
                    val proof = proof(rows, organizationId, marketplaceOrderId, observationId)
                        ?: return MercadoLivreClosedOrderRevenueAuthoritySourceResult.IntegrityFailure
                    if (rows.next()) return MercadoLivreClosedOrderRevenueAuthoritySourceResult.IntegrityFailure
                    MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(listOf(proof))
                }
            }
        }
    } catch (_: Exception) {
        MercadoLivreClosedOrderRevenueAuthoritySourceResult.Unavailable
    }

    private fun proof(
        row: java.sql.ResultSet,
        organizationId: OrganizationId,
        orderId: MarketplaceOrderId,
        requestedObservationId: MarketplaceEconomicEvidenceObservationId
    ): MercadoLivreClosedOrderRevenueProviderProof? = try {
        val observationId = MarketplaceEconomicEvidenceObservationId.parse(
            row.getObject("fact_id", UUID::class.java).toString()
        )
        if (observationId != requestedObservationId) return null
        val currency = MarketplaceCurrency(row.getString("identity_currency").trimEnd())
        val externalOrderId = MarketplaceExternalOrderId(row.getString("identity_external_order_id"))
        val observation = MarketplaceEconomicComponentObservation(
            id = observationId,
            subject = MarketplaceEconomicEvidenceSubject(
                organizationId, orderId, MarketplaceKey(row.getString("marketplace_key")), externalOrderId, currency
            ),
            family = MarketplaceEconomicEvidenceFamily.valueOf(row.getString("family")),
            component = EconomicComponent(
                organizationId, EconomicComponentId(row.getObject("component_id", UUID::class.java)), orderId,
                EconomicComponentType.valueOf(row.getString("component_type")),
                EconomicDirection.valueOf(row.getString("direction")),
                MarketplaceMoney.parse(currency, row.getBigDecimal("magnitude").stripTrailingZeros().toPlainString()),
                EconomicSource(
                    EconomicSourceKind.valueOf(row.getString("source_kind")),
                    EconomicSourceSystemKey(row.getString("source_system_key")),
                    EconomicExternalReferenceState.Present(EconomicExternalReference(row.getString("source_external_reference")))
                ),
                row.getTimestamp("occurred_at").toInstant(),
                EconomicEvidenceQuality.valueOf(row.getString("quality"))
            ),
            EconomicComponentCoverage.valueOf(row.getString("coverage")),
            row.getTimestamp("fact_observed_at").toInstant()
        )
        MercadoLivreClosedOrderRevenueProviderProof(
            observation, organizationId, orderId, observation.subject.marketplace, externalOrderId, currency,
            row.getString("capability"), MarketplaceExternalOrderId(row.getString("external_order_ref")),
            MarketplaceCurrency(row.getString("source_currency").trimEnd()),
            MarketplaceMoney.parse(MarketplaceCurrency(row.getString("source_currency").trimEnd()), row.getBigDecimal("total_amount").stripTrailingZeros().toPlainString()),
            row.getTimestamp("date_closed").toInstant(), row.getTimestamp("source_observed_at").toInstant(),
            MercadoLivreClosedOrderRevenuePromotionOutcome.valueOf(row.getString("outcome"))
        )
    } catch (_: Exception) { null }

    private companion object {
        const val SQL = """
            SELECT promotion.outcome, promotion.source_capability AS capability,
                   fact.fact_id, fact.family, fact.observed_at AS fact_observed_at,
                   component.component_id, component.component_type, component.direction, component.magnitude,
                   component.source_kind, component.source_system_key, component.source_external_reference,
                   component.occurred_at, component.quality, component.coverage,
                   identity.marketplace_key, identity.external_order_id AS identity_external_order_id,
                   identity.currency AS identity_currency,
                   source.external_order_ref, source.currency AS source_currency, source.total_amount,
                   source.date_closed, source.observed_at AS source_observed_at
              FROM marketplace_order_revenue_source_promotion promotion
              JOIN marketplace_economic_evidence_fact fact
                ON fact.organization_id=promotion.organization_id AND fact.marketplace_order_id=promotion.marketplace_order_id AND fact.fact_id=promotion.economic_observation_id
              JOIN marketplace_economic_evidence_component_fact component
                ON component.organization_id=fact.organization_id AND component.marketplace_order_id=fact.marketplace_order_id AND component.fact_id=fact.fact_id
              JOIN integration_mercado_livre_order_source_observation source
                ON source.organization_id=promotion.organization_id AND source.connection_id=promotion.source_connection_id AND source.capability=promotion.source_capability AND source.input_progress_version=promotion.source_input_progress_version AND source.record_ordinal=promotion.source_record_ordinal
              JOIN marketplace_order_identity_registry identity
                ON identity.organization_id=promotion.organization_id AND identity.marketplace_order_id=promotion.marketplace_order_id
             WHERE promotion.organization_id=? AND promotion.marketplace_order_id=? AND promotion.economic_observation_id=?
               AND promotion.outcome IN ('PROMOTED','DUPLICATE')
             LIMIT 2
        """
    }
}
