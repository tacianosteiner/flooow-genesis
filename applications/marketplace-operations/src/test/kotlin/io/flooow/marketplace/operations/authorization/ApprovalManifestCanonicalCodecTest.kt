package io.flooow.marketplace.operations.authorization

import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.organization.OrganizationId
import java.security.MessageDigest
import java.time.Instant
import java.time.LocalDateTime
import java.util.Base64
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse

class ApprovalManifestCanonicalCodecTest {
    @Test fun `manifest signature and evidence golden vectors are exact`() {
        val manifest = fixture()
        val bytes = ApprovalManifestCanonicalCodec.canonicalManifestBytes(manifest)
        assertEquals(793, bytes.size)
        assertEquals(MANIFEST_HEX, bytes.hex())
        assertEquals("209c15498e4da3568d52e44e121515457b4001e478221002c4b4e3c04184a8d0", ApprovalManifestCanonicalCodec.manifestDigest(bytes))
        val preimage = ApprovalManifestCanonicalCodec.canonicalSignaturePreimageBytes("Ed25519", KEY_ID, KEY_FP, ApprovalManifestCanonicalCodec.manifestDigest(bytes))
        assertEquals(222, preimage.size)
        assertEquals(SIGNATURE_HEX, preimage.hex())
        assertEquals("d011a3dd9a4eca3f07be18bacdb32720effba0babad1b80814156bb20d9bcfa2", preimage.sha256())
        val evidence = evidence()
        assertEquals(529, ApprovalEvidenceBindingCodec.canonicalBytes(evidence).size)
        assertEquals("9f61859daa192ae3482ad3dbb28cd7ebb5d2f143cdb6e83092054a80b512e965", ApprovalEvidenceBindingCodec.fingerprint(evidence))
        assertFalse(ApprovalEvidenceBindingCodec.canonicalBytes(evidence).contentEquals(ApprovalEvidenceBindingCodec.canonicalBytes(evidence.copy(omieCurrency="BRL"))))
    }

    @Test fun `every manifest semantic field is bound and canonical primitives fail closed`() {
        val original = fixture()
        val canonical = ApprovalManifestCanonicalCodec.canonicalManifestBytes(original)
        val mutations = listOf(
            original.copy(manifestId=UUID.fromString("77777777-7777-4777-8777-777777777778")),
            original.copy(organizationId=OrganizationId.parse("11111111-1111-4111-8111-111111111112")),
            original.copy(mercadoLivreConnectionId=UUID.fromString("88888888-8888-4888-8888-888888888889")),
            original.copy(omieConnectionId=UUID.fromString("99999999-9999-4999-8999-999999999998")),
            original.copy(sourceOrderReference="SO-2026-0002"), original.copy(integrationReference="INT-2026-0002"),
            original.copy(marketplaceOrderId=MarketplaceOrderId.parse("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaab")),
            original.copy(accountableOperator=GovernanceSubjectId(UUID.fromString("33333333-3333-4333-8333-333333333334"))),
            original.copy(approvalSource=GovernanceSourceId(UUID.fromString("66666666-6666-4666-8666-666666666667"))),
            original.copy(approvalWindowStart=original.approvalWindowStart.plusSeconds(1)),
            original.copy(approvalWindowEnd=original.approvalWindowEnd.plusSeconds(1)),
            original.copy(revocationOwner=GovernanceSubjectId(UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbc"))),
            original.copy(credentialCustodian=GovernanceSubjectId(UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccd"))),
            original.copy(credentialRotationOwner=GovernanceSubjectId(UUID.fromString("dddddddd-dddd-4ddd-8ddd-ddddddddddde"))),
            original.copy(reason="S2A field proof approval changed"), original.copy(provenance="revision-7.3-test"),
            original.copy(correlationId=UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeef")),
            original.copy(evidenceBindingFingerprint="8".repeat(64))
        )
        mutations.forEach { assertFalse(canonical.contentEquals(ApprovalManifestCanonicalCodec.canonicalManifestBytes(it))) }
        assertFailsWith<IllegalArgumentException> { original.copy(manifestId=UUID(0,0)) }
        assertFailsWith<IllegalArgumentException> { original.copy(organizationId=OrganizationId(UUID(0,0))) }
        assertFailsWith<IllegalArgumentException> { original.copy(sourceOrderReference=" padded") }
        assertFailsWith<IllegalArgumentException> { original.copy(reason="e\u0301") }
        assertFailsWith<IllegalArgumentException> { original.copy(provenance="line\nfeed") }
        assertFailsWith<IllegalArgumentException> { original.copy(approvalWindowStart=original.approvalWindowStart.plusNanos(1)) }
        assertFailsWith<IllegalArgumentException> { original.copy(approvalWindowEnd=original.approvalWindowStart) }
    }

    @Test fun `every evidence property nullable marker and Unicode scalar are bound`() {
        val original=evidence(); val canonical=ApprovalEvidenceBindingCodec.canonicalBytes(original)
        val mutations=listOf(
            original.copy(organizationId=OrganizationId.parse("11111111-1111-4111-8111-111111111112")),
            original.copy(marketplaceOrderId=MarketplaceOrderId.parse("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaab")),
            original.copy(mercadoLivreConnectionId=UUID.fromString("88888888-8888-4888-8888-888888888889")),
            original.copy(mlCapability="marketplace-economic.order-source-x"), original.copy(mlInputProgressVersion=2),
            original.copy(mlRecordOrdinal=2), original.copy(marketplaceKey="mercado-livre-x"),
            original.copy(marketplaceExternalOrderId="MLB-987654321"), original.copy(mlCurrency="USD"),
            original.copy(mlPromotionOutcome="DUPLICATE"), original.copy(omieConnectionId=UUID.fromString("99999999-9999-4999-8999-999999999998")),
            original.copy(omieCapability="marketplace-economic.omie-transaction-evidence.reacquisition-v3-x"),
            original.copy(omieInputProgressVersion=2), original.copy(omieRecordOrdinal=2),
            original.copy(omieSourceOrderReference="SO-2026-0002"), original.copy(omieIntegrationReference=null),
            original.copy(omieCurrency="BRL"), original.copy(omieSemanticFingerprintVersion=2),
            original.copy(omieSemanticFingerprint="cd".repeat(32)),
            original.copy(omieProviderRevisionLocal=original.omieProviderRevisionLocal.plusNanos(1_000))
        )
        mutations.forEach { assertFalse(canonical.contentEquals(ApprovalEvidenceBindingCodec.canonicalBytes(it))) }
        assertFalse(ApprovalEvidenceBindingCodec.canonicalBytes(original.copy(omieIntegrationReference=null))
            .contentEquals(ApprovalEvidenceBindingCodec.canonicalBytes(original.copy(omieIntegrationReference="NULL"))))
        assertFailsWith<IllegalArgumentException> { ApprovalEvidenceBindingCodec.canonicalBytes(original.copy(mlCapability="e\u0301")) }
        assertFailsWith<IllegalArgumentException> { ApprovalEvidenceBindingCodec.canonicalBytes(original.copy(mlCapability="\uD800")) }
        assertFailsWith<IllegalArgumentException> { ApprovalEvidenceBindingCodec.canonicalBytes(original.copy(mlRecordOrdinal=-1)) }
        assertFailsWith<IllegalArgumentException> { ApprovalEvidenceBindingCodec.canonicalBytes(original.copy(omieProviderRevisionLocal=original.omieProviderRevisionLocal.plusNanos(1))) }
    }

    @Test fun `signed transport is canonical and defensively owned`() {
        val raw = ByteArray(64) { it.toByte() }
        val encoded = Base64.getUrlEncoder().withoutPadding().encodeToString(raw)
        val envelope = SignedApprovalAttestation.parse(fixture(),"Ed25519",KEY_ID,KEY_FP,encoded)
        val copy = envelope.signatureBytes(); copy[0] = 99
        assertContentEquals(raw,envelope.signatureBytes())
        assertFailsWith<IllegalArgumentException> { SignedApprovalAttestation.parse(fixture(),"Ed25519",KEY_ID,KEY_FP,"$encoded=") }
        assertFailsWith<IllegalArgumentException> { SignedApprovalAttestation.parse(fixture(),"RSA",KEY_ID,KEY_FP,encoded) }
        assertFailsWith<IllegalArgumentException> { SignedApprovalAttestation.parse(fixture(),"Ed25519",KEY_ID,KEY_FP,"+") }
        assertFailsWith<IllegalArgumentException> { SignedApprovalAttestation.parse(fixture(),"Ed25519",KEY_ID,KEY_FP,"_") }
        assertFailsWith<IllegalArgumentException> { SignedApprovalAttestation.parse(fixture(),"Ed25519",KEY_ID,KEY_FP,Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(63))) }
    }

    private fun evidence()=ApprovalEvidenceBindingCodec.Evidence(
        ORG, MarketplaceOrderId.parse("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"), UUID.fromString("88888888-8888-4888-8888-888888888888"),
        "marketplace-economic.order-source",1,1,"mercado-livre","MLB-123456789","BRL","PROMOTED",
        UUID.fromString("99999999-9999-4999-8999-999999999999"),"marketplace-economic.omie-transaction-evidence.reacquisition-v3",
        1,1,"SO-2026-0001","INT-2026-0001",null,1,"ab".repeat(32),LocalDateTime.parse("2026-09-25T11:59:59.123456")
    )

    private fun fixture() = ApprovalManifest(1,UUID.fromString("77777777-7777-4777-8777-777777777777"),ORG,
        UUID.fromString("88888888-8888-4888-8888-888888888888"),UUID.fromString("99999999-9999-4999-8999-999999999999"),
        "SO-2026-0001","INT-2026-0001",MarketplaceOrderId.parse("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,GovernanceSubjectId(UUID.fromString("33333333-3333-4333-8333-333333333333")),
        GovernanceSourceId(UUID.fromString("66666666-6666-4666-8666-666666666666")),Instant.parse("2026-09-25T12:00:00Z"),Instant.parse("2026-10-25T12:00:00Z"),
        GovernanceSubjectId(UUID.fromString("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")),GovernanceSubjectId(UUID.fromString("cccccccc-cccc-4ccc-8ccc-cccccccccccc")),
        CredentialDeliveryMethod.PROTECTED_TTY_ONE_TIME,GovernanceSubjectId(UUID.fromString("dddddddd-dddd-4ddd-8ddd-dddddddddddd")),
        ImmediateRevocationPolicy.SEPARATE_APPROVAL_REQUIRED,"S2A field proof approval","revision-6-golden-vector",
        UUID.fromString("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"),"9f61859daa192ae3482ad3dbb28cd7ebb5d2f143cdb6e83092054a80b512e965")

    private fun ByteArray.hex()=joinToString(""){"%02x".format(it)}
    private fun ByteArray.sha256()=MessageDigest.getInstance("SHA-256").digest(this).hex()
    companion object {
        val ORG=OrganizationId.parse("11111111-1111-4111-8111-111111111111")
        val KEY_ID=SignerKeyId(UUID.fromString("22222222-2222-4222-8222-222222222222"))
        val KEY_FP=SignerKeyFingerprint("06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9")
        const val SIGNATURE_HEX="0000001f464c4f4f4f573a5332413a415050524f56414c2d5349474e41545552453a3100000007456432353531390000002432323232323232322d323232322d343232322d383232322d32323232323232323232323200000040303665336664386664613239626236306162353935353764653631656462306165636462323331313334626533306537356234353566386531623739326661390000004032303963313534393865346461333536386435326534346531323135313534353762343030316534373832323130303263346234653363303431383461386430"
        const val MANIFEST_HEX="0000001e464c4f4f4f573a5332413a415050524f56414c2d4d414e49464553543a3100000001310000002437373737373737372d373737372d343737372d383737372d3737373737373737373737370000002431313131313131312d313131312d343131312d383131312d3131313131313131313131310000002438383838383838382d383838382d343838382d383838382d3838383838383838383838380000002439393939393939392d393939392d343939392d383939392d3939393939393939393939390000000c534f2d323032362d303030310000000d494e542d323032362d303030310000002461616161616161612d616161612d346161612d386161612d616161616161616161616161000000235452414e53414354494f4e5f4944454e544954595f4445434953494f4e5f57524954450000002433333333333333332d333333332d343333332d383333332d3333333333333333333333330000002436363636363636362d363636362d343636362d383636362d3636363636363636363636360000001b323032362d30392d32355431323a30303a30302e3030303030305a0000001b323032362d31302d32355431323a30303a30302e3030303030305a0000002462626262626262622d626262622d346262622d386262622d6262626262626262626262620000002463636363636363632d636363632d346363632d386363632d6363636363636363636363630000001650524f5445435445445f5454595f4f4e455f54494d450000002464646464646464642d646464642d346464642d386464642d6464646464646464646464640000001a53455041524154455f415050524f56414c5f524551554952454400000018533241206669656c642070726f6f6620617070726f76616c000000187265766973696f6e2d362d676f6c64656e2d766563746f720000002465656565656565652d656565652d346565652d386565652d6565656565656565656565650000004039663631383539646161313932616533343832616433646262323863643765626235643266313433636462366538333039323035346138306235313265393635"
    }
}
