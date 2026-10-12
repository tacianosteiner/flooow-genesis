# Continuation unit 2 ? scoped fields, variadics and original provenance

The current cached source inventory now has 31,451 scalar identifier occurrences
bound to structural declaration/output-field types; 91 star-expansion syntax
occurrences were separated from the prior 31,542 diagnostic total. This is not
an independent semantic closure denominator or complete runtime/catalog proof.

Resolution covers aliases, correlated scopes, UNION arms, CTE/recursive CTE
outputs, VALUES, LATERAL/ordinality, array slicing, %ROWTYPE, SQL-return fields,
PL parameters/locals, system declarations, Flyway 13.2.0 history declarations
and record assignments that structurally dominate a use. INSERT source values
are separated from target-table namespace. Operator/cast/coercion and complete
exception/control-flow semantics still require their own proof.

Seventeen currently known variadic calls are source-bound: three text-array
hash calls and fourteen qualified builtin num_nonnulls calls. These use exact
source ordinals/hashes and PostgreSQL 18.4 catalog declarations. Trigger/default
and structured-body expansion can still enlarge the execution graph; no full
scope-zero is inferred from cached scope-zero.

Original body rebinding discovered two previously omitted structured SQL RETURN
bodies. They are now preserved as exact original AST/provenance and must expand
reachability through governance serialization helpers. The old empty body is
not classified as an executable no-op or OUT_OF_SCOPE.

52 ordinary bodies and 2 structured-body declarations are rebound to original
source. Ordinal/hash provenance for extracted expressions is allowed by the
mission; parser-only normalization remains explicit. Missing original declaration
binding is zero for this current source set, but exact semantic-item coverage is
still open because omitted/implicit functions require expansion.

No SQL/runtime/native/key/policy/canonical action occurred. Prior artifacts and
hashes remain preserved. Next unit: structured SQL + trigger dependency expansion,
full control-flow and NULL-effect obligations, then the two-layer model contract.
