package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.EconomicComponent
import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentId
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.EconomicExternalReference
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceCorrection
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceCorrectionReason
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceFamily
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceVersion
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidencePersistResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceUpdate
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicFact
import io.flooow.marketplace.operations.economics.evidence.valueForPersistence
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.materialization.FinancialLedgerComponentMaterializationAuthorityDecision
import io.flooow.marketplace.operations.economics.ledger.materialization.FinancialLedgerMaterializationPolicyVersion
import io.flooow.marketplace.operations.economics.ledger.materialization.FinancialLedgerMaterializationSourceFingerprintV1
import io.flooow.marketplace.operations.economics.ledger.materialization.FinancialLedgerSourceAuthoritySemanticVersion
import io.flooow.marketplace.operations.economics.ledger.materialization.GovernedFinancialLedgerComponentMaterializationBoundary
import io.flooow.marketplace.operations.economics.ledger.materialization.GovernedFinancialLedgerComponentMaterializationResult
import io.flooow.marketplace.operations.economics.ledger.materialization.GovernedFinancialLedgerMaterializationCommitFailure
import io.flooow.marketplace.operations.economics.ledger.materialization.GovernedFinancialLedgerMaterializationCommitResult
import io.flooow.marketplace.operations.economics.ledger.materialization.VerifiedFinancialLedgerComponentMaterializationPlan
import io.flooow.organization.OrganizationId
import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Proxy
import java.sql.Connection
import java.sql.Driver
import java.sql.DriverManager
import java.sql.DriverPropertyInfo
import java.sql.SQLException
import java.sql.Timestamp
import java.time.Instant
import java.util.Properties
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.logging.Logger
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNull
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresGovernedFinancialLedgerMaterializationCommitStoreTest {
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
    fun `first commit writes exact trace entry lineage and replay is idempotent`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )
        assertDurableExact(plan, first.traceId.valueForPersistence(), first.entryId.valueForPersistence())

        val replay = assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
            store.commit(plan)
        )
        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)
        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(1, lineageCount(observation))
    }

    @Test
    fun `lineage insert failure rolls back trace entry and lineage as one unit`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        installFailingLineageTrigger()

        val result =
            PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
                .commit(verifiedPlan(observation))

        val failure =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.Failed>(result)
        assertEquals(
            GovernedFinancialLedgerMaterializationCommitFailure.INTEGRITY_FAILURE,
            failure.failure
        )
        assertEquals(0, traceCount(observation))
        assertEquals(0, entryCount(observation))
        assertEquals(0, lineageCount(observation))
    }

    @Test
    fun `semantic replay changes fail closed without creating new durable facts`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        val originalPlan = verifiedPlan(observation)

        val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(originalPlan)
        )

        assertIntegrity(
            store.commit(
                verifiedPlan(
                    observation,
                    basis = FinancialLedgerBasis.ACTUAL
                )
            )
        )
        assertIntegrity(
            store.commit(
                verifiedPlan(
                    observation,
                    semanticVersion = "marketplace-economic-component/2"
                )
            )
        )

        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(1, lineageCount(observation))
        assertDurableExact(
            originalPlan,
            first.traceId.valueForPersistence(),
            first.entryId.valueForPersistence()
        )
    }

    @Test
    fun `durable source payload drift against verified plan fails before mutation`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        tamperSourceMagnitude(observation, "11")

        val result =
            PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
                .commit(plan)

        assertIntegrity(result)
        assertEquals(0, traceCount(observation))
        assertEquals(0, entryCount(observation))
        assertEquals(0, lineageCount(observation))
    }

    @Test
    fun `existing trace with mismatched context fails closed before append`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        insertExistingTrace(
            observation = observation,
            marketplace = "amazon"
        )

        val result =
            PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
                .commit(verifiedPlan(observation))

        assertIntegrity(result)
        assertEquals(1, traceCount(observation))
        assertEquals(0, entryCount(observation))
        assertEquals(0, lineageCount(observation))
    }

    @Test
    fun `unbound exact ledger entry cannot be retrospectively claimed`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val traceId = insertExistingTrace(observation)
        insertExactUnboundEntry(observation, traceId)

        val result =
            PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
                .commit(verifiedPlan(observation))

        assertIntegrity(result)
        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(0, lineageCount(observation))
    }

    @Test
    fun `source authority identity remains scoped by organization and order`() {
        val organizationId = OrganizationId.parse(UUID.randomUUID().toString())
        val sourceId = MarketplaceEconomicEvidenceObservationId.parse(
            UUID.randomUUID().toString()
        )
        val first = observation(
            organizationId = organizationId,
            orderId = MarketplaceOrderId.parse(UUID.randomUUID().toString()),
            observationId = sourceId
        )
        val second = observation(
            organizationId = organizationId,
            orderId = MarketplaceOrderId.parse(UUID.randomUUID().toString()),
            observationId = sourceId
        )

        insertOrganization(organizationId)
        persistObservation(first)
        persistObservation(second)

        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        val firstResult =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
                store.commit(verifiedPlan(first))
            )
        val secondResult =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
                store.commit(verifiedPlan(second))
            )

        check(firstResult.traceId != secondResult.traceId)
        check(firstResult.entryId != secondResult.entryId)
        assertEquals(1, traceCount(first))
        assertEquals(1, traceCount(second))
        assertEquals(1, lineageCount(first))
        assertEquals(1, lineageCount(second))
        assertEquals(2, lineageCountBySource(organizationId, sourceId))
    }

    @Test
    fun `concurrent identical first materialization converges to one durable lineage`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        val ready = CountDownLatch(2)
        val start = CountDownLatch(1)
        val pool = Executors.newFixedThreadPool(2)

        try {
            val futures = (1..2).map {
                pool.submit<GovernedFinancialLedgerMaterializationCommitResult> {
                    ready.countDown()
                    check(start.await(30, TimeUnit.SECONDS))
                    store.commit(plan)
                }
            }

            check(ready.await(30, TimeUnit.SECONDS))
            start.countDown()

            val results = futures.map { it.get(90, TimeUnit.SECONDS) }
            val materialized =
                results.filterIsInstance<GovernedFinancialLedgerMaterializationCommitResult.Materialized>()
            val replay =
                results.filterIsInstance<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>()

            assertEquals(1, materialized.size)
            assertEquals(1, replay.size)
            assertEquals(materialized.single().traceId, replay.single().traceId)
            assertEquals(materialized.single().entryId, replay.single().entryId)
            assertEquals(1, traceCount(observation))
            assertEquals(1, entryCount(observation))
            assertEquals(1, lineageCount(observation))
        } finally {
            start.countDown()
            pool.shutdownNow()
            check(pool.awaitTermination(30, TimeUnit.SECONDS))
        }
    }

    @Test
    fun `commit acknowledgement loss verifies durable lineage before reporting materialized`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val separator = if (configuration.url.contains("?")) "&" else "?"
        val faultUrl =
            "${configuration.url}${separator}b3b2bCommitAckLoss=${UUID.randomUUID()}"
        val driver = CommitAcknowledgementLossDriver(
            acceptedUrl = faultUrl,
            delegateUrl = configuration.url,
            delegateUser = configuration.user,
            delegatePassword = configuration.password
        )

        val driversBefore = buildList<Driver> {
            val drivers = DriverManager.getDrivers()
            while (drivers.hasMoreElements()) {
                add(drivers.nextElement())
            }
        }

        driversBefore.forEach { DriverManager.deregisterDriver(it) }
        DriverManager.registerDriver(driver)
        driversBefore.forEach { DriverManager.registerDriver(it) }

        try {
            val faultConfiguration = PostgresConfiguration(
                faultUrl,
                configuration.user,
                configuration.password
            )
            val result =
                assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
                    PostgresGovernedFinancialLedgerMaterializationCommitStore(
                        faultConfiguration
                    ).commit(plan)
                )

            check(driver.ackLossInjected.get())
            assertDurableExact(
                plan,
                result.traceId.valueForPersistence(),
                result.entryId.valueForPersistence()
            )
            assertEquals(1, traceCount(observation))
            assertEquals(1, entryCount(observation))
            assertEquals(1, lineageCount(observation))

            val replay =
                assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
                    PostgresGovernedFinancialLedgerMaterializationCommitStore(
                        configuration
                    ).commit(plan)
                )
            assertEquals(result.traceId, replay.traceId)
            assertEquals(result.entryId, replay.entryId)
        } finally {
            DriverManager.deregisterDriver(driver)
        }
    }

    @Test
    fun `connection acquisition failure is unavailable and creates no durable facts`() {
        val observation = observation()
        val plan = verifiedPlan(observation)
        val separator = if (configuration.url.contains("?")) "&" else "?"
        val faultUrl =
            "${configuration.url}${separator}b3b2bUnavailable=${UUID.randomUUID()}"
        val driver = AlwaysUnavailableDriver(faultUrl)
        val driversBefore = buildList<Driver> {
            val drivers = DriverManager.getDrivers()
            while (drivers.hasMoreElements()) {
                add(drivers.nextElement())
            }
        }

        driversBefore.forEach { DriverManager.deregisterDriver(it) }
        DriverManager.registerDriver(driver)

        val result =
            try {
                val faultConfiguration = PostgresConfiguration(
                    faultUrl,
                    configuration.user,
                    configuration.password
                )
                PostgresGovernedFinancialLedgerMaterializationCommitStore(faultConfiguration)
                    .commit(plan)
            } finally {
                DriverManager.deregisterDriver(driver)
                driversBefore.forEach { DriverManager.registerDriver(it) }
            }

        val failure =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.Failed>(result)
        assertEquals(
            GovernedFinancialLedgerMaterializationCommitFailure.UNAVAILABLE,
            failure.failure
        )
        assertEquals(0, count("SELECT count(*) FROM marketplace_financial_trace"))
        assertEquals(0, count("SELECT count(*) FROM marketplace_financial_ledger_entry"))
        assertEquals(
            0,
            count(
                "SELECT count(*) FROM marketplace_financial_ledger_materialization_lineage"
            )
        )
    }

    @Test
    fun `sources participating in durable correction are not first-time materialized`() {
        val original = observation()
        val replacement = observation(
            organizationId = original.subject.organizationId,
            orderId = original.subject.orderId
        )
        insertOrganization(original.subject.organizationId)
        persistObservation(original)
        appendCorrection(original, replacement)

        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        assertIntegrity(store.commit(verifiedPlan(original)))
        assertIntegrity(store.commit(verifiedPlan(replacement)))
        assertEquals(0, traceCount(original))
        assertEquals(0, entryCount(original))
        assertEquals(0, lineageCount(original))
    }

    @Test
    fun `historical exact lineage remains replayable after correction while replacement stays blocked`() {
        val original = observation()
        val replacement = observation(
            organizationId = original.subject.organizationId,
            orderId = original.subject.orderId
        )
        insertOrganization(original.subject.organizationId)
        persistObservation(original)

        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        val originalPlan = verifiedPlan(original)
        val first =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
                store.commit(originalPlan)
            )

        appendCorrection(original, replacement)

        val replay =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
                store.commit(originalPlan)
            )
        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)

        assertIntegrity(store.commit(verifiedPlan(replacement)))
        assertEquals(1, traceCount(original))
        assertEquals(1, entryCount(original))
        assertEquals(1, lineageCount(original))
    }

    @Test
    fun `tampered lineage cannot be accepted as exact replay`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )
        tamperLineageBasis(observation, "ACTUAL")

        assertIntegrity(store.commit(plan))
        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(1, lineageCount(observation))
    }

    @Test
    fun `tampered ledger entry cannot be accepted as exact replay`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )
        tamperLedgerMagnitude(observation, "11")

        assertIntegrity(store.commit(plan))
        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(1, lineageCount(observation))
    }

    @Test
    fun `corrected source before first materialization fails closed`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        persistCorrectionViaRepository(observation)

        val result =
            PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
                .commit(verifiedPlan(observation))

        assertIntegrity(result)
        assertEquals(0, traceCount(observation))
        assertEquals(0, entryCount(observation))
        assertEquals(0, lineageCount(observation))
    }

    @Test
    fun `historical lineage remains replayable after source is later corrected`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )
        persistCorrectionViaRepository(observation)

        val replay =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
                store.commit(plan)
            )

        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)
        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(1, lineageCount(observation))
    }

    @Test
    fun `correction context blocks first materialization and replacement until correction lineage exists`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val replacement = persistCorrection(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        assertIntegrity(store.commit(verifiedPlan(observation)))
        assertIntegrity(store.commit(verifiedPlan(replacement)))
        assertEquals(0, traceCount(observation))
        assertEquals(0, entryCount(observation))
        assertEquals(0, lineageCount(observation))
    }

    @Test
    fun `historical materialization remains replayable after source is later superseded`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )

        val replacement = persistCorrection(observation)
        val replay = assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
            store.commit(plan)
        )
        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)
        assertIntegrity(store.commit(verifiedPlan(replacement)))
        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(1, lineageCount(observation))
    }

    @Test
    fun `correction participation before first materialization fails closed`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        persistCorrectionParticipation(observation)

        val result =
            PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
                .commit(plan)

        assertIntegrity(result)
        assertEquals(0, traceCount(observation))
        assertEquals(0, entryCount(observation))
        assertEquals(0, lineageCount(observation))
    }

    @Test
    fun `existing historical lineage remains replayable after later correction`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )
        persistCorrectionParticipation(observation)

        val replay = assertIs<
            GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized
        >(store.commit(plan))

        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)
        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(1, lineageCount(observation))
    }

    @Test
    fun `concurrent identical first materialization serializes to one durable result`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val ready = CountDownLatch(2)
        val start = CountDownLatch(1)
        val executor = Executors.newFixedThreadPool(2)

        try {
            val futures = (1..2).map {
                executor.submit<GovernedFinancialLedgerMaterializationCommitResult> {
                    ready.countDown()
                    check(start.await(10, TimeUnit.SECONDS))
                    PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
                        .commit(plan)
                }
            }

            check(ready.await(10, TimeUnit.SECONDS))
            start.countDown()

            val results = futures.map { it.get(60, TimeUnit.SECONDS) }
            val materialized = results.filterIsInstance<
                GovernedFinancialLedgerMaterializationCommitResult.Materialized
            >()
            val replayed = results.filterIsInstance<
                GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized
            >()

            assertEquals(1, materialized.size)
            assertEquals(1, replayed.size)
            assertEquals(materialized.single().traceId, replayed.single().traceId)
            assertEquals(materialized.single().entryId, replayed.single().entryId)
            assertEquals(1, traceCount(observation))
            assertEquals(1, entryCount(observation))
            assertEquals(1, lineageCount(observation))
        } finally {
            start.countDown()
            executor.shutdownNow()
            check(executor.awaitTermination(10, TimeUnit.SECONDS))
        }
    }

    @Test
    fun `correction participants fail closed before first materialization`() {
        val original = observation()
        val replacement = observation(
            organizationId = original.subject.organizationId,
            orderId = original.subject.orderId
        )
        insertOrganization(original.subject.organizationId)
        persistObservation(original)
        persistCorrection(original, replacement)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        assertIntegrity(store.commit(verifiedPlan(original)))
        assertIntegrity(store.commit(verifiedPlan(replacement)))
        assertEquals(0, traceCount(original))
        assertEquals(0, entryCount(original))
        assertEquals(0, lineageCount(original))
    }

    @Test
    fun `historical lineage remains replayable after source correction while replacement stays blocked`() {
        val original = observation()
        val replacement = observation(
            organizationId = original.subject.organizationId,
            orderId = original.subject.orderId
        )
        insertOrganization(original.subject.organizationId)
        persistObservation(original)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        val plan = verifiedPlan(original)

        val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )
        persistCorrection(original, replacement)

        val replay = assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
            store.commit(plan)
        )
        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)
        assertIntegrity(store.commit(verifiedPlan(replacement)))
        assertEquals(1, traceCount(original))
        assertEquals(1, entryCount(original))
        assertEquals(1, lineageCount(original))
    }

    @Test
    fun `correction participation blocks ordinary first materialization for both sides`() {
        val original = observation()
        insertOrganization(original.subject.organizationId)
        persistObservation(original)
        val replacement = replacementObservation(original)
        applyCorrection(original, replacement)

        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        assertIntegrity(store.commit(verifiedPlan(original)))
        assertIntegrity(store.commit(verifiedPlan(replacement)))
        assertEquals(0, traceCount(original))
        assertEquals(0, entryCount(original))
        assertEquals(0, lineageCount(original))
    }

    @Test
    fun `historical lineage remains replayable after source is later superseded`() {
        val original = observation()
        insertOrganization(original.subject.organizationId)
        persistObservation(original)
        val plan = verifiedPlan(original)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )
        val replacement = replacementObservation(original)
        applyCorrection(original, replacement)

        val replay = assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
            store.commit(plan)
        )

        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)
        assertEquals(1, traceCount(original))
        assertEquals(1, entryCount(original))
        assertEquals(1, lineageCount(original))
    }

    @Test
    fun `concurrent identical first materialization produces one materialized and one replay`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
        val start = CountDownLatch(1)
        val executor = Executors.newFixedThreadPool(2)

        try {
            val futures = (1..2).map {
                executor.submit<GovernedFinancialLedgerMaterializationCommitResult> {
                    check(start.await(10, TimeUnit.SECONDS))
                    store.commit(plan)
                }
            }
            start.countDown()
            val results = futures.map { it.get(60, TimeUnit.SECONDS) }
            val materialized = results.filterIsInstance<
                GovernedFinancialLedgerMaterializationCommitResult.Materialized
            >()
            val replay = results.filterIsInstance<
                GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized
            >()

            assertEquals(1, materialized.size)
            assertEquals(1, replay.size)
            assertEquals(materialized.single().traceId, replay.single().traceId)
            assertEquals(materialized.single().entryId, replay.single().entryId)
            assertEquals(1, traceCount(observation))
            assertEquals(1, entryCount(observation))
            assertEquals(1, lineageCount(observation))
        } finally {
            executor.shutdownNow()
        }
    }

    @Test
    fun `first materialization fails closed for both sides of durable correction`() {
        val original = observation()
        insertOrganization(original.subject.organizationId)
        persistObservation(original)
        val replacement = persistCorrectionForSource(original)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        assertIntegrity(store.commit(verifiedPlan(original)))
        assertIntegrity(store.commit(verifiedPlan(replacement)))
        assertEquals(0, traceCount(original))
        assertEquals(0, entryCount(original))
        assertEquals(0, lineageCount(original))
    }

    @Test
    fun `historical lineage remains exact replay after source is later superseded`() {
        val original = observation()
        insertOrganization(original.subject.organizationId)
        persistObservation(original)
        val plan = verifiedPlan(original)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
            store.commit(plan)
        )
        persistCorrectionForSource(original)
        val replay = assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
            store.commit(plan)
        )

        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)
        assertEquals(1, traceCount(original))
        assertEquals(1, entryCount(original))
        assertEquals(1, lineageCount(original))
    }

    @Test
    fun `durable source cannot be borrowed across organizations`() {
        val sourceOrganization = OrganizationId.parse(UUID.randomUUID().toString())
        val otherOrganization = OrganizationId.parse(UUID.randomUUID().toString())
        val orderId = MarketplaceOrderId.parse(UUID.randomUUID().toString())
        val sourceId = MarketplaceEconomicEvidenceObservationId.parse(UUID.randomUUID().toString())
        val persisted = observation(
            organizationId = sourceOrganization,
            orderId = orderId,
            observationId = sourceId
        )
        val foreignPlanObservation = observation(
            organizationId = otherOrganization,
            orderId = orderId,
            observationId = sourceId
        )

        insertOrganization(sourceOrganization)
        insertOrganization(otherOrganization)
        persistObservation(persisted)

        val result = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
            .commit(verifiedPlan(foreignPlanObservation))

        assertIntegrity(result)
        assertEquals(0, traceCountFor(otherOrganization, orderId))
        assertEquals(0, lineageCountFor(otherOrganization, orderId))
    }

    @Test
    fun `database connection failure is unavailable and creates no durable facts`() {
        val observation = observation()
        val unavailableConfiguration = PostgresConfiguration(
            "jdbc:postgresql://127.0.0.1:1/postgres?connectTimeout=1",
            "unused",
            "unused"
        )

        val result = PostgresGovernedFinancialLedgerMaterializationCommitStore(
            unavailableConfiguration
        ).commit(verifiedPlan(observation))

        val failure = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Failed>(result)
        assertEquals(
            GovernedFinancialLedgerMaterializationCommitFailure.UNAVAILABLE,
            failure.failure
        )
    }

    @Test
    fun `source already participating in durable correction cannot first materialize as ordinary fact`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        appendCorrection(observation)

        val result =
            PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
                .commit(plan)

        assertIntegrity(result)
        assertEquals(0, traceCount(observation))
        assertEquals(0, entryCount(observation))
        assertEquals(0, lineageCount(observation))
    }

    @Test
    fun `historical lineage remains exactly replayable after source is superseded`() {
        val observation = observation()
        insertOrganization(observation.subject.organizationId)
        persistObservation(observation)
        val plan = verifiedPlan(observation)
        val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)

        val first =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(
                store.commit(plan)
            )

        appendCorrection(observation)

        val replay =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
                store.commit(plan)
            )

        assertEquals(first.traceId, replay.traceId)
        assertEquals(first.entryId, replay.entryId)
        assertEquals(1, traceCount(observation))
        assertEquals(1, entryCount(observation))
        assertEquals(1, lineageCount(observation))
    }

    private fun verifiedPlan(
        observation: MarketplaceEconomicComponentObservation,
        basis: FinancialLedgerBasis = FinancialLedgerBasis.EXPECTED,
        semanticVersion: String = "marketplace-economic-component/1"
    ): VerifiedFinancialLedgerComponentMaterializationPlan {
        val authority = FinancialLedgerComponentMaterializationAuthorityDecision.Authorized(
            observation.id,
            FinancialLedgerSourceAuthoritySemanticVersion(semanticVersion),
            FinancialLedgerMaterializationPolicyVersion.V1,
            FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation),
            basis
        )
        val result = GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(
            observation.subject.organizationId,
            observation,
            authority
        )
        return assertIs<GovernedFinancialLedgerComponentMaterializationResult.Eligible>(result).plan
    }

    private fun observation(
        organizationId: OrganizationId =
            OrganizationId.parse(UUID.randomUUID().toString()),
        orderId: MarketplaceOrderId =
            MarketplaceOrderId.parse(UUID.randomUUID().toString()),
        observationId: MarketplaceEconomicEvidenceObservationId =
            MarketplaceEconomicEvidenceObservationId.parse(UUID.randomUUID().toString())
    ): MarketplaceEconomicComponentObservation {
        val currency = MarketplaceCurrency("BRL")
        val subject = MarketplaceEconomicEvidenceSubject(
            organizationId,
            orderId,
            MarketplaceKey("mercado-livre"),
            MarketplaceExternalOrderId("order-${orderId.value}"),
            currency
        )
        val component = EconomicComponent(
            organizationId,
            EconomicComponentId.parse(UUID.randomUUID().toString()),
            orderId,
            EconomicComponentType.REVENUE,
            EconomicDirection.ADDITION,
            MarketplaceMoney.parse(currency, "10"),
            EconomicSource(
                EconomicSourceKind.MARKETPLACE,
                EconomicSourceSystemKey("b3b-source"),
                EconomicExternalReferenceState.Present(
                    EconomicExternalReference("source-${orderId.value}")
                )
            ),
            Instant.parse("2026-09-14T10:00:00.123456Z"),
            EconomicEvidenceQuality.CONFIRMED
        )
        return MarketplaceEconomicComponentObservation(
            observationId,
            subject,
            MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
            component,
            EconomicComponentCoverage.COMPLETE,
            Instant.parse("2026-09-14T10:00:01.123456Z")
        )
    }

    private fun insertOrganization(organizationId: OrganizationId) {
        connection().use { connection ->
            connection.prepareStatement(
                "INSERT INTO integration_organization " +
                    "(organization_id,status,created_at,updated_at) VALUES (?,?,?,?)"
            ).use { statement ->
                val now = Timestamp.from(Instant.parse("2026-09-14T09:59:00Z"))
                statement.setObject(1, organizationId.value)
                statement.setString(2, "ACTIVE")
                statement.setTimestamp(3, now)
                statement.setTimestamp(4, now)
                assertEquals(1, statement.executeUpdate())
            }
        }
    }

    private fun persistObservation(observation: MarketplaceEconomicComponentObservation) {
        val subject = observation.subject
        val component = observation.component
        val observationId = observation.id.valueForPersistence()
        val sourceReference =
            assertIs<EconomicExternalReferenceState.Present>(
                component.source.externalReference
            ).reference.value

        connection().use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_subject " +
                        "(organization_id,marketplace_order_id,marketplace_key," +
                        "external_order_id,currency) VALUES (?,?,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setString(3, subject.marketplace.value)
                    statement.setString(4, subject.externalOrderId.value)
                    statement.setString(5, subject.currency.code)
                    statement.executeUpdate()
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_update " +
                        "(organization_id,marketplace_order_id,evidence_version," +
                        "update_id,change_kind) VALUES (?,?,1,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, observationId)
                    statement.setString(4, "FACT")
                    statement.executeUpdate()
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,1,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, observationId)
                    statement.setString(4, "FACT")
                    statement.executeUpdate()
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,observed_at) VALUES (?,?,?,1,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, observationId)
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, observation.family.name)
                    statement.setTimestamp(6, Timestamp.from(observation.observedAt))
                    statement.executeUpdate()
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_component_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,component_id,component_type,direction,magnitude," +
                        "currency,source_kind,source_system_key,source_external_reference," +
                        "source_external_reference_absence_reason,occurred_at,quality,coverage) " +
                        "VALUES (?,?,?,1,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, observationId)
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, observation.family.name)
                    statement.setObject(6, component.id.value)
                    statement.setString(7, component.type.name)
                    statement.setString(8, component.direction.name)
                    statement.setBigDecimal(9, component.magnitude.amount)
                    statement.setString(10, component.magnitude.currency.code)
                    statement.setString(11, component.source.kind.name)
                    statement.setString(12, component.source.systemKey.value)
                    statement.setString(13, sourceReference)
                    statement.setTimestamp(14, Timestamp.from(component.occurredAt))
                    statement.setString(15, component.quality.name)
                    statement.setString(16, observation.coverageClaim.name)
                    statement.executeUpdate()
                }
                connection.prepareStatement(
                    "UPDATE marketplace_economic_evidence_subject SET current_version=1 " +
                        "WHERE organization_id=? AND marketplace_order_id=?"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.executeUpdate()
                }
                connection.commit()
            } catch (error: Exception) {
                connection.rollback()
                throw error
            }
        }
    }

    private fun persistCorrection(
        original: MarketplaceEconomicComponentObservation,
        replacement: MarketplaceEconomicComponentObservation
    ) {
        require(original.subject == replacement.subject)
        val subject = original.subject
        val replacementComponent = replacement.component
        val replacementReference =
            assertIs<EconomicExternalReferenceState.Present>(
                replacementComponent.source.externalReference
            ).reference.value
        val correctionId = UUID.randomUUID()

        connection().use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_update " +
                        "(organization_id,marketplace_order_id,evidence_version," +
                        "update_id,change_kind) VALUES (?,?,2,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacement.id.valueForPersistence())
                    statement.setString(4, "FACT")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,observed_at) VALUES (?,?,?,2,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacement.id.valueForPersistence())
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, replacement.family.name)
                    statement.setTimestamp(6, Timestamp.from(replacement.observedAt))
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_component_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,component_id,component_type,direction,magnitude," +
                        "currency,source_kind,source_system_key,source_external_reference," +
                        "source_external_reference_absence_reason,occurred_at,quality,coverage) " +
                        "VALUES (?,?,?,2,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacement.id.valueForPersistence())
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, replacement.family.name)
                    statement.setObject(6, replacementComponent.id.value)
                    statement.setString(7, replacementComponent.type.name)
                    statement.setString(8, replacementComponent.direction.name)
                    statement.setBigDecimal(9, replacementComponent.magnitude.amount)
                    statement.setString(10, replacementComponent.magnitude.currency.code)
                    statement.setString(11, replacementComponent.source.kind.name)
                    statement.setString(12, replacementComponent.source.systemKey.value)
                    statement.setString(13, replacementReference)
                    statement.setTimestamp(14, Timestamp.from(replacementComponent.occurredAt))
                    statement.setString(15, replacementComponent.quality.name)
                    statement.setString(16, replacement.coverageClaim.name)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_correction " +
                        "(organization_id,marketplace_order_id,correction_id,evidence_version," +
                        "superseded_fact_id,replacement_fact_id,reason,observed_at) " +
                        "VALUES (?,?,?,2,?,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setObject(4, original.id.valueForPersistence())
                    statement.setObject(5, replacement.id.valueForPersistence())
                    statement.setString(6, "SOURCE_CORRECTION")
                    statement.setTimestamp(
                        7,
                        Timestamp.from(Instant.parse("2026-09-14T10:00:02.123456Z"))
                    )
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "UPDATE marketplace_economic_evidence_subject SET current_version=2 " +
                        "WHERE organization_id=? AND marketplace_order_id=?"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.commit()
            } catch (error: Exception) {
                connection.rollback()
                throw error
            }
        }
    }

    private fun assertDurableExact(
        plan: VerifiedFinancialLedgerComponentMaterializationPlan,
        traceId: UUID,
        entryId: UUID
    ) {
        connection().use { connection ->
            connection.prepareStatement(
                "SELECT trace.order_id,trace.marketplace_key,trace.external_order_id," +
                    "trace.currency,entry.trace_id,entry.entry_id,entry.stage,entry.basis," +
                    "entry.direction,entry.magnitude,entry.source_kind,entry.source_system_key," +
                    "entry.external_reference,entry.external_reference_absence_reason," +
                    "entry.occurred_at,entry.corrects_entry_id," +
                    "lineage.source_fingerprint_canonicalization_version," +
                    "lineage.source_fingerprint_sha256,lineage.source_authority_semantic_version," +
                    "lineage.materialization_policy_version " +
                    "FROM marketplace_financial_ledger_materialization_lineage lineage " +
                    "JOIN marketplace_financial_trace trace " +
                    "ON trace.organization_id=lineage.organization_id " +
                    "AND trace.trace_id=lineage.trace_id " +
                    "JOIN marketplace_financial_ledger_entry entry " +
                    "ON entry.organization_id=lineage.organization_id " +
                    "AND entry.entry_id=lineage.ledger_entry_id " +
                    "WHERE lineage.organization_id=? AND lineage.source_order_id=? " +
                    "AND lineage.source_authority_identity=?"
            ).use { statement ->
                statement.setObject(1, plan.subject.organizationId.value)
                statement.setObject(2, plan.subject.orderId.value)
                statement.setObject(3, plan.sourceAuthorityIdentity.valueForPersistence())
                statement.executeQuery().use { result ->
                    check(result.next())
                    assertEquals(plan.subject.orderId.value, result.getObject("order_id", UUID::class.java))
                    assertEquals(plan.subject.marketplace.value, result.getString("marketplace_key"))
                    assertEquals(plan.subject.externalOrderId.value, result.getString("external_order_id"))
                    assertEquals(plan.subject.currency.code, result.getString("currency").trim())
                    assertEquals(traceId, result.getObject("trace_id", UUID::class.java))
                    assertEquals(entryId, result.getObject("entry_id", UUID::class.java))
                    assertEquals(plan.stage.name, result.getString("stage"))
                    assertEquals(plan.basis.name, result.getString("basis"))
                    assertEquals(plan.direction.name, result.getString("direction"))
                    assertEquals(0, result.getBigDecimal("magnitude").compareTo(plan.magnitude.amount))
                    assertEquals(plan.source.kind.name, result.getString("source_kind"))
                    assertEquals(plan.source.systemKey.value, result.getString("source_system_key"))
                    assertEquals(
                        assertIs<EconomicExternalReferenceState.Present>(
                            plan.source.externalReference
                        ).reference.value,
                        result.getString("external_reference")
                    )
                    assertNull(result.getString("external_reference_absence_reason"))
                    assertEquals(plan.occurredAt, result.getTimestamp("occurred_at").toInstant())
                    assertNull(result.getObject("corrects_entry_id"))
                    assertEquals(
                        plan.verifiedSourceFingerprint.canonicalizationVersion,
                        result.getInt("source_fingerprint_canonicalization_version")
                    )
                    assertEquals(
                        plan.verifiedSourceFingerprint.sha256,
                        result.getString("source_fingerprint_sha256")
                    )
                    assertEquals(
                        plan.sourceAuthoritySemanticVersion.value,
                        result.getString("source_authority_semantic_version")
                    )
                    assertEquals(
                        plan.materializationPolicyVersion.value,
                        result.getString("materialization_policy_version")
                    )
                    check(!result.next())
                }
            }
        }
    }

    private class CommitAcknowledgementLossDriver(
        private val acceptedUrl: String,
        private val delegateUrl: String,
        private val delegateUser: String,
        private val delegatePassword: String
    ) : Driver {
        val ackLossInjected = AtomicBoolean(false)

        override fun acceptsURL(url: String?): Boolean = url == acceptedUrl

        override fun connect(url: String?, info: Properties?): Connection? {
            if (!acceptsURL(url)) {
                return null
            }
            val delegate = DriverManager.getConnection(
                delegateUrl,
                delegateUser,
                delegatePassword
            )
            return Proxy.newProxyInstance(
                Connection::class.java.classLoader,
                arrayOf(Connection::class.java)
            ) { _, method, args ->
                if (
                    method.name == "commit" &&
                    method.parameterCount == 0 &&
                    ackLossInjected.compareAndSet(false, true)
                ) {
                    invokeDelegate(method, delegate, args)
                    throw SQLException(
                        "simulated commit acknowledgement loss",
                        "08006"
                    )
                }
                invokeDelegate(method, delegate, args)
            } as Connection
        }

        private fun invokeDelegate(
            method: java.lang.reflect.Method,
            delegate: Connection,
            args: Array<out Any?>?
        ): Any? =
            try {
                if (args == null) {
                    method.invoke(delegate)
                } else {
                    method.invoke(delegate, *args)
                }
            } catch (error: InvocationTargetException) {
                throw error.targetException
            }

        override fun getPropertyInfo(
            url: String?,
            info: Properties?
        ): Array<DriverPropertyInfo> = emptyArray()

        override fun getMajorVersion(): Int = 1

        override fun getMinorVersion(): Int = 0

        override fun jdbcCompliant(): Boolean = false

        override fun getParentLogger(): Logger = Logger.getGlobal()
    }

    private fun appendCorrection(
        original: MarketplaceEconomicComponentObservation,
        replacement: MarketplaceEconomicComponentObservation
    ) {
        check(original.subject == replacement.subject)
        val subject = original.subject
        val replacementComponent = replacement.component
        val replacementReference =
            assertIs<EconomicExternalReferenceState.Present>(
                replacementComponent.source.externalReference
            ).reference.value
        val replacementId = replacement.id.valueForPersistence()
        val correctionId = UUID.randomUUID()

        connection().use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_update " +
                        "(organization_id,marketplace_order_id,evidence_version," +
                        "update_id,change_kind) VALUES (?,?,2,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "FACT")
                    assertEquals(1, statement.executeUpdate())
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,observed_at) VALUES (?,?,?,2,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, replacement.family.name)
                    statement.setTimestamp(6, Timestamp.from(replacement.observedAt))
                    assertEquals(1, statement.executeUpdate())
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_component_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,component_id,component_type,direction,magnitude," +
                        "currency,source_kind,source_system_key,source_external_reference," +
                        "source_external_reference_absence_reason,occurred_at,quality,coverage) " +
                        "VALUES (?,?,?,2,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, replacement.family.name)
                    statement.setObject(6, replacementComponent.id.value)
                    statement.setString(7, replacementComponent.type.name)
                    statement.setString(8, replacementComponent.direction.name)
                    statement.setBigDecimal(9, replacementComponent.magnitude.amount)
                    statement.setString(10, replacementComponent.magnitude.currency.code)
                    statement.setString(11, replacementComponent.source.kind.name)
                    statement.setString(12, replacementComponent.source.systemKey.value)
                    statement.setString(13, replacementReference)
                    statement.setTimestamp(14, Timestamp.from(replacementComponent.occurredAt))
                    statement.setString(15, replacementComponent.quality.name)
                    statement.setString(16, replacement.coverageClaim.name)
                    assertEquals(1, statement.executeUpdate())
                }

                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_correction " +
                        "(organization_id,marketplace_order_id,correction_id,evidence_version," +
                        "superseded_fact_id,replacement_fact_id,reason,observed_at) " +
                        "VALUES (?,?,?,2,?,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setObject(4, original.id.valueForPersistence())
                    statement.setObject(5, replacementId)
                    statement.setString(6, "SOURCE_CORRECTION")
                    statement.setTimestamp(
                        7,
                        Timestamp.from(Instant.parse("2026-09-14T10:00:02.123456Z"))
                    )
                    assertEquals(1, statement.executeUpdate())
                }

                connection.prepareStatement(
                    "UPDATE marketplace_economic_evidence_subject SET current_version=2 " +
                        "WHERE organization_id=? AND marketplace_order_id=?"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    assertEquals(1, statement.executeUpdate())
                }

                connection.commit()
            } catch (error: Exception) {
                connection.rollback()
                throw error
            }
        }
    }

    private fun persistCorrectionViaRepository(
        observation: MarketplaceEconomicComponentObservation
    ) {
        val subject = observation.subject
        val component = observation.component
        val replacementObservedAt = observation.observedAt.plusSeconds(3)
        val replacement = MarketplaceEconomicComponentObservation(
            id = MarketplaceEconomicEvidenceObservationId.parse(
                UUID.randomUUID().toString()
            ),
            subject = subject,
            family = observation.family,
            component = EconomicComponent(
                organizationId = subject.organizationId,
                id = EconomicComponentId.parse(UUID.randomUUID().toString()),
                orderId = subject.orderId,
                type = component.type,
                direction = component.direction,
                magnitude = component.magnitude,
                source = EconomicSource(
                    kind = component.source.kind,
                    systemKey = component.source.systemKey,
                    externalReference = EconomicExternalReferenceState.Present(
                        EconomicExternalReference(
                            "replacement-${subject.orderId.value}"
                        )
                    )
                ),
                occurredAt = component.occurredAt.plusSeconds(2),
                quality = component.quality
            ),
            coverageClaim = observation.coverageClaim,
            observedAt = replacementObservedAt
        )
        val correction = MarketplaceEconomicEvidenceCorrection(
            id = MarketplaceEconomicEvidenceObservationId.parse(
                UUID.randomUUID().toString()
            ),
            subject = subject,
            replacement = MarketplaceIndependentEconomicFact.Component(replacement),
            supersedesObservationId = observation.id,
            reason = MarketplaceEconomicEvidenceCorrectionReason.SOURCE_CORRECTION,
            observedAt = replacementObservedAt.plusSeconds(1)
        )
        val result = PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration).apply(
            MarketplaceEconomicEvidenceVersion.ZERO.next(),
            MarketplaceIndependentEconomicEvidenceUpdate.Correct(correction)
        )
        assertIs<MarketplaceIndependentEconomicEvidencePersistResult.Applied>(result)
    }

    private fun persistCorrection(
        superseded: MarketplaceEconomicComponentObservation
    ): MarketplaceEconomicComponentObservation {
        val subject = superseded.subject
        val replacementId = MarketplaceEconomicEvidenceObservationId.parse(
            UUID.randomUUID().toString()
        )
        val correctionId = UUID.randomUUID()
        val replacementComponent = EconomicComponent(
            subject.organizationId,
            EconomicComponentId.parse(UUID.randomUUID().toString()),
            subject.orderId,
            superseded.component.type,
            superseded.component.direction,
            MarketplaceMoney.parse(subject.currency, "12"),
            EconomicSource(
                superseded.component.source.kind,
                superseded.component.source.systemKey,
                EconomicExternalReferenceState.Present(
                    EconomicExternalReference("replacement-${subject.orderId.value}")
                )
            ),
            Instant.parse("2026-09-14T10:01:00.123456Z"),
            superseded.component.quality
        )
        val replacement = MarketplaceEconomicComponentObservation(
            replacementId,
            subject,
            superseded.family,
            replacementComponent,
            superseded.coverageClaim,
            Instant.parse("2026-09-14T10:01:01.123456Z")
        )
        val sourceReference = assertIs<EconomicExternalReferenceState.Present>(
            replacement.component.source.externalReference
        ).reference.value

        connection().use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_update " +
                        "(organization_id,marketplace_order_id,evidence_version," +
                        "update_id,change_kind) VALUES (?,?,2,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacement.id.valueForPersistence())
                    statement.setString(4, "FACT")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,observed_at) VALUES (?,?,?,2,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacement.id.valueForPersistence())
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, replacement.family.name)
                    statement.setTimestamp(6, Timestamp.from(replacement.observedAt))
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_component_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,component_id,component_type,direction,magnitude," +
                        "currency,source_kind,source_system_key,source_external_reference," +
                        "source_external_reference_absence_reason,occurred_at,quality,coverage) " +
                        "VALUES (?,?,?,2,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacement.id.valueForPersistence())
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, replacement.family.name)
                    statement.setObject(6, replacement.component.id.value)
                    statement.setString(7, replacement.component.type.name)
                    statement.setString(8, replacement.component.direction.name)
                    statement.setBigDecimal(9, replacement.component.magnitude.amount)
                    statement.setString(10, replacement.component.magnitude.currency.code)
                    statement.setString(11, replacement.component.source.kind.name)
                    statement.setString(12, replacement.component.source.systemKey.value)
                    statement.setString(13, sourceReference)
                    statement.setTimestamp(14, Timestamp.from(replacement.component.occurredAt))
                    statement.setString(15, replacement.component.quality.name)
                    statement.setString(16, replacement.coverageClaim.name)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_correction " +
                        "(organization_id,marketplace_order_id,correction_id,evidence_version," +
                        "superseded_fact_id,replacement_fact_id,reason,observed_at) " +
                        "VALUES (?,?,?,2,?,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setObject(4, superseded.id.valueForPersistence())
                    statement.setObject(5, replacement.id.valueForPersistence())
                    statement.setString(6, "SOURCE_CORRECTION")
                    statement.setTimestamp(
                        7,
                        Timestamp.from(Instant.parse("2026-09-14T10:01:02.123456Z"))
                    )
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "UPDATE marketplace_economic_evidence_subject SET current_version=2 " +
                        "WHERE organization_id=? AND marketplace_order_id=?"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.commit()
            } catch (error: Exception) {
                connection.rollback()
                throw error
            }
        }
        return replacement
    }

    private fun persistCorrectionParticipation(
        observation: MarketplaceEconomicComponentObservation
    ) {
        val subject = observation.subject
        val original = observation.component
        val correctionId = UUID.randomUUID()
        val replacementId = UUID.randomUUID()
        val replacementComponentId = UUID.randomUUID()
        val sourceReference =
            assertIs<EconomicExternalReferenceState.Present>(
                original.source.externalReference
            ).reference.value

        connection().use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_update " +
                        "(organization_id,marketplace_order_id,evidence_version," +
                        "update_id,change_kind) VALUES (?,?,2,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "FACT")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,observed_at) VALUES (?,?,?,2,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, observation.family.name)
                    statement.setTimestamp(
                        6,
                        Timestamp.from(Instant.parse("2026-09-14T10:00:02.123456Z"))
                    )
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_component_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,component_id,component_type,direction,magnitude," +
                        "currency,source_kind,source_system_key,source_external_reference," +
                        "source_external_reference_absence_reason,occurred_at,quality,coverage) " +
                        "VALUES (?,?,?,2,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, observation.family.name)
                    statement.setObject(6, replacementComponentId)
                    statement.setString(7, original.type.name)
                    statement.setString(8, original.direction.name)
                    statement.setBigDecimal(9, original.magnitude.amount)
                    statement.setString(10, original.magnitude.currency.code)
                    statement.setString(11, original.source.kind.name)
                    statement.setString(12, original.source.systemKey.value)
                    statement.setString(13, sourceReference + "-replacement")
                    statement.setTimestamp(14, Timestamp.from(original.occurredAt))
                    statement.setString(15, original.quality.name)
                    statement.setString(16, observation.coverageClaim.name)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_correction " +
                        "(organization_id,marketplace_order_id,correction_id,evidence_version," +
                        "superseded_fact_id,replacement_fact_id,reason,observed_at) " +
                        "VALUES (?,?,?,2,?,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setObject(4, observation.id.valueForPersistence())
                    statement.setObject(5, replacementId)
                    statement.setString(6, "SOURCE_CORRECTION")
                    statement.setTimestamp(
                        7,
                        Timestamp.from(Instant.parse("2026-09-14T10:00:03.123456Z"))
                    )
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "UPDATE marketplace_economic_evidence_subject SET current_version=2 " +
                        "WHERE organization_id=? AND marketplace_order_id=?"
                ).use { statement ->
                    statement.setObject(1, subject.organizationId.value)
                    statement.setObject(2, subject.orderId.value)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.commit()
            } catch (error: Exception) {
                connection.rollback()
                throw error
            }
        }
    }

    private fun replacementObservation(
        original: MarketplaceEconomicComponentObservation
    ): MarketplaceEconomicComponentObservation {
        val subject = original.subject
        val originalComponent = original.component
        return MarketplaceEconomicComponentObservation(
            id = MarketplaceEconomicEvidenceObservationId.parse(UUID.randomUUID().toString()),
            subject = subject,
            family = original.family,
            component = EconomicComponent(
                organizationId = subject.organizationId,
                id = EconomicComponentId.parse(UUID.randomUUID().toString()),
                orderId = subject.orderId,
                type = originalComponent.type,
                direction = originalComponent.direction,
                magnitude = MarketplaceMoney.parse(subject.currency, "12"),
                source = EconomicSource(
                    originalComponent.source.kind,
                    originalComponent.source.systemKey,
                    EconomicExternalReferenceState.Present(
                        EconomicExternalReference("replacement-${subject.orderId.value}")
                    )
                ),
                occurredAt = Instant.parse("2026-09-14T10:00:02.123456Z"),
                quality = originalComponent.quality
            ),
            coverageClaim = original.coverageClaim,
            observedAt = Instant.parse("2026-09-14T10:00:03.123456Z")
        )
    }

    private fun applyCorrection(
        original: MarketplaceEconomicComponentObservation,
        replacement: MarketplaceEconomicComponentObservation
    ) {
        val correction = MarketplaceEconomicEvidenceCorrection(
            id = MarketplaceEconomicEvidenceObservationId.parse(UUID.randomUUID().toString()),
            subject = original.subject,
            replacement = MarketplaceIndependentEconomicFact.Component(replacement),
            supersedesObservationId = original.id,
            reason = MarketplaceEconomicEvidenceCorrectionReason.SOURCE_CORRECTION,
            observedAt = Instant.parse("2026-09-14T10:00:04.123456Z")
        )
        val result = PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration).apply(
            MarketplaceEconomicEvidenceVersion(1),
            MarketplaceIndependentEconomicEvidenceUpdate.Correct(correction)
        )
        assertIs<MarketplaceIndependentEconomicEvidencePersistResult.Applied>(result)
    }

    private fun appendCorrection(
        observation: MarketplaceEconomicComponentObservation
    ) {
        val subject = observation.subject
        val original = observation.component
        val correctionId = UUID.randomUUID()
        val replacementFactId = UUID.randomUUID()
        val replacementComponentId = UUID.randomUUID()
        val replacementOccurredAt = original.occurredAt.plusSeconds(1)
        val replacementObservedAt = observation.observedAt.plusSeconds(1)
        val correctionObservedAt = observation.observedAt.plusSeconds(2)

        connection().use { connection ->
            connection.autoCommit = false
            try {
                executeUpdate(
                    connection,
                    "INSERT INTO marketplace_economic_evidence_update " +
                        "(organization_id,marketplace_order_id,evidence_version," +
                        "update_id,change_kind) VALUES (?,?,?,?,?)",
                    subject.organizationId.value,
                    subject.orderId.value,
                    2L,
                    correctionId,
                    "CORRECTION"
                )
                executeUpdate(
                    connection,
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,?,?),(?,?,?,?,?)",
                    subject.organizationId.value,
                    subject.orderId.value,
                    correctionId,
                    2L,
                    "CORRECTION",
                    subject.organizationId.value,
                    subject.orderId.value,
                    replacementFactId,
                    2L,
                    "FACT"
                )
                executeUpdate(
                    connection,
                    "INSERT INTO marketplace_economic_evidence_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,observed_at) VALUES (?,?,?,?,?,?,?)",
                    subject.organizationId.value,
                    subject.orderId.value,
                    replacementFactId,
                    2L,
                    "COMPONENT",
                    observation.family.name,
                    Timestamp.from(replacementObservedAt)
                )
                executeUpdate(
                    connection,
                    "INSERT INTO marketplace_economic_evidence_component_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,component_id,component_type,direction,magnitude," +
                        "currency,source_kind,source_system_key,source_external_reference," +
                        "source_external_reference_absence_reason,occurred_at,quality,coverage) " +
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)",
                    subject.organizationId.value,
                    subject.orderId.value,
                    replacementFactId,
                    2L,
                    "COMPONENT",
                    observation.family.name,
                    replacementComponentId,
                    original.type.name,
                    original.direction.name,
                    original.magnitude.amount,
                    original.magnitude.currency.code,
                    original.source.kind.name,
                    original.source.systemKey.value,
                    "replacement-$replacementFactId",
                    Timestamp.from(replacementOccurredAt),
                    original.quality.name,
                    observation.coverageClaim.name
                )
                executeUpdate(
                    connection,
                    "INSERT INTO marketplace_economic_evidence_correction " +
                        "(organization_id,marketplace_order_id,correction_id,evidence_version," +
                        "superseded_fact_id,replacement_fact_id,reason,observed_at) " +
                        "VALUES (?,?,?,?,?,?,?,?)",
                    subject.organizationId.value,
                    subject.orderId.value,
                    correctionId,
                    2L,
                    observation.id.valueForPersistence(),
                    replacementFactId,
                    "SOURCE_CORRECTION",
                    Timestamp.from(correctionObservedAt)
                )
                executeUpdate(
                    connection,
                    "UPDATE marketplace_economic_evidence_subject SET current_version=2 " +
                        "WHERE organization_id=? AND marketplace_order_id=?",
                    subject.organizationId.value,
                    subject.orderId.value
                )
                connection.commit()
            } catch (error: Exception) {
                connection.rollback()
                throw error
            }
        }
    }

    private fun executeUpdate(
        connection: Connection,
        sql: String,
        vararg values: Any?
    ): Int =
        connection.prepareStatement(sql).use { statement ->
            values.forEachIndexed { index, value ->
                statement.setObject(index + 1, value)
            }
            statement.executeUpdate()
        }

    private fun assertIntegrity(
        result: GovernedFinancialLedgerMaterializationCommitResult
    ) {
        val failure =
            assertIs<GovernedFinancialLedgerMaterializationCommitResult.Failed>(result)
        assertEquals(
            GovernedFinancialLedgerMaterializationCommitFailure.INTEGRITY_FAILURE,
            failure.failure
        )
    }

    private fun tamperSourceMagnitude(
        observation: MarketplaceEconomicComponentObservation,
        magnitude: String
    ) {
        executeSql(
            "ALTER TABLE marketplace_economic_evidence_component_fact " +
                "DISABLE TRIGGER protect_marketplace_economic_component_fact_mutation"
        )
        connection().use { connection ->
            connection.prepareStatement(
                "UPDATE marketplace_economic_evidence_component_fact " +
                    "SET magnitude=? WHERE organization_id=? " +
                    "AND marketplace_order_id=? AND fact_id=?"
            ).use { statement ->
                statement.setBigDecimal(1, magnitude.toBigDecimal())
                statement.setObject(2, observation.subject.organizationId.value)
                statement.setObject(3, observation.subject.orderId.value)
                statement.setObject(4, observation.id.valueForPersistence())
                assertEquals(1, statement.executeUpdate())
            }
        }
        executeSql(
            "ALTER TABLE marketplace_economic_evidence_component_fact " +
                "ENABLE TRIGGER protect_marketplace_economic_component_fact_mutation"
        )
    }

    private fun insertExistingTrace(
        observation: MarketplaceEconomicComponentObservation,
        marketplace: String = observation.subject.marketplace.value,
        externalOrderId: String = observation.subject.externalOrderId.value
    ): UUID {
        val traceId = UUID.randomUUID()
        connection().use { connection ->
            connection.prepareStatement(
                "INSERT INTO marketplace_financial_trace " +
                    "(organization_id,trace_id,open_request_id,order_id," +
                    "marketplace_key,external_order_id,currency) " +
                    "VALUES (?,?,?,?,?,?,?)"
            ).use { statement ->
                statement.setObject(1, observation.subject.organizationId.value)
                statement.setObject(2, traceId)
                statement.setObject(3, UUID.randomUUID())
                statement.setObject(4, observation.subject.orderId.value)
                statement.setString(5, marketplace)
                statement.setString(6, externalOrderId)
                statement.setString(7, observation.subject.currency.code)
                assertEquals(1, statement.executeUpdate())
            }
        }
        return traceId
    }

    private fun insertExactUnboundEntry(
        observation: MarketplaceEconomicComponentObservation,
        traceId: UUID
    ) {
        val component = observation.component
        val sourceReference =
            assertIs<EconomicExternalReferenceState.Present>(
                component.source.externalReference
            ).reference.value
        connection().use { connection ->
            connection.prepareStatement(
                "INSERT INTO marketplace_financial_ledger_entry " +
                    "(organization_id,entry_id,append_request_id,trace_id,stage,basis," +
                    "direction,magnitude,source_kind,source_system_key,external_reference," +
                    "external_reference_absence_reason,occurred_at,corrects_entry_id) " +
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,NULL,?,NULL)"
            ).use { statement ->
                statement.setObject(1, observation.subject.organizationId.value)
                statement.setObject(2, UUID.randomUUID())
                statement.setObject(3, UUID.randomUUID())
                statement.setObject(4, traceId)
                statement.setString(5, "SALE")
                statement.setString(6, "EXPECTED")
                statement.setString(7, component.direction.name)
                statement.setBigDecimal(8, component.magnitude.amount)
                statement.setString(9, component.source.kind.name)
                statement.setString(10, component.source.systemKey.value)
                statement.setString(11, sourceReference)
                statement.setTimestamp(12, Timestamp.from(component.occurredAt))
                assertEquals(1, statement.executeUpdate())
            }
        }
    }

    private fun lineageCountBySource(
        organizationId: OrganizationId,
        sourceId: MarketplaceEconomicEvidenceObservationId
    ): Int =
        count(
            "SELECT count(*) FROM marketplace_financial_ledger_materialization_lineage " +
                "WHERE organization_id=? AND source_authority_identity=?",
            organizationId.value,
            sourceId.valueForPersistence()
        )

    private fun tamperLineageBasis(
        observation: MarketplaceEconomicComponentObservation,
        basis: String
    ) {
        executeSql(
            "ALTER TABLE marketplace_financial_ledger_materialization_lineage " +
                "DISABLE TRIGGER USER"
        )
        connection().use { connection ->
            connection.prepareStatement(
                "UPDATE marketplace_financial_ledger_materialization_lineage SET basis=? " +
                    "WHERE organization_id=? AND source_order_id=? " +
                    "AND source_authority_identity=?"
            ).use { statement ->
                statement.setString(1, basis)
                statement.setObject(2, observation.subject.organizationId.value)
                statement.setObject(3, observation.subject.orderId.value)
                statement.setObject(4, observation.id.valueForPersistence())
                assertEquals(1, statement.executeUpdate())
            }
        }
        executeSql(
            "ALTER TABLE marketplace_financial_ledger_materialization_lineage " +
                "ENABLE TRIGGER USER"
        )
    }

    private fun tamperLedgerMagnitude(
        observation: MarketplaceEconomicComponentObservation,
        magnitude: String
    ) {
        executeSql(
            "ALTER TABLE marketplace_financial_ledger_entry DISABLE TRIGGER USER"
        )
        connection().use { connection ->
            connection.prepareStatement(
                "UPDATE marketplace_financial_ledger_entry entry SET magnitude=? " +
                    "FROM marketplace_financial_trace trace " +
                    "WHERE trace.organization_id=entry.organization_id " +
                    "AND trace.trace_id=entry.trace_id AND trace.organization_id=? " +
                    "AND trace.order_id=?"
            ).use { statement ->
                statement.setBigDecimal(1, magnitude.toBigDecimal())
                statement.setObject(2, observation.subject.organizationId.value)
                statement.setObject(3, observation.subject.orderId.value)
                assertEquals(1, statement.executeUpdate())
            }
        }
        executeSql(
            "ALTER TABLE marketplace_financial_ledger_entry ENABLE TRIGGER USER"
        )
    }

    private fun persistCorrectionForSource(
        original: MarketplaceEconomicComponentObservation
    ): MarketplaceEconomicComponentObservation {
        val replacement = observation(
            organizationId = original.subject.organizationId,
            orderId = original.subject.orderId,
            observationId = MarketplaceEconomicEvidenceObservationId.parse(
                UUID.randomUUID().toString()
            )
        )
        val correctionId = UUID.randomUUID()
        val replacementId = replacement.id.valueForPersistence()
        val replacementComponent = replacement.component
        val replacementReference =
            assertIs<EconomicExternalReferenceState.Present>(
                replacementComponent.source.externalReference
            ).reference.value

        connection().use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_update " +
                        "(organization_id,marketplace_order_id,evidence_version," +
                        "update_id,change_kind) VALUES (?,?,2,?,?)"
                ).use { statement ->
                    statement.setObject(1, original.subject.organizationId.value)
                    statement.setObject(2, original.subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, original.subject.organizationId.value)
                    statement.setObject(2, original.subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setString(4, "CORRECTION")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_identifier " +
                        "(organization_id,marketplace_order_id,observation_id," +
                        "evidence_version,identifier_kind) VALUES (?,?,?,2,?)"
                ).use { statement ->
                    statement.setObject(1, original.subject.organizationId.value)
                    statement.setObject(2, original.subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "FACT")
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,observed_at) VALUES (?,?,?,2,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, original.subject.organizationId.value)
                    statement.setObject(2, original.subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, replacement.family.name)
                    statement.setTimestamp(6, Timestamp.from(replacement.observedAt))
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_component_fact " +
                        "(organization_id,marketplace_order_id,fact_id,evidence_version," +
                        "fact_kind,family,component_id,component_type,direction,magnitude," +
                        "currency,source_kind,source_system_key,source_external_reference," +
                        "source_external_reference_absence_reason,occurred_at,quality,coverage) " +
                        "VALUES (?,?,?,2,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, original.subject.organizationId.value)
                    statement.setObject(2, original.subject.orderId.value)
                    statement.setObject(3, replacementId)
                    statement.setString(4, "COMPONENT")
                    statement.setString(5, replacement.family.name)
                    statement.setObject(6, replacementComponent.id.value)
                    statement.setString(7, replacementComponent.type.name)
                    statement.setString(8, replacementComponent.direction.name)
                    statement.setBigDecimal(9, replacementComponent.magnitude.amount)
                    statement.setString(10, replacementComponent.magnitude.currency.code)
                    statement.setString(11, replacementComponent.source.kind.name)
                    statement.setString(12, replacementComponent.source.systemKey.value)
                    statement.setString(13, replacementReference)
                    statement.setTimestamp(14, Timestamp.from(replacementComponent.occurredAt))
                    statement.setString(15, replacementComponent.quality.name)
                    statement.setString(16, replacement.coverageClaim.name)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "INSERT INTO marketplace_economic_evidence_correction " +
                        "(organization_id,marketplace_order_id,correction_id,evidence_version," +
                        "superseded_fact_id,replacement_fact_id,reason,observed_at) " +
                        "VALUES (?,?,?,2,?,?,?,?)"
                ).use { statement ->
                    statement.setObject(1, original.subject.organizationId.value)
                    statement.setObject(2, original.subject.orderId.value)
                    statement.setObject(3, correctionId)
                    statement.setObject(4, original.id.valueForPersistence())
                    statement.setObject(5, replacementId)
                    statement.setString(6, "SOURCE_CORRECTION")
                    statement.setTimestamp(7, Timestamp.from(replacement.observedAt))
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "UPDATE marketplace_economic_evidence_subject SET current_version=2 " +
                        "WHERE organization_id=? AND marketplace_order_id=?"
                ).use { statement ->
                    statement.setObject(1, original.subject.organizationId.value)
                    statement.setObject(2, original.subject.orderId.value)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.commit()
            } catch (error: Exception) {
                connection.rollback()
                throw error
            }
        }
        return replacement
    }

    private fun traceCountFor(
        organizationId: OrganizationId,
        orderId: MarketplaceOrderId
    ): Int =
        count(
            "SELECT count(*) FROM marketplace_financial_trace " +
                "WHERE organization_id=? AND order_id=?",
            organizationId.value,
            orderId.value
        )

    private fun lineageCountFor(
        organizationId: OrganizationId,
        orderId: MarketplaceOrderId
    ): Int =
        count(
            "SELECT count(*) FROM marketplace_financial_ledger_materialization_lineage " +
                "WHERE organization_id=? AND source_order_id=?",
            organizationId.value,
            orderId.value
        )

    private fun installFailingLineageTrigger() {
        executeSql(
            "CREATE FUNCTION a_b3b2b_fail_lineage_insert() RETURNS trigger " +
                "LANGUAGE plpgsql AS 'BEGIN RAISE EXCEPTION ''forced lineage failure''; END;'"
        )
        executeSql(
            "CREATE TRIGGER a_b3b2b_fail_lineage_insert BEFORE INSERT " +
                "ON marketplace_financial_ledger_materialization_lineage " +
                "FOR EACH ROW EXECUTE FUNCTION a_b3b2b_fail_lineage_insert()"
        )
    }

    private fun executeSql(sql: String) {
        connection().use { connection ->
            connection.createStatement().use { statement ->
                statement.execute(sql)
            }
        }
    }

    private fun traceCount(observation: MarketplaceEconomicComponentObservation): Int =
        count(
            "SELECT count(*) FROM marketplace_financial_trace " +
                "WHERE organization_id=? AND order_id=?",
            observation.subject.organizationId.value,
            observation.subject.orderId.value
        )

    private fun entryCount(observation: MarketplaceEconomicComponentObservation): Int =
        count(
            "SELECT count(*) FROM marketplace_financial_ledger_entry entry " +
                "JOIN marketplace_financial_trace trace " +
                "ON trace.organization_id=entry.organization_id " +
                "AND trace.trace_id=entry.trace_id " +
                "WHERE trace.organization_id=? AND trace.order_id=?",
            observation.subject.organizationId.value,
            observation.subject.orderId.value
        )

    private fun lineageCount(observation: MarketplaceEconomicComponentObservation): Int =
        count(
            "SELECT count(*) FROM marketplace_financial_ledger_materialization_lineage " +
                "WHERE organization_id=? AND source_order_id=?",
            observation.subject.organizationId.value,
            observation.subject.orderId.value
        )

    private fun count(sql: String, vararg values: Any): Int =
        connection().use { connection ->
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

    private class AlwaysUnavailableDriver(
        private val acceptedUrl: String
    ) : Driver {
        override fun acceptsURL(url: String?): Boolean = url == acceptedUrl

        override fun connect(url: String?, info: Properties?): Connection? {
            if (!acceptsURL(url)) return null
            throw SQLException("simulated connection unavailable", "08001")
        }

        override fun getPropertyInfo(
            url: String?,
            info: Properties?
        ): Array<DriverPropertyInfo> = emptyArray()

        override fun getMajorVersion(): Int = 1
        override fun getMinorVersion(): Int = 0
        override fun jdbcCompliant(): Boolean = false
        override fun getParentLogger(): Logger = Logger.getLogger("b3b2b-unavailable")
    }

    private fun connection(): Connection =
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        )
}
