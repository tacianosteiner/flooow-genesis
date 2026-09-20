package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.materialization.*
import io.flooow.marketplace.operations.economics.reconciliation.*
import io.flooow.organization.OrganizationId
import java.sql.DriverManager
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import kotlin.test.*
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

/** Test-only proof. It is not part of a production artifact or HTTP surface. */
class SyntheticGovernedLedgerDecisionRoomProofTest {
    private lateinit var postgres: PostgreSQLContainer
    private lateinit var configuration: PostgresConfiguration

    @BeforeTest fun start() {
        postgres = PostgreSQLContainer("postgres:18.4").also { it.start() }
        configuration = PostgresConfiguration(postgres.jdbcUrl, postgres.username, postgres.password)
        Flyway.configure().dataSource(configuration.url, configuration.user, configuration.password).load().migrate()
    }
    @AfterTest fun stop() = postgres.stop()

    @Test fun `synthetic facts use governed stores through blocked decision room`() {
        val organization = OrganizationId.parse("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        insertOrganization(organization)
        val observations = listOf(observation(organization, "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "cccccccc-cccc-4ccc-8ccc-ccccccccccc1"), observation(organization, "dddddddd-dddd-4ddd-8ddd-dddddddddddd", "cccccccc-cccc-4ccc-8ccc-ccccccccccc2"))
        val evidence = PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration)
        val materializations = observations.map { observation ->
            assertIs<MarketplaceIndependentEconomicEvidencePersistResult.Applied>(
                evidence.apply(MarketplaceEconomicEvidenceVersion.ZERO, MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(MarketplaceIndependentEconomicFact.Component(observation)))
            )
            val authority = MercadoLivreClosedOrderRevenueBasisAuthority(
                MercadoLivreClosedOrderRevenueAuthoritySource { _, _, _ ->
                    MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found(listOf(proof(observation)))
                }
            ).resolve(organization, observation)
            val plan = assertIs<GovernedFinancialLedgerComponentMaterializationResult.Eligible>(
                GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(organization, observation, authority)
            ).plan
            assertEquals(observation.id, plan.sourceAuthorityIdentity)
            assertEquals(FinancialLedgerBasis.ACTUAL, plan.basis)
            assertEquals(FinancialLedgerMaterializationPolicyVersion.V1, plan.materializationPolicyVersion)
            val store = PostgresGovernedFinancialLedgerMaterializationCommitStore(configuration)
            val first = assertIs<GovernedFinancialLedgerMaterializationCommitResult.Materialized>(store.commit(plan))
            val replay = assertIs<GovernedFinancialLedgerMaterializationCommitResult.AlreadyMaterialized>(store.commit(plan))
            assertEquals(first.traceId, replay.traceId); assertEquals(first.entryId, replay.entryId)
            assertEquals(1, count("select count(*) from marketplace_financial_ledger_materialization_lineage where organization_id=? and source_authority_identity=?", organization.value, observation.id.valueForPersistence()))
            first
        }
        val cases = PostgresDurableReconciliationCaseRepository(configuration)
        val detector = DeterministicSystemicDivergenceDetector(PostgresSystemicDivergenceSignalRepository(configuration))
        val orchestrator = GovernedReconciliationCaseOrchestrator(
            cases, PostgresGovernedReconciliationCaseRevisionCommitStore(configuration)
        ) { org, now -> detector.analyze(org, cases.list(org, null, 100).cases, SystemicDivergencePolicies.current, now) }
        val policy = FinancialReconciliationPolicy(
            FinancialReconciliationPolicyVersion("synthetic-test/1"), MarketplaceCurrency("BRL"),
            FinancialLedgerStage.entries.associateWith { MarketplaceMoney.parse(MarketplaceCurrency("BRL"), "0") }
        )
        val execution = GovernedFinancialReconciliationExecutionService(
            PostgresMarketplaceFinancialLedgerRepository(configuration),
            FinancialReconciliationPolicySource { FinancialReconciliationPolicySelection.Selected(policy) }, orchestrator
        )
        val created = materializations.map { result ->
            val orchestrated = assertIs<GovernedFinancialReconciliationExecutionResult.Orchestrated>(execution.execute(organization, result.traceId))
            assertEquals(FinancialReconciliationStatus.DIVERGENCE, orchestrated.assessmentStatus)
            assertIs<ReconciliationCaseOrchestrationResult.Created>(orchestrated.orchestration).value
        }
        val signals = PostgresSystemicDivergenceSignalRepository(configuration).list(organization, null, 100).signals
        // Actual-only facts are a real DIVERGENCE, but have no comparable absolute
        // difference; the detector correctly declines to manufacture a signal.
        assertEquals(0, signals.size)
        val projection = assertIs<EconomicDecisionRoomProjectionReadResult.Found>(
            EconomicDecisionRoomProjectionService(cases, UnavailableEconomicDecisionRoomAuthoritySource, UnavailableEconomicDecisionRoomReconciliationAssessmentSource).read(organization, created.first().caseId)
        ).projection
        assertEquals(EconomicDecisionRoomProjectionStatus.BLOCKED, projection.projectionStatus)
        assertEquals(EconomicDecisionRoomAuthorityStatus.NOT_ASSEMBLED, projection.authorityStatus)
        assertTrue(EconomicDecisionRoomProjectionBlockingReason.RECONCILIATION_ASSESSMENT_UNAVAILABLE in projection.projectionBlockingReasons)
        assertTrue(EconomicDecisionRoomProjectionBlockingReason.AUTHORITY_NOT_ASSEMBLED in projection.projectionBlockingReasons)
        assertNull(projection.totalQuantifiedLeakage)
        assertTrue(projection.evidenceReferences.any { it.startsWith("financial-ledger-entry:") })
    }

    @Test fun `governance boundaries fail closed in test fixtures`() {
        val observation = observation(OrganizationId.parse("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"), "ffffffff-ffff-4fff-8fff-ffffffffffff", "11111111-1111-4111-8111-111111111111")
        val authorized = FinancialLedgerComponentMaterializationAuthorityDecision.Authorized(observation.id, FinancialLedgerSourceAuthoritySemanticVersion("synthetic-test/1"), FinancialLedgerMaterializationPolicyVersion.V1, FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation), FinancialLedgerBasis.ACTUAL)
        assertIs<GovernedFinancialLedgerComponentMaterializationResult.Failed.IntegrityFailure>(GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(OrganizationId.parse("22222222-2222-4222-8222-222222222222"), observation, authorized))
        val invalidFingerprint = FinancialLedgerComponentMaterializationAuthorityDecision.Authorized(observation.id, FinancialLedgerSourceAuthoritySemanticVersion("synthetic-test/1"), FinancialLedgerMaterializationPolicyVersion.V1, FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation).copy(sha256 = "0".repeat(64)), FinancialLedgerBasis.ACTUAL)
        assertIs<GovernedFinancialLedgerComponentMaterializationResult.Failed.IntegrityFailure>(GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(observation.subject.organizationId, observation, invalidFingerprint))
        assertIs<GovernedFinancialLedgerComponentMaterializationResult.Failed.Unavailable>(GovernedFinancialLedgerComponentMaterializationBoundary.evaluate(observation.subject.organizationId, observation, FinancialLedgerComponentMaterializationAuthorityDecision.Unavailable))
    }

    private fun observation(org: OrganizationId, order: String, id: String): MarketplaceEconomicComponentObservation {
        val currency = MarketplaceCurrency("BRL"); val orderId = MarketplaceOrderId.parse(order)
        val subject = MarketplaceEconomicEvidenceSubject(org, orderId, MarketplaceKey("mercado-livre"), MarketplaceExternalOrderId("MLB-$order"), currency)
        val component = EconomicComponent(org, EconomicComponentId.parse(UUID.nameUUIDFromBytes((id+"component").toByteArray()).toString()), orderId, EconomicComponentType.REVENUE, EconomicDirection.ADDITION, MarketplaceMoney.parse(currency, "100.00"), EconomicSource(EconomicSourceKind.MARKETPLACE, EconomicSourceSystemKey("br.com.mercadolivre"), EconomicExternalReferenceState.Present(EconomicExternalReference("MLB-$order"))), Instant.parse("2026-09-19T12:00:00.000001Z"), EconomicEvidenceQuality.CONFIRMED)
        return MarketplaceEconomicComponentObservation(MarketplaceEconomicEvidenceObservationId.parse(id), subject, MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER, component, EconomicComponentCoverage.PARTIAL, Instant.parse("2026-09-19T12:01:00.000001Z"))
    }
    private fun proof(o: MarketplaceEconomicComponentObservation) = MercadoLivreClosedOrderRevenueProviderProof(o, o.subject.organizationId, o.subject.orderId, o.subject.marketplace, o.subject.externalOrderId, o.subject.currency, MercadoLivreClosedOrderRevenueBasisAuthority.SOURCE_CAPABILITY, o.subject.externalOrderId, o.subject.currency, o.component.magnitude, o.component.occurredAt, o.observedAt, MercadoLivreClosedOrderRevenuePromotionOutcome.PROMOTED)
    private fun insertOrganization(org: OrganizationId) { DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { c -> c.prepareStatement("insert into integration_organization (organization_id,status,created_at,updated_at) values (?,?,?,?)").use { s -> val now=Timestamp.from(Instant.parse("2026-09-19T11:00:00Z")); s.setObject(1,org.value); s.setString(2,"ACTIVE"); s.setTimestamp(3,now);s.setTimestamp(4,now);assertEquals(1,s.executeUpdate()) } } }
    private fun count(sql: String, vararg values: Any): Int = DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { c -> c.prepareStatement(sql).use { s -> values.forEachIndexed { i,v -> s.setObject(i+1,v) }; s.executeQuery().use { r -> check(r.next()); r.getInt(1) } } }
}
