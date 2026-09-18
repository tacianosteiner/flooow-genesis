package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.organization.OrganizationId
import java.nio.charset.StandardCharsets
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

class FinancialReconciliationAssessmentFingerprintTest {
    private val brl = MarketplaceCurrency("BRL")

    @Test
    fun `known answer canonical bytes and fingerprint are stable`() {
        val assessment = knownAssessment()

        val canonicalJson = FinancialReconciliationAssessmentCanonicalizerV1
            .canonicalJson(assessment)

        assertEquals(KNOWN_CANONICAL_JSON, canonicalJson)
        assertEquals(
            KNOWN_CANONICAL_JSON,
            String(
                FinancialReconciliationAssessmentCanonicalizerV1.canonicalBytes(assessment),
                StandardCharsets.UTF_8
            )
        )

        val fingerprint = FinancialReconciliationAssessmentFingerprinter.fingerprint(assessment)

        assertEquals(1, fingerprint.canonicalizationVersion)
        assertEquals(KNOWN_SHA256, fingerprint.sha256)
        assertEquals(64, fingerprint.sha256.length)
        assertTrue(fingerprint.sha256.all { it in '0'..'9' || it in 'a'..'f' })
        assertEquals("[REDACTED]", fingerprint.toString())
    }

    @Test
    fun `acceptance computes governed fingerprint internally`() {
        val assessment = knownAssessment()
        val accepted = AcceptedFinancialReconciliationAssessment.accept(
            assessment,
            Instant.parse("2026-09-13T16:00:00.123456Z")
        )

        assertEquals(assessment, accepted.assessment)
        assertEquals(
            FinancialReconciliationAssessmentFingerprinter.fingerprint(assessment),
            accepted.assessmentFingerprint
        )
        assertEquals(
            Instant.parse("2026-09-13T16:00:00.123456Z"),
            accepted.acceptedAt
        )
    }

    @Test
    fun `acceptance occurrence time is excluded from assessment identity`() {
        val assessment = knownAssessment()
        val first = AcceptedFinancialReconciliationAssessment.accept(
            assessment,
            Instant.parse("2026-09-13T16:00:00.000001Z")
        )
        val second = AcceptedFinancialReconciliationAssessment.accept(
            assessment,
            Instant.parse("2026-09-13T16:00:01.999999Z")
        )

        assertEquals(first.assessmentFingerprint, second.assessmentFingerprint)
        assertNotEquals(first.acceptedAt, second.acceptedAt)
    }

    @Test
    fun `acceptance retains microsecond precision gate`() {
        assertFailsWith<IllegalArgumentException> {
            AcceptedFinancialReconciliationAssessment.accept(
                knownAssessment(),
                Instant.parse("2026-09-13T16:00:00.123456789Z")
            )
        }
    }

    @Test
    fun `same complete assessment is deterministic and input line order is irrelevant`() {
        val first = knownAssessment(reverseInputLines = false)
        val second = knownAssessment(reverseInputLines = true)

        assertEquals(
            FinancialReconciliationAssessmentFingerprinter.fingerprint(first),
            FinancialReconciliationAssessmentFingerprinter.fingerprint(second)
        )
        assertEquals(
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalJson(first),
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalJson(second)
        )
    }

    @Test
    fun `changed non divergent content changes fingerprint even when divergence remains`() {
        val original = knownAssessment(taxExpected = "5.000000")
        val changed = knownAssessment(taxExpected = "6.000000")

        assertEquals(FinancialReconciliationStatus.DIVERGENCE, original.status)
        assertEquals(FinancialReconciliationStatus.DIVERGENCE, changed.status)
        assertNotEquals(
            FinancialReconciliationAssessmentFingerprinter.fingerprint(original),
            FinancialReconciliationAssessmentFingerprinter.fingerprint(changed)
        )
    }

    @Test
    fun `changed divergent content changes fingerprint`() {
        val original = knownAssessment(
            saleActual = "110.500000",
            saleSignedDifference = "10.500000"
        )
        val changed = knownAssessment(
            saleActual = "111.500000",
            saleSignedDifference = "11.500000"
        )

        assertNotEquals(
            FinancialReconciliationAssessmentFingerprinter.fingerprint(original),
            FinancialReconciliationAssessmentFingerprinter.fingerprint(changed)
        )
    }

    @Test
    fun `v1 stage order is frozen by names and not runtime ordinal`() {
        assertEquals(
            listOf(
                "SALE",
                "MARKETPLACE_COMMISSION",
                "MARKETPLACE_FEE",
                "SHIPPING",
                "ADVERTISING",
                "TAX",
                "PRODUCT_COST",
                "FINANCIAL_COST",
                "OTHER_ADJUSTMENT",
                "SETTLEMENT",
                "PAYMENT_ACCOUNT",
                "BANK"
            ),
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalStageNames()
        )
    }

    @Test
    fun `entry ids use frozen unsigned uuid order including high bit`() {
        val high = FinancialLedgerEntryId.parse("80000000-0000-0000-0000-000000000000")
        val low = FinancialLedgerEntryId.parse("7fffffff-ffff-ffff-ffff-ffffffffffff")

        assertEquals(
            listOf(
                "7fffffff-ffff-ffff-ffff-ffffffffffff",
                "80000000-0000-0000-0000-000000000000"
            ),
            FinancialReconciliationAssessmentCanonicalizerV1
                .canonicalEntryIdStrings(listOf(high, low))
        )
    }

    @Test
    fun `canonical money text normalizes zero trailing zeros negatives and exponent candidates`() {
        assertEquals(
            "0",
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalMoneyText(money("0.000000"))
        )
        assertEquals(
            "10.5",
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalMoneyText(money("10.500000"))
        )
        assertEquals(
            "-0.5",
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalMoneyText(money("-0.500000"))
        )
        assertEquals(
            "100000000000000000",
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalMoneyText(
                money("100000000000000000.000000")
            )
        )
    }

    @Test
    fun `canonical json escaping is fixed and rejects unpaired surrogates`() {
        val unicodeTail = String(
            charArrayOf(
                '\u00E9',
                '\uD83D',
                '\uDE00'
            )
        )
        val input = String(
            charArrayOf(
                '\u0000',
                '\b',
                '\u000C',
                '\n',
                '\r',
                '\t',
                '"',
                '\\',
                '\u00E9',
                '\uD83D',
                '\uDE00'
            )
        )

        assertEquals(
            "\"\\u0000\\b\\f\\n\\r\\t\\\"\\\\" + unicodeTail + "\"",
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalJsonString(input)
        )

        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalJsonString(
                String(charArrayOf('\uD800'))
            )
        }
        assertFailsWith<IllegalArgumentException> {
            FinancialReconciliationAssessmentCanonicalizerV1.canonicalJsonString(
                String(charArrayOf('\uDC00'))
            )
        }
    }

    @Test
    fun `canonical output is compact utf8 json without bom or trailing newline`() {
        val bytes = FinancialReconciliationAssessmentCanonicalizerV1
            .canonicalBytes(knownAssessment())
        val text = String(bytes, StandardCharsets.UTF_8)

        assertTrue(bytes.size >= 3)
        assertTrue(
            !(bytes[0] == 0xEF.toByte() &&
                bytes[1] == 0xBB.toByte() &&
                bytes[2] == 0xBF.toByte())
        )
        assertTrue(!text.endsWith("\n"))
        assertTrue(!text.contains(": "))
        assertTrue(!text.contains(", "))
    }

    private fun knownAssessment(
        reverseInputLines: Boolean = false,
        taxExpected: String = "5.000000",
        saleActual: String = "110.500000",
        saleSignedDifference: String = "10.500000"
    ): FinancialReconciliationAssessment {
        val sale = FinancialReconciliationLine(
            stage = FinancialLedgerStage.SALE,
            expected = observed(
                "100.000000",
                "80000000-0000-0000-0000-000000000000",
                "7fffffff-ffff-ffff-ffff-ffffffffffff"
            ),
            actual = observed(
                saleActual,
                "00000000-0000-0000-0000-000000000003"
            ),
            difference = FinancialReconciliationDifference.Compared(
                signedDifference = money(saleSignedDifference),
                absoluteDifference = money(saleSignedDifference),
                tolerance = money("0.010000")
            ),
            status = FinancialReconciliationStatus.DIVERGENCE
        )
        val tax = FinancialReconciliationLine(
            stage = FinancialLedgerStage.TAX,
            expected = observed(
                taxExpected,
                "00000000-0000-0000-0000-000000000004"
            ),
            actual = FinancialReconciliationSide.NotObserved,
            difference = FinancialReconciliationDifference.NotComparable,
            status = FinancialReconciliationStatus.PENDING
        )
        val lines = if (reverseInputLines) listOf(sale, tax) else listOf(tax, sale)

        return FinancialReconciliationAssessment(
            organizationId = OrganizationId.parse("10000000-0000-0000-0000-000000000001"),
            traceId = FinancialTraceId.parse("20000000-0000-0000-0000-000000000001"),
            orderId = MarketplaceOrderId.parse("30000000-0000-0000-0000-000000000001"),
            currency = brl,
            policyVersion = FinancialReconciliationPolicyVersion("financial/1"),
            lines = lines,
            status = FinancialReconciliationStatus.DIVERGENCE
        )
    }

    private fun observed(
        amount: String,
        vararg ids: String
    ): FinancialReconciliationSide.Observed =
        FinancialReconciliationSide.Observed(
            netAmount = money(amount),
            effectiveEntryIds = ids.map { FinancialLedgerEntryId.parse(it) }
        )

    private fun money(value: String): MarketplaceMoney = MarketplaceMoney.parse(brl, value)

    companion object {
        private const val KNOWN_SHA256 =
            "99c2c6a1b523c1ec9ef63dfb0d5bf7072c18e95c7b77ed9277d5c7460c3cc513"

        private const val KNOWN_CANONICAL_JSON =
            "{\"canonicalizationVersion\":1,\"organizationId\":\"10000000-0000-0000-0000-000000000001\",\"traceId\":\"20000000-0000-0000-0000-000000000001\",\"orderId\":\"30000000-0000-0000-0000-000000000001\",\"currency\":\"BRL\",\"policyVersion\":\"financial/1\",\"status\":\"DIVERGENCE\",\"lines\":[{\"stage\":\"SALE\",\"status\":\"DIVERGENCE\",\"expected\":{\"kind\":\"OBSERVED\",\"netAmount\":{\"currency\":\"BRL\",\"amount\":\"100\"},\"effectiveEntryIds\":[\"7fffffff-ffff-ffff-ffff-ffffffffffff\",\"80000000-0000-0000-0000-000000000000\"]},\"actual\":{\"kind\":\"OBSERVED\",\"netAmount\":{\"currency\":\"BRL\",\"amount\":\"110.5\"},\"effectiveEntryIds\":[\"00000000-0000-0000-0000-000000000003\"]},\"difference\":{\"kind\":\"COMPARED\",\"signedDifference\":{\"currency\":\"BRL\",\"amount\":\"10.5\"},\"absoluteDifference\":{\"currency\":\"BRL\",\"amount\":\"10.5\"},\"tolerance\":{\"currency\":\"BRL\",\"amount\":\"0.01\"}}},{\"stage\":\"TAX\",\"status\":\"PENDING\",\"expected\":{\"kind\":\"OBSERVED\",\"netAmount\":{\"currency\":\"BRL\",\"amount\":\"5\"},\"effectiveEntryIds\":[\"00000000-0000-0000-0000-000000000004\"]},\"actual\":{\"kind\":\"NOT_OBSERVED\"},\"difference\":{\"kind\":\"NOT_COMPARABLE\"}}]}"
    }
}
