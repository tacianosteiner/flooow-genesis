package io.flooow.marketplace.operations.authorization

import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.security.KeyPairGenerator
import java.security.Signature
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ApprovalAttestationCanonicalCodecTest {
    @Test fun `canonical manifest strictly round trips`() {
        val bytes = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest())
        assertContentEquals(bytes, ApprovalManifestCanonicalCodec.canonicalManifestBytes(
            ApprovalManifestCanonicalCodec.decodeCanonicalManifest(bytes)
        ))
    }

    @Test fun `trailing bytes are rejected`() {
        val bytes = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest()) + byteArrayOf(0)
        assertFailsWith<IllegalArgumentException> { ApprovalManifestCanonicalCodec.decodeCanonicalManifest(bytes) }
    }

    @Test fun `truncated bytes are rejected`() {
        val bytes = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest()).dropLast(1).toByteArray()
        assertFailsWith<IllegalArgumentException> { ApprovalManifestCanonicalCodec.decodeCanonicalManifest(bytes) }
    }

    @Test fun `malformed UTF-8 is rejected without repair`() {
        val bytes = replaceFrame(canonicalBytes(), 19, byteArrayOf(0xc3.toByte(), 0x28))
        assertFailsWith<IllegalArgumentException> { ApprovalManifestCanonicalCodec.decodeCanonicalManifest(bytes) }
    }

    @Test fun `non-canonical UUID is rejected`() {
        val bytes = replaceFrame(canonicalBytes(), 2, "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA".toByteArray())
        assertFailsWith<IllegalArgumentException> { ApprovalManifestCanonicalCodec.decodeCanonicalManifest(bytes) }
    }

    @Test fun `non-canonical Instant is rejected`() {
        val bytes = replaceFrame(canonicalBytes(), 12, "2026-01-01T00:00:00Z".toByteArray())
        assertFailsWith<IllegalArgumentException> { ApprovalManifestCanonicalCodec.decodeCanonicalManifest(bytes) }
    }

    @Test fun `invalid enum is rejected`() {
        val bytes = replaceFrame(canonicalBytes(), 9, "transaction_identity_decision_write".toByteArray())
        assertFailsWith<IllegalArgumentException> { ApprovalManifestCanonicalCodec.decodeCanonicalManifest(bytes) }
    }

    @Test fun `boundary whitespace is rejected without trimming`() {
        val bytes = replaceFrame(canonicalBytes(), 19, " reason".toByteArray())
        assertFailsWith<IllegalArgumentException> { ApprovalManifestCanonicalCodec.decodeCanonicalManifest(bytes) }
    }

    @Test fun `JCA Ed25519 rejects changed signature preimage and SPKI`() {
        val signer = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
        val otherSigner = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
        val preimage = "exact canonical signature preimage".toByteArray(StandardCharsets.UTF_8)
        val signature = Signature.getInstance("Ed25519").run {
            initSign(signer.private)
            update(preimage)
            sign()
        }
        val publicKey = SignerPublicKeyInfo.parse(signer.public.encoded)

        assertTrue(Ed25519ApprovalSignatureVerifier.verify(publicKey, preimage, signature))

        val changedSignature = signature.copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() }
        assertFalse(Ed25519ApprovalSignatureVerifier.verify(publicKey, preimage, changedSignature))

        val changedPreimage = preimage.copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() }
        assertFalse(Ed25519ApprovalSignatureVerifier.verify(publicKey, changedPreimage, signature))

        val wrongPublicKey = SignerPublicKeyInfo.parse(otherSigner.public.encoded)
        assertFalse(Ed25519ApprovalSignatureVerifier.verify(wrongPublicKey, preimage, signature))
    }

    private fun canonicalBytes() = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest())

    private fun replaceFrame(source: ByteArray, frameIndex: Int, replacement: ByteArray): ByteArray {
        val frames = mutableListOf<ByteArray>()
        var position = 0
        while (position < source.size) {
            require(position + Int.SIZE_BYTES <= source.size)
            val length = ByteBuffer.wrap(source, position, Int.SIZE_BYTES).int
            position += Int.SIZE_BYTES
            require(length >= 0 && length <= source.size - position)
            frames += source.copyOfRange(position, position + length)
            position += length
        }
        frames[frameIndex] = replacement
        return ByteArrayOutputStream().also { output ->
            frames.forEach { frame ->
                output.write(ByteBuffer.allocate(Int.SIZE_BYTES).putInt(frame.size).array())
                output.write(frame)
            }
        }.toByteArray()
    }

    private fun manifest() = ApprovalManifest(
        1, UUID.fromString("11111111-1111-1111-1111-111111111111"), OrganizationId(UUID.fromString("22222222-2222-2222-2222-222222222222")),
        UUID.fromString("33333333-3333-3333-3333-333333333333"), UUID.fromString("44444444-4444-4444-4444-444444444444"),
        "OMIE-1", "ML-1", MarketplaceOrderId(UUID.fromString("55555555-5555-5555-5555-555555555555")),
        SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE, GovernanceSubjectId(UUID.fromString("66666666-6666-6666-6666-666666666666")),
        GovernanceSourceId(UUID.fromString("77777777-7777-7777-7777-777777777777")), Instant.parse("2026-01-01T00:00:00Z"), Instant.parse("2026-01-02T00:00:00Z"),
        GovernanceSubjectId(UUID.fromString("88888888-8888-8888-8888-888888888888")), GovernanceSubjectId(UUID.fromString("99999999-9999-9999-9999-999999999999")),
        CredentialDeliveryMethod.PROTECTED_TTY_ONE_TIME, GovernanceSubjectId(UUID.fromString("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")),
        ImmediateRevocationPolicy.SEPARATE_APPROVAL_REQUIRED, "reason", "provenance", UUID.fromString("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"), "c".repeat(64)
    )
}
