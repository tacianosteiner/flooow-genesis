package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs

class GovernedReconciliationCaseOrchestratorTest {
    private val currency =
        MarketplaceCurrency("BRL")

    private val orgA =
        OrganizationId(
            UUID.fromString(
                "10000000-0000-0000-0000-000000000001"
            )
        )

    private val orgB =
        OrganizationId(
            UUID.fromString(
                "10000000-0000-0000-0000-000000000002"
            )
        )

    private val trace =
        FinancialTraceId.of(
            UUID.fromString(
                "20000000-0000-0000-0000-000000000001"
            )
        )

    private val order =
        MarketplaceOrderId(
            UUID.fromString(
                "30000000-0000-0000-0000-000000000001"
            )
        )

    private val at =
        Instant.parse(
            "2026-09-08T12:00:00Z"
        )

    @Test
    fun `accepted divergence creates and exact replay is unchanged without duplicate analysis`() {
        val repository =
            MemoryRepository()

        val commitStore =
            MemoryCommitStore(repository)

        var analyses = 0

        val orchestrator =
            GovernedReconciliationCaseOrchestrator(
                repository,
                commitStore,
                SystemicDivergenceAnalysisTrigger { _, _ ->
                    analyses += 1
                }
            )

        val accepted =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment(
                    absolute = "5",
                    pendingExpected = "20"
                ),
                at
            )

        val created =
            assertIs<ReconciliationCaseOrchestrationResult.Created>(
                orchestrator.process(
                    accepted,
                    orgA
                )
            )

        val unchanged =
            assertIs<ReconciliationCaseOrchestrationResult.Unchanged>(
                orchestrator.process(
                    accepted,
                    orgA
                )
            )

        assertEquals(
            created.value.caseId,
            unchanged.value.caseId
        )

        assertEquals(
            1L,
            unchanged.value.revision
        )

        assertEquals(
            1,
            repository.values.size
        )

        assertEquals(
            1,
            analyses
        )
    }

    @Test
    fun `exact assessment identity revises even when divergent case projection is unchanged`() {
        val repository =
            MemoryRepository()

        val commitStore =
            MemoryCommitStore(repository)

        val orchestrator =
            GovernedReconciliationCaseOrchestrator(
                repository,
                commitStore
            )

        val first =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment(
                    absolute = "5",
                    pendingExpected = "20"
                ),
                at
            )

        val second =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment(
                    absolute = "5",
                    pendingExpected = "21"
                ),
                at.plusSeconds(1)
            )

        val created =
            assertIs<ReconciliationCaseOrchestrationResult.Created>(
                orchestrator.process(
                    first,
                    orgA
                )
            )

        val revised =
            assertIs<ReconciliationCaseOrchestrationResult.Revised>(
                orchestrator.process(
                    second,
                    orgA
                )
            )

        assertEquals(
            created.value.absoluteDifferenceSummary,
            revised.value.absoluteDifferenceSummary
        )

        assertEquals(
            created.value.stages.single().stage,
            revised.value.stages.single().stage
        )

        assertEquals(
            2L,
            revised.value.revision
        )

        assertEquals(
            2,
            commitStore.appliedFingerprints.size
        )
    }

    @Test
    fun `material divergent observation revises and other organization is rejected`() {
        val repository =
            MemoryRepository()

        val commitStore =
            MemoryCommitStore(repository)

        val orchestrator =
            GovernedReconciliationCaseOrchestrator(
                repository,
                commitStore
            )

        val first =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment("5"),
                at
            )

        orchestrator.process(
            first,
            orgA
        )

        val revised =
            assertIs<ReconciliationCaseOrchestrationResult.Revised>(
                orchestrator.process(
                    AcceptedFinancialReconciliationAssessment.accept(
                        assessment("7"),
                        at.plusSeconds(1)
                    ),
                    orgA
                )
            )

        assertEquals(
            2L,
            revised.value.revision
        )

        assertEquals(
            ReconciliationCaseOrchestrationResult.Rejected(
                ReconciliationCaseOrchestrationFailure
                    .ORGANIZATION_MISMATCH
            ),
            orchestrator.process(
                first,
                orgB
            )
        )
    }

    @Test
    fun `non divergent assessment is not eligible and never reaches commit authority`() {
        val repository =
            MemoryRepository()

        val commitStore =
            MemoryCommitStore(repository)

        val orchestrator =
            GovernedReconciliationCaseOrchestrator(
                repository,
                commitStore
            )

        val reconciled =
            assessment(
                absolute = "0",
                status =
                    FinancialReconciliationStatus
                        .FULLY_RECONCILED
            )

        assertEquals(
            ReconciliationCaseOrchestrationResult.NotEligible,
            orchestrator.process(
                AcceptedFinancialReconciliationAssessment.accept(
                    reconciled,
                    at
                ),
                orgA
            )
        )

        assertEquals(
            0,
            commitStore.commitCount
        )
    }

    @Test
    fun `systemic analysis failure cannot rewrite an applied governed commit`() {
        val repository =
            MemoryRepository()

        val commitStore =
            MemoryCommitStore(repository)

        val orchestrator =
            GovernedReconciliationCaseOrchestrator(
                repository,
                commitStore,
                SystemicDivergenceAnalysisTrigger { _, _ ->
                    error("derived systemic projection unavailable")
                }
            )

        val result =
            orchestrator.process(
                AcceptedFinancialReconciliationAssessment.accept(
                    assessment("5"),
                    at
                ),
                orgA
            )

        val created =
            assertIs<ReconciliationCaseOrchestrationResult.Created>(
                result
            )

        assertEquals(
            1L,
            created.value.revision
        )

        assertEquals(
            1L,
            repository.values
                .getValue(created.value.caseId)
                .revision
        )
    }

    @Test
    fun `impossible applied revision fails closed as integrity failure`() {
        val repository =
            MemoryRepository()

        val commitStore =
            MemoryCommitStore(
                repository,
                forcedAppliedRevision = 999L
            )

        val result =
            GovernedReconciliationCaseOrchestrator(
                repository,
                commitStore
            ).process(
                AcceptedFinancialReconciliationAssessment.accept(
                    assessment("5"),
                    at
                ),
                orgA
            )

        assertEquals(
            ReconciliationCaseOrchestrationResult.Failed(
                ReconciliationCaseOrchestrationFailure
                    .INTEGRITY_FAILURE
            ),
            result
        )
    }

    @Test
    fun `governed commit failures remain semantically distinct and do not trigger systemic analysis`() {
        val failures =
            listOf(
                GovernedReconciliationCaseCommitFailure.CONFLICT to
                    ReconciliationCaseOrchestrationFailure.CONFLICT,

                GovernedReconciliationCaseCommitFailure.INTEGRITY_FAILURE to
                    ReconciliationCaseOrchestrationFailure.INTEGRITY_FAILURE,

                GovernedReconciliationCaseCommitFailure.UNAVAILABLE to
                    ReconciliationCaseOrchestrationFailure.UNAVAILABLE
            )

        failures.forEach { (commitFailure, expectedFailure) ->
            val repository =
                MemoryRepository()

            val commitStore =
                MemoryCommitStore(
                    repository,
                    forcedFailure = commitFailure
                )

            var analyses = 0

            val orchestrator =
                GovernedReconciliationCaseOrchestrator(
                    repository,
                    commitStore,
                    SystemicDivergenceAnalysisTrigger { _, _ ->
                        analyses += 1
                    }
                )

            val result =
                orchestrator.process(
                    AcceptedFinancialReconciliationAssessment.accept(
                        assessment("5"),
                        at
                    ),
                    orgA
                )

            assertEquals(
                ReconciliationCaseOrchestrationResult.Failed(
                    expectedFailure
                ),
                result
            )

            assertEquals(
                0,
                analyses
            )
        }
    }

    @Test
    fun `reader failure remains fail closed before governed commit`() {
        val repository =
            MemoryRepository(
                failReads = true
            )

        val commitStore =
            MemoryCommitStore(repository)

        val result =
            GovernedReconciliationCaseOrchestrator(
                repository,
                commitStore
            ).process(
                AcceptedFinancialReconciliationAssessment.accept(
                    assessment("5"),
                    at
                ),
                orgA
            )

        assertEquals(
            ReconciliationCaseOrchestrationResult.Failed(
                ReconciliationCaseOrchestrationFailure.PERSISTENCE
            ),
            result
        )

        assertEquals(
            0,
            commitStore.commitCount
        )
    }

    private fun assessment(
        absolute: String,
        expected: String? = "10",
        pendingExpected: String? = null,
        status: FinancialReconciliationStatus =
            FinancialReconciliationStatus.DIVERGENCE
    ): FinancialReconciliationAssessment {
        val saleExpected =
            expected?.let {
                FinancialReconciliationSide.Observed(
                    money(it),
                    listOf(entry(1))
                )
            } ?: FinancialReconciliationSide.NotObserved

        val saleActualAmount =
            if (expected == null) {
                "5"
            } else if (
                status ==
                FinancialReconciliationStatus.FULLY_RECONCILED
            ) {
                expected
            } else {
                (
                    expected.toBigDecimal() +
                        absolute.toBigDecimal()
                    ).toPlainString()
            }

        val saleActual =
            FinancialReconciliationSide.Observed(
                money(saleActualAmount),
                listOf(entry(2))
            )

        val saleDifference =
            if (expected == null) {
                FinancialReconciliationDifference.NotComparable
            } else {
                FinancialReconciliationDifference.Compared(
                    signedDifference =
                        money(
                            if (
                                status ==
                                FinancialReconciliationStatus
                                    .FULLY_RECONCILED
                            ) {
                                "0"
                            } else {
                                absolute
                            }
                        ),
                    absoluteDifference =
                        money(absolute),
                    tolerance =
                        money("0")
                )
            }

        val sale =
            FinancialReconciliationLine(
                stage =
                    FinancialLedgerStage.SALE,
                expected = saleExpected,
                actual = saleActual,
                difference = saleDifference,
                status = status
            )

        val lines =
            mutableListOf(
                sale
            )

        if (pendingExpected != null) {
            lines +=
                FinancialReconciliationLine(
                    stage =
                        FinancialLedgerStage.TAX,
                    expected =
                        FinancialReconciliationSide.Observed(
                            money(pendingExpected),
                            listOf(entry(3))
                        ),
                    actual =
                        FinancialReconciliationSide.NotObserved,
                    difference =
                        FinancialReconciliationDifference.NotComparable,
                    status =
                        FinancialReconciliationStatus.PENDING
                )
        }

        return FinancialReconciliationAssessment(
            organizationId = orgA,
            traceId = trace,
            orderId = order,
            currency = currency,
            policyVersion =
                FinancialReconciliationPolicyVersion(
                    "case/1"
                ),
            lines = lines,
            status = status
        )
    }

    private fun money(
        value: String
    ): MarketplaceMoney =
        MarketplaceMoney.calculated(
            currency,
            value.toBigDecimal()
        )

    private fun entry(
        value: Long
    ): FinancialLedgerEntryId =
        FinancialLedgerEntryId.of(
            UUID.fromString(
                "40000000-0000-0000-0000-" +
                    value.toString().padStart(
                        12,
                        '0'
                    )
            )
        )

    private class MemoryRepository(
        private val failReads: Boolean = false
    ) : DurableReconciliationCaseRepository {
        val values =
            mutableMapOf<
                ReconciliationCaseId,
                DurableReconciliationCase
                >()

        override fun save(
            value: DurableReconciliationCase
        ): DurableReconciliationCase {
            error(
                "Legacy save authority must not be used by governed orchestration"
            )
        }

        override fun find(
            organizationId: OrganizationId,
            caseId: ReconciliationCaseId
        ): DurableReconciliationCase? {
            if (failReads) {
                error(
                    "case reader unavailable"
                )
            }

            return values[caseId]
                ?.takeIf {
                    it.organizationId ==
                        organizationId
                }
        }

        override fun list(
            organizationId: OrganizationId,
            cursor: ReconciliationCaseCursor?,
            limit: Int
        ): ReconciliationCasePage =
            ReconciliationCasePage(
                values.values
                    .filter {
                        it.organizationId ==
                            organizationId
                    },
                null
            )
    }

    private class MemoryCommitStore(
        private val repository: MemoryRepository,
        private val forcedFailure:
            GovernedReconciliationCaseCommitFailure? = null,
        private val forcedAppliedRevision: Long? = null
    ) : GovernedReconciliationCaseRevisionCommitStore {
        private val fingerprints =
            mutableMapOf<
                ReconciliationCaseId,
                FinancialReconciliationAssessmentFingerprint
                >()

        val appliedFingerprints =
            mutableListOf<
                FinancialReconciliationAssessmentFingerprint
                >()

        var commitCount: Int = 0
            private set

        override fun commit(
            command: GovernedReconciliationCaseRevisionCommit
        ): GovernedReconciliationCaseCommitResult {
            commitCount += 1

            if (forcedFailure != null) {
                return GovernedReconciliationCaseCommitResult.Failed(
                    forcedFailure
                )
            }

            val id =
                command.caseValue.caseId

            val current =
                repository.values[id]

            val fingerprint =
                command.acceptedAssessment
                    .assessmentFingerprint

            if (
                current != null &&
                fingerprints[id] == fingerprint
            ) {
                return GovernedReconciliationCaseCommitResult
                    .AlreadyApplied(
                        current.revision
                    )
            }

            if (
                current == null &&
                command.caseValue.revision != 1L
            ) {
                return GovernedReconciliationCaseCommitResult.Failed(
                    GovernedReconciliationCaseCommitFailure.CONFLICT
                )
            }

            if (
                current != null &&
                command.caseValue.revision !=
                current.revision + 1L
            ) {
                return GovernedReconciliationCaseCommitResult.Failed(
                    GovernedReconciliationCaseCommitFailure.CONFLICT
                )
            }

            repository.values[id] =
                command.caseValue

            fingerprints[id] =
                fingerprint

            appliedFingerprints +=
                fingerprint

            return GovernedReconciliationCaseCommitResult.Applied(
                forcedAppliedRevision
                    ?: command.caseValue.revision
            )
        }
    }
}
