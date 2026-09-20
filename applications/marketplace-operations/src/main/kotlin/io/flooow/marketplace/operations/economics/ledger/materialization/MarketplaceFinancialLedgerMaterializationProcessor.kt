package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.evidence.ChangeSequenceCheckpoint
import io.flooow.marketplace.operations.economics.evidence.CheckpointAdvanceResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChange
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeed
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeedResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeKind
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceUpdateReadResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceUpdateReader
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceUpdate
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicFact
import io.flooow.marketplace.operations.economics.evidence.ProjectionName
import io.flooow.organization.OrganizationId

sealed interface MarketplaceFinancialLedgerMaterializationProcessorResult {
    data class Success(
        val processedChanges: Int,
        val materialized: Int,
        val alreadyMaterialized: Int,
        val notEligible: Int,
        val checkpoint: ChangeSequenceCheckpoint
    ) : MarketplaceFinancialLedgerMaterializationProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object NoChanges :
        MarketplaceFinancialLedgerMaterializationProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object CheckpointConflict :
        MarketplaceFinancialLedgerMaterializationProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object CommitConflict :
        MarketplaceFinancialLedgerMaterializationProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object Unavailable :
        MarketplaceFinancialLedgerMaterializationProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object UnsupportedCorrection :
        MarketplaceFinancialLedgerMaterializationProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object IntegrityFailure :
        MarketplaceFinancialLedgerMaterializationProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }
}

class MarketplaceFinancialLedgerMaterializationProcessor(
    private val updateReader: MarketplaceEconomicEvidenceUpdateReader,
    private val changeFeed: MarketplaceEconomicEvidenceChangeFeed,
    private val authorityResolver: (
        OrganizationId,
        MarketplaceEconomicComponentObservation
    ) -> FinancialLedgerComponentMaterializationAuthorityDecision,
    private val commitStore: GovernedFinancialLedgerMaterializationCommitStore
) {
    fun processBatch(
        organizationId: OrganizationId,
        limit: Int
    ): MarketplaceFinancialLedgerMaterializationProcessorResult {
        MarketplaceEconomicEvidenceChangeFeed.requireValidLimit(limit)

        val checkpoint =
            when (
                val result =
                    changeFeed.currentCheckpoint(
                        organizationId,
                        PROJECTION_NAME
                    )
            ) {
                is MarketplaceEconomicEvidenceChangeFeedResult.Success ->
                    result.value

                MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure ->
                    return MarketplaceFinancialLedgerMaterializationProcessorResult
                        .IntegrityFailure
            }

        val changes =
            when (
                val result =
                    changeFeed.changesSince(
                        organizationId,
                        checkpoint,
                        limit
                    )
            ) {
                is MarketplaceEconomicEvidenceChangeFeedResult.Success ->
                    result.value

                MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure ->
                    return MarketplaceFinancialLedgerMaterializationProcessorResult
                        .IntegrityFailure
            }

        if (changes.isEmpty()) {
            return MarketplaceFinancialLedgerMaterializationProcessorResult.NoChanges
        }

        if (!isValidBatch(organizationId, checkpoint, changes)) {
            return MarketplaceFinancialLedgerMaterializationProcessorResult
                .IntegrityFailure
        }

        if (
            changes.any {
                it.changeKind == MarketplaceEconomicEvidenceChangeKind.CORRECTION
            }
        ) {
            return MarketplaceFinancialLedgerMaterializationProcessorResult
                .UnsupportedCorrection
        }

        var materialized = 0
        var alreadyMaterialized = 0
        var notEligible = 0

        for (change in changes) {
            if (change.changeKind == MarketplaceEconomicEvidenceChangeKind.ATTEMPT) {
                continue
            }

            if (change.changeKind != MarketplaceEconomicEvidenceChangeKind.FACT) {
                return MarketplaceFinancialLedgerMaterializationProcessorResult
                    .IntegrityFailure
            }

            val update =
                when (
                    val read =
                        updateReader.findUpdate(
                            subject = change.subject,
                            evidenceVersion = change.evidenceVersion,
                            updateId = change.updateId,
                            changeKind = change.changeKind
                        )
                ) {
                    is MarketplaceEconomicEvidenceUpdateReadResult.Found ->
                        read.update

                    MarketplaceEconomicEvidenceUpdateReadResult.NotFound,
                    MarketplaceEconomicEvidenceUpdateReadResult.IntegrityFailure ->
                        return MarketplaceFinancialLedgerMaterializationProcessorResult
                            .IntegrityFailure
                }

            val observeFact =
                update as? MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact
                    ?: return MarketplaceFinancialLedgerMaterializationProcessorResult
                        .IntegrityFailure

            val fact = observeFact.fact

            if (
                fact.subject != change.subject ||
                fact.id != change.updateId
            ) {
                return MarketplaceFinancialLedgerMaterializationProcessorResult
                    .IntegrityFailure
            }

            val observation =
                when (fact) {
                    is MarketplaceIndependentEconomicFact.Component ->
                        fact.observation

                    is MarketplaceIndependentEconomicFact.ExternalIdentity,
                    is MarketplaceIndependentEconomicFact.OrderOccurrence ->
                        continue
                }

            val authorityDecision =
                authorityResolver(
                    organizationId,
                    observation
                )

            when (
                val boundary =
                    GovernedFinancialLedgerComponentMaterializationBoundary
                        .evaluate(
                            organizationId,
                            observation,
                            authorityDecision
                        )
            ) {
                is GovernedFinancialLedgerComponentMaterializationResult
                    .NotEligible -> {
                    notEligible++
                }

                is GovernedFinancialLedgerComponentMaterializationResult
                    .Failed.IntegrityFailure -> {
                    return MarketplaceFinancialLedgerMaterializationProcessorResult
                        .IntegrityFailure
                }

                GovernedFinancialLedgerComponentMaterializationResult
                    .Failed.Unavailable -> {
                    return MarketplaceFinancialLedgerMaterializationProcessorResult
                        .Unavailable
                }

                is GovernedFinancialLedgerComponentMaterializationResult
                    .Eligible -> {
                    when (val committed = commitStore.commit(boundary.plan)) {
                        is GovernedFinancialLedgerMaterializationCommitResult
                            .Materialized -> {
                            materialized++
                        }

                        is GovernedFinancialLedgerMaterializationCommitResult
                            .AlreadyMaterialized -> {
                            alreadyMaterialized++
                        }

                        is GovernedFinancialLedgerMaterializationCommitResult
                            .Failed -> {
                            return when (committed.failure) {
                                GovernedFinancialLedgerMaterializationCommitFailure
                                    .CONFLICT ->
                                    MarketplaceFinancialLedgerMaterializationProcessorResult
                                        .CommitConflict

                                GovernedFinancialLedgerMaterializationCommitFailure
                                    .UNAVAILABLE ->
                                    MarketplaceFinancialLedgerMaterializationProcessorResult
                                        .Unavailable

                                GovernedFinancialLedgerMaterializationCommitFailure
                                    .INTEGRITY_FAILURE ->
                                    MarketplaceFinancialLedgerMaterializationProcessorResult
                                        .IntegrityFailure
                            }
                        }
                    }
                }
            }
        }

        val destination = changes.last().changeSequence

        return when (
            val advance =
                changeFeed.advanceCheckpoint(
                    organizationId,
                    PROJECTION_NAME,
                    checkpoint,
                    destination
                )
        ) {
            MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure ->
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .IntegrityFailure

            is MarketplaceEconomicEvidenceChangeFeedResult.Success ->
                when (val value = advance.value) {
                    is CheckpointAdvanceResult.Advanced ->
                        MarketplaceFinancialLedgerMaterializationProcessorResult.Success(
                            processedChanges = changes.size,
                            materialized = materialized,
                            alreadyMaterialized = alreadyMaterialized,
                            notEligible = notEligible,
                            checkpoint = value.checkpoint
                        )

                    is CheckpointAdvanceResult.Stale ->
                        if (value.currentCheckpoint >= destination) {
                            MarketplaceFinancialLedgerMaterializationProcessorResult.Success(
                                processedChanges = changes.size,
                                materialized = materialized,
                                alreadyMaterialized = alreadyMaterialized,
                                notEligible = notEligible,
                                checkpoint = value.currentCheckpoint
                            )
                        } else {
                            MarketplaceFinancialLedgerMaterializationProcessorResult
                                .CheckpointConflict
                        }

                    CheckpointAdvanceResult.Regression ->
                        MarketplaceFinancialLedgerMaterializationProcessorResult
                            .IntegrityFailure
                }
        }
    }

    private fun isValidBatch(
        organizationId: OrganizationId,
        checkpoint: ChangeSequenceCheckpoint,
        changes: List<MarketplaceEconomicEvidenceChange>
    ): Boolean {
        var previous = checkpoint

        for (change in changes) {
            if (
                change.subject.organizationId != organizationId ||
                change.changeSequence <= previous
            ) {
                return false
            }

            previous = change.changeSequence
        }

        return true
    }

    companion object {
        val PROJECTION_NAME: ProjectionName =
            ProjectionName("financial-ledger-materialization")
    }
}