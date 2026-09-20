# TASK-0165S2A — Explicit governed transaction identity writer

Status: IMPLEMENTED / PROVEN TECHNICALLY; REAL AUTHORIZED FIELD PROOF HOLD

Date: 2026-09-18

Base commit: f8d89a3d007f69616fc1f5145b8146ef19ef555e

Accepted scope: ADR/SPEC-0084 closed eight-file writer infrastructure package.
Revision 9 was revalidated and locally committed separately with an explicit
11-file whitelist. Post-commit worktree was clean; no push. S1 document remains
byte-identical SHA256 C64B28EF23F8B4AABCC19CE7BB420764C008C3DDAAC30B276DEEAB842857783E.
Final corrected V034 backend tests and subsequent final packaging passed.

Working-tree migration inspection ends at V034; V035 is selected for S2A only.
Older S3/V035 reservation is superseded; future S2B/S3 numbers remain unreserved.
S2A is explicit durable identity, not automatic policy or EXPECTED authority.

Internal adversarial design review: relation-specific rejection; canonical ML ID
with exact server-bound selected ML lineage; org-global confirmed uniqueness via
controlled head projection; actual V3 ingestion progress-row lock; same-transaction
current grant revalidation; fixed null guards; deterministic semantic fingerprints;
single shared future decision universe. BLOCKER=0 / unresolved authority-corrupting
HIGH=0 for this infrastructure design. This is not independent security certification.

Implementation: domain command/fingerprints, same-transaction authorized PostgreSQL
writer, V035 immutable ledger and controlled head projection, exact current source
evidence and org-global confirmed cardinality. Closed eight-file scope only.

Final fresh focused validation: TransactionIdentityTest (3) and
PostgresTransactionIdentityWriterTest (15), 18 cases, zero failures/errors/skips.
Both test tasks executed after final source/schema with task-specific --rerun,
--no-build-cache --no-daemon --console=plain. Archived XML timestamps
2026-09-18T19:41:28Z. Final V035 source/resource SHA256
75635967E95789E00BFD6368B906BEBF36055BAE8737B061A57A39D102DAD7FB.

Full validation: .\\gradlew.bat build --no-build-cache --no-daemon --console=plain,
BUILD SUCCESSFUL in 13m 48s; 100 tasks, 13 executed, 87 up-to-date.
Affected tests executed; existing up-to-date results are not claimed fresh.
Internal final implementation review: BLOCKER=0; unresolved authority-corrupting
HIGH=0. Failed initial fixture/compile attempts were corrected before final proof,
without relaxing production constraints or widening authority.

Known limitation: contradictory current evidence also blocks releasing a binding;
an exceptional correction needs separate governance. Deployment requires
least-privilege roles; database owner/server compromise is outside this boundary.
No public route or real authority provisioning is selected.
S2A real authorized field proof HOLD; real governed corpus=0. S2B/S3/C2 HOLD;
ExpectedSaleBasisPolicy UNFROZEN / real-pair RESEARCH gated by >=1 field pair;
economic equivalence and non-zero leakage NOT PROVEN. Security/runtime backlogs
remain separate and no source proof volume may be used as a fixture database.
