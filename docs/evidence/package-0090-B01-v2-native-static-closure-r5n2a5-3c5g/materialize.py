"""C5G evidence only. No SQL, network, native execution, or historical writes."""
import collections
import hashlib
import json
import pathlib
import subprocess
import copy
import functools

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).resolve().parent
F = OUT.with_name(OUT.name[:-1] + 'f')
D = OUT.with_name(OUT.name[:-1] + 'd')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
@functools.lru_cache(maxsize=None)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
def write(n,x): (OUT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def rel(p): return p.relative_to(ROOT).as_posix()

assert git('rev-parse','--show-toplevel').lower() == ROOT.as_posix().lower()
assert git('branch','--show-current') == 'checkpoint/package-0090-cloud-handoff'
assert git('rev-parse','HEAD') == '451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert subprocess.run(['git','merge-base','--is-ancestor','cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','HEAD'],cwd=ROOT).returncode == 0
receipt=read(F/'scope-receipt.json')
authorized=set(receipt['new_paths']+receipt['prior_authorized_untracked_paths_preserved'])
actual=set(git('ls-files','--others','--exclude-standard').splitlines())
assert len(authorized)==148
assert all(p.startswith(rel(OUT)+'/') for p in actual-authorized), actual-authorized
assert not authorized-actual
historical=read(F/'preflight.json')['preexisting_sha256']
historical.update({p:sha(ROOT/p) for p in authorized})
assert all(sha(ROOT/p)==h for p,h in historical.items())
manifests=[]
for m in ROOT.glob('docs/evidence/*3c5*/SHA256-MANIFEST.json'):
    if m.parent==OUT: continue
    for p,h in read(m)['files'].items(): assert sha(ROOT/p)==h,(m,p)
    manifests.append({'path':rel(m),'sha256':sha(m),'entries':len(read(m)['files'])})
records=read(F/'derived-canonical-350-registry.json')['case_records']
assert len(records)==350 and len({r['WITNESS_ID'] for r in records})==350
assert all(r['DECISION_PREDICATE_COMPLETE'] and r['AUTHORITY_CHAIN_COMPLETE'] and r['STATUS']=='SPEC_COMPLETE_NOT_EVALUATED' for r in records)
write('preflight.json',{'status':'PASS','head':git('rev-parse','HEAD'),'baseline':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','baseline_ancestor':True,'tracked_dirty':0,'staged':0,'historical_sha256':historical,'manifests':manifests,'registry_sha256':sha(F/'derived-canonical-350-registry.json'),'V043_sha256':read(F/'preflight.json')['V043_sha256']})
write('resumption-reconciliation.json',{'status':'PASS','git_status_untracked_entries_before':14,'authorized_untracked_files_before':148,'paths':sorted(authorized),'provenance':'Exact C5F scope-receipt prior paths plus new paths; all historical bytes and nine manifests verified. materialize.py is the first new C5G-only file.','unauthorized_count':0})
models=read(D/'baseline-models.json')['models']
artifacts={x['WITNESS_ID']:x for x in read(D/'artifact-specification.json')['case_packages']}
overrides=read(F/'seven-artifact-overrides.json')['overrides']
assert len(overrides)==7
for override in overrides:
    artifact=copy.deepcopy(artifacts[override['WITNESS_ID']])
    application=override['override_application']
    artifact['current_status']=application['set_current_status']
    artifact['output_schema']['spec_version']=application['set_spec_version']
    for field in application['retire_legacy_output_fields']:
        artifact['output_schema'].pop(field,None)
    artifact['output_schema'].update(application['authoritative_expected_schema'])
    artifact['future_proof_needed']=application['replace_future_proof_needed']
    artifact['expected_predicate_ref']=override['new_expected_predicate']
    artifact['C5F_override_provenance']={'path':rel(F/'seven-artifact-overrides.json'),'sha256':sha(F/'seven-artifact-overrides.json'),'override':override}
    artifacts[override['WITNESS_ID']]=artifact
packets=[]
facts=[]
source_checks={}
for i,r in enumerate(records):
    chain={k:r[k] for k in ['SOURCE_PROVENANCE','AUTHORITY_FOR_BASELINE','AUTHORITY_FOR_MUTATION','AUTHORITY_FOR_DECISION']}
    for refs in chain.values():
        for ref in refs:
            p=ref['path']; assert sha(ROOT/p)==ref['sha256'],p
            source_checks[p]=ref['sha256']
    model=models[r['BASELINE_STATE']['library_model_id']]
    # These are observations of immutable artifacts, never authority decisions.
    obs={'baseline_parameter_schema_present':bool(model),'concrete_baseline_binding_present':r['BASELINE_STATE']['instantiated_values_present'],'mutation_descriptor_present':bool(r['MUTATION']['definition']),'architecture_dependency':r['ARCHITECTURAL_DEPENDENCY'],'evaluated_native_decision':None,'post_mutation_state':None}
    assert obs['concrete_baseline_binding_present'] is False
    missing=[{'kind':'STATIC_TYPED_FIXTURE_BINDING','requirement':artifacts[r['WITNESS_ID']]['required_inputs'],'baseline_model':r['BASELINE_STATE']['library_model_id']}, {'kind':'INDEPENDENT_STATIC_DECISION_TRACE','requirement':'Evaluate actual fully bound state and exact mutation under source schemas; expected_decision is an assertion, not an executable observation.'}]
    if r['ARCHITECTURAL_DEPENDENCY']: missing.append({'kind':'FROZEN_ARCHITECTURAL_DEPENDENCY','requirement':r['ARCHITECTURAL_DEPENDENCY']})
    packet={'WITNESS_ID':r['WITNESS_ID'],'SPECIFICATION_HASH':canon(r),'AUTHORITY_CHAIN_HASH':canon(chain),'BASELINE_INPUT':{'state':r['BASELINE_STATE'],'parameter_model':model,'binding_status':'PARAMETRIC_ONLY_NOT_AN_INSTANTIATED_VALID_BASELINE'},'MUTATION_INPUT':r['MUTATION'],'DECISION_PREDICATE':r['EXPECTED_DECISION_PREDICATE'],'REQUIRED_INPUTS':artifacts[r['WITNESS_ID']]['required_inputs'],'AVAILABLE_INPUTS':{'canonical_record':r,'authority_chain':chain,'schema_library':{'path':rel(D/'schema-library.json'),'sha256':sha(D/'schema-library.json')},'artifact_specification':artifacts[r['WITNESS_ID']]},'MISSING_INPUTS':missing,'PROOF_METHOD':'IMMUTABLE_ARTIFACT_EVALUATION','EXPECTED_RESULT':r['EXPECTED_DECISION_PREDICATE'],'EXPECTED_RESULT_SOURCE':{'path':rel(F/'derived-canonical-350-registry.json'),'pointer':f'/case_records/{i}/EXPECTED_DECISION_PREDICATE','sha256':sha(F/'derived-canonical-350-registry.json')},'OBSERVED_STATIC_RESULT':obs,'OBSERVED_RESULT_SOURCE':{'evaluator':rel(OUT/'materialize.py'),'inputs':'Actual baseline model and instantiation flag read independently of expected decision; only availability/structure observed. No witness proposition evaluated.'},'PROOF_STATUS':'UNKNOWN','PROOF_PROVENANCE':{'canonical_registry_sha256':sha(F/'derived-canonical-350-registry.json'),'canonical_index':i,'hash_algorithm':'SHA256 canonical JSON: UTF8, sorted keys, compact separators, ensure_ascii=False','no_expected_result_injection':True},'RUNTIME_REQUIRED':False,'RUNTIME_REQUIREMENT_REASON':'Not established: supplied specification explicitly permits future static concrete or mechanically bound symbolic fixture. No evidence establishes that SQL/runtime is necessary.','BASELINE_STATE':r['BASELINE_STATE'],'EXACT_MUTATION':r['MUTATION'],'POST_MUTATION_STATIC_STATE':None,'OBSERVABLE_STATIC_FACTS':obs,'OBSERVED_DECISION':None,'EXPECTED_OBSERVED_INDEPENDENCE':'Availability observation independent of expected outcome; insufficient for witness proof.','T8_PRESERVATION':r.get('T8_compatibility'),'I13_PRESERVATION':r['PRINCIPAL_CONTEXT']['I13']}
    packets.append(packet)
    facts.append({'WITNESS_ID':r['WITNESS_ID'],'PROOF_STATUS':'UNKNOWN','OBSERVED_STATIC_RESULT':obs,'missing_inputs':missing})
write('canonical-350-proof-packet-registry.json',{'total':350,'packets':packets,'scope':'Materialized immutable proof inputs, including complete parameter models; no fixture completeness or canonical decision proof claimed.'})
write('source-integrity.json',source_checks)
write('baseline-input-inventory.json',[{'WITNESS_ID':p['WITNESS_ID'],'baseline_hash':canon(p['BASELINE_INPUT']),'bound':False,'missing':p['MISSING_INPUTS']} for p in packets])
write('mutation-input-inventory.json',[{'WITNESS_ID':p['WITNESS_ID'],'mutation':p['MUTATION_INPUT'],'mutation_hash':canon(p['MUTATION_INPUT']),'executed':False,'post_state':None} for p in packets])
write('static-evaluation-results.json',{'scope':'Immutable input availability evaluation, not canonical predicate execution','results':facts})
write('proof-method-inventory.json',{'IMMUTABLE_ARTIFACT_EVALUATION':350,'PURE_STATIC_DERIVATION':0,'DETERMINISTIC_IN_MEMORY':0,'FUTURE_ISOLATED_RUNTIME_REQUIRED':0,'reason':'All canonical records explicitly lack bound baseline values. Static authority decisions cannot be observed from normative result assertions. No runtime necessity inferred from missing static fixtures.'})
write('expected-observed-independence-audit.json',{'evaluated_witness_propositions':0,'availability_evaluations':350,'independent_witness_proofs':0,'cases':[{'WITNESS_ID':p['WITNESS_ID'],'expected_source':p['EXPECTED_RESULT_SOURCE'],'observed_source':p['OBSERVED_RESULT_SOURCE'],'sufficient_for_proof':False} for p in packets]})
write('tautology-audit.json',{'TAUTOLOGICAL_PROOFS_DETECTED':0,'TAUTOLOGICAL_PROOFS_REJECTED':0,'TAUTOLOGICAL_PROOFS_ACCEPTED':0,'proof_candidates_submitted':0,'shortcut_rejected_for_all_350':'Copying expected decision or evaluating normative mapping alone cannot prove system enforcement. No such proof was submitted or accepted.','seven_case_rule':'UNKNOWN evidence availability and REJECT qualification remain separate; prospective mapping is normative only.'})
write('runtime-required-contracts.json',{'contracts':[],'count':0,'reason':'No runtime requirement established. All 350 are UNKNOWN for missing static binding/trace, not runtime-required by convenience.'})
write('bounded-static-gap-contracts.json',{'next_gate':'BOUNDED_STATIC_WITNESS_PROOF_GAP_CLOSURE','contracts':[{'WITNESS_ID':p['WITNESS_ID'],'required_baseline_model':p['BASELINE_INPUT']['state']['library_model_id'],'required_inputs':p['REQUIRED_INPUTS'],'required_mutation':p['MUTATION_INPUT'],'required_observation':'A fully typed independently evaluated post-mutation state with complete source constraint and decision trace; no expected result as input to evaluator.','pass_predicate':p['DECISION_PREDICATE']['PASS'],'fail_predicate':p['DECISION_PREDICATE']['FAIL'],'unknown_predicate':p['DECISION_PREDICATE']['UNKNOWN_NOT_EVALUABLE'],'isolation':'Static/in-memory only; no existing DB or native runtime; frozen architecture remains unresolved.','cleanup':'C5G evidence retained; future artifacts in new evidence namespace only.','provenance':'Pin C5F registry, schema, model, actual fixture bindings, evaluator and trace hashes.'} for p in packets]})
summary={'BRANCH':git('branch','--show-current'),'BASELINE_HEAD':'cbc284f62d9bd09b7169b55c8d66a3c51a68c6cb','CURRENT_HEAD':git('rev-parse','HEAD'),'TRACKED_DIRTY_COUNT':0,'STAGED_COUNT':0,'GIT_STATUS_UNTRACKED_ENTRIES_BEFORE':14,'AUTHORIZED_UNTRACKED_FILES_BEFORE':148,'UNAUTHORIZED_UNTRACKED_COUNT':0,'RESUMPTION_RECONCILIATION':'PASS','PROJECT_AUTHORITY_TRANSITION':'T8','TRANSITION_RESOLVED':'YES','CANONICAL_CASES_TOTAL':350,'WITNESSES_TOTAL':350,'PROOF_PACKETS_TOTAL':350,'PURE_STATIC_DERIVATION':0,'IMMUTABLE_ARTIFACT_EVALUATION':350,'DETERMINISTIC_IN_MEMORY':0,'FUTURE_ISOLATED_RUNTIME_REQUIRED':0,'STATICALLY_PROVEN':0,'STATICALLY_DISPROVEN':0,'PROVEN':0,'DISPROVEN':0,'UNKNOWN':350,'NOT_EVALUATED_RUNTIME_REQUIRED':0,'CONTRADICTED':0,'TAUTOLOGICAL_PROOFS_DETECTED':0,'TAUTOLOGICAL_PROOFS_REJECTED':0,'TAUTOLOGICAL_PROOFS_ACCEPTED':0,'SUBSTITUTION_WITNESSES_REQUIRED':350,'SUBSTITUTION_WITNESSES_PROVEN':0,'SUBSTITUTION_WITNESSES_UNKNOWN':350,'POSTMASTER_CONTEXT_BINDING_RESOLVED':'NO','INTERNAL_SCOPE_RESOLVED':'NO','ATOMIC_BOUNDARY_RESOLVED':'NO','CANONICAL_INTERNAL_OBLIGATION_UNIVERSE_ESTABLISHED':'NO','CANONICAL_INTERNAL_OBLIGATIONS_TOTAL':'NOT_ESTABLISHED','ATOMIC_NORMATIVE_CANDIDATES_TOTAL':108,'AMBIGUOUS_CANDIDATES_PRESERVED':105,'CANONICAL_ATTACK_DENOMINATOR':350,'DENOMINATOR_CHANGED':'NO','ATTACKS_MATERIALIZED_THIS_GATE':0,'ATTACKS_EVALUATED_THIS_GATE':0,'N1_SUBSTITUTION_STATIC_WITNESSES':'OPEN','N1_DECISIONS_REQUIRED':12,'N1_DECISIONS_CLOSED':11,'N1_DECISIONS_OPEN':1,'V2_NATIVE_STATIC_DESIGN_PROOF':'FAIL','V2_NATIVE_STATUS':'BLOCKED','SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO','SELECTED_OUTCOME':'C_STATIC_WITNESS_GAPS_REMAIN','NEXT_EXECUTED':False,'NEXT_GATE':'BOUNDED_STATIC_WITNESS_PROOF_GAP_CLOSURE'}
write('coverage-accounting.json',summary)
write('primary-result.json',{'outcome':summary['SELECTED_OUTCOME'],'reason':'All 350 have materialized immutable parameter models and mutations, but no fully bound static baseline or independent decision trace. Do not manufacture complete fixtures with an all-valid assertion or infer runtime necessity.','limitations':'This gate evaluates supplied immutable proof inputs; it does not synthesize a complete typed fixture/evaluator for the native and graph models. No canonical proposition is proven or disproven.','next_gate':summary['NEXT_GATE']})
write('final-summary.json',summary)
print(json.dumps({'preflight':'PASS','packets':len(packets),'unknown':350,'historical_files_verified':len(historical)}))
