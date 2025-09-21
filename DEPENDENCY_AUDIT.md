# Auditoría de dependencias y seguridad - GRUPO GAD

## 1. poetry check
- El archivo `pyproject.toml` fue modificado manualmente y no coincide con el lockfile.
- Advertencias por duplicidad de campos: `[project.*]` y `[tool.poetry.*]`.
- Recomendación: Ejecutar `poetry lock` para regenerar el lockfile y limpiar advertencias, pero NO hacerlo si hay otro asistente trabajando en dependencias.

## 2. poetry show --tree
- No se detectan dependencias rotas ni incompatibles.
- Varias dependencias usan `typing-extensions` en diferentes versiones, pero no hay conflictos activos.
- No se observan duplicados críticos ni dependencias obsoletas.

## 3. safety
- No está instalado en el entorno. Para instalar y ejecutar:
  ```bash
  poetry add --group dev safety
  poetry run safety check --full-report
  ```
- Recomendación: Ejecutar este comando periódicamente para detectar vulnerabilidades conocidas.

## 4. Recomendaciones generales
- Mantener actualizado el lockfile (`poetry.lock`).
- Revisar advertencias de Poetry tras cada cambio en dependencias.
- Ejecutar auditorías de seguridad regularmente.
- No modificar dependencias mientras otro asistente (IA o humano) esté trabajando en el entorno.

---

**Última auditoría:** Septiembre 2025
