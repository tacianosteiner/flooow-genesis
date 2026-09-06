package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssembler
import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssemblyNotReadyReason
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.ChangeSequenceCheckpoint
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceVersion
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionCursor
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionReadResult
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionPage
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionRecord
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionWriteResult
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceState
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.junit.jupiter.api.AfterAll
import org.junit.jupiter.api.BeforeAll
import org.junit.jupiter.api.TestInstance
import org.testcontainers.postgresql.PostgreSQLContainer

@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class PostgresMarketplaceSalesIntelligenceProjectionTest {
    private lateinit var postgres: PostgreSQLContainer
    private lateinit var configuration: PostgresConfiguration
    private lateinit var projection: PostgresMarketplaceSalesIntelligenceProjection
    private val baseTime = Instant.parse("2026-09-06T12:00:00.123456Z")

    @BeforeAll
    fun startPostgres() {
        postgres = PostgreSQLContainer("postgres:18.4")
        postgres.start()
        configuration = PostgresConfiguration(postgres.jdbcUrl, postgres.username, postgres.password)
        Flyway.configure()
            .dataSource(configuration.url, configuration.user, configuration.password)
            .load()
            .migrate()
        projection = PostgresMarketplaceSalesIntelligenceProjection(configuration)
    }

    @AfterAll
    fun stopPostgres() = postgres.stop()

    @BeforeTest
    fun clearData() {
        connection().use { connection ->
            connection.createStatement().use {
                it.execute("TRUNCATE integration_organization CASCADE")
            }
        }
        projection = PostgresMarketplaceSalesIntelligenceProjection(configuration)
    }

    @Test
    fun `V018 creates bounded projection schema and keyset index`() {
        connection().use { connection ->
            val version = connection.prepareStatement(
                "SELECT success FROM flyway_schema_history WHERE version='018'"
            ).use { statement ->
                statement.executeQuery().use { result ->
                    assertTrue(result.next())
                    result.getBoolean(1)
                }
            }
            assertTrue(version)

            val index = connection.prepareStatement(
                "SELECT indexdef FROM pg_indexes " +
                    "WHERE tablename='marketplace_sales_intelligence_projection' " +
                    "AND indexname='marketplace_sales_intelligence_org_page_idx'"
            ).use { statement ->
                statement.executeQuery().use { result ->
                    assertTrue(result.next())
                    result.getString(1)
                }
            }
            assertTrue(index.contains("organization_id"))
            assertTrue(index.contains("projected_at DESC"))
            assertTrue(index.contains("marketplace_order_id DESC"))
        }
    }

    @Test
    fun `unresolved state round trips and equal or stale sequences are no ops`() {
        val organization = createOrganization(1)
        val order = createSubject(organization, 11)
        val newest = unresolved(organization, order, 5, baseTime)

        assertIs<MarketplaceSalesIntelligenceProjectionWriteResult.Applied>(
            projection.materializeIfNewer(newest)
        )
        assertIs<MarketplaceSalesIntelligenceProjectionWriteResult.NoOpAlreadyCurrent>(
            projection.materializeIfNewer(newest.copy(projectedAt = baseTime.plusSeconds(1)))
        )
        assertIs<MarketplaceSalesIntelligenceProjectionWriteResult.NoOpAlreadyCurrent>(
            projection.materializeIfNewer(
                newest.copy(
                    lastAppliedChangeSequence = ChangeSequenceCheckpoint(4),
                    projectedAt = baseTime.plusSeconds(2)
                )
            )
        )

        val durable = assertIs<MarketplaceSalesIntelligenceProjectionReadResult.Success<MarketplaceSalesIntelligenceProjectionRecord?>>(
            projection.detailByOrganizationAndSubject(organization, order)
        ).value
        assertNotNull(durable)
        assertEquals(ChangeSequenceCheckpoint(5), durable.lastAppliedChangeSequence)
        assertEquals(baseTime, durable.projectedAt)
        assertIs<MarketplaceSalesIntelligenceState.Unresolved>(durable.state)
    }

    @Test
    fun `newer unresolved atomically replaces older current state`() {
        val organization = createOrganization(2)
        val order = createSubject(organization, 21)
        projection.materializeIfNewer(unresolved(organization, order, 1, baseTime))

        val newer = unresolved(
            organization,
            order,
            2,
            baseTime.plusSeconds(1),
            MarketplaceEconomicTruthAssemblyNotReadyReason.ORDER_OCCURRED_AT_CONFLICT
        )
        assertIs<MarketplaceSalesIntelligenceProjectionWriteResult.Applied>(
            projection.materializeIfNewer(newer)
        )

        val durable = assertIs<MarketplaceSalesIntelligenceProjectionReadResult.Success<MarketplaceSalesIntelligenceProjectionRecord?>>(
            projection.currentBySubject(organization, order)
        ).value
        assertNotNull(durable)
        assertEquals(ChangeSequenceCheckpoint(2), durable.lastAppliedChangeSequence)
        val state = assertIs<MarketplaceSalesIntelligenceState.Unresolved>(durable.state)
        assertEquals(
            setOf(MarketplaceEconomicTruthAssemblyNotReadyReason.ORDER_OCCURRED_AT_CONFLICT),
            state.reasons
        )
    }

    @Test
    fun `organization scoped detail and keyset pagination remain isolated and stable`() {
        val firstOrg = createOrganization(3)
        val secondOrg = createOrganization(4)
        val firstOrders = (1L..6L).map { createSubject(firstOrg, 100 + it) }
        val foreign = createSubject(secondOrg, 999)

        firstOrders.forEachIndexed { index, order ->
            projection.materializeIfNewer(
                unresolved(
                    firstOrg,
                    order,
                    index.toLong() + 1,
                    baseTime.plusSeconds(index.toLong())
                )
            )
        }
        projection.materializeIfNewer(unresolved(secondOrg, foreign, 1, baseTime.plusSeconds(20)))

        val firstPage = assertIs<MarketplaceSalesIntelligenceProjectionReadResult.Success<MarketplaceSalesIntelligenceProjectionPage>>(
            projection.listByOrganization(firstOrg, null, 3)
        ).value
        assertEquals(3, firstPage.records.size)
        assertNotNull(firstPage.nextCursor)
        assertTrue(firstPage.records.all { it.organizationId == firstOrg })

        val secondPage = assertIs<MarketplaceSalesIntelligenceProjectionReadResult.Success<MarketplaceSalesIntelligenceProjectionPage>>(
            projection.listByOrganization(firstOrg, firstPage.nextCursor, 3)
        ).value
        assertEquals(3, secondPage.records.size)
        assertNull(secondPage.nextCursor)
        assertEquals(
            firstOrders.toSet(),
            (firstPage.records + secondPage.records).map { it.marketplaceOrderId }.toSet()
        )

        val foreignDetail = assertIs<MarketplaceSalesIntelligenceProjectionReadResult.Success<MarketplaceSalesIntelligenceProjectionRecord?>>(
            projection.detailByOrganizationAndSubject(firstOrg, foreign)
        ).value
        assertNull(foreignDetail)
    }

    @Test
    fun `concurrent old and new writers converge to newest sequence`() {
        val organization = createOrganization(5)
        val order = createSubject(organization, 501)
        val executor = Executors.newFixedThreadPool(2)
        try {
            val old = executor.submit<MarketplaceSalesIntelligenceProjectionWriteResult> {
                projection.materializeIfNewer(unresolved(organization, order, 10, baseTime))
            }
            val newer = executor.submit<MarketplaceSalesIntelligenceProjectionWriteResult> {
                projection.materializeIfNewer(
                    unresolved(organization, order, 11, baseTime.plusSeconds(1))
                )
            }
            old.get(30, TimeUnit.SECONDS)
            newer.get(30, TimeUnit.SECONDS)
        } finally {
            executor.shutdownNow()
        }

        val durable = assertIs<MarketplaceSalesIntelligenceProjectionReadResult.Success<MarketplaceSalesIntelligenceProjectionRecord?>>(
            projection.detailByOrganizationAndSubject(organization, order)
        ).value
        assertNotNull(durable)
        assertEquals(ChangeSequenceCheckpoint(11), durable.lastAppliedChangeSequence)
    }

    @Test
    fun `malformed durable payload fails closed after restart`() {
        val organization = createOrganization(6)
        val order = createSubject(organization, 601)
        projection.materializeIfNewer(unresolved(organization, order, 1, baseTime))

        connection().use { connection ->
            connection.prepareStatement(
                "UPDATE marketplace_sales_intelligence_projection " +
                    "SET state_payload='{}'::jsonb WHERE organization_id=? AND marketplace_order_id=?"
            ).use { statement ->
                statement.setObject(1, organization.value)
                statement.setObject(2, order.value)
                assertEquals(1, statement.executeUpdate())
            }
        }

        projection = PostgresMarketplaceSalesIntelligenceProjection(configuration)
        assertIs<MarketplaceSalesIntelligenceProjectionReadResult.IntegrityFailure>(
            projection.detailByOrganizationAndSubject(organization, order)
        )
    }

    @Test
    fun `representative volume keeps bounded indexed list and detail shapes`() {
        val organization = createOrganization(7)
        repeat(250) { index ->
            val order = createSubject(organization, 7000L + index)
            projection.materializeIfNewer(
                unresolved(
                    organization,
                    order,
                    index.toLong() + 1,
                    baseTime.plusSeconds(index.toLong())
                )
            )
        }

        val page = assertIs<MarketplaceSalesIntelligenceProjectionReadResult.Success<MarketplaceSalesIntelligenceProjectionPage>>(
            projection.listByOrganization(organization, null, 50)
        ).value
        assertEquals(50, page.records.size)
        assertNotNull(page.nextCursor)

        connection().use { connection ->
            connection.createStatement().use { it.execute("SET enable_seqscan=off") }
            val detailPlan = connection.prepareStatement(
                "EXPLAIN SELECT * FROM marketplace_sales_intelligence_projection " +
                    "WHERE organization_id=? AND marketplace_order_id=?"
            ).use { statement ->
                statement.setObject(1, organization.value)
                statement.setObject(2, page.records.first().marketplaceOrderId.value)
                statement.executeQuery().use { result ->
                    buildString {
                        while (result.next()) appendLine(result.getString(1))
                    }
                }
            }
            assertTrue(
                detailPlan.contains("marketplace_sales_intelligence_projection_pkey")
            )

            val listPlan = connection.prepareStatement(
                "EXPLAIN SELECT * FROM marketplace_sales_intelligence_projection " +
                    "WHERE organization_id=? " +
                    "ORDER BY projected_at DESC, marketplace_order_id DESC LIMIT 50"
            ).use { statement ->
                statement.setObject(1, organization.value)
                statement.executeQuery().use { result ->
                    buildString {
                        while (result.next()) appendLine(result.getString(1))
                    }
                }
            }
            assertTrue(listPlan.contains("marketplace_sales_intelligence_org_page_idx"))
        }
    }

    private fun unresolved(
        organizationId: OrganizationId,
        orderId: MarketplaceOrderId,
        sequence: Long,
        projectedAt: Instant,
        reason: MarketplaceEconomicTruthAssemblyNotReadyReason =
            MarketplaceEconomicTruthAssemblyNotReadyReason.ORDER_OCCURRED_AT_UNRESOLVED
    ) = MarketplaceSalesIntelligenceProjectionRecord(
        organizationId = organizationId,
        marketplaceOrderId = orderId,
        sourceEvidenceVersion = MarketplaceEconomicEvidenceVersion(sequence),
        state = MarketplaceSalesIntelligenceState.Unresolved(
            MarketplaceEconomicTruthAssembler.POLICY_VERSION,
            setOf(reason)
        ),
        lastAppliedChangeSequence = ChangeSequenceCheckpoint(sequence),
        projectedAt = projectedAt
    )

    private fun createOrganization(seed: Long): OrganizationId {
        val organization = OrganizationId(uuid(seed))
        connection().use { connection ->
            connection.prepareStatement(
                "INSERT INTO integration_organization " +
                    "(organization_id,status,created_at,updated_at) VALUES (?,'ACTIVE',?,?)"
            ).use { statement ->
                statement.setObject(1, organization.value)
                statement.setTimestamp(2, Timestamp.from(baseTime))
                statement.setTimestamp(3, Timestamp.from(baseTime))
                statement.executeUpdate()
            }
        }
        return organization
    }

    private fun createSubject(
        organization: OrganizationId,
        seed: Long
    ): MarketplaceOrderId {
        val order = MarketplaceOrderId(uuid(seed))
        connection().use { connection ->
            connection.prepareStatement(
                "INSERT INTO marketplace_economic_evidence_subject " +
                    "(organization_id,marketplace_order_id,marketplace_key,external_order_id,currency) " +
                    "VALUES (?,?,'mercado-livre',?,'BRL')"
            ).use { statement ->
                statement.setObject(1, organization.value)
                statement.setObject(2, order.value)
                statement.setString(3, "order-$seed")
                statement.executeUpdate()
            }
        }
        return order
    }

    private fun connection(): Connection = DriverManager.getConnection(
        configuration.url,
        configuration.user,
        configuration.password
    )

    private fun uuid(value: Long): UUID = UUID(0L, value)
}
