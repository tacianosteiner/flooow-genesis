package io.flooow.marketplace.operations.authorization

import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.Base64
import java.util.UUID

enum class CredentialDeliveryMethod { PROTECTED_TTY_ONE_TIME }
enum class ImmediateRevocationPolicy { SEPARATE_APPROVAL_REQUIRED }

data class ApprovalManifest(
    val schemaVersion: Int,
    val manifestId: UUID,
    val organizationId: OrganizationId,
    val mercadoLivreConnectionId: UUID,
    val omieConnectionId: UUID,
    val sourceOrderReference: String,
    val integrationReference: String,
    val marketplaceOrderId: MarketplaceOrderId,
    val permission: SignerApprovalPermission,
    val accountableOperator: GovernanceSubjectId,
    val approvalSource: GovernanceSourceId,
    val approvalWindowStart: Instant,
    val approvalWindowEnd: Instant,
    val revocationOwner: GovernanceSubjectId,
    val credentialCustodian: GovernanceSubjectId,
    val credentialDeliveryMethod: CredentialDeliveryMethod,
    val credentialRotationOwner: GovernanceSubjectId,
    val immediateRevocationPolicy: ImmediateRevocationPolicy,
    val reason: String,
    val provenance: String,
    val correlationId: UUID,
    val evidenceBindingFingerprint: String
) {
    init {
        require(schemaVersion == ApprovalManifestCanonicalCodec.SCHEMA_VERSION)
        require(
            manifestId != NIL_UUID &&
                organizationId.value != NIL_UUID &&
                mercadoLivreConnectionId != NIL_UUID &&
                omieConnectionId != NIL_UUID
        )
        require(marketplaceOrderId.value != NIL_UUID && correlationId != NIL_UUID)
        require(permission == SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE)
        requireCanonicalText(sourceOrderReference, 256, "sourceOrderReference")
        requireCanonicalText(integrationReference, 60, "integrationReference")
        requireCanonicalText(reason, 512, "reason")
        requireCanonicalText(provenance, 1024, "provenance")
        requireCanonicalInstant(approvalWindowStart, "approvalWindowStart")
        requireCanonicalInstant(approvalWindowEnd, "approvalWindowEnd")
        require(approvalWindowStart < approvalWindowEnd)
        require(LOWER_HEX_64.matches(evidenceBindingFingerprint))
    }

    private companion object {
        val NIL_UUID: UUID = UUID(0, 0)
        val LOWER_HEX_64 = Regex("[0-9a-f]{64}")
    }
}

class SignedApprovalAttestation private constructor(
    val manifest: ApprovalManifest,
    val algorithmId: String,
    val signerKeyId: SignerKeyId,
    val signerKeyFingerprint: SignerKeyFingerprint,
    signatureBytes: ByteArray
) {
    private val signature = signatureBytes.copyOf()
    fun signatureBytes(): ByteArray = signature.copyOf()

    override fun equals(other: Any?): Boolean = this === other ||
        other is SignedApprovalAttestation && manifest == other.manifest && algorithmId == other.algorithmId &&
        signerKeyId == other.signerKeyId && signerKeyFingerprint == other.signerKeyFingerprint &&
        signature.contentEquals(other.signature)

    override fun hashCode(): Int {
        var result = manifest.hashCode()
        result = 31 * result + algorithmId.hashCode()
        result = 31 * result + signerKeyId.hashCode()
        result = 31 * result + signerKeyFingerprint.hashCode()
        return 31 * result + signature.contentHashCode()
    }

    companion object {
        private val CANONICAL_BASE64URL = Regex("[A-Za-z0-9_-]+")

        fun parse(
            manifest: ApprovalManifest,
            algorithmId: String,
            signerKeyId: SignerKeyId,
            signerKeyFingerprint: SignerKeyFingerprint,
            signatureBase64Url: String
        ): SignedApprovalAttestation {
            require(algorithmId == "Ed25519")
            require(CANONICAL_BASE64URL.matches(signatureBase64Url) && '=' !in signatureBase64Url)
            val decoded = try { Base64.getUrlDecoder().decode(signatureBase64Url) }
            catch (failure: IllegalArgumentException) { throw IllegalArgumentException("Invalid base64url signature", failure) }
            require(decoded.size == 64)
            require(Base64.getUrlEncoder().withoutPadding().encodeToString(decoded) == signatureBase64Url)
            return SignedApprovalAttestation(manifest, algorithmId, signerKeyId, signerKeyFingerprint, decoded)
        }
    }
}
