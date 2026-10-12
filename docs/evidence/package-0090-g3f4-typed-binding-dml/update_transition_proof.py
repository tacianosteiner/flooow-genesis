"""Bounded source proof of UPDATE cardinality and immediate zero-row denial.
Does not close triggers, external authority, global NULL safety or runtime parity.
"""
import hashlib,json
from source_binding import BASE,read,strings,walk
OUT=BASE/'continuation-08'
def conjuncts(n):
    if 'BoolExpr' in n:
        b=n['BoolExpr']
        if b['boolop']!='AND_EXPR':return []
        return [x for a in b['args'] for x in conjuncts(a)]
    return [n]
def main():
    source=read(OUT/'EXPANDED-DML-DEPENDENCIES.json');proofs=[]
    for item in source:
        if item['kind']!='UpdateStmt':continue
        n=item['exact_ast'];rel=n['relation'];alias=rel.get('alias',{}).get('aliasname',rel['relname']);keys=[]
        for c in item['constraint_asts']:
            v=c['ast']['Constraint']
            if v['contype']=='CONSTR_PRIMARY':keys.append([c['column']] if c['column'] else strings(v['keys']))
        bound={};predicates=conjuncts(n.get('whereClause',{}))
        for expr in predicates:
            a=expr.get('A_Expr',{})
            if a.get('kind')!='AEXPR_OP' or strings(a.get('name',[]))!=['=']:continue
            for left,right in [('lexpr','rexpr'),('rexpr','lexpr')]:
                refs=strings(a.get(left,{}).get('ColumnRef',{}).get('fields',[]))
                if not refs or len(refs)>2 or len(refs)==2 and refs[0]!=alias:continue
                rhs=a.get(right,{});dependent=False
                for k,v,_ in walk(rhs):
                    if k=='ColumnRef':
                        r=strings(v['fields'])
                        if len(r)==1 or r[0]==alias:dependent=True
                # Parameters/constants and NEW/OLD per-row records do not vary
                # with each candidate target row. Do not accept function calls.
                if any(k in ['FuncCall','SubLink'] for k,_,_ in walk(rhs)):dependent=True
                if not dependent:bound[refs[-1]]=rhs
        key=next((k for k in keys if all(col in bound for col in k)),None)
        following=item['following_sibling_control_ast'];guard=following[0].get('PLpgSQL_stmt_if') if following else None
        deny=bool(guard and guard.get('cond',{}).get('PLpgSQL_expr',{}).get('query','').strip().upper()=='NOT FOUND' and
                  guard.get('then_body') and guard['then_body'][0].get('PLpgSQL_stmt_raise',{}).get('elog_level',21)>=21)
        proofs.append({'id':item['id'],'source':item['original_source'],'function':item['function'],'statement_ordinal':item['statement_ordinal'],
            'primary_key_asts':[c for c in item['constraint_asts'] if c['ast']['Constraint']['contype']=='CONSTR_PRIMARY'],
            'target_key':key,'bound_key_expressions':bound,'grouped_predicate':n.get('whereClause'),
            'AT_MOST_ONE_TARGET_ROW_SOURCE_PROVEN':bool(key),'IMMEDIATE_ZERO_ROW_DENIAL_SOURCE_PROVEN':deny,
            'exact_zero_row_guard':guard if deny else None,
            'EXACTLY_ONE_ON_NORMAL_CONTINUATION_SOURCE_PROVEN':bool(key and deny),
            'zero_row_counterexample_required':not deny,
            'remaining':'Catalog/constraint/trigger parity and complete caller path/authority proof; this is one subobligation only',
            'proof_paths':['STATIC_SOURCE_PROOF','EXECUTABLE_SQL_NEGATIVE','CONSTRAINT_FAILURE','DML_STATE_TRANSITION']})
    d={'UPDATE_SITE_N':len(proofs),'AT_MOST_ONE_TARGET_ROW_SOURCE_PROVEN_N':sum(x['AT_MOST_ONE_TARGET_ROW_SOURCE_PROVEN'] for x in proofs),
       'IMMEDIATE_ZERO_ROW_DENIAL_SOURCE_PROVEN_N':sum(x['IMMEDIATE_ZERO_ROW_DENIAL_SOURCE_PROVEN'] for x in proofs),
       'EXACTLY_ONE_ON_NORMAL_CONTINUATION_SOURCE_PROVEN_N':sum(x['EXACTLY_ONE_ON_NORMAL_CONTINUATION_SOURCE_PROVEN'] for x in proofs),'DML_COMPLETE_N':0,'proofs':proofs}
    (OUT/'UPDATE-TRANSITION-SUBPROOFS.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');print({k:v for k,v in d.items() if k!='proofs'})
if __name__=='__main__':main()
