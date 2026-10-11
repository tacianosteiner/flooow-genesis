"""Fresh isolated complete-artifact consumer; no native protocol mutations."""
from pathlib import Path
import json,hashlib,subprocess,sys,uuid,tempfile,shutil,os,time,datetime,traceback,socket,threading,io,tarfile
from verify import verify
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
IMAGE='sha256:07fc165de5bb569d822460e2df645c5489f99220fc2cb16c86596d39db394561'
HEAD='0db4b7bed49ca76ca879875057d75bc2e68b0296'
SOURCE='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration'
BASE='19131bb9cd655312252c8c83f0f78e7c0742274f'
MAC='applications/marketplace-operations-persistence-postgres/native/flooow_offline_mac32'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    envelope=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert not out.exists();out.mkdir(parents=True)
    checked=verify(envelope);manifest=json.loads((envelope/'PROMOTION-MANIFEST.json').read_text());nonce=uuid.uuid4().hex[:12];name='flooow-0090-promotion-'+nonce;network=name+'-isolated'
    record={'input_head':HEAD,'marker':'TEST_ONLY_NONCANONICAL','execution_identity':manifest['rehearsal_execution_identity'],'manifest_sha256':checked['manifest_sha256'],'successor_sha256':checked['successor_sha256'],'cases':[],'errors':[],'not_run':[],'native_protocol_changed':False,'numeric_values_adopted':False,'canonical_access':False,'canonical_mutation':False,'commands':[],'container_removed':False,'network_removed':False,'plaintext_secrets_created':False}
    def save(): (out/'RAW.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
    def call(args,data=None,ok=True,timeout=60):
        r=subprocess.run(args,input=data,capture_output=True,timeout=timeout)
        record['commands'].append({'command':args,'exit':r.returncode,'stdout':r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace')})
        if ok and r.returncode:raise RuntimeError('Failed '+args[0]+': '+r.stderr.decode(errors='replace')[-2500:])
        return r
    def ex(*args,user='postgres',data=None,ok=True):return call(['docker','exec','--user',user,'-i',name,*args],data,ok)
    def sql(text,role='postgres',ok=True):return ex('psql','-X','-w','-h','/tmp/pgsock','-U',role,'-d','promotion_fixture','-At','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose',data=text.encode(),ok=ok)
    def case(id,success,detail):
        record['cases'].append({'id':id,'result':'PASS' if success else 'FAIL','detail':detail});print(id+': '+('PASS' if success else 'FAIL'),flush=True)
    created_network=False;created_container=False;relay=None;relay_children=[]
    scratch=Path(tempfile.mkdtemp(prefix='flooow-current-promotion-'));assert scratch.resolve().parent==Path(tempfile.gettempdir()).resolve()
    try:
        migrations=scratch/'migrations';migrations.mkdir();inventory=[]
        for p in sorted((ROOT/SOURCE).glob('V*.sql')):
            version=int(p.name.split('__')[0][1:])
            if version>42:continue
            path=p.relative_to(ROOT).as_posix();accepted=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT);current=subprocess.check_output(['git','show',HEAD+':'+path],cwd=ROOT);assert accepted==current
            (migrations/p.name).write_bytes(accepted);inventory.append({'path':path,'sha256':sha(accepted)})
        assert len(inventory)==42;record['prerequisite_migration_inventory']=inventory
        successor=envelope/manifest['successor_filename'];shutil.copyfile(successor,migrations/'V043__TEST_ONLY_NONCANONICAL_executable_successor.sql')
        # Fixed cached dependency versions, no downloading or dependency changes.
        cache=Path.home()/'.gradle/caches/modules-2/files-2.1'
        core=list((cache/'org.flywaydb/flyway-core/13.2.0').rglob('*.jar'));driver=list((cache/'org.postgresql/postgresql/42.7.12').rglob('*.jar'));assert len(core)==len(driver)==1
        other=[p for p in sorted(cache.rglob('*.jar')) if p not in core+driver and not p.name.startswith(('flyway-core-','postgresql-'))]
        cp=os.pathsep.join(str(p) for p in core+driver+other);record['dependency_jars']=[{'name':p.name,'sha256':sha(p.read_bytes())} for p in core+driver+other]
        args=scratch/'compile.args';args.write_text('-cp\n"'+cp.replace('\\','/')+'"\n-d\n"'+scratch.as_posix()+'"\n"'+(HERE/'CurrentPromotionFlyway.java').as_posix()+'"\n')
        call(['javac','@'+str(args)]);record['consumer_class_sha256']=sha((scratch/'CurrentPromotionFlyway.class').read_bytes())
        record['consumer_binary_set']={p.name:sha(p.read_bytes()) for p in scratch.glob('CurrentPromotionFlyway*.class')}
        consumed=migrations/'V043__TEST_ONLY_NONCANONICAL_executable_successor.sql';original=consumed.read_bytes()
        try:
            consumed.write_bytes(original+b'\n-- TEST_ONLY_NONCANONICAL material substitution\n')
            for mode in ['original_expected_hash','rehashed_resource_map']:
                props=scratch/'negative.properties'
                lines=['marker=TEST_ONLY_NONCANONICAL','manifest='+str(envelope/'PROMOTION-MANIFEST.json').replace('\\','/'),'manifest_sha256='+checked['manifest_sha256'],'successor='+successor.as_posix(),'successor_sha256='+checked['successor_sha256'],'url=jdbc:postgresql://127.0.0.1:1/promotion_fixture','migrations='+migrations.as_posix(),'target=043']
                lines += ['migration_sha256.'+Path(row['path']).name+'='+row['sha256'] for row in inventory]
                lines += ['migration_sha256.'+consumed.name+'='+(checked['successor_sha256'] if mode=='original_expected_hash' else sha(consumed.read_bytes()))]
                props.write_text('\n'.join(lines)+'\n')
                negative=scratch/'negative.args';negative.write_text('-cp\n"'+(str(scratch)+os.pathsep+cp).replace('\\','/')+'"\nCurrentPromotionFlyway\n"'+props.as_posix()+'"\n')
                result=call(['java','@'+str(negative)],ok=False)
                case('actual_consumer_rejects_material_substitution_'+mode,result.returncode!=0 and b'CONSUMED_' in result.stderr and b'Unable to obtain connection' not in result.stderr,{'rejected_before_database_connection':True,'stderr':result.stderr.decode(errors='replace')})
        finally:consumed.write_bytes(original)
        call(['docker','network','create','--internal','--label','flooow.scope=0090-executable-promotion',network]);created_network=True
        call(['docker','run','--detach','--name',name,'--label','flooow.scope=0090-executable-promotion','--label','flooow.promotion.manifest='+checked['manifest_sha256'],'--label','flooow.execution.identity='+manifest['rehearsal_execution_identity'],'--network',network,'-p','127.0.0.1::5432','--tmpfs','/tmp','--tmpfs','/run','--tmpfs','/var/lib/postgresql','--cpus','1','--memory','768m','--entrypoint','sleep',IMAGE,'infinity']);created_container=True
        def endpoint():
            info=json.loads(call(['docker','inspect',name]).stdout)[0]
            assert info['Image']==IMAGE and info['Config']['Labels']['flooow.promotion.manifest']==checked['manifest_sha256']
            assert info['Config']['Labels']['flooow.execution.identity']==manifest['rehearsal_execution_identity']
            assert not info['Mounts'] and info['HostConfig']['NetworkMode']==network
            n=json.loads(call(['docker','network','inspect',network]).stdout)[0];assert n['Internal'] and n['Labels']['flooow.scope']=='0090-executable-promotion'
            ports=info['NetworkSettings']['Ports']['5432/tcp'];assert not ports, 'Internal network must expose no Docker host port'
            record['isolation']={'container_id':info['Id'],'network_id':n['Id'],'internal_network':True,'mounts':info['Mounts'],'ports':ports,'image':info['Image'],'execution_identity':manifest['rehearsal_execution_identity']}
            assert relay is not None
            return 'jdbc:postgresql://127.0.0.1:'+str(relay.getsockname()[1])+'/promotion_fixture'
        # Internal Docker networks deliberately do not publish ports. A loopback
        # relay enters only this owned container through docker exec, without egress.
        relay=socket.socket();relay.bind(('127.0.0.1',0));relay.listen()
        def connections():
            while True:
                try:conn,_=relay.accept()
                except OSError:return
                def forward(conn):
                    proc=subprocess.Popen(['docker','exec','-i',name,'/usr/local/bin/test-only-jdbc-relay'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);relay_children.append(proc)
                    def inbound():
                        try:
                            while b:=conn.recv(65536):proc.stdin.write(b);proc.stdin.flush()
                        except (OSError,BrokenPipeError):pass
                        finally:proc.stdin.close()
                    threading.Thread(target=inbound,daemon=True).start()
                    try:
                        while b:=proc.stdout.read1(65536):conn.sendall(b)
                    except OSError:pass
                    finally:
                        conn.close();proc.wait(timeout=10)
                        record.setdefault('relay_exits',[]).append({'exit':proc.returncode,'stderr':proc.stderr.read().decode(errors='replace')})
                threading.Thread(target=forward,args=(conn,),daemon=True).start()
        threading.Thread(target=connections,daemon=True).start()
        endpoint();case('independent_target_boundary',True,record['isolation'])
        ex('mkdir','-p','/tmp/pgsock');ex('initdb','-D','/tmp/pgdata','--auth=trust','--no-locale','--encoding=UTF8')
        ex('pg_ctl','-D','/tmp/pgdata','-l','/tmp/postgres.log','-o',"-k /tmp/pgsock -c listen_addresses='*'",'-w','start');ex('createdb','-h','/tmp/pgsock','promotion_fixture')
        relay_source=b'''#include <unistd.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <stdlib.h>
static void sendall(int fd,char*b,int n){while(n>0){int w=write(fd,b,n);if(w<=0)exit(2);b+=w;n-=w;}}
int main(){int s=socket(AF_INET,SOCK_STREAM,0);struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(5432),.sin_addr.s_addr=htonl(INADDR_LOOPBACK)};if(connect(s,(void*)&a,sizeof(a)))return 3;for(;;){fd_set f;FD_ZERO(&f);FD_SET(0,&f);FD_SET(s,&f);if(select(s+1,&f,0,0,0)<0)return 4;char b[65536];if(FD_ISSET(0,&f)){int n=read(0,b,sizeof(b));if(n<=0)return 0;sendall(s,b,n);}if(FD_ISSET(s,&f)){int n=read(s,b,sizeof(b));if(n<=0)return 0;sendall(1,b,n);}}}'''
        ex('gcc','-x','c','-O2','-o','/usr/local/bin/test-only-jdbc-relay','-',data=relay_source,user='0')
        record['experimental_transport_relay_source_sha256']=sha(relay_source)
        def migrate(target):
            nowverify=verify(envelope);assert nowverify==checked
            assert sha((migrations/'V043__TEST_ONLY_NONCANONICAL_executable_successor.sql').read_bytes())==manifest['successor_sha256']
            for row in inventory:assert sha((migrations/Path(row['path']).name).read_bytes())==row['sha256']
            url=endpoint();props=scratch/'consumer.properties';props.write_text('\n'.join(['marker=TEST_ONLY_NONCANONICAL','manifest='+str(envelope/'PROMOTION-MANIFEST.json').replace('\\','/'),'manifest_sha256='+checked['manifest_sha256'],'successor='+successor.as_posix(),'successor_sha256='+checked['successor_sha256'],'url='+url,'migrations='+migrations.as_posix(),'target='+target])+'\n')
            with props.open('a') as f:
                for row in inventory:f.write('migration_sha256.'+Path(row['path']).name+'='+row['sha256']+'\n')
                f.write('migration_sha256.V043__TEST_ONLY_NONCANONICAL_executable_successor.sql='+checked['successor_sha256']+'\n')
            java=scratch/'run.args';java.write_text('-cp\n"'+(str(scratch)+os.pathsep+cp).replace('\\','/')+'"\nCurrentPromotionFlyway\n"'+props.as_posix()+'"\n')
            r=call(['java','@'+str(java)],ok=False,timeout=180);(out/('FLYWAY-'+target+'.log')).write_bytes(r.stdout+r.stderr)
            if r.returncode:raise RuntimeError('Complete artifact migration failed: '+r.stderr.decode(errors='replace')[-2000:])
            case('complete_artifact_migration_'+target,True,{'consumer':'Actual Flyway 13.2.0 / JDBC 42.7.12','manifest':checked,'fragment_execution':False})
        migrate('042')
        owners=['control','verification','issuance','execution','audit','readiness','principal_lock','intent_audit']
        setup=[]
        for owner in owners:
            setup.append('CREATE ROLE flooow_offline_'+owner+'_owner NOLOGIN '+('INHERIT' if owner=='control' else 'NOINHERIT')+' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;')
        for role in ['postgres']+['flooow_offline_'+o+'_owner' for o in owners]:
            for kind in ['TABLES','SEQUENCES','FUNCTIONS','TYPES','SCHEMAS','LARGE OBJECTS']:setup.append('ALTER DEFAULT PRIVILEGES FOR ROLE '+role+' REVOKE ALL ON '+kind+' FROM PUBLIC;')
        setup.append('GRANT USAGE ON SCHEMA public TO flooow_offline_control_owner;');sql('\n'.join(setup))
        # Stream through exec into the live tmpfs; Docker archive cp can write
        # beneath a tmpfs mount instead of into the running mounted filesystem.
        archive=io.BytesIO()
        with tarfile.open(fileobj=archive,mode='w') as tar:
            for p in sorted((ROOT/MAC).iterdir()):
                if p.is_file():tar.add(p,arcname='native/'+p.name)
        ex('mkdir','-p','/review',user='0')
        ex('tar','-xf','-','-C','/review',data=archive.getvalue(),user='0')
        ex('sh','-c','cd /review/native && make with_llvm=no && make install with_llvm=no',user='0')
        native=ex('sha256sum','/review/native/flooow_offline_mac32.so',user='0').stdout.decode().split()[0];record['frozen_crypto_binary_sha256']=native
        assert native=='5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5'
        sql("CREATE SCHEMA offline_crypto AUTHORIZATION postgres; CREATE EXTENSION pgcrypto VERSION '1.4' SCHEMA offline_crypto; CREATE EXTENSION flooow_offline_mac32 VERSION '1.0'; REVOKE ALL ON SCHEMA offline_crypto FROM PUBLIC; REVOKE ALL ON ALL FUNCTIONS IN SCHEMA offline_crypto FROM PUBLIC; GRANT USAGE ON SCHEMA offline_crypto TO flooow_offline_readiness_owner; GRANT EXECUTE ON FUNCTION offline_crypto.hmac(bytea,bytea,text),offline_crypto.timing_safe_equal32(bytea,bytea) TO flooow_offline_readiness_owner;")
        migrate('043')
        record['flyway_history']=json.loads(sql("SELECT json_agg(json_build_object('version',version,'script',script,'checksum',checksum,'success',success) ORDER BY installed_rank) FROM flyway_schema_history;").stdout)
        case('complete_committed_43_history',len(record['flyway_history'])==43 and all(r['success'] for r in record['flyway_history']),record['flyway_history'])
        oracle=json.loads((ROOT/'docs/evidence/PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json').read_text())
        record['installed_public_contracts']=oracle['public_contracts']
        setup=[]
        for slot in ['AUDITOR','VERIFIER','ISSUER','EXECUTOR']:
            role='test_only_'+slot.lower()+'_'+nonce;setup.append('CREATE ROLE '+role+' LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; GRANT USAGE ON SCHEMA public TO '+role+';')
            for contract in oracle['public_contracts'].values():
                if contract['slot']==slot:setup.append('GRANT EXECUTE ON FUNCTION '+contract['signature']+' TO '+role+';')
        sql('\n'.join(setup))
        for slot in ['AUDITOR','VERIFIER','ISSUER','EXECUTOR']:
            role='test_only_'+slot.lower()+'_'+nonce
            leak=sql("SELECT count(*) FROM pg_class t JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname IN ('public','offline_crypto') AND t.relkind IN ('r','S') AND (has_table_privilege('"+role+"',t.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') OR has_any_column_privilege('"+role+"',t.oid,'SELECT,INSERT,UPDATE,REFERENCES'));").stdout.decode().strip()
            case('service_raw_acl_absent_'+slot,leak=='0',{'raw_privileges':leak,'grants':'Exact existing reviewed S surface only; initial synthetic role fixture, no expansion beyond reviewed surface'})
        record['post_install_governance_rows']=json.loads(sql("SELECT json_build_object('header', (SELECT count(*) FROM offline_binding_header),'readiness',(SELECT count(*) FROM offline_readiness),'policy',(SELECT count(*) FROM offline_deadline_policy),'expected_attestation',(SELECT count(*) FROM offline_expected_signed_attestation));").stdout)
        record['next_positive_boundary']='No current synthetic governed binding/authority/readiness lineage has been provisioned. No numeric policy fixture is provisioned and no unsupported health attestation is manufactured.'
        # Current exact installed wrapper is exercised; denial is not positive parity.
        a,b=uuid.uuid4(),uuid.uuid4();role='test_only_auditor_'+nonce
        r=sql("BEGIN READ ONLY ISOLATION LEVEL REPEATABLE READ; SELECT offline_preflight('"+str(a)+"',decode(repeat('01',32),'hex'),'"+str(b)+"','0090-v1',decode(repeat('02',32),'hex'),decode(repeat('03',32),'hex'),decode(repeat('04',32),'hex'));",role,ok=False)
        case('actual_promoted_preflight_missing_current_binding_denied',r.returncode!=0 and b'P0017' in r.stderr,{'sqlstate':'P0017','stderr':r.stderr.decode(),'positive_execution':False,'row_counts':record['post_install_governance_rows']})
        stages=['claim','verification','admission','ownership_acquisition','effect_transition','terminal_transition','retry_replay_denial','ownership_retention','ownership_release','reconciliation_required','reconciliation_completion','full_authority_joins','runtime_consumption_positive']
        for stage in stages:record['not_run'].append({'CASE':stage,'BLOCKING_FINDING':'CURRENT_SYNTHETIC_GOVERNED_LINEAGE_NOT_PROVISIONED','WHY_NOT_EXECUTABLE':'Complete successor installed; positive wrappers require current full binding, authority/source/accepted-consumption lineage and separately satisfied readiness/policy predicates. Empty installed tables cannot establish them. No stub, copied canonical context or invented numeric authority is substituted.','WHAT_AUTHORITY_OR_ARTIFACT_MISSING':'Hash-bound complete noncanonical full-domain fixture contract resolving source/approval/attestation lineage, truthful readiness witness and explicitly permitted experimental policy fixture handling without numeric authority.'})
    except Exception as e:
        record['errors'].append({'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()});print('ERROR '+traceback.format_exc(),flush=True)
    finally:
        if relay is not None:relay.close()
        for child in relay_children:
            if child.poll() is None:child.terminate();child.wait(timeout=10)
        if created_container:
            info=json.loads(call(['docker','inspect',name]).stdout)[0];assert info['Config']['Labels']['flooow.scope']=='0090-executable-promotion'
            logs=ex('cat','/tmp/postgres.log',ok=False);(out/'POSTGRES.log').write_bytes(logs.stdout+logs.stderr)
            call(['docker','rm','-f',info['Id']]);record['container_removed']=True
        if created_network:call(['docker','network','rm',network]);record['network_removed']=True
        # Scratch contains no credentials/keys. Only this newly owned verified path.
        assert scratch.resolve().parent==Path(tempfile.gettempdir()).resolve() and scratch.name.startswith('flooow-current-promotion-')
        shutil.rmtree(scratch);record['scratch_removed']=True;save()
    return int(bool(record['errors']) or any(c['result']=='FAIL' for c in record['cases']))
if __name__=='__main__':raise SystemExit(main())
