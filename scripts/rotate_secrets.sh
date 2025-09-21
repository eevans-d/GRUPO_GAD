#!/usr/bin/env bash
set -euo pipefail

# Script DOCUMENTAL para rotación segura de secretos y limpieza de historial.
# NO lo ejecutes sin revisar y coordinar (este script sólo documenta pasos automatizables).

echo "=== Guia de rotación de secretos (documental) ==="
echo "1) Rotar credenciales externas: DB, JWT_SECRET, TELEGRAM_TOKEN, API keys"
echo "   - Actualiza los secretos en el proveedor (DB host, secrets manager, etc)."
echo "2) Actualiza archivos .env en entornos (staging/production) con nuevos valores"
echo "3) Para eliminar secretos del historial Git: usar git-filter-repo o BFG con un backup local"
echo "   Ejemplo (BFG): bfg --delete-files .env.production --no-blob-protection"
echo "   - Reescribe historial: git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo "4) Forzar push: git push --force --all (coordinar con equipo)\n"

echo "Nota: Este script es solo guía. No ejecuta ninguna eliminación automática." 
