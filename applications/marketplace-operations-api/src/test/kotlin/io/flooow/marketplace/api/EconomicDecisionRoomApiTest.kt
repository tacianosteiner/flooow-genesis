package io.flooow.marketplace.api

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.ledger.*
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityAssemblyFailureReason
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityInputs
import io.flooow.marketplace.operations.economics.reconciliation.*
import io.flooow.organization.OrganizationId
import io.ktor.client.request.*
import io.ktor.client.statement.bodyAsText
import io.ktor.http.*
import io.ktor.server.testing.testApplication
import kotlinx.serialization.json.*
import java.time.Instant
import java.util.UUID
import kotlin.test.*

class EconomicDecisionRoomApiTest {
    @Test fun `malformed case id is rejected`() = testApplication {
        application { configured(Repository(case)) }
        val response = client.get("$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/not-a-uuid") { bearerAuth(TEST_SERVICE_TOKEN) }
        assertEquals(HttpStatusCode.BadRequest, response.status)
        assertTrue(response.bodyAsText().contains("INVALID_ECONOMIC_DECISION_ROOM_CASE_ID"))
    }

    @Test fun `blocked endpoint preserves financial variance without zero leakage and is read only`() = testApplication {
        val repository = Repository(case)
        application { configured(repository) }
        val response = client.get("$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/${case.caseId.value}") { bearerAuth(TEST_SERVICE_TOKEN) }
        assertEquals(HttpStatusCode.OK, response.status)
        assertEquals("no-store", response.headers[HttpHeaders.CacheControl])
        val json = Json.parseToJsonElement(response.bodyAsText()).jsonObject
        assertEquals("BLOCKED", json.getValue("projectionStatus").jsonPrimitive.content)
        assertEquals("NOT_ASSEMBLED", json.getValue("authorityStatus").jsonPrimitive.content)
        assertTrue(json.getValue("totalQuantifiedLeakage") is JsonNull)
        val stage = json.getValue("stages").jsonArray.single().jsonObject
        assertEquals("-10", stage.getValue("signedVariance").jsonObject.getValue("amount").jsonPrimitive.content)
        assertTrue(stage.getValue("interpretation") is JsonNull)
        assertEquals(0, repository.saves)
    }

    @Test fun `authenticated organization scopes projection lookup`() = testApplication {
        val repository = Repository(case)
        application { configured(repository) }
        client.get("$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/${case.caseId.value}") {
            bearerAuth(TEST_SERVICE_TOKEN)
            header("X-Organization-Id", "99999999-9999-4999-8999-999999999999")
        }
        assertEquals(TEST_ORGANIZATION_ID, repository.lastOrganization)
    }

    @Test fun `cross organization repository leak is indistinguishable from missing case`() = testApplication {
        val foreign = caseFor(OrganizationId.parse("99999999-9999-4999-8999-999999999999"))
        application { configured(Repository(foreign, leakAcrossOrganizations = true)) }
        val response = client.get("$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/${foreign.caseId.value}") {
            bearerAuth(TEST_SERVICE_TOKEN)
        }
        assertEquals(HttpStatusCode.NotFound, response.status)
        assertTrue(response.bodyAsText().contains("ECONOMIC_DECISION_ROOM_PROJECTION_NOT_FOUND"))
    }

    @Test fun `cross organization assessment source leak is indistinguishable from missing projection`() = testApplication {
        val repository = Repository(case)
        val foreignAssessment = assessmentFor(
            OrganizationId.parse("99999999-9999-4999-8999-999999999999")
        )
        application {
            configured(
                repository,
                assessmentSource = EconomicDecisionRoomReconciliationAssessmentSource { _, _ ->
                    EconomicDecisionRoomReconciliationAssessmentRead.Available(
                        EconomicDecisionRoomReconciliationAssessmentBinding(
                            case.caseId,
                            case.revision,
                            foreignAssessment
                        )
                    )
                }
            )
        }

        val missing = client.get(
            "$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/40000000-0000-0000-0000-000000000099"
        ) { bearerAuth(TEST_SERVICE_TOKEN) }

        val leaked = client.get(
            "$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/${case.caseId.value}"
        ) { bearerAuth(TEST_SERVICE_TOKEN) }

        assertEquals(HttpStatusCode.NotFound, missing.status)
        assertEquals(missing.status, leaked.status)

        val missingProblem =
            Json.parseToJsonElement(missing.bodyAsText()).jsonObject
        val leakedProblem =
            Json.parseToJsonElement(leaked.bodyAsText()).jsonObject

        listOf("type", "title", "status", "detail", "code").forEach { field ->
            assertEquals(
                missingProblem[field],
                leakedProblem[field],
                "Public problem field $field must not reveal the cross-organization source leak"
            )
        }

        assertEquals(
            "ECONOMIC_DECISION_ROOM_PROJECTION_NOT_FOUND",
            leakedProblem.getValue("code").jsonPrimitive.content
        )
        assertNotEquals(
            missingProblem.getValue("instance"),
            leakedProblem.getValue("instance"),
            "Problem instance must continue to identify the URL actually requested"
        )
    }

    @Test fun `cross organization authority source leak is indistinguishable from missing projection`() = testApplication {
        val repository = Repository(case)
        val foreignOrganization =
            OrganizationId.parse("99999999-9999-4999-8999-999999999999")

        val foreignAuthority = EconomicDecisionRoomAuthorityContext(
            organizationId = foreignOrganization,
            caseId = case.caseId,
            marketplaceOrderId = case.orderId,
            financialTraceId = case.traceId,
            policyVersion = case.policyVersion,
            currency = case.currency,
            reconciliationRevision = case.revision,
            inputs = EconomicTruthAuthorityInputs(null, null, null, null)
        )

        application {
            configured(
                repository,
                authoritySource = EconomicDecisionRoomAuthoritySource { _, _ ->
                    EconomicDecisionRoomAuthorityRead.Available(foreignAuthority)
                }
            )
        }

        val missing = client.get(
            "$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/40000000-0000-0000-0000-000000000099"
        ) { bearerAuth(TEST_SERVICE_TOKEN) }

        val leaked = client.get(
            "$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/${case.caseId.value}"
        ) { bearerAuth(TEST_SERVICE_TOKEN) }

        assertEquals(HttpStatusCode.NotFound, missing.status)
        assertEquals(missing.status, leaked.status)

        val missingProblem =
            Json.parseToJsonElement(missing.bodyAsText()).jsonObject
        val leakedProblem =
            Json.parseToJsonElement(leaked.bodyAsText()).jsonObject

        listOf("type", "title", "status", "detail", "code").forEach { field ->
            assertEquals(
                missingProblem[field],
                leakedProblem[field],
                "Public problem field $field must not reveal the cross-organization source leak"
            )
        }

        assertEquals(
            "ECONOMIC_DECISION_ROOM_PROJECTION_NOT_FOUND",
            leakedProblem.getValue("code").jsonPrimitive.content
        )
        assertNotEquals(
            missingProblem.getValue("instance"),
            leakedProblem.getValue("instance"),
            "Problem instance must continue to identify the URL actually requested"
        )
    }

    @Test fun `existing reconciliation case endpoint remains unchanged`() = testApplication {
        val repository = Repository(case)
        application { configured(repository) }
        val response = client.get("$RECONCILIATION_CASES_PATH/${case.caseId.value}") { bearerAuth(TEST_SERVICE_TOKEN) }
        assertEquals(HttpStatusCode.OK, response.status)
        val json = Json.parseToJsonElement(response.bodyAsText()).jsonObject
        assertEquals("OPEN", json.getValue("status").jsonPrimitive.content)
        assertFalse("projectionStatus" in json)
    }

    @Test fun `OpenAPI endpoint resolves actual projection graph enums and nullability`() {
        val openApi = Json.parseToJsonElement(
            requireNotNull(javaClass.getResource("/openapi.json")).readText()
        ).jsonObject

        val endpointSchema = openApi.getValue("paths").jsonObject
            .getValue("$ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH/{caseId}").jsonObject
            .getValue("get").jsonObject
            .getValue("responses").jsonObject
            .getValue("200").jsonObject
            .getValue("content").jsonObject
            .getValue("application/json").jsonObject
            .getValue("schema").jsonObject

        assertEquals(
            "#/components/schemas/EconomicDecisionRoomProjection",
            endpointSchema.getValue("\$ref").jsonPrimitive.content
        )

        val projectionSchema = openApi.resolveLocalSchema(endpointSchema)
        val projection = projectionSchema.getValue("properties").jsonObject

        val stageItems = projection.getValue("stages").jsonObject.getValue("items").jsonObject
        assertEquals(
            "#/components/schemas/EconomicDecisionRoomStage",
            stageItems.getValue("\$ref").jsonPrimitive.content
        )
        val stage = openApi.resolveLocalSchema(stageItems).getValue("properties").jsonObject

        val totalAlternatives = projection.getValue("totalQuantifiedLeakage")
            .jsonObject.getValue("oneOf").jsonArray.map { it.jsonObject }

        assertTrue(
            totalAlternatives.any { it["type"]?.jsonPrimitive?.content == "null" },
            "totalQuantifiedLeakage must expose an explicit null branch"
        )

        val moneyReference = totalAlternatives.single { it["\$ref"] != null }
        assertEquals(
            "#/components/schemas/EconomicDecisionRoomMoney",
            moneyReference.getValue("\$ref").jsonPrimitive.content
        )
        val moneySchema = openApi.resolveLocalSchema(moneyReference)
        assertEquals(
            setOf("currency", "amount"),
            moneySchema.getValue("required").jsonArray.mapTo(linkedSetOf()) {
                it.jsonPrimitive.content
            }
        )

        assertEquals(EconomicDecisionRoomProjectionStatus.entries.names(), projection.getValue("projectionStatus").enumNames())
        assertEquals(EconomicDecisionRoomAuthorityStatus.entries.names(), projection.getValue("authorityStatus").enumNames())
        assertEquals(EconomicTruthAuthorityAssemblyFailureReason.entries.names(), projection.getValue("authorityBlockingReasons").arrayEnumNames())
        assertEquals(EconomicLeakageGovernanceBlockingReason.entries.names(), projection.getValue("governanceBlockingReasons").arrayEnumNames())
        assertEquals(EconomicDecisionRoomProjectionBlockingReason.entries.names(), projection.getValue("projectionBlockingReasons").arrayEnumNames())
        assertEquals(ReconciliationCaseStatus.entries.names(), projection.getValue("reconciliationCaseStatus").enumNames())
        assertEquals(FinancialLedgerStage.entries.names(), stage.getValue("stage").enumNames())
        assertEquals(EconomicLeakageInterpretationStatus.entries.names(), stage.getValue("interpretation").nullableEnumNames())
        assertEquals(EconomicDecisionRoomStageBlockingReason.entries.names(), stage.getValue("blockingReason").nullableEnumNames())
    }

    private fun io.ktor.server.application.Application.configured(
        repository: DurableReconciliationCaseRepository,
        authoritySource: EconomicDecisionRoomAuthoritySource =
            UnavailableEconomicDecisionRoomAuthoritySource,
        assessmentSource: EconomicDecisionRoomReconciliationAssessmentSource =
            UnavailableEconomicDecisionRoomReconciliationAssessmentSource
    ) {
        val projections = EconomicDecisionRoomProjectionService(
            repository,
            authoritySource,
            assessmentSource
        )
        configureApi(
            serviceToken = ServiceToken.test(TEST_SERVICE_TOKEN),
            serviceOrganizationId = TEST_ORGANIZATION_ID,
            record = { _, _ -> error("not used") },
            reconciliationCasesApi = ReconciliationCasesApi(repository, ReconciliationCaseCursorCodec("cursor-secret".toByteArray())),
            economicDecisionRoomApi = EconomicDecisionRoomApi(projections)
        )
    }

    private class Repository(
        private val value: DurableReconciliationCase,
        private val leakAcrossOrganizations: Boolean = false
    ) : DurableReconciliationCaseRepository {
        var saves = 0
        var lastOrganization: OrganizationId? = null
        override fun save(value: DurableReconciliationCase): DurableReconciliationCase { saves++; return value }
        override fun find(organizationId: OrganizationId, caseId: ReconciliationCaseId): DurableReconciliationCase? {
            lastOrganization = organizationId
            return value.takeIf { (leakAcrossOrganizations || it.organizationId == organizationId) && it.caseId == caseId }
        }
        override fun list(organizationId: OrganizationId, cursor: ReconciliationCaseCursor?, limit: Int) = ReconciliationCasePage(emptyList(), null)
    }

    private fun assessmentFor(
        organizationId: OrganizationId
    ): FinancialReconciliationAssessment {
        val trace = FinancialTrace(
            organizationId = organizationId,
            id = FinancialTraceId.parse(
                "30000000-0000-0000-0000-000000000001"
            ),
            requestId = FinancialTraceOpenRequestId.of(
                UUID.fromString("60000000-0000-0000-0000-000000000001")
            ),
            orderId = MarketplaceOrderId.parse(
                "20000000-0000-0000-0000-000000000001"
            ),
            marketplace = MarketplaceKey("mercado-livre"),
            externalOrderId = MarketplaceExternalOrderId("order-001"),
            currency = currency,
            openedAt = Instant.parse("2026-09-13T11:00:00Z"),
            entries = listOf(
                RecordedFinancialLedgerEntry(
                    organizationId = organizationId,
                    id = FinancialLedgerEntryId.parse(
                        "50000000-0000-0000-0000-000000000001"
                    ),
                    requestId = FinancialLedgerAppendRequestId.of(
                        UUID.fromString(
                            "60000000-0000-0000-0000-000000000002"
                        )
                    ),
                    traceId = FinancialTraceId.parse(
                        "30000000-0000-0000-0000-000000000001"
                    ),
                    stage = FinancialLedgerStage.SALE,
                    basis = FinancialLedgerBasis.EXPECTED,
                    direction = EconomicDirection.ADDITION,
                    magnitude = MarketplaceMoney.parse(currency, "100"),
                    source = EconomicSource(
                        EconomicSourceKind.MARKETPLACE,
                        EconomicSourceSystemKey("meli-br"),
                        EconomicExternalReferenceState.Present(
                            EconomicExternalReference("expected-sale")
                        )
                    ),
                    occurredAt = Instant.parse("2026-09-13T11:01:00Z"),
                    recordedAt = Instant.parse("2026-09-13T11:02:00Z")
                ),
                RecordedFinancialLedgerEntry(
                    organizationId = organizationId,
                    id = FinancialLedgerEntryId.parse(
                        "50000000-0000-0000-0000-000000000002"
                    ),
                    requestId = FinancialLedgerAppendRequestId.of(
                        UUID.fromString(
                            "60000000-0000-0000-0000-000000000003"
                        )
                    ),
                    traceId = FinancialTraceId.parse(
                        "30000000-0000-0000-0000-000000000001"
                    ),
                    stage = FinancialLedgerStage.SALE,
                    basis = FinancialLedgerBasis.ACTUAL,
                    direction = EconomicDirection.ADDITION,
                    magnitude = MarketplaceMoney.parse(currency, "90"),
                    source = EconomicSource(
                        EconomicSourceKind.MARKETPLACE,
                        EconomicSourceSystemKey("meli-br"),
                        EconomicExternalReferenceState.Present(
                            EconomicExternalReference("actual-sale")
                        )
                    ),
                    occurredAt = Instant.parse("2026-09-13T11:03:00Z"),
                    recordedAt = Instant.parse("2026-09-13T11:04:00Z")
                )
            )
        )

        val policy = FinancialReconciliationPolicy(
            FinancialReconciliationPolicyVersion("policy/1"),
            currency,
            FinancialLedgerStage.entries.associateWith {
                MarketplaceMoney.parse(currency, "0")
            }
        )

        return assertIs<FinancialReconciliationResult.Assessed>(
            MarketplaceFinancialReconciliation.assess(trace, policy)
        ).assessment
    }

    private val currency = MarketplaceCurrency("BRL")
    private val expectedId = FinancialLedgerEntryId.parse("50000000-0000-0000-0000-000000000001")
    private val actualId = FinancialLedgerEntryId.parse("50000000-0000-0000-0000-000000000002")
    private val case = caseFor(TEST_ORGANIZATION_ID)

    private fun caseFor(organizationId: OrganizationId) = DurableReconciliationCase(
        ReconciliationCaseId.of(UUID.fromString("40000000-0000-0000-0000-000000000001")),
        organizationId,
        MarketplaceOrderId.parse("20000000-0000-0000-0000-000000000001"),
        FinancialTraceId.parse("30000000-0000-0000-0000-000000000001"),
        FinancialReconciliationPolicyVersion("policy/1"),
        currency,
        ReconciliationCaseStatus.OPEN,
        Instant.parse("2026-09-13T12:00:00Z"),
        Instant.parse("2026-09-13T12:00:00Z"),
        null,
        1,
        MarketplaceMoney.parse(currency, "10"),
        listOf(
            ReconciliationCaseStageDifference(
                FinancialLedgerStage.SALE,
                MarketplaceMoney.parse(currency, "-100"),
                MarketplaceMoney.parse(currency, "-110"),
                MarketplaceMoney.parse(currency, "-10"),
                MarketplaceMoney.parse(currency, "10"),
                MarketplaceMoney.parse(currency, "0"),
                listOf(expectedId),
                listOf(actualId)
            )
        ),
        listOf(expectedId, actualId)
    )

    private fun List<Enum<*>>.names() = mapTo(linkedSetOf()) { it.name }
    private fun JsonElement.enumNames() = jsonObject.getValue("enum").jsonArray.mapTo(linkedSetOf()) { it.jsonPrimitive.content }
    private fun JsonElement.arrayEnumNames() = jsonObject.getValue("items").enumNames()
    private fun JsonElement.nullableEnumNames(): Set<String> {
        val alternatives = jsonObject.getValue("oneOf").jsonArray.map { it.jsonObject }
        assertTrue(
            alternatives.any { it["type"]?.jsonPrimitive?.content == "null" },
            "Nullable enum must expose an explicit null branch"
        )
        return alternatives.single { it["enum"] != null }
            .getValue("enum").jsonArray.mapTo(linkedSetOf()) { it.jsonPrimitive.content }
    }

    private fun JsonObject.resolveLocalSchema(schema: JsonObject): JsonObject {
        val ref = schema["\$ref"]?.jsonPrimitive?.content ?: return schema
        require(ref.startsWith("#/components/schemas/")) {
            "Only local component schema references are supported"
        }
        val name = ref.removePrefix("#/components/schemas/")
        return getValue("components").jsonObject
            .getValue("schemas").jsonObject
            .getValue(name).jsonObject
    }
}
