package io.flooow.marketplace.operations.economics.provider.omie

import io.flooow.integration.connector.ConnectorBudget
import io.flooow.integration.connector.ConnectorCancellation
import io.flooow.integration.connector.ConnectorReadResult
import io.flooow.marketplace.operations.economics.provider.OmieTransactionEvidenceCapability
import io.flooow.marketplace.operations.economics.provider.OmieTransactionEvidenceRecord
import java.net.URI
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNull

class OmieTransactionEvidenceConnectorTest {
    private val now = Instant.parse("2026-09-10T12:00:00Z")
    private val credential = """{"schemaVersion":1,"appKey":"key","appSecret":"secret"}""".toByteArray()

    @Test
    fun `parses documented pedido venda shape including customer reference products and amount`() {
        val connector = connector {
            OmieHttpResponse(200, """
                {"nPagina":1,"nTotPaginas":1,"pedido_venda_produto":[{
                  "cabecalho":{"codigo_pedido":123,"codigo_pedido_integracao":"ERP-1","data_previsao":"10/09/2026"},
                  "informacoes_adicionais":{"numero_pedido_cliente":"ML-123"},
                  "det":[{"produto":{"codigo_produto_integracao":"SKU-1","quantidade":2}}],
                  "total_pedido":{"valor_total_pedido":95.02}
                }]}
            """.trimIndent().toByteArray())
        }
        val page = assertIs<ConnectorReadResult.Page>(connector.read()).value
        val record = assertIs<OmieTransactionEvidenceRecord>(page.records.single())
        assertEquals("ERP-1", record.integrationOrderReference!!.encodedForPersistence())
        assertEquals("ML-123", record.customerOrderReference!!.encodedForPersistence())
        assertEquals("SKU-1", record.products.single().productCode.encodedForPersistence())
        assertEquals("2", record.products.single().quantity.canonicalValue())
        assertEquals("95.02", record.totalAmount!!.canonicalValue())
        assertNull(record.currency)
    }

    @Test
    fun `supports alternate documented keys without converting integration ref to marketplace id`() {
        val connector = connector {
            OmieHttpResponse(200, """
                {"nPagina":1,"nTotPaginas":1,"pedido_venda_produto":[{
                  "cab":{"codigo_pedido":"124","codigo_pedido_integracao":"ERP-2"},
                  "itens":[{"produto":{"cCodigo":"SKU-2","quantidade":"1"}}],
                  "total_pedido":{"valor_total_pedido":"10,00"}
                }]}
            """.trimIndent().toByteArray())
        }
        val record = assertIs<OmieTransactionEvidenceRecord>(connector.read().let { (it as ConnectorReadResult.Page).value.records.single() })
        assertEquals("ERP-2", record.integrationOrderReference!!.encodedForPersistence())
        assertNull(record.customerOrderReference)
        assertEquals("SKU-2", record.products.single().productCode.encodedForPersistence())
        assertNull(record.currency)
    }

    private fun connector(response: () -> OmieHttpResponse) = OmieTransactionEvidenceConnector(
        URI.create("https://example.test/omie"), Clock.fixed(now, ZoneOffset.UTC), OmieHttpTransport { _, _, _, _ -> response() }
    )

    private fun OmieTransactionEvidenceConnector.read() = readPage(
        OmieTransactionEvidenceCapability.KEY, credential.copyOf(), null,
        ConnectorBudget(now.plusSeconds(30), 100, 100_000), ConnectorCancellation.NEVER
    )
}
