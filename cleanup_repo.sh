#!/bin/bash

# Script de limpieza y optimizaci0n para GRUPO_GAD
# Ejecutar: bash cleanup_repo.sh

set -e

echo "ὐd AN1LISIS DEL REPOSITORIO GRUPO_GAD"
echo "======================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. BACKUP PREVENTIVO
echo -e "${YELLOW}὎6 Creando backup de seguridad...${NC}"
BACKUP_DIR="../GRUPO_GAD_backup_$(date +%Y%m%d_%H%M%S)"
cp -r . "$BACKUP_DIR"
echo -e "${GREEN}✓ Backup creado en: $BACKUP_DIR${NC}"
echo ""

# 2. AN1LISIS DE TAMA1O
echo -e "${YELLOW}὚2 An1lisis de tama1o actual:${NC}"
INITIAL_SIZE=$(du -sh .git/ | cut -f1)
echo "Tama1o del .git: $INITIAL_SIZE"
echo "Tama1o total del proyecto:"
du -sh . | cut -f1
echo ""

# 3. ARCHIVOS GRANDES EN EL DIRECTORIO
echo -e "${YELLOW}ὐe Buscando archivos grandes (>5MB) en el directorio...${NC}"
find . -type f -size +5M -not -path "./.git/*" -not -path "./.venv/*" -not -path "./node_modules/*" -exec ls -lh {} \; 2>/dev/null | awk '{print $9, ":", $5}' || echo "No se encontraron archivos grandes"
echo ""

# 4. ARCHIVOS DUPLICADOS
echo -e "${YELLOW}ὐd Buscando archivos duplicados...${NC}"
find . -type f -not -path "./.git/*" -not -path "./.venv/*" -not -path "./node_modules/*" -exec md5sum {} + 2>/dev/null | sort | uniq -w32 -dD | head -20 || echo "No se encontraron duplicados obvios"
echo ""

# 5. ARCHIVOS TEMPORALES Y CACH09
echo -e "${YELLOW}Ὕ1️  Limpiando archivos temporales y cach0...${NC}"
find . -type f -name "*.pyc" -delete 2>/dev/null && echo "✓ Eliminados archivos .pyc"
find . -type f -name "*.pyo" -delete 2>/dev/null && echo "✓ Eliminados archivos .pyo"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null && echo "✓ Eliminados directorios __pycache__"
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null && echo "✓ Eliminados directorios .pytest_cache"
find . -type f -name ".DS_Store" -delete 2>/dev/null && echo "✓ Eliminados archivos .DS_Store"
find . -type f -name "Thumbs.db" -delete 2>/dev/null && echo "✓ Eliminados archivos Thumbs.db"
find . -type f -name "*.log" -size +10M -delete 2>/dev/null && echo "✓ Eliminados logs grandes"
echo ""

# 6. DIRECTORIOS COMUNES QUE NO DEBER1AN ESTAR EN GIT
echo -e "${YELLOW}Ὄ1 Verificando directorios que no deber1an estar en Git...${NC}"
for dir in node_modules .venv venv env __pycache__ .pytest_cache dist build *.egg-info .eggs coverage htmlcov; do
    if [ -d "$dir" ]; then
        echo -e "${RED}⚠️  Encontrado: $dir (deber1a estar en .gitignore)${NC}"
    fi
done
echo ""

# 7. CREAR/ACTUALIZAR .gitignore
echo -e "${YELLOW}Ὅ D Creando/Actualizando .gitignore...${NC}"
cat > .gitignore << 'EOF'
# ===========================
# Python
# ===========================
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
pip-log.txt
pip-delete-this-directory.txt

# ===========================
# Virtual Environment
# ===========================
.venv/
venv/
ENV/
env/
env.bak/
venv.bak/
pyvenv.cfg

# ===========================
# Testing
# ===========================
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.nox/
coverage.xml
*.cover
.hypothesis/
.pytype/
.mypy_cache/
.dmypy.json
dmypy.json
nosetests.xml
test-results/

# ===========================
# Jupyter Notebook
# ===========================
.ipynb_checkpoints
*.ipynb
profile_default/
ipython_config.py

# ===========================
# Database
# ===========================
*.db
*.sqlite
*.sqlite3
*.sql
db.sqlite3
db.sqlite3-journal

# ===========================
# Logs
# ===========================
*.log
logs/
*.log.*
log/

# ===========================
# OS Files
# ===========================
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# ===========================
# IDE
# ===========================
.vscode/
.idea/
*.swp
*.swo
*~
.project
.pydevproject
.settings/

# ===========================
# Environment variables
# ===========================
.env
.env.local
.env.*.local
.envrc
*.env

# ===========================
# FastAPI/Uvicorn specific
# ===========================
instance/
.webassets-cache

# ===========================
# Data & Models (Machine Learning)
# ===========================
data/
datasets/
*.pkl
*.pickle
*.h5
*.hdf5
*.pt
*.pth
*.ckpt
models/
checkpoints/

# ===========================
# Documentation builds
# ===========================
docs/_build/
site/
.doctrees

# ===========================
# Backup files
# ===========================
*.bak
*.backup
*.old
*.orig
*~

# ===========================
# Temporary files
# ===========================
tmp/
temp/
*.tmp

# ===========================
# Node (si usas frontend)
# ===========================
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# ===========================
# Archivos grandes
# ===========================
*.csv
*.xlsx
*.xls
*.pdf
*.zip
*.tar.gz
*.mp4
*.mp3
*.avi

# ===========================
# Git
# ===========================
.git/
*.patch
*.diff
EOF
echo -e "${GREEN}✓ .gitignore creado/actualizado${NC}"
echo ""

# 8. CREAR .copilotignore
echo -e "${YELLOW}Ὅ D Creando .copilotignore...${NC}"
cat > .copilotignore << 'EOF'
# Datos y modelos
data/
datasets/
models/
*.csv
*.xlsx
*.json
*.pkl
*.h5

# Dependencias
node_modules/
.venv/
venv/

# Logs y temporales
*.log
*.tmp
__pycache__/

# Documentaci0n generada
docs/_build/
site/

# Tests y coverage
.pytest_cache/
htmlcov/
.coverage
EOF
echo -e "${GREEN}✓ .copilotignore creado${NC}"
echo ""

# 9. REMOVER ARCHIVOS DEL 1NDICE DE GIT
echo -e "${YELLOW}ὐ4 Removiendo archivos ignorados del 1ndice de Git...${NC}"
git rm -r --cached . 2>/dev/null || true
git add .
echo -e "${GREEN}✓ 1ndice actualizado${NC}"
echo ""

# 10. OPTIMIZACI0N DE GIT
echo -e "${YELLOW}⚙️  Optimizando repositorio Git...${NC}"
git reflog expire --expire=now --all
echo "✓ Reflog limpiado"
git gc --aggressive --prune=now
echo "✓ Garbage collection ejecutado"
git repack -ad
echo "✓ Objetos reempaquetados"
echo ""

# 11. AN1LISIS POST-LIMPIEZA
echo -e "${YELLOW}὚2 An1lisis despu0s de la limpieza:${NC}"
FINAL_SIZE=$(du -sh .git/ | cut -f1)
echo "Tama1o del .git: $FINAL_SIZE (antes: $INITIAL_SIZE)"
echo "Tama1o total del proyecto:"
du -sh . | cut -f1
echo ""

# 12. RECOMENDACIONES
echo -e "${GREEN}✅ LIMPIEZA COMPLETADA${NC}"
echo ""
echo -e "${YELLOW}Ὄ B PR0XIMOS PASOS:${NC}"
echo ""
echo "1. Revisa los cambios: git status"
echo "2. Haz commit: git commit -m 'chore: Limpieza y actualizaci0n de .gitignore'"
echo "3. Reinicia VS Code para aplicar cambios de Copilot"
echo ""
echo -e "${GREEN}Backup guardado en: $BACKUP_DIR${NC}"