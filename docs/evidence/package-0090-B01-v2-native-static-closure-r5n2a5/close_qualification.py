"""Phase A only. Enforce independent review before opening Phase B."""
import hashlib,json
from qualification import O,R,N,N1,rd,put,pointer,sha
def checks():
    results=[]
    def ck(n,v):results.append(dict(name=n,passed=bool(v)))
    inputs=rd(O/'qualification-input-ledger.json')['inputs'];participants=rd(O/'seven-participant-qualification.json')['participants'];model=rd(N1/'participant-qualification.json')['matrix'];canonical=rd(N/'native-participants.json')['participants'];names={p['PARTICIPANT_ID'] for p in canonical}
    required={p['PARTICIPANT_ID']+'/'+x['args'][0] for p in model for x in p['qualification']['args']}
    ck('exact70inputdenominator',len(inputs)==len({i['QUALIFICATION_INPUT_ID'] for i in inputs})==len(required)==70 and {i['QUALIFICATION_INPUT_ID'] for i in inputs}==required)
    ck('exact7participants',len(participants)==7 and {p['PARTICIPANT_ID'] for p in participants}==names)
    for p in participants:
        pid=p['PARTICIPANT_ID'];ck('28dimensions:'+pid,len(p['QUALIFICATION_DIMENSIONS'])==len({d['DIMENSION'] for d in p['QUALIFICATION_DIMENSIONS']})==28);ck('notlivequalified:'+pid,p['RUNTIME_QUALIFIED'] is False)
        ck('dimension_input_lineage:'+pid,all(d['INPUT_ID'] in required and bool(d['SOURCE_EVIDENCE']) for d in p['QUALIFICATION_DIMENSIONS']))
    for inp in inputs:
        iid=inp['QUALIFICATION_INPUT_ID'];ck('resolved:'+iid,inp['RESOLUTION_STATUS']=='RESOLVED' and inp['physical_values_present'] is False)
        ck('nonemptyrule:'+iid,bool(inp['DERIVATION_RULE']) and bool(inp['NULL_OR_UNKNOWN_BEHAVIOR']) and bool(inp['FAIL_CLOSED_BEHAVIOR']))
        for i,s in enumerate(inp['SOURCE_PROVENANCE']):
            p=R/s['path'];value=pointer(rd(p),s['pointer']);digest=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();ck('source:'+iid+':'+str(i),sha(p)==s['sha256'] and digest==s['canonical_fact_sha256'])
        if inp['INPUT_PURPOSE'] in ['INDEPENDENT_OBSERVER_RECEIPT','COMPLETED_WORK_RECEIPT']:
            rule=inp['DERIVATION_RULE'];route=rule['ROUTE_BINDING'];ck('exactrole_route:'+iid,route['subject']==inp['PARTICIPANT_ID'] and route['challenge_sender']=='HEALTH_GUARD' and route['response_recipient']=='HEALTH_GUARD')
            ck('independentpublication:'+iid,rule['INDEPENDENT_OBSERVATION_REQUIREMENT']['purpose']==2 and bool(rule['OBSERVATION_PUBLICATION_COMPARISON_MAP']) and bool(rule['ROLE_RESULT_FIELD_COMPARISON_MAP']) and bool(rule['RESPONSE_FIELD_COMPARISON_MAP']))
    review=rd(O/'qualification-adversarial-review.json');ck('independentqualificationPASS',review['INDEPENDENT_QUALIFICATION_REVIEW']=='PASS' and review['QUALIFICATION_ADVERSARIAL_FINDINGS_OPEN']==0)
    for p,h in review.get('source_sha256',{}).items():ck('reviewhash:'+p,sha(R/p)==h)
    return dict(scope='PHASE_A_STATIC_INPUT_RESOLUTION_ONLY',checks_distinct=len(results),test_failures=sum(not x['passed'] for x in results),checks=results)
def main():
    result=checks();put('qualification-static-checks.json',result);review=rd(O/'qualification-adversarial-review.json');ledger=rd(O/'qualification-input-ledger.json')
    closed=result['test_failures']==0 and ledger['resolved']==70 and ledger['unresolved']==ledger['contradicted']==0 and review['INDEPENDENT_QUALIFICATION_REVIEW']=='PASS' and review['QUALIFICATION_ADVERSARIAL_FINDINGS_OPEN']==0
    put('qualification-closure.json',dict(N1_QUALIFICATION_INPUT_RESOLUTION='CLOSED' if closed else 'OPEN',PHASE_B_EXECUTED=False,QUALIFICATION_INPUTS_REQUIRED=ledger['required'],QUALIFICATION_INPUTS_RESOLVED=ledger['resolved'],QUALIFICATION_INPUTS_UNRESOLVED=ledger['unresolved'],QUALIFICATION_INPUTS_CONTRADICTED=ledger['contradicted'],INDEPENDENT_QUALIFICATION_REVIEW=review['INDEPENDENT_QUALIFICATION_REVIEW'],QUALIFICATION_ADVERSARIAL_FINDINGS_OPEN=review['QUALIFICATION_ADVERSARIAL_FINDINGS_OPEN'],qualification_static_check_failures=result['test_failures'],scope='STATIC_COMPARISON_CONTRACT_CLOSED_NOT_RUNTIME_QUALIFICATION'))
    print(json.dumps({k:v for k,v in rd(O/'qualification-closure.json').items()}))
    assert closed,'Phase B must not begin'
if __name__=='__main__':main()
