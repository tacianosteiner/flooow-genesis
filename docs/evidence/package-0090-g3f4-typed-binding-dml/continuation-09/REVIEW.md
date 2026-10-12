# Scoped call argument review

Revisited all 15,513 explicit calls in the 68-function source graph using exact SQL scopes and record control paths, with the published expanded resolver as the unchanged base. Eight additional graph edges are implicit triggers. The initial traversal stack failure is preserved; analysis-only stack allowance repairs traversal and confers no numeric runtime policy.

243 previously untyped call arguments reduced to two after pinned catalog return candidates, text/non-array concatenation, min/max and array type rules. The remaining two use pg_proc.proargtypes subscripting: REL_18_4 pg_type declares oidvector with typelem oid and array_subscript_handler. Final unresolved call argument types: 0. Scalar identifier bindings remain 31,956/31,956. Neither count is semantic closure. Some type rules inherited from the prior resolver are structural; exact operator/polymorphic/overload safety remains separately open.

264 source call occurrences have one compatible target declaration; no compatible-target ambiguity remains in that subset. Compatibility is not complete namespace/ACL/overload-ranking or executable acceptance proof. Other calls cross builtin and extension boundaries. All 316 prior input bundles are explicitly partitioned as real unresolved gaps with narrowed missing facts and proof paths. Expanded trigger/constraint obligations are additional; the 316 are not a final denominator. No out-of-scope exclusion or final execution-dependency PASS is manufactured.

All frozen prior artifacts remain unchanged. No SQL/native/canonical/production execution, signing or policy adoption.
