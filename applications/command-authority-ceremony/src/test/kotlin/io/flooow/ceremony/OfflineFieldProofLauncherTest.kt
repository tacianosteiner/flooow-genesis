package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.*
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.identity.*
import io.flooow.marketplace.persistence.postgres.PostgresConfiguration
import io.flooow.organization.OrganizationId
import java.security.SecureRandom
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.Base64
import java.util.UUID
import kotlin.test.*

class OfflineFieldProofLauncherTest {
    @Test fun `all durable identities come from the immutable plan`() {
        val fixture = Fixture()
        val result = fixture.launcher().execute(fixture.input)

        assertEquals(OfflineFieldProofOutcome.SUCCESS_RECONCILED, result.outcome)
        assertEquals(fixture.input.plan.principalId, fixture.issuer.principal?.principalId)
        assertEquals(fixture.input.plan.credentialId, fixture.issuer.credential?.credentialId)
        assertEquals(fixture.input.plan.grantId, fixture.issuer.grant?.grantId)
        assertEquals(fixture.input.plan.principalOperationId, fixture.issuer.principal?.operationId)
        assertEquals(fixture.input.plan.initialCredentialOperationId, fixture.issuer.credential?.operationId)
        assertEquals(fixture.input.plan.grantOperationId, fixture.issuer.grant?.operationId)
        assertEquals(fixture.input.plan.decisionId, fixture.runtime.writtenDecisionId)
    }

    @Test fun `exact replay reuses the plan and creates no new ceremony`() {
        val fixture = Fixture(state = completeState(), reconciliation = exactReconciliation())
        val result = fixture.launcher().execute(fixture.input)
        assertEquals(OfflineFieldProofOutcome.ALREADY_APPLIED_RECONCILED, result.outcome)
        assertEquals(0, fixture.verifier.calls)
        assertEquals(0, fixture.issuer.calls)
        assertEquals(0, fixture.tty.deliveries)
    }

    @Test fun `shared database identities are rejected structurally`() {
        val same = PostgresConfiguration("jdbc:postgresql://localhost/db", "same", "secret")
        assertFailsWith<IllegalArgumentException> { OfflineDatabaseConfiguration(same, same, same) }
    }

    @Test fun `wrong database role boundary and missing secure tty fail before verification`() {
        val roleFailure = Fixture(boundaryAllowed = false)
        assertEquals(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, roleFailure.launcher().execute(roleFailure.input).outcome)
        assertEquals(0, roleFailure.verifier.calls)

        val ttyFailure = Fixture(ttyProtected = false)
        assertEquals(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, ttyFailure.launcher().execute(ttyFailure.input).outcome)
        assertEquals(0, ttyFailure.verifier.calls)
    }

    @Test fun `manifest target command and approval window mismatches fail closed`() {
        val targetMismatch = Fixture().let { it.copyInput(target = it.input.target.copy(integrationReference = "other")) }
        assertEquals(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, targetMismatch.launcher().execute(targetMismatch.input).outcome)
        val commandMismatch = Fixture().let { it.copyInput(command = it.input.command.copy(sourceOrderReference = "other")) }
        assertEquals(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, commandMismatch.launcher().execute(commandMismatch.input).outcome)
        val expired = Fixture(now = Instant.parse("2026-10-01T00:00:00Z"))
        assertEquals(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, expired.launcher().execute(expired.input).outcome)
    }

    @Test fun `credential does not appear in launcher output and mutable material is destroyed`() {
        val fixture = Fixture()
        val result = fixture.launcher().execute(fixture.input)
        assertFalse(result.toString().contains(fixture.tty.deliveredToken))
        assertEquals(1, fixture.lifecycle.created)
        assertEquals(1, fixture.lifecycle.destroyed)
        assertTrue(fixture.lifecycle.verifierCreationRejected)
    }

    @Test fun `delivery failure destroys credential and requires human review`() {
        val fixture = Fixture(deliveryFails = true)
        val result = fixture.launcher().execute(fixture.input)
        assertEquals(OfflineFieldProofOutcome.CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW, result.outcome)
        assertEquals(AttestedCeremonyStage.INITIAL_CREDENTIAL_APPLIED, result.lastStage)
        assertEquals(1, fixture.lifecycle.destroyed)
        assertEquals(0, fixture.runtime.writeCalls)
    }

    @Test fun `grant or authentication failure after delivery is terminal`() {
        val grantFailure = Fixture().also { it.issuer.failGrant = true }
        assertEquals(OfflineFieldProofOutcome.CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW, grantFailure.launcher().execute(grantFailure.input).outcome)
        assertEquals(1, grantFailure.tty.deliveries)

        val authFailure = Fixture().also { it.runtime.failAuthentication = true }
        assertEquals(OfflineFieldProofOutcome.CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW, authFailure.launcher().execute(authFailure.input).outcome)
        assertEquals(0, authFailure.runtime.writeCalls)
    }

    @Test fun `restart after credential effect never fabricates a replacement secret`() {
        val fixture = Fixture(state = emptyState().copy(principalCount = 1, credentialCount = 1, authorityOperationCount = 2))
        val result = fixture.launcher().execute(fixture.input)
        assertEquals(OfflineFieldProofOutcome.CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW, result.outcome)
        assertEquals(0, fixture.verifier.calls)
        assertEquals(0, fixture.tty.deliveries)
    }

    @Test fun `unknown writer outcome preserves decision id and is ambiguous`() {
        val fixture = Fixture(reconciliation = OfflineFieldProofReconciliation(true, false, emptyState(), false))
            .also { it.runtime.throwOnWrite = true }
        val result = fixture.launcher().execute(fixture.input)
        assertEquals(OfflineFieldProofOutcome.AMBIGUOUS_COMMIT, result.outcome)
        assertEquals(AttestedCeremonyStage.CREDENTIAL_DESTROYED, result.lastStage)
        assertEquals(fixture.input.plan.decisionId, fixture.runtime.writtenDecisionId)
    }

    @Test fun `unknown writer outcome is resolved when exact durable decision is reconciled`() {
        val fixture = Fixture().also { it.runtime.throwOnWrite = true }
        val result = fixture.launcher().execute(fixture.input)
        assertEquals(OfflineFieldProofOutcome.SUCCESS_RECONCILED, result.outcome)
        assertEquals(fixture.input.plan.decisionId, fixture.runtime.writtenDecisionId)
    }

    @Test fun `post proof missing state and wrong lineage are never accepted`() {
        val missing = Fixture(reconciliation = OfflineFieldProofReconciliation(true, false, emptyState(), false))
        assertEquals(OfflineFieldProofOutcome.POST_PROOF_MISMATCH, missing.launcher().execute(missing.input).outcome)

        val wrongLineage = Fixture(state = emptyState().copy(lineageMatches = false))
        assertEquals(OfflineFieldProofOutcome.POST_PROOF_MISMATCH, wrongLineage.launcher().execute(wrongLineage.input).outcome)
        assertEquals(0, wrongLineage.verifier.calls)
    }

    @Test fun `denied operator and verifier create no authority`() {
        val operatorDenied = Fixture(operatorAllowed = false)
        assertEquals(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, operatorDenied.launcher().execute(operatorDenied.input).outcome)
        assertEquals(0, operatorDenied.verifier.calls)

        val verifierDenied = Fixture().also { it.verifier.result = AcceptedAttestationResult.InvalidSignature }
        assertEquals(OfflineFieldProofOutcome.DENIED_BEFORE_DURABLE_EFFECT, verifierDenied.launcher().execute(verifierDenied.input).outcome)
        assertEquals(0, verifierDenied.issuer.calls)
    }

    @Test fun `rotate and revoke are absent from real attested authority surface`() {
        val names = AttestedCommandAuthorityIssuer::class.java.methods.map { it.name }.toSet()
        assertFalse("rotateCredential" in names)
        assertFalse("revokePermission" in names)
    }

    @Test fun `principal only restart continues the identical plan`() {
        val fixture=Fixture(state=emptyState().copy(principalCount=1,authorityOperationCount=1))
        assertEquals(OfflineFieldProofOutcome.SUCCESS_RECONCILED,fixture.launcher().execute(fixture.input).outcome)
        assertEquals(fixture.input.plan.principalId,fixture.issuer.principal?.principalId)
        assertEquals(fixture.input.plan.principalOperationId,fixture.issuer.principal?.operationId)
    }

    @Test fun `later operation prefix never generates replacement even when rows are inconsistent`() {
        val fixture=Fixture(state=emptyState().copy(authorityOperationCount=1,lineageMatches=false,credentialOperationPresent=true))
        assertEquals(OfflineFieldProofOutcome.CREDENTIAL_LOST_REQUIRES_HUMAN_REVIEW,fixture.launcher().execute(fixture.input).outcome)
        assertEquals(0,fixture.lifecycle.created);assertEquals(0,fixture.issuer.calls);assertEquals(0,fixture.verifier.calls)
    }

    @Test fun `decision or head incomplete state invokes reconciliation without commands`() {
        for (state in listOf(emptyState().copy(decisionCount=1,lineageMatches=false),emptyState().copy(headCount=1,lineageMatches=false))) {
            val fixture=Fixture(state=state,reconciliation=OfflineFieldProofReconciliation(false,false,state,false))
            assertEquals(OfflineFieldProofOutcome.POST_PROOF_MISMATCH,fixture.launcher().execute(fixture.input).outcome)
            assertEquals(0,fixture.verifier.calls);assertEquals(0,fixture.issuer.calls);assertEquals(0,fixture.lifecycle.created)
        }
    }

    @Test fun `production entrypoint is attested and reconciliation has no command dependencies`() {
        val root=java.nio.file.Path.of("src/main/kotlin/io/flooow/ceremony")
        val composition=java.nio.file.Files.readString(root.resolve("PostgresCeremonyComposition.kt"))
        val launcher=java.nio.file.Files.readString(root.resolve("OfflineFieldProofLauncher.kt"))
        assertTrue(composition.contains("OfflineFieldProofLauncher("))
        assertTrue(launcher.contains("ExecuteAttestedFieldProof("))
        assertFalse(composition.contains("ExecuteFieldProof("));assertFalse(launcher.contains("ExecuteFieldProof("))
        for (source in listOf("PostgresCeremonyComposition.kt","OfflineFieldProofLauncher.kt","ExecuteAttestedFieldProof.kt","PostgresOfflineFieldProofSupport.kt")) {
            val text=java.nio.file.Files.readString(root.resolve(source))
            for (forbidden in listOf("java.net.http", "okhttp", "HttpClient", "ExecuteFieldProof(")) assertFalse(text.contains(forbidden),"$source references $forbidden")
        }
        val dependencies=PostgresOfflineFieldProofReconciler::class.java.declaredConstructors.flatMap { it.parameterTypes.toList() }
        assertEquals(listOf(javax.sql.DataSource::class.java),dependencies)
    }

    private class Fixture(
        val now: Instant = NOW,
        val state: OfflineFieldProofDurableState = emptyState(),
        val reconciliation: OfflineFieldProofReconciliation = exactReconciliation(),
        val boundaryAllowed: Boolean = true,
        val ttyProtected: Boolean = true,
        val deliveryFails: Boolean = false,
        val operatorAllowed: Boolean = true,
        inputOverride: OfflineFieldProofInput? = null
    ) {
        val input: OfflineFieldProofInput = inputOverride ?: input()
        val verifier = FakeVerifier(input)
        val issuer = FakeIssuer(input)
        val runtime = FakeRuntime(input, issuer)
        val tty = FakeTty(ttyProtected, deliveryFails)
        val lifecycle = Lifecycle()

        fun launcher() = OfflineFieldProofLauncher(
            verifier, issuer, runtime, tty,
            OfflineFieldProofBoundaryVerifier { boundaryAllowed },
            object : OfflineFieldProofReconciler {
                override fun inspect(input: OfflineFieldProofInput) = state
                override fun reconcile(input: OfflineFieldProofInput) = reconciliation
            },
            OfflineFieldProofOperatorConfirmation { operatorAllowed },
            Clock.fixed(now, ZoneOffset.UTC), SecureRandom(), lifecycle
        )

        fun copyInput(
            target: FieldProofTarget = input.target,
            command: TransactionIdentityCommand = input.command
        ): Fixture = Fixture(
            now, state, reconciliation, boundaryAllowed, ttyProtected, deliveryFails, operatorAllowed,
            OfflineFieldProofInput(input.attestation, target, command, input.plan)
        )
    }

    private class FakeVerifier(input: OfflineFieldProofInput) : AcceptedAttestationVerifier {
        var calls = 0
        var result: AcceptedAttestationResult = AcceptedAttestationResult.Accepted(receipt(input))
        override fun verify(attestation: SignedApprovalAttestation): AcceptedAttestationResult { calls++; return result }
    }

    private class FakeIssuer(private val input: OfflineFieldProofInput) : AttestedCommandAuthorityIssuer {
        var calls = 0
        var principal: AttestedPrincipalRequest? = null
        var credential: AttestedInitialCredentialRequest? = null
        var grant: AttestedGrantRequest? = null
        var failGrant = false
        override fun issuePrincipal(request: AttestedPrincipalRequest): AttestedAuthorityResult {
            calls++; principal = request; return applied(request.operationId)
        }
        override fun bindInitialCredential(request: AttestedInitialCredentialRequest): AttestedAuthorityResult {
            calls++; credential = request.copy(secretVerifier = request.secretVerifier.copyOf()); return applied(request.operationId)
        }
        override fun grantPermission(request: AttestedGrantRequest): AttestedAuthorityResult {
            calls++; grant = request
            return if (failGrant) AttestedAuthorityResult.Denied(AttestedAuthorityFailure.INTEGRITY_FAILURE)
            else applied(request.operationId)
        }
        private fun applied(id: UUID) = AttestedAuthorityResult.Applied(
            AttestedAuthorityReceipt(id, "1".repeat(64), "2".repeat(64), NOW)
        )
    }

    private class FakeRuntime(
        private val input: OfflineFieldProofInput,
        private val issuer: FakeIssuer
    ) : AttestedRuntimeBoundary {
        var failAuthentication = false
        var throwOnWrite = false
        var writeCalls = 0
        var writtenDecisionId: UUID? = null
        override fun matchesTarget(target: FieldProofTarget) = true
        override fun authenticate(token: String): AuthenticatedCommand? {
            if (failAuthentication) return null
            val credential = CommandCredential.parse(token) ?: return null
            return credential.use {
                CommandCredentialVerifier.fromPersistence(issuer.credential!!.secretVerifier).let { verifier ->
                    AuthenticatedCommand.verify(
                        credential, verifier, input.attestation.manifest.organizationId, input.plan.principalId,
                        input.attestation.manifest.mercadoLivreConnectionId,
                        input.attestation.manifest.omieConnectionId, 1
                    )
                }
            }
        }
        override fun write(actor: AuthenticatedCommand, command: TransactionIdentityCommand) =
            error("Legacy write is unavailable")
        override fun writeAttested(
            actor: AuthenticatedCommand,
            command: TransactionIdentityCommand,
            manifest: ApprovalManifest
        ): TransactionIdentityWriteResult {
            writeCalls++
            writtenDecisionId = command.decisionId
            if (throwOnWrite) throw IllegalStateException("unknown commit outcome")
            return TransactionIdentityWriteResult.Applied(command.decisionId, "3".repeat(64))
        }
    }

    private class FakeTty(private val protected: Boolean, private val fails: Boolean) : ProtectedTty {
        var deliveries = 0
        var deliveredToken = ""
        override fun isProtected() = protected
        override fun deliverOnce(token: CharArray) {
            deliveries++
            deliveredToken = String(token)
            token.fill('\u0000')
            if (fails) throw IllegalStateException("delivery failed")
        }
    }

    private class Lifecycle : CredentialLifecycleObserver {
        var created = 0
        var destroyed = 0
        var verifierCreationRejected = false
        override fun created() { created++ }
        override fun destroyed(verifierCreationRejected: Boolean) {
            destroyed++
            this.verifierCreationRejected = verifierCreationRejected
        }
    }

    private companion object {
        val NOW: Instant = Instant.parse("2026-09-30T12:00:00Z")
        fun id(n: Int) = UUID.fromString("92000000-0000-4000-8000-${n.toString().padStart(12, '0')}")
        fun input(): OfflineFieldProofInput {
            val organizationId = OrganizationId.parse(id(1).toString())
            val manifest = ApprovalManifest(
                1, id(2), organizationId, id(3), id(4), "source-order", "integration-reference",
                MarketplaceOrderId.parse(id(5).toString()), SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,
                GovernanceSubjectId(id(6)), GovernanceSourceId(id(7)), NOW.minusSeconds(60), NOW.plusSeconds(60),
                GovernanceSubjectId(id(8)), GovernanceSubjectId(id(9)), CredentialDeliveryMethod.PROTECTED_TTY_ONE_TIME,
                GovernanceSubjectId(id(10)), ImmediateRevocationPolicy.SEPARATE_APPROVAL_REQUIRED,
                "approved field proof", "offline-launcher-test", id(11), "a".repeat(64)
            )
            val attestation = SignedApprovalAttestation.parse(
                manifest, "Ed25519", SignerKeyId(id(12)), SignerKeyFingerprint("b".repeat(64)),
                Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(64) { 1 })
            )
            val target = FieldProofTarget(
                organizationId, id(3), id(4), "source-order", "integration-reference", id(5),
                "approved field proof", "offline-launcher-test", id(11)
            )
            val command = TransactionIdentityCommand(
                id(20), "source-order", id(5), TransactionIdentityKind.CONFIRMED,
                ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION, "offline-launcher-test", id(11)
            )
            val plan = OfflineFieldProofExecutionPlan(
                1, id(13), CommandPrincipalId(id(14)), id(15), id(16), id(17), id(18), id(19), id(20)
            )
            return OfflineFieldProofInput(attestation, target, command, plan)
        }
        fun receipt(input: OfflineFieldProofInput) = AcceptedAttestationReceipt(
            input.attestation.manifest.organizationId, input.attestation.manifest.manifestId,
            "c".repeat(64), "d".repeat(64), NOW, NOW
        )
        fun emptyState() = OfflineFieldProofDurableState(0, 0, 0, 0, 0, 0, true)
        fun completeState() = OfflineFieldProofDurableState(1, 1, 1, 3, 1, 1, true)
        fun exactReconciliation() = OfflineFieldProofReconciliation(true, true, completeState(), true)
    }
}
