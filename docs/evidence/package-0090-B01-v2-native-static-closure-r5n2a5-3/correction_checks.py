"""Regression evidence for reviewer counterexamples; no gate closure computation."""
import copy,json,hashlib
from pathlib import Path
from model import symbol,eq,evaluate_rule,run,UNKNOWN
from typed_identity import bind,difference
O=Path(__file__).resolve().parent;E=O.parent;N=E/'package-0090-B01-v2-native-static-closure-r5n'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    checks=[]
    def check(name,value):
        checks.append(dict(id=name,passed=value is True))
        assert value is True,name
    x=symbol('u64','x');y=symbol('u64','y')
    check('boolean_false_is_not_integer_zero',eq(False,0,set()) is False)
    check('boolean_true_is_not_integer_one',eq(True,1,set()) is False)
    check('nested_boolean_is_not_integer',eq({'fields':[False]},{'fields':[0]},set()) is False)
    check('nested_unconstrained_symbols_preserve_unknown',eq({'fields':[x]},{'fields':[y]},set())==UNKNOWN)
    check('nested_explicit_disequality_is_false',eq({'fields':[x]},{'fields':[y]},{frozenset(['x','y'])}) is False)
    check('all_equal_preserves_unknown',evaluate_rule(dict(op='ALL_EQUAL',args=['$v']),dict(v=[x,y]),set())==UNKNOWN)
    fixtures=rd(O/'primary-rejected/typed-baselines.json')['fixtures']
    codec=rd(N/'native-identity-codec.json');native=rd(N/'native-participants.json')['participants'];abi=rd(N/'native-message-abi.json')
    inputs=rd(E/'package-0090-B01-v2-native-static-closure-r5n2a5/qualification-input-ledger.json')['inputs']
    bindings=bind(fixtures,native,codec,abi,inputs)
    tag_rule=dict(id='FIXED_INPUT_TAGS',expression=dict(op='EXACT_SEQUENCE',args=['$input_tags','$allowed_input_tags']),evidence_refs=['native-message-abi.json#/input_record_schema'])
    for fid,fixture in fixtures.items():
        check(fid+'/exact_tags_admit',run(fixture,[],[tag_rule])['admitted'])
        for label,tags in [('empty',[]),('duplicate',[1,1,2,3]),('reordered',[3,2,1]),('extra',[1,2,3,4])]:
            check(fid+'/'+label+'_tags_reject',not run(fixture,[dict(field='input_tags',new_value=tags)],[tag_rule])['admitted'])
        for name in fixture['constructor_bindings']:
            frame=fixture['state']['expected_'+name]
            check(fid+'/'+name+'/exact_field_set',set(frame['fields'])=={f['name'] for f in codec['schemas'][frame['schema_name']]})
            rule=dict(id='MATCH',expression=dict(op='EQ',args=['$observed_'+name,'$expected_'+name]),evidence_refs=[])
            check(fid+'/'+name+'/actual_component_mutation_rejects',not run(fixture,[difference(fixture,'observed_'+name,fid+'/regression')],[rule])['admitted'])
        result=run(fixture,[],[])['state']
        if fixture['mode']=='FRESH_ENROLLMENT':
            check(fid+'/derived_full_cohort',all(result[k] is True for k in ['drain_complete','old_generation_extinct','fresh_material_complete','cohort_requalification_complete']))
            drained=copy.deepcopy(fixture['state']['lifecycle_records']['drain_receipts']);drained.pop('POSTMASTER')
            check(fid+'/missing_actual_drain_receipt_rejects',run(fixture,[dict(field='lifecycle_records',path=['drain_receipts'],new_value=drained)],[])['state']['drain_complete'] is False)
    payload=dict(status='INCREMENTAL_CORRECTION_CHECKS_ONLY_NOT_350_ATTACK_REEVALUATION',checks=checks,total=len(checks),failures=sum(not c['passed'] for c in checks),fixture_count=len(bindings),N1_SUBSTITUTION_STATIC_WITNESSES='OPEN',remaining='Catalog/effect witnesses, observer/writer binding, POSTMASTER inheritance semantics and independent revalidation remain unclosed')
    (O/'correction-check-results.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in payload.items() if k!='checks'}))
if __name__=='__main__':main()
