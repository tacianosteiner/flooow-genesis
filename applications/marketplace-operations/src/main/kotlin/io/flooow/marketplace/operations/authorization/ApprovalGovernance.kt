package io.flooow.marketplace.operations.authorization

import io.flooow.organization.OrganizationId
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.spec.X509EncodedKeySpec
import java.text.Normalizer
import java.time.Instant
import java.util.UUID

private val NIL_UUID: UUID = UUID(0, 0)
private val LOWER_HEX_64 = Regex("[0-9a-f]{64}")

private fun requireGovernanceId(value: UUID, label: String): UUID {
    require(value != NIL_UUID) { "$label must be a non-nil UUID" }
    return value
}

@JvmInline value class GovernanceSubjectId(val value: UUID) {
    init { requireGovernanceId(value, "GovernanceSubjectId") }
    override fun toString() = value.toString()
}
@JvmInline value class GovernanceInstitutionId(val value: UUID) {
    init { requireGovernanceId(value, "GovernanceInstitutionId") }
    override fun toString() = value.toString()
}
@JvmInline value class GovernanceSourceId(val value: UUID) {
    init { requireGovernanceId(value, "GovernanceSourceId") }
    override fun toString() = value.toString()
}
@JvmInline value class SignerKeyId(val value: UUID) {
    init { requireGovernanceId(value, "SignerKeyId") }
    override fun toString() = value.toString()
}
@JvmInline value class SignerAuthorityId(val value: UUID) {
    init { requireGovernanceId(value, "SignerAuthorityId") }
    override fun toString() = value.toString()
}

enum class SignerKeyState { ACTIVE, RETIRED, REVOKED, COMPROMISED }
enum class SignerAuthorityState { ENABLED, DISABLED }
enum class SignerRole { S2A_FIELD_PROOF_APPROVER }
enum class ApprovalAction { S2A_FIELD_PROOF_APPROVAL }
enum class SignerApprovalPermission { TRANSACTION_IDENTITY_DECISION_WRITE }

@JvmInline value class SignerKeyFingerprint(val value: String) {
    init { require(LOWER_HEX_64.matches(value)) { "Signer key fingerprint must be lowercase hexadecimal SHA-256" } }
    override fun toString() = value
}
@JvmInline value class SignerKeyLineageFingerprint(val value: String) {
    init { require(LOWER_HEX_64.matches(value)) { "Signer-key lineage fingerprint must be lowercase hexadecimal SHA-256" } }
    override fun toString() = value
}
@JvmInline value class SignerAuthorityFingerprint(val value: String) {
    init { require(LOWER_HEX_64.matches(value)) { "Signer-authority fingerprint must be lowercase hexadecimal SHA-256" } }
    override fun toString() = value
}

class SignerPublicKeyInfo private constructor(private val canonicalDer: ByteArray) {
    fun bytes(): ByteArray = canonicalDer.copyOf()
    fun fingerprint(): SignerKeyFingerprint = SignerKeyFingerprint(
        MessageDigest.getInstance("SHA-256").digest(canonicalDer).toGovernanceHex()
    )

    override fun equals(other: Any?) = other is SignerPublicKeyInfo && canonicalDer.contentEquals(other.canonicalDer)
    override fun hashCode() = canonicalDer.contentHashCode()

    companion object {
        private val ED25519_SPKI_PREFIX = byteArrayOf(
            0x30, 0x2a, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70, 0x03, 0x21, 0x00
        )

        fun parse(der: ByteArray): SignerPublicKeyInfo {
            val candidate = der.copyOf()
            require(candidate.size == 44 && candidate.copyOfRange(0, 12).contentEquals(ED25519_SPKI_PREFIX)) {
                "Signer public key must be canonical Ed25519 SubjectPublicKeyInfo DER"
            }
            val decoded = try {
                KeyFactory.getInstance("Ed25519").generatePublic(X509EncodedKeySpec(candidate))
            } catch (failure: Exception) {
                throw IllegalArgumentException("Signer public key must be valid Ed25519 SubjectPublicKeyInfo DER", failure)
            }
            require(decoded.encoded.contentEquals(candidate)) {
                "Signer public key must round-trip as canonical Ed25519 SubjectPublicKeyInfo DER"
            }
            return SignerPublicKeyInfo(candidate)
        }
    }
}

data class SignerKeyRevision(
    val organizationId: OrganizationId,
    val signerKeyId: SignerKeyId,
    val revision: Int,
    val signerSubjectId: GovernanceSubjectId,
    val subjectPublicKeyInfo: SignerPublicKeyInfo,
    val signerKeyFingerprint: SignerKeyFingerprint,
    val state: SignerKeyState,
    val validFrom: Instant,
    val effectiveAt: Instant,
    val supersedesRevision: Int?,
    val predecessorLineageFingerprint: SignerKeyLineageFingerprint?,
    val lineageFingerprint: SignerKeyLineageFingerprint,
    val reason: String,
    val provenance: String,
    val correlationId: UUID
) {
    val algorithmId: String get() = "Ed25519"
    init {
        require(revision > 0) { "Revision must be positive" }
        require((revision == 1 && supersedesRevision == null && predecessorLineageFingerprint == null) ||
            (revision > 1 && supersedesRevision == revision - 1 && predecessorLineageFingerprint != null)) {
            "Signer-key predecessor representation must be exact"
        }
        require(signerKeyFingerprint == subjectPublicKeyInfo.fingerprint()) { "Signer-key fingerprint does not match SPKI" }
        requireCanonicalInstant(validFrom, "validFrom")
        requireCanonicalInstant(effectiveAt, "effectiveAt")
        requireCanonicalText(reason, 512, "reason")
        requireCanonicalText(provenance, 1024, "provenance")
        requireGovernanceId(correlationId, "correlationId")
    }
}

data class SignerAuthorityRevision(
    val organizationId: OrganizationId,
    val signerAuthorityId: SignerAuthorityId,
    val revision: Int,
    val signerSubjectId: GovernanceSubjectId,
    val signerAuthorizingInstitutionId: GovernanceInstitutionId,
    val signerRole: SignerRole,
    val signerKeyId: SignerKeyId,
    val signerKeyRevision: Int,
    val signerKeyFingerprint: SignerKeyFingerprint,
    val approvalAction: ApprovalAction,
    val permission: SignerApprovalPermission,
    val validFrom: Instant,
    val validUntil: Instant,
    val state: SignerAuthorityState,
    val supersedesSignerAuthorityId: SignerAuthorityId?,
    val predecessorSignerAuthorityFingerprint: SignerAuthorityFingerprint?,
    val signerAuthorityFingerprint: SignerAuthorityFingerprint,
    val reason: String,
    val provenance: String,
    val approvalSourceId: GovernanceSourceId,
    val correlationId: UUID
) {
    init {
        require(revision > 0 && signerKeyRevision > 0) { "Revisions must be positive" }
        require((revision == 1 && supersedesSignerAuthorityId == null && predecessorSignerAuthorityFingerprint == null) ||
            (revision > 1 && supersedesSignerAuthorityId != null && predecessorSignerAuthorityFingerprint != null)) {
            "Signer-authority predecessor representation must be exact"
        }
        require(validFrom < validUntil) { "Signer-authority validity window must be non-empty" }
        requireCanonicalInstant(validFrom, "validFrom")
        requireCanonicalInstant(validUntil, "validUntil")
        requireCanonicalText(reason, 512, "reason")
        requireCanonicalText(provenance, 1024, "provenance")
        requireGovernanceId(correlationId, "correlationId")
    }
}

interface ApprovalGovernance {
    fun appendSignerKeyRevision(revision: SignerKeyRevision): GovernanceAppendResult
    fun appendSignerAuthorityRevision(revision: SignerAuthorityRevision): GovernanceAppendResult
}

sealed interface GovernanceAppendReceipt {
    val organizationId: OrganizationId
    val revision: Int
    val fingerprint: String
    val serverRecordedAt: Instant

    data class SignerKey(
        override val organizationId: OrganizationId,
        val signerKeyId: SignerKeyId,
        override val revision: Int,
        override val fingerprint: String,
        override val serverRecordedAt: Instant
    ) : GovernanceAppendReceipt

    data class SignerAuthority(
        override val organizationId: OrganizationId,
        val signerAuthorityId: SignerAuthorityId,
        override val revision: Int,
        override val fingerprint: String,
        override val serverRecordedAt: Instant
    ) : GovernanceAppendReceipt
}

sealed interface GovernanceAppendResult {
    data class Applied(val receipt: GovernanceAppendReceipt) : GovernanceAppendResult
    data class AlreadyApplied(val receipt: GovernanceAppendReceipt) : GovernanceAppendResult
    data object Conflict : GovernanceAppendResult
    data object IntegrityFailure : GovernanceAppendResult
    data object GovernanceUnavailable : GovernanceAppendResult
}

internal fun requireCanonicalInstant(value: Instant, label: String) {
    require(value.nano % 1_000 == 0) { "$label must have microsecond precision" }
}

internal fun requireCanonicalText(value: String, maximumUtf8Bytes: Int, label: String) {
    require(value.isNotEmpty()) { "$label must not be empty" }
    require(value == Normalizer.normalize(value, Normalizer.Form.NFC)) { "$label must already be NFC" }
    require(value.firstOrNull()?.isWhitespace() != true && value.lastOrNull()?.isWhitespace() != true) {
        "$label must not have leading or trailing whitespace"
    }
    require(value.none { it.code in 0..31 || it.code == 127 }) { "$label contains a prohibited control character" }
    require(value.toByteArray(Charsets.UTF_8).size <= maximumUtf8Bytes) { "$label exceeds its UTF-8 byte bound" }
    var index = 0
    while (index < value.length) {
        val current = value[index]
        when {
            Character.isHighSurrogate(current) -> {
                require(index + 1 < value.length && Character.isLowSurrogate(value[index + 1])) {
                    "$label contains an invalid Unicode scalar value"
                }
                index += 2
            }
            Character.isLowSurrogate(current) -> throw IllegalArgumentException("$label contains an invalid Unicode scalar value")
            else -> index++
        }
    }
}

internal fun ByteArray.toGovernanceHex(): String = joinToString("") { "%02x".format(it) }
