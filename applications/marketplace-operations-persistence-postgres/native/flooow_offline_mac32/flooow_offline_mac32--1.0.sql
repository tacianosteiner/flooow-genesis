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
