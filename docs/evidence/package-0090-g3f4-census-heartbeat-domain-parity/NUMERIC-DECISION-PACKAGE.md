# Numeric decision package — proposal only

Scope: TEST_ONLY_NONCANONICAL. Status: HOLD_INSUFFICIENT_QUALIFICATION.

NUMERIC_DECISION_STATUS=PROPOSAL_ONLY_NOT_AUTHORIZED
NUMERIC_VALUES_ADOPTED=NO
NUMERIC_CANDIDATE_EVIDENCE_READY=NO

No ACK, policy, health, resource or drain bound is proposed for adoption. Experimental abort (5s), root observer gate lease (20s), heartbeat freshness (10s), cancel-to-terminate observation (200ms), receiver poll (20ms), capacity (128), CPU quota (1) and memory (768MiB) are harness controls only. Gate preparation was moved out of evaluated cases; stale heartbeat rejection remains based on original monotonic emission, never on receipt time.

TIMING-QUALIFICATION.json records descriptive nearest-rank P50/P95/P99/MAX with denominators, client failures and assertion outcomes. These tiny cohorts and serial catalog/census observation do not establish tail reliability or worst-case continuous coverage. Container writable overlay fdatasync is distinguished from tmpfs; its underlying physical device is not identified. No extrapolation to production or persistent-device tails is justified.

Prerequisites for a future numeric proposal: all mechanism regressions and race schedules pass on fixed source/binary hashes; independent census/enforcer failure coverage; complete frozen verifier/domain/ownership parity; explicit censored/failure accounting; representative CPU/memory/persistent-storage cohorts; sufficient repeated distributions and operational risk analysis. A measured candidate still requires separate literal numeric policy authority before adoption.

H01 remains OPEN. Existing historical timing bounds and all frozen protocol/policy artifacts remain unchanged.
