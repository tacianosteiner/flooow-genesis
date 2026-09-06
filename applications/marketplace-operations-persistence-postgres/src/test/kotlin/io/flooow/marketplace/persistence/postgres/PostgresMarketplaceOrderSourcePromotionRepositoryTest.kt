package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceReadResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicFact
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderIdentityResolution
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderOccurrencePromotionOutcome
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderOccurrencePromotionWriteResult
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderPromotionIdentifierFactory
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderSourceKey
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderSourcePendingResult
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderSourcePromotionBatchResult
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderSourcePromotionCandidate
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderSourcePromotionContract
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderSourcePromotionService
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.sql.Timestamp
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.UUID
import java.util.concurrent.Callable
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import java.util.concurrent.atomic.AtomicLong
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresMarketplaceOrderSourcePromotionRepositoryTest {
    private lateinit var postgres: PostgreSQLContainer
    private lateinit var configuration: PostgresConfiguration
    private lateinit var repository: PostgresMarketplaceOrderSourcePromotionRepository
    private val ids = AtomicLong(1)
    private val now = Instant.parse("2026-09-06T22:30:00.123456Z")
    private val clock = Clock.fixed(now, ZoneOffset.UTC)

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
            .dataSource(configuration.url, configuration.user, configuration.password)
            .load()
            .migrate()
        repository = PostgresMarketplaceOrderSourcePromotionRepository(configuration)
    }

    @AfterTest
    fun stopPostgres() = postgres.stop()

    @Test
    fun `V022 is additive append only and contains no forbidden source payload`() {
        assertEquals(
            "022",
            text(
                "SELECT version FROM flyway_schema_history " +
                    "WHERE version='022' AND success"
            )
        )

        assertEquals(
            setOf(
                "marketplace_order_identity_registry",
                "marketplace_order_occurrence_source_promotion"
            ),
            strings(
                "SELECT table_name FROM information_schema.tables " +
                    "WHERE table_schema='public' AND table_name IN (" +
                    "'marketplace_order_identity_registry'," +
                    "'marketplace_order_occurrence_source_promotion')"
            ).toSet()
        )

        val columns = strings(
            "SELECT column_name FROM information_schema.columns " +
                "WHERE table_name IN (" +
                "'marketplace_order_identity_registry'," +
                "'marketplace_order_occurrence_source_promotion')"
        ).map(String::lowercase)

        listOf(
            "raw_json",
            "access_token",
            "refresh_token",
            "client_secret",
            "buyer",
            "email",
            "phone",
            "total_amount",
            "paid_amount",
            "sale_fee"
        ).forEach { forbidden ->
            assertFalse(columns.any { it.contains(forbidden) })
        }

        assertEquals(
            setOf(
                "marketplace_order_identity_registry",
                "marketplace_order_occurrence_source_promotion"
            ),
            strings(
                "SELECT event_object_table FROM information_schema.triggers " +
                    "WHERE trigger_name LIKE 'protect_marketplace_order_%_mutation' " +
                    "ORDER BY event_object_table"
            ).toSet()
        )
    }

    @Test
    fun `same external identity across connections converges and currency conflict is explicit`() {
        val org = organization()
        val connectionA = connection(org)
        val connectionB = connection(org)
        val first = source(org, connectionA, 0, "external-1", "BRL", now.minusSeconds(3600))
        val second = source(org, connectionB, 0, "external-1", "BRL", now.minusSeconds(3600))

        val winner = MarketplaceOrderId(uuid())
        val loser = MarketplaceOrderId(uuid())

        val firstResult = assertIs<MarketplaceOrderIdentityResolution.Resolved>(
            repository.resolveOrAllocate(first, winner, now)
        )
        val secondResult = assertIs<MarketplaceOrderIdentityResolution.Resolved>(
            repository.resolveOrAllocate(second, loser, now)
        )

        assertTrue(firstResult.allocatedNow)
        assertFalse(secondResult.allocatedNow)
        assertEquals(firstResult.orderId, secondResult.orderId)
        assertNotEquals(loser, secondResult.orderId)

        val conflictSource = source(
            org,
            connectionB,
            1,
            "external-1",
            "USD",
            now.minusSeconds(3600)
        )
        val conflict = assertIs<MarketplaceOrderIdentityResolution.Conflict>(
            repository.resolveOrAllocate(conflictSource, MarketplaceOrderId(uuid()), now)
        )
        assertEquals(firstResult.orderId, conflict.existingOrderId)

        assertEquals(
            MarketplaceOrderOccurrencePromotionWriteResult.APPLIED,
            repository.markTerminal(
                conflictSource,
                conflict.existingOrderId,
                MarketplaceOrderOccurrencePromotionOutcome.IDENTITY_CONFLICT,
                now
            )
        )
    }

    @Test
    fun `concurrent first allocation converges to one durable internal order id`() {
        val org = organization()
        val connection = connection(org)
        val candidate = source(
            org,
            connection,
            0,
            "concurrent-order",
            "BRL",
            now.minusSeconds(3600)
        )
        val proposedA = MarketplaceOrderId(uuid())
        val proposedB = MarketplaceOrderId(uuid())
        val start = CountDownLatch(1)
        val executor = Executors.newFixedThreadPool(2)

        val results = try {
            val futureA = executor.submit(
                Callable {
                    check(start.await(5, TimeUnit.SECONDS)) {
                        "Concurrent identity allocation start barrier timed out"
                    }
                    repository.resolveOrAllocate(candidate, proposedA, now)
                }
            )
            val futureB = executor.submit(
                Callable {
                    check(start.await(5, TimeUnit.SECONDS)) {
                        "Concurrent identity allocation start barrier timed out"
                    }
                    repository.resolveOrAllocate(candidate, proposedB, now)
                }
            )

            start.countDown()

            listOf(
                futureA.get(30, TimeUnit.SECONDS),
                futureB.get(30, TimeUnit.SECONDS)
            )
        } catch (error: TimeoutException) {
            throw AssertionError(
                "Concurrent identity allocation did not converge within 30 seconds",
                error
            )
        } finally {
            executor.shutdownNow()
            check(executor.awaitTermination(10, TimeUnit.SECONDS)) {
                "Concurrent identity allocation executor did not terminate"
            }
        }

        val resolved = results.map {
            assertIs<MarketplaceOrderIdentityResolution.Resolved>(it)
        }
        assertEquals(1, resolved.count { it.allocatedNow })
        assertEquals(1, resolved.map { it.orderId }.toSet().size)
    }

    @Test
    fun `pending source work set is ordered and terminal replay is fail closed`() {
        val org = organization()
        val connection = connection(org)
        val second = source(org, connection, 2, "order-2", "BRL", now.minusSeconds(3600))
        val first = source(org, connection, 1, "order-1", "BRL", now.minusSeconds(3700))

        val pending = assertIs<MarketplaceOrderSourcePendingResult.Available>(
            repository.pending(org, connection, 10)
        ).candidates
        assertEquals(listOf(1L, 2L), pending.map { it.sourceKey.inputProgressVersion })

        val identity = assertIs<MarketplaceOrderIdentityResolution.Resolved>(
            repository.resolveOrAllocate(first, MarketplaceOrderId(uuid()), now)
        )

        assertEquals(
            MarketplaceOrderOccurrencePromotionWriteResult.APPLIED,
            repository.markTerminal(
                first,
                identity.orderId,
                MarketplaceOrderOccurrencePromotionOutcome.PROMOTED,
                now
            )
        )
        assertEquals(
            MarketplaceOrderOccurrencePromotionWriteResult.ALREADY_APPLIED,
            repository.markTerminal(
                first,
                identity.orderId,
                MarketplaceOrderOccurrencePromotionOutcome.PROMOTED,
                now.plusSeconds(1)
            )
        )
        assertEquals(
            MarketplaceOrderOccurrencePromotionWriteResult.CONFLICT,
            repository.markTerminal(
                first,
                identity.orderId,
                MarketplaceOrderOccurrencePromotionOutcome.DUPLICATE,
                now.plusSeconds(2)
            )
        )

        val restarted = PostgresMarketplaceOrderSourcePromotionRepository(configuration)
        val remaining = assertIs<MarketplaceOrderSourcePendingResult.Available>(
            restarted.pending(org, connection, 10)
        ).candidates
        assertEquals(listOf(second.sourceKey), remaining.map { it.sourceKey })
    }

    @Test
    fun `real evidence repository promotes duplicate and conflict without financial components`() {
        val org = organization()
        val connection = connection(org)
        val first = source(org, connection, 0, "live-order", "BRL", now.minusSeconds(7200))

        val orderSequence = AtomicLong(1000)
        val observationSequence = AtomicLong(2000)
        val service = MarketplaceOrderSourcePromotionService(
            repository,
            PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration),
            clock,
            MarketplaceOrderPromotionIdentifierFactory {
                MarketplaceOrderId(UUID(0, orderSequence.getAndIncrement()))
            },
            MarketplaceOrderPromotionIdentifierFactory {
                MarketplaceEconomicEvidenceObservationId.parse(
                    UUID(0, observationSequence.getAndIncrement()).toString()
                )
            }
        )

        val promoted = assertIs<MarketplaceOrderSourcePromotionBatchResult.Completed>(
            service.promotePending(org, connection, 10)
        )
        assertEquals(1, promoted.promoted)

        val duplicateSource = source(
            org,
            connection,
            1,
            "live-order",
            "BRL",
            first.dateCreated
        )
        val duplicate = assertIs<MarketplaceOrderSourcePromotionBatchResult.Completed>(
            service.promotePending(org, connection, 10)
        )
        assertEquals(1, duplicate.duplicates)

        val conflictSource = source(
            org,
            connection,
            2,
            "live-order",
            "BRL",
            first.dateCreated.plusSeconds(60)
        )
        val conflict = assertIs<MarketplaceOrderSourcePromotionBatchResult.Completed>(
            service.promotePending(org, connection, 10)
        )
        assertEquals(1, conflict.evidenceConflicts)

        assertEquals(
            listOf("PROMOTED", "DUPLICATE", "EVIDENCE_CONFLICT"),
            strings(
                "SELECT outcome FROM marketplace_order_occurrence_source_promotion " +
                    "WHERE organization_id='${org.value}' " +
                    "ORDER BY source_input_progress_version"
            )
        )

        val orderId = MarketplaceOrderId(
            UUID.fromString(
                text(
                    "SELECT marketplace_order_id::text " +
                        "FROM marketplace_order_identity_registry " +
                        "WHERE organization_id='${org.value}'"
                )
            )
        )
        val subject = MarketplaceEconomicEvidenceSubject(
            org,
            orderId,
            MarketplaceOrderSourcePromotionContract.MARKETPLACE,
            MarketplaceExternalOrderId("live-order"),
            MarketplaceCurrency("BRL")
        )
        val evidence = assertIs<MarketplaceIndependentEconomicEvidenceReadResult.Found>(
            PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration)
                .find(subject)
        ).versionedEvidence.evidence

        assertEquals(1, evidence.activeFacts.size)
        val occurrence = assertIs<MarketplaceIndependentEconomicFact.OrderOccurrence>(
            evidence.activeFacts.single()
        ).observation
        assertEquals(first.dateCreated, occurrence.occurredAt)
        assertEquals(first.observedAt, occurrence.observedAt)
        assertEquals(EconomicSourceKind.MARKETPLACE, occurrence.source.kind)
        assertTrue(evidence.activeFacts.none { it is MarketplaceIndependentEconomicFact.Component })

        assertEquals(
            "live-order",
            text(
                "SELECT external_order_ref " +
                    "FROM integration_mercado_livre_order_source_observation " +
                    "WHERE organization_id='${org.value}' " +
                    "AND input_progress_version=0"
            )
        )

        assertEquals(
            duplicateSource.externalOrderId,
            MarketplaceExternalOrderId("live-order")
        )
        assertEquals(
            conflictSource.externalOrderId,
            MarketplaceExternalOrderId("live-order")
        )
    }

    @Test
    fun `identity and promotion are organization isolated and registry is immutable`() {
        val orgA = organization()
        val orgB = organization()
        val sourceA = source(
            orgA,
            connection(orgA),
            0,
            "shared-external",
            "BRL",
            now.minusSeconds(3600)
        )
        val sourceB = source(
            orgB,
            connection(orgB),
            0,
            "shared-external",
            "BRL",
            now.minusSeconds(3600)
        )

        val a = assertIs<MarketplaceOrderIdentityResolution.Resolved>(
            repository.resolveOrAllocate(sourceA, MarketplaceOrderId(uuid()), now)
        )
        val b = assertIs<MarketplaceOrderIdentityResolution.Resolved>(
            repository.resolveOrAllocate(sourceB, MarketplaceOrderId(uuid()), now)
        )
        assertNotEquals(a.orderId, b.orderId)

        assertFailsWith<SQLException> {
            execute(
                "UPDATE marketplace_order_identity_registry " +
                    "SET currency='USD' WHERE organization_id=?",
                orgA.value
            )
        }
    }

    private fun organization(): OrganizationId {
        val org = OrganizationId(uuid())
        execute(
            "INSERT INTO integration_organization " +
                "(organization_id,status,created_at,updated_at) " +
                "VALUES (?,'ACTIVE',?,?)",
            org.value,
            Timestamp.from(now),
            Timestamp.from(now)
        )
        return org
    }

    private fun connection(org: OrganizationId): IntegrationConnectionId {
        val connection = IntegrationConnectionId(uuid())
        execute(
            "INSERT INTO integration_connection (" +
                "organization_id,connection_id,provider_key,credential_kind,status," +
                "binding_version,created_at,updated_at" +
                ") VALUES (?,?,'br.com.mercadolivre','OAUTH2_AUTHORIZATION_CODE'," +
                "'ACTIVE',1,?,?)",
            org.value,
            connection.value,
            Timestamp.from(now),
            Timestamp.from(now)
        )

        execute(
            "INSERT INTO integration_connector_progress (" +
                "organization_id,connection_id,capability,progress_version," +
                "progress_envelope,exhausted,last_observed_at,updated_at" +
                ") VALUES (?,?,?,1,?,false,?,?)",
            org.value,
            connection.value,
            MarketplaceOrderSourcePromotionContract.CAPABILITY,
            byteArrayOf(1),
            Timestamp.from(now),
            Timestamp.from(now)
        )
        return connection
    }

    private fun source(
        org: OrganizationId,
        connection: IntegrationConnectionId,
        version: Long,
        external: String,
        currency: String,
        dateCreated: Instant
    ): MarketplaceOrderSourcePromotionCandidate {
        val observed = now.plusSeconds(version)
        val key = ByteArray(32) { index ->
            ((version + index + connection.value.leastSignificantBits) and 0xff).toByte()
        }

        execute(
            "INSERT INTO integration_connector_page_commit (" +
                "organization_id,connection_id,capability,input_progress_version," +
                "page_commit_key,record_count,exhausted,observed_at,committed_at" +
                ") VALUES (?,?,?,?,?,1,false,?,?)",
            org.value,
            connection.value,
            MarketplaceOrderSourcePromotionContract.CAPABILITY,
            version,
            key,
            Timestamp.from(observed),
            Timestamp.from(observed)
        )

        execute(
            "INSERT INTO integration_mercado_livre_order_source_observation (" +
                "organization_id,connection_id,capability,input_progress_version," +
                "record_ordinal,external_order_ref,provider_status,date_created," +
                "date_last_updated,date_closed,currency,total_amount,paid_amount," +
                "pack_ref,shipping_ref,observed_at" +
                ") VALUES (?,?,?,?,0,?,'paid',?,?,?, ?,100.00,100.00,NULL,NULL,?)",
            org.value,
            connection.value,
            MarketplaceOrderSourcePromotionContract.CAPABILITY,
            version,
            external,
            Timestamp.from(dateCreated),
            Timestamp.from(observed),
            Timestamp.from(observed),
            currency,
            Timestamp.from(observed)
        )

        return MarketplaceOrderSourcePromotionCandidate(
            MarketplaceOrderSourceKey(
                org,
                connection,
                MarketplaceOrderSourcePromotionContract.CAPABILITY,
                version,
                0
            ),
            MarketplaceExternalOrderId(external),
            MarketplaceCurrency(currency),
            dateCreated,
            observed
        )
    }

    private fun uuid(): UUID = UUID(0, ids.getAndIncrement())

    private fun execute(sql: String, vararg values: Any?) {
        connection().use { connection ->
            connection.prepareStatement(sql).use { statement ->
                values.forEachIndexed { index, value ->
                    when (value) {
                        is ByteArray -> statement.setBytes(index + 1, value)
                        else -> statement.setObject(index + 1, value)
                    }
                }
                statement.executeUpdate()
            }
        }
    }

    private fun text(sql: String): String = connection().use { connection ->
        connection.createStatement().use { statement ->
            statement.executeQuery(sql).use {
                check(it.next())
                it.getString(1)
            }
        }
    }

    private fun strings(sql: String): List<String> = connection().use { connection ->
        connection.createStatement().use { statement ->
            statement.executeQuery(sql).use { result ->
                buildList {
                    while (result.next()) add(result.getString(1))
                }
            }
        }
    }

    private fun connection(): Connection = DriverManager.getConnection(
        configuration.url,
        configuration.user,
        configuration.password
    )
}