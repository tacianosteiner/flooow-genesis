"""Read-only offline integrity/structure verifier; never an enforcement proof."""
import sys
sys.dont_write_bytecode=True
import hashlib,itertools,json,subprocess,zlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def h(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value)})
def run():
    f=read(OUT/'baseline-freeze.json');g=read(OUT/'NATIVE-GATE.json')
    check('branch',git('branch','--show-current').decode().strip()==f['branch'])
    check('head',git('rev-parse','HEAD').decode().strip()==f['baseline_head'])
    check('remote_tracking_ref_no_network',git('rev-parse','origin/'+f['branch']).decode().strip()==f['baseline_head'])
    check('tracked_clean',not git('diff','--name-only'))
    check('staged_empty',not git('diff','--cached','--name-only'))
    for p,d in f['source_checkout_sha256'].items():check('frozen:'+p,(ROOT/p).is_file() and h((ROOT/p).read_bytes())==d)
    paths=list(f['source_Git_LF_sha256'])
    batch=subprocess.run(['git','cat-file','--batch'],input=(''.join('HEAD:'+p+'\n' for p in paths)).encode(),stdout=subprocess.PIPE,check=True,cwd=ROOT).stdout
    offset=0
    for p in paths:
        end=batch.index(b'\n',offset);header=batch[offset:end].split();size=int(header[-1]);offset=end+1
        content=batch[offset:offset+size];offset+=size+1
        check('git_lf:'+p,h(content)==f['source_Git_LF_sha256'][p])
    old=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').decode().splitlines())
    prefix=OUT.relative_to(ROOT).as_posix()+'/'
    report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n1.md'
    check('old_72_paths_preserved',len(old)==72 and old<=now)
    check('new_scope_only',all(p in old or p.startswith(prefix) or p==report for p in now))
    vpath=next(p for p in paths if p.startswith('applications/') and '/V043__' in p)
    vb=git('show','HEAD:'+vpath)
    check('canonical_V043_sha256',h(vb)==f['CURRENT_V043_GIT_LF_SHA256'])
    crc=zlib.crc32(b''.join(vb.splitlines()))
    crc=crc if crc<2**31 else crc-2**32
    check('canonical_V043_Flyway_CRC32',crc==f['FLYWAY_SIGNED_CRC32'])
    check('canonical_V043_fence_first',b"RAISE EXCEPTION USING ERRCODE = '55000'" in vb and vb.index(b"RAISE EXCEPTION USING ERRCODE = '55000'")<vb.index(b'SET LOCAL search_path'))
    roots=read(OUT/'root-cause-accounting.json');check('root_3_minus_1_equals_2',len(roots['original_roots'])==3 and sum(r['classification']=='CLOSED_BY_R5N' for r in roots['original_roots'])==1 and roots['R5N_OPEN_ROOTS']==2)
    protocols=read(OUT/'closed-protocol-freeze.json')
    for name,d in protocols['files'].items():check('preserved:'+name,h((OUT/('preserved-'+name)).read_bytes())==d)
    q=read(OUT/'participant-qualification.json')['matrix'];ps={r['PARTICIPANT_ID'] for r in q}
    check('exact_seven',ps==set('POSTMASTER SUPERVISOR RECEIVER CENSUS_OBSERVER APPROVAL_PRODUCER APPROVAL_CONSUMER ENFORCEMENT_WORKER'.split()) and len(q)==7)
    for name,key in [('execution-isolation','profiles'),('authority-isolation','profiles'),('credential-custody','credentials')]:
        rows=read(OUT/(name+'.json'))[key]
        check(name+'_seven',len(rows)==7)
    pairs=read(OUT/'independence-matrix.json')['pairs'];check('21_pairwise_relations',len(pairs)==21)
    sources=read(OUT/'catalog-projection.json')['sources'];check('19_sources',len(sources)==19)
    check('146_explicit_fields',sum(len(s['EXACT_PROJECTED_FIELDS']) for s in sources)==146)
    attacks=read(OUT/'substitution-matrix.json');check('168_original_cases',len(attacks['preserved_cases'])==168)
    check('182_new_cases',len(attacks['new_cases'])==182)
    for p in ps:check('26_new_per_participant:'+p,sum(r['participant']==p for r in attacks['new_cases'])==26)
    check('unknown_not_qualified',all(r['UNKNOWN']=='NOT_QUALIFIED' for r in q))
    check('all_execution_flags_NO',all(g[k]=='NO' for k in ['IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED']))
    if (OUT/'independent-review.json').exists():
        r=read(OUT/'independent-review.json')
        check('review_is_object',isinstance(r,dict))
        for p,d in r['consumed_sha256'].items():check('reviewed:'+p,h((ROOT/p).read_bytes())==d)
        check('seven_independently_reevaluated',len(r['per_participant_verdict'])==7)
        check('no_false_design_pass',g['V2_NATIVE_STATUS']=='BLOCKED' and g['NATIVE_PARTICIPANTS_FULLY_DESIGNED']==sum(p['FULLY_DESIGNED'] for p in r['per_participant_verdict']))
        check('finite_atomic_blockers',len(r['residual_native_blockers'])==g['BLOCKER_COUNT_FOR_V2_NATIVE'])
        required={'BLOCKER_ID','PARTICIPANT','MISSING_DECISION','MISSING_SOURCE','WHY_STATIC','MINIMUM_NEXT_ACTION'}
        check('all_blockers_six_fields',all(required<=set(b) and all(b[k] for k in required) for b in r['residual_native_blockers']))
        check('historical_and_atomic_counts_distinct',g['R5_NATIVE_TRUE_STATIC_DESIGN_FAILURES_REMAINING']==2 and g['BLOCKER_COUNT_FOR_V2_NATIVE']==12)
    if (OUT/'SHA256-MANIFEST.json').exists():
        m=read(OUT/'SHA256-MANIFEST.json')
        for p,d in m['files'].items():check('sealed:'+p,h((ROOT/p).read_bytes())==d)
        actual={p.relative_to(ROOT).as_posix() for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report}
        check('manifest_exact_scope',actual==set(m['files']))
    result={'scope':'OFFLINE_INTEGRITY_AND_STRUCTURE_NOT_DESIGN_OR_RUNTIME_PROOF','tests_distinct':len(checks),'test_failures':sum(not c['passed'] for c in checks),'checks':checks}
    print(json.dumps(result if '--detail' in sys.argv else {k:v for k,v in result.items() if k!='checks'}))
    return result
if __name__=='__main__':sys.exit(bool(run()['test_failures']))
