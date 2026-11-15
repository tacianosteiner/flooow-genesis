"""Verify and seal new C5I evidence. Historical bytes are read only."""
import ast
import hashlib
import json
import pathlib
import subprocess

P=pathlib.Path(__file__).resolve().parent
R=P.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def write(n,x):(P/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
pre=read(P/'preflight.json')
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert not list(P.rglob('*.pyc'))
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
assert all(sha(R/p)==h for p,h in pre['V043_sha256'].items())
reviews=[read(P/f'independent-review-{i}.json') for i in [1,2]]
registry=read(P/'canonical-fact-registry.json');facts={f['FACT_ID']:f for f in registry['facts']}
assert len(facts)==14566 and sum(f['PROJECTION_COUNT'] for f in facts.values())==93316
assert sum(f['PROJECTION_COUNT']>0 for f in facts.values())==14300
assert sum(f['PROJECTION_COUNT']==0 for f in facts.values())==266
assert all(f['DEPENDENT_WITNESSES'] and f['FACT_ID']=='FACT/'+canon(f['CANONICAL_KEY']) for f in facts.values())
status_counts={k:sum(f['STATUS']==k for f in facts.values()) for k in ['ESTABLISHED','DERIVABLE','UNRESOLVED_BINDING','UNRESOLVED_CARDINALITY','AUTHORITY_REQUIRED','RUNTIME_REQUIRED','CONTRADICTED']}
assert sum(status_counts.values())==14566
projections=read(P/'declared-slot-classification.json')['slots']
assert len(projections)==93316 and len({(p['WITNESS_ID'],p['C5H_SLOT_ORDINAL']) for p in projections})==93316
assert all(p['FACT_ID'] in facts for p in projections)
assert all(p['SLOT_CLASS']!='UNIQUE_CANONICAL_FACT' or not p['REPEATED_PROJECTION'] for p in projections)
assert sum(p['REPEATED_PROJECTION'] for p in projections)==79016
dedup=read(P/'projection-deduplication.json')
assert dedup['DEDUPLICATED_SLOT_COUNT']==93316-14300==79016
bindings=read(P/'binding-graph.json')['edges'];assert len(bindings)==903
assert all(set(e['SOURCE_FACT'])<=facts.keys() and set(e['CONTEXT_CARDINALITY_FACT_PREREQUISITES'])<=facts.keys() and e['LOSSLESS'] in ['YES','NO'] for e in bindings)
assert sum(e['STATUS']=='COMPLETE' for e in bindings)==56
assert sum(e['STATUS']=='AMBIGUOUS' for e in bindings)==847
dag=read(P/'canonical-decision-dag.json')
assert len(dag['nodes'])==1429 and len(dag['edges'])==721 and dag['CYCLES_DETECTED']==0
assert dag['UNBOUND_DECISION_INPUTS']==len(dag['unbound_normalized_guard_ports'])+len(dag['unbound_other_required_inputs'])==1626
for n in dag['nodes']:
 if n['NODE_KIND']=='BASELINE_PROJECTION':
  assert all(facts[f]['FACT_TYPE']!='MUTATION_BINDING_OBLIGATION' for f in n['INPUTS'])
fixtures=read(P/'witness-fixture-projections.json')['fixtures']
assert len(fixtures)==350 and len({f['WITNESS_ID'] for f in fixtures})==350
for f in fixtures:
 h=f.pop('FIXTURE_HASH');assert h==canon(f);f['FIXTURE_HASH']=h
 assert f['FIXTURE_COMPLETE']=='NO' and set(f['CANONICAL_FACT_IDS'])<=facts.keys()
 assert all(facts[x]['STATUS']=='UNRESOLVED_CARDINALITY' for x in f['MISSING_CARDINALITY_IDS'])
results=read(P/'static-evaluation-results.json')['results']
assert len(results)==350 and all(r['PROOF_STATUS']=='UNKNOWN' and r['OBSERVED_RESULT'] is None and not r['canonical_evaluation_executed'] for r in results)
valid=read(P/'subpredicate-evaluator-revalidation.json')
assert valid['valid']==43 and valid['invalid']==0 and valid['composable_into_complete_canonical_evaluator_now']==0
assert len(read(P/'subpredicate-unit-revalidation.json')['results'])==43
assert len(read(P/'blocked-evaluator-analysis.json')['classes'])==6
F=P.with_name(P.name[:-1]+'f');seven=read(F/'seven-artifact-overrides.json')['overrides']
write('frozen-preservation.json',{
 'PROJECT_AUTHORITY_TRANSITION':'T8','EVENT':'FRESH_GENERATION_LEDGER_SUCCESSION',
 'preserved_rule':'SOURCE_GENERATION_CREDENTIAL_AUTHORITY_DOES_NOT_AUTOMATICALLY_TRANSFER_TO_TARGET_GENERATION',
 'new_rotation_principal_replacement_substitution_necessity_sufficiency_destruction_or_target_difference_inferences':False,
 'I13':'Full independent seven-slot/21-pair plus required auxiliary separation remains cross-cutting; neither guard validity nor shared enum facts prove principal/credential equality or inequality.',
 'I13_source':{'path':'docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/independence-matrix.json','sha256':sha(R/'docs/evidence/package-0090-B01-v2-native-static-closure-r5n1/independence-matrix.json')},
 'seven_exact_ids':[s['WITNESS_ID'] for s in seven],
 'typed_separation':['INTERPRETER_UNAVAILABLE proof-evaluability','REQUIRED_CATALOG_IDENTITY_ROW_EVIDENCE availability UNKNOWN','TARGET_GENERATION_CREDENTIAL_AUTHORITY_QUALIFICATION REJECT','broader positive native qualification NOT_QUALIFIED'],
 'seven_only_order':'Exact bounded omission -> evidence availability UNKNOWN -> positive prerequisite unsatisfied -> qualification REJECT',
 'unknown_equals_reject':False,'global_mapping_created':False,'wire_code_conversion':False,
 'ordered_mapping_source_sha256':sha(F/'seven-artifact-overrides.json'),'normative_mapping_is_not_observed_proof':True,
 'POSTMASTER_CONTEXT_BINDING_RESOLVED':'NO','INTERNAL_SCOPE_RESOLVED':'NO','ATOMIC_BOUNDARY_RESOLVED':'NO','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED':'NO',
 'ATOMIC_NORMATIVE_CANDIDATES_TOTAL':108,'AMBIGUOUS_CANDIDATES_PRESERVED':105,'CANONICAL_ATTACK_DENOMINATOR':350,'DENOMINATOR_CHANGED':'NO'})
imports={}
for n in ['recover_model.py','revalidate.py','finalize.py']:
 t=ast.parse((P/n).read_text(encoding='utf-8'));imports[n]=[ast.unparse(x) for x in t.body if isinstance(x,(ast.Import,ast.ImportFrom))]
write('prohibited-contact-audit.json',{
 'scope':'C5I primary/reviewer tool actions only; not unrelated host activity.',
 'actions_reviewed':[
  {'actions':'Get-Content UTF8 request/source; rg/Get-ChildItem/Select-Object local inspections; inline Python json/pathlib/hashlib source/schema/manifest analysis','effect':'Read-only local artifacts'},
  {'actions':'git status, branch --show-current, rev-parse, diff --name-only, diff --cached --name-only, ls-files --others --exclude-standard, merge-base --is-ancestor','effect':'Read-only repository metadata'},
  {'actions':'apply_patch C5I evidence helpers; python -B recover_model.py (iterated on local unit-vector/schema/accounting refinements)','effect':'C5I-only structural/derived evidence writes; no historical generator execution'},
  {'actions':'Compile/execute hash-pinned C5H static_evaluator.py after import/side-effect inspection; generic UNIT_* operand controls for43 program templates','effect':'Pure in-memory predicate calculations only. Unit vectors never enter canonical fact registry/fixtures or canonical attack suite.'},
  {'actions':'Two independent reviewer tasks: local source/hash/slot/DAG/function audits and own C5I review JSON','effect':'No DB/network/native/build/SQL/git mutation; Python -B prevents pycache artifacts'},
  {'actions':'Copy-Item exact supplied request to C5I/project-authority-input.txt; python -B finalize.py','effect':'New evidence provenance copy, final integrity checks and C5I-only seal'}],
 'inspected_imports':imports,
 'execution_inspection':'Only read-only git subprocesses; no database client/driver/SQL, Docker/Compose/existing container, Gradle/build/native system, B02/V043/attack runner, socket/HTTP/package install or network proof fetch was used.',
 'SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','NETWORK_CONTACT_FOR_PROOF':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO',
 'limit':'Tool-action/code audit rather than OS packet capture; does not infer prohibited-contact absence from intent alone.'})
summary=read(P/'final-summary.json')
for i,r in enumerate(reviews,1):summary[f'INDEPENDENT_REVIEW_{i}']=r.get('status',r.get('result'))
assert summary['INDEPENDENT_REVIEW_1'] and summary['INDEPENDENT_REVIEW_2']
summary['FACT_COUNT_SCOPE']='SOURCE_SCOPED_VALUES_AND_BINDING_OBLIGATIONS_NOT_PHYSICAL_ROW_CENSUS'
summary['SUBPREDICATE_VALIDITY_SCOPE']='LOCAL_NORMALIZED_TYPED_FUNCTIONS;COMPLETE_CANONICAL_COMPOSITION_NOT_CERTIFIED'
summary['PHYSICAL_FACT_UNIVERSE_MINIMALITY']='NOT_ESTABLISHED'
summary['CANONICAL_MODEL_COMPLETENESS']='PARTIAL_WITH_EXPLICIT_BINDING_CARDINALITY_COMPOSITION_GAPS'
summary['INDEPENDENT_CANONICAL_OBSERVATIONS']=0
write('static-validation.json',{'status':'PASS_FOR_BOUNDED_STRUCTURAL_RECOVERY_AND_CONSERVATIVE_ACCOUNTING','historical_hashes_verified':9298,'declared_slots_verified':93316,'primary_scoped_facts':14300,'supplemental_source_cardinality_roots':266,'total_facts':14566,'status_partition':status_counts,'slot_projection_multiplicity':93316,'same_unit_slot_reduction':79016,'repeated_projection_flags_verified':79016,'slot_source_category_is_not_multiplicity_axis':True,'exact_witnesses':350,'bindings':903,'native_guard_templates':49,'functionally_revalidated_local_guards':43,'blocked_programs':6,'partial_DAG_nodes':1429,'partial_DAG_edges':721,'cycles':0,'complete_canonical_evaluators':0,'complete_fixtures':0,'canonical_proofs':0,'V043_unchanged':True,'tracked_dirty':0,'staged':0})
prior=set(pre['authorized_paths']);untracked=set(git('ls-files','--others','--exclude-standard').splitlines())
assert not prior-untracked and all(x.startswith(P.relative_to(R).as_posix()+'/') for x in untracked-prior)
summary['UNAUTHORIZED_UNTRACKED_COUNT']=0
summary['UNTRACKED_FILES_AFTER']=len(untracked)+sum(not (P/n).exists() for n in ['SHA256-MANIFEST.json','final-return.txt'])
write('final-summary.json',summary);write('coverage-accounting.json',summary)
(P/'final-return.txt').write_text('\n'.join(f'{k}={str(v).lower() if isinstance(v,bool) else v}' for k,v in summary.items())+'\n',encoding='utf-8')
write('SHA256-MANIFEST.json',{'algorithm':'SHA256','self_excluded':True,'files':{p.relative_to(R).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}})
assert all(sha(R/p)==h for p,h in read(P/'SHA256-MANIFEST.json')['files'].items())
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER']
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
print(json.dumps(summary,indent=2))
