package io.flooow.marketplace.operations.economics.ledger.materialization

import io.flooow.marketplace.operations.economics.EconomicComponentType
import io.flooow.marketplace.operations.economics.EconomicDirection
import io.flooow.marketplace.operations.economics.EconomicSource
import io.flooow.marketplace.operations.economics.MarketplaceMoney
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicComponentObservation
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceObservationId
import io.flooow.marketplace.operations.economics.evidence.MarketplaceEconomicEvidenceSubject
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerBasis
import io.flooow.marketplace.operations.economics.ledger.FinancialLedgerStage
import io.flooow.organization.OrganizationId
import java.time.Instant

@JvmInline
value class FinancialLedgerSourceAuthoritySemanticVersion(val value: String) {
    init { require(Regex("[a-z0-9][a-z0-9./-]{0,63}").matches(value)) { "Invalid authority semantic version" } }
    override fun toString(): String = "[REDACTED]"
}

@JvmInline
value class FinancialLedgerMaterializationPolicyVersion(val value: String) {
    init { require(Regex("[a-z0-9][a-z0-9./-]{0,63}").matches(value)) { "Invalid materialization policy version" } }
    override fun toString(): String = "[REDACTED]"
    companion object {
        val V1 = FinancialLedgerMaterializationPolicyVersion("marketplace-financial-ledger-materialization/1")
    }
}

enum class FinancialLedgerComponentMaterializationNotAuthorizedReason {
    BASIS_AUTHORITY_UNAVAILABLE,
    UNSUPPORTED_SOURCE_KIND,
    UNSUPPORTED_FINANCIAL_STAGE,
    FINANCIAL_OCCURRENCE_AUTHORITY_UNAVAILABLE
}

sealed interface FinancialLedgerComponentMaterializationAuthorityDecision {
    data class Authorized(
        val sourceAuthorityIdentity: MarketplaceEconomicEvidenceObservationId,
        val sourceAuthoritySemanticVersion: FinancialLedgerSourceAuthoritySemanticVersion,
        val materializationPolicyVersion: FinancialLedgerMaterializationPolicyVersion,
        val expectedSourceFingerprint: FinancialLedgerMaterializationSourceFingerprint,
        val basis: FinancialLedgerBasis
    ) : FinancialLedgerComponentMaterializationAuthorityDecision { override fun toString() = "[REDACTED]" }

    data class NotAuthorized(val reason: FinancialLedgerComponentMaterializationNotAuthorizedReason) :
        FinancialLedgerComponentMaterializationAuthorityDecision { override fun toString() = "[REDACTED]" }

    data object IntegrityFailure : FinancialLedgerComponentMaterializationAuthorityDecision
    data object Unavailable : FinancialLedgerComponentMaterializationAuthorityDecision
}

class VerifiedFinancialLedgerComponentMaterializationPlan internal constructor(
    val sourceAuthorityIdentity: MarketplaceEconomicEvidenceObservationId,
    val sourceAuthoritySemanticVersion: FinancialLedgerSourceAuthoritySemanticVersion,
    val materializationPolicyVersion: FinancialLedgerMaterializationPolicyVersion,
    val verifiedSourceFingerprint: FinancialLedgerMaterializationSourceFingerprint,
    val subject: MarketplaceEconomicEvidenceSubject,
    val stage: FinancialLedgerStage,
    val basis: FinancialLedgerBasis,
    val direction: EconomicDirection,
    val magnitude: MarketplaceMoney,
    val source: EconomicSource,
    val occurredAt: Instant
) { override fun toString() = "[REDACTED]" }

enum class FinancialLedgerComponentMaterializationIntegrityFailureReason {
    OPERATIONAL_ORGANIZATION_MISMATCH,
    SOURCE_OBSERVATION_INCONSISTENT,
    AUTHORITY_INTEGRITY_FAILURE,
    SOURCE_AUTHORITY_IDENTITY_MISMATCH,
    MATERIALIZATION_POLICY_VERSION_UNSUPPORTED,
    SOURCE_FINGERPRINT_MISMATCH
}

sealed interface GovernedFinancialLedgerComponentMaterializationResult {
    data class Eligible(val plan: VerifiedFinancialLedgerComponentMaterializationPlan) :
        GovernedFinancialLedgerComponentMaterializationResult { override fun toString() = "[REDACTED]" }
    data class NotEligible(val reason: FinancialLedgerComponentMaterializationNotAuthorizedReason) :
        GovernedFinancialLedgerComponentMaterializationResult { override fun toString() = "[REDACTED]" }
    sealed interface Failed : GovernedFinancialLedgerComponentMaterializationResult {
        data class IntegrityFailure(val reason: FinancialLedgerComponentMaterializationIntegrityFailureReason) :
            Failed { override fun toString() = "[REDACTED]" }
        data object Unavailable : Failed
    }
}

object FinancialLedgerComponentStageCompatibility {
    fun stageFor(type: EconomicComponentType): FinancialLedgerStage = when (type) {
        EconomicComponentType.REVENUE -> FinancialLedgerStage.SALE
        EconomicComponentType.MARKETPLACE_COMMISSION -> FinancialLedgerStage.MARKETPLACE_COMMISSION
        EconomicComponentType.MARKETPLACE_FEE -> FinancialLedgerStage.MARKETPLACE_FEE
        EconomicComponentType.SHIPPING -> FinancialLedgerStage.SHIPPING
        EconomicComponentType.ADVERTISING -> FinancialLedgerStage.ADVERTISING
        EconomicComponentType.TAX -> FinancialLedgerStage.TAX
        EconomicComponentType.PRODUCT_COST -> FinancialLedgerStage.PRODUCT_COST
        EconomicComponentType.FINANCIAL_COST -> FinancialLedgerStage.FINANCIAL_COST
        EconomicComponentType.OTHER_ADJUSTMENT -> FinancialLedgerStage.OTHER_ADJUSTMENT
    }
}

object GovernedFinancialLedgerComponentMaterializationBoundary {
    fun evaluate(
        operationalOrganizationId: OrganizationId,
        observation: MarketplaceEconomicComponentObservation,
        authorityDecision: FinancialLedgerComponentMaterializationAuthorityDecision
    ): GovernedFinancialLedgerComponentMaterializationResult {
        if (operationalOrganizationId != observation.subject.organizationId)
            return integrity(FinancialLedgerComponentMaterializationIntegrityFailureReason.OPERATIONAL_ORGANIZATION_MISMATCH)

        if (
            observation.component.organizationId != observation.subject.organizationId ||
            observation.component.orderId != observation.subject.orderId ||
            observation.component.magnitude.currency != observation.subject.currency
        ) return integrity(FinancialLedgerComponentMaterializationIntegrityFailureReason.SOURCE_OBSERVATION_INCONSISTENT)

        val stage = FinancialLedgerComponentStageCompatibility.stageFor(observation.component.type)
        return when (authorityDecision) {
            FinancialLedgerComponentMaterializationAuthorityDecision.IntegrityFailure ->
                integrity(FinancialLedgerComponentMaterializationIntegrityFailureReason.AUTHORITY_INTEGRITY_FAILURE)
            FinancialLedgerComponentMaterializationAuthorityDecision.Unavailable ->
                GovernedFinancialLedgerComponentMaterializationResult.Failed.Unavailable
            is FinancialLedgerComponentMaterializationAuthorityDecision.NotAuthorized ->
                GovernedFinancialLedgerComponentMaterializationResult.NotEligible(authorityDecision.reason)
            is FinancialLedgerComponentMaterializationAuthorityDecision.Authorized ->
                authorized(observation, stage, authorityDecision)
        }
    }

    private fun authorized(
        observation: MarketplaceEconomicComponentObservation,
        stage: FinancialLedgerStage,
        authority: FinancialLedgerComponentMaterializationAuthorityDecision.Authorized
    ): GovernedFinancialLedgerComponentMaterializationResult {
        if (authority.sourceAuthorityIdentity != observation.id)
            return integrity(FinancialLedgerComponentMaterializationIntegrityFailureReason.SOURCE_AUTHORITY_IDENTITY_MISMATCH)
        if (authority.materializationPolicyVersion != FinancialLedgerMaterializationPolicyVersion.V1)
            return integrity(FinancialLedgerComponentMaterializationIntegrityFailureReason.MATERIALIZATION_POLICY_VERSION_UNSUPPORTED)

        val verified = FinancialLedgerMaterializationSourceFingerprintV1.fingerprint(observation)
        if (verified != authority.expectedSourceFingerprint)
            return integrity(FinancialLedgerComponentMaterializationIntegrityFailureReason.SOURCE_FINGERPRINT_MISMATCH)

        return GovernedFinancialLedgerComponentMaterializationResult.Eligible(
            VerifiedFinancialLedgerComponentMaterializationPlan(
                observation.id, authority.sourceAuthoritySemanticVersion, authority.materializationPolicyVersion,
                verified, observation.subject, stage, authority.basis, observation.component.direction,
                observation.component.magnitude, observation.component.source, observation.component.occurredAt
            )
        )
    }

    private fun integrity(reason: FinancialLedgerComponentMaterializationIntegrityFailureReason) =
        GovernedFinancialLedgerComponentMaterializationResult.Failed.IntegrityFailure(reason)
}
