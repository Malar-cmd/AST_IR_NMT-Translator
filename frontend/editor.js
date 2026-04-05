require.config({
  paths: { vs: 'https://unpkg.com/monaco-editor@0.45.0/min/vs' }
});

require(['vs/editor/editor.main'], function () {

  const editor = monaco.editor.create(
    document.getElementById('editor'),
    {
      value: `import java.util.*;

public class Main {

    public static void main(String[] args) {

    }

}`,
      language: 'java',
      theme: 'vs-dark'
    }
  );

  const modal = document.getElementById("pythonModal");
  const textarea = document.getElementById("pythonInput");

  // 🔥 Open modal (Ctrl + Enter)
  editor.addCommand(
    monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
    () => {
      modal.style.display = "block";
    }
  );

  // 🔥 Cancel modal
  document.getElementById("cancelBtn").onclick = () => {
    modal.style.display = "none";
  };

  // 🔥 TRANSLATE (FINAL FIXED)
  document.getElementById("translateBtn").onclick = () => {

    const code = textarea.value;

    console.log("Sending Python:", code);

    if (!code.trim()) {
      alert("Please enter Python code!");
      return;
    }

    fetch("http://127.0.0.1:5000/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ code: code })
    })
      .then(res => res.json())
      .then(data => {

        console.log("Backend response:", data);

        const javaCode = data.output || "// Translation failed";

        // 🔥 Safe insertion into main()
        const currentCode = editor.getValue();

        const updatedCode = currentCode.replace(
          /public static void main\(String\[\] args\) \{\s*/,
          match => match + "\n        " + javaCode.replace(/\n/g, "\n        ") + "\n"
        );

        editor.setValue(updatedCode);

        modal.style.display = "none";
        textarea.value = "";
      })
      .catch(err => {
        console.error("Translate error:", err);
        alert("Translation failed!");
      });
  };

  // 🔥 RUN JAVA
  document.getElementById("runBtn").onclick = () => {

    const code = editor.getValue();

    console.log("Running Java:", code);

    fetch("http://127.0.0.1:5000/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ code: code })
    })
      .then(res => res.json())
      .then(data => {

        console.log("Run output:", data);

        document.getElementById("console").textContent =
          data.output || "Program executed (no output)";
      })
      .catch(err => {
        console.error("Run error:", err);
        document.getElementById("console").textContent =
          "Error running code.";
      });
  };

});