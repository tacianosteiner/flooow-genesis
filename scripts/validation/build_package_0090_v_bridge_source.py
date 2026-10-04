"""Approved source-only Ed25519 V bridge; never connects to a database."""
import package_0090_source_gate as gate

MARKER='-- Approved V Ed25519 bridge: no A/private-native access.'
END_MARKER='-- End approved V Ed25519 bridge.'
NAME='offline_internal_canonical_spki_ed25519_verify'
TYPES=('bytea',)*3
OWNER=gate.OWNERS['V']
NATIVE='canonical_spki_ed25519_verify'
GRANTS={('public',NAME,TYPES,gate.OWNERS['A']),('offline_crypto',NATIVE,TYPES,OWNER)}


def build():
    return MARKER+'''
-- Existing crypto dependency inspection above requires D-only native ACLs
-- before the newly approved two V grants below. This is no general ACL repair.
DO $$
DECLARE
    native_oid pg_catalog.oid;
    deployment_oid pg_catalog.oid;
BEGIN
    SELECT r.oid INTO deployment_oid FROM pg_catalog.pg_roles r WHERE r.rolname='postgres';
    native_oid := pg_catalog.to_regprocedure('offline_crypto.canonical_spki_ed25519_verify(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea)');
    IF native_oid IS NULL OR NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc p
        JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
        JOIN pg_catalog.pg_language l ON l.oid=p.prolang
        JOIN pg_catalog.pg_depend d ON d.classid='pg_catalog.pg_proc'::pg_catalog.regclass
             AND d.objid=p.oid AND d.deptype='e' AND d.refclassid='pg_catalog.pg_extension'::pg_catalog.regclass
        JOIN pg_catalog.pg_extension e ON e.oid=d.refobjid
        WHERE p.oid=native_oid AND p.proowner=deployment_oid AND n.nspname='offline_crypto'
          AND l.lanname='c' AND p.prokind='f' AND p.provolatile='i'
          AND p.proisstrict AND NOT p.prosecdef AND NOT p.proretset AND p.proparallel='s'
          AND p.pronargdefaults=0 AND p.provariadic=0 AND p.proargnames IS NULL
          AND p.proallargtypes IS NULL AND p.proargmodes IS NULL AND p.proconfig IS NULL
          AND p.prorettype='pg_catalog.bool'::pg_catalog.regtype
          AND p.probin='$libdir/flooow_offline_mac32' AND p.prosrc='canonical_spki_ed25519_verify'
          AND e.extname='flooow_offline_mac32' AND e.extversion='1.0' AND e.extowner=deployment_oid
    ) OR EXISTS (
        SELECT 1 FROM pg_catalog.pg_proc p CROSS JOIN LATERAL
            pg_catalog.aclexplode(COALESCE(p.proacl,pg_catalog.acldefault('f',p.proowner))) a
        WHERE p.oid=native_oid AND (a.grantee<>deployment_oid OR a.is_grantable AND a.grantee<>p.proowner)
    ) THEN
        RAISE EXCEPTION 'Approved exact private Ed25519 deployment prerequisite is missing or unsafe';
    END IF;
END;
$$;
GRANT USAGE ON SCHEMA offline_crypto TO flooow_offline_verification_owner;
GRANT EXECUTE ON FUNCTION offline_crypto.canonical_spki_ed25519_verify(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea) TO flooow_offline_verification_owner;

CREATE FUNCTION public.offline_internal_canonical_spki_ed25519_verify(
    subject_public_key_info_der pg_catalog.bytea,
    canonical_signature_preimage_bytes pg_catalog.bytea,
    signature_bytes pg_catalog.bytea
) RETURNS pg_catalog.bool
LANGUAGE plpgsql IMMUTABLE STRICT PARALLEL SAFE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp
AS $offline_v_ed25519$
BEGIN
    RETURN offline_crypto.canonical_spki_ed25519_verify($1,$2,$3);
END;
$offline_v_ed25519$;
ALTER FUNCTION public.offline_internal_canonical_spki_ed25519_verify(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea) OWNER TO flooow_offline_verification_owner;
REVOKE ALL ON FUNCTION public.offline_internal_canonical_spki_ed25519_verify(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.offline_internal_canonical_spki_ed25519_verify(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea) TO flooow_offline_audit_owner;
'''+END_MARKER+'\n'


def install(source):
    if MARKER in source:
        start=source.index(MARKER);end=source.index(END_MARKER,start)+len(END_MARKER)
        return source[:start]+build().rstrip()+source[end:]
    from build_package_0090_s01_source import MARKER as s01_marker
    point=source.index(s01_marker)
    return source[:point]+build()+'\n'+source[point:]


if __name__=='__main__':
    path=gate.ROOT/gate.V043
    path.write_text(install(path.read_text(encoding='utf-8-sig')),encoding='utf-8')
