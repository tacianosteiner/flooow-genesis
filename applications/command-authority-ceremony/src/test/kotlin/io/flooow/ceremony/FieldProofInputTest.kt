package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.CommandPermission
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class FieldProofInputTest {
    private val now = Instant.parse("2026-06-01T00:00:00Z")
    private fun approval() = HumanApproval("operator", "approval", Instant.parse("2026-01-01T00:00:00Z"), Instant.parse("2026-12-31T00:00:00Z"), "revoke", "custodian", "TTY", "rotation", "NONE")
    private fun target(permission: CommandPermission = CommandPermission.TRANSACTION_IDENTITY_DECISION_WRITE) = FieldProofTarget(OrganizationId.parse(UUID.randomUUID().toString()), UUID.randomUUID(), UUID.randomUUID(), "source", "reference", UUID.randomUUID(), "reason", "provenance", UUID.randomUUID(), permission)
    @Test fun `all named human fields and bounded approval window are mandatory`() {
        assertTrue(approval().valid(now))
        assertFalse(approval().copy(approvalSource = "").valid(now))
        assertFalse(approval().copy(windowEnd = Instant.parse("2026-01-02T00:00:00Z")).valid(now))
    }
    @Test fun `only exact pair and decision write permission are eligible`() {
        assertTrue(target().valid())
        assertFalse(target(CommandPermission.TRANSACTION_IDENTITY_POLICY_ADMIN).valid())
        assertFalse(target().copy(sourceOrderReference = "").valid())
        assertFalse(target().copy(integrationReference = "").valid())
    }
}
