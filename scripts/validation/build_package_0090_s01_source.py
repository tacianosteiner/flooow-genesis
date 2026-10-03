"""Offline S01 source generator. No database access or additional helper surface."""
import re
from pathlib import Path
import package_0090_source_gate as gate
from build_package_0090_q_source import deny
from package_0090_s01_readiness import ORGANIZATION_SQL, CONNECTION_SQL, Q_SENTINEL_SQL, target_query

NAMES = ('binding_id','plan_fingerprint','expected_incarnation_id','surface_version',
         'expected_history_digest','expected_acl_digest','expected_policy_digest')
TYPES = ('uuid','bytea','uuid','text','bytea','bytea','bytea')
MARKER = '-- Public S01: authenticated bound private readiness predicates.'


def bound_target():
    """Preserve every frozen join/filter; substitute only authenticated header fields."""
    fields = iter(('marketplace_order_id','organization_id','omie_connection_id',
                   'source_order_reference','integration_reference','mercado_livre_connection_id'))
    sql = re.sub(r'\?', lambda _: 'header_record.'+next(fields), target_query())
    for relation in sorted({r.split('.')[1] for r,c in __import__('package_0090_s01_readiness').target_columns()}, key=len, reverse=True):
        sql = re.sub(r'(?<![.\w])'+relation+r'\b', 'public.'+relation, sql)
    return sql


def build(source):
    p = source.split('AS $offline_p$',1)[1].split('$offline_p$;',1)[0]
    declarations = p.split('BEGIN',1)[0]
    for name in ('attempt_record','execution_record','pointer_record'):
        declarations = declarations.replace('    '+name+' record;\n','')
    declarations = declarations.replace('    principal_found pg_catalog.uuid;\n','')
    guard = '    SELECT h.binding_id'+p.split('    SELECT h.binding_id',1)[1].split('    -- C:',1)[0]
    end = guard.index('      INTO header_record')
    guard = '''    SELECT h.binding_id,h.deployment_id,h.deployment_incarnation_id,h.identity_slots,
           h.offline_surface_version,h.deadline_policy_version,h.deadline_policy_digest,
           h.plan_fingerprint,h.organization_id,h.mercado_livre_connection_id,h.omie_connection_id,
           h.marketplace_order_id,h.source_order_reference,h.integration_reference
''' + guard[end:]
    guard = guard.replace('slot_number=3','slot_number=4')
    initial = '''BEGIN
    IF $1 IS NULL OR $2 IS NULL OR $3 IS NULL OR $4 IS NULL OR $5 IS NULL OR $6 IS NULL OR $7 IS NULL
       OR $1='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR $3='00000000-0000-0000-0000-000000000000'::pg_catalog.uuid
       OR pg_catalog.octet_length($2)<>32 OR pg_catalog.octet_length($5)<>32
       OR pg_catalog.octet_length($6)<>32 OR pg_catalog.octet_length($7)<>32 OR $4<>'0090-v1'
       OR pg_catalog.current_setting('transaction_isolation')<>'repeatable read'
       OR pg_catalog.current_setting('transaction_read_only')<>'on' THEN
        RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
    END IF;
'''
    time = '''    database_now := pg_catalog.clock_timestamp();
''' + deny('policy_record.policy_digest<>$7 OR NOT pg_catalog.isfinite(database_now)\n'
       '       OR NOT pg_catalog.isfinite(policy_record.effective_from) OR database_now<policy_record.effective_from\n'
       '       OR NOT pg_catalog.isfinite(ready_record.watchdog_checked_at) OR database_now<ready_record.watchdog_checked_at\n'
       '       OR EXTRACT(EPOCH FROM(database_now-ready_record.watchdog_checked_at))*1000000>policy_values[23]\n'
       '       OR EXTRACT(EPOCH FROM(database_now-pg_catalog.transaction_timestamp()))*1000000>policy_values[19]')
    predicates = ''
    for sql in (ORGANIZATION_SQL,*CONNECTION_SQL,bound_target()):
        predicates += '    '+sql.replace('SELECT ', 'SELECT ',1).replace('\n','\n    ')+' INTO predicate_ready;\n'
        predicates += deny('predicate_ready IS NOT TRUE')
    # The frozen EXISTS remains unchanged. An independent readiness cardinality
    # requirement rejects ambiguity without changing the producer's identity join.
    counted = bound_target().replace('SELECT EXISTS(SELECT 1','SELECT pg_catalog.count(*)=1',1).rstrip()[:-1]
    predicates += '    '+counted.replace('\n','\n    ')+' INTO predicate_ready;\n'+deny('predicate_ready IS NOT TRUE')
    signature = ','.join('pg_catalog.'+t for t in TYPES)
    return MARKER+'\nCREATE FUNCTION public.offline_preflight(\n    '+',\n    '.join(n+' pg_catalog.'+t for n,t in zip(NAMES,TYPES))+'''
) RETURNS pg_catalog.bytea
LANGUAGE plpgsql STABLE SECURITY DEFINER CALLED ON NULL INPUT
SET search_path=pg_catalog,pg_temp
AS $offline_s01$
'''+declarations+'    predicate_ready pg_catalog.bool;\n'+initial+guard+time+predicates+'    RETURN '+Q_SENTINEL_SQL+''';
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION USING ERRCODE='P0017',MESSAGE='ACCESS_DENIED';
END;
$offline_s01$;
ALTER FUNCTION public.offline_preflight('''+signature+') OWNER TO flooow_offline_audit_owner;\nREVOKE ALL ON FUNCTION public.offline_preflight('+signature+') FROM PUBLIC;\n'


if __name__=='__main__':
    source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig').split(MARKER,1)[0].rstrip()
    (gate.ROOT/gate.V043).write_text(source+'\n\n'+build(source),encoding='utf-8')
