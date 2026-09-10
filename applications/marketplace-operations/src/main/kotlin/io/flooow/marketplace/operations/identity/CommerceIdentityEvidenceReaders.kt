package io.flooow.marketplace.operations.identity

import io.flooow.organization.OrganizationId

/** Read-only, organization-scoped ports for durable source evidence. */
fun interface MercadoLivreIdentityEvidenceReader {
    fun read(organizationId: OrganizationId, limit: Int): List<MercadoLivreTransactionEvidence>
}

fun interface OmieIdentityEvidenceReader {
    fun read(organizationId: OrganizationId, limit: Int): List<OmieSalesOrderEvidence>
}
