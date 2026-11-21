import pathlib,json,hashlib,tarfile,subprocess
r=pathlib.Path(__file__).parent;p=r.parent/'managed-host-preparation-v2'
e=json.loads((p/'managed-execution.json').read_text(encoding='utf-8-sig'));a=json.loads((p/'authority-receipt.json').read_text(encoding='utf-8-sig'))
def unpack(name):
 with tarfile.open(p/name,'r:') as t:
  z=t.getmembers();assert len(z)<32 and all(x.isfile() or x.isdir() for x in z)
  return {x.name:t.extractfile(x).read() for x in z if x.isfile()}
s=unpack('source-bundle.tar');v=unpack('runtime-bundle.tar')
for files in (s,v):
 m=json.loads(files['probe/input-manifest.json']);assert set(m)==set(files)-{'probe/input-manifest.json'}
 assert all(hashlib.sha256(files[k]).hexdigest()==h for k,h in m.items())
assert json.loads(s['probe/input-manifest.json'])==a['INPUTS']['source_manifest']
assert hashlib.sha256((p/'source-bundle.tar').read_bytes()).hexdigest()==a['INPUTS']['source_bundle_sha256']
elf=v['probe/self-session-probe'];assert elf.startswith(b'\x7fELF')
assert hashlib.sha256(elf).hexdigest()==e['compiled_publisher_sha256']
assert hashlib.sha256(v['probe/input-manifest.json']).hexdigest()==e['immutable_image_metadata']['Config']['Labels']['flooow.input_manifest_sha256']
script=v['probe/run_self_session_probe.sh'].decode();assert not any(x.startswith('gcc ') for x in script.splitlines())
assert '/probe/self-session-probe' in script and '/tmp/self-session-probe' not in script
record=e['actual_publisher_birth_executable_namespace']['stdout'].splitlines();assert record[0]=='/probe/self-session-probe' and record[1].split()[0]==e['compiled_publisher_sha256']
stat=record[2];pid=int(stat.split(' ',1)[0]);fields=stat[stat.rfind(')')+2:].split()
assert pid==e['actual_publisher_pid_in_managed_namespace'] and int(fields[1])==1
assert e['manager_before']==e['manager_after'] and e['exit_code']==0
captures=[]
for args in (['image','inspect',e['immutable_image_id']],['container','inspect',e['runtime_container_id']]):
 q=subprocess.run(['docker','--context','desktop-linux',*args],capture_output=True,text=True,timeout=15)
 captures.append(dict(args=args,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr))
 if args[0]=='image':
  assert q.returncode==0;image=json.loads(q.stdout)[0];assert image['Id']==e['immutable_image_id'] and image['Parent']==e['base_image']
 else:assert q.returncode!=0
r.joinpath('reconstruction.json').write_text(json.dumps(dict(source_files=len(s),runtime_files=len(v),manifest_hashes_match=True,precompiled_elf_hash=e['compiled_publisher_sha256'],publisher_namespace_pid=pid,publisher_parent_namespace_pid=int(fields[1]),publisher_start_ticks=int(fields[19]),no_runtime_gcc=True,read_only_metadata_captures=captures),indent=2)+'\n')
print(json.dumps(dict(all_checks=True,publisher_pid=pid,start_ticks=int(fields[19]))))
