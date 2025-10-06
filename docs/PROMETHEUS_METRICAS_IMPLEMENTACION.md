# 🔥 Métricas Prometheus para WebSockets

Este documento describe la implementación de métricas Prometheus para el subsistema WebSocket en GRUPO_GAD.

## Resumen

Se han implementado métricas Prometheus para monitorear el rendimiento y estado del sistema de WebSockets, siguiendo el diseño especificado en `docs/PROMETHEUS_METRICAS_DISENO.md`.

## Métricas Implementadas

### Métricas Básicas (Fase 1)

| Nombre | Tipo | Labels | Descripción |
|--------|------|--------|-------------|
| `ggrt_active_connections` | Gauge | `env` | Conexiones WebSocket activas en el proceso. |
| `ggrt_connections_total` | Counter | `env` | Total histórico de conexiones aceptadas. |
| `ggrt_messages_sent_total` | Counter | `env` | Mensajes enviados (unicast + broadcast). |
| `ggrt_broadcasts_total` | Counter | `env` | Eventos broadcast realizados. |
| `ggrt_send_errors_total` | Counter | `env` | Errores al enviar mensajes. |
| `ggrt_heartbeat_last_timestamp` | Gauge | `env` | Timestamp (epoch) del último ciclo heartbeat. |

### Métricas Opcionales (Fase 2)

| Nombre | Tipo | Labels | Descripción |
|--------|------|--------|-------------|
| `ggrt_role_connections` | Gauge | `env`, `role` | Conexiones activas por rol. |
| `ggrt_user_active` | Gauge | `env` | Usuarios únicos con ≥1 conexión. |
| `ggrt_message_latency_seconds` | Histogram | `env` | Latencia de mensajes (PING/PONG). |

## Acceso a las Métricas

Las métricas están disponibles en:

1. **Métricas Básicas (legacy)**: `/metrics` - Formato de texto simple compatible con sistemas anteriores.
2. **Métricas Prometheus Completas**: `/api/v1/metrics/prometheus` - Formato estándar Prometheus con todas las métricas.

## Configuración de Prometheus (ejemplo)

```yaml
scrape_configs:
  - job_name: 'grupogad_api'
    metrics_path: '/api/v1/metrics/prometheus'
    scrape_interval: 15s
    static_configs:
      - targets: ['api:8000']
```

## Alertas Recomendadas

Se recomienda configurar alertas para:

- **Alta tasa de errores**: `rate(ggrt_send_errors_total[5m]) > 0.1`
- **Caída de conexiones**: `delta(ggrt_active_connections[5m]) < -10`
- **Heartbeat no actualizado**: `time() - ggrt_heartbeat_last_timestamp > 120`

## Próximos Pasos

- Implementar paneles Grafana para visualizar estas métricas
- Configurar alertas basadas en umbrales específicos
- Extender métricas a otros subsistemas (API, Database, Redis)