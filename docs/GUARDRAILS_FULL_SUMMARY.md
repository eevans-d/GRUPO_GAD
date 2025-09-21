# GUARDRAILS — Resumen consolidado y hoja de ruta

Fecha: 2025-09-06
Branch activo: `chore/guardrails-env-fixes`

## 1) Propósito
Consolidar en un único documento todo lo realizado por el flujo Guardrails (scripts, parches, respaldos) y proporcionar una hoja de ruta y checklist priorizada para continuar el trabajo de forma segura.

## 2) Acciones realizadas (resumen)
- Ejecutado instalador/flujo Guardrails y creado artefactos iniciales.
- Añadido/actualizado (commits en `chore/guardrails-env-fixes`):
  - `.gitignore` — ignorar `.env.production`
  - `.env.example` — plantilla sin secretos
  - `config/settings.py` — parche (anotar `env_files` como ClassVar)
  - `src/core/auth.py` — shim para compatibilidad de imports
  - `scripts/guardrails.sh`, `scripts/check_allowlist.py` (existentes/previos)
  - `scripts/rotate_secrets.sh` — guía documental para rotación
  - `scripts/prepare_repo_backup.sh` — crea mirror bare (backup)
  - `scripts/perform_history_cleanup.sh` — guía de limpieza destructiva (BFG/git-filter-repo)
  - `docs/SECRETS_ROTATION.md` — pasos operativos para rotar secretos
  - `docs/PR_BODY.md` — cuerpo del PR listo para pegar en GitHub
  - `docs/GUARDRAILS_REGISTRY.md` — entradas registradas durante la sesión

## 3) Backup y seguridad
- Backup espejo creado localmente: `backups/git-mirror-20250906T062707Z` (mirror bare)
- `.env.production` fue sanitizado (valores reemplazados con placeholders). Nota: esto no elimina las versiones anteriores del historial.

## 4) Estado de pruebas y validaciones
- `PYTHONPATH=. .venv/bin/pytest -q` → todos los tests locales pasaron.
- `scripts/check_allowlist.py` → salida: ✓ Allowlist PyPI OK.
- Alembic: se comprobó en modo neutral con `DB_URL=sqlite+aiosqlite:///:memory:` para evitar conectar a la DB real; no se ejecutó `alembic upgrade head` en producción.

## 5) Commits y branch
- Branch remoto: `chore/guardrails-env-fixes` (push realizado). 
- Commits recientes (resumen): cambios en env, settings, auth shim, scripts y docs. (Ver `git log` para hashes completos.)

## 6) PR
- PR draft creado como archivo `docs/PR_BODY.md`. Enlace para abrir PR en GitHub:
  https://github.com/eevans-d/GRUPO_GAD/pull/new/chore/guardrails-env-fixes

## 7) Hoja de ruta / Checklist priorizada (acciones para continuar)

P0 — Inmediato (0-24h)
- [ ] Abrir PR y revisar con el equipo (no destructivo). Responsable: equipo.
- [ ] Rotar credenciales en proveedores: DB password, SECRET_KEY, Telegram token, otras API keys. (Hacer antes de limpiar historial.)
- [ ] Actualizar entornos (staging/production) con nuevas credenciales.

P0 — Verificación
- [ ] Ejecutar `alembic upgrade head` en staging/DB controlada y validar endpoints de salud.
- [ ] Validar login/logout cookie E2E en entorno con la API corriendo.

P1 — Limpieza de historial (destructivo)
- [ ] Crear backup espejo final (`scripts/prepare_repo_backup.sh`) y moverlo a almacenamiento seguro.
- [ ] Ejecutar `git-filter-repo` o BFG en el mirror para eliminar `.env.production` y cualquier fichero con secretos.
- [ ] Empujar forzado (`git push --force --all`) y avisar a todos los colaboradores para reclonar.

P2 — CI y prevención
- [ ] Añadir workflow CI que ejecute `pytest` y `scripts/check_allowlist.py` en PRs.
- [ ] Añadir pre-commit hooks y bloqueo para evitar commitear `.env` reales.

P3 — Observabilidad / hardening
- [ ] Añadir métricas, logging estructurado y healthchecks en Docker Compose.

## 8) Comandos útiles (reproducibles)
```bash
# Tests
PYTHONPATH=. .venv/bin/pytest -q

# Crear backup mirror (local)
bash scripts/prepare_repo_backup.sh

# Ejecutar pruebas alembic en modo neutral (no afecta DB real)
DB_URL=sqlite+aiosqlite:///:memory: .venv/bin/alembic current

# Limpiar historial (ejemplo; NO ejecutar sin backup y coordinación)
# git clone --mirror <repo> repo-mirror.git
# cd repo-mirror.git
# git filter-repo --invert-paths --paths .env.production
# git push --force --all
```

## 9) Dónde retomar mañana
- Revisa y abre el PR desde la rama `chore/guardrails-env-fixes`.
- Coordina ventana y rota credenciales antes de cualquier limpieza de historial.
- Si autorizas, puedo ejecutar la limpieza destructiva guiada (requiere confirmación explícita).

---
Archivos clave y notas de auditoría ya añadidos al repo en `docs/` y `scripts/`.

Fin del resumen consolidado.
