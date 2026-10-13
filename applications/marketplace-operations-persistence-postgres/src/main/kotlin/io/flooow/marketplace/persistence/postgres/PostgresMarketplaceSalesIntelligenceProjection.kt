package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssemblyPolicyVersion
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.ChangeSequenceCheckpoint
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceVersion
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjection
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionCursor
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionPage
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionReadResult
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionRecord
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionWriteResult
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.ResultSet
import java.sql.Timestamp
import java.sql.Types
import java.util.UUID
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject

class PostgresMarketplaceSalesIntelligenceProjection(
    private val configuration: PostgresConfiguration
) : MarketplaceSalesIntelligenceProjection {
    override fun currentBySubject(
        organizationId: OrganizationId,
        marketplaceOrderId: MarketplaceOrderId
    ): MarketplaceSalesIntelligenceProjectionReadResult<MarketplaceSalesIntelligenceProjectionRecord?> =
        readOne(organizationId, marketplaceOrderId)

    override fun detailByOrganizationAndSubject(
        organizationId: OrganizationId,
        marketplaceOrderId: MarketplaceOrderId
    ): MarketplaceSalesIntelligenceProjectionReadResult<MarketplaceSalesIntelligenceProjectionRecord?> =
        readOne(organizationId, marketplaceOrderId)

    override fun materializeIfNewer(
        record: MarketplaceSalesIntelligenceProjectionRecord
    ): MarketplaceSalesIntelligenceProjectionWriteResult = try {
        val encoded = MarketplaceSalesIntelligenceStateCodecV1.encode(record.state)
        connection().use { connection ->
            connection.prepareStatement(UPSERT_SQL).use { statement ->
                statement.setObject(1, record.organizationId.value)
                statement.setObject(2, record.marketplaceOrderId.value)
                statement.setLong(3, record.sourceEvidenceVersion.valueForPersistence())
                statement.setString(4, encoded.stateKind)
                statement.setString(5, record.state.assemblyPolicyVersion.value)
                if (encoded.calculationPolicyVersion == null) {
                    statement.setNull(6, Types.VARCHAR)
                } else {
                    statement.setString(6, encoded.calculationPolicyVersion)
                }
                if (encoded.calculationKind == null) {
                    statement.setNull(7, Types.VARCHAR)
                } else {
                    statement.setString(7, encoded.calculationKind)
                }
                statement.setObject(8, encoded.payload, Types.OTHER)
                statement.setLong(9, record.lastAppliedChangeSequence.valueForPersistence())
                statement.setTimestamp(10, Timestamp.from(record.projectedAt))
                statement.executeQuery().use { result ->
                    if (result.next()) {
                        MarketplaceSalesIntelligenceProjectionWriteResult.Applied
                    } else {
                        when (val current = currentBySubject(record.organizationId, record.marketplaceOrderId)) {
                            is MarketplaceSalesIntelligenceProjectionReadResult.Success ->
                                if (current.value?.lastAppliedChangeSequence?.let { it >= record.lastAppliedChangeSequence } == true)
                                    MarketplaceSalesIntelligenceProjectionWriteResult.NoOpAlreadyCurrent
                                else MarketplaceSalesIntelligenceProjectionWriteResult.IntegrityFailure
                            MarketplaceSalesIntelligenceProjectionReadResult.IntegrityFailure ->
                                MarketplaceSalesIntelligenceProjectionWriteResult.IntegrityFailure
                        }
                    }
                }
            }
        }
    } catch (_: Exception) {
        MarketplaceSalesIntelligenceProjectionWriteResult.IntegrityFailure
    }

    override fun listByOrganization(
        organizationId: OrganizationId,
        cursor: MarketplaceSalesIntelligenceProjectionCursor?,
        limit: Int
    ): MarketplaceSalesIntelligenceProjectionReadResult<MarketplaceSalesIntelligenceProjectionPage> {
        val validated = MarketplaceSalesIntelligenceProjection.requireValidPageSize(limit)
        return try {
            val rows = connection().use { connection ->
                val sql = if (cursor == null) LIST_FIRST_SQL else LIST_AFTER_SQL
                connection.prepareStatement(sql).use { statement ->
                    statement.setObject(1, organizationId.value)
                    var index = 2
                    if (cursor != null) {
                        val timestamp = Timestamp.from(cursor.projectedAt)
                        statement.setTimestamp(index++, timestamp)
                        statement.setTimestamp(index++, timestamp)
                        statement.setObject(index++, cursor.marketplaceOrderId.value)
                    }
                    statement.setInt(index, validated + 1)
                    statement.executeQuery().use { result ->
                        buildList {
                            while (result.next()) add(result.toRecord())
                        }
                    }
                }
            }

            val hasMore = rows.size > validated
            val visible = if (hasMore) rows.take(validated) else rows
            val nextCursor = if (hasMore && visible.isNotEmpty()) {
                visible.last().let {
                    MarketplaceSalesIntelligenceProjectionCursor(
                        projectedAt = it.projectedAt,
                        marketplaceOrderId = it.marketplaceOrderId
                    )
                }
            } else {
                null
            }
            MarketplaceSalesIntelligenceProjectionReadResult.Success(
                MarketplaceSalesIntelligenceProjectionPage(visible, nextCursor)
            )
        } catch (_: Exception) {
            MarketplaceSalesIntelligenceProjectionReadResult.IntegrityFailure
        }
    }

    private fun readOne(
        organizationId: OrganizationId,
        marketplaceOrderId: MarketplaceOrderId
    ): MarketplaceSalesIntelligenceProjectionReadResult<MarketplaceSalesIntelligenceProjectionRecord?> =
        try {
            val value = connection().use { connection ->
                connection.prepareStatement(DETAIL_SQL).use { statement ->
                    statement.setObject(1, organizationId.value)
                    statement.setObject(2, marketplaceOrderId.value)
                    statement.executeQuery().use { result ->
                        if (result.next()) result.toRecord() else null
                    }
                }
            }
            MarketplaceSalesIntelligenceProjectionReadResult.Success(value)
        } catch (_: Exception) {
            MarketplaceSalesIntelligenceProjectionReadResult.IntegrityFailure
        }

    private fun ResultSet.toRecord(): MarketplaceSalesIntelligenceProjectionRecord {
        val organizationId = OrganizationId(getObject("organization_id", UUID::class.java))
        val orderId = MarketplaceOrderId(getObject("marketplace_order_id", UUID::class.java))
        val assemblyPolicyVersion =
            MarketplaceEconomicTruthAssemblyPolicyVersion(getString("assembly_policy_version"))
        val stateKind = getString("state_kind")
        val payload = Json.parseToJsonElement(getString("state_payload")).jsonObject

        val state = MarketplaceSalesIntelligenceStateCodecV1.decode(organizationId, orderId, assemblyPolicyVersion,
            stateKind, getString("calculation_policy_version"), getString("calculation_kind"), payload)

        return MarketplaceSalesIntelligenceProjectionRecord(
            organizationId = organizationId,
            marketplaceOrderId = orderId,
            sourceEvidenceVersion = MarketplaceEconomicEvidenceVersion(
                getLong("source_evidence_version")
            ),
            state = state,
            lastAppliedChangeSequence = ChangeSequenceCheckpoint(
                getLong("last_applied_change_sequence")
            ),
            projectedAt = getTimestamp("projected_at").toInstant()
        )
    }

    private fun connection(): Connection = DriverManager.getConnection(
        configuration.url,
        configuration.user,
        configuration.password
    )

    companion object {
        private const val DETAIL_SQL =
            "SELECT * FROM marketplace_sales_intelligence_projection " +
                "WHERE organization_id=? AND marketplace_order_id=?"

        private const val LIST_FIRST_SQL =
            "SELECT * FROM marketplace_sales_intelligence_projection " +
                "WHERE organization_id=? " +
                "ORDER BY projected_at DESC, marketplace_order_id DESC LIMIT ?"

        private const val LIST_AFTER_SQL =
            "SELECT * FROM marketplace_sales_intelligence_projection " +
                "WHERE organization_id=? AND " +
                "(projected_at<? OR (projected_at=? AND marketplace_order_id<?)) " +
                "ORDER BY projected_at DESC, marketplace_order_id DESC LIMIT ?"

        private const val UPSERT_SQL =
            "INSERT INTO marketplace_sales_intelligence_projection " +
                "(organization_id,marketplace_order_id,source_evidence_version," +
                "state_kind,assembly_policy_version,calculation_policy_version," +
                "calculation_kind,state_payload,last_applied_change_sequence,projected_at) " +
                "VALUES (?,?,?,?,?,?,?,?,?,?) " +
                "ON CONFLICT (organization_id,marketplace_order_id) DO UPDATE SET " +
                "source_evidence_version=EXCLUDED.source_evidence_version," +
                "state_kind=EXCLUDED.state_kind," +
                "assembly_policy_version=EXCLUDED.assembly_policy_version," +
                "calculation_policy_version=EXCLUDED.calculation_policy_version," +
                "calculation_kind=EXCLUDED.calculation_kind," +
                "state_payload=EXCLUDED.state_payload," +
                "last_applied_change_sequence=EXCLUDED.last_applied_change_sequence," +
                "projected_at=EXCLUDED.projected_at " +
                "WHERE EXCLUDED.last_applied_change_sequence>" +
                "marketplace_sales_intelligence_projection.last_applied_change_sequence " +
                "AND EXCLUDED.source_evidence_version>=" +
                "marketplace_sales_intelligence_projection.source_evidence_version " +
                "RETURNING last_applied_change_sequence"
    }
}
