"""Offline Package 0090 source gate. Never connects to or executes against a DB.

Install pglast==7.10 in an isolated directory, then supply --parser-path.
The parser uses PostgreSQL 17 grammar; parsing is not PostgreSQL 18 runtime proof.
Use --closure to require full implementation in addition to the prerequisite gate.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = Path("applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration")
V043 = MIGRATIONS / "V043__create_governed_offline_field_proof_capability_composition.sql"
SPEC = Path("docs/specifications/SPEC-0090-governed-offline-field-proof-exclusive-capability-composition.md")
BASELINE = "19131bb9cd655312252c8c83f0f78e7c0742274f"
OWNERS = {
    "V": "flooow_offline_verification_owner",
    "I": "flooow_offline_issuance_owner",
    "E": "flooow_offline_execution_owner",
    "A": "flooow_offline_audit_owner",
    "P": "flooow_offline_principal_lock_owner",
    "Q": "flooow_offline_readiness_owner",
    "Z": "flooow_offline_intent_audit_owner",
}
PRIVILEGES = {
    "READ_PRIVILEGE": "select",
    "LOCK_ENABLING_UPDATE_PRIVILEGE": "update",
    "BOOKKEEPING_INSERT": "insert",
    "BOOKKEEPING_UPDATE": "update",
}


def parse(source):
    import pglast
    from pglast.parser import parse_sql_json
    if pglast.__version__ != "v7.10":
        raise ValueError("Expected pinned pglast v7.10")
    statements = [s["stmt"] for s in json.loads(parse_sql_json(source))["stmts"]]
    # parse_sql checks SQL syntax; parse_plpgsql also checks DO body syntax.
    blocks = pglast.parse_plpgsql(source)
    return statements, blocks


def expected_column_grants(spec):
    expected = set()
    for line in spec.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 6 or cells[1] not in OWNERS or cells[4] not in PRIVILEGES:
            continue
        expected.add((OWNERS[cells[1]], cells[2], cells[3], PRIVILEGES[cells[4]]))
    if not expected:
        raise ValueError("Normative column grant inventory is empty")
    return expected


def inspect_precondition_bodies(blocks):
    """Inspect embedded SQL too: a DO body must not hide an effect or live role."""
    from pglast.parser import parse_sql_json

    def visit(node):
        if isinstance(node, list):
            for child in node:
                visit(child)
        elif isinstance(node, dict):
            if "PLpgSQL_stmt_dynexecute" in node:
                raise ValueError("Dynamic precondition SQL is forbidden")
            if "PLpgSQL_stmt_execsql" in node:
                query = node["PLpgSQL_stmt_execsql"]["sqlstmt"]["PLpgSQL_expr"]["query"]
                for raw in json.loads(parse_sql_json(query))["stmts"]:
                    statement = raw["stmt"]
                    if "SelectStmt" in statement:
                        if statement["SelectStmt"].get("intoClause"):
                            raise ValueError("Precondition SQL must not create a SELECT INTO relation")
                    elif "CreateRoleStmt" in statement:
                        role = statement["CreateRoleStmt"]
                        flags = {o["DefElem"]["defname"]: o["DefElem"]["arg"]
                                 for o in role.get("options", [])}
                        required = {k: {"Boolean": {"boolval": False}} for k in
                                    ("canlogin", "inherit", "superuser", "createdb", "createrole",
                                     "isreplication", "bypassrls")}
                        if role["role"] not in OWNERS.values() or flags != required:
                            raise ValueError("Unapproved role or role attributes in precondition SQL")
                    else:
                        raise ValueError("Precondition body contains unapproved SQL effect")
            for child in node.values():
                visit(child)

    visit(blocks)


def actual_column_grants(statements):
    grants = set()
    schema_usage=set()
    private_usage=set()
    for statement in statements:
        grant = statement.get("GrantStmt")
        if not grant or not grant.get("is_grant"):
            continue
        if grant["objtype"] == "OBJECT_FUNCTION":
            # Reviewed separately against the exact internal-P manifest, never ignored.
            continue
        if grant['objtype']=='OBJECT_SCHEMA':
            import package_0090_q_source as q
            if grant.get('grant_option') or grant.get('privileges')!=[{'AccessPriv':{'priv_name':'usage'}}] or grant['objects'] not in ([{'String':{'sval':'public'}}],[{'String':{'sval':'offline_crypto'}}]):
                raise ValueError('Unapproved schema grant')
            for r in grant['grantees']:
                name=r['RoleSpec'].get('rolename')
                if grant['objects']==[{'String':{'sval':'offline_crypto'}}]:
                    if name!=OWNERS['V'] or name in private_usage:raise ValueError('Only V exact private USAGE')
                    private_usage.add(name)
                    continue
                if name not in q.USAGE | {OWNERS['V'],OWNERS['I']} or name in schema_usage:raise ValueError('Unapproved/duplicate schema USAGE')
                schema_usage.add(name)
            continue
        if grant["objtype"] != "OBJECT_TABLE":
            raise ValueError("Prerequisite candidate contains an unexpected non-column grant")
        if grant.get("grant_option"):
            raise ValueError("Grant option is forbidden")
        for relation in grant["objects"]:
            rel = relation["RangeVar"]
            qualified = rel["schemaname"] + "." + rel["relname"]
            for grantee in grant["grantees"]:
                owner = grantee["RoleSpec"].get("rolename")
                if owner not in OWNERS.values():
                    raise ValueError("Unexpected grant recipient")
                if not grant.get("privileges"):
                    raise ValueError("Whole-table/ALL grant is forbidden")
                for privilege in grant["privileges"]:
                    priv = privilege["AccessPriv"]
                    if not priv.get("cols"):
                        raise ValueError("Whole-table grant is forbidden")
                    for column in priv["cols"]:
                        item = (owner, qualified, column["String"]["sval"], priv["priv_name"])
                        if item in grants:
                            raise ValueError("Duplicate physical column grant")
                        grants.add(item)
    q_present=any(s.get('CreateFunctionStmt',{}).get('funcname')==[{'String':{'sval':'public'}},{'String':{'sval':'offline_internal_readiness'}}] for s in statements)
    original_present=any(s.get('CreateFunctionStmt',{}).get('funcname')==[{'String':{'sval':'public'}},{'String':{'sval':'offline_internal_matches_original_signed_attestation'}}] for s in statements)
    issuance_present=any(s.get('CreateFunctionStmt',{}).get('funcname')==[{'String':{'sval':'public'}},{'String':{'sval':'offline_begin_principal'}}] for s in statements)
    if schema_usage != ((q.USAGE if q_present else set()) | ({OWNERS['V']} if original_present else set()) | ({OWNERS['I']} if issuance_present else set())):
        raise ValueError('Exact Q/A/E public USAGE prerequisites missing')
    from build_package_0090_v_bridge_source import NAME as v_name
    v_present=any(s.get('CreateFunctionStmt',{}).get('funcname')==[{'String':{'sval':'public'}},{'String':{'sval':v_name}}] for s in statements)
    if private_usage!=({OWNERS['V']} if v_present else set()):raise ValueError('Exact V-only private schema path missing')
    return grants


def prerequisite_checks(source, spec):
    statements, blocks = parse(source)
    import pglast
    preconditions = []
    for statement in statements:
        if 'DoStmt' in statement:
            body = next(a['DefElem']['arg']['String']['sval'] for a in statement['DoStmt']['args']
                        if a['DefElem']['defname'] == 'as')
            preconditions.extend(pglast.parse_plpgsql('DO $precondition$' + body + '$precondition$;'))
    inspect_precondition_bodies(preconditions)
    expected = expected_column_grants(spec)
    actual = actual_column_grants(statements)
    if expected != actual:
        raise ValueError("Column ACL mismatch: missing=" + repr(sorted(expected - actual))
                         + "; extra=" + repr(sorted(actual - expected)))
    first = statements[0].get("DoStmt")
    if not first:
        raise ValueError("First statement must be the incomplete-candidate interlock")
    body = first["args"][0]["DefElem"]["arg"]["String"]["sval"]
    if not re.fullmatch(r"\s*BEGIN\s+RAISE EXCEPTION USING ERRCODE = '55000',\s*"
                        r"MESSAGE = 'Package 0090 V043 implementation closure is incomplete; execution denied';\s*END;\s*", body):
        raise ValueError("Incomplete-candidate execution interlock is absent or conditional")
    for statement in statements:
        if not set(statement) <= {"DoStmt", "VariableSetStmt", "CreateStmt", "AlterTableStmt", "IndexStmt", "GrantStmt", "CreateFunctionStmt", "AlterOwnerStmt", "CreateTrigStmt"}:
            raise ValueError("Unapproved top-level SQL statement")
    admin = source.split("-- ADMIN: SPEC 24", 1)[1].split("-- T01", 1)[0]
    if re.search(r"\b(?:CREATE|ALTER) ROLE\b", admin, re.IGNORECASE):
        raise ValueError("ADMIN provisioning/repair is forbidden")
    if "OR NOT owner_role.rolinherit" not in admin or "IF NOT FOUND THEN\n        RAISE EXCEPTION" not in admin:
        raise ValueError("ADMIN missing-role/INHERIT prerequisite is incorrect")
    creates = [s["CreateStmt"] for s in statements if "CreateStmt" in s]
    scope = spec.split("### 24.2 Closed ownership and ACL scope", 1)[1].split("### 24.3", 1)[0]
    controls = set(re.findall(r"(?m)^- public\.(offline_[a-z_]+)$", scope))
    if len(controls) != 15 or len(creates) != 15 or any(c["relation"]["schemaname"] != "public" for c in creates) or {
        c["relation"]["relname"] for c in creates
    } != controls:
        raise ValueError("Control creation scope is not exactly 15 Package 0090 tables")
    for statement in statements:
        for kind in ("AlterTableStmt", "IndexStmt"):
            if kind in statement:
                relation = statement[kind]["relation"]
                if relation.get("schemaname") != "public" or relation["relname"] not in controls:
                    raise ValueError("DDL outside approved control tables is forbidden")
    policy = next(c for c in creates if c["relation"]["relname"] == "offline_deadline_policy")
    activation = next((c["ColumnDef"] for c in policy["tableElts"]
                       if "ColumnDef" in c and c["ColumnDef"]["colname"] == "effective_from"), None)
    if activation is None:
        raise ValueError("Required policy activation column is missing")
    if activation["typeName"]["names"] != [{"String": {"sval": "pg_catalog"}}, {"String": {"sval": "timestamptz"}}]:
        raise ValueError("Policy activation type is incorrect")
    typmods = activation["typeName"].get("typmods", [])
    if len(typmods) != 1 or typmods[0].get("A_Const", {}).get("ival", {}).get("ival") != 6:
        raise ValueError("Policy activation precision must be exactly six")
    constraints = {c["Constraint"]["contype"] for c in activation["constraints"]}
    if "CONSTR_NOTNULL" not in constraints or "CONSTR_DEFAULT" in constraints:
        raise ValueError("Activation must be explicit NOT NULL without DEFAULT")
    if len([g for g in actual if g[1:3] == ("public.offline_deadline_policy", "effective_from")]) != 7:
        raise ValueError("Activation column must have exactly seven approved grants")
    import package_0090_capability_source
    capability = package_0090_capability_source.check(statements, expected, source)
    return {"sql_statements": len(statements), "plpgsql_blocks": len(blocks),
            "exact_column_grants": len(actual), "control_tables": len(creates), **capability}


def closure_gaps(source, spec):
    # No source-only report promotes these implementation gaps to runtime evidence.
    missing = []
    # 18 public signatures + P/Q/Z/V bridge + the narrowly approved ADMIN trigger.
    closed_function_count = 24
    if len(re.findall(r"(?im)^CREATE(?: OR REPLACE)? FUNCTION public\.offline_", source)) != closed_function_count:
        missing.append("Operational public wrappers remain incomplete; P/Q/Z/V and S01-S04 have bounded review only")
    if not re.search(r"(?im)^CREATE(?: OR REPLACE)? FUNCTION public\.offline_internal_readiness\(", source):
        missing.append("Internal Q is absent; operational wrappers/guards remain incomplete")
    if len(re.findall(r"(?im)^CREATE(?: OR REPLACE)? FUNCTION public\.offline_", source)) != closed_function_count:
        missing.append("Wrapper transport and private decision commitment codecs/goldens are incomplete; fixture binding/catalog goldens do not close them")
    if len(re.findall(r"(?im)^CREATE(?: OR REPLACE)? FUNCTION public\.offline_", source)) != closed_function_count or not re.search(r"(?im)^GRANT EXECUTE ON FUNCTION", source):
        missing.append("Exact frozen/internal capability EXECUTE ACL closure is absent")
    approval = ('FIXTURE_ID=PACKAGE-0090-G3F-3B-FIXTURE-001',
                'POLICY_VERSION=fixture-1',
                'TAG28_PREFLIGHT_RECEIPT_TTL_US=1000000',
                'TAG29_PREFLIGHT_RECEIPT_TTL_APPROVED_MAX_US=2000000',
                'SCOPE=TEST_GOLDEN_REHEARSAL_ONLY',
                'PRODUCTION_POLICY_APPROVAL=NO', 'PRODUCTION_POLICY_PROVISIONING=NO',
                'APPROVAL_PROVENANCE=FLOOOW_TECHNICAL_FIXTURE_APPROVAL_2026-10-03')
    section = spec.split('## Independent technical test-fixture approval', 1)[-1]
    if not all(re.search(r'(?m)^' + re.escape(line) + r'\s*$', section) for line in approval):
        missing.append("Replacement normative fixture TTL/maximum approval is not supplied by the contract")
    return missing


def frozen_chain():
    manifest = {}
    for path in sorted((ROOT / MIGRATIONS).glob("V*.sql")):
        match = re.match(r"V(\d+)__", path.name)
        if not match or int(match[1]) > 42:
            continue
        relative = path.relative_to(ROOT).as_posix()
        baseline = subprocess.run(["git", "show", BASELINE + ":" + relative], cwd=ROOT,
                                  check=True, capture_output=True).stdout
        # Git normalizes working-tree CRLF; compare canonical repository bytes.
        current = path.read_bytes().replace(b"\r\n", b"\n")
        baseline = baseline.replace(b"\r\n", b"\n")
        if current != baseline:
            raise ValueError("Frozen migration changed: " + path.name)
        manifest[path.name] = hashlib.sha256(baseline).hexdigest()
    if len(manifest) != 42:
        raise ValueError("Expected all 42 immutable baseline migrations")
    return manifest


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--parser-path", type=Path, required=True)
    cli.add_argument("--closure", action="store_true")
    cli.add_argument("--output", type=Path)
    args = cli.parse_args()
    sys.path.insert(0, str(args.parser_path.resolve()))
    source = (ROOT / V043).read_text(encoding="utf-8-sig")
    spec = (ROOT / SPEC).read_text(encoding="utf-8-sig")
    try:
        checks = prerequisite_checks(source, spec)
        chain = frozen_chain()
        gaps = closure_gaps(source, spec)
        result = {
            "gate": "G3F.3B_SOURCE_PREREQUISITE_ALIGNMENT",
            "source_prerequisite_alignment": "PASS",
            "v043_implementation_and_contract_closure": "HOLD" if gaps else "NOT_PROVEN",
            "parser": "pglast 7.10 / PostgreSQL 17 grammar; not PG18 execution proof",
            "validation": checks, "frozen_v001_v042": "PASS", "frozen_sha256": chain,
            "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "spec_sha256": hashlib.sha256(spec.encode("utf-8")).hexdigest(),
            "unresolved_blocker_count": len(gaps), "unresolved_blockers": gaps,
            "v043_executed": False, "database_connection_attempted": False,
            "protected_database_mutation": False, "g3g_authorized": False,
        }
    except (ValueError, subprocess.CalledProcessError) as error:
        result = {"source_prerequisite_alignment": "FAIL", "error": str(error),
                  "database_connection_attempted": False}
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["source_prerequisite_alignment"] != "PASS" or args.closure else 0


if __name__ == "__main__":
    sys.exit(main())
