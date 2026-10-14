"""Independent S04 call expectations from source and frozen PostgreSQL definitions.

Does not execute S04; expression types and catalog identity checks are not BOUND.
"""
import json
import re
import urllib.request
from pathlib import Path
import package_0090_source_closure as q

BASELINE='95ec5a3919d0e29ed291e0fcee7c1278482226bb'
OUT=q.ROOT/'docs/evidence/package-0090-effective-expectation-t10-fence'
ADDENDUM=q.ROOT/'docs/evidence/package-0090-test-activation-native-health-first-positive/s04-source-addendum.json'
PROVIDER='https://raw.githubusercontent.com/postgres/postgres/REL_18_4/src/include/catalog/'


def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def records(path):
    return [dict(re.findall(r"(\w+)\s*=>\s*'([^']*)'",part)) for part in re.findall(r'\{([^{}]+)\}',path.read_text())]


def download():
    folder=OUT/'postgres-18.4'; folder.mkdir(parents=True,exist_ok=True)
    for name in ['pg_proc.dat','pg_operator.dat','pg_cast.dat','pg_type.dat','pg_proc.h']:
        path=folder/name
        if not path.exists(): q.command(['curl.exe','--fail','--location','--retry','2','--max-time','30',PROVIDER+name,'--output',str(path)])
    save('provider-source-freeze.json',{p.name:dict(url=PROVIDER+p.name,sha256=q.sha(p.read_bytes())) for p in folder.iterdir() if p.is_file()})


def prepare():
    download()
    source=json.loads(ADDENDUM.read_text())
    procs=records(OUT/'postgres-18.4/pg_proc.dat')
    # These are exact declared local/parameter and selected-record types from S04.
    vars={'slot_cursor':'int4','slot_length':'int8','slot_oid':'int8','slot_name_length':'int8','slot_name':'text','slot_oids':'int8[]','slot_names':'text[]','slot_number':'int4','field_tag':'int4','byte_number':'int4','cursor_position':'int4','payload_length':'int8','domain_length':'int8','field_value':'numeric','policy_values':'int8[]','database_now':'timestamptz','header_record.identity_slots':'bytea','header_record.deadline_policy_version':'text','policy_record.policy_version':'text','policy_record.canonical_policy':'bytea','policy_record.policy_digest':'bytea','policy_record.effective_from':'timestamptz','ready_record.watchdog_checked_at':'timestamptz'}
    observed_types=[]
    def infer(node):
        if 'ColumnRef' in node:
            name='.'.join(x['String']['sval'] for x in node['ColumnRef']['fields'] if 'String' in x)
            q.require(name in vars,'Unknown exact local/record type: '+name); return vars[name]
        if 'ParamRef' in node: return {1:'uuid',2:'bytea',3:'uuid',4:'text'}[node['ParamRef']['number']]
        if 'A_Const' in node:
            c=node['A_Const']; return 'int4' if 'ival' in c else 'unknown' if 'sval' in c else 'bool' if 'boolval' in c else 'numeric'
        if 'TypeCast' in node:
            n=node['TypeCast']['typeName']; return '.'.join(x['String']['sval'] for x in n['names']).removeprefix('pg_catalog.')+('[]' if n.get('arrayBounds') else '')
        if 'FuncCall' in node:
            f=node['FuncCall']; name=f['funcname'][-1]['String']['sval']; args=[infer(x) for x in f.get('args',[])]
            return resolve(name,args)[1]
        if 'A_Expr' in node:
            e=node['A_Expr']; left=infer(e['lexpr']); right=infer(e['rexpr']); op=e['name'][0]['String']['sval']
            if op=='-' and left==right=='timestamptz': return 'interval'
            if left in ['int4','int8','numeric'] and right in ['int4','int8','numeric']: return max([left,right],key=['int4','int8','numeric'].index)
            raise RuntimeError('Unproven expression operator type '+str((left,op,right)))
        raise RuntimeError('Unproven expression type '+str(node)[:120])
    def resolve(name,args):
        normalized=['text' if x=='unknown' else x for x in args]
        if name in ['convert_to','convert_from']:
            q.require(args[1]=='unknown','Encoding-name argument differs from canonical literal')
            normalized[1]='name'
        if name=='array_append':
            q.require(len(args)==2 and args[0]==args[1]+'[]','Polymorphic array correspondence differs')
            wanted=['anycompatiblearray','anycompatible']; result=args[0]
        else:
            wanted=normalized; result=None
        candidates=[p for p in procs if p.get('proname')==name and p.get('proargtypes','').split()==wanted]
        q.require(len(candidates)==1,'Expected provider signature not unique: '+str((name,wanted)))
        p=candidates[0]; return p,result or p['prorettype']
    contexts=[]
    for index,group in enumerate(source['candidate_contexts']):
        sites=[]
        for number in group['site_indices']:
            site=source['call_sites'][number]; args=[infer(n) for n in site['argument_asts']]; name=site['callee'].split('.')[-1]
            p,result=resolve(name,args)
            sites.append(dict(site_index=number,source_location=dict(statement_ordinal=site['statement_ordinal'],control_path=site['control_path'],ast_path=site['path']),input_types=args,expected_oid=int(p['oid']),expected_signature='pg_catalog.'+name+'('+','.join(p.get('proargtypes','').split())+')',result_type=result,provider_definition=p,implicit_coercions=[dict(position=i,source=x,target=p['proargtypes'].split()[i],kind='UNKNOWN_LITERAL_INPUT') for i,x in enumerate(args) if x=='unknown'],search_path=['pg_catalog','pg_temp'],caller=site['caller']))
        q.require(len({x['expected_signature'] for x in sites})==1,'Candidate group needs split')
        contexts.append(dict(candidate_index=index,original_key=group['key'],sites=sites,expected_resolution_complete=True,semantic_status='UNBOUND',runtime_resolution_comparison_pending=True,full_operator_cast_closure=False))
    save('s04-expected-resolution.json',dict(total=33,resolved=33,unresolved=0,contexts=contexts,source_sha256=q.SOURCE_HASH,addendum_sha256=q.sha(ADDENDUM.read_bytes()),local_types=vars,semantic_status='UNBOUND',expected_function_call_resolution_only=True,operator_cast_closure_complete=False,provider_source='PostgreSQL REL_18_4 pg_proc.dat plus type-resolution rules',not_a_complete_reachability_graph=True))


def qualify(sql,run,container,folder,record,fixture,runtime_work):
    data=json.loads((OUT/'s04-expected-resolution.json').read_text()); results=[]
    seen=set()
    for context in data['contexts']:
        for site in context['sites']:
            p=site['provider_definition']; oid=site['expected_oid']
            if oid in seen: continue
            seen.add(oid)
            actual=json.loads(sql("SELECT json_build_object('oid',p.oid,'name',p.proname,'schema',n.nspname,'args',oidvectortypes(p.proargtypes),'result_type',p.prorettype::regtype::text,'source',p.prosrc,'owner',pg_get_userbyid(p.proowner),'security_definer',p.prosecdef,'strict',p.proisstrict,'volatile',p.provolatile,'parallel',p.proparallel,'config',p.proconfig,'language',l.lanname) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_language l ON l.oid=p.prolang WHERE p.oid=%d;"%oid).stdout)
            # Name/OID/source and defaulted provider flags are frozen separately.
            aliases={'int4':'integer','int8':'bigint','bool':'boolean','timestamptz':'timestamp with time zone'}
            expected_args=', '.join(aliases.get(x,x) for x in p.get('proargtypes','').split())
            passed=int(actual['oid'])==oid and actual['name']==p['proname'] and actual['schema']=='pg_catalog' and actual['args']==expected_args and actual['result_type']==aliases.get(p['prorettype'],p['prorettype']) and actual['source']==p['prosrc'] and actual['owner']=='postgres' and actual['language']=='internal' and not actual['security_definer'] and actual['config'] is None and actual['strict']==(p.get('proisstrict','t')=='t') and actual['volatile']==p.get('provolatile','i') and actual['parallel']==p.get('proparallel','s')
            row=dict(name='provider_function_identity_'+str(oid),passed=passed,group='RESOLUTION_IDENTITY',details=dict(expected=site,observed=actual,actual_source_expression_not_executed=True))
            record['cases'].append(row); results.append(row); q.require(passed,row['name'])
        site=context['sites'][0]
        original= json.loads(ADDENDUM.read_text())['call_sites'][site['site_index']]
        args=[]
        for typ,node in zip(site['input_types'],original['argument_asts']):
            if typ=='unknown':
                literal=node['A_Const']['sval']['sval']; args.append("'"+literal.replace("'","''")+"'")
            else: args.append('NULL::pg_catalog.'+typ)
        name=site['expected_signature'].split('(')[0]
        expression=name+'('+','.join(args)+')'
        got=sql("SELECT pg_typeof(%s)=to_regtype('%s'),has_function_privilege('flooow_offline_audit_owner','%s','EXECUTE'),has_schema_privilege('flooow_offline_audit_owner','pg_catalog','USAGE');"%(expression,site['result_type'],site['expected_signature'])).stdout.decode().strip()
        row=dict(name='typed_resolution_witness_context_'+str(context['candidate_index']),passed=got=='t|t|t',group='RESOLUTION_WITNESS',details=dict(expression=expression,result_type=site['result_type'],observed=got,source_operand_types_independently_derived=True,canonical_source_expression_and_S04_not_executed=True))
        record['cases'].append(row); results.append(row); q.require(row['passed'],row['name'])
    (folder/'resolution-identity-runtime.json').write_text(json.dumps(dict(cases=results,semantic_status='UNBOUND',no_S04_execution=True,expression_resolution_not_executed=True,complete_expectation_manifest=False),indent=2)+'\n')


if __name__=='__main__': prepare()
