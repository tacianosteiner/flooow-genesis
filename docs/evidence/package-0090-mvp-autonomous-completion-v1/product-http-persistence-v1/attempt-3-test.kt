package io.flooow.marketplace.api

import com.github.dockerjava.api.model.ExposedPort
import com.github.dockerjava.api.model.PortBinding
import com.github.dockerjava.api.model.Ports
import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.ledger.*
import io.flooow.marketplace.operations.economics.reconciliation.*
import io.flooow.marketplace.persistence.postgres.*
import io.flooow.organization.OrganizationId
import io.ktor.client.request.*
import io.ktor.client.statement.bodyAsText
import io.ktor.http.*
import io.ktor.server.testing.testApplication
import java.sql.DriverManager
import java.time.Instant
import java.util.UUID
import kotlin.test.*
import kotlinx.serialization.json.*
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

/** Real isolated product HTTP/persistence integration; no PACKAGE-0090 proof. */
class EconomicDecisionRoomPostgresApiTest {
    @Test
    fun `real persisted case remains blocked without authority and GET is replayable and read only`() {
        val postgres = PostgreSQLContainer("postgres:18.4")
            .withLabel("flooow.authority", "mvp-autonomous-completion-v1")
            .withCreateContainerCmdModifier { command ->
                requireNotNull(command.hostConfig).withPortBindings(
                    PortBinding(Ports.Binding.bindIpAndPort("127.0.0.1", 0), ExposedPort.tcp(5432))
                )
            }
        postgres.start()
        try {
            val configuration = PostgresConfiguration(postgres.jdbcUrl, postgres.username, postgres.password)
            // Product schema only. Canonical V043 stays present and fenced.
            Flyway.configure().dataSource(configuration.url, configuration.user, configuration.password)
                .target("42").load().migrate()
            val cases = PostgresDurableReconciliationCaseRepository(configuration)
            val currency = MarketplaceCurrency("BRL")
            val time = Instant.parse("2026-09-13T12:00:00Z")
            val traceId = FinancialTraceId.parse("30000000-0000-0000-0000-000000000091")
            val orderId = MarketplaceOrderId.parse("20000000-0000-0000-0000-000000000091")
            DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { connection ->
                connection.prepareStatement("INSERT INTO integration_organization (organization_id,status,created_at,updated_at) VALUES (?,'ACTIVE',?,?)").use {
                    it.setObject(1, TEST_ORGANIZATION_ID.value)
                    it.setTimestamp(2, java.sql.Timestamp.from(time)); it.setTimestamp(3, java.sql.Timestamp.from(time))
                    assertEquals(1, it.executeUpdate())
                }
                connection.prepareStatement("INSERT INTO marketplace_financial_trace (organization_id,trace_id,open_request_id,order_id,marketplace_key,external_order_id,currency,opened_at) VALUES (?,?,?,?,'mercado-livre','isolated-api-case','BRL',?)").use {
                    it.setObject(1, TEST_ORGANIZATION_ID.value); it.setObject(2, traceId.value)
                    it.setObject(3, UUID.fromString("60000000-0000-0000-0000-000000000091")); it.setObject(4, orderId.value)
                    it.setTimestamp(5, java.sql.Timestamp.from(time)); assertEquals(1, it.executeUpdate())
                }
            }
            // Persist through the existing atomic assessment/case lineage seam.
            // These are synthetic domain fixtures, never canonical source authority.
            val trace = FinancialTrace(
                organizationId = TEST_ORGANIZATION_ID, id = traceId,
                requestId = FinancialTraceOpenRequestId.of(UUID.fromString("60000000-0000-0000-0000-000000000091")),
                orderId = orderId, marketplace = MarketplaceKey("mercado-livre"),
                externalOrderId = MarketplaceExternalOrderId("isolated-api-case"),
                currency = currency, openedAt = time,
                entries = listOf(FinancialLedgerBasis.EXPECTED to "100", FinancialLedgerBasis.ACTUAL to "110").mapIndexed { index, (basis, amount) ->
                    RecordedFinancialLedgerEntry(
                        organizationId = TEST_ORGANIZATION_ID,
                        id = FinancialLedgerEntryId.parse("50000000-0000-0000-0000-00000000009${index + 1}"),
                        requestId = FinancialLedgerAppendRequestId.of(UUID.fromString("60000000-0000-0000-0000-00000000009${index + 2}")),
                        traceId = traceId, stage = FinancialLedgerStage.SALE, basis = basis,
                        direction = EconomicDirection.ADDITION, magnitude = MarketplaceMoney.parse(currency, amount),
                        source = EconomicSource(EconomicSourceKind.MARKETPLACE, EconomicSourceSystemKey("meli-br"),
                            EconomicExternalReferenceState.Present(EconomicExternalReference("isolated-$index"))),
                        occurredAt = time, recordedAt = time
                    )
                }
            )
            val assessment = assertIs<FinancialReconciliationResult.Assessed>(MarketplaceFinancialReconciliation.assess(
                trace, FinancialReconciliationPolicy(FinancialReconciliationPolicyVersion("policy/isolated"), currency,
                    FinancialLedgerStage.entries.associateWith { MarketplaceMoney.parse(currency, "0") })
            )).assessment
            assertEquals(FinancialReconciliationStatus.DIVERGENCE, assessment.status)
            val orchestrator = GovernedReconciliationCaseOrchestrator(cases, PostgresGovernedReconciliationCaseRevisionCommitStore(configuration))
            val persisted = assertIs<ReconciliationCaseOrchestrationResult.Created>(orchestrator.process(
                AcceptedFinancialReconciliationAssessment.accept(assessment, time), TEST_ORGANIZATION_ID
            )).value
            val caseId = persisted.caseId
            val dataSource = PostgresDataSources.create(configuration)
            val projections = EconomicDecisionRoomProjectionService(
                cases, PostgresEconomicDecisionRoomAuthoritySource(dataSource),
                PostgresEconomicDecisionRoomReconciliationAssessmentSource(dataSource)
            )
            testApplication {
                application {
                    configureApi(
                        serviceToken = ServiceToken.test(TEST_SERVICE_TOKEN),
                        serviceOrganizationId = TEST_ORGANIZATION_ID,
                        record = { _, _ -> error("read endpoint must never record") },
                        reconciliationCasesApi = ReconciliationCasesApi(cases, ReconciliationCaseCursorCodec("isolated-public-test-only".toByteArray())),
                        economicDecisionRoomApi = EconomicDecisionRoomApi(projections)
                    )
                }
                val path = "$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/${caseId.value}"
                assertEquals(HttpStatusCode.Unauthorized, client.get(path).status)
                val first = client.get(path) { bearerAuth(TEST_SERVICE_TOKEN) }
                val second = client.get(path) { bearerAuth(TEST_SERVICE_TOKEN) }
                assertEquals(HttpStatusCode.OK, first.status)
                assertEquals(first.bodyAsText(), second.bodyAsText())
                assertEquals("no-store", first.headers[HttpHeaders.CacheControl])
                val json = Json.parseToJsonElement(first.bodyAsText()).jsonObject
                assertEquals("BLOCKED", json.getValue("projectionStatus").jsonPrimitive.content)
                assertEquals("NOT_ASSEMBLED", json.getValue("authorityStatus").jsonPrimitive.content)
                assertIs<JsonNull>(json.getValue("totalQuantifiedLeakage"))
                assertTrue(json.getValue("blockingReasons").jsonArray.any {
                    it.jsonPrimitive.content == "AUTHORITY_NOT_ASSEMBLED"
                })
                assertEquals("10", json.getValue("stages").jsonArray.single().jsonObject
                    .getValue("signedVariance").jsonObject.getValue("amount").jsonPrimitive.content)
                val missing = client.get("$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/40000000-0000-0000-0000-000000000092") { bearerAuth(TEST_SERVICE_TOKEN) }
                assertEquals(HttpStatusCode.NotFound, missing.status)
            }
            testApplication {
                application {
                    configureApi(
                        serviceToken = ServiceToken.test(TEST_SERVICE_TOKEN),
                        serviceOrganizationId = OrganizationId.parse("99999999-9999-4999-8999-999999999999"),
                        record = { _, _ -> error("read endpoint must never record") },
                        economicDecisionRoomApi = EconomicDecisionRoomApi(projections)
                    )
                }
                val response = client.get("$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/${caseId.value}") {
                    bearerAuth(TEST_SERVICE_TOKEN)
                    header("X-Organization-Id", TEST_ORGANIZATION_ID.value.toString())
                }
                assertEquals(HttpStatusCode.NotFound, response.status)
                assertTrue(response.bodyAsText().contains("ECONOMIC_DECISION_ROOM_PROJECTION_NOT_FOUND"))
            }
            assertEquals(persisted, cases.find(TEST_ORGANIZATION_ID, caseId))
            DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { connection ->
                connection.createStatement().use { statement ->
                    statement.executeQuery("SELECT count(*) FROM flyway_schema_history WHERE version='043' OR version='43'").use {
                        assertTrue(it.next()); assertEquals(0, it.getInt(1))
                    }
                    statement.executeQuery("SELECT count(*) FROM marketplace_financial_ledger_entry").use {
                        assertTrue(it.next()); assertEquals(0, it.getInt(1))
                    }
                    statement.executeQuery("SELECT count(*) FROM marketplace_reconciliation_case").use {
                        assertTrue(it.next()); assertEquals(1, it.getInt(1))
                    }
                }
            }
        } finally {
            postgres.stop()
        }
    }
}
