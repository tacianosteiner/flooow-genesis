package io.flooow.marketplace.persistence.postgres

import io.flooow.marketplace.operations.economics.*
import io.flooow.marketplace.operations.economics.evidence.*
import io.flooow.marketplace.operations.economics.sales.*
import io.flooow.organization.OrganizationId
import java.sql.Connection
import java.sql.DriverManager
import java.sql.Timestamp
import java.time.Instant
import java.util.UUID
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject

class HistoricalEconomicProjectionRevision internal constructor(
    val revisionId: Long, val snapshot: ConsumedEconomicEvidenceSnapshot, val publishedAt: Instant
) { init { require(revisionId > 0) }; override fun toString(): String = "[REDACTED]" }

sealed interface EconomicLineageReadResult {
    data class Found(val revision: HistoricalEconomicProjectionRevision): EconomicLineageReadResult { override fun toString(): String = "[REDACTED]" }
    data object NotFound: EconomicLineageReadResult
    data object IntegrityFailure: EconomicLineageReadResult
}
sealed interface EconomicLineagePublicationResult {
    data class Published(val revisionId: Long): EconomicLineagePublicationResult { override fun toString(): String = "[REDACTED]" }
    data class IdenticalPublished(val revisionId: Long): EconomicLineagePublicationResult { override fun toString(): String = "[REDACTED]" }
    data class Superseded(val currentRevisionId: Long?): EconomicLineagePublicationResult { override fun toString(): String = "[REDACTED]" }
    data object CommitOutcomeUnknown: EconomicLineagePublicationResult
    data object IntegrityFailure: EconomicLineagePublicationResult
}
internal enum class EconomicLineageWriteStage {
    AFTER_LOCK, AFTER_HEADER, DURING_FIRST_MEMBER, DURING_LATER_MEMBER, DURING_CORRECTION_EDGE,
    DURING_NORMALIZED_OUTCOME, BEFORE_CURRENT_PUBLICATION, DURING_CURRENT_PUBLICATION, AFTER_CURRENT_BEFORE_COMMIT
}

/** Uncomposed until an independently authorized production historical schema rollout. */
class PostgresMarketplaceSalesIntelligenceLineagePublicationRepository internal constructor(
    private val configuration: PostgresConfiguration,
    private val hook: (EconomicLineageWriteStage, Connection) -> Unit,
    private val acquire: () -> Connection
) {
    constructor(configuration: PostgresConfiguration): this(configuration, { _, _ -> },
        { DriverManager.getConnection(configuration.url,configuration.user,configuration.password) })

    fun publish(snapshot: ConsumedEconomicEvidenceSnapshot, record: MarketplaceSalesIntelligenceProjectionRecord): EconomicLineagePublicationResult {
        var commitAttempted = false
        return try {
        val scope = snapshot.subject
        require(record.organizationId == scope.organizationId && record.marketplaceOrderId == scope.orderId)
        require(record.sourceEvidenceVersion == snapshot.readEvidenceVersion && record.lastAppliedChangeSequence == snapshot.triggerChangeSequence && record.projectedAt == snapshot.projectedAt)
        val state = MarketplaceSalesIntelligenceStateCodecV1.encodeFrozen(snapshot.outcome)
        require(state == MarketplaceSalesIntelligenceStateCodecV1.encodeFrozen(record.state))
        val bytes = snapshot.canonicalManifestForPersistence()
        acquire().use { c ->
            c.autoCommit = false; c.transactionIsolation = Connection.TRANSACTION_READ_COMMITTED
            c.createStatement().use { it.execute("SET LOCAL search_path=pg_catalog,public,pg_temp") }
            try {
                c.prepareStatement("SELECT currency,marketplace_key,external_order_id FROM marketplace_economic_evidence_subject WHERE organization_id=? AND marketplace_order_id=? FOR NO KEY UPDATE").use { s ->
                    bind(s, scope.organizationId.value, scope.orderId.value)
                    s.executeQuery().use { r -> check(r.next()); check(r.getString(1) == scope.currency.code && r.getString(2) == scope.marketplace.value && r.getString(3) == scope.externalOrderId.value) }
                }
                hook(EconomicLineageWriteStage.AFTER_LOCK,c)
                val triggerVersion = c.prepareStatement("SELECT evidence_version FROM marketplace_economic_evidence_update WHERE organization_id=? AND marketplace_order_id=? AND change_sequence=?").use { s ->
                    bind(s,scope.organizationId.value,scope.orderId.value,snapshot.triggerChangeSequence.valueForPersistence())
                    s.executeQuery().use { r -> check(r.next()); r.getLong(1) }
                }
                check(triggerVersion <= snapshot.readEvidenceVersion.valueForPersistence())
                val duplicate = readRevision(c,scope.organizationId,scope.orderId,"h.trigger_change_sequence",snapshot.triggerChangeSequence.valueForPersistence())
                if (duplicate != null) {
                    check(duplicate.snapshot.canonicalManifestForPersistence().contentEquals(bytes))
                    check(duplicate.snapshot.manifestDigest == snapshot.manifestDigest)
                    c.commit(); return EconomicLineagePublicationResult.IdenticalPublished(duplicate.revisionId)
                }
                val current = c.prepareStatement("SELECT last_applied_change_sequence,source_evidence_version,current_revision_id FROM marketplace_sales_intelligence_projection WHERE organization_id=? AND marketplace_order_id=?").use { s ->
                    bind(s,scope.organizationId.value,scope.orderId.value)
                    s.executeQuery().use { r -> if(r.next()) Triple(r.getLong(1),r.getLong(2),r.getObject(3)?.let { check(it is Long); it }) else null }
                }
                if (current != null && current.first >= snapshot.triggerChangeSequence.valueForPersistence()) {
                    check(current.second >= triggerVersion)
                    if(current.third == null) verifyLegacyCurrent(c,scope.organizationId,scope.orderId)
                    else { val id=checkNotNull(current.third); checkNotNull(readRevision(c,scope.organizationId,scope.orderId,"h.projection_revision",id)); verifyCurrent(c,scope.organizationId,scope.orderId,id) }
                    c.commit(); return EconomicLineagePublicationResult.Superseded(current.third)
                }
                check(current == null || snapshot.readEvidenceVersion.valueForPersistence() >= current.second)
                val id = c.prepareStatement("INSERT INTO marketplace_sales_intelligence_revision (organization_id,marketplace_order_id,trigger_change_sequence,read_evidence_version,marketplace_key,external_order_id,currency,projected_at,assembly_policy_version,calculation_policy_version,state_kind,calculation_kind,coverage_count,state_payload_format_version,state_payload,manifest_format_version,manifest_digest,manifest_bytes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,?::jsonb,1,?,?) RETURNING projection_revision").use { s ->
                    bind(s,scope.organizationId.value,scope.orderId.value,snapshot.triggerChangeSequence.valueForPersistence(),snapshot.readEvidenceVersion.valueForPersistence(),
                        scope.marketplace.value,scope.externalOrderId.value,scope.currency.code,Timestamp.from(snapshot.projectedAt),snapshot.outcome.assemblyPolicyVersion.value,
                        state.calculationPolicyVersion,state.stateKind,state.calculationKind,snapshot.componentCoverage.size,state.payload,snapshot.manifestDigest,bytes)
                    s.executeQuery().use { r -> check(r.next()); r.getLong(1) }
                }
                hook(EconomicLineageWriteStage.AFTER_HEADER,c)
                snapshot.members.forEachIndexed { index, member ->
                    val o = member.observation
                    execute(c,"INSERT INTO marketplace_sales_intelligence_revision_observation (organization_id,marketplace_order_id,projection_revision,read_evidence_version,observation_id,evidence_version,identifier_kind,context_role,family,recorded_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        scope.organizationId.value,scope.orderId.value,id,snapshot.readEvidenceVersion.valueForPersistence(),o.observationId.valueForPersistence(),o.evidenceVersion.valueForPersistence(),o.identifierKind.name,member.contextRole.name,o.family?.name,Timestamp.from(o.recordedAt))
                    hook(if(index==0) EconomicLineageWriteStage.DURING_FIRST_MEMBER else EconomicLineageWriteStage.DURING_LATER_MEMBER,c)
                }
                snapshot.members.filter { it.observation.identifierKind == MarketplaceEconomicObservationIdentifierKind.CORRECTION }.forEach { member ->
                    val o=member.observation
                    val old = snapshot.members.single { it.observation.observationId == o.supersedesObservationId }.observation
                    execute(c,"INSERT INTO marketplace_sales_intelligence_revision_correction (organization_id,marketplace_order_id,projection_revision,correction_id,evidence_version,superseded_observation_id,superseded_evidence_version,replacement_observation_id) VALUES (?,?,?,?,?,?,?,?)",
                        scope.organizationId.value,scope.orderId.value,id,o.observationId.valueForPersistence(),o.evidenceVersion.valueForPersistence(),old.observationId.valueForPersistence(),old.evidenceVersion.valueForPersistence(),checkNotNull(o.replacementObservationId).valueForPersistence())
                    hook(EconomicLineageWriteStage.DURING_CORRECTION_EDGE,c)
                }
                (snapshot.outcome as? MarketplaceSalesIntelligenceState.Unresolved)?.reasons?.forEach { reason ->
                    execute(c,"INSERT INTO marketplace_sales_intelligence_revision_reason VALUES (?,?,?,?)",scope.organizationId.value,scope.orderId.value,id,reason.name)
                }
                snapshot.componentCoverage.forEach { (type, coverage) ->
                    execute(c,"INSERT INTO marketplace_sales_intelligence_revision_coverage VALUES (?,?,?,?,?)",scope.organizationId.value,scope.orderId.value,id,type.name,coverage.name)
                }
                hook(EconomicLineageWriteStage.DURING_NORMALIZED_OUTCOME,c)
                hook(EconomicLineageWriteStage.BEFORE_CURRENT_PUBLICATION,c)
                hook(EconomicLineageWriteStage.DURING_CURRENT_PUBLICATION,c)
                execute(c,"INSERT INTO marketplace_sales_intelligence_projection (organization_id,marketplace_order_id,source_evidence_version,state_kind,assembly_policy_version,calculation_policy_version,calculation_kind,state_payload,last_applied_change_sequence,projected_at,current_revision_id) VALUES (?,?,?,?,?,?,?,?::jsonb,?,?,?) ON CONFLICT (organization_id,marketplace_order_id) DO UPDATE SET source_evidence_version=EXCLUDED.source_evidence_version,state_kind=EXCLUDED.state_kind,assembly_policy_version=EXCLUDED.assembly_policy_version,calculation_policy_version=EXCLUDED.calculation_policy_version,calculation_kind=EXCLUDED.calculation_kind,state_payload=EXCLUDED.state_payload,last_applied_change_sequence=EXCLUDED.last_applied_change_sequence,projected_at=EXCLUDED.projected_at,current_revision_id=EXCLUDED.current_revision_id WHERE EXCLUDED.last_applied_change_sequence>marketplace_sales_intelligence_projection.last_applied_change_sequence AND EXCLUDED.source_evidence_version>=marketplace_sales_intelligence_projection.source_evidence_version",
                    scope.organizationId.value,scope.orderId.value,snapshot.readEvidenceVersion.valueForPersistence(),state.stateKind,snapshot.outcome.assemblyPolicyVersion.value,state.calculationPolicyVersion,state.calculationKind,state.payload,snapshot.triggerChangeSequence.valueForPersistence(),Timestamp.from(snapshot.projectedAt),id)
                hook(EconomicLineageWriteStage.AFTER_CURRENT_BEFORE_COMMIT,c)
                c.createStatement().use { it.execute("SET CONSTRAINTS ALL IMMEDIATE") }
                val stored = checkNotNull(readRevision(c,scope.organizationId,scope.orderId,"h.projection_revision",id))
                check(stored.snapshot.canonicalManifestForPersistence().contentEquals(bytes))
                verifyCurrent(c,scope.organizationId,scope.orderId,id)
                commitAttempted = true
                c.commit(); EconomicLineagePublicationResult.Published(id)
            } catch(e: Exception) { try { c.rollback() } catch(rollback: Exception) { e.addSuppressed(rollback) }; throw e }
        }
    } catch (_: Exception) { if(commitAttempted) EconomicLineagePublicationResult.CommitOutcomeUnknown else EconomicLineagePublicationResult.IntegrityFailure }
    }

    fun findHistoricalRevision(org: OrganizationId, order: MarketplaceOrderId, revision: Long): EconomicLineageReadResult = read(org,order,"h.projection_revision",revision)
    fun findPublishedRevisionForTrigger(org: OrganizationId, order: MarketplaceOrderId, trigger: ChangeSequenceCheckpoint): EconomicLineageReadResult = read(org,order,"h.trigger_change_sequence",trigger.valueForPersistence())
    private fun read(org: OrganizationId, order: MarketplaceOrderId, key: String, value: Long): EconomicLineageReadResult = try {
        require(value > 0)
        acquire().use { c ->
            c.autoCommit=false; c.transactionIsolation=Connection.TRANSACTION_REPEATABLE_READ
            c.createStatement().use { it.execute("SET LOCAL search_path=pg_catalog,public,pg_temp") }
            try { val revision=readRevision(c,org,order,key,value); c.commit(); if(revision==null) EconomicLineageReadResult.NotFound else EconomicLineageReadResult.Found(revision) }
            catch(e: Exception) { try { c.rollback() } catch(rollback: Exception) { e.addSuppressed(rollback) }; throw e }
        }
    } catch (_: Exception) { EconomicLineageReadResult.IntegrityFailure }

    private fun readRevision(c: Connection, org: OrganizationId, order: MarketplaceOrderId, key: String, value: Long): HistoricalEconomicProjectionRevision? {
        check(key == "h.projection_revision" || key == "h.trigger_change_sequence")
        return c.prepareStatement("SELECT h.*,p.published_at FROM marketplace_sales_intelligence_revision h LEFT JOIN marketplace_sales_intelligence_revision_publication p USING (organization_id,marketplace_order_id,projection_revision) WHERE h.organization_id=? AND h.marketplace_order_id=? AND $key=?").use { s ->
            bind(s,org.value,order.value,value)
            s.executeQuery().use { r ->
                if(!r.next()) return null
                val id=r.getLong("projection_revision"); val publishedAt=checkNotNull(r.getTimestamp("published_at")).toInstant()
                check(r.getInt("manifest_format_version")==1 && r.getInt("state_payload_format_version")==MarketplaceSalesIntelligenceStateCodecV1.FORMAT_VERSION)
                val subject=MarketplaceEconomicEvidenceSubject(org,order,MarketplaceKey(r.getString("marketplace_key")),MarketplaceExternalOrderId(r.getString("external_order_id")),MarketplaceCurrency(r.getString("currency")))
                val state=MarketplaceSalesIntelligenceStateCodecV1.decodeFrozen(org,order,MarketplaceEconomicTruthAssemblyPolicyVersion(r.getString("assembly_policy_version")),r.getString("state_kind"),r.getString("calculation_policy_version"),r.getString("calculation_kind"),Json.parseToJsonElement(r.getString("state_payload")).jsonObject)
                val readVersion=MarketplaceEconomicEvidenceVersion(r.getLong("read_evidence_version")); val trigger=ChangeSequenceCheckpoint(r.getLong("trigger_change_sequence")); val projectedAt=r.getTimestamp("projected_at").toInstant()
                val storedBytes=r.getBytes("manifest_bytes"); val digest=r.getString("manifest_digest"); val coverageCount=r.getInt("coverage_count")
                c.prepareStatement("SELECT validate_marketplace_sales_revision_boundary(?,?,?)").use { q -> bind(q,org.value,order.value,id); q.executeQuery().use { check(it.next()) } }
                val members=c.prepareStatement("SELECT o.*,e.superseded_observation_id,e.replacement_observation_id FROM marketplace_sales_intelligence_revision_observation o LEFT JOIN marketplace_sales_intelligence_revision_correction e ON e.organization_id=o.organization_id AND e.marketplace_order_id=o.marketplace_order_id AND e.projection_revision=o.projection_revision AND e.correction_id=o.observation_id WHERE o.organization_id=? AND o.marketplace_order_id=? AND o.projection_revision=?").use { q ->
                    bind(q,org.value,order.value,id); q.executeQuery().use { rows -> buildList {
                        while(rows.next()) add(ConsumedEconomicEvidenceMember(VersionedEconomicEvidenceObservation(
                            observationId(rows.getObject("observation_id",UUID::class.java)),MarketplaceEconomicEvidenceVersion(rows.getLong("evidence_version")),MarketplaceEconomicObservationIdentifierKind.valueOf(rows.getString("identifier_kind")),rows.getString("family")?.let { MarketplaceEconomicEvidenceFamily.valueOf(it) },rows.getTimestamp("recorded_at").toInstant(),
                            rows.getObject("superseded_observation_id",UUID::class.java)?.let(::observationId),rows.getObject("replacement_observation_id",UUID::class.java)?.let(::observationId)),ConsumedEconomicEvidenceContextRole.valueOf(rows.getString("context_role"))))
                    } }
                }
                val coverage=c.prepareStatement("SELECT component_type,coverage_state FROM marketplace_sales_intelligence_revision_coverage WHERE organization_id=? AND marketplace_order_id=? AND projection_revision=?").use { q ->
                    bind(q,org.value,order.value,id); q.executeQuery().use { rows -> buildMap { while(rows.next()) check(put(EconomicComponentType.valueOf(rows.getString(1)),EconomicComponentCoverage.valueOf(rows.getString(2)))==null) } }
                }
                check(coverage.size==coverageCount)
                val snapshot=ConsumedEconomicEvidenceSnapshot.rehydratePersisted(subject,readVersion,trigger,projectedAt,state,members,coverage)
                check(snapshot.canonicalManifestForPersistence().contentEquals(storedBytes) && snapshot.manifestDigest==digest)
                HistoricalEconomicProjectionRevision(id,snapshot,publishedAt)
            }
        }
    }
    private fun verifyLegacyCurrent(c: Connection, org: OrganizationId, order: MarketplaceOrderId) {
        c.prepareStatement("SELECT p.* FROM marketplace_sales_intelligence_projection p JOIN marketplace_economic_evidence_update boundary ON boundary.organization_id=p.organization_id AND boundary.marketplace_order_id=p.marketplace_order_id AND boundary.evidence_version=p.source_evidence_version JOIN marketplace_economic_evidence_update trigger_update ON trigger_update.organization_id=p.organization_id AND trigger_update.marketplace_order_id=p.marketplace_order_id AND trigger_update.change_sequence=p.last_applied_change_sequence AND trigger_update.evidence_version<=boundary.evidence_version WHERE p.organization_id=? AND p.marketplace_order_id=? AND p.current_revision_id IS NULL").use { q ->
            bind(q,org.value,order.value)
            q.executeQuery().use { r ->
                check(r.next())
                MarketplaceSalesIntelligenceStateCodecV1.decode(org,order,MarketplaceEconomicTruthAssemblyPolicyVersion(r.getString("assembly_policy_version")),r.getString("state_kind"),r.getString("calculation_policy_version"),r.getString("calculation_kind"),Json.parseToJsonElement(r.getString("state_payload")).jsonObject)
            }
        }
    }
    private fun verifyCurrent(c: Connection, org: OrganizationId, order: MarketplaceOrderId, id: Long) {
        c.prepareStatement("SELECT p.current_revision_id=h.projection_revision AND p.source_evidence_version=h.read_evidence_version AND p.last_applied_change_sequence=h.trigger_change_sequence AND p.projected_at=h.projected_at AND p.assembly_policy_version=h.assembly_policy_version AND p.calculation_policy_version IS NOT DISTINCT FROM h.calculation_policy_version AND p.state_kind=h.state_kind AND p.calculation_kind IS NOT DISTINCT FROM h.calculation_kind AND p.state_payload=h.state_payload FROM marketplace_sales_intelligence_projection p JOIN marketplace_sales_intelligence_revision h ON h.organization_id=p.organization_id AND h.marketplace_order_id=p.marketplace_order_id AND h.projection_revision=p.current_revision_id WHERE p.organization_id=? AND p.marketplace_order_id=? AND p.current_revision_id=?").use { q -> bind(q,org.value,order.value,id); q.executeQuery().use { r -> check(r.next() && r.getBoolean(1)) } }
    }
    private fun observationId(uuid: UUID) = MarketplaceEconomicEvidenceObservationId.parse(uuid.toString())
    private fun execute(c: Connection, sql: String, vararg values: Any?) { c.prepareStatement(sql).use { s -> bind(s,*values); check(s.executeUpdate()==1) } }
    private fun bind(s: java.sql.PreparedStatement, vararg values: Any?) { values.forEachIndexed { index,value -> s.setObject(index+1,value) } }
}
