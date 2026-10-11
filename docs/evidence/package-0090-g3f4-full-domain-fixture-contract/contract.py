"""Non-executing TEST_ONLY contract data. No database or native runtime imports."""
HEAD='c19644fc77ce930eeae7f83c2d219d8d5e07433f'
SUCCESSOR='6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7'
SOURCE='b0ea86b6ba355fdf25fe09836bd4b75e4a4a2ad88ab7ef0e4724ca0d5a013e7d'
VERSION=1
FIELDS='fixture_id fixture_version source_head successor_sha256 fixture_manifest_sha256 organization_id case_id order_id trace_id deployment_id incarnation_id service_identity service_role_oid allocation_id binding_id binding_generation policy_id policy_revision policy_hash approval_id approval_generation approval_hash attestation_id attestation_generation attestation_hash receipt_id receipt_generation execution_id attempt_id execution_generation ownership_state effect_state terminal_state reconciliation_state issued_at valid_from expires_at readiness_state watchdog_state census_state'.split()
UUID_FIELDS='fixture_id organization_id order_id trace_id deployment_id incarnation_id allocation_id binding_id policy_id approval_id attestation_id receipt_id execution_id attempt_id'.split()
GEN_FIELDS='binding_generation policy_revision approval_generation attestation_generation receipt_generation execution_generation'.split()
HASH_FIELDS='successor_sha256 fixture_manifest_sha256 policy_hash approval_hash attestation_hash'.split()
STATES=['NOT_READY','ELIGIBLE_FOR_TEST','READY_FOR_TEST_ONLY_SUCCESSOR_CONSUMPTION','QUARANTINED','DRAINING','RECONCILIATION_REQUIRED','TERMINAL']
POLICY_NAMES='TRANSACTION_TIMEOUT STATEMENT_TIMEOUT IDLE_IN_TRANSACTION_TIMEOUT LOCK_TIMEOUT ATTEMPT_VALIDITY EXECUTION_VALIDITY BINDING_VALIDITY ADMISSION_VALIDITY DELIVERY_OPERATION_WINDOW READ_TRANSACTION_TIMEOUT WATCHDOG_ENFORCEMENT_INTERVAL WATCHDOG_HEALTH_MAX_AGE DELIVERY_LOCAL_SAFETY_MARGIN PREFLIGHT_RECEIPT_TTL'.split()
# Fixture classes exercise nesting, not latency/safety suitability. All values us.
POLICY_VALUES=[1000000,2000000,500000,1000000,500000,1000000,100000,200000,4000000,8000000,3000000,6000000,8000000,16000000,1000000,2000000,500000,1000000,1000000,2000000,100000,200000,200000,400000,1000,2000,100000,200000]
CASES=[
 ('claim',['S01','S13'],'EXECUTOR','NONE','NONE','NONE','NOT_STARTED','CLAIMED; original absolute lease; one pointer; no effects'),
 ('verification',['S05','S06'],'VERIFIER','OWNED','NONE','NONE','NOT_STARTED','Original signed bytes verified; exact fresh ATTESTATION_VERIFIED receipt'),
 ('admission',['S16'],'EXECUTOR','OWNED','GRANT_APPLIED','NONE','NOT_STARTED','One ISSUED admission bound to exact credential/grant revisions'),
 ('ownership_acquisition',['S13'],'EXECUTOR','NONE','NONE','NONE','NOT_STARTED','One OWNED execution and possession digest; distinct claim receipt'),
 ('effect_transition',['S07','S08','S09','S10','S11','S12','S17','S18'],'ISSUER_AND_EXECUTOR','OWNED','ATTESTATION_VERIFIED','NONE','NOT_STARTED','Each actual committed stage appends its own exact receipt; no prefilled effects'),
 ('terminal_transition',['S18'],'EXECUTOR','OWNED','GRANT_APPLIED','NONE','NOT_STARTED','Actual decision -> EFFECTS_COMPLETE; admission CONSUMED; execution RELEASED; reconciliation REQUIRED'),
 ('retry_replay_denial',['S14','S15','S18'],'EXECUTOR','RELEASED','IDENTITY_DECISION_APPLIED','EFFECTS_COMPLETE','REQUIRED','Exact denial/non-replay result for selected overload; no renewed lease or second effect'),
 ('ownership_retention',['S02','S03'],'AUDITOR','OWNED','ATTESTATION_VERIFIED','NONE','NOT_STARTED','Failure leaves ownership retained; no synthetic release; reconciliation evidence preserved'),
 ('ownership_release',['S18'],'EXECUTOR','OWNED','GRANT_APPLIED','NONE','NOT_STARTED','Release only atomic with actual decision/effect and reconciliation REQUIRED'),
 ('reconciliation_required',['S18','S03'],'EXECUTOR_AND_AUDITOR','OWNED','GRANT_APPLIED','NONE','NOT_STARTED','Actual committed effect produces REQUIRED; no invented administrative completion'),
 ('reconciliation_completion',['S03'],'AUDITOR','RELEASED','IDENTITY_DECISION_APPLIED','EFFECTS_COMPLETE','REQUIRED','Read-only full snapshot then separate disposable administrative independent recomputation; never auditor UPDATE'),
 ('full_authority_joins',['S01','S05','S06','S16','S17','S18','S03'],'ALL_FOUR','OWNED','ATTESTATION_VERIFIED','NONE','NOT_STARTED','Every exact source/approval/signature/consumption/authorization join; missing one denies'),
 ('runtime_consumption',['S01','S13','S05','S06','S07','S08','S09','S10','S11','S12','S16','S17','S18','S03'],'ALL_FOUR','NONE','NONE','NONE','NOT_STARTED','Whole successor, exact isolated target, actual four service sessions, full fresh sequence; no fragment execution'),
]
NEGATIVES={'wrong_role_oid':'service_role_oid','wrong_deployment':'deployment_id','wrong_incarnation':'incarnation_id','old_allocation':'allocation_id','old_binding_generation':'binding_generation','old_approval_generation':'approval_generation','old_attestation_generation':'attestation_generation','expired_receipt':'receipt_expires_at','wrong_policy_revision':'policy_revision','wrong_execution_generation':'execution_generation','wrong_ownership_state':'ownership_state','wrong_reconciliation_state':'reconciliation_state','wrong_successor_hash':'successor_sha256'}
def cases(oracle):
    result=[]
    for name,wrappers,slot,own,effect,terminal,recon,expected in CASES:
        r={'CASE_ID':name,'WRAPPERS':[{'id':w,**oracle[w]} for w in wrappers],
           'REQUIRED_ROLES':{'caller':slot,'owners':'Existing frozen eight owner roles; no service membership/private/raw privilege'},
           'REQUIRED_ROLE_OIDS':'Four distinct live pg_roles OID+rolname+session_user matches; OID from fresh target catalog, never seed-generated as actual identity',
           'REQUIRED_LOGINS':'Four live LOGIN NOINHERIT nonprivileged roles; exact per-slot reviewed S grants, no raw access; auditor RR read-only, mutators RC read-write',
           'REQUIRED_DEPLOYMENT_IDENTITY':'Fresh TEST_ONLY deployment; exact header/readiness/admission equality; reject cloned target',
           'REQUIRED_INCARNATION':'Fresh incarnation, exact key/readiness/header/admission equality; restart invalidates all runtime observations',
           'REQUIRED_POLICY_STATE':'Immutable test-only 29-tag frame, actual/max int8 us, digest and exact revision; all nesting/freshness/time guards',
           'REQUIRED_READINESS_STATE':'Isolated READY_FOR_TEST_ONLY_SUCCESSOR_CONSUMPTION; live installed history/ACL/key evidence; synthetic health scoped as fixture, not native health PASS',
           'REQUIRED_APPROVAL_STATE':'Exact organization, plan, manifest hash, signer authority/key revisions, operation intent and active unrevoked validity; no equivalent matching',
           'REQUIRED_ATTESTATION_STATE':'Original exact canonical bytes+Ed25519 test signature; public key authority revision; expected original attestation match; no re-sign substitution',
           'REQUIRED_RECEIPT_STATE':'Only receipts from actual frozen producer/wrapper commits in predecessor stages; exact byte domain/tag/order/MAC and lineage; no fabricated receipt row',
           'REQUIRED_BINDING_STATE':'All 40 header columns and frozen constraints; ACTIVE lifecycle; claim_permitted current pointer; no tombstone reuse',
           'REQUIRED_EXECUTION_STATE':'Current pointer, attempt, execution, instance, allocation, possession digest and executor OID; original absolute deadlines',
           'REQUIRED_OWNERSHIP_STATE':own,'REQUIRED_EFFECT_STATE':effect,'REQUIRED_RECONCILIATION_STATE':recon,
           'REQUIRED_TIME_STATE':'Runtime database clock, issued<=valid_from<=now<expires; original nested windows; receipt and watchdog freshness; all times finite; exact frozen guard revalidation',
           'REQUIRED_GENERATION_STATE':'Allocation+binding registry revision, current pointer/attempt/execution generation, signer/key/credential/grant revisions, current server incarnation; no stale generation repair',
           'REQUIRED_EXPECTED_RESULT':expected,'REQUIRED_TERMINAL_STATE':terminal,
           'REQUIRED_SOURCE_GUARDS':'Every exact body/constraint/transitive guard in SOURCE-OBLIGATIONS.json; no selected subset; semantic coverage remains separately reviewed',
           'REQUIRED_PERSISTENCE_PROOFS':'Fresh disposable runtime evidence only; design manifest does not confer eligibility'}
        result.append(r)
    return result
def joins():
    pairs=[
      ('identity_slots','service_role_oid','pg_roles','oid'),('identity_slots','service_identity','pg_roles','rolname'),
      ('binding','deployment_id','readiness','deployment_id'),('binding','incarnation_id','readiness','incarnation_id'),
      ('allocation','allocation_id','enrollment_anchor','allocation_id'),('allocation','service_role_oid','identity_slots','service_role_oid'),
      ('allocation','binding_generation','registry','binding_generation'),('binding','binding_id','attempt_pointer','binding_id'),
      ('attempt_pointer','attempt_id','attempt','attempt_id'),('attempt_pointer','execution_generation','attempt','execution_generation'),
      ('attempt','execution_generation','execution','execution_generation'),('execution','execution_id','admission','execution_id'),
      ('execution','service_role_oid','identity_slots','service_role_oid'),('binding','policy_revision','policy','policy_revision'),
      ('binding','policy_hash','policy','policy_hash'),('readiness','policy_hash','policy','policy_hash'),
      ('binding','approval_id','approval','approval_id'),('approval','approval_generation','registry','approval_generation'),
      ('approval','approval_hash','attestation','approval_hash'),('attestation','attestation_generation','registry','attestation_generation'),
      ('attestation','attestation_hash','expected_original_attestation','attestation_hash'),('receipt','attestation_id','accepted_attestation','attestation_id'),
      ('receipt','receipt_generation','registry','receipt_generation'),('receipt','execution_id','execution','execution_id'),
      ('ownership','execution_id','execution','execution_id'),('ownership','ownership_state','execution','ownership_state'),
      ('effect','receipt_id','stage_receipt','receipt_id'),('effect','attempt_id','attempt','attempt_id'),
      ('reconciliation','binding_id','binding','binding_id'),('reconciliation','reconciliation_state','registry','reconciliation_state'),
      ('consumption','organization_id','binding','organization_id'),('source_observation','organization_id','binding','organization_id'),
      ('principal','organization_id','binding','organization_id'),('credential','principal_id','principal','principal_id'),
      ('grant','principal_id','principal','principal_id'),('admission','credential_revision','credential','credential_revision'),
      ('admission','grant_revision','grant','grant_revision'),('consumption','attestation_id','accepted_attestation','attestation_id'),
      ('decision','organization_id','binding','organization_id'),('decision','order_id','binding','order_id')]
    return [{'JOIN_ID':f'J{i:02d}','SOURCE_RELATION':a,'SOURCE_KEY':b,'TARGET_RELATION':c,'TARGET_KEY':d,'REQUIRED_EQUALITY':'Exact typed equality; same organization/fixture context; byte fields exact; no wildcard','NULL_ALLOWED':False,'GENERATION_BOUND':'Exact independently current registry and incarnation; revalidate before acting','REVISION_BOUND':'Exact immutable row revision plus current allocation/promotion registry; no monotonic greater-than substitution','FAILURE_SQLSTATE_OR_DENIAL':'FIXTURE_INELIGIBLE; actual SQL error/result remains frozen, P0017 only where source specifies it','MODEL_RELATION_ONLY':True} for i,(a,b,c,d) in enumerate(pairs,1)]
