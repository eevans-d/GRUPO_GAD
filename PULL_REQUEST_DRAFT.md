# CI moderna + test stability + docs

## 🎯 Objetivo
Dejar el repositorio con una CI confiable (lint, typing, tests, cobertura) y pruebas estables sin depender de servicios externos.

### ✅ Cambios principales

**CI (GitHub Actions):**
- Nuevo workflow `.github/workflows/ci.yml`:
	- Python 3.12 + Poetry 2.x mediante pipx, cache de `.venv`.
	- Lint con `ruff`, type-check con `mypy` (no bloqueante por ahora).
	- `pytest` con cobertura (HTML artifact y `--cov-fail-under=85`).
	- Base de datos para tests: `sqlite+aiosqlite:///:memory:`.
- `.github/workflows/standard.yml`: se removió la parte de Python para evitar duplicidad; mantenemos Node (si aplica) y `semgrep`.

**Pruebas unificadas:**
- Configuración de `pytest` unificada en `pyproject.toml` (se elimina `pytest.ini` en este repo).
- `pythonpath = ["src"]`, `asyncio_mode = "auto"`, filtros de warnings y cobertura.

**Tipado y dependencias:**
- `tests/conftest.py`: corrección de anotación a `AsyncGenerator[AsyncSession, None]`.
- `pyproject.toml`: añadida dependencia `requests` para servicios del bot.

**Docs:**
- `README.md`: agregado badge de CI y sección “CI/CD”.

### 🧪 Verificación
- Suite de tests local: verde (1 skip esperado).
- CI se ejecutará automáticamente al pushear a la rama; artifact `htmlcov` disponible.

### 📌 Notas
- Mantenemos `mypy` como “soft-fail” para no bloquear entregas; podemos endurecerlo en una siguiente iteración.
- Si se prefiere, se puede retirar `standard.yml` completamente y mover `semgrep` al workflow principal.

### 📁 Archivos modificados
- `.github/workflows/ci.yml` (nuevo flujo principal)
- `.github/workflows/standard.yml` (simplificado, sin Python)
- `pyproject.toml` (pytest config consolidada y `requests`)
- `tests/conftest.py` (tipado)
- `README.md` (badge y doc CI)

### 🚀 Siguientes pasos propuestos
1. Endurecer `mypy` a “hard-fail” cuando el tipado esté saneado al 100%.
2. Integrar un badge de cobertura (ej. Codecov) o publicar `coverage.xml` como artifact adicional.
3. Opcional: mover `semgrep` al workflow principal y retirar `standard.yml`.
