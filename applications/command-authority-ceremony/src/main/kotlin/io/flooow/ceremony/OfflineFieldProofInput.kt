package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.ApprovalManifest
import io.flooow.marketplace.operations.authorization.CommandPermission
import io.flooow.marketplace.operations.authorization.CommandPrincipalId
import io.flooow.marketplace.operations.authorization.CredentialDeliveryMethod
import io.flooow.marketplace.operations.authorization.GovernanceSourceId
import io.flooow.marketplace.operations.authorization.GovernanceSubjectId
import io.flooow.marketplace.operations.authorization.ImmediateRevocationPolicy
import io.flooow.marketplace.operations.authorization.SignedApprovalAttestation
import io.flooow.marketplace.operations.authorization.SignerApprovalPermission
import io.flooow.marketplace.operations.authorization.SignerKeyFingerprint
import io.flooow.marketplace.operations.authorization.SignerKeyId
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.identity.ExplicitTransactionIdentityReason
import io.flooow.marketplace.operations.identity.TransactionIdentityCommand
import io.flooow.marketplace.operations.identity.TransactionIdentityKind
import io.flooow.organization.OrganizationId
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import java.time.Instant
import java.util.UUID

data class OfflineFieldProofInput(
    val attestation: SignedApprovalAttestation,
    val target: FieldProofTarget,
    val command: TransactionIdentityCommand,
    val plan: OfflineFieldProofExecutionPlan
) {
    init {
        require(command.decisionId == plan.decisionId) { "Command decisionId differs from execution plan" }
    }
}

/**
 * Strict non-secret artifact loader. The transport is deliberately simpler than the signed canonical format:
 * one UTF-8 `key=value` per line, no comments, escaping, duplicate keys, unknown keys, trimming or repair.
 */
object OfflineFieldProofInputLoader {
    fun load(path: Path): OfflineFieldProofInput {
        require(Files.isRegularFile(path)) { "Field-proof input must be a regular file" }
        val bytes = Files.readAllBytes(path)
        val decoder = StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT)
        val text = decoder.decode(ByteBuffer.wrap(bytes)).toString()
        require(!text.startsWith('\uFEFF') && '\r' !in text) { "Input must be canonical UTF-8 with LF line endings" }
        val lines = text.split('\n').let { if (it.lastOrNull().isNullOrEmpty()) it.dropLast(1) else it }
        require(lines.isNotEmpty() && lines.none(String::isEmpty)) { "Input contains an empty record" }
        val values = linkedMapOf<String, String>()
        lines.forEach { line ->
            val separator = line.indexOf('=')
            require(separator > 0) { "Input record is malformed" }
            val key = line.substring(0, separator)
            val value = line.substring(separator + 1)
            require(KEY.matches(key) && value.isNotEmpty()) { "Input key or value is malformed" }
            require(values.put(key, value) == null) { "Duplicate input key: $key" }
        }
        require(values.keys == REQUIRED_KEYS) {
            "Input keys differ from the exact version-1 schema"
        }
        require(values.getValue("bundle.version") == "1") { "Unsupported input bundle version" }

        val manifest = ApprovalManifest(
            schemaVersion = strictInt(values, "manifest.schemaVersion"),
            manifestId = strictUuid(values, "manifest.manifestId"),
            organizationId = OrganizationId.parse(strictUuid(values, "manifest.organizationId").toString()),
            mercadoLivreConnectionId = strictUuid(values, "manifest.mercadoLivreConnectionId"),
            omieConnectionId = strictUuid(values, "manifest.omieConnectionId"),
            sourceOrderReference = values.getValue("manifest.sourceOrderReference"),
            integrationReference = values.getValue("manifest.integrationReference"),
            marketplaceOrderId = MarketplaceOrderId.parse(strictUuid(values, "manifest.marketplaceOrderId").toString()),
            permission = strictEnum(values, "manifest.permission"),
            accountableOperator = GovernanceSubjectId(strictUuid(values, "manifest.accountableOperator")),
            approvalSource = GovernanceSourceId(strictUuid(values, "manifest.approvalSource")),
            approvalWindowStart = strictInstant(values, "manifest.approvalWindowStart"),
            approvalWindowEnd = strictInstant(values, "manifest.approvalWindowEnd"),
            revocationOwner = GovernanceSubjectId(strictUuid(values, "manifest.revocationOwner")),
            credentialCustodian = GovernanceSubjectId(strictUuid(values, "manifest.credentialCustodian")),
            credentialDeliveryMethod = strictEnum(values, "manifest.credentialDeliveryMethod"),
            credentialRotationOwner = GovernanceSubjectId(strictUuid(values, "manifest.credentialRotationOwner")),
            immediateRevocationPolicy = strictEnum(values, "manifest.immediateRevocationPolicy"),
            reason = values.getValue("manifest.reason"),
            provenance = values.getValue("manifest.provenance"),
            correlationId = strictUuid(values, "manifest.correlationId"),
            evidenceBindingFingerprint = values.getValue("manifest.evidenceBindingFingerprint")
        )
        val attestation = SignedApprovalAttestation.parse(
            manifest,
            values.getValue("attestation.algorithmId"),
            SignerKeyId(strictUuid(values, "attestation.signerKeyId")),
            SignerKeyFingerprint(values.getValue("attestation.signerKeyFingerprint")),
            values.getValue("attestation.signatureBase64Url")
        )
        val target = FieldProofTarget(
            organizationId = OrganizationId.parse(strictUuid(values, "target.organizationId").toString()),
            mercadoLivreConnectionId = strictUuid(values, "target.mercadoLivreConnectionId"),
            omieConnectionId = strictUuid(values, "target.omieConnectionId"),
            sourceOrderReference = values.getValue("target.sourceOrderReference"),
            integrationReference = values.getValue("target.integrationReference"),
            marketplaceOrderId = strictUuid(values, "target.marketplaceOrderId"),
            reason = values.getValue("target.reason"),
            provenance = values.getValue("target.provenance"),
            correlationId = strictUuid(values, "target.correlationId"),
            permission = strictEnum(values, "target.permission")
        )
        val command = TransactionIdentityCommand(
            decisionId = strictUuid(values, "command.decisionId"),
            sourceOrderReference = values.getValue("command.sourceOrderReference"),
            marketplaceOrderId = strictUuid(values, "command.marketplaceOrderId"),
            kind = strictEnum(values, "command.kind"),
            reason = strictEnum(values, "command.reason"),
            provenance = values.getValue("command.provenance"),
            correlationId = strictUuid(values, "command.correlationId"),
            supersedesDecisionId = strictNullableUuid(values.getValue("command.supersedesDecisionId"))
        )
        val plan = OfflineFieldProofExecutionPlan(
            version = strictInt(values, "plan.version"),
            runId = strictUuid(values, "plan.runId"),
            principalId = CommandPrincipalId(strictUuid(values, "plan.principalId")),
            credentialId = strictUuid(values, "plan.credentialId"),
            grantId = strictUuid(values, "plan.grantId"),
            principalOperationId = strictUuid(values, "plan.principalOperationId"),
            initialCredentialOperationId = strictUuid(values, "plan.initialCredentialOperationId"),
            grantOperationId = strictUuid(values, "plan.grantOperationId"),
            decisionId = strictUuid(values, "plan.decisionId")
        )
        return OfflineFieldProofInput(attestation, target, command, plan)
    }

    private fun strictUuid(values: Map<String, String>, key: String): UUID = strictUuid(values.getValue(key), key)
    private fun strictUuid(value: String, key: String): UUID {
        val parsed = UUID.fromString(value)
        require(parsed.toString() == value) { "$key is not a canonical UUID" }
        return parsed
    }
    private fun strictNullableUuid(value: String): UUID? = if (value == "NULL") null else strictUuid(value, "supersedesDecisionId")
    private fun strictInstant(values: Map<String, String>, key: String): Instant {
        val value = values.getValue(key)
        val parsed = Instant.parse(value)
        require(parsed.toString() == value) { "$key is not a canonical Instant" }
        return parsed
    }
    private fun strictInt(values: Map<String, String>, key: String): Int {
        val value = values.getValue(key)
        val parsed = value.toInt()
        require(parsed.toString() == value) { "$key is not a canonical integer" }
        return parsed
    }
    private inline fun <reified T : Enum<T>> strictEnum(values: Map<String, String>, key: String): T =
        enumValueOf<T>(values.getValue(key))

    private val KEY = Regex("[A-Za-z][A-Za-z0-9.]*")
    private val REQUIRED_KEYS = linkedSetOf(
        "bundle.version",
        "manifest.schemaVersion", "manifest.manifestId", "manifest.organizationId",
        "manifest.mercadoLivreConnectionId", "manifest.omieConnectionId", "manifest.sourceOrderReference",
        "manifest.integrationReference", "manifest.marketplaceOrderId", "manifest.permission",
        "manifest.accountableOperator", "manifest.approvalSource", "manifest.approvalWindowStart",
        "manifest.approvalWindowEnd", "manifest.revocationOwner", "manifest.credentialCustodian",
        "manifest.credentialDeliveryMethod", "manifest.credentialRotationOwner",
        "manifest.immediateRevocationPolicy", "manifest.reason", "manifest.provenance",
        "manifest.correlationId", "manifest.evidenceBindingFingerprint",
        "attestation.algorithmId", "attestation.signerKeyId", "attestation.signerKeyFingerprint",
        "attestation.signatureBase64Url",
        "target.organizationId", "target.mercadoLivreConnectionId", "target.omieConnectionId",
        "target.sourceOrderReference", "target.integrationReference", "target.marketplaceOrderId",
        "target.reason", "target.provenance", "target.correlationId", "target.permission",
        "command.decisionId", "command.sourceOrderReference", "command.marketplaceOrderId", "command.kind",
        "command.reason", "command.provenance", "command.correlationId", "command.supersedesDecisionId",
        "plan.version", "plan.runId", "plan.principalId", "plan.credentialId", "plan.grantId",
        "plan.principalOperationId", "plan.initialCredentialOperationId", "plan.grantOperationId", "plan.decisionId"
    )
}
