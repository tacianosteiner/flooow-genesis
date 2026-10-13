package io.flooow.marketplace.operations.economics.sales

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.UUID
import kotlin.test.*

class ConsumedEconomicEvidenceSnapshotTest {
    private val time = Instant.parse("2026-10-12T12:00:00.123456Z")
    private val subject = MarketplaceEconomicEvidenceSubject(OrganizationId(UUID(0, 1)), MarketplaceOrderId(UUID(0, 2)),
        MarketplaceKey("fixture"), MarketplaceExternalOrderId("order"), MarketplaceCurrency("BRL"))
    private val source = EconomicSource(EconomicSourceKind.MANUAL, EconomicSourceSystemKey("fixture"),
        EconomicExternalReferenceState.Absent(EconomicExternalReferenceAbsenceReason.INTERNAL_ORIGIN))
    private fun id(value: Long) = MarketplaceEconomicEvidenceObservationId.parse(UUID(0, value).toString())
    private fun fact(value: Long, occurredAt: Instant = time) = MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(
        MarketplaceIndependentEconomicFact.OrderOccurrence(MarketplaceEconomicOrderOccurrenceObservation(id(value), subject, source, occurredAt, time)))
    private fun attempt(value: Long) = MarketplaceIndependentEconomicEvidenceUpdate.RecordAttempt(
        MarketplaceEconomicEvidenceCollectionAttempt(id(value), subject, MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
            EconomicSourceSystemKey("fixture"), MarketplaceEconomicEvidenceAttemptOutcome.NO_EVIDENCE, time))
    private fun correction(original: Long, replacement: Long, correction: Long) = MarketplaceIndependentEconomicEvidenceUpdate.Correct(
        MarketplaceEconomicEvidenceCorrection(id(correction), subject, fact(replacement).fact, id(original),
            MarketplaceEconomicEvidenceCorrectionReason.SOURCE_CORRECTION, time))
    private fun replay(vararg updates: MarketplaceIndependentEconomicEvidenceUpdate): VersionedMarketplaceIndependentEconomicEvidence {
        var evidence = MarketplaceIndependentEconomicEvidence.empty(subject)
        val members = mutableListOf<VersionedEconomicEvidenceObservation>()
        var version = MarketplaceEconomicEvidenceVersion.ZERO
        updates.forEach { update ->
            when (val result = MarketplaceIndependentEconomicEvidenceMerger.apply(evidence, update)) {
                is MarketplaceIndependentEconomicEvidenceResult.Applied -> {
                    evidence = result.evidence; version = version.next()
                    members += MarketplaceEconomicObservationLineage.membersOf(update, version)
                }
                is MarketplaceIndependentEconomicEvidenceResult.Duplicate -> Unit
                else -> error("invalid fixture")
            }
        }
        return VersionedMarketplaceIndependentEconomicEvidence(evidence, version, MarketplaceEconomicObservationLineage(subject, members))
    }
    private fun snapshot(value: VersionedMarketplaceIndependentEconomicEvidence, trigger: Long = 8,
        policy: MarketplaceEconomicTruthAssemblyPolicyVersion = MarketplaceEconomicTruthAssembler.POLICY_VERSION): ConsumedEconomicEvidenceSnapshot {
        val input = ConsumedEconomicEvidenceSnapshot.capture(value, ChangeSequenceCheckpoint(trigger))
        val original = MarketplaceEconomicTruthAssembler.assemble(value.evidence)
        val assembly = when (original) {
            is MarketplaceEconomicTruthAssemblyResult.NotReady -> MarketplaceEconomicTruthAssemblyResult.NotReady(original.reasons, policy)
            is MarketplaceEconomicTruthAssemblyResult.Ready -> original.copy(assemblyPolicyVersion = policy)
        }
        val state = when (assembly) {
            is MarketplaceEconomicTruthAssemblyResult.NotReady -> MarketplaceSalesIntelligenceState.Unresolved(policy, assembly.reasons)
            is MarketplaceEconomicTruthAssemblyResult.Ready -> {
                val calculation = MarketplaceEconomicTruthCalculator.calculate(assembly.order)
                MarketplaceSalesIntelligenceState.Calculated(policy, calculationPolicyVersionOf(calculation), calculation)
            }
        }
        return input.finalize(assembly, state, time)
    }

    @Test fun `fact keeps exact identity version family kind and recorded time`() {
        val value = replay(fact(10))
        val member = assertNotNull(value.observationLineage).observations.single()
        assertEquals(id(10), member.observationId); assertEquals(MarketplaceEconomicEvidenceVersion(1), member.evidenceVersion)
        assertEquals(MarketplaceEconomicObservationIdentifierKind.FACT, member.identifierKind)
        assertEquals(MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER, member.family); assertEquals(time, member.recordedAt)
    }
    @Test fun `each fact retains own version not aggregate current version`() {
        val value = replay(fact(10), fact(11))
        assertEquals(2L, value.version.valueForPersistence())
        assertEquals(listOf(1L, 2L), assertNotNull(value.observationLineage).observations.map { it.evidenceVersion.valueForPersistence() })
    }
    @Test fun `attempt retains defined domain family and remains contextual for absence`() {
        val value = snapshot(replay(attempt(20)))
        assertEquals(EconomicOrderAssemblyState.NOT_READY, value.orderAssemblyState)
        assertTrue(value.componentCoverage.isEmpty())
        assertEquals(id(20), value.members.single().observation.observationId)
        assertEquals(MarketplaceEconomicObservationIdentifierKind.ATTEMPT, value.members.single().observation.identifierKind)
        assertEquals(MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER, value.members.single().observation.family)
        assertEquals(ConsumedEconomicEvidenceContextRole.ATTEMPT_CONTEXT, value.members.single().contextRole)
        assertEquals(setOf(MarketplaceEconomicTruthAssemblyNotReadyReason.ORDER_OCCURRED_AT_UNRESOLVED),
            assertIs<MarketplaceSalesIntelligenceState.Unresolved>(value.outcome).reasons)
    }
    @Test fun `correction keeps historical fact edge and replacement sharing update version`() {
        val old = snapshot(replay(fact(10)))
        val corrected = snapshot(replay(fact(10), correction(10, 11, 12)))
        val byId = corrected.members.associateBy { it.observation.observationId }
        assertEquals(ConsumedEconomicEvidenceContextRole.HISTORICAL_SUPERSEDED_FACT, byId.getValue(id(10)).contextRole)
        assertEquals(1L, byId.getValue(id(10)).observation.evidenceVersion.valueForPersistence())
        assertEquals(ConsumedEconomicEvidenceContextRole.CONSUMED_ACTIVE_FACT, byId.getValue(id(11)).contextRole)
        val edge = byId.getValue(id(12))
        assertEquals(ConsumedEconomicEvidenceContextRole.CORRECTION_CONTEXT, edge.contextRole)
        assertEquals(id(10), edge.observation.supersedesObservationId); assertEquals(id(11), edge.observation.replacementObservationId)
        assertEquals(edge.observation.evidenceVersion, byId.getValue(id(11)).observation.evidenceVersion)
        assertEquals(MarketplaceEconomicObservationIdentifierKind.FACT, byId.getValue(id(11)).observation.identifierKind)
        assertEquals(ConsumedEconomicEvidenceContextRole.CONSUMED_ACTIVE_FACT, old.members.single().contextRole)
    }
    @Test fun `chained corrections classify by accepted active set rather than row order`() {
        val value = snapshot(replay(fact(10), correction(10, 11, 12), correction(11, 13, 14)))
        assertEquals(setOf(id(13)), value.members.filter { it.contextRole == ConsumedEconomicEvidenceContextRole.CONSUMED_ACTIVE_FACT }.map { it.observation.observationId }.toSet())
        assertEquals(2, value.members.count { it.contextRole == ConsumedEconomicEvidenceContextRole.HISTORICAL_SUPERSEDED_FACT })
    }
    @Test fun `duplicate replay creates no new member or version`() {
        val value = replay(fact(10), fact(10))
        assertEquals(1L, value.version.valueForPersistence()); assertEquals(1, assertNotNull(value.observationLineage).observations.size)
    }
    @Test fun `lineage rejects duplicates missing foreign subject wrong kind version and edge`() {
        val value = replay(fact(10), correction(10, 11, 12))
        val members = assertNotNull(value.observationLineage).observations
        assertFailsWith<IllegalArgumentException> { MarketplaceEconomicObservationLineage(subject, members + members.first()) }
        fun reject(changed: List<VersionedEconomicEvidenceObservation>, changedSubject: MarketplaceEconomicEvidenceSubject = subject) {
            assertFailsWith<IllegalArgumentException> { VersionedMarketplaceIndependentEconomicEvidence(value.evidence, value.version,
                MarketplaceEconomicObservationLineage(changedSubject, changed)) }
        }
        reject(members.drop(1))
        reject(members, subject.copy(organizationId = OrganizationId(UUID(0, 99))))
        reject(members, subject.copy(orderId = MarketplaceOrderId(UUID(0, 99))))
        reject(members.map { if (it.observationId == id(10)) it.copy(identifierKind = MarketplaceEconomicObservationIdentifierKind.ATTEMPT) else it })
        reject(members.map { if (it.observationId == id(10)) it.copy(evidenceVersion = MarketplaceEconomicEvidenceVersion(2)) else it })
        reject(members.map { if (it.observationId == id(12)) it.copy(supersedesObservationId = id(99)) else it })
        assertFailsWith<IllegalArgumentException> { members.first().copy(supersedesObservationId = id(10)) }
    }
    @Test fun `snapshot refuses unavailable lineage rather than inferring member versions`() {
        val value = replay(fact(10))
        assertFailsWith<IllegalArgumentException> { snapshot(VersionedMarketplaceIndependentEconomicEvidence(value.evidence, value.version)) }
    }
    @Test fun `canonical manifest ignores membership insertion order`() {
        val value = replay(fact(10), correction(10, 11, 12), attempt(20))
        val reversed = VersionedMarketplaceIndependentEconomicEvidence(value.evidence, value.version,
            MarketplaceEconomicObservationLineage(subject, assertNotNull(value.observationLineage).observations.reversed()))
        assertEquals(snapshot(value).manifestDigest, snapshot(reversed).manifestDigest)
        assertContentEquals(snapshot(value).canonicalManifest(), snapshot(reversed).canonicalManifest())
    }
    @Test fun `manifest binds exact member version kind role and family`() {
        val value = snapshot(replay(fact(10)))
        val member = value.members.single()
        val variants = listOf(
            member.copy(observation = member.observation.copy(evidenceVersion = MarketplaceEconomicEvidenceVersion(2))),
            member.copy(observation = member.observation.copy(identifierKind = MarketplaceEconomicObservationIdentifierKind.ATTEMPT)),
            member.copy(contextRole = ConsumedEconomicEvidenceContextRole.HISTORICAL_SUPERSEDED_FACT),
            member.copy(observation = member.observation.copy(family = MarketplaceEconomicEvidenceFamily.PRODUCT_COST)))
        variants.forEach { assertFalse(value.canonicalManifest().contentEquals(value.canonicalManifest(listOf(it)))) }
    }
    @Test fun `manifest binds policy trigger typed outcome and subject`() {
        val value = replay(fact(10))
        assertNotEquals(snapshot(value).manifestDigest, snapshot(value, trigger = 9).manifestDigest)
        assertNotEquals(snapshot(value).manifestDigest, snapshot(value, policy = MarketplaceEconomicTruthAssemblyPolicyVersion("fixture/2")).manifestDigest)
        assertNotEquals(snapshot(replay(attempt(20))).manifestDigest, snapshot(value).manifestDigest)
        assertEquals(64, snapshot(value).manifestDigest.length)
    }
    @Test fun `same membership different typed reasons change manifest`() {
        val value = replay(attempt(20))
        fun outcome(reason: MarketplaceEconomicTruthAssemblyNotReadyReason): ConsumedEconomicEvidenceSnapshot {
            val policy = MarketplaceEconomicTruthAssembler.POLICY_VERSION
            return ConsumedEconomicEvidenceSnapshot.capture(value, ChangeSequenceCheckpoint(8)).finalize(
                MarketplaceEconomicTruthAssemblyResult.NotReady(setOf(reason), policy),
                MarketplaceSalesIntelligenceState.Unresolved(policy, setOf(reason)), time)
        }
        assertNotEquals(outcome(MarketplaceEconomicTruthAssemblyNotReadyReason.ORDER_OCCURRED_AT_UNRESOLVED).manifestDigest,
            outcome(MarketplaceEconomicTruthAssemblyNotReadyReason.ORDER_OCCURRED_AT_CONFLICT).manifestDigest)
    }
    @Test fun `framing distinguishes null empty embedded delimiters and unicode`() {
        val cases = listOf(listOf<String?>(null), listOf(""), listOf("a", "bc"), listOf("ab", "c"),
            listOf("a:1", "b"), listOf("a", "1:b"), listOf("?"), listOf("e"), emptyList())
        assertEquals(cases.size, cases.map { EconomicEvidenceManifestFraming.encode(it).toList() }.toSet().size)
    }
    @Test fun `collections and calculation outcome are defensively frozen`() {
        val value = replay(fact(10))
        val input = assertNotNull(value.observationLineage).observations.toMutableList()
        val lineage = MarketplaceEconomicObservationLineage(subject, input); input.clear()
        assertEquals(1, lineage.observations.size)
        assertFailsWith<UnsupportedOperationException> { (lineage.observations as MutableList).clear() }
        val snapshot = snapshot(value)
        assertFailsWith<UnsupportedOperationException> { (snapshot.members as MutableList).clear() }
        assertFailsWith<UnsupportedOperationException> { (snapshot.componentCoverage as MutableMap).clear() }
        val calculation = assertIs<MarketplaceEconomicTruthCalculationResult.Incomplete>(assertIs<MarketplaceSalesIntelligenceState.Calculated>(snapshot.outcome).calculationResult)
        assertFailsWith<UnsupportedOperationException> { (calculation.missingTypes as MutableList).clear() }
        assertEquals("[REDACTED]", snapshot.toString())
    }
    @Test fun `component present yields partial even when observation declares complete`() {
        val component = EconomicComponent(subject.organizationId, EconomicComponentId(UUID(0, 90)), subject.orderId,
            EconomicComponentType.REVENUE, EconomicDirection.ADDITION, MarketplaceMoney.parse(subject.currency, "10"),
            source, time, EconomicEvidenceQuality.CONFIRMED)
        val update = MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact(MarketplaceIndependentEconomicFact.Component(
            MarketplaceEconomicComponentObservation(id(91), subject, MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
                component, EconomicComponentCoverage.COMPLETE, time)))
        val value = snapshot(replay(fact(10), update))
        assertEquals(EconomicComponentCoverage.PARTIAL, value.componentCoverage[EconomicComponentType.REVENUE])
        assertTrue(value.componentCoverage.filterKeys { it != EconomicComponentType.REVENUE }.values.all { it == EconomicComponentCoverage.MISSING })
        val result = assertIs<MarketplaceEconomicTruthCalculationResult.Incomplete>(assertIs<MarketplaceSalesIntelligenceState.Calculated>(value.outcome).calculationResult)
        assertEquals(listOf(EconomicComponentType.REVENUE), result.partialTypes)
    }
    @Test fun `absence claims enumerate policy boundary without invented missing observations`() {
        val snapshot = snapshot(replay(fact(10)))
        assertEquals(EconomicOrderAssemblyState.READY, snapshot.orderAssemblyState)
        assertEquals(EconomicComponentType.entries.toSet(), snapshot.componentCoverage.keys)
        assertTrue(snapshot.componentCoverage.values.all { it == EconomicComponentCoverage.MISSING })
        assertEquals(listOf(id(10)), snapshot.members.map { it.observation.observationId })
    }
    @Test fun `permuted manifests remain stable for realistic attempt counts`() {
        val value = replay(*(1L..1000L).map { attempt(it + 100) }.toTypedArray())
        val started = System.nanoTime()
        val baseline = snapshot(value)
        val elapsed = System.nanoTime() - started
        println("MANIFEST_BENCHMARK members=1000 bytes=${baseline.canonicalManifest().size} buildAndDigestNanos=$elapsed")
        repeat(10) { seed ->
            val permuted = VersionedMarketplaceIndependentEconomicEvidence(value.evidence, value.version,
                MarketplaceEconomicObservationLineage(subject, assertNotNull(value.observationLineage).observations.shuffled(kotlin.random.Random(seed))))
            assertEquals(baseline.manifestDigest, snapshot(permuted).manifestDigest)
        }
        assertTrue(baseline.canonicalManifest().size < 250_000)
    }
    @Test fun `persistence rehydration preserves bytes and never shares mutable storage`() {
        val original=snapshot(replay(fact(10),correction(10,11,12)))
        val members=original.members.reversed().toMutableList()
        val coverage=original.componentCoverage.toMutableMap()
        val stored=ConsumedEconomicEvidenceSnapshot.rehydratePersisted(original.subject,original.readEvidenceVersion,original.triggerChangeSequence,original.projectedAt,original.outcome,members,coverage)
        members.clear();coverage.clear()
        assertContentEquals(original.canonicalManifestForPersistence(),stored.canonicalManifestForPersistence())
        val exposed=stored.canonicalManifestForPersistence();exposed[0]=(exposed[0].toInt() xor 1).toByte()
        assertFalse(exposed.contentEquals(stored.canonicalManifestForPersistence()))
        assertEquals(original.manifestDigest,stored.manifestDigest)
    }
    @Test fun `rehydration rejects incorrect role scope outcome and repeated correction target`() {
        val original=snapshot(replay(fact(10)))
        fun reconstruct(members: List<ConsumedEconomicEvidenceMember> = original.members, state: MarketplaceSalesIntelligenceState = original.outcome) =
            ConsumedEconomicEvidenceSnapshot.rehydratePersisted(original.subject,original.readEvidenceVersion,original.triggerChangeSequence,original.projectedAt,state,members,original.componentCoverage)
        assertFailsWith<IllegalArgumentException> { reconstruct(original.members.map { it.copy(contextRole=ConsumedEconomicEvidenceContextRole.ATTEMPT_CONTEXT) }) }
        val state=assertIs<MarketplaceSalesIntelligenceState.Calculated>(original.outcome)
        val calculation=assertIs<MarketplaceEconomicTruthCalculationResult.Incomplete>(state.calculationResult)
        assertFailsWith<IllegalArgumentException> { reconstruct(state=state.copy(calculationResult=calculation.copy(organizationId=OrganizationId(UUID(0,99))))) }
        val chain=snapshot(replay(fact(10),correction(10,11,12),correction(11,13,14)))
        val bad=chain.members.map { if(it.observation.observationId==id(14)) it.copy(observation=it.observation.copy(supersedesObservationId=id(10))) else it }
        assertFailsWith<IllegalArgumentException> { ConsumedEconomicEvidenceSnapshot.rehydratePersisted(chain.subject,chain.readEvidenceVersion,chain.triggerChangeSequence,chain.projectedAt,chain.outcome,bad,chain.componentCoverage) }
    }

}
