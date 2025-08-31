# Plan de Acción: GRUPO GAD - Próximos Pasos

**Fecha:** 30 de Agosto de 2025
**Fase Actual:** FASE 6 - Pruebas y Calidad de Código

## Introducción

Este documento detalla la hoja de ruta de ejecución para estabilizar y asegurar la calidad del proyecto **GRUPO GAD**. Las siguientes acciones se basan en el análisis técnico y los documentos de estrategia (`EXECUTIVE_ROADMAP.md`, `PROJECT_LOG.md`).

El objetivo principal es abordar las deficiencias críticas de calidad y robustez antes de continuar con el desarrollo de nuevas funcionalidades.

---

## ✅ Checklist de Tareas Inmediatas (FASE 6)

Estas tareas deben realizarse en secuencia para establecer una línea base clara del estado del proyecto y abordar los problemas más urgentes.

### **Paso 1: Análisis de Calidad de Código (Linting y Tipado)**

*   **Objetivo:** Identificar y documentar todos los errores de estilo, bugs potenciales y problemas de tipado estático en la base del código.
*   **Archivos Clave:** Todo el directorio `src/`.
*   **Comandos a Ejecutar:**
    ```bash
    # Generar informe de Ruff (linter)
    poetry run ruff check . --output-format=full > ruff_report.txt

    # Generar informe de MyPy (tipado)
    poetry run mypy . > mypy_report.txt
    ```
*   **Criterio de Aceptación:**
    *   Se han creado los archivos `ruff_report.txt` y `mypy_report.txt`.
    *   El contenido de estos archivos servirá como una lista de tareas para la refactorización y corrección de código.

### **Paso 2: Ejecución de Pruebas y Cobertura**

*   **Objetivo:** Ejecutar la suite de pruebas existente para detectar regresiones y generar un informe de cobertura que muestre qué partes del código no están probadas.
*   **Archivos Clave:** `tests/`, `pytest.ini`.
*   **Comando a Ejecutar:**
    ```bash
    # Ejecutar pytest y generar un informe de cobertura en formato HTML
    poetry run pytest --cov=src --cov-report=html
    ```
*   **Criterio de Aceptación:**
    *   La suite de pruebas se ejecuta completamente (los fallos son aceptables en esta fase inicial).
    *   Se crea un directorio `htmlcov/` con el informe de cobertura detallado, accesible abriendo `htmlcov/index.html` en un navegador.

### **Paso 3: Corregir Schemas de Actualización (Gap de Seguridad)**

*   **Objetivo:** Solucionar la vulnerabilidad que permite la actualización de campos sensibles en los endpoints de `PUT`.
*   **Archivos Clave:**
    *   `src/schemas/usuario.py`
    *   `src/schemas/tarea.py`
*   **Acción a Realizar:**
    1.  Modificar la clase `UsuarioUpdate` para que solo incluya los campos que un usuario puede modificar (ej: `email`, `nombre`, `password`, todos opcionales).
    2.  Modificar la clase `TareaUpdate` para que solo incluya los campos actualizables de una tarea (ej: `titulo`, `descripcion`, `estado`, `fecha_vencimiento`, todos opcionales).
*   **Criterio de Aceptación:**
    *   Las clases `UsuarioUpdate` y `TareaUpdate` ya no son `pass`, sino que definen explícitamente los campos permitidos para una operación de actualización.

### **Paso 4: Implementar Pruebas Unitarias y de Integración**

*   **Objetivo:** Aumentar la fiabilidad del código creando pruebas para la lógica de negocio y los flujos de API críticos.
*   **Archivos Clave:** `tests/unit/`, `tests/integration/`.
*   **Acción a Realizar:**
    1.  **Pruebas Unitarias:** Añadir tests para los `services` y `crud` que no tengan cobertura.
    2.  **Pruebas de Integración:** Crear un nuevo archivo de prueba que simule un flujo completo:
        *   Crear un usuario.
        *   Obtener un token de autenticación.
        *   Usar el token para crear una tarea.
        *   Actualizar la tarea.
        *   Eliminar la tarea.
*   **Criterio de Aceptación:**
    *   La cobertura de pruebas, medida con el comando del **Paso 2**, aumenta a un mínimo del 85%.

---

## 🚀 Blueprint de Tareas Estratégicas (Post-Fase 6)

Una vez que la base del código sea estable y esté probada, se deben abordar las siguientes deficiencias arquitectónicas.

### **Paso 5: Implementar Sistema de Logging Centralizado**

*   **Objetivo:** Dotar a la aplicación de la capacidad de registrar eventos, errores y peticiones para facilitar la depuración y monitorización.
*   **Archivos Clave:** `src/api/main.py`, `src/bot/main.py`, `config/settings.py`.
*   **Acción a Realizar:**
    1.  Añadir `loguru` a las dependencias en `pyproject.toml`.
    2.  Configurar `loguru` en el arranque de la aplicación (`main.py`) para que escriba en la consola y/o en un archivo de log (`logs/api.log`).
    3.  Añadir un middleware a FastAPI para registrar todas las peticiones HTTP entrantes.
    4.  Añadir llamadas de log explícitas en los bloques `try/except` y en puntos clave de la lógica de negocio.
*   **Criterio de Aceptación:**
    *   La aplicación genera logs estructurados y útiles durante su ejecución.

### **Paso 6: Integrar Alembic para Migraciones de Base de Datos**

*   **Objetivo:** Eliminar el riesgo de la gestión manual del esquema de la base de datos, implementando un sistema de migraciones versionado y automático.
*   **Archivos Clave:** `pyproject.toml`, `alembic.ini` (nuevo), `alembic/` (nuevo directorio).
*   **Acción a Realizar:**
    1.  Añadir `alembic` a las dependencias en `pyproject.toml` y ejecutar `poetry install`.
    2.  Inicializar Alembic: `poetry run alembic init alembic`.
    3.  Configurar `alembic/env.py` para que apunte a los modelos de SQLAlchemy y a la URL de la base de datos.
    4.  Generar la primera migración automática: `poetry run alembic revision --autogenerate -m "Initial migration"`.
    5.  Aplicar la migración a la base de datos: `poetry run alembic upgrade head`.
*   **Criterio de Aceptación:**
    *   El comando `alembic upgrade head` se ejecuta correctamente.
    *   Se crea una tabla `alembic_version` en la base de datos.
    *   Los futuros cambios en los modelos de `src/api/models/` pueden ser gestionados con `alembic revision --autogenerate`.
