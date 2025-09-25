# Diseño Propuesto de Métricas (Prometheus) para Subsistema WebSocket

Objetivo: Documentar el diseño antes de implementar (cumple modo "Barco Anclado" al no introducir código todavía).

## Principios

1. Baja cardinalidad: Evitar labels con valores altamente variables (IDs directos de usuarios, UUIDs de conexión).
2. Métricas enfocadas en salud y desempeño, no en auditoría detallada.
3. Evitar duplicar información ya presente en logs estructurados.
4. Preparar nombres compatibles con convención Prometheus: `snake_case`, prefijo de dominio sugerido `ggrt_` (GRUPO GAD Real Time).

## Métricas Básicas

| Nombre | Tipo | Labels | Descripción |
|--------|------|--------|-------------|
| `ggrt_active_connections` | Gauge | `env` | Conexiones WebSocket activas en el proceso. |
| `ggrt_connections_total` | Counter | `env` | Total histórico de conexiones aceptadas. |
| `ggrt_messages_sent_total` | Counter | `env` | Mensajes enviados (unicast + broadcast). |
| `ggrt_broadcasts_total` | Counter | `env` | Eventos broadcast realizados. |
| `ggrt_send_errors_total` | Counter | `env` | Errores al enviar mensajes. |
| `ggrt_heartbeat_last_timestamp` | Gauge | `env` | Timestamp (epoch) del último ciclo heartbeat completado. |

## Métricas Opcionales (Fase 2)

| Nombre | Tipo | Labels | Nota |
|--------|------|--------|------|
| `ggrt_role_connections` | Gauge | `env`, `role` | Cardinalidad controlada si el número de roles es finito y pequeño. |
| `ggrt_user_active` | Gauge | `env` | Cantidad de usuarios únicos con ≥1 conexión (no por usuario). |
| `ggrt_message_latency_seconds` | Histogram | `env` | Solo si se mide round-trip PING/PONG en el futuro. |

## No Incluir (Justificación)

- IDs de conexión como label: cardinalidad explosiva.
- user_id como label: potencial de fuga de información y cardinalidad alta.
- Niveles de severidad de notificaciones: ya se reflejan en logs (no crítico en métricas).

## Exposición Planeada

1. Usar `prometheus_client` (cuando se levante el modo anclado) e integrar un endpoint `/metrics` consolidado (si no existe ya en API principal).
2. Actualización periódica (pull) desde `websocket_manager.get_stats()` para gauges; counters se incrementan in-situ al enviar mensajes.
3. Asegurar que el heartbeat no se convierte en fuente de cardinalidad (una sola métrica timestamp).

## Estrategia de Implementación (Post-Anclaje)

1. Crear módulo `src/observability/metrics.py` centralizado.
2. Registrar métricas en import único (idempotente).
3. Añadir hook ligero en `WebSocketManager` para incrementar counters existentes (sin reestructurar lógica).
4. Testing: validar que los counters crecen en broadcast/unicast y que gauges reflejan alta/baja de conexiones mediante fixtures.

## Riesgos y Mitigaciones

- Riesgo: Bloqueo GIL en picos de exportación → Métricas simples; no se serializan datos grandes.
- Riesgo: Colisión de nombres → Prefijo `ggrt_` y documentación previa aquí.
- Riesgo: Fuga de datos sensibles → No se etiquetan usuarios / conexiones.

## Estado

Documentado. Pendiente ejecución tras levantar congelamiento.
