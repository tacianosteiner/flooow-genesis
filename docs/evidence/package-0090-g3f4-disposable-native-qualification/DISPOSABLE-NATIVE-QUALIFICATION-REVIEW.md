# G3F4 disposable native implementation and qualification

Status: DISPOSABLE MECHANISMS QUALIFIED IN RECORDED CASES; FULL GATE HOLD.
Input branch: checkpoint/package-0090-cloud-handoff.
Input commit: bd840059f5a78d8e28a09a0ccc6463f3d5098663.

## Authority consumed

The following is the user's explicit authorization, preserved verbatim. It is the execution authority for this isolated experiment; earlier proposals alone did not authorize implementation.

> Authorize G3F4_DISPOSABLE_NATIVE_PROTOCOL_IMPLEMENTATION_AND_QUALIFICATION against approved G3F4_NATIVE_ENROLLMENT_PROTOCOL_V1 SHA256 9211331ab14ebf5b356716714f5b947bb45a739623690bb286024be3d70a550d and VERSIONED_REHEARSAL_POLICY_CONTEXT structure SHA256 d1aeee0a73aa20715d569fefa93c0c7512b6cca49d6a6154c57737df4e6ffb55 only in independently isolated disposable rehearsal infrastructure. Permit minimal native PostgreSQL component implementation and compilation, disposable supervisor/receiver/socket runtime, synthetic disposable role/database/context fixtures, runtime qualification, bounded fault injection, measurement collection and cleanup of owned disposable resources. Experimental harness controls must be recorded separately and confer no numeric policy authority. Forbid canonical V6 access or mutation, canonical deployment/incarnation or other canonical IDs, T0, canonical keypair or other signing keys, SIGN, canonical ADMIN execution, TREG, final runner, production deployment, production secrets, canonical header/readiness provisioning and any adoption, approval or provisioning of numeric ACK, policy, health, resource or drain bounds. Preserve existing frozen artifacts and record failures without production or full-watchdog PASS claims.

The two input hashes refer to frozen Git blob bytes. Synthetic identifiers, four synthetic login roles, a disposable database and a protected minimal binding table were created solely inside owned containers. Fixture PostgreSQL administration was performed; canonical ADMIN was never executed. No canonical infrastructure, keys, credentials, IDs, readiness/header provisioning, T0, SIGN, TREG or final runner was used. No migration, API, production dependency or deployment was added.

## Implemented and observed

The native shared-preload component enrolls from the PostgreSQL login event using server-derived identity and a self pidfd. The supervisor creates receiver and postmaster with atomic clone3/CLONE_PIDFD anchors, seals an inherited memfd context, and transfers the postmaster anchor through a private socketpair. The receiver uses private AF_UNIX SOCK_SEQPACKET, peer/message pidfds and SCM credentials, compares retained kernel anchors, checks the fixture catalog independently and returns an epoch/request-digest association. That digest is not a signature. Receiver or postmaster generation loss invalidates enrollment and causes coarse disposable PostgreSQL fast shutdown; restart creates a fresh bootstrap epoch.

R1 recorded 16 passing cases; R2 recorded 34; R3 recorded 37 native/adversarial passing cases, including 228 parser assertions. These rounds overlap and must not be summed as unique coverage. R3 additionally recorded a harness failure: I/O generation could not write its destination. Its I/O-labelled observations are excluded from load qualification. A strict successor measurement run corrected the directory and recorded five passing cases, including an actual permission denial for startup event-trigger disabling. CPU and 16 MiB overlay I/O generators completed, but overlap with measured requests was not verified. No load-tail qualification follows.

The retained standalone STARTUP-BYPASS attempt ran after container removal and produced Docker's no-such-container error. Its original exit-only PASS inference is explicitly invalidated in its wrapper and excluded from coverage. The later measurement case supplies the actual runtime evidence. Initial compilation failures are retained in BUILD-ATTEMPTS.json; the final native build passed strict compiler checks. The final Python driver additionally propagates case/harness failures as nonzero exit status; this orchestration correction is syntax checked, with the preceding executed source snapshots preserved separately.

R2 also retains a successful independent kernel-anchor probe with descriptor substitution and child churn. Positive admission, service SQL denial, role/name/OID/attribute/membership changes, missing binding, wrong database/slot/deployment/incarnation/epoch, bad version, partial frame, absent/unsafe socket, foreign receiver anchor, lost/late reply, bounded catalog stalls, same-anchor replay, two live backends per slot, backend death and receiver/postmaster restart are bounded observations, not exhaustive security proof. Per-case records remain in QUALIFICATION.json.

## Experimental controls, not policy

The harness uses a 5,000,000 us abort budget, 128 registry entries, 20 ms death polling, 6 s late-reply injection and 7 s catalog/lock stalls. Measurement generators and subprocess timeouts are experimental controls only. They approve no ACK, freshness, policy, health, resource or drain bounds and do not resolve the existing 60 s versus 1 s/max 2 s policy conflict. No historical temporal bound was changed.

Native handler totals, receiver receive/validation/reply offsets and client process totals are distinct measurements. Client totals include Docker/psql startup. MEASUREMENTS.json reports descriptive observed values only; finer login-to-send boundaries, scheduler isolation, JVM/GC, sustained load, worst-case guarantees and safety margins remain unknown. Enrollment is not continuing health.

## Isolation and provenance

Image: sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561, PostgreSQL 18.4. Kernel: 6.18.33.2-microsoft-standard-WSL2. Containers had network none, no host mounts or published ports, and tmpfs PostgreSQL/run/tmp storage. Only labelled experiment-owned containers were removed. No plaintext credentials were created; fixture local authentication used trust within this isolation.

Default Docker seccomp rejected clone3 with errno 38. The frozen test profile permits clone3 and leaves all other rules of the retained Moby source profile unchanged. It is not seccomp-unconfined and adds no capability. Equality to Docker's separately versioned built-in profile is not claimed. Exact source/test profile hashes and build hashes are in raw records. The missing libpq client header was fetched from official PostgreSQL REL_18_4 and pinned to SHA256 499d984421f5490be016f7d49a8599e7f8be120f0cf80c200e872265064be7c0; no package was installed. SOURCE-R1/R2/R3/MEASUREMENT snapshots preserve the source used by each run, independently of later harness edits.

## Remaining closure and decision

H01 numeric policy reconciliation remains OPEN. H02 complete native/watchdog runtime remains OPEN: this prototype has an ASCII-only parser, a minimal protected role/slot fixture rather than full V043/original-attestation validation, no general UTF-8 NFC qualification, no continuing independent freshness enforcement, no complete transaction/effect/ownership drain reconciliation, and no universal suspend/scheduling bound. Its SPI abort timer is experimental and does not establish general caller-timeout restoration semantics. H03 structural authority is previously closed, but current approval custody/runtime qualification remains OPEN because this experiment uses synthetic bootstrap context. Existing B0/H3/M0/L0 disposition remains HOLD.

No production PASS, full-watchdog PASS, canonical readiness or adoption decision is made. The next technically determined work is to define and qualify the remaining full binding/attestation and continuing enforcement invariants against synthetic fixtures, under the same disposable-only boundary; canonical integration and numeric adoption remain outside this authority.
