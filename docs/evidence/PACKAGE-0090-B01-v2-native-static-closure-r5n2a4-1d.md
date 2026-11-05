# Package 0090 R5N.2A4.1D — producer execution plan design

This is a new normative design, not recovered implementation, graph closure, source privilege proof or Reader ACL derivation. G1 and G2 define eight fixed entry contracts. The selected authority model is D: existing authenticated self-session LOGIN bridge plus a fixed acquisition membrane, with separate pure transforms.

The eight boundaries are ordinary catalog projection, public stats roster, self-session bridge, config sanitization, stored-body hashing, frame assembly, config predicate evaluation and graph predicate evaluation. Different source authority, principal, transformation or predicate families remain separate. No per-field steps are created. All 146 field definitions and 26 predicate expressions are frozen inputs in G1/G2.

The source membrane is an explicit proposed per-operation catalog-read capability, not a claim that a SQL INVOKER function can access inaccessible columns. It must retain caller identity, gate the enrolled session before exact catalog reads, avoid raw grants, and return only approved projected values. Bare INVOKER SQL requiring raw SELECT, owner-mediated views and SECURITY DEFINER are rejected implementations. A backend source primitive or equivalently confined mechanism must prove its complete internal authorization and effect expansion at binding; the design does not choose a programming language or grant privileges.

Raw config and stored-body bytes are potentially sensitive. Their accepted sanitization/digest processing occurs inside the trusted acquisition membrane, before Reader transport, memory, logs or diagnostics. Pure frame/effect evaluators receive only bounded immutable projected values and no DB credential. Secret/key stores and raw secret retrieval remain forbidden. The eight approved body digests are integrity outputs and never authority/effect evidence by themselves.

Protected stats fields remain NULL in the raw roster. The accepted own-session bridge supplies separately attributed selected facts under two independent observers; it does not broaden pg_stat visibility or add an eighth native participant. No pg_read_all_stats, superuser, BYPASSRLS, role membership or SD is required.

Every one of the existing 16 gaps has one terminal design path, but all remain OPEN_NOT_BOUND. The 17 predecessor closure failures are preserved and are not rerun as a graph closure suite here. Actual future source callsites, SQL ACL, physical authentication and source effect manifests remain acceptance obligations. Missing/unknown input or unsupported implicit call rejects before result publication; no optimistic no-effect conclusion.

Only this untracked design scope may change. Reader ACL and downstream gates remain unexecuted. See gate.json for measured final accounting, design-validation.json for design-only checks, independent-design-review.json for independent review and SHA256-MANIFEST.json for sealed checkout-byte hashes.
