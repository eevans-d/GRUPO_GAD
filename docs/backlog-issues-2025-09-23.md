# Backlog — 2025-09-23

## 1) Backlog: Pruebas E2E de WebSockets (no crítico)
- Descripción: Implementar un script E2E mínimo que valide conexión válida/ inválida a WebSockets y verifique mensajes y cierres esperados, sin cambiar lógica.
- Criterios de aceptación:
  - Conexión con credenciales/parámetros válidos recibe handshake OK y ping/pong operativo.
  - Conexión inválida (sin token o con parámetros incorrectos si aplica) se cierra con código y mensaje consistente.
  - No se modifica ninguna ruta ni lógica de negocio existente.
- Etiquetas sugeridas: `backlog`, `testing`, `low-priority`

## 2) Backlog: Revisar exclusiones temporales de mypy
- Descripción: Reducir gradualmente las exclusiones en `pyproject.toml` añadiendo type hints en los módulos afectados, sin romper CI, manteniendo 0 secretos en logs.
- Criterios de aceptación:
  - Remover exclusiones de 1–2 archivos por iteración con PR pequeño y validaciones verdes.
  - Mantener `mypy` verde y `pytest` verde.
  - Confirmar que logs no exponen secretos (inspección manual básica + grep de patrones sensibles).
- Etiquetas sugeridas: `backlog`, `tech-debt`, `low-priority`

## 3) Backlog: Normalizar ruff (estilo) sin cambiar lógica
- Descripción: Corregir hallazgos F541 (f-strings sin placeholders), F401 (imports no usados) y E501 (línea larga) únicamente donde no afecte comportamiento ni runtime.
- Criterios de aceptación:
  - PRs pequeños (micro-PR) que corrigen estilo sin tocar lógica/contratos.
  - `ruff check` en verde sin deshabilitar reglas.
  - Confirmar cero cambios de interfaz o mensajes funcionales.
- Etiquetas sugeridas: `backlog`, `testing`, `style`, `low-priority`
