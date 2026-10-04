"""Fail-closed original-input consumer audit at the next mutable boundary.

This is an authority/information-flow witness, not an exploit/runtime certificate.
"""
import hashlib
import json
import package_0090_source_gate as gate

def audit():
    source=(gate.ROOT/gate.V043).read_text(encoding='utf-8-sig')
    spec=(gate.ROOT/gate.SPEC).read_text(encoding='utf-8-sig')
    statements,_=gate.parse(source)
    grants=gate.actual_column_grants(statements)
    expected_reads=sorted((o,c) for o,r,c,p in grants if r=='public.offline_expected_signed_attestation' and p=='select')
    if len(expected_reads)!=8 or any(o!=gate.OWNERS['A'] for o,c in expected_reads):
        raise ValueError('Expected-input authority changed; reevaluate mutable boundary')
    body=source.split('AS $offline_s02$',1)[1].split('$offline_s02$;',1)[0]
    needed=["current_setting('transaction_isolation')<>'repeatable read'","current_setting('transaction_read_only')<>'on'",'slot_number=4 AND slot_name <> SESSION_USER']
    if not all(value in body for value in needed):raise ValueError('R transaction/session guard changed')
    frozen_path=next((gate.ROOT/gate.MIGRATIONS).glob('V041__*.sql'))
    frozen=frozen_path.read_text(encoding='utf-8-sig')
    if 'offline_expected_signed_attestation' in frozen:raise ValueError('Frozen dependency acquired original-input authority')
    original=json.loads((gate.ROOT/'docs/evidence/PACKAGE-0090-S02-ORIGINAL-INPUT-GOLDENS.json').read_text())
    a=original['originals']['A'];b=original['originals']['B']
    if a['binding_id']!=b['binding_id'] or a['manifest_digest']!=b['manifest_digest']:
        raise ValueError('Witness is not same public scope')
    if not all(a[k]!=b[k] for k in ('signer_key_id','signer_key_fingerprint','signature_bytes','commitment_digest')):
        raise ValueError('Witness failed to distinguish original inputs')
    isolated=json.loads((gate.ROOT/'docs/evidence/PACKAGE-0090-S02-ISOLATED-PREDICATE-REVIEW.json').read_text())
    if isolated['status']!='PASS' or isolated['ab_matrix']!={'expected_A_stored_A':True,'expected_A_stored_B':False,'expected_B_stored_A':False,'expected_B_stored_B':True}:
        raise ValueError('Real SQL/native witness missing')
    from build_package_0090_original_match_source import NAME, TYPES, GRANTS
    from package_0090_original_match_source import check
    fn=next(s['CreateFunctionStmt'] for s in statements if s.get('CreateFunctionStmt',{}).get('funcname')==[{'String':{'sval':'public'}},{'String':{'sval':NAME}}])
    check(fn,source)
    helper_review=json.loads((gate.ROOT/'docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-MATCH-REVIEW.json').read_text())
    if helper_review['status']!='PASS_ISOLATED_HELPER':raise ValueError('Helper isolated evidence missing')
    return dict(gate='G3F.3B_MUTATION_ORIGINAL_SIGNED_INPUT_CONSUMER_AUTHORITY',
        status='CLOSED_APPROVED_PRIVATE_V_PREDICATE',unresolved_authority_blocker_count=0,
        approved_operational_expected_reads=expected_reads,physical_grant_count=len(grants),
        v_i_e_expected_reads=[],s02_available_to_mutable_guard=False,
        native_validity_cannot_identify_registered_original=True,
        private_match_helper=NAME,private_match_execute=sorted(GRANTS),helper_review=helper_review['status'],
        original_ab_matrix=helper_review['matrix'],implemented_s05_stub=False,
        authority_widened=False,approved_private_comparison_added=True,
        v043_executed=False,protected_database_connection=False,
        next_gate='S05_S06_COMPLETE_IMPLEMENTATION',
        limitations=['Helper isolated proof is separate from complete mutation wrapper runtime closure.'])

if __name__=='__main__':
    report=audit();(gate.ROOT/'docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
