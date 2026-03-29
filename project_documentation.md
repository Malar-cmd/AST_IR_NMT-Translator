# Python to Java IDE: Project Documentation

This document provides a detailed technical overview of the "Python to Java IDE" project. The project is an end-to-end web application that allows users to write Python code, translate it into Java code directly within an in-browser editor, and execute the resulting Java code on the backend.

## 1. System Architecture

The project follows a standard client-server architecture:
- **Frontend**: A web-based Integrated Development Environment (IDE) built with HTML, CSS, vanilla JavaScript, and the Monaco Editor (the core editor behind VS Code).
- **Backend**: A RESTful API built with Python and Flask. It handles serving the frontend files, compiling Python to an Intermediate Representation (IR), translating the IR to Java, and securely executing Java code in temporary directories.

---

## 2. Backend Components (Python & Flask)

The backend code is primarily located in the `backend/` directory.

### `app.py`
This is the main entry point for the Flask web server.
- **Static File Serving**: Serves `index.html`, `style.css`, and `editor.js` for the frontend.
- **`/translate` Endpoint**: Receives Python code via a JSON POST request. It calls the `translate_python_to_java` function and returns the generated Java code.
- **`/run` Endpoint**: Receives Java code via a JSON POST request. It creates a temporary directory `tempfile.TemporaryDirectory()`, writes the code to a `Main.java` file, and uses Python's `subprocess` module to compile (`javac`) and run (`java`) the code. It captures the standard output or standard error and returns it to the client. It also enforces a 5-second timeout on execution to prevent infinite loops.

### `translator.py`
This serves as the orchestrator for the translation process.
- It exposes a `translate_python_to_java(code)` function.
- It takes the raw Python code, passes it to the `ir_builder`, takes the resulting JSON-like Intermediate Representation (IR), and passes it to `ir_to_java` to get the final Java string.

### `ir_builder.py`
This file is responsible for parsing Python code and generating a custom Intermediate Representation (IR).
- It uses Python's built-in `ast` (Abstract Syntax Tree) module to parse the raw Python source code.
- It recursively traverses the AST (handling `ast.Assign`, `ast.Call`, `ast.FunctionDef`, `ast.BinOp`, etc.) and converts these nodes into a simplified, uniform JSON dictionary structure.
- **Example IR**: An assignment `x = 5` becomes `{"type": "assign", "target": "x", "value": {"type": "const", "value": 5}}`.

### `ir_to_java.py`
This file is responsible for taking the JSON-like Intermediate Representation and generating valid Java syntax.
- It traverses the IR dictionaries and builds strings of Java code.
- It separates function definitions from the main body.
- It wraps everything cleanly inside a `public class Main` and puts standalone statements inside a `public static void main(String[] args)` method.
- **Type inference**: Currently, it heavily assumes integer (`int`) types for variables and method parameters, as seen in `int {stmt['target']} = ...` and `int {p}`.

---

## 3. Frontend Components (HTML & JS)

The frontend code is located in the `frontend/` directory.

### `index.html`
- Sets up the structure of the application.
- Loads the **Monaco Editor** script from a CDN.
- Contains the main editor container (`#editor`), a "Run" button (`#runBtn`), an output console area (`#console`), and a hidden modal (`#pythonModal`) for entering Python code.

### `editor.js`
This script manages the interactivity of the IDE.
- **Editor Initialization**: Initializes the Monaco Editor with an empty Java `Main` class template and a dark theme (`vs-dark`).
- **Hotkey Registration**: Listens for the `CtrlCmd + Enter` keyboard shortcut while focused in the editor. Once pressed, it saves the user's cursor position and opens the Python Input Modal.
- **Translation Pipeline**: When the user clicks "Translate" inside the modal, it sends the Python code to the backend `/translate` API. Upon receiving the Java code, it uses `editor.executeEdits` to insert the converted Java code exactly where the user's cursor was.
- **Execution Pipeline**: When the user clicks "▶ Run", it grabs the entire contents of the Monaco Editor and sends it to the backend's `/run` API. It then displays the compilation errors or standard output in the DOM console element.

---

## 4. How Data Flows

### The Translation Flow
1. User presses `CtrlCmd + Enter` in the browser editor and types Python code in the popup modal.
2. User clicks "Translate".
3. JS sends the Python code via a POST request to `/translate`.
4. Flask (`app.py`) receives the request and calls `translator.py`.
5. `translator.py` uses `ir_builder.py` (which uses `ast`) to convert the Python code into an AST and then into a JSON IR.
6. `translator.py` uses `ir_to_java.py` to map the JSON IR to Java string syntax.
7. Flask returns the Java string to the frontend.
8. JS inserts the Java code into the Monaco Editor at the user's last cursor position.

### The Execution Flow
1. User clicks the "▶ Run" button in the UI.
2. JS grabs all the Java code from the Monaco Editor and POSTs it to the `/run` endpoint.
3. Flask (`app.py`) creates a secure, temporary directory.
4. Flask writes the code to `Main.java`.
5. Flask executes `javac Main.java` via `subprocess`.
6. Flask executes `java Main` via `subprocess`.
7. Flask captures the console output and sends it back to the frontend.
8. JS updates the `#console` element with the output of the Java program.
