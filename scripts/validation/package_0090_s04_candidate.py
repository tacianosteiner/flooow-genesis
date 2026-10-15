"""Pre-authorization candidate only: canonical V043 is never written or executed."""
import difflib
import json
import re
import zlib
from pathlib import Path
import package_0090_source_closure as q
import package_0090_full_reachable as raw

BASELINE='c4ce67ae68e9b06d74fbd41c285f5ed87a679984'
OUT=q.ROOT/'docs/evidence/package-0090-s04-return-tuple-correction-candidate'


def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def crc(data):
    result=0
    for line in data.decode('utf-8-sig').splitlines(): result=zlib.crc32(line.encode(),result)
    return result if result<2**31 else result-2**32
def clean(node):
    if isinstance(node,dict): return {k:clean(v) for k,v in node.items() if k not in ['location','stmt_location','stmt_len','list_start','list_end','arg_location']}
    if isinstance(node,list): return [clean(x) for x in node]
    return node


def prepare(parser):
    OUT.mkdir(exist_ok=True)
    canonical=q.git('show',BASELINE+':'+q.V043.relative_to(q.ROOT).as_posix())
    q.require(q.sha(canonical)==q.SOURCE_HASH and q.V043.read_bytes().replace(b'\r\n',b'\n')==canonical,'Canonical drift')
    start=canonical.index(b'CREATE FUNCTION public.offline_read_history(')
    end=canonical.index(b'$offline_s04$;',start)+len(b'$offline_s04$;')
    function=canonical[start:end]
    query_start=function.index(b'RETURN QUERY ')
    query_end=function.index(b';',query_start)+1
    old_query=function[query_start:query_end]
    new_query=old_query
    for col in ['version','type','script']:
        token=('h.'+col).encode(); q.require(old_query.count(token)==1,'Source projection not unique')
        new_query=new_query.replace(token,token+b'::pg_catalog.text')
    q.require(canonical.count(old_query)==1,'Whole source return statement not unique')
    candidate=canonical.replace(old_query,new_query)
    declaration=function[function.index(b'RETURNS TABLE('):function.index(b'\nLANGUAGE')]
    for name,content in [('S04-CURRENT-FUNCTION.sql',function),('S04-CURRENT-RETURN-QUERY.sql',old_query),('S04-CANDIDATE-RETURN-QUERY.sql',new_query),('S04-RETURN-DECLARATION.sql',declaration)]:
        (OUT/name).write_bytes(content+b'\n')
    rel=q.V043.relative_to(q.ROOT).as_posix()
    patch=''.join(difflib.unified_diff(canonical.decode().splitlines(True),candidate.decode().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel,n=3))
    patch_path=OUT/'V043-S04-RETURN-TUPLE-CANDIDATE.patch'; patch_path.write_bytes(patch.encode())
    q.require(sum(line.startswith('-') and not line.startswith('---') for line in patch.splitlines())==1,'Unexpected replaced physical line count')
    # Read-only applicability check against the unchanged Git index. --check
    # never applies or stages a patch. Verify the index entry byte-for-byte.
    index_before=q.git('ls-files','--stage',rel)
    checked=q.command(['git','apply','--check','--cached',str(patch_path)],check=False)
    q.require(checked.returncode==0 and q.git('ls-files','--stage',rel)==index_before,'Patch check failed or index changed')
    old_tree=json.loads(parser(canonical.decode()))['stmts']; new_tree=json.loads(parser(candidate.decode()))['stmts']
    q.require(len(old_tree)==len(new_tree),'Statement count changed')
    changed=[]
    for i,(old,new) in enumerate(zip(old_tree,new_tree)):
        if clean(old['stmt'])!=clean(new['stmt']): changed.append(i)
    q.require(len(changed)==1,'More than one definition changed')
    old_f=old_tree[changed[0]]['stmt']['CreateFunctionStmt']; new_f=new_tree[changed[0]]['stmt']['CreateFunctionStmt']
    def without_body(f):
        return clean({**f,'options':[x for x in f['options'] if x['DefElem']['defname']!='as']})
    q.require(without_body(old_f)==without_body(new_f),'API/attributes changed')
    old_select=old_query.decode().removeprefix('RETURN QUERY ').removesuffix(';')
    new_select=new_query.decode().removeprefix('RETURN QUERY ').removesuffix(';')
    a=clean(json.loads(parser(old_select))['stmts'][0]['stmt']['SelectStmt'])
    b=clean(json.loads(parser(new_select))['stmts'][0]['stmt']['SelectStmt'])
    for i in [1,2,3]:
        cast=b['targetList'][i]['ResTarget']['val']['TypeCast']
        q.require(cast['arg']==a['targetList'][i]['ResTarget']['val'],'Projection operand changed')
        q.require(cast['typeName']['names']==[{'String':{'sval':'pg_catalog'}},{'String':{'sval':'text'}}],'Cast target not exact')
        b['targetList'][i]['ResTarget']['val']=cast['arg']
    q.require(a==b,'Other SELECT/order/relation/columns changed')
    q.require(candidate.replace(new_query,old_query)==canonical,'Inverse source proof failed')
    metadata=dict(baseline=BASELINE,current_git_blob=q.git('rev-parse',BASELINE+':'+rel).decode().strip(),current_Git_LF_sha256=q.sha(canonical),working_bytes_sha256=q.sha(q.V043.read_bytes()),function_sha256=q.sha(function),function_start_line=canonical[:start].count(b'\n')+1,function_end_line=canonical[:end].count(b'\n')+1,return_query_sha256=q.sha(old_query),candidate_return_query_sha256=q.sha(new_query),candidate_Git_LF_sha256=q.sha(candidate),candidate_full_source_not_written=True,index_entry_unchanged=True,patch_applicability_check_only=True)
    save('source-freeze.json',metadata)
    save('candidate-source-hash.json',dict(current=q.sha(canonical),hypothetical_candidate=q.sha(candidate),canonical_replaced=False))
    save('candidate-diff-audit.json',dict(files=1,functions=1,expression_changes=3,replaced_physical_lines=1,diff_added_lines=1,diff_removed_lines=1,return_declaration_changed=False,argument_signature_changed=False,fence_changed=False,other_V043_body_changed=False,API_AST_equal=True,SELECT_AST_equal_after_removing_only_expected_three_TypeCast_nodes=True,physical_line_count_note='All three original result expressions occupy one physical source line; forcing three changed lines would add whitespace churn',patch_sha256=q.sha(patch_path.read_bytes()),checked_not_applied=True))
    save('api-identity.json',dict(changed=False,attributes=without_body(old_f),ownership_and_EXECUTE_statements_unchanged=True,exceptions_and_all_guard_bytes_unchanged=True,full_file_inverse_diff_proven=True))
    old_expected=json.loads((raw.OUT/'return-tuple-expectation.json').read_text())
    save('return-contract.json',dict(declared_return_types=old_expected['canonical_declared_types'],independent_Flyway_projection=old_expected['independent_Flyway_projection'],independent_expected_history=old_expected['expected_history'],Flyway_jar_sha256=old_expected['Flyway_jar_sha256'],mismatch_positions=['version','type','script'],old_query=old_select,candidate_query=new_select,return_declaration=declaration.decode(),strategy='EXPLICIT_PG_CATALOG_TEXT_PROJECTION',alternative_review=dict(unqualified_cast='Shorter but caller search_path sensitive; rejected by requirement',CAST_AS_form='Same semantics, more syntax; no narrower authority footprint',return_varchar_API='Changes declared contract; forbidden',alter_Flyway_history='Changes provider/storage; forbidden',choice='Three qualified postfix casts preserve API and are the minimal expression-only correction')))
    save('migration-impact.json',dict(old_source_sha256=q.sha(canonical),candidate_source_sha256=q.sha(candidate),old_Flyway_signed_CRC32=crc(canonical),candidate_Flyway_signed_CRC32=crc(candidate),checksum_changed=crc(canonical)!=crc(candidate),canonical_execution_history='No canonical application in retained qualification evidence; shared/production history not independently inspected or contacted',historical_denial_probe_not_complete_migration=True,release_coordination='Explicit authority required before source adoption; rebaseline derived-body/source/semantic/ACL/native expected hashes, input manifests and release ledger. No Flyway repair, retrospective mutation or promotion authorized',canonical_unexecuted_is_not_mutation_authority=True))


def last_json(result):
    rows=[line for line in result.stdout.decode().splitlines() if line.startswith('{')]
    q.require(len(rows)==1,'Expected one JSON result'); return json.loads(rows[0])


def qualify(sql,run,container,folder,record,fixture,runtime_work):
    record['recipe_hashes'][Path(raw.__file__).name]=q.sha(Path(raw.__file__).read_bytes())
    raw.qualify(sql,run,container,folder,record,fixture,runtime_work)
    contract=json.loads((OUT/'return-contract.json').read_text()); rows=[]
    def case(name,passed,detail):
        row=dict(name=name,passed=bool(passed),group='CANDIDATE',details=detail)
        rows.append(row); record['cases'].append(row); q.require(passed,name)
    declaration=contract['return_declaration']; query=contract['candidate_query']
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
    canonical=q.git('show',BASELINE+':'+q.V043.relative_to(q.ROOT).as_posix())
    case('canonical_and_index_unchanged',q.sha(canonical)==q.SOURCE_HASH and q.V043.read_bytes().replace(b'\r\n',b'\n')==canonical,dict(canonical_sha256=q.sha(canonical),candidate_executed_only_in_pg_temp=True))
    (folder/'candidate-runtime.json').write_text(json.dumps(dict(cases=rows,candidate=result,shadow_proof=shadow,corrected_types=['text','text','text'],canonical_S04_executed=False,qualified_candidate_helper_sql=helper),indent=2)+'\n')


if __name__=='__main__':
    import sys
    sys.path.insert(0,str(Path.home()/'AppData/Local/Temp/room-lineage-sql-parser'))
    from pglast.parser import parse_sql_json
    prepare(parse_sql_json)
