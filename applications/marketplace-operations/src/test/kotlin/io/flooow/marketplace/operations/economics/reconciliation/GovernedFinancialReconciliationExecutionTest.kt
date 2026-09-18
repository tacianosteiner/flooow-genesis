package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicExternalReference
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerAppendRequestId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerAppendResult
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryDraft
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTrace
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceOpenRequestId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceOpenResult
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceReadResult
import io.flooow.marketplace.operations.economics.ledger.MarketplaceFinancialLedgerRepository
import io.flooow.marketplace.operations.economics.ledger.OpenFinancialTrace
import io.flooow.marketplace.operations.economics.ledger.RecordedFinancialLedgerEntry
import io.flooow.organization.OrganizationId
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotNull

class GovernedFinancialReconciliationExecutionTest {
    private val orgA =
        OrganizationId.parse(
            "10000000-0000-0000-0000-000000000001"
        )

    private val orgB =
        OrganizationId.parse(
            "10000000-0000-0000-0000-000000000002"
        )

    private val traceId =
        FinancialTraceId.parse(
            "20000000-0000-0000-0000-000000000001"
        )

    private val orderId =
        MarketplaceOrderId.parse(
            "30000000-0000-0000-0000-000000000001"
        )

    private val brl =
        MarketplaceCurrency("BRL")

    private val acceptedClock =
        Clock.fixed(
            Instant.parse(
                "2026-09-13T18:30:00.123456789Z"
            ),
            ZoneOffset.UTC
        )

    @Test
    fun `durable trace is assessed accepted internally and sent to governed authority`() {
        val ledger =
            StubLedger {
                FinancialTraceReadResult.Found(
                    divergentTrace(orgA)
                )
            }

        val cases =
            MemoryCaseRepository()

        val commits =
            CapturingCommitStore()

        val service =
            GovernedFinancialReconciliationExecutionService(
                ledger = ledger,
                policySource =
                    FinancialReconciliationPolicySource {
                        context ->
                        FinancialReconciliationPolicySelection
                            .Selected(
                                zeroPolicy(
                                    context.currency
                                )
                            )
                    },
                orchestrator =
                    GovernedReconciliationCaseOrchestrator(
                        cases,
                        commits
                    ),
                clock = acceptedClock
            )

        val result =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .Orchestrated
                >(
                service.execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            FinancialReconciliationStatus.DIVERGENCE,
            result.assessmentStatus
        )

        val created =
            assertIs<
                ReconciliationCaseOrchestrationResult.Created
                >(
                result.orchestration
            )

        assertEquals(
            1L,
            created.value.revision
        )

        val command =
            assertNotNull(
                commits.command
            )

        assertEquals(
            Instant.parse(
                "2026-09-13T18:30:00.123456Z"
            ),
            command.acceptedAssessment.acceptedAt
        )

        assertEquals(
            FinancialReconciliationAssessmentFingerprinter
                .fingerprint(
                    command.acceptedAssessment.assessment
                ),
            command.acceptedAssessment
                .assessmentFingerprint
        )

        assertEquals(
            traceId,
            command.acceptedAssessment
                .assessment
                .traceId
        )

        assertEquals(
            orgA,
            command.acceptedAssessment
                .assessment
                .organizationId
        )
    }

    @Test
    fun `policy selection is scoped by durable tenant marketplace and currency`() {
        var selected:
            FinancialReconciliationPolicyContext? = null

        val service =
            GovernedFinancialReconciliationExecutionService(
                ledger =
                    StubLedger {
                        FinancialTraceReadResult.Found(
                            divergentTrace(orgA)
                        )
                    },
                policySource =
                    FinancialReconciliationPolicySource {
                        context ->
                        selected =
                            context

                        FinancialReconciliationPolicySelection
                            .Selected(
                                zeroPolicy(
                                    context.currency
                                )
                            )
                    },
                orchestrator =
                    orchestrator(
                        CapturingCommitStore()
                    ),
                clock = acceptedClock
            )

        assertIs<
            GovernedFinancialReconciliationExecutionResult
                .Orchestrated
            >(
            service.execute(
                orgA,
                traceId
            )
        )

        val context =
            assertNotNull(
                selected
            )

        assertEquals(
            orgA,
            context.organizationId
        )

        assertEquals(
            MarketplaceKey(
                "mercado-livre"
            ),
            context.marketplace
        )

        assertEquals(
            brl,
            context.currency
        )

        assertEquals(
            "[REDACTED]",
            context.toString()
        )
    }

    @Test
    fun `fully reconciled trace is assessed but never creates a divergence case`() {
        val commits =
            CapturingCommitStore()

        val service =
            service(
                FinancialTraceReadResult.Found(
                    completeTrace(orgA)
                ),
                commits = commits
            )

        val result =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .Orchestrated
                >(
                service.execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            FinancialReconciliationStatus.FULLY_RECONCILED,
            result.assessmentStatus
        )

        assertEquals(
            ReconciliationCaseOrchestrationResult.NotEligible,
            result.orchestration
        )

        assertEquals(
            null,
            commits.command
        )
    }

    @Test
    fun `empty durable trace is explicitly not assessable`() {
        val service =
            service(
                FinancialTraceReadResult.Found(
                    trace(
                        organizationId = orgA,
                        entries = emptyList()
                    )
                )
            )

        val result =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .NotAssessable
                >(
                service.execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            FinancialReconciliationNotAssessableReason
                .NO_FINANCIAL_FACTS,
            result.reason
        )
    }

    @Test
    fun `trace absence integrity corruption and reader failure stay distinct`() {
        val notFound =
            service(
                FinancialTraceReadResult.NotFound
            ).execute(
                orgA,
                traceId
            )

        assertEquals(
            GovernedFinancialReconciliationExecutionResult
                .TraceNotFound,
            notFound
        )

        val unavailable =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .Failed
                >(
                service(
                    FinancialTraceReadResult.Unavailable
                ).execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            GovernedFinancialReconciliationExecutionFailure
                .TRACE_READ_FAILURE,
            unavailable.failure
        )

        val integrity =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .Failed
                >(
                service(
                    FinancialTraceReadResult.IntegrityFailure
                ).execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            GovernedFinancialReconciliationExecutionFailure
                .TRACE_INTEGRITY_FAILURE,
            integrity.failure
        )

        val readFailure =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .Failed
                >(
                GovernedFinancialReconciliationExecutionService(
                    ledger =
                        StubLedger {
                            error(
                                "database unavailable"
                            )
                        },
                    policySource =
                        selectedPolicySource(),
                    orchestrator =
                        orchestrator(
                            CapturingCommitStore()
                        ),
                    clock = acceptedClock
                ).execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            GovernedFinancialReconciliationExecutionFailure
                .TRACE_READ_FAILURE,
            readFailure.failure
        )
    }

    @Test
    fun `cross tenant trace from corrupted reader fails closed before policy or orchestration`() {
        var policyCalls = 0

        val commits =
            CapturingCommitStore()

        val service =
            GovernedFinancialReconciliationExecutionService(
                ledger =
                    StubLedger {
                        FinancialTraceReadResult.Found(
                            divergentTrace(orgB)
                        )
                    },
                policySource =
                    FinancialReconciliationPolicySource {
                        policyCalls += 1
                        FinancialReconciliationPolicySelection
                            .Selected(
                                zeroPolicy(it.currency)
                            )
                    },
                orchestrator =
                    orchestrator(
                        commits
                    ),
                clock = acceptedClock
            )

        val result =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .Failed
                >(
                service.execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            GovernedFinancialReconciliationExecutionFailure
                .TRACE_INTEGRITY_FAILURE,
            result.failure
        )

        assertEquals(
            0,
            policyCalls
        )

        assertEquals(
            null,
            commits.command
        )
    }

    @Test
    fun `policy authority is explicit unavailable and wrong currency fails closed`() {
        val unavailable =
            GovernedFinancialReconciliationExecutionService(
                ledger =
                    StubLedger {
                        FinancialTraceReadResult.Found(
                            divergentTrace(orgA)
                        )
                    },
                policySource =
                    FinancialReconciliationPolicySource {
                        FinancialReconciliationPolicySelection
                            .Unavailable
                    },
                orchestrator =
                    orchestrator(
                        CapturingCommitStore()
                    ),
                clock = acceptedClock
            ).execute(
                orgA,
                traceId
            )

        assertEquals(
            GovernedFinancialReconciliationExecutionResult
                .PolicyUnavailable,
            unavailable
        )

        val wrongCurrency =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .Failed
                >(
                GovernedFinancialReconciliationExecutionService(
                    ledger =
                        StubLedger {
                            FinancialTraceReadResult.Found(
                                divergentTrace(orgA)
                            )
                        },
                    policySource =
                        FinancialReconciliationPolicySource {
                            FinancialReconciliationPolicySelection
                                .Selected(
                                    zeroPolicy(
                                        MarketplaceCurrency(
                                            "USD"
                                        )
                                    )
                                )
                        },
                    orchestrator =
                        orchestrator(
                            CapturingCommitStore()
                        ),
                    clock = acceptedClock
                ).execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            GovernedFinancialReconciliationExecutionFailure
                .POLICY_INTEGRITY_FAILURE,
            wrongCurrency.failure
        )
    }

    @Test
    fun `typed policy read and integrity failures remain distinct`() {
        val cases =
            listOf(
                FinancialReconciliationPolicySelection.ReadFailure to
                    GovernedFinancialReconciliationExecutionFailure
                        .POLICY_READ_FAILURE,
                FinancialReconciliationPolicySelection.IntegrityFailure to
                    GovernedFinancialReconciliationExecutionFailure
                        .POLICY_INTEGRITY_FAILURE
            )

        cases.forEach { (selection, expectedFailure) ->
            val commits =
                CapturingCommitStore()

            val result =
                assertIs<
                    GovernedFinancialReconciliationExecutionResult
                        .Failed
                    >(
                    GovernedFinancialReconciliationExecutionService(
                        ledger =
                            StubLedger {
                                FinancialTraceReadResult.Found(
                                    divergentTrace(orgA)
                                )
                            },
                        policySource =
                            FinancialReconciliationPolicySource {
                                selection
                            },
                        orchestrator =
                            orchestrator(
                                commits
                            ),
                        clock = acceptedClock
                    ).execute(
                        orgA,
                        traceId
                    )
                )

            assertEquals(
                expectedFailure,
                result.failure
            )

            assertEquals(
                null,
                commits.command
            )
        }
    }

    @Test
    fun `policy source failure is controlled and never reaches governed commit`() {
        val commits =
            CapturingCommitStore()

        val result =
            assertIs<
                GovernedFinancialReconciliationExecutionResult
                    .Failed
                >(
                GovernedFinancialReconciliationExecutionService(
                    ledger =
                        StubLedger {
                            FinancialTraceReadResult.Found(
                                divergentTrace(orgA)
                            )
                        },
                    policySource =
                        FinancialReconciliationPolicySource {
                            error(
                                "policy authority unavailable"
                            )
                        },
                    orchestrator =
                        orchestrator(
                            commits
                        ),
                    clock = acceptedClock
                ).execute(
                    orgA,
                    traceId
                )
            )

        assertEquals(
            GovernedFinancialReconciliationExecutionFailure
                .POLICY_READ_FAILURE,
            result.failure
        )

        assertEquals(
            null,
            commits.command
        )
    }

    @Test
    fun `execution result renderings remain redacted`() {
        val renderings =
            listOf(
                GovernedFinancialReconciliationExecutionResult
                    .TraceNotFound
                    .toString(),
                GovernedFinancialReconciliationExecutionResult
                    .PolicyUnavailable
                    .toString(),
                GovernedFinancialReconciliationExecutionResult
                    .Failed(
                        GovernedFinancialReconciliationExecutionFailure
                            .TRACE_READ_FAILURE
                    )
                    .toString(),
                FinancialReconciliationPolicySelection
                    .Unavailable
                    .toString(),
                FinancialReconciliationPolicySelection
                    .Selected(
                        zeroPolicy(brl)
                    )
                    .toString()
            )

        assertEquals(
            List(
                renderings.size
            ) {
                "[REDACTED]"
            },
            renderings
        )
    }

    private fun service(
        read: FinancialTraceReadResult,
        commits: CapturingCommitStore =
            CapturingCommitStore()
    ): GovernedFinancialReconciliationExecutionService =
        GovernedFinancialReconciliationExecutionService(
            ledger =
                StubLedger {
                    read
                },
            policySource =
                selectedPolicySource(),
            orchestrator =
                orchestrator(
                    commits
                ),
            clock = acceptedClock
        )

    private fun selectedPolicySource():
        FinancialReconciliationPolicySource =
        FinancialReconciliationPolicySource {
            FinancialReconciliationPolicySelection
                .Selected(
                    zeroPolicy(it.currency)
                )
        }

    private fun orchestrator(
        commits: CapturingCommitStore
    ): GovernedReconciliationCaseOrchestrator =
        GovernedReconciliationCaseOrchestrator(
            MemoryCaseRepository(),
            commits
        )

    private fun zeroPolicy(
        currency: MarketplaceCurrency
    ): FinancialReconciliationPolicy =
        FinancialReconciliationPolicy(
            FinancialReconciliationPolicyVersion(
                "pilot-reconciliation/1"
            ),
            currency,
            FinancialLedgerStage.entries
                .associateWith {
                    MarketplaceMoney.parse(
                        currency,
                        "0"
                    )
                }
        )

    private fun divergentTrace(
        organizationId: OrganizationId
    ): FinancialTrace =
        trace(
            organizationId,
            listOf(
                entry(
                    organizationId,
                    1,
                    FinancialLedgerBasis.EXPECTED,
                    "10"
                ),
                entry(
                    organizationId,
                    2,
                    FinancialLedgerBasis.ACTUAL,
                    "12"
                )
            )
        )

    private fun completeTrace(
        organizationId: OrganizationId
    ): FinancialTrace =
        trace(
            organizationId,
            listOf(
                entry(
                    organizationId,
                    1,
                    FinancialLedgerBasis.EXPECTED,
                    "10"
                ),
                entry(
                    organizationId,
                    2,
                    FinancialLedgerBasis.ACTUAL,
                    "10"
                )
            )
        )

    private fun trace(
        organizationId: OrganizationId,
        entries: Collection<RecordedFinancialLedgerEntry>
    ): FinancialTrace =
        FinancialTrace(
            organizationId = organizationId,
            id = traceId,
            requestId =
                FinancialTraceOpenRequestId.of(
                    UUID.fromString(
                        "21000000-0000-0000-0000-000000000001"
                    )
                ),
            orderId = orderId,
            marketplace =
                MarketplaceKey(
                    "mercado-livre"
                ),
            externalOrderId =
                MarketplaceExternalOrderId(
                    "order-001"
                ),
            currency = brl,
            openedAt =
                Instant.parse(
                    "2026-09-13T18:00:00Z"
                ),
            entries = entries
        )

    private fun entry(
        organizationId: OrganizationId,
        number: Int,
        basis: FinancialLedgerBasis,
        amount: String
    ): RecordedFinancialLedgerEntry =
        RecordedFinancialLedgerEntry(
            organizationId = organizationId,
            id =
                FinancialLedgerEntryId.of(
                    UUID.fromString(
                        "40000000-0000-0000-0000-" +
                            number
                                .toString()
                                .padStart(
                                    12,
                                    '0'
                                )
                    )
                ),
            requestId =
                FinancialLedgerAppendRequestId.of(
                    UUID.fromString(
                        "50000000-0000-0000-0000-" +
                            number
                                .toString()
                                .padStart(
                                    12,
                                    '0'
                                )
                    )
                ),
            traceId = traceId,
            stage =
                FinancialLedgerStage.SALE,
            basis = basis,
            direction =
                EconomicDirection.ADDITION,
            magnitude =
                MarketplaceMoney.parse(
                    brl,
                    amount
                ),
            source =
                EconomicSource(
                    EconomicSourceKind.MARKETPLACE,
                    EconomicSourceSystemKey(
                        "meli-br"
                    ),
                    EconomicExternalReferenceState
                        .Present(
                            EconomicExternalReference(
                                "fact-$number"
                            )
                        )
                ),
            occurredAt =
                Instant.parse(
                    "2026-09-13T18:05:00Z"
                ).plusSeconds(
                    number.toLong()
                ),
            recordedAt =
                Instant.parse(
                    "2026-09-13T18:06:00Z"
                ).plusSeconds(
                    number.toLong()
                )
        )

    private class StubLedger(
        private val reader:
            (
                OrganizationId,
                FinancialTraceId
            ) -> FinancialTraceReadResult
    ) : MarketplaceFinancialLedgerRepository {
        constructor(
            reader: () -> FinancialTraceReadResult
        ) : this(
            { _, _ ->
                reader()
            }
        )

        override fun open(
            command: OpenFinancialTrace,
            traceId: FinancialTraceId
        ): FinancialTraceOpenResult =
            error(
                "open is outside execution test scope"
            )

        override fun append(
            draft: FinancialLedgerEntryDraft,
            entryId: FinancialLedgerEntryId
        ): FinancialLedgerAppendResult =
            error(
                "append is outside execution test scope"
            )

        override fun find(
            organizationId: OrganizationId,
            traceId: FinancialTraceId
        ): FinancialTraceReadResult =
            reader(
                organizationId,
                traceId
            )

        override fun findByOrder(
            organizationId: OrganizationId,
            orderId: MarketplaceOrderId
        ): FinancialTraceReadResult =
            error(
                "findByOrder is outside execution test scope"
            )
    }

    private class MemoryCaseRepository :
        DurableReconciliationCaseRepository {
        override fun save(
            value: DurableReconciliationCase
        ): DurableReconciliationCase =
            error(
                "legacy save authority must not be used"
            )

        override fun find(
            organizationId: OrganizationId,
            caseId: ReconciliationCaseId
        ): DurableReconciliationCase? =
            null

        override fun list(
            organizationId: OrganizationId,
            cursor: ReconciliationCaseCursor?,
            limit: Int
        ): ReconciliationCasePage =
            ReconciliationCasePage(
                emptyList(),
                null
            )
    }

    private class CapturingCommitStore :
        GovernedReconciliationCaseRevisionCommitStore {
        var command:
            GovernedReconciliationCaseRevisionCommit? = null
            private set

        override fun commit(
            command: GovernedReconciliationCaseRevisionCommit
        ): GovernedReconciliationCaseCommitResult {
            this.command =
                command

            return GovernedReconciliationCaseCommitResult
                .Applied(
                    command.caseValue.revision
                )
        }
    }
}
