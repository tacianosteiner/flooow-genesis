# Continuation unit 1 ? frozen source bindings and implicit declarations

Input checkpoint: 483cd290ba3b40e90c5f11a0652591883618cc28.
Correct worktree: C:/Users/xmz_r/Downloads/flooow-v042-implementation.
The old feature/task-0165s2a worktree was neither modified nor repurposed.

Three transaction_identity_hash call sites have exact original body/hash and
variadic type-expansion bindings. The 17-argument caller additionally uses the
PG18.4 implicit bpchar?text cast. This closes that source-binding omission, not
runtime catalog attestation, caller non-NULL preconditions or all variadic calls.

The reachable builtin num_nonnulls has fourteen additional cached call sites.
Their exact record/parameter bindings are the next work unit; total currently
known variadic sites is seventeen, not three. No complete variadic count is
claimed before trigger/default/implicit expansion finishes.

Frozen DML declaration expansion distinguishes 26 INSERT/UPDATE statements from
105 row-lock clauses previously grouped as 131 ?DML sites.? Table changes,
constraints, FK target declarations, unique indexes, trigger creation/deletion,
operation-specific nonfiring triggers and original security/search_path are
retained. Rowcount/CAS/exception/lock scope proof remains open. Source declaration
presence is not complete DML semantic proof or observed disposable catalog state.

Source indexing is metadata lookup for dependencies; unrelated function bodies
were not semantically analyzed. No live SQL, positive wrapper, native source
change, canonical context/key/time or numeric policy adoption occurred.

The prior 316 bundle ledger is preserved. No candidate is silently promoted and
no unrelated object is declared unreachable merely because absent from a graph.
Closure denominator remains UNKNOWN; fixture/Room readiness remains NO.

Primary references: [PG variadic SQL functions](https://www.postgresql.org/docs/18/xfunc-sql.html),
[function resolution](https://www.postgresql.org/docs/18/typeconv-func.html),
[PG18.4 cast declarations](https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/include/catalog/pg_cast.dat).
The downloaded catalog declarations are offline metadata, not a live catalog or
PG18.4 execution claim. Parser grammar remains PG18.6 and is only a syntax tool.
