package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.organization.OrganizationId
import java.security.MessageDigest
import java.sql.Connection
import java.sql.ResultSet
import java.util.UUID

/** No provisioning or connection ownership: authorization belongs to the writer transaction. */
class PostgresCommandAuthorization {
    fun authenticate(connection: Connection, token: String): AuthenticatedCommand? {
        val credential = CommandCredential.parse(token) ?: return null
        connection.prepareStatement(
            """SELECT c.*, p.mercado_livre_connection_id, p.omie_connection_id, o.status AS organization_status
                FROM command_credential_revision c
                JOIN command_principal p USING (organization_id, principal_id)
                JOIN integration_organization o USING (organization_id)
                WHERE credential_id=? ORDER BY revision DESC LIMIT 1"""
        ).use { statement ->
            statement.setObject(1, credential.id)
            statement.executeQuery().use { rows ->
                if (!rows.next()) {
                    CommandCredentialVerifier.fromPersistence(ByteArray(32)).matches(credential)
                    return null
                }
                val verified = AuthenticatedCommand.verify(
                    credential,
                    CommandCredentialVerifier.fromPersistence(rows.getBytes("secret_verifier")),
                    OrganizationId.parse(rows.uuid("organization_id").toString()),
                    CommandPrincipalId(rows.uuid("principal_id")),
                    rows.uuid("mercado_livre_connection_id"), rows.uuid("omie_connection_id"),
                    rows.getInt("revision")
                )
                return verified?.takeIf {
                    rows.getString("state") == "ENABLED" && rows.getString("organization_status") == "ACTIVE"
                }
            }
        }
    }

    fun authorizeForWrite(
        connection: Connection,
        actor: AuthenticatedCommand,
        permission: CommandPermission
    ): CommandAuthorizationResult {
        require(!connection.autoCommit) { "Command authorization requires the writer transaction" }
        require(connection.transactionIsolation == Connection.TRANSACTION_READ_COMMITTED) {
            "Command authorization requires READ COMMITTED"
        }
        connection.prepareStatement(
            "SELECT status FROM integration_organization WHERE organization_id=? FOR SHARE"
        ).use { statement ->
            statement.setObject(1, actor.organizationId.value)
            statement.executeQuery().use { rows ->
                if (!rows.next() || rows.getString(1) != "ACTIVE") return CommandAuthorizationResult.Denied
            }
        }
        connection.prepareStatement(
            """SELECT mercado_livre_connection_id, omie_connection_id FROM command_principal
                WHERE organization_id=? AND principal_id=? FOR UPDATE"""
        ).use { statement ->
            statement.setObject(1, actor.organizationId.value)
            statement.setObject(2, actor.principalId.value)
            statement.executeQuery().use { rows ->
                if (!rows.next() || rows.uuid("mercado_livre_connection_id") != actor.mercadoLivreConnectionId ||
                    rows.uuid("omie_connection_id") != actor.omieConnectionId) return CommandAuthorizationResult.Denied
            }
        }
        connection.prepareStatement(
            """SELECT revision, state FROM command_credential_revision
                WHERE organization_id=? AND principal_id=? AND credential_id=? ORDER BY revision DESC LIMIT 1"""
        ).use { statement ->
            statement.setObject(1, actor.organizationId.value)
            statement.setObject(2, actor.principalId.value)
            statement.setObject(3, actor.credentialId)
            statement.executeQuery().use { rows ->
                if (!rows.next() || rows.getInt("revision") != actor.credentialRevision ||
                    rows.getString("state") != "ENABLED") return CommandAuthorizationResult.Denied
            }
        }
        connection.prepareStatement(
            """SELECT * FROM command_permission_grant WHERE organization_id=? AND principal_id=?
                AND permission=? ORDER BY revision DESC LIMIT 1"""
        ).use { statement ->
            statement.setObject(1, actor.organizationId.value)
            statement.setObject(2, actor.principalId.value)
            statement.setString(3, permission.name)
            statement.executeQuery().use { rows ->
                if (!rows.next() || rows.getString("state") == "DISABLED") return CommandAuthorizationResult.Denied
                if (rows.getString("state") != "ENABLED" || rows.getInt("revision") < 1) {
                    return CommandAuthorizationResult.IntegrityFailure
                }
                val version = "command-authorization/1"
                val fields = listOf(
                    version, actor.organizationId.value.toString(), actor.principalId.value.toString(),
                    actor.mercadoLivreConnectionId.toString(), actor.omieConnectionId.toString(),
                    rows.uuid("grant_id").toString(), rows.getInt("revision").toString(),
                    permission.name, rows.getString("state"),
                    rows.getObject("supersedes_grant_id")?.toString() ?: "",
                    rows.getString("reason"), rows.getString("provenance"),
                    rows.uuid("correlation_id").toString(), rows.getTimestamp("decided_at").toInstant().toString()
                )
                val canonical = fields.joinToString("") { "${it.toByteArray(Charsets.UTF_8).size}:$it" }
                val fingerprint = MessageDigest.getInstance("SHA-256")
                    .digest(canonical.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
                return CommandAuthorizationResult.Authorized(CommandAuthorizationLineage(
                    actor.principalId, rows.uuid("grant_id"), rows.getInt("revision"),
                    permission, version, fingerprint
                ))
            }
        }
    }

    private fun ResultSet.uuid(column: String): UUID = getObject(column, UUID::class.java)
}
