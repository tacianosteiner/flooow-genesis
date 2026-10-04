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
    return dict(gate='G3F.3B_MUTATION_ORIGINAL_SIGNED_INPUT_CONSUMER_AUTHORITY',
        status='HOLD_NO_APPROVED_MUTABLE_ORIGINAL_INPUT_PREDICATE',unresolved_authority_blocker_count=1,
        boundary='S05/S06 before treating a caller signed envelope as the registered original input',
        physical_grant_count=len(grants),expected_relation='public.offline_expected_signed_attestation',
        approved_operational_expected_reads=expected_reads,
        v_i_e_expected_reads=[],s02_available_to_mutable_guard=False,
        s02_restrictions=['AUDITOR_SESSION_USER','REPEATABLE_READ','READ_ONLY'],
        mutable_restrictions=['VERIFIER_ISSUER_EXECUTOR_SESSION_USER','READ_COMMITTED','READ_WRITE'],
        witness=isolated['ab_matrix'],same_binding_and_manifest=True,same_plan=isolated['frozen_witness']['PLAN_EQUAL']=='true',
        native_validity_cannot_identify_registered_original=True,
        rationale='Cryptographically valid B cannot be promoted to the independently registered original A. Only S02 may read/compare the original tuple. Its R guard cannot be invoked as an authorization oracle from mutable V/I/E transactions. Frozen V041/V042 lack this new commitment. No approved mutable predicate bridges the gap; caller values or stored accepted rows cannot supply their own original expectation.',
        recommended_bounded_handoff={
            'owner':'flooow_offline_control_owner',
            'capability':'One private original-input equality predicate for V/S05-S06 only',
            'proposed_signature':'public.offline_internal_matches_original_signed_attestation(uuid,bytea,uuid,text,text,text,uuid,text,bytea) RETURNS boolean',
            'properties':'STABLE SECURITY DEFINER CALLED ON NULL INPUT; fixed search_path=pg_catalog,pg_temp; no defaults/variadic',
            'inputs':'authenticated binding tuple plus manifest_digest,algorithm_id,signer_key_id,signer_key_fingerprint,signature_bytes',
            'output':'boolean only; no raw original values or commitment returned',
            'guards':'Independent exact VERIFIER session OID/name/binding authentication; no AUDITOR R bypass; exact canonical/digest/header/tuple checks',
            'acl':'ADMIN implicit control reads; exact non-grantable EXECUTE to V only; PUBLIC/service direct access none; no V table reads',
            'effect':'V validates the independently registered original before frozen lookup/persistence; I/E rely only on the verified bound stage lineage',
            'requires':'Explicit narrow ADMIN function ownership/EXECUTE/consumer contract amendment; not self-authorized by existing S02_ONLY reads'},
        frozen_v041_sha256=hashlib.sha256(frozen.encode('utf-8')).hexdigest(),
        implemented_s05_stub=False,authority_widened=False,v043_executed=False,protected_database_connection=False,
        limitations=['Information-flow/authority boundary proof, not a claim that an unimplemented mutable wrapper was exploited.'])

if __name__=='__main__':
    report=audit();(gate.ROOT/'docs/evidence/PACKAGE-0090-MUTATION-ORIGINAL-INPUT-AUTHORITY.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
