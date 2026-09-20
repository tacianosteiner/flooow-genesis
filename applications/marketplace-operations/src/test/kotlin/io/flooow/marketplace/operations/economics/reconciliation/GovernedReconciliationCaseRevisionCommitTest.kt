package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.organization.OrganizationId
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class GovernedReconciliationCaseRevisionCommitTest {
    private val currency = MarketplaceCurrency("BRL")
    private val acceptedAt = Instant.parse("2026-09-13T18:00:00.123456Z")

    @Test
    fun `commit command binds exact accepted assessment snapshot internally`() {
        val assessment = assessment()
        val accepted =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment,
                acceptedAt
            )

        val caseValue =
            DurableReconciliationCase.fromAssessment(
                caseId = DurableReconciliationCase.deterministicId(assessment),
                assessment = assessment,
                openedAt = acceptedAt,
                observedAt = acceptedAt
            )

        val command =
            GovernedReconciliationCaseRevisionCommit.create(
                caseValue,
                accepted
            )

        val verified =
            FinancialReconciliationAssessmentSnapshotCodec.verify(
                command.assessmentSnapshot,
                accepted.assessmentFingerprint
            )

        assertEquals(assessment, verified.assessment)
        assertEquals(1L, command.caseValue.revision)
    }

    @Test
    fun `commit command rejects a case from another accepted assessment context`() {
        val accepted =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment(),
                acceptedAt
            )

        val foreignAssessment =
            assessment(
                organizationId =
                    OrganizationId.parse(
                        "90000000-0000-0000-0000-000000000001"
                    )
            )

        val foreignCase =
            DurableReconciliationCase.fromAssessment(
                caseId =
                    DurableReconciliationCase.deterministicId(
                        foreignAssessment
                    ),
                assessment = foreignAssessment,
                openedAt = acceptedAt,
                observedAt = acceptedAt
            )

        assertFailsWith<IllegalArgumentException> {
            GovernedReconciliationCaseRevisionCommit.create(
                foreignCase,
                accepted
            )
        }
    }

    @Test
    fun `commit command requires case observation time to be acceptedAt`() {
        val assessment = assessment()
        val accepted =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment,
                acceptedAt
            )

        val caseValue =
            DurableReconciliationCase.fromAssessment(
                caseId =
                    DurableReconciliationCase.deterministicId(
                        assessment
                    ),
                assessment = assessment,
                openedAt = acceptedAt,
                observedAt =
                    Instant.parse(
                        "2026-09-13T18:00:01.123456Z"
                    )
            )

        assertFailsWith<IllegalArgumentException> {
            GovernedReconciliationCaseRevisionCommit.create(
                caseValue,
                accepted
            )
        }
    }

    @Test
    fun `commit command rejects forged economic case projection`() {
        val assessment = assessment()
        val accepted =
            AcceptedFinancialReconciliationAssessment.accept(
                assessment,
                acceptedAt
            )

        val valid =
            DurableReconciliationCase.fromAssessment(
                caseId = DurableReconciliationCase.deterministicId(assessment),
                assessment = assessment,
                openedAt = acceptedAt,
                observedAt = acceptedAt
            )

        val forged =
            DurableReconciliationCase(
                caseId = valid.caseId,
                organizationId = valid.organizationId,
                orderId = valid.orderId,
                traceId = valid.traceId,
                policyVersion = valid.policyVersion,
                currency = valid.currency,
                status = valid.status,
                openedAt = valid.openedAt,
                lastObservedAt = valid.lastObservedAt,
                resolvedAt = valid.resolvedAt,
                revision = valid.revision,
                absoluteDifferenceSummary = money("999"),
                stages = valid.stages,
                evidenceEntryIds = valid.evidenceEntryIds
            )

        assertFailsWith<IllegalArgumentException> {
            GovernedReconciliationCaseRevisionCommit.create(
                forged,
                accepted
            )
        }
    }

    private fun assessment(
        organizationId: OrganizationId =
            OrganizationId.parse(
                "10000000-0000-0000-0000-000000000001"
            )
    ): FinancialReconciliationAssessment {
        val line =
            FinancialReconciliationLine(
                stage = FinancialLedgerStage.SALE,
                expected =
                    FinancialReconciliationSide.Observed(
                        money("100"),
                        listOf(
                            FinancialLedgerEntryId.parse(
                                "70000000-0000-0000-0000-000000000001"
                            )
                        )
                    ),
                actual =
                    FinancialReconciliationSide.Observed(
                        money("110"),
                        listOf(
                            FinancialLedgerEntryId.parse(
                                "70000000-0000-0000-0000-000000000002"
                            )
                        )
                    ),
                difference =
                    FinancialReconciliationDifference.Compared(
                        signedDifference = money("10"),
                        absoluteDifference = money("10"),
                        tolerance = money("0.01")
                    ),
                status = FinancialReconciliationStatus.DIVERGENCE
            )

        return FinancialReconciliationAssessment(
            organizationId = organizationId,
            traceId =
                FinancialTraceId.parse(
                    "20000000-0000-0000-0000-000000000001"
                ),
            orderId =
                MarketplaceOrderId.parse(
                    "30000000-0000-0000-0000-000000000001"
                ),
            currency = currency,
            policyVersion =
                FinancialReconciliationPolicyVersion(
                    "financial/1"
                ),
            lines = listOf(line),
            status = FinancialReconciliationStatus.DIVERGENCE
        )
    }

    private fun money(value: String): MarketplaceMoney =
        MarketplaceMoney.parse(currency, value)
}
