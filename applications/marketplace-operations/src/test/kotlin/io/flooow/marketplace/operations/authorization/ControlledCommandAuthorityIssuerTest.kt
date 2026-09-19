package io.flooow.marketplace.operations.authorization

import io.flooow.organization.OrganizationId
import java.util.Base64
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

class ControlledCommandAuthorityIssuerTest {
    private val org = OrganizationId.parse(UUID.randomUUID().toString())
    private val principal = CommandPrincipalId(UUID.randomUUID())
    private fun credential(id: UUID = UUID.randomUUID(), byte: Byte = 1) = CommandCredential.parse(
        "fc1.$id.${Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(32) { byte })}"
    )!!

    @Test fun `provisioning intent binds operation and semantic authority but excludes no secret receipt`() {
        val request = InitialCredentialBinding(UUID.randomUUID(), org, principal, credential(), "approved", "synthetic", UUID.randomUUID())
        val same = request.copy()
        assertEquals(request.intentFingerprint(), same.intentFingerprint())
        assertNotEquals(request.intentFingerprint(), request.copy(operationId = UUID.randomUUID()).intentFingerprint())
        assertTrue(request.credential.toString().contains("REDACTED"))
    }
}
