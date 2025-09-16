# Análisis de tests y cobertura - GRUPO GAD (sept-2025)

Este informe resume el estado actual de los tests, las causas de las fallas y las acciones recomendadas. No se realizaron cambios en el código fuente.

## Resumen de ejecución
- Comando: `pytest --cov=src --cov-report=term-missing --disable-warnings -v`
- Resultado: 48 tests ejecutados, 45 OK, 3 FAIL, 1 SKIP
- Cobertura total: 79% (umbral configurado en 85% en `[tool.pytest.ini_options].addopts`)

## Fallas detectadas (3)
Archivo: `tests/test_core_database.py`

1) test_async_session_factory_run
- Error: `TypeError: 'NoneType' object is not callable`
- Causa probable: `AsyncSessionFactory` es `None` en `src/core/database.py`.

2) test_async_engine_exists
- Error: `assert None is not None`
- Causa probable: `async_engine` es `None` en `src/core/database.py`.

3) test_async_session_factory
- Error: `assert callable(session_factory)` -> es `None`
- Causa probable: Igual que (1): `AsyncSessionFactory` no inicializado correctamente.

## Diagnóstico raíz
`src/core/database.py` no está inicializando el motor asíncrono ni la fábrica de sesiones durante la importación de módulo (contexto de tests). Con SQLite asincrónico, la URL debe ser `sqlite+aiosqlite:///./dev.db` y se requiere tener instalado `aiosqlite` (ya instalado).

Adicionalmente, los tests esperan que el módulo exponga:
- `async_engine` (instancia creada)
- `AsyncSessionFactory` (callable que retorna `AsyncSession`)

## Recomendaciones (sin aplicar cambios)

1) Inicialización segura en `src/core/database.py`
- Asegurar fallback para entorno de test si `DATABASE_URL` no está seteada o si apunta a SQLite:

Sugerencia de implementación (referencia):

```python
# src/core/database.py
from __future__ import annotations
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
```

2) Validar importación
- Evitar inicializar a `None` y luego setear; crear directamente `async_engine` y `AsyncSessionFactory` como arriba.

3) Ajustes de entorno para tests
- Verificar que `DATABASE_URL` en `.env` (o variables de entorno del runner) use `sqlite+aiosqlite` durante tests.
- Confirmar que `aiosqlite` está instalado (ya se hizo).

4) Umbral de cobertura
- Actualmente 79% < 85% (umbral). Aunque arreglemos los 3 tests, la ejecución fallará por cobertura si no se supera 85%.
- Opciones:
  - Aumentar cobertura con tests sobre `src/api/database.py`, `src/core/database.py`, `routers`, etc.
  - Temporalmente bajar `--cov-fail-under` a 75-80% solo localmente (no recomendado para CI) hasta subir cobertura con nuevos tests.

## Áreas con cobertura baja o 0%
- `src/api/database.py` -> 0%
- `src/api/models.py` -> 0% (archivo contenedor, quizá obsoleto)
- `src/core/database.py` -> 64%
- `src/api/main.py` -> 76%
- Routers `tasks.py` (81%) y `users.py` (78%) pueden ganar 2-5% con tests adicionales

## Sugerencias de tests rápidos para subir cobertura (sin tocar código)
- Añadir pruebas de importación y smoke de `src/api/main.py` con `TestClient` validando `/health`.
- Mock de `AsyncSessionFactory` para validar creación de sesión.
- Tests de rutas `users` y `tasks` para ramas no cubiertas (errores 401/403, validaciones 422).

## Próximos pasos propuestos
1. Aplicar la inicialización segura en `src/core/database.py` (snippet anterior).
2. Re-ejecutar tests; validar que los 3 FAIL pasan.
3. Añadir 2-3 tests de smoke adicionales para superar el 85% o ajustar temporalmente el umbral local.

Nota: Si deseas, puedo aplicar el cambio mínimo en `src/core/database.py` y agregar 2 tests pequeños para levantar cobertura, manteniendo consistencia con el proyecto.
