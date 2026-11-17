# FLOOOW Post-MVP Cross-Block Contract Registry V1
Status: PREPARED_POST_MVP_RESEARCH
Implementation authority: NONE

Cross-block semantics are defined once, versioned, hash-bound and consumed by reference. Downstream blocks must not silently redefine upstream objects.

RuntimeEvidence: 0001 â†’ 0002,0013,0020
QualifiedEvidence: 0002 â†’ downstream as applicable
EconomicEntityIdentity: 0003 â†’ 0004,0005,0013,0017-0020
EvidenceAuthorityBinding: 0004 â†’ 0005,0011,0017
HypothesisIdentity/EvidenceBasis/AdmissibilityState: 0005 â†’ 0013,0018,0020
SkillCapabilityIdentity: 0007/0008 â†’ 0009,0010
AuthorityEnvelope: 0009 â†’ 0010,0015,0019
EconomicExperimentIdentity: 0010 composed with 0005 â†’ 0013,0018,0020
ExecutionCommand/ExecutionReceipt: 0010 â†’ 0013,0019,0020
WorldRegimeHypothesis: 0011 â†’ 0012,0013,0017
ScenarioContext: 0012/0017 â†’ 0013,0018
ExpectedIncrementalEffect/Counterfactual/CausalQualification: 0013 â†’ 0014,0018,0020
GovernedBeliefRevisionEvidence: 0014 â†’ 0015,0016,0020
AutonomyEnvelope: 0015 â†’ 0016
CapitalContext: 0017 â†’ 0018
CapitalAtRisk/CapitalEfficiencyFrontier: 0018 â†’ 0019,0020
InvestmentReadiness/CapitalTrace: 0019 â†’ 0020
EconomicReturn/InformationReturn/LearningEvidence: 0020 â†’ future P10 composition

Governed Economic Experimentation = EVOLVE + COMPOSE:
Signal â†’ Hypothesis â†’ Evidence Basis â†’ Admissibility â†’ Experiment Design â†’ Expected Incremental Effect â†’ Expected Economic Value â†’ Capital At Risk â†’ Governed Decision â†’ Authority Envelope â†’ Execution â†’ Receipt â†’ Observed Outcome â†’ Incremental Outcome â†’ Counterfactual â†’ Causal Qualification â†’ Economic Return â†’ Information Return â†’ Governed Learning.

Fundamental learning unit = Hypothesis. Creative != Hypothesis. Asset variation != semantic variation != independent hypothesis.
Identity candidate: HYPOTHESIS_ID â†’ EXPERIMENT_ID â†’ TREATMENT_ID â†’ ASSET_VARIANT_ID.

Evidence-weighted capital escalation candidate:
E0_HYPOTHESIS_ONLY / E1_HISTORICAL_ANALOGUE / E2_BOUNDED_EXPERIMENTAL_EVIDENCE / E3_REPLICATED_EVIDENCE / E4_CAUSAL_ECONOMIC_EVIDENCE / E5_LONGITUDINAL_ECONOMIC_EVIDENCE.
CAPITAL_ESCALATION requires EVIDENCE_DELTA + ECONOMIC_REASSESSMENT + AUTHORITY_CHECK. No stage automatically grants authority.

Experiment objective candidate: LEARN / EARN / LEARN_AND_EARN. Optimization reward != causal identification.
Information Return remains separate from Economic Return and must not become an opaque score before measurement ancestry/calibration are established.

Every promoted contract must eventually record CONTRACT_ID, SCHEMA_VERSION, SEMANTIC_HASH, PRODUCER_BLOCK, AUTHORITY_CLASS, PROVENANCE, CONSUMER_BLOCKS, BACKWARD_COMPATIBILITY, SUPERSESSION_RULE, STATUS. Unknown fields remain NOT_ESTABLISHED.
