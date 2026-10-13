"""Static DDL/PLpgSQL/FK checks only; never connects to or qualifies PostgreSQL."""
import argparse
import json
import re
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--parser-path", type=Path, help="Directory containing pglast 8.5")
args = parser.parse_args()
if args.parser_path:
    sys.path.insert(0, str(args.parser_path.resolve()))
try:
    import pglast
    from pglast import ast, enums, parse_sql
except ImportError as error:
    raise SystemExit("Install pglast==8.5 into a temporary directory and pass --parser-path") from error

root = Path(__file__).resolve().parents[2]
blueprint = root / "docs/specifications/SPEC-0091-historical-lineage-ddl-blueprint.md"
blocks = re.findall(r"```sql\n(.*?)```", blueprint.read_text(encoding="utf-8"), re.S)
if len(blocks) != 1:
    raise SystemExit("Expected exactly one candidate SQL block")
sql = blocks[0]
statements = parse_sql(sql)
functions = re.findall(r"CREATE FUNCTION .*?\$\$;", sql, re.S)
for function in functions:
    pglast.parse_plpgsql(function)
for kind, name in re.findall(r"(CONSTRAINT|TRIGGER|INDEX)\s+([a-z_][a-z_0-9]*)", sql):
    if len(name.encode("utf-8")) > 63:
        raise SystemExit(f"Truncated {kind} name: {name}")

tables = {}
foreign_keys = []
def strings(values):
    return tuple(value.sval for value in values or ())

def constraint(table, value, column=None):
    if value.contype in (enums.ConstrType.CONSTR_PRIMARY, enums.ConstrType.CONSTR_UNIQUE):
        tables[table]["keys"].add(strings(value.keys) or (column,))
    if value.contype == enums.ConstrType.CONSTR_FOREIGN:
        foreign_keys.append((table, value))

def ingest(source):
    for raw in parse_sql(source):
        statement = raw.stmt
        if isinstance(statement, ast.CreateStmt):
            name = statement.relation.relname
            tables[name] = {"columns": {}, "keys": set()}
            for item in statement.tableElts or ():
                if isinstance(item, ast.ColumnDef):
                    tables[name]["columns"][item.colname] = strings(item.typeName.names)
                    for value in item.constraints or ():
                        constraint(name, value, item.colname)
                elif isinstance(item, ast.Constraint):
                    constraint(name, item)
        elif isinstance(statement, ast.AlterTableStmt):
            name = statement.relation.relname
            if name not in tables:
                continue
            for command in statement.cmds:
                definition = command.def_
                if isinstance(definition, ast.ColumnDef):
                    tables[name]["columns"][definition.colname] = strings(definition.typeName.names)
                elif isinstance(definition, ast.Constraint):
                    constraint(name, definition)

migration_root = root / "applications/marketplace-operations-persistence-postgres/src/main/resources/db/migration"
for filename in ("V015__create_independent_marketplace_economic_evidence.sql",
                 "V018__create_marketplace_sales_intelligence_projection.sql"):
    ingest((migration_root / filename).read_text(encoding="utf-8"))
foreign_keys.clear()
ingest(sql)
resolved = []
for table, value in foreign_keys:
    target = value.pktable.relname
    local, remote = strings(value.fk_attrs), strings(value.pk_attrs)
    if len(local) != len(remote) or remote not in tables[target]["keys"]:
        raise SystemExit(f"No exact unique FK target: {value.conname}")
    for left, right in zip(local, remote):
        if tables[table]["columns"][left] != tables[target]["columns"][right]:
            raise SystemExit(f"FK column/type mismatch: {value.conname}")
    resolved.append(value.conname)
print(json.dumps({"parser": pglast.__version__, "sql_statements": len(statements),
    "plpgsql_functions": len(functions), "candidate_fks_resolved": len(resolved),
    "resolved_names": resolved, "identifier_length_check": "PASS",
    "source_scope": "V015/V018 declared schema plus candidate DDL",
    "POSTGRES_EXECUTION": "NOT_PERFORMED", "DDL_GATE": "DESIGN_ONLY"}, indent=2))
