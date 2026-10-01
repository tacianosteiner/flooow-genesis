package io.flooow.marketplace.operations.authorization

import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.time.Instant
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeFormatterBuilder
import java.util.UUID

object ApprovalGovernanceFingerprintCodec {
    const val KEY_DOMAIN = "FLOOOW:S2A:SIGNER-KEY-LINEAGE:1"
    const val AUTHORITY_DOMAIN = "FLOOOW:S2A:SIGNER-AUTHORITY-LINEAGE:1"
    private val instantFormatter: DateTimeFormatter = DateTimeFormatterBuilder().appendInstant(6).toFormatter()

    fun signerKeyPreimage(revision: SignerKeyRevision): ByteArray = record(KEY_DOMAIN) {
        text(revision.organizationId.value.toString())
        text(revision.signerKeyId.value.toString())
        integer(revision.revision)
        text(revision.signerSubjectId.value.toString())
        text(revision.algorithmId)
        bytes(revision.subjectPublicKeyInfo.bytes())
        text(revision.signerKeyFingerprint.value)
        text(revision.state.name)
        instant(revision.validFrom)
        instant(revision.effectiveAt)
        nullableInteger(revision.supersedesRevision)
        nullableText(revision.predecessorLineageFingerprint?.value)
    }

    fun signerKeyFingerprint(revision: SignerKeyRevision): SignerKeyLineageFingerprint =
        SignerKeyLineageFingerprint(sha256(signerKeyPreimage(revision)))

    fun signerAuthorityPreimage(revision: SignerAuthorityRevision): ByteArray = record(AUTHORITY_DOMAIN) {
        text(revision.organizationId.value.toString())
        text(revision.signerAuthorityId.value.toString())
        integer(revision.revision)
        text(revision.signerSubjectId.value.toString())
        text(revision.signerAuthorizingInstitutionId.value.toString())
        text(revision.signerRole.name)
        text(revision.signerKeyId.value.toString())
        integer(revision.signerKeyRevision)
        text(revision.signerKeyFingerprint.value)
        text(revision.approvalAction.name)
        text(revision.permission.name)
        instant(revision.validFrom)
        instant(revision.validUntil)
        text(revision.state.name)
        text(revision.approvalSourceId.value.toString())
        nullableText(revision.supersedesSignerAuthorityId?.value?.toString())
        nullableText(revision.predecessorSignerAuthorityFingerprint?.value)
    }

    fun signerAuthorityFingerprint(revision: SignerAuthorityRevision): SignerAuthorityFingerprint =
        SignerAuthorityFingerprint(sha256(signerAuthorityPreimage(revision)))

    private fun sha256(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).toGovernanceHex()

    private fun record(domain: String, fields: CanonicalWriter.() -> Unit): ByteArray =
        CanonicalWriter().apply { text(domain); fields() }.toByteArray()

    private class CanonicalWriter {
        private val output = ByteArrayOutputStream()

        fun text(value: String) = frame(value.toByteArray(StandardCharsets.UTF_8))
        fun integer(value: Int) { require(value >= 0); text(value.toString()) }
        fun instant(value: Instant) { requireCanonicalInstant(value, "Instant"); text(instantFormatter.format(value)) }
        fun bytes(value: ByteArray) = frame(value.copyOf())
        fun nullableInteger(value: Int?) {
            if (value == null) { text("NULL"); frame(byteArrayOf()) } else { text("PRESENT"); integer(value) }
        }
        fun nullableText(value: String?) {
            if (value == null) { text("NULL"); frame(byteArrayOf()) } else { text("PRESENT"); text(value) }
        }
        fun toByteArray(): ByteArray = output.toByteArray()
        private fun frame(value: ByteArray) {
            output.write(ByteBuffer.allocate(Int.SIZE_BYTES).putInt(value.size).array())
            output.write(value)
        }
    }
}
