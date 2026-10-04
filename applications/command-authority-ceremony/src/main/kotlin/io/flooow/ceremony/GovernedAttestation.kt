package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import java.time.Instant
import java.util.UUID

/** Pure retained canonical/JCA/proof verification; no SQL and no caller truth flag. */
internal object GovernedAttestation {
    fun verify(attestation: SignedApprovalAttestation, snapshot: Map<String, Any?>) {
        fun value(name: String): Any = requireNotNull(snapshot[name]) { "SNAPSHOT_INCOMPLETE" }
        fun bytes(name: String) = value(name) as ByteArray
        fun string(name: String) = value(name) as String
        val manifest = attestation.manifest
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest)
        val digest = ApprovalManifestCanonicalCodec.manifestDigest(canonical)
        val preimage = ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes(attestation.algorithmId, attestation.signerKeyId, attestation.signerKeyFingerprint, digest)
        require(value("artifact_version") == 1 && value("schema_version") == manifest.schemaVersion && value("canonicalization_version") == ApprovalManifestCanonicalCodec.CANONICALIZATION_VERSION)
        require(bytes("canonical_manifest_bytes").contentEquals(canonical) && string("manifest_digest") == digest)
        require(bytes("signature_preimage_bytes").contentEquals(preimage) && string("algorithm_id") == attestation.algorithmId)
        require(value("signer_key_id") == attestation.signerKeyId.value && string("signer_key_fingerprint") == attestation.signerKeyFingerprint.value)
        require(bytes("signature_bytes").contentEquals(attestation.signatureBytes()))
        if (snapshot.containsKey("signed_evidence_binding_fingerprint")) require(value("signed_evidence_binding_fingerprint") == manifest.evidenceBindingFingerprint)
        val publicKey = SignerPublicKeyInfo.parse(bytes("subject_public_key_info_der"))
        require(publicKey.fingerprint() == attestation.signerKeyFingerprint)
        require(Ed25519ApprovalSignatureVerifier.verify(publicKey, preimage, bytes("signature_bytes"))) { "JCA_DENIED" }
        val proof = AcceptedAttestationProof.create(
            value("artifact_version") as Int, value("canonicalization_version") as Int, canonical, digest, preimage,
            string("algorithm_id"), SignerKeyId(value("signer_key_id") as UUID), value("signer_key_revision") as Int,
            SignerKeyFingerprint(string("signer_key_fingerprint")), SignerKeyLineageFingerprint(string("signer_key_lineage_fingerprint")),
            publicKey.bytes(), bytes("signature_bytes"), SignerAuthorityId(value("signer_authority_id") as UUID),
            value("signer_authority_revision") as Int, SignerAuthorityFingerprint(string("signer_authority_fingerprint")), value("verified_at") as Instant
        )
        require(AcceptedAttestationFingerprintCodec.fingerprint(proof) == string("accepted_proof_fingerprint")) { "PROOF_DENIED" }
    }
    fun fromBegin(stage: GovernedCall, output: Map<String, Any?>, attestation: SignedApprovalAttestation): Map<String, Any?> {
        val result = output.filterKeys { it.startsWith("result_") }.mapKeys { it.key.removePrefix("result_") }.toMutableMap()
        if (stage == GovernedCall.S05) {
            result["artifact_version"] = 1
            result["schema_version"] = attestation.manifest.schemaVersion
            result["canonicalization_version"] = ApprovalManifestCanonicalCodec.CANONICALIZATION_VERSION
            result["algorithm_id"] = attestation.algorithmId
            result["signature_bytes"] = attestation.signatureBytes()
            result["signature_preimage_bytes"] = result.remove("canonical_signature_preimage_bytes")
            result["signed_evidence_binding_fingerprint"] = attestation.manifest.evidenceBindingFingerprint
        }
        verify(attestation, result)
        return result
    }
}
