#!/usr/bin/env bash
set -euo pipefail

# Script DOCUMENTAL para ejecutar limpieza de historial con git-filter-repo o BFG.
# WARNING: destructive. Use only after backup and team coordination.

echo "This script will guide you through history cleanup options. Read carefully."

echo "1) Ensure you have a backup: run scripts/prepare_repo_backup.sh"
echo "2) Example with git-filter-repo (recommended):"
echo "   git clone --mirror <repo> repo-mirror.git"
echo "   cd repo-mirror.git"
echo "   git filter-repo --invert-paths --paths .env.production"
echo "   git push --force --all"

echo "3) Example with BFG (alternative):"
echo "   bfg --delete-files .env.production repo-mirror.git"

echo "Important: After rewriting history, instruct all collaborators to reclone or run appropriate commands to reset their clones."

echo "This script does NOT execute the commands automatically. It's a guide."
