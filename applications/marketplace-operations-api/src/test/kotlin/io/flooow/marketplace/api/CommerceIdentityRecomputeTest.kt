package io.flooow.marketplace.api

import io.flooow.marketplace.operations.identity.*
import io.flooow.organization.OrganizationId
import io.ktor.client.request.bearerAuth
import io.ktor.client.request.post
import io.ktor.client.request.get
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.server.testing.testApplication
import java.math.BigDecimal
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertContains
import kotlin.test.assertEquals
import kotlin.test.assertFalse

class CommerceIdentityRecomputeTest {
    private val organization = OrganizationId.parse("11111111-1111-4111-8111-111111111111")
    private val at = Instant.parse("2026-09-09T12:00:00Z")

    @Test
    fun `recompute is authenticated bodyless and exposes real evaluator health`() = testApplication {
        application {
            val recompute = CommerceIdentityRecomputeApi(
                MercadoLivreIdentityEvidenceReader { org, _ -> listOf(ml(org)) },
                OmieIdentityEvidenceReader { org, _ -> OmieIdentityEvidenceRead(listOf(omie(org)), 1, 0) }
            )
            configureApi(
                ServiceToken.test(TEST_SERVICE_TOKEN), organization,
                record = { _, _ -> error("not used") },
                commerceIdentityHealthApi = CommerceIdentityHealthApi(recompute::current),
                commerceIdentityRecomputeApi = recompute
            )
        }
        val unauthorized = client.post("/v1/commerce-identity/recompute")
        assertEquals(HttpStatusCode.Unauthorized, unauthorized.status)

        val withBody = client.post("/v1/commerce-identity/recompute") {
            bearerAuth(TEST_SERVICE_TOKEN)
            contentType(ContentType.Application.Json)
            setBody("{}")
        }
        assertEquals(HttpStatusCode.BadRequest, withBody.status)

        val response = client.post("/v1/commerce-identity/recompute") {
            bearerAuth(TEST_SERVICE_TOKEN)
        }
        assertEquals(HttpStatusCode.OK, response.status)
        assertContains(response.bodyAsText(), "\"exactConfirmed\":1")
        assertFalse(response.bodyAsText().contains("secret"))

        val health = client.get("/v1/commerce-identity/health") {
            bearerAuth(TEST_SERVICE_TOKEN)
        }
        assertEquals(HttpStatusCode.OK, health.status)
        assertContains(health.bodyAsText(), "\"exactConfirmed\":1")
    }

    @Test
    fun `zero evidence recompute remains explicit zero`() = testApplication {
        application {
            configureApi(
                ServiceToken.test(TEST_SERVICE_TOKEN), organization,
                record = { _, _ -> error("not used") },
                commerceIdentityRecomputeApi = CommerceIdentityRecomputeApi(
                    MercadoLivreIdentityEvidenceReader { _, _ -> emptyList() },
                    OmieIdentityEvidenceReader { _, _ -> OmieIdentityEvidenceRead(emptyList(), 0, 0) }
                )
            )
        }
        val response = client.post("/v1/commerce-identity/recompute") {
            bearerAuth(TEST_SERVICE_TOKEN)
        }
        assertEquals(HttpStatusCode.OK, response.status)
        assertContains(response.bodyAsText(), "\"mlTransactionsInspected\":0")
        assertFalse(response.bodyAsText().contains("coveragePercentage"))
    }

    @Test
    fun `non evaluable persisted Omie rows are reported without failing recompute`() = testApplication {
        application {
            val records = List(117) { index -> omie(organization, "ERP-$index") }
            configureApi(
                ServiceToken.test(TEST_SERVICE_TOKEN), organization,
                record = { _, _ -> error("not used") },
                commerceIdentityRecomputeApi = CommerceIdentityRecomputeApi(
                    MercadoLivreIdentityEvidenceReader { _, _ -> emptyList() },
                    OmieIdentityEvidenceReader { _, _ -> OmieIdentityEvidenceRead(records, 132, 15) }
                )
            )
        }
        val response = client.post("/v1/commerce-identity/recompute") {
            bearerAuth(TEST_SERVICE_TOKEN)
        }
        assertEquals(HttpStatusCode.OK, response.status)
        assertContains(response.bodyAsText(), "\"omiePersistedRows\":132")
        assertContains(response.bodyAsText(), "\"omieIdentityEvaluableRows\":117")
        assertContains(response.bodyAsText(), "\"omieNonEvaluableRows\":15")
    }

    private fun ml(org: OrganizationId) = MercadoLivreTransactionEvidence(
        org, "123456789012", null, null, emptySet(), setOf("SKU"),
        mapOf("SKU" to BigDecimal.ONE), CommerceIdentityAmount("BRL", BigDecimal("10.00")), at, setOf("ml:evidence")
    )

    private fun omie(org: OrganizationId, integration: String = "ERP-1") = OmieSalesOrderEvidence(
        org, setOf("SKU"), mapOf("SKU" to BigDecimal.ONE), integration, null,
        CommerceIdentityAmount("BRL", BigDecimal("10.00")), at, setOf("omie:evidence"), setOf("123456789012")
    )
}
