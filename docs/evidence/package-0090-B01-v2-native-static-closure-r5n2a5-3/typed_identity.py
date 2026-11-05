"""Construct symbolic instances of the frozen codecs, without allocating physical values."""
import copy
from model import symbol,eq,UNKNOWN
def frame(codec,name,scope,overrides=None):
    schema=codec['schemas'][name] if name!='bootstrap_context' else codec['bootstrap_context_schema']
    fields={f['name']:symbol(f['type'],scope+'/'+name+'/'+f['name']) for f in schema}
    assert set(overrides or {})<=set(fields), (name, set(overrides or {})-set(fields))
    fields.update(overrides or {})
    return dict(constructor='FROZEN_IDENTITY_FRAME',schema_name=name,domain='FLOOOW/PACKAGE0090/R5N/IDENTITY/'+name+'/V1',field_schema=copy.deepcopy(schema),encoding=codec['encoding'],fields=fields)
def digest(value):return dict(constructor='SYMBOLIC_CANONICAL_FRAME_DIGEST',algorithm='SHA256_COMPLETE_FROZEN_DOMAIN_FRAME',canonical_digest_of=copy.deepcopy(value),not_an_allocated_digest=True)
def typed_set(codec,type_name,scope):
    key={'dependency_node_set':'dependency_node_schema','dependency_edge_set':'dependency_edge_schema','work_revision_set':'work_revision_schema'}[type_name]
    result=symbol(type_name,scope+'/'+type_name);result.update(element_schema=copy.deepcopy(codec[key]),encoding=codec['set_encoding'],quantification='Complete arbitrary finite approved set; no representative element or physical set allocated')
    return result
def bind(fixtures,native,codec,abi,qualification_inputs):
    ids=[p['PARTICIPANT_ID'] for p in native];actors=abi['actor_enum'];relations=[]
    for mode in ['CURRENT_WORK','FRESH_ENROLLMENT']:
        root='QUALIFIED_COHORT/'+mode
        shared={name:symbol('uuid',root+'/'+name) for name in ['qualification_id','incarnation_id','epoch']}
        hwm={pid:symbol('u64',root+'/'+pid+'/independently_current_generation') for pid in ids}
        parent_frames={who:frame(codec,'parent_identity',root+'/'+who+'/retained_birth_before_child_enrollment') for who in ['SUPERVISOR','HOST_PLATFORM']}
        records={}
        for p in native:
            pid=p['PARTICIPANT_ID'];slot=p['participant_enum'];scope=root+'/'+pid;parent=parent_frames['HOST_PLATFORM' if pid=='SUPERVISOR' else 'SUPERVISOR']
            bootstrap=frame(codec,'bootstrap_context',scope,dict(shared,participant_id=slot,generation=hwm[pid]))
            source=frame(codec,'source_identity',scope)
            recipe=frame(codec,'build_recipe_identity',scope,dict(source_identity=digest(source)))
            loader=frame(codec,'loader_identity',scope)
            binary=frame(codec,'binary_module_identity',scope,dict(loader_identity=digest(loader),build_recipe_identity=digest(recipe)))
            dependencies=frame(codec,'dependency_set_identity',scope,dict(dependency_nodes=typed_set(codec,'dependency_node_set',scope),dependency_edges=typed_set(codec,'dependency_edge_set',scope)))
            process=frame(codec,'process_instance_identity',scope,dict(parent_identity=digest(parent),participant_id=slot,qualification_id=shared['qualification_id'],incarnation_id=shared['incarnation_id']))
            generation=frame(codec,'generation',scope,dict(shared,participant_id=slot,generation_high_water=hwm[pid]))
            purpose=codec['credential_purpose_enum']['POSTMASTER_SERVER_ENDPOINT' if pid=='POSTMASTER' else 'GENERATION_TRANSPORT']
            credential=frame(codec,'credential_identity',scope,dict(credential_purpose=purpose,participant_id=slot,generation=hwm[pid],bootstrap_context_digest=digest(bootstrap)))
            channel=frame(codec,'authenticated_channel_identity',scope,dict(bootstrap_context_digest=digest(bootstrap),sender_birth_identity=digest(process)))
            enrollment=frame(codec,'enrollment_identity',scope,dict(bootstrap_context_digest=digest(bootstrap),participant_id=slot,parent_identity=digest(parent),process_identity=digest(process),source_identity=digest(source),build_recipe_identity=digest(recipe),binary_module_identity=digest(binary),dependency_set_identity=digest(dependencies),loader_identity=digest(loader),credential_identity=digest(credential),channel_identity=digest(channel)))
            revision=frame(codec,'registry_revision',scope,dict(per_entity_work_revision_vector=typed_set(codec,'work_revision_set',scope)))
            module=frame(codec,'binary_module_identity',scope+'/independently_approved_loaded_module',dict(loader_identity=digest(loader),build_recipe_identity=digest(recipe)))
            records[pid]=dict(binary=binary,module=module,dependencies=dependencies,loader=loader,parent=parent,subject_process=process,generation=generation,enrollment=enrollment,credential=credential,channel=channel,registry_revision=revision,bootstrap=bootstrap)
        # The retained SUPERVISOR parent tuple and that actor's own process birth
        # describe the same kernel object, rather than unrelated digest variables.
        sup=records['SUPERVISOR'];parent_frames['SUPERVISOR']['fields'].update(retained_pidfd_dev=copy.deepcopy(sup['subject_process']['fields']['child_pidfd_dev']),retained_pidfd_inode=copy.deepcopy(sup['subject_process']['fields']['child_pidfd_inode']),kernel_start_ticks=copy.deepcopy(sup['subject_process']['fields']['child_kernel_start_ticks']),approved_binary_identity=digest(sup['binary']))
        for pid in ids:
            record=records[pid];record['parent']=copy.deepcopy(parent_frames['HOST_PLATFORM' if pid=='SUPERVISOR' else 'SUPERVISOR'])
            record['subject_process']['fields']['parent_identity']=digest(record['parent'])
            record['channel']['fields']['sender_birth_identity']=digest(record['subject_process'])
            record['enrollment']['fields'].update(parent_identity=digest(record['parent']),process_identity=digest(record['subject_process']),channel_identity=digest(record['channel']))
        for p in native:
            pid=p['PARTICIPANT_ID'];fixture=fixtures[pid+'/'+mode];state=fixture['state'];emitter=next(f['sender'] for f in abi['frames'] if f['id']==pid+'/RESPONSE')
            for field in ['binary','module','dependencies','loader','parent','subject_process','generation','enrollment','credential','channel','registry_revision']:
                state['expected_'+field]=copy.deepcopy(records[pid][field]);state['observed_'+field]=copy.deepcopy(records[pid][field])
            state['expected_kernel_sender']=copy.deepcopy(records[emitter]['subject_process']);state['observed_kernel_sender']=copy.deepcopy(records[emitter]['subject_process'])
            state['lifecycle_records']=dict(required_slots=ids,drain_receipts={x:dict(subject=x,independent_outcome='DRAIN_PROVEN') for x in ids} if mode=='FRESH_ENROLLMENT' else {},extinction_receipts={x:dict(subject=x,independent_outcome='EXTINCTION_PROVEN') for x in ids} if mode=='FRESH_ENROLLMENT' else {},fresh_private_key_slots=[x for x in ids if x!='POSTMASTER'],fresh_endpoint_manifest_slots=['POSTMASTER'],qualification_receipts={q['QUALIFICATION_INPUT_ID']:dict(subject=q['PARTICIPANT_ID'],input_id=q['QUALIFICATION_INPUT_ID'],source_validation='TRUE',observed_generation=copy.deepcopy(records[q['PARTICIPANT_ID']]['generation']),expected_generation=copy.deepcopy(records[q['PARTICIPANT_ID']]['generation'])) for q in qualification_inputs},required_qualification_input_ids=[q['QUALIFICATION_INPUT_ID'] for q in qualification_inputs])
            state['lifecycle_records']['material_records']={x:dict(subject=x,purpose=codec['credential_purpose_enum']['POSTMASTER_SERVER_ENDPOINT' if x=='POSTMASTER' else 'GENERATION_TRANSPORT'],generation=copy.deepcopy(hwm[x]),expected_generation=copy.deepcopy(hwm[x]),identity_kind='EXPECTED_ENDPOINT_MANIFEST' if x=='POSTMASTER' else 'INDEPENDENTLY_EXPECTED_FRESH_PUBLIC_KEY_IDENTITY',observed_reference=symbol('bytes32',root+'/'+x+'/current_material_reference'),expected_reference=symbol('bytes32',root+'/'+x+'/current_material_reference'),retired_reference=symbol('bytes32',root+'/'+x+'/retired_material_reference')) for x in ids}
            for material in state['lifecycle_records']['material_records'].values():fixture['distinct_variables'].append([material['expected_reference']['variable'],material['retired_reference']['variable']])
            fixture['constructor_bindings']={field:dict(schema_name=value['schema_name'],all_fields=[x['name'] for x in value['field_schema']],expected_state_field='expected_'+field,observed_state_field='observed_'+field) for field,value in records[pid].items() if field!='bootstrap'}
            fixture['relational_bindings']=['process.parent_identity = digest(exact retained parent frame)','child expected parent frame is shared with the same cohort SUPERVISOR birth; SUPERVISOR binds HOST_PLATFORM','process participant/qualification/incarnation fields = exact context','generation participant/context/high-water = current trusted slot record','credential participant/generation/bootstrap = same slot/context; POSTMASTER purpose3 is endpoint, not a signing key','channel sender birth/bootstrap = exact subject process/context','enrollment binds parent/process/source/recipe/binary/dependency/loader/credential/channel and context','actual emitter uses its own current process record (CENSUS for POSTMASTER)']
            relations.append(dict(fixture=fixture['id'],subject=pid,emitter=emitter,constructor_bindings=fixture['constructor_bindings'],relations=fixture['relational_bindings']))
    return relations
MUTATION_FIELDS={'observed_binary':'complete_file_sha256','observed_module':'complete_file_sha256','observed_dependencies':'dependency_nodes','observed_loader':'complete_loader_file_sha256','observed_parent':'kernel_start_ticks','observed_subject_process':'child_kernel_start_ticks','observed_kernel_sender':'child_kernel_start_ticks','observed_generation':'generation_high_water','observed_enrollment':'process_identity','observed_credential':'credential_certificate_or_endpoint_manifest_digest','observed_channel':'sender_birth_identity','observed_registry_revision':'generation_registry_revision'}
def difference(fixture,field,caseid):
    old=fixture['state'][field]
    path=['fields',MUTATION_FIELDS[field]] if isinstance(old,dict) and old.get('constructor')=='FROZEN_IDENTITY_FRAME' else []
    leaf=old
    for key in path:leaf=leaf[key]
    if isinstance(leaf,dict) and leaf.get('constructor')=='SYMBOLIC_CANONICAL_FRAME_DIGEST':
        # Mutate a complete observed process preimage rather than an opaque digest label.
        path+=['canonical_digest_of','fields','child_kernel_start_ticks'];leaf=leaf['canonical_digest_of']['fields']['child_kernel_start_ticks']
    if isinstance(leaf,dict) and 'variable' in leaf:
        new=copy.deepcopy(leaf);new['variable']=caseid+'/'+field+'/wrong_observed_component'
        return dict(field=field,path=path,new_value=new,distinct_from=leaf['variable'],source_component=path[-1] if path else field)
    if type(leaf) is int:return dict(field=field,path=path,new_value=(leaf%7)+1,source_component=path[-1] if path else field)
    raise ValueError('UNRESOLVED typed component: '+field)
def derive_lifecycle(state,distinct):
    records=state.get('lifecycle_records')
    if records is None:return
    required=set(records['required_slots'])
    state['drain_complete']=set(records['drain_receipts'])==required and all(r['subject']==p and r['independent_outcome']=='DRAIN_PROVEN' for p,r in records['drain_receipts'].items())
    state['old_generation_extinct']=set(records['extinction_receipts'])==required and all(r['subject']==p and r['independent_outcome']=='EXTINCTION_PROVEN' for p,r in records['extinction_receipts'].items())
    material=records['material_records'];state['fresh_material_complete']=set(records['fresh_private_key_slots'])==required-{'POSTMASTER'} and len(records['fresh_private_key_slots'])==len(required)-1 and records['fresh_endpoint_manifest_slots']==['POSTMASTER'] and set(material)==required and all(m['subject']==slot and m['purpose']==(3 if slot=='POSTMASTER' else 1) and eq(m['generation'],m['expected_generation'],distinct) is True and eq(m['observed_reference'],m['expected_reference'],distinct) is True and eq(m['observed_reference'],m['retired_reference'],distinct) is False for slot,m in material.items())
    receipts=records['qualification_receipts'];state['cohort_requalification_complete']=set(receipts)==set(records['required_qualification_input_ids']) and all(r['input_id']==key and r['source_validation']=='TRUE' and eq(r['observed_generation'],r['expected_generation'],distinct) is True for key,r in receipts.items())
