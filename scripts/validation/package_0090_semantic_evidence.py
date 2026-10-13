"""Deterministically consolidate recorded foundation proof, without granting closure."""
import argparse
import json
from pathlib import Path
import package_0090_source_closure as q

ap = argparse.ArgumentParser(); ap.add_argument('--directory', required=True)
args = ap.parse_args(); folder = Path(args.directory).resolve()
r = json.loads((folder / 'foundation-runtime.json').read_text())
state = json.loads((folder / 'READINESS.json').read_text())
fixture = json.loads((folder / 'active-fixture-manifest.json').read_text())
unit = json.loads((folder / 'unit-tests.json').read_text())
q.require(not r['errors'] and len(r['cases']) == 93 and all(c['passed'] for c in r['cases']) and r['owned_runtime_destroyed'], 'Passing foundation and cleanup required')
q.require(unit['tests_run'] == 9 and unit['failures'] == 0 and unit['errors'] == 0, 'Executed unit proof required')
q.require(all(q.sha((folder / name).read_bytes()) == h for name, h in r['input_hashes'].items()), 'Runtime input drift')
q.require(all(q.sha((q.ROOT / 'scripts/validation' / name).read_bytes()) == h for name, h in r['recipe_hashes'].items()), 'Executed recipe drift')
q.require(state['call_sites'] == 15513 and state['final_context_groups'] == 818 and state['bound_call_shapes'] == 0, 'Exact candidate ledger required')
state.update({'scope_review': 'B01_B02_B03_B06', 'native_foundation_tests': 93, 'mutation_tests': 9, 'total_distinct_tests': 102,
              'final_failures': 0, 'scoped_blockers': 4, 'known_package_blocker_groups': 8,
              'scoped_high_count': 'UNKNOWN', 'scoped_medium_count': 'UNKNOWN', 'scoped_low_count': 'UNKNOWN',
              'function_catalog_properties_verified': 70, 'complete_function_security_contexts_proven': 0,
              'expected_column_grants_verified': 1040, 'complete_effective_acl_manifest_ready': False,
              'authentic_positive_wrappers_expected': 18, 'authentic_positive_wrappers_proven': 0, 'authentic_positive_wrappers_unproven': 18,
              'active_fixture_components_required': fixture['components_required'], 'active_fixture_input_declarations_present': fixture['components_present'],
              'active_fixture_components_missing': fixture['components_missing'], 'ACTIVE_FIXTURE_RECIPE_READY': False,
              'ACTIVE_FIXTURE_RECIPE_HASHED': 'BOUNDED_FOUNDATION_ONLY', 'canonical_v043_submitted': False,
              'canonical_v043_mutated': False, 'shared_database_contacted': False, 'production_contacted': False, 'next_executed': False})
(folder / 'READINESS.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
files = list(folder.rglob('*')) + [q.ROOT / 'docs/evidence/PACKAGE-0090-V043-semantic-ledger-active-fixture.md']
files += [q.ROOT / 'scripts/validation' / name for name in ['package_0090_active_foundation.py', 'package_0090_semantic_ledger.py',
          'package_0090_semantic_validator.py', 'test_package_0090_semantic_foundation.py', 'package_0090_semantic_evidence.py']]
entries = {p.relative_to(q.ROOT).as_posix(): {'sha256': q.sha(p.read_bytes()), 'bytes': p.stat().st_size}
           for p in sorted(files) if p.is_file() and p.name != 'SHA256-MANIFEST.json'}
(folder / 'SHA256-MANIFEST.json').write_text(json.dumps({'scope': 'BOUNDED_SOURCE_LEDGER_AND_FIXTURE_FOUNDATION_NOT_ACTIVE_CLOSURE', 'entries': entries}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'hash_entries': len(entries), 'distinct_tests': 102, 'active_fixture_ready': False}))
