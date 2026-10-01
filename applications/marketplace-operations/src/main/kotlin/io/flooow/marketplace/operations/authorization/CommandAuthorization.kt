package io.flooow.marketplace.operations.authorization

import io.flooow.organization.OrganizationId
import java.security.MessageDigest
import java.util.Base64
import java.util.UUID

enum class CommandPermission {
    TRANSACTION_IDENTITY_DECISION_WRITE,
    TRANSACTION_IDENTITY_POLICY_ADMIN
}

data class CommandPrincipalId(val value: UUID)

/** Construct only from a verified, server-resolved dedicated credential. */
class AuthenticatedCommand internal constructor(
    val organizationId: OrganizationId,
    val principalId: CommandPrincipalId,
    val mercadoLivreConnectionId: UUID,
    val omieConnectionId: UUID,
    val credentialId: UUID,
    val credentialRevision: Int
) {
    companion object {
        fun verify(
            credential: CommandCredential,
            verifier: CommandCredentialVerifier,
            organizationId: OrganizationId,
            principalId: CommandPrincipalId,
            mercadoLivreConnectionId: UUID,
            omieConnectionId: UUID,
            revision: Int
        ): AuthenticatedCommand? {
            require(revision > 0)
            if (!verifier.matches(credential)) return null
            return AuthenticatedCommand(
                organizationId, principalId, mercadoLivreConnectionId,
                omieConnectionId, credential.id, revision
            )
        }
    }
}

/** A parsed secret never exposes its material through object rendering. */
class CommandCredential private constructor(val id: UUID, private val secret: ByteArray) : AutoCloseable {
    @Volatile
    private var destroyed = false

    internal fun digest(): ByteArray = synchronized(this) {
        check(!destroyed) { "Command credential has been destroyed" }
        MessageDigest.getInstance("SHA-256").digest(
            "flooow-command-credential/1\u0000".toByteArray(Charsets.UTF_8) + secret
        )
    }

    /** Idempotently invalidates this credential and overwrites its secret material. */
    fun destroy() = synchronized(this) {
        if (!destroyed) {
            secret.fill(0)
            destroyed = true
        }
    }

    override fun close() = destroy()

    /** Narrow test-only observation: it never exposes or copies secret material. */
    internal fun isDestroyedAndZeroizedForTest(): Boolean = synchronized(this) {
        destroyed && secret.all { it == 0.toByte() }
    }

    override fun toString(): String = "CommandCredential([REDACTED])"

    companion object {
        fun parse(value: String): CommandCredential? {
            if (value.length != 84) return null
            val parts = value.split('.')
            if (parts.size != 3 || parts[0] != "fc1") return null
            val id = try { UUID.fromString(parts[1]) } catch (_: IllegalArgumentException) { return null }
            if (id.toString() != parts[1] || !parts[2].matches(Regex("[A-Za-z0-9_-]{43}"))) return null
            val bytes = try { Base64.getUrlDecoder().decode(parts[2]) } catch (_: IllegalArgumentException) { return null }
            if (bytes.size != 32 || Base64.getUrlEncoder().withoutPadding().encodeToString(bytes) != parts[2]) return null
            return CommandCredential(id, bytes)
        }
    }
}

class CommandCredentialVerifier private constructor(private val digest: ByteArray) {
    fun matches(candidate: CommandCredential): Boolean =
        MessageDigest.isEqual(digest, candidate.digest())

    fun persistenceBytes(): ByteArray = digest.copyOf()
    override fun toString(): String = "CommandCredentialVerifier([REDACTED])"

    companion object {
        fun fromCredential(credential: CommandCredential): CommandCredentialVerifier =
            CommandCredentialVerifier(credential.digest())

        fun fromPersistence(bytes: ByteArray): CommandCredentialVerifier {
            require(bytes.size == 32) { "Invalid command credential verifier shape" }
            return CommandCredentialVerifier(bytes.copyOf())
        }
    }
}

data class CommandAuthorizationLineage(
    val principalId: CommandPrincipalId,
    val grantId: UUID,
    val grantRevision: Int,
    val permission: CommandPermission,
    val semanticVersion: String,
    val semanticFingerprint: String
)

sealed interface CommandAuthorizationResult {
    data object Denied : CommandAuthorizationResult
    data class Authorized(val lineage: CommandAuthorizationLineage) : CommandAuthorizationResult
    data object IntegrityFailure : CommandAuthorizationResult
}
