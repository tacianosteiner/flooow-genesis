"""Authorized corrected-source helper proof; never invokes canonical S04."""
import json
from pathlib import Path
import package_0090_source_closure as q
OUT=q.ROOT/'docs/evidence/package-0090-s04-return-tuple-correction-applied'

def last_json(result):
    rows=[line for line in result.stdout.decode().splitlines() if line.startswith('{')]
    q.require(len(rows)==1,'Expected one JSON result'); return json.loads(rows[0])


def qualify(sql,run,container,folder,record,fixture,runtime_work):
    contract=json.loads((OUT/'return-contract.json').read_text()); rows=[]
    def case(name,passed,detail):
        row=dict(name=name,passed=bool(passed),group='CANDIDATE',details=detail)
        rows.append(row); record['cases'].append(row); q.require(passed,name)
    declaration=contract['return_declaration']; query=contract['candidate_query']
    control='CREATE FUNCTION pg_temp.test_0090_old_raw() '+declaration+' LANGUAGE plpgsql AS $raw$ BEGIN RETURN QUERY '+contract['old_query']+'; END $raw$; CREATE FUNCTION pg_temp.test_0090_old_result() RETURNS pg_catalog.text LANGUAGE plpgsql AS $raw$ BEGIN PERFORM * FROM pg_temp.test_0090_old_raw(); RETURN \'00000\'; EXCEPTION WHEN OTHERS THEN RETURN SQLSTATE; END $raw$; SELECT pg_temp.test_0090_old_result();'
    old_state=sql(control).stdout.decode().splitlines()[-1]
    case('old_raw_control_reproduces_42804',old_state=='42804',old_state)
    helper='CREATE FUNCTION pg_temp.test_0090_qualified_candidate() '+declaration+' LANGUAGE plpgsql AS $candidate$ BEGIN RETURN QUERY '+query+'; END $candidate$;'
    capture="CREATE FUNCTION pg_temp.test_0090_candidate_result() RETURNS pg_catalog.jsonb LANGUAGE plpgsql AS $capture$ DECLARE data pg_catalog.jsonb; ranks pg_catalog.int4[]; BEGIN SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(t)-'delivery_ordinal' ORDER BY delivery_ordinal),pg_catalog.array_agg(t.installed_rank ORDER BY delivery_ordinal) INTO data,ranks FROM pg_temp.test_0090_qualified_candidate() WITH ORDINALITY AS t(installed_rank,version,type,script,checksum,success,delivery_ordinal); RETURN pg_catalog.jsonb_build_object('sqlstate','00000','rows',data,'delivered_ranks',ranks); EXCEPTION WHEN OTHERS THEN RETURN pg_catalog.jsonb_build_object('sqlstate',SQLSTATE,'message',SQLERRM); END $capture$; SELECT pg_temp.test_0090_candidate_result();"
    result=last_json(sql(helper+capture))
    case('qualified_candidate_success_00000',result['sqlstate']=='00000',result['sqlstate'])
    case('qualified_candidate_exact_42_rows_all_six_fields',result.get('rows')==contract['independent_expected_history'],dict(rows=len(result.get('rows',[])),comparison='Exact independently frozen six-field values'))
    case('qualified_candidate_rank_order_1_to_42',result.get('delivered_ranks')==list(range(1,43)),'WITH ORDINALITY retains actual function delivery order; never sort by installed_rank to establish this assertion')
    for col in ['version','type','script']:
        got=sql("SELECT pg_catalog.bool_and(pg_catalog.pg_typeof(h.%s::pg_catalog.text)='pg_catalog.text'::pg_catalog.regtype),pg_catalog.bool_and(pg_catalog.varcharsend(h.%s) IS NOT DISTINCT FROM pg_catalog.textsend(h.%s::pg_catalog.text)) FROM public.flyway_schema_history h;"%(col,col,col)).stdout.decode().strip()
        case('candidate_type_and_binary_content_'+col,got=='t|t',dict(observed=got,comparison='Raw varchar binary send vs text binary send for every source row'))
    case('NULL_preserved',sql('SELECT (NULL::pg_catalog.varchar)::pg_catalog.text IS NULL;').stdout.strip()==b't','No coalesce/default/normalization')
    case('expected_database_encoding_UTF8',sql('SHOW server_encoding;').stdout.strip()==b'UTF8','Compare binary textual contents under approved encoding')
    q.require(sql("SELECT to_regtype('public.text') IS NULL;").stdout.strip()==b't','Do not replace existing public.text')
    shadow_script="CREATE TYPE public.text AS (value pg_catalog.int4); CREATE TYPE pg_temp.text AS (value pg_catalog.int4); SET search_path=pg_temp,public,pg_catalog; "+helper+" SELECT pg_catalog.jsonb_build_object('unqualified_oid',pg_catalog.to_regtype('text')::pg_catalog.oid,'qualified_oid',pg_catalog.to_regtype('pg_catalog.text')::pg_catalog.oid,'all_text', (SELECT pg_catalog.bool_and(pg_catalog.pg_typeof(h.version::pg_catalog.text)='pg_catalog.text'::pg_catalog.regtype AND pg_catalog.pg_typeof(h.type::pg_catalog.text)='pg_catalog.text'::pg_catalog.regtype AND pg_catalog.pg_typeof(h.script::pg_catalog.text)='pg_catalog.text'::pg_catalog.regtype) FROM public.flyway_schema_history h),'rows',(SELECT pg_catalog.jsonb_agg(t ORDER BY installed_rank) FROM pg_temp.test_0090_qualified_candidate() t)); DROP TYPE public.text;"
    shadow=last_json(sql(shadow_script))
    case('qualified_cast_resists_temp_and_public_type_shadow',int(shadow['unqualified_oid'])!=int(shadow['qualified_oid']) and int(shadow['qualified_oid'])==25 and shadow['all_text'] and shadow['rows']==contract['independent_expected_history'],dict(unqualified_type_oid=shadow['unqualified_oid'],qualified_text_oid=shadow['qualified_oid'],rows=len(shadow['rows']),search_path='pg_temp,public,pg_catalog',public_type_removed=True))
    canonical=q.git('show','HEAD:'+q.V043.relative_to(q.ROOT).as_posix())
    case('canonical_and_index_unchanged',q.sha(canonical)==q.SOURCE_HASH and q.V043.read_bytes().replace(b'\r\n',b'\n')==canonical,dict(canonical_sha256=q.sha(canonical),candidate_executed_only_in_pg_temp=True))
    (folder/'corrected-runtime.json').write_text(json.dumps(dict(cases=rows,old_raw_sqlstate=old_state,candidate=result,shadow_proof=shadow,corrected_types=['text','text','text'],canonical_S04_executed=False,qualified_candidate_helper_sql=helper),indent=2)+'\n')


