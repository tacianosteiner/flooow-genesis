"""Seal reviewed design evidence only; no operational authority."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def read(n):return json.loads((OUT/n).read_text(encoding='utf-8-sig'))
def save(n,x):(OUT/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT).decode().strip()
def seal():
    files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}
    report=ROOT/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n1.md'
    files[report.relative_to(ROOT).as_posix()]=hashlib.sha256(report.read_bytes()).hexdigest()
    save('SHA256-MANIFEST.json',{'algorithm':'SHA256_CHECKOUT_BYTES','self_excluded':True,'files':files})
def finalize():
    r=read('independent-review.json');g=read('NATIVE-GATE.json');f=read('baseline-freeze.json')
    assert r['verdict']=='FAIL_STATIC_DESIGN' and r['blocker_count']==12
    g.update(r['protocol_verdicts'])
    for k,v in r['metrics'].items():g[k]=len(v) if isinstance(v,list) else v
    g.update(CURRENT_HEAD=git('rev-parse','HEAD'),REMOTE_HEAD=git('rev-parse','origin/'+f['branch']),LOCAL_EQUALS_REMOTE='YES',TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,UNTRACKED_BEFORE=72,UNAUTHORIZED_UNTRACKED_COUNT=0,
      R5_NATIVE_TRUE_STATIC_DESIGN_FAILURES_REMAINING=2,REMAINING_ATOMIC_DECISIONS=12,R5N_STATIC_ISOLATION='BLOCKED',R5N_STATIC_CATALOG='BLOCKED',NATIVE_INDEPENDENT_REVIEW=r['verdict'],V2_NATIVE_STATUS='BLOCKED',BLOCKER_COUNT_FOR_V2_NATIVE=12,RESIDUAL_NATIVE_BLOCKERS=[b['BLOCKER_ID'] for b in r['residual_native_blockers']],NEXT_GATE=r['next_gate'],NATIVE_PARTICIPANTS_FULLY_DESIGNED=r['NATIVE_PARTICIPANTS_FULLY_DESIGNED'],UNRESOLVED_NATIVE_WORK_ANCHORS=r['UNRESOLVED_NATIVE_WORK_ANCHORS'])
    save('atomic-residuals.json',{'source':'independent-review.json#/residual_native_blockers','blockers':r['residual_native_blockers'],'count':12,'historical_families_remaining':2,'count_reconciliation':r['count_reconciliation'],'non_target_blockers_unchanged':['V2-EPOCH','V2-PARTITIONS','V2-TEMPLATES']})
    report=ROOT/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n1.md'
    def render():
        lines=['# Package 0090 B01 — R5N.1 static evidence','',
          '**BLOCKED — independent review FAIL_STATIC_DESIGN; 0/7 fully designed.**','',
          'Only new design/evidence files were created. No implementation, native build, SQL, database contact, V043, B02, network qualification, staging, commit, push or PR occurred. No prior source/evidence was changed.','',
          '## Accounting','',
          'Three original proof families remain accounted for: ISOLATION_CUSTODY and CATALOG_WORK_WITNESS remain open; PUBLICATION_GENERATION_BINDING was CLOSED_BY_R5N. Thus 3 − 1 = 2 historical families. This review exposes 12 atomic decisions within those same two families; it does not manufacture twelve original roots. The 490 non-native R5 failures are unchanged.','',
          '## Candidate design and independent result','',
          'Seven distinct participants retain the byte-identical approved message ABI, generation/registry and identity codecs. Candidate additions describe 240 syscall policy rows, seven authority profiles, 189 custody field declarations, 21 pairwise independence relations, 19 catalog relations, 146 projected fields, 26 named predicates and 21 graph edge types. These are inventory counts, not counts of proven rules.','',
          'Independent per-participant evaluation records all ten components in independent-review.json. Identity, ABI, generation and registry retain complete static design with future measured evidence pending. Isolation, custody, catalog, completed work, independence and substitution rejection fail static design for every participant. Future binary hashes/PIDs/installed-policy measurements are not counted as static blockers.','',
          'The 168 prior substitution rows and 182 new rows (26 per participant) are preserved. A calculated static attack rerun is NOT proven: expected-outcome declarations do not establish rejection. This deficiency is N1-SUBSTITUTION-STATIC-WITNESSES. Completed-work NO is not solely custody: catalog visibility, reader effects, snapshot barrier and exact qualification bindings are independently necessary.','',
          '## Atomic residuals','']
        for b in r['residual_native_blockers']:
            lines+=['### '+b['BLOCKER_ID'],'']
            for k in ['PARTICIPANT','MISSING_DECISION','MISSING_SOURCE','WHY_STATIC','MINIMUM_NEXT_ACTION']:
                v=b[k];lines += ['**'+k+'**: '+(', '.join(v) if isinstance(v,list) else v),'']
        lines+=['## Integrity and limits','',
          'Preflight verified all 72 pre-existing untracked paths in authorized R5/R5N scopes, branch/HEAD/remote tracking identity, tracked/staged zero, old manifests and canonical V043 integrity. REMOTE_HEAD is the existing remote tracking ref; no network refresh was performed. Negative execution statements describe actions of this task and immutable prior records, not forensic knowledge of unobserved actors.','',
          'Canonical V043 Git-LF SHA256: `'+f['CURRENT_V043_GIT_LF_SHA256']+'`; Flyway signed CRC32: `'+str(f['FLYWAY_SIGNED_CRC32'])+'`. The 55000 fence remains before search_path.','',
          'Run `python -B docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/verify.py`. Checks validate frozen bytes, Git-LF identities, scope, inventories, review hashes and manifest. Passing these checks does not close the design predicates. derive.py is the candidate derivation only; final reviewed metadata is produced by finalize.py and supersedes its draft gate. Do not rerun derive.py alone and treat its draft status as accepted.','',
          'Unresolved catalog inventory: five known field/roster issues, two additional missing field families, ten named predicates. Unresolved isolation: two decision families; custody: one decision family; all 21 independence pairs remain unproven. Exact lists and metric granularity are in independent-review.json.','',
          '## Receipt','', '```text']
        lines += [k+'='+str(v) for k,v in g.items() if k not in ['metric_granularity']]
        lines+=['```','', 'Next action: close the twelve enumerated static decisions and repeat independent review. No live gate is authorized by this receipt.','']
        report.write_bytes('\n'.join(lines).encode())
    save('test-results.json',{'pending_sealed_verification':True})
    save('NATIVE-GATE.json',g);render()
    g['UNTRACKED_AFTER']=len(git('ls-files','--others','--exclude-standard').splitlines())+int(not (OUT/'SHA256-MANIFEST.json').exists())
    save('NATIVE-GATE.json',g);render();seal()
    result=json.loads(subprocess.check_output([sys.executable,'-B',str(OUT/'verify.py'),'--detail'],cwd=ROOT))
    assert result['test_failures']==0
    save('test-results.json',result)
    g.update(TESTS_DISTINCT=result['tests_distinct'],TEST_FAILURES=0)
    save('NATIVE-GATE.json',g);render();seal()
    final=json.loads(subprocess.check_output([sys.executable,'-B',str(OUT/'verify.py')],cwd=ROOT))
    assert final['test_failures']==0 and final['tests_distinct']==g['TESTS_DISTINCT']
    print(json.dumps(final))
if __name__=='__main__':finalize()
