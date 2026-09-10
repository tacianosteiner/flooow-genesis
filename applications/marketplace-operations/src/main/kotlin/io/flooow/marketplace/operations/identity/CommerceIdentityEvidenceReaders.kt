package io.flooow.marketplace.operations.identity

import io.flooow.organization.OrganizationId

/** Read-only, organization-scoped ports for durable source evidence. */
fun interface MercadoLivreIdentityEvidenceReader {
    fun read(organizationId: OrganizationId, limit: Int): List<MercadoLivreTransactionEvidence>
}

data class OmieIdentityEvidenceRead(
    val records: List<OmieSalesOrderEvidence>,
    val persistedRows: Int,
    val skippedRows: Int
) {
    init {
        require(persistedRows >= records.size)
        require(skippedRows == persistedRows - records.size)
    }
}

fun interface OmieIdentityEvidenceReader {
    fun read(organizationId: OrganizationId, limit: Int): OmieIdentityEvidenceRead
}
