package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.ledger.*
import io.flooow.marketplace.operations.economics.ledger.materialization.*
import io.flooow.marketplace.operations.economics.promotion.*
import io.flooow.marketplace.operations.economics.reconciliation.*
import io.flooow.marketplace.operations.economics.reconciliation.EconomicLeakageGovernanceBlockingReason
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityState
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
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class ControlledDurableLedgerDecisionRoomBlockedProjectionProofTest {
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
    fun `real durable D4 reconciliation projects truthful BLOCKED Decision Room result`() {
        val organizationId = OrganizationId(UUID(0, 94_001))
        val otherOrganizationId = OrganizationId(UUID(0, 94_002))
        val connectionId = IntegrationConnectionId(UUID(0, 94_010))
        val orderId = MarketplaceOrderId(UUID(0, 94_101))
        val observationId = MarketplaceEconomicEvidenceObservationId.parse(UUID(0, 94_201).toString())
        val componentId = EconomicComponentId(UUID(0, 94_202))
        val externalOrderId = MarketplaceExternalOrderId("290000009401")
        val currency = MarketplaceCurrency("BRL")
        val occurredAt = Instant.parse("2026-09-21T14:00:00.123456Z")
        val observedAt = Instant.parse("2026-09-21T14:30:00.123456Z")
        val policyVersion = FinancialReconciliationPolicyVersion("d4-controlled/1")

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
        val ledgerCommitStore = PostgresGovernedFinancialLedgerMaterializationCommitStore(dataSource, ledger)
        val processor = MarketplaceFinancialLedgerMaterializationProcessor(
            updateReader = evidence,
            changeFeed = feed,
            authorityResolver = authority::resolve,
            commitStore = ledgerCommitStore
        )

        val materialized = assertIs<MarketplaceFinancialLedgerMaterializationProcessorResult.Success>(
            processor.processBatch(organizationId, 1)
        )
        assertEquals(1, materialized.processedChanges)
        assertEquals(1, materialized.materialized)

        val trace = assertIs<FinancialTraceReadResult.Found>(ledger.findByOrder(organizationId, orderId)).trace
        val ledgerEntry = trace.entries.single()
        assertEquals(FinancialLedgerBasis.ACTUAL, ledgerEntry.basis)
        assertEquals(FinancialLedgerStage.SALE, ledgerEntry.stage)
        assertEquals(MarketplaceMoney.parse(currency, "123.45"), ledgerEntry.magnitude)

        insertPolicy(organizationId, policyVersion.value, "0")
        activatePolicy(organizationId, policyVersion.value)

        val policySource = PostgresFinancialReconciliationPolicySource(configuration)
        val selected = assertIs<FinancialReconciliationPolicySelection.Selected>(
            policySource.select(
                FinancialReconciliationPolicyContext(
                    organizationId, MarketplaceKey("mercado-livre"), currency
                )
            )
        )
        assertEquals(policyVersion, selected.policy.version)
        assertEquals(currency, selected.policy.currency)
        assertEquals(
            FinancialReconciliationPolicySelection.Unavailable,
            policySource.select(
                FinancialReconciliationPolicyContext(
                    otherOrganizationId, MarketplaceKey("mercado-livre"), currency
                )
            )
        )

        val cases = PostgresDurableReconciliationCaseRepository(configuration)
        val caseCommitStore = PostgresGovernedReconciliationCaseRevisionCommitStore(configuration)
        val orchestrator = GovernedReconciliationCaseOrchestrator(cases, caseCommitStore)
        val reconciliation = GovernedFinancialReconciliationExecutionService(
            ledger = ledger,
            policySource = policySource,
            orchestrator = orchestrator
        )

        val first = assertIs<GovernedFinancialReconciliationExecutionResult.Orchestrated>(
            reconciliation.execute(organizationId, trace.id)
        )
        assertEquals(FinancialReconciliationStatus.DIVERGENCE, first.assessmentStatus)
        val created = assertIs<ReconciliationCaseOrchestrationResult.Created>(first.orchestration).value
        assertEquals(ReconciliationCaseStatus.OPEN, created.status)
        assertEquals(1L, created.revision)

        val assessmentSource = PostgresEconomicDecisionRoomReconciliationAssessmentSource(dataSource)
        val authoritySourceForDecisionRoom = PostgresEconomicDecisionRoomAuthoritySource(dataSource)
        val projectionService = EconomicDecisionRoomProjectionService(cases, authoritySourceForDecisionRoom, assessmentSource)
        val stateBeforeFirstDecisionRoomRead = durableState(organizationId, created)
        val assessmentRead = assertIs<EconomicDecisionRoomReconciliationAssessmentRead.Available>(
            assessmentSource.read(organizationId, created)
        )
        assertEquals(created.caseId, assessmentRead.binding.caseId)
        assertEquals(created.revision, assessmentRead.binding.reconciliationRevision)
        val authorityRead = assertIs<EconomicDecisionRoomAuthorityRead.Available>(
            authoritySourceForDecisionRoom.read(organizationId, created)
        )
        val authorityContext = authorityRead.context
        assertEquals(created.organizationId, authorityContext.organizationId)
        assertEquals(created.caseId, authorityContext.caseId)
        assertEquals(created.orderId, authorityContext.marketplaceOrderId)
        assertEquals(created.traceId, authorityContext.financialTraceId)
        assertEquals(created.policyVersion, authorityContext.policyVersion)
        assertEquals(created.currency, authorityContext.currency)
        assertEquals(created.revision, authorityContext.reconciliationRevision)
        val identity = requireNotNull(authorityContext.inputs.identity)
        val currencyAuthority = requireNotNull(authorityContext.inputs.currency)
        val allocation = requireNotNull(authorityContext.inputs.allocation)
        val currentness = requireNotNull(authorityContext.inputs.currentness)
        listOf(identity, currencyAuthority, allocation, currentness).forEach {
            assertEquals(EconomicTruthAuthorityState.UNRESOLVED, it.state)
            assertTrue(it.evidenceReferences.isEmpty())
        }

        val projection = assertIs<EconomicDecisionRoomProjectionReadResult.Found>(
            projectionService.read(organizationId, created.caseId)
        ).projection
        assertEquals(stateBeforeFirstDecisionRoomRead, durableState(organizationId, created))
        assertEquals(EconomicDecisionRoomAuthorityStatus.ASSEMBLED, projection.authorityStatus)
        assertEquals(EconomicDecisionRoomProjectionStatus.BLOCKED, projection.projectionStatus)
        assertEquals(false, projection.governancePermitted)
        assertEquals(
            setOf(
                EconomicLeakageGovernanceBlockingReason.IDENTITY_UNRESOLVED,
                EconomicLeakageGovernanceBlockingReason.CURRENCY_UNRESOLVED,
                EconomicLeakageGovernanceBlockingReason.ALLOCATION_UNRESOLVED,
                EconomicLeakageGovernanceBlockingReason.EVIDENCE_CURRENTNESS_UNRESOLVED
            ),
            projection.governanceBlockingReasons
        )
        assertEquals(
            setOf(
                EconomicDecisionRoomProjectionBlockingReason.GOVERNANCE_NOT_PERMITTED,
                EconomicDecisionRoomProjectionBlockingReason.LEAKAGE_UNQUANTIFIED
            ),
            projection.projectionBlockingReasons
        )
        val saleProjection = projection.stages.single { it.stage == FinancialLedgerStage.SALE }
        assertEquals(EconomicLeakageInterpretationStatus.UNQUANTIFIED, saleProjection.interpretation)
        assertEquals(EconomicDecisionRoomStageBlockingReason.GOVERNANCE_NOT_SATISFIED, saleProjection.blockingReason)
        assertNull(projection.totalQuantifiedLeakage)

        val lineage = lineageRow(organizationId, created.caseId, 1L)
        val snapshot = FinancialReconciliationAssessmentSnapshot.parse(
            lineage.snapshotSchemaVersion, lineage.snapshot
        )
        val verified = FinancialReconciliationAssessmentSnapshotCodec.rehydrate(snapshot)
        val persistedFingerprint = FinancialReconciliationAssessmentFingerprint.parsePersisted(
            lineage.fingerprintVersion, lineage.fingerprint
        )
        assertEquals(persistedFingerprint, verified.fingerprint)

        val expectedCaseId = DurableReconciliationCase.deterministicId(verified.assessment)
        assertEquals(expectedCaseId, created.caseId)

        val durable = requireNotNull(cases.find(organizationId, expectedCaseId))
        assertEquals(organizationId, durable.organizationId)
        assertEquals(trace.id, durable.traceId)
        assertEquals(orderId, durable.orderId)
        assertEquals(currency, durable.currency)
        assertEquals(policyVersion, durable.policyVersion)
        assertEquals(ReconciliationCaseStatus.OPEN, durable.status)
        assertEquals(1L, durable.revision)

        val saleStage = durable.stages.single { it.stage == FinancialLedgerStage.SALE }
        assertNull(saleStage.expected)
        assertEquals(MarketplaceMoney.parse(currency, "123.45"), saleStage.actual)
        assertTrue(saleStage.expectedEntryIds.isEmpty())
        assertEquals(listOf(ledgerEntry.id), saleStage.actualEntryIds)
        assertTrue(durable.evidenceEntryIds.contains(ledgerEntry.id))

        val assessment = verified.assessment
        assertEquals(organizationId, assessment.organizationId)
        assertEquals(trace.id, assessment.traceId)
        assertEquals(orderId, assessment.orderId)
        assertEquals(currency, assessment.currency)
        assertEquals(policyVersion, assessment.policyVersion)
        assertEquals(FinancialReconciliationStatus.DIVERGENCE, assessment.status)
        val saleLine = assessment.lines.single { it.stage == FinancialLedgerStage.SALE }
        assertEquals(FinancialReconciliationSide.NotObserved, saleLine.expected)
        val actual = assertIs<FinancialReconciliationSide.Observed>(saleLine.actual)
        assertEquals(MarketplaceMoney.parse(currency, "123.45"), actual.netAmount)
        assertEquals(listOf(ledgerEntry.id), actual.effectiveEntryIds)
        assertEquals(FinancialReconciliationDifference.NotComparable, saleLine.difference)
        assertEquals(FinancialReconciliationStatus.DIVERGENCE, saleLine.status)

        assertEquals(1L, caseCount(organizationId, trace.id))
        assertEquals(1L, lineageCount(organizationId, expectedCaseId))

        val secondProjection = assertIs<EconomicDecisionRoomProjectionReadResult.Found>(
            projectionService.read(organizationId, created.caseId)
        ).projection
        assertEquals(projection.authorityStatus, secondProjection.authorityStatus)
        assertEquals(projection.governancePermitted, secondProjection.governancePermitted)
        assertEquals(projection.governanceBlockingReasons, secondProjection.governanceBlockingReasons)
        assertEquals(projection.projectionBlockingReasons, secondProjection.projectionBlockingReasons)
        assertEquals(projection.projectionStatus, secondProjection.projectionStatus)
        assertEquals(projection.totalQuantifiedLeakage, secondProjection.totalQuantifiedLeakage)
        val secondSaleProjection = secondProjection.stages.single { it.stage == FinancialLedgerStage.SALE }
        assertEquals(saleProjection.interpretation, secondSaleProjection.interpretation)
        assertEquals(saleProjection.blockingReason, secondSaleProjection.blockingReason)
        assertEquals(stateBeforeFirstDecisionRoomRead, durableState(organizationId, created))
    }

    private fun seedOrganization(organizationId: OrganizationId) = execute(
        "INSERT INTO integration_organization (organization_id,status,created_at,updated_at) " +
            "VALUES ('${organizationId.value}','ACTIVE','2026-09-21T13:00:00Z','2026-09-21T13:00:00Z')"
    )

    private fun seedConnection(organizationId: OrganizationId, connectionId: IntegrationConnectionId) {
        execute("INSERT INTO integration_connection (organization_id,connection_id,provider_key,credential_kind,status,binding_version,created_at,updated_at) VALUES ('${organizationId.value}','${connectionId.value}','br.com.mercadolivre','OAUTH2_AUTHORIZATION_CODE','ACTIVE',1,'2026-09-21T13:00:00Z','2026-09-21T13:00:00Z')")
        execute("INSERT INTO integration_connector_progress (organization_id,connection_id,capability,progress_version,progress_envelope,exhausted,last_observed_at,updated_at) VALUES ('${organizationId.value}','${connectionId.value}','marketplace-economic.order-source',1,decode('01','hex'),false,'2026-09-21T13:00:00Z','2026-09-21T13:00:00Z')")
    }

    private fun seedClosedOrderSource(organizationId: OrganizationId, connectionId: IntegrationConnectionId, externalOrderId: MarketplaceExternalOrderId, currency: MarketplaceCurrency, occurredAt: Instant, observedAt: Instant) {
        execute("INSERT INTO integration_connector_page_commit (organization_id,connection_id,capability,input_progress_version,page_commit_key,record_count,exhausted,observed_at,committed_at) VALUES ('${organizationId.value}','${connectionId.value}','marketplace-economic.order-source',1,decode('${"02".repeat(32)}','hex'),1,false,'$observedAt','$observedAt')")
        execute("INSERT INTO integration_mercado_livre_order_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,provider_status,date_created,date_last_updated,date_closed,currency,total_amount,paid_amount,pack_ref,shipping_ref,observed_at) VALUES ('${organizationId.value}','${connectionId.value}','marketplace-economic.order-source',1,0,'${externalOrderId.value}','paid','2026-09-21T13:30:00Z','$observedAt','$occurredAt','${currency.code}',123.45,123.45,NULL,NULL,'$observedAt')")
    }

    private fun seedOrderIdentity(organizationId: OrganizationId, connectionId: IntegrationConnectionId, orderId: MarketplaceOrderId, externalOrderId: MarketplaceExternalOrderId, currency: MarketplaceCurrency) = execute(
        "INSERT INTO marketplace_order_identity_registry (organization_id,marketplace_key,external_order_id,marketplace_order_id,currency,allocated_at,first_source_connection_id,first_source_capability,first_source_input_progress_version,first_source_record_ordinal) VALUES ('${organizationId.value}','mercado-livre','${externalOrderId.value}','${orderId.value}','${currency.code}','2026-09-21T13:45:00Z','${connectionId.value}','marketplace-economic.order-source',1,0)"
    )

    private fun insertPolicy(organizationId: OrganizationId, version: String, tolerance: String) {
        dataSource.connection.use { connection ->
            connection.prepareStatement("INSERT INTO marketplace_financial_reconciliation_policy (organization_id,marketplace_key,currency,policy_version,stage_tolerances) VALUES (?,?,?,?,?::jsonb)").use { statement ->
                statement.setObject(1, organizationId.value)
                statement.setString(2, "mercado-livre")
                statement.setString(3, "BRL")
                statement.setString(4, version)
                statement.setString(5, tolerancesJson(tolerance))
                assertEquals(1, statement.executeUpdate())
            }
        }
    }

    private fun activatePolicy(organizationId: OrganizationId, version: String) {
        dataSource.connection.use { connection ->
            connection.prepareStatement("INSERT INTO marketplace_financial_reconciliation_policy_current (organization_id,marketplace_key,currency,policy_version) VALUES (?,?,?,?)").use { statement ->
                statement.setObject(1, organizationId.value)
                statement.setString(2, "mercado-livre")
                statement.setString(3, "BRL")
                statement.setString(4, version)
                assertEquals(1, statement.executeUpdate())
            }
        }
    }

    private fun tolerancesJson(amount: String): String = buildJsonObject {
        FinancialLedgerStage.entries.forEach { stage -> put(stage.name, JsonPrimitive(amount)) }
    }.toString()

    private fun durableState(organizationId: OrganizationId, case: DurableReconciliationCase): DurableState =
        DurableState(
            economicEvidenceFacts = count("SELECT count(*) FROM marketplace_economic_evidence_fact WHERE organization_id=?", organizationId.value),
            revenuePromotions = count("SELECT count(*) FROM marketplace_order_revenue_source_promotion WHERE organization_id=?", organizationId.value),
            financialTraces = count("SELECT count(*) FROM marketplace_financial_trace WHERE organization_id=?", organizationId.value),
            financialLedgerEntries = count("SELECT count(*) FROM marketplace_financial_ledger_entry WHERE organization_id=?", organizationId.value),
            materializationLineages = count("SELECT count(*) FROM marketplace_financial_ledger_materialization_lineage WHERE organization_id=?", organizationId.value),
            reconciliationCases = count("SELECT count(*) FROM marketplace_reconciliation_case WHERE organization_id=?", organizationId.value),
            assessmentLineages = count("SELECT count(*) FROM marketplace_reconciliation_case_revision_assessment WHERE organization_id=?", organizationId.value),
            caseRevision = case.revision,
            assessmentFingerprint = lineageRow(organizationId, case.caseId, case.revision).fingerprint,
            traceId = case.traceId,
            caseId = case.caseId
        )
    private fun lineageRow(organizationId: OrganizationId, caseId: ReconciliationCaseId, revision: Long): LineageRow =
        dataSource.connection.use { connection ->
            connection.prepareStatement("SELECT assessment_fingerprint_version,assessment_fingerprint,assessment_snapshot_schema_version,assessment_snapshot::text,accepted_at FROM marketplace_reconciliation_case_revision_assessment WHERE organization_id=? AND case_id=? AND case_revision=?").use { statement ->
                statement.setObject(1, organizationId.value)
                statement.setObject(2, caseId.valueForPersistence())
                statement.setLong(3, revision)
                statement.executeQuery().use { result ->
                    check(result.next())
                    val row = LineageRow(result.getInt(1), result.getString(2), result.getInt(3), result.getString(4), result.getTimestamp(5).toInstant())
                    check(!result.next())
                    row
                }
            }
        }

    private fun caseCount(organizationId: OrganizationId, traceId: FinancialTraceId): Long =
        count("SELECT count(*) FROM marketplace_reconciliation_case WHERE organization_id=? AND financial_trace_id=?", organizationId.value, traceId.valueForPersistence())

    private fun lineageCount(organizationId: OrganizationId, caseId: ReconciliationCaseId): Long =
        count("SELECT count(*) FROM marketplace_reconciliation_case_revision_assessment WHERE organization_id=? AND case_id=?", organizationId.value, caseId.valueForPersistence())

    private fun lineageCountForOrganization(organizationId: OrganizationId): Long =
        count("SELECT count(*) FROM marketplace_reconciliation_case_revision_assessment WHERE organization_id=?", organizationId.value)

    private fun count(sql: String, vararg values: Any): Long = dataSource.connection.use { connection ->
        connection.prepareStatement(sql).use { statement ->
            values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }
            statement.executeQuery().use { result -> check(result.next()); result.getLong(1) }
        }
    }

    private fun execute(sql: String) { dataSource.connection.use { it.createStatement().use { statement -> statement.executeUpdate(sql) } } }

    private data class DurableState(
        val economicEvidenceFacts: Long,
        val revenuePromotions: Long,
        val financialTraces: Long,
        val financialLedgerEntries: Long,
        val materializationLineages: Long,
        val reconciliationCases: Long,
        val assessmentLineages: Long,
        val caseRevision: Long,
        val assessmentFingerprint: String,
        val traceId: FinancialTraceId,
        val caseId: ReconciliationCaseId
    )
    private data class LineageRow(
        val fingerprintVersion: Int,
        val fingerprint: String,
        val snapshotSchemaVersion: Int,
        val snapshot: String,
        val acceptedAt: Instant
    )
}
