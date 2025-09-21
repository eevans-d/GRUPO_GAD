Título: [URGENTE] Guardrails & env hardening — revisar y ejecutar roadmap

Resumen

Este issue agrupa las tareas necesarias para asegurar que el repositorio `GRUPO_GAD` no contenga secretos en texto plano, que los desarrolladores tengan una plantilla `.env.example` y que exista un plan coordinado para rotar credenciales y limpiar el historial si procede.

Archivos y cambios de referencia (rama `chore/guardrails-env-fixes`)

- `.env.example` (plantilla)
- `.env.production` (sanitizado con placeholders)
- `config/settings.py` (ClassVar fix)
- `src/core/auth.py` (shim)
- `scripts/prepare_repo_backup.sh` (crea mirror bare)
- `scripts/perform_history_cleanup.sh` (guía para BFG/git-filter-repo)
- `scripts/rotate_secrets.sh` (guía documental)
- `docs/SECRETS_ROTATION.md`
- `docs/GUARDRAILS_FULL_SUMMARY.md` (resumen consolidado)
- `docs/PR_BODY.md` (texto PR listo)

Backup

- Mirror creado: `backups/git-mirror-20250906T062707Z` (verificar y mover a almacenamiento seguro antes de operaciones destructivas)

Objetivo del issue

1) Abrir PR con los cambios (rama: `chore/guardrails-env-fixes`) y revisarlo. No contiene limpieza destructiva.
2) Coordinar rotación de credenciales en proveedores (DB, JWT secret, Telegram token, etc.).
3) Tras rotación y validación en staging, ejecutar limpieza del historial si se acuerda.

Checklist propuesto (usa esta lista para triage):

- [ ] Abrir PR desde `chore/guardrails-env-fixes` y asignar reviewers
- [ ] Reproducir tests localmente: `PYTHONPATH=. .venv/bin/pytest -q`
- [ ] Revisar y aprobar `.env.example`
- [ ] Validar que la aplicación arranca con placeholders en `.env` (staging)
- [ ] Rotar credenciales en proveedores y actualizar entornos (staging/production)
- [ ] Verificar servicios en staging (health endpoints, login/logout)
- [ ] Crear backup espejo final (`scripts/prepare_repo_backup.sh`) y mover a almacenamiento seguro
- [ ] Ejecutar limpieza de historial en mirror (git-filter-repo / BFG) — solo tras aprobación
- [ ] Forzar push del mirror reescrito y notificar a todo el equipo
- [ ] Añadir CI jobs para bloquear commiteo de `.env` reales y ejecutar checks (pytest + allowlist)

Asignación sugerida

- Responsable técnico: @owner (reemplazar por usuario GitHub)
- DevOps / DB: @db-admin
- QA: @qa

Notas finales

Este documento está en `docs/` para que lo uses como plantilla al crear el Issue en GitHub; contiene los enlaces y pasos reproducibles para la operación. Ejecutar la limpieza destructiva requiere confirmación explícita y coordinación con todo el equipo.
