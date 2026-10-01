package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import java.util.UUID
import io.flooow.marketplace.persistence.postgres.PostgresConfiguration
import io.flooow.marketplace.persistence.postgres.PostgresDataSources
import java.sql.Connection
import javax.sql.DataSource

data class OfflineDatabaseConfiguration(
    val verifier: PostgresConfiguration,
    val issuer: PostgresConfiguration,
    val runtime: PostgresConfiguration
) {
    init {
        require(setOf(verifier.user, issuer.user, runtime.user).size == 3) {
            "Verifier, issuer and runtime database login names must be distinct"
        }
    }

    companion object {
        fun fromEnvironment(environment: Map<String, String> = System.getenv()): OfflineDatabaseConfiguration {
            fun boundary(prefix: String) = PostgresConfiguration(
                environment["FLOOOW_${prefix}_DATABASE_URL"].orEmpty(),
                environment["FLOOOW_${prefix}_DATABASE_USER"].orEmpty(),
                environment["FLOOOW_${prefix}_DATABASE_PASSWORD"].orEmpty()
            )
            return OfflineDatabaseConfiguration(boundary("VERIFIER"), boundary("ISSUER"), boundary("RUNTIME"))
        }
    }
}

data class OfflineDataSources(val verifier: DataSource, val issuer: DataSource, val runtime: DataSource) {
    companion object {
        fun create(configuration: OfflineDatabaseConfiguration) = OfflineDataSources(
            PostgresDataSources.create(configuration.verifier),
            PostgresDataSources.create(configuration.issuer),
            PostgresDataSources.create(configuration.runtime)
        )
    }
}

class PostgresOfflineFieldProofBoundaryVerifier(
    private val configuration: OfflineDatabaseConfiguration,
    private val dataSources: OfflineDataSources
) : OfflineFieldProofBoundaryVerifier {
    override fun verify(input: OfflineFieldProofInput): Boolean = runCatching {
        val identities = listOf(
            verifyBoundary(dataSources.verifier, configuration.verifier.user, "flooow_attestation_verifier"),
            verifyBoundary(dataSources.issuer, configuration.issuer.user, "flooow_command_issuer"),
            verifyBoundary(dataSources.runtime, configuration.runtime.user, "flooow_command_runtime")
        )
        require(identities.toSet().size == identities.size) { "Database service identities are not distinct" }
        dataSources.runtime.connection.use { connection ->
            connection.isReadOnly = true
            connection.autoCommit = false
            require(PostgresOfflineMigrationHistory.provesV042(connection)) { "V042 migration history is not proven" }
            connection.prepareStatement(
                """SELECT status='ACTIVE' FROM public.integration_organization WHERE organization_id=?"""
            ).use { statement ->
                statement.setObject(1, input.attestation.manifest.organizationId.value)
                statement.executeQuery().use { rows -> require(rows.next() && rows.getBoolean(1)) { "Organization is not ACTIVE" } }
            }
            for (table in listOf("s2a_accepted_attestation", "s2a_attestation_consumption", "s2a_signer_key_revision",
                "s2a_signer_authority_revision", "command_authority_operation", "command_principal",
                "command_credential_revision", "command_permission_grant", "marketplace_transaction_identity_decision",
                "marketplace_transaction_identity_head")) {
                connection.prepareStatement("SELECT has_table_privilege(current_user, ?, 'SELECT')").use { statement ->
                    statement.setString(1, "public.$table")
                    statement.executeQuery().use { rows -> require(rows.next() && rows.getBoolean(1)) }
                }
            }
            for (function in AUDIT_FUNCTIONS) {
                connection.prepareStatement("SELECT NOT p.prosecdef AND p.provolatile IN ('i','s') AND has_function_privilege(current_user,p.oid,'EXECUTE') FROM pg_catalog.pg_proc p WHERE p.oid=to_regprocedure(?)").use { statement ->
                    statement.setString(1,function)
                    statement.executeQuery().use { rows -> require(rows.next() && rows.getBoolean(1) && !rows.next()) }
                }
            }
            val requiredFunctions = listOf(
                "s2a_v042_begin_attested_decision_verification",
                "s2a_v042_apply_attested_decision"
            )
            connection.prepareStatement(
                """SELECT count(*) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
                   WHERE n.nspname='public' AND p.proname = ANY(?)"""
            ).use { statement ->
                statement.setArray(1, connection.createArrayOf("text", requiredFunctions.toTypedArray()))
                statement.executeQuery().use { rows -> rows.next(); require(rows.getInt(1) == 2) { "V042 capability contract is absent" } }
            }
            require(connection.createStatement().use { statement ->
                statement.executeQuery("SELECT to_regclass('public.s2a_attestation_consumption') IS NOT NULL").use { rows ->
                    rows.next() && rows.getBoolean(1)
                }
            }) { "V042 consumption relation is absent" }
        }
        true
    }.getOrDefault(false)

    private fun verifyBoundary(dataSource: DataSource, expectedLogin: String, expectedRole: String): String =
        dataSource.connection.use { connection ->
            val identity = connection.createStatement().use { statement ->
                statement.executeQuery(
                    """SELECT session_user,current_user,rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls
                       FROM pg_catalog.pg_roles WHERE rolname=session_user"""
                ).use { rows ->
                    require(rows.next())
                    require(rows.getString(1) == expectedLogin) { "Unexpected database login identity" }
                    require(!(rows.getBoolean(3) || rows.getBoolean(4) || rows.getBoolean(5) || rows.getBoolean(6) || rows.getBoolean(7))) {
                        "Operational database login is privileged"
                    }
                    rows.getString(1)
                }
            }
            require(hasRole(connection, expectedRole)) { "Required capability membership is absent" }
            for (role in PROTECTED_ROLES - expectedRole) {
                require(!hasRole(connection, role)) { "Protected-role cross-membership is forbidden" }
            }
            identity
        }

    private fun hasRole(connection: Connection, role: String): Boolean = connection.prepareStatement(
        "SELECT pg_catalog.pg_has_role(session_user, ?, 'USAGE') OR current_user=?"
    ).use { statement ->
        statement.setString(1, role)
        statement.setString(2, role)
        statement.executeQuery().use { rows -> rows.next() && rows.getBoolean(1) }
    }

    private companion object {
        val AUDIT_FUNCTIONS = listOf(
            "public.s2a_v042_authority_intent(text,uuid,uuid,uuid,uuid,uuid,uuid,bytea,uuid,text,text,uuid,uuid,text,text)",
            "public.s2a_v042_authority_receipt(text,text,uuid,uuid,integer,uuid,integer,text,text)",
            "public.s2a_v042_text(text)", "public.s2a_v042_frame(bytea)",
            "public.transaction_identity_intent(public.marketplace_transaction_identity_decision)",
            "public.transaction_identity_fingerprint(public.marketplace_transaction_identity_decision)",
            "public.transaction_identity_grant_fingerprint(uuid,uuid)", "public.transaction_identity_hash(text[])"
        )
        val PROTECTED_ROLES = setOf(
            "flooow_approval_governance",
            "flooow_attestation_verifier",
            "flooow_command_issuer",
            "flooow_command_runtime"
        )
    }
}

class PostgresOfflineFieldProofReconciler(
    private val auditDataSource: DataSource
) : OfflineFieldProofReconciler {
    override fun inspect(input: OfflineFieldProofInput): OfflineFieldProofDurableState =
        readOnly { inspect(it, input) }

    private fun inspect(connection: Connection, input: OfflineFieldProofInput): OfflineFieldProofDurableState {
        val plan = input.plan
        val manifest = input.attestation.manifest
        val authority = run {
            val principal = count(
                connection, "public.command_principal",
                "organization_id=? AND principal_id=? AND mercado_livre_connection_id=? AND omie_connection_id=? " +
                    "AND reason=? AND provenance=? AND correlation_id=?",
                manifest.organizationId.value, plan.principalId.value, manifest.mercadoLivreConnectionId,
                manifest.omieConnectionId, manifest.reason, manifest.provenance, manifest.correlationId
            )
            val credential = count(
                connection, "public.command_credential_revision",
                "organization_id=? AND principal_id=? AND credential_id=? AND revision=1 " +
                    "AND supersedes_revision IS NULL AND state='ENABLED' AND reason=? AND provenance=? AND correlation_id=?",
                manifest.organizationId.value, plan.principalId.value, plan.credentialId,
                manifest.reason, manifest.provenance, manifest.correlationId
            )
            val grant = count(
                connection, "public.command_permission_grant",
                "organization_id=? AND principal_id=? AND grant_id=? AND revision=1 " +
                    "AND supersedes_grant_id IS NULL AND permission='TRANSACTION_IDENTITY_DECISION_WRITE' " +
                    "AND state='ENABLED' AND reason=? AND provenance=? AND correlation_id=?",
                manifest.organizationId.value, plan.principalId.value, plan.grantId,
                manifest.reason, manifest.provenance, manifest.correlationId
            )
            val principalOperation = count(
                connection, "public.command_authority_operation",
                "organization_id=? AND operation_id=? AND operation='PRINCIPAL' AND principal_id=? " +
                    "AND credential_id IS NULL AND credential_revision IS NULL AND grant_id IS NULL " +
                    "AND grant_revision IS NULL AND permission IS NULL AND state IS NULL " +
                    "AND correlation_id=? AND attestation_manifest_id=?",
                manifest.organizationId.value, plan.principalOperationId, plan.principalId.value,
                manifest.correlationId, manifest.manifestId
            )
            val credentialOperation = count(
                connection, "public.command_authority_operation",
                "organization_id=? AND operation_id=? AND operation='INITIAL_CREDENTIAL' AND principal_id=? " +
                    "AND credential_id=? AND credential_revision=1 AND grant_id IS NULL AND grant_revision IS NULL " +
                    "AND permission IS NULL AND state='ENABLED' AND correlation_id=? AND attestation_manifest_id=?",
                manifest.organizationId.value, plan.initialCredentialOperationId, plan.principalId.value,
                plan.credentialId, manifest.correlationId, manifest.manifestId
            )
            val grantOperation = count(
                connection, "public.command_authority_operation",
                "organization_id=? AND operation_id=? AND operation='GRANT' AND principal_id=? " +
                    "AND credential_id IS NULL AND credential_revision IS NULL AND grant_id=? AND grant_revision=1 " +
                    "AND permission='TRANSACTION_IDENTITY_DECISION_WRITE' AND state='ENABLED' " +
                    "AND correlation_id=? AND attestation_manifest_id=?",
                manifest.organizationId.value, plan.grantOperationId, plan.principalId.value, plan.grantId,
                manifest.correlationId, manifest.manifestId
            )
            val actualPrincipal = count(connection, "public.command_principal", "organization_id=? AND principal_id=?", manifest.organizationId.value, plan.principalId.value)
            val actualCredential = count(connection, "public.command_credential_revision", "organization_id=? AND (credential_id=? OR principal_id=?)", manifest.organizationId.value, plan.credentialId, plan.principalId.value)
            val actualGrant = count(connection, "public.command_permission_grant", "organization_id=? AND (grant_id=? OR principal_id=?)", manifest.organizationId.value, plan.grantId, plan.principalId.value)
            val actualOperations = count(connection, "public.command_authority_operation", "organization_id=? AND (principal_id=? OR attestation_manifest_id=? OR operation_id IN (?,?,?))", manifest.organizationId.value, plan.principalId.value, manifest.manifestId, plan.principalOperationId, plan.initialCredentialOperationId, plan.grantOperationId)
            val operationCount = principalOperation + credentialOperation + grantOperation
            val operationsAreUnique = principalOperation in 0..1 && credentialOperation in 0..1 && grantOperation in 0..1
            val prefixIsExact = when (operationCount) {
                0 -> principal == 0 && credential == 0 && grant == 0
                1 -> principal == 1 && credential == 0 && grant == 0 && principalOperation == 1
                2 -> principal == 1 && credential == 1 && grant == 0 &&
                    principalOperation == 1 && credentialOperation == 1
                3 -> principal == 1 && credential == 1 && grant == 1 &&
                    principalOperation == 1 && credentialOperation == 1 && grantOperation == 1
                else -> false
            }
            Triple(listOf(actualPrincipal, actualCredential, actualGrant), actualOperations,
                operationsAreUnique && prefixIsExact && actualPrincipal == principal && actualCredential == credential &&
                actualGrant == grant && actualOperations == operationCount)
        }
        val decisionState = run {
            val decision = count(connection, "public.marketplace_transaction_identity_decision", "organization_id=? AND decision_id=?", manifest.organizationId.value, plan.decisionId)
            val head = count(connection, "public.marketplace_transaction_identity_head", "organization_id=? AND decision_id=?", manifest.organizationId.value, plan.decisionId)
            decision to head
        }
        return OfflineFieldProofDurableState(
            authority.first[0], authority.first[1], authority.first[2], authority.second,
            decisionState.first, decisionState.second,
            authority.third && decisionState.first in 0..1 && decisionState.second in 0..1 &&
                decisionState.first == decisionState.second &&
                (decisionState.first == 0 || authority.second == 3) &&
                (if (authority.second == 0) count(connection,"public.s2a_attestation_consumption",
                    "organization_id=? AND manifest_id=?",manifest.organizationId.value,manifest.manifestId)==0
                 else accepted(connection,input) && consumption(connection,input) && fingerprints(connection,input,authority.second)),
            count(connection, "public.command_authority_operation",
                "organization_id=? AND (principal_id=? OR attestation_manifest_id=? OR operation_id IN (?,?)) " +
                "AND operation IN ('INITIAL_CREDENTIAL','ROTATE_CREDENTIAL','GRANT','REVOKE')",
                manifest.organizationId.value, plan.principalId.value, manifest.manifestId,
                plan.initialCredentialOperationId, plan.grantOperationId) > 0
        )
    }

    override fun reconcile(input: OfflineFieldProofInput): OfflineFieldProofReconciliation = readOnly { connection ->
        val state = inspect(connection, input)
        val accepted = accepted(connection, input)
        val consumed = consumption(connection, input)
        val complete = state.lineageMatches && state.principalCount == 1 && state.credentialCount == 1 &&
            state.grantCount == 1 && state.authorityOperationCount == 3 && state.decisionCount == 1 && state.headCount == 1
        OfflineFieldProofReconciliation(accepted, consumed, state,
            accepted && consumed && complete && fingerprints(connection, input) && decision(connection, input) && evidence(connection, input))
    }

    /** JDBC read-only is set before starting a repeatable-read transaction; PostgreSQL enforces it. */
    private fun <T> readOnly(block: (Connection) -> T): T = auditDataSource.connection.use { connection ->
        connection.isReadOnly = true
        connection.transactionIsolation = Connection.TRANSACTION_REPEATABLE_READ
        connection.autoCommit = false
        try { block(connection) } finally { connection.rollback() }
    }

    private fun accepted(connection: Connection, input: OfflineFieldProofInput): Boolean =
        runCatching { acceptedArtifact(connection, input) }.getOrDefault(false)

    private fun acceptedArtifact(connection: Connection, input: OfflineFieldProofInput): Boolean {
        val signed = input.attestation
        val m = signed.manifest
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(m)
        val digest = ApprovalManifestCanonicalCodec.manifestDigest(canonical)
        val preimage = ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes(
            signed.algorithmId, signed.signerKeyId, signed.signerKeyFingerprint, digest)
        if (count(connection, "public.s2a_accepted_attestation", "organization_id=? AND manifest_id=?",
                m.organizationId.value, m.manifestId) != 1) return false
        return connection.prepareStatement("""
            SELECT a.* FROM public.s2a_accepted_attestation a
            JOIN public.s2a_signer_key_revision k ON k.organization_id=a.organization_id
              AND k.signer_key_id=a.signer_key_id AND k.revision=a.signer_key_revision
              AND k.signer_key_fingerprint=a.signer_key_fingerprint
              AND k.lineage_fingerprint=a.signer_key_lineage_fingerprint
              AND k.subject_public_key_info_der=a.subject_public_key_info_der
            JOIN public.s2a_signer_authority_revision g ON g.organization_id=a.organization_id
              AND g.signer_authority_id=a.signer_authority_id AND g.revision=a.signer_authority_revision
              AND g.signer_authority_fingerprint=a.signer_authority_fingerprint
              AND g.signer_subject_id=k.signer_subject_id AND g.signer_key_id=k.signer_key_id
              AND g.signer_key_revision=k.revision AND g.signer_key_fingerprint=k.signer_key_fingerprint
              AND g.approval_source_id=? AND g.signer_role='S2A_FIELD_PROOF_APPROVER'
              AND g.approval_action='S2A_FIELD_PROOF_APPROVAL'
              AND g.permission='TRANSACTION_IDENTITY_DECISION_WRITE'
              AND k.algorithm_id=a.algorithm_id AND k.state='ACTIVE' AND k.valid_from<=a.verified_at AND k.effective_at<=a.verified_at
              AND g.state='ENABLED' AND g.valid_from<=a.verified_at AND a.verified_at<g.valid_until
              AND g.decided_at<=a.verified_at
            WHERE a.organization_id=? AND a.manifest_id=?
        """).use { statement ->
            statement.setObject(1, m.approvalSource.value)
            statement.setObject(2, m.organizationId.value)
            statement.setObject(3, m.manifestId)
            statement.executeQuery().use { rows ->
                if (!rows.next()) return false
                val publicKey = SignerPublicKeyInfo.parse(rows.getBytes("subject_public_key_info_der"))
                val proof = AcceptedAttestationProof.create(
                    rows.getInt("artifact_version"), rows.getInt("canonicalization_version"),
                    rows.getBytes("canonical_manifest_bytes"), rows.getString("manifest_digest"),
                    rows.getBytes("canonical_signature_preimage_bytes"), rows.getString("algorithm_id"),
                    SignerKeyId(rows.getObject("signer_key_id", UUID::class.java)), rows.getInt("signer_key_revision"),
                    SignerKeyFingerprint(rows.getString("signer_key_fingerprint")),
                    SignerKeyLineageFingerprint(rows.getString("signer_key_lineage_fingerprint")),
                    publicKey.bytes(), rows.getBytes("signature_bytes"),
                    SignerAuthorityId(rows.getObject("signer_authority_id", UUID::class.java)),
                    rows.getInt("signer_authority_revision"),
                    SignerAuthorityFingerprint(rows.getString("signer_authority_fingerprint")),
                    rows.getTimestamp("verified_at").toInstant())
                val matches = !proof.verifiedAt.isBefore(m.approvalWindowStart) && proof.verifiedAt.isBefore(m.approvalWindowEnd) &&
                    rows.getInt("schema_version") == m.schemaVersion &&
                    proof.canonicalManifestBytes().contentEquals(canonical) && proof.manifestDigest == digest &&
                    proof.canonicalSignaturePreimageBytes().contentEquals(preimage) &&
                    proof.algorithmId == signed.algorithmId && proof.signerKeyId == signed.signerKeyId &&
                    proof.signerKeyFingerprint == signed.signerKeyFingerprint &&
                    publicKey.fingerprint() == signed.signerKeyFingerprint &&
                    proof.signatureBytes().contentEquals(signed.signatureBytes()) &&
                    rows.getTimestamp("recorded_at").toInstant() == proof.verifiedAt &&
                    AcceptedAttestationFingerprintCodec.fingerprint(proof) == rows.getString("accepted_proof_fingerprint") &&
                    Ed25519ApprovalSignatureVerifier.verify(publicKey, preimage, proof.signatureBytes())
                matches && !rows.next()
            }
        }
    }

    private fun consumption(connection: Connection, input: OfflineFieldProofInput): Boolean {
        val m=input.attestation.manifest
        val p=input.plan
        return count(connection,"public.s2a_attestation_consumption","organization_id=? AND manifest_id=?",
            m.organizationId.value,m.manifestId)==1 &&
            count(connection,"public.s2a_attestation_consumption c JOIN public.s2a_accepted_attestation a USING (organization_id,manifest_id) " +
                "JOIN public.command_principal p ON p.organization_id=c.organization_id AND p.principal_id=c.principal_id " +
                "JOIN public.command_authority_operation o ON o.organization_id=c.organization_id AND o.attestation_manifest_id=c.manifest_id AND o.principal_id=c.principal_id",
                "c.organization_id=? AND c.manifest_id=? AND c.manifest_digest=? AND c.manifest_digest=a.manifest_digest " +
                "AND c.principal_id=? AND c.correlation_id=? AND o.operation_id=? AND o.operation='PRINCIPAL' " +
                "AND o.correlation_id=c.correlation_id AND p.correlation_id=c.correlation_id " +
                "AND c.consumed_at=o.decided_at AND p.decided_at=o.decided_at",
                m.organizationId.value,m.manifestId,
                ApprovalManifestCanonicalCodec.manifestDigest(ApprovalManifestCanonicalCodec.canonicalManifestBytes(m)),
                p.principalId.value,m.correlationId,p.principalOperationId)==1
    }

    private fun fingerprints(connection: Connection, input: OfflineFieldProofInput, expectedCount: Int = 3): Boolean =
        connection.prepareStatement("""
            SELECT count(*) FROM public.command_authority_operation o
            JOIN public.command_principal p USING (organization_id,principal_id)
            JOIN public.s2a_accepted_attestation a ON a.organization_id=o.organization_id AND a.manifest_id=o.attestation_manifest_id
            LEFT JOIN public.command_permission_grant g ON g.organization_id=o.organization_id AND g.grant_id=o.grant_id
            LEFT JOIN public.command_credential_revision c ON c.organization_id=o.organization_id
              AND c.credential_id=o.credential_id AND c.revision=o.credential_revision
            WHERE o.organization_id=? AND o.attestation_manifest_id=? AND o.principal_id=?
              AND ((o.operation='PRINCIPAL' AND o.decided_at=p.decided_at)
                OR (o.operation='INITIAL_CREDENTIAL' AND o.decided_at=c.decided_at)
                OR (o.operation='GRANT' AND o.decided_at=g.decided_at))
              AND o.intent_fingerprint=public.s2a_v042_authority_intent(o.operation,o.operation_id,o.organization_id,o.principal_id,
                p.mercado_livre_connection_id,p.omie_connection_id,o.credential_id,c.secret_verifier,o.grant_id,
                p.reason,p.provenance,o.correlation_id,o.attestation_manifest_id,a.accepted_proof_fingerprint,a.manifest_digest)
              AND o.receipt_fingerprint=public.s2a_v042_authority_receipt(o.intent_fingerprint,o.operation,o.principal_id,
                o.credential_id,o.credential_revision,o.grant_id,o.grant_revision,o.permission,o.state)
        """).use { statement ->
            statement.setObject(1,input.attestation.manifest.organizationId.value)
            statement.setObject(2,input.attestation.manifest.manifestId)
            statement.setObject(3,input.plan.principalId.value)
            statement.executeQuery().use { it.next() && it.getInt(1)==expectedCount }
        }

    private fun decision(connection: Connection, input: OfflineFieldProofInput): Boolean {
        val m=input.attestation.manifest
        val p=input.plan
        val d=input.command
        return count(connection, "public.marketplace_transaction_identity_decision d JOIN public.marketplace_transaction_identity_head h ON h.organization_id=d.organization_id AND h.decision_id=d.decision_id",
            "d.organization_id=? AND d.decision_id=? AND d.principal_id=? AND d.credential_id=? AND d.credential_revision=1 " +
            "AND d.grant_id=? AND d.grant_revision=1 AND d.omie_connection_id=? AND d.ml_connection_id=? " +
            "AND d.source_order_reference=? AND d.marketplace_order_id=? AND d.kind=? AND d.reason=? " +
            "AND d.provenance=? AND d.correlation_id=? AND d.supersedes_decision_id IS NOT DISTINCT FROM ? " +
            "AND h.omie_connection_id=d.omie_connection_id AND h.source_order_reference=d.source_order_reference " +
            "AND h.marketplace_order_id=d.marketplace_order_id AND h.kind=d.kind " +
            "AND d.intent_fingerprint=public.transaction_identity_intent(d) " +
            "AND d.decision_semantic_fingerprint=public.transaction_identity_fingerprint(d) " +
            "AND d.authorization_fingerprint=public.transaction_identity_grant_fingerprint(d.organization_id,d.grant_id)",
            m.organizationId.value,p.decisionId,p.principalId.value,p.credentialId,p.grantId,
            m.omieConnectionId,m.mercadoLivreConnectionId,d.sourceOrderReference,d.marketplaceOrderId,d.kind.name,
            d.reason.name,d.provenance,d.correlationId,d.supersedesDecisionId) == 1
    }

    private fun evidence(connection: Connection, input: OfflineFieldProofInput): Boolean {
        return connection.prepareStatement("""
            SELECT d.*,i.marketplace_key,p.outcome,b.source_integration_ref,b.currency AS omie_currency,
                v.semantic_fingerprint_version,v.source_evidence_semantic_fingerprint,
                coalesce(v.provider_modified_local,v.provider_created_local) AS evidence_revision
            FROM public.marketplace_transaction_identity_decision d
            JOIN public.marketplace_order_identity_registry i ON i.organization_id=d.organization_id
                AND i.marketplace_order_id=d.marketplace_order_id AND i.external_order_id=d.external_order_id AND i.currency=d.currency
            JOIN public.marketplace_order_occurrence_source_promotion p ON p.organization_id=d.organization_id
                AND p.marketplace_order_id=d.marketplace_order_id AND p.source_connection_id=d.ml_connection_id
                AND p.source_capability=d.ml_capability AND p.source_input_progress_version=d.ml_progress_version
                AND p.source_record_ordinal=d.ml_record_ordinal AND p.outcome IN ('PROMOTED','DUPLICATE')
            JOIN public.integration_omie_transaction_evidence b ON b.organization_id=d.organization_id
                AND b.connection_id=d.omie_connection_id AND b.capability=d.omie_capability
                AND b.input_progress_version=d.omie_progress_version AND b.record_ordinal=d.omie_record_ordinal
                AND b.source_order_ref=d.source_order_reference
            JOIN public.integration_omie_transaction_evidence_v3 v ON v.organization_id=b.organization_id
                AND v.connection_id=b.connection_id AND v.capability=b.capability
                AND v.input_progress_version=b.input_progress_version AND v.record_ordinal=b.record_ordinal
            WHERE d.organization_id=? AND d.decision_id=?
        """).use { statement ->
            statement.setObject(1,input.attestation.manifest.organizationId.value)
            statement.setObject(2,input.plan.decisionId)
            statement.executeQuery().use { rows ->
                if (!rows.next()) return false
                val m=input.attestation.manifest
                val revision=rows.getObject("evidence_revision",java.time.LocalDateTime::class.java)
                val binding=ApprovalEvidenceBindingCodec.Evidence(m.organizationId,m.marketplaceOrderId,
                    m.mercadoLivreConnectionId,rows.getString("ml_capability"),rows.getLong("ml_progress_version"),
                    rows.getInt("ml_record_ordinal"),rows.getString("marketplace_key"),rows.getString("external_order_id"),
                    rows.getString("currency"),rows.getString("outcome"),m.omieConnectionId,
                    rows.getString("omie_capability"),rows.getLong("omie_progress_version"),rows.getInt("omie_record_ordinal"),
                    rows.getString("source_order_reference"),rows.getString("source_integration_ref"),rows.getString("omie_currency"),
                    rows.getInt("semantic_fingerprint_version"),rows.getString("source_evidence_semantic_fingerprint"),revision)
                val matches=revision==rows.getObject("provider_revision_local",java.time.LocalDateTime::class.java) &&
                    rows.getString("omie_semantic_fingerprint")==binding.omieSemanticFingerprint &&
                    ApprovalEvidenceBindingCodec.fingerprint(binding)==m.evidenceBindingFingerprint
                matches && !rows.next()
            }
        }

    }

    private fun count(connection: Connection, table: String, predicate: String, vararg values: Any?): Int =
        connection.prepareStatement("SELECT count(*) FROM $table WHERE $predicate").use { statement ->
            values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }
            statement.executeQuery().use { rows -> rows.next(); rows.getInt(1) }
        }
}
