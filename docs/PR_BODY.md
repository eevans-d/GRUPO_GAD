Título: chore: guardrails env fixes — .env.example, ignore, settings, auth shim, secrets docs

Resumen

Este PR agrupa varios cambios de bajo riesgo para mejorar la seguridad operativa y la experiencia de desarrollo:

- Añade `.env.example` con placeholders y añade `.env.production` a `.gitignore`.
- Anota `env_files` como `ClassVar` en `config/settings.py` para evitar errores de Pydantic en tiempo de importación.
- Añade un shim `src/core/auth.py` para restaurar imports esperados por `dashboard` (evita romper tests/arranque).
- Sanea `.env.production` reemplazando valores sensibles por placeholders.
- Añade documentación y scripts de ayuda relacionados con la rotación y limpieza de secretos:
  - `docs/SECRETS_ROTATION.md` — pasos operativos para rotar y limpiar secretos.
  - `scripts/prepare_repo_backup.sh` — crea un mirror bare como backup pre-limpieza.
  - `scripts/rotate_secrets.sh` — guía documental para la rotación.
  - `scripts/perform_history_cleanup.sh` — guía con comandos ejemplo para `git-filter-repo`/BFG.
- Actualiza `docs/GUARDRAILS_REGISTRY.md` registrando las acciones realizadas y el backup creado.

Motivación

Estos cambios reducen el riesgo de exponer secretos por accidente y facilitan la ejecución local del proyecto sin depender de credenciales reales. La eliminación definitiva de secretos del historial NO se hace en este PR; eso requiere una operación destructiva separada y coordinación del equipo.

Checklist para reviewers

- [ ] Reproducir tests localmente: `PYTHONPATH=. .venv/bin/pytest -q`
- [ ] Comprobar que `.env.example` cubre todas las variables necesarias para dev
- [ ] Verificar que `config/settings.py` no rompe importaciones/arranque (usar `.env` con placeholders)
- [ ] Confirmar que el dashboard admin sirve correctamente y que el shim `src/core/auth.py` es aceptable
- [ ] Revisar `docs/SECRETS_ROTATION.md` y planificar ventana para limpieza del historial si se decide

Notas de seguridad y despliegue

- Se creó un backup espejo en `backups/git-mirror-20250906T062707Z` antes de cualquier acción destructiva.
- Si se decide limpiar historial, usar `git-filter-repo` o BFG en espejo, empujar forzado y pedir a todos los colaboradores que reclonen.

Comandos útiles para reviewers

```bash
# ejecutar tests
PYTHONPATH=. .venv/bin/pytest -q

# arrancar en dev (ejemplo)
cp .env.example .env
# rellenar valores en .env si se prueban endpoints que necesitan credenciales
.venv/bin/uvicorn src.api.main:app --reload
```

Link para crear PR en GitHub (ya puedes abrirla):
https://github.com/eevans-d/GRUPO_GAD/pull/new/chore/guardrails-env-fixes
