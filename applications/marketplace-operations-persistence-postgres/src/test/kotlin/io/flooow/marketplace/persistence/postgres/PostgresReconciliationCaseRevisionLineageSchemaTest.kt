package io.flooow.marketplace.persistence.postgres

import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import org.flywaydb.core.Flyway
import org.flywaydb.core.api.MigrationVersion
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresReconciliationCaseRevisionLineageSchemaTest {

    @Test
    fun `legacy reconciliation case survives lineage migration without synthetic backfill`() {
        PostgreSQLContainer("postgres:18.4").use { pg ->
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
                .target(MigrationVersion.fromVersion("24"))
                .load()
                .migrate()

            val fixture = fixture()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                persistOrganizationAndTrace(connection, fixture)
                persistCase(connection, fixture, revision = 7L)
            }

            Flyway.configure()
                .dataSource(
                    configuration.url,
                    configuration.user,
                    configuration.password
                )
                .load()
                .migrate()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                assertEquals(
                    1L,
                    scalarLong(
                        connection,
                        """
                        SELECT count(*)
                          FROM marketplace_reconciliation_case
                         WHERE organization_id=?
                           AND case_id=?
                        """.trimIndent(),
                        fixture.organizationId,
                        fixture.caseId
                    )
                )

                assertEquals(
                    0L,
                    scalarLong(
                        connection,
                        """
                        SELECT count(*)
                          FROM marketplace_reconciliation_case_revision_assessment
                         WHERE organization_id=?
                           AND case_id=?
                        """.trimIndent(),
                        fixture.organizationId,
                        fixture.caseId
                    )
                )
            }
        }
    }

    @Test
    fun `legacy same revision update allows only lifecycle fields while revision change still requires lineage`() {
        PostgreSQLContainer("postgres:18.4").use { pg ->
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
                .target(
                    MigrationVersion.fromVersion(
                        "24"
                    )
                )
                .load()
                .migrate()

            val fixture =
                fixture()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                persistOrganizationAndTrace(
                    connection,
                    fixture
                )

                persistCase(
                    connection,
                    fixture,
                    revision = 7L
                )
            }

            Flyway.configure()
                .dataSource(
                    configuration.url,
                    configuration.user,
                    configuration.password
                )
                .load()
                .migrate()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                val affected =
                    connection.prepareStatement(
                        """
                        UPDATE marketplace_reconciliation_case
                           SET status='ACKNOWLEDGED'
                         WHERE organization_id=?
                           AND case_id=?
                           AND revision=7
                        """.trimIndent()
                    ).use { statement ->
                        statement.setObject(
                            1,
                            fixture.organizationId
                        )
                        statement.setObject(
                            2,
                            fixture.caseId
                        )
                        statement.executeUpdate()
                    }

                assertEquals(
                    1,
                    affected
                )

                assertEquals(
                    1L,
                    scalarLong(
                        connection,
                        """
                        SELECT count(*)
                          FROM marketplace_reconciliation_case
                         WHERE organization_id=?
                           AND case_id=?
                           AND revision=7
                           AND status='ACKNOWLEDGED'
                        """.trimIndent(),
                        fixture.organizationId,
                        fixture.caseId
                    )
                )

                assertEquals(
                    0L,
                    scalarLong(
                        connection,
                        """
                        SELECT count(*)
                          FROM marketplace_reconciliation_case_revision_assessment
                         WHERE organization_id=?
                           AND case_id=?
                        """.trimIndent(),
                        fixture.organizationId,
                        fixture.caseId
                    )
                )

                /*
                 * Same-revision mutation of assessment-bound economic state is
                 * not lifecycle. It must fail rather than silently detach the
                 * durable case projection from its revision semantics.
                 */
                connection.autoCommit =
                    false

                connection.prepareStatement(
                    """
                    UPDATE marketplace_reconciliation_case
                       SET absolute_difference_summary=11
                     WHERE organization_id=?
                       AND case_id=?
                       AND revision=7
                    """.trimIndent()
                ).use { statement ->
                    statement.setObject(
                        1,
                        fixture.organizationId
                    )
                    statement.setObject(
                        2,
                        fixture.caseId
                    )

                    assertEquals(
                        1,
                        statement.executeUpdate()
                    )
                }

                assertFailsWith<SQLException> {
                    connection.commit()
                }

                connection.rollback()

                assertEquals(
                    10L,
                    scalarLong(
                        connection,
                        """
                        SELECT absolute_difference_summary::bigint
                          FROM marketplace_reconciliation_case
                         WHERE organization_id=?
                           AND case_id=?
                           AND revision=7
                        """.trimIndent(),
                        fixture.organizationId,
                        fixture.caseId
                    )
                )

                /*
                 * A genuine assessment revision transition still requires
                 * matching lineage at transaction commit.
                 */
                connection.autoCommit =
                    false

                connection.prepareStatement(
                    """
                    UPDATE marketplace_reconciliation_case
                       SET revision=8
                     WHERE organization_id=?
                       AND case_id=?
                       AND revision=7
                    """.trimIndent()
                ).use { statement ->
                    statement.setObject(
                        1,
                        fixture.organizationId
                    )
                    statement.setObject(
                        2,
                        fixture.caseId
                    )

                    assertEquals(
                        1,
                        statement.executeUpdate()
                    )
                }

                assertFailsWith<SQLException> {
                    connection.commit()
                }

                connection.rollback()

                assertEquals(
                    7L,
                    scalarLong(
                        connection,
                        """
                        SELECT revision
                          FROM marketplace_reconciliation_case
                         WHERE organization_id=?
                           AND case_id=?
                        """.trimIndent(),
                        fixture.organizationId,
                        fixture.caseId
                    )
                )

                assertEquals(
                    0L,
                    scalarLong(
                        connection,
                        """
                        SELECT count(*)
                          FROM marketplace_reconciliation_case_revision_assessment
                         WHERE organization_id=?
                           AND case_id=?
                        """.trimIndent(),
                        fixture.organizationId,
                        fixture.caseId
                    )
                )
            }
        }
    }

    @Test
    fun `new or changed current case revision cannot commit without matching lineage`() {
        PostgreSQLContainer("postgres:18.4").use { pg ->
            pg.start()
            val configuration =
                migratedConfiguration(pg)

            val fixture = fixture()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                persistOrganizationAndTrace(connection, fixture)

                assertFailsWith<SQLException> {
                    persistCase(connection, fixture, revision = 1L)
                }
            }
        }
    }

    @Test
    fun `case revision and exact assessment lineage can commit atomically`() {
        PostgreSQLContainer("postgres:18.4").use { pg ->
            pg.start()
            val configuration =
                migratedConfiguration(pg)

            val fixture = fixture()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                connection.autoCommit = false

                persistOrganizationAndTrace(connection, fixture)
                persistCase(connection, fixture, revision = 1L)
                persistLineage(
                    connection,
                    fixture,
                    revision = 1L,
                    fingerprint = "a".repeat(64)
                )

                connection.commit()

                assertEquals(
                    1L,
                    scalarLong(
                        connection,
                        """
                        SELECT count(*)
                          FROM marketplace_reconciliation_case_revision_assessment
                         WHERE organization_id=?
                           AND case_id=?
                           AND case_revision=1
                        """.trimIndent(),
                        fixture.organizationId,
                        fixture.caseId
                    )
                )
            }
        }
    }

    @Test
    fun `lineage is append only`() {
        PostgreSQLContainer("postgres:18.4").use { pg ->
            pg.start()
            val configuration =
                migratedConfiguration(pg)

            val fixture = fixture()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                connection.autoCommit = false

                persistOrganizationAndTrace(connection, fixture)
                persistCase(connection, fixture, 1L)
                persistLineage(
                    connection,
                    fixture,
                    1L,
                    "b".repeat(64)
                )

                connection.commit()

                assertFailsWith<SQLException> {
                    connection.prepareStatement(
                        """
                        UPDATE marketplace_reconciliation_case_revision_assessment
                           SET accepted_at=now()
                         WHERE organization_id=?
                           AND case_id=?
                           AND case_revision=1
                        """.trimIndent()
                    ).use { statement ->
                        statement.setObject(1, fixture.organizationId)
                        statement.setObject(2, fixture.caseId)
                        statement.executeUpdate()
                    }
                }

                connection.rollback()

                assertFailsWith<SQLException> {
                    connection.prepareStatement(
                        """
                        DELETE FROM marketplace_reconciliation_case_revision_assessment
                         WHERE organization_id=?
                           AND case_id=?
                           AND case_revision=1
                        """.trimIndent()
                    ).use { statement ->
                        statement.setObject(1, fixture.organizationId)
                        statement.setObject(2, fixture.caseId)
                        statement.executeUpdate()
                    }
                }
            }
        }
    }

    @Test
    fun `future or mismatched lineage revision fails at transaction commit`() {
        PostgreSQLContainer("postgres:18.4").use { pg ->
            pg.start()
            val configuration =
                migratedConfiguration(pg)

            val fixture = fixture()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                connection.autoCommit = false

                persistOrganizationAndTrace(connection, fixture)
                persistCase(connection, fixture, 1L)

                persistLineage(
                    connection,
                    fixture,
                    revision = 2L,
                    fingerprint = "c".repeat(64)
                )

                assertFailsWith<SQLException> {
                    connection.commit()
                }

                connection.rollback()
            }
        }
    }

    private fun migratedConfiguration(
        pg: PostgreSQLContainer
    ): PostgresConfiguration {
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

        return configuration
    }

    private fun persistOrganizationAndTrace(
        connection: Connection,
        fixture: Fixture
    ) {
        connection.prepareStatement(
            """
            INSERT INTO integration_organization
                (organization_id,status,created_at,updated_at)
            VALUES (?,'ACTIVE',now(),now())
            """.trimIndent()
        ).use { statement ->
            statement.setObject(1, fixture.organizationId)
            statement.executeUpdate()
        }

        connection.prepareStatement(
            """
            INSERT INTO marketplace_financial_trace
                (
                    organization_id,
                    trace_id,
                    open_request_id,
                    order_id,
                    marketplace_key,
                    external_order_id,
                    currency
                )
            VALUES (?,?,?,?,?,?,?)
            """.trimIndent()
        ).use { statement ->
            statement.setObject(1, fixture.organizationId)
            statement.setObject(2, fixture.traceId)
            statement.setObject(3, UUID.randomUUID())
            statement.setObject(4, fixture.orderId)
            statement.setString(5, "mercado-livre")
            statement.setString(6, "MLB-ORDER-1")
            statement.setString(7, "BRL")
            statement.executeUpdate()
        }
    }

    private fun persistCase(
        connection: Connection,
        fixture: Fixture,
        revision: Long
    ) {
        connection.prepareStatement(
            """
            INSERT INTO marketplace_reconciliation_case
                (
                    organization_id,
                    case_id,
                    marketplace_order_id,
                    financial_trace_id,
                    policy_version,
                    currency,
                    status,
                    opened_at,
                    last_observed_at,
                    resolved_at,
                    revision,
                    absolute_difference_summary,
                    stage_details,
                    evidence_entry_ids
                )
            VALUES
                (?,?,?,?,?,'BRL','OPEN',?,?,NULL,?,10,'[]'::jsonb,'[]'::jsonb)
            """.trimIndent()
        ).use { statement ->
            statement.setObject(1, fixture.organizationId)
            statement.setObject(2, fixture.caseId)
            statement.setObject(3, fixture.orderId)
            statement.setObject(4, fixture.traceId)
            statement.setString(5, "financial/1")
            statement.setTimestamp(
                6,
                Timestamp.from(fixture.acceptedAt)
            )
            statement.setTimestamp(
                7,
                Timestamp.from(fixture.acceptedAt)
            )
            statement.setLong(8, revision)
            statement.executeUpdate()
        }
    }

    private fun persistLineage(
        connection: Connection,
        fixture: Fixture,
        revision: Long,
        fingerprint: String
    ) {
        connection.prepareStatement(
            """
            INSERT INTO marketplace_reconciliation_case_revision_assessment
                (
                    organization_id,
                    case_id,
                    case_revision,
                    assessment_fingerprint_version,
                    assessment_fingerprint,
                    assessment_snapshot_schema_version,
                    assessment_snapshot,
                    accepted_at
                )
            VALUES
                (?,?,?,1,?,1,?::jsonb,?)
            """.trimIndent()
        ).use { statement ->
            statement.setObject(1, fixture.organizationId)
            statement.setObject(2, fixture.caseId)
            statement.setLong(3, revision)
            statement.setString(4, fingerprint)
            statement.setString(
                5,
                """{"schemaVersion":1}"""
            )
            statement.setTimestamp(
                6,
                Timestamp.from(fixture.acceptedAt)
            )
            statement.executeUpdate()
        }
    }

    private fun scalarLong(
        connection: Connection,
        sql: String,
        first: UUID,
        second: UUID
    ): Long =
        connection.prepareStatement(sql).use { statement ->
            statement.setObject(1, first)
            statement.setObject(2, second)
            statement.executeQuery().use { result ->
                check(result.next())
                result.getLong(1)
            }
        }

    private fun fixture(): Fixture =
        Fixture(
            organizationId =
                UUID.fromString(
                    "10000000-0000-0000-0000-000000000001"
                ),
            caseId =
                UUID.fromString(
                    "40000000-0000-0000-0000-000000000001"
                ),
            orderId =
                UUID.fromString(
                    "30000000-0000-0000-0000-000000000001"
                ),
            traceId =
                UUID.fromString(
                    "20000000-0000-0000-0000-000000000001"
                ),
            acceptedAt =
                Instant.parse(
                    "2026-09-13T18:00:00.123456Z"
                )
        )

    private data class Fixture(
        val organizationId: UUID,
        val caseId: UUID,
        val orderId: UUID,
        val traceId: UUID,
        val acceptedAt: Instant
    )
}
