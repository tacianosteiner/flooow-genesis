package io.flooow.ceremony

import java.sql.Connection

/** Frozen repository migrations; Flyway uses its default public history table and SQL CRC32. */
internal object PostgresOfflineMigrationHistory {
    fun provesV042(connection: Connection): Boolean = runCatching {
        val seen = mutableSetOf<Int>()
        var previousVersion = 0
        connection.createStatement().use { statement ->
            statement.executeQuery("SELECT version,type,script,checksum,success FROM public.flyway_schema_history ORDER BY installed_rank").use { rows ->
                while (rows.next()) {
                    val version = rows.getString(1)?.toIntOrNull() ?: return false
                    val expected = migrations[version] ?: return false
                    if (!seen.add(version) || version <= previousVersion || rows.getString(2) != "SQL" ||
                        rows.getString(3) != expected.first || rows.getInt(4) != expected.second || rows.wasNull() ||
                        !rows.getBoolean(5)) return false
                    previousVersion = version
                }
            }
        }
        seen == migrations.keys
    }.getOrDefault(false)

    private val migrations = mapOf(
        1 to ("V001__create_inventory_risk_assessment_journal.sql" to -1586741974),
        2 to ("V002__create_integration_event_outbox.sql" to 126115083),
        3 to ("V003__create_integration_event_delivery.sql" to -1080502606),
        4 to ("V004__create_integration_control_plane.sql" to -88250422),
        5 to ("V005__propagate_organization_context.sql" to -295115246),
        6 to ("V006__create_inventory_source_ledger.sql" to -160916869),
        7 to ("V007__create_inventory_identity_mapping.sql" to 1400283408),
        8 to ("V008__create_canonical_inventory_observation.sql" to -1830861528),
        9 to ("V009__allow_mapping_across_matching_inventory_evidence.sql" to -168542165),
        10 to ("V010__create_canonical_inventory_source_acceptance.sql" to -267556503),
        11 to ("V011__create_canonical_inventory_measure_selection.sql" to 998362485),
        12 to ("V012__create_canonical_inventory_candidate_snapshot.sql" to 711492973),
        13 to ("V013__create_canonical_inventory_candidate_adjudication.sql" to -59414358),
        14 to ("V014__create_marketplace_financial_ledger.sql" to 520974744),
        15 to ("V015__create_independent_marketplace_economic_evidence.sql" to 1556483168),
        16 to ("V016__create_marketplace_economic_evidence_projection_checkpoint.sql" to 1462337216),
        17 to ("V017__add_order_occurrence_to_independent_marketplace_economic_evidence.sql" to 1173709995),
        18 to ("V018__create_marketplace_sales_intelligence_projection.sql" to 309518371),
        19 to ("V019__create_omie_product_cost_source_observation.sql" to -792333816),
        20 to ("V020__create_credential_rotation_execution.sql" to -1694687584),
        21 to ("V021__create_mercado_livre_order_source_observation.sql" to 993334571),
        22 to ("V022__create_marketplace_order_identity_and_occurrence_promotion.sql" to -954032763),
        23 to ("V023__create_marketplace_order_revenue_source_promotion.sql" to 1426238664),
        24 to ("V024__create_marketplace_reconciliation_case.sql" to -537037466),
        25 to ("V025__create_marketplace_systemic_divergence_signal.sql" to -178315441),
        26 to ("V026__create_omie_transaction_evidence.sql" to 1375235353),
        27 to ("V027__add_mercado_livre_seller_sku_evidence.sql" to -1453432903),
        28 to ("V028__allow_governed_reacquisition_capabilities.sql" to -414040372),
        29 to ("V029__create_cross_system_product_identity_decision.sql" to -712778487),
        30 to ("V030__create_reconciliation_case_revision_assessment_lineage.sql" to -810899834),
        31 to ("V031__create_financial_reconciliation_policy_authority.sql" to 673194505),
        32 to ("V032__create_financial_ledger_materialization_lineage.sql" to 1965235234),
        33 to ("V033__create_omie_transaction_evidence_v3_source_evidence.sql" to -445138512),
        34 to ("V034__create_command_authorization.sql" to -1770184515),
        35 to ("V035__create_explicit_transaction_identity.sql" to 1551560369),
        36 to ("V036__add_transaction_identity_withdrawal.sql" to -1440468462),
        37 to ("V037__add_controlled_command_authority_provisioning.sql" to -973168858),
        38 to ("V038__add_revenue_promotion_economic_observation_lineage.sql" to -1432966794),
        39 to ("V039__restrict_transaction_identity_runtime_privileges.sql" to 677069546),
        40 to ("V040__create_s2a_approval_governance.sql" to 1009186060),
        41 to ("V041__create_s2a_accepted_attestation.sql" to 2058571507),
        42 to ("V042__create_s2a_attestation_consumption_and_attested_command_authority.sql" to -1293350141),
    )
}
