# 📚 GRUPO_GAD - Índice de Documentación

**Sistema de Gestión Administrativa Gubernamental**  
Versión: 0.1.0 | FastAPI + PostgreSQL + WebSockets

---

## 🎯 Documentación por Audiencia

### 👨‍💻 Para Desarrolladores

#### Empezando
- [**README.md**](README.md) - Instalación rápida y guía de inicio
- [**CONTRIBUTING.md**](CONTRIBUTING.md) - Guía de contribución al proyecto

#### Arquitectura y Diseño
- [**docs/PROJECT_OVERVIEW.md**](docs/PROJECT_OVERVIEW.md) - Visión general técnica del proyecto
- [**ARCHITECTURAL_ANALYSIS.md**](ARCHITECTURAL_ANALYSIS.md) - Análisis arquitectónico detallado
- [**FUNCTIONAL_ANALYSIS.md**](FUNCTIONAL_ANALYSIS.md) - Análisis funcional del sistema
- [**ESPECIFICACION_TECNICA.md**](ESPECIFICACION_TECNICA.md) - Especificaciones técnicas

#### WebSockets
- [**WEBSOCKET_SYSTEM_STATUS.md**](WEBSOCKET_SYSTEM_STATUS.md) - Estado y documentación del sistema WebSocket
- `src/core/websockets.py` - Implementación del WebSocket Manager
- `src/api/routers/websockets.py` - Endpoints WebSocket
- `dashboard/static/websocket_test.html` - UI de prueba para WebSockets

#### Guías de Desarrollo
- [**REFACTORING_PLAN.md**](REFACTORING_PLAN.md) - Plan de refactorización
- [**OPTIMIZATION_SUMMARY.md**](OPTIMIZATION_SUMMARY.md) - Resumen de optimizaciones
- [**DEPENDENCY_AUDIT.md**](DEPENDENCY_AUDIT.md) - Auditoría de dependencias

#### Copilot Instructions
- [**.github/copilot-instructions.md**](.github/copilot-instructions.md) - Guía para Agentes de IA

---

### 🚀 Para DevOps

#### Despliegue
- [**docs/DEPLOYMENT_GUIDE.md**](docs/DEPLOYMENT_GUIDE.md) - Guía completa de despliegue (si existe)
- [**BLUEPRINT_DESPLIEGUE_EJECUTIVO.md**](BLUEPRINT_DESPLIEGUE_EJECUTIVO.md) - Blueprint ejecutivo de despliegue
- [**DIAGNOSTICO_FINAL_DESPLIEGUE.md**](DIAGNOSTICO_FINAL_DESPLIEGUE.md) - Diagnóstico final pre-despliegue
- [**ROADMAP_TO_PRODUCTION.md**](ROADMAP_TO_PRODUCTION.md) - Roadmap a producción

#### Checklists y Playbooks
- [**CHECKLIST_PRODUCCION.md**](CHECKLIST_PRODUCCION.md) - Checklist pre-producción
- [**docs/PLAYBOOK_ROLLBACK_RUNBOOK.md**](docs/PLAYBOOK_ROLLBACK_RUNBOOK.md) - Procedimiento de rollback (si existe)
- [**docs/PLAYBOOK_FINALIZACION.md**](docs/PLAYBOOK_FINALIZACION.md) - Playbook de finalización (si existe)

#### Infraestructura
- [**docker-compose.yml**](docker-compose.yml) - Configuración Docker para desarrollo
- [**docker-compose.prod.yml**](docker-compose.prod.yml) - Configuración Docker para producción
- [**Caddyfile**](Caddyfile) - Configuración del reverse proxy Caddy
- [**alembic.ini**](alembic.ini) - Configuración de migraciones de base de datos
- **docker/** - Archivos Docker adicionales

#### Scripts de Automatización
- `scripts/smoke_staging.sh` - Tests de humo para staging
- `scripts/emergency_rollback.sh` - Script de rollback de emergencia
- `scripts/security_audit.sh` - Auditoría de seguridad
- `scripts/test_websockets.py` - Cliente de prueba WebSocket
- `scripts/create_dashboard_test_data.py` - Generador de datos de prueba

---

### 🧪 Para QA

#### Testing
- [**TESTS_REQUIREMENTS.md**](TESTS_REQUIREMENTS.md) - Requisitos de testing
- [**TESTS_COVERAGE_ANALYSIS.md**](TESTS_COVERAGE_ANALYSIS.md) - Análisis de cobertura de tests
- [**pytest.ini**](pytest.ini) - Configuración de pytest
- **tests/** - Suite completa de tests
  - `tests/test_dependencies_complete.py` - Tests de dependencias
  - `tests/test_routers_tasks_complete.py` - Tests de router de tareas
  - `tests/test_routers_users_complete.py` - Tests de router de usuarios
  - `tests/test_websockets_handshake.py` - Tests de WebSocket handshake
  - `tests/integration/` - Tests de integración

#### Ejecución de Tests
```bash
# Ejecutar todos los tests
pytest -q

# Ejecutar con cobertura
pytest --cov=src --cov-report=term-missing

# Ejecutar tests específicos
pytest tests/test_dependencies_complete.py -v
```

#### Reportes de Calidad
- **coverage_report.txt** - Reporte de cobertura
- **ruff_report.txt** - Reporte de linting
- **pip_audit_report.json** - Reporte de auditoría de seguridad

---

### 📊 Para Management

#### Roadmaps y Status
- [**EXECUTIVE_ROADMAP.md**](EXECUTIVE_ROADMAP.md) - Roadmap ejecutivo del proyecto
- [**PROJECT_STATUS.md**](PROJECT_STATUS.md) - Estado actual del proyecto
- [**PROJECT_LOG.md**](PROJECT_LOG.md) - Log de actividades del proyecto

#### Análisis y Compliance
- [**Compliance_Audit_v1.0.0.md**](Compliance_Audit_v1.0.0.md) - Auditoría de compliance
- [**ATTACK_PLAN.md**](ATTACK_PLAN.md) - Plan de ataque al proyecto
- [**GRUPO_GAD_ACTION_PLAN.md**](GRUPO_GAD_ACTION_PLAN.md) - Plan de acción
- [**GRUPO_GAD_BLUEPRINT.md**](GRUPO_GAD_BLUEPRINT.md) - Blueprint del proyecto

#### Cambios y Mejoras
- [**CHANGELOG.md**](CHANGELOG.md) - Registro de cambios
- [**ANTES_VS_DESPUES_FASE1.md**](ANTES_VS_DESPUES_FASE1.md) - Comparativa de mejoras Fase 1
- [**RESUMEN_FASE1_PROMPTS_1-2-3.md**](RESUMEN_FASE1_PROMPTS_1-2-3.md) - Resumen de Fase 1

#### Implementación y Prompts
- [**IMPLEMENTACION_PROMPTS_PASIVOS.md**](IMPLEMENTACION_PROMPTS_PASIVOS.md) - Implementación de prompts pasivos
- [**prompts_pasivos_avanzados_GRUPO_GAD.md**](prompts_pasivos_avanzados_GRUPO_GAD.md) - Prompts pasivos avanzados

---

## 📋 Scripts Útiles

### Desarrollo
```bash
# Iniciar el servidor de desarrollo
uvicorn src.api.main:app --reload

# Aplicar migraciones de base de datos
alembic upgrade head

# Generar nueva migración
alembic revision --autogenerate -m "descripcion"
```

### Testing y Calidad
```bash
# Ejecutar tests con cobertura
pytest --cov=src --cov-report=html

# Linting con ruff
ruff check src/

# Auditoría de seguridad
pip-audit
```

### Docker
```bash
# Levantar entorno de desarrollo
docker-compose up -d --build

# Levantar entorno de producción
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose logs -f
```

---

## 🔧 Configuración

### Variables de Entorno
Ver [`.env.example`](.env.example) para la configuración completa de variables de entorno necesarias.

### Dependencias
- **Python**: >=3.12
- **FastAPI**: >=0.115.0
- **SQLAlchemy**: >=2.0.25
- **PostgreSQL**: 13+
- **Redis**: 5.0+ (opcional, para WebSockets distribuidos)

---

## 📈 Estado del Proyecto

### Cobertura de Tests
Objetivo: **>85%** | Actual: Ver `coverage_report.txt`

### Badges
<!-- Agregar badges de CI/CD, cobertura, calidad de código -->

---

## 🆘 Soporte

### Contacto
- **Email**: dev@grupogad.com
- **Issues**: GitHub Issues

### Recursos Adicionales
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 📜 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

---

**Última actualización**: 2024
**Mantenido por**: Equipo GAD
