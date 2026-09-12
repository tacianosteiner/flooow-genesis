package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.promotion.*
import io.flooow.marketplace.operations.identity.*
import io.flooow.organization.OrganizationId
import java.math.BigDecimal
import java.sql.DriverManager
import java.sql.Timestamp
import java.util.UUID
import kotlin.test.Test
import kotlin.test.assertIs
import kotlin.test.assertTrue
import org.flywaydb.core.Flyway
import org.testcontainers.postgresql.PostgreSQLContainer

class PostgresGovernedProductCostPromotionAuthorityTest {
 @Test fun `does not resolve durable authority across organizations`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c); val other=OrganizationId(UUID.randomUUID())
   DriverManager.getConnection(c.url,c.user,c.password).use { db -> db.prepareStatement("INSERT INTO integration_organization VALUES (?,'ACTIVE',now(),now())").use { it.setObject(1,other.value); it.executeUpdate() } }
   val request=fixture.request(other); val result=PostgresGovernedProductCostPromotionAuthority(c).read(request)
   assertIs<GovernedProductCostSourceRead.SubjectUnresolved>(result)
  }
 }
 @Test fun `does not resolve durable authority across Mercado Livre connections`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c); val otherMl=UUID.randomUUID()
   persistActiveConnection(c,fixture.organization,otherMl,"br.com.mercadolivre","OAUTH2_AUTHORIZATION_CODE")
   val request=fixture.request(fixture.organization,mercadoLivreConnection=otherMl); val result=PostgresGovernedProductCostPromotionAuthority(c).read(request)
   assertIs<GovernedProductCostSourceRead.SubjectUnresolved>(result)
  }
 }
 @Test fun `does not resolve durable authority across Omie connections`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c); val otherOmie=UUID.randomUUID()
   persistActiveConnection(c,fixture.organization,otherOmie,"omie","STATIC_API_CREDENTIAL")
   val request=fixture.request(fixture.organization,omieConnection=otherOmie); val result=PostgresGovernedProductCostPromotionAuthority(c).read(request)
   assertIs<GovernedProductCostSourceRead.SubjectUnresolved>(result)
  }
 }
 @Test fun `missing Omie product-cost source observation is not promotable`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c,includeOmieCostObservation=false)
   val result=PostgresGovernedProductCostPromotionAuthority(c).read(fixture.request(fixture.organization))
   assertIs<GovernedProductCostSourceRead.SubjectUnresolved>(result)
  }
 }
 @Test fun `null nCMC is treated as missing cost`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c,omieUnitCost=null)
   val result=PostgresGovernedProductCostPromotionAuthority(c).read(fixture.request(fixture.organization))
   assertIs<GovernedProductCostSourceRead.CostMissing>(result)
  }
 }
 @Test fun `zero nCMC remains a valid observed zero`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c,omieUnitCost=BigDecimal.ZERO)
   val result=PostgresGovernedProductCostPromotionAuthority(c).read(fixture.request(fixture.organization))
   assertIs<GovernedProductCostSourceRead.Available>(result)
   assertTrue(result.unitCost.compareTo(BigDecimal.ZERO) == 0)
  }
 }
 @Test fun `missing durable currency is not promotable`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c)
   val result=PostgresGovernedProductCostPromotionAuthority(c).read(fixture.request(fixture.organization,currencyAuthority=null))
   assertIs<GovernedProductCostSourceRead.CurrencyUnavailable>(result)
  }
 }
 @Test fun `contradictory durable currency authorities fail closed`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c,itemCurrency="EUR")
   val result=PostgresGovernedProductCostPromotionAuthority(c).read(fixture.request(fixture.organization))
   assertIs<GovernedProductCostSourceRead.IntegrityFailure>(result)
  }
 }
 @Test fun `does not infer BRL when governed currency authority is missing`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c,marketplaceCurrency="BRL")
   val result=PostgresGovernedProductCostPromotionAuthority(c).read(fixture.request(fixture.organization,currencyAuthority=null))
   assertIs<GovernedProductCostSourceRead.CurrencyUnavailable>(result)
  }
 }
 @Test fun `missing durable quantity allocation is not promotable`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c)
   val result=PostgresGovernedProductCostPromotionAuthority(c).read(fixture.request(fixture.organization,allocation=null))
   assertIs<GovernedProductCostSourceRead.AllocationUnavailable>(result)
  }
 }
 @Test fun `contradictory durable quantity authorities fail closed`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val fixture=persistValidFixture(c)
   val result=PostgresGovernedProductCostPromotionAuthority(c).read(fixture.request(fixture.organization,allocation=ProductCostQuantityAllocation(BigDecimal("3"))))
   assertIs<GovernedProductCostSourceRead.IntegrityFailure>(result)
  }
 }
 @Test fun `confirmed exact durable authorities resolve promotable product cost`() {
  PostgreSQLContainer("postgres:18.4").use { pg -> pg.start(); val c=PostgresConfiguration(pg.jdbcUrl,pg.username,pg.password); Flyway.configure().dataSource(c.url,c.user,c.password).load().migrate()
   val org=OrganizationId(UUID.randomUUID()); val ml=UUID.randomUUID(); val omie=UUID.randomUUID(); val order=MarketplaceOrderId(UUID.randomUUID()); val now=Timestamp.from(java.time.Instant.parse("2026-09-11T18:00:00Z"));
   DriverManager.getConnection(c.url,c.user,c.password).use { db -> fun x(s:String,vararg v:Any){db.prepareStatement(s).use{p->v.forEachIndexed{i,a->p.setObject(i+1,a)};p.executeUpdate()}}
    x("INSERT INTO integration_organization VALUES (?,'ACTIVE',?,?)",org.value,now,now); x("INSERT INTO integration_connection VALUES (?,?,?,?,'ACTIVE',1,?,?)",org.value,ml,"br.com.mercadolivre","OAUTH2_AUTHORIZATION_CODE",now,now); x("INSERT INTO integration_connection VALUES (?,?,?,?,'ACTIVE',1,?,?)",org.value,omie,"omie","STATIC_API_CREDENTIAL",now,now)
    x("INSERT INTO integration_connector_progress VALUES (?,?,?,1,NULL,true,?,?)",org.value,ml,"marketplace-economic.order-source",now,now); x("INSERT INTO integration_connector_page_commit VALUES (?,?,?,0,?,1,true,?,?)",org.value,ml,"marketplace-economic.order-source",ByteArray(32),now,now); x("INSERT INTO integration_mercado_livre_order_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,provider_status,date_created,date_last_updated,currency,total_amount,observed_at) VALUES (?,?,'marketplace-economic.order-source',0,0,'O','paid',?,?, 'USD',10,?)",org.value,ml,now,now,now); x("INSERT INTO integration_mercado_livre_order_item_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,item_ordinal,item_ref,quantity,unit_price,currency,seller_sku) VALUES (?,?,'marketplace-economic.order-source',0,0,0,'I',2,5,'USD','SKU')",org.value,ml)
    x("INSERT INTO marketplace_order_identity_registry (organization_id,marketplace_key,external_order_id,marketplace_order_id,currency,allocated_at,first_source_connection_id,first_source_capability,first_source_input_progress_version,first_source_record_ordinal) VALUES (?,'mercado-livre','O',?,'USD',?,?,?,0,0)",org.value,order.value,now,ml,"marketplace-economic.order-source")
    x("INSERT INTO integration_connector_progress VALUES (?,?,?,1,NULL,true,?,?)",org.value,omie,"marketplace-economic.product-cost",now,now); x("INSERT INTO integration_connector_page_commit VALUES (?,?,?,0,?,1,true,?,?)",org.value,omie,"marketplace-economic.product-cost",ByteArray(32),now,now); x("INSERT INTO integration_omie_product_cost_source_observation VALUES (?,?,'marketplace-economic.product-cost',0,0,'P',NULL,NULL,'L',3,NULL,NULL,NULL,'2026-09-11',?)",org.value,omie,now)
   }
   val rel=CrossSystemProductIdentityRelation(CrossSystemProductIdentityScope(org,ml.toString(),omie.toString()),MercadoLivreProductIdentity("I","SKU"),OmieProviderProductIdentity("P")); val req=GovernedProductCostPromotionRequest(MarketplaceEconomicEvidenceSubject(org,order,MarketplaceKey("mercado-livre"),MarketplaceExternalOrderId("O"),MarketplaceCurrency("USD")),rel,OmieProductCostSourceObservationKey(omie.toString(),"marketplace-economic.product-cost",0,0),ProductCostQuantityAllocation(BigDecimal("2")),MarketplaceCurrency("USD")); val r=PostgresGovernedProductCostPromotionAuthority(c).read(req); assertIs<GovernedProductCostSourceRead.Available>(r); assertTrue(r.unitCost.compareTo(BigDecimal("3")) == 0)
  }
 }
 private data class Fixture(val organization: OrganizationId,val ml: UUID,val omie: UUID,val order: MarketplaceOrderId,val currency: MarketplaceCurrency) {
  fun request(org: OrganizationId,mercadoLivreConnection: UUID=ml,omieConnection: UUID=omie,allocation: ProductCostQuantityAllocation?=ProductCostQuantityAllocation(BigDecimal("2")),currencyAuthority: MarketplaceCurrency?=currency)=GovernedProductCostPromotionRequest(MarketplaceEconomicEvidenceSubject(org,order,MarketplaceKey("mercado-livre"),MarketplaceExternalOrderId("O"),currency),CrossSystemProductIdentityRelation(CrossSystemProductIdentityScope(org,mercadoLivreConnection.toString(),omieConnection.toString()),MercadoLivreProductIdentity("I","SKU"),OmieProviderProductIdentity("P")),OmieProductCostSourceObservationKey(omieConnection.toString(),"marketplace-economic.product-cost",0,0),allocation,currencyAuthority)
 }
 private fun persistActiveConnection(c: PostgresConfiguration,organization: OrganizationId,connection: UUID,provider: String,auth: String) {
  DriverManager.getConnection(c.url,c.user,c.password).use { db -> db.prepareStatement("INSERT INTO integration_connection VALUES (?,?,?,?,'ACTIVE',1,now(),now())").use { statement -> statement.setObject(1,organization.value); statement.setObject(2,connection); statement.setString(3,provider); statement.setString(4,auth); statement.executeUpdate() } }
 }
 private fun persistValidFixture(c: PostgresConfiguration,includeOmieCostObservation: Boolean=true,omieUnitCost: BigDecimal?=BigDecimal("3"),marketplaceCurrency: String="USD",itemCurrency: String=marketplaceCurrency): Fixture { val o=OrganizationId(UUID.randomUUID()); val ml=UUID.randomUUID(); val om=UUID.randomUUID(); val id=MarketplaceOrderId(UUID.randomUUID()); val n=Timestamp.from(java.time.Instant.parse("2026-09-11T18:00:00Z")); DriverManager.getConnection(c.url,c.user,c.password).use { d -> fun x(s:String,vararg v:Any?){d.prepareStatement(s).use{p->v.forEachIndexed{i,a->p.setObject(i+1,a)};p.executeUpdate()}}; x("INSERT INTO integration_organization VALUES (?,'ACTIVE',?,?)",o.value,n,n); x("INSERT INTO integration_connection VALUES (?,?,?,?,'ACTIVE',1,?,?)",o.value,ml,"br.com.mercadolivre","OAUTH2_AUTHORIZATION_CODE",n,n); x("INSERT INTO integration_connection VALUES (?,?,?,?,'ACTIVE',1,?,?)",o.value,om,"omie","STATIC_API_CREDENTIAL",n,n); x("INSERT INTO integration_connector_progress VALUES (?,?,?,1,NULL,true,?,?)",o.value,ml,"marketplace-economic.order-source",n,n); x("INSERT INTO integration_connector_page_commit VALUES (?,?,?,0,?,1,true,?,?)",o.value,ml,"marketplace-economic.order-source",ByteArray(32),n,n); x("INSERT INTO integration_mercado_livre_order_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,external_order_ref,provider_status,date_created,date_last_updated,currency,total_amount,observed_at) VALUES (?,?,'marketplace-economic.order-source',0,0,'O','paid',?,?,?,10,?)",o.value,ml,n,n,marketplaceCurrency,n); x("INSERT INTO integration_mercado_livre_order_item_source_observation (organization_id,connection_id,capability,input_progress_version,record_ordinal,item_ordinal,item_ref,quantity,unit_price,currency,seller_sku) VALUES (?,?,'marketplace-economic.order-source',0,0,0,'I',2,5,?,'SKU')",o.value,ml,itemCurrency); x("INSERT INTO marketplace_order_identity_registry (organization_id,marketplace_key,external_order_id,marketplace_order_id,currency,allocated_at,first_source_connection_id,first_source_capability,first_source_input_progress_version,first_source_record_ordinal) VALUES (?,'mercado-livre','O',?,?,?,?,?,0,0)",o.value,id.value,marketplaceCurrency,n,ml,"marketplace-economic.order-source"); x("INSERT INTO integration_connector_progress VALUES (?,?,?,1,NULL,true,?,?)",o.value,om,"marketplace-economic.product-cost",n,n); x("INSERT INTO integration_connector_page_commit VALUES (?,?,?,0,?,1,true,?,?)",o.value,om,"marketplace-economic.product-cost",ByteArray(32),n,n); if(includeOmieCostObservation)x("INSERT INTO integration_omie_product_cost_source_observation VALUES (?,?,'marketplace-economic.product-cost',0,0,'P',NULL,NULL,'L',?,NULL,NULL,NULL,'2026-09-11',?)",o.value,om,omieUnitCost,n) }; return Fixture(o,ml,om,id,MarketplaceCurrency(marketplaceCurrency)) }
}
