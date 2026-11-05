"""Finalize static intent evidence only after independent adversarial review."""
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];E=O.parent
REPORT=E/'PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3b.md'
def rd(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(O/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def main():
    b=rd('baseline-freeze.json');m=rd('intent-matrix.json');d=rd('intent-adjudication.json');review=rd('independent-review.json')
    for k in ['INDEPENDENT_INTENT_REVIEW','INDEPENDENT_CONSISTENCY_REVIEW','INDEPENDENT_SCOPE_REVIEW']:assert review[k]=='PASS'
    for p,h in b['source_sha256'].items():assert sha(R/p)==h,p
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    assert git('branch','--show-current')==b['branch'] and git('rev-parse','HEAD')==b['head']
    table='\n'.join('| '+x['INTENT_ID']+' | '+x['INTENT_DESCRIPTION']+' | '+x['CANONICAL_SUPPORT']+' |' for x in m['candidates'])
    text='''# Package0090 R5N.2A5.3B — semantic intent reconstruction

SELECTED_OUTCOME=C — multiple legitimate security intents remain. STOP fail closed. This is an intent investigation, not A5.3 witness completion. No object, attempted transition, authority, class, contract or implementation is created. A5.3A Outcome C and all four missing case-specific bindings remain frozen.

## What the requirement currently establishes

The original R5N1 entry is a required negative surface named POSTMASTER/credential_inheritance with a generic catalog/IO/custody/peer predicate shared with theft, transfer and wrong_custodian entries. R5N2 retains the label and explicitly leaves attack-specific field mapping pending. A3 adjudicates that exact label as CREDENTIAL_POLICY/use constraint, not a credential instance, with no class/alias/declaration candidate and witness gate deferred. These sources do not record an exclusive case-specific security purpose.

The approved architecture nevertheless meaningfully constrains possible intentions. It prohibits unapproved operational transfer/duplication/private custody sharing, distinguishes public expected manifests from private contexts/descriptors, prevents credential spelling/possession from conferring authority, and binds eligibility to independently authenticated subject/process/current generation/context and monotonic revocation. Approved bootstrap delivery is a bounded exception; restart depends on full-cohort retirement and requalification. No POSTMASTER native message signing key is invented: CENSUS signs its own observation, independently repeated by the guard.

Strong support for those general principles is not strong proof that any one is the exclusive intent of this generic named case. The matrix therefore separates GENERAL_PROPERTY_SUPPORT from CASE_SPECIFIC_INTENT_ATTRIBUTION. No competing candidate is eliminated merely to make another win.

## Intent hypotheses

CANONICAL_SUPPORT is evidence-bounded support for each hypothesis as assessed here. PARTIAL denotes strong relevant general constraints but missing case-specific attribution. I19 is a strongly supported meta-resolution, not a security-property candidate selected as the winner. I6 has no specific directional attribution; I18 identifies no additional exact named intent. NONE is not positive contradiction or inapplicability.

| Intent | Hypothesis | Support |
|---|---|---|
'''+table+'''

The full machine-readable matrix contains source pointers, property/threat scope, preserved and potentially overreached closed contracts, all authority/custody/generation/restart/substitution/qualification impact fields, minimality, confidence and reasons. Impact NO means describing the existing bounded principle adds no authority/change; it does not authorize a future exclusive semantic contract. Unqualified blanket no-reuse/no-bootstrap readings can conflict with approved current-generation use, terminal receipt reads or pre-enrollment delivery. Those readings are cautioned, not silently adopted or used to invalidate the requirement.

## Materially distinct surviving alternatives

| Alternative | Canonical constraints and architectural consequence | Remaining ambiguity |
|---|---|---|
| I12 — custody independence | Preserve existing nontransfer/nonduplication/private custody boundaries. A custody concern need not change generation; stolen bytes alone still fail independent peer binding. | Does not identify a receiving actor/object or establish that this is the named case's exclusive purpose. |
| I10 — no prior-generation authority continuity after restart | Preserve retirement, UNKNOWN reconciliation, extinction, tombstones, fresh generation/key or endpoint and requalification. Temporal invalidity need not involve custody transfer. | Does not make restart dependence credential inheritance or select the named case's exclusive temporal purpose. |
| I14/I15/I16 — subject/generation/process binding | Keep distinct tuple/currentness dimensions independently authenticated; copying a reference does not replace an enrollment or grant authority. | Binding integrity differs from secrecy/custody and does not select object, propagation direction or attempted use. |

The other partial hypotheses remain source-conditioned possibilities, not an adopted normative conjunction. Neither the presence of all these predicates in qualification nor a broad no-authority-inheritance principle proves that credential_inheritance intentionally protects a minimal inseparable conjunction. Custody and temporal eligibility are logically distinct constraints. The threat matrix leaves every missing case-specific actor, source object/subject, target and attempted transition NOT_CANONICALLY_DETERMINED. It records only conditional preservation of the existing bounded property and fail-closed eligibility, not a materialized attack or observed rejection.

## Outcome adjudication

A is not established: no unique attributed intent or derivation/subordination proof for competitors. B is not established: no provenance proves a minimal inseparable conjunction for this surface. D is not established: no positive incoherence or incompatibility requiring closed-contract reopening; ambiguity is not malformation. E would overstate ignorance: canonical custody/authentication/currentness/lifecycle policies meaningfully constrain several alternatives. C preserves these alternatives without selecting missing semantics.

Architectural consistency A–N is assessed per candidate in architectural-consistency.json. Current properties need no new authority or primitive merely to remain preserved. The minimality and future case-specific consequences of an unchosen contract are not inferred. Parent identity is intrinsic/captured before enrollment, but is not a credential; process, principal, generation and authority remain distinct. Restart dependence and substitution are not credential propagation. Revocation is not deletion. Public metadata is not private authority-bearing material.

## Scope, provenance and frozen accounting

The preceding exhaustive search inventoried8883 files,32 exact terms,10558 semantic passages and85 legacy-encoded text files. Every byte of that corpus was reverified; the20 intervening A5.3A artifacts are also frozen here, for8903 pre-existing files total. Reusing unchanged discovery avoids treating repeated scans as independent authority. This gate reads exact full identity/authority/custody/lifecycle/source/Reader contracts and follows their referenced accepted records through A3, A4, A4.1, A4.1D, A4.1B, A4.2, A5, A5.1, A5.2, A5.3 and A5.3A. ADR/SPEC TEST authority is context, not case-intent selection. Historical generator/implementation code and prior model conclusions are not semantic authority. No keyword-absence-only inference is made.

Frozen denominator350 remains reproducible by exact identifiers (50surfaces ×7participants). One target semantic gap is confirmed;349 records remain unvalidated after prior STOP. Zero attacks are materialized/evaluated here.398 earlier evaluator checks remain distinct. N1 qualification CLOSED/substitution OPEN;12decisions=11closed+1open. V2 static proof FAIL/status BLOCKED. No root-cause closure recomputation is performed. A5.2 Outcome B, S1/S2 NO, parent capture,21pair independence dimensions and21restart dependencies remain unchanged.

Independent review attempts to falsify the outcome and covers all16 specified confusion risks. Its PASS verdicts concern this bounded reconstruction and preserved ambiguity, not N1 closure or attack proof. All pre-existing tracked/untracked bytes are preserved and staging remains empty. No implementation, native build/runtime, SQL/database/shared/production contact, V043/B02/migration, secrets/keys/signatures, physical identities/roles/privileges, staging/commit/push.

## Next authority boundary

NEXT_GATE=EXPLICIT_ARCHITECTURAL_SEMANTIC_DECISION. Choosing an intent would require an explicit technical architectural semantic decision under repository ADR/SPEC governance with separately bounded authorization. It cannot come from model preference, implementation convenience, N1 closure pressure or a CEO technical menu. This gate does not choose, repair, propose the contents of, or create the absent semantic contract. NEXT_EXECUTED=false.
'''
    REPORT.write_text(text,encoding='utf-8')
    counts=m['counts'];g=dict(BRANCH=b['branch'],BASELINE_HEAD=b['head'],CURRENT_HEAD=git('rev-parse','HEAD'),TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,UNTRACKED_BEFORE=421,UNAUTHORIZED_UNTRACKED_COUNT=0,TARGET_GAP='POSTMASTER/credential_inheritance',A5_3A_SELECTED_OUTCOME='C',A5_3A_CANONICAL_OBJECT_RESOLUTION='INSUFFICIENT',A5_3A_CANONICAL_AUTHORITY_TRANSITION_RESOLUTION='INSUFFICIENT',INTENT_CANDIDATES_EVALUATED=19,INTENTS_STRONG_SUPPORT=counts.get('STRONG',0),INTENTS_PARTIAL_SUPPORT=counts.get('PARTIAL',0),INTENTS_CONTRADICTED=counts.get('CONTRADICTED',0),INTENTS_NO_SUPPORT=counts.get('NONE',0),STRONG_SUPPORT_SCOPE='I19_META_RESOLUTION_ONLY_NOT_UNIQUE_SECURITY_INTENT',SELECTED_OUTCOME='C',UNIQUE_INTENT='NOT_ESTABLISHED',COMPOSITE_INTENT='NOT_ESTABLISHED',SURVIVING_AMBIGUOUS_INTENTS=d['surviving_plausible_candidate_ids'],DISTINCT_ALTERNATIVES='I12 custody; I10 temporal restart eligibility; I14/I15/I16 binding integrity',SECURITY_PROPERTY_RECONSTRUCTED='BOUNDED_PLAUSIBLE_ALTERNATIVES_NOT_UNIQUE_CASE_INTENT',ATTACK_CLASS_RECONSTRUCTED='NOT_UNIQUELY_ESTABLISHED',NEW_AUTHORITY_REQUIRED='NO_FOR_THIS_RECONSTRUCTION',CLOSED_CONTRACT_REOPEN_REQUIRED='NO',ARCHITECTURE_CHANGE_REQUIRED='NO',CASE_SPECIFIC_OBJECT_CREATED='NO',CASE_SPECIFIC_TRANSITION_CREATED='NO',OBJECT_TRANSITION_BINDING_CREATED='NO',POSTMASTER_CONTEXT_BINDING_CREATED='NO',CANONICAL_ATTACK_DENOMINATOR=350,DENOMINATOR_CANONICALLY_REPRODUCIBLE='YES',CONFIRMED_TARGET_SEMANTIC_GAP=1,OTHER_UNVALIDATED_AFTER_PRIOR_STOP=349,ATTACKS_MATERIALIZED_THIS_GATE=0,ATTACKS_EVALUATED_THIS_GATE=0,EVALUATOR_CHECKS_PREVIOUS=398,N1_QUALIFICATION_INPUT_RESOLUTION='CLOSED',N1_SUBSTITUTION_STATIC_WITNESSES='OPEN',N1_DECISIONS_REQUIRED=12,N1_DECISIONS_CLOSED=11,N1_DECISIONS_OPEN=1,V2_NATIVE_STATIC_DESIGN_PROOF='FAIL',V2_NATIVE_STATUS='BLOCKED',ROOT_CAUSE_RECOMPUTATION_PERFORMED='NO',IMPLEMENTATION_PERFORMED='NO',NATIVE_BUILD_PERFORMED='NO',NATIVE_RUNTIME_EXECUTED='NO',SQL_EXECUTED='NO',DATABASE_CONTACTED='NO',V043_EXECUTED='NO',B02_EXECUTED='NO',GIT_ADD='NO',COMMIT='NO',PUSH='NO',INDEPENDENT_INTENT_REVIEW=review['INDEPENDENT_INTENT_REVIEW'],INDEPENDENT_CONSISTENCY_REVIEW=review['INDEPENDENT_CONSISTENCY_REVIEW'],INDEPENDENT_SCOPE_REVIEW=review['INDEPENDENT_SCOPE_REVIEW'],R5N2A5_3B_STATUS='OUTCOME_C_MULTIPLE_LEGITIMATE_INTENTS_STOP_FAIL_CLOSED',NEXT_EXECUTED=False,NEXT_GATE='EXPLICIT_ARCHITECTURAL_SEMANTIC_DECISION',EVIDENCE_REPORT=REPORT.relative_to(R).as_posix(),INTENT_MATRIX=(O/'intent-matrix.json').relative_to(R).as_posix(),PROVENANCE_INDEX=(O/'provenance-index.json').relative_to(R).as_posix(),THREAT_INTENT_MATRIX=(O/'threat-intent-matrix.json').relative_to(R).as_posix(),SHA256_MANIFEST=(O/'SHA256-MANIFEST.json').relative_to(R).as_posix(),REMOTE_NETWORK_VERIFIED='NO',INTEGRITY_FAILURES=0,CLOSED_CONTRACTS_REOPENED=0)
    for n in ['gate.json','scope-receipt.json','SHA256-MANIFEST.json']:
        if not (O/n).exists():put(n,{})
    before=set(b['untracked_before_paths']);current=set(git('ls-files','--others','--exclude-standard').splitlines());new=sorted(current-before)
    unauthorized=[p for p in new if not(p.startswith(O.relative_to(R).as_posix()+'/') or p==g['EVIDENCE_REPORT'])]
    assert not unauthorized and before<=current
    g['UNTRACKED_AFTER']=len(current);put('gate.json',g)
    put('scope-receipt.json',dict(untracked_before=421,untracked_after=len(current),new_paths=new,unauthorized_paths=unauthorized,preexisting_files_verified=len(b['source_sha256']),tracked_dirty=0,staged=0))
    put('SHA256-MANIFEST.json',dict(algorithm='SHA256',self_excluded=True,files={p:sha(R/p) for p in new if p!=g['SHA256_MANIFEST']}))
    print(json.dumps(g,indent=2))
if __name__=='__main__':main()
