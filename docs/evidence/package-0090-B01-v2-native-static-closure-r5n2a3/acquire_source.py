"""Acquire only PostgreSQL public source at already-frozen REL_18_4 identity."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess,urllib.request
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
PR='docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a2/'
PG='docs/evidence/package-0090-full-reachable-expectation-closure-v2/provider/'
TAG='REL_18_4'
def sha(b):return hashlib.sha256(b).hexdigest()
def rd(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def wr(n,x):(O/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Flooow-Package0090-Pinned-Public-Source-Proof'}),timeout=40).read()
def main():
    assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff' and git('rev-parse','HEAD')=='cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb'
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    before=[p for p in git('ls-files','--others','--exclude-standard').splitlines() if '/package-0090-B01-v2-native-static-closure-r5n2a3/' not in p];assert len(before)==166
    frozen=rd(PR+'baseline-freeze.json');frozen['source_checkout_sha256'].update({p:sha((R/p).read_bytes()) for p in before});frozen.update(untracked_before=166,untracked_before_paths=before,REMOTE_NETWORK_VERIFIED='NO');wr('baseline-freeze.json',frozen)
    catalog=rd('docs/evidence/package-0090-full-reachable-expectation-closure-v2/provider-catalog-source-freeze.json')
    assert '/REL_18_4/' in catalog['pg_proc.dat']['source'] and sha((R/PG/'pg_proc.dat').read_bytes())==catalog['pg_proc.dat']['sha256']
    assert '#define PG_VERSION_NUM 180004' in (R/PG/'pg_config.h').read_text()
    source_dir=O/'postgres-source';source_dir.mkdir(exist_ok=True)
    tag_origin='https://api.github.com/repos/postgres/postgres/git/ref/tags/'+TAG
    raw=get(tag_origin);(source_dir/'tag-ref.json').write_bytes(raw);tag=json.loads(raw)
    obj=tag['object'];assert obj['type'] in ['commit','tag']
    if obj['type']=='tag':
        tagbytes=get(obj['url']);(source_dir/'annotated-tag.json').write_bytes(tagbytes);obj=json.loads(tagbytes)['object']
    assert obj['type']=='commit';commit=obj['sha'];assert len(commit)==40
    files=['src/backend/utils/adt/pgstatfuncs.c','src/backend/utils/activity/backend_status.c','src/include/utils/backend_status.h','src/include/pgstat.h','src/include/utils/acl.h','src/include/catalog/pg_authid.dat','src/backend/utils/adt/acl.c','src/backend/catalog/system_views.sql','src/include/catalog/pg_proc.dat','src/backend/utils/init/miscinit.c']
    files.append('src/backend/utils/misc/superuser.c')
    records=[]
    for path in files:
        url='https://raw.githubusercontent.com/postgres/postgres/'+commit+'/'+path
        b=get(url);digest=sha(b);target=source_dir/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
        record=dict(path=target.relative_to(R).as_posix(),upstream_path=path,origin=url,sha256=digest,bytes=len(b),commit=commit,version='18.4')
        legacy=R/PG/Path(path).name
        if legacy.exists():record['matches_preexisting_frozen_bytes']=digest==sha(legacy.read_bytes());assert record['matches_preexisting_frozen_bytes'],path
        records.append(record)
    wr('postgres-source-manifest.json',dict(POSTGRES_TARGET_MAJOR=18,POSTGRES_TARGET_MINOR=4,POSTGRES_SOURCE_IDENTITY=TAG+'@'+commit,POSTGRES_SOURCE_ALREADY_FROZEN='YES_RELEASE_TAG_AND_PROVIDER_HASHES',POSTGRES_SOURCE_ACQUIRED='YES',tag_origin=tag_origin,tag_metadata_sha256=sha(raw),files=records,acquisition_authority='User R5N.2A3 §2B, exact already-frozen public PostgreSQL source only',not_performed=['Flooow git fetch','remote-head verification','Docker','DB','SQL','build','runtime qualification']))
    print(json.dumps({'source_identity':TAG+'@'+commit,'files':len(records),'pgstatfuncs_sha256':records[0]['sha256']}))
if __name__=='__main__':main()
