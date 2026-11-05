"""Six-decision offline static derivation; no native implementation or SQL execution."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,re,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
PRE='docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a/'
N1='docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/'
N2='docs/evidence/package-0090-B01-v2-native-static-closure-r5n2/'
N='docs/evidence/package-0090-B01-v2-native-static-closure-r5n/'
PG='docs/evidence/package-0090-full-reachable-expectation-closure-v2/provider/'
BASE='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
ORDER=['N1-'+x for x in ['SCALAR-SYSCALL-IR','SOURCE-STATS-VISIBILITY','CREDENTIAL-CLASS-INVENTORY','SNAPSHOT-MUTATION-BARRIER','CATALOG-EFFECT-GRAPH','READER-EFFECTIVE-ACL']]
def sha(b):return hashlib.sha256(b).hexdigest()
def rd(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def wr(n,x):(O/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def doc(n,**x):wr(n+'.json',dict(scope='R5N2A2_STATIC_DESIGN_ONLY',implementation_performed=False,**x))
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def ref(p,ptr='/'):return dict(path=p,sha256=sha((R/p).read_bytes()),pointer=ptr)
def original_expression(row):
    p=R/row['SOURCE'];pointer=row['POINTER']
    if pointer.startswith('/line/'):return p.read_text(encoding='utf-8-sig').splitlines()[int(pointer.split('/')[-1])-1]
    v=rd(row['SOURCE'])
    for part in pointer.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~');v=v[int(part)] if isinstance(v,list) else v[part]
    assert isinstance(v,str) and sha(v.encode())==row['VALUE_SHA256']
    return v
def main():
    assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff' and git('rev-parse','HEAD')==BASE
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    old=[p for p in git('ls-files','--others','--exclude-standard').splitlines() if '/package-0090-B01-v2-native-static-closure-r5n2a2/' not in p]
    assert len(old)==145
    freeze=rd(PRE+'baseline-freeze.json');freeze['source_checkout_sha256'].update({p:sha((R/p).read_bytes()) for p in old});freeze.update(untracked_before=145,untracked_before_paths=old,REMOTE_NETWORK_VERIFIED='NO');wr('baseline-freeze.json',freeze)
    prior=rd(PRE+'foundation-residuals.json')['residuals'];byid={r['BLOCKER_ID']:r for r in prior}
    doc('six-register',order=ORDER,records=[dict(BLOCKER_ID=i,CURRENT_MISSING_DECISION=byid[i]['EXACT_MISSING_DECISION'],AUTHORITATIVE_INPUTS=[ref(PRE+'foundation-residuals.json')],DEPENDENCIES=ORDER[:ORDER.index(i)],OUTPUT_CONTRACT=i+'/R5N2A2',STATIC_CLOSURE_CRITERION='Independent source review confirms complete logical contract; no future instance value required',FUTURE_IMPLEMENTATION_PROOF='Required later, not static failure',FUTURE_BUILD_PROOF='Required later, not static failure',FUTURE_RUNTIME_PROOF='Required later, not static failure',STATUS='REVIEW_REQUIRED') for i in ORDER],official_residual_denominator=10,deferred={'N1-QUALIFICATION-INPUT-RESOLUTION':'OPEN_BY_DEPENDENCY','N1-SUBSTITUTION-STATIC-WITNESSES':'OPEN_BY_DEPENDENCY'})
    # A. Semantic families preserve source-derived operation groups, refine their common contract.
    ir=rd(PRE+'scalar-operation-ir.json');families=[]
    pointer=dict(ir['pointer_policy'],zero_length='No dereference; NULL allowed only declared OPTIONAL zero-size field. Mandatory identity resource cannot be NULL even for0bytes.',oversized_length='Reject before memory access/allocation',unterminated_string='Paths supplied as counted immutable bytes; embedded NUL or missing required terminal terminator in platform input rejects',noncanonical_path='Absolute path only under committed directory label or relative under retained approved directory; reject empty components,dot,dotdot,embeddedNUL; symlink/rename cannot change retained identity during use')
    quotas=[]
    units={'max_bytes_per_operation':'bytes','max_vector_count':'elements','max_path_bytes':'bytes','max_private_memory':'bytes','max_descriptors':'handles','max_children':'births','max_ipc_objects':'objects','max_wait_ns':'nanoseconds','max_operations_per_work':'operations'}
    for name,unit in units.items():quotas.append(dict(QUOTA_ID=name,UNIT=unit,SCOPE='exact participant+generation+context+work',WINDOW_OR_LIFETIME='one work; live-object reservations additionally persist until independently observed destruction',COUNTER_IDENTITY='SHA256(canonical participant,generation,context,work,quota_id)',INITIAL_VALUE=0,MAX_VALUE='mandatory immutable policy u64 value;positive except source-permitted zero child/IPC;<=2^63-1',OVERFLOW='checked u64 reserve+delta; any overflow DENY',RESET='Never reconnect/crash reset; new work gets new counter after prior consumption resolved; live resources carry reservations',GENERATION_BINDING='exact current generation',CONTEXT_BINDING='exact immutable context policy digest',UNKNOWN='Hold unresolved reservation; no new eligibility'))
    scalar_types={'U64':dict(signed=False,bits=64,range='0..2^64-1'),'U32':dict(signed=False,bits=32,range='0..2^32-1'),'I64':dict(signed=True,bits=64,range='-2^63..2^63-1')}
    for fid,schema in sorted(ir['schema_table'].items()):
        families.append(dict(FAMILY_ID=fid,OPERATION_SEMANTICS='Only concrete operation members in mapping table; named source predicate and operation-specific valid field domain conjunctive',RESOURCE_SEMANTICS='All refs retain enrolled object birth identity and current committed label; no path/FD-number-only authority',ARGUMENT_SCHEMA=schema,FLAG_SCHEMA='Symbolic enum set peroperation; unknown symbol/bit rejects; no implicit allow; required/forbidden masks in operation table',COMMAND_SCHEMA='Exact peroperation enum; unknown rejects',POINTER_SCHEMA=pointer,LENGTH_SCHEMA='Counted bytes/elements; exact payload length; checked arithmetic and mandatory quota bound',COUNT_SCHEMA='Exact element count including nested vectors; sum lengths checked; zero only if sourceoperation supports empty operation',QUOTA_SCHEMA=quotas,LABEL_REQUIREMENT=ref(PRE+'logical-label-ir.json'),CREDENTIAL_REQUIREMENT='Current exact class/purpose; noncredential operation requires explicit NONE, not ambient privilege',CONTEXT_REQUIREMENT='exactcontext',GENERATION_REQUIREMENT='exactcurrentgeneration',RETURN_SCHEMA='Typed result only declared resource/bytes/count; no partially labeled handle escapes',ERROR_SCHEMA='Bounded error, no work-success; preserve unknown effects and reserved budget',UNKNOWN_SCHEMA='Reject operation and qualification'))
    # Finite symbolic parameters. Numeric platform masks are future ABI binding, not invented.
    flags={
      'sendmsg':['MSG_DONTWAIT','MSG_NOSIGNAL'],'recvmsg':['MSG_DONTWAIT','MSG_CMSG_CLOEXEC'],
      'sendto':['MSG_DONTWAIT','MSG_NOSIGNAL'],'recvfrom':['MSG_DONTWAIT'],
      'openat':['O_RDONLY','O_RDWR','O_WRONLY','O_CREAT','O_EXCL','O_TRUNC','O_APPEND','O_CLOEXEC','O_DIRECTORY','O_NOFOLLOW'],
      'mmap':['MAP_PRIVATE','MAP_ANONYMOUS','MAP_FIXED_NOREPLACE'],'mprotect':['PROT_READ','PROT_WRITE'],'pipe2':['O_CLOEXEC','O_NONBLOCK'],
      'socket':['AF_UNIX','SOCK_STREAM','SOCK_SEQPACKET','SOCK_CLOEXEC','SOCK_NONBLOCK'],
      'accept4':['SOCK_CLOEXEC','SOCK_NONBLOCK'],'clone':['SIGCHLD','CLONE_CHILD_SETTID','CLONE_CHILD_CLEARTID'],
      'renameat2':['RENAME_NOREPLACE'],'unlinkat':['AT_REMOVEDIR'],'newfstatat':['AT_EMPTY_PATH','AT_SYMLINK_NOFOLLOW'],
      'getrandom':['GRND_NONBLOCK'],'ppoll':[],'poll':[],'fork':[],'pidfd_send_signal':[]}
    commands={'fcntl':['F_GETFD','F_GETFL','F_GET_SEALS','F_SETFD','F_SETFL','F_SETLK','F_SETLKW'],'shutdown':['SHUT_RD','SHUT_WR','SHUT_RDWR'],'epoll_ctl':['EPOLL_CTL_ADD','EPOLL_CTL_MOD','EPOLL_CTL_DEL'],'lseek':['SEEK_SET','SEEK_CUR','SEEK_END'],'futex':['FUTEX_WAIT_PRIVATE','FUTEX_WAKE_PRIVATE'],'madvise':['MADV_NORMAL','MADV_DONTNEED','MADV_WILLNEED'],'semctl':['GETVAL','GETALL','SETVAL','SETALL','IPC_STAT','IPC_RMID'],'shmctl':['IPC_STAT','IPC_RMID'],'clock_gettime':['CLOCK_MONOTONIC','CLOCK_BOOTTIME','CLOCK_REALTIME'],'clock_nanosleep':['CLOCK_MONOTONIC','CLOCK_BOOTTIME'],'getsockopt':['SO_PEERCRED','SO_PEERPIDFD','SO_ERROR'],'setsockopt':['SO_PASSCRED','SO_PASSPIDFD'],'rt_sigaction':['APPROVED_HANDLER','DEFAULT','IGNORE'],'rt_sigprocmask':['SIG_BLOCK','SIG_UNBLOCK','SIG_SETMASK']}
    variants={}
    variant_specs='''read|resource:R,out:BO,length:U64
pread64|resource:R,out:BO,length:U64,offset:I64
write|resource:R,input:BI,length:U64
pwrite64|resource:R,input:BI,length:U64,offset:I64
readv|resource:R,vectors:VO,count:U64
writev|resource:R,vectors:VI,count:U64
getrandom|out:BO,length:U64,flags:FLAGS
sendmsg|resource:R,message:MI,flags:FLAGS
recvmsg|resource:R,message:MO,flags:FLAGS
sendto|resource:R,input:BI,length:U64,flags:FLAGS,address:AI,address_length:U64
recvfrom|resource:R,out:BO,length:U64,flags:FLAGS,address:AO,address_length:U64
openat|directory:R,path:PI,flags:FLAGS,mode:U32
readlinkat|directory:R,path:PI,out:BO,length:U64
getdents64|resource:R,out:BO,length:U64
renameat|directory:R,path:PI,destination_directory:R,destination_path:PI
renameat2|directory:R,path:PI,destination_directory:R,destination_path:PI,flags:FLAGS
unlinkat|directory:R,path:PI,flags:FLAGS
mkdirat|directory:R,path:PI,mode:U32
socket|domain:ENUM,socket_type:FLAGS,protocol:U32
bind|resource:R,address:AI,address_length:U64
connect|resource:R,address:AI,address_length:U64
listen|resource:R,backlog:U32
accept4|resource:R,address:AO,address_length:U64,flags:FLAGS
shutdown|resource:R,command:CMD
getsockopt|resource:R,level:ENUM,command:CMD,out:BO,length:U64
setsockopt|resource:R,level:ENUM,command:CMD,input:BI,length:U64
poll|polls:PO,count:U64,timeout:TIME
ppoll|polls:PO,count:U64,timeout:TIME,signal_mask:SM,signal_mask_size:U64
epoll_create1|flags:FLAGS
epoll_ctl|resource:R,command:CMD,target:R,event:EV
epoll_wait|resource:R,events:EO,count:U32,timeout:TIME
brk|private_end:ADDR
mmap|address:ADDR,length:U64,protection:FLAGS,flags:FLAGS,backing:R_OPT,offset:I64
munmap|address:ADDR,length:U64
mprotect|address:ADDR,length:U64,protection:FLAGS
madvise|address:ADDR,length:U64,command:CMD
msync|address:ADDR,length:U64,flags:FLAGS
clone|flags:FLAGS,stack:ADDR,parent_tid:TID_OUT,child_tid:TID_OUT,tls:PRIVATE_REF
fork|
wait4|target:CHILD,status:STATUS_OUT,options:FLAGS,usage:USAGE_OUT
waitid|target_kind:ENUM,target:CHILD,information:STATUS_OUT,options:FLAGS,usage:USAGE_OUT
pidfd_send_signal|target:R,signal:ENUM,information:NULL,flags:FLAGS
exit|status:I32
exit_group|status:I32
semget|key:IPC_KEY,count:U32,flags:FLAGS
semctl|resource:IPC_REF,element:U32,command:CMD,value:IPC_VALUE
semop|resource:IPC_REF,operations:SEMOPS,count:U64
semtimedop|resource:IPC_REF,operations:SEMOPS,count:U64,timeout:TIME
shmget|key:IPC_KEY,length:U64,flags:FLAGS
shmat|resource:IPC_REF,address:ADDR,flags:FLAGS
shmdt|address:ADDR
shmctl|resource:IPC_REF,command:CMD,value:IPC_VALUE
fstat|resource:R,out:STAT_OUT
newfstatat|directory:R,path:PI,out:STAT_OUT,flags:FLAGS
statfs|path:PI,out:STAT_OUT
fstatfs|resource:R,out:STAT_OUT
rt_sigaction|signal:ENUM,action:SIGACTION,old_action:SIGACTION_OUT,mask_size:U64
rt_sigprocmask|command:CMD,mask:SM,old_mask:SM_OUT,mask_size:U64
rt_sigreturn|private_signal_frame:PRIVATE_REF
clock_gettime|clock:CMD,out:CLOCK_OUT
gettimeofday|out:CLOCK_OUT,timezone:NULL
clock_nanosleep|clock:CMD,flags:FLAGS,requested:TIME,remaining:CLOCK_OUT
nanosleep|requested:TIME,remaining:CLOCK_OUT
fcntl|resource:R,command:CMD,value:FD_VALUE
close|resource:R
dup|resource:R
dup2|resource:R,destination:FD_SLOT
dup3|resource:R,destination:FD_SLOT,flags:FLAGS
pipe2|out:RESOURCE_PAIR_OUT,flags:FLAGS
getpid|
getppid|
gettid|
getuid|
geteuid|
getgid|
getegid|
getgroups|count:U32,out:IDENTITY_OUT
getrlimit|limit_kind:ENUM,out:LIMIT_OUT
prlimit64|target:SELF,limit_kind:ENUM,new_limit:NULL,old_limit:LIMIT_OUT
sched_getaffinity|target:SELF,length:U64,out:BO
uname|out:IDENTITY_OUT
lseek|resource:R,offset:I64,command:CMD
fsync|resource:R
fdatasync|resource:R
ftruncate|resource:R,length:U64
fchmod|resource:R,mode:U32
fchown|resource:R,uid:SELF_UID,gid:SELF_GID
umask|mode:U32
futex|address:PRIVATE_REF,command:CMD,value:U32,timeout:TIME,second_address:NULL,third_value:U32
sched_yield|'''
    scalar_types['I32']=dict(signed=True,bits=32,range='-2^31..2^31-1')
    flags.update({'epoll_create1':['EPOLL_CLOEXEC'],'dup3':['O_CLOEXEC'],'msync':['MS_SYNC','MS_ASYNC','MS_INVALIDATE'],'semget':['IPC_CREAT','IPC_EXCL','OWNER_READ','OWNER_WRITE'],'shmget':['IPC_CREAT','IPC_EXCL','OWNER_READ','OWNER_WRITE'],'shmat':['SHM_RDONLY'],'clock_nanosleep':['TIMER_ABSTIME'],'wait4':['WNOHANG','WUNTRACED','WCONTINUED'],'waitid':['WEXITED','WSTOPPED','WCONTINUED','WNOHANG','WNOWAIT']})
    commands['clock_nanosleep']=['CLOCK_MONOTONIC','CLOCK_BOOTTIME','CLOCK_REALTIME']
    enum_domains={'domain':['AF_UNIX'],'protocol':[0],'level':['SOL_SOCKET'],'target_kind':['P_PID','P_PIDFD'],'signal':['SIGSTOP','SIGTERM','SIGCONT','SIGINT','SIGCHLD','SIGPIPE','SIGALRM','SIGHUP','SIGUSR1','SIGUSR2','SIGQUIT','SIGSEGV','SIGBUS','SIGILL','SIGFPE','SIGABRT'],'limit_kind':['RLIMIT_NOFILE','RLIMIT_AS','RLIMIT_DATA','RLIMIT_STACK','RLIMIT_CORE','RLIMIT_NPROC','RLIMIT_CPU','RLIMIT_FSIZE','RLIMIT_MEMLOCK']}
    compound_types={
      'R':'Mandatory retained RESOURCE_REF, complete committed label; no numeric identity-only ref.',
      'R_OPT':'Retained RESOURCE_REF or NONE only for anonymous mapping; backingNONE requiresMAP_ANONYMOUS and offset0.',
      'BI':'Mandatory counted immutable byte input copy, exact declaredlength; emptyallowsNULL.', 'BO':'Entire counted output range privately writable, no partial success accepted as full result; emptyallowsNULL.',
      'VI':'Counted immutable vector of BI; exactcount and checked sumlength; depth<=2, no aliases to control/outputstate.', 'VO':'Counted private writable vector of BO; exactcount/sumlength; validateallbeforeeffect.',
      'MI':'Immutable message record:vectorcount+VI, exactapprovedpeer/channel identity, no unsolicitedSCM_RIGHTS, controlcount0 except sourceauthorized sendercredential metadata; pointers validated before use.',
      'MO':'Private writable message record/vectorbuffers; controls only independently validated sendercredentials/PIDFD metadata, unsolicitedSCM_RIGHTS rejected+quarantined; no received handle authority until labelschecked.',
      'PI':'Counted immutable canonical path bytes; noNUL/dot/dotdot/escape; trustedadapter validates Linux terminator without interpreting arbitrarytype.',
      'AI':'Immutable exact AF_UNIX enrolledendpoint address; no network/DNS/caller pathselection.', 'AO':'Private writable endpointmetadata only, boundedlength; outputoptional when declaredlength0.',
      'TIME':'NONE for no wait where sourceoperationpermits, otherwise unsigned ns<=max_wait_ns; no unlimited negative timeout; platform signed sentinel normalized only by approvedadapter.',
      'ADDR':'Private owned addressrange or NONE only for allocation-chosen address; no remap ofcode/guard/otherresource; overflowreject.',
      'PRIVATE_REF':'Retained private subject range/handle, exact currentprocesscontext; no foreignpointer.',
      'CHILD':'Exact retained enginechild registry identity, not PID/name-only; zero/all-child selectors forbidden unless complete ownedchildset proven.',
      'SELF':'Currentsubject only; platform pid0 self normalized, no arbitraryprocess.', 'SELF_UID':'CurrentengineUID or source-no-change sentinel, neverotherUID.', 'SELF_GID':'CurrentengineGID or source-no-change sentinel, neverotherGID.',
      'FD_SLOT':'Unprotected destination slot reserved under max_descriptors; anyalias of protectedslot/otherprocessdenies.',
      'IPC_KEY':'Private engine namespace key; must resolve to approvedIPCbirth; globalkeyauthority forbidden.', 'IPC_REF':'ExactengineprivateIPC retainedidentity, no otherslot/hostnamespace.',
      'IPC_VALUE':'Commandtagged union:IPC_STAT=privatewritablemetadata;IPC_RMID=no payload;GETVAL/GETALL=boundedoutput;SETVAL/SETALL=boundedprivateengine values; any other variantreject.',
      'SEMOPS':'Counted immutable array(indexu32,delta_i16,flags subset IPC_NOWAIT/SEM_UNDO); indexes/count privateobjectbounds; no hosteffect.',
      'FD_VALUE':'Commandtagged union:F_GETFD/F_GETFL/F_GET_SEALS=NONE;F_SETFD=FD_CLOEXEC only;F_SETFL=O_NONBLOCK only;F_SETLK/F_SETLKW=privateengine lock(type READ/WRITE/UNLOCK,whenceSTART/CURRENT/END,checkedrange). Unknown command/valuevariantreject.',
      'SIGACTION':'NONE for query, or exact DEFAULT/IGNORE/approved immutablecode handler + boundedmask + flags SA_RESTART,SA_SIGINFO,SA_ONSTACK; no callerexecutable address.',
      'SIGACTION_OUT':'NONE or privatewritable exactcanonical previoussigaction; no arbitrarycall.', 'SM':'NONE or immutable finite set from exact signal enum; no pointerloop; sizeexact ABI manifest.',
      'SM_OUT':'NONE or privatewritable signalset; entirelengthvalidated.', 'PO':'Exactcount vector(retainedresource,eventsubsetREAD/WRITE/HANGUP/ERROR,private result); all source FDpredicates enforced.',
      'EV':'Single immutable epollevent(retainedtarget,eventsubsetREAD/WRITE/HANGUP/ERROR,opaqueprivatecookie); ctlDEL no event payload; other commandsrequireexactrecord.',
      'EO':'Exactcount writable epollevent records; returnedcount<=declared count; each eventtargetalreadyapproved.',
      'NULL':'Must be absent/zero; any nonNULL rejects.',
      'RESOURCE_PAIR_OUT':'Privatewritable pair; both resulting handles committedengineprivate labels atomically beforevisibility.',
      'TID_OUT':'NONE or privatewritable currentchildTID field, source cloneflags determinepresence, no foreignprocesswrite.',
      'STATUS_OUT':'NONE or privatewritable ownedchild status record, approvedwaittarget only.', 'USAGE_OUT':'NONE or privatewritable bounded ownedchild usage record.',
      'STAT_OUT':'Privatewritable metadata only from approved retainedresource:birth/class/owner/size/mode; never contents or secretpayload.',
      'CLOCK_OUT':'NONE only when optional output, else privatewritable seconds/nanoseconds pair; overflow/noncanonicalnsec rejects.',
      'IDENTITY_OUT':'Privatewritable currentprocess/kernel identity metadata only, no otherprocess/sessionsecret.',
      'LIMIT_OUT':'Privatewritable currentsubject resource-limit pair; queryonly, never raisingquota.'}
    returns={'READ_BUFFER':'u64 actualbytes<=length','WRITE_BUFFER':'u64 consumedbytes<=length','VECTOR_READ':'u64 actualbytes<=sumlengths','VECTOR_WRITE':'u64 consumedbytes<=sumlengths','PATH':'operationdefined retainednewhandle or successbool; mutations remainprivateengine; no handlebeforelabel','SOCKET':'retainedenrolledsocket handle or successbool; no outsidepeer','WAIT':'u32 readycount<=count plus exact ownedresources only','MEMORY':'retainedprivate range withinreservation or successbool; nonexec','PROCESS':'retainedapprovedchildbirth or ownedchildstatus or terminalexit; no otherprocess','IPC':'retainedprivateengine IPC or boundedvalues or successbool','METADATA':'canonical approvedmetadata record only','SIGNAL_LOCAL':'previousapprovedsignalstate or successbool','CLOCK':'canonical bounded clock/time or successbool','FD_CONTROL':'retainedprivatehandle/queryvalue/successbool, no authoritywidening','IDENTITY_LOCAL':'currentidentity/limits only','PRIVATE_CONTROL':'privatecontrol result, no externalresource effect'}
    for line in variant_specs.splitlines():
        opname,params=line.split('|');fields=[dict(name=f.split(':')[0],type=f.split(':')[1]) for f in params.split(',') if f]
        variants[opname]=dict(operation=opname,ordered_fields=fields,mandatory='All listed fields present; NONE allowed only by exact type/command variant; every unlisted field forbidden',scalar_domains=scalar_types,enum_domains=enum_domains,compound_type_table=compound_types,command_applicability='REQUIRED' if any(f['type']=='CMD' for f in fields) else 'FORBIDDEN',flags_applicability='Only named FLAGS fields; unmappedbit/symbol rejects',quota_delta='length bytes,vectorcount entries,pathcountedbytes,one operation; allocation reserves positive bytes/handles/children/IPCobject; release only exact independent destruction; failedunknown reservesuntilreconciled',special_constraints='mode<=0777 and no group/otherauthority outsideprivateengine; sockets AF_UNIX only; protections onlyREAD/WRITE noEXEC; READONLYbacking cannotWRITE; resource clone/inheritance exactlyclosedlabel policy; source originalpredicate remains conjunctive')
    all_operations={r['LOGICAL_OPERATION'] for r in ir['rules']};assert set(variants)==all_operations
    exact_returns={}
    def ret(names,schema):
        for name in names.split():exact_returns[name]=schema
    ret('read pread64 write pwrite64 readv writev sendmsg recvmsg sendto recvfrom getrandom','u64 actual_count<=declared requested bytes or checked vector sum; outputcopy exactlyactual_count only; shortresult distinct from complete worksuccess')
    ret('openat socket accept4 dup dup2 dup3 epoll_create1','Retained RESOURCE_REF for exactnew object, committedlabel beforevisibility; invalid/rawnumeric-only handle never success')
    ret('readlinkat','u64 copied_bytes<=length; exactthatmany path bytes inout, no implicitNUL/displayconversion; truncation returned as incomplete outcome, never fullpathproof')
    ret('getdents64','u64 copied_bytes<=length; out exactcanonical directorymetadata entries(namecountedbytes,retainedinodeidentity,typeenum), entireentry boundaries checked; partial/unrecognizedentry=>UNKNOWN')
    ret('renameat renameat2 unlinkat mkdirat bind connect listen shutdown setsockopt epoll_ctl munmap mprotect madvise msync fchmod fchown fsync fdatasync ftruncate close shmdt rt_sigaction rt_sigprocmask rt_sigreturn sched_yield','BOOL true only on verifiedcompleteoperation; declared optionaloutrecords copied exactly or resultUNKNOWN; no partialsuccess receipt')
    ret('getsockopt','u64 actual_output_bytes<=length plus exactsourcecommand result:SO_PEERCRED=>pid/u32uid/u32gid;SO_PEERPIDFD=>retainedtemporaryobservationref;SO_ERROR=>boundedi32error; no arbitraryoptionoutput')
    ret('poll ppoll epoll_wait','u32 ready_count<=requestedcount; exactcanonical events only for alreadyapprovedretainedresources; duplicates/unmappedtarget=>UNKNOWN')
    ret('mmap brk','Retained PRIVATE_RANGE(address+u64length+subjectbinding); exact requestedownership/nonexec/quotabounds checked; nativefailure sentinel or unchangedoldbreak when requestedchangefailed=>ERROR')
    ret('fork clone','Retained approved child birth PROCESS resource plus canonical parent/child branch enum; child noeligibility until complete committedlabels independentlyobserved')
    ret('wait4 waitid','Ownedchildstatus record(retainedbirth,exit_or_signal enum,status_i32,usage_u64fields); NONREADY distinct taggedvariant when allowedWNOHANG; no unknownchild')
    ret('pidfd_send_signal','BOOL true means operationaccepted for exactretainedtarget/signal, not proofprocessstopped/extinct; independentobserver stillrequired')
    ret('exit exit_group','NEVER_RETURNS; processend is not successfulworkreply, independentlyobserved extinction needed')
    ret('semget shmget','Retained privateengine IPC_REF plus exactcommittednamespace/birth identity; no rawID-only authority')
    ret('semop semtimedop','BOOL verifiedcompleteprivateIPC operation, no sourceoutsidecompartment')
    ret('semctl shmctl','Exact commandtagged result:GETVAL=>u32;GETALL=>u32count+u32values withinobjectbounds;IPC_STAT=>boundedcanonical privateIPCmetadata;SETVAL/SETALL/IPC_RMID=>BOOL; othersERROR')
    ret('shmat','Retained private IPC-backed PRIVATE_RANGE withinreservedbytes, never executable/foreignnamespace')
    ret('fstat newfstatat statfs fstatfs','STAT_OUT canonical approvedmetadata only, exactfields dev_u64,inode_u64,birthdigest32,ownerUID_u32,ownerGID_u32,size_u64,mode_u32,type_enum,blocks_u64,blocksize_u64; unsupportedfield=>UNKNOWN, no arbitrarynativepaddingbytes')
    ret('clock_gettime gettimeofday','CLOCK_OUT(seconds_i64,nanoseconds_u32<1000000000), exactclockidentity; nativeunit conversionchecked; infinity/overflow=>ERROR')
    ret('clock_nanosleep nanosleep','BOOL completedwait or taggedINTERRUPTED remainingTIME; remaining never interpreted as completedwait/work')
    ret('fcntl','Exact commandtaggedresult:F_GETFD/F_GETFL/F_GET_SEALS=>knownsymbolset withunknownbitreject;F_SETFD/F_SETFL/F_SETLK/F_SETLKW=>BOOL; unknowncommandERROR')
    ret('pipe2','Exactlytwo retainedprivateengine handles atomicallycommitted and reserved; partialcreation=>UNKNOWN/cleanup, notsuccess')
    ret('getpid getppid gettid getuid geteuid getgid getegid','u32 currentpid/tid/uid/gid or approvedparentpid as operationselects; returnednumber alone not nativeidentityauthority')
    ret('getgroups','u32 actual_or_required_count; if requestedcount0 noentries, else exactactualcount u32GIDs<=requestedcount; currentprocessgroups only')
    ret('getrlimit prlimit64','LIMIT_OUT(current_u64,max_u64); queryonly currentprocess; platforminfinity represented tagINFINITY nottruncatedinteger')
    ret('sched_getaffinity','u64 copiedbytes<=length, exactcurrentprocess CPUmask; no foreigntarget')
    ret('uname','Canonical strictboundedUTF8 systemidentity fields(sysname,nodename,release,version,machine); no nativepadding/localeconversion')
    ret('lseek','i64 resulting_offset>=0; checkedsourceposition update on exactretainedprivateengine resource; rawerror=-1 never validnegativeoffset')
    ret('umask','u32 previousmask in0..0777; currentnewmask confinedprivateprocess, no authorityexport')
    ret('futex','u32 awakened_count<=requestedcount forWAKE; WAIT=>BOOLorboundedtimeout/interruptederror; privateaddresses only, no externalprocessauthority')
    assert set(exact_returns)==all_operations
    for op,var in variants.items():
        field_domains={}
        for field in var['ordered_fields']:
            if field['type']!='FLAGS':continue
            name=field['name'];domain=flags.get(op,[])
            if name=='protection':domain=['PROT_READ','PROT_WRITE']
            if name=='socket_type':domain=['SOCK_STREAM','SOCK_SEQPACKET','SOCK_CLOEXEC','SOCK_NONBLOCK']
            field_domains[name]=dict(known_symbols=domain,required=[],forbidden=['unknownsymbol','PROT_EXEC','MAP_SHARED','foreignnamespace'],unknown='REJECT',encoding='Canonical closed symbolic set; numeric OS masks are futureABItranslation only')
        var['per_field_flag_domains']=field_domains;var['RETURN_SCHEMA']=exact_returns[op]
    mapped=[]
    for row in ir['rules']:
        op=row['LOGICAL_OPERATION'];fid=row['OPERATION_CLASS']
        mapped.append(dict(RULE_ID=row['RULE_ID'],FAMILY_ID=fid,PARTICIPANT=row['PARTICIPANT'],OPERATION=op,RESOURCE=row['RESOURCE_CLASS'],ARGUMENT_BINDINGS=dict(normalized_schema=variants[op],original_source_predicate=row['ARGUMENT_PREDICATES']['logical_predicate'],scalar_types=scalar_types,reserved='Every unlisted field absent; all listed fields typed; no truncated/sign-reinterpreted values',overflow='reject; no truncation'),FLAG_BINDINGS=variants[op]['per_field_flag_domains'],COMMAND_BINDINGS=dict(known=commands.get(op,[]),applicability=variants[op]['command_applicability'],no_command='FORBIDDEN means field must be absent; REQUIRED with empty enum means operation unsupported/DENY, never allow',unknown='REJECT'),POINTER_BINDINGS=pointer,QUOTA_BINDINGS=[q['QUOTA_ID'] for q in quotas],RETURN_BINDINGS=exact_returns[op],ACTION='CONDITIONAL',FAILURE='No qualification and no success receipt',UNKNOWN='No operation / preserve uncertain outcome',exact_mapping='Originalsource argument slot i maps ordered_fields[i] in canonical logical operation variant; architecture ABI expansion onlyfutureadapter. Resource-slot literals refer expectedretained handlebinding; pointer0 refersNULL; scalars exacttypedcompare. Emptyflagdomain requiresno flags.'))
    # Give formerly opaque generic predicates a finite decision vocabulary; unsupported cases deny.
    operator_semantics={
      'PROCESS_LOCAL_MEMORY_CLOCK_SIGNAL_HANDLER_OR_IDENTITY_ONLY':'Require operation family in MEMORY,CLOCK,SIGNAL_LOCAL,IDENTITY_LOCAL,PRIVATE_CONTROL; every referenced address range privately owned by subject, signal handler approved immutable code, clock from exact enumerated clock IDs, identity target self only, resource effect confined to private subject. No external resource/credential/role/namespace mutation. If normalization cannot establish these facts=>UNKNOWN.',
      'SEALED_RESOURCE_QUOTAS':'Apply all applicable quota reservations in canonical quota-ID order before effect; atomic reserve, no overflow/reset; uncertain effects retain reservation.',
      'FD_IN':'Resolve source numeric slot selector to normalized RESOURCE_REF; verify complete committed retained object binding equals one of immutable expected slot handles; integer equality alone insufficient.',
      'FD_LABEL_IN':'Require current committed label resource_class and authority action in exact approved set; retained identity stable through use. For a path-typed originalslot (statfs), atomically resolvepath via closed retainedroot adapter to a retainedobject resource then testlabel, never treatpathbytes asFD or reopen aftercheck. Unsupported retainedresolution=>UNKNOWN.',
      'FLAGS_SUBSET':'Decode platform bits to closed symbolic set using approved ABI manifest; reject any unmapped bit; require subset of sourcepredicate and new peroperation known set.',
      'ARG_EQ':'Resolve indexed original logical argument via variant ordered_fields; resource vs literal slot compares independently retained expected slot binding, pointer vs0 requiresNULL, scalar exacttyped equality. Any unsupported comparison/unknownslot=>UNKNOWN; no rawFDnumber-only authority.',
      'ARG_IN':'Typed membership in exact finite predicate literal set after normalization; no ambient enum expansion.',
      'AND':'FALSE if any false, UNKNOWN if nofalse and someunknown, TRUE otherwise.',
      'TRUE':'True only for no additional predicate; all family/common constraints still mandatory.',
      'NO_PROT_EXEC':'Reject any requested executable mapping/protection, including W+X.',
      'ANON_PRIVATE_OR_APPROVED_RO_MAPPING':'Either private anonymous nonexec range in subject quota or immutable approved read-only file mapping; writes to readonly backing deny.',
      'REQUEST_LENGTH_LE':'Exact normalized requested byte length<=literal bound andquota; otherwise reject.'}
    operator_semantics.update({
      'FD_EQ':'LikeFD_IN with singleton expected slot; compare retained identity+label, notinteger.',
      'FD_NOT_IN':'Normalized retained handle is not any protected expected slot; unknown relation denies.',
      'EVERY_POLLED_FD_IN':'Each vector entry resolves to one immutable expected allowed slot retainedidentity; all entries validated before waiting, count exact/withinquota; emptyvector only explicitzero wait.',
      'EVERY_POLLED_FD_LABEL_IN':'Each vector entry committedlabelclass belongs literalset; same lifetime/generation/context; events only READABLE,WRITABLE,HANGUP,ERROR,EXIT; no new handle authority.',
      'ALL_PATHS_LABEL_IN':'Every source/destination path endpoint resolves under retained directory capability to committedlabel in literalset; mutation permitted only PGDATA/PGSOCKET engineprivate; APPROVED_CODE_RO read-only. Atomic retainedresolution through operation, never name-only reopen.',
      'DENY_SYMLINK_ESCAPE':'Any resolution step outside committed root/identity or unresolved symlink/rename race rejects whole operation; no partial rename or fallbackpath.',
      'NO_HOST_OR_OTHER_SLOT_PATH':'Reject any pathobject labeledHOST or subject!=current slot except explicitly immutable approved public material.',
      'SOCKET_DOMAIN_AND_PATH_LABEL':'ExactAF_UNIX, approved endpoint retained labelPGSOCKET; no externaladdress, no arbitrary peer. Creation/bootstrap/accept only POSTMASTER and fixed enrolled sessionplan; nativeparticipants only fixed inheritedchannel.',
      'ENGINE_CHILD_ONLY':'RequirePARTICIPANT=POSTMASTER and exact approved unused enginechildbirthplan; child noeligibility until independently observed nativebirthidentity+complete labels.',
      'CLONE_FLAGS_SUBSET':'Normalizeflags to symbols; require subsetof exactliteralset and no namespace/share-code/credential changes. Every unrecognized bit rejects.',
      'SAME_TEST_NAMESPACES_AND_CGROUP':'Compare all child namespace/cgroup retainedidentities to approved enginecompartment; everyfield equal, no newhost/otherslot namespace.',
      'ENGINE_OWNED_DESCRIPTOR_ONLY':'PARTICIPANT=POSTMASTER and all source/destination handles retainedlabelsubject belongs sameprivateengine; cannot duplicate anynative slot handle or overwriteprotectedFD.',
      'NO_INHERITED_NATIVE_SLOT_DESCRIPTOR':'Reject source or destination aliases ofCTX,KEY,CHANNEL,JOURNAL,publicmaterial,targetpidfd nativehandles; no descriptor-number-only tests.',
      'NO_OTHER_SLOT_OR_HOST_LABEL':'Reject retainedobject/alias label belonging othernativeparticipant orHOST; trustedbootstrap has noACTIVE exception.',
      'IPC_NAMESPACE_LABEL_ONLY':'PARTICIPANT=POSTMASTER; everyIPCobject retainedbirth belongs exactengineprivateIPCnamespace; command/permissions cannot expose otherUID/group or escape subject.',
      'ENGINE_OWNED_CHILD_SET_ONLY':'waittarget is exactindependently approved childbirth retainedreference in enginechildregistry; no processname/PID reuse; unknownchilddenies.',
      'ENGINE_INTERNAL_DESCRIPTOR_LABEL_ONLY':'PARTICIPANT=POSTMASTER; newpipe/epoll handles get engineprivate committedlabel before visibility; epolltarget everyretainedrefsameengine; no unsolicitedFDimport.',
      'METADATA_ONLY_NO_OPEN_OR_READ':'Operation result only exactdeclared metadataschema, nevercontents, executable mapping orauthority; resource identity must still pass retainedlabelchecks.',
      'DECLARED_OR_TEMP_ANCILLARY_HANDLE':'Handle is declaredslot resource or temporary senderPIDFD observation retainedfrom authenticatedsource; temporary handle onlymetadata/close and cannot become execution/credential/channel authority.'})
    unresolved_ops=set()
    def visit(v):
        if isinstance(v,dict):
            if 'op' in v and v['op'] not in operator_semantics:unresolved_ops.add(v['op'])
            for x in v.values():visit(x)
        elif isinstance(v,list):
            for x in v:visit(x)
    for row in mapped:visit(row['ARGUMENT_BINDINGS']['original_source_predicate'])
    doc('operation-families',families=families,operation_variants=variants,scalar_types=scalar_types,quota_table=quotas,operator_semantics=operator_semantics,remaining_operator_definitions=sorted(unresolved_ops),logical_default='DENY',platform_binding='Linux/ELF architecture/ABI numeric table and complete mediation adapter FUTURE_IMPLEMENTATION_DECISION/PROOF; preserve closed label IR, do not choose backend',source=ref(PRE+'scalar-operation-ir.json'))
    doc('rule-family-map',rules=mapped,total=len(mapped),mapped=len(mapped),unmapped=0,unique_families=len(families),no_claim_of_closed_until_review=True)
    # B. Frozen source availability and precise unresolved field semantics.
    required=['datid','pid','usesysid','usename','backend_start','backend_type'];view=(R/PG/'system_views.sql').read_text();proc=(R/PG/'pg_proc.dat').read_text()
    doc('stats-source-trace',SOURCE_FILE=None,SOURCE_HASH=None,FUNCTION_SOURCE_RANGE=None,VISIBILITY_MACRO_SOURCE=None,VISIBILITY_HELPER_SOURCE=None,declaration=ref(PG+'pg_proc.dat'),view=ref(PG+'system_views.sql'),pg18_function='pg_stat_get_activity',frozen_implementation_found=False,search_scope=['frozen provider inventory','read-only filename inventory under C:/Projects and C:/Users/xmz_r/Downloads; no pgstatfuncs.c found'],fields=[dict(FIELD_ID=n,QUALIFICATION_REQUIRED=True,VISIBLE_WITHOUT_ELEVATED_STATS_AUTHORITY='UNKNOWN_SOURCE_NOT_PRESENT',VISIBLE_FOR_OWN_SESSION='UNKNOWN_SOURCE_NOT_PRESENT',VISIBLE_VIA_ROLE_MEMBERSHIP='UNKNOWN_SOURCE_NOT_PRESENT',REQUIRES_PG_READ_ALL_STATS='NOT_AUTHORIZED_WITHOUT_SOURCE_PROOF',SENSITIVE='query/config/credential fields excluded; these six are constrained census metadata',ALTERNATE_NARROW_SOURCE='pg_database or pg_roles for static OID/name identity; cannot substitute backend session attribution',SELECTED_SOURCE='pg_stat_activity.'+n) for n in required],known_source_identity='six output names/prototype/view lineage known; native visibility branches and helper definitions not present',forbidden=['pg_monitor shortcut','pg_read_all_settings shortcut','pg_read_all_stats without proven required gated field','query text','credential/config secrets'],MINIMUM_AUTHORITY='UNRESOLVED_SOURCE_DEPENDENCY; never broad privilege fallback')
    # C. Semantic reference ledger (not occurrence denominator); preserve original expressions for audit.
    lexical=rd(PRE+'credential-reference-ledger.json')['references'];semantic={};noncred=[];unresolved=[];occurrences=[]
    def add(kind,referent_id,classid,expr,row,complete):
        key=kind+'|'+referent_id
        entry=semantic.setdefault(key,dict(REFERENT_KIND=kind,REFERENT_ID=referent_id,CREDENTIAL_CLASS_ID=classid,classification_complete=complete,SOURCE_LOCATIONS=[],REFERENCE_EXPRESSIONS=[]))
        entry['SOURCE_LOCATIONS'].append(dict(path=row['SOURCE'],pointer=row['POINTER']));entry['REFERENCE_EXPRESSIONS'].append(expr)
        occurrences.append(key)
    for row in lexical:
        expr=original_expression(row);s=expr.lower();loc=row['SOURCE']+row['POINTER']
        if any(n in row['SOURCE'] for n in ['SHA256-MANIFEST.json','baseline-freeze.json']) or (re.fullmatch(r'[A-Za-z0-9_./:-]+\.json(?:#.*)?',expr) is not None):
            noncred.append(dict(SOURCE_LOCATION=loc,REFERENCE_EXPRESSION=expr,REFERENT_KIND='NON_CREDENTIAL_USE_OF_TERM',REFERENT_ID='evidence-path-or-hash'));continue
        if 'token' in s and not any(t in s for t in ['credential','private key','password','authenticat']) and any(t in s for t in ['mutat','barrier','exclusion','snapshot']):
            noncred.append(dict(SOURCE_LOCATION=loc,REFERENCE_EXPRESSION=expr,REFERENT_KIND='NON_CREDENTIAL_USE_OF_TERM',REFERENT_ID='mutation-protocol-token-not-authentication'));continue
        candidates=[]
        for text,cid in [('generation_transport','GENERATION_TRANSPORT'),('one_use_work_authorization','ONE_USE_WORK_AUTHORIZATION'),('postmaster_server_endpoint','POSTMASTER_SERVER_ENDPOINT')]:
            if text in s:candidates.append(cid)
        if not candidates:
            if any(t in s for t in ['read_proxy','sql authentication','proxy authentication','sql credential','sql transport']):candidates=['PROXY_ROLE_SESSION_AUTHENTICATION']
            elif 'user=postgres' in s or '--auth=trust' in s:candidates=['LEGACY_TEST_TRUST_SUPERUSER_ENDPOINT']
        if len(candidates)==1:
            cid=candidates[0]
            kind='CREDENTIAL_CLASS_REFERENCE'
            if 'observer' in row['POINTER'].lower():kind='CREDENTIAL_OBSERVER'
            elif 'issuer' in row['POINTER'].lower():kind='CREDENTIAL_ISSUER'
            elif 'custodian' in row['POINTER'].lower():kind='CREDENTIAL_CUSTODIAN'
            elif any(k in row['POINTER'].lower() for k in ['policy','transfer','expiry','replay']):kind='CREDENTIAL_POLICY'
            elif any(k in row['POINTER'].lower() for k in ['credential_ref','credential_purpose','credential_class']):kind='CREDENTIAL_PROPERTY'
            add(kind,cid+'/'+kind,cid,expr,row,True)
        else:
            # Preserve exact unresolved referent rather than mapping broad prose to a fictional credential instance.
            normalized=' '.join(expr.split());rid='UNRESOLVED_REFERENCE_EXPRESSION/'+sha(normalized.encode())
            add('CREDENTIAL_PROPERTY',rid,None,expr,row,False);unresolved.append(loc)
    entries=list(semantic.values())
    doc('semantic-credential-ledger',lexical_mentions_total=len(lexical),semantic_references=entries,semantic_references_total=len(entries),non_credential_mentions=noncred,non_credential_lexical_mentions=len(noncred),duplicate_semantic_mentions=len(occurrences)-len(entries),semantic_references_unclassified=sum(not e['classification_complete'] for e in entries),lexical_accounting='noncredential + semantic occurrences =2013; duplicates counted only after referent canonicalization; no claim regex establishes exhaustive semantic truth',unclassified_source_locations=unresolved,referent_kind_enum='CREDENTIAL_INSTANCE CREDENTIAL_CLASS_REFERENCE CREDENTIAL_PROPERTY CREDENTIAL_POLICY CREDENTIAL_OBSERVER CREDENTIAL_ISSUER CREDENTIAL_CUSTODIAN NON_CREDENTIAL_USE_OF_TERM'.split())
    classes=rd(N2+'credential-classes.json')['classes']
    doc('credential-class-contracts',carried_classes=classes,known_additional_referents=['LEGACY_TEST_TRUST_SUPERUSER_ENDPOINT','PROXY_ROLE_SESSION_AUTHENTICATION'],legacy_status='FORBIDDEN_FOR_V2_NATIVE_READER; frozen isolated test initdb trust+localpostgres not authority exception',proxy_interface=dict(PURPOSE='Authenticate one fixed ordinary READ_PROXY role/session on approved isolated TEST server',PROTOCOL='Existing PostgreSQL role/session authentication plus independently enrolled local proxy endpoint; no Package wrapper key substitution',ISSUER='DEPLOYMENT external provisioning under approved role/endpoint manifest',SUBJECT='Exact fixed READ_PROXY principal and enrolled proxy process',CUSTODIAN='Proxy only; participants receive signed nonsecret snapshot, no SQL handle',DELIVERY='Pre-enrollment protected capability channel; no caller-selected role/endpoint/auth data',AUTHENTICATION='Future mechanism must independently bind authenticated SQL session role+server endpoint+proxy birth identity to exact manifest, reject caller choice of user=postgres or alternate server; no ambient trust',AUTHORITY='Only exact approved read projection, no role/owner/SET/ADMIN privileges',TARGET_SCOPE='One isolated TEST database/server endpoint',CONTEXT='exactenrolled',GENERATION='exactcurrent',REGISTRY_REVISION='exactcurrent',USE_COUNT='One session per snapshot challenge; reconnect retires session',EXPIRY='Versioned positive bounded snapshot lease and generation continuity',TRANSFER='FORBIDDEN',DUPLICATION='FORBIDDEN',INHERITANCE='Only explicit pre-enrollment delivery',PERSISTENCE='No participant persistence; proxy private lifecycle only',REVOCATION='Session/role/endpoint/generation loss invalidates',OBSERVER='Independent HEALTH_GUARD verifies SQL role/session/server binding and proxy process',DESTRUCTION='Close session, revoke private transport; independent extinction receipt',REPLAY='Old session/challenge invalid',UNKNOWN='NOT_QUALIFIED'),mechanism_selection=dict(authority='DEPLOYMENT only, not caller/native participant',admissible='Mechanism from frozen architecture that proves above role/session/endpoint invariant with same effective ACL. No password/certificate/peer scheme invented.',classification='FUTURE_IMPLEMENTATION_DECISION only if identical logical authority and verification interface; if new trust/privilege/secret scope needed=>STATIC_DECISION_REQUIRED',remaining='Existing source fixes legacy trust but does not select ordinary proxy mechanism. Exact semantic mapping and accepted mechanism contract still subject independent review'),source=ref('scripts/validation/package_0090_native_health_qualification/qualification.py'))
    # D. Coherent snapshot + mutation epoch + generation conditional publication.
    names=['role_attribute','membership','SET_INHERIT_ADMIN_options','ownership','object_ACL','default_privilege','routine_security','routine_owner','schema_authority','configuration_authority','reader_authority','credential_authority','registry_generation_authority']
    coverage=[dict(EVENT_CLASS=n,DOMAIN='Only authority reachable from seven native participants or READ_PROXY in isolated TEST namespace/database; shared role changes included',BEGIN='Before effect can become usable, publish INVALIDATING event and increment monotonic domain revision under writer serialization; mark affected snapshots invalid',COMMIT='Publish exact poststate digest/eventcommit; affected prior snapshots remain invalid, never revalidate by same digest',ABORT='Retain revision increment/invalidation even if change aborted; prevents ABA validity',FAILURE='Missing begin/commit/source coverage=>domainUNKNOWN; no qualifying publication',INVALIDATION='Every affected snapshot/work consumed under older revision becomes ineligible') for n in names]
    doc('snapshot-mutation-contract',alternatives=[{'mechanism':'global exclusion','verdict':'Stronger than needed; no frozen requirement to stop unrelated mutations'},{'mechanism':'bounded domain exclusion','verdict':'Sufficient but stronger if complete observed revision/publication protocol exists'},{'mechanism':'coherent snapshot+mutationepoch+generationconditionalpublication','verdict':'SELECTED_LOGICAL_PROTOCOL'},{'mechanism':'before/after digest only','verdict':'INSUFFICIENT ABA and observation-to-publication race'},{'mechanism':'generation only','verdict':'INSUFFICIENT catalog mutations without generation transition'}],BARRIER_SCOPE='Native qualification authority domain only',MUTATION_DOMAIN='Reachable role/membership/owner/schema/ACL/default/routine/config/reader/credential/native registry state',MUTATION_EVENT_CLASSES=coverage,BEGIN_IDENTITY='Signed challenge binding current mutation_revision,registrytip,generation,session,context',END_IDENTITY='Signed independent observer receipt binding complete snapshot digest and exact same mutation_revision,registrytip,generation,session,context',SNAPSHOT_IDENTITY='Closed canonical codec complete19source146field projection digest',GENERATION='Exactcurrenthighwater',REGISTRY_REVISION='Exactcurrenttip',AUTHORITY_STATE_BEFORE='Complete independent authority-domain digest+revision',AUTHORITY_STATE_AFTER='Equal revision and verified complete snapshot bound to post-observation challenge, not digest equality alone',VALIDATION='All source identities/reader constraints/snapshot coherence/event coverage/current revision known true; any intervening relevant event invalidates',PUBLICATION_ORDER='Writer performs CAS(expected mutation_revision,registrytip,generation,snapshotID,workunconsumed) under same domain serialization as mutationBEGIN; append one-use qualification receipt only on exact match. MutationBEGIN before CAS invalidates; CAS before mutationBEGIN produces receipt immediately invalidated for futureuse. Consumers revalidate revision under same conditionaluse protocol, never trust old receipt alone.',INVALIDATION='Monotonic before mutation takes effect; no ABA rollback to earlier validrevision',LOSS='Observer gap/eventsequencegap/sourcehookabsence=>UNKNOWN',CRASH='PersistpendingUNKNOWN and revision highwater; no truncate-to-success/reset',TIMEOUT='Versioned positive bounded observation lease; missing/overflow=>deny',RECONNECT='Discardwholeobservation; newchallenge',RESTART='Retire old process/session/observer incarnation; newgeneration before newqualification',UNKNOWN='NOT_QUALIFIED',logical_event_coverage=len(coverage),PHYSICAL_BARRIER_IMPLEMENTATION='FUTURE_IMPLEMENTATION_PROOF',adapter_requirement='Future mediation proof must cover every mutation class and relevant source path before activation; prove begin-before-effect linearization and CAS order. Trusted HOST outside malicious-admin threat model, but governed admin mutations still routed; any unmediated relevant mutator means domainNOTCONFORMANT.',source=ref(PRE+'snapshot-observation-barrier.json'))
    # E. Native-scoped graph: types are codec identities unless a reachable callable effect exists.
    constructors=[
      dict(CONSTRUCTOR_ID='ROUTINE_EXECUTION',SOURCE='pg_proc.oid/proowner/proacl/prosecdef/proconfig + separate executeACL origins',FROM='reader or SET/INHERIT reachable role',TO='routine OID',EDGE_TYPE='DIRECT_ACL or PUBLIC_ACL',APPLICABILITY='Only if caller has effective EXECUTE and fixed source path actually invokes routine',TRANSITIVE='Effect reachability only after entry condition true',EFFECT='INVOKER retains currentrole; DEFINER uses exact owner for duration, scoped proconfig/searchpath checked; no execution effect merely existence',UNKNOWN='Unsupported body/effect/sourcepath=>NOTQUALIFIED'),
      dict(CONSTRUCTOR_ID='SECURITY_DEFINER',SOURCE='pg_proc.prosecdef/proowner/proconfig',FROM='reachable executable routine',TO='exact owner authority context',EDGE_TYPE='SECURITY_DEFINER_PATH',APPLICABILITY='Only executable routine transition with approved exact body/context',TRANSITIVE='Traverse owner effects separately from membership',EFFECT='Enter owner context for function only; do not pretend membership/SET',UNKNOWN='Missing body/context allowlist=>NOTQUALIFIED'),
      dict(CONSTRUCTOR_ID='TYPE_CODEC_IDENTITY',SOURCE='Closed source/type/field codec table',FROM='source field',TO='canonical primitive codec',EDGE_TYPE='NO_NATIVE_AUTHORITY_EDGE_REQUIRED',APPLICABILITY='Snapshot bytes decoded solely by closed canonical primitive decoders; never arbitrary PG type input',TRANSITIVE=False,EFFECT='Type existence/OID not privilege; no new authority edge',UNKNOWN='Unknowncodec=>preparsereject'),
      dict(CONSTRUCTOR_ID='SOURCE_TYPE_CALLABLE',SOURCE='Source producer fixed SQL types and pg_type supportcallables where actually invoked',FROM='fixedproducer expression',TO='exact invokedtypefunction',EDGE_TYPE='ROUTINE_EXECUTION existing semantic transition',APPLICABILITY='Only if actual producer parse/type path invokes callable, not because type exists',TRANSITIVE='Reuse routine effect semantics',EFFECT='Needs source-approved callableeffect manifest or rejectunsupportedsource',UNKNOWN='Native sourceparse/typecallable absence=>NOTQUALIFIED'),
      dict(CONSTRUCTOR_ID='FUTURE_DEFAULT_PRIVILEGES',SOURCE='pg_default_acl.defaclrole/defaclnamespace/defaclobjtype/defaclacl + creator CREATE/schema rights',FROM='exact creatorrole/objectclass/schemascope',TO='future object -> ACLgrantee/privilege/grantoption',EDGE_TYPE='DEFAULT_PRIVILEGE_EFFECT',APPLICABILITY='Only if creator can create target objectclass in scope; globaldefault applies then schemaadditionalrights; retain exact creatorrole, not inherited role whose defaults incidentally exist',TRANSITIVE='Evaluate future object effect only; never existingobjectACL',EFFECT='Potentialfuture rights invalidating native noauthority invariant if creator reachable',UNKNOWN='Unknown create/effect scope=>NOTQUALIFIED')]
    doc('native-effect-graph',constructors=constructors,base_semantics=ref(PG+'acl.c'),default_semantics=ref(PG+'aclchk.c'),distinct_dimensions=['MEMBER_OF','INHERIT','SET','ADMIN','OWNERSHIP','DIRECT_ACL','PUBLIC_ACL','DEFAULT_PRIVILEGE_EFFECT','SECURITY_DEFINER_PATH','CREATEROLE','SUPERUSER','BYPASSRLS','BOOTSTRAP'],scope_fence='Only NATIVE qualification; never V2-PARTITIONS complete graph',missing_source_families='Codec-only type edges removed; producer callable/type/defaultargument source effects remain explicit until fixed source plan/effect manifest proved. Do not silently drop source-side effects just because decoder pure.',source_relations=19,projected_fields=146,predicate_count=26)
    # F. Derivation consumes prior five outputs; unknown input remains an exact witness, never YES.
    invariants=['NO_MUTATION_PATH','NO_ROLE_ESCALATION_PATH','NO_CREDENTIAL_SECRET_PATH','NO_GENERIC_SQL_AUTHORITY','NO_ARBITRARY_OBJECT_AUTHORITY']
    doc('reader-authority-derivation',inputs=[ORDER[i] for i in range(5)],START_NODE='Exactly enrolled ordinary READ_PROXY principal; no postgres authority',fixpoint=dict(MEMBER='closure allmemberedges; preserve options',INHERIT='closure only inherit_option=true; perPG18 edge option not roleattribute shortcut',SET='closure only set_option=true; never relabelINHERIT',ADMIN='memberclosure reaches grant with admin_option; self false unlesssuperuser per frozenacl.c',OWNERSHIP='Owner implicit authority separate from ACL; SETreachable owner retains typed SETpath',SECURITY_DEFINER='Only executable relevant routine switches toowner scopedexecution; unapprovedeffectUNKNOWN',DEFAULT='Futurecreator identity/schema/class paths separate from existing ACL',PUBLIC='No rolemembership; addPUBLICorigin grants applicable to everyprincipal',cycle='Visited typednode/state; no depthlimit; keep origin paths',stop='Finitecomplete source universe reaches stable typedstate set',UNKNOWN='Any needed edge/source/identity missing=>qualification failure'),invariants=[dict(ID=n,VALUE='UNKNOWN',exact_missing_inputs=['PG18 visibility implementation/required projection minimal privilege','Exact fixed producer call/parse/effect allowlist','Proxy class effective role/endpoint binding and full PUBLIC/default/owner graph']) for n in invariants],no_broad_privilege_exception=True,actual_authority_graph_available=False,reason='No actual reader ACL expected-manifest or complete producer effect allowlist exists in frozen inputs; cannot derive no-path from desired invariants alone')
    doc('closure-preservation',CLOSED_CONTRACTS_REOPENED=0,CONTRADICTIONS_DISCOVERED=0,preserved=['N1-LABEL-IR-ATOMICITY','N1-READER-PREPARSE-GATE','N1-CONFIG-SECRET-EXCLUSION','N1-CATALOG-CODEC-TYPE-TABLE','ABI','generation','registry','completed-work anchors'],deferred=['N1-QUALIFICATION-INPUT-RESOLUTION','N1-SUBSTITUTION-STATIC-WITNESSES'])
    print(json.dumps(dict(generated=True,targets=6,logical_rules=len(mapped),families=len(families),remaining_operators=len(unresolved_ops),lexical=len(lexical),semantic=len(entries),semantic_unclassified=sum(not e['classification_complete'] for e in entries),mutation_classes=len(coverage),live=False)))
if __name__=='__main__':main()
