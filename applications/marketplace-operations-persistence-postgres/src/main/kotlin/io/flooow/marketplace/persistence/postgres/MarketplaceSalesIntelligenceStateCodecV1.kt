package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.ContributionMarginUndefinedReason
import io.flooow.marketplace.operations.economics.EconomicCalculationPolicyVersion
import io.flooow.marketplace.operations.economics.EconomicComponent
import io.flooow.marketplace.operations.economics.EconomicComponentId
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.EconomicExternalReference
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceAbsenceReason
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssemblyNotReadyReason
import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssemblyPolicyVersion
import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthQuality
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceCalculationSnapshot
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceContributionMarginSnapshot
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceState
import io.flooow.marketplace.operations.economics.sales.calculationPolicyVersionOf
import io.flooow.organization.OrganizationId
import java.math.BigDecimal
import java.time.Instant
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

internal object MarketplaceSalesIntelligenceStateCodecV1 {
    const val FORMAT_VERSION = 1
    data class EncodedState(val stateKind: String, val calculationPolicyVersion: String?, val calculationKind: String?, val payload: String)
    fun decode(organizationId: OrganizationId, marketplaceOrderId: MarketplaceOrderId,
        assemblyPolicyVersion: MarketplaceEconomicTruthAssemblyPolicyVersion, stateKind: String,
        calculationPolicyText: String?, calculationKind: String?, payload: JsonObject): MarketplaceSalesIntelligenceState {
        return when (stateKind) {
            "UNRESOLVED" -> {
                val reasons = payload.requiredArray("reasons")
                    .map { MarketplaceEconomicTruthAssemblyNotReadyReason.valueOf(it.jsonPrimitive.content) }
                    .toSet()
                MarketplaceSalesIntelligenceState.Unresolved(
                    assemblyPolicyVersion,
                    reasons
                )
            }

            "CALCULATED" -> {
                val policyText = calculationPolicyText
                    ?: error("calculation policy missing")
                val kind = calculationKind
                    ?: error("calculation kind missing")
                val calculationPolicyVersion = EconomicCalculationPolicyVersion(policyText)
                val snapshot = decodeCalculationSnapshot(
                    kind = kind,
                    payload = payload,
                    organizationId = organizationId,
                    marketplaceOrderId = marketplaceOrderId
                )
                val calculationResult = snapshot.toCalculationResult(
                    organizationId,
                    marketplaceOrderId,
                    calculationPolicyVersion
                )
                MarketplaceSalesIntelligenceState.Calculated(
                    assemblyPolicyVersion = assemblyPolicyVersion,
                    calculationPolicyVersion = calculationPolicyVersion,
                    calculationResult = calculationResult
                )
            }

            else -> error("unknown projection state")
        }
    }
    fun encode(state: MarketplaceSalesIntelligenceState): EncodedState =
        when (state) {
            is MarketplaceSalesIntelligenceState.Unresolved -> EncodedState(
                stateKind = "UNRESOLVED",
                calculationPolicyVersion = null,
                calculationKind = null,
                payload = buildJsonObject {
                    put(
                        "reasons",
                        buildJsonArray {
                            state.reasons
                                .sortedBy { it.name }
                                .forEach { add(JsonPrimitive(it.name)) }
                        }
                    )
                }.toString()
            )

            is MarketplaceSalesIntelligenceState.Calculated -> {
                val snapshot = MarketplaceSalesIntelligenceCalculationSnapshot.from(
                    state.calculationResult
                )
                val kind = when (snapshot) {
                    is MarketplaceSalesIntelligenceCalculationSnapshot.Complete -> "COMPLETE"
                    is MarketplaceSalesIntelligenceCalculationSnapshot.Incomplete -> "INCOMPLETE"
                }
                EncodedState(
                    stateKind = "CALCULATED",
                    calculationPolicyVersion =
                        calculationPolicyVersionOf(state.calculationResult).value,
                    calculationKind = kind,
                    payload = encodeCalculationSnapshot(snapshot).toString()
                )
            }
        }

    private fun encodeCalculationSnapshot(
        snapshot: MarketplaceSalesIntelligenceCalculationSnapshot
    ): JsonObject = when (snapshot) {
        is MarketplaceSalesIntelligenceCalculationSnapshot.Complete -> buildJsonObject {
            put("marketplace", JsonPrimitive(snapshot.marketplace.value))
            put("externalOrderId", JsonPrimitive(snapshot.externalOrderId.value))
            put("orderOccurredAt", JsonPrimitive(snapshot.orderOccurredAt.toString()))
            put("currency", JsonPrimitive(snapshot.currency.code))
            put("grossRevenue", money(snapshot.grossRevenue))
            put("totalMarketplaceFees", money(snapshot.totalMarketplaceFees))
            put("totalShipping", money(snapshot.totalShipping))
            put("totalAdvertising", money(snapshot.totalAdvertising))
            put("totalTaxes", money(snapshot.totalTaxes))
            put("totalProductCost", money(snapshot.totalProductCost))
            put("totalFinancialCost", money(snapshot.totalFinancialCost))
            put("totalOtherAdjustments", money(snapshot.totalOtherAdjustments))
            put("contribution", money(snapshot.contribution))
            put("contributionMargin", contributionMargin(snapshot.contributionMargin))
            put("truthQuality", JsonPrimitive(snapshot.truthQuality.name))
            put("components", components(snapshot.components))
        }

        is MarketplaceSalesIntelligenceCalculationSnapshot.Incomplete -> buildJsonObject {
            put(
                "missingTypes",
                buildJsonArray {
                    snapshot.missingTypes.forEach { add(JsonPrimitive(it.name)) }
                }
            )
            put(
                "partialTypes",
                buildJsonArray {
                    snapshot.partialTypes.forEach { add(JsonPrimitive(it.name)) }
                }
            )
            put("suppliedComponents", components(snapshot.suppliedComponents))
        }
    }

    private fun decodeCalculationSnapshot(
        kind: String,
        payload: JsonObject,
        organizationId: OrganizationId,
        marketplaceOrderId: MarketplaceOrderId
    ): MarketplaceSalesIntelligenceCalculationSnapshot = when (kind) {
        "COMPLETE" -> MarketplaceSalesIntelligenceCalculationSnapshot.Complete(
            marketplace = MarketplaceKey(payload.requiredString("marketplace")),
            externalOrderId = MarketplaceExternalOrderId(
                payload.requiredString("externalOrderId")
            ),
            orderOccurredAt = Instant.parse(payload.requiredString("orderOccurredAt")),
            currency = MarketplaceCurrency(payload.requiredString("currency")),
            grossRevenue = payload.requiredObject("grossRevenue").toMoney(),
            totalMarketplaceFees = payload.requiredObject("totalMarketplaceFees").toMoney(),
            totalShipping = payload.requiredObject("totalShipping").toMoney(),
            totalAdvertising = payload.requiredObject("totalAdvertising").toMoney(),
            totalTaxes = payload.requiredObject("totalTaxes").toMoney(),
            totalProductCost = payload.requiredObject("totalProductCost").toMoney(),
            totalFinancialCost = payload.requiredObject("totalFinancialCost").toMoney(),
            totalOtherAdjustments = payload.requiredObject("totalOtherAdjustments").toMoney(),
            contribution = payload.requiredObject("contribution").toMoney(),
            contributionMargin = payload.requiredObject("contributionMargin").toContributionMargin(),
            truthQuality = MarketplaceEconomicTruthQuality.valueOf(
                payload.requiredString("truthQuality")
            ),
            components = decodeComponents(
                payload.requiredArray("components"),
                organizationId,
                marketplaceOrderId
            )
        )

        "INCOMPLETE" -> MarketplaceSalesIntelligenceCalculationSnapshot.Incomplete(
            missingTypes = payload.requiredArray("missingTypes")
                .map { EconomicComponentType.valueOf(it.jsonPrimitive.content) },
            partialTypes = payload.requiredArray("partialTypes")
                .map { EconomicComponentType.valueOf(it.jsonPrimitive.content) },
            suppliedComponents = decodeComponents(
                payload.requiredArray("suppliedComponents"),
                organizationId,
                marketplaceOrderId
            )
        )

        else -> error("unknown calculation kind")
    }

    private fun money(value: MarketplaceMoney): JsonObject = buildJsonObject {
        put("currency", JsonPrimitive(value.currency.code))
        put("amount", JsonPrimitive(value.amount.toPlainString()))
    }

    private fun JsonObject.toMoney(): MarketplaceMoney =
        MarketplaceMoney.parse(
            MarketplaceCurrency(requiredString("currency")),
            requiredString("amount")
        )

    private fun contributionMargin(
        value: MarketplaceSalesIntelligenceContributionMarginSnapshot
    ): JsonObject = when (value) {
        is MarketplaceSalesIntelligenceContributionMarginSnapshot.Defined ->
            buildJsonObject {
                put("kind", JsonPrimitive("DEFINED"))
                put("value", JsonPrimitive(value.decimalValue.toPlainString()))
            }

        is MarketplaceSalesIntelligenceContributionMarginSnapshot.Undefined ->
            buildJsonObject {
                put("kind", JsonPrimitive("UNDEFINED"))
                put("reason", JsonPrimitive(value.reason.name))
            }
    }

    private fun JsonObject.toContributionMargin():
        MarketplaceSalesIntelligenceContributionMarginSnapshot =
        when (requiredString("kind")) {
            "DEFINED" ->
                MarketplaceSalesIntelligenceContributionMarginSnapshot.Defined(
                    BigDecimal(requiredString("value"))
                )
            "UNDEFINED" ->
                MarketplaceSalesIntelligenceContributionMarginSnapshot.Undefined(
                    ContributionMarginUndefinedReason.valueOf(requiredString("reason"))
                )
            else -> error("unknown contribution margin kind")
        }

    private fun components(values: List<EconomicComponent>): JsonArray =
        buildJsonArray {
            values.forEach { value ->
                add(
                    buildJsonObject {
                        put("id", JsonPrimitive(value.id.value.toString()))
                        put("type", JsonPrimitive(value.type.name))
                        put("direction", JsonPrimitive(value.direction.name))
                        put("magnitude", money(value.magnitude))
                        put("source", source(value.source))
                        put("occurredAt", JsonPrimitive(value.occurredAt.toString()))
                        put("quality", JsonPrimitive(value.quality.name))
                    }
                )
            }
        }

    private fun decodeComponents(
        values: JsonArray,
        organizationId: OrganizationId,
        marketplaceOrderId: MarketplaceOrderId
    ): List<EconomicComponent> = values.map { element ->
        val value = element.jsonObject
        EconomicComponent(
            organizationId = organizationId,
            id = EconomicComponentId.parse(value.requiredString("id")),
            orderId = marketplaceOrderId,
            type = EconomicComponentType.valueOf(value.requiredString("type")),
            direction = EconomicDirection.valueOf(value.requiredString("direction")),
            magnitude = value.requiredObject("magnitude").toMoney(),
            source = value.requiredObject("source").toSource(),
            occurredAt = Instant.parse(value.requiredString("occurredAt")),
            quality = EconomicEvidenceQuality.valueOf(value.requiredString("quality"))
        )
    }

    private fun source(value: EconomicSource): JsonObject = buildJsonObject {
        put("kind", JsonPrimitive(value.kind.name))
        put("systemKey", JsonPrimitive(value.systemKey.value))
        when (val reference = value.externalReference) {
            is EconomicExternalReferenceState.Present -> {
                put("referenceKind", JsonPrimitive("PRESENT"))
                put("reference", JsonPrimitive(reference.reference.value))
            }
            is EconomicExternalReferenceState.Absent -> {
                put("referenceKind", JsonPrimitive("ABSENT"))
                put("absenceReason", JsonPrimitive(reference.reason.name))
            }
        }
    }

    private fun JsonObject.toSource(): EconomicSource {
        val externalReference = when (requiredString("referenceKind")) {
            "PRESENT" ->
                EconomicExternalReferenceState.Present(
                    EconomicExternalReference(requiredString("reference"))
                )
            "ABSENT" ->
                EconomicExternalReferenceState.Absent(
                    EconomicExternalReferenceAbsenceReason.valueOf(
                        requiredString("absenceReason")
                    )
                )
            else -> error("unknown source reference kind")
        }
        return EconomicSource(
            kind = EconomicSourceKind.valueOf(requiredString("kind")),
            systemKey = EconomicSourceSystemKey(requiredString("systemKey")),
            externalReference = externalReference
        )
    }

    private fun JsonObject.requiredString(name: String): String =
        get(name)?.jsonPrimitive?.contentOrNull ?: error("missing payload field")

    private fun JsonObject.requiredObject(name: String): JsonObject =
        get(name)?.jsonObject ?: error("missing payload object")

    private fun JsonObject.requiredArray(name: String): JsonArray =
        get(name)?.jsonArray ?: error("missing payload array")


    fun encodeFrozen(state: MarketplaceSalesIntelligenceState): EncodedState = encode(canonicalState(state))
    fun decodeFrozen(organizationId: OrganizationId, orderId: MarketplaceOrderId, assembly: MarketplaceEconomicTruthAssemblyPolicyVersion,
        kind: String, policy: String?, calculationKind: String?, payload: JsonObject): MarketplaceSalesIntelligenceState {
        require((kind == "UNRESOLVED" && policy == null && calculationKind == null) || (kind == "CALCULATED" && policy != null && calculationKind != null))
        val state = decode(organizationId, orderId, assembly, kind, policy, calculationKind, payload)
        require(Json.parseToJsonElement(encodeFrozen(state).payload) == payload) { "Frozen payload is noncanonical or contains unknown/invalid fields" }
        return state
    }
    private fun canonicalState(state: MarketplaceSalesIntelligenceState): MarketplaceSalesIntelligenceState = when(state) {
        is MarketplaceSalesIntelligenceState.Unresolved -> state
        is MarketplaceSalesIntelligenceState.Calculated -> {
            val frozen = when(val snapshot = MarketplaceSalesIntelligenceCalculationSnapshot.from(state.calculationResult)) {
                is MarketplaceSalesIntelligenceCalculationSnapshot.Incomplete -> snapshot.copy(missingTypes = snapshot.missingTypes.sortedBy { it.name },
                    partialTypes = snapshot.partialTypes.sortedBy { it.name }, suppliedComponents = snapshot.suppliedComponents.sortedBy { it.id.value.toString() })
                is MarketplaceSalesIntelligenceCalculationSnapshot.Complete -> snapshot.copy(components = snapshot.components.sortedBy { it.id.value.toString() })
            }
            val subject = when(val result = state.calculationResult) {
                is io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthCalculationResult.Incomplete -> result.organizationId to result.orderId
                is io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthCalculationResult.Complete -> result.result.organizationId to result.result.orderId
            }
            state.copy(calculationResult = frozen.toCalculationResult(subject.first, subject.second, state.calculationPolicyVersion))
        }
    }
}
