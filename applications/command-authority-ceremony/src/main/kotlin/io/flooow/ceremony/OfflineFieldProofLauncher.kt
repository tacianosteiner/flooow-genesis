package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.AcceptedAttestationResult
import io.flooow.marketplace.operations.authorization.AcceptedAttestationVerifier
import io.flooow.marketplace.operations.authorization.AttestedCommandAuthorityIssuer
import java.security.SecureRandom
import java.time.Clock
import javax.sql.DataSource

enum class OfflineFieldProofOutcome {
    SUCCESS_RECONCILED,
    ALREADY_APPLIED_RECONCILED,
    INCOMPLETE_AUTHORITY,
    WRITER_FAILED,
    AMBIGUOUS_COMMIT,
    CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW,
    POST_PROOF_MISMATCH,
    DENIED_BEFORE_DURABLE_EFFECT
}

data class OfflineFieldProofLauncherResult(
    val outcome: OfflineFieldProofOutcome,
    val planFingerprint: String,
    val lastStage: AttestedCeremonyStage
)

fun interface OfflineFieldProofOperatorConfirmation {
    fun authorize(input: OfflineFieldProofInput): Boolean
}

fun interface OfflineFieldProofBoundaryVerifier {
    fun verify(input: OfflineFieldProofInput): Boolean
}

interface OfflineFieldProofReconciler {
    fun inspect(input: OfflineFieldProofInput): OfflineFieldProofDurableState
    fun reconcile(input: OfflineFieldProofInput): OfflineFieldProofReconciliation
}

data class OfflineFieldProofDurableState(
    val principalCount: Int,
    val credentialCount: Int,
    val grantCount: Int,
    val authorityOperationCount: Int,
    val decisionCount: Int,
    val headCount: Int,
    val lineageMatches: Boolean,
    val credentialOperationPresent: Boolean = false
) {
    init {
        require(listOf(principalCount, credentialCount, grantCount, authorityOperationCount, decisionCount, headCount)
            .all { it >= 0 })
    }

    val hasCredentialEffect: Boolean get() = credentialCount > 0 || grantCount > 0 || credentialOperationPresent
    val hasDecisionEffect: Boolean get() = decisionCount > 0 || headCount > 0
    val isEmpty: Boolean get() = principalCount + credentialCount + grantCount + authorityOperationCount + decisionCount + headCount == 0
}

data class OfflineFieldProofReconciliation(
    val acceptedAttestationProven: Boolean,
    val consumptionLineageProven: Boolean,
    val state: OfflineFieldProofDurableState,
    val exact: Boolean
)

/** Coordinates existing verifier/issuer/writer boundaries; it creates no independent authority. */
class OfflineFieldProofLauncher private constructor(
    private val verifier: AcceptedAttestationVerifier,
    private val issuer: AttestedCommandAuthorityIssuer,
    private val runtime: AttestedRuntimeBoundary,
    private val tty: ProtectedTty,
    private val boundaryVerifier: OfflineFieldProofBoundaryVerifier,
    private val reconciler: OfflineFieldProofReconciler,
    private val operatorConfirmation: OfflineFieldProofOperatorConfirmation,
    private val clock: Clock,
    private val random: SecureRandom = SecureRandom(),
    private val credentialLifecycleObserver: CredentialLifecycleObserver?,
    @Suppress("UNUSED_PARAMETER") internalSeam: Unit
) {
    constructor(
        verifier: AcceptedAttestationVerifier,
        issuer: AttestedCommandAuthorityIssuer,
        runtime: AttestedRuntimeBoundary,
        tty: ProtectedTty,
        boundaryVerifier: OfflineFieldProofBoundaryVerifier,
        reconciler: OfflineFieldProofReconciler,
        operatorConfirmation: OfflineFieldProofOperatorConfirmation,
        clock: Clock,
        random: SecureRandom = SecureRandom()
    ) : this(
        verifier, issuer, runtime, tty, boundaryVerifier, reconciler, operatorConfirmation,
        clock, random, null, Unit
    )

    internal constructor(
        verifier: AcceptedAttestationVerifier,
        issuer: AttestedCommandAuthorityIssuer,
        runtime: AttestedRuntimeBoundary,
        tty: ProtectedTty,
        boundaryVerifier: OfflineFieldProofBoundaryVerifier,
        reconciler: OfflineFieldProofReconciler,
        operatorConfirmation: OfflineFieldProofOperatorConfirmation,
        clock: Clock,
        random: SecureRandom,
        credentialLifecycleObserver: CredentialLifecycleObserver
    ) : this(
        verifier, issuer, runtime, tty, boundaryVerifier, reconciler, operatorConfirmation,
        clock, random, credentialLifecycleObserver, Unit
    )

    fun execute(input: OfflineFieldProofInput): OfflineFieldProofLauncherResult {
        val fingerprint = input.plan.fingerprint()
        if (!tty.isProtected() || !boundaryVerifier.verify(input)) {
            return result(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, fingerprint, AttestedCeremonyStage.PRE_FLIGHT)
        }

        val initial = try {
            reconciler.inspect(input)
        } catch (_: Throwable) {
            return result(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, fingerprint, AttestedCeremonyStage.PRE_FLIGHT)
        }
        if (initial.hasDecisionEffect) {
            val reconciliation = runCatching { reconciler.reconcile(input) }.getOrNull()
            return if (reconciliation?.exact == true) {
                result(OfflineFieldProofOutcome.ALREADY_APPLIED_RECONCILED, fingerprint, AttestedCeremonyStage.IDENTITY_DECISION_APPLIED)
            } else {
                result(OfflineFieldProofOutcome.POST_PROOF_MISMATCH, fingerprint, AttestedCeremonyStage.PRE_FLIGHT)
            }
        }
        if (initial.hasCredentialEffect) {
            return result(
                OfflineFieldProofOutcome.CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW,
                fingerprint,
                AttestedCeremonyStage.INITIAL_CREDENTIAL_APPLIED
            )
        }
        if (!initial.lineageMatches) {
            return result(OfflineFieldProofOutcome.POST_PROOF_MISMATCH, fingerprint, AttestedCeremonyStage.PRE_FLIGHT)
        }
        if (!operatorConfirmation.authorize(input)) {
            return result(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, fingerprint, AttestedCeremonyStage.PRE_FLIGHT)
        }

        var lastStage = AttestedCeremonyStage.PRE_FLIGHT
        val progress = AttestedCeremonyProgressObserver { lastStage = it }
        val ceremony = if (credentialLifecycleObserver == null) {
            ExecuteAttestedFieldProof(verifier, issuer, runtime, tty, clock, random, progress)
        } else {
            ExecuteAttestedFieldProof(verifier, issuer, runtime, tty, clock, random, credentialLifecycleObserver, progress)
        }
        val execution = try {
            ceremony.execute(input.attestation, input.target, input.command, input.plan)
        } catch (_: Throwable) {
            val reconciliation = runCatching { reconciler.reconcile(input) }.getOrNull()
            return if (reconciliation?.exact == true) {
                result(OfflineFieldProofOutcome.SUCCESS_RECONCILED, fingerprint, AttestedCeremonyStage.IDENTITY_DECISION_APPLIED)
            } else {
                result(OfflineFieldProofOutcome.AMBIGUOUS_COMMIT, fingerprint, lastStage)
            }
        }
        return when (execution) {
            is AttestedCeremonyResult.Applied -> {
                val reconciliation = runCatching { reconciler.reconcile(input) }.getOrNull()
                if (reconciliation?.exact == true) {
                    result(
                        if (execution.exactReplay) OfflineFieldProofOutcome.ALREADY_APPLIED_RECONCILED
                        else OfflineFieldProofOutcome.SUCCESS_RECONCILED,
                        fingerprint,
                        AttestedCeremonyStage.IDENTITY_DECISION_APPLIED
                    )
                } else {
                    result(OfflineFieldProofOutcome.POST_PROOF_MISMATCH, fingerprint, AttestedCeremonyStage.IDENTITY_DECISION_APPLIED)
                }
            }
            is AttestedCeremonyResult.Denied -> result(
                OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, fingerprint, execution.stage
            )
            is AttestedCeremonyResult.IncompleteAuthority -> result(
                OfflineFieldProofOutcome.INCOMPLETE_AUTHORITY, fingerprint, execution.stage
            )
            is AttestedCeremonyResult.CredentialLostRequiresHumanReview -> result(
                OfflineFieldProofOutcome.CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW, fingerprint, execution.stage
            )
            is AttestedCeremonyResult.WriterFailed -> {
                val state = runCatching { reconciler.inspect(input) }.getOrNull()
                val expectedAuthorityOnly = state?.let {
                    it.lineageMatches && it.principalCount == 1 && it.credentialCount == 1 &&
                        it.grantCount == 1 && it.authorityOperationCount == 3 &&
                        it.decisionCount == 0 && it.headCount == 0
                } == true
                result(
                    if (expectedAuthorityOnly) OfflineFieldProofOutcome.WRITER_FAILED
                    else OfflineFieldProofOutcome.POST_PROOF_MISMATCH,
                    fingerprint,
                    execution.stage
                )
            }
        }
    }

    private fun result(
        outcome: OfflineFieldProofOutcome,
        fingerprint: String,
        stage: AttestedCeremonyStage
    ) = OfflineFieldProofLauncherResult(outcome, fingerprint, stage)
}

class SystemConsoleOperatorConfirmation : OfflineFieldProofOperatorConfirmation {
    override fun authorize(input: OfflineFieldProofInput): Boolean {
        val console = System.console() ?: return false
        val fingerprint = input.plan.fingerprint()
        console.writer().apply {
            println("REAL_FIELD_PROOF=HOLD")
            println("PLAN_FINGERPRINT=$fingerprint")
            println("MANIFEST_ID=${input.attestation.manifest.manifestId}")
            println("ORGANIZATION_ID=${input.attestation.manifest.organizationId}")
            println("PRINCIPAL_ID=${input.plan.principalId}")
            println("CREDENTIAL_ID=${input.plan.credentialId}")
            println("GRANT_ID=${input.plan.grantId}")
            println("DECISION_ID=${input.plan.decisionId}")
            println("PROVIDER_CALL=NO")
            println("ROTATE_CREDENTIAL=HOLD")
            println("REVOKE=HOLD")
            println("Independent authority effects may commit before the identity decision.")
            println("Type EXECUTE $fingerprint to authorize this exact plan:")
            flush()
        }
        return console.readLine() == "EXECUTE $fingerprint"
    }
}
