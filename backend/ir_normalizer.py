def normalize_ir(ir):
    return {
        "type": "program",
        "body": flatten([normalize_stmt(s) for s in ir["body"]])
    }


# ---------------- STATEMENTS ---------------- #

def normalize_stmt(stmt):

    t = stmt["type"]

    # ---------- FUNCTION ---------- #
    if t == "function":
        return [{
            "type": "function",
            "name": stmt["name"],
            "params": stmt["params"],
            "body": flatten([normalize_stmt(s) for s in stmt["body"]])
        }]

    # ---------- ASSIGN ---------- #
    if t == "assign":

        val = stmt["value"]

        # 🔥 HANDLE list(map(...)) / list(filter(...))
        if val["type"] == "call" and val["name"] == "list":
            inner = val["args"][0]

            # ---------- MAP ---------- #
            if inner["type"] == "call" and inner["name"] == "map":
                func = inner["args"][0]
                iterable = normalize_expr(inner["args"][1])
                var = "x"

                return [
                    {
                        "type": "assign",
                        "target": stmt["target"],
                        "value": {"type": "list_init"}
                    },
                    {
                        "type": "for_each",
                        "var": var,
                        "iter": iterable,
                        "body": [
                            {
                                "type": "append",
                                "target": stmt["target"],
                                "value": normalize_lambda(func, var)
                            }
                        ]
                    }
                ]

            # ---------- FILTER ---------- #
            if inner["type"] == "call" and inner["name"] == "filter":
                func = inner["args"][0]
                iterable = normalize_expr(inner["args"][1])
                var = "x"

                return [
                    {
                        "type": "assign",
                        "target": stmt["target"],
                        "value": {"type": "list_init"}
                    },
                    {
                        "type": "for_each",
                        "var": var,
                        "iter": iterable,
                        "body": [
                            {
                                "type": "if",
                                "condition": normalize_lambda(func, var),
                                "then": [
                                    {
                                        "type": "append",
                                        "target": stmt["target"],
                                        "value": {"type": "var", "value": var}
                                    }
                                ],
                                "else": []
                            }
                        ]
                    }
                ]

        return [{
            "type": "assign",
            "target": stmt["target"],
            "value": normalize_expr(stmt["value"])
        }]

    # ---------- PRINT ---------- #
    if t == "print":
        return [{
            "type": "print",
            "args": [normalize_expr(a) for a in stmt["args"]]
        }]

    # ---------- IF ---------- #
    if t == "if":
        return [{
            "type": "if",
            "condition": normalize_expr(stmt["condition"]),
            "then": flatten([normalize_stmt(s) for s in stmt["then"]]),
            "else": flatten([normalize_stmt(s) for s in stmt["else"]])
        }]

    # ---------- FOR RANGE ---------- #
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
                return [stmt]

            var = stmt["var"]

            return [{
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
                "body": flatten([normalize_stmt(s) for s in stmt["body"]])
            }]

    return [stmt]


# ---------------- EXPRESSIONS ---------------- #

def normalize_expr(expr):

    if expr["type"] in ["var", "const"]:
        return expr

    if expr["type"] == "binary":
        return {
            "type": "binary",
            "op": expr["op"],
            "left": normalize_expr(expr["left"]),
            "right": normalize_expr(expr["right"])
        }

    if expr["type"] == "compare":
        return {
            "type": "compare",
            "op": expr["op"],
            "left": normalize_expr(expr["left"]),
            "right": normalize_expr(expr["right"])
        }

    return expr


# ---------------- LAMBDA ---------------- #

def normalize_lambda(func, var):

    if func["type"] == "lambda":
        body = func["body"]
        param = func["params"][0]
        return substitute_var(normalize_expr(body), param, var)

    return {"type": "var", "value": var}


def substitute_var(expr, old, new):

    if expr["type"] == "var" and expr["value"] == old:
        return {"type": "var", "value": new}

    if expr["type"] in ["binary", "compare"]:
        return {
            "type": expr["type"],
            "op": expr["op"],
            "left": substitute_var(expr["left"], old, new),
            "right": substitute_var(expr["right"], old, new)
        }

    return expr


# ---------------- HELPERS ---------------- #

def flatten(lst):
    result = []
    for item in lst:
        result.extend(item)
    return result