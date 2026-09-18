package io.flooow.marketplace.operations.economics.provider.omie

import io.flooow.integration.connector.*
import io.flooow.integration.control.ProviderKey
import io.flooow.marketplace.operations.economics.provider.*
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.net.http.HttpTimeoutException
import java.security.MessageDigest
import java.time.Clock
import java.time.Duration
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.format.ResolverStyle
import java.time.temporal.ChronoUnit
import kotlinx.serialization.json.*

/**
 * Read-only Omie ListarPedidos V3 evidence adapter.
 *
 * V3 intentionally does not reuse the legacy `data_previsao -> UTC midnight`
 * transaction parser. It preserves provider-local lifecycle timestamps and
 * financial-basis source evidence without promoting any financial authority.
 */
class OmieTransactionEvidenceV3Connector(
    private val endpoint: URI = DEFAULT_ENDPOINT,
    private val clock: Clock = Clock.systemUTC(),
    private val transport: OmieHttpTransport = JdkOmieTransactionV3Transport()
) : PullConnector {
    override val descriptor = ConnectorDescriptor(
        ProviderKey.of("omie"),
        listOf(
            ConnectorRecordDefinition(
                OmieTransactionEvidenceV3Capability.KEY,
                OmieTransactionEvidenceV3Record::class
            )
        )
    )

    init {
        require(endpoint.scheme.equals("https", true))
        require(endpoint.host != null)
    }

    override fun readPage(
        capability: ConnectorCapability,
        credentialBytes: ByteArray,
        currentProgress: ConnectorProgress?,
        budget: ConnectorBudget,
        cancellation: ConnectorCancellation
    ): ConnectorReadResult {
        if (capability != OmieTransactionEvidenceV3Capability.KEY) {
            return failed(ConnectorAdapterFailureKind.REMOTE_PERMANENT)
        }
        if (cancellation.isCancelled()) {
            return failed(ConnectorAdapterFailureKind.CANCELLED)
        }
        if (!clock.instant().isBefore(budget.deadline)) {
            return failed(ConnectorAdapterFailureKind.BUDGET_EXCEEDED)
        }

        val page = decodePage(currentProgress)
            ?: if (currentProgress == null) {
                1
            } else {
                return failed(ConnectorAdapterFailureKind.REMOTE_DATA_INVALID)
            }

        val credential = decodeCredential(credentialBytes)
            ?: return failed(ConnectorAdapterFailureKind.AUTHENTICATION_REQUIRED)

        val body = buildJsonObject {
            put("call", "ListarPedidos")
            put("app_key", credential.first)
            put("app_secret", credential.second)
            put(
                "param",
                buildJsonArray {
                    add(
                        buildJsonObject {
                            put("pagina", page)
                            put("registros_por_pagina", minOf(budget.maxRecords, 100))
                            put("apenas_importado_api", "N")
                        }
                    )
                }
            )
        }.toString().toByteArray(Charsets.UTF_8)

        val response = try {
            val timeout = Duration.between(clock.instant(), budget.deadline)
            if (timeout.isZero || timeout.isNegative) {
                body.fill(0)
                return failed(ConnectorAdapterFailureKind.BUDGET_EXCEEDED)
            }
            transport.post(endpoint, body, timeout, budget.maxResponseBytes)
        } catch (_: OmieV3ResponseTooLargeException) {
            body.fill(0)
            return failed(ConnectorAdapterFailureKind.BUDGET_EXCEEDED)
        } catch (_: HttpTimeoutException) {
            body.fill(0)
            return failed(ConnectorAdapterFailureKind.BUDGET_EXCEEDED)
        } catch (_: InterruptedException) {
            Thread.currentThread().interrupt()
            body.fill(0)
            return failed(ConnectorAdapterFailureKind.CANCELLED)
        } catch (_: Exception) {
            body.fill(0)
            return failed(ConnectorAdapterFailureKind.REMOTE_TEMPORARY)
        } finally {
            body.fill(0)
        }

        try {
            if (response.statusCode !in 200..299) {
                return failed(
                    when {
                        response.statusCode == 429 ->
                            ConnectorAdapterFailureKind.RATE_LIMITED
                        response.statusCode in 500..599 ->
                            ConnectorAdapterFailureKind.REMOTE_TEMPORARY
                        else ->
                            ConnectorAdapterFailureKind.REMOTE_PERMANENT
                    }
                )
            }

            val observed = clock.instant().truncatedTo(ChronoUnit.MICROS)
            val root = Json.parseToJsonElement(response.body.decodeToString()).jsonObject

            if (root.containsKey("faultstring") || root.containsKey("faultcode")) {
                return failed(ConnectorAdapterFailureKind.REMOTE_PERMANENT)
            }

            val totalPages =
                (root["nTotPaginas"] ?: root["total_de_paginas"])
                    ?.jsonPrimitive
                    ?.intOrNull
                    ?: 1

            val nodes = sequenceOf(
                "pedido_venda_produto",
                "pedido_venda",
                "pedidos",
                "lista_pedidos"
            ).mapNotNull { root[it] }.firstOrNull()

            val records = (nodes as? JsonArray ?: JsonArray(emptyList()))
                .map { parseRecord(it.jsonObject, observed) }

            if (records.size > budget.maxRecords) {
                return failed(ConnectorAdapterFailureKind.BUDGET_EXCEEDED)
            }

            val next = if (page >= totalPages) {
                null
            } else {
                ConnectorProgress.take("page=${page + 1}".toByteArray())
            }

            return ConnectorReadResult.Page(
                ConnectorPage(
                    records,
                    next,
                    observed,
                    next == null,
                    response.body.size.toLong()
                )
            )
        } catch (_: Exception) {
            return failed(ConnectorAdapterFailureKind.REMOTE_DATA_INVALID)
        } finally {
            response.body.fill(0)
        }
    }

    private fun parseRecord(
        source: JsonObject,
        observedAt: java.time.Instant
    ): OmieTransactionEvidenceV3Record {
        val header = objectAt(source, "cabecalho")
            ?: objectAt(source, "cab")
            ?: source

        val orderReference = requireNotNull(
            text(header, "codigo_pedido") ?: text(source, "codigo_pedido")
        ) { "Missing Omie order code" }

        val additional = objectAt(source, "informacoes_adicionais")
            ?: objectAt(source, "informacoes_adicionais_pedido")

        val infoCadastro = objectAt(source, "infoCadastro")
        val totals = objectAt(source, "total_pedido")
        val freight = objectAt(source, "frete")
        val marketplace = objectAt(source, "market_place")

        val lines = ((source["det"] ?: source["itens"] ?: source["detalhes"])
            as? JsonArray)
            .orEmpty()
            .map { parseLine(it.jsonObject) }
            .sortedBy(::canonicalLineText)

        val coreTotalKeys = setOf(
            "valor_total_pedido",
            "valor_mercadorias",
            "valor_descontos",
            "valor_deducoes"
        )

        val additionalTotals = totals
            ?.entries
            ?.asSequence()
            ?.filterNot { it.key in coreTotalKeys }
            ?.mapNotNull { (key, value) ->
                val primitive = value as? JsonPrimitive ?: return@mapNotNull null
                val raw = primitive.content.trim()
                if (raw.isEmpty()) return@mapNotNull null
                val parsed = runCatching {
                    ProviderSourceDecimal.parse(raw.replace(',', '.'))
                }.getOrNull() ?: return@mapNotNull null
                key to parsed
            }
            ?.toMap()
            .orEmpty()

        val recordMaterial = ParsedV3Material(
            orderReference = OmieOrderReference.of(orderReference),
            integrationOrderReference =
                text(header, "codigo_pedido_integracao")
                    ?.let(OmieIntegrationReference::of),
            customerOrderReference =
                (text(additional, "numero_pedido_cliente")
                    ?: text(header, "numero_pedido_cliente"))
                    ?.let(OmieCustomerOrderReference::of),
            sourceOrderOrigin =
                text(header, "origem_pedido")?.let(OmieOrderOrigin::of),
            status = text(header, "etapa")?.let(OmieOrderStatus::of),
            currency =
                text(header, "codigo_moeda")
                    ?.uppercase()
                    ?.let(MercadoLivreSourceCurrency::of),
            providerCreatedLocal =
                localTimestampPair(
                    text(infoCadastro, "dInc"),
                    text(infoCadastro, "hInc")
                ),
            providerModifiedLocal =
                localTimestampPair(
                    text(infoCadastro, "dAlt"),
                    text(infoCadastro, "hAlt")
                ),
            cancelled = flag(infoCadastro, "cancelado"),
            cancelledLocal =
                localTimestampPair(
                    text(infoCadastro, "dCan"),
                    text(infoCadastro, "hCan")
                ),
            invoiced = flag(infoCadastro, "faturado"),
            invoicedLocal =
                localTimestampPair(
                    text(infoCadastro, "dFat"),
                    text(infoCadastro, "hFat")
                ),
            authorized = flag(infoCadastro, "autorizado"),
            denied = flag(infoCadastro, "denegado"),
            returned = flag(infoCadastro, "devolvido"),
            partiallyReturned = flag(infoCadastro, "devolvido_parcial"),
            orderEnded = flag(header, "encerrado"),
            orderEndedReason =
                text(header, "enc_motivo")?.let(OmieOrderEndReason::of),
            orderEndedLocal =
                localTimestampPair(
                    text(header, "enc_data"),
                    text(header, "enc_hora")
                ),
            orderDiscountType =
                text(header, "tipo_desconto_pedido")?.let(OmieDiscountType::of),
            orderDiscountPercent = decimal(header, "perc_desconto_pedido"),
            orderDiscountAmount = decimal(header, "valor_desconto_pedido"),
            totalOrderAmount = decimal(totals, "valor_total_pedido"),
            merchandiseAmount = decimal(totals, "valor_mercadorias"),
            discountAmount = decimal(totals, "valor_descontos"),
            deductionAmount = decimal(totals, "valor_deducoes"),
            freightAmount = decimal(freight, "valor_frete"),
            insuranceAmount = decimal(freight, "valor_seguro"),
            otherExpenseAmount = decimal(freight, "outras_despesas"),
            marketplaceFeeAmount = decimal(marketplace, "nTaxa"),
            marketplaceShippingAmount = decimal(marketplace, "nEnvio"),
            additionalOrderTotals = additionalTotals,
            lines = lines
        )

        val sourceFingerprint = sha256(source.toString())
        val semanticFingerprint = semanticFingerprint(recordMaterial)

        return OmieTransactionEvidenceV3Record(
            orderReference = recordMaterial.orderReference,
            integrationOrderReference = recordMaterial.integrationOrderReference,
            customerOrderReference = recordMaterial.customerOrderReference,
            sourceOrderOrigin = recordMaterial.sourceOrderOrigin,
            status = recordMaterial.status,
            currency = recordMaterial.currency,
            providerCreatedLocal = recordMaterial.providerCreatedLocal,
            providerModifiedLocal = recordMaterial.providerModifiedLocal,
            cancelled = recordMaterial.cancelled,
            cancelledLocal = recordMaterial.cancelledLocal,
            invoiced = recordMaterial.invoiced,
            invoicedLocal = recordMaterial.invoicedLocal,
            authorized = recordMaterial.authorized,
            denied = recordMaterial.denied,
            returned = recordMaterial.returned,
            partiallyReturned = recordMaterial.partiallyReturned,
            orderEnded = recordMaterial.orderEnded,
            orderEndedReason = recordMaterial.orderEndedReason,
            orderEndedLocal = recordMaterial.orderEndedLocal,
            orderDiscountType = recordMaterial.orderDiscountType,
            orderDiscountPercent = recordMaterial.orderDiscountPercent,
            orderDiscountAmount = recordMaterial.orderDiscountAmount,
            totalOrderAmount = recordMaterial.totalOrderAmount,
            merchandiseAmount = recordMaterial.merchandiseAmount,
            discountAmount = recordMaterial.discountAmount,
            deductionAmount = recordMaterial.deductionAmount,
            freightAmount = recordMaterial.freightAmount,
            insuranceAmount = recordMaterial.insuranceAmount,
            otherExpenseAmount = recordMaterial.otherExpenseAmount,
            marketplaceFeeAmount = recordMaterial.marketplaceFeeAmount,
            marketplaceShippingAmount = recordMaterial.marketplaceShippingAmount,
            additionalOrderTotals = recordMaterial.additionalOrderTotals,
            lines = recordMaterial.lines,
            observedAt = observedAt,
            sourceFingerprint = sourceFingerprint,
            sourceEvidenceSemanticFingerprint = semanticFingerprint
        )
    }

    private fun parseLine(source: JsonObject): OmieTransactionEvidenceV3Line {
        val ide = objectAt(source, "ide")
        val product = objectAt(source, "produto") ?: objectAt(source, "ide") ?: source
        val additional = objectAt(source, "inf_adic")

        val productIdentifiers = listOfNotNull(
            identifier(
                product,
                listOf("codigo_produto"),
                OmieTransactionProductIdentifierKind.INTERNAL_PRODUCT_ID
            ),
            identifier(
                product,
                listOf("codigo_produto_integracao", "cCodInt"),
                OmieTransactionProductIdentifierKind.INTEGRATION_PRODUCT_CODE
            ),
            identifier(
                product,
                listOf("codigo", "cCodigo"),
                OmieTransactionProductIdentifierKind.DISPLAY_PRODUCT_CODE
            )
        )

        return OmieTransactionEvidenceV3Line(
            internalItemReference =
                text(ide, "codigo_item")?.let(OmieOrderItemReference::of),
            integrationItemReference =
                text(ide, "codigo_item_integracao")
                    ?.let(OmieOrderItemIntegrationReference::of),
            productIdentifiers = productIdentifiers,
            quantity = decimal(product, "quantidade"),
            unitValue = decimal(product, "valor_unitario"),
            discountType =
                text(product, "tipo_desconto")?.let(OmieDiscountType::of),
            discountPercent = decimal(product, "percentual_desconto"),
            discountValue = decimal(product, "valor_desconto"),
            deductionValue = decimal(product, "valor_deducao"),
            merchandiseValue = decimal(product, "valor_mercadoria"),
            totalValue = decimal(product, "valor_total"),
            doNotGenerateFinancial = flag(additional, "nao_gerar_financeiro"),
            doNotSumTotal = flag(additional, "nao_somar_total"),
            kit = flag(product, "kit"),
            kitComponent = flag(product, "componente_kit"),
            kitParentItemReference =
                text(product, "codigo_item_kit")?.let(OmieOrderItemReference::of)
        )
    }

    private fun identifier(
        source: JsonObject?,
        aliases: List<String>,
        kind: OmieTransactionProductIdentifierKind
    ): OmieTransactionProductIdentifier? {
        val values = aliases.mapNotNull { text(source, it) }.distinct()
        require(values.size <= 1) {
            "Conflicting Omie product identifier aliases"
        }
        return values.singleOrNull()?.let {
            OmieTransactionProductIdentifier.of(kind, it)
        }
    }

    private fun localTimestampPair(
        date: String?,
        time: String?
    ): LocalDateTime? {
        if (date == null && time == null) return null
        require(date != null && time != null) {
            "Partial Omie local timestamp"
        }
        return LocalDateTime.parse(
            "$date $time",
            LOCAL_DATE_TIME_FORMATTER
        )
    }

    private fun flag(source: JsonObject?, key: String): Boolean? =
        text(source, key)?.let {
            when (it.uppercase()) {
                "S" -> true
                "N" -> false
                else -> error("Invalid Omie S/N flag")
            }
        }

    private fun decimal(
        source: JsonObject?,
        key: String
    ): ProviderSourceDecimal? =
        text(source, key)?.let {
            ProviderSourceDecimal.parse(it.replace(',', '.'))
        }

    private fun text(source: JsonObject?, key: String): String? =
        (source?.get(key) as? JsonPrimitive)
            ?.content
            ?.trim()
            ?.takeIf { it.isNotEmpty() }

    private fun objectAt(source: JsonObject?, key: String): JsonObject? =
        source?.get(key) as? JsonObject

    private fun semanticFingerprint(material: ParsedV3Material): String {
        val canonical = buildJsonObject {
            put("schema", "omie-transaction-evidence-v3/1")
            putText("orderReference", material.orderReference.encodedForPersistence())
            putText(
                "integrationOrderReference",
                material.integrationOrderReference?.encodedForPersistence()
            )
            putText(
                "customerOrderReference",
                material.customerOrderReference?.encodedForPersistence()
            )
            putText(
                "sourceOrderOrigin",
                material.sourceOrderOrigin?.encodedForPersistence()
            )
            putText("status", material.status?.encodedForPersistence())
            putText("currency", material.currency?.encodedForPersistence())
            putLocal("providerCreatedLocal", material.providerCreatedLocal)
            putLocal("providerModifiedLocal", material.providerModifiedLocal)
            putNullableBoolean("cancelled", material.cancelled)
            putLocal("cancelledLocal", material.cancelledLocal)
            putNullableBoolean("invoiced", material.invoiced)
            putLocal("invoicedLocal", material.invoicedLocal)
            putNullableBoolean("authorized", material.authorized)
            putNullableBoolean("denied", material.denied)
            putNullableBoolean("returned", material.returned)
            putNullableBoolean("partiallyReturned", material.partiallyReturned)
            putNullableBoolean("orderEnded", material.orderEnded)
            putText(
                "orderEndedReason",
                material.orderEndedReason?.encodedForPersistence()
            )
            putLocal("orderEndedLocal", material.orderEndedLocal)
            putText(
                "orderDiscountType",
                material.orderDiscountType?.encodedForPersistence()
            )
            putDecimal("orderDiscountPercent", material.orderDiscountPercent)
            putDecimal("orderDiscountAmount", material.orderDiscountAmount)
            putDecimal("totalOrderAmount", material.totalOrderAmount)
            putDecimal("merchandiseAmount", material.merchandiseAmount)
            putDecimal("discountAmount", material.discountAmount)
            putDecimal("deductionAmount", material.deductionAmount)
            putDecimal("freightAmount", material.freightAmount)
            putDecimal("insuranceAmount", material.insuranceAmount)
            putDecimal("otherExpenseAmount", material.otherExpenseAmount)
            putDecimal("marketplaceFeeAmount", material.marketplaceFeeAmount)
            putDecimal(
                "marketplaceShippingAmount",
                material.marketplaceShippingAmount
            )
            put(
                "additionalOrderTotals",
                buildJsonObject {
                    material.additionalOrderTotals.toSortedMap().forEach { (key, value) ->
                        put(key, value.canonicalValue())
                    }
                }
            )
            put(
                "lines",
                buildJsonArray {
                    material.lines
                        .sortedBy(::canonicalLineText)
                        .forEach { add(lineJson(it)) }
                }
            )
        }.toString()

        return sha256(canonical)
    }

    private fun canonicalLineText(line: OmieTransactionEvidenceV3Line): String =
        lineJson(line).toString()

    private fun lineJson(line: OmieTransactionEvidenceV3Line): JsonObject =
        buildJsonObject {
            putText(
                "internalItemReference",
                line.internalItemReference?.encodedForPersistence()
            )
            putText(
                "integrationItemReference",
                line.integrationItemReference?.encodedForPersistence()
            )
            put(
                "productIdentifiers",
                buildJsonArray {
                    line.productIdentifiers.forEach { identifier ->
                        add(
                            buildJsonObject {
                                put("kind", identifier.kind.name)
                                put("value", identifier.encodedForPersistence())
                            }
                        )
                    }
                }
            )
            putDecimal("quantity", line.quantity)
            putDecimal("unitValue", line.unitValue)
            putText(
                "discountType",
                line.discountType?.encodedForPersistence()
            )
            putDecimal("discountPercent", line.discountPercent)
            putDecimal("discountValue", line.discountValue)
            putDecimal("deductionValue", line.deductionValue)
            putDecimal("merchandiseValue", line.merchandiseValue)
            putDecimal("totalValue", line.totalValue)
            putNullableBoolean(
                "doNotGenerateFinancial",
                line.doNotGenerateFinancial
            )
            putNullableBoolean("doNotSumTotal", line.doNotSumTotal)
            putNullableBoolean("kit", line.kit)
            putNullableBoolean("kitComponent", line.kitComponent)
            putText(
                "kitParentItemReference",
                line.kitParentItemReference?.encodedForPersistence()
            )
        }

    private fun JsonObjectBuilder.putText(key: String, value: String?) {
        if (value == null) put(key, JsonNull) else put(key, value)
    }

    private fun JsonObjectBuilder.putDecimal(
        key: String,
        value: ProviderSourceDecimal?
    ) {
        if (value == null) put(key, JsonNull) else put(key, value.canonicalValue())
    }

    private fun JsonObjectBuilder.putLocal(
        key: String,
        value: LocalDateTime?
    ) {
        if (value == null) {
            put(key, JsonNull)
        } else {
            put(key, value.format(CANONICAL_LOCAL_DATE_TIME_FORMATTER))
        }
    }

    private fun JsonObjectBuilder.putNullableBoolean(
        key: String,
        value: Boolean?
    ) {
        if (value == null) put(key, JsonNull) else put(key, value)
    }

    private fun sha256(value: String): String =
        MessageDigest.getInstance("SHA-256")
            .digest(value.toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it) }

    private fun decodePage(progress: ConnectorProgress?): Int? =
        progress?.useBytes {
            Regex("page=([1-9][0-9]*)")
                .matchEntire(it.decodeToString())
                ?.groupValues
                ?.get(1)
                ?.toIntOrNull()
                ?.takeIf { page -> page >= 2 }
        }

    private fun decodeCredential(bytes: ByteArray): Pair<String, String>? =
        runCatching {
            val source = Json.parseToJsonElement(bytes.decodeToString()).jsonObject
            if (source["schemaVersion"]?.jsonPrimitive?.intOrNull != 1) {
                null
            } else {
                Pair(
                    source["appKey"]!!.jsonPrimitive.content,
                    source["appSecret"]!!.jsonPrimitive.content
                ).takeIf { it.first.isNotBlank() && it.second.isNotBlank() }
            }
        }.getOrNull()

    private fun failed(kind: ConnectorAdapterFailureKind) =
        ConnectorReadResult.Failed(ConnectorAdapterFailure.of(kind))

    private data class ParsedV3Material(
        val orderReference: OmieOrderReference,
        val integrationOrderReference: OmieIntegrationReference?,
        val customerOrderReference: OmieCustomerOrderReference?,
        val sourceOrderOrigin: OmieOrderOrigin?,
        val status: OmieOrderStatus?,
        val currency: MercadoLivreSourceCurrency?,
        val providerCreatedLocal: LocalDateTime?,
        val providerModifiedLocal: LocalDateTime?,
        val cancelled: Boolean?,
        val cancelledLocal: LocalDateTime?,
        val invoiced: Boolean?,
        val invoicedLocal: LocalDateTime?,
        val authorized: Boolean?,
        val denied: Boolean?,
        val returned: Boolean?,
        val partiallyReturned: Boolean?,
        val orderEnded: Boolean?,
        val orderEndedReason: OmieOrderEndReason?,
        val orderEndedLocal: LocalDateTime?,
        val orderDiscountType: OmieDiscountType?,
        val orderDiscountPercent: ProviderSourceDecimal?,
        val orderDiscountAmount: ProviderSourceDecimal?,
        val totalOrderAmount: ProviderSourceDecimal?,
        val merchandiseAmount: ProviderSourceDecimal?,
        val discountAmount: ProviderSourceDecimal?,
        val deductionAmount: ProviderSourceDecimal?,
        val freightAmount: ProviderSourceDecimal?,
        val insuranceAmount: ProviderSourceDecimal?,
        val otherExpenseAmount: ProviderSourceDecimal?,
        val marketplaceFeeAmount: ProviderSourceDecimal?,
        val marketplaceShippingAmount: ProviderSourceDecimal?,
        val additionalOrderTotals: Map<String, ProviderSourceDecimal>,
        val lines: List<OmieTransactionEvidenceV3Line>
    )

    companion object {
        val DEFAULT_ENDPOINT: URI =
            URI.create("https://app.omie.com.br/api/v1/produtos/pedido/")

        private val LOCAL_DATE_TIME_FORMATTER =
            DateTimeFormatter.ofPattern("dd/MM/uuuu HH:mm:ss")
                .withResolverStyle(ResolverStyle.STRICT)

        private val CANONICAL_LOCAL_DATE_TIME_FORMATTER =
            DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss")
                .withResolverStyle(ResolverStyle.STRICT)
    }
}

private class JdkOmieTransactionV3Transport(
    private val client: HttpClient =
        HttpClient.newBuilder()
            .followRedirects(HttpClient.Redirect.NEVER)
            .build()
) : OmieHttpTransport {
    override fun post(
        endpoint: URI,
        body: ByteArray,
        timeout: Duration,
        maxResponseBytes: Long
    ): OmieHttpResponse {
        val response = client.send(
            HttpRequest.newBuilder(endpoint)
                .timeout(timeout)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofByteArray(body))
                .build(),
            HttpResponse.BodyHandlers.ofInputStream()
        )

        val output = ByteArrayOutputStream()

        response.body().use { input ->
            val buffer = ByteArray(8192)
            var total = 0L
            while (true) {
                val count = input.read(buffer)
                if (count < 0) break
                total += count
                if (total > maxResponseBytes) {
                    throw OmieV3ResponseTooLargeException()
                }
                output.write(buffer, 0, count)
            }
        }

        return OmieHttpResponse(
            response.statusCode(),
            output.toByteArray(),
            response.headers().firstValue("Retry-After").orElse(null)
        )
    }
}

private class OmieV3ResponseTooLargeException : IOException()
