# Authority join graph — semantic closure HOLD

AUTHORITY-JOIN-GRAPH.json defines 40 exact model joins, all required edge fields and no null/wildcard matching. Model relations are explicitly labelled and are not claimed as SQL table names. SOURCE-OBLIGATIONS.json preserves actual relation DDL, foreign keys and function bodies/calls across all 43 migrations.

The model covers identity -> live role catalog; allocation -> anchor/registry; binding -> readiness/policy/pointer; pointer -> attempt -> execution -> admission; approval -> original attestation -> accepted consumption; receipt -> execution/effect; ownership -> execution; reconciliation -> binding; tenant/source/principal/credential/grant/decision lineage.

The complete typed SQL predicate and original frame witness mapping is not yet independently certified. Lexical inventory is deliberately not called a complete semantic join graph. Every runtime-required join must be mapped to its actual relation/column keys and source guard before replacing this HOLD.
