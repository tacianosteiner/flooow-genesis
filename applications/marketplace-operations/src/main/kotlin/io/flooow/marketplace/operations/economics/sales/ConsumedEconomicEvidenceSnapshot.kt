package io.flooow.marketplace.operations.economics.sales

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.security.MessageDigest
import java.time.Instant
import java.util.Collections

enum class ConsumedEconomicEvidenceContextRole {
    CONSUMED_ACTIVE_FACT, HISTORICAL_SUPERSEDED_FACT, CORRECTION_CONTEXT, ATTEMPT_CONTEXT
}

data class ConsumedEconomicEvidenceMember(
    val observation: VersionedEconomicEvidenceObservation,
    val contextRole: ConsumedEconomicEvidenceContextRole
) { override fun toString(): String = "[REDACTED]" }

enum class EconomicOrderAssemblyState { READY, NOT_READY }

/** In-memory consumed boundary; neither published history nor retrieval authority. */
class ConsumedEconomicEvidenceSnapshot private constructor(
    val subject: MarketplaceEconomicEvidenceSubject,
    val readEvidenceVersion: MarketplaceEconomicEvidenceVersion,
    val triggerChangeSequence: ChangeSequenceCheckpoint,
    val projectedAt: Instant,
    outcome: MarketplaceSalesIntelligenceState,
    members: Collection<ConsumedEconomicEvidenceMember>,
    coverage: Map<EconomicComponentType, EconomicComponentCoverage>
) {
    val outcome: MarketplaceSalesIntelligenceState = freezeOutcome(outcome)
    val members: List<ConsumedEconomicEvidenceMember> = Collections.unmodifiableList(
        members.sortedBy { it.observation.observationId }
    )
    val componentCoverage: Map<EconomicComponentType, EconomicComponentCoverage> =
        Collections.unmodifiableMap(coverage.toMap())
    val orderAssemblyState = if (outcome is MarketplaceSalesIntelligenceState.Unresolved)
        EconomicOrderAssemblyState.NOT_READY else EconomicOrderAssemblyState.READY
    init {
        require(readEvidenceVersion > MarketplaceEconomicEvidenceVersion.ZERO)
        require(triggerChangeSequence > ChangeSequenceCheckpoint.NONE && projectedAt.nano % 1_000 == 0)
        require(this.members.map { it.observation.observationId }.toSet().size == this.members.size)
        val byId = this.members.associateBy { it.observation.observationId }
        val observations = this.members.map { it.observation }
        val groups = observations.groupBy { it.evidenceVersion }
        require(groups.size.toLong() == readEvidenceVersion.valueForPersistence())
        require(groups.keys.sorted().withIndex().all { (index, version) -> version.valueForPersistence() == index.toLong() + 1 })
        val superseded = observations.filter { it.identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION }.map { it.supersedesObservationId }.toSet()
        val edges = observations.filter { it.identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION }
        require(edges.map { it.supersedesObservationId }.distinct().size == edges.size)
        edges.forEach { edge ->
            val old = byId.getValue(requireNotNull(edge.supersedesObservationId)).observation
            val replacement = byId.getValue(requireNotNull(edge.replacementObservationId)).observation
            require(old.identifierKind == MarketplaceEconomicObservationIdentifierKind.FACT && old.evidenceVersion < edge.evidenceVersion)
            require(replacement.identifierKind == MarketplaceEconomicObservationIdentifierKind.FACT && replacement.evidenceVersion == edge.evidenceVersion)
            require(!edge.recordedAt.isBefore(old.recordedAt) && !edge.recordedAt.isBefore(replacement.recordedAt))
            require(edge.observationId != old.observationId && edge.observationId != replacement.observationId && old.observationId != replacement.observationId)
        }
        groups.values.forEach { values ->
            val correction = values.filter { it.identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION }
            require(if (correction.isEmpty()) values.size == 1 else correction.size == 1 && values.size == 2 && values.any { it.observationId == correction.single().replacementObservationId })
        }
        this.members.forEach { member ->
            val expected = when(member.observation.identifierKind) {
                MarketplaceEconomicObservationIdentifierKind.FACT -> if(member.observation.observationId in superseded) ConsumedEconomicEvidenceContextRole.HISTORICAL_SUPERSEDED_FACT else ConsumedEconomicEvidenceContextRole.CONSUMED_ACTIVE_FACT
                MarketplaceEconomicObservationIdentifierKind.ATTEMPT -> ConsumedEconomicEvidenceContextRole.ATTEMPT_CONTEXT
                MarketplaceEconomicObservationIdentifierKind.CORRECTION -> ConsumedEconomicEvidenceContextRole.CORRECTION_CONTEXT
            }
            require(member.contextRole == expected)
        }
        require(componentCoverage.values.none { it == EconomicComponentCoverage.NOT_APPLICABLE })
        when(val state = this.outcome) {
            is MarketplaceSalesIntelligenceState.Unresolved -> require(componentCoverage.isEmpty())
            is MarketplaceSalesIntelligenceState.Calculated -> {
                val components = when(val result = state.calculationResult) {
                    is MarketplaceEconomicTruthCalculationResult.Incomplete -> {
                        require(result.organizationId == subject.organizationId && result.orderId == subject.orderId)
                        require(result.missingTypes.distinct().size == result.missingTypes.size && result.partialTypes.distinct().size == result.partialTypes.size)
                        require(result.missingTypes.toSet() == componentCoverage.filterValues { it == EconomicComponentCoverage.MISSING }.keys)
                        require(result.partialTypes.toSet() == componentCoverage.filterValues { it == EconomicComponentCoverage.PARTIAL }.keys)
                        require(result.missingTypes.isNotEmpty() || result.partialTypes.isNotEmpty())
                        result.suppliedComponents
                    }
                    is MarketplaceEconomicTruthCalculationResult.Complete -> {
                        require(result.result.organizationId == subject.organizationId && result.result.orderId == subject.orderId)
                        require(result.result.marketplace == subject.marketplace && result.result.externalOrderId == subject.externalOrderId && result.result.currency == subject.currency)
                        require(result.result.orderOccurredAt.nano % 1_000 == 0)
                        require(listOf(result.result.grossRevenue,result.result.totalMarketplaceFees,result.result.totalShipping,result.result.totalAdvertising,
                            result.result.totalTaxes,result.result.totalProductCost,result.result.totalFinancialCost,result.result.totalOtherAdjustments,result.result.contribution).all { it.currency == subject.currency })
                        require(componentCoverage.values.all { it == EconomicComponentCoverage.COMPLETE })
                        result.result.components
                    }
                }
                require(components.map { it.id }.distinct().size == components.size)
                require(components.all { it.organizationId == subject.organizationId && it.orderId == subject.orderId && it.magnitude.currency == subject.currency && it.occurredAt.nano % 1_000 == 0 })
            }
        }
    }
    /** Fresh canonical bytes for persistence integrity; no execution/retrieval authority. */
    fun canonicalManifestForPersistence(): ByteArray = canonicalManifest()

    val manifestDigest: String = MessageDigest.getInstance("SHA-256").digest(canonicalManifest())
        .joinToString("") { HEX[it.toInt().and(255).ushr(4)].toString() + HEX[it.toInt().and(15)] }

    internal fun canonicalManifest(manifestMembers: List<ConsumedEconomicEvidenceMember> = members): ByteArray {
        val fields = mutableListOf<String?>()
        fun field(value: Any?) { fields += value?.toString() }
        field("flooow-consumed-economic-evidence/1")
        field(subject.organizationId.value); field(subject.orderId.value)
        field(subject.marketplace.value); field(subject.externalOrderId.value); field(subject.currency.code)
        field(readEvidenceVersion.valueForPersistence()); field(triggerChangeSequence.valueForPersistence())
        field(projectedAt.epochSecond); field(projectedAt.nano)
        field(outcome.assemblyPolicyVersion.value)
        field((outcome as? MarketplaceSalesIntelligenceState.Calculated)?.calculationPolicyVersion?.value)
        field(orderAssemblyState.name)
        val reasons = (outcome as? MarketplaceSalesIntelligenceState.Unresolved)?.reasons.orEmpty().sortedBy { it.name }
        field(reasons.size); reasons.forEach { field(it.name) }
        field(componentCoverage.size)
        componentCoverage.entries.sortedBy { it.key.name }.forEach { field(it.key.name); field(it.value.name) }
        field(manifestMembers.size)
        manifestMembers.sortedBy { it.observation.observationId }.forEach {
            val member = it.observation
            field(member.observationId.valueForPersistence()); field(member.evidenceVersion.valueForPersistence())
            field(member.identifierKind.name); field(member.family?.name); field(it.contextRole.name)
            field(member.recordedAt.epochSecond); field(member.recordedAt.nano)
            field(member.supersedesObservationId?.valueForPersistence()); field(member.replacementObservationId?.valueForPersistence())
        }
        fun money(value: MarketplaceMoney) { field(value.currency.code); field(value.amount.toPlainString()) }
        fun components(values: List<EconomicComponent>) {
            field(values.size)
            values.sortedBy { it.id.value.toString() }.forEach {
                field(it.organizationId.value); field(it.orderId.value); field(it.id.value)
                field(it.type.name); field(it.direction.name); money(it.magnitude)
                field(it.source.kind.name); field(it.source.systemKey.value)
                when (val reference = it.source.externalReference) {
                    is EconomicExternalReferenceState.Present -> { field("PRESENT"); field(reference.reference.value) }
                    is EconomicExternalReferenceState.Absent -> { field("ABSENT"); field(reference.reason.name) }
                }
                field(it.occurredAt.epochSecond); field(it.occurredAt.nano); field(it.quality.name)
            }
        }
        when (val state = outcome) {
            is MarketplaceSalesIntelligenceState.Unresolved -> field("UNRESOLVED")
            is MarketplaceSalesIntelligenceState.Calculated -> when (val calculation = state.calculationResult) {
                is MarketplaceEconomicTruthCalculationResult.Incomplete -> {
                    field("INCOMPLETE"); field(calculation.organizationId.value); field(calculation.orderId.value)
                    field(calculation.missingTypes.size); calculation.missingTypes.sortedBy { it.name }.forEach { field(it.name) }
                    field(calculation.partialTypes.size); calculation.partialTypes.sortedBy { it.name }.forEach { field(it.name) }
                    components(calculation.suppliedComponents)
                }
                is MarketplaceEconomicTruthCalculationResult.Complete -> {
                    field("COMPLETE")
                    val result = calculation.result
                    field(result.organizationId.value); field(result.orderId.value)
                    field(result.marketplace.value); field(result.externalOrderId.value)
                    field(result.orderOccurredAt.epochSecond); field(result.orderOccurredAt.nano); field(result.currency.code)
                    listOf(result.grossRevenue, result.totalMarketplaceFees, result.totalShipping, result.totalAdvertising,
                        result.totalTaxes, result.totalProductCost, result.totalFinancialCost, result.totalOtherAdjustments,
                        result.contribution).forEach(::money)
                    when (val margin = result.contributionMargin) {
                        is ContributionMargin.Defined -> { field("DEFINED"); field(margin.decimalValue.toPlainString()) }
                        is ContributionMargin.Undefined -> { field("UNDEFINED"); field(margin.reason.name) }
                    }
                    field(result.truthQuality.name); components(result.components)
                }
            }
        }
        return EconomicEvidenceManifestFraming.encode(fields)
    }
    override fun toString(): String = "[REDACTED]"

    companion object {
        private const val HEX = "0123456789abcdef"
        /** Validates stored typed context only; never runs an assembler or calculator. */
        fun rehydratePersisted(subject: MarketplaceEconomicEvidenceSubject, readEvidenceVersion: MarketplaceEconomicEvidenceVersion,
            triggerChangeSequence: ChangeSequenceCheckpoint, projectedAt: Instant, outcome: MarketplaceSalesIntelligenceState,
            members: Collection<ConsumedEconomicEvidenceMember>, coverage: Map<EconomicComponentType, EconomicComponentCoverage>): ConsumedEconomicEvidenceSnapshot =
            ConsumedEconomicEvidenceSnapshot(subject, readEvidenceVersion, triggerChangeSequence, projectedAt, outcome, members, coverage)

        private fun freezeOutcome(state: MarketplaceSalesIntelligenceState): MarketplaceSalesIntelligenceState = when(state) {
            is MarketplaceSalesIntelligenceState.Unresolved -> state
            is MarketplaceSalesIntelligenceState.Calculated -> state.copy(calculationResult = when(val result = state.calculationResult) {
                is MarketplaceEconomicTruthCalculationResult.Incomplete -> result.copy(
                    missingTypes = Collections.unmodifiableList(result.missingTypes.toList()), partialTypes = Collections.unmodifiableList(result.partialTypes.toList()),
                    suppliedComponents = Collections.unmodifiableList(result.suppliedComponents.toList()))
                is MarketplaceEconomicTruthCalculationResult.Complete -> result.copy(result = result.result.copy(components = Collections.unmodifiableList(result.result.components.toList())))
            })
        }
        fun capture(versioned: VersionedMarketplaceIndependentEconomicEvidence, trigger: ChangeSequenceCheckpoint): Input {
            require(trigger > ChangeSequenceCheckpoint.NONE)
            val lineage = requireNotNull(versioned.observationLineage) { "Exact durable membership unavailable" }
            lineage.validate(versioned.evidence, versioned.version)
            return Input(versioned, trigger)
        }
    }

    class Input internal constructor(
        private val versioned: VersionedMarketplaceIndependentEconomicEvidence,
        private val trigger: ChangeSequenceCheckpoint
    ) {
        fun finalize(assembly: MarketplaceEconomicTruthAssemblyResult, state: MarketplaceSalesIntelligenceState,
            projectedAt: Instant): ConsumedEconomicEvidenceSnapshot {
            require(projectedAt.nano % 1_000 == 0)
            require(assembly.assemblyPolicyVersion == state.assemblyPolicyVersion)
            val evidence = versioned.evidence
            val coverage = when (assembly) {
                is MarketplaceEconomicTruthAssemblyResult.NotReady -> {
                    require(state is MarketplaceSalesIntelligenceState.Unresolved && state.reasons == assembly.reasons)
                    emptyMap()
                }
                is MarketplaceEconomicTruthAssemblyResult.Ready -> {
                    require(state is MarketplaceSalesIntelligenceState.Calculated)
                    require(assembly.order.organizationId == evidence.subject.organizationId && assembly.order.id == evidence.subject.orderId)
                    when (val result = state.calculationResult) {
                        is MarketplaceEconomicTruthCalculationResult.Incomplete -> {
                            require(result.organizationId == evidence.subject.organizationId && result.orderId == evidence.subject.orderId)
                            require(result.suppliedComponents == assembly.order.components)
                            require(result.missingTypes.toSet() == assembly.order.coverage.filterValues { it == EconomicComponentCoverage.MISSING }.keys)
                            require(result.partialTypes.toSet() == assembly.order.coverage.filterValues { it == EconomicComponentCoverage.PARTIAL }.keys)
                        }
                        is MarketplaceEconomicTruthCalculationResult.Complete -> {
                            require(result.result.organizationId == evidence.subject.organizationId && result.result.orderId == evidence.subject.orderId)
                            require(result.result.components == assembly.order.components)
                            require(assembly.order.coverage.values.none { it == EconomicComponentCoverage.MISSING || it == EconomicComponentCoverage.PARTIAL })
                        }
                    }
                    assembly.order.coverage.filterValues { it != EconomicComponentCoverage.NOT_APPLICABLE }
                }
            }
            val activeIds = evidence.activeFacts.mapTo(mutableSetOf()) { it.id }
            val members = requireNotNull(versioned.observationLineage).observations.map {
                val role = when (it.identifierKind) {
                    MarketplaceEconomicObservationIdentifierKind.FACT -> if (it.observationId in activeIds)
                        ConsumedEconomicEvidenceContextRole.CONSUMED_ACTIVE_FACT else ConsumedEconomicEvidenceContextRole.HISTORICAL_SUPERSEDED_FACT
                    MarketplaceEconomicObservationIdentifierKind.CORRECTION -> ConsumedEconomicEvidenceContextRole.CORRECTION_CONTEXT
                    MarketplaceEconomicObservationIdentifierKind.ATTEMPT -> ConsumedEconomicEvidenceContextRole.ATTEMPT_CONTEXT
                }
                ConsumedEconomicEvidenceMember(it, role)
            }
            val frozenState = when (state) {
                is MarketplaceSalesIntelligenceState.Unresolved -> state
                is MarketplaceSalesIntelligenceState.Calculated -> state.copy(calculationResult = when (val result = state.calculationResult) {
                    is MarketplaceEconomicTruthCalculationResult.Incomplete -> result.copy(
                        missingTypes = Collections.unmodifiableList(result.missingTypes.toList()),
                        partialTypes = Collections.unmodifiableList(result.partialTypes.toList()),
                        suppliedComponents = Collections.unmodifiableList(result.suppliedComponents.toList()))
                    is MarketplaceEconomicTruthCalculationResult.Complete -> result.copy(result = result.result.copy(
                        components = Collections.unmodifiableList(result.result.components.toList())))
                })
            }
            return ConsumedEconomicEvidenceSnapshot(evidence.subject, versioned.version, trigger, projectedAt, frozenState, members, coverage)
        }
    }
}

/** Signed big-endian byte length; -1 null, 0 empty, UTF-8 bytes otherwise. */
internal object EconomicEvidenceManifestFraming {
    fun encode(fields: List<String?>): ByteArray {
        val bytes = ByteArrayOutputStream()
        DataOutputStream(bytes).use { output ->
            fields.forEach { value ->
                if (value == null) output.writeInt(-1) else {
                    val encoded = value.toByteArray(Charsets.UTF_8)
                    output.writeInt(encoded.size); output.write(encoded)
                }
            }
        }
        return bytes.toByteArray()
    }
}
