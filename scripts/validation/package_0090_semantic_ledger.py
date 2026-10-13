"""Source-context successor. Preserves diagnostic corpus and never promotes candidates.

All occurrence assignments/consumer paths are reproducible. Closure requires
separate runtime, NULL, security and authority evidence for every context group.
"""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import package_0090_source_closure as q

BASE = q.ROOT / 'docs/evidence/package-0090-g3f4-typed-binding-dml'


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def identity(v):
    return hashlib.sha256(canon(v)).hexdigest()


def strip_positions(v):
    if isinstance(v, dict):
        return {k: strip_positions(x) for k, x in v.items() if k not in ('location', 'arg_location', 'rexpr_list_start', 'rexpr_list_end')}
    if isinstance(v, list):
        return [strip_positions(x) for x in v]
    return v


def strings(nodes):
    return [x['String']['sval'] for x in nodes]


def typename(t):
    return '.'.join(strings(t['names'])).removeprefix('pg_catalog.') + ('[]' if t.get('arrayBounds') else '')


def signature(f):
    name = '.'.join(strings(f['funcname']))
    if '.' not in name:
        name = 'public.' + name
    return name + '(' + ','.join(typename(p['FunctionParameter']['argType']) for p in f.get('parameters', []) if p['FunctionParameter'].get('mode') not in ['FUNC_PARAM_OUT', 'FUNC_PARAM_TABLE']) + ')'


def at(node, path):
    return locate(node, path)[0]


def locate(node, path):
    mapped = []
    for key in path:
        if key == 'SelectStmt' and isinstance(node, dict) and 'SelectStmt' not in node and mapped and mapped[-1] in ('larg', 'rarg') and 'op' in node:
            # Tagged analysis serialization versus bare SelectStmt set-operation member.
            # Preserve every actual member/path; only skip the redundant type wrapper.
            continue
        node = node[key]
        mapped.append(key)
    return node, mapped


def walk(node, path=()):
    if isinstance(node, dict):
        for k, value in node.items():
            yield k, value, path + (k,)
            yield from walk(value, path + (k,))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk(value, path + (i,))


def write(folder, name, obj):
    (folder / name).write_bytes(json.dumps(obj, indent=2, ensure_ascii=False).encode('utf-8') + b'\n')


def source_index(parser):
    index, columns, grants, inputs = {}, set(), [], {}
    v043_signatures = []
    for path in sorted(q.MIGRATIONS.glob('V*.sql')):
        rel = path.relative_to(q.ROOT).as_posix()
        b = q.git('show', 'HEAD:' + rel)
        inputs[rel] = q.sha(b)
        for ordinal, raw in enumerate(json.loads(parser(b.decode('utf-8-sig')))['stmts']):
            statement = raw['stmt']
            provenance = {'file': rel, 'git_source_sha256': q.sha(b), 'statement_ordinal': ordinal}
            if 'CreateFunctionStmt' in statement:
                f = statement['CreateFunctionStmt']; sig = signature(f)
                opts = {x['DefElem']['defname']: x['DefElem'].get('arg') for x in f['options']}
                settings = [x['DefElem']['arg']['VariableSetStmt'] for x in f['options'] if x['DefElem']['defname'] == 'set']
                index[sig] = {'signature': sig, 'schema': sig.split('.')[0], 'owner': 'postgres',
                              'security_mode': 'DEFINER' if opts.get('security', {}).get('Boolean', {}).get('boolval') else 'INVOKER',
                              'strict': bool(opts.get('strict', {}).get('Boolean', {}).get('boolval')),
                              'volatility': opts.get('volatility', {}).get('String', {}).get('sval', 'volatile'),
                              'search_path': [a['A_Const']['sval']['sval'] for setting in settings if setting['name'] == 'search_path' for a in setting.get('args', [])],
                              'definition_source': provenance, 'owner_source': provenance,
                              'runtime_correspondence_proven': False}
                if path.name.startswith('V043'):
                    v043_signatures.append(sig)
            if 'AlterOwnerStmt' in statement:
                s = statement['AlterOwnerStmt']
                if s['objectType'] == 'OBJECT_FUNCTION':
                    obj = s['object']['ObjectWithArgs']
                    name = '.'.join(strings(obj['objname']))
                    if '.' not in name:
                        name = 'public.' + name
                    sig = name + '(' + ','.join(typename(x['TypeName']) for x in obj.get('objargs', [])) + ')'
                    if sig in index:
                        index[sig]['owner'] = s['newowner']['rolename']
                        index[sig]['owner_source'] = provenance
            if path.name.startswith('V043') and 'GrantStmt' in statement:
                g = statement['GrantStmt']
                grants.append({'ast': strip_positions(g), 'provenance': provenance})
                if g.get('is_grant') and g['objtype'] == 'OBJECT_TABLE':
                    for obj in g['objects']:
                        rv = obj['RangeVar']; relation = rv.get('schemaname', 'public') + '.' + rv['relname']
                        for p in g.get('privileges', []):
                            priv = p['AccessPriv']
                            for col in priv.get('cols', []):
                                for grantee in g['grantees']:
                                    role = grantee['RoleSpec'].get('rolename', 'PUBLIC')
                                    columns.add((role, relation, col['String']['sval'], priv['priv_name']))
    return index, columns, grants, inputs, v043_signatures


def fixture_manifest():
    names = ['PACKAGE-0090-G3F-3B-FIXTURE-001.json', 'PACKAGE-0090-G3F-3B-EVIDENCE-FIXTURE-001.json', 'PACKAGE-0090-G3F-3B-CODEC-GOLDENS.json']
    documents = {n: json.loads((q.ROOT / 'docs/evidence' / n).read_text(encoding='utf-8-sig')) for n in names}
    policy = documents[names[0]]
    domain = b'FLOOOW/OFFLINE-FIELD-PROOF/DEADLINE-POLICY/V1'
    frame = struct.pack('>I', len(domain)) + domain + struct.pack('>H', 29)
    q.require(len(policy['fields']) == 29, 'Approved complete policy required')
    for tag, field in enumerate(policy['fields'], 1):
        q.require(field['tag'] == tag, 'Ascending immutable policy tags required')
        value = field['value'].encode() if tag == 1 else struct.pack('>q', field['value'])
        payload = b'\x01' + value
        frame += struct.pack('>HI', tag, len(payload)) + payload
    q.require(frame.hex() == policy['canonical_policy_hex'] and q.sha(frame) == policy['canonical_policy_sha256'], 'Independent approved policy encoding mismatch')
    components = [
        ('canonical_policy', 'public.offline_deadline_policy', 'ALREADY_APPROVED_TEST_VALUE_EXISTS', policy, 'SPEC-0090 Independent technical test-fixture approval; section21.2/25'),
        ('retained_source_rows', 'V001-V042 retained domain', 'ALREADY_APPROVED_TEST_VALUE_EXISTS', documents[names[1]], 'SPEC-0090 Complete normative retained TEST evidence fixture'),
        ('codec_goldens', 'binding/manifest/evidence encodings', 'ALREADY_APPROVED_TEST_VALUE_EXISTS', documents[names[2]], 'SPEC-0090 codec goldens reference'),
        ('service_identity_recipe', 'pg_roles/four service slots', 'DERIVABLE_FROM_APPROVED_FIXTURE', {'names': ['test_0090_verification', 'test_0090_issuance', 'test_0090_execution', 'test_0090_audit'], 'attributes': 'LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS', 'memberships': [], 'oid_rule': 'Capture real allocated OIDs; never substitute model OIDs'}, 'SPEC-0090 section3; full-domain fixture contract'),
        ('live_binding', 'offline_binding_header/lifecycle', 'DERIVABLE_FROM_APPROVED_FIXTURE', None, 'SPEC-0090 section4; full-domain fixture contract; live OIDs and all immutable bytes unresolved'),
        ('readiness_and_history_acl_expectations', 'offline_readiness', 'DERIVABLE_FROM_APPROVED_FIXTURE', None, 'SPEC-0090 section16/21.2; complete independently expected manifests required'),
        ('native_participant_health', 'host/enrollment/watchdog', 'NEEDS_NEW_TEST_FIXTURE_APPROVAL', None, 'NATIVE-HEALTH-CONTRACT.md; independently observed progress/enrollment required; existing model insufficient'),
        ('runtime_clock_and_windows', 'binding/attestation/policy effective_from', 'NEEDS_NEW_TEST_FIXTURE_APPROVAL', None, 'Fixed golden epoch is not a live DB clock; immutable runtime manifest required'),
        ('original_signed_attestation_and_commitment', 'offline_expected_signed_attestation/frozen V041', 'DERIVABLE_FROM_APPROVED_FIXTURE', None, 'SPEC-0090 signed input amendments; originals verified independently, not fabricated'),
        ('test_key_custody', 'offline_preflight_key/ephemeral signing key', 'DERIVABLE_FROM_APPROVED_FIXTURE', None, 'Full-domain fixture contract: disposable non-public-seed secret; private custody and erasure'),
        ('canonical_authority_and_intent_lineage', 'V041/V042 governance and admission', 'DERIVABLE_FROM_APPROVED_FIXTURE', None, 'SPEC-0090 section21.4; original verified authority required'),
        ('expected_committed_receipts_states_audit', 'all thirteen required case trajectories', 'DERIVABLE_FROM_APPROVED_FIXTURE', None, 'POSITIVE-CASE-PRECONDITIONS.json; no downstream effects/receipts prefilled')]
    rows = []
    for name, table, classification, value, approval in components:
        rows.append({'logical_name': name, 'table_or_domain': table, 'classification': classification, 'exact_value': value,
                     'canonical_encoding': 'UTF8 sorted-key compact JSON; policy additionally DEADLINE-POLICY/V1',
                     'sha256': identity(value) if value is not None else None, 'approval_provenance': approval,
                     'scope': 'TEST_ONLY', 'production_authority': False, 'input_complete': value is not None,
                     'active_runtime_proven': False})
    return {'components': rows, 'components_required': len(rows), 'components_present': sum(x['input_complete'] for x in rows),
            'components_missing': sum(not x['input_complete'] for x in rows),
            'active_fixture_contract_ready': False, 'full_fixture_ready': False, 'production_authority': False,
            'canonical_policy_hex': frame.hex(), 'canonical_policy_sha256': q.sha(frame),
            'input_hashes': {n: q.sha((q.ROOT / 'docs/evidence' / n).read_bytes()) for n in names},
            'no_production_authority_dependency': True,
            'positive_execution_interlock': 'Full-domain fixture contract denies positives until typed SQL mapping and independently validated original binding/attestation/live readiness are complete'}


def build(folder, parser):
    source = q.git('show', 'HEAD:' + q.V043.relative_to(q.ROOT).as_posix())
    q.require(q.sha(source) == q.SOURCE_HASH, 'Canonical source drift')
    q.derive(source, parser)
    historical = q.ROOT / 'docs/evidence/package-0090-v043-source-closure-release-gate'
    manifest = json.loads((historical / 'SHA256-MANIFEST.json').read_text())
    q.require(all(q.sha((q.ROOT / p).read_bytes()) == v['sha256'] for p, v in manifest['entries'].items()), 'Frozen prior evidence changed')
    functions, expected_columns, grant_operations, source_hashes, v043 = source_index(parser)
    import package_0090_source_gate as authority
    normative_columns = authority.expected_column_grants((q.ROOT / authority.SPEC).read_text(encoding='utf-8-sig'))
    q.require(expected_columns == normative_columns, 'Canonical and normative column ACL sets differ')
    calls = json.loads((BASE / 'continuation-09/SCOPED-CALL-CANDIDATES.json').read_text())
    q.require(len(calls) == 15513, 'Frozen call count differs')
    corrected = 0
    for c in calls:
        if c['callee_spelling'] == 'pg_catalog.convert_to' and c['argument_types'] == ['bool', 'unknown_literal']:
            q.require(c['argument_asts'][0]['A_Expr']['kind'] == 'AEXPR_NULLIF', 'Correction boundary differs')
            c['argument_types'][0] = 'text'; corrected += 1
    q.require(corrected == 4, 'Exact prior NULLIF correction required')
    corpus = {}
    for p in (BASE / 'continuation-05').glob('*.json'):
        if not re.fullmatch(r'[0-9a-f]{24}\.json', p.name):
            continue
        f = json.loads(p.read_text(encoding='utf-8'))
        signature_ = f['function']['signature']
        corpus[signature_] = f
        q.require(signature_ in functions, 'Unknown source function signature: ' + signature_)
    q.require(len(corpus) == 68, 'Exact 68-function corpus required')
    needed = set(corpus) | set(v043)
    contexts = [functions[s] for s in sorted(needed)]
    grouped, traces, occurrences, source_inputs = collections.defaultdict(list), {}, [], {}
    old_groups = set()
    for ordinal, c in enumerate(calls):
        f = corpus[c['caller']]
        cp = c['control_path']
        statements = [s for s in f['statements'] if s.get('control_ast_path', []) in (cp, cp + ['PLpgSQL_expr'])]
        q.require(len(statements) == 1, 'Unique source statement/context required')
        statement = statements[0]
        expected_name = [{'String': {'sval': n}} for n in c['callee_spelling'].split('.')]
        path_status = 'EXACT_CORPUS_PATH'
        try:
            actual, mapped_path = locate(statement['ast'], c['ast_path'])
            actual = actual.get('FuncCall', actual)
            q.require(actual['funcname'] == expected_name, 'Source call path mismatch')
            original_paths = [mapped_path]
            if mapped_path != c['ast_path']:
                path_status = 'MECHANICAL_SELECT_MEMBER_WRAPPER_RELOCATION'
            parent = at(statement['ast'], c['ast_path'][:-1])
        except (KeyError, IndexError):
            matches = [(value, list(path[:-1])) for key_, value, path in walk(statement['ast']) if key_ == 'FuncCall'
                       and value['funcname'] == expected_name and strip_positions(value.get('args', [])) == strip_positions(c['argument_asts'])]
            original_paths = [path for _, path in matches]
            path_status = 'UNIQUE_EXACT_AST_RELOCATION' if len(matches) == 1 else 'SOURCE_PATH_MAPPING_UNPROVEN'
            parent = at(statement['ast'], original_paths[0][:-1]) if len(matches) == 1 else None
        occurrence_id = 'site-' + identity({'caller': c['caller'], 'control_path': cp, 'ast_path': c['ast_path']})[:24]
        context = functions[c['caller']]
        old_key = (c['callee_spelling'], tuple(c['argument_types']), c['explicit_variadic'])
        old_groups.add(old_key)
        # Different callers/effective owners cannot share an authority bucket.
        key = old_key + (c['caller'],)
        record = {'occurrence_id': occurrence_id, 'diagnostic_ordinal': ordinal, 'source_function': c['caller'],
                  'source_provenance': c['original_source'], 'control_path': cp, 'sql_ast_path': c['ast_path'],
                  'source_argument_expressions_sha256': identity(strip_positions(c['argument_asts'])),
                  'original_ast_path_candidates': original_paths, 'path_mapping_status': path_status,
                  'statement_query_sha256': statement.get('query_sha256'), 'consumer_parent_ast_sha256': identity(strip_positions(parent)),
                  'immediate_consumer_path': c['ast_path'][:-1], 'consumer_structural_trace_present': True,
                  'consumer_semantics_proven': False, 'effective_role_source': context['owner'] if context['security_mode'] == 'DEFINER' else 'CURRENT_USER_INHERITED_FROM_CALL_EDGE',
                  'security_mode': context['security_mode'], 'search_path': context['search_path'],
                  'parser_only_normalizations': f['function'].get('parser_only_normalizations', []),
                  'trace_boundary': 'Exact static expression/control paths, not dominated guard or runtime authority proof'}
        grouped[key].append(record)
        occurrences.append(record)
        traces[occurrence_id] = {'callee_result': c['callee_spelling'], 'immediate_expression_path': record['immediate_consumer_path'],
                                 'control_consumer_path': cp, 'source_function_outcome': 'UNPROVEN', 'authority_consequence': 'UNPROVEN', 'semantic_proven': False}
        src = f['function']['source']; source_inputs[src['file']] = src['source_hash']
    for p, h in source_inputs.items():
        q.require(q.sha(q.git('show', 'HEAD:' + p)) == h, 'Expanded source byte provenance differs')
    q.require(len({x['occurrence_id'] for x in occurrences}) == 15513, 'Unique complete occurrence assignment required')
    q.require(len(old_groups) == 174, 'Prior corrected shape denominator differs')
    ledger = []
    for key, sites in sorted(grouped.items()):
        name, types, variadic, caller = key
        sid = 'shape-' + identity(key)[:24]
        context = functions[caller]
        ledger.append({'shape_id': sid, 'diagnostic_shape_id': 'diagnostic-' + identity(key[:3])[:24],
                       'source_functions': [caller], 'source_files': sorted({s['source_provenance']['file'] for s in sites}), 'call_count': len(sites),
                       'occurrence_ids': [s['occurrence_id'] for s in sites], 'callee_spelling': name,
                       'candidate_argument_types': list(types), 'resolved_argument_types': None, 'cast_chain': None,
                       'callee_signature': None, 'callee_runtime_identity': None, 'resolution_mode': 'SOURCE_CONTEXT_CANDIDATE',
                       'caller_class': caller, 'session_user': 'AUTHENTIC_SLOT_UNPROVEN',
                       'effective_role': context['owner'] if context['security_mode'] == 'DEFINER' else 'INHERITED_CALL_EDGE_UNPROVEN',
                       'security_mode': context['security_mode'], 'function_owner': context['owner'], 'search_path': context['search_path'],
                       'required_schema_usage': 'UNPROVEN', 'required_execute': 'UNPROVEN', 'required_table_reads': 'UNPROVEN', 'required_helper_calls': 'UNPROVEN',
                       'strictness': None, 'volatility': None, 'result_sql_type': None, 'result_semantic_states': None,
                       'null_input_contract': 'UNPROVEN', 'null_internal_contract': 'UNPROVEN', 'missing_row_contract': 'UNPROVEN', 'duplicate_row_contract': 'UNPROVEN',
                       'authority_meaning': 'UNPROVEN', 'consumer_truth_mapping': 'UNPROVEN', 'consumer_trace_ids': [s['occurrence_id'] for s in sites],
                       'positive_fixture_case': None, 'negative_fixture_cases': [],
                       'grouping_equivalence_proven': False, 'grouping_boundary': 'Caller/effective context partition only; consumer/cast/NULL equivalence still open',
                       'static_resolution_status': 'CANDIDATE', 'runtime_resolution_status': 'UNPROVEN', 'semantic_status': 'UNBOUND',
                       'evidence_ids': ['source-function-contexts.json', 'source-occurrences.json.gz'],
                       'remaining_dimensions': ['exact runtime resolution/types/casts', 'complete security privilege chain', 'NULL authority consumers', 'grouping equivalence', 'ACTIVE positive fixture']})
    status = {'source_hash': q.SOURCE_HASH, 'call_sites': 15513, 'original_groups': 174, 'final_context_groups': len(ledger),
              'groups_split': sum(len({c['caller'] for c in calls if (c['callee_spelling'], tuple(c['argument_types']), c['explicit_variadic']) == key}) > 1 for key in old_groups),
              'groups_merged': 0, 'additional_context_groups': len(ledger) - 174,
              'bound_call_shapes': 0, 'unbound_call_shapes': len(ledger), 'consumer_structural_occurrences': len(traces), 'consumer_semantics_proven': 0,
              'function_contexts_required': len(contexts), 'function_contexts_static_recorded': len(contexts), 'function_contexts_fully_proven': 0,
              'source_column_acl_expected': len(expected_columns), 'source_column_acl_normative_equality': True,
              'call_binding_semantics_ready': False, 'null_semantics_ready': False, 'security_function_semantics_ready': False,
              'ACTIVE_FIXTURE_CONTRACT_READY': False, 'FULL_FIXTURE_READY': False,
              'B01_STATUS': 'OPEN', 'B02_STATUS': 'OPEN', 'B03_STATUS': 'OPEN', 'B06_STATUS': 'OPEN',
              'B04_STATUS': 'OPEN', 'B05_STATUS': 'OPEN', 'B07_STATUS': 'OPEN', 'B08_STATUS': 'OPEN',
              'null_authority_cases_required': 'UNKNOWN_REQUIRED_STATE_EXPANSION_NOT_PROVEN', 'null_authority_cases_proven': 0,
              'null_authority_cases_unproven': 'UNKNOWN', 'source_inputs': source_hashes, 'expanded_source_inputs': source_inputs}
    write(folder, 'semantic-ledger.json', {'schema_version': 1, 'records': ledger})
    (folder / 'source-occurrences.json.gz').write_bytes(gzip.compress(canon(occurrences), mtime=0))
    (folder / 'consumer-traces.json.gz').write_bytes(gzip.compress(canon(traces), mtime=0))
    write(folder, 'consumer-traces.json', {'structural_trace_occurrences': len(traces), 'semantically_proven_groups': 0, 'ledger': 'consumer-traces.json.gz', 'sha256': q.sha(canon(traces))})
    write(folder, 'source-function-contexts.json', contexts)
    write(folder, 'expected-acl-manifest.json', {'scope': 'INDEPENDENT_SOURCE_AND_SPEC_COLUMN_SUBMANIFEST_NOT_COMPLETE_EFFECTIVE_ACL',
          'complete_effective_manifest_ready': False, 'column_grants': [{'role': r, 'relation': t, 'column': c, 'privilege': p} for r, t, c, p in sorted(expected_columns)],
          'source_grant_revoke_operations': grant_operations, 'provenance': ['canonical V043 Git source', 'SPEC-0090 section22.4 exact normative rows'], 'normative_equality': True})
    write(folder, 'active-fixture-manifest.json', fixture_manifest())
    write(folder, 'null-authority-matrix.json', {'required_cases': None, 'proven_cases': 0,
          'taxonomy': ['TRUE', 'FALSE', 'NULL', 'ABSENT_ROW', 'MULTIPLE_ROWS', 'DENIED', 'INVALID_INPUT', 'NOT_APPLICABLE', 'EXPIRED', 'NOT_YET_VALID', 'UNPROVISIONED', 'INACTIVE', 'REVOKED', 'TERMINAL', 'UNKNOWN'],
          'provenance': ['SPEC-0090 sections2,3,12,17,25'], 'boundary': 'Applicability must be established per semantic consumer; taxonomy does not assign every state to every function',
          'cases': [], 'coverage_complete': False})
    wrappers = [s for s in v043 if not s.split('(')[0].split('.')[-1].startswith('offline_internal_') and not s.startswith('public.offline_lock_bound_principal(')]
    q.require(len(wrappers) == 18, 'Exact public wrapper denominator required')
    write(folder, 'positive-wrapper-results.json', {'expected_signatures': wrappers,
          'classification': {s: 'POSITIVE_REQUIRED' for s in wrappers}, 'authentic_positive_wrappers_expected': 18,
          'authentic_positive_wrappers_proven': 0, 'authentic_positive_wrappers_unproven': 18, 'positive_execution_allowed': False,
          'reason': 'ACTIVE fixture prerequisites not independently proven; no fabricated READY/binding/health/receipt state'})
    write(folder, 'READINESS.json', status)
    return status


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--parser-path', required=True); ap.add_argument('--output', required=True)
    args = ap.parse_args(); sys.path.insert(0, args.parser_path)
    from pglast.parser import parse_sql_json
    folder = Path(args.output); folder.mkdir(parents=True, exist_ok=False)
    status = build(folder, parse_sql_json)
    print(json.dumps({k: v for k, v in status.items() if k not in ['source_inputs', 'expanded_source_inputs']}))
