package io.flooow.marketplace.operations.economics.promotion

import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceVersion
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidence
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidencePersistResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceReadResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceRepository
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceUpdate
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicFact
import io.flooow.marketplace.operations.economics.evidence.VersionedMarketplaceIndependentEconomicEvidence
import io.flooow.organization.OrganizationId
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.UUID
import java.util.concurrent.atomic.AtomicInteger
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class MarketplaceOrderSourcePromotionTest {
    private val now = Instant.parse("2026-09-06T22:00:00.123456Z")
    private val occurredAt = Instant.parse("2026-09-06T20:00:00.000000Z")
    private val clock = Clock.fixed(now, ZoneOffset.UTC)
    private val organization = OrganizationId(uuid(1))
    private val connection = IntegrationConnectionId(uuid(2))
    private val orderId = MarketplaceOrderId(uuid(100))

    @Test
    fun `service builds exact marketplace occurrence source and preserves source clocks`() {
        val candidate = candidate()
        val source = ScriptedSourceRepository(
            listOf(candidate),
            identity = MarketplaceOrderIdentityResolution.Resolved(orderId, true)
        )
        val evidence = ScriptedEvidenceRepository(
            mutableListOf(ApplyStep.Applied)
        )

        val service = service(source, evidence)
        val result = assertIs<MarketplaceOrderSourcePromotionBatchResult.Completed>(
            service.promotePending(organization, connection, 10)
        )

        assertEquals(1, result.promoted)
        assertEquals(0, result.duplicates)
        assertEquals(
            MarketplaceOrderOccurrencePromotionOutcome.PROMOTED,
            source.terminalOutcome
        )

        val update = assertIs<MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact>(
            evidence.lastUpdate
        )
        val fact = assertIs<MarketplaceIndependentEconomicFact.OrderOccurrence>(
            update.fact
        )
        val observation = fact.observation

        assertEquals(
            MarketplaceOrderSourcePromotionContract.MARKETPLACE,
            observation.subject.marketplace
        )
        assertEquals(candidate.externalOrderId, observation.subject.externalOrderId)
        assertEquals(candidate.currency, observation.subject.currency)
        assertEquals(orderId, observation.subject.orderId)
        assertEquals(EconomicSourceKind.MARKETPLACE, observation.source.kind)
        assertEquals(
            MarketplaceOrderSourcePromotionContract.SOURCE_SYSTEM_KEY,
            observation.source.systemKey
        )
        val external = assertIs<EconomicExternalReferenceState.Present>(
            observation.source.externalReference
        )
        assertEquals(candidate.externalOrderId.value, external.reference.value)
        assertEquals(candidate.dateCreated, observation.occurredAt)
        assertEquals(candidate.observedAt, observation.observedAt)
    }

    @Test
    fun `duplicate evidence becomes durable duplicate terminal outcome`() {
        val candidate = candidate()
        val source = ScriptedSourceRepository(
            listOf(candidate),
            identity = MarketplaceOrderIdentityResolution.Resolved(orderId, false)
        )
        val evidence = ScriptedEvidenceRepository(
            mutableListOf(ApplyStep.Duplicate)
        )

        val result = assertIs<MarketplaceOrderSourcePromotionBatchResult.Completed>(
            service(source, evidence).promotePending(organization, connection, 10)
        )

        assertEquals(1, result.duplicates)
        assertEquals(
            MarketplaceOrderOccurrencePromotionOutcome.DUPLICATE,
            source.terminalOutcome
        )
    }

    @Test
    fun `source fact conflict is terminal evidence conflict and never correction`() {
        val candidate = candidate()
        val source = ScriptedSourceRepository(
            listOf(candidate),
            identity = MarketplaceOrderIdentityResolution.Resolved(orderId, false)
        )
        val evidence = ScriptedEvidenceRepository(
            mutableListOf(ApplyStep.SourceConflict)
        )

        val result = assertIs<MarketplaceOrderSourcePromotionBatchResult.Completed>(
            service(source, evidence).promotePending(organization, connection, 10)
        )

        assertEquals(1, result.evidenceConflicts)
        assertEquals(
            MarketplaceOrderOccurrencePromotionOutcome.EVIDENCE_CONFLICT,
            source.terminalOutcome
        )
        assertTrue(
            evidence.lastUpdate is MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact
        )
    }

    @Test
    fun `stale evidence version retries at most three cycles and converges`() {
        val candidate = candidate()
        val source = ScriptedSourceRepository(
            listOf(candidate),
            identity = MarketplaceOrderIdentityResolution.Resolved(orderId, true)
        )
        val evidence = ScriptedEvidenceRepository(
            mutableListOf(
                ApplyStep.Stale,
                ApplyStep.Stale,
                ApplyStep.Applied
            )
        )

        val result = assertIs<MarketplaceOrderSourcePromotionBatchResult.Completed>(
            service(source, evidence).promotePending(organization, connection, 10)
        )

        assertEquals(1, result.promoted)
        assertEquals(3, evidence.applyCalls.get())
        assertEquals(3, evidence.findCalls.get())
    }

    @Test
    fun `identity conflict is terminal without touching economic evidence`() {
        val candidate = candidate(currency = "USD")
        val source = ScriptedSourceRepository(
            listOf(candidate),
            identity = MarketplaceOrderIdentityResolution.Conflict(orderId)
        )
        val evidence = ScriptedEvidenceRepository(mutableListOf())

        val result = assertIs<MarketplaceOrderSourcePromotionBatchResult.Completed>(
            service(source, evidence).promotePending(organization, connection, 10)
        )

        assertEquals(1, result.identityConflicts)
        assertEquals(0, evidence.findCalls.get())
        assertEquals(0, evidence.applyCalls.get())
        assertEquals(
            MarketplaceOrderOccurrencePromotionOutcome.IDENTITY_CONFLICT,
            source.terminalOutcome
        )
    }

    @Test
    fun `evidence integrity failure blocks without terminal business marker`() {
        val candidate = candidate()
        val source = ScriptedSourceRepository(
            listOf(candidate),
            identity = MarketplaceOrderIdentityResolution.Resolved(orderId, true)
        )
        val evidence = ScriptedEvidenceRepository(
            mutableListOf(),
            failFind = true
        )

        val result = assertIs<MarketplaceOrderSourcePromotionBatchResult.Blocked>(
            service(source, evidence).promotePending(organization, connection, 10)
        )

        assertEquals(
            MarketplaceOrderSourcePromotionBlockReason.INTEGRITY_FAILURE,
            result.reason
        )
        assertNull(source.terminalOutcome)
    }

    @Test
    fun `terminal write conflict blocks instead of overwriting prior meaning`() {
        val candidate = candidate()
        val source = ScriptedSourceRepository(
            listOf(candidate),
            identity = MarketplaceOrderIdentityResolution.Resolved(orderId, true),
            terminalWrite = MarketplaceOrderOccurrencePromotionWriteResult.CONFLICT
        )
        val evidence = ScriptedEvidenceRepository(
            mutableListOf(ApplyStep.Applied)
        )

        val result = assertIs<MarketplaceOrderSourcePromotionBatchResult.Blocked>(
            service(source, evidence).promotePending(organization, connection, 10)
        )

        assertEquals(
            MarketplaceOrderSourcePromotionBlockReason.TERMINAL_CONFLICT,
            result.reason
        )
    }

    private fun service(
        source: MarketplaceOrderSourcePromotionRepository,
        evidence: MarketplaceIndependentEconomicEvidenceRepository
    ) = MarketplaceOrderSourcePromotionService(
        sourceRepository = source,
        evidenceRepository = evidence,
        clock = clock,
        orderIds = MarketplaceOrderPromotionIdentifierFactory { orderId },
        observationIds = observationFactory()
    )

    private fun candidate(
        currency: String = "BRL"
    ) = MarketplaceOrderSourcePromotionCandidate(
        sourceKey = MarketplaceOrderSourceKey(
            organizationId = organization,
            connectionId = connection,
            capability = MarketplaceOrderSourcePromotionContract.CAPABILITY,
            inputProgressVersion = 7,
            recordOrdinal = 0
        ),
        externalOrderId = MarketplaceExternalOrderId("200000000001"),
        currency = MarketplaceCurrency(currency),
        dateCreated = occurredAt,
        observedAt = now
    )

    private fun observationFactory():
        MarketplaceOrderPromotionIdentifierFactory<MarketplaceEconomicEvidenceObservationId> {
        val sequence = AtomicInteger(1)
        return MarketplaceOrderPromotionIdentifierFactory {
            MarketplaceEconomicEvidenceObservationId.parse(
                uuid(200 + sequence.getAndIncrement().toLong()).toString()
            )
        }
    }

    private fun uuid(value: Long): UUID = UUID(0, value)
}

private class ScriptedSourceRepository(
    private val candidates: List<MarketplaceOrderSourcePromotionCandidate>,
    private val identity: MarketplaceOrderIdentityResolution,
    private val terminalWrite: MarketplaceOrderOccurrencePromotionWriteResult =
        MarketplaceOrderOccurrencePromotionWriteResult.APPLIED
) : MarketplaceOrderSourcePromotionRepository {
    var terminalOutcome: MarketplaceOrderOccurrencePromotionOutcome? = null
        private set

    override fun pending(
        organizationId: OrganizationId,
        connectionId: IntegrationConnectionId,
        limit: Int
    ): MarketplaceOrderSourcePendingResult =
        MarketplaceOrderSourcePendingResult.Available(
            candidates.filter {
                it.sourceKey.organizationId == organizationId &&
                    it.sourceKey.connectionId == connectionId
            }.take(limit)
        )

    override fun resolveOrAllocate(
        candidate: MarketplaceOrderSourcePromotionCandidate,
        proposedOrderId: MarketplaceOrderId,
        allocatedAt: Instant
    ): MarketplaceOrderIdentityResolution = identity

    override fun markTerminal(
        candidate: MarketplaceOrderSourcePromotionCandidate,
        orderId: MarketplaceOrderId,
        outcome: MarketplaceOrderOccurrencePromotionOutcome,
        promotedAt: Instant
    ): MarketplaceOrderOccurrencePromotionWriteResult {
        if (
            terminalWrite == MarketplaceOrderOccurrencePromotionWriteResult.APPLIED ||
            terminalWrite == MarketplaceOrderOccurrencePromotionWriteResult.ALREADY_APPLIED
        ) {
            terminalOutcome = outcome
        }
        return terminalWrite
    }
}

private enum class ApplyStep {
    Applied,
    Duplicate,
    Stale,
    SourceConflict
}

private class ScriptedEvidenceRepository(
    private val steps: MutableList<ApplyStep>,
    private val failFind: Boolean = false
) : MarketplaceIndependentEconomicEvidenceRepository {
    val findCalls = AtomicInteger()
    val applyCalls = AtomicInteger()
    var lastUpdate: MarketplaceIndependentEconomicEvidenceUpdate? = null
        private set

    override fun find(
        subject: MarketplaceEconomicEvidenceSubject
    ): MarketplaceIndependentEconomicEvidenceReadResult {
        findCalls.incrementAndGet()
        return if (failFind) {
            MarketplaceIndependentEconomicEvidenceReadResult.IntegrityFailure
        } else {
            MarketplaceIndependentEconomicEvidenceReadResult.NotFound
        }
    }

    override fun apply(
        expectedVersion: MarketplaceEconomicEvidenceVersion,
        update: MarketplaceIndependentEconomicEvidenceUpdate
    ): MarketplaceIndependentEconomicEvidencePersistResult {
        applyCalls.incrementAndGet()
        lastUpdate = update
        val step = if (steps.isEmpty()) {
            error("No scripted evidence apply result")
        } else {
            steps.removeAt(0)
        }

        return when (step) {
            ApplyStep.Applied ->
                MarketplaceIndependentEconomicEvidencePersistResult.Applied(
                    versioned(update.subject, MarketplaceEconomicEvidenceVersion.ZERO.next())
                )

            ApplyStep.Duplicate ->
                MarketplaceIndependentEconomicEvidencePersistResult.Duplicate(
                    versioned(update.subject, MarketplaceEconomicEvidenceVersion.ZERO)
                )

            ApplyStep.Stale ->
                MarketplaceIndependentEconomicEvidencePersistResult.StaleVersion(
                    MarketplaceEconomicEvidenceVersion.ZERO
                )

            ApplyStep.SourceConflict ->
                MarketplaceIndependentEconomicEvidencePersistResult.SourceFactConflict
        }
    }

    private fun versioned(
        subject: MarketplaceEconomicEvidenceSubject,
        version: MarketplaceEconomicEvidenceVersion
    ): VersionedMarketplaceIndependentEconomicEvidence =
        VersionedMarketplaceIndependentEconomicEvidence(
            MarketplaceIndependentEconomicEvidence.empty(subject),
            version
        )
}