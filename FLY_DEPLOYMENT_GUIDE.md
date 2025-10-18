# 🚀 FLY.IO DEPLOYMENT GUIDE - GRUPO_GAD

**Plataforma**: Fly.io  
**Fecha**: 18 Octubre 2025  
**Tiempo estimado**: 30-40 minutos  
**Costo**: $0-15/mes (Free tier generoso)  

---

## 📋 TABLA DE CONTENIDOS

1. [¿Por qué Fly.io?](#why-flyio)
2. [Pre-requisitos](#prerequisites)
3. [Setup Inicial (10 min)](#initial-setup)
4. [Configuración de Secrets (15 min)](#secrets-config)
5. [Deploy de Base de Datos (5 min)](#database-setup)
6. [Deploy de Redis (5 min)](#redis-setup)
7. [Deploy de la Aplicación (10 min)](#app-deploy)
8. [Verificación y Testing (5 min)](#verification)
9. [Troubleshooting](#troubleshooting)
10. [Comandos Útiles](#useful-commands)

---

## 🎯 ¿POR QUÉ FLY.IO? {#why-flyio}

### Ventajas vs Otras Plataformas

| Feature | Fly.io | Railway | Heroku | AWS |
|---------|--------|---------|--------|-----|
| **Edge Computing** | ✅ Global | ❌ US-only | ❌ US-EU | ✅ Manual |
| **Free Tier** | ✅ $5/mes | ✅ $5/mes | ❌ $0 | ❌ Complejo |
| **PostgreSQL** | ✅ Incluido | ✅ Incluido | ❌ Addon | ❌ RDS |
| **Redis** | ✅ Upstash | ⚠️ Limitado | ❌ Addon | ❌ ElastiCache |
| **WebSockets** | ✅ Nativo | ✅ Nativo | ⚠️ Limitado | ✅ Manual |
| **Scaling** | ✅ Auto | ⚠️ Manual | ❌ Paid | ✅ Manual |
| **Deployment** | ✅ < 2 min | ✅ < 3 min | ⚠️ 5 min | ❌ 10+ min |

### Arquitectura Fly.io

```
Usuario (Lima)
    ↓
Fly Edge (mia - Miami) ← Solo 200ms latencia
    ↓
GRUPO_GAD App
    ├─ PostgreSQL (attached)
    ├─ Redis (Upstash)
    └─ WebSocket Manager
```

### Pricing

```
FREE TIER (suficiente para desarrollo):
├─ 3 shared-cpu-1x VMs
├─ 3 GB persistent storage
├─ 160 GB outbound data transfer
└─ PostgreSQL: hasta 3 GB

PRODUCTION (estimado $10-15/mes):
├─ 2x shared-cpu-1x (512 MB) @ $5/cada
├─ PostgreSQL 10 GB @ $3
├─ Redis Upstash @ gratis (10K requests/day)
└─ Bandwidth @ incluido
───────────────────────────
TOTAL: ~$13/mes
```

---

## ✅ PRE-REQUISITOS {#prerequisites}

### 1. Cuenta Fly.io
```bash
# Crear cuenta (gratis)
open https://fly.io/app/sign-up

# Verifica email
# Agrega tarjeta de crédito (no se cobra sin exceder free tier)
```

### 2. Instalar flyctl CLI
```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Verificar instalación
flyctl version
```

### 3. Login
```bash
flyctl auth login
# Abre browser para autenticar
```

### 4. Secrets Preparados
Debes tener listos los 8 secrets críticos de `MY_DEPLOYMENT_SECRETS.md`:
- ✅ SECRET_KEY
- ✅ POSTGRES_USER
- ✅ POSTGRES_PASSWORD
- ✅ POSTGRES_DB
- ⚠️ DATABASE_URL (se genera automáticamente)
- ⚠️ REDIS_URL (se provisiona después)

---

## 🚀 SETUP INICIAL (10 min) {#initial-setup}

### Paso 1: Clonar y Preparar Proyecto
```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD

# Verificar archivos críticos
ls -la fly.toml Dockerfile .dockerignore
# Deberían existir todos
```

### Paso 2: Inicializar App en Fly.io
```bash
# Launch app (interactivo)
flyctl launch

# Responde:
# ✅ App name: grupo-gad (o personalizado)
# ✅ Region: mia (Miami) - Closest to LATAM
# ❌ PostgreSQL: NO (lo crearemos después con más control)
# ❌ Redis: NO (usaremos Upstash)
# ✅ Deploy now: NO (primero configuramos secrets)
```

Esto crea/actualiza `fly.toml` con tu app name.

### Paso 3: Verificar fly.toml
```bash
cat fly.toml

# Deberías ver:
# app = "grupo-gad"  (o tu nombre)
# primary_region = "mia"
# [env] con variables
```

---

## 🔐 CONFIGURACIÓN DE SECRETS (15 min) {#secrets-config}

### Secrets en Fly.io

Fly.io maneja secrets de forma segura con `flyctl secrets set`.

### Paso 1: Agregar Secrets Base
```bash
# SECRET_KEY (de MY_DEPLOYMENT_SECRETS.md)
flyctl secrets set SECRET_KEY=1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d

# PostgreSQL credentials (temporales, se actualizan después)
flyctl secrets set POSTGRES_USER=gcp_user
flyctl secrets set POSTGRES_PASSWORD=E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=
flyctl secrets set POSTGRES_DB=gcp_db

# Environment
flyctl secrets set ENVIRONMENT=production
flyctl secrets set DEBUG=false
```

### Paso 2: Verificar Secrets
```bash
flyctl secrets list

# Output:
# NAME                | DIGEST                          | CREATED AT
# SECRET_KEY          | abc123...                       | 1m ago
# POSTGRES_USER       | def456...                       | 1m ago
# POSTGRES_PASSWORD   | ghi789...                       | 1m ago
# ...
```

### Paso 3: Secrets Avanzados (Opcional)
```bash
# CORS origins (si tienes dominio custom)
flyctl secrets set CORS_ORIGINS='["https://tu-dominio.com"]'

# Logging
flyctl secrets set LOG_LEVEL=info

# Workers
flyctl secrets set WORKERS=1
```

---

## 🗄️ DEPLOY DE BASE DE DATOS (5 min) {#database-setup}

### Fly Postgres (Managed)

Fly.io ofrece PostgreSQL gestionado con backups automáticos.

### Paso 1: Crear Cluster PostgreSQL
```bash
# Crear cluster
flyctl postgres create \
  --name grupo-gad-db \
  --region mia \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 10

# Output esperado:
# Creating postgres cluster grupo-gad-db in organization personal
# ✓ Successfully created postgres cluster grupo-gad-db
#   Username:    postgres
#   Password:    [auto-generated]
#   Hostname:    grupo-gad-db.internal
#   Proxy port:  5432
#   Postgres port: 5433
```

### Paso 2: Attach a la App
```bash
# Conectar DB a tu app
flyctl postgres attach grupo-gad-db --app grupo-gad

# Esto automáticamente:
# ✅ Crea secret DATABASE_URL
# ✅ Configura conexión privada
# ✅ Habilita backups
```

### Paso 3: Verificar DATABASE_URL
```bash
flyctl secrets list | grep DATABASE_URL

# Deberías ver algo como:
# DATABASE_URL  | xyz789...  | 30s ago
```

### Paso 4: (Opcional) Acceso Remoto
```bash
# Proxy para acceso local (desarrollo)
flyctl proxy 5432 -a grupo-gad-db

# En otra terminal, conecta con psql:
psql postgresql://postgres:[PASSWORD]@localhost:5432/grupo_gad
```

### Paso 5: Ejecutar Migraciones Iniciales
```bash
# Las migraciones se ejecutan automáticamente en deploy
# (definido en fly.toml: release_command = "alembic upgrade head")
```

---

## 🔴 DEPLOY DE REDIS (5 min) {#redis-setup}

### Opción 1: Upstash Redis (Recomendado - Gratis)

Upstash ofrece Redis serverless con integración nativa en Fly.io.

```bash
# Crear base de datos Redis en Upstash
flyctl redis create \
  --name grupo-gad-redis \
  --region global \
  --plan free

# Output:
# Your Upstash Redis database grupo-gad-redis is ready
# REDIS_URL: redis://[token]@fly.upstash.io:6379

# Attach a tu app
flyctl redis attach grupo-gad-redis --app grupo-gad

# Esto crea automáticamente el secret REDIS_URL
```

### Opción 2: Fly.io Redis (Paid - Más control)

Si necesitas más control o mayor throughput:

```bash
flyctl redis create \
  --name grupo-gad-redis \
  --region mia \
  --vm-size shared-cpu-1x \
  --eviction noeviction \
  --plan paid

# Luego attach
flyctl redis attach grupo-gad-redis --app grupo-gad
```

### Verificar REDIS_URL
```bash
flyctl secrets list | grep REDIS_URL

# Deberías ver:
# REDIS_URL  | abc123...  | 1m ago
```

---

## 🚀 DEPLOY DE LA APLICACIÓN (10 min) {#app-deploy}

### Paso 1: Build y Deploy
```bash
# Deploy completo (build + migrations + start)
flyctl deploy

# Output esperado:
# ==> Verifying app config
# --> Verified app config
# ==> Building image
# [+] Building 45.2s (15/15) FINISHED
# ...
# ==> Pushing image to fly
# ...
# ==> Creating release
# --> release v1 created
# ==> Running deployment
#   ✓ Running migration: alembic upgrade head
#   ✓ Deploying 1 machine
# --> Machine a1b2c3d4e5 is HEALTHY
# ==> Visit your newly deployed app at https://grupo-gad.fly.dev/
```

### Paso 2: Monitor Deploy
```bash
# Ver logs en tiempo real
flyctl logs

# Ver status
flyctl status

# Output:
# ID       NAME      REGION  STATE   CHECKS  VMSIZE          CPU   MEM
# a1b2c3d  grupo-gad mia     started 2 total shared-cpu-1x  1     512 MB
```

### Paso 3: Configurar Dominio (Opcional)
```bash
# Si tienes dominio custom
flyctl certs create tu-dominio.com

# Agregar DNS CNAME:
# tu-dominio.com  →  grupo-gad.fly.dev
```

---

## ✅ VERIFICACIÓN Y TESTING (5 min) {#verification}

### Health Checks
```bash
# Check básico
curl https://grupo-gad.fly.dev/health
# Esperado: {"status":"ok"}

# Check detallado
curl https://grupo-gad.fly.dev/health/ready
# Esperado: {"status":"ready","database":"ok","redis":"ok"}
```

### API Documentation
```bash
# Swagger UI
open https://grupo-gad.fly.dev/docs

# ReDoc
open https://grupo-gad.fly.dev/redoc
```

### WebSocket Test
```bash
# Test desde browser
open https://grupo-gad.fly.dev/dashboard/websocket_test.html

# O con wscat (instalar: npm install -g wscat)
wscat -c wss://grupo-gad.fly.dev/ws/connect

# Deberías recibir:
# < {"event_type":"CONNECTION_ACK","data":{"message":"Connected"},...}
```

### Database Verification
```bash
# Ver logs de migrations
flyctl logs | grep alembic

# Conectar y verificar tablas
flyctl proxy 5432 -a grupo-gad-db

# En otra terminal:
psql postgresql://postgres:[PASSWORD]@localhost:5432/grupo_gad
# \dt  -- Lista tablas
# SELECT COUNT(*) FROM alembic_version;
```

### Redis Verification
```bash
# Ejecutar comando en Redis
flyctl ssh console -a grupo-gad
# Dentro de la VM:
curl -X GET http://localhost:8080/api/cache/test
```

---

## 🔧 TROUBLESHOOTING {#troubleshooting}

### Problema 1: Deploy Fallido

**Síntoma**: `Deploy failed: health checks failing`

**Diagnóstico**:
```bash
# Ver logs detallados
flyctl logs --app grupo-gad

# Ver status de health checks
flyctl status --app grupo-gad

# SSH a la máquina
flyctl ssh console --app grupo-gad
# Dentro: curl localhost:8080/health
```

**Soluciones comunes**:
```bash
# 1. Verificar PORT
flyctl secrets set PORT=8080

# 2. Verificar DATABASE_URL
flyctl secrets list | grep DATABASE_URL

# 3. Re-attach database
flyctl postgres attach grupo-gad-db --app grupo-gad

# 4. Restart
flyctl apps restart grupo-gad
```

---

### Problema 2: DATABASE_URL Incorrecto

**Síntoma**: `SQLSTATE[08006] connection failed`

**Diagnóstico**:
```bash
# Ver DATABASE_URL (no muestra valor, solo confirma existencia)
flyctl secrets list | grep DATABASE_URL

# Verificar conectividad a DB
flyctl postgres connect -a grupo-gad-db
```

**Solución**:
```bash
# Re-attach database (regenera DATABASE_URL)
flyctl postgres detach grupo-gad-db --app grupo-gad
flyctl postgres attach grupo-gad-db --app grupo-gad

# Restart app
flyctl apps restart grupo-gad
```

---

### Problema 3: Redis Connection Timeout

**Síntoma**: `RedisConnectionError: Connection timeout`

**Diagnóstico**:
```bash
# Verificar REDIS_URL
flyctl secrets list | grep REDIS_URL

# Test Redis connectivity
flyctl ssh console --app grupo-gad
# Dentro:
redis-cli -u $REDIS_URL PING
```

**Solución**:
```bash
# Re-attach Redis
flyctl redis detach grupo-gad-redis --app grupo-gad
flyctl redis attach grupo-gad-redis --app grupo-gad

# O crear nuevo Redis
flyctl redis create --name grupo-gad-redis-2 --region global --plan free
flyctl redis attach grupo-gad-redis-2 --app grupo-gad
```

---

### Problema 4: Migrations No Se Ejecutan

**Síntoma**: `alembic.util.exc.CommandError: Can't locate revision`

**Diagnóstico**:
```bash
# Ver logs de release_command
flyctl logs | grep alembic

# SSH y ejecutar manualmente
flyctl ssh console --app grupo-gad
# Dentro:
cd /app
alembic current
alembic upgrade head
```

**Solución**:
```bash
# Ejecutar migrations manualmente
flyctl ssh console --app grupo-gad
# Dentro:
alembic upgrade head
exit

# Restart
flyctl apps restart grupo-gad
```

---

### Problema 5: Out of Memory

**Síntoma**: `OOMKilled: Container killed due to out of memory`

**Diagnóstico**:
```bash
flyctl status --app grupo-gad
# Ver columna MEM

flyctl logs | grep -i "memory\|oom"
```

**Solución**:
```bash
# Escalar memoria
flyctl scale memory 1024 --app grupo-gad

# O reducir workers (ya está en 1)
# O agregar más VMs
flyctl scale count 2 --app grupo-gad
```

---

## 📚 COMANDOS ÚTILES {#useful-commands}

### App Management
```bash
# Ver info de la app
flyctl info --app grupo-gad

# Ver status
flyctl status --app grupo-gad

# Restart
flyctl apps restart grupo-gad

# Destroy (CUIDADO)
flyctl apps destroy grupo-gad
```

### Logs
```bash
# Logs en tiempo real
flyctl logs --app grupo-gad

# Últimas 100 líneas
flyctl logs --app grupo-gad -n 100

# Filtrar por nivel
flyctl logs --app grupo-gad | grep ERROR
```

### Scaling
```bash
# Escalar memoria
flyctl scale memory 512   # 512 MB
flyctl scale memory 1024  # 1 GB

# Escalar número de VMs
flyctl scale count 1  # 1 VM (default)
flyctl scale count 2  # 2 VMs (auto-balancing)

# Cambiar tipo de VM
flyctl scale vm shared-cpu-1x  # 1 CPU, 256 MB
flyctl scale vm dedicated-cpu-1x  # 1 vCPU dedicado
```

### Database Management
```bash
# Info de PostgreSQL
flyctl postgres info --app grupo-gad-db

# Conectar a PostgreSQL
flyctl postgres connect --app grupo-gad-db

# Backup (automático, pero puedes forzar)
flyctl postgres backup create --app grupo-gad-db

# Listar backups
flyctl postgres backup list --app grupo-gad-db

# Restore (CUIDADO)
flyctl postgres backup restore [backup-id] --app grupo-gad-db
```

### Redis Management
```bash
# Info de Redis
flyctl redis info --app grupo-gad-redis

# Ejecutar comandos Redis
flyctl redis connect --app grupo-gad-redis
# Dentro:
PING
INFO
KEYS *
```

### Secrets Management
```bash
# Listar secrets
flyctl secrets list --app grupo-gad

# Agregar secret
flyctl secrets set KEY=value --app grupo-gad

# Agregar múltiples
flyctl secrets set \
  KEY1=value1 \
  KEY2=value2 \
  --app grupo-gad

# Eliminar secret
flyctl secrets unset KEY --app grupo-gad

# Importar desde .env
flyctl secrets import < .env --app grupo-gad
```

### SSH Access
```bash
# SSH a la VM
flyctl ssh console --app grupo-gad

# Ejecutar comando remoto
flyctl ssh console --app grupo-gad -C "ls -la /app"

# Ver filesystem
flyctl ssh sftp shell --app grupo-gad
```

### Certificates (SSL)
```bash
# Listar certificados
flyctl certs list --app grupo-gad

# Crear certificado para dominio custom
flyctl certs create tu-dominio.com --app grupo-gad

# Verificar certificado
flyctl certs show tu-dominio.com --app grupo-gad

# Eliminar certificado
flyctl certs delete tu-dominio.com --app grupo-gad
```

### Monitoring
```bash
# Dashboard web
flyctl dashboard --app grupo-gad

# Métricas en terminal
flyctl metrics --app grupo-gad

# Ver releases
flyctl releases --app grupo-gad

# Rollback a release anterior
flyctl releases rollback [version] --app grupo-gad
```

---

## 🎯 WORKFLOW COMPLETO (Resumen)

```bash
# 1. Setup inicial (una vez)
flyctl launch
flyctl postgres create --name grupo-gad-db --region mia
flyctl postgres attach grupo-gad-db --app grupo-gad
flyctl redis create --name grupo-gad-redis --region global --plan free
flyctl redis attach grupo-gad-redis --app grupo-gad

# 2. Configurar secrets (una vez)
flyctl secrets set SECRET_KEY=[tu-valor]
flyctl secrets set POSTGRES_USER=gcp_user
flyctl secrets set POSTGRES_PASSWORD=[tu-password]
flyctl secrets set ENVIRONMENT=production

# 3. Deploy (cada cambio)
git add .
git commit -m "feat: nueva funcionalidad"
git push origin master
flyctl deploy

# 4. Verificar
flyctl logs
curl https://grupo-gad.fly.dev/health

# 5. Monitorear
flyctl dashboard
```

---

## 💰 COSTOS ESTIMADOS

### Free Tier (Desarrollo)
```
✅ App: 1 VM shared-cpu-1x (512 MB)     → Gratis
✅ PostgreSQL: 1 VM + 10 GB             → Gratis (hasta 3 GB)
✅ Redis Upstash: 10K req/day           → Gratis
✅ Bandwidth: 160 GB/mes                → Gratis
───────────────────────────────────────────────
TOTAL: $0/mes
```

### Production (Escalado)
```
💰 App: 2 VMs shared-cpu-1x (512 MB)    → $10/mes ($5 cada)
💰 PostgreSQL: 1 VM + 20 GB             → $5/mes
💰 Redis Upstash: 100K req/day          → Gratis (hasta 1M)
✅ Bandwidth: 500 GB/mes                → Incluido
───────────────────────────────────────────────
TOTAL: $15/mes
```

---

## 📖 RECURSOS ADICIONALES

- **Fly.io Docs**: https://fly.io/docs/
- **Fly.io PostgreSQL**: https://fly.io/docs/postgres/
- **Fly.io Redis**: https://fly.io/docs/reference/redis/
- **Upstash Redis**: https://upstash.com/docs/redis
- **FastAPI on Fly**: https://fly.io/docs/python/the-basics/
- **WebSockets on Fly**: https://fly.io/docs/app-guides/websockets/

---

**Última actualización**: 18 Octubre 2025  
**Status**: ✅ Production-ready  
**Tiempo total**: 30-40 minutos  
**Siguiente paso**: `flyctl launch`
