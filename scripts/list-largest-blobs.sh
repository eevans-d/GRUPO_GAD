#!/usr/bin/env bash
# Uso:
#   ./scripts/list-largest-blobs.sh 200 100
# Genera:
#   - audit-history-top.csv: blobs más grandes del historial
#   - audit-worktree-top.csv: archivos más grandes del working tree HEAD
#   - audit-summary.md: resumen legible

set -euo pipefail
TOP_HISTORY="${1:-200}"
TOP_WORKTREE="${2:-100}"

# Requisitos mínimos
command -v git >/dev/null 2>&1 || { echo "git no está disponible"; exit 1; }

echo "== Audit: largest blobs in history =="
# Lista blobs con tamaño, objeto y ruta, ordenados desc
# Formato CSV: size_bytes,sha,path
# Nota: cat-file batch-check imprime: sha type size rest
# Luego filtramos por blobs y ordenamos por size desc

git rev-list --objects --all \
| git cat-file --batch-check='%(objectname) %(objecttype) %(objectsize) %(rest)' \
| awk '$2 == "blob" { 
    size=$3; sha=$1; path=""; 
    for (i=4; i<=NF; i++) { path=path (i==4?"":" ") $i } 
    print size "," sha "," path 
  }' \
| sort -t, -k1,1nr \
| head -n "$TOP_HISTORY" > audit-history-top.csv || true

echo "== Audit: largest files in working tree (HEAD) =="
# Lista archivos por tamaño en HEAD (no historial)
# Formato CSV: size_bytes,path

git ls-tree -r -l HEAD \
| awk '{print $4 "," $5}' \
| sort -t, -k1,1nr \
| head -n "$TOP_WORKTREE" > audit-worktree-top.csv || true

# Resumen bonito
{
  echo "# Repo Size Audit"
  echo
  echo "Fecha: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  echo
  echo "## Top ${TOP_HISTORY} blobs en historial"
  echo
  echo '```csv'
  head -n 20 audit-history-top.csv || true
  echo '```'
  echo
  echo "## Top ${TOP_WORKTREE} archivos en working tree (HEAD)"
  echo
  echo '```csv'
  head -n 20 audit-worktree-top.csv || true
  echo '```'
  echo
  echo "## Sugerencias inmediatas"
  echo "- Mueve assets/datasets/binarios a Releases/almacenamiento externo o LFS si deben versionarse."
  echo "- Asegura .gitignore para evitar reincidencia."
  echo "- Si la mayoría del peso es histórico, planifica limpieza con git filter-repo (ver docs/CLEANUP_HISTORY.md si existe)."
} > audit-summary.md

echo "Auditoría creada: audit-history-top.csv, audit-worktree-top.csv, audit-summary.md"
