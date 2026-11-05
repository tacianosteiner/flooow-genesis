"""Seal independently reviewed static evidence; no implementation authority."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
REPORT=R/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a2.md'
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def wr(n,x):(O/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def seal():
    files={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}
    files[REPORT.relative_to(R).as_posix()]=hashlib.sha256(REPORT.read_bytes()).hexdigest()
    wr('SHA256-MANIFEST.json',{'algorithm':'SHA256_CHECKOUT_BYTES','self_excluded':True,'files':files})
def main():
    review=rd('independent-review.json');g=dict(review['metrics']);freeze=rd('baseline-freeze.json')
    byid={b['BLOCKER_ID']:b for b in review['blocker_verdicts']}
    assert len(byid)==6 and sum(b['STATUS']=='CLOSED' for b in byid.values())==g['SIX_BLOCKERS_CLOSED']
    g.update(BRANCH=git('branch','--show-current'),BASELINE_HEAD=freeze['baseline_head'],CURRENT_HEAD=git('rev-parse','HEAD'),REMOTE_TRACKING_REF_HEAD=git('rev-parse','origin/'+freeze['branch']),REMOTE_NETWORK_VERIFIED='NO',TRACKED_DIRTY_COUNT=len(git('diff','--name-only').splitlines()),STAGED_COUNT=len(git('diff','--cached','--name-only').splitlines()),UNTRACKED_BEFORE=145,UNAUTHORIZED_UNTRACKED_COUNT=0,OFFICIAL_R5N2_RESIDUAL_DENOMINATOR=10,OFFICIAL_RESIDUALS_AFTER=g['FOUNDATIONAL_STATIC_FAILURES_REMAINING']+2,CANONICAL_V043_MUTATED='NO',PRODUCTION_CONTACTED='NO',GIT_ADD='NO',COMMIT='NO',PUSH='NO',NEXT_EXECUTED=False,NEXT_GATE='CLOSE_FOUR_EXACT_FOUNDATIONAL_STATIC_DECISIONS_BEFORE_FINAL_TWO')
    reg=rd('six-register.json')
    for b in reg['records']:
        b['STATUS']=byid[b['BLOCKER_ID']]['STATUS'];b['INDEPENDENT_VERDICT']=byid[b['BLOCKER_ID']]
    wr('six-register.json',reg)
    wr('residual-static-decisions.json',{'required':6,'closed':g['SIX_BLOCKERS_CLOSED'],'residuals':review['residuals'],'official_denominator':10,'deferred_final_two':['N1-QUALIFICATION-INPUT-RESOLUTION','N1-SUBSTITUTION-STATIC-WITNESSES']})
    def report():
        lines=['# Package0090 — R5N.2A2 six-decision continuation','',
          '**BLOCKED:2/6 closed;4 exact foundational static decisions remain.**','',
          'Scalar logical policy and snapshot observation/publication protocol closed independently. Stats visibility, semantic credential inventory, fixed producer effects and expected reader authority remain open. Official R5N.2 entering denominator remains10; after prior label/preparse closures and these2 closures there are4 foundations plus2 deferred final derivations. No blocker family was added.','',
          '## Closure evidence','',
          'All240 source rule IDs and ASTs map exactly once to16 source-derived semantic families and90 exact operation variants. The logical table specifies typed ordered active fields, per-field flag domains, command applicability,31 operator meanings, pointer safety, lengths/counts, quota reservations and operation-specific returns. mmap protection and mapping flags are distinct; readlinkat/getdents64/lseek/getgroups have explicit result shapes; path metadata resolves retained object labels. Linux numeric ABI layouts and physical enforcement remain future adapter proofs. No backend was selected and no240 runtime observations were demanded.','',
          'The snapshot protocol compares coherent read-only observation, monotonic authority mutation revision and exact generation/registry/work identities under conditional publication. Thirteen event classes have begin-before-effect invalidation, commit/abort semantics, CAS ordering, current-use revalidation, ABA prevention, loss/crash/timeout/reconnect/restart UNKNOWN behavior. Global exclusion and before/after digest alone were rejected as unnecessarily strong or insufficient. Physical mediation/observer implementation is future proof, not a static blocker.','',
          '## Source and semantic limits','',
          'Required statistics projection has6 fields. The frozen view/declaration identify lineage but no native implementation/helper visibility source was found in the searched frozen inventory or local source filename inventories under C:/Projects and Downloads. Native implementation-backed field visibility proofs=0; no pg_monitor/pg_read_all_settings/pg_read_all_stats shortcut was authorized. usename is a pg_authid view join, not a direct native output. No general upstream expectation substitutes for frozen source.','',
          'The2013 lexical mentions are separated into419 CANDIDATE canonical-expression/reference records,29 classified noncredential mentions and1565 repeated candidate mentions.416 candidate referents remain unclassified. Expression hashes identify unresolved expressions only, never credentials or authority. The true semantic inventory/class total is NOT_ESTABLISHED. The field CREDENTIAL_SEMANTIC_REFERENCES_TOTAL=419 is this auditable candidate ledger count, not a claim that419 credentials exist or that semantic adjudication is complete. The finite same-authority proxy authentication interface is preserved; concrete mechanism selection may be implementation only if no new trust/authority, otherwise a static decision. No password/certificate/peer mechanism was invented; legacy trust/superuser endpoint is forbidden for the ordinary reader.','',
          'Codec-only type identity creates no native authority edge. Actual producer type/routine/default-argument invocation still requires an exact fixed source effect manifest or explicit finite rejection. Routine owner, EXECUTE/PUBLIC, DEFINER/INVOKER and configuration context remain distinct; default privileges retain creator-role/schema/object-class/future-object semantics. This does not close the global V2-PARTITIONS graph.','',
          'Reader typed fixpoint preserves13 authority dimensions, but no complete expected projection/ACL/callable policy graph exists. Each of the five no-authority invariants is UNKNOWN with explicit missing inputs. Desired invariants were not hard-coded toYES. Aggregate unresolved catalog counters are NOT_ESTABLISHED rather than carrying old unverified precision or inferringzero.','',
          '## Independent decisions','', '| Blocker | Status |','|---|---|']
        for b in review['blocker_verdicts']:lines+=['| '+b['BLOCKER_ID']+' | '+b['STATUS']+' |']
        lines+=['','## Exact static residuals','']
        for b in review['residuals']:
            lines+=['### '+b['BLOCKER_ID'],'']
            for k,v in b.items():
                if k!='BLOCKER_ID':lines+=['**'+k+'**: '+str(v),'']
        lines+=['## Preservation and verification','',
          'Preflight enumerated145 authorized prior untracked paths, verified branch/HEAD, tracked/staged zero, old source/evidence manifests and canonical V043 identity/fence. Prior evidence and canonical source are immutable in this tranche. No closed contract was reopened and no contradiction was found. The two final derivations remain OPEN_BY_DEPENDENCY and were not attempted. No implementation, build, native/SQL/PostgreSQL/Docker/database/production/V043/B02 execution, staging, commit or push occurred. Negative execution statements concern this task and retained records, not forensic knowledge about unobserved actors.','',
          'V043 Git-LF SHA256:`'+freeze['CURRENT_V043_GIT_LF_SHA256']+'`; Flyway signedCRC32:`'+str(freeze['FLYWAY_SIGNED_CRC32'])+'`;55000 fence unchanged before search_path. REMOTE_TRACKING_REF_HEAD is local only; no networkverification.','',
          'Run read-only `python -B docs/evidence/package-0090-B01-v2-native-static-closure-r5n2a2/verify.py`. Integrity/structure checks do not approve architecture;20 independent review checks are separately recorded in independent-review.json. The manifest is sealed only after final package assembly and checked from fresh bytes. derive.py emits candidates; finalize.py applies the reviewed receipt, so candidate defaults alone never authorize closure.','',
          '## Final receipt','', '```text']
        lines += [k+'='+str(v) for k,v in g.items()]
        lines += ['```','', 'Next bounded action: the four exact source/semantic/policy decisions above, then fresh independent review. Final two derivations remain deferred.','']
        REPORT.write_bytes('\n'.join(lines).encode())
    wr('test-results.json',{'pending_seal':True});wr('FOUNDATION-GATE.json',g);report()
    g['UNTRACKED_AFTER']=len(git('ls-files','--others','--exclude-standard').splitlines())+int(not (O/'SHA256-MANIFEST.json').exists())
    wr('FOUNDATION-GATE.json',g);report();seal()
    result=json.loads(subprocess.check_output([sys.executable,'-B',str(O/'verify.py'),'--detail'],cwd=R));assert result['test_failures']==0
    wr('test-results.json',result);g.update(TESTS_DISTINCT=result['tests_distinct'],TEST_FAILURES=0)
    wr('FOUNDATION-GATE.json',g);report();seal()
    final=json.loads(subprocess.check_output([sys.executable,'-B',str(O/'verify.py')],cwd=R));assert final['test_failures']==0 and final['tests_distinct']==g['TESTS_DISTINCT'];print(json.dumps(final))
if __name__=='__main__':main()
