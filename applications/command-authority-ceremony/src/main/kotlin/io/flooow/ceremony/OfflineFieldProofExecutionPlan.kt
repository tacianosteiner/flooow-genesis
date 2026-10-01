package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.CommandPrincipalId
import java.security.MessageDigest
import java.util.UUID

/** Non-secret, immutable recovery identity allocated before any durable effect. */
data class OfflineFieldProofExecutionPlan(
    val version: Int,
    val runId: UUID,
    val principalId: CommandPrincipalId,
    val credentialId: UUID,
    val grantId: UUID,
    val principalOperationId: UUID,
    val initialCredentialOperationId: UUID,
    val grantOperationId: UUID,
    val decisionId: UUID
) {
    init {
        require(version == VERSION) { "Unsupported execution-plan version" }
        val identities = listOf(
            runId,
            principalId.value,
            credentialId,
            grantId,
            principalOperationId,
            initialCredentialOperationId,
            grantOperationId,
            decisionId
        )
        require(identities.none { it == NIL_UUID }) { "Execution-plan identifiers must be non-nil" }
        require(identities.toSet().size == identities.size) { "Execution-plan identifiers must be distinct" }
    }

    fun fingerprint(): String {
        val values = listOf(
            version.toString(), runId.toString(), principalId.value.toString(), credentialId.toString(),
            grantId.toString(), principalOperationId.toString(), initialCredentialOperationId.toString(),
            grantOperationId.toString(), decisionId.toString()
        )
        val framed = values.joinToString("") { value ->
            val bytes = value.toByteArray(Charsets.UTF_8)
            "${bytes.size}:$value"
        }
        return MessageDigest.getInstance("SHA-256")
            .digest(("offline-field-proof-plan/1" + framed).toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it) }
    }

    companion object {
        const val VERSION = 1
        private val NIL_UUID = UUID(0, 0)
    }
}
