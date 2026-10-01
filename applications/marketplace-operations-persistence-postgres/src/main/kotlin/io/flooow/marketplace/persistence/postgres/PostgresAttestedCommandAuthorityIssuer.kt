package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.ApprovalManifest
import io.flooow.marketplace.operations.authorization.AttestedAuthorityFailure
import io.flooow.marketplace.operations.authorization.AttestedAuthorityReceipt
import io.flooow.marketplace.operations.authorization.AttestedAuthorityResult
import io.flooow.marketplace.operations.authorization.AttestedCommandAuthorityIssuer
import io.flooow.marketplace.operations.authorization.AttestedGrantRequest
import io.flooow.marketplace.operations.authorization.AttestedInitialCredentialRequest
import io.flooow.marketplace.operations.authorization.AttestedPrincipalRequest
import org.postgresql.util.PSQLException
import java.sql.Connection
import java.sql.PreparedStatement
import java.sql.ResultSet
import java.sql.SQLException
import java.sql.Timestamp
import java.util.UUID
import javax.sql.DataSource

/** V042 command-authority adapter. Its DataSource must authenticate only as flooow_command_issuer. */
class PostgresAttestedCommandAuthorityIssuer(private val dataSource: DataSource) : AttestedCommandAuthorityIssuer {
    override fun issuePrincipal(request: AttestedPrincipalRequest): AttestedAuthorityResult = execute(
        request.manifestClaim,
        BEGIN_PRINCIPAL_SQL,
        APPLY_PRINCIPAL_SQL,
        bindBase = { statement ->
            var index = 1
            statement.setObject(index++, request.organizationId.value)
            statement.setObject(index++, request.manifestId)
            statement.setObject(index++, request.operationId)
            statement.setObject(index++, request.principalId.value)
            bindManifest(statement, index, request.manifestClaim)
        }
    )

    override fun bindInitialCredential(request: AttestedInitialCredentialRequest): AttestedAuthorityResult {
        val secretVerifier = request.secretVerifier.copyOf()
        return execute(
            request.manifestClaim,
            BEGIN_INITIAL_CREDENTIAL_SQL,
            APPLY_INITIAL_CREDENTIAL_SQL,
            bindBase = { statement ->
                var index = 1
                statement.setObject(index++, request.organizationId.value)
                statement.setObject(index++, request.manifestId)
                statement.setObject(index++, request.operationId)
                statement.setObject(index++, request.principalId.value)
                statement.setObject(index++, request.credentialId)
                statement.setBytes(index++, secretVerifier)
                bindManifest(statement, index, request.manifestClaim)
            }
        )
    }

    override fun grantPermission(request: AttestedGrantRequest): AttestedAuthorityResult = execute(
        request.manifestClaim,
        BEGIN_GRANT_SQL,
        APPLY_GRANT_SQL,
        bindBase = { statement ->
            var index = 1
            statement.setObject(index++, request.organizationId.value)
            statement.setObject(index++, request.manifestId)
            statement.setObject(index++, request.operationId)
            statement.setObject(index++, request.principalId.value)
            statement.setObject(index++, request.grantId)
            bindManifest(statement, index, request.manifestClaim)
        }
    )

    private fun execute(
        expectedManifest: ApprovalManifest,
        beginSql: String,
        applySql: String,
        bindBase: (PreparedStatement) -> Int
    ): AttestedAuthorityResult {
        dataSource.connection.use { connection ->
            connection.autoCommit = false
            connection.transactionIsolation = Connection.TRANSACTION_READ_COMMITTED
            try {
                val snapshot = connection.prepareStatement(beginSql).use { statement ->
                    bindBase(statement)
                    statement.executeQuery().use { rows ->
                        check(rows.next()) { "V042 BEGIN returned no immutable snapshot" }
                        val value = ImmutableAcceptedAttestationSnapshot.fromV042(rows)
                        check(!rows.next()) { "V042 BEGIN returned more than one immutable snapshot" }
                        value
                    }
                }

                ImmutableAcceptedAttestationVerifier.verify(expectedManifest, snapshot)?.let { failure ->
                    connection.rollback()
                    return AttestedAuthorityResult.Denied(failure)
                }

                val result = connection.prepareStatement(applySql).use { statement ->
                    var index = bindBase(statement)
                    index = bindSnapshot(statement, index, snapshot)
                    check(index == statement.parameterMetaData.parameterCount + 1) {
                        "V042 APPLY parameter contract mismatch"
                    }
                    statement.executeQuery().use { rows ->
                        check(rows.next()) { "V042 APPLY returned no receipt" }
                        val value = mapReceipt(rows)
                        check(!rows.next()) { "V042 APPLY returned more than one receipt" }
                        value
                    }
                }
                connection.commit()
                return result
            } catch (failure: SQLException) {
                connection.rollback()
                return mapSql(failure)?.let(AttestedAuthorityResult::Denied) ?: throw failure
            } catch (_: IllegalArgumentException) {
                connection.rollback()
                return AttestedAuthorityResult.Denied(AttestedAuthorityFailure.UNSUPPORTED_CANONICAL_FORM)
            } catch (failure: Throwable) {
                connection.rollback()
                throw failure
            }
        }
    }

    private fun bindManifest(statement: PreparedStatement, firstIndex: Int, manifest: ApprovalManifest): Int {
        var index = firstIndex
        statement.setInt(index++, manifest.schemaVersion)
        statement.setObject(index++, manifest.manifestId)
        statement.setObject(index++, manifest.organizationId.value)
        statement.setObject(index++, manifest.mercadoLivreConnectionId)
        statement.setObject(index++, manifest.omieConnectionId)
        statement.setString(index++, manifest.sourceOrderReference)
        statement.setString(index++, manifest.integrationReference)
        statement.setObject(index++, manifest.marketplaceOrderId.value)
        statement.setString(index++, manifest.permission.name)
        statement.setObject(index++, manifest.accountableOperator.value)
        statement.setObject(index++, manifest.approvalSource.value)
        statement.setTimestamp(index++, Timestamp.from(manifest.approvalWindowStart))
        statement.setTimestamp(index++, Timestamp.from(manifest.approvalWindowEnd))
        statement.setObject(index++, manifest.revocationOwner.value)
        statement.setObject(index++, manifest.credentialCustodian.value)
        statement.setString(index++, manifest.credentialDeliveryMethod.name)
        statement.setObject(index++, manifest.credentialRotationOwner.value)
        statement.setString(index++, manifest.immediateRevocationPolicy.name)
        statement.setString(index++, manifest.reason)
        statement.setString(index++, manifest.provenance)
        statement.setObject(index++, manifest.correlationId)
        statement.setString(index++, manifest.evidenceBindingFingerprint)
        return index
    }

    private fun bindSnapshot(
        statement: PreparedStatement,
        firstIndex: Int,
        snapshot: ImmutableAcceptedAttestationSnapshot
    ): Int {
        var index = firstIndex
        statement.setInt(index++, snapshot.artifactVersion)
        statement.setInt(index++, snapshot.canonicalizationVersion)
        statement.setBytes(index++, snapshot.canonicalManifestBytes())
        statement.setString(index++, snapshot.manifestDigest)
        statement.setBytes(index++, snapshot.canonicalSignaturePreimageBytes())
        statement.setString(index++, snapshot.algorithmId)
        statement.setObject(index++, snapshot.signerSubjectId)
        statement.setObject(index++, snapshot.signerKeyId)
        statement.setInt(index++, snapshot.signerKeyRevision)
        statement.setString(index++, snapshot.signerKeyFingerprint)
        statement.setString(index++, snapshot.signerKeyLineageFingerprint)
        statement.setBytes(index++, snapshot.subjectPublicKeyInfoDer())
        statement.setBytes(index++, snapshot.signatureBytes())
        statement.setObject(index++, snapshot.signerAuthorityId)
        statement.setInt(index++, snapshot.signerAuthorityRevision)
        statement.setString(index++, snapshot.signerAuthorityFingerprint)
        statement.setTimestamp(index++, Timestamp.from(snapshot.verifiedAt))
        statement.setString(index++, snapshot.acceptedProofFingerprint)
        statement.setString(index++, snapshot.signedEvidenceBindingFingerprint)
        return index
    }

    private fun mapReceipt(rows: ResultSet): AttestedAuthorityResult {
        val receipt = AttestedAuthorityReceipt(
            rows.getObject("result_operation_id", UUID::class.java),
            rows.getString("result_intent_fingerprint"),
            rows.getString("result_receipt_fingerprint"),
            rows.getTimestamp("result_effect_time").toInstant()
        )
        return when (rows.getString("outcome")) {
            "APPLIED" -> AttestedAuthorityResult.Applied(receipt)
            "ALREADY_APPLIED" -> AttestedAuthorityResult.AlreadyApplied(receipt)
            else -> error("Unknown V042 APPLY outcome")
        }
    }

    private fun mapSql(failure: SQLException): AttestedAuthorityFailure? {
        val detail = (failure as? PSQLException)?.serverErrorMessage?.detail
        return when (failure.sqlState) {
            "P0015", "42501" -> AttestedAuthorityFailure.GOVERNANCE_UNAVAILABLE
            "P0016" -> AttestedAuthorityFailure.GOVERNANCE_CONFLICT
            "P0017" -> when (detail) {
                "SCOPE_MISMATCH" -> AttestedAuthorityFailure.SCOPE_MISMATCH
                "EXPIRED_OR_NOT_YET_VALID" -> AttestedAuthorityFailure.EXPIRED_OR_NOT_YET_VALID
                else -> null
            }
            "P0018" -> when (detail) {
                "UNSUPPORTED_CANONICAL_FORM" -> AttestedAuthorityFailure.UNSUPPORTED_CANONICAL_FORM
                "INTEGRITY_FAILURE" -> AttestedAuthorityFailure.INTEGRITY_FAILURE
                else -> null
            }
            "23502", "23503", "23505", "23514" -> AttestedAuthorityFailure.INTEGRITY_FAILURE
            else -> null
        }
    }

    private companion object {
        val BEGIN_PRINCIPAL_SQL = "SELECT * FROM public.s2a_v042_begin_attested_principal_verification(${"?,".repeat(25)}?)"
        val APPLY_PRINCIPAL_SQL = "SELECT * FROM public.s2a_v042_apply_attested_principal(${"?,".repeat(44)}?)"
        val BEGIN_INITIAL_CREDENTIAL_SQL = "SELECT * FROM public.s2a_v042_begin_attested_initial_credential_verification(${"?,".repeat(27)}?)"
        val APPLY_INITIAL_CREDENTIAL_SQL = "SELECT * FROM public.s2a_v042_apply_attested_initial_credential(${"?,".repeat(46)}?)"
        val BEGIN_GRANT_SQL = "SELECT * FROM public.s2a_v042_begin_attested_grant_verification(${"?,".repeat(26)}?)"
        val APPLY_GRANT_SQL = "SELECT * FROM public.s2a_v042_apply_attested_grant(${"?,".repeat(45)}?)"
    }
}
