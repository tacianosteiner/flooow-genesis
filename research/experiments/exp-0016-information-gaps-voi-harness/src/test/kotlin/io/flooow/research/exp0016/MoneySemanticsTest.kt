package io.flooow.research.exp0016

import java.math.BigDecimal
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class MoneySemanticsTest {
    @Test
    fun `economic cost money cannot be negative`() {
        assertFailsWith<IllegalArgumentException> {
            Money(
                amount = BigDecimal("-0.01"),
                currency = "BRL",
            )
        }
    }

    @Test
    fun `signed money can represent negative net economic value`() {
        val net =
            SignedMoney(
                amount = BigDecimal("-25.00"),
                currency = "BRL",
            )

        assertEquals(BigDecimal("-25.00"), net.amount)
        assertEquals("BRL", net.currency)
    }

    @Test
    fun `money addition preserves currency discipline`() {
        val a = Money(BigDecimal("10.00"), "BRL")
        val b = Money(BigDecimal("5.00"), "BRL")

        assertEquals(BigDecimal("15.00"), (a + b).amount)
    }

    @Test
    fun `money addition rejects currency mismatch`() {
        val a = Money(BigDecimal("10.00"), "BRL")
        val b = Money(BigDecimal("5.00"), "USD")

        assertFailsWith<IllegalArgumentException> {
            a + b
        }
    }
}
