package io.flooow.marketplace.persistence.postgres

import java.sql.Connection
import java.sql.DriverManager
import java.security.MessageDigest
import java.util.Collections
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceChangeFeed
import io.flooow.marketplace.operations.economics.evidence.MarketplaceIndependentEconomicEvidenceRepository
import io.flooow.marketplace.operations.economics.sales.MarketplaceSalesIntelligenceProjectionProcessor
import java.time.Clock

data class RoomHistoryMigrationEntry(val version: String, val type: String, val script: String, val checksum: Int, val description: String = script.substringAfter("__").removeSuffix(".sql").replace('_',' ')) {
    init { require(version.isNotBlank() && type == "SQL" && script.isNotBlank()) }
}

/** Matching release source artifact. Never infer expectations from the target database. */
class RoomHistoryStartupManifest(
    migrations: List<RoomHistoryMigrationEntry>,
    catalog: Map<RoomHistoryCatalogSection, List<List<String>>>,
    val runtimeIdentity: String,
    val qualificationOnly: Boolean = false,
    val historicalMigration: RoomHistoryMigrationEntry? = null
) {
    val migrations = Collections.unmodifiableList(migrations.toList())
    val catalog = Collections.unmodifiableMap(catalog.mapValues { (_,rows) -> Collections.unmodifiableList(rows.map { Collections.unmodifiableList(it.toList()) }) })
    init {
        require(migrations.isNotEmpty() && migrations.map { it.version }.distinct().size == migrations.size)
        require(catalog.keys == RoomHistoryCatalogSection.entries.toSet())
        require(runtimeIdentity == "flooow_room_history_runtime")
    }
    override fun toString() = "[REDACTED]"
}

enum class RoomHistoryStartupStatus {
    READY, NOT_CONFIGURED, MIGRATION_HISTORY_MISMATCH, SCHEMA_MISMATCH, OWNER_MISMATCH,
    ACL_MISMATCH, FUNCTION_MISMATCH, TRIGGER_MISMATCH, RUNTIME_IDENTITY_MISMATCH, UNAVAILABLE
}

enum class RoomHistoryCatalogSection(val failure: RoomHistoryStartupStatus) {
    TABLES(RoomHistoryStartupStatus.OWNER_MISMATCH), COLUMNS(RoomHistoryStartupStatus.SCHEMA_MISMATCH),
    KEYS(RoomHistoryStartupStatus.SCHEMA_MISMATCH), CHECKS(RoomHistoryStartupStatus.SCHEMA_MISMATCH),
    FUNCTIONS(RoomHistoryStartupStatus.FUNCTION_MISMATCH), INTERNAL_FK_TRIGGERS(RoomHistoryStartupStatus.TRIGGER_MISMATCH), TRIGGERS(RoomHistoryStartupStatus.TRIGGER_MISMATCH),
    COLUMN_ACL(RoomHistoryStartupStatus.ACL_MISMATCH), OWNER_SOURCE_ACL(RoomHistoryStartupStatus.ACL_MISMATCH), FUNCTION_ACL(RoomHistoryStartupStatus.ACL_MISMATCH),
    SEQUENCE(RoomHistoryStartupStatus.OWNER_MISMATCH), SCHEMA_ACL(RoomHistoryStartupStatus.ACL_MISMATCH),
    ROLES(RoomHistoryStartupStatus.RUNTIME_IDENTITY_MISMATCH), MEMBERSHIPS(RoomHistoryStartupStatus.RUNTIME_IDENTITY_MISMATCH)
}

class RoomHistoryWriterStartupGuard internal constructor(private val acquire: () -> Connection) {
    constructor(configuration: PostgresConfiguration): this({ DriverManager.getConnection(configuration.url,configuration.user,configuration.password) })

    fun verify(manifest: RoomHistoryStartupManifest?): RoomHistoryStartupStatus = verifyInternal(manifest,false)
    internal fun verifyQualification(manifest: RoomHistoryStartupManifest?): RoomHistoryStartupStatus = verifyInternal(manifest,true)
    private fun verifyInternal(manifest: RoomHistoryStartupManifest?, qualification: Boolean): RoomHistoryStartupStatus {
        if (manifest == null || !qualification && (manifest.qualificationOnly || manifest.historicalMigration == null ||
            manifest.historicalMigration !in manifest.migrations || (manifest.historicalMigration.version.toIntOrNull() ?: 0) <= 43)) return RoomHistoryStartupStatus.NOT_CONFIGURED
        return try { acquire().use { c ->
            c.autoCommit=false;c.transactionIsolation=Connection.TRANSACTION_REPEATABLE_READ;c.isReadOnly=true
            try {
                c.createStatement().use { it.execute("SET LOCAL search_path=pg_catalog,public,pg_temp") }
                if (rows(c,"SELECT current_setting('server_version_num')::int BETWEEN 180000 AND 189999").single().single() != "t") return@use RoomHistoryStartupStatus.SCHEMA_MISMATCH
                val identity=rows(c,"SELECT session_user::text,current_user::text")
                if(identity != listOf(listOf(manifest.runtimeIdentity,manifest.runtimeIdentity))) return@use RoomHistoryStartupStatus.RUNTIME_IDENTITY_MISMATCH
                val history=rows(c,"SELECT version,type,script,checksum::text,success::text,description FROM public.flyway_schema_history ORDER BY installed_rank")
                val expected=manifest.migrations.map { listOf(it.version,it.type,it.script,it.checksum.toString(),"true",it.description) }
                if(history!=expected) return@use RoomHistoryStartupStatus.MIGRATION_HISTORY_MISMATCH
                for(section in RoomHistoryCatalogSection.entries) {
                    if(observe(c,section)!=manifest.catalog.getValue(section)) return@use section.failure
                }
                c.commit();RoomHistoryStartupStatus.READY
            } finally { c.rollback() }
        } } catch (_: Exception) { RoomHistoryStartupStatus.UNAVAILABLE }
    }

    internal companion object {
        private val historyTables="'marketplace_sales_intelligence_revision','marketplace_sales_intelligence_revision_observation','marketplace_sales_intelligence_revision_correction','marketplace_sales_intelligence_revision_reason','marketplace_sales_intelligence_revision_coverage','marketplace_sales_intelligence_revision_publication','marketplace_sales_intelligence_projection'"
        private val sources="'marketplace_economic_evidence_subject','marketplace_economic_evidence_update','marketplace_economic_evidence_identifier','marketplace_economic_evidence_fact','marketplace_economic_evidence_collection_attempt','marketplace_economic_evidence_correction','marketplace_economic_evidence_projection_checkpoint','integration_organization','flyway_schema_history'"
        private val functions="'reject_marketplace_sales_history_mutation','reject_marketplace_sales_sealed_detail','validate_marketplace_sales_publication_insert','publish_marketplace_sales_revision','validate_marketplace_sales_revision_boundary','check_marketplace_sales_revision_boundary'"
        private fun rows(c: Connection,sql: String): List<List<String>> = c.createStatement().use { q ->q.executeQuery(sql).use { r ->buildList { while(r.next()) add((1..r.metaData.columnCount).map { r.getString(it) ?: "<NULL>" }) } } }
        private fun sha(s: String): String = MessageDigest.getInstance("SHA-256").digest(s.replace("\r\n","\n").toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it.toInt() and 255) }
        fun observe(c: Connection,section: RoomHistoryCatalogSection): List<List<String>> = when(section) {
            RoomHistoryCatalogSection.TABLES -> rows(c,"SELECT c.relname,c.relkind::text,r.rolname,c.relrowsecurity::text,c.relforcerowsecurity::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='public' AND c.relname IN ($historyTables) ORDER BY c.relname")
            RoomHistoryCatalogSection.COLUMNS -> rows(c,"SELECT c.relname,a.attname,format_type(a.atttypid,a.atttypmod),a.attnotnull::text,a.attidentity::text,coalesce(pg_get_expr(d.adbin,d.adrelid),'') FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname IN ($historyTables) AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
            RoomHistoryCatalogSection.KEYS -> rows(c,"SELECT c.relname,k.conname,k.contype::text,k.convalidated::text,k.condeferrable::text,k.condeferred::text,pg_get_constraintdef(k.oid) FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname IN ($historyTables) AND k.contype IN ('p','u','f') ORDER BY c.relname,k.conname")
            RoomHistoryCatalogSection.CHECKS -> rows(c,"SELECT c.relname,k.conname,pg_get_constraintdef(k.oid),k.convalidated::text FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname IN ($historyTables) AND k.contype='c' ORDER BY c.relname,k.conname")
            RoomHistoryCatalogSection.FUNCTIONS -> rows(c,"SELECT p.proname,pg_get_function_identity_arguments(p.oid),r.rolname,l.lanname,p.prosecdef::text,p.provolatile::text,p.proisstrict::text,coalesce(array_to_string(p.proconfig,'|'),''),pg_get_function_result(p.oid),p.prokind::text,p.pronargdefaults::text,p.provariadic::text,p.proparallel::text,pg_get_function_arguments(p.oid),p.prosrc FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_roles r ON r.oid=p.proowner JOIN pg_language l ON l.oid=p.prolang WHERE n.nspname='public' AND (p.proname IN ($functions) OR p.proname LIKE '%marketplace_sales_%') ORDER BY p.proname,pg_get_function_identity_arguments(p.oid)").map { it.dropLast(1)+sha(it.last()) }
            RoomHistoryCatalogSection.TRIGGERS -> rows(c,"SELECT c.relname,t.tgname,p.proname,t.tgtype::text,t.tgenabled::text,t.tgdeferrable::text,t.tginitdeferred::text,p.pronamespace::regnamespace::text,pg_get_triggerdef(t.oid) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_proc p ON p.oid=t.tgfoid WHERE n.nspname='public' AND c.relname IN ($historyTables) AND NOT t.tgisinternal ORDER BY c.relname,t.tgname")
            RoomHistoryCatalogSection.INTERNAL_FK_TRIGGERS -> rows(c,"SELECT c.relname,k.conname,p.proname,t.tgtype::text,t.tgenabled::text,t.tgdeferrable::text,t.tginitdeferred::text,p.pronamespace::regnamespace::text FROM pg_trigger t JOIN pg_constraint k ON k.oid=t.tgconstraint JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_class child ON child.oid=k.conrelid JOIN pg_namespace n ON n.oid=child.relnamespace JOIN pg_proc p ON p.oid=t.tgfoid WHERE n.nspname='public' AND child.relname IN ($historyTables) AND k.contype='f' AND t.tgisinternal ORDER BY c.relname,k.conname,p.proname,t.tgtype")
            RoomHistoryCatalogSection.COLUMN_ACL -> rows(c,"SELECT c.relname,a.attname,has_column_privilege('flooow_room_history_runtime',c.oid,a.attnum,'SELECT')::text,has_column_privilege('flooow_room_history_runtime',c.oid,a.attnum,'INSERT')::text,has_column_privilege('flooow_room_history_runtime',c.oid,a.attnum,'UPDATE')::text,has_column_privilege('flooow_room_history_runtime',c.oid,a.attnum,'REFERENCES')::text,has_table_privilege('flooow_room_history_runtime',c.oid,'DELETE')::text,has_table_privilege('flooow_room_history_runtime',c.oid,'TRUNCATE')::text,has_table_privilege('flooow_room_history_runtime',c.oid,'TRIGGER')::text,(SELECT count(*)::text FROM aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) x WHERE x.grantee=0 OR x.grantee=(SELECT oid FROM pg_roles WHERE rolname='flooow_room_history_runtime') AND x.is_grantable OR c.relname IN ($historyTables) AND x.grantee NOT IN (c.relowner,(SELECT oid FROM pg_roles WHERE rolname='flooow_room_history_runtime'))),(SELECT count(*)::text FROM aclexplode(a.attacl) x WHERE x.grantee=0 OR x.is_grantable OR c.relname IN ($historyTables) AND x.grantee NOT IN (c.relowner,(SELECT oid FROM pg_roles WHERE rolname='flooow_room_history_runtime'))) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname IN ($historyTables,$sources) AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
            RoomHistoryCatalogSection.OWNER_SOURCE_ACL -> rows(c,"SELECT c.relname,a.attname,has_column_privilege('flooow_room_history_owner',c.oid,a.attnum,'SELECT')::text,has_column_privilege('flooow_room_history_owner',c.oid,a.attnum,'INSERT')::text,has_column_privilege('flooow_room_history_owner',c.oid,a.attnum,'UPDATE')::text,has_column_privilege('flooow_room_history_owner',c.oid,a.attnum,'REFERENCES')::text FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname IN ('marketplace_economic_evidence_subject','marketplace_economic_evidence_update','marketplace_economic_evidence_identifier','marketplace_economic_evidence_fact','marketplace_economic_evidence_collection_attempt','marketplace_economic_evidence_correction') AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
            RoomHistoryCatalogSection.FUNCTION_ACL -> rows(c,"SELECT p.proname,pg_get_function_identity_arguments(p.oid),has_function_privilege('flooow_room_history_runtime',p.oid,'EXECUTE')::text,(SELECT count(*)::text FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) x WHERE x.grantee NOT IN (p.proowner,(SELECT oid FROM pg_roles WHERE rolname='flooow_room_history_runtime')) OR x.grantee=(SELECT oid FROM pg_roles WHERE rolname='flooow_room_history_runtime') AND x.is_grantable) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND (p.proname IN ($functions) OR p.proname LIKE '%marketplace_sales_%') ORDER BY p.proname,pg_get_function_identity_arguments(p.oid)")
            RoomHistoryCatalogSection.SEQUENCE -> rows(c,"SELECT c.relname,r.rolname,s.seqmin::text,s.seqmax::text,s.seqincrement::text,s.seqcycle::text,has_sequence_privilege('flooow_room_history_runtime',c.oid,'USAGE')::text,has_sequence_privilege('flooow_room_history_runtime',c.oid,'SELECT')::text,has_sequence_privilege('flooow_room_history_runtime',c.oid,'UPDATE')::text FROM pg_sequence s JOIN pg_class c ON c.oid=s.seqrelid JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_roles r ON r.oid=c.relowner WHERE n.nspname='public' AND c.relname='marketplace_sales_intelligence_revision_projection_revision_seq'")
            RoomHistoryCatalogSection.SCHEMA_ACL -> rows(c,"SELECT n.nspname,has_schema_privilege('flooow_room_history_runtime',n.oid,'USAGE')::text,has_schema_privilege('flooow_room_history_runtime',n.oid,'CREATE')::text,(SELECT count(*)::text FROM aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) x WHERE x.privilege_type='CREATE' AND x.grantee NOT IN (n.nspowner,(SELECT oid FROM pg_roles WHERE rolname='postgres'))),n.nspowner::regrole::text,(SELECT datdba::regrole::text FROM pg_database WHERE datname=current_database()),has_database_privilege('flooow_room_history_runtime',current_database(),'CREATE')::text,has_schema_privilege('flooow_room_history_owner',n.oid,'USAGE')::text,has_schema_privilege('flooow_room_history_owner',n.oid,'CREATE')::text FROM pg_namespace n WHERE n.nspname='public'")
            RoomHistoryCatalogSection.ROLES -> rows(c,"SELECT rolname,rolcanlogin::text,rolinherit::text,rolsuper::text,rolcreatedb::text,rolcreaterole::text,rolreplication::text,rolbypassrls::text FROM pg_roles WHERE rolname IN ('flooow_room_history_owner','flooow_room_history_runtime') ORDER BY rolname")
            RoomHistoryCatalogSection.MEMBERSHIPS -> rows(c,"SELECT r.rolname,m.rolname FROM pg_auth_members a JOIN pg_roles r ON r.oid=a.roleid JOIN pg_roles m ON m.oid=a.member WHERE r.rolname IN ('flooow_room_history_owner','flooow_room_history_runtime') OR m.rolname IN ('flooow_room_history_owner','flooow_room_history_runtime') ORDER BY r.rolname,m.rolname")
        }
    }
}

sealed interface RoomHistoryWriterComposition {
    data class Blocked(val readiness: RoomHistoryStartupStatus): RoomHistoryWriterComposition
    class Ready internal constructor(val processor: MarketplaceSalesIntelligenceProjectionProcessor): RoomHistoryWriterComposition
}

/** Explicit matching-release factory; no flag, launcher, HTTP route or normal startup calls it. */
class RoomHistoryWriterCompositionFactory(private val configuration: PostgresConfiguration) {
    internal fun createQualification(manifest: RoomHistoryStartupManifest, evidence: MarketplaceIndependentEconomicEvidenceRepository,
        feed: MarketplaceEconomicEvidenceChangeFeed, clock: Clock = Clock.systemUTC()): RoomHistoryWriterComposition {
        val status=RoomHistoryWriterStartupGuard(configuration).verifyQualification(manifest)
        if(status!=RoomHistoryStartupStatus.READY) return RoomHistoryWriterComposition.Blocked(status)
        return RoomHistoryWriterComposition.Ready(MarketplaceSalesIntelligenceProjectionProcessor.historical(evidence,feed,PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration),clock))
    }
    fun create(manifest: RoomHistoryStartupManifest?, evidence: MarketplaceIndependentEconomicEvidenceRepository,
        feed: MarketplaceEconomicEvidenceChangeFeed, clock: Clock = Clock.systemUTC()): RoomHistoryWriterComposition {
        val status=RoomHistoryWriterStartupGuard(configuration).verify(manifest)
        if(status!=RoomHistoryStartupStatus.READY) return RoomHistoryWriterComposition.Blocked(status)
        return RoomHistoryWriterComposition.Ready(MarketplaceSalesIntelligenceProjectionProcessor.historical(evidence,feed,PostgresMarketplaceSalesIntelligenceLineagePublicationRepository(configuration),clock))
    }
}
