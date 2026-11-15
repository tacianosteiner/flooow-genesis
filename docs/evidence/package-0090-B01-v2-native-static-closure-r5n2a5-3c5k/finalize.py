"""C5K conservative certification/preservation seal. Writes C5K only."""
import ast,collections,hashlib,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;R=P.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(P/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
pre=read(P/'preflight.json')
assert len(pre['historical_sha256'])==9349
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
assert all(sha(R/p)==h for p,h in pre['V043_sha256'].items())
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert not list(P.rglob('*.pyc'))
review=[read(P/f'independent-review-{i}.json') for i in [1,2]]
inventory=read(P/'49-function-inventory.json')['functions'];assert len(inventory)==49
assert len({x['FUNCTION_ID'] for x in inventory})==49 and sum(x['VALID'] for x in inventory)==2
assert all(not x['ALGORITHM_DISPROVEN'] for x in inventory)
assert sum(x['CANONICALLY_BINDABLE'] is True for x in inventory)==2
proof=read(P/'strict-function-certification-proofs.json');assert len(proof['proofs'])==21 and proof['counted_valid']==2
new=read(P/'remaining-three-operator-analysis.json');assert len(new['operators'])==3 and new['strictly_certified_new_functions']==0
unit=read(P/'all-49-unit-validation.json');assert len(unit['legacy_43_program_results'])==43
assert len(unit['new_three_results']['observations'])==189 and len(unit['new_three_results']['negative_controls'])==11
assert len(unit['J_three_role_program_comparisons'])==3 and all(v==192 for v in unit['J_three_role_program_comparisons'].values())
inputs=read(P/'canonical-input-binding-registry.json')['bindings'];outputs=read(P/'canonical-output-binding-registry.json')['bindings']
ic=collections.Counter(x['STATUS'] for x in inputs);oc=collections.Counter(x['STATUS'] for x in outputs)
assert len(inputs)==1526 and dict(ic)=={'AMBIGUOUS':595,'MISSING':805,'COMPLETE':126}
assert len(outputs)==350 and dict(oc)=={'MISSING':329,'COMPLETE':21}
assert all(x['STATUS']!='COMPLETE' for x in inputs if x['LAYER']=='NORMAL_FORM_CONTRACT_TO_FUNCTION' and not x['FUNCTION_STRICTLY_CERTIFIED'])
graph=read(P/'composition-graph.json');assert len(graph['nodes'])==763 and len(graph['edges'])==714 and graph['cycles']==0
assert collections.Counter(x['STATUS'] for x in graph['edges'])=={'MISSING':679,'COMPLETE':35}
dag=read(P/'canonical-decision-dag.json');assert dag['CANONICAL_DECISION_DAG_STATUS']=='INCOMPLETE_BINDING'
witnesses=read(P/'witness-evaluation.json')['evaluations']
assert len(witnesses)==350 and len({x['WITNESS_ID'] for x in witnesses})==350
assert all(x['PROOF_STATUS']=='UNKNOWN' and x['OBSERVED_RESULT'] is None for x in witnesses)
assert read(P/'canonical-evaluator-assembly.json')['COMPLETE_CANONICAL_DECISION_EVALUATORS']==0
F=P.with_name(P.name[:-1]+'f');scoped=read(F/'seven-artifact-overrides.json')['overrides']
write('frozen-preservation.json',{'PROJECT_AUTHORITY_TRANSITION':'T8','EVENT':'FRESH_GENERATION_LEDGER_SUCCESSION','rule':'SOURCE_GENERATION_CREDENTIAL_AUTHORITY_DOES_NOT_AUTOMATICALLY_TRANSFER_TO_TARGET_GENERATION','new_rotation_principal_replacement_substitution_necessity_sufficiency_destruction_or_target_difference_inferences':False,'I13':'Full independent seven-slot/21-pair and required auxiliary separation preserved; no real identities assigned or equated','seven_exact_ids':[s['WITNESS_ID'] for s in scoped],'typed_layers':['helper UNAVAILABLE proof-input state','domain EVIDENCE_AVAILABILITY UNKNOWN','qualification REJECT'],'unknown_equals_reject':False,'seven_only_order':'Bounded omission -> evidence UNKNOWN -> prerequisite unsatisfied -> qualification REJECT','new_global_mapping':False,'wire_code_conversion':False,'POSTMASTER_CONTEXT_BINDING_RESOLVED':'NO','INTERNAL_SCOPE_RESOLVED':'NO','ATOMIC_BOUNDARY_RESOLVED':'NO','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED':'NO','dependency_record':'Per-case frozen ARCHITECTURAL_DEPENDENCY declarations preserved; missing source/type binding not silently promoted to a new architectural answer.','historical_files_verified':9349,'historical_files_changed':0,'denominator':350,'normative_candidates':108,'ambiguities_preserved':105})
write('prohibited-contact-audit.json',{'scope':'C5K primary/reviewer performed actions; no claim about unrelated machine activity','actions_reviewed':['Read request/source/schema/manifest files via Get-Content,rg,local Python.','Read-only Git status/rev-parse/branch/diff/ls-files/merge-base.','apply_patch and targeted Python edits of new C5K helpers/artifacts only; copy exact request to C5K.','Compile only pure frozen H/I/J helper definitions, never import/run historical generators; python -B run_gate.py executes local UNIT operator comparisons and source/hash inspections.','Two initial independent source/code audits ended before final review due service usage limits; two new independent final reviewers completed24-topic audits and correction rereviews.','Preserve rejected unconditional VALID49 draft and first reviews under draft-certification-rejected; revise only current K certification.','python -B finalize.py verifies preservation/accounting and seals new K evidence.'],'script_imports':{n:[ast.unparse(x) for x in ast.parse((P/n).read_text(encoding='utf-8')).body if isinstance(x,(ast.Import,ast.ImportFrom))] for n in ['final_operators.py','validate_local.py','run_gate.py','finalize.py']},'inspection':'No database client/driver/SQL execution, endpoint access, container/Docker/Compose, native/build/migration/attack runner or network/package fetch. Proof helpers have no IO; only orchestration reads/writes local evidence and read-only Git.','SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','NETWORK_CONTACT_FOR_PROOF':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO','limit':'Code/tool-action audit, not host-wide packet capture.'})
write('minimum-binding-closure-contract.json',{'next_gate':'BOUNDED_CANONICAL_BINDING_CLOSURE','functions_requiring_strict_certification':[c['FUNCTION_ID'] for c in inventory if not c['VALID']],'required_artifacts_per_function':['Exact frozen source schema instantiation for every scalar/tuple/row/enum/collection input','Unique source actor/context/generation/principal/credential/pre-post stage selectors','Executable lossless extraction/normalization proof or exact source-parametric projection; matching names or identity over a new cell is insufficient','Output source-stage adapters and strong validation rereview'],'special_obligations':['Full source body/effect expansion authentication and lossless call projection, not digest-only verification','Actual creator and tagged logical primitive vs SQL admission identity with no physical fallback','Closed source primitive EffectLeaf normalization/canonical entry/resource admission','SET/INHERIT/current database owner/ADMIN scoped semantics remain frozen J; no broad self-superuser equivalence'],'source_values_may_remain_uninstantiated_for_structural_proofs':True,'do_not_invent_fixture_values_or_new_policy':True,'no_database_network_production_git_actions':True,'next_executed':False})
summary=read(P/'final-summary.json')
for i,r in enumerate(review,1):summary[f'INDEPENDENT_REVIEW_{i}']=r.get('status',r.get('result',r.get('verdict')))
assert summary['INDEPENDENT_REVIEW_1'] and summary['INDEPENDENT_REVIEW_2']
summary['STRICT_CERTIFICATION_COMPLETED_FOR_ALL_49']='NO'
summary['FULL_C5K_CLOSURE_OBJECTIVE']='NOT_COMPLETED'
summary['OUTCOME_C_SCOPE']='Earliest canonical-binding route;49 local implementations available, not49 strict function certifications.'
summary['PROVENANCE_AND_PRESERVATION']='PASS'
write('static-validation.json',{'status':'PASS_FOR_CONSERVATIVE_PARTIAL_C5K_REPORT','historical_hashes_verified':9349,'available_functions':49,'calculation_tested':49,'strictly_certified':2,'not_certified_for_all_required_properties':47,'algorithm_disproven':0,'remaining_new_operators_identified':3,'remaining_new_operators_implemented':3,'remaining_new_operators_strictly_certified':0,'new_local_unit_observations':189,'new_unavailable_controls':11,'old43_programs_replayed':43,'J_role_programs_replayed':3,'input_bindings':dict(ic),'output_bindings':dict(oc),'composition_edges':{'complete':35,'missing':679},'canonical_evaluators':0,'canonical_witnesses_proven':0,'unknown':350,'V043_preserved':True,'tracked_dirty':0,'staged':0,'rejected_VALID49_draft_preserved':True})
u=set(git('ls-files','--others','--exclude-standard').splitlines());old=set(pre['authorized_paths'])
assert not old-u and all(x.startswith(P.relative_to(R).as_posix()+'/') for x in u-old)
summary['UNAUTHORIZED_UNTRACKED_COUNT']=0
summary['UNTRACKED_FILES_AFTER']=len(u)+sum(not (P/n).exists() for n in ['SHA256-MANIFEST.json','final-return.txt'])
write('final-summary.json',summary);write('coverage-accounting.json',summary)
(P/'final-return.txt').write_text('\n'.join(f'{k}={str(v).lower() if isinstance(v,bool) else v}' for k,v in summary.items())+'\n',encoding='utf-8')
write('SHA256-MANIFEST.json',{'algorithm':'SHA256','self_excluded':True,'files':{p.relative_to(R).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}})
assert all(sha(R/p)==h for p,h in read(P/'SHA256-MANIFEST.json')['files'].items())
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER']
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
print(json.dumps(summary,indent=2))
