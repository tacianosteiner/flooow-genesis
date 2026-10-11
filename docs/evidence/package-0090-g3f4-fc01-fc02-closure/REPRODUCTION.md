# Disposable closure entrypoints

Scope: TEST_ONLY_NONCANONICAL. No canonical or numeric authority.

The active successor is `scripts/validation/package_0090_population_qualification`.
The preceding census and quarantine directories are preserved dependencies and
historical evidence, not the current runtime PASS denominator. Carried legacy
orchestrators and source-preparation scripts are not active final entrypoints.

From an exact-byte checkout (`core.autocrlf=false`), with the pinned local image,
Docker and the recorded toolchain/header available:

```powershell
python docs/evidence/package-0090-g3f4-fc01-fc02-closure/run_awake.py <fresh-batch-name>
python docs/evidence/package-0090-g3f4-fc01-fc02-closure/reconcile_final.py <fresh-batch-name>
python docs/evidence/package-0090-g3f4-fc01-fc02-closure/closure_report.py <fresh-batch-name>
```

Never reuse an evidence directory. The final mission entrypoint refuses source
drift, wrong branch/head, staged/dirty tracked work or historical hash mismatch.
Its baseline is the recorded input HEAD; a future post-publication rehearsal
requires a new separately recorded input baseline rather than silently editing
that immutable expectation. Individual development runs must pass an explicit
`build.py --output <fresh-directory> --scenario-module <module>`.

The runtime has no published port, network, host mount, canonical database or
production credentials. Synthetic private Ed25519 keys stay in container tmpfs;
cleanup erases them and removes owned labeled resources. Do not run unrelated
historical final runners, canonical ceremonies or source-generating preparers.

`fc01-fc02-final-03` is the sole final denominator. `final-01` predates additional
instrumentation. `final-02` has a literal harness publication error and is
invalidated by source drift. Neither contributes inherited PASS.

Frozen-source execution means actual unchanged V043 submitted to PostgreSQL and
its unconditional first-statement 55000 observed. It does not mean positive
wrapper execution. The matching source security review retains that fence;
fixture changes cannot satisfy an unconditional raise. No bypass is authorized.
