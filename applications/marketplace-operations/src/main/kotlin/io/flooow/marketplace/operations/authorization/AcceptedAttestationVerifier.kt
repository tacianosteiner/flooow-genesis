package io.flooow.marketplace.operations.authorization

import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.UUID

class AcceptedAttestationProof private constructor(
    val artifactVersion: Int,
    val canonicalizationVersion: Int,
    canonicalManifestBytes: ByteArray,
    val manifestDigest: String,
    canonicalSignaturePreimageBytes: ByteArray,
    val algorithmId: String,
    val signerKeyId: SignerKeyId,
    val signerKeyRevision: Int,
    val signerKeyFingerprint: SignerKeyFingerprint,
    val signerKeyLineageFingerprint: SignerKeyLineageFingerprint,
    subjectPublicKeyInfoDer: ByteArray,
    signatureBytes: ByteArray,
    val signerAuthorityId: SignerAuthorityId,
    val signerAuthorityRevision: Int,
    val signerAuthorityFingerprint: SignerAuthorityFingerprint,
    val verifiedAt: Instant
) {
    private val manifestBytes = canonicalManifestBytes.copyOf()
    private val signaturePreimage = canonicalSignaturePreimageBytes.copyOf()
    private val publicKeyDer = subjectPublicKeyInfoDer.copyOf()
    private val signature = signatureBytes.copyOf()

    fun canonicalManifestBytes() = manifestBytes.copyOf()
    fun canonicalSignaturePreimageBytes() = signaturePreimage.copyOf()
    fun subjectPublicKeyInfoDer() = publicKeyDer.copyOf()
    fun signatureBytes() = signature.copyOf()

    override fun equals(other: Any?): Boolean = this === other ||
        other is AcceptedAttestationProof && artifactVersion == other.artifactVersion &&
        canonicalizationVersion == other.canonicalizationVersion && manifestBytes.contentEquals(other.manifestBytes) &&
        manifestDigest == other.manifestDigest && signaturePreimage.contentEquals(other.signaturePreimage) &&
        algorithmId == other.algorithmId && signerKeyId == other.signerKeyId && signerKeyRevision == other.signerKeyRevision &&
        signerKeyFingerprint == other.signerKeyFingerprint && signerKeyLineageFingerprint == other.signerKeyLineageFingerprint &&
        publicKeyDer.contentEquals(other.publicKeyDer) && signature.contentEquals(other.signature) &&
        signerAuthorityId == other.signerAuthorityId && signerAuthorityRevision == other.signerAuthorityRevision &&
        signerAuthorityFingerprint == other.signerAuthorityFingerprint && verifiedAt == other.verifiedAt

    override fun hashCode(): Int {
        var result = artifactVersion
        result = 31 * result + canonicalizationVersion
        result = 31 * result + manifestBytes.contentHashCode()
        result = 31 * result + manifestDigest.hashCode()
        result = 31 * result + signaturePreimage.contentHashCode()
        result = 31 * result + algorithmId.hashCode()
        result = 31 * result + signerKeyId.hashCode()
        result = 31 * result + signerKeyRevision
        result = 31 * result + signerKeyFingerprint.hashCode()
        result = 31 * result + signerKeyLineageFingerprint.hashCode()
        result = 31 * result + publicKeyDer.contentHashCode()
        result = 31 * result + signature.contentHashCode()
        result = 31 * result + signerAuthorityId.hashCode()
        result = 31 * result + signerAuthorityRevision
        result = 31 * result + signerAuthorityFingerprint.hashCode()
        return 31 * result + verifiedAt.hashCode()
    }

    companion object {
        private val HEX = Regex("[0-9a-f]{64}")
        fun create(
            artifactVersion: Int,
            canonicalizationVersion: Int,
            canonicalManifestBytes: ByteArray,
            manifestDigest: String,
            canonicalSignaturePreimageBytes: ByteArray,
            algorithmId: String,
            signerKeyId: SignerKeyId,
            signerKeyRevision: Int,
            signerKeyFingerprint: SignerKeyFingerprint,
            signerKeyLineageFingerprint: SignerKeyLineageFingerprint,
            subjectPublicKeyInfoDer: ByteArray,
            signatureBytes: ByteArray,
            signerAuthorityId: SignerAuthorityId,
            signerAuthorityRevision: Int,
            signerAuthorityFingerprint: SignerAuthorityFingerprint,
            verifiedAt: Instant
        ): AcceptedAttestationProof {
            require(artifactVersion == 1 && canonicalizationVersion == 1)
            require(canonicalManifestBytes.isNotEmpty() && canonicalManifestBytes.size <= 4096)
            require(HEX.matches(manifestDigest) && algorithmId == "Ed25519")
            require(canonicalSignaturePreimageBytes.size == 222)
            require(signerKeyRevision > 0 && signerAuthorityRevision > 0)
            require(signatureBytes.size == 64)
            requireCanonicalInstant(verifiedAt, "verifiedAt")
            SignerPublicKeyInfo.parse(subjectPublicKeyInfoDer)
            return AcceptedAttestationProof(artifactVersion, canonicalizationVersion, canonicalManifestBytes,
                manifestDigest, canonicalSignaturePreimageBytes, algorithmId, signerKeyId, signerKeyRevision,
                signerKeyFingerprint, signerKeyLineageFingerprint, subjectPublicKeyInfoDer, signatureBytes,
                signerAuthorityId, signerAuthorityRevision, signerAuthorityFingerprint, verifiedAt)
        }
    }
}

data class AcceptedAttestationReceipt(
    val organizationId: OrganizationId,
    val manifestId: UUID,
    val manifestDigest: String,
    val acceptedProofFingerprint: String,
    val verifiedAt: Instant,
    val recordedAt: Instant
)

sealed interface AcceptedAttestationResult {
    data class Accepted(val receipt: AcceptedAttestationReceipt) : AcceptedAttestationResult
    data class AlreadyAccepted(val receipt: AcceptedAttestationReceipt) : AcceptedAttestationResult
    data object GovernanceUnavailable : AcceptedAttestationResult
    data object InvalidSignature : AcceptedAttestationResult
    data object GovernanceConflict : AcceptedAttestationResult
    data object IntegrityFailure : AcceptedAttestationResult
    data object ScopeMismatch : AcceptedAttestationResult
    data object ExpiredOrNotYetValid : AcceptedAttestationResult
    data object UnsupportedCanonicalForm : AcceptedAttestationResult
}

fun interface AcceptedAttestationVerifier {
    fun verify(attestation: SignedApprovalAttestation): AcceptedAttestationResult
}
