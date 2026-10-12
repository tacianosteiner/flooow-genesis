"""Scope-aware frozen-source identifier rebinding; abstains on ambiguity.

This proves structural field/type bindings, not runtime catalog or authority.
Branch-sensitive record dominance and implicit effects remain explicit gaps.
"""
from pathlib import Path
import collections,json,hashlib,re
from catalog_metadata import records as dat_records
from source_binding import read,walk,strings,BASE,ROOT,OUT

RESULT=BASE/'continuation-03'
INDEX=read(OUT/'SOURCE-DECLARATION-INDEX.json')
TABLES=read(OUT/'EFFECTIVE-TABLE-CATALOG.json')
CATALOG=INDEX['catalog']
BYNAME=collections.defaultdict(list)
for sig,f in CATALOG.items():BYNAME[f['name']].append(f)
BUILTINS=collections.defaultdict(list)
for record in dat_records((OUT/'pg18.4/pg_proc.dat').read_text()):
    if record.get('proname'):BUILTINS[record['proname']].append(record)
ARRAY_NAMES={'_'+t['typname']:t['typname']+'[]' for t in dat_records((OUT/'pg18.4/pg_type.dat').read_text()) if t.get('array_type_oid')}
IMPLICIT={(c['castsource'],c['casttarget']) for c in dat_records((OUT/'pg18.4/pg_cast.dat').read_text()) if c.get('castcontext')=='i'}
PREFERRED={t['typname'] for t in dat_records((OUT/'pg18.4/pg_type.dat').read_text()) if t.get('typispreferred')=='t'}
# Source declarations, never pg_authid data. Sensitive role fields are omitted.
ctype={'Oid':'oid','NameData':'name','bool':'bool','int16':'int2','int32':'int4','int64':'int8','char':'char','text':'text','aclitem':'aclitem','oidvector':'oidvector','int2vector':'int2vector','TransactionId':'xid','TimestampTz':'timestamptz','float4':'float4'}
for header in (RESULT/'pg18.4').glob('*.h'):
    text=header.read_text();table=header.stem
    declarations=re.findall(r'^\s*(\w+)\s+(\w+)(\[[^]]*\])?\s*(?:BKI_[^;]+)?;',text,re.M)
    cols={name:{'type':ctype[t]+('[]' if array else '')} for t,name,array in declarations if t in ctype}
    TABLES['pg_catalog.'+table]={'columns':cols}
TABLES['pg_catalog.pg_roles']={'columns':{k:{'type':v} for k,v in {'oid':'oid','rolname':'name','rolsuper':'bool','rolinherit':'bool','rolcreaterole':'bool','rolcreatedb':'bool','rolcanlogin':'bool','rolreplication':'bool','rolbypassrls':'bool','rolconnlimit':'int4','rolvaliduntil':'timestamptz','rolconfig':'text[]'}.items()}}
if (RESULT/'FLYWAY-SOURCE.json').exists():
    info=read(RESULT/'FLYWAY-SOURCE.json');data=(RESULT/'FLYWAY-PG13.2.0-SOURCE.java.reference.txt').read_bytes()
    assert hashlib.sha256(data).hexdigest()==info['sha256']
    TABLES['public.flyway_schema_history']={'columns':{k:{'type':v} for k,v in {'installed_rank':'int4','version':'varchar','description':'varchar','type':'varchar','script':'varchar','checksum':'int4','installed_by':'varchar','installed_on':'timestamp','execution_time':'int4','success':'bool'}.items()}}

def common(values):
    types=[v for v in values if v not in ['unknown_literal','NULL_LITERAL']]
    if not types:return 'unknown_literal'
    if 'UNRESOLVED' in types:return 'UNRESOLVED'
    def casts(a,b):
        return a==b or (a,b) in IMPLICIT or a.endswith('[]') and b.endswith('[]') and (a[:-2],b[:-2]) in IMPLICIT
    candidate=types[0]
    for t in types[1:]:
        if candidate!=t and candidate not in PREFERRED and casts(candidate,t) and not casts(t,candidate):candidate=t
    return candidate if all(casts(t,candidate) for t in types) else 'UNRESOLVED'

class Resolver:
    def __init__(self,f):
        self.f=f;self.vars=dict(zip(f['parameter_names'],f['parameter_types']));self.vars.update({'$'+str(i+1):t for i,t in enumerate(f['parameter_types'])})
        self.vars.update({'found':'bool','FOUND':'bool'})
        self.records={};self.pending=[];self.record_defs=collections.defaultdict(list);self.use_path=()
        for n,t in list(self.vars.items()):
            rel=t if '.' in t else 'public.'+t
            if rel in TABLES:self.records[n]={k:v['type'] for k,v in TABLES[rel]['columns'].items()}
        for datum in (f.get('plpgsql_ast') or {}).get('datums',[]):
            v=datum.get('PLpgSQL_var')
            if v:self.vars[v['refname']]=v.get('datatype',{}).get('PLpgSQL_type',{}).get('typname','UNRESOLVED').removeprefix('pg_catalog.')
        self.vars={n:ARRAY_NAMES.get(t,t) for n,t in self.vars.items()}
        for n,t in self.vars.items():
            rowtype=t[:-8] if t.lower().endswith('%rowtype') else t
            rel=rowtype if '.' in rowtype else 'public.'+rowtype
            if rel in TABLES:self.records[n]={k:v['type'] for k,v in TABLES[rel]['columns'].items()}
        for normalization in f.get('analysis_normalizations',[]):
            self.records[normalization['record_name']]=normalization['original_column_types']
    def column(self,fields,scopes):
        if not fields:return ('UNRESOLVED','EMPTY_IDENTIFIER')
        if len(fields)>=3:
            rel='.'.join(fields[:-1]);t=TABLES.get(rel,{}).get('columns',{}).get(fields[-1],{}).get('type')
            return (t,'QUALIFIED_FROZEN_RELATION') if t else ('UNRESOLVED','QUALIFIED_RELATION_OR_FIELD_MISSING')
        if len(fields)==2:
            alias,col=fields
            for scope in reversed(scopes):
                if alias in scope['aliases']:
                    t=scope['aliases'][alias].get(col)
                    return (t,'LEXICALLY_SCOPED_RELATION_OUTPUT') if t and t!='UNRESOLVED' else ('UNRESOLVED','SCOPED_OUTPUT_MISSING_OR_AMBIGUOUS')
            t=self.records.get(alias,{}).get(col)
            if not t or t=='UNRESOLVED':
                dominating=[]
                for definition in self.record_defs.get(alias,[]):
                    path=definition['path'];positions=[i for i,x in enumerate(path) if isinstance(x,int)]
                    if definition['kind']=='PLpgSQL_stmt_fors':
                        prefix=path+('body',)
                        if tuple(self.use_path[:len(prefix)])==prefix:dominating.append((len(path),path[-2] if isinstance(path[-2],int) else -1,definition))
                    elif positions:
                        i=positions[-1];prefix=path[:i]
                        if tuple(self.use_path[:i])==prefix and len(self.use_path)>i and isinstance(self.use_path[i],int) and path[i]<self.use_path[i]:
                            dominating.append((len(prefix),path[i],definition))
                if dominating:
                    dominating.sort(key=lambda x:(x[0],x[1]));t=dominating[-1][2]['columns'].get(col)
                    if t and t!='UNRESOLVED':return t,'RECORD_FIELD_STRUCTURALLY_DOMINATING_ASSIGNMENT'
            return (t,'DECLARED_COMPOSITE_OR_RECORD_SHAPE') if t and t!='UNRESOLVED' else ('UNRESOLVED','RECORD_FIELD_SHAPE_OR_DOMINANCE_PENDING')
        col=fields[0];var=self.vars.get(col)
        for scope in reversed(scopes):
            options=[v[col] for v in scope['aliases'].values() if col in v]
            if options:
                if len(options)==1 and not var and options[0]!='UNRESOLVED':return options[0],'UNQUALIFIED_SINGLE_SCOPED_COLUMN'
                if self.f['language']=='sql' and len(options)==1:return options[0],'SQL_LANGUAGE_COLUMN_PRECEDENCE'
                return 'UNRESOLVED','COLUMN_OR_PL_VARIABLE_AMBIGUITY'
        if var and var!='UNRESOLVED':return var,'DECLARED_PARAMETER_OR_LOCAL'
        if col in self.records:return 'record','DECLARED_RECORD'
        for scope in reversed(scopes):
            if col in scope['aliases']:return 'record','WHOLE_ROW_ALIAS'
        return 'UNRESOLVED','IDENTIFIER_NOT_FOUND_IN_LEXICAL_SCOPE'
    def typ(self,node,scopes):
        if not isinstance(node,dict):return 'UNRESOLVED'
        if 'ColumnRef' in node:return self.column(strings(node['ColumnRef']['fields']),scopes)[0]
        if 'ParamRef' in node:return self.vars.get('$'+str(node['ParamRef']['number']),'UNRESOLVED')
        if 'TypeCast' in node:
            t=node['TypeCast']['typeName'];return '.'.join(strings(t['names'])).removeprefix('pg_catalog.')+('[]' if t.get('arrayBounds') else '')
        if 'A_Const' in node:
            v=node['A_Const'];return 'NULL_LITERAL' if v.get('isnull') else 'unknown_literal' if 'sval' in v else 'bool' if 'boolval' in v else 'int4' if 'ival' in v else 'numeric'
        if 'A_ArrayExpr' in node:
            t=common([self.typ(x,scopes) for x in node['A_ArrayExpr']['elements']]);return ('text' if t=='unknown_literal' else t)+'[]'
        if 'A_Indirection' in node:
            a=node['A_Indirection'];t=self.typ(a['arg'],scopes)
            indices=[x['A_Indices'] for x in a.get('indirection',[]) if 'A_Indices' in x]
            return t if any(x.get('is_slice') for x in indices) else t[:-2] if indices and t.endswith('[]') else 'UNRESOLVED'
        if any(k in node for k in ['BoolExpr','NullTest','BooleanTest']):return 'bool'
        if 'A_Expr' in node:
            a=node['A_Expr'];ops=strings(a.get('name',[]))
            if ops==['||']:
                t=common([self.typ(a.get('lexpr'),scopes),self.typ(a.get('rexpr'),scopes)])
                return 'text' if t=='unknown_literal' else t if t in ['text','bytea'] or t.endswith('[]') else 'UNRESOLVED'
            if ops and ops[0] in ['=','<>','<','>','<=','>=','~','!~','~~','!~~']:return 'bool'
            return common([self.typ(a.get('lexpr'),scopes),self.typ(a.get('rexpr'),scopes)])
        if 'CoalesceExpr' in node:return common([self.typ(x,scopes) for x in node['CoalesceExpr']['args']])
        if 'CaseExpr' in node:
            c=node['CaseExpr'];return common([self.typ(x['CaseWhen']['result'],scopes) for x in c.get('args',[])]+[self.typ(c.get('defresult'),scopes)])
        if 'SubLink' in node:
            s=node['SubLink']
            return 'bool' if s['subLinkType']=='EXISTS_SUBLINK' else next(iter(self.select(s['subselect'].get('SelectStmt',{}),scopes).values()),'UNRESOLVED')
        if 'FuncCall' in node:
            c=node['FuncCall'];n='.'.join(strings(c['funcname']));name=n if '.' in n else 'public.'+n
            args=[self.typ(x,scopes) for x in c.get('args',[])];f=[x for x in BYNAME.get(name,[]) if len(x['parameters'])==len(args)]
            if len(f)==1:return f[0]['return_type']
            short=n.removeprefix('pg_catalog.')
            returns={'count':'int8','cardinality':'int4','num_nonnulls':'int4','get_byte':'int4','octet_length':'int4','array_position':'int4','sha256':'bytea','uuid_send':'bytea','int8send':'bytea','int4send':'bytea','decode':'bytea','convert_to':'bytea','encode':'text','btrim':'text','to_char':'text','left':'text','right':'text','substring':'text','split_part':'text','replace':'text','convert_from':'text','clock_timestamp':'timestamptz','transaction_timestamp':'timestamptz','current_database':'name','current_setting':'text','bool_and':'bool','bool_or':'bool','isfinite':'bool'}
            if short=='substring' and args and args[0]=='bytea':return 'bytea'
            if short in returns:return returns[short]
            if short in ['min','max','trunc']:return args[0] if args else 'UNRESOLVED'
            return 'UNRESOLVED'
        return 'UNRESOLVED'
    def from_item(self,node,scope,outer):
        if 'RangeVar' in node:
            r=node['RangeVar'];schema=r.get('schemaname') or ('pg_catalog' if 'pg_catalog.'+r['relname'] in TABLES else 'public');rel=schema+'.'+r['relname'];alias=r.get('alias',{}).get('aliasname',r['relname'])
            cols=scope['ctes'].get(r['relname']) if not r.get('schemaname') and r['relname'] in scope['ctes'] else {k:v['type'] for k,v in TABLES.get(rel,{}).get('columns',{}).items()}
            scope['aliases'][alias]=cols or {}
        elif 'JoinExpr' in node:
            j=node['JoinExpr'];self.from_item(j['larg'],scope,outer);self.from_item(j['rarg'],scope,outer)
        elif 'RangeSubselect' in node:
            r=node['RangeSubselect'];sc=outer+[scope] if r.get('lateral') else outer
            cols=self.select(r['subquery'].get('SelectStmt',{}),sc)
            names=strings(r.get('alias',{}).get('colnames',[]))
            if names:
                vals=list(cols.values());cols={n:vals[i] if i<len(vals) else 'UNRESOLVED' for i,n in enumerate(names)}
            if r.get('alias'):scope['aliases'][r['alias']['aliasname']]=cols
        elif 'RangeFunction' in node:
            r=node['RangeFunction'];cols={};default_alias=None;ordered=None
            for fn in r.get('functions',[]):
                for kind,call,_ in walk(fn):
                    if kind!='FuncCall':continue
                    name='.'.join(strings(call['funcname']));name=name if '.' in name else 'public.'+name
                    default_alias=name.split('.')[-1]
                    options=[x for x in BYNAME.get(name,[]) if len(x['parameters'])==len(call.get('args',[]))]
                    if len(options)==1:cols.update(options[0]['output_fields'])
                    short=default_alias
                    if short=='unnest' and len(call.get('args',[]))==1:
                        t=self.typ(call['args'][0],outer+[scope]);elem=t[:-2] if t.endswith('[]') else 'UNRESOLVED'
                        cols={'unnest':elem};ordered=['unnest']
                        if r.get('ordinality'):cols['ordinality']='int8';ordered.append('ordinality')
                    elif short in BUILTINS:
                        opts=[x for x in BUILTINS[short] if x.get('proallargtypes') and x.get('proargnames')]
                        if len(opts)==1:
                            meta=opts[0];types=meta['proallargtypes'].strip('{}').split(',');modes=meta.get('proargmodes','').strip('{}').split(',');names=meta['proargnames'].strip('{}').split(',')
                            cols={n:t for n,t,m in zip(names,types,modes) if m in ['o','b','t']};ordered=[n for n,m in zip(names,modes) if m in ['o','b','t']]
            alias=r.get('alias',{});rename=strings(alias.get('colnames',[]))
            if rename:
                cols={n:cols[ordered[i]] if ordered and i<len(ordered) else 'UNRESOLVED' for i,n in enumerate(rename)}
            if alias or default_alias:scope['aliases'][alias.get('aliasname',default_alias)]=cols
    def scope(self,s,outer):
        scope={'aliases':{},'ctes':dict(outer[-1]['ctes']) if outer else {}}
        for item in s.get('withClause',{}).get('ctes',[]):
            c=item['CommonTableExpr'];query=c['ctequery'].get('SelectStmt',{})
            cols=self.select(query,outer+[scope]);names=strings(c.get('aliascolnames',[]))
            if names:
                vals=list(cols.values());cols={n:vals[i] if i<len(vals) else 'UNRESOLVED' for i,n in enumerate(names)}
            scope['ctes'][c['ctename']]=cols
            if s.get('withClause',{}).get('recursive'):
                cols=self.select(query,outer+[scope])
                if names:
                    vals=list(cols.values());cols={n:vals[i] if i<len(vals) else 'UNRESOLVED' for i,n in enumerate(names)}
                scope['ctes'][c['ctename']]=cols
        for node in s.get('fromClause',[]):self.from_item(node,scope,outer)
        return scope
    def select(self,s,outer):
        scope=self.scope(s,outer);result={}
        if s.get('valuesLists'):
            rows=[x.get('List',{}).get('items',[]) for x in s['valuesLists']]
            if rows:
                for i in range(len(rows[0])):
                    t=common([self.typ(row[i],outer+[scope]) for row in rows]);result['column'+str(i+1)]='text' if t=='unknown_literal' else t
            return result
        if s.get('larg') and s.get('rarg'):
            left=self.select(s['larg'],outer);right=self.select(s['rarg'],outer)
            if len(left)==len(right):return {k:common([v,w]) for (k,v),w in zip(left.items(),right.values())}
        for wrapped in s.get('targetList',[]):
            t=wrapped['ResTarget'];v=t.get('val',{});refs=strings(v.get('ColumnRef',{}).get('fields',[]))
            cast_refs=strings(v.get('TypeCast',{}).get('arg',{}).get('ColumnRef',{}).get('fields',[]))
            fn_names=strings(v.get('FuncCall',{}).get('funcname',[]))
            name=t.get('name') or (refs[-1] if refs else cast_refs[-1] if cast_refs else fn_names[-1] if fn_names else '?column?')
            if any('A_Star' in x for x in v.get('ColumnRef',{}).get('fields',[])):
                aliases=[scope['aliases'].get(refs[0],{})] if refs else scope['aliases'].values()
                result.update({k:v for a in aliases for k,v in a.items()});continue
            if name:result[name]=self.typ(v,outer+[scope])
        return result
    def discover_records(self,statements):
        # Shape inference is distinct from control-flow dominance. If a record
        # receives incompatible shapes, don't pick whichever assignment is last.
        by_query=collections.defaultdict(list);shapes=collections.defaultdict(list)
        for s in statements:by_query[s['query']].append(s)
        for kind,node,path in walk((self.f.get('plpgsql_ast') or {}).get('action',{})):
            if kind not in ['PLpgSQL_stmt_execsql','PLpgSQL_stmt_fors']:continue
            target_node=node.get('target',node.get('var',{}));target=target_node.get('PLpgSQL_rec')
            row=target_node.get('PLpgSQL_row',{})
            if not target and len(row.get('fields',[]))==1:
                name=row['fields'][0]['name']
                if self.vars.get(name) in ['record','pg_catalog.record']:target={'refname':name}
            expr=node.get('sqlstmt',node.get('query',{})).get('PLpgSQL_expr',{})
            if not target or expr.get('query') not in by_query:continue
            matches=[s for s in by_query[expr['query']] if tuple(self.f['expressions'][int(s['SQL_STATEMENT_ID'].rsplit(':S',1)[1])]['ast_path'])==path+('sqlstmt' if kind=='PLpgSQL_stmt_execsql' else 'query',)]
            if len(matches)!=1:continue
            self.use_path=path+('sqlstmt' if kind=='PLpgSQL_stmt_execsql' else 'query',)
            ast=matches[0]['ast'];s=ast['stmts'][0]['stmt'].get('SelectStmt',{})
            if len(s.get('targetList',[]))==1:
                v=s['targetList'][0]['ResTarget'].get('val',{}).get('ColumnRef',{})
                if any('A_Star' in x for x in v.get('fields',[])):
                    scope=self.scope(s,[]);cols={k:v for alias in scope['aliases'].values() for k,v in alias.items()}
                else:cols=self.select(s,[])
            else:cols=self.select(s,[])
            if cols:
                shapes[target['refname']].append(cols)
                self.record_defs[target['refname']].append({'path':path,'columns':cols,'kind':kind,'statement_id':matches[0]['SQL_STATEMENT_ID']})
        for name,possibilities in shapes.items():
            keys=set().union(*(p.keys() for p in possibilities));merged={}
            for key in keys:
                vals={p.get(key,'UNRESOLVED') for p in possibilities};merged[key]=next(iter(vals)) if len(vals)==1 else 'UNRESOLVED'
            # Keep shape disagreement for diagnostics, but use-site dominance
            # chooses only an assignment that necessarily precedes this path.
            if name not in self.records:self.records[name]={}
    def references(self,node,scopes,path=()):
        if not isinstance(node,(dict,list)):return
        if isinstance(node,list):
            for i,v in enumerate(node):yield from self.references(v,scopes,path+(i,))
            return
        if 'SelectStmt' in node:
            s=node['SelectStmt'];scope=self.scope(s,scopes)
            for k,v in s.items():
                if k in ['larg','rarg'] and isinstance(v,dict):
                    yield from self.references({'SelectStmt':v},scopes+[scope],path+('SelectStmt',k))
                else:yield from self.references(v,scopes+[scope],path+('SelectStmt',k))
            return
        for dml_kind in ['UpdateStmt','InsertStmt','DeleteStmt']:
            if dml_kind in node:
                s=node[dml_kind];scope={'aliases':{},'ctes':{}}
                if s.get('relation'):self.from_item({'RangeVar':s['relation']},scope,scopes)
                for from_node in s.get('fromClause',s.get('usingClause',[])):self.from_item(from_node,scope,scopes)
                for k,v in s.items():
                    # INSERT VALUES/SELECT cannot read the target columns as a
                    # FROM namespace. They may bind PL variables of same names.
                    namespace=scopes if dml_kind=='InsertStmt' and k=='selectStmt' else scopes+[scope]
                    yield from self.references(v,namespace,path+(dml_kind,k))
                return
        if 'ColumnRef' in node:
            if any('A_Star' in x for x in node['ColumnRef']['fields']):
                return  # expansion syntax is not an identifier with a scalar type
            fields=strings(node['ColumnRef']['fields']);typ,origin=self.column(fields,scopes)
            yield {'path':list(path+('ColumnRef',)),'reference':fields,'type':typ,'binding_origin':origin,
                   'status':'PROVEN_SOURCE_FIELD_TYPE' if typ!='UNRESOLVED' else 'REAL_UNRESOLVED_GAP',
                   'record_dominance':'STRUCTURAL_DOMINANCE_SOURCE_PROOF' if origin=='RECORD_FIELD_STRUCTURALLY_DOMINATING_ASSIGNMENT' else 'NOT_PROVEN_BY_THIS_RECORD_ASSIGNMENT' if fields and fields[0] in self.record_defs else 'NOT_DYNAMIC_RECORD_SHAPE'}
            return
        for k,v in node.items():yield from self.references(v,scopes,path+(k,))

def main():
    RESULT.mkdir(exist_ok=True)
    old=ROOT/'docs/evidence/package-0090-g3f4-authority-boundary-typed';reachable=set(read(BASE/'CASE-REACHABILITY-CANDIDATES.json')['candidate_functions'])
    functions={read(p)['signature']:read(p) for p in (old/'functions').glob('*.json') if read(p)['signature'] in reachable}
    grouped=collections.defaultdict(list)
    for ref in sorted((old/'final-03/statements').glob('*.reference.json')):
        r=read(ref);data=(ROOT/r['artifact']).read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
        for s in json.loads(data):
            if s['SQL_OBJECT'] in functions:grouped[s['SQL_OBJECT']].append(s)
    records=[];totals=collections.Counter()
    for sig,f in functions.items():
        resolver=Resolver(f);resolver.discover_records(grouped[sig])
        for s in grouped[sig]:
            resolver.use_path=tuple(f['expressions'][int(s['SQL_STATEMENT_ID'].rsplit(':S',1)[1])]['ast_path'])
            for record in resolver.references(s['ast'],[]):
                totals[record['status']]+=1
                records.append({'statement_id':s['SQL_STATEMENT_ID'],'object':sig,**record})
    (RESULT/'IDENTIFIER-BINDINGS.json').write_text(json.dumps(records,separators=(',',':'),sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    summary={'diagnostic_occurrence_n':len(records),'source_field_type_resolved_n':totals['PROVEN_SOURCE_FIELD_TYPE'],'source_field_type_unresolved_n':totals['REAL_UNRESOLVED_GAP'],
             'runtime_catalog_verified':False,'execution_relevant_denominator':'UNKNOWN','dynamic_record_dominance_complete':False,
             'proof_boundary':'Structural frozen-source fields/types only. Polymorphic/operator/catalog and control-flow use-site proof remain separate.',
             'unresolved_reason_counts':dict(collections.Counter(x['binding_origin'] for x in records if x['status']=='REAL_UNRESOLVED_GAP'))}
    (RESULT/'IDENTIFIER-SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');print(json.dumps(summary))

if __name__=='__main__':main()
