package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicy
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicyContext
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicySelection
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicySource
import io.flooow.marketplace.operations.economics.reconciliation.FinancialReconciliationPolicyVersion
import java.sql.DriverManager
import java.sql.SQLException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

class PostgresFinancialReconciliationPolicySource(
    private val configuration: PostgresConfiguration
) : FinancialReconciliationPolicySource {

    override fun select(
        context: FinancialReconciliationPolicyContext
    ): FinancialReconciliationPolicySelection {
        return try {
            DriverManager.getConnection(
                configuration.url,
                configuration.user,
                configuration.password
            ).use { connection ->
                connection.prepareStatement(
                    SELECT_CURRENT_POLICY
                ).use { statement ->
                    statement.setObject(
                        1,
                        context.organizationId.value
                    )
                    statement.setString(
                        2,
                        context.marketplace.value
                    )
                    statement.setString(
                        3,
                        context.currency.code
                    )

                    statement.executeQuery().use { result ->
                        if (!result.next()) {
                            return FinancialReconciliationPolicySelection
                                .Unavailable
                        }

                        val version =
                            FinancialReconciliationPolicyVersion(
                                result.getString(
                                    "policy_version"
                                )
                            )

                        val tolerancesNode =
                            Json.parseToJsonElement(
                                result.getString(
                                    "stage_tolerances"
                                )
                            ).jsonObject

                        val expectedKeys =
                            FinancialLedgerStage.entries
                                .map {
                                    it.name
                                }
                                .toSet()

                        require(
                            tolerancesNode.keys ==
                                expectedKeys
                        ) {
                            "Persisted reconciliation policy stage set is invalid"
                        }

                        val tolerances =
                            FinancialLedgerStage.entries
                                .associateWith { stage ->
                                    val value =
                                        requireNotNull(
                                            tolerancesNode[
                                                stage.name
                                            ]
                                        ).jsonPrimitive

                                    require(
                                        value.isString
                                    ) {
                                        "Persisted reconciliation tolerance must be canonical text"
                                    }

                                    MarketplaceMoney.parse(
                                        context.currency,
                                        value.content
                                    )
                                }

                        FinancialReconciliationPolicySelection
                            .Selected(
                                FinancialReconciliationPolicy(
                                    version = version,
                                    currency =
                                        context.currency,
                                    tolerancesByStage =
                                        tolerances
                                )
                            )
                    }
                }
            }
        } catch (_: SQLException) {
            FinancialReconciliationPolicySelection
                .ReadFailure
        } catch (_: RuntimeException) {
            FinancialReconciliationPolicySelection
                .IntegrityFailure
        }
    }

    companion object {
        private const val SELECT_CURRENT_POLICY =
            """
            SELECT
                policy.policy_version,
                policy.stage_tolerances
              FROM marketplace_financial_reconciliation_policy_current current_policy
              JOIN marketplace_financial_reconciliation_policy policy
                ON policy.organization_id =
                    current_policy.organization_id
               AND policy.marketplace_key =
                    current_policy.marketplace_key
               AND policy.currency =
                    current_policy.currency
               AND policy.policy_version =
                    current_policy.policy_version
             WHERE current_policy.organization_id = ?
               AND current_policy.marketplace_key = ?
               AND current_policy.currency = ?
            """
    }
}
