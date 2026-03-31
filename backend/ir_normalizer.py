def normalize_ir(ir):
    return {
        "type": "program",
        "body": [normalize_stmt(s) for s in ir["body"]]
    }


# ---------------- STATEMENTS ---------------- #

def normalize_stmt(stmt):

    t = stmt["type"]

    # ---------- FUNCTION ---------- #
    if t == "function":
        return {
            "type": "function",
            "name": stmt["name"],
            "params": stmt["params"],
            "body": [normalize_stmt(s) for s in stmt["body"]]
        }

    # ---------- ASSIGN ---------- #
    if t == "assign":
        return {
            "type": "assign",
            "target": stmt["target"],
            "value": normalize_expr(stmt["value"])
        }

    # 🔥 ---------- AUG ASSIGN → ASSIGN ---------- #
    if t == "aug_assign":
        return {
            "type": "assign",
            "target": stmt["target"],
            "value": {
                "type": "binary",
                "op": stmt["op"],
                "left": {"type": "var", "value": stmt["target"]},
                "right": normalize_expr(stmt["value"])
            }
        }

    # ---------- PRINT ---------- #
    if t == "print":
        return {
            "type": "print",
            "args": [normalize_expr(a) for a in stmt["args"]]
        }

    # ---------- CALL ---------- #
    if t == "call":
        return {
            "type": "call",
            "name": stmt["name"],
            "args": [normalize_expr(a) for a in stmt["args"]]
        }

    # ---------- RETURN ---------- #
    if t == "return":
        return {
            "type": "return",
            "value": normalize_expr(stmt["value"]) if stmt["value"] else None
        }

    # ---------- IF ---------- #
    if t == "if":
        return {
            "type": "if",
            "condition": normalize_expr(stmt["condition"]),
            "then": [normalize_stmt(s) for s in stmt["then"]],
            "else": [normalize_stmt(s) for s in stmt["else"]]
        }

    # 🔥 ---------- FOR (range → C-style) ---------- #
    if t == "for":
        iter_expr = stmt["iter"]

        if iter_expr["type"] == "call" and iter_expr["name"] == "range":
            args = iter_expr["args"]

            if len(args) == 1:
                start = {"type": "const", "value": 0}
                end = normalize_expr(args[0])
            elif len(args) == 2:
                start = normalize_expr(args[0])
                end = normalize_expr(args[1])
            else:
                return stmt  # fallback

            var = stmt["var"]

            return {
                "type": "for",
                "init": {
                    "type": "assign",
                    "target": var,
                    "value": start
                },
                "condition": {
                    "type": "compare",
                    "op": "<",
                    "left": {"type": "var", "value": var},
                    "right": end
                },
                "update": {
                    "type": "assign",
                    "target": var,
                    "value": {
                        "type": "binary",
                        "op": "+",
                        "left": {"type": "var", "value": var},
                        "right": {"type": "const", "value": 1}
                    }
                },
                "body": [normalize_stmt(s) for s in stmt["body"]]
            }

    # ---------- WHILE ---------- #
    if t == "while":
        return {
            "type": "while",
            "condition": normalize_expr(stmt["condition"]),
            "body": [normalize_stmt(s) for s in stmt["body"]]
        }

    return stmt


# ---------------- EXPRESSIONS ---------------- #

def normalize_expr(expr):

    t = expr["type"]

    if t == "binary":
        return {
            "type": "binary",
            "op": expr["op"],
            "left": normalize_expr(expr["left"]),
            "right": normalize_expr(expr["right"])
        }

    if t == "compare":
        return {
            "type": "compare",
            "op": expr["op"],
            "left": normalize_expr(expr["left"]),
            "right": normalize_expr(expr["right"])
        }

    if t == "call":
        return {
            "type": "call",
            "name": expr["name"],
            "args": [normalize_expr(a) for a in expr["args"]]
        }

    if t in ["var", "const"]:
        return expr

    return expr