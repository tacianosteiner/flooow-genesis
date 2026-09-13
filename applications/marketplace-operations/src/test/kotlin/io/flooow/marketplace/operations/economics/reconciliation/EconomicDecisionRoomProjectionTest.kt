package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.ledger.*
import io.flooow.marketplace.operations.economics.readiness.*
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.UUID
import kotlin.test.*

class EconomicDecisionRoomProjectionTest {
    @Test fun `missing authority is explicitly not assembled and blocked`() {
        val projection = project(authority = EconomicDecisionRoomAuthorityRead.Unavailable)
        assertEquals(EconomicDecisionRoomProjectionStatus.BLOCKED, projection.projectionStatus)
        assertEquals(EconomicDecisionRoomAuthorityStatus.NOT_ASSEMBLED, projection.authorityStatus)
        assertTrue(EconomicDecisionRoomProjectionBlockingReason.AUTHORITY_NOT_ASSEMBLED in projection.projectionBlockingReasons)
        assertEquals(4, projection.authorityBlockingReasons.size)
        assertEquals(EconomicDecisionRoomStageBlockingReason.AUTHORITY_NOT_ASSEMBLED, projection.stages.single().blockingReason)
        assertNull(projection.totalQuantifiedLeakage)
    }

    @Test fun `missing canonical assessment preserves variance but never calls it leakage`() {
        val projection = project(assessment = EconomicDecisionRoomReconciliationAssessmentRead.Unavailable)
        assertEquals(EconomicDecisionRoomProjectionStatus.BLOCKED, projection.projectionStatus)
        assertNull(projection.totalQuantifiedLeakage)
        assertEquals(MarketplaceMoney.parse(currency, "-10"), projection.stages.single().signedVariance)
        assertNull(projection.stages.single().interpretation)
        assertEquals(EconomicDecisionRoomStageBlockingReason.RECONCILIATION_ASSESSMENT_UNAVAILABLE, projection.stages.single().blockingReason)
        assertTrue(projection.evidenceReferences.any { it.startsWith("reconciliation-case:") })
        assertTrue(projection.evidenceReferences.any { it.startsWith("financial-ledger-entry:") })
    }

    @Test fun `unresolved authority makes leakage unquantified`() = assertGovernanceBlocked(EconomicTruthAuthorityState.UNRESOLVED)
    @Test fun `contradictory authority makes leakage unquantified`() = assertGovernanceBlocked(EconomicTruthAuthorityState.CONTRADICTORY)
    @Test fun `stale authority makes leakage unquantified`() = assertGovernanceBlocked(EconomicTruthAuthorityState.STALE)

    @Test fun `fully governed negative variance is unfavorable leakage`() {
        val projection = project()
        assertEquals(EconomicDecisionRoomProjectionStatus.READY, projection.projectionStatus)
        assertEquals(EconomicLeakageInterpretationStatus.UNFAVORABLE_LEAKAGE, projection.stages.single().interpretation)
        assertEquals(MarketplaceMoney.parse(currency, "10"), projection.totalQuantifiedLeakage)
    }

    @Test fun `fully governed positive variance is favorable and not quantified leakage`() {
        val assessment = assessment(expected = "100", actual = "110")
        val projection = project(case = durable(assessment), assessment = bound(assessment))
        assertEquals(EconomicLeakageInterpretationStatus.FAVORABLE_VARIANCE, projection.stages.single().interpretation)
        assertNull(projection.stages.single().quantifiedLeakage)
        assertEquals(MarketplaceMoney.parse(currency, "0"), projection.totalQuantifiedLeakage)
    }

    @Test fun `missing expected is unquantified and not zero`() {
        val assessment = assessment(expected = null, actual = "90")
        val projection = project(case = durable(assessment), assessment = bound(assessment))
        assertEquals(EconomicLeakageInterpretationStatus.UNQUANTIFIED, projection.stages.single().interpretation)
        assertEquals(EconomicDecisionRoomStageBlockingReason.MISSING_EXPECTED, projection.stages.single().blockingReason)
        assertNull(projection.totalQuantifiedLeakage)
    }

    @Test fun `missing actual is unquantified and not zero`() {
        val lines = listOf(
            assessment().lines.single(),
            assessment(expected = "-20", actual = null, stage = FinancialLedgerStage.SHIPPING).lines.single()
        )
        val assessment = FinancialReconciliationAssessment(
            organization, traceId, orderId, currency, policy, lines,
            FinancialReconciliationStatus.DIVERGENCE
        )
        val projection = project(
            case = durable(assessment),
            assessment = bound(assessment)
        )
        val shipping = projection.stages.single { it.stage == FinancialLedgerStage.SHIPPING }
        assertEquals(EconomicDecisionRoomProjectionStatus.BLOCKED, projection.projectionStatus)
        assertEquals(EconomicDecisionRoomStageBlockingReason.MISSING_ACTUAL, shipping.blockingReason)
        assertNull(shipping.quantifiedLeakage)
        assertNull(projection.totalQuantifiedLeakage, "A known subtotal must never be published as total leakage")
    }

    @Test fun `unsupported stage is unquantified`() {
        val assessment = assessment(stage = FinancialLedgerStage.TAX)
        val projection = project(case = durable(assessment), assessment = bound(assessment))
        assertEquals(EconomicDecisionRoomStageBlockingReason.UNSUPPORTED_STAGE, projection.stages.single().blockingReason)
        assertNull(projection.totalQuantifiedLeakage)
    }

    @Test fun `organization isolation returns not found without authority reads`() {
        var authorityReads = 0
        val repository = Repository(case)
        val service = EconomicDecisionRoomProjectionService(repository, EconomicDecisionRoomAuthoritySource { _, _ -> authorityReads++; canonicalAuthority() }, EconomicDecisionRoomReconciliationAssessmentSource { _, _ -> canonicalAssessment() })
        assertEquals(
            EconomicDecisionRoomProjectionReadResult.NotFound(EconomicDecisionRoomNotFoundDiagnostic.CASE_ABSENT),
            service.read(otherOrganization, caseId)
        )
        assertEquals(0, authorityReads)
    }

    @Test fun `repository cross organization leak remains externally not found`() {
        val foreignCase = DurableReconciliationCase.fromAssessment(caseId, assessment(organizationId = otherOrganization), instant, instant)
        val service = EconomicDecisionRoomProjectionService(
            LeakyRepository(foreignCase),
            EconomicDecisionRoomAuthoritySource { _, _ -> canonicalAuthority() },
            EconomicDecisionRoomReconciliationAssessmentSource { _, _ -> canonicalAssessment() }
        )
        assertEquals(
            EconomicDecisionRoomProjectionReadResult.NotFound(EconomicDecisionRoomNotFoundDiagnostic.ORGANIZATION_SCOPE_MISMATCH),
            service.read(organization, caseId)
        )
    }

    @Test fun `assessment cross organization mismatch remains externally not found`() {
        val foreign = assessment(organizationId = otherOrganization)
        val service = EconomicDecisionRoomProjectionService(
            Repository(case),
            EconomicDecisionRoomAuthoritySource { _, _ -> canonicalAuthority() },
            EconomicDecisionRoomReconciliationAssessmentSource { _, _ -> bound(foreign) }
        )
        assertEquals(
            EconomicDecisionRoomProjectionReadResult.NotFound(EconomicDecisionRoomNotFoundDiagnostic.ORGANIZATION_SCOPE_MISMATCH),
            service.read(organization, caseId)
        )
    }

    @Test fun `authority cross organization mismatch remains externally not found`() {
        val foreign = canonicalAuthorityContext().copy(organizationId = otherOrganization)
        val service = EconomicDecisionRoomProjectionService(
            Repository(case),
            EconomicDecisionRoomAuthoritySource { _, _ -> EconomicDecisionRoomAuthorityRead.Available(foreign) },
            EconomicDecisionRoomReconciliationAssessmentSource { _, _ -> canonicalAssessment() }
        )
        assertEquals(
            EconomicDecisionRoomProjectionReadResult.NotFound(EconomicDecisionRoomNotFoundDiagnostic.ORGANIZATION_SCOPE_MISMATCH),
            service.read(organization, caseId)
        )
    }

    @Test fun `assessment binding revision mismatch blocks interpretation`() {
        val projection = project(assessment = bound(assessment(), revision = case.revision + 1))
        assertTrue(EconomicDecisionRoomProjectionBlockingReason.RECONCILIATION_CONTEXT_MISMATCH in projection.projectionBlockingReasons)
        assertEquals(EconomicDecisionRoomStageBlockingReason.RECONCILIATION_CONTEXT_MISMATCH, projection.stages.single().blockingReason)
        assertEquals(EconomicDecisionRoomAuthorityStatus.NOT_ASSEMBLED, projection.authorityStatus)
        assertNull(projection.totalQuantifiedLeakage)
    }

    @Test fun `assessment binding case mismatch blocks interpretation`() {
        val projection = project(
            assessment = bound(
                assessment(),
                boundCaseId = ReconciliationCaseId.of(UUID.fromString("40000000-0000-0000-0000-000000000099"))
            )
        )
        assertEquals(EconomicDecisionRoomProjectionStatus.BLOCKED, projection.projectionStatus)
        assertEquals(EconomicDecisionRoomStageBlockingReason.RECONCILIATION_CONTEXT_MISMATCH, projection.stages.single().blockingReason)
        assertNull(projection.totalQuantifiedLeakage)
    }

    @Test fun `authority binding mismatch blocks before assembly with deterministic reasons`() {
        val mismatched = canonicalAuthorityContext().copy(reconciliationRevision = case.revision + 1)
        val projection = project(authority = EconomicDecisionRoomAuthorityRead.Available(mismatched))
        assertEquals(EconomicDecisionRoomProjectionStatus.BLOCKED, projection.projectionStatus)
        assertEquals(EconomicDecisionRoomAuthorityStatus.NOT_ASSEMBLED, projection.authorityStatus)
        assertEquals(
            listOf(
                EconomicDecisionRoomProjectionBlockingReason.AUTHORITY_CONTEXT_MISMATCH,
                EconomicDecisionRoomProjectionBlockingReason.AUTHORITY_NOT_ASSEMBLED
            ),
            projection.projectionBlockingReasons.toList()
        )
        assertEquals(EconomicDecisionRoomStageBlockingReason.AUTHORITY_CONTEXT_MISMATCH, projection.stages.single().blockingReason)
        assertNull(projection.totalQuantifiedLeakage)
    }

    @Test fun `authority subject mismatch blocks before assembly`() {
        val mismatched = canonicalAuthorityContext().copy(
            marketplaceOrderId = MarketplaceOrderId.parse("20000000-0000-0000-0000-000000000099")
        )
        val projection = project(authority = EconomicDecisionRoomAuthorityRead.Available(mismatched))
        assertEquals(EconomicDecisionRoomProjectionStatus.BLOCKED, projection.projectionStatus)
        assertEquals(EconomicDecisionRoomStageBlockingReason.AUTHORITY_CONTEXT_MISMATCH, projection.stages.single().blockingReason)
        assertNull(projection.totalQuantifiedLeakage)
    }

    @Test fun `provenance carries governed authorities reconciliation and ledger entries`() {
        val projection = project()
        assertEquals(
            setOf(
                "reconciliation-case:${caseId.value}",
                "financial-trace:${traceId.value}",
                "marketplace-order:${orderId.value}",
                "reconciliation-policy:${policy.value}",
                "financial-ledger-entry:${expectedId.value}",
                "financial-ledger-entry:${actualId.value}",
                "identity:1",
                "currency:1",
                "allocation:1",
                "currentness:1"
            ),
            projection.evidenceReferences
        )
    }

    private fun assertGovernanceBlocked(state: EconomicTruthAuthorityState) {
        val projection = project(authority = authority(state))
        assertEquals(EconomicDecisionRoomAuthorityStatus.ASSEMBLED, projection.authorityStatus)
        assertFalse(projection.governancePermitted)
        assertEquals(EconomicLeakageInterpretationStatus.UNQUANTIFIED, projection.stages.single().interpretation)
        assertNull(projection.totalQuantifiedLeakage)
    }

    private fun project(
        case: DurableReconciliationCase = this.case,
        authority: EconomicDecisionRoomAuthorityRead = canonicalAuthority(),
        assessment: EconomicDecisionRoomReconciliationAssessmentRead = canonicalAssessment()
    ): EconomicDecisionRoomReconciliationProjection {
        val service = EconomicDecisionRoomProjectionService(Repository(case), EconomicDecisionRoomAuthoritySource { _, _ -> authority }, EconomicDecisionRoomReconciliationAssessmentSource { _, _ -> assessment })
        return assertIs<EconomicDecisionRoomProjectionReadResult.Found>(service.read(organization, case.caseId)).projection
    }

    private fun authority(state: EconomicTruthAuthorityState) = EconomicDecisionRoomAuthorityRead.Available(
        canonicalAuthorityContext(
            EconomicTruthAuthorityInputs(
                EconomicTruthAuthorityEvidence(state, setOf("identity:1")),
                EconomicTruthAuthorityEvidence(EconomicTruthAuthorityState.CANONICAL, setOf("currency:1")),
                EconomicTruthAuthorityEvidence(EconomicTruthAuthorityState.CANONICAL, setOf("allocation:1")),
                EconomicTruthAuthorityEvidence(EconomicTruthAuthorityState.CANONICAL, setOf("currentness:1"))
            )
        )
    )
    private fun canonicalAuthority() = authority(EconomicTruthAuthorityState.CANONICAL)
    private fun canonicalAuthorityContext(inputs: EconomicTruthAuthorityInputs = canonicalInputs()) = EconomicDecisionRoomAuthorityContext(
        organization, caseId, orderId, traceId, policy, currency, case.revision, inputs
    )
    private fun canonicalInputs() = EconomicTruthAuthorityInputs(
        EconomicTruthAuthorityEvidence(EconomicTruthAuthorityState.CANONICAL, setOf("identity:1")),
        EconomicTruthAuthorityEvidence(EconomicTruthAuthorityState.CANONICAL, setOf("currency:1")),
        EconomicTruthAuthorityEvidence(EconomicTruthAuthorityState.CANONICAL, setOf("allocation:1")),
        EconomicTruthAuthorityEvidence(EconomicTruthAuthorityState.CANONICAL, setOf("currentness:1"))
    )
    private fun canonicalAssessment() = bound(assessment())
    private fun bound(
        assessment: FinancialReconciliationAssessment,
        revision: Long = 1,
        boundCaseId: ReconciliationCaseId = caseId
    ) = EconomicDecisionRoomReconciliationAssessmentRead.Available(
        EconomicDecisionRoomReconciliationAssessmentBinding(boundCaseId, revision, assessment)
    )

    private fun assessment(
        expected: String? = "-100",
        actual: String? = "-110",
        stage: FinancialLedgerStage = FinancialLedgerStage.SALE,
        organizationId: OrganizationId = organization
    ): FinancialReconciliationAssessment {
        val expectedSide = expected?.let { FinancialReconciliationSide.Observed(MarketplaceMoney.parse(currency, it), listOf(expectedId)) } ?: FinancialReconciliationSide.NotObserved
        val actualSide = actual?.let { FinancialReconciliationSide.Observed(MarketplaceMoney.parse(currency, it), listOf(actualId)) } ?: FinancialReconciliationSide.NotObserved
        val difference = if (expectedSide is FinancialReconciliationSide.Observed && actualSide is FinancialReconciliationSide.Observed) {
            val signed = actualSide.netAmount - expectedSide.netAmount
            FinancialReconciliationDifference.Compared(signed, MarketplaceMoney.parse(currency, signed.amount.abs().toPlainString()), MarketplaceMoney.parse(currency, "0"))
        } else FinancialReconciliationDifference.NotComparable
        val status = when {
            expectedSide is FinancialReconciliationSide.NotObserved -> FinancialReconciliationStatus.DIVERGENCE
            actualSide is FinancialReconciliationSide.NotObserved -> FinancialReconciliationStatus.PENDING
            else -> FinancialReconciliationStatus.DIVERGENCE
        }
        val line = FinancialReconciliationLine(stage, expectedSide, actualSide, difference, status)
        return FinancialReconciliationAssessment(organizationId, traceId, orderId, currency, policy, listOf(line), status)
    }

    private fun durable(assessment: FinancialReconciliationAssessment) = DurableReconciliationCase.fromAssessment(caseId, assessment, instant, instant)
    private val organization = OrganizationId.parse("10000000-0000-0000-0000-000000000001")
    private val otherOrganization = OrganizationId.parse("10000000-0000-0000-0000-000000000002")
    private val orderId = MarketplaceOrderId.parse("20000000-0000-0000-0000-000000000001")
    private val traceId = FinancialTraceId.parse("30000000-0000-0000-0000-000000000001")
    private val caseId = ReconciliationCaseId.of(UUID.fromString("40000000-0000-0000-0000-000000000001"))
    private val expectedId = FinancialLedgerEntryId.parse("50000000-0000-0000-0000-000000000001")
    private val actualId = FinancialLedgerEntryId.parse("50000000-0000-0000-0000-000000000002")
    private val currency = MarketplaceCurrency("BRL")
    private val policy = FinancialReconciliationPolicyVersion("policy/1")
    private val instant = Instant.parse("2026-09-13T12:00:00Z")
    private val case get() = durable(assessment())

    private class Repository(private val value: DurableReconciliationCase) : DurableReconciliationCaseRepository {
        override fun save(value: DurableReconciliationCase) = error("read only")
        override fun find(organizationId: OrganizationId, caseId: ReconciliationCaseId) = value.takeIf { it.organizationId == organizationId && it.caseId == caseId }
        override fun list(organizationId: OrganizationId, cursor: ReconciliationCaseCursor?, limit: Int) = error("not used")
    }

    private class LeakyRepository(private val value: DurableReconciliationCase) : DurableReconciliationCaseRepository {
        override fun save(value: DurableReconciliationCase) = error("read only")
        override fun find(organizationId: OrganizationId, caseId: ReconciliationCaseId) = value
        override fun list(organizationId: OrganizationId, cursor: ReconciliationCaseCursor?, limit: Int) = error("not used")
    }
}
