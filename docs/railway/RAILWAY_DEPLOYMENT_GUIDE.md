# 🚀 GRUPO_GAD - Guía de Deployment en Railway

**Estado de Compatibilidad**: ✅ 100% COMPATIBLE  
**Tiempo Estimado**: 15-20 minutos  
**Dificultad**: ⭐ Muy Fácil (sin DevOps necesario)  

---

## ✅ Por qué Railway es PERFECTO para GRUPO_GAD

- ✅ **Dockerfile optimizado** → Railway lo detecta automáticamente
- ✅ **PostgreSQL + Redis** → Incluidos, no configuras nada
- ✅ **Database URLs automáticas** → Railway te las genera
- ✅ **Deploy desde GitHub** → 1 click, completamente automático
- ✅ **Health checks definidos** → Railway monitorea tu app
- ✅ **SSL automático** → HTTPS gratis
- ✅ **$5 crédito mensual** → Tier gratuito disponible

---

## 🎯 PLAN DE ACCIÓN EN 6 PASOS

### PASO 1: Genera los Secrets Independientes (5 minutos)

Estos secrets NO dependen del servidor. Généralos AHORA:

```bash
# 1. SECRET_KEY (JWT/Encriptación)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copia el output

# 2. POSTGRES_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
# Copia el output

# 3. SSH_PRIVATE_KEY (si ya tienes claves SSH)
cat ~/.ssh/id_rsa
# Copia TODO (desde -----BEGIN... hasta ...END----)

# Si NO tienes claves:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/grupogad -N ""
cat ~/.ssh/grupogad
```

**Valores que tienes que decidir:**
- POSTGRES_USER: `grupogad_user`
- POSTGRES_DB: `grupogad_prod`

---

### PASO 2: Ve a Railway (2 minutos)

1. Abre: **https://railway.app**
2. Click: **"Login with GitHub"**
3. Autoriza la conexión a tu cuenta GitHub
4. ¡Listo! Estás en Railway

---

### PASO 3: Crea un Nuevo Proyecto (2 minutos)

1. Click: **"New Project"**
2. Selecciona: **"Deploy from GitHub repo"**
3. Selecciona tu repositorio: **eevans-d/GRUPO_GAD**
4. ✅ Railway comenzará a construir automáticamente

**Nota**: Railway detecta `docker/Dockerfile.api` automáticamente

---

### PASO 4: Añade PostgreSQL (1 minuto)

1. En el dashboard del proyecto
2. Click: **"+ Add Service"**
3. Selecciona: **"PostgreSQL"**
4. ✅ Railway lo crea automáticamente

**Railway te dará**: `DATABASE_URL` (cópialo, lo necesitarás)

---

### PASO 5: Añade Redis (1 minuto)

1. Click: **"+ Add Service"**
2. Selecciona: **"Redis"**
3. ✅ Railway lo crea automáticamente

**Railway te dará**: `REDIS_URL` (cópialo, lo necesitarás)

---

### PASO 6: Configura Variables de Entorno en Railway (3 minutos)

En el dashboard de tu proyecto → **Variables**

Añade cada una:

| NAME | VALUE |
|------|-------|
| `SECRET_KEY` | (el que generaste arriba con Python) |
| `POSTGRES_USER` | `grupogad_user` |
| `POSTGRES_PASSWORD` | (el que generaste arriba) |
| `POSTGRES_DB` | `grupogad_prod` |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | (el que Railway te dio automáticamente) |
| `REDIS_URL` | (el que Railway te dio automáticamente) |

**Importante**: No necesitas `SERVER_HOST` ni `SERVER_USERNAME` (Railway no los usa)

---

## 📍 CONFIGURAR GITHUB SECRETS (3 minutos)

Ahora TAMBIÉN necesitas estos valores en GitHub para CI/CD:

### Ve a GitHub

1. Tu repositorio **eevans-d/GRUPO_GAD**
2. **Settings** → **Secrets and variables** → **Actions**
3. Click: **"New repository secret"**

### Añade CADA secreto (15 total):

**TIER 1 - Credenciales Base (4):**
- `SSH_PRIVATE_KEY` = (tu clave SSH)
- `SERVER_HOST` = ⏭️ SKIP (no necesario con Railway)
- `SERVER_USERNAME` = ⏭️ SKIP (no necesario con Railway)
- `SECRET_KEY` = (igual al de Railway)

**TIER 2 - Base de Datos (4):**
- `DATABASE_URL` = (el de Railway)
- `POSTGRES_USER` = `grupogad_user`
- `POSTGRES_PASSWORD` = (el que generaste)
- `POSTGRES_DB` = `grupogad_prod`

**TIER 3 - Cache & Registry (4):**
- `REDIS_URL` = (el de Railway)
- `DOCKER_USERNAME` = (tu usuario Docker Hub - regístrate si no tienes)
- `DOCKER_PASSWORD` = (token de Docker Hub)
- `GKE_PROJECT_ID` = ⏭️ SKIP (solo si usas Google Cloud)

**TIER 4 - Backups & Monitoring (3 - Opcionales):**
- `BACKUP_ACCESS_KEY` = ⏭️ SKIP (por ahora)
- `BACKUP_SECRET_KEY` = ⏭️ SKIP (por ahora)
- `CLOUDFLARE_TOKEN` = ⏭️ SKIP (por ahora)

---

## ✅ CHECKLIST DE VERIFICACIÓN

```
[ ] 1. Cuenta de Railway creada
[ ] 2. GRUPO_GAD conectado desde GitHub
[ ] 3. Dockerfile.api detectado (Railway lo menciona)
[ ] 4. PostgreSQL creado (visible en dashboard)
[ ] 5. Redis creado (visible en dashboard)
[ ] 6. Variables de entorno en Railway configuradas (7 variables)
[ ] 7. Secretos en GitHub configurados (mínimo 10 críticos)
[ ] 8. API desplegada (Railway muestra status: "Running")
[ ] 9. API accesible en: https://proyecto-nombre.railway.app
[ ] 10. Database conectada (verificar en logs)
[ ] 11. Redis conectado (verificar en logs)
```

---

## 🎁 LO QUE SUCEDE AUTOMÁTICAMENTE

Una vez que todo está configurado:

```
1. Railway detecta cambios en GitHub ✅
2. Construye imagen Docker ✅
3. Ejecuta: `docker build -f docker/Dockerfile.api .` ✅
4. Inicia contenedor con variables de entorno ✅
5. Inyecta DATABASE_URL y REDIS_URL ✅
6. API escucha en PORT asignado ✅
7. PostgreSQL accesible a través de DATABASE_URL ✅
8. Redis accesible a través de REDIS_URL ✅
9. Expone API en: proyecto-nombre.railway.app ✅
10. SSL/HTTPS automático ✅
```

---

## 🔍 VERIFICAR QUE TODO FUNCIONA

### En Railway Dashboard:

1. Ve a tu proyecto
2. Click en el servicio **API**
3. Tab: **Logs** → Deberías ver algo como:

```
[INFO] Starting application...
[INFO] FastAPI running on 0.0.0.0:PORT
[INFO] Database connection pool initialized
[INFO] Redis connection established
[INFO] Application ready
```

### Probar la API:

```bash
# Reemplaza con tu dominio de Railway
curl https://grupo-gad-prod.railway.app/metrics

# O desde el navegador:
https://grupo-gad-prod.railway.app/metrics
```

Deberías ver: `# HELP process_resident_memory_bytes...`

---

## 🌐 TU DOMINIO EN RAILWAY

Railway te asigna automáticamente:

**`https://grupo-gad-prod.railway.app`**

(El nombre exacto depende del que elijas)

### Acceder a la API:

- **Documentación**: `https://grupo-gad-prod.railway.app/docs`
- **Redoc**: `https://grupo-gad-prod.railway.app/redoc`
- **Métricas**: `https://grupo-gad-prod.railway.app/metrics`

---

## ⚠️ MIGRACIONES ALEMBIC

### Opción 1: Manual (Recomendado para la primera vez)

```bash
# Localmente en tu máquina:
export DATABASE_URL="postgresql://user:pass@host:5432/db"
alembic upgrade head
```

Luego despliega en Railway.

### Opción 2: Automático en Railway

Si quieres que Railway ejecute migraciones automáticamente:

1. En Railway → Variables
2. Añade: `RUN_MIGRATIONS=true`
3. Railway ejecutará `alembic upgrade head` antes de iniciar

---

## 🐛 TROUBLESHOOTING

### "Database connection error"

**Problema**: API no puede conectar a PostgreSQL

**Solución**:
1. Verifica `DATABASE_URL` en Railway
2. Verifica que PostgreSQL está corriendo (verde en dashboard)
3. Espera 30 segundos (PostgreSQL se inicia lentamente)

### "Redis connection error"

**Problema**: API no puede conectar a Redis

**Solución**:
1. Verifica `REDIS_URL` en Railway
2. Verifica que Redis está corriendo (verde en dashboard)

### "Application crashed"

**Problema**: La app se reinicia constantemente

**Solución**:
1. Ve a Logs en Railway
2. Lee el error exacto
3. Busca la variable mal configurada
4. Recarga el servicio (restart button)

### "Port already in use"

**Problema**: Puerto 8000 está ocupado

**Solución**: Railway asigna PORT automáticamente (no uses 8000 hardcoded)

---

## 💰 COSTOS

### Tier Gratuito de Railway:
- **$5 crédito mensual** (approx 5 GB RAM/mes)
- PostgreSQL: ~$0.15/GB
- Redis: ~$0.10/GB
- Compute: ~$0.000463/GB-hour

### Estimación para GRUPO_GAD:
- **Staging**: ~$2-5/mes
- **Production**: ~$10-20/mes (si crece)

### Para Empezar:
- Usa el **$5 crédito gratuito** por 1 mes
- Después, solo pagas lo que uses

---

## 🔄 FLUJO COMPLETO RESUMIDO

```
1. Génera secrets locales (5 min)
           ↓
2. Crea proyecto en Railway (2 min)
           ↓
3. Añade PostgreSQL (1 min)
           ↓
4. Añade Redis (1 min)
           ↓
5. Configura variables en Railway (3 min)
           ↓
6. Configura secretos en GitHub (3 min)
           ↓
7. Railway detecta cambios en GitHub
           ↓
8. Construye imagen Docker
           ↓
9. Inicia aplicación
           ↓
10. ✅ API LIVE EN PRODUCCIÓN
```

---

## ✨ PRÓXIMO PASO

**¿Estás listo?**

1. Abre: **https://railway.app**
2. Login con GitHub
3. Crea nuevo proyecto
4. Selecciona eevans-d/GRUPO_GAD
5. ¡Sigue los 6 pasos arriba!

**En 15-20 minutos, tu API estará en producción.** 🚀

---

## ❓ PREGUNTAS FRECUENTES

### ¿Necesito saber DevOps?
**NO.** Railway abstrae todo. Solo necesitas pegar variables.

### ¿Puedo desplegar sin CI/CD?
**SÍ.** Railway lo hace automáticamente desde GitHub.

### ¿Qué pasa si hay error en el deploy?
**Railway rollback automático** a la versión anterior.

### ¿Puedo escalar después?
**SÍ.** Railway escala horizontalmente con 1 click.

### ¿Puedo migrar a DigitalOcean después?
**SÍ.** Exporta tu DB, configura nuevo servidor, listo.

### ¿Necesito un dominio custom?
**NO.** Tienes `proyecto.railway.app` gratis.

---

## 📚 REFERENCIAS

- **Railway Docs**: https://docs.railway.app
- **Railway Deploy**: https://railway.app/new
- **GRUPO_GAD Repo**: https://github.com/eevans-d/GRUPO_GAD

---

**¡Hoy va a ser el día que GRUPO_GAD llega a producción!** 🎉

Si tienes dudas en cualquier paso, pregunta. Estoy aquí para ayudarte.
