package io.flooow.marketplace.operations.economics.evidence

sealed interface MarketplaceEconomicEvidenceUpdateReadResult {
    data class Found(
        val update: MarketplaceIndependentEconomicEvidenceUpdate
    ) : MarketplaceEconomicEvidenceUpdateReadResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object NotFound : MarketplaceEconomicEvidenceUpdateReadResult {
        override fun toString(): String = "[REDACTED]"
    }

    data object IntegrityFailure : MarketplaceEconomicEvidenceUpdateReadResult {
        override fun toString(): String = "[REDACTED]"
    }
}

fun interface MarketplaceEconomicEvidenceUpdateReader {
    fun findUpdate(
        subject: MarketplaceEconomicEvidenceSubject,
        evidenceVersion: MarketplaceEconomicEvidenceVersion,
        updateId: MarketplaceEconomicEvidenceObservationId,
        changeKind: MarketplaceEconomicEvidenceChangeKind
    ): MarketplaceEconomicEvidenceUpdateReadResult
}