# Proyecto GRUPO_GAD — Guía de referencia operativa y lista de verificación

Propósito
--------
Este documento ofrece una guía operativa y de seguridad para desarrolladores y agentes automatizados que trabajen con el repo GRUPO_GAD.
Incluye: estructura del proyecto, dependencias críticas, pasos reproducibles (comandos), hardening recomendado, snippets prácticos y una checklist mínima para PRs y despliegues.

Resumen de cambios en esta versión
----------------------------------
- Ampliada la sección de hardening con comandos reproducibles (`pip-audit`, `gitleaks`, `pre-commit`).
- Añadidos snippets seguros: plantilla `.env.example`, patrón seguro de carga de `settings` (Pydantic v2), recomendación para `alembic/env.py` (import lazy).
- Lista concreta de secrets que crear en GitHub y nombres estándar.

Checklist inicial (rápida)
-------------------------
- Revisar siempre `.env` y `.env.production` antes de ejecutar cualquier script.
- Confirmar que CI usa `secrets.*` (no valores codificados).
- Ejecutar tests y `pip-audit` localmente antes de abrir PR.
- Asegurar que `config/settings.py` y `alembic/env.py` son import-safe.

Índice rápido
-----------
1. Estructura y archivos clave
2. Dependencias y entorno
3. Seguridad práctica y comandos
4. Patrón seguro para `config/settings.py` (ejemplo)
5. Patrón seguro para `alembic/env.py` (ejemplo)
6. CI / Secrets recomendados
7. Checklist PR / Deploy
8. Operaciones frecuentes y runbook
9. Archivos añadidos / cambios propuestos

1. Estructura y archivos clave
------------------------------
- `config/` — configuraciones centrales; `config/settings.py` contiene la lógica para resolver `DATABASE_URL` y otras variables.
- `alembic/` — migraciones; `env.py` se ejecuta en distintos contextos (offline/online), debe ser robusto a falta de envs.
- `docker/`, `docker-compose.yml` — entornos de desarrollo; `docker/init_postgis.sql` inicializa PostGIS.
- `.github/workflows/` — pipelines CI (lint/test/build/security).

2. Dependencias y entorno
-------------------------
- Python 3.11+
- FastAPI, Pydantic v2 (pydantic-settings), SQLAlchemy async + asyncpg
- PostGIS (imagen `postgis/postgis:15-*`), Redis
- Dev: pytest, ruff, black, pip-audit, gitleaks, pre-commit

3. Seguridad práctica y comandos
--------------------------------
Acciones rápidas (local):

```bash
# Exportar dependencias y auditar
poetry export -f requirements.txt -o requirements.txt --without-hashes
pip-audit -r requirements.txt

# Ejecutar gitleaks local para búsqueda rápida (si instalado)
gitleaks detect --source . --report-path gitleaks-report.json || true

# Ejecutar tests
poetry run pytest -q

# Formateo y linters (pre-commit)
pre-commit run --all-files
```

Recomendaciones:
- Automatizar `pip-audit` y `gitleaks` en CI (job `security`) y decidir si vulnerabilidades bloquean PR.
- Mantener `.env.example` en el repo con placeholders `CHANGEME_*` y nunca subir `.env` real.

4. Patrón seguro para `config/settings.py` (Pydantic v2)
-----------------------------------------------------
Resumen: permitir una instanciación "permissive" para tareas de lectura o scripts que no requieran todas las variables. A continuación un patrón recomendado (pseudo-snippet):

```py
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    DATABASE_URL: str | None = Field(default=None)
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    SECRET_KEY: str | None = None

    model_config = {
        "extra": "ignore",
        "validate_assignment": True,
    }

    def assemble_db_url(self) -> str | None:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB:
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return None

# Evitar instanciar Settings() en import si no se necesita; cuando se haga, atrapar errores o usar .construct() para lectura no validante.
```

Notas:
- Para scripts que sólo requieren una variable puntual (por ejemplo la URL), preferir `os.getenv("DATABASE_URL")` en lugar de instanciar el Settings global.

5. Patrón seguro para `alembic/env.py`
-------------------------------------
Problema: `alembic/env.py` no debe importar `settings` a nivel de módulo si ese import lanza excepciones cuando faltan variables de entorno.

Recomendación: importar settings dentro de `run_migrations_online()` / `run_migrations_offline()`.

Ejemplo (esquema):

```py
def run_migrations_online():
    # import local y perezoso
    from config.settings import Settings
    settings = Settings()
    engine = create_async_engine(str(settings.assemble_db_url()), poolclass=pool.NullPool)
    ...
```

6. CI / Secrets recomendados
----------------------------
Crear en GitHub repo settings los siguientes secrets (nombres recomendados):

- POSTGRES_PASSWORD
- POSTGRES_USER (opcional si se usa distinto)
- POSTGRES_DB
- POSTGRES_SERVER
- POSTGRES_PORT
- DATABASE_URL (útil si se prefiere pasar la URL completa)
- SECRET_KEY
- TELEGRAM_TOKEN
- DOCKER_USERNAME
- DOCKER_PASSWORD

Snippet de job security (GitHub Actions) sugerido:

```yaml
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Export requirements
        run: poetry export -f requirements.txt -o requirements.txt --without-hashes
      - name: Run pip-audit
        run: pip-audit -r requirements.txt || true
      - name: Run gitleaks
        run: gitleaks detect --source . || true
```

7. Checklist PR / Deploy
------------------------
- [ ] `git grep -n "password\|secret\|token"` sin valores en claro
- [ ] `pre-commit run --all-files` (format + linters)
- [ ] `pip-audit` y/o reporte en el job `security`
- [ ] Tests pasan (`pytest`)
- [ ] `.env` no se incluye en el diff

8. Operaciones frecuentes y runbook
----------------------------------
- Levantar entorno local (dev):

```bash
cp .env.example .env
docker compose up -d --build
poetry install --no-root
poetry run pytest -q
```

- Verificar PostGIS:

```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT PostGIS_version();"
```

- Backup y rollback:

```bash
PGUSER=$POSTGRES_USER PGDATABASE=$POSTGRES_DB pg_dump -h $POSTGRES_SERVER -p $POSTGRES_PORT -U $POSTGRES_USER > backup-$(date +%F).sql
# Para restaurar: psql -U $POSTGRES_USER -d $POSTGRES_DB -f backup-YYYY-MM-DD.sql
```

9. Archivos añadidos / cambios propuestos
----------------------------------------
- Añadir `.env.example` con placeholders `CHANGEME_*` (si no existe) y comprobar que `.env` está en `.gitignore`.
- Refactor corto a `config/settings.py`: exponer `assemble_db_url()` y evitar `Settings()` en import a nivel módulo.
- Ajustar `alembic/env.py` para import perezoso de settings.

Anexos: `.env.example` (plantilla)
--------------------------------
Se recomienda mantener un `.env.example` con placeholders en la raíz del repo. Copiarlo a `.env` y rellenar con valores del entorno o de GitHub Secrets en CI.

Fin del documento.
