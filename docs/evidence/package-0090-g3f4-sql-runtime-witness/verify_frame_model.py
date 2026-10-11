"""Independent pure model verifier; never validates an actual process/socket/receipt."""
import json,hashlib
def canonical(r):return json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def verify(frame,payload,external,ledger,now,test_max_age):
    completion={'operation_class','operation_id','target_anchor_identity','input_revision','completed_sequence','result_digest','durable_result_reference','independent_observation_reference'}
    payloads={'enrollment':{'binding_id','slot','role_oid','db_oid','role_name','db_name','postmaster_start','backend_start','context_fingerprint','policy_hash'},'identity_proof':{'boot_start','target_start','namespace_digest','pidfd_anchor_digest'},'generation_proof':{'slot','generation','ledger_revision','allocation_id'},'heartbeat':{'health_class'},'progress':completion,'completed_work_witness':completion,'approval_state':completion|{'approval_generation','approval_hash'},'enforcement_state':completion|{'target_outcome'},'quarantine':{'ledger_revision','generation','reason','current_registration_digest'},'drain':{'target_set_digest','ownership_digest','drain_state','release_authorized'},'recovery_observation':{'census_observation_epoch','registry_revision','postmaster_generation','receiver_generation','supervisor_generation','anchor_digest','enrollment_generation','new_eligibility'}}
    if frame.get('frame_type') not in payloads or set(payload)!=payloads[frame['frame_type']]:return False
    numeric={'slot','role_oid','db_oid','postmaster_start','backend_start','boot_start','target_start','generation','ledger_revision','input_revision','completed_sequence','approval_generation','census_observation_epoch','registry_revision','postmaster_generation','receiver_generation','supervisor_generation','enrollment_generation'}
    for key,value in payload.items():
        if key in numeric:
            if type(value) is not int or not 0<value<2**64:return False
        elif key in ['release_authorized','new_eligibility']:
            if value is not False:return False
        elif not isinstance(value,str) or not value:return False
    if frame['frame_type']=='heartbeat' and payload['health_class']!='LIVENESS_ONLY':return False
    if frame['frame_type']=='enforcement_state' and payload['target_outcome'] not in ['EXIT_OBSERVED','CANCEL_OBSERVED']:return False
    required={'frame_identity','frame_type','frame_version','participant_identity','participant_generation','deployment_id','incarnation_id','boot_epoch','sequence','emitted_boottime_us','observation_epoch','registry_revision','payload_digest','challenge','witness_type','witness_generation','witness_sequence','independent_verifier_identity','verification_result'}
    if set(frame)!=required or set(external)!={'frame_type','participant_identity','participant_generation','deployment_id','incarnation_id','boot_epoch','observation_epoch','registry_revision','challenge','independent_verifier_identity','corroborated_payload_digest','corroborated_completion_sequence','observer_observed_boottime_us','participant_restart_revision'}:return False
    if frame['frame_version']!='DESIGN_LOGICAL_V2_NOT_NATIVE_WIRE':return False
    for k in ['participant_generation','sequence','emitted_boottime_us','observation_epoch','registry_revision','witness_generation','witness_sequence']:
        if type(frame[k]) is not int or not 0<=frame[k]<2**64:return False
    for k in ['frame_type','participant_identity','participant_generation','deployment_id','incarnation_id','boot_epoch','observation_epoch','registry_revision','challenge','independent_verifier_identity']:
        if frame[k]!=external[k]:return False
    if external['independent_verifier_identity']==frame['participant_identity']:return False
    stamp=frame['emitted_boottime_us']
    if not stamp<=external['observer_observed_boottime_us']<=now or now-stamp>test_max_age:return False
    if ledger['restart_revision']!=external['participant_restart_revision'] or frame['sequence']!=ledger['last_sequence']+1 or frame['challenge'] in ledger['consumed_challenges']:return False
    digest=hashlib.sha256(canonical(payload)).hexdigest()
    if frame['payload_digest']!=digest or external['corroborated_payload_digest']!=digest:return False
    if frame['frame_type'] in ['progress','completed_work_witness','enforcement_state','approval_state']:
        if frame['witness_type']!='GENERATION_BOUND_COMPLETION_RECEIPT_WITH_EXTERNAL_CORROBORATION' or frame['witness_generation']!=frame['participant_generation'] or frame['witness_sequence']!=ledger['last_completed_sequence']+1 or external['corroborated_completion_sequence']!=frame['witness_sequence']:return False
        if payload['completed_sequence']!=frame['witness_sequence'] or payload['input_revision']!=frame['registry_revision']:return False
    else:
        if frame['witness_type']!='NO_COMPLETION_CLAIM' or frame['witness_generation']!=0 or frame['witness_sequence']!=0:return False
    # Independent observations are a separate model input. A producer's claimed
    # verification_result is ignored as authority; actual external acquisition is
    # a future native implementation requirement, not implemented by this function.
    ledger['last_sequence']=frame['sequence'];ledger['consumed_challenges'].append(frame['challenge'])
    if frame['frame_type'] in ['progress','completed_work_witness','enforcement_state','approval_state']:ledger['last_completed_sequence']=frame['witness_sequence']
    return True
