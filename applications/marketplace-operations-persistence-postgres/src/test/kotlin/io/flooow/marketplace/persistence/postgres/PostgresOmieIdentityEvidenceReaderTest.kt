package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.provider.OmieTransactionEvidenceCapability
import io.flooow.marketplace.operations.identity.ExplicitMarketplaceOrderReferenceResolver
import io.flooow.organization.OrganizationId
import java.sql.DriverManager
import java.time.Instant
import java.util.UUID
import org.testcontainers.postgresql.PostgreSQLContainer
import kotlin.test.Test
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertEquals

class PostgresOmieIdentityEvidenceReaderTest {
    private val organization = OrganizationId.parse("11111111-1111-4111-8111-111111111111")
    private val occurredAt = Instant.parse("2026-09-09T12:00:00Z")

    @Test
    fun `each identity bearing shape projects without fabrication`() {
        val integration = row(integration = "ERP-1").toDomain(organization)
        val customer = row(customer = "CUSTOMER-1").toDomain(organization)
        val product = row(products = "[{\"code\":\"SKU-1\",\"quantity\":\"2\"}]").toDomain(organization)

        assertNotNull(integration)
        assertNotNull(customer)
        assertNotNull(product)
        assertEquals(null, product!!.orderAmount)
    }

    @Test
    fun `row without integration customer or products is skipped`() {
        assertNull(row().toDomain(organization))
    }

    @Test
    fun `missing amount and currency remain missing`() {
        val evidence = row(integration = "ERP-1").toDomain(organization)
        assertNotNull(evidence)
        assertNull(evidence!!.orderAmount)
    }

    @Test
    fun `postgres reader feeds explicit resolver from durable provider reference`() {
        val postgres = PostgreSQLContainer("postgres:18.4")
        postgres.start()
        try {
            val configuration = PostgresConfiguration(postgres.jdbcUrl, postgres.username, postgres.password)
            val organizationId = organization.value
            val connectionId = UUID.fromString("33333333-3333-4333-8333-333333333333")
            val orderId = "2000018336941860"
            DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { c ->
                c.createStatement().use { statement ->
                    statement.execute(
                        """CREATE TABLE integration_omie_transaction_evidence (
                            organization_id UUID NOT NULL, connection_id UUID NOT NULL, capability TEXT NOT NULL,
                            input_progress_version BIGINT NOT NULL, record_ordinal INTEGER NOT NULL,
                            source_order_ref TEXT NOT NULL, source_integration_ref TEXT,
                            source_customer_order_ref TEXT, occurred_at TIMESTAMPTZ,
                            currency CHAR(3), total_amount NUMERIC(24,6), product_refs JSONB NOT NULL,
                            observed_at TIMESTAMPTZ NOT NULL, source_fingerprint TEXT NOT NULL
                        )"""
                    )
                }
                c.prepareStatement(
                    "INSERT INTO integration_omie_transaction_evidence " +
                        "(organization_id,connection_id,capability,input_progress_version,record_ordinal," +
                        "source_order_ref,source_integration_ref,source_customer_order_ref,occurred_at," +
                        "currency,total_amount,product_refs,observed_at,source_fingerprint) VALUES (?,?,?,?,?,?,?,?,?,?,?,?::jsonb,?,?)"
                ).use { statement ->
                    statement.setObject(1, organizationId)
                    statement.setObject(2, connectionId)
                    statement.setString(3, OmieTransactionEvidenceCapability.KEY.value)
                    statement.setLong(4, 1)
                    statement.setInt(5, 0)
                    statement.setString(6, "OMIE-1")
                    statement.setString(7, orderId)
                    statement.setNull(8, java.sql.Types.VARCHAR)
                    statement.setTimestamp(9, java.sql.Timestamp.from(occurredAt))
                    statement.setNull(10, java.sql.Types.CHAR)
                    statement.setNull(11, java.sql.Types.NUMERIC)
                    statement.setString(12, "[]")
                    statement.setTimestamp(13, java.sql.Timestamp.from(occurredAt))
                    statement.setString(14, "fp-1")
                    statement.executeUpdate()
                }
            }

            val read = PostgresOmieIdentityEvidenceReader(
                configuration, IntegrationConnectionId(connectionId)
            ).read(organization, 10)
            assertEquals(1, read.records.size)
            assertEquals(
                setOf(orderId),
                ExplicitMarketplaceOrderReferenceResolver.resolve(
                    setOf(orderId), listOf(read.records.single().integrationCode)
                )
            )
        } finally {
            postgres.stop()
        }
    }

    private fun row(
        integration: String? = null,
        customer: String? = null,
        products: String = "[]"
    ) = PostgresOmieIdentityEvidenceReader.OmieRow(
        "OMIE-1", integration, customer, occurredAt, null, null, products,
        occurredAt, "fingerprint-1"
    )
}
