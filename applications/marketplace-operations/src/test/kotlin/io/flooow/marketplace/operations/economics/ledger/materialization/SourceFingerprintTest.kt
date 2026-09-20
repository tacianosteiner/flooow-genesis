package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.organization.OrganizationId
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

class FinancialLedgerMaterializationSourceFingerprintTest {
    @Test
    fun `canonical known answer and digest are stable`() {
        val observation = observation()
        val expected =
            "{\"canonicalizationVersion\":1,\"observationId\":\"00000000-0000-0000-0000-000000000001\"," +
                "\"subject\":{\"organizationId\":\"00000000-0000-0000-0000-000000000003\"," +
                "\"orderId\":\"00000000-0000-0000-0000-000000000004\",\"marketplace\":\"mercado-livre\"," +
                "\"externalOrderId\":\"MLB-123\",\"currency\":\"BRL\"},\"family\":\"MARKETPLACE_ORDER\"," +
                "\"component\":{\"id\":\"00000000-0000-0000-0000-000000000002\",\"type\":\"REVENUE\"," +
                "\"direction\":\"ADDITION\",\"magnitude\":{\"currency\":\"BRL\",\"amount\":\"123.45\"}," +
                "\"source\":{\"kind\":\"MARKETPLACE\",\"systemKey\":\"mercado-livre\"," +
                "\"externalReference\":{\"state\":\"PRESENT\",\"value\":\"order-123\"}}," +
                "\"occurredAt\":\"2026-09-13T10:00:00.123456Z\",\"quality\":\"CONFIRMED\"}," +
                "\"coverageClaim\":\"COMPLETE\",\"observedAt\":\"2026-09-13T10:01:00.654321Z\"}"

        assertEquals(expected, FinancialLedgerMaterializationSourceFingerprintV1.canonicalJson(observation))
        assertEquals(
            "e62c30908543b79a5e24edc9f8539926fe3640632c63b65daaadff5d6fb9b496",
            FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation).sha256
        )
    }

    @Test
    fun `fingerprint binds all governed source meaning`() {
        val base = FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation())
        listOf(
            observation(quality = EconomicEvidenceQuality.ESTIMATED),
            observation(coverage = EconomicComponentCoverage.PARTIAL),
            observation(observedAt = Instant.parse("2026-09-13T10:01:01.654321Z")),
            observation(marketplace = "amazon"),
            observation(externalOrderId = "MLB-124")
        ).forEach {
            assertNotEquals(base, FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(it))
        }
    }

    @Test
    fun `retry is deterministic and json escaping is canonical`() {
        assertEquals(
            FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation()),
            FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation())
        )
        val canonical = FinancialLedgerMaterializationSourceFingerprintV1.canonicalJson(
            observation(externalOrderId = "MLB-\"quoted\"\\path")
        )
        assertTrue(canonical.contains("\"externalOrderId\":\"MLB-\\\"quoted\\\"\\\\path\""))
    }

    @Test
    fun `absent internal source reference uses frozen canonical literal`() {
        val original = observation()
        val internal = original.copy(
            component = original.component.copy(
                source = EconomicSource(
                    EconomicSourceKind.CALCULATED,
                    EconomicSourceSystemKey("internal"),
                    EconomicExternalReferenceState.Absent(
                        EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN
                    )
                )
            )
        )
        val canonical = FinancialLedgerMaterializationSourceFingerprintV1.canonicalJson(internal)
        assertTrue(canonical.contains("\"externalReference\":{\"state\":\"ABSENT\",\"reason\":\"INTERNAL_ORIGIN\"}"))
        assertNotEquals(
            FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(original),
            FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(internal)
        )
    }

    private fun observation(
        quality: EconomicEvidenceQuality = EconomicEvidenceQuality.CONFIRMED,
        coverage: EconomicComponentCoverage = EconomicComponentCoverage.COMPLETE,
        observedAt: Instant = Instant.parse("2026-09-13T10:01:00.654321Z"),
        marketplace: String = "mercado-livre",
        externalOrderId: String = "MLB-123"
    ): MarketplaceEconomicComponentObservation {
        val organizationId = OrganizationId.parse("00000000-0000-0000-0000-000000000003")
        val orderId = MarketplaceOrderId.parse("00000000-0000-0000-0000-000000000004")
        val currency = MarketplaceCurrency("BRL")
        val subject = MarketplaceEconomicEvidenceSubject(
            organizationId, orderId, MarketplaceKey(marketplace), MarketplaceExternalOrderId(externalOrderId), currency
        )
        val component = EconomicComponent(
            organizationId = organizationId,
            id = EconomicComponentId.parse("00000000-0000-0000-0000-000000000002"),
            orderId = orderId,
            type = EconomicComponentType.REVENUE,
            direction = EconomicDirection.ADDITION,
            magnitude = MarketplaceMoney.parse(currency, "123.45"),
            source = EconomicSource(
                EconomicSourceKind.MARKETPLACE,
                EconomicSourceSystemKey("mercado-livre"),
                EconomicExternalReferenceState.Present(EconomicExternalReference("order-123"))
            ),
            occurredAt = Instant.parse("2026-09-13T10:00:00.123456Z"),
            quality = quality
        )
        return MarketplaceEconomicComponentObservation(
            MarketplaceEconomicEvidenceObservationId.parse("00000000-0000-0000-0000-000000000001"),
            subject, MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER, component, coverage, observedAt
        )
    }
}
