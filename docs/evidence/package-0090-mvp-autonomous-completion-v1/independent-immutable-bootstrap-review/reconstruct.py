import pathlib,json,hashlib,uuid
root=pathlib.Path(__file__).parent
raw=root.joinpath('execution.txt').read_bytes()
lines=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig').splitlines()
def single(prefix):
 values=[x[len(prefix):] for x in lines if x.startswith(prefix)]
 assert len(values)==1
 return values[0]
p=json.loads(single('BOOTSTRAP_PG|'))
system=bytes.fromhex(p['database_system_identifier_wire_hex']);server=bytes.fromhex(p['server_start_pg_wire_hex'])
assert len(system)==len(server)==8
assert int.from_bytes(system,'big',signed=True)==int(p['database_system_identifier_sql_int64'])
assert int.from_bytes(server,'big',signed=True)==int(p['server_start_pg_us'])
assert 0<int.from_bytes(system,'big')<2**64
assert -(2**63)<int(p['server_start_pg_us'])<2**63-1
assert 0<int(p['database_oid'])<2**32 and 0<int(p['reader_role_oid'])<2**32
assert p['reader_flags']==dict(login=True,superuser=False,inherit=False,create_role=False,create_db=False,replication=False,bypass_rls=False)
assert p['reader_memberships']==p['reader_sessions_before_candidate']==0
assert uuid.UUID(single('BOOTSTRAP_OS_BOOT_ID|')).int!=0
assert 0<int(single('BOOTSTRAP_TIME_NAMESPACE_INODE|'))<2**64
observed=[json.loads(x) for x in lines if x.startswith('{"kind":')]
public=[x for x in observed if x['kind'].startswith('RAW_PUBLIC4_')]
assert len(public)==3
for row in public:
 b=bytes.fromhex(row['payload_hex']);assert hashlib.sha256(b).hexdigest()==row['sha256']
 assert b[0]==4
 offset=1;fields=[]
 for _ in range(4):
  n=b[offset];offset+=1;assert 0<n<=63 and offset+n<=len(b)
  fields.append(b[offset:offset+n].decode('ascii'));offset+=n
 assert offset==len(b)
 assert fields[0]==p['database_oid'] and fields[1]==p['reader_role_oid'] and fields[3]==p['reader_role_name']
assert max(i for i,x in enumerate(lines) if x.startswith('BOOTSTRAP_'))<min(i for i,x in enumerate(lines) if x.startswith('{"kind":'))
expected=[x for x in observed if x['kind'].startswith('RAW_BOOTSTRAP_EXPECTATION_')]
assert len(expected)==3
identity=('device','inode','original_started_us','original_finished_us','database_oid','reader_oid','system_identifier_u64','server_start_pg_us')
assert len({tuple(x[k] for k in identity) for x in expected})==1
assert all(x['original_started_us']<=x['original_finished_us']<=x['start_boottime_us']<=x['finish_boottime_us'] for x in expected)
assert all(x['database_oid']==int(p['database_oid']) and x['reader_oid']==int(p['reader_role_oid']) and x['system_identifier_u64']==str(int.from_bytes(system,'big')) and x['server_start_pg_us']==p['server_start_pg_us'] for x in expected)
frozen=[x for x in expected if x['kind']=='RAW_BOOTSTRAP_EXPECTATION_FROZEN_BEFORE_CANDIDATE']
assert len(frozen)==1 and all(frozen[0]['finish_boottime_us']<=x['start_boottime_us'] for x in public)
result=dict(immutable_expected_reads=3,original_interval_preserved=True,all_checks=True,system_identifier_unsigned=int.from_bytes(system,'big'),raw_system_signed=int(p['database_system_identifier_sql_int64']),server_start_pg_us=int.from_bytes(server,'big',signed=True),database_oid=p['database_oid'],reader_oid=p['reader_role_oid'],raw_records=len(public),anchor_records=len([x for x in observed if x["kind"].startswith("KERNEL_")]),approval_policy_generation='NOT_ESTABLISHED',source_acceptance='NOT_ESTABLISHED')
root.joinpath('reconstruction.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))


