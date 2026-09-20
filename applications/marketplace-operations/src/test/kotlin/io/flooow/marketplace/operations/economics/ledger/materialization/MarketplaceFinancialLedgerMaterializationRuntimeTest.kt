package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.evidence.ChangeSequenceCheckpoint
import io.flooow.marketplace.operations.economics.evidence.CheckpointAdvanceResult
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChange
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeed
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeedResult
import io.flooow.marketplace.operations.economics.evidence.ProjectionName
import io.flooow.organization.OrganizationId
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs

class MarketplaceFinancialLedgerMaterializationRuntimeTest {

    @Test
    fun `dispatch aggregates successful organization batches`() {
        val first =
            OrganizationId.parse(
                "11111111-1111-4111-8111-111111111111"
            )

        val second =
            OrganizationId.parse(
                "22222222-2222-4222-8222-222222222222"
            )

        val feed =
            DiscoveryFeed(
                MarketplaceEconomicEvidenceChangeFeedResult.Success(
                    listOf(first, second)
                )
            )

        val calls = mutableListOf<OrganizationId>()

        val runtime =
            MarketplaceFinancialLedgerMaterializationRuntime(
                changeFeed = feed,
                processBatch = { organizationId, limit ->
                    assertEquals(100, limit)
                    calls += organizationId

                    if (organizationId == first) {
                        MarketplaceFinancialLedgerMaterializationProcessorResult
                            .Success(
                                processedChanges = 3,
                                materialized = 2,
                                alreadyMaterialized = 1,
                                notEligible = 0,
                                checkpoint = ChangeSequenceCheckpoint(3)
                            )
                    } else {
                        MarketplaceFinancialLedgerMaterializationProcessorResult
                            .Success(
                                processedChanges = 2,
                                materialized = 1,
                                alreadyMaterialized = 0,
                                notEligible = 1,
                                checkpoint = ChangeSequenceCheckpoint(2)
                            )
                    }
                }
            )

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationRuntimeResult.Success
            >(
                runtime.dispatchOnce(
                    organizationLimit = 50,
                    batchLimit = 100
                )
            )

        assertEquals(listOf(first, second), calls)
        assertEquals(2, result.organizationsDiscovered)
        assertEquals(2, result.organizationsProcessed)
        assertEquals(5, result.processedChanges)
        assertEquals(3, result.materialized)
        assertEquals(1, result.alreadyMaterialized)
        assertEquals(1, result.notEligible)

        assertEquals(
            MarketplaceFinancialLedgerMaterializationProcessor.PROJECTION_NAME,
            feed.requestedProjection
        )
        assertEquals(50, feed.requestedLimit)
    }

    @Test
    fun `empty discovery produces no pending organizations`() {
        val feed =
            DiscoveryFeed(
                MarketplaceEconomicEvidenceChangeFeedResult.Success(
                    emptyList()
                )
            )

        var processorCalls = 0

        val runtime =
            MarketplaceFinancialLedgerMaterializationRuntime(
                feed
            ) { _, _ ->
                processorCalls++
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .NoChanges
            }

        assertIs<
            MarketplaceFinancialLedgerMaterializationRuntimeResult
                .NoPendingOrganizations
        >(
            runtime.dispatchOnce(
                organizationLimit = 10,
                batchLimit = 10
            )
        )

        assertEquals(0, processorCalls)
    }

    @Test
    fun `discovery integrity failure fails closed before processor`() {
        val feed =
            DiscoveryFeed(
                MarketplaceEconomicEvidenceChangeFeedResult.IntegrityFailure
            )

        var processorCalls = 0

        val runtime =
            MarketplaceFinancialLedgerMaterializationRuntime(
                feed
            ) { _, _ ->
                processorCalls++
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .NoChanges
            }

        assertIs<
            MarketplaceFinancialLedgerMaterializationRuntimeResult
                .IntegrityFailure
        >(
            runtime.dispatchOnce(
                organizationLimit = 10,
                batchLimit = 10
            )
        )

        assertEquals(0, processorCalls)
    }

    @Test
    fun `runtime stops at first unavailable organization and does not cross blocker`() {
        val first =
            OrganizationId.parse(
                "33333333-3333-4333-8333-333333333333"
            )

        val blocked =
            OrganizationId.parse(
                "44444444-4444-4444-8444-444444444444"
            )

        val later =
            OrganizationId.parse(
                "55555555-5555-4555-8555-555555555555"
            )

        val feed =
            DiscoveryFeed(
                MarketplaceEconomicEvidenceChangeFeedResult.Success(
                    listOf(first, blocked, later)
                )
            )

        val calls = mutableListOf<OrganizationId>()

        val runtime =
            MarketplaceFinancialLedgerMaterializationRuntime(
                feed
            ) { organizationId, _ ->
                calls += organizationId

                when (organizationId) {
                    first ->
                        MarketplaceFinancialLedgerMaterializationProcessorResult
                            .Success(
                                processedChanges = 1,
                                materialized = 1,
                                alreadyMaterialized = 0,
                                notEligible = 0,
                                checkpoint = ChangeSequenceCheckpoint(1)
                            )

                    blocked ->
                        MarketplaceFinancialLedgerMaterializationProcessorResult
                            .Unavailable

                    else ->
                        error("Runtime crossed blocking organization")
                }
            }

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationRuntimeResult.Blocked
            >(
                runtime.dispatchOnce(
                    organizationLimit = 10,
                    batchLimit = 10
                )
            )

        assertEquals(blocked, result.organizationId)
        assertEquals(
            MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                .AUTHORITY_OR_PERSISTENCE_UNAVAILABLE,
            result.reason
        )

        assertEquals(
            listOf(first, blocked),
            calls
        )
    }

    @Test
    fun `no changes is safe under stale discovery`() {
        val organization =
            OrganizationId.parse(
                "66666666-6666-4666-8666-666666666666"
            )

        val feed =
            DiscoveryFeed(
                MarketplaceEconomicEvidenceChangeFeedResult.Success(
                    listOf(organization)
                )
            )

        val runtime =
            MarketplaceFinancialLedgerMaterializationRuntime(
                feed
            ) { _, _ ->
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .NoChanges
            }

        val result =
            assertIs<
                MarketplaceFinancialLedgerMaterializationRuntimeResult.Success
            >(
                runtime.dispatchOnce(
                    organizationLimit = 10,
                    batchLimit = 10
                )
            )

        assertEquals(1, result.organizationsDiscovered)
        assertEquals(1, result.organizationsProcessed)
        assertEquals(0, result.processedChanges)
        assertEquals(0, result.materialized)
    }

    @Test
    fun `runtime maps every blocking processor outcome`() {
        val organization =
            OrganizationId.parse(
                "77777777-7777-4777-8777-777777777777"
            )

        val mappings =
            listOf(
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .CheckpointConflict to
                    MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                        .CHECKPOINT_CONFLICT,

                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .CommitConflict to
                    MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                        .COMMIT_CONFLICT,

                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .Unavailable to
                    MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                        .AUTHORITY_OR_PERSISTENCE_UNAVAILABLE,

                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .UnsupportedCorrection to
                    MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                        .UNSUPPORTED_CORRECTION,

                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .IntegrityFailure to
                    MarketplaceFinancialLedgerMaterializationRuntimeBlockReason
                        .INTEGRITY_FAILURE
            )

        mappings.forEach { (processorResult, expectedReason) ->
            val runtime =
                MarketplaceFinancialLedgerMaterializationRuntime(
                    DiscoveryFeed(
                        MarketplaceEconomicEvidenceChangeFeedResult.Success(
                            listOf(organization)
                        )
                    )
                ) { _, _ ->
                    processorResult
                }

            val result =
                assertIs<
                    MarketplaceFinancialLedgerMaterializationRuntimeResult.Blocked
                >(
                    runtime.dispatchOnce(
                        organizationLimit = 10,
                        batchLimit = 10
                    )
                )

            assertEquals(expectedReason, result.reason)
        }
    }

    @Test
    fun `runtime validates dispatch limits before discovery`() {
        val feed =
            DiscoveryFeed(
                MarketplaceEconomicEvidenceChangeFeedResult.Success(
                    emptyList()
                )
            )

        assertFailsWith<IllegalArgumentException> {
            MarketplaceFinancialLedgerMaterializationRuntime(
                feed
            ) { _, _ ->
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .NoChanges
            }.dispatchOnce(
                organizationLimit = 0,
                batchLimit = 10
            )
        }

        assertFailsWith<IllegalArgumentException> {
            MarketplaceFinancialLedgerMaterializationRuntime(
                feed
            ) { _, _ ->
                MarketplaceFinancialLedgerMaterializationProcessorResult
                    .NoChanges
            }.dispatchOnce(
                organizationLimit = 10,
                batchLimit = 0
            )
        }

        assertEquals(0, feed.discoveryCalls)
    }

    private class DiscoveryFeed(
        private val organizations:
            MarketplaceEconomicEvidenceChangeFeedResult<List<OrganizationId>>
    ) : MarketplaceEconomicEvidenceChangeFeed {

        var discoveryCalls: Int = 0
        var requestedProjection: ProjectionName? = null
        var requestedLimit: Int? = null

        override fun organizationsWithPendingChanges(
            projectionName: ProjectionName,
            limit: Int
        ): MarketplaceEconomicEvidenceChangeFeedResult<List<OrganizationId>> {
            discoveryCalls++
            requestedProjection = projectionName
            requestedLimit = limit
            return organizations
        }

        override fun changesSince(
            organizationId: OrganizationId,
            checkpoint: ChangeSequenceCheckpoint,
            limit: Int
        ): MarketplaceEconomicEvidenceChangeFeedResult<
            List<MarketplaceEconomicEvidenceChange>
        > = error("Not used by runtime orchestration test")

        override fun currentCheckpoint(
            organizationId: OrganizationId,
            projectionName: ProjectionName
        ): MarketplaceEconomicEvidenceChangeFeedResult<
            ChangeSequenceCheckpoint
        > = error("Not used by runtime orchestration test")

        override fun advanceCheckpoint(
            organizationId: OrganizationId,
            projectionName: ProjectionName,
            expected: ChangeSequenceCheckpoint,
            next: ChangeSequenceCheckpoint
        ): MarketplaceEconomicEvidenceChangeFeedResult<
            CheckpointAdvanceResult
        > = error("Not used by runtime orchestration test")
    }
}