package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.identity.TransactionIdentityKind
import io.flooow.marketplace.operations.identity.ExplicitTransactionIdentityReason
import io.flooow.marketplace.persistence.postgres.PostgresConfiguration
import io.flooow.marketplace.persistence.postgres.PostgresDataSources
import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.file.Files
import java.nio.file.Path
import java.security.MessageDigest
import java.security.SecureRandom
import java.time.Instant
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import java.util.Base64
import java.util.UUID

/** Client expectations are independently approved deployment input, never runtime-derived authority. */
internal class GovernedDeployment(
    val bindingId: UUID, fingerprint: ByteArray, val incarnationId: UUID,
    historyDigest: ByteArray, aclDigest: ByteArray, policyDigest: ByteArray,
    val deliverySafetyMarginMicros: Long
) {
    private val fingerprint = fingerprint.copyOf()
    val historyDigest = historyDigest.copyOf()
    val aclDigest = aclDigest.copyOf()
    val policyDigest = policyDigest.copyOf()
    init {
        require(bindingId != UUID(0, 0) && incarnationId != UUID(0, 0))
        require(listOf(fingerprint, historyDigest, aclDigest, policyDigest).all { it.size == 32 })
        require(deliverySafetyMarginMicros > 0)
    }
    fun scope(): Map<String, Any?> = linkedMapOf("binding_id" to bindingId, "plan_fingerprint" to fingerprint.copyOf(), "expected_incarnation_id" to incarnationId, "surface_version" to "0090-v1")
    companion object {
        fun environment(environment: Map<String, String>): Pair<GovernedDeployment, GovernedSources> {
            fun required(name: String) = requireNotNull(environment["FLOOOW_$name"]) { "DEPLOYMENT_CONFIGURATION_MISSING" }
            fun digest(name: String): ByteArray {
                val value = required(name)
                require(Regex("[0-9a-f]{64}").matches(value))
                return value.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
            }
            val policy = Files.readAllBytes(Path.of(required("OFFLINE_POLICY_PATH")))
            val policyDigest = digest("OFFLINE_POLICY_DIGEST")
            require(MessageDigest.getInstance("SHA-256").digest(policy).contentEquals(policyDigest))
            val names = listOf("TRANSACTION_TIMEOUT", "STATEMENT_TIMEOUT", "IDLE_IN_TRANSACTION_TIMEOUT", "LOCK_TIMEOUT", "ATTEMPT_VALIDITY", "EXECUTION_VALIDITY", "BINDING_VALIDITY", "ADMISSION_VALIDITY", "DELIVERY_OPERATION_WINDOW", "READ_TRANSACTION_TIMEOUT", "WATCHDOG_ENFORCEMENT_INTERVAL", "WATCHDOG_HEALTH_MAX_AGE", "DELIVERY_LOCAL_SAFETY_MARGIN", "PREFLIGHT_RECEIPT_TTL")
            val fields = listOf(GovernedField("policy_version", "text")) + names.flatMap { listOf(GovernedField(it, "int8"), GovernedField(it + "_MAX", "int8")) }
            val decoded = GovernedFrame.decode(GovernedFrame.ROOT + "DEADLINE-POLICY/V1", fields, policy)
            names.forEach { require(decoded[it] as Long > 0 && decoded[it] as Long <= decoded[it + "_MAX"] as Long) }
            require((decoded["DELIVERY_LOCAL_SAFETY_MARGIN"] as Long) < (decoded["DELIVERY_OPERATION_WINDOW"] as Long))
            val configs = GovernedSlot.entries.associateWith { slot ->
                PostgresConfiguration(required("${slot.name}_DATABASE_URL"), required("${slot.name}_DATABASE_USER"), required("${slot.name}_DATABASE_PASSWORD"))
            }
            require(configs.values.map { it.user }.toSet().size == 4) { "SLOT_LOGIN_REUSE" }
            require(configs.values.map { it.url }.toSet().size == 1) { "SLOT_ENDPOINT_MISMATCH" }
            return GovernedDeployment(UUID.fromString(required("OFFLINE_BINDING_ID")), digest("OFFLINE_PLAN_FINGERPRINT"), UUID.fromString(required("OFFLINE_INCARNATION_ID")), digest("OFFLINE_HISTORY_DIGEST"), digest("OFFLINE_ACL_DIGEST"), policyDigest, decoded["DELIVERY_LOCAL_SAFETY_MARGIN"] as Long) to
                GovernedSources(configs.mapValues { PostgresDataSources.create(it.value) })
        }
    }
}

internal class GovernedOfflineFieldProofLauncher(
    private val deployment: GovernedDeployment,
    private val sources: GovernedSources,
    private val tty: ProtectedTty,
    private val confirmation: OfflineFieldProofOperatorConfirmation,
    private val random: SecureRandom = SecureRandom()
) {
    private fun domain(stage: GovernedCall, direction: String) = GovernedFrame.ROOT + "${stage.name}/$direction/V1"
    private fun decode(stage: GovernedCall, fields: List<GovernedField>, bytes: ByteArray, nullable: Set<String> = emptySet()) = GovernedFrame.decode(domain(stage, "OUTPUT"), fields, bytes, nullable)
    private fun run(stage: GovernedCall, args: Map<String, Any?>): ByteArray = sources.transaction(stage.slot) { it.call(stage, args) }

    fun execute(input: OfflineFieldProofInput): String {
        require(tty.isProtected()) { "SECURE_TTY_UNAVAILABLE" }
        requireEligible(input)
        val initial = audit(input)
        if (initial.exact) return "EFFECTS_COMPLETE_RECONCILIATION_REQUIRED"
        require(initial.empty) { "EXISTING_EFFECTS_REQUIRE_INSPECTION" }
        require(confirmation.authorize(input)) { "OPERATOR_DENIED" }
        val secret = ByteArray(32).also(random::nextBytes)
        val executionId = UUID.randomUUID()
        val instanceId = UUID.randomUUID()
        try {
            val claim = decode(GovernedCall.S13, GovernedFrame.fields("attempt_id uuid,generation int8,execution_id uuid,instance_id uuid,claimed_at timestamptz,attempt_expires_at timestamptz,execution_expires_at timestamptz,claim_receipt_id uuid"), run(GovernedCall.S13, deployment.scope() + mapOf("expected_generation" to initial.generation, "execution_id" to executionId, "instance_id" to instanceId, "possession_secret" to secret, "preflight_receipt" to initial.preflight)))
            require(claim["execution_id"] == executionId && claim["instance_id"] == instanceId && claim["generation"] == initial.generation)
            require(claim["attempt_expires_at"] as Instant > claim["claimed_at"] as Instant && claim["execution_expires_at"] as Instant > claim["claimed_at"] as Instant)
            val context = deployment.scope() + mapOf("attempt_id" to claim.getValue("attempt_id"), "generation" to claim.getValue("generation"), "execution_id" to executionId, "instance_id" to instanceId, "possession_secret" to secret)
            val manifest = manifestValues(input)
            verify(input, context, manifest)
            issue(input, context, manifest, GovernedCall.S07, GovernedCall.S08, GovernedTuples.S07_INPUT, GovernedTuples.S07_OUTPUT, GovernedTuples.S08_INPUT, GovernedTuples.S08_OUTPUT, mapOf("p_operation_id" to input.plan.principalOperationId, "p_principal_id" to input.plan.principalId.value))
            val raw = ByteArray(32).also(random::nextBytes)
            val token = ("fc1.${input.plan.credentialId}." + Base64.getUrlEncoder().withoutPadding().encodeToString(raw)).toCharArray()
            raw.fill(0)
            val credential = requireNotNull(CommandCredential.parse(String(token)))
            val derived = GovernedCredentialProof.derive(credential)
            try {
                val applied = issue(input, context, manifest, GovernedCall.S09, GovernedCall.S10, GovernedTuples.S09_INPUT, GovernedTuples.S09_OUTPUT, GovernedTuples.S10_INPUT, GovernedTuples.S10_OUTPUT, mapOf("p_operation_id" to input.plan.initialCredentialOperationId, "p_principal_id" to input.plan.principalId.value, "p_credential_id" to input.plan.credentialId, "p_secret_verifier" to derived))
                deliver(input, context, applied, token)
                issue(input, context, manifest, GovernedCall.S11, GovernedCall.S12, GovernedTuples.S11_INPUT, GovernedTuples.S11_OUTPUT, GovernedTuples.S12_INPUT, GovernedTuples.S12_OUTPUT, mapOf("p_operation_id" to input.plan.grantOperationId, "p_principal_id" to input.plan.principalId.value, "p_grant_id" to input.plan.grantId))
                val admission = decode(GovernedCall.S16, GovernedFrame.fields("admission_id uuid,credential_revision int4,grant_id uuid,grant_revision int4,permission text,authenticated_at timestamptz,expires_at timestamptz,durable_state text"), run(GovernedCall.S16, context + mapOf("credential_id" to input.plan.credentialId, "credential_revision" to 1, "derived_credential_proof" to derived)))
                require(admission["durable_state"] == "ISSUED" && admission["credential_revision"] == 1 && admission["grant_revision"] == 1 && admission["grant_id"] == input.plan.grantId && admission["permission"] == input.attestation.manifest.permission.name)
                require(admission["expires_at"] as Instant > admission["authenticated_at"] as Instant)
                credential.destroy(); derived.fill(0); token.fill('\u0000')
                write(input, AdmissionHandle(admission.getValue("admission_id") as UUID, context))
            } finally { credential.destroy(); derived.fill(0); token.fill('\u0000') }
            require(audit(input).exact) { "POST_WRITE_RECONCILIATION_UNPROVEN" }
            return "EFFECTS_COMPLETE_RECONCILIATION_REQUIRED"
        } finally { secret.fill(0) }
    }

    private fun requireEligible(input: OfflineFieldProofInput) {
        val m = input.attestation.manifest; val t = input.target; val c = input.command
        require(t.valid() && t.organizationId == m.organizationId && t.mercadoLivreConnectionId == m.mercadoLivreConnectionId && t.omieConnectionId == m.omieConnectionId && t.sourceOrderReference == m.sourceOrderReference && t.integrationReference == m.integrationReference && t.marketplaceOrderId == m.marketplaceOrderId.value && t.permission.name == m.permission.name && t.reason == m.reason && t.provenance == m.provenance && t.correlationId == m.correlationId)
        require(c.decisionId == input.plan.decisionId && c.sourceOrderReference == m.sourceOrderReference && c.marketplaceOrderId == m.marketplaceOrderId.value && c.provenance == m.provenance && c.correlationId == m.correlationId && c.kind == TransactionIdentityKind.CONFIRMED && c.reason == ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION && c.supersedesDecisionId == null)
    }
    private fun manifestValues(input: OfflineFieldProofInput): Map<String, Any?> {
        val m = input.attestation.manifest
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(m)
        return linkedMapOf(
            "p_schema_version" to m.schemaVersion, "p_manifest_id" to m.manifestId, "p_organization_id" to m.organizationId.value,
            "p_mercado_livre_connection_id" to m.mercadoLivreConnectionId, "p_omie_connection_id" to m.omieConnectionId,
            "p_source_order_reference" to m.sourceOrderReference, "p_integration_reference" to m.integrationReference,
            "p_marketplace_order_id" to m.marketplaceOrderId.value, "p_permission" to m.permission.name,
            "p_accountable_operator" to m.accountableOperator.value, "p_approval_source" to m.approvalSource.value,
            "p_approval_window_start" to m.approvalWindowStart, "p_approval_window_end" to m.approvalWindowEnd,
            "p_revocation_owner" to m.revocationOwner.value, "p_credential_custodian" to m.credentialCustodian.value,
            "p_credential_delivery_method" to m.credentialDeliveryMethod.name, "p_credential_rotation_owner" to m.credentialRotationOwner.value,
            "p_immediate_revocation_policy" to m.immediateRevocationPolicy.name, "p_reason" to m.reason,
            "p_provenance" to m.provenance, "p_correlation_id" to m.correlationId, "p_evidence_binding_fingerprint" to m.evidenceBindingFingerprint,
            "p_claim_manifest_id" to m.manifestId, "p_claim_organization_id" to m.organizationId.value,
            "p_canonicalization_version" to ApprovalManifestCanonicalCodec.CANONICALIZATION_VERSION, "p_canonical_manifest_bytes" to canonical,
            "p_manifest_digest" to ApprovalManifestCanonicalCodec.manifestDigest(canonical), "p_algorithm_id" to input.attestation.algorithmId,
            "p_signer_key_id" to input.attestation.signerKeyId.value, "p_signer_key_fingerprint" to input.attestation.signerKeyFingerprint.value, "p_signature_bytes" to input.attestation.signatureBytes()
        )
    }
    private fun request(stage: GovernedCall, fields: List<GovernedField>, values: Map<String, Any?>) = GovernedFrame.encode(domain(stage, "INPUT"), fields, fields.associate { it.name to values.getValue(it.name) })
    private fun verify(input: OfflineFieldProofInput, context: Map<String, Any?>, values: Map<String, Any?>) = sources.transaction(GovernedSlot.VERIFIER) { tx ->
        val begin = decode(GovernedCall.S05, GovernedTuples.S05_OUTPUT, tx.call(GovernedCall.S05, context + ("envelope" to request(GovernedCall.S05, GovernedTuples.S05_INPUT, values))), setOf("result_recorded_at"))
        require(begin["outcome"] in setOf("VERIFY_NEW", "VERIFY_REPLAY")) { "VERIFICATION_BEGIN_DENIED" }
        GovernedAttestation.fromBegin(GovernedCall.S05, begin, input.attestation)
        val expected = GovernedTuples.S06_INPUT.filter { it.name.startsWith("p_expected_") }.associate { it.name to begin.getValue("result_" + it.name.removePrefix("p_expected_")) }
        val persisted = decode(GovernedCall.S06, GovernedTuples.S06_OUTPUT, tx.call(GovernedCall.S06, context + ("verified_envelope" to request(GovernedCall.S06, GovernedTuples.S06_INPUT, values + expected))))
        require(persisted["outcome"] in setOf("ACCEPTED", "ALREADY_ACCEPTED") && persisted["result_organization_id"] == input.attestation.manifest.organizationId.value && persisted["result_manifest_id"] == input.attestation.manifest.manifestId)
    }
    private fun issue(input: OfflineFieldProofInput, context: Map<String, Any?>, values: Map<String, Any?>, beginCall: GovernedCall, applyCall: GovernedCall, beginFields: List<GovernedField>, outputFields: List<GovernedField>, applyFields: List<GovernedField>, resultFields: List<GovernedField>, operation: Map<String, Any?>): ByteArray = sources.transaction(GovernedSlot.ISSUER) { tx ->
        val payload = values + operation
        val beginRequest = request(beginCall, beginFields, payload)
        val begin = try {
            decode(beginCall, outputFields, tx.call(beginCall, context + (beginCall.fields.last().name to beginRequest)), outputFields.map { it.name }.toSet())
        } finally { beginRequest.fill(0) }
        require(begin["outcome"] in setOf("READY", "ALREADY_APPLIED")) { "ISSUANCE_BEGIN_DENIED" }
        val snapshot = GovernedAttestation.fromBegin(beginCall, begin, input.attestation)
        val expected = applyFields.filter { it.name.startsWith("p_expected_") }.associate { field ->
            val name = field.name.removePrefix("p_expected_").let { if (it == "evidence_binding_fingerprint") "signed_evidence_binding_fingerprint" else it }
            field.name to snapshot.getValue(name)
        }
        val applyRequest = request(applyCall, applyFields, payload + expected)
        val result = try { tx.call(applyCall, context + (applyCall.fields.last().name to applyRequest)) }
        finally { applyRequest.fill(0) }
        val receipt = if (applyCall == GovernedCall.S10) freshReceipt(result).first else result
        val decoded = decode(applyCall, resultFields, receipt)
        require(decoded["outcome"] in setOf("APPLIED", "ALREADY_APPLIED") && decoded["result_operation_id"] == operation["p_operation_id"])
        result
    }
    internal fun freshReceipt(bytes: ByteArray): Pair<ByteArray, UUID?> {
        val frame = decode(GovernedCall.S10, GovernedFrame.fields("frozen_receipt bytea,fresh_applied_receipt_id uuid,execution_id uuid,instance_id uuid,delivery_state text"), bytes, setOf("fresh_applied_receipt_id"))
        val receipt = frame.getValue("frozen_receipt") as ByteArray
        val frozen = decode(GovernedCall.S10, GovernedTuples.S10_OUTPUT, receipt)
        val fresh = frame["fresh_applied_receipt_id"] as UUID?
        require((frozen["outcome"] == "APPLIED" && fresh != null && frame["delivery_state"] == "CREATED_NOT_DELIVERABLE") || (frozen["outcome"] == "ALREADY_APPLIED" && fresh == null)) { "FRESH_RECEIPT_DENIED" }
        return receipt to fresh
    }
    private fun deliver(input: OfflineFieldProofInput, context: Map<String, Any?>, bytes: ByteArray, token: CharArray) {
        val (_, fresh) = freshReceipt(bytes)
        requireNotNull(fresh) { "REPLAY_HAS_NO_DELIVERY_PERMISSION" }
        val outer = decode(GovernedCall.S10, GovernedFrame.fields("frozen_receipt bytea,fresh_applied_receipt_id uuid,execution_id uuid,instance_id uuid,delivery_state text"), bytes, setOf("fresh_applied_receipt_id"))
        require(outer["execution_id"] == context["execution_id"] && outer["instance_id"] == context["instance_id"])
        val start = System.nanoTime()
        val delivery = decode(GovernedCall.S14, GovernedFrame.fields("delivery_receipt_id uuid,credential_id uuid,initial_operation_id uuid,fresh_applied_receipt_id uuid,execution_id uuid,instance_id uuid,attempted_at timestamptz,operation_deadline timestamptz,permission_to_attempt bool"), run(GovernedCall.S14, context + mapOf("credential_id" to input.plan.credentialId, "initial_operation_id" to input.plan.initialCredentialOperationId, "fresh_applied_receipt_id" to fresh)))
        require(delivery["permission_to_attempt"] == true && delivery["credential_id"] == input.plan.credentialId && delivery["initial_operation_id"] == input.plan.initialCredentialOperationId && delivery["fresh_applied_receipt_id"] == fresh && delivery["execution_id"] == context["execution_id"] && delivery["instance_id"] == context["instance_id"])
        val window = ChronoUnit.MICROS.between(delivery["attempted_at"] as Instant, delivery["operation_deadline"] as Instant)
        require(window > deployment.deliverySafetyMarginMicros && (System.nanoTime() - start) / 1000 < window - deployment.deliverySafetyMarginMicros) { "DELIVERY_WINDOW_CLOSED" }
        var acknowledged = false
        val delivered = token.copyOf()
        try { tty.deliverOnce(delivered); acknowledged = true }
        finally {
            delivered.fill('\u0000')
            val report = decode(GovernedCall.S15, GovernedFrame.fields("delivery_receipt_id uuid,delivery_state text,observed_at timestamptz,observation_code text,recorded_at timestamptz"), run(GovernedCall.S15, context + mapOf("delivery_receipt_id" to delivery.getValue("delivery_receipt_id"), "delivery_outcome" to if (acknowledged) "DELIVERY_ACKNOWLEDGED" else "DELIVERY_FAILED_REVIEW_REQUIRED", "delivery_observed_at" to Instant.now().truncatedTo(ChronoUnit.MICROS), "delivery_observation_code" to if (acknowledged) "COMPLETE" else "IO_FAILURE")))
            require(report["delivery_receipt_id"] == delivery["delivery_receipt_id"] && report["delivery_state"] == if (acknowledged) "DELIVERY_ACKNOWLEDGED" else "DELIVERY_FAILED_REVIEW_REQUIRED")
        }
    }
    private class AdmissionHandle(val id: UUID, val context: Map<String, Any?>)
    private fun write(input: OfflineFieldProofInput, admission: AdmissionHandle) {
        val c = input.command
        val fields = GovernedFrame.fields("decision_id uuid,source_order_reference text,marketplace_order_id uuid,kind text,reason text,provenance text,correlation_id uuid,supersedes_decision_id uuid")
        val request = GovernedFrame.encode(domain(GovernedCall.S17, "INPUT"), fields, mapOf("decision_id" to c.decisionId, "source_order_reference" to c.sourceOrderReference, "marketplace_order_id" to c.marketplaceOrderId, "kind" to c.kind.name, "reason" to c.reason.name, "provenance" to c.provenance, "correlation_id" to c.correlationId, "supersedes_decision_id" to c.supersedesDecisionId), setOf("supersedes_decision_id"))
        sources.transaction(GovernedSlot.EXECUTOR) { tx ->
            val result = tx.decision(admission.context + mapOf("admission_id" to admission.id, "decision_request" to request)) { bytes ->
                val envelope = decode(GovernedCall.S17, GovernedFrame.fields("caller_request bytea,preparation_digest bytea,accepted_snapshot bytea"), bytes)
                require((envelope["caller_request"] as ByteArray).contentEquals(request) && (envelope["preparation_digest"] as ByteArray).size == 32)
                GovernedAttestation.verify(input.attestation, GovernedFrame.decode(GovernedFrame.ROOT + "DECISION-ACCEPTED/V1", GovernedTuples.DECISION_ACCEPTED, envelope["accepted_snapshot"] as ByteArray))
            }
            val receipt = decode(GovernedCall.S18, GovernedTuples.S18_OUTPUT, result)
            require(receipt["outcome"] == "APPLIED" && receipt["result_decision_id"] == c.decisionId)
        }
    }
    private class Audit(val preflight: ByteArray, val generation: Long, val empty: Boolean, val exact: Boolean)
    private fun audit(input: OfflineFieldProofInput): Audit = sources.transaction(GovernedSlot.AUDITOR) { tx ->
        val scope = deployment.scope()
        val preflight = tx.call(GovernedCall.S01, scope + mapOf("expected_history_digest" to deployment.historyDigest, "expected_acl_digest" to deployment.aclDigest, "expected_policy_digest" to deployment.policyDigest))
        require(preflight.size > 32)
        val receipt = GovernedFrame.decode(GovernedFrame.ROOT + "PREFLIGHT/V1", GovernedFrame.fields("incarnation uuid,binding bytea,surface text,history bytea,acl bytea,policy bytea,issued_at timestamptz,expires_at timestamptz,key_version u32"), preflight.copyOfRange(0, preflight.size - 32))
        require(receipt["incarnation"] == deployment.incarnationId && receipt["surface"] == "0090-v1" && (receipt["binding"] as ByteArray).contentEquals(scope["plan_fingerprint"] as ByteArray) && (receipt["history"] as ByteArray).contentEquals(deployment.historyDigest) && (receipt["acl"] as ByteArray).contentEquals(deployment.aclDigest) && (receipt["policy"] as ByteArray).contentEquals(deployment.policyDigest) && receipt["expires_at"] as Instant > receipt["issued_at"] as Instant)
        val inspect = decode(GovernedCall.S02, GovernedFrame.fields("binding_state text,attempt_state text,generation int8,execution_state text,delivery_state text,reconciliation_state text,ceremony_result text,domain_projection text,admission_state text,admission_effectively_valid bool,counts bytea"), tx.call(GovernedCall.S02, scope), setOf("attempt_state", "execution_state", "admission_state"))
        val reconcile = decode(GovernedCall.S03, GovernedFrame.fields("outcome text,counts bytea,authority_intent_matches bool,authority_receipt_matches bool,accepted_snapshot bytea,decision_snapshot bytea,evidence_snapshot bytea,head_matches bool,diagnostic_code text"), tx.call(GovernedCall.S03, scope), setOf("accepted_snapshot", "decision_snapshot", "evidence_snapshot"))
        val history = tx.history(scope)
        val historyFields = GovernedFrame.fields("installed_rank int4,version text,type text,script text,checksum int4,success bool")
        require(history.isNotEmpty() && history.all { it["installed_rank"] is Int && it["version"] != null && it["checksum"] != null && it["success"] == true }) { "HISTORY_INCOMPLETE" }
        val ranks = history.map { it["installed_rank"] as Int }
        require(ranks == ranks.sorted() && ranks.distinct().size == ranks.size && ranks.all { it > 0 })
        val collection = ByteArrayOutputStream()
        DataOutputStream(collection).use { out ->
            out.writeInt(history.size)
            history.forEach { row -> val bytes = GovernedFrame.encode(GovernedFrame.ROOT + "HISTORY-ROW/V1", historyFields, row, setOf("version", "checksum")); out.writeInt(bytes.size); out.write(bytes) }
        }
        val historyFrame = GovernedFrame.encode(GovernedFrame.ROOT + "HISTORY/V1", listOf(GovernedField("rows", "bytea")), mapOf("rows" to collection.toByteArray()))
        require(MessageDigest.getInstance("SHA-256").digest(historyFrame).contentEquals(deployment.historyDigest)) { "HISTORY_DIGEST_MISMATCH" }
        val countsFields = (1..7).map { GovernedField("count$it", "int8") }
        val counts = GovernedFrame.decode(GovernedFrame.ROOT + "COUNTS/V1", countsFields, inspect["counts"] as ByteArray).values.map { it as Long }
        require(counts.all { it >= 0 } && inspect["generation"] as Long > 0)
        val reconCounts = GovernedFrame.decode(GovernedFrame.ROOT + "COUNTS/V1", countsFields, reconcile["counts"] as ByteArray).values.map { it as Long }
        require(reconCounts == counts && reconcile["outcome"] in setOf("EXACT", "MISMATCH", "INDETERMINATE")) { "AUDIT_INCONSISTENT" }
        val exact = if (reconcile["outcome"] == "EXACT") {
            require(reconCounts == listOf(1L, 1L, 1L, 1L, 1L, 3L, 1L) && reconcile["authority_intent_matches"] == true && reconcile["authority_receipt_matches"] == true && reconcile["head_matches"] == true)
            val accepted = GovernedFrame.decode(GovernedFrame.ROOT + "RECONCILE-ACCEPTED/V1", GovernedTuples.AUDIT_ACCEPTED, requireNotNull(reconcile["accepted_snapshot"]) as ByteArray).toMutableMap()
            require(accepted["organization_id"] == input.attestation.manifest.organizationId.value && accepted["manifest_id"] == input.attestation.manifest.manifestId)
            accepted["signature_preimage_bytes"] = accepted.remove("canonical_signature_preimage_bytes")
            GovernedAttestation.verify(input.attestation, accepted)
            val decision = GovernedFrame.decode(GovernedFrame.ROOT + "RECONCILE-DECISION/V1", GovernedTuples.AUDIT_DECISION, requireNotNull(reconcile["decision_snapshot"]) as ByteArray, setOf("supersedes_decision_id", "provider_revision_local"))
            verifyDecision(input, decision)
            val evidence = GovernedFrame.decode(GovernedFrame.ROOT + "RECONCILE-EVIDENCE/V1", GovernedFrame.fields("marketplace_key text,promotion_outcome text,source_integration_ref text,omie_currency text,semantic_fingerprint_version int4,source_evidence_semantic_fingerprint text,provider_revision_local timestamp without time zone"), requireNotNull(reconcile["evidence_snapshot"]) as ByteArray, setOf("source_integration_ref", "omie_currency", "provider_revision_local"))
            verifyEvidence(input, decision, evidence)
            true
        } else false
        val empty = counts.all { it == 0L } && inspect["domain_projection"] == "EMPTY" && inspect["binding_state"] == "ACTIVE" && inspect["delivery_state"] == "NOT_CREATED" && inspect["admission_state"] == null && inspect["ceremony_result"] == "NONE" && reconcile["outcome"] == "INDETERMINATE"
        Audit(preflight, inspect["generation"] as Long, empty, exact)
    }
    private fun transactionIdentityHash(fields: List<String>): String {
        val framed = fields.joinToString("") { "${it.toByteArray(Charsets.UTF_8).size}:$it" }
        return MessageDigest.getInstance("SHA-256").digest(framed.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
    }
    private fun verifyEvidence(input: OfflineFieldProofInput, d: Map<String, Any?>, e: Map<String, Any?>) {
        val m = input.attestation.manifest
        val evidence = ApprovalEvidenceBindingCodec.Evidence(m.organizationId, m.marketplaceOrderId, m.mercadoLivreConnectionId,
            d.getValue("ml_capability") as String, d.getValue("ml_progress_version") as Long, d.getValue("ml_record_ordinal") as Int,
            e.getValue("marketplace_key") as String, d.getValue("external_order_id") as String, d.getValue("currency") as String,
            e.getValue("promotion_outcome") as String, m.omieConnectionId, d.getValue("omie_capability") as String,
            d.getValue("omie_progress_version") as Long, d.getValue("omie_record_ordinal") as Int, d.getValue("source_order_reference") as String,
            e["source_integration_ref"] as String?, e["omie_currency"] as String?, e.getValue("semantic_fingerprint_version") as Int,
            e.getValue("source_evidence_semantic_fingerprint") as String, requireNotNull(e["provider_revision_local"]) as LocalDateTime)
        require(e["provider_revision_local"] == d["provider_revision_local"] && d["omie_semantic_fingerprint"] == evidence.omieSemanticFingerprint && ApprovalEvidenceBindingCodec.fingerprint(evidence) == m.evidenceBindingFingerprint)
    }
    private fun verifyDecision(input: OfflineFieldProofInput, d: Map<String, Any?>) {
        val c = input.command; val m = input.attestation.manifest; val p = input.plan
        require(d["organization_id"] == m.organizationId.value && d["decision_id"] == p.decisionId && d["omie_connection_id"] == m.omieConnectionId && d["ml_connection_id"] == m.mercadoLivreConnectionId && d["source_order_reference"] == c.sourceOrderReference && d["marketplace_order_id"] == c.marketplaceOrderId && d["kind"] == c.kind.name && d["reason"] == c.reason.name && d["provenance"] == c.provenance && d["correlation_id"] == c.correlationId && d["supersedes_decision_id"] == null && d["revision"] == 1 && d["principal_id"] == p.principalId.value && d["credential_id"] == p.credentialId && d["grant_id"] == p.grantId && d["credential_revision"] == 1 && d["grant_revision"] == 1 && d["permission"] == m.permission.name)
        val intent = transactionIdentityHash(listOf("transaction-identity-intent/1", m.organizationId.value.toString(), p.principalId.value.toString(), m.mercadoLivreConnectionId.toString(), m.omieConnectionId.toString(), c.sourceOrderReference, c.marketplaceOrderId.toString(), c.kind.name, c.reason.name, c.provenance, ""))
        require(d["intent_fingerprint"] == intent)
        val fingerprint = transactionIdentityHash(listOf("transaction-identity/1", intent, m.mercadoLivreConnectionId.toString(), d.getValue("ml_capability").toString(), d.getValue("ml_progress_version").toString(), d.getValue("ml_record_ordinal").toString(), d.getValue("external_order_id").toString(), d.getValue("currency").toString(), d.getValue("omie_capability").toString(), "1", d.getValue("omie_semantic_fingerprint").toString(), (requireNotNull(d["provider_revision_local"]) as LocalDateTime).format(DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss.SSSSSS")), p.grantId.toString(), "1", m.permission.name, d.getValue("authorization_semantic_version").toString(), d.getValue("authorization_fingerprint").toString()))
        require(d["decision_semantic_fingerprint"] == fingerprint)
    }
}
