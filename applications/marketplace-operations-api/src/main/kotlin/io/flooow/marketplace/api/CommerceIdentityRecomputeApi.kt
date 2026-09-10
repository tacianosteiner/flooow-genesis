package io.flooow.marketplace.api

import io.flooow.marketplace.operations.identity.CommerceIdentityHealthEvaluation
import io.flooow.marketplace.operations.identity.CommerceIdentityHealthEvaluator
import io.flooow.marketplace.operations.identity.CommerceIdentityPolicy
import io.flooow.marketplace.operations.identity.MercadoLivreIdentityEvidenceReader
import io.flooow.marketplace.operations.identity.OmieIdentityEvidenceReader
import io.flooow.marketplace.operations.identity.ExplicitMarketplaceOrderReferenceResolver
import io.flooow.marketplace.operations.identity.OmieSalesOrderEvidence
import io.flooow.organization.OrganizationId
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.time.Clock
import java.util.concurrent.ConcurrentHashMap

internal class CommerceIdentityRecomputeApi(
    private val marketplace: MercadoLivreIdentityEvidenceReader,
    private val omie: OmieIdentityEvidenceReader,
    private val clock: Clock = Clock.systemUTC(),
    private val policy: CommerceIdentityPolicy = CommerceIdentityPolicy("MGI_GENESIS_IDENTITY_V1")
) {
    private val evaluations = ConcurrentHashMap<OrganizationId, CommerceIdentityHealthEvaluation>()

    fun current(organizationId: OrganizationId): CommerceIdentityHealthEvaluation? = evaluations[organizationId]

    fun recompute(organizationId: OrganizationId): JsonObject {
        val evaluatedAt = clock.instant().truncatedTo(java.time.temporal.ChronoUnit.MICROS)
        val marketplaceRead = try {
            marketplace.read(organizationId, MAX_EVIDENCE)
        } catch (_: Exception) {
            throw CommerceIdentityRecomputeFailureException(CommerceIdentityFailureCategory.EVIDENCE_READ)
        }
        val marketplaceEvidence = marketplaceRead.records
        val omieRead = try {
            omie.read(organizationId, MAX_EVIDENCE)
        } catch (_: Exception) {
            throw CommerceIdentityRecomputeFailureException(CommerceIdentityFailureCategory.EVIDENCE_READ)
        }
        val observedOrderIds = marketplaceEvidence.map { it.orderId }.toSet()
        val omieEvidence = deduplicateSemanticEvidence(
            omieRead.records.map { order ->
                order.copy(
                    declaredMarketplaceOrderIds =
                        ExplicitMarketplaceOrderReferenceResolver.resolve(
                            observedOrderIds,
                            listOf(order.integrationCode, order.customerOrderNumber)
                        )
                )
            }
        )
        val evaluation = try {
            CommerceIdentityHealthEvaluator.evaluate(
                organizationId, marketplaceEvidence, omieEvidence, policy, evaluatedAt
            )
        } catch (_: Exception) {
            throw CommerceIdentityRecomputeFailureException(CommerceIdentityFailureCategory.EVALUATION)
        }
        evaluations[organizationId] = evaluation
        return buildJsonObject {
            put("status", "COMPLETED")
            put("mlTransactionsInspected", evaluation.health.mlTransactionsInspected)
            put("mlPersistedRows", marketplaceRead.persistedRows)
            put("mlSellerSkuRows", marketplaceRead.sellerSkuRows)
            put("mlUsableAmountDateRows", marketplaceRead.usableAmountDateRows)
            put("omieTransactionsInspected", evaluation.health.omieTransactionsInspected)
            put("omiePersistedRows", omieRead.persistedRows)
            put("omieIdentityEvaluableRows", omieEvidence.size)
            put("omieNonEvaluableRows", omieRead.skippedRows)
            put("omieIntegrationReferenceRows", omieRead.integrationReferenceRows)
            put("omieCustomerOrderReferenceRows", omieRead.customerOrderReferenceRows)
            put("omieProductEvidenceRows", omieRead.productEvidenceRows)
            put("omieAmountEvidenceRows", omieRead.amountEvidenceRows)
            put("omieExplicitMarketplaceOrderReferenceRows", omieEvidence.count { it.declaredMarketplaceOrderIds.isNotEmpty() })
            put("exactConfirmed", evaluation.health.exactConfirmed)
            put("candidate", evaluation.health.candidate)
            put("ambiguous", evaluation.health.ambiguous)
            put("conflict", evaluation.health.conflict)
            put("unresolved", evaluation.health.unresolved)
            evaluation.health.coveragePercentage?.let { put("coveragePercentage", it.toPlainString()) }
            put("policyVersion", evaluation.health.policyVersion)
            put("evaluatedAt", evaluation.health.evaluatedAt.toString())
        }
    }

    private fun deduplicateSemanticEvidence(records: List<OmieSalesOrderEvidence>): List<OmieSalesOrderEvidence> =
        records.groupBy(::semanticKey).toSortedMap().values.map { revisions ->
            revisions.sortedWith(compareBy<OmieSalesOrderEvidence> { it.integrationCode ?: "" }
                .thenBy { it.customerOrderNumber ?: "" }
                .thenBy { it.evidenceReferences.sorted().joinToString("|") })
                .reduce { left, right ->
                    left.copy(
                        evidenceReferences = (left.evidenceReferences + right.evidenceReferences).toSortedSet(),
                        declaredMarketplaceOrderIds =
                            (left.declaredMarketplaceOrderIds + right.declaredMarketplaceOrderIds).toSortedSet()
                    )
                }
        }

    private fun semanticKey(order: OmieSalesOrderEvidence): String {
        val sourceOrder = order.evidenceReferences
            .mapNotNull { reference ->
                reference.removePrefix("omie:").substringBeforeLast(":", "").takeIf { it.isNotBlank() }
            }
            .sorted()
            .firstOrNull() ?: "unknown"
        return listOf(sourceOrder, order.integrationCode ?: "", order.customerOrderNumber ?: "")
            .joinToString("\u001f")
    }

    private companion object { const val MAX_EVIDENCE = 10_000 }
}

internal enum class CommerceIdentityFailureCategory { EVIDENCE_READ, EVALUATION, UNKNOWN }

internal class CommerceIdentityRecomputeFailureException(
    val category: CommerceIdentityFailureCategory = CommerceIdentityFailureCategory.UNKNOWN
) : RuntimeException()
