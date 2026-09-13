package io.flooow.marketplace.operations.economics.reconciliation

import java.util.Collections

enum class EconomicLeakageGovernanceBlockingReason {
    IDENTITY_UNRESOLVED,
    CURRENCY_UNRESOLVED,
    ALLOCATION_UNRESOLVED,
    EVIDENCE_CURRENTNESS_UNRESOLVED,
    CONTRADICTORY_AUTHORITY,
    STALE_AUTHORITY
}

class EconomicLeakageGovernance private constructor(
    blockingReasons: Collection<EconomicLeakageGovernanceBlockingReason>,
    evidenceReferences: Collection<String>
) {
    val blockingReasons: Set<EconomicLeakageGovernanceBlockingReason> =
        Collections.unmodifiableSet(linkedSetOf<EconomicLeakageGovernanceBlockingReason>().apply {
            addAll(blockingReasons)
        })

    val evidenceReferences: Set<String> =
        Collections.unmodifiableSet(linkedSetOf<String>().apply {
            addAll(evidenceReferences)
        })

    val permitted: Boolean
        get() = blockingReasons.isEmpty()

    init {
        require(evidenceReferences.all { it.isNotBlank() && it == it.trim() }) {
            "Leakage governance evidence references must be non-blank canonical text"
        }
    }

    override fun toString(): String = "[REDACTED]"

    companion object {
        fun permitted(
            evidenceReferences: Collection<String> = emptySet()
        ): EconomicLeakageGovernance =
            EconomicLeakageGovernance(
                blockingReasons = emptySet(),
                evidenceReferences = evidenceReferences
            )

        fun blocked(
            blockingReasons: Collection<EconomicLeakageGovernanceBlockingReason>,
            evidenceReferences: Collection<String> = emptySet()
        ): EconomicLeakageGovernance {
            require(blockingReasons.isNotEmpty()) {
                "Blocked leakage governance requires at least one blocking reason"
            }

            return EconomicLeakageGovernance(
                blockingReasons = blockingReasons,
                evidenceReferences = evidenceReferences
            )
        }
    }
}