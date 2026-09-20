package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.EconomicComponent
import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentId
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
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
import io.flooow.marketplace.operations.economics.evidence.ChangeSequenceCheckpoint
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceUpdateReadResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceUpdateReader
import io.flooow.marketplace.operations.economics.evidence.CheckpointAdvanceResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChange
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeed
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeedResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeKind
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceFamily
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceVersion
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidence
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceMerger
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidencePersistResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceReadResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceRepository
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceUpdate
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicFact
import io.flooow.marketplace.operations.economics.evidence.ProjectionName
import io.flooow.marketplace.operations.economics.evidence.VersionedMarketplaceIndependentEconomicEvidence
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.organization.OrganizationId
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertTrue

class MarketplaceFinancialLedgerMaterializationProcessorTest {
    @Test
    fun `eligible source materializes once and advances independent checkpoint`() {
        val observation = observation()
        val feed = feed(change(observation))
        val updateReader = updateReader(observation)

        var commits = 0

        val processor =
            processor(
                updateReader = updateReader,
                feed = feed,
                authority = { _, source -> authorized(source) },
                commit = {
                    commits++
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult.Success
            >(
                processor.processBatch(
                    observation.subject.organizationId,
                    100
                )
            )

        assertEquals(1, result.processedChanges)
        assertEquals(1, result.materialized)
        assertEquals(0, result.alreadyMaterialized)
        assertEquals(0, result.notEligible)
        assertEquals(ChangeSequenceCheckpoint(1), result.checkpoint)
        assertEquals(1, commits)
        assertTrue(feed.advanceCalled)
        assertEquals(
            "financial-ledger-materialization",
            feed.lastProjectionName?.valueForPersistence()
        )
    }

    @Test
    fun `processor binds FACT processing to exact change update identity`() {
        val observation = observation()
        val feed = feed(change(observation))

        var readerCalls = 0
        var commits = 0

        val exactReader =
            MarketplaceEconomicEvidenceUpdateReader {
                    subject,
                    evidenceVersion,
                    updateId,
                    changeKind ->

                readerCalls++

                assertEquals(observation.subject, subject)
                assertEquals(
                    MarketplaceEconomicEvidenceVersion(1),
                    evidenceVersion
                )
                assertEquals(observation.id, updateId)
                assertEquals(
                    MarketplaceEconomicEvidenceChangeKind.FACT,
                    changeKind
                )

                MarketplaceEconomicEvidenceUpdateReadResult.Found(
                    MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                        MarketplaceIndependentEconomicFact.Component(
                            observation
                        )
                    )
                )
            }

        val processor =
            processor(
                updateReader = exactReader,
                feed = feed,
                authority = { _, source -> authorized(source) },
                commit = {
                    commits++
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult.Success
            >(
                processor.processBatch(
                    observation.subject.organizationId,
                    100
                )
            )

        assertEquals(1, readerCalls)
        assertEquals(1, commits)
        assertEquals(1, result.materialized)
        assertTrue(feed.advanceCalled)
    }

    @Test
    fun `exact replay is successful and checkpoint advances`() {
        val observation = observation()
        val feed = feed(change(observation))

        val processor =
            processor(
                updateReader = updateReader(observation),
                feed = feed,
                authority = { _, source -> authorized(source) },
                commit = {
                    GovernedFinancialLedgerMaterializationCommitResult
                        .AlreadyMaterialized(
                            traceId(),
                            entryId()
                        )
                }
            )

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult.Success
            >(
                processor.processBatch(
                    observation.subject.organizationId,
                    100
                )
            )

        assertEquals(0, result.materialized)
        assertEquals(1, result.alreadyMaterialized)
        assertTrue(feed.advanceCalled)
    }

    @Test
    fun `semantic non authorization consumes change without ledger mutation`() {
        val observation = observation()
        val feed = feed(change(observation))

        var commits = 0

        val processor =
            processor(
                updateReader = updateReader(observation),
                feed = feed,
                authority = { _, _ ->
                    FinancialLedgerComponentMaterializationAuthorityDecision
                        .NotAuthorized(
                            FinancialLedgerComponentMaterializationNotAuthorizedReason
                                .BASIS_AUTHORITY_UNAVAILABLE
                        )
                },
                commit = {
                    commits++
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult.Success
            >(
                processor.processBatch(
                    observation.subject.organizationId,
                    100
                )
            )

        assertEquals(1, result.notEligible)
        assertEquals(0, commits)
        assertTrue(feed.advanceCalled)
    }

    @Test
    fun `authority unavailable fails without advancing checkpoint`() {
        val observation = observation()
        val feed = feed(change(observation))

        val processor =
            processor(
                updateReader = updateReader(observation),
                feed = feed,
                authority = { _, _ ->
                    FinancialLedgerComponentMaterializationAuthorityDecision.Unavailable
                }
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.Unavailable
        >(
            processor.processBatch(
                observation.subject.organizationId,
                100
            )
        )

        assertFalse(feed.advanceCalled)
    }

    @Test
    fun `authority integrity failure fails closed without advancing checkpoint`() {
        val observation = observation()
        val feed = feed(change(observation))

        val processor =
            processor(
                updateReader = updateReader(observation),
                feed = feed,
                authority = { _, _ ->
                    FinancialLedgerComponentMaterializationAuthorityDecision
                        .IntegrityFailure
                }
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.IntegrityFailure
        >(
            processor.processBatch(
                observation.subject.organizationId,
                100
            )
        )

        assertFalse(feed.advanceCalled)
    }

    @Test
    fun `commit conflict does not advance checkpoint`() {
        val observation = observation()
        val feed = feed(change(observation))

        val processor =
            processor(
                updateReader = updateReader(observation),
                feed = feed,
                authority = { _, source -> authorized(source) },
                commit = {
                    GovernedFinancialLedgerMaterializationCommitResult.Failed(
                        GovernedFinancialLedgerMaterializationCommitFailure.CONFLICT
                    )
                }
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.CommitConflict
        >(
            processor.processBatch(
                observation.subject.organizationId,
                100
            )
        )

        assertFalse(feed.advanceCalled)
    }

    @Test
    fun `cross organization batch fails before authority or commit`() {
        val observation = observation()
        val operationalOrganization =
            OrganizationId.parse(
                "99999999-9999-4999-8999-999999999999"
            )

        val feed = feed(change(observation))

        var authorityCalls = 0
        var commits = 0

        val processor =
            processor(
                updateReader = updateReader(observation),
                feed = feed,
                authority = { _, source ->
                    authorityCalls++
                    authorized(source)
                },
                commit = {
                    commits++
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.IntegrityFailure
        >(
            processor.processBatch(
                operationalOrganization,
                100
            )
        )

        assertEquals(0, authorityCalls)
        assertEquals(0, commits)
        assertFalse(feed.advanceCalled)
    }
    @Test
    fun `missing exact update fails closed without checkpoint advance`() {
        val observation = observation()

        val feed =
            feed(
                change(
                    observation,
                    evidenceVersion = MarketplaceEconomicEvidenceVersion(2)
                )
            )

        val processor =
            processor(
                updateReader =
                    MarketplaceEconomicEvidenceUpdateReader {
                            _,
                            _,
                            _,
                            _ ->
                        MarketplaceEconomicEvidenceUpdateReadResult.NotFound
                    },
                feed = feed,
                authority = { _, source -> authorized(source) }
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.IntegrityFailure
        >(
            processor.processBatch(
                observation.subject.organizationId,
                100
            )
        )

        assertFalse(feed.advanceCalled)
    }

    @Test
    fun `stale checkpoint at or beyond destination converges successfully`() {
        val observation = observation()

        val feed =
            feed(
                change(observation),
                advanceResult =
                    CheckpointAdvanceResult.Stale(
                        ChangeSequenceCheckpoint(5)
                    )
            )

        val processor =
            processor(
                updateReader = updateReader(observation),
                feed = feed,
                authority = { _, source -> authorized(source) }
            )

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult.Success
            >(
                processor.processBatch(
                    observation.subject.organizationId,
                    100
                )
            )

        assertEquals(ChangeSequenceCheckpoint(5), result.checkpoint)
    }

    @Test
    fun `fact followed by attempt materializes fact once and advances through attempt`() {
        val observation = observation()

        val changes =
            listOf(
                change(
                    observation,
                    sequence = 1
                ),
                MarketplaceEconomicEvidenceChange(
                    subject = observation.subject,
                    updateId =
                        MarketplaceEconomicEvidenceObservationId.parse(
                            "11111111-1111-4111-8111-111111111111"
                        ),
                    evidenceVersion = MarketplaceEconomicEvidenceVersion(2),
                    changeSequence = ChangeSequenceCheckpoint(2),
                    changeKind = MarketplaceEconomicEvidenceChangeKind.ATTEMPT
                )
            )

        val feed = RecordingFeed(changes, null)

        var commits = 0

        val processor =
            processor(
                updateReader = updateReader(observation),
                feed = feed,
                authority = { _, source -> authorized(source) },
                commit = {
                    commits++
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult.Success
            >(
                processor.processBatch(
                    observation.subject.organizationId,
                    100
                )
            )

        assertEquals(2, result.processedChanges)
        assertEquals(1, result.materialized)
        assertEquals(1, commits)
        assertEquals(ChangeSequenceCheckpoint(2), result.checkpoint)
        assertTrue(feed.advanceCalled)
    }

    @Test
    fun `fact followed by correction fails closed before any batch side effect`() {
        val observation = observation()

        val correctionId =
            MarketplaceEconomicEvidenceObservationId.parse(
                "22222222-2222-4222-8222-222222222222"
            )

        val changes =
            listOf(
                change(
                    observation,
                    sequence = 1
                ),
                MarketplaceEconomicEvidenceChange(
                    subject = observation.subject,
                    updateId = correctionId,
                    evidenceVersion = MarketplaceEconomicEvidenceVersion(2),
                    changeSequence = ChangeSequenceCheckpoint(2),
                    changeKind = MarketplaceEconomicEvidenceChangeKind.CORRECTION
                )
            )

        val feed = RecordingFeed(changes, null)

        var readerCalls = 0
        var commits = 0

        val processor =
            processor(
                updateReader =
                    MarketplaceEconomicEvidenceUpdateReader {
                            subject,
                            evidenceVersion,
                            updateId,
                            changeKind ->

                        readerCalls++

                        MarketplaceEconomicEvidenceUpdateReadResult.Found(
                            MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                                MarketplaceIndependentEconomicFact.Component(
                                    observation
                                )
                            )
                        )
                    },
                feed = feed,
                authority = { _, source -> authorized(source) },
                commit = {
                    commits++
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.UnsupportedCorrection
        >(
            processor.processBatch(
                observation.subject.organizationId,
                100
            )
        )

        assertEquals(0, readerCalls)
        assertEquals(0, commits)
        assertFalse(feed.advanceCalled)
    }

    @Test
    fun `reader update identity mismatch fails closed before authority and commit`() {
        val observation = observation()
        val feed = feed(change(observation))

        val wrongObservation =
            observation().copy(
                id =
                    MarketplaceEconomicEvidenceObservationId.parse(
                        "33333333-3333-4333-8333-333333333333"
                    )
            )

        var authorityCalls = 0
        var commits = 0

        val processor =
            processor(
                updateReader =
                    MarketplaceEconomicEvidenceUpdateReader {
                            _,
                            _,
                            _,
                            _ ->

                        MarketplaceEconomicEvidenceUpdateReadResult.Found(
                            MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                                MarketplaceIndependentEconomicFact.Component(
                                    wrongObservation
                                )
                            )
                        )
                    },
                feed = feed,
                authority = { _, source ->
                    authorityCalls++
                    authorized(source)
                },
                commit = {
                    commits++
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.IntegrityFailure
        >(
            processor.processBatch(
                observation.subject.organizationId,
                100
            )
        )

        assertEquals(0, authorityCalls)
        assertEquals(0, commits)
        assertFalse(feed.advanceCalled)
    }

    @Test
    fun `restart replay converges through already materialized without duplicate effect`() {
        val observation = observation()

        val firstFeed = feed(change(observation))

        val firstProcessor =
            processor(
                updateReader = updateReader(observation),
                feed = firstFeed,
                authority = { _, source -> authorized(source) },
                commit = {
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        val first =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult.Success
            >(
                firstProcessor.processBatch(
                    observation.subject.organizationId,
                    100
                )
            )

        assertEquals(1, first.materialized)

        val replayFeed = feed(change(observation))

        val replayProcessor =
            processor(
                updateReader = updateReader(observation),
                feed = replayFeed,
                authority = { _, source -> authorized(source) },
                commit = {
                    GovernedFinancialLedgerMaterializationCommitResult
                        .AlreadyMaterialized(
                            traceId(),
                            entryId()
                        )
                }
            )

        val replay =
            assertIs<
                MarketplaceFinancialLedgerMaterializationProcessorResult.Success
            >(
                replayProcessor.processBatch(
                    observation.subject.organizationId,
                    100
                )
            )

        assertEquals(0, replay.materialized)
        assertEquals(1, replay.alreadyMaterialized)
        assertTrue(replayFeed.advanceCalled)
    }

    @Test
    fun `blocking first change prevents checkpoint from crossing later changes`() {
        val observation = observation()

        val secondObservation =
            observation().copy(
                id =
                    MarketplaceEconomicEvidenceObservationId.parse(
                        "44444444-4444-4444-8444-444444444444"
                    )
            )

        val changes =
            listOf(
                change(
                    observation,
                    sequence = 1
                ),
                MarketplaceEconomicEvidenceChange(
                    subject = secondObservation.subject,
                    updateId = secondObservation.id,
                    evidenceVersion = MarketplaceEconomicEvidenceVersion(2),
                    changeSequence = ChangeSequenceCheckpoint(2),
                    changeKind = MarketplaceEconomicEvidenceChangeKind.FACT
                )
            )

        val feed = RecordingFeed(changes, null)

        var commits = 0

        val processor =
            processor(
                updateReader =
                    MarketplaceEconomicEvidenceUpdateReader {
                            _,
                            evidenceVersion,
                            updateId,
                            _ ->

                        if (evidenceVersion == MarketplaceEconomicEvidenceVersion(1)) {
                            MarketplaceEconomicEvidenceUpdateReadResult.NotFound
                        } else {
                            MarketplaceEconomicEvidenceUpdateReadResult.Found(
                                MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                                    MarketplaceIndependentEconomicFact.Component(
                                        secondObservation
                                    )
                                )
                            )
                        }
                    },
                feed = feed,
                authority = { _, source -> authorized(source) },
                commit = {
                    commits++
                    GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                        traceId(),
                        entryId()
                    )
                }
            )

        assertIs<
            MarketplaceFinancialLedgerMaterializationProcessorResult.IntegrityFailure
        >(
            processor.processBatch(
                observation.subject.organizationId,
                100
            )
        )

        assertEquals(0, commits)
        assertFalse(feed.advanceCalled)
    }
    private fun processor(
        updateReader: MarketplaceEconomicEvidenceUpdateReader,
        feed: RecordingFeed,
        authority: (
            OrganizationId,
            MarketplaceEconomicComponentObservation
        ) -> FinancialLedgerComponentMaterializationAuthorityDecision,
        commit: (
            VerifiedFinancialLedgerComponentMaterializationPlan
        ) -> GovernedFinancialLedgerMaterializationCommitResult = {
            GovernedFinancialLedgerMaterializationCommitResult.Materialized(
                traceId(),
                entryId()
            )
        }
    ): MarketplaceFinancialLedgerMaterializationProcessor =
        MarketplaceFinancialLedgerMaterializationProcessor(
            updateReader = updateReader,
            changeFeed = feed,
            authorityResolver = authority,
            commitStore =
                GovernedFinancialLedgerMaterializationCommitStore {
                    commit(it)
                }
        )

    private fun updateReader(
        observation: MarketplaceEconomicComponentObservation
    ): MarketplaceEconomicEvidenceUpdateReader =
        MarketplaceEconomicEvidenceUpdateReader {
                subject,
                evidenceVersion,
                updateId,
                changeKind ->

            if (
                subject != observation.subject ||
                evidenceVersion != MarketplaceEconomicEvidenceVersion(1) ||
                updateId != observation.id ||
                changeKind != MarketplaceEconomicEvidenceChangeKind.FACT
            ) {
                MarketplaceEconomicEvidenceUpdateReadResult.IntegrityFailure
            } else {
                MarketplaceEconomicEvidenceUpdateReadResult.Found(
                    MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                        MarketplaceIndependentEconomicFact.Component(
                            observation
                        )
                    )
                )
            }
        }
    private fun repository(
        observation: MarketplaceEconomicComponentObservation,
        version: MarketplaceEconomicEvidenceVersion =
            MarketplaceEconomicEvidenceVersion(1)
    ): MarketplaceIndependentEconomicEvidenceRepository {
        val empty =
            MarketplaceIndependentEconomicEvidence.empty(
                observation.subject
            )

        val merged =
            MarketplaceIndependentEconomicEvidenceMerger.apply(
                empty,
                MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
                    MarketplaceIndependentEconomicFact.Component(
                        observation
                    )
                )
            )

        val evidence =
            assertIs<
                MarketplaceIndependentEconomicEvidenceResult.Applied
            >(merged).evidence

        return object : MarketplaceIndependentEconomicEvidenceRepository {
            override fun find(
                subject: MarketplaceEconomicEvidenceSubject
            ): MarketplaceIndependentEconomicEvidenceReadResult =
                if (subject == observation.subject) {
                    MarketplaceIndependentEconomicEvidenceReadResult.Found(
                        VersionedMarketplaceIndependentEconomicEvidence(
                            evidence,
                            version
                        )
                    )
                } else {
                    MarketplaceIndependentEconomicEvidenceReadResult.NotFound
                }

            override fun apply(
                expectedVersion: MarketplaceEconomicEvidenceVersion,
                update: MarketplaceIndependentEconomicEvidenceUpdate
            ): MarketplaceIndependentEconomicEvidencePersistResult =
                error("write not used by materialization processor test")
        }
    }

    private fun feed(
        change: MarketplaceEconomicEvidenceChange,
        advanceResult: CheckpointAdvanceResult? = null
    ): RecordingFeed =
        RecordingFeed(
            listOf(change),
            advanceResult
        )

    private fun change(
        observation: MarketplaceEconomicComponentObservation,
        evidenceVersion: MarketplaceEconomicEvidenceVersion =
            MarketplaceEconomicEvidenceVersion(1),
        sequence: Long = 1
    ): MarketplaceEconomicEvidenceChange =
        MarketplaceEconomicEvidenceChange(
            subject = observation.subject,
            updateId = observation.id,
            evidenceVersion = evidenceVersion,
            changeSequence = ChangeSequenceCheckpoint(sequence),
            changeKind = MarketplaceEconomicEvidenceChangeKind.FACT
        )

    private fun authorized(
        observation: MarketplaceEconomicComponentObservation
    ): FinancialLedgerComponentMaterializationAuthorityDecision =
        FinancialLedgerComponentMaterializationAuthorityDecision.Authorized(
            sourceAuthorityIdentity = observation.id,
            sourceAuthoritySemanticVersion =
                FinancialLedgerSourceAuthoritySemanticVersion(
                    "test.authority/1"
                ),
            materializationPolicyVersion =
                FinancialLedgerMaterializationPolicyVersion.V1,
            expectedSourceFingerprint =
                FinancialLedgerMaterializationSourceFingerprintV1
                    .fingerprint(observation),
            basis = FinancialLedgerBasis.ACTUAL
        )

    private fun observation(): MarketplaceEconomicComponentObservation {
        val organizationId =
            OrganizationId.parse(
                "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
            )

        val orderId =
            MarketplaceOrderId.parse(
                "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
            )

        val currency = MarketplaceCurrency("BRL")

        val subject =
            MarketplaceEconomicEvidenceSubject(
                organizationId = organizationId,
                orderId = orderId,
                marketplace = MarketplaceKey("mercado-livre"),
                externalOrderId =
                    MarketplaceExternalOrderId("MLB-123"),
                currency = currency
            )

        val component =
            EconomicComponent(
                organizationId = organizationId,
                id =
                    EconomicComponentId.parse(
                        "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
                    ),
                orderId = orderId,
                type = EconomicComponentType.REVENUE,
                direction = EconomicDirection.ADDITION,
                magnitude =
                    MarketplaceMoney.parse(
                        currency,
                        "100.00"
                    ),
                source =
                    EconomicSource(
                        kind = EconomicSourceKind.MARKETPLACE,
                        systemKey =
                            EconomicSourceSystemKey(
                                "br.com.mercadolivre"
                            ),
                        externalReference =
                            EconomicExternalReferenceState.Present(
                                EconomicExternalReference(
                                    "MLB-123"
                                )
                            )
                    ),
                occurredAt =
                    Instant.parse(
                        "2026-09-20T12:00:00.000001Z"
                    ),
                quality = EconomicEvidenceQuality.CONFIRMED
            )

        return MarketplaceEconomicComponentObservation(
            id =
                MarketplaceEconomicEvidenceObservationId.parse(
                    "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
                ),
            subject = subject,
            family =
                MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
            component = component,
            coverageClaim = EconomicComponentCoverage.PARTIAL,
            observedAt =
                Instant.parse(
                    "2026-09-20T12:01:00.000001Z"
                )
        )
    }

    private fun traceId(): FinancialTraceId =
        FinancialTraceId.parse(
            "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
        )

    private fun entryId(): FinancialLedgerEntryId =
        FinancialLedgerEntryId.parse(
            "ffffffff-ffff-4fff-8fff-ffffffffffff"
        )

    private class RecordingFeed(
        private val changes: List<MarketplaceEconomicEvidenceChange>,
        private val configuredAdvanceResult: CheckpointAdvanceResult?
    ) : MarketplaceEconomicEvidenceChangeFeed {
        var checkpoint: ChangeSequenceCheckpoint =
            ChangeSequenceCheckpoint.NONE

        var advanceCalled: Boolean = false
        var lastProjectionName: ProjectionName? = null

        override fun changesSince(
            organizationId: OrganizationId,
            checkpoint: ChangeSequenceCheckpoint,
            limit: Int
        ): MarketplaceEconomicEvidenceChangeFeedResult<
            List<MarketplaceEconomicEvidenceChange>
        > =
            MarketplaceEconomicEvidenceChangeFeedResult.Success(
                changes.take(limit)
            )

        override fun organizationsWithPendingChanges(
            projectionName: ProjectionName,
            limit: Int
        ): MarketplaceEconomicEvidenceChangeFeedResult<
            List<OrganizationId>
        > =
            MarketplaceEconomicEvidenceChangeFeedResult.Success(
                emptyList()
            )

        override fun currentCheckpoint(
            organizationId: OrganizationId,
            projectionName: ProjectionName
        ): MarketplaceEconomicEvidenceChangeFeedResult<
            ChangeSequenceCheckpoint
        > {
            lastProjectionName = projectionName

            return MarketplaceEconomicEvidenceChangeFeedResult.Success(
                checkpoint
            )
        }

        override fun advanceCheckpoint(
            organizationId: OrganizationId,
            projectionName: ProjectionName,
            expected: ChangeSequenceCheckpoint,
            next: ChangeSequenceCheckpoint
        ): MarketplaceEconomicEvidenceChangeFeedResult<
            CheckpointAdvanceResult
        > {
            advanceCalled = true
            lastProjectionName = projectionName

            val result =
                configuredAdvanceResult
                    ?: CheckpointAdvanceResult.Advanced(next)

            if (result is CheckpointAdvanceResult.Advanced) {
                checkpoint = result.checkpoint
            }

            return MarketplaceEconomicEvidenceChangeFeedResult.Success(
                result
            )
        }
    }
}