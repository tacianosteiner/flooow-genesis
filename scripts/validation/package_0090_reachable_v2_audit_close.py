"""Post-proof audit: strict cleanup/denominator checks before release closure.

This postprocessor is outside the already-frozen target recipe vector. It
never changes expectations or target observations and performs no database DDL.
"""
import collections,json,tempfile
from pathlib import Path
import package_0090_source_closure as q
from package_0090_reachable_v2 import OUT,save
import package_0090_reachable_v2_release as release

def keys(runtime):return {(c.get('group'),c['name']) for c in runtime['cases']}

def main():
 digest=release.verify_lock();inputs=release.get('independent-input-freeze-v2.json');preflight=json.loads((q.ROOT/inputs['preflight_artifact']).read_text());targets=[];checks=[]
 def check(name,condition,details):
  q.require(condition,name);checks.append(dict(name=name,passed=True,details=details))
 for n in [1,2]:
  runtime=release.get('target-'+str(n)+'/foundation-runtime.json');targets.append(runtime)
  check('complete_case_set_target_'+str(n),keys(runtime)==keys(preflight) and len(keys(runtime))==len(runtime['cases']),dict(expected=len(keys(preflight)),observed=len(runtime['cases'])))
  check('all_cases_pass_target_'+str(n),not runtime['errors'] and all(c['passed'] for c in runtime['cases']),dict(cases=len(runtime['cases'])))
  check('all_owned_resources_removed_target_'+str(n),runtime['owned_runtime_destroyed'] is True and len(runtime['cleanup'])==3 and {c['kind'] for c in runtime['cleanup']}=={'container','network','volume'} and all(c['removed'] is True for c in runtime['cleanup']),runtime['cleanup'])
  for row in runtime['cleanup']:
   command=['docker','inspect',row['name']] if row['kind']=='container' else ['docker',row['kind'],'inspect',row['name']]
   result=q.command(command,check=False)
   check('resource_absent_target_'+str(n)+'_'+row['kind'],result.returncode!=0,dict(kind=row['kind'],name=row['name'],inspect_exit=result.returncode))
  check('manifest_lock_target_'+str(n),runtime['expected_manifest_sha256_before']==digest==runtime['expected_manifest_sha256_after'],digest)
  check('frozen42_target_'+str(n),len(runtime['frozen_inputs'])==42 and runtime['frozen_inputs']==preflight['frozen_inputs'],dict(count=len(runtime['frozen_inputs'])))
  check('fixture_inputs_target_'+str(n),runtime['input_hashes']==preflight['input_hashes'],runtime['input_hashes'])
  check('no_canonical_execution_target_'+str(n),runtime['canonical_v043_submitted'] is False and runtime['canonical_v043_executed'] is False and runtime['active_fixture_ready'] is False,dict(live_eligible=False))
 check('independent_resource_identity',targets[0]['isolation']['id']!=targets[1]['isolation']['id'] and targets[0]['isolation']['volume']!=targets[1]['isolation']['volume'] and targets[0]['isolation']['project']!=targets[1]['isolation']['project'],dict(targets=[t['isolation'] for t in targets]))
 # Foundation finally unlinks both credential files even on errors. Check the
 # corresponding private recipe directories as a second read-only observation.
 retained=[str(p) for p in Path(tempfile.gettempdir()).glob('flooow-0090-ledger-foundation-*') if (p/'postgres-password').exists() or (p/'flyway.properties').exists()]
 check('foundation_credentials_absent',not retained,dict(retained_credential_directories=retained))
 release.close()
 save('post-proof-integrity-v2.json',dict(checks=checks,postprocessor_sha256=q.sha(Path(__file__).read_bytes()),scope='Post-proof audit only; this script was not part of expected provider derivation or target runtime recipe and does not replace the frozen input vector',manifest_sha256=digest))
 counts=collections.Counter(c.get('group','FOUNDATION') for c in targets[0]['cases']);unique=len(keys(targets[0]))
 save('test-accounting-v2.json',dict(runtime_distinct=unique,runtime_groups=dict(counts),runtime_repeated_executions=sum(len(t['cases']) for t in targets),manifest_runtime_distinct=1,reproducibility_distinct=1,total_distinct=unique+2,closure_assertions_separately_recorded=len(checks),closure_assertions_not_inflated_into_runtime_count=True,failures=0,development_attempts_not_final_acceptance=True,parser_inventory_not_counted_as_tests=True))
 save('READINESS.json',dict(status='EXPECTED_MANIFEST_CLOSED_RUNTIME_MATCHED_REPRODUCIBLE',expected_manifest_complete=True,expected_manifest_runtime_match=True,expected_manifest_reproducible=True,manifest_sha256=digest,currentness_mutation_classes_required=release.get('mutation-class-denominator-v3.json')['total'],semantic_bound=False,live_S04_eligible=False,V043_fence_present=True,canonical_V043_mutated=False,canonical_V043_executed=False,canonical_S04_executed=False,readiness_created=False,header_registered=False,auditor_slot_activated=False,currentness_generator_implemented=False,T10_fence_implemented=False,mutation_campaign_executed=False,TOCTOU_campaign_executed=False,benchmark_100us_executed=False,execution_authority='BLOCKED',recovery_authority='BLOCKED',Room_operational=False,shared_or_production_contacted=False,findings_scope='Independent reachable expectations/manifest/reproducibility only; no global Package0090 review',findings=dict(BLOCKER=[],HIGH=[],MEDIUM=[],LOW=[]),residual_risks=['No final-consumer currentness invalidation implementation/proof','No live corrected-source approval/readiness/native/guard eligibility proof','100us feasibility/currentness is unproven in this tranche','Opaque PostgreSQL C/internal providers bind to exact immutable artifacts and source, not full global SQL expansion','HOST_PLATFORM and external TEST audit root are explicit trust assumptions; no production WORM/HSM proof'],next='Define and govern complete qualification-generation/final-consumer invalidation design against mutation-class-denominator-v3, including all mutators; do not execute this next tranche.'))
 print(json.dumps(dict(complete=True,tests=unique+2,mutation_classes=release.get('mutation-class-denominator-v3.json')['total'],strict_integrity_checks=len(checks))))

if __name__=='__main__':main()
