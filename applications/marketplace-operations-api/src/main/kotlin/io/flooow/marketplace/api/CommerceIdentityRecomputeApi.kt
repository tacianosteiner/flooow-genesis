package io.flooow.marketplace.api

import io.flooow.marketplace.operations.identity.CommerceIdentityHealthEvaluation
import io.flooow.marketplace.operations.identity.CommerceIdentityHealthEvaluator
import io.flooow.marketplace.operations.identity.CommerceIdentityPolicy
import io.flooow.marketplace.operations.identity.MercadoLivreIdentityEvidenceReader
import io.flooow.marketplace.operations.identity.OmieIdentityEvidenceReader
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
        val marketplaceEvidence = marketplace.read(organizationId, MAX_EVIDENCE)
        val omieEvidence = omie.read(organizationId, MAX_EVIDENCE)
        val evaluation = CommerceIdentityHealthEvaluator.evaluate(
            organizationId, marketplaceEvidence, omieEvidence, policy, evaluatedAt
        )
        evaluations[organizationId] = evaluation
        return buildJsonObject {
            put("status", "COMPLETED")
            put("mlTransactionsInspected", evaluation.health.mlTransactionsInspected)
            put("omieTransactionsInspected", evaluation.health.omieTransactionsInspected)
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

    private companion object { const val MAX_EVIDENCE = 10_000 }
}

internal class CommerceIdentityRecomputeFailureException : RuntimeException()
