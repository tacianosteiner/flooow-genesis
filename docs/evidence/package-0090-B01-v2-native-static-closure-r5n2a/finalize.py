"""Seal independent R5N.2A static evidence without executing later gates."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
REPORT=R/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a.md'
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def wr(n,x):(O/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def seal():
    files={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}
    files[REPORT.relative_to(R).as_posix()]=hashlib.sha256(REPORT.read_bytes()).hexdigest()
    wr('SHA256-MANIFEST.json',{'algorithm':'SHA256_CHECKOUT_BYTES','self_excluded':True,'files':files})
def main():
    review=rd('independent-review.json');g=dict(review['metrics']);f=rd('baseline-freeze.json')
    assert len(review['blocker_verdicts'])==8 and sum(b['STATUS']=='CLOSED' for b in review['blocker_verdicts'])==g['FOUNDATIONAL_BLOCKERS_CLOSED']
    g.update(BRANCH=git('branch','--show-current'),BASELINE_HEAD=f['baseline_head'],CURRENT_HEAD=git('rev-parse','HEAD'),REMOTE_TRACKING_REF_HEAD=git('rev-parse','origin/'+f['branch']),REMOTE_NETWORK_VERIFIED='NO',TRACKED_DIRTY_COUNT=len(git('diff','--name-only').splitlines()),STAGED_COUNT=len(git('diff','--cached','--name-only').splitlines()),UNTRACKED_BEFORE=121,UNAUTHORIZED_UNTRACKED_COUNT=0,OFFICIAL_R5N2_RESIDUALS_AFTER=g['FOUNDATIONAL_STATIC_FAILURES_REMAINING']+2,RESIDUAL_STATIC_BLOCKERS=[b['BLOCKER_ID'] for b in review['residuals']],CANONICAL_V043_MUTATED='NO',PRODUCTION_CONTACTED='NO',GIT_ADD='NO',COMMIT='NO',PUSH='NO',NEXT_GATE='CLOSE_SIX_EXACT_FOUNDATIONAL_STATIC_DECISIONS_BEFORE_FINAL_TWO')
    wr('foundation-residuals.json',{'foundation_denominator':8,'official_R5N2_denominator':10,'residuals':review['residuals'],'deferred_final_two':{'N1-QUALIFICATION-INPUT-RESOLUTION':'OPEN_BY_DEPENDENCY','N1-SUBSTITUTION-STATIC-WITNESSES':'OPEN_BY_DEPENDENCY'},'no_new_blocker_families':True})
    wr('foundation-register.json',{'records':review['blocker_verdicts'],'topological_order':rd('dependency-dag.json')['topological_order'],'proof_levels':review['proof_levels']})
    def report():
        lines=['# Package 0090 — R5N.2A foundational static sub-gate','',
          '**BLOCKED_FOUNDATION_DESIGN: 2/8 foundations closed,6 exact static residuals.**','',
          'The official entering R5N.2 residual denominator remains10. This sub-gate closed label atomicity and preparse, leaving6 foundational decisions plus2 intentionally deferred final derivations. No prior evidence, canonical source, fixture, V043 or B02 changed. No implementation, build, native execution, SQL, database, production, Docker, staging, commit or push occurred.','',
          '## Dependency-first derivation','',
          'The DAG was emitted before closure derivation. It separates logical label rules from operation confinement, source visibility from acquisition, credentials from reader authority, and graph construction from effective privileges. The last two blockers remain OPEN_BY_DEPENDENCY and were not evaluated for closure.','',
          'Topological order: `'+ ' -> '.join(rd('dependency-dag.json')['topological_order'])+'`.','',
          '## Accepted static contracts','',
          'Label IR covers FD,path,socket,IPC,process,credential,snapshot,code and private-memory resources. It binds full subject/resource/participant/generation/registry/context/authority/credential/work/state tuples, atomic committed alias identities and explicit transfer/duplication/inheritance/fork/reconnect/restart/crash/UNKNOWN behavior. Independent review accepted the adapter complete-mediation contract without demanding an instantiated backend. Linux/ELF is fixed by frozen design; the specific Linux adapter remains unselected. The frozen seccomp/immutable-LSM conjunction was retained.','',
          'Preparse treats inputs as untrusted bytes, checks bounded envelope/source/schema/codec/relation/projection identities and canonical structure before any semantic decoding. It cannot invoke SQL, planner, dynamic loaders or arbitrary PostgreSQL type functions. Its146 field definitions are TOTAL across19relations; each row carries exactly its own relation subset from the closed codec. The source producer remains separately subject to reader/effect constraints.','',
          'Closed configuration exclusion, codec and ABI/generation/registry/completed-work measurement contracts remain frozen. No contradiction was identified and no contract was reopened. Absent physical enforcement/build/runtime values are future proof, not causes of the six static failures.','',
          '## Remaining evidence limits','',
          'All240 prior rule IDs and predicate ASTs are preserved and inspected. Typed argument groups, pointer and quota policy are added, but exact active-argument/flag/command mappings and all operator semantics remain incomplete for all240 rows;86 have the specifically generic process-local predicate. This is not a requirement for240 runtime syscall observations.','',
          'The credential ledger retains2013 matched reference mentions with source paths/pointers/hashes, of which1490 are unresolved lexical classifications. These are NOT a complete count of semantic credentials: regex classification cannot establish exhaustive authority mapping. Three approved-purpose classes are carried; legacy local trust superuser endpoint authority is explicitly forbidden for the native reader; exact proxy authentication remains unclassified. Therefore the exact credential-class total remains unknown. No password was invented.','',
          'The frozen PG18 provider contains the catalog declaration/view but not pgstatfuncs.c implementation. Required cross-role field visibility cannot be inferred from a signature, broad monitoring role or runtime observation. Narrow role/database sources are separated from SQL session attribution.','',
          'Catalog19/146/26/12 and unresolved5/2/2 are explicitly retained baseline inventories, not evidence that seven new constructor templates close all effects. Reader five no-authority invariants remain UNKNOWN. No global V2-PARTITIONS authority graph is claimed. The snapshot contract distinguishes consistent read-only acquisition from global exclusion; no physical exclusion token is invented. Complete event observation and publication ordering still require exact static source binding.','',
          '## Independent verdicts','', '| Blocker | Status | Reason |','|---|---|---|']
        for b in review['blocker_verdicts']:lines+=['| '+b['BLOCKER_ID']+' | '+b['STATUS']+' | '+b['reason'].replace('|','/')+' |']
        lines+=['','## Exact foundational residuals','']
        for b in review['residuals']:
            lines+=['### '+b['BLOCKER_ID'],'']
            for k,v in b.items():
                if k!='BLOCKER_ID':lines+=['**'+k+'**: '+str(v),'']
        lines+=['## Integrity receipt','',
          'Preflight enumerated all121 prior authorized untracked paths and verified branch/HEAD, tracked/staged zero, frozen source/evidence manifests and canonical V043 identity. Remote identity is the local tracking ref only; no network verification. Negative execution statements describe this task and retained prior records, not forensic knowledge of unobserved actors.','',
          'Canonical V043 Git-LF SHA256: `'+f['CURRENT_V043_GIT_LF_SHA256']+'`; Flyway signed CRC32: `'+str(f['FLYWAY_SIGNED_CRC32'])+'`. Its55000 fence remains before search_path.','',
          'Offline verifier: `python -B docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a/verify.py`. Tests prove byte integrity/inventory/structural consistency, not architecture closure or physical qualification. Manifest is read back after sealing.','',
          '## Final fields','', '```text']
        lines+=[k+'='+str(v) for k,v in g.items()]
        lines+=['```','', 'Next action is the six exact static residual decisions above. The two final derivations remain deferred. No later gate executed.','']
        REPORT.write_bytes('\n'.join(lines).encode())
    wr('test-results.json',{'pending_seal':True});wr('FOUNDATION-GATE.json',g);report()
    g['UNTRACKED_AFTER']=len(git('ls-files','--others','--exclude-standard').splitlines())+int(not (O/'SHA256-MANIFEST.json').exists())
    wr('FOUNDATION-GATE.json',g);report();seal()
    result=json.loads(subprocess.check_output([sys.executable,'-B',str(O/'verify.py'),'--detail'],cwd=R));assert result['test_failures']==0
    wr('test-results.json',result);g.update(TESTS_DISTINCT=result['tests_distinct'],TEST_FAILURES=0)
    wr('FOUNDATION-GATE.json',g);report();seal()
    final=json.loads(subprocess.check_output([sys.executable,'-B',str(O/'verify.py')],cwd=R));assert final['test_failures']==0 and final['tests_distinct']==g['TESTS_DISTINCT']
    print(json.dumps(final))
if __name__=='__main__':main()
