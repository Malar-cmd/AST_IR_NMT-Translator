# ---------------- GLOBAL STATE ---------------- #

declared_vars = set()
symbol_table = {}


# ---------------- MAIN ---------------- #

def ir_to_java(ir):

    global declared_vars, symbol_table
    declared_vars = set()
    symbol_table = {}

    code = []

    # Functions first
    for stmt in ir["body"]:
        if stmt["type"] == "function":
            code.append(function_to_java(stmt))

    # Then main-level statements
    for stmt in ir["body"]:
        if stmt["type"] != "function":
            code.extend(stmt_to_java(stmt))

    return "\n".join(code)


# ---------------- STATEMENTS ---------------- #

def stmt_to_java(stmt):

    global declared_vars, symbol_table
    t = stmt["type"]

    # ---------- ASSIGN ---------- #
    if t == "assign":
        var = stmt["target"]
        value = expr(stmt["value"])
        value_type = infer_expr_type(stmt["value"])

        if var in declared_vars:
            symbol_table[var] = value_type
            return [f"{var} = {value};"]
        else:
            declared_vars.add(var)
            symbol_table[var] = value_type
            return [f"{value_type} {var} = {value};"]

    # ❌ REMOVED aug_assign (normalized IR handles it)

    # ---------- PRINT ---------- #
    if t == "print":
        args = ", ".join(expr(a) for a in stmt["args"])
        return [f"System.out.println({args});"]

    # ---------- CALL ---------- #
    if t == "call":
        args = ", ".join(expr(a) for a in stmt["args"])
        return [f"{stmt['name']}({args});"]

    # ---------- RETURN ---------- #
    if t == "return":
        if stmt.get("value") is not None:
            return [f"return {expr(stmt['value'])};"]
        return ["return;"]

    # ---------- IF ---------- #
    if t == "if":
        lines = [f"if ({expr(stmt['condition'])}) {{"]

        for s in stmt["then"]:
            lines.extend(indent_list(stmt_to_java(s), 1))

        lines.append("}")

        if stmt["else"]:
            lines.append("else {")
            for s in stmt["else"]:
                lines.extend(indent_list(stmt_to_java(s), 1))
            lines.append("}")

        return lines

    # 🔥 ---------- NORMALIZED FOR LOOP ---------- #
    if t == "for":

        init_stmt = stmt["init"]
        condition = expr(stmt["condition"])
        update_stmt = stmt["update"]

        # Convert init & update
        init_line = stmt_to_java(init_stmt)[0].replace(";", "")
        update_line = stmt_to_java(update_stmt)[0].replace(";", "")

        lines = [f"for ({init_line}; {condition}; {update_line}) {{"]

        for s in stmt["body"]:
            lines.extend(indent_list(stmt_to_java(s), 1))

        lines.append("}")

        return lines

    # ---------- WHILE ---------- #
    if t == "while":
        return [
            f"while ({expr(stmt['condition'])}) {{",
            *indent_list(flatten([stmt_to_java(s) for s in stmt["body"]]), 1),
            "}"
        ]

    return ["// unsupported"]


# ---------------- EXPRESSIONS ---------------- #

def expr(e):

    t = e["type"]

    if t == "binary":
        if e["op"] == "**":
            return f"Math.pow({expr(e['left'])}, {expr(e['right'])})"
        return f"{expr(e['left'])} {e['op']} {expr(e['right'])}"

    if t == "compare":
        return f"{expr(e['left'])} {e['op']} {expr(e['right'])}"

    if t == "var":
        return e["value"]

    if t == "const":
        if isinstance(e["value"], str):
            return f"\"{e['value']}\""
        return str(e["value"])

    if t == "call":
        args = ", ".join(expr(a) for a in e["args"])
        return f"{e['name']}({args})"

    return "null"


# ---------------- TYPE INFERENCE ---------------- #

def infer_expr_type(e):

    global symbol_table
    t = e["type"]

    if t == "const":
        v = e["value"]
        if isinstance(v, int): return "int"
        if isinstance(v, float): return "double"
        if isinstance(v, str): return "String"

    if t == "var":
        return symbol_table.get(e["value"], "var")

    if t == "binary":
        left = infer_expr_type(e["left"])
        right = infer_expr_type(e["right"])

        if left == "String" or right == "String":
            return "String"

        if left == "double" or right == "double":
            return "double"

        return "int"

    if t == "call":
        return "int"

    return "var"


# ---------------- FUNCTIONS ---------------- #

def function_to_java(func):

    global declared_vars, symbol_table

    old_declared = declared_vars.copy()
    old_symbols = symbol_table.copy()

    declared_vars = set(func["params"])
    symbol_table = {p: "unknown" for p in func["params"]}

    param_types = infer_param_types(func)

    for p in param_types:
        symbol_table[p] = param_types[p]

    return_type = infer_function_return(func)

    params = ", ".join(f"{param_types[p]} {p}" for p in func["params"])

    lines = [f"public static {return_type} {func['name']}({params}) {{"]

    for s in func["body"]:
        lines.extend(indent_list(stmt_to_java(s), 1))

    lines.append("}")

    declared_vars = old_declared
    symbol_table = old_symbols

    return "\n".join(lines)


# ---------------- PARAM TYPE INFERENCE ---------------- #

def infer_param_types(func):

    local_types = {p: "unknown" for p in func["params"]}

    def scan_expr(e):
        if not e:
            return

        if e["type"] == "binary":
            scan_expr(e["left"])
            scan_expr(e["right"])

        elif e["type"] == "call":
            for a in e["args"]:
                scan_expr(a)

    for stmt in func["body"]:
        if stmt["type"] == "return":
            scan_expr(stmt["value"])
        elif stmt["type"] == "print":
            for a in stmt["args"]:
                scan_expr(a)

    for k in local_types:
        if local_types[k] == "unknown":
            local_types[k] = "int"

    return local_types


# ---------------- RETURN TYPE ---------------- #

def infer_function_return(func):

    for stmt in func["body"]:
        if stmt["type"] == "return":
            if stmt["value"]:
                return infer_expr_type(stmt["value"])

    return "void"


# ---------------- HELPERS ---------------- #

def indent_list(lines, level):
    pad = "    " * level
    return [pad + line for line in lines]


def flatten(lst):
    result = []
    for item in lst:
        result.extend(item)
    return result