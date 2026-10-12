"""Independent test-only logical V3 verifier. Not native framing or runtime.

No SQL, signing, keys, sockets, process signals or numeric policy adoption.
Observer context is synthetic trusted input, never a producer-provided receipt.
"""
from pathlib import Path
import copy,hashlib,json,re,unicodedata,uuid
from source_binding import BASE,ROOT,read

OUT=BASE/'continuation-04'
OLD=ROOT/'docs/evidence/package-0090-g3f4-sql-runtime-witness/final-02'
VERSION='TEST_ONLY_NONCANONICAL_LOGICAL_V3'
DOMAIN='FLOOOW/G3F4/LOGICAL_FRAME/V3/TEST_ONLY_NONCANONICAL'
U64=(1<<64)-1
ENVELOPE={
 'domain':'DOMAIN','test_only_noncanonical':'TRUE','frame_identity':'OPAQUE','frame_type':'FRAME_TYPE','frame_version':'VERSION',
 'participant_identity':'OPAQUE','participant_generation':'U64','consumer_identity':'OPAQUE','consumer_generation':'U64',
 'deployment_id':'UUID','incarnation_id':'UUID','binding_id':'UUID','plan_fingerprint':'SHA256','policy_hash':'SHA256',
 'boot_epoch':'OPAQUE','sequence':'U64','emitted_boottime_us':'U64','observation_epoch':'U64','registry_revision':'U64',
 'payload_digest':'SHA256','challenge':'OPAQUE','witness_type':'FRAME_TYPE','witness_generation':'U64','witness_sequence':'U64',
 'independent_verifier_identity':'OPAQUE','verification_result':'UNTRUSTED'}
PAYLOADS=read(OLD/'PAYLOAD-SCHEMAS.json')
TYPES=set(PAYLOADS)
PROFILES={x['FRAME_TYPE']:x for x in read(OLD/'RUNTIME-FRAME-CONTRACT.json')['frames']}
OPERATIONS={'SQL_COMMIT_RECEIPT','READINESS_CENSUS','ANCHOR_REGISTRATION','APPROVAL_PUBLICATION','APPROVAL_CONSUMPTION','RECONCILIATION_RECEIPT','CANCEL_OUTCOME','TERMINATE_EXIT','IDENTITY_OBSERVATION'}

def canon(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def digest(obj):return hashlib.sha256(canon(obj)).hexdigest()
def pairs(items):
    result={}
    for k,v in items:
        if k in result:raise ValueError('DUPLICATE_KEY')
        result[k]=v
    return result
def reject_float(value):raise ValueError('FLOAT_FORBIDDEN')
def no_constant(value):raise ValueError('NONFINITE_FORBIDDEN')
def decode(data):
    value=json.loads(data.decode('utf-8',errors='strict'),object_pairs_hook=pairs,parse_float=reject_float,parse_constant=no_constant)
    if canon(value)!=data:raise ValueError('NONCANONICAL_BYTES')
    return value

def valid(value,kind):
    if kind=='TRUE':return value is True
    if kind=='FALSE':return value is False
    if kind=='HEALTH_CLASS':return value=='PROCESS_ALIVE' and type(value) is str
    if kind=='OPERATION_CLASS':return type(value) is str and value in OPERATIONS
    if kind=='U64':return type(value) is int and 0<=value<=U64
    if kind=='OID':return type(value) is int and 1<=value<1<<32
    if type(value) is not str or not value or unicodedata.normalize('NFC',value)!=value:return False
    if any(ord(c)<32 or 0xd800<=ord(c)<=0xdfff for c in value):return False
    if kind=='DOMAIN':return value==DOMAIN
    if kind=='VERSION':return value==VERSION
    if kind=='FRAME_TYPE':return value in TYPES
    if kind=='UNTRUSTED':return value=='UNTRUSTED'
    if kind=='SHA256':return re.fullmatch('[0-9a-f]{64}',value) is not None
    if kind=='UUID':
        try:return str(uuid.UUID(value))==value
        except ValueError:return False
    return kind=='OPAQUE'

def payload_types(name):
    result={}
    for field,schema in PAYLOADS[name]['properties'].items():
        if schema.get('const') is False:kind='FALSE'
        elif schema.get('type')=='integer':kind='OID' if field in ['role_oid','db_oid'] else 'U64'
        elif schema.get('type')=='boolean':kind='BOOLEAN'
        else:
            kind='SHA256' if field.endswith(('_digest','_hash','_fingerprint')) else 'UUID' if field in ['binding_id','allocation_id'] else 'OPAQUE'
        if field=='health_class':kind='HEALTH_CLASS'
        if field=='operation_class':kind='OPERATION_CLASS'
        result[field]=kind
    return result

def snapshot_tuple(ctx):
    return {k:ctx[k] for k in ['participant_identity','participant_generation','consumer_identity','consumer_generation',
       'deployment_id','incarnation_id','binding_id','plan_fingerprint','policy_hash','boot_epoch','observation_epoch',
       'registry_revision','independent_verifier_identity','witness_generation','witness_sequence','anchor_identity','enrollment_generation',
       'postmaster_generation','receiver_generation','supervisor_generation','operation_binding','producer_role','consumer_role','verifier_role']}

def verify(data,observe,ledger):
    try:
        pair=decode(data)
        if type(pair) is not dict or set(pair)!= {'envelope','payload'}:raise ValueError('PAIR_SCHEMA')
        env,payload=pair['envelope'],pair['payload']
        if type(env) is not dict or set(env)!=set(ENVELOPE):raise ValueError('ENVELOPE_SCHEMA')
        if not all(valid(env[k],t) for k,t in ENVELOPE.items()):raise ValueError('ENVELOPE_TYPE')
        name=env['frame_type'];fields=payload_types(name)
        if type(payload) is not dict or set(payload)!=set(fields):raise ValueError('PAYLOAD_SCHEMA')
        if not all(valid(payload[k],t) for k,t in fields.items()):raise ValueError('PAYLOAD_TYPE')
        if env['payload_digest']!=digest(payload):raise ValueError('PAYLOAD_SUBSTITUTION')
        first=copy.deepcopy(observe())
        if first['controls_scope']!='TEST_ONLY_EXPERIMENTAL_NOT_POLICY':raise ValueError('MODEL_CONTROL_SCOPE')
        if first['anchor_independently_valid'] is not True or first['provisional'] is not False or first['quarantined'] is not False:raise ValueError('NO_CURRENT_ELIGIBILITY')
        if env['participant_identity']==env['independent_verifier_identity']:raise ValueError('SELF_VERIFIER')
        expected=snapshot_tuple(first)
        profile=PROFILES[name]
        if first['producer_role']!=profile['PRODUCER'] or first['consumer_role']!=profile['CONSUMER'] or first['verifier_role']!=profile['INDEPENDENT_VERIFIER']:raise ValueError('WRONG_INDEPENDENT_ROLE')
        for k,v in expected.items():
            if k in env and (not valid(v,ENVELOPE[k]) or env[k]!=v):raise ValueError('WRONG_CURRENT_CONTEXT:'+k)
        for k in ['postmaster_generation','receiver_generation','supervisor_generation','enrollment_generation']:
            if not valid(first[k],'U64'):raise ValueError('INVALID_OBSERVER_GENERATION')
        if 'binding_id' in payload and payload['binding_id']!=env['binding_id']:raise ValueError('PAYLOAD_BINDING_CONTEXT')
        for field,value in first['operation_binding'].items():
            if field not in payload or type(payload[field]) is not type(value) or payload[field]!=value:raise ValueError('WRONG_OPERATION_BINDING')
        if name=='generation_proof' and payload['generation']!=env['participant_generation']:raise ValueError('PAYLOAD_GENERATION')
        if name=='recovery_observation':
            bound={'postmaster_generation':'postmaster_generation','receiver_generation':'receiver_generation','supervisor_generation':'supervisor_generation',
                   'enrollment_generation':'enrollment_generation','registry_revision':'registry_revision','census_observation_epoch':'observation_epoch'}
            if any(payload[k]!=first[v] for k,v in bound.items()):raise ValueError('STALE_CENSUS_CONTEXT')
        key=(env['participant_identity'],env['participant_generation'],env['consumer_identity'],env['consumer_generation'],name)
        current=copy.deepcopy(ledger.get(key))
        if current is None or current['challenge']!=env['challenge'] or current['next_sequence']!=env['sequence']:raise ValueError('REPLAY_OR_SEQUENCE')
        if current['context_digest']!=digest(expected):raise ValueError('CHALLENGE_CONTEXT')
        if env['witness_type']!=name:raise ValueError('WRONG_COMPLETION_KIND')
        if canon(first['independent_payload'])!=canon(payload) or first['observed_outcome']!='CONFIRMED':raise ValueError('NO_INDEPENDENT_CORROBORATION')
        if not 0<=env['emitted_boottime_us']<=first['decision_now_us']:raise ValueError('FUTURE_EMISSION')
        if first['decision_now_us']-env['emitted_boottime_us']>first['experimental_max_age_us']:raise ValueError('STALE_EMISSION')
        # Re-read the independently current state immediately before acceptance.
        final=copy.deepcopy(observe())
        if snapshot_tuple(final)!=expected or final['provisional'] is not False or final['quarantined'] is not False or final['anchor_independently_valid'] is not True:raise ValueError('DECISION_CONTEXT_RACE')
        if final['experimental_max_age_us']!=first['experimental_max_age_us'] or final['controls_scope']!=first['controls_scope']:raise ValueError('MODEL_CONTROLS_CHANGED')
        if final['observed_outcome']!='CONFIRMED' or canon(final['independent_payload'])!=canon(payload):raise ValueError('CORROBORATION_RACE')
        if not 0<=env['emitted_boottime_us']<=final['decision_now_us'] or final['decision_now_us']-env['emitted_boottime_us']>final['experimental_max_age_us']:raise ValueError('DECISION_FRESHNESS_RACE')
        if ledger.get(key)!=current:raise ValueError('LEDGER_CAS_RACE')
        # Atomicity is a model obligation; this in-memory update is NOT a native
        # concurrent/durable ledger implementation or persistence proof.
        ledger[key]={'challenge':None,'next_sequence':env['sequence']+1,'context_digest':digest(expected)}
        return {'result':'MODEL_ACCEPT','liveness_only':name=='heartbeat','making_progress':name in ['progress','completed_work_witness','approval_state','enforcement_state'],
                'eligibility_created':False,'runtime_qualification':False}
    except (ValueError,UnicodeError,KeyError,TypeError,OverflowError) as e:
        return {'result':'MODEL_DENY','reason':str(e),'liveness_only':False,'making_progress':False,'eligibility_created':False,'runtime_qualification':False}

def example_value(kind,field):
    if kind=='FALSE':return False
    if kind=='TRUE':return True
    if kind in ['U64','OID']:return 1
    if kind=='HEALTH_CLASS':return 'PROCESS_ALIVE'
    if kind=='OPERATION_CLASS':return 'SQL_COMMIT_RECEIPT'
    if kind=='SHA256':return hashlib.sha256(('TEST_ONLY_NONCANONICAL:'+field).encode()).hexdigest()
    if kind=='UUID':return str(uuid.uuid5(uuid.NAMESPACE_URL,'TEST_ONLY_NONCANONICAL_MODEL:'+field))
    return 'TEST_ONLY_NONCANONICAL:'+field

def fixture(name):
    payload={k:example_value(v,k) for k,v in payload_types(name).items()}
    env={k:example_value(v,k) for k,v in ENVELOPE.items()}
    env.update(domain=DOMAIN,test_only_noncanonical=True,frame_type=name,frame_version=VERSION,witness_type=name,
               verification_result='UNTRUSTED',emitted_boottime_us=90,payload_digest=digest(payload))
    ctx={k:v for k,v in env.items()};ctx.update(anchor_identity='TEST_ONLY_NONCANONICAL:retained_anchor',enrollment_generation=1,
        producer_role=PROFILES[name]['PRODUCER'],consumer_role=PROFILES[name]['CONSUMER'],verifier_role=PROFILES[name]['INDEPENDENT_VERIFIER'],
        postmaster_generation=1,receiver_generation=1,supervisor_generation=1,
        operation_binding={k:payload[k] for k in ['operation_class','operation_id','target_anchor_identity','input_revision','completed_sequence'] if k in payload},
        controls_scope='TEST_ONLY_EXPERIMENTAL_NOT_POLICY',anchor_independently_valid=True,provisional=False,quarantined=False,
        independent_payload=copy.deepcopy(payload),observed_outcome='CONFIRMED',decision_now_us=100,experimental_max_age_us=20)
    key=(env['participant_identity'],env['participant_generation'],env['consumer_identity'],env['consumer_generation'],name)
    ledger={key:{'challenge':env['challenge'],'next_sequence':env['sequence'],'context_digest':digest(snapshot_tuple(ctx))}}
    return {'envelope':env,'payload':payload},ctx,ledger

def main():
    OUT.mkdir(exist_ok=True);results=[];schemas=[]
    for name in sorted(TYPES):
        pair,ctx,ledger=fixture(name);wire=canon(pair);accepted=verify(wire,lambda:copy.deepcopy(ctx),ledger)
        if accepted['result']!='MODEL_ACCEPT':raise AssertionError((name,accepted))
        denied=verify(wire,lambda:copy.deepcopy(ctx),ledger);assert denied['result']=='MODEL_DENY'
        cases=[{'name':'baseline','result':accepted['result']},{'name':'replay','result':denied['result']}]
        for field in ENVELOPE:
            p,c,l=fixture(name);del p['envelope'][field];before=copy.deepcopy(l);decision=verify(canon(p),lambda:copy.deepcopy(c),l)
            assert decision['result']=='MODEL_DENY' and l==before
            cases.append({'name':'missing:'+field,'result':decision['result']})
        for field in ['participant_identity','participant_generation','consumer_generation','deployment_id','incarnation_id','registry_revision','observation_epoch','witness_generation']:
            p,c,l=fixture(name);c[field]=c[field]+1 if type(c[field]) is int else example_value('UUID' if field.endswith('_id') else 'OPAQUE','WRONG_'+field)
            decision=verify(canon(p),lambda:copy.deepcopy(c),l);assert decision['result']=='MODEL_DENY';cases.append({'name':'wrong:'+field,'result':decision['result']})
        for scenario in ['stale_queue','freshness_race','census_snapshot_race','receiver_restart','supervisor_generation_loss','postmaster_restart','anchor_changed','participant_dead','provisional_anchor','no_corroboration','corroboration_race','model_bound_changed']:
            p,c,l=fixture(name);final=copy.deepcopy(c)
            if scenario=='stale_queue':c['decision_now_us']=1000;final=copy.deepcopy(c)
            elif scenario=='freshness_race':final['decision_now_us']=1000
            elif scenario=='census_snapshot_race':final['registry_revision']+=1;final['enrollment_generation']+=1
            elif scenario=='receiver_restart':final['consumer_generation']+=1
            elif scenario=='supervisor_generation_loss':final['witness_generation']+=1
            elif scenario=='postmaster_restart':final['postmaster_generation']+=1
            elif scenario=='anchor_changed':final['anchor_identity']='TEST_ONLY_NONCANONICAL:other_anchor'
            elif scenario=='participant_dead':c['anchor_independently_valid']=False;final=copy.deepcopy(c)
            elif scenario=='provisional_anchor':c['provisional']=True;final=copy.deepcopy(c)
            elif scenario=='no_corroboration':c['observed_outcome']='UNKNOWN';final=copy.deepcopy(c)
            elif scenario=='corroboration_race':final['observed_outcome']='UNKNOWN'
            elif scenario=='model_bound_changed':final['experimental_max_age_us']=10000
            observations=iter([c,final]);before=copy.deepcopy(l);decision=verify(canon(p),lambda:copy.deepcopy(next(observations)),l)
            assert decision['result']=='MODEL_DENY' and l==before
            cases.append({'name':scenario,'result':decision['result']})
        p,c,l=fixture(name);counter=[0];before=copy.deepcopy(l)
        def mutated_ledger_observation():
            counter[0]+=1
            if counter[0]==2:
                next(iter(l.values()))['next_sequence']+=1
            return c
        decision=verify(canon(p),mutated_ledger_observation,l)
        assert decision['result']=='MODEL_DENY';cases.append({'name':'in_place_ledger_cas_race','result':decision['result']})
        p,c,l=fixture(name);c['participant_generation']=True
        decision=verify(canon(p),lambda:c,l);assert decision['result']=='MODEL_DENY';cases.append({'name':'observer_boolean_generation','result':decision['result']})
        malformed=[b'{"envelope":{},"envelope":{},"payload":{}}',b'{"envelope":NaN,"payload":{}}',b'{"envelope":1.0,"payload":{}}',b'{"envelope":{}, "payload":{}}',b'\xff']
        for i,wire_bad in enumerate(malformed):
            p,c,l=fixture(name);decision=verify(wire_bad,lambda:copy.deepcopy(c),l);assert decision['result']=='MODEL_DENY';cases.append({'name':'encoding_denial:'+str(i),'result':decision['result']})
        if name=='heartbeat':assert accepted['making_progress'] is False
        schemas.append({'FRAME_TYPE':name,'FRAME_VERSION':VERSION,'DOMAIN':DOMAIN,'PRODUCER':PROFILES[name]['PRODUCER'],
                        'CONSUMER':PROFILES[name]['CONSUMER'],'VERIFIER':PROFILES[name]['INDEPENDENT_VERIFIER'],'FIELD_ORDER':{'envelope':sorted(ENVELOPE),'payload':sorted(payload_types(name))},
                        'FIELD_TYPE':{'envelope':ENVELOPE,'payload':payload_types(name)},'NULLABILITY':'NULL_FORBIDDEN_ALL_FIELDS',
                        'IDENTITY_BINDING':'Independent retained anchor and exact participant/consumer/verifier identities',
                        'GENERATION_BINDING':'Separate participant, consumer, verifier, enrollment and registry epochs; decision-time CAS',
                        'CONTEXT_BINDING':'Exact deployment/incarnation/binding/plan/policy/boot plus independent observation',
                        'SEQUENCE':'Strict next generation/channel sequence and one-use observer challenge',
                        'TIMESTAMP':'Original BOOTTIME emission; same boot; fresh both before and immediately at decision',
                        'PAYLOAD_DIGEST':'SHA256 of exact canonical payload bytes; not authority',
                        'ANTI_REPLAY':'Observer-owned generation/context-bound consumed challenge; restart invalidates prior context',
                        'FAILURE_ACTION':'Deny without liveness/progress/eligibility or mutation of later enrollment; retain ownership/quarantine',
                        'runtime_implementation':False})
        results.append({'frame_type':name,'controls':cases,'native_runtime_verified':False})
    report={'scope':'TEST_ONLY_NONCANONICAL_LOGICAL_DESIGN_MODEL_NOT_NATIVE_PROTOCOL_OR_RUNTIME_PASS',
            'experimental_controls':{'decision_now_us':100,'emitted_us':90,'max_age_us':20,'numeric_policy_authority':False},
            'FRAME_REQUIRED_N':11,'FRAME_SCHEMA_COMPLETE_N':11,'FRAME_VERIFIER_MODEL_COMPLETE_N':11,'FRAME_REPLAY_MODEL_COMPLETE_N':11,
            'MODEL_CONTROL_N':sum(len(x['controls']) for x in results),'MODEL_FAIL_N':0,'runtime_corrobation_complete':False,
            'completion_witness_contract_scope':'DESIGN_MODEL_ONLY; authenticated observation transport/atomic persistence/runtime still unproven',
            'results':results,'schemas':schemas}
    (OUT/'LOGICAL-FRAME-CONTRACT-AND-CONTROLS.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['results','schemas']}))

if __name__=='__main__':main()
