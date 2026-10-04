package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.identity.*
import java.lang.reflect.Proxy
import java.nio.file.Files
import java.nio.file.Path
import java.security.KeyFactory
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.EdECPrivateKeySpec
import java.security.spec.NamedParameterSpec
import java.sql.Connection
import java.sql.PreparedStatement
import java.sql.ResultSet
import java.time.Instant
import java.time.LocalDateTime
import java.util.Base64
import java.util.UUID
import javax.sql.DataSource
import kotlin.test.*

/** Bounded recording JDBC; real retained canonical/JCA validation, no database or V043 execution. */
class GovernedAdaptersTest {
    private val root: Path = generateSequence(Path.of("").toAbsolutePath()) { it.parent }.first { Files.exists(it.resolve("AGENTS.md")) }
    private fun golden(file: String, stage: String, key: String = "output_hex"): ByteArray {
        val text = Files.readString(root.resolve("docs/evidence/$file"))
        val block = Regex("\"$stage\":\\s*\\{([^}]+)").find(text)!!.groupValues[1]
        return hex(Regex("\"$key\":\\s*\"([0-9a-f]+)\"").find(block)!!.groupValues[1])
    }
    private fun hex(s: String) = s.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    private fun id(n: Int) = UUID(0, n.toLong())
    private val now = Instant.parse("2026-09-30T12:00:00Z")
    private fun domain(s: String) = GovernedFrame.ROOT + s + "/V1"
    private fun encode(stage: String, declaration: String, values: Map<String, Any?>, nullable: Set<String> = emptySet()) = GovernedFrame.fields(declaration).let { fields -> GovernedFrame.encode(domain("$stage/OUTPUT"), fields, fields.associate { it.name to values[it.name] }, nullable) }

    @Test fun `all eighteen SQL vectors and names match independent SPEC`() {
        val spec = Files.readString(root.resolve("docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md"))
        val entries = Regex("\\*\\*(S\\d+)\\*\\* CALLER_SLOT=(\\w+).*?`public\\.(\\w+)\\(([^`]+)\\)`", RegexOption.DOT_MATCHES_ALL).findAll(spec).toList()
        assertEquals(18, entries.size)
        entries.forEach { entry ->
            val call = GovernedCall.valueOf(entry.groupValues[1])
            assertEquals(entry.groupValues[2], call.slot.name)
            assertEquals(entry.groupValues[4], call.parameters)
            val types = entry.groupValues[4].split(',').map { it.split(' ')[1] }
            assertEquals("SELECT * FROM public.${entry.groupValues[3]}(" + types.joinToString(",") { "?::$it" } + ")", call.sql)
        }
    }
    @Test fun `complete launcher uses every wrapper without legacy SQL and reconciles with real JCA`() {
        val fixture = Fixture()
        assertEquals("EFFECTS_COMPLETE_RECONCILIATION_REQUIRED", fixture.launcher().execute(fixture.input))
        assertEquals(listOf("S01", "S02", "S03", "S04", "S13", "S05", "S06", "S07", "S08", "S09", "S10", "S14", "S15", "S11", "S12", "S16", "S17", "S18", "S01", "S02", "S03", "S04"), fixture.calls.map { it.stage.name })
        assertEquals(1, fixture.deliveries)
        assertTrue(fixture.protectedBuffers.isNotEmpty() && fixture.protectedBuffers.all { buffer -> buffer.all { it == 0.toByte() } })
        val prepare = fixture.calls.single { it.stage == GovernedCall.S17 }
        val apply = fixture.calls.single { it.stage == GovernedCall.S18 }
        assertEquals(prepare.connection, apply.connection)
        assertContentEquals(fixture.preparation, apply.arguments.getValue("verified_decision_request") as ByteArray)
        assertEquals(fixture.fresh, fixture.calls.single { it.stage == GovernedCall.S14 }.arguments["fresh_applied_receipt_id"])
        assertTrue(fixture.transactions.filter { it.slot == GovernedSlot.AUDITOR }.all { it.isolation == Connection.TRANSACTION_REPEATABLE_READ && it.readOnly && it.rollbacks == 1 && it.commits == 0 })
        assertTrue(fixture.transactions.filter { it.slot != GovernedSlot.AUDITOR }.all { it.isolation == Connection.TRANSACTION_READ_COMMITTED && !it.readOnly && it.commits == 1 })
    }
    @Test fun `fresh receipt decoder accepts independent committed golden and replay stays null`() {
        val f = Fixture(); val launcher = f.launcher()
        val file = "PACKAGE-0090-S07-S18-TRANSPORT-GOLDENS.json"
        assertNotNull(launcher.freshReceipt(golden(file, "S10")).second)
        assertNull(launcher.freshReceipt(golden(file, "S10", "replay_output_hex")).second)
        assertFails { launcher.freshReceipt(golden(file, "S10") + byteArrayOf(0)) }
    }
    @Test fun `S10 replay cannot cause delivery or admission`() {
        val f = Fixture(); f.replay = true
        assertFails { f.launcher().execute(f.input) }
        assertEquals(0, f.deliveries)
        assertFalse(f.calls.any { it.stage in setOf(GovernedCall.S14, GovernedCall.S16) })
    }
    @Test fun `JCA tampering rolls back before APPLY`() {
        val f = Fixture(); f.tamperJca = true
        assertFails { f.launcher().execute(f.input) }
        assertFalse(f.calls.any { it.stage == GovernedCall.S06 })
        assertEquals(1, f.transactions.single { it.slot == GovernedSlot.VERIFIER }.rollbacks)
    }
    @Test fun `decision snapshot tampering rolls back on original connection`() {
        val f = Fixture(); f.tamperDecision = true
        assertFails { f.launcher().execute(f.input) }
        assertFalse(f.calls.any { it.stage == GovernedCall.S18 })
        assertEquals(1, f.transactions.last().rollbacks)
    }
    @Test fun `failure between preparation and APPLY cannot transfer connection`() {
        val f = Fixture()
        assertFails { f.sources.transaction(GovernedSlot.EXECUTOR) { it.decision(f.context + mapOf("admission_id" to id(700), "decision_request" to f.request)) { error("JCA_INTERRUPTED") } } }
        assertEquals(listOf(GovernedCall.S17), f.calls.map { it.stage })
        assertEquals(1, f.transactions.single().rollbacks)
        assertEquals(0, f.transactions.single().commits)
    }
    @Test fun `wrong slot rejected before prepared statement`() {
        val f = Fixture()
        assertFails { f.sources.transaction(GovernedSlot.AUDITOR) { it.call(GovernedCall.S05, f.context + ("envelope" to byteArrayOf(1))) } }
        assertTrue(f.calls.isEmpty())
    }
    @Test fun `foreign binding server denial rolls back without retry`() {
        val f = Fixture(); f.rejectBinding = true
        assertFails { f.launcher().execute(f.input) }
        assertEquals(1, f.calls.size)
        assertEquals(1, f.transactions.single().rollbacks)
    }
    @Test fun `null server transport rolls back`() {
        val f = Fixture(); f.nullResult = true
        assertFails { f.launcher().execute(f.input) }
        assertEquals(1, f.transactions.single().rollbacks)
        assertEquals(0, f.transactions.single().commits)
    }
    @Test fun `null opaque caller envelope never reaches executeQuery`() {
        val f = Fixture()
        assertFails { f.sources.transaction(GovernedSlot.VERIFIER) { it.call(GovernedCall.S05, f.context + ("envelope" to null)) } }
        assertTrue(f.calls.isEmpty())
        assertEquals(1, f.transactions.single().rollbacks)
    }
    @Test fun `malformed envelope and missing evidence never become readiness`() {
        val f = Fixture(); f.malformedResult = true
        assertFails { f.launcher().execute(f.input) }
        assertEquals(1, f.calls.size)
        assertEquals(0, f.deliveries)
    }
    @Test fun `ambiguous S14 commit permits no TTY attempt or retry`() {
        val f = Fixture(); f.failCommitStage = GovernedCall.S14
        assertFails { f.launcher().execute(f.input) }
        assertEquals(0, f.deliveries)
        assertEquals(1, f.calls.count { it.stage == GovernedCall.S14 })
    }
    @Test fun `TTY failure records failure once and never grants or writes`() {
        val f = Fixture(); f.failTty = true
        assertFails { f.launcher().execute(f.input) }
        assertEquals(1, f.deliveries)
        assertEquals("DELIVERY_FAILED_REVIEW_REQUIRED", f.calls.single { it.stage == GovernedCall.S15 }.arguments["delivery_outcome"])
        assertFalse(f.calls.any { it.stage == GovernedCall.S11 })
    }
    @Test fun `expired delivery window denies TTY`() {
        val f = Fixture(); f.expiredDelivery = true
        assertFails { f.launcher().execute(f.input) }
        assertEquals(0, f.deliveries)
    }
    @Test fun `duplicate slot pools denied`() {
        val f = Fixture(); val source = proxy<DataSource> { _, _ -> error("UNUSED") }
        assertFails { GovernedSources(GovernedSlot.entries.associateWith { source }) }
        assertTrue(f.calls.isEmpty())
    }
    @Test fun `closed transaction cannot export preparation authority`() {
        val f = Fixture(); lateinit var old: GovernedTransaction
        f.sources.transaction(GovernedSlot.EXECUTOR) { old = it }
        assertFails { old.call(GovernedCall.S17, f.context + mapOf("admission_id" to id(700), "decision_request" to f.request)) }
        assertTrue(f.calls.isEmpty())
    }
    @Test fun `preparation captured on one connection is denied on a second connection`() {
        val f = Fixture(); var captured = byteArrayOf()
        assertFails { f.sources.transaction(GovernedSlot.EXECUTOR) { tx -> tx.decision(f.context + mapOf("admission_id" to id(700), "decision_request" to f.request)) { captured = it; error("INTERRUPTED") } } }
        assertFails { f.sources.transaction(GovernedSlot.EXECUTOR) { tx -> tx.call(GovernedCall.S18, f.context + mapOf("admission_id" to id(700), "verified_decision_request" to captured)) } }
        assertEquals(listOf(GovernedCall.S17), f.calls.map { it.stage })
        assertEquals(2, f.transactions.size)
        assertTrue(f.transactions.all { it.commits == 0 && it.rollbacks == 1 })
    }
    @Test fun `canonical codec rejects null duplicate tags malformed lengths unicode and type shapes`() {
        val fields = GovernedFrame.fields("value text")
        val good = GovernedFrame.encode("test", fields, mapOf("value" to "á"))
        assertEquals("á", GovernedFrame.decode("test", fields, good)["value"])
        assertFails { GovernedFrame.encode("test", fields, mapOf("value" to "a\u0301")) }
        assertFails { GovernedFrame.encode("test", fields, mapOf("value" to null)) }
        for (length in good.indices) assertFails { GovernedFrame.decode("test", fields, good.copyOf(length)) }
        assertFails { GovernedFrame.decode("test", fields, good + byteArrayOf(0)) }
        val wrongTag = good.copyOf().also { it[11] = 2 }
        assertFails { GovernedFrame.decode("test", fields, wrongTag) }
    }
    @Test fun `protected derivation matches retained credential algorithm without intermediate verifier`() {
        val credential = CommandCredential.parse("fc1.${id(402)}." + Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(32) { 7 }))!!
        val expected = CommandCredentialVerifier.fromCredential(credential).persistenceBytes()
        val actual = GovernedCredentialProof.derive(credential)
        assertContentEquals(expected, actual)
        credential.destroy(); actual.fill(0); expected.fill(0)
        assertFails { GovernedCredentialProof.derive(credential) }
    }

    private data class Call(val stage: GovernedCall, val connection: Int, val arguments: Map<String, Any?>)
    private class Tx(val slot: GovernedSlot) { var isolation = 0; var readOnly = false; var commits = 0; var rollbacks = 0 }
    private inline fun <reified T> proxy(crossinline handler: (String, Array<out Any?>) -> Any?): T = Proxy.newProxyInstance(T::class.java.classLoader, arrayOf(T::class.java)) { p, method, args ->
        when (method.name) {
            "hashCode" -> System.identityHashCode(p)
            "equals" -> p === args?.get(0)
            "toString" -> "RecordingJdbc"
            else -> handler(method.name, args ?: emptyArray())
        }
    } as T

    private inner class Fixture {
        val calls = mutableListOf<Call>(); val transactions = mutableListOf<Tx>()
        val protectedBuffers = mutableListOf<ByteArray>()
        var replay = false; var tamperJca = false; var tamperDecision = false; var rejectBinding = false
        var nullResult = false; var malformedResult = false; var failTty = false; var expiredDelivery = false
        var failCommitStage: GovernedCall? = null; var deliveries = 0; var complete = false
        val fresh = id(710); val delivery = id(711)
        var preparation = byteArrayOf()
        val source05 = GovernedFrame.decode(domain("S05/INPUT"), GovernedTuples.S05_INPUT, golden("PACKAGE-0090-S05-S06-TRANSPORT-GOLDENS.json", "S05", "input_hex"))
        val baseManifest = ApprovalManifestCanonicalCodec.decodeCanonicalManifest(source05["p_canonical_manifest_bytes"] as ByteArray)
        val plan = OfflineFieldProofExecutionPlan(1, id(400), CommandPrincipalId(id(401)), id(402), id(403), id(404), id(405), id(406), id(407))
        val revision = LocalDateTime.parse("2026-09-30T12:00:00")
        val evidence = ApprovalEvidenceBindingCodec.Evidence(baseManifest.organizationId, baseManifest.marketplaceOrderId, baseManifest.mercadoLivreConnectionId, "marketplace-economic.order-source", 1, 0, "mercado-livre", baseManifest.integrationReference, "BRL", "PROMOTED", baseManifest.omieConnectionId, "marketplace-economic.omie-transaction-evidence.reacquisition-v3", 1, 0, baseManifest.sourceOrderReference, baseManifest.integrationReference, "BRL", 1, "1".repeat(64), revision)
        val manifest = baseManifest.copy(evidenceBindingFingerprint = ApprovalEvidenceBindingCodec.fingerprint(evidence))
        val keyDer = hex("302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        val key = SignerPublicKeyInfo.parse(keyDer)
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest)
        val digest = ApprovalManifestCanonicalCodec.manifestDigest(canonical)
        val preimage = ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes("Ed25519", SignerKeyId(id(101)), key.fingerprint(), digest)
        // Public RFC8032 TEST seed; never a deployment/private production key.
        val signature = Signature.getInstance("Ed25519").run {
            initSign(KeyFactory.getInstance("Ed25519").generatePrivate(EdECPrivateKeySpec(NamedParameterSpec.ED25519, hex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"))))
            update(preimage); sign()
        }
        val attestation = SignedApprovalAttestation.parse(manifest, "Ed25519", SignerKeyId(id(101)), key.fingerprint(), Base64.getUrlEncoder().withoutPadding().encodeToString(signature))
        val proof = AcceptedAttestationProof.create(1, 1, canonical, digest, preimage, "Ed25519", SignerKeyId(id(101)), 1, key.fingerprint(), SignerKeyLineageFingerprint("a".repeat(64)), keyDer, signature, SignerAuthorityId(id(201)), 1, SignerAuthorityFingerprint("b".repeat(64)), now)
        val snapshot: Map<String, Any?> = mapOf("artifact_version" to 1, "schema_version" to 1, "canonicalization_version" to 1, "canonical_manifest_bytes" to canonical, "manifest_digest" to digest, "signature_preimage_bytes" to preimage, "algorithm_id" to "Ed25519", "signer_subject_id" to id(300), "signer_key_id" to id(101), "signer_key_revision" to 1, "signer_key_fingerprint" to key.fingerprint().value, "signer_key_lineage_fingerprint" to "a".repeat(64), "subject_public_key_info_der" to keyDer, "signature_bytes" to signature, "signer_authority_id" to id(201), "signer_authority_revision" to 1, "signer_authority_fingerprint" to "b".repeat(64), "verified_at" to now, "accepted_proof_fingerprint" to AcceptedAttestationFingerprintCodec.fingerprint(proof), "signed_evidence_binding_fingerprint" to manifest.evidenceBindingFingerprint)
        val command = TransactionIdentityCommand(plan.decisionId, manifest.sourceOrderReference, manifest.marketplaceOrderId.value, TransactionIdentityKind.CONFIRMED, ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION, manifest.provenance, manifest.correlationId)
        val input = OfflineFieldProofInput(attestation, FieldProofTarget(manifest.organizationId, manifest.mercadoLivreConnectionId, manifest.omieConnectionId, manifest.sourceOrderReference, manifest.integrationReference, manifest.marketplaceOrderId.value, manifest.reason, manifest.provenance, manifest.correlationId), command, plan)
        val request = GovernedFrame.encode(domain("S17/INPUT"), GovernedFrame.fields("decision_id uuid,source_order_reference text,marketplace_order_id uuid,kind text,reason text,provenance text,correlation_id uuid,supersedes_decision_id uuid"), mapOf("decision_id" to command.decisionId, "source_order_reference" to command.sourceOrderReference, "marketplace_order_id" to command.marketplaceOrderId, "kind" to command.kind.name, "reason" to command.reason.name, "provenance" to command.provenance, "correlation_id" to command.correlationId, "supersedes_decision_id" to null), setOf("supersedes_decision_id"))
        val history = Regex("(\\d+) to \\(\"(V\\d+__[^\"]+\\.sql)\" to (-?\\d+)\\)").findAll(Files.readString(root.resolve("applications/command-authority-ceremony/src/main/kotlin/io/flooow/ceremony/PostgresOfflineMigrationHistory.kt"))).map { mapOf<String, Any?>("installed_rank" to it.groupValues[1].toInt(), "version" to it.groupValues[1], "type" to "SQL", "script" to it.groupValues[2], "checksum" to it.groupValues[3].toInt(), "success" to true) }.toList()
        val historyDigest = hex(Regex("\"history\":\\s*\\{.*?\"sha256\":\\s*\"([0-9a-f]+)\"", RegexOption.DOT_MATCHES_ALL).find(Files.readString(root.resolve("docs/evidence/PACKAGE-0090-G3F-3B-CATALOG-GOLDENS.json")))!!.groupValues[1])
        val deployment = GovernedDeployment(id(999), ByteArray(32) { 1 }, id(333), historyDigest, ByteArray(32) { 2 }, ByteArray(32) { 3 }, 1000)
        val context = deployment.scope() + mapOf("attempt_id" to id(600), "generation" to 1L, "execution_id" to id(601), "instance_id" to id(602), "possession_secret" to ByteArray(32) { 4 })
        val sources = GovernedSources(GovernedSlot.entries.associateWith { slot -> proxy<DataSource> { method, _ -> if (method == "getConnection") connection(slot) else null } })
        fun launcher() = GovernedOfflineFieldProofLauncher(deployment, sources, object : ProtectedTty {
            override fun isProtected() = true
            override fun deliverOnce(token: CharArray) { deliveries++; token.fill('\u0000'); if (failTty) error("TEST_IO_FAILURE") }
        }, OfflineFieldProofOperatorConfirmation { true })
        private fun connection(slot: GovernedSlot): Connection {
            val tx = Tx(slot); transactions.add(tx); val number = transactions.size
            return proxy { method, args -> when (method) {
                "setTransactionIsolation" -> { tx.isolation = args[0] as Int; null }
                "setReadOnly" -> { tx.readOnly = args[0] as Boolean; null }
                "commit" -> { if (calls.lastOrNull()?.stage == failCommitStage && failCommitStage != null) error("TEST_AMBIGUOUS_COMMIT"); tx.commits++; null }
                "rollback" -> { tx.rollbacks++; null }
                "prepareStatement" -> statement(args[0] as String, number, slot)
                else -> null
            } }
        }
        private fun statement(sql: String, number: Int, slot: GovernedSlot): PreparedStatement {
            val stage = GovernedCall.entries.single { it.sql == sql }
            assertEquals(slot, stage.slot)
            val bound = mutableMapOf<Int, Any?>()
            return proxy { method, args -> when {
                method.startsWith("set") -> {
                    val index = args[0] as Int
                    if (method == "setBytes" && ((stage in setOf(GovernedCall.S09, GovernedCall.S10) && index == stage.fields.size) || (stage == GovernedCall.S16 && stage.fields[index-1].name == "derived_credential_proof"))) protectedBuffers.add(args[1] as ByteArray)
                    bound[index] = when (val value = args[1]) { is ByteArray -> value.copyOf(); is java.sql.Timestamp -> value.toInstant(); else -> value }; null
                }
                method == "executeQuery" -> {
                    val values = stage.fields.mapIndexed { index, field -> field.name to bound.getValue(index + 1) }.toMap()
                    if (stage == GovernedCall.S17) assertTrue(protectedBuffers.all { buffer -> buffer.all { it == 0.toByte() } })
                    calls.add(Call(stage, number, values))
                    if (rejectBinding) error("TEST_BOUND_SCOPE_DENIED")
                    if (stage == GovernedCall.S04) rows(history.map { it.values.toList() })
                    else rows(listOf(listOf(if (nullResult) null else if (malformedResult) byteArrayOf(0) else response(stage, values))))
                }
                else -> null
            } }
        }
        private fun rows(values: List<List<Any?>>): ResultSet {
            var index = -1
            return proxy { method, args -> when (method) {
                "next" -> { index++; index < values.size }
                "getBytes", "getObject", "getString" -> values[index][(args[0] as Int) - 1]
                else -> null
            } }
        }
        private fun response(s: GovernedCall, a: Map<String, Any?>): ByteArray {
            fun emit(fields: List<GovernedField>, values: Map<String, Any?>, nullable: Set<String> = emptySet()) = GovernedFrame.encode(domain("${s.name}/OUTPUT"), fields, fields.associate { it.name to values[it.name] }, nullable)
            fun receipt(fields: List<GovernedField>, operation: UUID) = emit(fields, mapOf("outcome" to if (replay && s == GovernedCall.S10) "ALREADY_APPLIED" else "APPLIED", "result_operation_id" to operation, "result_intent_fingerprint" to "1".repeat(64), "result_receipt_fingerprint" to "2".repeat(64), "result_effect_time" to now))
            val counts = GovernedFrame.encode(domain("COUNTS"), (1..7).map { GovernedField("c$it", "int8") }, (1..7).associate { "c$it" to if (complete) listOf(1L,1L,1L,1L,1L,3L,1L)[it-1] else 0L })
            return when (s) {
                GovernedCall.S01 -> GovernedFrame.encode(domain("PREFLIGHT"), GovernedFrame.fields("incarnation uuid,binding bytea,surface text,history bytea,acl bytea,policy bytea,issued_at timestamptz,expires_at timestamptz,key_version u32"), mapOf("incarnation" to deployment.incarnationId, "binding" to a["plan_fingerprint"], "surface" to "0090-v1", "history" to historyDigest, "acl" to deployment.aclDigest, "policy" to deployment.policyDigest, "issued_at" to now, "expires_at" to now.plusSeconds(60), "key_version" to 1L)) + ByteArray(32)
                GovernedCall.S02 -> encode("S02", "binding_state text,attempt_state text,generation int8,execution_state text,delivery_state text,reconciliation_state text,ceremony_result text,domain_projection text,admission_state text,admission_effectively_valid bool,counts bytea", mapOf("binding_state" to "ACTIVE", "attempt_state" to null, "generation" to 1L, "execution_state" to null, "delivery_state" to "NOT_CREATED", "reconciliation_state" to "NOT_STARTED", "ceremony_result" to "NONE", "domain_projection" to if (complete) "DECISION_HEAD_PRESENT" else "EMPTY", "admission_state" to null, "admission_effectively_valid" to false, "counts" to counts), setOf("attempt_state", "execution_state", "admission_state"))
                GovernedCall.S03 -> reconciliation(counts)
                GovernedCall.S13 -> encode("S13", "attempt_id uuid,generation int8,execution_id uuid,instance_id uuid,claimed_at timestamptz,attempt_expires_at timestamptz,execution_expires_at timestamptz,claim_receipt_id uuid", mapOf("attempt_id" to id(600), "generation" to 1L, "execution_id" to a["execution_id"], "instance_id" to a["instance_id"], "claimed_at" to now, "attempt_expires_at" to now.plusSeconds(60), "execution_expires_at" to now.plusSeconds(60), "claim_receipt_id" to id(605)))
                GovernedCall.S05 -> {
                    val values = snapshot.mapKeys { "result_" + it.key }.toMutableMap()
                    values["outcome"] = "VERIFY_NEW"; values["result_recorded_at"] = now
                    values["result_canonical_signature_preimage_bytes"] = if (tamperJca) preimage + byteArrayOf(0) else preimage
                    emit(GovernedTuples.S05_OUTPUT, values)
                }
                GovernedCall.S06 -> emit(GovernedTuples.S06_OUTPUT, mapOf("outcome" to "ACCEPTED", "result_organization_id" to manifest.organizationId.value, "result_manifest_id" to manifest.manifestId, "result_manifest_digest" to digest, "result_accepted_proof_fingerprint" to snapshot["accepted_proof_fingerprint"], "result_verified_at" to now, "result_recorded_at" to now))
                GovernedCall.S07, GovernedCall.S09, GovernedCall.S11 -> {
                    val fields = when (s) { GovernedCall.S07 -> GovernedTuples.S07_OUTPUT; GovernedCall.S09 -> GovernedTuples.S09_OUTPUT; else -> GovernedTuples.S11_OUTPUT }
                    val values = snapshot.mapKeys { "result_" + it.key } + mapOf("outcome" to "READY", "result_operation_id" to when(s) { GovernedCall.S07 -> plan.principalOperationId; GovernedCall.S09 -> plan.initialCredentialOperationId; else -> plan.grantOperationId }, "result_intent_fingerprint" to "1".repeat(64))
                    emit(fields, values, fields.map { it.name }.toSet())
                }
                GovernedCall.S08 -> receipt(GovernedTuples.S08_OUTPUT, plan.principalOperationId)
                GovernedCall.S10 -> {
                    val frozen = receipt(GovernedTuples.S10_OUTPUT, plan.initialCredentialOperationId)
                    encode("S10", "frozen_receipt bytea,fresh_applied_receipt_id uuid,execution_id uuid,instance_id uuid,delivery_state text", mapOf("frozen_receipt" to frozen, "fresh_applied_receipt_id" to if (replay) null else fresh, "execution_id" to a["execution_id"], "instance_id" to a["instance_id"], "delivery_state" to "CREATED_NOT_DELIVERABLE"), setOf("fresh_applied_receipt_id"))
                }
                GovernedCall.S12 -> receipt(GovernedTuples.S12_OUTPUT, plan.grantOperationId)
                GovernedCall.S14 -> encode("S14", "delivery_receipt_id uuid,credential_id uuid,initial_operation_id uuid,fresh_applied_receipt_id uuid,execution_id uuid,instance_id uuid,attempted_at timestamptz,operation_deadline timestamptz,permission_to_attempt bool", a + mapOf("delivery_receipt_id" to delivery, "attempted_at" to now, "operation_deadline" to if (expiredDelivery) now else now.plusSeconds(60), "permission_to_attempt" to true))
                GovernedCall.S15 -> encode("S15", "delivery_receipt_id uuid,delivery_state text,observed_at timestamptz,observation_code text,recorded_at timestamptz", mapOf("delivery_receipt_id" to delivery, "delivery_state" to a["delivery_outcome"], "observed_at" to a["delivery_observed_at"], "observation_code" to a["delivery_observation_code"], "recorded_at" to now))
                GovernedCall.S16 -> encode("S16", "admission_id uuid,credential_revision int4,grant_id uuid,grant_revision int4,permission text,authenticated_at timestamptz,expires_at timestamptz,durable_state text", mapOf("admission_id" to id(700), "credential_revision" to 1, "grant_id" to plan.grantId, "grant_revision" to 1, "permission" to manifest.permission.name, "authenticated_at" to now, "expires_at" to now.plusSeconds(60), "durable_state" to "ISSUED"))
                GovernedCall.S17 -> {
                    val accepted = GovernedFrame.encode(domain("DECISION-ACCEPTED"), GovernedTuples.DECISION_ACCEPTED, snapshot + if (tamperDecision) mapOf("signature_bytes" to ByteArray(64)) else emptyMap())
                    encode("S17", "caller_request bytea,preparation_digest bytea,accepted_snapshot bytea", mapOf("caller_request" to a["decision_request"], "preparation_digest" to ByteArray(32), "accepted_snapshot" to accepted)).also { preparation = it }
                }
                GovernedCall.S18 -> { complete = true; emit(GovernedTuples.S18_OUTPUT, mapOf("outcome" to "APPLIED", "result_decision_id" to plan.decisionId, "result_decision_semantic_fingerprint" to "3".repeat(64), "result_decided_at" to now)) }
                else -> error("UNEXPECTED_STAGE")
            }
        }
        private fun hash(fields: List<String>): String = MessageDigest.getInstance("SHA-256").digest(fields.joinToString("") { "${it.toByteArray().size}:$it" }.toByteArray()).joinToString("") { "%02x".format(it) }
        private fun reconciliation(counts: ByteArray): ByteArray {
            val accepted = snapshot.filterKeys { it != "signer_subject_id" && it != "signed_evidence_binding_fingerprint" }.toMutableMap()
            accepted["canonical_signature_preimage_bytes"] = accepted.remove("signature_preimage_bytes")
            accepted += mapOf("organization_id" to manifest.organizationId.value, "manifest_id" to manifest.manifestId, "recorded_at" to now)
            val intent = hash(listOf("transaction-identity-intent/1", manifest.organizationId.value.toString(), plan.principalId.value.toString(), manifest.mercadoLivreConnectionId.toString(), manifest.omieConnectionId.toString(), command.sourceOrderReference, command.marketplaceOrderId.toString(), command.kind.name, command.reason.name, command.provenance, ""))
            val fingerprint = hash(listOf("transaction-identity/1", intent, manifest.mercadoLivreConnectionId.toString(), evidence.mlCapability, "1", "0", manifest.integrationReference, "BRL", evidence.omieCapability, "1", "1".repeat(64), "2026-09-30T12:00:00.000000", plan.grantId.toString(), "1", manifest.permission.name, "command-authorization/1", "4".repeat(64)))
            val d: Map<String, Any?> = mapOf("organization_id" to manifest.organizationId.value, "decision_id" to plan.decisionId, "omie_connection_id" to manifest.omieConnectionId, "source_order_reference" to command.sourceOrderReference, "marketplace_order_id" to command.marketplaceOrderId, "kind" to command.kind.name, "reason" to command.reason.name, "revision" to 1, "supersedes_decision_id" to null, "ml_connection_id" to manifest.mercadoLivreConnectionId, "ml_capability" to evidence.mlCapability, "ml_progress_version" to 1L, "ml_record_ordinal" to 0, "external_order_id" to manifest.integrationReference, "currency" to "BRL", "omie_capability" to evidence.omieCapability, "omie_progress_version" to 1L, "omie_record_ordinal" to 0, "omie_semantic_fingerprint" to "1".repeat(64), "provider_revision_local" to revision, "principal_id" to plan.principalId.value, "credential_id" to plan.credentialId, "credential_revision" to 1, "grant_id" to plan.grantId, "grant_revision" to 1, "permission" to manifest.permission.name, "authorization_semantic_version" to "command-authorization/1", "authorization_fingerprint" to "4".repeat(64), "intent_fingerprint" to intent, "decision_semantic_fingerprint" to fingerprint, "provenance" to command.provenance, "correlation_id" to command.correlationId, "decided_at" to now)
            val e = mapOf<String, Any?>("marketplace_key" to "mercado-livre", "promotion_outcome" to "PROMOTED", "source_integration_ref" to manifest.integrationReference, "omie_currency" to "BRL", "semantic_fingerprint_version" to 1, "source_evidence_semantic_fingerprint" to "1".repeat(64), "provider_revision_local" to revision)
            return encode("S03", "outcome text,counts bytea,authority_intent_matches bool,authority_receipt_matches bool,accepted_snapshot bytea,decision_snapshot bytea,evidence_snapshot bytea,head_matches bool,diagnostic_code text", mapOf("outcome" to if (complete) "EXACT" else "INDETERMINATE", "counts" to counts, "authority_intent_matches" to complete, "authority_receipt_matches" to complete, "accepted_snapshot" to if (complete) GovernedFrame.encode(domain("RECONCILE-ACCEPTED"), GovernedTuples.AUDIT_ACCEPTED, accepted) else null, "decision_snapshot" to if (complete) GovernedFrame.encode(domain("RECONCILE-DECISION"), GovernedTuples.AUDIT_DECISION, d, setOf("supersedes_decision_id", "provider_revision_local")) else null, "evidence_snapshot" to if (complete) GovernedFrame.encode(domain("RECONCILE-EVIDENCE"), GovernedFrame.fields("marketplace_key text,promotion_outcome text,source_integration_ref text,omie_currency text,semantic_fingerprint_version int4,source_evidence_semantic_fingerprint text,provider_revision_local timestamp without time zone"), e) else null, "head_matches" to complete, "diagnostic_code" to "TEST_ONLY"), setOf("accepted_snapshot", "decision_snapshot", "evidence_snapshot"))
        }
    }
}
