package io.flooow.marketplace.operations.identity

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ExplicitMarketplaceOrderReferenceResolverTest {
    private val observed = setOf("2000018336941860")

    @Test
    fun `exact and representation-only forms resolve`() {
        assertEquals(setOf("2000018336941860"), ExplicitMarketplaceOrderReferenceResolver.resolve(observed, listOf("2000018336941860")))
        assertEquals(setOf("2000018336941860"), ExplicitMarketplaceOrderReferenceResolver.resolve(observed, listOf("#2000018336941860")))
        assertEquals(setOf("2000018336941860"), ExplicitMarketplaceOrderReferenceResolver.resolve(observed, listOf(" 2000018336941860 ")))
    }

    @Test
    fun `unknown and embedded values do not resolve`() {
        assertTrue(ExplicitMarketplaceOrderReferenceResolver.resolve(observed, listOf("2000017885956380")).isEmpty())
        assertTrue(ExplicitMarketplaceOrderReferenceResolver.resolve(observed, listOf("ML-2000018336941860", "pedido 2000018336941860", "x2000018336941860")).isEmpty())
        assertTrue(ExplicitMarketplaceOrderReferenceResolver.resolve(observed, listOf("##2000018336941860")).isEmpty())
    }

    @Test
    fun `missing remains absent`() {
        assertTrue(ExplicitMarketplaceOrderReferenceResolver.resolve(observed, listOf(null, "   ")).isEmpty())
    }
}
