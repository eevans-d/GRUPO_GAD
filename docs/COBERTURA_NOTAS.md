# Notas sobre Cobertura de WebSockets

Este documento explica el warning observado al ejecutar un subconjunto reducido de tests con `--cov=src/core/websockets`:

```
CoverageWarning: Module src.core.websockets was never imported. (module-not-imported)
No data was collected.
```

## Causa

Cuando se ejecuta únicamente un test muy específico (p.ej. `tests/test_websocket_manager_stats.py`) pytest puede:

1. No forzar la importación temprana del módulo bajo cobertura antes de que coverage inicie el trace; o
2. Resolver rutas relativas de forma distinta si el paquete raíz no se detecta como paquete importable según `PYTHONPATH` / layout.

En la ejecución completa de la batería de pruebas el módulo sí se importa de manera natural (p.ej. a través de las rutas FastAPI o de otros tests de WebSocket), por lo que el warning no aparece.

## Solución Temporal (sin romper modo "Barco Anclado")

Se agrega un test mínimo `test_websocket_import.py` que:

- Importa explícitamente `websocket_manager`.
- Llama `get_stats()` para verificar estructura base.
- No abre conexiones ni inicia el heartbeat (éste solo se crea tras el primer `accept()`).

Esto fuerza a coverage a registrar el módulo incluso en ejecuciones selectivas.

## Acciones Diferidas (Post "Desanclaje")

- Evaluar ajuste de `pyproject.toml` / `pytest.ini` para definir `--cov` paths estándar sin necesidad de test de import artificial.
- Posible uso de `coverage run -m pytest` con `source=src/core` para reducir discrepancias de path.
- Añadir reportes XML/HTML para pipeline CI (si no existen) y umbrales mínimos.

## Riesgos Evitados

- No se modifica lógica de producción.
- No se agrega instrumentación intrusiva.
- No se adelanta integración Prometheus (solo documentación separada).

## Comandos de Ejemplo

Ejecutar test específico asegurando cobertura del módulo:

```
pytest -q tests/test_websocket_import.py --cov=src/core/websockets --cov-report=term-missing
```

Ejecutar subset original (ya debería dejar de mostrar el warning):

```
pytest -q tests/test_websocket_manager_stats.py --cov=src/core/websockets --cov-report=term-missing
```

## Estado

Implementado el test de import mínimo. Sin cambios funcionales.
