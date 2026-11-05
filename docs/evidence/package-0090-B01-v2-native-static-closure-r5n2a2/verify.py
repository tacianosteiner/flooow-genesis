"""Read-only byte/structure verification; not physical qualification."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,subprocess,zlib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
def main():
    f=rd('baseline-freeze.json');ck('branch',git('branch','--show-current')==f['branch']);ck('HEAD',git('rev-parse','HEAD')==f['baseline_head'])
    ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in f['source_checkout_sha256'].items():ck('unchanged:'+p,(R/p).is_file() and sha((R/p).read_bytes())==h)
    paths=list(f['source_Git_LF_sha256']);b=subprocess.run(['git','cat-file','--batch'],cwd=R,input=''.join('HEAD:'+p+'\n' for p in paths).encode(),stdout=subprocess.PIPE,check=True).stdout;off=0
    for p in paths:
        end=b.index(b'\n',off);size=int(b[off:end].split()[-1]);off=end+1;ck('GitLF:'+p,sha(b[off:off+size])==f['source_Git_LF_sha256'][p]);off+=size+1
    vp=next(p for p in paths if p.startswith('applications/') and '/V043__' in p);vb=subprocess.check_output(['git','show','HEAD:'+vp],cwd=R)
    crc=zlib.crc32(b''.join(vb.splitlines()));crc=crc if crc<2**31 else crc-2**32
    ck('V043_SHA',sha(vb)==f['CURRENT_V043_GIT_LF_SHA256']);ck('V043_CRC',crc==f['FLYWAY_SIGNED_CRC32']);fence=b"RAISE EXCEPTION USING ERRCODE = '55000'";ck('V043_fence',fence in vb and vb.index(fence)<vb.index(b'SET LOCAL search_path'))
    old=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/'
    report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a2.md';ck('old145',len(old)==145 and old<=now);ck('newscope_only',all(p in old or p.startswith(prefix) or p==report for p in now))
    reg=rd('six-register.json');ck('six_targets',len(reg['records'])==len(set(r['BLOCKER_ID'] for r in reg['records']))==6)
    ck('two_deferred',set(reg['deferred'].values())=={'OPEN_BY_DEPENDENCY'})
    fm=rd('operation-families.json');mp=rd('rule-family-map.json');families={f['FAMILY_ID'] for f in fm['families']}
    ck('240_unique_rows',len(mp['rules'])==len({r['RULE_ID'] for r in mp['rules']})==240)
    ck('onefamily_each',all(r['FAMILY_ID'] in families for r in mp['rules']))
    ck('16_source_families',len(families)==16)
    ck('no_unregistered_ASToperators',fm['remaining_operator_definitions']==[])
    for r in mp['rules']:ck('logical_rule_fields:'+r['RULE_ID'],all(k in r for k in ['ARGUMENT_BINDINGS','FLAG_BINDINGS','COMMAND_BINDINGS','POINTER_BINDINGS','QUOTA_BINDINGS','ACTION','FAILURE','UNKNOWN']))
    sem=rd('semantic-credential-ledger.json');ck('2013_lexicalretained',sem['lexical_mentions_total']==2013)
    ck('semantic_accounting',sem['semantic_references_total']+sem['duplicate_semantic_mentions']+sem['non_credential_lexical_mentions']==2013)
    ck('unclassified_preserved',sem['semantic_references_unclassified']==sum(not r['classification_complete'] for r in sem['semantic_references']))
    mut=rd('snapshot-mutation-contract.json');ck('13_eventclasses',len(mut['MUTATION_EVENT_CLASSES'])==13)
    ck('eventclasses_unique',len({x['EVENT_CLASS'] for x in mut['MUTATION_EVENT_CLASSES']})==13)
    for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));ck('syntax:'+p.name,True)
    if (O/'independent-review.json').exists():
        review=rd('independent-review.json')
        for p,h in review['source_sha256'].items():ck('reviewed:'+p,sha((R/p).read_bytes())==h)
    if (O/'FOUNDATION-GATE.json').exists():
        g=rd('FOUNDATION-GATE.json');ck('six_accounted',g['SIX_BLOCKERS_CLOSED']+g['FOUNDATIONAL_STATIC_FAILURES_REMAINING']==6)
        ck('no_globalPASS',g['V2_NATIVE_STATUS']!='PASS_DESIGN_ONLY')
        ck('no_reopened',g['CLOSED_CONTRACTS_REOPENED']==g['CONTRADICTIONS_DISCOVERED']==0)
        ck('no_execution',all(g[k]=='NO' for k in ['IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED']))
    if (O/'SHA256-MANIFEST.json').exists():
        m=rd('SHA256-MANIFEST.json')
        for p,h in m['files'].items():ck('sealed:'+p,sha((R/p).read_bytes())==h)
        expected={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report};ck('manifest_exact',expected==set(m['files']))
    out={'scope':'OFFLINE_INTEGRITY_STRUCTURE_NOT_ARCHITECTURE_APPROVAL','tests_distinct':len(checks),'test_failures':sum(not c['passed'] for c in checks),'checks':checks}
    print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));return out['test_failures']
if __name__=='__main__':sys.exit(bool(main()))
