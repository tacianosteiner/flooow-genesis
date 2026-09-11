package io.flooow.marketplace.operations.identity

import java.time.Instant

/**
 * Read-only product/offer evidence bridge. An exact seller-SKU/code overlap is
 * deliberately retained as a suggested relation; it never confirms a product
 * mapping or changes Economic Truth.
 */
object ProductIdentityBridge {
    fun candidates(
        marketplace: MercadoLivreTransactionEvidence,
        omieOrders: List<OmieSalesOrderEvidence>,
        policy: CommerceIdentityPolicy,
        evaluatedAt: Instant
    ): List<CommerceIdentityCandidate> {
        require(omieOrders.all { it.organizationId == marketplace.organizationId }) {
            "Product identity evidence organization mismatch"
        }
        return omieOrders.flatMap { omie ->
            marketplace.sellerSkus.intersect(omie.productCodes).sorted().map { sellerSku ->
                CommerceIdentityCandidate(
                    marketplace.organizationId,
                    CommerceIdentitySystem.MERCADO_LIVRE,
                    CommerceIdentityType.SELLER_SKU,
                    sellerSku,
                    CommerceIdentitySystem.OMIE,
                    CommerceIdentityType.ERP_PRODUCT_CODE,
                    sellerSku,
                    CommerceIdentityMatchState.CANDIDATE,
                    CommerceIdentityConfirmationState.SUGGESTED,
                    listOf(
                        CommerceIdentityEvidence(
                            marketplace.organizationId,
                            CommerceIdentitySystem.MERCADO_LIVRE,
                            CommerceIdentityType.SELLER_SKU,
                            sellerSku,
                            CommerceIdentityEvidenceKind.EXACT_SELLER_SKU,
                            "MGI_EXACT_SELLER_SKU",
                            evaluatedAt
                        )
                    ),
                    policy.version,
                    evaluatedAt
                )
            }
        }
    }
}
