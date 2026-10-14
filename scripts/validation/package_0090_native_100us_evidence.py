"""Conservative feasibility decision from real native clock samples."""
import json
import math
from pathlib import Path
import package_0090_native_100us as n
from test_package_0090_native_100us import validate_samples

NAMES=['POSTMASTER','SUPERVISOR','RECEIVER','CENSUS_OBSERVER','APPROVAL_PRODUCER','APPROVAL_CONSUMER','ENFORCEMENT_WORKER']


def stats(values):
    v=sorted(values)
    def percentile(p):return v[max(0,math.ceil(len(v)*p)-1)]/1000
    return {'n':len(v),'min_us':v[0]/1000,'p50_us':percentile(.5),'p90_us':percentile(.9),'p95_us':percentile(.95),'p99_us':percentile(.99),'max_us':v[-1]/1000}


def collect():
    root=n.OUT;accepted=root/'warm-3';variants={};timelines={};epoch_distributions={}
    for mode in ['unpinned','pin']:
        data=json.loads((accepted/('warm-'+mode+'.json')).read_text());validate_samples(data)
        samples=data['samples'][50:]
        variants[mode]={name:stats([p['age_ns'] for s in samples for p in s['participants'] if p['index']==i]) for i,name in enumerate(NAMES)}
        epochs=[{'epoch':s['epoch'],'oldest_age_ns':max(p['age_ns'] for p in s['participants']),
                 'newest_age_ns':min(p['age_ns'] for p in s['participants']),
                 'all_under_100us':s['consumer_under_100us']} for s in samples]
        epoch_distributions[mode]={'epochs':epochs,'oldest':stats([e['oldest_age_ns'] for e in epochs]),
                'newest':stats([e['newest_age_ns'] for e in epochs]),'attempts':len(epochs),
                'passes':sum(e['all_under_100us'] for e in epochs),'pass_rate':sum(e['all_under_100us'] for e in epochs)/len(epochs)}
        timelines[mode]={'guard_catalog_dependency':stats([s['guard_db_ns'] for s in samples]),
                'guard_fresh_signature_and_first_result_validation':stats([s['participants'][0]['t'][7]-s['participants'][0]['t'][8] for s in samples]),
                'participant_components':{name:{
                    'work':stats([p['t'][2]-p['t'][1] for s in samples for p in s['participants'] if p['index']==i]),
                    'serialization_and_send_preparation':stats([p['t'][4]-p['t'][2] for s in samples for p in s['participants'] if p['index']==i]),
                    'IPC_and_queue_and_guard_descheduling_combined':stats([p['t'][5]-p['t'][4] for s in samples for p in s['participants'] if p['index']==i]),
                    'credentials_pidfd_generation_combined':stats([p['t'][6]-p['t'][5] for s in samples for p in s['participants'] if p['index']==i]),
                    'guard_processing_after_identity':stats([p['t'][9]-p['t'][6] for s in samples for p in s['participants'] if p['index']==i]),
                    'end_to_end_age':variants[mode][name]} for i,name in enumerate(NAMES)},
                'hot_path_evidence_IO':'NONE','scheduler_policy':data['scheduler_policy'],
                'available_cpu_count':data['available_cpu_count'],'affinity_pinned':data['affinity_pinned']}
    n.a.save(root,'participant-latency-distributions.json',{'variants':variants,'steady_state_warmup_excluded_per_variant':50,'selected_final_variant':'pin'})
    n.a.save(root,'complete-epoch-distribution.json',{'variants':epoch_distributions,'steady_state_attempts':900,'passes':0,'pass_rate':0,
                'all_measurement_epochs_including_warmup':1020})
    n.a.save(root,'hot-path-timeline.json',{'source_raw_cold':'cold/cold-samples.json','source_raw_warm':['warm-3/warm-unpinned.json','warm-3/warm-pin.json'],
                'events':{'T0':'trigger received','T1':'barrier release / functional work starts','T2':'completed work','T3':'original emission timestamp serialized','T4':'authenticated send begins','T5':'recvmsg returns, kernel delivery observed','T6':'credentials/pidfd/generation validated','T7':'functional result validated','T8':'fresh guard catalog query finishes','T9':'complete guard decision','T10':'in-memory qualification consumer reads; not canonical readiness'},
                'event_order':'T8 may precede T7; preserve real partial ordering, do not force a fictional sequential timeline',
                'variants':timelines,'scheduler_wait_us':None,'scheduler_unavailable_reason':'Linux sched_schedstats observed0; retain raw counters but do not interpret zero as zero scheduler wait',
                'IPC_us':None,'queue_wait_us':None,'credential_validation_us_separate':None,'pidfd_validation_us_separate':None,
                'measurement_limits':'Transport/queue/descheduling cannot be separately attributed with compatible kernel timestamps in this capture. Credentials and pidfd checks have a measured combined span. These gaps remain explicit, not hidden in other.',
                'setup_legal_basis':'Current user phases4/5/6/9/10 authorize pre-established processes, connections/plans, providers, pidfds/channels, immutable identity expectations and buffers. Actual SQL queries/signatures/kernel action and validation are rerun each epoch.',
                'hot_path_evidence_IO':'NONE_OPTIMIZED_BASELINE_PRESENT', 'unsafe_realtime_privileges':False})
    pinned=timelines['pin'];tail=pinned['guard_catalog_dependency']['min_us']+pinned['guard_fresh_signature_and_first_result_validation']['min_us']
    measured_passes=sum(v['passes'] for v in epoch_distributions.values())
    n.q.require(measured_passes==0,'This bounded no-control report must not hide an actual timing pass')
    n.a.save(root,'measurement-integrity-tests.json',{'participant_mechanism_cases':[{'participant':name,'passed':True,'basis':'C work validation and retained positive causal timestamps for both500-epoch variants'} for name in NAMES],
        'complete_epoch_cases':[{'name':'exact_seven_participants','passed':True},{'name':'fresh_mechanism_work_valid','passed':True},{'name':'consumer_age_projection_matches_C','passed':True}],
        'count':10,'measurement_samples_not_counted_as_distinct_tests':True})
    decision={'100US_FEASIBILITY':'INCONCLUSIVE','tested_implementations_satisfy_100us':False,
              'VALID_FRESH_CONTROL':False,'FIRST_PATH_NATIVE_HEALTH_READY':False,
              'NATIVE_HEALTH_NEGATIVE_CAMPAIGN_PASS':'NOT_EXECUTED_NO_VALID_CONTROL',
              'RESTART_REPLACEMENT_FIRST_PATH_PASS':'NOT_EXECUTED_NO_VALID_CONTROL',
              'TIMING_AMENDMENT_REQUIRED_FOR_FURTHER_PROGRESS':False,
              'timing_amendment_proposed':False,'timing_amendment_adopted':False,
              'observed_pinned_serial_guard_tail_lower_bound_us':tail,
              'lower_bound_scope':'Empirical bound over tested serialized fresh guard catalog plus original-signature verification; not a physical or architectural universal bound',
              'dominant_components':['Cold shell/psql/startup catalog query22.3–40.9ms','Warm independent fresh DB query plus fresh Ed25519 verification and waiting for heterogeneous participant work'],
              'tested':['Original instrumented path20epochs','Persistent processes, barrier, prepared libpq and prepassed authenticated pidfds, normal scheduling','Same warmed protocol with deterministic eight-core affinity and normal scheduling'],
              'legitimate_avenues_remaining':['Nonblocking receive and incremental independent validation','Overlap fresh libpq catalog work and independent signature verification while preserving currentness','Prove exact catalog dependency/functional query requirements before reducing query work','Compatible kernel tracing for transport/runqueue attribution within authorized privileges'],
              'reason':'Zero of900 steady-state seven-mechanism epochs passed. Remaining legitimate concurrency/query avenues prevent an inherent NO or any timing-amendment claim. Full original-approval/lifecycle semantics remain unclosed independently of timing.'}
    n.a.save(root,'feasibility-decision.json',decision)
    for filename in ['valid-fresh-control.json','native-health-positive.json','native-health-negative.json','restart-replacement.json']:
        n.a.save(root,filename,{'status':'NOT_PROVEN_NO_VALID_FRESH_CONTROL','valid_fresh_control':False,
                  'full_contract_proven':False,'readiness_written':False,'timing_projection_passes':0})
    n.a.save(root,'READINESS.json',{**decision,'baseline':n.BASELINE,'source_sha256':n.q.SOURCE_HASH,
                'freshness_actual_us':100,'freshness_approved_max_us':200,'hot_path_evidence_IO':'NONE_OPTIMIZED',
                'readiness_created':False,'header_registered':False,'original_registered':False,'auditor_slot_authentic':False,
                'precheck':'FAIL_NO_VALID_NATIVE_FRESH_CONTROL','S04_executed':False,'S04_pass':False,'S04_actual_rows':None,
                'global_bound':0,'global_unbound':851,'S04_bound':0,'S04_unbound':33,
                'clock_boundary_tests':6,'participant_mechanism_assertions':7,'complete_epoch_integrity_assertions':3,
                'native_full_positive_tests':0,'native_negative_tests':0,'restart_tests':0,'readiness_tests':0,'S04_tests':0,
                'distinct_tests':16,'participant_measurement_samples':7140,'epoch_measurement_samples':1020,
                'accepted_failures':0,'primary_goal_valid_fresh_control_achieved':False,
                'scoped_blockers':1,'high_count':'UNKNOWN_FULL_NATIVE_SECURITY_REVIEW_NOT_EXECUTED',
                'medium_count':'UNKNOWN','low_count':'UNKNOWN','canonical_v043_executed':False,'canonical_v043_mutated':False,
                'shared_db_contacted':False,'production_contacted':False,'execution_authority':'BLOCKED','recovery_authority':'BLOCKED',
                'ROOM_OPERATIONAL':False,'NEXT_EXECUTED':False})
    n.a.save(root,'development-attempts.json',{'warm-1':'Diagnostic-buffer race; ages retained but invalid work timelines, excluded from accepted distributions',
                'warm-2':'Trace retention fixed, superseded by producer-only key generation; excluded from final custody-preserving distributions',
                'accepted_warm_cohort':'warm-3','raw_attempts_preserved':True})
    inputs=[n.q.ROOT/'scripts/validation'/name for name in ['package_0090_active_foundation.py','package_0090_native_100us.py','package_0090_native_100us_warm.c',
              'package_0090_s04_native_health.c','test_package_0090_native_100us.py','package_0090_native_100us_evidence.py']]
    doc=n.q.ROOT/'docs/evidence/PACKAGE-0090-native-health-100us-feasibility.md'
    if doc.exists():inputs.append(doc)
    n.a.save(root,'SHA256-MANIFEST.json',{'inputs':{p.relative_to(n.q.ROOT).as_posix():n.q.sha(p.read_bytes()) for p in inputs},
            'outputs':{p.relative_to(root).as_posix():n.q.sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'},
            'canonical_git_lf_sha256':n.q.sha(n.q.git('show','HEAD:'+n.q.V043.relative_to(n.q.ROOT).as_posix()))})
    print(json.dumps(decision,indent=2))


if __name__=='__main__':collect()
