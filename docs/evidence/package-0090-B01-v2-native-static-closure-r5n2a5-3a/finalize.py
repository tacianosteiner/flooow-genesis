"""Close this evidence-only provenance gate with an explicit blocked result."""
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];E=O.parent
REPORT=E/'PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3a.md'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(O/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def main():
    base=rd(O/'baseline-freeze.json');search=rd(O/'search-inventory.json');decision=rd(O/'semantic-adjudication.json');review=rd(O/'independent-review.json')
    assert decision['SELECTED_OUTCOME']=='C'
    for k in ['INDEPENDENT_PROVENANCE_REVIEW','INDEPENDENT_SEMANTIC_REVIEW','INDEPENDENT_ACCOUNTING_REVIEW']:assert review[k]=='PASS'
    for p,h in base['source_sha256'].items():assert sha(R/p)==h,p
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    report='''# Package0090 R5N.2A5.3A — canonical semantic provenance resolution

SELECTED_OUTCOME=C. STOP FAIL-CLOSED. No canonical interpretation selected, no contract repair, no witness materialized, no resumption of A5.3.

The missing contract is the case-specific association of (1) the exact inherited object, (2) the attempted authority transition and its source/receiving subject/custody, phase and generation relation, and (3) their compatibility in the original POSTMASTER substitution/restart case. This does not mean general custody, generation or subject-binding semantics are missing.

The earliest case is a generic R5N1 added surface with a generic required predicate. R5N2 preserves the exact identifier but explicitly leaves the attack-specific field mapping pending. A2 semantic reference226 remains incomplete; A3 adjudication226 positively classifies this exact expression as CREDENTIAL_POLICY/use constraint, not an actual credential instance, with no class/alias/declaration candidate and witness gate explicitly deferred. The class3 contract distinguishes public expected read-only endpoint manifest from private context/retained nontransferable descriptor; it separates identity/authentication from ACL authority. The custody contract specializes POSTMASTER to HOST-held expected endpoint authentication and explicitly excludes a fabricated POSTMASTER message key. ABI POSTMASTER_transport binds CENSUS's own signature and independent guard observation. General prohibitions constrain a future typed witness; they do not select this original case's object and transition.

The proposed simplifications were tested, not adopted: public copy is not private material; descriptor is not automatically a secret; reference/possession/custody is not authority; copyability is not inheritance; captured parent/restart dependence does not imply credential propagation. Nonexistence of a POSTMASTER message signing key excludes that interpretation but does not positively establish inapplicability of all operational credential inheritance attacks. Therefore Outcome B is not proven. No unique pair establishes Outcome A.

Object-resolution enumerates the six requested candidate categories plus the no-determined-object resolution marker, without claiming exhaustiveness. Transition-resolution examines all21 requested candidates. The147-cell matrix records no canonically established pair for this original case. Its NOT_APPLICABLE marker cells are not an inapplicability verdict for POSTMASTER/class3 or the original attack.

Repository-wide discovery inventories all8883 tracked and pre-existing untracked files, with relevance checked by pathname and text; all32 required exact terms and semantic line conjunctions are recorded, producing10558 primary discovery passages. The85 legacy-encoded text files are additionally decoded with BOM-aware UTF16/CP1252/Latin1 discovery, with zero additional semantic passages. Exact source selections, source-role distinctions and transitive existing references are retained; zero existing referenced paths fall outside the inventory. Keyword absence is not the decision rule: the decisive positive evidence is that the source case leaves its mapping pending while referenced accepted contracts define distinct non-equivalent objects and do not bind one to this case. Historical generator code is provenance of case enumeration, not architecture authority. Repeated files, archived/rejected evaluator output and prior conclusions do not count as independent semantic authority. Ignored docs/scripts inventory contains zero files.

The denominator is reproduced by exact identifier equality:168 preserved R5N cases +182 R5N1 added cases =350 R5N2 required IDs, 50 surfaces ×7 participants. This does not promote all enumerated requirements into complete typed witnesses. Prior primary350/350 remains withdrawn. Accepted accounting remains0 materialized/evaluated attacks,133 insufficient structured candidates,217 unresolved incomplete candidates; one confirmed target semantic gap and349 unvalidated cases after STOP. No invalid/duplicate removal, no accepted/rejected attack proof. VALID_ATTACKS is NOT_ESTABLISHED, not an inferred zero. The398 incremental evaluator checks remain separate and were read, not rerun as attack evaluations.

Independent read-only review attempted to falsify Outcome C, checked12 specific confusion risks and confirmed provenance/semantics/accounting PASS. These PASS results concern this fail-closed provenance decision, not attack proof or N1 closure.

N1 qualification remains CLOSED, substitution OPEN, decisions11closed/1open of12. V2 static proof FAIL/status BLOCKED. All prior contracts, tracked files and pre-existing untracked evidence are preserved byte-for-byte. No build/runtime/SQL/database/V043/B02/keys/signing/physical identities/privileges/staging/commit/push. No root-cause promotion is performed by this narrow gate.

Next bounded gate is a separately authorized semantic-contract decision for the absent case-specific object/transition/context association. This gate neither proposes its content nor implements a repair. NEXT_EXECUTED=false.

Audit artifacts: baseline-freeze.json; search-inventory.json; semantic-search-passages.json; canonical-source-selections.json; object-resolution.json; transition-resolution.json; object-transition-matrix.json; semantic-adjudication.json; attack-accounting.json; independent-review.json; gate.json; scope-receipt.json; SHA256-MANIFEST.json.
'''
    REPORT.write_text(report,encoding='utf-8')
    gate=dict(BRANCH=base['branch'],BASELINE_HEAD=base['head'],CURRENT_HEAD=git('rev-parse','HEAD'),TRACKED_DIRTY_COUNT=0,STAGED_COUNT=0,UNTRACKED_BEFORE=401,UNAUTHORIZED_UNTRACKED_COUNT=0,TARGET_GAP='POSTMASTER/credential_inheritance',CANONICAL_OBJECT_RESOLUTION='INSUFFICIENT',CANONICAL_AUTHORITY_TRANSITION_RESOLUTION='INSUFFICIENT',CANONICAL_OBJECT_TRANSITION_BINDING='NOT_ESTABLISHED',SELECTED_OUTCOME='C',CANONICAL_OBJECT='NOT_DETERMINED',CANONICAL_AUTHORITY_TRANSITION='NOT_DETERMINED',CANONICAL_PAIR_VALID='NOT_ESTABLISHED',POSTMASTER_CREDENTIAL_INHERITANCE_APPLICABLE='NOT_DETERMINED',INAPPLICABILITY_PROVEN='NO',CANONICAL_CONTRACT_SILENT_OR_INSUFFICIENT='YES',MISSING_SEMANTIC_CONTRACTS=decision['missing'],CANONICAL_ATTACK_DENOMINATOR_PREVIOUS=350,DENOMINATOR_CANONICALLY_REPRODUCIBLE='YES',MATERIALIZED_ATTACKS=0,VALID_ATTACKS='NOT_ESTABLISHED',INVALID_EXPECTATIONS=0,DUPLICATE_OR_DERIVED=0,UNRESOLVED_CANONICAL_GAPS=350,CONFIRMED_TARGET_SEMANTIC_GAP=1,OTHER_UNVALIDATED_AFTER_PRIOR_STOP=349,ATTACK_REJECTED_AS_DESIGNED=0,ATTACK_ACCEPTED_DESIGN_FAILURE=0,EVALUATOR_CHECKS=398,N1_QUALIFICATION_INPUT_RESOLUTION='CLOSED',N1_SUBSTITUTION_STATIC_WITNESSES='OPEN',N1_DECISIONS_REQUIRED=12,N1_DECISIONS_CLOSED=11,N1_DECISIONS_OPEN=1,V2_NATIVE_STATIC_DESIGN_PROOF='FAIL',V2_NATIVE_STATUS='BLOCKED',IMPLEMENTATION_PERFORMED='NO',NATIVE_BUILD_PERFORMED='NO',NATIVE_RUNTIME_EXECUTED='NO',SQL_EXECUTED='NO',DATABASE_CONTACTED='NO',V043_EXECUTED='NO',B02_EXECUTED='NO',GIT_ADD='NO',COMMIT='NO',PUSH='NO',INDEPENDENT_PROVENANCE_REVIEW='PASS',INDEPENDENT_SEMANTIC_REVIEW='PASS',INDEPENDENT_ACCOUNTING_REVIEW='PASS',EVIDENCE_REPORT=REPORT.relative_to(R).as_posix(),SHA256_MANIFEST=(O/'SHA256-MANIFEST.json').relative_to(R).as_posix(),R5N2A5_3A_STATUS='OUTCOME_C_STOP_FAIL_CLOSED',NEXT_EXECUTED=False,NEXT_GATE='SEPARATELY_AUTHORIZED_CASE_SPECIFIC_SEMANTIC_CONTRACT_DECISION; no repair proposed or executed in this gate',REMOTE_NETWORK_VERIFIED='NO',INTEGRITY_FAILURES=0,CLOSED_CONTRACTS_REOPENED=0)
    for n in ['gate.json','scope-receipt.json','SHA256-MANIFEST.json']:
        if not (O/n).exists():put(n,{})
    before=set(base['untracked_before_paths']);current=set(git('ls-files','--others','--exclude-standard').splitlines());new=sorted(current-before)
    unauthorized=[p for p in new if not(p.startswith(O.relative_to(R).as_posix()+'/') or p==REPORT.relative_to(R).as_posix())]
    assert not unauthorized and before<=current
    gate['UNTRACKED_AFTER']=len(current);put('gate.json',gate)
    put('scope-receipt.json',dict(untracked_before=401,untracked_after=len(current),new_paths=new,unauthorized=unauthorized,all_prior_paths_hash_verified=len(base['source_sha256']),tracked_dirty=0,staged=0,prior_review_artifacts_in_baseline='Four late prior A5.3 review files already present at this gate preflight; preserved unchanged',ignored_docs_scripts_files=0))
    put('SHA256-MANIFEST.json',dict(algorithm='SHA256',self_excluded=True,files={p:sha(R/p) for p in new if p!=gate['SHA256_MANIFEST']}))
    print(json.dumps(gate,indent=2))
if __name__=='__main__':main()
