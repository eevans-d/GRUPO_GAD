# 🔧 GUÍA DE SOLUCIÓN: Build Failed en Fly.io

**Fecha**: 19 Octubre 2025  
**Problema**: Build failed en commit d0044d1  
**Solución**: Dockerfile mejorado en commit 68dbe26 ✅  

---

## 🎯 **SOLUCIÓN INMEDIATA** (2 minutos)

### **Opción A: Retry desde Dashboard de Fly.io** (MÁS FÁCIL)

1. **En el dashboard de Fly.io**, donde viste el error, busca el botón:
   ```
   "Retry from latest commit (master)"
   ```

2. **Haz click** en ese botón

3. **Espera** ~5-10 minutos mientras Fly.io:
   - ✅ Descarga el nuevo código (commit 68dbe26)
   - ✅ Instala dependencias PostgreSQL
   - ✅ Compila la imagen Docker
   - ✅ Despliega la aplicación

4. **Verifica** que el build termine exitosamente

---

### **Opción B: Deploy desde Terminal** (Alternativa)

Si prefieres hacerlo desde terminal:

```bash
# 1. Ir al directorio del proyecto
cd /home/eevan/ProyectosIA/GRUPO_GAD

# 2. Asegurarte de estar en el último commit
git pull origin master

# 3. Verificar que estás en el commit correcto
git log --oneline -1
# Deberías ver: 68dbe26 fix(docker): add PostgreSQL support...

# 4. Si no tienes flyctl instalado:
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"

# 5. Login en Fly.io
flyctl auth login

# 6. Deploy manual
flyctl deploy --app grupo-gad
```

---

## 🔍 **QUÉ SE ARREGLÓ**

### **Problema Identificado**

El Dockerfile original faltaba:
- ❌ Librerías PostgreSQL para compilar `psycopg2` y `asyncpg`
- ❌ Librerías runtime para conectarse a PostgreSQL
- ❌ Directorios necesarios (`logs/`, `data/`)
- ❌ Variable de entorno `PORT`

### **Solución Aplicada** (commit 68dbe26)

```diff
# Build stage - Agregado soporte PostgreSQL
+ libpq-dev         # Para compilar psycopg2/asyncpg
+ python3-dev       # Headers de Python
+ pip upgrade       # Última versión de pip

# Runtime stage - Agregado runtime PostgreSQL
+ libpq5           # Cliente PostgreSQL runtime
+ PORT=8080        # Variable de entorno
+ templates/       # Directorio de templates
+ logs/ y data/    # Directorios necesarios
```

### **Test Local Exitoso** ✅

```bash
# Build testeado localmente antes de push
docker build -t grupo-gad-test .
# ✅ SUCCESS - Build completed without errors
```

---

## 📊 **CRONOLOGÍA DE SOLUCIÓN**

```
d0044d1 (18 Oct) → Build FALLÓ en Fly.io
  ❌ Falta soporte PostgreSQL
  ❌ Falta directorios necesarios
  
↓ [Diagnóstico y fix - 19 Oct]

68dbe26 (19 Oct) → Build CORREGIDO
  ✅ PostgreSQL libs agregadas
  ✅ Directorios creados
  ✅ Test local exitoso
  
↓ [Deploy en Fly.io]

🎯 PRÓXIMO: Retry desde dashboard de Fly.io
```

---

## 🚀 **PASOS DETALLADOS PARA FLY.IO DASHBOARD**

### 1. Acceder al Dashboard

```
https://fly.io/apps/grupo-gad
```

O desde tu navegador donde viste el error.

### 2. Identificar la Sección de Deployments

Busca una sección que diga:
- "Recent Deployments"
- "Deploy History"
- "Latest Deploy"

### 3. Encontrar el Deploy Fallido

Verás algo como:
```
❌ v0 (d0044d1) - Failed
   Build failed
   X minutes ago
```

### 4. Opciones Disponibles

Deberías ver botones como:
- `Retry same commit now (d0044d1)` ← **NO uses este**
- `Retry from latest commit (master)` ← **USA ESTE** ✅
- `View logs`

### 5. Hacer Click en "Retry from latest commit"

Este botón:
- ✅ Descarga el código del último commit (68dbe26)
- ✅ Inicia un nuevo build con el Dockerfile corregido
- ✅ Usa la misma configuración (fly.toml, secrets, etc.)

### 6. Monitor del Build en Tiempo Real

Verás una pantalla con logs del build:

```
Building image...
[+] Building 45.2s
 => [internal] load build definition
 => [internal] load .dockerignore
 => [builder 1/5] FROM python:3.12-slim
 => [builder 2/5] WORKDIR /build
 => [builder 3/5] RUN apt-get update && apt-get install -y libpq-dev...
      ✅ Installing PostgreSQL libs (NUEVO)
 => [builder 4/5] COPY requirements.txt .
 => [builder 5/5] RUN pip install --upgrade pip && pip install...
      ✅ Installing Python dependencies
 => [stage-1 1/12] FROM python:3.12-slim
 => [stage-1 2/12] WORKDIR /app
 => [stage-1 3/12] RUN apt-get update && apt-get install -y libpq5...
      ✅ Installing runtime PostgreSQL (NUEVO)
 => [stage-1 4/12] COPY --from=builder /install /usr/local
 => [stage-1 5/12] COPY alembic.ini ./
 => [stage-1 6/12] COPY alembic ./alembic
 => [stage-1 7/12] COPY config ./config
 => [stage-1 8/12] COPY src ./src
 => [stage-1 9/12] COPY dashboard ./dashboard
 => [stage-1 10/12] COPY templates ./templates (NUEVO)
 => [stage-1 11/12] RUN mkdir -p /app/logs /app/data (NUEVO)
 => [stage-1 12/12] RUN groupadd -r app...
 => exporting to image
 => => exporting layers
 => => writing image
 => => naming to fly.io/grupo-gad:deployment-...
```

### 7. Esperar Confirmación

Al final deberías ver:
```
✅ Image successfully pushed to registry
✅ Creating release
✅ Running release_command: alembic upgrade head
✅ Deploying 1 machine
✅ Machine [id] is HEALTHY

Visit your app at: https://grupo-gad.fly.dev
```

---

## ✅ **VERIFICACIÓN POST-DEPLOY**

### 1. Health Check

```bash
# Desde tu terminal local
curl https://grupo-gad.fly.dev/health

# Respuesta esperada:
{"status":"ok","timestamp":"2025-10-19T..."}
```

### 2. API Docs

Abre en navegador:
```
https://grupo-gad.fly.dev/docs
```

Deberías ver la interfaz Swagger de FastAPI.

### 3. Logs de la App

En el dashboard de Fly.io, o desde terminal:
```bash
flyctl logs --app grupo-gad

# Deberías ver:
INFO: Started server process
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8080
```

---

## 🔧 **SI SIGUE FALLANDO**

### Diagnóstico Avanzado

#### 1. Ver Logs Completos del Build

En el dashboard, click en "View logs" del deploy fallido.

Busca líneas que contengan:
- `ERROR`
- `failed`
- `cannot find`
- `ModuleNotFoundError`

#### 2. Errores Comunes y Soluciones

**Error: "No module named 'psycopg2'"**
```bash
# Solución: Ya lo arreglamos en commit 68dbe26
# Asegúrate de usar "Retry from latest commit"
```

**Error: "Out of memory"**
```bash
# Solución: Escalar el builder
flyctl scale vm shared-cpu-1x --app grupo-gad
```

**Error: "Permission denied"**
```bash
# Solución: Verificar permisos en Dockerfile
# Ya configurado con usuario 'app' no-root
```

**Error: "Database connection failed"**
```bash
# Solución: Verificar DATABASE_URL secret
flyctl secrets list --app grupo-gad | grep DATABASE_URL

# Si falta, configurar:
flyctl postgres attach grupo-gad-db --app grupo-gad
```

#### 3. Build Local para Debug

```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD

# Build completo con output verbose
docker build -t grupo-gad-test -f Dockerfile . 2>&1 | tee build.log

# Si falla, revisar build.log
less build.log
```

---

## 📞 **OBTENER AYUDA DE FLY.IO**

Si después de retry sigue fallando:

### 1. Copiar Logs del Error

En el dashboard, selecciona TODO el texto del error y cópialo.

### 2. Reportar en Community

```
https://community.fly.io/

Título: "Build failed for FastAPI + PostgreSQL app"

Mensaje:
```
```
Hola, mi app FastAPI está fallando en el build.

Commit: 68dbe26
App: grupo-gad
Region: mia (Miami)

Dockerfile: Multi-stage Python 3.12-slim
Dependencies: FastAPI, PostgreSQL (asyncpg), Redis

Error logs:
[PEGA AQUÍ LOS LOGS COMPLETOS]

Dockerfile disponible en:
https://github.com/eevans-d/GRUPO_GAD/blob/master/Dockerfile

¿Alguna sugerencia?
```
```

### 3. Soporte Directo

Si tienes plan pago:
```
https://fly.io/dashboard/personal/support
```

---

## 🎯 **SIGUIENTE PASO RECOMENDADO**

```
┌─────────────────────────────────────────┐
│  ACCIÓN INMEDIATA                       │
└─────────────────────────────────────────┘

1. Ve al dashboard de Fly.io
   https://fly.io/apps/grupo-gad

2. Busca el botón:
   "Retry from latest commit (master)"

3. Haz click

4. Espera 5-10 minutos

5. Verifica:
   https://grupo-gad.fly.dev/health

6. Si funciona: ✅ ¡LISTO!

7. Si falla: Mira los logs y avísame
```

---

## 📊 **COMPARACIÓN: ANTES vs DESPUÉS**

### ANTES (d0044d1)
```dockerfile
# Build stage
RUN apt-get install -y gcc g++ make
# ❌ FALTA: libpq-dev para PostgreSQL

# Runtime stage
RUN apt-get install -y curl ca-certificates
# ❌ FALTA: libpq5 para runtime PostgreSQL

# Copy files
COPY src ./src
# ❌ FALTA: templates/
# ❌ FALTA: mkdir logs/ data/
```

### DESPUÉS (68dbe26)
```dockerfile
# Build stage
RUN apt-get install -y gcc g++ make libpq-dev python3-dev
# ✅ AGREGADO: Soporte PostgreSQL completo

# Runtime stage
RUN apt-get install -y curl ca-certificates libpq5
# ✅ AGREGADO: Cliente PostgreSQL runtime

# Copy files
COPY src ./src
COPY templates ./templates
RUN mkdir -p /app/logs /app/data
# ✅ AGREGADO: Directorios necesarios
```

---

## ✅ **CHECKLIST FINAL**

```
Pre-deploy:
[x] Dockerfile corregido
[x] PostgreSQL libs agregadas
[x] Commit pusheado (68dbe26)
[x] Test local exitoso

En Fly.io Dashboard:
[ ] Acceder a https://fly.io/apps/grupo-gad
[ ] Click en "Retry from latest commit (master)"
[ ] Esperar build completo (~5-10 min)
[ ] Verificar deploy exitoso

Post-deploy:
[ ] Test: curl https://grupo-gad.fly.dev/health
[ ] Abrir: https://grupo-gad.fly.dev/docs
[ ] Verificar logs: flyctl logs --app grupo-gad
[ ] Confirmar: App está HEALTHY
```

---

**Última actualización**: 19 Octubre 2025  
**Commit actual**: 68dbe26  
**Status**: ✅ Listo para retry en Fly.io  
**Siguiente acción**: Click en "Retry from latest commit (master)"
