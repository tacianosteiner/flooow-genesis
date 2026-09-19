package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import java.sql.Connection
import java.sql.SQLException
import java.util.UUID
import javax.sql.DataSource

/** Offline issuer capability. Its DataSource must authenticate as a member of flooow_command_issuer. */
class PostgresControlledCommandAuthorityIssuer(private val dataSource: DataSource) : ControlledCommandAuthorityIssuer {
    override fun issuePrincipal(request: PrincipalIssuance) = provision(request.operationId, request.organizationId, request.intentFingerprint(), ControlledAuthorityOperation.PRINCIPAL, request.principalId, request.correlationId) { c ->
        advisory(c, "command-authority-principal/1:${request.organizationId.value}:${request.principalId.value}")
        insert(c, "INSERT INTO command_principal VALUES (?,?,?,?,?,?,?,clock_timestamp())", request.organizationId.value, request.principalId.value,
            request.mercadoLivreConnectionId, request.omieConnectionId, request.reason, request.provenance, request.correlationId)
        parts(request.principalId, null, null, null, null, null, null)
    }

    override fun bindInitialCredential(request: InitialCredentialBinding) = credential(request, ControlledAuthorityOperation.INITIAL_CREDENTIAL, true)
    override fun rotateCredential(request: CredentialRotation) = credential(request, ControlledAuthorityOperation.ROTATE_CREDENTIAL, false)

    override fun grantPermission(request: PermissionGrant) = provision(request.operationId, request.organizationId, request.intentFingerprint(), ControlledAuthorityOperation.GRANT, request.principalId, request.correlationId) { c ->
        principalLock(c, request.organizationId.value, request.principalId.value)
        if (latestGrant(c, request.organizationId.value, request.principalId.value, request.permission) != null) throw Integrity()
        insert(c, "INSERT INTO command_permission_grant VALUES (?,?,?,?,'ENABLED',1,NULL,?,?,?,clock_timestamp())", request.organizationId.value,
            request.principalId.value, request.grantId, request.permission.name, request.reason, request.provenance, request.correlationId)
        parts(request.principalId, null, null, request.grantId, 1, request.permission, "ENABLED")
    }

    override fun revokePermission(request: PermissionRevocation) = provision(request.operationId, request.organizationId, request.intentFingerprint(), ControlledAuthorityOperation.REVOKE, request.principalId, request.correlationId) { c ->
        principalLock(c, request.organizationId.value, request.principalId.value)
        val current = latestGrant(c, request.organizationId.value, request.principalId.value, request.permission) ?: throw Integrity()
        if (current.id != request.supersedesGrantId || current.state != "ENABLED") throw Integrity()
        insert(c, "INSERT INTO command_permission_grant VALUES (?,?,?,?,'DISABLED',?,?,?,?,?,clock_timestamp())", request.organizationId.value,
            request.principalId.value, request.grantId, request.permission.name, current.revision + 1, current.id, request.reason, request.provenance, request.correlationId)
        parts(request.principalId, null, null, request.grantId, current.revision + 1, request.permission, "DISABLED")
    }

    private fun credential(request: Any, operation: ControlledAuthorityOperation, initial: Boolean): ControlledAuthorityResult {
        val value = when (request) { is InitialCredentialBinding -> CredentialData(request.operationId, request.organizationId, request.principalId, request.credential, request.reason, request.provenance, request.correlationId, request.intentFingerprint())
            is CredentialRotation -> CredentialData(request.operationId, request.organizationId, request.principalId, request.credential, request.reason, request.provenance, request.correlationId, request.intentFingerprint())
            else -> error("Unsupported credential request") }
        return provision(value.operationId, value.organizationId, value.intent, operation, value.principalId, value.correlationId) { c ->
            principalLock(c, value.organizationId.value, value.principalId.value)
            val existing = credentialRevision(c, value.organizationId.value, value.principalId.value, value.credential.id)
            if (initial && (existing != null || hasCredential(c, value.organizationId.value, value.principalId.value)) || !initial && existing == null) throw Integrity()
            val revision = if (initial) 1 else existing!!.revision + 1
            insert(c, "INSERT INTO command_credential_revision VALUES (?,?,?,?,?,'ENABLED',?,?,?, ?,clock_timestamp())", value.organizationId.value,
                value.principalId.value, value.credential.id, revision, existing?.revision,
                CommandCredentialVerifier.fromCredential(value.credential).persistenceBytes(), value.reason, value.provenance, value.correlationId)
            parts(value.principalId, value.credential.id, revision, null, null, null, "ENABLED")
        }
    }

    private fun provision(operationId: UUID, org: io.flooow.organization.OrganizationId, intent: String, operation: ControlledAuthorityOperation,
        principal: CommandPrincipalId, correlation: UUID, write: (Connection) -> Parts): ControlledAuthorityResult {
        return dataSource.connection.use { c ->
            c.autoCommit = false
            c.transactionIsolation = Connection.TRANSACTION_READ_COMMITTED
            try {
                issuer(c)
                advisory(c, "command-authority-operation/1:${org.value}:$operationId")
                existing(c, org.value, operationId)?.let { old ->
                    c.rollback()
                    return if (old.intentFingerprint == intent) ControlledAuthorityResult.AlreadyApplied(old) else ControlledAuthorityResult.IntegrityFailure
                }
                val result = write(c)
                val receipt = receipt(org, operationId, operation, result, intent)
                insert(c, "INSERT INTO command_authority_operation (organization_id,operation_id,operation,principal_id,credential_id,credential_revision,grant_id,grant_revision,permission,state,intent_fingerprint,receipt_fingerprint,correlation_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    org.value, operationId, operation.name, result.principal.value, result.credentialId, result.credentialRevision, result.grantId,
                    result.grantRevision, result.permission?.name, result.state, intent, receipt.receiptFingerprint, correlation)
                c.commit(); ControlledAuthorityResult.Applied(receipt)
            } catch (e: Integrity) { c.rollback(); ControlledAuthorityResult.IntegrityFailure
            } catch (e: SQLException) { c.rollback(); when (e.sqlState) { "P0012", "42501" -> ControlledAuthorityResult.AuthorityUnavailable; "23505", "23514", "23503", "23502" -> ControlledAuthorityResult.IntegrityFailure; else -> throw e }
            } catch (e: Throwable) { c.rollback(); throw e }
        }
    }

    private fun issuer(c: Connection) {
        c.prepareStatement("SELECT pg_has_role(current_user,'flooow_command_issuer','member')").use { s -> s.executeQuery().use { r ->
            if (!r.next() || !r.getBoolean(1)) throw SQLException("Protected issuer role required", "42501") } }
    }
    private fun principalLock(c: Connection, org: UUID, principal: UUID) {
        advisory(c, "command-authority-principal/1:$org:$principal")
        c.prepareStatement("SELECT 1 FROM command_principal WHERE organization_id=? AND principal_id=? FOR UPDATE").use { s ->
            s.setObject(1, org); s.setObject(2, principal); s.executeQuery().use { r -> if (!r.next()) throw Integrity() } }
    }
    private fun advisory(c: Connection, resource: String) = c.prepareStatement("SELECT pg_advisory_xact_lock(hashtextextended(?,0))").use { s -> s.setString(1, resource); s.executeQuery().close() }
    private fun existing(c: Connection, org: UUID, operation: UUID): ControlledAuthorityReceipt? = c.prepareStatement("SELECT * FROM command_authority_operation WHERE organization_id=? AND operation_id=?").use { s ->
        s.setObject(1, org); s.setObject(2, operation); s.executeQuery().use { r -> if (!r.next()) null else receiptFrom(r) } }
    private fun credentialRevision(c: Connection, org: UUID, principal: UUID, credential: UUID): Leaf? = c.prepareStatement("SELECT revision,state FROM command_credential_revision WHERE organization_id=? AND principal_id=? AND credential_id=? ORDER BY revision DESC LIMIT 1").use { s ->
        s.setObject(1, org);s.setObject(2, principal);s.setObject(3, credential);s.executeQuery().use { r -> if(r.next()) Leaf(credential,r.getInt(1),r.getString(2)) else null } }
    private fun hasCredential(c: Connection, org: UUID, principal: UUID): Boolean = c.prepareStatement("SELECT EXISTS (SELECT 1 FROM command_credential_revision WHERE organization_id=? AND principal_id=?)").use { s ->
        s.setObject(1, org);s.setObject(2, principal);s.executeQuery().use { r -> r.next();r.getBoolean(1) } }
    private fun latestGrant(c: Connection, org: UUID, principal: UUID, permission: CommandPermission): Leaf? = c.prepareStatement("SELECT grant_id,revision,state FROM command_permission_grant WHERE organization_id=? AND principal_id=? AND permission=? ORDER BY revision DESC LIMIT 1").use { s ->
        s.setObject(1,org);s.setObject(2,principal);s.setString(3,permission.name);s.executeQuery().use {r->if(r.next()) Leaf(r.getObject(1,UUID::class.java),r.getInt(2),r.getString(3)) else null} }
    private fun insert(c: Connection, sql: String, vararg values: Any?) = c.prepareStatement(sql).use { s -> values.forEachIndexed { i,v -> s.setObject(i+1,v) }; s.executeUpdate() }
    private fun receipt(org: io.flooow.organization.OrganizationId, operationId: UUID, operation: ControlledAuthorityOperation, parts: Parts, intent: String): ControlledAuthorityReceipt {
        val fingerprint = authorityReceipt(intent, operation.name, parts.principal.value.toString(), parts.credentialId?.toString() ?: "", parts.credentialRevision?.toString() ?: "", parts.grantId?.toString() ?: "", parts.grantRevision?.toString() ?: "", parts.permission?.name ?: "", parts.state ?: "")
        return ControlledAuthorityReceipt(org,operationId,operation,parts.principal,parts.credentialId,parts.credentialRevision,parts.grantId,parts.grantRevision,parts.permission,parts.state,intent,fingerprint)
    }
    private fun receiptFrom(r: java.sql.ResultSet): ControlledAuthorityReceipt {
        val org=io.flooow.organization.OrganizationId.parse(r.getObject("organization_id",UUID::class.java).toString())
        val principal=CommandPrincipalId(r.getObject("principal_id",UUID::class.java))
        fun uuid(name:String)=r.getObject(name) as? UUID
        fun integer(name:String)=r.getObject(name) as? Int
        return ControlledAuthorityReceipt(org,r.getObject("operation_id",UUID::class.java),ControlledAuthorityOperation.valueOf(r.getString("operation")),principal,uuid("credential_id"),integer("credential_revision"),uuid("grant_id"),integer("grant_revision"),r.getString("permission")?.let(CommandPermission::valueOf),r.getString("state"),r.getString("intent_fingerprint"),r.getString("receipt_fingerprint"))
    }
    private fun parts(principal:CommandPrincipalId, credential:UUID?, credentialRevision:Int?, grant:UUID?, grantRevision:Int?, permission:CommandPermission?, state:String?)=Parts(principal,credential,credentialRevision,grant,grantRevision,permission,state)
    private data class Parts(val principal:CommandPrincipalId,val credentialId:UUID?,val credentialRevision:Int?,val grantId:UUID?,val grantRevision:Int?,val permission:CommandPermission?,val state:String?)
    private data class Leaf(val id:UUID,val revision:Int,val state:String)
    private data class CredentialData(val operationId:UUID,val organizationId:io.flooow.organization.OrganizationId,val principalId:CommandPrincipalId,val credential:CommandCredential,val reason:String,val provenance:String,val correlationId:UUID,val intent:String)
    private class Integrity : RuntimeException()
}
