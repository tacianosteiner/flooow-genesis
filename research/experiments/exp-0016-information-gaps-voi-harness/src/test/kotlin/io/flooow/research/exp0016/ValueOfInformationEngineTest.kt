package io.flooow.research.exp0016

import java.math.BigDecimal
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ValueOfInformationEngineTest {
    private val engine = ValueOfInformationEngine()
    private val now = Instant.parse("2026-09-07T12:00:00Z")

    @Test
    fun `positive conservative net value recommends information acquisition`() {
        val result =
            engine.assess(
                gap = gap(),
                method =
                    method(
                        acquisition = "20.00",
                        delay = "5.00",
                        reserve = "10.00",
                    ),
                impact = impact(floor = "100.00", ceiling = "250.00"),
            )

        assertEquals(InformationAcquisitionDecision.ACQUIRE_INFORMATION, result.decision)
        assertEquals(BigDecimal("65.00"), result.conservativeNetValue!!.amount)
        assertTrue(InformationReasonCode.POSITIVE_VALUE_OF_INFORMATION in result.reasonCodes)
        assertFalse(result.canonicalTruth)
        assertFalse(result.executable)
    }

    @Test
    fun `negative conservative net value blocks information acquisition`() {
        val result =
            engine.assess(
                gap = gap(),
                method =
                    method(
                        acquisition = "50.00",
                        delay = "25.00",
                        reserve = "10.00",
                    ),
                impact = impact(floor = "60.00", ceiling = "200.00"),
            )

        assertEquals(InformationAcquisitionDecision.DO_NOT_ACQUIRE, result.decision)
        assertEquals(BigDecimal("-25.00"), result.conservativeNetValue!!.amount)
    }

    @Test
    fun `missing impact estimate defers instead of guessing`() {
        val result =
            engine.assess(
                gap = gap(),
                method = method(),
                impact = null,
            )

        assertEquals(InformationAcquisitionDecision.DEFER, result.decision)
        assertNull(result.conservativeNetValue)
        assertTrue(InformationReasonCode.INSUFFICIENT_IMPACT_BASIS in result.reasonCodes)
    }

    @Test
    fun `empty gap reasons are insufficient basis`() {
        val result =
            engine.assess(
                gap = gap(reasons = emptySet()),
                method = method(),
                impact = impact("100.00", "150.00"),
            )

        assertEquals(InformationAcquisitionDecision.INSUFFICIENT_BASIS, result.decision)
        assertTrue(InformationReasonCode.GAP_NOT_ACTIONABLE in result.reasonCodes)
    }

    @Test
    fun `acquisition method must declare evidence requirements`() {
        val result =
            engine.assess(
                gap = gap(),
                method =
                    method(
                        requiredEvidenceKinds = emptySet(),
                    ),
                impact = impact("100.00", "150.00"),
            )

        assertEquals(InformationAcquisitionDecision.INSUFFICIENT_BASIS, result.decision)
        assertTrue(InformationReasonCode.NO_REQUIRED_EVIDENCE_DECLARED in result.reasonCodes)
    }

    @Test
    fun `method that misses decision deadline is rejected`() {
        val result =
            engine.assess(
                gap =
                    gap(
                        deadline = now.plusSeconds(3600),
                    ),
                method =
                    method(
                        earliestAvailableAt = now.plusSeconds(7200),
                    ),
                impact = impact("1000.00", "1500.00"),
            )

        assertEquals(InformationAcquisitionDecision.DO_NOT_ACQUIRE, result.decision)
        assertTrue(InformationReasonCode.DEADLINE_MISSED in result.reasonCodes)
        assertNull(result.conservativeNetValue)
    }

    @Test
    fun `unresolved contradiction is an explicit information gap reason`() {
        val result =
            engine.assess(
                gap =
                    gap(
                        reasons = setOf(GapReason.UNRESOLVED_CONTRADICTION),
                    ),
                method = method(),
                impact = impact("100.00", "150.00"),
            )

        assertEquals(InformationAcquisitionDecision.ACQUIRE_INFORMATION, result.decision)
    }

    @Test
    fun `missing evidence is not treated as zero value`() {
        val result =
            engine.assess(
                gap =
                    gap(
                        reasons = setOf(GapReason.MISSING_EVIDENCE),
                    ),
                method = method(),
                impact = null,
            )

        assertEquals(InformationAcquisitionDecision.DEFER, result.decision)
        assertNull(result.conservativeNetValue)
    }

    private fun gap(
        reasons: Set<GapReason> = setOf(GapReason.UNKNOWN_CAUSAL_EFFECT),
        deadline: Instant? = now.plusSeconds(86_400),
    ): InformationGap =
        InformationGap(
            gapId = "gap-1",
            organizationId = "org-1",
            subjectId = "campaign-1",
            decisionContext = "ads-budget-allocation",
            unknownVariable = "incremental_margin_effect",
            confidenceBand = ConfidenceBand.LOW,
            reasons = reasons,
            deadline = deadline,
        )

    private fun method(
        acquisition: String = "20.00",
        delay: String = "5.00",
        reserve: String = "10.00",
        requiredEvidenceKinds: Set<String> = setOf("incremental-outcome-measurement"),
        earliestAvailableAt: Instant = now.plusSeconds(1800),
    ): AcquisitionMethod =
        AcquisitionMethod(
            methodId = "method-1",
            kind = AcquisitionMethodKind.CONTROLLED_EXPERIMENT,
            requiredEvidenceKinds = requiredEvidenceKinds,
            acquisitionCost = money(acquisition),
            delayCost = money(delay),
            executionRiskReserve = money(reserve),
            earliestAvailableAt = earliestAvailableAt,
        )

    private fun impact(
        floor: String,
        ceiling: String,
    ): DecisionImpactEstimate =
        DecisionImpactEstimate(
            expectedImprovementFloor = money(floor),
            expectedImprovementCeiling = money(ceiling),
        )

    private fun money(value: String): Money =
        Money(
            amount = BigDecimal(value),
            currency = "BRL",
        )
}
