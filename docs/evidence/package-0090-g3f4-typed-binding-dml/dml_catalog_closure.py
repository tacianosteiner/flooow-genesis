"""Expand frozen DML implicit declarations; source proof != runtime proof."""
from pathlib import Path
import json, collections, hashlib
from source_binding import read, dump, OUT, BASE, ROOT, walk, strings, typename

def order(p):
    return (int(Path(p['SOURCE_FILE']).name.split('__')[0][1:]),p['SOURCE_STATEMENT_ORDINAL'])

def main():
    index=read(OUT/'SOURCE-DECLARATION-INDEX.json')
    tables=json.loads(json.dumps(index['tables']))
    for name,t in tables.items():
        for change in t['alterations']:
            for wrapped in change['ast']['cmds']:
                cmd=wrapped['AlterTableCmd'];op=cmd['subtype']
                if op=='AT_AddConstraint':t['constraints'].append(cmd['def'])
                elif op=='AT_DropConstraint':t['constraints']=[c for c in t['constraints'] if c['Constraint'].get('conname')!=cmd['name']]
                elif op=='AT_AddColumn':
                    c=cmd['def']['ColumnDef'];t['columns'][c['colname']]={'type':typename(c['typeName']),'constraints':c.get('constraints',[]),'generated':c.get('generated'),'identity':c.get('identity'),'raw_default':c.get('raw_default'),'provenance':change['provenance']}
                elif op=='AT_ChangeOwner':t['owner_ast']=cmd.get('newowner')
                else:raise ValueError('Unmodeled frozen table alteration '+op)
    triggers={};indexes={}
    for entry in sorted(index['implicit_ddl'],key=lambda x:order(x['provenance'])):
        tr=entry['ast'].get('CreateTrigStmt')
        if tr:
            name=tr['relation'].get('schemaname','public')+'.'+tr['relation']['relname']
            triggers[(name,tr['trigname'])]=entry
        ix=entry['ast'].get('IndexStmt')
        if ix:
            rel=ix['relation'];name=rel.get('schemaname','public')+'.'+rel['relname']
            indexes[(name,ix.get('idxname','SOURCE_ORDINAL_'+str(entry['provenance']['SOURCE_STATEMENT_ORDINAL'])))] = entry
        drop=entry['ast'].get('DropStmt')
        if drop and drop['removeType']=='OBJECT_TRIGGER':
            for obj in drop['objects']:
                names=strings(obj['List']['items']);rel='.'.join(names[:-1]);rel=rel if '.' in rel else 'public.'+rel
                triggers.pop((rel,names[-1]),None)
        if drop and drop['removeType']=='OBJECT_INDEX':
            for obj in drop['objects']:
                names=strings(obj['List']['items']);idxname=names[-1]
                indexes={k:v for k,v in indexes.items() if k[1]!=idxname}
    old=ROOT/'docs/evidence/package-0090-g3f4-authority-boundary-typed'
    funcs={read(p)['signature']:read(p) for p in (old/'functions').glob('*.json')}
    inventory=read(BASE/'semantic-checkpoint/DML-DEPENDENCY-GRAPH.json');expanded=[]
    for item in inventory:
        r=item['TARGET_RELATION'];name=(r.get('schema','')+'.'+r.get('relation','')) if r.get('relation') else None
        if item['KIND']=='LockingClause':
            expanded.append({**item,'classification':'REAL_UNRESOLVED_GAP','smallest_missing_fact':'Bind locking-clause alias targets to exact scoped FROM relations and row identity; validate effective locking strategy.',
                             'source_metadata_complete':False,'dml_semantics_complete':False})
            continue
        if name not in tables:raise ValueError('DML target missing frozen table declaration: '+str(name))
        t=tables[name];all_constraints=[]
        for col,value in t['columns'].items():
            all_constraints.extend({'column':col,'ast':c,'source':value.get('provenance',t['provenance'])} for c in value['constraints'])
        for c in t['constraints']:
            origins=[a['provenance'] for a in t['alterations'] for cmd in a['ast']['cmds']
                     if cmd['AlterTableCmd'].get('def')==c and cmd['AlterTableCmd']['subtype']=='AT_AddConstraint']
            all_constraints.append({'column':None,'ast':c,'source':origins[-1] if origins else t['provenance']})
        fk=[]
        for c in all_constraints:
            q=c['ast']['Constraint']
            if q['contype']=='CONSTR_FOREIGN':
                rel=q['pktable'];target=rel.get('schemaname','public')+'.'+rel['relname']
                fk.append({'referenced_relation':target,'column_map_ast':q,'referenced_declaration':tables.get(target,{}).get('provenance'),
                           'semantics':'Enforce declared key/match/deferrability/action; NULL and trigger/FK checks are not WHERE-only semantics.'})
        relevant=[];nonfiring=[]
        for (rel,trigname),entry in triggers.items():
            if rel!=name:continue
            tr=entry['ast']['CreateTrigStmt'];call='.'.join(strings(tr['funcname']));call=call if '.' in call else 'public.'+call
            f=[(s,v) for s,v in index['catalog'].items() if v['name']==call]
            event=4 if item['KIND']=='InsertStmt' else 16 if item['KIND']=='UpdateStmt' else 8
            # INSERT ... ON CONFLICT may execute UPDATE triggers; don't erase
            # those dependencies when a conflict branch is retained.
            possible_events=event | (16 if (item.get('ON_CONFLICT_AST') or {}).get('action')=='ONCONFLICT_UPDATE' else 0)
            if not tr['events'] & possible_events:
                nonfiring.append({'name':trigname,'classification':'PROVEN_OUT_OF_SCOPE_FOR_THIS_DML_EVENT','events':tr['events'],'source':entry['provenance']})
                continue
            relevant.append({'name':trigname,'trigger_ast':tr,'source':entry['provenance'],'function_candidates':[s for s,v in f],
                             'function_source_provenances':[v['provenance'] for s,v in f], 'body_control_flow_complete':False})
        caller=index['catalog'][item['PROVENANCE']['SOURCE_OBJECT']]
        idx=item['PROVENANCE']['STATEMENT_ORDINAL'];cached=funcs[item['PROVENANCE']['SOURCE_OBJECT']]
        expression=cached['expressions'][idx]
        expected='UNRESOLVED_REQUIRES_FOLLOWING_FOUND_OR_ROW_COUNT_CONTROL_FLOW'
        provenances={'create_table':t['provenance'],'alterations':[x['provenance'] for x in t['alterations']], 'caller':caller['provenance']}
        expanded.append({**item,'target_declaration':t['provenance'],'effective_columns':t['columns'],'explicit_constraint_metadata':all_constraints,
                         'foreign_key_dependencies':fk,'trigger_dependencies':relevant,'original_security_definer':caller['security_definer'],
                         'nonfiring_triggers_by_event':nonfiring,'unique_index_dependencies':[v for (rel,_),v in indexes.items() if rel==name and v['ast']['IndexStmt'].get('unique')],
                         'original_search_path_ast':caller['search_path_ast'],'caller_control_context':expression['context'],
                         'caller_control_ast_path':expression['ast_path'],
                         'source_provenances':provenances,'rls_source_declarations':'NONE_IN_INDEXED_FROZEN_DDL; actual disposable catalog must later corroborate',
                         'generated_and_default_sources':'EXACT_COLUMN_CONSTRAINT_AST_RETAINED; functions/sequences expand through those ASTs',
                         'expected_rowcount':expected,'source_metadata_complete':True,'dml_semantics_complete':False,
                         'classification':'REAL_UNRESOLVED_GAP',
                         'smallest_missing_fact':'Resolve grouped predicate/SET/RETURNING bindings, trigger control-flow and rowcount/CAS/exception effects on the concrete path.'})
    dump('DML-CATALOG-EXPANSION.json',{'diagnostic_sites_n':len(expanded),'write_statement_n':sum(x['KIND']!='LockingClause' for x in expanded),
                                     'row_lock_clause_n':sum(x['KIND']=='LockingClause' for x in expanded),
                                     'write_metadata_source_complete_n':sum(x.get('source_metadata_complete',False) for x in expanded),
                                     'full_dml_semantics_complete_n':0,'sites':expanded,
                                     'proof_boundary':'Frozen source-declaration proof only; no live catalog or positive SQL execution.'})
    dump('EFFECTIVE-TABLE-CATALOG.json',tables)
    print('DML_SOURCE_METADATA=26_WRITES; ROW_LOCK_SCOPE=105_OPEN; FULL_DML_SEMANTICS=HOLD')

if __name__=='__main__':main()
