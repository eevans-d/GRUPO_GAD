# Checklist de Pruebas E2E (End-to-End)

Este documento contiene el checklist de pruebas para asegurar la funcionalidad y robustez del sistema GAD. Está basado en la sección "Pruebas y Operación" del GAD Agile Kit.

## Casos de Prueba Clave (20)

### Autenticación (5 casos)

*   [ ] **Positivo Nivel 1:** Un usuario con Nivel 1 puede ejecutar comandos de Nivel 1 (e.g., `/mi_estado`).
*   [ ] **Negativo Nivel 1:** Un usuario con Nivel 1 NO puede ejecutar comandos de Nivel 2 o 3 (e.g., `/crear_tarea`).
*   [ ] **Positivo Nivel 3:** Un usuario con Nivel 3 puede ejecutar comandos de todos los niveles.
*   [ ] **Negativo No Whitelist:** Un usuario de Telegram que NO está en la whitelist no puede interactuar con el bot.
*   [ ] **Borde:** Un ID de whitelist es removido, el usuario pierde el acceso inmediatamente.

### Tareas (8 casos)

*   [ ] **Creación Exitosa:** Un usuario Nivel 3 puede crear una nueva tarea con efectivos disponibles.
*   [ ] **Creación con Conflicto:** El sistema previene la creación de una tarea si los efectivos asignados tienen conflictos de turno o licencias.
*   [ ] **Finalización por Delegado (Frase):** El delegado de la tarea puede finalizarla usando una frase clave (e.g., "LISTO TSK-001").
*   [ ] **Finalización por Delegado (Comando):** El delegado de la tarea puede finalizarla usando el comando `/finalizar TSK-001`.
*   [ ] **Negativo Finalización No Delegado:** Un usuario que no es el delegado NO puede finalizar la tarea.
*   [ ] **Liberación Grupal:** Al finalizar una tarea, todos los efectivos asignados cambian su estado a 'activo'.
*   [ ] **Query Disponibles:** El comando `/disponibles` muestra correctamente los efectivos activos.
*   [ ] **Borde Tarea Inexistente:** Intentar finalizar una tarea con un código que no existe arroja un error amigable.

### Auto-Mejora (3 casos)

*   [ ] **Refresh de Métricas:** La vista materializada `mv_metricas_duraciones` se actualiza después de finalizar 5 o más tareas.
*   [ ] **Generación de Sugerencia:** Al crear una tarea de un tipo con suficientes datos históricos, el sistema sugiere la dotación de personal.
*   [ ] **Sin Sugerencia:** Al crear una tarea de un tipo sin datos históricos, el sistema no ofrece sugerencias.

### Resiliencia (4 casos)

*   [ ] **Reinicio del Bot:** Si el contenedor del bot se reinicia, se reconecta y sigue funcionando.
*   [ ] **Reinicio de la API:** Si el contenedor de la API se reinicia, el bot maneja el error temporalmente y se reconecta.
*   [ ] **Health Check:** El endpoint `/health` de la API siempre responde con `{"status": "ok"}`.
*   [ ] **Fallback Manual:** Un administrador (Nivel 3) puede forzar la finalización de una tarea directamente a través de la API si el bot falla.
