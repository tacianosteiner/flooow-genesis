package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.organization.OrganizationId
import java.io.PrintWriter
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import javax.sql.DataSource
import kotlin.test.*
import org.flywaydb.core.Flyway
import org.postgresql.ds.PGSimpleDataSource
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresApprovalGovernanceTest {
    private lateinit var db: PostgreSQLContainer

    private val organization = syntheticUuid(1)
    private val subject = syntheticUuid(2)
    private val institution = syntheticUuid(3)
    private val source = syntheticUuid(4)
    private val spkiHex = "302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    private val keyHash = "06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9"
    private val validFrom = Instant.parse("2026-09-25T12:00:00.000000Z")
    private val validUntil = Instant.parse("2026-10-25T12:00:00.000000Z")

    @BeforeTest
    fun start() {
        db = PostgreSQLContainer("postgres:18.4")
        db.start()
        Flyway.configure().dataSource(db.jdbcUrl, db.username, db.password).load().migrate()
        update("INSERT INTO integration_organization VALUES (?,'ACTIVE',now(),now())", organization)
    }

    @AfterTest
    fun stop() {
        if (::db.isInitialized) db.stop()
    }

    @Test
    fun `M01 M02 M03 M04 M05 M06 M07 M08 schema migration and canonical parity are exact`() {
        assertEquals(16, columnCount("s2a_signer_key_revision"))
        assertEquals(21, columnCount("s2a_signer_authority_revision"))
        assertEquals(0, countObjects("SELECT count(*) FROM pg_class WHERE relname IN ('s2a_accepted_attestation','s2a_attestation_consumption')"))
        assertEquals(0, countObjects("SELECT count(*) FROM pg_roles WHERE rolname='flooow_attestation_verifier'"))
        assertEquals(1, countObjects("SELECT count(*) FROM pg_roles WHERE rolname='flooow_approval_governance' AND NOT rolcanlogin AND NOT rolinherit"))

        val goldenOrganization = UUID.fromString("11111111-1111-4111-8111-111111111111")
        val goldenKey = UUID.fromString("22222222-2222-4222-8222-222222222222")
        val goldenSubject = UUID.fromString("33333333-3333-4333-8333-333333333333")
        val goldenAuthorityR1 = UUID.fromString("44444444-4444-4444-8444-444444444441")
        val goldenAuthorityR2 = UUID.fromString("44444444-4444-4444-8444-444444444442")
        val goldenInstitution = UUID.fromString("55555555-5555-4555-8555-555555555555")
        val goldenSource = UUID.fromString("66666666-6666-4666-8666-666666666666")

        val keyR1Expected = "9e83dedfa91c44e001cbf4dbbe729436942ca5b6a568865eff3641e45651de65"
        val keyR2Expected = "7910bae04e816d4f94cd2086c7963d66d104eb2e33d9795fa14e4f0ca47e21e4"
        val authorityR1Expected = "983e222e3e8d9692261db6613c3f0767947c32399493c3ae7de1824aa6371254"
        val authorityR2Expected = "04cb49bc072d0d5466a767f5bc0424e1e3f7fcd6ae486bd3b6bf4f45328452a6"

        assertEquals(keyR1Expected, dbKeyFingerprint(
            goldenOrganization, goldenKey, 1, goldenSubject, "ACTIVE", validFrom, null, null
        ))
        assertEquals(keyR2Expected, dbKeyFingerprint(
            goldenOrganization, goldenKey, 2, goldenSubject, "RETIRED",
            Instant.parse("2026-10-01T12:00:00.000000Z"), 1, keyR1Expected
        ))
        assertEquals(authorityR1Expected, dbAuthorityFingerprint(
            goldenOrganization, goldenAuthorityR1, 1, goldenSubject, goldenInstitution, goldenKey,
            "ENABLED", goldenSource, null, null
        ))
        assertEquals(authorityR2Expected, dbAuthorityFingerprint(
            goldenOrganization, goldenAuthorityR2, 2, goldenSubject, goldenInstitution, goldenKey,
            "DISABLED", goldenSource, goldenAuthorityR1, authorityR1Expected
        ))

        val keyR1 = SignerKeyRevision(
            OrganizationId.parse(goldenOrganization.toString()), SignerKeyId(goldenKey), 1,
            GovernanceSubjectId(goldenSubject), SignerPublicKeyInfo.parse(spkiHex.hex()),
            SignerKeyFingerprint(keyHash), SignerKeyState.ACTIVE, validFrom, validFrom,
            null, null, SignerKeyLineageFingerprint("0".repeat(64)),
            "Synthetic governance", "v040-golden", syntheticUuid(700001)
        ).withComputedFingerprint()
        val keyR2 = SignerKeyRevision(
            keyR1.organizationId, keyR1.signerKeyId, 2, keyR1.signerSubjectId,
            keyR1.subjectPublicKeyInfo, keyR1.signerKeyFingerprint, SignerKeyState.RETIRED,
            validFrom, Instant.parse("2026-10-01T12:00:00.000000Z"), 1, keyR1.lineageFingerprint,
            SignerKeyLineageFingerprint("0".repeat(64)), "Synthetic governance", "v040-golden",
            syntheticUuid(700002)
        ).withComputedFingerprint()
        val authR1 = SignerAuthorityRevision(
            keyR1.organizationId, SignerAuthorityId(goldenAuthorityR1), 1, keyR1.signerSubjectId,
            GovernanceInstitutionId(goldenInstitution), SignerRole.S2A_FIELD_PROOF_APPROVER,
            keyR1.signerKeyId, 1, keyR1.signerKeyFingerprint, ApprovalAction.S2A_FIELD_PROOF_APPROVAL,
            SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE, validFrom, validUntil,
            SignerAuthorityState.ENABLED, null, null, SignerAuthorityFingerprint("0".repeat(64)),
            "Synthetic governance", "v040-golden", GovernanceSourceId(goldenSource), syntheticUuid(700003)
        ).withComputedFingerprint()
        val authR2 = SignerAuthorityRevision(
            authR1.organizationId, SignerAuthorityId(goldenAuthorityR2), 2, authR1.signerSubjectId,
            authR1.signerAuthorizingInstitutionId, authR1.signerRole, authR1.signerKeyId, 1,
            authR1.signerKeyFingerprint, authR1.approvalAction, authR1.permission,
            validFrom, validUntil, SignerAuthorityState.DISABLED, authR1.signerAuthorityId,
            authR1.signerAuthorityFingerprint, SignerAuthorityFingerprint("0".repeat(64)),
            "Synthetic governance", "v040-golden", authR1.approvalSourceId, syntheticUuid(700004)
        ).withComputedFingerprint()

        assertEquals(keyR1Expected, keyR1.lineageFingerprint.value)
        assertEquals(keyR2Expected, keyR2.lineageFingerprint.value)
        assertEquals(authorityR1Expected, authR1.signerAuthorityFingerprint.value)
        assertEquals(authorityR2Expected, authR2.signerAuthorityFingerprint.value)
    }

    @Test
    fun `K01 K02 K03 K04 K05 K06 K07 K08 K09 K10 K11 K12 K13 K14 K15 K16 K17 key lineage is immutable canonical and fail closed`() {
        val service = governance()
        val keyId = syntheticUuid(101)
        val first = keyRevision(keyId, 1)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerKeyRevision(first))
        assertIs<GovernanceAppendResult.AlreadyApplied>(service.appendSignerKeyRevision(first))
        assertEquals(GovernanceAppendResult.Conflict, service.appendSignerKeyRevision(first.copy(reason = "Different reason")))

        val retired = keyRevision(keyId, 2, SignerKeyState.RETIRED, first)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerKeyRevision(retired))
        assertEquals(2, count("s2a_signer_key_revision"))
        assertEquals(GovernanceAppendResult.Conflict, service.appendSignerKeyRevision(
            keyRevision(keyId, 3, SignerKeyState.ACTIVE, retired)))

        assertFailsWith<IllegalArgumentException> {
            keyRevision(keyId, 3, SignerKeyState.REVOKED, retired).copy(supersedesRevision = 1)
        }
        assertEquals(GovernanceAppendResult.IntegrityFailure, service.appendSignerKeyRevision(
            keyRevision(syntheticUuid(102), 1).copy(lineageFingerprint = SignerKeyLineageFingerprint("0".repeat(64)))))

        val updateFailure = assertFailsWith<SQLException> {
            update("UPDATE s2a_signer_key_revision SET reason='Changed' WHERE organization_id=? AND signer_key_id=?", organization, keyId)
        }
        assertEquals("23514", updateFailure.sqlState)
        val deleteFailure = assertFailsWith<SQLException> {
            update("DELETE FROM s2a_signer_key_revision WHERE organization_id=? AND signer_key_id=?", organization, keyId)
        }
        assertEquals("23514", deleteFailure.sqlState)

        val futureKey = keyRevision(syntheticUuid(103), 1)
            .copy(effectiveAt = Instant.parse("2099-01-01T00:00:00.000000Z"))
            .withComputedFingerprint()
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerKeyRevision(futureKey))
        assertFailsWith<IllegalArgumentException> { keyRevision(syntheticUuid(104), 1).copy(reason = " padded") }
        assertFailsWith<IllegalArgumentException> { SignerPublicKeyInfo.parse(ByteArray(44)) }
    }

    @Test
    fun `A01 A02 A03 A04 A05 A06 A07 A08 A09 A10 A11 A12 A13 A14 A15 A16 A17 A18 A19 A20 A21 A22 A23 A24 authority lineage uses revision row identity`() {
        val service = governance()
        val key = keyRevision(syntheticUuid(201), 1)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerKeyRevision(key))
        val first = authorityRevision(syntheticUuid(211), 1, key)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerAuthorityRevision(first))
        assertIs<GovernanceAppendResult.AlreadyApplied>(service.appendSignerAuthorityRevision(first))
        assertEquals(GovernanceAppendResult.Conflict, service.appendSignerAuthorityRevision(first.copy(reason = "Different reason")))

        val second = authorityRevision(syntheticUuid(212), 2, key, SignerAuthorityState.DISABLED, first)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerAuthorityRevision(second))
        assertEquals(first.signerAuthorityId, second.supersedesSignerAuthorityId)
        assertNotEquals(first.signerAuthorityId, second.signerAuthorityId)
        assertEquals(2, count("s2a_signer_authority_revision"))

        val stale = authorityRevision(syntheticUuid(213), 3, key, SignerAuthorityState.ENABLED, second)
            .copy(supersedesSignerAuthorityId = first.signerAuthorityId).withComputedFingerprint()
        assertEquals(GovernanceAppendResult.Conflict, service.appendSignerAuthorityRevision(stale))
        val changedWindow = authorityRevision(syntheticUuid(214), 3, key, SignerAuthorityState.ENABLED, second)
            .copy(validUntil = validUntil.plusSeconds(1)).withComputedFingerprint()
        assertEquals(GovernanceAppendResult.Conflict, service.appendSignerAuthorityRevision(changedWindow))
        val mismatch = authorityRevision(syntheticUuid(215), 3, key, SignerAuthorityState.ENABLED, second)
            .copy(signerAuthorityFingerprint = SignerAuthorityFingerprint("0".repeat(64)))
        assertEquals(GovernanceAppendResult.IntegrityFailure, service.appendSignerAuthorityRevision(mismatch))

        assertEquals("23514", assertFailsWith<SQLException> {
            update("UPDATE s2a_signer_authority_revision SET reason='Changed' WHERE organization_id=?", organization)
        }.sqlState)
        assertEquals("23514", assertFailsWith<SQLException> {
            update("DELETE FROM s2a_signer_authority_revision WHERE organization_id=?", organization)
        }.sqlState)
    }

    @Test
    fun `S01 S02 S03 S04 S05 S06 S07 S08 S09 S10 S11 S12 S13 S14 S15 privileges expose only narrow governance append`() {
        for (role in listOf("PUBLIC", "flooow_approval_governance", "flooow_command_runtime", "flooow_command_issuer")) {
            for (table in listOf("s2a_signer_key_revision", "s2a_signer_authority_revision")) {
                for (privilege in listOf("INSERT", "UPDATE", "DELETE")) {
                    assertFalse(hasTablePrivilege(role, table, privilege), "$role unexpectedly has $privilege on $table")
                }
            }
        }
        assertTrue(hasFunctionPrivilege("flooow_approval_governance", KEY_FUNCTION_SIGNATURE, "EXECUTE"))
        assertTrue(hasFunctionPrivilege("flooow_approval_governance", AUTHORITY_FUNCTION_SIGNATURE, "EXECUTE"))
        for (role in listOf("PUBLIC", "flooow_command_runtime", "flooow_command_issuer")) {
            assertFalse(hasFunctionPrivilege(role, KEY_FUNCTION_SIGNATURE, "EXECUTE"))
            assertFalse(hasFunctionPrivilege(role, AUTHORITY_FUNCTION_SIGNATURE, "EXECUTE"))
        }
        roleDataSource("flooow_command_runtime").connection.use { connection ->
            assertEquals("42501", assertFailsWith<SQLException> {
                connection.createStatement().execute(
                    "SELECT * FROM public.s2a_append_signer_key_revision(NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL)"
                )
            }.sqlState)
        }
        assertEquals(0, countObjects(
            "SELECT count(*) FROM pg_auth_members WHERE roleid='flooow_approval_governance'::regrole OR member='flooow_approval_governance'::regrole"
        ))
    }

    @Test
    fun `S16 preexisting contaminated governance role fails closed while clean role is normalized`() {
        PostgreSQLContainer("postgres:18.4").use { contaminated ->
            contaminated.start()
            DriverManager.getConnection(contaminated.jdbcUrl, contaminated.username, contaminated.password).use { c ->
                c.createStatement().use { s ->
                    s.execute("CREATE ROLE flooow_approval_governance LOGIN INHERIT")
                    s.execute("CREATE ROLE v040_inbound NOLOGIN")
                    s.execute("CREATE ROLE v040_outbound NOLOGIN")
                    s.execute("GRANT flooow_approval_governance TO v040_inbound")
                    s.execute("GRANT v040_outbound TO flooow_approval_governance")
                }
            }
            assertFails {
                Flyway.configure().dataSource(contaminated.jdbcUrl, contaminated.username, contaminated.password).load().migrate()
            }
            DriverManager.getConnection(contaminated.jdbcUrl, contaminated.username, contaminated.password).use { c ->
                c.createStatement().use { s ->
                    s.executeQuery("SELECT count(*) FROM flyway_schema_history WHERE version='40' AND success").use { r ->
                        r.next()
                        assertEquals(0, r.getInt(1))
                    }
                    s.executeQuery("SELECT to_regprocedure('public.s2a_append_signer_key_revision(uuid,uuid,integer,uuid,text,bytea,text,text,timestamptz,timestamptz,integer,text,text,text,uuid)') IS NULL").use { r ->
                        r.next()
                        assertTrue(r.getBoolean(1))
                    }
                }
            }
        }

        PostgreSQLContainer("postgres:18.4").use { clean ->
            clean.start()
            DriverManager.getConnection(clean.jdbcUrl, clean.username, clean.password).use { c ->
                c.createStatement().use { s -> s.execute("CREATE ROLE flooow_approval_governance LOGIN INHERIT") }
            }
            Flyway.configure().dataSource(clean.jdbcUrl, clean.username, clean.password).load().migrate()
            DriverManager.getConnection(clean.jdbcUrl, clean.username, clean.password).use { c ->
                c.createStatement().use { s ->
                    s.executeQuery("SELECT count(*) FROM pg_roles WHERE rolname='flooow_approval_governance' AND NOT rolcanlogin AND NOT rolinherit").use { r ->
                        r.next()
                        assertEquals(1, r.getInt(1))
                    }
                    s.executeQuery("SELECT count(*) FROM pg_auth_members WHERE roleid='flooow_approval_governance'::regrole OR member='flooow_approval_governance'::regrole").use { r ->
                        r.next()
                        assertEquals(0, r.getInt(1))
                    }
                }
            }
        }
    }

    @Test
    fun `C01 C02 C03 C04 C05 adversarial concurrency and rollback are deterministic`() {
        val service = governance()

        // C01 + C05: different key successors compete for the same predecessor.
        val keyRoot = keyRevision(syntheticUuid(301), 1)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerKeyRevision(keyRoot))
        val keyA = keyRevision(keyRoot.signerKeyId.value, 2, SignerKeyState.RETIRED, keyRoot)
        val keyB = keyRevision(keyRoot.signerKeyId.value, 2, SignerKeyState.REVOKED, keyRoot)
        val keyResults = race(
            { governance().appendSignerKeyRevision(keyA) },
            { governance().appendSignerKeyRevision(keyB) }
        )
        assertEquals(1, keyResults.count { it is GovernanceAppendResult.Applied })
        assertEquals(1, keyResults.count { it == GovernanceAppendResult.Conflict })
        assertEquals(2, countForKey(keyRoot.signerKeyId.value))

        // C02 + C05: different authority successors compete for the same current leaf.
        val authorityKey = keyRevision(syntheticUuid(302), 1)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerKeyRevision(authorityKey))
        val authorityRoot = authorityRevision(syntheticUuid(311), 1, authorityKey)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerAuthorityRevision(authorityRoot))
        val authorityA = authorityRevision(syntheticUuid(312), 2, authorityKey, SignerAuthorityState.DISABLED, authorityRoot)
        val authorityB = authorityRevision(syntheticUuid(313), 2, authorityKey, SignerAuthorityState.DISABLED, authorityRoot)
        val authorityResults = race(
            { governance().appendSignerAuthorityRevision(authorityA) },
            { governance().appendSignerAuthorityRevision(authorityB) }
        )
        assertEquals(1, authorityResults.count { it is GovernanceAppendResult.Applied })
        assertEquals(1, authorityResults.count { it == GovernanceAppendResult.Conflict })
        assertEquals(2, countAuthorityScope(authorityKey.signerKeyId.value))

        // C03: key-only and authority mutation contend on the same key lock and must complete without deadlock.
        val contendedKey = keyRevision(syntheticUuid(303), 1)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerKeyRevision(contendedKey))
        val contendedSuccessor = keyRevision(contendedKey.signerKeyId.value, 2, SignerKeyState.RETIRED, contendedKey)
        val contendedAuthority = authorityRevision(syntheticUuid(314), 1, contendedKey)
        val completion = race(
            { governance().appendSignerKeyRevision(contendedSuccessor) },
            { governance().appendSignerAuthorityRevision(contendedAuthority) }
        )
        assertTrue(completion.all { it is GovernanceAppendResult.Applied })

        // C04: a DB-side lineage failure after transaction entry must leave no partial successor.
        val rollbackKey = keyRevision(syntheticUuid(304), 1)
        assertIs<GovernanceAppendResult.Applied>(service.appendSignerKeyRevision(rollbackKey))
        val invalidSuccessor = keyRevision(rollbackKey.signerKeyId.value, 2, SignerKeyState.RETIRED, rollbackKey)
            .copy(validFrom = validFrom.plusSeconds(1))
            .withComputedFingerprint()
        val before = countForKey(rollbackKey.signerKeyId.value)
        assertEquals(GovernanceAppendResult.Conflict, service.appendSignerKeyRevision(invalidSuccessor))
        assertEquals(before, countForKey(rollbackKey.signerKeyId.value))
    }

    @Test
    fun `exact replay remains one applied one already applied and one row`() {
        val key = keyRevision(syntheticUuid(401), 1)
        val keyResults = race(
            { governance().appendSignerKeyRevision(key) },
            { governance().appendSignerKeyRevision(key) }
        )
        assertEquals(1, keyResults.count { it is GovernanceAppendResult.Applied })
        assertEquals(1, keyResults.count { it is GovernanceAppendResult.AlreadyApplied })
        assertEquals(1, countForKey(key.signerKeyId.value))

        val authority = authorityRevision(syntheticUuid(411), 1, key)
        val authorityResults = race(
            { governance().appendSignerAuthorityRevision(authority) },
            { governance().appendSignerAuthorityRevision(authority) }
        )
        assertEquals(1, authorityResults.count { it is GovernanceAppendResult.Applied })
        assertEquals(1, authorityResults.count { it is GovernanceAppendResult.AlreadyApplied })
        assertEquals(1, countAuthorityScope(key.signerKeyId.value))
    }

    @Test
    fun `zero command authority proof and SQLSTATE meanings remain isolated`() {
        val forbidden = listOf(
            "command_principal",
            "command_credential_revision",
            "command_permission_grant",
            "command_authority_operation",
            "marketplace_transaction_identity_decision"
        )
        val before = forbidden.associateWith(::count)
        val key = keyRevision(syntheticUuid(501), 1)
        assertIs<GovernanceAppendResult.Applied>(governance().appendSignerKeyRevision(key))
        assertIs<GovernanceAppendResult.Applied>(
            governance().appendSignerAuthorityRevision(authorityRevision(syntheticUuid(511), 1, key))
        )
        assertEquals(before, forbidden.associateWith(::count))

        val foreign = keyRevision(syntheticUuid(502), 1)
            .copy(organizationId = OrganizationId.parse(syntheticUuid(99).toString()))
            .withComputedFingerprint()
        assertEquals(
            GovernanceAppendResult.GovernanceUnavailable,
            PostgresApprovalGovernance(roleDataSource("flooow_approval_governance")).appendSignerKeyRevision(foreign)
        )
    }

    private fun governance() = PostgresApprovalGovernance(roleDataSource("flooow_approval_governance"))

    private fun keyRevision(
        keyId: UUID,
        revision: Int,
        state: SignerKeyState = SignerKeyState.ACTIVE,
        predecessor: SignerKeyRevision? = null
    ): SignerKeyRevision {
        val initial = SignerKeyRevision(
            OrganizationId.parse(organization.toString()), SignerKeyId(keyId), revision, GovernanceSubjectId(subject),
            SignerPublicKeyInfo.parse(spkiHex.hex()), SignerKeyFingerprint(keyHash), state, validFrom,
            if (revision == 1) validFrom else validFrom.plusSeconds(revision.toLong()),
            predecessor?.revision, predecessor?.lineageFingerprint, SignerKeyLineageFingerprint("0".repeat(64)),
            "Synthetic governance", "v040-test", syntheticUuid(800000 + revision)
        )
        return initial.withComputedFingerprint()
    }

    private fun authorityRevision(
        id: UUID,
        revision: Int,
        key: SignerKeyRevision,
        state: SignerAuthorityState = SignerAuthorityState.ENABLED,
        predecessor: SignerAuthorityRevision? = null
    ): SignerAuthorityRevision {
        val initial = SignerAuthorityRevision(
            key.organizationId, SignerAuthorityId(id), revision, key.signerSubjectId,
            GovernanceInstitutionId(institution), SignerRole.S2A_FIELD_PROOF_APPROVER,
            key.signerKeyId, 1, key.signerKeyFingerprint, ApprovalAction.S2A_FIELD_PROOF_APPROVAL,
            SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE, validFrom, validUntil,
            state, predecessor?.signerAuthorityId, predecessor?.signerAuthorityFingerprint,
            SignerAuthorityFingerprint("0".repeat(64)), "Synthetic governance", "v040-test",
            GovernanceSourceId(source), syntheticUuid(810000 + revision)
        )
        return initial.withComputedFingerprint()
    }

    private fun dbKeyFingerprint(
        org: UUID,
        key: UUID,
        revision: Int,
        signerSubject: UUID,
        state: String,
        effectiveAt: Instant,
        supersedesRevision: Int?,
        predecessorFingerprint: String?
    ): String = connection().use { connection ->
        connection.prepareStatement(
            "SELECT public.s2a_signer_key_lineage_fingerprint(?,?,?,?,?,?,?,?,?,?,?,?)"
        ).use { statement ->
            val values = arrayOf<Any?>(
                org, key, revision, signerSubject, "Ed25519", spkiHex.hex(), keyHash, state,
                Timestamp.from(validFrom), Timestamp.from(effectiveAt), supersedesRevision, predecessorFingerprint
            )
            values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }
            statement.executeQuery().use { result ->
                result.next()
                result.getString(1)
            }
        }
    }

    private fun dbAuthorityFingerprint(
        org: UUID,
        authorityId: UUID,
        revision: Int,
        signerSubject: UUID,
        authorizingInstitution: UUID,
        keyId: UUID,
        state: String,
        approvalSource: UUID,
        predecessorAuthorityId: UUID?,
        predecessorFingerprint: String?
    ): String = connection().use { connection ->
        connection.prepareStatement(
            "SELECT public.s2a_signer_authority_fingerprint(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        ).use { statement ->
            val values = arrayOf<Any?>(
                org, authorityId, revision, signerSubject, authorizingInstitution,
                "S2A_FIELD_PROOF_APPROVER", keyId, 1, keyHash,
                "S2A_FIELD_PROOF_APPROVAL", "TRANSACTION_IDENTITY_DECISION_WRITE",
                Timestamp.from(validFrom), Timestamp.from(validUntil), state, approvalSource,
                predecessorAuthorityId, predecessorFingerprint
            )
            values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }
            statement.executeQuery().use { result ->
                result.next()
                result.getString(1)
            }
        }
    }

    private fun race(
        left: () -> GovernanceAppendResult,
        right: () -> GovernanceAppendResult
    ): List<GovernanceAppendResult> {
        val ready = CountDownLatch(2)
        val start = CountDownLatch(1)
        val executor = Executors.newFixedThreadPool(2)
        return try {
            val futures = listOf(left, right).map { operation ->
                executor.submit<GovernanceAppendResult> {
                    ready.countDown()
                    assertTrue(start.await(10, TimeUnit.SECONDS), "start barrier timed out")
                    operation()
                }
            }
            assertTrue(ready.await(10, TimeUnit.SECONDS), "workers did not reach barrier")
            start.countDown()
            futures.map { it.get(15, TimeUnit.SECONDS) }
        } finally {
            executor.shutdownNow()
            assertTrue(executor.awaitTermination(10, TimeUnit.SECONDS), "executor did not terminate")
        }
    }

    private fun countForKey(keyId: UUID): Int = connection().use { c ->
        c.prepareStatement(
            "SELECT count(*) FROM s2a_signer_key_revision WHERE organization_id=? AND signer_key_id=?"
        ).use { s ->
            s.setObject(1, organization)
            s.setObject(2, keyId)
            s.executeQuery().use { r -> r.next(); r.getInt(1) }
        }
    }

    private fun countAuthorityScope(keyId: UUID): Int = connection().use { c ->
        c.prepareStatement(
            "SELECT count(*) FROM s2a_signer_authority_revision WHERE organization_id=? AND signer_key_id=?"
        ).use { s ->
            s.setObject(1, organization)
            s.setObject(2, keyId)
            s.executeQuery().use { r -> r.next(); r.getInt(1) }
        }
    }

    private fun SignerKeyRevision.withComputedFingerprint() =
        copy(lineageFingerprint = ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(this))

    private fun SignerAuthorityRevision.withComputedFingerprint() =
        copy(signerAuthorityFingerprint = ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(this))

    private fun connection(): Connection = DriverManager.getConnection(db.jdbcUrl, db.username, db.password)

    private fun update(sql: String, vararg values: Any?) =
        connection().use { c ->
            c.prepareStatement(sql).use { s ->
                values.forEachIndexed { i, v -> s.setObject(i + 1, v) }
                s.executeUpdate()
            }
        }

    private fun count(table: String) = countObjects("SELECT count(*) FROM $table")

    private fun countObjects(sql: String) =
        connection().use { c ->
            c.createStatement().use { s ->
                s.executeQuery(sql).use { r -> r.next(); r.getInt(1) }
            }
        }

    private fun columnCount(table: String) =
        connection().use { c ->
            c.prepareStatement(
                "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name=?"
            ).use { s ->
                s.setString(1, table)
                s.executeQuery().use { r -> r.next(); r.getInt(1) }
            }
        }

    private fun hasTablePrivilege(role: String, table: String, privilege: String) =
        connection().use { c ->
            val sql = if (role == "PUBLIC") {
                "SELECT EXISTS (SELECT 1 FROM pg_class c, aclexplode(c.relacl) a WHERE c.oid=?::regclass AND a.grantee=0 AND a.privilege_type=?)"
            } else {
                "SELECT has_table_privilege(?, ?, ?)"
            }
            c.prepareStatement(sql).use { s ->
                if (role == "PUBLIC") {
                    s.setString(1, table)
                    s.setString(2, privilege)
                } else {
                    s.setString(1, role)
                    s.setString(2, table)
                    s.setString(3, privilege)
                }
                s.executeQuery().use { r -> r.next(); r.getBoolean(1) }
            }
        }

    private fun hasFunctionPrivilege(role: String, function: String, privilege: String) =
        connection().use { c ->
            val sql = if (role == "PUBLIC") {
                "SELECT EXISTS (SELECT 1 FROM pg_proc p, aclexplode(p.proacl) a WHERE p.oid=?::regprocedure AND a.grantee=0 AND a.privilege_type=?)"
            } else {
                "SELECT has_function_privilege(?, ?, ?)"
            }
            c.prepareStatement(sql).use { s ->
                if (role == "PUBLIC") {
                    s.setString(1, function)
                    s.setString(2, privilege)
                } else {
                    s.setString(1, role)
                    s.setString(2, function)
                    s.setString(3, privilege)
                }
                s.executeQuery().use { r -> r.next(); r.getBoolean(1) }
            }
        }

    private fun roleDataSource(role: String): DataSource {
        val base = PGSimpleDataSource()
        base.setURL(db.jdbcUrl)
        base.user = db.username
        base.password = db.password
        return object : DataSource {
            override fun getConnection(): Connection =
                base.connection.also { it.createStatement().use { s -> s.execute("SET ROLE $role") } }

            override fun getConnection(username: String, password: String) = getConnection()
            override fun getLogWriter(): PrintWriter? = base.logWriter
            override fun setLogWriter(out: PrintWriter?) { base.logWriter = out }
            override fun setLoginTimeout(seconds: Int) { base.loginTimeout = seconds }
            override fun getLoginTimeout() = base.loginTimeout
            override fun getParentLogger() = base.parentLogger
            override fun <T : Any?> unwrap(iface: Class<T>) = base.unwrap(iface)
            override fun isWrapperFor(iface: Class<*>) = base.isWrapperFor(iface)
        }
    }

    private fun syntheticUuid(slot: Int): UUID =
        UUID.fromString("70000000-0000-4000-8000-${slot.toString().padStart(12, '0')}")

    private fun String.hex() = chunked(2).map { it.toInt(16).toByte() }.toByteArray()

    private companion object {
        const val KEY_FUNCTION_SIGNATURE =
            "s2a_append_signer_key_revision(uuid,uuid,integer,uuid,text,bytea,text,text,timestamp with time zone,timestamp with time zone,integer,text,text,text,uuid)"
        const val AUTHORITY_FUNCTION_SIGNATURE =
            "s2a_append_signer_authority_revision(uuid,uuid,integer,uuid,uuid,text,uuid,integer,text,text,text,timestamp with time zone,timestamp with time zone,text,uuid,text,text,text,uuid,uuid)"
    }
}
