package io.flooow.marketplace.operations.authorization

import io.flooow.organization.OrganizationId
import java.security.MessageDigest
import java.util.UUID

/** Offline capability. It has no HTTP representation and never returns secret material. */
interface ControlledCommandAuthorityIssuer {
    fun issuePrincipal(request: PrincipalIssuance): ControlledAuthorityResult
    fun bindInitialCredential(request: InitialCredentialBinding): ControlledAuthorityResult
    fun rotateCredential(request: CredentialRotation): ControlledAuthorityResult
    fun grantPermission(request: PermissionGrant): ControlledAuthorityResult
    fun revokePermission(request: PermissionRevocation): ControlledAuthorityResult
}

enum class ControlledAuthorityOperation { PRINCIPAL, INITIAL_CREDENTIAL, ROTATE_CREDENTIAL, GRANT, REVOKE }

data class ControlledAuthorityReceipt(
    val organizationId: OrganizationId,
    val operationId: UUID,
    val operation: ControlledAuthorityOperation,
    val principalId: CommandPrincipalId,
    val credentialId: UUID?,
    val credentialRevision: Int?,
    val grantId: UUID?,
    val grantRevision: Int?,
    val permission: CommandPermission?,
    val state: String?,
    val intentFingerprint: String,
    val receiptFingerprint: String
)

sealed interface ControlledAuthorityResult {
    data class Applied(val receipt: ControlledAuthorityReceipt) : ControlledAuthorityResult
    data class AlreadyApplied(val receipt: ControlledAuthorityReceipt) : ControlledAuthorityResult
    data object IntegrityFailure : ControlledAuthorityResult
    data object AuthorityUnavailable : ControlledAuthorityResult
}

data class PrincipalIssuance(
    val operationId: UUID,
    val organizationId: OrganizationId,
    val principalId: CommandPrincipalId,
    val mercadoLivreConnectionId: UUID,
    val omieConnectionId: UUID,
    val reason: String,
    val provenance: String,
    val correlationId: UUID
) { fun intentFingerprint() = authorityIntent("principal", operationId, organizationId.value, principalId.value,
    mercadoLivreConnectionId, omieConnectionId, reason, provenance, correlationId) }

data class InitialCredentialBinding(
    val operationId: UUID,
    val organizationId: OrganizationId,
    val principalId: CommandPrincipalId,
    val credential: CommandCredential,
    val reason: String,
    val provenance: String,
    val correlationId: UUID
) { fun intentFingerprint() = authorityIntent("initial-credential", operationId, organizationId.value, principalId.value,
    credential.id, CommandCredentialVerifier.fromCredential(credential).persistenceBytes().toHex(), reason, provenance, correlationId) }

data class CredentialRotation(
    val operationId: UUID,
    val organizationId: OrganizationId,
    val principalId: CommandPrincipalId,
    val credential: CommandCredential,
    val reason: String,
    val provenance: String,
    val correlationId: UUID
) { fun intentFingerprint() = authorityIntent("rotate-credential", operationId, organizationId.value, principalId.value,
    credential.id, CommandCredentialVerifier.fromCredential(credential).persistenceBytes().toHex(), reason, provenance, correlationId) }

data class PermissionGrant(
    val operationId: UUID,
    val organizationId: OrganizationId,
    val principalId: CommandPrincipalId,
    val grantId: UUID,
    val permission: CommandPermission,
    val reason: String,
    val provenance: String,
    val correlationId: UUID
) { fun intentFingerprint() = authorityIntent("grant", operationId, organizationId.value, principalId.value,
    grantId, permission.name, reason, provenance, correlationId) }

data class PermissionRevocation(
    val operationId: UUID,
    val organizationId: OrganizationId,
    val principalId: CommandPrincipalId,
    val grantId: UUID,
    val supersedesGrantId: UUID,
    val permission: CommandPermission,
    val reason: String,
    val provenance: String,
    val correlationId: UUID
) { fun intentFingerprint() = authorityIntent("revoke", operationId, organizationId.value, principalId.value,
    grantId, supersedesGrantId, permission.name, reason, provenance, correlationId) }

private fun authorityIntent(kind: String, vararg values: Any): String = authorityHash(listOf("controlled-command-authority/1", kind) + values.map { it.toString() })
fun authorityReceipt(intent: String, vararg values: String): String = authorityHash(listOf("controlled-command-authority-receipt/1", intent) + values)
private fun authorityHash(values: List<String>): String = MessageDigest.getInstance("SHA-256").digest(
    values.joinToString("") { "${it.toByteArray(Charsets.UTF_8).size}:$it" }.toByteArray(Charsets.UTF_8)
).joinToString("") { "%02x".format(it) }
private fun ByteArray.toHex(): String = joinToString("") { "%02x".format(it) }
