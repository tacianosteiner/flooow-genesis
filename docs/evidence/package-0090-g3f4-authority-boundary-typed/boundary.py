"""Explicit corrected SQL/external layers, with pending enforcement marked."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
def build(tables):
    old=json.loads((ROOT/'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/AUTHORITY-JOIN-GRAPH.json').read_text())
    # Exact column renames are corrections, not assertions of equivalent authority.
    sql={
      'J01':('decoded_header_slots','slot_oid','pg_catalog.pg_roles','oid'),
      'J02':('decoded_header_slots','slot_name','pg_catalog.pg_roles','rolname'),
      'J03':('public.offline_binding_header','deployment_id','public.offline_readiness','deployment_id'),
      'J04':('public.offline_binding_header','deployment_incarnation_id','public.offline_readiness','incarnation_id'),
      'J08':('public.offline_binding_header','binding_id','public.offline_attempt_pointer','binding_id'),
      'J09':('public.offline_attempt_pointer','current_attempt_id','public.offline_attempt','attempt_id'),
      'J10':('public.offline_attempt_pointer','generation','public.offline_attempt','generation'),
      'J11':('public.offline_attempt','generation','public.offline_execution','generation'),
      'J12':('public.offline_execution','execution_id','public.offline_admission','execution_id'),
      'J13':('public.offline_execution','executor_oid','decoded_header_slots','executor_slot_oid'),
      'J14':('public.offline_binding_header','deadline_policy_version','public.offline_deadline_policy','policy_version'),
      'J15':('public.offline_binding_header','deadline_policy_digest','public.offline_deadline_policy','policy_digest'),
      'J16':('public.offline_readiness','policy_digest','public.offline_deadline_policy','policy_digest'),
      'J24':('public.offline_stage_receipt','execution_id','public.offline_execution','execution_id'),
      'J25':('public.offline_execution','execution_id','BOUND_WRAPPER_ARGUMENT','execution_id'),
      'J26':('public.offline_execution','state','EXPECTED_SQL_LITERAL','OWNED'),
      'J27':('public.offline_stage_receipt','receipt_id','FROZEN_PRODUCER_RECEIPT','receipt_id'),
      'J28':('public.offline_stage_receipt','attempt_id','public.offline_attempt','attempt_id'),
      'J29':('public.offline_reconciliation','binding_id','public.offline_binding_header','binding_id'),
      'J31':('public.s2a_attestation_consumption','organization_id','public.offline_binding_header','organization_id'),
      'J32':('public.integration_mercado_livre_order_source_observation','organization_id','public.offline_binding_header','organization_id'),
      'J33':('public.command_principal','organization_id','public.offline_binding_header','organization_id'),
      'J34':('public.command_credential_revision','principal_id','public.command_principal','principal_id'),
      'J35':('public.command_permission_grant','principal_id','public.command_principal','principal_id'),
      'J36':('public.offline_admission','credential_revision','public.command_credential_revision','revision'),
      'J37':('public.offline_admission','grant_revision','public.command_permission_grant','revision'),
      'J38':('public.s2a_attestation_consumption','accepted_attestation_id','public.s2a_accepted_attestation','accepted_attestation_id'),
      'J39':('public.marketplace_transaction_identity_decision','organization_id','public.offline_binding_header','organization_id'),
      'J40':('public.marketplace_transaction_identity_decision','marketplace_order_id','public.offline_binding_header','marketplace_order_id')}
    external={
      'J05':('PROCESS_IDENTITY_ENFORCED','Replace nonexistent allocation UUID equality with retained OS pidfd anchor identity + boot/start namespace tuple.','atomic process anchor, anchor_equal/fstat, catalog-backed backend identity','quarantine.h observation_entry.inode/pid/request; protocol.h anchor_equal'),
      'J06':('PROTOCOL_ENFORCED','Allocation-to-role binding is protocol/server identity, not an allocation SQL table.','server-derived role/db OIDs and names matched to exact decoded header slots','protocol.h request_fields.role/db/slot and context_matches; receiver catalog probe'),
      'J07':('EXTERNAL_RUNTIME_ENFORCED','Replace binding_generation registry fiction with distinct enrollment_revision/registry_revision; never equate these with SQL pointer.generation.','current promotion phase, anchor and census observation epoch/revision CAS','quarantine.h observation_registered/enrollment_revision/registry_revision'),
      'J18':('EXTERNAL_RUNTIME_ENFORCED','Approval-generation observer registry is external; existing gate lease does not implement independent producer generation.','original approval publication digest, process generation, independent consumer/guard receipt','protocol.h read_gate health_gate.context/header/expires; logical approval_state payload'),
      'J20':('CRYPTOGRAPHICALLY_ENFORCED','Attestation generation surrogate is not a SQL revision. Bind exact original signed input and accepted signer/key/authority revisions separately.','original Ed25519 signature and exact canonical expected input; independent publication/consumption context','offline_internal_matches_original_signed_attestation; offline_expected_signed_attestation; approval_state'),
      'J23':('PROTOCOL_ENFORCED','Receipt generation must be decoded from exact receipt context; no generic registry.receipt_generation column exists.','exact frozen receipt domain/binding/attempt/generation/execution fields plus external completion generation/challenge','offline_stage_receipt generation/attempt/execution; logical completion receipt'),
      'J30':('MODEL_ONLY_INVALID','Reject reconciliation.state equals generic external registry state. SQL reconciliation is administrative evidence; observer completion is a distinct cross-layer witness.','independent recomputation digest/context must bind offline_reconciliation.binding_id/evidence_digest/recorded_at, never rewrite state through a health frame','offline_reconcile read-only snapshot; offline_reconciliation administrative state')}
    crypto={'J19':'Original approval material cannot be reduced to a generic approval_hash=attestation_hash; require exact manifest/signature/context validation.','J21':'Original attestation commitments are exact canonical bytes, algorithm/key fingerprint/signature and commitment_digest, not a free interchangeable attestation_hash.'}
    edges=[];cross=[]
    for original in old:
        jid=original['JOIN_ID'];record={'EDGE_ID':jid,'CURRENT_MODEL':original,'MODEL_CORRECTION_REQUIRED':'YES','SQL_MISMATCH_INCLUDES_EXTERNAL':False}
        if jid in sql:
            a,b,c,d=sql[jid];missing=[f'{r}.{col}' for r,col in [(a,b),(c,d)] if r not in ['decoded_header_slots','BOUND_WRAPPER_ARGUMENT','EXPECTED_SQL_LITERAL','FROZEN_PRODUCER_RECEIPT'] and col not in tables.get(r,{})]
            record.update(classification='SQL_ENFORCED',layer='LAYER_A_SQL_AUTHORITY',actual_binding={'source_relation':a,'source_column':b,'target_relation':c,'target_column':d},SQL_RELATION_EXISTS='YES' if not missing else 'PARTIAL_CATALOG_MAPPING',EXTERNAL_WITNESS_REQUIRED='NO_FOR_THIS_SQL_EDGE',enforcement_verified=False,reason='Candidate corrected actual SQL columns; exact predicate/control-flow matching is still required. Self-relations denote state/receipt existence obligations, never tautological authority.',missing_catalog_columns=missing)
        elif jid in external:
            category,reason,witness,source=external[jid];record.update(classification=category,layer='LAYER_B_EXTERNAL_AUTHORITY' if category!='MODEL_ONLY_INVALID' else 'INVALID_OLD_EDGE_REPLACED_WITH_CROSS_LAYER_EVIDENCE',ACTUAL_ENFORCEMENT_BOUNDARY=source,SQL_RELATION_EXISTS='NO_FOR_OLD_EXTERNAL_RELATION',EXTERNAL_WITNESS_REQUIRED='YES',reason=reason,witness_required=witness,enforcement_verified=False,enforcement_status='CURRENT_PARTIAL_PRIMITIVE_OR_DESIGN_REQUIREMENT_NOT_FULL_RUNTIME_PASS')
            cross.append({'EXTERNAL_EDGE_ID':jid,'PRODUCER':'Trusted bootstrap/enrollment producer' if jid in ['J05','J06','J07'] else 'Approval/attestation/receipt producer or independent reconciliation observer','INDEPENDENT_VERIFIER':'HEALTH_GUARD anchored by HOST_PLATFORM; database evidence re-read independently','BOUND_SQL_OR_RUNTIME_FIELD':{'SQL':'offline_binding_header.binding_id/deployment_id/deployment_incarnation_id/identity_slots/plan_fingerprint/deadline_policy_digest; exact attempt/execution context where applicable','RUNTIME':'request_fields binding/deployment/incarnation/epoch/slot/role/db/fingerprint/policy, pidfd anchor and current enrollment_revision/registry_revision','SPECIAL':'offline_reconciliation binding_id/evidence_digest/recorded_at; administrative state not observer-writable' if jid=='J30' else witness},'GENERATION_BOUND':'Distinct SQL pointer generation and external process/enrollment generations; exact current tuple, no numeric equivalence','INCARNATION_BOUND':'Exact server/current header incarnation','DEPLOYMENT_BOUND':'Exact current header/runtime deployment','ANTI_REPLAY_BOUND':'Current allocation/anchor and one-use independent challenge, strict sequence, original emission, current registry CAS; original signed/receipt bytes cannot be substituted','FAIL_CLOSED_ACTION':'Deny promotion/ACCEPT; retain quarantine and ownership; stale snapshots cannot erase new enrollment or create eligibility','status':'DESIGN_BINDING_DEFINED_RUNTIME_NOT_IMPLEMENTED'})
        elif jid in crypto:
            record.update(classification='CRYPTOGRAPHICALLY_ENFORCED',layer='LAYER_B_EXTERNAL_AUTHORITY',SQL_RELATION_EXISTS='YES_ORIGINAL_INPUT_STORAGE_NOT_GENERIC_APPROVAL_TABLE',EXTERNAL_WITNESS_REQUIRED='YES',reason=crypto[jid],enforcement_verified=False)
            cross.append({'EXTERNAL_EDGE_ID':jid,'PRODUCER':'Test-only original attestation signer/publication producer','INDEPENDENT_VERIFIER':'Frozen exact-input crypto verifier plus independently anchored approval consumer/guard','BOUND_SQL_OR_RUNTIME_FIELD':'offline_expected_signed_attestation binding_id/manifest_digest/algorithm_id/signer_key_id/signer_key_fingerprint/signature_bytes/canonical_expected_attestation/commitment_digest; accepted signer/key/authority revisions','GENERATION_BOUND':'Original publication/process generation plus separately exact SQL signer/key revisions','INCARNATION_BOUND':'Exact signed header incarnation','DEPLOYMENT_BOUND':'Exact signed header deployment','ANTI_REPLAY_BOUND':'Original bytes, current exact context, independent challenge/receipt; no re-sign or restore eligibility','FAIL_CLOSED_ACTION':'Deny on any mismatch/missing original evidence; never infer identity/authority from hash equality alone','status':'DESIGN_BINDING_DEFINED_RUNTIME_WITNESS_PENDING'})
        else:record.update(classification='MODEL_ONLY_INVALID',layer='INVALID_OLD_EDGE',SQL_RELATION_EXISTS='NO_LITERAL_GENERIC_JOIN',EXTERNAL_WITNESS_REQUIRED='YES',reason='Generic approval_id table join (J17) or untyped receipt-to-attestation equality (J22) is not actual SQL enforcement. Replace with exact original approval/signature context or typed frozen receipt decoder predicates; no invented relation or equivalent matching.',enforcement_verified=False)
        edges.append(record)
    return {'edges':edges,'seven_mismatch_reviews':[e for e in edges if e['EDGE_ID'] in external],'cross_layer_bindings':cross,'sql_layer':[e for e in edges if e['layer']=='LAYER_A_SQL_AUTHORITY'],'external_layer':[e for e in edges if e['layer']=='LAYER_B_EXTERNAL_AUTHORITY'],'invalid_model_edges':[e for e in edges if e['classification']=='MODEL_ONLY_INVALID'],'UNCLASSIFIED_AUTHORITY_EDGE_N':0,'EXTERNAL_AUTHORITY_BINDING_COMPLETE':'YES_DESIGN_DECLARED_NOT_RUNTIME_QUALIFIED','authority_graph_complete':False}
