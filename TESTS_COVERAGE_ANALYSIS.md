# Análisis de tests y cobertura - GRUPO GAD (sept-2025)

Este informe refleja el estado actual tras estabilizar pruebas y modernizar la CI.

## Resumen de ejecución actual
- Comando: `pytest --cov=src --cov-report=term-missing --disable-warnings -v`
- Resultado: suite verde con 1 SKIP esperado.
- Cobertura total aproximada local: 74% (umbral CI configurado: 85%).

Notas:
- El skip corresponde a `tests/test_models.py` por conflicto de nombres con `src/api/models`.
- La CI sube el reporte HTML `htmlcov` como artifact para inspección detallada.

## Áreas con cobertura baja (o 0%) que conviene apuntar
- `src/api/database.py` → 0%
- `src/api/models.py` → 0% (probablemente contenedor/obsoleto)
- `src/core/database.py` → ~45%
- Routers con ramas sin cubrir (401/403/422): `auth.py`, `users.py`, `tasks.py`, `dashboard.py`.
- `src/api/dependencies.py` con caminos de error (50%).

## Plan de subida a ≥85% (rápido y seguro)
1) Smoke y salud del servicio (fácil +3-5%)
   - Testear `/metrics` y `lifespan` de `src/api/main.py` con `TestClient`.
   - Verificar CORS headers básicos en una petición simple.

2) Ramas de error típicas (fácil +5-8%)
   - `auth`: credenciales inválidas → 401.
   - `users`/`tasks`: sin token → 401; token sin permisos (si aplica) → 403.
   - Validaciones 422 en `create` y `update` con payloads inválidos.

3) Núcleo de base de datos (medio +5-7%)
   - Tests directos sobre `src/core/database.py` verificando que `get_db_session` produce sesiones y cierra correctamente.
   - Cobertura de inicialización por defecto con SQLite en memoria.

4) Módulos a 0% (fácil +2-3%)
   - `src/api/database.py` y `src/api/models.py`: confirmar si siguen en uso; si son puentes/legacy, añadir tests mínimos de import o plan de eliminación.

## Ejemplos de pruebas a añadir
- `tests/test_health_and_metrics.py`
  - GET `/metrics` → 200 y formato esperado.
- `tests/test_auth_errors.py`
  - POST `/auth/login` con credenciales inválidas → 401.
- `tests/test_users_errors.py`
  - GET `/users/` sin token → 401.
  - POST `/users/` con payload incompleto → 422.
- `tests/test_tasks_errors.py`
  - GET `/tasks/` sin token → 401.
  - POST `/tasks/` con payload inválido → 422.

## Consideraciones
- Mantener tests deterministas: usar SQLite en memoria y dependencias sobreescritas (como en `tests/conftest.py`).
- Evitar acoplar tests a implementación interna; probar contratos de endpoints y efectos observables.
- Revisar si `mypy` puede pasar a “hard-fail” tras una ronda de ajuste de tipos.

## Próximos pasos
1. Añadir 5-8 pruebas según ejemplos de arriba para subir de ~74% a ≥85%.
2. Confirmar en CI que el umbral se supera (artifact `htmlcov` debe reflejarlo).
3. Decidir sobre `src/api/database.py` y `src/api/models.py`: cubrir o retirar si son legacy.
