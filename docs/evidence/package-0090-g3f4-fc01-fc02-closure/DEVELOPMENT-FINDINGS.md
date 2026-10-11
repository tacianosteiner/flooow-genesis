# Successor development findings

The prior 1211-file successor evidence manifest and all 885 historical checks remain
preserved. No previous PASS is counted as current qualification.

parallel-pre-fix-01 reproduces actual unsupported governed execution: the EXPLAIN
ANALYZE completes successfully with two Workers Launched. The expected security
assertion is a literal FAIL. Owned fixture cleanup is preserved in raw evidence.

parallel-post-fix-01 reveals the real PostgreSQL 18 default `io worker` population.
The initial full-population classifier treats it as unknown and correctly fails
closed, causing four baseline admission FAILs. Its parallel-denial assertion cannot
qualify the worker fix, because baseline login itself was denied. That entire round
remains failed development evidence. The successor explicitly classifies this known
storage service as OBSERVED_ONLY, without granting governed SQL authority.

The frozen V043 interlock is an unconditional DO/RAISE SQLSTATE 55000 before DDL.
The message states implementation closure is incomplete. Subsequent inspection
finds a matching post-H02 source security review with PASS, while that review
explicitly retains the executable fence. The SQL does not consume review state:
there is no runtime predicate or missing fixture datum that can satisfy an
unconditional raise. FC01-SOURCE-INTERLOCK-DIAGNOSIS.json records the exact review
and hash domains. Positive execution requires a legitimate executable handoff;
no fence is removed, stripped or bypassed.

population-post-fix-02 restores all four allocated logins and rejects the actual
parallel worker at the native executor boundary, then recovers only after a fresh
joint generation. population-development-03 additionally observes an actual
autovacuum worker under separately labeled experimental fixture controls.

finite-schedule-development-01 compiles the actual observer into its controlled
model and passes seventeen named state/generation schedules plus the unknown-type
classifier assertion. Catalog/PID tuple reuse is a model vector, not a forced
Linux allocator wrap. The duplicate-row vector is fail closed in the successor.

compound-development-01 passes two concurrent actual writers under receiver stall,
query-first rollback/OWNED retention and approval revocation during delayed ACK.
ceremony-development-01 signs A and later B independently inside separate private
container tmpfs, verifies native admission, and rejects actual old A approval,
attestation/frame and mixed A/B authority material under B. The child assertions
are counted once through the parent record. No full SQL accepted-consumption
ceremony is inferred while the unchanged frozen source is fenced.

fc01-fc02-final-01 completed 443 PASS with no FAIL or operational error. Further
compound requirements then justified new instrumentation; that whole cohort is
historical evidence rather than qualification of changed code.

extended-development-01 passes actual approval revocation plus an originally
emitted stale Supervisor heartbeat, then records an operational reset error:
the harness asserts approval publication against the already stopped catalog
before restarting PostgreSQL. This error is preserved and never qualified.

extended-development-02 repairs only that reset ordering and observes all thirteen
assertions PASS with no operational errors. It additionally exercises quarantine
between positive decision preparation and send, a live stopped postmaster, and a
live host approval consumer with stalled publication. Stopped retained postmaster
cleanup now continues the same kernel object before shutdown, including during
the already-quarantined witness wait. This does not restore eligibility.

fc01-fc02-final-02 records a distinct harness publication race in progress_probe:
two observation callers use the same gate.bin.next pathname and one atomic move
consumes the other caller's temporary file. Its literal operational error is
preserved. This batch is disqualified, not reconciled as a final PASS.

The successor serializes all observer snapshot/publication callers through the
same reentrant health lock and uses a unique temporary pathname for each root
publication. Existing explicitly locked test transitions remain compatible.
Source drift invalidates the incomplete final-02 batch; owned cleanup still runs.
No heartbeat, gate lease, census or policy number changes.

Only fc01-fc02-final-03 may contribute to the final new denominator. All previous
development, final-01, incomplete final-02 and 384-PASS rounds remain historical.
