"""Offline readiness only. Never creates acceptance or policy activation."""
import json,pathlib,hashlib,copy
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evaluate(matrix, integrity, reconstruction):
    rows={(r['field'],r['scope']):r for r in matrix['rows']}
    required=[('SOURCE_ID','archived issued-pending data','RECONSTRUCTED_EXACT_SUBJECT'),('SOURCE_AUTHORITY','bounded pending provisioning issuance','SUPPORTED_UNDER_EXPLICIT_EXISTING_HOST_ASSUMPTION'),('SOURCE_PROVENANCE','archived issued-pending data','RECONSTRUCTED_BOUNDED_CHAIN'),('SOURCE_HASH_OR_EXISTING_INTEGRITY_BINDING','archived issued-pending data','RECONSTRUCTED_EXACT_BYTES')]
    ok=integrity and reconstruction is True and all(rows.get((field,scope),{}).get('status')==status for field,scope,status in required)
    return dict(pending_data_ready_for_distinct_acceptance_review=bool(ok), source_acceptance_issued=False, policy_approval=False, operative_use=False, future_blanket_release=False)
def main():
    matrix=json.loads((HERE/'field-matrix.json').read_text());bindings=json.loads((HERE/'source-bindings.json').read_text())
    integrity=all(sha(ROOT/x['path'])==x['sha256'] for x in bindings)
    recon=json.loads((HERE/'reconstruction.json').read_text())
    results=[]
    def check(name,m,i,r,want):
        actual=evaluate(m,i,r);assert actual['pending_data_ready_for_distinct_acceptance_review'] is want
        assert not any(actual[k] for k in ['source_acceptance_issued','policy_approval','operative_use','future_blanket_release'])
        results.append(dict(case=name,actual=actual))
    check('original pinned pending-data subject',matrix,integrity,recon['all_checks'],True)
    check('input bytes mismatch',matrix,False,True,False)
    check('reconstruction unavailable',matrix,True,None,False)
    check('reconstruction false',matrix,True,False,False)
    for index in range(5):
        if matrix['rows'][index]['field']=='SOURCE_ACCEPTANCE_RECORD':continue
        for mutation in ['NOT_ESTABLISHED','PASS','',None]:
            m=copy.deepcopy(matrix);m['rows'][index]['status']=mutation
            check('field '+str(index)+' replaced '+repr(mutation),m,True,True,False)
    m=copy.deepcopy(matrix);m['rows']=[x for x in m['rows'] if x['scope']!='operative policy/session use']
    check('downstream activation fields absent do not cycle input qualification',m,True,True,True)
    (HERE/'controller-results.json').write_text(json.dumps(dict(kind='READINESS_ONLY_NOT_ACCEPTANCE',source_integrity=integrity,cases=results),indent=2)+'\n')
if __name__=='__main__':main()
