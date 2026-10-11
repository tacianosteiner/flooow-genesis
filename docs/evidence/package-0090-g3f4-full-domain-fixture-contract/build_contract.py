"""Freeze auditable design artifacts and exercise independent model validator only."""
from pathlib import Path
import json,hashlib,subprocess,re,copy,importlib.util
import contract
HERE=Path(__file__).parent;ROOT=HERE.parents[2]
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,r):
    p=HERE/name;assert not p.exists(),name;p.write_bytes((json.dumps(r,indent=2,ensure_ascii=False)+'\n').encode())
def md(name,s):
    p=HERE/name;assert not p.exists(),name;p.write_bytes(s.encode())
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def main():
    assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
    assert git('rev-parse','HEAD')==git('rev-parse','origin/checkpoint/package-0090-cloud-handoff')==contract.HEAD
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    oracle=json.loads((ROOT/'docs/evidence/PACKAGE-0090-H02-INDEPENDENT-SQL-REVIEW.json').read_text())['public_contracts']
    previous=ROOT/'docs/evidence/package-0090-g3f4-hash-bound-successor'
    manifest=previous/'envelope-02/PROMOTION-MANIFEST.json';successor=next((previous/'envelope-02').glob('V043__*.sql'));assert sha(successor.read_bytes())==contract.SUCCESSOR
    historical=json.loads((previous/'final-02/SHA256-PUBLICATION.json').read_text())
    assert all(sha((ROOT/n).read_bytes())==v for n,v in historical['files'].items())
    spec=importlib.util.spec_from_file_location('preservation',ROOT/'scripts/validation/package_0090_executable_promotion/final_gate.py');module=importlib.util.module_from_spec(spec)
    import sys;sys.path.insert(0,str(ROOT/'scripts/validation/package_0090_executable_promotion'));spec.loader.exec_module(module);old=module.preservation();assert old['failures']==0
    authorization=Path('C:/Users/xmz_r/.codex/attachments/fbd5d3d2-301a-44ea-88b9-892ad9fa6ac9/Pasted text.txt')
    save('BASELINE.json',{'branch':git('branch','--show-current'),'local_head':contract.HEAD,'remote_head':contract.HEAD,'origin_main':git('rev-parse','origin/main'),'tracked_dirty_count':0,'staged_count':0,'historical_checks':old['N']+len(historical['files'])+1,'historical_mismatch':0,'authorization_sha256':sha(authorization.read_bytes()),'successor_sha256':contract.SUCCESSOR,'promotion_manifest_sha256':sha(manifest.read_bytes()),'scope':'NONEXECUTING_DESIGN_ONLY'})
    sqlroot=ROOT/'applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration'
    sources=[];tables=[];functions=[];foreign_keys=[]
    for p in sorted(sqlroot.glob('V*.sql')):
        if int(p.name.split('__')[0][1:])>43:continue
        data=subprocess.check_output(['git','show',contract.HEAD+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT);text=data.decode();sources.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(data)})
        if p.name.startswith('V043__'):assert sha(data)==contract.SOURCE
        for m in re.finditer(r'CREATE TABLE\s+(public\.\w+)\s*\((.*?)\n\);',text,re.S):
            columns=[{'name':c.group(1),'declaration':c.group(2).strip()} for c in re.finditer(r'^\s{4}(\w+)\s+(pg_catalog\.[^\n,]+)',m.group(2),re.M)]
            tables.append({'relation':m.group(1),'source':p.name,'line':text.count('\n',0,m.start())+1,'ddl_sha256':sha(m.group().encode()),'columns':columns,'constraints':m.group()})
        for m in re.finditer(r'CREATE(?: OR REPLACE)? FUNCTION\s+(public\.\w+)\s*\(.*?\bAS\s+(\$\w*\$)(.*?)\2\s*;',text,re.S|re.I):
            functions.append({'function':m.group(1),'source':p.name,'line':text.count('\n',0,m.start())+1,'body_sha256':sha(m.group().encode()),'definition':m.group(),'public_calls':sorted(set(re.findall(r'\b(public\.\w+)\s*\(',m.group(3)))),'coverage':'EXACT_BYTES_LEXICAL_INVENTORY_NOT_SEMANTIC_PROOF'})
        foreign_keys += [{'source':p.name,'definition':m.group(),'sha256':sha(m.group().encode())} for m in re.finditer(r'ALTER TABLE\s+public\.\w+.*?FOREIGN KEY.*?;',text,re.S)]
    save('SOURCE-OBLIGATIONS.json',{'sources':sources,'tables':tables,'functions':functions,'foreign_keys':foreign_keys,'semantic_coverage_complete':False,'unresolved':'Exact mapping/typed overload resolution of every runtime predicate to independently validated row/frame witness; lexical discovery alone cannot certify it.'})
    cases=contract.cases(oracle);save('POSITIVE-CASE-PRECONDITIONS.json',cases);joins=contract.joins();save('AUTHORITY-JOIN-GRAPH.json',joins)
    properties={k:{'type':'string'} for k in contract.FIELDS}
    for k in contract.UUID_FIELDS:properties[k]={'type':'string','format':'uuid'}
    for k in contract.GEN_FIELDS+['service_role_oid','fixture_version']:properties[k]={'type':'integer','minimum':1}
    for k in contract.HASH_FIELDS:properties[k]={'type':'string','pattern':'^[0-9a-f]{64}$'}
    properties['case_id']={'enum':[c['CASE_ID'] for c in cases]};properties['readiness_state']={'enum':contract.STATES}
    for k in ['context','registry','model_rows','runtime_evidence']:properties[k]={'type':'object','description':'Closed operational semantics enforced by independent validator; runtime evidence is never accepted as a self-attested boolean'}
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:flooow:test-only:fixture-contract:v1','type':'object','additionalProperties':False,'required':list(properties),'properties':properties,'x-input-head':contract.HEAD,'x-successor-sha256':contract.SUCCESSOR,'x-uuid-fields':contract.UUID_FIELDS,'x-generation-fields':contract.GEN_FIELDS,'x-hash-fields':contract.HASH_FIELDS,'x-runtime-schema-status':'HOLD_SEMANTIC_ROW_FRAME_WITNESS_MAPPING','x-hash-domain':'Canonical UTF-8 JSON sorted keys/no whitespace; omit only fixture_manifest_sha256 from its own digest; no timestamp exclusions'}
    save('FIXTURE-SCHEMA.json',schema)
    policy={'POLICY_FIXTURE_AUTHORITY':'TEST_ONLY','NUMERIC_POLICY_ADOPTED':'NO','PRODUCTION_POLICY_ELIGIBLE':'NO','marker':'TEST_ONLY_NONAUTHORITATIVE','policy_class':'STATE_TRANSITION_DESIGN_V1','fields':[{'NAME':n+('_ACTUAL_US' if i%2==0 else '_TEST_MAX_US'),'VALUE':contract.POLICY_VALUES[i],'UNIT':'microseconds','WHY_REQUIRED':'Exercise exact frozen nesting/freshness/state guards; not a measured safety or production recommendation','TEST_SCOPE':'DISPOSABLE_DESIGN_ONLY','NOT_PRODUCTION_POLICY':'YES'} for i,n in enumerate([n for n in contract.POLICY_NAMES for _ in range(2)])]}
    save('POLICY-TEST-VALUES.json',policy)
    from generate_fixture import generate
    from validate_fixture import validate
    results=[];controls=[]
    for c in cases:
        r=generate('public-design-seed-v1',c['CASE_ID']);assert canonical(r)==canonical(generate('public-design-seed-v1',c['CASE_ID']))
        v=validate(r);assert v['MODEL_VALID'] and not v['POSITIVE_EXECUTION_ELIGIBLE'],v
        for name,field in contract.NEGATIVES.items():
            bad=copy.deepcopy(r)
            if field=='receipt_expires_at':bad['context'][field]='2026-10-11T00:00:01.000000Z'
            elif type(bad[field]) is int:bad[field]=bad[field]+1 if field=='service_role_oid' else 0
            elif field.endswith('_id'):bad[field]='11111111-1111-5111-8111-111111111111'
            elif field=='successor_sha256':bad[field]='0'*64
            else:bad[field]='WRONG_STATE'
            bad['fixture_manifest_sha256']=sha(canonical({k:v for k,v in bad.items() if k!='fixture_manifest_sha256'}));bv=validate(bad)
            assert not bv['MODEL_VALID'] and not bv['POSITIVE_EXECUTION_ELIGIBLE'],(c['CASE_ID'],name)
            controls.append({'CASE_ID':c['CASE_ID'],'NEGATIVE_CONTROL':name,'CHANGED_GOVERNED_DIMENSION':field,'DIGEST_RECOMPUTED':True,'MODEL_DENIED':True,'ACTUAL_SQL_EXECUTION':'NOT_RUN'})
        omission_n=0
        for field in schema['required']:
            bad=copy.deepcopy(r);del bad[field];bv=validate(bad);assert not bv['MODEL_VALID'] and not bv['POSITIVE_EXECUTION_ELIGIBLE'];omission_n+=1
        join_n=0
        for j in joins:
            bad=copy.deepcopy(r);del bad['model_rows'][j['SOURCE_RELATION']][j['SOURCE_KEY']];bad['fixture_manifest_sha256']=sha(canonical({k:v for k,v in bad.items() if k!='fixture_manifest_sha256'}));assert not validate(bad)['MODEL_VALID'];join_n+=1
        spoof=copy.deepcopy(r);spoof['runtime_evidence']={k:True for k in spoof['runtime_evidence']};spoof['fixture_manifest_sha256']=sha(canonical({k:v for k,v in spoof.items() if k!='fixture_manifest_sha256'}));assert not validate(spoof)['POSITIVE_EXECUTION_ELIGIBLE']
        results.append({'case_id':c['CASE_ID'],'deterministic_bytes_equal':True,'model_valid':True,'negative_dimensions_denied':13,'required_field_omissions_denied':omission_n,'join_omissions_denied':join_n,'fabricated_runtime_proofs_ineligible':True,'fixture_status':v})
    save('NEGATIVE-CONTROL-MATRIX.json',controls);save('VALIDATION-RESULTS.json',{'cases':results,'actual_positive_wrappers_executed':0,'native_protocol_changes':0,'full_authority_validation':'NOT_IMPLEMENTED_BY_DESIGN_MODEL','full_readiness_validation':'NOT_IMPLEMENTED_BY_DESIGN_MODEL','FAIL':0})
    # One candidate dry-run model, never represented as a validated positive fixture.
    save('CANDIDATE-MODEL.json',generate('public-design-seed-v1','claim'))
    md('POSITIVE-CASE-PRECONDITIONS.md','# Thirteen case contracts\n\nMachine-readable exact reviewed wrapper signatures and all required dimensions are in POSITIVE-CASE-PRECONDITIONS.json. These are candidate prerequisites, not execution authority. Full source predicate witness coverage remains HOLD.\n\n'+ '\n'.join(f"- {c['CASE_ID']}: {c['REQUIRED_EXPECTED_RESULT']}" for c in cases)+'\n')
    md('NEGATIVE-CONTROL-MATRIX.md','# Negative controls\n\nEach of 13 case models has all 13 one-dimension controls. Only its semantic field changes; the manifest digest is recomputed so denial is not merely checksum failure. All required top-level fields and every model join also have omission checks. JSON runtime-proof booleans never grant eligibility. These are model validator results; none is an actual frozen SQL negative-control PASS. The exact per-case matrix is in NEGATIVE-CONTROL-MATRIX.json.\n')
    md('AUTHORITY-JOIN-GRAPH.md','# Authority join graph — semantic closure HOLD\n\nAUTHORITY-JOIN-GRAPH.json defines 40 exact model joins, all required edge fields and no null/wildcard matching. Model relations are explicitly labelled and are not claimed as SQL table names. SOURCE-OBLIGATIONS.json preserves actual relation DDL, foreign keys and function bodies/calls across all 43 migrations.\n\nThe model covers identity -> live role catalog; allocation -> anchor/registry; binding -> readiness/policy/pointer; pointer -> attempt -> execution -> admission; approval -> original attestation -> accepted consumption; receipt -> execution/effect; ownership -> execution; reconciliation -> binding; tenant/source/principal/credential/grant/decision lineage.\n\nThe complete typed SQL predicate and original frame witness mapping is not yet independently certified. Lexical inventory is deliberately not called a complete semantic join graph. Every runtime-required join must be mapped to its actual relation/column keys and source guard before replacing this HOLD.\n')
    print(json.dumps({'candidate_case_contracts':13,'model_joins':len(joins),'negative_controls':len(controls),'full_contract_ready':False,'positive_execution':False,'historical_hashes_intact':True}))
if __name__=='__main__':main()
