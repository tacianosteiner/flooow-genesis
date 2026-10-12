# Last-Codex adversarial review

Date: 2026-10-12. Result: HOLD. Publish best safe checkpoint as explicitly authorized.
BLOCKER_COUNT=3; HIGH_COUNT=2; MEDIUM_COUNT=1; LOW_COUNT=0.

| ID / severity | Finding | Disposition |
|---|---|---|
| B1 BLOCKER | Candidate reachability/arity is not catalog/overload proof; concrete omitted V035 variadic hash dependency. User calls 13 paths “entrypoints”, but the preserved contracts contain 17 SQL signatures. | Preserve 13 case universe and exact signatures; declaration extracted/hash-bound, call coercion/search_path/ACL and expanded dependencies still open. No candidate becomes PROVEN. |
| B2 BLOCKER | 131 parsed DML/row-lock sites lack proven implicit PK/FK/UNIQUE/CHECK/NOT NULL/default/generated/trigger/RLS/view/lock/CAS/rowcount/exception dependencies. | Structured graph exposes every missing bundle. No fixture READY or finite denominator. |
| B3 BLOCKER | Original provenance, scoped identifiers, grouped control flow, independent semantic deduplication and full three-valued logic review remain incomplete. | 12,570 ordinal/query links checked but not promoted to original-source predicate proof; 31,542 identifier occurrences remain unbound in this continuation. |
| H1 HIGH | Variadic hashing elides NULL elements; distinct argument vectors can yield identical source-derived preimages. | Abstract control retained; no cryptographic collision/exploit or executable SQL claim. Prove all caller field-presence and ordering prerequisites. |
| H2 HIGH | Eleven required-field structures agree, but encoding/enums/context binding and independent runtime corroboration/atomic replay ledgers are not closed. | Typed field/design refinement preserved; zero complete runtime verifiers claimed; sender result/digest/reference cannot create authority. |
| M1 MEDIUM | Execution recipes depend on unfinished contracts/authority; guard scripts alone are not useful qualification runners. | 02–06 explicitly double-blocked, no dynamic command injection; remaining code reasoning disclosed rather than claiming mostly execution. |

## Attacks and boundaries

- Reachable omission: variadic helper is positive evidence that cached scope is incomplete.
- Unreachable inclusion: all candidate inventory membership remains conditional; no node declared OUT_OF_SCOPE solely because absent from the candidate graph.
- Syntax/semantic duplicate overcount: RAISE literal/SQLSTATE and assignment syntax excluded from grouped candidate meanings; no asserted unique closure denominator.
- Predicate flattening: grouped AST/control context retained; candidate leaves do not individually authorize state transitions.
- Identifier ambiguity: aliases/CTE/subquery/record/parameter/schemas/extension overloads not guessed.
- SQL/external authority: previous 29 SQL candidates and nine cross-layer design bindings stay separate; no generic registry/approval/receipt relation invented.
- Script authority bypass: false flag blocks first; changing flag still stops at incomplete recipe. No external command/runner accepted.
- Canonical leakage/hidden mutation: no runtime/signing/Docker/canonical commands, secrets or IDs in handoff; only 01/99 read-only checks/console collection.
- Cleanup/retry: no new disposable resources created. Unknown effect does not release ownership or justify reexecution.
- Publication: current instruction permits coherent partial checkpoint. The earlier intake README's no-commit rule is historical and is explicitly superseded by the latest mission's best-safe-checkpoint authorization.

## PostgreSQL distinctions that the remaining proof must preserve

IF/ELSIF selects a branch only on TRUE; IF ELSE handles FALSE and NULL.
A rejection IF with UNKNOWN can therefore skip its RAISE. WHERE/JOIN matching
requires TRUE; that does not imply every PL branch is fail-closed.
See [PostgreSQL control structures](https://www.postgresql.org/docs/18/plpgsql-control-structures.html).

CHECK accepts TRUE or NULL, unlike NOT NULL. FK and uniqueness behavior depends
on declared match/null semantics, referential actions and relevant deferrability;
absence of WHERE effects does not imply absence of constraints/triggers.
See [PostgreSQL constraints](https://www.postgresql.org/docs/18/ddl-constraints.html).

IN/NOT IN and ANY/ALL may yield NULL; empty-array results, NULL arrays/elements,
strictness and operator choice require exact treatment.
See [PostgreSQL comparisons](https://www.postgresql.org/docs/18/functions-comparisons.html).

SECURITY DEFINER identity/search_path, function strictness and volatility are
source/catalog obligations, not inferred from a function name.
See [CREATE FUNCTION](https://www.postgresql.org/docs/18/sql-createfunction.html).

These are review rules, not proof that each frozen source occurrence is safe.
No NULL_SEMANTICS_MISMATCH_N=0 or complete control-flow claim is made.
