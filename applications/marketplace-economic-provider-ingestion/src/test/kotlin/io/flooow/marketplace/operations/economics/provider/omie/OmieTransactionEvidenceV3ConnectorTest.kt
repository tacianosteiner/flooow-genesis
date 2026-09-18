package io.flooow.marketplace.operations.economics.provider.omie

import io.flooow.integration.connector.*
import io.flooow.marketplace.operations.economics.provider.OmieTransactionEvidenceV3Capability
import io.flooow.marketplace.operations.economics.provider.OmieTransactionEvidenceV3Record
import java.net.URI
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class OmieTransactionEvidenceV3ConnectorTest {
    private val now = Instant.parse("2026-09-18T14:00:00Z")
    private val credential =
        """{"schemaVersion":1,"appKey":"key","appSecret":"secret"}"""
            .toByteArray()

    @Test
    fun `v3 parses lifecycle origin financial basis and line evidence without UTC invention`() {
        val record = record(fullPayload())

        assertEquals("MLV", record.sourceOrderOrigin!!.encodedForPersistence())
        assertEquals("60", record.status!!.encodedForPersistence())
        assertNull(record.currency)

        assertEquals(
            "2026-09-10T08:15:30",
            record.providerCreatedLocal.toString()
        )
        assertEquals(
            "2026-09-11T09:16:31",
            record.providerModifiedLocal.toString()
        )
        assertEquals(false, record.cancelled)
        assertEquals(true, record.invoiced)
        assertEquals(true, record.authorized)
        assertEquals(false, record.denied)

        assertEquals("100", record.totalOrderAmount!!.canonicalValue())
        assertEquals("110", record.merchandiseAmount!!.canonicalValue())
        assertEquals("10", record.discountAmount!!.canonicalValue())
        assertEquals("2", record.freightAmount!!.canonicalValue())
        assertEquals("3", record.marketplaceFeeAmount!!.canonicalValue())
        assertEquals("4", record.marketplaceShippingAmount!!.canonicalValue())
        assertEquals(
            "18",
            record.additionalOrderTotals["valor_icms"]!!.canonicalValue()
        )

        assertEquals(2, record.lines.size)
        assertTrue(
            record.lines.any {
                it.doNotGenerateFinancial == true &&
                    it.doNotSumTotal == false
            }
        )
        assertTrue(
            Regex("[0-9a-f]{64}")
                .matches(record.sourceEvidenceSemanticFingerprint)
        )
    }

    @Test
    fun `semantic fingerprint is stable when provider line order changes`() {
        val first = record(fullPayload(reverseLines = false))
        val second = record(fullPayload(reverseLines = true))

        assertNotEquals(first.sourceFingerprint, second.sourceFingerprint)
        assertEquals(
            first.sourceEvidenceSemanticFingerprint,
            second.sourceEvidenceSemanticFingerprint
        )
    }

    @Test
    fun `semantic fingerprint changes when marketplace financial evidence changes`() {
        val first = record(fullPayload(marketplaceFee = "3"))
        val second = record(fullPayload(marketplaceFee = "3.01"))

        assertNotEquals(
            first.sourceEvidenceSemanticFingerprint,
            second.sourceEvidenceSemanticFingerprint
        )
    }

    @Test
    fun `partial provider local timestamp fails closed as remote data invalid`() {
        val connector = connector(
            fullPayload().replace(
                """"hInc":"08:15:30",""",
                ""
            )
        )

        val result = connector.readPage(
            OmieTransactionEvidenceV3Capability.KEY,
            credential.copyOf(),
            null,
            ConnectorBudget(now.plusSeconds(30), 100, 100_000),
            ConnectorCancellation.NEVER
        )

        val failure = assertIs<ConnectorReadResult.Failed>(result)
        assertEquals(
            ConnectorAdapterFailureKind.REMOTE_DATA_INVALID,
            failure.failure.kind
        )
    }

    @Test
    fun `unknown provider S N flag fails closed as remote data invalid`() {
        val connector = connector(
            fullPayload().replace(
                "\"cancelado\":\"N\"",
                "\"cancelado\":\"?\""
            )
        )

        val result = connector.readPage(
            OmieTransactionEvidenceV3Capability.KEY,
            credential.copyOf(),
            null,
            ConnectorBudget(now.plusSeconds(30), 100, 100_000),
            ConnectorCancellation.NEVER
        )

        val failure = assertIs<ConnectorReadResult.Failed>(result)
        assertEquals(
            ConnectorAdapterFailureKind.REMOTE_DATA_INVALID,
            failure.failure.kind
        )
    }

    private fun record(payload: String): OmieTransactionEvidenceV3Record {
        val result = connector(payload).readPage(
            OmieTransactionEvidenceV3Capability.KEY,
            credential.copyOf(),
            null,
            ConnectorBudget(now.plusSeconds(30), 100, 100_000),
            ConnectorCancellation.NEVER
        )

        val page = assertIs<ConnectorReadResult.Page>(result).value
        return assertIs<OmieTransactionEvidenceV3Record>(
            page.records.single()
        )
    }

    private fun connector(payload: String) =
        OmieTransactionEvidenceV3Connector(
            URI.create("https://example.test/omie"),
            Clock.fixed(now, ZoneOffset.UTC),
            OmieHttpTransport { _, _, _, _ ->
                OmieHttpResponse(200, payload.toByteArray())
            }
        )

    private fun fullPayload(
        reverseLines: Boolean = false,
        marketplaceFee: String = "3"
    ): String {
        val lineA =
            """
            {
              "ide":{
                "codigo_item":"10",
                "codigo_item_integracao":"ITEM-10"
              },
              "produto":{
                "codigo_produto":"101",
                "codigo_produto_integracao":"PROD-101",
                "codigo":"SKU-101",
                "quantidade":"1",
                "valor_unitario":"60",
                "tipo_desconto":"V",
                "percentual_desconto":"0",
                "valor_desconto":"5",
                "valor_deducao":"0",
                "valor_mercadoria":"60",
                "valor_total":"55",
                "kit":"N",
                "componente_kit":"N"
              },
              "inf_adic":{
                "nao_gerar_financeiro":"S",
                "nao_somar_total":"N"
              }
            }
            """.trimIndent()

        val lineB =
            """
            {
              "ide":{
                "codigo_item":"11",
                "codigo_item_integracao":"ITEM-11"
              },
              "produto":{
                "codigo_produto":"102",
                "codigo_produto_integracao":"PROD-102",
                "codigo":"SKU-102",
                "quantidade":"1",
                "valor_unitario":"50",
                "tipo_desconto":"V",
                "percentual_desconto":"0",
                "valor_desconto":"5",
                "valor_deducao":"0",
                "valor_mercadoria":"50",
                "valor_total":"45",
                "kit":"N",
                "componente_kit":"N"
              },
              "inf_adic":{
                "nao_gerar_financeiro":"N",
                "nao_somar_total":"N"
              }
            }
            """.trimIndent()

        val lines = if (reverseLines) "$lineB,$lineA" else "$lineA,$lineB"

        return """
        {
          "nPagina":1,
          "nTotPaginas":1,
          "pedido_venda_produto":[{
            "cabecalho":{
              "codigo_pedido":"123",
              "codigo_pedido_integracao":"ERP-1",
              "origem_pedido":"MLV",
              "etapa":"60",
              "tipo_desconto_pedido":"V",
              "perc_desconto_pedido":"0",
              "valor_desconto_pedido":"0",
              "encerrado":"N"
            },
            "informacoes_adicionais":{
              "numero_pedido_cliente":"ML-123"
            },
            "infoCadastro":{
              "dInc":"10/09/2026",
              "hInc":"08:15:30",
              "dAlt":"11/09/2026",
              "hAlt":"09:16:31",
              "cancelado":"N",
              "faturado":"S",
              "dFat":"11/09/2026",
              "hFat":"10:00:00",
              "autorizado":"S",
              "denegado":"N",
              "devolvido":"N",
              "devolvido_parcial":"N"
            },
            "frete":{
              "valor_frete":"2",
              "valor_seguro":"1",
              "outras_despesas":"0.5"
            },
            "market_place":{
              "nTaxa":"$marketplaceFee",
              "nEnvio":"4"
            },
            "total_pedido":{
              "base_calculo_icms":"100",
              "valor_icms":"18",
              "valor_mercadorias":"110",
              "valor_descontos":"10",
              "valor_deducoes":"0",
              "valor_total_pedido":"100",
              "base_ibs_cbs":"100",
              "valor_cbs":"0"
            },
            "det":[
              $lines
            ]
          }]
        }
        """.trimIndent()
    }
}
