package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.connector.*
import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.provider.*
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.Timestamp
import java.time.Clock
import java.time.Instant
import kotlin.reflect.KClass
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

class PostgresOmieTransactionEvidenceV3Committer(
    configuration: PostgresConfiguration,
    protector: ConnectorProgressProtector,
    clock: Clock = Clock.systemUTC()
) : ConnectorPageCommitter {
    private val progress =
        PostgresConnectorProgressStore(configuration, protector, clock)

    override val capability: ConnectorCapability =
        OmieTransactionEvidenceV3Capability.KEY

    override val recordType: KClass<out ConnectorRecord> =
        OmieTransactionEvidenceV3Record::class

    override fun load(
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        capability: ConnectorCapability
    ): VersionedConnectorProgress {
        require(capability == this.capability)
        return progress.load(organizationId, connectionId, capability)
    }

    override fun commit(
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        capability: ConnectorCapability,
        expectedProgressVersion: Long,
        pageCommitKey: ConnectorPageCommitKey,
        records: List<ConnectorRecord>,
        nextProgress: ConnectorProgress?,
        exhausted: Boolean,
        observedAt: Instant
    ): ConnectorPageCommitResult {
        require(capability == this.capability)

        val typed = records.map {
            require(it is OmieTransactionEvidenceV3Record)
            it
        }

        require(typed.all { it.observedAt == observedAt })

        return progress.commitPage(
            organizationId,
            connectionId,
            capability,
            expectedProgressVersion,
            pageCommitKey,
            typed.size,
            nextProgress,
            exhausted,
            observedAt,
            persistRecords = { connection ->
                typed.forEachIndexed { ordinal, record ->
                    insertBase(
                        connection,
                        organizationId,
                        connectionId,
                        expectedProgressVersion,
                        ordinal,
                        record
                    )
                    insertV3(
                        connection,
                        organizationId,
                        connectionId,
                        expectedProgressVersion,
                        ordinal,
                        record
                    )
                    insertLines(
                        connection,
                        organizationId,
                        connectionId,
                        expectedProgressVersion,
                        ordinal,
                        record
                    )
                }
            },
            validateExistingRecords = { connection ->
                validateExisting(
                    connection,
                    organizationId,
                    connectionId,
                    expectedProgressVersion,
                    typed
                )
            }
        )
    }

    private fun insertBase(
        connection: Connection,
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        progressVersion: Long,
        ordinal: Int,
        record: OmieTransactionEvidenceV3Record
    ) {
        val legacyProducts = record.lines.flatMap { line ->
            val quantity = line.quantity ?: return@flatMap emptyList()
            line.productIdentifiers.map { identifier ->
                OmieTransactionProductObservation(identifier, quantity)
            }
        }

        connection.prepareStatement(
            """
            INSERT INTO integration_omie_transaction_evidence (
                organization_id,
                connection_id,
                capability,
                input_progress_version,
                record_ordinal,
                source_order_ref,
                source_integration_ref,
                source_customer_order_ref,
                occurred_at,
                source_status,
                currency,
                total_amount,
                product_refs,
                observed_at,
                source_fingerprint
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?::jsonb,?,?)
            """.trimIndent()
        ).use { statement ->
            statement.setObject(1, organizationId.value)
            statement.setObject(2, connectionId.value)
            statement.setString(3, capability.value)
            statement.setLong(4, progressVersion)
            statement.setInt(5, ordinal)
            statement.setString(
                6,
                record.orderReference.encodedForPersistence()
            )
            statement.setString(
                7,
                record.integrationOrderReference?.encodedForPersistence()
            )
            statement.setString(
                8,
                record.customerOrderReference?.encodedForPersistence()
            )
            statement.setTimestamp(9, null)
            statement.setString(
                10,
                record.status?.encodedForPersistence()
            )
            statement.setString(
                11,
                record.currency?.encodedForPersistence()
            )
            statement.setBigDecimal(
                12,
                record.totalOrderAmount?.valueForPersistence()
            )
            statement.setString(
                13,
                OmieProductRefsJson.encode(legacyProducts)
            )
            statement.setTimestamp(
                14,
                Timestamp.from(record.observedAt)
            )
            statement.setString(15, record.sourceFingerprint)
            check(statement.executeUpdate() == 1)
        }
    }

    private fun insertV3(
        connection: Connection,
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        progressVersion: Long,
        ordinal: Int,
        record: OmieTransactionEvidenceV3Record
    ) {
        connection.prepareStatement(
            """
            INSERT INTO integration_omie_transaction_evidence_v3 (
                organization_id,
                connection_id,
                capability,
                input_progress_version,
                record_ordinal,

                source_order_origin,

                provider_created_local,
                provider_modified_local,

                source_cancelled,
                source_cancelled_local,

                source_invoiced,
                source_invoiced_local,

                source_authorized,
                source_denied,
                source_returned,
                source_partially_returned,

                order_ended,
                order_ended_reason,
                order_ended_local,

                order_discount_type,
                order_discount_percent,
                order_discount_amount,

                merchandise_amount,
                discount_amount,
                deduction_amount,

                freight_amount,
                insurance_amount,
                other_expense_amount,

                marketplace_fee_amount,
                marketplace_shipping_amount,

                additional_order_totals,

                semantic_fingerprint_version,
                source_evidence_semantic_fingerprint
            ) VALUES (
                ?,?,?,?,?,
                ?,
                ?,?,
                ?,?,
                ?,?,
                ?,?,?,?,
                ?,?,?,
                ?,?,?,
                ?,?,?,
                ?,?,?,
                ?,?,
                ?::jsonb,
                ?,?
            )
            """.trimIndent()
        ).use { statement ->
            var index = 1

            statement.setObject(index++, organizationId.value)
            statement.setObject(index++, connectionId.value)
            statement.setString(index++, capability.value)
            statement.setLong(index++, progressVersion)
            statement.setInt(index++, ordinal)

            statement.setString(
                index++,
                record.sourceOrderOrigin?.encodedForPersistence()
            )

            statement.setTimestamp(
                index++,
                record.providerCreatedLocal?.let(Timestamp::valueOf)
            )
            statement.setTimestamp(
                index++,
                record.providerModifiedLocal?.let(Timestamp::valueOf)
            )

            statement.setObject(index++, record.cancelled)
            statement.setTimestamp(
                index++,
                record.cancelledLocal?.let(Timestamp::valueOf)
            )

            statement.setObject(index++, record.invoiced)
            statement.setTimestamp(
                index++,
                record.invoicedLocal?.let(Timestamp::valueOf)
            )

            statement.setObject(index++, record.authorized)
            statement.setObject(index++, record.denied)
            statement.setObject(index++, record.returned)
            statement.setObject(index++, record.partiallyReturned)

            statement.setObject(index++, record.orderEnded)
            statement.setString(
                index++,
                record.orderEndedReason?.encodedForPersistence()
            )
            statement.setTimestamp(
                index++,
                record.orderEndedLocal?.let(Timestamp::valueOf)
            )

            statement.setString(
                index++,
                record.orderDiscountType?.encodedForPersistence()
            )
            statement.setBigDecimal(
                index++,
                record.orderDiscountPercent?.valueForPersistence()
            )
            statement.setBigDecimal(
                index++,
                record.orderDiscountAmount?.valueForPersistence()
            )

            statement.setBigDecimal(
                index++,
                record.merchandiseAmount?.valueForPersistence()
            )
            statement.setBigDecimal(
                index++,
                record.discountAmount?.valueForPersistence()
            )
            statement.setBigDecimal(
                index++,
                record.deductionAmount?.valueForPersistence()
            )

            statement.setBigDecimal(
                index++,
                record.freightAmount?.valueForPersistence()
            )
            statement.setBigDecimal(
                index++,
                record.insuranceAmount?.valueForPersistence()
            )
            statement.setBigDecimal(
                index++,
                record.otherExpenseAmount?.valueForPersistence()
            )

            statement.setBigDecimal(
                index++,
                record.marketplaceFeeAmount?.valueForPersistence()
            )
            statement.setBigDecimal(
                index++,
                record.marketplaceShippingAmount?.valueForPersistence()
            )

            statement.setString(
                index++,
                buildJsonObject {
                    record.additionalOrderTotals.forEach { (key, value) ->
                        put(key, value.canonicalValue())
                    }
                }.toString()
            )

            statement.setInt(index++, 1)
            statement.setString(
                index++,
                record.sourceEvidenceSemanticFingerprint
            )

            check(index == 34)
            check(statement.executeUpdate() == 1)
        }
    }

    private fun insertLines(
        connection: Connection,
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        progressVersion: Long,
        recordOrdinal: Int,
        record: OmieTransactionEvidenceV3Record
    ) {
        record.lines.forEachIndexed { lineOrdinal, line ->
            connection.prepareStatement(
                """
                INSERT INTO integration_omie_transaction_evidence_v3_line (
                    organization_id,
                    connection_id,
                    capability,
                    input_progress_version,
                    record_ordinal,
                    line_ordinal,

                    internal_item_ref,
                    integration_item_ref,

                    product_internal_ref,
                    product_integration_ref,
                    product_display_code,

                    quantity,
                    unit_value,

                    discount_type,
                    discount_percent,
                    discount_value,
                    deduction_value,

                    merchandise_value,
                    total_value,

                    do_not_generate_financial,
                    do_not_sum_total,

                    is_kit,
                    is_kit_component,
                    kit_parent_item_ref
                ) VALUES (
                    ?,?,?,?,?,?,
                    ?,?,
                    ?,?,?,
                    ?,?,
                    ?,?,?,?,
                    ?,?,
                    ?,?,
                    ?,?,?
                )
                """.trimIndent()
            ).use { statement ->
                val byKind = line.productIdentifiers.associateBy { it.kind }
                var index = 1

                statement.setObject(index++, organizationId.value)
                statement.setObject(index++, connectionId.value)
                statement.setString(index++, capability.value)
                statement.setLong(index++, progressVersion)
                statement.setInt(index++, recordOrdinal)
                statement.setInt(index++, lineOrdinal)

                statement.setString(
                    index++,
                    line.internalItemReference?.encodedForPersistence()
                )
                statement.setString(
                    index++,
                    line.integrationItemReference?.encodedForPersistence()
                )

                statement.setString(
                    index++,
                    byKind[
                        OmieTransactionProductIdentifierKind.INTERNAL_PRODUCT_ID
                    ]?.encodedForPersistence()
                )
                statement.setString(
                    index++,
                    byKind[
                        OmieTransactionProductIdentifierKind.INTEGRATION_PRODUCT_CODE
                    ]?.encodedForPersistence()
                )
                statement.setString(
                    index++,
                    byKind[
                        OmieTransactionProductIdentifierKind.DISPLAY_PRODUCT_CODE
                    ]?.encodedForPersistence()
                )

                statement.setBigDecimal(
                    index++,
                    line.quantity?.valueForPersistence()
                )
                statement.setBigDecimal(
                    index++,
                    line.unitValue?.valueForPersistence()
                )

                statement.setString(
                    index++,
                    line.discountType?.encodedForPersistence()
                )
                statement.setBigDecimal(
                    index++,
                    line.discountPercent?.valueForPersistence()
                )
                statement.setBigDecimal(
                    index++,
                    line.discountValue?.valueForPersistence()
                )
                statement.setBigDecimal(
                    index++,
                    line.deductionValue?.valueForPersistence()
                )

                statement.setBigDecimal(
                    index++,
                    line.merchandiseValue?.valueForPersistence()
                )
                statement.setBigDecimal(
                    index++,
                    line.totalValue?.valueForPersistence()
                )

                statement.setObject(index++, line.doNotGenerateFinancial)
                statement.setObject(index++, line.doNotSumTotal)

                statement.setObject(index++, line.kit)
                statement.setObject(index++, line.kitComponent)
                statement.setString(
                    index++,
                    line.kitParentItemReference?.encodedForPersistence()
                )

                check(index == 25)
                check(statement.executeUpdate() == 1)
            }
        }
    }

    private fun validateExisting(
        connection: Connection,
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        progressVersion: Long,
        records: List<OmieTransactionEvidenceV3Record>
    ) {
        connection.prepareStatement(
            """
            SELECT
                b.source_order_ref,
                b.source_fingerprint,
                v.source_evidence_semantic_fingerprint,
                (
                    SELECT count(*)
                    FROM integration_omie_transaction_evidence_v3_line l
                    WHERE l.organization_id = v.organization_id
                      AND l.connection_id = v.connection_id
                      AND l.capability = v.capability
                      AND l.input_progress_version = v.input_progress_version
                      AND l.record_ordinal = v.record_ordinal
                ) AS line_count
            FROM integration_omie_transaction_evidence b
            JOIN integration_omie_transaction_evidence_v3 v
              ON v.organization_id = b.organization_id
             AND v.connection_id = b.connection_id
             AND v.capability = b.capability
             AND v.input_progress_version = b.input_progress_version
             AND v.record_ordinal = b.record_ordinal
            WHERE b.organization_id = ?
              AND b.connection_id = ?
              AND b.capability = ?
              AND b.input_progress_version = ?
            ORDER BY b.record_ordinal
            """.trimIndent()
        ).use { statement ->
            statement.setObject(1, organizationId.value)
            statement.setObject(2, connectionId.value)
            statement.setString(3, capability.value)
            statement.setLong(4, progressVersion)

            statement.executeQuery().use { result ->
                var index = 0

                while (result.next()) {
                    check(index < records.size)

                    val expected = records[index]

                    check(
                        result.getString("source_order_ref") ==
                            expected.orderReference.encodedForPersistence()
                    )
                    check(
                        result.getString("source_fingerprint") ==
                            expected.sourceFingerprint
                    )
                    check(
                        result.getString(
                            "source_evidence_semantic_fingerprint"
                        ) == expected.sourceEvidenceSemanticFingerprint
                    )
                    check(
                        result.getInt("line_count") ==
                            expected.lines.size
                    )

                    index += 1
                }

                check(index == records.size)
            }
        }
    }
}
