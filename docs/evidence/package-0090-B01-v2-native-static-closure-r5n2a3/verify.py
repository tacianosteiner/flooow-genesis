"""Read-only offline source/evidence verification; never calls a server."""
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
    for p,h in f['source_checkout_sha256'].items():ck('frozen:'+p,(R/p).is_file() and sha((R/p).read_bytes())==h)
    paths=list(f['source_Git_LF_sha256']);b=subprocess.run(['git','cat-file','--batch'],input=''.join('HEAD:'+p+'\n' for p in paths).encode(),stdout=subprocess.PIPE,cwd=R,check=True).stdout;offset=0
    for p in paths:
        end=b.index(b'\n',offset);size=int(b[offset:end].split()[-1]);offset=end+1
        ck('GitLF:'+p,sha(b[offset:offset+size])==f['source_Git_LF_sha256'][p]);offset+=size+1
    vp=next(p for p in paths if p.startswith('applications/') and '/V043__' in p);vb=subprocess.check_output(['git','show','HEAD:'+vp],cwd=R)
    crc=zlib.crc32(b''.join(vb.splitlines()));crc=crc if crc<2**31 else crc-2**32
    ck('V043_SHA',sha(vb)==f['CURRENT_V043_GIT_LF_SHA256']);ck('V043_CRC',crc==f['FLYWAY_SIGNED_CRC32']);fence=b"RAISE EXCEPTION USING ERRCODE = '55000'";ck('V043_fence',fence in vb and vb.index(fence)<vb.index(b'SET LOCAL search_path'))
    old=set(f['untracked_before_paths']);now=set(git('ls-files','--others','--exclude-standard').splitlines());prefix=O.relative_to(R).as_posix()+'/'
    report='docs/evidence/PACKAGE-0090-B01-v2-native-static-closure-r5n2a3.md';ck('old166_preserved',len(old)==166 and old<=now);ck('newscope_only',all(p in old or p.startswith(prefix) or p==report for p in now))
    sm=rd('postgres-source-manifest.json');commit=sm['POSTGRES_SOURCE_IDENTITY'].split('@')[1]
    ck('already_proven18_4',sm['POSTGRES_TARGET_MAJOR']==18 and sm['POSTGRES_TARGET_MINOR']==4 and sm['POSTGRES_SOURCE_IDENTITY'].startswith('REL_18_4@'))
    for s in sm['files']:
        ck('source_bytes:'+s['upstream_path'],sha((R/s['path']).read_bytes())==s['sha256'])
        ck('source_origin:'+s['upstream_path'],s['origin']=='https://raw.githubusercontent.com/postgres/postgres/'+commit+'/'+s['upstream_path'])
    ck('tag_metadata',sha((O/'postgres-source/tag-ref.json').read_bytes())==sm['tag_metadata_sha256'])
    stats=rd('stats-field-proof.json');ck('six_fact_fields',{r['FIELD_ID'] for r in stats['fields']}=={'datid','pid','usesysid','usename','backend_start','backend_type'})
    ck('protected_fields_not_public',all(r['VISIBILITY_BRANCH']=='OWN_ROLE_VISIBLE' for r in stats['fields'] if r['FIELD_ID'] in ['backend_start','backend_type']))
    ck('no_stats_role',stats['pg_read_all_stats_required'] is False)
    for name,a in stats['source_anchors'].items():
        ck('anchor_hash:'+name,sha((R/a['path']).read_bytes())==a['sha256'])
        ck('anchor_range:'+name,1<=a['line_start']<=a['line_end']<=len((R/a['path']).read_text().splitlines()))
    st=rd('referent-symbol-table.json');rows=st['adjudications'];byid={r['REFERENCE_ID']:r for r in rows};classes=rd('credential-class-manifest.json');classids={c['CREDENTIAL_CLASS_ID'] for c in classes['classes']}
    ck('419_exact_candidates',len(rows)==len(byid)==419)
    ck('no_ambiguous',all(r['REFERENT_TYPE']!='AMBIGUOUS' for r in rows))
    for r in rows:
        ck('complete_symbol:'+r['REFERENCE_ID'],all(r[k] for k in ['SOURCE_PATH','SOURCE_LOCATION','SOURCE_EXPRESSION','DECLARATION_OR_USE','REFERENT_SYMBOL','REFERENT_TYPE','REFERENT_OWNER','REFERENT_SCOPE','CONTEXT_PROOF']))
        if r['ALIAS_OF']:
            target=byid[r['ALIAS_OF']];ck('alias:'+r['REFERENCE_ID'],r['REFERENT_SYMBOL']==target['REFERENT_SYMBOL'] and r['REFERENT_TYPE']==target['REFERENT_TYPE'] and r['CREDENTIAL_CLASS_ID']==target['CREDENTIAL_CLASS_ID'])
        if r['REFERENT_TYPE']=='ACTUAL_CREDENTIAL':ck('actual_class:'+r['REFERENCE_ID'],r['CREDENTIAL_CLASS_ID'] in classids)
    ck('four_semantic_classes',len(classids)==4)
    ck('native_wire_enum_preserved',classes['native_wire_purpose_enum_unchanged']=={'GENERATION_TRANSPORT':1,'ONE_USE_WORK_AUTHORIZATION':2,'POSTMASTER_SERVER_ENDPOINT':3})
    h=rd('handoff-manifest.json');ck('four_gates_deferred',all(h[k]=='OPEN_BY_DEPENDENCY' for k in ['N1_CATALOG_EFFECT_GRAPH','N1_READER_EFFECTIVE_ACL','N1_QUALIFICATION_INPUT_RESOLUTION','N1_SUBSTITUTION_STATIC_WITNESSES']))
    for p in O.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'));ck('syntax:'+p.name,True)
    if (O/'independent-review.json').exists():
        review=rd('independent-review.json')
        for p,hv in review['source_sha256'].items():ck('reviewed:'+p,sha((R/p).read_bytes())==hv)
        ck('independent_targets',review['target_verdicts']=={'N1-SOURCE-STATS-VISIBILITY':'CLOSED','N1-CREDENTIAL-CLASS-INVENTORY':'CLOSED'} and review['INDEPENDENT_REVIEW']=='PASS')
    if (O/'SOURCE-IDENTITY-GATE.json').exists():
        g=rd('SOURCE-IDENTITY-GATE.json');ck('target_closed',g['TARGET_BLOCKERS_CLOSED']==2)
        ck('no_execution',all(g[k]=='NO' for k in ['IMPLEMENTATION_PERFORMED','NATIVE_BUILD_PERFORMED','NATIVE_RUNTIME_EXECUTED','SQL_EXECUTED','DATABASE_CONTACTED','V043_EXECUTED','B02_EXECUTED']))
        ck('buckets419',sum(g[k] for k in ['CREDENTIAL_ACTUAL_REFERENCES','CREDENTIAL_NON_CREDENTIAL_REFERENCES','CREDENTIAL_POLICY_METADATA_REFERENCES','CREDENTIAL_AUTH_MECHANISM_REFERENCES'])==419)
    if (O/'SHA256-MANIFEST.json').exists():
        m=rd('SHA256-MANIFEST.json')
        for p,hv in m['files'].items():ck('sealed:'+p,sha((R/p).read_bytes())==hv)
        expected={p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file() and p.name!='SHA256-MANIFEST.json'}|{report};ck('manifest_exact',expected==set(m['files']))
    out={'scope':'OFFLINE_SOURCE_SYMBOL_AND_INTEGRITY_CHECKS_NOT_RUNTIME_PROOF','tests_distinct':len(checks),'test_failures':sum(not c['passed'] for c in checks),'checks':checks}
    print(json.dumps(out if '--detail' in sys.argv else {k:v for k,v in out.items() if k!='checks'}));return out['test_failures']
if __name__=='__main__':sys.exit(bool(main()))
