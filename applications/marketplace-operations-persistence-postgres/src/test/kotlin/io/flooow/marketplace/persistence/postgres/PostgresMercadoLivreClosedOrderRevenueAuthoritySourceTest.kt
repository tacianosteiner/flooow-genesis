package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.EconomicComponent
import io.flooow.marketplace.operations.economics.EconomicComponentCoverage
import io.flooow.marketplace.operations.economics.EconomicComponentId
import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicEvidenceQuality
import io.flooow.marketplace.operations.economics.EconomicExternalReference
import io.flooow.marketplace.operations.economics.EconomicExternalReferenceState
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.EconomicSourceKind
import io.flooow.marketplace.operations.economics.EconomicSourceSystemKey
import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceExternalOrderId
import io.flooow.marketplace.operations.economics.MarketplaceKey
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceFamily
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.ledger.materialization.MercadoLivreClosedOrderRevenueAuthoritySourceResult
import io.flooow.marketplace.operations.economics.ledger.materialization.MercadoLivreClosedOrderRevenuePromotionOutcome
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.time.Instant
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.flywaydb.core.api.MigrationVersion
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresMercadoLivreClosedOrderRevenueAuthoritySourceTest {
    @Test
    fun `resolves exact durable lineage and fails closed on ambiguity conflicts tenants and legacy null`() {
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
             * Historical compatibility proof:
             * create one legitimate V023 success before V038.
             */
            migrate(configuration, "037")

            val organization = UUID(0, 91_001)
            val otherOrganization = UUID(0, 91_002)
            val connection = UUID(0, 91_010)
            val otherConnection = UUID(0, 91_011)

            val legacyOrder = UUID(0, 91_100)
            val promotedOrder = UUID(0, 91_101)
            val duplicateOrder = UUID(0, 91_102)
            val conflictOrder = UUID(0, 91_103)

            seedOrganization(configuration, organization)
            seedOrganization(configuration, otherOrganization)
            seedConnection(configuration, organization, connection)
            seedConnection(configuration, otherOrganization, otherConnection)

            seedSource(
                configuration,
                organization,
                connection,
                90,
                "290000009090",
                "BRL",
                "50.000000",
                "2026-09-20 18:00:00.000001+00",
                "2026-09-20 18:30:00.000001+00"
            )

            seedIdentity(
                configuration,
                organization,
                connection,
                legacyOrder,
                "290000009090",
                "BRL",
                90
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
                    '$organization',
                    '$connection',
                    'marketplace-economic.order-source',
                    90,
                    0,
                    '$legacyOrder',
                    'PROMOTED',
                    '2026-09-20 18:31:00.000001+00'
                )
                """.trimIndent()
            )

            migrate(configuration)

            assertEquals(
                "1",
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$organization'
                      AND marketplace_order_id='$legacyOrder'
                      AND outcome='PROMOTED'
                      AND economic_observation_id IS NULL
                    """.trimIndent()
                )
            )

            val source =
                PostgresMercadoLivreClosedOrderRevenueAuthoritySource(configuration)

            val arbitraryLegacyObservation =
                MarketplaceEconomicEvidenceObservationId.parse(
                    UUID(0, 91_199).toString()
                )

            assertEquals(
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound,
                source.findProofs(
                    OrganizationId(organization),
                    arbitraryLegacyObservation,
                    MarketplaceOrderId(legacyOrder)
                )
            )

            /*
             * ----------------------------------------------------
             * PROMOTED exact lineage.
             * ----------------------------------------------------
             */
            seedSource(
                configuration,
                organization,
                connection,
                1,
                "290000009101",
                "BRL",
                "123.450000",
                "2026-09-20 19:00:00.123456+00",
                "2026-09-20 19:30:00.123456+00"
            )

            seedIdentity(
                configuration,
                organization,
                connection,
                promotedOrder,
                "290000009101",
                "BRL",
                1
            )

            val promotedFact = UUID(0, 91_201)
            val promotedComponent = UUID(0, 91_202)

            seedExactRevenueEvidence(
                configuration,
                organization,
                promotedOrder,
                promotedFact,
                promotedComponent,
                "290000009101",
                "123.450000",
                "BRL",
                "2026-09-20 19:00:00.123456+00",
                "2026-09-20 19:30:00.123456+00"
            )

            insertSuccessfulTerminal(
                configuration,
                organization,
                connection,
                progressVersion = 1,
                order = promotedOrder,
                outcome = "PROMOTED",
                observation = promotedFact
            )

            val promotedId =
                MarketplaceEconomicEvidenceObservationId.parse(
                    promotedFact.toString()
                )

            val expectedPromotedObservation =
                observation(
                    organization = organization,
                    order = promotedOrder,
                    fact = promotedFact,
                    component = promotedComponent,
                    externalOrder = "290000009101",
                    amount = "123.45",
                    currency = "BRL",
                    occurredAt = Instant.parse("2026-09-20T19:00:00.123456Z"),
                    observedAt = Instant.parse("2026-09-20T19:30:00.123456Z")
                )

            val beforePromoted = snapshot(configuration)

            val promotedResult =
                assertIs<MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found>(
                    source.findProofs(
                        OrganizationId(organization),
                        promotedId,
                        MarketplaceOrderId(promotedOrder)
                    )
                )

            assertEquals(1, promotedResult.proofs.size)

            val promotedProof = promotedResult.proofs.single()

            assertEquals(
                expectedPromotedObservation,
                promotedProof.durableObservation
            )
            assertEquals(OrganizationId(organization), promotedProof.organizationId)
            assertEquals(MarketplaceOrderId(promotedOrder), promotedProof.marketplaceOrderId)
            assertEquals(MarketplaceKey("mercado-livre"), promotedProof.identityMarketplace)
            assertEquals(
                MarketplaceExternalOrderId("290000009101"),
                promotedProof.identityExternalOrderId
            )
            assertEquals(MarketplaceCurrency("BRL"), promotedProof.identityCurrency)
            assertEquals(
                "marketplace-economic.order-source",
                promotedProof.sourceCapability
            )
            assertEquals(
                MarketplaceExternalOrderId("290000009101"),
                promotedProof.sourceExternalOrderId
            )
            assertEquals(MarketplaceCurrency("BRL"), promotedProof.sourceCurrency)
            assertEquals(
                MarketplaceMoney.parse(MarketplaceCurrency("BRL"), "123.45"),
                promotedProof.sourceTotalAmount
            )
            assertEquals(
                Instant.parse("2026-09-20T19:00:00.123456Z"),
                promotedProof.sourceDateClosed
            )
            assertEquals(
                Instant.parse("2026-09-20T19:30:00.123456Z"),
                promotedProof.sourceObservedAt
            )
            assertEquals(
                MercadoLivreClosedOrderRevenuePromotionOutcome.PROMOTED,
                promotedProof.outcome
            )

            val promotedReplay =
                source.findProofs(
                    OrganizationId(organization),
                    promotedId,
                    MarketplaceOrderId(promotedOrder)
                )

            assertEquals(promotedResult, promotedReplay)
            assertEquals(beforePromoted, snapshot(configuration))

            /*
             * Wrong identity coordinates must never resolve.
             */
            assertEquals(
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound,
                source.findProofs(
                    OrganizationId(otherOrganization),
                    promotedId,
                    MarketplaceOrderId(promotedOrder)
                )
            )

            assertEquals(
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound,
                source.findProofs(
                    OrganizationId(organization),
                    promotedId,
                    MarketplaceOrderId(UUID(0, 91_999))
                )
            )

            assertEquals(
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound,
                source.findProofs(
                    OrganizationId(organization),
                    MarketplaceEconomicEvidenceObservationId.parse(
                        UUID(0, 91_998).toString()
                    ),
                    MarketplaceOrderId(promotedOrder)
                )
            )

            /*
             * ----------------------------------------------------
             * DUPLICATE retained canonical lineage.
             * ----------------------------------------------------
             */
            seedSource(
                configuration,
                organization,
                connection,
                2,
                "290000009102",
                "BRL",
                "77.770000",
                "2026-09-20 20:00:00.111111+00",
                "2026-09-20 20:30:00.222222+00"
            )

            seedIdentity(
                configuration,
                organization,
                connection,
                duplicateOrder,
                "290000009102",
                "BRL",
                2
            )

            val retainedFact = UUID(0, 91_301)
            val retainedComponent = UUID(0, 91_302)

            seedExactRevenueEvidence(
                configuration,
                organization,
                duplicateOrder,
                retainedFact,
                retainedComponent,
                "290000009102",
                "77.770000",
                "BRL",
                "2026-09-20 20:00:00.111111+00",
                "2026-09-20 20:30:00.222222+00"
            )

            insertSuccessfulTerminal(
                configuration,
                organization,
                connection,
                progressVersion = 2,
                order = duplicateOrder,
                outcome = "DUPLICATE",
                observation = retainedFact
            )

            val retainedId =
                MarketplaceEconomicEvidenceObservationId.parse(
                    retainedFact.toString()
                )

            val duplicateResult =
                assertIs<MercadoLivreClosedOrderRevenueAuthoritySourceResult.Found>(
                    source.findProofs(
                        OrganizationId(organization),
                        retainedId,
                        MarketplaceOrderId(duplicateOrder)
                    )
                )

            assertEquals(1, duplicateResult.proofs.size)
            assertEquals(
                retainedId,
                duplicateResult.proofs.single().durableObservation.id
            )
            assertEquals(
                MercadoLivreClosedOrderRevenuePromotionOutcome.DUPLICATE,
                duplicateResult.proofs.single().outcome
            )

            /*
             * ----------------------------------------------------
             * LEGAL MULTI-SOURCE AMBIGUITY.
             *
             * Second durable source coordinate points to the same:
             * organization + order + retained canonical observation.
             *
             * This state is accepted by current V038 invariants.
             * D3A must therefore fail closed.
             * ----------------------------------------------------
             */
            seedSource(
                configuration,
                organization,
                connection,
                3,
                "290000009102",
                "BRL",
                "77.770000",
                "2026-09-20 20:00:00.111111+00",
                "2026-09-20 20:30:00.222222+00"
            )

            insertSuccessfulTerminal(
                configuration,
                organization,
                connection,
                progressVersion = 3,
                order = duplicateOrder,
                outcome = "PROMOTED",
                observation = retainedFact
            )

            assertEquals(
                "2",
                scalar(
                    configuration,
                    """
                    SELECT COUNT(*)
                    FROM marketplace_order_revenue_source_promotion
                    WHERE organization_id='$organization'
                      AND marketplace_order_id='$duplicateOrder'
                      AND economic_observation_id='$retainedFact'
                      AND outcome IN ('PROMOTED','DUPLICATE')
                    """.trimIndent()
                )
            )

            assertEquals(
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.IntegrityFailure,
                source.findProofs(
                    OrganizationId(organization),
                    retainedId,
                    MarketplaceOrderId(duplicateOrder)
                )
            )

            /*
             * ----------------------------------------------------
             * Conflict terminals never provide authority.
             * ----------------------------------------------------
             */
            /*
             * Identity must originate from an internally consistent durable
             * source. A later distinct source coordinate is what proves the
             * currency conflict.
             */
            seedSource(
                configuration,
                organization,
                connection,
                40,
                "290000009103",
                "BRL",
                "10.000000",
                "2026-09-20 20:50:00.000001+00",
                "2026-09-20 20:55:00.000001+00"
            )

            seedIdentity(
                configuration,
                organization,
                connection,
                conflictOrder,
                "290000009103",
                "BRL",
                40
            )

            /*
             * Later Mercado Livre source disagrees with retained identity
             * currency and therefore legally supports IDENTITY_CONFLICT.
             */
            seedSource(
                configuration,
                organization,
                connection,
                4,
                "290000009103",
                "USD",
                "10.000000",
                "2026-09-20 21:00:00.000001+00",
                "2026-09-20 21:30:00.000001+00"
            )

            insertConflictTerminal(
                configuration,
                organization,
                connection,
                progressVersion = 4,
                order = conflictOrder,
                outcome = "IDENTITY_CONFLICT"
            )

            val conflictObservationId =
                MarketplaceEconomicEvidenceObservationId.parse(
                    UUID(0, 91_401).toString()
                )

            assertEquals(
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound,
                source.findProofs(
                    OrganizationId(organization),
                    conflictObservationId,
                    MarketplaceOrderId(conflictOrder)
                )
            )

            /*
             * Separate evidence conflict with same identity currency.
             */
            val evidenceConflictOrder = UUID(0, 91_104)

            seedSource(
                configuration,
                organization,
                connection,
                5,
                "290000009104",
                "BRL",
                "11.000000",
                "2026-09-20 21:05:00.000001+00",
                "2026-09-20 21:35:00.000001+00"
            )

            seedIdentity(
                configuration,
                organization,
                connection,
                evidenceConflictOrder,
                "290000009104",
                "BRL",
                5
            )

            insertConflictTerminal(
                configuration,
                organization,
                connection,
                progressVersion = 5,
                order = evidenceConflictOrder,
                outcome = "EVIDENCE_CONFLICT"
            )

            assertEquals(
                MercadoLivreClosedOrderRevenueAuthoritySourceResult.NotFound,
                source.findProofs(
                    OrganizationId(organization),
                    MarketplaceEconomicEvidenceObservationId.parse(
                        UUID(0, 91_402).toString()
                    ),
                    MarketplaceOrderId(evidenceConflictOrder)
                )
            )

            /*
             * Read-only behavior for findProofs was already proven at the
             * promoted replay boundary by exact before/after snapshot
             * equality. Subsequent fixture inserts legitimately change row
             * counts and therefore are not compared against that snapshot.
             */
            assertTrue(
                scalar(
                    configuration,
                    "SELECT COUNT(*) FROM marketplace_order_revenue_source_promotion"
                ).toInt() >= 6
            )
        } finally {
            postgres.stop()
        }
    }

    @Test
    fun `database operational failure maps to unavailable`() {
        val source =
            PostgresMercadoLivreClosedOrderRevenueAuthoritySource(
                PostgresConfiguration(
                    "jdbc:postgresql://127.0.0.1:1/flooow_d3a_unavailable",
                    "invalid",
                    "invalid"
                )
            )

        assertEquals(
            MercadoLivreClosedOrderRevenueAuthoritySourceResult.Unavailable,
            source.findProofs(
                OrganizationId(UUID(0, 92_001)),
                MarketplaceEconomicEvidenceObservationId.parse(
                    UUID(0, 92_002).toString()
                ),
                MarketplaceOrderId(UUID(0, 92_003))
            )
        )
    }

    private fun observation(
        organization: UUID,
        order: UUID,
        fact: UUID,
        component: UUID,
        externalOrder: String,
        amount: String,
        currency: String,
        occurredAt: Instant,
        observedAt: Instant
    ): MarketplaceEconomicComponentObservation {
        val marketplaceCurrency = MarketplaceCurrency(currency)

        return MarketplaceEconomicComponentObservation(
            id = MarketplaceEconomicEvidenceObservationId.parse(fact.toString()),
            subject =
                MarketplaceEconomicEvidenceSubject(
                    OrganizationId(organization),
                    MarketplaceOrderId(order),
                    MarketplaceKey("mercado-livre"),
                    MarketplaceExternalOrderId(externalOrder),
                    marketplaceCurrency
                ),
            family = MarketplaceEconomicEvidenceFamily.MARKETPLACE_ORDER,
            component =
                EconomicComponent(
                    OrganizationId(organization),
                    EconomicComponentId(component),
                    MarketplaceOrderId(order),
                    EconomicComponentType.REVENUE,
                    EconomicDirection.ADDITION,
                    MarketplaceMoney.parse(marketplaceCurrency, amount),
                    EconomicSource(
                        EconomicSourceKind.MARKETPLACE,
                        EconomicSourceSystemKey("br.com.mercadolivre"),
                        EconomicExternalReferenceState.Present(
                            EconomicExternalReference(externalOrder)
                        )
                    ),
                    occurredAt,
                    EconomicEvidenceQuality.CONFIRMED
                ),
            coverageClaim = EconomicComponentCoverage.PARTIAL,
            observedAt = observedAt
        )
    }

    private fun migrate(
        configuration: PostgresConfiguration,
        target: String? = null
    ) {
        val configured =
            Flyway.configure()
                .dataSource(
                    configuration.url,
                    configuration.user,
                    configuration.password
                )
                .locations("classpath:db/migration")

        if (target != null) {
            configured.target(MigrationVersion.fromVersion(target))
        }

        configured.load().migrate()
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
                '2026-09-20 17:00:00+00',
                '2026-09-20 17:00:00+00'
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
                '2026-09-20 17:00:00+00',
                '2026-09-20 17:00:00+00'
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
                100,
                decode('01','hex'),
                false,
                '2026-09-20 23:00:00+00',
                '2026-09-20 23:00:00+00'
            )
            """.trimIndent()
        )
    }

    private fun seedSource(
        configuration: PostgresConfiguration,
        organization: UUID,
        connection: UUID,
        progressVersion: Long,
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
                0,
                '$externalOrder',
                'paid',
                '2026-09-20 17:30:00.000001+00',
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
                '2026-09-20 17:45:00.000001+00',
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

    private fun insertSuccessfulTerminal(
        configuration: PostgresConfiguration,
        organization: UUID,
        connection: UUID,
        progressVersion: Long,
        order: UUID,
        outcome: String,
        observation: UUID
    ) {
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
                '$organization',
                '$connection',
                'marketplace-economic.order-source',
                $progressVersion,
                0,
                '$order',
                '$outcome',
                '$observation',
                '2026-09-20 22:00:00.000001+00'
            )
            """.trimIndent()
        )
    }

    private fun insertConflictTerminal(
        configuration: PostgresConfiguration,
        organization: UUID,
        connection: UUID,
        progressVersion: Long,
        order: UUID,
        outcome: String
    ) {
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
                '$organization',
                '$connection',
                'marketplace-economic.order-source',
                $progressVersion,
                0,
                '$order',
                '$outcome',
                '2026-09-20 22:05:00.000001+00'
            )
            """.trimIndent()
        )
    }

    private fun snapshot(
        configuration: PostgresConfiguration
    ): Map<String, String> =
        mapOf(
            "sourceRows" to
                scalar(
                    configuration,
                    "SELECT COUNT(*) FROM integration_mercado_livre_order_source_observation"
                ),
            "promotionRows" to
                scalar(
                    configuration,
                    "SELECT COUNT(*) FROM marketplace_order_revenue_source_promotion"
                ),
            "factRows" to
                scalar(
                    configuration,
                    "SELECT COUNT(*) FROM marketplace_economic_evidence_fact"
                ),
            "componentRows" to
                scalar(
                    configuration,
                    "SELECT COUNT(*) FROM marketplace_economic_evidence_component_fact"
                ),
            "identityRows" to
                scalar(
                    configuration,
                    "SELECT COUNT(*) FROM marketplace_order_identity_registry"
                )
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