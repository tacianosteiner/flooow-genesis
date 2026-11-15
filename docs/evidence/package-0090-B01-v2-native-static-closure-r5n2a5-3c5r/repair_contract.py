"""Representation-only gate classifier. Not authentication, admission or witness execution."""
FIELDS=('ARTIFACT_REQUIREMENT_ESTABLISHED','ARTIFACT_AUTHORITY_ESTABLISHED','ARTIFACT_AUTHENTICATION_CRITERIA_ESTABLISHED','ARTIFACT_ADMISSION_CRITERIA_ESTABLISHED','ARTIFACT_EXISTS','ARTIFACT_AUTHENTICATED','ARTIFACT_ADMITTED')
ABSENT='ABSENT_NOT_ESTABLISHED_UNDER_EXISTING_AUTHORITY'
def classify(state,facts):
    if set(state)!=set(FIELDS) or any(v not in ('YES','NO','NOT_ESTABLISHED') for v in state.values()):return None
    # Positive evidence facts are inputs from independent authority, never inferred
    # from existence/packaging/hash or from this function's return value.
    if facts.get('frozen_authority_contradiction_proved') is True:return 'CONTRADICTED'
    if facts.get('new_normative_authority_required_proved') is True:return 'NEW_AUTHORITY_REQUIRED'
    if facts.get('inherently_observational_runtime_required_proved') is True:return 'RUNTIME_REQUIRED'
    if facts.get('requirement_underspecified_proved') is True:return 'REQUIREMENT_UNDERSPECIFIED'
    if all(state[k]=='YES' for k in FIELDS[:4]):
        if state['ARTIFACT_EXISTS']=='NO' and state['ARTIFACT_AUTHENTICATED']!='YES' and state['ARTIFACT_ADMITTED']!='YES':return ABSENT
        if state['ARTIFACT_EXISTS']=='YES' and state['ARTIFACT_AUTHENTICATED']=='YES' and facts.get('independent_authentication_proved') is True:
            if facts.get('origin')=='PRE_EXISTING':return 'EXISTING_AUTHENTICATED_ARTIFACT_RECOVERED'
            if facts.get('origin')=='DETERMINISTIC_ASSEMBLY' and facts.get('all_assembly_inputs_established') is True:return 'DETERMINISTIC_AUTHENTICATED_ARTIFACT_ASSEMBLED'
    return None
def closure_eligible(state,facts):
    disqualifiers=['frozen_authority_contradiction_proved','new_normative_authority_required_proved','inherently_observational_runtime_required_proved','requirement_underspecified_proved']
    return not any(facts.get(k) is True for k in disqualifiers) and all(state[k]=='YES' for k in FIELDS) and facts.get('independent_authentication_proved') is True and facts.get('independent_admission_proved') is True
def six_state_tests():
    base={k:'YES' for k in FIELDS[:4]};absent={**base,'ARTIFACT_EXISTS':'NO','ARTIFACT_AUTHENTICATED':'NOT_ESTABLISHED','ARTIFACT_ADMITTED':'NOT_ESTABLISHED'}
    cases=[
      ('1_EXISTING_AUTHENTICATED_ADMITTED',{k:'YES' for k in FIELDS},dict(origin='PRE_EXISTING',independent_authentication_proved=True,independent_admission_proved=True),'EXISTING_AUTHENTICATED_ARTIFACT_RECOVERED'),
      ('2_ABSENT_EXISTING_AUTHORITY_CRITERIA',absent,{},ABSENT),
      ('3_GENUINELY_NEW_AUTHORITY',{**absent,'ARTIFACT_AUTHORITY_ESTABLISHED':'NO'},dict(new_normative_authority_required_proved=True),'NEW_AUTHORITY_REQUIRED'),
      ('4_POSITIVE_RUNTIME_NECESSITY',absent,dict(inherently_observational_runtime_required_proved=True),'RUNTIME_REQUIRED'),
      ('5_REQUIREMENT_UNDERSPECIFIED',{**absent,'ARTIFACT_REQUIREMENT_ESTABLISHED':'NO'},dict(requirement_underspecified_proved=True),'REQUIREMENT_UNDERSPECIFIED'),
      ('6_CONTRADICTS_FROZEN_AUTHORITY',absent,dict(frozen_authority_contradiction_proved=True),'CONTRADICTED')]
    return [dict(CASE_ID=n,STATE=s,INDEPENDENT_SYNTHETIC_FACTS=f,EXPECTED_STATUS=e,ACTUAL_STATUS=classify(s,f),PASS=classify(s,f)==e,SYNTHETIC_ONLY=True,ACTUAL_DOMAIN_CLOSURES=0) for n,s,f,e in cases]
