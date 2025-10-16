# ========================================================================
# 📊 GRUPO_GAD - Monitoring Setup Guide
# ========================================================================

## 🎯 Objetivo

Este documento describe cómo configurar y usar el stack de monitoring completo (Prometheus + Grafana + AlertManager) para GRUPO_GAD.

---

## 🚀 Quick Start

### 1. Iniciar Monitoring Stack

```bash
# Desde el root del proyecto
cd /opt/grupogad

# Iniciar monitoring (requiere que API esté running)
docker compose -f docker-compose.monitoring.yml up -d

# Verificar servicios
docker compose -f docker-compose.monitoring.yml ps

# Expected output:
# grupo_gad_prometheus      running (healthy)
# grupo_gad_grafana          running (healthy)
# grupo_gad_alertmanager    running (healthy)
# grupo_gad_node_exporter   running
# grupo_gad_postgres_exporter running
# grupo_gad_redis_exporter  running
```

### 2. Acceder a las UIs

| Servicio | URL | Credenciales | Propósito |
|----------|-----|--------------|-----------|
| **Grafana** | http://localhost:3000 | admin / changeme* | Dashboards & visualización |
| **Prometheus** | http://localhost:9090 | - | Query metrics raw |
| **AlertManager** | http://localhost:9093 | - | Gestión de alertas |

*⚠️ Cambiar password en `.env`: `GRAFANA_ADMIN_PASSWORD=<secure-password>`

### 3. Validar Scraping

```bash
# Ver targets en Prometheus
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Expected output:
{
  "job": "api",
  "health": "up"
}
{
  "job": "postgres",
  "health": "up"
}
{
  "job": "redis",
  "health": "up"
}
# ...
```

---

## 📊 Dashboards

### Dashboard 1: API Overview

**Métricas clave**:
- **Request Rate**: `rate(http_requests_total[5m])`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[5m])`
- **Latency P50/P95/P99**: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))`
- **Active WebSocket Connections**: `websocket_connections_active`

**Panel queries** (agregar en Grafana):

```promql
# Request Rate por endpoint
sum(rate(http_requests_total[5m])) by (method, path)

# Error rate %
sum(rate(http_requests_total{status=~"5.."}[5m])) 
/ 
sum(rate(http_requests_total[5m])) * 100

# Latency percentiles
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # P50
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # P95
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # P99

# Top 5 slowest endpoints
topk(5, 
  histogram_quantile(0.95, 
    sum(rate(http_request_duration_seconds_bucket[5m])) by (le, path)
  )
)
```

### Dashboard 2: Database Health

```promql
# Active connections
pg_stat_activity_count

# Database size
pg_database_size_bytes / 1024 / 1024 / 1024  # GB

# Transaction rate
rate(pg_stat_database_xact_commit[5m])

# Cache hit ratio
rate(pg_stat_database_blks_hit[5m]) 
/ 
(rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))

# Slow queries (duration > 1s)
pg_stat_activity_max_tx_duration > 1
```

### Dashboard 3: Redis Performance

```promql
# Memory usage %
redis_memory_used_bytes / redis_memory_max_bytes * 100

# Commands per second
rate(redis_commands_processed_total[5m])

# Hit rate %
rate(redis_keyspace_hits_total[5m]) 
/ 
(rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100

# Keys evicted per second
rate(redis_evicted_keys_total[5m])

# Connected clients
redis_connected_clients
```

### Dashboard 4: Infrastructure

```promql
# CPU usage %
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage %
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage %
(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100

# Network IO
rate(node_network_receive_bytes_total[5m])  # RX
rate(node_network_transmit_bytes_total[5m])  # TX
```

---

## 🚨 Alertas

### Configurar Notificaciones

#### Email (SMTP)

Editar `monitoring/alertmanager/alertmanager.yml`:

```yaml
global:
  smtp_from: 'alerts@grupogad.gob.ec'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'alerts@grupogad.gob.ec'
  smtp_auth_password: '<APP_PASSWORD>'  # Gmail: usar App Password
  smtp_require_tls: true
```

#### Slack

1. Crear Webhook en Slack: https://api.slack.com/messaging/webhooks
2. Actualizar `alertmanager.yml`:

```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX'
    channel: '#alerts-grupogad'
```

#### Telegram (Opcional)

Usar Alertmanager Bot: https://github.com/metalmatze/alertmanager-bot

### Validar Alertas

```bash
# Ver alertas activas
curl http://localhost:9093/api/v2/alerts | jq '.[] | {name: .labels.alertname, status: .status.state}'

# Simular alerta (parar API)
docker compose -f docker-compose.prod.yml stop api

# Esperar 1 minuto → Ver alerta "APIDown" en AlertManager
# http://localhost:9093

# Restaurar
docker compose -f docker-compose.prod.yml start api
```

---

## 🔧 Maintenance

### Ajustar Retention

**Prometheus** (por defecto 30 días):

```yaml
# docker-compose.monitoring.yml
command:
  - '--storage.tsdb.retention.time=90d'  # Cambiar a 90 días
```

**Grafana** (auto-cleanup):

```bash
# Limpiar dashboards snapshot antiguos (manual)
docker exec grupo_gad_grafana sqlite3 /var/lib/grafana/grafana.db \
  "DELETE FROM dashboard_snapshot WHERE created < datetime('now', '-30 days');"
```

### Backup de Configuración

```bash
# Backup Prometheus config
cp -r monitoring/prometheus /backups/prometheus_$(date +%Y%m%d)

# Backup Grafana dashboards
docker exec grupo_gad_grafana tar czf /tmp/grafana-dashboards.tar.gz /var/lib/grafana/dashboards
docker cp grupo_gad_grafana:/tmp/grafana-dashboards.tar.gz /backups/

# Backup AlertManager config
cp monitoring/alertmanager/alertmanager.yml /backups/alertmanager_$(date +%Y%m%d).yml
```

### Upgrade

```bash
# Pull nuevas versiones
docker compose -f docker-compose.monitoring.yml pull

# Restart con zero-downtime
docker compose -f docker-compose.monitoring.yml up -d --remove-orphans
```

---

## 📝 Custom Metrics

### Agregar Métricas en FastAPI

```python
from prometheus_client import Counter, Histogram, Gauge

# Counter: Incrementa monotónicamente
custom_events = Counter(
    'custom_events_total',
    'Total de eventos custom',
    ['event_type']
)

# Uso
custom_events.labels(event_type='user_login').inc()

# Histogram: Distribución de valores
task_duration = Histogram(
    'task_duration_seconds',
    'Duración de tareas en segundos',
    ['task_type']
)

# Uso
with task_duration.labels(task_type='report_generation').time():
    generate_report()

# Gauge: Valor que sube/baja
active_tasks = Gauge(
    'active_tasks',
    'Número de tareas activas'
)

# Uso
active_tasks.set(10)
active_tasks.inc()  # +1
active_tasks.dec()  # -1
```

### Query en Prometheus

```promql
# Rate de eventos custom
rate(custom_events_total[5m])

# Duración P95 de tareas
histogram_quantile(0.95, 
  sum(rate(task_duration_seconds_bucket[5m])) by (le, task_type)
)

# Tareas activas
active_tasks
```

---

## 🐛 Troubleshooting

### Prometheus no scrape targets

**Síntoma**: Targets en estado `DOWN` en http://localhost:9090/targets

**Solución**:

```bash
# Verificar que servicios están en la misma red
docker network inspect monitoring
docker network inspect gad-network

# Verificar que API expone /metrics
curl http://localhost:8000/metrics

# Ver logs de Prometheus
docker logs grupo_gad_prometheus | grep -i error

# Test manual de scraping
docker exec grupo_gad_prometheus wget -qO- http://api:8000/metrics
```

### Grafana no muestra datos

**Síntoma**: Dashboards vacíos o "No data"

**Solución**:

```bash
# Verificar datasource
curl http://localhost:3000/api/datasources

# Test query manual
curl -X POST http://localhost:3000/api/ds/query \
  -H "Content-Type: application/json" \
  -u admin:changeme \
  -d '{
    "queries": [
      {
        "expr": "up",
        "datasource": {"type": "prometheus", "uid": "prometheus"}
      }
    ]
  }'

# Verificar Prometheus desde Grafana
docker exec grupo_gad_grafana wget -qO- http://prometheus:9090/api/v1/query?query=up
```

### AlertManager no envía emails

**Síntoma**: Alertas activas pero no llegan emails

**Solución**:

```bash
# Ver logs de AlertManager
docker logs grupo_gad_alertmanager | grep -i error

# Test manual SMTP
docker exec grupo_gad_alertmanager sh -c "
  echo 'Test email' | 
  sendmail -v -f alerts@grupogad.gob.ec devops@grupogad.gob.ec
"

# Verificar configuración
docker exec grupo_gad_alertmanager cat /etc/alertmanager/alertmanager.yml

# Forzar reload configuración
curl -X POST http://localhost:9093/-/reload
```

---

## 📚 Referencias

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)

---

**Last Updated**: 2025-10-16  
**Version**: 1.0.0
