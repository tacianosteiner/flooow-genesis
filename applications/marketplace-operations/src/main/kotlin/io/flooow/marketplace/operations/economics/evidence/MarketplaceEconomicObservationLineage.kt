package io.flooow.marketplace.operations.economics.evidence

import java.time.Instant
import java.util.Collections

/** Identifier kind, not the change kind: correction replacements remain FACT. */
enum class MarketplaceEconomicObservationIdentifierKind { FACT, ATTEMPT, CORRECTION }

data class VersionedEconomicEvidenceObservation(
    val observationId: MarketplaceEconomicEvidenceObservationId,
    val evidenceVersion: MarketplaceEconomicEvidenceVersion,
    val identifierKind: MarketplaceEconomicObservationIdentifierKind,
    val family: MarketplaceEconomicEvidenceFamily?,
    val recordedAt: Instant,
    val supersedesObservationId: MarketplaceEconomicEvidenceObservationId? = null,
    val replacementObservationId: MarketplaceEconomicEvidenceObservationId? = null
) {
    init {
        require(evidenceVersion > MarketplaceEconomicEvidenceVersion.ZERO)
        require(recordedAt.nano % 1_000 == 0)
        require((identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION) ==
            (supersedesObservationId != null && replacementObservationId != null))
        require((supersedesObservationId == null) == (replacementObservationId == null))
        require((identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION) == (family == null))
    }
    override fun toString(): String = "[REDACTED]"
}

/** Complete replay membership. Payloads, source times and source identities stay in the aggregate. */
class MarketplaceEconomicObservationLineage(
    val subject: MarketplaceEconomicEvidenceSubject,
    observations: Collection<VersionedEconomicEvidenceObservation>
) {
    val observations: List<VersionedEconomicEvidenceObservation> = Collections.unmodifiableList(
        observations.sortedWith(compareBy<VersionedEconomicEvidenceObservation> { it.evidenceVersion }
            .thenBy { it.observationId })
    )
    init { require(this.observations.map { it.observationId }.toSet().size == this.observations.size) }

    fun validate(evidence: MarketplaceIndependentEconomicEvidence, version: MarketplaceEconomicEvidenceVersion) {
        require(subject == evidence.subject)
        val byId = observations.associateBy { it.observationId }
        require(byId.keys == (evidence.facts.map { it.id } + evidence.attempts.map { it.id } +
            evidence.corrections.map { it.id }).toSet())
        require(observations.all { it.evidenceVersion <= version })
        evidence.facts.forEach { fact ->
            val member = byId.getValue(fact.id)
            require(member.identifierKind == MarketplaceEconomicObservationIdentifierKind.FACT)
            require(member.family == fact.family && member.recordedAt == fact.observedAt)
        }
        evidence.attempts.forEach { attempt ->
            val member = byId.getValue(attempt.id)
            require(member.identifierKind == MarketplaceEconomicObservationIdentifierKind.ATTEMPT)
            require(member.family == attempt.family && member.recordedAt == attempt.attemptedAt)
        }
        evidence.corrections.forEach { correction ->
            val member = byId.getValue(correction.id)
            require(member.identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION)
            require(member.recordedAt == correction.observedAt)
            require(member.supersedesObservationId == correction.supersedesObservationId)
            require(member.replacementObservationId == correction.replacement.id)
            require(byId.getValue(correction.replacement.id).evidenceVersion == member.evidenceVersion)
            require(byId.getValue(correction.supersedesObservationId).evidenceVersion < member.evidenceVersion)
        }
        val grouped = observations.groupBy { it.evidenceVersion }
        require(grouped.size.toLong() == version.valueForPersistence())
        require(grouped.keys.sorted().withIndex().all { (index, value) -> value.valueForPersistence() == index.toLong() + 1 })
        grouped.values.forEach { members ->
            if (members.any { it.identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION }) {
                require(members.size == 2)
                val correction = members.single { it.identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION }
                require(members.single { it.identifierKind == MarketplaceEconomicObservationIdentifierKind.FACT }.observationId == correction.replacementObservationId)
            } else require(members.size == 1)
        }
    }
    override fun equals(other: Any?): Boolean = other is MarketplaceEconomicObservationLineage &&
        subject == other.subject && observations == other.observations
    override fun hashCode(): Int = 31 * subject.hashCode() + observations.hashCode()
    override fun toString(): String = "[REDACTED]"

    companion object {
        /** Call only for an accepted durable update (or explicit test fixture), never a duplicate. */
        fun membersOf(update: MarketplaceIndependentEconomicEvidenceUpdate, version: MarketplaceEconomicEvidenceVersion): List<VersionedEconomicEvidenceObservation> {
            fun fact(value: MarketplaceIndependentEconomicFact) = VersionedEconomicEvidenceObservation(
                value.id, version, MarketplaceEconomicObservationIdentifierKind.FACT, value.family, value.observedAt
            )
            return when (update) {
                is MarketplaceIndependentEconomicEvidenceUpdate.ObserveFact -> listOf(fact(update.fact))
                is MarketplaceIndependentEconomicEvidenceUpdate.RecordAttempt -> listOf(VersionedEconomicEvidenceObservation(
                    update.attempt.id, version, MarketplaceEconomicObservationIdentifierKind.ATTEMPT,
                    update.attempt.family, update.attempt.attemptedAt
                ))
                is MarketplaceIndependentEconomicEvidenceUpdate.Correct -> listOf(
                    VersionedEconomicEvidenceObservation(update.correction.id, version,
                        MarketplaceEconomicObservationIdentifierKind.CORRECTION, null, update.correction.observedAt,
                        update.correction.supersedesObservationId, update.correction.replacement.id),
                    fact(update.correction.replacement)
                )
            }
        }
    }
}
