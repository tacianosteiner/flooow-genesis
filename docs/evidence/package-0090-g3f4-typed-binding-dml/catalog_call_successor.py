"""Offline exact-signature catalog evidence; never treats a candidate as execution proof."""
import collections
import hashlib
import json
from pathlib import Path

from catalog_metadata import records

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "continuation-09/SCOPED-CALL-CANDIDATES.json"
CATALOG = ROOT / "continuation-02/pg18.4/pg_proc.dat"
OUT = ROOT / "continuation-13"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    calls = json.loads(INPUT.read_text(encoding="utf-8"))
    funcs = collections.defaultdict(list)
    for record in records(CATALOG.read_text(encoding="utf-8")):
        funcs[(record.get("proname"), tuple(record.get("proargtypes", "").split()))].append(record)

    groups = collections.defaultdict(list)
    for call in calls:
        key = (call["callee_spelling"], tuple(call["argument_types"]), call["explicit_variadic"])
        groups[key].append(call)

    output = []
    counts = collections.Counter()
    for (spelling, argtypes, variadic), sites in sorted(groups.items()):
        namespace, sep, name = spelling.rpartition(".")
        fully_qualified = bool(sep) and namespace == "pg_catalog"
        exact = funcs.get((name if sep else spelling, argtypes), []) if fully_qualified else []
        # An exact proargtypes match is only catalog evidence. SQL defaults,
        # special syntax, extension shadowing, polymorphism, ACL and execution
        # context are outside this bounded match.
        if not fully_qualified:
            result = "NAMESPACE_OR_SOURCE_FUNCTION_REVIEW_REQUIRED"
        elif variadic:
            result = "EXPLICIT_VARIADIC_REVIEW_REQUIRED"
        elif len(exact) == 1:
            result = "ONE_EXACT_PG_CATALOG_SIGNATURE_CANDIDATE"
        elif exact:
            result = "MULTIPLE_EXACT_CATALOG_SIGNATURES"
        else:
            result = "NO_EXACT_CATALOG_SIGNATURE"
        counts[result] += len(sites)
        output.append({
            "callee_spelling": spelling,
            "argument_types": list(argtypes),
            "explicit_variadic": variadic,
            "source_site_n": len(sites),
            "catalog_match_class": result,
            "catalog_oid_candidates": [r.get("oid") for r in exact],
            "catalog_signature_candidates": [
                {"oid": r.get("oid"), "proargtypes": r.get("proargtypes", ""),
                 "prorettype": r.get("prorettype"), "proisstrict": r.get("proisstrict", "f"),
                 "provolatile": r.get("provolatile", "v"),
                 "prosecdef": r.get("prosecdef", "f"), "provariadic": r.get("provariadic")}
                for r in exact
            ],
            "source_callers": dict(sorted(collections.Counter(s["caller"] for s in sites).items())),
            "example_source": sites[0]["original_source"],
            "full_execution_binding_complete": False,
        })

    OUT.mkdir(exist_ok=True)
    result = {
        "SOURCE_CALL_N": len(calls),
        "GROUPED_SIGNATURE_N": len(output),
        "MATCH_CLASS_SITE_COUNTS": dict(sorted(counts.items())),
        "EXACT_CATALOG_CANDIDATE_IS_NOT_EXECUTION_BINDING": True,
        "SOURCE_INPUT_SHA256": sha(INPUT),
        "CATALOG_INPUT_SHA256": sha(CATALOG),
        "BINDING_COMPLETE_N": 0,
        "BINDING_INCOMPLETE_N": len(calls),
        "OPERATOR_SITE_N": None,
        "CALL_OR_OPERATOR_BINDING_N": None,
        "NOT_EVALUATED": ["operator exact signatures", "overload ranking", "implicit casts",
                          "namespace search_path", "ACL EXECUTE", "security definer",
                          "installed catalog and extension runtime state"],
    }
    (OUT / "CATALOG-CALL-SIGNATURE-GROUPS.json").write_bytes((json.dumps(output, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    (OUT / "CATALOG-CALL-STATUS.json").write_bytes((json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
