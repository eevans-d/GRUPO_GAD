# 📦 Documentación Final - GRUPO GAD

## 1. Descripción General
- Proyecto GRUPO GAD: API y backend para gestión de tareas, usuarios y operaciones de seguridad.
- Stack: Python 3.12+, FastAPI, SQLAlchemy Async, Alembic, Poetry 2.x, Docker.

## 2. Instalación y Setup

### Requisitos
- Python 3.12+
- Docker (opcional)
- Poetry 2.x

### Instalación
```bash
git clone https://github.com/eevans-d/GRUPO_GAD.git
cd GRUPO_GAD
poetry install
cp .env.example .env
```

### Migraciones
```bash
alembic upgrade head
```

### Tests
```bash
pytest --disable-warnings -v
```

## 3. Despliegue

### Local
```bash
uvicorn src.api.main:app --reload
```

### Producción (Docker)
```bash
docker-compose up --build -d
```

## 4. Endpoints Principales

- `/auth/login` - Autenticación de usuarios
- `/users/` - CRUD de usuarios
- `/tasks/` - CRUD de tareas
- `/dashboard/` - Panel de control

## 5. Seguridad

- Validación de campos sensibles en actualizaciones
- Hash de contraseñas
- Tokens JWT para autenticación

## 6. Migraciones y Base de Datos

- Alembic configurado para SQLite y PostgreSQL
- Migraciones reproducibles y seguras

## 7. Auditoría y Calidad

- Linter: ruff
- Tipado: mypy
- Tests: pytest (>78% cobertura)
- Script de auditoría de seguridad incluido

## 8. Checklist de Entrega

- [x] Migraciones aplicadas y validadas
- [x] Tests en verde
- [x] Seguridad y robustez garantizadas
- [x] Documentación actualizada
- [x] Listo para producción