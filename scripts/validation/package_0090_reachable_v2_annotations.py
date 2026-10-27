"""Explicit source successor mapping and per-node null/error/provider annotations."""
import json
import package_0090_source_closure as q
import package_0090_reachable_v2 as e
OUT=e.OUT

def prepare(r):
 corrected=(OUT/'S04-CORRECTED-FUNCTION.sql').read_bytes().rstrip(b'\n');old=(OUT.parent/'package-0090-s04-return-tuple-correction-candidate/S04-CURRENT-FUNCTION.sql').read_bytes().rstrip(b'\n');before=b'h.version,h.type,h.script';after=b'h.version::pg_catalog.text,h.type::pg_catalog.text,h.script::pg_catalog.text';q.require(old.replace(before,after)==corrected,'Source successor not exact correction')
 data=json.loads((OUT/'expression-site-v3.json').read_text());oldsites=json.loads((OUT.parent/'package-0090-full-reachable-expectation-closure/expression-site-denominator.json').read_text())['sites'];q.require([x['SITE_ID'] for x in data['sites']]==[x['SITE_ID'] for x in oldsites],'Site identity drift')
 nulls={'BoolExpr':'SQL three-valued AND/OR/NOT; a NULL IF condition is not TRUE; evaluation order is not an authorization guarantee','NullTest':'IS NULL/IS NOT NULL always returns a non-null boolean','A_Indirection':'Scalar array read with NULL/out-of-range index returns NULL; index arithmetic errors propagate','MinMaxExpr':'LEAST ignores NULL arguments, returns NULL only when all inputs are NULL; comparison uses the independently selected default btree family','SortBy':'Default ascending order with NULLS LAST; installed_rank source is NOT NULL; this node describes ordering rather than a scalar result transformation','SubLink':'EXISTS returns non-null boolean; membership query relation/columns are separate graph dependencies','SQLValueFunction':'SESSION_USER binds the authenticated session identity, not CURRENT_USER; role-lookup errors cannot yield a successful result','TypeCast':'Strict scalar casts preserve NULL; an explicitly typed empty ArrayExpr constructs a non-null empty array','A_Expr':'Strict scalar provider returns NULL for NULL operand; ANY additionally follows scalar-array SQL NULL/empty-array rules'}
 for site in data['sites']:
  a=site['analysis'];kind=site['EXPRESSION_KIND'];site['CONTROL_PATH']=site['SOURCE_LOCATION']['control_path'];site['EXPECTED_COLLATION']=dict(result_oid=a['collation_oid'],input_oid=a['input_collation_oid']);site['EXPECTED_ERROR_NULL_RELEVANCE']=dict(NULL_rule=nulls[kind],error_rule='Provider-defined ordinary errors are caught by the unchanged WHEN OTHERS and re-raised P0017; query_canceled/assert_failure are excluded by PostgreSQL and propagate without successful return',semantic_execution_proven=False)
  if a['provider_oid']:
   p=r.proc_by_oid[a['provider_oid']];site['EXPECTED_PROVIDER']=dict(kind='PG_CATALOG_FUNCTION',oid=p['oid'],name=p['proname'],declared_args=r.args(p),strict=p['proisstrict'])
  else:site['EXPECTED_PROVIDER']=dict(kind='EXACT_POSTGRES_INTRINSIC_NODE',node=a['mechanism'],provider_image=q.IMAGE)
  site['SOURCE_LOCATION'].update(canonical_function='public.offline_read_history(uuid,bytea,uuid,text)',query_sha256=r.statements[site['SOURCE_LOCATION']['statement_ordinal']]['query_sha256'])
 e.save('expression-site-v3.json',data)
 add=json.loads(e.ADD.read_text());contexts=json.loads((OUT/'function-reachability-v2.json').read_text())['call_contexts'];groups=[]
 for i,group in enumerate(add['candidate_contexts']):
  selected=[contexts[n] for n in group['site_indices']];q.require(len({x['analysis']['provider_oid'] for x in selected})==1,'Function group silently changes provider');groups.append(dict(GROUP_ID='S04-CALL-GROUP-%02d'%i,original_key=group['key'],source_site_indices=group['site_indices'],sites=selected,expected_resolved=True,semantic_status='UNBOUND'))
 q.require(len(groups)==33,'Function group denominator drift')
 e.save('function-context-groups-v2.json',dict(total=33,resolved=33,unresolved=0,groups=groups,polymorphic_instantiations_preserved=True,semantic_status='UNBOUND'))
 e.save('expression-successor-mapping.json',dict(previous_denominator=190,current_historical_denominator=190,old_S04_sha=q.sha(old),corrected_S04_sha=q.sha(corrected),mapping=[dict(SITE_ID=x['SITE_ID'],successor_SITE_ID=x['SITE_ID'],AST_semantics_changed=False) for x in data['sites']],separate_correction_edges=[dict(id='S04-RETURN-TEXT-'+name,source_column=name,target='pg_catalog.text',governance='PACKAGE0090/S04/return-tuple-correction/v1') for name in ['version','type','script']],changed_statement_ordinal=113,no_historical_reclassification=True))
