# Package0090 native health100us feasibility — no timing amendment

Result: INCONCLUSIVE. The tested cold and warmed mechanisms do not satisfy
100us. No legitimate fresh control, READY/header or S04 invocation was created.
This is not an inherent impossibility result or a timing amendment request.

Branch: checkpoint/package-0090-cloud-handoff. Baseline local/origin:
701b595511dc70f50a38f128b1c6aa411d3259a1. Initial tracked/staged status was clean;
protected local/origin refs retained their prior hashes. The explicit user
request and its SHA256 are frozen in freshness-contract.json/USER-REQUEST.txt.

## Exact equations

Native qualification uses the current request's complete-seven-participant
constraint together with the Native Health Contract/Design: original emission,
same Linux boot and compatible CLOCK_BOOTTIME. Each participant's own T3 is
retained. At the guard's complete T9 decision, and again at a qualification
consumer T10, require0 <= observer_ns - original_emission_ns <=100000.
All comparisons use integer nanoseconds; no rounding, grace,200us substitution
or later timestamp replaces an original emission. The boundary is inclusive,
consistent with S04 rejecting ages greater than the actual.

The canonical S04 equation is separately
0 <= EXTRACT(EPOCH FROM(database_now-watchdog_checked_at))*1000000
<= policy_values[23], using PostgreSQL wall-clock timestamptz. That actual value
is fixture tag24=100us; approved maximum200us remains a bound, not the active
value. The native BOOTTIME equation and SQL watchdog equation are not identical
events/clock domains. No cross-clock equivalence or readiness materialization
proof is assumed. The old native prototype sampled its guard clock before
some final verification; this tranche measures through complete verification
and consumer read instead.

## Cold decomposition before optimization

Twenty instrumented reproductions preserve the original source at the baseline
and retain full derived C source/hash and raw outputs. Each captures T0 trigger,
T1 work start,T2 work finish,T3 original emission,T4 send,T5 recvmsg return,T6
credential/pidfd validation,T7 result verification,T8 fresh catalog completion,
T9 full guard decision. Canonical readiness T10 is NOT_REACHED. T8 can precede
T7: the real event DAG is retained rather than forcing a fictional sequence.

The post-emission guard catalog operation uses shell/popen/psql and a new
connection. Its measured min/p50/max was22268.680/25673.357/40868.835us.
Participant POSTMASTER/CENSUS work medians were26580.694/26257.207us.
Complete guard ages across the140 participant samples ranged23019.977 to
104024.951us. The code also delayed early emissions behind later setup/enrollment
and a guard wait for all participants. Evidence printing occurs before complete
validation in this original path. Docker exec outside the native process is not
included in the measured freshness intervals. These measurements establish the
dominant original sources; they do not establish physical lower bounds.

## Contract-preserving setup and optimized mechanism experiment

The current request explicitly permits setup/prewarming of processes, host and
pidfd anchors, enrollment/generation/channel binding, connections/plans,
providers, immutable dependency expectations, memory and output buffers.
The warmed mechanism harness performs these before a shared atomic barrier.
It retains all seven actors, original per-actor emissions, kernel credentials,
SCM_RIGHTS pidfd transfer and independent FD target correlation. Host/root and
actual PostgreSQL postmaster pidfds remain live-checked. Generation/counter/
nonce are checked on every result.

POSTMASTER and CENSUS execute actual fresh prepared libpq catalog/history/role
queries on persistent sessions. HEALTH_GUARD runs its own fresh query every
epoch and compares result bytes. No old query result substitutes for new work.
The guard retains independent fresh signature verification. Producer key
generation occurs only inside the producer process before the epoch; only the
public key crosses its authenticated setup channel. Consumer verification and
producer signing are rerun for every fresh context-bound nonce.

Supervisor/receiver execute fresh generation/epoch/target-pidfd validation and
digest computation against legally pre-established target identity. Enforcement
uses an actual pidfd SIGSTOP action; the independent parent guard observes the
kernel stop event before returning completion to the actor. The actor emits
only after completion. Old stop events are consumed and actual continuation is
confirmed outside the fresh section before another epoch. This removes process
creation and virtual-file lookups from the optimized hot path while retaining
fresh kernel action/outcome checks.

Result evidence stays in memory until decisions finish; JSON/file/stdout
persistence occurs afterward. HOT_PATH_EVIDENCE_IO=NONE for the optimized path.
The guard verifies the exact current producer signature once, then matches the
consumer's exact original bytes; it does not repeat identical crypto work or
reuse a previous epoch's verification. Actual complete original V041 approval
publication/lineage, full native lifecycle and valid-control attacks remain
unclosed; timing of these mechanisms is not full health authority.

## Steady-state measurements

Two final variants each perform500 complete epochs; first50 are excluded from
steady-state summaries. Every epoch executes fresh work after the barrier.
Both variants use SCHED_OTHER(0),16 available CPUs and no container CPU quota
(cpu.max=`max 100000`). No realtime priority, unsafe scheduler privilege or
global kernel setting was changed. The pinned variant assigns the guard and
seven actors to eight distinct available CPUs; it is deterministic TEST
engineering, not a production scheduling claim.

| Variant | Steady epochs | Passes | Oldest min/p50/max (us) |
|---|---:|---:|---|
| Persistent, unpinned |450|0|571.344 /1093.821 /2807.933|
| Persistent, pinned |450|0|381.730 /494.912 /1029.365|

Final pinned participant age distributions are:

| Participant | min | p50 | p90 | p95 | p99 | max (us) |
|---|---:|---:|---:|---:|---:|---:|
| POSTMASTER |253.401|377.908|453.107|485.362|616.952|885.788|
| SUPERVISOR |380.793|493.904|607.308|658.557|773.938|1029.365|
| RECEIVER |381.730|494.115|605.164|648.819|747.220|1024.608|
| CENSUS_OBSERVER |236.539|361.682|438.687|486.333|606.574|746.676|
| APPROVAL_PRODUCER |310.336|420.048|523.167|561.115|661.175|901.406|
| APPROVAL_CONSUMER |226.001|277.590|365.241|411.393|505.878|700.058|
| ENFORCEMENT_WORKER |190.367|217.467|286.143|306.269|359.757|610.101|

The pinned guard's independent catalog min/p50 was86.931/101.436us; fresh
signature/first-result validation min/p50 was82.381/92.362us. These serial
post-emission operations give an empirical169.312us tail bound across the
tested samples. This is a bound for this measured serial implementation, not
every possible contract-preserving implementation. The fast participants also
wait for heterogeneous peer work and full guard validation before simultaneous
eligibility, so their age cannot be inferred from their own work duration alone.

## Measurement limits are explicit

T5 is kernel delivery observed at recvmsg return in BOOTTIME, not the kernel
enqueue instant. IPC transport, socket queueing and guard descheduling cannot
be uniquely separated with these captures. Credential and pidfd validation are
measured as a combined span. Raw /proc scheduler counters are retained, but
Linux sched_schedstats was observed disabled(0); zero counters are not evidence
of zero scheduler wait. Exact scheduler/transport/queue subdivisions therefore
remain UNKNOWN, not a hidden other bucket. No privileged kernel tracer or
global scheduler setting was enabled. These limits prevent a complete causal
latency attribution and are included in the INCONCLUSIVE decision.

All emitter/guard timestamps call the same CLOCK_BOOTTIME primitive in the same
Linux container/boot context; no REALTIME timestamp enters native age math.
Exact99us,100us,101us, one-nanosecond-over, future and mixed-clock tests pass
normally and under Python -O. Raw integer nanoseconds remain authoritative;
display microseconds/percentiles do not drive eligibility.

## Decision, remaining avenues and interlocks

100US_FEASIBILITY=INCONCLUSIVE. Zero of900 final steady-state complete epochs
passed. The measured mechanisms show large improvement over shell/new-connection
execution, but not a valid fresh control. Legitimate avenues remain: nonblocking
receive/incremental independent validation; overlap fresh libpq and signature
work while proving dependency currentness; determine the exact required
catalog query before reducing it; obtain compatible kernel tracing within
authorized privileges. They were not executed as NEXT.

TIMING_AMENDMENT_REQUIRED_FOR_FURTHER_PROGRESS=NO: exhaustion has not been proved.
No replacement timing is proposed or adopted. Participant count,100us actual,
200us maximum, original emissions and canonical SQL remain unchanged.

VALID_FRESH_CONTROL=NO; FIRST_PATH_NATIVE_HEALTH_READY=NO. Full native positive,
valid-control negatives and replacement/guard-restart campaigns are NOT_EXECUTED.
Readiness/header/original and S04 stay unexecuted behind the failed native gate;
no invalid starting control is used to manufacture successful negative proof.
Global semantic bound0/unbound851 and S04 bound0/unbound33 remain unchanged.

Tests are counted separately from measurements:6 clock cases,7 participant
mechanism/retention assertions and3 complete-epoch integrity assertions=16
distinct cases. The132 reused foundation assertions per target are supporting
reproduction evidence, not recounted as new test cases. Accepted measurement
records comprise140 cold plus7000 warmed participant samples and1020 epoch
records, with6300 participant/900 epoch samples in steady-state warm summaries.
No accepted assertion failed; the target fresh-control goal was not achieved.

Raw development runs remain separate: warm1 had a diagnostic-buffer retention
race; warm2 fixed retention but is superseded by producer-only key preparation.
Neither feeds final distributions. Final warm3 checks source ages against all
retained timestamps and native consumer decisions. All owned target resources
were removed; no private keys are stored in evidence.

Scoped BLOCKER_COUNT=1: complete native fresh control remains unproven.
HIGH/MEDIUM/LOW are UNKNOWN pending full native security review, not a global
Package severity claim.

## Integrity

V043 Git-LF SHA256 remains
b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d;
fence present; source unmodified and canonical migration unexecuted. V001-V042,
main, Room and global-commerce refs/worktrees remain unchanged. No shared or
production DB contact, production policy/key, field authority or Room activation.
EXECUTION_AUTHORITY=BLOCKED; RECOVERY_AUTHORITY=BLOCKED; ROOM_OPERATIONAL=NO.

NEXT: test an independently validated concurrent guard receive/catalog/crypto
pipeline and complete currentness/clock attribution without changing timing.
NEXT_EXECUTED=NO.
