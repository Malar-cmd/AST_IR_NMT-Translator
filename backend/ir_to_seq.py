def ir_to_sequence(ir):

    lines = []

    for stmt in ir["body"]:
        lines.extend(stmt_to_seq(stmt))

    return "\n".join(lines)


def stmt_to_seq(stmt):

    t = stmt["type"]

    # ---------- ASSIGN ---------- #
    if t == "assign":
        return [f"ASSIGN {stmt['target']} {expr_to_seq(stmt['value'])}"]

    # ---------- PRINT ---------- #
    if t == "print":
        args = " ".join(expr_to_seq(a) for a in stmt["args"])
        return [f"PRINT {args}"]

    # ---------- IF ---------- #
    if t == "if":
        lines = [f"IF {expr_to_seq(stmt['condition'])}"]

        for s in stmt["then"]:
            lines.extend(["  " + l for l in stmt_to_seq(s)])

        if stmt.get("else")
            lines.append("ELSE")
            for s in stmt["else"]:
                lines.extend(["  " + l for l in stmt_to_seq(s)])

        lines.append("ENDIF")
        return lines

    # ---------- FOR LOOP (FIXED) ---------- #
    if t == "for":

        if "init" in stmt:
            init = stmt_to_seq(stmt["init"])[0]
            cond = expr_to_seq(stmt["condition"])
            update = stmt_to_seq(stmt["update"])[0]

            lines = [f"FOR {init} ; {cond} ; {update}"]

            for s in stmt["body"]:
                lines.extend(["  " + l for l in stmt_to_seq(s)])

            lines.append("ENDFOR")
            return lines

        # Python-style for loop (for x in list)
        elif "iter" in stmt:
            var = stmt["var"]
            iterable = expr_to_seq(stmt["iter"])

            lines = [f"FOR_EACH {var} IN {iterable}"]

            for s in stmt["body"]:
                lines.extend(["  " + l for l in stmt_to_seq(s)])

            lines.append("ENDFOR")
            return lines

        # fallback
        return ["FOR_UNKNOWN"]

    # ---------- FOR EACH (explicit IR) ---------- #
    if t == "for_each":
        var = stmt["var"]
        iterable = expr_to_seq(stmt["iter"])

        lines = [f"FOR_EACH {var} IN {iterable}"]

        for s in stmt["body"]:
            lines.extend(["  " + l for l in stmt_to_seq(s)])

        lines.append("ENDFOR")
        return lines

    # ---------- WHILE ---------- #
    if t == "while":
        lines = [f"WHILE {expr_to_seq(stmt['condition'])}"]

        for s in stmt["body"]:
            lines.extend(["  " + l for l in stmt_to_seq(s)])

        lines.append("ENDWHILE")
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
        if isinstance(e["value"], str):
            return f"\"{e['value']}\""
        return str(e["value"])

    if t == "call":
        if e["name"] == "len":
            return f"LEN({expr_to_seq(e['args'][0])})"

        args = " ".join(expr_to_seq(a) for a in e["args"])
        return f"{e['name']}({args})"

    return "UNK"