from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ir_builder import build_ir
from ir_to_java import ir_to_java
from ir_normalizer import normalize_ir
import subprocess
import tempfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(__name__)
CORS(app)


# ---------------- FRONTEND ROUTES ---------------- #

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/style.css")
def style():
    return send_from_directory(FRONTEND_DIR, "style.css")


@app.route("/editor.js")
def editor():
    return send_from_directory(FRONTEND_DIR, "editor.js")


# ---------------- TRANSLATE ---------------- #

@app.route("/translate", methods=["POST"])
def translate():

    try:
        data = request.get_json()
        code = data.get("code", "")

        if not code.strip():
            return jsonify({"output": "// No input provided"})

        # 🔥 STEP 1: Build IR
        ir = build_ir(code)
        print("Raw IR:", ir)

        # 🔥 STEP 2: Normalize IR
        normalized_ir = normalize_ir(ir)
        print("Normalized IR:", normalized_ir)

        # 🔥 STEP 3: Convert to Java
        java_code = ir_to_java(normalized_ir)
        print("Generated Java:\n", java_code)   # ✅ IMPORTANT

        return jsonify({
            "output": java_code
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "output": f"// ERROR: {str(e)}"
        })


# ---------------- RUN JAVA ---------------- #

@app.route("/run", methods=["POST"])
def run_java():

    java_code = request.json["code"]

    try:
        with tempfile.TemporaryDirectory() as temp_dir:

            java_file = os.path.join(temp_dir, "Main.java")

            with open(java_file, "w") as f:
                f.write(java_code)

            # 🔥 Compile
            compile_proc = subprocess.run(
                ["javac", java_file],
                capture_output=True,
                text=True
            )

            if compile_proc.returncode != 0:
                return jsonify({"output": compile_proc.stderr})

            # 🔥 Run
            run_proc = subprocess.run(
                ["java", "-cp", temp_dir, "Main"],
                capture_output=True,
                text=True,
                timeout=5
            )

            return jsonify({
                "output": run_proc.stdout or run_proc.stderr
            })

    except subprocess.TimeoutExpired:
        return jsonify({"output": "Execution timed out."})


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)