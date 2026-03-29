from ir_builder import build_ir
from ir_to_java import ir_to_java


def translate_python_to_java(code):
    try:
        ir = build_ir(code)
        print("IR:", ir)
        return ir_to_java(ir)
    except Exception as e:
        print("Error:", e)
        return "// Waiting for valid Python code..."