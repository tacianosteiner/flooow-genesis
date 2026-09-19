package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.connector.*
import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.integration.control.ProviderKey
import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.identity.*
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.time.Instant
import java.time.Clock
import java.time.ZoneOffset
import java.time.LocalDateTime
import java.util.Base64
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.test.*
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresTransactionIdentityWriterTest {
    private lateinit var db: PostgreSQLContainer
    private val writer = PostgresTransactionIdentityWriter()
    private val auth = PostgresCommandAuthorization()
    private val org = UUID.randomUUID()
    private val ml = UUID.randomUUID()
    private val omie = UUID.randomUUID()
    private val principal = UUID.randomUUID()
    private val credential = UUID.randomUUID()
    private val grant = UUID.randomUUID()
    private val targetA = UUID.randomUUID()
    private val targetB = UUID.randomUUID()
    private val now = Instant.parse("2026-09-18T16:00:00Z")
    private val civil = LocalDateTime.parse("2026-09-18T12:00:00")
    private val mlCap = "marketplace-economic.order-source"
    private val v3 = "marketplace-economic.omie-transaction-evidence.reacquisition-v3"
    private val fp = "a".repeat(64)
    private fun connection(): Connection = DriverManager.getConnection(db.jdbcUrl,db.username,db.password)
    private fun sql(query: String,vararg values: Any?) = connection().use { update(it,query,*values) }
    private fun update(c: Connection,query: String,vararg values: Any?): Int = c.prepareStatement(query).use { s ->
        values.forEachIndexed { i,v -> s.setObject(i+1,v) }; s.executeUpdate()
    }
    private fun token(id: UUID=credential) = "fc1.$id." + Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(32) { 1 })
    private fun actor(id: UUID=credential) = connection().use { assertNotNull(auth.authenticate(it,token(id))) }
    private fun command(target: UUID=targetA,subject: String="OMIE-1",kind: TransactionIdentityKind=TransactionIdentityKind.CONFIRMED) =
        TransactionIdentityCommand(UUID.randomUUID(),subject,target,kind,
            if(kind==TransactionIdentityKind.CONFIRMED) ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION else ExplicitTransactionIdentityReason.EXPLICIT_REJECTION,
            "synthetic independent explicit evidence",UUID.randomUUID())
    private fun record(cmd: TransactionIdentityCommand,actor: AuthenticatedCommand=actor()): TransactionIdentityWriteResult = connection().use { c ->
        c.autoCommit=false
        try { val result=writer.record(c,actor,cmd)
            if(result is TransactionIdentityWriteResult.Failed) c.rollback() else c.commit()
            result
        } catch(e: Throwable) { c.rollback(); throw e }
    }
    private fun failure(expected: TransactionIdentityFailure,result: TransactionIdentityWriteResult) =
        assertEquals(expected,assertIs<TransactionIdentityWriteResult.Failed>(result).failure)
    private fun count(table: String) = connection().use { c -> c.createStatement().use { s ->
        s.executeQuery("SELECT count(*) FROM $table").use { r -> r.next(); r.getInt(1) }
    } }
    private fun value(query: String): String = connection().use { c -> c.createStatement().use { s ->
        s.executeQuery(query).use { r -> assertTrue(r.next()); r.getString(1) }
    } }

    @BeforeTest fun start() {
        db=PostgreSQLContainer("postgres:18.4"); db.start()
        Flyway.configure().dataSource(db.jdbcUrl,db.username,db.password).load().migrate()
    }
    @AfterTest fun stop() { if(::db.isInitialized) db.stop() }

    private fun provider(id: UUID,key: String,status: String="SUSPENDED") {
        sql("INSERT INTO integration_connection VALUES (?,?,?,?,?,1,?,?)",org,id,key,
            if(key=="omie") "STATIC_API_CREDENTIAL" else "OAUTH2_AUTHORIZATION_CODE",status,java.sql.Timestamp.from(now),java.sql.Timestamp.from(now))
    }
    private fun authority(actorId: UUID=principal,credId: UUID=credential,mlId: UUID=ml,omieId: UUID=omie,grantId: UUID=if(actorId==principal) grant else UUID.randomUUID(),
        permission: String="TRANSACTION_IDENTITY_DECISION_WRITE") {
        sql("INSERT INTO command_principal VALUES (?,?,?,?,'test','synthetic',?,now())",org,actorId,mlId,omieId,UUID.randomUUID())
        val verifier=CommandCredentialVerifier.fromCredential(assertNotNull(CommandCredential.parse(token(credId))))
        sql("INSERT INTO command_credential_revision VALUES (?,?,?,1,NULL,'ENABLED',?,'test','synthetic',?,now())",
            org,actorId,credId,verifier.persistenceBytes(),UUID.randomUUID())
        sql("INSERT INTO command_permission_grant VALUES (?,?,?,?,'ENABLED',1,NULL,'test','synthetic',?,?)",
            org,actorId,grantId,permission,UUID.randomUUID(),java.sql.Timestamp.from(now))
    }
    private fun page(c: Connection,conn: UUID,cap: String,input: Long,records: Int) {
        update(c,"INSERT INTO integration_connector_progress VALUES (?,?,?, ?,?,false,?,?) ON CONFLICT(organization_id,connection_id,capability) DO UPDATE SET progress_version=EXCLUDED.progress_version",
            org,conn,cap,input+1,byteArrayOf(1),java.sql.Timestamp.from(now),java.sql.Timestamp.from(now))
        val key=ByteArray(32) { (input+1).toByte() }
        update(c,"INSERT INTO integration_connector_page_commit VALUES (?,?,?,?,?,?,false,?,?)",
            org,conn,cap,input,key,records,java.sql.Timestamp.from(now),java.sql.Timestamp.from(now))
    }
    private fun mlSource(c: Connection,conn: UUID,ordinal: Int,target: UUID,external: String,outcome: String,registry: Boolean) {
        update(c,"""INSERT INTO integration_mercado_livre_order_source_observation
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,provider_status,
            date_created,date_last_updated,currency,total_amount,observed_at) VALUES (?,?,?,0,?,?,'paid',?,?,'BRL',58.28,?)""",
            org,conn,mlCap,ordinal,external,java.sql.Timestamp.from(now),java.sql.Timestamp.from(now),java.sql.Timestamp.from(now))
        if(registry) update(c,"INSERT INTO marketplace_order_identity_registry VALUES (?,'mercado-livre',? ,?,'BRL',?,?,?,?,?)",
            org,external,target,java.sql.Timestamp.from(now),conn,mlCap,0L,ordinal)
        update(c,"INSERT INTO marketplace_order_occurrence_source_promotion VALUES (?,?,?,0,?,?,?,?)",
            org,conn,mlCap,ordinal,target,outcome,java.sql.Timestamp.from(now))
    }
    private fun source(c: Connection,conn: UUID,input: Long,subject: String,integration: String?,created: LocalDateTime?,modified: LocalDateTime?,semantic: String,currency: String?) {
        update(c,"""INSERT INTO integration_omie_transaction_evidence
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,source_order_ref,source_integration_ref,
            currency,total_amount,product_refs,observed_at,source_fingerprint) VALUES (?,?,?,?,0,?,?,?,58.28,'[]',?,?)""",
            org,conn,v3,input,subject,integration,currency,java.sql.Timestamp.from(now),"b".repeat(64))
        update(c,"""INSERT INTO integration_omie_transaction_evidence_v3
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,provider_created_local,provider_modified_local,
            additional_order_totals,semantic_fingerprint_version,source_evidence_semantic_fingerprint) VALUES (?,?,?,?,0,?,?,'{}',1,?)""",
            org,conn,v3,input,created,modified,semantic)
    }
    private fun observation(input: Long,subject: String="OMIE-1",integration: String?=null,created: LocalDateTime?=civil,
        modified: LocalDateTime?=null,semantic: String=fp,currency: String?="BRL",conn: UUID=omie) = connection().use { c ->
        c.autoCommit=false
        page(c,conn,v3,input,1); source(c,conn,input,subject,integration,created,modified,semantic,currency); c.commit()
    }
    private fun fixture() {
        sql("INSERT INTO integration_organization VALUES (?,'ACTIVE',now(),now())",org)
        provider(ml,"br.com.mercadolivre","REVOKED"); provider(omie,"omie")
        authority()
        connection().use { c -> c.autoCommit=false; page(c,ml,mlCap,0,2)
            mlSource(c,ml,0,targetA,"ML-A","PROMOTED",true); mlSource(c,ml,1,targetB,"ML-B","PROMOTED",true); c.commit() }
    }
    private fun revoke(c: Connection) = update(c,"INSERT INTO command_permission_grant VALUES (?,?,?,'TRANSACTION_IDENTITY_DECISION_WRITE','DISABLED',2,?,'revoked','synthetic',?,now())",
        org,principal,UUID.randomUUID(),grant,UUID.randomUUID())
    private fun awaitLock(queryPrefix: String) {
        val deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(8)
        var waiting=false
        while(!waiting && System.nanoTime()<deadline) {
            connection().use { c -> c.prepareStatement("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE wait_event_type='Lock' AND query LIKE ?)").use { s ->
                s.setString(1,"$queryPrefix%")
                s.executeQuery().use { r -> r.next(); waiting=r.getBoolean(1) }
            } }
            if(!waiting) Thread.sleep(20)
        }
        assertTrue(waiting,"PostgreSQL must show an actual lock waiter")
    }

    @Test fun `empty migration and permission failures create no decisions`() {
        assertEquals(0,count("command_permission_grant")); assertEquals(0,count("marketplace_transaction_identity_decision"))
        fixture(); observation(0)
        sql("INSERT INTO command_permission_grant VALUES (?,?,?,'TRANSACTION_IDENTITY_DECISION_WRITE','DISABLED',2,?,'revoke','synthetic',?,now())",
            org,principal,UUID.randomUUID(),grant,UUID.randomUUID())
        failure(TransactionIdentityFailure.AUTHORIZATION_DENIED,record(command()))
        val otherPrincipal=UUID.randomUUID(); val otherCredential=UUID.randomUUID()
        authority(otherPrincipal,otherCredential,permission="TRANSACTION_IDENTITY_POLICY_ADMIN")
        failure(TransactionIdentityFailure.AUTHORIZATION_DENIED,record(command(),actor(otherCredential)))
        assertEquals(0,count("marketplace_transaction_identity_decision"))
    }

    @Test fun `historical explicit confirmation is exact missing reference neutral and replay immutable`() {
        fixture(); observation(0,currency=null)
        val cmd=command(); val applied=assertIs<TransactionIdentityWriteResult.Applied>(record(cmd))
        assertEquals(fp,value("SELECT omie_semantic_fingerprint FROM marketplace_transaction_identity_decision"))
        assertEquals(grant.toString(),value("SELECT grant_id::text FROM marketplace_transaction_identity_decision"))
        observation(1,integration="OTHER",modified=civil.plusDays(1),semantic="c".repeat(64))
        val replay=assertIs<TransactionIdentityWriteResult.AlreadyApplied>(record(cmd.copy(correlationId=UUID.randomUUID())))
        assertEquals(applied.semanticFingerprint,replay.semanticFingerprint)
        failure(TransactionIdentityFailure.INTEGRITY_FAILURE,record(cmd.copy(provenance="changed intent")))
        failure(TransactionIdentityFailure.CONFLICT,record(command()))
        assertEquals(1,count("marketplace_transaction_identity_decision"))
    }

    @Test fun `server scope spoof and stale credential cannot authorize while rotation preserves replay actor`() {
        fixture(); observation(0)
        val aa=actor(); val cmd=command(); assertIs<TransactionIdentityWriteResult.Applied>(record(cmd,aa))
        val parsed=assertNotNull(CommandCredential.parse(token()))
        val verifier=CommandCredentialVerifier.fromCredential(parsed)
        val foreign=assertNotNull(AuthenticatedCommand.verify(parsed,verifier,OrganizationId.parse(UUID.randomUUID().toString()),
            aa.principalId,ml,omie,1))
        failure(TransactionIdentityFailure.AUTHORIZATION_DENIED,record(command(),foreign))
        val wrongOmie=assertNotNull(AuthenticatedCommand.verify(parsed,verifier,aa.organizationId,aa.principalId,ml,UUID.randomUUID(),1))
        failure(TransactionIdentityFailure.AUTHORIZATION_DENIED,record(command(),wrongOmie))
        sql("INSERT INTO command_credential_revision VALUES (?,?,?,2,1,'ENABLED',?,'rotate','synthetic',?,now())",
            org,principal,credential,verifier.persistenceBytes(),UUID.randomUUID())
        failure(TransactionIdentityFailure.AUTHORIZATION_DENIED,record(command(),aa))
        assertIs<TransactionIdentityWriteResult.AlreadyApplied>(record(cmd,actor()))
        assertEquals("1",value("SELECT credential_revision::text FROM marketplace_transaction_identity_decision"))
    }

    @Test fun `committed page completeness and semantic sidecar cannot be manufactured`() {
        fixture(); observation(0)
        sql("UPDATE integration_connector_page_commit SET record_count=2 WHERE connection_id=?",omie)
        failure(TransactionIdentityFailure.INTEGRITY_FAILURE,record(command()))
        sql("UPDATE integration_connector_page_commit SET record_count=1 WHERE connection_id=?",omie)
        connection().use { c -> c.autoCommit=false; page(c,omie,v3,1,1)
            update(c,"""INSERT INTO integration_omie_transaction_evidence
                (organization_id,connection_id,capability,input_progress_version,record_ordinal,source_order_ref,product_refs,observed_at,source_fingerprint)
                VALUES (?,?,?,1,0,'OMIE-1','[]',?,?)""",org,omie,v3,java.sql.Timestamp.from(now),"d".repeat(64)); c.commit() }
        failure(TransactionIdentityFailure.INTEGRITY_FAILURE,record(command()))
        assertEquals(0,count("marketplace_transaction_identity_decision"))
    }

    @Test fun `rejected relation alternatives survive confirmation and corrections`() {
        fixture(); observation(0)
        val rejected=command(kind=TransactionIdentityKind.REJECTED)
        assertIs<TransactionIdentityWriteResult.Applied>(record(rejected))
        val confirmed=command(targetB)
        assertIs<TransactionIdentityWriteResult.Applied>(record(confirmed))
        val release=confirmed.copy(decisionId=UUID.randomUUID(),kind=TransactionIdentityKind.REJECTED,
            reason=ExplicitTransactionIdentityReason.CORRECTION,supersedesDecisionId=confirmed.decisionId)
        assertIs<TransactionIdentityWriteResult.Applied>(record(release))
        val correctA=rejected.copy(decisionId=UUID.randomUUID(),kind=TransactionIdentityKind.CONFIRMED,
            reason=ExplicitTransactionIdentityReason.CORRECTION,supersedesDecisionId=rejected.decisionId)
        assertIs<TransactionIdentityWriteResult.Applied>(record(correctA))
        failure(TransactionIdentityFailure.CONFLICT,record(correctA.copy(decisionId=UUID.randomUUID())))
        assertEquals(4,count("marketplace_transaction_identity_decision")); assertEquals(2,count("marketplace_transaction_identity_head"))
    }

    @Test fun `current provider revision ties and bad unknown timestamps fail closed`() {
        fixture(); observation(0)
        observation(1,semantic=fp)
        assertIs<TransactionIdentityWriteResult.Applied>(record(command()))
        assertEquals("0",value("SELECT omie_progress_version::text FROM marketplace_transaction_identity_decision"))
        observation(2,semantic="c".repeat(64))
        failure(TransactionIdentityFailure.CONFLICT,record(command(targetB)))
        observation(3,created=null,modified=null)
        failure(TransactionIdentityFailure.CURRENTNESS_UNPROVEN,record(command(targetB)))
        observation(4,created=civil.plusDays(2),modified=civil)
        failure(TransactionIdentityFailure.INTEGRITY_FAILURE,record(command(targetB)))
    }

    @Test fun `latest integration currency and wrong target lineage cannot fallback`() {
        fixture(); observation(0,integration="ML-A")
        assertIs<TransactionIdentityWriteResult.Applied>(record(command()))
        observation(1,integration="ML-A",modified=civil.plusDays(1),semantic="c".repeat(64),currency="USD")
        failure(TransactionIdentityFailure.CONFLICT,record(command()))
        failure(TransactionIdentityFailure.EVIDENCE_UNAVAILABLE,record(command(UUID.randomUUID())))
        failure(TransactionIdentityFailure.EVIDENCE_UNAVAILABLE,record(command(subject="UNKNOWN")))
        assertEquals(1,count("marketplace_transaction_identity_decision"))
    }

    @Test fun `multiple ML connections preserve exact lineage one canonical target and global binding`() {
        fixture(); observation(0)
        val ml2=UUID.randomUUID(); provider(ml2,"br.com.mercadolivre")
        connection().use { c -> c.autoCommit=false; page(c,ml2,mlCap,0,1); mlSource(c,ml2,0,targetA,"ML-A","DUPLICATE",false); c.commit() }
        val credential2=UUID.randomUUID(); authority(UUID.randomUUID(),credential2,ml2)
        assertIs<TransactionIdentityWriteResult.Applied>(record(command(),actor(credential2)))
        assertEquals(ml2.toString(),value("SELECT ml_connection_id::text FROM marketplace_transaction_identity_decision"))
        observation(1,subject="OMIE-2")
        failure(TransactionIdentityFailure.CONFLICT,record(command(subject="OMIE-2")))
        assertEquals(2,count("marketplace_order_identity_registry"))
    }

    @Test fun `two actors racing same subject different targets have one winner`() {
        fixture(); observation(0)
        race(command(),actor(),command(targetB),actor())
    }
    @Test fun `different Omie connections racing one canonical target share reservation`() {
        fixture(); observation(0)
        val omie2=UUID.randomUUID(); provider(omie2,"omie"); observation(0,conn=omie2)
        val credential2=UUID.randomUUID(); authority(UUID.randomUUID(),credential2,omieId=omie2)
        race(command(),actor(),command(),actor(credential2))
    }
    private fun race(a: TransactionIdentityCommand,aa: AuthenticatedCommand,b: TransactionIdentityCommand,ba: AuthenticatedCommand) {
        val pool=Executors.newFixedThreadPool(2); val start=CountDownLatch(1)
        try {
            val futures=listOf(pool.submit<TransactionIdentityWriteResult> { start.await(); record(a,aa) },
                pool.submit<TransactionIdentityWriteResult> { start.await(); record(b,ba) })
            start.countDown(); val outcomes=futures.map { it.get(15,TimeUnit.SECONDS) }
            assertEquals(1,outcomes.count { it is TransactionIdentityWriteResult.Applied })
            assertEquals(1,outcomes.count { it==TransactionIdentityWriteResult.Failed(TransactionIdentityFailure.CONFLICT) })
            assertEquals(1,count("marketplace_transaction_identity_decision"))
        } finally { pool.shutdownNow() }
    }

    @Test fun `concurrent corrections have one child and rollback leaves no projection`() {
        fixture(); observation(0); val original=command(); assertIs<TransactionIdentityWriteResult.Applied>(record(original))
        val correction=original.copy(decisionId=UUID.randomUUID(),kind=TransactionIdentityKind.REJECTED,
            reason=ExplicitTransactionIdentityReason.CORRECTION,supersedesDecisionId=original.decisionId)
        val pool=Executors.newFixedThreadPool(2); val start=CountDownLatch(1); val aa=actor()
        try {
            val futures=(1..2).map { pool.submit<TransactionIdentityWriteResult> { start.await(); record(correction.copy(decisionId=UUID.randomUUID()),aa) } }
            start.countDown(); val outcomes=futures.map { it.get(15,TimeUnit.SECONDS) }
            assertEquals(1,outcomes.count { it is TransactionIdentityWriteResult.Applied }); assertEquals(2,count("marketplace_transaction_identity_decision"))
        } finally { pool.shutdownNow() }
        observation(1,subject="OMIE-2")
        connection().use { c -> c.autoCommit=false; assertIs<TransactionIdentityWriteResult.Applied>(writer.record(c,aa,command(subject="OMIE-2"))); c.rollback() }
        assertEquals(2,count("marketplace_transaction_identity_decision")); assertEquals(1,count("marketplace_transaction_identity_head"))
    }

    @Test fun `decision transaction serializes grant revocation and retains historical authority`() {
        fixture(); observation(0); val aa=actor(); val pool=Executors.newSingleThreadExecutor()
        try {
            connection().use { c -> c.autoCommit=false
                assertIs<TransactionIdentityWriteResult.Applied>(writer.record(c,aa,command()))
                val future=pool.submit<Int> { connection().use { revoke(it) } }
                awaitLock("INSERT INTO command_permission_grant"); assertFalse(future.isDone); c.commit()
                assertEquals(1,future.get(10,TimeUnit.SECONDS))
            }
            failure(TransactionIdentityFailure.AUTHORIZATION_DENIED,record(command()))
            assertEquals(grant.toString(),value("SELECT grant_id::text FROM marketplace_transaction_identity_decision"))
        } finally { pool.shutdownNow() }
    }

    private fun ingestion(persist: (Connection)->Unit): ConnectorPageCommitResult {
        val configuration=PostgresConfiguration(db.jdbcUrl,db.username,db.password)
        val protector=object : ConnectorProgressProtector {
            override fun seal(context: ConnectorProgressProtectionContext,plaintextBytes: ByteArray): SealedConnectorProgress = error("Unused exhausted-page protector")
            override fun open(context: ConnectorProgressProtectionContext,sealedProgress: SealedConnectorProgress): ByteArray = error("Unused exhausted-page protector")
        }
        // Obtain the opaque page key through its actual public runtime boundary.
        // The connector/access are synthetic and make no network call; persistence uses the real progress store.
        val store=PostgresConnectorProgressStore(configuration,protector)
        val cap=ConnectorCapability.of(v3)
        val committer=object : ConnectorPageCommitter {
            override val capability=cap
            override val recordType=FenceRecord::class
            override fun load(organizationId: OrganizationId,connectionId: IntegrationConnectionId,capability: ConnectorCapability) = VersionedConnectorProgress(1,null)
            override fun commit(organizationId: OrganizationId,connectionId: IntegrationConnectionId,capability: ConnectorCapability,
                expectedProgressVersion: Long,pageCommitKey: ConnectorPageCommitKey,records: List<ConnectorRecord>,
                nextProgress: ConnectorProgress?,exhausted: Boolean,observedAt: Instant) =
                store.commitPage(organizationId,connectionId,capability,expectedProgressVersion,pageCommitKey,records.size,
                    nextProgress,exhausted,observedAt,persistRecords=persist,validateExistingRecords={ error("No replay expected") })
        }
        val connector=object : PullConnector {
            override val descriptor=ConnectorDescriptor(ProviderKey.of("omie"),listOf(ConnectorRecordDefinition(cap,FenceRecord::class)))
            override fun readPage(capability: ConnectorCapability,credentialBytes: ByteArray,currentProgress: ConnectorProgress?,
                budget: ConnectorBudget,cancellation: ConnectorCancellation) =
                ConnectorReadResult.Page(ConnectorPage(listOf(FenceRecord()),null,now,true,1))
        }
        val access=object : ConnectorConnectionAccess {
            override fun activeProvider(organizationId: OrganizationId,connectionId: IntegrationConnectionId) = ProviderKey.of("omie")
            override fun <T> withActiveCredential(organizationId: OrganizationId,connectionId: IntegrationConnectionId,operation: (ByteArray)->T) = operation(byteArrayOf(0))
        }
        val runtime=ConnectorRuntime(access,listOf(connector),listOf(committer),Clock.fixed(now,ZoneOffset.UTC))
        val result=assertIs<ConnectorExecutionOutcome.Success>(runtime.execute(ConnectorInvocation(OrganizationId.parse(org.toString()),
            IntegrationConnectionId(omie),cap,ConnectorInvocationId(UUID.randomUUID()),ConnectorBudget(now.plusSeconds(30),1,100))))
        assertEquals(ConnectorSuccessKind.COMMITTED,result.kind)
        return ConnectorPageCommitResult.COMMITTED
    }
    private class FenceRecord : ConnectorRecord
    private fun enableIngestion() {
        sql("UPDATE integration_connection SET status='ACTIVE' WHERE connection_id=?",omie)
        sql("INSERT INTO integration_credential_binding VALUES (?,?,1,'synthetic-test-reference',?,NULL)",org,omie,java.sql.Timestamp.from(now))
    }
    @Test fun `writer uses real ingestion progress fence until decision commit`() {
        fixture(); observation(0); enableIngestion(); val aa=actor(); val pool=Executors.newSingleThreadExecutor()
        try {
            connection().use { c -> c.autoCommit=false; assertIs<TransactionIdentityWriteResult.Applied>(writer.record(c,aa,command()))
                val future=pool.submit<ConnectorPageCommitResult> { ingestion { source(it,omie,1,"OMIE-1","OTHER",civil,civil.plusDays(1),"c".repeat(64),"BRL") } }
                awaitLock("SELECT progress_version,exhausted FROM integration_connector_progress"); assertFalse(future.isDone); c.commit()
                assertEquals(ConnectorPageCommitResult.COMMITTED,future.get(10,TimeUnit.SECONDS))
            }
            assertEquals(fp,value("SELECT omie_semantic_fingerprint FROM marketplace_transaction_identity_decision"))
            failure(TransactionIdentityFailure.CONFLICT,record(command()))
        } finally { pool.shutdownNow() }
    }
    @Test fun `ingestion first forces writer to see newer contradiction`() {
        fixture(); observation(0); enableIngestion(); val aa=actor(); val pool=Executors.newFixedThreadPool(2)
        val inserted=CountDownLatch(1); val release=CountDownLatch(1)
        try {
            val ingest=pool.submit<ConnectorPageCommitResult> { ingestion { c ->
                source(c,omie,1,"OMIE-1","OTHER",civil,civil.plusDays(1),"c".repeat(64),"BRL")
                inserted.countDown(); assertTrue(release.await(10,TimeUnit.SECONDS))
            } }
            assertTrue(inserted.await(8,TimeUnit.SECONDS))
            val write=pool.submit<TransactionIdentityWriteResult> { record(command(),aa) }
            awaitLock("SELECT transaction_identity_locks"); release.countDown()
            assertEquals(ConnectorPageCommitResult.COMMITTED,ingest.get(10,TimeUnit.SECONDS))
            failure(TransactionIdentityFailure.CONFLICT,write.get(10,TimeUnit.SECONDS))
            assertEquals(0,count("marketplace_transaction_identity_decision"))
        } finally { release.countDown(); pool.shutdownNow() }
    }

    @Test fun `withdrawal releases contradicted confirmation without asserting replacement`() {
        fixture()
        observation(0)

        val original=command()
        assertIs<TransactionIdentityWriteResult.Applied>(
            record(original)
        )

        observation(
            1,
            integration="ML-B",
            modified=civil.plusDays(1),
            semantic="c".repeat(64)
        )

        val withdrawal=original.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="explicit governed withdrawal",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=original.decisionId
        )

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(withdrawal)
        )

        assertEquals(
            "WITHDRAWN",
            value(
                "SELECT kind FROM marketplace_transaction_identity_head " +
                    "WHERE decision_id='${withdrawal.decisionId}'"
            )
        )

        assertEquals(
            "0",
            value(
                "SELECT count(*)::text FROM marketplace_transaction_identity_head " +
                    "WHERE kind='CONFIRMED'"
            )
        )

        assertEquals(
            "0",
            value(
                "SELECT count(*)::text FROM marketplace_transaction_identity_decision " +
                    "WHERE marketplace_order_id='$targetB'"
            )
        )

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(command(targetB))
        )

        assertEquals(
            "1",
            value(
                "SELECT count(*)::text FROM marketplace_transaction_identity_head " +
                    "WHERE kind='CONFIRMED'"
            )
        )
    }

    @Test fun `withdrawal copies parent evidence and replay does not recalculate current V3`() {
        fixture()
        observation(0)

        val original=command()

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(original)
        )

        val withdrawal=original.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="explicit governed withdrawal",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=original.decisionId
        )

        val applied=assertIs<TransactionIdentityWriteResult.Applied>(
            record(withdrawal)
        )

        assertEquals(
            "1",
            value(
                """SELECT count(*)::text
                     FROM marketplace_transaction_identity_decision child
                     JOIN marketplace_transaction_identity_decision parent
                       ON parent.organization_id=child.organization_id
                      AND parent.decision_id=child.supersedes_decision_id
                    WHERE child.decision_id='${withdrawal.decisionId}'
                      AND ROW(
                          child.ml_connection_id,
                          child.ml_capability,
                          child.ml_progress_version,
                          child.ml_record_ordinal,
                          child.external_order_id,
                          child.currency,
                          child.omie_capability,
                          child.omie_progress_version,
                          child.omie_record_ordinal,
                          child.omie_semantic_fingerprint,
                          child.provider_revision_local
                      ) IS NOT DISTINCT FROM ROW(
                          parent.ml_connection_id,
                          parent.ml_capability,
                          parent.ml_progress_version,
                          parent.ml_record_ordinal,
                          parent.external_order_id,
                          parent.currency,
                          parent.omie_capability,
                          parent.omie_progress_version,
                          parent.omie_record_ordinal,
                          parent.omie_semantic_fingerprint,
                          parent.provider_revision_local
                      )"""
            )
        )

        observation(
            1,
            integration="OTHER",
            modified=civil.plusDays(1),
            semantic="c".repeat(64)
        )

        val replay=assertIs<TransactionIdentityWriteResult.AlreadyApplied>(
            record(
                withdrawal.copy(
                    correlationId=UUID.randomUUID()
                )
            )
        )

        assertEquals(
            applied.semanticFingerprint,
            replay.semanticFingerprint
        )
    }

    @Test fun `withdrawal requires the current confirmed parent`() {
        fixture()
        observation(0)

        val rejected=command(
            kind=TransactionIdentityKind.REJECTED
        )

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(rejected)
        )

        val invalidWithdrawal=rejected.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="invalid withdrawal attempt",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=rejected.decisionId
        )

        failure(
            TransactionIdentityFailure.CONFLICT,
            record(invalidWithdrawal)
        )

        val confirmed=command(targetB)

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(confirmed)
        )

        val withdrawal=confirmed.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="explicit governed withdrawal",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=confirmed.decisionId
        )

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(withdrawal)
        )

        failure(
            TransactionIdentityFailure.CONFLICT,
            record(
                withdrawal.copy(
                    decisionId=UUID.randomUUID(),
                    correlationId=UUID.randomUUID()
                )
            )
        )
    }

    @Test fun `concurrent withdrawals create one current child`() {
        fixture()
        observation(0)

        val original=command()

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(original)
        )

        val actor=actor()

        val first=original.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="first governed withdrawal",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=original.decisionId
        )

        val second=first.copy(
            decisionId=UUID.randomUUID(),
            provenance="second governed withdrawal",
            correlationId=UUID.randomUUID()
        )

        val pool=Executors.newFixedThreadPool(2)
        val start=CountDownLatch(1)

        try {
            val futures=listOf(
                pool.submit<TransactionIdentityWriteResult> {
                    start.await()
                    record(first,actor)
                },
                pool.submit<TransactionIdentityWriteResult> {
                    start.await()
                    record(second,actor)
                }
            )

            start.countDown()

            val outcomes=futures.map {
                it.get(15,TimeUnit.SECONDS)
            }

            assertEquals(
                1,
                outcomes.count {
                    it is TransactionIdentityWriteResult.Applied
                }
            )

            assertEquals(
                1,
                outcomes.count {
                    it ==
                        TransactionIdentityWriteResult.Failed(
                            TransactionIdentityFailure.CONFLICT
                        )
                }
            )

            assertEquals(
                "1",
                value(
                    "SELECT count(*)::text FROM marketplace_transaction_identity_head " +
                        "WHERE kind='WITHDRAWN'"
                )
            )

            assertEquals(
                "0",
                value(
                    "SELECT count(*)::text FROM marketplace_transaction_identity_head " +
                        "WHERE kind='CONFIRMED'"
                )
            )
        } finally {
            pool.shutdownNow()
        }
    }

    @Test fun `withdrawal ignores later V3 integrity damage but remains explicit authority`() {
        fixture()
        observation(0)

        val original=command()

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(original)
        )

        sql(
            "UPDATE integration_connector_page_commit " +
                "SET record_count=2 WHERE connection_id=?",
            omie
        )

        val withdrawal=original.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="explicit withdrawal despite later evidence damage",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=original.decisionId
        )

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(withdrawal)
        )

        assertEquals(
            "WITHDRAWN",
            value(
                "SELECT kind FROM marketplace_transaction_identity_head " +
                    "WHERE decision_id='${withdrawal.decisionId}'"
            )
        )
    }
    @Test fun `withdrawal serializes replacement confirmation on the same stable subject`() {
        fixture()
        observation(0)

        val original=command()
        assertIs<TransactionIdentityWriteResult.Applied>(
            record(original)
        )

        val secondPrincipal=UUID.randomUUID()
        val secondCredential=UUID.randomUUID()

        authority(
            actorId=secondPrincipal,
            credId=secondCredential
        )

        val secondActor=actor(secondCredential)

        val withdrawal=original.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="serialized withdrawal before replacement confirmation",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=original.decisionId
        )

        val pool=Executors.newSingleThreadExecutor()

        try {
            connection().use { c ->
                c.autoCommit=false

                assertIs<TransactionIdentityWriteResult.Applied>(
                    writer.record(
                        c,
                        actor(),
                        withdrawal
                    )
                )

                val future=pool.submit<TransactionIdentityWriteResult> {
                    record(
                        command(targetB),
                        secondActor
                    )
                }

                awaitLock(
                    "SELECT transaction_identity_locks"
                )

                assertFalse(future.isDone)

                c.commit()

                assertIs<TransactionIdentityWriteResult.Applied>(
                    future.get(
                        10,
                        TimeUnit.SECONDS
                    )
                )
            }

            assertEquals(
                "1",
                value(
                    "SELECT count(*)::text " +
                        "FROM marketplace_transaction_identity_head " +
                        "WHERE kind='CONFIRMED'"
                )
            )

            assertEquals(
                "WITHDRAWN",
                value(
                    "SELECT kind " +
                        "FROM marketplace_transaction_identity_head " +
                        "WHERE marketplace_order_id='$targetA'"
                )
            )

            assertEquals(
                "CONFIRMED",
                value(
                    "SELECT kind " +
                        "FROM marketplace_transaction_identity_head " +
                        "WHERE marketplace_order_id='$targetB'"
                )
            )
        } finally {
            pool.shutdownNow()
        }
    }

    @Test fun `withdrawal serializes target reassignment from another stable subject`() {
        fixture()

        observation(
            0,
            subject="OMIE-1"
        )

        observation(
            1,
            subject="OMIE-2"
        )

        val original=command(
            target=targetA,
            subject="OMIE-1"
        )

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(original)
        )

        val secondPrincipal=UUID.randomUUID()
        val secondCredential=UUID.randomUUID()

        authority(
            actorId=secondPrincipal,
            credId=secondCredential
        )

        val secondActor=actor(secondCredential)

        val withdrawal=original.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="serialized target release",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=original.decisionId
        )

        val replacement=command(
            target=targetA,
            subject="OMIE-2"
        )

        val pool=Executors.newSingleThreadExecutor()

        try {
            connection().use { c ->
                c.autoCommit=false

                assertIs<TransactionIdentityWriteResult.Applied>(
                    writer.record(
                        c,
                        actor(),
                        withdrawal
                    )
                )

                val future=pool.submit<TransactionIdentityWriteResult> {
                    record(
                        replacement,
                        secondActor
                    )
                }

                awaitLock(
                    "SELECT transaction_identity_locks"
                )

                assertFalse(future.isDone)

                c.commit()

                assertIs<TransactionIdentityWriteResult.Applied>(
                    future.get(
                        10,
                        TimeUnit.SECONDS
                    )
                )
            }

            assertEquals(
                "1",
                value(
                    "SELECT count(*)::text " +
                        "FROM marketplace_transaction_identity_head " +
                        "WHERE kind='CONFIRMED' " +
                        "AND marketplace_order_id='$targetA'"
                )
            )

            assertEquals(
                "OMIE-2",
                value(
                    "SELECT source_order_reference " +
                        "FROM marketplace_transaction_identity_head " +
                        "WHERE kind='CONFIRMED' " +
                        "AND marketplace_order_id='$targetA'"
                )
            )
        } finally {
            pool.shutdownNow()
        }
    }

    @Test fun `withdrawal transaction serializes grant revocation and preserves historical authority`() {
        fixture()
        observation(0)

        val original=command()

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(original)
        )

        val withdrawal=original.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="withdrawal before grant revocation",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=original.decisionId
        )

        val aa=actor()
        val pool=Executors.newSingleThreadExecutor()

        try {
            connection().use { c ->
                c.autoCommit=false

                assertIs<TransactionIdentityWriteResult.Applied>(
                    writer.record(
                        c,
                        aa,
                        withdrawal
                    )
                )

                val future=pool.submit<Int> {
                    connection().use {
                        revoke(it)
                    }
                }

                awaitLock(
                    "INSERT INTO command_permission_grant"
                )

                assertFalse(future.isDone)

                c.commit()

                assertEquals(
                    1,
                    future.get(
                        10,
                        TimeUnit.SECONDS
                    )
                )
            }

            assertEquals(
                grant.toString(),
                value(
                    "SELECT grant_id::text " +
                        "FROM marketplace_transaction_identity_decision " +
                        "WHERE decision_id='${withdrawal.decisionId}'"
                )
            )

            failure(
                TransactionIdentityFailure.AUTHORIZATION_DENIED,
                record(
                    command(
                        target=targetB
                    )
                )
            )
        } finally {
            pool.shutdownNow()
        }
    }

    @Test fun `withdrawal rollback preserves original confirmed head and permits later governed withdrawal`() {
        fixture()
        observation(0)

        val original=command()

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(original)
        )

        val withdrawal=original.copy(
            decisionId=UUID.randomUUID(),
            kind=TransactionIdentityKind.WITHDRAWN,
            reason=ExplicitTransactionIdentityReason.CORRECTION,
            provenance="rollback withdrawal",
            correlationId=UUID.randomUUID(),
            supersedesDecisionId=original.decisionId
        )

        val aa=actor()

        connection().use { c ->
            c.autoCommit=false

            assertIs<TransactionIdentityWriteResult.Applied>(
                writer.record(
                    c,
                    aa,
                    withdrawal
                )
            )

            c.rollback()
        }

        assertEquals(
            "1",
            value(
                "SELECT count(*)::text " +
                    "FROM marketplace_transaction_identity_decision"
            )
        )

        assertEquals(
            original.decisionId.toString(),
            value(
                "SELECT decision_id::text " +
                    "FROM marketplace_transaction_identity_head"
            )
        )

        assertEquals(
            "CONFIRMED",
            value(
                "SELECT kind " +
                    "FROM marketplace_transaction_identity_head"
            )
        )

        assertIs<TransactionIdentityWriteResult.Applied>(
            record(withdrawal)
        )

        assertEquals(
            "2",
            value(
                "SELECT count(*)::text " +
                    "FROM marketplace_transaction_identity_decision"
            )
        )

        assertEquals(
            "WITHDRAWN",
            value(
                "SELECT kind " +
                    "FROM marketplace_transaction_identity_head"
            )
        )
    }
    @Test fun `SQL NULL enums foreign keys fingerprints immutable history and projection attacks fail`() {
        fixture(); observation(0); val cmd=command(); assertIs<TransactionIdentityWriteResult.Applied>(record(cmd))
        val table="marketplace_transaction_identity_decision"
        listOf("UPDATE $table SET kind='REJECTED'","DELETE FROM $table",
            "UPDATE marketplace_transaction_identity_head SET kind='REJECTED'","DELETE FROM marketplace_transaction_identity_head",
            "INSERT INTO marketplace_transaction_identity_head SELECT * FROM marketplace_transaction_identity_head").forEach {
            assertFailsWith<SQLException> { sql(it) }
        }
        val modifications=listOf("'revision',NULL","'grant_revision',NULL","'supersedes_decision_id',NULL,'revision',2,'reason','CORRECTION'",
            "'reason','POLICY_EXACT_MATCH'","'kind','UNKNOWN'","'organization_id','${UUID.randomUUID()}'",
            "'ml_connection_id','$omie'","'decision_semantic_fingerprint','${"0".repeat(64)}'","'grant_id','${UUID.randomUUID()}'")
        modifications.forEach { fields ->
            assertFailsWith<SQLException> { sql("""INSERT INTO $table SELECT (jsonb_populate_record(NULL::$table,
                to_jsonb(d) || jsonb_build_object('decision_id','${UUID.randomUUID()}', $fields))).* FROM $table d WHERE decision_id=?""",cmd.decisionId) }
        }
        assertEquals(1,count(table)); assertEquals(1,count("marketplace_transaction_identity_head"))
    }
}
