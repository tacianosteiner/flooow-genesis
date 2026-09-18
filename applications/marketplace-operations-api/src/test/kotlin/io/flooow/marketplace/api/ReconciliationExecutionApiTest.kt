package io.flooow.marketplace.api

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.reconciliation.DurableReconciliationCase
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationNotAssessableReason
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicyVersion
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationStatus
import io.flooow.marketplace.operations.economics.reconciliation.GovernedFinancialReconciliationExecutionFailure
import io.flooow.marketplace.operations.economics.reconciliation.GovernedFinancialReconciliationExecutionResult
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseId
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseOrchestrationFailure
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseOrchestrationResult
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseStageDifference
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseStatus
import io.flooow.organization.OrganizationId
import io.ktor.client.request.bearerAuth
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.HttpStatusCode
import io.ktor.server.testing.testApplication
import java.time.Instant
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertTrue
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

class ReconciliationExecutionApiTest {
    private val organization =
        OrganizationId.parse(
            "33333333-3333-4333-8333-333333333333"
        )

    private val trace =
        FinancialTraceId.parse(
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        )

    @Test
    fun `runtime trigger requires service bearer before execution`() =
        testApplication {
            var calls = 0

            application {
                configureApi(
                    serviceToken =
                        ServiceToken.test(
                            TEST_SERVICE_TOKEN
                        ),
                    serviceOrganizationId =
                        organization,
                    record = { _, _ ->
                        error(
                            "not used"
                        )
                    },
                    reconciliationExecutionApi =
                        ReconciliationExecutionApi {
                                _,
                                _ ->
                            calls += 1

                            error(
                                "must not execute"
                            )
                        }
                )
            }

            val response =
                client.post(
                    path(
                        trace
                    )
                )

            assertEquals(
                HttpStatusCode.Unauthorized,
                response.status
            )

            assertEquals(
                0,
                calls
            )
        }

    @Test
    fun `authenticated principal owns organization and success response exposes only minimal case result`() =
        testApplication {
            var capturedOrganization:
                OrganizationId? = null

            var capturedTrace:
                FinancialTraceId? = null

            application {
                configureApi(
                    serviceToken =
                        ServiceToken.test(
                            TEST_SERVICE_TOKEN
                        ),
                    serviceOrganizationId =
                        organization,
                    record = { _, _ ->
                        error(
                            "not used"
                        )
                    },
                    reconciliationExecutionApi =
                        ReconciliationExecutionApi {
                                org,
                                traceId ->
                            capturedOrganization =
                                org

                            capturedTrace =
                                traceId

                            GovernedFinancialReconciliationExecutionResult
                                .Orchestrated(
                                    FinancialReconciliationStatus
                                        .DIVERGENCE,
                                    ReconciliationCaseOrchestrationResult
                                        .Created(
                                            case(
                                                org,
                                                traceId
                                            )
                                        )
                                )
                        }
                )
            }

            val response =
                client.post(
                    path(
                        trace
                    )
                ) {
                    bearerAuth(
                        TEST_SERVICE_TOKEN
                    )
                }

            assertEquals(
                HttpStatusCode.Created,
                response.status
            )

            assertEquals(
                organization,
                capturedOrganization
            )

            assertEquals(
                trace,
                capturedTrace
            )

            assertEquals(
                "no-store",
                response.headers[
                    "Cache-Control"
                ]
            )

            val body =
                Json.parseToJsonElement(
                    response.bodyAsText()
                ).jsonObject

            assertEquals(
                setOf(
                    "outcome",
                    "assessmentStatus",
                    "caseId",
                    "revision"
                ),
                body.keys
            )

            assertEquals(
                "CASE_CREATED",
                body.getValue(
                    "outcome"
                ).jsonPrimitive.content
            )

            assertEquals(
                "DIVERGENCE",
                body.getValue(
                    "assessmentStatus"
                ).jsonPrimitive.content
            )

            assertEquals(
                1L,
                body.getValue(
                    "revision"
                ).jsonPrimitive.content.toLong()
            )

            val forbidden =
                setOf(
                    "organizationId",
                    "policy",
                    "policyVersion",
                    "tolerances",
                    "assessment",
                    "fingerprint",
                    "snapshot",
                    "acceptedAt"
                )

            assertTrue(
                forbidden.none {
                    it in body
                }
            )
        }

    @Test
    fun `runtime trigger rejects caller body query and organization injection before execution`() =
        testApplication {
            var calls = 0

            application {
                configureApi(
                    serviceToken =
                        ServiceToken.test(
                            TEST_SERVICE_TOKEN
                        ),
                    serviceOrganizationId =
                        organization,
                    record = { _, _ ->
                        error(
                            "not used"
                        )
                    },
                    reconciliationExecutionApi =
                        ReconciliationExecutionApi {
                                _,
                                _ ->
                            calls += 1

                            GovernedFinancialReconciliationExecutionResult
                                .TraceNotFound
                        }
                )
            }

            val query =
                client.post(
                    path(
                        trace
                    ) +
                        "?organizationId=" +
                        "44444444-4444-4444-8444-444444444444"
                ) {
                    bearerAuth(
                        TEST_SERVICE_TOKEN
                    )
                }

            val body =
                client.post(
                    path(
                        trace
                    )
                ) {
                    bearerAuth(
                        TEST_SERVICE_TOKEN
                    )

                    setBody(
                        """{"organizationId":"44444444-4444-4444-8444-444444444444","policyVersion":"attacker/1"}"""
                    )
                }

            assertProblem(
                query.status,
                query.bodyAsText(),
                HttpStatusCode.BadRequest,
                "MALFORMED_REQUEST"
            )

            assertProblem(
                body.status,
                body.bodyAsText(),
                HttpStatusCode.BadRequest,
                "MALFORMED_REQUEST"
            )

            assertEquals(
                0,
                calls
            )
        }

    @Test
    fun `trace identifier must be canonical lowercase uuid`() =
        testApplication {
            var calls = 0

            application {
                configureApi(
                    serviceToken =
                        ServiceToken.test(
                            TEST_SERVICE_TOKEN
                        ),
                    serviceOrganizationId =
                        organization,
                    record = { _, _ ->
                        error(
                            "not used"
                        )
                    },
                    reconciliationExecutionApi =
                        ReconciliationExecutionApi {
                                _,
                                _ ->
                            calls += 1

                            error(
                                "must not execute"
                            )
                        }
                )
            }

            val uppercase =
                client.post(
                    "$RECONCILIATION_EXECUTION_BASE_PATH/" +
                        "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA" +
                        "/execute"
                ) {
                    bearerAuth(
                        TEST_SERVICE_TOKEN
                    )
                }

            assertProblem(
                uppercase.status,
                uppercase.bodyAsText(),
                HttpStatusCode.BadRequest,
                "INVALID_RECONCILIATION_TRACE_ID"
            )

            assertEquals(
                0,
                calls
            )
        }

    @Test
    fun `runtime result classification preserves not found conflict unavailable and integrity boundaries`() =
        testApplication {
            application {
                configureApi(
                    serviceToken =
                        ServiceToken.test(
                            TEST_SERVICE_TOKEN
                        ),
                    serviceOrganizationId =
                        organization,
                    record = { _, _ ->
                        error(
                            "not used"
                        )
                    },
                    reconciliationExecutionApi =
                        ReconciliationExecutionApi {
                                _,
                                traceId ->
                            when (
                                traceId.value.toString()
                                    .first()
                            ) {
                                '1' ->
                                    GovernedFinancialReconciliationExecutionResult
                                        .TraceNotFound

                                '2' ->
                                    GovernedFinancialReconciliationExecutionResult
                                        .PolicyUnavailable

                                '3' ->
                                    GovernedFinancialReconciliationExecutionResult
                                        .NotAssessable(
                                            FinancialReconciliationNotAssessableReason
                                                .NO_FINANCIAL_FACTS
                                        )

                                '4' ->
                                    GovernedFinancialReconciliationExecutionResult
                                        .Failed(
                                            GovernedFinancialReconciliationExecutionFailure
                                                .TRACE_READ_FAILURE
                                        )

                                '5' ->
                                    GovernedFinancialReconciliationExecutionResult
                                        .Failed(
                                            GovernedFinancialReconciliationExecutionFailure
                                                .POLICY_INTEGRITY_FAILURE
                                        )

                                '6' ->
                                    GovernedFinancialReconciliationExecutionResult
                                        .Orchestrated(
                                            FinancialReconciliationStatus
                                                .DIVERGENCE,
                                            ReconciliationCaseOrchestrationResult
                                                .Failed(
                                                    ReconciliationCaseOrchestrationFailure
                                                        .CONFLICT
                                                )
                                        )

                                else ->
                                    GovernedFinancialReconciliationExecutionResult
                                        .Orchestrated(
                                            FinancialReconciliationStatus
                                                .DIVERGENCE,
                                            ReconciliationCaseOrchestrationResult
                                                .Failed(
                                                    ReconciliationCaseOrchestrationFailure
                                                        .UNAVAILABLE
                                                )
                                        )
                            }
                        }
                )
            }

            suspend fun execute(
                id: String
            ) =
                client.post(
                    "$RECONCILIATION_EXECUTION_BASE_PATH/$id/execute"
                ) {
                    bearerAuth(
                        TEST_SERVICE_TOKEN
                    )
                }

            val notFound =
                execute(
                    "10000000-0000-4000-8000-000000000001"
                )

            val policyMissing =
                execute(
                    "20000000-0000-4000-8000-000000000001"
                )

            val notAssessable =
                execute(
                    "30000000-0000-4000-8000-000000000001"
                )

            val readUnavailable =
                execute(
                    "40000000-0000-4000-8000-000000000001"
                )

            val integrity =
                execute(
                    "50000000-0000-4000-8000-000000000001"
                )

            val conflict =
                execute(
                    "60000000-0000-4000-8000-000000000001"
                )

            val persistenceUnavailable =
                execute(
                    "70000000-0000-4000-8000-000000000001"
                )

            assertProblem(
                notFound.status,
                notFound.bodyAsText(),
                HttpStatusCode.NotFound,
                "RECONCILIATION_TRACE_NOT_FOUND"
            )

            assertProblem(
                policyMissing.status,
                policyMissing.bodyAsText(),
                HttpStatusCode.Conflict,
                "RECONCILIATION_POLICY_UNAVAILABLE"
            )

            assertProblem(
                notAssessable.status,
                notAssessable.bodyAsText(),
                HttpStatusCode.Conflict,
                "RECONCILIATION_NOT_ASSESSABLE"
            )

            assertProblem(
                readUnavailable.status,
                readUnavailable.bodyAsText(),
                HttpStatusCode.ServiceUnavailable,
                "RECONCILIATION_EXECUTION_UNAVAILABLE"
            )

            assertProblem(
                integrity.status,
                integrity.bodyAsText(),
                HttpStatusCode.InternalServerError,
                "RECONCILIATION_EXECUTION_INTEGRITY_FAILURE"
            )

            assertProblem(
                conflict.status,
                conflict.bodyAsText(),
                HttpStatusCode.Conflict,
                "RECONCILIATION_EXECUTION_CONFLICT"
            )

            assertProblem(
                persistenceUnavailable.status,
                persistenceUnavailable.bodyAsText(),
                HttpStatusCode.ServiceUnavailable,
                "RECONCILIATION_EXECUTION_UNAVAILABLE"
            )
        }

    @Test
    fun `non divergence assessment is successful but cannot manufacture a reconciliation case`() =
        testApplication {
            application {
                configureApi(
                    serviceToken =
                        ServiceToken.test(
                            TEST_SERVICE_TOKEN
                        ),
                    serviceOrganizationId =
                        organization,
                    record = { _, _ ->
                        error(
                            "not used"
                        )
                    },
                    reconciliationExecutionApi =
                        ReconciliationExecutionApi {
                                _,
                                _ ->
                            GovernedFinancialReconciliationExecutionResult
                                .Orchestrated(
                                    FinancialReconciliationStatus
                                        .FULLY_RECONCILED,
                                    ReconciliationCaseOrchestrationResult
                                        .NotEligible
                                )
                        }
                )
            }

            val response =
                client.post(
                    path(
                        trace
                    )
                ) {
                    bearerAuth(
                        TEST_SERVICE_TOKEN
                    )
                }

            assertEquals(
                HttpStatusCode.OK,
                response.status
            )

            val body =
                Json.parseToJsonElement(
                    response.bodyAsText()
                ).jsonObject

            assertEquals(
                setOf(
                    "outcome",
                    "assessmentStatus"
                ),
                body.keys
            )

            assertEquals(
                "NO_CASE",
                body.getValue(
                    "outcome"
                ).jsonPrimitive.content
            )

            assertEquals(
                "FULLY_RECONCILED",
                body.getValue(
                    "assessmentStatus"
                ).jsonPrimitive.content
            )
        }

    @Test
    fun `committed OpenAPI exposes authenticated bodyless trace execution without internal authorities`() {
        val resource =
            assertNotNull(
                ReconciliationExecutionApiTest::class.java
                    .getResource(
                        "/openapi.json"
                    )
            )

        val root =
            Json.parseToJsonElement(
                resource.readText()
            ).jsonObject

        val operation =
            root.getValue(
                "paths"
            ).jsonObject
                .getValue(
                    "$RECONCILIATION_EXECUTION_BASE_PATH/{traceId}/execute"
                ).jsonObject
                .getValue(
                    "post"
                ).jsonObject

        assertFalse(
            "requestBody" in operation
        )

        val security =
            operation.getValue(
                "security"
            ).jsonArray

        assertEquals(
            1,
            security.size
        )

        assertTrue(
            "serviceBearer" in
                security.single()
                    .jsonObject
        )

        val responses =
            operation.getValue(
                "responses"
            ).jsonObject

        assertEquals(
            setOf(
                "200",
                "201",
                "400",
                "401",
                "404",
                "409",
                "500",
                "503"
            ),
            responses.keys
        )

        val schema =
            root.getValue(
                "components"
            ).jsonObject
                .getValue(
                    "schemas"
                ).jsonObject
                .getValue(
                    "ReconciliationExecutionResponse"
                ).jsonObject

        assertEquals(
            false,
            schema.getValue(
                "additionalProperties"
            ).jsonPrimitive.boolean
        )

        val properties =
            schema.getValue(
                "properties"
            ).jsonObject

        assertEquals(
            setOf(
                "outcome",
                "assessmentStatus",
                "caseId",
                "revision"
            ),
            properties.keys
        )

        val forbidden =
            setOf(
                "organizationId",
                "financialTrace",
                "policy",
                "policyVersion",
                "tolerances",
                "assessment",
                "fingerprint",
                "snapshot",
                "acceptedAt"
            )

        assertTrue(
            forbidden.none {
                it in properties
            }
        )
    }

    private fun case(
        organizationId: OrganizationId,
        traceId: FinancialTraceId
    ): DurableReconciliationCase {
        val currency =
            MarketplaceCurrency(
                "BRL"
            )

        val at =
            Instant.parse(
                "2026-09-13T20:30:00Z"
            )

        return DurableReconciliationCase(
            caseId =
                ReconciliationCaseId.of(
                    UUID.fromString(
                        "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
                    )
                ),
            organizationId =
                organizationId,
            orderId =
                MarketplaceOrderId(
                    UUID.fromString(
                        "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
                    )
                ),
            traceId =
                traceId,
            policyVersion =
                FinancialReconciliationPolicyVersion(
                    "policy/1"
                ),
            currency =
                currency,
            status =
                ReconciliationCaseStatus.OPEN,
            openedAt =
                at,
            lastObservedAt =
                at,
            resolvedAt =
                null,
            revision =
                1L,
            absoluteDifferenceSummary =
                MarketplaceMoney.parse(
                    currency,
                    "10"
                ),
            stages =
                listOf(
                    ReconciliationCaseStageDifference(
                        stage =
                            FinancialLedgerStage.TAX,
                        expected =
                            MarketplaceMoney.parse(
                                currency,
                                "100"
                            ),
                        actual =
                            MarketplaceMoney.parse(
                                currency,
                                "90"
                            ),
                        signedDifference =
                            MarketplaceMoney.parse(
                                currency,
                                "-10"
                            ),
                        absoluteDifference =
                            MarketplaceMoney.parse(
                                currency,
                                "10"
                            ),
                        tolerance =
                            MarketplaceMoney.parse(
                                currency,
                                "0"
                            ),
                        expectedEntryIds =
                            emptyList(),
                        actualEntryIds =
                            emptyList()
                    )
                ),
            evidenceEntryIds =
                emptyList()
        )
    }

    private fun path(
        traceId: FinancialTraceId
    ): String =
        "$RECONCILIATION_EXECUTION_BASE_PATH/" +
            traceId.value.toString() +
            "/execute"

    private fun assertProblem(
        actualStatus: HttpStatusCode,
        rawBody: String,
        expectedStatus: HttpStatusCode,
        expectedCode: String
    ) {
        assertEquals(
            expectedStatus,
            actualStatus
        )

        val body =
            Json.parseToJsonElement(
                rawBody
            ).jsonObject

        assertEquals(
            expectedCode,
            body.getValue(
                "code"
            ).jsonPrimitive.content
        )
    }
}
