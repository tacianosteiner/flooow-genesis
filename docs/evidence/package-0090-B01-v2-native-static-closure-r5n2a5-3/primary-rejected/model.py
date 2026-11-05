"""Pure evidence evaluator. Symbolic measurements are variables, never allocated identities."""
import copy
UNKNOWN='UNKNOWN'
def symbol(sort,variable):return {'symbolic_sort':sort,'variable':variable,'not_a_physical_value':True}
def eq(a,b,distinct):
    if a is None or b is None:return UNKNOWN
    if a==b:return True
    if isinstance(a,dict) and isinstance(b,dict) and 'variable' in a and 'variable' in b:
        pair=frozenset([a['variable'],b['variable']]);return False if pair in distinct else UNKNOWN
    if type(a)!=type(b):return False
    if not isinstance(a,(dict,list)):return False
    return False
def evaluate_rule(rule,state,distinct):
    op=rule['op'];args=rule.get('args',[])
    def value(x):return state.get(x[1:]) if isinstance(x,str) and x.startswith('$') else x
    if op=='EQ':return eq(value(args[0]),value(args[1]),distinct)
    if op=='FALSE':return eq(value(args[0]),False,distinct)
    if op=='TRUE':return eq(value(args[0]),True,distinct)
    if op=='EMPTY':
        v=value(args[0]);return UNKNOWN if v is None else len(v)==0
    if op=='UNIQUE':
        v=value(args[0]);return UNKNOWN if v is None else len(v)==len(set(v))
    if op=='ALL_EQUAL':
        v=value(args[0]);return UNKNOWN if v is None or not v else all(x==v[0] for x in v)
    if op=='SUBSET':
        a,b=value(args[0]),value(args[1]);return UNKNOWN if a is None or b is None else set(a)<=set(b)
    if op=='ALL_TRUE':
        values=[evaluate_rule(x,state,distinct) for x in args]
        return False if False in values else UNKNOWN if UNKNOWN in values else True
    if op=='IMPLIES':
        premise=evaluate_rule(args[0],state,distinct);conclusion=evaluate_rule(args[1],state,distinct)
        return True if premise is False or conclusion is True else UNKNOWN if UNKNOWN in [premise,conclusion] else False
    raise ValueError('Unbound evidence operation: '+op)
def run(fixture,mutation,rules):
    state=copy.deepcopy(fixture['state']);distinct={frozenset(x) for x in fixture['distinct_variables']}
    for change in mutation:
        state[change['field']]=copy.deepcopy(change['new_value'])
        if change.get('distinct_from'):
            distinct.add(frozenset([change['new_value']['variable'],change['distinct_from']]))
    trace=[dict(predicate_id=r['id'],expression=r['expression'],value=evaluate_rule(r['expression'],state,distinct),evidence_refs=r['evidence_refs']) for r in rules]
    failed=[t['predicate_id'] for t in trace if t['value'] is False];unknown=[t['predicate_id'] for t in trace if t['value']==UNKNOWN]
    admitted=not failed and not unknown
    return dict(state=state,trace=trace,failed_predicates=failed,unknown_predicates=unknown,admitted=admitted)
