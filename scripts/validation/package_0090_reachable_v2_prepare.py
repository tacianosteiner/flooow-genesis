"""Ordered expected-input derivation; all values precede target observations."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/tmp/package0090-pglast-8.5'))
from pglast.parser import parse_sql_json
import package_0090_reachable_v2 as e
import package_0090_reachable_v2_coercions as coercions
import package_0090_reachable_v2_components as components
import package_0090_reachable_v2_integrity as integrity
import package_0090_reachable_v2_storage as storage
import package_0090_reachable_v2_privileges as privileges
import package_0090_reachable_v2_profiles as profiles
import package_0090_reachable_v2_annotations as annotations
import package_0090_reachable_v2_runtime as runtime
import package_0090_reachable_v2_catalog as catalog
import package_0090_reachable_v2_contracts as contracts
import package_0090_reachable_v2_consumers as consumers
import package_0090_reachable_v2_structure as structure
import package_0090_reachable_v2_attacks as attacks
import package_0090_reachable_v2_candidates as candidates

def prepare():
 e.q.require(not (e.OUT/'expected-currentness-manifest-v6.json').exists(),'Frozen evidence must not be regenerated in place; use a new governed release directory')
 r,sites=e.prepare(parse_sql_json)
 coercions.prepare(r)
 components.prepare(r,sites)
 integrity.prepare(r)
 storage.prepare(r)
 privileges.prepare(r)
 profiles.prepare(r)
 annotations.prepare(r)
 runtime.prepare(r,sites)
 catalog.prepare(r)
 contracts.prepare(r)
 consumers.prepare(r)
 structure.prepare(r)
 attacks.prepare(r)
 candidates.prepare(r)
 return r
if __name__=='__main__':prepare()
