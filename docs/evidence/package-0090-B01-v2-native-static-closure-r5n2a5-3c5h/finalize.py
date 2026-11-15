"""Verify preservation and seal C5H-only evidence; no prohibited runtime."""
import ast
import hashlib
import json
import pathlib
import subprocess

P=pathlib.Path(__file__).resolve().parent
R=P.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(P/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def canon(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
pre=read(P/'preflight.json')
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
assert all(sha(R/p)==h for p,h in pre['V043_sha256'].items())
reviews=[read(P/f'independent-review-{i}.json') for i in [1,2]]
assert not list(P.rglob('*.pyc'))
fixtures=read(P/'derived-fixture-registry.json')['fixtures']
assert len(fixtures)==350 and len({f['WITNESS_ID'] for f in fixtures})==350
for f in fixtures:
 h=f.pop('C5H_FIXTURE_HASH');assert canon(f)==h;f['C5H_FIXTURE_HASH']=h
 assert f['FIXTURE_COMPLETE']=='NO'
del fixtures
inventory=read(P/'fixture-field-inventory.json')
assert inventory['required_total']==inventory['available_before']+inventory['derived_C5H']+inventory['still_missing']
del inventory
predicates=read(P/'unique-predicate-registry.json')['predicates']
assert len(predicates)==49 and sum(p['status']=='DERIVED_C5H' for p in predicates)==43
results=read(P/'independent-static-evaluation.json')
assert len(results['canonical_cases'])==350
assert all(r['PROOF_STATUS']=='UNKNOWN' and r['OBSERVED_RESULT'] is None and not r['canonical_evaluation_executed'] for r in results['canonical_cases'])
gaps=read(P/'350-gap-decomposition.json')['gaps']
assert len(gaps)==350 and all(g['FINAL_GAP_CLASS']=='COMPOUND_GAP' and g['AUTHORITY_GAP_EXISTS']=='NO' for g in gaps)
for g in gaps:
 assert set(g['PREDICATE_INPUTS_REQUIRED'])==set(g['PREDICATE_INPUTS_AVAILABLE'])|set(g['PREDICATE_INPUTS_MISSING'])
 assert not set(g['PREDICATE_INPUTS_AVAILABLE'])&set(g['PREDICATE_INPUTS_MISSING'])
del gaps
F=P.with_name(P.name[:-1]+'f')
scoped=read(F/'seven-artifact-overrides.json')['overrides']
assert len(scoped)==7 and all(s['WITNESS_ID'].endswith('/catalog_row_omission') for s in scoped)
write('frozen-preservation.json',{
 'PROJECT_AUTHORITY_TRANSITION':'T8','EVENT':'FRESH_GENERATION_LEDGER_SUCCESSION',
 'preserved_rule':'SOURCE_GENERATION_CREDENTIAL_AUTHORITY_DOES_NOT_AUTOMATICALLY_TRANSFER_TO_TARGET_GENERATION',
 'no_new_derivations':['CREDENTIAL_MATERIAL_ROTATION_REQUIRED','PRINCIPAL_IDENTITY_CHANGE_REQUIRED','PARTICIPANT_SUBSTITUTION_NECESSARY','PARTICIPANT_SUBSTITUTION_SUFFICIENT','SOURCE_CREDENTIAL_DESTRUCTION_REQUIRED','TARGET_CREDENTIAL_DIFFERENCE_REQUIRED'],
 'I13':'Full source independence matrix and every C5G canonical principal context byte-preserved; no new identities assigned or equalized.',
 'I13_source':'docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/independence-matrix.json',
 'I13_source_sha256':sha(R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/independence-matrix.json'),
 'seven_exact_ids':[s['WITNESS_ID'] for s in scoped],
 'seven_scoped_rule':{'stage1':{'object':'REQUIRED_CATALOG_IDENTITY_ROW_EVIDENCE','domain':'EVIDENCE_AVAILABILITY','stage':'CATALOG_IDENTITY_EVIDENCE_RESOLUTION','result':'UNKNOWN'},'stage2':{'object':'TARGET_GENERATION_CREDENTIAL_AUTHORITY_QUALIFICATION','domain':'QUALIFICATION_DECISION','stage':'POST_EVIDENCE_RESOLUTION_QUALIFICATION_GATE','result':'REJECT'},'unknown_equals_reject':False,'scope':'Exact seven only','wire_conversion':False,'observed_proof_claimed':False},
 'seven_source_sha256':sha(F/'seven-artifact-overrides.json'),
 'architectural_questions_answered':0,'108_105_350_preserved':True,'N1':'OPEN_11_OF_12','V2':'FAIL_BLOCKED'})
imports={}
for n in ['close_gaps.py','static_evaluator.py','finalize.py']:
 tree=ast.parse((P/n).read_text(encoding='utf-8'))
 imports[n]=[ast.unparse(x) for x in tree.body if isinstance(x,(ast.Import,ast.ImportFrom))]
write('prohibited-contact-audit.json',{
 'scope':'Performed actions in C5H primary session and two explicitly constrained reviewers. This does not assert anything about unrelated machine processes.',
 'action_ledger':[
  {'actions':'Read request attachment via Get-Content UTF8; local Get-Content/rg/Get-ChildItem/Select-Object of frozen authority and evidence','effect':'Read only'},
  {'actions':'git status, rev-parse, branch --show-current, diff --name-only, diff --cached --name-only, ls-files --others --exclude-standard, merge-base --is-ancestor','effect':'Read-only Git; no add/commit/push'},
  {'actions':'Inline Python pathlib/json/hashlib inspections of frozen source, schemas, manifest and historical byte hashes; importlib.util.find_spec local availability check only','effect':'Local static inspection; no package install/network'},
  {'actions':'apply_patch C5H evidence scripts; python -B close_gaps.py (iterated after local accounting/parser/source-dependency fixes); pure in-memory expression tests and partial model-fragment evaluations','effect':'Only C5H evidence writes; canonical attack suite not invoked'},
  {'actions':'Two independent review tasks: local read-only Git/Python inspections; reviewed scripts, field/hash/source facts; each writes own C5H review JSON','effect':'No native/build/SQL/DB/network. Reviewers removed only the C5H pycache files accidentally created by their initial imports; no historical artifact changed.'},
  {'actions':'Copy-Item of supplied request to C5H/project-authority-input.txt','effect':'New authority-input copy only'},
  {'actions':'python -B finalize.py','effect':'Final integrity verification and C5H-only sealing'}],
 'inspected_script_imports':imports,
 'execution_inspection':'static_evaluator has no IO. close_gaps/finalize use only local file operations and read-only git subprocess commands. No database driver/client, Docker/Compose/container, Gradle/build, native process, network API, SQL, V043/B02 migration, or attack runner executed.',
 'SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','NETWORK_CONTACT_FOR_PROOF':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO',
 'evidence_limit':'Action/script audit rather than OS packet capture. Scope is this gate, not preexisting host state.'})
summary=read(P/'final-summary.json')
summary['INDEPENDENT_REVIEW_1']=reviews[0].get('status',reviews[0].get('result'))
summary['INDEPENDENT_REVIEW_2']=reviews[1].get('status',reviews[1].get('result'))
assert summary['INDEPENDENT_REVIEW_1'] and summary['INDEPENDENT_REVIEW_2']
summary['FULL_C5H_CLOSURE_OBJECTIVE']='NOT_COMPLETED'
summary['EXACT_INSTANTIATED_FIXTURE_FIELD_UNIVERSE']='NOT_ESTABLISHED'
summary['MAXIMUM_STATIC_CLOSURE']='NOT_ESTABLISHED'
summary['NATIVE_SUBPREDICATES_OBSERVED_AVAILABLE']=sum(r['NATIVE_SUBPREDICATE_OBSERVATION']['availability']=='AVAILABLE' for r in results['canonical_cases'])
summary['FIELD_FRAGMENT_OBSERVATIONS']=len(results['field_fragment_observations'])
summary['KNOWN_LIMITATION']='Field totals count declared schema slots and binding/trace obligations, not a complete instantiated row/field universe. Evaluator totals count native violation subpredicates, not complete canonical decisions. No full fixture or canonical proof closed.'
write('static-validation.json',{'status':'PASS_FOR_SOURCE_INTEGRITY_AND_CONSERVATIVE_ACCOUNTING_ONLY','historical_hashes_verified':9270,'packet_count':350,'fixture_hashes_verified':350,'unique_native_violation_predicates':49,'native_subpredicate_evaluators_derived':43,'full_canonical_decision_evaluators':0,'canonical_witness_proofs':0,'gap_sum':350,'result_sum':350,'field_obligation_partition_verified':True,'eligible_complete_fixtures':0,'V043_preserved':True,'tracked_dirty':0,'staged':0,'maximal_closure':'NOT_ESTABLISHED','full_objective':'NOT_COMPLETED'})
prior=set(pre['authorized_paths'])
untracked=set(git('ls-files','--others','--exclude-standard').splitlines())
assert not prior-untracked
unauthorized=[x for x in untracked-prior if not x.startswith(P.relative_to(R).as_posix()+'/')]
assert not unauthorized
future=['SHA256-MANIFEST.json','final-return.txt']
summary['UNTRACKED_FILES_AFTER']=len(untracked)+sum(not (P/n).exists() for n in future)
summary['UNAUTHORIZED_UNTRACKED_COUNT']=0
write('final-summary.json',summary)
write('coverage-accounting.json',summary)
(P/'final-return.txt').write_text('\n'.join(f'{k}={str(v).lower() if isinstance(v,bool) else v}' for k,v in summary.items())+'\n',encoding='utf-8')
write('SHA256-MANIFEST.json',{'algorithm':'SHA256','self_excluded':True,'files':{p.relative_to(R).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}})
assert all(sha(R/p)==h for p,h in read(P/'SHA256-MANIFEST.json')['files'].items())
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER']
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
print(json.dumps(summary,indent=2))
