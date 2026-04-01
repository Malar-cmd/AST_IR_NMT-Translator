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

    # ---------- IF ---------- #
    if isinstance(stmt, ast.If):
        return {
            "type": "if",
            "condition": expr_to_ir(stmt.test),
            "then": [stmt_to_ir(s) for s in stmt.body],
            "else": [stmt_to_ir(s) for s in stmt.orelse]
        }

    # ---------- RETURN ---------- #
    if isinstance(stmt, ast.Return):
        return {
            "type": "return",
            "value": expr_to_ir(stmt.value) if stmt.value else None
        }

    # ---------- EXPRESSION ---------- #
    if isinstance(stmt, ast.Expr):
        return expr_to_ir(stmt.value)

    return {"type": "unknown"}


# ---------------- EXPRESSIONS ---------------- #

def expr_to_ir(expr):

    # ---------- CONSTANT ---------- #
    if isinstance(expr, ast.Constant):
        return {"type": "const", "value": expr.value}

    # ---------- VARIABLE ---------- #
    if isinstance(expr, ast.Name):
        return {"type": "var", "value": expr.id}

    # ---------- LIST ---------- #
    if isinstance(expr, ast.List):
        return {
            "type": "list",
            "elements": [expr_to_ir(e) for e in expr.elts]
        }

    # ---------- BINARY ---------- #
    if isinstance(expr, ast.BinOp):
        return {
            "type": "binary",
            "op": op(expr.op),
            "left": expr_to_ir(expr.left),
            "right": expr_to_ir(expr.right)
        }

    # ---------- COMPARE ---------- #
    if isinstance(expr, ast.Compare):
        return {
            "type": "compare",
            "op": op(expr.ops[0]),
            "left": expr_to_ir(expr.left),
            "right": expr_to_ir(expr.comparators[0])
        }

    # ---------- LAMBDA ---------- #
    if isinstance(expr, ast.Lambda):
        return {
            "type": "lambda",
            "params": [a.arg for a in expr.args.args],
            "body": expr_to_ir(expr.body)
        }

    # ---------- CALL ---------- #
    if isinstance(expr, ast.Call):

        # PRINT
        if isinstance(expr.func, ast.Name) and expr.func.id == "print":
            return {
                "type": "print",
                "args": [expr_to_ir(a) for a in expr.args]
            }

        # NORMAL FUNCTION
        if isinstance(expr.func, ast.Name):
            return {
                "type": "call",
                "name": expr.func.id,
                "args": [expr_to_ir(a) for a in expr.args]
            }

        # 🔥 METHOD CALL (FIXED)
        if isinstance(expr.func, ast.Attribute):
            return {
                "type": "method_call",
                "object": expr_to_ir(expr.func.value),
                "method": expr.func.attr,
                "args": [expr_to_ir(a) for a in expr.args]
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
    if isinstance(o, ast.LtE): return "<="
    if isinstance(o, ast.Gt): return ">"
    if isinstance(o, ast.GtE): return ">="

    return "?"