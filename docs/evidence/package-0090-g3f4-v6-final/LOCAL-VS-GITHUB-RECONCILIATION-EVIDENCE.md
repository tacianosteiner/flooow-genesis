# Local and GitHub reconciliation

Branch: `checkpoint/package-0090-cloud-handoff`. Inspection HEAD: `bd72e6463adbbf4d53c1500187a1cee99fea77c7`.
Origin/main: `77d482c97a663a527dcacc85036c7577dfc92782`. Evidence scope: G3F4 isolated rehearsal only.
Canonical baseline: NOT_READY / watchdog=false; all nine V6 registration rows absent.
Before/end allowlisted projection equal; policy SHA256 `e840fcadac2d5198a91cdb7b2345a31d4776cb3ead6e8b697391a4461a1a253d` unchanged.
Canonical mutation/T0/keypair/SIGN/ADMIN/TREG/runner: NONE. Test fixtures are separate.
Full root/migration projection, exact source chain, preserved hashes, and test results: [GATE-DATA.json](GATE-DATA.json).
ADMIN R2 SHA256: `c8ee2b6d06652d99db111a01956808f7488cde30f520e58d85114331a4a6d923`. Host-only authority is not full-runner execution authority.


Existing active Package0090 branch contains the correct lineage: origin/main is its ancestor,
39 commits behind this checkpoint, zero remote-only main commits. Active branch was initially synced.
Preserve this branch; do not create duplicated history, rebase, reset, merge or push main.
Initial local-only work: one existing ceremony test edit and one untracked historical rehearsal authorization.
The former is preserved; the latter is archived unchanged, with no expanded execution authority.
Two additional V041/V042 fixtures and their reset helper now explicitly target042, avoiding fenced V043.
First runs exposed that fixture defect; interrupted failing runs are not counted as passing runs.
No migration bytes, wrapper API, crypto, policy, ACL, deployment identity or provider path changed.

All previously tracked bytes except the documented fixtures are equal to initial capture.
All72 preexisting public external files and seven source pins remain equal; R1 is preserved.
Old V4/V5 allocations are historical/expired, not repaired/reused. Other branches/worktrees were inventoried,
not modified or assumed merged. Two requested research paths are absent here; no research files were imported.
Generated build files, private temp captures, old external artifacts and secret material are not staged.
Scoped .gitattributes prevents core.autocrlf from changing hash-pinned new files or the archived authorization.
Post-push LOCAL_HEAD==origin branch must be verified separately; this document is pre-commit evidence.
