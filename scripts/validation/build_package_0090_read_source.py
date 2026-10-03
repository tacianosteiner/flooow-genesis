"""Offline remaining auditor wrapper generation; no database connection."""
from build_package_0090_s01_source import build as s01_build
import package_0090_source_gate as gate

MARKER='-- Public remaining auditor wrappers:'
TYPES=('uuid','bytea','uuid','text')
NAMES=('binding_id','plan_fingerprint','expected_incarnation_id','surface_version')
OWNER='flooow_offline_audit_owner'


def guard(source, extra_header=()):
    body=s01_build(source).split('AS $offline_s01$',1)[1].split('$offline_s01$;',1)[0]
    declarations=body.split('BEGIN',1)[0].replace('    predicate_ready pg_catalog.bool;\n','')
    checks='    SELECT h.binding_id'+body.split('    SELECT h.binding_id',1)[1].split('    SELECT pg_catalog.count(*)=1',1)[0]
    checks=checks.replace('policy_record.policy_digest<>$7 OR ','')
    # S02-S04 R does not require domain-target readiness or preflight digests.
    first=checks.index('      INTO header_record')
    checks='''    SELECT h.binding_id,h.deployment_id,h.deployment_incarnation_id,h.identity_slots,
           h.offline_surface_version,h.deadline_policy_version,h.deadline_policy_digest,
           h.plan_fingerprint'''+''.join(',h.'+n for n in extra_header)+'\n'+checks[first:]
    initial='''BEGIN
    IF $1 IS NULL OR $2 IS NULL OR $3 IS NULL OR $4 IS NULL
       OR $1='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR $3='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR pg_catalog.octet_length($2)<>32 OR $4<>'0090-v1'
       OR pg_catalog.current_setting('transaction_isolation')<>'repeatable read'
       OR pg_catalog.current_setting('transaction_read_only')<>'on' THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
'''
    return declarations,initial+checks


def wrapper(name,returns,declarations,body,tag):
    signature=','.join('pg_catalog.'+t for t in TYPES)
    return 'CREATE FUNCTION public.'+name+'(\n    '+',\n    '.join(n+' pg_catalog.'+t for n,t in zip(NAMES,TYPES))+') RETURNS '+returns+'''
LANGUAGE plpgsql STABLE SECURITY DEFINER CALLED ON NULL INPUT
SET search_path=pg_catalog,pg_temp
AS $offline_'''+tag+'$\n'+declarations+body+'''
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
END;
$offline_'''+tag+'$;\nALTER FUNCTION public.'+name+'('+signature+') OWNER TO '+OWNER+';\nREVOKE ALL ON FUNCTION public.'+name+'('+signature+') FROM PUBLIC;\n'


def build(source):
    declarations,checks=guard(source)
    history='''    RETURN QUERY SELECT h.installed_rank,h.version,h.type,h.script,h.checksum,h.success
      FROM public.flyway_schema_history h ORDER BY h.installed_rank;
    IF EXTRACT(EPOCH FROM(pg_catalog.clock_timestamp()-pg_catalog.transaction_timestamp()))*1000000>policy_values[19] THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
    RETURN;
'''
    returns='TABLE(installed_rank pg_catalog.int4,version pg_catalog.text,type pg_catalog.text,script pg_catalog.text,checksum pg_catalog.int4,success pg_catalog.bool)'
    return MARKER+' S04 bound complete history; no truncation/repair.\n'+wrapper('offline_read_history',returns,declarations,checks+history,'s04')


if __name__=='__main__':
    source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig').split(MARKER,1)[0].rstrip()
    (gate.ROOT/gate.V043).write_text(source+'\n\n'+build(source),encoding='utf-8')
