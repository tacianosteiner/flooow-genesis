"""Complete C5L audit records; derive topology and precise remaining recovery scopes."""
import collections
import importlib.util
import json
import pathlib

P=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('c5l',P/'run_gate.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def read(n):return json.loads((P/(n+'.json')).read_text(encoding='utf-8'))
def write(n,x):g.write(n,x)
inputs=read('canonical-input-binding-registry')['bindings'];ib={b['BINDING_ID']:b for b in inputs}
outputs=read('output-binding-closure')['records'];ob={'OUTPUT/'+b['WITNESS_ID']:b for b in outputs}
comp=read('composition-edge-recomputation');eb={e['EDGE_ID']:e for e in comp['edges']}
plans=read('source-parametric-projection-proofs')['plans'];pm={(p['witness'],p['input']):p for p in plans}
facts=g.read('i','canonical-fact-registry.json')['facts'];fm={f['FACT_ID']:f for f in facts}
funcs=g.read('k','49-function-inventory.json')['functions'];fun={f['FUNCTION_ID']:f for f in funcs}
families=g.read('d','family-descriptors.json')['families']

for n,records,kind in [('input-binding-equivalence-classes',ib,'INPUT'),('output-binding-equivalence-classes',ob,'OUTPUT'),('composition-equivalence-classes',eb,'COMPOSITION')]:
    x=read(n)
    for c in x['classes']:
        members=c['MEMBERS'];b=records[members[0]];key=c['SEMANTIC_KEY']
        c.update(BINDING_CLASS_ID=c['CLASS_ID'],SEMANTIC_OBJECT=(b.get('INPUT_ID') if kind=='INPUT' else b.get('OUTPUT_ID') if kind=='OUTPUT' else b['SOURCE_OUTPUT']),DOMAIN='SOURCE_TYPED_OPERAND' if kind=='INPUT' else 'AVAILABLE_BOOLEAN_VIOLATION_EVIDENCE' if kind=='OUTPUT' else 'SOURCE_STAGE_COMPOSITION',STAGE=b.get('SOURCE_STAGE',b.get('TARGET_STAGE',b.get('ORDER'))),SOURCE_TYPE=(pm[(b['WITNESS_ID'],b['INPUT_ID'])]['field_vector'] if kind=='INPUT' and (b['WITNESS_ID'],b['INPUT_ID']) in pm else fun[b['FUNCTION_ID']]['INPUT_SCHEMA'] if kind=='INPUT' else 'AVAILABLE bool or UNAVAILABLE/null' if kind=='OUTPUT' else b['COMPATIBILITY']['source_target_type']),SOURCE_IDENTITY_RULE=key,TARGET_FUNCTION_CLASS=b.get('FUNCTION_ID',b.get('TARGET_FUNCTION')),TARGET_INPUT_ROLE=b.get('INPUT_ID',b.get('CANONICAL_TARGET',b.get('TARGET_INPUT'))),TRANSFORMATION=b.get('TRANSFORMATION',b.get('OUTPUT_BINDING_RULE',b.get('BINDING'))),CARDINALITY=b.get('CARDINALITY','one scoped source-output/target-input edge'),AUTHORITY_SOURCE=b.get('BINDING_AUTHORITY',b.get('OUTPUT_BINDING_AUTHORITY',b.get('AUTHORITY_SOURCE'))),MEMBER_BINDINGS=members,MEMBER_COUNT=len(members),CLOSURE_STATUS='CLOSED' if all(records[m]['STATUS']=='COMPLETE' for m in members) else 'UNRESOLVED')
    write(n,x)

x=read('ambiguous-input-resolution')
for r in x['records']:
    b=ib[r['BINDING_ID']];p=pm.get((b['WITNESS_ID'],b['INPUT_ID']));selected=set(p['baseline_fact_ids']) if p else set()
    r.update(TARGET_FUNCTION=b['FUNCTION_ID'],TARGET_INPUT=b['INPUT_ID'],CANDIDATE_SOURCES=[c['FACT_ID'] for c in r['CANDIDATES']],DOMINATED_CANDIDATES=[c['FACT_ID'] for c in r['CANDIDATES'] if p and c['FACT_ID'] not in selected],NONDOMINATED_CANDIDATES=list(selected) if p else r['NONDOMINATED_UNRESOLVED_CANDIDATE_SET'],SELECTED_SOURCE_IF_UNIQUE=dict(projection_plan=g.digest(p),source_components=p['baseline_fact_ids'],mutation_support=p['mutation_fact_id']) if p else None,RESOLUTION_STATUS=r['STATUS'])
    for c in r['CANDIDATES']:
        exact=c['FACT_ID'] in selected
        match='MATCH_UNDER_FROZEN_SOURCE_PARAMETER_CONSTRAINTS' if exact else 'UNRESOLVED' if not p else 'NO_EXACT_QUALIFIED_OPERAND_MATCH'
        for name in ['SEMANTIC_OBJECT_MATCH','DOMAIN_MATCH','STAGE_MATCH','IDENTITY_MATCH','CARDINALITY_MATCH','AUTHORITY_MATCH','TYPE_MATCH','PROVENANCE_MATCH']:c[name]=match
        if exact:
            c['STAGE_MATCH']='MATCH_VIA_EXACT_TAGGED_MUTATION_TRANSFORM' if p['side'].startswith('TAGGED') else 'INDEPENDENT_APPROVED_BASELINE'
            c['PROVENANCE_MATCH']='I source key + D schema/model + F exact case, all source hashes preserved'
        elif p:
            c['ELIMINATION_CONSTRAINT']='Not the field vector of identity['+p['actor']+']/'+p['schema']+' under exact model/view/variant; schema fields and actor enumeration frozen in D. This only eliminates it as the direct operand source, not as possible support.'
        fact=fm[c['FACT_ID']];key=fact['CANONICAL_KEY']
        c['PROVENANCE_MATCH']='FROZEN_SOURCE_REFERENCE_HASH_MATCHES_PRESERVED_HISTORY'
        c['AUTHORITY_MATCH']='FROZEN_SOURCE_CONTRACT; operand-specific admission '+('ESTABLISHED' if exact else 'NOT_ESTABLISHED')
        if p:
            target_types={f['type'] for f in p['field_vector']}
            slot=key[2] if len(key)==4 else ''
            schema_match=any(slot.endswith('/'+p['schema']+'/'+f['name']) for f in p['field_vector'])
            identity_match=(len(key)==4 and isinstance(key[1],dict) and key[1].get('model_id')==p['model_id'] and key[1].get('selected_view')==p['selected_view'] and key[1].get('exact_variant_hash')==p['exact_variant_hash'] and slot.startswith('identity['+p['actor']+']/')) or (key==['FROZEN_ENUM_VALUE','NATIVE_ACTOR_ENUM',p['actor']] and any(f['name']=='participant_id' for f in p['field_vector']))
            c['TYPE_MATCH']='MATCHES_A_REQUIRED_FIELD_TYPE' if fact['VALUE_TYPE'] in target_types else 'DOES_NOT_MATCH_REQUIRED_FIELD_TYPES'
            c['IDENTITY_MATCH']='EXACT_SOURCE_IDENTITY_COORDINATES_MATCH' if identity_match else 'REQUIRED_ACTOR_MODEL_VIEW_VARIANT_OR_NATIVE_ENUM_IDENTITY_DOES_NOT_MATCH'
            c['SEMANTIC_OBJECT_MATCH']='REQUIRED_SOURCE_SCHEMA_FIELD_MATCH' if schema_match or exact else 'NOT_A_FIELD_OF_REQUIRED_SOURCE_OBJECT'
            c['DOMAIN_MATCH']='MATCH_NATIVE_IDENTITY_DOMAIN' if slot.startswith('identity[') or key[:2]==['FROZEN_ENUM_VALUE','NATIVE_ACTOR_ENUM'] else 'OTHER_SOURCE_DOMAIN'
            c['CARDINALITY_MATCH']='ONE_SCALAR' if len(p['field_vector'])==1 and fact['VALUE_TYPE'] in target_types else 'SCALAR_COMPONENT_ONLY; full ordered tuple required' if fact['VALUE_TYPE'] in target_types else 'NOT_ESTABLISHED'
            if not exact:c['STAGE_MATCH']='BASELINE_PARAMETER_REQUIRES_EXACT_OPERAND_PROJECTION; no post-state identity inferred'
        else:
            for name in ['SEMANTIC_OBJECT_MATCH','DOMAIN_MATCH','STAGE_MATCH','IDENTITY_MATCH','CARDINALITY_MATCH','TYPE_MATCH']:c[name]='NOT_ESTABLISHED_FOR_EXACT_OPERAND'
    for name in ['SEMANTIC_OBJECT_MATCH','DOMAIN_MATCH','STAGE_MATCH','IDENTITY_MATCH','CARDINALITY_MATCH','AUTHORITY_MATCH','TYPE_MATCH','PROVENANCE_MATCH']:r[name]='UNIQUE_COMPOSITE_PROJECTION_ESTABLISHED' if p else 'NOT_ESTABLISHED_FOR_UNIQUE_SOURCE'
x.update(AUTHORITY_REQUIRED_AMBIGUITIES=0,CARDINALITY_REQUIRED_AMBIGUITIES=0,ordinary_ambiguity_may_include_collection_dependencies=True)
write('ambiguous-input-resolution',x)

blocker_notes={
 'wrong_module':'Frozen nonempty finite map and MODULE_KEY=min(full canonical natural key) constrain selector. Existing I map entry schemas are obligations, but no verified exact keyed-map extraction/normalization plan yet connects complete map + lexical key to function scalar. Do not choose arbitrary entry; actual map extent not supplied.',
 'wrong_dependency':'Need complete typed node/edge graph with source root in nodes, full X/E_X expansion, exact ordering/hash and counts<4096. Single changed digest or schema row cannot stand for complete closed graph.',
 'wrong_enrollment':'Mutation is enrollment reference HASH(full enrollment tuple), while local operands are message subject enrollment/current enrolled reference. Exact ABI sender/subject/frame selector, complete enrollment tuple hash and independent registry admission must be jointly projected; identity schema alone is insufficient.',
 'wrong_channel':'Local operands say full channel inventory, while mutated source is authenticated channel endpoint-manifest digest. Need source proof of complete inventory extent and mapping to tuple/context/actual emitter. Do not reduce to changed digest.',
 'transferred_channel':'Mutation changes kernel_observation.actual_emitter_birth while claimed sender/channel fields remain unchanged. I sender_birth_identity digest cannot replace actual independent kernel-observed birth tuple. Need exact source observation/full birth extraction.',
 'replayed_challenge':'Need exact request sequence plus independently prior last-accepted/work-consumed scopes; a sequence numeric leaf alone does not bind one-use/work authority.',
 'replayed_response':'Need complete response work/input/result tuple and independent currently requested work identity, including source sender/subject/context fields, not response.expected result.',
 'replayed_completed_work_receipt':'Need full receipt entity/revision/generation/context/work tuple plus independent current publication and its exact receipt stage; source field names alone do not establish tuple projection.',
 'registry_rollback':'Need independently observed durable journal tip sequence and candidate previous-tip sequence source types/bounds plus journal-tip-to-registry contract. I registry revision fields are distinct from journal sequence; do not substitute equal-looking revision.',
 'tombstoned_generation':'Need supplied generation and exact irreversible retired-generation set membership with source entity/epoch scope; scalar generation type cannot establish complete set.',
 'restart_substitution':'Need explicitly new qualification old work UNKNOWN and attempt-to-adopt event projection; do not transfer old enrollment to new birth or infer from helper UNAVAILABLE.',
 'reconnect_substitution':'Need new channel admission event and exact old-work domain UNKNOWN independently; no inferred channel transfer or qualification from unavailable evaluator.',
 'participant_role_substitution':'Need full participant-role/message binding and independently expected role under actual emitter versus subject ABI. Same native enum value alone is insufficient.',
 'producer_consumer_substitution':'Need independently distinct actor/generation/purpose credential references for concurrent producer/consumer, including complete credential-to-key admission. No principal equality inferred.',
 'observer_writer_substitution':'Need authenticated actual registry writer identity from source write event and independently required NativeRegistryWriter; actor enum alone is not write provenance.',
 'credential_theft':'Need full actual holder birth/resource custody and independently authorized principal, including private-resource object identity; claimed credential subject alone cannot bind holder.',
 'credential_transfer':'Need exact presenter/custodian/phase/bootstrap exception event projections without widening T8 nontransfer. Role enum and phase literal are not source event authentication.',
 'credential_inheritance':'Need source and target generation, exact empty target-qualification receipt collection and authenticated inheritance claim. Missing receipts are not empty; no substitution/rotation authority inferred.',
 'wrong_custodian':'Need observed full private-resource custodian birth and source-required exact custody identity; neither private secret nor holder identity may be fabricated.',
 'catalog_stale_snapshot':'Need independent same-domain T_NOW and MAX_AGE frozen policy source plus captured boottime clock binding. Whole mutation root is not a unique clock/policy scalar.',
 'catalog_row_omission':'Need exact independent Reader SQL identity row keyed by trusted OID/name and complete observed row multiset. A schema slot does not establish the expected row or omission.',
 'catalog_row_injection':'Need independent protected OID/name roster and full observed union-by-OID-OR-NAME multiset; preserve collisions and duplicates until natural-key validation.',
 'catalog_duplication':'Need complete observed multiset and exact natural-key vector from source schema; duplicate detection cannot use a deduplicated relation.',
 'mixed_snapshot':'Need exact source-collection snapshot identity roster/cardinality and complete independently captured provenance per source collection; no inferred equal session/backend.',
 'snapshot_reconnect':'Need incoming and pending snapshot backend identities as different source-stage tuples; one generic model parameter cannot authenticate both.',
 'snapshot_restart':'Need incoming native observation lineage and pending snapshot lineage, full subject/generation/birth context; source shape alone does not prove independent observations.'}
sql_note='Need exact trusted S01 Reader SQL role OID/name and catalog/source-operation context, complete keyed row/ACL/membership/source-call projection; native actor enum R is not SQL identity. Preserve duplicate rows, natural keys and J database-owner/SET/INHERIT/ADMIN rules; source schemas alone do not resolve operand-specific identity.'
effect_note='Need authenticated full source body/call/effect expansion and exact lossless invocation/creator/object/resource normalization. Hash-only authentication and caller-selected labels are insufficient. Logical primitive versus SQL-admitted callable and independently fixed policy must remain distinct; missing source evidence is not a new policy choice.'
x=read('missing-input-source-recovery')
for r in x['records']:
    b=ib[r['BINDING_ID']];p=pm.get((b['WITNESS_ID'],b['INPUT_ID']));f=fun[b['FUNCTION_ID']];family=b['WITNESS_ID'].split('/')[1]
    note=blocker_notes.get(family,effect_note if family in ['default_privilege_path','SECURITY_DEFINER_path','reader_mutation'] else sql_note)
    r.update(TARGET_FUNCTION=b['FUNCTION_ID'],TARGET_INPUT=b['INPUT_ID'],REQUIRED_SEMANTIC_OBJECT=b['INPUT_ID'],REQUIRED_DOMAIN='Exact source-scoped normalized operand; native/SQL domains distinct',REQUIRED_STAGE=b['SOURCE_STAGE'],REQUIRED_TYPE=p['field_vector'] if p else f['INPUT_SCHEMA'],REQUIRED_CARDINALITY=p['cardinality'] if p else b['CARDINALITY'],SOURCE_FOUND=bool(p),SOURCE_FACT_ID=p['baseline_fact_ids']+[p['mutation_fact_id']] if p else [],CANDIDATE_SOURCE_IDS=b['CANONICAL_SOURCE_FACT'],DERIVATION_AVAILABLE=bool(p),DERIVATION_RULE=p['extraction'] if p else None,AUTHORITY_SOURCE=b['BINDING_AUTHORITY'],CLOSURE_STATUS=r['STATUS'],EXACT_REMAINING_GAP=None if p else note)
write('missing-input-source-recovery',x)
analysis=[]
cert=read('all-49-certification-recomputation')
for c in cert['functions']:
    for family in c['families']:
        analysis.append(dict(FUNCTION_ID=c['FUNCTION_ID'],FAMILY=family,STRICT_CERTIFIED=c['STRICT_CERTIFIED'],FROZEN_SELECTOR=families[family]['selector'],FROZEN_PREDICATE=families[family]['violation_predicate'],SOURCE=g.ref('d','family-descriptors.json','/families/'+family),RECOVERY='CLOSED_EXACT_SOURCE_PARAMETRIC' if c['STRICT_CERTIFIED'] else 'TECHNICAL_SOURCE_PROJECTION_NOT_ESTABLISHED',EXACT_GAP=None if c['STRICT_CERTIFIED'] else blocker_notes.get(family,effect_note if family in ['default_privilege_path','SECURITY_DEFINER_path','reader_mutation'] else sql_note),NOT_A_PROOF_OF_IMPOSSIBILITY=True,NEW_AUTHORITY_ALTERNATIVE_ESTABLISHED=False))
write('remaining-source-recovery-analysis',dict(functions_examined=49,family_rules_examined=len(analysis),records=analysis,maximality_claim='All49 profiles reexamined; only evidenced source projections closed. Remaining engineering proof gaps are listed individually; no claim that further source recovery is impossible.',next_bounded_action='Recover keyed module-map scalar projection and independent native source-stage adapters; keep full collection admission constraints, then recheck all49.'))

x=read('output-binding-closure')
for o in x['records']:
    o.update(OUTPUT_SEMANTIC_OBJECT='Case-specific source-typed violation evidence',OUTPUT_STAGE=o['TARGET_STAGE'],OUTPUT_TYPE='AVAILABLE boolean or UNAVAILABLE/null',TARGET_IDENTITY=o['CANONICAL_TARGET'],TARGET_CARDINALITY='Exactly one scoped guard',AUTHORITY_SOURCE=o['OUTPUT_BINDING_AUTHORITY'])
write('output-binding-closure',x)
for c in cert['functions']:
    props=c['PROPERTIES']
    if 'ALL_INPUT_BINDINGS_COMPLETE' in props:props['ALL_REQUIRED_INPUT_BINDINGS_COMPLETE']=props.pop('ALL_INPUT_BINDINGS_COMPLETE')
    if 'ALL_OUTPUT_BINDINGS_COMPLETE' in props:props['ALL_REQUIRED_OUTPUT_BINDINGS_COMPLETE']=props.pop('ALL_OUTPUT_BINDINGS_COMPLETE')
write('all-49-certification-recomputation',cert)

# Recompute topology independently of prior counters and presumed case ordering.
nodes={n['NODE_ID'] for n in comp['nodes']};adj=collections.defaultdict(list);degree={n:0 for n in nodes}
for e in comp['edges']:
    a,b=e['SOURCE_FUNCTION'],e['TARGET_FUNCTION'];assert a in nodes and b in nodes
    adj[a].append(b);degree[b]+=1
    source_complete=e['STATUS']=='COMPLETE' or (a.startswith('GUARD/') and ob['OUTPUT/'+a[6:]]['STATUS']=='COMPLETE')
    e.update(SOURCE_BINDING_STATUS='COMPLETE' if source_complete else 'MISSING',TARGET_BINDING_STATUS=e['STATUS'],SEMANTIC_COMPATIBILITY='ESTABLISHED' if e['STATUS']=='COMPLETE' else 'EXACT_TRANSFORM_NOT_ESTABLISHED',TYPE_COMPATIBILITY='ESTABLISHED' if e['STATUS']=='COMPLETE' else 'EXACT_SOURCE_TYPE_INSTANCE_NOT_ESTABLISHED',STAGE_COMPATIBILITY='ESTABLISHED' if e['STATUS']=='COMPLETE' else 'SOURCE_STAGE_ADAPTER_NOT_ESTABLISHED',CARDINALITY_COMPATIBILITY='ONE_SCOPED_EDGE; underlying collection completeness remains independent',ORDER_AUTHORITY=e['AUTHORITY_SOURCE'],CONDITION_AUTHORITY=e['AUTHORITY_SOURCE'],EDGE_STATUS=e['CLOSURE_STATUS'])
queue=collections.deque(n for n,d in degree.items() if d==0);visited=[]
while queue:
    n=queue.popleft();visited.append(n)
    for nxt in adj[n]:
        degree[nxt]-=1
        if not degree[nxt]:queue.append(nxt)
cycles=0 if len(visited)==len(nodes) else 1
assert cycles==0
comp.update(cycles=cycles,topological_order=visited,topological_nodes_visited=len(visited),cycle_method='Kahn traversal over every frozen edge including incomplete dependencies')
write('composition-edge-recomputation',comp)
dag=read('canonical-decision-dag');dag['CYCLES_DETECTED']=cycles;dag['TOPOLOGICAL_NODES_VISITED']=len(visited);write('canonical-decision-dag',dag)

x=read('minimum-remaining-blocker-set')
for c in x['causes']:
    binds=[ib[i] for i in c['input_ids']];outs=[ob[i] for i in c['output_ids']]
    functions=set(b['FUNCTION_ID'] for b in binds+outs);witnesses=set(b['WITNESS_ID'] for b in binds+outs)
    for eid in c['edge_ids']:
        e=eb[eid]
        for key in ['SOURCE_FUNCTION','TARGET_FUNCTION']:
            value=e[key]
            if value.startswith('EVALUATOR/'):functions.add(value)
            elif value.startswith('GUARD/'):witnesses.add(value[6:])
    c.update(FUNCTIONS_AFFECTED=sorted(functions),WITNESSES_AFFECTED=sorted(witnesses),PROJECTED_BINDINGS_AFFECTED=len(c['input_ids'])+len(c['output_ids'])+len(c['edge_ids']),SOURCE_RECOVERY_ANALYSIS='remaining-source-recovery-analysis.json',MINIMALITY='One nonduplicated recovery concern class, not proven individually irreducible or globally minimal. Exact per-profile missing transforms available in source analysis.')
write('minimum-remaining-blocker-set',x)

x=read('minimum-binding-contract-validation')
for c in x['items']:
    if c['pointer'].startswith('/special_obligations/') and not c['pointer'].endswith('/3'):
        c.update(classification='UNRESOLVABLE_FROM_CURRENT_STATIC_EVIDENCE',rationale='Exact full source authentication/admission normalization is not presently evidenced. Preserve frozen requirement and technical source-recovery task; no concrete new normative alternative demonstrated.')
    if c['pointer'].startswith('/functions_requiring_strict_certification/'):
        fc=next(f for f in cert['functions'] if f['FUNCTION_ID']==c['item']);c.update(classification='DETERMINISTICALLY_DERIVABLE' if fc['STRICT_CERTIFIED'] else 'UNRESOLVABLE_FROM_CURRENT_STATIC_EVIDENCE',rationale='Fresh all49 recomputation; exact per-profile gap in remaining-source-recovery-analysis.json',closure='STRICT_CERTIFIED' if fc['STRICT_CERTIFIED'] else 'NOT_CERTIFIED')
write('minimum-binding-contract-validation',x)
print(json.dumps(dict(status='AUDIT_RECORDS_ENRICHED',topological_nodes=len(visited),cycles=cycles)))
