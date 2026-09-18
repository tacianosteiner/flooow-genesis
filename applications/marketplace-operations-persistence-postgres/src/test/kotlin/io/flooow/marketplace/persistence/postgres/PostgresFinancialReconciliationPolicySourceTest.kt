package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicyContext
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicySelection
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.sql.Types
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject

class PostgresFinancialReconciliationPolicySourceTest {
    private val orgA =
        UUID.fromString(
            "10000000-0000-0000-0000-000000000001"
        )

    private val orgB =
        UUID.fromString(
            "10000000-0000-0000-0000-000000000002"
        )

    private val marketplace =
        "mercado-livre"

    private val currency =
        "BRL"

    @Test
    fun `current policy is exact scoped and cross organization reads fail closed`() {
        withDatabase { configuration ->
            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                seedOrganization(
                    connection,
                    orgA
                )

                seedOrganization(
                    connection,
                    orgB
                )

                insertPolicy(
                    connection,
                    orgA,
                    "policy/1",
                    "0.01"
                )

                activatePolicy(
                    connection,
                    orgA,
                    "policy/1"
                )
            }

            val source =
                PostgresFinancialReconciliationPolicySource(
                    configuration
                )

            val selected =
                assertIs<
                    FinancialReconciliationPolicySelection
                        .Selected
                    >(
                    source.select(
                        context(
                            orgA
                        )
                    )
                )

            assertEquals(
                "policy/1",
                selected.policy.version.value
            )

            assertEquals(
                MarketplaceCurrency(
                    "BRL"
                ),
                selected.policy.currency
            )

            FinancialLedgerStage.entries
                .forEach { stage ->
                    assertEquals(
                        "0.01",
                        selected.policy
                            .tolerancesByStage
                            .getValue(stage)
                            .amount
                            .toPlainString()
                    )
                }

            assertEquals(
                FinancialReconciliationPolicySelection
                    .Unavailable,
                source.select(
                    context(
                        orgB
                    )
                )
            )

            assertEquals(
                FinancialReconciliationPolicySelection
                    .Unavailable,
                source.select(
                    FinancialReconciliationPolicyContext(
                        organizationId =
                            OrganizationId(
                                orgA
                            ),
                        marketplace =
                            MarketplaceKey(
                                "amazon"
                            ),
                        currency =
                            MarketplaceCurrency(
                                "BRL"
                            )
                    )
                )
            )
        }
    }

    @Test
    fun `missing binding and database failure remain distinct`() {
        withDatabase { configuration ->
            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                seedOrganization(
                    connection,
                    orgA
                )
            }

            assertEquals(
                FinancialReconciliationPolicySelection
                    .Unavailable,
                PostgresFinancialReconciliationPolicySource(
                    configuration
                ).select(
                    context(
                        orgA
                    )
                )
            )
        }

        assertEquals(
            FinancialReconciliationPolicySelection
                .ReadFailure,
            PostgresFinancialReconciliationPolicySource(
                PostgresConfiguration(
                    url =
                        "jdbc:postgresql://127.0.0.1:1/" +
                            "flooow_unavailable" +
                            "?connectTimeout=1&socketTimeout=1",
                    user = "none",
                    password = "none"
                )
            ).select(
                context(
                    orgA
                )
            )
        )
    }

    @Test
    fun `policy definitions are immutable and current binding may activate another immutable version`() {
        withDatabase { configuration ->
            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                seedOrganization(
                    connection,
                    orgA
                )

                insertPolicy(
                    connection,
                    orgA,
                    "policy/1",
                    "0"
                )

                insertPolicy(
                    connection,
                    orgA,
                    "policy/2",
                    "0.05"
                )

                activatePolicy(
                    connection,
                    orgA,
                    "policy/1"
                )

                assertFailsWith<SQLException> {
                    connection.prepareStatement(
                        """
                        UPDATE marketplace_financial_reconciliation_policy
                           SET stage_tolerances=?::jsonb
                         WHERE organization_id=?
                           AND marketplace_key=?
                           AND currency=?
                           AND policy_version='policy/1'
                        """.trimIndent()
                    ).use { statement ->
                        statement.setString(
                            1,
                            tolerancesJson(
                                "0.10"
                            )
                        )
                        statement.setObject(
                            2,
                            orgA
                        )
                        statement.setString(
                            3,
                            marketplace
                        )
                        statement.setString(
                            4,
                            currency
                        )
                        statement.executeUpdate()
                    }
                }

                connection.prepareStatement(
                    """
                    UPDATE marketplace_financial_reconciliation_policy_current
                       SET policy_version='policy/2',
                           activated_at=transaction_timestamp()
                     WHERE organization_id=?
                       AND marketplace_key=?
                       AND currency=?
                    """.trimIndent()
                ).use { statement ->
                    statement.setObject(
                        1,
                        orgA
                    )
                    statement.setString(
                        2,
                        marketplace
                    )
                    statement.setString(
                        3,
                        currency
                    )

                    assertEquals(
                        1,
                        statement.executeUpdate()
                    )
                }
            }

            val selected =
                assertIs<
                    FinancialReconciliationPolicySelection
                        .Selected
                    >(
                    PostgresFinancialReconciliationPolicySource(
                        configuration
                    ).select(
                        context(
                            orgA
                        )
                    )
                )

            assertEquals(
                "policy/2",
                selected.policy.version.value
            )

            assertEquals(
                "0.05",
                selected.policy
                    .tolerancesByStage
                    .getValue(
                        FinancialLedgerStage.SALE
                    )
                    .amount
                    .toPlainString()
            )
        }
    }

    @Test
    fun `database rejects incomplete tolerance policies`() {
        withDatabase { configuration ->
            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                seedOrganization(
                    connection,
                    orgA
                )

                assertFailsWith<SQLException> {
                    connection.prepareStatement(
                        """
                        INSERT INTO marketplace_financial_reconciliation_policy
                            (
                                organization_id,
                                marketplace_key,
                                currency,
                                policy_version,
                                stage_tolerances
                            )
                        VALUES (?,?,?,?,?::jsonb)
                        """.trimIndent()
                    ).use { statement ->
                        statement.setObject(
                            1,
                            orgA
                        )
                        statement.setString(
                            2,
                            marketplace
                        )
                        statement.setString(
                            3,
                            currency
                        )
                        statement.setString(
                            4,
                            "invalid/1"
                        )
                        statement.setString(
                            5,
                            """{"SALE":"0"}"""
                        )
                        statement.executeUpdate()
                    }
                }
            }
        }
    }

    private fun context(
        organizationId: UUID
    ): FinancialReconciliationPolicyContext =
        FinancialReconciliationPolicyContext(
            organizationId =
                OrganizationId(
                    organizationId
                ),
            marketplace =
                MarketplaceKey(
                    marketplace
                ),
            currency =
                MarketplaceCurrency(
                    currency
                )
        )

    private fun withDatabase(
        block:
            (
                PostgresConfiguration
            ) -> Unit
    ) {
        PostgreSQLContainer(
            "postgres:18.4"
        ).use { pg ->
            pg.start()

            val configuration =
                PostgresConfiguration(
                    pg.jdbcUrl,
                    pg.username,
                    pg.password
                )

            Flyway.configure()
                .dataSource(
                    configuration.url,
                    configuration.user,
                    configuration.password
                )
                .load()
                .migrate()

            block(
                configuration
            )
        }
    }

    private fun seedOrganization(
        connection: Connection,
        organizationId: UUID
    ) {
        connection.prepareStatement(
            """
            INSERT INTO integration_organization
                (
                    organization_id,
                    status,
                    created_at,
                    updated_at
                )
            VALUES (?,'ACTIVE',now(),now())
            """.trimIndent()
        ).use { statement ->
            statement.setObject(
                1,
                organizationId
            )
            statement.executeUpdate()
        }
    }

    private fun insertPolicy(
        connection: Connection,
        organizationId: UUID,
        version: String,
        tolerance: String
    ) {
        connection.prepareStatement(
            """
            INSERT INTO marketplace_financial_reconciliation_policy
                (
                    organization_id,
                    marketplace_key,
                    currency,
                    policy_version,
                    stage_tolerances
                )
            VALUES (?,?,?,?,?)
            """.trimIndent()
        ).use { statement ->
            statement.setObject(
                1,
                organizationId
            )
            statement.setString(
                2,
                marketplace
            )
            statement.setString(
                3,
                currency
            )
            statement.setString(
                4,
                version
            )
            statement.setObject(
                5,
                tolerancesJson(
                    tolerance
                ),
                Types.OTHER
            )
            statement.executeUpdate()
        }
    }

    private fun activatePolicy(
        connection: Connection,
        organizationId: UUID,
        version: String
    ) {
        connection.prepareStatement(
            """
            INSERT INTO marketplace_financial_reconciliation_policy_current
                (
                    organization_id,
                    marketplace_key,
                    currency,
                    policy_version
                )
            VALUES (?,?,?,?)
            """.trimIndent()
        ).use { statement ->
            statement.setObject(
                1,
                organizationId
            )
            statement.setString(
                2,
                marketplace
            )
            statement.setString(
                3,
                currency
            )
            statement.setString(
                4,
                version
            )
            statement.executeUpdate()
        }
    }

    private fun tolerancesJson(
        amount: String
    ): String =
        buildJsonObject {
            FinancialLedgerStage.entries
                .forEach { stage ->
                    put(
                        stage.name,
                        JsonPrimitive(
                            amount
                        )
                    )
                }
        }.toString()
}
