CREATE FUNCTION offline_crypto.timing_safe_equal32(
    pg_catalog.bytea,
    pg_catalog.bytea
)
RETURNS pg_catalog.bool
AS 'MODULE_PATHNAME', 'timing_safe_equal32'
LANGUAGE C
IMMUTABLE
STRICT
PARALLEL SAFE
SECURITY INVOKER;

-- Private dependency. Separate deployment governance grants only V EXECUTE;
-- ordinary/public/service callers must never receive this native capability.
CREATE FUNCTION offline_crypto.canonical_spki_ed25519_verify(
    pg_catalog.bytea,
    pg_catalog.bytea,
    pg_catalog.bytea
)
RETURNS pg_catalog.bool
AS 'MODULE_PATHNAME', 'canonical_spki_ed25519_verify'
LANGUAGE C
IMMUTABLE
STRICT
PARALLEL SAFE
SECURITY INVOKER;

REVOKE ALL PRIVILEGES ON FUNCTION offline_crypto.canonical_spki_ed25519_verify(
    pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea
) FROM PUBLIC;
