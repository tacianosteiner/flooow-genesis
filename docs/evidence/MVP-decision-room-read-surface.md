# MVP Decision Room read surface

The case list now opens the existing governed Decision Room projection. The
browser preserves blocked authority, unquantified amounts, decimal strings and
source diagnostics. Failed list/signal reads remain unavailable rather than
becoming an empty list, zero count or absence of signals. Detail requests are
read-only, cancellable and protected against late responses from another case.

The HTTP integration test composes the production projection service with real
PostgreSQL repositories in a fresh disposable container. Its synthetic domain
assessment enters through the existing atomic assessment/case lineage commit;
it does not establish canonical economic source authority. Missing economic
authority remains `BLOCKED` / `NOT_ASSEMBLED`, with a null leakage total.
Repeated GETs preserve complete case and lineage rows and leave the ledger
empty. Unauthenticated access is rejected; another authenticated organization
cannot retrieve the case, including with a forged organization header.

Validation on 2026-11-17:

- Web lint, production build and 25 tests passed.
- Complete API suite: 70 tests, zero failures/errors/skips.
- Two selected PostgreSQL Decision Room persistence test classes passed.
- Disposable schema migration/repeat/validation through V042 passed.

The three PostgreSQL integration tests explicitly target V042 because this
product schema predates V043. Canonical V043 remains present, unchanged and
fenced. Default production migration configuration is unchanged. Containers
bind only disposable loopback ports and are stopped after tests.

Reproduce the product checks:

```powershell
cd applications/economic-decision-room-web
npm run lint
npm run build
npm test -- --run
cd ../..
./gradlew.bat :applications:marketplace-operations-api:test --offline --no-daemon
./gradlew.bat :applications:marketplace-operations-persistence-postgres:test --tests '*PostgresEconomicDecisionRoomAuthoritySourceTest' --tests '*PostgresEconomicDecisionRoomReconciliationAssessmentSourceTest' --offline --no-daemon
```

This change is authorized by the prospective
`FLOOOW_MVP_AUTONOMOUS_COMPLETION_AUTHORITY_V1` mandate. It does not establish
S03 source acceptance, E1-E4, canonical witnesses, N1, V2, browser E2E or MVP
finalization. Native candidate evidence remains separate from this product
change. Existing historical authority gaps remain `NOT_ESTABLISHED`.
