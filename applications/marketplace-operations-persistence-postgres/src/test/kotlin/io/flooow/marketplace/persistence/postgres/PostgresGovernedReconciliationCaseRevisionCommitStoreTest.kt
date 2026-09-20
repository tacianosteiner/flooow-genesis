package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.reconciliation.AcceptedFinancialReconciliationAssessment
import io.flooow.marketplace.operations.economics.reconciliation.DurableReconciliationCase
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessment
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentFingerprinter
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentSnapshot
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationAssessmentSnapshotCodec
import io.flooow.marketplace.operations.economics.reconciliation.GovernedReconciliationCaseCommitFailure
import io.flooow.marketplace.operations.economics.reconciliation.GovernedReconciliationCaseCommitResult
import io.flooow.marketplace.operations.economics.reconciliation.GovernedReconciliationCaseRevisionCommit
import java.sql.Connection
import java.sql.DriverManager
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.flywaydb.core.api.MigrationVersion
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresGovernedReconciliationCaseRevisionCommitStoreTest {
    private val currency =
        MarketplaceCurrency("BRL")

    private val acceptedAt1 =
        Instant.parse(
            "2026-09-13T18:00:00.123456Z"
        )

    private val acceptedAt2 =
        Instant.parse(
            "2026-09-13T18:01:00.123456Z"
        )

    private val acceptedAt3 =
        Instant.parse(
            "2026-09-13T18:02:00.123456Z"
        )

    @Test
    fun `connection acquisition failure is unavailable and never escapes`() {
        val fixture =
            fixture()

        val command =
            command(
                assessment =
                    assessment(
                        fixture,
                        saleActual = "110"
                    ),
                acceptedAt = acceptedAt1,
                revision = 1L,
                openedAt = acceptedAt1
            )

        val store =
            PostgresGovernedReconciliationCaseRevisionCommitStore(
                PostgresConfiguration(
                    url = "jdbc:postgresql://127.0.0.1:1/flooow_unavailable?connectTimeout=1&socketTimeout=1",
                    user = "none",
                    password = "none"
                )
            )

        assertEquals(
            GovernedReconciliationCaseCommitResult.Failed(
                GovernedReconciliationCaseCommitFailure.UNAVAILABLE
            ),
            store.commit(command)
        )
    }

    @Test
    fun `new revision is applied atomically and exact retry is already applied`() {
        withMigratedDatabase { configuration, fixture ->
            val store =
                PostgresGovernedReconciliationCaseRevisionCommitStore(
                    configuration
                )

            val assessment =
                assessment(
                    fixture,
                    saleActual = "110",
                    taxExpected = "5"
                )

            val command =
                command(
                    assessment = assessment,
                    acceptedAt = acceptedAt1,
                    revision = 1L,
                    openedAt = acceptedAt1
                )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    1L
                ),
                store.commit(command)
            )

            assertEquals(
                GovernedReconciliationCaseCommitResult.AlreadyApplied(
                    1L
                ),
                store.commit(command)
            )

            assertEquals(
                1L,
                lineageCount(
                    configuration,
                    fixture
                )
            )

            assertEquals(
                1L,
                currentRevision(
                    configuration,
                    fixture
                )
            )
        }
    }

    @Test
    fun `changed non divergent assessment content advances revision even when case projection is unchanged`() {
        withMigratedDatabase { configuration, fixture ->
            val store =
                PostgresGovernedReconciliationCaseRevisionCommitStore(
                    configuration
                )

            val firstAssessment =
                assessment(
                    fixture,
                    saleActual = "110",
                    taxExpected = "5"
                )

            val secondAssessment =
                assessment(
                    fixture,
                    saleActual = "110",
                    taxExpected = "6"
                )

            val first =
                command(
                    assessment = firstAssessment,
                    acceptedAt = acceptedAt1,
                    revision = 1L,
                    openedAt = acceptedAt1
                )

            val second =
                command(
                    assessment = secondAssessment,
                    acceptedAt = acceptedAt2,
                    revision = 2L,
                    openedAt = acceptedAt1
                )

            assertEquals(
                first.caseValue.absoluteDifferenceSummary,
                second.caseValue.absoluteDifferenceSummary
            )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    1L
                ),
                store.commit(first)
            )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    2L
                ),
                store.commit(second)
            )

            assertEquals(
                2L,
                currentRevision(
                    configuration,
                    fixture
                )
            )

            assertEquals(
                2L,
                lineageCount(
                    configuration,
                    fixture
                )
            )
        }
    }

    @Test
    fun `stale or skipped revision is conflict and does not mutate durable state`() {
        withMigratedDatabase { configuration, fixture ->
            val store =
                PostgresGovernedReconciliationCaseRevisionCommitStore(
                    configuration
                )

            val first =
                command(
                    assessment =
                        assessment(
                            fixture,
                            saleActual = "110"
                        ),
                    acceptedAt = acceptedAt1,
                    revision = 1L,
                    openedAt = acceptedAt1
                )

            val skipped =
                command(
                    assessment =
                        assessment(
                            fixture,
                            saleActual = "120"
                        ),
                    acceptedAt = acceptedAt2,
                    revision = 3L,
                    openedAt = acceptedAt1
                )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    1L
                ),
                store.commit(first)
            )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Failed(
                    GovernedReconciliationCaseCommitFailure.CONFLICT
                ),
                store.commit(skipped)
            )

            assertEquals(
                1L,
                currentRevision(
                    configuration,
                    fixture
                )
            )

            assertEquals(
                1L,
                lineageCount(
                    configuration,
                    fixture
                )
            )
        }
    }

    @Test
    fun `assessment identity may validly return A to B to A across distinct revisions`() {
        withMigratedDatabase { configuration, fixture ->
            val store =
                PostgresGovernedReconciliationCaseRevisionCommitStore(
                    configuration
                )

            val assessmentA =
                assessment(
                    fixture,
                    saleActual = "110"
                )

            val assessmentB =
                assessment(
                    fixture,
                    saleActual = "120"
                )

            val a1 =
                command(
                    assessmentA,
                    acceptedAt1,
                    1L,
                    acceptedAt1
                )

            val b2 =
                command(
                    assessmentB,
                    acceptedAt2,
                    2L,
                    acceptedAt1
                )

            val a3 =
                command(
                    assessmentA,
                    acceptedAt3,
                    3L,
                    acceptedAt1
                )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    1L
                ),
                store.commit(a1)
            )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    2L
                ),
                store.commit(b2)
            )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    3L
                ),
                store.commit(a3)
            )

            val fingerprints =
                fingerprintsByRevision(
                    configuration,
                    fixture
                )

            assertEquals(
                3,
                fingerprints.size
            )

            assertEquals(
                fingerprints.getValue(1L),
                fingerprints.getValue(3L)
            )

            assertTrue(
                fingerprints.getValue(1L) !=
                    fingerprints.getValue(2L)
            )
        }
    }

    @Test
    fun `legacy current revision without lineage advances to first verified N plus 1`() {
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

            migrate(
                configuration,
                target = "29"
            )

            val fixture = fixture()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                seedOrganizationAndTrace(
                    connection,
                    fixture
                )

                persistLegacyCase(
                    connection,
                    fixture,
                    revision = 7L,
                    openedAt =
                        Instant.parse(
                            "2026-09-13T17:00:00.123456Z"
                        )
                )
            }

            migrate(configuration)

            val store =
                PostgresGovernedReconciliationCaseRevisionCommitStore(
                    configuration
                )

            val acceptedAt =
                Instant.parse(
                    "2026-09-13T18:10:00.123456Z"
                )

            val command =
                command(
                    assessment =
                        assessment(
                            fixture,
                            saleActual = "110"
                        ),
                    acceptedAt = acceptedAt,
                    revision = 8L,
                    openedAt =
                        Instant.parse(
                            "2026-09-13T17:00:00.123456Z"
                        )
                )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    8L
                ),
                store.commit(command)
            )

            assertEquals(
                8L,
                currentRevision(
                    configuration,
                    fixture
                )
            )

            assertEquals(
                1L,
                lineageCount(
                    configuration,
                    fixture
                )
            )
        }
    }

    @Test
    fun `verified lineage is checked before idempotence and durable tampering is integrity failure`() {
        withMigratedDatabase { configuration, fixture ->
            val store =
                PostgresGovernedReconciliationCaseRevisionCommitStore(
                    configuration
                )

            val assessmentA =
                assessment(
                    fixture,
                    saleActual = "110"
                )

            val assessmentB =
                assessment(
                    fixture,
                    saleActual = "120"
                )

            val commandA =
                command(
                    assessmentA,
                    acceptedAt1,
                    1L,
                    acceptedAt1
                )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Applied(
                    1L
                ),
                store.commit(commandA)
            )

            tamperCurrentLineage(
                configuration,
                fixture,
                assessmentB
            )

            assertEquals(
                GovernedReconciliationCaseCommitResult.Failed(
                    GovernedReconciliationCaseCommitFailure.INTEGRITY_FAILURE
                ),
                store.commit(commandA)
            )
        }
    }

    @Test
    fun `concurrent identical first commit yields one applied and one already applied`() {
        withMigratedDatabase { configuration, fixture ->
            val store =
                PostgresGovernedReconciliationCaseRevisionCommitStore(
                    configuration
                )

            val command =
                command(
                    assessment =
                        assessment(
                            fixture,
                            saleActual = "110"
                        ),
                    acceptedAt = acceptedAt1,
                    revision = 1L,
                    openedAt = acceptedAt1
                )

            val start =
                CountDownLatch(1)

            val executor =
                Executors.newFixedThreadPool(2)

            try {
                val first =
                    executor.submit<GovernedReconciliationCaseCommitResult> {
                        start.await()
                        store.commit(command)
                    }

                val second =
                    executor.submit<GovernedReconciliationCaseCommitResult> {
                        start.await()
                        store.commit(command)
                    }

                start.countDown()

                val results =
                    listOf(
                        first.get(),
                        second.get()
                    )

                assertEquals(
                    1,
                    results.count {
                        it ==
                            GovernedReconciliationCaseCommitResult.Applied(
                                1L
                            )
                    }
                )

                assertEquals(
                    1,
                    results.count {
                        it ==
                            GovernedReconciliationCaseCommitResult.AlreadyApplied(
                                1L
                            )
                    }
                )

                assertEquals(
                    1L,
                    lineageCount(
                        configuration,
                        fixture
                    )
                )
            } finally {
                executor.shutdownNow()
            }
        }
    }

    private fun command(
        assessment: FinancialReconciliationAssessment,
        acceptedAt: Instant,
        revision: Long,
        openedAt: Instant
    ): GovernedReconciliationCaseRevisionCommit {
        val accepted =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment,
                acceptedAt
            )

        val value =
            DurableReconciliationCase.fromAssessment(
                caseId =
                    DurableReconciliationCase.deterministicId(
                        assessment
                    ),
                assessment = assessment,
                openedAt = openedAt,
                observedAt = acceptedAt,
                revision = revision
            )

        return GovernedReconciliationCaseRevisionCommit.create(
            value,
            accepted
        )
    }

    private fun assessment(
        fixture: Fixture,
        saleActual: String,
        taxExpected: String = "5"
    ): FinancialReconciliationAssessment {
        val signedValue =
            saleActual.toBigDecimal() -
                "100".toBigDecimal()

        val signedDifference =
            if (signedValue.signum() == 0) {
                "0"
            } else {
                signedValue.stripTrailingZeros().toPlainString()
            }

        val absoluteValue =
            signedValue.abs()

        val absoluteDifference =
            if (absoluteValue.signum() == 0) {
                "0"
            } else {
                absoluteValue.stripTrailingZeros().toPlainString()
            }

        /*
         * Persistence-module tests must not bypass the domain by invoking
         * internal reconciliation constructors.
         *
         * Snapshot-v1 parsing is a public domain-owned, strict rehydration
         * boundary. Authority is still established later by
         * AcceptedFinancialReconciliationAssessment.accept(...).
         */
        val payload =
            """
            {
              "schemaVersion": 1,
              "organizationId": "${fixture.organizationId}",
              "traceId": "${fixture.traceId}",
              "orderId": "${fixture.orderId}",
              "currency": "BRL",
              "policyVersion": "financial/1",
              "status": "DIVERGENCE",
              "lines": [
                {
                  "stage": "SALE",
                  "status": "DIVERGENCE",
                  "expected": {
                    "kind": "OBSERVED",
                    "netAmount": {
                      "currency": "BRL",
                      "amount": "100"
                    },
                    "effectiveEntryIds": [
                      "70000000-0000-0000-0000-000000000001"
                    ]
                  },
                  "actual": {
                    "kind": "OBSERVED",
                    "netAmount": {
                      "currency": "BRL",
                      "amount": "$saleActual"
                    },
                    "effectiveEntryIds": [
                      "70000000-0000-0000-0000-000000000002"
                    ]
                  },
                  "difference": {
                    "kind": "COMPARED",
                    "signedDifference": {
                      "currency": "BRL",
                      "amount": "$signedDifference"
                    },
                    "absoluteDifference": {
                      "currency": "BRL",
                      "amount": "$absoluteDifference"
                    },
                    "tolerance": {
                      "currency": "BRL",
                      "amount": "0.01"
                    }
                  }
                },
                {
                  "stage": "TAX",
                  "status": "PENDING",
                  "expected": {
                    "kind": "OBSERVED",
                    "netAmount": {
                      "currency": "BRL",
                      "amount": "$taxExpected"
                    },
                    "effectiveEntryIds": [
                      "70000000-0000-0000-0000-000000000003"
                    ]
                  },
                  "actual": {
                    "kind": "NOT_OBSERVED"
                  },
                  "difference": {
                    "kind": "NOT_COMPARABLE"
                  }
                }
              ]
            }
            """.trimIndent()

        val snapshot =
            FinancialReconciliationAssessmentSnapshot.parse(
                persistedSchemaVersion = 1,
                json = payload
            )

        return FinancialReconciliationAssessmentSnapshotCodec
            .rehydrate(snapshot)
            .assessment
    }

    private fun withMigratedDatabase(
        block: (
            PostgresConfiguration,
            Fixture
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

            migrate(configuration)

            val fixture =
                fixture()

            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                seedOrganizationAndTrace(
                    connection,
                    fixture
                )
            }

            block(
                configuration,
                fixture
            )
        }
    }

    private fun migrate(
        configuration: PostgresConfiguration,
        target: String? = null
    ) {
        val builder =
            Flyway.configure()
                .dataSource(
                    configuration.url,
                    configuration.user,
                    configuration.password
                )

        if (target != null) {
            builder.target(
                MigrationVersion.fromVersion(
                    target
                )
            )
        }

        builder.load().migrate()
    }

    private fun seedOrganizationAndTrace(
        connection: Connection,
        fixture: Fixture
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
            VALUES
                (?,'ACTIVE',now(),now())
            """.trimIndent()
        ).use { statement ->
            statement.setObject(
                1,
                fixture.organizationId
            )
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
            VALUES
                (?,?,?,?,?,?,?)
            """.trimIndent()
        ).use { statement ->
            statement.setObject(
                1,
                fixture.organizationId
            )
            statement.setObject(
                2,
                fixture.traceId
            )
            statement.setObject(
                3,
                UUID.randomUUID()
            )
            statement.setObject(
                4,
                fixture.orderId
            )
            statement.setString(
                5,
                "mercado-livre"
            )
            statement.setString(
                6,
                "MLB-ORDER-0165P"
            )
            statement.setString(
                7,
                "BRL"
            )
            statement.executeUpdate()
        }
    }

    private fun persistLegacyCase(
        connection: Connection,
        fixture: Fixture,
        revision: Long,
        openedAt: Instant
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
                (
                    ?,?,?,?,?,'BRL','OPEN',
                    ?,?,NULL,?,10,
                    '[]'::jsonb,
                    '[]'::jsonb
                )
            """.trimIndent()
        ).use { statement ->
            val assessment =
                assessment(
                    fixture,
                    saleActual = "110"
                )

            statement.setObject(
                1,
                fixture.organizationId
            )
            statement.setObject(
                2,
                DurableReconciliationCase
                    .deterministicId(
                        assessment
                    )
                    .valueForPersistence()
            )
            statement.setObject(
                3,
                fixture.orderId
            )
            statement.setObject(
                4,
                fixture.traceId
            )
            statement.setString(
                5,
                "financial/1"
            )
            statement.setTimestamp(
                6,
                Timestamp.from(openedAt)
            )
            statement.setTimestamp(
                7,
                Timestamp.from(openedAt)
            )
            statement.setLong(
                8,
                revision
            )
            statement.executeUpdate()
        }
    }

    private fun tamperCurrentLineage(
        configuration: PostgresConfiguration,
        fixture: Fixture,
        replacementAssessment: FinancialReconciliationAssessment
    ) {
        val fingerprint =
            FinancialReconciliationAssessmentFingerprinter
                .fingerprint(
                    replacementAssessment
                )

        val snapshot =
            FinancialReconciliationAssessmentSnapshot
                .capture(
                    replacementAssessment
                )

        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            connection.createStatement().use {
                it.execute(
                    """
                    ALTER TABLE
                        marketplace_reconciliation_case_revision_assessment
                    DISABLE TRIGGER USER
                    """.trimIndent()
                )
            }

            connection.prepareStatement(
                """
                UPDATE marketplace_reconciliation_case_revision_assessment
                   SET assessment_fingerprint=?,
                       assessment_snapshot=?::jsonb
                 WHERE organization_id=?
                   AND case_id=?
                   AND case_revision=1
                """.trimIndent()
            ).use { statement ->
                statement.setString(
                    1,
                    fingerprint.sha256
                )
                statement.setString(
                    2,
                    snapshot.json
                )
                statement.setObject(
                    3,
                    fixture.organizationId
                )
                statement.setObject(
                    4,
                    DurableReconciliationCase
                        .deterministicId(
                            replacementAssessment
                        )
                        .valueForPersistence()
                )
                assertEquals(
                    1,
                    statement.executeUpdate()
                )
            }

            connection.createStatement().use {
                it.execute(
                    """
                    ALTER TABLE
                        marketplace_reconciliation_case_revision_assessment
                    ENABLE TRIGGER USER
                    """.trimIndent()
                )
            }
        }
    }

    private fun currentRevision(
        configuration: PostgresConfiguration,
        fixture: Fixture
    ): Long =
        scalarLong(
            configuration,
            """
            SELECT revision
              FROM marketplace_reconciliation_case
             WHERE organization_id=?
               AND financial_trace_id=?
               AND policy_version='financial/1'
            """.trimIndent(),
            fixture.organizationId,
            fixture.traceId
        )

    private fun lineageCount(
        configuration: PostgresConfiguration,
        fixture: Fixture
    ): Long =
        scalarLong(
            configuration,
            """
            SELECT count(*)
              FROM marketplace_reconciliation_case_revision_assessment
             WHERE organization_id=?
               AND case_id=(
                    SELECT case_id
                      FROM marketplace_reconciliation_case
                     WHERE organization_id=?
                       AND financial_trace_id=?
                       AND policy_version='financial/1'
               )
            """.trimIndent(),
            fixture.organizationId,
            fixture.organizationId,
            fixture.traceId
        )

    private fun fingerprintsByRevision(
        configuration: PostgresConfiguration,
        fixture: Fixture
    ): Map<Long, String> =
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            connection.prepareStatement(
                """
                SELECT
                    case_revision,
                    assessment_fingerprint
                  FROM marketplace_reconciliation_case_revision_assessment
                 WHERE organization_id=?
                 ORDER BY case_revision
                """.trimIndent()
            ).use { statement ->
                statement.setObject(
                    1,
                    fixture.organizationId
                )

                statement.executeQuery().use { result ->
                    buildMap {
                        while (result.next()) {
                            put(
                                result.getLong(
                                    "case_revision"
                                ),
                                result.getString(
                                    "assessment_fingerprint"
                                )
                            )
                        }
                    }
                }
            }
        }

    private fun scalarLong(
        configuration: PostgresConfiguration,
        sql: String,
        vararg values: UUID
    ): Long =
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            connection.prepareStatement(
                sql
            ).use { statement ->
                values.forEachIndexed { index, value ->
                    statement.setObject(
                        index + 1,
                        value
                    )
                }

                statement.executeQuery().use { result ->
                    check(result.next())
                    result.getLong(1)
                }
            }
        }

    private fun fixture(): Fixture =
        Fixture(
            organizationId =
                UUID.fromString(
                    "10000000-0000-0000-0000-000000000001"
                ),
            traceId =
                UUID.fromString(
                    "20000000-0000-0000-0000-000000000001"
                ),
            orderId =
                UUID.fromString(
                    "30000000-0000-0000-0000-000000000001"
                )
        )

    private fun money(
        value: String
    ): MarketplaceMoney =
        MarketplaceMoney.parse(
            currency,
            value
        )

    private data class Fixture(
        val organizationId: UUID,
        val traceId: UUID,
        val orderId: UUID
    )
}
