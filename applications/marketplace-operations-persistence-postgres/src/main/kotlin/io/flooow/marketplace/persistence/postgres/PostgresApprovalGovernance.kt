package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.ApprovalGovernance
import io.flooow.marketplace.operations.authorization.ApprovalGovernanceFingerprintCodec
import io.flooow.marketplace.operations.authorization.GovernanceAppendReceipt
import io.flooow.marketplace.operations.authorization.GovernanceAppendResult
import io.flooow.marketplace.operations.authorization.SignerAuthorityId
import io.flooow.marketplace.operations.authorization.SignerAuthorityRevision
import io.flooow.marketplace.operations.authorization.SignerKeyId
import io.flooow.marketplace.operations.authorization.SignerKeyRevision
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.PreparedStatement
import java.sql.ResultSet
import java.sql.SQLException
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import javax.sql.DataSource

/** Narrow V040 adapter. The DataSource must authenticate with approval-governance capability. */
class PostgresApprovalGovernance(private val dataSource: DataSource) : ApprovalGovernance {
    override fun appendSignerKeyRevision(revision: SignerKeyRevision): GovernanceAppendResult {
        val computed = ApprovalGovernanceFingerprintCodec.signerKeyFingerprint(revision)
        if (computed != revision.lineageFingerprint) return GovernanceAppendResult.IntegrityFailure
        return transact { connection ->
            connection.prepareStatement(KEY_APPEND).use { statement ->
                var index = 1
                statement.setObject(index++, revision.organizationId.value)
                statement.setObject(index++, revision.signerKeyId.value)
                statement.setInt(index++, revision.revision)
                statement.setObject(index++, revision.signerSubjectId.value)
                statement.setString(index++, revision.algorithmId)
                statement.setBytes(index++, revision.subjectPublicKeyInfo.bytes())
                statement.setString(index++, revision.signerKeyFingerprint.value)
                statement.setString(index++, revision.state.name)
                statement.setTimestamp(index++, Timestamp.from(revision.validFrom))
                statement.setTimestamp(index++, Timestamp.from(revision.effectiveAt))
                statement.setNullableInt(index++, revision.supersedesRevision)
                statement.setString(index++, computed.value)
                statement.setString(index++, revision.reason)
                statement.setString(index++, revision.provenance)
                statement.setObject(index, revision.correlationId)
                statement.executeQuery().use { result ->
                    check(result.next()) { "Approval-governance key append returned no receipt" }
                    val receipt = GovernanceAppendReceipt.SignerKey(
                        OrganizationId.parse(result.getObject("result_organization_id", UUID::class.java).toString()),
                        SignerKeyId(result.getObject("result_signer_key_id", UUID::class.java)),
                        result.getInt("result_revision"), result.getString("result_fingerprint"),
                        result.instant("result_recorded_at")
                    )
                    result.outcome(receipt)
                }
            }
        }
    }

    override fun appendSignerAuthorityRevision(revision: SignerAuthorityRevision): GovernanceAppendResult {
        val computed = ApprovalGovernanceFingerprintCodec.signerAuthorityFingerprint(revision)
        if (computed != revision.signerAuthorityFingerprint) return GovernanceAppendResult.IntegrityFailure
        return transact { connection ->
            connection.prepareStatement(AUTHORITY_APPEND).use { statement ->
                var index = 1
                statement.setObject(index++, revision.organizationId.value)
                statement.setObject(index++, revision.signerAuthorityId.value)
                statement.setInt(index++, revision.revision)
                statement.setObject(index++, revision.signerSubjectId.value)
                statement.setObject(index++, revision.signerAuthorizingInstitutionId.value)
                statement.setString(index++, revision.signerRole.name)
                statement.setObject(index++, revision.signerKeyId.value)
                statement.setInt(index++, revision.signerKeyRevision)
                statement.setString(index++, revision.signerKeyFingerprint.value)
                statement.setString(index++, revision.approvalAction.name)
                statement.setString(index++, revision.permission.name)
                statement.setTimestamp(index++, Timestamp.from(revision.validFrom))
                statement.setTimestamp(index++, Timestamp.from(revision.validUntil))
                statement.setString(index++, revision.state.name)
                statement.setObject(index++, revision.supersedesSignerAuthorityId?.value)
                statement.setString(index++, computed.value)
                statement.setString(index++, revision.reason)
                statement.setString(index++, revision.provenance)
                statement.setObject(index++, revision.approvalSourceId.value)
                statement.setObject(index, revision.correlationId)
                statement.executeQuery().use { result ->
                    check(result.next()) { "Approval-governance authority append returned no receipt" }
                    val receipt = GovernanceAppendReceipt.SignerAuthority(
                        OrganizationId.parse(result.getObject("result_organization_id", UUID::class.java).toString()),
                        SignerAuthorityId(result.getObject("result_signer_authority_id", UUID::class.java)),
                        result.getInt("result_revision"), result.getString("result_fingerprint"),
                        result.instant("result_decided_at")
                    )
                    result.outcome(receipt)
                }
            }
        }
    }

    private fun transact(operation: (Connection) -> GovernanceAppendResult): GovernanceAppendResult =
        dataSource.connection.use { connection ->
            connection.autoCommit = false
            connection.transactionIsolation = Connection.TRANSACTION_READ_COMMITTED
            try {
                operation(connection).also { connection.commit() }
            } catch (failure: SQLException) {
                connection.rollback()
                when (failure.sqlState) {
                    "P0013", "42501" -> GovernanceAppendResult.GovernanceUnavailable
                    "P0014", "23505" -> GovernanceAppendResult.Conflict
                    "23502", "23503", "23514" -> GovernanceAppendResult.IntegrityFailure
                    "P0010", "P0011", "P0012" -> throw failure
                    else -> throw failure
                }
            } catch (failure: Throwable) {
                connection.rollback()
                throw failure
            }
        }

    private fun ResultSet.outcome(receipt: GovernanceAppendReceipt): GovernanceAppendResult =
        when (getString("outcome")) {
            "APPLIED" -> GovernanceAppendResult.Applied(receipt)
            "ALREADY_APPLIED" -> GovernanceAppendResult.AlreadyApplied(receipt)
            else -> error("Unknown approval-governance append outcome")
        }

    private fun ResultSet.instant(column: String): Instant = getTimestamp(column).toInstant()

    private fun PreparedStatement.setNullableInt(index: Int, value: Int?) {
        if (value == null) setObject(index, null) else setInt(index, value)
    }

    private companion object {
        const val KEY_APPEND = """
            SELECT * FROM public.s2a_append_signer_key_revision(
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """
        const val AUTHORITY_APPEND = """
            SELECT * FROM public.s2a_append_signer_authority_revision(
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """
    }
}
