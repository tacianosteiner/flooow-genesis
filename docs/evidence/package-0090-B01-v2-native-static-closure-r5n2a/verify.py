"""Read-only offline R5N.2A integrity verifier, not native qualification."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,subprocess,zlib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def sha(b):return hashlib.sha256(b).hexdigest()
checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
def main():
    f=rd('baseline-freeze.json')
    ck('branch',git('branch','--show-current')==f['branch']);ck('HEAD',git('rev-parse','HEAD')==f['baseline_head'])
    ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in f['source_checkout_sha256'].items():ck('frozen:'+p,(R/p).is_file() and sha((R/p).read_bytes())==h)
    paths=list(f['source_Git_LF_sha256']);data=subprocess.run(['git','cat-file','--batch'],cwd=R,input=''.join('HEAD:'+p+'\n' for p in paths).encode(),stdout=subprocess.PIPE,check=True).stdout;off=0
    for p in paths:
        end=data.index(b'\n',off);size=int(data[off:end].split()[-1]);off=end+1
        ck('GitLF:'+p,sha(data[off:off+size])==f['source_Git_LF_sha256'][p]);off+=size+1
    vp=next(p for p in paths if p.startswith('applications/') and '/V043__' in p)
    vb=subprocess.check_output(['git','show','HEAD:'+vp],cwd=R);crc=zlib.crc32(b''.join(vb.splitlines()));crc=crc if crc<2**31 else crc-2**32
    ck('V043_SHA',sha(vb)==f['CURRENT_V043_GIT_LF_SHA256']);ck('V043_CRC',crc==f['FLYWAY_SIGNED_CRC32'])
    fence=b"RAISE EXCEPTION USING ERRCODE = '55000'";ck('V043_fence',fence in vb and vb.index(fence)<vb.index(b'SET LOCAL search_path'))
    old=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/'
    report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a.md'
    ck('old121_preserved',len(old)==121 and old<=now);ck('only_authorized_new_scope',all(p in old or p.startswith(prefix) or p==report for p in now))
    dag=rd('dependency-dag.json');order=dag['topological_order'];ck('DAG_eight',len(set(order))==8)
    for row in dag['records']:ck('DAG_order:'+row['BLOCKER_ID'],all(order.index(p)<order.index(row['BLOCKER_ID']) for p in row['DEPENDS_ON']))
    ck('denominator_ten',dag['official_residual_denominator']==10)
    ck('final_two_deferred',set(dag['deferred'].values())=={'OPEN_BY_DEPENDENCY'})
    ir=rd('scalar-operation-ir.json');ck('240_distinct_logical_rows',len(ir['rules'])==len({r['RULE_ID'] for r in ir['rules']})==240)
    required=set('RULE_ID PARTICIPANT OPERATION_CLASS RESOURCE_CLASS ACTION ARGUMENT_SCHEMA ARGUMENT_PREDICATES POINTER_POLICY SIZE_POLICY COUNT_POLICY QUOTA_POLICY LABEL_REQUIREMENT CREDENTIAL_REQUIREMENT GENERATION_REQUIREMENT CONTEXT_REQUIREMENT RESULT_POLICY ERROR_POLICY UNKNOWN_POLICY'.split())
    for row in ir['rules']:ck('logical_fields:'+row['RULE_ID'],required<=set(row) and row['ACTION'] in ['ALLOW','DENY','CONDITIONAL'])
    for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));ck('Python_syntax:'+p.name,True)
    refs=rd('credential-reference-ledger.json');ck('lexical_ledger_count',refs['total']==len(refs['references']))
    ck('unclassified_not_inferred_zero',refs['unclassified']==sum(not r['classification_complete'] for r in refs['references']))
    if (O/'independent-review.json').exists():
        review=rd('independent-review.json')
        for p,h in review['source_sha256'].items():ck('reviewed:'+p,sha((R/p).read_bytes())==h)
    if (O/'FOUNDATION-GATE.json').exists():
        gate=rd('FOUNDATION-GATE.json')
        ck('foundation_accounting',gate['FOUNDATIONAL_BLOCKERS_CLOSED']+gate['FOUNDATIONAL_STATIC_FAILURES_REMAINING']==8)
        ck('not_global_PASS',gate['V2_NATIVE_STATUS']!='PASS_DESIGN_ONLY')
        ck('no_execution',all(gate[k]=='NO' for k in ['IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED']))
        ck('no_reopens',gate['CLOSED_CONTRACTS_REOPENED']==0 and gate['CONTRADICTIONS_DISCOVERED']==0)
    if (O/'SHA256-MANIFEST.json').exists():
        manifest=rd('SHA256-MANIFEST.json')
        for p,h in manifest['files'].items():ck('sealed:'+p,sha((R/p).read_bytes())==h)
        expected={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report}
        ck('manifest_exact_coverage',expected==set(manifest['files']))
    out={'scope':'OFFLINE_INTEGRITY_STRUCTURE_NOT_ARCHITECTURE_OR_RUNTIME_PROOF','tests_distinct':len(checks),'test_failures':sum(not c['passed'] for c in checks),'checks':checks}
    print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));return out['test_failures']
if __name__=='__main__':sys.exit(bool(main()))
