"""Conservative source-order relation graph, explicitly not runtime lock-order proof."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / 'docs/evidence/package-0090-g3f4-typed-binding-dml/continuation-12/LOCK-SOURCE-EFFECTS.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    locks = json.loads(INPUT.read_text(encoding='utf-8'))
    functions = collections.defaultdict(list)
    graph, edges = collections.defaultdict(set), []
    for lock in locks:
        functions[lock['SOURCE_OBJECT']].append(lock)
    for function, seq in sorted(functions.items()):
        seq.sort(key=lambda x: x['STATEMENT_ORDINAL'])
        for before, after in zip(seq, seq[1:]):
            a, b = before['TARGET_RELATION'], after['TARGET_RELATION']
            if a == b:
                continue
            graph[a].add(b)
            edges.append({'from': a, 'to': b, 'function': function, 'before_lock_id': before['LOCK_ID'],
                          'after_lock_id': after['LOCK_ID'], 'runtime_order_proven': False})
    # Report mutual reachability components. Branches/loops/calls may change actual order.
    nodes = set(graph) | {v for s in graph.values() for v in s}
    def reaches(start):
        seen, pending = set(), list(graph[start])
        while pending:
            n = pending.pop()
            if n not in seen:
                seen.add(n)
                pending.extend(graph[n])
        return seen
    reach = {n: reaches(n) for n in nodes}
    components, used = [], set()
    for n in sorted(nodes):
        if n in used:
            continue
        component = sorted({n} | {m for m in nodes if m in reach[n] and n in reach[m]})
        used.update(component)
        if len(component) > 1:
            components.append(component)
    result = {'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(), 'explicit_lock_sites': len(locks),
              'modes': dict(collections.Counter(l['LOCK_STRENGTH'] for l in locks)), 'lock_bearing_functions': len(functions),
              'source_order_relation_edges': edges, 'potential_cycle_components': components,
              'LOCK_EDGE_CYCLE_UNEXPLAINED': 'UNKNOWN', 'RUNTIME_GLOBAL_LOCK_ORDER_PROVEN': False,
              'boundary': 'Source-order union only; NOT a global acquisition graph. Function calls, branch feasibility, loops, FK/index/advisory locks and transaction/isolation trajectories remain open.'}
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['explicit_lock_sites', 'modes', 'lock_bearing_functions', 'potential_cycle_components', 'LOCK_EDGE_CYCLE_UNEXPLAINED']}))


if __name__ == '__main__':
    main()
