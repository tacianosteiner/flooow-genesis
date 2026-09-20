package io.flooow.marketplace.persistence.postgres

import io.flooow.integration.control.IntegrationConnectionId
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderRevenuePromotionCandidate
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderRevenuePromotionOutcome
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderRevenuePromotionWriteResult
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderSourceKey
import io.flooow.marketplace.operations.economics.promotion.MarketplaceOrderSourcePromotionContract
import io.flooow.organization.OrganizationId
import java.math.BigDecimal
import java.sql.Connection
import java.sql.DriverManager
import java.sql.SQLException
import java.time.Instant
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.flywaydb.core.api.MigrationVersion
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresMarketplaceOrderRevenueLineageTest {
    @Test
    fun `V038 preserves legacy null and governs exact revenue lineage`() {
        val postgres = PostgreSQLContainer("postgres:18.4")
        postgres.start()

        try {
            val configuration =
                PostgresConfiguration(
                    postgres.jdbcUrl,
                    postgres.username,
                    postgres.password
                )

            /*
             * Phase 1:
             * migrate only through V037 so we can create a legitimate
             * historical V023 promotion that predates economic lineage.
             */
            Flyway.configure()
                .dataSource(
                    configuration.url,
                    configuration.user,
                    configuration.password
                )
                .locations("classpath:db/migration")
                .target(MigrationVersion.fromVersion("037"))
                .load()
                .migrate()

            val org = UUID(0, 8_001)
            val connection = UUID(0, 8_002)
            val order = UUID(0, 8_003)
            val legacyOrder = UUID(0, 8_004)

            seedOrganization(configuration, org)
            seedConnection(configuration, org, connection)

            /*
             * Exact source used by governed new writes after V038.
             */
            seedSource(
                configuration = configuration,
                organization = org,
                connection = connection,
                progressVersion = 1,
                ordinal = 0,
                externalOrder = "200000008001",
                currency = "BRL",
                amount = "123.450000",
                dateClosed = "2026-09-06 20:30:00.123456+00",
                observedAt = "2026-09-06 21:00:00.123456+00"
            )

            /*
             * Same durable provider semantics, separate source-key,
             * used to prove DUPLICATE can bind to the already retained fact.
             */
            seedSource(
                configuration = configuration,
                organization = org,
                connection = connection,
                progressVersion = 2,
                ordinal = 0,
                externalOrder = "200000008001",
                currency = "BRL",
                amount = "123.450000",
                dateClosed = "2026-09-06 20:30:00.123456+00",
                observedAt = "2026-09-06 21:00:00.123456+00"
            )

            /*
             * Mismatching economic amount used for trigger attack.
             */
            seedSource(
                configuration = configuration,
                organization = org,
                connection = connection,
                progressVersion = 3,
                ordinal = 0,
                externalOrder = "200000008001",
                currency = "BRL",
                amount = "999.000000",
                dateClosed = "2026-09-06 20:30:00.123456+00",
                observedAt = "2026-09-06 21:00:00.123456+00"
            )

            /*
             * Currency mismatch source used for IDENTITY_CONFLICT.
             */
            seedSource(
                configuration = configuration,
                organization = org,
                connection = connection,
                progressVersion = 4,
                ordinal = 0,
                externalOrder = "200000008001",
                currency = "USD",
                amount = "123.450000",
                dateClosed = "2026-09-06 20:30:00.123456+00",
                observedAt = "2026-09-06 21:00:00.123456+00"
            )

            /*
             * Fresh source key for proving the conflict-lineage rule itself.
             * It is never terminalized before the direct adversarial insert.
             */
            seedSource(
                configuration = configuration,
                organization = org,
                connection = connection,
                progressVersion = 5,
                ordinal = 0,
                externalOrder = "200000008001",
                currency = "USD",
                amount = "123.450000",
                dateClosed = "2026-09-06 20:30:00.123456+00",
                observedAt = "2026-09-06 21:00:00.123456+00"
            )

            /*
             * Fresh valid source for attempting to bind a real fact belonging
             * to another marketplace order.
             */
            seedSource(
                configuration = configuration,
                organization = org,
                connection = connection,
                progressVersion = 6,
                ordinal = 0,
                externalOrder = "200000008001",
                currency = "BRL",
                amount = "123.450000",
                dateClosed = "2026-09-06 20:30:00.123456+00",
                observedAt = "2026-09-06 21:00:00.123456+00"
            )

            val otherOrder = UUID(0, 8_005)

            seedSource(
                configuration = configuration,
                organization = org,
                connection = connection,
                progressVersion = 7,
                ordinal = 0,
                externalOrder = "200000008005",
                currency = "BRL",
                amount = "77.000000",
                dateClosed = "2026-09-06 20:31:00.123456+00",
                observedAt = "2026-09-06 21:01:00.123456+00"
            )

            /*
             * Historical source and identity: terminalized before V038.
             */
            seedSource(
                configuration = configuration,
                organization = org,
                connection = connection,
                progressVersion = 90,
                ordinal = 0,
                externalOrder = "200000008090",
                currency = "BRL",
                amount = "50.000000",
                dateClosed = "2026-09-06 19:00:00.000001+00",
                observedAt = "2026-09-06 19:30:00.000001+00"
            )

            seedIdentity(
                configuration,
                org,
                connection,
                order,
                "200000008001",
                "BRL",
                1
            )

            seedIdentity(
                configuration,
                org,
                connection,
                legacyOrder,
                "200000008090",
                "BRL",
                90
            )

            seedIdentity(
                configuration,
                org,
                connection,
                otherOrder,
                "200000008005",
                "BRL",
                7
            )

            execute(
                configuration,
                """
                INSERT INTO marketplace_order_revenue_source_promotion (
                    organization_id,
                    source_connection_id,
                    source_capability,
                    source_input_progress_version,
                    source_record_ordinal,
                    marketplace_order_id,
                    outcome,
                    promoted_at
                ) VALUES (
                    '$org',
                    '$connection',
                    'marketplace-economic.order-source',
                    90,
                    0,
                    '$legacyOrder',
                    'PROMOTED',
                    '2026-09-06 19:31:00.000001+00'
                )
                """.trimIndent()
            )

            /*
             * Phase 2: now apply V038.
             */
            Flyway.configure()
                .dataSource(
                    configuration.url,
                    configuration.user,
                    configuration.password
                )
                .locations("classpath:db/migration")
                .load()
                .migrate()

            assertEquals(
                "038",
                scalar(
                    configuration,
                    "SELECT version FROM flyway_schema_history " +
                        "WHERE version='038' AND success"
                )
            )

            /*
             * Critical compatibility invariant:
             * old legitimate row remains present and NULL.
             * No inferred lineage/backfill.
             */
            assertEquals(
                "1",
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_input_progress_version=90
                      AND economic_observation_id IS NULL
                    """.trimIndent()
                )
            )

            /*
             * Durable retained evidence fact for the real source semantics.
             */
            val retainedFact = UUID(0, 8_101)
            val component = UUID(0, 8_102)
            seedExactRevenueEvidence(
                configuration = configuration,
                organization = org,
                order = order,
                fact = retainedFact,
                component = component,
                externalOrder = "200000008001",
                amount = "123.450000",
                currency = "BRL",
                occurredAt = "2026-09-06 20:30:00.123456+00",
                observedAt = "2026-09-06 21:00:00.123456+00"
            )

            val otherFact = UUID(0, 8_105)
            seedExactRevenueEvidence(
                configuration = configuration,
                organization = org,
                order = otherOrder,
                fact = otherFact,
                component = UUID(0, 8_106),
                externalOrder = "200000008005",
                amount = "77.000000",
                currency = "BRL",
                occurredAt = "2026-09-06 20:31:00.123456+00",
                observedAt = "2026-09-06 21:01:00.123456+00"
            )

            val repository =
                PostgresMarketplaceOrderSourcePromotionRepository(configuration)

            val normal =
                revenueCandidate(
                    organization = org,
                    connection = connection,
                    order = order,
                    progressVersion = 1,
                    currency = "BRL",
                    identityCurrency = "BRL",
                    amount = "123.450000"
                )

            val duplicate =
                revenueCandidate(
                    organization = org,
                    connection = connection,
                    order = order,
                    progressVersion = 2,
                    currency = "BRL",
                    identityCurrency = "BRL",
                    amount = "123.450000"
                )

            val amountMismatch =
                revenueCandidate(
                    organization = org,
                    connection = connection,
                    order = order,
                    progressVersion = 3,
                    currency = "BRL",
                    identityCurrency = "BRL",
                    amount = "999.000000"
                )

            val identityConflict =
                revenueCandidate(
                    organization = org,
                    connection = connection,
                    order = order,
                    progressVersion = 4,
                    currency = "USD",
                    identityCurrency = "BRL",
                    amount = "123.450000"
                )

            val wrongOrderFact =
                revenueCandidate(
                    organization = org,
                    connection = connection,
                    order = order,
                    progressVersion = 6,
                    currency = "BRL",
                    identityCurrency = "BRL",
                    amount = "123.450000"
                )

            val retainedId =
                MarketplaceEconomicEvidenceObservationId.parse(
                    retainedFact.toString()
                )

            val promotedAt =
                Instant.parse("2026-09-06T22:30:00.000001Z")

            /*
             * PROMOTED -> exact durable fact.
             */
            assertEquals(
                MarketplaceOrderRevenuePromotionWriteResult.APPLIED,
                repository.markRevenueTerminal(
                    normal,
                    MarketplaceOrderRevenuePromotionOutcome.PROMOTED,
                    retainedId,
                    promotedAt
                )
            )

            assertEquals(
                retainedFact.toString(),
                scalar(
                    configuration,
                    """
                    SELECT economic_observation_id::text
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_input_progress_version=1
                    """.trimIndent()
                )
            )

            /*
             * Exact replay -> ALREADY_APPLIED.
             */
            assertEquals(
                MarketplaceOrderRevenuePromotionWriteResult.ALREADY_APPLIED,
                repository.markRevenueTerminal(
                    normal,
                    MarketplaceOrderRevenuePromotionOutcome.PROMOTED,
                    retainedId,
                    promotedAt.plusSeconds(1)
                )
            )

            /*
             * Same terminal source/outcome but a different lineage identity:
             * replay classification must occur before the V038 trigger.
             */
            val differentId =
                MarketplaceEconomicEvidenceObservationId.parse(
                    UUID(0, 8_199).toString()
                )

            assertEquals(
                MarketplaceOrderRevenuePromotionWriteResult.CONFLICT,
                repository.markRevenueTerminal(
                    normal,
                    MarketplaceOrderRevenuePromotionOutcome.PROMOTED,
                    differentId,
                    promotedAt.plusSeconds(2)
                )
            )

            assertEquals(
                order.toString(),
                scalar(
                    configuration,
                    """
                    SELECT marketplace_order_id::text
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_connection_id='$connection'
                      AND source_capability='marketplace-economic.order-source'
                      AND source_input_progress_version=1
                      AND source_record_ordinal=0
                    """.trimIndent()
                )
            )
            assertEquals(
                "PROMOTED",
                scalar(
                    configuration,
                    """
                    SELECT outcome
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_connection_id='$connection'
                      AND source_capability='marketplace-economic.order-source'
                      AND source_input_progress_version=1
                      AND source_record_ordinal=0
                    """.trimIndent()
                )
            )
            assertEquals(
                retainedFact.toString(),
                scalar(
                    configuration,
                    """
                    SELECT economic_observation_id::text
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_connection_id='$connection'
                      AND source_capability='marketplace-economic.order-source'
                      AND source_input_progress_version=1
                      AND source_record_ordinal=0
                    """.trimIndent()
                )
            )
            assertEquals(
                "1",
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_connection_id='$connection'
                      AND source_capability='marketplace-economic.order-source'
                      AND source_input_progress_version=1
                      AND source_record_ordinal=0
                    """.trimIndent()
                )
            )

            /*
             * DUPLICATE -> exact retained fact, not a generated candidate id.
             */
            assertEquals(
                MarketplaceOrderRevenuePromotionWriteResult.APPLIED,
                repository.markRevenueTerminal(
                    duplicate,
                    MarketplaceOrderRevenuePromotionOutcome.DUPLICATE,
                    retainedId,
                    promotedAt.plusSeconds(3)
                )
            )

            assertEquals(
                retainedFact.toString(),
                scalar(
                    configuration,
                    """
                    SELECT economic_observation_id::text
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_input_progress_version=2
                    """.trimIndent()
                )
            )

            /*
             * New successful terminal without lineage is rejected.
             * Repository fails closed instead of fabricating identity.
             */
            assertEquals(
                MarketplaceOrderRevenuePromotionWriteResult.UNAVAILABLE,
                repository.markRevenueTerminal(
                    amountMismatch,
                    MarketplaceOrderRevenuePromotionOutcome.PROMOTED,
                    null,
                    promotedAt.plusSeconds(4)
                )
            )

            assertEquals(
                "0",
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_input_progress_version=3
                    """.trimIndent()
                )
            )

            /*
             * Exact UUID exists, but its economic semantics do not match
             * source amount 999. Trigger must reject.
             */
            assertEquals(
                MarketplaceOrderRevenuePromotionWriteResult.UNAVAILABLE,
                repository.markRevenueTerminal(
                    amountMismatch,
                    MarketplaceOrderRevenuePromotionOutcome.PROMOTED,
                    retainedId,
                    promotedAt.plusSeconds(5)
                )
            )

            assertEquals(
                "0",
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_input_progress_version=3
                    """.trimIndent()
                )
            )

            /*
             * Conflict terminal is the opposite: it MUST NOT claim lineage.
             */
            assertEquals(
                MarketplaceOrderRevenuePromotionWriteResult.APPLIED,
                repository.markRevenueTerminal(
                    identityConflict,
                    MarketplaceOrderRevenuePromotionOutcome.IDENTITY_CONFLICT,
                    null,
                    promotedAt.plusSeconds(6)
                )
            )

            assertEquals(
                "1",
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_input_progress_version=4
                      AND outcome='IDENTITY_CONFLICT'
                      AND economic_observation_id IS NULL
                    """.trimIndent()
                )
            )

            /*
             * A fresh conflict source with a real lineage fact must fail at
             * V038's lineage rule, not at the source terminal primary key.
             */
            val conflictLineageError = assertFailsWith<SQLException> {
                execute(
                    configuration,
                    """
                    INSERT INTO marketplace_order_revenue_source_promotion (
                        organization_id,
                        source_connection_id,
                        source_capability,
                        source_input_progress_version,
                        source_record_ordinal,
                        marketplace_order_id,
                        outcome,
                        economic_observation_id,
                        promoted_at
                    ) VALUES (
                        '$org',
                        '$connection',
                        'marketplace-economic.order-source',
                        5,
                        0,
                        '$order',
                        'IDENTITY_CONFLICT',
                        '$retainedFact',
                        '2026-09-06 22:40:00.000001+00'
                    )
                    """.trimIndent()
                )
            }
            assertTrue(
                conflictLineageError.message.orEmpty().contains(
                    "conflict revenue promotion must not claim economic observation lineage"
                )
            )

            assertEquals(
                MarketplaceOrderRevenuePromotionWriteResult.UNAVAILABLE,
                repository.markRevenueTerminal(
                    wrongOrderFact,
                    MarketplaceOrderRevenuePromotionOutcome.PROMOTED,
                    MarketplaceEconomicEvidenceObservationId.parse(otherFact.toString()),
                    promotedAt.plusSeconds(7)
                )
            )
            assertEquals(
                "0",
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND source_connection_id='$connection'
                      AND source_capability='marketplace-economic.order-source'
                      AND source_input_progress_version=6
                      AND source_record_ordinal=0
                    """.trimIndent()
                )
            )

            /*
             * FK organization/order binding is exact.
             */
            val unrelatedFact = UUID(0, 8_888)

            assertFailsWith<SQLException> {
                execute(
                    configuration,
                    """
                    INSERT INTO marketplace_order_revenue_source_promotion (
                        organization_id,
                        source_connection_id,
                        source_capability,
                        source_input_progress_version,
                        source_record_ordinal,
                        marketplace_order_id,
                        outcome,
                        economic_observation_id,
                        promoted_at
                    ) VALUES (
                        '$org',
                        '$connection',
                        'marketplace-economic.order-source',
                        3,
                        0,
                        '$order',
                        'PROMOTED',
                        '$unrelatedFact',
                        '2026-09-06 22:41:00.000001+00'
                    )
                    """.trimIndent()
                )
            }

            /*
             * Append-only guarantee remains active after V038.
             */
            assertFailsWith<SQLException> {
                execute(
                    configuration,
                    """
                    UPDATE marketplace_order_revenue_source_promotion
                    SET economic_observation_id = NULL
                    WHERE organization_id='$org'
                      AND source_input_progress_version=1
                    """.trimIndent()
                )
            }

            assertTrue(
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$org'
                      AND economic_observation_id='$retainedFact'
                    """.trimIndent()
                ).toInt() >= 2
            )
        } finally {
            postgres.stop()
        }
    }

    private fun seedOrganization(
        configuration: PostgresConfiguration,
        organization: UUID
    ) {
        execute(
            configuration,
            """
            INSERT INTO integration_organization (
                organization_id,
                status,
                created_at,
                updated_at
            ) VALUES (
                '$organization',
                'ACTIVE',
                '2026-09-06 18:00:00+00',
                '2026-09-06 18:00:00+00'
            )
            """.trimIndent()
        )
    }

    private fun seedConnection(
        configuration: PostgresConfiguration,
        organization: UUID,
        connection: UUID
    ) {
        execute(
            configuration,
            """
            INSERT INTO integration_connection (
                organization_id,
                connection_id,
                provider_key,
                credential_kind,
                status,
                binding_version,
                created_at,
                updated_at
            ) VALUES (
                '$organization',
                '$connection',
                'br.com.mercadolivre',
                'OAUTH2_AUTHORIZATION_CODE',
                'ACTIVE',
                1,
                '2026-09-06 18:00:00+00',
                '2026-09-06 18:00:00+00'
            )
            """.trimIndent()
        )

        execute(
            configuration,
            """
            INSERT INTO integration_connector_progress (
                organization_id,
                connection_id,
                capability,
                progress_version,
                progress_envelope,
                exhausted,
                last_observed_at,
                updated_at
            ) VALUES (
                '$organization',
                '$connection',
                'marketplace-economic.order-source',
                90,
                decode('01','hex'),
                false,
                '2026-09-06 23:00:00+00',
                '2026-09-06 23:00:00+00'
            )
            """.trimIndent()
        )
    }
    private fun seedSource(
        configuration: PostgresConfiguration,
        organization: UUID,
        connection: UUID,
        progressVersion: Long,
        ordinal: Int,
        externalOrder: String,
        currency: String,
        amount: String,
        dateClosed: String,
        observedAt: String
    ) {
        val pageKey =
            progressVersion
                .toString(16)
                .padStart(2, '0')
                .takeLast(2)
                .repeat(32)

        execute(
            configuration,
            """
            INSERT INTO integration_connector_page_commit (
                organization_id,
                connection_id,
                capability,
                input_progress_version,
                page_commit_key,
                record_count,
                exhausted,
                observed_at,
                committed_at
            ) VALUES (
                '$organization',
                '$connection',
                'marketplace-economic.order-source',
                $progressVersion,
                decode('$pageKey','hex'),
                1,
                false,
                '$observedAt',
                '$observedAt'
            )
            """.trimIndent()
        )

        execute(
            configuration,
            """
            INSERT INTO integration_mercado_livre_order_source_observation (
                organization_id,
                connection_id,
                capability,
                input_progress_version,
                record_ordinal,
                external_order_ref,
                provider_status,
                date_created,
                date_last_updated,
                date_closed,
                currency,
                total_amount,
                paid_amount,
                pack_ref,
                shipping_ref,
                observed_at
            ) VALUES (
                '$organization',
                '$connection',
                'marketplace-economic.order-source',
                $progressVersion,
                $ordinal,
                '$externalOrder',
                'paid',
                '2026-09-06 18:30:00.000001+00',
                '$observedAt',
                '$dateClosed',
                '$currency',
                $amount,
                $amount,
                NULL,
                NULL,
                '$observedAt'
            )
            """.trimIndent()
        )
    }

    private fun seedIdentity(
        configuration: PostgresConfiguration,
        organization: UUID,
        connection: UUID,
        order: UUID,
        externalOrder: String,
        currency: String,
        firstProgressVersion: Long
    ) {
        execute(
            configuration,
            """
            INSERT INTO marketplace_order_identity_registry (
                organization_id,
                marketplace_key,
                external_order_id,
                marketplace_order_id,
                currency,
                allocated_at,
                first_source_connection_id,
                first_source_capability,
                first_source_input_progress_version,
                first_source_record_ordinal
            ) VALUES (
                '$organization',
                'mercado-livre',
                '$externalOrder',
                '$order',
                '$currency',
                '2026-09-06 18:45:00.000001+00',
                '$connection',
                'marketplace-economic.order-source',
                $firstProgressVersion,
                0
            )
            """.trimIndent()
        )
    }

    private fun seedExactRevenueEvidence(
        configuration: PostgresConfiguration,
        organization: UUID,
        order: UUID,
        fact: UUID,
        component: UUID,
        externalOrder: String,
        amount: String,
        currency: String,
        occurredAt: String,
        observedAt: String
    ) {
        connection(configuration).use { sql ->
            sql.autoCommit = false

            try {
                fun executeInTransaction(statementSql: String) {
                    sql.createStatement().use { statement ->
                        statement.executeUpdate(statementSql)
                    }
                }

                executeInTransaction(
                    """
                    INSERT INTO marketplace_economic_evidence_subject (
                        organization_id,
                        marketplace_order_id,
                        marketplace_key,
                        external_order_id,
                        currency,
                        current_version
                    ) VALUES (
                        '$organization',
                        '$order',
                        'mercado-livre',
                        '$externalOrder',
                        '$currency',
                        0
                    )
                    """.trimIndent()
                )

                /*
                 * V015's evidence graph is commit-consistent:
                 * update -> identifier -> fact -> subtype are validated
                 * by DEFERRABLE INITIALLY DEFERRED constraint triggers.
                 * They must therefore be committed atomically.
                 */

                executeInTransaction(
                    """
                    INSERT INTO marketplace_economic_evidence_update (
                        organization_id,
                        marketplace_order_id,
                        evidence_version,
                        update_id,
                        change_kind
                    ) VALUES (
                        '$organization',
                        '$order',
                        1,
                        '$fact',
                        'FACT'
                    )
                    """.trimIndent()
                )

                executeInTransaction(
                    """
                    INSERT INTO marketplace_economic_evidence_identifier (
                        organization_id,
                        marketplace_order_id,
                        observation_id,
                        evidence_version,
                        identifier_kind
                    ) VALUES (
                        '$organization',
                        '$order',
                        '$fact',
                        1,
                        'FACT'
                    )
                    """.trimIndent()
                )

                executeInTransaction(
                    """
                    INSERT INTO marketplace_economic_evidence_fact (
                        organization_id,
                        marketplace_order_id,
                        fact_id,
                        evidence_version,
                        identifier_kind,
                        fact_kind,
                        family,
                        observed_at
                    ) VALUES (
                        '$organization',
                        '$order',
                        '$fact',
                        1,
                        'FACT',
                        'COMPONENT',
                        'MARKETPLACE_ORDER',
                        '$observedAt'
                    )
                    """.trimIndent()
                )

                executeInTransaction(
                    """
                    INSERT INTO marketplace_economic_evidence_component_fact (
                        organization_id,
                        marketplace_order_id,
                        fact_id,
                        evidence_version,
                        fact_kind,
                        family,
                        component_id,
                        component_type,
                        direction,
                        magnitude,
                        currency,
                        source_kind,
                        source_system_key,
                        source_external_reference,
                        source_external_reference_absence_reason,
                        occurred_at,
                        quality,
                        coverage
                    ) VALUES (
                        '$organization',
                        '$order',
                        '$fact',
                        1,
                        'COMPONENT',
                        'MARKETPLACE_ORDER',
                        '$component',
                        'REVENUE',
                        'ADDITION',
                        $amount,
                        '$currency',
                        'MARKETPLACE',
                        'br.com.mercadolivre',
                        '$externalOrder',
                        NULL,
                        '$occurredAt',
                        'CONFIRMED',
                        'PARTIAL'
                    )
                    """.trimIndent()
                )

                /*
                 * Root may advance only after journal version 1 exists.
                 * Deferred validation sees the complete graph at commit.
                 */
                executeInTransaction(
                    """
                    UPDATE marketplace_economic_evidence_subject
                    SET current_version = 1
                    WHERE organization_id = '$organization'
                      AND marketplace_order_id = '$order'
                    """.trimIndent()
                )

                sql.commit()
            } catch (error: Exception) {
                sql.rollback()
                throw error
            }
        }
    }
    private fun revenueCandidate(
        organization: UUID,
        connection: UUID,
        order: UUID,
        progressVersion: Long,
        currency: String,
        identityCurrency: String,
        amount: String
    ): MarketplaceOrderRevenuePromotionCandidate =
        MarketplaceOrderRevenuePromotionCandidate(
            sourceKey =
                MarketplaceOrderSourceKey(
                    organizationId = OrganizationId(organization),
                    connectionId = IntegrationConnectionId(connection),
                    capability = MarketplaceOrderSourcePromotionContract.CAPABILITY,
                    inputProgressVersion = progressVersion,
                    recordOrdinal = 0
                ),
            externalOrderId = MarketplaceExternalOrderId("200000008001"),
            sourceCurrency = MarketplaceCurrency(currency),
            identityCurrency = MarketplaceCurrency(identityCurrency),
            orderId = MarketplaceOrderId(order),
            totalAmount = BigDecimal(amount),
            dateClosed = Instant.parse("2026-09-06T20:30:00.123456Z"),
            observedAt = Instant.parse("2026-09-06T21:00:00.123456Z")
        )

    private fun execute(
        configuration: PostgresConfiguration,
        sql: String
    ) {
        connection(configuration).use { connection ->
            connection.createStatement().use { statement ->
                statement.executeUpdate(sql)
            }
        }
    }

    private fun scalar(
        configuration: PostgresConfiguration,
        sql: String
    ): String =
        connection(configuration).use { connection ->
            connection.createStatement().use { statement ->
                statement.executeQuery(sql).use { result ->
                    check(result.next())
                    result.getString(1)
                }
            }
        }

    private fun connection(
        configuration: PostgresConfiguration
    ): Connection =
        DriverManager.getConnection(
            configuration.url,
            configuration.user,
            configuration.password
        )
}
