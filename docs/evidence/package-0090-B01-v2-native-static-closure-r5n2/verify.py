"""Offline integrity/inventory checks only; not qualification execution."""
import sys
sys.dont_write_bytecode=True
import hashlib,itertools,json,subprocess,zlib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
def main():
    oldscript=R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/verify.py'
    # Old verifier intentionally forbids new R5N2 untracked files, so reuse its frozen byte and Git-LF algorithms here, not its scope assertion.
    f=rd(O/'baseline-freeze.json')
    ck('branch',git('branch','--show-current')==f['branch']);ck('head',git('rev-parse','HEAD')==f['baseline_head'])
    ck('remote_tracking_ref_only',git('rev-parse','origin/'+f['branch'])==f['remote_tracking_ref_head'])
    ck('tracked_clean',not git('diff','--name-only'));ck('staged_empty',not git('diff','--cached','--name-only'))
    for p,h in f['source_checkout_sha256'].items():ck('unchanged:'+p,(R/p).is_file() and sha((R/p).read_bytes())==h)
    paths=list(f['source_Git_LF_sha256'])
    b=subprocess.run(['git','cat-file','--batch'],input=''.join('HEAD:'+p+'\n' for p in paths).encode(),stdout=subprocess.PIPE,check=True,cwd=R).stdout
    offset=0
    for p in paths:
        end=b.index(b'\n',offset);size=int(b[offset:end].split()[-1]);offset=end+1
        ck('GitLF:'+p,sha(b[offset:offset+size])==f['source_Git_LF_sha256'][p]);offset+=size+1
    vp=next(p for p in paths if p.startswith('applications/') and '/V043__' in p)
    vb=subprocess.check_output(['git','show','HEAD:'+vp],cwd=R)
    ck('V043_canonical_sha256',sha(vb)==f['CURRENT_V043_GIT_LF_SHA256'])
    crc=zlib.crc32(b''.join(vb.splitlines()));crc=crc if crc<2**31 else crc-2**32
    ck('V043_Flyway_CRC32',crc==f['FLYWAY_SIGNED_CRC32'])
    fence=b"RAISE EXCEPTION USING ERRCODE = '55000'"
    ck('V043_fence_before_search_path',fence in vb and vb.index(fence)<vb.index(b'SET LOCAL search_path'))
    old=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/'
    report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2.md'
    ck('old99',len(old)==99 and old<=now);ck('only_authorized_new_scope',all(p in old or p.startswith(prefix) or p==report for p in now))
    reg=rd(O/'twelve-blocker-register.json')['records'];contracts=rd(O/'decision-contracts.json')['contracts']
    ck('fixed_denominator12',len(reg)==len(contracts)==12 and {b['BLOCKER_ID'] for b in reg}==set(contracts))
    for b in reg:ck('proofclass:'+b['BLOCKER_ID'],b['PROOF_CLASS']=='STATIC_DESIGN' and bool(b['FUTURE_EVIDENCE_REQUIRED']))
    table=rd(O/'catalog-codec-type-table.json');fields=table['fields']
    ck('fields146',len(fields)==146);ck('all_fields_typed',all(f['CANONICAL_TYPE'] in table['types'] for f in fields))
    ck('unique_field_tags',len({(f['RELATION_TAG'],f['FIELD_TAG']) for f in fields})==len(fields))
    ck('19_relation_tags',len({f['RELATION_TAG'] for f in fields})==19)
    ck('raw_config_removed',all(f['CANONICAL_TYPE']=='CONFIG_ASSERTIONS_V2' for f in fields if f['FIELD_NAME'] in ['proconfig','setconfig']))
    for v in table['vectors']:
        if v['type']=='oid':ck('OID_static_vector',int(v['hex'],16)==v['value'])
        elif v['type']=='int4':ck('signed_static_vector',int.from_bytes(bytes.fromhex(v['hex']),'big',signed=True)==v['value'])
        elif v['type']=='text':ck('text_static_vector',bytes.fromhex(v['hex'])==len(v['value'].encode()).to_bytes(4,'big')+v['value'].encode())
    ws=rd(O/'substitution-witnesses.json');ck('350_attacks',len(ws['cases'])==350)
    ck('unique_attacks',len({c['ATTACK_ID'] for c in ws['cases']})==350)
    ck('witness_count_arithmetic',ws['complete']==sum(c['STATIC_WITNESS_COMPLETE'] for c in ws['cases']) and ws['complete']+ws['unresolved']==350)
    pair=rd(O/'independence-rules.json')['pairs'];ck('21_pairs',len(pair)==21)
    ck('pairs_distinct',len({tuple(p['participants']) for p in pair})==21)
    for name in ['native-message-abi.json','native-registry-generation.json','native-identity-codec.json']:
        ck('protocol_preserved:'+name,(O/('preserved-'+name)).read_bytes()==(R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n'/name).read_bytes())
    if (O/'independent-review.json').exists():
        review=rd(O/'independent-review.json')
        for p,h in review['consumed_sha256'].items():ck('review_hash:'+p,sha((R/p).read_bytes())==h)
    if (O/'NATIVE-GATE.json').exists():
        gate=rd(O/'NATIVE-GATE.json')
        required={'BLOCKER_ID','PROOF_CLASS','STATIC_DECISION','AUTHORITATIVE_INPUTS','FUTURE_EVIDENCE_REQUIRED','VERIFICATION_RULE','UNKNOWN_BEHAVIOR','CLOSURE_CRITERION','STATUS'}
        ck('final_register_fields',all(required<=set(b) for b in reg))
        ck('review_closed_count',gate['TWELVE_BLOCKERS_CLOSED']==sum(b['STATUS']=='CLOSED' for b in review['blocker_verdicts']))
        ck('twelve_accounting',gate['TWELVE_BLOCKERS_CLOSED']+gate['TRUE_STATIC_DESIGN_FAILURES_REMAINING']==12)
        ck('residual_count',gate['BLOCKER_COUNT_FOR_V2_NATIVE']==len(review['residual_native_blockers'])==gate['TRUE_STATIC_DESIGN_FAILURES_REMAINING'])
        ck('participants_recomputed',gate['NATIVE_PARTICIPANTS_FULLY_DESIGNED']==sum(p['PARTICIPANT_STATIC_DESIGN']=='COMPLETE' for p in review['per_participant_verdict']))
        ck('remote_network_not_claimed',gate['REMOTE_NETWORK_VERIFIED']=='NO')
        ck('no_false_PASS',gate['V2_NATIVE_STATUS']!='PASS_DESIGN_ONLY' or gate['TWELVE_BLOCKERS_CLOSED']==12 and gate['NATIVE_PARTICIPANTS_FULLY_DESIGNED']==7)
        ck('no_execution_claim',all(gate[k]=='NO' for k in ['IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED']))
    if (O/'SHA256-MANIFEST.json').exists():
        m=rd(O/'SHA256-MANIFEST.json')
        for p,h in m['files'].items():ck('sealed:'+p,sha((R/p).read_bytes())==h)
        actual={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report}
        ck('manifest_exact_scope',actual==set(m['files']))
    out={'scope':'INTEGRITY_STRUCTURE_STATIC_VECTORS_NOT_DESIGN_OR_RUNTIME_APPROVAL','tests_distinct':len(checks),'test_failures':sum(not c['passed'] for c in checks),'checks':checks}
    print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));return out['test_failures']
if __name__=='__main__':sys.exit(bool(main()))
