package io.flooow.ceremony

import io.flooow.marketplace.operations.authorization.AuthenticatedCommand
import io.flooow.marketplace.operations.identity.TransactionIdentityCommand
import io.flooow.marketplace.operations.identity.TransactionIdentityWriteResult
import io.flooow.marketplace.persistence.postgres.PostgresCommandAuthorization
import io.flooow.marketplace.persistence.postgres.PostgresControlledCommandAuthorityIssuer
import io.flooow.marketplace.persistence.postgres.PostgresTransactionIdentityWriter
import javax.sql.DataSource

/** Explicitly keeps issuer and runtime connection ownership separate. */
class PostgresCeremonyComposition(
    issuerDataSource: DataSource,
    runtimeDataSource: DataSource,
    private val writeRecord: (java.sql.Connection, AuthenticatedCommand, TransactionIdentityCommand) -> TransactionIdentityWriteResult =
        { connection, actor, command -> PostgresTransactionIdentityWriter().record(connection, actor, command) }
) {
    val issuer = PostgresControlledCommandAuthorityIssuer(issuerDataSource)
    val runtime: RuntimeBoundary = object : RuntimeBoundary {
        private val authorization = PostgresCommandAuthorization()
        override fun matchesTarget(target: FieldProofTarget): Boolean = runtimeDataSource.connection.use { connection ->
            connection.prepareStatement(
                """SELECT EXISTS(SELECT 1
                    FROM integration_omie_transaction_evidence b
                    JOIN integration_omie_transaction_evidence_v3 v
                      USING(organization_id,connection_id,capability,input_progress_version,record_ordinal)
                    JOIN marketplace_order_identity_registry i
                      ON i.organization_id=b.organization_id
                     AND i.marketplace_order_id=?
                     AND i.marketplace_key='mercado-livre'
                     AND i.external_order_id=b.source_integration_ref
                    JOIN marketplace_order_occurrence_source_promotion p
                      ON p.organization_id=i.organization_id
                     AND p.marketplace_order_id=i.marketplace_order_id
                    JOIN integration_mercado_livre_order_source_observation s
                      ON s.organization_id=p.organization_id
                     AND s.connection_id=p.source_connection_id
                     AND s.capability=p.source_capability
                     AND s.input_progress_version=p.source_input_progress_version
                     AND s.record_ordinal=p.source_record_ordinal
                    WHERE b.organization_id=?
                      AND b.connection_id=?
                      AND b.capability='marketplace-economic.omie-transaction-evidence.reacquisition-v3'
                      AND b.source_order_ref=?
                      AND b.source_integration_ref=?
                      AND p.source_connection_id=?
                      AND p.source_capability='marketplace-economic.order-source'
                      AND p.outcome IN ('PROMOTED','DUPLICATE')
                      AND s.external_order_ref=i.external_order_id)"""
            ).use { statement ->
                statement.setObject(1, target.marketplaceOrderId)
                statement.setObject(2, target.organizationId.value)
                statement.setObject(3, target.omieConnectionId)
                statement.setString(4, target.sourceOrderReference)
                statement.setString(5, target.integrationReference)
                statement.setObject(6, target.mercadoLivreConnectionId)
                statement.executeQuery().use { rows -> rows.next() && rows.getBoolean(1) }
            }
        }
        override fun authenticate(token: String): AuthenticatedCommand? = runtimeDataSource.connection.use { authorization.authenticate(it, token) }
        override fun write(actor: AuthenticatedCommand, command: TransactionIdentityCommand): TransactionIdentityWriteResult = runtimeDataSource.connection.use { connection ->
            connection.autoCommit = false
            try {
                val result = writeRecord(connection, actor, command)
                if (result is TransactionIdentityWriteResult.Applied || result is TransactionIdentityWriteResult.AlreadyApplied) connection.commit() else connection.rollback()
                result
            } catch (failure: Throwable) { connection.rollback(); throw failure }
        }
    }
}

/** The only concrete delivery path; unavailable consoles fail closed. */
class SystemConsoleProtectedTty : ProtectedTty {
    private val console get() = System.console()
    override fun isProtected(): Boolean = console != null
    override fun deliverOnce(token: CharArray) {
        val active = requireNotNull(console) { "SECURE_TTY=UNAVAILABLE" }
        try { active.writer().println(String(token)); active.flush() } finally { token.fill('\u0000') }
    }
}

fun main(args: Array<String>) {
    require(args.contentEquals(arrayOf("execute-field-proof"))) { "Only execute-field-proof is supported" }
    require(System.console() != null) { "SECURE_TTY=UNAVAILABLE" }
    error("Human-approved manifest and explicit two-DataSource configuration are required; real execution remains disabled")
}
