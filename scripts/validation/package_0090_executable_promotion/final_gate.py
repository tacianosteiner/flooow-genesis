"""Single frozen current-head promotion run; earlier rounds are historical only."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,shutil,importlib.util
from verify import verify
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
OUT=ROOT/'docs/evidence/package-0090-g3f4-hash-bound-successor'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,r):p.write_bytes((json.dumps(r,indent=2)+'\n').encode())
def preservation():
    spec=importlib.util.spec_from_file_location('historical_audit',ROOT/'docs/evidence/package-0090-g3f4-executable-handoff-native-health/gate_v2.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);r=m.audit()
    p=ROOT/'docs/evidence/package-0090-g3f4-executable-handoff-native-health/final-02/SHA256-PUBLICATION.json'
    for n,v in json.loads(p.read_text())['files'].items():
        actual=sha((ROOT/n).read_bytes());r['checks'].append({'path':n,'expected':v,'actual':actual,'equal':actual==v,'domain':'LATEST_PUBLISHED_EXACT_BYTES'});r['N']+=1;r['failures']+=int(actual!=v)
    assert sha(p.read_bytes())=='a47e5a343c9f5bcd052494873328fe5de02babba2470262c96be1d66d9269271'
    r['checks'].append({'path':p.relative_to(ROOT).as_posix(),'expected':'a47e5a343c9f5bcd052494873328fe5de02babba2470262c96be1d66d9269271','actual':sha(p.read_bytes()),'equal':True,'domain':'LATEST_PUBLICATION_MANIFEST'});r['N']+=1
    return r
def main():
    out=OUT/sys.argv[1];assert not out.exists();out.mkdir()
    env=OUT/'envelope-02';verified=verify(env);save(out/'INDEPENDENT-VERIFICATION.json',verified)
    manifest=json.loads((env/'PROMOTION-MANIFEST.json').read_text());transform=manifest['transformation']
    save(out/'MACHINE-COMPARISON.json',{'SOURCE_SHA256':manifest['frozen_source_sha256'],'SUCCESSOR_SHA256':verified['successor_sha256'],'TRANSFORMATION_KIND':transform['kind'],'TRANSFORMATION_RANGE':{'offset':transform['offset'],'length':transform['length'],'domain':'ACCEPTED_GIT_BLOB_LF'},'SEMANTIC_STATEMENTS_CHANGED_N':0,'SECURITY_REVIEWED_STATEMENTS_CHANGED_N':0,'definition':'Unconditional execution fence is externalized into the independently verified promotion envelope. Every other security-reviewed statement is byte-identical. No domain statement changed.'})
    before=preservation();save(out/'HISTORICAL-PRE.json',before);assert not before['failures']
    files={str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes()) for p in HERE.iterdir() if p.is_file()}
    for p in [OUT/'PROMOTION-CONTRACT.md',OUT/'RESIDUAL-CONTRACT.md',*env.iterdir()]:
        if p.is_file():files[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p.read_bytes())
    frozen=sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode());save(out/'IMMUTABLE-SOURCE.json',{'files':files,'source_sha256':frozen,'inherited_PASS':False})
    cases=[]
    for key in ['PROMOTION_MANIFEST_VERIFY','SUCCESSOR_PROVENANCE_VERIFY','SUCCESSOR_SEMANTIC_EQUIVALENCE','NONCANONICAL_MANIFEST_VERIFY']:
        cases.append({'id':key,'result':'PASS','detail':verified[key]})
    scratch=Path(tempfile.mkdtemp(prefix='flooow-promotion-negative-'))
    try:
        for field,value in [('input_commit','0'*40),('marker','CANONICAL'),('SUCCESSOR_CANONICAL',True),('SUCCESSOR_NUMERIC_AUTHORITY',True),('successor_sha256','0'*64),('runtime_consumer_source_sha256','0'*64),('explicit_authorization_sha256','0'*64)]:
            d=scratch/field;shutil.copytree(env,d);m=json.loads((d/'PROMOTION-MANIFEST.json').read_text());m[field]=value;save(d/'PROMOTION-MANIFEST.json',m)
            try:verify(d);rejected=False
            except AssertionError:rejected=True
            cases.append({'id':'independent_reject_'+field,'result':'PASS' if rejected else 'FAIL'})
        d=scratch/'semantic-substitution';shutil.copytree(env,d);m=json.loads((d/'PROMOTION-MANIFEST.json').read_text());p=d/m['successor_filename'];p.write_bytes(p.read_bytes().replace(b'CREATE TABLE',b'CREATE TEMP TABLE',1));m['successor_sha256']=sha(p.read_bytes());save(d/'PROMOTION-MANIFEST.json',m)
        try:verify(d);rejected=False
        except AssertionError:rejected=True
        cases.append({'id':'independent_reject_semantic_change_even_rehashed','result':'PASS' if rejected else 'FAIL'})
    finally:
        assert scratch.parent.resolve()==Path(tempfile.gettempdir()).resolve() and scratch.name.startswith('flooow-promotion-negative-');shutil.rmtree(scratch)
    save(out/'PROMOTION-ASSERTIONS.json',{'cases':cases,'scratch_removed':True})
    assert all(sha((ROOT/n).read_bytes())==v for n,v in files.items())
    with (out/'EXECUTION.console.log').open('w',encoding='utf-8') as log:
        run=subprocess.run([sys.executable,'-B',str(HERE/'qualify.py'),str(env),str(out/'execution')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    raw=json.loads((out/'execution/RAW.json').read_text());after=preservation();save(out/'HISTORICAL-POST.json',after)
    same=all(sha((ROOT/n).read_bytes())==v for n,v in files.items())
    cases+=raw['cases'];cases.append({'id':'final_source_bytes_unchanged','result':'PASS' if same else 'FAIL'});cases.append({'id':'historical_hashes_intact','result':'PASS' if not after['failures'] else 'FAIL'});cases.append({'id':'owned_cleanup_complete','result':'PASS' if all(raw.get(k) for k in ['container_removed','network_removed','scratch_removed']) else 'FAIL'})
    nr=raw['not_run']
    for fc in ['FC03','FC04','FC05','FC07']:nr.append({'CASE':fc,'BLOCKING_FINDING':'FC01_POSITIVE_PREREQUISITE_NOT_CLOSED','WHY_NOT_EXECUTABLE':'User requires complete positive FC01 before these actual-domain dependent cases. No inherited or selected native PASS substitutes.','WHAT_AUTHORITY_OR_ARTIFACT_MISSING':'Full current successor positive domain qualification'})
    result={'source_sha256':frozen,'manifest_sha256':verified['manifest_sha256'],'successor_sha256':verified['successor_sha256'],'native_binary_sha256':raw.get('frozen_crypto_binary_sha256'),'cases':cases,'not_run':nr,'executed':len(cases),'PASS':sum(c['result']=='PASS' for c in cases),'FAIL':sum(c['result']=='FAIL' for c in cases),'operational_errors':raw['errors'],'NOT_RUN':len(nr),'unexplained_NOT_RUN':sum(not all(c.get(k) for k in ['BLOCKING_FINDING','WHY_NOT_EXECUTABLE','WHAT_AUTHORITY_OR_ARTIFACT_MISSING']) for c in nr),'execution_exit':run.returncode,'inherited_PASS':False,'FC01':'HOLD_POSITIVE_DOMAIN_NOT_QUALIFIED','historical_checks':after['N'],'historical_mismatch':after['failures'],'source_frozen':same,'cleanup':{k:raw.get(k) for k in ['container_removed','network_removed','scratch_removed']}}
    save(out/'FINAL-MATRIX.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['cases','not_run']}))
    return int(bool(raw['errors']) or result['FAIL'] or result['unexplained_NOT_RUN'])
if __name__=='__main__':raise SystemExit(main())
