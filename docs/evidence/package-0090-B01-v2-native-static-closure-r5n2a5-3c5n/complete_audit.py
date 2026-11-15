"""Reconcile discovery counts with independently qualified source pointers."""
import json,pathlib
P=pathlib.Path(__file__).resolve().parent
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def write(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
sources=read('newly-recovered-sources')['entries'];registry=read('static-search-surface-registry');qualified={}
for s in sources:
    for r in s['PROVENANCE']:qualified.setdefault(r['path'],set()).add(r['pointer'])
for surface in registry['surfaces']:
    pointers=sorted(qualified.get(surface['PATH_OR_ARTIFACT'],set()))
    surface.update(QUALIFIED_SOURCE_DEFINITION_POINTERS=pointers,QUALIFIED_SOURCE_DEFINITION_POINTER_COUNT=len(pointers),QUALIFICATION_COUNT_UNIT='Unique exact source-definition pointers, separate from lexical occurrence counts',SEMANTIC_QUALIFICATION_SCOPE='Only listed literal source-definition pointers; remaining semantic source/admission search is open')
registry['pattern_sets']['identity']=['model_id','selected_view','exact_variant','sender_enrollment','sql_role_oid']
registry['pattern_sets']['types']=['bytes32','u64','oid','natural_key','canonical_tuple']
write('static-search-surface-registry',registry)
front=read('minimum-blocker-frontier');summary=read('final-summary')
summary['STATIC_RECOVERABLE_BLOCKERS']=sum(b['BLOCKER_CLASS']=='STATIC_SOURCE_RECOVERABLE' for b in front['blockers'])
summary['SOURCE_IDENTITY_AMBIGUOUS_BLOCKERS']=sum(b['BLOCKER_CLASS']=='SOURCE_IDENTITY_AMBIGUOUS' for b in front['blockers'])
summary['EXHAUSTIVE_SEMANTIC_QUALIFICATION']='NOT_ESTABLISHED'
summary['QUALIFIED_CANDIDATE_COUNT_SCOPE']='Exact required remaining source, excludes merely qualified raw components'
write('final-summary',summary)
sat=read('saturation-analysis')
sat['basis']='Remaining roots include source-identity and existing admission gaps; material native/SQL source-specific semantic avenues remain. Most roots are not proven dependent on a nonstatic blocker. Improvement percentage is not used.'
sat['authority_blocked_scope']='Existing frozen source authentication/admission evidence, not a newly required normative project-authority decision.'
write('saturation-analysis',sat)
write('execution-sequence',dict(reproduction=['python -B run_gate.py','python -B complete_audit.py','python -B validate.py','independent adversarial reviews against stable artifacts','python -B finalize.py'],no_historical_generator_executed=True,new_gate_only=True))
print(json.dumps(dict(status='AUDIT_RECONCILED',qualified_pointer_files=len(qualified),static_recoverable_blockers=summary['STATIC_RECOVERABLE_BLOCKERS'],identity_ambiguous_blockers=summary['SOURCE_IDENTITY_AMBIGUOUS_BLOCKERS'])))
