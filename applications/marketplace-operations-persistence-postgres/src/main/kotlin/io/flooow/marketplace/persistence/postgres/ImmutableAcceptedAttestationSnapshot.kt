package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.AcceptedAttestationFingerprintCodec
import io.flooow.marketplace.operations.authorization.AcceptedAttestationProof
import io.flooow.marketplace.operations.authorization.ApprovalManifest
import io.flooow.marketplace.operations.authorization.ApprovalManifestCanonicalCodec
import io.flooow.marketplace.operations.authorization.AttestedAuthorityFailure
import io.flooow.marketplace.operations.authorization.Ed25519ApprovalSignatureVerifier
import io.flooow.marketplace.operations.authorization.SignerAuthorityFingerprint
import io.flooow.marketplace.operations.authorization.SignerAuthorityId
import io.flooow.marketplace.operations.authorization.SignerKeyFingerprint
import io.flooow.marketplace.operations.authorization.SignerKeyId
import io.flooow.marketplace.operations.authorization.SignerKeyLineageFingerprint
import io.flooow.marketplace.operations.authorization.SignerPublicKeyInfo
import java.sql.ResultSet
import java.time.Instant
import java.util.UUID

/** Immutable V041/V042 artifact used at the Java JCA boundary before any durable authority effect. */
internal class ImmutableAcceptedAttestationSnapshot private constructor(
    val artifactVersion: Int,
    val schemaVersion: Int,
    val canonicalizationVersion: Int,
    canonicalManifestBytes: ByteArray,
    val manifestDigest: String,
    canonicalSignaturePreimageBytes: ByteArray,
    val algorithmId: String,
    val signerSubjectId: UUID,
    val signerKeyId: UUID,
    val signerKeyRevision: Int,
    val signerKeyFingerprint: String,
    val signerKeyLineageFingerprint: String,
    subjectPublicKeyInfoDer: ByteArray,
    signatureBytes: ByteArray,
    val signerAuthorityId: UUID,
    val signerAuthorityRevision: Int,
    val signerAuthorityFingerprint: String,
    val verifiedAt: Instant,
    val acceptedProofFingerprint: String,
    val signedEvidenceBindingFingerprint: String
) {
    private val manifestBytes = canonicalManifestBytes.copyOf()
    private val signaturePreimage = canonicalSignaturePreimageBytes.copyOf()
    private val publicKeyDer = subjectPublicKeyInfoDer.copyOf()
    private val signature = signatureBytes.copyOf()

    fun canonicalManifestBytes() = manifestBytes.copyOf()
    fun canonicalSignaturePreimageBytes() = signaturePreimage.copyOf()
    fun subjectPublicKeyInfoDer() = publicKeyDer.copyOf()
    fun signatureBytes() = signature.copyOf()

    companion object {
        fun fromV042(row: ResultSet) = ImmutableAcceptedAttestationSnapshot(
            row.getInt("result_artifact_version"),
            row.getInt("result_schema_version"),
            row.getInt("result_canonicalization_version"),
            row.getBytes("result_canonical_manifest_bytes"),
            row.getString("result_manifest_digest"),
            row.getBytes("result_signature_preimage_bytes"),
            row.getString("result_algorithm_id"),
            row.getObject("result_signer_subject_id", UUID::class.java),
            row.getObject("result_signer_key_id", UUID::class.java),
            row.getInt("result_signer_key_revision"),
            row.getString("result_signer_key_fingerprint"),
            row.getString("result_signer_key_lineage_fingerprint"),
            row.getBytes("result_subject_public_key_info_der"),
            row.getBytes("result_signature_bytes"),
            row.getObject("result_signer_authority_id", UUID::class.java),
            row.getInt("result_signer_authority_revision"),
            row.getString("result_signer_authority_fingerprint"),
            row.getTimestamp("result_verified_at").toInstant(),
            row.getString("result_accepted_proof_fingerprint"),
            row.getString("result_signed_evidence_binding_fingerprint")
        )

        fun fromV041(
            row: ResultSet,
            manifest: ApprovalManifest,
            algorithmId: String,
            signatureBytes: ByteArray
        ) = ImmutableAcceptedAttestationSnapshot(
            1,
            manifest.schemaVersion,
            ApprovalManifestCanonicalCodec.CANONICALIZATION_VERSION,
            row.getBytes("result_canonical_manifest_bytes"),
            row.getString("result_manifest_digest"),
            row.getBytes("result_canonical_signature_preimage_bytes"),
            algorithmId,
            row.getObject("result_signer_subject_id", UUID::class.java),
            row.getObject("result_signer_key_id", UUID::class.java),
            row.getInt("result_signer_key_revision"),
            row.getString("result_signer_key_fingerprint"),
            row.getString("result_signer_key_lineage_fingerprint"),
            row.getBytes("result_subject_public_key_info_der"),
            signatureBytes,
            row.getObject("result_signer_authority_id", UUID::class.java),
            row.getInt("result_signer_authority_revision"),
            row.getString("result_signer_authority_fingerprint"),
            row.getTimestamp("result_verified_at").toInstant(),
            row.getString("result_accepted_proof_fingerprint"),
            manifest.evidenceBindingFingerprint
        )
    }
}

internal object ImmutableAcceptedAttestationVerifier {
    fun verify(
        expectedManifest: ApprovalManifest,
        snapshot: ImmutableAcceptedAttestationSnapshot
    ): AttestedAuthorityFailure? = try {
        val canonicalManifest = ApprovalManifestCanonicalCodec.canonicalManifestBytes(expectedManifest)
        val decodedManifest = ApprovalManifestCanonicalCodec.decodeCanonicalManifest(snapshot.canonicalManifestBytes())
        val manifestDigest = ApprovalManifestCanonicalCodec.manifestDigest(canonicalManifest)
        val signerKeyId = SignerKeyId(snapshot.signerKeyId)
        val signerKeyFingerprint = SignerKeyFingerprint(snapshot.signerKeyFingerprint)
        val signaturePreimage = ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes(
            snapshot.algorithmId,
            signerKeyId,
            signerKeyFingerprint,
            manifestDigest
        )

        if (
            snapshot.artifactVersion != 1 ||
            snapshot.schemaVersion != expectedManifest.schemaVersion ||
            snapshot.canonicalizationVersion != ApprovalManifestCanonicalCodec.CANONICALIZATION_VERSION ||
            decodedManifest != expectedManifest ||
            !snapshot.canonicalManifestBytes().contentEquals(canonicalManifest) ||
            snapshot.manifestDigest != manifestDigest ||
            !snapshot.canonicalSignaturePreimageBytes().contentEquals(signaturePreimage) ||
            snapshot.signedEvidenceBindingFingerprint != expectedManifest.evidenceBindingFingerprint
        ) return AttestedAuthorityFailure.INTEGRITY_FAILURE

        val publicKey = SignerPublicKeyInfo.parse(snapshot.subjectPublicKeyInfoDer())
        if (publicKey.fingerprint() != signerKeyFingerprint) return AttestedAuthorityFailure.INTEGRITY_FAILURE
        if (!Ed25519ApprovalSignatureVerifier.verify(publicKey, signaturePreimage, snapshot.signatureBytes())) {
            return AttestedAuthorityFailure.INVALID_SIGNATURE
        }

        val proof = AcceptedAttestationProof.create(
            snapshot.artifactVersion,
            snapshot.canonicalizationVersion,
            canonicalManifest,
            manifestDigest,
            signaturePreimage,
            snapshot.algorithmId,
            signerKeyId,
            snapshot.signerKeyRevision,
            signerKeyFingerprint,
            SignerKeyLineageFingerprint(snapshot.signerKeyLineageFingerprint),
            publicKey.bytes(),
            snapshot.signatureBytes(),
            SignerAuthorityId(snapshot.signerAuthorityId),
            snapshot.signerAuthorityRevision,
            SignerAuthorityFingerprint(snapshot.signerAuthorityFingerprint),
            snapshot.verifiedAt
        )
        if (AcceptedAttestationFingerprintCodec.fingerprint(proof) != snapshot.acceptedProofFingerprint) {
            AttestedAuthorityFailure.INTEGRITY_FAILURE
        } else {
            null
        }
    } catch (_: IllegalArgumentException) {
        AttestedAuthorityFailure.UNSUPPORTED_CANONICAL_FORM
    }
}
