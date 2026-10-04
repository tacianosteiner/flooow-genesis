"""Exact helper in network-disabled disposable PG; never executes V043."""
import hashlib
import json
from pathlib import Path
import tempfile
import package_0090_source_gate as gate
from package_0090_s02_isolated_review import run, quote
from package_0090_ed25519_review import BUILDER, EXPECTED_BUILDER_ID
from build_package_0090_original_match_source import build, NAME, TYPES

def review():
    if run(['docker','image','inspect',BUILDER,'--format','{{.Id}}']).strip()!=EXPECTED_BUILDER_ID:raise ValueError('Builder changed')
    gold=json.loads((gate.ROOT/'docs/evidence/PACKAGE-0090-S02-ORIGINAL-INPUT-GOLDENS.json').read_text())
    originals=gold['originals'];a=originals['A'];binding=a['binding_id']
    source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
    roles=['test_verifier','test_issuer','test_executor','test_auditor']
    sql=''.join('CREATE ROLE '+r+' LOGIN NOINHERIT;\n' for r in roles)
    denied_owners=['flooow_offline_audit_owner','flooow_offline_issuance_owner','flooow_offline_execution_owner']
    sql+=''.join('CREATE ROLE '+r+' NOLOGIN NOINHERIT;\n' for r in denied_owners)
    sql+='CREATE ROLE flooow_offline_control_owner NOLOGIN INHERIT;\nCREATE ROLE flooow_offline_verification_owner NOLOGIN NOINHERIT;\n'
    sql+='CREATE TABLE public.offline_binding_header(binding_id uuid PRIMARY KEY,plan_fingerprint bytea,deployment_incarnation_id uuid,offline_surface_version text,identity_slots bytea,manifest_digest bytea);\n'
    sql+='CREATE TABLE public.offline_expected_signed_attestation(binding_id uuid,manifest_digest text,algorithm_id text,signer_key_id uuid,signer_key_fingerprint text,signature_bytes bytea,canonical_expected_attestation bytea,commitment_digest bytea);\n'
    for table in ['offline_binding_header','offline_expected_signed_attestation']:
        sql+='ALTER TABLE public.'+table+' OWNER TO flooow_offline_control_owner;\nREVOKE ALL ON public.'+table+' FROM PUBLIC;\n'
    slots="int4send(4)||(SELECT string_agg(int4send(9+octet_length(convert_to(r.rolname,'UTF8')))||decode(lpad(to_hex(x.slot),2,'0'),'hex')||oidsend(r.oid)||int4send(octet_length(convert_to(r.rolname,'UTF8')))||convert_to(r.rolname,'UTF8'),''::bytea ORDER BY x.slot) FROM (VALUES "+','.join('('+str(i)+','+quote(r)+')' for i,r in enumerate(roles,1))+') x(slot,name) JOIN pg_roles r ON r.rolname=x.name)'
    incarnation='00000000-0000-0000-0000-000000000333';plan='01'*32
    sql+='INSERT INTO public.offline_binding_header VALUES('+quote(binding)+",decode('"+plan+"','hex'),"+quote(incarnation)+",'0090-v1',"+slots+",decode("+quote(a['manifest_digest'])+",'hex'));\n"
    def install_original(label):
        values=originals[label]
        columns=list(values)
        return 'DELETE FROM public.offline_expected_signed_attestation;\nINSERT INTO public.offline_expected_signed_attestation('+','.join(columns)+') VALUES('+','.join("decode("+quote(values[k])+",'hex')" if k in ('signature_bytes','canonical_expected_attestation','commitment_digest') else quote(values[k]) for k in columns)+');\n'
    sql+=install_original('A')+build(source)
    signature=','.join('pg_catalog.'+t for t in TYPES)
    # Test-only entry mirrors SECURITY DEFINER nesting without granting membership
    # or direct helper access to any service. Production S05/S06 are not installed.
    sql+='CREATE FUNCTION public.test_v_entry('+signature+') RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $entry$ SELECT public.'+NAME+'('+','.join('$'+str(i) for i in range(1,10))+') $entry$;\n'
    sql+='ALTER FUNCTION public.test_v_entry('+signature+') OWNER TO flooow_offline_verification_owner;\nREVOKE ALL ON FUNCTION public.test_v_entry('+signature+') FROM PUBLIC;\n'
    sql+='GRANT EXECUTE ON FUNCTION public.test_v_entry('+signature+') TO '+','.join(roles)+';\n'
    def args(label):
        v=originals[label]
        return [quote(binding),"decode('"+plan+"','hex')",quote(incarnation),"'0090-v1'",quote(v['manifest_digest']),quote(v['algorithm_id']),quote(v['signer_key_id']),quote(v['signer_key_fingerprint']),"decode("+quote(v['signature_bytes'])+",'hex')"]
    def assertion(arguments,expected=None,deny=False):
        call='public.test_v_entry('+','.join(arguments)+')'
        if deny:return "DO $deny$ BEGIN BEGIN PERFORM "+call+"; RAISE EXCEPTION 'DENIAL_MISSING'; EXCEPTION WHEN SQLSTATE 'P0017' THEN IF SQLERRM<>'ACCESS_DENIED' THEN RAISE EXCEPTION 'UNSANITIZED'; END IF; END; END; $deny$;\n"
        return "DO $assert$ BEGIN IF "+call+' IS DISTINCT FROM '+str(expected).lower()+" THEN RAISE EXCEPTION 'COMPARISON_FAILED'; END IF; END; $assert$;\n"
    def auth(role):return 'SET SESSION AUTHORIZATION '+role+';\n'
    matrix={}
    for original in ['A','B']:
        sql+=install_original(original)+auth('test_verifier')
        for caller in ['A','B']:
            expected=original==caller;sql+=assertion(args(caller),expected);matrix['original_'+original+'_caller_'+caller]=expected
        sql+='RESET SESSION AUTHORIZATION;\n'
    sql+=install_original('A')
    negatives=[]
    for role in roles[1:]:
        sql+=auth(role)+assertion(args('A'),deny=True)+'RESET SESSION AUTHORIZATION;\n';negatives.append('WRONG_SESSION_'+role)
    sql+=auth('test_verifier')
    for index in range(9):
        values=args('A');values[index]='NULL';sql+=assertion(values,deny=True);negatives.append('NULL_'+str(index+1))
    changes={0:quote('00000000-0000-0000-0000-000000000444'),1:"decode(repeat('02',32),'hex')",2:quote('00000000-0000-0000-0000-000000000444'),3:"'wrong'",4:"repeat('0',64)",5:"'alternate'",6:quote('00000000-0000-0000-0000-000000000444'),7:"repeat('0',64)",8:"decode(repeat('00',64),'hex')"}
    for index,value in changes.items():
        values=args('A');values[index]=value;sql+=assertion(values,False,deny=index<4);negatives.append('WRONG_'+str(index+1))
    helper='public.'+NAME+'('+','.join(args('A'))+')'
    sql+="DO $direct$ BEGIN BEGIN PERFORM "+helper+"; RAISE EXCEPTION 'DIRECT_ACCESS'; EXCEPTION WHEN insufficient_privilege THEN NULL; END; END; $direct$;\nRESET SESSION AUTHORIZATION;\n"
    for role in roles:
        sql+=auth(role)+"DO $direct$ BEGIN BEGIN PERFORM "+helper+"; RAISE EXCEPTION 'DIRECT_ACCESS'; EXCEPTION WHEN insufficient_privilege THEN NULL; END; END; $direct$;\nRESET SESSION AUTHORIZATION;\n";negatives.append('SERVICE_DIRECT_'+role)
    for change in ["DELETE FROM public.offline_expected_signed_attestation;","UPDATE public.offline_expected_signed_attestation SET canonical_expected_attestation=decode('00','hex');","UPDATE public.offline_expected_signed_attestation SET commitment_digest=decode(repeat('00',32),'hex');","INSERT INTO public.offline_expected_signed_attestation SELECT * FROM public.offline_expected_signed_attestation;"]:
        sql+='BEGIN;\n'+change+'\n'+auth('test_verifier')+assertion(args('A'),False)+'RESET SESSION AUTHORIZATION;\nROLLBACK;\n';negatives.append(change.split()[0]+'_CORRUPT_OR_CARDINALITY')
    sql+="DO $acl$ BEGIN IF EXISTS(SELECT 1 FROM pg_proc p,LATERAL aclexplode(p.proacl) x WHERE p.proname="+quote(NAME)+" AND x.privilege_type='EXECUTE' AND (x.grantee=0 OR x.is_grantable)) THEN RAISE EXCEPTION 'PUBLIC_OR_GRANT_OPTION'; END IF; IF EXISTS(SELECT 1 FROM pg_roles r WHERE r.rolname IN ("+','.join(quote(r) for r in roles+denied_owners)+") AND has_function_privilege(r.oid,"+quote('public.'+NAME+'('+','.join(TYPES)+')')+",'EXECUTE')) THEN RAISE EXCEPTION 'SERVICE_HELPER_ACCESS'; END IF; IF has_table_privilege('flooow_offline_verification_owner','public.offline_expected_signed_attestation','SELECT') THEN RAISE EXCEPTION 'V_TABLE_SELECT'; END IF; END; $acl$;\nSELECT 'ORIGINAL_MATCH_ISOLATED_PASS';\n"
    with tempfile.TemporaryDirectory(prefix='flooow-0090-original-match-') as scratch:
        work=Path(scratch);(work/'review.sql').write_text(sql,encoding='utf-8',newline='\n')
        script='''set -eu
mkdir /tmp/pgdata /tmp/pgsocket
chown postgres:postgres /tmp/pgdata /tmp/pgsocket
runuser -u postgres -- /usr/lib/postgresql/18/bin/initdb -D /tmp/pgdata -A trust >/work/init.log
runuser -u postgres -- /usr/lib/postgresql/18/bin/pg_ctl -D /tmp/pgdata -l /tmp/pgserver.log -o "-k /tmp/pgsocket -c listen_addresses=''" start >/work/start.log
/usr/lib/postgresql/18/bin/psql -X -v ON_ERROR_STOP=1 -h /tmp/pgsocket -U postgres -d postgres -f /work/review.sql >/work/result.log 2>&1 || { cat /work/result.log; exit 1; }
cat /work/result.log
'''
        (work/'run.sh').write_text(script,encoding='ascii',newline='\n')
        output=run(['docker','run','--rm','--network','none','--entrypoint','sh','--mount',f'type=bind,source={work},target=/work',BUILDER,'/work/run.sh'])
        if 'ORIGINAL_MATCH_ISOLATED_PASS' not in output:raise ValueError('Review incomplete')
    return dict(status='PASS_ISOLATED_HELPER',matrix=matrix,negatives=negatives,sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),builder_id=EXPECTED_BUILDER_ID,v043_executed=False,protected_database_connection=False,production_roles_created=False,limitations=['Disposable mock header/original relations and test-only V entry; complete mutation wrapper runtime closure remains separate.'])

if __name__=='__main__':
    result=review();(gate.ROOT/'docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-MATCH-REVIEW.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))

