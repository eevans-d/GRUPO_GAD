# ========================================================================
# 📚 GRUPO_GAD - Production Operations Runbook
# ========================================================================
# Última actualización: 2025-10-16
# Versión: 1.0.0
# Owner: DevOps Team
# ========================================================================

## 🎯 Objetivo

Este runbook documenta los procedimientos operacionales estándar (SOP) para el sistema GRUPO_GAD en producción, incluyendo deployment, monitoreo, troubleshooting y recuperación ante desastres.

---

## 📋 Tabla de Contenidos

1. [Arquitectura de Producción](#arquitectura-de-producción)
2. [Deployment](#deployment)
3. [Monitoreo](#monitoreo)
4. [Procedimientos de Emergencia](#procedimientos-de-emergencia)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance](#maintenance)
7. [Escalation](#escalation)

---

## 🏗️ Arquitectura de Producción

### Stack Tecnológico

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │  Caddy (Reverse      │
         │  Proxy + HTTPS)      │
         │  Port: 80/443        │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  FastAPI Application │
         │  (uvicorn)           │
         │  Port: 8000          │
         └──────────┬───────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│  PostgreSQL 15   │  │  Redis 7         │
│  + PostGIS       │  │  (Cache/WS)      │
│  Port: 5432      │  │  Port: 6379      │
└──────────────────┘  └──────────────────┘
```

### Servicios Docker

| Servicio | Container Name | Image | Ports | Health Check |
|----------|----------------|-------|-------|--------------|
| API | grupo_gad_api | ghcr.io/eevans-d/grupo_gad/api:v1.0.0 | 8000 | `/api/v1/health` |
| DB | grupo_gad_db | postgis/postgis:15-3.3 | 5432 | `pg_isready` |
| Redis | grupo_gad_redis | redis:7-alpine | 6379 | `redis-cli ping` |
| Caddy | grupo_gad_caddy | caddy:2.8 | 80, 443 | - |
| Bot | grupo_gad_bot | ghcr.io/eevans-d/grupo_gad/bot:v1.0.0 | - | - |

### Variables de Entorno Críticas

**⚠️ CRÍTICO**: Validar antes de cada deployment

```bash
# Security
SECRET_KEY=<64-char-hex>         # HS256 JWT signing
POSTGRES_PASSWORD=<strong-pwd>    # DB credentials
REDIS_PASSWORD=<strong-pwd>       # Redis credentials

# Environment
ENVIRONMENT=production

# URLs
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
```

---

## 🚀 Deployment

### Pre-Deployment Checklist

```bash
# 1. Verificar que estás en master
git branch --show-current
# Esperado: master

# 2. Pull últimos cambios
git pull origin master

# 3. Verificar tests pasan
make test

# 4. Verificar security scan
safety check --file requirements.txt

# 5. Verificar .env.production está configurado
grep -q "CAMBIAR_POR" .env.production && echo "❌ STOP: Configurar .env.production" || echo "✅ OK"

# 6. Verificar backups recientes
ls -lh backups/*.sql.gz | tail -5
```

### Deployment Normal (Zero-Downtime)

```bash
# Deployment con backup automático
./scripts/deploy_production.sh

# Deployment sin backup (solo en emergencias)
./scripts/deploy_production.sh --skip-backup

# Deployment forzado (sin confirmación)
./scripts/deploy_production.sh --force
```

**Tiempo estimado**: 3-5 minutos

**Pasos automáticos**:
1. ✅ Verificar prerequisitos
2. 💾 Backup de base de datos
3. 📦 Pull imágenes Docker
4. 🗄️ Ejecutar migraciones Alembic
5. 🚀 Deploy servicios (zero-downtime)
6. 🧪 Smoke tests (health, metrics, WS)
7. 🧹 Cleanup imágenes antiguas

### Post-Deployment Verification

```bash
# 1. Verificar servicios running
docker compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                 STATUS                   HEALTH
# grupo_gad_api        Up 2 minutes (healthy)
# grupo_gad_db         Up 3 minutes (healthy)
# grupo_gad_redis      Up 3 minutes (healthy)
# grupo_gad_caddy      Up 2 minutes
# grupo_gad_bot        Up 2 minutes

# 2. Verificar health endpoint
curl -f http://localhost:8000/api/v1/health
# Esperado: {"status":"healthy", "environment":"production"}

# 3. Verificar metrics
curl http://localhost:8000/metrics | grep http_requests_total

# 4. Verificar logs (sin errores críticos)
docker compose -f docker-compose.prod.yml logs --tail=50 api | grep -i error

# 5. Verificar WebSocket (opcional)
python3 scripts/ws_smoke_test.py
```

### Rollback

**Cuando usar rollback**:
- Health checks fallan después de deployment
- Errores críticos en logs
- Performance degradation severa
- Bug crítico descubierto en producción

```bash
# Rollback automático con último backup
./scripts/rollback_production.sh

# Rollback con backup específico
./scripts/rollback_production.sh --backup-file backups/pre_deploy_20251016_143022.sql.gz
```

**Tiempo estimado**: 2-3 minutos

**⚠️ IMPORTANTE**: El rollback incluye:
1. 🛑 Stop servicios (API, bot, Caddy)
2. 💾 Restaurar DB desde backup
3. 🔄 Git checkout commit anterior
4. 🚀 Restart servicios
5. 🧪 Verificar health

---

## 📊 Monitoreo

### Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| API Health | http://localhost:8000/api/v1/health | Status básico |
| Metrics | http://localhost:8000/metrics | Prometheus metrics |
| Grafana | http://localhost:3000 | Visualización (si configurado) |

### Métricas Clave (KPIs)

**Golden Signals**:

1. **Latency** (Latencia)
   ```bash
   # P50, P95, P99
   curl http://localhost:8000/metrics | grep http_request_duration_seconds
   ```
   - ✅ P95 < 200ms
   - ⚠️ P95 200-500ms
   - 🚨 P95 > 500ms

2. **Traffic** (Tráfico)
   ```bash
   # Requests per second
   curl http://localhost:8000/metrics | grep http_requests_total
   ```
   - Baseline: ~10 RPS (normal operations)
   - Peak: ~50 RPS (emergency scenarios)

3. **Errors** (Errores)
   ```bash
   # Error rate
   curl http://localhost:8000/metrics | grep http_requests_total | grep '5xx'
   ```
   - ✅ Error rate < 1%
   - ⚠️ Error rate 1-5%
   - 🚨 Error rate > 5%

4. **Saturation** (Saturación)
   ```bash
   # Resource usage
   docker stats --no-stream grupo_gad_api grupo_gad_db grupo_gad_redis
   ```
   - ✅ CPU < 70%, Memory < 80%
   - ⚠️ CPU 70-90%, Memory 80-90%
   - 🚨 CPU > 90%, Memory > 90%

### WebSocket Monitoring

```bash
# Ver conexiones activas
curl http://localhost:8000/ws/stats

# Expected output:
{
  "active_connections": 10,
  "total_messages_sent": 1500,
  "total_broadcasts": 50,
  "last_broadcast_at": "2025-10-16T12:30:45Z"
}
```

### Database Monitoring

```bash
# Conexiones activas
docker exec grupo_gad_db psql -U grupogad_user -d grupogad_prod -c \
  "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Queries lentas (> 1 segundo)
docker exec grupo_gad_db psql -U grupogad_user -d grupogad_prod -c \
  "SELECT pid, query_start, state, query FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '1 second';"

# Tamaño de base de datos
docker exec grupo_gad_db psql -U grupogad_user -d grupogad_prod -c \
  "SELECT pg_size_pretty(pg_database_size('grupogad_prod'));"
```

### Logs

```bash
# Seguir logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f api

# Filtrar errores
docker compose -f docker-compose.prod.yml logs api | grep -i error

# Últimas 100 líneas
docker compose -f docker-compose.prod.yml logs --tail=100 api

# Logs estructurados (JSON)
docker compose -f docker-compose.prod.yml logs api | grep '"level":"error"'
```

---

## 🚨 Procedimientos de Emergencia

### 1. API Down (HTTP 503/504)

**Síntomas**:
- Health endpoint no responde
- Requests timeout
- HTTP 503 Service Unavailable

**Diagnóstico**:

```bash
# 1. Verificar si contenedor está running
docker compose -f docker-compose.prod.yml ps api

# 2. Ver logs recientes
docker compose -f docker-compose.prod.yml logs --tail=100 api

# 3. Verificar health
docker exec grupo_gad_api curl -f http://localhost:8000/api/v1/health
```

**Solución**:

```bash
# Opción A: Restart rápido
docker compose -f docker-compose.prod.yml restart api

# Esperar 10 segundos
sleep 10

# Verificar health
curl http://localhost:8000/api/v1/health

# Opción B: Rollback completo (si restart no funciona)
./scripts/rollback_production.sh
```

**ETA**: 1-3 minutos

---

### 2. Database Connection Issues

**Síntomas**:
- Logs: "could not connect to server"
- API devuelve HTTP 500
- Timeout en queries

**Diagnóstico**:

```bash
# 1. Verificar DB container
docker compose -f docker-compose.prod.yml ps db

# 2. Test conexión manual
docker exec grupo_gad_db pg_isready -U grupogad_user -d grupogad_prod

# 3. Ver conexiones activas
docker exec grupo_gad_db psql -U grupogad_user -d grupogad_prod -c \
  "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 4. Ver errores en logs
docker compose -f docker-compose.prod.yml logs --tail=50 db | grep ERROR
```

**Solución**:

```bash
# Opción A: Restart PostgreSQL
docker compose -f docker-compose.prod.yml restart db

# Esperar health check
sleep 15

# Opción B: Matar conexiones colgadas
docker exec grupo_gad_db psql -U grupogad_user -d grupogad_prod -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND now() - query_start > interval '5 minutes';"

# Opción C: Rollback completo
./scripts/rollback_production.sh
```

**ETA**: 2-5 minutos

---

### 3. High CPU/Memory Usage

**Síntomas**:
- Server lento
- Requests timeout
- OOMKiller mata contenedores

**Diagnóstico**:

```bash
# 1. Ver resource usage
docker stats --no-stream

# 2. Top procesos en API container
docker exec grupo_gad_api ps aux --sort=-%cpu | head -10

# 3. Memory usage
docker exec grupo_gad_api free -h

# 4. Queries lentas en DB
docker exec grupo_gad_db psql -U grupogad_user -d grupogad_prod -c \
  "SELECT pid, now() - query_start as duration, state, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 5;"
```

**Solución**:

```bash
# Opción A: Escalar API (si Docker Swarm/Kubernetes)
docker compose -f docker-compose.prod.yml up -d --scale api=3

# Opción B: Matar queries lentas
docker exec grupo_gad_db psql -U grupogad_user -d grupogad_prod -c \
  "SELECT pg_terminate_backend(<PID>);"

# Opción C: Restart servicios
docker compose -f docker-compose.prod.yml restart api

# Opción D: Limpiar Redis cache
docker exec grupo_gad_redis redis-cli FLUSHDB
```

**ETA**: 2-5 minutos

---

### 4. Disk Space Full

**Síntomas**:
- Logs: "No space left on device"
- Writes fallan
- Containers crashean

**Diagnóstico**:

```bash
# 1. Ver espacio disponible
df -h

# 2. Ver tamaño de logs
du -sh logs/
du -sh /var/lib/docker/containers/

# 3. Ver volúmenes Docker
docker system df -v
```

**Solución**:

```bash
# Opción A: Limpiar logs antiguos
find logs/ -name "*.log" -mtime +7 -delete

# Opción B: Limpiar Docker
docker system prune -af --volumes

# Opción C: Limpiar backups antiguos
find backups/ -name "*.sql.gz" -mtime +30 -delete

# Opción D: Rotar logs Caddy
docker exec grupo_gad_caddy sh -c "truncate -s 0 /var/log/caddy/*.log"
```

**ETA**: 5-10 minutos

---

### 5. Security Incident

**Síntomas**:
- Accesos no autorizados
- Datos sensibles expuestos
- Ataques DDoS

**Respuesta Inmediata**:

```bash
# 1. STOP servicios públicos
docker compose -f docker-compose.prod.yml stop caddy

# 2. Backup completo inmediato
./scripts/backup_production.sh

# 3. Analizar logs de acceso
grep -i "401\|403\|500" logs/*.log | tail -100

# 4. Ver IPs sospechosas
docker compose -f docker-compose.prod.yml logs caddy | grep -E "40[13]" | awk '{print $1}' | sort | uniq -c | sort -rn | head -20

# 5. Notificar al equipo de seguridad
# [Agregar contacto aquí]
```

**ETA**: Inmediato (< 1 minuto)

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: "Connection refused" al acceder a API

**Causa**: Caddy no puede conectar a API container

**Solución**:
```bash
# Verificar que API está en la misma red
docker network inspect grupo_gad_gad-network

# Verificar que API escucha en 0.0.0.0:8000
docker exec grupo_gad_api netstat -tlnp | grep 8000

# Test desde Caddy container
docker exec grupo_gad_caddy wget -qO- http://api:8000/api/v1/health
```

---

#### Issue: Alembic migrations fallan

**Causa**: Schema drift o migration conflicto

**Solución**:
```bash
# Ver estado actual
docker exec grupo_gad_api alembic current

# Ver historial
docker exec grupo_gad_api alembic history

# Forzar downgrade y upgrade
docker exec grupo_gad_api alembic downgrade -1
docker exec grupo_gad_api alembic upgrade head

# En caso extremo: stamp manual
docker exec grupo_gad_api alembic stamp head
```

---

#### Issue: WebSocket connections drop

**Causa**: Timeout o heartbeat failure

**Solución**:
```bash
# Ver configuración heartbeat
docker exec grupo_gad_api env | grep WS_

# Aumentar timeout (en .env.production)
# WS_HEARTBEAT_INTERVAL=60
# WS_CONNECTION_TIMEOUT=600

# Restart API
docker compose -f docker-compose.prod.yml restart api
```

---

## 🔧 Maintenance

### Daily Tasks

```bash
# Verificar health (automatizar con cron)
0 */6 * * * curl -f http://localhost:8000/api/v1/health || echo "API DOWN" | mail -s "ALERT" admin@grupogad.gob.ec
```

### Weekly Tasks

```bash
# Backup completo (automatizar)
0 2 * * 0 /opt/grupogad/scripts/backup_production.sh

# Limpiar logs antiguos
0 3 * * 0 find /opt/grupogad/logs/ -name "*.log" -mtime +30 -delete

# Analizar performance
0 4 * * 0 docker stats --no-stream > /opt/grupogad/reports/weekly_stats.txt
```

### Monthly Tasks

- [ ] Revisar security patches (Ubuntu, Docker, Python packages)
- [ ] Rotar credenciales (DB passwords, API keys)
- [ ] Auditoría de logs de acceso
- [ ] Revisar y actualizar este runbook
- [ ] Disaster recovery drill (test restore desde backup)

---

## 📞 Escalation

### Niveles de Severidad

| Nivel | Descripción | Response Time | Escalation |
|-------|-------------|---------------|------------|
| **P0** | Producción completamente down | < 15 min | Inmediato a CTO |
| **P1** | Funcionalidad crítica afectada | < 1 hora | A Tech Lead |
| **P2** | Performance degradation | < 4 horas | A DevOps |
| **P3** | Minor issues | < 1 día | A Development Team |

### Contactos

```yaml
# Team Contacts (ACTUALIZAR)
tech_lead:
  name: "[NOMBRE]"
  email: "tech.lead@grupogad.gob.ec"
  phone: "+593 [PHONE]"

devops:
  name: "[NOMBRE]"
  email: "devops@grupogad.gob.ec"
  phone: "+593 [PHONE]"

cto:
  name: "[NOMBRE]"
  email: "cto@grupogad.gob.ec"
  phone: "+593 [PHONE]"

security:
  name: "[NOMBRE]"
  email: "security@grupogad.gob.ec"
  phone: "+593 [PHONE]"
```

### External Services

```yaml
domain_registrar: "[PROVIDER]"
cloud_provider: "GCP / AWS / Azure"
ssl_provider: "Let's Encrypt (auto)"
monitoring: "Prometheus + Grafana"
backup_storage: "S3 compatible"
```

---

## 📝 Change Log

| Fecha | Versión | Cambios | Autor |
|-------|---------|---------|-------|
| 2025-10-16 | 1.0.0 | Versión inicial | DevOps Team |

---

## 📚 Referencias

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [PostgreSQL High Availability](https://www.postgresql.org/docs/current/high-availability.html)
- [Docker Production Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**🔐 CONFIDENCIAL - Solo para uso interno del equipo GRUPO_GAD**
