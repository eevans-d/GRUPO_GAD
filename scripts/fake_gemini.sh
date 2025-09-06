#!/usr/bin/env bash
# Simula una respuesta JSON válida de Gemini consumiendo el prompt desde stdin.
# Guarda el prompt recibido en /tmp y emite una respuesta JSON válida por stdout.
set -euo pipefail

# Leer todo stdin (prompt) y guardarlo
cat > /tmp/_fake_gemini_prompt.txt

# Respuesta JSON simulada (impresa en stdout)
cat <<'JSON'
{
  "diff_unified": "diff --git a/README.md b/README.md\nnew file mode 100644\nindex 0000000..1111111\n--- /dev/null\n+++ b/README.md\n@@ -0,0 +1 @@\n+Hello Guardrails Standard\n",
  "changeset": {
    "files": ["README.md"],
    "new_dependencies": [],
    "new_dev_dependencies": [],
    "tests_added": ["tests/sanity.test.js"],
    "commands_to_run": ["echo 'apply manually with git apply -p0 outputs/runs/.../last.diff'"]
  }
}
JSON

