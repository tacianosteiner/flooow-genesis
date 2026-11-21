import ast
import pathlib
import sys

controller = pathlib.Path(sys.argv[1])
source = controller.read_text(encoding="utf-8")
tree = ast.parse(source)

def render(node):
    try:
        return ast.get_source_segment(source, node) or ""
    except Exception:
        return ""

def output_path(node):
    """
    Recover a static path rooted at variable 'output':
      output / "a"
      output / "a/b"
      output / "a" / "b"
    """
    parts = []

    cur = node

    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):

        right = cur.right

        if not (
            isinstance(right, ast.Constant)
            and isinstance(right.value, str)
        ):
            return None

        parts.insert(0, right.value)
        cur = cur.left

    if isinstance(cur, ast.Name) and cur.id == "output":
        return "/".join(parts)

    return None

events = []

for node in ast.walk(tree):

    if not isinstance(node, ast.Call):
        continue

    if not isinstance(node.func, ast.Attribute):
        continue

    path = output_path(node.func.value)

    if path is None:
        continue

    method = node.func.attr

    if method in {
        "read_bytes",
        "read_text",
        "open",
        "stat",
        "exists",
    }:
        mode = "READ"

    elif method in {
        "write_bytes",
        "write_text",
        "touch",
        "unlink",
        "mkdir",
    }:
        mode = "WRITE"

    else:
        mode = "USE"

    events.append((
        getattr(node, "lineno", 0),
        mode,
        path,
        render(node).replace("\n", " ")[:400],
    ))

for line, mode, path, expression in sorted(events):
    print(f"{line}|{mode}|{path}|{expression}")