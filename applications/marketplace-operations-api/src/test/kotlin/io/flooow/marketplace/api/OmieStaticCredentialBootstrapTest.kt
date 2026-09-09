package io.flooow.marketplace.api

import io.flooow.integration.control.*
import io.flooow.organization.OrganizationId
import io.ktor.client.request.bearerAuth
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.server.application.Application
import io.ktor.server.testing.testApplication
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertContains
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class OmieStaticCredentialBootstrapTest {
    private val organization = OrganizationId.parse("11111111-1111-4111-8111-111111111111")

    @Test
    fun `happy path creates active Omie static credential and zeroizes envelope`() {
        val repository = MemoryRepository(organization)
        val vault = MemoryVault()
        val service = IntegrationControlPlaneService(repository, vault)
        val result = OmieStaticCredentialBootstrap(service)
            .bootstrap(organization, "app-key", "app-secret")

        assertEquals("omie", repository.connections.single().providerKey.value)
        assertEquals(CredentialKind.STATIC_API_CREDENTIAL, repository.connections.single().credentialKind)
        assertEquals(IntegrationConnectionStatus.ACTIVE, repository.connections.single().status)
        assertEquals(
            "{\"schemaVersion\":1,\"appKey\":\"app-key\",\"appSecret\":\"app-secret\"}",
            vault.storedBytes.decodeToString()
        )
        assertTrue(vault.lastInputBytes.all { it.toInt() == 0 })
        assertTrue(result.connectionId == repository.connections.single().id)
    }

    @Test
    fun `bind failure never produces ready and leaves connection inactive`() {
        val repository = MemoryRepository(organization, bindResult = false)
        val service = IntegrationControlPlaneService(repository, MemoryVault())

        assertFailsWith<IllegalStateException> {
            OmieStaticCredentialBootstrap(service).bootstrap(organization, "app-key", "app-secret")
        }
        assertEquals(IntegrationConnectionStatus.DRAFT, repository.connections.single().status)
    }

    @Test
    fun `inactive or different organization cannot receive a connection`() {
        val repository = MemoryRepository(organization)
        val service = IntegrationControlPlaneService(repository, MemoryVault())
        val otherOrganization = OrganizationId.parse("22222222-2222-4222-8222-222222222222")

        assertFailsWith<IllegalArgumentException> {
            OmieStaticCredentialBootstrap(service).bootstrap(otherOrganization, "app-key", "app-secret")
        }
        assertTrue(repository.connections.isEmpty())
    }

    @Test
    fun `request is authenticated and malformed credentials are rejected without disclosure`() =
        testApplication {
            application { configureForTest() }

            val unauthorized = client.post("/v1/integrations/omie/bootstrap") {
                contentType(ContentType.Application.Json)
                setBody("{\"appKey\":\"key\",\"appSecret\":\"secret\"}")
            }
            assertEquals(HttpStatusCode.Unauthorized, unauthorized.status)

            listOf(
                "{",
                "{\"appSecret\":\"secret\"}",
                "{\"appKey\":\"key\"}",
                "{\"appKey\":\" \",\"appSecret\":\"secret\"}",
                "{\"appKey\":\"key\",\"appSecret\":\"\"}",
                "{\"appKey\":1,\"appSecret\":\"secret\"}",
                "{\"appKey\":\"key\",\"appSecret\":\"secret\",\"organizationId\":\"other\"}"
            ).forEach { body ->
                val response = client.post("/v1/integrations/omie/bootstrap") {
                    bearerAuth(TEST_SERVICE_TOKEN)
                    contentType(ContentType.Application.Json)
                    setBody(body)
                }
                assertEquals(HttpStatusCode.BadRequest, response.status)
                assertFalse(response.bodyAsText().contains("app-secret"))
            }
        }

    @Test
    fun `happy HTTP response contains only status and connection identity`() = testApplication {
        application { configureForTest() }
        val response = client.post("/v1/integrations/omie/bootstrap") {
            bearerAuth(TEST_SERVICE_TOKEN)
            contentType(ContentType.Application.Json)
            setBody("{\"appKey\":\"app-key\",\"appSecret\":\"app-secret\"}")
        }
        val body = response.bodyAsText()
        assertEquals(HttpStatusCode.Created, response.status)
        assertContains(body, "\"status\":\"READY\"")
        assertContains(body, "\"connectionId\"")
        assertFalse(body.contains("app-key"))
        assertFalse(body.contains("app-secret"))
        assertFalse(body.contains("secretRef"))
    }

    @Test
    fun `HTTP bootstrap uses the authenticated principal organization`() = testApplication {
        val principalOrganization = OrganizationId.parse("33333333-3333-4333-8333-333333333333")
        val repository = MemoryRepository(principalOrganization)
        application {
            configureApi(
                serviceToken = ServiceToken.test(TEST_SERVICE_TOKEN),
                serviceOrganizationId = principalOrganization,
                record = { _, _ -> error("not used") },
                omieStaticCredentialBootstrap = OmieStaticCredentialBootstrap(
                    IntegrationControlPlaneService(repository, MemoryVault())
                )
            )
        }

        val response = client.post("/v1/integrations/omie/bootstrap") {
            bearerAuth(TEST_SERVICE_TOKEN)
            contentType(ContentType.Application.Json)
            setBody("{\"appKey\":\"app-key\",\"appSecret\":\"app-secret\"}")
        }

        assertEquals(HttpStatusCode.Created, response.status)
        assertEquals(principalOrganization, repository.connections.single().organizationId)
    }

    private fun Application.configureForTest() {
        val repository = MemoryRepository(TEST_ORGANIZATION_ID)
        configureApi(
            serviceToken = ServiceToken.test(TEST_SERVICE_TOKEN),
            serviceOrganizationId = TEST_ORGANIZATION_ID,
            record = { _, _ -> error("not used") },
            omieStaticCredentialBootstrap = OmieStaticCredentialBootstrap(
                IntegrationControlPlaneService(repository, MemoryVault())
            )
        )
    }

    private class MemoryVault : SecretVault {
        var storedBytes: ByteArray = ByteArray(0)
        var lastInputBytes: ByteArray = ByteArray(0)
        override fun store(organizationId: OrganizationId, connectionId: IntegrationConnectionId, credentialBytes: ByteArray): SecretReference {
            lastInputBytes = credentialBytes
            storedBytes = credentialBytes.copyOf()
            return SecretReference.of("memory-${connectionId.value}")
        }
        override fun <T> withSecret(organizationId: OrganizationId, connectionId: IntegrationConnectionId, reference: SecretReference, operation: (ByteArray) -> T): T = operation(storedBytes.copyOf())
        override fun revoke(organizationId: OrganizationId, connectionId: IntegrationConnectionId, reference: SecretReference) = Unit
    }

    private class MemoryRepository(
        private val organization: OrganizationId,
        private val bindResult: Boolean = true
    ) : IntegrationControlPlaneRepository {
        val connections = mutableListOf<IntegrationConnection>()
        override fun createOrganization(organization: IntegrationOrganization, audit: IntegrationAuditEntry) = Unit
        override fun findOrganization(id: OrganizationId) = if (id == organization) IntegrationOrganization(id, IntegrationOrganizationStatus.ACTIVE, Instant.EPOCH, Instant.EPOCH) else null
        override fun changeOrganizationStatus(id: OrganizationId, expected: IntegrationOrganizationStatus, updated: IntegrationOrganization, audit: IntegrationAuditEntry) = true
        override fun createConnection(connection: IntegrationConnection, audit: IntegrationAuditEntry) { connections += connection }
        override fun findConnection(organizationId: OrganizationId, connectionId: IntegrationConnectionId) = connections.find { it.organizationId == organizationId && it.id == connectionId }
        override fun bindInitialCredential(organizationId: OrganizationId, connectionId: IntegrationConnectionId, reference: SecretReference, now: Instant, audit: IntegrationAuditEntry): Boolean {
            if (!bindResult) return false
            val index = connections.indexOfFirst { it.organizationId == organizationId && it.id == connectionId }
            if (index < 0) return false
            connections[index] = connections[index].copy(status = IntegrationConnectionStatus.ACTIVE, bindingVersion = 1)
            return true
        }
        override fun rotateCredential(organizationId: OrganizationId, connectionId: IntegrationConnectionId, expectedVersion: Int, newReference: SecretReference, now: Instant, audit: IntegrationAuditEntry): SecretReference? = null
        override fun currentBinding(organizationId: OrganizationId, connectionId: IntegrationConnectionId): CredentialBinding? = null
        override fun changeConnectionStatus(organizationId: OrganizationId, connectionId: IntegrationConnectionId, expected: IntegrationConnectionStatus, target: IntegrationConnectionStatus, now: Instant, audit: IntegrationAuditEntry) = true
        override fun revokeConnection(organizationId: OrganizationId, connectionId: IntegrationConnectionId, now: Instant, audit: IntegrationAuditEntry) = true
        override fun registerDestination(destination: IntegrationDestination, audit: IntegrationAuditEntry) = Unit
        override fun findDestination(organizationId: OrganizationId, destinationId: IntegrationDestinationId): IntegrationDestination? = null
        override fun changeDestinationStatus(organizationId: OrganizationId, destinationId: IntegrationDestinationId, expected: IntegrationDestinationStatus, target: IntegrationDestinationStatus, now: Instant, audit: IntegrationAuditEntry) = true
        override fun auditEntries(organizationId: OrganizationId): List<IntegrationAuditEntry> = emptyList()
    }
}
