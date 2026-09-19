# TASK-0165S2A1 — V036 Final Adversarial Gate

## Status

**PASSED**

V036 governed transaction identity withdrawal is frozen as technically validated at:

`54c4d9980c01cc6da0c9f3ac291338694d1210c0`

## Chain of custody

Baseline / V035 parent:

`48b5cd3831f3165591ec9519e8b99d4ee540e619`

V036 candidate:

`54c4d9980c01cc6da0c9f3ac291338694d1210c0`

Relationship:

- candidate is the direct child of baseline;
- commit distance is exactly 1;
- local HEAD equals candidate;
- origin branch HEAD equals candidate;
- worktree remained clean through validation.

## Final adversarial validation

Final gate package:

`FLLOOW-V036-FINAL-GATE-V2-20260919-150304`

Result:

```text
V036_FINAL_GATE=PASSED
BASELINE=48b5cd3831f3165591ec9519e8b99d4ee540e619
CANDIDATE=54c4d9980c01cc6da0c9f3ac291338694d1210c0
DIRECT_PARENT=True
COMMIT_DISTANCE=1
WORKTREE_CLEAN=True
DOMAIN_COMPILE=PASSED
FOCUSED_POSTGRES_TESTS=PASSED
FULL_BUILD=PASSED
GIT_DIFF_CHECK=PASSED
COMMIT=False
PUSH=False
```

The full repository build completed successfully with:

```text
BUILD SUCCESSFUL
100 actionable tasks: 100 executed
```

## Focused proof

The PostgreSQL transaction identity writer adversarial suite executed successfully, including the V036 withdrawal properties:

- contradictory-current-evidence withdrawal;
- no implicit replacement confirmation;
- parent evidence-lineage preservation;
- replay invariance;
- confirmed-parent requirement;
- concurrent withdrawal serialization;
- later V3 integrity damage does not make a historical binding irreversible;
- serialization against replacement confirmation;
- serialization against target reassignment;
- grant revocation serialization;
- rollback preservation;
- SQL immutability and projection attack resistance.

## Previous gate result correction

An earlier V036 gate reported:

```text
V036_FINAL_GATE=FAILED
FAILURE=HEAD_MISMATCH
expected=48b5cd3831f3165591ec9519e8b99d4ee540e619
actual=54c4d9980c01cc6da0c9f3ac291338694d1210c0
```

That result is **not evidence of a V036 implementation failure**.

The earlier gate incorrectly used the V035 parent/baseline SHA as the expected candidate HEAD.

The corrected gate separates:

```text
BASELINE_HEAD  = 48b5cd3831f3165591ec9519e8b99d4ee540e619
CANDIDATE_HEAD = 54c4d9980c01cc6da0c9f3ac291338694d1210c0
```

and validates the direct parent relationship independently.

Therefore the earlier result is classified as:

`VALIDATION-INSTRUMENT PRECONDITION FAILURE`

not:

`V036 TECHNICAL FAILURE`

## Governance boundary

This proof does not activate:

- S2B automatic policy;
- ExpectedSaleBasisPolicy;
- S3;
- C2;
- any real principal;
- any real permission grant;
- any operational field decision.

Those boundaries remain unchanged.

## Freeze

V036 candidate:

`54c4d9980c01cc6da0c9f3ac291338694d1210c0`

is accepted as the frozen implementation for TASK-0165S2A1 subject to the governance boundaries above.
