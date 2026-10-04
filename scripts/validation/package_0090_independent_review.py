"""Review-only extractor: SQL AST + normative Markdown, no implementation generators.

Does not execute SQL, install objects, or treat source ACLs as installed ACLs.
Run with the separately installed pinned pglast on PYTHONPATH.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from pglast import parser

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / 'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration'
SPEC = ROOT / 'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md'
OWNERS = dict(zip('VIEAPQZ', ('flooow_offline_verification_owner',
    'flooow_offline_issuance_owner', 'flooow_offline_execution_owner',
    'flooow_offline_audit_owner', 'flooow_offline_principal_lock_owner',
    'flooow_offline_readiness_owner', 'flooow_offline_intent_audit_owner')))

def names(items):
    return '.'.join(i['String']['sval'] for i in items)

def typ(t):
    return names(t['names']) + '[]' * len(t.get('arrayBounds', []))

def identity(o):
    return names(o['objname']) + '(' + ','.join(typ(t['TypeName']) for t in o.get('objargs', [])) + ')'

def main():
    path = next(MIGRATIONS.glob('V043*'))
    source = path.read_text(encoding='utf-8-sig')
    spec = SPEC.read_text(encoding='utf-8-sig')
    statements = [r['stmt'] for r in json.loads(parser.parse_sql_json(source))['stmts']]
    definitions, bodies, owner_map, revokes, function_grants, schema_grants, column_grants = {}, {}, {}, [], [], [], []
    unsafe_grants = []
    for s in statements:
        if 'CreateFunctionStmt' in s:
            f = s['CreateFunctionStmt']
            args = [a['FunctionParameter'] for a in f.get('parameters', [])]
            inputs = [a for a in args if a.get('mode') not in ('FUNC_PARAM_TABLE','FUNC_PARAM_OUT')]
            key = names(f['funcname']) + '(' + ','.join(typ(a['argType']) for a in inputs) + ')'
            options = {d['DefElem']['defname']: d['DefElem'].get('arg') for d in f['options']}
            body = options['as']['List']['items'][0]['String']['sval']
            bodies[key]=body
            set_opt = options.get('set', {}).get('VariableSetStmt', {})
            definitions[key] = dict(name=names(f['funcname']), arguments=[(a.get('name'),typ(a['argType'])) for a in inputs],
                defaults=any('defexpr' in a for a in args), variadic=any(a.get('mode')=='FUNC_PARAM_VARIADIC' for a in args),
                result=typ(f['returnType']), returns_set=f['returnType'].get('setof',False),
                output_columns=[(a.get('name'),typ(a['argType'])) for a in args if a.get('mode')=='FUNC_PARAM_TABLE'],
                volatility=options.get('volatility',{}).get('String',{}).get('sval','volatile'),
                security_definer=options.get('security',{}).get('Boolean',{}).get('boolval',False),
                strict=options.get('strict',{}).get('Boolean',{}).get('boolval',False),
                search_path=set_opt,
                line=source[:f['returnType']['location']].count('\n')+1,
                body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                qualified_calls=sorted(set(re.findall(r'\b(public|offline_crypto|pg_catalog)\.([a-z_][a-z_0-9]*)\s*\(',body))),
                forbidden_tokens=[p for p in (r'\bEXECUTE\s',r'\bSET\s+ROLE\b',r'\bset_config\s*\(',r'\bregproc\b',r'\bregclass\b',r'\bpg_temp\.',r'\bCOMMIT\b',r'\bROLLBACK\b') if re.search(p,body,re.I)],
                session_identity='SESSION_USER' in body,
                transaction_settings=sorted(set(re.findall(r"current_setting\('([^']+)'",body))),
                lock_markers=[(m.group(0),body[:m.start()].count('\n')+1) for m in re.finditer(r'FOR UPDATE|FOR SHARE|public\.offline_lock_bound_principal|public\.transaction_identity_progress_lock|pg_catalog\.pg_advisory_xact_lock',body)],
                writes=sorted(set(re.findall(r'\b(?:INSERT INTO|UPDATE|DELETE FROM)\s+(public\.[a-z_]+)',body))))
        elif 'AlterOwnerStmt' in s:
            a=s['AlterOwnerStmt']
            if a['objectType']=='OBJECT_FUNCTION':owner_map[identity(a['object']['ObjectWithArgs'])]=a['newowner']['rolename']
        elif 'GrantStmt' in s:
            g=s['GrantStmt']
            if g.get('grant_option'):unsafe_grants.append(g)
            roles=[r['RoleSpec'].get('rolename','PUBLIC') for r in g['grantees']]
            if g['objtype']=='OBJECT_FUNCTION':
                rows=[(identity(o['ObjectWithArgs']),r) for o in g['objects'] for r in roles]
                (function_grants if g.get('is_grant') else revokes).extend(rows)
            elif g.get('is_grant') and g['objtype']=='OBJECT_SCHEMA':
                schema_grants.extend((names([o]),r,p['AccessPriv']['priv_name']) for o in g['objects'] for r in roles for p in g.get('privileges',[]))
            elif g.get('is_grant') and g['objtype']=='OBJECT_TABLE':
                for o in g['objects']:
                    t=o['RangeVar']; relation=t.get('schemaname','')+'.'+t['relname']
                    for p in g.get('privileges',[]):
                        a=p['AccessPriv']
                        if not a.get('cols'):unsafe_grants.append(g)
                        column_grants.extend((r,relation,c['String']['sval'],a['priv_name']) for r in roles for c in a.get('cols',[]))
    contracts={}
    manifest=spec.split('### 21.1 Exact public SQL manifest',1)[1].split('### 21.2',1)[0]
    for m in re.finditer(r'\*\*(S\d\d)\*\*(.*?)(?=\*\*S\d\d\*\*|\Z)',manifest,re.S):
        label,block=m.groups()
        signature=re.search(r'`(public\.offline_\w+)\(([^`]+)\)`',block)
        if not signature:continue
        args=[tuple(a.strip().split()) for a in signature[2].split(',')]
        key=signature[1]+'('+','.join(a[1] for a in args)+')'
        f=definitions.get(key)
        contracts[label]=dict(signature=key,exists=f is not None,slot=re.search(r'CALLER_SLOT=(\w+)',block)[1])
        contracts[label]['expected_arguments']=args
        if f:
            f['owner']=owner_map.get(key)
            f['public_revoked']=(key,'PUBLIC') in revokes
            f['direct_non_owner_grants']=[r for k,r in function_grants if k==key]
            contracts[label]['argument_names_match']=f['arguments']==args
            role_key={'AUDITOR':'A','VERIFIER':'V','ISSUER':'I','EXECUTOR':'E'}[contracts[label]['slot']]
            search=f['search_path']
            path_values=[a['A_Const']['sval']['sval'] for a in search.get('args',[])]
            contracts[label]['governed_metadata_match']=(f['owner']==OWNERS[role_key] and f['public_revoked'] and f['security_definer'] and not f['strict'] and not f['defaults'] and not f['variadic'] and search.get('name')=='search_path' and path_values==['pg_catalog','pg_temp'] and f['volatility']==('stable' if int(label[1:])<=4 else 'volatile') and (f['result']=='pg_catalog.record' and f['returns_set'] and len(f['output_columns'])==6 if label=='S04' else f['result']=='pg_catalog.bytea' and not f['returns_set']))
            contracts[label]['metadata']=f
    expected_columns=set()
    privilege={'READ_PRIVILEGE':'select','LOCK_ENABLING_UPDATE_PRIVILEGE':'update','BOOKKEEPING_INSERT':'insert','BOOKKEEPING_UPDATE':'update'}
    for line in spec.splitlines():
        cells=[c.strip() for c in line.strip().split('|')[1:-1]]
        if len(cells)==9 and cells[0] in OWNERS and cells[3] in privilege:
            expected_columns.add((OWNERS[cells[0]],cells[1],cells[2],privilege[cells[3]]))
    actual=set(column_grants)
    for key,f in definitions.items():
        f['owner']=owner_map.get(key)
        f['public_revoked']=(key,'PUBLIC') in revokes
    frozen={}
    frozen_differences=[]
    for p in sorted(MIGRATIONS.glob('V*.sql')):
        if int(p.name[1:4])>42:continue
        baseline_bytes=subprocess.check_output(['git','show','19131bb9cd655312252c8c83f0f78e7c0742274f:'+p.relative_to(ROOT).as_posix()],cwd=ROOT).replace(b'\r\n',b'\n')
        current=p.read_bytes().replace(b'\r\n',b'\n')
        frozen[p.name]=hashlib.sha256(current).hexdigest()
        if current!=baseline_bytes:frozen_differences.append(p.name)
    frozen_definitions={}
    for p in sorted(MIGRATIONS.glob('V*.sql')):
        if int(p.name[1:4])>42:continue
        for r in json.loads(parser.parse_sql_json(p.read_text(encoding='utf-8-sig')))['stmts']:
            fn=r['stmt'].get('CreateFunctionStmt')
            if fn:
                qualified=names(fn['funcname'])
                if '.' not in qualified:qualified='public.'+qualified
                frozen_definitions[qualified]=(p.name,fn)
    tuple_reviews={}
    def normalized_type(text):
        t=json.loads(parser.parse_sql_json('SELECT NULL::'+text))['stmts'][0]['stmt']['SelectStmt']['targetList'][0]['ResTarget']['val']['TypeCast']['typeName']
        name=typ(t)
        return name if '.' in name else 'pg_catalog.'+name
    for m in re.finditer(r'\*\*(S\d\d) frozen tuple contract\*\*:\s*static `([^`]+)`;(.*?)(?=\*\*S\d\d frozen tuple contract|### 21.2|\Z)',manifest,re.S):
        stage,fn_name,block=m.groups()
        file,fn=frozen_definitions[fn_name]
        entries={}
        for direction in ('INPUT','OUTPUT'):
            line=re.search(r'^'+direction+r': (.+)$',block,re.M)[1]
            expected=[]
            for field in line.rstrip('.').split('; '):
                number,field=field.split('=',1)
                field_name,field_type=field.split(' ',1)
                expected.append((field_name,normalized_type(field_type)))
            actual_vector=[]
            for p in fn.get('parameters',[]):
                a=p['FunctionParameter'];out=a.get('mode') in ('FUNC_PARAM_OUT','FUNC_PARAM_TABLE')
                if out==(direction=='OUTPUT'):
                    t=typ(a['argType']);actual_vector.append((a.get('name'),t if '.' in t else 'pg_catalog.'+t))
            entries[direction]=dict(expected=expected,actual=actual_vector,match=expected==actual_vector)
        tuple_reviews[stage]=dict(function=fn_name,file=file,vectors=entries,status='PASS_METADATA_ONLY_NOT_RUNTIME_SEMANTICS')
    delegated_calls=[]
    for key,body in bodies.items():
        declarations=dict(re.findall(r'^\s*(\w+)\s+(pg_catalog\.\w+)(?:\([^\n;]+\))?\s*;',body,re.M))
        for call in re.finditer(r'FROM public\.(s2a_\w+)\(([^;\n]+)\)\s+v;',body):
            file,fn=frozen_definitions['public.'+call[1]]
            parameters=[p['FunctionParameter'] for p in fn['parameters'] if p['FunctionParameter'].get('mode') not in ('FUNC_PARAM_OUT','FUNC_PARAM_TABLE')]
            expressions=[v.strip() for v in call[2].split(',')]
            mapped=[]
            for expression,p in zip(expressions,parameters):
                identifier=expression.split('::')[0]
                declared=declarations.get(identifier)
                t=typ(p['argType']);expected_type=t if '.' in t else 'pg_catalog.'+t
                parameter_name=identifier.removeprefix('input_').removeprefix('facts_')
                if identifier.startswith('accepted_'):
                    parameter_name='p_expected_'+identifier.removeprefix('accepted_')
                    if identifier=='accepted_signed_evidence_binding_fingerprint':parameter_name='p_expected_evidence_binding_fingerprint'
                mapped.append(dict(expression=expression,expected_parameter=p.get('name'),declared_type=declared,expected_type=expected_type,
                    parameter_order_match=parameter_name==p.get('name'),type_match=declared==expected_type))
            delegated_calls.append(dict(wrapper=key,function='public.'+call[1],frozen_file=file,
                arity_match=len(expressions)==len(parameters),argument_mapping=mapped,
                order_match=all(x['parameter_order_match'] for x in mapped),types_match=all(x['type_match'] for x in mapped),
                explicit_casts=all('::' in x for x in expressions)))
    # Independent role/dependency rows transcribed from SPEC21.7,23.3 and
    # approved native/original-input amendments; never generator constants.
    dependency_names={
        'A':('offline_internal_verify_authority_intent','offline_internal_readiness','offline_internal_canonical_spki_ed25519_verify','transaction_identity_grant_fingerprint','transaction_identity_hash','transaction_identity_intent','transaction_identity_fingerprint'),
        'E':('offline_lock_bound_principal','offline_internal_readiness','transaction_identity_grant_fingerprint','transaction_identity_hash','s2a_v042_apply_attested_decision','s2a_v042_begin_attested_decision_verification','transaction_identity_fingerprint','transaction_identity_intent','transaction_identity_progress_lock'),
        'I':('s2a_v042_begin_attested_principal_verification','s2a_v042_apply_attested_principal','s2a_v042_begin_attested_initial_credential_verification','s2a_v042_apply_attested_initial_credential','s2a_v042_begin_attested_grant_verification','s2a_v042_apply_attested_grant'),
        'V':('offline_internal_matches_original_signed_attestation','s2a_begin_attestation_verification','s2a_persist_attestation_verification_result'),
        'P':('command_authorization_organization_lock',),
        'Z':('s2a_v042_authority_intent','s2a_v042_authority_receipt','s2a_v042_frame','s2a_v042_text','s2a_v042_instant')}
    expected_execute=set()
    private_vectors={
        'offline_lock_bound_principal':('uuid','bytea','uuid','text','uuid','int8','uuid','uuid','bytea'),
        'offline_internal_verify_authority_intent':('uuid','bytea','uuid','text'),
        'offline_internal_readiness':('uuid','bytea','uuid','text','bytea','bytea','bytea','bytea'),
        'offline_internal_canonical_spki_ed25519_verify':('bytea','bytea','bytea'),
        'offline_internal_matches_original_signed_attestation':('uuid','bytea','uuid','text','text','text','uuid','text','bytea')}
    for owner,dependencies in dependency_names.items():
        for name in dependencies:
            qualified='public.'+name
            local=[k for k in definitions if k.startswith(qualified+'(')]
            if local:
                if len(local)!=1:raise ValueError('Unexpected private overload '+qualified)
                signature=qualified+'('+','.join('pg_catalog.'+t for t in private_vectors[name])+')'
            else:
                _,f=frozen_definitions[qualified]
                vector=[p['FunctionParameter']['argType'] for p in f['parameters'] if p['FunctionParameter'].get('mode') not in ('FUNC_PARAM_OUT','FUNC_PARAM_TABLE')]
                signature=qualified+'('+','.join(typ(t) if '.' in typ(t) else ('public.' if typ(t)=='marketplace_transaction_identity_decision' else 'pg_catalog.')+typ(t) for t in vector)+')'
            expected_execute.add((signature,OWNERS[owner]))
    expected_execute.add(('offline_crypto.canonical_spki_ed25519_verify(pg_catalog.bytea,pg_catalog.bytea,pg_catalog.bytea)',OWNERS['V']))
    expected_schema={('public',owner,'usage') for owner in OWNERS.values()}|{('offline_crypto',OWNERS['V'],'usage')}
    result=dict(baseline='9ba136cd4920d2710d6a886f0eea7cee938c3b2a',method='INDEPENDENT_SQL_AST_AND_NORMATIVE_MARKDOWN_NO_GENERATOR_IMPORTS',
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),statement_count=len(statements),
        first_statement=statements[0],public_contracts=contracts,definitions=definitions,
        counts=dict(public_contracts=len(contracts),public_wrappers=sum(not any(t in f['name'] for t in ('internal','offline_lock')) for f in definitions.values()),executor=sum(c['slot']=='EXECUTOR' for c in contracts.values()),columns=len(actual),execute=len(function_grants),schema_usage=len(schema_grants)),
        column_acl=dict(missing=sorted(expected_columns-actual),extra=sorted(actual-expected_columns),duplicates=len(column_grants)-len(actual)),
        function_execute=function_grants,function_acl=dict(missing=sorted(expected_execute-set(function_grants)),extra=sorted(set(function_grants)-expected_execute),duplicates=len(function_grants)-len(set(function_grants)),public_unauthorized=sum(r=='PUBLIC' for k,r in function_grants),service_direct_private=sum(r not in OWNERS.values() for k,r in function_grants)),
        schema_usage=schema_grants,schema_acl=dict(missing=sorted(expected_schema-set(schema_grants)),extra=sorted(set(schema_grants)-expected_schema)),unsafe_grants=unsafe_grants,
        frozen_source_sha256=frozen,frozen_differences=frozen_differences,frozen_comparison='GIT_CANONICAL_LF_VS_19131bb9cd655312252c8c83f0f78e7c0742274f',frozen_tuple_reviews=tuple_reviews,delegated_calls=delegated_calls,installed_acl_proof='NOT_EXECUTED',role_membership_effective_acl='REQUIRES_ISOLATED_CATALOG_PROOF')
    target=ROOT/'docs/evidence/PACKAGE-0090-INDEPENDENT-SOURCE-REVIEW.json'
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(counts=result['counts'],column_acl=result['column_acl'],unsafe_grants=len(unsafe_grants),contract_signature_or_argument_mismatches=[k for k,v in contracts.items() if not v.get('argument_names_match')]),indent=2))

if __name__=='__main__':main()
