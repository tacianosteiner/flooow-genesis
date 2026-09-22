package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.ledger.*
import io.flooow.marketplace.operations.economics.ledger.materialization.*
import io.flooow.marketplace.operations.economics.promotion.*
import io.flooow.marketplace.operations.economics.reconciliation.*
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

class PostgresEconomicDecisionRoomReconciliationAssessmentSourceTest {
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
    fun `real persisted reconciliation assessment lineage is available to Decision Room reader`() {
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

        val decisionRoomAssessmentSource =
            PostgresEconomicDecisionRoomReconciliationAssessmentSource(dataSource)
        val assessmentRead = assertIs<EconomicDecisionRoomReconciliationAssessmentRead.Available>(
            decisionRoomAssessmentSource.read(organizationId, created)
        )
        assertEquals(created.caseId, assessmentRead.binding.caseId)
        assertEquals(created.revision, assessmentRead.binding.reconciliationRevision)
        assertEquals(created.organizationId, assessmentRead.binding.assessment.organizationId)
        assertEquals(created.orderId, assessmentRead.binding.assessment.orderId)
        assertEquals(created.traceId, assessmentRead.binding.assessment.traceId)
        assertEquals(created.policyVersion, assessmentRead.binding.assessment.policyVersion)
        assertEquals(created.currency, assessmentRead.binding.assessment.currency)

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

        val replay = assertIs<GovernedFinancialReconciliationExecutionResult.Orchestrated>(
            reconciliation.execute(organizationId, trace.id)
        )
        assertEquals(FinancialReconciliationStatus.DIVERGENCE, replay.assessmentStatus)
        val unchanged = assertIs<ReconciliationCaseOrchestrationResult.Unchanged>(replay.orchestration).value
        assertEquals(expectedCaseId, unchanged.caseId)
        assertEquals(1L, unchanged.revision)
        assertEquals(1L, caseCount(organizationId, trace.id))
        assertEquals(1L, lineageCount(organizationId, expectedCaseId))

        assertIs<FinancialTraceReadResult.NotFound>(ledger.find(otherOrganizationId, trace.id))
        assertEquals(
            GovernedFinancialReconciliationExecutionResult.TraceNotFound,
            reconciliation.execute(otherOrganizationId, trace.id)
        )
        assertEquals(0L, caseCount(otherOrganizationId, trace.id))
        assertEquals(0L, lineageCountForOrganization(otherOrganizationId))
    }

    @Test
    fun `missing exact assessment lineage is unavailable`() {
        val organizationId = OrganizationId(UUID(0, 94_901))
        val currency = MarketplaceCurrency("BRL")
        val durableCase = DurableReconciliationCase(
            caseId = ReconciliationCaseId.of(UUID(0, 94_902)),
            organizationId = organizationId,
            orderId = MarketplaceOrderId(UUID(0, 94_903)),
            traceId = FinancialTraceId(UUID(0, 94_904)),
            policyVersion = FinancialReconciliationPolicyVersion("d4-controlled/1"),
            currency = currency,
            status = ReconciliationCaseStatus.OPEN,
            openedAt = Instant.parse("2026-09-21T15:00:00.123456Z"),
            lastObservedAt = Instant.parse("2026-09-21T15:00:00.123456Z"),
            resolvedAt = null,
            revision = 1L,
            absoluteDifferenceSummary = MarketplaceMoney.parse(currency, "0.00"),
            stages = listOf(
                ReconciliationCaseStageDifference(
                    stage = FinancialLedgerStage.SALE,
                    expected = null,
                    actual = null,
                    signedDifference = null,
                    absoluteDifference = null,
                    tolerance = MarketplaceMoney.parse(currency, "0.00"),
                    expectedEntryIds = emptyList(),
                    actualEntryIds = emptyList()
                )
            ),
            evidenceEntryIds = emptyList()
        )

        assertIs<EconomicDecisionRoomReconciliationAssessmentRead.Unavailable>(
            PostgresEconomicDecisionRoomReconciliationAssessmentSource(dataSource).read(
                organizationId,
                durableCase
            )
        )
    }

    @Test
    fun `persisted assessment fingerprint corruption is an integrity failure`() {
        `real persisted reconciliation assessment lineage is available to Decision Room reader`()

        val organizationId = OrganizationId(UUID(0, 94_001))
        val caseId = dataSource.connection.use { connection ->
            connection.prepareStatement(
                "SELECT case_id FROM marketplace_reconciliation_case WHERE organization_id = ?"
            ).use { statement ->
                statement.setObject(1, organizationId.value)
                statement.executeQuery().use { rows ->
                    check(rows.next())
                    val value = ReconciliationCaseId.of(rows.getObject(1, UUID::class.java))
                    check(!rows.next())
                    value
                }
            }
        }
        val cases = PostgresDurableReconciliationCaseRepository(configuration)
        val persistedCase = requireNotNull(cases.find(organizationId, caseId))
        val validLineage = lineageRow(organizationId, caseId, persistedCase.revision)
        val corruptFingerprint = "0".repeat(64)
        assertTrue(validLineage.fingerprint != corruptFingerprint)

        dataSource.connection.use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    """
                    INSERT INTO marketplace_reconciliation_case_revision_assessment
                        (organization_id, case_id, case_revision,
                         assessment_fingerprint_version, assessment_fingerprint,
                         assessment_snapshot_schema_version, assessment_snapshot, accepted_at)
                    SELECT organization_id, case_id, ?, assessment_fingerprint_version, ?,
                           assessment_snapshot_schema_version, assessment_snapshot, accepted_at
                      FROM marketplace_reconciliation_case_revision_assessment
                     WHERE organization_id = ? AND case_id = ? AND case_revision = ?
                    """.trimIndent()
                ).use { statement ->
                    statement.setLong(1, persistedCase.revision + 1)
                    statement.setString(2, corruptFingerprint)
                    statement.setObject(3, organizationId.value)
                    statement.setObject(4, caseId.valueForPersistence())
                    statement.setLong(5, persistedCase.revision)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    "UPDATE marketplace_reconciliation_case SET revision = ? WHERE organization_id = ? AND case_id = ?"
                ).use { statement ->
                    statement.setLong(1, persistedCase.revision + 1)
                    statement.setObject(2, organizationId.value)
                    statement.setObject(3, caseId.valueForPersistence())
                    assertEquals(1, statement.executeUpdate())
                }
                connection.commit()
            } catch (failure: Throwable) {
                connection.rollback()
                throw failure
            }
        }

        val assessment = FinancialReconciliationAssessmentSnapshotCodec.rehydrate(
            FinancialReconciliationAssessmentSnapshot.parse(
                validLineage.snapshotSchemaVersion,
                validLineage.snapshot
            )
        ).assessment
        val corruptedCase = persistedCase.withObservation(assessment, persistedCase.lastObservedAt)
        assertEquals(persistedCase.revision + 1, corruptedCase.revision)

        assertIs<EconomicDecisionRoomReconciliationAssessmentRead.IntegrityFailure>(
            PostgresEconomicDecisionRoomReconciliationAssessmentSource(dataSource).read(
                organizationId,
                corruptedCase
            )
        )
    }

    @Test
    fun `valid assessment lineage contradicting durable case projection is an integrity failure`() {
        `real persisted reconciliation assessment lineage is available to Decision Room reader`()

        val organizationId = OrganizationId(UUID(0, 94_001))
        val caseId = dataSource.connection.use { connection ->
            connection.prepareStatement(
                "SELECT case_id FROM marketplace_reconciliation_case WHERE organization_id = ?"
            ).use { statement ->
                statement.setObject(1, organizationId.value)
                statement.executeQuery().use { rows ->
                    check(rows.next())
                    val value = ReconciliationCaseId.of(rows.getObject(1, UUID::class.java))
                    check(!rows.next())
                    value
                }
            }
        }
        val cases = PostgresDurableReconciliationCaseRepository(configuration)
        val persistedCase = requireNotNull(cases.find(organizationId, caseId))
        val validLineage = lineageRow(organizationId, caseId, persistedCase.revision)
        val validFingerprint = FinancialReconciliationAssessmentFingerprint.parsePersisted(
            validLineage.fingerprintVersion,
            validLineage.fingerprint
        )
        val validAssessment = FinancialReconciliationAssessmentSnapshotCodec.verify(
            FinancialReconciliationAssessmentSnapshot.parse(
                validLineage.snapshotSchemaVersion,
                validLineage.snapshot
            ),
            validFingerprint
        ).assessment
        assertEquals(persistedCase.organizationId, validAssessment.organizationId)

        dataSource.connection.use { connection ->
            connection.autoCommit = false
            try {
                connection.prepareStatement(
                    """
                    INSERT INTO marketplace_reconciliation_case_revision_assessment
                        (organization_id, case_id, case_revision,
                         assessment_fingerprint_version, assessment_fingerprint,
                         assessment_snapshot_schema_version, assessment_snapshot, accepted_at)
                    SELECT organization_id, case_id, ?, assessment_fingerprint_version, assessment_fingerprint,
                           assessment_snapshot_schema_version, assessment_snapshot, accepted_at
                      FROM marketplace_reconciliation_case_revision_assessment
                     WHERE organization_id = ? AND case_id = ? AND case_revision = ?
                    """.trimIndent()
                ).use { statement ->
                    statement.setLong(1, persistedCase.revision + 1)
                    statement.setObject(2, organizationId.value)
                    statement.setObject(3, caseId.valueForPersistence())
                    statement.setLong(4, persistedCase.revision)
                    assertEquals(1, statement.executeUpdate())
                }
                connection.prepareStatement(
                    """
                    UPDATE marketplace_reconciliation_case
                       SET revision = ?, evidence_entry_ids = '[]'::jsonb
                     WHERE organization_id = ? AND case_id = ?
                    """.trimIndent()
                ).use { statement ->
                    statement.setLong(1, persistedCase.revision + 1)
                    statement.setObject(2, organizationId.value)
                    statement.setObject(3, caseId.valueForPersistence())
                    assertEquals(1, statement.executeUpdate())
                }
                connection.commit()
            } catch (failure: Throwable) {
                connection.rollback()
                throw failure
            }
        }

        val contradictoryCase = requireNotNull(cases.find(organizationId, caseId))
        assertEquals(persistedCase.revision + 1, contradictoryCase.revision)
        assertTrue(contradictoryCase.evidenceEntryIds.isEmpty())

        assertIs<EconomicDecisionRoomReconciliationAssessmentRead.IntegrityFailure>(
            PostgresEconomicDecisionRoomReconciliationAssessmentSource(dataSource).read(
                organizationId,
                contradictoryCase
            )
        )
    }

    @Test
    fun `assessment lineage is unavailable to a foreign organization`() {
        `real persisted reconciliation assessment lineage is available to Decision Room reader`()

        val organizationA = OrganizationId(UUID(0, 94_001))
        val organizationB = OrganizationId(UUID(0, 94_002))
        val caseId = dataSource.connection.use { connection ->
            connection.prepareStatement(
                "SELECT case_id FROM marketplace_reconciliation_case WHERE organization_id = ?"
            ).use { statement ->
                statement.setObject(1, organizationA.value)
                statement.executeQuery().use { rows ->
                    check(rows.next())
                    val value = ReconciliationCaseId.of(rows.getObject(1, UUID::class.java))
                    check(!rows.next())
                    value
                }
            }
        }
        val ownCase = requireNotNull(
            PostgresDurableReconciliationCaseRepository(configuration).find(organizationA, caseId)
        )
        val foreignCase = DurableReconciliationCase(
            caseId = ownCase.caseId,
            organizationId = organizationB,
            orderId = ownCase.orderId,
            traceId = ownCase.traceId,
            policyVersion = ownCase.policyVersion,
            currency = ownCase.currency,
            status = ownCase.status,
            openedAt = ownCase.openedAt,
            lastObservedAt = ownCase.lastObservedAt,
            resolvedAt = ownCase.resolvedAt,
            revision = ownCase.revision,
            absoluteDifferenceSummary = ownCase.absoluteDifferenceSummary,
            stages = ownCase.stages,
            evidenceEntryIds = ownCase.evidenceEntryIds
        )
        val source = PostgresEconomicDecisionRoomReconciliationAssessmentSource(dataSource)

        assertIs<EconomicDecisionRoomReconciliationAssessmentRead.Available>(
            source.read(organizationA, ownCase)
        )
        assertIs<EconomicDecisionRoomReconciliationAssessmentRead.Unavailable>(
            source.read(organizationB, foreignCase)
        )
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

    private data class LineageRow(
        val fingerprintVersion: Int,
        val fingerprint: String,
        val snapshotSchemaVersion: Int,
        val snapshot: String,
        val acceptedAt: Instant
    )
}
