"""Native/language/collation bindings checked without native-health activation."""
import json,re
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT

def qualify(sql,run,container,folder,record,fixture,runtime_work):
 record['recipe_hashes'][Path(__file__).name]=q.sha(Path(__file__).read_bytes());cases=[];native=json.loads((OUT/'native-provider-identities.json').read_text())
 def case(name,passed,details,group):
  c=dict(name=name,passed=bool(passed),details=details,group=group);cases.append(c);record['cases'].append(c);q.require(passed,name)
 entries=native['ELF_files']+native.get('locale_data_files',[])+[native['custom_module']]
 output=run(['docker','exec',container,'sha256sum',*[x['path'] for x in entries]]).decode().splitlines();actual={line.split(None,1)[1].strip():line.split()[0] for line in output}
 for row in entries:
  path=row['path'];case('native_file_'+path,actual.get(path)==row['sha256'],dict(path=path,expected=row['sha256'],observed=actual.get(path)),'POLICY_NATIVE_AUDIT_EXPECTATION')
  stat=run(['docker','exec',container,'stat','-Lc','%u:%g:%a',path]).decode().strip();uid,gid,mode=stat.split(':');case('native_provider_owner_'+path,uid=='0' and gid=='0' and int(mode,8)&0o022==0,dict(path=path,observed=stat,rule='Root-owned and not writable by group/other; loaded identity/currentness requires separate future guard proof'),'POLICY_NATIVE_AUDIT_EXPECTATION')
 profile=json.loads(sql("SELECT jsonb_build_object('name',l.lanname,'owner',pg_get_userbyid(l.lanowner),'ispl',l.lanispl,'trusted',l.lanpltrusted,'handler',l.lanplcallfoid='pg_catalog.plpgsql_call_handler()'::regprocedure,'inline',l.laninline='pg_catalog.plpgsql_inline_handler(internal)'::regprocedure,'validator',l.lanvalidator='pg_catalog.plpgsql_validator(oid)'::regprocedure,'acl',l.lanacl) FROM pg_language l WHERE l.lanname='plpgsql';").stdout)
 case('plpgsql_language_dispatch_exact',profile==dict(name='plpgsql',owner='postgres',ispl=True,trusted=True,handler=True,inline=True,validator=True,acl=None),profile,'FUNCTION_IDENTITY')
 colls=json.loads((OUT/'collation-v2.json').read_text())['providers'];fields=list(colls[0]);parts=[]
 for field in fields:parts.extend(["'"+field+"'",'c.'+field+'::text'])
 actual_colls=json.loads(sql('SELECT jsonb_agg(jsonb_build_object('+','.join(parts)+') ORDER BY c.oid) FROM pg_collation c WHERE c.oid IN (100,950);').stdout);by_oid={x['oid']:x for x in actual_colls}
 for expected in colls:
  wanted={k:(None if v=='_null_' else 'true' if k=='collisdeterministic' and v=='t' else 'false' if k=='collisdeterministic' and v=='f' else v) for k,v in expected.items()};a=by_oid.get(expected['oid']);case('collation_'+expected['collname'],wanted==a,dict(expected=wanted,observed=a),'TYPE')
 db=json.loads(sql("SELECT jsonb_build_object('encoding',pg_encoding_to_char(d.encoding),'provider',d.datlocprovider,'collate',d.datcollate,'ctype',d.datctype,'locale',d.datlocale,'version',d.datcollversion,'owner',pg_get_userbyid(d.datdba)) FROM pg_database d WHERE d.datname=current_database();").stdout);expected=dict(encoding='UTF8',provider='c',collate='en_US.utf8',ctype='en_US.utf8',locale=None,version=native['libc_version'].split()[-1],owner='postgres');case('database_locale_bootstrap_exact',db==expected,dict(expected=expected,observed=db),'TYPE')
 case('PostgreSQL_REL18_4_exact',sql('SHOW server_version_num;').stdout.strip()==b'180004','Approved image/source target PostgreSQL 18.4','TYPE')
 (folder/'native-provider-runtime.json').write_text(json.dumps(dict(cases=cases,files=actual,language=profile,collations=actual_colls,database=db,native_health_work_claimed=False),indent=2)+'\n')
