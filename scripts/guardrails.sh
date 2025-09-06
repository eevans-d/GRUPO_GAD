#!/usr/bin/env bash
set -euo pipefail

# Guardrails Standard: genera -> valida -> aplica -> testea -> revierte/commitea
MODEL="${MODEL:-gemini-1.5-pro}"
TEMP="${TEMP:-0.2}"
OBJECTIVE=""
SCOPE=""
DRY_RUN="false"

usage(){
  echo "Uso: $0 -o \"Objetivo\" [-s \"alcance\"] [--dry-run]"
  echo "Ejemplo: $0 -o \"Crear endpoint GET /health\" -s \"src/app.ts tests/health.test.ts\""
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--objective) OBJECTIVE="${2:-}"; shift 2;;
    -s|--scope) SCOPE="${2:-}"; shift 2;;
    --dry-run) DRY_RUN="true"; shift 1;;
    -h|--help) usage;;
    *) echo "Flag desconocida: $1"; usage;;
  esac
done
[[ -z "$OBJECTIVE" ]] && usage

# Prerrequisitos
command -v python3 >/dev/null || { echo "python3 requerido"; exit 2; }
command -v git >/dev/null || { echo "git requerido"; exit 2; }

timestamp="$(date +%Y%m%dT%H%M%S)"
run_dir="outputs/runs/$timestamp"
mkdir -p "$run_dir"

# Advertir si hay cambios sin commitear
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "⚠️ Hay cambios sin commitear."
  read -r -p "¿Continuar? [y/N]: " ans
  [[ "${ans:-N}" =~ [Yy] ]] || { echo "Abortado."; exit 10; }
fi

# Cargar manifest
manifest="(sin manifest)"
if [[ -f docs/manifest.json ]]; then
  manifest="$(cat docs/manifest.json)"
fi

# Construir prompt
cat > "$run_dir/prompt.txt" <<EOF
SISTEMA: Eres un implementador disciplinado. Cumple docs/manifest.json si existe. 
Entrega SOLO JSON válido con los campos exigidos. Sin texto adicional.

OBJETIVO: $OBJECTIVE

ALCANCE: $SCOPE

REGLAS:
- No agregues dependencias fuera del allowlist sin justificación
- Genera diff aplicable desde raíz del repo (git unified diff)
- Cambios pequeños y atómicos
- Incluye tests cuando corresponda

SALIDA OBLIGATORIA (JSON):
{
  "diff_unified": "string con diff en formato unified",
  "changeset": {
    "files": ["rutas afectadas"],
    "new_dependencies": ["deps runtime si hubiera"],
    "new_dev_dependencies": ["deps dev si hubiera"],
    "tests_added": ["tests nuevos si hubiera"],
    "commands_to_run": ["comandos sugeridos"]
  }
}

REFERENCIAS:
[manifest.json] $manifest
EOF

echo "🤖 Invocando Gemini..."
call_gemini() {
  if [[ -n "${GEMINI_CMD:-}" ]]; then
    eval "$GEMINI_CMD $TEMP"
  else
    gemini prompt --model "$MODEL" --response-mime application/json --temperature "$TEMP"
  fi
}

if ! cat "$run_dir/prompt.txt" | call_gemini > "$run_dir/output.json"; then
  echo "❌ Gemini falló"; exit 3
fi

# Validación básica JSON
python3 - "$run_dir/output.json" <<'PY'
import sys, json
try:
  data = json.load(open(sys.argv[1], encoding="utf-8"))
  assert isinstance(data, dict)
  assert "diff_unified" in data and "changeset" in data
  assert isinstance(data["diff_unified"], str) and data["diff_unified"].strip()
  cs = data["changeset"]
  assert isinstance(cs, dict)
  for k in ["files","new_dependencies","new_dev_dependencies","tests_added","commands_to_run"]:
    assert k in cs and isinstance(cs[k], list)
  print("✓ JSON válido")
except Exception as e:
  print(f"❌ JSON inválido: {e}")
  sys.exit(1)
PY

# Extraer diff
python3 - "$run_dir/output.json" "$run_dir/last.diff" <<'PY'
import sys, json, pathlib
data = json.load(open(sys.argv[1], encoding="utf-8"))
pathlib.Path(sys.argv[2]).write_text(data["diff_unified"], encoding="utf-8")
cs = data["changeset"]
print("📁 Archivos:", ", ".join(cs.get("files",[])) or "(ninguno)")
print("📦 Nuevas deps:", ", ".join(cs.get("new_dependencies",[])) or "(ninguna)")
print("🔧 Dev deps:", ", ".join(cs.get("new_dev_dependencies",[])) or "(ninguna)")
print("🧪 Tests:", ", ".join(cs.get("tests_added",[])) or "(ninguno)")
PY

# Confirmar dependencias nuevas
has_new=$(python3 - "$run_dir/output.json" <<'PY'
import sys,json
d=json.load(open(sys.argv[1], encoding="utf-8"))
print(1 if (d["changeset"].get("new_dependencies") or d["changeset"].get("new_dev_dependencies")) else 0)
PY
)
if [[ "$has_new" -eq 1 ]]; then
  read -r -p "🔍 Propone nuevas dependencias. ¿Continuar? [y/N]: " ans
  [[ "${ans:-N}" =~ [Yy] ]] || { echo "Abortado por dependencias"; exit 4; }
fi

# Dry-run o aplicar
if [[ "$DRY_RUN" == "true" ]]; then
  echo "🔍 DRY-RUN: diff en $run_dir/last.diff"
  echo "Para aplicar: git apply -p0 $run_dir/last.diff"
  exit 0
fi

echo "📝 Aplicando diff..."
if ! git apply -p0 "$run_dir/last.diff"; then
  echo "❌ Error aplicando diff. Revisa: $run_dir/last.diff"
  exit 5
fi

# Función revert
revert() { 
  echo "⏪ Revirtiendo..."
  git apply -R -p0 "$run_dir/last.diff" || true
}

# Tests Node
if [[ -f package.json ]]; then
  if npm pkg get scripts.test >/dev/null 2>&1 && ! npm pkg get scripts.test | grep -q 'undefined'; then
    echo "🧪 Tests Node..."
    if ! npm test --silent; then
      echo "❌ Tests Node fallaron"
      revert; exit 6
    fi
  else
    echo "ℹ️ Sin script 'test' en package.json"
  fi
fi

# Tests Python  
if [[ -d pyservice && -d pyservice/tests ]]; then
  if command -v pytest >/dev/null 2>&1; then
    echo "🧪 Tests Python..."
    if ! (cd pyservice && pytest -q); then
      echo "❌ Tests Python fallaron"
      revert; exit 7
    fi
  else
    echo "ℹ️ pytest no disponible"
  fi
fi

# Commit
msg="feat(ia): ${OBJECTIVE} [guardrails-standard]"
git add -A
if git diff --cached --quiet; then
  echo "ℹ️ Sin cambios efectivos"
else
  git commit -m "$msg"
  echo "✅ Commit: $msg"
fi

echo "🎯 Completado: $run_dir"
