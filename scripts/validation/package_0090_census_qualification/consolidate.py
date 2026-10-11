"""Evidence index: final exact runtime bytes only, never inherited PASS."""
from pathlib import Path
import json,hashlib,subprocess,math
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
runtime=['receiver.c','supervisor.c','login.c','protocol.h','heartbeat.h','census.h','frame_tests.c','boottime.c']
final_hashes={n:sha(HERE/n) for n in runtime}
rounds=load(OUT/'FINAL-SELECTED-ROUNDS.json')['rounds'];entries=[];cases=[]
for row in rounds:
    dest=ROOT/row['directory'];rawpath=dest/'RAW-QUALIFICATION.json'
    raw=load(rawpath) if rawpath.exists() else {'cases':[],'errors':['BUILD_OR_SETUP_FAILED_BEFORE_RUNTIME']}
    inputs=load(dest/'BUILD-INPUT-SHA256.json')['files']
    copied={}
    for operation in load(dest/'BUILD.json'):
        if operation['command'][-1]=='sha256sum /usr/local/src-full/*.c /usr/local/src-full/*.h':
            for line in operation['stdout'].splitlines():
                digest,filename=line.split(maxsplit=1);copied[Path(filename).name]=digest
    equal=all(inputs.get(n)==h and copied.get(n)==h for n,h in final_hashes.items())
    extras=['heartbeat_tests.c','binding_encode.c','binding_codec.c'] if row['module']=='binding_encoding_probe' else ['fake_receiver.c'] if row['module']=='socket_probe' else []
    entry={**row,'final_runtime_bytes_equal':equal,'compiled_copy_sha256':copied,'extra_compiled_components_equal':all(inputs.get(n)==sha(HERE/n) and copied.get(n)==sha(HERE/n) for n in extras),'N':len(raw['cases']),'FAIL':sum(c['result']=='FAIL' for c in raw['cases']),'NOT_RUN':sum(c['result'].startswith('NOT_RUN') for c in raw['cases']),'errors':raw['errors'],'cleanup':{k:raw.get(k) for k in ['private_key_erasure','private_key_absent','owned_container_removed']},'binary_hashes':raw.get('binary_hashes'),'build_input_sha256':sha(dest/'BUILD-INPUT-SHA256.json')}
    entries.append(entry)
    for c in raw['cases']:cases.append({**c,'round':row['module'],'evidence':row['directory'],'final_runtime_bytes_equal':equal})
common={'scope':'TEST_ONLY_NONCANONICAL','gate':'HOLD','runtime_source_sha256':final_hashes,'inherited_runtime_PASS_used':False,'numeric_policy_authority':'NONE'}
selection=load(OUT/'FINAL-SELECTED-ROUNDS.json')
retained_races=[{'finding':'PRE_ENROLLMENT_CENSUS_DURING_LIVE_QUARANTINE','evidence':row['directory'],'disposition':'OPEN_HOLD','retained_error':load(ROOT/row['directory']/'RAW-QUALIFICATION.json')['errors'],'not_resolved_by_harness_retry':True} for row in selection.get('superseded_drain_rounds',[]) if load(ROOT/row['directory']/'RAW-QUALIFICATION.json')['errors']]
save('POST-ATTEMPT10-FULL-REGRESSION.json',{**common,'rounds':entries,'N':len(cases),'N_EXECUTED_ASSERTIONS':sum(not c['result'].startswith('NOT_RUN') for c in cases),'FAIL':sum(c['result']=='FAIL' for c in cases),'NOT_RUN':sum(c['result'].startswith('NOT_RUN') for c in cases),'cases':cases,'retained_final_byte_open_races':retained_races,'complete_frozen_domain_regression':False})
groups={
 'INDEPENDENT-SERVER-CENSUS.json':['census'],
 'PARTICIPANT-LIVENESS.json':['heartbeat','heartbeat_protocol'],
 'OID-REUSE-TOMBSTONE.json':['tombstone'],
 'FULL-CONTEXT-REPLAY-SOCKET.json':['protocol','clone','admission','restart','socket','replay'],
 'ACTIVE-ENFORCEMENT-FULL-MATRIX.json':['enforcement','drain','heartbeat','active_death'],
 'FULL-DOMAIN-RECONCILIATION.json':['effect','domain','ownership','ownership_row_contract','domain_query_first','active_death'],
 'OWNERSHIP-PARITY.json':['effect','domain','ownership','ownership_row_contract'],
 'POSTMASTER-CONTROL-CONSISTENCY.json':['restart','heartbeat'],
 'CONTINUOUS-COVERAGE.json':['census','heartbeat','enforcement','drain']}
for name,groupset in groups.items():
    selected=[c for c in cases if c['group'] in groupset]
    save(name,{**common,'cases':selected,'full_contract_PASS_claimed':False,'limitations':['Serial census and catalog queries run in receiver; separate exhaustive independent worker is not qualified.','No independent enforcer with all retained backend anchors has been qualified under compound receiver/postmaster stalls.','Synthetic table observations are not full frozen claim/attempt/effect/retry wrappers.','All failures and NOT_RUN cases remain open unless explicitly resolved by final-byte rerun.']})
progress=next((ROOT/r['directory'] for r in rounds if r['module']=='progress_probe'),None)
liveness=load(OUT/'PARTICIPANT-LIVENESS.json')
liveness['PROCESS_ALIVE_IS_NOT_PARTICIPANT_MAKING_PROGRESS']=True
liveness['liveness_renewal_basis']='Validated original CLOCK_BOOTTIME emission timestamp, never receipt time'
liveness['stale_queued_heartbeat_evidence']=[c for c in cases if c['group']=='heartbeat_protocol']
if progress:
    log=(progress/'NATIVE-RUNTIME.log').read_text(encoding='utf-8')
    events=[json.loads(line) for line in log.splitlines() if line.startswith('{')]
    witness=False
    for i,event in enumerate(events):
        if event.get('event')=='receiver_progress_lost':
            for following in events[i+1:]:
                if following.get('event')=='supervisor_started':break
                if following.get('event')=='supervisor_generation_loss':
                    witness=witness or following.get('receiver_dead') is False;break
    liveness['alive_receiver_at_progress_loss_observed']=witness
save('PARTICIPANT-LIVENESS.json',liveness)
save('FROZEN-DOMAIN-PARITY.json',{**common,'public_reference_evidence':['BINDING-REFERENCE-PARITY.json','HUP-FINAL-PUBLIC-JVM-PARITY.json'],'final_native_encoding_cases':[c for c in cases if c['group']=='encoding'],'byte_and_public_signature_primitives':'QUALIFIED_SELECTED_VECTORS','full_semantic_verifier_authority_source_consumption_policy_parity':'HOLD_NOT_QUALIFIED','migration_interlock':'PRESERVED_MIGRATION_EXECUTABLE_NO','runtime_inherited_PASS_used':False})
cohorts={}
for c in cases:
    d=c.get('detail');samples=d.get('requests',[]) if isinstance(d,dict) else []
    if isinstance(d,dict) and 'elapsed_us' in d:samples=[d]
    if samples:
        key=c['round']+'/'+c['group']+'/'+c['name'];values=sorted(s['elapsed_us'] for s in samples if isinstance(s.get('elapsed_us'),(int,float)))
        def p(q):return values[max(0,math.ceil(q*len(values))-1)] if values else None
        cohorts[key]={'N':len(values),'FAIL':sum(s.get('exit',0)!=0 for s in samples),'CENSORED':None,'censoring_accounting':'HOLD_NOT_INDEPENDENTLY_ENUMERATED','P50_us':p(.5),'P95_us':p(.95),'P99_us':p(.99),'MAX_us':max(values) if values else None,'case_result':c['result'],'samples':samples,'tail_qualification':False}
native={}
for row in rounds:
    path=ROOT/row['directory']/'NATIVE-RUNTIME.log'
    if not path.exists():continue
    events=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.startswith('{')]
    for kind in ['ACCEPT','DENY']:
        values=sorted(e['reply_us'] for e in events if e.get('event')==kind and 'reply_us' in e)
        if not values:continue
        native[row['module']+'/'+kind]={'N':len(values),'FAIL':None,'CENSORED':None,'P50_us':values[math.ceil(.5*len(values))-1],'P95_us':values[math.ceil(.95*len(values))-1],'P99_us':values[math.ceil(.99*len(values))-1],'MAX_us':max(values),'raw_reply_us':values,'metric':'receiver validation/reply elapsed, not end-to-end login latency','timing_exceedance_policy':'NONE_AUTHORIZED','tail_qualification':False}
required={name:{'status':'HOLD_INCOMPLETE_QUALIFICATION','N':None,'FAIL':None,'CENSORED':None,'reason':'No complete independently tagged representative distribution; selected case timings remain in cohorts, never inferred as a full cohort or zero.'} for name in ['warm idle','cold','CPU contention','tmpfs I/O','connection churn','receiver recovery','supervisor recovery','postmaster rebootstrap','revocation enforcement','cancel path','terminate path','drain','census detection','heartbeat stall detection','persistent-storage I/O']}
save('TIMING-QUALIFICATION.json',{**common,'cohorts':cohorts,'native_round_observations':native,'required_cohort_qualification':required,'percentile_method':'nearest-rank descriptive only; tiny N is not tail qualification','NUMERIC_CANDIDATE_EVIDENCE_READY':False,'NUMERIC_VALUES_ADOPTED':False,'controls':'abort5s / gate20s / heartbeat10s / cancel-to-terminate200ms are experimental only','bound_proposal':None,'failure_vs_expected_denial':'Nonzero client exit may be expected fault handling, not an unexplained implementation failure; case_result records assertion outcome. Null means unqualified/unknown, never zero.'})
audit=load(OUT/'FROZEN-PRESERVATION-AUDIT.json')
owned=subprocess.run(['docker','ps','-aq','--filter','label=flooow.scope=0090-census-heartbeat-domain-parity'],capture_output=True,text=True,check=True).stdout.strip()
save('CANONICAL-NON-MUTATION-PROOF.json',{**common,'proof_scope':'Agent target/action inventory and frozen source hashes, not a claim of global host-state equivalence','HISTORICAL_HASHES_INTACT':audit['failures']==0,'historical_N':audit['N'],'CANONICAL_V6_ACCESSED':False,'CANONICAL_V6_MUTATED':False,'CANONICAL_DATABASE_MUTATED':False,'CANONICAL_IDS_USED':False,'CANONICAL_KEYS_USED':False,'T0_CONSUMED':False,'CANONICAL_SIGN_EXECUTED':False,'CANONICAL_ADMIN_EXECUTED':False,'TREG_EXECUTED':False,'FINAL_RUNNER_EXECUTED':False,'NUMERIC_VALUES_ADOPTED':False,'owned_container_ids_remaining':owned.splitlines(),'DISPOSABLE_RESOURCES_REMOVED':not owned,'TEST_PRIVATE_KEYS_ERASED':all(e['cleanup']['private_key_absent'] and e['cleanup']['private_key_erasure'] for e in entries if e['cleanup']['owned_container_removed']),'rounds':entries})
print('FINAL_N',len(cases),'FAIL',sum(c['result']=='FAIL' for c in cases),'NOT_RUN',sum(c['result'].startswith('NOT_RUN') for c in cases),'ROUND_ERRORS',sum(bool(e['errors']) for e in entries),'EXACT_FINAL_BYTES',all(e['final_runtime_bytes_equal'] for e in entries),'OWNED_REMAINING',bool(owned))
