package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId

/**
 * Durable commit boundary downstream from the verified B3-A plan.
 *
 * Input intentionally contains no caller-selected trace id, ledger entry id,
 * open request id or append request id.
 *
 * A persistence implementation must atomically:
 *
 * 1. ensure or validate the subject FinancialTrace;
 * 2. append the exact verified financial fact;
 * 3. persist immutable source-to-entry lineage.
 *
 * No successful result may escape without all three durable facts.
 */
fun interface GovernedFinancialLedgerMaterializationCommitStore {
    fun commit(
        plan: VerifiedFinancialLedgerComponentMaterializationPlan
    ): GovernedFinancialLedgerMaterializationCommitResult
}

enum class GovernedFinancialLedgerMaterializationCommitFailure {
    CONFLICT,
    INTEGRITY_FAILURE,
    UNAVAILABLE
}

sealed interface GovernedFinancialLedgerMaterializationCommitResult {
    class Materialized(
        val traceId: FinancialTraceId,
        val entryId: FinancialLedgerEntryId
    ) : GovernedFinancialLedgerMaterializationCommitResult {
        override fun toString(): String = "[REDACTED]"
    }

    class AlreadyMaterialized(
        val traceId: FinancialTraceId,
        val entryId: FinancialLedgerEntryId
    ) : GovernedFinancialLedgerMaterializationCommitResult {
        override fun toString(): String = "[REDACTED]"
    }

    class Failed(
        val failure: GovernedFinancialLedgerMaterializationCommitFailure
    ) : GovernedFinancialLedgerMaterializationCommitResult {
        override fun toString(): String = "[REDACTED]"
    }
}
