package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.ledger.*
import io.flooow.marketplace.operations.economics.ledger.materialization.*
import io.flooow.marketplace.operations.economics.promotion.*
import io.flooow.organization.OrganizationId
import java.math.BigDecimal
import java.time.Instant
import java.util.UUID
import javax.sql.DataSource
import kotlin.test.AfterTest
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class ControlledDurableMercadoLivreLedgerMaterializationProofTest {
    private lateinit var postgres: PostgreSQLContainer
    private lateinit var configuration: PostgresConfiguration
    private lateinit var dataSource: DataSource

    @BeforeTest
    fun start() {
        postgres = PostgreSQLContainer("postgres:18.4").also { it.start() }
        configuration = PostgresConfiguration(postgres.jdbcUrl, postgres.username, postgres.password)
        dataSource = PostgresDataSources.create(configuration)
        Flyway.configure().dataSource(configuration.url, configuration.user, configuration.password)
            .load().migrate()
    }

    @AfterTest
    fun stop() = postgres.stop()

    @Test
    fun `real Mercado Livre durable evidence materializes once through processor and commit replay`() {
        val organizationId = OrganizationId(UUID(0, 93_001))
        val otherOrganizationId = OrganizationId(UUID(0, 93_002))
        val connectionId = IntegrationConnectionId(UUID(0, 93_010))
        val orderId = MarketplaceOrderId(UUID(0, 93_101))
        val observationId = MarketplaceEconomicEvidenceObservationId.parse(UUID(0, 93_201).toString())
        val componentId = EconomicComponentId(UUID(0, 93_202))
        val externalOrderId = MarketplaceExternalOrderId("290000009301")
        val currency = MarketplaceCurrency("BRL")
        val occurredAt = Instant.parse("2026-09-21T12:00:00.123456Z")
        val observedAt = Instant.parse("2026-09-21T12:30:00.123456Z")

        seedOrganization(organizationId)
        seedOrganization(otherOrganizationId)
        seedConnection(organizationId, connectionId)
        seedClosedOrderSource(organizationId, connectionId, externalOrderId, currency, occurredAt, observedAt)
        seedOrderIdentity(organizationId, connectionId, orderId, externalOrderId, currency)

        val observation = MarketplaceEconomicComponentObservation(
            id = observationId,
            subject = MarketplaceEconomicEvidenceSubject(
                organizationId, orderId, MarketplaceKey("mercado-livre"), externalOrderId, currency
            ),
            family = MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
            component = EconomicComponent(
                organizationId, componentId, orderId, EconomicComponentType.REVENUE,
                EconomicDirection.ADDITION, MarketplaceMoney.parse(currency, "123.45"),
                EconomicSource(
                    EconomicSourceKind.MARKETPLACE,
                    EconomicSourceSystemKey("br.com.mercadolivre"),
                    EconomicExternalReferenceState.Present(EconomicExternalReference(externalOrderId.value))
                ),
                occurredAt,
                EconomicEvidenceQuality.CONFIRMED
            ),
            coverageClaim = EconomicComponentCoverage.PARTIAL,
            observedAt = observedAt
        )

        val evidence = PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration)
        assertIs<MarketplaceIndependentEconomicEvidencePersistResult.Applied>(
            evidence.apply(
                MarketplaceEconomicEvidenceVersion.ZERO,
                MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                    MarketplaceIndependentEconomicFact.Component(observation)
                )
            )
        )

        val promotion = PostgresMarketplaceOrderSourcePromotionRepository(configuration)
        assertEquals(
            MarketplaceOrderRevenuePromotionWriteResult.APPLIED,
            promotion.markRevenueTerminal(
                MarketplaceOrderRevenuePromotionCandidate(
                    sourceKey = MarketplaceOrderSourceKey(
                        organizationId, connectionId, MarketplaceOrderSourcePromotionContract.CAPABILITY, 1, 0
                    ),
                    externalOrderId = externalOrderId,
                    sourceCurrency = currency,
                    identityCurrency = currency,
                    orderId = orderId,
                    totalAmount = BigDecimal("123.45"),
                    dateClosed = occurredAt,
                    observedAt = observedAt
                ),
                MarketplaceOrderRevenuePromotionOutcome.PROMOTED,
                observationId,
                observedAt.plusSeconds(1)
            )
        )

        val feed = PostgresMarketplaceEconomicEvidenceChangeFeed(configuration)
        val authoritySource = PostgresMercadoLivreClosedOrderRevenueAuthoritySource(dataSource)
        val authority = MercadoLivreClosedOrderRevenueBasisAuthority(authoritySource)
        val ledger = PostgresMarketplaceFinancialLedgerRepository(configuration)
        val commitStore = PostgresGovernedFinancialLedgerMaterializationCommitStore(dataSource, ledger)
        val processor = MarketplaceFinancialLedgerMaterializationProcessor(
            updateReader = evidence,
            changeFeed = feed,
            authorityResolver = authority::resolve,
            commitStore = commitStore
        )

        val seededFactChange =
            assertIs<MarketplaceEconomicEvidenceChangeFeedResult.Success<List<MarketplaceEconomicEvidenceChange>>>(
                feed.changesSince(organizationId, ChangeSequenceCheckpoint.NONE, 1)
            ).value.single()
        assertEquals(MarketplaceEconomicEvidenceChangeKind.FACT, seededFactChange.changeKind)
        assertEquals(observationId, seededFactChange.updateId)
        val seededFactChangeSequence = seededFactChange.changeSequence

        val first = assertIs<MarketplaceFinancialLedgerMaterializationProcessorResult.Success>(
            processor.processBatch(organizationId, 1)
        )
        assertEquals(1, first.processedChanges)
        assertEquals(1, first.materialized)
        assertEquals(0, first.alreadyMaterialized)
        assertEquals(0, first.notEligible)
        assertEquals(seededFactChangeSequence, first.checkpoint)
        assertEquals(first.checkpoint, currentCheckpoint(feed, organizationId))
        assertEquals(1, traceCount(organizationId, orderId))
        assertEquals(1, entryCount(organizationId, orderId))
        assertEquals(1, lineageCount(organizationId, orderId, observationId))
        assertEquals(0, traceCount(otherOrganizationId, orderId))
        assertEquals(0, entryCount(otherOrganizationId, orderId))
        assertEquals(0, lineageCount(otherOrganizationId, orderId, observationId))
        assertIs<FinancialTraceReadResult.NotFound>(ledger.findByOrder(otherOrganizationId, orderId))

        val trace = assertIs<FinancialTraceReadResult.Found>(ledger.findByOrder(organizationId, orderId)).trace
        val entry = trace.entries.single()
        val lineage = lineage(organizationId, orderId, observationId)
        assertEquals(FinancialLedgerBasis.ACTUAL, entry.basis)
        assertEquals(FinancialLedgerStage.SALE, entry.stage)
        assertEquals(FinancialLedgerMaterializationPolicyVersion.V1.value, lineage.policyVersion)
        assertEquals(MercadoLivreClosedOrderRevenueBasisAuthority.AUTHORITY_SEMANTIC_VERSION.value, lineage.semanticVersion)
        assertEquals(observationId.valueForPersistence(), lineage.sourceAuthorityIdentity)
        assertEquals(trace.id.valueForPersistence(), lineage.traceId)
        assertEquals(entry.id.valueForPersistence(), lineage.entryId)

        assertIs<MarketplaceFinancialLedgerMaterializationProcessorResult.NoChanges>(
            processor.processBatch(organizationId, 1)
        )
        assertEquals(first.checkpoint, currentCheckpoint(feed, organizationId))
        assertEquals(1, traceCount(organizationId, orderId))
        assertEquals(1, entryCount(organizationId, orderId))
        assertEquals(1, lineageCount(organizationId, orderId, observationId))

        val canonicalObservation = assertIs<MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found>(
            authoritySource.findProofs(organizationId, observationId, orderId)
        ).proofs.single().durableObservation
        val decision = authority.resolve(organizationId, canonicalObservation)
        val plan = assertIs<GovernedFinancialLedgerComponentMaterializationResult.Eligible>(
            GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(organizationId, canonicalObservation, decision)
        ).plan
        val replay = assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(
            commitStore.commit(plan)
        )
        assertEquals(trace.id, replay.traceId)
        assertEquals(entry.id, replay.entryId)
        val replayLineage = lineage(organizationId, orderId, observationId)
        assertEquals(lineage.sourceAuthorityIdentity, replayLineage.sourceAuthorityIdentity)
        assertEquals(lineage.semanticVersion, replayLineage.semanticVersion)
        assertEquals(lineage.policyVersion, replayLineage.policyVersion)
        assertEquals(lineage.traceId, replayLineage.traceId)
        assertEquals(lineage.entryId, replayLineage.entryId)
        assertEquals(replay.traceId.valueForPersistence(), replayLineage.traceId)
        assertEquals(replay.entryId.valueForPersistence(), replayLineage.entryId)
        assertEquals(1, traceCount(organizationId, orderId))
        assertEquals(1, entryCount(organizationId, orderId))
        assertEquals(1, lineageCount(organizationId, orderId, observationId))
    }

    private fun seedOrganization(organizationId: OrganizationId) = execute(
        "INSERT INTO integration_organization (organization_id,status,created_at,updated_at) VALUES ('${organizationId.value}','ACTIVE','2026-09-21T11:00:00Z','2026-09-21T11:00:00Z')"
    )

    private fun seedConnection(organizationId: OrganizationId, connectionId: IntegrationConnectionId) {
        execute("INSERT INTO integration_connection (organization_id,connection_id,provider_key,credential_kind,status,binding_version,created_at,updated_at) VALUES ('${organizationId.value}','${connectionId.value}','br.com.mercadolivre','OAUTH2_AUTHORIZATION_CODE','ACTIVE',1,'2026-09-21T11:00:00Z','2026-09-21T11:00:00Z')")
        execute("INSERT INTO integration_connector_progress (organization_id,connection_id,capability,progress_version,progress_envelope,exhausted,last_observed_at,updated_at) VALUES ('${organizationId.value}','${connectionId.value}','marketplace-economic.order-source',1,decode('01','hex'),false,'2026-09-21T11:00:00Z','2026-09-21T11:00:00Z')")
    }

    private fun seedClosedOrderSource(organizationId: OrganizationId, connectionId: IntegrationConnectionId, externalOrderId: MarketplaceExternalOrderId, currency: MarketplaceCurrency, occurredAt: Instant, observedAt: Instant) {
        execute("INSERT INTO integration_connector_page_commit (organization_id,connection_id,capability,input_progress_version,page_commit_key,record_count,exhausted,observed_at,committed_at) VALUES ('${organizationId.value}','${connectionId.value}','marketplace-economic.order-source',1,decode('${"01".repeat(32)}','hex'),1,false,'$observedAt','$observedAt')")
        execute("INSERT INTO integration_mercado_livre_order_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,provider_status,date_created,date_last_updated,date_closed,currency,total_amount,paid_amount,pack_ref,shipping_ref,observed_at) VALUES ('${organizationId.value}','${connectionId.value}','marketplace-economic.order-source',1,0,'${externalOrderId.value}','paid','2026-09-21T11:30:00Z','$observedAt','$occurredAt','${currency.code}',123.45,123.45,NULL,NULL,'$observedAt')")
    }

    private fun seedOrderIdentity(organizationId: OrganizationId, connectionId: IntegrationConnectionId, orderId: MarketplaceOrderId, externalOrderId: MarketplaceExternalOrderId, currency: MarketplaceCurrency) = execute(
        "INSERT INTO marketplace_order_identity_registry (organization_id,marketplace_key,external_order_id,marketplace_order_id,currency,allocated_at,first_source_connection_id,first_source_capability,first_source_input_progress_version,first_source_record_ordinal) VALUES ('${organizationId.value}','mercado-livre','${externalOrderId.value}','${orderId.value}','${currency.code}','2026-09-21T11:45:00Z','${connectionId.value}','marketplace-economic.order-source',1,0)"
    )

    private fun currentCheckpoint(feed: PostgresMarketplaceEconomicEvidenceChangeFeed, organizationId: OrganizationId): ChangeSequenceCheckpoint =
        assertIs<MarketplaceEconomicEvidenceChangeFeedResult.Success<ChangeSequenceCheckpoint>>(
            feed.currentCheckpoint(organizationId, MarketplaceFinancialLedgerMaterializationProcessor.PROJECTION_NAME)
        ).value

    private fun traceCount(organizationId: OrganizationId, orderId: MarketplaceOrderId) = count(
        "SELECT count(*) FROM marketplace_financial_trace WHERE organization_id=? AND order_id=?", organizationId.value, orderId.value
    )

    private fun entryCount(organizationId: OrganizationId, orderId: MarketplaceOrderId) = count(
        "SELECT count(*) FROM marketplace_financial_ledger_entry entry JOIN marketplace_financial_trace trace ON trace.organization_id=entry.organization_id AND trace.trace_id=entry.trace_id WHERE trace.organization_id=? AND trace.order_id=?", organizationId.value, orderId.value
    )

    private fun lineageCount(organizationId: OrganizationId, orderId: MarketplaceOrderId, observationId: MarketplaceEconomicEvidenceObservationId) = count(
        "SELECT count(*) FROM marketplace_financial_ledger_materialization_lineage WHERE organization_id=? AND source_order_id=? AND source_authority_identity=?", organizationId.value, orderId.value, observationId.valueForPersistence()
    )

    private fun lineage(organizationId: OrganizationId, orderId: MarketplaceOrderId, observationId: MarketplaceEconomicEvidenceObservationId): Lineage = dataSource.connection.use { connection ->
        connection.prepareStatement("SELECT source_authority_identity,source_authority_semantic_version,materialization_policy_version,trace_id,ledger_entry_id FROM marketplace_financial_ledger_materialization_lineage WHERE organization_id=? AND source_order_id=? AND source_authority_identity=?").use { statement ->
            statement.setObject(1, organizationId.value)
            statement.setObject(2, orderId.value)
            statement.setObject(3, observationId.valueForPersistence())
            statement.executeQuery().use { result ->
                check(result.next())
                Lineage(result.getObject(1, UUID::class.java), result.getString(2), result.getString(3), result.getObject(4, UUID::class.java), result.getObject(5, UUID::class.java))
            }
        }
    }

    private fun count(sql: String, vararg values: Any): Int = dataSource.connection.use { connection ->
        connection.prepareStatement(sql).use { statement ->
            values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }
            statement.executeQuery().use { result -> check(result.next()); result.getInt(1) }
        }
    }

    private fun execute(sql: String) { dataSource.connection.use { it.createStatement().use { statement -> statement.executeUpdate(sql) } } }

    private data class Lineage(val sourceAuthorityIdentity: UUID, val semanticVersion: String, val policyVersion: String, val traceId: UUID, val entryId: UUID)
}
