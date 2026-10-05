"""Bounded real installed native/ACL/policy prerequisites, never positive-flow substitutes."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from time import time
import package_0090_source_gate as source

def probe(work):
    work=Path(work); record=json.loads((work/'record.json').read_text()); c=record['container']
    d=json.loads(subprocess.check_output(['docker','inspect',c]))[0]
    if d['Config']['Labels']['com.docker.compose.project']!=record['disposable_project']:
        raise RuntimeError('Wrong disposable container')
    def execute(statement):
        return subprocess.run(['docker','exec','-i',c,'psql','-X','-U','postgres','-d','g3f4','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose'],input=statement,text=True,capture_output=True)
    def sql(statement):
        r=execute(statement)
        if r.returncode: raise RuntimeError('SQL prerequisite failed: '+r.stderr)
        return r.stdout.strip()
    def save(): (work/'record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    fixture=json.loads((source.ROOT/'docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json').read_text())
    canonical=bytes.fromhex(fixture['canonical_policy_hex']); digest=hashlib.sha256(canonical).hexdigest()
    if digest!=fixture['canonical_policy_sha256']:raise RuntimeError('Policy digest mismatch')
    if not (work/'service-credentials.json').exists():
        sql("INSERT INTO public.offline_deadline_policy VALUES ('fixture-1',decode('"+digest+"','hex'),decode('"+canonical.hex()+"','hex'),clock_timestamp());")
    record['policy']=dict(fixture_id=fixture['fixture_id'],scope=fixture['scope'],version='fixture-1',digest=digest,production_provisioning=False,active='YES_REHEARSAL_ONLY')
    # Private generated seed; deterministic per-label rehearsal credentials derived from it.
    seed=secrets.token_bytes(32); credentials={}
    oracle=json.loads((source.ROOT/'docs/evidence/PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json').read_text())
    if (work/'service-credentials.json').exists():
        credentials=json.loads((work/'service-credentials.json').read_text())
    for slot in ([] if credentials else ['AUDITOR','VERIFIER','ISSUER','EXECUTOR']):
        name='g3f4_'+slot.lower()+'_'+record['disposable_project'][-12:]
        password=hashlib.sha256(seed+slot.encode()).hexdigest(); credentials[slot]=(name,password)
        sql(f"CREATE ROLE {name} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '{password}'; GRANT CONNECT ON DATABASE g3f4 TO {name}; GRANT USAGE ON SCHEMA public TO {name};")
        for contract in oracle['public_contracts'].values():
            if contract['slot']==slot: sql('GRANT EXECUTE ON FUNCTION '+contract['signature']+' TO '+name+';')
    record['service_roles']={slot:v[0] for slot,v in credentials.items()}
    (work/'service-credentials.json').write_text(json.dumps(credentials),encoding='utf-8')
    record['roles']=json.loads(sql("SELECT json_agg(json_build_object('name',rolname,'login',rolcanlogin,'inherit',rolinherit,'superuser',rolsuper,'createdb',rolcreatedb,'createrole',rolcreaterole,'replication',rolreplication,'bypassrls',rolbypassrls)) FROM pg_roles WHERE rolname LIKE 'flooow_offline_%' OR rolname LIKE 'g3f4_%';"))
    native=json.loads((source.ROOT/'docs/evidence/PACKAGE-0090-ED25519-NATIVE-REVIEW.json').read_text())
    crypto=[]
    for vector in native['vectors']:
        query="SELECT offline_crypto.canonical_spki_ed25519_verify("+','.join("decode('"+vector[k]+"','hex')" for k in ('spki_hex','message_hex','signature_hex'))+");"
        result=execute(query); out=result.stdout.strip()
        state=None
        if result.returncode:
            import re
            found=re.search(r'ERROR:\s+([A-Z0-9]{5}):',result.stderr);state=found[1] if found else 'UNCLASSIFIED'
        accepted=out=='t' and result.returncode==0
        crypto.append(dict(name=vector['name'],accepted=accepted,expected_accepted=vector['native']=='true',sqlstate=state,output=out))
    if not all(r['accepted']==r['expected_accepted'] for r in crypto):raise RuntimeError('Native accepted-artifact parity failure')
    record['native_runtime_crypto']=dict(status='PASS',vectors=crypto,count=len(crypto),native_runtime_load='PASS')
    names=[v[0] for v in credentials.values()]
    roles=','.join("'"+n+"'" for n in names)
    record['service_effective_acl']=json.loads(sql("""SELECT json_build_object(
      'raw_table_privileges',(SELECT count(*) FROM pg_class t JOIN pg_namespace n ON n.oid=t.relnamespace CROSS JOIN pg_roles r WHERE r.rolname IN ("""+roles+""") AND n.nspname IN ('public','offline_crypto') AND t.relkind IN ('r','S') AND (has_table_privilege(r.oid,t.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') OR has_any_column_privilege(r.oid,t.oid,'SELECT,INSERT,UPDATE,REFERENCES'))),
      'private_or_frozen_execute',(SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN pg_roles r WHERE r.rolname IN ("""+roles+""") AND (p.proname LIKE 's2a_v04%' OR p.proname LIKE 'offline_internal_%' OR p.proname='offline_lock_bound_principal' OR n.nspname='offline_crypto') AND has_function_privilege(r.oid,p.oid,'EXECUTE')),
      'memberships',(SELECT count(*) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member WHERE r.rolname IN ("""+roles+""")));"""))
    probes=[]
    for owner in ['postgres','flooow_offline_control_owner']+list(source.OWNERS.values()):
        statement='BEGIN; GRANT CREATE ON DATABASE g3f4 TO '+owner+'; SET LOCAL ROLE '+owner+'; CREATE SCHEMA g3f4_probe; CREATE TABLE g3f4_probe.t (v int); CREATE FUNCTION g3f4_probe.f() RETURNS int LANGUAGE sql AS \'SELECT 1\'; CREATE TYPE g3f4_probe.e AS ENUM (\'x\'); RESET ROLE; '
        statement+="SELECT json_build_object('schema_public',EXISTS(SELECT 1 FROM pg_namespace n CROSS JOIN LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) a WHERE n.nspname='g3f4_probe' AND a.grantee=0),'function_public',has_function_privilege('public','g3f4_probe.f()','EXECUTE'),'table_public',EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a WHERE n.nspname='g3f4_probe' AND a.grantee=0),'type_public',EXISTS(SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace CROSS JOIN LATERAL aclexplode(coalesce(t.typacl,acldefault('T',t.typowner))) a WHERE n.nspname='g3f4_probe' AND a.grantee=0)); ROLLBACK;"
        leaks=json.loads(next(line for line in sql(statement).splitlines() if line.startswith('{')))
        probes.append(dict(owner=owner,leaks=leaks,probe_transaction='ROLLED_BACK_INCLUDING_TEMPORARY_DATABASE_CREATE_GRANT'))
    record['default_acl_probes']=probes
    save()

if __name__=='__main__':probe(sys.argv[1])
