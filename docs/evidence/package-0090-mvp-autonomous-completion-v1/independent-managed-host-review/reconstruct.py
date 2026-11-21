import pathlib,json,hashlib,tarfile,subprocess
r=pathlib.Path(__file__).parent;p=r.parent/'managed-host-preparation-v1';e=json.loads((p/'managed-execution.json').read_text(encoding='utf-8-sig'));a=json.loads((p/'authority-receipt.json').read_text(encoding='utf-8-sig'))
with tarfile.open(p/'source-bundle.tar','r:') as t:
 members=t.getmembers();assert len(members)<32 and all(x.isfile() or x.isdir() for x in members)
 files={x.name:t.extractfile(x).read() for x in members if x.isfile()}
 manifest=json.loads(files['probe/input-manifest.json']);assert set(manifest)==set(files)-{'probe/input-manifest.json'}
 assert all(hashlib.sha256(files[k]).hexdigest()==v for k,v in manifest.items())
 assert manifest==a['INPUTS']['source_manifest']
 assert hashlib.sha256((p/'source-bundle.tar').read_bytes()).hexdigest()==a['INPUTS']['source_bundle_sha256']
 assert hashlib.sha256(files['probe/input-manifest.json']).hexdigest()==e['immutable_image_metadata']['Config']['Labels']['flooow.input_manifest_sha256']
assert e['manager_before']==e['manager_after'] and e['exit_code']==0
checks=[]
def read(*args):
 q=subprocess.run(['docker','--context','desktop-linux',*args],capture_output=True,text=True,timeout=15)
 checks.append(dict(command=['docker','--context','desktop-linux',*args],exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr))
 return q
image=read('image','inspect',e['immutable_image_id']);assert image.returncode==0
actual=json.loads(image.stdout)[0];assert actual['Id']==e['immutable_image_id'] and actual['Parent']==e['base_image']
for cid in (e['runtime_container_id'],):assert read('container','inspect',cid).returncode!=0
for mount in e['launch_inspect_before_start']['Mounts']:
 if mount['Type']=='volume':assert read('volume','inspect',mount['Name']).returncode!=0
r.joinpath('independent-metadata-and-bundle-check.json').write_text(json.dumps(dict(bundle_matches_receipt=True,manifest_matches_all_tar_files=True,manifest_hash_matches_image_label=True,actual_image_parent_matches=True,read_captures=checks),indent=2)+'\n')
print(json.dumps(dict(bundle_files=len(files),checks_pass=True,containers_created_by_reviewer=0)))
