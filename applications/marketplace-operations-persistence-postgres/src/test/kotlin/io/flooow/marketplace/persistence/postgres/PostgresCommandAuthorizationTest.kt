package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.util.Base64
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.test.*
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresCommandAuthorizationTest {
    private lateinit var postgres: PostgreSQLContainer
    private val adapter = PostgresCommandAuthorization()
    private val org = UUID.randomUUID()
    private val principal = UUID.randomUUID()
    private val ml = UUID.randomUUID()
    private val omie = UUID.randomUUID()
    private val credential = UUID.randomUUID()
    private val grant = UUID.randomUUID()
    private val permission = CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE
    private fun token(byte: Byte = 1) = "fc1.$credential." +
        Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(32) { byte })
    private fun connection(): Connection = DriverManager.getConnection(postgres.jdbcUrl, postgres.username, postgres.password)
    private fun execute(sql: String, vararg args: Any?) = connection().use { c -> update(c, sql, *args) }
    private fun update(c: Connection, sql: String, vararg args: Any?): Int = c.prepareStatement(sql).use { s ->
        args.forEachIndexed { i, value -> s.setObject(i + 1, value) }
        s.executeUpdate()
    }
    private fun actor() = connection().use { assertNotNull(adapter.authenticate(it, token())) }
    private fun authorize(actor: AuthenticatedCommand, p: CommandPermission = permission): CommandAuthorizationResult =
        connection().use { c -> c.autoCommit = false; try { adapter.authorizeForWrite(c, actor, p) } finally { c.rollback() } }

    @BeforeTest
    fun start() {
        postgres = PostgreSQLContainer("postgres:18.4")
        postgres.start()
        Flyway.configure().dataSource(postgres.jdbcUrl, postgres.username, postgres.password).load().migrate()
    }
    @AfterTest
    fun stop() { if (::postgres.isInitialized) postgres.stop() }

    private fun fixture() {
        execute("INSERT INTO integration_organization VALUES (?,'ACTIVE',now(),now())", org)
        execute("INSERT INTO integration_connection VALUES (?,?,'br.com.mercadolivre','OAUTH2_AUTHORIZATION_CODE','REVOKED',1,now(),now())", org, ml)
        execute("INSERT INTO integration_connection VALUES (?,?,'omie','STATIC_API_CREDENTIAL','SUSPENDED',1,now(),now())", org, omie)
        execute("INSERT INTO command_principal VALUES (?,?,?,?,'test','synthetic',?,now())", org, principal, ml, omie, UUID.randomUUID())
        credentialRevision(1, null, 1)
    }
    private fun credentialRevision(revision: Int, previous: Int?, byte: Byte, state: String = "ENABLED") {
        val verifier = CommandCredentialVerifier.fromCredential(assertNotNull(CommandCredential.parse(token(byte))))
        execute("INSERT INTO command_credential_revision VALUES (?,?,?,?,?,?,?,'test','synthetic',?,now())",
            org, principal, credential, revision, previous, state, verifier.persistenceBytes(), UUID.randomUUID())
    }
    private fun grantSql() = "INSERT INTO command_permission_grant VALUES (?,?,?,?,?,?,?,'test','synthetic',?,now())"
    private fun enable() = execute(grantSql(), org, principal, grant, permission.name, "ENABLED", 1, null, UUID.randomUUID())
    private fun revoke(c: Connection) = update(c, grantSql(), org, principal, UUID.randomUUID(), permission.name, "DISABLED", 2, grant, UUID.randomUUID())

    @Test
    fun `migration creates no authority and valid credentials alone deny`() {
        connection().use { c -> c.createStatement().use { s ->
            s.executeQuery("SELECT (SELECT count(*) FROM command_principal)+(SELECT count(*) FROM command_credential_revision)+(SELECT count(*) FROM command_permission_grant)").use {
                it.next(); assertEquals(0, it.getInt(1))
            }
            assertNull(adapter.authenticate(c, token()))
        } }
        fixture()
        val actor = actor()
        assertEquals(CommandAuthorizationResult.Denied, authorize(actor))
        connection().use { assertNull(adapter.authenticate(it, token(2))) }
        enable()
        val allowed = assertIs<CommandAuthorizationResult.Authorized>(authorize(actor))
        assertEquals(grant, allowed.lineage.grantId)
        assertEquals(64, allowed.lineage.semanticFingerprint.length)
        assertEquals(CommandAuthorizationResult.Denied, authorize(actor, CommandPermission.TRANSACTION_IDENTITY_POLICY_ADMIN))
        val parsed = assertNotNull(CommandCredential.parse(token()))
        val verifier = CommandCredentialVerifier.fromCredential(parsed)
        // Even a forged in-process snapshot cannot override durable tenant/principal/pair binding.
        val foreign = assertNotNull(AuthenticatedCommand.verify(parsed, verifier,
            OrganizationId.parse(UUID.randomUUID().toString()), actor.principalId, ml, omie, 1))
        assertEquals(CommandAuthorizationResult.Denied, authorize(foreign))
        val wrongPair = assertNotNull(AuthenticatedCommand.verify(parsed, verifier,
            actor.organizationId, actor.principalId, omie, ml, 1))
        assertEquals(CommandAuthorizationResult.Denied, authorize(wrongPair))
        connection().use { revoke(it) }
        assertEquals(CommandAuthorizationResult.Denied, authorize(actor))
    }

    @Test
    fun `authenticate destroys parsed credential after both successful and denied paths`() {
        fixture()
        var successful: CommandCredential? = null
        val successAdapter = PostgresCommandAuthorization { value ->
            CommandCredential.parse(value)?.also { successful = it }
        }
        connection().use { assertNotNull(successAdapter.authenticate(it, token())) }
        assertFailsWith<IllegalStateException> {
            CommandCredentialVerifier.fromCredential(assertNotNull(successful))
        }

        var denied: CommandCredential? = null
        val deniedAdapter = PostgresCommandAuthorization { value ->
            CommandCredential.parse(value)?.also { denied = it }
        }
        connection().use { assertNull(deniedAdapter.authenticate(it, token(2))) }
        assertFailsWith<IllegalStateException> {
            CommandCredentialVerifier.fromCredential(assertNotNull(denied))
        }
    }

    @Test
    fun `rotation preserves actor but invalidates old admission and token`() {
        fixture(); enable()
        val old = actor()
        val lineage = assertIs<CommandAuthorizationResult.Authorized>(authorize(old)).lineage
        credentialRevision(2, 1, 2)
        connection().use { c ->
            assertNull(adapter.authenticate(c, token()))
            val rotated = assertNotNull(adapter.authenticate(c, token(2)))
            assertEquals(old.principalId, rotated.principalId)
            assertEquals(lineage, assertIs<CommandAuthorizationResult.Authorized>(authorize(rotated)).lineage)
        }
        assertEquals(CommandAuthorizationResult.Denied, authorize(old))
        credentialRevision(3, 2, 2, "DISABLED")
        connection().use { assertNull(adapter.authenticate(it, token(2))) }
    }

    @Test
    fun `authority history rejects mutation forks and foreign lineage`() {
        fixture(); enable()
        assertFailsWith<SQLException> { execute("UPDATE command_permission_grant SET state='DISABLED'") }
        assertFailsWith<SQLException> { execute("DELETE FROM command_credential_revision") }
        assertFailsWith<SQLException> { execute("DELETE FROM command_principal") }
        assertFailsWith<SQLException> { credentialRevision(2, null, 2) }
        assertFailsWith<SQLException> { execute(grantSql(), UUID.randomUUID(), principal, UUID.randomUUID(), permission.name, "ENABLED", 2, grant, UUID.randomUUID()) }
        connection().use { revoke(it) }
        assertFailsWith<SQLException> { execute(grantSql(), org, principal, UUID.randomUUID(), permission.name, "ENABLED", 2, grant, UUID.randomUUID()) }
        assertFailsWith<SQLException> { credentialRevision(3, 2, 2) }
        assertEquals(CommandAuthorizationResult.Denied, authorize(actor()))
    }

    @Test
    fun `write admission holds revocation until rollback and revoke first denies`() {
        fixture(); enable()
        val actor = actor()
        val executor = Executors.newSingleThreadExecutor()
        val started = CountDownLatch(1)
        try {
            connection().use { writer ->
                writer.autoCommit = false
                assertIs<CommandAuthorizationResult.Authorized>(adapter.authorizeForWrite(writer, actor, permission))
                val future = executor.submit<Int> {
                    connection().use { revoker -> started.countDown(); revoke(revoker) }
                }
                assertTrue(started.await(5, TimeUnit.SECONDS))
                // Wait until PostgreSQL itself proves the revoker is blocked on our authority lock.
                val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
                var blocked = false
                while (!blocked && System.nanoTime() < deadline) {
                    connection().use { observer -> observer.createStatement().use { s ->
                        s.executeQuery("SELECT EXISTS (SELECT 1 FROM pg_stat_activity WHERE wait_event_type='Lock' AND query LIKE 'INSERT INTO command_permission_grant%')").use { r -> r.next(); blocked = r.getBoolean(1) }
                    } }
                    if (!blocked) Thread.sleep(20)
                }
                assertTrue(blocked, "Revocation must wait for the admitted writer")
                assertFalse(future.isDone)
                writer.rollback()
                assertEquals(1, future.get(5, TimeUnit.SECONDS))
            }
            assertEquals(CommandAuthorizationResult.Denied, authorize(actor))
        } finally { executor.shutdownNow() }
    }

    @Test
    fun `committed admission retains exact historical lineage after revocation`() {
        fixture(); enable()
        val actor = actor()
        val lineage = connection().use { writer ->
            writer.autoCommit = false
            val admission = assertIs<CommandAuthorizationResult.Authorized>(adapter.authorizeForWrite(writer, actor, permission))
            writer.commit()
            admission.lineage
        }
        connection().use { revoke(it) }
        connection().use { c -> c.prepareStatement("SELECT revision,state FROM command_permission_grant WHERE organization_id=? AND grant_id=?").use { s ->
            s.setObject(1, org); s.setObject(2, lineage.grantId)
            s.executeQuery().use { r -> assertTrue(r.next()); assertEquals(lineage.grantRevision, r.getInt(1)); assertEquals("ENABLED", r.getString(2)) }
        } }
        assertEquals(CommandAuthorizationResult.Denied, authorize(actor))
    }

    @Test
    fun `authorization requires writer transaction and fresh isolation`() {
        fixture(); enable()
        val actor = actor()
        connection().use { c ->
            assertFailsWith<IllegalArgumentException> { adapter.authorizeForWrite(c, actor, permission) }
            c.autoCommit = false
            c.transactionIsolation = Connection.TRANSACTION_REPEATABLE_READ
            assertFailsWith<IllegalArgumentException> { adapter.authorizeForWrite(c, actor, permission) }
            c.rollback()
        }
        execute("UPDATE integration_organization SET status='SUSPENDED' WHERE organization_id=?", org)
        assertEquals(CommandAuthorizationResult.Denied, authorize(actor))
        connection().use { assertNull(adapter.authenticate(it, token())) }
    }
}
