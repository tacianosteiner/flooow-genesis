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
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class FinancialReconciliationAssessmentSnapshotTest {
    private val brl = MarketplaceCurrency("BRL")

    @Test
    fun `snapshot round trip preserves exact semantic assessment and fingerprint`() {
        val assessment = assessment()
        val snapshot = FinancialReconciliationAssessmentSnapshot.capture(assessment)
        val parsed = FinancialReconciliationAssessmentSnapshot.parse(1, snapshot.json)
        val verified = FinancialReconciliationAssessmentSnapshotCodec.verify(
            parsed,
            FinancialReconciliationAssessmentFingerprinter.fingerprint(assessment)
        )

        assertEquals(1, snapshot.schemaVersion)
        assertEquals(assessment, verified.assessment)
        assertEquals(
            FinancialReconciliationAssessmentFingerprinter.fingerprint(assessment),
            verified.fingerprint
        )
    }

    @Test
    fun `snapshot has exact top level contract and embedded schema version`() {
        val root = Json.parseToJsonElement(
            FinancialReconciliationAssessmentSnapshot.capture(assessment()).json
        ) as JsonObject
        assertEquals(
            setOf("schemaVersion", "organizationId", "traceId", "orderId", "currency", "policyVersion", "status", "lines"),
            root.keys
        )
        assertEquals(JsonPrimitive(1), root["schemaVersion"])
        assertTrue(root["lines"] is JsonArray)
    }

    @Test
    fun `snapshot v1 emits frozen stage and status literals`() {
        val root =
            Json.parseToJsonElement(
                FinancialReconciliationAssessmentSnapshot
                    .capture(assessment())
                    .json
            ) as JsonObject

        assertEquals(
            JsonPrimitive("DIVERGENCE"),
            root["status"]
        )

        val lines =
            root.getValue("lines") as JsonArray

        val sale =
            lines[0] as JsonObject

        val tax =
            lines[1] as JsonObject

        assertEquals(
            JsonPrimitive("SALE"),
            sale["stage"]
        )
        assertEquals(
            JsonPrimitive("DIVERGENCE"),
            sale["status"]
        )
        assertEquals(
            JsonPrimitive("TAX"),
            tax["stage"]
        )
        assertEquals(
            JsonPrimitive("PENDING"),
            tax["status"]
        )
    }

    @Test
    fun `json property order and insignificant whitespace are not snapshot identity`() {
        val assessment = assessment()
        val canonical = FinancialReconciliationAssessmentSnapshot.capture(assessment)
        val root = Json.parseToJsonElement(canonical.json) as JsonObject

        val reordered = JsonObject(
            linkedMapOf(
                "lines" to root.getValue("lines"),
                "status" to root.getValue("status"),
                "policyVersion" to root.getValue("policyVersion"),
                "currency" to root.getValue("currency"),
                "orderId" to root.getValue("orderId"),
                "traceId" to root.getValue("traceId"),
                "organizationId" to root.getValue("organizationId"),
                "schemaVersion" to root.getValue("schemaVersion")
            )
        )

        val nonCanonicalTransportJson =
            "\n  " + reordered.toString() + "  \n"

        val parsed = FinancialReconciliationAssessmentSnapshot.parse(
            1,
            nonCanonicalTransportJson
        )

        assertEquals(canonical, parsed)

        val verified = FinancialReconciliationAssessmentSnapshotCodec.verify(
            parsed,
            FinancialReconciliationAssessmentFingerprinter.fingerprint(assessment)
        )

        assertEquals(assessment, verified.assessment)
    }

    @Test
    fun `persisted and embedded snapshot versions must agree`() {
        val snapshot = FinancialReconciliationAssessmentSnapshot.capture(assessment())
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentSnapshot.parse(2, snapshot.json)
        }
        val tampered = snapshot.json.replace("\"schemaVersion\":1", "\"schemaVersion\":2")
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentSnapshot.parse(1, tampered)
        }
    }

    @Test
    fun `additional top level or nested fields fail closed`() {
        val snapshot = FinancialReconciliationAssessmentSnapshot.capture(assessment())
        val root = Json.parseToJsonElement(snapshot.json) as JsonObject
        val topTampered = JsonObject(root + ("extra" to JsonPrimitive("x"))).toString()
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentSnapshot.parse(1, topTampered)
        }

        val lines = root.getValue("lines") as JsonArray
        val first = lines.first() as JsonObject
        val nestedRoot = JsonObject(
            root + ("lines" to JsonArray(listOf(JsonObject(first + ("extra" to JsonPrimitive("x")))) + lines.drop(1)))
        ).toString()
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentSnapshot.parse(1, nestedRoot)
        }
    }

    @Test
    fun `non canonical money text fails closed`() {
        val snapshot = FinancialReconciliationAssessmentSnapshot.capture(assessment())
        val tampered = snapshot.json.replace("\"amount\":\"100\"", "\"amount\":\"100.0\"")
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentSnapshot.parse(1, tampered)
        }
    }

    @Test
    fun `entry ids outside frozen unsigned order fail closed`() {
        val snapshot = FinancialReconciliationAssessmentSnapshot.capture(assessment())
        val canonical = "\"effectiveEntryIds\":[\"7fffffff-ffff-ffff-ffff-ffffffffffff\",\"80000000-0000-0000-0000-000000000000\"]"
        val reversed = "\"effectiveEntryIds\":[\"80000000-0000-0000-0000-000000000000\",\"7fffffff-ffff-ffff-ffff-ffffffffffff\"]"
        assertTrue(canonical in snapshot.json)
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentSnapshot.parse(1, snapshot.json.replace(canonical, reversed))
        }
    }

    @Test
    fun `line arrays outside frozen stage order fail closed`() {
        val snapshot = FinancialReconciliationAssessmentSnapshot.capture(assessment())
        val root = Json.parseToJsonElement(snapshot.json) as JsonObject
        val lines = root.getValue("lines") as JsonArray
        val tampered = JsonObject(root + ("lines" to JsonArray(lines.reversed()))).toString()
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentSnapshot.parse(1, tampered)
        }
    }

    @Test
    fun `tampered snapshot cannot verify against accepted fingerprint`() {
        val original = assessment()
        val tampered = FinancialReconciliationAssessmentSnapshot.capture(
            assessment(saleActual = "111.5", signedDifference = "11.5")
        )
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentSnapshotCodec.verify(
                tampered,
                FinancialReconciliationAssessmentFingerprinter.fingerprint(original)
            )
        }
    }

    private fun assessment(
        saleActual: String = "110.5",
        signedDifference: String = "10.5"
    ): FinancialReconciliationAssessment {
        val sale = FinancialReconciliationLine(
            stage = FinancialLedgerStage.SALE,
            expected = FinancialReconciliationSide.Observed(
                netAmount = money("100"),
                effectiveEntryIds = listOf(
                    FinancialLedgerEntryId.parse("80000000-0000-0000-0000-000000000000"),
                    FinancialLedgerEntryId.parse("7fffffff-ffff-ffff-ffff-ffffffffffff")
                )
            ),
            actual = FinancialReconciliationSide.Observed(
                netAmount = money(saleActual),
                effectiveEntryIds = listOf(
                    FinancialLedgerEntryId.parse("00000000-0000-0000-0000-000000000003")
                )
            ),
            difference = FinancialReconciliationDifference.Compared(
                signedDifference = money(signedDifference),
                absoluteDifference = money(signedDifference),
                tolerance = money("0.01")
            ),
            status = FinancialReconciliationStatus.DIVERGENCE
        )
        val tax = FinancialReconciliationLine(
            stage = FinancialLedgerStage.TAX,
            expected = FinancialReconciliationSide.Observed(
                netAmount = money("5"),
                effectiveEntryIds = listOf(
                    FinancialLedgerEntryId.parse("00000000-0000-0000-0000-000000000004")
                )
            ),
            actual = FinancialReconciliationSide.NotObserved,
            difference = FinancialReconciliationDifference.NotComparable,
            status = FinancialReconciliationStatus.PENDING
        )
        return FinancialReconciliationAssessment(
            organizationId = OrganizationId.parse("10000000-0000-0000-0000-000000000001"),
            traceId = FinancialTraceId.parse("20000000-0000-0000-0000-000000000001"),
            orderId = MarketplaceOrderId.parse("30000000-0000-0000-0000-000000000001"),
            currency = brl,
            policyVersion = FinancialReconciliationPolicyVersion("financial/1"),
            lines = listOf(tax, sale),
            status = FinancialReconciliationStatus.DIVERGENCE
        )
    }

    private fun money(value: String): MarketplaceMoney = MarketplaceMoney.parse(brl, value)
}
