from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from translator import translate_python_to_java
import subprocess
import tempfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/style.css")
def style():
    return send_from_directory(FRONTEND_DIR, "style.css")


@app.route("/editor.js")
def editor():
    return send_from_directory(FRONTEND_DIR, "editor.js")


@app.route("/translate", methods=["POST"])
def translate():
    code = request.json["code"]
    return jsonify({
        "java_code": translate_python_to_java(code)
    })


@app.route("/run", methods=["POST"])
def run_java():
    java_code = request.json["code"]

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            java_file = os.path.join(temp_dir, "Main.java")

            with open(java_file, "w") as f:
                f.write(java_code)

            compile_proc = subprocess.run(
                ["javac", java_file],
                capture_output=True,
                text=True
            )

            if compile_proc.returncode != 0:
                return jsonify({"output": compile_proc.stderr})

            run_proc = subprocess.run(
                ["java", "-cp", temp_dir, "Main"],
                capture_output=True,
                text=True,
                timeout=5
            )

            return jsonify({"output": run_proc.stdout or run_proc.stderr})

    except subprocess.TimeoutExpired:
        return jsonify({"output": "Execution timed out."})


if __name__ == "__main__":
    app.run(debug=True)