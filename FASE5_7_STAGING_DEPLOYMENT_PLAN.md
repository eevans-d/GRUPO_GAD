# 🚀 FASE 5.7: STAGING DEPLOYMENT TEST - PLAN DE EJECUCIÓN

**Fecha**: 16 Octubre 2025  
**Objetivo**: Validar deployment completo en entorno staging local  
**Metodología**: NO SALTEAR NINGÚN PASO  
**Criterio de éxito**: Todos los checks pasando ✅

---

## 📋 CHECKLIST DE EJECUCIÓN

### FASE 5.7.1: Pre-Flight Checks ☑️
- [ ] 1.1. Validar `.env.staging` existe y tiene todos los secrets
- [ ] 1.2. Validar `docker-compose.staging.yml` está completo
- [ ] 1.3. Verificar puertos disponibles (8001, 5435, 6382, 8443)
- [ ] 1.4. Limpiar containers staging previos si existen
- [ ] 1.5. Verificar disk space suficiente (>5GB)
- [ ] 1.6. Validar Docker daemon running
- [ ] 1.7. Validar network no conflictos

### FASE 5.7.2: Database Setup ☑️
- [ ] 2.1. Levantar PostgreSQL staging
- [ ] 2.2. Esperar healthcheck pass (10s timeout)
- [ ] 2.3. Validar PostGIS extension instalada
- [ ] 2.4. Ejecutar migraciones Alembic
- [ ] 2.5. Verificar tablas creadas
- [ ] 2.6. Seed data staging (si aplica)

### FASE 5.7.3: Redis Setup ☑️
- [ ] 3.1. Levantar Redis staging
- [ ] 3.2. Esperar healthcheck pass
- [ ] 3.3. Validar autenticación con password
- [ ] 3.4. Test SET/GET keys
- [ ] 3.5. Verificar maxmemory policy

### FASE 5.7.4: API Deployment ☑️
- [ ] 4.1. Build imagen Docker API
- [ ] 4.2. Levantar API staging
- [ ] 4.3. Esperar healthcheck pass (30s timeout)
- [ ] 4.4. Verificar logs sin errores
- [ ] 4.5. Test endpoint `/health`
- [ ] 4.6. Test endpoint `/docs`
- [ ] 4.7. Test endpoint `/metrics`

### FASE 5.7.5: Caddy Reverse Proxy ☑️
- [ ] 5.1. Verificar Caddyfile.staging
- [ ] 5.2. Levantar Caddy staging
- [ ] 5.3. Validar certificado self-signed generado
- [ ] 5.4. Test HTTPS (https://localhost:8443)
- [ ] 5.5. Verificar HTTP → HTTPS redirect
- [ ] 5.6. Validar security headers

### FASE 5.7.6: Health Checks Completos ☑️
- [ ] 6.1. Ejecutar `health_check.sh --production` (simula staging)
- [ ] 6.2. Validar Docker containers (4/4 running)
- [ ] 6.3. Validar API health endpoint
- [ ] 6.4. Validar API response time (<300ms)
- [ ] 6.5. Validar PostgreSQL connectivity
- [ ] 6.6. Validar Redis connectivity
- [ ] 6.7. Validar disk/memory/cpu usage
- [ ] 6.8. Verificar logs accesibles
- [ ] 6.9. Exit code 0 (healthy)

### FASE 5.7.7: Functional Tests ☑️
- [ ] 7.1. Test autenticación (login/JWT)
- [ ] 7.2. Test CRUD endpoints principales
- [ ] 7.3. Test WebSocket connection
- [ ] 7.4. Test Redis caching
- [ ] 7.5. Test error handling
- [ ] 7.6. Test rate limiting (si configurado)

### FASE 5.7.8: Performance Baseline ☑️
- [ ] 8.1. Ejecutar pytest con coverage
- [ ] 8.2. Validar coverage ≥70%
- [ ] 8.3. Ejecutar smoke tests
- [ ] 8.4. Medir latencia baseline (curl timing)
- [ ] 8.5. Test concurrencia (10 requests simultáneos)
- [ ] 8.6. Verificar no memory leaks

### FASE 5.7.9: Monitoring Validation ☑️
- [ ] 9.1. Levantar stack monitoring staging
- [ ] 9.2. Verificar Prometheus scraping
- [ ] 9.3. Verificar métricas en /metrics
- [ ] 9.4. Grafana dashboard carga datos
- [ ] 9.5. Alertas configuradas (test firing)

### FASE 5.7.10: Deployment Scripts Test ☑️
- [ ] 10.1. Adaptar `deploy_production.sh` para staging
- [ ] 10.2. Test deploy script (dry-run)
- [ ] 10.3. Test rollback script (simulado)
- [ ] 10.4. Verificar backup creation
- [ ] 10.5. Verificar zero-downtime behavior

### FASE 5.7.11: Security Validation ☑️
- [ ] 11.1. Verificar HTTPS funcionando
- [ ] 11.2. Test security headers presente
- [ ] 11.3. Validar secrets no expuestos
- [ ] 11.4. Test autenticación JWT
- [ ] 11.5. Verificar CORS configurado

### FASE 5.7.12: Documentation & Cleanup ☑️
- [ ] 12.1. Documentar issues encontrados
- [ ] 12.2. Documentar fixes aplicados
- [ ] 12.3. Actualizar DEPLOYMENT_CHECKLIST si necesario
- [ ] 12.4. Crear reporte staging test
- [ ] 12.5. Stop containers staging
- [ ] 12.6. Cleanup volumes staging (opcional)
- [ ] 12.7. Commit cambios necesarios

---

## 🎯 CRITERIOS DE ÉXITO

```yaml
deployment:
  all_containers_running: true
  all_healthchecks_passing: true
  api_response_time: <300ms
  zero_errors_in_logs: true

functionality:
  api_endpoints_working: true
  websocket_working: true
  auth_working: true
  database_working: true
  redis_working: true

performance:
  pytest_coverage: ≥70%
  api_latency_p95: <200ms
  concurrent_requests: ≥10

security:
  https_working: true
  jwt_auth_working: true
  secrets_not_exposed: true
  security_headers_present: true

monitoring:
  prometheus_scraping: true
  grafana_loading: true
  metrics_available: true
```

---

## 🔧 COMANDOS DE EJECUCIÓN

### Pre-Flight
```bash
# 1. Validar environment
cat .env.staging

# 2. Verificar puertos libres
ss -tulpn | grep -E '8001|5435|6382|8443'

# 3. Limpiar containers previos
docker compose -f docker-compose.staging.yml down -v
```

### Deployment
```bash
# 4. Levantar servicios staging
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# 5. Verificar containers
docker compose -f docker-compose.staging.yml ps

# 6. Ver logs
docker compose -f docker-compose.staging.yml logs -f
```

### Migrations
```bash
# 7. Ejecutar migraciones
docker compose -f docker-compose.staging.yml exec api-staging alembic upgrade head

# 8. Verificar tablas
docker compose -f docker-compose.staging.yml exec db-staging psql -U postgres -d grupogad_staging -c "\dt"
```

### Testing
```bash
# 9. Health check
./scripts/health_check.sh --production  # Simula staging

# 10. API tests
curl http://localhost:8001/health
curl https://localhost:8443/health --insecure  # Self-signed cert
curl http://localhost:8001/docs

# 11. Pytest
docker compose -f docker-compose.staging.yml exec api-staging pytest -v

# 12. Coverage
docker compose -f docker-compose.staging.yml exec api-staging pytest --cov=src --cov-report=term-missing
```

### Monitoring
```bash
# 13. Levantar monitoring staging
docker compose -f docker-compose.monitoring.yml up -d

# 14. Verificar métricas
curl http://localhost:8001/metrics

# 15. Prometheus targets
curl http://localhost:9090/api/v1/targets | jq
```

### Cleanup
```bash
# 16. Stop servicios
docker compose -f docker-compose.staging.yml down

# 17. Cleanup volumes (opcional - destruye data)
docker compose -f docker-compose.staging.yml down -v

# 18. Cleanup monitoring
docker compose -f docker-compose.monitoring.yml down
```

---

## 📝 ISSUES TRACKING

### Issues Encontrados
- [ ] Issue #1: [Descripción]
  - Severity: [LOW|MEDIUM|HIGH|CRITICAL]
  - Impact: [Descripción]
  - Fix: [Descripción solución]
  - Status: [OPEN|IN_PROGRESS|RESOLVED]

### Fixes Aplicados
- [x] Fix #1: [Descripción]
  - Before: [Estado anterior]
  - After: [Estado nuevo]
  - Files changed: [Lista archivos]
  - Commit: [SHA]

---

## 🎓 LECCIONES APRENDIDAS

### ✅ Lo Que Funcionó
1. [Item 1]
2. [Item 2]

### ❌ Lo Que Falló
1. [Item 1] - Fix: [Solución]
2. [Item 2] - Fix: [Solución]

### 🔄 Mejoras Necesarias
1. [Item 1]
2. [Item 2]

---

## 📊 MÉTRICAS FINALES

```yaml
deployment_staging:
  duration: [X] minutos
  containers_running: [X]/4
  healthchecks_passing: [X]/4
  
tests:
  pytest_passed: [X]/[Y]
  coverage: [X]%
  smoke_tests_passed: [X]/[Y]
  
performance:
  api_latency_avg: [X]ms
  api_latency_p95: [X]ms
  api_latency_p99: [X]ms
  concurrent_requests_handled: [X]
  
security:
  https_working: [true|false]
  jwt_auth_working: [true|false]
  vulnerabilities_found: [X]
```

---

## ✅ SIGN-OFF

**Staging Deployment Test**:
- [ ] Todas las fases completadas (12/12)
- [ ] Todos los checks pasando
- [ ] Issues documentados y resueltos
- [ ] Métricas dentro del baseline
- [ ] Ready para PASO 2 (CI/CD Setup)

**Aprobado por**: _______________  
**Fecha**: _______________  
**Firma**: _______________

---

**Próximo paso**: FASE 5.8 - CI/CD Configuration (GitHub Secrets)

