"""Three-valued source rules and exact consumer context; no SQL execution."""
import collections,hashlib,json,itertools
from source_binding import BASE,walk,strings,read

INPUT=BASE/'continuation-05'
OUT=BASE/'continuation-06'
T,F,U='TRUE','FALSE','UNKNOWN'
def logical(op,values):
    if op=='NOT':return U if values[0]==U else F if values[0]==T else T
    if op=='AND':return F if F in values else U if U in values else T
    if op=='OR':return T if T in values else U if U in values else F
    raise ValueError(op)
def compare(a,b,distinct=False):
    if distinct:return F if a==b else T
    return U if a is None or b is None else T if a==b else F
def membership(value,elements,negate=False):
    state=logical('OR',[compare(value,x) for x in elements])
    return logical('NOT',[state]) if negate else state
def quantified(value,elements,all_=False):
    if elements is None:return U
    return logical('AND' if all_ else 'OR',[compare(value,x) for x in elements])

def main():
    assert logical('AND',[F,U])==F and logical('OR',[T,U])==T and logical('NOT',[U])==U
    assert membership(1,[2,None],True)==U and quantified(1,[],True)==T and quantified(1,[])==F
    assert compare(None,None,True)==F and compare(None,1,True)==T
    controls={'truth_tables':[{ 'operator':op,'left':a,'right':b,'result':logical(op,[a,b])} for op in ['AND','OR'] for a,b in itertools.product([T,F,U],repeat=2)],
              'NOT':{x:logical('NOT',[x]) for x in [T,F,U]},
              'NULL_comparison':{'ordinary_equality_null_null':compare(None,None),'distinct_null_null':compare(None,None,True),'distinct_null_value':compare(None,1,True)},
              'IN_NOT_IN':{'match_with_null':membership(1,[1,None]),'no_match_with_null':membership(1,[2,None]),'not_in_no_match_with_null':membership(1,[2,None],True)},
              'ANY_ALL':{'empty_any':quantified(1,[]),'empty_all':quantified(1,[],True),'null_array':quantified(1,None),'all_with_null':quantified(1,[1,None],True)},
              'scope':'ABSTRACT_PG_RULE_CONTROLS_NOT_EXECUTABLE_SQL_OR_FULL_SOURCE_SAFETY'}
    items=[]
    for path in sorted(INPUT.glob('*.json')):
        if path.name=='EXPANDED-SOURCE-GRAPH.json':continue
        f=read(path)
        for stmt in f['statements']:
            for kind,node,astpath in walk(stmt['ast']):
                if kind not in ['BoolExpr','NullTest','BooleanTest','A_Expr','SubLink','CaseExpr','CoalesceExpr']:continue
                if kind=='A_Expr' and node.get('kind')=='AEXPR_OP' and not any(op in ['=','<>','<','>','<=','>='] for op in strings(node.get('name',[]))):continue
                rule={
                    'BoolExpr':'Exact AND/OR/NOT grouping follows three-valued truth tables; never flatten leaves into independent acceptance.',
                    'NullTest':'Scalar IS NULL/IS NOT NULL are two-valued. Row/composite tests require all-field NULL/non-NULL semantics; mixed rows can satisfy neither.',
                    'BooleanTest':'IS [NOT] TRUE/FALSE/UNKNOWN are explicit two-valued tests; ordinary NOT differs.',
                    'A_Expr':'Ordinary strict comparisons can be UNKNOWN. IN/NOT IN and ANY/ALL retain NULL/empty-array/operator semantics; DISTINCT is null-safe.',
                    'SubLink':'EXISTS tests presence, not projected values; UNKNOWN WHERE rows do not exist for this subquery.',
                    'CaseExpr':'Only TRUE WHEN wins; unmatched/NULL branch chooses later WHEN/ELSE, whose value may remain NULL.',
                    'CoalesceExpr':'First non-NULL expression wins; it does not establish identity, authorization or actual zero.'}[kind]
                contexts=[]
                if 'whereClause' in astpath:contexts.append('WHERE_REQUIRES_TRUE')
                if 'quals' in astpath:contexts.append('JOIN_MATCH_REQUIRES_TRUE_OUTER_JOIN_NULL_EXTENSION_REVIEW')
                if 'havingClause' in astpath:contexts.append('HAVING_REQUIRES_TRUE')
                if 'CaseWhen' in astpath:contexts.append('CASE_WHEN_TRUE_ONLY')
                cp=stmt.get('control_ast_path',[])
                if 'PLpgSQL_stmt_if' in cp or 'PLpgSQL_if_elsif' in cp:contexts.append('IF_TRUE_BRANCH_FALSE_OR_UNKNOWN_FALLTHROUGH')
                if not contexts:contexts.append('VALUE_OR_RETURN_NULLABILITY_REQUIRES_DATAFLOW_REVIEW')
                items.append({'source_function':f['function']['signature'],'source':f['function']['source'],'statement_ordinal':stmt['ordinal'],'ast_path':list(astpath),
                              'node_kind':kind,'operator':node.get('kind') or node.get('boolop') or node.get('nulltesttype') or node.get('booltesttype') or node.get('subLinkType'),
                              'source_rule':rule,'exact_consumer_contexts':contexts,'grouping_hash':hashlib.sha256(json.dumps(node,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                              'authorization_or_state_safety_complete':False,'missing_fact':'Operand strictness/coercion/nullability and complete acceptance/state-effect dataflow; rule knowledge alone does not close it.',
                              'proof_paths':['STATIC_SOURCE_PROOF','EXECUTABLE_SQL_NEGATIVE','CONSTRAINT_FAILURE']})
    (OUT/'NULL-CONSUMER-RULES.json').write_text(json.dumps(items,separators=(',',':'),sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    (OUT/'THREE-VALUED-RULE-CONTROLS.json').write_text(json.dumps(controls,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    summary={'NULL_SENSITIVE_AST_CANDIDATE_N':len(items),'rule_context_mapped_n':len(items),'NULL_SEMANTICS_RESOLVED_N':'UNKNOWN_FULL_SEMANTIC_SET_NOT_PROVEN',
             'NULL_SEMANTICS_UNRESOLVED_N':'UNKNOWN_OPERAND_AND_EFFECT_PROOF_OPEN','NULL_SEMANTICS_MISMATCH_N':'UNKNOWN_NOT_ZERO_CLAIM',
             'no_runtime_execution':True,'scope':'Expanded original source AST including structured SQL bodies and trigger functions'}
    (OUT/'NULL-SEMANTICS-STATUS.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');print(json.dumps(summary))

if __name__=='__main__':main()
