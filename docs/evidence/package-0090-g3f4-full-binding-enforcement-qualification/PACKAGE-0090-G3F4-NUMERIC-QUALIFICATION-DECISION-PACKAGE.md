# Package0090 G3F4 numeric qualification decision package

H01_STATUS=OPEN.
NUMERIC_DECISION_STATUS=PROPOSAL_ONLY_NOT_AUTHORIZED.
NUMERIC_VALUES_ADOPTED=NO.
NUMERIC_CANDIDATE_EVIDENCE_READY=NO.

Decision: recommend no numeric envelope from this experiment. TIMING-MEASUREMENTS.json retains descriptive N/FAIL/CENSORED/P50/P95/P99/MAX and explicit unknown boundaries. Nearest-rank percentiles from tiny cohorts are not tail or worst-case guarantees. Observer ineligible counts include deliberate faults; they are not an operational failure-rate estimate. Timing samples from overlapping rounds are not pooled as independent observations.

Recorded cohorts include native enrollment, independent observer execution/gaps, CPU and tmpfs-I/O overlap, bounded stalls, revocation/cancellation/termination and generation loss. Cold startup, recovery, precise revocation/detection/cancel/quarantine boundaries and full effect/drain timing are not all independently instrumented. Missing metrics remain null/unknown, never zero. I/O cohorts do not represent physical storage latency. Four requests per load cohort cannot substantiate P99 exposure or reliability.

Security exposure remains unbounded under a live-but-stalled observer/enforcer, serial catalog blocking, scheduler suspension and incomplete registry census/ownership reconciliation. No measured distribution closes those invariants. There is no defensible explicit safety-margin rationale for a production candidate until those gaps and cold/degraded/failure/censored populations are qualified.

The 5,000,000us enrollment abort and synthetic observation lease,200,000us escalation delay,20ms polling,128-entry capacity, CPU/memory quotas and injected delays are harness controls only. They confer no ACK/policy/health/resource/drain authority. The initial 2s harness lease failure and successor5s lease are separately preserved; this is not adoption of either value. Historical60s/1s/2s/100us values are preserved in place and their policy conflict remains OPEN.

Next technical prerequisite: close measurement boundaries and independent enforcement/census/frozen-domain parity before collecting representative cold/degraded distributions and proposing one coherent candidate. Governance adoption and canonical provisioning are outside this authorization.
