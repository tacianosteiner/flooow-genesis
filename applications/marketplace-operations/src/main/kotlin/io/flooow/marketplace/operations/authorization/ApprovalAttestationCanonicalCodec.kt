package io.flooow.marketplace.operations.authorization

import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.organization.OrganizationId
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.nio.charset.CodingErrorAction
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.X509EncodedKeySpec
import java.time.Instant
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeFormatterBuilder
import java.text.Normalizer
import java.util.UUID

object ApprovalManifestCanonicalCodec {
    const val SCHEMA_VERSION = 1
    const val CANONICALIZATION_VERSION = 1
    const val MANIFEST_DOMAIN = "FLOOOW:S2A:APPROVAL-MANIFEST:1"
    const val SIGNATURE_DOMAIN = "FLOOOW:S2A:APPROVAL-SIGNATURE:1"

    fun canonicalManifestBytes(manifest: ApprovalManifest): ByteArray = CanonicalWriter.record(MANIFEST_DOMAIN) {
        integer(manifest.schemaVersion); uuid(manifest.manifestId); uuid(manifest.organizationId.value)
        uuid(manifest.mercadoLivreConnectionId); uuid(manifest.omieConnectionId)
        text(manifest.sourceOrderReference); text(manifest.integrationReference); uuid(manifest.marketplaceOrderId.value)
        text(manifest.permission.name); uuid(manifest.accountableOperator.value); uuid(manifest.approvalSource.value)
        instant(manifest.approvalWindowStart); instant(manifest.approvalWindowEnd); uuid(manifest.revocationOwner.value)
        uuid(manifest.credentialCustodian.value); text(manifest.credentialDeliveryMethod.name)
        uuid(manifest.credentialRotationOwner.value); text(manifest.immediateRevocationPolicy.name)
        text(manifest.reason); text(manifest.provenance); uuid(manifest.correlationId); text(manifest.evidenceBindingFingerprint)
    }

    fun manifestDigest(canonicalManifestBytes: ByteArray): String = sha256(canonicalManifestBytes)

    fun canonicalSignaturePreimageBytes(
        algorithmId: String,
        signerKeyId: SignerKeyId,
        signerKeyFingerprint: SignerKeyFingerprint,
        manifestDigest: String
    ): ByteArray {
        require(algorithmId == "Ed25519" && HEX.matches(manifestDigest))
        return CanonicalWriter.record(SIGNATURE_DOMAIN) {
            text(algorithmId); uuid(signerKeyId.value); text(signerKeyFingerprint.value); text(manifestDigest)
        }
    }
}

object ApprovalEvidenceBindingCodec {
    const val DOMAIN = "FLOOOW:S2A:EVIDENCE-BINDING:1"
    data class Evidence(
        val organizationId: OrganizationId, val marketplaceOrderId: MarketplaceOrderId,
        val mercadoLivreConnectionId: UUID, val mlCapability: String, val mlInputProgressVersion: Long,
        val mlRecordOrdinal: Int, val marketplaceKey: String, val marketplaceExternalOrderId: String,
        val mlCurrency: String, val mlPromotionOutcome: String, val omieConnectionId: UUID,
        val omieCapability: String, val omieInputProgressVersion: Long, val omieRecordOrdinal: Int,
        val omieSourceOrderReference: String, val omieIntegrationReference: String?, val omieCurrency: String?,
        val omieSemanticFingerprintVersion: Int, val omieSemanticFingerprint: String,
        val omieProviderRevisionLocal: LocalDateTime
    )
    fun canonicalBytes(evidence: Evidence): ByteArray = CanonicalWriter.record(DOMAIN) {
        uuid(evidence.organizationId.value); uuid(evidence.marketplaceOrderId.value); uuid(evidence.mercadoLivreConnectionId)
        text(evidence.mlCapability); integer(evidence.mlInputProgressVersion); integer(evidence.mlRecordOrdinal)
        text(evidence.marketplaceKey); text(evidence.marketplaceExternalOrderId); text(evidence.mlCurrency)
        text(evidence.mlPromotionOutcome); uuid(evidence.omieConnectionId); text(evidence.omieCapability)
        integer(evidence.omieInputProgressVersion); integer(evidence.omieRecordOrdinal); text(evidence.omieSourceOrderReference)
        nullableText(evidence.omieIntegrationReference); nullableText(evidence.omieCurrency)
        integer(evidence.omieSemanticFingerprintVersion); text(evidence.omieSemanticFingerprint)
        localDateTime(evidence.omieProviderRevisionLocal)
    }
    fun fingerprint(evidence: Evidence): String = sha256(canonicalBytes(evidence))
}

object AcceptedAttestationFingerprintCodec {
    const val DOMAIN = "FLOOOW:S2A:ACCEPTED-ATTESTATION-PROOF:1"
    const val ARTIFACT_VERSION = 1
    fun canonicalBytes(proof: AcceptedAttestationProof): ByteArray = CanonicalWriter.record(DOMAIN) {
        integer(proof.artifactVersion); integer(proof.canonicalizationVersion); bytes(proof.canonicalManifestBytes())
        text(proof.manifestDigest); bytes(proof.canonicalSignaturePreimageBytes()); text(proof.algorithmId)
        uuid(proof.signerKeyId.value); integer(proof.signerKeyRevision); text(proof.signerKeyFingerprint.value)
        text(proof.signerKeyLineageFingerprint.value); bytes(proof.subjectPublicKeyInfoDer()); bytes(proof.signatureBytes())
        uuid(proof.signerAuthorityId.value); integer(proof.signerAuthorityRevision)
        text(proof.signerAuthorityFingerprint.value); instant(proof.verifiedAt)
    }
    fun fingerprint(proof: AcceptedAttestationProof): String = sha256(canonicalBytes(proof))
}

object Ed25519ApprovalSignatureVerifier {
    fun verify(
        subjectPublicKeyInfo: SignerPublicKeyInfo,
        canonicalSignaturePreimageBytes: ByteArray,
        signatureBytes: ByteArray
    ): Boolean {
        require(signatureBytes.size == 64)

        val publicKey =
            KeyFactory.getInstance("Ed25519")
                .generatePublic(
                    X509EncodedKeySpec(
                        subjectPublicKeyInfo.bytes()
                    )
                )

        val verifier =
            Signature.getInstance("Ed25519")

        verifier.initVerify(publicKey)
        verifier.update(
            canonicalSignaturePreimageBytes.copyOf()
        )

        return try {
            verifier.verify(
                signatureBytes.copyOf()
            )
        }
        catch (_: java.security.SignatureException) {
            false
        }
    }
}

private val HEX = Regex("[0-9a-f]{64}")
private fun sha256(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).toGovernanceHex()

private class CanonicalWriter {
    private val output = ByteArrayOutputStream()
    fun text(value: String) {
        require(value.isNotEmpty()) { "Canonical text must not be empty" }
        require(!value.first().isWhitespace() && !value.last().isWhitespace()) {
            "Canonical text must not have boundary whitespace"
        }
        require(value.none { it.code <= 0x1f || it.code == 0x7f }) {
            "Canonical text must not contain control characters"
        }
        require(Normalizer.isNormalized(value, Normalizer.Form.NFC)) { "Canonical text must be NFC" }
        val encoded = try {
            StandardCharsets.UTF_8.newEncoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .encode(java.nio.CharBuffer.wrap(value))
        } catch (failure: java.nio.charset.CharacterCodingException) {
            throw IllegalArgumentException("Canonical text must contain valid Unicode scalar values", failure)
        }
        val bytes = ByteArray(encoded.remaining())
        encoded.get(bytes)
        frame(bytes)
    }
    fun bytes(value: ByteArray) = frame(value.copyOf())
    fun uuid(value: UUID) = text(value.toString())
    fun integer(value: Int) { require(value >= 0); text(value.toString()) }
    fun integer(value: Long) { require(value >= 0); text(value.toString()) }
    fun instant(value: Instant) { requireCanonicalInstant(value, "Instant"); text(INSTANT.format(value)) }
    fun localDateTime(value: LocalDateTime) { require(value.nano % 1_000 == 0); text(LOCAL.format(value)) }
    fun nullableText(value: String?) { if (value == null) { text("NULL"); frame(byteArrayOf()) } else { text("PRESENT"); text(value) } }
    private fun frame(value: ByteArray) { output.write(ByteBuffer.allocate(4).putInt(value.size).array()); output.write(value) }
    companion object {
        private val INSTANT = DateTimeFormatterBuilder().appendInstant(6).toFormatter()
        private val LOCAL = DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss.SSSSSS")
        fun record(domain: String, fields: CanonicalWriter.() -> Unit): ByteArray = CanonicalWriter().apply { text(domain); fields() }.output.toByteArray()
    }
}
