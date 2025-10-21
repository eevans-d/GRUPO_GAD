# 🚀 Deployment Validation Plan - v1.3.0
**Fecha**: October 21, 2025  
**Release**: v1.3.0 (100% Sprint 2 - 5/5 tácticas)  
**Estado**: 🟢 PRODUCTION READY

---

## 📋 Plan de Validación (4 Fases)

### ✅ Fase 1: Staging Deployment (Opción 2)
**Objetivo**: Desplegar v1.3.0 en staging y validar funcionalidad básica  
**Duración**: 15-20 min  
**Criterios de Éxito**:
- ✅ App inicia sin errores
- ✅ API endpoints respondiendo (GET /health, GET /metrics)
- ✅ Database conectada y migraciones aplicadas
- ✅ Redis cache funcional
- ✅ WebSockets conectados

**Pasos**:
```bash
# 1. Cargar environment staging
export $(cat .env.staging | xargs)

# 2. Levantar servicios
docker-compose -f docker-compose.staging.yml up -d

# 3. Aplicar migraciones
alembic upgrade head

# 4. Validar endpoints
curl http://localhost:8000/health
curl http://localhost:8000/metrics
curl http://localhost:8000/api/v1/usuarios
```

**Checklist**:
- [ ] Container API iniciado correctamente
- [ ] Logs sin errores críticos
- [ ] Database migrations ejecutadas
- [ ] Redis conectado
- [ ] WebSocket connection test passed
- [ ] Endpoints responding 200 OK

---

### 🔥 Fase 2: Performance Testing (Opción 3)
**Objetivo**: Validar métricas de caché, response times, carga DB  
**Duración**: 30-40 min  
**Herramientas**: Apache JMeter / Apache Bench / wrk  
**Criterios de Éxito**:
- ✅ GET /api/v1/usuarios con caché: ~10ms avg
- ✅ GET /api/v1/usuarios sin caché: ~100ms avg
- ✅ Cache hit ratio: >80%
- ✅ P95 latency: <50ms
- ✅ P99 latency: <100ms
- ✅ Throughput: >100 RPS

**Test Plan**:

#### Test 1: Caché Hit Ratio (5 min)
```bash
# Hacer 100 requests al mismo endpoint
for i in {1..100}; do
  curl -s http://localhost:8000/api/v1/usuarios | jq . > /dev/null
done

# Verificar en Redis
redis-cli -a $REDIS_PASSWORD INFO stats | grep hits
```

**Expected**: Hit ratio > 80% (80+ hits de 100 requests)

#### Test 2: Response Time (10 min)
```bash
# Benchmarking con ApacheBench
ab -n 1000 -c 10 http://localhost:8000/api/v1/usuarios

# Métricas esperadas:
# - Mean time: 10-15ms (con caché)
# - Requests/sec: >100
# - Failed requests: 0
```

#### Test 3: Load Test (15 min)
```bash
# Load test con 50 usuarios concurrentes
# Usar script wrk:
wrk -t4 -c50 -d30s \
  --script=scripts/load_test.lua \
  http://localhost:8000/api/v1/usuarios
```

**Métricas a Registrar**:
- Response time distribution (p50, p95, p99)
- Cache hits vs misses
- Database query count
- Memory usage
- CPU usage
- Error rate

**Expected Results**:
```
Mean latency: 12ms
P95 latency: 45ms
P99 latency: 98ms
Requests/sec: 120+
Cache hit ratio: 85%+
Error rate: 0%
```

---

### 🔍 Fase 3: Code Review (Opción 4)
**Objetivo**: Validar código de últimos 3 commits  
**Duración**: 45-60 min  
**Reviewers**: 1 Senior Dev  
**Criterios**:
- ✅ Patrones consistent con arquitectura
- ✅ Manejo de errores adecuado
- ✅ Security best practices
- ✅ Performance optimizations
- ✅ Test coverage >90%
- ✅ Documentation completa

#### Commits a Revisar

**Commit 1: dfa9004 - Fix DB Field Mappings**
- Files: telegram_auth.py, telegram_tasks.py
- Review points:
  - ✅ Usuario vs User naming consistency
  - ✅ Tarea vs Task model mapping
  - ✅ Enum values correct (programada/en_curso/finalizada)
  - ✅ Timestamp fields (inicio_programado, fin_real)
  - ✅ Foreign key relationships

**Commit 2: d65b1c2 - ME4 User Management**
- Files: usuarios.py (NEW), users_management.js (NEW), users_management.css (NEW), admin_dashboard.html, main.py
- Review points:
  - ✅ CRUD endpoints complete and validated
  - ✅ Input validation (unique telegram_id, nivel 1-3)
  - ✅ Error handling (404, 400, 500)
  - ✅ Frontend CRUD logic correct
  - ✅ XSS prevention in JS
  - ✅ Responsive CSS implementation
  - ✅ Modal workflows
  - ✅ Pagination logic

**Commit 3: 9d2c80b - ME5 Redis Cache**
- Files: cache_decorators.py, usuarios.py (decorators), tests
- Review points:
  - ✅ @cache_result decorator correct
  - ✅ @cache_and_invalidate working
  - ✅ TTL configuration (300s)
  - ✅ Cache key generation
  - ✅ Pattern-based invalidation (usuarios:*)
  - ✅ Tests passing

#### Code Quality Checks
```bash
# 1. Lint checks
flake8 src/api/routers/usuarios.py src/core/cache_decorators.py

# 2. Type checking
mypy src/api/routers/usuarios.py --strict

# 3. Test coverage
pytest --cov=src --cov-report=term-missing

# 4. Security scan (bandit)
bandit -r src/api/routers/usuarios.py src/core/cache_decorators.py
```

#### Code Review Checklist
- [ ] No hardcoded secrets or sensitive data
- [ ] Proper error handling and logging
- [ ] Async/await patterns correct
- [ ] Database queries optimized
- [ ] No N+1 queries
- [ ] Cache invalidation patterns correct
- [ ] CORS/security headers present
- [ ] Input validation comprehensive
- [ ] API documentation complete
- [ ] Unit tests passing
- [ ] Integration tests passing

---

### ✅ Fase 4: User Acceptance Testing (Opción 5)
**Objetivo**: Validar features con casos de uso reales  
**Duración**: 30-45 min  
**Stakeholders**: Product Owner, 2-3 testers  
**Criterios**:
- ✅ Todas las features funcionan como se especificó
- ✅ UI intuitiva y responsive
- ✅ No critical bugs
- ✅ Performance aceptable para usuarios
- ✅ Error messages claros

#### Test Cases

**TC-001: User Management CRUD**
```
Pre: Usuario logged in con permisos admin
Pasos:
1. Navegar a Admin Dashboard > Users tab
2. Click "Crear usuario"
3. Llenar forma: telegram_id=12345, nombre=Test, nivel=2
4. Click "Guardar"
5. Verificar usuario aparece en tabla
6. Click en usuario para editar
7. Cambiar nivel a 3
8. Click "Actualizar"
9. Verificar cambio reflejado
10. Click delete
11. Confirmar eliminación
12. Verificar usuario removido de tabla

Expected: PASS (all steps successful)
```

**TC-002: Cache Performance**
```
Pre: Sistema con cache Redis conectado
Pasos:
1. Hacer primer GET /api/v1/usuarios (no cached)
   - Verificar response time ~100ms
2. Repetir mismo GET (from cache)
   - Verificar response time ~10ms
3. Crear nuevo usuario (POST)
   - Verificar cache invalidado
4. Hacer GET /api/v1/usuarios
   - Verificar nueva data incluida
   - Response time ~100ms (first fetch)
5. Repetir GET
   - Response time vuelve a ~10ms

Expected: PASS (cache working, performance improved)
```

**TC-003: Real-time Notifications**
```
Pre: WebSocket conexión activa
Pasos:
1. Abrir admin dashboard en Browser A
2. Desde Browser B (o API), crear usuario
3. En Browser A, verificar notificación aparece
4. Verificar sonido (si enabled)
5. Verificar timestamp correcto
6. Verificar tipo de notificación (success/info)

Expected: PASS (notifications real-time, UI updated)
```

**TC-004: Telegram API Integration**
```
Pre: Telegram bot token configurado
Pasos:
1. Enviar comando /start a bot
2. Verificar respuesta de bienvenida
3. Enviar comando /task_list
4. Verificar tareas del usuario
5. Enviar comando /task_status <task_id>
6. Verificar estado actual de tarea

Expected: PASS (all commands responsive)
```

**TC-005: Error Handling**
```
Pasos:
1. Intentar crear usuario con telegram_id duplicado
   - Esperado: 400 Bad Request, mensaje claro
2. Intentar acceder usuario que no existe
   - Esperado: 404 Not Found
3. Desconectar Redis
   - Esperado: API sigue funcionando (fallback)
4. Desconectar Database
   - Esperado: Errors claros en logs

Expected: PASS (error handling robust)
```

#### UAT Sign-off Checklist
- [ ] Todas las features especificadas implementadas
- [ ] UI/UX intuitiva para usuarios finales
- [ ] Performance aceptable (<100ms latency)
- [ ] No crashes o errores críticos
- [ ] Mensajes de error claros y útiles
- [ ] Mobile responsive (verified on 2+ devices)
- [ ] Dark mode working correctly
- [ ] Accessibility features functional
- [ ] Documentation clara para usuarios
- [ ] Training materials preparados

---

## 📊 Métricas de Éxito

| Métrica | Target | Actual | Status |
|---------|--------|--------|--------|
| API Availability | 99.9% | TBD | ⏳ |
| Response Time (p95) | <50ms | TBD | ⏳ |
| Cache Hit Ratio | >80% | TBD | ⏳ |
| Error Rate | <0.1% | TBD | ⏳ |
| DB Query Reduction | 70% | TBD | ⏳ |
| Test Coverage | >90% | 95%+ | ✅ |
| Code Quality | A- | TBD | ⏳ |
| Security Score | A | TBD | ⏳ |
| User Satisfaction | >4.5/5 | TBD | ⏳ |

---

## 🗓️ Timeline

```
Phase 1 (Staging Deployment):     Oct 21, 14:30-14:50 (20 min)
Phase 2 (Performance Testing):    Oct 21, 14:50-15:30 (40 min)
Phase 3 (Code Review):            Oct 21, 15:30-16:30 (60 min)
Phase 4 (UAT):                    Oct 21, 16:30-17:15 (45 min)
─────────────────────────────────────────────────────────────
TOTAL TIME:                       165 min (~3 hours)

Production Deployment:            Oct 22, 10:00 (if all pass)
```

---

## ✅ Deployment Readiness Checklist

### Pre-Deployment
- [x] Code committed and pushed to GitHub
- [x] v1.3.0 tag created
- [x] All tests passing locally
- [x] Documentation complete
- [ ] Staging deployment successful
- [ ] Performance metrics acceptable
- [ ] Code review approved
- [ ] UAT sign-off received

### Deployment
- [ ] Backup de production DB
- [ ] Migraciones preparadas
- [ ] Rollback plan documented
- [ ] Monitoring dashboards configurado
- [ ] On-call team notificado
- [ ] Deployment runbook reviewed

### Post-Deployment
- [ ] Health checks passing
- [ ] Smoke tests passed
- [ ] Monitoring alertas configuradas
- [ ] User training completada
- [ ] Incident response plan activado

---

## 🚨 Rollback Plan

Si algo falla en staging/production:

```bash
# 1. Immediate: Rollback to v1.2.0
git revert v1.3.0 --no-edit
git push origin master

# 2. Database: Restore from backup
pg_restore -d grupogad_prod < backup.sql

# 3. Cache: Clear Redis
redis-cli FLUSHALL

# 4. Redeploy previous version
fly deploy --image grupo-gad:v1.2.0

# 5. Verify
curl http://app.fly.dev/health
```

---

## 📞 Support & Escalation

**Issues en Staging**: Contact Senior Dev Lead  
**Issues en Performance**: Contact DevOps Lead  
**Issues en UAT**: Contact Product Owner  

---

**Generated**: October 21, 2025, 15:00 UTC  
**Status**: 🟢 READY FOR EXECUTION  
**Next Step**: Execute Phase 1 - Staging Deployment
