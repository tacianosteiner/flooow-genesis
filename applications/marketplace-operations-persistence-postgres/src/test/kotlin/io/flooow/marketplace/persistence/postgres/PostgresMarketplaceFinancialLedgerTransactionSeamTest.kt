package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceAbsenceReason
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerAppendRequestId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerAppendResult
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryDraft
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceOpenRequestId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceOpenResult
import io.flooow.marketplace.operations.economics.ledger.OpenFinancialTrace
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresMarketplaceFinancialLedgerTransactionSeamTest {
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
    fun `same connection seam never owns commit and caller rollback removes trace and entry`() {
        val organizationId = OrganizationId.parse(
            "10000000-0000-0000-0000-000000000001"
        )
        val orderId = MarketplaceOrderId.parse(
            "20000000-0000-0000-0000-000000000001"
        )
        val traceId = FinancialTraceId.of(
            UUID.fromString("30000000-0000-0000-0000-000000000001")
        )
        val entryId = FinancialLedgerEntryId.of(
            UUID.fromString("40000000-0000-0000-0000-000000000001")
        )
        val currency = MarketplaceCurrency("BRL")

        insertOrganization(organizationId)

        val ledger = PostgresMarketplaceFinancialLedgerRepository(configuration)

        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            connection.autoCommit = false

            val open = ledger.openWithinTransaction(
                connection,
                OpenFinancialTrace(
                    organizationId = organizationId,
                    requestId = FinancialTraceOpenRequestId.of(
                        UUID.fromString("50000000-0000-0000-0000-000000000001")
                    ),
                    orderId = orderId,
                    marketplace = MarketplaceKey("mercado-livre"),
                    externalOrderId = MarketplaceExternalOrderId("MLB-B3B2-A"),
                    currency = currency,
                ),
                traceId,
            )

            assertIs<FinancialTraceOpenResult.Opened>(open)

            val append = ledger.appendWithinTransaction(
                connection,
                FinancialLedgerEntryDraft(
                    organizationId = organizationId,
                    requestId = FinancialLedgerAppendRequestId.of(
                        UUID.fromString("60000000-0000-0000-0000-000000000001")
                    ),
                    traceId = traceId,
                    stage = FinancialLedgerStage.SALE,
                    basis = FinancialLedgerBasis.EXPECTED,
                    direction = EconomicDirection.ADDITION,
                    magnitude = MarketplaceMoney.parse(currency, "10"),
                    source = EconomicSource(
                        kind = EconomicSourceKind.CALCULATED,
                        systemKey = EconomicSourceSystemKey("b3b2-seam"),
                        externalReference = EconomicExternalReferenceState.Absent(
                            EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN
                        ),
                    ),
                    occurredAt = Instant.parse("2026-09-13T20:01:00.123456Z"),
                    correctsEntryId = null,
                ),
                entryId,
            )

            assertIs<FinancialLedgerAppendResult.Appended>(append)

            assertEquals(
                1,
                countRows(
                    connection,
                    "marketplace_financial_trace",
                    organizationId
                )
            )
            assertEquals(
                1,
                countRows(
                    connection,
                    "marketplace_financial_ledger_entry",
                    organizationId
                )
            )

            connection.rollback()
        }

        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            assertEquals(
                0,
                countRows(
                    connection,
                    "marketplace_financial_trace",
                    organizationId
                )
            )
            assertEquals(
                0,
                countRows(
                    connection,
                    "marketplace_financial_ledger_entry",
                    organizationId
                )
            )
        }
    }

    @Test
    fun `transaction seam rejects autocommit before any durable mutation`() {
        val organizationId = OrganizationId.parse(
            "10000000-0000-0000-0000-000000000002"
        )
        val orderId = MarketplaceOrderId.parse(
            "20000000-0000-0000-0000-000000000002"
        )
        val traceId = FinancialTraceId.of(
            UUID.fromString("30000000-0000-0000-0000-000000000002")
        )
        val entryId = FinancialLedgerEntryId.of(
            UUID.fromString("40000000-0000-0000-0000-000000000002")
        )
        val currency = MarketplaceCurrency("BRL")

        insertOrganization(organizationId)
        val ledger = PostgresMarketplaceFinancialLedgerRepository(configuration)

        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            check(connection.autoCommit)

            val openCommand = OpenFinancialTrace(
                organizationId = organizationId,
                requestId = FinancialTraceOpenRequestId.of(
                    UUID.fromString("50000000-0000-0000-0000-000000000002")
                ),
                orderId = orderId,
                marketplace = MarketplaceKey("mercado-livre"),
                externalOrderId = MarketplaceExternalOrderId("MLB-B3B2-A-AUTOCOMMIT"),
                currency = currency,
            )

            assertFailsWith<IllegalStateException> {
                ledger.openWithinTransaction(
                    connection,
                    openCommand,
                    traceId,
                )
            }

            val draft = FinancialLedgerEntryDraft(
                organizationId = organizationId,
                requestId = FinancialLedgerAppendRequestId.of(
                    UUID.fromString("60000000-0000-0000-0000-000000000002")
                ),
                traceId = traceId,
                stage = FinancialLedgerStage.SALE,
                basis = FinancialLedgerBasis.EXPECTED,
                direction = EconomicDirection.ADDITION,
                magnitude = MarketplaceMoney.parse(currency, "10"),
                source = EconomicSource(
                    kind = EconomicSourceKind.CALCULATED,
                    systemKey = EconomicSourceSystemKey("b3b2-seam"),
                    externalReference = EconomicExternalReferenceState.Absent(
                        EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN
                    ),
                ),
                occurredAt = Instant.parse("2026-09-13T20:02:00.123456Z"),
                correctsEntryId = null,
            )

            assertFailsWith<IllegalStateException> {
                ledger.appendWithinTransaction(
                    connection,
                    draft,
                    entryId,
                )
            }

            assertEquals(
                0,
                countRows(
                    connection,
                    "marketplace_financial_trace",
                    organizationId
                )
            )
            assertEquals(
                0,
                countRows(
                    connection,
                    "marketplace_financial_ledger_entry",
                    organizationId
                )
            )
        }
    }

    private fun insertOrganization(organizationId: OrganizationId) {
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            connection.prepareStatement(
                "INSERT INTO integration_organization " +
                    "(organization_id,status,created_at,updated_at) " +
                    "VALUES (?,?,?,?)"
            ).use { statement ->
                val now = Timestamp.from(
                    Instant.parse("2026-09-13T20:00:00Z")
                )
                statement.setObject(1, organizationId.value)
                statement.setString(2, "ACTIVE")
                statement.setTimestamp(3, now)
                statement.setTimestamp(4, now)
                assertEquals(1, statement.executeUpdate())
            }
        }
    }

    private fun countRows(
        connection: Connection,
        table: String,
        organizationId: OrganizationId
    ): Int {
        require(
            table == "marketplace_financial_trace" ||
                table == "marketplace_financial_ledger_entry"
        )

        return connection.prepareStatement(
            "SELECT count(*) FROM $table WHERE organization_id=?"
        ).use { statement ->
            statement.setObject(1, organizationId.value)
            statement.executeQuery().use { result ->
                check(result.next())
                result.getInt(1)
            }
        }
    }
}
