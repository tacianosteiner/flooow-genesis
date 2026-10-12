"""Structural CFG with grouped guards and explicit error/loop obligations.

Never claims runtime/semantic acceptance from a syntactically complete graph.
"""
import collections,hashlib,json
from source_binding import BASE,ROOT,read,walk

INPUT=BASE/'continuation-05'
OUT=BASE/'continuation-06'
SUPPORTED={'PLpgSQL_stmt_block','PLpgSQL_stmt_if','PLpgSQL_stmt_assign','PLpgSQL_stmt_raise','PLpgSQL_stmt_execsql',
 'PLpgSQL_stmt_perform','PLpgSQL_stmt_return','PLpgSQL_stmt_return_next','PLpgSQL_stmt_return_query',
 'PLpgSQL_stmt_fori','PLpgSQL_stmt_fors','PLpgSQL_stmt_foreach_a'}

def uid(parts):return hashlib.sha256(json.dumps(parts,separators=(',',':'),sort_keys=True).encode()).hexdigest()[:24]
def dump(n,x):(OUT/n).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')

class Builder:
    def __init__(self,f):self.f=f;self.nodes=[];self.edges=[];self.gaps=[];self.exception='PROPAGATE_SQL_EXCEPTION_TO_CALLER'
    def edge(self,a,b,condition):self.edges.append({'from':a,'to':b,'condition':condition})
    def seq(self,seq,path,successor):
        following=successor
        for i in reversed(range(len(seq))):following=self.stmt(seq[i],path+(i,),following)
        return following
    def stmt(self,wrapped,path,successor):
        kind=next((k for k in wrapped if k.startswith('PLpgSQL_stmt_')),None)
        if kind not in SUPPORTED:
            self.gaps.append({'path':list(path),'kind':kind,'reason':'UNHANDLED_CONTROL_KIND'});return successor
        value=wrapped[kind];key=uid([self.f['function']['signature'],path,kind]);self.nodes.append({'id':key,'kind':kind,'path':list(path),
             'source':self.f['function']['source'],'line_in_compiled_body':value.get('lineno'),
             'guard_ast':value.get('cond'),'NULL_CONTROL_RULE':'TRUE branch only; FALSE and UNKNOWN continue to next alternative' if kind=='PLpgSQL_stmt_if' else None,
             'semantic_class':'CONTROL_STRUCTURE_SOURCE_FACT_NOT_FINAL_GOVERNED_ITEM',
             'proof_paths':['STATIC_SOURCE_PROOF','EXECUTABLE_SQL_POSITIVE','EXECUTABLE_SQL_NEGATIVE']})
        p=path+(kind,)
        if kind=='PLpgSQL_stmt_block':
            if value.get('exceptions'):
                self.gaps.append({'node':key,'reason':'EXCEPTION_SQLSTATE_DISPATCH_REQUIRES_CALLEE_DML_ERROR_MAPPING','exact_ast':value['exceptions']})
            body=self.seq(value.get('body',[]),p+('body',),successor);self.edge(key,body,'ENTER_BLOCK')
        elif kind=='PLpgSQL_stmt_if':
            then=self.seq(value.get('then_body',[]),p+('then_body',),successor)
            fallback=self.seq(value.get('else_body',[]),p+('else_body',),successor)
            for i in reversed(range(len(value.get('elsif_list',[])))):
                wrapped_elif=value['elsif_list'][i];elifnode=wrapped_elif.get('PLpgSQL_if_elsif',wrapped_elif)
                eid=uid([key,'ELSIF',i]);body=self.seq(elifnode.get('stmts',[]),p+('elsif_list',i,'stmts'),successor)
                self.nodes.append({'id':eid,'kind':'ELSIF','guard_ast':elifnode.get('cond'),'source':self.f['function']['source']})
                self.edge(eid,body,'TRUE');self.edge(eid,fallback,'FALSE_OR_UNKNOWN');fallback=eid
            self.edge(key,then,'TRUE');self.edge(key,fallback,'FALSE_OR_UNKNOWN')
        elif kind in ['PLpgSQL_stmt_fori','PLpgSQL_stmt_fors','PLpgSQL_stmt_foreach_a']:
            body=self.seq(value.get('body',[]),p+('body',),key);self.edge(key,body,'NEXT_VALID_ITERATION');self.edge(key,successor,'NO_MORE_ITERATIONS')
            self.gaps.append({'node':key,'reason':'LOOP_INPUT_CARDINALITY_BOUND_STEP_AND_ERROR_SEMANTICS_NOT_PROVEN','loop_ast_fields':{k:v for k,v in value.items() if k!='body'}})
        elif kind=='PLpgSQL_stmt_return':self.edge(key,'FUNCTION_RETURN','EARLY_RETURN')
        elif kind=='PLpgSQL_stmt_raise':
            if value.get('elog_level',21)>=21:self.edge(key,self.exception,'RAISE_EXCEPTION')
            else:self.edge(key,successor,'NONTERMINATING_RAISE')
        else:
            self.edge(key,successor,'NORMAL_COMPLETION')
            self.edge(key,self.exception,'SQL_OR_EXPRESSION_ERROR')
        return key
    def build(self):
        action=self.f.get('control_ast')
        if action:entry=self.stmt(action,(), 'FUNCTION_FALLTHROUGH_RETURN_RULE')
        else:
            entry='SQL_BODY_ENTRY'
            self.nodes.append({'id':entry,'kind':'SQL_BODY','source':self.f['function']['source'],'body_hashes':[uid(s['ast']) for s in self.f['statements']],
                               'NULL_CONTROL_RULE':'SQL CASE/COALESCE/RETURN and three-valued predicates retained in exact body AST'})
            self.edge(entry,'FUNCTION_RETURN','SQL_BODY_RESULT');self.edge(entry,self.exception,'SQL_BODY_ERROR')
        return {'signature':self.f['function']['signature'],'entry':entry,'nodes':self.nodes,'edges':self.edges,'semantic_gaps':self.gaps,
                'structural_kind_coverage_complete':not any(x.get('reason')=='UNHANDLED_CONTROL_KIND' for x in self.gaps),
                'full_control_flow_semantics_complete':False,'raw_source_ast_preserved':True}

def main():
    OUT.mkdir(exist_ok=True);graphs={}
    for p in sorted(INPUT.glob('*.json')):
        if p.name=='EXPANDED-SOURCE-GRAPH.json':continue
        f=read(p);graph=Builder(f).build();graphs[graph['signature']]=graph
        dump(uid(graph['signature'])+'.json',graph)
    source=read(INPUT/'EXPANDED-SOURCE-GRAPH.json');adj=collections.defaultdict(set)
    for edge in source['edges']:adj[edge['caller']].update(edge.get('candidate_targets',[]))
    def reach(roots):
        seen=set();queue=list(roots)
        while queue:
            item=queue.pop()
            if item in seen:continue
            seen.add(item);queue.extend(adj[item]-seen)
        return seen
    cases=read(ROOT/'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/POSITIVE-CASE-PRECONDITIONS.json');rows=[]
    for case in cases:
        roots=[w['signature'].replace('pg_catalog.','') for w in case['WRAPPERS']];members=reach(roots)
        rows.append({'case_id':case['CASE_ID'],'entry_signatures':roots,'transitive_functions':sorted(members),
                     'structural_cfg_available':all(k in graphs and graphs[k]['structural_kind_coverage_complete'] for k in members),
                     'full_control_semantics_complete':False,'remaining':'operator/callee/constraint/rowcount/exception/loop and path-precondition proofs'})
    dump('CASE-CONTROL-FLOW.json',{'case_n':13,'structural_cfg_available_n':sum(x['structural_cfg_available'] for x in rows),
                                 'CONTROL_FLOW_COMPLETE_N':0,'semantic_completion_not_claimed':True,'cases':rows})
    print('STRUCTURAL_CASE_CFG=13; COMPLETE_EXECUTION_SEMANTICS=0; SOURCE_AST_AND_GROUPING_PRESERVED')

if __name__=='__main__':main()
