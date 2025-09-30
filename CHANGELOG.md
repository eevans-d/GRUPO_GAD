# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
