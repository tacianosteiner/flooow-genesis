# FLOOOW Post-MVP Codex Preparation Matrix

Status: PREPARED_POST_MVP_RESEARCH
Implementation authority: NONE
MVP dependency: NONE

| Block | Phase | Wave | Canonical implementation dependencies |
|---|---|---|---|
| 0001 | P0 | A | MVP finalized |
| 0002 | P1 | B | 0001 |
| 0003 | P2 | C | 0002 |
| 0004 | P2 | D | 0003 |
| 0005 | P3 | E | 0004 |
| 0006 | P4 | A | 0002 |
| 0007 | P5 | B | 0006 |
| 0008 | P5 | C | 0007 |
| 0009 | P6 | D | 0008 + PACKAGE-0090/S2A ancestry |
| 0010 | P7 | E | 0009 |
| 0011 | P8 | A | 0004 |
| 0012 | P8 | B | 0011 |
| 0013 | P9 | G | 0005 + 0010 + 0012 |
| 0014 | P9 | H | 0013 + Belief Revision ancestry |
| 0015 | P10 | I | 0009 + 0014 |
| 0016 | P10 | J | 0001-0015 as applicable |
| 0017 | P8 | C | 0004 + 0011 + 0012 |
| 0018 | P3+P8 | F | 0005 + 0017 |
| 0019 | P7 | G | 0010 + 0018 |
| 0020 | P9 | H | 0013 + 0014 + 0019 |

Preparation parallelism never overrides implementation dependencies.

PARALLEL_PREPARATION=YES
PARALLEL_SHARED_STATE_MUTATION=NO
SERIAL_GOVERNED_INTEGRATION=YES
IMPLEMENTATION_AUTHORIZED=NO
