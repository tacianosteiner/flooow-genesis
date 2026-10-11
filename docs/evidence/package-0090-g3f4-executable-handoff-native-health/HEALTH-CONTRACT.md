# Required native health contract — qualification HOLD

PROCESS_ALIVE != PARTICIPANT_HEALTHY. HEARTBEAT_FRESH != PARTICIPANT_MAKING_PROGRESS. CHANNEL_CONNECTED != CORRECT_GENERATION. A loop tick is not proof that required functional work completed.

Every participant requires independently observed identity, current generation, retained pidfd anchor, existence, original-emission heartbeat freshness, separately advancing completed-work progress, authenticated channel reachability, dependency health and applicable server-derived catalog binding. Revalidate all decision dependencies immediately before ACCEPT or census action. Never renew from stale queued emission, stale snapshot, old registry revision or pre-promotion observations. Quarantine is monotonic; provisional anchors grant no eligibility.

| Participant | Current identity / generation / anchor | Liveness / progress evidence and residual | Required external observer / fail-closed action |
|---|---|---|---|
| POSTMASTER | Supervisor-created child, retained atomic pidfd, joint boot epoch and server start | Existence/catalog sampling; no separately qualified heartbeat + functional-progress producer | Supervisor plus observer must deny admission/quarantine when identity, dependency or progress becomes unprovable |
| SUPERVISOR | Native retained anchor and sealed joint epoch | Original BOOTTIME heartbeat; loop advancement does not establish every completed function | Receiver and observer must deny promotion and retain quarantine |
| RECEIVER | Native retained child pidfd and joint epoch | Original emission heartbeat, reply freshness revalidation; complete functional progress witness missing | Supervisor and observer deny ACCEPT and initiate owned drain |
| CENSUS_OBSERVER | Separate native retained child anchor and joint epoch | Census epoch/revision CAS is protected; progress tick currently starts before successful census | Supervisor/receiver must reject stale applicability, deny eligibility and retain existing quarantine |
| APPROVAL_CONSUMER | Host harness thread, publication lease; no independently anchored native producer | Valid signature/publication is evidence of material, not independently qualified producer health or progress | Native consumer must require current anchored producer/channel/generation; stale approval cannot restore eligibility |
| ENFORCEMENT_WORKER | Enforcement co-located with observer/receiver; no independently identified worker | Actual selected cancel/terminate checks; complete operation-specific progress protocol missing | External observer must detect stuck work, deny admission, retain ownership and require reconciliation |

Required observed identity prevents PID/OID reuse, role recreation, namespace substitution, stale SCM descriptors and stale sockets. A jointly bootstrapped epoch does not prove independently replaceable supervisor/receiver epochs. No replacement contract is invented here. Recovery cannot erase quarantine or ownership; new eligibility requires an independently validated current enrollment and applicable authority.

Actual graph: Supervisor -> Receiver, Observer, Postmaster retained anchors; Receiver -> Supervisor, Observer, Postmaster dependencies; Observer -> Supervisor, Receiver, Postmaster and enrolled backend census. Receiver/Observer -> approval publication lease is not an independently anchored producer edge. Co-located enforcement has no independent worker edge. Reciprocal observations alone cannot establish full graph completeness.

`health_contract.py` freezes 54 single-participant states and eight compound states. Each full-contract NOT_RUN has an explicit blocker, reason and missing artifact. Fresh selected native regressions are reported separately; none is promoted into a full nine-dimension state PASS. No numeric thresholds are selected or adopted. Full worst-case and numeric-candidate readiness remain HOLD.
