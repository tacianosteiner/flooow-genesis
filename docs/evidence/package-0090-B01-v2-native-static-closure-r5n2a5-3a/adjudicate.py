"""Evidence-only semantic adjudication; no attack implementation or execution."""
import hashlib,json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];E=O.parent
P='package-0090-B01-v2-native-static-closure-'
REPORT=E/'PACKAGE-0090-B01-v2-native-static-closure-r5n2a5-3a.md'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(O/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=R).decode().strip()
def main():
    base=rd(O/'baseline-freeze.json')
    for p,h in base['source_sha256'].items():assert sha(R/p)==h,p
    assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
    sources=[]
    def source(gate,name,pointer,role):
        path=E/(P+gate)/name;v=rd(path)
        for part in pointer.strip('/').split('/') if pointer else []:v=v[int(part)] if isinstance(v,list) else v[part]
        ref=dict(id='S'+str(len(sources)+1),path=path.relative_to(R).as_posix(),sha256=sha(path),pointer=pointer,exact_fact=v,authority_role=role)
        sources.append(ref);return ref['id']
    n=rd(E/(P+'r5n2')/'substitution-witnesses.json')['cases'];idx=next(i for i,c in enumerate(n) if c['ATTACK_ID']=='POSTMASTER/credential_inheritance')
    s_case=source('r5n2','substitution-witnesses.json','/cases/'+str(idx),'Frozen attack identifier; explicitly incomplete witness, not proof of specific object/transition')
    m=rd(E/(P+'r5n1')/'substitution-matrix.json');mi=next(i for i,c in enumerate(m['new_cases']) if c['id']=='POSTMASTER/credential_inheritance')
    s_origin=source('r5n1','substitution-matrix.json','/new_cases/'+str(mi),'Original added required case; generic predicate, not enforcement or typed inheritance proof')
    source('r5n2a2','semantic-credential-ledger.json','/semantic_references/226','Historical unresolved reference; no credential class identified')
    source('r5n2a3','referent-symbol-table.json','/adjudications/226','Accepted referent adjudication explicitly classifies exact case label as policy/use constraint, not actual credential instance; witness gate deferred, no class or alias assigned')
    s_cust=source('r5n1','credential-custody.json','/credentials/0','Accepted general custody constraints, specialized POSTMASTER endpoint manifest, no POSTMASTER message key; generic delivery fields cannot override specialization')
    s_class=source('r5n2a3','credential-class-manifest.json','/classes/2','Accepted class3 semantics: public expected manifest vs private context/descriptor, subject and authority distinct')
    s_part=source('r5n','native-participants.json','/participants/0','Accepted subject identity/process/currentness boundaries and independently observed endpoint')
    s_codec=source('r5n','native-identity-codec.json','/schemas/credential_identity','Exact credential identity tuple is not credential material or independent grant')
    s_purpose=source('r5n','native-identity-codec.json','/credential_purpose_enum','Class/purpose3 server endpoint distinct from class1 transport')
    s_abi=source('r5n','native-message-abi.json','/sender_vs_subject','Subject distinct from actual frame emitter')
    source('r5n','native-message-abi.json','/POSTMASTER_transport','CENSUS signs its own observation, independently repeated by guard; no POSTMASTER sender key')
    s_restart=source('r5n2a5-2','replacement-dependency-graph.json','','Accepted restart dependence is not an inheritance attack object/transition')
    s_gap=source('r5n2a5-3','canonical-gap.json','','Prior diagnostic conclusion only; not independent authority for current outcome')
    # Direct text authorities and original construction are read, never executed.
    for rel,start,end,role in [('docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md',503,540,'TEST-only authority envelope, not typed inheritance witness'),('docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md',2580,2625,'TEST-only qualification envelope; no target case object/transition binding'),('docs/evidence/'+P+'r5n1/derive.py',258,280,'Historical evidence generator: 26 extra attack names crossed with7slots; code explains provenance, never supplies missing canonical semantics')]:
        path=R/rel;lines=path.read_text(encoding='utf-8-sig').splitlines();sources.append(dict(id='S'+str(len(sources)+1),path=rel,sha256=sha(path),line_start=start,line_end=end,exact_fact='\n'.join(lines[start-1:end]),authority_role=role))
    put('canonical-source-selections.json',dict(sources=sources,independence_rule='Repeated copies, archives and prior conclusions are not independent corroboration. Source count means distinct selected files, not canonical votes. No implementation detail creates semantics.'))
    objdefs=[
      ('PUBLIC_MANIFEST_COPY','PARTIAL',[s_class,s_cust,s_part],'Public expected read-only endpoint manifest exists; copying alone does not confer credential authority. No original attack binding chooses this copy.'),
      ('PRIVATE_CREDENTIAL_DESCRIPTOR','PARTIAL',[s_class,s_cust],'Protected private context/retained nontransferable descriptor and pre-enrollment inventory exist. No case-specific descriptor, source, recipient, phase or attempted use is fixed.'),
      ('SECRET_CREDENTIAL_MATERIAL','PARTIAL',[s_class,s_cust,s_part],'Private material has generic custody constraints. POSTMASTER message signing key is explicitly excluded; observer private keys belong to observers. No secret material is assigned to this inheritance case.'),
      ('CREDENTIAL_IDENTITY_REFERENCE','PARTIAL',[s_codec,s_purpose,s_class],'Purpose3 credential identity tuple and public references exist. Identity reference does not itself carry authority; no case binding selects one.'),
      ('AUTHORITY_BEARING_CREDENTIAL_OBJECT','PARTIAL',[s_class,s_part],'Class3 authenticates exact expected server endpoint under independently verified current bindings; spelling/possession/public digest is not authority. Exact inherited operational object remains unspecified.'),
      ('ANOTHER_EXACTLY_DEFINED_CANONICAL_OBJECT','NO',[s_case,s_origin,s_part],'Complete case lineage and broader source search identify no uniquely bound additional object. Candidate list is not assumed exhaustive.'),
      ('NO_CANONICALLY_DETERMINED_OBJECT','YES',[s_case,s_origin,s_class,s_cust],'Resolution is insufficient: original case is a generic required surface with exact field mapping pending; later general contracts distinguish possible objects without binding this case.')]
    objects=[dict(OBJECT_CANDIDATE=name,CANONICAL_SUPPORT=support,CANONICAL_SOURCE_COUNT=len(refs),EXACT_SOURCE_REFERENCES=refs,SEMANTIC_REASON=reason,CONTRADICTIONS=['POSTMASTER message signing key interpretation contradicts specialized endpoint/observer route'] if name=='SECRET_CREDENTIAL_MATERIAL' else [],CONFIDENCE='Evidence-bounded finding about unresolved case binding, not probability or authority',support_scope='Support for candidate semantics/existence; PARTIAL never means selected attack object') for name,support,refs,reason in objdefs]
    put('object-resolution.json',dict(candidates=objects,selected_object=None,unique_object_established=False))
    names=['custody transfer','custody duplication','authority delegation','authority transfer','authority inheritance','authority reuse','credential reuse','stale credential reuse','cross-generation reuse','cross-participant reuse','parent-to-child inheritance','child-to-parent inheritance','restart reuse','substitution reuse','impersonation','subject-binding bypass','generation-binding bypass','revocation bypass','qualification bypass','no authority transition at all','another explicitly canonical transition']
    transitions=[]
    for name in names:
        refs=[s_case,s_origin,s_class,s_cust]
        reason='General class3 constraints restrict transfer/duplication/operational inheritance and bind exact subject/current generation; the original case does not specify this attempted transition.'
        if name in ['parent-to-child inheritance','child-to-parent inheritance','restart reuse','cross-generation reuse']:refs+=[s_part,s_restart];reason+=' Captured parent identity and full-cohort restart dependence do not establish credential propagation or direction.'
        if name=='no authority transition at all':reason='Public read-only manifest access need not transfer authority, but no source selects that object/use for this negative case.'
        if name=='another explicitly canonical transition':reason='No unique additional transition was found in complete case lineage and referenced contracts; alternatives are not assumed exhaustive.'
        transitions.append(dict(TRANSITION_CANDIDATE=name,CANONICAL_SUPPORT='NO' if name=='another explicitly canonical transition' else 'PARTIAL',SOURCE_COUNT=len(refs),EXACT_SOURCE_REFERENCES=refs,PRECONDITIONS='General current context/enrollment, exact subject/server/peer, approved bootstrap phase; actual attack preconditions unspecified',SOURCE_AUTHORITY='NOT_DETERMINED_FOR_CASE; HOST provisions, observer keys remain separate',TARGET_AUTHORITY='NOT_DETERMINED_FOR_CASE; no authority from copy/possession alone',SOURCE_SUBJECT='NOT_DETERMINED_FOR_CASE',TARGET_SUBJECT='POSTMASTER named target; alleged receiving subject is not specified',GENERATION_RELATION='Currentness/retirement rules known; exact source/target generation relation not selected for case',CUSTODY_EFFECT='NOT_DETERMINED_FOR_CASE; public expected reference and private custody not equivalent',REVOCATION_EFFECT='General tombstone/currentness restrictions remain; exact attempted bypass unspecified',QUALIFICATION_EFFECT='Missing/ambiguous facts deny qualification; denial of missing proof is not evaluated attack rejection',SEMANTIC_REASON=reason,CONTRADICTIONS=[]))
    put('transition-resolution.json',dict(candidates=transitions,selected_transition=None,unique_transition_established=False))
    matrix=[]
    for obj in objects:
        for transition in transitions:
            absent=obj['OBJECT_CANDIDATE']=='NO_CANONICALLY_DETERMINED_OBJECT'
            matrix.append(dict(object_candidate=obj['OBJECT_CANDIDATE'],transition_candidate=transition['TRANSITION_CANDIDATE'],classification='NOT_APPLICABLE' if absent else 'INSUFFICIENT_PROVENANCE',reason='Resolution marker is not an object and cannot form an attack pair' if absent else 'General existence/prohibition is not a source binding this exact object and transition to the original POSTMASTER case. No pair promoted from independent candidate plausibility.',evidence_refs=sorted(set(obj['EXACT_SOURCE_REFERENCES']+transition['EXACT_SOURCE_REFERENCES'])),scope='Canonical establishment of attempted attack pair, not whether a prohibited operation would be permitted'))
    put('object-transition-matrix.json',dict(objects=len(objects),transitions=len(transitions),cells=matrix,unique_pair_established=False,canonically_valid_pairs=0,not_inapplicability_proof=True))
    old=rd(E/(P+'r5n')/'native-substitution-matrix.json')['cases'];original=m['preserved_cases']+m['new_cases']
    ids=lambda items,key:{x[key] for x in items}
    assert len(old)==168 and len(m['new_cases'])==182 and len(original)==350
    assert ids(old,'id')==ids(m['preserved_cases'],'id') and ids(original,'id')==ids(n,'ATTACK_ID') and len(ids(n,'ATTACK_ID'))==350
    assert len({x['SUBSTITUTED_COMPONENT'] for x in n})==50 and sum(x['STATIC_WITNESS_COMPLETE'] for x in n)==133
    prior=rd(E/(P+'r5n2a5-3')/'attack-evaluation-ledger.json');assert len(prior['cases'])==350 and all(not x['evaluation_executed'] for x in prior['cases'])
    checks=rd(E/(P+'r5n2a5-3')/'correction-check-results.json');assert checks['total']==398
    put('attack-accounting.json',dict(CANONICAL_ATTACK_DENOMINATOR_PREVIOUS=350,DENOMINATOR_CANONICALLY_REPRODUCIBLE='YES',lineage='R5N168 required cases + R5N1 182 added required cases = R5N2 350 exact retained identifiers; 50 surfaces ×7slots; no claim350 fully typed canonical witnesses',ids=sorted(ids(n,'ATTACK_ID')),structured_candidates=133,incomplete_candidates=217,MATERIALIZED_ATTACKS=0,VALID_ATTACKS='NOT_ESTABLISHED',INVALID_EXPECTATIONS=0,DUPLICATE_OR_DERIVED=0,UNRESOLVED_CANONICAL_GAPS=350,confirmed_target_semantic_gap=1,other_unvalidated_after_prior_STOP=349,ATTACK_REJECTED_AS_DESIGNED=0,ATTACK_ACCEPTED_DESIGN_FAILURE=0,EVALUATOR_CHECKS=398,scope='Accepted proof accounting, not discarded provisional calculations. No attack executed by this gate; frozen denominator retained.'))
    put('semantic-adjudication.json',dict(SELECTED_OUTCOME='C',CANONICAL_CONTRACT_SILENT_OR_INSUFFICIENT='YES',missing=['MISSING_CASE_SPECIFIC_OBJECT_SEMANTICS','MISSING_CASE_SPECIFIC_TRANSITION_SEMANTICS','MISSING_OBJECT_TRANSITION_BINDING','MISSING_POSTMASTER_CONTEXT_BINDING'],general_contracts_not_missing=['Purpose3 endpoint authentication','Public reference vs private custody distinction','No POSTMASTER native message signing key','Approved pre-enrollment delivery vs prohibited operational inheritance','Current generation/context/subject/revocation/qualification constraints','Retained parent identity and full-cohort restart topology'],reason='Original label+generic predicate never bind exact inherited object, source/receiving subject and custody, lifecycle phase, generation relation or attempted authority use. Later independent identity/custody/restart contracts constrain possible witnesses but do not uniquely choose their conjunction.',rejected_outcomes=dict(A='No unique provenance-bound object/transition/pair',B='No positive evidence that all operational inheritance attacks are inapplicable to POSTMASTER; nonexistence of POST signing key only excludes that interpretation'),no_witness_materialized=True,no_contract_repair=True,STOP_FAIL_CLOSED=True))
    print('PRIMARY_OUTCOME=C; 147 matrix cells; 350 IDs reproduced; no witness materialized')
if __name__=='__main__':main()
