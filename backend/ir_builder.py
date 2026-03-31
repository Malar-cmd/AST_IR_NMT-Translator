import ast


def build_ir(code):
    tree = ast.parse(code)
    return {
        "type": "program",
        "body": [stmt_to_ir(stmt) for stmt in tree.body]
    }


# ---------------- STATEMENTS ---------------- #

def stmt_to_ir(stmt):

    # ---------- FUNCTION ---------- #
    if isinstance(stmt, ast.FunctionDef):
        return {
            "type": "function",
            "name": stmt.name,
            "params": [a.arg for a in stmt.args.args],
            "body": [stmt_to_ir(s) for s in stmt.body]
        }

    # ---------- ASSIGN ---------- #
    if isinstance(stmt, ast.Assign):
        return {
            "type": "assign",
            "target": stmt.targets[0].id,
            "value": expr_to_ir(stmt.value)
        }

    # ---------- AUG ASSIGN ---------- #
    if isinstance(stmt, ast.AugAssign):
        return {
            "type": "aug_assign",
            "target": stmt.target.id,
            "op": op(stmt.op),
            "value": expr_to_ir(stmt.value)
        }

    # ---------- EXPRESSION ---------- #
    if isinstance(stmt, ast.Expr):
        return expr_to_ir(stmt.value)

    # ---------- RETURN ---------- #
    if isinstance(stmt, ast.Return):
        return {
            "type": "return",
            "value": expr_to_ir(stmt.value) if stmt.value else None
        }

    # ---------- IF ---------- #
    if isinstance(stmt, ast.If):
        return {
            "type": "if",
            "condition": expr_to_ir(stmt.test),
            "then": [stmt_to_ir(s) for s in stmt.body],
            "else": [stmt_to_ir(s) for s in stmt.orelse]
        }

    # ---------- FOR ---------- #
    if isinstance(stmt, ast.For):
        return {
            "type": "for",
            "var": stmt.target.id,
            "iter": expr_to_ir(stmt.iter),
            "body": [stmt_to_ir(s) for s in stmt.body]
        }

    # ---------- WHILE ---------- #
    if isinstance(stmt, ast.While):
        return {
            "type": "while",
            "condition": expr_to_ir(stmt.test),
            "body": [stmt_to_ir(s) for s in stmt.body]
        }

    return {"type": "unknown"}


# ---------------- EXPRESSIONS ---------------- #

def expr_to_ir(expr):

    # ---------- BINARY ---------- #
    if isinstance(expr, ast.BinOp):
        return {
            "type": "binary",
            "op": op(expr.op),
            "left": expr_to_ir(expr.left),
            "right": expr_to_ir(expr.right)
        }

    # ---------- VARIABLE ---------- #
    if isinstance(expr, ast.Name):
        return {
            "type": "var",
            "value": expr.id
        }

    # ---------- CONSTANT ---------- #
    if isinstance(expr, ast.Constant):
        value = expr.value
        return {
            "type": "const",
            "value": value,
            "datatype": infer_type(value)
        }

    # ---------- FUNCTION CALL ---------- #
    if isinstance(expr, ast.Call):

        # Handle print separately
        if isinstance(expr.func, ast.Name) and expr.func.id == "print":
            return {
                "type": "print",
                "args": [expr_to_ir(a) for a in expr.args]
            }

        return {
            "type": "call",
            "name": expr.func.id,
            "args": [expr_to_ir(a) for a in expr.args]
        }

    # ---------- COMPARISON ---------- #
    if isinstance(expr, ast.Compare):
        return {
            "type": "compare",
            "op": op(expr.ops[0]),
            "left": expr_to_ir(expr.left),
            "right": expr_to_ir(expr.comparators[0])
        }

    return {"type": "unknown"}


# ---------------- OPERATORS ---------------- #

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
    if isinstance(o, ast.Lt): return "<"
    if isinstance(o, ast.Gt): return ">"
    if isinstance(o, ast.LtE): return "<="
    if isinstance(o, ast.GtE): return ">="

    return "?"


# ---------------- TYPE INFERENCE ---------------- #

def infer_type(value):
    if isinstance(value, int): return "int"
    if isinstance(value, float): return "double"
    if isinstance(value, str): return "String"
    return "var"