package io.flooow.marketplace.operations.economics.sales

import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssembler
import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssemblyResult
import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthCalculator
import io.flooow.marketplace.operations.economics.MarketplaceOrder
import io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthCalculationResult
import io.flooow.marketplace.operations.economics.evidence.ChangeSequenceCheckpoint
import io.flooow.marketplace.operations.economics.evidence.CheckpointAdvanceResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChange
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeed
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeedResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceReadResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceRepository
import io.flooow.marketplace.operations.economics.evidence.ProjectionName
import io.flooow.organization.OrganizationId
import java.time.Clock
import java.time.temporal.ChronoUnit

sealed interface MarketplaceSalesIntelligenceProjectionProcessorResult {
    data class Success(
        val processedChanges: Int,
        val checkpoint: ChangeSequenceCheckpoint
    ) : MarketplaceSalesIntelligenceProjectionProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object NoChanges : MarketplaceSalesIntelligenceProjectionProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object CheckpointConflict : MarketplaceSalesIntelligenceProjectionProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object ReconciliationRequired : MarketplaceSalesIntelligenceProjectionProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object IntegrityFailure : MarketplaceSalesIntelligenceProjectionProcessorResult {
        override fun toString(): String = "[REDACTED]"
    }
}

class MarketplaceSalesIntelligenceProjectionProcessor(
    private val evidenceRepository: MarketplaceIndependentEconomicEvidenceRepository,
    private val changeFeed: MarketplaceEconomicEvidenceChangeFeed,
    private val projection: MarketplaceSalesIntelligenceProjection,
    private val clock: Clock = Clock.systemUTC(),
    private val calculator: (MarketplaceOrder) -> MarketplaceEconomicTruthCalculationResult = {
        order -> MarketplaceEconomicTruthCalculator.calculate(order)
    },
    internal val snapshotObserver: (ConsumedEconomicEvidenceSnapshot) -> Unit = {},
    private val historyPublication: MarketplaceSalesIntelligenceHistoryPublication? = null
) {
    @Synchronized
    fun processBatch(
        organizationId: OrganizationId,
        limit: Int
    ): MarketplaceSalesIntelligenceProjectionProcessorResult {
        MarketplaceEconomicEvidenceChangeFeed.requireValidLimit(limit)

        val checkpoint = when (
            val result = changeFeed.currentCheckpoint(organizationId, PROJECTION_NAME)
        ) {
            is MarketplaceEconomicEvidenceChangeFeedResult.Success -> result.value
            MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure ->
                return MarketplaceSalesIntelligenceProjectionProcessorResult.IntegrityFailure
        }

        val uncertain = pending
        if (historyPublication != null && uncertain != null && uncertain.first.subject.organizationId == organizationId &&
            checkpoint >= uncertain.first.triggerChangeSequence) {
            val resolution = try { historyPublication.reconcile(checkNotNull(pendingChange), uncertain.first) }
                catch (_: Exception) { return MarketplaceSalesIntelligenceProjectionProcessorResult.ReconciliationRequired }
            when (resolution) {
                is EconomicLineageReconciliationResult.Known -> { pending = null; pendingChange = null; reconciliationRequired = false }
                else -> return MarketplaceSalesIntelligenceProjectionProcessorResult.ReconciliationRequired
            }
        }

        val changes = when (
            val result = changeFeed.changesSince(organizationId, checkpoint, limit)
        ) {
            is MarketplaceEconomicEvidenceChangeFeedResult.Success -> result.value
            MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure ->
                return MarketplaceSalesIntelligenceProjectionProcessorResult.IntegrityFailure
        }

        if (changes.isEmpty()) {
            return MarketplaceSalesIntelligenceProjectionProcessorResult.NoChanges
        }
        if (!isValidBatch(organizationId, checkpoint, changes)) {
            return MarketplaceSalesIntelligenceProjectionProcessorResult.IntegrityFailure
        }

        for (change in changes) {
            when (materializeChange(organizationId, change)) {
                MaterializeOutcome.Complete -> Unit
                MaterializeOutcome.Failure ->
                    return if (reconciliationRequired) MarketplaceSalesIntelligenceProjectionProcessorResult.ReconciliationRequired
                    else MarketplaceSalesIntelligenceProjectionProcessorResult.IntegrityFailure
            }
        }

        val destination = changes.last().changeSequence
        return when (
            val advance = changeFeed.advanceCheckpoint(
                organizationId,
                PROJECTION_NAME,
                checkpoint,
                destination
            )
        ) {
            MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure ->
                MarketplaceSalesIntelligenceProjectionProcessorResult.IntegrityFailure

            is MarketplaceEconomicEvidenceChangeFeedResult.Success -> when (val value = advance.value) {
                is CheckpointAdvanceResult.Advanced ->
                    MarketplaceSalesIntelligenceProjectionProcessorResult.Success(
                        changes.size,
                        value.checkpoint
                    )

                is CheckpointAdvanceResult.Stale ->
                    if (value.currentCheckpoint >= destination) {
                        MarketplaceSalesIntelligenceProjectionProcessorResult.Success(
                            changes.size,
                            value.currentCheckpoint
                        )
                    } else {
                        MarketplaceSalesIntelligenceProjectionProcessorResult.CheckpointConflict
                    }

                CheckpointAdvanceResult.Regression ->
                    MarketplaceSalesIntelligenceProjectionProcessorResult.IntegrityFailure
            }
        }
    }

    private fun materializeChange(
        organizationId: OrganizationId,
        change: MarketplaceEconomicEvidenceChange
    ): MaterializeOutcome {
        if (historyPublication != null) return materializeHistorical(change)
        val current = when (
            val result = projection.currentBySubject(organizationId, change.subject.orderId)
        ) {
            is MarketplaceSalesIntelligenceProjectionReadResult.Success -> result.value
            MarketplaceSalesIntelligenceProjectionReadResult.IntegrityFailure ->
                return MaterializeOutcome.Failure
        }

        if (current != null && (current.organizationId != organizationId || current.marketplaceOrderId != change.subject.orderId))
            return MaterializeOutcome.Failure
        if (current != null &&
            current.lastAppliedChangeSequence >= change.changeSequence
        ) {
            return MaterializeOutcome.Complete
        }

        val versionedEvidence = when (val result = evidenceRepository.find(change.subject)) {
            is MarketplaceIndependentEconomicEvidenceReadResult.Found -> result.versionedEvidence
            MarketplaceIndependentEconomicEvidenceReadResult.NotFound,
            MarketplaceIndependentEconomicEvidenceReadResult.IntegrityFailure ->
                return MaterializeOutcome.Failure
        }

        if (versionedEvidence.evidence.subject != change.subject ||
            versionedEvidence.version < change.evidenceVersion ||
            (current != null && versionedEvidence.version < current.sourceEvidenceVersion)) return MaterializeOutcome.Failure
        val snapshotInput = try {
            ConsumedEconomicEvidenceSnapshot.capture(versionedEvidence, change.changeSequence)
        } catch (_: IllegalArgumentException) { return MaterializeOutcome.Failure }
        val assembly = MarketplaceEconomicTruthAssembler.assemble(versionedEvidence.evidence)
        val state = when (assembly) {
            is MarketplaceEconomicTruthAssemblyResult.NotReady ->
                MarketplaceSalesIntelligenceState.Unresolved(
                    assemblyPolicyVersion = assembly.assemblyPolicyVersion,
                    reasons = assembly.reasons
                )

            is MarketplaceEconomicTruthAssemblyResult.Ready -> {
                val calculation = calculator(assembly.order)
                MarketplaceSalesIntelligenceState.Calculated(
                    assemblyPolicyVersion = assembly.assemblyPolicyVersion,
                    calculationPolicyVersion = calculationPolicyVersionOf(calculation),
                    calculationResult = calculation
                )
            }
        }

        val record = MarketplaceSalesIntelligenceProjectionRecord(
            organizationId = organizationId,
            marketplaceOrderId = change.subject.orderId,
            sourceEvidenceVersion = versionedEvidence.version,
            state = state,
            lastAppliedChangeSequence = change.changeSequence,
            projectedAt = clock.instant().truncatedTo(ChronoUnit.MICROS)
        )

        val snapshot = try {
            snapshotInput.finalize(assembly, state, record.projectedAt)
        } catch (_: IllegalArgumentException) { return MaterializeOutcome.Failure }
        snapshotObserver(snapshot)
        return when (projection.materializeIfNewer(record)) {
            MarketplaceSalesIntelligenceProjectionWriteResult.Applied,
            MarketplaceSalesIntelligenceProjectionWriteResult.NoOpAlreadyCurrent ->
                MaterializeOutcome.Complete
            MarketplaceSalesIntelligenceProjectionWriteResult.IntegrityFailure ->
                MaterializeOutcome.Failure
        }
    }

    private var pending: Pair<ConsumedEconomicEvidenceSnapshot, MarketplaceSalesIntelligenceProjectionRecord>? = null
    private var pendingChange: MarketplaceEconomicEvidenceChange? = null
    internal var reconciliationRequired: Boolean = false
        private set

    private fun materializeHistorical(change: MarketplaceEconomicEvidenceChange): MaterializeOutcome {
        val port = checkNotNull(historyPublication)
        try {
            val frozen = pending?.takeIf { it.first.subject == change.subject && it.first.triggerChangeSequence == change.changeSequence }
            when (val resolution = port.reconcile(change, frozen?.first)) {
                is EconomicLineageReconciliationResult.Known -> { if (frozen != null) { pending = null; pendingChange = null }; pendingChange = null; reconciliationRequired = false; return MaterializeOutcome.Complete }
                EconomicLineageReconciliationResult.IntegrityFailure -> return MaterializeOutcome.Failure
                EconomicLineageReconciliationResult.Absent -> Unit
            }
            // Do not skip an unresolved pending input from a different subject/trigger.
            if (pending != null && frozen == null) return MaterializeOutcome.Failure
            val pair = frozen ?: run {
                val evidence = (evidenceRepository.find(change.subject) as? MarketplaceIndependentEconomicEvidenceReadResult.Found)?.versionedEvidence
                    ?: return MaterializeOutcome.Failure
                if (evidence.evidence.subject != change.subject || evidence.version < change.evidenceVersion) return MaterializeOutcome.Failure
                val input = ConsumedEconomicEvidenceSnapshot.capture(evidence, change.changeSequence)
                val assembly = MarketplaceEconomicTruthAssembler.assemble(evidence.evidence)
                val state = when (assembly) {
                    is MarketplaceEconomicTruthAssemblyResult.NotReady -> MarketplaceSalesIntelligenceState.Unresolved(assembly.assemblyPolicyVersion, assembly.reasons)
                    is MarketplaceEconomicTruthAssemblyResult.Ready -> {
                        val calculation = calculator(assembly.order)
                        MarketplaceSalesIntelligenceState.Calculated(assembly.assemblyPolicyVersion, calculationPolicyVersionOf(calculation), calculation)
                    }
                }
                val record = MarketplaceSalesIntelligenceProjectionRecord(change.subject.organizationId, change.subject.orderId,
                    evidence.version, state, change.changeSequence, clock.instant().truncatedTo(ChronoUnit.MICROS))
                val snapshot = input.finalize(assembly, state, record.projectedAt)
                snapshotObserver(snapshot)
                snapshot to record
            }
            pending = pair
            pendingChange = change
            reconciliationRequired = true // An exception after submission cannot establish rollback.
            return when (val result = port.publish(pair.first, pair.second)) {
                is EconomicLineagePublicationResult.Published, is EconomicLineagePublicationResult.IdenticalPublished -> { pending = null; pendingChange = null; reconciliationRequired = false; MaterializeOutcome.Complete }
                is EconomicLineagePublicationResult.Superseded -> {
                    reconciliationRequired = false
                    if (result.currentRevisionId != null && port.reconcile(change, pair.first) is EconomicLineageReconciliationResult.Known) {
                        pending = null; pendingChange = null; reconciliationRequired = false; MaterializeOutcome.Complete
                    } else MaterializeOutcome.Failure
                }
                EconomicLineagePublicationResult.CommitOutcomeUnknown -> { pending = pair; reconciliationRequired = true; MaterializeOutcome.Failure }
                EconomicLineagePublicationResult.IntegrityFailure -> { pending = null; pendingChange = null; reconciliationRequired = false; MaterializeOutcome.Failure }
            }
        } catch (_: Exception) { return MaterializeOutcome.Failure }
    }

    private fun isValidBatch(
        organizationId: OrganizationId,
        checkpoint: ChangeSequenceCheckpoint,
        changes: List<MarketplaceEconomicEvidenceChange>
    ): Boolean {
        var previous = checkpoint
        for (change in changes) {
            if (change.subject.organizationId != organizationId ||
                change.changeSequence <= previous
            ) {
                return false
            }
            previous = change.changeSequence
        }
        return true
    }

    private enum class MaterializeOutcome {
        Complete,
        Failure
    }

    companion object {
        fun historical(
            evidenceRepository: MarketplaceIndependentEconomicEvidenceRepository,
            changeFeed: MarketplaceEconomicEvidenceChangeFeed,
            publication: MarketplaceSalesIntelligenceHistoryPublication,
            clock: Clock = Clock.systemUTC()
        ): MarketplaceSalesIntelligenceProjectionProcessor = MarketplaceSalesIntelligenceProjectionProcessor(
            evidenceRepository, changeFeed, object: MarketplaceSalesIntelligenceProjection {
                override fun currentBySubject(organizationId: OrganizationId, marketplaceOrderId: io.flooow.marketplace.operations.economics.MarketplaceOrderId) = error("legacy path forbidden")
                override fun materializeIfNewer(record: MarketplaceSalesIntelligenceProjectionRecord) = error("legacy path forbidden")
                override fun listByOrganization(organizationId: OrganizationId, cursor: MarketplaceSalesIntelligenceProjectionCursor?, limit: Int) = error("legacy path forbidden")
                override fun detailByOrganizationAndSubject(organizationId: OrganizationId, marketplaceOrderId: io.flooow.marketplace.operations.economics.MarketplaceOrderId) = error("legacy path forbidden")
            }, clock, historyPublication = publication)

        val PROJECTION_NAME: ProjectionName = ProjectionName("sales-intelligence")
    }
}
