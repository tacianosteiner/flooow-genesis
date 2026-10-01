package io.flooow.ceremony

import java.nio.file.Files
import java.util.Base64
import java.util.UUID
import kotlin.io.path.deleteIfExists
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class OfflineFieldProofInputLoaderTest {
    @Test fun `strict artifact loads the complete signed input and stable plan`() {
        withArtifact(validArtifact()) { path ->
            val input = OfflineFieldProofInputLoader.load(path)
            assertEquals(uuid(2), input.attestation.manifest.manifestId)
            assertEquals(uuid(20), input.command.decisionId)
            assertEquals(uuid(20), input.plan.decisionId)
            assertEquals(uuid(14), input.plan.principalId.value)
        }
    }

    @Test fun `unknown missing duplicate and noncanonical values are rejected`() {
        val valid = validArtifact()
        listOf(
            valid + "unknown.field=value\n",
            valid.lineSequence().filterNot { it.startsWith("plan.grantId=") }.joinToString("\n", postfix = "\n"),
            valid + "plan.grantId=${uuid(16)}\n",
            valid.replace(uuid(2).toString(), "92000000-0000-4000-8000-2"),
            valid.replace("2026-09-30T11:59:00Z", "2026-09-30T11:59:00.000Z"),
            valid.replace("command.kind=CONFIRMED", "command.kind=confirmed")
        ).forEach { malformed ->
            withArtifact(malformed) { path -> assertFailsWith<IllegalArgumentException> { OfflineFieldProofInputLoader.load(path) } }
        }
    }

    @Test fun `malformed utf8 carriage return and decision conflict are rejected`() {
        val invalidUtf8 = Files.createTempFile("field-proof-invalid", ".input")
        try {
            Files.write(invalidUtf8, byteArrayOf(0xC3.toByte(), 0x28))
            assertFailsWith<Exception> { OfflineFieldProofInputLoader.load(invalidUtf8) }
        } finally { invalidUtf8.deleteIfExists() }

        withArtifact(validArtifact().replace("\n", "\r\n")) { path ->
            assertFailsWith<IllegalArgumentException> { OfflineFieldProofInputLoader.load(path) }
        }
        withArtifact(validArtifact().replace("plan.decisionId=${uuid(20)}", "plan.decisionId=${uuid(21)}")) { path ->
            assertFailsWith<IllegalArgumentException> { OfflineFieldProofInputLoader.load(path) }
        }
    }

    private fun validArtifact(): String = listOf(
        "bundle.version=1",
        "manifest.schemaVersion=1",
        "manifest.manifestId=${uuid(2)}",
        "manifest.organizationId=${uuid(1)}",
        "manifest.mercadoLivreConnectionId=${uuid(3)}",
        "manifest.omieConnectionId=${uuid(4)}",
        "manifest.sourceOrderReference=source-order",
        "manifest.integrationReference=integration-reference",
        "manifest.marketplaceOrderId=${uuid(5)}",
        "manifest.permission=TRANSACTION_IDENTITY_DECISION_WRITE",
        "manifest.accountableOperator=${uuid(6)}",
        "manifest.approvalSource=${uuid(7)}",
        "manifest.approvalWindowStart=2026-09-30T11:59:00Z",
        "manifest.approvalWindowEnd=2026-09-30T12:01:00Z",
        "manifest.revocationOwner=${uuid(8)}",
        "manifest.credentialCustodian=${uuid(9)}",
        "manifest.credentialDeliveryMethod=PROTECTED_TTY_ONE_TIME",
        "manifest.credentialRotationOwner=${uuid(10)}",
        "manifest.immediateRevocationPolicy=SEPARATE_APPROVAL_REQUIRED",
        "manifest.reason=approved field proof",
        "manifest.provenance=offline-launcher-test",
        "manifest.correlationId=${uuid(11)}",
        "manifest.evidenceBindingFingerprint=${"a".repeat(64)}",
        "attestation.algorithmId=Ed25519",
        "attestation.signerKeyId=${uuid(12)}",
        "attestation.signerKeyFingerprint=${"b".repeat(64)}",
        "attestation.signatureBase64Url=${Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(64) { 1 })}",
        "target.organizationId=${uuid(1)}",
        "target.mercadoLivreConnectionId=${uuid(3)}",
        "target.omieConnectionId=${uuid(4)}",
        "target.sourceOrderReference=source-order",
        "target.integrationReference=integration-reference",
        "target.marketplaceOrderId=${uuid(5)}",
        "target.reason=approved field proof",
        "target.provenance=offline-launcher-test",
        "target.correlationId=${uuid(11)}",
        "target.permission=TRANSACTION_IDENTITY_DECISION_WRITE",
        "command.decisionId=${uuid(20)}",
        "command.sourceOrderReference=source-order",
        "command.marketplaceOrderId=${uuid(5)}",
        "command.kind=CONFIRMED",
        "command.reason=EXPLICIT_CONFIRMATION",
        "command.provenance=offline-launcher-test",
        "command.correlationId=${uuid(11)}",
        "command.supersedesDecisionId=NULL",
        "plan.version=1",
        "plan.runId=${uuid(13)}",
        "plan.principalId=${uuid(14)}",
        "plan.credentialId=${uuid(15)}",
        "plan.grantId=${uuid(16)}",
        "plan.principalOperationId=${uuid(17)}",
        "plan.initialCredentialOperationId=${uuid(18)}",
        "plan.grantOperationId=${uuid(19)}",
        "plan.decisionId=${uuid(20)}"
    ).joinToString("\n", postfix = "\n")

    private fun withArtifact(content: String, block: (java.nio.file.Path) -> Unit) {
        val path = Files.createTempFile("field-proof", ".input")
        try {
            Files.writeString(path, content)
            block(path)
        } finally { path.deleteIfExists() }
    }

    private fun uuid(n: Int) = UUID.fromString("92000000-0000-4000-8000-${n.toString().padStart(12, '0')}")
}
