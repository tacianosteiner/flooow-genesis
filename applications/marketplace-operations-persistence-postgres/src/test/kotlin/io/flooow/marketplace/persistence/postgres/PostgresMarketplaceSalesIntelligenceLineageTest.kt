package io.flooow.marketplace.persistence.postgres

import com.github.dockerjava.api.model.ExposedPort
import com.github.dockerjava.api.model.PortBinding
import com.github.dockerjava.api.model.Ports
import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.sales.*
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.sql.SQLException
import java.sql.Timestamp
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.AtomicInteger
import java.lang.reflect.Proxy
import java.lang.reflect.InvocationTargetException
import java.nio.file.Files
import java.nio.file.Path
import java.sql.Connection
import java.sql.DriverManager
import kotlin.test.*
import org.flywaydb.core.Flyway
import org.junit.jupiter.api.AfterAll
import org.junit.jupiter.api.BeforeAll
import org.junit.jupiter.api.TestInstance
import org.testcontainers.postgresql.PostgreSQLContainer

@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class PostgresMarketplaceSalesIntelligenceLineageTest {
    private lateinit var postgres: PostgreSQLContainer
    private lateinit var configuration: PostgresConfiguration
    private lateinit var legacy: ConsumedEconomicEvidenceSnapshot
    private lateinit var invalidLegacy: ConsumedEconomicEvidenceSnapshot
    private val candidate: String get() = checkNotNull(javaClass.getResource("/room-lineage/historical_lineage_candidate.sql")).readText()

    @BeforeAll fun start() {
        postgres = PostgreSQLContainer("postgres:18.4").withCreateContainerCmdModifier { command ->
            checkNotNull(command.hostConfig).withPortBindings(PortBinding(Ports.Binding.bindIp("127.0.0.1"), ExposedPort.tcp(5432)))
        }
        postgres.start()
        val bindings = checkNotNull(postgres.containerInfo.networkSettings.ports.bindings[ExposedPort.tcp(5432)])
        assertEquals(1, bindings.size); assertEquals("127.0.0.1", bindings.single().hostIp)
        configuration = PostgresConfiguration(postgres.jdbcUrl, postgres.username, postgres.password)
        connection().use { c ->
            val version = c.createStatement().use { s -> s.executeQuery("SHOW server_version").use { r -> r.next(); r.getString(1) } }
            println("ROOM_PROOF_ENV postgres=$version image=postgres:18.4 network=${postgres.containerInfo.networkSettings.networks.keys} hostBinding=${bindings.single().hostIp}")
        }
        Flyway.configure().dataSource(configuration.url,configuration.user,configuration.password).target("042").load().migrate()
        val legacyScope=scope();apply(legacyScope,attempt(legacyScope));legacy=snapshot(legacyScope)
        assertIs<MarketplaceSalesIntelligenceProjectionWriteResult.Applied>(PostgresMarketplaceSalesIntelligenceProjection(configuration).materializeIfNewer(record(legacy)))
        val invalidScope=scope();apply(invalidScope,attempt(invalidScope));invalidLegacy=snapshot(invalidScope)
        assertIs<MarketplaceSalesIntelligenceProjectionWriteResult.Applied>(PostgresMarketplaceSalesIntelligenceProjection(configuration).materializeIfNewer(record(invalidLegacy)))
        connection().use { c -> execute(c,"UPDATE marketplace_sales_intelligence_projection SET source_evidence_version=999999 WHERE organization_id=? AND marketplace_order_id=?",invalidScope.organizationId.value,invalidScope.orderId.value) }
        connection().use { c ->
            c.autoCommit = false
            try { c.createStatement().use { it.execute(candidate) }; c.commit() }
            catch (e: Exception) { c.rollback(); throw e }
        }
    }
    @AfterAll fun stop() { if (::postgres.isInitialized) postgres.stop() }
    private fun connection(): Connection = DriverManager.getConnection(configuration.url,configuration.user,configuration.password)
    private fun strings(sql: String): List<String> = connection().use { c -> c.createStatement().use { s -> s.executeQuery(sql).use { r -> buildList { while(r.next()) add(r.getString(1)) } } } }

    @Test fun `test only candidate exactly matches documented blueprint`() {
        val repo = generateSequence(Path.of("").toAbsolutePath()) { it.parent }.first { Files.exists(it.resolve("AGENTS.md")) }
        val document = Files.readString(repo.resolve("docs/specifications/SPEC-0091-historical-lineage-ddl-blueprint.md")).replace("\r", "")
        assertEquals(document.substringAfter("```sql\n").substringBefore("```").trim(),candidate.replace("\r", "").substringAfter("\n").trim())
        assertFalse(strings("SELECT version FROM flyway_schema_history WHERE success ORDER BY installed_rank").any { it.toInt() > 42 })
    }
    @Test fun `candidate executes and catalogs contain exact scoped constraints and triggers`() {
        val names = Regex("CONSTRAINT (msi_[a-z_]+)").findAll(candidate).map { it.groupValues[1] }.toSet()
        assertEquals(names,strings("SELECT conname FROM pg_constraint WHERE connamespace='public'::regnamespace AND conname LIKE 'msi_%' AND contype<>'t'").toSet())
        val triggers = Regex("CREATE (?:CONSTRAINT )?TRIGGER (msi_[a-z_]+)").findAll(candidate).map { it.groupValues[1] }.toSet()
        assertEquals(triggers,strings("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgname LIKE 'msi_%'").toSet())
        assertEquals(6,strings("SELECT tgname FROM pg_trigger WHERE tgname LIKE 'msi_%_boundary' AND tgdeferrable AND tginitdeferred").size)
        assertEquals(triggers.size,strings("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal AND tgname LIKE 'msi_%' AND tgenabled='O'").size)
        assertEquals(listOf("21"),strings("SELECT tgtype::text FROM pg_trigger WHERE tgname='msi_current_publish'"))
        assertEquals(listOf("27"),strings("SELECT tgtype::text FROM pg_trigger WHERE tgname='msi_header_immutable'"))
        assertEquals(listOf("34"),strings("SELECT tgtype::text FROM pg_trigger WHERE tgname='msi_header_no_truncate'"))
        assertEquals(listOf("false:1"),strings("SELECT seqcycle::text||':'||seqmin::text FROM pg_sequence WHERE seqrelid=pg_get_serial_sequence('marketplace_sales_intelligence_revision','projection_revision')::regclass"))
        assertEquals(listOf("bigint:YES"),strings("SELECT data_type||':'||is_nullable FROM information_schema.columns WHERE table_name='marketplace_sales_intelligence_projection' AND column_name='current_revision_id'"))
        assertEquals(listOf("a"),strings("SELECT attidentity::text FROM pg_attribute WHERE attrelid='marketplace_sales_intelligence_revision'::regclass AND attname='projection_revision'"))
        assertEquals(listOf("bigint:false"),strings("SELECT data_type||':'||is_nullable FROM information_schema.columns WHERE table_name='marketplace_sales_intelligence_revision' AND column_name='projection_revision'").map { it.replace("NO","false") })
        assertEquals(13,strings("SELECT conname FROM pg_constraint WHERE conname LIKE 'msi_%' AND contype='f'").size)
        assertEquals(Regex("CHECK\\s*\\(").findAll(candidate).count(), strings("SELECT conname FROM pg_constraint WHERE contype='c' AND conrelid::regclass::text LIKE 'marketplace_sales_intelligence_revision%'").size)
        assertEquals(6,strings("SELECT conname FROM pg_constraint WHERE conname LIKE 'msi_%' AND contype='p'").size)
        assertEquals(5,strings("SELECT conname FROM pg_constraint WHERE conname LIKE 'msi_%' AND contype='u'").size)
        val fk=Regex("CONSTRAINT\\s+(msi_[a-z_]+)\\s+FOREIGN KEY\\s*\\(([^)]+)\\)\\s+REFERENCES\\s+([a-z_]+)\\s*\\(([^)]+)\\)")
        val tableBlocks=Regex("CREATE TABLE ([a-z_]+) \\((.*?)\\n\\);",RegexOption.DOT_MATCHES_ALL)
        assertEquals(6,tableBlocks.findAll(candidate).count())
        tableBlocks.findAll(candidate).forEach { table ->
            val columns=Regex("^    ([a-z_]+) (timestamptz\\(6\\)|char\\(3\\)|uuid|bigint|smallint|text|jsonb|bytea)([^\\n]*)",RegexOption.MULTILINE)
            columns.findAll(table.groupValues[2]).forEach { column ->
                val expectedType=when(column.groupValues[2]) { "timestamptz(6)" -> "timestamp(6) with time zone";"char(3)" -> "character(3)";else ->column.groupValues[2] }
                connection().use { c -> c.prepareStatement("SELECT format_type(atttypid,atttypmod),attnotnull FROM pg_attribute WHERE attrelid=?::regclass AND attname=?").use { q ->
                    bind(q,table.groupValues[1],column.groupValues[1]);q.executeQuery().use { r ->assertTrue(r.next());assertEquals(expectedType,r.getString(1));assertEquals(column.groupValues[3].contains("NOT NULL")||column.groupValues[3].contains("GENERATED ALWAYS"),r.getBoolean(2)) }
                } }
            }
        }
        assertEquals(13,fk.findAll(candidate).count())
        fk.findAll(candidate).forEach { expected ->
            connection().use { c ->
                c.prepareStatement("SELECT (SELECT string_agg(a.attname,',' ORDER BY x.ordinality) FROM unnest(k.conkey) WITH ORDINALITY x(attnum,ordinality) JOIN pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=x.attnum),k.confrelid::regclass::text,(SELECT string_agg(a.attname,',' ORDER BY x.ordinality) FROM unnest(k.confkey) WITH ORDINALITY x(attnum,ordinality) JOIN pg_attribute a ON a.attrelid=k.confrelid AND a.attnum=x.attnum) FROM pg_constraint k WHERE conname=?").use { q ->
                    bind(q,expected.groupValues[1]);q.executeQuery().use { r -> assertTrue(r.next())
                        assertEquals(expected.groupValues[2].split(',').joinToString(",") { it.trim() },r.getString(1))
                        assertEquals(expected.groupValues[3],r.getString(2))
                        assertEquals(expected.groupValues[4].split(',').joinToString(",") { it.trim() },r.getString(3))
                    }
                }
            }
        }
        assertTrue(strings("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='msi_observation_source_fk'").single().contains("organization_id, marketplace_order_id, observation_id, evidence_version, identifier_kind"))
        assertTrue(strings("SELECT indexdef FROM pg_indexes WHERE indexname='msi_revision_history_idx'").single().contains("projected_at DESC, projection_revision DESC"))
    }
    private val counter = AtomicLong(100)
    private val time = Instant.parse("2026-10-13T12:00:00.123456Z")
    private fun uuid() = UUID(91,counter.incrementAndGet())
    private fun observation() = MarketplaceEconomicEvidenceObservationId.parse(uuid().toString())
    private fun source() = EconomicSource(EconomicSourceKind.MANUAL,EconomicSourceSystemKey("fixture"),EconomicExternalReferenceState.Absent(EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN))
    private fun scope(): MarketplaceEconomicEvidenceSubject {
        val subject=MarketplaceEconomicEvidenceSubject(OrganizationId(uuid()),MarketplaceOrderId(uuid()),MarketplaceKey("fixture"),MarketplaceExternalOrderId("order-${counter.get()}"),MarketplaceCurrency("BRL"))
        connection().use { c -> execute(c,"INSERT INTO integration_organization VALUES (?,'ACTIVE',?,?)",subject.organizationId.value,Timestamp.from(time),Timestamp.from(time)) }
        return subject
    }
    private fun evidence() = PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration)
    private fun writer() = PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration)
    private fun apply(subject: MarketplaceEconomicEvidenceSubject, update: MarketplaceIndependentEconomicEvidenceUpdate) {
        val found = evidence().find(subject)
        val version = (found as? MarketplaceIndependentEconomicEvidenceReadResult.Found)?.versionedEvidence?.version ?: MarketplaceEconomicEvidenceVersion.ZERO
        assertIs<MarketplaceIndependentEconomicEvidencePersistResult.Applied>(evidence().apply(version,update))
    }
    private fun attempt(subject: MarketplaceEconomicEvidenceSubject) = MarketplaceIndependentEconomicEvidenceUpdate.RecordAttempt(MarketplaceEconomicEvidenceCollectionAttempt(observation(),subject,MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,EconomicSourceSystemKey("fixture"),MarketplaceEconomicEvidenceAttemptOutcome.NO_EVIDENCE,time))
    private fun fact(subject: MarketplaceEconomicEvidenceSubject) = MarketplaceIndependentEconomicFact.OrderOccurrence(MarketplaceEconomicOrderOccurrenceObservation(observation(),subject,source(),time.minusSeconds(60),time))
    private fun snapshot(subject: MarketplaceEconomicEvidenceSubject): ConsumedEconomicEvidenceSnapshot {
        val versioned=assertIs<MarketplaceIndependentEconomicEvidenceReadResult.Found>(evidence().find(subject)).versionedEvidence
        val trigger=connection().use { c -> c.prepareStatement("SELECT change_sequence FROM marketplace_economic_evidence_update WHERE organization_id=? AND marketplace_order_id=? AND evidence_version=?").use { q -> bind(q,subject.organizationId.value,subject.orderId.value,versioned.version.valueForPersistence());q.executeQuery().use { r -> assertTrue(r.next());ChangeSequenceCheckpoint(r.getLong(1)) } } }
        val assembled=MarketplaceEconomicTruthAssembler.assemble(versioned.evidence)
        val state=when(assembled) {
            is MarketplaceEconomicTruthAssemblyResult.NotReady -> MarketplaceSalesIntelligenceState.Unresolved(assembled.assemblyPolicyVersion,assembled.reasons)
            is MarketplaceEconomicTruthAssemblyResult.Ready -> { val calculation=MarketplaceEconomicTruthCalculator.calculate(assembled.order);MarketplaceSalesIntelligenceState.Calculated(assembled.assemblyPolicyVersion,calculationPolicyVersionOf(calculation),calculation) }
        }
        return ConsumedEconomicEvidenceSnapshot.capture(versioned,trigger).finalize(assembled,state,time.plusSeconds(versioned.version.valueForPersistence()))
    }
    private fun record(s: ConsumedEconomicEvidenceSnapshot)=MarketplaceSalesIntelligenceProjectionRecord(s.subject.organizationId,s.subject.orderId,s.readEvidenceVersion,s.outcome,s.triggerChangeSequence,s.projectedAt)
    private fun publish(s: ConsumedEconomicEvidenceSnapshot): Long = assertIs<EconomicLineagePublicationResult.Published>(writer().publish(s,record(s))).revisionId
    private fun read(s: ConsumedEconomicEvidenceSnapshot,id: Long)=assertIs<EconomicLineageReadResult.Found>(writer().findHistoricalRevision(s.subject.organizationId,s.subject.orderId,id)).revision
    private fun clone(s: ConsumedEconomicEvidenceSnapshot, outcome: MarketplaceSalesIntelligenceState=s.outcome, members: List<ConsumedEconomicEvidenceMember> = s.members, projectedAt: Instant=s.projectedAt, readVersion: MarketplaceEconomicEvidenceVersion=s.readEvidenceVersion)=
        ConsumedEconomicEvidenceSnapshot.rehydratePersisted(s.subject,readVersion,s.triggerChangeSequence,projectedAt,outcome,members,s.componentCoverage)
    private fun execute(c: Connection,sql: String,vararg args: Any?): Int=c.prepareStatement(sql).use { q ->bind(q,*args);q.executeUpdate() }
    private fun bind(q: java.sql.PreparedStatement,vararg args: Any?) { args.forEachIndexed { index,a ->q.setObject(index+1,a) } }
    private fun queryLong(c: Connection, sql: String,vararg args: Any?): Long=c.prepareStatement(sql).use { q -> bind(q,*args);q.executeQuery().use { r ->assertTrue(r.next());r.getLong(1) } }
    private fun counts(subject: MarketplaceEconomicEvidenceSubject)=connection().use { c ->
        listOf("revision","revision_observation","revision_correction","revision_reason","revision_coverage","revision_publication").associateWith { name ->
            queryLong(c,"SELECT count(*) FROM marketplace_sales_intelligence_$name WHERE organization_id=? AND marketplace_order_id=?",subject.organizationId.value,subject.orderId.value) }
    }
    private fun current(subject: MarketplaceEconomicEvidenceSubject)=connection().use { c ->c.prepareStatement("SELECT row_to_json(p)::text FROM marketplace_sales_intelligence_projection p WHERE organization_id=? AND marketplace_order_id=?").use { q ->bind(q,subject.organizationId.value,subject.orderId.value);q.executeQuery().use { r -> if(r.next()) r.getString(1) else null } } }
    private fun correctionFixture(): Pair<ConsumedEconomicEvidenceSnapshot,ConsumedEconomicEvidenceSnapshot> {
        val subject=scope();val original=fact(subject);apply(subject,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(original));val old=snapshot(subject)
        val replacement=fact(subject)
        apply(subject,MarketplaceIndependentEconomicEvidenceUpdate.Correct(MarketplaceEconomicEvidenceCorrection(observation(),subject,replacement,original.id,MarketplaceEconomicEvidenceCorrectionReason.SOURCE_CORRECTION,time)))
        return old to snapshot(subject)
    }

    @Test fun `single connection transaction publishes and manifest round trips without business replay`() {
        val subject=scope();apply(subject,attempt(subject));val s=snapshot(subject)
        val calls=AtomicInteger();val commits=AtomicInteger();val rollbacks=AtomicInteger();val disabled=AtomicInteger()
        val repository=PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration,{_,_->},{
            calls.incrementAndGet();val real=connection()
            Proxy.newProxyInstance(Connection::class.java.classLoader,arrayOf(Connection::class.java)) { _,method,args ->
                when(method.name) { "commit" ->commits.incrementAndGet();"rollback"->rollbacks.incrementAndGet();"setAutoCommit"->if(args?.first()==false) disabled.incrementAndGet() }
                try { method.invoke(real,*(args ?: emptyArray())) } catch(e: InvocationTargetException) { throw e.targetException }
            } as Connection
        })
        val result=assertIs<EconomicLineagePublicationResult.Published>(repository.publish(s,record(s)))
        assertEquals(1,calls.get());assertEquals(1,commits.get());assertEquals(0,rollbacks.get());assertEquals(1,disabled.get())
        val stored=read(s,result.revisionId)
        assertContentEquals(s.canonicalManifestForPersistence(),stored.snapshot.canonicalManifestForPersistence())
        assertEquals(s.manifestDigest,stored.snapshot.manifestDigest);assertIs<MarketplaceSalesIntelligenceState.Unresolved>(stored.snapshot.outcome)
        assertIs<EconomicLineageReadResult.Found>(writer().findPublishedRevisionForTrigger(subject.organizationId,subject.orderId,s.triggerChangeSequence))
        assertEquals(1L,counts(subject)["revision_publication"])
    }
    @Test fun `identical and divergent duplicate contexts are exact not do nothing`() {
        val subject=scope();apply(subject,attempt(subject));val s=snapshot(subject);val id=publish(s)
        assertEquals(id,assertIs<EconomicLineagePublicationResult.IdenticalPublished>(writer().publish(s,record(s))).revisionId)
        val policy=MarketplaceEconomicTruthAssemblyPolicyVersion("fixture/2")
        val changedPolicy=clone(s,MarketplaceSalesIntelligenceState.Unresolved(policy,assertIs<MarketplaceSalesIntelligenceState.Unresolved>(s.outcome).reasons))
        val changedOutcome=clone(s,MarketplaceSalesIntelligenceState.Unresolved(s.outcome.assemblyPolicyVersion,setOf(MarketplaceEconomicTruthAssemblyNotReadyReason.ORDER_OCCURRED_AT_CONFLICT)))
        val changedMember=clone(s,members=s.members.map { it.copy(observation=it.observation.copy(recordedAt=time.plusSeconds(1))) })
        listOf(changedPolicy,changedOutcome,changedMember,clone(s,projectedAt=s.projectedAt.plusSeconds(1))).forEach {
            assertIs<EconomicLineagePublicationResult.IntegrityFailure>(writer().publish(it,record(it)))
        }
        apply(subject,attempt(subject));val later=snapshot(subject)
        val changedRead=ConsumedEconomicEvidenceSnapshot.rehydratePersisted(subject,later.readEvidenceVersion,s.triggerChangeSequence,s.projectedAt,later.outcome,later.members,later.componentCoverage)
        assertIs<EconomicLineagePublicationResult.IntegrityFailure>(writer().publish(changedRead,record(changedRead)))
        assertEquals(1L,counts(subject)["revision"]);assertEquals(s.manifestDigest,read(s,id).snapshot.manifestDigest)
    }
    @Test fun `unresolved later ready incomplete and policy change preserve old history`() {
        val subject=scope();apply(subject,attempt(subject));val first=snapshot(subject);val id1=publish(first)
        apply(subject,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(fact(subject)));val second=snapshot(subject);val id2=publish(second)
        assertIs<MarketplaceSalesIntelligenceState.Unresolved>(read(first,id1).snapshot.outcome)
        val ready=read(second,id2).snapshot;assertEquals(EconomicOrderAssemblyState.READY,ready.orderAssemblyState)
        assertIs<MarketplaceEconomicTruthCalculationResult.Incomplete>(assertIs<MarketplaceSalesIntelligenceState.Calculated>(ready.outcome).calculationResult)
        assertEquals(first.manifestDigest,read(first,id1).snapshot.manifestDigest)
        apply(subject,attempt(subject));val third=snapshot(subject)
        // Context fixture for versioned policy storage; no fabricated complete calculation.
        val changed=clone(third,(third.outcome as MarketplaceSalesIntelligenceState.Calculated).copy(assemblyPolicyVersion=MarketplaceEconomicTruthAssemblyPolicyVersion("fixture/2")))
        val id3=publish(changed)
        assertEquals("fixture/2",read(changed,id3).snapshot.outcome.assemblyPolicyVersion.value)
        assertEquals(second.outcome.assemblyPolicyVersion,read(second,id2).snapshot.outcome.assemblyPolicyVersion)
    }
    @Test fun `correction history retains old active fact and exact current edges`() {
        val (old,corrected)=correctionFixture();val id1=publish(old);val id2=publish(corrected)
        assertEquals(ConsumedEconomicEvidenceContextRole.CONSUMED_ACTIVE_FACT,read(old,id1).snapshot.members.single().contextRole)
        val stored=read(corrected,id2).snapshot
        assertEquals(1,stored.members.count { it.contextRole==ConsumedEconomicEvidenceContextRole.HISTORICAL_SUPERSEDED_FACT })
        assertEquals(1,stored.members.count { it.contextRole==ConsumedEconomicEvidenceContextRole.CORRECTION_CONTEXT })
        assertEquals(1,stored.members.count { it.contextRole==ConsumedEconomicEvidenceContextRole.CONSUMED_ACTIVE_FACT })
        assertEquals(1L,counts(old.subject)["revision_correction"])
        assertEquals(old.manifestDigest,read(old,id1).snapshot.manifestDigest)
        assertContentEquals(corrected.canonicalManifestForPersistence(),stored.canonicalManifestForPersistence())
        val currentEvidence=assertIs<MarketplaceIndependentEconomicEvidenceReadResult.Found>(evidence().find(old.subject)).versionedEvidence.evidence
        val active=currentEvidence.activeFacts.single()
        apply(old.subject,MarketplaceIndependentEconomicEvidenceUpdate.Correct(MarketplaceEconomicEvidenceCorrection(observation(),old.subject,fact(old.subject),active.id,MarketplaceEconomicEvidenceCorrectionReason.SOURCE_CORRECTION,time)))
        val third=snapshot(old.subject);val id3=publish(third);val chain=read(third,id3).snapshot
        assertEquals(2,chain.members.count { it.contextRole==ConsumedEconomicEvidenceContextRole.HISTORICAL_SUPERSEDED_FACT })
        assertEquals(2,chain.members.count { it.contextRole==ConsumedEconomicEvidenceContextRole.CORRECTION_CONTEXT })
        assertEquals(1,chain.members.count { it.contextRole==ConsumedEconomicEvidenceContextRole.CONSUMED_ACTIVE_FACT })
        assertEquals(corrected.manifestDigest,read(corrected,id2).snapshot.manifestDigest)
        assertEquals(old.manifestDigest,read(old,id1).snapshot.manifestDigest)
        assertEquals(3L,counts(old.subject)["revision_correction"])
    }
    @Test fun `all eight failures roll back header members edges outcomes receipt and current`() {
        val points=EconomicLineageWriteStage.entries.filter { it!=EconomicLineageWriteStage.AFTER_LOCK }
        points.forEach { point ->
            val (old,candidate)=correctionFixture();val id=publish(old);val before=counts(old.subject);val current=current(old.subject)
            val repository=PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration,{ stage,c ->
                if(stage==point) {
                    if(point==EconomicLineageWriteStage.AFTER_CURRENT_BEFORE_COMMIT)
                        assertEquals(2L,queryLong(c,"SELECT count(*) FROM marketplace_sales_intelligence_revision_publication WHERE organization_id=? AND marketplace_order_id=?",old.subject.organizationId.value,old.subject.orderId.value))
                    if(point==EconomicLineageWriteStage.DURING_CURRENT_PUBLICATION) {
                        c.prepareStatement("UPDATE marketplace_sales_intelligence_projection SET current_revision_id=NULL WHERE organization_id=? AND marketplace_order_id=?").use { q ->bind(q,old.subject.organizationId.value,old.subject.orderId.value);q.executeUpdate() }
                    } else throw IllegalStateException("injected $point")
                }
            },{ connection() })
            assertIs<EconomicLineagePublicationResult.IntegrityFailure>(repository.publish(candidate,record(candidate)),point.name)
            assertEquals(before,counts(old.subject),point.name);assertEquals(current,current(old.subject),point.name)
            assertEquals(old.manifestDigest,read(old,id).snapshot.manifestDigest)
        }
    }
    @Test fun `concurrent scheduling orders serialize real publications with no orphan losers`() {
        listOf(false,true).forEach { newerFirst ->
            val subject=scope();repeat(5) { apply(subject,attempt(subject)) };apply(subject,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(fact(subject)))
            val base=snapshot(subject);publish(base)
            apply(subject,attempt(subject));val a=snapshot(subject)
            apply(subject,attempt(subject));val b=snapshot(subject)
            assertEquals(listOf(6L,7L,8L),listOf(base,a,b).map { it.readEvidenceVersion.valueForPersistence() })
            val acquired=CountDownLatch(1);val release=CountDownLatch(1);val started=CountDownLatch(1)
            val firstPid=AtomicInteger();val secondPid=AtomicInteger()
            val first=PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration,{ stage,c -> if(stage==EconomicLineageWriteStage.AFTER_LOCK) { firstPid.set(queryLong(c,"SELECT pg_backend_pid()").toInt()); acquired.countDown();assertTrue(release.await(20,TimeUnit.SECONDS)) } },{ connection() })
            val second=PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration,{_,_->},{ connection().also { secondPid.set(queryLong(it,"SELECT pg_backend_pid()").toInt());started.countDown() } })
            val pool=Executors.newFixedThreadPool(2)
            try {
                val f1=pool.submit<EconomicLineagePublicationResult> { val s=if(newerFirst)b else a;first.publish(s,record(s)) }
                assertTrue(acquired.await(20,TimeUnit.SECONDS))
                val f2=pool.submit<EconomicLineagePublicationResult> { val s=if(newerFirst)a else b;second.publish(s,record(s)) }
                assertTrue(started.await(20,TimeUnit.SECONDS))
                var blocked=false
                repeat(100) {
                    if(!blocked) { blocked=connection().use { c ->queryLong(c,"SELECT count(*) FROM pg_stat_activity WHERE pid=? AND wait_event_type='Lock'",secondPid.get()) } == 1L
                        if(!blocked) Thread.sleep(20) }
                }
                assertTrue(blocked,"second real backend must be waiting on the held publication lock")
                assertNotEquals(firstPid.get(),secondPid.get())
                release.countDown()
                assertIs<EconomicLineagePublicationResult.Published>(f1.get(30,TimeUnit.SECONDS))
                if(newerFirst) assertIs<EconomicLineagePublicationResult.Superseded>(f2.get(30,TimeUnit.SECONDS)) else assertIs<EconomicLineagePublicationResult.Published>(f2.get(30,TimeUnit.SECONDS))
            } finally { release.countDown();pool.shutdownNow() }
            assertEquals(if(newerFirst)2L else 3L,counts(subject)["revision"])
            assertEquals(counts(subject)["revision"],counts(subject)["revision_publication"])
            val winner=assertIs<EconomicLineageReadResult.Found>(writer().findPublishedRevisionForTrigger(subject.organizationId,subject.orderId,b.triggerChangeSequence)).revision
            connection().use { c ->assertEquals(winner.revisionId,queryLong(c,"SELECT current_revision_id FROM marketplace_sales_intelligence_projection WHERE organization_id=? AND marketplace_order_id=?",subject.organizationId.value,subject.orderId.value)) }
            assertEquals(b.readEvidenceVersion,winner.snapshot.readEvidenceVersion)
            if(newerFirst) assertIs<EconomicLineageReadResult.NotFound>(writer().findPublishedRevisionForTrigger(subject.organizationId,subject.orderId,a.triggerChangeSequence))
        }
    }
    @Test fun `foreign reads and mismatched publication scope fail closed`() {
        val subject=scope();apply(subject,attempt(subject));val s=snapshot(subject);val id=publish(s)
        val foreign=scope();apply(foreign,attempt(foreign))
        assertIs<EconomicLineageReadResult.NotFound>(writer().findHistoricalRevision(foreign.organizationId,subject.orderId,id))
        assertIs<EconomicLineageReadResult.NotFound>(writer().findHistoricalRevision(subject.organizationId,foreign.orderId,id))
        assertIs<EconomicLineagePublicationResult.IntegrityFailure>(writer().publish(s,record(s).copy(organizationId=foreign.organizationId)))
        assertIs<EconomicLineagePublicationResult.IntegrityFailure>(writer().publish(s,record(s).copy(marketplaceOrderId=foreign.orderId)))
        assertEquals(1L,counts(subject)["revision"])
    }
    @Test fun `wrong durable member version kind and foreign identities are rejected by SQL`() {
        val subject=scope();val f=fact(subject);apply(subject,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(f));val old=snapshot(subject);publish(old)
        apply(subject,attempt(subject));val s=snapshot(subject)
        val foreign=scope();val ff=fact(foreign);apply(foreign,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(ff))
        val wrongOrder=subject.copy(orderId=MarketplaceOrderId(uuid()),externalOrderId=MarketplaceExternalOrderId("other-order"));val of=fact(wrongOrder);apply(wrongOrder,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(of))
        listOf(Triple(f.id,2L,"FACT"),Triple(f.id,1L,"ATTEMPT"),Triple(ff.id,1L,"FACT"),Triple(of.id,1L,"FACT")).forEach { (id,version,kind) ->
            val before=counts(subject);var rejected=false
            val repository=PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration,{stage,c ->if(stage==EconomicLineageWriteStage.AFTER_HEADER) {
                val revision=queryLong(c,"SELECT projection_revision FROM marketplace_sales_intelligence_revision WHERE organization_id=? AND marketplace_order_id=? AND trigger_change_sequence=?",subject.organizationId.value,subject.orderId.value,s.triggerChangeSequence.valueForPersistence())
                try { execute(c,"INSERT INTO marketplace_sales_intelligence_revision_observation VALUES (?,?,?,?,?,?,?,?,?,?)",subject.organizationId.value,subject.orderId.value,revision,2L,id.valueForPersistence(),version,kind,if(kind=="FACT") "CONSUMED_ACTIVE_FACT" else "ATTEMPT_CONTEXT","MARKETPLACE_ORDER",Timestamp.from(time)) }
                catch(e: SQLException) { assertEquals("23503",e.sqlState);rejected=true;throw e }
            } },{connection()})
            assertIs<EconomicLineagePublicationResult.IntegrityFailure>(repository.publish(s,record(s)));assertTrue(rejected);assertEquals(before,counts(subject))
        }
    }
    @Test fun `post publication mutations pointer attacks and receipt forgery reject`() {
        val (old,s)=correctionFixture();publish(old);val id=publish(s)
        val foreign=scope();apply(foreign,attempt(foreign));val foreignId=publish(snapshot(foreign))
        val org=s.subject.organizationId.value;val order=s.subject.orderId.value
        val attacks=listOf(
            "UPDATE marketplace_sales_intelligence_revision SET manifest_digest=repeat('0',64) WHERE projection_revision=$id",
            "DELETE FROM marketplace_sales_intelligence_revision WHERE projection_revision=$id",
            "TRUNCATE marketplace_sales_intelligence_revision",
            "UPDATE marketplace_sales_intelligence_revision_observation SET recorded_at=recorded_at WHERE projection_revision=$id",
            "DELETE FROM marketplace_sales_intelligence_revision_observation WHERE projection_revision=$id",
            "INSERT INTO marketplace_sales_intelligence_revision_observation SELECT * FROM marketplace_sales_intelligence_revision_observation WHERE projection_revision=$id LIMIT 1",
            "INSERT INTO marketplace_sales_intelligence_revision_correction SELECT * FROM marketplace_sales_intelligence_revision_correction WHERE projection_revision=$id LIMIT 1",
            "INSERT INTO marketplace_sales_intelligence_revision_publication VALUES ('$org','$order',$id,now())",
            "UPDATE marketplace_sales_intelligence_projection SET current_revision_id=NULL WHERE organization_id='$org' AND marketplace_order_id='$order'",
            "UPDATE marketplace_sales_intelligence_projection SET current_revision_id=$foreignId WHERE organization_id='$org' AND marketplace_order_id='$order'",
            "DELETE FROM marketplace_sales_intelligence_projection WHERE organization_id='$org' AND marketplace_order_id='$order'",
            "TRUNCATE marketplace_sales_intelligence_projection",
            "UPDATE marketplace_sales_intelligence_projection SET marketplace_order_id='${foreign.orderId.value}' WHERE organization_id='$org' AND marketplace_order_id='$order'"
        )
        val before=counts(s.subject);val current=current(s.subject)
        attacks.forEach { sql ->connection().use { c ->assertFailsWith<SQLException>(sql) { c.createStatement().use { it.execute(sql) } } } }
        assertEquals(before,counts(s.subject));assertEquals(current,current(s.subject))
    }
    @Test fun `controlled disposable corruption fails historical read without leaving triggers disabled`() {
        val subject=scope();apply(subject,attempt(subject));val s=snapshot(subject);val id=publish(s)
        connection().use { c ->c.autoCommit=false
            try {
                c.createStatement().use { q ->
                    q.execute("ALTER TABLE marketplace_sales_intelligence_revision DISABLE TRIGGER msi_header_immutable")
                    q.execute("UPDATE marketplace_sales_intelligence_revision SET manifest_digest=repeat('0',64) WHERE projection_revision=$id")
                    q.execute("ALTER TABLE marketplace_sales_intelligence_revision ENABLE TRIGGER msi_header_immutable")
                };c.commit()
            } catch(e: Exception) { c.rollback();throw e }
        }
        assertIs<EconomicLineageReadResult.IntegrityFailure>(writer().findHistoricalRevision(subject.organizationId,subject.orderId,id))
        assertEquals(listOf("O"),strings("SELECT tgenabled::text FROM pg_trigger WHERE tgname='msi_header_immutable'"))
        connection().use { c ->assertFailsWith<SQLException> { c.createStatement().use { it.execute("UPDATE marketplace_sales_intelligence_revision SET manifest_digest=repeat('1',64) WHERE projection_revision=$id") } } }
    }

    @Test fun `legacy row stays unlinked until a genuine new transition`() {
        val subject=legacy.subject
        assertIs<EconomicLineagePublicationResult.Superseded>(writer().publish(legacy,record(legacy))).also { assertNull(it.currentRevisionId) }
        assertEquals(0L,counts(subject)["revision"])
        assertIs<EconomicLineageReadResult.NotFound>(writer().findPublishedRevisionForTrigger(subject.organizationId,subject.orderId,legacy.triggerChangeSequence))
        apply(subject,attempt(subject));val next=snapshot(subject);val id=publish(next)
        assertEquals(id,read(next,id).revisionId);assertEquals(1L,counts(subject)["revision"])
        assertIs<EconomicLineagePublicationResult.IntegrityFailure>(writer().publish(invalidLegacy,record(invalidLegacy)))
        assertEquals(0L,counts(invalidLegacy.subject)["revision"])
    }
    @Test fun `lost commit acknowledgement returns unknown and reconciles exact stored publication`() {
        val subject=scope();apply(subject,attempt(subject));val s=snapshot(subject)
        val repository=PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration,{_,_->},{
            val real=connection()
            Proxy.newProxyInstance(Connection::class.java.classLoader,arrayOf(Connection::class.java)) { _,method,args ->
                try {
                    val result=method.invoke(real,*(args ?: emptyArray()))
                    if(method.name=="commit") throw SQLException("simulated acknowledgement loss","08006")
                    result
                } catch(e: InvocationTargetException) { throw e.targetException }
            } as Connection
        })
        assertIs<EconomicLineagePublicationResult.CommitOutcomeUnknown>(repository.publish(s,record(s)))
        val existing=assertIs<EconomicLineageReadResult.Found>(writer().findPublishedRevisionForTrigger(subject.organizationId,subject.orderId,s.triggerChangeSequence)).revision
        assertEquals(existing.revisionId,assertIs<EconomicLineagePublicationResult.IdenticalPublished>(writer().publish(s,record(s))).revisionId)
        assertEquals(1L,counts(subject)["revision_publication"])
    }
    @Test fun `deferred orphan and wrong family fail real SQL validation and roll back`() {
        listOf(false,true).forEach { wrongFamily ->
            val subject=scope();apply(subject,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(fact(subject)));val old=snapshot(subject);publish(old)
            apply(subject,attempt(subject));val next=snapshot(subject)
            val before=counts(subject);val current=current(subject)
            if(wrongFamily) {
                val changed=clone(next,members=next.members.map { if(it.observation.identifierKind==MarketplaceEconomicObservationIdentifierKind.FACT) it.copy(observation=it.observation.copy(family=MarketplaceEconomicEvidenceFamily.PRODUCT_COST)) else it })
                assertIs<EconomicLineagePublicationResult.IntegrityFailure>(writer().publish(changed,record(changed)))
            } else {
                var observed=false
                val repository=PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration,{stage,c ->if(stage==EconomicLineageWriteStage.AFTER_HEADER) {
                    try { c.createStatement().use { it.execute("SET CONSTRAINTS ALL IMMEDIATE") } }
                    catch(e: SQLException) { assertTrue(e.message.orEmpty().contains("revision was never published"));observed=true;throw e }
                } },{connection()})
                assertIs<EconomicLineagePublicationResult.IntegrityFailure>(repository.publish(next,record(next)));assertTrue(observed)
            }
            assertEquals(before,counts(subject));assertEquals(current,current(subject))
        }
    }
    @Test fun `half self wrong version replacement and foreign correction edges reject by SQL`() {
        listOf("half","self","version","replacement","foreign").forEach { attack ->
            val (old,next)=correctionFixture();publish(old)
            val subject=old.subject;val before=counts(subject);val current=current(subject)
            val foreign=scope();val foreignFact=fact(foreign);apply(foreign,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(foreignFact))
            val edge=next.members.single { it.contextRole==ConsumedEconomicEvidenceContextRole.CORRECTION_CONTEXT }.observation
            var rejected=false
            val repository=PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration,{stage,c ->
                if(stage==EconomicLineageWriteStage.DURING_LATER_MEMBER) {
                    val id=queryLong(c,"SELECT projection_revision FROM marketplace_sales_intelligence_revision WHERE organization_id=? AND marketplace_order_id=? AND trigger_change_sequence=?",subject.organizationId.value,subject.orderId.value,next.triggerChangeSequence.valueForPersistence())
                    if(queryLong(c,"SELECT count(*) FROM marketplace_sales_intelligence_revision_observation WHERE projection_revision=?",id)==next.members.size.toLong()) {
                        val target=if(attack=="self") edge.observationId.valueForPersistence() else if(attack=="foreign") foreignFact.id.valueForPersistence() else checkNotNull(edge.supersedesObservationId).valueForPersistence()
                        val replacement=if(attack=="half") null else if(attack=="replacement") foreignFact.id.valueForPersistence() else checkNotNull(edge.replacementObservationId).valueForPersistence()
                        try { execute(c,"INSERT INTO marketplace_sales_intelligence_revision_correction (organization_id,marketplace_order_id,projection_revision,correction_id,evidence_version,superseded_observation_id,superseded_evidence_version,replacement_observation_id) VALUES (?,?,?,?,?,?,?,?)",subject.organizationId.value,subject.orderId.value,id,edge.observationId.valueForPersistence(),if(attack=="version")3L else 2L,target,1L,replacement) }
                        catch(e: SQLException) { assertTrue(e.sqlState in setOf("23502","23503","23514"),attack);rejected=true;throw e }
                    }
                }
            },{connection()})
            assertIs<EconomicLineagePublicationResult.IntegrityFailure>(repository.publish(next,record(next)));assertTrue(rejected,attack)
            assertEquals(before,counts(subject));assertEquals(current,current(subject))
        }
    }
    @Test fun `strict frozen codec rejects unknown nested fields duplicates and invalid values`() {
        val subject=scope();apply(subject,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(fact(subject)))
        val component=EconomicComponent(subject.organizationId,EconomicComponentId(uuid()),subject.orderId,EconomicComponentType.REVENUE,EconomicDirection.ADDITION,MarketplaceMoney.parse(subject.currency,"10"),source(),time.minusSeconds(60),EconomicEvidenceQuality.CONFIRMED)
        apply(subject,MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(MarketplaceIndependentEconomicFact.Component(MarketplaceEconomicComponentObservation(observation(),subject,MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,component,EconomicComponentCoverage.COMPLETE,time))))
        val s=snapshot(subject)
        val id=publish(s)
        val roundtrip=read(s,id).snapshot
        assertContentEquals(s.canonicalManifestForPersistence(),roundtrip.canonicalManifestForPersistence())
        val storedCalculation=assertIs<MarketplaceEconomicTruthCalculationResult.Incomplete>(assertIs<MarketplaceSalesIntelligenceState.Calculated>(roundtrip.outcome).calculationResult)
        assertEquals(listOf(component),storedCalculation.suppliedComponents)
        assertEquals(EconomicComponentCoverage.PARTIAL,roundtrip.componentCoverage[EconomicComponentType.REVENUE])
        val encoded=MarketplaceSalesIntelligenceStateCodecV1.encodeFrozen(s.outcome)
        val payload=kotlinx.serialization.json.Json.parseToJsonElement(encoded.payload) as kotlinx.serialization.json.JsonObject
        val bad=kotlinx.serialization.json.JsonObject(payload+mapOf("unknown" to kotlinx.serialization.json.JsonPrimitive("bad")))
        assertFailsWith<IllegalArgumentException> { MarketplaceSalesIntelligenceStateCodecV1.decodeFrozen(subject.organizationId,subject.orderId,s.outcome.assemblyPolicyVersion,encoded.stateKind,encoded.calculationPolicyVersion,encoded.calculationKind,bad) }
        val missing=payload.getValue("missingTypes") as kotlinx.serialization.json.JsonArray
        val duplicate=kotlinx.serialization.json.JsonObject(payload+mapOf("missingTypes" to kotlinx.serialization.json.JsonArray((missing+missing.first()).sortedBy { it.toString() })))
        val components=payload.getValue("suppliedComponents") as kotlinx.serialization.json.JsonArray
        val first=components.single() as kotlinx.serialization.json.JsonObject
        val src=first.getValue("source") as kotlinx.serialization.json.JsonObject
        val money=first.getValue("magnitude") as kotlinx.serialization.json.JsonObject
        val badComponents=listOf(
            kotlinx.serialization.json.JsonObject(first+mapOf("source" to kotlinx.serialization.json.JsonObject(src+mapOf("unknown" to kotlinx.serialization.json.JsonPrimitive("bad"))))),
            kotlinx.serialization.json.JsonObject(first+mapOf("magnitude" to kotlinx.serialization.json.JsonObject(money+mapOf("amount" to kotlinx.serialization.json.JsonPrimitive("NaN"))))),
            kotlinx.serialization.json.JsonObject(first+mapOf("id" to kotlinx.serialization.json.JsonPrimitive(component.id.value.toString().uppercase())))
        )
        badComponents.forEach { changed ->
            val nested=kotlinx.serialization.json.JsonObject(payload+mapOf("suppliedComponents" to kotlinx.serialization.json.JsonArray(listOf(changed))))
            assertFailsWith<IllegalArgumentException> { MarketplaceSalesIntelligenceStateCodecV1.decodeFrozen(subject.organizationId,subject.orderId,s.outcome.assemblyPolicyVersion,encoded.stateKind,encoded.calculationPolicyVersion,encoded.calculationKind,nested) }
        }
        // Strict snapshot validation catches duplicated typed coverage even if canonical sorting alone retains it.
        assertFailsWith<IllegalArgumentException> {
            val decoded=MarketplaceSalesIntelligenceStateCodecV1.decodeFrozen(subject.organizationId,subject.orderId,s.outcome.assemblyPolicyVersion,encoded.stateKind,encoded.calculationPolicyVersion,encoded.calculationKind,duplicate)
            clone(s,outcome=decoded)
        }
    }

    @Test fun `concurrent identical candidates produce one revision and one idempotent winner`() {
        val subject=scope();apply(subject,attempt(subject));val s=snapshot(subject)
        val ready=CountDownLatch(2);val start=CountDownLatch(1);val pool=Executors.newFixedThreadPool(2)
        try {
            val futures=(1..2).map { pool.submit<EconomicLineagePublicationResult> { ready.countDown();assertTrue(start.await(20,TimeUnit.SECONDS));writer().publish(s,record(s)) } }
            assertTrue(ready.await(20,TimeUnit.SECONDS));start.countDown()
            val results=futures.map { it.get(30,TimeUnit.SECONDS) }
            assertEquals(1,results.count { it is EconomicLineagePublicationResult.Published })
            assertEquals(1,results.count { it is EconomicLineagePublicationResult.IdenticalPublished })
            assertEquals(1L,counts(subject)["revision"]);assertEquals(1L,counts(subject)["revision_publication"])
        } finally { start.countDown();pool.shutdownNow() }
    }

}
