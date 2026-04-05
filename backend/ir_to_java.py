declared_vars = set()
symbol_table = {}

METHOD_MAP = {
    "append": "add",
    "pop": "remove",
    "insert": "add",
    "clear": "clear",

    "upper": "toUpperCase",
    "lower": "toLowerCase",
    "strip": "trim",
    "replace": "replace",
}


def reset_translation_state():
    global declared_vars, symbol_table
    declared_vars = set()
    symbol_table = {}


def to_wrapper_type(t):
    return {
        "int": "Integer",
        "double": "Double",
        "float": "Float",
        "char": "Character",
        "boolean": "Boolean"
    }.get(t, t)


def ir_to_java(ir, preserve_state=False):
    global declared_vars, symbol_table

    if not preserve_state:
        declared_vars = set()
        symbol_table = {}

    code = []

    for stmt in ir["body"]:
        if stmt["type"] == "function":
            code.append(function_to_java(stmt))
        else:
            code.extend(stmt_to_java(stmt))

    return "\n".join(code)


def stmt_to_java(stmt):
    global declared_vars, symbol_table
    t = stmt["type"]

    if t == "assign":
        var = stmt["target"]
        value_obj = stmt["value"]

        if value_obj.get("type") == "list":
            elements = value_obj.get("elements", [])
            elem_type = to_wrapper_type(infer_list_type(elements))

            vals = ", ".join(expr(e) for e in elements)

            if var in declared_vars:
                return [f"{var} = new ArrayList<>(Arrays.asList({vals}));"]

            declared_vars.add(var)
            symbol_table[var] = f"List<{elem_type}>"

            if not elements:
                return [f"List<{elem_type}> {var} = new ArrayList<>();"]

            return [f"List<{elem_type}> {var} = new ArrayList<>(Arrays.asList({vals}));"]

        value = expr(value_obj)

        if var in declared_vars:
            return [f"{var} = {value};"]

        value_type = infer_expr_type(value_obj)

        declared_vars.add(var)
        symbol_table[var] = value_type

        return [f"{value_type} {var} = {value};"]

    if t == "print":
        args = " + \" \" + ".join(expr(a) for a in stmt["args"])
        return [f"System.out.println({args});"]

    if t == "append":
        return [f"{stmt['target']}.add({expr(stmt['value'])});"]

    if t == "method_call":
        obj = expr(stmt["object"])
        method = METHOD_MAP.get(stmt["method"], stmt["method"])
        args = ", ".join(expr(a) for a in stmt["args"])
        return [f"{obj}.{method}({args});"]

    if t == "if":
        lines = [f"if ({expr(stmt['condition'])}) {{"]

        for s in stmt["then"]:
            lines.extend(indent_list(stmt_to_java(s), 1))

        lines.append("}")

        if stmt.get("else"):
            lines.append("else {")
            for s in stmt["else"]:
                lines.extend(indent_list(stmt_to_java(s), 1))
            lines.append("}")

        return lines

    if t == "for":

        if "init" in stmt:
            init = stmt_to_java(stmt["init"])[0].replace(";", "")
            cond = expr(stmt["condition"])
            update = stmt_to_java(stmt["update"])[0].replace(";", "")

            lines = [f"for ({init}; {cond}; {update}) {{"]

            for s in stmt["body"]:
                lines.extend(indent_list(stmt_to_java(s), 1))

            lines.append("}")
            return lines

        elif "iter" in stmt:
            var = stmt["var"]
            iterable = expr(stmt["iter"])

            if isinstance(stmt["iter"], dict) and stmt["iter"]["type"] == "var":
                list_name = stmt["iter"]["value"]
                list_type = symbol_table.get(list_name, "Object")

                if list_type.startswith("List<"):
                    var_type = list_type.replace("List<", "").replace(">", "")
                else:
                    var_type = "Object"
            else:
                var_type = "Object"

            if var not in declared_vars:
                declared_vars.add(var)
                header = f"for ({var_type} {var} : {iterable}) {{"
            else:
                header = f"for ({var} : {iterable}) {{"

            lines = [header]

            for s in stmt["body"]:
                lines.extend(indent_list(stmt_to_java(s), 1))

            lines.append("}")
            return lines

        return ["// unsupported for-loop"]

    if t == "for_each":
        var = stmt["var"]
        iterable = expr(stmt["iter"])

        if isinstance(stmt["iter"], dict) and stmt["iter"]["type"] == "var":
            list_name = stmt["iter"]["value"]
            list_type = symbol_table.get(list_name, "Object")

            if list_type.startswith("List<"):
                var_type = list_type.replace("List<", "").replace(">", "")
            else:
                var_type = "Object"
        else:
            var_type = "Object"

        if var not in declared_vars:
            declared_vars.add(var)
            header = f"for ({var_type} {var} : {iterable}) {{"
        else:
            header = f"for ({var} : {iterable}) {{"

        lines = [header]

        for s in stmt["body"]:
            lines.extend(indent_list(stmt_to_java(s), 1))

        lines.append("}")
        return lines

    if t == "while":
        return [
            f"while ({expr(stmt['condition'])}) {{",
            *indent_list(flatten([stmt_to_java(s) for s in stmt["body"]]), 1),
            "}"
        ]

    if t == "return":
        if stmt.get("value"):
            return [f"return {expr(stmt['value'])};"]
        return ["return;"]

    return ["// unsupported"]


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
        if e["name"] == "len":
            return f"{expr(e['args'][0])}.size()"
        args = ", ".join(expr(a) for a in e["args"])
        return f"{e['name']}({args})"

    if t == "method_call":
        obj = expr(e["object"])
        method = METHOD_MAP.get(e["method"], e["method"])
        args = ", ".join(expr(a) for a in e["args"])
        return f"{obj}.{method}({args})"

    return "null"


def infer_expr_type(e):
    t = e["type"]

    if t == "const":
        v = e["value"]
        if isinstance(v, int): return "int"
        if isinstance(v, float): return "double"
        if isinstance(v, str): return "String"

    if t == "binary":
        l = infer_expr_type(e["left"])
        r = infer_expr_type(e["right"])

        if "String" in (l, r): return "String"
        if "double" in (l, r): return "double"
        return "int"

    if t == "call":
        return "int"

    return "Object"


def infer_list_type(elements):
    if not elements:
        return "Object"

    types = set(infer_expr_type(e) for e in elements)

    if len(types) == 1:
        return list(types)[0]

    return "Object"


def function_to_java(func):
    global declared_vars, symbol_table

    old_declared = declared_vars.copy()
    old_symbols = symbol_table.copy()

    declared_vars = set(func["params"])
    symbol_table = {p: "Object" for p in func["params"]}

    params = ", ".join(f"Object {p}" for p in func["params"])
    return_type = "Object"

    lines = [f"public static {return_type} {func['name']}({params}) {{"]

    for s in func["body"]:
        lines.extend(indent_list(stmt_to_java(s), 1))

    lines.append("}")

    declared_vars = old_declared
    symbol_table = old_symbols

    return "\n".join(lines)


def indent_list(lines, level):
    pad = "    " * level
    return [pad + line for line in lines]


def flatten(lst):
    result = []
    for item in lst:
        result.extend(item)
    return result