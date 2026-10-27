"""Authorized resolution-assumption probes, confined to rolled-back test DDL."""
import json
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT,save

def prepare(r):
 raising="LANGUAGE plpgsql AS $x$ BEGIN RAISE EXCEPTION 'resolution lure reached'; END $x$;"
 tests=[
 dict(id='pg_temp_function_shadow',ddl='CREATE FUNCTION pg_temp.octet_length(bytea) RETURNS int4 '+raising,expression="pg_catalog.octet_length('\\x01'::pg_catalog.bytea)=1"),
 dict(id='public_overload',ddl='CREATE FUNCTION public.octet_length(bytea) RETURNS int4 '+raising,expression="pg_catalog.octet_length('\\x01'::pg_catalog.bytea)=1"),
 dict(id='operator_overload',ddl='CREATE FUNCTION public.probe_0090_add(int4,int4) RETURNS int4 '+raising+' CREATE OPERATOR public.+ (LEFTARG=int4,RIGHTARG=int4,FUNCTION=public.probe_0090_add);',expression='1+2=3'),
 dict(id='implicit_cast_lure',ddl='CREATE TYPE public.probe_0090_lure AS (value int4); CREATE FUNCTION public.probe_0090_cast(bytea) RETURNS public.probe_0090_lure LANGUAGE SQL AS $x$ SELECT ROW(1)::public.probe_0090_lure $x$; CREATE CAST (bytea AS public.probe_0090_lure) WITH FUNCTION public.probe_0090_cast(bytea) AS IMPLICIT; CREATE FUNCTION public.octet_length(public.probe_0090_lure) RETURNS int4 '+raising,expression="pg_catalog.octet_length('\\x01'::pg_catalog.bytea)=1"),
 dict(id='unknown_literal_lure',ddl='CREATE FUNCTION public.pg_char_to_encoding(text) RETURNS int4 '+raising,expression="pg_catalog.pg_char_to_encoding('UTF8')=6"),
 dict(id='shadow_type',ddl='CREATE TYPE public.text AS (value int4); CREATE TYPE pg_temp.text AS (value int4);',expression="pg_catalog.pg_typeof('x'::pg_catalog.text)='pg_catalog.text'::pg_catalog.regtype"),
 dict(id='altered_caller_search_path',ddl='CREATE FUNCTION public.probe_0090_add(int4,int4) RETURNS int4 '+raising+' CREATE OPERATOR public.+ (LEFTARG=int4,RIGHTARG=int4,FUNCTION=public.probe_0090_add);',expression="1+2=3 AND pg_catalog.current_setting('search_path')='pg_catalog, pg_temp'")]
 save('resolution-attack-v2.json',dict(tests=tests,helper_security=dict(owner='flooow_offline_audit_owner',security_definer=True,search_path=['pg_catalog','pg_temp'],invoker='test_0090_audit'),expected='All helper expressions TRUE; attacker lures never reached; canonical S04 never invoked',scope='Expected resolution assumptions only; not mutation/TOCTOU or final-consumer currentness invalidation proof',rollback_required=True,independent=True))

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());model=json.loads((OUT/'resolution-attack-v2.json').read_text());cases=[]
 for test in model['tests']:
  # Every fresh connection owns pg_temp. Only synthetic public objects named
  # here are touched, and ROLLBACK removes all DDL, grants and role changes.
  query='BEGIN; '+test['ddl']+' CREATE FUNCTION public.probe_0090_resolution() RETURNS bool LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $h$ BEGIN RETURN '+test['expression']+'; END $h$; ALTER FUNCTION public.probe_0090_resolution() OWNER TO flooow_offline_audit_owner; GRANT EXECUTE ON FUNCTION public.probe_0090_resolution() TO test_0090_audit; SET LOCAL ROLE test_0090_audit; SET LOCAL search_path=public,pg_temp,pg_catalog; SELECT public.probe_0090_resolution(); RESET ROLE; ROLLBACK;'
  output=sql(query).stdout.decode().splitlines();passed=output.count('t')==1 and output[-1]=='ROLLBACK';row=dict(name='resolution_'+test['id'],passed=passed,group='RESOLUTION_ATTACK',details=dict(output=output,rolled_back=True,canonical_S04_executed=False));cases.append(row);record['cases'].append(row);q.require(passed,row['name'])
 (folder/'resolution-attack-runtime.json').write_text(json.dumps(dict(cases=cases),indent=2)+'\n')
