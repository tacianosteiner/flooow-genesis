package io.flooow.marketplace.persistence.postgres

import io.flooow.organization.OrganizationId
import java.time.Instant
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

    private fun row(
        integration: String? = null,
        customer: String? = null,
        products: String = "[]"
    ) = PostgresOmieIdentityEvidenceReader.OmieRow(
        "OMIE-1", integration, customer, occurredAt, null, null, products,
        occurredAt, "fingerprint-1"
    )
}
