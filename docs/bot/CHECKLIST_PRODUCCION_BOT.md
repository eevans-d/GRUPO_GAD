# ✅ Checklist de Producción - Bot de Telegram GRUPO_GAD

## 📋 Información del Documento

**Fecha de creación:** 11 de octubre de 2025  
**Versión del Bot:** 1.0.0  
**Deployment Target:** Producción  
**Autor:** Equipo de Desarrollo GRUPO_GAD

---

## 🎯 Objetivo

Este checklist asegura que todos los pasos críticos se completan antes, durante y después de un deployment a producción. **NUNCA** deployar a producción sin completar este checklist.

---

## 📊 Guía de Uso

### Símbolos

- ✅ **Completado y verificado**
- 🔄 **En progreso**
- ❌ **Falta completar**
- ⚠️ **Bloqueante - NO deployar sin esto**
- 🔔 **Comunicación requerida**

### Responsables

- **DEV:** Desarrollador que implementó features
- **LEAD:** Tech Lead / Reviewer
- **OPS:** DevOps / SysAdmin
- **QA:** Quality Assurance
- **PO:** Product Owner

---

## 📝 FASE 1: PRE-DEPLOYMENT (1-2 días antes)

### 🔍 Code Quality

| # | Tarea | Responsable | Status | Notas |
|---|-------|-------------|--------|-------|
| 1.1 | ⚠️ Todos los tests pasan (39/39) | DEV | ❌ | `pytest tests/bot/ -v` |
| 1.2 | ⚠️ Coverage > 80% | DEV | ❌ | `pytest --cov=src/bot` |
| 1.3 | Code review aprobado | LEAD | ❌ | GitHub PR aprobado |
| 1.4 | Sin comentarios pendientes en PR | DEV | ❌ | Resolver todos los threads |
| 1.5 | Linter/formatter pasados | DEV | ❌ | `black src/bot/` + `ruff check` |
| 1.6 | Sin warnings de seguridad | DEV | ❌ | `bandit -r src/bot/` |
| 1.7 | Dependencias actualizadas | DEV | ❌ | `pip list --outdated` |
| 1.8 | Sin TODOs críticos en código | DEV | ❌ | `grep -r "TODO:" src/bot/` |

**Comandos de verificación:**
```bash
# Ejecutar todos los checks
python -m pytest tests/bot/ -v --cov=src/bot --cov-report=term-missing
black --check src/bot/
ruff check src/bot/
bandit -r src/bot/
grep -r "TODO:" src/bot/ | grep -i "critical\|urgent"
```

---

### 📦 Staging Testing

| # | Tarea | Responsable | Status | Notas |
|---|-------|-------------|--------|-------|
| 2.1 | ⚠️ Deployment a staging exitoso | OPS | ❌ | `./scripts/deploy_bot.sh -e staging` |
| 2.2 | ⚠️ Bot funcional en staging > 24h | QA | ❌ | Sin crashes |
| 2.3 | Comando /start testeado | QA | ❌ | Responde correctamente |
| 2.4 | Crear tarea (wizard completo) | QA | ❌ | Wizard de 6 pasos OK |
| 2.5 | Finalizar tarea testeada | QA | ❌ | Lista + selección + confirmación |
| 2.6 | Cancelar tarea testeado | QA | ❌ | Comando /cancelar funciona |
| 2.7 | Usuarios no autorizados bloqueados | QA | ❌ | Whitelist funcionando |
| 2.8 | Manejo de errores validado | QA | ❌ | Mensajes amigables |
| 2.9 | Performance aceptable | QA | ❌ | Respuestas < 2s |
| 2.10 | Logs sin errores críticos | OPS | ❌ | `docker logs gad_bot_staging` |

**Test Cases Críticos:**

```bash
# TC-001: Happy path - Crear tarea completa
- /start → "📋 Crear Tarea" → Completar 6 pasos → Verificar éxito

# TC-002: Cancelar wizard a mitad
- /start → "📋 Crear Tarea" → Paso 3 → /cancelar → Verificar vuelta a menú

# TC-003: Usuario no autorizado
- Usar cuenta NO en whitelist → /start → Verificar mensaje de no autorizado

# TC-004: Manejo de errores API
- Simular API down → Intentar crear tarea → Verificar mensaje de error amigable

# TC-005: Finalizar tarea sin tareas pendientes
- /start → "✅ Finalizar Tarea" → Verificar mensaje "no hay tareas"
```

---

### 🔐 Seguridad

| # | Tarea | Responsable | Status | Notas |
|---|-------|-------------|--------|-------|
| 3.1 | ⚠️ Telegram Token rotado (si aplica) | OPS | ❌ | Nuevo token de @BotFather |
| 3.2 | ⚠️ SECRET_KEY generado aleatorio | OPS | ❌ | 32+ caracteres, no compartido |
| 3.3 | ⚠️ Whitelist configurada correctamente | OPS | ❌ | Solo usuarios autorizados |
| 3.4 | Variables sensibles NO en Git | DEV | ❌ | `.env` en `.gitignore` |
| 3.5 | Permisos de archivos configurados | OPS | ❌ | `.env` con permisos 600 |
| 3.6 | Firewall configurado | OPS | ❌ | Solo puertos necesarios |
| 3.7 | SSL/TLS verificado | OPS | ❌ | HTTPS para API |
| 3.8 | Rate limiting configurado | DEV | ❌ | Evitar spam/abuse |

**Verificación de seguridad:**
```bash
# Verificar que .env no está en Git
git ls-files | grep .env || echo "✅ .env no está en Git"

# Verificar permisos de .env
ls -l /opt/grupogad/.env | grep "rw-------" && echo "✅ Permisos correctos"

# Test de rate limiting
# Enviar 20 mensajes rápidos al bot y verificar que bloquea
```

---

### 🗄️ Base de Datos

| # | Tarea | Responsable | Status | Notas |
|---|-------|-------------|--------|-------|
| 4.1 | ⚠️ Backup completo realizado | OPS | ❌ | `./scripts/backup/backup_postgres.sh` |
| 4.2 | ⚠️ Backup verificado (restore test) | OPS | ❌ | Restore exitoso en staging |
| 4.3 | Migraciones testeadas en staging | DEV | ❌ | `alembic upgrade head` |
| 4.4 | Script de rollback listo | DEV | ❌ | `alembic downgrade -1` funciona |
| 4.5 | Espacio en disco suficiente | OPS | ❌ | > 20% libre |
| 4.6 | Índices optimizados | DEV | ❌ | Queries < 100ms |
| 4.7 | Conexiones DB configuradas | OPS | ❌ | Pool size adecuado |

**Comandos de verificación:**
```bash
# Realizar backup
./scripts/backup/backup_postgres.sh
ls -lh /opt/backups/*.sql.gz

# Test restore en staging
./scripts/backup/restore_postgres.sh /opt/backups/postgres_grupogad_YYYYMMDD.sql.gz

# Verificar espacio
df -h | grep /opt
```

---

### 🔔 Comunicación

| # | Tarea | Responsable | Status | Notas |
|---|-------|-------------|--------|-------|
| 5.1 | 🔔 Notificar a equipo de deployment | LEAD | ❌ | Email + Slack |
| 5.2 | 🔔 Notificar a usuarios finales | PO | ❌ | Si hay downtime |
| 5.3 | Ventana de mantenimiento agendada | OPS | ❌ | Fecha/hora definida |
| 5.4 | On-call engineer asignado | OPS | ❌ | Disponible durante deploy |
| 5.5 | Plan de rollback comunicado | LEAD | ❌ | Todos conocen el proceso |
| 5.6 | Incidentes pasados revisados | LEAD | ❌ | Evitar repetir errores |

**Template de notificación:**
```
ASUNTO: [DEPLOY] Bot de Telegram GRUPO_GAD - Producción
FECHA: DD/MM/YYYY
HORA: HH:MM (hora local)
DOWNTIME ESTIMADO: ~30 segundos
FEATURES NUEVAS: [Lista de features]
ROLLBACK PLAN: [Link al procedimiento]
ON-CALL: [Nombre + teléfono]
```

---

### 📄 Documentación

| # | Tarea | Responsable | Status | Notas |
|---|-------|-------------|--------|-------|
| 6.1 | README actualizado | DEV | ❌ | Instrucciones correctas |
| 6.2 | CHANGELOG actualizado | DEV | ❌ | v1.0.0 documentado |
| 6.3 | Deployment guide revisado | LEAD | ❌ | `DEPLOYMENT_GUIDE_BOT.md` |
| 6.4 | Variables de entorno documentadas | DEV | ❌ | `.env.example` completo |
| 6.5 | Troubleshooting guide actualizado | DEV | ❌ | Errores comunes |
| 6.6 | Runbook de producción creado | OPS | ❌ | Procedimientos operacionales |

---

## 🚀 FASE 2: DEPLOYMENT (Día D)

### ⏱️ Tiempo Estimado: 15-30 minutos

### 🔧 Preparación Inmediata

| # | Tarea | Responsable | Status | Hora | Notas |
|---|-------|-------------|--------|------|-------|
| 7.1 | ⚠️ Todos en llamada | LEAD | ❌ | - | Zoom/Meet link |
| 7.2 | ⚠️ Screen sharing activo | OPS | ❌ | - | Todos pueden ver |
| 7.3 | Logs en monitoreo en vivo | OPS | ❌ | - | Terminal abierto |
| 7.4 | Backup confirmado < 1h | OPS | ❌ | - | Timestamp verificado |
| 7.5 | Git tag creado | DEV | ❌ | - | `git tag v1.0.0` |

---

### 📦 Build & Push

| # | Tarea | Comando | Status | Hora | Notas |
|---|-------|---------|--------|------|-------|
| 8.1 | ⚠️ Build imagen Docker | `docker build -f docker/Dockerfile.bot -t gad-bot:v1.0.0 .` | ❌ | - | Sin errores |
| 8.2 | ⚠️ Tag imagen | `docker tag gad-bot:v1.0.0 registry.../gad-bot:v1.0.0` | ❌ | - | - |
| 8.3 | Push a registry | `docker push registry.../gad-bot:v1.0.0` | ❌ | - | Upload completo |
| 8.4 | Verificar imagen en registry | `docker pull registry.../gad-bot:v1.0.0` | ❌ | - | Pull exitoso |

**O usar script automatizado:**
```bash
./scripts/deploy_bot.sh -e production -t v1.0.0
```

---

### 🎯 Deployment a Producción

| # | Tarea | Comando | Status | Hora | Notas |
|---|-------|---------|--------|------|-------|
| 9.1 | SSH a servidor producción | `ssh deploy@api.grupogad.gob.ec` | ❌ | - | Conexión exitosa |
| 9.2 | Navegar a directorio | `cd /opt/grupogad` | ❌ | - | - |
| 9.3 | Pull imagen | `docker compose -f docker-compose.prod.yml pull bot` | ❌ | - | - |
| 9.4 | Tag imagen actual como "previous" | `docker tag ...bot:latest ...bot:previous` | ❌ | - | Para rollback |
| 9.5 | ⚠️ STOP bot (downtime inicia) | `docker compose -f docker-compose.prod.yml stop bot` | ❌ | XX:XX | Anotar hora |
| 9.6 | Remover contenedor viejo | `docker compose -f docker-compose.prod.yml rm -f bot` | ❌ | - | - |
| 9.7 | ⚠️ START bot nuevo | `docker compose -f docker-compose.prod.yml up -d bot` | ❌ | XX:XX | Anotar hora |
| 9.8 | Calcular downtime | - | ❌ | - | Meta: < 1 min |

---

## ✅ FASE 3: POST-DEPLOYMENT (Inmediato)

### 🔍 Verificación Inmediata (Primeros 5 min)

| # | Tarea | Comando | Status | Resultado | Notas |
|---|-------|---------|--------|-----------|-------|
| 10.1 | ⚠️ Contenedor corriendo | `docker ps \| grep gad_bot` | ❌ | - | STATUS: Up |
| 10.2 | ⚠️ Healthcheck OK | `docker inspect gad_bot_production \| grep Health` | ❌ | - | "healthy" |
| 10.3 | ⚠️ Logs sin errores | `docker logs --tail 50 gad_bot_production` | ❌ | - | Sin exceptions |
| 10.4 | ⚠️ Test /start en Telegram | Enviar `/start` al bot | ❌ | - | Responde OK |
| 10.5 | Test crear tarea | Wizard completo | ❌ | - | 6 pasos OK |
| 10.6 | Test finalizar tarea | Finalizar una tarea | ❌ | - | Funciona OK |
| 10.7 | Conectividad con API | Logs de API calls | ❌ | - | Sin timeouts |
| 10.8 | CPU/Memoria normal | `docker stats gad_bot_production` | ❌ | - | < 50% |

**Script de verificación rápida:**
```bash
# Ejecutar todas las verificaciones
./scripts/post_deployment_verification.sh

# O manualmente:
docker ps | grep gad_bot
docker logs --tail 50 gad_bot_production 2>&1 | grep -i "error" || echo "✅ No errors"
docker inspect gad_bot_production | grep -A2 Health
```

---

### 📊 Monitoreo Continuo (Primeros 30 min)

| # | Tarea | Frecuencia | Status | Notas |
|---|-------|------------|--------|-------|
| 11.1 | Monitorear logs | Cada 5 min | ❌ | Buscar anomalías |
| 11.2 | Verificar métricas | Cada 10 min | ❌ | CPU, Memoria, Red |
| 11.3 | Test funcional completo | Min 15 | ❌ | Todas las funcionalidades |
| 11.4 | Verificar alertas | Continuo | ❌ | No alertas disparadas |
| 11.5 | User feedback | Min 20 | ❌ | Preguntar a usuarios beta |

**Comandos de monitoreo:**
```bash
# Logs en tiempo real
docker logs -f gad_bot_production

# Métricas del contenedor
watch -n 5 'docker stats gad_bot_production --no-stream'

# Verificar procesos
docker exec gad_bot_production ps aux
```

---

### 🔔 Comunicación Post-Deploy

| # | Tarea | Responsable | Status | Hora | Notas |
|---|-------|-------------|--------|------|-------|
| 12.1 | 🔔 Notificar deployment exitoso | LEAD | ❌ | - | Email + Slack |
| 12.2 | 🔔 Actualizar status page | OPS | ❌ | - | "All systems operational" |
| 12.3 | Documentar tiempo real de downtime | OPS | ❌ | - | Para métricas |
| 12.4 | Documentar issues encontrados | DEV | ❌ | - | Para próximo deploy |
| 12.5 | Agradecer al equipo | LEAD | ❌ | - | 🎉 |

**Template de éxito:**
```
✅ DEPLOYMENT EXITOSO - Bot de Telegram GRUPO_GAD v1.0.0

Fecha: DD/MM/YYYY HH:MM
Downtime: XX segundos
Issues: Ninguno
Verificación: Todas pasaron ✅
Status: OPERACIONAL

Gracias al equipo por el excelente trabajo! 🎉
```

---

## 🔄 FASE 4: ROLLBACK (Solo si hay problemas)

### ⚠️ Criterios para Rollback Inmediato

Hacer rollback SI:
- ❌ Bot no responde después de 2 minutos
- ❌ Errores críticos en logs
- ❌ Comando /start no funciona
- ❌ Healthcheck falla 3+ veces
- ❌ CPU/Memoria > 90% sostenido
- ❌ API no accesible desde bot

### 🚨 Procedimiento de Rollback

| # | Tarea | Comando | Status | Hora | Notas |
|---|-------|---------|--------|------|-------|
| 13.1 | 🔔 ANUNCIAR ROLLBACK | Slack + Email | ❌ | - | Alertar al equipo |
| 13.2 | Stop bot fallido | `docker compose stop bot` | ❌ | - | - |
| 13.3 | Remover contenedor | `docker compose rm -f bot` | ❌ | - | - |
| 13.4 | Tag previous como latest | `docker tag ...bot:previous ...bot:latest` | ❌ | - | - |
| 13.5 | Start versión anterior | `docker compose up -d bot` | ❌ | - | - |
| 13.6 | Verificar rollback OK | Ver logs | ❌ | - | Bot funcional |
| 13.7 | 🔔 Confirmar rollback exitoso | Slack + Email | ❌ | - | - |
| 13.8 | Post-mortem meeting | Agendar | ❌ | - | Analizar qué pasó |

**Rollback rápido:**
```bash
./scripts/deploy_bot.sh -e production --rollback
```

---

## 📊 FASE 5: POST-DEPLOYMENT (24-48 horas)

### 📈 Monitoreo Extendido

| # | Tarea | Frecuencia | Status | Notas |
|---|-------|------------|--------|-------|
| 14.1 | Revisar logs diarios | 2x/día | ❌ | Mañana y noche |
| 14.2 | Verificar métricas | 1x/día | ❌ | CPU, memoria, latencia |
| 14.3 | User feedback | Continuo | ❌ | Support tickets |
| 14.4 | Performance baselines | Día 2 | ❌ | Documentar para futuro |
| 14.5 | Alertas de monitoreo | Continuo | ❌ | Ajustar si hay falsos + |

---

### 📝 Documentación Post-Deploy

| # | Tarea | Responsable | Status | Notas |
|---|-------|-------------|--------|-------|
| 15.1 | Actualizar CHANGELOG | DEV | ❌ | Documentar v1.0.0 |
| 15.2 | Deployment report | LEAD | ❌ | Tiempo, issues, métricas |
| 15.3 | Lessons learned | LEAD | ❌ | Qué mejorar para próximo |
| 15.4 | Actualizar runbook | OPS | ❌ | Con aprendizajes |
| 15.5 | Cerrar issues/PRs | DEV | ❌ | GitHub cleanup |
| 15.6 | Celebrar 🎉 | TODOS | ❌ | Equipo merece reconocimiento |

---

## 📞 Contactos de Emergencia

### Durante Deployment

| Rol | Nombre | Teléfono | Slack |
|-----|--------|----------|-------|
| **Lead Developer** | - | +593-XXX-XXXX | @lead |
| **DevOps** | - | +593-XXX-XXXX | @devops |
| **On-Call Engineer** | - | +593-XXX-XXXX | @oncall |
| **Product Owner** | - | +593-XXX-XXXX | @po |

### Escalación

1. **Nivel 1 (0-15 min):** Dev intenta fix
2. **Nivel 2 (15-30 min):** Lead toma decisión de rollback
3. **Nivel 3 (30+ min):** CTO notificado, post-mortem

---

## 📚 Referencias

- [Deployment Guide Completo](./DEPLOYMENT_GUIDE_BOT.md)
- [Code Review Report](../CODE_REVIEW_REPORT.md)
- [Testing Manual](./TESTING_MANUAL_COMPLETO.md)
- [Troubleshooting Guide](./DEPLOYMENT_GUIDE_BOT.md#troubleshooting)

---

## 🎓 Lecciones Aprendidas (Actualizar después de cada deploy)

### Deploy v1.0.0 (DD/MM/YYYY)

**Lo que salió bien:**
- [ ] Item 1
- [ ] Item 2

**Lo que mejorar:**
- [ ] Item 1
- [ ] Item 2

**Tiempo real vs estimado:**
- Estimado: 30 min
- Real: XX min
- Downtime: XX seg

**Issues encontrados:**
- [ ] Issue 1 + solución
- [ ] Issue 2 + solución

---

## ✅ Firma de Aprobación

**Este deployment fue:**

- [ ] ✅ **EXITOSO** - Todos los checks pasaron
- [ ] 🔄 **ROLLBACK** - Se revirtió por: _____________________
- [ ] ⏸️ **CANCELADO** - Razón: _____________________

**Firmado por:**

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| Developer | - | - | - |
| Tech Lead | - | - | - |
| DevOps | - | - | - |

---

**Última actualización:** 11 de octubre de 2025  
**Versión del documento:** 1.0  
**Mantenedor:** Equipo GRUPO_GAD

---

## 🔖 Apéndice: Scripts Útiles

### Script de Verificación Rápida

```bash
#!/bin/bash
# quick_verify.sh - Verificación post-deploy en 1 minuto

echo "🔍 Verificando deployment..."

# 1. Contenedor corriendo
if docker ps | grep -q gad_bot_production; then
    echo "✅ Contenedor corriendo"
else
    echo "❌ Contenedor NO está corriendo"
    exit 1
fi

# 2. Healthcheck
HEALTH=$(docker inspect gad_bot_production | grep -o '"Status":"[^"]*"' | head -1)
if [[ $HEALTH == *"healthy"* ]]; then
    echo "✅ Healthcheck OK"
else
    echo "❌ Healthcheck FAIL: $HEALTH"
    exit 1
fi

# 3. Sin errores en logs
ERRORS=$(docker logs --tail 100 gad_bot_production 2>&1 | grep -c -i "error\|exception")
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ Sin errores en logs"
else
    echo "⚠️ $ERRORS errores encontrados en logs"
fi

# 4. CPU/Memoria
STATS=$(docker stats gad_bot_production --no-stream --format "{{.CPUPerc}} {{.MemPerc}}")
echo "📊 Recursos: CPU/MEM: $STATS"

echo ""
echo "✅ Verificación completada"
```

### Script de Rollback Rápido

```bash
#!/bin/bash
# quick_rollback.sh - Rollback en 30 segundos

echo "🚨 INICIANDO ROLLBACK..."

cd /opt/grupogad

docker compose -f docker-compose.prod.yml stop bot
docker compose -f docker-compose.prod.yml rm -f bot
docker tag registry.grupogad.gob.ec/gad-bot:previous registry.grupogad.gob.ec/gad-bot:latest
docker compose -f docker-compose.prod.yml up -d bot

echo "✅ Rollback completado - verificar logs"
docker logs --tail 20 gad_bot_production
```

---

**🎉 ¡Buen deployment!**
