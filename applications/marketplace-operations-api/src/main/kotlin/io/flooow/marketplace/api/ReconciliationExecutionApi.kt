package io.flooow.marketplace.api

import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationStatus
import io.flooow.marketplace.operations.economics.reconciliation.GovernedFinancialReconciliationExecutionFailure
import io.flooow.marketplace.operations.economics.reconciliation.GovernedFinancialReconciliationExecutionResult
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseOrchestrationFailure
import io.flooow.marketplace.operations.economics.reconciliation.ReconciliationCaseOrchestrationResult
import io.flooow.organization.OrganizationId
import io.ktor.http.HttpStatusCode
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

internal const val RECONCILIATION_EXECUTION_BASE_PATH =
    "/v1/reconciliation/traces"

internal data class ReconciliationExecutionHttpResult(
    val status: HttpStatusCode,
    val body: JsonObject
)

internal class ReconciliationExecutionProblemException(
    val status: HttpStatusCode,
    val type: String,
    val title: String,
    val detail: String,
    val code: String
) : RuntimeException()

/**
 * Authenticated transport adapter for governed financial reconciliation.
 *
 * The transport may provide only:
 *
 *   authenticated organizationId + canonical traceId
 *
 * It cannot provide or override:
 *
 * - FinancialTrace
 * - reconciliation policy or tolerance
 * - policy version
 * - assessment
 * - fingerprint
 * - snapshot
 * - acceptedAt
 * - reconciliation case revision
 */
internal class ReconciliationExecutionApi(
    private val execute:
        (
            OrganizationId,
            FinancialTraceId
        ) -> GovernedFinancialReconciliationExecutionResult
) {
    fun execute(
        organizationId: OrganizationId,
        rawTraceId: String
    ): ReconciliationExecutionHttpResult {
        val traceId =
            try {
                FinancialTraceId.parse(
                    rawTraceId
                )
            } catch (_: IllegalArgumentException) {
                throw problem(
                    HttpStatusCode.BadRequest,
                    "invalid-reconciliation-trace-id",
                    "Invalid reconciliation trace identifier",
                    "The reconciliation trace identifier is invalid",
                    "INVALID_RECONCILIATION_TRACE_ID"
                )
            }

        return when (
            val result =
                execute(
                    organizationId,
                    traceId
                )
        ) {
            is GovernedFinancialReconciliationExecutionResult.Orchestrated ->
                orchestrated(
                    result
                )

            is GovernedFinancialReconciliationExecutionResult.NotAssessable ->
                throw problem(
                    HttpStatusCode.Conflict,
                    "reconciliation-not-assessable",
                    "Reconciliation not assessable",
                    "The durable financial trace does not yet contain assessable financial facts",
                    "RECONCILIATION_NOT_ASSESSABLE"
                )

            GovernedFinancialReconciliationExecutionResult.TraceNotFound ->
                throw problem(
                    HttpStatusCode.NotFound,
                    "reconciliation-trace-not-found",
                    "Reconciliation trace not found",
                    "The requested durable financial trace was not found",
                    "RECONCILIATION_TRACE_NOT_FOUND"
                )

            GovernedFinancialReconciliationExecutionResult.PolicyUnavailable ->
                throw problem(
                    HttpStatusCode.Conflict,
                    "reconciliation-policy-unavailable",
                    "Reconciliation policy unavailable",
                    "No active governed reconciliation policy is bound to this financial trace context",
                    "RECONCILIATION_POLICY_UNAVAILABLE"
                )

            is GovernedFinancialReconciliationExecutionResult.Failed ->
                failed(
                    result.failure
                )
        }
    }

    private fun orchestrated(
        result: GovernedFinancialReconciliationExecutionResult.Orchestrated
    ): ReconciliationExecutionHttpResult =
        when (
            val orchestration =
                result.orchestration
        ) {
            is ReconciliationCaseOrchestrationResult.Created ->
                caseResult(
                    HttpStatusCode.Created,
                    "CASE_CREATED",
                    result.assessmentStatus,
                    orchestration.value.caseId.value.toString(),
                    orchestration.value.revision
                )

            is ReconciliationCaseOrchestrationResult.Revised ->
                caseResult(
                    HttpStatusCode.OK,
                    "CASE_REVISED",
                    result.assessmentStatus,
                    orchestration.value.caseId.value.toString(),
                    orchestration.value.revision
                )

            is ReconciliationCaseOrchestrationResult.Unchanged ->
                caseResult(
                    HttpStatusCode.OK,
                    "UNCHANGED",
                    result.assessmentStatus,
                    orchestration.value.caseId.value.toString(),
                    orchestration.value.revision
                )

            ReconciliationCaseOrchestrationResult.NotEligible ->
                ReconciliationExecutionHttpResult(
                    HttpStatusCode.OK,
                    buildJsonObject {
                        put(
                            "outcome",
                            "NO_CASE"
                        )
                        put(
                            "assessmentStatus",
                            assessmentStatusName(
                                result.assessmentStatus
                            )
                        )
                    }
                )

            is ReconciliationCaseOrchestrationResult.Rejected ->
                throw problem(
                    HttpStatusCode.InternalServerError,
                    "reconciliation-execution-integrity-failure",
                    "Reconciliation execution integrity failure",
                    "The governed reconciliation boundary rejected an impossible execution context",
                    "RECONCILIATION_EXECUTION_INTEGRITY_FAILURE"
                )

            is ReconciliationCaseOrchestrationResult.Failed ->
                orchestrationFailure(
                    orchestration.failure
                )
        }

    private fun caseResult(
        status: HttpStatusCode,
        outcome: String,
        assessmentStatus: FinancialReconciliationStatus,
        caseId: String,
        revision: Long
    ): ReconciliationExecutionHttpResult =
        ReconciliationExecutionHttpResult(
            status,
            buildJsonObject {
                put(
                    "outcome",
                    outcome
                )
                put(
                    "assessmentStatus",
                    assessmentStatusName(
                        assessmentStatus
                    )
                )
                put(
                    "caseId",
                    caseId
                )
                put(
                    "revision",
                    revision
                )
            }
        )

    private fun failed(
        failure: GovernedFinancialReconciliationExecutionFailure
    ): Nothing =
        when (failure) {
            GovernedFinancialReconciliationExecutionFailure
                .TRACE_READ_FAILURE,
            GovernedFinancialReconciliationExecutionFailure
                .POLICY_READ_FAILURE ->
                throw problem(
                    HttpStatusCode.ServiceUnavailable,
                    "reconciliation-execution-unavailable",
                    "Reconciliation execution unavailable",
                    "A required durable reconciliation authority is temporarily unavailable",
                    "RECONCILIATION_EXECUTION_UNAVAILABLE"
                )

            GovernedFinancialReconciliationExecutionFailure
                .TRACE_INTEGRITY_FAILURE,
            GovernedFinancialReconciliationExecutionFailure
                .POLICY_INTEGRITY_FAILURE ->
                throw problem(
                    HttpStatusCode.InternalServerError,
                    "reconciliation-execution-integrity-failure",
                    "Reconciliation execution integrity failure",
                    "A durable reconciliation authority could not be verified",
                    "RECONCILIATION_EXECUTION_INTEGRITY_FAILURE"
                )

            GovernedFinancialReconciliationExecutionFailure
                .EXECUTION_FAILURE ->
                throw problem(
                    HttpStatusCode.InternalServerError,
                    "reconciliation-execution-failed",
                    "Reconciliation execution failed",
                    "The governed reconciliation execution could not be completed safely",
                    "RECONCILIATION_EXECUTION_FAILED"
                )
        }

    private fun orchestrationFailure(
        failure: ReconciliationCaseOrchestrationFailure
    ): Nothing =
        when (failure) {
            ReconciliationCaseOrchestrationFailure.CONFLICT ->
                throw problem(
                    HttpStatusCode.Conflict,
                    "reconciliation-execution-conflict",
                    "Reconciliation execution conflict",
                    "The durable reconciliation case changed concurrently",
                    "RECONCILIATION_EXECUTION_CONFLICT"
                )

            ReconciliationCaseOrchestrationFailure.UNAVAILABLE,
            ReconciliationCaseOrchestrationFailure.PERSISTENCE ->
                throw problem(
                    HttpStatusCode.ServiceUnavailable,
                    "reconciliation-execution-unavailable",
                    "Reconciliation execution unavailable",
                    "The governed reconciliation case authority is temporarily unavailable",
                    "RECONCILIATION_EXECUTION_UNAVAILABLE"
                )

            ReconciliationCaseOrchestrationFailure.INTEGRITY_FAILURE,
            ReconciliationCaseOrchestrationFailure.ORGANIZATION_MISMATCH ->
                throw problem(
                    HttpStatusCode.InternalServerError,
                    "reconciliation-execution-integrity-failure",
                    "Reconciliation execution integrity failure",
                    "The governed reconciliation case authority could not be verified",
                    "RECONCILIATION_EXECUTION_INTEGRITY_FAILURE"
                )
        }

    private fun problem(
        status: HttpStatusCode,
        typeSuffix: String,
        title: String,
        detail: String,
        code: String
    ): ReconciliationExecutionProblemException =
        ReconciliationExecutionProblemException(
            status = status,
            type =
                "https://flooow.io/problems/" +
                    typeSuffix,
            title = title,
            detail = detail,
            code = code
        )
}

private fun assessmentStatusName(
    status: FinancialReconciliationStatus
): String =
    when (status) {
        FinancialReconciliationStatus.PENDING ->
            "PENDING"

        FinancialReconciliationStatus.PARTIALLY_RECONCILED ->
            "PARTIALLY_RECONCILED"

        FinancialReconciliationStatus.DIVERGENCE ->
            "DIVERGENCE"

        FinancialReconciliationStatus.FULLY_RECONCILED ->
            "FULLY_RECONCILED"
    }
