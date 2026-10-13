"""Freeze collected bounded proof and keep every unproved promotion gate NO."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import package_0090_source_closure as q

ap = argparse.ArgumentParser()
ap.add_argument('--evidence-directory', required=True)
args = ap.parse_args()
folder = Path(args.evidence_directory).resolve()
r = json.loads((folder / 'qualification.json').read_text(encoding='utf-8'))
q.require(r['source']['sha256_git_lf'] == q.SOURCE_HASH and not r['canonical_mutated'], 'Unchanged exact source required')
q.require(r['body_qualified'] and not r['errors'] and r['owned_runtime_destroyed'], 'Passing bounded body proof and cleanup required')
q.require(all(c['passed'] for c in r['cases']) and len(r['cases']) == 315, 'Exact final campaign required')
q.require(all(q.sha((q.ROOT / p).read_bytes()) == h for p, h in r['recipe_sources'].items()), 'Executed recipe source drift')
status = {'scope': 'BOUNDED_PROOF_FULL_CLOSURE_NOT_ACHIEVED', 'baseline': r['baseline'],
          'source_hash': q.SOURCE_HASH, 'canonical_fence_present': True, 'canonical_source_mutated': False,
          'qualification_body_equivalent_except_fence': True, 'qualification_body_applied': True,
          'canonical_v043_migration_completed': False, 'call_sites': 15513, 'call_shapes': 174,
          'fully_bound_call_shapes': 0, 'unbound_call_shapes': 174, 'DML_TOTAL': 28,
          'DML_SEMANTICALLY_PROVEN': 0, 'DML_UNPROVEN': 28, 'explicit_lock_sites': 109,
          'lock_bearing_functions': 30, 'LOCK_EDGE_CYCLE_UNEXPLAINED': 'UNKNOWN',
          'source_semantics_ready': False, 'integrated_proof_ready': False, 'full_fixture_ready': False,
          'full_execution_recipes_ready': False, 'source_promotion_ready': False,
          'fence_removal_technically_eligible': False, 'fence_removal_authority_present': False,
          'active_restart_replay_ready': False, 'failure_injection_ready': False,
          'integrated_witness_executed': False, 'integrated_witness_independent': False,
          'known_blocker_groups': 8, 'full_review_high_count': 'UNKNOWN',
          'full_review_medium_count': 'UNKNOWN', 'full_review_low_count': 'UNKNOWN',
          'native_distinct_tests': len(r['cases']), 'boundary_distinct_tests': 5, 'total_distinct_tests': 320,
          'test_groups': dict(collections.Counter(c['group'] for c in r['cases'])), 'failures_final_campaign': 0,
          'concurrency_tests': 0, 'integrated_witness_tests': 0,
          'shared_database_contacted': False, 'production_contacted': False,
          'room_operational': False, 'execution_authority': 'BLOCKED', 'recovery_authority': 'BLOCKED',
          'next_executed': False}
(folder / 'READINESS.json').write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
inputs = list(folder.rglob('*'))
inputs += [p for p in (q.ROOT / 'scripts/validation').glob('*') if p.name in [
    'Package0090SourceClosureFlyway.java', 'package_0090_source_closure.py', 'package_0090_call_classifier.py',
    'package_0090_operator_census.py', 'package_0090_lock_graph.py', 'test_package_0090_source_closure.py',
    'package_0090_closure_manifest.py']]
inputs += [q.ROOT / 'docs/evidence/PACKAGE-0090-V043-semantic-integrated-closure.md',
           q.ROOT / 'docs/adr/ADR-0090-governed-offline-field-proof-exclusive-capability-composition.md',
           q.ROOT / 'docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md']
entries = {p.relative_to(q.ROOT).as_posix(): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
           for p in sorted(inputs) if p.is_file() and p.name != 'SHA256-MANIFEST.json'}
(folder / 'SHA256-MANIFEST.json').write_text(json.dumps({'scope': 'BOUND_RECORDED_SUBSET_NOT_FULL_EXECUTION_RECIPES', 'entries': entries}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'entries': len(entries), 'distinct_tests': 320, 'source_promotion_ready': False}))
