package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.organization.OrganizationId
import java.io.PrintWriter
import java.security.KeyFactory
import java.security.Signature
import java.security.spec.PKCS8EncodedKeySpec
import java.sql.Timestamp
import java.time.Instant
import java.time.LocalDateTime
import java.util.Base64
import java.util.UUID
import javax.sql.DataSource
import kotlin.test.assertIs
import org.postgresql.ds.PGSimpleDataSource
import org.postgresql.util.PSQLException
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresV042MigrationTest {
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
    fun `PostgreSQL 18_4 applies V001 through V042 and materializes the frozen schema`() {
        assertTrue(scalarString("SHOW server_version").startsWith("18.4"))
        assertEquals(180004, scalarInt("SHOW server_version_num"))
        assertEquals(42, scalarInt("SELECT max(version::integer) FROM flyway_schema_history WHERE success"))
        assertEquals(0, scalarInt("SELECT count(*) FROM flyway_schema_history WHERE NOT success"))

        val columns = columns("s2a_attestation_consumption")
        assertEquals(
            mapOf(
                "organization_id" to Column("uuid", true),
                "manifest_id" to Column("uuid", true),
                "manifest_digest" to Column("character(64)", true),
                "principal_id" to Column("uuid", true),
                "correlation_id" to Column("uuid", true),
                "consumed_at" to Column("timestamp(6) with time zone", true)
            ),
            columns
        )
        assertConstraint(
            "s2a_attestation_consumption_pkey",
            "PRIMARY KEY (organization_id, manifest_id)"
        )
        assertTableConstraintContains(
            "s2a_attestation_consumption",
            "UNIQUE (organization_id, manifest_id, principal_id)"
        )
        assertTableConstraintContains(
            "s2a_attestation_consumption",
            "REFERENCES s2a_accepted_attestation(organization_id, manifest_id)"
        )
        assertTableConstraintContains(
            "s2a_attestation_consumption",
            "REFERENCES command_principal(organization_id, principal_id)"
        )
        assertEquals(1, immutableTriggerCount())

        assertEquals(Column("uuid", false), columns("command_authority_operation")["attestation_manifest_id"])
        assertConstraintContains(
            "command_authority_operation_v042_attestation_kind_check",
            "attestation_manifest_id IS NULL"
        )
        assertConstraintContains(
            "command_authority_operation_v042_consumption_fk",
            "REFERENCES s2a_attestation_consumption(organization_id, manifest_id, principal_id)"
        )
        assertConstraintContains(
            "command_authority_operation_v042_credential_target_fk",
            "REFERENCES command_credential_revision(organization_id, credential_id, revision, principal_id, state)"
        )
        assertConstraintContains(
            "command_authority_operation_v042_grant_target_fk",
            "REFERENCES command_permission_grant(organization_id, grant_id, revision, principal_id, permission, state)"
        )
        assertIndexContains("command_authority_operation_v042_manifest_kind_key", "attestation_manifest_id IS NOT NULL")
        assertIndexContains("command_authority_operation_v042_manifest_kind_key", "operation = ANY")
        assertIndexContains("command_authority_operation_v042_grant_receipt_key", "operation = 'GRANT'::text")
    }

    @Test
    fun `the nine caller capabilities have exact input and return contracts`() {
        assertEquals(6, functions(ISSUER_FUNCTIONS).size)
        assertEquals(3, functions(WRITER_FUNCTIONS).size)
        assertEquals(9, functions(CALLER_FUNCTIONS).size)

        for (name in CALLER_FUNCTIONS) {
            assertEquals(1, scalarInt("SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='$name'"), name)
            val contract = sourceContract(name)
            assertEquals(contract.inputTypes, inputTypes(name), "$name input identity")
            assertEquals(contract.outputs, outputContract(name), "$name return contract")
        }

        assertEquals(32, sourceContract("s2a_v042_apply_legacy_unlinked_decision").inputTypes.size)
        assertEquals(30, sourceContract("s2a_v042_begin_attested_decision_verification").inputTypes.size)
        assertEquals(73, sourceContract("s2a_v042_apply_attested_decision").inputTypes.size)
        ISSUER_FUNCTIONS.take(3).forEach { assertEquals(32, sourceContract(it).outputs.size, it) }
        ISSUER_FUNCTIONS.drop(3).forEach { assertEquals(5, sourceContract(it).outputs.size, it) }
        assertEquals(4, sourceContract("s2a_v042_apply_legacy_unlinked_decision").outputs.size)
        assertEquals(33, sourceContract("s2a_v042_begin_attested_decision_verification").outputs.size)
        assertEquals(4, sourceContract("s2a_v042_apply_attested_decision").outputs.size)
    }

    @Test
    fun `dedicated owner roles ownership and SECURITY DEFINER posture are exact`() {
        assertEquals(
            Role(false, false, false, false, false, false, false),
            role("flooow_v042_capability_owner")
        )
        for (name in PROTECTED_ROLES) {
            val role = role(name)
            assertFalse(role.superuser, name)
            assertFalse(role.createDb, name)
            assertFalse(role.createRole, name)
            assertFalse(role.bypassRls, name)
        }

        for (name in CALLER_FUNCTIONS) {
            connection().use { connection ->
                connection.prepareStatement(
                    """
                    SELECT pg_get_userbyid(proowner), prosecdef,
                           EXISTS (SELECT 1 FROM unnest(proconfig) c WHERE replace(c,' ','')='search_path=pg_catalog,pg_temp')
                      FROM pg_proc
                     WHERE pronamespace='public'::regnamespace AND proname=?
                    """.trimIndent()
                ).use { statement ->
                    statement.setString(1, name)
                    statement.executeQuery().use { result ->
                        assertTrue(result.next(), name)
                        assertEquals("flooow_v042_capability_owner", result.getString(1), name)
                        assertTrue(result.getBoolean(2), name)
                        assertTrue(result.getBoolean(3), name)
                    }
                }
            }
        }

        assertEquals(
            0,
            scalarInt(
                """
                SELECT count(*)
                  FROM pg_auth_members m
                  JOIN pg_roles parent ON parent.oid=m.roleid
                  JOIN pg_roles member ON member.oid=m.member
                 WHERE parent.rolname='flooow_v042_capability_owner'
                    OR member.rolname='flooow_v042_capability_owner'
                """.trimIndent()
            )
        )
        for (name in PROTECTED_ROLES) {
            assertFalse(scalarBoolean("SELECT pg_has_role('$name','flooow_v042_capability_owner','SET')"), name)
        }

        assertTrue(schemaPrivilege("flooow_v042_capability_owner", "USAGE"))
        assertFalse(schemaPrivilege("flooow_v042_capability_owner", "CREATE"))
        assertFalse(publicSchemaPrivilege("CREATE"))
        assertFalse(scalarBoolean("SELECT nspowner='flooow_v042_capability_owner'::regrole FROM pg_namespace WHERE nspname='public'"))
        assertFalse(scalarBoolean("SELECT datdba='flooow_v042_capability_owner'::regrole FROM pg_database WHERE datname=current_database()"))
    }

    @Test
    fun `caller EXECUTE and direct table privilege matrices are exact`() {
        val identities = CALLER_FUNCTIONS.associateWith(::functionIdentity)
        for ((name, identity) in identities) {
            assertFalse(publicExecute(identity), name)
            assertEquals(name in ISSUER_FUNCTIONS, functionPrivilege("flooow_command_issuer", identity), "issuer $name")
            assertEquals(name in WRITER_FUNCTIONS, functionPrivilege("flooow_command_runtime", identity), "runtime $name")
            assertFalse(functionPrivilege("flooow_attestation_verifier", identity), "verifier $name")
            assertFalse(functionPrivilege("flooow_approval_governance", identity), "governance $name")
        }

        for (table in ISSUER_PROTECTED_TABLES) {
            assertTrue(tablePrivilege("flooow_command_issuer", table, "SELECT"), table)
            for (privilege in listOf("INSERT", "UPDATE", "DELETE")) {
                assertFalse(tablePrivilege("flooow_command_issuer", table, privilege), "$table $privilege")
            }
        }
        for (table in listOf("integration_organization", "integration_connection")) {
            assertTrue(tablePrivilege("flooow_command_issuer", table, "SELECT"), table)
        }
        assertFalse(tablePrivilege("flooow_command_runtime", "marketplace_transaction_identity_decision", "INSERT"))
        assertTrue(tablePrivilege("flooow_command_runtime", "command_principal", "SELECT"))
        assertTrue(tablePrivilege("flooow_command_runtime", "command_principal", "UPDATE"))
        for (table in RUNTIME_READ_TABLES) {
            assertTrue(tablePrivilege("flooow_command_runtime", table, "SELECT"), table)
        }
    }

    @Test
    fun `real role-context attacks stop at PostgreSQL privilege boundaries`() {
        val principalBefore = tableCount("command_principal")
        assertSqlState(
            "flooow_command_issuer",
            "INSERT INTO public.command_principal SELECT * FROM public.command_principal WHERE FALSE",
            "42501"
        )
        assertEquals(principalBefore, tableCount("command_principal"))

        val decisionBefore = tableCount("marketplace_transaction_identity_decision")
        assertSqlState(
            "flooow_command_runtime",
            "INSERT INTO public.marketplace_transaction_identity_decision SELECT * FROM public.marketplace_transaction_identity_decision WHERE FALSE",
            "42501"
        )
        assertEquals(decisionBefore, tableCount("marketplace_transaction_identity_decision"))

        assertSqlState(
            "flooow_command_issuer",
            nullInvocation("s2a_v042_apply_legacy_unlinked_decision"),
            "42501"
        )
        assertSqlState(
            "flooow_command_runtime",
            nullInvocation("s2a_v042_begin_attested_principal_verification"),
            "42501"
        )

        connection().use { connection -> connection.createStatement().use { it.execute("CREATE ROLE flooow_v042_a31_unprivileged NOLOGIN NOINHERIT") } }
        try {
            assertEquals(
                0,
                scalarInt(
                    """
                    SELECT count(*) FROM pg_auth_members
                     WHERE member='flooow_v042_a31_unprivileged'::regrole
                        OR roleid='flooow_v042_a31_unprivileged'::regrole
                    """.trimIndent()
                )
            )
            assertSqlState(
                "flooow_v042_a31_unprivileged",
                nullInvocation("s2a_v042_begin_attested_principal_verification"),
                "42501"
            )
        } finally {
            connection().use { connection -> connection.createStatement().use { it.execute("DROP ROLE flooow_v042_a31_unprivileged") } }
        }
    }

    @Test
    fun `internal helper closure and V040 V041 privilege boundaries are preserved`() {
        val ownerHelpers = Regex(
            "GRANT EXECUTE ON FUNCTION public\\.(.*?) TO flooow_v042_capability_owner;",
            setOf(RegexOption.DOT_MATCHES_ALL)
        ).findAll(migrationSql).map { "public.${it.groupValues[1].replace(Regex("\\s+"), "")}" }.toList()
        assertEquals(20, ownerHelpers.size)
        ownerHelpers.forEach { identity ->
            assertNotNull(scalarNullableString("SELECT to_regprocedure('$identity')::text"), identity)
            assertTrue(functionPrivilege("flooow_v042_capability_owner", identity), identity)
        }

        val callerNames = CALLER_FUNCTIONS.toSet()
        val v042Helpers = functionNames("s2a_v042_%").filterNot { it in callerNames }
        assertEquals(7, v042Helpers.size)
        for (name in v042Helpers) {
            val identity = functionIdentity(name)
            assertFalse(publicExecute(identity), "PUBLIC $name")
            PROTECTED_ROLES.forEach { role -> assertFalse(functionPrivilege(role, identity), "$role $name") }
        }

        val v040Key = "s2a_append_signer_key_revision(uuid,uuid,integer,uuid,text,bytea,text,text,timestamp with time zone,timestamp with time zone,integer,text,text,text,uuid)"
        val v040Authority = "s2a_append_signer_authority_revision(uuid,uuid,integer,uuid,uuid,text,uuid,integer,text,text,text,timestamp with time zone,timestamp with time zone,text,uuid,text,text,text,uuid,uuid)"
        for (identity in listOf(v040Key, v040Authority)) {
            assertTrue(functionPrivilege("flooow_approval_governance", identity), identity)
            for (role in listOf("flooow_command_issuer", "flooow_command_runtime", "flooow_attestation_verifier")) {
                assertFalse(functionPrivilege(role, identity), "$role $identity")
            }
        }

        val v041Begin = "public.s2a_begin_attestation_verification(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamp with time zone,timestamp with time zone,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,bytea,text,text,uuid,text,bytea)"
        val v041Persist = "public.s2a_persist_attestation_verification_result(integer,uuid,uuid,uuid,uuid,text,text,uuid,text,uuid,uuid,timestamp with time zone,timestamp with time zone,uuid,uuid,text,uuid,text,text,text,uuid,text,integer,bytea,text,text,uuid,text,bytea,bytea,uuid,integer,text,bytea,uuid,integer,text,text)"
        for (identity in listOf(v041Begin, v041Persist)) {
            assertTrue(functionPrivilege("flooow_attestation_verifier", identity), identity)
            for (role in listOf("flooow_command_issuer", "flooow_command_runtime", "flooow_approval_governance")) {
                assertFalse(functionPrivilege(role, identity), "$role $identity")
            }
        }
    }

    @Test
    fun `V042 decimal UTF_8 framing remains separated from V041 binary framing`() {
        val before = durableState()

        assertEquals("303a", scalarString("SELECT encode(public.s2a_v042_frame(''::bytea),'hex')"))
        assertEquals("333a616263", scalarString("SELECT encode(public.s2a_v042_text('abc'),'hex')"))
        assertEquals("323ac3a9", scalarString("SELECT encode(public.s2a_v042_text(U&'\\00E9'),'hex')"))
        assertEquals(
            "33363a31313131313131312d313131312d343131312d383131312d313131313131313131313131",
            scalarString(
                "SELECT encode(public.s2a_v042_text('11111111-1111-4111-8111-111111111111'),'hex')"
            )
        )

        assertEquals("00000000", scalarString("SELECT encode(public.s2a_v041_frame(''::bytea),'hex')"))
        assertEquals("00000003616263", scalarString("SELECT encode(public.s2a_v041_text('abc'),'hex')"))
        assertEquals("00000002c3a9", scalarString("SELECT encode(public.s2a_v041_text(U&'\\00E9'),'hex')"))
        assertFalse(scalarString("SELECT encode(public.s2a_v041_text('abc'),'hex')") == scalarString("SELECT encode(public.s2a_v042_text('abc'),'hex')"))

        assertEquals(before, durableState(), "framing helpers changed durable state")
    }

    // A3_2_CONT1_GATE_3_VECTORS
    @Test
    fun `V042 frozen authority fingerprint vectors are exact in PostgreSQL`() {
        val principalIntent =
            scalarString(
                """
                SELECT public.s2a_v042_authority_intent(
                    'PRINCIPAL',
                    '12121212-1212-4121-8121-121212121212'::uuid,
                    '11111111-1111-4111-8111-111111111111'::uuid,
                    '13131313-1313-4131-8131-131313131313'::uuid,
                    '88888888-8888-4888-8888-888888888888'::uuid,
                    '99999999-9999-4999-8999-999999999999'::uuid,
                    NULL::uuid,
                    NULL::bytea,
                    NULL::uuid,
                    'S2A field proof approval',
                    'revision-6-golden-vector',
                    'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee'::uuid,
                    '77777777-7777-4777-8777-777777777777'::uuid,
                    '9bf856a724a921d7a63a87c551fdcf82e896fb13b184c785909269ecdbe685b9',
                    '209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0'
                )
                """.trimIndent()
            )

        assertEquals(
            "a51a46e777ea83218a5e21411263801062ed2fbae004eb6e3c9e21fdf287cf50",
            principalIntent
        )

        val principalReceipt =
            scalarString(
                """
                SELECT public.s2a_v042_authority_receipt(
                    '$principalIntent',
                    'PRINCIPAL',
                    '13131313-1313-4131-8131-131313131313'::uuid,
                    NULL::uuid,
                    NULL::integer,
                    NULL::uuid,
                    NULL::integer,
                    NULL::text,
                    NULL::text
                )
                """.trimIndent()
            )

        assertEquals(
            "2452d2807b7086383a52500bf346d5bd549ed102986a76867bd51dbc7a700a06",
            principalReceipt
        )

        val initialIntent =
            scalarString(
                """
                SELECT public.s2a_v042_authority_intent(
                    'INITIAL_CREDENTIAL',
                    '16161616-1616-4161-8161-161616161616'::uuid,
                    '11111111-1111-4111-8111-111111111111'::uuid,
                    '13131313-1313-4131-8131-131313131313'::uuid,
                    NULL::uuid,
                    NULL::uuid,
                    '14141414-1414-4141-8141-141414141414'::uuid,
                    decode(
                        '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f',
                        'hex'
                    ),
                    NULL::uuid,
                    'S2A field proof approval',
                    'revision-6-golden-vector',
                    'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee'::uuid,
                    '77777777-7777-4777-8777-777777777777'::uuid,
                    '9bf856a724a921d7a63a87c551fdcf82e896fb13b184c785909269ecdbe685b9',
                    '209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0'
                )
                """.trimIndent()
            )

        assertEquals(
            "3b0bbe7cda4e4517cda84d574ff38a4171d1e786a83d40abd101af6b3ab3b021",
            initialIntent
        )

        val initialReceipt =
            scalarString(
                """
                SELECT public.s2a_v042_authority_receipt(
                    '$initialIntent',
                    'INITIAL_CREDENTIAL',
                    '13131313-1313-4131-8131-131313131313'::uuid,
                    '14141414-1414-4141-8141-141414141414'::uuid,
                    1,
                    NULL::uuid,
                    NULL::integer,
                    NULL::text,
                    'ENABLED'
                )
                """.trimIndent()
            )

        assertEquals(
            "8b3fbc153250f3cd4dfc8bc45b877b48aa1589a7766a1e28b6910ce2fe0810c4",
            initialReceipt
        )

        val grantIntent =
            scalarString(
                """
                SELECT public.s2a_v042_authority_intent(
                    'GRANT',
                    '17171717-1717-4171-8171-171717171717'::uuid,
                    '11111111-1111-4111-8111-111111111111'::uuid,
                    '13131313-1313-4131-8131-131313131313'::uuid,
                    NULL::uuid,
                    NULL::uuid,
                    NULL::uuid,
                    NULL::bytea,
                    '15151515-1515-4151-8151-151515151515'::uuid,
                    'S2A field proof approval',
                    'revision-6-golden-vector',
                    'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee'::uuid,
                    '77777777-7777-4777-8777-777777777777'::uuid,
                    '9bf856a724a921d7a63a87c551fdcf82e896fb13b184c785909269ecdbe685b9',
                    '209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0'
                )
                """.trimIndent()
            )

        assertEquals(
            "f8719d1939f19fbc9a74a007a3af63e9e8e1b3f30f060a51d38e022581a4e1bc",
            grantIntent
        )

        val grantReceipt =
            scalarString(
                """
                SELECT public.s2a_v042_authority_receipt(
                    '$grantIntent',
                    'GRANT',
                    '13131313-1313-4131-8131-131313131313'::uuid,
                    NULL::uuid,
                    NULL::integer,
                    '15151515-1515-4151-8151-151515151515'::uuid,
                    1,
                    'TRANSACTION_IDENTITY_DECISION_WRITE',
                    'ENABLED'
                )
                """.trimIndent()
            )

        assertEquals(
            "3c281f1daafb5398e44a7edf95aa73f265fa316fcf0207eb5ce80cc45a25e9b9",
            grantReceipt
        )

        val principalPreimageBytes =
            scalarInt(
                """
                SELECT octet_length(
                    public.s2a_v042_text('controlled-command-authority/2') ||
                    public.s2a_v042_text('principal') ||
                    public.s2a_v042_text('12121212-1212-4121-8121-121212121212') ||
                    public.s2a_v042_text('11111111-1111-4111-8111-111111111111') ||
                    public.s2a_v042_text('13131313-1313-4131-8131-131313131313') ||
                    public.s2a_v042_text('88888888-8888-4888-8888-888888888888') ||
                    public.s2a_v042_text('99999999-9999-4999-8999-999999999999') ||
                    public.s2a_v042_text('S2A field proof approval') ||
                    public.s2a_v042_text('revision-6-golden-vector') ||
                    public.s2a_v042_text('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee') ||
                    public.s2a_v042_text('77777777-7777-4777-8777-777777777777') ||
                    public.s2a_v042_text('9bf856a724a921d7a63a87c551fdcf82e896fb13b184c785909269ecdbe685b9') ||
                    public.s2a_v042_text('209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0')
                )
                """.trimIndent()
            )

        assertEquals(505, principalPreimageBytes)

        val principalReceiptPreimageBytes = scalarInt(
            """
            SELECT octet_length(
                public.s2a_v042_text('controlled-command-authority-receipt/1') ||
                public.s2a_v042_text('$principalIntent') || public.s2a_v042_text('PRINCIPAL') ||
                public.s2a_v042_text('13131313-1313-4131-8131-131313131313') ||
                public.s2a_v042_text('') || public.s2a_v042_text('') || public.s2a_v042_text('') ||
                public.s2a_v042_text('') || public.s2a_v042_text('') || public.s2a_v042_text('')
            )
            """.trimIndent()
        )
        assertEquals(170, principalReceiptPreimageBytes)

        val initialPreimageBytes = scalarInt(
            """
            SELECT octet_length(
                public.s2a_v042_text('controlled-command-authority/2') ||
                public.s2a_v042_text('initial-credential') ||
                public.s2a_v042_text('16161616-1616-4161-8161-161616161616') ||
                public.s2a_v042_text('11111111-1111-4111-8111-111111111111') ||
                public.s2a_v042_text('13131313-1313-4131-8131-131313131313') ||
                public.s2a_v042_text('14141414-1414-4141-8141-141414141414') ||
                public.s2a_v042_text('000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f') ||
                public.s2a_v042_text('S2A field proof approval') || public.s2a_v042_text('revision-6-golden-vector') ||
                public.s2a_v042_text('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee') ||
                public.s2a_v042_text('77777777-7777-4777-8777-777777777777') ||
                public.s2a_v042_text('9bf856a724a921d7a63a87c551fdcf82e896fb13b184c785909269ecdbe685b9') ||
                public.s2a_v042_text('209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0')
            )
            """.trimIndent()
        )
        assertEquals(543, initialPreimageBytes)

        val initialReceiptPreimageBytes = scalarInt(
            """
            SELECT octet_length(
                public.s2a_v042_text('controlled-command-authority-receipt/1') ||
                public.s2a_v042_text('$initialIntent') || public.s2a_v042_text('INITIAL_CREDENTIAL') ||
                public.s2a_v042_text('13131313-1313-4131-8131-131313131313') ||
                public.s2a_v042_text('14141414-1414-4141-8141-141414141414') ||
                public.s2a_v042_text('1') || public.s2a_v042_text('') || public.s2a_v042_text('') ||
                public.s2a_v042_text('') || public.s2a_v042_text('ENABLED')
            )
            """.trimIndent()
        )
        assertEquals(225, initialReceiptPreimageBytes)

        val grantPreimageBytes = scalarInt(
            """
            SELECT octet_length(
                public.s2a_v042_text('controlled-command-authority/2') || public.s2a_v042_text('grant') ||
                public.s2a_v042_text('17171717-1717-4171-8171-171717171717') ||
                public.s2a_v042_text('11111111-1111-4111-8111-111111111111') ||
                public.s2a_v042_text('13131313-1313-4131-8131-131313131313') ||
                public.s2a_v042_text('15151515-1515-4151-8151-151515151515') ||
                public.s2a_v042_text('TRANSACTION_IDENTITY_DECISION_WRITE') ||
                public.s2a_v042_text('S2A field proof approval') || public.s2a_v042_text('revision-6-golden-vector') ||
                public.s2a_v042_text('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee') ||
                public.s2a_v042_text('77777777-7777-4777-8777-777777777777') ||
                public.s2a_v042_text('9bf856a724a921d7a63a87c551fdcf82e896fb13b184c785909269ecdbe685b9') ||
                public.s2a_v042_text('209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0')
            )
            """.trimIndent()
        )
        assertEquals(500, grantPreimageBytes)

        val grantReceiptPreimageBytes = scalarInt(
            """
            SELECT octet_length(
                public.s2a_v042_text('controlled-command-authority-receipt/1') ||
                public.s2a_v042_text('$grantIntent') || public.s2a_v042_text('GRANT') ||
                public.s2a_v042_text('13131313-1313-4131-8131-131313131313') ||
                public.s2a_v042_text('') || public.s2a_v042_text('') ||
                public.s2a_v042_text('15151515-1515-4151-8151-151515151515') || public.s2a_v042_text('1') ||
                public.s2a_v042_text('TRANSACTION_IDENTITY_DECISION_WRITE') || public.s2a_v042_text('ENABLED')
            )
            """.trimIndent()
        )
        assertEquals(247, grantReceiptPreimageBytes)
    }

    @Test
    fun `V042 frozen authority manifest is accepted with exact digest and proof`() {
        installV042PrincipalFixture()
        val manifest = v042FrozenAuthorityManifest()
        assertEquals(V042_MANIFEST, manifest.manifestId)
        assertEquals(OrganizationId.parse(V042_ORGANIZATION.toString()), manifest.organizationId)
        assertEquals("S2A field proof approval", manifest.reason)
        assertEquals("revision-6-golden-vector", manifest.provenance)
        assertEquals(UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), manifest.correlationId)
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest)
        val manifestDigest = ApprovalManifestCanonicalCodec.manifestDigest(canonical)
        assertEquals(
            "209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0",
            manifestDigest
        )

        val signed = signedV042(manifest)
        val signaturePreimage =
            ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes(
                signed.algorithmId,
                signed.signerKeyId,
                signed.signerKeyFingerprint,
                manifestDigest
            )
        val currentDurableEvidenceFingerprint = scalarString(
            "SELECT public.s2a_v041_evidence_fingerprint(" +
                "'$V042_ORGANIZATION'::uuid,'$V042_MARKETPLACE_ORDER'::uuid," +
                "'$V042_ML_CONNECTION'::uuid,'$V042_OMIE_CONNECTION'::uuid," +
                "'SO-2026-0001','INT-2026-0001')"
        )
        assertEquals(manifest.evidenceBindingFingerprint, currentDurableEvidenceFingerprint)
        assertIs<AcceptedAttestationResult.Accepted>(v042Verifier().verify(signed))

        connection().use { connection ->
            connection.prepareStatement(
                """
                SELECT artifact_version, schema_version, canonicalization_version,
                       canonical_manifest_bytes, manifest_digest,
                       canonical_signature_preimage_bytes, algorithm_id,
                       signer_key_id, signer_key_revision, signer_key_fingerprint,
                       signer_key_lineage_fingerprint, subject_public_key_info_der,
                       signature_bytes, signer_authority_id, signer_authority_revision,
                       signer_authority_fingerprint, verified_at,
                       accepted_proof_fingerprint,
                       (SELECT signer_subject_id FROM public.s2a_signer_key_revision k
                         WHERE k.organization_id=a.organization_id AND k.signer_key_id=a.signer_key_id
                           AND k.revision=a.signer_key_revision) AS signer_subject_id
                  FROM public.s2a_accepted_attestation a
                 WHERE organization_id=? AND manifest_id=?
                """.trimIndent()
            ).use { statement ->
                statement.setObject(1, V042_ORGANIZATION)
                statement.setObject(2, V042_MANIFEST)
                statement.executeQuery().use { row ->
                    assertTrue(row.next(), "frozen accepted artifact is absent")
                    assertEquals(1, row.getInt("artifact_version"))
                    assertEquals(1, row.getInt("schema_version"))
                    assertEquals(1, row.getInt("canonicalization_version"))
                    assertTrue(canonical.contentEquals(row.getBytes("canonical_manifest_bytes")))
                    assertEquals(manifestDigest, row.getString("manifest_digest"))
                    assertTrue(signaturePreimage.contentEquals(row.getBytes("canonical_signature_preimage_bytes")))
                    assertEquals("Ed25519", row.getString("algorithm_id"))
                    assertEquals(V042_SUBJECT, row.getObject("signer_subject_id", UUID::class.java))
                    assertEquals(V042_KEY_ID, row.getObject("signer_key_id", UUID::class.java))
                    assertEquals(1, row.getInt("signer_key_revision"))
                    assertEquals(V042_KEY_FINGERPRINT.toString(), row.getString("signer_key_fingerprint"))
                    assertEquals(
                        scalarString(
                            "SELECT lineage_fingerprint::text FROM public.s2a_signer_key_revision " +
                                "WHERE organization_id='$V042_ORGANIZATION'::uuid AND signer_key_id='$V042_KEY_ID'::uuid AND revision=1"
                        ),
                        row.getString("signer_key_lineage_fingerprint")
                    )
                    assertTrue(V042_SPKI_HEX.hex().contentEquals(row.getBytes("subject_public_key_info_der")))
                    assertTrue(signed.signatureBytes().contentEquals(row.getBytes("signature_bytes")))
                    assertEquals(V042_AUTHORITY, row.getObject("signer_authority_id", UUID::class.java))
                    assertEquals(1, row.getInt("signer_authority_revision"))
                    assertEquals(
                        scalarString(
                            "SELECT signer_authority_fingerprint::text FROM public.s2a_signer_authority_revision " +
                                "WHERE organization_id='$V042_ORGANIZATION'::uuid AND signer_authority_id='$V042_AUTHORITY'::uuid AND revision=1"
                        ),
                        row.getString("signer_authority_fingerprint")
                    )
                    assertNotNull(row.getTimestamp("verified_at"))
                    assertEquals(
                        row.getString("accepted_proof_fingerprint"),
                        AcceptedAttestationFingerprintCodec.fingerprint(
                            AcceptedAttestationProof.create(
                                row.getInt("artifact_version"),
                                row.getInt("canonicalization_version"),
                                row.getBytes("canonical_manifest_bytes"),
                                row.getString("manifest_digest"),
                                row.getBytes("canonical_signature_preimage_bytes"),
                                row.getString("algorithm_id"),
                                SignerKeyId(row.getObject("signer_key_id", UUID::class.java)),
                                row.getInt("signer_key_revision"),
                                SignerKeyFingerprint(row.getString("signer_key_fingerprint")),
                                SignerKeyLineageFingerprint(row.getString("signer_key_lineage_fingerprint")),
                                row.getBytes("subject_public_key_info_der"),
                                row.getBytes("signature_bytes"),
                                SignerAuthorityId(row.getObject("signer_authority_id", UUID::class.java)),
                                row.getInt("signer_authority_revision"),
                                SignerAuthorityFingerprint(row.getString("signer_authority_fingerprint")),
                                row.getTimestamp("verified_at").toInstant()
                            )
                        )
                    )
                    assertFalse(row.next(), "more than one frozen accepted artifact")
                }
            }
        }

        assertEquals(V042_EVIDENCE_FINGERPRINT, manifest.evidenceBindingFingerprint)
        assertEquals(1, tableCount("s2a_accepted_attestation"))
        assertEquals(0, tableCount("command_principal"))
        assertEquals(0, tableCount("s2a_attestation_consumption"))
        assertEquals(0, tableCount("command_authority_operation"))
        assertEquals(0, tableCount("command_credential_revision"))
        assertEquals(0, tableCount("command_permission_grant"))
        assertEquals(0, tableCount("marketplace_transaction_identity_decision"))
    }

    // A3_2_CONT1_GATE_4_PRINCIPAL_BEGIN
    @Test
    fun `V042 principal BEGIN returns READY and does not mutate durable state`() {
        installV042PrincipalFixture()

        assertIs<AcceptedAttestationResult.Accepted>(
            v042Verifier().verify(
                signedV042(v042Manifest())
            )
        )

        assertEquals(1, tableCount("s2a_accepted_attestation"))
        assertEquals(0, tableCount("command_principal"))
        assertEquals(0, tableCount("s2a_attestation_consumption"))
        assertEquals(0, tableCount("command_authority_operation"))

        val before = durableState()
        val begin = beginV042Principal()

        assertEquals("READY", begin.outcome)
        assertEquals(V042_OPERATION, begin.operationId)
        assertTrue(begin.intentFingerprint.matches(Regex("^[0-9a-f]{64}$")))
        assertEquals(null, begin.receiptFingerprint)
        assertEquals(null, begin.effectTime)

        assertEquals(
            scalarString(
                """
                SELECT manifest_digest::text
                FROM public.s2a_accepted_attestation
                WHERE organization_id='$V042_ORGANIZATION'::uuid
                  AND manifest_id='$V042_MANIFEST'::uuid
                """.trimIndent()
            ),
            begin.manifestDigest
        )

        assertEquals(
            scalarString(
                """
                SELECT accepted_proof_fingerprint::text
                FROM public.s2a_accepted_attestation
                WHERE organization_id='$V042_ORGANIZATION'::uuid
                  AND manifest_id='$V042_MANIFEST'::uuid
                """.trimIndent()
            ),
            begin.acceptedProofFingerprint
        )

        assertEquals(V042_EVIDENCE_FINGERPRINT, begin.signedEvidenceBinding)
        assertEquals(V042_EVIDENCE_FINGERPRINT, begin.currentEvidenceBinding)
        assertNotNull(begin.observedEffectTime)
        assertEquals(1, begin.observedEffectiveKeyRevision)
        assertEquals("ACTIVE", begin.observedEffectiveKeyState)
        assertEquals(V042_AUTHORITY, begin.observedCurrentAuthorityId)
        assertEquals(1, begin.observedCurrentAuthorityRevision)
        assertTrue(assertNotNull(begin.observedCurrentAuthorityFingerprint).matches(Regex("^[0-9a-f]{64}$")))

        assertEquals(before, durableState(), "PRINCIPAL BEGIN changed durable state")
        assertEquals(0, tableCount("command_principal"))
        assertEquals(0, tableCount("s2a_attestation_consumption"))
        assertEquals(0, tableCount("command_authority_operation"))
    }

    // A3_2_CONT1_GATES_5_THROUGH_10
    @Test
    fun `V042 principal APPLY is atomic immutable historically replayable and one manifest one root`() {
        installV042PrincipalFixture()
        assertIs<AcceptedAttestationResult.Accepted>(v042Verifier().verify(signedV042(v042Manifest())))

        val begin = beginV042Principal()
        val beforeApply = durableState()
        val applied = applyV042Principal(begin)

        assertEquals("APPLIED", applied.outcome)
        assertEquals(V042_OPERATION, applied.operationId)
        assertEquals(begin.intentFingerprint, applied.intentFingerprint)
        assertNotNull(applied.receiptFingerprint)
        assertNotNull(applied.effectTime)
        assertFalse(beforeApply == durableState(), "PRINCIPAL APPLY did not create its atomic effect")

        assertEquals(1, tableCount("command_principal"))
        assertEquals(1, tableCount("command_authority_operation"))
        assertEquals(1, tableCount("s2a_attestation_consumption"))
        assertEquals(0, tableCount("command_credential_revision"))
        assertEquals(0, tableCount("command_permission_grant"))
        assertEquals(0, tableCount("marketplace_transaction_identity_decision"))
        assertEquals(0, tableCount("marketplace_transaction_identity_head"))

        assertEquals(
            "$V042_ORGANIZATION|$V042_PRINCIPAL|$V042_ML_CONNECTION|$V042_OMIE_CONNECTION|${v042SyntheticUuid(14)}",
            scalarString(
                """
                SELECT organization_id||'|'||principal_id||'|'||mercado_livre_connection_id||'|'||
                       omie_connection_id||'|'||correlation_id
                  FROM public.command_principal
                """.trimIndent()
            )
        )
        assertEquals(
            "$V042_ORGANIZATION|$V042_MANIFEST|$V042_PRINCIPAL|${v042SyntheticUuid(14)}|${begin.manifestDigest}",
            scalarString(
                """
                SELECT organization_id||'|'||manifest_id||'|'||principal_id||'|'||correlation_id||'|'||manifest_digest
                  FROM public.s2a_attestation_consumption
                """.trimIndent()
            )
        )
        assertEquals(
            "$V042_ORGANIZATION|$V042_OPERATION|PRINCIPAL|$V042_PRINCIPAL|$V042_MANIFEST|${begin.intentFingerprint}|${applied.receiptFingerprint}",
            scalarString(
                """
                SELECT organization_id||'|'||operation_id||'|'||operation||'|'||principal_id||'|'||
                       attestation_manifest_id||'|'||intent_fingerprint||'|'||receipt_fingerprint
                  FROM public.command_authority_operation
                """.trimIndent()
            )
        )

        val principalTime = scalarTimestamp("SELECT decided_at FROM public.command_principal")
        val operationTime = scalarTimestamp("SELECT decided_at FROM public.command_authority_operation")
        val consumptionTime = scalarTimestamp("SELECT consumed_at FROM public.s2a_attestation_consumption")
        assertEquals(applied.effectTime, principalTime)
        assertEquals(principalTime, operationTime)
        assertEquals(operationTime, consumptionTime)

        val afterApply = durableState()
        val updateFailure = captureDbFailure {
            v042Update(
                "UPDATE public.s2a_attestation_consumption SET correlation_id=? WHERE organization_id=? AND manifest_id=?",
                v042SyntheticUuid(990), V042_ORGANIZATION, V042_MANIFEST
            )
        }
        assertEquals("23514", updateFailure.sqlState)
        assertEquals(afterApply, durableState(), "rejected consumption UPDATE changed durable state")

        val deleteFailure = captureDbFailure {
            v042Update(
                "DELETE FROM public.s2a_attestation_consumption WHERE organization_id=? AND manifest_id=?",
                V042_ORGANIZATION, V042_MANIFEST
            )
        }
        assertEquals("23514", deleteFailure.sqlState)
        assertEquals(afterApply, durableState(), "rejected consumption DELETE changed durable state")

        val replayBegin = beginV042Principal()
        assertEquals("ALREADY_APPLIED", replayBegin.outcome)
        assertEquals(applied.receiptFingerprint, replayBegin.receiptFingerprint)
        assertEquals(applied.effectTime, replayBegin.effectTime)
        assertEquals(null, replayBegin.currentEvidenceBinding)
        assertEquals(null, replayBegin.observedEffectTime)
        assertEquals(null, replayBegin.observedEffectiveKeyRevision)
        assertEquals(null, replayBegin.observedEffectiveKeyState)
        assertEquals(null, replayBegin.observedCurrentAuthorityId)
        assertEquals(null, replayBegin.observedCurrentAuthorityRevision)
        assertEquals(null, replayBegin.observedCurrentAuthorityFingerprint)
        val replay = applyV042Principal(replayBegin)
        assertEquals("ALREADY_APPLIED", replay.outcome)
        assertEquals(applied.operationId, replay.operationId)
        assertEquals(applied.intentFingerprint, replay.intentFingerprint)
        assertEquals(applied.receiptFingerprint, replay.receiptFingerprint)
        assertEquals(applied.effectTime, replay.effectTime)
        assertEquals(afterApply, durableState(), "exact replay changed durable state")

        v042Update(
            "UPDATE public.integration_organization SET status='SUSPENDED' WHERE organization_id=?",
            V042_ORGANIZATION
        )
        assertEquals(
            "SUSPENDED",
            scalarString("SELECT status FROM public.integration_organization WHERE organization_id='$V042_ORGANIZATION'::uuid")
        )
        val suspendedState = durableState()
        val historicalBegin = beginV042Principal()
        assertEquals("ALREADY_APPLIED", historicalBegin.outcome)
        assertEquals(applied.operationId, historicalBegin.operationId)
        assertEquals(applied.intentFingerprint, historicalBegin.intentFingerprint)
        assertEquals(applied.receiptFingerprint, historicalBegin.receiptFingerprint)
        assertEquals(applied.effectTime, historicalBegin.effectTime)
        assertEquals(begin.manifestDigest, historicalBegin.manifestDigest)
        assertEquals(begin.acceptedProofFingerprint, historicalBegin.acceptedProofFingerprint)
        assertEquals(V042_SUBJECT, historicalBegin.signerSubjectId)
        assertEquals(null, historicalBegin.currentEvidenceBinding)
        assertEquals(null, historicalBegin.observedEffectTime)
        assertEquals(null, historicalBegin.observedEffectiveKeyRevision)
        assertEquals(null, historicalBegin.observedEffectiveKeyState)
        assertEquals(null, historicalBegin.observedCurrentAuthorityId)
        assertEquals(null, historicalBegin.observedCurrentAuthorityRevision)
        assertEquals(null, historicalBegin.observedCurrentAuthorityFingerprint)
        val historicalReplay = applyV042Principal(historicalBegin)
        assertEquals("ALREADY_APPLIED", historicalReplay.outcome)
        assertEquals(applied.receiptFingerprint, historicalReplay.receiptFingerprint)
        assertEquals(applied.effectTime, historicalReplay.effectTime)
        assertEquals(suspendedState, durableState(), "historical replay changed durable state")

        val currentnessFailure = captureDbFailure {
            beginV042Principal(v042SyntheticUuid(904), v042SyntheticUuid(905))
        }
        assertEquals("P0017", currentnessFailure.sqlState)
        assertEquals("EXPIRED_OR_NOT_YET_VALID", currentnessFailure.detail)
        assertEquals(suspendedState, durableState(), "currentness control denial changed durable state")
        v042Update(
            "UPDATE public.integration_organization SET status='ACTIVE' WHERE organization_id=?",
            V042_ORGANIZATION
        )

        val beforeChangedIntent = durableState()
        val historicalOperation = scalarString(
            """
            SELECT operation_id||'|'||intent_fingerprint||'|'||receipt_fingerprint||'|'||
                   decided_at::text||'|'||attestation_manifest_id||'|'||principal_id||'|'||correlation_id
              FROM public.command_authority_operation
             WHERE organization_id='$V042_ORGANIZATION'::uuid
               AND operation_id='$V042_OPERATION'::uuid
            """.trimIndent()
        )
        val changedIntentFailure = captureDbFailure {
            beginV042Principal(reason = "S2A field proof approval changed intent")
        }
        assertEquals("P0018", changedIntentFailure.sqlState)
        assertEquals("INTEGRITY_FAILURE", changedIntentFailure.detail)
        assertEquals(beforeChangedIntent, durableState(), "changed-intent denial changed durable state")
        assertEquals(
            historicalOperation,
            scalarString(
                """
                SELECT operation_id||'|'||intent_fingerprint||'|'||receipt_fingerprint||'|'||
                       decided_at::text||'|'||attestation_manifest_id||'|'||principal_id||'|'||correlation_id
                  FROM public.command_authority_operation
                 WHERE organization_id='$V042_ORGANIZATION'::uuid
                   AND operation_id='$V042_OPERATION'::uuid
                """.trimIndent()
            )
        )
        val originalReplayAfterConflict = beginV042Principal()
        assertEquals("ALREADY_APPLIED", originalReplayAfterConflict.outcome)
        assertEquals(applied.operationId, originalReplayAfterConflict.operationId)
        assertEquals(applied.intentFingerprint, originalReplayAfterConflict.intentFingerprint)
        assertEquals(applied.receiptFingerprint, originalReplayAfterConflict.receiptFingerprint)
        assertEquals(applied.effectTime, originalReplayAfterConflict.effectTime)
        assertEquals(beforeChangedIntent, durableState(), "conflicting reuse poisoned historical replay")

        val secondOperation = v042SyntheticUuid(907)
        val secondPrincipal = v042SyntheticUuid(908)
        assertEquals(
            0,
            scalarInt("SELECT count(*) FROM public.command_authority_operation WHERE organization_id='$V042_ORGANIZATION'::uuid AND operation_id='$secondOperation'::uuid")
        )
        assertEquals(
            0,
            scalarInt("SELECT count(*) FROM public.command_principal WHERE organization_id='$V042_ORGANIZATION'::uuid AND principal_id='$secondPrincipal'::uuid")
        )
        val rootAPrincipal = scalarString(
            "SELECT principal_id||'|'||mercado_livre_connection_id||'|'||omie_connection_id||'|'||correlation_id||'|'||decided_at::text FROM public.command_principal"
        )
        val rootAConsumption = scalarString(
            "SELECT organization_id||'|'||manifest_id||'|'||principal_id||'|'||manifest_digest||'|'||correlation_id||'|'||consumed_at::text FROM public.s2a_attestation_consumption"
        )
        val rootAOperation = scalarString(
            "SELECT operation_id||'|'||principal_id||'|'||attestation_manifest_id||'|'||intent_fingerprint||'|'||receipt_fingerprint||'|'||correlation_id||'|'||decided_at::text FROM public.command_authority_operation"
        )
        val beforeSecondRoot = durableState()
        val secondBegin = beginV042Principal(secondOperation, secondPrincipal)
        assertEquals("READY", secondBegin.outcome)
        assertEquals(beforeSecondRoot, durableState(), "second-root BEGIN changed durable state")
        val secondRootFailure = captureDbFailure {
            applyV042Principal(secondBegin, secondOperation, secondPrincipal)
        }
        assertEquals("P0016", secondRootFailure.sqlState)
        assertEquals("GOVERNANCE_CONFLICT", secondRootFailure.detail)
        assertEquals(beforeSecondRoot, durableState(), "second-root denial changed durable state")
        assertEquals(rootAPrincipal, scalarString(
            "SELECT principal_id||'|'||mercado_livre_connection_id||'|'||omie_connection_id||'|'||correlation_id||'|'||decided_at::text FROM public.command_principal"
        ))
        assertEquals(rootAConsumption, scalarString(
            "SELECT organization_id||'|'||manifest_id||'|'||principal_id||'|'||manifest_digest||'|'||correlation_id||'|'||consumed_at::text FROM public.s2a_attestation_consumption"
        ))
        assertEquals(rootAOperation, scalarString(
            "SELECT operation_id||'|'||principal_id||'|'||attestation_manifest_id||'|'||intent_fingerprint||'|'||receipt_fingerprint||'|'||correlation_id||'|'||decided_at::text FROM public.command_authority_operation"
        ))
        assertEquals(1, tableCount("command_principal"))
        assertEquals(1, tableCount("command_authority_operation"))
        assertEquals(1, tableCount("s2a_attestation_consumption"))
        assertEquals(
            0,
            scalarInt("SELECT count(*) FROM public.command_principal WHERE principal_id='$secondPrincipal'::uuid")
        )
        assertEquals(
            0,
            scalarInt("SELECT count(*) FROM public.command_authority_operation WHERE operation_id='$secondOperation'::uuid")
        )
        val originalRootReplay = beginV042Principal()
        assertEquals("ALREADY_APPLIED", originalRootReplay.outcome)
        assertEquals(applied.operationId, originalRootReplay.operationId)
        assertEquals(applied.intentFingerprint, originalRootReplay.intentFingerprint)
        assertEquals(applied.receiptFingerprint, originalRootReplay.receiptFingerprint)
        assertEquals(applied.effectTime, originalRootReplay.effectTime)
        assertEquals(beforeSecondRoot, durableState(), "second-root denial poisoned original replay")
    }

    @Test
    fun `V042 real V041 principal and initial credential execution chain`() {
        installV042PrincipalFixture()
        val manifest = v042FrozenAuthorityManifest()
        assertEquals(
            "209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0",
            ApprovalManifestCanonicalCodec.manifestDigest(ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest))
        )
        assertIs<AcceptedAttestationResult.Accepted>(v042Verifier().verify(signedV042(manifest)))
        assertEquals(0, tableCount("command_principal"))
        assertEquals(0, tableCount("s2a_attestation_consumption"))
        assertEquals(0, tableCount("command_authority_operation"))
        val acceptedArtifactBeforeAuthority = scalarString(
            "SELECT row_to_json(a)::text FROM public.s2a_accepted_attestation a " +
                "WHERE a.organization_id='$V042_ORGANIZATION'::uuid AND a.manifest_id='$V042_MANIFEST'::uuid"
        )

        val principalBegin = beginV042Principal(
            provenance = "revision-6-golden-vector",
            correlationId = UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"),
            revocationOwner = UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            credentialCustodian = UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            credentialRotationOwner = UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        )
        assertEquals("READY", principalBegin.outcome)
        val beforePrincipalApply = durableState()
        val principalApply = applyV042Principal(
            principalBegin,
            provenance = "revision-6-golden-vector",
            correlationId = UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"),
            revocationOwner = UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            credentialCustodian = UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            credentialRotationOwner = UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        )
        assertEquals("APPLIED", principalApply.outcome)
        assertEquals(principalBegin.intentFingerprint, principalApply.intentFingerprint)
        assertEquals(1, tableCount("command_principal"))
        assertEquals(1, tableCount("s2a_attestation_consumption"))
        assertEquals(1, tableCount("command_authority_operation"))
        assertFalse(beforePrincipalApply == durableState())

        val verifier = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f".hex()
        val beforeInitialBegin = durableState()
        val initialBegin = beginAttestedInitialCredentialVerification(
            V042_ORGANIZATION, V042_MANIFEST, V042_INITIAL_CREDENTIAL_OPERATION, V042_PRINCIPAL,
            V042_CREDENTIAL, verifier, 1, V042_MANIFEST, V042_ORGANIZATION, V042_ML_CONNECTION,
            V042_OMIE_CONNECTION, "SO-2026-0001", "INT-2026-0001", V042_MARKETPLACE_ORDER,
            "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE,
            Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), "PROTECTED_TTY_ONE_TIME", UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
            "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval", "revision-6-golden-vector",
            UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), V042_EVIDENCE_FINGERPRINT
        )
        assertEquals("READY", initialBegin.outcome)
        assertEquals(V042_INITIAL_CREDENTIAL_OPERATION, initialBegin.operationId)
        assertEquals(null, initialBegin.receiptFingerprint)
        assertEquals(null, initialBegin.effectTime)
        assertEquals(principalBegin.acceptedProofFingerprint, initialBegin.acceptedProofFingerprint)
        assertEquals(V042_EVIDENCE_FINGERPRINT, initialBegin.signedEvidenceBinding)
        assertEquals(V042_EVIDENCE_FINGERPRINT, initialBegin.currentEvidenceBinding)
        assertEquals(beforeInitialBegin, durableState(), "INITIAL_CREDENTIAL BEGIN changed durable state")

        val initialApply = applyAttestedInitialCredentialVerification(
            V042_ORGANIZATION, V042_MANIFEST, V042_INITIAL_CREDENTIAL_OPERATION, V042_PRINCIPAL,
            V042_CREDENTIAL, verifier, initialBegin.schemaVersion, V042_MANIFEST, V042_ORGANIZATION,
            V042_ML_CONNECTION, V042_OMIE_CONNECTION, "SO-2026-0001", "INT-2026-0001",
            V042_MARKETPLACE_ORDER, "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT,
            V042_APPROVAL_SOURCE, Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL),
            UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"), UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), "PROTECTED_TTY_ONE_TIME", UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
            "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval", "revision-6-golden-vector",
            UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), V042_EVIDENCE_FINGERPRINT,
            initialBegin.artifactVersion, initialBegin.canonicalizationVersion, initialBegin.canonicalManifestBytes,
            initialBegin.manifestDigest, initialBegin.signaturePreimageBytes, initialBegin.algorithmId,
            initialBegin.signerSubjectId, initialBegin.signerKeyId, initialBegin.signerKeyRevision,
            initialBegin.signerKeyFingerprint, initialBegin.signerKeyLineageFingerprint,
            initialBegin.subjectPublicKeyInfoDer, initialBegin.signatureBytes, initialBegin.signerAuthorityId,
            initialBegin.signerAuthorityRevision, initialBegin.signerAuthorityFingerprint, initialBegin.verifiedAt,
            initialBegin.acceptedProofFingerprint, initialBegin.signedEvidenceBinding
        )
        assertEquals("APPLIED", initialApply.outcome)
        assertEquals(V042_INITIAL_CREDENTIAL_OPERATION, initialApply.operationId)
        assertEquals(initialBegin.intentFingerprint, initialApply.intentFingerprint)
        assertNotNull(initialApply.receiptFingerprint)
        assertNotNull(initialApply.effectTime)
        assertEquals(1, tableCount("command_principal"))
        assertEquals(1, tableCount("s2a_attestation_consumption"))
        assertEquals(2, tableCount("command_authority_operation"))
        assertEquals(1, tableCount("command_credential_revision"))
        assertEquals(0, tableCount("command_permission_grant"))
        assertEquals(0, tableCount("marketplace_transaction_identity_decision"))
        assertEquals(
            "$V042_ORGANIZATION|$V042_PRINCIPAL|$V042_CREDENTIAL|1|ENABLED",
            scalarString("SELECT organization_id||'|'||principal_id||'|'||credential_id||'|'||revision||'|'||state FROM public.command_credential_revision")
        )
        assertEquals(1, scalarInt("SELECT count(*) FROM public.command_authority_operation WHERE operation='INITIAL_CREDENTIAL'"))
        assertEquals(
            acceptedArtifactBeforeAuthority,
            scalarString(
                "SELECT row_to_json(a)::text FROM public.s2a_accepted_attestation a " +
                    "WHERE a.organization_id='$V042_ORGANIZATION'::uuid AND a.manifest_id='$V042_MANIFEST'::uuid"
            ),
            "V042 authority effects mutated the accepted V041 artifact"
        )
    }

    @Test
    fun `V042 initial credential exact replay rejects changed verifier and reason`() {
        installV042PrincipalFixture()
        val manifest = v042FrozenAuthorityManifest()
        assertIs<AcceptedAttestationResult.Accepted>(v042Verifier().verify(signedV042(manifest)))
        val acceptedArtifact = scalarString("SELECT row_to_json(a)::text FROM public.s2a_accepted_attestation a WHERE a.organization_id='$V042_ORGANIZATION'::uuid AND a.manifest_id='$V042_MANIFEST'::uuid")
        val principalBegin = beginV042Principal(provenance = "revision-6-golden-vector", correlationId = UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), revocationOwner = UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"), credentialCustodian = UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), credentialRotationOwner = UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd"))
        assertEquals("READY", principalBegin.outcome)
        assertEquals("APPLIED", applyV042Principal(principalBegin, provenance = "revision-6-golden-vector", correlationId = UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), revocationOwner = UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"), credentialCustodian = UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), credentialRotationOwner = UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd")).outcome)
        val verifier = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f".hex()
        fun begin(verifierValue: ByteArray = verifier, reason: String = "S2A field proof approval") = beginAttestedInitialCredentialVerification(V042_ORGANIZATION, V042_MANIFEST, V042_INITIAL_CREDENTIAL_OPERATION, V042_PRINCIPAL, V042_CREDENTIAL, verifierValue, 1, V042_MANIFEST, V042_ORGANIZATION, V042_ML_CONNECTION, V042_OMIE_CONNECTION, "SO-2026-0001", "INT-2026-0001", V042_MARKETPLACE_ORDER, "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE, Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"), UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), "PROTECTED_TTY_ONE_TIME", UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd"), "SEPARATE_APPROVAL_REQUIRED", reason, "revision-6-golden-vector", UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), V042_EVIDENCE_FINGERPRINT)
        val original = begin()
        assertEquals("READY", original.outcome)
        val applied = applyAttestedInitialCredentialVerification(V042_ORGANIZATION, V042_MANIFEST, V042_INITIAL_CREDENTIAL_OPERATION, V042_PRINCIPAL, V042_CREDENTIAL, verifier, original.schemaVersion, V042_MANIFEST, V042_ORGANIZATION, V042_ML_CONNECTION, V042_OMIE_CONNECTION, "SO-2026-0001", "INT-2026-0001", V042_MARKETPLACE_ORDER, "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE, Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"), UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"), "PROTECTED_TTY_ONE_TIME", UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd"), "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval", "revision-6-golden-vector", UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), V042_EVIDENCE_FINGERPRINT, original.artifactVersion, original.canonicalizationVersion, original.canonicalManifestBytes, original.manifestDigest, original.signaturePreimageBytes, original.algorithmId, original.signerSubjectId, original.signerKeyId, original.signerKeyRevision, original.signerKeyFingerprint, original.signerKeyLineageFingerprint, original.subjectPublicKeyInfoDer, original.signatureBytes, original.signerAuthorityId, original.signerAuthorityRevision, original.signerAuthorityFingerprint, original.verifiedAt, original.acceptedProofFingerprint, original.signedEvidenceBinding)
        assertEquals("APPLIED", applied.outcome)
        val durableAfterApply = durableState()
        fun assertReplay() {
            val replay = begin()
            assertEquals("ALREADY_APPLIED", replay.outcome)
            assertEquals(applied.operationId, replay.operationId)
            assertEquals(applied.intentFingerprint, replay.intentFingerprint)
            assertEquals(applied.receiptFingerprint, replay.receiptFingerprint)
            assertEquals(applied.effectTime, replay.effectTime)
            assertEquals(original.artifactVersion, replay.artifactVersion)
            assertEquals(original.schemaVersion, replay.schemaVersion)
            assertEquals(original.canonicalizationVersion, replay.canonicalizationVersion)
            assertTrue(original.canonicalManifestBytes.contentEquals(replay.canonicalManifestBytes))
            assertEquals(original.manifestDigest, replay.manifestDigest)
            assertTrue(original.signaturePreimageBytes.contentEquals(replay.signaturePreimageBytes))
            assertEquals(original.algorithmId, replay.algorithmId)
            assertEquals(original.signerSubjectId, replay.signerSubjectId)
            assertEquals(original.signerKeyId, replay.signerKeyId)
            assertEquals(original.signerKeyRevision, replay.signerKeyRevision)
            assertEquals(original.signerKeyFingerprint, replay.signerKeyFingerprint)
            assertEquals(original.signerKeyLineageFingerprint, replay.signerKeyLineageFingerprint)
            assertTrue(original.subjectPublicKeyInfoDer.contentEquals(replay.subjectPublicKeyInfoDer))
            assertTrue(original.signatureBytes.contentEquals(replay.signatureBytes))
            assertEquals(original.signerAuthorityId, replay.signerAuthorityId)
            assertEquals(original.signerAuthorityRevision, replay.signerAuthorityRevision)
            assertEquals(original.signerAuthorityFingerprint, replay.signerAuthorityFingerprint)
            assertEquals(original.verifiedAt, replay.verifiedAt)
            assertEquals(original.acceptedProofFingerprint, replay.acceptedProofFingerprint)
            assertEquals(original.signedEvidenceBinding, replay.signedEvidenceBinding)
            assertEquals(null, replay.currentEvidenceBinding)
            assertEquals(null, replay.observedEffectTime)
            assertEquals(null, replay.observedEffectiveKeyRevision)
            assertEquals(null, replay.observedEffectiveKeyState)
            assertEquals(null, replay.observedCurrentAuthorityId)
            assertEquals(null, replay.observedCurrentAuthorityRevision)
            assertEquals(null, replay.observedCurrentAuthorityFingerprint)
            assertEquals(durableAfterApply, durableState(), "exact replay changed durable state")
        }
        assertReplay()
        val changedVerifier = verifier.copyOf().also { it[0] = (it[0].toInt() xor 1).toByte() }
        val verifierFailure = captureDbFailure { begin(changedVerifier) }
        assertEquals("P0018", verifierFailure.sqlState)
        assertEquals("Historical operation fingerprint integrity failure", verifierFailure.primaryMessage)
        assertEquals("INTEGRITY_FAILURE", verifierFailure.detail)
        assertEquals(durableAfterApply, durableState(), "changed verifier changed durable state")
        assertReplay()
        val reasonFailure = captureDbFailure { begin(reason = "S2A field proof approval changed intent") }
        assertEquals("P0018", reasonFailure.sqlState)
        assertEquals("Historical operation fingerprint integrity failure", reasonFailure.primaryMessage)
        assertEquals("INTEGRITY_FAILURE", reasonFailure.detail)
        assertEquals(durableAfterApply, durableState(), "changed reason changed durable state")
        assertReplay()
        assertEquals(acceptedArtifact, scalarString("SELECT row_to_json(a)::text FROM public.s2a_accepted_attestation a WHERE a.organization_id='$V042_ORGANIZATION'::uuid AND a.manifest_id='$V042_MANIFEST'::uuid"))
        assertEquals(1, tableCount("command_principal"))
        assertEquals(1, tableCount("s2a_attestation_consumption"))
        assertEquals(2, tableCount("command_authority_operation"))
        assertEquals(1, tableCount("command_credential_revision"))
        assertEquals(1, scalarInt("SELECT count(*) FROM public.command_authority_operation WHERE operation='INITIAL_CREDENTIAL'"))
        assertEquals(0, tableCount("command_permission_grant"))
        assertEquals(0, tableCount("marketplace_transaction_identity_decision"))
    }

    @Test
    fun `V042 grant exact replay rejects changed reason`() {
        installV042PrincipalFixture()
        val manifest = v042FrozenAuthorityManifest()
        assertIs<AcceptedAttestationResult.Accepted>(v042Verifier().verify(signedV042(manifest)))
        val acceptedArtifact = scalarString("SELECT row_to_json(a)::text FROM public.s2a_accepted_attestation a WHERE a.organization_id='$V042_ORGANIZATION'::uuid AND a.manifest_id='$V042_MANIFEST'::uuid")
        val principalBegin = beginV042Principal(provenance = "revision-6-golden-vector", correlationId = V042_CORRELATION, revocationOwner = V042_REVOCATION_OWNER, credentialCustodian = V042_CREDENTIAL_CUSTODIAN, credentialRotationOwner = V042_ROTATION_OWNER)
        assertEquals("READY", principalBegin.outcome)
        assertEquals("APPLIED", applyV042Principal(principalBegin, provenance = "revision-6-golden-vector", correlationId = V042_CORRELATION, revocationOwner = V042_REVOCATION_OWNER, credentialCustodian = V042_CREDENTIAL_CUSTODIAN, credentialRotationOwner = V042_ROTATION_OWNER).outcome)

        fun begin(reason: String = "S2A field proof approval") = beginAttestedGrantVerification(
            V042_ORGANIZATION, V042_MANIFEST, V042_GRANT_OPERATION, V042_PRINCIPAL, V042_GRANT,
            1, V042_MANIFEST, V042_ORGANIZATION, V042_ML_CONNECTION, V042_OMIE_CONNECTION,
            "SO-2026-0001", "INT-2026-0001", V042_MARKETPLACE_ORDER,
            "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE,
            Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), V042_REVOCATION_OWNER,
            V042_CREDENTIAL_CUSTODIAN, "PROTECTED_TTY_ONE_TIME", V042_ROTATION_OWNER,
            "SEPARATE_APPROVAL_REQUIRED", reason, "revision-6-golden-vector", V042_CORRELATION,
            V042_EVIDENCE_FINGERPRINT
        )

        fun apply(snapshot: V042InitialCredentialBeginResult, reason: String = "S2A field proof approval") =
            applyAttestedGrantVerification(
                V042_ORGANIZATION, V042_MANIFEST, V042_GRANT_OPERATION, V042_PRINCIPAL, V042_GRANT,
                snapshot.schemaVersion, V042_MANIFEST, V042_ORGANIZATION, V042_ML_CONNECTION,
                V042_OMIE_CONNECTION, "SO-2026-0001", "INT-2026-0001", V042_MARKETPLACE_ORDER,
                "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE,
                Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), V042_REVOCATION_OWNER,
                V042_CREDENTIAL_CUSTODIAN, "PROTECTED_TTY_ONE_TIME", V042_ROTATION_OWNER,
                "SEPARATE_APPROVAL_REQUIRED", reason, "revision-6-golden-vector", V042_CORRELATION,
                V042_EVIDENCE_FINGERPRINT, snapshot.artifactVersion, snapshot.canonicalizationVersion,
                snapshot.canonicalManifestBytes, snapshot.manifestDigest, snapshot.signaturePreimageBytes,
                snapshot.algorithmId, snapshot.signerSubjectId, snapshot.signerKeyId, snapshot.signerKeyRevision,
                snapshot.signerKeyFingerprint, snapshot.signerKeyLineageFingerprint,
                snapshot.subjectPublicKeyInfoDer, snapshot.signatureBytes, snapshot.signerAuthorityId,
                snapshot.signerAuthorityRevision, snapshot.signerAuthorityFingerprint, snapshot.verifiedAt,
                snapshot.acceptedProofFingerprint, snapshot.signedEvidenceBinding
            )

        val original = begin()
        assertEquals("READY", original.outcome)
        assertEquals(V042_SUBJECT, original.signerSubjectId)
        assertEquals(V042_EVIDENCE_FINGERPRINT, original.currentEvidenceBinding)
        val applied = apply(original)
        assertEquals("APPLIED", applied.outcome)
        val durableAfterApply = durableState()

        fun assertReplay() {
            val replay = begin()
            assertEquals("ALREADY_APPLIED", replay.outcome)
            assertEquals(applied.operationId, replay.operationId)
            assertEquals(applied.intentFingerprint, replay.intentFingerprint)
            assertEquals(applied.receiptFingerprint, replay.receiptFingerprint)
            assertEquals(applied.effectTime, replay.effectTime)
            assertEquals(original.signerSubjectId, replay.signerSubjectId)
            assertEquals(original.signerKeyId, replay.signerKeyId)
            assertEquals(original.signerKeyRevision, replay.signerKeyRevision)
            assertEquals(original.signerAuthorityId, replay.signerAuthorityId)
            assertEquals(original.signerAuthorityRevision, replay.signerAuthorityRevision)
            assertEquals(null, replay.currentEvidenceBinding)
            assertEquals(null, replay.observedEffectTime)
            assertEquals(null, replay.observedEffectiveKeyRevision)
            assertEquals(null, replay.observedEffectiveKeyState)
            assertEquals(null, replay.observedCurrentAuthorityId)
            assertEquals(null, replay.observedCurrentAuthorityRevision)
            assertEquals(null, replay.observedCurrentAuthorityFingerprint)
            assertEquals("ALREADY_APPLIED", apply(replay).outcome)
            assertEquals(durableAfterApply, durableState(), "exact GRANT replay changed durable state")
        }

        assertReplay()
        val reasonFailure = captureDbFailure { begin("S2A field proof approval changed intent") }
        assertEquals("P0018", reasonFailure.sqlState)
        assertEquals("Historical operation fingerprint integrity failure", reasonFailure.primaryMessage)
        assertEquals("INTEGRITY_FAILURE", reasonFailure.detail)
        assertEquals(durableAfterApply, durableState(), "changed GRANT reason changed durable state")
        assertReplay()
        v042Update(
            "UPDATE public.integration_organization SET status='SUSPENDED' WHERE organization_id=?",
            V042_ORGANIZATION
        )
        val suspendedState = durableState()
        val historicalReplay = begin()
        assertEquals("ALREADY_APPLIED", historicalReplay.outcome)
        assertEquals(null, historicalReplay.currentEvidenceBinding)
        assertEquals(null, historicalReplay.observedEffectTime)
        assertEquals("ALREADY_APPLIED", apply(historicalReplay).outcome)
        assertEquals(suspendedState, durableState(), "historical GRANT replay required fresh currentness")
        assertEquals(acceptedArtifact, scalarString("SELECT row_to_json(a)::text FROM public.s2a_accepted_attestation a WHERE a.organization_id='$V042_ORGANIZATION'::uuid AND a.manifest_id='$V042_MANIFEST'::uuid"))
        assertEquals(1, tableCount("command_principal"))
        assertEquals(1, tableCount("s2a_attestation_consumption"))
        assertEquals(2, tableCount("command_authority_operation"))
        assertEquals(0, tableCount("command_credential_revision"))
        assertEquals(1, tableCount("command_permission_grant"))
        assertEquals(0, tableCount("marketplace_transaction_identity_decision"))
    }

    @Test
    fun `V042 attested decision applies and replays only after predecessor authorization`() {
        installV042PrincipalFixture(decisionCompatible = true)
        val decisionIntegrationReference = "MLB-123456789"
        val decisionEvidenceFingerprint = scalarString(
            "SELECT public.s2a_v041_evidence_fingerprint(" +
                "'$V042_ORGANIZATION'::uuid,'$V042_MARKETPLACE_ORDER'::uuid," +
                "'$V042_ML_CONNECTION'::uuid,'$V042_OMIE_CONNECTION'::uuid," +
                "'SO-2026-0001','$decisionIntegrationReference')"
        )
        val manifest = v042FrozenAuthorityManifest().copy(
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        )
        assertIs<AcceptedAttestationResult.Accepted>(v042Verifier().verify(signedV042(manifest)))
        val acceptedArtifact = scalarString(
            "SELECT row_to_json(a)::text FROM public.s2a_accepted_attestation a " +
                "WHERE a.organization_id='$V042_ORGANIZATION'::uuid AND a.manifest_id='$V042_MANIFEST'::uuid"
        )

        val principalBegin = beginV042Principal(
            provenance = "revision-6-golden-vector", correlationId = V042_CORRELATION,
            revocationOwner = V042_REVOCATION_OWNER, credentialCustodian = V042_CREDENTIAL_CUSTODIAN,
            credentialRotationOwner = V042_ROTATION_OWNER,
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        )
        assertEquals("APPLIED", applyV042Principal(
            principalBegin, provenance = "revision-6-golden-vector", correlationId = V042_CORRELATION,
            revocationOwner = V042_REVOCATION_OWNER, credentialCustodian = V042_CREDENTIAL_CUSTODIAN,
            credentialRotationOwner = V042_ROTATION_OWNER,
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        ).outcome)

        val verifier = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f".hex()
        val credentialBegin = beginAttestedInitialCredentialVerification(
            V042_ORGANIZATION, V042_MANIFEST, V042_INITIAL_CREDENTIAL_OPERATION, V042_PRINCIPAL,
            V042_CREDENTIAL, verifier, 1, V042_MANIFEST, V042_ORGANIZATION, V042_ML_CONNECTION,
            V042_OMIE_CONNECTION, "SO-2026-0001", decisionIntegrationReference, V042_MARKETPLACE_ORDER,
            "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE,
            Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), V042_REVOCATION_OWNER,
            V042_CREDENTIAL_CUSTODIAN, "PROTECTED_TTY_ONE_TIME", V042_ROTATION_OWNER,
            "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval", "revision-6-golden-vector",
            V042_CORRELATION, decisionEvidenceFingerprint
        )
        assertEquals("APPLIED", applyAttestedInitialCredentialVerification(
            V042_ORGANIZATION, V042_MANIFEST, V042_INITIAL_CREDENTIAL_OPERATION, V042_PRINCIPAL,
            V042_CREDENTIAL, verifier, credentialBegin.schemaVersion, V042_MANIFEST, V042_ORGANIZATION,
            V042_ML_CONNECTION, V042_OMIE_CONNECTION, "SO-2026-0001", decisionIntegrationReference,
            V042_MARKETPLACE_ORDER, "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT,
            V042_APPROVAL_SOURCE, Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL),
            V042_REVOCATION_OWNER, V042_CREDENTIAL_CUSTODIAN, "PROTECTED_TTY_ONE_TIME",
            V042_ROTATION_OWNER, "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval",
            "revision-6-golden-vector", V042_CORRELATION, decisionEvidenceFingerprint,
            credentialBegin.artifactVersion, credentialBegin.canonicalizationVersion,
            credentialBegin.canonicalManifestBytes, credentialBegin.manifestDigest,
            credentialBegin.signaturePreimageBytes, credentialBegin.algorithmId,
            credentialBegin.signerSubjectId, credentialBegin.signerKeyId, credentialBegin.signerKeyRevision,
            credentialBegin.signerKeyFingerprint, credentialBegin.signerKeyLineageFingerprint,
            credentialBegin.subjectPublicKeyInfoDer, credentialBegin.signatureBytes,
            credentialBegin.signerAuthorityId, credentialBegin.signerAuthorityRevision,
            credentialBegin.signerAuthorityFingerprint, credentialBegin.verifiedAt,
            credentialBegin.acceptedProofFingerprint, credentialBegin.signedEvidenceBinding
        ).outcome)

        val grantBegin = beginAttestedGrantVerification(
            V042_ORGANIZATION, V042_MANIFEST, V042_GRANT_OPERATION, V042_PRINCIPAL, V042_GRANT,
            1, V042_MANIFEST, V042_ORGANIZATION, V042_ML_CONNECTION, V042_OMIE_CONNECTION,
            "SO-2026-0001", decisionIntegrationReference, V042_MARKETPLACE_ORDER,
            "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE,
            Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), V042_REVOCATION_OWNER,
            V042_CREDENTIAL_CUSTODIAN, "PROTECTED_TTY_ONE_TIME", V042_ROTATION_OWNER,
            "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval", "revision-6-golden-vector",
            V042_CORRELATION, decisionEvidenceFingerprint
        )
        assertEquals("APPLIED", applyAttestedGrantVerification(
            V042_ORGANIZATION, V042_MANIFEST, V042_GRANT_OPERATION, V042_PRINCIPAL, V042_GRANT,
            grantBegin.schemaVersion, V042_MANIFEST, V042_ORGANIZATION, V042_ML_CONNECTION,
            V042_OMIE_CONNECTION, "SO-2026-0001", decisionIntegrationReference, V042_MARKETPLACE_ORDER,
            "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE,
            Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), V042_REVOCATION_OWNER,
            V042_CREDENTIAL_CUSTODIAN, "PROTECTED_TTY_ONE_TIME", V042_ROTATION_OWNER,
            "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval", "revision-6-golden-vector",
            V042_CORRELATION, decisionEvidenceFingerprint, grantBegin.artifactVersion,
            grantBegin.canonicalizationVersion, grantBegin.canonicalManifestBytes, grantBegin.manifestDigest,
            grantBegin.signaturePreimageBytes, grantBegin.algorithmId, grantBegin.signerSubjectId,
            grantBegin.signerKeyId, grantBegin.signerKeyRevision, grantBegin.signerKeyFingerprint,
            grantBegin.signerKeyLineageFingerprint, grantBegin.subjectPublicKeyInfoDer,
            grantBegin.signatureBytes, grantBegin.signerAuthorityId, grantBegin.signerAuthorityRevision,
            grantBegin.signerAuthorityFingerprint, grantBegin.verifiedAt,
            grantBegin.acceptedProofFingerprint, grantBegin.signedEvidenceBinding
        ).outcome)

        val beforeFinalAdversarials = durableState()

        val crossOrganizationAttempt = captureDbFailure {
            beginAttestedDecision(
                decisionId = v042SyntheticUuid(916),
                organizationId = v042SyntheticUuid(917),
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
        }

        assertEquals("P0012", crossOrganizationAttempt.sqlState)
        assertEquals(
            "Command authority unavailable",
            crossOrganizationAttempt.primaryMessage
        )
        assertEquals(null, crossOrganizationAttempt.detail)

        assertEquals(
            beforeFinalAdversarials,
            durableState(),
            "cross-organization attested decision attempt changed durable state"
        )

        val authorizationFingerprint = scalarString(
            "SELECT public.transaction_identity_grant_fingerprint('$V042_ORGANIZATION'::uuid,'$V042_GRANT'::uuid)"
        )
        val intentFingerprint = scalarString(
            "SELECT public.transaction_identity_hash('transaction-identity-intent/1','$V042_ORGANIZATION'," +
                "'$V042_PRINCIPAL','$V042_ML_CONNECTION','$V042_OMIE_CONNECTION','SO-2026-0001'," +
                "'$V042_MARKETPLACE_ORDER','CONFIRMED','EXPLICIT_CONFIRMATION','revision-6-golden-vector','')"
        )
        val semanticFingerprint = scalarString(
            "SELECT public.transaction_identity_hash('transaction-identity/1','$intentFingerprint'," +
                "'$V042_ML_CONNECTION','$V042_ML_CAPABILITY','1','1','MLB-123456789','BRL'," +
                "'$V042_OMIE_CAPABILITY','1','${"ab".repeat(32)}','2026-09-25T11:59:59.123456'," +
                "'$V042_GRANT','1','TRANSACTION_IDENTITY_DECISION_WRITE','command-authorization/1'," +
                "'$authorizationFingerprint')"
        )

        val legacyRouteMismatchDecision = v042SyntheticUuid(918)

        val legacyRouteMismatch = captureDbFailure {
            connection().use { c ->
                c.createStatement().use {
                    it.execute("SET ROLE flooow_command_runtime")
                }

                val values = listOf(
                    V042_ORGANIZATION,
                    legacyRouteMismatchDecision,
                    V042_OMIE_CONNECTION,
                    "SO-2026-0001",
                    V042_MARKETPLACE_ORDER,
                    "CONFIRMED",
                    "EXPLICIT_CONFIRMATION",
                    1,
                    null,
                    V042_ML_CONNECTION,
                    V042_ML_CAPABILITY,
                    1L,
                    1,
                    "MLB-123456789",
                    "BRL",
                    V042_OMIE_CAPABILITY,
                    1L,
                    1,
                    "ab".repeat(32),
                    LocalDateTime.parse("2026-09-25T11:59:59.123456"),
                    V042_PRINCIPAL,
                    V042_CREDENTIAL,
                    1,
                    V042_GRANT,
                    1,
                    "TRANSACTION_IDENTITY_DECISION_WRITE",
                    "command-authorization/1",
                    authorizationFingerprint,
                    intentFingerprint,
                    semanticFingerprint,
                    "revision-6-golden-vector",
                    V042_CORRELATION
                )

                assertEquals(
                    32,
                    values.size,
                    "legacy-unlinked adversarial parameter count drift"
                )

                c.prepareStatement(
                    "SELECT * FROM public.s2a_v042_apply_legacy_unlinked_decision(" +
                        List(values.size) { "?" }.joinToString() +
                        ")"
                ).use { s ->
                    values.forEachIndexed { index, value ->
                        s.setObject(index + 1, value)
                    }
                    s.executeQuery().close()
                }
            }
        }

        assertEquals("P0018", legacyRouteMismatch.sqlState)
        assertEquals(
            "Legacy-unlinked route mismatch",
            legacyRouteMismatch.primaryMessage
        )
        assertEquals("ROUTE_MISMATCH", legacyRouteMismatch.detail)

        assertEquals(
            beforeFinalAdversarials,
            durableState(),
            "legacy route mismatch attempt changed durable state"
        )

        val beforeBegin = durableState()
        val begin = beginAttestedDecision(
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        )
        assertEquals("READY", begin.outcome)
        assertEquals(V042_DECISION, begin.decisionId)
        assertEquals(V042_MANIFEST, begin.manifestId)
        assertEquals(null, begin.semanticFingerprint)
        assertEquals(null, begin.decidedAt)
        assertEquals(beforeBegin, durableState(), "attested decision BEGIN changed durable state")

        val applied = applyAttestedDecision(
            begin, authorizationFingerprint, intentFingerprint, semanticFingerprint,
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        )
        assertEquals("APPLIED", applied.outcome)
        assertEquals(V042_DECISION, applied.decisionId)
        assertEquals(semanticFingerprint, applied.semanticFingerprint)
        assertNotNull(applied.decidedAt)
        val durableAfterApply = durableState()

        val replayBegin = beginAttestedDecision(
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        )
        assertEquals("ALREADY_APPLIED", replayBegin.outcome)
        assertEquals(applied.decisionId, replayBegin.decisionId)
        assertEquals(applied.semanticFingerprint, replayBegin.semanticFingerprint)
        assertEquals(applied.decidedAt, replayBegin.decidedAt)
        assertEquals(null, replayBegin.manifestId)
        assertEquals("ALREADY_APPLIED", applyAttestedDecision(
            begin, authorizationFingerprint, intentFingerprint, semanticFingerprint,
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        ).outcome)
        assertEquals(durableAfterApply, durableState(), "exact attested decision replay changed durable state")

        v042Update("UPDATE public.integration_organization SET status='SUSPENDED' WHERE organization_id=?", V042_ORGANIZATION)
        val suspendedFailure = captureDbFailure {
            beginAttestedDecision(
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
        }
        assertEquals("P0012", suspendedFailure.sqlState)
        assertEquals("Command authority unavailable", suspendedFailure.primaryMessage)
        assertEquals(null, suspendedFailure.detail)
        v042Update("UPDATE public.integration_organization SET status='ACTIVE' WHERE organization_id=?", V042_ORGANIZATION)
        assertEquals("ALREADY_APPLIED", beginAttestedDecision(
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        ).outcome)

        fun assertOriginalReplayStillValid() {
            val replay = beginAttestedDecision(
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
            assertEquals("ALREADY_APPLIED", replay.outcome)
            assertEquals(applied.decisionId, replay.decisionId)
            assertEquals(applied.semanticFingerprint, replay.semanticFingerprint)
            assertEquals(applied.decidedAt, replay.decidedAt)
            assertEquals(durableAfterApply, durableState(), "adversarial decision attempt changed durable state")
        }

        val changedReason = captureDbFailure {
            applyAttestedDecision(
                begin, authorizationFingerprint, intentFingerprint, semanticFingerprint,
                decisionReason = "EXPLICIT_REJECTION",
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
        }
        assertEquals("23514", changedReason.sqlState)
        assertEquals("Decision replay integrity failure", changedReason.primaryMessage)
        assertEquals(null, changedReason.detail)
        assertOriginalReplayStillValid()

        val wrongGrant = captureDbFailure {
            beginAttestedDecision(
                grantId = v042SyntheticUuid(910),
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
        }
        assertEquals("P0012", wrongGrant.sqlState)
        assertEquals("Command authority unavailable", wrongGrant.primaryMessage)
        assertEquals(null, wrongGrant.detail)
        assertOriginalReplayStillValid()

        val wrongRevision = captureDbFailure {
            beginAttestedDecision(
                grantRevision = 2,
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
        }
        assertEquals("P0012", wrongRevision.sqlState)
        assertEquals("Command authority unavailable", wrongRevision.primaryMessage)
        assertEquals(null, wrongRevision.detail)
        assertOriginalReplayStillValid()

        val wrongManifest = captureDbFailure {
            beginAttestedDecision(
                decisionId = v042SyntheticUuid(911),
                claimManifestId = v042SyntheticUuid(912),
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
        }
        assertEquals("P0017", wrongManifest.sqlState)
        assertEquals("Linked grant manifest scope mismatch", wrongManifest.primaryMessage)
        assertEquals("SCOPE_MISMATCH", wrongManifest.detail)
        assertOriginalReplayStillValid()

        val crossPrincipal = captureDbFailure {
            beginAttestedDecision(
                decisionId = v042SyntheticUuid(913),
                principalId = v042SyntheticUuid(914),
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
        }
        assertEquals("P0012", crossPrincipal.sqlState)
        assertEquals("Command authority unavailable", crossPrincipal.primaryMessage)
        assertEquals(null, crossPrincipal.detail)
        assertOriginalReplayStillValid()

        val secondDecisionId = v042SyntheticUuid(915)
        val secondBegin = beginAttestedDecision(
            decisionId = secondDecisionId,
            integrationReference = decisionIntegrationReference,
            evidenceBindingFingerprint = decisionEvidenceFingerprint
        )
        assertEquals("READY", secondBegin.outcome)
        val secondDecision = captureDbFailure {
            applyAttestedDecision(
                secondBegin, authorizationFingerprint, intentFingerprint, semanticFingerprint,
                decisionId = secondDecisionId,
                integrationReference = decisionIntegrationReference,
                evidenceBindingFingerprint = decisionEvidenceFingerprint
            )
        }
        assertEquals("P0018", secondDecision.sqlState)
        assertEquals("Linked grant action already consumed", secondDecision.primaryMessage)
        assertEquals("SINGLE_ACTION_CONSUMED", secondDecision.detail)
        assertOriginalReplayStillValid()

        fun forbiddenFieldProofOperation(
            operationId: UUID,
            operation: String,
            credentialId: UUID?,
            credentialRevision: Int?,
            grantId: UUID?,
            grantRevision: Int?,
            permission: String?,
            state: String
        ): V042DbFailure = captureDbFailure {
            v042Update(
                """
                INSERT INTO public.command_authority_operation(
                    organization_id,operation_id,operation,principal_id,credential_id,credential_revision,
                    grant_id,grant_revision,permission,state,intent_fingerprint,receipt_fingerprint,
                    correlation_id,decided_at,attestation_manifest_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """.trimIndent(),
                V042_ORGANIZATION, operationId, operation, V042_PRINCIPAL, credentialId, credentialRevision,
                grantId, grantRevision, permission, state, "1".repeat(64), "2".repeat(64),
                V042_CORRELATION, Timestamp.from(V042_VALID_FROM), V042_MANIFEST
            )
        }

        val rotateDenial = forbiddenFieldProofOperation(
            v042SyntheticUuid(920), "ROTATE_CREDENTIAL", V042_CREDENTIAL, 1,
            null, null, null, "ENABLED"
        )
        assertEquals("23514", rotateDenial.sqlState)
        assertEquals(
            "new row for relation \"command_authority_operation\" violates check constraint " +
                "\"command_authority_operation_v042_attestation_kind_check\"",
            rotateDenial.primaryMessage
        )
        assertNotNull(rotateDenial.detail)
        assertTrue(rotateDenial.detail.contains("ROTATE_CREDENTIAL"))
        assertOriginalReplayStillValid()

        val revokeDenial = forbiddenFieldProofOperation(
            v042SyntheticUuid(921), "REVOKE", null, null,
            V042_GRANT, 1, "TRANSACTION_IDENTITY_DECISION_WRITE", "DISABLED"
        )
        assertEquals("23514", revokeDenial.sqlState)
        assertEquals(
            "new row for relation \"command_authority_operation\" violates check constraint " +
                "\"command_authority_operation_v042_attestation_kind_check\"",
            revokeDenial.primaryMessage
        )
        assertNotNull(revokeDenial.detail)
        assertTrue(revokeDenial.detail.contains("REVOKE"))
        assertOriginalReplayStillValid()

        assertEquals(acceptedArtifact, scalarString(
            "SELECT row_to_json(a)::text FROM public.s2a_accepted_attestation a " +
                "WHERE a.organization_id='$V042_ORGANIZATION'::uuid AND a.manifest_id='$V042_MANIFEST'::uuid"
        ))
        assertEquals(1, tableCount("marketplace_transaction_identity_decision"))
        assertEquals(1, tableCount("marketplace_transaction_identity_head"))
        assertEquals(3, tableCount("command_authority_operation"))
    }

    private fun beginAttestedDecision(
        decisionId: UUID = V042_DECISION,
        grantId: UUID = V042_GRANT,
        grantRevision: Int = 1,
        claimManifestId: UUID = V042_MANIFEST,
        principalId: UUID = V042_PRINCIPAL,
        organizationId: UUID = V042_ORGANIZATION,
        integrationReference: String = "INT-2026-0001",
        evidenceBindingFingerprint: String = V042_EVIDENCE_FINGERPRINT
    ): V042DecisionBeginResult = connection().use { c ->
        c.createStatement().use { it.execute("SET ROLE flooow_command_runtime") }
        val values = listOf(
            organizationId, principalId, grantId, grantRevision, decisionId,
            V042_OMIE_CONNECTION, "SO-2026-0001", V042_MARKETPLACE_ORDER,
            1, claimManifestId, organizationId, V042_ML_CONNECTION, V042_OMIE_CONNECTION,
            "SO-2026-0001", integrationReference, V042_MARKETPLACE_ORDER,
            "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE,
            Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), V042_REVOCATION_OWNER,
            V042_CREDENTIAL_CUSTODIAN, "PROTECTED_TTY_ONE_TIME", V042_ROTATION_OWNER,
            "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval", "revision-6-golden-vector",
            V042_CORRELATION, evidenceBindingFingerprint
        )
        assertEquals(30, values.size, "V042 DECISION BEGIN parameter count drift")
        c.prepareStatement(
            "SELECT * FROM public.s2a_v042_begin_attested_decision_verification(${List(values.size) { "?" }.joinToString()})"
        ).use { s ->
            values.forEachIndexed { index, value -> s.setObject(index + 1, value) }
            s.executeQuery().use { r ->
                assertTrue(r.next(), "V042 DECISION BEGIN returned no row")
                val value = V042DecisionBeginResult(
                    outcome = r.getString("outcome"),
                    decisionId = r.getObject("result_decision_id", UUID::class.java),
                    semanticFingerprint = r.getString("result_decision_semantic_fingerprint"),
                    decidedAt = r.getTimestamp("result_decided_at"),
                    manifestId = r.getObject("result_manifest_id", UUID::class.java),
                    artifactVersion = r.getObject("result_artifact_version", Int::class.javaObjectType),
                    schemaVersion = r.getObject("result_schema_version", Int::class.javaObjectType),
                    canonicalizationVersion = r.getObject("result_canonicalization_version", Int::class.javaObjectType),
                    canonicalManifestBytes = r.getBytes("result_canonical_manifest_bytes"),
                    manifestDigest = r.getString("result_manifest_digest"),
                    signaturePreimageBytes = r.getBytes("result_signature_preimage_bytes"),
                    algorithmId = r.getString("result_algorithm_id"),
                    signerSubjectId = r.getObject("result_signer_subject_id", UUID::class.java),
                    signerKeyId = r.getObject("result_signer_key_id", UUID::class.java),
                    signerKeyRevision = r.getObject("result_signer_key_revision", Int::class.javaObjectType),
                    signerKeyFingerprint = r.getString("result_signer_key_fingerprint"),
                    signerKeyLineageFingerprint = r.getString("result_signer_key_lineage_fingerprint"),
                    subjectPublicKeyInfoDer = r.getBytes("result_subject_public_key_info_der"),
                    signatureBytes = r.getBytes("result_signature_bytes"),
                    signerAuthorityId = r.getObject("result_signer_authority_id", UUID::class.java),
                    signerAuthorityRevision = r.getObject("result_signer_authority_revision", Int::class.javaObjectType),
                    signerAuthorityFingerprint = r.getString("result_signer_authority_fingerprint"),
                    verifiedAt = r.getTimestamp("result_verified_at"),
                    acceptedProofFingerprint = r.getString("result_accepted_proof_fingerprint"),
                    signedEvidenceBinding = r.getString("result_signed_evidence_binding_fingerprint")
                )
                assertFalse(r.next(), "V042 DECISION BEGIN returned more than one row")
                value
            }
        }
    }

    private fun applyAttestedDecision(
        snapshot: V042DecisionBeginResult,
        authorizationFingerprint: String,
        intentFingerprint: String,
        semanticFingerprint: String,
        decisionId: UUID = V042_DECISION,
        grantId: UUID = V042_GRANT,
        grantRevision: Int = 1,
        decisionReason: String = "EXPLICIT_CONFIRMATION",
        claimManifestId: UUID = V042_MANIFEST,
        principalId: UUID = V042_PRINCIPAL,
        integrationReference: String = "INT-2026-0001",
        evidenceBindingFingerprint: String = V042_EVIDENCE_FINGERPRINT
    ): V042DecisionApplyResult = connection().use { c ->
        c.createStatement().use { it.execute("SET ROLE flooow_command_runtime") }
        val values = listOf(
            V042_ORGANIZATION, decisionId, V042_OMIE_CONNECTION, "SO-2026-0001", V042_MARKETPLACE_ORDER,
            "CONFIRMED", decisionReason, 1, null, V042_ML_CONNECTION, V042_ML_CAPABILITY, 1L, 1,
            "MLB-123456789", "BRL", V042_OMIE_CAPABILITY, 1L, 1, "ab".repeat(32),
            LocalDateTime.parse("2026-09-25T11:59:59.123456"), principalId, V042_CREDENTIAL, 1,
            grantId, grantRevision, "TRANSACTION_IDENTITY_DECISION_WRITE", "command-authorization/1",
            authorizationFingerprint, intentFingerprint, semanticFingerprint, "revision-6-golden-vector",
            V042_CORRELATION, 1, claimManifestId, V042_ORGANIZATION, V042_ML_CONNECTION,
            V042_OMIE_CONNECTION, "SO-2026-0001", integrationReference, V042_MARKETPLACE_ORDER,
            "TRANSACTION_IDENTITY_DECISION_WRITE", V042_SUBJECT, V042_APPROVAL_SOURCE,
            Timestamp.from(V042_VALID_FROM), Timestamp.from(V042_VALID_UNTIL), V042_REVOCATION_OWNER,
            V042_CREDENTIAL_CUSTODIAN, "PROTECTED_TTY_ONE_TIME", V042_ROTATION_OWNER,
            "SEPARATE_APPROVAL_REQUIRED", "S2A field proof approval", "revision-6-golden-vector",
            V042_CORRELATION, evidenceBindingFingerprint,
            snapshot.artifactVersion, snapshot.canonicalizationVersion, snapshot.canonicalManifestBytes,
            snapshot.manifestDigest, snapshot.signaturePreimageBytes, snapshot.algorithmId,
            snapshot.signerSubjectId, snapshot.signerKeyId, snapshot.signerKeyRevision,
            snapshot.signerKeyFingerprint, snapshot.signerKeyLineageFingerprint,
            snapshot.subjectPublicKeyInfoDer, snapshot.signatureBytes, snapshot.signerAuthorityId,
            snapshot.signerAuthorityRevision, snapshot.signerAuthorityFingerprint, snapshot.verifiedAt,
            snapshot.acceptedProofFingerprint, snapshot.signedEvidenceBinding
        )
        assertEquals(73, values.size, "V042 DECISION APPLY parameter count drift")
        c.prepareStatement(
            "SELECT * FROM public.s2a_v042_apply_attested_decision(${List(values.size) { "?" }.joinToString()})"
        ).use { s ->
            values.forEachIndexed { index, value -> s.setObject(index + 1, value) }
            s.executeQuery().use { r ->
                assertTrue(r.next(), "V042 DECISION APPLY returned no row")
                val value = V042DecisionApplyResult(
                    r.getString("outcome"),
                    r.getObject("result_decision_id", UUID::class.java),
                    r.getString("result_decision_semantic_fingerprint"),
                    r.getTimestamp("result_decided_at")
                )
                assertFalse(r.next(), "V042 DECISION APPLY returned more than one row")
                value
            }
        }
    }

    private fun beginV042Principal(
        operationId: UUID = V042_OPERATION,
        principalId: UUID = V042_PRINCIPAL,
        reason: String = "S2A field proof approval",
        provenance: String = "revision-7.3-synthetic-test",
        correlationId: UUID = v042SyntheticUuid(14),
        revocationOwner: UUID = v042SyntheticUuid(11),
        credentialCustodian: UUID = v042SyntheticUuid(12),
        credentialRotationOwner: UUID = v042SyntheticUuid(13),
        integrationReference: String = "INT-2026-0001",
        evidenceBindingFingerprint: String = V042_EVIDENCE_FINGERPRINT
    ): V042PrincipalBeginResult =
        connection().use { c ->
            c.createStatement().use { it.execute("SET ROLE flooow_command_issuer") }

            val placeholders = List(26) { "?" }.joinToString(",")
            c.prepareStatement(
                "SELECT * FROM public.s2a_v042_begin_attested_principal_verification($placeholders)"
            ).use { s ->
                var i = 1

                s.setObject(i++, V042_ORGANIZATION)
                s.setObject(i++, V042_MANIFEST)
                s.setObject(i++, operationId)
                s.setObject(i++, principalId)

                s.setInt(i++, 1)
                s.setObject(i++, V042_MANIFEST)
                s.setObject(i++, V042_ORGANIZATION)
                s.setObject(i++, V042_ML_CONNECTION)
                s.setObject(i++, V042_OMIE_CONNECTION)
                s.setString(i++, "SO-2026-0001")
                s.setString(i++, integrationReference)
                s.setObject(i++, V042_MARKETPLACE_ORDER)
                s.setString(i++, "TRANSACTION_IDENTITY_DECISION_WRITE")
                s.setObject(i++, V042_SUBJECT)
                s.setObject(i++, V042_APPROVAL_SOURCE)
                s.setTimestamp(i++, Timestamp.from(V042_VALID_FROM))
                s.setTimestamp(i++, Timestamp.from(V042_VALID_UNTIL))
                s.setObject(i++, revocationOwner)
                s.setObject(i++, credentialCustodian)
                s.setString(i++, "PROTECTED_TTY_ONE_TIME")
                s.setObject(i++, credentialRotationOwner)
                s.setString(i++, "SEPARATE_APPROVAL_REQUIRED")
                s.setString(i++, reason)
                s.setString(i++, provenance)
                s.setObject(i++, correlationId)
                s.setString(i++, evidenceBindingFingerprint)

                assertEquals(27, i, "V042 PRINCIPAL BEGIN parameter count drift")

                s.executeQuery().use { r ->
                    assertTrue(r.next(), "V042 PRINCIPAL BEGIN returned no row")

                    val value =
                        V042PrincipalBeginResult(
                            outcome = r.getString("outcome"),
                            operationId = r.getObject("result_operation_id", UUID::class.java),
                            intentFingerprint = r.getString("result_intent_fingerprint"),
                            receiptFingerprint = r.getString("result_receipt_fingerprint"),
                            effectTime = r.getTimestamp("result_effect_time"),
                            artifactVersion = r.getInt("result_artifact_version"),
                            schemaVersion = r.getInt("result_schema_version"),
                            canonicalizationVersion = r.getInt("result_canonicalization_version"),
                            canonicalManifestBytes = r.getBytes("result_canonical_manifest_bytes"),
                            manifestDigest = r.getString("result_manifest_digest"),
                            signaturePreimageBytes = r.getBytes("result_signature_preimage_bytes"),
                            algorithmId = r.getString("result_algorithm_id"),
                            signerSubjectId = r.getObject("result_signer_subject_id", UUID::class.java),
                            signerKeyId = r.getObject("result_signer_key_id", UUID::class.java),
                            signerKeyRevision = r.getInt("result_signer_key_revision"),
                            signerKeyFingerprint = r.getString("result_signer_key_fingerprint"),
                            signerKeyLineageFingerprint = r.getString("result_signer_key_lineage_fingerprint"),
                            subjectPublicKeyInfoDer = r.getBytes("result_subject_public_key_info_der"),
                            signatureBytes = r.getBytes("result_signature_bytes"),
                            signerAuthorityId = r.getObject("result_signer_authority_id", UUID::class.java),
                            signerAuthorityRevision = r.getInt("result_signer_authority_revision"),
                            signerAuthorityFingerprint = r.getString("result_signer_authority_fingerprint"),
                            verifiedAt = r.getTimestamp("result_verified_at"),
                            acceptedProofFingerprint = r.getString("result_accepted_proof_fingerprint"),
                            signedEvidenceBinding = r.getString("result_signed_evidence_binding_fingerprint"),
                            currentEvidenceBinding = r.getString("result_current_durable_evidence_binding"),
                            observedEffectTime = r.getTimestamp("result_observed_effect_time"),
                            observedEffectiveKeyRevision = r.getObject("result_observed_effective_signer_key_revision", Int::class.javaObjectType),
                            observedEffectiveKeyState = r.getString("result_observed_effective_signer_key_state"),
                            observedCurrentAuthorityId =
                                r.getObject("result_observed_current_signer_authority_id", UUID::class.java),
                            observedCurrentAuthorityRevision =
                                r.getObject("result_observed_current_signer_authority_revision", Int::class.javaObjectType),
                            observedCurrentAuthorityFingerprint =
                                r.getString("result_observed_current_signer_authority_fingerprint")
                        )

                    assertFalse(r.next(), "V042 PRINCIPAL BEGIN returned more than one row")
                    value
                }
            }
        }

    private fun beginAttestedGrantVerification(
        organizationId: UUID, manifestId: UUID, operationId: UUID, principalId: UUID, grantId: UUID,
        schemaVersion: Int, claimManifestId: UUID, claimOrganizationId: UUID,
        mercadoLivreConnectionId: UUID, omieConnectionId: UUID, sourceOrderReference: String,
        integrationReference: String, marketplaceOrderId: UUID, permission: String,
        accountableOperator: UUID, approvalSource: UUID, approvalWindowStart: Timestamp,
        approvalWindowEnd: Timestamp, revocationOwner: UUID, credentialCustodian: UUID,
        credentialDeliveryMethod: String, credentialRotationOwner: UUID, immediateRevocationPolicy: String,
        reason: String, provenance: String, correlationId: UUID, evidenceBindingFingerprint: String
    ): V042InitialCredentialBeginResult = connection().use { c ->
        c.createStatement().use { it.execute("SET ROLE flooow_command_issuer") }
        c.prepareStatement("SELECT * FROM public.s2a_v042_begin_attested_grant_verification(${List(27) { "?" }.joinToString()})").use { s ->
            var i = 1
            s.setObject(i++, organizationId); s.setObject(i++, manifestId); s.setObject(i++, operationId)
            s.setObject(i++, principalId); s.setObject(i++, grantId); s.setInt(i++, schemaVersion)
            s.setObject(i++, claimManifestId); s.setObject(i++, claimOrganizationId)
            s.setObject(i++, mercadoLivreConnectionId); s.setObject(i++, omieConnectionId)
            s.setString(i++, sourceOrderReference); s.setString(i++, integrationReference)
            s.setObject(i++, marketplaceOrderId); s.setString(i++, permission)
            s.setObject(i++, accountableOperator); s.setObject(i++, approvalSource)
            s.setTimestamp(i++, approvalWindowStart); s.setTimestamp(i++, approvalWindowEnd)
            s.setObject(i++, revocationOwner); s.setObject(i++, credentialCustodian)
            s.setString(i++, credentialDeliveryMethod); s.setObject(i++, credentialRotationOwner)
            s.setString(i++, immediateRevocationPolicy); s.setString(i++, reason)
            s.setString(i++, provenance); s.setObject(i++, correlationId)
            s.setString(i++, evidenceBindingFingerprint)
            assertEquals(28, i, "V042 GRANT BEGIN parameter count drift")
            s.executeQuery().use { r ->
                assertTrue(r.next(), "V042 GRANT BEGIN returned no row")
                val value = V042InitialCredentialBeginResult(
                    r.getString("outcome"), r.getObject("result_operation_id", UUID::class.java),
                    r.getString("result_intent_fingerprint"), r.getString("result_receipt_fingerprint"),
                    r.getTimestamp("result_effect_time"), r.getInt("result_artifact_version"),
                    r.getInt("result_schema_version"), r.getInt("result_canonicalization_version"),
                    r.getBytes("result_canonical_manifest_bytes"), r.getString("result_manifest_digest"),
                    r.getBytes("result_signature_preimage_bytes"), r.getString("result_algorithm_id"),
                    r.getObject("result_signer_subject_id", UUID::class.java),
                    r.getObject("result_signer_key_id", UUID::class.java), r.getInt("result_signer_key_revision"),
                    r.getString("result_signer_key_fingerprint"), r.getString("result_signer_key_lineage_fingerprint"),
                    r.getBytes("result_subject_public_key_info_der"), r.getBytes("result_signature_bytes"),
                    r.getObject("result_signer_authority_id", UUID::class.java), r.getInt("result_signer_authority_revision"),
                    r.getString("result_signer_authority_fingerprint"), r.getTimestamp("result_verified_at"),
                    r.getString("result_accepted_proof_fingerprint"), r.getString("result_signed_evidence_binding_fingerprint"),
                    r.getString("result_current_durable_evidence_binding"), r.getTimestamp("result_observed_effect_time"),
                    r.getObject("result_observed_effective_signer_key_revision", Int::class.javaObjectType),
                    r.getString("result_observed_effective_signer_key_state"),
                    r.getObject("result_observed_current_signer_authority_id", UUID::class.java),
                    r.getObject("result_observed_current_signer_authority_revision", Int::class.javaObjectType),
                    r.getString("result_observed_current_signer_authority_fingerprint")
                )
                assertFalse(r.next(), "V042 GRANT BEGIN returned more than one row")
                value
            }
        }
    }

    private fun applyAttestedGrantVerification(
        organizationId: UUID, manifestId: UUID, operationId: UUID, principalId: UUID, grantId: UUID,
        schemaVersion: Int, claimManifestId: UUID, claimOrganizationId: UUID,
        mercadoLivreConnectionId: UUID, omieConnectionId: UUID, sourceOrderReference: String,
        integrationReference: String, marketplaceOrderId: UUID, permission: String,
        accountableOperator: UUID, approvalSource: UUID, approvalWindowStart: Timestamp,
        approvalWindowEnd: Timestamp, revocationOwner: UUID, credentialCustodian: UUID,
        credentialDeliveryMethod: String, credentialRotationOwner: UUID, immediateRevocationPolicy: String,
        reason: String, provenance: String, correlationId: UUID, evidenceBindingFingerprint: String,
        expectedArtifactVersion: Int, expectedCanonicalizationVersion: Int,
        expectedCanonicalManifestBytes: ByteArray, expectedManifestDigest: String,
        expectedSignaturePreimageBytes: ByteArray, expectedAlgorithmId: String,
        expectedSignerSubjectId: UUID, expectedSignerKeyId: UUID, expectedSignerKeyRevision: Int,
        expectedSignerKeyFingerprint: String, expectedSignerKeyLineageFingerprint: String,
        expectedSubjectPublicKeyInfoDer: ByteArray, expectedSignatureBytes: ByteArray,
        expectedSignerAuthorityId: UUID, expectedSignerAuthorityRevision: Int,
        expectedSignerAuthorityFingerprint: String, expectedVerifiedAt: Timestamp,
        expectedAcceptedProofFingerprint: String, expectedEvidenceBindingFingerprint: String
    ): V042InitialCredentialApplyResult = connection().use { c ->
        c.createStatement().use { it.execute("SET ROLE flooow_command_issuer") }
        c.prepareStatement("SELECT * FROM public.s2a_v042_apply_attested_grant(${List(46) { "?" }.joinToString()})").use { s ->
            var i = 1
            s.setObject(i++, organizationId); s.setObject(i++, manifestId); s.setObject(i++, operationId)
            s.setObject(i++, principalId); s.setObject(i++, grantId); s.setInt(i++, schemaVersion)
            s.setObject(i++, claimManifestId); s.setObject(i++, claimOrganizationId)
            s.setObject(i++, mercadoLivreConnectionId); s.setObject(i++, omieConnectionId)
            s.setString(i++, sourceOrderReference); s.setString(i++, integrationReference)
            s.setObject(i++, marketplaceOrderId); s.setString(i++, permission)
            s.setObject(i++, accountableOperator); s.setObject(i++, approvalSource)
            s.setTimestamp(i++, approvalWindowStart); s.setTimestamp(i++, approvalWindowEnd)
            s.setObject(i++, revocationOwner); s.setObject(i++, credentialCustodian)
            s.setString(i++, credentialDeliveryMethod); s.setObject(i++, credentialRotationOwner)
            s.setString(i++, immediateRevocationPolicy); s.setString(i++, reason)
            s.setString(i++, provenance); s.setObject(i++, correlationId); s.setString(i++, evidenceBindingFingerprint)
            s.setInt(i++, expectedArtifactVersion); s.setInt(i++, expectedCanonicalizationVersion)
            s.setBytes(i++, expectedCanonicalManifestBytes); s.setString(i++, expectedManifestDigest)
            s.setBytes(i++, expectedSignaturePreimageBytes); s.setString(i++, expectedAlgorithmId)
            s.setObject(i++, expectedSignerSubjectId); s.setObject(i++, expectedSignerKeyId)
            s.setInt(i++, expectedSignerKeyRevision); s.setString(i++, expectedSignerKeyFingerprint)
            s.setString(i++, expectedSignerKeyLineageFingerprint); s.setBytes(i++, expectedSubjectPublicKeyInfoDer)
            s.setBytes(i++, expectedSignatureBytes); s.setObject(i++, expectedSignerAuthorityId)
            s.setInt(i++, expectedSignerAuthorityRevision); s.setString(i++, expectedSignerAuthorityFingerprint)
            s.setTimestamp(i++, expectedVerifiedAt); s.setString(i++, expectedAcceptedProofFingerprint)
            s.setString(i++, expectedEvidenceBindingFingerprint)
            assertEquals(47, i, "V042 GRANT APPLY parameter count drift")
            s.executeQuery().use { r ->
                assertTrue(r.next(), "V042 GRANT APPLY returned no row")
                val value = V042InitialCredentialApplyResult(
                    r.getString("outcome"), r.getObject("result_operation_id", UUID::class.java),
                    r.getString("result_intent_fingerprint"), r.getString("result_receipt_fingerprint"),
                    r.getTimestamp("result_effect_time")
                )
                assertFalse(r.next(), "V042 GRANT APPLY returned more than one row")
                value
            }
        }
    }

    private fun beginAttestedInitialCredentialVerification(
        organizationId: UUID,
        manifestId: UUID,
        operationId: UUID,
        principalId: UUID,
        credentialId: UUID,
        secretVerifier: ByteArray,
        schemaVersion: Int,
        claimManifestId: UUID,
        claimOrganizationId: UUID,
        mercadoLivreConnectionId: UUID,
        omieConnectionId: UUID,
        sourceOrderReference: String,
        integrationReference: String,
        marketplaceOrderId: UUID,
        permission: String,
        accountableOperator: UUID,
        approvalSource: UUID,
        approvalWindowStart: Timestamp,
        approvalWindowEnd: Timestamp,
        revocationOwner: UUID,
        credentialCustodian: UUID,
        credentialDeliveryMethod: String,
        credentialRotationOwner: UUID,
        immediateRevocationPolicy: String,
        reason: String,
        provenance: String,
        correlationId: UUID,
        evidenceBindingFingerprint: String
    ): V042InitialCredentialBeginResult =
        connection().use { c ->
            c.createStatement().use { it.execute("SET ROLE flooow_command_issuer") }
            c.prepareStatement(
                """
                SELECT * FROM public.s2a_v042_begin_attested_initial_credential_verification(
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?
                )
                """.trimIndent()
            ).use { s ->
                var i = 1
                s.setObject(i++, organizationId)
                s.setObject(i++, manifestId)
                s.setObject(i++, operationId)
                s.setObject(i++, principalId)
                s.setObject(i++, credentialId)
                s.setBytes(i++, secretVerifier)
                s.setInt(i++, schemaVersion)
                s.setObject(i++, claimManifestId)
                s.setObject(i++, claimOrganizationId)
                s.setObject(i++, mercadoLivreConnectionId)
                s.setObject(i++, omieConnectionId)
                s.setString(i++, sourceOrderReference)
                s.setString(i++, integrationReference)
                s.setObject(i++, marketplaceOrderId)
                s.setString(i++, permission)
                s.setObject(i++, accountableOperator)
                s.setObject(i++, approvalSource)
                s.setTimestamp(i++, approvalWindowStart)
                s.setTimestamp(i++, approvalWindowEnd)
                s.setObject(i++, revocationOwner)
                s.setObject(i++, credentialCustodian)
                s.setString(i++, credentialDeliveryMethod)
                s.setObject(i++, credentialRotationOwner)
                s.setString(i++, immediateRevocationPolicy)
                s.setString(i++, reason)
                s.setString(i++, provenance)
                s.setObject(i++, correlationId)
                s.setString(i++, evidenceBindingFingerprint)
                assertEquals(29, i, "V042 INITIAL_CREDENTIAL BEGIN parameter count drift")

                s.executeQuery().use { r ->
                    assertTrue(r.next(), "V042 INITIAL_CREDENTIAL BEGIN returned no row")
                    val value = V042InitialCredentialBeginResult(
                        outcome = r.getString("outcome"),
                        operationId = r.getObject("result_operation_id", UUID::class.java),
                        intentFingerprint = r.getString("result_intent_fingerprint"),
                        receiptFingerprint = r.getString("result_receipt_fingerprint"),
                        effectTime = r.getTimestamp("result_effect_time"),
                        artifactVersion = r.getInt("result_artifact_version"),
                        schemaVersion = r.getInt("result_schema_version"),
                        canonicalizationVersion = r.getInt("result_canonicalization_version"),
                        canonicalManifestBytes = r.getBytes("result_canonical_manifest_bytes"),
                        manifestDigest = r.getString("result_manifest_digest"),
                        signaturePreimageBytes = r.getBytes("result_signature_preimage_bytes"),
                        algorithmId = r.getString("result_algorithm_id"),
                        signerSubjectId = r.getObject("result_signer_subject_id", UUID::class.java),
                        signerKeyId = r.getObject("result_signer_key_id", UUID::class.java),
                        signerKeyRevision = r.getInt("result_signer_key_revision"),
                        signerKeyFingerprint = r.getString("result_signer_key_fingerprint"),
                        signerKeyLineageFingerprint = r.getString("result_signer_key_lineage_fingerprint"),
                        subjectPublicKeyInfoDer = r.getBytes("result_subject_public_key_info_der"),
                        signatureBytes = r.getBytes("result_signature_bytes"),
                        signerAuthorityId = r.getObject("result_signer_authority_id", UUID::class.java),
                        signerAuthorityRevision = r.getInt("result_signer_authority_revision"),
                        signerAuthorityFingerprint = r.getString("result_signer_authority_fingerprint"),
                        verifiedAt = r.getTimestamp("result_verified_at"),
                        acceptedProofFingerprint = r.getString("result_accepted_proof_fingerprint"),
                        signedEvidenceBinding = r.getString("result_signed_evidence_binding_fingerprint"),
                        currentEvidenceBinding = r.getString("result_current_durable_evidence_binding"),
                        observedEffectTime = r.getTimestamp("result_observed_effect_time"),
                        observedEffectiveKeyRevision =
                            r.getObject("result_observed_effective_signer_key_revision", Int::class.javaObjectType),
                        observedEffectiveKeyState = r.getString("result_observed_effective_signer_key_state"),
                        observedCurrentAuthorityId =
                            r.getObject("result_observed_current_signer_authority_id", UUID::class.java),
                        observedCurrentAuthorityRevision =
                            r.getObject("result_observed_current_signer_authority_revision", Int::class.javaObjectType),
                        observedCurrentAuthorityFingerprint =
                            r.getString("result_observed_current_signer_authority_fingerprint")
                    )
                    assertFalse(r.next(), "V042 INITIAL_CREDENTIAL BEGIN returned more than one row")
                    value
                }
            }
        }

    private fun applyAttestedInitialCredentialVerification(
        organizationId: UUID,
        manifestId: UUID,
        operationId: UUID,
        principalId: UUID,
        credentialId: UUID,
        secretVerifier: ByteArray,
        schemaVersion: Int,
        claimManifestId: UUID,
        claimOrganizationId: UUID,
        mercadoLivreConnectionId: UUID,
        omieConnectionId: UUID,
        sourceOrderReference: String,
        integrationReference: String,
        marketplaceOrderId: UUID,
        permission: String,
        accountableOperator: UUID,
        approvalSource: UUID,
        approvalWindowStart: Timestamp,
        approvalWindowEnd: Timestamp,
        revocationOwner: UUID,
        credentialCustodian: UUID,
        credentialDeliveryMethod: String,
        credentialRotationOwner: UUID,
        immediateRevocationPolicy: String,
        reason: String,
        provenance: String,
        correlationId: UUID,
        evidenceBindingFingerprint: String,
        expectedArtifactVersion: Int,
        expectedCanonicalizationVersion: Int,
        expectedCanonicalManifestBytes: ByteArray,
        expectedManifestDigest: String,
        expectedSignaturePreimageBytes: ByteArray,
        expectedAlgorithmId: String,
        expectedSignerSubjectId: UUID,
        expectedSignerKeyId: UUID,
        expectedSignerKeyRevision: Int,
        expectedSignerKeyFingerprint: String,
        expectedSignerKeyLineageFingerprint: String,
        expectedSubjectPublicKeyInfoDer: ByteArray,
        expectedSignatureBytes: ByteArray,
        expectedSignerAuthorityId: UUID,
        expectedSignerAuthorityRevision: Int,
        expectedSignerAuthorityFingerprint: String,
        expectedVerifiedAt: Timestamp,
        expectedAcceptedProofFingerprint: String,
        expectedEvidenceBindingFingerprint: String
    ): V042InitialCredentialApplyResult =
        connection().use { c ->
            c.createStatement().use { it.execute("SET ROLE flooow_command_issuer") }
            c.prepareStatement(
                """
                SELECT * FROM public.s2a_v042_apply_attested_initial_credential(
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,?,?,?
                )
                """.trimIndent()
            ).use { s ->
                var i = 1
                s.setObject(i++, organizationId)
                s.setObject(i++, manifestId)
                s.setObject(i++, operationId)
                s.setObject(i++, principalId)
                s.setObject(i++, credentialId)
                s.setBytes(i++, secretVerifier)
                s.setInt(i++, schemaVersion)
                s.setObject(i++, claimManifestId)
                s.setObject(i++, claimOrganizationId)
                s.setObject(i++, mercadoLivreConnectionId)
                s.setObject(i++, omieConnectionId)
                s.setString(i++, sourceOrderReference)
                s.setString(i++, integrationReference)
                s.setObject(i++, marketplaceOrderId)
                s.setString(i++, permission)
                s.setObject(i++, accountableOperator)
                s.setObject(i++, approvalSource)
                s.setTimestamp(i++, approvalWindowStart)
                s.setTimestamp(i++, approvalWindowEnd)
                s.setObject(i++, revocationOwner)
                s.setObject(i++, credentialCustodian)
                s.setString(i++, credentialDeliveryMethod)
                s.setObject(i++, credentialRotationOwner)
                s.setString(i++, immediateRevocationPolicy)
                s.setString(i++, reason)
                s.setString(i++, provenance)
                s.setObject(i++, correlationId)
                s.setString(i++, evidenceBindingFingerprint)
                s.setInt(i++, expectedArtifactVersion)
                s.setInt(i++, expectedCanonicalizationVersion)
                s.setBytes(i++, expectedCanonicalManifestBytes)
                s.setString(i++, expectedManifestDigest)
                s.setBytes(i++, expectedSignaturePreimageBytes)
                s.setString(i++, expectedAlgorithmId)
                s.setObject(i++, expectedSignerSubjectId)
                s.setObject(i++, expectedSignerKeyId)
                s.setInt(i++, expectedSignerKeyRevision)
                s.setString(i++, expectedSignerKeyFingerprint)
                s.setString(i++, expectedSignerKeyLineageFingerprint)
                s.setBytes(i++, expectedSubjectPublicKeyInfoDer)
                s.setBytes(i++, expectedSignatureBytes)
                s.setObject(i++, expectedSignerAuthorityId)
                s.setInt(i++, expectedSignerAuthorityRevision)
                s.setString(i++, expectedSignerAuthorityFingerprint)
                s.setTimestamp(i++, expectedVerifiedAt)
                s.setString(i++, expectedAcceptedProofFingerprint)
                s.setString(i++, expectedEvidenceBindingFingerprint)
                assertEquals(48, i, "V042 INITIAL_CREDENTIAL APPLY parameter count drift")

                s.executeQuery().use { r ->
                    assertTrue(r.next(), "V042 INITIAL_CREDENTIAL APPLY returned no row")
                    val value = V042InitialCredentialApplyResult(
                        outcome = r.getString("outcome"),
                        operationId = r.getObject("result_operation_id", UUID::class.java),
                        intentFingerprint = r.getString("result_intent_fingerprint"),
                        receiptFingerprint = r.getString("result_receipt_fingerprint"),
                        effectTime = r.getTimestamp("result_effect_time")
                    )
                    assertFalse(r.next(), "V042 INITIAL_CREDENTIAL APPLY returned more than one row")
                    value
                }
            }
        }

    private fun applyV042Principal(
        begin: V042PrincipalBeginResult,
        operationId: UUID = V042_OPERATION,
        principalId: UUID = V042_PRINCIPAL,
        provenance: String = "revision-7.3-synthetic-test",
        correlationId: UUID = v042SyntheticUuid(14),
        revocationOwner: UUID = v042SyntheticUuid(11),
        credentialCustodian: UUID = v042SyntheticUuid(12),
        credentialRotationOwner: UUID = v042SyntheticUuid(13),
        integrationReference: String = "INT-2026-0001",
        evidenceBindingFingerprint: String = V042_EVIDENCE_FINGERPRINT
    ): V042PrincipalApplyResult =
        connection().use { c ->
            c.createStatement().use { it.execute("SET ROLE flooow_command_issuer") }
            val placeholders = List(45) { "?" }.joinToString(",")
            c.prepareStatement("SELECT * FROM public.s2a_v042_apply_attested_principal($placeholders)").use { s ->
                var i = 1
                s.setObject(i++, V042_ORGANIZATION)
                s.setObject(i++, V042_MANIFEST)
                s.setObject(i++, operationId)
                s.setObject(i++, principalId)
                s.setInt(i++, 1)
                s.setObject(i++, V042_MANIFEST)
                s.setObject(i++, V042_ORGANIZATION)
                s.setObject(i++, V042_ML_CONNECTION)
                s.setObject(i++, V042_OMIE_CONNECTION)
                s.setString(i++, "SO-2026-0001")
                s.setString(i++, integrationReference)
                s.setObject(i++, V042_MARKETPLACE_ORDER)
                s.setString(i++, "TRANSACTION_IDENTITY_DECISION_WRITE")
                s.setObject(i++, V042_SUBJECT)
                s.setObject(i++, V042_APPROVAL_SOURCE)
                s.setTimestamp(i++, Timestamp.from(V042_VALID_FROM))
                s.setTimestamp(i++, Timestamp.from(V042_VALID_UNTIL))
                s.setObject(i++, revocationOwner)
                s.setObject(i++, credentialCustodian)
                s.setString(i++, "PROTECTED_TTY_ONE_TIME")
                s.setObject(i++, credentialRotationOwner)
                s.setString(i++, "SEPARATE_APPROVAL_REQUIRED")
                s.setString(i++, "S2A field proof approval")
                s.setString(i++, provenance)
                s.setObject(i++, correlationId)
                s.setString(i++, evidenceBindingFingerprint)
                s.setInt(i++, begin.artifactVersion)
                s.setInt(i++, begin.canonicalizationVersion)
                s.setBytes(i++, begin.canonicalManifestBytes)
                s.setString(i++, begin.manifestDigest)
                s.setBytes(i++, begin.signaturePreimageBytes)
                s.setString(i++, begin.algorithmId)
                s.setObject(i++, begin.signerSubjectId)
                s.setObject(i++, begin.signerKeyId)
                s.setInt(i++, begin.signerKeyRevision)
                s.setString(i++, begin.signerKeyFingerprint)
                s.setString(i++, begin.signerKeyLineageFingerprint)
                s.setBytes(i++, begin.subjectPublicKeyInfoDer)
                s.setBytes(i++, begin.signatureBytes)
                s.setObject(i++, begin.signerAuthorityId)
                s.setInt(i++, begin.signerAuthorityRevision)
                s.setString(i++, begin.signerAuthorityFingerprint)
                s.setTimestamp(i++, begin.verifiedAt)
                s.setString(i++, begin.acceptedProofFingerprint)
                s.setString(i++, begin.signedEvidenceBinding)
                assertEquals(46, i, "V042 PRINCIPAL APPLY parameter count drift")

                s.executeQuery().use { r ->
                    assertTrue(r.next(), "V042 PRINCIPAL APPLY returned no row")
                    val value = V042PrincipalApplyResult(
                        outcome = r.getString("outcome"),
                        operationId = r.getObject("result_operation_id", UUID::class.java),
                        intentFingerprint = r.getString("result_intent_fingerprint"),
                        receiptFingerprint = r.getString("result_receipt_fingerprint"),
                        effectTime = r.getTimestamp("result_effect_time")
                    )
                    assertFalse(r.next(), "V042 PRINCIPAL APPLY returned more than one row")
                    value
                }
            }
        }

    private fun installV042PrincipalFixture(decisionCompatible: Boolean = false) {
        val now = Timestamp.from(Instant.parse("2026-09-25T12:00:00Z"))

        v042Update(
            "INSERT INTO integration_organization VALUES (?,'ACTIVE',?,?)",
            V042_ORGANIZATION, now, now
        )
        v042Update(
            "INSERT INTO integration_connection VALUES (?,?,?,'OAUTH2_AUTHORIZATION_CODE','REVOKED',1,?,?)",
            V042_ORGANIZATION, V042_ML_CONNECTION, "br.com.mercadolivre", now, now
        )
        v042Update(
            "INSERT INTO integration_connection VALUES (?,?,?,'STATIC_API_CREDENTIAL','SUSPENDED',1,?,?)",
            V042_ORGANIZATION, V042_OMIE_CONNECTION, "omie", now, now
        )

        connection().use { c ->
            c.autoCommit = false

            v042Page(c, V042_ML_CONNECTION, V042_ML_CAPABILITY, 1, 2, 1)

            v042Execute(
                c,
                """
                INSERT INTO integration_mercado_livre_order_source_observation
                (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,
                 provider_status,date_created,date_last_updated,currency,total_amount,observed_at)
                VALUES (?,?,?,1,1,'MLB-123456789','paid',?,?,'BRL',58.28,?)
                """.trimIndent(),
                V042_ORGANIZATION, V042_ML_CONNECTION, V042_ML_CAPABILITY, now, now, now
            )

            v042Execute(
                c,
                "INSERT INTO marketplace_order_identity_registry VALUES (?,'mercado-livre','MLB-123456789',?,'BRL',?,?,?,?,1)",
                V042_ORGANIZATION, V042_MARKETPLACE_ORDER, now, V042_ML_CONNECTION, V042_ML_CAPABILITY, 1L
            )

            v042Execute(
                c,
                "INSERT INTO marketplace_order_occurrence_source_promotion VALUES (?,?,?,1,1,?,'PROMOTED',?)",
                V042_ORGANIZATION, V042_ML_CONNECTION, V042_ML_CAPABILITY, V042_MARKETPLACE_ORDER, now
            )

            v042Page(c, V042_OMIE_CONNECTION, V042_OMIE_CAPABILITY, 1, 2, 2)
            v042Omie(
                c, 0, "OTHER-SYNTHETIC", null, "BRL",
                LocalDateTime.parse("2026-09-24T10:00:00.000000"),
                "cd".repeat(32), now
            )
            v042Omie(
                c, 1, "SO-2026-0001",
                if (decisionCompatible) "MLB-123456789" else "INT-2026-0001", null,
                LocalDateTime.parse("2026-09-25T11:59:59.123456"),
                "ab".repeat(32), now
            )

            c.commit()
        }

        val keyDraft =
            SignerKeyRevision(
                OrganizationId.parse(V042_ORGANIZATION.toString()),
                SignerKeyId(V042_KEY_ID),
                1,
                GovernanceSubjectId(V042_SUBJECT),
                SignerPublicKeyInfo.parse(V042_SPKI_HEX.hex()),
                V042_KEY_FINGERPRINT,
                SignerKeyState.ACTIVE,
                V042_VALID_FROM,
                V042_VALID_FROM,
                null,
                null,
                SignerKeyLineageFingerprint("0".repeat(64)),
                "Synthetic V041 key",
                "v041-test",
                v042SyntheticUuid(801)
            )

        val key =
            keyDraft.copy(
                lineageFingerprint =
                    ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(keyDraft)
            )

        assertIs<GovernanceAppendResult.Applied>(
            v042Governance().appendSignerKeyRevision(key)
        )

        val authorityDraft =
            SignerAuthorityRevision(
                key.organizationId,
                SignerAuthorityId(V042_AUTHORITY),
                1,
                key.signerSubjectId,
                GovernanceInstitutionId(V042_INSTITUTION),
                SignerRole.S2A_FIELD_PROOF_APPROVER,
                key.signerKeyId,
                1,
                key.signerKeyFingerprint,
                ApprovalAction.S2A_FIELD_PROOF_APPROVAL,
                SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,
                V042_VALID_FROM,
                V042_VALID_UNTIL,
                SignerAuthorityState.ENABLED,
                null,
                null,
                SignerAuthorityFingerprint("0".repeat(64)),
                "Synthetic V041 authority",
                "v041-test",
                GovernanceSourceId(V042_APPROVAL_SOURCE),
                v042SyntheticUuid(802)
            )

        val authority =
            authorityDraft.copy(
                signerAuthorityFingerprint =
                    ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(authorityDraft)
            )

        assertIs<GovernanceAppendResult.Applied>(
            v042Governance().appendSignerAuthorityRevision(authority)
        )
    }

    private fun v042Manifest(
        provenance: String = "revision-7.3-synthetic-test",
        correlationId: UUID = v042SyntheticUuid(14),
        revocationOwner: UUID = v042SyntheticUuid(11),
        credentialCustodian: UUID = v042SyntheticUuid(12),
        credentialRotationOwner: UUID = v042SyntheticUuid(13)
    ) =
        ApprovalManifest(
            1,
            V042_MANIFEST,
            OrganizationId.parse(V042_ORGANIZATION.toString()),
            V042_ML_CONNECTION,
            V042_OMIE_CONNECTION,
            "SO-2026-0001",
            "INT-2026-0001",
            MarketplaceOrderId.parse(V042_MARKETPLACE_ORDER.toString()),
            SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,
            GovernanceSubjectId(V042_SUBJECT),
            GovernanceSourceId(V042_APPROVAL_SOURCE),
            V042_VALID_FROM,
            V042_VALID_UNTIL,
            GovernanceSubjectId(revocationOwner),
            GovernanceSubjectId(credentialCustodian),
            CredentialDeliveryMethod.PROTECTED_TTY_ONE_TIME,
            GovernanceSubjectId(credentialRotationOwner),
            ImmediateRevocationPolicy.SEPARATE_APPROVAL_REQUIRED,
            "S2A field proof approval",
            provenance,
            correlationId,
            V042_EVIDENCE_FINGERPRINT
        )

    private fun v042FrozenAuthorityManifest() =
        v042Manifest(
            provenance = "revision-6-golden-vector",
            correlationId = UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"),
            revocationOwner = UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            credentialCustodian = UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            credentialRotationOwner = UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        )

    private fun signedV042(manifest: ApprovalManifest): SignedApprovalAttestation {
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest)
        val preimage =
            ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes(
                "Ed25519",
                SignerKeyId(V042_KEY_ID),
                V042_KEY_FINGERPRINT,
                ApprovalManifestCanonicalCodec.manifestDigest(canonical)
            )

        val privateKey =
            KeyFactory
                .getInstance("Ed25519")
                .generatePrivate(
                    PKCS8EncodedKeySpec((V042_PKCS8_PREFIX + V042_SEED_HEX).hex())
                )

        val signature =
            Signature
                .getInstance("Ed25519")
                .run {
                    initSign(privateKey)
                    update(preimage)
                    sign()
                }

        return SignedApprovalAttestation.parse(
            manifest,
            "Ed25519",
            SignerKeyId(V042_KEY_ID),
            V042_KEY_FINGERPRINT,
            Base64.getUrlEncoder().withoutPadding().encodeToString(signature)
        )
    }

    private fun v042Page(
        c: Connection,
        id: UUID,
        capability: String,
        input: Long,
        count: Int,
        marker: Int
    ) {
        v042Execute(
            c,
            "INSERT INTO integration_connector_progress VALUES (?,?,?,?,?,false,?,?)",
            V042_ORGANIZATION,
            id,
            capability,
            input + 1,
            byteArrayOf(marker.toByte()),
            Timestamp.from(V042_VALID_FROM),
            Timestamp.from(V042_VALID_FROM)
        )

        v042Execute(
            c,
            "INSERT INTO integration_connector_page_commit VALUES (?,?,?,?,?,?,false,?,?)",
            V042_ORGANIZATION,
            id,
            capability,
            input,
            ByteArray(32) { marker.toByte() },
            count,
            Timestamp.from(V042_VALID_FROM),
            Timestamp.from(V042_VALID_FROM)
        )
    }

    private fun v042Omie(
        c: Connection,
        ordinal: Int,
        order: String,
        integration: String?,
        currency: String?,
        revision: LocalDateTime,
        fingerprint: String,
        observed: Timestamp
    ) {
        v042Execute(
            c,
            """
            INSERT INTO integration_omie_transaction_evidence
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,source_order_ref,
             source_integration_ref,currency,total_amount,product_refs,observed_at,source_fingerprint)
            VALUES (?,?,?,1,?,?,?,?,58.28,'[]',?,?)
            """.trimIndent(),
            V042_ORGANIZATION,
            V042_OMIE_CONNECTION,
            V042_OMIE_CAPABILITY,
            ordinal,
            order,
            integration,
            currency,
            observed,
            "ef".repeat(32)
        )

        v042Execute(
            c,
            """
            INSERT INTO integration_omie_transaction_evidence_v3
            (organization_id,connection_id,capability,input_progress_version,record_ordinal,provider_created_local,
             additional_order_totals,semantic_fingerprint_version,source_evidence_semantic_fingerprint)
            VALUES (?,?,?,1,?,?,'{}',1,?)
            """.trimIndent(),
            V042_ORGANIZATION,
            V042_OMIE_CONNECTION,
            V042_OMIE_CAPABILITY,
            ordinal,
            revision,
            fingerprint
        )
    }

    private fun v042Governance() =
        PostgresApprovalGovernance(
            v042RoleDataSource("flooow_approval_governance")
        )

    private fun v042Verifier() =
        PostgresAcceptedAttestationVerifier(
            v042RoleDataSource("flooow_attestation_verifier")
        )

    private fun v042RoleDataSource(role: String): DataSource {
        val base =
            PGSimpleDataSource().also {
                it.setURL(db.jdbcUrl)
                it.user = db.username
                it.password = db.password
            }

        return object : DataSource {
            override fun getConnection(): Connection =
                base.connection.also { c ->
                    c.createStatement().use { it.execute("SET ROLE $role") }
                }

            override fun getConnection(username: String?, password: String?): Connection =
                getConnection()

            override fun getLogWriter(): PrintWriter? = base.logWriter
            override fun setLogWriter(out: PrintWriter?) { base.logWriter = out }
            override fun setLoginTimeout(seconds: Int) { base.loginTimeout = seconds }
            override fun getLoginTimeout(): Int = base.loginTimeout
            override fun getParentLogger() = base.parentLogger
            override fun <T : Any?> unwrap(iface: Class<T>): T = base.unwrap(iface)
            override fun isWrapperFor(iface: Class<*>): Boolean = base.isWrapperFor(iface)
        }
    }

    private fun v042Execute(c: Connection, sql: String, vararg values: Any?) {
        c.prepareStatement(sql).use { s ->
            values.forEachIndexed { index, value ->
                s.setObject(index + 1, value)
            }
            s.executeUpdate()
        }
    }

    private fun v042Update(sql: String, vararg values: Any?) =
        connection().use { c ->
            v042Execute(c, sql, *values)
        }

    private fun v042SyntheticUuid(slot: Int): UUID =
        UUID.fromString(
            "71000000-0000-4000-8000-${slot.toString().padStart(12, '0')}"
        )

    private fun String.hex(): ByteArray =
        chunked(2).map { it.toInt(16).toByte() }.toByteArray()

    private data class V042PrincipalBeginResult(
        val outcome: String,
        val operationId: UUID,
        val intentFingerprint: String,
        val receiptFingerprint: String?,
        val effectTime: Timestamp?,
        val artifactVersion: Int,
        val schemaVersion: Int,
        val canonicalizationVersion: Int,
        val canonicalManifestBytes: ByteArray,
        val manifestDigest: String,
        val signaturePreimageBytes: ByteArray,
        val algorithmId: String,
        val signerSubjectId: UUID,
        val signerKeyId: UUID,
        val signerKeyRevision: Int,
        val signerKeyFingerprint: String,
        val signerKeyLineageFingerprint: String,
        val subjectPublicKeyInfoDer: ByteArray,
        val signatureBytes: ByteArray,
        val signerAuthorityId: UUID,
        val signerAuthorityRevision: Int,
        val signerAuthorityFingerprint: String,
        val verifiedAt: Timestamp,
        val acceptedProofFingerprint: String,
        val signedEvidenceBinding: String,
        val currentEvidenceBinding: String?,
        val observedEffectTime: Timestamp?,
        val observedEffectiveKeyRevision: Int?,
        val observedEffectiveKeyState: String?,
        val observedCurrentAuthorityId: UUID?,
        val observedCurrentAuthorityRevision: Int?,
        val observedCurrentAuthorityFingerprint: String?
    )

    private data class V042PrincipalApplyResult(
        val outcome: String,
        val operationId: UUID,
        val intentFingerprint: String,
        val receiptFingerprint: String,
        val effectTime: Timestamp
    )

    private data class V042InitialCredentialBeginResult(
        val outcome: String,
        val operationId: UUID,
        val intentFingerprint: String,
        val receiptFingerprint: String?,
        val effectTime: Timestamp?,
        val artifactVersion: Int,
        val schemaVersion: Int,
        val canonicalizationVersion: Int,
        val canonicalManifestBytes: ByteArray,
        val manifestDigest: String,
        val signaturePreimageBytes: ByteArray,
        val algorithmId: String,
        val signerSubjectId: UUID,
        val signerKeyId: UUID,
        val signerKeyRevision: Int,
        val signerKeyFingerprint: String,
        val signerKeyLineageFingerprint: String,
        val subjectPublicKeyInfoDer: ByteArray,
        val signatureBytes: ByteArray,
        val signerAuthorityId: UUID,
        val signerAuthorityRevision: Int,
        val signerAuthorityFingerprint: String,
        val verifiedAt: Timestamp,
        val acceptedProofFingerprint: String,
        val signedEvidenceBinding: String,
        val currentEvidenceBinding: String?,
        val observedEffectTime: Timestamp?,
        val observedEffectiveKeyRevision: Int?,
        val observedEffectiveKeyState: String?,
        val observedCurrentAuthorityId: UUID?,
        val observedCurrentAuthorityRevision: Int?,
        val observedCurrentAuthorityFingerprint: String?
    )

    private data class V042InitialCredentialApplyResult(
        val outcome: String,
        val operationId: UUID,
        val intentFingerprint: String,
        val receiptFingerprint: String,
        val effectTime: Timestamp
    )

    private data class V042DecisionBeginResult(
        val outcome: String,
        val decisionId: UUID,
        val semanticFingerprint: String?,
        val decidedAt: Timestamp?,
        val manifestId: UUID?,
        val artifactVersion: Int?,
        val schemaVersion: Int?,
        val canonicalizationVersion: Int?,
        val canonicalManifestBytes: ByteArray?,
        val manifestDigest: String?,
        val signaturePreimageBytes: ByteArray?,
        val algorithmId: String?,
        val signerSubjectId: UUID?,
        val signerKeyId: UUID?,
        val signerKeyRevision: Int?,
        val signerKeyFingerprint: String?,
        val signerKeyLineageFingerprint: String?,
        val subjectPublicKeyInfoDer: ByteArray?,
        val signatureBytes: ByteArray?,
        val signerAuthorityId: UUID?,
        val signerAuthorityRevision: Int?,
        val signerAuthorityFingerprint: String?,
        val verifiedAt: Timestamp?,
        val acceptedProofFingerprint: String?,
        val signedEvidenceBinding: String?
    )

    private data class V042DecisionApplyResult(
        val outcome: String,
        val decisionId: UUID,
        val semanticFingerprint: String,
        val decidedAt: Timestamp
    )

    private data class V042DbFailure(
        val sqlState: String?,
        val detail: String?,
        val primaryMessage: String?
    )

    private val V042_ORGANIZATION = UUID.fromString("11111111-1111-4111-8111-111111111111")
    private val V042_KEY_ID = UUID.fromString("22222222-2222-4222-8222-222222222222")
    private val V042_SUBJECT = UUID.fromString("33333333-3333-4333-8333-333333333333")
    private val V042_AUTHORITY = UUID.fromString("44444444-4444-4444-8444-444444444441")
    private val V042_INSTITUTION = UUID.fromString("55555555-5555-4555-8555-555555555555")
    private val V042_APPROVAL_SOURCE = UUID.fromString("66666666-6666-4666-8666-666666666666")
    private val V042_MANIFEST = UUID.fromString("77777777-7777-4777-8777-777777777777")
    private val V042_ML_CONNECTION = UUID.fromString("88888888-8888-4888-8888-888888888888")
    private val V042_OMIE_CONNECTION = UUID.fromString("99999999-9999-4999-8999-999999999999")
    private val V042_MARKETPLACE_ORDER = UUID.fromString("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    private val V042_OPERATION = UUID.fromString("12121212-1212-4121-8121-121212121212")
    private val V042_PRINCIPAL = UUID.fromString("13131313-1313-4131-8131-131313131313")
    private val V042_CREDENTIAL = UUID.fromString("14141414-1414-4141-8141-141414141414")
    private val V042_GRANT = UUID.fromString("15151515-1515-4151-8151-151515151515")
    private val V042_INITIAL_CREDENTIAL_OPERATION = UUID.fromString("16161616-1616-4161-8161-161616161616")
    private val V042_GRANT_OPERATION = UUID.fromString("17171717-1717-4171-8171-171717171717")
    private val V042_DECISION = UUID.fromString("18181818-1818-4181-8181-181818181818")
    private val V042_REVOCATION_OWNER = UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
    private val V042_CREDENTIAL_CUSTODIAN = UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
    private val V042_ROTATION_OWNER = UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
    private val V042_CORRELATION = UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")

    private val V042_KEY_FINGERPRINT =
        SignerKeyFingerprint("06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9")

    private val V042_VALID_FROM =
        Instant.parse("2026-09-25T12:00:00.000000Z")

    private val V042_VALID_UNTIL =
        Instant.parse("2026-10-25T12:00:00.000000Z")

    private val V042_EVIDENCE_FINGERPRINT =
        "9f61859daa192ae3482ad3dbb28cd7ebb5d2f143cdb6e83092054a80b512e965"

    private val V042_SPKI_HEX =
        "302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"

    private val V042_PKCS8_PREFIX =
        "302e020100300506032b657004220420"

    private val V042_SEED_HEX =
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"

    private val V042_ML_CAPABILITY =
        "marketplace-economic.order-source"

    private val V042_OMIE_CAPABILITY =
        "marketplace-economic.omie-transaction-evidence.reacquisition-v3"

    private val migrationSql: String
        get() = checkNotNull(javaClass.getResourceAsStream("/db/migration/V042__create_s2a_attestation_consumption_and_attested_command_authority.sql"))
            .bufferedReader(Charsets.UTF_8).use { it.readText() }

    private fun sourceContract(name: String): FunctionContract {
        val match = checkNotNull(
            Regex(
                "CREATE FUNCTION public\\.${Regex.escape(name)}\\((.*?)\\)\\s*RETURNS TABLE\\((.*?)\\)\\s*LANGUAGE",
                setOf(RegexOption.DOT_MATCHES_ALL)
            ).find(migrationSql)
        ) { "Missing source contract for $name" }
        val inputs = declarations(match.groupValues[1]).map { canonicalType(it.substringAfter(' ')) }
        val outputs = declarations(match.groupValues[2]).map {
            val normalized = it.replace(Regex("\\s+"), " ").trim()
            normalized.substringBefore(' ') to canonicalType(normalized.substringAfter(' '))
        }
        return FunctionContract(inputs, outputs)
    }

    private fun declarations(value: String) = value.split(',').map { it.replace(Regex("\\s+"), " ").trim() }.filter { it.isNotEmpty() }

    private fun canonicalType(value: String): String =
        value.trim()
            .replace(Regex("timestamptz(?:\\(\\d+\\))?", RegexOption.IGNORE_CASE), "timestamp with time zone")
            .replace(Regex("char\\(\\d+\\)", RegexOption.IGNORE_CASE), "character")

    private fun inputTypes(name: String): List<String> = connection().use { connection ->
        connection.prepareStatement(
            """
            SELECT format_type(type_oid,NULL)
              FROM pg_proc p
              CROSS JOIN LATERAL unnest(p.proargtypes::oid[]) WITH ORDINALITY a(type_oid,ord)
             WHERE p.pronamespace='public'::regnamespace AND p.proname=?
             ORDER BY ord
            """.trimIndent()
        ).use { statement ->
            statement.setString(1, name)
            statement.executeQuery().use { result -> buildList { while (result.next()) add(result.getString(1)) } }
        }
    }

    private fun outputContract(name: String): List<Pair<String, String>> = connection().use { connection ->
        connection.prepareStatement(
            """
            SELECT p.proargnames[s.i], format_type(p.proallargtypes[s.i],NULL)
              FROM pg_proc p
              CROSS JOIN LATERAL generate_subscripts(p.proallargtypes,1) s(i)
             WHERE p.pronamespace='public'::regnamespace AND p.proname=?
               AND p.proargmodes[s.i] IN ('o','t')
             ORDER BY s.i
            """.trimIndent()
        ).use { statement ->
            statement.setString(1, name)
            statement.executeQuery().use { result -> buildList { while (result.next()) add(result.getString(1) to result.getString(2)) } }
        }
    }

    private fun functions(names: List<String>): List<String> = functionNames(null).filter { it in names }

    private fun functionNames(like: String?): List<String> = connection().use { connection ->
        val sql = "SELECT proname FROM pg_proc WHERE pronamespace='public'::regnamespace" +
            (if (like == null) "" else " AND proname LIKE ?") + " ORDER BY proname"
        connection.prepareStatement(sql).use { statement ->
            if (like != null) statement.setString(1, like)
            statement.executeQuery().use { result -> buildList { while (result.next()) add(result.getString(1)) } }
        }
    }

    private fun functionIdentity(name: String): String = scalarString(
        "SELECT oid::regprocedure::text FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='$name'"
    )

    private fun nullInvocation(name: String): String {
        val match = checkNotNull(
            Regex("CREATE FUNCTION public\\.${Regex.escape(name)}\\((.*?)\\)\\s*RETURNS", setOf(RegexOption.DOT_MATCHES_ALL)).find(migrationSql)
        )
        val casts = declarations(match.groupValues[1]).map { it.substringAfter(' ') }
        return "SELECT * FROM public.$name(${casts.joinToString(",") { "NULL::$it" }})"
    }

    private fun role(name: String): Role = connection().use { connection ->
        connection.prepareStatement(
            "SELECT rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=?"
        ).use { statement ->
            statement.setString(1, name)
            statement.executeQuery().use { result ->
                assertTrue(result.next(), name)
                Role(
                    result.getBoolean(1),
                    result.getBoolean(2),
                    result.getBoolean(3),
                    result.getBoolean(4),
                    result.getBoolean(5),
                    result.getBoolean(6),
                    result.getBoolean(7)
                )
            }
        }
    }

    private fun columns(table: String): Map<String, Column> = connection().use { connection ->
        connection.prepareStatement(
            """
            SELECT a.attname,format_type(a.atttypid,a.atttypmod),a.attnotnull
              FROM pg_attribute a
             WHERE a.attrelid=?::regclass AND a.attnum>0 AND NOT a.attisdropped
             ORDER BY a.attnum
            """.trimIndent()
        ).use { statement ->
            statement.setString(1, "public.$table")
            statement.executeQuery().use { result -> buildMap { while (result.next()) put(result.getString(1), Column(result.getString(2), result.getBoolean(3))) } }
        }
    }

    private fun assertConstraint(name: String, expected: String) = assertEquals(expected, constraintDef(name), name)
    private fun assertConstraintContains(name: String, expected: String) = assertTrue(constraintDef(name).contains(expected), "$name: ${constraintDef(name)}")
    private fun constraintDef(name: String) = scalarString("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='$name'")
    private fun assertTableConstraintContains(table: String, expected: String) {
        val definitions = connection().use { connection ->
            connection.prepareStatement(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid=?::regclass ORDER BY oid"
            ).use { statement ->
                statement.setString(1, "public.$table")
                statement.executeQuery().use { result -> buildList { while (result.next()) add(result.getString(1)) } }
            }
        }
        assertTrue(definitions.any { it.contains(expected) }, "$table missing $expected: $definitions")
    }
    private fun assertIndexContains(name: String, expected: String) {
        val definition = scalarString("SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND indexname='$name'")
        assertTrue(definition.contains(expected), "$name: $definition")
    }

    private fun immutableTriggerCount() = scalarInt(
        """
        SELECT count(*) FROM pg_trigger
         WHERE tgrelid='public.s2a_attestation_consumption'::regclass
           AND tgname='s2a_attestation_consumption_immutable'
           AND NOT tgisinternal AND (tgtype & 2)=2 AND (tgtype & 16)=16 AND (tgtype & 8)=8
        """.trimIndent()
    )

    private fun functionPrivilege(role: String, identity: String) = connection().use { connection ->
        connection.prepareStatement("SELECT has_function_privilege(?,?,'EXECUTE')").use { statement ->
            statement.setString(1, role)
            statement.setString(2, identity)
            statement.executeQuery().use { result -> result.next(); result.getBoolean(1) }
        }
    }

    private fun publicExecute(identity: String) = connection().use { connection ->
        connection.prepareStatement(
            """
            SELECT EXISTS(
                SELECT 1 FROM pg_proc p,
                LATERAL aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) acl
                WHERE p.oid=?::regprocedure AND acl.grantee=0 AND acl.privilege_type='EXECUTE'
            )
            """.trimIndent()
        ).use { statement ->
            statement.setString(1, identity)
            statement.executeQuery().use { result -> result.next(); result.getBoolean(1) }
        }
    }

    private fun tablePrivilege(role: String, table: String, privilege: String) =
        scalarBoolean("SELECT has_table_privilege('$role','public.$table','$privilege')")

    private fun schemaPrivilege(role: String, privilege: String) =
        scalarBoolean("SELECT has_schema_privilege('$role','public','$privilege')")

    private fun publicSchemaPrivilege(privilege: String) = scalarBoolean(
        """
        SELECT EXISTS(
            SELECT 1 FROM pg_namespace n,
            LATERAL aclexplode(COALESCE(n.nspacl,acldefault('n',n.nspowner))) acl
            WHERE n.nspname='public' AND acl.grantee=0 AND acl.privilege_type='$privilege'
        )
        """.trimIndent()
    )

    private fun assertSqlState(role: String, sql: String, expected: String) {
        val failure = try {
            connection().use { connection ->
                connection.createStatement().use { statement ->
                    statement.execute("SET ROLE $role")
                    statement.execute(sql)
                }
            }
            null
        } catch (error: SQLException) {
            error
        }
        assertNotNull(failure, "$role unexpectedly executed: $sql")
        assertEquals(expected, failure.sqlState, "$role: ${failure.message}")
    }

    private fun captureDbFailure(action: () -> Unit): V042DbFailure {
        val failure = try {
            action()
            null
        } catch (error: SQLException) {
            error
        }
        assertNotNull(failure, "database action unexpectedly succeeded")
        return V042DbFailure(
            failure.sqlState,
            (failure as? PSQLException)?.serverErrorMessage?.detail,
            (failure as? PSQLException)?.serverErrorMessage?.message
        )
    }

    private fun tableCount(table: String) = scalarInt("SELECT count(*) FROM public.$table")

    private fun durableState(): DurableState = DurableState(
        STATE_TABLES.associateWith { table ->
            connection().use { connection ->
                connection.createStatement().use { statement ->
                    statement.executeQuery(
                        """
                        SELECT count(*),
                               md5(COALESCE(string_agg(row_to_json(t)::text,E'\\n' ORDER BY row_to_json(t)::text),''))
                          FROM public.$table t
                        """.trimIndent()
                    ).use { result ->
                        result.next()
                        TableState(result.getLong(1), result.getString(2))
                    }
                }
            }
        }
    )

    private fun scalarInt(sql: String) = connection().use { connection -> connection.createStatement().use { statement -> statement.executeQuery(sql).use { result -> result.next(); result.getInt(1) } } }
    private fun scalarTimestamp(sql: String) = connection().use { connection -> connection.createStatement().use { statement -> statement.executeQuery(sql).use { result -> result.next(); result.getTimestamp(1) } } }
    private fun scalarBoolean(sql: String) = connection().use { connection -> connection.createStatement().use { statement -> statement.executeQuery(sql).use { result -> result.next(); result.getBoolean(1) } } }
    private fun scalarString(sql: String) = checkNotNull(scalarNullableString(sql))
    private fun scalarNullableString(sql: String): String? = connection().use { connection -> connection.createStatement().use { statement -> statement.executeQuery(sql).use { result -> result.next(); result.getString(1) } } }
    private fun connection(): Connection = DriverManager.getConnection(db.jdbcUrl, db.username, db.password)

    private data class Column(val type: String, val notNull: Boolean)
    private data class FunctionContract(val inputTypes: List<String>, val outputs: List<Pair<String, String>>)
    private data class TableState(val count: Long, val digest: String)
    private data class DurableState(val tables: Map<String, TableState>)
    private data class Role(
        val canLogin: Boolean,
        val inherit: Boolean,
        val superuser: Boolean,
        val createDb: Boolean,
        val createRole: Boolean,
        val replication: Boolean,
        val bypassRls: Boolean
    )

    private companion object {
        val ISSUER_FUNCTIONS = listOf(
            "s2a_v042_begin_attested_principal_verification",
            "s2a_v042_begin_attested_initial_credential_verification",
            "s2a_v042_begin_attested_grant_verification",
            "s2a_v042_apply_attested_principal",
            "s2a_v042_apply_attested_initial_credential",
            "s2a_v042_apply_attested_grant"
        )
        val WRITER_FUNCTIONS = listOf(
            "s2a_v042_apply_legacy_unlinked_decision",
            "s2a_v042_begin_attested_decision_verification",
            "s2a_v042_apply_attested_decision"
        )
        val CALLER_FUNCTIONS = ISSUER_FUNCTIONS + WRITER_FUNCTIONS
        val PROTECTED_ROLES = listOf(
            "flooow_command_issuer",
            "flooow_command_runtime",
            "flooow_attestation_verifier",
            "flooow_approval_governance"
        )
        val ISSUER_PROTECTED_TABLES = listOf(
            "command_principal",
            "command_credential_revision",
            "command_permission_grant",
            "command_authority_operation"
        )
        val RUNTIME_READ_TABLES = listOf(
            "command_credential_revision",
            "command_permission_grant",
            "integration_organization",
            "integration_connection",
            "marketplace_transaction_identity_decision",
            "marketplace_transaction_identity_head",
            "marketplace_order_identity_registry",
            "marketplace_order_occurrence_source_promotion",
            "integration_mercado_livre_order_source_observation",
            "integration_omie_transaction_evidence",
            "integration_omie_transaction_evidence_v3",
            "integration_connector_page_commit",
            "integration_connector_progress"
        )
        val STATE_TABLES = listOf(
            "command_principal",
            "command_credential_revision",
            "command_permission_grant",
            "command_authority_operation",
            "s2a_attestation_consumption",
            "marketplace_transaction_identity_decision",
            "marketplace_transaction_identity_head",
            "s2a_accepted_attestation"
        )
    }
}
