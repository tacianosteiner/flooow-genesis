package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.organization.OrganizationId
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put

const val FINANCIAL_RECONCILIATION_ASSESSMENT_SNAPSHOT_SCHEMA_VERSION = 1

class FinancialReconciliationAssessmentSnapshot internal constructor(
    val schemaVersion: Int,
    val json: String
) {
    init {
        require(schemaVersion == FINANCIAL_RECONCILIATION_ASSESSMENT_SNAPSHOT_SCHEMA_VERSION) {
            "Unsupported financial reconciliation assessment snapshot schema version"
        }
    }

    override fun equals(other: Any?): Boolean =
        other is FinancialReconciliationAssessmentSnapshot &&
            schemaVersion == other.schemaVersion &&
            json == other.json

    override fun hashCode(): Int = 31 * schemaVersion + json.hashCode()
    override fun toString(): String = "[REDACTED]"

    companion object {
        fun capture(assessment: FinancialReconciliationAssessment): FinancialReconciliationAssessmentSnapshot =
            FinancialReconciliationAssessmentSnapshotCodec.capture(assessment)

        fun parse(
            persistedSchemaVersion: Int,
            json: String
        ): FinancialReconciliationAssessmentSnapshot =
            FinancialReconciliationAssessmentSnapshotCodec.parse(persistedSchemaVersion, json)
    }
}

data class VerifiedFinancialReconciliationAssessmentSnapshot(
    val assessment: FinancialReconciliationAssessment,
    val fingerprint: FinancialReconciliationAssessmentFingerprint
) {
    override fun toString(): String = "[REDACTED]"
}

object FinancialReconciliationAssessmentSnapshotCodec {
    private val json = Json {
        isLenient = false
        ignoreUnknownKeys = false
    }

    fun capture(assessment: FinancialReconciliationAssessment): FinancialReconciliationAssessmentSnapshot =
        FinancialReconciliationAssessmentSnapshot(
            schemaVersion = FINANCIAL_RECONCILIATION_ASSESSMENT_SNAPSHOT_SCHEMA_VERSION,
            json = encodeAssessment(assessment).toString()
        )

    fun parse(
        persistedSchemaVersion: Int,
        payload: String
    ): FinancialReconciliationAssessmentSnapshot {
        require(persistedSchemaVersion == FINANCIAL_RECONCILIATION_ASSESSMENT_SNAPSHOT_SCHEMA_VERSION) {
            "Unsupported financial reconciliation assessment snapshot schema version"
        }
        val root = parseObject(payload)
        requireExactKeys(
            root,
            setOf("schemaVersion", "organizationId", "traceId", "orderId", "currency", "policyVersion", "status", "lines"),
            "assessment snapshot"
        )
        val embeddedVersion = requireInteger(root, "schemaVersion")
        require(embeddedVersion == persistedSchemaVersion) {
            "Persisted snapshot schema version must match embedded schemaVersion"
        }
        val assessment = decodeAssessment(root)
        return FinancialReconciliationAssessmentSnapshot(
            schemaVersion = persistedSchemaVersion,
            json = encodeAssessment(assessment).toString()
        )
    }

    fun rehydrate(
        snapshot: FinancialReconciliationAssessmentSnapshot
    ): VerifiedFinancialReconciliationAssessmentSnapshot {
        val assessment = decodeAssessment(parseObject(snapshot.json))
        return VerifiedFinancialReconciliationAssessmentSnapshot(
            assessment = assessment,
            fingerprint = FinancialReconciliationAssessmentFingerprinter.fingerprint(assessment)
        )
    }

    fun verify(
        snapshot: FinancialReconciliationAssessmentSnapshot,
        expectedFingerprint: FinancialReconciliationAssessmentFingerprint
    ): VerifiedFinancialReconciliationAssessmentSnapshot {
        val restored = rehydrate(snapshot)
        require(restored.fingerprint == expectedFingerprint) {
            "Assessment snapshot fingerprint mismatch"
        }
        return restored
    }

    private fun encodeAssessment(assessment: FinancialReconciliationAssessment): JsonObject =
        buildJsonObject {
            put("schemaVersion", JsonPrimitive(FINANCIAL_RECONCILIATION_ASSESSMENT_SNAPSHOT_SCHEMA_VERSION))
            put("organizationId", JsonPrimitive(assessment.organizationId.value.toString()))
            put("traceId", JsonPrimitive(assessment.traceId.valueForPersistence().toString()))
            put("orderId", JsonPrimitive(assessment.orderId.value.toString()))
            put("currency", JsonPrimitive(assessment.currency.code))
            put("policyVersion", JsonPrimitive(assessment.policyVersion.value))
            put("status", JsonPrimitive(snapshotStatusName(assessment.status)))
            put(
                "lines",
                buildJsonArray {
                    assessment.lines
                        .sortedBy { canonicalStageIndex(it.stage) }
                        .forEach { add(encodeLine(it)) }
                }
            )
        }

    private fun encodeLine(line: FinancialReconciliationLine): JsonObject =
        buildJsonObject {
            put("stage", JsonPrimitive(snapshotStageName(line.stage)))
            put("status", JsonPrimitive(snapshotStatusName(line.status)))
            put("expected", encodeSide(line.expected))
            put("actual", encodeSide(line.actual))
            put("difference", encodeDifference(line.difference))
        }

    private fun encodeSide(side: FinancialReconciliationSide): JsonObject =
        when (side) {
            FinancialReconciliationSide.NotObserved ->
                buildJsonObject { put("kind", JsonPrimitive("NOT_OBSERVED")) }
            is FinancialReconciliationSide.Observed ->
                buildJsonObject {
                    put("kind", JsonPrimitive("OBSERVED"))
                    put("netAmount", encodeMoney(side.netAmount))
                    put(
                        "effectiveEntryIds",
                        buildJsonArray {
                            FinancialReconciliationAssessmentCanonicalizerV1
                                .canonicalEntryIdStrings(side.effectiveEntryIds)
                                .forEach { add(JsonPrimitive(it)) }
                        }
                    )
                }
        }

    private fun encodeDifference(difference: FinancialReconciliationDifference): JsonObject =
        when (difference) {
            FinancialReconciliationDifference.NotComparable ->
                buildJsonObject { put("kind", JsonPrimitive("NOT_COMPARABLE")) }
            is FinancialReconciliationDifference.Compared ->
                buildJsonObject {
                    put("kind", JsonPrimitive("COMPARED"))
                    put("signedDifference", encodeMoney(difference.signedDifference))
                    put("absoluteDifference", encodeMoney(difference.absoluteDifference))
                    put("tolerance", encodeMoney(difference.tolerance))
                }
        }

    private fun encodeMoney(value: MarketplaceMoney): JsonObject =
        buildJsonObject {
            put("currency", JsonPrimitive(value.currency.code))
            put(
                "amount",
                JsonPrimitive(FinancialReconciliationAssessmentCanonicalizerV1.canonicalMoneyText(value))
            )
        }

    private fun decodeAssessment(root: JsonObject): FinancialReconciliationAssessment {
        requireExactKeys(
            root,
            setOf("schemaVersion", "organizationId", "traceId", "orderId", "currency", "policyVersion", "status", "lines"),
            "assessment snapshot"
        )
        require(requireInteger(root, "schemaVersion") == FINANCIAL_RECONCILIATION_ASSESSMENT_SNAPSHOT_SCHEMA_VERSION) {
            "Unsupported embedded assessment snapshot schema version"
        }

        val organizationId = OrganizationId.parse(requireString(root, "organizationId"))
        val traceId = FinancialTraceId.parse(requireString(root, "traceId"))
        val orderId = MarketplaceOrderId.parse(requireString(root, "orderId"))
        val currency = MarketplaceCurrency(requireString(root, "currency"))
        val policyVersion = FinancialReconciliationPolicyVersion(requireString(root, "policyVersion"))
        val status = parseStatus(requireString(root, "status"))

        val linesElement = root["lines"] ?: throw IllegalArgumentException("assessment snapshot lines are required")
        val linesArray = linesElement as? JsonArray
            ?: throw IllegalArgumentException("assessment snapshot lines must be an array")
        require(linesArray.isNotEmpty()) { "assessment snapshot lines must not be empty" }

        val lines = linesArray.map { decodeLine(it, currency) }
        val stages = lines.map { it.stage }
        require(stages == stages.sortedBy(::canonicalStageIndex)) {
            "assessment snapshot lines must use frozen snapshot-v1 stage order"
        }
        require(stages.toSet().size == stages.size) {
            "assessment snapshot stages must be unique"
        }

        return FinancialReconciliationAssessment(
            organizationId = organizationId,
            traceId = traceId,
            orderId = orderId,
            currency = currency,
            policyVersion = policyVersion,
            lines = lines,
            status = status
        )
    }

    private fun decodeLine(element: JsonElement, currency: MarketplaceCurrency): FinancialReconciliationLine {
        val obj = element as? JsonObject
            ?: throw IllegalArgumentException("assessment snapshot line must be an object")
        requireExactKeys(obj, setOf("stage", "status", "expected", "actual", "difference"), "assessment snapshot line")
        return FinancialReconciliationLine(
            stage = parseStage(requireString(obj, "stage")),
            expected = decodeSide(obj["expected"] ?: throw IllegalArgumentException("expected side is required"), currency),
            actual = decodeSide(obj["actual"] ?: throw IllegalArgumentException("actual side is required"), currency),
            difference = decodeDifference(obj["difference"] ?: throw IllegalArgumentException("difference is required"), currency),
            status = parseStatus(requireString(obj, "status"))
        )
    }

    private fun decodeSide(element: JsonElement, expectedCurrency: MarketplaceCurrency): FinancialReconciliationSide {
        val obj = element as? JsonObject
            ?: throw IllegalArgumentException("assessment side must be an object")
        return when (val kind = requireString(obj, "kind")) {
            "NOT_OBSERVED" -> {
                requireExactKeys(obj, setOf("kind"), "NOT_OBSERVED side")
                FinancialReconciliationSide.NotObserved
            }
            "OBSERVED" -> {
                requireExactKeys(obj, setOf("kind", "netAmount", "effectiveEntryIds"), "OBSERVED side")
                val money = decodeMoney(
                    obj["netAmount"] ?: throw IllegalArgumentException("OBSERVED netAmount is required"),
                    expectedCurrency
                )
                val idsArray = (obj["effectiveEntryIds"] ?: throw IllegalArgumentException("effectiveEntryIds is required")) as? JsonArray
                    ?: throw IllegalArgumentException("effectiveEntryIds must be an array")
                require(idsArray.isNotEmpty()) { "effectiveEntryIds must not be empty" }
                val rawIds = idsArray.mapIndexed { index, item ->
                    requireJsonString(item, "effectiveEntryIds[$index]")
                }
                val ids = rawIds.map(FinancialLedgerEntryId::parse)
                require(
                    rawIds == FinancialReconciliationAssessmentCanonicalizerV1.canonicalEntryIdStrings(ids)
                ) {
                    "effectiveEntryIds must use frozen unsigned UUID order"
                }
                require(ids.toSet().size == ids.size) { "effectiveEntryIds must be unique" }
                FinancialReconciliationSide.Observed(money, ids)
            }
            else -> throw IllegalArgumentException("Unsupported reconciliation side kind: $kind")
        }
    }

    private fun decodeDifference(element: JsonElement, expectedCurrency: MarketplaceCurrency): FinancialReconciliationDifference {
        val obj = element as? JsonObject
            ?: throw IllegalArgumentException("assessment difference must be an object")
        return when (val kind = requireString(obj, "kind")) {
            "NOT_COMPARABLE" -> {
                requireExactKeys(obj, setOf("kind"), "NOT_COMPARABLE difference")
                FinancialReconciliationDifference.NotComparable
            }
            "COMPARED" -> {
                requireExactKeys(
                    obj,
                    setOf("kind", "signedDifference", "absoluteDifference", "tolerance"),
                    "COMPARED difference"
                )
                FinancialReconciliationDifference.Compared(
                    signedDifference = decodeMoney(
                        obj["signedDifference"] ?: throw IllegalArgumentException("signedDifference is required"),
                        expectedCurrency
                    ),
                    absoluteDifference = decodeMoney(
                        obj["absoluteDifference"] ?: throw IllegalArgumentException("absoluteDifference is required"),
                        expectedCurrency
                    ),
                    tolerance = decodeMoney(
                        obj["tolerance"] ?: throw IllegalArgumentException("tolerance is required"),
                        expectedCurrency
                    )
                )
            }
            else -> throw IllegalArgumentException("Unsupported reconciliation difference kind: $kind")
        }
    }

    private fun decodeMoney(element: JsonElement, expectedCurrency: MarketplaceCurrency): MarketplaceMoney {
        val obj = element as? JsonObject ?: throw IllegalArgumentException("money must be an object")
        requireExactKeys(obj, setOf("currency", "amount"), "money")
        val currency = MarketplaceCurrency(requireString(obj, "currency"))
        require(currency == expectedCurrency) { "snapshot money currency must match assessment currency" }
        val amount = requireString(obj, "amount")
        val money = MarketplaceMoney.parse(currency, amount)
        require(FinancialReconciliationAssessmentCanonicalizerV1.canonicalMoneyText(money) == amount) {
            "snapshot money amount must use canonical-v1 text"
        }
        return money
    }

    private fun parseObject(payload: String): JsonObject {
        val element = try {
            json.parseToJsonElement(payload)
        } catch (failure: RuntimeException) {
            throw IllegalArgumentException("Malformed assessment snapshot JSON", failure)
        }
        return element as? JsonObject
            ?: throw IllegalArgumentException("assessment snapshot root must be an object")
    }

    private fun requireExactKeys(obj: JsonObject, expected: Set<String>, label: String) {
        require(obj.keys == expected) { "$label contains missing or additional fields" }
    }

    private fun requireInteger(obj: JsonObject, key: String): Int {
        val primitive = obj[key]?.jsonPrimitive ?: throw IllegalArgumentException("$key is required")
        require(!primitive.isString) { "$key must be a JSON integer" }
        return primitive.intOrNull ?: throw IllegalArgumentException("$key must be a JSON integer")
    }

    private fun requireString(obj: JsonObject, key: String): String =
        requireJsonString(obj[key] ?: throw IllegalArgumentException("$key is required"), key)

    private fun requireJsonString(element: JsonElement, label: String): String {
        val primitive = element as? JsonPrimitive
            ?: throw IllegalArgumentException("$label must be a JSON string")
        require(primitive.isString) { "$label must be a JSON string" }
        return primitive.contentOrNull ?: throw IllegalArgumentException("$label must be a JSON string")
    }

    private fun snapshotStageName(
        stage: FinancialLedgerStage
    ): String =
        when (stage) {
            FinancialLedgerStage.SALE -> "SALE"
            FinancialLedgerStage.MARKETPLACE_COMMISSION -> "MARKETPLACE_COMMISSION"
            FinancialLedgerStage.MARKETPLACE_FEE -> "MARKETPLACE_FEE"
            FinancialLedgerStage.SHIPPING -> "SHIPPING"
            FinancialLedgerStage.ADVERTISING -> "ADVERTISING"
            FinancialLedgerStage.TAX -> "TAX"
            FinancialLedgerStage.PRODUCT_COST -> "PRODUCT_COST"
            FinancialLedgerStage.FINANCIAL_COST -> "FINANCIAL_COST"
            FinancialLedgerStage.OTHER_ADJUSTMENT -> "OTHER_ADJUSTMENT"
            FinancialLedgerStage.SETTLEMENT -> "SETTLEMENT"
            FinancialLedgerStage.PAYMENT_ACCOUNT -> "PAYMENT_ACCOUNT"
            FinancialLedgerStage.BANK -> "BANK"
        }

    private fun snapshotStatusName(
        status: FinancialReconciliationStatus
    ): String =
        when (status) {
            FinancialReconciliationStatus.PENDING -> "PENDING"
            FinancialReconciliationStatus.PARTIALLY_RECONCILED ->
                "PARTIALLY_RECONCILED"
            FinancialReconciliationStatus.DIVERGENCE -> "DIVERGENCE"
            FinancialReconciliationStatus.FULLY_RECONCILED ->
                "FULLY_RECONCILED"
        }

    private fun parseStage(value: String): FinancialLedgerStage = when (value) {
        "SALE" -> FinancialLedgerStage.SALE
        "MARKETPLACE_COMMISSION" -> FinancialLedgerStage.MARKETPLACE_COMMISSION
        "MARKETPLACE_FEE" -> FinancialLedgerStage.MARKETPLACE_FEE
        "SHIPPING" -> FinancialLedgerStage.SHIPPING
        "ADVERTISING" -> FinancialLedgerStage.ADVERTISING
        "TAX" -> FinancialLedgerStage.TAX
        "PRODUCT_COST" -> FinancialLedgerStage.PRODUCT_COST
        "FINANCIAL_COST" -> FinancialLedgerStage.FINANCIAL_COST
        "OTHER_ADJUSTMENT" -> FinancialLedgerStage.OTHER_ADJUSTMENT
        "SETTLEMENT" -> FinancialLedgerStage.SETTLEMENT
        "PAYMENT_ACCOUNT" -> FinancialLedgerStage.PAYMENT_ACCOUNT
        "BANK" -> FinancialLedgerStage.BANK
        else -> throw IllegalArgumentException("Unsupported financial ledger stage for snapshot v1: $value")
    }

    private fun parseStatus(value: String): FinancialReconciliationStatus = when (value) {
        "PENDING" -> FinancialReconciliationStatus.PENDING
        "PARTIALLY_RECONCILED" -> FinancialReconciliationStatus.PARTIALLY_RECONCILED
        "DIVERGENCE" -> FinancialReconciliationStatus.DIVERGENCE
        "FULLY_RECONCILED" -> FinancialReconciliationStatus.FULLY_RECONCILED
        else -> throw IllegalArgumentException("Unsupported financial reconciliation status for snapshot v1: $value")
    }

    private fun canonicalStageIndex(stage: FinancialLedgerStage): Int =
        when (stage) {
            FinancialLedgerStage.SALE -> 0
            FinancialLedgerStage.MARKETPLACE_COMMISSION -> 1
            FinancialLedgerStage.MARKETPLACE_FEE -> 2
            FinancialLedgerStage.SHIPPING -> 3
            FinancialLedgerStage.ADVERTISING -> 4
            FinancialLedgerStage.TAX -> 5
            FinancialLedgerStage.PRODUCT_COST -> 6
            FinancialLedgerStage.FINANCIAL_COST -> 7
            FinancialLedgerStage.OTHER_ADJUSTMENT -> 8
            FinancialLedgerStage.SETTLEMENT -> 9
            FinancialLedgerStage.PAYMENT_ACCOUNT -> 10
            FinancialLedgerStage.BANK -> 11
        }
}
