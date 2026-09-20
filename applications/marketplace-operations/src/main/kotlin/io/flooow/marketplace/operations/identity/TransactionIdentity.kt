package io.flooow.marketplace.operations.identity

import io.flooow.marketplace.operations.authorization.AuthenticatedCommand
import io.flooow.marketplace.operations.authorization.CommandAuthorizationLineage
import java.security.MessageDigest
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.UUID

enum class TransactionIdentityKind { CONFIRMED, REJECTED, WITHDRAWN }
enum class ExplicitTransactionIdentityReason { EXPLICIT_CONFIRMATION, EXPLICIT_REJECTION, CORRECTION }

data class TransactionIdentityCommand(
    val decisionId: UUID,
    val sourceOrderReference: String,
    val marketplaceOrderId: UUID,
    val kind: TransactionIdentityKind,
    val reason: ExplicitTransactionIdentityReason,
    val provenance: String,
    val correlationId: UUID,
    val supersedesDecisionId: UUID? = null
) {
    init {
        requireBounded(sourceOrderReference, 256)
        requireBounded(provenance, 1024)
        require((supersedesDecisionId != null) == (reason == ExplicitTransactionIdentityReason.CORRECTION))
        if (supersedesDecisionId == null) require(
            (kind == TransactionIdentityKind.CONFIRMED && reason == ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION) ||
                (kind == TransactionIdentityKind.REJECTED && reason == ExplicitTransactionIdentityReason.EXPLICIT_REJECTION)
        )
    }

    fun intentFingerprint(actor: AuthenticatedCommand): String = transactionIdentityHash(listOf(
        "transaction-identity-intent/1", actor.organizationId.value.toString(), actor.principalId.value.toString(),
        actor.mercadoLivreConnectionId.toString(), actor.omieConnectionId.toString(), sourceOrderReference,
        marketplaceOrderId.toString(), kind.name, reason.name, provenance, supersedesDecisionId?.toString() ?: ""
    ))

    private fun requireBounded(value: String, max: Int) {
        require(value.toByteArray(Charsets.UTF_8).size in 1..max && value == value.trim() && value.isNotBlank())
        require(value.none { it.code < 32 || it.code == 127 })
    }
}

data class TransactionIdentityEvidence(
    val mlCapability: String,
    val mlProgressVersion: Long,
    val mlRecordOrdinal: Int,
    val externalOrderId: String,
    val currency: String,
    val omieCapability: String,
    val omieProgressVersion: Long,
    val omieRecordOrdinal: Int,
    val omieSemanticFingerprint: String,
    val providerRevision: LocalDateTime
) {
    fun decisionFingerprint(intent: String, actor: AuthenticatedCommand, authority: CommandAuthorizationLineage): String =
        transactionIdentityHash(listOf(
            "transaction-identity/1", intent, actor.mercadoLivreConnectionId.toString(), mlCapability,
            mlProgressVersion.toString(), mlRecordOrdinal.toString(), externalOrderId, currency,
            omieCapability, "1", omieSemanticFingerprint, providerRevision.format(CIVIL_FORMAT),
            authority.grantId.toString(), authority.grantRevision.toString(), authority.permission.name,
            authority.semanticVersion, authority.semanticFingerprint
        ))
}

enum class TransactionIdentityFailure {
    AUTHORIZATION_DENIED, EVIDENCE_UNAVAILABLE, CURRENTNESS_UNPROVEN, CONFLICT, INTEGRITY_FAILURE
}

sealed interface TransactionIdentityWriteResult {
    data class Applied(val decisionId: UUID, val semanticFingerprint: String) : TransactionIdentityWriteResult
    data class AlreadyApplied(val decisionId: UUID, val semanticFingerprint: String) : TransactionIdentityWriteResult
    data class Failed(val failure: TransactionIdentityFailure) : TransactionIdentityWriteResult
}

private val CIVIL_FORMAT = DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss.SSSSSS")
private fun transactionIdentityHash(fields: List<String>): String {
    val value = fields.joinToString("") { "${it.toByteArray(Charsets.UTF_8).size}:$it" }
    return MessageDigest.getInstance("SHA-256").digest(value.toByteArray(Charsets.UTF_8))
        .joinToString("") { "%02x".format(it) }
}
