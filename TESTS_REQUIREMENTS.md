# Requisito para ejecución de tests: pytest-asyncio

Para ejecutar los tests y obtener el reporte de cobertura en este proyecto, es necesario tener instalado el paquete `pytest-asyncio` en el entorno de desarrollo.

## Instalación (solo entorno local, no modifica dependencias globales)

```bash
poetry add --group dev pytest-asyncio
```

Luego, ejecuta:

```bash
pytest --cov=src --cov-report=term-missing --disable-warnings -v
```

---

Si tienes dudas sobre la instalación o el entorno, consulta la documentación en `GRUPO_GAD_BLUEPRINT.md` o pide ayuda a una IA o profesional.
