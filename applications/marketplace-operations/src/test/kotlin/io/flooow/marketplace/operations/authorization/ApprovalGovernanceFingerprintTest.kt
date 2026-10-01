package io.flooow.marketplace.operations.authorization

import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotEquals

class ApprovalGovernanceFingerprintTest {
    private val organization = OrganizationId.parse("11111111-1111-4111-8111-111111111111")
    private val keyId = SignerKeyId(UUID.fromString("22222222-2222-4222-8222-222222222222"))
    private val subjectId = GovernanceSubjectId(UUID.fromString("33333333-3333-4333-8333-333333333333"))
    private val authority1 = SignerAuthorityId(UUID.fromString("44444444-4444-4444-8444-444444444441"))
    private val authority2 = SignerAuthorityId(UUID.fromString("44444444-4444-4444-8444-444444444442"))
    private val institution = GovernanceInstitutionId(UUID.fromString("55555555-5555-4555-8555-555555555555"))
    private val source = GovernanceSourceId(UUID.fromString("66666666-6666-4666-8666-666666666666"))
    private val spki = SignerPublicKeyInfo.parse("302a300506032b6570032100d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a".hex())
    private val keyFingerprint = SignerKeyFingerprint("06e3fd8fda29bb60ab59557de61edb0aecdb231134be30e75b455f8e1b792fa9")
    private val keyR1Hash = "9e83dedfa91c44e001cbf4dbbe729436942ca5b6a568865eff3641e45651de65"
    private val authorityR1Hash = "983e222e3e8d9692261db6613c3f0767947c32399493c3ae7de1824aa6371254"
    private val zeroHash = "0".repeat(64)

    @Test fun `G01 G02 G03 G04 frozen key and authority golden vectors`() {
        val key1 = key(1, SignerKeyState.ACTIVE, "2026-09-25T12:00:00.000000Z", null, null)
        assertEquals(383, ApprovalGovernanceFingerprintCodec.signerKeyPreimage(key1).size)
        assertEquals(keyR1Hash, ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(key1).value)
        val key2 = key(2, SignerKeyState.RETIRED, "2026-10-01T12:00:00.000000Z", 1, SignerKeyLineageFingerprint(keyR1Hash))
        assertEquals(455, ApprovalGovernanceFingerprintCodec.signerKeyPreimage(key2).size)
        assertEquals("7910bae04e816d4f94cd2086c7963d66d104eb2e33d9795fa14e4f0ca47e21e4", ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(key2).value)

        val authorityRevision1 = authority(authority1, 1, SignerAuthorityState.ENABLED, null, null)
        assertEquals(551, ApprovalGovernanceFingerprintCodec.signerAuthorityPreimage(authorityRevision1).size)
        assertEquals(authorityR1Hash, ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(authorityRevision1).value)
        val authorityRevision2 = authority(authority2, 2, SignerAuthorityState.DISABLED, authority1, SignerAuthorityFingerprint(authorityR1Hash))
        assertEquals(658, ApprovalGovernanceFingerprintCodec.signerAuthorityPreimage(authorityRevision2).size)
        assertEquals("04cb49bc072d0d5466a767f5bc0424e1e3f7fcd6ae486bd3b6bf4f45328452a6", ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(authorityRevision2).value)
    }

    @Test fun `G05 G06 G07 G08 semantic and predecessor mutations have frozen hashes`() {
        assertEquals("d46f26319b9291fe173f9d71767f59a7b04bb455782e037b21e59fc03247a0c9",
            ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(key(1, SignerKeyState.RETIRED, "2026-09-25T12:00:00.000000Z", null, null)).value)
        assertEquals("7cec3b60b5aff97c7056ec2e0261d979681900133c76edea4a059bfed3bb6858",
            ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(key(2, SignerKeyState.RETIRED, "2026-10-01T12:00:00.000000Z", 1, SignerKeyLineageFingerprint(zeroHash))).value)
        assertEquals("ecf57994085f857f6eb419d397244d3acc6695656cd03388edf1d3cecb2ed95b",
            ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(authority(authority1, 1, SignerAuthorityState.DISABLED, null, null)).value)
        assertEquals("d9aefc960283cac9c386af0a0af728e29e1991d424c0e9fc423562d6032e01d2",
            ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(authority(authority2, 2, SignerAuthorityState.DISABLED, authority1, SignerAuthorityFingerprint(zeroHash))).value)
    }

    @Test fun `G09 G10 excluded metadata is fingerprint neutral`() {
        val key = key(1, SignerKeyState.ACTIVE, "2026-09-25T12:00:00.000000Z", null, null)
        val changedKey = key.copy(reason = "Lifecycle review", provenance = "golden-vector-v1-metadata-mutation", correlationId = UUID.fromString("77777777-7777-4777-8777-777777777777"))
        assertContentEquals(ApprovalGovernanceFingerprintCodec.signerKeyPreimage(key), ApprovalGovernanceFingerprintCodec.signerKeyPreimage(changedKey))
        val authority = authority(authority1, 1, SignerAuthorityState.ENABLED, null, null)
        val changedAuthority = authority.copy(reason = "Governance review", provenance = "golden-vector-v1-metadata-mutation", correlationId = UUID.fromString("88888888-8888-4888-8888-888888888888"))
        assertContentEquals(ApprovalGovernanceFingerprintCodec.signerAuthorityPreimage(authority), ApprovalGovernanceFingerprintCodec.signerAuthorityPreimage(changedAuthority))
    }

    @Test fun `G11 SPKI is canonical fingerprinted and defensively copied`() {
        assertEquals(keyFingerprint, spki.fingerprint())
        val first = spki.bytes(); first[0] = 0
        assertNotEquals(0, spki.bytes()[0].toInt())
        assertFailsWith<IllegalArgumentException> { SignerPublicKeyInfo.parse(ByteArray(44)) }
    }

    @Test fun `G12 G13 G14 malformed canonical inputs are rejected without transformation`() {
        assertFailsWith<IllegalArgumentException> { GovernanceSubjectId(UUID(0, 0)) }
        assertFailsWith<IllegalArgumentException> { key(1, SignerKeyState.ACTIVE, "2026-09-25T12:00:00.000000001Z", null, null) }
        assertFailsWith<IllegalArgumentException> { key(1, SignerKeyState.ACTIVE, "2026-09-25T12:00:00.000000Z", null, null).copy(reason = " padded") }
        assertFailsWith<IllegalArgumentException> { key(1, SignerKeyState.ACTIVE, "2026-09-25T12:00:00.000000Z", null, null).copy(reason = "e\u0301") }
        assertFailsWith<IllegalArgumentException> { key(1, SignerKeyState.ACTIVE, "2026-09-25T12:00:00.000000Z", null, null).copy(reason = "bad\ntext") }
        key(1, SignerKeyState.ACTIVE, "2026-09-25T12:00:00.000000Z", null, null).copy(reason = "Valid \uD83D\uDD10")
    }

    private fun key(
        revision: Int,
        state: SignerKeyState,
        effectiveAt: String,
        supersedes: Int?,
        predecessor: SignerKeyLineageFingerprint?
    ) = SignerKeyRevision(
        organization, keyId, revision, subjectId, spki, keyFingerprint, state,
        Instant.parse("2026-09-25T12:00:00.000000Z"), Instant.parse(effectiveAt), supersedes, predecessor,
        SignerKeyLineageFingerprint(zeroHash), "Synthetic governance", "golden-vector-v1", UUID.fromString("77777777-7777-4777-8777-777777777777")
    )

    private fun authority(
        id: SignerAuthorityId,
        revision: Int,
        state: SignerAuthorityState,
        predecessorId: SignerAuthorityId?,
        predecessorFingerprint: SignerAuthorityFingerprint?
    ) = SignerAuthorityRevision(
        organization, id, revision, subjectId, institution, SignerRole.S2A_FIELD_PROOF_APPROVER,
        keyId, 1, keyFingerprint, ApprovalAction.S2A_FIELD_PROOF_APPROVAL,
        SignerApprovalPermission.TRANSACTION_IDENTITY_DECISION_WRITE,
        Instant.parse("2026-09-25T12:00:00.000000Z"), Instant.parse("2026-10-25T12:00:00.000000Z"),
        state, predecessorId, predecessorFingerprint, SignerAuthorityFingerprint(zeroHash),
        "Synthetic governance", "golden-vector-v1", source, UUID.fromString("88888888-8888-4888-8888-888888888888")
    )

    private fun String.hex(): ByteArray {
        require(length % 2 == 0)
        return chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    }
}
