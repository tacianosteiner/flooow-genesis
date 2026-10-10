package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.identity.*
import io.flooow.marketplace.persistence.postgres.PostgresApprovalGovernance
import io.flooow.marketplace.persistence.postgres.PostgresConfiguration
import io.flooow.organization.OrganizationId
import org.flywaydb.core.Flyway
import org.postgresql.ds.PGSimpleDataSource
import org.postgresql.util.PSQLException
import org.testcontainers.postgresql.PostgreSQLContainer
import java.io.PrintWriter
import java.security.KeyFactory
import java.security.Signature
import java.security.spec.PKCS8EncodedKeySpec
import java.sql.*
import java.time.*
import java.util.Base64
import java.util.UUID
import javax.sql.DataSource
import kotlin.test.*

class CommandAuthorityCeremonyPostgresTest {
    private lateinit var db: PostgreSQLContainer
    @BeforeTest fun start(){db=PostgreSQLContainer("postgres:18.4").also{it.start()};Flyway.configure().dataSource(db.jdbcUrl,db.username,db.password).target("042").load().migrate();auditReadGrants();seed()}
    @AfterTest fun stop(){if(::db.isInitialized)db.stop()}

    @Test fun `real attested ceremony links authority applies decision destroys secret and replays authority exactly`() {
        val tty=RecordingTty();val lifecycle=Lifecycle();val composition=composition();val before=snapshot();val manifest=manifest()
        val plan=plan();val signed=sign(manifest);val input=OfflineFieldProofInput(signed,target(manifest),command(manifest),plan)
        val applied=assertIs<AttestedCeremonyResult.Applied>(ceremony(composition,tty,lifecycle).execute(signed,input.target,input.command,plan))
        assertEquals(Delta(1,1,1,1,1,3,1,1),snapshot()-before)
        assertEquals(1,tty.calls);assertEquals(1,lifecycle.created);assertEquals(1,lifecycle.destroyed);assertTrue(lifecycle.verifierCreationRejected)
        assertEquals(applied.plan.decisionId,uuidValue("SELECT decision_id FROM marketplace_transaction_identity_head"))
        assertEquals(manifestId,uuidValue("SELECT attestation_manifest_id FROM command_authority_operation WHERE operation='GRANT'"))
        assertEquals(0,rawSecretOccurrences(tty.token))
        val principal=CommandPrincipalId(uuidValue("SELECT principal_id FROM command_principal"));val credential=uuidValue("SELECT credential_id FROM command_credential_revision");val grant=uuidValue("SELECT grant_id FROM command_permission_grant");val verifier=bytes("SELECT secret_verifier FROM command_credential_revision")
        val operations=connection().use{c->c.createStatement().use{s->s.executeQuery("SELECT operation,operation_id FROM command_authority_operation").use{r->buildMap{while(r.next())put(r.getString(1),r.getObject(2,UUID::class.java))}}}}
        assertIs<AttestedAuthorityResult.AlreadyApplied>(composition.issuer.issuePrincipal(AttestedPrincipalRequest(orgId,manifestId,manifest,operations.getValue("PRINCIPAL"),principal)))
        assertIs<AttestedAuthorityResult.AlreadyApplied>(composition.issuer.bindInitialCredential(AttestedInitialCredentialRequest(orgId,manifestId,manifest,operations.getValue("INITIAL_CREDENTIAL"),principal,credential,verifier)))
        assertIs<AttestedAuthorityResult.AlreadyApplied>(composition.issuer.grantPermission(AttestedGrantRequest(orgId,manifestId,manifest,operations.getValue("GRANT"),principal,grant)))
        val reconciliation=PostgresOfflineFieldProofReconciler(runtimeDs()).reconcile(input)
        assertTrue(reconciliation.acceptedAttestationProven);assertTrue(reconciliation.consumptionLineageProven);assertTrue(reconciliation.exact)
        assertEquals(Delta(1,1,1,1,1,3,1,1),snapshot()-before)
    }

    @Test fun `mismatched target expired claim and invalid signature deny with zero effect`() {
        val before=snapshot();val manifest=manifest()
        listOf(target(manifest).copy(integrationReference="WRONG"),target(manifest).copy(organizationId=OrganizationId.parse(id(90).toString())),target(manifest).copy(reason="override")).forEach{candidate->
            val tty=RecordingTty();val lifecycle=Lifecycle();assertIs<AttestedCeremonyResult.Denied>(ceremony(composition(),tty,lifecycle).execute(sign(manifest),candidate,command(manifest),plan()));assertEquals(before,snapshot());assertEquals(0,tty.calls);assertEquals(0,lifecycle.created)
        }
        val expired=manifest.copy(approvalWindowStart=validFrom.minusSeconds(120),approvalWindowEnd=validFrom.minusSeconds(60));assertIs<AttestedCeremonyResult.Denied>(ceremony(composition(),RecordingTty(),Lifecycle()).execute(sign(expired),target(expired),command(expired),plan()));assertEquals(before,snapshot())
        val valid=sign(manifest);val changed=valid.signatureBytes().also{it[0]=(it[0].toInt() xor 1).toByte()};val invalid=SignedApprovalAttestation.parse(manifest,"Ed25519",valid.signerKeyId,valid.signerKeyFingerprint,Base64.getUrlEncoder().withoutPadding().encodeToString(changed))
        assertIs<AttestedCeremonyResult.Denied>(ceremony(composition(),RecordingTty(),Lifecycle()).execute(invalid,target(manifest),command(manifest),plan()));assertEquals(before,snapshot())
    }

    @Test fun `writer failure keeps committed authority history and no decision`() {
        val tty=RecordingTty();val lifecycle=Lifecycle();val composition=PostgresCeremonyComposition(verifierDs(),issuerDs(),runtimeDs()){_,_,_,_->assertEquals(1,lifecycle.destroyed);throw WriterFailure()}
        val failure=assertFailsWith<WriterFailure>{ceremony(composition,tty,lifecycle).execute(sign(manifest()),target(),command(),plan())}
        assertEquals("controlled writer failure without secret",failure.message);assertEquals(Delta(1,1,1,1,1,3,0,0),snapshot());assertEquals(1,lifecycle.destroyed);assertTrue(lifecycle.verifierCreationRejected)
    }

    @Test fun `issuer direct DML is denied and real composition is attested only`() {
        val failure=assertFailsWith<PSQLException>{issuerDs().connection.use{it.createStatement().executeUpdate("INSERT INTO command_principal VALUES ('$org','${id(99)}','$ml','$omie','x','x','${id(98)}',now())")}}
        assertEquals("42501",failure.sqlState);assertEquals(0,count("command_principal"));assertTrue(composition().issuer is AttestedCommandAuthorityIssuer)
    }

    @Test fun `read only reconciliation never repairs missing accepted artifact`() {
        val input=appliedInput()
        corrupt("DELETE FROM s2a_accepted_attestation")
        mismatchWithoutEffects(input, accepted=false)
    }

    @Test fun `read only reconciliation never repairs missing consumption`() {
        val input=appliedInput()
        corrupt("DELETE FROM s2a_attestation_consumption")
        mismatchWithoutEffects(input, consumed=false)
    }

    @Test fun `wrong consumption principal digest and correlation fail closed`() {
        val input=appliedInput()
        for (mutation in listOf("principal_id='${id(91)}'", "manifest_digest='${"0".repeat(64)}'", "correlation_id='${id(92)}'", "consumed_at=consumed_at + interval '1 second'")) {
            corrupt("UPDATE s2a_attestation_consumption SET $mutation")
            mismatchWithoutEffects(input, consumed=false)
            corrupt("UPDATE s2a_attestation_consumption SET principal_id='${input.plan.principalId.value}',manifest_digest='${ApprovalManifestCanonicalCodec.manifestDigest(ApprovalManifestCanonicalCodec.canonicalManifestBytes(input.attestation.manifest))}',correlation_id='${input.attestation.manifest.correlationId}',consumed_at=(SELECT decided_at FROM command_authority_operation WHERE operation='PRINCIPAL')")
        }
    }

    @Test fun `incomplete decision and head mismatched lineage and fingerprints fail closed`() {
        val input=appliedInput()
        corrupt("UPDATE marketplace_transaction_identity_head SET kind='REJECTED'")
        mismatchWithoutEffects(input)
        corrupt("DELETE FROM marketplace_transaction_identity_head")
        mismatchWithoutEffects(input)
    }

    @Test fun `corrupt accepted fingerprint and signer lineage fail closed without repair`() {
        val input=appliedInput()
        val original=value("SELECT accepted_proof_fingerprint FROM s2a_accepted_attestation")
        corrupt("UPDATE s2a_accepted_attestation SET accepted_proof_fingerprint='${"0".repeat(64)}'")
        mismatchWithoutEffects(input,accepted=false)
        corrupt("UPDATE s2a_accepted_attestation SET accepted_proof_fingerprint='$original',signer_key_lineage_fingerprint='${"0".repeat(64)}'")
        mismatchWithoutEffects(input,accepted=false)
    }

    @Test fun `duplicate accepted lineage fails closed`() {
        val input=appliedInput()
        update("ALTER TABLE s2a_accepted_attestation DROP CONSTRAINT s2a_accepted_attestation_pkey CASCADE")
        corrupt("INSERT INTO s2a_accepted_attestation SELECT * FROM s2a_accepted_attestation")
        mismatchWithoutEffects(input, accepted=false)
    }

    @Test fun `migration history rejects missing failed duplicated or inconsistent V042 despite capabilities`() {
        connection().use { assertTrue(PostgresOfflineMigrationHistory.provesV042(it)) }
        assertEquals(2,value("SELECT count(*) FROM pg_proc WHERE proname IN ('s2a_v042_begin_attested_decision_verification','s2a_v042_apply_attested_decision')").toInt())
        for (mutation in listOf("DELETE FROM flyway_schema_history WHERE version='042'",
            "UPDATE flyway_schema_history SET success=false WHERE version='042'",
            "UPDATE flyway_schema_history SET checksum=0 WHERE version='042'",
            "UPDATE flyway_schema_history SET version='041' WHERE version='042'")) {
            connection().use { c ->
                c.autoCommit=false
                c.createStatement().use { it.executeUpdate(mutation) }
                assertFalse(PostgresOfflineMigrationHistory.provesV042(c))
                c.rollback()
            }
        }
    }

    @Test fun `preflight rejects invalid history before authority despite existing capabilities`() {
        for ((login,role) in listOf("offline_verifier" to "flooow_attestation_verifier","offline_issuer" to "flooow_command_issuer","offline_runtime" to "flooow_command_runtime")) {
            update("CREATE ROLE $login LOGIN PASSWORD 'synthetic-only' INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS")
            update("GRANT $role TO $login")
        }
        fun config(login:String)=PostgresConfiguration(db.jdbcUrl,login,"synthetic-only")
        val configuration=OfflineDatabaseConfiguration(config("offline_verifier"),config("offline_issuer"),config("offline_runtime"))
        val boundary=PostgresOfflineFieldProofBoundaryVerifier(configuration,OfflineDataSources.create(configuration))
        val m=manifest();val input=OfflineFieldProofInput(sign(m),target(m),command(m),plan())
        assertTrue(boundary.verify(input))
        val before=snapshot()
        connection().use { c ->
            c.createStatement().use { it.execute("CREATE TEMP TABLE history_baseline AS TABLE flyway_schema_history") }
            for (mutation in listOf("DELETE FROM flyway_schema_history WHERE version='042'",
                "UPDATE flyway_schema_history SET success=false WHERE version='042'",
                "UPDATE flyway_schema_history SET checksum=0 WHERE version='042'")) {
                c.createStatement().use { it.executeUpdate(mutation) }
                assertFalse(boundary.verify(input))
                c.createStatement().use { it.executeUpdate("DELETE FROM flyway_schema_history");it.executeUpdate("INSERT INTO flyway_schema_history SELECT * FROM history_baseline") }
            }
        }
        assertEquals(before,snapshot())
    }

    @Test fun `wrong durable authority receipt and decision intent fail closed`() {
        val input=appliedInput()
        corrupt("UPDATE command_authority_operation SET receipt_fingerprint='${"0".repeat(64)}' WHERE operation='GRANT'")
        mismatchWithoutEffects(input)
        corrupt("UPDATE marketplace_transaction_identity_decision SET provenance='wrong-provenance'")
        mismatchWithoutEffects(input)
    }

    @Test fun `audit transaction is enforced read only by PostgreSQL`() {
        runtimeDs().connection.use { c ->
            c.isReadOnly=true;c.autoCommit=false
            assertEquals("on",c.createStatement().use { it.executeQuery("SHOW transaction_read_only").use { r -> r.next();r.getString(1) } })
            val failure=assertFailsWith<PSQLException> { c.createStatement().executeUpdate("INSERT INTO marketplace_transaction_identity_head SELECT * FROM marketplace_transaction_identity_head") }
            assertEquals("25006",failure.sqlState)
            c.rollback()
        }
    }

    @Test fun `durable principal prefix continues exact plan then complete restart creates no authority`() {
        val m=manifest();val input=OfflineFieldProofInput(sign(m),target(m),command(m),plan());val c=composition()
        assertIs<AcceptedAttestationResult.Accepted>(c.verifier.verify(input.attestation))
        assertIs<AttestedAuthorityResult.Applied>(c.issuer.issuePrincipal(AttestedPrincipalRequest(orgId,manifestId,m,input.plan.principalOperationId,input.plan.principalId)))
        val reconciler=PostgresOfflineFieldProofReconciler(runtimeDs())
        val prefix=reconciler.inspect(input)
        assertEquals(1,prefix.principalCount);assertEquals(1,prefix.authorityOperationCount)
        assertTrue(prefix.lineageMatches);assertFalse(prefix.hasCredentialEffect)
        val tty=RecordingTty();val lifecycle=Lifecycle()
        fun launcher(verifier:AcceptedAttestationVerifier)=OfflineFieldProofLauncher(verifier,c.issuer,c.runtime,tty,
            OfflineFieldProofBoundaryVerifier { true },reconciler,OfflineFieldProofOperatorConfirmation { true },
            Clock.fixed(validFrom,ZoneOffset.UTC),java.security.SecureRandom(),lifecycle)
        assertEquals(OfflineFieldProofOutcome.SUCCESS_RECONCILED,launcher(c.verifier).execute(input).outcome)
        val before=snapshot();val deliveries=tty.calls;val created=lifecycle.created
        assertEquals(OfflineFieldProofOutcome.ALREADY_APPLIED_RECONCILED,
            launcher(AcceptedAttestationVerifier { error("Replay must never call command verifier") }).execute(input).outcome)
        assertEquals(before,snapshot());assertEquals(deliveries,tty.calls);assertEquals(created,lifecycle.created)
    }

    private fun appliedInput(): OfflineFieldProofInput {
        val m=manifest();val input=OfflineFieldProofInput(sign(m),target(m),command(m),plan())
        assertIs<AttestedCeremonyResult.Applied>(ceremony(composition(),RecordingTty(),Lifecycle()).execute(input.attestation,input.target,input.command,input.plan))
        return input
    }

    private fun mismatchWithoutEffects(input:OfflineFieldProofInput,accepted:Boolean?=null,consumed:Boolean?=null) {
        val before=snapshot()
        val result=PostgresOfflineFieldProofReconciler(runtimeDs()).reconcile(input)
        assertFalse(result.exact)
        accepted?.let { assertEquals(it,result.acceptedAttestationProven) }
        consumed?.let { assertEquals(it,result.consumptionLineageProven) }
        assertEquals(before,snapshot())
    }

    // Corruption is injected exclusively into disposable synthetic fixtures by the test owner.
    private fun corrupt(sql:String)=connection().use { c ->
        c.createStatement().use { it.execute("SET session_replication_role=replica");it.executeUpdate(sql) }
    }

    private fun ceremony(c:PostgresCeremonyComposition,t:RecordingTty,l:Lifecycle)=ExecuteAttestedFieldProof(c.verifier,c.issuer,c.runtime,t,Clock.fixed(validFrom,ZoneOffset.UTC),java.security.SecureRandom(),l)
    private fun composition()=PostgresCeremonyComposition(verifierDs(),issuerDs(),runtimeDs())
    private fun verifierDs()=roleDs("flooow_attestation_verifier");private fun issuerDs()=roleDs("flooow_command_issuer");private fun runtimeDs()=roleDs("flooow_command_runtime")
    private fun target(m:ApprovalManifest=manifest())=FieldProofTarget(m.organizationId,m.mercadoLivreConnectionId,m.omieConnectionId,m.sourceOrderReference,m.integrationReference,m.marketplaceOrderId.value,m.reason,m.provenance,m.correlationId,CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE)
    private fun command(m:ApprovalManifest=manifest())=TransactionIdentityCommand(decision,m.sourceOrderReference,m.marketplaceOrderId.value,TransactionIdentityKind.CONFIRMED,ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION,m.provenance,m.correlationId)
    private fun plan()=OfflineFieldProofExecutionPlan(
        1,id(20),CommandPrincipalId(id(21)),id(22),id(23),id(24),id(25),id(26),decision
    )

    private fun auditReadGrants() {
        update("GRANT SELECT ON public.flyway_schema_history,public.s2a_accepted_attestation,public.s2a_attestation_consumption,public.s2a_signer_key_revision,public.s2a_signer_authority_revision,public.command_authority_operation TO flooow_command_runtime")
        for (identity in listOf(
            "public.s2a_v042_authority_intent(text,uuid,uuid,uuid,uuid,uuid,uuid,bytea,uuid,text,text,uuid,uuid,text,text)",
            "public.s2a_v042_authority_receipt(text,text,uuid,uuid,integer,uuid,integer,text,text)",
            "public.s2a_v042_text(text)","public.s2a_v042_frame(bytea)")) update("GRANT EXECUTE ON FUNCTION $identity TO flooow_command_runtime")
    }
    private fun seed(){val now=Timestamp.from(validFrom);update("INSERT INTO integration_organization VALUES (?,'ACTIVE',?,?)",org,now,now);update("INSERT INTO integration_connection VALUES (?,?,?,'OAUTH2_AUTHORIZATION_CODE','REVOKED',1,?,?)",org,ml,"br.com.mercadolivre",now,now);update("INSERT INTO integration_connection VALUES (?,?,?,'STATIC_API_CREDENTIAL','SUSPENDED',1,?,?)",org,omie,"omie",now,now)
        connection().use{c->c.autoCommit=false;page(c,ml,mlCap,1,2,1);execute(c,"INSERT INTO integration_mercado_livre_order_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,provider_status,date_created,date_last_updated,currency,total_amount,observed_at) VALUES (?,?,?,1,1,'MLB-123456789','paid',?,?,'BRL',58.28,?)",org,ml,mlCap,now,now,now);execute(c,"INSERT INTO marketplace_order_identity_registry VALUES (?,'mercado-livre','MLB-123456789',?,'BRL',?,?,?,?,1)",org,order,now,ml,mlCap,1L);execute(c,"INSERT INTO marketplace_order_occurrence_source_promotion VALUES (?,?,?,1,1,?,'PROMOTED',?)",org,ml,mlCap,order,now);page(c,omie,omieCap,1,2,2);omie(c,0,"OTHER-SYNTHETIC",null,"BRL",LocalDateTime.parse("2026-09-24T10:00:00.000000"),"cd".repeat(32),now);omie(c,1,"SO-2026-0001","MLB-123456789",null,LocalDateTime.parse("2026-09-25T11:59:59.123456"),"ab".repeat(32),now);c.commit()}
        val kd=SignerKeyRevision(orgId,SignerKeyId(key),1,GovernanceSubjectId(subject),SignerPublicKeyInfo.parse(spki.hex()),keyFp,SignerKeyState.ACTIVE,validFrom,validFrom,null,null,SignerKeyLineageFingerprint("0".repeat(64)),"Synthetic V041 key","ceremony-test",id(81));val k=kd.copy(lineageFingerprint=ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(kd));val governance=PostgresApprovalGovernance(roleDs("flooow_approval_governance"));assertIs<GovernanceAppendResult.Applied>(governance.appendSignerKeyRevision(k));val ad=SignerAuthorityRevision(orgId,SignerAuthorityId(authority),1,k.signerSubjectId,GovernanceInstitutionId(institution),SignerRole.S2A_FIELD_PROOF_APPROVER,k.signerKeyId,1,k.signerKeyFingerprint,ApprovalAction.S2A_FIELD_PROOF_APPROVAL,SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,validFrom,validUntil,SignerAuthorityState.ENABLED,null,null,SignerAuthorityFingerprint("0".repeat(64)),"Synthetic V041 authority","ceremony-test",GovernanceSourceId(source),id(82));assertIs<GovernanceAppendResult.Applied>(governance.appendSignerAuthorityRevision(ad.copy(signerAuthorityFingerprint=ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(ad))))}
    private fun manifest()=ApprovalManifest(1,manifestId,orgId,ml,omie,"SO-2026-0001","MLB-123456789",MarketplaceOrderId.parse(order.toString()),SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,GovernanceSubjectId(subject),GovernanceSourceId(source),validFrom,validUntil,GovernanceSubjectId(id(11)),GovernanceSubjectId(id(12)),CredentialDeliveryMethod.PROTECTED_TTY_ONE_TIME,GovernanceSubjectId(id(13)),ImmediateRevocationPolicy.SEPARATE_APPROVAL_REQUIRED,"S2A field proof approval","ceremony-attested-test",id(14),evidenceFingerprint())
    private fun sign(m:ApprovalManifest):SignedApprovalAttestation{val canonical=ApprovalManifestCanonicalCodec.canonicalManifestBytes(m);val preimage=ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes("Ed25519",SignerKeyId(key),keyFp,ApprovalManifestCanonicalCodec.manifestDigest(canonical));val privateKey=KeyFactory.getInstance("Ed25519").generatePrivate(PKCS8EncodedKeySpec((pkcs8+seedHex).hex()));val signature=Signature.getInstance("Ed25519").run{initSign(privateKey);update(preimage);sign()};return SignedApprovalAttestation.parse(m,"Ed25519",SignerKeyId(key),keyFp,Base64.getUrlEncoder().withoutPadding().encodeToString(signature))}
    private fun page(c:Connection,id:UUID,cap:String,input:Long,records:Int,marker:Int){execute(c,"INSERT INTO integration_connector_progress VALUES (?,?,?,?,?,false,?,?)",org,id,cap,input+1,byteArrayOf(marker.toByte()),Timestamp.from(validFrom),Timestamp.from(validFrom));execute(c,"INSERT INTO integration_connector_page_commit VALUES (?,?,?,?,?,?,false,?,?)",org,id,cap,input,ByteArray(32){marker.toByte()},records,Timestamp.from(validFrom),Timestamp.from(validFrom))}
    private fun omie(c:Connection,ordinal:Int,ref:String,integration:String?,currency:String?,revision:LocalDateTime,fingerprint:String,observed:Timestamp){execute(c,"INSERT INTO integration_omie_transaction_evidence (organization_id,connection_id,capability,input_progress_version,record_ordinal,source_order_ref,source_integration_ref,currency,total_amount,product_refs,observed_at,source_fingerprint) VALUES (?,?,?,1,?,?,?,?,58.28,'[]',?,?)",org,omie,omieCap,ordinal,ref,integration,currency,observed,"ef".repeat(32));execute(c,"INSERT INTO integration_omie_transaction_evidence_v3 (organization_id,connection_id,capability,input_progress_version,record_ordinal,provider_created_local,additional_order_totals,semantic_fingerprint_version,source_evidence_semantic_fingerprint) VALUES (?,?,?,1,?,?,'{}',1,?)",org,omie,omieCap,ordinal,revision,fingerprint)}
    private fun roleDs(role:String):DataSource{val base=PGSimpleDataSource().also{it.setURL(db.jdbcUrl);it.user=db.username;it.password=db.password};return object:DataSource{override fun getConnection()=base.connection.also{c->c.createStatement().use{it.execute("SET ROLE $role")}};override fun getConnection(u:String?,p:String?)=getConnection();override fun getLogWriter():PrintWriter?=base.logWriter;override fun setLogWriter(out:PrintWriter?){base.logWriter=out};override fun setLoginTimeout(s:Int){base.loginTimeout=s};override fun getLoginTimeout()=base.loginTimeout;override fun getParentLogger()=base.parentLogger;override fun <T:Any?> unwrap(i:Class<T>)=base.unwrap(i);override fun isWrapperFor(i:Class<*>)=base.isWrapperFor(i)}}
    private fun connection()=DriverManager.getConnection(db.jdbcUrl,db.username,db.password);private fun update(sql:String,vararg v:Any?)=connection().use{execute(it,sql,*v)};private fun execute(c:Connection,sql:String,vararg v:Any?)=c.prepareStatement(sql).use{s->v.forEachIndexed{i,x->s.setObject(i+1,x)};s.executeUpdate()}
    private fun value(sql:String)=connection().use{c->c.createStatement().use{s->s.executeQuery(sql).use{r->r.next();r.getString(1)}}};private fun count(t:String)=value("SELECT count(*) FROM $t").toInt();private fun uuidValue(sql:String)=connection().use{c->c.createStatement().use{s->s.executeQuery(sql).use{r->r.next();r.getObject(1,UUID::class.java)}}};private fun bytes(sql:String)=connection().use{c->c.createStatement().use{s->s.executeQuery(sql).use{r->r.next();r.getBytes(1)}}}
    private fun evidenceFingerprint()=value("SELECT public.s2a_v041_evidence_fingerprint('$org'::uuid,'$order'::uuid,'$ml'::uuid,'$omie'::uuid,'SO-2026-0001','MLB-123456789')")
    private fun snapshot()=Delta(count("s2a_accepted_attestation"),count("s2a_attestation_consumption"),count("command_principal"),count("command_credential_revision"),count("command_permission_grant"),count("command_authority_operation"),count("marketplace_transaction_identity_decision"),count("marketplace_transaction_identity_head"))
    private fun rawSecretOccurrences(token:String):Int{val encoded=token.substringAfterLast('.');val raw=Base64.getUrlDecoder().decode(encoded).joinToString(""){"%02x".format(it)};return listOf("command_principal","command_credential_revision","command_permission_grant","command_authority_operation","marketplace_transaction_identity_decision","marketplace_transaction_identity_head").sumOf{t->connection().use{c->c.prepareStatement("SELECT count(*) FROM $t row_value WHERE row_to_json(row_value)::text LIKE ? OR row_to_json(row_value)::text LIKE ? OR row_to_json(row_value)::text LIKE ?").use{s->s.setString(1,"%$token%");s.setString(2,"%$encoded%");s.setString(3,"%$raw%");s.executeQuery().use{r->r.next();r.getInt(1)}}}}}
    private fun id(n:Int)=UUID.fromString("71000000-0000-4000-8000-${n.toString().padStart(12,'0')}");private fun String.hex()=chunked(2).map{it.toInt(16).toByte()}.toByteArray()
    private data class Delta(val accepted:Int,val consumption:Int,val principal:Int,val credential:Int,val grant:Int,val authority:Int,val decision:Int,val head:Int){operator fun minus(b:Delta)=Delta(accepted-b.accepted,consumption-b.consumption,principal-b.principal,credential-b.credential,grant-b.grant,authority-b.authority,decision-b.decision,head-b.head)}
    private class RecordingTty:ProtectedTty{var calls=0;var token="";override fun isProtected()=true;override fun deliverOnce(t:CharArray){calls++;token=String(t);t.fill('\u0000')}};private class Lifecycle:CredentialLifecycleObserver{var created=0;var destroyed=0;var verifierCreationRejected=false;override fun created(){created++};override fun destroyed(v:Boolean){destroyed++;verifierCreationRejected=v}};private class WriterFailure:RuntimeException("controlled writer failure without secret")
    private val org=UUID.fromString("11111111-1111-4111-8111-111111111111");private val orgId=OrganizationId.parse(org.toString());private val key=UUID.fromString("22222222-2222-4222-8222-222222222222");private val subject=UUID.fromString("33333333-3333-4333-8333-333333333333");private val authority=UUID.fromString("44444444-4444-4444-8444-444444444441");private val institution=UUID.fromString("55555555-5555-4555-8555-555555555555");private val source=UUID.fromString("66666666-6666-4666-8666-666666666666");private val manifestId=UUID.fromString("77777777-7777-4777-8777-777777777777");private val ml=UUID.fromString("88888888-8888-4888-8888-888888888888");private val omie=UUID.fromString("99999999-9999-4999-8999-999999999999");private val order=UUID.fromString("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa");private val decision=UUID.fromString("18181818-1818-4181-8181-181818181818")
    private val keyFp=SignerKeyFingerprint("06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9");private val validFrom=Instant.parse("2026-09-25T12:00:00.000000Z");private val validUntil=Instant.parse("2026-10-25T12:00:00.000000Z");private val spki="302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a";private val pkcs8="302e020100300506032b657004220420";private val seedHex="9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60";private val mlCap="marketplace-economic.order-source";private val omieCap="marketplace-economic.omie-transaction-evidence.reacquisition-v3"
}
