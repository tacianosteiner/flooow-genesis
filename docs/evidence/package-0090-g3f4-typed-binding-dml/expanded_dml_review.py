"""Expanded write/lock dependencies and exact rowcount control context. No SQL."""
import collections,hashlib,json
from source_binding import BASE,read,walk,strings
OUT=BASE/'continuation-08'
def dump(n,d):(OUT/n).write_text(json.dumps(d,separators=(',',':'),sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def main():
    OUT.mkdir(exist_ok=True)
    tables=read(BASE/'continuation-02/EFFECTIVE-TABLE-CATALOG.json')
    prior=read(BASE/'continuation-02/DML-CATALOG-EXPANSION.json')
    metadata={x['TARGET_RELATION']['schema']+'.'+x['TARGET_RELATION']['relation']:x for x in prior['sites'] if x['KIND']!='LockingClause'}
    graph=read(BASE/'continuation-05/EXPANDED-SOURCE-GRAPH.json');rows=[]
    for p in sorted((BASE/'continuation-05').glob('*.json')):
        if p.name=='EXPANDED-SOURCE-GRAPH.json':continue
        f=read(p);sig=f['function']['signature']
        for s in f['statements']:
            cp=s.get('control_ast_path',[]);following=[];node=f.get('control_ast')
            try:
                for k in cp[:-3]:node=node[k]
                if isinstance(cp[-4],int):
                    parent=f['control_ast']
                    for k in cp[:-4]:parent=parent[k]
                    following=parent[cp[-4]+1:]
            except (KeyError,TypeError,IndexError):pass
            for kind,n,path in walk(s['ast']):
                if kind not in ['InsertStmt','UpdateStmt','DeleteStmt','MergeStmt','LockingClause']:continue
                identity=[sig,s['ordinal'],list(path)];item={'id':hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24],
                    'function':sig,'statement_ordinal':s['ordinal'],'node_path':list(path),'kind':kind,'original_source':f['function']['source'],
                    'exact_ast':n,'control_path':cp,'following_sibling_control_ast':following,
                    'classification':'REAL_UNRESOLVED_GAP','complete':False,
                    'proof_paths':['STATIC_SOURCE_PROOF','CONSTRAINT_FAILURE','DML_STATE_TRANSITION','EXECUTABLE_SQL_NEGATIVE']}
                if kind=='LockingClause':
                    select=s['ast']
                    for k in path[:-3]:select=select[k]
                    item.update({'candidate_relations':[v for k,v,_ in walk(select) if k=='RangeVar'],
                        'lock_mode':n['strength'],'wait_policy':n['waitPolicy'],'explicit_lock_targets':strings(n.get('lockedRels',[])),
                        'remaining':['Exact scoped alias/row identity lock applicability','Lock acquisition order and concurrent isolation proof','Locking does not establish authority or participant progress']})
                else:
                    r=n['relation'];rel=r.get('schemaname','public')+'.'+r['relname'];t=tables[rel]
                    old=metadata.get(rel);constraints=[]
                    for col,v in t['columns'].items():constraints.extend({'column':col,'ast':c} for c in v.get('constraints',[]))
                    constraints.extend({'column':None,'ast':c} for c in t.get('constraints',[]))
                    trigger_edges=[e for e in graph['edges'] if e['caller']==sig and e['kind']=='IMPLICIT_TRIGGER' and e['target_relation']==rel]
                    opts={x['DefElem']['defname']:x['DefElem'].get('arg') for x in f['original_definition']['options']}
                    item.update({'target_relation':rel,'target_declaration':t['provenance'],'effective_columns':t['columns'],
                        'constraint_asts':constraints,'previous_target_metadata':old,'source_trigger_candidates':trigger_edges,
                        'security_options_ast':opts,'on_conflict':n.get('onConflictClause'),'where_grouped_ast':n.get('whereClause'),
                        'set_or_insert_targets':n.get('targetList',n.get('cols')),'returning_ast':n.get('returningClause',n.get('returningList')),
                        'found_observations_after_statement':[{'kind':k,'ast_path':list(pp),'query':v['query']} for k,v,pp in walk(following) if k=='PLpgSQL_expr' and 'found' in v['query'].lower()],
                        'zero_row_behavior':'INSERT VALUES proposes one row before triggers/conflict; zero rows possible with DO NOTHING or trigger suppression; error branches separate' if kind=='InsertStmt' else 'Zero matched rows are ordinary DML completion; FOUND/ROW_COUNT/error controls must establish required transition',
                        'multirow_behavior':'INSERT source cardinality, trigger return and conflict branch need exact path proof' if kind=='InsertStmt' else 'Exact unique-key equality/nullability required to bound update cardinality; static declaration alone is insufficient',
                        'remaining':['Complete grouped predicate and CAS proof','Zero/multiple row acceptance and exception propagation','Event-specific trigger transition proof','Defaults/generated/FK/unique/check/NOT NULL and RLS/catalog corroboration']})
                rows.append(item)
    dump('EXPANDED-DML-DEPENDENCIES.json',rows)
    summary={'REACHABLE_WRITE_STATEMENT_N':sum(x['kind']!='LockingClause' for x in rows),'REACHABLE_ROW_LOCK_CLAUSE_N':sum(x['kind']=='LockingClause' for x in rows),
        'REACHABLE_DML_AND_LOCK_N':len(rows),'DML_COMPLETE_N':0,'DML_INCOMPLETE_N':len(rows),'write_kind_counts':dict(collections.Counter(x['kind'] for x in rows)),
        'denominator_is_diagnostic_not_semantic':True,'runtime_execution':False}
    dump('EXPANDED-DML-STATUS.json',summary);print(json.dumps(summary))
if __name__=='__main__':main()
