# Checklist Pre-Deploy (Subsistema WebSockets / Tiempo Real)

Esta lista se revisa antes de desplegar a producción tras levantar modo "Barco Anclado".

## Configuración
- [ ] Variables ENV críticas definidas (`ENVIRONMENT=production`, claves JWT, secrets externos).
- [ ] Revisión de CORS y proxies de confianza (no comodines en producción).
- [ ] Revisar versión de dependencias de seguridad (jwt, fastapi, websockets, loguru) sin CVEs pendientes.

## Base de Código
- [ ] Sin TODOs críticos abiertos en `websockets.py`.
- [ ] Sin prints o logs de debug accidentales (solo logger estructurado).
- [ ] Revisión de que `websocket_manager` no acumula referencias (lint / inspección). 

## Migraciones / DB
- [ ] Migraciones Alembic aplicadas (`alembic upgrade head`).
- [ ] Ningún script de migración pendiente rota en pruebas locales.

## Pruebas
- [ ] Suite completa `pytest` verde (incluyendo tests de websockets y métricas) con skips esperados documentados.
- [ ] Cobertura mínima aceptable (definir umbral, recomendado ≥ 65% backend global; módulo websockets ≥ líneas usadas en rutas críticas).
- [ ] Tests de token policy confirman gating en producción.

## Observabilidad
- [ ] Logs sin datos sensibles (ver sample en staging).
- [ ] Endpoint de stats `/ws/stats` responde con estructura prevista.
- [ ] (Cuando se implemente) Endpoint `/metrics` expone métricas base sin cardinalidad excesiva.

## Rendimiento / Estabilidad
- [ ] Heartbeat interval validado (30s actual) → ajustar solo si produce carga innecesaria.
- [ ] No se detectan fugas de memoria en pruebas de conexión repetida (stress local opcional).

## Seguridad
- [ ] Token JWT requerido en producción para handshake WebSocket (test correspondiente pasa y no está skippeado en prod).
- [ ] Secrets no impresos en logs.
- [ ] Dependencias auditadas (pip-audit / safety) sin findings críticos.

## Documentación
- [ ] `WEBSOCKET_SYSTEM_STATUS.md` actualizado con rutas y métricas vigentes.
- [ ] `PROMETHEUS_METRICAS_DISENO.md` alineado con implementación (o actualizado si hubo cambios).
- [ ] Changelog registra cualquier adición de métricas/endpoint.

## Operacional
- [ ] Estrategia de rollback definida (última imagen estable etiquetada).
- [ ] Monitoreo configurado para alertar si `active_connections` cae a 0 inesperadamente durante horario laboral.

## Aprobaciones
- [ ] Revisión de seguridad.
- [ ] Revisión técnica (peer review último diff relevante).
- [ ] Aprobación de producto (si aplica a funcionalidades dependientes del canal tiempo real).

Estado actual: DOCUMENTO BASE añadido en congelamiento (sin implementación adicional).
