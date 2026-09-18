package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.identity.*
import java.sql.Connection
import java.sql.ResultSet
import java.sql.SQLException
import java.time.LocalDateTime

private const val ML_SOURCE = "marketplace-economic.order-source"
private const val OMIE_V3 = "marketplace-economic.omie-transaction-evidence.reacquisition-v3"

/** Single caller-owned transaction. No provider client, routing or provisioning. */
class PostgresTransactionIdentityWriter {
    private val authorization = PostgresCommandAuthorization()

    fun record(c: Connection, actor: AuthenticatedCommand, command: TransactionIdentityCommand): TransactionIdentityWriteResult {
        val permission = CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE
        val first = authorization.authorizeForWrite(c, actor, permission)
        if (first is CommandAuthorizationResult.Denied) return failed(TransactionIdentityFailure.AUTHORIZATION_DENIED)
        if (first !is CommandAuthorizationResult.Authorized) return failed(TransactionIdentityFailure.INTEGRITY_FAILURE)
        val intent = command.intentFingerprint(actor)
        try {
            c.prepareStatement("SELECT pg_advisory_xact_lock(hashtextextended(?,0))").use { s ->
                s.setString(1, "transaction-identity/id/1:${actor.organizationId.value}:${command.decisionId}")
                s.executeQuery().close()
            }
            c.prepareStatement("SELECT intent_fingerprint,decision_semantic_fingerprint FROM marketplace_transaction_identity_decision WHERE organization_id=? AND decision_id=?").use { s ->
                s.setObject(1, actor.organizationId.value); s.setObject(2, command.decisionId)
                s.executeQuery().use { r ->
                    if (r.next()) return if (r.getString(1) == intent) {
                        TransactionIdentityWriteResult.AlreadyApplied(command.decisionId, r.getString(2))
                    } else failed(TransactionIdentityFailure.INTEGRITY_FAILURE)
                }
            }
            c.prepareStatement("SELECT transaction_identity_locks(?,?,?,?,?,?)").use { s ->
                val values = listOf(actor.organizationId.value, actor.principalId.value, command.decisionId,
                    actor.omieConnectionId, command.sourceOrderReference, command.marketplaceOrderId)
                values.forEachIndexed { i, v -> s.setObject(i + 1, v) }; s.executeQuery().close()
            }
            val target = target(c, actor, command) ?: return failed(TransactionIdentityFailure.EVIDENCE_UNAVAILABLE)
            val rows = omie(c, actor, command)
            if (rows.isEmpty()) return failed(TransactionIdentityFailure.EVIDENCE_UNAVAILABLE)
            if (rows.any { !it.valid || (it.created != null && it.modified != null && it.modified < it.created) }) {
                return failed(TransactionIdentityFailure.INTEGRITY_FAILURE)
            }
            if (rows.any { it.created == null && it.modified == null }) return failed(TransactionIdentityFailure.CURRENTNESS_UNPROVEN)
            val max = rows.maxOf { it.modified ?: requireNotNull(it.created) }
            val current = rows.filter { (it.modified ?: it.created) == max }
            if (current.map { it.semantic }.distinct().size != 1) return failed(TransactionIdentityFailure.CONFLICT)
            if (current.any { (it.integration != null && it.integration != target.external) ||
                (it.currency != null && it.currency != target.currency) }) return failed(TransactionIdentityFailure.CONFLICT)
            val omie = current.minWith(compareBy<Omie> { it.progress }.thenBy { it.ordinal })
            if ((omie.integration != null && omie.integration != target.external) ||
                (omie.currency != null && omie.currency != target.currency)) return failed(TransactionIdentityFailure.CONFLICT)
            val revision = c.prepareStatement("""SELECT d.revision,h.decision_id FROM marketplace_transaction_identity_head h
                JOIN marketplace_transaction_identity_decision d USING(organization_id,decision_id)
                WHERE h.organization_id=? AND h.omie_connection_id=? AND h.source_order_reference=? AND h.marketplace_order_id=?""").use { s ->
                s.setObject(1, actor.organizationId.value); s.setObject(2, actor.omieConnectionId)
                s.setString(3, command.sourceOrderReference); s.setObject(4, command.marketplaceOrderId)
                s.executeQuery().use { r ->
                    if (command.supersedesDecisionId == null) {
                        if (r.next()) return failed(TransactionIdentityFailure.CONFLICT)
                        1
                    } else {
                        if (!r.next() || r.getObject("decision_id") != command.supersedesDecisionId) return failed(TransactionIdentityFailure.CONFLICT)
                        Math.addExact(r.getInt("revision"), 1)
                    }
                }
            }
            val evidence = TransactionIdentityEvidence(ML_SOURCE, target.progress, target.ordinal, target.external,
                target.currency, OMIE_V3, omie.progress, omie.ordinal, omie.semantic, max)
            // This re-check belongs to the exact transaction immediately before immutable insert.
            val final = authorization.authorizeForWrite(c, actor, permission)
            if (final is CommandAuthorizationResult.Denied) return failed(TransactionIdentityFailure.AUTHORIZATION_DENIED)
            if (final !is CommandAuthorizationResult.Authorized) return failed(TransactionIdentityFailure.INTEGRITY_FAILURE)
            val lineage = final.lineage
            val semantic = evidence.decisionFingerprint(intent, actor, lineage)
            val columns = """organization_id,decision_id,omie_connection_id,source_order_reference,marketplace_order_id,
                kind,reason,revision,supersedes_decision_id,ml_connection_id,ml_capability,ml_progress_version,ml_record_ordinal,
                external_order_id,currency,omie_capability,omie_progress_version,omie_record_ordinal,omie_semantic_fingerprint,
                provider_revision_local,principal_id,credential_id,credential_revision,grant_id,grant_revision,permission,
                authorization_semantic_version,authorization_fingerprint,intent_fingerprint,decision_semantic_fingerprint,
                provenance,correlation_id"""
            val values = listOf(actor.organizationId.value, command.decisionId, actor.omieConnectionId, command.sourceOrderReference,
                command.marketplaceOrderId, command.kind.name, command.reason.name, revision, command.supersedesDecisionId,
                actor.mercadoLivreConnectionId, ML_SOURCE, target.progress, target.ordinal, target.external, target.currency,
                OMIE_V3, omie.progress, omie.ordinal, omie.semantic, max, actor.principalId.value, actor.credentialId,
                actor.credentialRevision, lineage.grantId, lineage.grantRevision, lineage.permission.name, lineage.semanticVersion,
                lineage.semanticFingerprint, intent, semantic, command.provenance, command.correlationId)
            c.prepareStatement("INSERT INTO marketplace_transaction_identity_decision ($columns) VALUES (${values.joinToString(",") { "?" }})").use { s ->
                values.forEachIndexed { i, v -> s.setObject(i + 1, v) }; s.executeUpdate()
            }
            return TransactionIdentityWriteResult.Applied(command.decisionId, semantic)
        } catch (e: SQLException) {
            return when (e.sqlState) {
                "P0002" -> failed(TransactionIdentityFailure.EVIDENCE_UNAVAILABLE)
                "P0010" -> failed(TransactionIdentityFailure.CURRENTNESS_UNPROVEN)
                "P0011", "23505" -> failed(TransactionIdentityFailure.CONFLICT)
                "P0012" -> failed(TransactionIdentityFailure.AUTHORIZATION_DENIED)
                "23514", "23503", "23502" -> failed(TransactionIdentityFailure.INTEGRITY_FAILURE)
                else -> throw e // Infrastructure/deadlock/serialization is not an ordinary identity result.
            }
        }
    }

    private fun target(c: Connection, actor: AuthenticatedCommand, command: TransactionIdentityCommand): Target? =
        c.prepareStatement("""SELECT i.external_order_id,i.currency,p.source_input_progress_version,p.source_record_ordinal
            FROM marketplace_order_identity_registry i JOIN marketplace_order_occurrence_source_promotion p
            ON p.organization_id=i.organization_id AND p.marketplace_order_id=i.marketplace_order_id
            JOIN integration_mercado_livre_order_source_observation s ON s.organization_id=p.organization_id
                AND s.connection_id=p.source_connection_id AND s.capability=p.source_capability
                AND s.input_progress_version=p.source_input_progress_version AND s.record_ordinal=p.source_record_ordinal
            WHERE i.organization_id=? AND i.marketplace_order_id=? AND i.marketplace_key='mercado-livre'
                AND p.source_connection_id=? AND p.source_capability='marketplace-economic.order-source'
                AND p.outcome IN ('PROMOTED','DUPLICATE') AND s.external_order_ref=i.external_order_id AND s.currency=i.currency
            ORDER BY p.source_input_progress_version,p.source_record_ordinal LIMIT 1""").use { s ->
            s.setObject(1, actor.organizationId.value); s.setObject(2, command.marketplaceOrderId); s.setObject(3, actor.mercadoLivreConnectionId)
            s.executeQuery().use { r -> if (r.next()) Target(r.getString(1),r.getString(2),r.getLong(3),r.getInt(4)) else null }
        }

    private fun omie(c: Connection, actor: AuthenticatedCommand, command: TransactionIdentityCommand): List<Omie> =
        c.prepareStatement("""SELECT b.input_progress_version,b.record_ordinal,b.source_integration_ref,b.currency,
            v.provider_created_local,v.provider_modified_local,v.source_evidence_semantic_fingerprint,v.semantic_fingerprint_version,p.record_count,
            (p.record_count=(SELECT count(*) FROM integration_omie_transaction_evidence x WHERE x.organization_id=b.organization_id
                AND x.connection_id=b.connection_id AND x.capability=b.capability AND x.input_progress_version=b.input_progress_version)
             AND p.record_count=(SELECT count(*) FROM integration_omie_transaction_evidence_v3 x WHERE x.organization_id=b.organization_id
                AND x.connection_id=b.connection_id AND x.capability=b.capability AND x.input_progress_version=b.input_progress_version)
             AND b.input_progress_version<pr.progress_version) AS page_complete
            FROM integration_omie_transaction_evidence b LEFT JOIN integration_omie_transaction_evidence_v3 v
            USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
            LEFT JOIN integration_connector_page_commit p USING(organization_id,connection_id,capability,input_progress_version)
            JOIN integration_connector_progress pr ON pr.organization_id=b.organization_id AND pr.connection_id=b.connection_id AND pr.capability=b.capability
            WHERE b.organization_id=? AND b.connection_id=? AND b.capability=? AND b.source_order_ref=?""").use { s ->
            s.setObject(1, actor.organizationId.value); s.setObject(2, actor.omieConnectionId)
            s.setString(3, OMIE_V3); s.setString(4, command.sourceOrderReference)
            s.executeQuery().use { r -> buildList { while(r.next()) {
                val semantic = r.getString("source_evidence_semantic_fingerprint") ?: ""
                add(Omie(r.getLong("input_progress_version"),r.getInt("record_ordinal"),r.getString("source_integration_ref"),
                    r.getString("currency"),r.civil("provider_created_local"),r.civil("provider_modified_local"),semantic,
                    r.getBoolean("page_complete") && r.getObject("record_count") != null && r.getInt("record_ordinal") < r.getInt("record_count") &&
                        r.getInt("semantic_fingerprint_version") == 1 && semantic.matches(Regex("[0-9a-f]{64}"))))
            } } }
        }

    private data class Target(val external: String,val currency: String,val progress: Long,val ordinal: Int)
    private data class Omie(val progress: Long,val ordinal: Int,val integration: String?,val currency: String?,
        val created: LocalDateTime?,val modified: LocalDateTime?,val semantic: String,val valid: Boolean)
    private fun ResultSet.civil(column: String): LocalDateTime? = getObject(column,LocalDateTime::class.java)
    private fun failed(f: TransactionIdentityFailure) = TransactionIdentityWriteResult.Failed(f)
}
