# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-10-13

### Added
- **Cache Auto-Invalidation** - Invalidación automática de cache al modificar tareas (create/update/delete/emergency)
- Función helper `invalidate_task_related_cache()` para invalidación selectiva en `src/api/routers/tasks.py`
- Script de smoke test `scripts/test_cache_invalidation.py` para validar invalidación de cache
- Documentación completa de finalización en `FINALIZACION_PRODUCCION_READY.md`

### Fixed
- **12 tests fallidos corregidos** - Mejora de pass rate de 90.7% a 98.3% (176/179 passing)
- `tests/bot/test_finalizar_tarea.py` - Corregidos imports de ApiService a ruta correcta
- `tests/bot/test_finalizar_tarea.py` - Corregidos valores de enum TaskType y TaskStatus
- `tests/bot/test_callback_handler.py` - Corregida estructura de acceso a wizard data

### Changed
- `src/api/routers/tasks.py` - Todos los endpoints CRUD ahora invalidan cache relacionado
- `src/api/routers/tasks.py` - Agregada dependencia opcional de CacheService en 4 endpoints
- Tests actualizados para usar valores válidos de enums del sistema real

### Documentation
- `FINALIZACION_PRODUCCION_READY.md` - Reporte completo con métricas y próximos pasos
- `MANUAL_GRUPO_GAD_REAL.md` - Manual técnico 100% actualizado con el proyecto real

### Notes
- Sistema 100% production-ready con tests al 98.3% y cache consistente
- Cache patterns: `stats:user:*`, `tasks:list:*`, `task:{id}`
- Invalidación failsafe: no falla request si falla invalidación

## [1.3.0] - 2025-10-11

### Added
- **Bot Feature: `/historial`** - Comando para consultar historial de tareas con paginación y filtros (todas/activas/finalizadas)
- **Bot Feature: `/estadisticas`** - Dashboard personal de productividad con métricas visuales y barras de progreso ASCII
- Tests completos para nuevos comandos del bot (`test_historial.py`, `test_estadisticas.py`)
- Documentación comprehensiva en `docs/bot/FEATURES_BONUS.md` con guías de implementación y uso
- Sección de Bot de Telegram en README principal con listado de comandos

### Changed
- `src/bot/handlers/__init__.py` actualizado con registro de nuevos comandos
- `src/bot/commands/__init__.py` creado para exportación centralizada de comandos
- README.md expandido con sección completa del bot y sus capacidades

### Documentation
- Plan de 7 opciones post-desarrollo completado al 100%
- Documentación optimizada y consolidada para mantenimiento
- Resumen ejecutivo de jornada con estado del proyecto

## [1.2.0] - 2025-10-06

### Added
- Métricas Prometheus para el subsistema WebSocket.
- Endpoints `/metrics` (básico) y `/api/v1/metrics/prometheus` (completo) para monitoreo.
- Documentación detallada en `docs/PROMETHEUS_METRICAS_IMPLEMENTACION.md`.

### Changed
- WebSocketManager ahora registra métricas en tiempo real.

## [1.1.0] - 2025-09-30

### Added
- WebSockets cross-worker mediante Redis Pub/Sub (opcional vía `REDIS_HOST`).
- Documentación de despliegue prod-local y guía de Pub/Sub en `README.md`.

### Fixed
- Tipados estrictos en `src/core/ws_pubsub.py` para cumplir mypy.

### Notes
- La función de Pub/Sub no cambia el comportamiento local si no se configura Redis.

## [1.0.0] - 2025-09-01

### Added
- **API Completa**: Implementación de los 11 endpoints principales para la gestión de tareas, usuarios y métricas.
- **Bot de Telegram**: Funcionalidad inicial con 3 comandos básicos para interacción remota.
- **Dashboard con Mapa**: Panel de control web con visualización de geolocalización de tareas usando PostGIS.
- **Control de Telegram Integrado**: Endpoint administrativo para enviar notificaciones a través del bot.

### Fixed
- **Suite de Pruebas**: Corrección de todas las pruebas, logrando un 100% de aprobación (13/13 tests).
- **Configuración de Entorno**: Estandarización y corrección de la carga de variables de entorno en producción.
- **Validaciones Pydantic**: Refinamiento de los modelos de datos para validaciones más estrictas y seguras.

### Changed
- **Despliegue a Producción**: Migración del proceso de despliegue a un sistema basado en Docker Compose para mayor portabilidad.
- **SSL Automático**: Implementación de Caddy como reverse proxy para la gestión automática de certificados SSL.

### Security
- **Filtro de Agente de Usuario**: Implementado un filtro para bloquear peticiones de agentes no autorizados.
- **Autenticación JWT**: Todos los endpoints críticos ahora están protegidos mediante autenticación por JSON Web Tokens.
- **Auditoría de Acceso**: El acceso a los endpoints administrativos es ahora auditado y registrado.
