require.config({
  paths: { vs: 'https://unpkg.com/monaco-editor@0.45.0/min/vs' }
});

require(['vs/editor/editor.main'], function () {

  const editor = monaco.editor.create(
    document.getElementById('editor'),
    {
      value: `public class Main {

    public static void main(String[] args) {

    }

}`,
      language: 'java',
      theme: 'vs-dark'
    }
  );

  const modal = document.getElementById("pythonModal");
  const textarea = document.getElementById("pythonInput");

  let pos;

  editor.addCommand(
    monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
    () => {
      pos = editor.getPosition();
      modal.style.display = "block";
    }
  );

  document.getElementById("cancelBtn").onclick = () => modal.style.display = "none";

  document.getElementById("translateBtn").onclick = () => {

    fetch("http://127.0.0.1:5000/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: textarea.value })
    })
      .then(res => res.json())
      .then(data => {
        editor.executeEdits("", [{
          range: new monaco.Range(pos.lineNumber, pos.column, pos.lineNumber, pos.column),
          text: "\n" + data.java_code + "\n"
        }]);
        modal.style.display = "none";
      });
  };

  document.getElementById("runBtn").onclick = () => {
    fetch("/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: editor.getValue() })
    })
      .then(res => res.json())
      .then(data => {
        document.getElementById("console").textContent = data.output;
      });
  };

});