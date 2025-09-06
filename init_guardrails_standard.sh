#!/usr/bin/env bash
set -euo pipefail

echo "🎯 Instalando Guardrails Standard (equilibrio perfecto)..."

# Estructura base
mkdir -p scripts outputs/runs docs .github/workflows .vscode tests
touch outputs/.gitkeep

# 1) Manifest mínimo pero efectivo
if [ ! -f docs/manifest.json ]; then
cat > docs/manifest.json <<'JSON'
{
  "project": {
    "name": "TU_PROYECTO",
    "version": "0.1.0",
    "description": "Proyecto con Guardrails Standard"
  },
  "dependencies": {
    "allowlist": {
      "npm": ["express", "zod", "dotenv", "pino", "cors"],
      "pypi": ["fastapi", "uvicorn", "pydantic", "python-dotenv", "pytest", "requests"]
    },
    "dev_allowlist": {
      "npm": ["typescript", "ts-node", "eslint", "@typescript-eslint/parser", "@typescript-eslint/eslint-plugin", "jest", "ts-jest", "@types/jest", "supertest", "@types/supertest"]
    }
  },
  "testing_policy": {
    "unit_min_coverage_pct": 50,
    "smoke_required": true
  },
  "invariants": [
    "Validar inputs con esquemas cuando aplique",
    "No dependencias fuera de allowlist sin justificación",
    "Tests mínimos por módulo nuevo"
  ]
}
JSON
echo "✓ docs/manifest.json creado"
else
echo "• docs/manifest.json ya existe"
fi

# 2) Script principal Guardrails Standard
if [ ! -f scripts/guardrails.sh ]; then
cat > scripts/guardrails.sh <<'SCRIPT'
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
SCRIPT
chmod +x scripts/guardrails.sh
echo "✓ scripts/guardrails.sh creado"
else
echo "• scripts/guardrails.sh ya existe"
fi

# 3) Validador de allowlist
if [ ! -f scripts/check_allowlist.py ]; then
cat > scripts/check_allowlist.py <<'PY'
#!/usr/bin/env python3
import json, pathlib, sys, re

def check_npm():
    if not pathlib.Path("package.json").exists():
        return True
    
    manifest = json.loads(pathlib.Path("docs/manifest.json").read_text())
    pkg = json.loads(pathlib.Path("package.json").read_text())
    
    runtime_allow = set(manifest.get("dependencies", {}).get("allowlist", {}).get("npm", []))
    dev_allow = set(manifest.get("dependencies", {}).get("dev_allowlist", {}).get("npm", []))
    
    runtime_used = set(pkg.get("dependencies", {}).keys())
    dev_used = set(pkg.get("devDependencies", {}).keys())
    
    bad_runtime = runtime_used - runtime_allow
    bad_dev = dev_used - dev_allow
    
    if bad_runtime or bad_dev:
        print(f"❌ Dependencias fuera de allowlist:")
        if bad_runtime: print(f"  Runtime: {list(bad_runtime)}")
        if bad_dev: print(f"  Dev: {list(bad_dev)}")
        return False
    
    print("✓ Allowlist npm OK")
    return True

def check_python():
    req_file = pathlib.Path("pyservice/requirements.txt")
    if not req_file.exists():
        return True
        
    manifest = json.loads(pathlib.Path("docs/manifest.json").read_text())
    allow = set(p.lower() for p in manifest.get("dependencies", {}).get("allowlist", {}).get("pypi", []))
    
    used = []
    for line in req_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name = re.split(r"[<>=~!]", line)[0].split("[")[0].strip().lower()
            if name: used.append(name)
    
    bad = [p for p in used if p not in allow]
    if bad:
        print(f"❌ PyPI fuera de allowlist: {bad}")
        return False
    
    print("✓ Allowlist PyPI OK")
    return True

if __name__ == "__main__":
    npm_ok = check_npm()
    py_ok = check_python()
    sys.exit(0 if (npm_ok and py_ok) else 1)
PY
chmod +x scripts/check_allowlist.py
echo "✓ scripts/check_allowlist.py creado"
else
echo "• scripts/check_allowlist.py ya existe"
fi

# 4) CI Standard (mínimo pero efectivo)
if [ ! -f .github/workflows/standard.yml ]; then
cat > .github/workflows/standard.yml <<'YML'
name: Standard
on: [push, pull_request]
jobs:
  standard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        if: hashFiles('package.json') != ''
        uses: actions/setup-node@v4
        with: { node-version: '20' }
      - name: Install Node deps
        if: hashFiles('package.json') != ''
        run: npm ci
      - name: Lint
        if: hashFiles('package.json') != ''
        run: npx eslint . || echo "Lint warnings"
      - name: Typecheck  
        if: hashFiles('package.json') != ''
        run: npx tsc --noEmit || echo "Type warnings"
      - name: Node tests
        if: hashFiles('package.json') != ''
        run: npm test --silent
        
      - name: Setup Python
        if: hashFiles('pyservice/requirements.txt') != ''
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Python deps
        if: hashFiles('pyservice/requirements.txt') != ''
        run: python -m pip install -r pyservice/requirements.txt
      - name: Python tests
        if: hashFiles('pyservice/tests/') != ''
        run: cd pyservice && pytest -q
        
      - name: Check allowlists
        run: python scripts/check_allowlist.py
        
      - name: Basic security scan
        uses: returntocorp/semgrep-action@v1
        with:
          config: p/security-audit
YML
echo "✓ .github/workflows/standard.yml creado"
else
echo "• standard.yml ya existe"
fi

# 5) VS Code task
if [ ! -f .vscode/tasks.json ]; then
cat > .vscode/tasks.json <<'JSON'
{
  "version": "2.0.0",
  "inputs": [
    {
      "id": "objective",
      "type": "promptString", 
      "description": "Objetivo claro y específico"
    },
    {
      "id": "scope",
      "type": "promptString",
      "description": "Archivos a tocar (opcional)",
      "default": ""
    },
    {
      "id": "dryrun",
      "type": "pickString",
      "description": "Modo",
      "options": ["aplicar", "dry-run"],
      "default": "aplicar"
    }
  ],
  "tasks": [
    {
      "label": "Guardrails Standard",
      "type": "shell",
      "command": "${workspaceFolder}/scripts/guardrails.sh",
      "args": [
        "-o", "${input:objective}",
        "-s", "${input:scope}",
        "${input:dryrun}" == "dry-run" ? "--dry-run" : ""
      ],
      "options": {
        "env": {
          "GEMINI_CMD": "gemini prompt --model gemini-1.5-pro --response-mime application/json --temperature"
        }
      },
      "problemMatcher": []
    }
  ]
}
JSON
echo "✓ .vscode/tasks.json creado"
else
echo "• .vscode/tasks.json ya existe"
fi

# 6) Tests mínimos si faltan
if [ -f package.json ] && [ ! -f tests/sanity.test.js ]; then
mkdir -p tests
cat > tests/sanity.test.js <<'JS'
import test from 'node:test';
import assert from 'node:assert/strict';

test('sanity check', () => {
  assert.equal(1 + 1, 2);
});
JS
echo "✓ tests/sanity.test.js creado"

# Configurar script test si no existe
if ! npm run -s | grep -q '"test"'; then
  npm pkg set scripts.test="node --test" >/dev/null 2>&1 || true
  echo "✓ script 'test' configurado"
fi
fi

if [ -d pyservice ] && [ ! -f pyservice/tests/test_sanity.py ]; then
mkdir -p pyservice/tests
cat > pyservice/tests/test_sanity.py <<'PY'
def test_sanity():
    assert 2 + 2 == 4
PY
echo "✓ pyservice/tests/test_sanity.py creado"
fi

echo ""
echo "🎯 ¡Guardrails Standard instalado!"
echo ""
echo "Próximos pasos:"
echo "1) Configura GEMINI_CMD:"
echo "   export GEMINI_CMD=\"gemini prompt --model gemini-1.5-pro --response-mime application/json --temperature\""
echo ""
echo "2) Ajusta docs/manifest.json con tu proyecto real"
echo ""  
echo "3) Primera prueba:"
echo "   scripts/guardrails.sh -o \"Crear función de saludo\" --dry-run"
echo ""
echo "4) Commit inicial:"
echo "   git add . && git commit -m 'feat: setup Guardrails Standard'"
