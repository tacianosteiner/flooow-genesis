"""R5N.1 offline design-data derivation. No SQL/native/build/network calls."""
import sys
sys.dont_write_bytecode=True
import hashlib,itertools,json,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
BASE='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb';BRANCH='checkpoint/package-0090-cloud-handoff'
RN='docs/evidence/package-0090-B01-v2-native-static-closure-r5n/'
R5='docs/evidence/package-0090-B01-v2-static-closure-revision-5/'
SRC='docs/evidence/package-0090-full-reachable-expectation-closure-v2/'
PG=SRC+'provider/';N='scripts/validation/package_0090_native_health_qualification/'
REPORT='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n1.md'
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def save(n,x):(OUT/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def doc(n,**kw):save(n+'.json',dict(scope='R5N1_NATIVE_STATIC_DESIGN_ONLY',implementation_authorized=False,runtime_proven=False,**kw))
def ref(p,ptr='/'):return dict(path=p,sha256=sha((ROOT/p).read_bytes()),pointer=ptr)
def op(name,*args):return dict(op=name,args=list(args))
def field(n,t,nullable=False):return dict(name=n,type=t,nullable=nullable)

def freeze_and_account():
    global P,BEFORE
    assert git('branch','--show-current').decode().strip()==BRANCH and git('rev-parse','HEAD').decode().strip()==BASE
    assert git('rev-parse','origin/'+BRANCH).decode().strip()==BASE
    assert git('diff','--name-only')==git('diff','--cached','--name-only')==b''
    f=read(RN+'baseline-freeze.json');prior=dict(f['source_checkout_sha256'])
    BEFORE=[p for p in git('ls-files','--others','--exclude-standard').decode().splitlines() if p.startswith((RN,R5)) or p in ['docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n.md','docs/evidence/PACKAGE-0090-B01-v2-static-closure-revision-5.md']]
    assert len(BEFORE)==72
    for p in BEFORE:prior[p]=sha((ROOT/p).read_bytes())
    for p in BEFORE:
        if p.endswith('.json'):read(p)
        else:(ROOT/p).read_bytes()
    for prefix in (R5,RN):
        m=read(prefix+'SHA256-MANIFEST.json')
        for p,h in m['files'].items():
            b=(ROOT/p).read_bytes();b=b.replace(b'\r\n',b'\n') if p.endswith('.md') else b
            assert sha(b)==h,p
    P=[x['PARTICIPANT_ID'] for x in read(RN+'native-participants.json')['participants']]
    save('baseline-freeze.json',dict(branch=BRANCH,baseline_head=BASE,remote_tracking_head=BASE,tracked_dirty_before=0,staged_before=0,
       untracked_before=72,untracked_before_paths=sorted(BEFORE),unauthorized_before=[],remote_authority='existing remote tracking ref; no network refresh',
       source_checkout_sha256=dict(sorted(prior.items())),source_Git_LF_sha256=f['source_Git_LF_sha256'],old_manifests_verified=['R5','R5N'],
       CURRENT_V043_GIT_LF_SHA256=f['CURRENT_V043_GIT_LF_SHA256'],FLYWAY_SIGNED_CRC32=f['FLYWAY_SIGNED_CRC32'],V043_FENCE_PRESENT=True,
       noncontact_basis='Prior immutable negative records and no live commands this tranche; no forensic claim over unobserved actors'))
    review=read(RN+'independent-native-review.json');roots=review['root_cause_verdicts']
    assert len(roots)==3 and sum(not r['closed'] for r in roots)==2
    doc('root-cause-accounting',original_roots=[dict(original_index=i+1,family=r['family_id'],
       classification='CLOSED_BY_R5N' if r['closed'] else 'STILL_OPEN',evidence=ref(RN+'independent-native-review.json','/root_cause_verdicts/'+str(i)),
       exact_previous_verdict=r) for i,r in enumerate(roots)],
       R5_NATIVE_ROOT_CAUSES_ORIGINAL=3,R5N_CLOSED_ROOTS=1,R5N_OPEN_ROOTS=2,arithmetic='3 original proof families - 1 independently closed publication/generation family = 2 remaining; no merged/deleted root',
       historical_failure_audit=ref(RN+'failure-audit.json'),non_target_failures_unchanged=490)
    # Carry closed protocol bytes unchanged into this tranche, including their source identity.
    preserved={}
    for name in ['native-message-abi.json','native-registry-generation.json','native-identity-codec.json']:
        b=(ROOT/RN/name).read_bytes();(OUT/('preserved-'+name)).write_bytes(b);preserved[name]=sha(b)
    doc('closed-protocol-freeze',source=RN,files=preserved,ABI_REDESIGNED=False,GENERATION_REDESIGNED=False,REGISTRY_REDESIGNED=False,
       contradiction_policy='Any actual contradiction reopens the corresponding proof; copied bytes alone not new runtime evidence')

def isolation():
    # The rule IR is a policy specification, never a filter/LSM implementation.
    common='read pread64 write sendmsg recvmsg poll ppoll clock_gettime fstat newfstatat fcntl close rt_sigaction rt_sigprocmask rt_sigreturn futex brk mmap munmap madvise getpid gettid getrandom exit exit_group'.split()
    pgextra='readv writev pwrite64 lseek fsync fdatasync ftruncate openat readlinkat getdents64 renameat renameat2 unlinkat mkdirat fchmod fchown umask fcntl pipe2 socket bind listen accept4 connect shutdown getsockopt setsockopt recvfrom sendto epoll_create1 epoll_ctl epoll_wait wait4 waitid clone fork getppid getuid geteuid getgid getegid getgroups getrlimit prlimit64 sched_getaffinity sched_yield clock_nanosleep nanosleep gettimeofday uname statfs fstatfs semget semctl semop semtimedop shmget shmat shmdt shmctl mprotect msync dup dup2 dup3'.split()
    forbidden='execve execveat ptrace process_vm_writev process_vm_readv pidfd_open pidfd_getfd kill tkill tgkill bpf perf_event_open mount umount2 pivot_root chroot setns unshare io_uring_setup io_uring_enter io_uring_register keyctl add_key request_key open_by_handle_at init_module finit_module delete_module reboot kexec_load setuid setgid setresuid setresgid capset'.split()
    resources={
      'CTX_FD3':dict(kind='sealed_memfd',ops=['READ','PREAD','FSTAT','GET_SEALS'],mutate=False),
      'KEY_FD4':dict(kind='sealed_private_key',ops=['BOOTSTRAP_IMPORT_ONLY'],mutate=False),
      'CHANNEL_FD5':dict(kind='inherited_seqpacket',ops=['SENDMSG','RECVMSG','POLL','FSTAT'],peer='exact enrolled HEALTH_GUARD/slot pair'),
      'TARGET_FD6':dict(kind='retained_pidfd',ops=['POLL','FSTAT'],mutate=False),
      'PUBLIC_MATERIAL_FD7_11':dict(kind='sealed_public_material',ops=['READ','PREAD','FSTAT','GET_SEALS'],mutate=False),
      'JOURNAL_FD16':dict(kind='native_journal',ops=['READ','PREAD','FSTAT'],mutate=False),
      'PGDATA':dict(kind='filesystem_label',root='private approved TEST PGDATA mount only',ops=['READ','WRITE','CREATE','RENAME','UNLINK','FSYNC'],owner='POSTMASTER private engine UID'),
      'PGSOCKET':dict(kind='unix_socket_label',root='private approved TEST PG socket directory',ops=['LISTEN','ACCEPT','CONNECT'],network='AF_UNIX only'),
      'APPROVED_CODE':dict(kind='readonly_mount',ops=['READ','EXECMAP_DURING_BOOTSTRAP_ONLY'],write=False),
      'HOST_ROOT':dict(kind='explicit_trust_boundary',ops=['PRE_ENROLLMENT_PROVISION','DESTROY_AFTER_DRAIN'],operational_native_capability=False)}
    rule_rows=[];profiles=[]
    fdsets={p:[3,5,16] for p in P}
    for p in ['APPROVAL_PRODUCER','APPROVAL_CONSUMER']:fdsets[p]+=[7,8,9,10,11]
    for p in ['ENFORCEMENT_WORKER','CENSUS_OBSERVER']:fdsets[p]+=[6]
    for p in P:
        calls=sorted(set(common+(pgextra if p=='POSTMASTER' else [])+(['pidfd_send_signal'] if p=='ENFORCEMENT_WORKER' else [])))
        for call in calls:
            if call in ['exit','exit_group']:predicate=op('TRUE')
            elif call in ['read','pread64']:predicate=op('FD_IN',0,[3,16]+([7,8,9,10,11] if p in ['APPROVAL_PRODUCER','APPROVAL_CONSUMER'] else [])) if p!='POSTMASTER' else op('FD_LABEL_IN',0,['PGDATA','PGSOCKET','APPROVED_CODE'])
            elif call=='write':predicate=op('FD_IN',0,[5]) if p!='POSTMASTER' else op('FD_LABEL_IN',0,['PGDATA','PGSOCKET'])
            elif call in ['sendmsg','recvmsg']:predicate=op('AND',op('FD_EQ',0,5),op('FLAGS_SUBSET',2,['MSG_DONTWAIT','MSG_NOSIGNAL','MSG_CMSG_CLOEXEC'])) if p!='POSTMASTER' else op('FD_LABEL_IN',0,['PGSOCKET'])
            elif call in ['poll','ppoll']:predicate=op('EVERY_POLLED_FD_IN',fdsets[p]) if p!='POSTMASTER' else op('EVERY_POLLED_FD_LABEL_IN',['PGDATA','PGSOCKET','ENGINE_CHILD_PIDFD'])
            elif call=='pidfd_send_signal':predicate=op('AND',op('ARG_EQ',0,6),op('ARG_IN',1,['SIGSTOP','SIGTERM','SIGCONT']),op('ARG_EQ',2,0),op('ARG_EQ',3,0))
            elif call=='close':predicate=op('FD_NOT_IN',0,fdsets[p]) if p!='POSTMASTER' else op('FD_LABEL_IN',0,['PGDATA','PGSOCKET','ENGINE_CHILD_PIDFD','APPROVED_CODE'])
            elif call=='fcntl':predicate=op('AND',op('ARG_IN',1,['F_GETFD','F_GETFL','F_GET_SEALS']),op('FD_IN',0,fdsets[p])) if p!='POSTMASTER' else op('AND',op('FD_LABEL_IN',0,['PGDATA','PGSOCKET','ENGINE_CHILD_PIDFD']),op('ARG_IN',1,['F_GETFD','F_GETFL','F_SETFD','F_SETFL','F_SETLK','F_SETLKW']))
            elif call in ['mmap','mprotect']:predicate=op('AND',op('NO_PROT_EXEC'),op('ANON_PRIVATE_OR_APPROVED_RO_MAPPING'))
            elif call in ['openat','readlinkat','getdents64','renameat','renameat2','unlinkat','mkdirat']:predicate=op('ALL_PATHS_LABEL_IN',['PGDATA','PGSOCKET','APPROVED_CODE_RO'],op('DENY_SYMLINK_ESCAPE'),op('NO_HOST_OR_OTHER_SLOT_PATH'))
            elif call in ['socket','bind','listen','accept4','connect','shutdown','getsockopt','setsockopt','recvfrom','sendto']:predicate=op('SOCKET_DOMAIN_AND_PATH_LABEL','AF_UNIX','PGSOCKET')
            elif call in ['clone','fork']:predicate=op('ENGINE_CHILD_ONLY',op('CLONE_FLAGS_SUBSET',['SIGCHLD','CLONE_CHILD_SETTID','CLONE_CHILD_CLEARTID']),op('SAME_TEST_NAMESPACES_AND_CGROUP'))
            elif call in ['dup','dup2','dup3']:predicate=op('ENGINE_OWNED_DESCRIPTOR_ONLY',op('NO_INHERITED_NATIVE_SLOT_DESCRIPTOR'),op('NO_OTHER_SLOT_OR_HOST_LABEL'))
            elif call in ['readv','writev','pwrite64','lseek','fsync','fdatasync','ftruncate','fchmod','fchown','statfs','fstatfs']:predicate=op('FD_LABEL_IN',0,['PGDATA','PGSOCKET'])
            elif call in ['semget','semctl','semop','semtimedop','shmget','shmat','shmdt','shmctl']:predicate=op('IPC_NAMESPACE_LABEL_ONLY','PRIVATE_TEST_ENGINE')
            elif call in ['wait4','waitid']:predicate=op('ENGINE_OWNED_CHILD_SET_ONLY')
            elif call in ['pipe2','epoll_create1','epoll_ctl','epoll_wait']:predicate=op('ENGINE_INTERNAL_DESCRIPTOR_LABEL_ONLY')
            elif call in ['getrandom']:predicate=op('REQUEST_LENGTH_LE',32)
            elif call in ['fstat','newfstatat']:predicate=op('METADATA_ONLY_NO_OPEN_OR_READ',op('DECLARED_OR_TEMP_ANCILLARY_HANDLE'))
            else:predicate=op('PROCESS_LOCAL_MEMORY_CLOCK_SIGNAL_HANDLER_OR_IDENTITY_ONLY',op('SEALED_RESOURCE_QUOTAS'))
            rule_rows.append(dict(rule_id=p+'/ACTIVE/'+call,participant=p,phase='ACTIVE',syscall=call,effect='ALLOW_IF',predicate=predicate,
              other_arguments='Linux ABI validation; unknown flags/addressability/classification => DENY_AND_UNKNOWN',
              source=ref(N+'supervisor.c' if p=='SUPERVISOR' else N+'observer.c' if p in ['CENSUS_OBSERVER','ENFORCEMENT_WORKER'] else N+'receiver.c' if p=='RECEIVER' else RN+'three-test-only-module-contracts.json'),
              implementation='Future compiled seccomp plus filesystem/socket/IPC label enforcement; no filter built here'))
        profiles.append(dict(PARTICIPANT_ID=p,EXECUTION_BOUNDARY='private TEST user/PID/mount/time/IPC/cgroup compartment, exact HOST-approved labels and immutable executable',
          EXPECTED_PARENT_CLASS='HOST_PLATFORM' if p=='SUPERVISOR' else 'SUPERVISOR',ALLOWED_PARENT_IDENTITY_RULE='Exact retained birth tuple from preserved native identity codec; no PID/name-only match',FORBIDDEN_PARENT_CLASSES='Any caller/restarted/tombstoned/generic harness parent',
          PROCESS_IDENTITY_RULE='preserved native-identity-codec process_instance_identity + current registry entity',BINARY_IDENTITY_RULE='full approved executable bytes SHA256, FUTURE_MEASURED',MODULE_IDENTITY_RULE='exact approved module map/hash; FUTURE_MEASURED never source hash substitution',LOADER_IDENTITY_RULE='approved ELF interpreter+fixed resolution manifest; no ambient ENV',DEPENDENCY_IDENTITY_RULE='closed flat node/edge manifest, exact approved file handles',
          CHILD_CREATION_ALLOWED=p in ['SUPERVISOR','POSTMASTER'],CHILD_CREATION_POLICY='SUPERVISOR fixed seven-slot pre-enrollment plan only; after sealing no clone/fork/exec. POSTMASTER only owned engine children under ACTIVE rule table and HOST observed birth inventory; unknown process class quarantines',
          SIBLING_COMMUNICATION_ALLOWED=False,SIBLING_COMMUNICATION_POLICY='Native participants communicate only via exact HEALTH_GUARD typed channels; readonly artifact/journal sharing is not an unmediated sibling RPC',
          INHERITED_HANDLE_POLICY='Only signed bootstrap inventory, no unknown descriptor; receive current SCM_PIDFD as temporary validation handle and close it; reject all unsolicited SCM_RIGHTS',INHERITED_DESCRIPTOR_POLICY={'protected_fd_numbers':fdsets[p],'fd4':'private key import PRE_ENROLLMENT then closed and forbidden for data IO','temporary_fds':'fstat/close only, never replace protected fd or label'},
          INHERITED_ENVIRONMENT_POLICY='Empty environment except explicit immutable locale/loader and exact descriptor-role map approved in build manifest; no PATH/PYTHONPATH/LD_PRELOAD/LD_LIBRARY_PATH import fallback',INHERITED_CREDENTIAL_POLICY='Fresh slot/purpose/generation key only; no inherited host/admin/provider/domain key or DB superuser password',
          DYNAMIC_CODE_LOADING_POLICY='All code/provider mappings preloaded/hash-verified during trusted initialization; ACTIVE denies executable new mappings/dlopen targets; unsupported required dependency denies activation',ARBITRARY_MODULE_LOADING_POLICY='DENY',ARBITRARY_COMMAND_POLICY='DENY exec/shell/SQL API in native messages',
          NETWORK_POLICY='No AF_INET/AF_INET6/external DNS; exact inherited AF_UNIX channels. POSTMASTER private TEST listener only; observer SQL transport held by dedicated fixed reader proxy, never exported to participants',
          FILESYSTEM_POLICY='No host/prod/private-other-slot mount. Code/config/public originals RO; private key sealed memory; native journal participants RO. POSTMASTER PGDATA private engine storage write is explicit service exception, never native caller-selected file authority',
          DATABASE_CONNECTION_POLICY='OS-only participants hold no SQL credential/session. POSTMASTER owns private TEST server only. Receiver/census request typed fixed observation from private READ_PROXY; no participant has arbitrary SQL transport',
          RESTART_POLICY='No bootstrap authority returns inside ACTIVE; retire old generation, reconcile UNKNOWN, prove old endpoints extinct, then explicit fresh bootstrap/new generation',RECONNECT_POLICY='Retain pending UNKNOWN; no new enrolled channel or inherited credential while unresolved',UNKNOWN_IDENTITY_BEHAVIOR='FAIL_CLOSED',
          DEFAULT_SYSCALL='DENY_AND_UNKNOWN',forbidden_syscalls=forbidden,
          postmaster_exception_necessity='A database engine must manage its own private storage/children to perform source-mandated catalog probes; read-only OS process cannot start it. This grants no SQL superuser/login credential or arbitrary command to a native participant caller' if p=='POSTMASTER' else 'NO_ENGINE_EXCEPTION'))
    doc('execution-isolation',profiles=profiles,rules=rule_rows,resources=resources,
      IR_enforcement='Seccomp handles scalar syscall/FD/flag predicates; immutable LSM label rules handle paths/socket/IPC classes and descriptor provenance. Both conjunctive; if any predicate cannot be enforced atomically or label is unknown, deny activation. An implementer may not replace a label predicate with unconditional syscall ALLOW',
      phase_edges=[['TRUSTED_BOOTSTRAP','CONFINED_PRE_ENROLLMENT'],['CONFINED_PRE_ENROLLMENT','ACTIVE'],['ACTIVE','REVOKED']],
      phase_gate='HOST_PLATFORM independently verifies immutable mounts/UID/capabilities/FD inventory, approved code and installed policy digest before ACTIVE; no participant may install/weaken/unload filters or transition itself back to bootstrap',
      supported_platform='Approved frozen Linux/ELF platform only; architecture syscall numbers resolved from approved ABI header at future build; unknown syscall/architecture unsupported, never widened',
      source_requirement='Backend-dependent label/IPC/filter operations require exact future enforcement artifact and independent verification; rule-table completeness is a design claim for review, not installed confinement proof')
    return profiles,rule_rows

def authority_custody_independence():
    auth=[];creds=[]
    for p in P:
        auth.append(dict(PARTICIPANT_ID=p,PRINCIPAL_CLASS='PRIVATE_TEST_ENGINE_OS_UID' if p=='POSTMASTER' else 'UNIQUE_NATIVE_SLOT_OS_UID_WITHOUT_SQL_ROLE',LOGIN_OR_NONLOGIN_REQUIREMENT='No native SQL login credential; reader proxy has separate explicit LOGIN role',ROLE_MEMBERSHIP_REQUIREMENT='Zero incoming/outgoing SQL owner/admin/shared-role memberships; no native OS supplementary privilege groups',SET_ROLE_POLICY='DENY',INHERIT_POLICY='DENY authority inheritance; process forks only as declared engine children, never key inheritance',ADMIN_OPTION_POLICY='DENY',OWNERSHIP_POLICY='No inspected database/schema/table/function ownership; engine OS owns only private TEST PGDATA, not native registry or other slot material',CREATEROLE_POLICY='DENY',SUPERUSER_POLICY='NO SQL superuser credential or operational root broker',BYPASSRLS_POLICY='DENY',PUBLIC_DEPENDENCY_POLICY='No authority inferred from PUBLIC; snapshot must classify every applicable public grant separately',DEFAULT_PRIVILEGE_DEPENDENCY_POLICY='No implicit non-owner new-object privilege; require approved creator/default snapshot',SECURITY_DEFINER_DEPENDENCY_POLICY='Native snapshot reader INVOKER/read-only only; no privileged definer fallback without independently closed exception',ALLOWED_CAPABILITY_CLASSES=['exact native message/work type','read fixed sealed/public inputs','role-specific isolated operation'],FORBIDDEN_CAPABILITY_CLASSES=['arbitrary SQL','shell','arbitrary path/module/target','host/admin/shared Package privilege','generic native worker'],MUTATION_AUTHORITY='fixed one-target native enforcement only' if p=='ENFORCEMENT_WORKER' else 'private TEST engine housekeeping only' if p=='POSTMASTER' else 'NONE on inspected data; signed native proposals only',READ_AUTHORITY='Only exact approved role resources',OBSERVATION_AUTHORITY='Role-specific signed facts; cannot self-issue independent observer truth',CROSS_PARTICIPANT_AUTHORITY_ALLOWED=False,CROSS_PARTICIPANT_AUTHORITY_RULE='No access to other slot private key/process memory/write endpoint; all peer facts independently revalidated by HEALTH_GUARD'))
        creds.append(dict(CREDENTIAL_ID_CLASS=p+'/TEST_GENERATION_TRANSPORT',ISSUER='HOST_PLATFORM approved TEST key custodian',RECIPIENT_PARTICIPANT=p,CUSTODIAN=p if p!='POSTMASTER' else 'HOST-held expected server endpoint authentication manifest, no fabricated POSTMASTER message key',DELIVERY_CHANNEL='Dedicated inherited sealed FD4 or server-endpoint expected manifest for POSTMASTER',DELIVERY_AUTHENTICATION='Exact retained parent/child birth and immutable bootstrap inventory',STORAGE_POLICY='Private slot UID only, sealed memfd, no host paths/env/argv/log export',MEMORY_RESIDENCE_POLICY='Import before ACTIVE, non-dumpable private memory, no ptrace/proc access; fixed bounded buffers zeroized after retirement',PERSISTENCE_POLICY='No private key disk persistence; public SPKI/digest/tombstone only',TRANSFER_ALLOWED=False,TRANSFER_TARGETS=[],DUPLICATION_ALLOWED=False,INHERITANCE_ALLOWED=False,USE_COUNT='One accepted work authorization; duplicate returns same receipt. Separate heartbeat purpose has finite approved frame count',EXPIRY_RULE='Exact immutable native policy BOOTTIME bound and current boot/timens; current generation/enrollment mandatory, no TTL renewal',GENERATION_BINDING='Exact current slot/generation high-water, no fallback',REGISTRY_BINDING='Exact native current enrollment/publication revisions',CONTEXT_BINDING='Preserved R5N bootstrap/full-message context',REVOCATION_AUTHORITY='NATIVE_REGISTRY_WRITER applies exact invalidation; HOST controls custody teardown',REVOCATION_OBSERVER='HEALTH_GUARD observed by HOST_PLATFORM',CRASH_BEHAVIOR='UNKNOWN, no reissue of same live authority',RESTART_BEHAVIOR='New generation/key only after old reconciliation/extinction/tombstone',RECONNECT_BEHAVIOR='No key/channel adoption while UNKNOWN',LEAK_OR_THEFT_BEHAVIOR='Quarantine entire affected generation; retire key/channel; stolen bytes alone cannot match required current kernel sender anchor',REPLAY_BEHAVIOR='Deny used challenge/stale generation/context; identical terminal receipt read only',DESTRUCTION_OR_ZEROIZATION_REQUIREMENT='Close import descriptor, explicit secret buffer cleanse on retirement; absence of destruction witness UNKNOWN',UNKNOWN_CUSTODY_BEHAVIOR='FAIL_CLOSED'))
    pairs=[]
    for a,b in itertools.combinations(P,2):
        sameparent=a!='SUPERVISOR' and b!='SUPERVISOR'
        pairs.append(dict(pair=[a,b],MUST_BE_DISTINCT=True,MAY_SHARE_BOUNDARY=True,MAY_SHARE_PARENT=sameparent,MAY_SHARE_READ_AUTHORITY=True,MAY_SHARE_CREDENTIAL_CLASS=True,MUST_NOT_SHARE_CREDENTIAL=True,MUST_NOT_SHARE_MUTATION_AUTHORITY=True,MUST_NOT_SHARE_OBSERVER_AUTHORITY=True,MUST_NOT_SHARE_OUTCOME_AUTHORITY=True,
          MAY_justifications=dict(boundary='Only common outer TEST namespace/host, never same process/private UID or writable memory',parent='Both are exact SUPERVISOR children' if sameparent else 'Not allowed: SUPERVISOR parent is HOST_PLATFORM, child parent is SUPERVISOR',read='Same immutable expected public manifest/original signature bytes or readonly journal, never private key or independent observation receipt ownership',credential_class='Same Ed25519/public binding format only; concrete key/custody/purpose/generation instances distinct'),
          MUST_NOT_enforcement=['different retained birth anchors and slot UIDs','private memfd/LSM labels','no process memory/ptrace/descriptor transfer','exact sender role/purpose keys and channel peer matching','independent observer key/UID and native registry writer separate from HEALTH_GUARD']))
    doc('authority-isolation',profiles=auth,bootstrap_is_not_operational_capability=True)
    doc('credential-custody',credentials=creds,values='Concrete keys/UIDs/policy bytes FUTURE_MEASURED under preserved R5N rules; no actual secret created')
    doc('independence-matrix',pairs=pairs,relations_total=21,auxiliary_required_separations=[['NATIVE_REGISTRY_WRITER','HEALTH_GUARD'],['HEALTH_GUARD','HOST_PLATFORM'],['READ_PROXY','each native participant'],['outcome claimant','CENSUS_OBSERVER/HEALTH_GUARD']],
       no_claimant_self_witness=True)
    return auth,creds,pairs

def projection():
    # Projection columns are explicit; raw pg_authid/password and query text never included.
    specs={
      'pg_roles':'oid rolname rolcanlogin rolinherit rolsuper rolcreaterole rolcreatedb rolreplication rolbypassrls',
      'pg_auth_members':'oid roleid member grantor admin_option inherit_option set_option',
      'pg_database':'oid datname datdba datallowconn datconnlimit encoding datacl',
      'pg_namespace':'oid nspname nspowner nspacl',
      'pg_class':'oid relname relnamespace relowner relkind relrowsecurity relforcerowsecurity relacl',
      'pg_attribute':'attrelid attnum attname atttypid attnotnull attisdropped attacl',
      'pg_proc':'oid proname pronamespace proowner prolang prokind prosecdef proisstrict proretset provolatile proparallel pronargs pronargdefaults prorettype proargtypes proallargtypes proargmodes proargnames proconfig proacl prosrc probin prosqlbody',
      'pg_type':'oid typname typnamespace typowner typtype typrelid typelem typarray typbasetype typacl',
      'pg_language':'oid lanname lanowner lanpltrusted lanplcallfoid laninline lanvalidator lanacl',
      'pg_depend':'classid objid objsubid refclassid refobjid refobjsubid deptype',
      'pg_shdepend':'dbid classid objid objsubid refclassid refobjid deptype',
      'pg_default_acl':'oid defaclrole defaclnamespace defaclobjtype defaclacl',
      'pg_db_role_setting':'setdatabase setrole setconfig',
      'pg_parameter_acl':'oid parname paracl',
      'pg_policy':'oid polname polrelid polcmd polpermissive polroles polqual polwithcheck',
      'pg_trigger':'oid tgrelid tgparentid tgname tgfoid tgtype tgenabled tgisinternal tgconstraint tgqual',
      'pg_rewrite':'oid rulename ev_class ev_type ev_enabled is_instead ev_qual ev_action',
      'pg_extension':'oid extname extowner extnamespace extrelocatable extversion',
      'pg_stat_activity':'datid pid usesysid usename backend_start backend_type'}
    bki=(ROOT/PG/'postgres.bki').read_text();types={}
    for m in re.finditer(r'^create (\w+) [^\n]*\n\s*\(\n(.*?)\n\s*\)',bki,re.M|re.S):
        types[m.group(1)]={a:t for a,t in re.findall(r'^\s*(\w+) = (\w+)',m.group(2),re.M)}
    viewtypes={'pg_roles':dict(oid='oid',rolname='name',rolcanlogin='bool',rolinherit='bool',rolsuper='bool',rolcreaterole='bool',rolcreatedb='bool',rolreplication='bool',rolbypassrls='bool'),
       'pg_stat_activity':dict(datid='oid',pid='int4',usesysid='oid',usename='name',backend_start='timestamptz',backend_type='text')}
    nullable={'relacl','attacl','proallargtypes','proargmodes','proargnames','proconfig','proacl','probin','prosqlbody','typacl','lanacl','nspacl','datacl','setconfig','paracl','polqual','polwithcheck','tgqual','ev_qual','ev_action','backend_start','backend_type','usename','usesysid','datid'}
    hashonly={'prosrc','probin','prosqlbody','polqual','polwithcheck','tgqual','ev_qual','ev_action'}
    rows=[]
    keys={'pg_roles':['oid'],'pg_auth_members':['oid'],'pg_attribute':['attrelid','attnum'],'pg_depend':['classid','objid','objsubid','refclassid','refobjid','refobjsubid','deptype'],'pg_shdepend':['dbid','classid','objid','objsubid','refclassid','refobjid','deptype'],'pg_db_role_setting':['setdatabase','setrole'],'pg_stat_activity':['pid','backend_start']}
    for relation,cols in specs.items():
        fields=[]
        for col in cols.split():
            t=viewtypes.get(relation,types.get(relation,{})).get(col)
            assert t,(relation,col)
            fields.append(dict(source_field=col,projected_name=col+'_sha256' if col in hashonly else col,pg18_type=t,
               type='bytes32' if col in hashonly else t,nullable=col in nullable,
               expression=op('NULL_PRESERVING_SHA256_UTF8_STORED_BYTES',op('FIELD',col)) if col in hashonly else op('FIELD',col),
               NULL_rule='Preserve SQL NULL presence; no zero/empty coercion. Privilege arrays NULL use approved PG18 hardwired-default expansion only in predicate layer' if col in nullable else 'Any NULL => UNKNOWN/reject snapshot'))
        predicate=op('TRUE')
        if relation=='pg_attribute':predicate=op('AND',op('GT',op('FIELD','attnum'),0),op('EQ',op('FIELD','attisdropped'),False))
        if relation=='pg_shdepend':predicate=op('IN',op('FIELD','dbid'),[0,'EXPECTED_DATABASE_OID'])
        if relation=='pg_stat_activity':predicate=op('OR',op('EQ',op('FIELD','datid'),'EXPECTED_DATABASE_OID'),op('IN',op('FIELD','usesysid'),'EXPECTED_PROTECTED_ROLE_OIDS'),op('IN',op('FIELD','usename'),'EXPECTED_PROTECTED_ROLE_NAMES'))
        rows.append(dict(SOURCE_ID='pg_catalog.'+relation,SOURCE_VERSION='Frozen PostgreSQL18 provider manifest; exact file hash is source authority',EXACT_PROJECTED_FIELDS=fields,
          EXACT_ROW_PREDICATE=predicate,EXACT_JOIN_KEYS=keys.get(relation,['oid']),DEPENDENCY_DIRECTION='Referencing member/object/function -> granted role, owner, referenced dependency/object; preserve grantor as independent field, never merge origins',
          NULL_SEMANTICS='Per field; any essential role/backend/scope identity NULL => UNKNOWN. Nullable ACL/config/body absence preserved, not inferred safe',DUPLICATE_SEMANTICS='Duplicate natural key or unexpected duplicate source row rejects; no DISTINCT/dedup hiding evidence',ORDERING_RULE='Unsigned lexicographic order of complete canonical row bytes, duplicate key separately checked',CANONICAL_ENCODING='catalog-encoding.json',CANONICALIZATION_RULE='No pretty-print/psql/locale or lossy normalization; typed field order is the explicit list',SNAPSHOT_SCOPE='Current isolated TEST database; role/member/db shared catalogs all rows needed to discover unexpected paths, never a caller-selected object filter',SNAPSHOT_IDENTITY_RULE='SHA256 typed source_id/version/snapshot-context/full ordered row collection',SNAPSHOT_REVISION_RULE='Single read-only REPEATABLE READ MVCC transaction plus independent native registry/kernel barrier before/after; pg_stat activity needs separate volatile-statistics applicability check',SOURCE_AUTHORITY=ref(PG+'system_views.sql') if relation in viewtypes else ref(PG+'postgres.bki'),READER_PRINCIPAL='R5N1_READ_PROXY SQL role: LOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS, zero memberships',REQUIRED_READ_PRIVILEGE='SELECT exact listed non-secret metadata fields or exact fixed read-only projection; no table wildcard, no secret field grant',FORBIDDEN_PRIVILEGES=['DML','GRANT OPTION','ownership','SET ROLE','CREATEROLE','superuser','BYPASSRLS','credential secrets','arbitrary SQL API'],SENSITIVE_FIELDS_EXCLUDED=['pg_authid.rolpassword','pg_shadow.passwd','pg_stat_activity.query/query_id/client_addr/client_hostname','private Package key_material/secret_verifier','raw function/policy/trigger bodies'],MISSING_ROW_SEMANTICS='Expected identity/source row missing => UNKNOWN; collection absence is only evidence after complete verified snapshot, never query failure',MULTIPLE_ROW_SEMANTICS='Expected singleton multiple rows => UNKNOWN; legitimate graph collections preserve all distinct rows',UNKNOWN_SEMANTICS='FAIL_CLOSED',
          source_visibility_proof='UNRESOLVED_PG_STAT_GET_ACTIVITY_BODY' if relation=='pg_stat_activity' else 'View/BKI field identity frozen; exact future read privileges and no-secret exposure checked independently before activation'))
    doc('catalog-projection',sources=rows,source_relations_total=len(rows),projected_fields_total=sum(len(r['EXACT_PROJECTED_FIELDS']) for r in rows),
       projected_scope_derivation='Role/privilege/ownership/SD/default/config/dependency discovery needs global metadata address/ACL origins in the isolated TEST database; pg_roles avoids password source, bodies are hashes only. External native registry/kernel/context facts are separate typed inputs, not fabricated SQL catalogs',
       no_SELECT_star=True,no_implicit_column_order=True,no_psql_or_locale=True,
       native_registry_source=ref(RN+'native-registry-generation.json'),native_kernel_source=ref(RN+'native-identity-codec.json'),
       no_catalog_row_filter_for_convenience=True)
    doc('catalog-encoding',domain='FLOOOW/PACKAGE0090/R5N1/CATALOG/V1',
       frame='u32be UTF8 domain length || domain || u16be field count || fields ascending contiguous tag u16be,length u32be,payload; null payload00; present01||typed bytes',
       numeric='oid u32be; int2/int4/int8 signed 2/4/8-byte BE two-complement; bool 00/01; char exactly1 ASCII byte; name/text strict already NFC UTF8; reject noncanonical, no normalization',
       timestamp='finite signed i64 UTC microseconds since2000-01-01 as native source, SQL NULL presence preserved; reject infinity sentinels/submicrosecond conversion',
       arrays='u32be count then u32be element size+typed element; preserve declared argument/setting order. ACL exploded rows sort complete canonical bytes and preserve grantor/grantee/privilege/grant-option; NULL ACL != empty ACL',
       collection='u32be row count then u32be row size+row; source rows sorted complete unsigned bytes, reject duplicate natural keys; never truncate/adopt live extras',
       ACL='Normalize each explicit aclitem through frozen acl.c aclexplode semantics into grantor oid,grantee oid (0=PUBLIC),privilege exact enum,is_grantable bool. NULL ACL uses acldefault(kind,owner) model, explicit empty ACL count0 retains owner implicit rights separately. Default ACL rows never retroactively replace current-object ACL',
       pg_node_tree_and_body='Hash exact stored UTF8 bytes with NULL-preserving presence; no pg_get_functiondef pretty rendering. Verified expected source/body effect manifests separate from digest equality',
       bounds='All count/byte limits finite positive in independent immutable native snapshot policy before later execution. Overflow, unknown type/source or limit breach => UNKNOWN, no partial snapshot')
    return rows

def predicates_consistency_and_reader(sources):
    predicates=[]
    expressions={
      'IS_EXPECTED_ROLE':op('AND',op('EQ','role.oid','expected.oid'),op('EQ','role.rolname','expected.name')),
      'HAS_LOGIN':op('EQ','role.rolcanlogin',True),'IS_SUPERUSER':op('EQ','role.rolsuper',True),'HAS_CREATEROLE':op('EQ','role.rolcreaterole',True),'HAS_BYPASSRLS':op('EQ','role.rolbypassrls',True),
      'CAN_INHERIT_ROLE':op('OR',op('EQ','member','target'),op('IS_SUPERUSER','member'),op('REACHABLE','INHERIT','member','target')),
      'CAN_SET_ROLE':op('OR',op('EQ','member','target'),op('IS_SUPERUSER','member'),op('REACHABLE','SET','member','target')),
      'HAS_ADMIN_OPTION':op('AND',op('NE','member','target'),op('OR',op('IS_SUPERUSER','member'),op('EXISTS_EDGE_FROM_REACHABLE_MEMBERS','member','target','admin_option=true'))),
      'IS_OBJECT_OWNER':op('EQ','object.owner_oid','role.oid'),'IS_SCHEMA_OWNER':op('EQ','schema.nspowner','role.oid'),'IS_FUNCTION_OWNER':op('EQ','function.proowner','role.oid'),
      'HAS_DIRECT_PRIVILEGE':op('EXISTS_EXPLICIT_ACL','object','role.oid','privilege'),
      'HAS_GRANT_OPTION':op('OR',op('IS_OBJECT_OWNER','role','object'),op('EXISTS_EFFECTIVE_GRANT_OPTION','object','role','privilege')),
      'HAS_PUBLIC_PRIVILEGE':op('EXISTS_ACL','object',0,'privilege'),
      'HAS_DEFAULT_PRIVILEGE_PATH':op('EXISTS_EFFECTIVE_CREATOR_DEFAULT','actual_creator','schema','kind','grantee','privilege'),
      'HAS_SECURITY_DEFINER_PATH':op('EXISTS_REACHABLE_FUNCTION','function.prosecdef=true','caller_execute_and_schema_usage','owner_role','verified_body_effect_graph'),
      'HAS_TRANSITIVE_MEMBERSHIP_PATH':op('REACHABLE','MEMBER','member','target'),
      'HAS_BOOTSTRAP_AUTHORITY_PATH':op('EXISTS_CALLABLE_EDGE_TO','HOST_ROOT_OR_DEPLOYMENT_OR_CREATEROLE_OR_SUPERUSER'),
      'HAS_UNEXPECTED_WRITE_PATH':op('EXISTS_REACHABLE_EFFECT_OUTSIDE_ALLOWLIST','WRITE_OR_ROLE_GRANT_OR_CREATE_OR_SIGNAL'),
      'HAS_UNEXPECTED_OBSERVATION_PATH':op('EXISTS_REACHABLE_EFFECT_OUTSIDE_ALLOWLIST','READ_OTHER_SLOT_SECRET_OR_UNAPPROVED_METADATA'),
      'HAS_UNEXPECTED_CREDENTIAL_PATH':op('EXISTS_REACHABLE_EFFECT_OUTSIDE_ALLOWLIST','READ_TRANSFER_DUPLICATE_PRIVATE_KEY_OR_DB_CHANNEL'),
      'ROLE_ROSTER_EXACT':op('BIJECTION','observed_protected_roles','independently_expected_OID_name_role_roster'),
      'BACKEND_CENSUS_EXACT':op('AND',op('BIJECTION','catalog.pid_start_role_db_set','registry.enrolled_backend_set'),op('EQ','kernel.birth_anchor_set','registry.retained_anchor_set'),op('NO_STATS_FIELD_REDACTION_OR_UNKNOWN')),
      'FUNCTION_CONFIG_SAFE':op('AND',op('EXACT_APPROVED_PROCONFIG','function'),op('QUALIFIED_STATIC_DEPENDENCIES_ONLY','function'),op('NO_UNAPPROVED_SD_OR_OWNER_PATH','function')),
      'SNAPSHOT_COHERENT':op('AND','all_sources_complete','same_MVCC_snapshot','same_reader_backend_start','same_native_generation_barrier','no_volatile_census_drift'),
      'NATIVE_QUALIFIED':op('ALL_KNOWN_TRUE','identity','ABI','isolation','custody','authority','registry','generation','catalog','completed_work','independent_observer','one_use_current_publication')}
    for name,e in expressions.items():predicates.append(dict(id=name,expression=e,truth_domain=['TRUE','FALSE','UNKNOWN'],UNKNOWN='Not qualified; no false/zero inference',inputs='Exactly explicit catalog rows plus typed protected expected manifest/native registry/kernel/work/observer receipts'))
    edges=['MEMBER','INHERIT','SET','ADMIN','IMPLICIT_DATABASE_OWNER','OWNER','DIRECT_ACL','GRANT_OPTION','PUBLIC_ACL','GLOBAL_DEFAULT','SCHEMA_DEFAULT','CREATOR','SCHEMA_USAGE','FUNCTION_EXECUTE','SECURITY_DEFINER','DEPENDENCY','BOOTSTRAP','READ_RESOURCE','WRITE_RESOURCE','CREDENTIAL_CUSTODY','OBSERVER_RECEIPT']
    doc('catalog-security-predicates',predicates=predicates,edge_types=edges,
       nodes='Typed role OID/name; object address(classid,objid,objsubid); schema/database; function signature/owner/body; external actor/key/endpoint/work/receipt',
       role_edge_rules={'MEMBER':'member->roleid for every pg_auth_members row, all options preserved','INHERIT':'member->roleid only inherit_option=true; rolinherit is grant-default attribute, not a retroactive substitute for current edge option','SET':'member->roleid only set_option=true, independent of inherit_option','ADMIN':'admin_option=true on edge reached via MEMBER recursion; is_admin_of_role special case member==target false, superuser true otherwise, per frozen acl.c','IMPLICIT_DATABASE_OWNER':'current pg_database.datdba -> pg_database_owner as provider roles_is_member_of adds, even absent explicit membership'},
       traversal='BFS/least fixed point per typed edge class, initial role itself where provider permits; visited set, no arbitrary depth cap; finite nodes are complete snapshot. Cycle detected/preserved then visited suppresses iteration only, never drops authority. Missing endpoint/type/effect proof => UNKNOWN',
       privilege_rules='Grantors retained separately. Owner implicit rights, direct ACL/PUBLIC, inherited roles, SET-reachable owners, defaults for future creation and SECURITY DEFINER effects are distinct edges; no effective-boolean equivalence collapse',
       source_authority=[ref(PG+'acl.c'),ref(PG+'aclchk.c'),ref(PG+'system_views.sql'),ref(PG+'pg_auth_members.h')],
       unresolved_predicates=['BACKEND_CENSUS_EXACT non-superuser field visibility and row completeness from pg_stat_get_activity native implementation','HAS_UNEXPECTED_WRITE_PATH exact body effect closure for future private reader query/engine authority if generic SQL gate absent'])
    doc('catalog-reader',principal='Dedicated READ_PROXY OS process and R5N1_read_proxy LOGIN role; not any of the seven participant identities',
       endpoint='Only fixed native observation request on authenticated peer channel; participants hold no raw SQL socket/password/role token',
       projected_source_objects=[dict(source=x['SOURCE_ID'],fields=[f['source_field'] for f in x['EXACT_PROJECTED_FIELDS']]) for x in sources],
       MUTATION_AUTHORITY='NONE',CREATEROLE='NO',SUPERUSER='NO',BYPASSRLS='NO',GENERIC_SQL_AUTHORITY='NO_EXTERNALLY_EXPOSED_API',ARBITRARY_OBJECT_AUTHORITY='NO',CREDENTIAL_SECRET_READ='NO',
       grants='Exact SELECT non-secret metadata columns/fixed read-only projections only; LOGIN+CONNECT+minimum schema USAGE. No memberships/SET ROLE/ADMIN/grant options/ownership/default privileges/host key paths',
       SQL_transport='Proxy alone holds preauthenticated fixed-role SQL descriptor; immutable frontend builder emits only approved BEGIN READ ONLY REPEATABLE READ, fixed projection statements, COMMIT/ROLLBACK. Request carries no SQL/object/path/role selector. No module/recipient may obtain descriptor or credential',
       SECURITY_DEFINER='Not used to bypass source visibility. A superuser definer or pg_read_all_stats membership is NOT silently adopted; if ordinary reader cannot read required facts, gate remains BLOCKED until exact weaker authority contract proven',
       stronger_reader_exception='NONE approved in this gate',
       role_query_gate_source=ref(N+'login.c'),
       atomic_static_gap='Frozen ExecutorStart/ProcessUtility hooks run after some parsing/planning work. Exact earliest pre-parse/frontend fixed-statement enforcement hook and effect-free query construction proof are not pinned; arbitrary-SQL transport confinement is not proved merely by naming a proxy',
       source_visibility_gap='Frozen system_views.sql and pg_proc.dat name pg_stat_get_activity but do not include its native body/visibility checks. No non-superuser cross-role backend_start completeness proof from these files alone')
    doc('snapshot-consistency',SNAPSHOT_BEGIN_RULE='Acquire native observation barrier for exact qualification/generation registry revision, capture expected roster+kernel birth/descriptor epoch, use fresh owned reader connection, BEGIN READ ONLY REPEATABLE READ before any projection',SNAPSHOT_END_RULE='All explicit source collections complete; reread barrier/kernel generation and volatile census; exact reader backend PID/start/context unchanged, no lost/overflow observation; commit/rollback read-only, independently witness digest before health',CONSISTENCY_BOUNDARY='Catalog MVCC on one backend/transaction; volatile pg_stat_activity and external native registry/kernel facts require separate before/after applicability and no-changing-enrollment barrier. MVCC alone does not freeze stats or external processes',SNAPSHOT_ID='SHA256 typed context + expected manifest/policy + exact reader authenticated backend PID/start + MVCC snapshot identity + barrier revision + all ordered source digests',BACKEND_OR_SESSION_IDENTITY_RULE='Actual owned proxy connection and reader backend PID/start, no reconnect/helper equivalence. Native probe session does not replace non-target final consumer session',CATALOG_REVISION_OR_EQUIVALENT_RULE='Trusted TEST admin/DDL exclusion while native generation sealed plus fixed MVCC snapshot and independently unchanged native observation barrier; no claim that catalog has a universal monotonic revision column',RETRY_RULE='Discard incomplete snapshot as UNKNOWN; new independently authorized read only after same lineage/pending state remains consistent; never merge rows across attempts',CONCURRENT_CHANGE_RULE='Any catalog/role/body/ACL expected identity drift or native/backend census applicability drift => UNKNOWN; no optimistic repair/adopt live extras',PARTIAL_READ_RULE='Never qualify; no truncation/sampling',CONNECTION_LOSS_RULE='UNKNOWN pending observation retained',RECONNECT_RULE='New reader session identity and full fresh snapshot; never complete old pending observation with rows from new backend',RESTART_RULE='Old generation/current tip preserved; new process cannot reset UNKNOWN or revive retired data',
       no_live_currentness_proof_claimed=True)
    return predicates,edges

def qualification_and_attacks():
    prior=read(RN+'native-participants.json')['participants'];matrix=[]
    for p in prior:
        matrix.append(dict(PARTICIPANT_ID=p['PARTICIPANT_ID'],carried_closed_identity=ref(RN+'native-participants.json','/participants/'+str(P.index(p['PARTICIPANT_ID']))),
          carried_protocol_hashes={n:sha((ROOT/RN/n).read_bytes()) for n in ['native-message-abi.json','native-registry-generation.json','native-identity-codec.json']},
          qualification=op('ALL_KNOWN_TRUE',*[op('INPUT',x) for x in ['STATIC_CONSTANT_IDENTITY_MODEL','FUTURE_MEASURED_APPROVED_CODE_PARENT_PROCESS','STATIC_ISOLATION_IR','CUSTODY_ATTESTATION','CATALOG_SNAPSHOT_AUTHORITY_PREDICATES','REGISTRY_SNAPSHOT','CURRENT_GENERATION_HIGH_WATER','COMPLETED_WORK_RECEIPT','INDEPENDENT_OBSERVER_RECEIPT','ONE_USE_PUBLICATION']]),
          input_types={'STATIC_CONSTANT_IDENTITY_MODEL':'STATIC_CONSTANT','FUTURE_MEASURED_APPROVED_CODE_PARENT_PROCESS':'FUTURE_MEASURED','STATIC_ISOLATION_IR':'STATIC_CONSTANT','CUSTODY_ATTESTATION':'INDEPENDENT_OBSERVER_RECEIPT','CATALOG_SNAPSHOT_AUTHORITY_PREDICATES':'CATALOG_SNAPSHOT','REGISTRY_SNAPSHOT':'REGISTRY_SNAPSHOT','CURRENT_GENERATION_HIGH_WATER':'REGISTRY_SNAPSHOT','COMPLETED_WORK_RECEIPT':'COMPLETED_WORK_RECEIPT','INDEPENDENT_OBSERVER_RECEIPT':'INDEPENDENT_OBSERVER_RECEIPT','ONE_USE_PUBLICATION':'REGISTRY_SNAPSHOT'},
          UNKNOWN='NOT_QUALIFIED',STATIC_IDENTITY_DESIGN='CARRIED_CLOSED_RULES_FUTURE_VALUES_PENDING',STATIC_ABI_DESIGN='CARRIED_CLOSED',STATIC_ISOLATION_DESIGN='CANDIDATE_EXACT_IR_REVIEW_REQUIRED',STATIC_CUSTODY_DESIGN='CANDIDATE_REVIEW_REQUIRED',STATIC_GENERATION_DESIGN='CARRIED_CLOSED',STATIC_REGISTRY_DESIGN='CARRIED_CLOSED',STATIC_CATALOG_DESIGN='REVIEW_REQUIRED',STATIC_COMPLETED_WORK_DESIGN='REQUIRES_BOTH_CUSTODY_AND_CATALOG_NOT_ONLY_CUSTODY',STATIC_INDEPENDENCE_DESIGN='REVIEW_REQUIRED',STATIC_SUBSTITUTION_REJECTION_DESIGN='REVIEW_REQUIRED',FULLY_DESIGNED='NOT_YET_ACCEPTED'))
    doc('participant-qualification',matrix=matrix,participants_required=7,not_carried_zero_or_assumed_seven=True,
       completed_work_connection='Exact identity/generation/entity revision/channel/key/context/observer/outcome/one-use publication as preserved native work record; catalog visibility and fixed reader effect authority are independent static prerequisites, so earlier NO was not solely missing custody')
    extra='credential_theft credential_transfer credential_inheritance wrong_custodian wrong_reader catalog_row_omission catalog_row_injection catalog_duplication catalog_stale_snapshot mixed_snapshot wrong_role transitive_SET_ROLE transitive_INHERIT ADMIN_option_escalation ownership_escalation PUBLIC_path default_privilege_path SECURITY_DEFINER_path search_path_substitution CREATEROLE_path superuser_path bootstrap_path reader_mutation reader_privilege_escalation snapshot_reconnect snapshot_restart'.split()
    attacks=[]
    for p in P:
        for name in extra:
            attacks.append(dict(id=p+'/'+name,participant=p,surface=name,required_outcome='UNKNOWN' if name in ['catalog_stale_snapshot','mixed_snapshot','snapshot_reconnect','snapshot_restart'] else 'REJECT',
              predicate='Catalog snapshot exact natural-key roster/complete field presence/same observation identity plus separated edge-type least-fixed-point authority and role-specific IO/custody/peer predicates must all be known true',
              implementation_executed=False,proof='STATIC_REQUIRED_CASE_NOT_ENFORCEMENT_PROOF'))
    doc('substitution-matrix',preserved_cases=read(RN+'native-substitution-matrix.json')['cases'],new_cases=attacks,
       inherited_cases=168,new_cases_total=len(attacks),UNKNOWN_fails_closed=True,
       not_all_coverage_rows_are_proven_rejection=True)

def generate():
    freeze_and_account();profiles,iso=isolation();auth,creds,pairs=authority_custody_independence();sources=projection();preds,edges=predicates_consistency_and_reader(sources);qualification_and_attacks()
    atomics=[dict(BLOCKER_ID='N1-SOURCE-STATS-VISIBILITY',PARTICIPANT=['POSTMASTER','RECEIVER','CENSUS_OBSERVER','ENFORCEMENT_WORKER'],MISSING_DECISION='Minimum non-secret cross-role backend census read authority cannot be approved from a prototype/view alone; no superuser/pg_read_all_stats fallback',MISSING_SOURCE='Pinned PG18 src/backend/utils/adt/pgstatfuncs.c::pg_stat_get_activity visibility/redaction body (not present in frozen provider inventory)',WHY_STATIC='Needs source semantics before selecting least-privilege authority, not an actual runtime backend PID/hash',MINIMUM_NEXT_ACTION='Add independently verified source snapshot for exact approved PG18 build and derive field visibility/row completeness; keep reader ordinary and no secret read'),
      dict(BLOCKER_ID='N1-READER-PREPARSE-GATE',PARTICIPANT=['POSTMASTER','RECEIVER','CENSUS_OBSERVER'],MISSING_DECISION='Exact fixed-statement ingress gate must run before arbitrary parse/type/planner effects, not only ExecutorStart/ProcessUtility',MISSING_SOURCE='Pinned PG18 frontend exec_simple_query/exec_parse_message path or exact fixed reader proxy state-machine/source-to-packet proof',WHY_STATIC='Two ingress implementations can satisfy fixed query prose while one evaluates unapproved functions before guard. Actual compiled artifact may remain FUTURE_MEASURED after rule closes',MINIMUM_NEXT_ACTION='Specify pre-parser byte/protocol allowlist/entrypoint and exact constant statement construction with no participant SQL input; source-pin earliest effect boundary'),
      dict(BLOCKER_ID='N1-LABEL-IR-ATOMICITY',PARTICIPANT=P,MISSING_DECISION='Atomic enforcement semantics for dynamic engine FD/path/IPC label predicates and syscall phase transition need exact backend decision procedure',MISSING_SOURCE='Native policy backend specification for FD_LABEL_IN/ALL_PATHS_LABEL_IN/IPC namespace and pre-enrollment-to-active installation, including rename/symlink/SCM descriptor race handling',WHY_STATIC='A complete rule list with uninterpreted enforcement operations is not yet an enforceable unique policy. Future installed bytecode/digest is separate from missing decision procedure',MINIMUM_NEXT_ACTION='Choose/pin deterministic label-policy backend and define every label IR operation atomically, including denied ambiguous races; do not weaken to syscall-wide allow')]
    doc('atomic-residuals',blockers=atomics,count=len(atomics),historical_families=['R5N-STATIC-ISOLATION','R5N-STATIC-CATALOG'],
       no_broad_more_design_blocker=True,non_target_blockers_unchanged=['V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES'])
    save('NATIVE-GATE.json',dict(BRANCH=BRANCH,BASELINE_HEAD=BASE,R5_NATIVE_ROOT_CAUSES_ORIGINAL=3,
      R5_NATIVE_ROOT_CAUSE_1='NATIVE/ISOLATION_CUSTODY:STILL_OPEN',R5_NATIVE_ROOT_CAUSE_2='NATIVE/CATALOG_WORK_WITNESS:STILL_OPEN',R5_NATIVE_ROOT_CAUSE_3='NATIVE/PUBLICATION_GENERATION_BINDING:CLOSED_BY_R5N',ROOT_CAUSE_ACCOUNTING_RECONCILED='YES',R5_NATIVE_TRUE_STATIC_DESIGN_FAILURES_BEFORE=2,R5_NATIVE_TRUE_STATIC_DESIGN_FAILURES_REMAINING=3,R5N_STATIC_ISOLATION='REVIEW_PENDING',R5N_STATIC_CATALOG='REVIEW_PENDING',NATIVE_PARTICIPANTS_REQUIRED=7,NATIVE_PARTICIPANTS_FULLY_DESIGNED=0,UNRESOLVED_NATIVE_WORK_ANCHORS=7,GENERIC_PROCESS_SUBSTITUTIONS=0,
      NATIVE_MESSAGE_ABI_COMPLETE='YES',NATIVE_GENERATION_PROTOCOL_COMPLETE='YES',NATIVE_REGISTRY_PROTOCOL_COMPLETE='YES',NATIVE_COMPLETED_WORK_PROTOCOL_COMPLETE='REVIEW_PENDING',NATIVE_INDEPENDENCE_MODEL_COMPLETE='REVIEW_PENDING',NATIVE_CUSTODY_MODEL_COMPLETE='REVIEW_PENDING',NATIVE_CATALOG_MODEL_COMPLETE='REVIEW_PENDING',NATIVE_SUBSTITUTION_MATRIX_COMPLETE='REVIEW_PENDING',
      CATALOG_SOURCE_RELATIONS_TOTAL=len(sources),CATALOG_PROJECTED_FIELDS_TOTAL=sum(len(s['EXACT_PROJECTED_FIELDS']) for s in sources),CATALOG_SECURITY_PREDICATES_TOTAL=len(preds),CATALOG_GRAPH_EDGE_TYPES_TOTAL=len(edges),CATALOG_UNRESOLVED_FIELDS=3,CATALOG_UNRESOLVED_PREDICATES=2,
      NATIVE_ISOLATION_RULES_TOTAL=len(iso)+sum(len(p) for p in profiles)+sum(len(a) for a in auth),NATIVE_CUSTODY_RULES_TOTAL=sum(len(c) for c in creds),NATIVE_INDEPENDENCE_RELATIONS_TOTAL=len(pairs),NATIVE_UNRESOLVED_ISOLATION_RULES=1,NATIVE_UNRESOLVED_CUSTODY_RULES=0,NATIVE_UNRESOLVED_INDEPENDENCE_RELATIONS=0,
      IMPLEMENTATION_PERFORMED='NO',NATIVE_BUILD_PERFORMED='NO',NATIVE_RUNTIME_EXECUTED='NO',SQL_EXECUTED='NO',DATABASE_CONTACTED='NO',V043_EXECUTED='NO',B02_EXECUTED='NO',NATIVE_INDEPENDENT_REVIEW='PENDING',V2_NATIVE_STATUS='BLOCKED',BLOCKER_COUNT_FOR_V2_NATIVE=len(atomics),RESIDUAL_NATIVE_BLOCKERS=[b['BLOCKER_ID'] for b in atomics],NEXT_EXECUTED=False,NEXT_GATE='CLOSE_ATOMIC_NATIVE_SOURCE_INGRESS_AND_LABEL_POLICY_PROOFS_NO_LIVE_EXECUTION'))
    print(json.dumps(dict(generated=True,participants=len(P),catalog_sources=len(sources),projected_fields=sum(len(s['EXACT_PROJECTED_FIELDS']) for s in sources),atomic_candidate_blockers=len(atomics),live_executed=False)))
