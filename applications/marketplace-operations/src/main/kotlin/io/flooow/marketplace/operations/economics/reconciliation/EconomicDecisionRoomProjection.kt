package io.flooow.marketplace.operations.economics.reconciliation

import io.flooow.marketplace.operations.economics.MarketplaceCurrency
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.MarketplaceOrderId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerEntryId
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.marketplace.operations.economics.ledger.FinancialTraceId
import io.flooow.marketplace.operations.economics.readiness.EconomicLeakageGovernanceMapper
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityAssemblyFailureReason
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityAssemblyResult
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityAssembler
import io.flooow.marketplace.operations.economics.readiness.EconomicTruthAuthorityInputs
import io.flooow.organization.OrganizationId
import java.time.Instant
import java.util.Collections

enum class EconomicDecisionRoomProjectionStatus { READY, BLOCKED }
enum class EconomicDecisionRoomAuthorityStatus { ASSEMBLED, NOT_ASSEMBLED }
enum class EconomicDecisionRoomProjectionBlockingReason {
    RECONCILIATION_ASSESSMENT_UNAVAILABLE,
    RECONCILIATION_CONTEXT_MISMATCH,
    AUTHORITY_CONTEXT_MISMATCH,
    AUTHORITY_NOT_ASSEMBLED,
    GOVERNANCE_NOT_PERMITTED,
    LEAKAGE_UNQUANTIFIED
}
enum class EconomicDecisionRoomStageBlockingReason {
    RECONCILIATION_ASSESSMENT_UNAVAILABLE,
    RECONCILIATION_CONTEXT_MISMATCH,
    AUTHORITY_CONTEXT_MISMATCH,
    AUTHORITY_NOT_ASSEMBLED,
    GOVERNANCE_NOT_SATISFIED,
    MISSING_EXPECTED,
    MISSING_ACTUAL,
    RECONCILIATION_INCOMPLETE,
    UNSUPPORTED_STAGE
}

data class EconomicDecisionRoomAuthorityContext(
    val organizationId: OrganizationId,
    val caseId: ReconciliationCaseId,
    val marketplaceOrderId: MarketplaceOrderId,
    val financialTraceId: FinancialTraceId,
    val policyVersion: FinancialReconciliationPolicyVersion,
    val currency: MarketplaceCurrency,
    val reconciliationRevision: Long,
    val inputs: EconomicTruthAuthorityInputs
)

sealed interface EconomicDecisionRoomAuthorityRead {
    data class Available(val context: EconomicDecisionRoomAuthorityContext) : EconomicDecisionRoomAuthorityRead
    data object Unavailable : EconomicDecisionRoomAuthorityRead
    data object IntegrityFailure : EconomicDecisionRoomAuthorityRead
}

fun interface EconomicDecisionRoomAuthoritySource {
    fun read(organizationId: OrganizationId, case: DurableReconciliationCase): EconomicDecisionRoomAuthorityRead
}

data class EconomicDecisionRoomReconciliationAssessmentBinding(
    val caseId: ReconciliationCaseId,
    val reconciliationRevision: Long,
    val assessment: FinancialReconciliationAssessment
)

sealed interface EconomicDecisionRoomReconciliationAssessmentRead {
    data class Available(val binding: EconomicDecisionRoomReconciliationAssessmentBinding) : EconomicDecisionRoomReconciliationAssessmentRead
    data object Unavailable : EconomicDecisionRoomReconciliationAssessmentRead
    data object IntegrityFailure : EconomicDecisionRoomReconciliationAssessmentRead
}

fun interface EconomicDecisionRoomReconciliationAssessmentSource {
    fun read(organizationId: OrganizationId, case: DurableReconciliationCase): EconomicDecisionRoomReconciliationAssessmentRead
}

data class EconomicDecisionRoomStageProjection(
    val stage: FinancialLedgerStage,
    val expected: MarketplaceMoney?,
    val actual: MarketplaceMoney?,
    val signedVariance: MarketplaceMoney?,
    val absoluteVariance: MarketplaceMoney?,
    val interpretation: EconomicLeakageInterpretationStatus?,
    val quantifiedLeakage: MarketplaceMoney?,
    val blockingReason: EconomicDecisionRoomStageBlockingReason?,
    val expectedEntryIds: List<FinancialLedgerEntryId>,
    val actualEntryIds: List<FinancialLedgerEntryId>
)

class EconomicDecisionRoomReconciliationProjection internal constructor(
    val caseId: ReconciliationCaseId,
    val marketplaceOrderId: MarketplaceOrderId,
    val financialTraceId: FinancialTraceId,
    val policyVersion: FinancialReconciliationPolicyVersion,
    val currency: MarketplaceCurrency,
    val reconciliationCaseStatus: ReconciliationCaseStatus,
    val reconciliationRevision: Long,
    val lastObservedAt: Instant,
    val projectionStatus: EconomicDecisionRoomProjectionStatus,
    val authorityStatus: EconomicDecisionRoomAuthorityStatus,
    authorityBlockingReasons: Set<EconomicTruthAuthorityAssemblyFailureReason>,
    val governancePermitted: Boolean,
    governanceBlockingReasons: Set<EconomicLeakageGovernanceBlockingReason>,
    projectionBlockingReasons: Set<EconomicDecisionRoomProjectionBlockingReason>,
    val totalQuantifiedLeakage: MarketplaceMoney?,
    stages: List<EconomicDecisionRoomStageProjection>,
    evidenceReferences: Set<String>
) {
    val authorityBlockingReasons = Collections.unmodifiableSet(authorityBlockingReasons.toSet())
    val governanceBlockingReasons = Collections.unmodifiableSet(governanceBlockingReasons.toSet())
    val projectionBlockingReasons = Collections.unmodifiableSet(projectionBlockingReasons.toSet())
    val stages = Collections.unmodifiableList(stages.toList())
    val evidenceReferences = Collections.unmodifiableSet(evidenceReferences.toSet())
    override fun toString(): String = "[REDACTED]"
}

sealed interface EconomicDecisionRoomProjectionReadResult {
    data class Found(val projection: EconomicDecisionRoomReconciliationProjection) : EconomicDecisionRoomProjectionReadResult
    data class NotFound(val diagnostic: EconomicDecisionRoomNotFoundDiagnostic) : EconomicDecisionRoomProjectionReadResult
    data object IntegrityFailure : EconomicDecisionRoomProjectionReadResult
}

enum class EconomicDecisionRoomNotFoundDiagnostic {
    CASE_ABSENT,
    ORGANIZATION_SCOPE_MISMATCH
}

class EconomicDecisionRoomProjectionService(
    private val cases: DurableReconciliationCaseRepository,
    private val authorities: EconomicDecisionRoomAuthoritySource,
    private val assessments: EconomicDecisionRoomReconciliationAssessmentSource
) {
    fun read(organizationId: OrganizationId, caseId: ReconciliationCaseId): EconomicDecisionRoomProjectionReadResult {
        val case = cases.find(organizationId, caseId)
            ?: return EconomicDecisionRoomProjectionReadResult.NotFound(EconomicDecisionRoomNotFoundDiagnostic.CASE_ABSENT)
        if (case.organizationId != organizationId) {
            return EconomicDecisionRoomProjectionReadResult.NotFound(EconomicDecisionRoomNotFoundDiagnostic.ORGANIZATION_SCOPE_MISMATCH)
        }
        if (case.caseId != caseId) return EconomicDecisionRoomProjectionReadResult.IntegrityFailure

        val assessmentRead = assessments.read(organizationId, case)
        if (assessmentRead is EconomicDecisionRoomReconciliationAssessmentRead.IntegrityFailure) {
            return EconomicDecisionRoomProjectionReadResult.IntegrityFailure
        }
        val assessmentBinding = (assessmentRead as? EconomicDecisionRoomReconciliationAssessmentRead.Available)?.binding
        if (assessmentBinding != null && assessmentBinding.assessment.organizationId != organizationId) {
            return EconomicDecisionRoomProjectionReadResult.NotFound(EconomicDecisionRoomNotFoundDiagnostic.ORGANIZATION_SCOPE_MISMATCH)
        }
        val assessmentContextMatches = assessmentBinding == null || assessmentBinding.matches(case)
        val assessment = assessmentBinding?.assessment?.takeIf { assessmentContextMatches }

        val authorityRead = authorities.read(organizationId, case)
        if (authorityRead is EconomicDecisionRoomAuthorityRead.IntegrityFailure) {
            return EconomicDecisionRoomProjectionReadResult.IntegrityFailure
        }
        val authorityContext = (authorityRead as? EconomicDecisionRoomAuthorityRead.Available)?.context
        if (authorityContext != null && authorityContext.organizationId != organizationId) {
            return EconomicDecisionRoomProjectionReadResult.NotFound(EconomicDecisionRoomNotFoundDiagnostic.ORGANIZATION_SCOPE_MISMATCH)
        }
        val authorityContextMatches = authorityContext == null || authorityContext.matches(case)
        val assembly = if (assessmentContextMatches && authorityContextMatches) {
            EconomicTruthAuthorityAssembler.assemble(
                authorityContext?.inputs ?: EconomicTruthAuthorityInputs(null, null, null, null),
                assessment
            )
        } else null
        val authorityFailures = (assembly as? EconomicTruthAuthorityAssemblyResult.NotAssembled)?.reasons.orEmpty()
        val assembled = assembly as? EconomicTruthAuthorityAssemblyResult.Assembled
        val governance = assembled?.authorities?.let(EconomicLeakageGovernanceMapper::from)
        val interpretation = if (assessment != null && governance != null) {
            MarketplaceEconomicLeakageInterpretation.interpret(assessment, governance)
        } else null
        val hasUnquantifiedStage = interpretation?.lines?.any {
            it.interpretation == EconomicLeakageInterpretationStatus.UNQUANTIFIED
        } == true

        val blockers = linkedSetOf<EconomicDecisionRoomProjectionBlockingReason>()
        if (assessmentBinding == null) blockers += EconomicDecisionRoomProjectionBlockingReason.RECONCILIATION_ASSESSMENT_UNAVAILABLE
        if (!assessmentContextMatches) blockers += EconomicDecisionRoomProjectionBlockingReason.RECONCILIATION_CONTEXT_MISMATCH
        if (!authorityContextMatches) blockers += EconomicDecisionRoomProjectionBlockingReason.AUTHORITY_CONTEXT_MISMATCH
        if (assembled == null) blockers += EconomicDecisionRoomProjectionBlockingReason.AUTHORITY_NOT_ASSEMBLED
        if (governance != null && !governance.permitted) blockers += EconomicDecisionRoomProjectionBlockingReason.GOVERNANCE_NOT_PERMITTED
        if (hasUnquantifiedStage) {
            blockers += EconomicDecisionRoomProjectionBlockingReason.LEAKAGE_UNQUANTIFIED
        }

        val references = linkedSetOf<String>()
        references += "reconciliation-case:${case.caseId.value}"
        references += "financial-trace:${case.traceId.value}"
        references += "marketplace-order:${case.orderId.value}"
        references += "reconciliation-policy:${case.policyVersion.value}"
        case.evidenceEntryIds.forEach { references += "financial-ledger-entry:${it.value}" }
        governance?.evidenceReferences?.let(references::addAll)

        return EconomicDecisionRoomProjectionReadResult.Found(
            EconomicDecisionRoomReconciliationProjection(
                case.caseId, case.orderId, case.traceId, case.policyVersion, case.currency, case.status,
                case.revision, case.lastObservedAt,
                if (blockers.isEmpty()) EconomicDecisionRoomProjectionStatus.READY else EconomicDecisionRoomProjectionStatus.BLOCKED,
                if (assembled == null) EconomicDecisionRoomAuthorityStatus.NOT_ASSEMBLED else EconomicDecisionRoomAuthorityStatus.ASSEMBLED,
                authorityFailures,
                governance?.permitted == true,
                governance?.blockingReasons.orEmpty(),
                blockers,
                interpretation?.totalQuantifiedLeakage?.takeUnless { hasUnquantifiedStage },
                interpretation?.lines?.map(::interpretedStage)
                    ?: case.stages.map { durableStage(it, fallbackStageReason(assessmentBinding, assessmentContextMatches, authorityContextMatches)) },
                references
            )
        )
    }

    private fun interpretedStage(line: EconomicLeakageLine) = EconomicDecisionRoomStageProjection(
        line.stage, line.expected, line.actual, line.signedVariance, line.absoluteVariance,
        line.interpretation, line.quantifiedLeakage, line.blockingReason?.projectionReason(),
        line.expectedEntryIds, line.actualEntryIds
    )

    private fun durableStage(
        stage: ReconciliationCaseStageDifference,
        blockingReason: EconomicDecisionRoomStageBlockingReason
    ) = EconomicDecisionRoomStageProjection(
        stage.stage, stage.expected, stage.actual, stage.signedDifference, stage.absoluteDifference,
        null, null, blockingReason,
        stage.expectedEntryIds, stage.actualEntryIds
    )

    private fun fallbackStageReason(
        assessmentBinding: EconomicDecisionRoomReconciliationAssessmentBinding?,
        assessmentContextMatches: Boolean,
        authorityContextMatches: Boolean
    ): EconomicDecisionRoomStageBlockingReason = when {
        assessmentBinding == null -> EconomicDecisionRoomStageBlockingReason.RECONCILIATION_ASSESSMENT_UNAVAILABLE
        !assessmentContextMatches -> EconomicDecisionRoomStageBlockingReason.RECONCILIATION_CONTEXT_MISMATCH
        !authorityContextMatches -> EconomicDecisionRoomStageBlockingReason.AUTHORITY_CONTEXT_MISMATCH
        else -> EconomicDecisionRoomStageBlockingReason.AUTHORITY_NOT_ASSEMBLED
    }
}

private fun EconomicDecisionRoomAuthorityContext.matches(case: DurableReconciliationCase): Boolean =
    organizationId == case.organizationId && caseId == case.caseId && marketplaceOrderId == case.orderId &&
        financialTraceId == case.traceId && policyVersion == case.policyVersion && currency == case.currency &&
        reconciliationRevision == case.revision

private fun EconomicDecisionRoomReconciliationAssessmentBinding.matches(case: DurableReconciliationCase): Boolean =
    caseId == case.caseId && reconciliationRevision == case.revision &&
        assessment.organizationId == case.organizationId && assessment.orderId == case.orderId &&
        assessment.traceId == case.traceId && assessment.policyVersion == case.policyVersion &&
        assessment.currency == case.currency

private fun EconomicLeakageBlockingReason.projectionReason() = when (this) {
    EconomicLeakageBlockingReason.GOVERNANCE_NOT_SATISFIED -> EconomicDecisionRoomStageBlockingReason.GOVERNANCE_NOT_SATISFIED
    EconomicLeakageBlockingReason.MISSING_EXPECTED -> EconomicDecisionRoomStageBlockingReason.MISSING_EXPECTED
    EconomicLeakageBlockingReason.MISSING_ACTUAL -> EconomicDecisionRoomStageBlockingReason.MISSING_ACTUAL
    EconomicLeakageBlockingReason.RECONCILIATION_INCOMPLETE -> EconomicDecisionRoomStageBlockingReason.RECONCILIATION_INCOMPLETE
    EconomicLeakageBlockingReason.UNSUPPORTED_STAGE -> EconomicDecisionRoomStageBlockingReason.UNSUPPORTED_STAGE
}

object UnavailableEconomicDecisionRoomAuthoritySource : EconomicDecisionRoomAuthoritySource {
    override fun read(organizationId: OrganizationId, case: DurableReconciliationCase) = EconomicDecisionRoomAuthorityRead.Unavailable
}

object UnavailableEconomicDecisionRoomReconciliationAssessmentSource : EconomicDecisionRoomReconciliationAssessmentSource {
    override fun read(organizationId: OrganizationId, case: DurableReconciliationCase) = EconomicDecisionRoomReconciliationAssessmentRead.Unavailable
}
