package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.reconciliation.DurableReconciliationCase
import io.flooow.marketplace.operations.economics.reconciliation.EconomicDecisionRoomAuthorityContext
import io.flooow.marketplace.operations.economics.reconciliation.EconomicDecisionRoomAuthorityRead
import io.flooow.marketplace.operations.economics.reconciliation.EconomicDecisionRoomAuthoritySource
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityEvidence
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityInputs
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityState
import io.flooow.organization.OrganizationId
import java.sql.SQLException
import java.sql.Connection
import javax.sql.DataSource

/**
 * Read-only verification of the persisted D3C/D4 Mercado Livre ACTUAL SALE chain.
 * It deliberately exposes no authority dimension as canonical or reconciled.
 */
class PostgresEconomicDecisionRoomAuthoritySource(
    private val dataSource: DataSource
) : EconomicDecisionRoomAuthoritySource {
    override fun read(
        organizationId: OrganizationId,
        case: DurableReconciliationCase
    ): EconomicDecisionRoomAuthorityRead {
        if (organizationId != case.organizationId || case.evidenceEntryIds.isEmpty()) {
            return EconomicDecisionRoomAuthorityRead.Unavailable
        }
        return try {
            dataSource.connection.use { connection ->
                try {
                    connection.autoCommit = false
                    connection.isReadOnly = true
                    connection.transactionIsolation = Connection.TRANSACTION_REPEATABLE_READ
                    val result = case.evidenceEntryIds.map { entryId ->
                    connection.prepareStatement(SQL).use { statement ->
                        statement.setObject(1, case.organizationId.value)
                        statement.setObject(2, entryId.valueForPersistence())
                        statement.setObject(3, case.traceId.valueForPersistence())
                        statement.executeQuery().use { rows ->
                            if (!rows.next()) return@use null
                            val row = Row(
                                traceOrderId = rows.getObject("trace_order_id"),
                                traceCurrency = rows.getString("trace_currency").trimEnd(),
                                lineageOrderId = rows.getObject("source_order_id"),
                                stage = rows.getString("stage"),
                                basis = rows.getString("basis"),
                                componentType = rows.getString("component_type"),
                                promotionOutcome = rows.getString("promotion_outcome"),
                                sourceExternalOrderId = rows.getString("source_external_order_id"),
                                sourceCurrency = rows.getString("source_currency"),
                                identityExternalOrderId = rows.getString("identity_external_order_id"),
                                identityCurrency = rows.getString("identity_currency"),
                                marketplaceKey = rows.getString("marketplace_key")
                            )
                            if (rows.next()) throw IntegrityException()
                            row
                        }
                    }
                }
                    connection.commit()
                    if (result.any { it == null }) return EconomicDecisionRoomAuthorityRead.Unavailable
                    if (result.filterNotNull().any { !it.matches(case) }) return EconomicDecisionRoomAuthorityRead.IntegrityFailure
                    EconomicDecisionRoomAuthorityRead.Available(
                    EconomicDecisionRoomAuthorityContext(
                        organizationId = case.organizationId,
                        caseId = case.caseId,
                        marketplaceOrderId = case.orderId,
                        financialTraceId = case.traceId,
                        policyVersion = case.policyVersion,
                        currency = case.currency,
                        reconciliationRevision = case.revision,
                        inputs = unresolvedInputs()
                    )
                    )
                } catch (failure: Throwable) {
                    safeRollbackIfNeeded(connection)
                    throw failure
                }
            }
        } catch (_: IntegrityException) {
            EconomicDecisionRoomAuthorityRead.IntegrityFailure
        } catch (_: SQLException) {
            EconomicDecisionRoomAuthorityRead.Unavailable
        } catch (_: RuntimeException) {
            EconomicDecisionRoomAuthorityRead.IntegrityFailure
        }
    }

    private fun unresolvedInputs() = EconomicTruthAuthorityInputs(
        identity = unresolved(),
        currency = unresolved(),
        allocation = unresolved(),
        currentness = unresolved()
    )

    private fun unresolved() = EconomicTruthAuthorityEvidence(EconomicTruthAuthorityState.UNRESOLVED)

    private data class Row(
        val traceOrderId: Any,
        val traceCurrency: String,
        val lineageOrderId: Any,
        val stage: String?,
        val basis: String?,
        val componentType: String?,
        val promotionOutcome: String?,
        val sourceExternalOrderId: String?,
        val sourceCurrency: String?,
        val identityExternalOrderId: String?,
        val identityCurrency: String?,
        val marketplaceKey: String?
    ) {
        fun matches(case: DurableReconciliationCase): Boolean =
            traceOrderId == case.orderId.value &&
                lineageOrderId == case.orderId.value &&
                traceCurrency == case.currency.code &&
                stage == "SALE" && basis == "ACTUAL" && componentType == "REVENUE" &&
                promotionOutcome in setOf("PROMOTED", "DUPLICATE") &&
                marketplaceKey == "mercado-livre" &&
                sourceExternalOrderId != null && sourceExternalOrderId == identityExternalOrderId &&
                sourceCurrency?.trimEnd() == identityCurrency?.trimEnd() &&
                sourceCurrency?.trimEnd() == case.currency.code
    }

    private class IntegrityException : RuntimeException()

    private fun safeRollbackIfNeeded(connection: Connection) {
        try {
            if (!connection.autoCommit) {
                connection.rollback()
            }
        } catch (_: SQLException) {
            // Preserve the original failure classification.
        }
    }

    private companion object {
        const val SQL = """
            SELECT trace.order_id AS trace_order_id,
                   trace.currency AS trace_currency,
                   lineage.source_order_id,
                   lineage.stage,
                   lineage.basis,
                   component.component_type,
                   promotion.outcome AS promotion_outcome,
                   source.external_order_ref AS source_external_order_id,
                   source.currency AS source_currency,
                   identity.external_order_id AS identity_external_order_id,
                   identity.currency AS identity_currency,
                   identity.marketplace_key
              FROM marketplace_financial_ledger_entry entry
              JOIN marketplace_financial_trace trace
                ON trace.organization_id = entry.organization_id
               AND trace.trace_id = entry.trace_id
              LEFT JOIN marketplace_financial_ledger_materialization_lineage lineage
                ON lineage.organization_id = entry.organization_id
               AND lineage.ledger_entry_id = entry.entry_id
              LEFT JOIN marketplace_economic_evidence_component_fact component
                ON component.organization_id = lineage.organization_id
               AND component.marketplace_order_id = lineage.source_order_id
               AND component.fact_id = lineage.source_authority_identity
              LEFT JOIN marketplace_order_revenue_source_promotion promotion
                ON promotion.organization_id = lineage.organization_id
               AND promotion.marketplace_order_id = lineage.source_order_id
               AND promotion.economic_observation_id = lineage.source_authority_identity
              LEFT JOIN integration_mercado_livre_order_source_observation source
                ON source.organization_id = promotion.organization_id
               AND source.connection_id = promotion.source_connection_id
               AND source.capability = promotion.source_capability
               AND source.input_progress_version = promotion.source_input_progress_version
               AND source.record_ordinal = promotion.source_record_ordinal
              LEFT JOIN marketplace_order_identity_registry identity
                ON identity.organization_id = promotion.organization_id
               AND identity.marketplace_order_id = promotion.marketplace_order_id
             WHERE entry.organization_id = ?
               AND entry.entry_id = ?
               AND entry.trace_id = ?
        """
    }
}
