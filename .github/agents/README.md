# AI Agent System for GitHub Copilot - GRUPO_GAD

**Versión:** 1.0.0  
**Parte:** 1/3 - Agentes Core y Arquitectura  
**Fecha:** 2025-01-04

---

## 📋 Descripción

Este directorio contiene el **sistema multi-agente especializado** para GitHub Copilot en el proyecto GRUPO_GAD. Cada archivo define un agente con rol específico, instrucciones contextualizadas al proyecto, y guidelines para actuar de forma efectiva.

## 🎯 Objetivo

Proporcionar prompts estructurados que guíen a GitHub Copilot para actuar como agentes especializados en diferentes aspectos del desarrollo, **siempre contextualizados** a la arquitectura, tecnologías y convenciones de GRUPO_GAD.

## 🤖 Agentes Disponibles (Parte 1/3)

### 1. Project Coordinator Agent
**Archivo:** `01_PROJECT_COORDINATOR.md`  
**Rol:** Coordinador central de proyectos

**Responsabilidades:**
- Analizar contexto del repositorio GRUPO_GAD
- Crear planes de ejecución detallados
- Coordinar implementación entre componentes
- Sincronizar trabajo de otros agentes
- Generar entregas documentadas y validadas

**Cuándo usar:**
- Inicio de nueva feature o proyecto
- Necesitas descomponer tarea grande en subtareas
- Requieres planificación con dependencias
- Coordinar trabajo entre múltiples desarrolladores
- Validar completitud de entregas

**Ejemplo de invocación:**
```markdown
@coordinator Planifica la implementación de un sistema de notificaciones en tiempo real
que integre con el WebSocket existente, persista en PostgreSQL y exponga endpoints REST.
```

---

### 2. Solution Architect Agent
**Archivo:** `02_SOLUTION_ARCHITECT.md`  
**Rol:** Arquitecto de soluciones

**Responsabilidades:**
- Analizar arquitectura actual de GRUPO_GAD
- Diseñar soluciones escalables y mantenibles
- Especificar componentes, interfaces y contratos
- Documentar decisiones arquitectónicas con justificación
- Asegurar integración con sistema existente

**Cuándo usar:**
- Antes de implementar funcionalidad compleja
- Necesitas diseñar nuevos componentes
- Requieres evaluar alternativas técnicas
- Definir estructura de datos y APIs
- Resolver problemas arquitectónicos

**Ejemplo de invocación:**
```markdown
@architect Diseña la arquitectura para un sistema de permisos granulares que permita
control de acceso a recursos a nivel de entidad, integrándose con el sistema de autenticación
JWT existente sin romper la arquitectura en capas actual.
```

---

### 3. Software Developer Agent
**Archivo:** `03_SOFTWARE_DEVELOPER.md`  
**Rol:** Desarrollador implementador

**Responsabilidades:**
- Implementar código siguiendo diseños arquitectónicos
- Seguir convenciones y estándares de GRUPO_GAD
- Escribir código limpio, testeable y documentado
- Crear tests unitarios y de integración
- Validar con linters y herramientas del proyecto

**Cuándo usar:**
- Implementar features diseñadas por Architect
- Crear nuevos endpoints, servicios o CRUDs
- Escribir tests para código existente o nuevo
- Refactorizar código siguiendo patrones
- Fix de bugs con tests de regresión

**Ejemplo de invocación:**
```markdown
@developer Implementa el diseño de NotificationService especificado en el documento de
arquitectura. Incluye CRUD operations, service layer, endpoints REST, y tests con cobertura
>= 85%. Seguir patrones existentes en src/api/services/auth.py
```

---

## 🏗️ Arquitectura del Proyecto GRUPO_GAD

### Stack Tecnológico Principal
- **Backend:** FastAPI 0.115+, Uvicorn
- **Database:** PostgreSQL con SQLAlchemy 2.0 Async
- **Migraciones:** Alembic 1.13+
- **Auth:** JWT (python-jose) + bcrypt
- **WebSockets:** Sistema real-time con heartbeat
- **Cache/Pub-Sub:** Redis 5.0+
- **Testing:** pytest 8.x + pytest-asyncio + pytest-cov
- **Linting:** ruff, mypy
- **Deployment:** Docker, Docker Compose, Caddy

### Estructura de Directorios Clave
```
GRUPO_GAD/
├── src/
│   ├── api/              # API FastAPI
│   │   ├── main.py       # Entry point
│   │   ├── routers/      # Endpoints
│   │   ├── services/     # Business logic
│   │   ├── crud/         # DB operations
│   │   └── middleware/   # Middleware
│   ├── core/             # Core functionality
│   │   ├── database.py   # DB engine
│   │   ├── websockets.py # WebSocket manager
│   │   ├── security.py   # Auth & JWT
│   │   └── logging.py    # Structured logging
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   └── bot/              # Telegram bot
├── config/
│   └── settings.py       # Pydantic Settings
├── alembic/              # DB migrations
├── tests/                # pytest tests
│   ├── unit/
│   └── integration/
├── dashboard/            # Static frontend
├── docker/               # Dockerfiles
├── docs/                 # Documentation
├── scripts/              # Automation scripts
└── .github/
    ├── copilot-instructions.md  # Quick guide
    └── agents/                  # This directory
```

### Convenciones Principales
1. **Settings:** Usar `get_settings()` (lazy singleton)
2. **Database:** Async everywhere con `AsyncSession`
3. **Logging:** `get_logger(__name__)` para logging estructurado
4. **Routers:** Registrar en `src/api/routers/__init__.py`
5. **Tests:** SQLite in-memory (pytest.ini)
6. **Validación:** Pydantic v2 con `ConfigDict`

---

## 📖 Cómo Usar Estos Agentes

### Opción 1: Mención Explícita (Recomendado)

En tu prompt a GitHub Copilot, menciona el agente que quieres activar:

```markdown
@coordinator Planifica implementación de [feature]

@architect Diseña arquitectura para [componente]

@developer Implementa [tarea según diseño]
```

### Opción 2: Contexto Implícito

Describe tu necesidad y GitHub Copilot puede inferir qué agente usar:

**Ejemplo - Activa Coordinator:**
> "Necesito implementar un sistema de reportes. ¿Puedes crear un plan de implementación
> detallado que considere la arquitectura actual de GRUPO_GAD?"

**Ejemplo - Activa Architect:**
> "Quiero añadir soporte para múltiples roles de usuario. ¿Cómo debería diseñarse
> esto para integrarse con el sistema de autenticación JWT existente?"

**Ejemplo - Activa Developer:**
> "Implementa un endpoint GET /api/v1/reports que liste reportes con paginación,
> siguiendo el patrón de los routers existentes en el proyecto."

### Opción 3: Workflow Completo

Para features complejas, usa los agentes en secuencia:

```markdown
1. @coordinator Crea plan para implementar sistema de reportes PDF

2. @architect Diseña arquitectura del generador de reportes, considerando:
   - Generación async para reportes largos
   - Storage de PDFs generados
   - API para consulta de estado
   - Integración con modelos existentes

3. @developer Implementa el diseño de Architect con tests >= 85% cobertura
```

---

## 🎨 Templates y Ejemplos

Cada agente incluye templates completos y ejemplos contextualizados a GRUPO_GAD:

### Coordinator - Plan de Tarea
- Estructura de carpetas específica del proyecto
- Dependencias entre componentes existentes
- Checklist de validación
- Comandos específicos de GRUPO_GAD

### Architect - Diseño Arquitectónico
- Análisis de arquitectura actual
- Modelo de datos con SQLAlchemy
- Diseño de APIs REST
- Decisiones con alternativas evaluadas
- Integraciones con WebSocket, Redis, etc.

### Developer - Implementación
- Templates de Model, Schema, CRUD, Service, Router
- Convenciones de nomenclatura del proyecto
- Patterns de testing (unit + integration)
- Validación pre-commit (ruff, mypy, pytest)

---

## ✅ Validación y Calidad

Todos los agentes siguen los mismos estándares de calidad:

### Checklist de Código
- [ ] Sigue convenciones de nomenclatura (snake_case, PascalCase)
- [ ] Type hints en todas las funciones públicas
- [ ] Docstrings (Google style)
- [ ] Async/await en operaciones I/O
- [ ] Usa `get_settings()` para configuración
- [ ] Logging con `get_logger(__name__)`

### Checklist de Tests
- [ ] Tests unitarios para lógica de negocio
- [ ] Tests de integración end-to-end
- [ ] Cobertura >= 85% en código nuevo
- [ ] Casos: happy path, validaciones, errores, edge cases
- [ ] Mocks apropiados (DB, servicios externos)

### Checklist de Validación
- [ ] `ruff format src/ tests/` - Formateo
- [ ] `ruff check src/ tests/ --fix` - Linting
- [ ] `mypy src/` - Type checking
- [ ] `pytest --cov=src --cov-report=term-missing` - Tests + cobertura
- [ ] Todos los tests pasan (100%)
- [ ] No hay warnings de deprecación

### Checklist de Documentación
- [ ] Docstrings actualizados
- [ ] README.md si añade funcionalidad pública
- [ ] OpenAPI schemas correctos en /docs
- [ ] CHANGELOG.md entrada del cambio

---

## 🔧 Comandos Útiles

### Desarrollo
```bash
# Ejecutar API local
uvicorn src.api.main:app --reload

# Con Docker
docker compose up -d --build
docker logs -f gad_api_dev

# Migraciones
alembic upgrade head
alembic revision --autogenerate -m "descripción"
```

### Testing
```bash
# Tests rápidos
pytest -q

# Tests con cobertura
pytest --cov=src --cov-report=term-missing

# Tests específicos
pytest tests/unit/test_auth.py -v

# Ver cobertura HTML
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Linting y Formateo
```bash
# Formateo automático
ruff format src/ tests/

# Linting con auto-fix
ruff check src/ tests/ --fix

# Type checking
mypy src/
```

### Docker
```bash
# Build y levantar
docker compose up -d --build

# Ver logs
docker logs -f gad_api_dev

# Bash en contenedor
docker exec -it gad_api_dev bash

# Limpiar y rebuild
docker compose down -v
docker compose up -d --build
```

---

## 📚 Referencias

### Documentación del Proyecto
- **Guía rápida:** `.github/copilot-instructions.md`
- **Análisis técnico:** `docs/deployment/01_ANALISIS_TECNICO_PROYECTO.md`
- **README principal:** `README.md`
- **Action plan:** `GRUPO_GAD_ACTION_PLAN.md`

### Documentación Externa
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [pytest](https://docs.pytest.org/)

---

## 🚀 Próximos Pasos

### Parte 2/3: Agentes de Calidad y Seguridad (Próximamente)
- **QA Agent:** Testing exhaustivo, casos edge, performance
- **Security Agent:** Análisis de vulnerabilidades, best practices
- **Performance Agent:** Optimización, profiling, caching

### Parte 3/3: Agentes de Operaciones (Próximamente)
- **DevOps Agent:** Deployment, CI/CD, monitoring
- **Documentation Agent:** Docs técnicas, user guides, API docs

---

## 🤝 Contribuir

### Mejorar Agentes Existentes
Si encuentras que un agente necesita mejora:

1. Identifica qué falta o está incorrecto
2. Verifica contra el código actual de GRUPO_GAD
3. Propón mejora específica contextualizada al proyecto
4. Actualiza documentación relevante

### Reportar Issues
Si un agente da instrucciones incorrectas:

1. Documenta el contexto (qué pediste)
2. Qué respuesta dió el agente
3. Por qué es incorrecta según GRUPO_GAD
4. Qué debería haber respondido

---

## 📝 Changelog

### v1.0.0 (2025-01-04)
- ✅ **Parte 1/3 completada:** Agentes Core
  - Project Coordinator Agent
  - Solution Architect Agent
  - Software Developer Agent
- ✅ Templates completos contextualizados a GRUPO_GAD
- ✅ Ejemplos prácticos de uso
- ✅ Integración con arquitectura existente
- ✅ Convenciones y estándares del proyecto

---

## 📄 Licencia

Este sistema de agentes es parte del proyecto GRUPO_GAD y sigue la misma licencia (MIT).

---

**¿Preguntas o dudas?**  
Consulta `.github/copilot-instructions.md` para guía rápida del proyecto, o revisa el agente específico que necesites.

**Inicio rápido:**
1. Lee este README completo
2. Revisa `.github/copilot-instructions.md`
3. Explora el agente que necesites (01, 02 o 03)
4. Invoca al agente en tu prompt con `@[role]` o contexto implícito

---

*Sistema multi-agente para GitHub Copilot - Parte 1/3: Agentes Core y Arquitectura*
