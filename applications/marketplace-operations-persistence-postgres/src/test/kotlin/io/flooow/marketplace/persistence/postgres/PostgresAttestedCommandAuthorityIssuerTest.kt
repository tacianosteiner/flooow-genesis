package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.organization.OrganizationId
import org.flywaydb.core.Flyway
import org.postgresql.ds.PGSimpleDataSource
import org.postgresql.util.PSQLException
import org.testcontainers.postgresql.PostgreSQLContainer
import java.io.PrintWriter
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Proxy
import java.security.KeyFactory
import java.security.Signature
import java.security.spec.PKCS8EncodedKeySpec
import java.sql.Connection
import java.sql.PreparedStatement
import java.sql.ResultSet
import java.sql.SQLException
import java.sql.Timestamp
import java.time.Instant
import java.time.LocalDateTime
import java.util.Base64
import java.util.UUID
import javax.sql.DataSource
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import kotlin.test.assertTrue

class PostgresAttestedCommandAuthorityIssuerTest {
    private lateinit var db: PostgreSQLContainer

    @BeforeTest
    fun start() {
        db = PostgreSQLContainer("postgres:18.4")
        db.start()
        Flyway.configure().dataSource(db.jdbcUrl, db.username, db.password).load().migrate()
    }

    @AfterTest
    fun stop() {
        if (::db.isInitialized) db.stop()
    }

    @Test
    fun `real V042 issuer verifies immutable JCA snapshot applies three acts and rejects adversarial inputs without effects`() {
        installFixture()
        val manifest = manifest()
        assertIs<AcceptedAttestationResult.Accepted>(verifier().verify(sign(manifest)))
        val acceptedOnly = durableState()
        assertEquals(DurableState(1, 0, 0, 0, 0, 0), acceptedOnly)

        assertDeniedWithoutEffect(
            issuer(tamperBeginBytes("result_signature_bytes") { bytes -> bytes.copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() } }),
            principalRequest(manifest),
            AttestedAuthorityFailure.INVALID_SIGNATURE,
            acceptedOnly
        )
        assertDeniedWithoutEffect(
            issuer(tamperBeginBytes("result_signature_preimage_bytes") { bytes -> bytes.copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() } }),
            principalRequest(manifest),
            AttestedAuthorityFailure.INTEGRITY_FAILURE,
            acceptedOnly
        )
        assertDeniedWithoutEffect(
            issuer(tamperBeginBytes("result_subject_public_key_info_der") { bytes -> bytes.copyOf().also { it[it.lastIndex] = (it.last().toInt() xor 1).toByte() } }),
            principalRequest(manifest),
            AttestedAuthorityFailure.INTEGRITY_FAILURE,
            acceptedOnly
        )
        assertDeniedWithoutEffect(
            issuer(tamperBeginString("result_accepted_proof_fingerprint", "0".repeat(64))),
            principalRequest(manifest),
            AttestedAuthorityFailure.INTEGRITY_FAILURE,
            acceptedOnly
        )
        assertDeniedWithoutEffect(
            issuer(tamperBeginBytes("result_canonical_manifest_bytes") { it + byteArrayOf(0) }),
            principalRequest(manifest),
            AttestedAuthorityFailure.UNSUPPORTED_CANONICAL_FORM,
            acceptedOnly
        )
        assertFailsWith<PSQLException> { issuer(failApply()).issuePrincipal(principalRequest(manifest)) }
        assertEquals(acceptedOnly, durableState(), "unknown SQL failure before APPLY was not rolled back")

        val changedClaim = manifest.copy(reason = "changed signed claim")
        assertEquals(
            AttestedAuthorityResult.Denied(AttestedAuthorityFailure.INTEGRITY_FAILURE),
            issuer().issuePrincipal(principalRequest(changedClaim))
        )
        assertEquals(acceptedOnly, durableState())

        val wrongManifest = manifest.copy(manifestId = uuid(90))
        assertEquals(
            AttestedAuthorityResult.Denied(AttestedAuthorityFailure.GOVERNANCE_UNAVAILABLE),
            issuer().issuePrincipal(principalRequest(wrongManifest))
        )
        assertEquals(acceptedOnly, durableState())

        val crossOrganization = manifest.copy(organizationId = OrganizationId.parse(uuid(91).toString()))
        assertEquals(
            AttestedAuthorityResult.Denied(AttestedAuthorityFailure.GOVERNANCE_UNAVAILABLE),
            issuer().issuePrincipal(principalRequest(crossOrganization))
        )
        assertEquals(acceptedOnly, durableState())

        val realIssuer = issuer()
        val principalApplied = assertIs<AttestedAuthorityResult.Applied>(realIssuer.issuePrincipal(principalRequest(manifest)))
        val principalReplay = assertIs<AttestedAuthorityResult.AlreadyApplied>(realIssuer.issuePrincipal(principalRequest(manifest)))
        assertEquals(principalApplied.receipt, principalReplay.receipt)
        assertEquals(DurableState(1, 1, 1, 0, 0, 1), durableState())

        val changedPrincipalRequest = principalRequest(manifest).copy(principalId = CommandPrincipalId(uuid(92)))
        assertEquals(
            AttestedAuthorityResult.Denied(AttestedAuthorityFailure.INTEGRITY_FAILURE),
            realIssuer.issuePrincipal(changedPrincipalRequest)
        )
        assertEquals(DurableState(1, 1, 1, 0, 0, 1), durableState())

        val credentialRequest = AttestedInitialCredentialRequest(
            organizationId, manifest.manifestId, manifest, credentialOperation, principalId,
            credentialId, ByteArray(32) { (it + 1).toByte() }
        )
        val credentialApplied = assertIs<AttestedAuthorityResult.Applied>(realIssuer.bindInitialCredential(credentialRequest))
        val credentialReplay = assertIs<AttestedAuthorityResult.AlreadyApplied>(realIssuer.bindInitialCredential(credentialRequest))
        assertEquals(credentialApplied.receipt, credentialReplay.receipt)
        assertEquals(DurableState(1, 1, 1, 1, 0, 2), durableState())

        val wrongCredential = credentialRequest.copy(credentialId = uuid(93))
        assertEquals(
            AttestedAuthorityResult.Denied(AttestedAuthorityFailure.INTEGRITY_FAILURE),
            realIssuer.bindInitialCredential(wrongCredential)
        )
        assertEquals(DurableState(1, 1, 1, 1, 0, 2), durableState())

        val grantRequest = AttestedGrantRequest(
            organizationId, manifest.manifestId, manifest, grantOperation, principalId, grantId
        )
        val grantApplied = assertIs<AttestedAuthorityResult.Applied>(realIssuer.grantPermission(grantRequest))
        val grantReplay = assertIs<AttestedAuthorityResult.AlreadyApplied>(realIssuer.grantPermission(grantRequest))
        assertEquals(grantApplied.receipt, grantReplay.receipt)
        val complete = DurableState(1, 1, 1, 1, 1, 3)
        assertEquals(complete, durableState())

        val wrongGrant = grantRequest.copy(grantId = uuid(94))
        assertEquals(
            AttestedAuthorityResult.Denied(AttestedAuthorityFailure.INTEGRITY_FAILURE),
            realIssuer.grantPermission(wrongGrant)
        )
        assertEquals(complete, durableState())

        assertEquals(principalReplay, realIssuer.issuePrincipal(principalRequest(manifest)))
        assertEquals(credentialReplay, realIssuer.bindInitialCredential(credentialRequest))
        assertEquals(grantReplay, realIssuer.grantPermission(grantRequest))
        assertEquals(complete, durableState(), "adversarial calls poisoned historical exact replay")

        assertDirectIssuerDmlDenied("INSERT INTO public.command_principal VALUES ('$organization'::uuid,'${uuid(99)}'::uuid,'$mlConnection'::uuid,'$omieConnection'::uuid,'x','x','${manifest.correlationId}'::uuid,clock_timestamp())")
    }

    private fun assertDeniedWithoutEffect(
        subject: PostgresAttestedCommandAuthorityIssuer,
        request: AttestedPrincipalRequest,
        expected: AttestedAuthorityFailure,
        before: DurableState
    ) {
        assertEquals(AttestedAuthorityResult.Denied(expected), subject.issuePrincipal(request))
        assertEquals(before, durableState())
    }

    private fun principalRequest(value: ApprovalManifest) = AttestedPrincipalRequest(
        value.organizationId, value.manifestId, value, principalOperation, principalId
    )

    private fun issuer(dataSource: DataSource = roleDataSource("flooow_command_issuer")) =
        PostgresAttestedCommandAuthorityIssuer(dataSource)

    private fun verifier() = PostgresAcceptedAttestationVerifier(roleDataSource("flooow_attestation_verifier"))

    private fun installFixture() {
        val now = Timestamp.from(validFrom)
        update("INSERT INTO integration_organization VALUES (?,'ACTIVE',?,?)", organization, now, now)
        update("INSERT INTO integration_connection VALUES (?,?,?,'OAUTH2_AUTHORIZATION_CODE','REVOKED',1,?,?)", organization, mlConnection, "br.com.mercadolivre", now, now)
        update("INSERT INTO integration_connection VALUES (?,?,?,'STATIC_API_CREDENTIAL','SUSPENDED',1,?,?)", organization, omieConnection, "omie", now, now)
        connection().use { connection ->
            connection.autoCommit = false
            page(connection, mlConnection, mlCapability, 1, 2, 1)
            execute(connection, """
                INSERT INTO integration_mercado_livre_order_source_observation
                (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,
                 provider_status,date_created,date_last_updated,currency,total_amount,observed_at)
                VALUES (?,?,?,1,1,'MLB-123456789','paid',?,?,'BRL',58.28,?)
            """.trimIndent(), organization, mlConnection, mlCapability, now, now, now)
            execute(connection, "INSERT INTO marketplace_order_identity_registry VALUES (?,'mercado-livre','MLB-123456789',?,'BRL',?,?,?,?,1)", organization, marketplaceOrder, now, mlConnection, mlCapability, 1L)
            execute(connection, "INSERT INTO marketplace_order_occurrence_source_promotion VALUES (?,?,?,1,1,?,'PROMOTED',?)", organization, mlConnection, mlCapability, marketplaceOrder, now)
            page(connection, omieConnection, omieCapability, 1, 2, 2)
            omie(connection, 0, "OTHER-SYNTHETIC", null, "BRL", LocalDateTime.parse("2026-09-24T10:00:00.000000"), "cd".repeat(32), now)
            omie(connection, 1, "SO-2026-0001", "INT-2026-0001", null, LocalDateTime.parse("2026-09-25T11:59:59.123456"), "ab".repeat(32), now)
            connection.commit()
        }

        val keyDraft = SignerKeyRevision(
            organizationId, SignerKeyId(keyId), 1, GovernanceSubjectId(subjectId),
            SignerPublicKeyInfo.parse(spkiHex.hex()), keyFingerprint, SignerKeyState.ACTIVE,
            validFrom, validFrom, null, null, SignerKeyLineageFingerprint("0".repeat(64)),
            "Synthetic V041 key", "s2a6-test", uuid(81)
        )
        val key = keyDraft.copy(lineageFingerprint = ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(keyDraft))
        val governance = PostgresApprovalGovernance(roleDataSource("flooow_approval_governance"))
        assertIs<GovernanceAppendResult.Applied>(governance.appendSignerKeyRevision(key))

        val authorityDraft = SignerAuthorityRevision(
            organizationId, SignerAuthorityId(authorityId), 1, key.signerSubjectId,
            GovernanceInstitutionId(institutionId), SignerRole.S2A_FIELD_PROOF_APPROVER,
            key.signerKeyId, 1, key.signerKeyFingerprint, ApprovalAction.S2A_FIELD_PROOF_APPROVAL,
            SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE, validFrom, validUntil,
            SignerAuthorityState.ENABLED, null, null, SignerAuthorityFingerprint("0".repeat(64)),
            "Synthetic V041 authority", "s2a6-test", GovernanceSourceId(approvalSource), uuid(82)
        )
        val authority = authorityDraft.copy(
            signerAuthorityFingerprint = ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(authorityDraft)
        )
        assertIs<GovernanceAppendResult.Applied>(governance.appendSignerAuthorityRevision(authority))
    }

    private fun manifest() = ApprovalManifest(
        1, manifestId, organizationId, mlConnection, omieConnection, "SO-2026-0001", "INT-2026-0001",
        MarketplaceOrderId.parse(marketplaceOrder.toString()), SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,
        GovernanceSubjectId(subjectId), GovernanceSourceId(approvalSource), validFrom, validUntil,
        GovernanceSubjectId(uuid(11)), GovernanceSubjectId(uuid(12)), CredentialDeliveryMethod.PROTECTED_TTY_ONE_TIME,
        GovernanceSubjectId(uuid(13)), ImmediateRevocationPolicy.SEPARATE_APPROVAL_REQUIRED,
        "S2A field proof approval", "s2a6-attested-issuer-test", uuid(14), evidenceFingerprint
    )

    private fun sign(value: ApprovalManifest): SignedApprovalAttestation {
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(value)
        val preimage = ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes(
            "Ed25519", SignerKeyId(keyId), keyFingerprint, ApprovalManifestCanonicalCodec.manifestDigest(canonical)
        )
        val privateKey = KeyFactory.getInstance("Ed25519").generatePrivate(PKCS8EncodedKeySpec((pkcs8Prefix + seedHex).hex()))
        val signature = Signature.getInstance("Ed25519").run { initSign(privateKey); update(preimage); sign() }
        return SignedApprovalAttestation.parse(
            value, "Ed25519", SignerKeyId(keyId), keyFingerprint,
            Base64.getUrlEncoder().withoutPadding().encodeToString(signature)
        )
    }

    private fun durableState() = DurableState(
        count("s2a_accepted_attestation"), count("s2a_attestation_consumption"), count("command_principal"),
        count("command_credential_revision"), count("command_permission_grant"), count("command_authority_operation")
    )

    private fun tamperBeginBytes(column: String, transform: (ByteArray) -> ByteArray): DataSource =
        interceptBegin { method, args, delegate ->
            if (method.name == "getBytes" && args?.firstOrNull() == column) transform(method.invoke(delegate, *args) as ByteArray)
            else invoke(delegate, method, args)
        }

    private fun tamperBeginString(column: String, value: String): DataSource =
        interceptBegin { method, args, delegate ->
            if (method.name == "getString" && args?.firstOrNull() == column) value else invoke(delegate, method, args)
        }

    private fun interceptBegin(resultInvocation: (java.lang.reflect.Method, Array<out Any?>?, ResultSet) -> Any?): DataSource =
        proxyDataSource { sql, statement ->
            if (!sql.contains("_begin_attested_")) statement else proxy(PreparedStatement::class.java, statement) { method, args ->
                val result = invoke(statement, method, args)
                if (method.name == "executeQuery") {
                    val rows = result as ResultSet
                    proxy(ResultSet::class.java, rows) { rowMethod, rowArgs -> resultInvocation(rowMethod, rowArgs, rows) }
                } else result
            }
        }

    private fun failApply(): DataSource = proxyDataSource { sql, statement ->
        if (!sql.contains("_apply_attested_")) statement else proxy(PreparedStatement::class.java, statement) { method, args ->
            if (method.name == "executeQuery") throw PSQLException("synthetic pre-APPLY failure", org.postgresql.util.PSQLState.UNKNOWN_STATE)
            invoke(statement, method, args)
        }
    }

    private fun proxyDataSource(wrap: (String, PreparedStatement) -> PreparedStatement): DataSource {
        val delegate = roleDataSource("flooow_command_issuer")
        return object : DataSource by delegate {
            override fun getConnection(): Connection {
                val connection = delegate.connection
                return proxy(Connection::class.java, connection) { method, args ->
                    val result = invoke(connection, method, args)
                    if (method.name == "prepareStatement" && args?.firstOrNull() is String) {
                        wrap(args[0] as String, result as PreparedStatement)
                    } else result
                }
            }
        }
    }

    private fun <T> proxy(type: Class<T>, delegate: T, invocation: (java.lang.reflect.Method, Array<out Any?>?) -> Any?): T =
        type.cast(Proxy.newProxyInstance(type.classLoader, arrayOf(type)) { _, method, args -> invocation(method, args) })

    private fun invoke(delegate: Any, method: java.lang.reflect.Method, args: Array<out Any?>?): Any? = try {
        if (args == null) method.invoke(delegate) else method.invoke(delegate, *args)
    } catch (failure: InvocationTargetException) {
        throw failure.targetException
    }

    private fun assertDirectIssuerDmlDenied(sql: String) {
        val failure = runCatching { roleDataSource("flooow_command_issuer").connection.use { it.createStatement().execute(sql) } }.exceptionOrNull()
        assertIs<PSQLException>(failure)
        assertEquals("42501", failure.sqlState)
    }

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

    private fun page(c: Connection, id: UUID, capability: String, input: Long, records: Int, marker: Int) {
        execute(c, "INSERT INTO integration_connector_progress VALUES (?,?,?,?,?,false,?,?)", organization, id, capability, input + 1, byteArrayOf(marker.toByte()), Timestamp.from(validFrom), Timestamp.from(validFrom))
        execute(c, "INSERT INTO integration_connector_page_commit VALUES (?,?,?,?,?,?,false,?,?)", organization, id, capability, input, ByteArray(32) { marker.toByte() }, records, Timestamp.from(validFrom), Timestamp.from(validFrom))
    }

    private fun omie(c: Connection, ordinal: Int, order: String, integration: String?, currency: String?, revision: LocalDateTime, fingerprint: String, observed: Timestamp) {
        execute(c, """
            INSERT INTO integration_omie_transaction_evidence
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,source_order_ref,
             source_integration_ref,currency,total_amount,product_refs,observed_at,source_fingerprint)
            VALUES (?,?,?,1,?,?,?,?,58.28,'[]',?,?)
        """.trimIndent(), organization, omieConnection, omieCapability, ordinal, order, integration, currency, observed, "ef".repeat(32))
        execute(c, """
            INSERT INTO integration_omie_transaction_evidence_v3
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,provider_created_local,
             additional_order_totals,semantic_fingerprint_version,source_evidence_semantic_fingerprint)
            VALUES (?,?,?,1,?,?,'{}',1,?)
        """.trimIndent(), organization, omieConnection, omieCapability, ordinal, revision, fingerprint)
    }

    private fun update(sql: String, vararg values: Any?) = connection().use { execute(it, sql, *values) }
    private fun execute(connection: Connection, sql: String, vararg values: Any?) = connection.prepareStatement(sql).use { statement -> values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }; statement.executeUpdate() }
    private fun count(table: String) = connection().use { connection -> connection.createStatement().use { statement -> statement.executeQuery("SELECT count(*) FROM public.$table").use { it.next(); it.getInt(1) } } }
    private fun connection() = java.sql.DriverManager.getConnection(db.jdbcUrl, db.username, db.password)
    private fun uuid(slot: Int) = UUID.fromString("71000000-0000-4000-8000-${slot.toString().padStart(12, '0')}")
    private fun String.hex() = chunked(2).map { it.toInt(16).toByte() }.toByteArray()

    private data class DurableState(val accepted: Int, val consumption: Int, val principal: Int, val credential: Int, val grant: Int, val operations: Int)

    private val organization = UUID.fromString("11111111-1111-4111-8111-111111111111")
    private val organizationId = OrganizationId.parse(organization.toString())
    private val keyId = UUID.fromString("22222222-2222-4222-8222-222222222222")
    private val subjectId = UUID.fromString("33333333-3333-4333-8333-333333333333")
    private val authorityId = UUID.fromString("44444444-4444-4444-8444-444444444441")
    private val institutionId = UUID.fromString("55555555-5555-4555-8555-555555555555")
    private val approvalSource = UUID.fromString("66666666-6666-4666-8666-666666666666")
    private val manifestId = UUID.fromString("77777777-7777-4777-8777-777777777777")
    private val mlConnection = UUID.fromString("88888888-8888-4888-8888-888888888888")
    private val omieConnection = UUID.fromString("99999999-9999-4999-8999-999999999999")
    private val marketplaceOrder = UUID.fromString("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    private val principalOperation = UUID.fromString("12121212-1212-4121-8121-121212121212")
    private val principalId = CommandPrincipalId(UUID.fromString("13131313-1313-4131-8131-131313131313"))
    private val credentialId = UUID.fromString("14141414-1414-4141-8141-141414141414")
    private val grantId = UUID.fromString("15151515-1515-4151-8151-151515151515")
    private val credentialOperation = UUID.fromString("16161616-1616-4161-8161-161616161616")
    private val grantOperation = UUID.fromString("17171717-1717-4171-8171-171717171717")
    private val keyFingerprint = SignerKeyFingerprint("06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9")
    private val validFrom = Instant.parse("2026-09-25T12:00:00.000000Z")
    private val validUntil = Instant.parse("2026-10-25T12:00:00.000000Z")
    private val evidenceFingerprint = "9f61859daa192ae3482ad3dbb28cd7ebb5d2f143cdb6e83092054a80b512e965"
    private val spkiHex = "302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    private val pkcs8Prefix = "302e020100300506032b657004220420"
    private val seedHex = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
    private val mlCapability = "marketplace-economic.order-source"
    private val omieCapability = "marketplace-economic.omie-transaction-evidence.reacquisition-v3"
}
