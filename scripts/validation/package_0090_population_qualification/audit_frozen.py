"""Non-mutating predecessor preservation audit. No runtime/canonical access."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/evidence/package-0090-g3f4-census-heartbeat-domain-parity'
def sha(p,lf=False):
    b=(ROOT/p).read_bytes();return hashlib.sha256(b.replace(b'\r\n',b'\n') if lf else b).hexdigest()
checks=[]
for folder in ['package-0090-g3f4-full-binding-enforcement-qualification','package-0090-g3f4-disposable-native-qualification']:
    manifest=json.loads((ROOT/'docs/evidence'/folder/'SHA256.json').read_text(encoding='utf-8-sig'))
    for p,expected in manifest['files'].items():checks.append({'path':p,'expected':expected,'actual':sha(p,True),'equal':sha(p,True)==expected,'domain':'Canonical Git LF'})
lineage=json.loads((ROOT/'docs/evidence/package-0090-g3f4-current-contract-reconciliation/CONTRACT-LINEAGE.json').read_text(encoding='utf-8-sig'))
for p,expected in lineage['source_worktree_sha256'].items():checks.append({'path':p,'expected':expected,'actual':sha(p),'equal':sha(p)==expected,'domain':'Historical worktree bytes'})
protocol='docs/evidence/package-0090-g3f4-current-contract-reconciliation/G3F4-NATIVE-ENROLLMENT-PROTOCOL-V1.md'
policy='docs/evidence/package-0090-g3f4-current-contract-reconciliation/VERSIONED-REHEARSAL-POLICY-CONTEXT.md'
result={'input_head':'0078290f79c8e6bcdc7b124ca0ae24963a915e2d','tracked_diff':subprocess.run(['git','diff','--name-only','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.splitlines(),'checks':checks,'N':len(checks),'failures':sum(not c['equal'] for c in checks),'approved_protocol_sha256':sha(protocol,True),'approved_policy_structure_sha256':sha(policy,True),'origin_main':subprocess.run(['git','rev-parse','origin/main'],cwd=ROOT,capture_output=True,text=True).stdout.strip()}
(OUT/'FROZEN-PRESERVATION-AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['N'],result['failures'],result['tracked_diff'])
