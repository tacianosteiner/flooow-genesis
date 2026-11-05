"""Finalize reviewed offline evidence; does not implement native qualification."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
REPORT=R/'docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2.md'
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def wr(n,x):(O/n).write_bytes(json.dumps(x,indent=2,ensure_ascii=False).encode()+b'\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def seal():
    files={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(O.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}
    files[REPORT.relative_to(R).as_posix()]=hashlib.sha256(REPORT.read_bytes()).hexdigest()
    wr('SHA256-MANIFEST.json',{'algorithm':'SHA256_CHECKOUT_BYTES','self_excluded':True,'files':files})
def main():
    review=rd('independent-review.json');g=dict(review['metrics']);freeze=rd('baseline-freeze.json')
    verdict={b['BLOCKER_ID']:b for b in review['blocker_verdicts']}
    assert len(verdict)==12 and sum(b['STATUS']=='CLOSED' for b in verdict.values())==g['TWELVE_BLOCKERS_CLOSED']
    registry=rd('twelve-blocker-register.json');contracts=rd('decision-contracts.json')['contracts']
    for b in registry['records']:
        bid=b['BLOCKER_ID'];b.update(STATIC_DECISION=contracts[bid],AUTHORITATIVE_INPUTS=[b['SOURCE_EVIDENCE'],{'path':(O/'decision-contracts.json').relative_to(R).as_posix(),'pointer':'/contracts/'+bid,'sha256':hashlib.sha256((O/'decision-contracts.json').read_bytes()).hexdigest()}],VERIFICATION_RULE=verdict[bid]['CLOSED_or_OPEN_reason'],UNKNOWN_BEHAVIOR='NOT_QUALIFIED; unavailable evidence never inferred safe',STATUS=verdict[bid]['STATUS'])
    registry['authority']='Final fresh independent review; generator defaults superseded'
    wr('twelve-blocker-register.json',registry)
    wr('residual-static-decisions.json',{'proof_class':'STATIC_DESIGN','denominator':12,'closed':g['TWELVE_BLOCKERS_CLOSED'],'residuals':review['residual_native_blockers'],'new_blocker_discovered':review['new_blocker_discovered']})
    g.update(BRANCH=git('branch','--show-current'),BASELINE_HEAD=freeze['baseline_head'],CURRENT_HEAD=git('rev-parse','HEAD'),REMOTE_TRACKING_REF_HEAD=git('rev-parse','origin/'+freeze['branch']),REMOTE_NETWORK_VERIFIED='NO',TRACKED_DIRTY_COUNT=len(git('diff','--name-only').splitlines()),STAGED_COUNT=len(git('diff','--cached','--name-only').splitlines()),UNTRACKED_BEFORE_INTERRUPTION=99,UNTRACKED_AT_RESUME=115,UNAUTHORIZED_UNTRACKED_COUNT=0,PARTIAL_R5N2_FILES_RECOVERED=16,PARTIAL_R5N2_FILES_REPAIRED=3,PARTIAL_R5N2_FILES_REJECTED=0,CANONICAL_V043_MUTATED='NO',CANONICAL_V043_EXECUTED='NO',PRODUCTION_CONTACTED='NO',GIT_ADD='NO',COMMIT='NO',PUSH='NO',PR='NO',UNCLASSIFIED_CREDENTIAL_REFERENCES='AT_LEAST_1_NOT_EXHAUSTIVELY_ENUMERATED',CATALOG_FIELDS_WITHOUT_CODEC=0,NATIVE_CUSTODY_CLASS_FIELD_DECLARATIONS=60)
    recovery=rd('recovery-audit.json')
    recovery['resume_checkpoints']=[{'untracked':113,'partial_files_read':14,'source':'first resume inspection, before recovery audit creation'},{'untracked':115,'partial_files_read':16,'source':'latest resume inspection including completed independent review and earlier recovery audit'}]
    recovery['repaired_existing_paths']=[(O/n).relative_to(R).as_posix() for n in ['derive.py','catalog-codec-type-table.json','verify.py']]
    recovery['repair_definition']='Existing candidate source/codec/verifier changed during resumed work; new completion metadata is not a repaired prior file.'
    recovery['final_classification']={p.name:('COMPLETE' if p.name.startswith('preserved-') or p.name in ['.gitattributes','baseline-freeze.json','verify.py','independent-review.json'] else 'PARTIAL' if p.name in ['decision-contracts.json','credential-classes.json','qualification-inputs.json','substitution-witnesses.json','independence-rules.json'] else 'COMPLETE') for p in O.iterdir() if p.is_file()}
    recovery['final_classification_basis']='PARTIAL means explicitly OPEN design subcontracts retained, not malformed bytes. Closed codec/config/publication subcontracts remain individually accepted. No unfinished Python statements, temporary PASS or disabled checks found. No files discarded.'
    wr('recovery-audit.json',recovery)
    def report():
        lines=['# Package 0090 — R5N.2 resumed static closure','',
          '**BLOCKED: 2/12 static decisions closed; 10 exact residuals; no new blocker.**','',
          'This resumes existing R5N.2 files. It does not restart or discard the package. Independent review was rerun from final inputs after the prior infrastructure interruption; partial reviewer messages were not accepted as a gate result.','',
          '## Result','',
          'Closed: N1-CONFIG-SECRET-EXCLUSION and N1-CATALOG-CODEC-TYPE-TABLE. Configuration excludes raw secret values before export/log/hash and binds assertions to exact source-row keys. All 146 projected fields have deterministic codecs; privileges use 15 canonical semantic identities and the exact ALTER SYSTEM alias from frozen acl.c, without invented PostgreSQL native masks.','',
          'Label publication now separates NATIVE_REGISTRY_WRITER(10) from read-only HEALTH_GUARD(8), specifies complete signed sidejournal records, CAS, recovery, replay, generation/currentness and UNKNOWN. This closes the publication subcondition, but not original kernel-object label propagation/inspection; it remains under the same label blocker. The snapshot-byte preparse gate likewise does not silently remove the earlier SQL parse/type/planner effect boundary.','',
          'The denominator remains exactly 12. EPOCH, PARTITIONS, TEMPLATES, canonical source, fixtures, V043 and B02 are untouched. The latest graph has 12 NATIVE qualification edge kinds; it does not claim the complete global authority graph.','',
          '## Evidence levels and counters','',
          'Seven participants were independently evaluated on all ten components; none is fully designed. Identity/ABI/generation/registry and per-role completed-work anchor measurement contracts are statically complete with future values pending. UNRESOLVED_NATIVE_WORK_ANCHORS=0 counts missing anchor measurement contracts, not successful live work or fully qualified participants. Catalog/custody/isolation/input and 217 attack-witness decisions still prevent qualification. This refines the earlier aggregate completed-work NO rather than fabricating runtime evidence.','',
          'There are 350 preserved substitution cases: 133 have explicit typed tuple comparison contracts; 217 still need exact graph/receipt/mutation witness mappings. These counts describe static contracts, not attacks executed. The 240 carried syscall rows all still depend on backend argument/label decisions. Custody count7 means carried participant custody rows, not60 class field declarations; all7 remain unresolved. The three purpose classes provide60 field declarations but omit at least the proxy SQL authentication class. No exhaustive reference ledger exists: the unclassified-reference value is explicitly a lower bound, never assumed exact1.','',
          'Catalog counts:19 sources,146 fields,26 carried predicates,12 latest edge kinds. Five source-visibility fields remain unresolved; codec-unresolved fields=0 is distinct. Two predicate algorithm roots remain open, with additional transitively affected predicates; this count is not the earlier count of every affected predicate. Two missing callable/default field families remain explicit.','',
          'No binary/hash/PID/syscall-number/catalog snapshot/key/physical receipt absence was counted as a static failure. Implementation, build, runtime and physical instantiation remain pending future gates and were not executed.','',
          '## Twelve decisions','', '| Blocker | Status | Independent reason |','|---|---|---|']
        for b in review['blocker_verdicts']:lines+=['| '+b['BLOCKER_ID']+' | '+b['STATUS']+' | '+b['CLOSED_or_OPEN_reason'].replace('|','/')+' |']
        lines+=['','## Exact residual static decisions','']
        for b in review['residual_native_blockers']:
            lines+=['### '+b['BLOCKER_ID'],'']
            for k,v in b.items():
                if k!='BLOCKER_ID':lines+=['**'+k+'**: '+str(v),'']
        lines+=['## Recovery and verification','',
          'Original preflight:99 authorized pre-existing untracked files. First resume:113 total/14 partial files. Latest resume:115 total/16 R5N.2 artifacts, including recovery audit and fresh independent review. Every existing artifact was read; Python syntax and JSON were parsed before execution. No unauthorized path, tracked change or staged file was found. Original hashes and full path classification are preserved in recovery-audit.json. Three existing files were repaired; no file was deleted/rejected.','',
          'Canonical V043 SHA256(Git LF): `'+freeze['CURRENT_V043_GIT_LF_SHA256']+'`; Flyway CRC32: `'+str(freeze['FLYWAY_SIGNED_CRC32'])+'`; 55000 fence unchanged and before search_path. Negative execution statements describe this task and retained prior records; no forensic claim about unobserved actors.','',
          'REMOTE_TRACKING_REF_HEAD is local only; REMOTE_NETWORK_VERIFIED=NO. No network qualification was performed.','',
          'Read-only verifier: `python -B docs/evidence/package-0090-B01-v2-native-static-closure-r5n2/verify.py`. Integrity/static-vector checks validate bytes, scope, hashes and inventories; they do not approve architecture. derive.py creates candidate data; finalize.py applies the independently reviewed verdict. Re-running derive.py alone replaces final metadata with candidate defaults and must not be interpreted as accepted closure.','',
          '## Final receipt','', '```text']
        lines += [k+'='+str(v) for k,v in g.items()]
        lines+=['```','', 'Next action: close only the ten exact static residuals above, then rerun independent review. No implementation/build/runtime/database gate is executed or authorized by this receipt.','']
        REPORT.write_bytes('\n'.join(lines).encode())
    wr('test-results.json',{'pending_final_integrity_verification':True})
    wr('NATIVE-GATE.json',g);report()
    current=git('ls-files','--others','--exclude-standard').splitlines()
    def classification(p):
        if '/package-0090-B01-v2-native-static-closure-r5n2/' in p or p.endswith('PACKAGE-0090-B01-v2-native-static-closure-r5n2.md'):return 'PARTIAL_R5N2'
        if 'native-static-closure-r5n1' in p.lower():return 'PREEXISTING_R5N1'
        if 'native-static-closure-r5n' in p.lower():return 'PREEXISTING_R5N'
        if 'static-closure-revision-5' in p.lower():return 'PREEXISTING_R5'
        return 'UNAUTHORIZED'
    recovery['final_path_classification']=[{'path':p,'classification':classification(p)} for p in current]
    assert all(p['classification']!='UNAUTHORIZED' for p in recovery['final_path_classification'])
    wr('recovery-audit.json',recovery)
    g['UNTRACKED_FINAL']=len(git('ls-files','--others','--exclude-standard').splitlines())+int(not (O/'SHA256-MANIFEST.json').exists())
    wr('NATIVE-GATE.json',g);report();seal()
    result=json.loads(subprocess.check_output([sys.executable,'-B',str(O/'verify.py'),'--detail'],cwd=R))
    assert result['test_failures']==0
    wr('test-results.json',result);g.update(TESTS_DISTINCT=result['tests_distinct'],TEST_FAILURES=0)
    wr('NATIVE-GATE.json',g);report();seal()
    final=json.loads(subprocess.check_output([sys.executable,'-B',str(O/'verify.py')],cwd=R))
    assert final['test_failures']==0 and final['tests_distinct']==g['TESTS_DISTINCT']
    print(json.dumps(final))
if __name__=='__main__':main()
