"""R5N native design evidence only. No module implementation or live execution."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
BRANCH='checkpoint/package-0090-cloud-handoff'
R5='docs/evidence/package-0090-B01-v2-static-closure-revision-5/'
R4='docs/evidence/package-0090-B01-v2-static-closure-revision-4/'
SRC='docs/evidence/package-0090-full-reachable-expectation-closure-v2/'
N='scripts/validation/package_0090_native_health_qualification/'
NATIVE=SRC+'native-proof-v6.json'
REPORT='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n.md'

def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def save(n,x):(OUT/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def doc(n,**kw):save(n+'.json',dict(scope='R5N_TEST_ONLY_NATIVE_STATIC_DESIGN',implementation_authorized=False,runtime_proven=False,**kw))
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def ref(p,ptr='/'):
    b=(ROOT/p).read_bytes();return dict(path=p,sha256=sha(b),pointer=ptr)
def actor(p):return 'R5N/'+p
def f(n,t,length,**kw):return dict(name=n,type=t,encoded_value_length=length,nullable=False,**kw)

def future(name,authority,inputs,algorithm,target,verifier):
    return dict(field=name,VALUE_STATE='FUTURE_MEASURED',MEASUREMENT_AUTHORITY=authority,
      CANONICAL_INPUT=inputs,MEASUREMENT_ALGORITHM=algorithm,BINDING_TARGET=target,VERIFIER=verifier,
      MISMATCH_BEHAVIOR='FAIL_CLOSED: quarantine, no enrollment/publication, preserve UNKNOWN',
      authority_time='Only after independent verification AND signed approved expected-manifest binding, never automatic trust-on-first-use',
      replay='Exact current incarnation/slot/generation and immutable expected manifest digest required; old value never adopted',actual_value_present=False)

def freeze():
    global ROSTER,AUTH,ACTORS
    assert git('branch','--show-current').decode().strip()==BRANCH
    assert git('rev-parse','HEAD').decode().strip()==BASE==git('rev-parse','origin/'+BRANCH).decode().strip()
    assert git('diff','--name-only')==git('diff','--cached','--name-only')==b''
    prior=load(R5+'baseline-freeze.json');inputs={p:sha((ROOT/p).read_bytes()) for p in prior['input_git_sha256']}
    old=git('ls-files','--others','--exclude-standard').decode().splitlines()
    r5paths=[p for p in old if p.startswith(R5) or p=='docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-5.md']
    assert len(r5paths)==51
    for p in r5paths:inputs[p]=sha((ROOT/p).read_bytes())
    for p in (ROOT/R5).iterdir():
        if p.suffix=='.json':json.loads(p.read_text(encoding='utf-8-sig'))
        else:p.read_bytes()
    for p in (ROOT/R4).iterdir():p.read_bytes()
    m=load(R5+'SHA256-MANIFEST.json')
    for p,h in m['files'].items():
        b=(ROOT/p).read_bytes();b=b.replace(b'\r\n',b'\n') if p.endswith('.md') else b
        assert sha(b)==h,p
    AUTH=load(NATIVE);ROSTER=[x['PARTICIPANT_NAME'] for x in AUTH['participants']]
    assert len(ROSTER)==len(set(ROSTER))==7
    ACTORS=ROSTER+['HEALTH_GUARD','HOST_PLATFORM','NATIVE_REGISTRY_WRITER']
    save('baseline-freeze.json',dict(branch=BRANCH,baseline_head=BASE,remote_tracking_head=BASE,
      remote_authority='existing origin tracking reference; no network call',TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,
      UNTRACKED_BEFORE=51,untracked_before_paths=sorted(r5paths),UNAUTHORIZED_UNTRACKED_PATHS=[],
      source_checkout_sha256=dict(sorted(inputs.items())),source_Git_LF_sha256=prior['input_git_sha256'],
      complete_R5_manifest_verified=True,complete_R5_files_consumed=51,R4_consumed=True,
      CURRENT_V043_GIT_LF_SHA256=prior['CURRENT_V043_GIT_LF_SHA256'],FLYWAY_SIGNED_CRC32=prior['FLYWAY_SIGNED_CRC32'],V043_FENCE_PRESENT=True,
      noncontact_basis='R5 immutable negative records + only file/Git reads in this gate; no forensic assertion about unseen external actors'))

def audit():
    lp=load(R5+'least-privilege-review-v5.json');fail=[(i,x) for i,x in enumerate(lp['checks']) if x['passed'] is False]
    assert len(fail)==len(lp['failures'])==lp['assertion_failures']==497
    assert {x['id'] for _,x in fail}==set(lp['failures'])
    rows=[]
    for i,x in fail:
        prefix=x['id'].split(':')[0]
        if prefix=='participant-privilege-closure':b='V2-NATIVE'
        elif prefix in ['obligation-design','class-design']:b='V2-PARTITIONS'
        elif prefix in ['store-authority','reseal-proof','consumer-original-handle-provenance']:b='V2-EPOCH'
        elif prefix in ['capability-closure','fixture-authority-closure']:b='V2-TEMPLATES'
        else:raise AssertionError(prefix)
        rows.append(dict(failure_id=x['id'],primary_blocker=b,source=ref(R5+'least-privilege-review-v5.json','/checks/'+str(i)),
          original_assertion=x,assignment_rule='Primary failing predicate owns the failure: per-role native privilege; physical class/target denominator; epoch store/reseal/session; capability/fixture authority. Native-themed target rows retain PARTITIONS primary and may have native secondary dependencies; none disappear',
          native_classification='L' if b=='V2-NATIVE' else 'NOT_NATIVE_PRIMARY',
          native_classification_reason='This is an aggregate per-participant failing closure predicate, derived from shared native proof families; it is not a missing binary value or an independent architecture defect' if b=='V2-NATIVE' else 'Outside native target; unchanged',
          future_implementation_evidence=False,future_build_evidence=False,future_runtime_evidence=False,
          closed_by_relabeling=False))
    roots=[dict(id='NATIVE/ISOLATION_CUSTODY',classifications=['A','E'],
       missing='Exact lifecycle phase, role-specific syscall/descriptor/UID/key/loader and privilege boundary',
       source=ref(R5+'native-confinement-contract-v5.json','/design_gap')),
      dict(id='NATIVE/CATALOG_WORK_WITNESS',classifications=['B','G'],
       missing='Exact independent server-generation/catalog/work attribution, with narrow observer entitlement rather than generic postgres helper credential',
       source=ref(R5+'static-adversarial-review-v5.json','/findings')),
      dict(id='NATIVE/PUBLICATION_GENERATION_BINDING',classifications=['C','F','H'],
       missing='Exact completed-work publication/registry/generation/replay and bootstrapping dependency protocol, distinct from runtime measured values',
       source=ref(R5+'native-seven-participant-contract-v5.json','/participants'))]
    edges=[]
    for r in rows:
        if r['primary_blocker']=='V2-NATIVE':
            slot=r['failure_id'].split(':',1)[1]
            deps=['NATIVE/ISOLATION_CUSTODY','NATIVE/PUBLICATION_GENERATION_BINDING']
            if slot in ['POSTMASTER','RECEIVER','CENSUS_OBSERVER']:deps+=['NATIVE/CATALOG_WORK_WITNESS']
            edges += [dict(cause=dep,consequence=r['failure_id'],relation='REQUIRED_PROOF_NOT_EQUIVALENCE') for dep in deps]
    counts={k:sum(r['primary_blocker']==k for r in rows) for k in ['V2-NATIVE','V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES']}
    assert counts=={'V2-NATIVE':7,'V2-EPOCH':15,'V2-PARTITIONS':468,'V2-TEMPLATES':7}
    doc('failure-audit',authoritative_source=ref(R5+'least-privilege-review-v5.json'),
       R5_DESIGN_FAILURES_TOTAL=497,failures=rows,primary_counts=counts,
       R5_NATIVE_FAILURES=7,R5_NATIVE_ROOT_CAUSES=3,R5_NATIVE_DUPLICATE_OR_DERIVED_FAILURES=7,
       R5_NATIVE_FUTURE_IMPLEMENTATION_EVIDENCE=0,R5_NATIVE_FUTURE_BUILD_EVIDENCE=0,R5_NATIVE_FUTURE_RUNTIME_EVIDENCE=0,
       classification_counts={c:(7 if c=='L' else 0) for c in 'ABCDEFGHIJKL'},
       root_cause_count_semantics='Three shared proof families, not three unique defects; each has seven participant-specific proof applications. All seven aggregate predicates remain individually traceable',
       no_failure_removed=True,non_target_failures_unchanged=490)
    doc('failure-dependency-graph',roots=roots,edges=edges,acyclic=True,
       no_equivalence_collapse=True,root_resolution_requires='Actual deterministic design rules and independent review; naming a family never closes a predicate')

def identities():
    old={r['participant']:r['existing_anchors'] for r in load(R5+'native-work-anchor-map-v5.json')['participants']}
    rows=[]
    for i,p in enumerate(ROSTER):
        a=AUTH['participants'][i]
        measured={
          'source_identity':future('source_identity','HOST_PLATFORM approved release custody',
             'Exact reviewed implementation source tree bytes for this slot, plus frozen primitive anchors; proposed module source does not yet exist',
             'SHA256 per file then SHA256 of length-framed sorted path+digest list','approved release manifest/slot','HEALTH_GUARD + release custodian'),
          'build_recipe_identity':future('build_recipe_identity','Independent TEST build/release custodian',
             'Exact compiler/linker/container/toolchain source/header digests, flags, source list and module contract digest',
             'SHA256 of typed ordered recipe frame; no ambient flag or PATH default','approved release manifest/slot','HOST_PLATFORM before spawn'),
          'binary_module_identity':future('binary_module_identity','Independent future build and approved release custodian',
             'Exact complete installed executable/shared-object file bytes, no source-hash substitution',
             'SHA256 all bytes; bind ELF architecture/class/PT_INTERP/build-id separately; expected digest approved before deployment','signed expected release manifest/slot','HOST_PLATFORM opens/hashes retained immutable executable handle; HEALTH_GUARD compares independently'),
          'dependency_set_identity':future('dependency_set_identity','Independent future build/release custodian',
             'Every transitive ELF DT_NEEDED/PT_INTERP resolution plus explicitly named dlopen providers (including frozen ICU primitive if used), resolved immutable path/link/inode/byte identity',
             'Resolve from empty loader environment and approved roots to fixed point; reject dynamic/unresolved/duplicate ambiguity; sorted typed node+edge frame SHA256','signed expected dependency manifest/slot','HOST_PLATFORM exact retained files plus HEALTH_GUARD loaded-map attestation'),
          'loader_identity':future('loader_identity','HOST_PLATFORM and approved build custodian',
             'Exact ELF interpreter/loader file bytes and closed relocation/provider allowlist',
             'SHA256 loader bytes plus SHA256 typed loader-resolution manifest; no PATH/LD_PRELOAD/LD_LIBRARY_PATH fallback','expected loader manifest digest','HOST_PLATFORM at start, HEALTH_GUARD before publication'),
          'parent_identity':future('parent_identity','HOST_PLATFORM retained birth-anchor custodian',
             'Parent boot_id, pid/user/mount/time namespace identities, cgroup identity, retained birth pidfd dev/inode, kernel start ticks, approved executable digest',
             'SHA256 exact typed parent tuple, independently retained before child enrollment; PID alone rejected','child enrollment and signed bootstrap descriptor inventory','HEALTH_GUARD; HOST_PLATFORM observes guard'),
          'process_instance_identity':future('process_instance_identity','HOST_PLATFORM retained kernel birth-anchor custody',
             'Same parent tuple plus slot, child retained birth pidfd dev/inode, kernel start ticks and qualification/incarnation',
             'Canonical tuple SHA256; compare retained kernel objects, never reacquire target by a claimed PID','current participant registry entity','HEALTH_GUARD via retained anchors and kernel per-message SCM_PIDFD'),
          'generation':future('generation','NATIVE_REGISTRY_WRITER with HEALTH_GUARD witness',
             'Verified prior native generation ledger high-water and irreversible tombstone chain for this qualification/incarnation/slot',
             'Fresh qualification first generation1 only after explicit genesis; replacement checked u64 previous+1, no rollback/fallback','current registry generation row','HEALTH_GUARD independently reads exact durable current entity'),
          'enrollment_identity':future('enrollment_identity','NATIVE_REGISTRY_WRITER',
             'Nonrecursive bootstrap context, slot, parent/process/source/build/binary/dependency/loader identities, already computed credential refs and already computed channel inventory; never include final enrollment inside channel input',
             'SHA256 canonical R5N enrollment record; CAS at exact current generation revision','participant registry entity','HEALTH_GUARD'),
          'credential_identity':future('credential_identity','HOST_PLATFORM private TEST key custodian',
             'Fresh slot/generation Ed25519 SPKI DER, credential purpose, qualification/incarnation, policy and allowed message types; no provider/canonical private key',
             'SHA256 SPKI DER + typed credential certificate; expected ref chosen from trusted enrollment, input reference must equal it','protected descriptor4 and current registry credential ref','HEALTH_GUARD checks expected certificate, peer identity and exact message signature'),
          'authenticated_channel_identity':future('authenticated_channel_identity','HOST_PLATFORM bootstrap socket inventory custodian',
             'socketpair inode/cookie pair, creator birth anchor, intended sender/recipient birth identities and roles (NOT final enrollment digests), descriptor-role numbers and namespace identities',
             'SHA256 signed immutable inventory; creation-time SO_PEERPIDFD checked as creator, each message current SCM_PIDFD checked as actual enrolled sender','enrollment and ABI channel ref','HEALTH_GUARD plus each distinct peer'),
          'registry_revision':future('registry_revision','NATIVE_REGISTRY_WRITER',
             'Exact generation-registry revision and independently current per-entity work-publication revisions',
             'Checked monotonic u64 revisions with exact predecessor/key CAS; no missing-row reset','all work/approval/guard tuples','HEALTH_GUARD'),
          'completed_work_identity':future('completed_work_identity','Independent work observer and NATIVE_REGISTRY_WRITER',
             'Exact challenge/input/expected-result/result/witness/full-context tuple for this participant and current generation',
             'SHA256 canonical completed-work record only after role-specific independent result observation, followed by one-use publication CAS','completed-work publication entity','HEALTH_GUARD + participant-specific independent witness')}
        if p=='POSTMASTER':
            measured['credential_identity']=future('credential_identity','HOST_PLATFORM approved native server endpoint custody',
              'Exact private TEST server endpoint owner/namespace, approved postmaster/backend bridge identity, protected native snapshot ACL/owner identity and enrolled observer role mapping; no fabricated POSTMASTER Ed25519 sender',
              'SHA256 canonical server-endpoint authentication manifest; two independent probes and retained postmaster/backend anchors must match it',
              'POSTMASTER subject credential_ref; actual witness sender_credential_ref is independently CENSUS_OBSERVER key',
              'HEALTH_GUARD + CENSUS_OBSERVER, each with its own fixed authenticated observation session')
            measured['authenticated_channel_identity']=future('authenticated_channel_identity','HOST_PLATFORM endpoint inventory custody',
              'Exact private TEST PostgreSQL endpoint, native snapshot helper identity and protected observer role/session bindings; witness AF_UNIX channel inventory separately identifies actual emitter',
              'SHA256 canonical endpoint inventory; exact catalog/server generation and retained postmaster/backend anchors cross-checked independently',
              'POSTMASTER probe subject channel identity, never a fake postmaster native socket/response',
              'HEALTH_GUARD + CENSUS_OBSERVER')
        rows.append(dict(PARTICIPANT_ID=p,participant_enum=i+1,PURPOSE=a['PROGRESS_SOURCE'],
          canonical_source=ref(NATIVE,'/participants/'+str(i)),EXISTING_SOURCE_ANCHORS=old[p],
          PARENT_REQUIREMENT='HOST_PLATFORM bootstrap retained parent' if p=='SUPERVISOR' else 'SUPERVISOR retained parent; replacement during sealed generation forbidden; full generation drain before fresh spawn phase',
          INDEPENDENCE_REQUIREMENT='Distinct process/birth anchor/UID/key/channel from other participant slots; no thread/harness/nonce identity substitute',
          EXECUTABLE_OR_MODULE_CLASS=('approved PostgreSQL18 engine plus TEST login bridge' if p=='POSTMASTER' else 'purpose-specific immutable TEST executable for '+p),
          DEPENDENCY_CLASS='Signed approved closed loader/dependency graph, measured later with complete rules now',
          CREDENTIAL_CLASS='Authenticated private TEST server-endpoint identity; distinct observer keys sign probe witnesses, never impersonate postmaster' if p=='POSTMASTER' else 'Slot/generation/purpose-bound TEST Ed25519 transport key; one-use work authorization separate from bounded heartbeat authentication',
          CHANNEL_CLASS='Private fixed TEST PostgreSQL generation/catalog probe endpoint + distinct authenticated observer witness channels' if p=='POSTMASTER' else 'Inherited AF_UNIX SOCK_SEQPACKET, signed creation inventory + kernel current SCM_PIDFD',
          GENERATION_CLASS='Monotonic current entity + irreversible high-water/tombstone, no replacement on unknown lineage',
          REGISTRY_CLASS='Native-only typed journal and current entity index, not epoch/global authority',
          WORK_PROOF_CLASS=a['COMPLETED_WORK_WITNESS'],GUARD_CLASS='Independent HEALTH_GUARD observed by HOST_PLATFORM',
          OBSERVER_CLASS='Independent native work witness, never subject-signed success alone',
          REVOCATION_CLASS='Current generation invalidation + registry tombstone + key/channel ineligibility; no automatic production/recovery authority',
          EXTINCTION_CLASS='Independent retained anchor+descendant+descriptor+catalog+registry evidence; death/timeout/absence alone insufficient',
          identity_tuple=dict(participant_logical_ID=p,participant_role=p,approved_primitive_anchors=old[p],measured_fields=measured,measurement_codec='native-identity-codec.json'),
          STATIC_DESIGN_COMPLETE='PROPOSED_COMPLETE_REQUIRES_INDEPENDENT_REVIEW',IMPLEMENTATION_PRESENT=False,
          BUILD_IDENTITY_INSTANTIATED=False,RUNTIME_IDENTITY_INSTANTIATED=False,RUNTIME_QUALIFIED=False))
    measurement_schemas={
      'source_identity':[f('source_tree_manifest_digest','bytes32',32),f('role_contract_digest','bytes32',32)],
      'build_recipe_identity':[f('recipe_manifest_digest','bytes32',32),f('source_identity','bytes32',32),f('toolchain_manifest_digest','bytes32',32),f('role_contract_digest','bytes32',32)],
      'binary_module_identity':[f('complete_file_sha256','bytes32',32),f('ELF_class','u16',2),f('ELF_machine','u16',2),f('loader_identity','bytes32',32),f('build_recipe_identity','bytes32',32)],
      'dependency_set_identity':[f('dependency_nodes','dependency_node_set','1..1048576'),f('dependency_edges','dependency_edge_set','1..1048576')],
      'loader_identity':[f('complete_loader_file_sha256','bytes32',32),f('resolution_manifest_digest','bytes32',32)],
      'parent_identity':[f('boot_id','uuid',16),f('pid_namespace_inode','u64',8),f('user_namespace_inode','u64',8),f('mount_namespace_inode','u64',8),f('time_namespace_inode','u64',8),f('cgroup_identity','bytes32',32),f('retained_pidfd_dev','u64',8),f('retained_pidfd_inode','u64',8),f('kernel_start_ticks','u64',8),f('approved_binary_identity','bytes32',32)],
      'process_instance_identity':[f('parent_identity','bytes32',32),f('participant_id','u16',2),f('child_pidfd_dev','u64',8),f('child_pidfd_inode','u64',8),f('child_kernel_start_ticks','u64',8),f('qualification_id','uuid',16),f('incarnation_id','uuid',16),f('namespace_set_digest','bytes32',32)],
      'generation':[f('qualification_id','uuid',16),f('incarnation_id','uuid',16),f('epoch','uuid',16),f('participant_id','u16',2),f('generation_high_water','u64',8),f('current_generation_record_digest','bytes32',32)],
      'enrollment_identity':[f('bootstrap_context_digest','bytes32',32),f('participant_id','u16',2),f('parent_identity','bytes32',32),f('process_identity','bytes32',32),f('source_identity','bytes32',32),f('build_recipe_identity','bytes32',32),f('binary_module_identity','bytes32',32),f('dependency_set_identity','bytes32',32),f('loader_identity','bytes32',32),f('credential_identity','bytes32',32),f('channel_identity','bytes32',32)],
      'credential_identity':[f('credential_purpose','u16',2),f('participant_id','u16',2),f('generation','u64',8),f('bootstrap_context_digest','bytes32',32),f('credential_certificate_or_endpoint_manifest_digest','bytes32',32)],
      'authenticated_channel_identity':[f('channel_class','u16',2),f('bootstrap_context_digest','bytes32',32),f('creator_identity','bytes32',32),f('sender_birth_identity','bytes32',32),f('recipient_birth_identity','bytes32',32),f('socket_or_server_endpoint_manifest_digest','bytes32',32)],
      'registry_revision':[f('generation_registry_revision','u64',8),f('per_entity_work_revision_vector','work_revision_set','1..1048576'),f('independently_observed_tip_digest','bytes32',32)],
      'completed_work_identity':[f('context_digest','bytes32',32),f('participant_id','u16',2),f('generation','u64',8),f('challenge_id','bytes32',32),f('work_id','bytes32',32),f('input_digest','bytes32',32),f('result_digest','bytes32',32),f('independent_witness_digest','bytes32',32),f('publication_record_digest','bytes32',32)]}
    bootstrap_context_schema=[f('qualification_id','uuid',16),f('deployment_id','uuid',16),f('incarnation_id','uuid',16),f('boot_id','uuid',16),f('time_namespace_inode','u64',8),f('database_system_identifier','u64',8),f('database_oid','u32',4),f('binding_id','uuid',16),f('approval_manifest_id','uuid',16),f('manifest_v6_digest','bytes32',32),f('approval_manifest_digest','bytes32',32),f('binding_fingerprint','bytes32',32),f('policy_version','nfc_utf8','1..255'),f('policy_digest','bytes32',32),f('epoch','uuid',16),f('participant_id','u16',2),f('generation','u64',8)]
    doc('native-identity-codec',schemas=measurement_schemas,bootstrap_context_schema=bootstrap_context_schema,
       bootstrap_context_rule='SHA256 same typed domain frame with schema_name=bootstrap_context and exact declared fields; excludes all credential/channel/enrollment/work/registry-record digests. Registry record context_digest means this bootstrap context, not a digest of that record or final enrollment',
       construction_order=['approved raw source/build/loader/dependency file manifests','trusted generation high-water and bootstrap_context_digest','parent/process birth identities','credential identity independent of final enrollment','channel identity from creator/sender/recipient birth identities independent of final enrollments','final enrollment identity binds credential/channel/process and bootstrap context','post-enrollment message context','completed-work identity after independent publication'],
       no_recursive_hash='Socket inventory/certificates contain only primitive/birth/bootstrap identifiers before final enrollment. Final enrollments may subsequently be listed in activation records but are NOT hashed back into the channel or key identity. Dependency edges hash flat nodes, not recursive child-subtree identities',
       encoding='For each named schema: u32be ASCII domain byte length || exact domain FLOOOW/PACKAGE0090/R5N/IDENTITY/{schema_name}/V1 || u16be field count || contiguous tag u16be,length u32be,value in declared order; required/non-null exact widths, big-endian integer/UUID rules as native-message-abi. Digest=SHA256 complete frame; no normalization, default or unknown field',
       dependency_node_schema=[f('load_name','nfc_utf8','1..4096'),f('approved_absolute_path','nfc_utf8','1..4096'),f('link_and_resolved_inode_manifest_digest','bytes32',32),f('complete_file_sha256','bytes32',32)],
       dependency_edge_schema=[f('parent_node_digest','bytes32',32),f('load_name','nfc_utf8','1..4096'),f('resolved_child_digest','bytes32',32)],
       work_revision_schema=[f('participant_id','u16',2),f('generation','u64',8),f('work_id','bytes32',32),f('current_entity_revision','u64',8),f('current_record_digest','bytes32',32)],
       set_encoding='u32be count <=4096; each element u32be size + same tagged-field record under corresponding IDENTITY/{dependency_node|dependency_edge|work_revision}/V1 domain; sort complete element bytes unsigned lexicographically, reject duplicates; total frame<=1048576',
       source_and_recipe_manifest='Immutable approved manifest files use same typed domain framing, exact sorted path/byte-digest source entries and ordered explicit flags/toolchain identities; SHA256 of exact approved manifest bytes, not regenerated live observations. Unsupported dynamic dependency/source input rejects release acceptance',
       credential_purpose_enum={'GENERATION_TRANSPORT':1,'ONE_USE_WORK_AUTHORIZATION':2,'POSTMASTER_SERVER_ENDPOINT':3},channel_class_enum={'INHERITED_SEQPACKET':1,'POSTMASTER_NATIVE_PROBE_ENDPOINT':2},
       no_runtime_values_created=True,actual_values='All concrete implementations/builds/processes/keys/channels remain explicitly FUTURE_MEASURED; this codec only defines how to bind later values')
    doc('native-participants',source_denominator=ref(NATIVE,'/participants'),source_required_edges=AUTH['required_edges'],
       participants=rows,NATIVE_PARTICIPANTS_REQUIRED=7,GENERIC_PROCESS_SUBSTITUTIONS=0,
       source_hash_is_not_binary_hash=True,non_target_blockers_untouched=['V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES'])

def protocol():
    # The ABI is design data, not a native encoder/worker implementation.
    common=[f('qualification_id','uuid',16),f('deployment_id','uuid',16),f('incarnation_id','uuid',16),
      f('boot_id','uuid',16),f('time_namespace_inode','u64',8),f('database_system_identifier','u64',8),f('database_oid','u32',4),
      f('binding_id','uuid',16),f('approval_manifest_id','uuid',16),f('manifest_v6_digest','bytes32',32),
      f('approval_manifest_digest','bytes32',32),f('binding_fingerprint','bytes32',32),f('policy_version','nfc_utf8','1..255'),f('policy_digest','bytes32',32),
      f('epoch','uuid',16),f('participant_id','u16',2),f('parent_identity','bytes32',32),f('process_identity','bytes32',32),
      f('generation','u64',8),f('enrollment_identity','bytes32',32),f('channel_identity','bytes32',32),f('credential_ref','bytes32',32),
      f('generation_registry_revision','u64',8),f('work_entity_revision','u64',8),f('challenge_id','bytes32',32),f('work_id','bytes32',32),
      f('input_digest','bytes32',32),f('expected_result_schema_digest','bytes32',32),f('result_code','u16',2),f('result_digest','bytes32',32),
      f('previous_state_digest','bytes32',32),f('original_emission_boottime_us','u64',8),f('sequence','u64',8),
      f('sender_generation','u64',8),f('sender_enrollment','bytes32',32),f('sender_process_identity','bytes32',32),f('sender_credential_ref','bytes32',32)]
    encoding=dict(magic_hex='464c4f4f4f574e31',version=1,
      header='magic8 || version u16be || message_type u16be || sender_actor u16be || recipient_actor u16be || payload_length u32be',
      payload='field_count u16be; ascending contiguous fields: tag u16be || length u32be || exact typed value; no presence byte because every field is required/non-null',
      signature='64-byte Ed25519 signature over ASCII FLOOOW/PACKAGE0090/R5N/TEST/V1 followed by complete header+payload; fixed algorithm; expected key looked up by enrolled role/purpose/generation, never selected by caller credential_ref',
      integers='Unsigned fixed-width big-endian u16/u32/u64; signed i64 is exactly8-byte big-endian two-complement in range -2^63..2^63-1. Overflow/range violation rejects; sequence/generation/revisions checked before increment',
      uuid='16 network-order bytes, non-nil',text='Strict UTF8 NFC already normalized, no control/NUL/empty; reject rather than normalize',
      bytes='bytes32 and bytes64 exact raw length',
      arrays='u32be count then u32be element length and exact canonical typed element; sets sort full unsigned bytes and reject duplicates; bounded <=4096 entries',
      maximum_frame_bytes=1048576,unknown='Unknown version/type/field, missing/extra/duplicate/out-of-order tag, invalid width, truncation/MSG_TRUNC/MSG_CTRUNC, trailing bytes or excess ancillary => reject before work',
      nonresult='Challenge result_code=0 NOT_A_RESULT and result_digest=SHA256(ASCII FLOOOW/R5N/NO-RESULT/V1); never an observed outcome',
      result_codes={'NOT_A_RESULT':0,'OBSERVED_EXACT_WORK':1,'REJECTED':2,'UNKNOWN':3},
      time='Original CLOCK_BOOTTIME microseconds=floor(clock_gettime(CLOCK_BOOTTIME) nanoseconds/1000) in same boot_id/time namespace. server_start_epoch_us is signed finite PostgreSQL microseconds since2000-01-01T00:00:00Z, matching frozen PgStartTime/pg_stat_activity conversion, not Unix1970; reject PostgreSQL infinity sentinels. Approval signed-window wall time preserves original canonical UTC encoding and authoritative independently observed database clock; never compare it directly to BOOTTIME. Immutable policy gives finite positive max age, work deadline, key validity and heartbeat frame limits; numeric values remain independently approved provisioning data; time/nonce never authority',
      schema_JSON='For expected_result_schema_digest only: exact declared field-schema array with object keys sorted ASCII lexicographically, arrays in declared order, UTF8 bytes, no BOM/newline/whitespace. Allowed values are printable ASCII strings, booleans true/false and exact nonnegative integers<=9007199254740991; no null/float/nonfinite/negative/duplicate keys. Decimal integers no leading zeros; strings escape only quote and backslash, slash is unescaped. This restricted domain is exactly json.dumps(schema,sort_keys=True,separators=(comma,colon),ensure_ascii=False,allow_nan=False).encode(UTF8) for these schema objects. SHA256 those exact bytes; schema digest is design data, never binary identity')
    frames=[]
    for i,p in enumerate(ROSTER):
        for direction in ['CHALLENGE','RESPONSE']:
            frames.append(dict(id=p+'/'+direction,message_type=(100 if direction=='CHALLENGE' else 200)+i+1,
              participant=p,sender='HEALTH_GUARD' if direction=='CHALLENGE' else 'CENSUS_OBSERVER' if p=='POSTMASTER' else p,
              recipient=('CENSUS_OBSERVER' if p=='POSTMASTER' else p) if direction=='CHALLENGE' else 'HEALTH_GUARD',
              field_order=common+[f('input_record' if direction=='CHALLENGE' else 'result_record','typed_record','1..1048576')],
              body='Only the declared context/digests, never SQL/shell/command/path/PID/operation-selector payload',
              challenge_binding='Challenge key=(qualification,epoch,slot,generation,challenge_id,work_id); input digest and expected result schema precommitted by HEALTH_GUARD; nonce only uniqueness, never identity',
              currentness='Exact trusted generation/enrollment/credential/channel/context and expected generation-registry revision; work_entity_revision is participant-specific CAS predecessor, not a shared global work counter',
              outcome='Response OBSERVED_EXACT_WORK accepted only with independently observed role result and exact result_digest; self signature alone never counts',
              replay='Repeated identical request returns original retained terminal receipt without work, new signing, counter advance or expiry renewal; conflicting digest/consumed challenge/stale generation denies; UNKNOWN never retries work'))
    doc('native-message-abi',encoding=encoding,actor_enum={p:i+1 for i,p in enumerate(ACTORS)},frames=frames,
       no_NULL_fields=True,NONCE_IS_IDENTITY=False,TIME_IS_AUTHORITY=False,
       credential_use='Work authorization consumed once per challenge; bounded heartbeat authentication cannot sign a different work/slot/purpose; original canonical approval private key is NEVER held',
       channel='Creation inventory binds socketpair cookies/inodes, creator anchor and intended peer roles. SO_PEERPIDFD on inherited socket proves creation peer only. Each recvmsg requires exactly one current kernel SCM_PIDFD matching enrolled sender; no post-start SCM_RIGHTS/duplicate descriptors allowed',
       sender_vs_subject='participant_id/process_identity/parent_identity/generation identify the subject. Header sender plus sender_generation/enrollment/process/credential fields identify actual emitter and are checked against its own current trusted actor row and kernel SCM_PIDFD; challenge sender is HEALTH_GUARD, not subject. No process identity inferred from nonce',
       POSTMASTER_transport='POSTMASTER is the actual retained PG18 postmaster, not a generic worker/proxy. Its protocol is a challenged independently observed server-derived generation/catalog probe through TEST login bridge and narrow fixed read-only native observer sessions. CENSUS_OBSERVER emits type201 as a WITNESS about POSTMASTER with its own signer/process/generation fields, never a forged POSTMASTER signature. HEALTH_GUARD independently repeats the server/anchor observation before accepting. Native observer sessions never replace non-target final consumer sessions',
       input_record_schema=[f('fixed_input_digest','bytes32',32),f('expected_public_material_digest','bytes32',32),f('expected_target_digest','bytes32',32)],
       input_record_rule='Strict nested TLV record with exactly these3 tags. Every digest must equal the role-specific preassigned sealed challenge manifest: fixed spawn/enrollment/census scope, original public material for producer/consumer, and exact inherited fd6 target for enforcer; no caller selects target. For roles without public material, expected_public_material_digest is SHA256(ASCII FLOOOW/R5N/NO-PUBLIC-MATERIAL/V1), an explicit non-authority marker',
       nested_record_encoding='u16be field_count then contiguous tag u16be/length u32be/value, exact declared typed widths; no null/unknown/duplicate/reordered/trailing fields; context-bound domain FLOOOW/PACKAGE0090/R5N/{INPUT|RESULT}/{participant}/V1 is prepended as u32be byte length + exact ASCII domain',
       result_record_schemas={
        'POSTMASTER':[f('server_start_epoch_us','i64',8),f('database_oid','u32',4),f('header_digest','bytes32',32),f('role_roster_digest','bytes32',32),f('backend_birth_set_digest','bytes32',32),f('retained_postmaster_digest','bytes32',32),f('observer1_receipt','bytes32',32),f('observer2_receipt','bytes32',32)],
        'SUPERVISOR':[f('spawn_plan_digest','bytes32',32),f('retained_child_set_digest','bytes32',32),f('enrollment_receipt_set_digest','bytes32',32),f('dependency_validation_digest','bytes32',32)],
        'RECEIVER':[f('candidate_enrollment_digest','bytes32',32),f('scope_header_digest','bytes32',32),f('current_generation_revision','u64',8),f('promotion_receipt','bytes32',32),f('independent_witness','bytes32',32)],
        'CENSUS_OBSERVER':[f('snapshot_start_boottime_us','u64',8),f('snapshot_finish_boottime_us','u64',8),f('anchor_set_digest','bytes32',32),f('catalog_set_digest','bytes32',32),f('discrepancy_set_digest','bytes32',32),f('generation_revision','u64',8),f('independent_query_receipt','bytes32',32)],
        'APPROVAL_PRODUCER':[f('original_bundle_digest','bytes32',32),f('original_signature_digest','bytes32',32),f('original_spki_digest','bytes32',32),f('canonical_header_digest','bytes32',32),f('custody_status_digest','bytes32',32),f('verification_window_digest','bytes32',32),f('publication_receipt','bytes32',32)],
        'APPROVAL_CONSUMER':[f('producer_publication_digest','bytes32',32),f('independent_original_verification_digest','bytes32',32),f('consumption_receipt','bytes32',32),f('expected_generation_revision','u64',8)],
        'ENFORCEMENT_WORKER':[f('target_anchor_digest','bytes32',32),f('revocation_authorization','bytes32',32),f('signal_attempt_digest','bytes32',32),f('kernel_witness','bytes32',32),f('catalog_witness','bytes32',32),f('descendant_witness','bytes32',32),f('descriptor_witness','bytes32',32),f('outcome_publication_receipt','bytes32',32)]},
       error_result_schema=[f('reason_code','u16',2),f('last_expected_state_digest','bytes32',32),f('pending_subject_work_id','bytes32',32),f('error_detail_digest','bytes32',32)],
       error_reason_enum={'CONTEXT_MISMATCH':1,'CREDENTIAL_MISMATCH':2,'REPLAY':3,'EXPIRED':4,'STALE_GENERATION':5,'DEPENDENCY_UNKNOWN':6,'OUTCOME_UNKNOWN':7,'CORRUPT_STATE':8,'UNSUPPORTED':9,'CONFINEMENT_FAILURE':10},
       error_encoding='REJECTED/UNKNOWN result codes select the exact4-field error_result_schema under RESULT-ERROR/{participant}/V1 domain; never fabricate absent success/witness facts. last_expected_state_digest is authenticated challenge previous_state_digest, NOT an assertion of current/observed state. pending_subject_work_id is authenticated challenge base work ID. error_detail_digest=SHA256(ASCII FLOOOW/R5N/ERROR/V1 || reason_code u16be || last_expected_state_digest32 || pending_subject_work_id32); no secret/raw request/error text. If context cannot be authenticated at all, close/reject channel without signing a forged contextual response',
       result_record_rule='OBSERVED_EXACT_WORK selects participant success schema; REJECTED/UNKNOWN select the one fixed error schema by result_code, never a caller schema selector. result_digest=SHA256(exact canonical context-bound selected result_record bytes). expected_result_schema_digest ALWAYS remains the precommitted success-schema digest from the challenge, including error responses; error schema is fixed by protocol version/result_code and does not change base_subject_work_id or challenge binding. Receipt fields in success records reference prior ARTIFACT/OBSERVATION/CONSUMPTION records, NEVER their own final COMPLETED_WORK publication. HEALTH_GUARD checks independent facts; self signature/digest/receipt ID alone is insufficient. Error records never enter OBSERVED/PUBLISHED health states',
       signature_verification_is_not_functional_work=True)
    work={
      'POSTMASTER':dict(expected='Successful server-derived generation/catalog probe, as canonical native-proof-v6 PROGRESS_SOURCE requires',
        witness='Two distinct authenticated read-only native catalog observers obtain matching exact server-start/database/role/header snapshots, bind independent backend birth anchors from TEST login bridge and retained expected postmaster anchor, and check generation registry revision unchanged before/after. A generic backend SELECT or nonce alone is insufficient',
        input='Expected immutable full header/role/database/postmaster generation and exact read projection digest',result='Exact consistent generation/catalog snapshot digest + both independently authenticated observation receipts',
        source=ref(NATIVE,'/participants/0/COMPLETED_WORK_WITNESS')),
      'SUPERVISOR':dict(expected='Complete fixed bootstrap spawn/enrollment/dependency validation for exact planned seven slots',
        witness='HEALTH_GUARD independently compares child birth pidfds, executable/parent identities and current registry enrollment receipts to the sealed spawn plan; loop ticks excluded',
        input='Immutable seven-slot spawn plan and parent/dependency context',result='Exact retained child-set/enrollment/dependency digest',source=ref(N+'supervisor.c')),
      'RECEIVER':dict(expected='Complete one exact bound enrollment decision with all scope, peer and catalog checks',
        witness='HEALTH_GUARD independently revalidates challenged request, narrow read-only catalog witnesses and the authoritative promotion entity/revision after CAS, not receiver ACK',
        input='Full candidate enrollment identity and expected current generation/entity predecessor',result='Exact enrollment decision + independently current promotion receipt',source=ref(N+'receiver.c')),
      'CENSUS_OBSERVER':dict(expected='Complete applicable catalog/kernel/registry set reconciliation',
        witness='HEALTH_GUARD independently queries fixed native snapshot and compares complete retained anchor set and discrepancy set; generation/entity revisions must match before/after; pre-query tick excluded',
        input='Frozen enrolled anchor/phase/role/database set and revision vector',result='Exact matched-set/discrepancy digest with freshness and CAS applicability witnesses',source=ref(N+'observer.c')),
      'APPROVAL_PRODUCER':dict(expected='Publish fully verified immutable TEST approval generation derived from original public signed material',
        witness='APPROVAL_CONSUMER independently repeats original Ed25519/SPKI/preimage/manifest/custody/window/header verification; HEALTH_GUARD compares both published digests and current generation',
        input='Sealed original public bundle + independently approved public custody record, canonical manifest bytes and four core work receipts',result='Verified original-material/full-context digest + one-use TEST publication receipt; no canonical signing key',source=ref(N+'qualification.py')),
      'APPROVAL_CONSUMER':dict(expected='Consume one current verified producer publication after independent original-material verification',
        witness='HEALTH_GUARD independently reads immutable producer publication, consumer verification digest and committed native consumption entity at its current revision',
        input='Exact original public bundle, producer publication and current generation/entity predecessor',result='One-use CONSUMED receipt matching original material and current complete context',source=ref(N+'protocol.h')),
      'ENFORCEMENT_WORKER':dict(expected='Complete the fixed target-bound STOP/TERM/CONT action and obtain independent actual-outcome confirmation',
        witness='CENSUS_OBSERVER independently observes exact inherited target pidfd state, complete target descendant/descriptor custody and fixed catalog target absence; HEALTH_GUARD independently rereads witness/registry. Signal-send ACK alone insufficient',
        input='One preassigned TEST-only target birth-anchor fd6 and target identity, sealed qualification revocation authorization; no caller target or signal selection',result='Attempt digest + separate observed actual disposition/extinction evidence; any incomplete witness UNKNOWN',source=ref(N+'observer.c'))}
    doc('completed-work-protocol',participants=[dict(PARTICIPANT_ID=p,WORK_CHALLENGE=p+'/CHALLENGE',EXPECTED_FUNCTION=w['expected'],
       INPUT_CONTEXT=w['input'],EXPECTED_RESULT_CLASS=w['result'],RESULT_BINDING='Full ABI tuple + challenge/input/result/previous-state digests and exact generation/entity revisions',
       RESULT_WITNESS=w['witness'],INDEPENDENT_OBSERVER='HEALTH_GUARD, with role-specific distinct witness as stated',
       ONE_USE_PUBLICATION='Native completed-work entity CAS for this work_id, never generation-registry reset',REPLAY_REJECTION='Same original receipt only; no new work, renewed clock or changed revision',
       FAILURE_RESULT='REJECTED; deny native guard and latch quarantine when required',UNKNOWN_RESULT='Durable UNKNOWN, no approval/enforcement eligibility or replacement',SOURCE=w['source']) for p,w in work.items()],
       bootstrap_dependency_order=[['POSTMASTER','SUPERVISOR','RECEIVER','CENSUS_OBSERVER'],['APPROVAL_PRODUCER'],['APPROVAL_CONSUMER'],['ENFORCEMENT_WORKER']],
       no_circular_eligibility='Provisional participants may perform only fixed TEST qualification chores; no Package execution authority. Final health requires all seven. Core4 work precedes producer ARTIFACT publication; consumer first independently verifies that ARTIFACT and emits OBSERVATION before producer COMPLETED_WORK can finalize; consumer CONSUMPTION of exact artifact then finalizes its own work. Enforcer attempt obtains independent observation before its final work publication. No stage requires its own final completed-work receipt or own final healthy decision',
       no_global_revision_deadlock='Generation registry revision is frozen for a native qualification round; completed-work journal/entity revisions are separate. Publishing slot A does not stale unrelated slot B generation context; HEALTH_GUARD verifies each exact current work entity and same frozen generation vector before final decision',
       POSTMASTER_scope='Uses the exact successful server-derived generation/catalog probe class mandated by frozen canonical native source; does not claim arbitrary backend work proves all postmaster functions. Native health probe sessions NEVER substitute for the non-target final consumer session')

def modules_and_boundaries():
    abi=load(OUT.relative_to(ROOT).as_posix()+'/native-message-abi.json')
    mods=[]
    for p in ['APPROVAL_PRODUCER','APPROVAL_CONSUMER','ENFORCEMENT_WORKER']:
        frames=[x for x in abi['frames'] if x['participant']==p]
        mods.append(dict(MODULE_ID=actor(p)+'/TEST-ONLY-V1',PURPOSE=next(x['PROGRESS_SOURCE'] for x in AUTH['participants'] if x['PARTICIPANT_NAME']==p),
          PARENT='SUPERVISOR retained birth-anchor; HOST_PLATFORM independently witnesses exact child/parent before enrollment',
          START_AUTHORITY='HOST_PLATFORM pre-enrollment fixed bootstrap plan only; no operational spawn/exec API',
          INPUT_ABI=frames[0],OUTPUT_ABI=frames[1],MESSAGE_VERSION=1,MESSAGE_FIELD_ORDER=frames[0]['field_order'],
          FIELD_TYPES='Exact per-field type/length in INPUT_ABI; no additional fields',FIELD_LENGTHS='Exact per-field widths; UTF8 1..255; whole frame<=1048576',
          NULLABILITY='No field nullable; non-result uses explicit NOT_A_RESULT enum and fixed no-result digest, never absent design',
          CANONICAL_ENCODING=abi['encoding'],DOMAIN_SEPARATOR='FLOOOW/PACKAGE0090/R5N/TEST/V1',
          CONTEXT_BINDING='All ordered ABI subject/emitter fields and exact typed input/result record, including expected original public material, policy, manifest and binding fingerprint',
          GENERATION_BINDING='Exact current incarnation+slot+generation+enrollment; latest high-water never falls back',
          REGISTRY_REVISION_BINDING='Frozen current generation registry revision plus current participant work entity predecessor; both rechecked before CAS/guard',
          CHALLENGE_BINDING='HEALTH_GUARD-authenticated one-use challenge and work ID; expected input/result schema precommitted',
          COMPLETED_WORK_BINDING='completed-work-protocol.json exact participant rule, independent witness required',
          CREDENTIAL_TYPE='TEST-only slot/generation/purpose Ed25519 transport certificate plus one-use work authorization; original canonical SPKI verify-only',
          CREDENTIAL_SOURCE='HOST_PLATFORM approved private TEST key custody; CSPRNG at future provisioning, no provider/domain/execution secret reuse',
          CREDENTIAL_CUSTODY='Only exact process UID, sealed memfd4 then private non-dumpable memory; no shared signing API/FD transfer; zero private key returns/logs; expected public ref pinned independently',
          CREDENTIAL_USE_COUNT='At most one accepted work completion per signed work authorization; duplicate requests return same retained receipt, no second signature/effect. Heartbeat key purpose restricted and bounded by approved per-generation frame limit',
          CREDENTIAL_EXPIRY_RULE='Current generation/enrollment plus immutable approved native policy key-valid-until BOOTTIME in exact boot/timens; expiry/revoke/tombstone invalidates without renewal; no hardcoded experimental TTL',
          CHANNEL_TYPE='Inherited AF_UNIX SOCK_SEQPACKET fd5; no alternate socket/path/RPC endpoint',
          CHANNEL_AUTHENTICATION=abi['channel'],PEER_IDENTITY_RULE='Signed bootstrap inventory creator identity + kernel CURRENT sender anchor + exact enum/credential/context equality',
          REPLAY_REJECTION=frames[0]['replay'],STALE_GENERATION_REJECTION='Exact latest authoritative current slot generation; old signed receipts cannot restore it',
          WRONG_PARENT_REJECTION='Compare retained expected parent tuple, no name/PID-only match',WRONG_BINARY_REJECTION='Compare approved executable+module+loader+dependency manifest actual measured identity before enrollment/publication',
          WRONG_CHANNEL_REJECTION='Reject transfer/creator/current-sender/namespace/inventory mismatch',WRONG_CONTEXT_REJECTION='Reject any mismatch in fixed expected ABI tuple, including original signed bundle/custody',
          UNKNOWN_BEHAVIOR='Persist exact pending work/operation tuple and quarantine; no blind retry/replacement/eligibility',
          REVOCATION_BEHAVIOR='Irreversible generation/credential/channel ineligibility and tombstone; keep retained evidence until independent extinction',
          CRASH_BEHAVIOR='Crash/ACK loss yields UNKNOWN unless independent exact outcome already durable; never treat process death as abort/extinction',
          OUTPUT_WITNESS='HEALTH_GUARD independent result check; ENFORCEMENT_WORKER additionally requires CENSUS_OBSERVER actual outcome, not worker signature',
          INDEPENDENT_OBSERVER='HEALTH_GUARD observed by HOST_PLATFORM; producer verification separately repeated by APPROVAL_CONSUMER',
          MODULE_IMPLEMENTED=False,SQL_TEXT_INPUT_ALLOWED=False,GENERIC_OPERATION_SELECTOR=False))
    doc('three-test-only-module-contracts',modules=mods,
       original_approval='Producer and consumer repeat frozen _observer_once public-material verification: exact independent custody status/bundle, SPKI DER/fingerprint, canonical manifest hash, exact canonical signature preimage and original Ed25519 signature, current signed window and independently fetched exact header/lifecycle. TEST transport signatures never replace original approval evidence',
       native_enforcement='Only one prebound target fd6 and fixed STOP_THEN_TERM_THEN_CONT; no PID, signal, path, SQL or shell selector; lost syscall/commit result UNKNOWN and never reexecuted',
       separate_outcome_witness=True)
    profiles=[]
    common_calls=['read','pread64','write','sendmsg','recvmsg','ppoll','poll','clock_gettime','fstat','newfstatat','fcntl','close','rt_sigaction','rt_sigprocmask','rt_sigreturn','futex','brk','mmap','munmap','madvise','getpid','gettid','getrandom','exit','exit_group']
    for p in ROSTER:
        profiles.append(dict(participant=p,phase_model=['TRUSTED_BOOTSTRAP','CONFINED_PRE_ENROLLMENT','ENROLLED','REVOKED'],
          uid='Unique TEST native slot UID except PostgreSQL engine children inherently share its private DB-service UID; no participant receives another slot key or writable memory',
          filesystem='Immutable private code/libs/config mount; no writable executable/plugin paths. Only native registry writer auxiliary owns its fixed journal append FD; participant inputs read from sealed descriptors, outputs through exact authenticated fd5',
          capabilities='Drop all Linux capabilities before enrollment; enforcer may retain only CAP_KILL in disposable TEST user/PID namespace, under exact fd6 signal filter. No SYS_ADMIN/SYS_PTRACE/SETUID/SETGID/NET_ADMIN operational capability',
          bootstrap='Only HOST_PLATFORM can create namespace/UID/mount/capability policy and approve release; SUPERVISOR fixed bootstrap spawn is PRE_ENROLLMENT only, loses spawn/exec/UID authority before active. Replacement requires old generation drain and a new bootstrap phase, never active generic spawner',
          calls=(['PostgreSQL18-engine-private-OS-service-policy'] if p=='POSTMASTER' else common_calls+(['pidfd_send_signal'] if p=='ENFORCEMENT_WORKER' else [])),
          argument_rules='Non-engine role IO only declared descriptors; fcntl only F_GETFD/F_GETFL/F_GET_SEALS, no dup/replacement. Anonymous mmap RW only, no writable executable mappings; allocator syscalls bounded by sealed memory quota. recvmsg fd5 only with strict ancillary checks; close only owned temporary validation handles, never protected target fd6',
          signal_rules='Only enforcer fd6 may receive SIGSTOP,SIGTERM,SIGCONT in fixed order once; deny kill/tkill/tgkill, pidfd_open/getfd, arbitrary FD creation/replacement, exec, ptrace/process_vm_writev. Any rejected syscall quarantines and outcome UNKNOWN',
          POSTMASTER_boundary='PostgreSQL engine remains the explicit frozen service/trusted implementation, not a generic native worker/broker: private TEST PGDATA and socket namespace only, approved engine/modules immutable, no host/prod mount/network/credential; only exact preprovisioned non-superuser native observer roles may reach read-only TEST snapshot function. No native message carries SQL. Full database mutation mechanism closure remains V2-PARTITIONS outside this gate' if p=='POSTMASTER' else 'NOT_APPLICABLE_ENGINE_BOUNDARY',
          unresolved='Engine OS-service policy and complete libc/OpenSSL syscall allowlist + argument-filter source-to-effect verification still require independent review; a proposed list alone is not proof',
          expected_policy_artifact=future('enforcement_policy','HOST_PLATFORM approved future implementation/build custody',
             'Exact declared role syscall/descriptor/namespace policy plus architecture ABI definitions and immutable module source',
             'Generate deterministic architecture-specific seccomp/LSM policy, offline validate every rule and default-deny coverage; hash exact policy bytes before approve/enroll',
             'expected confinement manifest','HOST_PLATFORM + HEALTH_GUARD attested installed policy digest')))
    doc('native-isolation-custody',profiles=profiles,distinct_actor_pairs=[['APPROVAL_PRODUCER','APPROVAL_CONSUMER'],['APPROVAL_CONSUMER','ENFORCEMENT_WORKER'],['ENFORCEMENT_WORKER','CENSUS_OBSERVER'],['NATIVE_REGISTRY_WRITER','HEALTH_GUARD'],['HEALTH_GUARD','HOST_PLATFORM']],
       fixed_descriptor_inventory={'3':'sealed expected context/policy/release manifest (all native modules)',
         '4':'slot/generation TEST transport key sealed memfd, import once then close; private memory never transferred',
         '5':'unique HEALTH_GUARD authenticated channel',
         '6':'enforcer preassigned target pidfd; CENSUS_OBSERVER separate read-only retained handle to same target, no signal permission',
         '7':'producer/consumer sealed original public bundle and custody/status record',
         '8':'producer/consumer original SPKI DER public bytes',
         '9':'producer/consumer original signature preimage bytes',
         '10':'producer/consumer original public signature bytes',
         '11':'producer/consumer canonical manifest bytes',
         '12':'receiver/census fixed TEST observer SQL connection, exact native read-only identity; no SQL selector in module ABI',
         '16':'read-only native registry journal; writer auxiliary has separate append/lock descriptors not held by participants'},
       credential_private_bytes_never_shared=True,HOST_PLATFORM_source=ref(NATIVE,'/HOST_PLATFORM'),
       trusted_root_is_not_capability='HOST_PLATFORM assumption is explicit and independently denies health on loss; no health participant can invoke arbitrary root/superuser/CREATEROLE actions',
       observer_isolation='Separate UID/key/process/namespace and read-only expected manifests/journal; no mutation/signing key co-holder; root compromise remains explicit canonical HOST_PLATFORM threat boundary, not silently proven safe')
    doc('catalog-witness-boundary',source_queries=[ref(N+'receiver.c'),ref(N+'observer.c')],source_hooks=[ref(N+'login.c')],
       native_probe_scope='Native generation/catalog probing ONLY, never non-target final consumer before/after settings',
       proposed_TEST_snapshot_endpoint='test_0090_native.observe_exact_context(pg_catalog.bytea) RETURNS pg_catalog.bytea, one immutable fixed source-derived read-only projection; not created or executed',
       API='Input exact full R5N context bytes checked against independently provisioned binding/enrollment and session_user OID/name; no table/column/SQL/PID selectors. Derive row roster from protected expected context, not caller values; return exact typed bounded snapshot and no credentials/private keys/query text',
       ACL='Dedicated per-observer SQL LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS, zero memberships; exact private TEST function EXECUTE only, no raw Package table/grant/signing access, no schema CREATE/default PUBLIC privilege. Local peer auth maps exact manifest OS UID; no postgres client secret held by any participant',
       definer_boundary='Proposed immutable qualified TEST-only SECURITY DEFINER snapshot body, fixed search_path pg_catalog,pg_temp, trusted TEST installation owner; no dynamic SQL/DML/role/system/file/signal calls, no caller identifier/operation selector. Admin creates it only in later authorized TEST fixture, never V043/canonical/shared DB',
       body_identity='Future reviewed exact AST/body copied from frozen bound catalog/census read predicates and exact output schema; byte/body/owner/ACL/default identity must be approved before any execution',
       independent_witness='HEALTH_GUARD and CENSUS_OBSERVER have distinct exact observer SQL identities/connections/keys, compare independently returned fixed snapshot and retained backend/postmaster anchors; helper SQL sessions only prove native probe facts',
       residual_static_boundary='Frozen source uses postgres helper connections and lacks exact future snapshot helper AST, typed output/caller roster and engine privilege/filter closure. This cannot be closed solely by naming a future helper or marking its hash FUTURE_MEASURED; reviewer must preserve genuine design gap if unresolved')

def registry():
    common=[f('qualification_id','uuid',16),f('incarnation_id','uuid',16),f('epoch','uuid',16),f('slot','u16',2),
      f('generation','u64',8),f('generation_registry_revision','u64',8),f('entity_revision','u64',8),
      f('previous_entity_digest','bytes32',32),f('record_sequence','u64',8),f('previous_journal_digest','bytes32',32),f('context_digest','bytes32',32)]
    definitions={
     'PARTICIPANT_REGISTRY':([f('process_identity','bytes32',32),f('parent_identity','bytes32',32),f('enrollment_identity','bytes32',32),f('credential_ref','bytes32',32),f('channel_identity','bytes32',32),f('state','u16',2)],['qualification_id','incarnation_id','epoch','slot','generation']),
     'GENERATION_LEDGER':([f('high_water_generation','u64',8),f('prior_tombstone_digest','bytes32',32),f('state','u16',2)],['qualification_id','incarnation_id','epoch','slot']),
     'GENERATION_TOMBSTONE':([f('retired_generation','u64',8),f('retired_enrollment','bytes32',32),f('revocation_digest','bytes32',32),f('extinction_receipt','bytes32',32),f('outcome_state','u16',2)],['qualification_id','incarnation_id','epoch','slot','retired_generation']),
     'COMPLETED_WORK_PUBLICATION':([f('publication_purpose','u16',2),f('related_subject_work_id','bytes32',32),f('enrollment_identity','bytes32',32),f('work_id','bytes32',32),f('challenge_id','bytes32',32),f('input_digest','bytes32',32),f('result_digest','bytes32',32),f('observer_receipt','bytes32',32),f('state','u16',2)],['qualification_id','incarnation_id','epoch','slot','generation','work_id'])}
    records=[]
    for i,(name,(fields,key)) in enumerate(definitions.items()):
        records.append(dict(type=name,record_type=i+1,version=1,canonical_tuple=common+fields,primary_identity=key,
          writer='NATIVE_REGISTRY_WRITER',observer='HEALTH_GUARD; HOST_PLATFORM independently observes guard and expected journal',
          credential='Native writer generation/purpose key, no participant co-holder',
          CAS_expected='Exact current verified journal tip/sequence AND entity key/revision/predecessor AND current generation high-water AND legal state edge; duplicate operation key never resets logical entity',
          CAS_next='Append journal_sequence+1/entity_revision+1 checked; update derived entity index only after fsync and independent witness; generation ledger increments only on authorized new generation, work publication never changes generation revision',
          monotonicity='No decreasing high-water/revision or deleted tombstone; incomplete/corrupt/unavailable latest row is UNKNOWN, never earlier generation fallback',
          one_use='Each challenge/work_id consumes at most one exact generation input/result/publication; duplicate same bytes returns original receipt, no work; conflicting bytes denies',
          replacement='Old enrollment revoked, pending UNKNOWN reconciled, old endpoint extinction independently proved, irreversible tombstone durable, checked new generation previous+1 before new enrollment',
          restart='Retain original pending/current high-water and tombstones; new process instance cannot adopt old enrollment/key/work; unclear continuity requires new isolated incarnation under separate trusted provisioning',
          reconnect='Retire old channel identity, preserve pending UNKNOWN; no new channel enrollment or work while unresolved',
          revocation='Monotonic invalidation before new eligibility; every old receipt/credential/channel remains ineligible',
          tombstone='Retired slot/generation remains irreversible even if newer process dies or registry lookup fails',
          stale_generation='Any supplied generation != independently current high-water/current entity denies; never search older signed rows as fallback',
          publication_receipt='Writer signature + exact record/journal/entity digest and revision + independent HEALTH_GUARD observed tip receipt, full R5N context',
          corruption='Bad encoding/signature/hash/predecessor/revision/duplicate entity/partial tail/missing tip => quarantine + UNKNOWN; no truncate-to-success/abort',
          UNKNOWN='Durable pending tuple survives crash and channel/process loss; no new eligibility, generation or blind replay until independent exact reconciliation'))
    doc('native-registry-generation',records=records,
      encoding='magic8 FLOOOWN1 || version u16be=1 || type u16be=(300+record_type) || sender u16be=NATIVE_REGISTRY_WRITER actor enum || recipient u16be=HEALTH_GUARD actor enum || payload_length u32be || typed TLV payload (u16be field count, contiguous tag u16be,length u32be,value) || Ed25519 signature64 over ASCII FLOOOW/PACKAGE0090/R5N/REGISTRY/V1 + complete preceding frame. Journal envelope=u32be frame length || frame || SHA256(frame). Exact record schema only; unknown/reordered/extra/truncated/trailing/null reject',
      state_enums={'PARTICIPANT_REGISTRY':{'PROVISIONAL':1,'ENROLLED':2,'REVOKED':3,'EXTINCT':4,'UNKNOWN':255},
        'GENERATION_LEDGER':{'CURRENT':1,'REVOKED':2,'TOMBSTONED':3,'NEW_GENERATION':4,'UNKNOWN':255},
        'GENERATION_TOMBSTONE':{'REVOKED_PENDING_EXTINCTION':1,'EXTINCT_PROVEN':2,'UNKNOWN':255},
        'COMPLETED_WORK_PUBLICATION':{'RESERVED':1,'WORK_PENDING':2,'OBSERVED':3,'PUBLISHED':4,'UNKNOWN':255,'OBSERVED_PROVEN':5,'CONSUMED':6,'PUBLISHED_UNVERIFIED_ARTIFACT':7}},
      publication_purpose_enum={'ARTIFACT':1,'OBSERVATION':2,'CONSUMPTION':3,'COMPLETED_WORK':4},
      base_subject_work_id_encoding='ABI work_id (base_subject_work_id)=SHA256(ASCII FLOOOW/PACKAGE0090/R5N/SUBJECT-WORK/V1 || bootstrap_context_digest32 || participant_id u16be || challenge_id32 || fixed_input_digest32 || expected_success_result_schema_digest32). Every suffix has exact stated width; ASCII prefix fixed, no NUL. Input/schema digests are precommitted before work and exclude final publication/result digests',
      purpose_work_id_encoding='Record work_id=SHA256(u32be domain byte length || exact ASCII FLOOOW/PACKAGE0090/R5N/WORK-ID/{purpose}/V1 || bootstrap_context_digest32 || related_subject_work_id32 || challenge_id32). purpose is exact uppercase ASCII enum name ARTIFACT/OBSERVATION/CONSUMPTION/COMPLETED_WORK, never numeric/string-coerced. related_subject_work_id MUST equal the base_subject_work_id of the observed subject; record publication_purpose u16be MUST match that purpose enum. Recompute and reject mismatch; no caller-chosen hashing/type order',
      publication_receipt_DAG='Each record-purpose work_id uses the exact independent purpose_work_id_encoding; distinct purposes have distinct entities. ARTIFACT result digest hashes original public material/full context, not its own receipt. OBSERVATION hashes prior artifact/attempt+observer evidence. CONSUMPTION hashes prior artifact+observation and exact one-use CAS. Only then COMPLETED_WORK hashes role result record containing those prior receipt digests. No result hashes its own final receipt or depends on a later DAG node',
      publication_rights='Only HEALTH_GUARD submits fixed validated record schemas to native writer. ARTIFACT must carry producer evidence; OBSERVATION requires distinct current consumer/census/guard witness as appropriate; CONSUMPTION only consumer + exact artifact one-use CAS; COMPLETED_WORK only after role-specific independent observation. Purpose is derived from fixed stage/message route, never arbitrary module operation selector',
      artifact_non_authority='ARTIFACT may publish as PUBLISHED_UNVERIFIED_ARTIFACT before consumer verification; observer_receipt is SHA256(ASCII FLOOOW/R5N/OBSERVATION-PENDING/V1), explicitly NOT_A_PROOF. Such records never satisfy native health. Independent consumer OBSERVATION upgrades exact artifact to PUBLISHED; one CONSUMPTION changes only that artifact to CONSUMED. Final COMPLETED_WORK is a separate entity and remains PUBLISHED for guard validation',
      pending_markers='Pending extinction_receipt=SHA256(ASCII FLOOOW/R5N/EXTINCTION-PENDING/V1), never EXTINCT evidence. First prior_tombstone/previous_entity_digest use context-bound native GENESIS digest; allowed only for independently approved NEW qualification, never inferred from unavailable history. Every marker is explicit NOT_A_PROOF, never zero/default authority',
      native_journal='One private native-only append journal; single writer owns exact inherited append FD and exclusive lock, observer receives separate read-only FD; no caller path/file/type selector. All four schemas fixed; not the global epoch ledger contract',
      durability='Append full frame; fsync journal and directory for creation; independent observer reread matching tip before any eligibility. Crash/torn tail/ACK loss UNKNOWN; never rewrite or infer rollback',
      genesis='SHA256(canonical domain FLOOOW/PACKAGE0090/R5N/GENESIS/V1 with qualification/incarnation/epoch/policy/manifest digest); approved new isolated genesis only, never inferred from missing old rows',
      dependency_rule='Generation registry and per-work publication entities have separate revision domains. Publish does not alter generation registry; guard validates current per-entity publication vector and identical generation/context/dependency vector immediately before native decision',
      no_bootstrap_cycle='Provisional native qualification chores are not Package authority. Only fixed native work, original public-material verification and preassigned TEST target control are eligible; final healthy output requires all seven independently observed current receipts',
      state_edges={'PARTICIPANT_REGISTRY':[['PROVISIONAL','ENROLLED'],['ENROLLED','REVOKED'],['REVOKED','EXTINCT']],
        'COMPLETED_WORK_PUBLICATION':[['RESERVED','WORK_PENDING'],['WORK_PENDING','OBSERVED'],['OBSERVED','PUBLISHED'],['WORK_PENDING','UNKNOWN'],['UNKNOWN','OBSERVED_PROVEN'],['OBSERVED_PROVEN','PUBLISHED'],['RESERVED','PUBLISHED_UNVERIFIED_ARTIFACT'],['PUBLISHED_UNVERIFIED_ARTIFACT','PUBLISHED'],['PUBLISHED','CONSUMED']],
        'GENERATION_LEDGER':[['CURRENT','REVOKED'],['REVOKED','TOMBSTONED'],['TOMBSTONED','NEW_GENERATION']],
        'GENERATION_TOMBSTONE':[['REVOKED_PENDING_EXTINCTION','EXTINCT_PROVEN']]},
      UNKNOWN_resolution='UNKNOWN->OBSERVED_PROVEN requires distinct independent exact outcome evidence; never participant success boolean or timeout; no retry of side effect')

def attacks_and_decision():
    attacks=['wrong_binary','wrong_module','wrong_dependency','wrong_loader','wrong_parent','wrong_process_instance','wrong_generation','stale_generation','wrong_enrollment','wrong_credential','reused_credential','wrong_channel','transferred_channel','replayed_challenge','replayed_response','replayed_completed_work_receipt','stale_registry_revision','registry_rollback','tombstoned_generation','restart_substitution','reconnect_substitution','participant_role_substitution','producer_consumer_substitution','observer_writer_substitution']
    rows=[]
    for p in ROSTER:
        for attack in attacks:
            rows.append(dict(id=p+'/'+attack,participant=p,attack=attack,
              expected='UNKNOWN_FAIL_CLOSED' if attack in ['restart_substitution','reconnect_substitution'] else 'REJECT',
              exact_predicate=dict(wrong_binary='measured executable digest == approved expected binary digest',wrong_module='measured module digest == approved expected module digest',
               wrong_dependency='closed measured dependency graph == approved expected dependency graph',wrong_loader='measured loader/interpreter map == approved manifest',
               wrong_parent='retained parent tuple == trusted expected parent',wrong_process_instance='current kernel sender birth anchor == enrolled process tuple',
               wrong_generation='supplied generation == latest current generation high-water',stale_generation='supplied generation == latest current generation high-water',
               wrong_enrollment='message enrollment digest == exact current enrollment entity',wrong_credential='message credential ref == trusted expected role/purpose/generation key and signature valid',
               reused_credential='one-use work authorization not consumed; identical terminal duplicate is read-only receipt replay',wrong_channel='channel creation inventory and current sender/recipient == exact enrollment',
               transferred_channel='current kernel sender birth-anchor == enrolled sender, even if socket inherited/transferred',replayed_challenge='challenge/work authorization unused and sequence strictly increasing',
               replayed_response='work input/result/one-use state exactly current, otherwise deny or original receipt only',replayed_completed_work_receipt='receipt entity/revision/generation/context == exact current published entity, never new work',
               stale_registry_revision='generation revision and per-work predecessor/current entity == exact expected current revision',registry_rollback='current verified journal high-water/tip never lower than durable independently held tip',
               tombstoned_generation='generation absent from irreversible retired-generation set',restart_substitution='new birth anchor never inherits pending/current enrollment; UNKNOWN requires reconciliation',
               reconnect_substitution='new channel cannot enroll while old pending UNKNOWN remains',participant_role_substitution='participant enum/message type/expected slot == exact trusted role',
               producer_consumer_substitution='producer,consumer,enforcer and guard have distinct keys/anchors/UIDs and purpose-specific accepted types',observer_writer_substitution='work/registry subject writer identity != independently trusted observer identity')[attack],
              SOURCE_PROOF=ref(NATIVE,'/participants/'+str(ROSTER.index(p))),
              evidence_level='STATIC_CONTRACT_CASE_NOT_RUNTIME_ATTACK',native_module_executed=False))
    doc('native-substitution-matrix',cases=rows,participants=7,attack_kinds=24,total=168,
       static_test_meaning='Deterministic required rejection/UNKNOWN predicate; independent reviewer must check whether confinement and witnesses actually make it enforceable. Table presence alone is not proof',
       UNKNOWN_never_TRUE=True)
    doc('native-independence-model',required_edges=AUTH['required_edges'],source=ref(NATIVE,'/required_edges'),
      actors=ACTORS,role_separation=[['APPROVAL_PRODUCER','APPROVAL_CONSUMER'],['APPROVAL_CONSUMER','ENFORCEMENT_WORKER'],['ENFORCEMENT_WORKER','CENSUS_OBSERVER'],['NATIVE_REGISTRY_WRITER','HEALTH_GUARD'],['HEALTH_GUARD','HOST_PLATFORM']],
      phase_separation='Trusted HOST_PLATFORM bootstrap is explicit pre-enrollment root assumption, not an operational capability. SUPERVISOR drops bootstrap powers before active; no generic root/SQL/shell/CREATEROLE entrypoint',
      guard_function='HEALTH_GUARD independently checks each current published native-work entity plus identical context/generation/dependency vector; HOST_PLATFORM independently observes guard identity/channel/generation/work and recomputes required native health facts from signed inputs',
      native_fact_not_execution_authority=True,non_target_gates_not_closed=True,
      STATIC_DESIGN_PROOF='PROPOSED_REQUIRED_RULES_REVIEW_PENDING',IMPLEMENTATION_PROOF_PENDING=True,BUILD_PROOF_PENDING=True,RUNTIME_PROOF_PENDING=True)
    save('NATIVE-GATE.json',dict(BRANCH=BRANCH,BASELINE_HEAD=BASE,R5_DESIGN_FAILURES_TOTAL=497,R5_NATIVE_FAILURES=7,R5_NATIVE_ROOT_CAUSES=3,
      R5_NATIVE_DUPLICATE_OR_DERIVED_FAILURES=7,R5_NATIVE_FUTURE_IMPLEMENTATION_EVIDENCE=0,R5_NATIVE_FUTURE_BUILD_EVIDENCE=0,R5_NATIVE_FUTURE_RUNTIME_EVIDENCE=0,
      R5_NATIVE_TRUE_STATIC_DESIGN_FAILURES_REMAINING=3,NATIVE_PARTICIPANTS_REQUIRED=7,NATIVE_PARTICIPANTS_FULLY_DESIGNED=0,UNRESOLVED_NATIVE_WORK_ANCHORS=7,GENERIC_PROCESS_SUBSTITUTIONS=0,
      NATIVE_MESSAGE_ABI_COMPLETE='REVIEW_PENDING',NATIVE_GENERATION_PROTOCOL_COMPLETE='REVIEW_PENDING',NATIVE_REGISTRY_PROTOCOL_COMPLETE='REVIEW_PENDING',NATIVE_COMPLETED_WORK_PROTOCOL_COMPLETE='REVIEW_PENDING',NATIVE_INDEPENDENCE_MODEL_COMPLETE='REVIEW_PENDING',NATIVE_CUSTODY_MODEL_COMPLETE='REVIEW_PENDING',NATIVE_SUBSTITUTION_MATRIX_COMPLETE='REVIEW_PENDING',
      IMPLEMENTATION_PERFORMED='NO',NATIVE_BUILD_PERFORMED='NO',NATIVE_RUNTIME_EXECUTED='NO',SQL_EXECUTED='NO',DATABASE_CONTACTED='NO',V043_EXECUTED='NO',B02_EXECUTED='NO',
      NATIVE_INDEPENDENT_REVIEW='PENDING',V2_NATIVE_STATUS='BLOCKED',BLOCKER_COUNT_FOR_V2_NATIVE=1,
      RESIDUAL_NATIVE_BLOCKERS=['Independent review of exact native isolation/catalog-work/publication rules pending; never infer closure from populated fields'],
      NON_TARGET_BLOCKERS_UNCHANGED=['V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES'],NEXT_EXECUTED=False,
      NEXT_GATE='INDEPENDENT_NATIVE_DESIGN_REVIEW_NO_LIVE_EXECUTION'))

def generate():
    freeze();audit();identities();protocol();modules_and_boundaries();registry();attacks_and_decision()
    print(json.dumps(dict(generated=True,participants=len(ROSTER),audited_failures=497,native_primary_failures=7,non_target_unchanged=490,live_executed=False)))
