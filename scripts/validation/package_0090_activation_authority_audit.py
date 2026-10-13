"""Non-executing authority audit and S04 source addendum; never provisions a DB.

The proposed amendment is not its own independent approval. Runtime closure
remains gated on separately recorded approval and independently observed health.
"""
import argparse
import collections
import json
import sys
from pathlib import Path
import package_0090_source_closure as q
import package_0090_semantic_ledger as ledger

BASELINE = 'c910b510fab2da0c28358d93d67b59dd18e7d58f'
ADR = 'docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md'
SPEC = 'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md'
HEALTH = 'docs/evidence/package-0090-g3f4-full-domain-fixture-contract/'
SIG = 'public.offline_read_history(uuid,bytea,uuid,text)'
OUTPUT = 'docs/evidence/package-0090-test-activation-native-health-first-positive'


def read(name):
    return json.loads((q.ROOT / name).read_text(encoding='utf-8-sig'))


def authority_gate(evidence):
    """Independent records must exist; caller assertions and proposed IDs do not suffice."""
    required = ('independent_activation_approval', 'approved_recipe', 'approval_identity',
                'change_identity', 'trusted_admin_audit_binding', 'test_native_harness_authority')
    return all(evidence.get(k) == 'INDEPENDENTLY_RECORDED' for k in required)


def validate_static_addendum(addendum):
    """Verify extraction coverage independently of the type-group generator."""
    expected = sum(k == 'FuncCall' for s in addendum['statements'] for k, _, _ in ledger.walk(s['ast']))
    q.require(expected == len(addendum['call_sites']) == addendum['call_sites_total'], 'Call coverage differs')
    covered = [i for g in addendum['candidate_contexts'] for i in g['site_indices']]
    q.require(sorted(covered) == list(range(expected)), 'Missing or multiply assigned call')
    q.require(len(addendum['candidate_contexts']) == addendum['candidate_contexts_total'], 'Candidate count differs')
    q.require(all(c['status'] == 'UNBOUND' and c['runtime_oid'] is None for c in addendum['call_sites']), 'Static evidence cannot bind runtime')
    q.require(all(g['status'] == 'UNBOUND' for g in addendum['candidate_contexts']), 'Static group cannot bind runtime')
    q.require(addendum['new_global_candidate_contexts'] == 818 + len(addendum['candidate_contexts']), 'Successor arithmetic differs')
    q.require(addendum['global_bound'] == 0 and addendum['global_unbound'] == addendum['new_global_candidate_contexts'], 'Unsupported global promotion')
    q.require(not addendum['group_equivalence_proven'] and not addendum['full_semantic_denominator_closed'], 'Unsupported closure')
    for c in addendum['call_sites']:
        statement = addendum['statements'][c['statement_ordinal']]
        node = ledger.at(statement['ast'], c['path'])
        q.require('.'.join(ledger.strings(node['funcname'])) == c['callee'], 'Call source path differs')
    for op in addendum['operator_and_implicit_expression_sites']:
        node = ledger.at(addendum['statements'][op['statement_ordinal']]['ast'], op['ast_path'])
        q.require(ledger.strip_positions(node) == op['ast'], 'Operator source path differs')
    q.require(len(addendum['operator_and_implicit_expression_sites']) == addendum['operator_and_implicit_expression_sites_total'], 'Operator count differs')


def build(folder, parser_path):
    sys.path.insert(0, parser_path)
    from pglast.parser import parse_sql_json, parse_plpgsql_json, scan
    source = q.git('show', 'HEAD:' + q.V043.relative_to(q.ROOT).as_posix())
    q.require(q.sha(source) == q.SOURCE_HASH, 'Canonical V043 drift')
    q.git('merge-base', '--is-ancestor', BASELINE, 'HEAD')
    q.require(q.git('diff', '--', str(q.MIGRATIONS.relative_to(q.ROOT))) == b'', 'Migration working-tree drift')
    for path in sorted(q.MIGRATIONS.glob('V*.sql')):
        if int(path.name.split('__')[0][1:]) <= 42:
            rel = path.relative_to(q.ROOT).as_posix()
            q.require(q.git('show', 'HEAD:' + rel) == q.git('show', q.FROZEN + ':' + rel), 'Frozen source drift: ' + rel)
    tree = json.loads(parse_sql_json(source.decode()))['stmts']
    declarations = [(i, raw) for i, raw in enumerate(tree) if 'CreateFunctionStmt' in raw['stmt']
                    and ledger.signature(raw['stmt']['CreateFunctionStmt']) == SIG]
    q.require(len(declarations) == 1, 'One S04 declaration required')
    ordinal, raw = declarations[0]
    start = raw.get('stmt_location', 0)
    end = start + raw['stmt_len'] if raw.get('stmt_len') else len(source)
    definition = source[start:end].decode()
    pl = json.loads(parse_plpgsql_json(definition))[0]['PLpgSQL_function']
    statements = []
    for key, expr, path in ledger.walk(pl):
        if key != 'PLpgSQL_expr':
            continue
        original = expr['query']; query = original; mode = expr.get('parseMode', 0)
        if mode == 2:
            query = 'SELECT ' + query
        elif mode in (3, 4, 5):
            token = next((t for t in scan(query) if t.name in ('COLON_EQUALS', 'EQUALS')), None)
            q.require(token is not None, 'Assignment token missing')
            query = 'SELECT ' + query[token.end + 1:]
        statements.append({'ordinal': len(statements), 'control_path': list(path), 'original_query': original,
                           'query_sha256': q.sha(original.encode()), 'parse_mode': mode,
                           'parser_only_query': query, 'ast': json.loads(parse_sql_json(query))})
    # Reuse only frozen-source type inference, never its historical closure labels.
    sys.path.insert(0, str(q.ROOT / 'docs/evidence/package-0090-g3f4-typed-binding-dml'))
    import identifier_rebinding as binding

    class S04Resolver(binding.Resolver):
        def references(self, node, scopes, path=()):
            if isinstance(node, dict) and 'FuncCall' in node:
                call = node['FuncCall']
                self.calls.append({'path': list(path) + ['FuncCall'],
                                   'callee': '.'.join(ledger.strings(call['funcname'])),
                                   'types': [self.typ(arg, scopes) for arg in call.get('args', [])],
                                   'variadic': bool(call.get('func_variadic')),
                                   'argument_asts': call.get('args', [])})
            yield from super().references(node, scopes, path)

    resolver = S04Resolver({'parameter_names': ['binding_id', 'plan_fingerprint', 'expected_incarnation_id', 'surface_version'],
                           'parameter_types': ['uuid', 'bytea', 'uuid', 'text'], 'plpgsql_ast': pl,
                           'expressions': [{'ast_path': s['control_path']} for s in statements]})
    resolver.discover_records([{'SQL_STATEMENT_ID': SIG + ':S' + str(s['ordinal']),
                               'query': s['original_query'], 'ast': s['ast']} for s in statements])
    calls = []; operators = []; groups = collections.defaultdict(list)
    kinds = {'A_Expr', 'TypeCast', 'BoolExpr', 'NullTest', 'BooleanTest', 'SQLValueFunction',
             'MinMaxExpr', 'A_Indirection', 'SubLink', 'SortBy', 'ArrayExpr', 'CoalesceExpr',
             'CollateClause', 'CaseExpr', 'RowExpr'}
    for s in statements:
        resolver.use_path = tuple(s['control_path'][:-1]); resolver.calls = []
        list(resolver.references(s['ast'], []))
        for c in resolver.calls:
            c.update({'caller': SIG, 'statement_ordinal': s['ordinal'], 'control_path': s['control_path'],
                      'consumer_path': c['path'][:-1], 'query_sha256': s['query_sha256'],
                      'status': 'UNBOUND', 'runtime_oid': None, 'consumer_semantics_proven': False,
                      'owner': 'flooow_offline_audit_owner', 'security_mode': 'DEFINER',
                      'search_path': ['pg_catalog', 'pg_temp']})
            calls.append(c)
            key = (c['callee'], tuple(c['types']), c['variadic'], SIG)
            # Unresolved expressions are kept distinct instead of assuming equivalence.
            if 'UNRESOLVED' in c['types']:
                key += (ledger.identity(ledger.strip_positions(c['argument_asts'])),)
            groups[key].append(len(calls) - 1)
        for kind, value, path in ledger.walk(s['ast']):
            if kind in kinds:
                operators.append({'kind': kind, 'statement_ordinal': s['ordinal'], 'ast_path': list(path),
                                  'control_path': s['control_path'], 'ast': ledger.strip_positions(value),
                                  'runtime_binding': 'UNBOUND', 'consumer_semantics_proven': False})
    q.require(calls and statements, 'Empty S04 addendum')
    corpus = [json.loads(p.read_text())['function']['signature'] for p in
              (ledger.BASE / 'continuation-05').glob('*.json') if len(p.stem) == 24]
    q.require(len(corpus) == 68 and SIG not in corpus, 'Historical omission premise differs')
    addendum = {'status': 'STATIC_CANDIDATES_ONLY', 'source_sha256': q.sha(source),
                'definition_statement_ordinal': ordinal, 'definition_sha256': q.sha(source[start:end]),
                'start_line': source[:start].count(b'\n') + 1, 'signature': SIG,
                'statements': statements, 'call_sites': calls, 'call_sites_total': len(calls),
                'candidate_contexts': [{'key': list(k), 'site_indices': v, 'status': 'UNBOUND'} for k, v in sorted(groups.items(), key=lambda x: str(x[0]))],
                'candidate_contexts_total': len(groups), 'operator_and_implicit_expression_sites': operators,
                'operator_and_implicit_expression_sites_total': len(operators),
                'operator_denominator_separate': True, 'group_equivalence_proven': False,
                'argument_type_inference_status': 'STATIC_DIAGNOSTIC_UNVALIDATED_NOT_CATALOG_TRUTH',
                'argument_type_inference_limitations': 'Inherited resolver may select generic builtin return types and does not establish record dominance. All groups are candidates; no overload, coercion or inferred type is promoted.',
                'implicit_catalog_cast_operator_implementation_closure': 'UNPROVEN',
                'base_818_unchanged': True, 'duplicate_caller_groups': 0,
                'deduplication_rule': 'Original group includes caller; S04 absent from all 68 callers. Callee spelling alone never merges different callers.',
                'new_global_candidate_contexts': 818 + len(groups), 'global_bound': 0,
                'global_unbound': 818 + len(groups), 'full_semantic_denominator_closed': False,
                'limitations': 'Candidate call grouping only. Operators, casts, consumer states and runtime OIDs are not proved. No historical callee closure labels imported.'}
    validate_static_addendum(addendum)
    ledger.write(folder, 's04-source-addendum.json', addendum)
    ledger.write(folder, 'semantic-corpus-addendum-s04.json', {k: v for k, v in addendum.items() if k not in ('statements', 'call_sites', 'operator_and_implicit_expression_sites')})
    design = read(HEALTH + 'NATIVE-HEALTH-DESIGN.json')
    dimensions = {'participant_identity': 'IDENTITY_SOURCE', 'host_process_binding': 'IDENTITY_BINDING',
                  'participant_generation': 'GENERATION_SOURCE', 'enrollment': 'GENERATION_CREATED_WHEN',
                  'authenticated_channel': 'GENERATION_BINDING', 'freshness': 'LIVENESS_SOURCE',
                  'functional_operation': 'COMPLETED_WORK_WITNESS', 'dependency_binding': 'GENERATION_OBSERVED_BY',
                  'catalog_binding': 'PROGRESS_SOURCE', 'generation_incarnation_semantics': 'GENERATION_BINDING',
                  'restart_behavior': 'RESTART_BEHAVIOR', 'failure_behavior': 'FAIL_CLOSED_ACTION'}
    requirements = []
    for p in design['participants']:
        for dimension, field in dimensions.items():
            requirements.append({'requirement_id': p['PARTICIPANT_NAME'] + '/' + dimension,
                                 'source': HEALTH + 'NATIVE-HEALTH-DESIGN.json#/participants/' + str(design['participants'].index(p)) + '/' + field,
                                 'required_evidence': p[field], 'producer': p['PARTICIPANT_NAME'],
                                 'observer': p['INDEPENDENT_OBSERVER'],
                                 'freshness_rule': p['LIVENESS_SOURCE'] + '; S04 watchdog age: exact fixture tag24=100us; no independent per-participant numeric window adopted',
                                 'success_semantics': design['decision_rule'], 'failure_semantics': p['FAIL_CLOSED_ACTION'],
                                 'observation': 'NOT_EXECUTED_AUTHORITY_HOLD'})
    ledger.write(folder, 'native-health-contract.json', {'status': 'RECONSTRUCTED_NOT_IMPLEMENTED',
        'dimensions': list(dimensions), 'requirements': requirements, 'required_edges': design['required_edges'],
        'root_assumption': design['root_assumption'], 'source_status': design['status'],
        'generation_implementation_authority_present': False, 'test_harness_authorized': False,
        'reason': 'Native contract final paragraph explicitly leaves framing/counters/channels/SCM_RIGHTS/pidfd/enforcement changes separately unauthorized; current task makes implementation conditional on authority.'})
    ledger.write(folder, 'native-participants.json', {'managed_participants': design['participants'],
        'managed_count': len(design['participants']), 'external_observer': 'HEALTH_GUARD', 'external_root': 'HOST_PLATFORM',
        'dependencies': design['required_edges'], 'runtime_binary_identity': None, 'runtime_generation': None,
        'enrollment_authority': 'Proposed trusted bootstrap only; no enrolled actor in this tranche',
        'owner': 'Trusted OS/bootstrap design, not service ownership', 'freshness_window': 'No separately approved per-participant numeric window; binding watchdog tag24 is 100us'})
    activation = {'status': 'PROPOSED_NOT_APPROVED', 'technical_fixture_approval_pattern_exists': True,
        'precedent': {'commit': '60f7bbe13f4c2b44d8e070a41d60dc5e28ae988d', 'source': SPEC + ':2263',
                      'approval_provenance': 'FLOOOW_TECHNICAL_FIXTURE_APPROVAL_2026-10-03',
                      'scope': 'TEST_GOLDEN_REHEARSAL_ONLY', 'delegated_new_approval_authority': False},
        'current_tranche_can_adopt_test_fixture_decision': False,
        'reason': 'A recorded independent approval is precedent, not delegation. AGENTS sections5/7 prohibit manufacturing approval identity/authority; current phases2/10 expressly condition adoption on governing authority.',
        'test_policy_values_approved': True, 'test_policy_activation_approved': False,
        'test_activation_recipe_approved': False, 'test_approval_identity_approved': False,
        'test_change_identity_approved': False, 'test_admin_audit_contract_approved': False,
        'existing_admin_audit_obligation': SPEC + ':2236',
        'existing_admin_audit_store_identified': False,
        'excluded_store': {'table': 'public.integration_control_audit', 'source': 'V004:59',
                           'reason': 'Integration organization/connection action/time/correlation log; lacks canonical policy, activation, actor, approval/change, deployment/incarnation and commit binding; no governing designation as deployment provisioning audit'},
        'new_package_audit_table_authorized': False,
        'proposed_recipe': {'identity': 'TEST_ONLY/0090/activation/db-clock-in-transaction/v1',
            'time_source': 'pg_catalog.clock_timestamp() exactly once after approval/audit PREPARED validation inside isolated ADMIN registration transaction',
            'precision': 'PostgreSQL finite timestamptz(6); integer microseconds; no floating epoch conversion',
            'effective_from': 'captured database clock; offset=0', 'capture_order': ['verify independent approved immutable decision and exact target', 'durably prepare audit', 'BEGIN ADMIN', 'capture clock and transaction identity', 'validate exact29 fields/digest/version', 'INSERT immutable policy and associate audit', 'COMMIT', 'independently confirm commit and audit acknowledgment before eligibility'],
            'canonical_representation': 'Existing29-field policy bytes unchanged; effective_from separate immutable activation metadata encoded UTC six fractional digits plus integer signed epoch microseconds',
            'audit_representation': 'Complete SPEC25.4 fields; prepared/transaction-associated/COMMITTED-or-ROLLED_BACK-or-UNKNOWN records, target and recipe binding',
            'replay': 'Plain duplicate SQL registration fails; exact approved replay only reconciles original acknowledged commit; divergent metadata/version/digest denied without upsert or renewal',
            'failure': 'No ACTIVE eligibility/READY while approval/audit/commit uncertain. No transaction claims external audit and PostgreSQL atomicity without demonstrated implementation.',
            'absolute_time_reproducible': False, 'semantic_recipe_reproducible_design': True},
        'proposed_identities': {'approval_id': None, 'change_id': None, 'actor_identity': None,
                               'reason': 'Must come from independent recorded TEST_ONLY approval; proposal intentionally does not mint an approval principal',
                               'target_policy_version': 'fixture-1', 'target_policy_digest': read('docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json')['canonical_policy_sha256'],
                               'scope': 'TEST_ONLY_DISPOSABLE_S04_NO_FIELD_AUTHORITY'},
        'activation_proven': False}
    ledger.write(folder, 'test-activation-contract.json', activation)
    hold = {'status': 'NOT_EXECUTED_AUTHORITY_HOLD', 'new_runtime_observation': False,
            'historical_preparation_source': 'docs/evidence/package-0090-first-positive/READINESS.json',
            'activation_approved': False, 'native_health_approved': False,
            'ready_created': False, 'positive_executed': False, 'positive_pass': False,
            'actual_rows': None, 'precheck': 'FAIL_AUTHORITY_PREREQUISITES', 'runtime_tests': 0}
    for name in ('admin-audit-observation.json', 'native-health-observation.json', 'readiness-observation.json',
                 'header-registration.json', 'auditor-slot.json', 's04-observation.json', 's04-negative-matrix.json',
                 's04-semantic-bindings.json', 's04-null-matrix.json', 's04-acl.json'):
        ledger.write(folder, name, {**hold, 'artifact': name, 'closure_complete': False})
    readiness = {**hold, 'baseline': BASELINE, 'source_hash': q.sha(source), 'branch': 'checkpoint/package-0090-cloud-handoff',
        'source_addendum_static': True, 'S04_CALL_SITES': len(calls), 'S04_CANDIDATE_CONTEXTS': len(groups),
        'S04_CONTEXTS_BOUND': 0, 'S04_CONTEXTS_UNBOUND': len(groups),
        'GLOBAL_BOUND_CALL_SHAPES': 0, 'GLOBAL_UNBOUND_CALL_SHAPES': 818 + len(groups),
        'G1': 'PARTIAL', 'G2': 'PARTIAL', 'G3': 'OPEN', 'G4': 'OPEN', 'G5': 'PARTIAL', 'G6': 'PARTIAL', 'G7': 'OPEN', 'G8': 'PARTIAL',
        'ACTIVE_FIXTURE_FOUNDATION_READY': False, 'FIRST_POSITIVE_FIXTURE_READY': False, 'FULL_FIXTURE_READY': False,
        'ACTIVE_LOADER_REPRODUCIBLE': False, 'B01': 'OPEN', 'B02': 'OPEN', 'B03': 'OPEN', 'B04': 'OPEN',
        'B05': 'OPEN', 'B06': 'OPEN', 'B07': 'OPEN', 'B08': 'OPEN', 'known_blocker_groups_remaining': 8,
        'scoped_blockers': ['Independent TEST activation decision/identities and trusted audit implementation unestablished',
                            'Separate native harness authority and independently completed participant health unestablished'],
        'HIGH': 'UNKNOWN_RUNTIME_REVIEW_NOT_EXECUTED', 'MEDIUM': 'UNKNOWN_RUNTIME_REVIEW_NOT_EXECUTED', 'LOW': 'UNKNOWN_RUNTIME_REVIEW_NOT_EXECUTED',
        'canonical_v043_executed': False, 'canonical_v043_mutated': False, 'shared_db_contacted': False,
        'production_contacted': False, 'execution_authority': 'BLOCKED', 'recovery_authority': 'BLOCKED', 'ROOM_OPERATIONAL': False,
        'NEXT_EXECUTED': False, 'fresh_database_campaign': 'NOT_EXECUTED_PHASE2_STOP',
        'static_reproduction': 'Source/contract generation can repeat; not ACTIVE loader reproducibility'}
    if (folder / 'unit-tests.json').exists():
        readiness['static_tests'] = json.loads((folder / 'unit-tests.json').read_text())
    ledger.write(folder, 'READINESS.json', readiness)
    inputs = [ADR, SPEC, HEALTH + 'NATIVE-HEALTH-CONTRACT.md', HEALTH + 'NATIVE-HEALTH-DESIGN.json',
              'AGENTS.md', 'docs/evidence/PACKAGE-0090-G3F-3B-FIXTURE-001.json',
              'docs/evidence/package-0090-first-positive/READINESS.json',
              'scripts/validation/package_0090_activation_authority_audit.py',
              'scripts/validation/test_package_0090_activation_authority_audit.py',
              'docs/evidence/PACKAGE-0090-test-activation-native-health-first-positive.md']
    inputs += ['scripts/validation/package_0090_semantic_ledger.py', 'scripts/validation/package_0090_source_closure.py',
               'docs/evidence/package-0090-g3f4-typed-binding-dml/identifier_rebinding.py',
               'docs/evidence/package-0090-g3f4-typed-binding-dml/catalog_metadata.py',
               'docs/evidence/package-0090-g3f4-typed-binding-dml/source_binding.py']
    for directory, pattern in [('continuation-02', '*.json'), ('continuation-02/pg18.4', '*.dat'),
                               ('continuation-03/pg18.4', '*.h'), ('continuation-05', '*.json')]:
        inputs += [p.relative_to(q.ROOT).as_posix() for p in sorted((ledger.BASE / directory).glob(pattern))]
    ledger.write(folder, 'SHA256-MANIFEST.json', {'inputs': {p: q.sha((q.ROOT / p).read_bytes()) for p in inputs},
        'outputs': {p.name: q.sha(p.read_bytes()) for p in sorted(folder.iterdir()) if p.is_file() and p.name != 'SHA256-MANIFEST.json'},
        'canonical_git_lf_sha256': q.sha(source), 'V043_FENCE_PRESENT': "implementation closure is incomplete; execution denied" in source.decode()})
    return readiness


if __name__ == '__main__':
    arg = argparse.ArgumentParser(); arg.add_argument('--parser-path', required=True); arg.add_argument('--directory', default=OUTPUT)
    args = arg.parse_args(); folder = Path(args.directory); folder.mkdir(parents=True, exist_ok=True)
    print(json.dumps(build(folder, args.parser_path), indent=2))
