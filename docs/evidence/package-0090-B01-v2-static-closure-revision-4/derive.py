"""R4 evidence-only derivation. Git/source/JSON reads; never SQL/native/runtime.

All incomplete physical proofs remain explicit. Proposed modules are data, not
executables. Run python -B derive.py; reviews/seal are separate steps.
"""
import sys
sys.dont_write_bytecode = True
import collections
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = 'fad53f6241724ea01e3ae552ebf6fe1e09794ea5'
BRANCH = 'checkpoint/package-0090-cloud-handoff'
R3 = 'docs/evidence/package-0090-B01-v2-static-closure-revision-3/'
R2 = 'docs/evidence/package-0090-B01-v2-static-closure-revision-2/'
SRC = 'docs/evidence/package-0090-full-reachable-expectation-closure-v2/'
NATIVE = 'scripts/validation/package_0090_native_health_qualification/'
V043 = 'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
VHASH = '007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a'
REPORT = 'docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-4.md'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def canon(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def save(name, x):
    (OUT / name).write_bytes(json.dumps(x, indent=2, ensure_ascii=False).encode() + b'\n')

def load(path):
    return json.loads(BLOBS[path].decode('utf-8-sig'))

def ref(path, pointer='/'):
    return dict(path=path, git_blob_oid=TREE[path], git_lf_sha256=sha(BLOBS[path]), pointer=pointer)

def contract(name, **kwargs):
    save(name + '-v4.json', dict(revision=4, scope='TEST_QUALIFICATION_ONLY',
         proof_level='DESIGNED_NOT_STATICALLY_CLOSED', implementation_authorized=False,
         runtime_authority=False, **kwargs))

def anchor(path, text):
    b=BLOBS[path].decode('utf-8-sig'); assert text in b, (path,text)
    return dict(**ref(path), line=b[:b.index(text)].count('\n')+1, symbol=text)

def main():
    global TREE, BLOBS
    assert git('branch','--show-current').decode().strip()==BRANCH
    assert git('merge-base', BASE, 'HEAD').decode().strip()==BASE
    TREE={}
    for row in git('ls-tree','-r','-z',BASE).split(b'\0'):
        if row:
            meta,p=row.split(b'\t',1);TREE[p.decode()]=meta.decode().split()[2]
    # Consume every frozen R3 input AND all authoritative R2/R3 files, not just reports.
    f=json.loads(git('show',BASE+':'+R3+'baseline-freeze.json'))
    inputs=set(f['input_git_sha256']) | {p for p in TREE if p.startswith((R2,R3))}
    inputs |= {'AGENTS.md','docs/evidence/PACKAGE-0090-B01-v2-expanded-capability-mediation.md',
               'docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-2.md',
               'docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-3.md'}
    ids=list(dict.fromkeys(TREE[p] for p in sorted(inputs)))
    raw=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(ids)+'\n').encode(),cwd=ROOT)
    byid={};pos=0
    for oid in ids:
        end=raw.index(b'\n',pos);h=raw[pos:end].decode().split();n=int(h[2]);pos=end+1
        assert h[:2]==[oid,'blob'];byid[oid]=raw[pos:pos+n];pos+=n+1
    BLOBS={p:byid[TREE[p]] for p in inputs}
    for p,h in f['input_git_sha256'].items(): assert sha(BLOBS[p])==h,p
    for p,b in BLOBS.items(): assert (ROOT/p).read_bytes().replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n'),p
    # Validate BOTH prior evidence manifests against source bytes, not their conclusions.
    for prefix in (R2,R3):
        m=load(prefix+'SHA256-MANIFEST.json')
        for p,h in m['files'].items():
            b=BLOBS[p] if p in BLOBS else git('show',BASE+':'+p)
            assert sha(b.replace(b'\r\n',b'\n'))==h or sha(b)==h,p
    v=BLOBS[V043];assert sha(v)==VHASH
    crc=zlib.crc32(''.join(v.decode('utf-8-sig').splitlines()).encode());crc=crc if crc<2**31 else crc-2**32
    assert crc==1279591798
    assert v.index(b"RAISE EXCEPTION USING ERRCODE = '55000'")<v.index(b'SET LOCAL search_path')
    refs={r:git('rev-parse',r).decode().strip() for r in ('refs/heads/main','refs/remotes/origin/main') if subprocess.run(['git','rev-parse','--verify',r],cwd=ROOT,capture_output=True).returncode==0}
    save('baseline-freeze.json',dict(branch=BRANCH,baseline_head=BASE,origin_head_after_fetch=BASE,
        baseline_preflight='fetch origin --prune; branch/local/origin equality; clean worktree/index verified before R4',
        worktree_clean_before_evidence=True,index_clean_before_evidence=True,
        input_git_sha256={p:sha(BLOBS[p]) for p in sorted(inputs)},protected_refs=refs,
        CURRENT_V043_GIT_LF_SHA256=VHASH,FLYWAY_SIGNED_CRC32=crc,V043_FENCE_PRESENT=True))
    save('source-integrity.json',dict(proof_level='STATICALLY_PROVEN_BYTES_ONLY',
        source_count=len(inputs),all_R2_R3_artifacts_consumed=True,prior_manifests_verified=True,
        CURRENT_V043_GIT_LF_SHA256=VHASH,FLYWAY_SIGNED_CRC32=crc,V043_FENCE_PRESENT=True,
        CANONICAL_V043_MUTATED=False,CANONICAL_V043_EXECUTED=False,SHARED_DB_CONTACTED=False,
        PRODUCTION_CONTACTED=False,Manifest_v6=ref(SRC+'expected-currentness-manifest-v6.json'),
        authority='baseline-freeze.json#/input_git_sha256', runtime_commands=[]))

    # First: exact design universe. Runtime identities are uninstantiated, never fabricated.
    common=['deployment_id','database_system_identifier','database_oid','database_name',
            'epoch_id','generation','policy_digest','manifest_digest','audit_tip','operation_id']
    actors=['TRANSITION_WORKER','MUTATION_CREDENTIAL_HOLDER','AUDIT_WRITER','OUTCOME_WRITER',
            'OUTCOME_OBSERVER','EXTINCTION_OBSERVER','REGISTRY_WRITER','REGISTRY_OBSERVER',
            'POLICY_CUSTODIAN','RESERVATION_WRITER','FINAL_CONSUMER','CONSUMER_OBSERVER']
    participants=['POSTMASTER','SUPERVISOR','RECEIVER','CENSUS_OBSERVER','APPROVAL_PRODUCER','APPROVAL_CONSUMER','ENFORCEMENT_WORKER']
    identities=[]
    for a in actors+participants:
        identities.append(dict(id='TEST/R4/'+a,category='TEST_QUALIFICATION',
            identity_components=common+['namespace_inode','uid','executable_sha256','pidfd_inode','process_start','enrollment_digest'],
            instantiation='FUTURE_PROVISIONING_ONLY',raw_authority=False))
    identities += [dict(id='CANONICAL/MANIFEST_V6',category='CANONICAL',source=ref(SRC+'expected-currentness-manifest-v6.json')),
        dict(id='TB/TEST_BOOTSTRAP_CUSTODIAN',category='TRUST_BOUNDARY',
             permitted='Create isolated TEST namespaces/files/identities before epoch; destroy whole isolated instance after drain',
             prohibited='No broker-callable root/postgres/superuser/CREATEROLE path; cannot issue semantic success receipts'),
        dict(id='EXTERNAL/R4/WITNESS',category='EXTERNAL_OBSERVER',
             permitted='Verify durable witness chains outside mutation namespace',
             prohibited='No mutation credential or access to mutation dispatcher')]
    contract('qualification-universe',identities=identities,identity_tuple=common,
        deployment='TEST/R4/isolated-linux-namespace; fresh host-provisioned incarnation',
        database='TEST/R4/disposable-pg18-cluster; fresh system_identifier+OID+name, never g3f4/shared reuse',
        admission='No operational enrollment until all exact hashes/handles and observer entitlements instantiated and verified',
        allowlists='Only endpoints and proposed modules in this R4; unexpected fd/process/socket/store => UNKNOWN and BLOCKED',
        completeness='NOT_PROVEN: dependency/descriptor closure and exact entitlement paths remain open',
        CANONICAL_OVERLAY=False,root_is_capability=False,implicit_actors=[])

    old=load(R3+'native-work-anchor-map-v3.json')['participant_candidate_anchor_references']
    candidates={x['PARTICIPANT_ID']:x['candidate_anchors'] for x in old}
    primitives=[anchor(NATIVE+'supervisor.c','SYS_clone3'),anchor(NATIVE+'protocol.h','SCM_PIDFD'),
        anchor(NATIVE+'protocol.h','anchor_equal'),anchor(NATIVE+'protocol.h','CLOCK_BOOTTIME')]
    native=[]
    work={
      'POSTMASTER':('postgres','Execute one bounded query in enrolled final backend and witness its completed result, not nonce signature'),
      'SUPERVISOR':('supervisor.c','Spawn exact generation, transfer retained anchors and witness receiver/observer enrollment plus child drain'),
      'RECEIVER':('receiver.c','Validate sender/anchor/context, insert exact registry row and independently witness that published row'),
      'CENSUS_OBSERVER':('observer.c','Compare complete registry census to retained backend anchors and publish exact discrepancy set'),
      'APPROVAL_PRODUCER':('proposed/approval_producer.c','Construct full-context challenge approval only from independent census+policy+manifest witnesses'),
      'APPROVAL_CONSUMER':('proposed/approval_consumer.c','Verify original signed full-context approval, compare current registry and publish one-use acceptance receipt'),
      'ENFORCEMENT_WORKER':('proposed/enforcement_worker.c','Consume one exact retained target anchor and fail-closed command; external observer confirms disposition')}
    for i,p in enumerate(participants):
        module,challenge=work[p]
        native.append(dict(participant=p,independent_process_required=True,threads_are_independence=False,
          exact_module_design=module,module_kind='PROPOSED_TEST_ONLY' if module.startswith('proposed/') else 'EXISTING_PRIMITIVE_REQUIRES_INTEGRATION',
          source_authority=candidates[p],reused_primitives=primitives,
          binary_identity=dict(expected_sha256=None,rule='Pinned artifact/dependency hashes from future reviewed build, not source hash substituted for binary'),
          parent='TB/TEST_BOOTSTRAP_CUSTODIAN' if p=='SUPERVISOR' else 'TEST/R4/SUPERVISOR',
          generation=common+['participant_slot','birth_anchor','prior_generation_tombstone'],
          enrollment='Fresh one-use full tuple challenge over inherited sealed context and SO_PEERPIDFD/SCM_PIDFD retained anchors; reject stale or missing peers',
          authenticated_channel='Dedicated inherited AF_UNIX SOCK_SEQPACKET; no pathname re-discovery or numeric PID re-acquisition',
          dependency_identity='Exact executable+ELF/interpreter/library/loader graph; missing build/dependency closure remains unresolved',
          registry_identity='TEST/R4/registry store row keyed by full tuple and participant_slot, monotonic revision',
          catalog_identity='Exact TEST database system_identifier/OID+source-pinned catalog projection digest; no S04 execution',
          completed_work_challenge=challenge,
          functional_work_evidence=['input_context_digest','challenge_id','prior_registry_revision','completed_result_digest','observed_registry_revision'],
          publication_witness='TEST/R4/REGISTRY_OBSERVER must independently reread exact row and compare current revision before acceptance',
          guard_binding='All seven current full-context receipts conjunctive; any missing/stale/unknown receipt denies',
          observer_binding='TEST/R4/EXTINCTION_OBSERVER plus EXTERNAL/R4/WITNESS, distinct process/credential from subject',
          restart='Invalidate generation; tombstone old enrollment; no replacement until pending UNKNOWN reconciled and old handles extinct',
          revocation='Disable enrollment and channel, drain all descendants, retain target anchors until independent extinction receipts',
          extinction='Observer confirms retained pidfd signalled + wait/reap witness + no live generation descendants/fds/registry eligibility; timeout is UNKNOWN',
          UNKNOWN='Persist pending tuple; deny guard/claim/reseal; no restart-as-success',
          unresolved=['Exact build/dependency/loader identity and confinement absent',
                      'Full-context completed-work/publication/guard integration not source-proven'],
          fully_designed=False,proof_level='PARTIAL_DESIGN_WITH_EXACT_EXISTING_ANCHORS'))
    contract('native-seven-participant-contract',participants=native,NATIVE_PARTICIPANTS_REQUIRED=7,
        NATIVE_PARTICIPANTS_FULLY_DESIGNED=0,UNRESOLVED_NATIVE_WORK_ANCHORS=7,GENERIC_PROCESS_SUBSTITUTIONS=0,
        minimum_new_modules=['approval_producer.c','approval_consumer.c','enforcement_worker.c'],
        gap='Three purpose-specific proposed TEST modules, never a generic worker; fixed message/authority ABI and dependency closure still require design proof')
    contract('native-independent-witness-topology',edges=[dict(subject=p,work_observer='TEST/R4/REGISTRY_OBSERVER',extinction_observer='TEST/R4/EXTINCTION_OBSERVER',external_witness='EXTERNAL/R4/WITNESS') for p in participants],
        no_colocated_witness=True,no_harness_substitution=True,source_primitives=primitives,
        independent_observer_entitlements='NOT_PROVEN; topology requirement is not a grant or proof of physical independence')
    contract('native-work-anchor-map',participants=[dict(participant=x['participant'],source=x['source_authority'],completed_work=x['completed_work_challenge'],publication=x['publication_witness'],unresolved=x['unresolved']) for x in native])
    contract('native-generation-contract',identity_components=common+['slot','birth_anchor','parent_anchor','registry_revision'],
        creation='Supervisor atomic clone3 CLONE_PIDFD, no numeric-PID fallback',invalidated_by=['death','replacement','channel_loss','context_change','unknown_work_result'],
        restart='New generation only after independently durable tombstone+extinction+reconciliation; never copy enrollment',source=primitives)
    contract('native-extinction-contract',subjects=participants,required_evidence=['retained_pidfd_exit','wait_reap','descendant_census','descriptor_census','registry_tombstone','channel_revocation'],
        observer='TEST/R4/EXTINCTION_OBSERVER',witness='EXTERNAL/R4/WITNESS',
        unknown='Missing observer, incomplete descendant/fd inventory, crash, timeout or unavailable kernel evidence keeps UNKNOWN; never reseal',
        source=primitives,complete_descendant_descriptor_proof=False)

    # Concrete design custody graph: no single writer owns mutation, audit and outcome.
    kinds=['SQL_SESSION','BACKEND_PID_START','TRANSACTION_XID','WORKER_PROCESS','DESCENDANT_PROCESS',
           'NATIVE_PIPE','FIFO','SOCKET','CAPABILITY_HANDLE','CREDENTIAL','DESCRIPTOR','STATE_RECORD',
           'RESERVATION_RECORD','AUDIT_RECORD','OUTCOME_RECORD','OBSERVER_HANDLE','REGISTRY_HANDLE',
           'GENERATION_HANDLE','ENROLLMENT_HANDLE','LOCAL_CAPABILITY_ENDPOINT']
    endpoints=[]
    for k in kinds:
        holder=('AUDIT_WRITER' if k=='AUDIT_RECORD' else 'OUTCOME_WRITER' if k=='OUTCOME_RECORD' else
                'RESERVATION_WRITER' if k=='RESERVATION_RECORD' else 'REGISTRY_WRITER' if k in ['REGISTRY_HANDLE','GENERATION_HANDLE','ENROLLMENT_HANDLE'] else
                'MUTATION_CREDENTIAL_HOLDER' if k=='CREDENTIAL' else 'FINAL_CONSUMER' if k in ['SQL_SESSION','BACKEND_PID_START','TRANSACTION_XID'] else 'TRANSITION_WORKER')
        endpoints.append(dict(id='TEST/R4/ENDPOINT/'+k,kind=k,creator='TB/TEST_BOOTSTRAP_CUSTODIAN',holder='TEST/R4/'+holder,
          consumer='TEST/R4/OUTCOME_OBSERVER' if k=='OUTCOME_RECORD' else 'EXTERNAL/R4/WITNESS' if k=='AUDIT_RECORD' else 'TEST/R4/TRANSITION_WORKER',
          allowed_operation='Single exact cataloged transition for this typed endpoint, no arbitrary selectors',
          forbidden_operation=['cross_epoch','cross_generation','cross_capability','arbitrary_SQL_path_shell','produce_own_success_witness'],
          lifecycle=['RESERVED','ENROLLED','ACTIVE','REVOKING','EXTINCTION_PENDING','EXTINCT','UNKNOWN'],
          durable_identity=common+['endpoint_type','endpoint_instance','creator_receipt','holder_enrollment'],
          revocation_authority='TEST/R4/TRANSITION_WORKER requests; TEST/R4/'+holder+' applies only this endpoint tombstone/revoke; TEST/R4/EXTINCTION_OBSERVER independently verifies, never trusts holder ACK',
          revocation_mechanism='Revoke exact handle/credential/registry eligibility; signal anchored process where applicable; retained durable tombstone',
          extinction_observer='TEST/R4/EXTINCTION_OBSERVER',
          extinction_evidence='Independent full-tuple endpoint-specific kernel/catalog/store receipt, witness countersignature',
          UNKNOWN='Retain reservation+tombstone and block both eligibility and reseal',
          reseal_dependency='All old generation instances extinct; no implicit absent-endpoint success',
          physical_instance=None,fully_bound=False))
    contract('endpoint-inventory',endpoints=endpoints,historical_V1=load(R3+'endpoint-inventory-v3.json'),
        candidate_endpoint_types=len(endpoints),ENDPOINTS_TOTAL=None,ENDPOINTS_FULLY_BOUND=0,UNBOUND_ENDPOINTS=None,
        inventory_exhaustive=False,gap='Type inventory is not descriptor/process/dependency instance closure; 21 historical endpoints are not adopted')
    contract('endpoint-custody',endpoints=endpoints,separate_actor_ids=actors,
        no_actor_may_hold_mutation_outcome_and_audit=True,unresolved='No exact platform privilege/delegation/credential entitlement proof for proposed custodians')
    contract('revocation-graph',edges=[dict(endpoint=e['id'],authority=e['revocation_authority'],observer=e['extinction_observer'],evidence=e['extinction_evidence']) for e in endpoints],complete=False)
    contract('extinction-proof-contract',endpoints=[e['id'] for e in endpoints],
        required=['credential_invalid','session_backend_terminated','all_descendants_reaped','all_mutation_fds_closed','native_registry_tombstoned','durable_observer_receipt'],
        no_timeout_implies_success=True,no_process_death_implies_rollback=True,observer='TEST/R4/EXTINCTION_OBSERVER',complete=False)
    stores={}
    for kind,writer in [('reservation','RESERVATION_WRITER'),('audit','AUDIT_WRITER'),('outcome','OUTCOME_WRITER'),('registry','REGISTRY_WRITER')]:
        stores[kind]=dict(design_path='/var/lib/flooow-b01-r4/'+kind+'/ledger',writer='TEST/R4/'+writer,
            reader='EXTERNAL/R4/WITNESS' if kind=='audit' else 'TEST/R4/OUTCOME_OBSERVER',
            identity=common+['store_inode','mount_namespace','writer_identity','previous_tip','record_digest'],
            write_rule='Exclusive writer; append length+canonical typed record+digest; fsync record and directory before receipt; conflicting duplicate key denies',
            transport='Dedicated credential-free full-tuple message; writer independently validates predecessor/reservation and required witness signatures',
            instantiated=False,filesystem_authority_and_crash_atomicity='NOT_PROVEN; path is a proposed design binding, never a live durable identity')
    contract('durable-outcome-contract',store=stores['outcome'],reservation=stores['reservation'],
        states=['PENDING','COMMITTED','ABORTED_PROVEN','UNKNOWN'],
        COMMITTED='Independent transaction identity + exact before/after/dependency delta witness; worker ACK alone insufficient',
        ABORTED_PROVEN='Independent no-effect and transaction resolution; absent row/timeout/dead process alone insufficient',
        UNKNOWN='Durable across reconnect/restart, prohibits second reservation and enrollment; independent reconciliation only',complete=False)
    contract('durable-audit-contract',store=stores['audit'],records=common+['capability_digest','target_digest','precondition_digest','outcome_digest','observer_receipt','previous_tip','revision'],
        authentication='External witness verifies chain and independent outcome proof; mutation worker cannot write/sign audit or outcome',complete=False)
    state=load(R3+'closed-epoch-state-machine-v3.json')
    contract('closed-epoch-state-machine',states=state['states'],transitions=state['transitions'],
        frozen_source=ref(R3+'closed-epoch-state-machine-v3.json'),
        unchanged_abstract_relation=True,physical_transition_authority='NOT_PROVEN',UNKNOWN_is_TRUE=False)
    inv=load(R3+'closed-epoch-physical-bindings-v3.json')['invariants']
    bindings=[]
    for x in inv:
        name=x['id'];observer='OUTCOME_OBSERVER' if name=='mutation_outcome_known' else 'EXTINCTION_OBSERVER' if name in ['old_capability_revoked','old_worker_extinct'] else 'REGISTRY_OBSERVER'
        bindings.append(dict(id=name,authoritative_source=ref(R3+'closed-epoch-physical-bindings-v3.json'),
            physical_target_design='TEST/R4/'+('outcome' if name=='mutation_outcome_known' else 'audit' if name=='audit_durable' else 'registry')+'/ledger',
            observer='TEST/R4/'+observer,durable_evidence=common+['invariant_id','observation_revision','receipt_digest'],
            UNKNOWN='Any missing/mismatched/stale/non-durable observation is UNKNOWN',
            fail_closed='No RESEAL_PENDING->SEALED_NEW_EPOCH until all seven independently TRUE',
            physical_binding_proven=False,gap='Exact observer entitlement, endpoint closure and durable write mechanism not statically closed'))
    contract('closed-epoch-physical-bindings',stores=stores,bindings=bindings,RESEAL_INVARIANTS_PHYSICALLY_BOUND=0)
    contract('closed-epoch-reseal-invariants',invariants=bindings,RESEAL_INVARIANTS_TOTAL=7,
        RESEAL_INVARIANTS_PHYSICALLY_BOUND=0,rule='Conjunction of seven independently KNOWN_TRUE receipts for same epoch/generation/manifest/policy; UNKNOWN != TRUE')
    cuts=['before_reservation','after_reservation_before_mutation','after_mutation_before_commit','commit_ack_lost','after_commit_before_outcome','after_outcome_before_audit','during_revocation','after_revocation_before_extinction','during_reseal','after_reseal_before_consumer_ACK']
    crashes=[dict(cut=c,state='MUTATION_UNKNOWN',durable_pending='Preserve reservation and last independently durable tuple',
                  continuation='No replay/new enrollment/reseal until independent outcome+audit+extinction reconciliation',
                  process_death_means_abort=False,reconnect_clears_pending=False) for c in cuts]
    contract('closed-epoch-crash-matrix',cases=crashes,all_14_states=state['states'],all_state_cut_pairs=len(cuts)*len(state['states']))
    contract('unknown-outcome-contract',cases=crashes,source=ref(R3+'unknown-outcome-contract-v3.json'),
        pending_key=common+['reservation_digest','capability_digest','target_digest','consumer_enrollment'],
        UNKNOWN_survives_restart=True,UNKNOWN_survives_reconnect=True,new_enrollment_allowed_while_UNKNOWN=False,
        reconciliation='Independent observer exact transaction outcome and expected delta, immutable outcome writer receipt, separate audit witness; no caller boolean',complete=False)
    consumer=load(R3+'consumer-session-contract-v3.json')
    contract('consumer-session-contract',source=ref(R3+'consumer-session-contract-v3.json'),
        authenticated_SQL_identity='test_0090_audit',helper_session_allowed=False,
        conjunctive_identity=common+['authenticated_handle','backend_pid','backend_start','session_identity','session_user','before_setting','after_setting','outcome','observer_receipt'],
        parameter_contracts=consumer['parameter_contracts'],
        exact_same_handle_rule=consumer['continuity_rule'],
        observer='TEST/R4/CONSUMER_OBSERVER independently witnesses messages and full backend tuple; it may not run a helper SET',
        reconnect='Old UNKNOWN persists; no new enrollment until independent reconciliation; new handle never inherits old eligibility',
        entitlement_gap='No independently source-proven mechanism for exact original-handle before/after observation and final decision transport',
        FINAL_CONSUMER_SESSION_CONTRACT_COMPLETE='NOT_PROVEN')

    # Only after universe/topology/custody: reproduce every R3 form, no representative collapse.
    spec=importlib.util.spec_from_file_location('r3_offline_derivation',ROOT/R3/'derive.py')
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    count=0;digest=hashlib.sha256();missing=[];groups=collections.Counter()
    target_design={'audit_binding':'TEST/R4/AUDIT_RECORD','native_anchor':'TEST/R4/ENROLLMENT_HANDLE',
        'native_binding':'TEST/R4/GENERATION_HANDLE','native_participant':'TEST/R4/native-seven-participant-contract',
        'policy_readiness_binding':'TEST/R4/STATE_RECORD','session_environment':'TEST/R4/SQL_SESSION'}
    for r in d.expand_mechanisms():
        count+=1;digest.update(d.canon(r)+b'\n')
        if r['PHYSICAL_TARGET'] is None:
            groups[r['TARGET_KIND']]+=1
            missing.append(dict(id=r['MECHANISM_ID'],source_authority=r['SOURCE_POINTER'],
                class_id=r['CLASS_ID'],operation_form=r['MUTATION_FORM'],
                proposed_target_type=target_design[r['TARGET_KIND']],physical_target=None,
                applicability='NOT_PROVEN',actor='NOT_BOUND',authority_path='NOT_PROVEN',
                dependency_effect=r['DEPENDENCIES'],before_state='Exact frozen source pointer; physical revision not instantiated',
                expected_after_state='Requires per-form data/provider/dependency applicability proof; never infer from mutation name',
                observer='NOT_BOUND',UNKNOWN_state='MUTATION_UNKNOWN',
                unresolved_count=1,proof_level='NOT_PROVEN',
                missing_proof='Type proposal does not establish exact field/store/process/observer entitlement or semantic dependency delta',
                individual_resolution='UNRESOLVED_NOT_COLLAPSED'))
    md=load(R3+'mechanism-denominator.json')
    assert count==md['enumerated_form_obligations']==445136
    assert digest.hexdigest()==md['expanded_records_sha256'] and len(missing)==422
    contract('class-mechanism-partitions',classes=load(R3+'class-mechanism-partitions-v3.json')['classes'],
        individual_missing_target_obligations=missing,group_counts=dict(groups),
        operation_expansion_source=ref(R3+'derive.py'),expanded_records_sha256=digest.hexdigest(),
        CLASSES_REQUIRED=46,CLASSES_FULLY_PARTITIONED=0,ALL_46_CLASSES_PARTITIONED=False,
        ALL_REACHABLE_MECHANISMS_PARTITIONED=False,no_representative_collapses=True)
    contract('mechanism-denominator',MECHANISMS_TOTAL=None,known_source_node_operation_forms=count,
        known_unresolved_physical_target_obligations=422,UNRESOLVED_PHYSICAL_TARGETS=422,
        complete_unresolved_count=None,complete_unclassified_count=None,
        lower_bound_only=True,representative_collapses_performed=0,
        denominator_complete=False,capability_derivation_allowed=False,
        why='422 individually indexed gaps remain; full AST/provider applicability, dependency and exact actor/observer closure not proved')
    contract('constraint-applicability',source=ref(R3+'constraint-applicability-v3.json'),
        records=load(R3+'constraint-applicability-v3.json')['records'],
        required_independent_forms=['NOT_NULL','CHECK','FK','PK','UNIQUE','BACKING_INDEX','RI_TRIGGERS','GENERATED_NAMES','DEPENDENCY_EFFECTS','VALIDATE','DATA_DEPENDENT'],
        semantic_status='Prior exact records retained as inspected candidates, NOT complete applicability proof',
        AST_completeness_claimed=False,provider_authority='Pinned PG18 source in baseline-freeze.json; no web/latest provider adopted')
    contract('acl-origin-ledger',source=ref(R3+'acl-origin-ledger-v3.json'),
        ledger=load(R3+'acl-origin-ledger-v3.json'),
        origin_dimensions=['DIRECT_GRANT','DIRECT_REVOKE','GRANT_OPTION','PUBLIC','OWNERSHIP','SET','INHERIT','ADMIN_OPTION','DEFAULT_PRIVILEGES','CREATOR_DERIVED','SECURITY_DEFINER','SCHEMA_PRIVILEGE','TRANSITIVE_ROLE_PATH'],
        origin_closure_proven=False,lexical_scan_is_AST=False)
    contract('dependency-effect-ledger',unresolved_records=[dict(id=r['id'],source=r['source_authority'],effect=r['dependency_effect'],closure=False) for r in missing],
        provider_sources=[ref(p) for p in sorted(inputs) if p.startswith(SRC+'provider/')],
        full_dependency_closure=False,AST_completeness=False)
    # Derivation order forbids inventing capabilities while denominator is open.
    for name,field in [('typed-capability-catalog','required_typed_capabilities'),('fixed-operation-templates','required_templates'),
        ('capability-principal-bindings','required_principals'),('capability-outcome-bindings','required_outcomes'),
        ('capability-observer-bindings','required_observers'),('executor-confinement','required_confined_executors')]:
        contract(name,**{field:None},derived_records=[],derivation_status='BLOCKED_BY_PHYSICAL_DENOMINATOR',
            empty_array_does_not_mean_zero_required=True,RAW_AUTHORITY_SURFACE='NOT_PROVEN',
            rejected=['arbitrary_SQL','arbitrary_identifier','arbitrary_path','arbitrary_shell','arbitrary_psql','generic_superuser_broker','generic_CREATEROLE_broker','generic_native_worker'],
            unresolved='Exact principal credential confinement/template/outcome/observer/revocation/UNKNOWN proof cannot be derived from an incomplete denominator')
    ag=load(R3+'authority-graph-v3.json')
    contract('authority-graph',source=ref(R3+'authority-graph-v3.json'),
        partial_route_candidates=ag['class_route_candidates'],
        allowed_categories=['BROKER_MEDIATED','EPOCH_REPLACEMENT_ONLY','IMMUTABLE_DURING_SEALED','TRUST_BOUNDARY_ONLY'],
        mutation_edges=[],AUTHORITY_EDGES_TOTAL=None,AUTHORITY_EDGES_CLASSIFIED=0,
        UNCLASSIFIED_MUTATION_EDGES=None,UNMEDIATED_ACTIVE_MUTATION_EDGES=None,
        AUTHORITY_GRAPH_COMPLETE=False,empty_array_is_not_zero_edges=True,
        direct_root_postgres_CREATEROLE_not_hidden=True)
    fix=load(R3+'fixture-correction-revalidation-v3.json')
    contract('fixture-correction-revalidation',MANIFEST_COMPATIBILITY_DECISION='C. B01_FIXTURE_MUST_CHANGE',
        canonical_v6_source=ref(SRC+'expected-currentness-manifest-v6.json'),
        exact_wrapper=fix['exact_wrapper'],auditor=fix['auditor'],
        obligations=['restore exact auditor wrapper EXECUTE','remove private Package-owner SET membership','zero incoming ADMIN owner memberships','zero outgoing ADMIN owner memberships','preserve raw history denial','no production carryover','no canonical waiver'],
        prior_source_evidence=fix,FIXTURE_CORRECTION_REVALIDATION='NOT_PROVEN_AGAINST_INCOMPLETE_V4_MODEL',
        fixture_implemented=False,overlay_created=False)
    findings=[]
    for b in load(R3+'findings.json')['blockers']:
        findings.append(dict(ID=b['ID'],severity='BLOCKER',source_authority=b['sources_inspected'],
            exact_missing_proof=b['exact_missing_proof'],derived_obligations=b['minimum_next_action'],
            physical_bindings='R4 proposed target/actor contracts; missing entitlement/dependency evidence stays explicit',
            unresolved_count=422 if b['ID']=='V2-PARTITIONS' else 7 if b['ID']=='V2-NATIVE' else None,
            proof_level='NOT_PROVEN',independent_reviewer_result='PENDING',
            R3_not_adopted_as_truth=True))
    save('findings.json',dict(BLOCKER_COUNT=4,HIGH_COUNT=0,MEDIUM_COUNT=0,LOW_COUNT=0,blockers=findings,
        source_integrity_tests_are_not_design_PASS=True))
    gate=dict(BRANCH=BRANCH,BASELINE_HEAD=BASE,CURRENT_V043_GIT_LF_SHA256=VHASH,FLYWAY_SIGNED_CRC32=crc,
        V043_FENCE_PRESENT=True,CANONICAL_V043_MUTATED=False,CANONICAL_V043_EXECUTED=False,SHARED_DB_CONTACTED=False,PRODUCTION_CONTACTED=False,
        QUALIFICATION_UNIVERSE_COMPLETE='NOT_PROVEN',CLASSES_REQUIRED=46,CLASSES_FULLY_PARTITIONED=0,
        MECHANISMS_TOTAL=None,UNRESOLVED_PHYSICAL_TARGETS=422,UNJUSTIFIED_REPRESENTATIVE_COLLAPSES=0,UNCLASSIFIED_MECHANISMS=None,
        NATIVE_PARTICIPANTS_REQUIRED=7,NATIVE_PARTICIPANTS_FULLY_DESIGNED=0,UNRESOLVED_NATIVE_WORK_ANCHORS=7,GENERIC_PROCESS_SUBSTITUTIONS=0,
        ENDPOINTS_TOTAL=None,ENDPOINTS_FULLY_BOUND=0,UNBOUND_ENDPOINTS=None,RESEAL_INVARIANTS_TOTAL=7,RESEAL_INVARIANTS_PHYSICALLY_BOUND=0,
        FINAL_CONSUMER_SESSION_CONTRACT_COMPLETE='NOT_PROVEN',REQUIRED_TYPED_CAPABILITIES=None,
        CAPABILITIES_WITH_FIXED_TEMPLATE=None,CAPABILITIES_WITH_EXACT_PRINCIPAL=None,CAPABILITIES_WITH_OUTCOME_BINDING=None,
        CAPABILITIES_WITH_OBSERVER_BINDING=None,CAPABILITIES_WITH_CONFINED_EXECUTOR=None,RAW_AUTHORITY_SURFACE='NOT_PROVEN',
        AUTHORITY_EDGES_TOTAL=None,AUTHORITY_EDGES_CLASSIFIED=0,UNCLASSIFIED_MUTATION_EDGES=None,UNMEDIATED_ACTIVE_MUTATION_EDGES=None,
        MANIFEST_COMPATIBILITY_DECISION='C. B01_FIXTURE_MUST_CHANGE',FIXTURE_CORRECTION_REVALIDATION='NOT_PROVEN',
        LEAST_PRIVILEGE_REVIEW='PENDING',STATIC_ADVERSARIAL_REVIEW='PENDING',BLOCKER_COUNT=4,HIGH_COUNT=0,MEDIUM_COUNT=0,LOW_COUNT=0,
        STATIC_GATE='BLOCKED',CURRENTNESS_MUTATION_CLASSES_PROVEN=0,CURRENTNESS_MUTATION_CLASSES_UNPROVEN=46,
        B02_CURRENTNESS_INTEGRATION_GATE='NOT_RERUN',COMPLETE_CURRENTNESS_GATE='FAIL_NOT_RERUN',NEXT_EXECUTED=False,
        NEXT_GATE='R4_DESIGN_COMPLETION_OF_FOUR_BLOCKERS_NO_LIVE_EXECUTION')
    save('STATIC-GATE.json',gate)
    print(json.dumps(dict(source_inputs=len(inputs),obligations=count,individual_unresolved=len(missing),STATIC_GATE='BLOCKED')))

if __name__=='__main__':main()
