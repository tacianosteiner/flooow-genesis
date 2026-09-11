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
        val knownObserved = KNOWN_PRODUCTION_ORDER_IDS.associateWith(observedOrderIds::contains)
        val omieReferences = omieRead.records.flatMap { listOf(it.integrationCode, it.customerOrderNumber) }
            .filterNotNull()
        val knownInOmieReferences = KNOWN_PRODUCTION_ORDER_IDS.associateWith { id ->
            omieReferences.any { ExplicitMarketplaceOrderReferenceResolver.normalize(it) == id }
        }
        val resolverEmissions = omieRead.records.map { order ->
            ExplicitMarketplaceOrderReferenceResolver.resolve(
                observedOrderIds,
                listOf(order.integrationCode, order.customerOrderNumber)
            )
        }
        val omieEvidence = deduplicateSemanticEvidence(
            omieRead.records.mapIndexed { index, order ->
                order.copy(declaredMarketplaceOrderIds = resolverEmissions[index])
            }
        )
        val knownResolverEmissions = KNOWN_PRODUCTION_ORDER_IDS.associateWith { id ->
            resolverEmissions.any { id in it }
        }
        val knownAfterAggregation = KNOWN_PRODUCTION_ORDER_IDS.associateWith { id ->
            omieEvidence.any { id in it.declaredMarketplaceOrderIds }
        }
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
            put("diagnostics", buildJsonObject {
                put("observedMlOrderIdCount", observedOrderIds.size)
                put("omieIntegrationReferenceCount", omieRead.records.count { it.integrationCode != null })
                put("omieCustomerOrderReferenceCount", omieRead.records.count { it.customerOrderNumber != null })
                put("knownProductionOrderIds", buildJsonObject {
                    KNOWN_PRODUCTION_ORDER_IDS.forEach { id ->
                        put(id, buildJsonObject {
                            put("observedInMl", knownObserved.getValue(id))
                            put("inOmieReferencesBeforeResolver", knownInOmieReferences.getValue(id))
                            put("emittedByResolverBeforeAggregation", knownResolverEmissions.getValue(id))
                            put("survivesSemanticAggregation", knownAfterAggregation.getValue(id))
                        })
                    }
                })
            })
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
        records.groupBy(::semanticRevisionKey).toSortedMap().flatMap { (key, revisions) ->
            if (key.startsWith("unparseable:")) {
                revisions.sortedWith(OMIE_EVIDENCE_ORDER)
            } else if (hasContradictoryProviderReferences(revisions)) {
                // Preserve contradiction as separate evidence; the bridge can
                // then retain its authoritative CONFLICT semantics.
                revisions.sortedWith(OMIE_EVIDENCE_ORDER)
            } else {
                listOf(aggregateRevisions(revisions))
            }
        }

    /** Accept only the exact provenance shape emitted by the durable reader. */
    private fun semanticRevisionKey(order: OmieSalesOrderEvidence): String {
        val sourceOrders = order.evidenceReferences.mapNotNull { reference ->
            OMIE_PROVENANCE_PATTERN.matchEntire(reference)?.groupValues?.get(1)
        }.distinct()
        return if (sourceOrders.size == 1) "source:${sourceOrders.single()}"
        else "unparseable:${order.evidenceReferences.sorted().joinToString("|")}"
    }

    private fun hasContradictoryProviderReferences(revisions: List<OmieSalesOrderEvidence>): Boolean =
        revisions.mapNotNull { it.integrationCode }.toSet().size > 1 ||
            revisions.mapNotNull { it.customerOrderNumber }.toSet().size > 1

    private fun aggregateRevisions(revisions: List<OmieSalesOrderEvidence>): OmieSalesOrderEvidence {
        val representative = revisions.maxWithOrNull(
            compareBy<OmieSalesOrderEvidence> { revisionRichness(it) }
                .thenBy { it.integrationCode ?: "" }
                .thenBy { it.customerOrderNumber ?: "" }
                .thenBy { it.evidenceReferences.sorted().joinToString("|") }
        ) ?: error("Omie evidence revision group is empty")
        return representative.copy(
            integrationCode = revisions.mapNotNull { it.integrationCode }.distinct().sorted().firstOrNull(),
            customerOrderNumber = revisions.mapNotNull { it.customerOrderNumber }.distinct().sorted().firstOrNull(),
            evidenceReferences = revisions.flatMap { it.evidenceReferences }.toSortedSet(),
            declaredMarketplaceOrderIds = revisions.flatMap { it.declaredMarketplaceOrderIds }.toSortedSet()
        )
    }

    private fun revisionRichness(order: OmieSalesOrderEvidence): Int =
        (if (order.integrationCode != null) 1 else 0) +
            (if (order.customerOrderNumber != null) 1 else 0) +
            order.productCodes.size * 2 +
            (if (order.orderAmount != null) 1 else 0)

    private companion object {
        val OMIE_PROVENANCE_PATTERN = Regex("omie:([^:]+):[^:]+")
        val OMIE_EVIDENCE_ORDER = compareBy<OmieSalesOrderEvidence> {
            it.evidenceReferences.sorted().joinToString("|")
        }
        val KNOWN_PRODUCTION_ORDER_IDS = listOf(
            "2000017885956380",
            "2000017921418896",
            "2000018336941860",
            "2000018381665458"
        )
        const val MAX_EVIDENCE = 10_000
    }

}

internal enum class CommerceIdentityFailureCategory { EVIDENCE_READ, EVALUATION, UNKNOWN }

internal class CommerceIdentityRecomputeFailureException(
    val category: CommerceIdentityFailureCategory = CommerceIdentityFailureCategory.UNKNOWN
) : RuntimeException()
