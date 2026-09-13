package io.flooow.marketplace.api

import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.reconciliation.*
import io.flooow.organization.OrganizationId
import kotlinx.serialization.json.*
import java.util.UUID

internal const val ECONOMIC_DECISION_ROOM_RECONCILIATION_PATH =
    "/v1/economic-decision-room/reconciliation"

internal class EconomicDecisionRoomApi(
    private val projections: EconomicDecisionRoomProjectionService
) {
    fun detail(organizationId: OrganizationId, rawCaseId: String): JsonObject {
        val caseId = try {
            ReconciliationCaseId.of(UUID.fromString(rawCaseId).also { require(it.toString() == rawCaseId) })
        } catch (_: Exception) {
            throw InvalidEconomicDecisionRoomCaseIdException()
        }
        return when (val result = projections.read(organizationId, caseId)) {
            is EconomicDecisionRoomProjectionReadResult.Found -> projectionJson(result.projection)
            is EconomicDecisionRoomProjectionReadResult.NotFound -> throw EconomicDecisionRoomProjectionNotFoundException()
            EconomicDecisionRoomProjectionReadResult.IntegrityFailure -> throw EconomicDecisionRoomProjectionReadFailureException()
        }
    }
}

private fun projectionJson(value: EconomicDecisionRoomReconciliationProjection) = buildJsonObject {
    put("caseId", value.caseId.value.toString())
    put("marketplaceOrderId", value.marketplaceOrderId.value.toString())
    put("financialTraceId", value.financialTraceId.value.toString())
    put("policyVersion", value.policyVersion.value)
    put("currency", value.currency.code)
    put("reconciliationCaseStatus", value.reconciliationCaseStatus.name)
    put("reconciliationRevision", value.reconciliationRevision)
    put("lastObservedAt", value.lastObservedAt.toString())
    put("projectionStatus", value.projectionStatus.name)
    put("authorityStatus", value.authorityStatus.name)
    put("authorityBlockingReasons", enumArray(value.authorityBlockingReasons.map { it.name }))
    put("governancePermitted", value.governancePermitted)
    put("governanceBlockingReasons", enumArray(value.governanceBlockingReasons.map { it.name }))
    put("projectionBlockingReasons", enumArray(value.projectionBlockingReasons.map { it.name }))
    put("totalQuantifiedLeakage", value.totalQuantifiedLeakage?.let(::decisionRoomMoney) ?: JsonNull)
    put("evidenceReferences", enumArray(value.evidenceReferences))
    put("stages", buildJsonArray { value.stages.forEach { add(stageJson(it)) } })
}

private fun stageJson(value: EconomicDecisionRoomStageProjection) = buildJsonObject {
    put("stage", value.stage.name)
    put("expected", value.expected?.let(::decisionRoomMoney) ?: JsonNull)
    put("actual", value.actual?.let(::decisionRoomMoney) ?: JsonNull)
    put("signedVariance", value.signedVariance?.let(::decisionRoomMoney) ?: JsonNull)
    put("absoluteVariance", value.absoluteVariance?.let(::decisionRoomMoney) ?: JsonNull)
    put("interpretation", value.interpretation?.let { JsonPrimitive(it.name) } ?: JsonNull)
    put("quantifiedLeakage", value.quantifiedLeakage?.let(::decisionRoomMoney) ?: JsonNull)
    put("blockingReason", value.blockingReason?.let { JsonPrimitive(it.name) } ?: JsonNull)
    put("expectedEntryIds", enumArray(value.expectedEntryIds.map { it.value.toString() }))
    put("actualEntryIds", enumArray(value.actualEntryIds.map { it.value.toString() }))
}

private fun decisionRoomMoney(value: MarketplaceMoney) = buildJsonObject {
    put("currency", value.currency.code)
    put("amount", value.amount.toPlainString())
}

private fun enumArray(values: Collection<String>) = buildJsonArray {
    values.sorted().forEach { add(JsonPrimitive(it)) }
}

internal class InvalidEconomicDecisionRoomCaseIdException : RuntimeException()
internal class EconomicDecisionRoomProjectionNotFoundException : RuntimeException()
internal class EconomicDecisionRoomProjectionReadFailureException : RuntimeException()
