package io.flooow.ceremony

import java.sql.Connection
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import javax.sql.DataSource

internal enum class GovernedSlot { AUDITOR, VERIFIER, ISSUER, EXECUTOR }

/** One separately authenticated pool per immutable deployment slot. */
internal class GovernedSources(private val sources: Map<GovernedSlot, DataSource>) {
    init {
        require(sources.keys == GovernedSlot.entries.toSet())
        require(sources.values.toSet().size == 4) { "SLOT_POOL_REUSE" }
    }
    fun <T> transaction(slot: GovernedSlot, block: (GovernedTransaction) -> T): T = sources.getValue(slot).connection.use { connection ->
        connection.autoCommit = false
        connection.transactionIsolation = if (slot == GovernedSlot.AUDITOR) Connection.TRANSACTION_REPEATABLE_READ else Connection.TRANSACTION_READ_COMMITTED
        connection.isReadOnly = slot == GovernedSlot.AUDITOR
        val transaction = GovernedTransaction(connection, slot)
        try {
            val result = block(transaction)
            if (slot == GovernedSlot.AUDITOR) connection.rollback() else connection.commit()
            result
        } catch (failure: Throwable) {
            try { connection.rollback() } catch (_: Throwable) { /* Never replace the original sanitized outcome. */ }
            throw failure
        } finally { transaction.close() }
    }
}

/** Cannot export a prepared decision; its JCA/apply handoff is confined to one owned transaction. */
internal class GovernedTransaction(private val connection: Connection, private val slot: GovernedSlot) {
    private var open = true
    private var decisionActive = false
    private var prepared = false
    fun close() { open = false }
    fun call(call: GovernedCall, arguments: Map<String, Any?>): ByteArray {
        require(call != GovernedCall.S04)
        check(open && call.slot == slot) { "SLOT_OR_TRANSACTION_DENIED" }
        if (call == GovernedCall.S17) check(decisionActive && !prepared) { "DECISION_SEQUENCE_DENIED" }
        if (call == GovernedCall.S18) check(decisionActive && prepared) { "DECISION_SEQUENCE_DENIED" }
        require(arguments.keys == call.fields.map { it.name }.toSet()) { "SQL_ARGUMENTS" }
        return connection.prepareStatement(call.sql).use { statement ->
            call.fields.forEachIndexed { index, field ->
                val value = requireNotNull(arguments[field.name]) { "SQL_NULL_ARGUMENT" }
                when (field.type) {
                    "uuid" -> { require(value is UUID && value != UUID(0, 0)); statement.setObject(index + 1, value) }
                    "bytea" -> {
                        require(value is ByteArray && value.size in 1..65536) { "SQL_BYTEA_SHAPE" }
                        if (field.name in setOf("plan_fingerprint", "expected_history_digest", "expected_acl_digest", "expected_policy_digest", "possession_secret", "derived_credential_proof")) require(value.size == 32) { "SQL_PROOF_SHAPE" }
                        statement.setBytes(index + 1, value)
                    }
                    "int8" -> { require(value is Long && value > 0); statement.setLong(index + 1, value) }
                    "int4" -> { require(value is Int && value > 0); statement.setInt(index + 1, value) }
                    "text" -> { require(value is String && value.isNotEmpty()); statement.setString(index + 1, value) }
                    "timestamptz" -> { require(value is Instant && value.nano % 1000 == 0); statement.setTimestamp(index + 1, Timestamp.from(value)) }
                    else -> error("SQL_TYPE")
                }
            }
            statement.executeQuery().use { rows ->
                check(rows.next()) { "SQL_CARDINALITY" }
                val result = requireNotNull(rows.getBytes(1)) { "SQL_NULL_RESULT" }.copyOf()
                check(!rows.next()) { "SQL_CARDINALITY" }
                if (call == GovernedCall.S17) prepared = true
                result
            }
        }
    }
    fun history(arguments: Map<String, Any?>): List<Map<String, Any?>> {
        check(open && slot == GovernedSlot.AUDITOR)
        val call = GovernedCall.S04
        require(arguments.keys == call.fields.map { it.name }.toSet())
        return connection.prepareStatement(call.sql).use { statement ->
            statement.setObject(1, arguments.getValue("binding_id"))
            statement.setBytes(2, arguments.getValue("plan_fingerprint") as ByteArray)
            statement.setObject(3, arguments.getValue("expected_incarnation_id"))
            statement.setString(4, arguments.getValue("surface_version") as String)
            statement.executeQuery().use { rows ->
                buildList {
                    while (rows.next()) add(linkedMapOf(
                        "installed_rank" to rows.getObject(1), "version" to rows.getString(2),
                        "type" to rows.getString(3), "script" to rows.getString(4),
                        "checksum" to rows.getObject(5), "success" to rows.getObject(6)
                    ))
                }
            }
        }
    }
    fun decision(arguments: Map<String, Any?>, verify: (ByteArray) -> Unit): ByteArray {
        check(open && slot == GovernedSlot.EXECUTOR && !decisionActive && !prepared) { "DECISION_SEQUENCE_DENIED" }
        decisionActive = true
        try {
            val envelope = call(GovernedCall.S17, arguments).copyOf()
            verify(envelope.copyOf())
            return call(GovernedCall.S18, arguments - "decision_request" + ("verified_decision_request" to envelope))
        } finally { decisionActive = false }
    }
}
