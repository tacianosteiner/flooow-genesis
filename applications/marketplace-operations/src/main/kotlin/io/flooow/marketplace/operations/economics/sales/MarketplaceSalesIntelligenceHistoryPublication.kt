package io.flooow.marketplace.operations.economics.sales

import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChange

sealed interface EconomicLineagePublicationResult {
    data class Published(val revisionId: Long): EconomicLineagePublicationResult { init { require(revisionId > 0) }; override fun toString() = "[REDACTED]" }
    data class IdenticalPublished(val revisionId: Long): EconomicLineagePublicationResult { init { require(revisionId > 0) }; override fun toString() = "[REDACTED]" }
    data class Superseded(val currentRevisionId: Long?): EconomicLineagePublicationResult { init { require(currentRevisionId == null || currentRevisionId > 0) }; override fun toString() = "[REDACTED]" }
    data object CommitOutcomeUnknown: EconomicLineagePublicationResult
    data object IntegrityFailure: EconomicLineagePublicationResult
}

sealed interface EconomicLineageReconciliationResult {
    data class Known(val publication: EconomicLineagePublicationResult): EconomicLineageReconciliationResult {
        init { require(publication is EconomicLineagePublicationResult.IdenticalPublished ||
            publication is EconomicLineagePublicationResult.Superseded && publication.currentRevisionId != null) }
        override fun toString() = "[REDACTED]"
    }
    data object Absent: EconomicLineageReconciliationResult
    data object IntegrityFailure: EconomicLineageReconciliationResult
}

/** Exact frozen input; the observer is never the publication port. */
interface MarketplaceSalesIntelligenceHistoryPublication {
    fun publish(snapshot: ConsumedEconomicEvidenceSnapshot, record: MarketplaceSalesIntelligenceProjectionRecord): EconomicLineagePublicationResult
    fun reconcile(change: MarketplaceEconomicEvidenceChange, expected: ConsumedEconomicEvidenceSnapshot? = null): EconomicLineageReconciliationResult
}
