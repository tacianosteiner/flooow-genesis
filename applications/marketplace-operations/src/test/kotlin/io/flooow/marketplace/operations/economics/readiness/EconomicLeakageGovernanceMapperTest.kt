package io.flooow.marketplace.operations.economics.readiness

import io.flooow.marketplace.operations.economics.reconciliation.EconomicLeakageGovernanceBlockingReason
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class EconomicLeakageGovernanceMapperTest {
    @Test
    fun `canonical authority permits economic leakage interpretation`() {
        val result = EconomicLeakageGovernanceMapper.from(
            assessment(
                identity = EconomicTruthAuthorityState.CANONICAL,
                currency = EconomicTruthAuthorityState.CANONICAL,
                allocation = EconomicTruthAuthorityState.RECONCILED,
                currentness = EconomicTruthAuthorityState.CANONICAL
            )
        )

        assertTrue(result.permitted)
        assertTrue(result.blockingReasons.isEmpty())
        assertEquals(
            setOf(
                "identity:test",
                "currency:test",
                "allocation:test",
                "currentness:test",
                "reconciliation:test"
            ),
            result.evidenceReferences
        )
    }

    @Test
    fun `unresolved identity blocks leakage interpretation`() {
        val result = EconomicLeakageGovernanceMapper.from(
            assessment(identity = EconomicTruthAuthorityState.UNRESOLVED)
        )

        assertFalse(result.permitted)
        assertTrue(
            EconomicLeakageGovernanceBlockingReason.IDENTITY_UNRESOLVED in
                result.blockingReasons
        )
    }

    @Test
    fun `unresolved currency blocks leakage interpretation`() {
        val result = EconomicLeakageGovernanceMapper.from(
            assessment(currency = EconomicTruthAuthorityState.UNRESOLVED)
        )

        assertFalse(result.permitted)
        assertTrue(
            EconomicLeakageGovernanceBlockingReason.CURRENCY_UNRESOLVED in
                result.blockingReasons
        )
    }

    @Test
    fun `unresolved allocation blocks leakage interpretation`() {
        val result = EconomicLeakageGovernanceMapper.from(
            assessment(allocation = EconomicTruthAuthorityState.UNRESOLVED)
        )

        assertFalse(result.permitted)
        assertTrue(
            EconomicLeakageGovernanceBlockingReason.ALLOCATION_UNRESOLVED in
                result.blockingReasons
        )
    }

    @Test
    fun `unresolved currentness blocks leakage interpretation`() {
        val result = EconomicLeakageGovernanceMapper.from(
            assessment(currentness = EconomicTruthAuthorityState.UNRESOLVED)
        )

        assertFalse(result.permitted)
        assertTrue(
            EconomicLeakageGovernanceBlockingReason.EVIDENCE_CURRENTNESS_UNRESOLVED in
                result.blockingReasons
        )
    }

    @Test
    fun `contradictory authority fails closed`() {
        val result = EconomicLeakageGovernanceMapper.from(
            assessment(identity = EconomicTruthAuthorityState.CONTRADICTORY)
        )

        assertFalse(result.permitted)
        assertTrue(
            EconomicLeakageGovernanceBlockingReason.CONTRADICTORY_AUTHORITY in
                result.blockingReasons
        )
    }

    @Test
    fun `stale authority fails closed`() {
        val result = EconomicLeakageGovernanceMapper.from(
            assessment(currentness = EconomicTruthAuthorityState.STALE)
        )

        assertFalse(result.permitted)
        assertTrue(
            EconomicLeakageGovernanceBlockingReason.STALE_AUTHORITY in
                result.blockingReasons
        )
    }

    private fun assessment(
        identity: EconomicTruthAuthorityState = EconomicTruthAuthorityState.CANONICAL,
        currency: EconomicTruthAuthorityState = EconomicTruthAuthorityState.CANONICAL,
        allocation: EconomicTruthAuthorityState = EconomicTruthAuthorityState.CANONICAL,
        currentness: EconomicTruthAuthorityState = EconomicTruthAuthorityState.CANONICAL
    ): EconomicTruthAuthorityAssessment =
        EconomicTruthAuthorityAssessment(
            identity = EconomicTruthAuthorityEvidence(
                identity,
                setOf("identity:test")
            ),
            currency = EconomicTruthAuthorityEvidence(
                currency,
                setOf("currency:test")
            ),
            allocation = EconomicTruthAuthorityEvidence(
                allocation,
                setOf("allocation:test")
            ),
            currentness = EconomicTruthAuthorityEvidence(
                currentness,
                setOf("currentness:test")
            ),
            reconciliation = null,
            reconciliationEvidenceReferences = setOf("reconciliation:test")
        )
}