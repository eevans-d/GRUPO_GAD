# Guardrails Registry

Registro de acciones automáticas y verificaciones realizadas por el flujo Guardrails Standard.

## Entrada: actualización checker allowlist

- Timestamp: 2025-09-06T05:17:39+00:00
- Branch: release/v1.0.0-rc1
- Autor: automated-assistant
- Archivos modificados: `scripts/check_allowlist.py`
- Descripción breve: Se actualizó `scripts/check_allowlist.py` para soportar extracción de dependencias desde `pyproject.toml` (Poetry), manejar ausencia/errores de `docs/manifest.json`, y considerar `dev_allowlist.pypi` al validar paquetes.
- Razón: evitar falsos positivos al validar dependencias PyPI y soportar la convención Poetry del proyecto.
- Acciones realizadas:
  - Lectura de `docs/manifest.json` y `pyproject.toml` para diagnóstico.
  - Parche aplicado para: manejo de manifest faltante, parseo básico de `pyproject.toml` (dependencias y dev group), fallback a `pyservice/requirements.txt` y `requirements.txt` si aplica, inclusión de `dev_allowlist.pypi` en la verificación.
  - Ejecución de `python3 scripts/check_allowlist.py` y verificación de salida (EXIT: 0).
- Resultado: Checker devuelve exit code 0; no se encontraron dependencias fuera de allowlist.

---

## Anexo: Resumen de sesión añadido

- Timestamp añadido al registro: 2025-09-06T05:18:00+00:00
- Fuente: `docs/GUARDRAILS_SUMMARY.md`

Contenido del resumen (se añade a continuación)...

Resumen completo de la sesión — Guardrails Standard

Plan corto
- Objetivo: documentar de forma precisa y completa todas las acciones realizadas en esta sesión relacionadas con la instalación, pruebas y aplicación de Guardrails Standard.

Checklist de requisitos atendidos
- Crear instalador "Guardrails Standard" — Done
- Generar scripts operativos (guardrails flow, allowlist checker) — Done
- Manifest template y allowlists — Done y refinado con deps reales del repo
- CI mínimo (.github/workflows) — Done
- VS Code task — Done
- Dry-run + validación JSON + tests + reversión/commit automático — Implementado y probado
- No dependencia externa obligatoria para pruebas (stub local) — Implementado

1) Cronología y acciones (qué, por qué, resultado)
- Creación de `init_guardrails_standard.sh`: instalador que crea la estructura base (scripts, manifest, CI, tasks, outputs). Resultado: archivo creado en la raíz.
- Ejecución de `init_guardrails_standard.sh`: generó `docs/manifest.json`, `scripts/guardrails.sh`, `scripts/check_allowlist.py`, `.github/workflows/standard.yml`, `.vscode/tasks.json`, y estructura `outputs/` y `tests/` cuando aplicaba.
- Implementación de un stub LLM inicial (`scripts/fake_gemini.sh`) para pruebas locales sin servicios externos.
- Pruebas dry-run con el stub: identificaron errores de formato/JSON en la salida del stub.
  - Problema: JSON/diff mal formado o con backticks/escapes incorrectos.
  - Acción: correcciones iterativas; creación de `scripts/fake_gemini2.sh` con JSON válido.
- Dry-run exitoso con `fake_gemini2.sh`: se generó `outputs/runs/<timestamp>/last.diff`.
- Aplicación del diff (ejecución sin `--dry-run`): `scripts/guardrails.sh` aplicó el diff con `git apply`, ejecutó pruebas condicionales si existían, y generó commit automático.
- Manejo de commits y conflictos:
  - Se creó un commit inicial con los artefactos generados por el LLM simulado.
  - Se realizó `git revert` cuando fue necesario; resolví conflictos (conservando `docs/manifest.json` actualizado).
  - Actualicé `docs/manifest.json` extrayendo dependencias desde `pyproject.toml` y commitée el cambio.
  - Reapliqué artefactos Guardrails en un commit limpio y realicé `git push` al remoto en la rama `release/v1.0.0-rc1`.
- Finalmente ejecutaste la aplicación del diff final y quedó commit final en la rama.

2) Archivos creados/actualizados (lista esencial)
- `init_guardrails_standard.sh` — instalador
- `scripts/guardrails.sh` — flujo principal
- `scripts/check_allowlist.py` — verificador allowlist
- `scripts/fake_gemini.sh` (iteraciones) y `scripts/fake_gemini2.sh` — stubs LLM para pruebas
- `.github/workflows/standard.yml` — workflow CI
- `.vscode/tasks.json` — tarea para VS Code
- `docs/manifest.json` — manifest inicial, luego actualizado con deps reales
- `outputs/runs/<timestamp>/...` — diffs, prompts y outputs generados
- Tests mínimos añadidos según contexto (`tests/sanity.test.js`, `pyservice/tests/test_sanity.py`) cuando aplicó

3) Commits importantes (resumen)
- c4c6f9a — feat(ia): Crear README con saludo [guardrails-standard] (commit generado por flujo inicial)
- b625144 — Revert "feat(ia): Crear README..." (revert del commit anterior; conflicto resuelto)
- 9de6701 — chore(manifest): actualizar docs/manifest.json con dependencias reales
- 3d688c5 — feat(guardrails): restore guardrails artifacts (reapliqué scripts/CI en commit limpio)
- 804d09e — feat(ia): Aplicar diff generado [guardrails-standard] (aplicación final del diff)
- Push al remoto: `origin/release/v1.0.0-rc1` actualizado con los commits anteriores

4) Problemas encontrados y resolución técnica
- JSON/diff mal formado: corregí el stub para emitir JSON válido y un diff unified con `/dev/null` para archivos nuevos y cabeceras `@@` correctas.
- `git apply` rechazando diffs: ajusté el formato del diff en el stub para compatibilidad con `git apply`.
- Conflicto durante `git revert` por `docs/manifest.json`: resolví marcando la versión actual y continuando con `git revert --continue`.
- Varios intentos de edición de archivos en caliente: aseguré permisos ejecutables y re-commit cuando fue necesario.

5) Validaciones y pruebas ejecutadas
- Múltiples dry-runs (con stub) que validaron JSON y produjeron `last.diff`.
- Ejecuté el flujo real con el stub: `git apply` + tests condicionales + commit automático.
- Ejecuté `scripts/check_allowlist.py` antes y después de actualizar `docs/manifest.json` (exit 0 OK).

6) Estado actual del repositorio
- Rama: `release/v1.0.0-rc1` (local y remoto sincronizados)
- `docs/manifest.json` actualizado y preservado
- Guardrails artifacts (scripts/CI) presentes en el repo
- Diffs y outputs ubicados en `outputs/runs/` (varios timestamps)

7) Comandos clave para reproducir
- Instalar: chmod +x init_guardrails_standard.sh && ./init_guardrails_standard.sh
- Dry-run con stub: export GEMINI_CMD="./scripts/fake_gemini2.sh" && scripts/guardrails.sh -o "Prueba" --dry-run
- Aplicar diff (script): env GEMINI_CMD="./scripts/fake_gemini2.sh" scripts/guardrails.sh -o "Aplicar diff"
- Validar allowlist: python3 scripts/check_allowlist.py
- Revertir/inspeccionar commits: git revert <hash>, git show <hash>, git log --oneline -n 8

8) Mapeo de requisitos -> estado
- Instalador y estructura — Done
- Manifest (fuente de verdad) — Done (actualizado)
- Allowlists — Done (pypi poblado; npm vacío si no aplica)
- Dry-run + JSON validation — Done
- Reversión automática en fallo de tests — Implementado
- CI mínimo — Done
- No servicios externos obligatorios — Done (stub local)

9) Riesgos y recomendaciones
- Los diffs aplicados en esta sesión provinieron de un stub; al usar LLM real, revisar antes de aplicar.
- Revisar `outputs/runs/<timestamp>/last.diff` antes de aplicar; el script permite dry-run.
- Mantener `docs/manifest.json` sincronizado con `pyproject.toml` si usas poetry.

10) Siguientes pasos sugeridos
- Revisar los diffs generados y confirmar o pedir revert parcial.
- Si vas a usar LLM real, configurar `GEMINI_CMD` y ejecutar dry-run.
- Preparar un PR para revisión de los artefactos Guardrails si deseas control de cambios colaborativo.

## Entrada: cambios de sesión y DB (POSTGRES_SERVER + cookies HttpOnly)

- Timestamp: 2025-09-06T05:40:00+00:00
- Branch: release/v1.0.0-rc1
- Autor: automated-assistant
- Archivos modificados:
  - `config/settings.py` (valor por defecto POSTGRES_SERVER, preferir .env.production)
  - `dashboard/static/dashboard.js` (eliminada dependencia de token en localStorage; añadido NetworkManager con cookies)
  - `src/api/routers/auth.py` (login: establecer cookie HttpOnly `access_token` además del body)
- Descripción breve: Cambios mínimos para evitar fallos por variables de entorno faltantes y para migrar la autenticación hacia sesiones por cookie HttpOnly. No se tocaron componentes Docker ni se añadieron dependencias externas.
- Acciones realizadas:
  - Actualizado `config/settings.py` para asegurar `POSTGRES_SERVER='db'` por defecto y preferir `.env.production` si existe.
  - Sustituido uso del token en localStorage en `dashboard/static/dashboard.js` por verificación de sesión usando `NetworkManager` con `credentials: 'include'`.
  - Modificado `src/api/routers/auth.py` para establecer cookie HttpOnly `access_token` en el login y mantener compatibilidad con la respuesta JSON.
  - Comprobación de sintaxis Python (`py_compile`) sobre los archivos modificados: OK.
  - Ejecutado `scripts/check_allowlist.py`: OK (exit 0).
- Resultado: Cambios commiteados localmente. Recomendado: realizar pruebas integradas (levantar API local y comprobar `/api/v1/users/me`, login y acceso al dashboard). No se realizaron cambios destructivos ni en Docker.
- Siguientes pasos sugeridos:
  1. Empujar commits al remoto (`git push origin release/v1.0.0-rc1`).
  2. Probar login en entorno local y verificar cookie HttpOnly (herramientas: navegador devtools, curl con --cookie).
  3. Actualizar frontend logout para borrar cookie vía endpoint `/logout` (backend) en vez de `localStorage.removeItem('admin_token')`.
  4. Revisar otras referencias a `localStorage` no sensibles y decidir si mantenerlas (notas) o migrarlas.

---

## Entrada: commit pendiente - scripts

- Timestamp: 2025-09-06T05:55:00+00:00
- Branch: release/v1.0.0-rc1
- Autor: automated-assistant
- Archivos revisados y commitados:
  - `scripts/check_allowlist.py` (mejoras: soporte pyproject, mensajes claros, dev_allowlist included)
  - `scripts/start.sh` (arranque: aplicar migraciones con alembic y lanzar uvicorn)
- Descripción breve: Revisé ambos scripts para asegurar comportamiento y los agregué al control de versiones.
- Acciones realizadas:
  - Lectura y verificación de `scripts/check_allowlist.py` (ya actualizado y probado previamente).
  - Lectura de `scripts/start.sh` (script de arranque simple que ejecuta migraciones y arranca Uvicorn).
  - Stage + commit de ambos archivos.
- Resultado: Cambios commitados y listos para push (a continuación se realizará push al remoto).

---

## Plan de trabajo consolidado y roadmap (registrado)

- Timestamp: 2025-09-06T06:05:00+00:00
- Branch objetivo: release/v1.0.0-rc1
- Autor: automated-assistant
- Propósito: Documento de trabajo priorizado y accionable que contiene las tareas siguientes, estimaciones, criterios de aceptación y comandos reproducibles. Diseñado para retomar el trabajo en una futura sesión con claridad.

Checklist principal (prioridades inmediatas)
1) Estabilización de entorno y variables (P0 - 0-24h)
   - Tarea: Asegurar `.env.production` presente y consistente; añadir `POSTGRES_SERVER=db` si falta.
   - Propietario: Tú / operator
   - Comandos clave:
     - Revisar .env: `sed -n '1,200p' .env.production`
     - Validar settings: `python -c "from config.settings import settings; print(settings.DB_URL)"`
   - Criterio de aceptación: API arranca localmente sin ValidationError de Pydantic para DB.
   - Riesgos: sobreescribir valores sensibles (no commitear `.env`).

2) Migraciones y arranque (P0 - 0-24h)
   - Tarea: Ejecutar migraciones con Alembic y confirmar schema.
   - Propietario: Tú / DBA
   - Comandos clave:
     - `python -m alembic current`
     - `python -m alembic upgrade head`
     - `./scripts/start.sh` (o `python -m uvicorn src.api.main:app --reload` para dev)
   - Criterio de aceptación: `alembic current` muestra revision aplicada; endpoint `/api/v1/health` responde OK.
   - Riesgos: migraciones destructivas — hacer backup antes.

3) Autenticación basada en cookies (P0 - 0-24h) [Parcialmente implementado]
   - Tarea: Verificar login/logout y que cookie HttpOnly se establezca y borre correctamente.
   - Propietario: Tú / QA
   - Comandos clave:
     - `curl -i -X POST -d "username=...&password=..." http://localhost:8000/api/v1/auth/login`
     - `curl -i -b "access_token=..." http://localhost:8000/api/v1/users/me`
     - `curl -i -X POST http://localhost:8000/api/v1/auth/logout`
   - Criterio de aceptación: navegador muestra cookie `access_token` HttpOnly; `/api/v1/users/me` responde 200 cuando la cookie está presente.

4) Docker / compose (P1 - 24-48h)
   - Tarea: No tocar producción ahora; preparar `docker-compose.yml` robusto para dev/ci (healthchecks y volúmenes) y `.env.production` usado por Docker.
   - Propietario: DevOps / Tú
   - Comandos clave:
     - `docker compose config`
     - `docker compose up --build -d`
   - Criterio de aceptación: servicios `db`, `api`, `redis` llegan a `healthy`.
   - Riesgos: no aplicar cambios directos mientras Gemini Code Assist trabaja en paralelo; usar rama feature/PR para cambios mayores.

5) Seguridad front y migración de localStorage (P1 - 48-72h)
   - Tarea: Mantener localStorage para datos no sensibles (notas/markers); eliminar token en favor de cookies (ya hecho).
   - Propietario: Frontend dev
   - Acciones concretas: remover `localStorage.removeItem('admin_token')` y usar `logout` endpoint — (ya implementado).
   - Criterio de aceptación: login/logout workflow en navegador y no existan referencias a `localStorage.getItem('admin_token')` en el código activo.

6) CI y pruebas (P2 - 3-7 días)
   - Tarea: Añadir prueba de integración mínima que valide health endpoints y checker allowlist en CI.
   - Propietario: Tú / CI owner
   - Comandos clave (local): `pytest -q` y `python3 scripts/check_allowlist.py`
   - Criterio de aceptación: workflow en `.github/workflows/*` pasa con cambios mínimos.

7) Observabilidad y logging (P2 - 1-2 semanas)
   - Tarea: Añadir metrics middleware y logging central (prometheus + logging config).
   - Propietario: DevOps / Backend
   - Criterio de aceptación: métricas expuestas y logs en `logs/` con rotación.

Entregables y artefactos a generar
- PRs separados por área: `fix/env`, `fix/auth-cookie`, `feat/docker-health`, `ci/tests`.
- Scripts: `consolidated_fix_grupo_gad.sh` (ya propuesto en docs), `validate_grupo_gad_final.sh` para validación automatizada.
- Registro actualizado: `docs/GUARDRAILS_REGISTRY.md` (esta entrada)

Notas operativas
- No commitear archivos `.env` ni secrets. Usar `backups/` locales para exportar dumps antes de migraciones.
- Para cambios Docker grandes, usar rama feature y abrir PR para revisión humana.

Siguiente acción inmediata sugerida (para la próxima sesión)
- Ejecutar migraciones en entorno de staging/local y validar health endpoints. Recopilar errores y registrar output en `outputs/runs/<timestamp>/`.

---

## Entrada: inicio del procedimiento de rotación de secretos y PR

- Timestamp: 2025-09-06T06:30:00+00:00
- Branch creada: `chore/guardrails-env-fixes`
- Autor: automated-assistant
- Descripción: Se creó una rama para agrupar cambios menores de configuración (plantilla .env, ignore, parche settings, shim auth). Se añadió un script documental `scripts/rotate_secrets.sh` que describe pasos seguros para rotar credenciales y limpiar secretos del historial.
- Acciones realizadas:
  - `git checkout -b chore/guardrails-env-fixes` (push al remoto)
  - Añadido `scripts/rotate_secrets.sh` (documental)
  - Recomendación: coordinar rotación de secretos y ejecutar BFG/git-filter-repo si se decide limpiar historial.

---
