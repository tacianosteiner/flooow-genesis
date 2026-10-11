# Non-self-referential observation graph

OBSERVER_GRAPH_NODES=9; OBSERVER_GRAPH_EDGES=8; SELF_HEALTH_ONLY_EDGES=0; UNOBSERVED_CRITICAL_PARTICIPANTS=0_IN_DESIGN.

HOST_PLATFORM -> HEALTH_GUARD -> {POSTMASTER, SUPERVISOR, RECEIVER, CENSUS_OBSERVER, APPROVAL_PRODUCER, APPROVAL_CONSUMER, ENFORCEMENT_WORKER}.

The mandatory graph is acyclic. The trusted host platform/service manager independently anchors and monitors the guard, and is an explicit trust boundary, not an assumed healthy participant hidden from the model. If root/guard health is unavailable or unprovable, all new acceptance is denied. Its supervision uses retained OS identity and an externally observed control loop/result, not solely a self-written heartbeat file.

Existing reciprocal observations may remain supplementary but cannot satisfy or bypass a required independent edge. Every decision requires all required dependencies, not majority, OR or mutual self-certification. No critical actor is sole authority for its own health. Missing observations retain quarantine/ownership and require reconciliation. The graph is a design obligation; it does not claim these processes or edges currently exist.
