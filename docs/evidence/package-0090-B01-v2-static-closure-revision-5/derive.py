"""R5 STATIC DESIGN data generator; no SQL, build, native or network execution.

Invoked only by verify_evidence.py --generate. New module/ABI/store descriptions
are contracts, never runnable fixture code. Unknown semantic closure stays open.
"""
import sys
sys.dont_write_bytecode=True
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import zlib

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
BRANCH='checkpoint/package-0090-cloud-handoff'
R4='docs/evidence/package-0090-B01-v2-static-closure-revision-4/'
R3='docs/evidence/package-0090-B01-v2-static-closure-revision-3/'
SRC='docs/evidence/package-0090-full-reachable-expectation-closure-v2/'
N='scripts/validation/package_0090_native_health_qualification/'
V043='applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration/V043__create_governed_offline_field_proof_capability_composition.sql'
VHASH='007ab786c417c41e2b1702ebf3852cb70ff5c142fa3fde195385e04c6dde8b4a'
PARTICIPANTS=['POSTMASTER','SUPERVISOR','RECEIVER','CENSUS_OBSERVER','APPROVAL_PRODUCER','APPROVAL_CONSUMER','ENFORCEMENT_WORKER']
ACTORS=PARTICIPANTS+['REGISTRY_WRITER','REGISTRY_OBSERVER','RESERVATION_WRITER','STATE_WRITER','OUTCOME_WRITER','OUTCOME_OBSERVER','AUDIT_WRITER','AUDIT_OBSERVER','GENERATION_WRITER','EXTINCTION_OBSERVER','EXTINCTION_WRITER','FINAL_CONSUMER','CONSUMER_OBSERVER','POLICY_CUSTODIAN','TRANSITION_WORKER','CATALOG_OBSERVER']

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def save(n,x):(OUT/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def load(p):return json.loads(BLOBS[p].decode('utf-8-sig'))
def ref(p,ptr='/'):return dict(path=p,git_blob_oid=TREE[p],git_lf_sha256=sha(BLOBS[p]),pointer=ptr)
def doc(n,**kw):save(n+'-v5.json',dict(revision=5,scope='TEST_ONLY_STATIC_DESIGN',implementation_authorized=False,physical_instantiation_performed=False,runtime_proven=False,**kw))
def actor(a):return 'TEST/R5/'+a
def fld(n,t,nullable=False):return dict(name=n,type=t,nullable=nullable)

# Exact context encoding shared by every native message and store record.
CONTEXT=[fld('qualification_id','uuid'),fld('deployment_id','uuid'),fld('database_system_identifier','u64'),
 fld('database_oid','u32'),fld('database_name','utf8_nfc'),fld('epoch','uuid'),fld('generation','u64'),
 fld('policy_digest','bytes32'),fld('manifest_digest','bytes32'),fld('enrollment_digest','bytes32'),
 fld('actor_id','u16'),fld('process_identity_digest','bytes32'),fld('parent_identity_digest','bytes32'),
 fld('backend_pid','u32',True),fld('backend_start_epoch_us','i64',True),fld('operation_id','uuid'),
 fld('challenge_id','bytes32'),fld('sequence','u64'),fld('registry_revision','u64'),fld('original_emitted_boottime_us','u64')]
ENCODING=dict(
 frame='ASCII FLOOOWR5 (8 bytes) || version u16be=1 || message_type u16be || sender u16be || recipient u16be || payload_size u32be || payload || signature64',
 payload='u16be field count; fields in declared order, tag u16be (1-based), length u32be, payload; null payload=00; present=01||typed value',
 integers='fixed-width big-endian; unsigned u16/u32/u64; i64 two-complement; checked range, overflow rejects',
 uuid='16 network-order bytes, non-nil',bytes32='exact 32 raw bytes',bytes64='exact 64 raw bytes',
 bool='one byte 00 or 01',utf8_nfc='strict UTF8 already NFC; no normalization; reject NUL/control, empty identity or >4096 bytes',
 array='u32be count, then u32be byte length + canonical typed element; ordered input preserves order; set sorted unsigned bytes and duplicates reject',
 bounds='frame <=1048576 bytes; array count<=4096; lengths checked before allocating; policy-specific smaller limits also mandatory',
 invalid='Unknown/reordered/duplicate/missing tags, unexpected NULL, noncanonical bytes, truncated/trailing bytes, unknown versions/types reject before effect',
 signature='Ed25519 over complete frame excluding signature64; statically assigned sender public key from enrolled credential manifest; no algorithm/key selector',
 domain='FLOOOW/B01/R5/TEST; signatures also bind message type, sender, recipient and qualification tuple; never canonical attestation authority')

def freeze():
    global TREE,BLOBS
    assert git('branch','--show-current').decode().strip()==BRANCH
    assert git('rev-parse','HEAD').decode().strip()==BASE
    assert git('rev-parse','origin/'+BRANCH).decode().strip()==BASE
    TREE={}
    for row in git('ls-tree','-r','-z',BASE).split(b'\0'):
        if row:
            m,p=row.split(b'\t',1);TREE[p.decode()]=m.decode().split()[2]
    previous=json.loads(git('show',BASE+':'+R4+'baseline-freeze.json'))
    inputs=set(previous['input_git_sha256']) | {p for p in TREE if p.startswith(R4)}
    inputs |= {p for p in TREE if p.startswith(('docs/adr/','docs/specifications/','scripts/validation/package_0090'))}
    inputs |= {'AGENTS.md','docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-4.md',
        'docs/evidence/package-0090-g3f4-executable-handoff-native-health/HEALTH-CONTRACT.md',
        'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/NATIVE-HEALTH-CONTRACT.md'}
    ids=list(dict.fromkeys(TREE[p] for p in sorted(inputs)))
    buf=subprocess.check_output(['git','cat-file','--batch'],input=('\n'.join(ids)+'\n').encode(),cwd=ROOT)
    blobs={};pos=0
    for oid in ids:
        e=buf.index(b'\n',pos);h=buf[pos:e].decode().split();size=int(h[2]);pos=e+1
        assert h[:2]==[oid,'blob'];blobs[oid]=buf[pos:pos+size];pos+=size+1
    BLOBS={p:blobs[TREE[p]] for p in inputs}
    for p,h in previous['input_git_sha256'].items():assert sha(BLOBS[p])==h,p
    for p,b in BLOBS.items():assert (ROOT/p).read_bytes().replace(b'\r\n',b'\n')==b.replace(b'\r\n',b'\n'),p
    m=load(R4+'SHA256-MANIFEST.json')
    for p,h in m['files'].items():
        b=BLOBS[p];b=b.replace(b'\r\n',b'\n') if p.endswith('.md') else b
        assert sha(b)==h,p
    v=BLOBS[V043];crc=zlib.crc32(''.join(v.decode('utf-8-sig').splitlines()).encode());crc=crc if crc<2**31 else crc-2**32
    assert sha(v)==VHASH and crc==1279591798
    assert v.index(b"RAISE EXCEPTION USING ERRCODE = '55000'")<v.index(b'SET LOCAL search_path')
    save('baseline-freeze.json',dict(R5_PREFLIGHT='PASS',branch=BRANCH,baseline_head=BASE,remote_tracking_head=BASE,
      remote_identity_authority='existing refs/remotes/origin; no network refresh requested/performed in offline tranche',
      tracked_dirty_before=0,staged_before=0,untracked_before=0,R4_manifest_verified=True,R4_manifest_files=len(m['files']),
      input_git_sha256={p:sha(BLOBS[p]) for p in sorted(inputs)},input_blob_oid={p:TREE[p] for p in sorted(inputs)},
      protected_refs=previous['protected_refs'],CURRENT_V043_GIT_LF_SHA256=VHASH,FLYWAY_SIGNED_CRC32=crc,V043_FENCE_PRESENT=True,
      no_execution_evidence_basis='Frozen R4 gate and source-integrity negative records; no runtime command invoked in R5. Not a forensic claim about unobserved external activity.'))
    save('source-integrity.json',dict(source_count=len(inputs),all_R4_inputs_reverified=True,complete_R4_evidence_consumed=True,
      Package_ADR_SPEC_scope='All tracked docs/adr and docs/specifications plus all previous source inputs and all scripts/validation/package_0090* sources',
      authority='baseline-freeze.json#/input_git_sha256',V043_GIT_LF_SHA256=VHASH,FLYWAY_SIGNED_CRC32=crc,V043_FENCE_PRESENT=True,
      CANONICAL_V043_MUTATED=False,CANONICAL_V043_EXECUTED=False,SHARED_DB_CONTACTED=False,PRODUCTION_CONTACTED=False,runtime_commands=[],network_calls=[]))

def native():
    # Native design first; future physical values have exact recipes, never invented hashes.
    old={r['participant']:r['source'] for r in load(R4+'native-work-anchor-map-v4.json')['participants']}
    native_source_refs=[ref(p) for p in sorted(BLOBS) if p.startswith(N) and p.endswith(('.c','.h'))]
    works={
     'POSTMASTER':dict(code=1,request=[fld('request_digest','bytes32'),fld('catalog_revision','u64')],
       response=[fld('backend_query_receipt','bytes32'),fld('catalog_snapshot_digest','bytes32'),fld('completed_queries','u64')],
       action='Complete one fixed read-only context/catalog witness query in the enrolled TEST backend; compare exact server PID/start/database/role tuple with independent catalog observer; count only after response and independent comparison',
       module='postgres18 + TEST-only login.c integration',observer='CATALOG_OBSERVER'),
     'SUPERVISOR':dict(code=2,request=[fld('spawn_plan_digest','bytes32'),fld('expected_child_slots','u16_array')],
       response=[fld('child_anchor_set_digest','bytes32'),fld('enrollment_receipt_set_digest','bytes32'),fld('completed_spawns','u64')],
       action='Spawn the fixed seven-slot topology via clone3 CLONE_PIDFD; independently observed exact child binary/parent/generation and successful enrolled receiver/observer challenge; heartbeat loop is not completed work',
       module='TEST-only adapted supervisor.c',observer='REGISTRY_OBSERVER'),
     'RECEIVER':dict(code=3,request=[fld('candidate_enrollment_digest','bytes32'),fld('expected_registry_revision','u64')],
       response=[fld('validated_context_digest','bytes32'),fld('registry_commit_receipt','bytes32'),fld('completed_enrollments','u64')],
       action='Validate full request, retained sender/parent/channel anchors, server-derived catalog identity and all current dependency receipts; propose exact enrollment CAS; count only independently observed committed registry revision',
       module='TEST-only adapted receiver.c',observer='REGISTRY_OBSERVER'),
     'CENSUS_OBSERVER':dict(code=4,request=[fld('anchor_set_digest','bytes32'),fld('snapshot_registry_revision','u64')],
       response=[fld('census_set_digest','bytes32'),fld('discrepancy_set_digest','bytes32'),fld('completed_censuses','u64')],
       action='Capture retained anchors/phase/enrollment/global revision, perform complete fixed catalog census, compare sets and revalidate unchanged snapshot via CAS; advancing tick before completed census is forbidden',
       module='TEST-only adapted observer.c with enforcement removed',observer='REGISTRY_OBSERVER'),
     'APPROVAL_PRODUCER':dict(code=5,request=[fld('census_receipt','bytes32'),fld('policy_receipt','bytes32'),fld('expected_registry_revision','u64')],
       response=[fld('approval_body_digest','bytes32'),fld('approval_signature','bytes64'),fld('completed_approvals','u64')],
       action='Independently verify current census, policy and all full-context seven-slot dependency receipts, sign immutable TEST approval whose body is exactly request context plus witness digests; no production signing key or generic signing API',
       module='NEW TEST ONLY approval_producer.c (DESIGN, NOT CREATED)',observer='REGISTRY_OBSERVER'),
     'APPROVAL_CONSUMER':dict(code=6,request=[fld('approval_body_digest','bytes32'),fld('approval_signature','bytes64'),fld('expected_registry_revision','u64')],
       response=[fld('one_use_publication_receipt','bytes32'),fld('new_registry_revision','u64'),fld('completed_consumptions','u64')],
       action='Verify original producer signature and expected producer enrollment, recompute full body from independent current witnesses, CAS UNUSED to CONSUMED and publish acceptance exactly once; recheck live registry before returning',
       module='NEW TEST ONLY approval_consumer.c (DESIGN, NOT CREATED)',observer='REGISTRY_OBSERVER'),
     'ENFORCEMENT_WORKER':dict(code=7,request=[fld('retained_target_identity_digest','bytes32'),fld('revocation_receipt','bytes32'),fld('disposition','u16')],
       response=[fld('attempt_receipt','bytes32'),fld('syscall_result','i64'),fld('completed_attempts','u64')],
       action='For one inherited exact target pidfd and frozen disposition STOP_THEN_TERM_THEN_CONT, attempt that finite sequence; never claims outcome or extinction. Distinct extinction observer checks kernel/catalog/descendant/descriptor evidence and independent outcome writer persists result',
       module='NEW TEST ONLY enforcement_worker.c (DESIGN, NOT CREATED)',observer='EXTINCTION_OBSERVER')}
    frames=[]
    for p,w in works.items():
        for direction in ('challenge','response'):
            extras=w['request'] if direction=='challenge' else w['response']
            frames.append(dict(id='R5/'+p+'/'+direction,message_type=100+w['code'] if direction=='challenge' else 200+w['code'],
              sender=actor('REGISTRY_OBSERVER') if direction=='challenge' else actor(p),
              recipient=actor(p) if direction=='challenge' else actor(w['observer']),
              fields=CONTEXT+extras,nullable_fields=['backend_pid','backend_start_epoch_us'],
              allowed_ancillary='Exactly one kernel SCM_PIDFD matching pre-enrolled sender; no SCM_RIGHTS after bootstrap; any extra ancillary/MSG_TRUNC/MSG_CTRUNC rejects and closes received extraneous descriptors',
              replay='Strictly greater sequence, unused challenge, same current epoch/generation/registry revision; identical terminal duplicate returns retained receipt only, no new work',
              credential=actor(p)+'/SIGNING_KEY' if direction=='response' else actor('REGISTRY_OBSERVER')+'/SIGNING_KEY'))
    doc('native-message-abi',encoding=ENCODING,actor_enum={a:i+1 for i,a in enumerate(ACTORS)},frames=frames,
       no_caller_selected_operation_or_target=True,
       nullable_pair_rule='backend PID/start either both present for backend-bound proof or both absent for native-only proof; absence never matches a backend',
       policy_freshness='Immutable approved TEST policy contains positive finite max age and work deadline per slot; original BOOTTIME emission age and sequence checked before accept and before publish; no hard-coded time threshold from experimental heartbeat.h',
       signature_not_work_proof=True,complete_work_requires_independent_observation=True)
    process_fields=[fld('qualified_deployment_digest','bytes32'),fld('pid_namespace_inode','u64'),fld('user_namespace_inode','u64'),fld('mount_namespace_inode','u64'),
        fld('retained_pidfd_dev','u64'),fld('retained_pidfd_inode','u64'),fld('kernel_start_ticks','u64'),fld('parent_identity_digest','bytes32'),
        fld('executable_manifest_digest','bytes32'),fld('enrollment_digest','bytes32'),fld('generation','u64')]
    loader=dict(binary_identity='Future approved build-manifest SHA256 of exact executable bytes, ELF class/machine/PT_INTERP/build-id and source/dependency/build recipe digests; source digest NEVER substituted for executable digest',
        actual_binary_sha256=None,DESIGN_BINDING_COMPLETE=True,PHYSICAL_INSTANTIATION_REQUIRED_LATER=True,
        dependencies='Parse PT_INTERP/DT_NEEDED/RPATH/RUNPATH and every transitive loader resolution offline at future build; exact finite resolved path+inode+bytes digest list, reject unresolved/duplicate/conflicting nodes; bind approved PG18/OpenSSL/libpq identities from frozen provider snapshots',
        loaders='Only manifest-enumerated absolute interpreter+ELF loader images on immutable private TEST mount; no ambient PATH/LD_PRELOAD/LD_LIBRARY_PATH/user site/plugin fallback',
        startup='Bootstrap opens/hashes all files without symlink fallback; retains exact handles on read-only mount; load only manifest set; seal writable context, close unknown fds, drop privileges, install no_new_privs and syscall policy before enrollment',
        post_enrollment='No execve/execveat/dlopen/ptrace/process_vm_writev/open writable executable/mprotect executable; unenumerated executable mappings revoke generation and quarantine',
        source_primitives=native_source_refs,guard='CATALOG_OBSERVER and REGISTRY_OBSERVER compare independently retained expected source/build/module/provider identities; missing build instance denies activation, not a missing design value')
    doc('native-loader-dependency-contract',process_identity_schema=process_fields,encoding=ENCODING,contract=loader,
        design_vs_physical='Recipe and required checks are design; actual binaries/load maps are future build/runtime evidence, not proof available in R5')
    matrix_names=['canonical_participant_ID','existing_source_anchors','executable_module_model','build_identity','loader_identity','dependency_closure','parent_identity','process_independence','credential_custody','generation_identity','generation_CAS','generation_tombstone','enrollment_identity','authenticated_channel','challenge_ABI','response_ABI','full_context','completed_work','one_use_publication','registry_writer','registry_observer','registry_CAS','guard_enforcer','outcome_witness','restart','reconnect','revocation_trigger','revocation_witness','extinction_witness','UNKNOWN','replay_rejection','substitution_rejection','stale_generation_rejection','binary_module_rejection','parent_rejection','credential_rejection','channel_rejection']
    rows=[]
    for p,w in works.items():
        bindings=[actor(p),old[p],w['module'],loader['binary_identity'],loader['loaders'],loader['dependencies'],
          'TEST/R5/BOOTSTRAP_CUSTODIAN' if p=='SUPERVISOR' else actor('SUPERVISOR'),
          'Distinct process, retained birth pidfd, distinct process-identity digest; no harness thread substitution',
          dict(id=actor(p)+'/SIGNING_KEY',custodian=actor(p),creation='Bootstrap injects fresh Ed25519 private seed through inherited sealed memfd fd4, read only by exact slot; no provider or canonical key; no cross-slot transfer; prevent dump/ptrace; close after in-process key import',
             public_key='Exact actor+generation key digest enrolled before any message acceptance; no caller key selector'),
          ['qualification_id','epoch','slot', 'generation','birth_pidfd_identity','executable_manifest_digest','parent_identity_digest'],
          'GENERATION_WRITER CAS compares exact prior global revision, current slot generation and prior tombstone; candidate generation=prior+1, checked u64; only after old UNKNOWN reconciled and full extinction receipt; simultaneous candidates conflict',
          'Append irreversible tombstone for old full identity; no reuse or rollback, even crash/restart; registry eligibility and all key/channel handles retired',
          'SHA256(ENCODING full context + process identity + loader manifest + key digest + role-specific protocol type); provisional is never eligible',
          dict(fd=5,kind='AF_UNIX SOCK_SEQPACKET inherited connected pair',
             channel_identity='Bootstrap signs pair cookie+socket inode pair+creator birth-anchor+exact fd inventory and intended sender/recipient enrollments; both endpoints verify sealed bootstrap receipt before activation',
             bootstrap_peer='SO_PEERPIDFD/SO_PEERCRED on inherited socket identifies creation-time peer, validated against BOOTSTRAP creator anchor, not assumed to be current role sender',
             current_sender='Enable SO_PASSPIDFD; every recvmsg must contain exactly one kernel SCM_PIDFD matching CURRENT enrolled sender birth-anchor and signed sender enum; reject any extra SCM_RIGHTS, credentials mismatch, stale descriptor or missing anchor',
             independence='Current sender and recipient process identities differ; immutable bootstrap creator identity never substitutes for either current process; no socket pathname/UID/PID equivalence'),
          'native-message-abi-v5.json#/frames/'+str((w['code']-1)*2),
          'native-message-abi-v5.json#/frames/'+str((w['code']-1)*2+1),
          [f['name'] for f in CONTEXT],w['action'],
          'Registry writer consumes exact operation/challenge at expected revision; duplicate identical receipt is read-only replay; conflicting duplicate denies; no new completed-work counter',
          actor('REGISTRY_WRITER'),actor('REGISTRY_OBSERVER'),
          'Read current global revision and exact enrollment/work digest; CAS old revision to old+1 on writer; observer independently rereads committed row; dependency drift invalidates original challenge, never recompute into acceptance',
          actor('APPROVAL_CONSUMER')+' denies unless all seven current independently witnessed completed-work receipts and policy/manifest/registry revisions match; '+actor('ENFORCEMENT_WORKER')+' acts on revoked target only',
          actor(w['observer'])+' -> '+actor('OUTCOME_WRITER')+'; subject signature or ACK alone is not outcome',
          'New generation only after old tombstone + all old endpoints extinct + pending UNKNOWN independently reconciled; never copy old private key or context',
          'Lost channel invalidates enrollment; no replacement channel enrollment while pending UNKNOWN; new channel identity cannot resurrect old receipts',
          ['identity_mismatch','dependency_drift','stale_work','invalid_signature','channel_loss','registry_CAS_conflict','quarantine','process_exit'],
          actor('REGISTRY_OBSERVER')+' independently checks exact revocation/tombstone revision; holder ACK is insufficient',
          actor('EXTINCTION_OBSERVER')+' checks retained kernel anchors, reaped descendants, complete descriptor closure, catalog absence and retired registry rows; outcome persisted separately',
          'Durable UNKNOWN survives process death/reconnect/restart; no new approval/work eligibility/reseal until independent reconciliation',
          'Reject used challenge, non-increasing sequence, prior epoch/generation, stale original emission or consumed publication',
          'Reject wrong actor/type/peer/process identity; no interchangeable participant',
          'Exact current generation and global revision required at challenge, work completion, CAS and final publication',
          'Compare approved build manifest and independently witnessed actual loader/module map; any mismatch quarantines',
          'Retained parent pidfd identity + start + namespace + manifest digest, not parent PID/name',
          'Exact enrolled actor/generation SPKI digest; no inherited/private shared-role signer; wrong key uniformly rejects',
          'Inherited peer anchor + exact descriptor role + signed sender/recipient; stale SCM_RIGHTS and alternate socket/channel reject']
        assert len(bindings)==len(matrix_names)==37
        matrix=[dict(REQUIREMENT=req,SOURCE_EVIDENCE=old[p],DESIGN_BINDING=b,INDEPENDENT_OBSERVER=actor(w['observer']),
          FAIL_CLOSED_BEHAVIOR='Deny/quarantine; retain durable UNKNOWN; never promote missing receipt into success',
          STATIC_STATUS='DESIGNED_PENDING_INDEPENDENT_REVIEW') for req,b in zip(matrix_names,bindings)]
        rows.append(dict(participant=p,participant_enum=w['code'],module=w['module'],closure_matrix=matrix,
            design_field_count=37,DESIGN_BINDING_COMPLETE='PENDING_REVIEW',
            PHYSICAL_INSTANTIATION_REQUIRED_LATER=True,actual_binary_hash=None,actual_process_handle=None,
            source_is_not_binary_identity=True,proof_level='PROPOSED_DETERMINISTIC_DESIGN_NOT_YET_ACCEPTED'))
    doc('native-seven-participant-contract',participants=rows,NATIVE_PARTICIPANTS_REQUIRED=7,
        NATIVE_PARTICIPANTS_FULLY_DESIGNED=0,UNRESOLVED_NATIVE_WORK_ANCHORS=7,GENERIC_PROCESS_SUBSTITUTIONS=0,
        counting='37 populated rows is structural completeness only; independent review must judge missing static integration and authority, not absence of future binary hashes')
    doc('native-work-anchor-map',participants=[dict(participant=p,existing_anchors=old[p],proposed_work=w['action'],expected_observer=actor(w['observer']),challenge_type=100+w['code'],response_type=200+w['code']) for p,w in works.items()],
        healthy='Completed exact work + independently current published registry witness, never nonce/heartbeat alone')
    doc('native-generation-contract',encoding=ENCODING,process_identity_fields=process_fields,
        initial='Bootstrap fresh qualification/epoch; generation1 only with proven empty prior registry for that NEW qualification, never inferred absence on unknown restored store',
        replacement='Checked generation+1 with exact prior-revision CAS and independently durable irreversible tombstone; all old endpoints extinct, pending outcomes known before new enrollment',
        actor=actor('GENERATION_WRITER'),observer=actor('REGISTRY_OBSERVER'),UNKNOWN='No next generation or key/channel reuse while any generation outcome is UNKNOWN',
        same_PID_not_same_process=True)
    doc('native-registry-protocol',writer=actor('REGISTRY_WRITER'),observer=actor('REGISTRY_OBSERVER'),encoding=ENCODING,
        phases=['PROVISIONAL','ENROLLED','WORK_PENDING','WORK_OBSERVED','PUBLISHED','REVOKED','EXTINCT','UNKNOWN'],
        key=['qualification_id','epoch','participant_slot','generation'],CAS=['global_revision','slot_revision','enrollment_digest','old_phase','prior_tip'],
        publication='WORK_OBSERVED->PUBLISHED only with independent work/outcome witness and unchanged complete dependency vector; atomically consumes challenge/approval ID; no publish from PROVISIONAL/UNKNOWN/REVOKED',
        withdrawal='Any identity/dependency/revision drift appends revocation/tombstone, monotonic quarantine; no status repair',
        credential='Private per-writer Ed25519 identity; stores do not accept subject-supplied outcome boolean as observation',
        replay='Same key+identical canonical digest returns original receipt; same key+different digest conflicts; terminal receipt replay never executes work',
        operation_vs_entity='operation_id is request idempotency identity only. Logical registry entity=(qualification_id,epoch,participant_slot,participant_generation); rederive exact entity_key_digest and prior entity revision from verified append chain. A different operation_id cannot reset phase or publication_consumed; entity CAS and legal phase edge still required',
        durable_protocol='durable-ledger-protocol-v5.json')
    doc('native-independent-witness-topology',participants=[dict(subject=actor(p),work_observer=actor(w['observer']),outcome_writer=actor('OUTCOME_WRITER'),audit_writer=actor('AUDIT_WRITER'),extinction_observer=actor('EXTINCTION_OBSERVER')) for p,w in works.items()],
        actor_separation='Subject/worker, writer, work witness and audit witness have distinct UID/key/process/descriptor sets; no shared writable state',
        source_graph_is_input_not_complete_proof=True,co_location_forbidden=True,
        host_administrator='TEST/R5/BOOTSTRAP_CUSTODIAN is trusted pre-enrollment/non-operational; never callable as a participant capability')
    doc('native-extinction-contract',source=ref('docs/evidence/package-0090-g3f4-executable-handoff-native-health/HEALTH-CONTRACT.md'),
        observer=actor('EXTINCTION_OBSERVER'),writer=actor('EXTINCTION_WRITER'),
        required_conjunction=['generation_tombstone_durable','all_pidfd_targets_signalled_and_wait_witnessed','all_descendants_reaped','all_accepted_descriptor_transfers_retired','all_native_channels_closed','all_SQL_backend_PID_start_identities_absent','all_registry_rows_ineligible','independent_extinction_receipt_durable'],
        UNKNOWN='Incomplete census, missing descriptor custody, timeout, process exit without descendant proof, unavailable catalog or observer => UNKNOWN; never infer extinct',
        retained_handles='Keep birth anchors and transfer receipts until terminal extinction evidence is durably witnessed; numeric PID re-acquisition is forbidden')
    # Confinement is a proposed implementation contract, not existing fixture authority.
    doc('native-confinement-contract',fixed_fd_roles={'3':'read-only approved loader/context manifest','4':'slot-private signing-key sealed memfd','5':'authenticated slot channel','6':'one retained enforcement target pidfd (enforcer only)'},
        bootstrap='Exact approved executable on immutable TEST mount, no_new_privs, non-dumpable, unique UID per actor, distinct key custody; close all nonmanifest inherited fds before enrollment',
        enforcement='One-shot worker accepts only message type107 and fixed STOP_THEN_TERM_THEN_CONT disposition1 for inherited fd6 target identity; no caller PID/path/fd/SQL selector; outputs attempt not success',
        kernel_filter='After bootstrap reject execve/execveat, ptrace, process_vm_writev, kill/tkill/tgkill, pidfd_open/pidfd_getfd, dup/dup2/dup3, fd replacement and executable writable mappings. Enforcer pidfd_send_signal only fd6 and exact permitted three signals; fd6 cannot be closed/replaced until exit. Unexpected syscall kills worker and outcome stays UNKNOWN',
        receiving='Post-enrollment recvmsg only fd5; reject any SCM_RIGHTS and unexpected ancillary, never install it as a target; kernel SCM_PIDFD must match enrolled sender, close temporary validation handles',
        capability_boundary='If platform permissions require CAP_KILL, confine to disposable TEST user/PID namespace and above immutable syscall filter; no ambient/root/superuser broker API. Exact filter instruction/syscall closure is a remaining design validation obligation, not proved by this prose',
        design_gap='No frozen source implements or statically verifies the proposed per-role filter/dependency startup boundary; exact full role-specific syscall/filter generation and credential entitlement remain NOT_PROVEN',
        runtime_qualification_required_later=True)

def epoch():
    # Derived after native proposals. Complete ABI for seven separate durable stores.
    store_fields={
      'reservation':[fld('capability_digest','bytes32'),fld('target_digest','bytes32'),fld('precondition_digest','bytes32'),fld('consumer_enrollment','bytes32'),fld('lease_revision','u64'),fld('state','u16')],
      'transition':[fld('from_state','u16'),fld('to_state','u16'),fld('reservation_digest','bytes32'),fld('required_witness_set_digest','bytes32'),fld('state_revision','u64')],
      'outcome':[fld('reservation_digest','bytes32'),fld('target_digest','bytes32'),fld('before_digest','bytes32'),fld('after_digest','bytes32'),fld('transaction_full_id','utf8_nfc',True),fld('resolution','u16'),fld('independent_observer_receipt','bytes32')],
      'audit':[fld('decision_id','uuid'),fld('change_id','uuid'),fld('approval_id','uuid'),fld('actor_enrollment','bytes32'),fld('source_context','bytes32'),fld('activation_recipe_digest','bytes32'),fld('effective_from_epoch_us','i64'),fld('outcome_receipt','bytes32'),fld('future_currentness_link','bytes32',True)],
      'participant_registry':[fld('participant_slot','u16'),fld('participant_generation','u64'),fld('process_identity','bytes32'),fld('parent_identity','bytes32'),fld('binary_manifest_digest','bytes32'),fld('channel_identity','bytes32'),fld('credential_public_digest','bytes32'),fld('phase','u16'),fld('work_receipt','bytes32',True),fld('publication_consumed','bool')],
      'generation_tombstone':[fld('participant_slot','u16'),fld('retired_generation','u64'),fld('new_generation','u64'),fld('prior_enrollment','bytes32'),fld('extinction_receipt','bytes32'),fld('pending_UNKNOWN','bool')],
      'extinction':[fld('retired_enrollment','bytes32'),fld('target_anchor_set','bytes32'),fld('descriptor_transfer_set','bytes32'),fld('descendant_set','bytes32'),fld('kernel_witness','bytes32'),fld('catalog_witness','bytes32'),fld('registry_tombstone','bytes32'),fld('status','u16')]}
    writers={'reservation':'RESERVATION_WRITER','transition':'STATE_WRITER','outcome':'OUTCOME_WRITER','audit':'AUDIT_WRITER','participant_registry':'REGISTRY_WRITER','generation_tombstone':'GENERATION_WRITER','extinction':'EXTINCTION_WRITER'}
    observers={'reservation':'OUTCOME_OBSERVER','transition':'REGISTRY_OBSERVER','outcome':'OUTCOME_OBSERVER','audit':'AUDIT_OBSERVER','participant_registry':'REGISTRY_OBSERVER','generation_tombstone':'REGISTRY_OBSERVER','extinction':'EXTINCTION_OBSERVER'}
    stores=[]
    for i,(name,fields) in enumerate(store_fields.items()):
        stores.append(dict(store=name,record_version=1,store_id=actor('STORE/'+name),path='/var/lib/flooow/b01-r5/'+name+'/ledger',
          field_order=CONTEXT+[fld('store_id','u16'),fld('record_revision','u64'),fld('previous_tip','bytes32'),fld('entity_key_digest','bytes32'),fld('entity_revision','u64'),fld('prior_entity_record','bytes32')]+fields,
          encoding=ENCODING,store_enum=i+1,identity_key=['qualification_id','epoch','generation','operation_id','store_id'],
          generation_key=['qualification_id','epoch','generation'],
          logical_entity_key={'reservation':['qualification_id','epoch','generation','operation_id'],
            'transition':['qualification_id','epoch'],
            'outcome':['qualification_id','epoch','generation','operation_id'],
            'audit':['qualification_id','epoch','decision_id'],
            'participant_registry':['qualification_id','epoch','participant_slot','participant_generation'],
            'generation_tombstone':['qualification_id','epoch','participant_slot','retired_generation'],
            'extinction':['qualification_id','epoch','retired_enrollment']}[name],
          CAS_predicate='Exclusive writer; expected global revision/tip == verified durable global tip AND expected entity revision/prior record == independently reconstructed latest record for entity_key_digest AND requested phase edge legal. New operation_id never resets existing entity. Consume exact request idempotency key; append global+1/entity+1 checked; any conflict denies without replacement',
          writer=actor(writers[name]),writer_credential=actor(writers[name])+'/SIGNING_KEY',
          observer=actor(observers[name]),observer_credential=actor(observers[name])+'/SIGNING_KEY',
          append_update='Append only. No in-place rewrite/truncate/delete. Logical state changes append predecessor-bound new revision; terminal keys cannot reactivate',
          record_envelope='u32be record size || canonical signed frame || SHA256(frame), no trailing bytes; writer signature binds store_id/type and full context',
          atomicity='Dedicated single writer per store, exclusive OS lock; before receipt append entire record, fsync ledger then fsync parent directory for creation/rotation. Startup scans complete length+signature+hash+revision chain; partial tail or ambiguous durability quarantines store and records UNKNOWN externally; never truncate into inferred abort',
          durability='Receipt only after full fsync success and independent observer reread of identical durable tip; fsync error/lost ACK => UNKNOWN. No network/distributed filesystem assumption; future filesystem crash behavior must be qualified',
          replay='Same operation identity key and exact canonical digest returns original signed receipt without append/effect; different digest conflicts; different operation targeting same entity must satisfy existing entity CAS/phase, never create fresh eligibility; pending never re-executes',
          corruption='Invalid signature/hash/length/revision/tip/missing predecessor or duplicated key => store quarantined; no repair/zero/default state',
          UNKNOWN='Persist pending on separate independently durable reservation/outcome lineage; block new work, generation and reseal until independent resolution',
          physical_instance=None,STATIC_DESIGN_BOUND=True,PHYSICAL_INSTANTIATION_PENDING=True,RUNTIME_PROOF_PENDING=True))
    doc('durable-ledger-protocol',stores=stores,enum_rules=dict(
        outcome={'PENDING':1,'COMMITTED':2,'ABORTED_PROVEN':3,'UNKNOWN':4},extinction={'PENDING':1,'EXTINCT_PROVEN':2,'UNKNOWN':3},
        reservation={'RESERVED':1,'IN_FLIGHT':2,'TERMINAL':3,'UNKNOWN':4},
        registry={'PROVISIONAL':1,'ENROLLED':2,'WORK_PENDING':3,'WORK_OBSERVED':4,'PUBLISHED':5,'REVOKED':6,'EXTINCT':7,'UNKNOWN':8}),
        entity_encoding='entity_key_digest=SHA256(canonical typed frame domain FLOOOW/B01/R5/ENTITY/V1, store_enum u16 followed by logical_entity_key fields in declared order and original types). Recompute from record fields and reject mismatch; no caller-selected key list. Entity index is reconstructed only from complete verified append chain, never mutable external authority',
        genesis='Fresh store global predecessor=SHA256(canonical frame domain FLOOOW/B01/R5/GENESIS/V1, fields store_enum u16,record_version u16,qualification_id uuid,deployment_id uuid,policy_digest bytes32,manifest_digest bytes32). First global revision=1. First entity predecessor=SHA256(ASCII FLOOOW/B01/R5/ENTITY-GENESIS/V1 || entity_key_digest), first entity revision=1 only after verified complete chain proves entity absent. Unknown/missing/corrupt chain never authorizes genesis or entity absence',
        nullability='Only fields explicitly marked nullable accept null; transaction_full_id absent only for non-SQL effects; future_currentness_link absent means NOT_YET_QUALIFIED, never eligible; missing work_receipt is pre-work only',
        transport='Writer-specific signed message type=400+store_enum, recipient exact writer enum; observer receipt type=500+store_enum contains key/revision/tip/full context; no caller path, store or schema selector')
    for name,store in [('durable-reservation-contract',stores[0]),('durable-outcome-contract',stores[2]),('durable-audit-contract',stores[3])]:
        doc(name,store=store,other_store_ownership_forbidden=True,
            outcome_evidence='COMMITTED requires exact full transaction plus independently observed expected dependency delta; ABORTED_PROVEN requires independent no-effect/transaction resolution; timeout, process death or absent row is not abort',
            static_gap='Exact per-writer syscall confinement and filesystem credential/read entitlement not fully source-to-effect proven; complete store schema does not close endpoint denominator')
    # Identity namespace includes every specified actor; not all physical endpoints are enumerated by this contract.
    doc('qualification-universe',identities=[dict(id=actor(a),actor_enum=i+1,category='TEST_QUALIFICATION',
       credential_id=actor(a)+'/SIGNING_KEY',independence='Distinct process/UID/key/enrollment; actual mapping from immutable bootstrap manifest, never hard-coded live PID/UID',
       physical_instance=None) for i,a in enumerate(ACTORS)]+[
       dict(id='TEST/R5/BOOTSTRAP_CUSTODIAN',category='TRUST_BOUNDARY',authority='Provision immutable isolated TEST environment before enrollment; destroy it after drain. No operational broker-callable superuser/root/CREATEROLE path'),
       dict(id='CANONICAL/MANIFEST_V6',category='CANONICAL',source=ref(SRC+'expected-currentness-manifest-v6.json')),
       dict(id='EXTERNAL/R5/AUDIT_WITNESS',category='EXTERNAL_OBSERVER',authority='Read-only verify independently copied signed ledger tips; no participant or mutation credentials')],
       universe_identity=CONTEXT,store_identities=[s['store_id'] for s in stores],
       complete=False,unknown_boundary='All dynamic kernel descriptors/descendants, provider-dependent SQL privileges and loader/startup authorities require full source-to-effect enumeration; declared actor/type set is not complete endpoint denominator',
       no_production_carryover=True,no_canonical_overlay=True)
    endpoints=[]
    # Fixed topology classes derived per role, direction and durable store, never one generic process class.
    for a in ACTORS:
        for kind in ['PROCESS','BIRTH_PIDFD','PARENT_PIDFD','ENROLLMENT','GENERATION','CHANNEL_SEND','CHANNEL_RECEIVE','SIGNING_KEY','LOADER_MANIFEST','INHERITED_CONTEXT']:
            endpoints.append(dict(ENDPOINT_ID=actor(a)+'/'+kind,TYPE=kind,CREATOR='TEST/R5/BOOTSTRAP_CUSTODIAN',OWNER=actor(a),HOLDER=actor(a),
              REQUESTER=actor('TRANSITION_WORKER'),TRANSFER_PATH='Bootstrap SCM_RIGHTS once, exact signed inventory+sender/recipient anchors before enrollment; no new rights transfer after sealed enrollment',
              AUTHORITY='Only native-message-abi fixed sender/recipient/message types for this actor; no target/path/SQL selectors',
              CREDENTIAL=actor(a)+'/SIGNING_KEY',GENERATION=['qualification_id','epoch','generation','enrollment_digest'],
              REVOCATION_TRIGGER=['quarantine','context_drift','key_or_channel_mismatch','old_generation','pending_UNKNOWN'],
              REVOCATION_ACTOR=actor('GENERATION_WRITER'),EXTINCTION_OBSERVER=actor('EXTINCTION_OBSERVER'),
              DURABLE_RECEIPT='extinction store full tuple + transfer/descendant/key/channel tombstone set',
              UNKNOWN_RULE='Missing instance/census/receipt blocks new enrollment and reseal',STATIC_DESIGN_BOUND=True,
              PHYSICAL_INSTANTIATION_PENDING=True,physical_instance=None))
    for s in stores:
        for kind in ['WRITE_FD','READ_FD','LOCK_FD','DIRECTORY_FD','OUTCOME_RECEIPT']:
            endpoints.append(dict(ENDPOINT_ID=s['store_id']+'/'+kind,TYPE=kind,CREATOR='TEST/R5/BOOTSTRAP_CUSTODIAN',OWNER=s['writer'],HOLDER=s['observer'] if kind=='READ_FD' else s['writer'],
              REQUESTER=actor('TRANSITION_WORKER'),TRANSFER_PATH='Exact one-time inherited descriptor inventory, no path opens post-enrollment',
              AUTHORITY='Writer append/CAS or observer read only for one fixed store, no alternate inode/directory selector',CREDENTIAL=s['writer_credential'] if kind!='READ_FD' else s['observer_credential'],
              GENERATION=s['generation_key'],REVOCATION_TRIGGER=['epoch_end','corruption','credential_drift','UNKNOWN'],REVOCATION_ACTOR=actor('GENERATION_WRITER'),
              EXTINCTION_OBSERVER=actor('EXTINCTION_OBSERVER'),DURABLE_RECEIPT='Signed descriptor/key retirement receipt plus independently witnessed final store tip',
              UNKNOWN_RULE='Ambiguous lock/write/fsync/descriptor closure => UNKNOWN, never reseal',STATIC_DESIGN_BOUND=True,PHYSICAL_INSTANTIATION_PENDING=True,physical_instance=None))
    for kind in ['SQL_CONNECTION','BACKEND_PID_START','SESSION_AUTHENTICATION','TRANSACTION_XID','RECONNECT_CANDIDATE','DESCENDANT_CENSUS','RESTART_CANDIDATE','SCM_RIGHTS_TRANSFER_LEDGER','POLICY_CURRENTNESS_HANDLE']:
        endpoints.append(dict(ENDPOINT_ID=actor('FINAL_CONSUMER')+'/'+kind,TYPE=kind,CREATOR='TEST/R5/BOOTSTRAP_CUSTODIAN',OWNER=actor('FINAL_CONSUMER'),HOLDER=actor('FINAL_CONSUMER'),REQUESTER=actor('FINAL_CONSUMER'),
          TRANSFER_PATH='Never transfer authenticated connection; observer receives only authenticated exact-tuple evidence',AUTHORITY='Exact original enrolled TEST auditor session; no helper SET, role/DB/epoch replacement',
          CREDENTIAL='TEST/R5/FINAL_CONSUMER/DB_AUTH_CREDENTIAL',GENERATION=['qualification_id','epoch','generation','session_enrollment'],REVOCATION_TRIGGER=['disconnect','backend_start_mismatch','pending_UNKNOWN','quarantine'],
          REVOCATION_ACTOR=actor('GENERATION_WRITER'),EXTINCTION_OBSERVER=actor('EXTINCTION_OBSERVER'),DURABLE_RECEIPT='Exact connection/backend identity + pending outcome + independent reconciliation/retirement receipts',
          UNKNOWN_RULE='Reconnect/restart never clears pending; no new enrollment until prior outcome resolved',STATIC_DESIGN_BOUND=False,PHYSICAL_INSTANTIATION_PENDING=True,physical_instance=None))
    assert len({e['ENDPOINT_ID'] for e in endpoints})==len(endpoints)
    doc('endpoint-inventory',endpoints=endpoints,known_design_classes=len(endpoints),ENDPOINTS_TOTAL=None,ENDPOINTS_FULLY_BOUND=0,UNBOUND_ENDPOINTS=None,
        complete=False,source_candidates=ref(R4+'endpoint-inventory-v4.json'),
        no_inherited_20_or_21_denominator=True,
        irreducible_static_gap='No complete role-specific syscall/startup/dependency FD and process creation model, SQL provider authority graph or independent final-consumer observer entitlement; extra descriptors/descendants remain possible, so closure cannot follow from generated rows')
    doc('endpoint-custody',endpoints=endpoints,actors=ACTORS,store_writer_observer_separation=True,complete=False)
    doc('revocation-graph',edges=[dict(endpoint=e['ENDPOINT_ID'],actor=e['REVOCATION_ACTOR'],observer=e['EXTINCTION_OBSERVER'],trigger=e['REVOCATION_TRIGGER'],receipt=e['DURABLE_RECEIPT']) for e in endpoints],
        closed=False,gap='Exact signal/DB-login revoke/key purge/descriptor revocation authority of GENERATION_WRITER is not fully confined by source; naming role does not authorize action')
    old=load(R4+'closed-epoch-state-machine-v4.json')
    (OUT/'frozen-state-machine-v4.json').write_bytes(BLOBS[R4+'closed-epoch-state-machine-v4.json'])
    doc('closed-epoch-state-machine',states=old['states'],transitions=old['transitions'],
        preserved_relation_sha256=sha(canonical(dict(states=old['states'],transitions=old['transitions']))),
        source=ref(R4+'closed-epoch-state-machine-v4.json'),no_semantic_correction=True)
    inv=load(R4+'closed-epoch-reseal-invariants-v4.json')['invariants']
    mappings=[('generation_tombstone','GENERATION_WRITER','REGISTRY_OBSERVER'),('extinction','EXTINCTION_WRITER','EXTINCTION_OBSERVER'),
       ('outcome','OUTCOME_WRITER','OUTCOME_OBSERVER'),('audit','AUDIT_WRITER','AUDIT_OBSERVER'),('generation_tombstone','GENERATION_WRITER','REGISTRY_OBSERVER'),
       ('transition','STATE_WRITER','REGISTRY_OBSERVER'),('participant_registry','REGISTRY_WRITER','REGISTRY_OBSERVER')]
    bindings=[dict(id=x['id'],PHYSICAL_TARGET_CLASS=actor('STORE/'+m[0]),WRITER=actor(m[1]),OBSERVER=actor(m[2]),
       REVOCATION_EVENT='Exact old-generation tombstone and eligibility invalidation for every known endpoint; no role grant inferred',
       EXTINCTION_EVIDENCE='Independent retained pidfd/descendant/descriptor/catalog/registry witnesses for full old endpoint inventory',
       DURABLE_RECEIPT='Canonical signed full context+store identity+revision+tip+independent observer witness',
       UNKNOWN_RULE='Any missing/stale/mismatched receipt blocks conjunction',
       STATIC_DESIGN_BOUND=False,PHYSICAL_INSTANTIATION_PENDING=True,RUNTIME_PROOF_PENDING=True,
       static_gap='Receipt schema and exact actor are specified; exhaustive target/entitlement/authority graph still open') for x,m in zip(inv,mappings)]
    doc('closed-epoch-reseal-invariants',invariants=bindings,RESEAL_INVARIANTS_TOTAL=7,RESEAL_INVARIANTS_STATICALLY_BOUND=0,RESEAL_INVARIANTS_PHYSICALLY_BOUND=0,
        gate='All seven exact independently KNOWN_TRUE same-context receipts required; UNKNOWN is never TRUE')
    doc('closed-epoch-physical-bindings',stores=stores,bindings=bindings,physical_instances=[],physical_instance_absence_is_not_design_gap=True,
        remaining_design_gap='Unknown endpoint inventory/entitlement/confinement, not merely absent runtime inode/PID/hash')
    cuts=load(R4+'closed-epoch-crash-matrix-v4.json')['cases']
    doc('closed-epoch-crash-matrix',cases=cuts,store_recovery='Every store uses durable-ledger-protocol scan; partial tail, unknown fsync or missing peer tip quarantines and preserves UNKNOWN; no blind replay or truncated-tail inferred rollback',
        all_state_cut_pairs=len(old['states'])*len(cuts),states=old['states'])
    doc('extinction-proof-contract',observers=[actor('EXTINCTION_OBSERVER'),actor('CATALOG_OBSERVER'),actor('REGISTRY_OBSERVER')],
        writer=actor('EXTINCTION_WRITER'),store='durable-ledger-protocol-v5.json#/stores/6',
        required=['all_exact_old_endpoints_revoked','all_retained_pidfds_exit_witnessed','all_descendants_reaped','all_descriptor_transfers_retired','all_SQL_PID_start_identities_absent','all_registry_rows_ineligible','independent_signed_receipts_durable'],
        UNKNOWN='Any inability to prove full inventory or required fact => UNKNOWN; exit/timeout alone does not prove extinction',static_complete=False)
    doc('consumer-session-contract',identity_fields=[f['name'] for f in CONTEXT]+['authenticated_handle_digest','session_user','before_setting','after_setting','outcome_receipt','independent_observer_receipt'],
        source=ref(R4+'consumer-session-contract-v4.json'),SQL_identity='test_0090_audit',helper_session_allowed=False,
        before_after='Same actual authenticated connection handle+backend PID/start; exact parameter enum from frozen R4, no new setting values',
        parameters=load(R4+'consumer-session-contract-v4.json')['parameter_contracts'],
        observer=actor('CONSUMER_OBSERVER'),reconnect='Durable pending reservation/outcome remains; forbid new enrollment until independent exact prior-session outcome reconciliation',
        deterministic_transport_required='Authenticate actual consumer request/response and backend provenance without exposing DB credentials or permitting observer/helper-session execution',
        STATIC_DESIGN_COMPLETE=False,
        exact_missing_design='Independent observer transport/authentication and entitlement for SAME original handle before/after session settings is not implemented in frozen source and is not closed by signing a consumer self-report; no validated fixed read-only provenance channel specified',
        future_physical_values=['actual_connection_handle','backend_PID_start','DB_auth_credential'],
        physical_values_not_the_reason_for_BLOCKED=True)
    doc('unknown-outcome-contract',key=[f['name'] for f in CONTEXT]+['reservation_digest','capability_digest','target_digest','consumer_enrollment'],
        states=['PENDING','COMMITTED','ABORTED_PROVEN','UNKNOWN'],store='durable-ledger-protocol-v5.json#/stores/2',
        survives_restart=True,survives_reconnect=True,new_enrollment_while_UNKNOWN=False,
        exact_rule='No transition out of UNKNOWN without independent observer receipt binding exact prior reservation/transaction/delta, new immutable outcome record and separate audit witness; timeout/death/absent row never substitute',
        static_complete=False,gap='Observer entitlement and complete effect/dependency denominator unresolved')

def partitions():
    # Preserve EVERY inherited null-target obligation; assigning a store/type does not resolve it.
    inherited=load(R4+'class-mechanism-partitions-v4.json')['individual_missing_target_obligations']
    graph=load(SRC+'s04-reachability-graph-v3.json');nodes={n['id']:n for n in graph['nodes']}
    mapping={'audit_binding':('audit','AUDIT_WRITER','AUDIT_OBSERVER'),
      'native_anchor':('generation_tombstone','GENERATION_WRITER','EXTINCTION_OBSERVER'),
      'native_binding':('participant_registry','REGISTRY_WRITER','REGISTRY_OBSERVER'),
      'native_participant':('participant_registry','REGISTRY_WRITER','REGISTRY_OBSERVER'),
      'policy_readiness_binding':('transition','POLICY_CUSTODIAN','REGISTRY_OBSERVER'),
      'session_environment':('original_session','FINAL_CONSUMER','CONSUMER_OBSERVER')}
    rows=[]
    for x in inherited:
        node_id=x['dependency_effect']['source_node'];n=nodes[node_id];kind=node_id.split(':')[0];store,w,o=mapping[kind]
        rows.append(dict(OBLIGATION_ID=x['id'],SOURCE_NODE=node_id,OPERATION_FORM=x['operation_form'],
          APPLICABILITY=dict(status='UNKNOWN',required='Per-form provider/source/domain preconditions, data-dependent validity and exact sealed-epoch authority; not deduced from lexical operation name'),
          PHYSICAL_TARGET=None,proposed_static_target=dict(store=actor('STORE/'+store) if store!='original_session' else actor('FINAL_CONSUMER')+'/SQL_CONNECTION',
            source_fields=n['fields'],source_selector=x['source_authority']),
          TARGET_IDENTITY_RULE=dict(required_fields=[f['name'] for f in CONTEXT]+['source_node_digest','operation_form_digest','exact_target_field_path','expected_store_revision'],
            unresolved='No source-to-store field mapping/effect proof justifies equating this canonical semantic rule with proposed TEST field'),
          ACTOR=actor(w),ACTOR_AUTHORITY='NOT_PROVEN: proposed writer identity is not per-operation entitlement',
          CREDENTIAL=actor(w)+'/SIGNING_KEY; exact operation authority not derived',DEPENDENCY_EFFECTS=x['dependency_effect'],
          OBSERVER=actor(o),OUTCOME_BINDING='Exact reservation/target/before/after/dependency delta in outcome ledger; independent observer entitlement NOT_PROVEN',
          REVOCATION_BINDING='Full old-generation target/credential/endpoint tombstone + independent extinction proof; denominator incomplete',
          UNKNOWN_BEHAVIOR='Retain durable pending tuple; deny effect/approval/reseal/new enrollment',SOURCE_PROOF=x['source_authority'],
          STATIC_STATUS='NOT_PROVEN',representative_collapse=False,source_fields=n['fields'],
          reason='Exact canonical-to-TEST field/effect/authority interpretation plus provider/data dependency applicability is incomplete; no obligation closed by target type alone'))
    assert len(rows)==len({r['OBLIGATION_ID'] for r in rows})==422
    doc('physical-target-bindings',obligations=rows,required_inherited_IDs=422,resolved=0,unresolved=422,complete=False)
    classes=load(R4+'class-mechanism-partitions-v4.json')['classes']
    doc('class-mechanism-partitions',classes=classes,CLASSES_REQUIRED=46,CLASSES_FULLY_PARTITIONED=0,
        source_authority=ref(R4+'class-mechanism-partitions-v4.json'),
        per_class_obligation_ids={c['CLASS_ID']:[r['OBLIGATION_ID'] for r in rows if r['SOURCE_NODE'].split(':')[0]==c['CLASS_ID'].rsplit('/',1)[1]] for c in classes},
        no_representative_collapse=True,complete=False,
        missing_proof='Full grantor/creator/default/membership/owner/SD/schema/bootstrap/session/native source-to-effect graph and operation applicability not complete')
    doc('mechanism-denominator',known_source_node_operation_forms=445136,MECHANISMS_TOTAL=None,denominator_complete=False,
        UNRESOLVED_PHYSICAL_TARGETS=422,UNJUSTIFIED_REPRESENTATIVE_COLLAPSES=0,UNCLASSIFIED_MECHANISMS=None,
        known_expansion_sha256='a55beb57cdca0a36be5e4b9016eea6fadb3964d6ce732cd5e5c4852b7c672d25',
        source=ref(R3+'derive.py'),null_is_not_zero=True,capability_derivation_allowed=False)
    providers=[ref(p) for p in sorted(BLOBS) if p.startswith(SRC+'provider/')]
    doc('constraint-applicability',records=load(R4+'constraint-applicability-v4.json')['records'],
        source=ref(R4+'constraint-applicability-v4.json'),provider_sources=providers,
        required=['NOT_NULL','CHECK','FK','PK','UNIQUE','backing_index','RI_triggers','generated_names','dependency_effects','VALIDATE','data_dependent'],
        exact_semantic_closure=False,lexical_scan_does_not_prove_AST=True)
    dims=['direct_GRANT','REVOKE','grantor','ownership','SET_ROLE','role_membership','transitive_membership','INHERIT','ADMIN_OPTION','PUBLIC','schema_authority','default_privileges','object_creator_defaults','SECURITY_DEFINER','function_owner','search_path','dependency_effects','CREATEROLE','superuser_bootstrap_boundary','wrapper_authority','native_actor_authority','session_authority']
    doc('acl-origin-ledger',prior_evidence=load(R4+'acl-origin-ledger-v4.json'),source=ref(R4+'acl-origin-ledger-v4.json'),
        independently_required_origin_dimensions=dims,semantic_provider_authority=providers,
        closure='NOT_PROVEN: current effective rows cannot establish exact unique grantor/creator/role path and per-operation effect; no lexical AST claim')
    doc('dependency-effect-ledger',obligations=[dict(id=r['OBLIGATION_ID'],source=r['SOURCE_PROOF'],operation=r['OPERATION_FORM'],dependencies=r['DEPENDENCY_EFFECTS'],complete=False) for r in rows],
        provider_sources=providers,complete=False,AST_complete=False)
    # Source graph is finite. Full physical authority graph is not inferred from it.
    edges=graph.get('edges',[])
    doc('authority-graph',source=ref(SRC+'s04-reachability-graph-v3.json'),source_graph_edge_count=len(edges),
        source_graph_edges_sha256=sha(canonical(edges)),
        classification_domain=['DENIED','MEDIATED_BY_FIXED_CAPABILITY','BOOTSTRAP_ONLY_NON_OPERATIONAL','READ_ONLY','TEST_ONLY_CONFINED','UNKNOWN'],
        inherited_unresolved_edges=[dict(obligation=r['OBLIGATION_ID'],source=r['SOURCE_NODE'],target=r['proposed_static_target'],actor=r['ACTOR'],classification='UNKNOWN',reason=r['reason']) for r in rows],
        AUTHORITY_EDGES_TOTAL=None,AUTHORITY_EDGES_CLASSIFIED=0,UNCLASSIFIED_MUTATION_EDGES=None,UNMEDIATED_ACTIVE_MUTATION_EDGES=None,
        complete=False,unknown_blocks=True,absence_is_not_denial=True)

def templates_and_decision():
    # Denominator remains open; Phase5 explicitly forbids capability derivation.
    for name,field in [('typed-capability-catalog','required_typed_capabilities'),('fixed-operation-templates','required_templates'),
       ('capability-principal-bindings','required_principals'),('capability-outcome-bindings','required_outcomes'),
       ('capability-observer-bindings','required_observers'),('executor-confinement','required_confined_executors')]:
        doc(name,**{field:None},derived_records=[],denominator_complete=False,
            derivation_status='BLOCKED_BY_PHASES_2_TO_4',RAW_AUTHORITY_SURFACE='NOT_PROVEN',
            empty_means_not_derived_not_zero=True,
            forbidden=['generic_SQL','generic_psql','generic_shell','superuser_broker','CREATEROLE_broker','arbitrary_identifier','arbitrary_target','SQL_fragments','generic_native_worker','shared_cross_authority_credential'],
            cross_capability_rejection_tests='NOT_DERIVABLE until exact complete capability/operation/credential domain exists; no sample-based proof')
    doc('fixture-correction-revalidation',source=ref(R4+'fixture-correction-revalidation-v4.json'),
        canonical_manifest=ref(SRC+'expected-currentness-manifest-v6.json'),MANIFEST_COMPATIBILITY_DECISION='C. B01_FIXTURE_MUST_CHANGE',
        exact_wrapper='public.offline_read_history(uuid,bytea,uuid,text)',auditor='test_0090_audit',
        required=['restore exact auditor EXECUTE','remove private Package-owner SET membership','zero incoming ADMIN owner memberships','zero outgoing ADMIN owner memberships','raw history SELECT denied','no transitive owner path','no PUBLIC bypass','no default bypass','no SECURITY DEFINER bypass','no CREATEROLE bypass','no operational bootstrap credential'],
        FIXTURE_CORRECTION_REVALIDATION='NOT_PROVEN',why='Exact authority graph and operation-specific principal/credential confinement remain incomplete',
        implemented=False,canonical_overlay=False)
    residual={
      'V2-NATIVE':('Exact participant-specific syscall/filter startup closure, role-specific credential permissions and fixed catalog-observer provenance entitlement are not source-to-effect closed. Message/registry/loader recipes are now explicit; absent future binary hashes alone are NOT a design blocker.',
        'Complete deterministic per-role privilege/filter and catalog witness contracts, then independent static review. Only afterward implement/build/run in separately authorized tranche.'),
      'V2-EPOCH':('Endpoint generation/transfer/descendant/descriptor and final-original-consumer independent observation authority are not exhaustive. Seven stores now have exact codecs/CAS/durability protocols; schemas do not establish observer entitlement or endpoint completeness.',
        'Close exact endpoint/syscall/provider authority inventory and credential-free independent original-handle witness design; retain seven reseal proofs unbound until complete.'),
      'V2-PARTITIONS':('All422 IDs retained individually; exact canonical-rule-to-TEST field/effect/authority interpretation, grantor/default/creator/membership/SD and provider/data applicability still incomplete; complete physical mechanism/authority denominators unknown.',
        'Finish semantic per-obligation source-to-effect/provider applicability and full graph enumeration; an offline analyzer/design proof is required, not necessarily a live DB.'),
      'V2-TEMPLATES':('Required typed capability denominator cannot be derived while physical design denominator remains incomplete; no minimum capability catalog or cross-capability proof can be claimed.',
        'After other static denominators close, derive exact minimum target/principal/credential/executor/observer/outcome templates and exhaustive pairwise rejection contracts.')}
    blocks=[]
    for k,(gap,action) in residual.items():
        blocks.append(dict(ID=k,EXACT_MISSING_PROOF=gap,WHY_STATIC_CLOSURE_FAILED='Deterministic design/semantic authority proof still missing; not blocked solely by future runtime values',
          MINIMUM_NEXT_ACTION=action,WHETHER_IMPLEMENTATION_IS_REQUIRED='NO_FOR_REMAINING_STATIC_DESIGN; YES_FOR_LATER_INSTANTIATION',
          WHETHER_BUILD_EVIDENCE_IS_REQUIRED='NO_FOR_STATIC_RECIPE; YES_FOR_ACTUAL_BINARY_LOADER_HASHES',
          WHETHER_RUNTIME_EVIDENCE_IS_REQUIRED='NO_FOR_STATIC_DESIGN; YES_FOR_ACTUAL_ISOLATION_EXTINCTION_DURABILITY',
          WHETHER_LIVE_DB_IS_REQUIRED='NO_FOR_THIS_STATIC_GATE; LATER_DISPOSABLE_TEST_DB_ONLY_UNDER_NEW_AUTHORITY',
          proof_level='NOT_PROVEN',independent_review='PENDING'))
    save('findings.json',dict(BLOCKER_COUNT=4,HIGH_COUNT=0,MEDIUM_COUNT=0,LOW_COUNT=0,blockers=blocks,
       irreducible_proof_boundaries=dict(build_only=['actual executable/module/loader SHA256','resolved built dependency map'],
         runtime_only=['actual pidfd/backend/session identities','observed crash fsync durability','actual syscall isolation','actual descendant/descriptor extinction'],
         static_missing=['per-role filter/credential/catalog witness design','complete endpoint/authority/applicability graph','final consumer independent provenance channel']),
       no_runtime_absence_promoted_to_missing_design=True))
    gate=dict(BRANCH=BRANCH,BASELINE_HEAD=BASE,CURRENT_V043_GIT_LF_SHA256=VHASH,FLYWAY_SIGNED_CRC32=1279591798,
      V043_FENCE_PRESENT=True,CANONICAL_V043_MUTATED=False,CANONICAL_V043_EXECUTED=False,SHARED_DB_CONTACTED=False,PRODUCTION_CONTACTED=False,
      QUALIFICATION_UNIVERSE_COMPLETE='NOT_PROVEN',CLASSES_REQUIRED=46,CLASSES_FULLY_PARTITIONED=0,MECHANISMS_TOTAL=None,
      UNRESOLVED_PHYSICAL_TARGETS=422,UNJUSTIFIED_REPRESENTATIVE_COLLAPSES=0,
      NATIVE_PARTICIPANTS_REQUIRED=7,NATIVE_PARTICIPANTS_FULLY_DESIGNED=0,UNRESOLVED_NATIVE_WORK_ANCHORS=7,GENERIC_PROCESS_SUBSTITUTIONS=0,
      ENDPOINTS_TOTAL=None,ENDPOINTS_FULLY_BOUND=0,UNBOUND_ENDPOINTS=None,
      RESEAL_INVARIANTS_TOTAL=7,RESEAL_INVARIANTS_STATICALLY_BOUND=0,RESEAL_INVARIANTS_PHYSICALLY_BOUND=0,
      FINAL_CONSUMER_SESSION_CONTRACT_COMPLETE='NOT_PROVEN',REQUIRED_TYPED_CAPABILITIES=None,CAPABILITIES_WITH_FIXED_TEMPLATE=None,
      CAPABILITIES_WITH_EXACT_PRINCIPAL=None,CAPABILITIES_WITH_OUTCOME_BINDING=None,CAPABILITIES_WITH_OBSERVER_BINDING=None,CAPABILITIES_WITH_CONFINED_EXECUTOR=None,RAW_AUTHORITY_SURFACE='NOT_PROVEN',
      AUTHORITY_EDGES_TOTAL=None,AUTHORITY_EDGES_CLASSIFIED=0,UNCLASSIFIED_MUTATION_EDGES=None,UNMEDIATED_ACTIVE_MUTATION_EDGES=None,
      MANIFEST_COMPATIBILITY_DECISION='C. B01_FIXTURE_MUST_CHANGE',FIXTURE_CORRECTION_REVALIDATION='NOT_PROVEN',
      LEAST_PRIVILEGE_REVIEW='PENDING',STATIC_ADVERSARIAL_REVIEW='PENDING',BLOCKER_COUNT=4,HIGH_COUNT=0,MEDIUM_COUNT=0,LOW_COUNT=0,
      STATIC_GATE='BLOCKED',CURRENTNESS_MUTATION_CLASSES_PROVEN=0,CURRENTNESS_MUTATION_CLASSES_UNPROVEN=46,
      B02_CURRENTNESS_INTEGRATION_GATE='NOT_RERUN',COMPLETE_CURRENTNESS_GATE='FAIL_NOT_RERUN',NEXT_EXECUTED=False,
      NEXT_GATE='COMPLETE_REMAINING_STATIC_DESIGN_PROOFS_NO_LIVE_EXECUTION')
    save('STATIC-GATE.json',gate)

def generate():
    freeze();native();epoch();partitions();templates_and_decision()
    print(json.dumps(dict(generated=True,sources=len(BLOBS),inherited_obligations=422,STATIC_GATE='BLOCKED',no_runtime=True)))
