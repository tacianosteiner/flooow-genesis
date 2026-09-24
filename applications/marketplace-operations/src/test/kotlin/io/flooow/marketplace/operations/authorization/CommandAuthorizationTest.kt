package io.flooow.marketplace.operations.authorization

import java.util.Base64
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class CommandAuthorizationTest {
    private val id = UUID.randomUUID()
    private fun token(bytes: ByteArray) = "fc1.$id.${Base64.getUrlEncoder().withoutPadding().encodeToString(bytes)}"

    @Test
    fun `strict credential syntax excludes legacy bearer and alternate encodings`() {
        val value = token(ByteArray(32) { it.toByte() })
        assertNotNull(CommandCredential.parse(value))
        listOf("", "service-bearer", " $value", "$value ", "$value=", value.dropLast(1),
            value.replace("fc1", "FC1"), value + ".extra",
            "fc1.1.${value.substringAfterLast('.')}").forEach { assertNull(CommandCredential.parse(it)) }
    }

    @Test
    fun `verifier rejects altered secret and defensive copies preserve validation`() {
        val credential = assertNotNull(CommandCredential.parse(token(ByteArray(32) { 1 })))
        val verifier = CommandCredentialVerifier.fromCredential(credential)
        assertTrue(verifier.matches(credential))
        assertFalse(verifier.matches(assertNotNull(CommandCredential.parse(token(ByteArray(32) { 2 })))))
        val bytes = verifier.persistenceBytes()
        val restored = CommandCredentialVerifier.fromPersistence(bytes)
        bytes.fill(0)
        assertTrue(restored.matches(credential))
        assertEquals("CommandCredential([REDACTED])", credential.toString())
        assertEquals("CommandCredentialVerifier([REDACTED])", verifier.toString())
    }

    @Test
    fun `destroy is idempotent zeroizes material and rejects later credential use`() {
        val credential = assertNotNull(CommandCredential.parse(token(ByteArray(32) { 7 })))
        credential.destroy()
        credential.close()

        assertTrue(credential.isDestroyedAndZeroizedForTest())
        assertFailsWith<IllegalStateException> { credential.digest() }
        assertFailsWith<IllegalStateException> { CommandCredentialVerifier.fromCredential(credential) }
        assertEquals("CommandCredential([REDACTED])", credential.toString())
    }
}
