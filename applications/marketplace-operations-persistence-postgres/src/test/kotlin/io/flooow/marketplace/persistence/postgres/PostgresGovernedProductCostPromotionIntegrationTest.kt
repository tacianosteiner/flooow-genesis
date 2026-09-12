package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.promotion.*
import io.flooow.marketplace.operations.identity.*
import io.flooow.organization.OrganizationId
import java.math.BigDecimal
import java.sql.DriverManager
import java.sql.Timestamp
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresGovernedProductCostPromotionIntegrationTest {
    @Test
    fun `confirmed governed product cost is durable idempotent auditable and append only`() =
        withPostgres { configuration ->
            val fixture = seedDurableAuthorities(configuration)
            val identityRepository = PostgresCrossSystemProductIdentityDecisionRepository(configuration)
            val identity = assertIs<CrossSystemProductIdentityWriteResult.Applied>(
                identityRepository.record(fixture.identityRequest, fixture.decidedAt)
            ).decision
            val identities = CrossSystemProductIdentityConfirmationService(identityRepository)
            assertIs<CrossSystemProductIdentityResolution.Confirmed>(identities.resolve(fixture.relation))

            val evidenceRepository = PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration)
            val service = GovernedProductCostPromotionService(
                PostgresGovernedProductCostPromotionAuthority(configuration),
                identities,
                evidenceRepository,
                Clock.fixed(fixture.promotedAt, ZoneOffset.UTC)
            )
            val firstRequest = fixture.request(inputProgressVersion = 0)

            assertEquals(GovernedProductCostPromotionResult.Promoted, service.promote(firstRequest))
            val firstRead = found(evidenceRepository, fixture.subject)
            val firstFact = productCosts(firstRead).single()
            val firstComponent = firstFact.observation.component
            val firstReference = assertIs<EconomicExternalReferenceState.Present>(
                firstComponent.source.externalReference
            ).reference.value

            assertEquals(fixture.subject, firstRead.evidence.subject)
            assertEquals(fixture.organization, firstComponent.organizationId)
            assertEquals(fixture.subject.orderId, firstComponent.orderId)
            assertEquals(MarketplaceEconomicEvidenceFamily.PRODUCT_COST, firstFact.family)
            assertEquals(EconomicComponentType.PRODUCT_COST, firstComponent.type)
            assertEquals(EconomicDirection.DEDUCTION, firstComponent.direction)
            assertEquals(EconomicEvidenceQuality.CONFIRMED, firstComponent.quality)
            assertEquals(EconomicComponentCoverage.PARTIAL, firstFact.observation.coverageClaim)
            assertEquals(EconomicSourceKind.ERP, firstComponent.source.kind)
            assertEquals(EconomicSourceSystemKey("omie"), firstComponent.source.systemKey)
            assertEquals(fixture.firstObservedAt, firstComponent.occurredAt)
            assertEquals(fixture.promotedAt, firstFact.observedAt)
            assertEquals(MarketplaceCurrency("USD"), firstComponent.magnitude.currency)
            assertDecimal("7.8125", firstComponent.magnitude.amount)
            assertEquals(
                "omie-product-cost/${fixture.omieConnection}/0/0/${identity.request.id.value}",
                firstReference
            )

            val durableIdentity = requireNotNull(
                identityRepository.find(fixture.organization, identity.request.id)
            )
            assertEquals(fixture.relation, durableIdentity.request.relation)
            assertEquals(fixture.identityRequest.correlationId, durableIdentity.request.correlationId)
            assertEquals("TASK-0165K durable confirmation", durableIdentity.request.provenance.encodedForPersistence())
            assertEquals(fixture.mlConnection.toString(), durableIdentity.request.relation.scope.mercadoLivreConnectionId)
            assertEquals(fixture.omieConnection.toString(), durableIdentity.request.relation.scope.omieConnectionId)
            assertEquals(MercadoLivreProductIdentity("MLB-1", "SKU-1"), durableIdentity.request.relation.mercadoLivre)
            assertEquals(OmieProviderProductIdentity("OMIE-1"), durableIdentity.request.relation.omie)
            assertEquals(fixture.mlConnection.toString(), scalarText(configuration,
                "SELECT first_source_connection_id::text FROM marketplace_order_identity_registry WHERE organization_id=? AND marketplace_order_id=?",
                fixture.organization.value, fixture.subject.orderId.value))
            assertDecimal("3.125", scalarDecimal(configuration,
                "SELECT unit_cmc FROM integration_omie_product_cost_source_observation WHERE organization_id=? AND connection_id=? AND input_progress_version=0 AND record_ordinal=0",
                fixture.organization.value, fixture.omieConnection))
            assertDecimal("2.5", scalarDecimal(configuration,
                "SELECT quantity FROM integration_mercado_livre_order_item_source_observation WHERE organization_id=? AND connection_id=? AND item_ref='MLB-1' AND seller_sku='SKU-1'",
                fixture.organization.value, fixture.mlConnection))
            assertEquals(listOf("USD", "USD", "USD"), listOf(
                scalarText(configuration, "SELECT currency FROM integration_mercado_livre_order_source_observation WHERE organization_id=? AND connection_id=?", fixture.organization.value, fixture.mlConnection).trimEnd(),
                scalarText(configuration, "SELECT currency FROM integration_mercado_livre_order_item_source_observation WHERE organization_id=? AND connection_id=?", fixture.organization.value, fixture.mlConnection).trimEnd(),
                scalarText(configuration, "SELECT currency FROM marketplace_order_identity_registry WHERE organization_id=? AND marketplace_order_id=?", fixture.organization.value, fixture.subject.orderId.value).trimEnd()
            ))
            assertEquals(MarketplaceCurrency("USD"), firstRequest.currencyAuthority)
            assertDecimal("2.5", requireNotNull(firstRequest.allocation).quantity)

            assertEquals(GovernedProductCostPromotionResult.AlreadyPromoted, service.promote(firstRequest))
            val replayed = found(evidenceRepository, fixture.subject)
            assertEquals(1, productCosts(replayed).size)
            assertEquals(firstFact, productCosts(replayed).single())
            assertEquals(1, componentRowCount(configuration, fixture))

            val newerRequest = fixture.request(inputProgressVersion = 1)
            assertEquals(GovernedProductCostPromotionResult.Promoted, service.promote(newerRequest))
            val appended = found(evidenceRepository, fixture.subject)
            val productCosts = productCosts(appended)
            assertEquals(2, productCosts.size)
            assertTrue(productCosts.contains(firstFact))
            assertTrue(appended.evidence.corrections.isEmpty())
            val newerFact = productCosts.single { it != firstFact }
            assertDecimal("10.625", newerFact.observation.component.magnitude.amount)
            assertEquals(fixture.firstObservedAt.plusSeconds(3600), newerFact.observation.component.occurredAt)
            assertEquals(
                "omie-product-cost/${fixture.omieConnection}/1/0/${identity.request.id.value}",
                assertIs<EconomicExternalReferenceState.Present>(
                    newerFact.observation.component.source.externalReference
                ).reference.value
            )
            assertEquals(2, componentRowCount(configuration, fixture))
            assertDecimal("7.8125", scalarDecimal(configuration,
                "SELECT magnitude FROM marketplace_economic_evidence_component_fact WHERE organization_id=? AND marketplace_order_id=? AND source_external_reference=?",
                fixture.organization.value, fixture.subject.orderId.value, firstReference))
        }

    @Test
    fun `blocked promotions produce zero durable product cost writes`() = withPostgres { configuration ->
        val organization = OrganizationId(UUID.fromString("11111111-1111-4111-8111-111111111111"))
        execute(configuration, "INSERT INTO integration_organization VALUES (?,'ACTIVE',now(),now())", organization.value)
        val subject = subject(organization)
        val relation = relation(organization)
        val request = request(subject, relation, 0)
        val evidence = PostgresMarketplaceIndependentEconomicEvidenceRepository(configuration)
        val confirmed = identityDecision(relation, CrossSystemProductIdentityDecisionKind.CONFIRMED)
        val rejected = identityDecision(relation, CrossSystemProductIdentityDecisionKind.REJECTED)

        fun promote(
            decisions: List<CrossSystemProductIdentityDecision>,
            source: GovernedProductCostSourceRead,
            candidate: GovernedProductCostPromotionRequest = request
        ) = GovernedProductCostPromotionService(
            object : GovernedProductCostPromotionAuthority {
                override fun read(request: GovernedProductCostPromotionRequest) = source
            },
            CrossSystemProductIdentityConfirmationService(IdentityRepository(decisions)),
            evidence,
            Clock.fixed(Instant.parse("2026-09-11T20:00:00Z"), ZoneOffset.UTC)
        ).promote(candidate)

        assertEquals(
            GovernedProductCostPromotionResult.IdentityUnconfirmed,
            promote(emptyList(), GovernedProductCostSourceRead.Available(BigDecimal.ONE, Instant.EPOCH))
        )
        assertEquals(
            GovernedProductCostPromotionResult.IdentityRejected,
            promote(listOf(rejected), GovernedProductCostSourceRead.Available(BigDecimal.ONE, Instant.EPOCH))
        )
        assertEquals(
            GovernedProductCostPromotionResult.CostMissing,
            promote(listOf(confirmed), GovernedProductCostSourceRead.CostMissing)
        )
        assertEquals(
            GovernedProductCostPromotionResult.CurrencyUnavailable,
            promote(
                listOf(confirmed),
                GovernedProductCostSourceRead.Available(BigDecimal.ONE, Instant.EPOCH),
                request.copy(currencyAuthority = null)
            )
        )
        assertEquals(
            GovernedProductCostPromotionResult.AllocationUnavailable,
            promote(
                listOf(confirmed),
                GovernedProductCostSourceRead.Available(BigDecimal.ONE, Instant.EPOCH),
                request.copy(allocation = null)
            )
        )
        assertIs<MarketplaceIndependentEconomicEvidenceReadResult.NotFound>(evidence.find(subject))
        assertEquals(0, scalarInt(configuration,
            "SELECT count(*) FROM marketplace_economic_evidence_component_fact WHERE component_type='PRODUCT_COST'"))
    }

    private data class Fixture(
        val organization: OrganizationId,
        val mlConnection: UUID,
        val omieConnection: UUID,
        val subject: MarketplaceEconomicEvidenceSubject,
        val relation: CrossSystemProductIdentityRelation,
        val identityRequest: CrossSystemProductIdentityDecisionRequest,
        val decidedAt: Instant,
        val firstObservedAt: Instant,
        val promotedAt: Instant
    ) {
        fun request(inputProgressVersion: Long) = GovernedProductCostPromotionRequest(
            subject,
            relation,
            OmieProductCostSourceObservationKey(
                relation.scope.omieConnectionId,
                "marketplace-economic.product-cost",
                inputProgressVersion,
                0
            ),
            ProductCostQuantityAllocation(BigDecimal("2.5")),
            MarketplaceCurrency("USD")
        )
    }

    private fun seedDurableAuthorities(configuration: PostgresConfiguration): Fixture {
        val organization = OrganizationId(UUID.fromString("11111111-1111-4111-8111-111111111111"))
        val mlConnection = UUID.fromString("22222222-2222-4222-8222-222222222222")
        val omieConnection = UUID.fromString("33333333-3333-4333-8333-333333333333")
        val firstObservedAt = Instant.parse("2026-09-11T18:00:00Z")
        val secondObservedAt = firstObservedAt.plusSeconds(3600)
        val subject = subject(organization)
        val relation = relation(organization)

        execute(configuration, "INSERT INTO integration_organization VALUES (?,'ACTIVE',?,?)",
            organization.value, Timestamp.from(firstObservedAt), Timestamp.from(firstObservedAt))
        execute(configuration, "INSERT INTO integration_connection VALUES (?,?,?,?,'ACTIVE',1,?,?)",
            organization.value, mlConnection, "br.com.mercadolivre", "OAUTH2_AUTHORIZATION_CODE", Timestamp.from(firstObservedAt), Timestamp.from(firstObservedAt))
        execute(configuration, "INSERT INTO integration_connection VALUES (?,?,?,?,'ACTIVE',1,?,?)",
            organization.value, omieConnection, "omie", "STATIC_API_CREDENTIAL", Timestamp.from(firstObservedAt), Timestamp.from(firstObservedAt))
        execute(configuration, "INSERT INTO integration_connector_progress VALUES (?,?,?,1,NULL,true,?,?)",
            organization.value, mlConnection, "marketplace-economic.order-source", Timestamp.from(firstObservedAt), Timestamp.from(firstObservedAt))
        execute(configuration, "INSERT INTO integration_connector_page_commit VALUES (?,?,?,0,?,1,true,?,?)",
            organization.value, mlConnection, "marketplace-economic.order-source", ByteArray(32) { 1 }, Timestamp.from(firstObservedAt), Timestamp.from(firstObservedAt))
        execute(configuration,
            "INSERT INTO integration_mercado_livre_order_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,provider_status,date_created,date_last_updated,currency,total_amount,observed_at) VALUES (?,?,'marketplace-economic.order-source',0,0,'ORDER-1','paid',?,?,'USD',10,?)",
            organization.value, mlConnection, Timestamp.from(firstObservedAt), Timestamp.from(firstObservedAt), Timestamp.from(firstObservedAt))
        execute(configuration,
            "INSERT INTO integration_mercado_livre_order_item_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,item_ordinal,item_ref,quantity,unit_price,currency,seller_sku) VALUES (?,?,'marketplace-economic.order-source',0,0,0,'MLB-1',2.5,5,'USD','SKU-1')",
            organization.value, mlConnection)
        execute(configuration,
            "INSERT INTO marketplace_order_identity_registry (organization_id,marketplace_key,external_order_id,marketplace_order_id,currency,allocated_at,first_source_connection_id,first_source_capability,first_source_input_progress_version,first_source_record_ordinal) VALUES (?,'mercado-livre','ORDER-1',?,'USD',?,?,'marketplace-economic.order-source',0,0)",
            organization.value, subject.orderId.value, Timestamp.from(firstObservedAt), mlConnection)
        execute(configuration, "INSERT INTO integration_connector_progress VALUES (?,?,?,2,NULL,true,?,?)",
            organization.value, omieConnection, "marketplace-economic.product-cost", Timestamp.from(secondObservedAt), Timestamp.from(secondObservedAt))
        listOf(0L to firstObservedAt, 1L to secondObservedAt).forEach { (version, observedAt) ->
            execute(configuration, "INSERT INTO integration_connector_page_commit VALUES (?,?,?, ?,?,1,true,?,?)",
                organization.value, omieConnection, "marketplace-economic.product-cost", version, ByteArray(32) { (version + 2).toByte() }, Timestamp.from(observedAt), Timestamp.from(observedAt))
        }
        execute(configuration,
            "INSERT INTO integration_omie_product_cost_source_observation VALUES (?,?,'marketplace-economic.product-cost',0,0,'OMIE-1',NULL,NULL,'LOCAL',3.125,NULL,NULL,NULL,'2026-09-11',?)",
            organization.value, omieConnection, Timestamp.from(firstObservedAt))
        execute(configuration,
            "INSERT INTO integration_omie_product_cost_source_observation VALUES (?,?,'marketplace-economic.product-cost',1,0,'OMIE-1',NULL,NULL,'LOCAL',4.25,NULL,NULL,NULL,'2026-09-11',?)",
            organization.value, omieConnection, Timestamp.from(secondObservedAt))

        val identityRequest = CrossSystemProductIdentityDecisionRequest(
            CrossSystemProductIdentityDecisionId(UUID.fromString("55555555-5555-4555-8555-555555555555")),
            relation,
            CrossSystemProductIdentityDecisionKind.CONFIRMED,
            CrossSystemProductIdentityPrincipal.of("operator:test"),
            CrossSystemProductIdentityDecisionReason.EXPLICIT_CONFIRMATION,
            CrossSystemProductIdentityProvenance.of("TASK-0165K durable confirmation"),
            CrossSystemProductIdentityCorrelationId(UUID.fromString("66666666-6666-4666-8666-666666666666"))
        )
        return Fixture(
            organization, mlConnection, omieConnection, subject, relation, identityRequest,
            secondObservedAt.plusSeconds(1), firstObservedAt, secondObservedAt.plusSeconds(2)
        )
    }

    private fun subject(organization: OrganizationId) = MarketplaceEconomicEvidenceSubject(
        organization,
        MarketplaceOrderId(UUID.fromString("44444444-4444-4444-8444-444444444444")),
        MarketplaceKey("mercado-livre"),
        MarketplaceExternalOrderId("ORDER-1"),
        MarketplaceCurrency("USD")
    )

    private fun relation(organization: OrganizationId) = CrossSystemProductIdentityRelation(
        CrossSystemProductIdentityScope(
            organization,
            "22222222-2222-4222-8222-222222222222",
            "33333333-3333-4333-8333-333333333333"
        ),
        MercadoLivreProductIdentity("MLB-1", "SKU-1"),
        OmieProviderProductIdentity("OMIE-1")
    )

    private fun request(
        subject: MarketplaceEconomicEvidenceSubject,
        relation: CrossSystemProductIdentityRelation,
        inputProgressVersion: Long
    ) = GovernedProductCostPromotionRequest(
        subject,
        relation,
        OmieProductCostSourceObservationKey(
            relation.scope.omieConnectionId,
            "marketplace-economic.product-cost",
            inputProgressVersion,
            0
        ),
        ProductCostQuantityAllocation(BigDecimal("2.5")),
        MarketplaceCurrency("USD")
    )

    private fun identityDecision(
        relation: CrossSystemProductIdentityRelation,
        kind: CrossSystemProductIdentityDecisionKind
    ) = CrossSystemProductIdentityDecision(
        CrossSystemProductIdentityDecisionRequest(
            CrossSystemProductIdentityDecisionId(UUID.randomUUID()),
            relation,
            kind,
            CrossSystemProductIdentityPrincipal.of("test"),
            if (kind == CrossSystemProductIdentityDecisionKind.CONFIRMED)
                CrossSystemProductIdentityDecisionReason.EXPLICIT_CONFIRMATION
            else CrossSystemProductIdentityDecisionReason.EXPLICIT_REJECTION,
            CrossSystemProductIdentityProvenance.of("test"),
            CrossSystemProductIdentityCorrelationId(UUID.randomUUID())
        ),
        1,
        Instant.EPOCH
    )

    private class IdentityRepository(
        private val decisions: List<CrossSystemProductIdentityDecision>
    ) : CrossSystemProductIdentityDecisionRepository {
        override fun record(request: CrossSystemProductIdentityDecisionRequest, decidedAt: Instant) =
            CrossSystemProductIdentityWriteResult.IntegrityFailure
        override fun find(organizationId: OrganizationId, id: CrossSystemProductIdentityDecisionId) =
            decisions.singleOrNull { it.request.id == id && it.request.relation.scope.organizationId == organizationId }
        override fun history(relation: CrossSystemProductIdentityRelation) =
            decisions.filter { it.request.relation == relation }
        override fun currentForMarketplaceIdentity(
            scope: CrossSystemProductIdentityScope,
            identity: MercadoLivreProductIdentity
        ) = decisions.filter {
            it.request.relation.scope == scope && it.request.relation.mercadoLivre == identity
        }
    }

    private fun found(
        repository: MarketplaceIndependentEconomicEvidenceRepository,
        subject: MarketplaceEconomicEvidenceSubject
    ) = assertIs<MarketplaceIndependentEconomicEvidenceReadResult.Found>(repository.find(subject))
        .versionedEvidence

    private fun productCosts(versioned: VersionedMarketplaceIndependentEconomicEvidence) =
        versioned.evidence.historicalFacts.filterIsInstance<MarketplaceIndependentEconomicFact.Component>()
            .filter { it.family == MarketplaceEconomicEvidenceFamily.PRODUCT_COST }

    private fun componentRowCount(configuration: PostgresConfiguration, fixture: Fixture) = scalarInt(
        configuration,
        "SELECT count(*) FROM marketplace_economic_evidence_component_fact WHERE organization_id=? AND marketplace_order_id=? AND component_type='PRODUCT_COST'",
        fixture.organization.value,
        fixture.subject.orderId.value
    )

    private fun execute(configuration: PostgresConfiguration, sql: String, vararg values: Any?) =
        DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { connection ->
            connection.prepareStatement(sql).use { statement ->
                values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }
                statement.executeUpdate()
            }
        }

    private fun scalarText(configuration: PostgresConfiguration, sql: String, vararg values: Any?): String =
        scalar(configuration, sql, *values) { it.getString(1) }

    private fun scalarDecimal(configuration: PostgresConfiguration, sql: String, vararg values: Any?): BigDecimal =
        scalar(configuration, sql, *values) { it.getBigDecimal(1) }

    private fun scalarInt(configuration: PostgresConfiguration, sql: String, vararg values: Any?): Int =
        scalar(configuration, sql, *values) { it.getInt(1) }

    private fun <T> scalar(
        configuration: PostgresConfiguration,
        sql: String,
        vararg values: Any?,
        read: (java.sql.ResultSet) -> T
    ): T = DriverManager.getConnection(configuration.url, configuration.user, configuration.password).use { connection ->
        connection.prepareStatement(sql).use { statement ->
            values.forEachIndexed { index, value -> statement.setObject(index + 1, value) }
            statement.executeQuery().use { result ->
                check(result.next())
                read(result)
            }
        }
    }

    private fun assertDecimal(expected: String, actual: BigDecimal) {
        assertTrue(actual.compareTo(BigDecimal(expected)) == 0, "expected $expected but was $actual")
    }

    private fun withPostgres(block: (PostgresConfiguration) -> Unit) {
        PostgreSQLContainer("postgres:18.4").use { postgres ->
            postgres.start()
            val configuration = PostgresConfiguration(postgres.jdbcUrl, postgres.username, postgres.password)
            Flyway.configure().dataSource(configuration.url, configuration.user, configuration.password)
                .load().migrate()
            block(configuration)
        }
    }
}
