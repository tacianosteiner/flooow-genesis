package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.identity.ExplicitTransactionIdentityReason
import io.flooow.marketplace.operations.identity.TransactionIdentityCommand
import io.flooow.marketplace.operations.identity.TransactionIdentityKind
import io.flooow.marketplace.operations.identity.TransactionIdentityWriteResult
import java.security.SecureRandom
import java.time.Clock
import java.util.Base64
import java.util.UUID

interface AttestedRuntimeBoundary : RuntimeBoundary {
    fun writeAttested(
        actor: AuthenticatedCommand,
        command: TransactionIdentityCommand,
        manifest: ApprovalManifest
    ): TransactionIdentityWriteResult
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
    @Suppress("UNUSED_PARAMETER") internalSeam: Unit
) {
    constructor(
        verifier: AcceptedAttestationVerifier,
        issuer: AttestedCommandAuthorityIssuer,
        runtime: AttestedRuntimeBoundary,
        tty: ProtectedTty,
        clock: Clock,
        random: SecureRandom = SecureRandom()
    ) : this(verifier, issuer, runtime, tty, clock, random, null, Unit)

    internal constructor(
        verifier: AcceptedAttestationVerifier,
        issuer: AttestedCommandAuthorityIssuer,
        runtime: AttestedRuntimeBoundary,
        tty: ProtectedTty,
        clock: Clock,
        random: SecureRandom,
        credentialLifecycleObserver: CredentialLifecycleObserver
    ) : this(verifier, issuer, runtime, tty, clock, random, credentialLifecycleObserver, Unit)

    fun execute(
        attestation: SignedApprovalAttestation,
        target: FieldProofTarget,
        command: TransactionIdentityCommand
    ): CeremonyResult {
        val manifest = attestation.manifest
        if (!locallyEligible(manifest, target, command)) return CeremonyResult.Denied
        val verification = verifier.verify(attestation)
        if (verification !is AcceptedAttestationResult.Accepted &&
            verification !is AcceptedAttestationResult.AlreadyAccepted
        ) return CeremonyResult.Denied

        val principalId = CommandPrincipalId(UUID.randomUUID())
        val credentialId = UUID.randomUUID()
        val grantId = UUID.randomUUID()
        val rawSecret = ByteArray(32).also(random::nextBytes)
        val token = "fc1.$credentialId.${Base64.getUrlEncoder().withoutPadding().encodeToString(rawSecret)}"
        rawSecret.fill(0)
        val credential = CommandCredential.parse(token) ?: return CeremonyResult.Denied
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
            if (!ok(issuer.issuePrincipal(AttestedPrincipalRequest(
                    manifest.organizationId, manifest.manifestId, manifest, UUID.randomUUID(), principalId
                )))) return CeremonyResult.IncompleteAuthority
            if (!ok(issuer.bindInitialCredential(AttestedInitialCredentialRequest(
                    manifest.organizationId, manifest.manifestId, manifest, UUID.randomUUID(), principalId,
                    credentialId, secretVerifier
                )))) return CeremonyResult.IncompleteAuthority
            tty.deliverOnce(token.toCharArray())
            if (!ok(issuer.grantPermission(AttestedGrantRequest(
                    manifest.organizationId, manifest.manifestId, manifest, UUID.randomUUID(), principalId, grantId
                )))) return CeremonyResult.IncompleteAuthority
            val actor = runtime.authenticate(token) ?: return CeremonyResult.IncompleteAuthority
            destroyCredential()
            return when (runtime.writeAttested(actor, command, manifest)) {
                is TransactionIdentityWriteResult.Applied,
                is TransactionIdentityWriteResult.AlreadyApplied -> CeremonyResult.Applied(principalId.value, command.decisionId)
                else -> CeremonyResult.WriterFailed
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
