import ast
import json
import pathlib
import sys

controller = pathlib.Path(sys.argv[1])
source = controller.read_text(encoding="utf-8")
tree = ast.parse(source)

records = {}

def add(name, line, mode, expression):
    records.setdefault(name, []).append({
        "line": line,
        "mode": mode,
        "expression": expression,
    })

def directory_literal(node):
    if not isinstance(node, ast.BinOp):
        return None
    if not isinstance(node.op, ast.Div):
        return None
    if not isinstance(node.left, ast.Name):
        return None
    if node.left.id != "directory":
        return None
    if not isinstance(node.right, ast.Constant):
        return None
    if not isinstance(node.right.value, str):
        return None
    return node.right.value

READ_METHODS = {
    "read_bytes",
    "read_text",
    "open",
    "exists",
    "stat",
}

WRITE_METHODS = {
    "write_bytes",
    "write_text",
    "touch",
    "mkdir",
    "unlink",
}

for node in ast.walk(tree):

    if isinstance(node, ast.Call):

        if isinstance(node.func, ast.Attribute):

            name = directory_literal(node.func.value)

            if name is not None:
                method = node.func.attr

                if method in READ_METHODS:
                    mode = "READ"
                elif method in WRITE_METHODS:
                    mode = "WRITE"
                else:
                    mode = "USE"

                add(
                    name,
                    getattr(node, "lineno", 0),
                    mode,
                    ast.get_source_segment(source, node) or "",
                )

    if isinstance(node, ast.BinOp):
        name = directory_literal(node)
        if name is not None:
            add(
                name,
                getattr(node, "lineno", 0),
                "PATH",
                ast.get_source_segment(source, node) or "",
            )

for name in sorted(records):
    events = sorted(records[name], key=lambda x: x["line"])
    print("FILE=" + name)
    for event in events:
        print(
            "EVENT="
            + str(event["line"])
            + "|"
            + event["mode"]
            + "|"
            + event["expression"].replace("\n", " ")[:300]
        )
    print()