package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.organization.OrganizationId
import java.io.PrintWriter
import java.security.KeyFactory
import java.security.Signature
import java.security.spec.PKCS8EncodedKeySpec
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.sql.Timestamp
import java.time.Instant
import java.time.LocalDateTime
import java.util.Base64
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import javax.sql.DataSource
import kotlin.test.*
import org.flywaydb.core.Flyway
import org.flywaydb.core.api.MigrationVersion
import org.postgresql.ds.PGSimpleDataSource
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresAcceptedAttestationVerifierTest {
    private lateinit var db: PostgreSQLContainer

    @BeforeTest
    fun start() {
        db = PostgreSQLContainer("postgres:18.4")
        db.start()
        Flyway.configure().dataSource(db.jdbcUrl, db.username, db.password).target("042").load().migrate()
    }

    @AfterTest
    fun stop() {
        if (::db.isInitialized) db.stop()
    }

    @Test
    fun `V041 latest schema capabilities privileges immutability and hard wall are exact`() {
        assertEquals(16, columnCount("s2a_signer_key_revision"))
        assertEquals(21, columnCount("s2a_signer_authority_revision"))
        assertEquals(21, columnCount("s2a_accepted_attestation"))
        assertEquals(EXPECTED_COLUMNS, columnNames("s2a_accepted_attestation"))
        assertEquals(1, scalar("SELECT count(*) FROM pg_class WHERE relname='s2a_attestation_consumption'"))
        assertEquals(1, scalar("SELECT count(*) FROM pg_roles WHERE rolname='flooow_attestation_verifier' AND NOT rolcanlogin AND NOT rolinherit"))
        assertEquals(0, scalar("SELECT count(*) FROM pg_auth_members WHERE roleid='flooow_attestation_verifier'::regrole OR member='flooow_attestation_verifier'::regrole"))
        assertEquals(0, scalar("SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND tablename='s2a_accepted_attestation' AND indexname NOT IN (SELECT indexrelid::regclass::text FROM pg_index WHERE indrelid='public.s2a_accepted_attestation'::regclass AND indisprimary)"))

        assertNotNull(regprocedure(BEGIN_SIGNATURE))
        assertNotNull(regprocedure(PERSIST_SIGNATURE))
        assertNull(regprocedure("public.s2a_accept_verified_attestation(integer)"))
        assertEquals(29, functionInputCount("s2a_begin_attestation_verification"))
        assertEquals(38, functionInputCount("s2a_persist_attestation_verification_result"))
        assertEquals(16, functionReturnColumnCount("s2a_begin_attestation_verification"))
        assertEquals(7, functionReturnColumnCount("s2a_persist_attestation_verification_result"))
        assertSecurityDefiner("s2a_begin_attestation_verification")
        assertSecurityDefiner("s2a_persist_attestation_verification_result")

        for (role in listOf("PUBLIC", "flooow_command_runtime", "flooow_command_issuer", "flooow_approval_governance")) {
            assertFalse(hasFunctionPrivilege(role, BEGIN_SIGNATURE, "EXECUTE"), "$role can execute begin")
            assertFalse(hasFunctionPrivilege(role, PERSIST_SIGNATURE, "EXECUTE"), "$role can execute persist")
            for (privilege in listOf("INSERT", "UPDATE", "DELETE")) {
                assertFalse(hasTablePrivilege(role, "s2a_accepted_attestation", privilege), "$role has $privilege")
            }
        }
        assertTrue(hasFunctionPrivilege("flooow_attestation_verifier", BEGIN_SIGNATURE, "EXECUTE"))
        assertTrue(hasFunctionPrivilege("flooow_attestation_verifier", PERSIST_SIGNATURE, "EXECUTE"))
        assertFalse(hasTablePrivilege("flooow_attestation_verifier", "s2a_accepted_attestation", "INSERT"))

        val forbidden = listOf(
            "command_principal", "command_credential_revision", "command_permission_grant",
            "command_authority_operation", "marketplace_transaction_identity_decision",
            "marketplace_transaction_identity_head"
        )
        val before = forbidden.associateWith(::tableCount)
        installFixture()
        val verifier = verifier()
        val attestation = signed(manifest())
        val accepted = assertIs<AcceptedAttestationResult.Accepted>(verifier.verify(attestation))
        assertEquals(1, tableCount("s2a_accepted_attestation"))
        assertEquals(accepted.receipt.verifiedAt, accepted.receipt.recordedAt)

        val replay = assertIs<AcceptedAttestationResult.AlreadyAccepted>(verifier.verify(attestation))
        assertEquals(accepted.receipt, replay.receipt)
        assertEquals(1, tableCount("s2a_accepted_attestation"))

        val conflicting = signed(manifest().copy(provenance = "revision-7.3-conflicting-replay"))
        assertEquals(AcceptedAttestationResult.GovernanceConflict, verifier.verify(conflicting))
        assertEquals(1, tableCount("s2a_accepted_attestation"))

        val badSignature = attestation.signatureBytes().also { it[0] = (it[0].toInt() xor 1).toByte() }
        val invalid = SignedApprovalAttestation.parse(
            manifest().copy(manifestId = syntheticUuid(900)), "Ed25519", SignerKeyId(KEY_ID), KEY_FINGERPRINT,
            Base64.getUrlEncoder().withoutPadding().encodeToString(badSignature)
        )
        assertEquals(AcceptedAttestationResult.InvalidSignature, verifier.verify(invalid))
        assertEquals(1, tableCount("s2a_accepted_attestation"))

        update("UPDATE integration_organization SET status='SUSPENDED',updated_at=now() WHERE organization_id=?", ORGANIZATION)
        val historical = assertIs<AcceptedAttestationResult.AlreadyAccepted>(verifier.verify(attestation))
        assertEquals(accepted.receipt, historical.receipt)
        assertEquals(1, tableCount("s2a_accepted_attestation"))
        assertEquals(before, forbidden.associateWith(::tableCount))

        assertEquals("23514", assertFailsWith<SQLException> {
            update("UPDATE s2a_accepted_attestation SET algorithm_id='Ed25519'")
        }.sqlState)
        assertEquals("23514", assertFailsWith<SQLException> {
            update("DELETE FROM s2a_accepted_attestation")
        }.sqlState)
        assertEquals(1, tableCount("s2a_accepted_attestation"))
    }

    @Test
    fun `V041 identical concurrency serializes to one accepted one replay and one row`() {
        installFixture()
        val attestation = signed(manifest().copy(manifestId = syntheticUuid(901)))
        val ready = CountDownLatch(2)
        val release = CountDownLatch(1)
        val executor = Executors.newFixedThreadPool(2)
        try {
            val futures = List(2) {
                executor.submit<AcceptedAttestationResult> {
                    ready.countDown()
                    assertTrue(release.await(10, TimeUnit.SECONDS))
                    verifier().verify(attestation)
                }
            }
            assertTrue(ready.await(10, TimeUnit.SECONDS))
            release.countDown()
            val results = futures.map { it.get(20, TimeUnit.SECONDS) }
            assertEquals(1, results.count { it is AcceptedAttestationResult.Accepted })
            assertEquals(1, results.count { it is AcceptedAttestationResult.AlreadyAccepted })
            assertEquals(1, tableCount("s2a_accepted_attestation"))
        } finally {
            executor.shutdownNow()
            assertTrue(executor.awaitTermination(10, TimeUnit.SECONDS))
        }
    }

    @Test
    fun `V041 inactive organization and missing evidence fail closed with zero effect`() {
        installFixture()
        update("UPDATE integration_organization SET status='SUSPENDED',updated_at=now() WHERE organization_id=?", ORGANIZATION)
        assertEquals(AcceptedAttestationResult.ExpiredOrNotYetValid, verifier().verify(signed(manifest())))
        assertEquals(0, tableCount("s2a_accepted_attestation"))
        update("UPDATE integration_organization SET status='ACTIVE',updated_at=now() WHERE organization_id=?", ORGANIZATION)
        val missing = manifest().copy(marketplaceOrderId = MarketplaceOrderId.parse(syntheticUuid(777).toString()))
        assertEquals(AcceptedAttestationResult.ScopeMismatch, verifier().verify(signed(missing)))
        assertEquals(0, tableCount("s2a_accepted_attestation"))
    }

    @Test
    fun `V041 contaminated protected role graph rejects migration`() {
        PostgreSQLContainer("postgres:18.4").use { contaminated ->
            contaminated.start()
            Flyway.configure().dataSource(contaminated.jdbcUrl, contaminated.username, contaminated.password)
                .target(MigrationVersion.fromVersion("040")).load().migrate()
            DriverManager.getConnection(contaminated.jdbcUrl, contaminated.username, contaminated.password).use { c ->
                c.createStatement().use { s ->
                    s.execute("CREATE ROLE flooow_attestation_verifier NOLOGIN NOINHERIT")
                    s.execute("GRANT flooow_attestation_verifier TO flooow_approval_governance")
                }
            }
            assertFails {
                Flyway.configure().dataSource(contaminated.jdbcUrl, contaminated.username, contaminated.password).load().migrate()
            }
            DriverManager.getConnection(contaminated.jdbcUrl, contaminated.username, contaminated.password).use { c ->
                c.createStatement().use { s ->
                    s.executeQuery("SELECT count(*) FROM flyway_schema_history WHERE version='41' AND success").use { r ->
                        r.next(); assertEquals(0, r.getInt(1))
                    }
                    s.executeQuery("SELECT to_regclass('public.s2a_accepted_attestation') IS NULL").use { r ->
                        r.next(); assertTrue(r.getBoolean(1))
                    }
                }
            }
        }
    }

    @Test
    fun `V041 conflicting replay is classified before window source and signer key scope`() {
        installFixture()

        val baseline =
            manifest().copy(
                manifestId = syntheticUuid(910)
            )

        val accepted =
            assertIs<AcceptedAttestationResult.Accepted>(
                verifier().verify(signed(baseline))
            )

        val forbiddenBefore =
            forbiddenCounts()

        val provenanceConflict =
            signed(
                baseline.copy(
                    provenance = "revision-7.3-replay-conflict"
                )
            )

        assertEquals(
            AcceptedAttestationResult.GovernanceConflict,
            verifier().verify(provenanceConflict)
        )

        val approvalSourceConflict =
            signed(
                baseline.copy(
                    approvalSource =
                        GovernanceSourceId(
                            syntheticUuid(911)
                        )
                )
            )

        assertEquals(
            AcceptedAttestationResult.GovernanceConflict,
            verifier().verify(approvalSourceConflict)
        )

        val windowConflict =
            signed(
                baseline.copy(
                    approvalWindowStart =
                        VALID_UNTIL.minusSeconds(1),
                    approvalWindowEnd =
                        VALID_UNTIL
                )
            )

        assertEquals(
            AcceptedAttestationResult.GovernanceConflict,
            verifier().verify(windowConflict)
        )

        val signerKeyConflict =
            signed(
                baseline,
                signerKeyId =
                    SignerKeyId(
                        syntheticUuid(912)
                    )
            )

        assertEquals(
            AcceptedAttestationResult.GovernanceConflict,
            verifier().verify(signerKeyConflict)
        )

        val exactReplay =
            assertIs<AcceptedAttestationResult.AlreadyAccepted>(
                verifier().verify(
                    signed(baseline)
                )
            )

        assertEquals(
            accepted.receipt,
            exactReplay.receipt
        )

        assertEquals(
            1,
            tableCount(
                "s2a_accepted_attestation"
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )
    }

    @Test
    fun `V041 raw 23505 remains unclassified while persist owns bounded unique replay classification`() {
        installFixture()

        val persistDefinition =
            functionDefinition(
                "s2a_persist_attestation_verification_result"
            )

        assertContains(
            persistDefinition,
            "EXCEPTION"
        )

        assertContains(
            persistDefinition,
            "unique_violation"
        )

        assertContains(
            persistDefinition,
            "Conflicting concurrent replay"
        )

        replaceEvidenceFunctionWithFailure(
            "23505"
        )

        val failure =
            assertFailsWith<SQLException> {
                verifier().verify(
                    signed(
                        manifest().copy(
                            manifestId =
                                syntheticUuid(913)
                        )
                    )
                )
            }

        assertEquals(
            "23505",
            failure.sqlState
        )

        assertEquals(
            0,
            tableCount(
                "s2a_accepted_attestation"
            )
        )
    }

    @Test
    fun `V041 SQL canonical boundary keeps explicit whitespace guard`() {
        val beginDefinition =
            functionDefinition(
                "s2a_begin_attestation_verification"
            )

        assertContains(
            beginDefinition,
            "^[[:space:]]|[[:space:]]$"
        )
    }
    // PASS_B_ADVERSARIAL_MATRIX_V1

    @Test
    fun `V041 SQLSTATE DETAIL matrix is exact and unknown diagnostics rethrow`() {
        installFixture()
        val forbiddenBefore = forbiddenCounts()

        fun mapped(sqlState: String, detail: String?, slot: Int): AcceptedAttestationResult {
            replaceEvidenceFunctionWithFailure(sqlState, detail)
            return verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(slot)
                    )
                )
            )
        }

        assertEquals(
            AcceptedAttestationResult.GovernanceUnavailable,
            mapped("P0015", null, 1001)
        )

        assertEquals(
            AcceptedAttestationResult.GovernanceUnavailable,
            mapped("42501", null, 1002)
        )

        assertEquals(
            AcceptedAttestationResult.GovernanceConflict,
            mapped("P0016", null, 1003)
        )

        assertEquals(
            AcceptedAttestationResult.ScopeMismatch,
            mapped("P0017", "SCOPE_MISMATCH", 1004)
        )

        assertEquals(
            AcceptedAttestationResult.ExpiredOrNotYetValid,
            mapped("P0017", "EXPIRED_OR_NOT_YET_VALID", 1005)
        )

        assertEquals(
            AcceptedAttestationResult.UnsupportedCanonicalForm,
            mapped("P0018", "UNSUPPORTED_CANONICAL_FORM", 1006)
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            mapped("P0018", "INTEGRITY_FAILURE", 1007)
        )

        for ((sqlState, slot) in listOf(
            "23502" to 1008,
            "23503" to 1009,
            "23514" to 1010
        )) {
            assertEquals(
                AcceptedAttestationResult.IntegrityFailure,
                mapped(sqlState, null, slot)
            )
        }

        for ((sqlState, detail, slot) in listOf(
            Triple("P0017", null, 1011),
            Triple("P0017", "UNKNOWN_DETAIL", 1012),
            Triple("P0018", null, 1013),
            Triple("P0018", "UNKNOWN_DETAIL", 1014),
            Triple("23505", null, 1015)
        )) {
            replaceEvidenceFunctionWithFailure(sqlState, detail)

            val failure =
                assertFailsWith<SQLException> {
                    verifier().verify(
                        signed(
                            manifest().copy(
                                manifestId = syntheticUuid(slot)
                            )
                        )
                    )
                }

            assertEquals(sqlState, failure.sqlState)
        }

        var slot = 1020

        for (sqlState in listOf(
            "P0010",
            "P0011",
            "P0012",
            "P0013",
            "P0014"
        )) {
            replaceEvidenceFunctionWithFailure(sqlState, null)

            val failure =
                assertFailsWith<SQLException> {
                    verifier().verify(
                        signed(
                            manifest().copy(
                                manifestId = syntheticUuid(slot++)
                            )
                        )
                    )
                }

            assertEquals(sqlState, failure.sqlState)
        }

        assertEquals(
            0,
            tableCount("s2a_accepted_attestation")
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )
    }

    @Test
    fun `V041 signer key temporal matrix is fail closed`() {
        installFixture()

        var forbiddenBefore =
            forbiddenCounts()

        appendKeySuccessor(
            SignerKeyState.ACTIVE,
            VALID_UNTIL.minusSeconds(60)
        )

        assertIs<AcceptedAttestationResult.Accepted>(
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1030)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        appendKeySuccessor(
            SignerKeyState.ACTIVE,
            VALID_FROM.plusSeconds(1)
        )

        assertEquals(
            AcceptedAttestationResult.ScopeMismatch,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1031)
                    )
                )
            )
        )

        assertEquals(
            0,
            tableCount("s2a_accepted_attestation")
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        appendKeySuccessor(
            SignerKeyState.REVOKED,
            VALID_FROM.plusSeconds(1)
        )

        assertEquals(
            AcceptedAttestationResult.ExpiredOrNotYetValid,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1032)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        appendKeySuccessor(
            SignerKeyState.ACTIVE,
            VALID_FROM
        )

        assertEquals(
            AcceptedAttestationResult.GovernanceConflict,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1033)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        rewriteRootKeyEffectiveAt(
            VALID_UNTIL.minusSeconds(60)
        )

        assertEquals(
            AcceptedAttestationResult.ExpiredOrNotYetValid,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1034)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )
    }

    @Test
    fun `V041 signer authority matrix is fail closed`() {
        installFixture()

        var forbiddenBefore =
            forbiddenCounts()

        removeSignerAuthority()

        assertEquals(
            AcceptedAttestationResult.GovernanceUnavailable,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1040)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        appendAuthoritySuccessor(
            SignerAuthorityState.DISABLED
        )

        assertEquals(
            AcceptedAttestationResult.ExpiredOrNotYetValid,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1041)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        rewriteRootAuthority(
            VALID_UNTIL.minusSeconds(120),
            VALID_UNTIL,
            SignerAuthorityState.ENABLED
        )

        assertEquals(
            AcceptedAttestationResult.ExpiredOrNotYetValid,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1042)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        rewriteRootAuthority(
            VALID_FROM,
            VALID_FROM.plusSeconds(60),
            SignerAuthorityState.ENABLED
        )

        assertEquals(
            AcceptedAttestationResult.ExpiredOrNotYetValid,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1043)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        assertEquals(
            AcceptedAttestationResult.ScopeMismatch,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1044),
                        approvalSource =
                            GovernanceSourceId(
                                syntheticUuid(1045)
                            )
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        val wrongFingerprint =
            SignerKeyFingerprint(
                "0".repeat(64)
            )

        assertEquals(
            AcceptedAttestationResult.ScopeMismatch,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1046)
                    ),
                    signerKeyFingerprint =
                        wrongFingerprint
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        val beginDefinition =
            functionDefinition(
                "s2a_begin_attestation_verification"
            )

        assertContains(
            beginDefinition,
            "authority_leaf_count>1"
        )

        assertContains(
            beginDefinition,
            "Authority ambiguous"
        )

        assertContains(
            beginDefinition,
            "leaf_count<>1"
        )

        assertContains(
            beginDefinition,
            "Key lineage conflict"
        )
    }

    @Test
    fun `V041 Mercado Livre evidence selection and all row integrity are exact`() {
        installFixture()

        var forbiddenBefore =
            forbiddenCounts()

        addMlOccurrence(
            ordinal = 2,
            outcome = "DUPLICATE"
        )

        assertIs<AcceptedAttestationResult.Accepted>(
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1050)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        addMlOccurrence(
            ordinal = 0,
            outcome = "DUPLICATE"
        )

        val earlierFingerprint =
            mlEvidenceFingerprint(
                ordinal = 0,
                outcome = "DUPLICATE"
            )

        assertIs<AcceptedAttestationResult.Accepted>(
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1051),
                        evidenceBindingFingerprint =
                            earlierFingerprint
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        addMlOccurrence(
            ordinal = 0,
            outcome = "DUPLICATE"
        )

        adminMutation(
            "integration_mercado_livre_order_source_observation",
            """
            UPDATE public.integration_mercado_livre_order_source_observation
            SET external_order_ref='MLB-CORRUPT-NONSELECTED'
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
              AND record_ordinal=1
            """.trimIndent(),
            ORGANIZATION,
            ML_CONNECTION,
            ML_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1052),
                        evidenceBindingFingerprint =
                            mlEvidenceFingerprint(
                                ordinal = 0,
                                outcome = "DUPLICATE"
                            )
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "marketplace_order_identity_registry",
            """
            DELETE FROM public.marketplace_order_identity_registry
            WHERE organization_id=?
              AND marketplace_order_id=?
            """.trimIndent(),
            ORGANIZATION,
            MARKETPLACE_ORDER
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1053)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_mercado_livre_order_source_observation",
            """
            DELETE FROM public.integration_mercado_livre_order_source_observation
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
              AND record_ordinal=1
            """.trimIndent(),
            ORGANIZATION,
            ML_CONNECTION,
            ML_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1054)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_mercado_livre_order_source_observation",
            """
            UPDATE public.integration_mercado_livre_order_source_observation
            SET external_order_ref='MLB-DIFFERENT'
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
              AND record_ordinal=1
            """.trimIndent(),
            ORGANIZATION,
            ML_CONNECTION,
            ML_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1055)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_mercado_livre_order_source_observation",
            """
            UPDATE public.integration_mercado_livre_order_source_observation
            SET currency='USD'
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
              AND record_ordinal=1
            """.trimIndent(),
            ORGANIZATION,
            ML_CONNECTION,
            ML_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1056)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )
    }

    @Test
    fun `V041 Omie V3 evidence integrity conflict and deterministic selection are exact`() {
        installFixture()

        var forbiddenBefore =
            forbiddenCounts()

        assertEquals(
            AcceptedAttestationResult.ScopeMismatch,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1060),
                        sourceOrderReference =
                            "SO-NOT-PRESENT"
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_omie_transaction_evidence_v3",
            """
            DELETE FROM public.integration_omie_transaction_evidence_v3
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
              AND record_ordinal=1
            """.trimIndent(),
            ORGANIZATION,
            OMIE_CONNECTION,
            OMIE_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1061)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_connector_page_commit",
            """
            DELETE FROM public.integration_connector_page_commit
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
            """.trimIndent(),
            ORGANIZATION,
            OMIE_CONNECTION,
            OMIE_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1062)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_connector_progress",
            """
            DELETE FROM public.integration_connector_progress
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
            """.trimIndent(),
            ORGANIZATION,
            OMIE_CONNECTION,
            OMIE_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1063)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        setOmiePageCount(3)

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1064)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_omie_transaction_evidence_v3",
            """
            UPDATE public.integration_omie_transaction_evidence_v3
            SET provider_created_local=NULL,
                provider_modified_local=NULL
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
              AND record_ordinal=1
            """.trimIndent(),
            ORGANIZATION,
            OMIE_CONNECTION,
            OMIE_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1065)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_omie_transaction_evidence_v3",
            """
            UPDATE public.integration_omie_transaction_evidence_v3
            SET provider_modified_local='2026-09-25T11:00:00.000000'
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
              AND record_ordinal=1
            """.trimIndent(),
            ORGANIZATION,
            OMIE_CONNECTION,
            OMIE_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.IntegrityFailure,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1066)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        addOmieTargetOccurrence(
            ordinal = 2,
            integrationReference = "INT-2026-0001",
            currency = null,
            providerRevision =
                LocalDateTime.parse(
                    "2026-09-25T11:59:59.123456"
                ),
            semanticFingerprint =
                "ac".repeat(32)
        )

        assertEquals(
            AcceptedAttestationResult.GovernanceConflict,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1067)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        addOmieTargetOccurrence(
            ordinal = 2,
            integrationReference = "INT-2026-0001",
            currency = null,
            providerRevision =
                LocalDateTime.parse(
                    "2026-09-25T11:59:59.123456"
                ),
            semanticFingerprint =
                "ab".repeat(32)
        )

        assertIs<AcceptedAttestationResult.Accepted>(
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1068)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        assertEquals(
            AcceptedAttestationResult.ScopeMismatch,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1069),
                        integrationReference =
                            "INT-DIFFERENT"
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )

        resetDatabase()
        installFixture()

        forbiddenBefore =
            forbiddenCounts()

        adminMutation(
            "integration_omie_transaction_evidence",
            """
            UPDATE public.integration_omie_transaction_evidence
            SET currency='USD'
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
              AND record_ordinal=1
            """.trimIndent(),
            ORGANIZATION,
            OMIE_CONNECTION,
            OMIE_CAPABILITY
        )

        assertEquals(
            AcceptedAttestationResult.GovernanceConflict,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1070)
                    )
                )
            )
        )

        assertEquals(
            forbiddenBefore,
            forbiddenCounts()
        )
    }

    @Test
    fun `V041 invalid JCA verification never reaches persistence`() {
        installFixture()

        val durableBefore =
            cryptoEffectCounts()

        update(
            "REVOKE EXECUTE ON FUNCTION $PERSIST_SIGNATURE FROM flooow_attestation_verifier"
        )

        val valid =
            signed(
                manifest().copy(
                    manifestId = syntheticUuid(1080)
                )
            )

        val corruptedBytes =
            valid.signatureBytes().also {
                it[0] =
                    (it[0].toInt() xor 1).toByte()
            }

        val corrupted =
            SignedApprovalAttestation.parse(
                valid.manifest,
                valid.algorithmId,
                valid.signerKeyId,
                valid.signerKeyFingerprint,
                Base64.getUrlEncoder()
                    .withoutPadding()
                    .encodeToString(corruptedBytes)
            )

        assertEquals(
            AcceptedAttestationResult.InvalidSignature,
            verifier().verify(corrupted)
        )

        assertEquals(
            AcceptedAttestationResult.InvalidSignature,
            verifier().verify(
                signed(
                    manifest().copy(
                        manifestId = syntheticUuid(1081)
                    ),
                    privateSeedHex =
                        "00".repeat(32)
                )
            )
        )

        val originalPreimage =
            signed(
                manifest().copy(
                    manifestId = syntheticUuid(1082)
                )
            )
        val changedPreimage =
            SignedApprovalAttestation.parse(
                originalPreimage.manifest.copy(reason = "changed canonical preimage"),
                originalPreimage.algorithmId,
                originalPreimage.signerKeyId,
                originalPreimage.signerKeyFingerprint,
                Base64.getUrlEncoder().withoutPadding().encodeToString(originalPreimage.signatureBytes())
            )

        assertEquals(
            AcceptedAttestationResult.InvalidSignature,
            verifier().verify(changedPreimage)
        )
        assertEquals(
            0,
            tableCount(
                "s2a_accepted_attestation"
            )
        )

        assertEquals(
            durableBefore,
            cryptoEffectCounts()
        )
    }

    @Test
    fun `V041 conflicting concurrent submissions accept at most one immutable artifact`() {
        installFixture()

        val forbiddenBefore =
            forbiddenCounts()

        val base =
            manifest().copy(
                manifestId = syntheticUuid(1090)
            )

        val left =
            signed(base)

        val right =
            signed(
                base.copy(
                    provenance =
                        "revision-7.3-concurrent-conflict"
                )
            )

        val ready =
            CountDownLatch(2)

        val release =
            CountDownLatch(1)

        val executor =
            Executors.newFixedThreadPool(2)

        try {
            val futures =
                listOf(left, right).map { attestation ->
                    executor.submit<AcceptedAttestationResult> {
                        ready.countDown()

                        assertTrue(
                            release.await(
                                10,
                                TimeUnit.SECONDS
                            )
                        )

                        verifier().verify(attestation)
                    }
                }

            assertTrue(
                ready.await(
                    10,
                    TimeUnit.SECONDS
                )
            )

            release.countDown()

            val results =
                futures.map {
                    it.get(
                        30,
                        TimeUnit.SECONDS
                    )
                }

            assertEquals(
                1,
                results.count {
                    it is AcceptedAttestationResult.Accepted
                }
            )

            assertEquals(
                1,
                results.count {
                    it == AcceptedAttestationResult.GovernanceConflict
                }
            )

            assertEquals(
                1,
                tableCount(
                    "s2a_accepted_attestation"
                )
            )

            assertEquals(
                forbiddenBefore,
                forbiddenCounts()
            )
        }
        finally {
            executor.shutdownNow()

            assertTrue(
                executor.awaitTermination(
                    10,
                    TimeUnit.SECONDS
                )
            )
        }
    }

    @Test
    fun `V041 organization shared lock wins disable race and disable waits`() {
        installFixture()

        val forbiddenBefore =
            forbiddenCounts()

        val target =
            manifest().copy(
                manifestId = syntheticUuid(1100)
            )

        val resource =
            "s2a-attestation/manifest/1:$ORGANIZATION:${target.manifestId}"

        val blocker =
            connection()

        blocker.autoCommit = false

        blocker.prepareStatement(
            """
            SELECT pg_catalog.pg_advisory_xact_lock(
                pg_catalog.hashtextextended(?,0)
            )
            """.trimIndent()
        ).use {
            it.setString(1, resource)
            it.execute()
        }

        val executor =
            Executors.newFixedThreadPool(2)

        var blockerReleased =
            false

        try {
            val verification =
                executor.submit<AcceptedAttestationResult> {
                    verifier().verify(
                        signed(target)
                    )
                }

            assertTrue(
                awaitCondition(10_000) {
                    scalar(
                        """
                        SELECT count(*)
                        FROM pg_catalog.pg_locks
                        WHERE locktype='advisory'
                          AND NOT granted
                        """.trimIndent()
                    ) > 0
                }
            )

            val disable =
                executor.submit<Boolean> {
                    connection().use { c ->
                        c.autoCommit = false

                        execute(
                            c,
                            """
                            UPDATE public.integration_organization
                            SET status='SUSPENDED',
                                updated_at=now()
                            WHERE organization_id=?
                            """.trimIndent(),
                            ORGANIZATION
                        )

                        c.commit()
                    }

                    true
                }

            Thread.sleep(350)

            assertFalse(
                disable.isDone,
                "organization disable must wait behind V041 FOR SHARE"
            )

            blocker.commit()
            blocker.close()

            blockerReleased =
                true

            assertIs<AcceptedAttestationResult.Accepted>(
                verification.get(
                    30,
                    TimeUnit.SECONDS
                )
            )

            assertTrue(
                disable.get(
                    30,
                    TimeUnit.SECONDS
                )
            )

            assertEquals(
                "SUSPENDED",
                organizationStatus()
            )

            assertEquals(
                1,
                tableCount(
                    "s2a_accepted_attestation"
                )
            )

            assertEquals(
                forbiddenBefore,
                forbiddenCounts()
            )
        }
        finally {
            if (!blockerReleased) {
                runCatching {
                    blocker.rollback()
                }

                runCatching {
                    blocker.close()
                }
            }

            executor.shutdownNow()

            assertTrue(
                executor.awaitTermination(
                    10,
                    TimeUnit.SECONDS
                )
            )
        }
    }

    @Test
    fun `V041 protected role graph rejects outbound verifier membership`() {
        PostgreSQLContainer("postgres:18.4").use { contaminated ->
            contaminated.start()

            Flyway.configure()
                .dataSource(
                    contaminated.jdbcUrl,
                    contaminated.username,
                    contaminated.password
                )
                .target(
                    MigrationVersion.fromVersion("040")
                )
                .load()
                .migrate()

            DriverManager.getConnection(
                contaminated.jdbcUrl,
                contaminated.username,
                contaminated.password
            ).use { c ->
                c.createStatement().use { s ->
                    s.execute(
                        "CREATE ROLE flooow_attestation_verifier NOLOGIN NOINHERIT"
                    )

                    s.execute(
                        "GRANT flooow_approval_governance TO flooow_attestation_verifier"
                    )
                }
            }

            assertFails {
                Flyway.configure()
                    .dataSource(
                        contaminated.jdbcUrl,
                        contaminated.username,
                        contaminated.password
                    )
                    .load()
                    .migrate()
            }

            DriverManager.getConnection(
                contaminated.jdbcUrl,
                contaminated.username,
                contaminated.password
            ).use { c ->
                c.createStatement().use { s ->
                    s.executeQuery(
                        """
                        SELECT count(*)
                        FROM flyway_schema_history
                        WHERE version='41'
                          AND success
                        """.trimIndent()
                    ).use { rows ->
                        rows.next()
                        assertEquals(
                            0,
                            rows.getInt(1)
                        )
                    }
                }
            }
        }
    }
    private fun installFixture() {
        val now = Timestamp.from(Instant.parse("2026-09-25T12:00:00Z"))
        update("INSERT INTO integration_organization VALUES (?,'ACTIVE',?,?)", ORGANIZATION, now, now)
        update("INSERT INTO integration_connection VALUES (?,?,?,'OAUTH2_AUTHORIZATION_CODE','REVOKED',1,?,?)", ORGANIZATION, ML_CONNECTION, "br.com.mercadolivre", now, now)
        update("INSERT INTO integration_connection VALUES (?,?,?,'STATIC_API_CREDENTIAL','SUSPENDED',1,?,?)", ORGANIZATION, OMIE_CONNECTION, "omie", now, now)

        connection().use { c ->
            c.autoCommit = false
            page(c, ML_CONNECTION, ML_CAPABILITY, 1, 2, 1)
            execute(c, """INSERT INTO integration_mercado_livre_order_source_observation
                (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,
                provider_status,date_created,date_last_updated,currency,total_amount,observed_at)
                VALUES (?,?,?,1,1,'MLB-123456789','paid',?,?,'BRL',58.28,?)""",
                ORGANIZATION, ML_CONNECTION, ML_CAPABILITY, now, now, now)
            execute(c, "INSERT INTO marketplace_order_identity_registry VALUES (?,'mercado-livre','MLB-123456789',?,'BRL',?,?,?,?,1)",
                ORGANIZATION, MARKETPLACE_ORDER, now, ML_CONNECTION, ML_CAPABILITY, 1L)
            execute(c, "INSERT INTO marketplace_order_occurrence_source_promotion VALUES (?,?,?,1,1,?,'PROMOTED',?)",
                ORGANIZATION, ML_CONNECTION, ML_CAPABILITY, MARKETPLACE_ORDER, now)

            page(c, OMIE_CONNECTION, OMIE_CAPABILITY, 1, 2, 2)
            omie(c, 0, "OTHER-SYNTHETIC", null, "BRL", LocalDateTime.parse("2026-09-24T10:00:00.000000"), "cd".repeat(32), now)
            omie(c, 1, "SO-2026-0001", "INT-2026-0001", null, LocalDateTime.parse("2026-09-25T11:59:59.123456"), "ab".repeat(32), now)
            c.commit()
        }

        val key = SignerKeyRevision(
            OrganizationId.parse(ORGANIZATION.toString()), SignerKeyId(KEY_ID), 1, GovernanceSubjectId(SUBJECT),
            SignerPublicKeyInfo.parse(SPKI_HEX.hex()), KEY_FINGERPRINT, SignerKeyState.ACTIVE,
            VALID_FROM, VALID_FROM, null, null, SignerKeyLineageFingerprint("0".repeat(64)),
            "Synthetic V041 key", "v041-test", syntheticUuid(801)
        ).let { it.copy(lineageFingerprint = ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(it)) }
        assertIs<GovernanceAppendResult.Applied>(governance().appendSignerKeyRevision(key))
        val authority = SignerAuthorityRevision(
            key.organizationId, SignerAuthorityId(AUTHORITY), 1, key.signerSubjectId,
            GovernanceInstitutionId(INSTITUTION), SignerRole.S2A_FIELD_PROOF_APPROVER, key.signerKeyId, 1,
            key.signerKeyFingerprint, ApprovalAction.S2A_FIELD_PROOF_APPROVAL,
            SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE, VALID_FROM, VALID_UNTIL,
            SignerAuthorityState.ENABLED, null, null, SignerAuthorityFingerprint("0".repeat(64)),
            "Synthetic V041 authority", "v041-test", GovernanceSourceId(APPROVAL_SOURCE), syntheticUuid(802)
        ).let { it.copy(signerAuthorityFingerprint = ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(it)) }
        assertIs<GovernanceAppendResult.Applied>(governance().appendSignerAuthorityRevision(authority))
    }

    private fun manifest() = ApprovalManifest(
        1, MANIFEST, OrganizationId.parse(ORGANIZATION.toString()), ML_CONNECTION, OMIE_CONNECTION,
        "SO-2026-0001", "INT-2026-0001", MarketplaceOrderId.parse(MARKETPLACE_ORDER.toString()),
        SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE, GovernanceSubjectId(SUBJECT),
        GovernanceSourceId(APPROVAL_SOURCE), VALID_FROM, VALID_UNTIL, GovernanceSubjectId(syntheticUuid(11)),
        GovernanceSubjectId(syntheticUuid(12)), CredentialDeliveryMethod.PROTECTED_TTY_ONE_TIME,
        GovernanceSubjectId(syntheticUuid(13)), ImmediateRevocationPolicy.SEPARATE_APPROVAL_REQUIRED,
        "S2A field proof approval", "revision-7.3-synthetic-test", syntheticUuid(14), EVIDENCE_FINGERPRINT
    )

    private fun signed(
        manifest: ApprovalManifest,
        signerKeyId: SignerKeyId = SignerKeyId(KEY_ID),
        signerKeyFingerprint: SignerKeyFingerprint = KEY_FINGERPRINT,
        privateSeedHex: String = SEED_HEX
    ): SignedApprovalAttestation {
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest)
        val preimage = ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes(
            "Ed25519",
            signerKeyId,
            signerKeyFingerprint,
            ApprovalManifestCanonicalCodec.manifestDigest(canonical)
        )
        val privateKey = KeyFactory.getInstance("Ed25519").generatePrivate(
            PKCS8EncodedKeySpec((PKCS8_PREFIX + privateSeedHex).hex())
        )
        val signature = Signature.getInstance("Ed25519").run {
            initSign(privateKey)
            update(preimage)
            sign()
        }
        return SignedApprovalAttestation.parse(
            manifest,
            "Ed25519",
            signerKeyId,
            signerKeyFingerprint,
            Base64.getUrlEncoder().withoutPadding().encodeToString(signature)
        )
    }

    private fun page(c: Connection, id: UUID, capability: String, input: Long, count: Int, marker: Int) {
        execute(c, "INSERT INTO integration_connector_progress VALUES (?,?,?,?,?,false,?,?)",
            ORGANIZATION, id, capability, input + 1, byteArrayOf(marker.toByte()), Timestamp.from(VALID_FROM), Timestamp.from(VALID_FROM))
        execute(c, "INSERT INTO integration_connector_page_commit VALUES (?,?,?,?,?,?,false,?,?)",
            ORGANIZATION, id, capability, input, ByteArray(32) { marker.toByte() }, count, Timestamp.from(VALID_FROM), Timestamp.from(VALID_FROM))
    }

    private fun omie(c: Connection, ordinal: Int, order: String, integration: String?, currency: String?,
                     revision: LocalDateTime, fingerprint: String, observed: Timestamp) {
        execute(c, """INSERT INTO integration_omie_transaction_evidence
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,source_order_ref,
            source_integration_ref,currency,total_amount,product_refs,observed_at,source_fingerprint)
            VALUES (?,?,?,1,?,?,?,?,58.28,'[]',?,?)""",
            ORGANIZATION, OMIE_CONNECTION, OMIE_CAPABILITY, ordinal, order, integration, currency, observed, "ef".repeat(32))
        execute(c, """INSERT INTO integration_omie_transaction_evidence_v3
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,provider_created_local,
            additional_order_totals,semantic_fingerprint_version,source_evidence_semantic_fingerprint)
            VALUES (?,?,?,1,?,?,'{}',1,?)""",
            ORGANIZATION, OMIE_CONNECTION, OMIE_CAPABILITY, ordinal, revision, fingerprint)
    }

    private fun forbiddenCounts() =
        listOf(
            "command_principal",
            "command_credential_revision",
            "command_permission_grant",
            "command_authority_operation",
            "marketplace_transaction_identity_decision",
            "marketplace_transaction_identity_head"
        ).associateWith(::tableCount)

    private fun cryptoEffectCounts() =
        listOf(
            "s2a_accepted_attestation",
            "s2a_attestation_consumption",
            "command_principal",
            "command_credential_revision",
            "command_permission_grant",
            "command_authority_operation",
            "marketplace_transaction_identity_decision",
            "marketplace_transaction_identity_head"
        ).associateWith(::tableCount)
    private fun functionDefinition(name: String): String =
        connection().use { c ->
            c.prepareStatement(
                """
                SELECT pg_get_functiondef(p.oid)
                FROM pg_proc p
                WHERE p.pronamespace='public'::regnamespace
                  AND p.proname=?
                """.trimIndent()
            ).use { statement ->
                statement.setString(1, name)
                statement.executeQuery().use { rows ->
                    check(rows.next()) {
                        "Function not found: $name"
                    }
                    rows.getString(1)
                }
            }
        }

    private fun replaceEvidenceFunctionWithFailure(
        sqlState: String
    ) {
        val ddl =
            """
            CREATE OR REPLACE FUNCTION public.s2a_v041_evidence_fingerprint(
                p_organization_id uuid,
                p_marketplace_order_id uuid,
                p_mercado_livre_connection_id uuid,
                p_omie_connection_id uuid,
                p_source_order_reference text,
                p_integration_reference text
            )
            RETURNS text
            LANGUAGE plpgsql
            SECURITY DEFINER
            SET search_path=pg_catalog,pg_temp
            AS ${'$'}${'$'}
            BEGIN
                RAISE EXCEPTION 'synthetic V041 SQLSTATE'
                    USING ERRCODE='$sqlState';
            END
            ${'$'}${'$'};
            """.trimIndent()

        connection().use { c ->
            c.createStatement().use {
                it.execute(ddl)
            }
        }
    }
    // PASS_B_ADVERSARIAL_HELPERS_V1

    private fun resetDatabase() {
        if (::db.isInitialized) {
            db.stop()
        }

        db =
            PostgreSQLContainer(
                "postgres:18.4"
            )

        db.start()

        Flyway.configure()
            .dataSource(
                db.jdbcUrl,
                db.username,
                db.password
            )
            .target("042")
            .load()
            .migrate()
    }

    private fun keyRevisionOne(): SignerKeyRevision {
        val draft =
            SignerKeyRevision(
                OrganizationId.parse(
                    ORGANIZATION.toString()
                ),
                SignerKeyId(KEY_ID),
                1,
                GovernanceSubjectId(SUBJECT),
                SignerPublicKeyInfo.parse(
                    SPKI_HEX.hex()
                ),
                KEY_FINGERPRINT,
                SignerKeyState.ACTIVE,
                VALID_FROM,
                VALID_FROM,
                null,
                null,
                SignerKeyLineageFingerprint(
                    "0".repeat(64)
                ),
                "Synthetic V041 key",
                "v041-test",
                syntheticUuid(801)
            )

        return draft.copy(
            lineageFingerprint =
                ApprovalGovernanceFingerprintCodec
                    .signerKeyFingerprint(draft)
        )
    }

    private fun appendKeySuccessor(
        state: SignerKeyState,
        effectiveAt: Instant
    ): SignerKeyRevision {
        val predecessor =
            keyRevisionOne()

        val draft =
            SignerKeyRevision(
                predecessor.organizationId,
                predecessor.signerKeyId,
                2,
                predecessor.signerSubjectId,
                predecessor.subjectPublicKeyInfo,
                predecessor.signerKeyFingerprint,
                state,
                predecessor.validFrom,
                effectiveAt,
                1,
                predecessor.lineageFingerprint,
                SignerKeyLineageFingerprint(
                    "0".repeat(64)
                ),
                "Synthetic V041 key successor",
                "v041-pass-b",
                syntheticUuid(820)
            )

        val successor =
            draft.copy(
                lineageFingerprint =
                    ApprovalGovernanceFingerprintCodec
                        .signerKeyFingerprint(draft)
            )

        assertIs<GovernanceAppendResult.Applied>(
            governance().appendSignerKeyRevision(
                successor
            )
        )

        return successor
    }

    private fun authorityRevisionOne(): SignerAuthorityRevision {
        val draft =
            SignerAuthorityRevision(
                OrganizationId.parse(
                    ORGANIZATION.toString()
                ),
                SignerAuthorityId(AUTHORITY),
                1,
                GovernanceSubjectId(SUBJECT),
                GovernanceInstitutionId(
                    INSTITUTION
                ),
                SignerRole.S2A_FIELD_PROOF_APPROVER,
                SignerKeyId(KEY_ID),
                1,
                KEY_FINGERPRINT,
                ApprovalAction.S2A_FIELD_PROOF_APPROVAL,
                SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,
                VALID_FROM,
                VALID_UNTIL,
                SignerAuthorityState.ENABLED,
                null,
                null,
                SignerAuthorityFingerprint(
                    "0".repeat(64)
                ),
                "Synthetic V041 authority",
                "v041-test",
                GovernanceSourceId(
                    APPROVAL_SOURCE
                ),
                syntheticUuid(802)
            )

        return draft.copy(
            signerAuthorityFingerprint =
                ApprovalGovernanceFingerprintCodec
                    .signerAuthorityFingerprint(
                        draft
                    )
        )
    }

    private fun appendAuthoritySuccessor(
        state: SignerAuthorityState
    ): SignerAuthorityRevision {
        val predecessor =
            authorityRevisionOne()

        val draft =
            SignerAuthorityRevision(
                predecessor.organizationId,
                SignerAuthorityId(
                    syntheticUuid(821)
                ),
                2,
                predecessor.signerSubjectId,
                predecessor.signerAuthorizingInstitutionId,
                predecessor.signerRole,
                predecessor.signerKeyId,
                predecessor.signerKeyRevision,
                predecessor.signerKeyFingerprint,
                predecessor.approvalAction,
                predecessor.permission,
                predecessor.validFrom,
                predecessor.validUntil,
                state,
                predecessor.signerAuthorityId,
                predecessor.signerAuthorityFingerprint,
                SignerAuthorityFingerprint(
                    "0".repeat(64)
                ),
                "Synthetic V041 authority successor",
                "v041-pass-b",
                predecessor.approvalSourceId,
                syntheticUuid(822)
            )

        val successor =
            draft.copy(
                signerAuthorityFingerprint =
                    ApprovalGovernanceFingerprintCodec
                        .signerAuthorityFingerprint(
                            draft
                        )
            )

        assertIs<GovernanceAppendResult.Applied>(
            governance()
                .appendSignerAuthorityRevision(
                    successor
                )
        )

        return successor
    }

    private fun rewriteRootKeyEffectiveAt(
        effectiveAt: Instant
    ) {
        val base =
            keyRevisionOne()

        val draft =
            base.copy(
                effectiveAt = effectiveAt,
                lineageFingerprint =
                    SignerKeyLineageFingerprint(
                        "0".repeat(64)
                    )
            )

        val rewritten =
            draft.copy(
                lineageFingerprint =
                    ApprovalGovernanceFingerprintCodec
                        .signerKeyFingerprint(
                            draft
                        )
            )

        adminMutation(
            "s2a_signer_key_revision",
            """
            UPDATE public.s2a_signer_key_revision
            SET effective_at=?,
                lineage_fingerprint=?
            WHERE organization_id=?
              AND signer_key_id=?
              AND revision=1
            """.trimIndent(),
            Timestamp.from(effectiveAt),
            rewritten.lineageFingerprint.value,
            ORGANIZATION,
            KEY_ID
        )
    }

    private fun rewriteRootAuthority(
        validFrom: Instant,
        validUntil: Instant,
        state: SignerAuthorityState
    ) {
        val base =
            authorityRevisionOne()

        val draft =
            base.copy(
                validFrom = validFrom,
                validUntil = validUntil,
                state = state,
                signerAuthorityFingerprint =
                    SignerAuthorityFingerprint(
                        "0".repeat(64)
                    )
            )

        val rewritten =
            draft.copy(
                signerAuthorityFingerprint =
                    ApprovalGovernanceFingerprintCodec
                        .signerAuthorityFingerprint(
                            draft
                        )
            )

        adminMutation(
            "s2a_signer_authority_revision",
            """
            UPDATE public.s2a_signer_authority_revision
            SET valid_from=?,
                valid_until=?,
                state=?,
                signer_authority_fingerprint=?
            WHERE organization_id=?
              AND signer_authority_id=?
            """.trimIndent(),
            Timestamp.from(validFrom),
            Timestamp.from(validUntil),
            state.name,
            rewritten.signerAuthorityFingerprint.value,
            ORGANIZATION,
            AUTHORITY
        )
    }

    private fun removeSignerAuthority() {
        adminMutation(
            "s2a_signer_authority_revision",
            """
            DELETE FROM public.s2a_signer_authority_revision
            WHERE organization_id=?
              AND signer_authority_id=?
            """.trimIndent(),
            ORGANIZATION,
            AUTHORITY
        )
    }

    private fun adminMutation(
        table: String,
        sql: String,
        vararg values: Any?
    ) {
        connection().use { c ->
            c.autoCommit = false

            try {
                c.createStatement().use {
                    it.execute(
                        "ALTER TABLE public.$table DISABLE TRIGGER ALL"
                    )
                }

                execute(
                    c,
                    sql,
                    *values
                )

                c.createStatement().use {
                    it.execute(
                        "ALTER TABLE public.$table ENABLE TRIGGER ALL"
                    )
                }

                c.commit()
            }
            catch (failure: Throwable) {
                c.rollback()
                throw failure
            }
        }
    }

    private fun addMlOccurrence(
        ordinal: Int,
        outcome: String
    ) {
        val observed =
            Timestamp.from(
                VALID_FROM
            )

        connection().use { c ->
            c.autoCommit = false

            execute(
                c,
                """
                INSERT INTO public.integration_mercado_livre_order_source_observation
                (
                    organization_id,
                    connection_id,
                    capability,
                    input_progress_version,
                    record_ordinal,
                    external_order_ref,
                    provider_status,
                    date_created,
                    date_last_updated,
                    currency,
                    total_amount,
                    observed_at
                )
                VALUES (
                    ?,?,?,1,?,
                    'MLB-123456789',
                    'paid',
                    ?,?,
                    'BRL',
                    58.28,
                    ?
                )
                """.trimIndent(),
                ORGANIZATION,
                ML_CONNECTION,
                ML_CAPABILITY,
                ordinal,
                observed,
                observed,
                observed
            )

            execute(
                c,
                """
                INSERT INTO public.marketplace_order_occurrence_source_promotion
                (
                    organization_id,
                    source_connection_id,
                    source_capability,
                    source_input_progress_version,
                    source_record_ordinal,
                    marketplace_order_id,
                    outcome,
                    promoted_at
                )
                VALUES (
                    ?,?,?,1,?,?,?,?
                )
                """.trimIndent(),
                ORGANIZATION,
                ML_CONNECTION,
                ML_CAPABILITY,
                ordinal,
                MARKETPLACE_ORDER,
                outcome,
                observed
            )

            c.commit()
        }
    }

    private fun mlEvidenceFingerprint(
        ordinal: Int,
        outcome: String
    ): String =
        ApprovalEvidenceBindingCodec.fingerprint(
            ApprovalEvidenceBindingCodec.Evidence(
                OrganizationId.parse(
                    ORGANIZATION.toString()
                ),
                MarketplaceOrderId.parse(
                    MARKETPLACE_ORDER.toString()
                ),
                ML_CONNECTION,
                ML_CAPABILITY,
                1L,
                ordinal,
                "mercado-livre",
                "MLB-123456789",
                "BRL",
                outcome,
                OMIE_CONNECTION,
                OMIE_CAPABILITY,
                1L,
                1,
                "SO-2026-0001",
                "INT-2026-0001",
                null,
                1,
                "ab".repeat(32),
                LocalDateTime.parse(
                    "2026-09-25T11:59:59.123456"
                )
            )
        )

    private fun setOmiePageCount(
        count: Int
    ) {
        adminMutation(
            "integration_connector_page_commit",
            """
            UPDATE public.integration_connector_page_commit
            SET record_count=?
            WHERE organization_id=?
              AND connection_id=?
              AND capability=?
              AND input_progress_version=1
            """.trimIndent(),
            count,
            ORGANIZATION,
            OMIE_CONNECTION,
            OMIE_CAPABILITY
        )
    }

    private fun addOmieTargetOccurrence(
        ordinal: Int,
        integrationReference: String?,
        currency: String?,
        providerRevision: LocalDateTime,
        semanticFingerprint: String
    ) {
        val observed =
            Timestamp.from(
                VALID_FROM
            )

        connection().use { c ->
            c.autoCommit = false

            omie(
                c,
                ordinal,
                "SO-2026-0001",
                integrationReference,
                currency,
                providerRevision,
                semanticFingerprint,
                observed
            )

            c.commit()
        }

        setOmiePageCount(3)
    }

    private fun replaceEvidenceFunctionWithFailure(
        sqlState: String,
        detail: String?
    ) {
        val escapedDetail =
            detail?.replace(
                "'",
                "''"
            )

        val detailClause =
            if (escapedDetail == null) {
                ""
            }
            else {
                ", DETAIL='$escapedDetail'"
            }

        val ddl =
            """
            CREATE OR REPLACE FUNCTION public.s2a_v041_evidence_fingerprint(
                p_organization_id uuid,
                p_marketplace_order_id uuid,
                p_mercado_livre_connection_id uuid,
                p_omie_connection_id uuid,
                p_source_order_reference text,
                p_integration_reference text
            )
            RETURNS text
            LANGUAGE plpgsql
            SECURITY DEFINER
            SET search_path=pg_catalog,pg_temp
            AS ${'$'}${'$'}
            BEGIN
                RAISE EXCEPTION 'synthetic V041 SQLSTATE'
                    USING ERRCODE='$sqlState'$detailClause;
            END
            ${'$'}${'$'};
            """.trimIndent()

        connection().use { c ->
            c.createStatement().use {
                it.execute(ddl)
            }
        }
    }

    private fun organizationStatus(): String =
        connection().use { c ->
            c.prepareStatement(
                """
                SELECT status
                FROM public.integration_organization
                WHERE organization_id=?
                """.trimIndent()
            ).use { statement ->
                statement.setObject(
                    1,
                    ORGANIZATION
                )

                statement.executeQuery().use { rows ->
                    check(rows.next())
                    rows.getString(1)
                }
            }
        }

    private fun awaitCondition(
        timeoutMillis: Long,
        condition: () -> Boolean
    ): Boolean {
        val deadline =
            System.nanoTime() +
                TimeUnit.MILLISECONDS
                    .toNanos(
                        timeoutMillis
                    )

        while (
            System.nanoTime() <
            deadline
        ) {
            if (condition()) {
                return true
            }

            Thread.sleep(50)
        }

        return condition()
    }
    private fun governance() = PostgresApprovalGovernance(roleDataSource("flooow_approval_governance"))
    private fun verifier() = PostgresAcceptedAttestationVerifier(roleDataSource("flooow_attestation_verifier"))
    private fun connection() = DriverManager.getConnection(db.jdbcUrl, db.username, db.password)
    private fun execute(c: Connection, sql: String, vararg values: Any?) = c.prepareStatement(sql).use { s ->
        values.forEachIndexed { i, value -> s.setObject(i + 1, value) }; s.executeUpdate()
    }
    private fun update(sql: String, vararg values: Any?) = connection().use { execute(it, sql, *values) }
    private fun tableCount(table: String) = scalar("SELECT count(*) FROM $table")
    private fun scalar(sql: String) = connection().use { c -> c.createStatement().use { s -> s.executeQuery(sql).use { r -> r.next(); r.getInt(1) } } }
    private fun columnCount(table: String) = connection().use { c -> c.prepareStatement("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name=?").use { s ->
        s.setString(1, table); s.executeQuery().use { r -> r.next(); r.getInt(1) }
    } }
    private fun columnNames(table: String) = connection().use { c -> c.prepareStatement("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=? ORDER BY ordinal_position").use { s ->
        s.setString(1, table); s.executeQuery().use { r -> buildList { while (r.next()) add(r.getString(1)) } }
    } }
    private fun regprocedure(signature: String): String? = connection().use { c -> c.prepareStatement("SELECT to_regprocedure(?)::text").use { s ->
        s.setString(1, signature); s.executeQuery().use { r -> r.next(); r.getString(1) }
    } }
    private fun functionInputCount(name: String) = connection().use { c -> c.prepareStatement("SELECT pronargs FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=?").use { s ->
        s.setString(1, name); s.executeQuery().use { r -> r.next(); r.getInt(1) }
    } }
    private fun functionReturnColumnCount(name: String) = connection().use { c -> c.prepareStatement("SELECT array_length(proallargtypes,1)-pronargs FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=?").use { s ->
        s.setString(1, name); s.executeQuery().use { r -> r.next(); r.getInt(1) }
    } }
    private fun assertSecurityDefiner(name: String) = connection().use { c -> c.prepareStatement("SELECT prosecdef,proconfig @> ARRAY['search_path=pg_catalog, pg_temp'] FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname=?").use { s ->
        s.setString(1, name); s.executeQuery().use { r -> r.next(); assertTrue(r.getBoolean(1)); assertTrue(r.getBoolean(2)) }
    } }
    private fun hasTablePrivilege(role: String, table: String, privilege: String) = privilege(role, table, privilege, true)
    private fun hasFunctionPrivilege(role: String, function: String, privilege: String) = privilege(role, function, privilege, false)
    private fun privilege(role: String, target: String, privilege: String, table: Boolean) = connection().use { c ->
        val sql = if (role == "PUBLIC") {
            if (table) "SELECT EXISTS(SELECT 1 FROM pg_class c,aclexplode(c.relacl) a WHERE c.oid=?::regclass AND a.grantee=0 AND a.privilege_type=?)"
            else "SELECT EXISTS(SELECT 1 FROM pg_proc p,aclexplode(p.proacl) a WHERE p.oid=?::regprocedure AND a.grantee=0 AND a.privilege_type=?)"
        } else if (table) "SELECT has_table_privilege(?,?,?)" else "SELECT has_function_privilege(?,?,?)"
        c.prepareStatement(sql).use { s ->
            if (role == "PUBLIC") { s.setString(1, target); s.setString(2, privilege) }
            else { s.setString(1, role); s.setString(2, target); s.setString(3, privilege) }
            s.executeQuery().use { r -> r.next(); r.getBoolean(1) }
        }
    }
    private fun roleDataSource(role: String): DataSource {
        val base = PGSimpleDataSource().also { it.setURL(db.jdbcUrl); it.user = db.username; it.password = db.password }
        return object : DataSource {
            override fun getConnection(): Connection = base.connection.also { c -> c.createStatement().use { it.execute("SET ROLE $role") } }
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

    private fun String.hex() = chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    private fun syntheticUuid(slot: Int) = UUID.fromString("71000000-0000-4000-8000-${slot.toString().padStart(12, '0')}")

    private companion object {
        val ORGANIZATION: UUID = UUID.fromString("11111111-1111-4111-8111-111111111111")
        val KEY_ID: UUID = UUID.fromString("22222222-2222-4222-8222-222222222222")
        val SUBJECT: UUID = UUID.fromString("33333333-3333-4333-8333-333333333333")
        val AUTHORITY: UUID = UUID.fromString("44444444-4444-4444-8444-444444444441")
        val INSTITUTION: UUID = UUID.fromString("55555555-5555-4555-8555-555555555555")
        val APPROVAL_SOURCE: UUID = UUID.fromString("66666666-6666-4666-8666-666666666666")
        val MANIFEST: UUID = UUID.fromString("77777777-7777-4777-8777-777777777777")
        val ML_CONNECTION: UUID = UUID.fromString("88888888-8888-4888-8888-888888888888")
        val OMIE_CONNECTION: UUID = UUID.fromString("99999999-9999-4999-8999-999999999999")
        val MARKETPLACE_ORDER: UUID = UUID.fromString("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        val KEY_FINGERPRINT = SignerKeyFingerprint("06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9")
        val VALID_FROM: Instant = Instant.parse("2026-09-25T12:00:00.000000Z")
        val VALID_UNTIL: Instant = Instant.parse("2026-10-25T12:00:00.000000Z")
        const val EVIDENCE_FINGERPRINT = "9f61859daa192ae3482ad3dbb28cd7ebb5d2f143cdb6e83092054a80b512e965"
        const val SPKI_HEX = "302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
        const val PKCS8_PREFIX = "302e020100300506032b657004220420"
        const val SEED_HEX = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
        const val ML_CAPABILITY = "marketplace-economic.order-source"
        const val OMIE_CAPABILITY = "marketplace-economic.omie-transaction-evidence.reacquisition-v3"
        const val BEGIN_SIGNATURE = "public.s2a_begin_attestation_verification(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamp with time zone,timestamp with time zone,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,bytea,text,text,uuid,text,bytea)"
        const val PERSIST_SIGNATURE = "public.s2a_persist_attestation_verification_result(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamp with time zone,timestamp with time zone,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,bytea,text,text,uuid,text,bytea,bytea,uuid,integer,text,bytea,uuid,integer,text,text)"
        val EXPECTED_COLUMNS = listOf("organization_id","manifest_id","artifact_version","schema_version","canonicalization_version","canonical_manifest_bytes","manifest_digest","canonical_signature_preimage_bytes","algorithm_id","signer_key_id","signer_key_revision","signer_key_fingerprint","signer_key_lineage_fingerprint","subject_public_key_info_der","signature_bytes","signer_authority_id","signer_authority_revision","signer_authority_fingerprint","verified_at","accepted_proof_fingerprint","recorded_at")
    }
}
