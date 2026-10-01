package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.identity.ExplicitTransactionIdentityReason
import io.flooow.marketplace.operations.identity.TransactionIdentityCommand
import io.flooow.marketplace.operations.identity.TransactionIdentityKind
import io.flooow.marketplace.operations.identity.TransactionIdentityWriteResult
import java.security.SecureRandom
import java.time.Clock
import java.util.Base64

interface AttestedRuntimeBoundary : RuntimeBoundary {
    fun writeAttested(
        actor: AuthenticatedCommand,
        command: TransactionIdentityCommand,
        manifest: ApprovalManifest
    ): TransactionIdentityWriteResult
}

enum class AttestedCeremonyStage {
    PRE_FLIGHT,
    ATTESTATION_VERIFIED,
    PRINCIPAL_APPLIED,
    INITIAL_CREDENTIAL_APPLIED,
    CREDENTIAL_DELIVERED,
    GRANT_APPLIED,
    AUTHENTICATED,
    CREDENTIAL_DESTROYED,
    IDENTITY_DECISION_APPLIED
}

sealed interface AttestedCeremonyResult {
    data class Applied(val plan: OfflineFieldProofExecutionPlan, val exactReplay: Boolean) : AttestedCeremonyResult
    data class Denied(val stage: AttestedCeremonyStage) : AttestedCeremonyResult
    data class IncompleteAuthority(val stage: AttestedCeremonyStage) : AttestedCeremonyResult
    data class CredentialLostRequiresHumanReview(val stage: AttestedCeremonyStage) : AttestedCeremonyResult
    data class WriterFailed(val stage: AttestedCeremonyStage) : AttestedCeremonyResult
}

fun interface AttestedCeremonyProgressObserver {
    fun reached(stage: AttestedCeremonyStage)
}

/** Real post-V042 field-proof orchestration. Signed V041 evidence is mandatory and never caller-reconstructed. */
class ExecuteAttestedFieldProof private constructor(
    private val verifier: AcceptedAttestationVerifier,
    private val issuer: AttestedCommandAuthorityIssuer,
    private val runtime: AttestedRuntimeBoundary,
    private val tty: ProtectedTty,
    private val clock: Clock,
    private val random: SecureRandom,
    private val credentialLifecycleObserver: CredentialLifecycleObserver?,
    private val progressObserver: AttestedCeremonyProgressObserver,
    @Suppress("UNUSED_PARAMETER") internalSeam: Unit
) {
    constructor(
        verifier: AcceptedAttestationVerifier,
        issuer: AttestedCommandAuthorityIssuer,
        runtime: AttestedRuntimeBoundary,
        tty: ProtectedTty,
        clock: Clock,
        random: SecureRandom = SecureRandom(),
        progressObserver: AttestedCeremonyProgressObserver = AttestedCeremonyProgressObserver {}
    ) : this(verifier, issuer, runtime, tty, clock, random, null, progressObserver, Unit)

    internal constructor(
        verifier: AcceptedAttestationVerifier,
        issuer: AttestedCommandAuthorityIssuer,
        runtime: AttestedRuntimeBoundary,
        tty: ProtectedTty,
        clock: Clock,
        random: SecureRandom,
        credentialLifecycleObserver: CredentialLifecycleObserver,
        progressObserver: AttestedCeremonyProgressObserver = AttestedCeremonyProgressObserver {}
    ) : this(verifier, issuer, runtime, tty, clock, random, credentialLifecycleObserver, progressObserver, Unit)

    fun execute(
        attestation: SignedApprovalAttestation,
        target: FieldProofTarget,
        command: TransactionIdentityCommand,
        plan: OfflineFieldProofExecutionPlan
    ): AttestedCeremonyResult {
        require(command.decisionId == plan.decisionId) { "Command decisionId differs from execution plan" }
        progressObserver.reached(AttestedCeremonyStage.PRE_FLIGHT)
        val manifest = attestation.manifest
        if (!locallyEligible(manifest, target, command)) return AttestedCeremonyResult.Denied(AttestedCeremonyStage.PRE_FLIGHT)
        val verification = verifier.verify(attestation)
        if (verification !is AcceptedAttestationResult.Accepted &&
            verification !is AcceptedAttestationResult.AlreadyAccepted
        ) return AttestedCeremonyResult.Denied(AttestedCeremonyStage.PRE_FLIGHT)
        progressObserver.reached(AttestedCeremonyStage.ATTESTATION_VERIFIED)

        val principalResult = issuer.issuePrincipal(AttestedPrincipalRequest(
            manifest.organizationId, manifest.manifestId, manifest, plan.principalOperationId, plan.principalId
        ))
        if (!ok(principalResult)) return AttestedCeremonyResult.IncompleteAuthority(AttestedCeremonyStage.ATTESTATION_VERIFIED)
        progressObserver.reached(AttestedCeremonyStage.PRINCIPAL_APPLIED)

        val rawSecret = ByteArray(32).also(random::nextBytes)
        val token = "fc1.${plan.credentialId}.${Base64.getUrlEncoder().withoutPadding().encodeToString(rawSecret)}"
        rawSecret.fill(0)
        val credential = CommandCredential.parse(token)
            ?: return AttestedCeremonyResult.Denied(AttestedCeremonyStage.PRINCIPAL_APPLIED)
        val secretVerifier = CommandCredentialVerifier.fromCredential(credential).persistenceBytes()
        credentialLifecycleObserver?.created()
        var destroyed = false

        fun destroyCredential() {
            if (!destroyed) {
                credential.destroy()
                secretVerifier.fill(0)
                destroyed = true
                credentialLifecycleObserver?.destroyed(runCatching { CommandCredentialVerifier.fromCredential(credential) }.isFailure)
            }
        }

        try {
            if (!ok(issuer.bindInitialCredential(AttestedInitialCredentialRequest(
                    manifest.organizationId, manifest.manifestId, manifest, plan.initialCredentialOperationId,
                    plan.principalId, plan.credentialId, secretVerifier
                )))) return AttestedCeremonyResult.IncompleteAuthority(AttestedCeremonyStage.PRINCIPAL_APPLIED)
            progressObserver.reached(AttestedCeremonyStage.INITIAL_CREDENTIAL_APPLIED)
            try {
                tty.deliverOnce(token.toCharArray())
            } catch (_: Throwable) {
                return AttestedCeremonyResult.CredentialLostRequiresHumanReview(
                    AttestedCeremonyStage.INITIAL_CREDENTIAL_APPLIED
                )
            }
            progressObserver.reached(AttestedCeremonyStage.CREDENTIAL_DELIVERED)
            if (!ok(issuer.grantPermission(AttestedGrantRequest(
                    manifest.organizationId, manifest.manifestId, manifest, plan.grantOperationId,
                    plan.principalId, plan.grantId
                )))) return AttestedCeremonyResult.CredentialLostRequiresHumanReview(
                AttestedCeremonyStage.CREDENTIAL_DELIVERED
            )
            progressObserver.reached(AttestedCeremonyStage.GRANT_APPLIED)
            val actor = runtime.authenticate(token)
                ?: return AttestedCeremonyResult.CredentialLostRequiresHumanReview(AttestedCeremonyStage.GRANT_APPLIED)
            progressObserver.reached(AttestedCeremonyStage.AUTHENTICATED)
            destroyCredential()
            progressObserver.reached(AttestedCeremonyStage.CREDENTIAL_DESTROYED)
            return when (val writeResult = runtime.writeAttested(actor, command, manifest)) {
                is TransactionIdentityWriteResult.Applied -> {
                    progressObserver.reached(AttestedCeremonyStage.IDENTITY_DECISION_APPLIED)
                    AttestedCeremonyResult.Applied(plan, exactReplay = false)
                }
                is TransactionIdentityWriteResult.AlreadyApplied -> {
                    progressObserver.reached(AttestedCeremonyStage.IDENTITY_DECISION_APPLIED)
                    AttestedCeremonyResult.Applied(plan, exactReplay = true)
                }
                else -> AttestedCeremonyResult.WriterFailed(AttestedCeremonyStage.CREDENTIAL_DESTROYED)
            }
        } finally {
            destroyCredential()
        }
    }

    private fun locallyEligible(
        manifest: ApprovalManifest,
        target: FieldProofTarget,
        command: TransactionIdentityCommand
    ): Boolean {
        val now = clock.instant()
        return tty.isProtected() && target.valid() && now >= manifest.approvalWindowStart && now <= manifest.approvalWindowEnd &&
            target.organizationId == manifest.organizationId &&
            target.mercadoLivreConnectionId == manifest.mercadoLivreConnectionId &&
            target.omieConnectionId == manifest.omieConnectionId &&
            target.sourceOrderReference == manifest.sourceOrderReference &&
            target.integrationReference == manifest.integrationReference &&
            target.marketplaceOrderId == manifest.marketplaceOrderId.value &&
            target.reason == manifest.reason && target.provenance == manifest.provenance &&
            target.correlationId == manifest.correlationId && target.permission.name == manifest.permission.name &&
            command.sourceOrderReference == manifest.sourceOrderReference &&
            command.marketplaceOrderId == manifest.marketplaceOrderId.value &&
            command.kind == TransactionIdentityKind.CONFIRMED &&
            command.reason == ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION &&
            command.provenance == manifest.provenance && command.correlationId == manifest.correlationId &&
            command.supersedesDecisionId == null && runtime.matchesTarget(target)
    }

    private fun ok(result: AttestedAuthorityResult) =
        result is AttestedAuthorityResult.Applied || result is AttestedAuthorityResult.AlreadyApplied
}
