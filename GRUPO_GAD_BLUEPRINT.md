# 📘 Hoja de Ruta y Checklist Absoluta - GRUPO GAD

## 1. Introducción y Conceptos Clave

### 1.1. Descripción General
GRUPO GAD es una plataforma backend para la gestión de tareas, usuarios y operaciones de seguridad. Permite crear, actualizar y monitorear tareas, usuarios y estados, con autenticación segura y control de acceso.

### 1.2. Arquitectura y Componentes
- API REST (FastAPI)
- Base de Datos (SQLite/PostgreSQL, SQLAlchemy, Alembic)
- Autenticación JWT
- Tests, linter, tipado y auditoría
- Despliegue local y Docker

### 1.3. Glosario
FastAPI, SQLAlchemy, Alembic, Poetry, Docker, JWT, Linter, Tests

---

## 2. Instalación y Preparación

### 2.1. Requisitos
- Linux/Windows/MacOS
- Python 3.12+
- Poetry
- Docker (opcional)

### 2.2. Clonado y Estructura
```bash
git clone https://github.com/eevans-d/GRUPO_GAD.git
cd GRUPO_GAD
```
Carpetas principales: src/, tests/, alembic/, README.md, .env.example, docker-compose.yml

### 2.3. Instalación y Configuración
```bash
poetry install
cp .env.example .env
poetry shell
```
Edita `.env` si usas PostgreSQL.

---

## 3. Migraciones y Base de Datos

### 3.1. Configuración
- Desarrollo: SQLite (`dev.db`)
- Producción: PostgreSQL (edita `.env` y/o `docker-compose.yml`)

### 3.2. Migraciones
```bash
alembic upgrade head
```
Si modificas modelos:
```bash
alembic revision --autogenerate -m "mensaje"
alembic upgrade head
```

### 3.3. Problemas Comunes
- Error de conexión: revisa `DATABASE_URL` y el servicio DB
- Conflictos: elimina migraciones viejas y genera una nueva
- SQLite solo para desarrollo

---

## 4. Ejecución y Pruebas

### 4.1. Arranque
- Local: `uvicorn src.api.main:app --reload`
- Docker: `docker-compose up --build -d`

### 4.2. Tests y Cobertura
```bash
pytest --disable-warnings -v
pytest --cov=src --cov-report=term-missing
```

### 4.3. Auditoría
```bash
poetry run ruff check .
poetry run mypy . --strict
```
Revisa el script de auditoría si existe.

---

## 5. Uso de la API y Endpoints

### 5.1. Autenticación
- `/auth/login` (token JWT)
- `/users/` (CRUD usuarios)

### 5.2. Tareas
- `POST /tasks/` (crear)
- `PUT /tasks/{task_id}` (actualizar)
- `GET /tasks/` (listar)
- `DELETE /tasks/{task_id}` (eliminar)

### 5.3. Dashboard
- `/dashboard/` (métricas y estado)

### 5.4. Ejemplo cURL
```bash
curl -X POST "http://localhost:8000/auth/login" -d "username=usuario&password=contraseña"
curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"123456","nombre":"Test","apellido":"User"}'
curl -X POST "http://localhost:8000/tasks/" -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"titulo":"Nueva tarea","tipo":"PATRULLAJE","delegado_usuario_id":1,"inicio_programado":"2025-09-12T10:00:00"}'
```

---

## 6. Mantenimiento, Actualizaciones y Despliegue

### 6.1. Actualización
```bash
poetry update
```
Si cambias modelos:
```bash
alembic revision --autogenerate -m "nueva migración"
alembic upgrade head
```

### 6.2. Errores Frecuentes
- Verifica `DATABASE_URL` y servicio DB
- Elimina migraciones viejas si hay conflictos
- Ejecuta `poetry install` o `poetry update` si hay problemas

### 6.3. Buenas Prácticas
- No subas contraseñas/credenciales
- Mantén `.env` fuera del control de versiones
- Ejecuta tests y auditoría antes de cada despliegue
- Haz backup antes de cambios mayores

### 6.4. Checklist Final
- Tests en verde
- Migraciones aplicadas
- Seguridad validada
- Despliegue con Docker o servidor
- Backup realizado

---

## 7. Expansión, Futuro y Recursos

### 7.1. Pedir Ayuda
- Explica el problema y da ejemplos
- Indica archivo y sección relevante
- Usa esta documentación como contexto

### 7.2. Sugerencias
- Notificaciones por email/Telegram
- Roles y permisos avanzados
- Mejorar dashboard
- Automatizar backups

### 7.3. Recursos
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Poetry](https://python-poetry.org/docs/)
- [Docker](https://docs.docker.com/get-started/)

---

**Archivo generado:** `/home/eevan/ProyectosIA/GRUPO_GAD/GRUPO_GAD_BLUEPRINT.md`

Esta guía te permitirá operar, mantener y expandir GRUPO GAD de forma segura y eficiente. Si necesitas profundizar en algún punto, puedes pedir ayuda a una IA o profesional usando este documento como base.
