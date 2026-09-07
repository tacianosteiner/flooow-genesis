# EXP-0016 â€” Information Gaps + Value of Information

Purpose: convert governed uncertainty into explicit information gaps and decide whether acquiring additional information is economically justified.

## Core invariants

uncertainty != permission to guess

missing information != zero

value of information != expected business value

information acquisition != canonical truth

information acquisition != authority to execute

AGENT != TRUTH
AGENT != AUTHORITY

## Model

An information gap captures:

- governed gap id;
- organization and subject scope;
- decision context;
- unknown variable;
- current belief state;
- current confidence band;
- uncertainty reasons;
- available acquisition method;
- acquisition cost;
- expected decision-impact range;
- reversibility;
- deadline;
- evidence requirements.

## Value of Information policy

VoI is not a magical probability produced by the model.

The harness uses a governed deterministic comparison:

expectedDecisionImprovementFloor
-
acquisitionCost
-
delayCost
-
executionRiskReserve

The result is a decision aid, not canonical truth.

## Decisions

- ACQUIRE_INFORMATION
- DEFER
- DO_NOT_ACQUIRE
- INSUFFICIENT_BASIS

Research-only. No production integration.
