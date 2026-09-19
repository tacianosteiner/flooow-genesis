package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.organization.OrganizationId
import java.io.PrintWriter
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.util.Base64
import java.util.UUID
import java.util.concurrent.Executors
import javax.sql.DataSource
import kotlin.test.*
import org.flywaydb.core.Flyway
import org.postgresql.ds.PGSimpleDataSource
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresControlledCommandAuthorityIssuerTest {
    private lateinit var db: PostgreSQLContainer
    private val org = UUID.randomUUID(); private val principal = UUID.randomUUID()
    private val ml = UUID.randomUUID(); private val omie = UUID.randomUUID()
    private val credential = UUID.randomUUID(); private val grant = UUID.randomUUID()
    private fun connection(): Connection = DriverManager.getConnection(db.jdbcUrl,db.username,db.password)
    private fun token(id: UUID=credential, byte: Byte=1) = "fc1.$id." + Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(32){byte})
    private fun credential(id: UUID=credential, byte: Byte=1) = assertNotNull(CommandCredential.parse(token(id,byte)))
    private fun orgId() = OrganizationId.parse(org.toString())
    private fun issuer() = PostgresControlledCommandAuthorityIssuer(roleDataSource("flooow_command_issuer"))
    private fun update(sql:String,vararg values:Any?) = connection().use { c -> c.prepareStatement(sql).use { s -> values.forEachIndexed{i,v->s.setObject(i+1,v)};s.executeUpdate() } }

    @BeforeTest fun start() { db=PostgreSQLContainer("postgres:18.4");db.start();Flyway.configure().dataSource(db.jdbcUrl,db.username,db.password).load().migrate() }
    @AfterTest fun stop(){if(::db.isInitialized)db.stop()}
    private fun fixture() {
        update("INSERT INTO integration_organization VALUES (?,'ACTIVE',now(),now())",org)
        update("INSERT INTO integration_connection VALUES (?,?,'br.com.mercadolivre','OAUTH2_AUTHORIZATION_CODE','REVOKED',1,now(),now())",org,ml)
        update("INSERT INTO integration_connection VALUES (?,?,'omie','STATIC_API_CREDENTIAL','SUSPENDED',1,now(),now())",org,omie)
    }
    private fun principalRequest(operation:UUID=UUID.randomUUID(), reason:String="approved") = PrincipalIssuance(operation,orgId(),CommandPrincipalId(principal),ml,omie,reason,"synthetic","${UUID.randomUUID()}".let(UUID::fromString))
    private fun bind(operation:UUID=UUID.randomUUID(), byte:Byte=1) = InitialCredentialBinding(operation,orgId(),CommandPrincipalId(principal),credential(credential,byte),"approved","synthetic",UUID.randomUUID())
    private fun grant(operation:UUID=UUID.randomUUID()) = PermissionGrant(operation,orgId(),CommandPrincipalId(principal),grant,CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE,"approved","synthetic",UUID.randomUUID())

    @Test fun `issuer provisions synthetic lineage and authorization interoperates without exposing secret`() {
        fixture(); val issuer=issuer()
        assertIs<ControlledAuthorityResult.Applied>(issuer.issuePrincipal(principalRequest()))
        val bound=assertIs<ControlledAuthorityResult.Applied>(issuer.bindInitialCredential(bind()))
        val enabled=assertIs<ControlledAuthorityResult.Applied>(issuer.grantPermission(grant()))
        assertNull(bound.receipt.toString().let { if(it.contains(token())) token() else null })
        connection().use { c ->
            val actor=assertNotNull(PostgresCommandAuthorization().authenticate(c,token()))
            c.autoCommit=false
            assertIs<CommandAuthorizationResult.Authorized>(PostgresCommandAuthorization().authorizeForWrite(c,actor,CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE));c.rollback()
        }
        assertEquals(CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE,enabled.receipt.permission)
        assertEquals(0, count("marketplace_transaction_identity_decision"))
    }

    @Test fun `operation replay rotation revocation and changed intent fail closed`() {
        fixture(); val issuer=issuer(); val principalOp=UUID.randomUUID(); val request=principalRequest(principalOp)
        assertIs<ControlledAuthorityResult.Applied>(issuer.issuePrincipal(request))
        assertIs<ControlledAuthorityResult.AlreadyApplied>(issuer.issuePrincipal(request))
        assertEquals(ControlledAuthorityResult.IntegrityFailure,issuer.issuePrincipal(request.copy(reason="different")))
        assertIs<ControlledAuthorityResult.Applied>(issuer.bindInitialCredential(bind()))
        assertIs<ControlledAuthorityResult.Applied>(issuer.grantPermission(grant()))
        val rotated=CredentialRotation(UUID.randomUUID(),orgId(),CommandPrincipalId(principal),credential(credential,2),"rotate","synthetic",UUID.randomUUID())
        assertIs<ControlledAuthorityResult.Applied>(issuer.rotateCredential(rotated))
        connection().use { c -> assertNull(PostgresCommandAuthorization().authenticate(c,token()));assertEquals(CommandPrincipalId(principal),assertNotNull(PostgresCommandAuthorization().authenticate(c,token(credential,2))).principalId) }
        val revoke=PermissionRevocation(UUID.randomUUID(),orgId(),CommandPrincipalId(principal),UUID.randomUUID(),grant,CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE,"revoke","synthetic",UUID.randomUUID())
        assertIs<ControlledAuthorityResult.Applied>(issuer.revokePermission(revoke))
        connection().use { c -> val actor=assertNotNull(PostgresCommandAuthorization().authenticate(c,token(credential,2)));c.autoCommit=false;assertEquals(CommandAuthorizationResult.Denied,PostgresCommandAuthorization().authorizeForWrite(c,actor,CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE));c.rollback() }
    }

    @Test fun `runtime and issuer roles cannot bypass their privilege boundary`() {
        fixture()
        roleDataSource("flooow_command_runtime").connection.use { c ->
            assertFailsWith<SQLException> { c.createStatement().executeUpdate("INSERT INTO command_principal VALUES ('$org','$principal','$ml','$omie','x','x','${UUID.randomUUID()}',now())") }
        }
        roleDataSource("flooow_command_issuer").connection.use { c ->
            assertFailsWith<SQLException> { c.createStatement().executeUpdate("INSERT INTO marketplace_transaction_identity_head VALUES ('$org','$omie','x','${UUID.randomUUID()}','${UUID.randomUUID()}','CONFIRMED')") }
        }
    }

    @Test fun `concurrent principal attempts serialize to one immutable root`() {
        fixture();val executor=Executors.newFixedThreadPool(2)
        try { val a=executor.submit<ControlledAuthorityResult>{issuer().issuePrincipal(principalRequest())};val b=executor.submit<ControlledAuthorityResult>{issuer().issuePrincipal(principalRequest())}
            val results=listOf(a.get(),b.get());assertEquals(1,results.count{it is ControlledAuthorityResult.Applied});assertEquals(1,results.count{it is ControlledAuthorityResult.IntegrityFailure});assertEquals(1,count("command_principal"))
        } finally {executor.shutdownNow()}
    }

    @Test fun `concurrent initial bindings serialize to one credential lineage`() {
        fixture(); val service=issuer(); assertIs<ControlledAuthorityResult.Applied>(service.issuePrincipal(principalRequest()))
        val executor=Executors.newFixedThreadPool(2)
        try { val a=executor.submit<ControlledAuthorityResult>{service.bindInitialCredential(bind(UUID.randomUUID(),1))};val b=executor.submit<ControlledAuthorityResult>{service.bindInitialCredential(InitialCredentialBinding(UUID.randomUUID(),orgId(),CommandPrincipalId(principal),credential(UUID.randomUUID(),2),"approved","synthetic",UUID.randomUUID()))}
            val results=listOf(a.get(),b.get());assertEquals(1,results.count{it is ControlledAuthorityResult.Applied});assertEquals(1,results.count{it is ControlledAuthorityResult.IntegrityFailure});assertEquals(1,count("command_credential_revision"))
        } finally {executor.shutdownNow()}
    }

    @Test fun `concurrent rotations are linearized on one credential lineage and replay is nonsecret`() {
        fixture(); val service=issuer(); val initial=bind()
        assertIs<ControlledAuthorityResult.Applied>(service.issuePrincipal(principalRequest()))
        assertIs<ControlledAuthorityResult.Applied>(service.bindInitialCredential(initial))
        val first=CredentialRotation(UUID.randomUUID(),orgId(),CommandPrincipalId(principal),credential(credential,2),"rotate-a","synthetic",UUID.randomUUID())
        val second=CredentialRotation(UUID.randomUUID(),orgId(),CommandPrincipalId(principal),credential(credential,3),"rotate-b","synthetic",UUID.randomUUID())
        val executor=Executors.newFixedThreadPool(2)
        try {
            val a=executor.submit<ControlledAuthorityResult>{issuer().rotateCredential(first)}; val b=executor.submit<ControlledAuthorityResult>{issuer().rotateCredential(second)}
            val results=listOf(a.get(),b.get())
            assertEquals(2,results.count { it is ControlledAuthorityResult.Applied })
            assertIs<ControlledAuthorityResult.AlreadyApplied>(service.rotateCredential(first))
            connection().use { c -> c.createStatement().executeQuery("SELECT revision,supersedes_revision FROM command_credential_revision WHERE credential_id='$credential' ORDER BY revision").use { r ->
                assertTrue(r.next()); assertEquals(1,r.getInt(1)); assertNull(r.getObject(2)); assertTrue(r.next()); assertEquals(2,r.getInt(1)); assertEquals(1,r.getInt(2)); assertTrue(r.next()); assertEquals(3,r.getInt(1)); assertEquals(2,r.getInt(2)); assertFalse(r.next())
            } }
            results.filterIsInstance<ControlledAuthorityResult.Applied>().forEach { assertFalse(it.receipt.toString().contains("fc1.")) }
        } finally { executor.shutdownNow() }
    }

    @Test fun `grant enable versus revoke serializes with one current disabled leaf`() {
        fixture(); val service=issuer(); assertIs<ControlledAuthorityResult.Applied>(service.issuePrincipal(principalRequest())); assertIs<ControlledAuthorityResult.Applied>(service.grantPermission(grant()))
        val revoke=PermissionRevocation(UUID.randomUUID(),orgId(),CommandPrincipalId(principal),UUID.randomUUID(),grant,CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE,"revoke","synthetic",UUID.randomUUID())
        val conflicting=PermissionGrant(UUID.randomUUID(),orgId(),CommandPrincipalId(principal),UUID.randomUUID(),CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE,"grant-again","synthetic",UUID.randomUUID())
        val executor=Executors.newFixedThreadPool(2)
        try {
            val a=executor.submit<ControlledAuthorityResult>{issuer().revokePermission(revoke)}; val b=executor.submit<ControlledAuthorityResult>{issuer().grantPermission(conflicting)}
            val results=listOf(a.get(),b.get())
            assertEquals(1,results.count { it is ControlledAuthorityResult.Applied }); assertEquals(1,results.count { it is ControlledAuthorityResult.IntegrityFailure })
            assertIs<ControlledAuthorityResult.AlreadyApplied>(service.revokePermission(revoke))
            connection().use { c -> c.createStatement().executeQuery("SELECT revision,state,supersedes_grant_id FROM command_permission_grant WHERE organization_id='$org' ORDER BY revision").use { r ->
                assertTrue(r.next());assertEquals(1,r.getInt(1));assertEquals("ENABLED",r.getString(2));assertNull(r.getObject(3));assertTrue(r.next());assertEquals(2,r.getInt(1));assertEquals("DISABLED",r.getString(2));assertEquals(grant,r.getObject(3));assertFalse(r.next())
            } }
        } finally { executor.shutdownNow() }
    }

    @Test fun `operation ledger rejects cross tenant and malformed shape without partial authority`() {
        fixture(); val service=issuer(); val issued=assertIs<ControlledAuthorityResult.Applied>(service.issuePrincipal(principalRequest()))
        val otherOrg=UUID.randomUUID(); val otherMl=UUID.randomUUID(); val otherOmie=UUID.randomUUID()
        update("INSERT INTO integration_organization VALUES (?,'ACTIVE',now(),now())",otherOrg)
        update("INSERT INTO integration_connection VALUES (?,?,'br.com.mercadolivre','OAUTH2_AUTHORIZATION_CODE','REVOKED',1,now(),now())",otherOrg,otherMl)
        update("INSERT INTO integration_connection VALUES (?,?,'omie','STATIC_API_CREDENTIAL','SUSPENDED',1,now(),now())",otherOrg,otherOmie)
        val cross=PrincipalIssuance(issued.receipt.operationId,OrganizationId.parse(otherOrg.toString()),CommandPrincipalId(principal),otherMl,otherOmie,"x","synthetic",UUID.randomUUID())
        assertEquals(ControlledAuthorityResult.IntegrityFailure,issuer().issuePrincipal(cross))
        assertEquals(1,count("command_principal")); assertEquals(0,connection().use { c -> c.createStatement().executeQuery("SELECT count(*) FROM command_authority_operation WHERE organization_id='$otherOrg'").use { r -> r.next();r.getInt(1) } })
        assertFailsWith<SQLException> { update("INSERT INTO command_authority_operation (organization_id,operation_id,operation,principal_id,credential_revision,intent_fingerprint,receipt_fingerprint,correlation_id) VALUES (?,?,?,?,?,?,?,?)",org,UUID.randomUUID(),"PRINCIPAL",principal,1,"${"a".repeat(64)}","${"b".repeat(64)}",UUID.randomUUID()) }
        assertEquals(1,count("command_authority_operation"))
    }

    @Test fun `ledger operation shapes are exclusive under direct SQL including null and hybrid attacks`() {
        fixture(); val service=issuer(); assertIs<ControlledAuthorityResult.Applied>(service.issuePrincipal(principalRequest())); assertIs<ControlledAuthorityResult.Applied>(service.bindInitialCredential(bind())); assertIs<ControlledAuthorityResult.Applied>(service.grantPermission(grant()))
        fun rejected(operation:String, credentialId:UUID?=null, credentialRevision:Int?=null, grantId:UUID?=null, grantRevision:Int?=null, permission:String?=null, state:String?=null) {
            val failure=assertFailsWith<SQLException> { update("INSERT INTO command_authority_operation (organization_id,operation_id,operation,principal_id,credential_id,credential_revision,grant_id,grant_revision,permission,state,intent_fingerprint,receipt_fingerprint,correlation_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",org,UUID.randomUUID(),operation,principal,credentialId,credentialRevision,grantId,grantRevision,permission,state,"${"a".repeat(64)}","${"b".repeat(64)}",UUID.randomUUID()) }
            assertEquals("23514",failure.sqlState)
        }
        // Valid forms were emitted through the issuer above: PRINCIPAL, INITIAL_CREDENTIAL and GRANT.
        // Every nullable cross-shape column is now explicitly rejected by the discriminated CHECK.
        rejected("PRINCIPAL", credentialRevision=1); rejected("PRINCIPAL", credentialId=credential); rejected("PRINCIPAL", grantId=grant); rejected("PRINCIPAL", grantRevision=1); rejected("PRINCIPAL", permission="TRANSACTION_IDENTITY_DECISION_WRITE"); rejected("PRINCIPAL", state="ENABLED")
        rejected("INITIAL_CREDENTIAL", credentialId=credential, credentialRevision=null, state="ENABLED"); rejected("INITIAL_CREDENTIAL", credentialId=credential, credentialRevision=1, grantId=grant, state="ENABLED"); rejected("INITIAL_CREDENTIAL", credentialId=credential, credentialRevision=1, grantRevision=1, state="ENABLED"); rejected("INITIAL_CREDENTIAL", credentialId=credential, credentialRevision=1, permission="TRANSACTION_IDENTITY_DECISION_WRITE", state="ENABLED")
        rejected("GRANT", grantId=grant, grantRevision=null, permission="TRANSACTION_IDENTITY_DECISION_WRITE", state="ENABLED"); rejected("GRANT", credentialId=credential, grantId=grant, grantRevision=1, permission="TRANSACTION_IDENTITY_DECISION_WRITE", state="ENABLED"); rejected("GRANT", credentialRevision=1, grantId=grant, grantRevision=1, permission="TRANSACTION_IDENTITY_DECISION_WRITE", state="ENABLED"); rejected("GRANT", grantId=grant, grantRevision=1, permission=null, state="ENABLED"); rejected("GRANT", grantId=grant, grantRevision=1, permission="TRANSACTION_IDENTITY_DECISION_WRITE", state="DISABLED")
        rejected("REVOKE", grantId=grant, grantRevision=1, permission="TRANSACTION_IDENTITY_DECISION_WRITE", state=null); rejected("REVOKE", grantId=grant, grantRevision=1, permission="TRANSACTION_IDENTITY_DECISION_WRITE", state="ENABLED"); rejected("REVOKE", credentialId=credential, credentialRevision=1, grantId=grant, grantRevision=1, permission="TRANSACTION_IDENTITY_DECISION_WRITE", state="DISABLED")
        rejected("PRINCIPAL", state="not-a-state"); assertEquals(3,count("command_authority_operation"))
    }

    private fun count(table:String)=connection().use{c->c.createStatement().use{s->s.executeQuery("SELECT count(*) FROM $table").use{r->r.next();r.getInt(1)}}}
    private fun roleDataSource(role:String):DataSource { val base=PGSimpleDataSource();base.setURL(db.jdbcUrl);base.user=db.username;base.password=db.password
        return object:DataSource {
            override fun getConnection():Connection=base.connection.also{it.createStatement().use{s->s.execute("SET ROLE $role")}}
            override fun getConnection(username:String,password:String)=getConnection();override fun getLogWriter():PrintWriter?=base.logWriter;override fun setLogWriter(out:PrintWriter?) {base.logWriter=out};override fun setLoginTimeout(seconds:Int){base.loginTimeout=seconds};override fun getLoginTimeout()=base.loginTimeout;override fun getParentLogger()=base.parentLogger;override fun <T:Any?> unwrap(iface:Class<T>)=base.unwrap(iface);override fun isWrapperFor(iface:Class<*>)=base.isWrapperFor(iface)
        }
    }
}
