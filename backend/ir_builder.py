import ast


def build_ir(code):
    tree = ast.parse(code)
    return {
        "type": "program",
        "body": [stmt_to_ir(stmt) for stmt in tree.body]
    }


# ---------------- STATEMENTS ---------------- #

def stmt_to_ir(stmt):

    if isinstance(stmt, ast.FunctionDef):
        return {
            "type": "function",
            "name": stmt.name,
            "params": [a.arg for a in stmt.args.args],
            "body": [stmt_to_ir(s) for s in stmt.body]
        }

    if isinstance(stmt, ast.Assign):
        return {
            "type": "assign",
            "target": get_target(stmt.targets[0]),
            "value": expr_to_ir(stmt.value)
        }

    if isinstance(stmt, ast.Expr):
        return expr_to_ir(stmt.value)

    if isinstance(stmt, ast.Return):
        return {
            "type": "return",
            "value": expr_to_ir(stmt.value) if stmt.value else None
        }

    if isinstance(stmt, ast.If):
        return {
            "type": "if",
            "condition": expr_to_ir(stmt.test),
            "then": [stmt_to_ir(s) for s in stmt.body],
            "else": [stmt_to_ir(s) for s in stmt.orelse] if stmt.orelse else []
        }

    if isinstance(stmt, ast.For):
        return {
            "type": "for",
            "var": get_target(stmt.target),
            "iter": expr_to_ir(stmt.iter),
            "body": [stmt_to_ir(s) for s in stmt.body]
        }

    return {
        "type": "unknown_stmt",
        "value": str(type(stmt))
    }


# ---------------- EXPRESSIONS ---------------- #

def expr_to_ir(expr):

    if isinstance(expr, ast.BinOp):
        return {
            "type": "binary",
            "op": op(expr.op),
            "left": expr_to_ir(expr.left),
            "right": expr_to_ir(expr.right)
        }

    if isinstance(expr, ast.Compare):
        return {
            "type": "compare",
            "left": expr_to_ir(expr.left),
            "op": op(expr.ops[0]),
            "right": expr_to_ir(expr.comparators[0])
        }

    if isinstance(expr, ast.Name):
        return {
            "type": "var",
            "value": expr.id
        }

    if isinstance(expr, ast.Constant):
        return {
            "type": "const",
            "value": expr.value,
            "datatype": type(expr.value).__name__
        }

    if isinstance(expr, ast.Call):
        name = get_func_name(expr.func)

        if name == "print":
            return {
                "type": "print",
                "args": [expr_to_ir(a) for a in expr.args]
            }

        return {
            "type": "call",
            "name": name,
            "args": [expr_to_ir(a) for a in expr.args]
        }

    if isinstance(expr, ast.UnaryOp):
        return {
            "type": "unary",
            "op": op(expr.op),
            "operand": expr_to_ir(expr.operand)
        }

    return {
        "type": "unknown_expr",
        "value": str(type(expr))
    }


# ---------------- HELPERS ---------------- #

def get_target(t):
    if isinstance(t, ast.Name):
        return t.id
    elif isinstance(t, ast.Attribute):
        return t.attr
    elif isinstance(t, ast.Subscript):
        return "index_access"
    return "complex_target"


def get_func_name(func):
    if isinstance(func, ast.Name):
        return func.id
    elif isinstance(func, ast.Attribute):
        return func.attr
    return "unknown"


def op(o):
    if isinstance(o, ast.Add): return "+"
    if isinstance(o, ast.Sub): return "-"
    if isinstance(o, ast.Mult): return "*"
    if isinstance(o, ast.Div): return "/"
    if isinstance(o, ast.Mod): return "%"
    if isinstance(o, ast.Pow): return "**"

    # Comparisons
    if isinstance(o, ast.Eq): return "=="
    if isinstance(o, ast.NotEq): return "!="
    if isinstance(o, ast.Gt): return ">"
    if isinstance(o, ast.Lt): return "<"
    if isinstance(o, ast.GtE): return ">="
    if isinstance(o, ast.LtE): return "<="

    # Unary
    if isinstance(o, ast.USub): return "-"

    return "?"