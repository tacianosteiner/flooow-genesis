"""Installed catalog comparison for the uniquely labelled disposable G3F.4 server."""
import json
from pathlib import Path
import subprocess
import sys
import package_0090_source_gate as source

def inspect(work):
    work=Path(work); record=json.loads((work/'record.json').read_text())
    container=record['container']; project=record['disposable_project']
    details=json.loads(subprocess.check_output(['docker','inspect',container]))[0]
    if details['Config']['Labels']['com.docker.compose.project']!=project:
        raise RuntimeError('Disposable identity mismatch')
    def sql(statement):
        r=subprocess.run(['docker','exec','-i',container,'psql','-X','-U','postgres','-d','g3f4','-At','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True,check=True)
        return json.loads(r.stdout)
    oracle=json.loads((source.ROOT/'docs/evidence/PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json').read_text(encoding='utf-8-sig'))
    catalog=sql("""SELECT json_agg(json_build_object(
      'name',n.nspname||'.'||p.proname,
      'signature',n.nspname||'.'||p.proname||'('||(SELECT coalesce(string_agg(tn.nspname||'.'||t.typname,',' ORDER BY a.i),'') FROM unnest(p.proargtypes::oid[]) WITH ORDINALITY a(oid,i) JOIN pg_type t ON t.oid=a.oid JOIN pg_namespace tn ON tn.oid=t.typnamespace)||')',
      'argument_names',p.proargnames,'argument_modes',p.proargmodes,'result',rn.nspname||'.'||rt.typname,
      'all_argument_types',(SELECT json_agg(tn.nspname||'.'||t.typname ORDER BY a.i) FROM unnest(p.proallargtypes) WITH ORDINALITY a(oid,i) JOIN pg_type t ON t.oid=a.oid JOIN pg_namespace tn ON tn.oid=t.typnamespace),
      'volatility',p.provolatile,'security_definer',p.prosecdef,'strict',p.proisstrict,
      'returns_set',p.proretset,'defaults',p.pronargdefaults,'variadic',p.provariadic,
      'search_path',p.proconfig,'owner',pg_get_userbyid(p.proowner),
      'acl',coalesce(p.proacl,acldefault('f',p.proowner))::text,
      'public_execute',has_function_privilege('public',p.oid,'EXECUTE')) ORDER BY p.proname)
      FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_type rt ON rt.oid=p.prorettype JOIN pg_namespace rn ON rn.oid=rt.typnamespace
      WHERE n.nspname='public' AND p.proname LIKE 'offline_%';""")
    installed={r['signature']:r for r in catalog}; mismatches=[]
    for label,c in oracle['public_contracts'].items():
        row=installed.get(c['signature']); meta=c['metadata']
        expected=dict(argument_names=[a[0] for a in c['expected_arguments']],result=meta['result'],
          volatility={'stable':'s','volatile':'v','immutable':'i'}[meta['volatility']],security_definer=True,
          strict=meta['strict'],returns_set=bool(meta['output_columns']) or meta['returns_set'],defaults=0,variadic='0',
          search_path=['search_path=pg_catalog, pg_temp'],owner=meta['owner'],public_execute=False)
        input_row=dict(row) if row else {}
        if row and row['argument_modes']:
            input_row['argument_names']=[name for name,mode in zip(row['argument_names'],row['argument_modes']) if mode in ('i','b','v')]
            expected['output_columns']=meta['output_columns']
            input_row['output_columns']=[[name,typ] for name,typ,mode in zip(row['argument_names'],row['all_argument_types'],row['argument_modes']) if mode=='t']
        delta={k:dict(expected=v,actual=input_row.get(k)) for k,v in expected.items() if input_row.get(k)!=v}
        if delta: mismatches.append(dict(label=label,signature=c['signature'],delta=delta))
    columns=sql("""SELECT coalesce(json_agg(json_build_array(r.rolname,n.nspname||'.'||c.relname,a.attname,lower(x.privilege_type),x.is_grantable)), '[]') FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(a.attacl) x JOIN pg_roles r ON r.oid=x.grantee WHERE r.rolname IN ('flooow_offline_verification_owner','flooow_offline_issuance_owner','flooow_offline_execution_owner','flooow_offline_audit_owner','flooow_offline_principal_lock_owner','flooow_offline_readiness_owner','flooow_offline_intent_audit_owner');""")
    actual_columns={tuple(r[:4]) for r in columns}
    expected_columns=source.expected_column_grants((source.ROOT/source.SPEC).read_text(encoding='utf-8-sig'))
    # Exact function OIDs resolved by PostgreSQL, rather than formatting aliases.
    expected_functions=[]
    for signature,role in oracle['function_execute']:
        value=sql("SELECT json_build_array('"+signature+"'::regprocedure::oid,'"+role+"');")
        expected_functions.append(tuple(value))
    functions=sql("""SELECT coalesce(json_agg(json_build_array(p.oid,r.rolname,x.is_grantable,p.oid::regprocedure::text)), '[]') FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) x JOIN pg_roles r ON r.oid=x.grantee WHERE x.privilege_type='EXECUTE' AND r.rolname IN ('flooow_offline_verification_owner','flooow_offline_issuance_owner','flooow_offline_execution_owner','flooow_offline_audit_owner','flooow_offline_principal_lock_owner','flooow_offline_readiness_owner','flooow_offline_intent_audit_owner') AND r.oid<>p.proowner;""")
    actual_functions={tuple(r[:2]) for r in functions}
    # Q's prerequisite hmac/mac32 grants are separate from the 32 V043 grants.
    prereq={tuple(sql("SELECT json_build_array('"+sig+"'::regprocedure::oid,'flooow_offline_readiness_owner');")) for sig in ['offline_crypto.hmac(bytea,bytea,text)','offline_crypto.timing_safe_equal32(bytea,bytea)']}
    schemas=sql("""SELECT json_agg(json_build_array(n.nspname,r.rolname,lower(x.privilege_type),x.is_grantable)) FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) x JOIN pg_roles r ON r.oid=x.grantee WHERE r.rolname IN ('flooow_offline_verification_owner','flooow_offline_issuance_owner','flooow_offline_execution_owner','flooow_offline_audit_owner','flooow_offline_principal_lock_owner','flooow_offline_readiness_owner','flooow_offline_intent_audit_owner');""")
    expected_schemas={tuple(r) for r in oracle['schema_usage']}|{('offline_crypto','flooow_offline_readiness_owner','usage')}
    actual_schemas={tuple(r[:3]) for r in schemas}
    acl=dict(column_count=len(actual_columns),column_missing=sorted(expected_columns-actual_columns),column_extra=sorted(actual_columns-expected_columns),
      v043_function_execute_count=len(actual_functions-prereq),prerequisite_function_execute_count=len(prereq),function_missing=sorted(set(expected_functions)-actual_functions),function_extra=sorted(actual_functions-set(expected_functions)-prereq),
      v043_schema_usage_count=len(actual_schemas)-1,prerequisite_schema_usage_count=1,schema_missing=sorted(expected_schemas-actual_schemas),schema_extra=sorted(actual_schemas-expected_schemas),
      grant_option_count=sum(r[4] for r in columns)+sum(r[2] for r in functions)+sum(r[3] for r in schemas),columns=columns,functions=functions,schemas=schemas)
    record['installed_catalog']=dict(rows=catalog,public_wrapper_count=len(oracle['public_contracts']),executor_signature_count=sum(c['slot']=='EXECUTOR' for c in oracle['public_contracts'].values()),mismatches=mismatches,unexpected_signatures=sorted(set(installed)-set(oracle['definitions'])))
    record['installed_acl']=acl
    (work/'record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(catalog_mismatches=mismatches,acl={k:v for k,v in acl.items() if k not in ('columns','functions','schemas')}),indent=2))

if __name__=='__main__': inspect(sys.argv[1])
