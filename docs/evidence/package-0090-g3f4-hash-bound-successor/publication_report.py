"""Non-runtime report and exact-byte publication inventory."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
CODE=ROOT/'scripts/validation/package_0090_executable_promotion'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,r):assert not p.exists();p.write_bytes((json.dumps(r,indent=2)+'\n').encode())
def main():
    final=OUT/'final-02';r=json.loads((final/'FINAL-MATRIX.json').read_text());raw=json.loads((final/'execution/RAW.json').read_text());frozen=json.loads((final/'IMMUTABLE-SOURCE.json').read_text())
    assert r['FAIL']==0 and not r['operational_errors'] and r['unexplained_NOT_RUN']==0 and r['source_frozen'] and r['historical_mismatch']==0
    assert all(r['cleanup'].values()) and all(sha((ROOT/n).read_bytes())==h for n,h in frozen['files'].items())
    assert r['native_binary_sha256']=='5aeedcdb693442b7738b6f33604e059094f584af29d1879bf35482ca06ef63b5'
    development=[]
    for p in sorted(OUT.glob('development-*/RAW.json')):
        v=json.loads(p.read_text());development.append({'round':p.parent.name,'errors':v['errors'],'all_owned_cleanup_complete':all(v.get(k) for k in ['container_removed','network_removed','scratch_removed']),'qualification_contribution':0});assert development[-1]['all_owned_cleanup_complete']
    names=subprocess.check_output(['docker','ps','-a','--filter','label=flooow.scope=0090-executable-promotion','--format','{{.Names}}']).decode().strip();assert not names
    networks=subprocess.check_output(['docker','network','ls','--filter','label=flooow.scope=0090-executable-promotion','--format','{{.Name}}']).decode().strip();assert not networks
    tracked=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode().splitlines();assert not tracked
    findings=[{'severity':'BLOCKER','id':'FULL_POSITIVE_DOMAIN_FIXTURE_CONTRACT','status':'HOLD','evidence':'RESIDUAL-CONTRACT.md; 13 actual-domain positive obligations NOT_RUN, plus four conditional dependent gates'},*({'severity':'HIGH','id':n,'status':'HOLD_UNCHANGED_NO_IMPLEMENTATION_AUTHORITY','evidence':'Preserved predecessor HEALTH-CONTRACT.md and current RESIDUAL-CONTRACT.md'} for n in ['NATIVE_IDENTITY','NATIVE_INDEPENDENT_GENERATIONS','COMPLETED_FUNCTIONAL_PROGRESS','INDEPENDENT_HEALTH_GRAPH'])]
    save(final/'SCOPE-FINAL-AUDIT.json',{'input_head':raw['input_head'],'branch':'checkpoint/package-0090-cloud-handoff','changed_scope':['scripts/validation/package_0090_executable_promotion/','docs/evidence/package-0090-g3f4-hash-bound-successor/'],'tracked_predecessor_changes':tracked,'runtime_native_protocol_changed':False,'native_binary_component':'Unchanged flooow_offline_mac32 extension used by the actual successor; no fresh full-watchdog PASS claimed','numeric_values_adopted':False,'plaintext_secrets_or_private_keys_created':False,'plaintext_credential_files_erased':True,'owned_containers_remaining':names,'owned_networks_remaining':networks,'development':development,'superseded_rounds':['final-01','envelope-01'],'only_final_round':'final-02','inherited_PASS':False,'findings':findings,'source_sha256':r['source_sha256'],'manifest_sha256':r['manifest_sha256'],'successor_sha256':r['successor_sha256'],'native_binary_sha256':r['native_binary_sha256']})
    report=f'''# Hash-bound executable successor — final characterization

Status: HOLD. Room engineering readiness is not established. Input branch `checkpoint/package-0090-cloud-handoff`, input commit `{raw['input_head']}`.

The final independently verified envelope-02 removes only the exact first execution fence. Reinsertion reproduces the accepted Git source bytes; all other statements remain byte-identical. Worktree CRLF identity is separately preserved. The full actual successor is consumed by Flyway 13.2.0 using 43 verified immutable in-memory resources; both material-substitution probes reject before connection. Actual V001–V043 migration history is successful. Four synthetic service identities receive only the existing reviewed slot surface; effective raw table/column privileges are absent. The real promoted preflight denies a missing current binding with P0017. This denial is not positive parity.

Final fresh result: {r['executed']} executed / {r['PASS']} PASS / {r['FAIL']} FAIL / {len(r['operational_errors'])} operational errors / {r['NOT_RUN']} explained NOT_RUN / {r['unexplained_NOT_RUN']} unexplained NOT_RUN. All 13 required positive-domain cases and four FC01-dependent gates remain explicitly NOT_RUN. Installation and selected negative checks do not close FC01. No previous PASS contributes. Seven development failures and final-01 remain historical evidence only.

The residual full-domain fixture boundary and four independent native health gap groups are documented in RESIDUAL-CONTRACT.md. Policy/readiness/lineage predicates were retained; no numeric bounds, eligibility flag or canonical context was manufactured. Native identity/generation/progress/enforcement protocols remain unchanged. PROCESS_ALIVE != PARTICIPANT_MAKING_PROGRESS.

Final execution-source set: `{r['source_sha256']}`. Promotion manifest: `{r['manifest_sha256']}`. Successor: `{r['successor_sha256']}`. Actual unchanged crypto extension binary: `{r['native_binary_sha256']}`. This binary identifier is not the supervisor/receiver/watchdog aggregate and confers no full native health qualification.

All {r['historical_checks']} historical hashes remain intact. No canonical V6/database/IDs/keys/T0/SIGN/ADMIN/TREG/final runner/production access or mutation occurred. No numeric policy was adopted. No private keys or plaintext credentials were created. All owned containers, internal networks and temporary scratch were removed, including failed development rounds. Publication is a characterized HOLD on the Room branch only; main and research are untouched. The publication commit containing this report supplies its final Git identity; that identity cannot be embedded into its own bytes.

Next gate: complete explicitly scoped noncanonical positive-domain fixture contract, then full actual positive successor parity and conditional FC03/FC04/FC05/FC07. Native changes require a separate reviewed contract and authorization. Exact proposed authorization phrase is preserved in RESIDUAL-CONTRACT.md; it has not been executed.
'''
    p=final/'REPORT.md';assert not p.exists();p.write_bytes(report.encode())
    files={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for base in [OUT,CODE] for p in sorted(base.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    for n in files:
        b=(ROOT/n).read_bytes();assert b'-----BEGIN '+b'PRIVATE KEY-----' not in b and b'-----BEGIN '+b'OPENSSH PRIVATE KEY-----' not in b
    aggregate=sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode());save(final/'SHA256-PUBLICATION.json',{'files':files,'aggregate_sha256':aggregate,'excluded':['this manifest itself'],'exact_byte_domain':'WORKTREE_BYTES; stage with core.autocrlf=false; verify Git index and tree before push'})
    print(json.dumps({'files':len(files),'aggregate_sha256':aggregate,'result':'HOLD_CHARACTERIZED_NOT_FC01_PASS'}))
if __name__=='__main__':main()
