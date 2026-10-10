# Current contract reconciliation — adversarial design review

Input head: `7814d6749060b9f41877d3638310fbefdb4dd5f9`. Status: DESIGN PROPOSAL / GOVERNANCE HOLD. Implementation and runtime PASS are not asserted. No canonical access or execution was performed in this mission.

## Severity and counting

Count unique unresolved findings, not each attack vector. Current package findings BLOCKER=0, HIGH=3, MEDIUM=0, LOW=0. Historical reports HIGH=2 remain unchanged; this review explicitly adds H03 for unresolved new-purpose/current-custody release authority. HOLD is mandatory; zero BLOCKER count does not mean safe release. No waiver or actual negative-runtime PASS is asserted.

| ID | Severity | Unresolved issue | Scope | Required disposition |
|---|---|---|---|---|
| H01 | HIGH | Policy/profile inconsistency and unqualified numeric operating envelope | policy/context mismatch,100us,cold/ACK | No numeric change; new version requires independent qualification and explicit approval |
| H02 | HIGH | Complete mandatory native admission/continuous watchdog deployment unqualified | receiver/watchdog/drain failure | Proposed V1 remains unimplemented; independent supervisor and failure matrix must qualify |
| H03 | HIGH | New native/policy purposes and current approval custody not approved | stale/copied approval,clone,restore | Historical host approval exists; verify current status and approve exact new purposes before consumption |

## Attacks and designed denials

| Attack | Finding | Required mechanism, not tested result |
|---|---|---|
| stale approval / copied approval artifact | H03 | Exact target/private marker,current authenticated status and digest; copy is not new authority |
| copied DB / physical clone / logical restore | H03 | External context excluded from DB backup; inaccessible NOT_READY, governed new incarnation before exposure |
| role recreation / OID reuse / role rename | H02 | OID OR name recognizes potential governed actor; both/current attributes/exact allocated slot must match; tombstones no rebind |
| slot substitution / database substitution | H02 | Exact binding fingerprint,slot,OID/name,DB namespace and approved host/header tuple; zero/ambiguous headers deny |
| socket path replacement / receiver impersonation | H03 | Protected checked namespace plus independently pinned peer process anchor and approved epoch; same-UID arbitrary native code outside service attacker model |
| receiver restart / postmaster restart / backend restart | H02 | Retained generation anchors die; fresh joint epoch,quarantine/drain; fresh physical backend enrollment; no resurrection |
| pidfd replay / SCM_RIGHTS replay / duplicate enrollment | H02 | SO_PEERPIDFD+SCM_PIDFD+SCM_RIGHTS anchor equality and liveness; one request/socket; exact same anchor idempotent,no renewal |
| connection pooling / fork / exec | H02 | Dedicated physical-backend enrollment per login/incarnation; CLOEXEC and connect/message/object equality; no logical-borrower identity |
| ACK timeout / ACK lost / partial frame / transfer failure | H01 | One monotonic total deadline; FATAL before usable login; provisional registry invalidates by backend death; numeric value unauthorized |
| receiver crash after ACCEPT / backend crash before ACCEPT | H02 | Independent supervisor invalidates admissions and drains; backend death invalidates anchor; ACK is not ongoing health |
| watchdog crash / drain failure | H02 | No positive refresh,deny admission,quarantine persists; signal success is not verified drain; no automatic ownership release |
| ambiguous COMMIT | H02 | Writer quiescence and authoritative query-first/reconciliation; preserve possible effects; no replay/renewal |
| policy/context version mismatch | H01 | Exact immutable context/policy/header/approval digests; no fallback to old or synthetically compatible profile |
| ADMIN/self-authored health or service bypass | H03 | Distinct responsibility/independent observation; event ALWAYS and protected GUC/DDL; trusted superuser remains trusted,not hostile-admin proof |

All vectors are design-reviewed only; runtime not run. Existing process-anchor PASS is preserved and does not answer role/approval/freshness failures. Proposed framing/namespace/generation/ACK/replay/duplicate/lifetime semantics have explicit fail-closed outcomes; their adoption and realization need governance and qualification. Existing host approval is not missing, but current revocation/custody status and exact new-purpose consumption are not proven by stored bytes.

DESIGN_SECURITY_REVIEW=PASS_FOR_INTERNAL_PROPOSAL_COHERENCE_RELEASE_HOLD
G3F4_H01=OPEN
WATCHDOG_DEPLOYMENT_HIGH=OPEN
