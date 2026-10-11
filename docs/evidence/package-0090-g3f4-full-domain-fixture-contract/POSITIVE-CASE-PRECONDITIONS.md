# Thirteen case contracts

Machine-readable exact reviewed wrapper signatures and all required dimensions are in POSITIVE-CASE-PRECONDITIONS.json. These are candidate prerequisites, not execution authority. Full source predicate witness coverage remains HOLD.

- claim: CLAIMED; original absolute lease; one pointer; no effects
- verification: Original signed bytes verified; exact fresh ATTESTATION_VERIFIED receipt
- admission: One ISSUED admission bound to exact credential/grant revisions
- ownership_acquisition: One OWNED execution and possession digest; distinct claim receipt
- effect_transition: Each actual committed stage appends its own exact receipt; no prefilled effects
- terminal_transition: Actual decision -> EFFECTS_COMPLETE; admission CONSUMED; execution RELEASED; reconciliation REQUIRED
- retry_replay_denial: Exact denial/non-replay result for selected overload; no renewed lease or second effect
- ownership_retention: Failure leaves ownership retained; no synthetic release; reconciliation evidence preserved
- ownership_release: Release only atomic with actual decision/effect and reconciliation REQUIRED
- reconciliation_required: Actual committed effect produces REQUIRED; no invented administrative completion
- reconciliation_completion: Read-only full snapshot then separate disposable administrative independent recomputation; never auditor UPDATE
- full_authority_joins: Every exact source/approval/signature/consumption/authorization join; missing one denies
- runtime_consumption: Whole successor, exact isolated target, actual four service sessions, full fresh sequence; no fragment execution
