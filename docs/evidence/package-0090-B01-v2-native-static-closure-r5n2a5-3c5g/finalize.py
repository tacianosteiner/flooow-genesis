"""Read-only integrity verification and new C5G evidence sealing only."""
import hashlib,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent
R=P.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(P/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert git('rev-parse','HEAD')=='451265ff5b3d286eb4d27c4b3817c2f558f30123'
pre=read(P/'preflight.json')
assert all(sha(R/p)==h for p,h in pre['historical_sha256'].items())
packets=read(P/'canonical-350-proof-packet-registry.json')['packets']
source=read(P.with_name(P.name[:-1]+'f')/'derived-canonical-350-registry.json')['case_records']
assert len(packets)==len(source)==350
assert len({p['WITNESS_ID'] for p in packets})==350
for p,s in zip(packets,source):
 assert p['WITNESS_ID']==s['WITNESS_ID']
 assert p['AVAILABLE_INPUTS']['canonical_record']==s
 assert p['PROOF_STATUS']=='UNKNOWN' and p['OBSERVED_DECISION'] is None
 if p['WITNESS_ID'].endswith('/catalog_row_omission'):
  schema=p['AVAILABLE_INPUTS']['artifact_specification']['output_schema']
  assert 'calculated_native_decision' not in schema and 'stage_1_result' in schema and 'stage_2_result' in schema
assert all(sha(R/p)==h for p,h in pre['V043_sha256'].items())
reviews={n:read(P/f'independent-review-{n}.json') for n in [1,2]}
write('prohibited-contact-audit.json',{
 'scope':'Actions of this C5G tool session and its two reviewers; no assertion about unrelated preexisting machine activity.',
 'reviewed_action_ledger':[
  {'actions':'PowerShell Get-Content, Get-ChildItem, Select-Object; rg text search','effect':'Local read only'},
  {'actions':'PowerShell Copy-Item of supplied request attachment to C5G/project-authority-input.txt; Python AST inspection of two evidence scripts','effect':'New C5G authority provenance copy and local code inspection'},
  {'actions':'git status, branch --show-current, ls-files --others --exclude-standard, rev-parse, diff --name-only, diff --cached --name-only, merge-base --is-ancestor','effect':'Repository metadata read only'},
  {'actions':'Python JSON/pathlib/hashlib/collections inspections of source evidence; SHA256 historical and manifest checks','effect':'Local immutable evidence read only'},
  {'actions':'apply_patch of C5G materialize.py and finalize.py; Python materialize.py twice (second run corrects seven C5F artifact overrides)','effect':'Writes only new C5G evidence namespace; no historical writes'},
  {'actions':'Two independent reviewer tasks explicitly constrained to read-only Git/Python and their own C5G review JSON','effect':'Review evidence only; no runtime authority'},
  {'actions':'Python finalize.py','effect':'Final integrity checks and C5G evidence sealing only'}],
 'code_inspection':'Both evidence scripts use only local filesystem, JSON, hashing, copy/cache and allowlisted read-only git subprocesses. No socket, HTTP, database driver, psql, Docker, Gradle, native executable, SQL execution, migrations or attack runner invoked.',
 'SHARED_DB_CONTACTED':'NO','PRODUCTION_CONTACTED':'NO','EXISTING_LOCAL_DB_CONTACTED':'NO','V043_EXECUTED':'NO','B02_EXECUTED':'NO','GIT_ADD':'NO','COMMIT':'NO','PUSH':'NO',
 'evidence_limit':'Tool-action ledger and inspected executed scripts support absence of contact in this gate; no OS-level network packet capture was taken.'})
summary=read(P/'final-summary.json')
summary['INDEPENDENT_REVIEW_1']='COMPLETED_WITH_STATIC_MATERIALIZATION_LIMITATION'
summary['INDEPENDENT_REVIEW_2']='COMPLETED_WITH_STATIC_MATERIALIZATION_LIMITATION'
summary['MAXIMUM_STATIC_EVALUATION_COMPLETENESS']='NOT_ESTABLISHED'
summary['KNOWN_LIMITATION']='350 immutable proof-input packets materialized; full typed fixtures and independent predicate traces not materialized. No claim that static synthesis is impossible. Reviews do not prove witnesses.'
summary['UNTRACKED_FILES_AFTER']=len(git('ls-files','--others','--exclude-standard').splitlines())+sum(not (P/n).exists() for n in ['SHA256-MANIFEST.json','static-validation.json'])
summary['UNAUTHORIZED_UNTRACKED_COUNT']=len([p for p in git('ls-files','--others','--exclude-standard').splitlines() if p not in pre['historical_sha256'] and not p.startswith(P.relative_to(R).as_posix()+'/')])
assert summary['UNAUTHORIZED_UNTRACKED_COUNT']==0
write('final-summary.json',summary)
write('coverage-accounting.json',summary)
write('static-validation.json',{'status':'PASS_FOR_INTEGRITY_AND_CONSERVATIVE_ACCOUNTING_ONLY','historical_hashes_verified':len(pre['historical_sha256']),'exact_C5F_records_consumed':350,'C5F_artifact_overrides_applied':7,'unique_packet_ids':350,'status_sum':350,'method_sum':350,'tracked_dirty':0,'staged':0,'V043_unchanged':True,'maximal_proof_materialization':'NOT_ESTABLISHED','proof_closure':False})
write('SHA256-MANIFEST.json',{'algorithm':'SHA256','self_excluded':True,'files':{p.relative_to(R).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='SHA256-MANIFEST.json'}})
assert all(sha(R/p)==h for p,h in read(P/'SHA256-MANIFEST.json')['files'].items())
assert summary['UNTRACKED_FILES_AFTER']==len(git('ls-files','--others','--exclude-standard').splitlines())
print(json.dumps(summary,indent=2))
