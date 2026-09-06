package io.flooow.marketplace.operations.economics.sales

import io.flooow.marketplace.operations.economics.EconomicExternalReferenceAbsenceReason
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.ChangeSequenceCheckpoint
import io.flooow.marketplace.operations.economics.evidence.CheckpointAdvanceResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChange
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeed
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeedResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeKind
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceVersion
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicOrderOccurrenceObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidence
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceMerger
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceReadResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceRepository
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceUpdate
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicFact
import io.flooow.marketplace.operations.economics.evidence.ProjectionName
import io.flooow.marketplace.operations.economics.evidence.VersionedMarketplaceIndependentEconomicEvidence
import io.flooow.organization.OrganizationId
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

class MarketplaceSalesIntelligenceProjectionProcessorTest {
    private val organization = OrganizationId(uuid(1))
    private val now = Instant.parse("2026-09-06T12:00:00.123456Z")
    private val clock = Clock.fixed(now, ZoneOffset.UTC)

    @Test
    fun `empty batch leaves checkpoint untouched`() {
        val subject = subject(10)
        val feed = FakeFeed(emptyList())
        val projection = FakeProjection()
        val processor = processor(feed, projection, mapOf(subject to versioned(empty(subject), 0)))

        assertIs<MarketplaceSalesIntelligenceProjectionProcessorResult.NoChanges>(
            processor.processBatch(organization, 100)
        )
        assertEquals(ChangeSequenceCheckpoint.NONE, feed.checkpoint)
        assertTrue(projection.records.isEmpty())
    }

    @Test
    fun `not ready materializes unresolved state and advances through final change`() {
        val subject = subject(11)
        val change = change(subject, 1, 1)
        val feed = FakeFeed(listOf(change))
        val projection = FakeProjection()
        val processor = processor(feed, projection, mapOf(subject to versioned(empty(subject), 1)))

        val result = assertIs<MarketplaceSalesIntelligenceProjectionProcessorResult.Success>(
            processor.processBatch(organization, 100)
        )
        assertEquals(ChangeSequenceCheckpoint(1), result.checkpoint)
        val record = projection.records.getValue(subject.orderId)
        assertIs<MarketplaceSalesIntelligenceState.Unresolved>(record.state)
        assertEquals(MarketplaceEconomicEvidenceVersion(1), record.sourceEvidenceVersion)
    }

    @Test
    fun `ready evidence flows through calculator and stores calculated state`() {
        val subject = subject(12)
        val change = change(subject, 1, 1)
        val projection = FakeProjection()
        val processor = processor(
            FakeFeed(listOf(change)),
            projection,
            mapOf(subject to versioned(withOccurrence(subject), 1))
        )

        assertIs<MarketplaceSalesIntelligenceProjectionProcessorResult.Success>(
            processor.processBatch(organization, 100)
        )
        val state = projection.records.getValue(subject.orderId).state
        assertIs<MarketplaceSalesIntelligenceState.Calculated>(state)
    }

    @Test
    fun `current refetch may be newer than invalidation evidence version`() {
        val subject = subject(13)
        val feed = FakeFeed(listOf(change(subject, 1, 1)))
        val projection = FakeProjection()
        val processor = processor(
            feed,
            projection,
            mapOf(subject to versioned(withOccurrence(subject), 7))
        )

        processor.processBatch(organization, 100)

        assertEquals(
            MarketplaceEconomicEvidenceVersion(7),
            projection.records.getValue(subject.orderId).sourceEvidenceVersion
        )
        assertEquals(
            ChangeSequenceCheckpoint(1),
            projection.records.getValue(subject.orderId).lastAppliedChangeSequence
        )
    }

    @Test
    fun `projection failure blocks checkpoint advancement`() {
        val subject = subject(14)
        val feed = FakeFeed(listOf(change(subject, 1, 1)))
        val projection = FakeProjection(failWrites = true)
        val processor = processor(
            feed,
            projection,
            mapOf(subject to versioned(empty(subject), 1))
        )

        assertIs<MarketplaceSalesIntelligenceProjectionProcessorResult.IntegrityFailure>(
            processor.processBatch(organization, 100)
        )
        assertEquals(ChangeSequenceCheckpoint.NONE, feed.checkpoint)
    }

    @Test
    fun `replay after checkpoint failure is safe because projection write is monotonic`() {
        val subject = subject(15)
        val feed = FakeFeed(listOf(change(subject, 1, 1)), failFirstAdvance = true)
        val projection = FakeProjection()
        val processor = processor(
            feed,
            projection,
            mapOf(subject to versioned(empty(subject), 1))
        )

        assertIs<MarketplaceSalesIntelligenceProjectionProcessorResult.IntegrityFailure>(
            processor.processBatch(organization, 100)
        )
        assertEquals(ChangeSequenceCheckpoint(1), projection.records.getValue(subject.orderId).lastAppliedChangeSequence)

        assertIs<MarketplaceSalesIntelligenceProjectionProcessorResult.Success>(
            processor.processBatch(organization, 100)
        )
        assertEquals(ChangeSequenceCheckpoint(1), feed.checkpoint)
        assertEquals(1, projection.appliedMutations)
    }

    @Test
    fun `multiple changes acknowledge exactly the final returned sequence`() {
        val first = subject(16)
        val second = subject(17)
        val changes = listOf(
            change(first, 1, 2),
            change(second, 1, 5)
        )
        val feed = FakeFeed(changes)
        val projection = FakeProjection()
        val processor = processor(
            feed,
            projection,
            mapOf(
                first to versioned(empty(first), 1),
                second to versioned(empty(second), 1)
            )
        )

        val result = assertIs<MarketplaceSalesIntelligenceProjectionProcessorResult.Success>(
            processor.processBatch(organization, 100)
        )
        assertEquals(ChangeSequenceCheckpoint(5), result.checkpoint)
        assertEquals(ChangeSequenceCheckpoint(5), feed.lastAdvanceDestination)
    }

    @Test
    fun `already current projection skips canonical refetch`() {
        val subject = subject(18)
        val projection = FakeProjection()
        projection.records[subject.orderId] = MarketplaceSalesIntelligenceProjectionRecord(
            organization,
            subject.orderId,
            MarketplaceEconomicEvidenceVersion(1),
            MarketplaceSalesIntelligenceState.Unresolved(
                io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssembler.POLICY_VERSION,
                setOf(
                    io.flooow.marketplace.operations.economics.MarketplaceEconomicTruthAssemblyNotReadyReason.ORDER_OCCURRED_AT_UNRESOLVED
                )
            ),
            ChangeSequenceCheckpoint(3),
            now
        )
        val feed = FakeFeed(listOf(change(subject, 1, 3)))
        val repository = CountingRepository(emptyMap())
        val processor = MarketplaceSalesIntelligenceProjectionProcessor(
            repository,
            feed,
            projection,
            clock
        )

        assertIs<MarketplaceSalesIntelligenceProjectionProcessorResult.Success>(
            processor.processBatch(organization, 100)
        )
        assertEquals(0, repository.findCalls)
    }

    private fun processor(
        feed: FakeFeed,
        projection: FakeProjection,
        evidence: Map<MarketplaceEconomicEvidenceSubject, VersionedMarketplaceIndependentEconomicEvidence>
    ) = MarketplaceSalesIntelligenceProjectionProcessor(
        CountingRepository(evidence),
        feed,
        projection,
        clock
    )

    private fun subject(seed: Long) = MarketplaceEconomicEvidenceSubject(
        organizationId = organization,
        orderId = MarketplaceOrderId(uuid(seed)),
        marketplace = MarketplaceKey("mercado-livre"),
        externalOrderId = MarketplaceExternalOrderId("order-$seed"),
        currency = MarketplaceCurrency("BRL")
    )

    private fun change(
        subject: MarketplaceEconomicEvidenceSubject,
        evidenceVersion: Long,
        sequence: Long
    ) = MarketplaceEconomicEvidenceChange(
        subject,
        MarketplaceEconomicEvidenceVersion(evidenceVersion),
        ChangeSequenceCheckpoint(sequence),
        MarketplaceEconomicEvidenceChangeKind.FACT
    )

    private fun empty(subject: MarketplaceEconomicEvidenceSubject) =
        MarketplaceIndependentEconomicEvidence.empty(subject)

    private fun withOccurrence(
        subject: MarketplaceEconomicEvidenceSubject
    ): MarketplaceIndependentEconomicEvidence {
        val occurrence = MarketplaceIndependentEconomicFact.OrderOccurrence(
            MarketplaceEconomicOrderOccurrenceObservation(
                id = MarketplaceEconomicEvidenceObservationId.parse(uuid(900).toString()),
                subject = subject,
                source = EconomicSource(
                    EconomicSourceKind.MANUAL,
                    EconomicSourceSystemKey("operator"),
                    EconomicExternalReferenceState.Absent(
                        EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN
                    )
                ),
                occurredAt = now.minusSeconds(60),
                observedAt = now
            )
        )
        val applied = MarketplaceIndependentEconomicEvidenceMerger.apply(
            MarketplaceIndependentEconomicEvidence.empty(subject),
            MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(occurrence)
        )
        return assertIs<MarketplaceIndependentEconomicEvidenceResult.Applied>(applied).evidence
    }

    private fun versioned(
        evidence: MarketplaceIndependentEconomicEvidence,
        version: Long
    ) = VersionedMarketplaceIndependentEconomicEvidence(
        evidence,
        MarketplaceEconomicEvidenceVersion(version)
    )

    private fun uuid(value: Long): UUID = UUID(0L, value)

    private class CountingRepository(
        private val evidence: Map<MarketplaceEconomicEvidenceSubject, VersionedMarketplaceIndependentEconomicEvidence>
    ) : MarketplaceIndependentEconomicEvidenceRepository {
        var findCalls: Int = 0

        override fun find(
            subject: MarketplaceEconomicEvidenceSubject
        ): MarketplaceIndependentEconomicEvidenceReadResult {
            findCalls += 1
            val value = evidence[subject]
            return if (value == null) {
                MarketplaceIndependentEconomicEvidenceReadResult.NotFound
            } else {
                MarketplaceIndependentEconomicEvidenceReadResult.Found(value)
            }
        }

        override fun apply(
            expectedVersion: MarketplaceEconomicEvidenceVersion,
            update: MarketplaceIndependentEconomicEvidenceUpdate
        ) = error("not used")
    }

    private class FakeProjection(
        private val failWrites: Boolean = false
    ) : MarketplaceSalesIntelligenceProjection {
        val records = linkedMapOf<MarketplaceOrderId, MarketplaceSalesIntelligenceProjectionRecord>()
        var appliedMutations: Int = 0

        override fun currentBySubject(
            organizationId: OrganizationId,
            marketplaceOrderId: MarketplaceOrderId
        ) = MarketplaceSalesIntelligenceProjectionReadResult.Success(records[marketplaceOrderId])

        override fun materializeIfNewer(
            record: MarketplaceSalesIntelligenceProjectionRecord
        ): MarketplaceSalesIntelligenceProjectionWriteResult {
            if (failWrites) return MarketplaceSalesIntelligenceProjectionWriteResult.IntegrityFailure
            val current = records[record.marketplaceOrderId]
            if (current != null &&
                current.lastAppliedChangeSequence >= record.lastAppliedChangeSequence
            ) {
                return MarketplaceSalesIntelligenceProjectionWriteResult.NoOpAlreadyCurrent
            }
            records[record.marketplaceOrderId] = record
            appliedMutations += 1
            return MarketplaceSalesIntelligenceProjectionWriteResult.Applied
        }

        override fun listByOrganization(
            organizationId: OrganizationId,
            cursor: MarketplaceSalesIntelligenceProjectionCursor?,
            limit: Int
        ) = MarketplaceSalesIntelligenceProjectionReadResult.Success(
            MarketplaceSalesIntelligenceProjectionPage(emptyList(), null)
        )

        override fun detailByOrganizationAndSubject(
            organizationId: OrganizationId,
            marketplaceOrderId: MarketplaceOrderId
        ) = currentBySubject(organizationId, marketplaceOrderId)
    }

    private class FakeFeed(
        private val changes: List<MarketplaceEconomicEvidenceChange>,
        private var failFirstAdvance: Boolean = false
    ) : MarketplaceEconomicEvidenceChangeFeed {
        var checkpoint: ChangeSequenceCheckpoint = ChangeSequenceCheckpoint.NONE
        var lastAdvanceDestination: ChangeSequenceCheckpoint? = null

        override fun changesSince(
            organizationId: OrganizationId,
            checkpoint: ChangeSequenceCheckpoint,
            limit: Int
        ) = MarketplaceEconomicEvidenceChangeFeedResult.Success(
            changes.filter { it.changeSequence > checkpoint }.take(limit)
        )

        override fun organizationsWithPendingChanges(
            projectionName: ProjectionName,
            limit: Int
        ) = MarketplaceEconomicEvidenceChangeFeedResult.Success(
            if (changes.any { it.changeSequence > checkpoint }) listOf(changes.first().subject.organizationId)
            else emptyList()
        )

        override fun currentCheckpoint(
            organizationId: OrganizationId,
            projectionName: ProjectionName
        ) = MarketplaceEconomicEvidenceChangeFeedResult.Success(checkpoint)

        override fun advanceCheckpoint(
            organizationId: OrganizationId,
            projectionName: ProjectionName,
            expected: ChangeSequenceCheckpoint,
            next: ChangeSequenceCheckpoint
        ): MarketplaceEconomicEvidenceChangeFeedResult<CheckpointAdvanceResult> {
            lastAdvanceDestination = next
            if (failFirstAdvance) {
                failFirstAdvance = false
                return MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure
            }
            if (checkpoint != expected) {
                return MarketplaceEconomicEvidenceChangeFeedResult.Success(
                    CheckpointAdvanceResult.Stale(checkpoint)
                )
            }
            checkpoint = next
            return MarketplaceEconomicEvidenceChangeFeedResult.Success(
                CheckpointAdvanceResult.Advanced(next)
            )
        }
    }
}
