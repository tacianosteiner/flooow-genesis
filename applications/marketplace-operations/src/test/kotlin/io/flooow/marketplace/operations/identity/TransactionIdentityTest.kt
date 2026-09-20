package io.flooow.marketplace.operations.identity

import io.flooow.marketplace.operations.authorization.*
import io.flooow.organization.OrganizationId
import java.util.Base64
import java.util.UUID
import java.time.LocalDateTime
import kotlin.test.*

class TransactionIdentityTest {
    private fun actor(): AuthenticatedCommand {
        val c = assertNotNull(CommandCredential.parse("fc1.${UUID.randomUUID()}." +
            Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(32) { 1 })))
        return assertNotNull(AuthenticatedCommand.verify(c,CommandCredentialVerifier.fromCredential(c),
            OrganizationId.parse(UUID.randomUUID().toString()),CommandPrincipalId(UUID.randomUUID()),UUID.randomUUID(),UUID.randomUUID(),1))
    }
    private fun command() = TransactionIdentityCommand(UUID.randomUUID(),"OMIE-STABLE",UUID.randomUUID(),
        TransactionIdentityKind.CONFIRMED,ExplicitTransactionIdentityReason.EXPLICIT_CONFIRMATION,"explicit evidence",UUID.randomUUID())

    @Test
    fun `initial and correction reasons have exact relation semantics`() {
        val c = command()
        assertFailsWith<IllegalArgumentException> { c.copy(reason=ExplicitTransactionIdentityReason.CORRECTION) }
        assertFailsWith<IllegalArgumentException> { c.copy(supersedesDecisionId=UUID.randomUUID()) }
        assertFailsWith<IllegalArgumentException> { c.copy(kind=TransactionIdentityKind.REJECTED) }
        assertNotNull(c.copy(kind=TransactionIdentityKind.REJECTED,reason=ExplicitTransactionIdentityReason.EXPLICIT_REJECTION))
        assertNotNull(c.copy(reason=ExplicitTransactionIdentityReason.CORRECTION,supersedesDecisionId=UUID.randomUUID()))
        listOf("", " x", "x ", "x\n", "é".repeat(129)).forEach {
            assertFailsWith<IllegalArgumentException> { c.copy(sourceOrderReference=it) }
        }
    }

    @Test
    fun `intent excludes replay metadata but commits to actor relation and explicit evidence`() {
        val actor = actor(); val c = command()
        val hash = c.intentFingerprint(actor)
        assertEquals(64,hash.length)
        assertEquals(hash,c.copy(decisionId=UUID.randomUUID(),correlationId=UUID.randomUUID()).intentFingerprint(actor))
        assertNotEquals(hash,c.copy(provenance="other authority evidence").intentFingerprint(actor))
        assertNotEquals(hash,c.copy(marketplaceOrderId=UUID.randomUUID()).intentFingerprint(actor))
        assertNotEquals(hash,c.copy(sourceOrderReference="other subject").intentFingerprint(actor))
        assertNotEquals(hash,c.intentFingerprint(actor()))
    }

    @Test
    fun `semantic fingerprint commits to durable ML grant and V3 identity but not equivalent observation coordinates`() {
        val actor=actor(); val intent=command().intentFingerprint(actor)
        val grant=CommandAuthorizationLineage(actor.principalId,UUID.randomUUID(),1,
            CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE,"command-authorization/1","b".repeat(64))
        val evidence=TransactionIdentityEvidence("marketplace-economic.order-source",0,0,"ML-A","BRL",
            "marketplace-economic.omie-transaction-evidence.reacquisition-v3",0,0,"a".repeat(64),LocalDateTime.parse("2026-09-18T12:00:00"))
        val fp=evidence.decisionFingerprint(intent,actor,grant)
        assertEquals(fp,evidence.copy(omieProgressVersion=1,omieRecordOrdinal=7).decisionFingerprint(intent,actor,grant))
        assertNotEquals(fp,evidence.copy(mlProgressVersion=1).decisionFingerprint(intent,actor,grant))
        assertNotEquals(fp,evidence.copy(omieSemanticFingerprint="c".repeat(64)).decisionFingerprint(intent,actor,grant))
        assertNotEquals(fp,evidence.decisionFingerprint(intent,actor,grant.copy(grantRevision=2)))
    }
}
