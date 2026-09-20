package io.flooow.marketplace.persistence.postgres

import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresFinancialLedgerMaterializationLineageSchemaTest {
    private lateinit var postgres: PostgreSQLContainer
    private lateinit var configuration: PostgresConfiguration

    @BeforeTest
    fun startPostgres() {
        postgres = PostgreSQLContainer("postgres:18.4")
        postgres.start()
        configuration = PostgresConfiguration(
            postgres.jdbcUrl,
            postgres.username,
            postgres.password
        )
        Flyway.configure()
            .dataSource(
                configuration.url,
                configuration.user,
                configuration.password
            )
            .load()
            .migrate()
    }

    @AfterTest
    fun stopPostgres() = postgres.stop()

    @Test
    fun `V032 installs frozen source lineage shape`() {
        assertTrue(
            queryStrings(
                "SELECT version FROM flyway_schema_history " +
                    "WHERE success ORDER BY installed_rank"
            ).contains("032")
        )

        val constraints = queryStrings(
            "SELECT pg_get_constraintdef(oid) " +
                "FROM pg_constraint " +
                "WHERE conrelid = " +
                "'marketplace_financial_ledger_materialization_lineage'::regclass"
        ).joinToString("\n")

        assertTrue(constraints.contains("source_fingerprint_canonicalization_version = 1"))
        assertTrue(constraints.contains("source_order_id"))
        assertTrue(constraints.contains("marketplace_economic_evidence_component_fact"))
        assertTrue(constraints.contains("marketplace-financial-ledger-materialization/1"))
        assertTrue(constraints.contains("EXPECTED"))
        assertTrue(constraints.contains("ACTUAL"))
        assertTrue(constraints.contains("SALE"))
        assertTrue(constraints.contains("OTHER_ADJUSTMENT"))
        assertTrue(!constraints.contains("SETTLEMENT"))
        assertTrue(!constraints.contains("PAYMENT_ACCOUNT"))
        assertTrue(!constraints.contains("BANK"))
    }

    @Test
    fun `lineage is immutable and exact source authority is unique`() {
        val fixture = fixture()
        insertOrganization(fixture.organizationId)
        insertTrace(fixture)
        insertSourceComponent(fixture)
        insertLedgerEntry(
            fixture = fixture,
            entryId = fixture.entryId,
            appendRequestId = fixture.appendRequestId,
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = null
        )
        insertLineage(
            fixture = fixture,
            sourceAuthorityIdentity = fixture.sourceAuthorityIdentity,
            entryId = fixture.entryId,
            stage = "SALE",
            basis = "EXPECTED"
        )

        assertEquals(
            1,
            countLineage(
                fixture.organizationId,
                fixture.sourceAuthorityIdentity
            )
        )

        assertFailsWith<SQLException> {
            executeUpdate(
                "UPDATE marketplace_financial_ledger_materialization_lineage " +
                    "SET basis='ACTUAL' " +
                    "WHERE organization_id=? " +
                    "AND source_authority_identity=?"
            ) {
                setObject(1, fixture.organizationId)
                setObject(2, fixture.sourceAuthorityIdentity)
            }
        }

        assertFailsWith<SQLException> {
            executeUpdate(
                "DELETE FROM marketplace_financial_ledger_materialization_lineage " +
                    "WHERE organization_id=? " +
                    "AND source_authority_identity=?"
            ) {
                setObject(1, fixture.organizationId)
                setObject(2, fixture.sourceAuthorityIdentity)
            }
        }

        val secondEntry = UUID.randomUUID()
        insertLedgerEntry(
            fixture = fixture,
            entryId = secondEntry,
            appendRequestId = UUID.randomUUID(),
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = null,
            sourceReference = "unrelated-$secondEntry"
        )

        assertFailsWith<SQLException> {
            insertLineage(
                fixture = fixture,
                sourceAuthorityIdentity = fixture.sourceAuthorityIdentity,
                entryId = secondEntry,
                stage = "SALE",
                basis = "EXPECTED"
            )
        }
    }

    @Test
    fun `lineage rejects semantic mismatch unsupported stage and correction entry`() {
        val fixture = fixture()
        insertOrganization(fixture.organizationId)
        insertTrace(fixture)
        insertSourceComponent(fixture)

        insertLedgerEntry(
            fixture = fixture,
            entryId = fixture.entryId,
            appendRequestId = fixture.appendRequestId,
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = null
        )

        assertFailsWith<SQLException> {
            insertLineage(
                fixture = fixture,
                sourceAuthorityIdentity = UUID.randomUUID(),
                entryId = fixture.entryId,
                stage = "TAX",
                basis = "EXPECTED"
            )
        }

        assertFailsWith<SQLException> {
            insertLineage(
                fixture = fixture,
                sourceAuthorityIdentity = UUID.randomUUID(),
                entryId = fixture.entryId,
                stage = "SETTLEMENT",
                basis = "EXPECTED"
            )
        }

        val correctionEntry = UUID.randomUUID()
        insertLedgerEntry(
            fixture = fixture,
            entryId = correctionEntry,
            appendRequestId = UUID.randomUUID(),
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = fixture.entryId,
            sourceReference = "correction-$correctionEntry"
        )

        assertFailsWith<SQLException> {
            insertLineage(
                fixture = fixture,
                sourceAuthorityIdentity = fixture.sourceAuthorityIdentity,
                entryId = correctionEntry,
                stage = "SALE",
                basis = "EXPECTED"
            )
        }
    }

    @Test
    fun `source identity is scoped by organization and order`() {
        val organizationId = UUID.randomUUID()
        val sharedSourceIdentity = UUID.randomUUID()
        val first = fixture(
            organizationId = organizationId,
            sourceAuthorityIdentity = sharedSourceIdentity
        )
        val second = fixture(
            organizationId = organizationId,
            sourceAuthorityIdentity = sharedSourceIdentity
        )

        insertOrganization(organizationId)

        listOf(first, second).forEach { fixture ->
            insertTrace(fixture)
            insertSourceComponent(fixture)
            insertLedgerEntry(
                fixture = fixture,
                entryId = fixture.entryId,
                appendRequestId = fixture.appendRequestId,
                stage = "SALE",
                basis = "EXPECTED",
                correctsEntryId = null
            )
            insertLineage(
                fixture = fixture,
                sourceAuthorityIdentity = sharedSourceIdentity,
                entryId = fixture.entryId,
                stage = "SALE",
                basis = "EXPECTED"
            )
        }

        assertEquals(
            2,
            countLineage(organizationId, sharedSourceIdentity)
        )
    }

    @Test
    fun `lineage rejects ledger payload that does not preserve source`() {
        val fixture = fixture()
        insertOrganization(fixture.organizationId)
        insertTrace(fixture)
        insertSourceComponent(fixture)

        insertLedgerEntry(
            fixture = fixture,
            entryId = fixture.entryId,
            appendRequestId = fixture.appendRequestId,
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = null,
            magnitude = "10.01"
        )

        assertFailsWith<SQLException> {
            insertLineage(
                fixture = fixture,
                sourceAuthorityIdentity = fixture.sourceAuthorityIdentity,
                entryId = fixture.entryId,
                stage = "SALE",
                basis = "EXPECTED"
            )
        }
    }

    @Test
    fun `lineage rejects any trace subject context mismatch`() {
        val organizationId = UUID.randomUUID()
        insertOrganization(organizationId)

        val marketplaceMismatch = fixture(
            organizationId = organizationId
        )
        insertTrace(
            fixture = marketplaceMismatch,
            marketplace = "amazon"
        )
        insertSourceComponent(marketplaceMismatch)
        insertLedgerEntry(
            fixture = marketplaceMismatch,
            entryId = marketplaceMismatch.entryId,
            appendRequestId = marketplaceMismatch.appendRequestId,
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = null
        )
        assertFailsWith<SQLException> {
            insertLineage(
                fixture = marketplaceMismatch,
                sourceAuthorityIdentity = marketplaceMismatch.sourceAuthorityIdentity,
                entryId = marketplaceMismatch.entryId,
                stage = "SALE",
                basis = "EXPECTED"
            )
        }

        val externalOrderMismatch = fixture(
            organizationId = organizationId
        )
        insertTrace(
            fixture = externalOrderMismatch,
            externalOrderId = "different-${externalOrderMismatch.orderId}"
        )
        insertSourceComponent(externalOrderMismatch)
        insertLedgerEntry(
            fixture = externalOrderMismatch,
            entryId = externalOrderMismatch.entryId,
            appendRequestId = externalOrderMismatch.appendRequestId,
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = null
        )
        assertFailsWith<SQLException> {
            insertLineage(
                fixture = externalOrderMismatch,
                sourceAuthorityIdentity = externalOrderMismatch.sourceAuthorityIdentity,
                entryId = externalOrderMismatch.entryId,
                stage = "SALE",
                basis = "EXPECTED"
            )
        }

        val currencyMismatch = fixture(
            organizationId = organizationId
        )
        insertTrace(
            fixture = currencyMismatch,
            currency = "USD"
        )
        insertSourceComponent(currencyMismatch)
        insertLedgerEntry(
            fixture = currencyMismatch,
            entryId = currencyMismatch.entryId,
            appendRequestId = currencyMismatch.appendRequestId,
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = null
        )
        assertFailsWith<SQLException> {
            insertLineage(
                fixture = currencyMismatch,
                sourceAuthorityIdentity = currencyMismatch.sourceAuthorityIdentity,
                entryId = currencyMismatch.entryId,
                stage = "SALE",
                basis = "EXPECTED"
            )
        }
    }

    @Test
    fun `lineage rejects invalid fingerprint policy and semantic version`() {
        val fixture = fixture()
        insertOrganization(fixture.organizationId)
        insertTrace(fixture)
        insertSourceComponent(fixture)
        insertLedgerEntry(
            fixture = fixture,
            entryId = fixture.entryId,
            appendRequestId = fixture.appendRequestId,
            stage = "SALE",
            basis = "EXPECTED",
            correctsEntryId = null
        )

        assertFailsWith<SQLException> {
            insertLineageRaw(
                fixture = fixture,
                sourceAuthorityIdentity = UUID.randomUUID(),
                entryId = fixture.entryId,
                fingerprint = "ABC",
                semanticVersion = "marketplace-economic-component/1",
                policyVersion = "marketplace-financial-ledger-materialization/1",
                stage = "SALE",
                basis = "EXPECTED"
            )
        }

        assertFailsWith<SQLException> {
            insertLineageRaw(
                fixture = fixture,
                sourceAuthorityIdentity = UUID.randomUUID(),
                entryId = fixture.entryId,
                fingerprint = "a".repeat(64),
                semanticVersion = "UPPERCASE/1",
                policyVersion = "marketplace-financial-ledger-materialization/1",
                stage = "SALE",
                basis = "EXPECTED"
            )
        }

        assertFailsWith<SQLException> {
            insertLineageRaw(
                fixture = fixture,
                sourceAuthorityIdentity = UUID.randomUUID(),
                entryId = fixture.entryId,
                fingerprint = "a".repeat(64),
                semanticVersion = "marketplace-economic-component/1",
                policyVersion = "marketplace-financial-ledger-materialization/2",
                stage = "SALE",
                basis = "EXPECTED"
            )
        }
    }

    private fun fixture(
        organizationId: UUID = UUID.randomUUID(),
        sourceAuthorityIdentity: UUID = UUID.randomUUID()
    ) = Fixture(
        organizationId = organizationId,
        traceId = UUID.randomUUID(),
        openRequestId = UUID.randomUUID(),
        orderId = UUID.randomUUID(),
        entryId = UUID.randomUUID(),
        appendRequestId = UUID.randomUUID(),
        sourceAuthorityIdentity = sourceAuthorityIdentity
    )

    private fun insertOrganization(organizationId: UUID) {
        val now = Timestamp.from(Instant.parse("2026-09-13T20:00:00Z"))
        executeUpdate(
            "INSERT INTO integration_organization " +
                "(organization_id,status,created_at,updated_at) " +
                "VALUES (?,'ACTIVE',?,?)"
        ) {
            setObject(1, organizationId)
            setTimestamp(2, now)
            setTimestamp(3, now)
        }
    }

    private fun insertTrace(
        fixture: Fixture,
        marketplace: String = "mercado-livre",
        externalOrderId: String = "order-${fixture.orderId}",
        currency: String = "BRL"
    ) {
        executeUpdate(
            "INSERT INTO marketplace_financial_trace " +
                "(organization_id,trace_id,open_request_id,order_id," +
                "marketplace_key,external_order_id,currency) " +
                "VALUES (?,?,?,?,?,?,?)"
        ) {
            setObject(1, fixture.organizationId)
            setObject(2, fixture.traceId)
            setObject(3, fixture.openRequestId)
            setObject(4, fixture.orderId)
            setString(5, marketplace)
            setString(6, externalOrderId)
            setString(7, currency)
        }
    }

    private fun insertLedgerEntry(
        fixture: Fixture,
        entryId: UUID,
        appendRequestId: UUID,
        stage: String,
        basis: String,
        correctsEntryId: UUID?,
        magnitude: String = "10.00",
        sourceReference: String = "source-${fixture.orderId}"
    ) {
        executeUpdate(
            "INSERT INTO marketplace_financial_ledger_entry " +
                "(organization_id,entry_id,append_request_id,trace_id," +
                "stage,basis,direction,magnitude,source_kind," +
                "source_system_key,external_reference," +
                "external_reference_absence_reason,occurred_at,corrects_entry_id) " +
                "VALUES (?,?,?,?,?,?,'ADDITION',?::numeric,'MARKETPLACE'," +
                "'b3b-source',?,NULL,?,?)"
        ) {
            setObject(1, fixture.organizationId)
            setObject(2, entryId)
            setObject(3, appendRequestId)
            setObject(4, fixture.traceId)
            setString(5, stage)
            setString(6, basis)
            setString(7, magnitude)
            setString(8, sourceReference)
            setTimestamp(
                9,
                Timestamp.from(Instant.parse("2026-09-13T20:01:00.123456Z"))
            )
            setObject(10, correctsEntryId)
        }
    }

    private fun insertSourceComponent(fixture: Fixture) {
        connection().use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_subject " +
                        "(organization_id,marketplace_order_id,marketplace_key," +
                        "external_order_id,currency) VALUES (?,?," +
                        "'mercado-livre',?,'BRL')"
                ).use { statement ->
                    statement.setObject(1, fixture.organizationId)
                    statement.setObject(2, fixture.orderId)
                    statement.setString(3, "order-${fixture.orderId}")
                    statement.executeUpdate()
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_update " +
                        "(organization_id,marketplace_order_id,evidence_version," +
                        "update_id,change_kind) VALUES (?,?,1,?,'FACT')"
                ).use { statement ->
                    statement.setObject(1, fixture.organizationId)
                    statement.setObject(2, fixture.orderId)
                    statement.setObject(3, fixture.sourceAuthorityIdentity)
                    statement.executeUpdate()
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) " +
                        "VALUES (?,?,?,1,'FACT')"
                ).use { statement ->
                    statement.setObject(1, fixture.organizationId)
                    statement.setObject(2, fixture.orderId)
                    statement.setObject(3, fixture.sourceAuthorityIdentity)
                    statement.executeUpdate()
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_fact " +
                        "(organization_id,marketplace_order_id,fact_id," +
                        "evidence_version,fact_kind,family,observed_at) " +
                        "VALUES (?,?,?,1,'COMPONENT'," +
                        "'MARKETPLACE_ORDER',?)"
                ).use { statement ->
                    statement.setObject(1, fixture.organizationId)
                    statement.setObject(2, fixture.orderId)
                    statement.setObject(3, fixture.sourceAuthorityIdentity)
                    statement.setTimestamp(
                        4,
                        Timestamp.from(
                            Instant.parse("2026-09-13T20:01:01.123456Z")
                        )
                    )
                    statement.executeUpdate()
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_component_fact " +
                        "(organization_id,marketplace_order_id,fact_id," +
                        "evidence_version,fact_kind,family,component_id," +
                        "component_type,direction,magnitude,currency," +
                        "source_kind,source_system_key," +
                        "source_external_reference," +
                        "source_external_reference_absence_reason," +
                        "occurred_at,quality,coverage) " +
                        "VALUES (?,?,?,1,'COMPONENT'," +
                        "'MARKETPLACE_ORDER',?,'REVENUE'," +
                        "'ADDITION',10.00,'BRL','MARKETPLACE'," +
                        "'b3b-source',?,NULL,?," +
                        "'CONFIRMED','COMPLETE')"
                ).use { statement ->
                    statement.setObject(1, fixture.organizationId)
                    statement.setObject(2, fixture.orderId)
                    statement.setObject(3, fixture.sourceAuthorityIdentity)
                    statement.setObject(4, UUID.randomUUID())
                    statement.setString(5, "source-${fixture.orderId}")
                    statement.setTimestamp(
                        6,
                        Timestamp.from(
                            Instant.parse("2026-09-13T20:01:00.123456Z")
                        )
                    )
                    statement.executeUpdate()
                }

                connection.prepareStatement(
                    "UPDATE marketplace_economic_evidence_subject " +
                        "SET current_version=1 " +
                        "WHERE organization_id=? " +
                        "AND marketplace_order_id=?"
                ).use { statement ->
                    statement.setObject(1, fixture.organizationId)
                    statement.setObject(2, fixture.orderId)
                    statement.executeUpdate()
                }

                connection.commit()
            } catch (error: Exception) {
                connection.rollback()
                throw error
            }
        }
    }

    private fun insertLineage(
        fixture: Fixture,
        sourceAuthorityIdentity: UUID,
        entryId: UUID,
        stage: String,
        basis: String
    ) {
        insertLineageRaw(
            fixture = fixture,
            sourceAuthorityIdentity = sourceAuthorityIdentity,
            entryId = entryId,
            fingerprint = "a".repeat(64),
            semanticVersion = "marketplace-economic-component/1",
            policyVersion = "marketplace-financial-ledger-materialization/1",
            stage = stage,
            basis = basis
        )
    }

    private fun insertLineageRaw(
        fixture: Fixture,
        sourceAuthorityIdentity: UUID,
        entryId: UUID,
        fingerprint: String,
        semanticVersion: String,
        policyVersion: String,
        stage: String,
        basis: String
    ) {
        executeUpdate(
            "INSERT INTO marketplace_financial_ledger_materialization_lineage " +
                "(organization_id,source_order_id,source_authority_identity," +
                "source_fingerprint_canonicalization_version," +
                "source_fingerprint_sha256,source_authority_semantic_version," +
                "materialization_policy_version,stage,basis,trace_id,ledger_entry_id) " +
                "VALUES (?,?,?,1,?,?,?,?,?,?,?)"
        ) {
            setObject(1, fixture.organizationId)
            setObject(2, fixture.orderId)
            setObject(3, sourceAuthorityIdentity)
            setString(4, fingerprint)
            setString(5, semanticVersion)
            setString(6, policyVersion)
            setString(7, stage)
            setString(8, basis)
            setObject(9, fixture.traceId)
            setObject(10, entryId)
        }
    }

    private fun countLineage(
        organizationId: UUID,
        sourceAuthorityIdentity: UUID
    ): Int = connection().use { connection ->
        connection.prepareStatement(
            "SELECT count(*) " +
                "FROM marketplace_financial_ledger_materialization_lineage " +
                "WHERE organization_id=? AND source_authority_identity=?"
        ).use { statement ->
            statement.setObject(1, organizationId)
            statement.setObject(2, sourceAuthorityIdentity)
            statement.executeQuery().use { result ->
                result.next()
                result.getInt(1)
            }
        }
    }

    private fun queryStrings(sql: String): List<String> =
        connection().use { connection ->
            connection.createStatement().use { statement ->
                statement.executeQuery(sql).use { result ->
                    buildList {
                        while (result.next()) {
                            add(result.getString(1))
                        }
                    }
                }
            }
        }

    private fun executeUpdate(
        sql: String,
        bind: java.sql.PreparedStatement.() -> Unit
    ): Int = connection().use { connection ->
        connection.prepareStatement(sql).use { statement ->
            statement.bind()
            statement.executeUpdate()
        }
    }

    private fun connection(): Connection =
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        )

    private data class Fixture(
        val organizationId: UUID,
        val traceId: UUID,
        val openRequestId: UUID,
        val orderId: UUID,
        val entryId: UUID,
        val appendRequestId: UUID,
        val sourceAuthorityIdentity: UUID
    )
}
