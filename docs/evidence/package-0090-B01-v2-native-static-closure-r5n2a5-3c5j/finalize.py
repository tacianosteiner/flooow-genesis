"""Seal C5J continuation evidence after independent reviews; no old writes."""
import ast
import hashlib
import json
import pathlib
import subprocess

P=pathlib.Path(__file__).resolve().parent;R=P.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(P/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
pre=read(P/'preflight.json')
assert len(pre['historical_sha256'])==9328
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
assert all(sha(R/p)==h for p,h in pre['V043_sha256'].items())
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
assert git('branch','--show-current')=='checkpoint/package-0090-cloud-handoff'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert not list(P.rglob('*.pyc'))
reviews=[read(P/f'independent-review-{n}.json') for n in [1,2]]
decomp=read(P/'compound-static-gap-decomposition.json')
assert decomp['facts_total']==14566 and decomp['source_context_work_groups_total']==666
assert decomp['unresolved_blocker_groups_total']==602 and decomp['supporting_resolved_groups_total']==64
ids=[f for g in decomp['groups'] for f in g['FACT_IDS']]
assert len(ids)==len(set(ids))==14566
I=P.with_name(P.name[:-1]+'i')
old={f['FACT_ID']:f for f in read(I/'canonical-fact-registry.json')['facts']}
assert set(ids)==set(old)
for g in decomp['groups']:
 assert sum(g['statuses'].values())==len(g['FACT_IDS'])
 for status,count in g['statuses'].items():assert sum(old[x]['STATUS']==status for x in g['FACT_IDS'])==count
unit=read(P/'unit-verification.json');assert unit['status']=='PASS' and unit['exhaustive_normalized_unit_graph_checks']==11664
assert len(unit['negative_and_boundary_controls'])==17
extension=read(P/'local-evaluator-extension.json')
assert extension['new_scoped_local_program_implementations']==3 and extension['local_functions_available_with_declared_scope']==46
assert len(extension['affected_witnesses'])==21 and extension['all_affected_witnesses_remain_UNKNOWN']
assert all(x['EXPECTED_RESULT_CONSUMED']=='NO' and x['DATABASE_ACCESS']=='NO' and x['NETWORK_ACCESS']=='NO' for x in extension['new_programs'])
div=read(P/'source-scope-divergence.json')
assert div['GENERAL_PROVIDER_EQUIVALENCE'] is False and div['canonical_scope']['affected_current_canonical_witnesses']==0
write('prohibited-contact-audit.json',{
 'scope':'C5J tool actions and two independent reviewers; unrelated host activity not asserted.',
 'actions_reviewed':[
  'Read frozen I summary/manifest/registry and source acl.c/pg_authid.dat/schema definitions with local Get-Content/rg/Python.',
  'Read-only git status/rev-parse/branch/diff/ls-files; no add/commit/push.',
  'apply_patch new C5J role_closure.py, decompose_and_verify.py, finalize.py; no old source/evidence edits.',
  'python -B decompose_and_verify.py: local data grouping, 11664 in-memory generic unitgraph comparisons plus17 controls. No canonical attack runner.',
  'Independent local source/code/function/manifest/hash reviews; reviewers write only own C5J JSON.',
  'python -B finalize.py: preservation verification and new C5J-only seal.'
 ],
 'script_imports':{n:[ast.unparse(x) for x in ast.parse((P/n).read_text(encoding='utf-8')).body if isinstance(x,(ast.Import,ast.ImportFrom))] for n in ['role_closure.py','decompose_and_verify.py','finalize.py']},
 'inspected_effects':'Pure role evaluator has no IO. Orchestration uses local artifact reads/writes and read-only Git. No PostgreSQL endpoint, SQL, container, native/build, migration, network/package-fetch or canonical attack suite used.',
 'SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','NETWORK_CONTACT_FOR_PROOF':'NO','V043_EXECUTED':'NO','V043_CHANGED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO',
 'evidence_limit':'Performed-action and code audit; no machine-wide network packet capture.'})
write('preservation.json',{'historical_files_verified':9328,'historical_files_modified':0,'C5I_facts_or_statuses_modified':0,'T8':'FRESH_GENERATION_LEDGER_SUCCESSION; source credential authority does not automatically transfer','I13':'Full independent seven-slot/auxiliary separation unchanged; no real principal/credential/generation identities assigned','seven_case_mapping':'Exact scoped evidence availability UNKNOWN and qualification REJECT remain distinct; new local role functions emit neither qualification nor proof status','architectural_questions_resolved':0,'canonical_witness_denominator':350,'native_guard_template_denominator':49,'canonical_attacks_materialized':0,'canonical_attacks_evaluated':0,'N1':'OPEN_11_OF_12','V2':'FAIL_BLOCKED'})
summary=read(P/'final-summary.json')
for i,review in enumerate(reviews,1):summary[f'INDEPENDENT_REVIEW_{i}']=review.get('status',review.get('result'))
assert summary['INDEPENDENT_REVIEW_1'] and summary['INDEPENDENT_REVIEW_2']
summary['PROVENANCE_AND_PRESERVATION']='PASS'
summary['UNAUTHORIZED_UNTRACKED_COUNT']=0
summary['LOCAL_VALIDITY_SCOPE']='CONSUMED_TYPED_GRAPH_OPERANDS;ADMIN_R_NE_A;EXTERNAL_FULL_SOURCE_AND_CANONICAL_GATES_NOT_PROVEN'
write('static-validation.json',{'status':'PASS_FOR_BOUNDED_STATIC_ENGINEERING_PROGRESS','historical_hashes_verified':9328,'fact_partition_verified':14566,'work_groups':666,'unresolved_groups':602,'supporting_resolved_groups':64,'new_local_programs':3,'generic_unit_comparisons':11664,'boundary_controls':17,'affected_witnesses_not_proven':21,'complete_canonical_evaluators':0,'complete_canonical_fixtures':0,'canonical_proofs':0,'unknown':350,'V043_preserved':True,'tracked_dirty':0,'staged':0})
u=set(git('ls-files','--others','--exclude-standard').splitlines());prior=set(pre['authorized_paths'])
assert not prior-u and all(x.startswith(P.relative_to(R).as_posix()+'/') for x in u-prior)
summary['UNTRACKED_FILES_AFTER']=len(u)+sum(not (P/n).exists() for n in ['SHA256-MANIFEST.json','final-return.txt'])
write('final-summary.json',summary)
(P/'final-return.txt').write_text('\n'.join(f'{k}={str(v).lower() if isinstance(v,bool) else v}' for k,v in summary.items())+'\n',encoding='utf-8')
write('SHA256-MANIFEST.json',{'algorithm':'SHA256','self_excluded':True,'files':{p.relative_to(R).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}})
assert all(sha(R/p)==h for p,h in read(P/'SHA256-MANIFEST.json')['files'].items())
assert len(git('ls-files','--others','--exclude-standard').splitlines())==summary['UNTRACKED_FILES_AFTER']
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
print(json.dumps(summary,indent=2))
