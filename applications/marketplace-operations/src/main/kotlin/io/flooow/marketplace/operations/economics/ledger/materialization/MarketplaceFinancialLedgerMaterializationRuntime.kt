package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeed
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeedResult
import io.flooow.organization.OrganizationId

enum class MarketplaceFinancialLedgerMaterializationRuntimeBlockReason {
    CHECKPOINT_CONFLICT,
    COMMIT_CONFLICT,
    AUTHORITY_OR_PERSISTENCE_UNAVAILABLE,
    UNSUPPORTED_CORRECTION,
    INTEGRITY_FAILURE
}

sealed interface MarketplaceFinancialLedgerMaterializationRuntimeResult {
    data class Success(
        val organizationsDiscovered: Int,
        val organizationsProcessed: Int,
        val processedChanges: Int,
        val materialized: Int,
        val alreadyMaterialized: Int,
        val notEligible: Int
    ) : MarketplaceFinancialLedgerMaterializationRuntimeResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object NoPendingOrganizations :
        MarketplaceFinancialLedgerMaterializationRuntimeResult {
        override fun toString(): String = "[REDACTED]"
    }

    data class Blocked(
        val organizationId: OrganizationId,
        val reason: MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
    ) : MarketplaceFinancialLedgerMaterializationRuntimeResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object IntegrityFailure :
        MarketplaceFinancialLedgerMaterializationRuntimeResult {
        override fun toString(): String = "[REDACTED]"
    }
}

class MarketplaceFinancialLedgerMaterializationRuntime(
    private val changeFeed: MarketplaceEconomicEvidenceChangeFeed,
    private val processBatch: (
        organizationId: OrganizationId,
        limit: Int
    ) -> MarketplaceFinancialLedgerMaterializationProcessorResult
) {
    fun dispatchOnce(
        organizationLimit: Int,
        batchLimit: Int
    ): MarketplaceFinancialLedgerMaterializationRuntimeResult {
        require(organizationLimit in 1..1_000) {
            "Materialization runtime organization limit must be from 1 through 1000"
        }

        MarketplaceEconomicEvidenceChangeFeed.requireValidLimit(batchLimit)

        val organizations =
            when (
                val result =
                    changeFeed.organizationsWithPendingChanges(
                        MarketplaceFinancialLedgerMaterializationProcessor.PROJECTION_NAME,
                        organizationLimit
                    )
            ) {
                is MarketplaceEconomicEvidenceChangeFeedResult.Success ->
                    result.value

                MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure ->
                    return MarketplaceFinancialLedgerMaterializationRuntimeResult
                        .IntegrityFailure
            }

        if (organizations.isEmpty()) {
            return MarketplaceFinancialLedgerMaterializationRuntimeResult
                .NoPendingOrganizations
        }

        var organizationsProcessed = 0
        var processedChanges = 0
        var materialized = 0
        var alreadyMaterialized = 0
        var notEligible = 0

        for (organizationId in organizations) {
            when (
                val result =
                    processBatch(
                        organizationId,
                        batchLimit
                    )
            ) {
                is MarketplaceFinancialLedgerMaterializationProcessorResult.Success -> {
                    organizationsProcessed++
                    processedChanges += result.processedChanges
                    materialized += result.materialized
                    alreadyMaterialized += result.alreadyMaterialized
                    notEligible += result.notEligible
                }

                MarketplaceFinancialLedgerMaterializationProcessorResult.NoChanges -> {
                    /*
                     * Discovery is advisory and may race with another worker.
                     * NoChanges is therefore a safe terminal outcome for this
                     * organization during this dispatch.
                     */
                    organizationsProcessed++
                }

                MarketplaceFinancialLedgerMaterializationProcessorResult.CheckpointConflict ->
                    return blocked(
                        organizationId,
                        MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                            .CHECKPOINT_CONFLICT
                    )

                MarketplaceFinancialLedgerMaterializationProcessorResult.CommitConflict ->
                    return blocked(
                        organizationId,
                        MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                            .COMMIT_CONFLICT
                    )

                MarketplaceFinancialLedgerMaterializationProcessorResult.Unavailable ->
                    return blocked(
                        organizationId,
                        MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                            .AUTHORITY_OR_PERSISTENCE_UNAVAILABLE
                    )

                MarketplaceFinancialLedgerMaterializationProcessorResult.UnsupportedCorrection ->
                    return blocked(
                        organizationId,
                        MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                            .UNSUPPORTED_CORRECTION
                    )

                MarketplaceFinancialLedgerMaterializationProcessorResult.IntegrityFailure ->
                    return blocked(
                        organizationId,
                        MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                            .INTEGRITY_FAILURE
                    )
            }
        }

        return MarketplaceFinancialLedgerMaterializationRuntimeResult.Success(
            organizationsDiscovered = organizations.size,
            organizationsProcessed = organizationsProcessed,
            processedChanges = processedChanges,
            materialized = materialized,
            alreadyMaterialized = alreadyMaterialized,
            notEligible = notEligible
        )
    }

    private fun blocked(
        organizationId: OrganizationId,
        reason: MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
    ): MarketplaceFinancialLedgerMaterializationRuntimeResult =
        MarketplaceFinancialLedgerMaterializationRuntimeResult.Blocked(
            organizationId = organizationId,
            reason = reason
        )
}