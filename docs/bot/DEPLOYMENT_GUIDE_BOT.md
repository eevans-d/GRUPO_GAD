# 🚀 Guía de Deployment - Bot de Telegram GRUPO_GAD

## 📋 Información del Documento

**Fecha de creación:** 11 de octubre de 2025  
**Versión del Bot:** 1.0.0  
**Autor:** Equipo de Desarrollo GRUPO_GAD  
**Última actualización:** Post-merge master

---

## 🎯 Objetivo

Esta guía proporciona instrucciones paso a paso para deployar el Bot de Telegram en diferentes entornos (development, staging, production).

---

## 📊 Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Entornos de Deployment](#entornos-de-deployment)
3. [Preparación Inicial](#preparación-inicial)
4. [Deployment Local (Development)](#deployment-local-development)
5. [Deployment a Staging](#deployment-a-staging)
6. [Deployment a Producción](#deployment-a-producción)
7. [Verificación Post-Deploy](#verificación-post-deploy)
8. [Rollback](#rollback)
9. [Troubleshooting](#troubleshooting)
10. [Monitoreo](#monitoreo)

---

## 🔧 Pre-requisitos

### Software Requerido

| Herramienta | Versión Mínima | Comando de Verificación |
|-------------|----------------|-------------------------|
| **Docker** | 20.10+ | `docker --version` |
| **Docker Compose** | 2.0+ | `docker compose version` |
| **Python** | 3.11+ | `python --version` |
| **Git** | 2.30+ | `git --version` |
| **pytest** | 7.0+ | `pytest --version` |

### Accesos Necesarios

- ✅ Token de bot de Telegram (de @BotFather)
- ✅ Admin Chat ID (tu Telegram ID)
- ✅ Acceso al servidor de producción (SSH)
- ✅ Credenciales de Docker Registry (staging/prod)
- ✅ Variables de entorno configuradas

### Verificar Pre-requisitos

```bash
# Script de verificación rápida
./scripts/deploy_bot.sh --help

# O manualmente:
docker --version
docker compose version
python --version
pytest --version
```

---

## 🌍 Entornos de Deployment

### Development (Local)

- **Propósito:** Desarrollo y testing local
- **URL:** `localhost`
- **Base de datos:** SQLite en memoria o PostgreSQL local
- **Método:** Docker Compose
- **Logs:** `docker logs gad_bot_dev`

### Staging

- **Propósito:** Testing pre-producción
- **URL:** `staging.grupogad.gob.ec`
- **Base de datos:** PostgreSQL (instancia dedicada)
- **Método:** Docker Compose en servidor staging
- **Logs:** `/var/log/gad/bot-staging.log`

### Production

- **Propósito:** Servicio en vivo para usuarios finales
- **URL:** `api.grupogad.gob.ec`
- **Base de datos:** PostgreSQL (cluster replicado)
- **Método:** Docker Compose + restart policies
- **Logs:** `/var/log/gad/bot-production.log`
- **Monitoring:** Prometheus + Grafana

---

## 📝 Preparación Inicial

### 1. Clonar Repositorio

```bash
# SSH (recomendado)
git clone git@github.com:eevans-d/GRUPO_GAD.git
cd GRUPO_GAD

# HTTPS
git clone https://github.com/eevans-d/GRUPO_GAD.git
cd GRUPO_GAD
```

### 2. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar con tus valores
nano .env
# o
vim .env
# o
code .env
```

**Variables críticas para el Bot:**

```bash
# Telegram Configuration
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_CHAT_ID=123456789
WHITELIST_IDS='[123456789, 987654321]'

# API Configuration
API_V1_STR=/api/v1
SECRET_KEY=CHANGEME_RANDOM_SECRET_KEY_MIN_32_CHARS

# Database (si el bot necesita acceso directo)
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/grupo_gad

# Environment
ENVIRONMENT=development  # development | staging | production
LOG_LEVEL=INFO
```

**Generar SECRET_KEY seguro:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Validar Configuración

```bash
# Ejecutar script de validación
python scripts/validate_config.py

# O validar manualmente
python -c "from config.settings import settings; print('Token:', settings.TELEGRAM_TOKEN[:10] if settings.TELEGRAM_TOKEN else 'NOT SET')"
```

**Output esperado:**
```
✅ TELEGRAM_TOKEN: 123456:ABC...
✅ ADMIN_CHAT_ID: 123456789
✅ WHITELIST_IDS: 2 usuarios autorizados
✅ DATABASE_URL: ...@db:5432/grupo_gad
✅ SECRET_KEY: 43 caracteres
✅ Configuración válida!
```

### 4. Ejecutar Tests

**IMPORTANTE:** Siempre ejecutar tests antes de deploy.

```bash
# Tests del bot solamente
python -m pytest tests/bot/ -v

# Tests con cobertura
python -m pytest tests/bot/ --cov=src/bot --cov-report=term-missing

# Tests rápidos (sin output verbose)
python -m pytest tests/bot/ -q
```

**Resultado esperado:**
```
tests/bot/test_keyboards.py .......                  [ 17%]
tests/bot/test_callback_handler.py ......            [ 32%]
tests/bot/test_start_command.py ..                   [ 37%]
tests/bot/test_wizard_multistep.py ..............    [ 73%]
tests/bot/test_finalizar_tarea.py ..........         [100%]

============== 39 passed in 2.45s ==============
```

---

## 💻 Deployment Local (Development)

### Método 1: Script Automatizado (Recomendado)

```bash
# Deployment completo con tests
./scripts/deploy_bot.sh -e development

# Deployment sin tests (desarrollo iterativo)
./scripts/deploy_bot.sh -e development --skip-tests
```

**Output esperado:**
```
============================================
DEPLOYMENT - Bot de Telegram GRUPO_GAD
============================================

▶ Validando entorno de deployment...
✓ Entorno: development
▶ Verificando pre-requisitos...
✓ Docker instalado: Docker version 24.0.5
✓ Archivo .env encontrado
✓ Variables críticas configuradas
▶ Ejecutando tests del bot...
✓ Todos los tests pasaron
▶ Construyendo imagen Docker...
✓ Imagen construida: gad-bot:latest
▶ Desplegando bot a development...
✓ Bot desplegado localmente
▶ Verificando deployment...
✓ Contenedor bot está corriendo
✓ Deployment verificado correctamente

============================================
DEPLOYMENT COMPLETADO EXITOSAMENTE
============================================
✓ Bot desplegado en development
✓ Imagen: gad-bot:latest

Comandos útiles:
  - Ver logs: docker logs -f gad_bot_dev
  - Detener bot: docker compose stop bot
  - Rollback: ./scripts/deploy_bot.sh -e development --rollback
```

### Método 2: Docker Compose Manual

```bash
# 1. Build de la imagen
docker compose build bot

# 2. Start del servicio
docker compose up -d bot

# 3. Ver logs
docker compose logs -f bot
```

### Verificar Deployment Local

```bash
# 1. Verificar contenedor corriendo
docker ps | grep bot

# 2. Ver logs en tiempo real
docker logs -f gad_bot_dev

# 3. Probar el bot en Telegram
# - Abre Telegram
# - Busca tu bot (@tubot)
# - Envía /start
# - Deberías ver el menú principal
```

---

## 🧪 Deployment a Staging

### Pre-requisitos Adicionales

- ✅ Acceso SSH al servidor staging
- ✅ Docker registry configurado
- ✅ Credenciales de registry
- ✅ DNS configurado para staging

### Paso 1: Preparar Imagen

```bash
# Autenticarse en registry
docker login registry.grupogad.gob.ec

# Build y tag
./scripts/deploy_bot.sh -e staging

# O manualmente:
docker build -f docker/Dockerfile.bot -t registry.grupogad.gob.ec/gad-bot:staging .
docker push registry.grupogad.gob.ec/gad-bot:staging
```

### Paso 2: Conectar al Servidor Staging

```bash
# SSH al servidor
ssh deploy@staging.grupogad.gob.ec

# Navegar al directorio del proyecto
cd /opt/grupogad
```

### Paso 3: Deploy en Servidor

```bash
# Pull de la imagen actualizada
docker compose -f docker-compose.yml pull bot

# Detener versión anterior
docker compose -f docker-compose.yml stop bot
docker compose -f docker-compose.yml rm -f bot

# Iniciar nueva versión
docker compose -f docker-compose.yml up -d bot

# Verificar
docker compose -f docker-compose.yml ps bot
docker compose -f docker-compose.yml logs -f bot
```

### Verificación en Staging

```bash
# En el servidor staging
docker logs --tail 50 gad_bot_staging

# Verificar conectividad
curl -I http://localhost:8000/health  # API health check

# Test manual del bot
# - Abre Telegram
# - Busca @grupogad_staging_bot
# - Envía /start
```

---

## 🏭 Deployment a Producción

### ⚠️ IMPORTANTE - Checklist Pre-Producción

**Antes de deployar a producción, DEBES:**

- [ ] ✅ Todos los tests pasan (39/39)
- [ ] ✅ Code review completado y aprobado
- [ ] ✅ Deployment a staging exitoso
- [ ] ✅ Testing manual en staging completado
- [ ] ✅ Backups de base de datos realizados
- [ ] ✅ Variables de entorno de producción validadas
- [ ] ✅ Notificación al equipo sobre deployment
- [ ] ✅ Plan de rollback documentado
- [ ] ✅ Monitoreo y alertas configuradas

**Ver checklist completo:** `docs/bot/CHECKLIST_PRODUCCION_BOT.md`

### Paso 1: Preparar Release

```bash
# 1. Crear tag de versión
git tag -a v1.0.0 -m "Release v1.0.0 - Bot con botones interactivos"
git push origin v1.0.0

# 2. Build imagen de producción con tag
IMAGE_TAG=v1.0.0 ./scripts/deploy_bot.sh -e production

# O manualmente:
docker build \
    -f docker/Dockerfile.bot \
    -t registry.grupogad.gob.ec/gad-bot:v1.0.0 \
    -t registry.grupogad.gob.ec/gad-bot:latest \
    .

docker push registry.grupogad.gob.ec/gad-bot:v1.0.0
docker push registry.grupogad.gob.ec/gad-bot:latest
```

### Paso 2: Backup Pre-Deploy

```bash
# En servidor de producción
ssh deploy@api.grupogad.gob.ec

# Backup de base de datos
./scripts/backup/backup_postgres.sh

# Backup de configuración
tar -czf /opt/backups/config-$(date +%Y%m%d-%H%M%S).tar.gz \
    /opt/grupogad/.env \
    /opt/grupogad/docker-compose.prod.yml

# Verificar backups
ls -lh /opt/backups/
```

### Paso 3: Deploy a Producción

```bash
# En servidor de producción
cd /opt/grupogad

# Pull imagen
docker compose -f docker-compose.prod.yml pull bot

# Tag imagen actual como "previous" (para rollback)
docker tag registry.grupogad.gob.ec/gad-bot:latest \
    registry.grupogad.gob.ec/gad-bot:previous

# Stop del bot actual (downtime starts)
docker compose -f docker-compose.prod.yml stop bot

# Remover contenedor
docker compose -f docker-compose.prod.yml rm -f bot

# Start nueva versión
docker compose -f docker-compose.prod.yml up -d bot

# Verificar inmediatamente
docker compose -f docker-compose.prod.yml ps bot
docker compose -f docker-compose.prod.yml logs --tail 50 bot
```

**Downtime esperado:** < 30 segundos

### Paso 4: Verificación Post-Deploy

Ver sección [Verificación Post-Deploy](#verificación-post-deploy)

---

## ✅ Verificación Post-Deploy

### Checklist de Verificación

Ejecutar **TODOS** estos checks después de cualquier deployment:

```bash
# 1. Verificar contenedor corriendo
docker ps | grep gad_bot

# 2. Verificar logs sin errores
docker logs --tail 100 gad_bot_production 2>&1 | grep -i "error\|exception" || echo "No errors found"

# 3. Verificar healthcheck
docker inspect gad_bot_production | grep -A5 Health

# 4. Test funcional: /start
# - Abre Telegram
# - Envía /start al bot
# - Verifica que responde con menú

# 5. Test funcional: Crear tarea
# - Click en "📋 Crear Tarea"
# - Completa wizard hasta el final
# - Verifica que no hay errores

# 6. Test funcional: Finalizar tarea
# - Click en "✅ Finalizar Tarea"
# - Verifica que lista se muestra
# - Selecciona una tarea
# - Confirma finalización

# 7. Verificar métricas (si aplica)
curl -s http://localhost:9090/metrics | grep bot_

# 8. Verificar conectividad con API
docker logs gad_bot_production 2>&1 | grep "API" | tail -20
```

### Script de Verificación Automatizada

```bash
# Ejecutar script post-deployment
./scripts/post_deployment_verification.sh

# O usar el flag del script de deploy
./scripts/deploy_bot.sh -e production --verify
```

**Output esperado:**
```
✅ Contenedor corriendo
✅ Healthcheck: healthy
✅ Sin errores en logs (últimos 100 líneas)
✅ Comando /start funcional
✅ API accesible
✅ Métricas disponibles

Verificación POST-DEPLOY: EXITOSA ✓
```

---

## 🔄 Rollback

### Cuándo Hacer Rollback

Hacer rollback inmediato si:
- ❌ Bot no responde después de 2 minutos
- ❌ Errores críticos en logs
- ❌ Comando /start no funciona
- ❌ Wizard de creación crashea
- ❌ API no accesible desde bot
- ❌ Healthcheck falla consistentemente

### Rollback Rápido

```bash
# Método 1: Script automatizado (30 segundos)
./scripts/deploy_bot.sh -e production --rollback

# Método 2: Manual (1 minuto)
cd /opt/grupogad

# Detener versión fallida
docker compose -f docker-compose.prod.yml stop bot
docker compose -f docker-compose.prod.yml rm -f bot

# Restaurar versión anterior
docker tag registry.grupogad.gob.ec/gad-bot:previous \
    registry.grupogad.gob.ec/gad-bot:latest

# Reiniciar con versión anterior
docker compose -f docker-compose.prod.yml up -d bot

# Verificar
docker logs -f gad_bot_production
```

### Rollback de Base de Datos

Si se hicieron migraciones incompatibles:

```bash
# Restaurar backup de base de datos
./scripts/backup/restore_postgres.sh /opt/backups/postgres_grupogad_YYYYMMDD.sql.gz

# Verificar integridad
docker exec gad_db_prod psql -U gad_user -d grupo_gad_prod -c "\dt"
```

### Comunicación de Rollback

```bash
# Notificar al equipo
echo "ROLLBACK realizado en producción. Versión revertida a previous." | \
    mail -s "[URGENTE] Rollback Bot GRUPO_GAD" team@grupogad.gob.ec

# Crear issue en GitHub
gh issue create \
    --title "Rollback Production - Bot v1.0.0" \
    --body "Deployment falló, rollback realizado a previous version"
```

---

## 🐛 Troubleshooting

### Bot No Inicia

**Síntoma:** Contenedor se detiene inmediatamente después de start.

**Diagnóstico:**
```bash
# Ver logs completos
docker logs gad_bot_production

# Ver exit code
docker inspect gad_bot_production | grep ExitCode
```

**Causas comunes:**
1. **Token inválido:**
   - Verificar `TELEGRAM_TOKEN` en `.env`
   - Probar token con curl: `curl https://api.telegram.org/bot<TOKEN>/getMe`

2. **Variables faltantes:**
   - Verificar todas las variables críticas
   - Ejecutar: `python -c "from config.settings import settings; print(settings.model_dump())"`

3. **Error de importación:**
   - Verificar que todas las dependencias están instaladas
   - Revisar `docker/requirements.bot.txt`

**Solución:**
```bash
# Reconstruir imagen limpia
docker compose build --no-cache bot
docker compose up -d bot
```

### Bot No Responde en Telegram

**Síntoma:** Bot aparece online pero no responde a mensajes.

**Diagnóstico:**
```bash
# Verificar que está escuchando
docker logs gad_bot_production | grep "iniciado\|listening"

# Verificar conexión a Telegram API
docker exec gad_bot_production curl -I https://api.telegram.org

# Verificar whitelist
docker logs gad_bot_production | grep "unauthorized\|whitelist"
```

**Causas comunes:**
1. **Usuario no en whitelist:**
   - Verificar `WHITELIST_IDS` en `.env`
   - Añadir tu Telegram ID: `WHITELIST_IDS='[123456789]'`

2. **Firewall bloqueando:**
   - Verificar firewall del servidor
   - Permitir conexiones salientes a api.telegram.org

3. **Polling no iniciado:**
   - Verificar que `Application.run_polling()` se está llamando

**Solución:**
```bash
# Añadir usuario a whitelist
echo "WHITELIST_IDS='[123456789, TU_ID_AQUI]'" >> .env

# Reiniciar bot
docker compose restart bot
```

### Wizard Se Traba en un Paso

**Síntoma:** Usuario queda stuck en paso X del wizard.

**Diagnóstico:**
```bash
# Ver estado de context
docker logs gad_bot_production | grep "wizard" | tail -20

# Ver errores de validación
docker logs gad_bot_production | grep "validation\|error" | tail -20
```

**Causas comunes:**
1. **Validación falla silenciosamente**
2. **State corrupto en `context.user_data`**
3. **Handler no registrado correctamente**

**Solución:**
```bash
# Usuario puede cancelar wizard y reiniciar
# Enviar /start en Telegram

# Si persiste, limpiar state (requiere acceso a DB)
docker exec gad_db_prod psql -U gad_user -d grupo_gad_prod \
    -c "DELETE FROM bot_user_states WHERE telegram_id = 123456789;"
```

### API No Accesible Desde Bot

**Síntoma:** Bot reporta errores de conexión a API.

**Diagnóstico:**
```bash
# Verificar API corriendo
docker ps | grep gad_api

# Test conexión desde bot
docker exec gad_bot_production curl -I http://api:8000/health

# Ver errores de conexión
docker logs gad_bot_production | grep "connection\|timeout" | tail -20
```

**Causas comunes:**
1. **API no está corriendo**
2. **Network configuration incorrecta**
3. **Timeout muy bajo**

**Solución:**
```bash
# Verificar red de Docker
docker network inspect gad-network

# Asegurar que bot y API están en misma red
docker compose up -d api bot

# Ajustar timeout en config
# Editar config/settings.py: HTTP_TIMEOUT = 30
```

### Errores Comunes y Soluciones Rápidas

| Error | Causa | Solución |
|-------|-------|----------|
| `ModuleNotFoundError` | Dependencia faltante | `pip install -r docker/requirements.bot.txt` |
| `Unauthorized` | Token inválido | Verificar `TELEGRAM_TOKEN` en .env |
| `Database connection failed` | DB no disponible | Verificar que servicio `db` está corriendo |
| `Permission denied` | Usuario sin permisos | Verificar `WHITELIST_IDS` |
| `Timeout` | API lenta | Aumentar `HTTP_TIMEOUT` |

---

## 📊 Monitoreo

### Logs en Tiempo Real

```bash
# Development
docker logs -f gad_bot_dev

# Production
docker logs -f gad_bot_production --tail 100

# Filtrar errores
docker logs gad_bot_production 2>&1 | grep -i "error\|exception"
```

### Métricas Clave

Monitorear estas métricas en producción:

1. **Disponibilidad:**
   - Uptime del contenedor: `docker inspect gad_bot_production | grep Running`
   - Healthcheck status: `docker inspect gad_bot_production | grep Health`

2. **Performance:**
   - Tiempo de respuesta promedio de comandos
   - Latencia de API calls

3. **Errores:**
   - Count de excepciones por hora
   - Rate de comandos fallidos

4. **Uso:**
   - Mensajes procesados por día
   - Usuarios activos (únicos por día)
   - Comandos más usados

### Alertas Recomendadas

Configurar alertas para:
- ⚠️ Bot down por > 2 minutos
- ⚠️ Tasa de error > 5%
- ⚠️ Healthcheck falla 3 veces consecutivas
- ⚠️ CPU > 80% por > 5 minutos
- ⚠️ Memoria > 90%

### Dashboards

Ver dashboards en Grafana (si configurado):
- **Bot Health:** `/dashboards/bot-health`
- **Bot Usage:** `/dashboards/bot-usage`
- **Bot Errors:** `/dashboards/bot-errors`

---

## 📞 Soporte y Contacto

### Documentación Relacionada

- [Configuración de Entorno](./bot/CONFIGURACION_ENTORNO.md)
- [Testing Manual](./bot/TESTING_MANUAL_COMPLETO.md)
- [Checklist de Producción](./bot/CHECKLIST_PRODUCCION_BOT.md)
- [Code Review Report](./CODE_REVIEW_REPORT.md)

### Contacto de Emergencia

- **Equipo de Desarrollo:** dev@grupogad.gob.ec
- **On-call (24/7):** +593-XXX-XXXX
- **Slack:** #grupo-gad-alerts
- **GitHub Issues:** https://github.com/eevans-d/GRUPO_GAD/issues

### Procedimiento de Escalamiento

1. **Nivel 1 (Dev):** Revisar logs, intentar fix rápido
2. **Nivel 2 (Lead):** Si no se resuelve en 15 min, escalar
3. **Nivel 3 (CTO):** Incidentes críticos de producción

---

## 📝 Changelog de Deployments

### v1.0.0 (11/10/2025)
- ✅ Release inicial del bot con botones interactivos
- ✅ Fases 1-3 implementadas y testeadas
- ✅ 39 tests automatizados pasando
- ✅ Documentación completa

### v0.9.0 (DD/MM/2025)
- Pre-release candidate
- Testing en staging

---

**Última actualización:** 11 de octubre de 2025  
**Mantenedor:** Equipo GRUPO_GAD  
**Versión del documento:** 1.0
