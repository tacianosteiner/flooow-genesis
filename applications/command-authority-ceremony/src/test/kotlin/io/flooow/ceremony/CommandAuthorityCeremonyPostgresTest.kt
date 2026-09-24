package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.CommandPermission
import io.flooow.marketplace.operations.authorization.CommandPrincipalId
import io.flooow.marketplace.operations.authorization.ControlledAuthorityResult
import io.flooow.marketplace.operations.authorization.PermissionRevocation
import io.flooow.marketplace.operations.identity.ExplicitTransactionIdentityReason
import io.flooow.marketplace.operations.identity.TransactionIdentityCommand
import io.flooow.marketplace.operations.identity.TransactionIdentityKind
import io.flooow.marketplace.operations.identity.TransactionIdentityWriteResult
import io.flooow.organization.OrganizationId
import java.io.ByteArrayOutputStream
import java.io.PrintWriter
import java.io.PrintStream
import java.sql.Connection
import java.sql.DriverManager
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.Base64
import java.util.UUID
import javax.sql.DataSource
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.postgresql.ds.PGSimpleDataSource
import org.testcontainers.postgresql.PostgreSQLContainer

class CommandAuthorityCeremonyPostgresTest {
    private lateinit var db: PostgreSQLContainer
    private val organization = UUID.randomUUID()
    private val ml = UUID.randomUUID()
    private val omie = UUID.randomUUID()
    private val order = UUID.randomUUID()
    private val now = Instant.parse("2026-09-24T12:00:00Z")

    @BeforeTest fun start() {
        db = PostgreSQLContainer("postgres:18.4").also { it.start() }
        Flyway.configure().dataSource(db.jdbcUrl, db.username, db.password).load().migrate()
        seedFixture()
    }
    @AfterTest fun stop() { if (::db.isInitialized) db.stop() }

    @Test fun `real postgres ceremony creates the governed proof once and destroys its credential`() {
        val tty = RecordingTty(); val lifecycle = Lifecycle(); val composition = composition()
        assertEquals("flooow_command_issuer", currentUser(issuerDataSource()))
        assertEquals("flooow_command_runtime", currentUser(runtimeDataSource()))
        val before = snapshot()
        val stdout = ByteArrayOutputStream(); val stderr = ByteArrayOutputStream()
        val originalOut = System.out; val originalErr = System.err
        val result: CeremonyResult
        try {
            System.setOut(PrintStream(stdout)); System.setErr(PrintStream(stderr))
            result = ceremony(composition, tty, lifecycle).execute(approval(), target(), command())
        } finally {
            System.setOut(originalOut); System.setErr(originalErr)
        }
        val applied = assertIs<CeremonyResult.Applied>(result)
        assertEquals(Delta(1,1,1,3,1,1), snapshot() - before)
        assertEquals(1, tty.calls); assertEquals(1, lifecycle.created); assertEquals(1, lifecycle.destroyed); assertTrue(lifecycle.verifierCreationRejected)
        assertEquals(organization, valueUuid("SELECT organization_id FROM marketplace_transaction_identity_decision"))
        assertEquals("CONFIRMED", value("SELECT kind FROM marketplace_transaction_identity_decision"))
        assertEquals(omie, valueUuid("SELECT omie_connection_id FROM marketplace_transaction_identity_decision"))
        assertEquals(ml, valueUuid("SELECT ml_connection_id FROM marketplace_transaction_identity_decision"))
        assertEquals("OMIE-1", value("SELECT source_order_reference FROM marketplace_transaction_identity_decision"))
        assertEquals(order, valueUuid("SELECT marketplace_order_id FROM marketplace_transaction_identity_decision"))
        assertEquals(applied.decisionId, valueUuid("SELECT decision_id FROM marketplace_transaction_identity_head"))
        assertEquals(organization, valueUuid("SELECT organization_id FROM marketplace_transaction_identity_head"))
        assertEquals(omie, valueUuid("SELECT omie_connection_id FROM marketplace_transaction_identity_head"))
        assertEquals("OMIE-1", value("SELECT source_order_reference FROM marketplace_transaction_identity_head"))
        assertEquals(order, valueUuid("SELECT marketplace_order_id FROM marketplace_transaction_identity_head"))
        assertEquals(1, count("marketplace_transaction_identity_decision")); assertEquals(1, count("marketplace_transaction_identity_head"))
        val secret = tty.token
        assertTrue(secret.isNotBlank())
        assertEquals(1, occurrences(tty.rendered, secret)); assertEquals(0, occurrences(result.toString(), secret))
        assertEquals(0, occurrences(stdout.toString(Charsets.UTF_8), secret)); assertEquals(0, occurrences(stderr.toString(Charsets.UTF_8), secret))
        assertEquals(0, rawSecretDatabaseOccurrences(secret))
    }

    @Test fun `expired approval has no durable authority or identity mutation`() {
        val tty = RecordingTty(); val lifecycle = Lifecycle()
        val before = snapshot()
        val result = ceremony(composition(), tty, lifecycle).execute(approval().copy(windowEnd = now.minusSeconds(1)), target(), command())
        assertEquals(CeremonyResult.Denied, result); assertEquals(Delta.ZERO, snapshot() - before)
        assertEquals(0, tty.calls); assertEquals(0, lifecycle.created); assertEquals(0, lifecycle.destroyed)
    }

    @Test fun `target binding mismatch missing reference and cross organization deny before provisioning`() {
        val variants = listOf(
            target().copy(integrationReference = "WRONG"),
            target().copy(integrationReference = ""),
            target().copy(organizationId = OrganizationId.parse(UUID.randomUUID().toString()))
        )
        val before = snapshot()
        variants.forEach { candidate ->
            val tty = RecordingTty(); val lifecycle = Lifecycle()
            assertEquals(CeremonyResult.Denied, ceremony(composition(), tty, lifecycle).execute(approval(), candidate, command()))
            assertEquals(Delta.ZERO, snapshot() - before)
            assertEquals(0, tty.calls); assertEquals(0, lifecycle.created); assertEquals(0, lifecycle.destroyed)
        }
    }

    @Test fun `writer failure preserves authority history but no decision head and destroys credential`() {
        val tty = RecordingTty(); val lifecycle = Lifecycle()
        val composition = PostgresCeremonyComposition(issuerDataSource(), runtimeDataSource()) { _, _, _ ->
            assertEquals(1, lifecycle.destroyed)
            assertTrue(lifecycle.verifierCreationRejected)
            throw ControlledWriterFailure()
        }
        val before = snapshot()
        val failure = runCatching { ceremony(composition, tty, lifecycle).execute(approval(), target(), command()) }.exceptionOrNull()
        assertIs<ControlledWriterFailure>(failure)
        assertEquals(Delta(1,1,1,3,0,0), snapshot() - before)
        assertEquals(1, lifecycle.created); assertEquals(1, lifecycle.destroyed); assertEquals(1, tty.calls)
        assertEquals("controlled writer failure without secret", failure.message)
        assertEquals(0, occurrences(failure.toString(), tty.token)); assertEquals(1, count("command_principal"))
    }

    @Test fun `separately approved revocation appends disabled grant history and receipt`() {
        val tty = RecordingTty(); val lifecycle = Lifecycle(); val composition = composition()
        val before = snapshot()
        val applied = assertIs<CeremonyResult.Applied>(ceremony(composition, tty, lifecycle).execute(approval(), target(), command()))
        val enabledGrant = valueUuid("SELECT grant_id FROM command_permission_grant WHERE state='ENABLED'")
        val revocation = composition.issuer.revokePermission(PermissionRevocation(
            UUID.randomUUID(), OrganizationId.parse(organization.toString()), CommandPrincipalId(applied.principalId),
            UUID.randomUUID(), enabledGrant, CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE,
            "separately approved synthetic revocation", "test", targetCorrelation
        ))
        assertIs<ControlledAuthorityResult.Applied>(revocation)
        assertEquals(Delta(1,1,2,4,1,1), snapshot() - before)
        assertEquals("DISABLED", value("SELECT state FROM command_permission_grant ORDER BY revision DESC LIMIT 1"))
        assertEquals("REVOKE", value("SELECT operation FROM command_authority_operation ORDER BY decided_at DESC LIMIT 1"))
    }

    private fun ceremony(composition: PostgresCeremonyComposition, tty: RecordingTty, lifecycle: Lifecycle) =
        ExecuteFieldProof(composition.issuer, composition.runtime, tty, Clock.fixed(now, ZoneOffset.UTC), java.security.SecureRandom(), lifecycle)
    private fun approval() = HumanApproval("operator", "synthetic-approved", now.minusSeconds(60), now.plusSeconds(60), "owner", "custodian", "TTY", "rotation", "NONE")
    private fun command() = TransactionIdentityCommand(UUID.randomUUID(), "OMIE-1", order, TransactionIdentityKind.CONFIRMED, ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION, "approved synthetic proof", UUID.randomUUID()).let { it.copy(correlationId = targetCorrelation) }
    private var targetCorrelation: UUID = UUID.randomUUID()

    // ExecuteFieldProof requires the target and command correlation pair to be exact.
    private fun target(): FieldProofTarget = FieldProofTarget(OrganizationId.parse(organization.toString()), ml, omie, "OMIE-1", "ML-1", order, "approved synthetic proof", "test", targetCorrelation)

    private fun composition() = PostgresCeremonyComposition(issuerDataSource(), runtimeDataSource())
    private fun issuerDataSource() = roleDataSource("flooow_command_issuer")
    private fun runtimeDataSource() = roleDataSource("flooow_command_runtime")
    private fun roleDataSource(role: String): DataSource {
        val base = PGSimpleDataSource().also { it.setURL(db.jdbcUrl); it.user = db.username; it.password = db.password }
        return object : DataSource {
            override fun getConnection(): Connection = base.connection.also { connection -> connection.createStatement().use { it.execute("SET ROLE $role") } }
            override fun getConnection(username: String?, password: String?) = getConnection()
            override fun getLogWriter(): PrintWriter? = base.logWriter
            override fun setLogWriter(out: PrintWriter?) { base.logWriter = out }
            override fun setLoginTimeout(seconds: Int) { base.loginTimeout = seconds }
            override fun getLoginTimeout() = base.loginTimeout
            override fun getParentLogger() = base.parentLogger
            override fun <T : Any?> unwrap(iface: Class<T>) = base.unwrap(iface)
            override fun isWrapperFor(iface: Class<*>) = base.isWrapperFor(iface)
        }
    }

    private fun seedFixture() {
        sql("INSERT INTO integration_organization VALUES (?,'ACTIVE',now(),now())", organization)
        sql("INSERT INTO integration_connection VALUES (?,?,'br.com.mercadolivre','OAUTH2_AUTHORIZATION_CODE','REVOKED',1,now(),now())", organization, ml)
        sql("INSERT INTO integration_connection VALUES (?,?,'omie','STATIC_API_CREDENTIAL','SUSPENDED',1,now(),now())", organization, omie)
        connection().use { c -> c.autoCommit = false
            update(c, "INSERT INTO integration_connector_progress VALUES (?,?,?,1,?,false,now(),now())", organization, ml, "marketplace-economic.order-source", byteArrayOf(1))
            update(c, "INSERT INTO integration_connector_page_commit VALUES (?,?,?,?,?,?,false,now(),now())", organization, ml, "marketplace-economic.order-source", 0, ByteArray(32) { 1 }, 1)
            update(c, "INSERT INTO integration_mercado_livre_order_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,provider_status,date_created,date_last_updated,currency,total_amount,observed_at) VALUES (?,?,?,0,0,'ML-1','paid',now(),now(),'BRL',58.28,now())", organization, ml, "marketplace-economic.order-source")
            update(c, "INSERT INTO marketplace_order_identity_registry VALUES (?,'mercado-livre','ML-1',?,'BRL',now(),?,'marketplace-economic.order-source',0,0)", organization, order, ml)
            update(c, "INSERT INTO marketplace_order_occurrence_source_promotion VALUES (?,?,?,0,0,?,'PROMOTED',now())", organization, ml, "marketplace-economic.order-source", order)
            update(c, "INSERT INTO integration_connector_progress VALUES (?,?,?,1,?,false,now(),now())", organization, omie, "marketplace-economic.omie-transaction-evidence.reacquisition-v3", byteArrayOf(1))
            update(c, "INSERT INTO integration_connector_page_commit VALUES (?,?,?,?,?,?,false,now(),now())", organization, omie, "marketplace-economic.omie-transaction-evidence.reacquisition-v3", 0, ByteArray(32) { 2 }, 1)
            update(c, "INSERT INTO integration_omie_transaction_evidence (organization_id,connection_id,capability,input_progress_version,record_ordinal,source_order_ref,source_integration_ref,currency,total_amount,product_refs,observed_at,source_fingerprint) VALUES (?,?,?,0,0,'OMIE-1','ML-1','BRL',58.28,'[]',now(),?)", organization, omie, "marketplace-economic.omie-transaction-evidence.reacquisition-v3", "a".repeat(64))
            update(c, "INSERT INTO integration_omie_transaction_evidence_v3 (organization_id,connection_id,capability,input_progress_version,record_ordinal,provider_created_local,provider_modified_local,additional_order_totals,semantic_fingerprint_version,source_evidence_semantic_fingerprint) VALUES (?,?,?,0,0,'2026-09-24 09:00:00',NULL,'{}',1,?)", organization, omie, "marketplace-economic.omie-transaction-evidence.reacquisition-v3", "b".repeat(64))
            c.commit()
        }
    }
    private fun connection() = DriverManager.getConnection(db.jdbcUrl, db.username, db.password)
    private fun sql(query: String, vararg values: Any?) = connection().use { update(it, query, *values) }
    private fun update(c: Connection, query: String, vararg values: Any?) = c.prepareStatement(query).use { statement -> values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }; statement.executeUpdate() }
    private fun currentUser(ds: DataSource) = ds.connection.use { value(it, "SELECT current_user") }
    private fun value(query: String) = connection().use { value(it, query) }
    private fun value(c: Connection, query: String) = c.createStatement().use { statement -> statement.executeQuery(query).use { result -> result.next(); result.getString(1) } }
    private fun valueUuid(query: String) = connection().use { c -> c.createStatement().use { s -> s.executeQuery(query).use { r -> r.next(); r.getObject(1, UUID::class.java) } } }
    private fun count(table: String) = value("SELECT count(*) FROM $table").toInt()
    private fun snapshot() = Delta(count("command_principal"), count("command_credential_revision"), count("command_permission_grant"), count("command_authority_operation"), count("marketplace_transaction_identity_decision"), count("marketplace_transaction_identity_head"))
    private fun occurrences(text: String, token: String) = Regex(Regex.escape(token)).findAll(text).count()
    private fun rawSecretDatabaseOccurrences(token: String): Int {
        val encodedSecret = token.substringAfterLast('.')
        val rawSecretHex = Base64.getUrlDecoder().decode(encodedSecret).joinToString("") { "%02x".format(it) }
        val tables = listOf(
            "command_principal", "command_credential_revision", "command_permission_grant",
            "command_authority_operation", "marketplace_transaction_identity_decision",
            "marketplace_transaction_identity_head"
        )
        return connection().use { connection ->
            tables.sumOf { table ->
                connection.prepareStatement(
                    "SELECT count(*) FROM $table row_value WHERE row_to_json(row_value)::text LIKE ? OR row_to_json(row_value)::text LIKE ? OR row_to_json(row_value)::text LIKE ?"
                ).use { statement ->
                    statement.setString(1, "%$token%")
                    statement.setString(2, "%$encodedSecret%")
                    statement.setString(3, "%$rawSecretHex%")
                    statement.executeQuery().use { rows -> rows.next(); rows.getInt(1) }
                }
            }
        }
    }
    private data class Delta(val principal:Int,val credential:Int,val grant:Int,val authority:Int,val decision:Int,val head:Int) { operator fun minus(before:Delta)=Delta(principal-before.principal,credential-before.credential,grant-before.grant,authority-before.authority,decision-before.decision,head-before.head); companion object { val ZERO=Delta(0,0,0,0,0,0) } }
    private class RecordingTty : ProtectedTty { var calls=0; var token=""; val rendered get()=token; override fun isProtected()=true; override fun deliverOnce(token:CharArray) { calls++; this.token=String(token); token.fill('\u0000') } }
    private class Lifecycle : CredentialLifecycleObserver { var created=0; var destroyed=0; var verifierCreationRejected=false; override fun created(){created++}; override fun destroyed(verifierCreationRejected:Boolean){destroyed++;this.verifierCreationRejected=verifierCreationRejected} }
    private class ControlledWriterFailure : RuntimeException("controlled writer failure without secret")
}
