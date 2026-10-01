package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.authorization.*
import io.flooow.organization.OrganizationId
import org.postgresql.util.PSQLException
import java.sql.Connection
import java.sql.PreparedStatement
import java.sql.SQLException
import java.sql.Timestamp
import java.util.UUID
import javax.sql.DataSource

/** V041 trusted-verifier adapter. Its DataSource must authenticate only as the dedicated verifier principal. */
class PostgresAcceptedAttestationVerifier(private val dataSource: DataSource) : AcceptedAttestationVerifier {
    override fun verify(attestation: SignedApprovalAttestation): AcceptedAttestationResult {
        val canonicalManifest = ApprovalManifestCanonicalCodec.canonicalManifestBytes(attestation.manifest)
        val manifestDigest = ApprovalManifestCanonicalCodec.manifestDigest(canonicalManifest)
        dataSource.connection.use { connection ->
            connection.autoCommit = false
            connection.transactionIsolation = Connection.TRANSACTION_READ_COMMITTED
            try {
                val begin = connection.prepareStatement(BEGIN_SQL).use { statement ->
                    bindEnvelope(statement, attestation, canonicalManifest, manifestDigest)
                    statement.executeQuery().use { rows ->
                        check(rows.next()) { "V041 begin returned no snapshot" }
                        ImmutableAcceptedAttestationSnapshot.fromV041(
                            rows,
                            attestation.manifest,
                            attestation.algorithmId,
                            attestation.signatureBytes()
                        )
                    }
                }

                val snapshot = begin
                val verificationFailure =
                    if (
                        snapshot.signerKeyId != attestation.signerKeyId.value ||
                        snapshot.signerKeyFingerprint != attestation.signerKeyFingerprint.value
                    ) {
                        AttestedAuthorityFailure.INTEGRITY_FAILURE
                    } else {
                        ImmutableAcceptedAttestationVerifier.verify(attestation.manifest, snapshot)
                    }
                if (verificationFailure != null) {
                    connection.rollback()
                    return verificationFailure.toAcceptedResult()
                }
                val result = connection.prepareStatement(PERSIST_SQL).use { statement ->
                    var index = bindEnvelope(statement, attestation, canonicalManifest, manifestDigest)
                    statement.setBytes(index++, snapshot.canonicalSignaturePreimageBytes())
                    statement.setObject(index++, snapshot.signerSubjectId)
                    statement.setInt(index++, snapshot.signerKeyRevision)
                    statement.setString(index++, snapshot.signerKeyLineageFingerprint)
                    statement.setBytes(index++, snapshot.subjectPublicKeyInfoDer())
                    statement.setObject(index++, snapshot.signerAuthorityId)
                    statement.setInt(index++, snapshot.signerAuthorityRevision)
                    statement.setString(index++, snapshot.signerAuthorityFingerprint)
                    statement.setString(index, snapshot.acceptedProofFingerprint)
                    statement.executeQuery().use { rows ->
                        check(rows.next()) { "V041 persistence returned no receipt" }
                        val receipt = AcceptedAttestationReceipt(
                            OrganizationId.parse(rows.getObject("result_organization_id", UUID::class.java).toString()),
                            rows.getObject("result_manifest_id", UUID::class.java), rows.getString("result_manifest_digest"),
                            rows.getString("result_accepted_proof_fingerprint"), rows.getTimestamp("result_verified_at").toInstant(),
                            rows.getTimestamp("result_recorded_at").toInstant()
                        )
                        when (rows.getString("outcome")) {
                            "ACCEPTED" -> AcceptedAttestationResult.Accepted(receipt)
                            "ALREADY_ACCEPTED" -> AcceptedAttestationResult.AlreadyAccepted(receipt)
                            else -> error("Unknown V041 persistence outcome")
                        }
                    }
                }
                connection.commit()
                return result
            } catch (failure: SQLException) {
                connection.rollback()
                return mapSql(failure) ?: throw failure
            } catch (failure: IllegalArgumentException) {
                connection.rollback()
                return AcceptedAttestationResult.UnsupportedCanonicalForm
            } catch (failure: Throwable) {
                connection.rollback()
                throw failure
            }
        }
    }

    private fun bindEnvelope(
        statement: PreparedStatement,
        attestation: SignedApprovalAttestation,
        canonicalManifest: ByteArray,
        manifestDigest: String
    ): Int {
        val m = attestation.manifest
        var i = 1
        statement.setInt(i++, m.schemaVersion); statement.setObject(i++, m.manifestId)
        statement.setObject(i++, m.organizationId.value); statement.setObject(i++, m.mercadoLivreConnectionId)
        statement.setObject(i++, m.omieConnectionId); statement.setString(i++, m.sourceOrderReference)
        statement.setString(i++, m.integrationReference); statement.setObject(i++, m.marketplaceOrderId.value)
        statement.setString(i++, m.permission.name); statement.setObject(i++, m.accountableOperator.value)
        statement.setObject(i++, m.approvalSource.value); statement.setTimestamp(i++, Timestamp.from(m.approvalWindowStart))
        statement.setTimestamp(i++, Timestamp.from(m.approvalWindowEnd)); statement.setObject(i++, m.revocationOwner.value)
        statement.setObject(i++, m.credentialCustodian.value); statement.setString(i++, m.credentialDeliveryMethod.name)
        statement.setObject(i++, m.credentialRotationOwner.value); statement.setString(i++, m.immediateRevocationPolicy.name)
        statement.setString(i++, m.reason); statement.setString(i++, m.provenance); statement.setObject(i++, m.correlationId)
        statement.setString(i++, m.evidenceBindingFingerprint); statement.setInt(i++, ApprovalManifestCanonicalCodec.CANONICALIZATION_VERSION)
        statement.setBytes(i++, canonicalManifest); statement.setString(i++, manifestDigest); statement.setString(i++, attestation.algorithmId)
        statement.setObject(i++, attestation.signerKeyId.value); statement.setString(i++, attestation.signerKeyFingerprint.value)
        statement.setBytes(i++, attestation.signatureBytes())
        return i
    }

    private fun mapSql(failure: SQLException): AcceptedAttestationResult? {
        val detail = (failure as? PSQLException)?.serverErrorMessage?.detail
        return when (failure.sqlState) {
            "P0015", "42501" -> AcceptedAttestationResult.GovernanceUnavailable
            "P0016" -> AcceptedAttestationResult.GovernanceConflict
            "P0017" -> when (detail) {
                "SCOPE_MISMATCH" -> AcceptedAttestationResult.ScopeMismatch
                "EXPIRED_OR_NOT_YET_VALID" -> AcceptedAttestationResult.ExpiredOrNotYetValid
                else -> null
            }
            "P0018" -> when (detail) {
                "UNSUPPORTED_CANONICAL_FORM" -> AcceptedAttestationResult.UnsupportedCanonicalForm
                "INTEGRITY_FAILURE" -> AcceptedAttestationResult.IntegrityFailure
                else -> null
            }
            "23502", "23503", "23514" -> AcceptedAttestationResult.IntegrityFailure
            else -> null
        }
    }

    private fun AttestedAuthorityFailure.toAcceptedResult(): AcceptedAttestationResult = when (this) {
        AttestedAuthorityFailure.INVALID_SIGNATURE -> AcceptedAttestationResult.InvalidSignature
        AttestedAuthorityFailure.UNSUPPORTED_CANONICAL_FORM -> AcceptedAttestationResult.UnsupportedCanonicalForm
        AttestedAuthorityFailure.SCOPE_MISMATCH -> AcceptedAttestationResult.ScopeMismatch
        AttestedAuthorityFailure.EXPIRED_OR_NOT_YET_VALID -> AcceptedAttestationResult.ExpiredOrNotYetValid
        AttestedAuthorityFailure.GOVERNANCE_UNAVAILABLE -> AcceptedAttestationResult.GovernanceUnavailable
        AttestedAuthorityFailure.GOVERNANCE_CONFLICT -> AcceptedAttestationResult.GovernanceConflict
        AttestedAuthorityFailure.INTEGRITY_FAILURE -> AcceptedAttestationResult.IntegrityFailure
    }

    private companion object {
        val BEGIN_SQL = "SELECT * FROM public.s2a_begin_attestation_verification(${"?,".repeat(28)}?)"
        val PERSIST_SQL = "SELECT * FROM public.s2a_persist_attestation_verification_result(${"?,".repeat(37)}?)"
    }
}
