# Bounded S03 integration continuation

Evolves the existing fixed acquisition/consumer seam; not a second source,
ledger, authority or reconciliation service. No default production bridge.

The decoder and pair constraint reconstruction consume only bounded private
S03OBSE2 evidence. Hash validity is not origin authentication or acceptance.
Expected bindings must be independently held; they cannot be recovered from
candidate claims. Protected issuer/bootstrap, approved source membership,
immutable owner publication and native channel custody remain separate
prerequisites. Unavailable prerequisites must remain NOT_ESTABLISHED.

No component in this directory may create signing roots, accept sources from
five nonempty fields or status strings, infer historical membership, publish
the four canonical inputs before independent acceptance, or self-certify.
