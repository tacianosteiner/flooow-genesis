"""Deterministic exact-source comparison ledger; explicitly not a PL/pgSQL AST proof."""
from pathlib import Path
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
SUCCESSOR='6ad78ba61d70e803d2a878034aa7988b69b6374568f96949b2ef6c8defc7a8c7'
def digest(b):return hashlib.sha256(b).hexdigest()
def masked(sql):
    # Preserve offsets. Comments/quoted literals cannot introduce comparisons.
    result=list(sql);i=0;depth=0
    while i<len(sql):
        start=i
        if sql.startswith('--',i):
            end=sql.find('\n',i);end=len(sql) if end<0 else end
        elif sql.startswith('/*',i):
            depth=1;end=i+2
            while depth and end<len(sql):
                if sql.startswith('/*',end):depth+=1;end+=2
                elif sql.startswith('*/',end):depth-=1;end+=2
                else:end+=1
            if depth:raise ValueError('Unclosed SQL comment')
        elif sql[i] in "'\"":
            quote=sql[i];end=i+1
            while end<len(sql):
                if sql[end]==quote:
                    if end+1<len(sql) and sql[end+1]==quote:end+=2;continue
                    end+=1;break
                end+=1
            else:raise ValueError('Unclosed quoted SQL token')
        else:i+=1;continue
        for p in range(start,end):
            if sql[p]!='\n':result[p]=' '
        i=end
    return ''.join(result)
def extract():
    p=ROOT/'docs/evidence/package-0090-g3f4-hash-bound-successor/envelope-02/V043__TEST_ONLY_NONCANONICAL_executable_successor.sql';data=p.read_bytes();assert digest(data)==SUCCESSOR;sql=data.decode();view=masked(sql)
    definitions=list(re.finditer(r'CREATE FUNCTION\s+(public\.\w+)\s*\(',view));rows=[]
    comparison=re.compile(r'(?<![:<>!=])(?:<>|<=|>=|=|<|>)(?!=)|\bIS\s+(?:NOT\s+)?(?:NULL|TRUE|FALSE|DISTINCT\s+FROM)\b|\b(?:NOT\s+)?IN\s*\(',re.I)
    for match in comparison.finditer(view):
        start=view.rfind(';',0,match.start())+1;stop=view.find(';',match.end());stop=len(sql) if stop<0 else stop+1
        body=sql[start:stop];before=[m for m in definitions if m.start()<match.start()];wrapper=before[-1].group(1) if before else 'DDL_PREREQUISITE'
        if before:
            next_def=next((m.start() for m in definitions if m.start()>before[-1].start()),len(sql));scope=sql[before[-1].start():next_def]
        else:scope=sql[:definitions[0].start()] if definitions else sql
        left=re.search(r'([\w.$]+(?:::[\w.]+)?)\s*$',view[max(start,match.start()-256):match.start()]);right=re.match(r'\s*([\w.$]+(?:::[\w.]+)?)',view[match.end():min(stop,match.end()+256)])
        rows.append({'PREDICATE_ID':f'P{len(rows)+1:05d}','WRAPPER_NAME':wrapper,'SOURCE_RELATION':'UNRESOLVED_TYPED_ALIAS','SOURCE_COLUMN':left.group(1) if left else 'COMPOUND_EXPRESSION','TARGET_RELATION':'UNRESOLVED_PARAMETER_OR_ALIAS','TARGET_COLUMN':right.group(1) if right else 'COMPOUND_EXPRESSION','COMPARISON_OPERATOR':match.group(),'NULL_SEMANTICS':'SQL three-valued comparison; WHERE accepts TRUE only; IF executes TRUE branch only; NOT NULL/distinct operators require separate exact context','GENERATION_SEMANTICS':'UNVERIFIED_SOURCE_GUARD_CONTEXT','REVISION_SEMANTICS':'UNVERIFIED_SOURCE_GUARD_CONTEXT','STATUS_SEMANTICS':'UNVERIFIED_SOURCE_GUARD_CONTEXT','TIME_SEMANTICS':'UNVERIFIED_SOURCE_GUARD_CONTEXT','ORGANIZATION_SCOPE':'UNVERIFIED_SOURCE_GUARD_CONTEXT','DEPLOYMENT_SCOPE':'UNVERIFIED_SOURCE_GUARD_CONTEXT','INCARNATION_SCOPE':'UNVERIFIED_SOURCE_GUARD_CONTEXT','FAILURE_BEHAVIOR':'Exact containing statement and function must be independently mapped; no inferred denial','SQLSTATE_OR_DENIAL':'UNRESOLVED_NOT_INFERRED','SOURCE_FILE':p.relative_to(ROOT).as_posix(),'SOURCE_LINE_RANGE':[sql.count('\n',0,start)+1,sql.count('\n',0,stop)+1],'SUCCESSOR_HASH':SUCCESSOR,'EXACT_STATEMENT':body,'STATEMENT_SHA256':digest(body.encode()),'FUNCTION_SCOPE_SHA256':digest(scope.encode()),'comparison_character_offset':match.start(),'SEMANTICALLY_VERIFIED':False})
    # Exact body predicates manually scoped to known actual SQL relations.
    profiles=[('J01',r'r\.oid::pg_catalog\.int8\s*=\s*slot_oid','decoded_identity_slots','slot_oid','pg_catalog.pg_roles','oid'),('J02',r'r\.rolname\s*=\s*slot_name','decoded_identity_slots','slot_name','pg_catalog.pg_roles','rolname'),('J03',r'r\.deployment_id\s*=\s*header_record\.deployment_id','public.offline_readiness','deployment_id','public.offline_binding_header','deployment_id'),('J04',r'r\.incarnation_id\s*=\s*\$3','public.offline_readiness','incarnation_id','bound_expected_incarnation_argument','$3')]
    maps=[];used=set()
    for jid,pattern,sr,sc,tr,tc in profiles:
        found=[]
        for m in re.finditer(pattern,view):
            op=view.index('=',m.start(),m.end());row=next(r for r in rows if r['comparison_character_offset']==op)
            if not row['WRAPPER_NAME'].startswith('public.offline_'):continue
            row.update(SOURCE_RELATION=sr,SOURCE_COLUMN=sc,TARGET_RELATION=tr,TARGET_COLUMN=tc,COMPARISON_OPERATOR='=',NULL_SEMANTICS='Non-null required input/domain fields; exact equality TRUE required; nullable missing SELECT row denied by NOT FOUND/STRICT checks',GENERATION_SEMANTICS='Exact current identity/incarnation; this leaf does not independently prove all generation predicates',REVISION_SEMANTICS='No revision equality at this leaf; other revision guards remain mandatory',STATUS_SEMANTICS='Other status guards remain mandatory',TIME_SEMANTICS='Other clock/window/freshness guards remain mandatory',ORGANIZATION_SCOPE='Other organization guards remain mandatory',DEPLOYMENT_SCOPE='Exact actual deployment equality' if jid=='J03' else 'Other deployment guards remain mandatory',INCARNATION_SCOPE='Exact bound incarnation equality' if jid=='J04' else 'Other incarnation guards remain mandatory',FAILURE_BEHAVIOR='Identity/bound readiness guard denial; no eligibility inferred from leaf success',SQLSTATE_OR_DENIAL='P0017_ACCESS_DENIED_OR_STRICT_SELECT_FAILURE_AS_ACTUAL_SOURCE',SEMANTICALLY_VERIFIED=True)
            found.append(row['PREDICATE_ID']);used.add(row['PREDICATE_ID'])
        maps.append({'MODEL_JOIN_ID':jid,'SQL_PREDICATES':found,'status':'MATCHED_LEAF_ONLY' if found else 'UNMATCHED'})
    prior=json.loads((ROOT/'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/AUTHORITY-JOIN-GRAPH.json').read_text())
    for j in prior:
        if j['JOIN_ID'] in {m['MODEL_JOIN_ID'] for m in maps}:continue
        reason='Typed actual SQL alias/key/predicate correspondence not independently verified'
        if any(j[k] in ['allocation','enrollment_anchor','registry'] for k in ['SOURCE_RELATION','TARGET_RELATION']):reason='External native allocation/registry concept; no corresponding SQL relation in approved successor; cannot invent a SQL predicate'
        maps.append({'MODEL_JOIN_ID':j['JOIN_ID'],'SQL_PREDICATES':[],'status':'UNMATCHED','reason':reason,'model_join':j})
    metrics={'SQL_PREDICATE_TOTAL':len(rows),'MODEL_JOIN_TOTAL':len(prior),'MATCHED_PREDICATE_N':len(used),'UNMATCHED_SQL_PREDICATE_N':len(rows)-len(used),'UNMATCHED_MODEL_JOIN_N':sum(not m['SQL_PREDICATES'] for m in maps),'SEMANTIC_MISMATCH_N':sum('External native' in m.get('reason','') for m in maps),'SQL_PREDICATE_COVERAGE_COMPLETE':'NO','AUTHORITY_JOIN_GRAPH_COMPLETE':'NO','denominator':'All lexical comparison candidates from exact successor, including compound/DDL/PLpgSQL contexts. Not falsely represented as a complete typed AST semantic count.'}
    return {'metrics':metrics,'predicates':rows,'model_mapping':maps,'extractor_sha256':digest(Path(__file__).read_bytes())}
