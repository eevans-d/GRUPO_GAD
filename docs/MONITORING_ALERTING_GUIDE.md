# Configuración de Alertas para GRUPO_GAD

Este documento describe la configuración de alertas y monitoreo para el sistema GRUPO_GAD en producción. Forma parte de la Fase 6 del roadmap: Post-Producción (Mantenimiento y Fine-Tuning).

## Arquitectura de Monitoreo

El sistema de monitoreo se compone de:

1. **Prometheus** - Recolección de métricas
2. **Grafana** - Visualización de dashboards
3. **Alertmanager** - Gestión y distribución de alertas
4. **Node Exporter** - Métricas del sistema operativo
5. **Redis Exporter** - Métricas de Redis
6. **Postgres Exporter** - Métricas de PostgreSQL

## Métricas Críticas

### 1. Métricas de Aplicación

| Métrica | Descripción | Umbral de Alerta |
|---------|-------------|------------------|
| `http_requests_total` | Total de peticiones HTTP | Rate > 1000 req/min |
| `http_request_duration_seconds` | Latencia de peticiones | P95 > 2s |
| `http_requests_errors_total` | Errores HTTP (4xx, 5xx) | Rate > 50 errors/min |
| `websocket_connections_total` | Conexiones WebSocket activas | > 500 conexiones |
| `websocket_messages_sent_total` | Mensajes WebSocket enviados | Rate > 10000 msg/min |
| `database_connections_active` | Conexiones activas a BD | > 80% del pool |
| `redis_connected_clients` | Clientes conectados a Redis | > 100 clientes |

### 2. Métricas de Infraestructura

| Métrica | Descripción | Umbral de Alerta |
|---------|-------------|------------------|
| `up` | Estado del servicio | 0 (servicio caído) |
| `node_cpu_seconds_total` | Uso de CPU | > 85% durante 5min |
| `node_memory_MemAvailable_bytes` | Memoria disponible | < 10% disponible |
| `node_filesystem_avail_bytes` | Espacio en disco | < 10% disponible |
| `node_load15` | Load average 15min | > 2.0 |

### 3. Métricas de Base de Datos

| Métrica | Descripción | Umbral de Alerta |
|---------|-------------|------------------|
| `pg_up` | Estado de PostgreSQL | 0 (BD caída) |
| `pg_stat_database_numbackends` | Conexiones activas | > 50 conexiones |
| `pg_stat_database_tup_inserted` | Rate de inserciones | Cambio > 1000% |
| `pg_database_size_bytes` | Tamaño de BD | > 80% del espacio asignado |
| `pg_stat_bgwriter_checkpoints_timed` | Checkpoints programados | Rate < 1/min |

## Configuración de Alertas

### Alertas Críticas (P0)

```yaml
groups:
- name: critical_alerts
  rules:
  - alert: ServiceDown
    expr: up == 0
    for: 30s
    labels:
      severity: critical
      priority: P0
    annotations:
      summary: "Servicio {{ $labels.instance }} está caído"
      description: "El servicio {{ $labels.job }} en {{ $labels.instance }} no responde."

  - alert: HighErrorRate
    expr: rate(http_requests_errors_total[5m]) > 50
    for: 2m
    labels:
      severity: critical
      priority: P0
    annotations:
      summary: "Tasa de errores alta en API"
      description: "La API está generando {{ $value }} errores por minuto."

  - alert: DatabaseDown
    expr: pg_up == 0
    for: 30s
    labels:
      severity: critical
      priority: P0
    annotations:
      summary: "Base de datos PostgreSQL caída"
      description: "PostgreSQL no está respondiendo en {{ $labels.instance }}."

  - alert: DiskSpaceCritical
    expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 5
    for: 1m
    labels:
      severity: critical
      priority: P0
    annotations:
      summary: "Espacio en disco críticamente bajo"
      description: "El disco {{ $labels.mountpoint }} tiene menos del 5% de espacio libre."
```

### Alertas de Advertencia (P1)

```yaml
- name: warning_alerts
  rules:
  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
    for: 5m
    labels:
      severity: warning
      priority: P1
    annotations:
      summary: "Uso alto de CPU"
      description: "CPU al {{ $value }}% en {{ $labels.instance }} durante 5 minutos."

  - alert: HighMemoryUsage
    expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
    for: 3m
    labels:
      severity: warning
      priority: P1
    annotations:
      summary: "Uso alto de memoria"
      description: "Memoria al {{ $value }}% en {{ $labels.instance }}."

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
    for: 3m
    labels:
      severity: warning
      priority: P1
    annotations:
      summary: "Tiempo de respuesta alto"
      description: "P95 de tiempo de respuesta: {{ $value }}s."

  - alert: TooManyDatabaseConnections
    expr: pg_stat_database_numbackends > 50
    for: 2m
    labels:
      severity: warning
      priority: P1
    annotations:
      summary: "Muchas conexiones a la base de datos"
      description: "{{ $value }} conexiones activas a PostgreSQL."
```

## Canales de Notificación

### 1. Configuración de Alertmanager

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@grupogad.com'
  smtp_auth_username: 'alerts@grupogad.com'
  smtp_auth_password: 'your_app_password'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      priority: P0
    receiver: critical-alerts
  - match:
      priority: P1
    receiver: warning-alerts

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'

- name: 'critical-alerts'
  email_configs:
  - to: 'admin@grupogad.com'
    subject: '[CRÍTICO] {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alerta: {{ .Annotations.summary }}
      Descripción: {{ .Annotations.description }}
      Severidad: {{ .Labels.severity }}
      Instancia: {{ .Labels.instance }}
      Tiempo: {{ .StartsAt }}
      {{ end }}
  telegram_configs:
  - api_url: 'https://api.telegram.org'
    bot_token: 'YOUR_TELEGRAM_BOT_TOKEN'
    chat_id: -1001234567890
    message: |
      🚨 *ALERTA CRÍTICA*
      {{ range .Alerts }}
      *{{ .Annotations.summary }}*
      {{ .Annotations.description }}
      Severidad: {{ .Labels.severity }}
      {{ end }}

- name: 'warning-alerts'
  email_configs:
  - to: 'devops@grupogad.com'
    subject: '[ADVERTENCIA] {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alerta: {{ .Annotations.summary }}
      Descripción: {{ .Annotations.description }}
      Severidad: {{ .Labels.severity }}
      {{ end }}
```

### 2. Integración con Telegram

Para recibir alertas en Telegram:

1. Crear un bot con @BotFather
2. Obtener el token del bot
3. Crear un grupo/canal para alertas
4. Añadir el bot al grupo y obtener el chat_id
5. Configurar en Alertmanager

### 3. Integración con Slack (Opcional)

```yaml
- name: 'slack-alerts'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: 'Alerta GRUPO_GAD'
    text: |
      {{ range .Alerts }}
      {{ .Annotations.summary }}
      {{ .Annotations.description }}
      {{ end }}
```

## Dashboards de Grafana

### 1. Dashboard Principal - Overview

Métricas incluidas:
- Estado general de servicios
- Tráfico HTTP (requests/min, errores, latencia)
- Uso de recursos (CPU, memoria, disco)
- Conexiones WebSocket activas
- Estado de la base de datos

### 2. Dashboard de Infraestructura

Métricas incluidas:
- Métricas detalladas del sistema operativo
- Uso de red
- I/O de disco
- Procesos en ejecución
- Load average histórico

### 3. Dashboard de Aplicación

Métricas incluidas:
- Métricas específicas de GRUPO_GAD
- Performance de endpoints
- Patrones de uso
- Métricas de negocio

## Plan de Escalado de Alertas

### Nivel 1 - Alerta Inicial
- Notificación automática via Telegram/Email
- Registro en sistema de tickets
- Timeout: 5 minutos

### Nivel 2 - Escalado
- Si no hay resolución en 15 minutos
- Notificación al equipo de guardia
- Llamada telefónica automática

### Nivel 3 - Escalado Crítico
- Si no hay resolución en 30 minutos
- Notificación a management
- Activación de procedimientos de emergencia

## Métricas de SLA

### Objetivos de Nivel de Servicio

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Disponibilidad | 99.9% | Uptime mensual |
| Tiempo de respuesta | P95 < 1s | Para endpoints principales |
| Tiempo de resolución | < 15 min | Para alertas P0 |
| Tiempo de recuperación | < 5 min | Tras caída de servicio |

### Cálculo de SLA

```promql
# Disponibilidad (%)
(1 - (sum(rate(up == 0[30d])) / sum(rate(up[30d])))) * 100

# Latencia P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[30d]))

# Tasa de errores
rate(http_requests_errors_total[30d]) / rate(http_requests_total[30d]) * 100
```

## Mantenimiento del Sistema de Monitoreo

### Tareas Regulares

1. **Diario:**
   - Revisar dashboards principales
   - Verificar que no hay alertas pendientes
   - Comprobar espacio en disco de métricas

2. **Semanal:**
   - Revisar tendencias de métricas
   - Ajustar umbrales si es necesario
   - Verificar backups de configuración

3. **Mensual:**
   - Revisar SLA y generar reportes
   - Optimizar consultas lentas
   - Actualizar documentación de runbooks

### Retención de Datos

- **Métricas alta frecuencia:** 7 días
- **Métricas media frecuencia:** 30 días
- **Métricas baja frecuencia:** 90 días
- **Alertas históricas:** 180 días

---

## Referencias

- [Prometheus Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [SLO/SLA Best Practices](https://cloud.google.com/blog/products/management-tools/sre-fundamentals-slis-slas-and-slos)