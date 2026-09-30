package io.flooow.marketplace.operations.authorization

import io.flooow.organization.OrganizationId
import java.security.MessageDigest
import java.time.Instant
import java.util.UUID

/** Real S2A issuance boundary.  The manifest claim is descriptive and is re-proven by PostgreSQL. */
interface AttestedCommandAuthorityIssuer {
    fun issuePrincipal(request: AttestedPrincipalRequest): AttestedAuthorityResult
    fun bindInitialCredential(request: AttestedInitialCredentialRequest): AttestedAuthorityResult
    fun grantPermission(request: AttestedGrantRequest): AttestedAuthorityResult
}

data class AttestedPrincipalRequest(
    val organizationId: OrganizationId,
    val manifestId: UUID,
    val manifestClaim: ApprovalManifest,
    val operationId: UUID,
    val principalId: CommandPrincipalId
) { init { require(manifestId == manifestClaim.manifestId && organizationId == manifestClaim.organizationId) } }

data class AttestedInitialCredentialRequest(
    val organizationId: OrganizationId,
    val manifestId: UUID,
    val manifestClaim: ApprovalManifest,
    val operationId: UUID,
    val principalId: CommandPrincipalId,
    val credentialId: UUID,
    val secretVerifier: ByteArray
) { init { require(manifestId == manifestClaim.manifestId && organizationId == manifestClaim.organizationId && secretVerifier.size == 32) } }

data class AttestedGrantRequest(
    val organizationId: OrganizationId,
    val manifestId: UUID,
    val manifestClaim: ApprovalManifest,
    val operationId: UUID,
    val principalId: CommandPrincipalId,
    val grantId: UUID
) { init { require(manifestId == manifestClaim.manifestId && organizationId == manifestClaim.organizationId) } }

data class AttestedAuthorityReceipt(
    val operationId: UUID,
    val intentFingerprint: String,
    val receiptFingerprint: String,
    val effectTime: Instant
)

sealed interface AttestedAuthorityResult {
    data class Applied(val receipt: AttestedAuthorityReceipt) : AttestedAuthorityResult
    data class AlreadyApplied(val receipt: AttestedAuthorityReceipt) : AttestedAuthorityResult
    data class Denied(val failure: AttestedAuthorityFailure) : AttestedAuthorityResult
}

enum class AttestedAuthorityFailure {
    INVALID_SIGNATURE, UNSUPPORTED_CANONICAL_FORM, SCOPE_MISMATCH,
    EXPIRED_OR_NOT_YET_VALID, GOVERNANCE_UNAVAILABLE, GOVERNANCE_CONFLICT,
    INTEGRITY_FAILURE
}

internal fun v042AuthorityIntent(vararg values: String): String = v042Hash(listOf("controlled-command-authority/2") + values)
internal fun v042AuthorityReceipt(intent: String, vararg values: String): String =
    v042Hash(listOf("controlled-command-authority-receipt/1", intent) + values)
private fun v042Hash(values: List<String>): String = MessageDigest.getInstance("SHA-256").digest(
    values.joinToString("") { "${it.toByteArray(Charsets.UTF_8).size}:$it" }.toByteArray(Charsets.UTF_8)
).joinToString("") { "%02x".format(it) }
