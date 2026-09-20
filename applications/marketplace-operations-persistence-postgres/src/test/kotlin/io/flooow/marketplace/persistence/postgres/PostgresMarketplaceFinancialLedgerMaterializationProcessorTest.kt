package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.ledger.*
import io.flooow.marketplace.operations.economics.ledger.materialization.*
import io.flooow.organization.OrganizationId
import java.sql.DriverManager
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import kotlin.test.*
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresMarketplaceFinancialLedgerMaterializationProcessorTest {

    private lateinit var postgres: PostgreSQLContainer
    private lateinit var configuration: PostgresConfiguration

    @BeforeTest
    fun start() {
        postgres =
            PostgreSQLContainer("postgres:18.4")
                .also { it.start() }

        configuration =
            PostgresConfiguration(
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
    fun stop() {
        postgres.stop()
    }

    @Test
    fun `real postgres processor materializes exact historical update while aggregate is ahead`() {
        val organization =
            OrganizationId.parse(
                "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
            )

        insertOrganization(organization)

        val observation =
            observation(
                organization = organization,
                order = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                observationId = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
            )

        val evidence =
            PostgresMarketplaceIndependentEconomicEvidenceRepository(
                configuration
            )

        val first =
            evidence.apply(
                MarketplaceEconomicEvidenceVersion.ZERO,
                MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                    MarketplaceIndependentEconomicFact.Component(
                        observation
                    )
                )
            )

        assertIs<
            MarketplaceIndependentEconomicEvidencePersistResult.Applied
        >(first)

        val attempt =
            MarketplaceEconomicEvidenceCollectionAttempt(
                id =
                    MarketplaceEconomicEvidenceObservationId.parse(
                        "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
                    ),
                subject = observation.subject,
                family = MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
                sourceSystemKey =
                    EconomicSourceSystemKey("br.com.mercadolivre"),
                outcome =
                    MarketplaceEconomicEvidenceAttemptOutcome.NO_EVIDENCE,
                attemptedAt =
                    Instant.parse(
                        "2026-09-20T12:02:00.000001Z"
                    )
            )

        val second =
            evidence.apply(
                MarketplaceEconomicEvidenceVersion(1),
                MarketplaceIndependentEconomicEvidenceUpdate.RecordAttempt(
                    attempt
                )
            )

        assertIs<
            MarketplaceIndependentEconomicEvidencePersistResult.Applied
        >(second)

        val current =
            assertIs<
                MarketplaceIndependentEconomicEvidenceReadResult.Found
            >(
                evidence.find(observation.subject)
            )

        assertEquals(
            MarketplaceEconomicEvidenceVersion(2),
            current.versionedEvidence.version
        )

        val feed =
            PostgresMarketplaceEconomicEvidenceChangeFeed(
                configuration
            )

        val initialCheckpoint =
            assertIs<
                MarketplaceEconomicEvidenceChangeFeedResult.Success<
                    ChangeSequenceCheckpoint
                >
            >(
                feed.currentCheckpoint(
                    organization,
                    MarketplaceFinancialLedgerMaterializationProcessor
                        .PROJECTION_NAME
                )
            ).value

        assertEquals(
            ChangeSequenceCheckpoint.NONE,
            initialCheckpoint
        )

        val pending =
            assertIs<
                MarketplaceEconomicEvidenceChangeFeedResult.Success<
                    List<MarketplaceEconomicEvidenceChange>
                >
            >(
                feed.changesSince(
                    organization,
                    ChangeSequenceCheckpoint.NONE,
                    10
                )
            ).value

        assertEquals(2, pending.size)

        val firstChange = pending[0]
        val secondChange = pending[1]

        assertEquals(
            MarketplaceEconomicEvidenceChangeKind.FACT,
            firstChange.changeKind
        )

        assertEquals(
            observation.id,
            firstChange.updateId
        )

        assertEquals(
            MarketplaceEconomicEvidenceVersion(1),
            firstChange.evidenceVersion
        )

        assertEquals(
            MarketplaceEconomicEvidenceChangeKind.ATTEMPT,
            secondChange.changeKind
        )

        val store =
            PostgresGovernedFinancialLedgerMaterializationCommitStore(
                configuration
            )

        val processor =
            MarketplaceFinancialLedgerMaterializationProcessor(
                updateReader = evidence,
                changeFeed = feed,
                authorityResolver = { org, source ->
                    assertEquals(organization, org)
                    assertEquals(observation, source)

                    FinancialLedgerComponentMaterializationAuthorityDecision
                        .Authorized(
                            source.id,
                            FinancialLedgerSourceAuthoritySemanticVersion(
                                "slice-b-postgres-test/1"
                            ),
                            FinancialLedgerMaterializationPolicyVersion.V1,
                            FinancialLedgerMaterializationSourceFingerprintV1
                                .fingerprint(source),
                            FinancialLedgerBasis.ACTUAL
                        )
                },
                commitStore = store
            )

        /*
         * limit=1 is intentional.
         *
         * Durable aggregate is already version 2, but processor must consume
         * the exact version-1 FACT identified by the first change.
         */
        val materialized =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .Success
            >(
                processor.processBatch(
                    organization,
                    1
                )
            )

        assertEquals(1, materialized.processedChanges)
        assertEquals(1, materialized.materialized)
        assertEquals(0, materialized.alreadyMaterialized)
        assertEquals(0, materialized.notEligible)
        assertEquals(
            firstChange.changeSequence,
            materialized.checkpoint
        )

        val ledger =
            PostgresMarketplaceFinancialLedgerRepository(
                configuration
            )

        val trace =
            assertIs<FinancialTraceReadResult.Found>(
                ledger.findByOrder(
                    organization,
                    observation.subject.orderId
                )
            ).trace

        assertEquals(1, trace.entries.size)

        val entry = trace.entries.single()

        assertEquals(FinancialLedgerBasis.ACTUAL, entry.basis)
        assertEquals(FinancialLedgerStage.SALE, entry.stage)
        assertEquals(
            observation.component.direction,
            entry.direction
        )
        assertEquals(
            observation.component.magnitude,
            entry.magnitude
        )
        assertEquals(
            observation.component.source,
            entry.source
        )
        assertEquals(
            observation.component.occurredAt,
            entry.occurredAt
        )
        assertNull(entry.correctsEntryId)

        assertEquals(
            1,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_entry
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )

        assertEquals(
            1,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_materialization_lineage
                WHERE organization_id=?
                  AND source_order_id=?
                  AND source_authority_identity=?
                """.trimIndent(),
                organization.value,
                observation.subject.orderId.value,
                observation.id.valueForPersistence()
            )
        )

        val lineage =
            lineage(
                organization,
                observation
            )

        assertEquals(
            1,
            lineage.canonicalizationVersion
        )
        assertEquals(
            FinancialLedgerMaterializationSourceFingerprintV1
                .fingerprint(observation)
                .sha256,
            lineage.fingerprint
        )
        assertEquals(
            "slice-b-postgres-test/1",
            lineage.semanticVersion
        )
        assertEquals(
            "marketplace-financial-ledger-materialization/1",
            lineage.policyVersion
        )
        assertEquals("SALE", lineage.stage)
        assertEquals("ACTUAL", lineage.basis)
        assertEquals(trace.id, lineage.traceId)
        assertEquals(entry.id, lineage.entryId)

        /*
         * Next real change is ATTEMPT.
         * It must advance the dedicated ledger-materializer checkpoint
         * without ledger mutation.
         */
        val attemptResult =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .Success
            >(
                processor.processBatch(
                    organization,
                    1
                )
            )

        assertEquals(1, attemptResult.processedChanges)
        assertEquals(0, attemptResult.materialized)
        assertEquals(0, attemptResult.alreadyMaterialized)
        assertEquals(
            secondChange.changeSequence,
            attemptResult.checkpoint
        )

        assertEquals(
            1,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_entry
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )

        assertEquals(
            1,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_materialization_lineage
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )

        /*
         * Restart/new processor instance over the same durable DB.
         * Checkpoint prevents duplicate effects.
         */
        val restarted =
            MarketplaceFinancialLedgerMaterializationProcessor(
                updateReader = evidence,
                changeFeed = feed,
                authorityResolver = { _, source ->
                    FinancialLedgerComponentMaterializationAuthorityDecision
                        .Authorized(
                            source.id,
                            FinancialLedgerSourceAuthoritySemanticVersion(
                                "slice-b-postgres-test/1"
                            ),
                            FinancialLedgerMaterializationPolicyVersion.V1,
                            FinancialLedgerMaterializationSourceFingerprintV1
                                .fingerprint(source),
                            FinancialLedgerBasis.ACTUAL
                        )
                },
                commitStore =
                    PostgresGovernedFinancialLedgerMaterializationCommitStore(
                        configuration
                    )
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.NoChanges
        >(
            restarted.processBatch(
                organization,
                10
            )
        )

        assertEquals(
            1,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_entry
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )

        assertEquals(
            1,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_materialization_lineage
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )
    }

    @Test
    fun `authority unavailable fails closed without ledger lineage or checkpoint advance`() {
        val organization =
            OrganizationId.parse(
                "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
            )

        insertOrganization(organization)

        val observation =
            observation(
                organization,
                "ffffffff-ffff-4fff-8fff-ffffffffffff",
                "11111111-1111-4111-8111-111111111111"
            )

        val evidence =
            PostgresMarketplaceIndependentEconomicEvidenceRepository(
                configuration
            )

        assertIs<
            MarketplaceIndependentEconomicEvidencePersistResult.Applied
        >(
            evidence.apply(
                MarketplaceEconomicEvidenceVersion.ZERO,
                MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                    MarketplaceIndependentEconomicFact.Component(
                        observation
                    )
                )
            )
        )

        val feed =
            PostgresMarketplaceEconomicEvidenceChangeFeed(
                configuration
            )

        val processor =
            MarketplaceFinancialLedgerMaterializationProcessor(
                updateReader = evidence,
                changeFeed = feed,
                authorityResolver = { _, _ ->
                    FinancialLedgerComponentMaterializationAuthorityDecision
                        .Unavailable
                },
                commitStore =
                    PostgresGovernedFinancialLedgerMaterializationCommitStore(
                        configuration
                    )
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.Unavailable
        >(
            processor.processBatch(
                organization,
                10
            )
        )

        assertEquals(
            ChangeSequenceCheckpoint.NONE,
            checkpoint(feed, organization)
        )

        assertEquals(
            0,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_entry
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )

        assertEquals(
            0,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_materialization_lineage
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )
    }

    @Test
    fun `wrong authority fingerprint fails closed without checkpoint crossing`() {
        val organization =
            OrganizationId.parse(
                "22222222-2222-4222-8222-222222222222"
            )

        insertOrganization(organization)

        val observation =
            observation(
                organization,
                "33333333-3333-4333-8333-333333333333",
                "44444444-4444-4444-8444-444444444444"
            )

        val evidence =
            PostgresMarketplaceIndependentEconomicEvidenceRepository(
                configuration
            )

        assertIs<
            MarketplaceIndependentEconomicEvidencePersistResult.Applied
        >(
            evidence.apply(
                MarketplaceEconomicEvidenceVersion.ZERO,
                MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                    MarketplaceIndependentEconomicFact.Component(
                        observation
                    )
                )
            )
        )

        val feed =
            PostgresMarketplaceEconomicEvidenceChangeFeed(
                configuration
            )

        val processor =
            MarketplaceFinancialLedgerMaterializationProcessor(
                updateReader = evidence,
                changeFeed = feed,
                authorityResolver = { _, source ->
                    FinancialLedgerComponentMaterializationAuthorityDecision
                        .Authorized(
                            source.id,
                            FinancialLedgerSourceAuthoritySemanticVersion(
                                "slice-b-postgres-test/1"
                            ),
                            FinancialLedgerMaterializationPolicyVersion.V1,
                            FinancialLedgerMaterializationSourceFingerprintV1
                                .fingerprint(source)
                                .copy(
                                    sha256 = "0".repeat(64)
                                ),
                            FinancialLedgerBasis.ACTUAL
                        )
                },
                commitStore =
                    PostgresGovernedFinancialLedgerMaterializationCommitStore(
                        configuration
                    )
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult
                .IntegrityFailure
        >(
            processor.processBatch(
                organization,
                10
            )
        )

        assertEquals(
            ChangeSequenceCheckpoint.NONE,
            checkpoint(feed, organization)
        )

        assertEquals(
            0,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_entry
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )

        assertEquals(
            0,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_materialization_lineage
                WHERE organization_id=?
                """.trimIndent(),
                organization.value
            )
        )
    }

    @Test
    fun `organization scoped feed cannot materialize another organizations evidence`() {
        val sourceOrganization =
            OrganizationId.parse(
                "55555555-5555-4555-8555-555555555555"
            )

        val otherOrganization =
            OrganizationId.parse(
                "66666666-6666-4666-8666-666666666666"
            )

        insertOrganization(sourceOrganization)
        insertOrganization(otherOrganization)

        val observation =
            observation(
                sourceOrganization,
                "77777777-7777-4777-8777-777777777777",
                "88888888-8888-4888-8888-888888888888"
            )

        val evidence =
            PostgresMarketplaceIndependentEconomicEvidenceRepository(
                configuration
            )

        assertIs<
            MarketplaceIndependentEconomicEvidencePersistResult.Applied
        >(
            evidence.apply(
                MarketplaceEconomicEvidenceVersion.ZERO,
                MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                    MarketplaceIndependentEconomicFact.Component(
                        observation
                    )
                )
            )
        )

        val feed =
            PostgresMarketplaceEconomicEvidenceChangeFeed(
                configuration
            )

        var authorityCalls = 0

        val processor =
            MarketplaceFinancialLedgerMaterializationProcessor(
                updateReader = evidence,
                changeFeed = feed,
                authorityResolver = { _, source ->
                    authorityCalls++

                    FinancialLedgerComponentMaterializationAuthorityDecision
                        .Authorized(
                            source.id,
                            FinancialLedgerSourceAuthoritySemanticVersion(
                                "slice-b-postgres-test/1"
                            ),
                            FinancialLedgerMaterializationPolicyVersion.V1,
                            FinancialLedgerMaterializationSourceFingerprintV1
                                .fingerprint(source),
                            FinancialLedgerBasis.ACTUAL
                        )
                },
                commitStore =
                    PostgresGovernedFinancialLedgerMaterializationCommitStore(
                        configuration
                    )
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.NoChanges
        >(
            processor.processBatch(
                otherOrganization,
                10
            )
        )

        assertEquals(0, authorityCalls)

        assertEquals(
            ChangeSequenceCheckpoint.NONE,
            checkpoint(feed, otherOrganization)
        )

        assertEquals(
            ChangeSequenceCheckpoint.NONE,
            checkpoint(feed, sourceOrganization)
        )

        assertEquals(
            0,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_entry
                """.trimIndent()
            )
        )

        assertEquals(
            0,
            count(
                """
                SELECT count(*)
                FROM marketplace_financial_ledger_materialization_lineage
                """.trimIndent()
            )
        )
    }

    private fun checkpoint(
        feed: PostgresMarketplaceEconomicEvidenceChangeFeed,
        organization: OrganizationId
    ): ChangeSequenceCheckpoint =
        assertIs<
            MarketplaceEconomicEvidenceChangeFeedResult.Success<
                ChangeSequenceCheckpoint
            >
        >(
            feed.currentCheckpoint(
                organization,
                MarketplaceFinancialLedgerMaterializationProcessor
                    .PROJECTION_NAME
            )
        ).value

    private fun observation(
        organization: OrganizationId,
        order: String,
        observationId: String
    ): MarketplaceEconomicComponentObservation {
        val currency = MarketplaceCurrency("BRL")
        val orderId = MarketplaceOrderId.parse(order)

        val subject =
            MarketplaceEconomicEvidenceSubject(
                organizationId = organization,
                orderId = orderId,
                marketplace = MarketplaceKey("mercado-livre"),
                externalOrderId =
                    MarketplaceExternalOrderId("MLB-$order"),
                currency = currency
            )

        val component =
            EconomicComponent(
                organizationId = organization,
                id =
                    EconomicComponentId.parse(
                        UUID.nameUUIDFromBytes(
                            "$observationId-component".toByteArray()
                        ).toString()
                    ),
                orderId = orderId,
                type = EconomicComponentType.REVENUE,
                direction = EconomicDirection.ADDITION,
                magnitude =
                    MarketplaceMoney.parse(
                        currency,
                        "100.00"
                    ),
                source =
                    EconomicSource(
                        EconomicSourceKind.MARKETPLACE,
                        EconomicSourceSystemKey(
                            "br.com.mercadolivre"
                        ),
                        EconomicExternalReferenceState.Present(
                            EconomicExternalReference(
                                "MLB-$order"
                            )
                        )
                    ),
                occurredAt =
                    Instant.parse(
                        "2026-09-20T12:00:00.000001Z"
                    ),
                quality = EconomicEvidenceQuality.CONFIRMED
            )

        return MarketplaceEconomicComponentObservation(
            id =
                MarketplaceEconomicEvidenceObservationId.parse(
                    observationId
                ),
            subject = subject,
            family =
                MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
            component = component,
            coverageClaim = EconomicComponentCoverage.PARTIAL,
            observedAt =
                Instant.parse(
                    "2026-09-20T12:01:00.000001Z"
                )
        )
    }

    private fun insertOrganization(
        organization: OrganizationId
    ) {
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            connection.prepareStatement(
                """
                INSERT INTO integration_organization
                    (organization_id,status,created_at,updated_at)
                VALUES (?,'ACTIVE',?,?)
                """.trimIndent()
            ).use { statement ->
                val now =
                    Timestamp.from(
                        Instant.parse(
                            "2026-09-20T11:00:00Z"
                        )
                    )

                statement.setObject(
                    1,
                    organization.value
                )
                statement.setTimestamp(2, now)
                statement.setTimestamp(3, now)

                assertEquals(
                    1,
                    statement.executeUpdate()
                )
            }
        }
    }

    private fun count(
        sql: String,
        vararg values: Any
    ): Int =
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            connection.prepareStatement(sql).use { statement ->
                values.forEachIndexed { index, value ->
                    statement.setObject(index + 1, value)
                }

                statement.executeQuery().use { result ->
                    check(result.next())
                    result.getInt(1)
                }
            }
        }

    private fun lineage(
        organization: OrganizationId,
        observation: MarketplaceEconomicComponentObservation
    ): Lineage =
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        ).use { connection ->
            connection.prepareStatement(
                """
                SELECT
                    source_fingerprint_canonicalization_version,
                    source_fingerprint_sha256,
                    source_authority_semantic_version,
                    materialization_policy_version,
                    stage,
                    basis,
                    trace_id,
                    ledger_entry_id
                FROM marketplace_financial_ledger_materialization_lineage
                WHERE organization_id=?
                  AND source_order_id=?
                  AND source_authority_identity=?
                """.trimIndent()
            ).use { statement ->
                statement.setObject(
                    1,
                    organization.value
                )
                statement.setObject(
                    2,
                    observation.subject.orderId.value
                )
                statement.setObject(
                    3,
                    observation.id.valueForPersistence()
                )

                statement.executeQuery().use { result ->
                    check(result.next())

                    Lineage(
                        canonicalizationVersion =
                            result.getInt(
                                "source_fingerprint_canonicalization_version"
                            ),
                        fingerprint =
                            result.getString(
                                "source_fingerprint_sha256"
                            ),
                        semanticVersion =
                            result.getString(
                                "source_authority_semantic_version"
                            ),
                        policyVersion =
                            result.getString(
                                "materialization_policy_version"
                            ),
                        stage =
                            result.getString("stage"),
                        basis =
                            result.getString("basis"),
                        traceId =
                            FinancialTraceId.of(
                                result.getObject(
                                    "trace_id",
                                    UUID::class.java
                                )
                            ),
                        entryId =
                            FinancialLedgerEntryId.of(
                                result.getObject(
                                    "ledger_entry_id",
                                    UUID::class.java
                                )
                            )
                    )
                }
            }
        }

    private data class Lineage(
        val canonicalizationVersion: Int,
        val fingerprint: String,
        val semanticVersion: String,
        val policyVersion: String,
        val stage: String,
        val basis: String,
        val traceId: FinancialTraceId,
        val entryId: FinancialLedgerEntryId
    )
}