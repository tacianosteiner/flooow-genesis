import pathlib,json,hashlib,tarfile,subprocess,ctypes as C,uuid
r=pathlib.Path(__file__).parent;p=r.parent/'managed-host-preparation-v5';e=json.loads((p/'managed-execution.json').read_text(encoding='utf-8-sig'))
with tarfile.open(p/'runtime-bundle.tar','r:') as t:files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
manifest=json.loads(files['probe/input-manifest.json']);assert all(hashlib.sha256(files[k]).hexdigest()==v for k,v in manifest.items())
proposal=json.loads(files['probe/policy-proposal.json']);ph=hashlib.sha256(files['probe/policy-proposal.json']).hexdigest()
assert hashlib.sha256(files['probe/self-session-probe']).hexdigest()==e['compiled_publisher_sha256']
rows=[json.loads(x) for x in e['stdout'].splitlines() if x.startswith('{"kind":')]
held=[x for x in rows if x['kind'].startswith('POLICY_SCOPED_DECISION_CANDIDATE_')];assert len(held)==2
assert held[0]['sender_pid']==held[1]['sender_pid']==e['actual_policy_proposal_custodian_pid']
for key in ('device','inode','private_record_sha256','proposal_sha256','start_boottime_us','finish_boottime_us'):assert held[0][key]==held[1][key]
assert held[0]['proposal_sha256']==ph
boot=next(x.split('|',1)[1] for x in e['stdout'].splitlines() if x.startswith('BOOTSTRAP_OS_BOOT_ID|'))
timens=int(next(x.split('|',1)[1] for x in e['stdout'].splitlines() if x.startswith('BOOTSTRAP_TIME_NAMESPACE_INODE|')))
b=next(x for x in rows if x['kind']=='RAW_BOOTSTRAP_EXPECTATION_FROZEN_BEFORE_CANDIDATE')
class Raw(C.LittleEndianStructure):
 _fields_=[('magic',C.c_uint32),('version',C.c_uint32),('db',C.c_uint32),('reader',C.c_uint32),('system',C.c_uint64),('timens',C.c_uint64),('start',C.c_uint64),('finish',C.c_uint64),('server',C.c_int64),('memberships',C.c_uint64),('sessions',C.c_uint64),('boot',C.c_ubyte*16),('flags',C.c_ubyte*7),('name',C.c_char*64)]
class Policy(C.LittleEndianStructure):
 _fields_=[('version',C.c_uint32),('source_state',C.c_uint32),('activation_state',C.c_uint32),('decision_state',C.c_uint32),('age',C.c_uint64),('lease',C.c_uint64),('rows',C.c_uint64),('frame',C.c_uint64),('start',C.c_uint64),('finish',C.c_uint64),('raw',Raw),('name',C.c_char*64),('sha',C.c_char*65),('request',C.c_ubyte*172)]
x=Policy();x.version=2;x.source_state=x.activation_state=x.decision_state=1
v=proposal['proposed_values'];x.age=v['original_source_max_age_us'];x.lease=v['challenge_lease_us'];x.rows=v['max_rows'];x.frame=v['max_private_frame_bytes'];x.start=held[0]['start_boottime_us'];x.finish=held[0]['finish_boottime_us'];x.name=proposal['proposed_policy_version'].encode();x.sha=ph.encode()
x.raw.magic=0x42505231;x.raw.version=1;x.raw.db=b['database_oid'];x.raw.reader=b['reader_oid'];x.raw.system=int(b['system_identifier_u64']);x.raw.server=int(b['server_start_pg_us']);x.raw.timens=timens;x.raw.start=b['original_started_us'];x.raw.finish=b['original_finished_us'];x.raw.boot[:]=uuid.UUID(boot).bytes;x.raw.flags[0]=1;x.raw.name=b'flooow_reader'
request=json.loads((p/'explicit-scoped-decision-request.json').read_text(encoding='utf-8-sig'))
encoded=bytes.fromhex(request['parent_delegation_reference_sha256'])+bytes.fromhex(ph)+uuid.UUID(request['manager']['daemon_id']).bytes+bytes.fromhex(request['image'][7:])+bytes.fromhex(request['container'])+request['custodian_pid'].to_bytes(4,'big')+request['custodian_start_ticks'].to_bytes(8,'big')+request['pid_namespace_inode'].to_bytes(8,'big')+request['time_namespace_inode'].to_bytes(8,'big')
assert len(encoded)==172 and encoded.hex()==request['request_hex']
assert hashlib.sha256(b'ISSUE_PENDING_POLICY_DECISION '+encoded.hex().encode('ascii')+b'\n').hexdigest()==request['control_bytes_sha256']
assert request['image']==e['immutable_image_id'] and request['container']==e['runtime_container_id'] and request['manager']==e['manager_before']==e['manager_after']
parent=(r.parent/'authority-receipt.json').read_bytes();assert hashlib.sha256(parent).hexdigest()==request['parent_delegation_reference_sha256']
meta=e['actual_policy_proposal_custodian_birth_executable_namespace']['stdout'].splitlines()
stat=meta[2];assert int(stat.split(' ',1)[0])==request['custodian_pid']
assert int(stat[stat.rfind(')')+2:].split()[19])==request['custodian_start_ticks']
assert 'pid:['+str(request['pid_namespace_inode'])+']' in meta and 'time:['+str(request['time_namespace_inode'])+']' in meta
x.request[:]=encoded
actual=hashlib.sha256(bytes(x)).hexdigest();assert actual==held[0]['private_record_sha256'],(actual,held[0]['private_record_sha256'],C.sizeof(x))
q=subprocess.run(['docker','--context','desktop-linux','image','inspect',e['immutable_image_id']],capture_output=True,text=True,timeout=15);assert q.returncode==0;im=json.loads(q.stdout)[0];assert im['Id']==e['immutable_image_id'] and im['Parent']==e['base_image']
r.joinpath('reconstruction.json').write_text(json.dumps(dict(all_checks=True,elf_hash=e['compiled_publisher_sha256'],proposal_hash=ph,raw_size=C.sizeof(Raw),private_projection_size=C.sizeof(Policy),independently_reconstructed_private_record_sha256=actual,custodian_pid=e['actual_policy_proposal_custodian_pid'],image_metadata=im),indent=2)+'\n')
print(json.dumps(dict(all_checks=True,private_record_sha256=actual)))


