def ir_to_sequence(ir):

    lines = []

    for stmt in ir["body"]:
        lines.extend(stmt_to_seq(stmt))

    return "\n".join(lines)


def stmt_to_seq(stmt):

    t = stmt["type"]

    if t == "assign":
        return [f"ASSIGN {stmt['target']} {expr_to_seq(stmt['value'])}"]

    if t == "print":
        args = " ".join(expr_to_seq(a) for a in stmt["args"])
        return [f"PRINT {args}"]

    if t == "if":
        lines = [f"IF {expr_to_seq(stmt['condition'])}"]

        for s in stmt["then"]:
            lines.extend(["  " + l for l in stmt_to_seq(s)])

        if stmt["else"]:
            lines.append("ELSE")
            for s in stmt["else"]:
                lines.extend(["  " + l for l in stmt_to_seq(s)])

        lines.append("ENDIF")
        return lines

    if t == "for":
        lines = [
            f"FOR {stmt_to_seq(stmt['init'])[0]} ; {expr_to_seq(stmt['condition'])} ; {stmt_to_seq(stmt['update'])[0]}"
        ]

        for s in stmt["body"]:
            lines.extend(["  " + l for l in stmt_to_seq(s)])

        lines.append("ENDFOR")
        return lines

    return ["UNKNOWN"]


def expr_to_seq(e):

    t = e["type"]

    if t == "binary":
        return f"({expr_to_seq(e['left'])} {e['op']} {expr_to_seq(e['right'])})"

    if t == "compare":
        return f"({expr_to_seq(e['left'])} {e['op']} {expr_to_seq(e['right'])})"

    if t == "var":
        return e["value"]

    if t == "const":
        return str(e["value"])

    return "UNK"