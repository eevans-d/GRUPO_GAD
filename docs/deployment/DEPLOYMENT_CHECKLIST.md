# 🚀 DEPLOYMENT CHECKLIST - GRUPO_GAD

**Versión**: 1.0.0  
**Última actualización**: 2025-10-16  
**Propósito**: Checklist completo para deployment seguro a producción

---

## 📋 Índice

- [Pre-Deployment](#pre-deployment)
- [Deployment Day](#deployment-day)
- [Post-Deployment](#post-deployment)
- [Rollback Procedure](#rollback-procedure)

---

## 🔍 PRE-DEPLOYMENT

### 1. Code Quality & Testing

#### 1.1 Tests Locales

```bash
# Ejecutar suite completa de tests
- [ ] pytest tests/ --cov=src --cov-report=term-missing
      → Coverage: ≥ 70%
      → All tests passing

# Verificar linting
- [ ] ruff check src/ tests/
      → No HIGH/MEDIUM issues

# Type checking (opcional)
- [ ] mypy src/
      → No critical errors
```

**Criterios de aceptación**:
- ✅ Test coverage ≥ 70%
- ✅ 0 failing tests
- ✅ 0 HIGH/MEDIUM lint issues

---

#### 1.2 Security Scanning

```bash
# Dependency vulnerabilities
- [ ] safety check --file requirements.txt
      → 0 CRITICAL vulnerabilities
      → Document known issues if any

# Static analysis
- [ ] bandit -r src/ -ll
      → 0 HIGH/MEDIUM issues
      → Review LOW issues

# Secret detection
- [ ] gitleaks detect --source . --no-git
      → No secrets in committed files
      → All secrets in .env.* (not committed)

# Container scan
- [ ] trivy image grupo_gad-api:latest --severity CRITICAL,HIGH
      → 0 CRITICAL
      → Document HIGH vulnerabilities + mitigations
```

**Criterios de aceptación**:
- ✅ 0 CRITICAL vulnerabilities
- ✅ HIGH vulnerabilities documented + mitigated
- ✅ No secrets en git history

---

#### 1.3 Performance Testing

```bash
# Load test (local/staging)
- [ ] locust -f tests/load/locustfile.py \
        --host http://localhost:8000 \
        --users 50 --spawn-rate 5 --run-time 5m \
        --headless --html reports/load-test.html

# Analizar resultados
- [ ] P95 latency < 500ms
- [ ] P99 latency < 2s
- [ ] 0% error rate bajo carga normal
- [ ] RPS sostenible ≥ 100 req/s
```

**Criterios de aceptación**:
- ✅ P95 latency < 500ms
- ✅ Error rate < 1% bajo carga
- ✅ No memory leaks durante test prolongado

---

### 2. Infrastructure Preparation

#### 2.1 Server Setup

```bash
# SSH al servidor
- [ ] ssh user@production-server

# Verificar recursos disponibles
- [ ] df -h
      → Disk space ≥ 20GB disponible
- [ ] free -h
      → Memory ≥ 4GB disponible
- [ ] nproc
      → CPU cores ≥ 2

# Verificar Docker
- [ ] docker --version
      → Docker ≥ 24.0
- [ ] docker compose version
      → Compose ≥ 2.20

# Verificar conectividad
- [ ] curl -I https://ghcr.io
      → Acceso a container registry
- [ ] ping 8.8.8.8
      → Conectividad internet
```

**Criterios de aceptación**:
- ✅ Disk ≥ 20GB
- ✅ Memory ≥ 4GB
- ✅ Docker + Compose instalados
- ✅ Conectividad externa OK

---

#### 2.2 Secrets Configuration

```bash
# Clonar repo (si es primer deployment)
- [ ] cd /opt
- [ ] git clone https://github.com/eevans-d/GRUPO_GAD.git grupogad
- [ ] cd grupogad

# Copiar template de secrets
- [ ] cp .env.production.example .env.production

# Generar secrets seguros
- [ ] openssl rand -hex 32 > /tmp/secret_key.txt
- [ ] openssl rand -base64 32 > /tmp/postgres_pass.txt
- [ ] openssl rand -base64 32 > /tmp/redis_pass.txt

# Editar .env.production
- [ ] vim .env.production
      Variables OBLIGATORIAS a cambiar:
      
      ✓ SECRET_KEY=<64-char-hex from /tmp/secret_key.txt>
      ✓ POSTGRES_PASSWORD=<from /tmp/postgres_pass.txt>
      ✓ REDIS_PASSWORD=<from /tmp/redis_pass.txt>
      ✓ TELEGRAM_BOT_TOKEN=<real-token> (si aplica)
      ✓ ALLOWED_HOSTS=api.grupogad.gob.ec,grupogad.gob.ec
      ✓ CORS_ORIGINS=https://grupogad.gob.ec

# Validar que no quedan placeholders
- [ ] grep -i "CAMBIAR_POR" .env.production
      → Output: (vacío) ✅
      → Si hay matches: ❌ STOP - Configurar secrets

# Limpiar archivos temporales
- [ ] shred -u /tmp/*_key.txt /tmp/*_pass.txt
```

**Criterios de aceptación**:
- ✅ .env.production existe
- ✅ Todos los secrets cambiados (no placeholders)
- ✅ Secrets seguros (≥32 caracteres aleatorios)
- ✅ Archivos temporales eliminados

---

#### 2.3 Domain & DNS Configuration

```bash
# Verificar DNS apunta al servidor
- [ ] nslookup api.grupogad.gob.ec
      → Apunta a: <IP del servidor> ✅

- [ ] nslookup grupogad.gob.ec
      → Apunta a: <IP del servidor> ✅

# Test conectividad desde exterior
- [ ] curl -I http://api.grupogad.gob.ec
      → Llega al servidor (aunque no haya servicio todavía)

# Configurar Caddyfile con dominio real
- [ ] cp Caddyfile Caddyfile.backup
- [ ] cp Caddyfile.production Caddyfile

# Editar Caddyfile
- [ ] vim Caddyfile
      → Descomentar sección production
      → Cambiar :80 por api.grupogad.gob.ec
      → Configurar email admin@grupogad.gob.ec para Let's Encrypt
```

**Criterios de aceptación**:
- ✅ DNS configurado correctamente
- ✅ Dominio apunta al servidor
- ✅ Caddyfile actualizado con dominio real
- ✅ Email configurado para Let's Encrypt

---

#### 2.4 Backup Configuration

```bash
# Crear directorio de backups
- [ ] mkdir -p /opt/grupogad/backups
- [ ] chmod 700 /opt/grupogad/backups

# Configurar backup automático (cron)
- [ ] crontab -e
      Agregar línea:
      0 2 * * * /opt/grupogad/scripts/backup_production.sh >> /opt/grupogad/logs/backup.log 2>&1

# Test manual backup
- [ ] cd /opt/grupogad
- [ ] ./scripts/backup_production.sh
      → Archivo creado en backups/*.sql.gz ✅
      → Tamaño > 0 bytes ✅
```

**Criterios de aceptación**:
- ✅ Directorio backups existe con permisos 700
- ✅ Cron job configurado (daily 2am)
- ✅ Backup manual funciona

---

### 3. CI/CD Setup (Opcional pero Recomendado)

```bash
# GitHub Repository Settings → Secrets and Variables → Actions
- [ ] PRODUCTION_SSH_KEY
      → Private SSH key para acceso al servidor
      → ssh-keygen -t ed25519 -C "github-actions@grupogad"
      → Agregar public key a ~/.ssh/authorized_keys en servidor

- [ ] PRODUCTION_USER
      → Username SSH (ej: ubuntu, admin)

- [ ] PRODUCTION_HOST
      → IP o hostname del servidor

- [ ] GRAFANA_ADMIN_PASSWORD (opcional)
      → Password seguro para Grafana

- [ ] SLACK_WEBHOOK_URL (opcional)
      → Webhook para notificaciones Slack
```

**Criterios de aceptación**:
- ✅ SSH key pair generado
- ✅ Public key en servidor
- ✅ Secrets configurados en GitHub
- ✅ Test SSH connection desde GitHub Actions (dry-run)

---

### 4. Monitoring Setup

```bash
# Configurar AlertManager notifications
- [ ] vim monitoring/alertmanager/alertmanager.yml
      
      # SMTP (Email)
      smtp_auth_username: alerts@grupogad.gob.ec
      smtp_auth_password: <Gmail App Password o SMTP password>
      
      # Slack (opcional)
      api_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      channel: '#alerts-grupogad'

# Configurar Grafana admin password
- [ ] vim .env.production
      GRAFANA_ADMIN_PASSWORD=<secure-random-password>

# Test SMTP (opcional)
- [ ] echo "Test email" | sendmail -v alerts@grupogad.gob.ec
      → Email recibido ✅
```

**Criterios de aceptación**:
- ✅ SMTP configurado (si se usa email)
- ✅ Slack webhook configurado (si se usa Slack)
- ✅ Grafana password seguro configurado
- ✅ Test de notificaciones OK

---

## 🚀 DEPLOYMENT DAY

### 5. Pre-Flight Checks

```bash
# Verificar estado del código
- [ ] cd /opt/grupogad
- [ ] git fetch origin
- [ ] git status
      → On branch master
      → Up to date with origin/master

- [ ] git log --oneline -5
      → Commits esperados visibles

# Verificar que no hay cambios locales
- [ ] git diff
      → Output: (vacío) ✅

# Pull último código
- [ ] git pull origin master
      → Already up to date o Fast-forward ✅
```

**Criterios de aceptación**:
- ✅ Branch master actualizado
- ✅ No cambios locales sin commit
- ✅ Código sincronizado con remote

---

### 6. Initial Deployment

```bash
# Crear Docker network
- [ ] docker network create gad-network || echo "Network exists"

# Iniciar base de datos primero
- [ ] docker compose -f docker-compose.prod.yml up -d db redis
- [ ] sleep 10

# Verificar DB está healthy
- [ ] docker compose -f docker-compose.prod.yml ps db
      → STATUS: healthy ✅

# Ejecutar migraciones (primera vez)
- [ ] docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
      → INFO [alembic.runtime.migration] Running upgrade...
      → No errors ✅

# Deploy completo con script
- [ ] ./scripts/deploy_production.sh --force
      → ✅ Prerequisitos OK
      → ✅ Backup creado
      → ✅ Imágenes actualizadas
      → ✅ Migraciones completadas
      → ✅ Servicios desplegados
      → ✅ Smoke tests completados
      → 🎉 Deployment completado exitosamente
```

**Duración estimada**: 5-10 minutos

**Criterios de aceptación**:
- ✅ Todos los servicios en estado `healthy`
- ✅ Script deployment sin errores
- ✅ Smoke tests passing

---

### 7. HTTPS & SSL Setup

```bash
# Caddy auto-genera certificados Let's Encrypt
# Solo verificar que funciona:

- [ ] docker compose -f docker-compose.prod.yml logs caddy | grep -i "certificate"
      → Successfully obtained certificate ✅

# Test HTTPS endpoint (puede tardar 1-2 min)
- [ ] curl -I https://api.grupogad.gob.ec/api/v1/health
      → HTTP/2 200 ✅
      → No SSL errors ✅

# Verificar redirección HTTP → HTTPS
- [ ] curl -I http://api.grupogad.gob.ec/api/v1/health
      → HTTP/1.1 308 Permanent Redirect
      → Location: https://... ✅
```

**Criterios de aceptación**:
- ✅ Certificado SSL obtenido
- ✅ HTTPS funciona correctamente
- ✅ HTTP redirige a HTTPS
- ✅ No errores SSL en navegador

---

## ✅ POST-DEPLOYMENT

### 8. Functional Verification

```bash
# Test 1: API Health
- [ ] curl https://api.grupogad.gob.ec/api/v1/health
      → {"status":"healthy","environment":"production"} ✅

# Test 2: Metrics endpoint
- [ ] curl https://api.grupogad.gob.ec/metrics | head -20
      → prometheus metrics output ✅

# Test 3: Database connectivity
- [ ] docker exec grupo_gad_api python -c \
        "from src.api.db import get_db_session; print('DB OK')"
      → DB OK ✅

# Test 4: Redis connectivity
- [ ] docker exec grupo_gad_redis redis-cli ping
      → PONG ✅

# Test 5: WebSocket connection (si aplica)
- [ ] python3 scripts/ws_smoke_test.py
      → CONNECTION_ACK received ✅
      → PING/PONG working ✅
```

**Criterios de aceptación**:
- ✅ Todos los tests passing
- ✅ API responde correctamente
- ✅ DB y Redis conectados
- ✅ WebSocket funcional

---

### 9. Monitoring Verification

```bash
# Iniciar monitoring stack
- [ ] docker compose -f docker-compose.monitoring.yml up -d
- [ ] sleep 15

# Verificar Prometheus scraping
- [ ] curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'
      → "up" para todos los targets ✅

# Verificar Grafana accesible
- [ ] curl -I http://localhost:3000
      → HTTP/1.1 200 OK ✅

# Login a Grafana
- [ ] Abrir navegador: http://<server-ip>:3000
      → Login: admin / <GRAFANA_ADMIN_PASSWORD>
      → Dashboard cargando ✅

# Verificar AlertManager
- [ ] curl http://localhost:9093/api/v2/alerts
      → [] (sin alertas activas) ✅
```

**Criterios de aceptación**:
- ✅ Prometheus scrapeando todos los targets
- ✅ Grafana accesible y funcional
- ✅ AlertManager sin alertas críticas
- ✅ Dashboards cargando datos

---

### 10. Performance Baseline

```bash
# Ejecutar load test light contra producción
- [ ] locust -f tests/load/locustfile.py \
        --host https://api.grupogad.gob.ec \
        --users 10 --spawn-rate 2 --run-time 5m \
        --headless --html reports/prod-baseline.html

# Analizar resultados
- [ ] Median response time < 200ms
- [ ] 95th percentile < 500ms
- [ ] 99th percentile < 2s
- [ ] Failures: 0% ✅

# Guardar baseline
- [ ] cp reports/prod-baseline.html reports/baseline_$(date +%Y%m%d).html
```

**Criterios de aceptación**:
- ✅ P95 < 500ms
- ✅ P99 < 2s
- ✅ Error rate < 1%
- ✅ Baseline documentado

---

### 11. Security Validation

```bash
# Verificar security headers
- [ ] curl -I https://api.grupogad.gob.ec | grep -E "(Strict-Transport|X-Content|X-Frame)"
      → Strict-Transport-Security: max-age=31536000 ✅
      → X-Content-Type-Options: nosniff ✅
      → X-Frame-Options: DENY ✅

# Test SSL rating (opcional)
- [ ] Visitar: https://www.ssllabs.com/ssltest/analyze.html?d=api.grupogad.gob.ec
      → Rating: A o A+ ✅

# Verificar no se exponen endpoints debug
- [ ] curl https://api.grupogad.gob.ec/docs
      → 404 Not Found (en producción debe estar deshabilitado) ✅

# Verificar rate limiting (si está habilitado)
- [ ] for i in {1..100}; do curl -s https://api.grupogad.gob.ec/api/v1/health; done
      → Algunas requests con 429 Too Many Requests ✅
```

**Criterios de aceptación**:
- ✅ Security headers presentes
- ✅ SSL rating A o superior
- ✅ Debug endpoints deshabilitados
- ✅ Rate limiting funcional

---

### 12. Documentation Update

```bash
# Documentar deployment
- [ ] Crear archivo: deployments/deployment_$(date +%Y%m%d).md
      Contenido:
      - Fecha y hora deployment
      - Commit hash deployed
      - Personas involucradas
      - Incidencias (si hubo)
      - Performance baseline results
      - Configuraciones específicas

# Actualizar runbook con lecciones aprendidas
- [ ] vim docs/PRODUCTION_RUNBOOK.md
      → Agregar sección "Deployment History"
      → Documentar issues encontrados + soluciones

# Notificar al equipo
- [ ] Enviar email/Slack:
      "✅ GRUPO_GAD deployed to production
       URL: https://api.grupogad.gob.ec
       Monitoring: http://<server>:3000
       Status: Healthy
       Performance: P95 <500ms, P99 <2s"
```

**Criterios de aceptación**:
- ✅ Deployment documentado
- ✅ Runbook actualizado
- ✅ Equipo notificado
- ✅ Access info compartida

---

## 🔄 ROLLBACK PROCEDURE

**⚠️ USAR SOLO EN CASO DE EMERGENCIA**

### Cuándo hacer rollback

- ❌ API no responde después de 5 minutos
- ❌ Error rate > 10%
- ❌ P99 latency > 5s sostenido
- ❌ Bug crítico descubierto en producción
- ❌ Data corruption detectada

### Rollback Steps

```bash
# 1. Stop traffic (opcional - si es crítico)
- [ ] docker compose -f docker-compose.prod.yml stop caddy
      → Traffic stopped ✅

# 2. Ejecutar rollback script
- [ ] ./scripts/rollback_production.sh
      → Confirmación: yes
      → 🛑 Servicios detenidos
      → 💾 DB restaurada desde backup
      → 🔄 Código revertido
      → 🚀 Servicios reiniciados
      → 🧪 Rollback verificado
      → 🎉 Rollback completado

# 3. Verificar health
- [ ] curl https://api.grupogad.gob.ec/api/v1/health
      → {"status":"healthy"} ✅

# 4. Verificar funcionalidad
- [ ] Ejecutar smoke tests
- [ ] Verificar endpoints críticos
- [ ] Verificar DB data integrity

# 5. Notificar rollback
- [ ] Enviar notificación al equipo
      "⚠️ ROLLBACK ejecutado en producción
       Razón: <describir issue>
       Status: Sistema restaurado
       Action items: <investigación necesaria>"
```

**Duración estimada**: 2-3 minutos

---

## 📊 Monitoring Checklist (Primeras 24h)

```bash
# Hora 0 (inmediatamente después de deployment)
- [ ] Verificar dashboards Grafana
- [ ] Verificar 0 alertas críticas
- [ ] Verificar logs sin errores

# Hora 1
- [ ] Verificar métricas estables
- [ ] Verificar memoria no crece indefinidamente
- [ ] Verificar CPU < 50%

# Hora 4
- [ ] Verificar P95 latency < 500ms
- [ ] Verificar error rate < 1%
- [ ] Verificar DB connections < 20

# Hora 12
- [ ] Analizar logs de errores
- [ ] Verificar no hay memory leaks
- [ ] Verificar backups automáticos funcionan

# Hora 24
- [ ] Performance baseline vs staging
- [ ] Documentar métricas clave
- [ ] Reunión post-mortem deployment
```

---

## 📝 Sign-Off

**Deployment ejecutado por**: ___________________________  
**Fecha**: ___________________________  
**Hora inicio**: ___________________________  
**Hora fin**: ___________________________

**Verificaciones completadas**:

- [ ] Pre-deployment checklist: 100%
- [ ] Deployment exitoso: ✅
- [ ] Post-deployment verification: 100%
- [ ] Monitoring activo: ✅
- [ ] Performance baseline: Documentado
- [ ] Equipo notificado: ✅

**Issues encontrados**: (Ninguno / Listar)

**Lecciones aprendidas**: (Documentar para próximo deployment)

---

**Próxima revisión**: 24 horas post-deployment  
**Owner**: DevOps Team / Tech Lead

---

**🎉 ¡Deployment a producción completado exitosamente!**
