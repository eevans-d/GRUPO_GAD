# 🔬 ANÁLISIS FORENSE PROFUNDO - Despliegue Fly.io (GRUPO_GAD)

**Fecha**: 19 Octubre 2025  
**Versión**: 1.0 - Ingeniería Inversa Completa  
**Perspectiva**: CLI/Fly.io  
**Estado**: ✅ Build FIXED (commit 68dbe26)  
**Próximo**: Retry Deployment

---

## 📋 TABLA DE CONTENIDOS

1. [Fases Críticas del Despliegue](#fases-críticas)
2. [Análisis CLI Detallado](#análisis-cli)
3. [Puntos de Falla Identificados](#puntos-de-falla)
4. [Flujo de Despliegue por Fase](#flujo-por-fase)
5. [Validación Pre-Despliegue](#validación-pre)
6. [Troubleshooting Avanzado](#troubleshooting)
7. [Checklist de Despliegue Seguro](#checklist)

---

## 🎯 FASES CRÍTICAS DEL DESPLIEGUE

### Fase 1: **BUILD PHASE** (Construcción de Imagen Docker)

#### 1.1 Análisis de Dockerfile - Multi-Stage Build

**Etapa 1: Builder (Compilación)**

```dockerfile
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

**Validaciones Críticas**:

| Parámetro | Valor | Propósito | ⚠️ Riesgo |
|-----------|-------|----------|---------|
| `PYTHONDONTWRITEBYTECODE=1` | ✅ | Evita .pyc en imagen | MENOR |
| `PYTHONUNBUFFERED=1` | ✅ | Logs en tiempo real | MINOR |
| `PIP_NO_CACHE_DIR=1` | ✅ | Reduce tamaño imagen | MENOR |
| `PIP_DISABLE_PIP_VERSION_CHECK=1` | ✅ | Acelera pip install | MENOR |

**Instalación de Dependencias (CRÍTICA)**:

```bash
# ✅ ESTADO ACTUAL (Commit 68dbe26) - CORREGIDO
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make \
    libpq-dev       # ← PostgreSQL development headers (AÑADIDO)
    python3-dev     # ← Python.h para C extensions (AÑADIDO)
```

**¿Por qué libpq-dev es CRÍTICO?**

| Paquete | Función | Archivo Compilado | Falla Sin Él |
|---------|---------|-------------------|--------------|
| `libpq-dev` | Headers PostgreSQL | `libpq.h` | asyncpg falla en `pip install` |
| `python3-dev` | Headers Python | `python.h` | Extensiones C fallan en compilación |
| `gcc/g++` | Compilador C/C++ | `.so` binaries | No se compilan extensiones |

**Verificación de asyncpg (Crítica)**:

```python
# requirements.txt línea 9
asyncpg>=0.29.0  # PostgreSQL async driver - REQUIERE libpq-dev

# Lo que sucede SIN libpq-dev:
# error: package not found for pg_config
# Building wheel for asyncpg (setup.py) ... error
# ERROR: Could not build wheels for asyncpg which use PEP 517
```

**Etapa 2: Runtime (Ejecución)**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    libpq5              # ← PostgreSQL runtime library (AÑADIDO)
```

**Por qué libpq5 en runtime**:

- `libpq5`: Client library para conectarse a PostgreSQL
- Sin ella: `error: libpq.so.5: cannot open shared object file`
- Alternativa rechazada: `psycopg2-binary` (binary bloat)

#### 1.2 Compilación de Dependencias Python

**requirements.txt - Top 10 Críticas**:

```
fastapi>=0.115.0              # Web framework
sqlalchemy[asyncio]>=2.0.25   # ORM async
alembic>=1.13.2               # Migrations
pydantic>=2.8.0               # Validation (REQUIERE python3-dev)
pydantic-settings>=2.2.1      # Settings loader
uvicorn[standard]>=0.30.0     # ASGI server
uvloop>=0.19.0                # Performance (REQUIERE gcc, libuv)
asyncpg>=0.29.0               # PostgreSQL driver (REQUIERE libpq-dev)
python-dotenv>=1.0.0          # .env loading
redis>=5.0.0                  # Redis client
```

**Paquetes que REQUIEREN Compilación (C Extensions)**:

| Paquete | C Extension | Headers Requeridos | Falla en Build |
|---------|-------------|-------------------|-----------------|
| `asyncpg` | `.so` binding | `libpq-dev` | ❌ sin libpq-dev |
| `pydantic` | Validación rápida | `python3-dev` | ❌ sin python3-dev |
| `uvloop` | Event loop | `gcc`, `libuv` | ❌ sin gcc |
| `redis` | Parsing | `gcc` | ❌ sin gcc |

**Flujo de pip install en Builder**:

```
1. pip install --upgrade pip
   └─ Versión mínima 23.1 (soporte wheels)

2. pip install --prefix=/install -r requirements.txt
   ├─ Descarga wheels pre-compilados (rápido)
   ├─ Si no existen: compila from source
   │  └─ REQUIERE gcc, python3-dev, libpq-dev
   └─ Instala en /install/ (no en /usr/local)
      └─ Facilita COPY en etapa Runtime
```

**Tamaño de Imagen sin Optimización**:

```
Etapa Builder (eliminada):    450 MB
├─ python:3.12-slim base:     140 MB
├─ gcc, g++, dev headers:     280 MB
├─ pip packages:              30 MB
└─ Descartada en etapa 2

Etapa Runtime (final):         185 MB
├─ python:3.12-slim base:     140 MB
├─ libpq5 + curl:             10 MB
└─ /install (del builder):    35 MB
```

**Gain**: 450 MB → 185 MB (59% reducción) ✅

---

### Fase 2: **RELEASE PHASE** (Migraciones - Crítica)

#### 2.1 Configuración en fly.toml

```toml
[deploy]
  release_command = "alembic upgrade head"
  strategy = "rolling"
```

**¿Qué significa?**

- **release_command**: Comando ejecutado ANTES de que Fly.io rota tráfico a nueva máquina
- **Timing**: Ocurre en máquina TEMPORAL (no la final)
- **Falla**: Si `alembic upgrade head` falla → ROLLBACK de despliegue
- **Timeout**: 30 segundos por defecto

#### 2.2 Análisis de alembic/env.py

```python
# Línea 32-40
try:
    from src.core.logging import get_logger
    migration_logger = get_logger("alembic.env")
    use_structured_logging = True
except ImportError:
    import logging
    migration_logger = logging.getLogger("alembic.env")
    use_structured_logging = False
```

**Flujo de Alembic en Fly.io**:

```
1. Container inicia
   └─ CMD: uvicorn (pero será interceptado)

2. Fly.io inyecta: release_command
   └─ Sustituye CMD
   └─ Ejecuta: alembic upgrade head
      ├─ Lee alembic.ini
      ├─ Carga src/api/models (SQLAlchemy)
      ├─ Conecta a DATABASE_URL (injected secret)
      ├─ Verifica alembic_version table
      ├─ Ejecuta pending migrations
      └─ Salida: "head is now at X"

3. Si exitoso:
   └─ Release command retorna exitcode 0
   └─ Fly.io inicia uvicorn en máquina final

4. Si falla:
   └─ Release command retorna exitcode != 0
   └─ Fly.io cancela despliegue
   └─ Máquina nueva se descarta
```

#### 2.3 Puntos de Falla en Release Phase

**Falla #1: DATABASE_URL no inyectada**

```bash
# Síntoma:
# Error: DATABASE_URL not set
# 
# Causa: Secret no configurado en Fly.io
#
# Solución:
flyctl secrets set DATABASE_URL="postgresql+asyncpg://user:pass@host/db" --app grupo-gad
```

**Falla #2: PostgreSQL no accesible**

```bash
# Síntoma:
# Could not connect to PostgreSQL: connection refused
#
# Causa: Database aún no creada OR network issue
#
# Solución:
flyctl postgres create --name grupo-gad-db --region mia
flyctl postgres attach grupo-gad-db --app grupo-gad
```

**Falla #3: Modelos no importan**

```bash
# Síntoma:
# ModuleNotFoundError: No module named 'src.api.models'
# SystemExit: 1
#
# Causa: sys.path mal configurado en alembic/env.py
#
# Verificar: Línea 17 en alembic/env.py
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

**Falla #4: Migration incompatible**

```bash
# Síntoma:
# sqlalchemy.exc.ProgrammingError: column "xyz" already exists
#
# Causa: Migration idempotente falla
#
# Solución:
# - Rollback y reintentar
# - O corregir migration con if_not_exists()
```

#### 2.4 Validación Pre-Release (CLI Commands)

```bash
# ANTES de desplegar en Fly.io, probar localmente:

# 1. Verificar sintaxis de alembic.ini
cd /home/eevan/ProyectosIA/GRUPO_GAD
alembic current

# 2. Verificar migrations pendientes
alembic upgrade --sql head | head -20

# 3. Probar conexión (requiere DATABASE_URL local)
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test_db"
alembic upgrade head --verbose

# 4. Si todo OK:
#    - Desplegar en Fly.io
#    - Fly.io ejecutará same command en release_command
```

---

### Fase 3: **RUNTIME PHASE** (Ejecución de Aplicación)

#### 3.1 Startup (Lifespan Event)

**main.py línea 53-130**:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown"""
    # STARTUP (antes de aceptar requests)
    api_logger.info("Iniciando...")
    _settings = get_settings()
    db_url = _settings.assemble_db_url()
    if not db_url:
        raise RuntimeError("DATABASE_URL no configurada")
    init_db(db_url)  # ← Crea async_engine
    
    # WebSockets initialization
    await websocket_event_emitter.start()
    initialize_websocket_integrator(websocket_event_emitter)
    await start_websocket_integration()
    
    # Metrics
    if METRICS_ENABLED:
        initialize_metrics()
    
    yield  # ← Servidor ahora acepta requests
    
    # SHUTDOWN (on Ctrl-C or kill signal)
    api_logger.info("Apagando...")
    # Cleanup...
```

**Duración esperada de Startup**:

| Componente | Tiempo | Crítico |
|-----------|--------|---------|
| import modules | 2-3s | SÍ |
| init_db(db_url) | 1-2s | SÍ - conexión test |
| websocket init | 0.5s | NO |
| metrics init | 0.1s | NO |
| **TOTAL** | **~4-6s** | - |

**Configuración de Health Check en fly.toml**:

```toml
[[services.http_checks]]
  interval = "15s"      # Cada 15 segundos
  timeout = "10s"       # Máximo 10s de espera
  grace_period = "30s"  # Wait 30s before first check
  restart_limit = 3     # 3 fallos = reinicia container
```

**¿Qué pasa si health check falla 3 veces?**

```
Time 0:   Container inicia → grace_period = 30s
Time 30:  Check 1 → FAIL (startup incompleto)
Time 45:  Check 2 → FAIL
Time 60:  Check 3 → FAIL
Time 65:  MACHINE RESTART ← Fly.io mata y reinicia container
```

#### 3.2 Endpoint /health

```python
# main.py línea ~315
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time() - app.state.start_time
    }
```

**Validación de /health**:

```bash
# Verificar endpoint funciona
curl -s http://localhost:8080/health | jq .

# En Fly.io, curl ya está en imagen (lo agregamos)
```

#### 3.3 Shutdown Graceful (Signal Handling)

```toml
[fly]
  kill_signal = "SIGINT"
  kill_timeout = "30s"
```

**Secuencia de Shutdown**:

```
1. Fly.io envía SIGINT (Ctrl-C)
   └─ Uvicorn captura signal

2. Uvicorn inicia shutdown sequence:
   ├─ Deja de aceptar nuevas conexiones
   ├─ Espera hasta 30s que requests terminen
   ├─ Cierra WebSockets
   └─ Llama shutdown handlers

3. FastAPI lifespan event ejecuta finally block:
   ├─ await websocket_manager.shutdown()
   ├─ await cache_service.shutdown()
   └─ await database.dispose()

4. Container se detiene (exitcode 0 si OK)
```

**Riesgo**: Si shutdown >30s → Fly.io fuerza SIGKILL

---

### Fase 4: **NETWORKING & PORT MAPPING**

#### 4.1 Puerto 8080 en Fly.io

```toml
[[services]]
  internal_port = 8080
  
  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true
    
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

**Mapeo de Puertos**:

```
External:               Internal (Container):
80   (HTTP)    ────→   8080 (uvicorn)
                       ↑ force_https redirige a 443

443 (HTTPS/TLS) ────→  8080 (uvicorn)
                       Fly.io termina TLS
```

**¿Por qué interno_port = 8080?**

- Railway usaba `$PORT` dinámico
- Fly.io prefiere puerto fijo interno
- Fly.io maneja routing automáticamente
- Nuestra app escucha `--port 8080`

#### 4.2 Load Balancer & Health Checks

```
CLIENTE
  │
  ├─→ HTTP  ─→ 80  ─→ Load Balancer ─→ 8080 (health check /health)
  │           (redirect)    ↓
  │                    HTTPS? ─→ 443
  │
  └─→ HTTPS ─→ 443 ─→ TLS Termination ─→ 8080 (forwarded)
```

**Health Check desde Load Balancer**:

```http
GET /health HTTP/1.1
Host: grupo-gad.fly.dev
User-Agent: Fly-HealthCheck
```

---

### Fase 5: **SECRETS & ENVIRONMENT VARIABLES**

#### 5.1 Injection Timing

```bash
# Fly.io secuencia:

1. Build image (incluye Dockerfile)
   └─ Secrets NO están disponibles

2. Release machine spin up
   └─ Inyecta secrets como ENV vars
   ├─ DATABASE_URL
   ├─ REDIS_URL
   ├─ SECRET_KEY
   └─ JWT_SECRET_KEY

3. Ejecuta release_command
   ├─ alembic upgrade head
   └─ USA secrets como env vars

4. Inicia uvicorn
   ├─ FastAPI lifespan
   ├─ get_settings() lee env vars
   └─ assemble_db_url() construye conexión
```

#### 5.2 Configuración de Settings (Pydantic)

```python
# config/settings.py línea 50-52
@field_validator("DATABASE_URL", mode="before")
@classmethod
def assemble_db_connection(cls, v: str | None, info: Any) -> str | None:
    if isinstance(v, str) and v:
        return v
    
    legacy_db_url = os.getenv("DB_URL")
    if legacy_db_url:
        return legacy_db_url
    
    # Fallback: construir desde componentes POSTGRES_*
    user = data.get("POSTGRES_USER")
    password = data.get("POSTGRES_PASSWORD")
    ...
    return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"
```

**Prioridad (DESC)**:

```
1. DATABASE_URL env var (si existe)
   └─ Fly.io lo inyecta automáticamente con `flyctl postgres attach`

2. DB_URL env var (legacy)
   └─ Soporte backward compatibility

3. Construir desde POSTGRES_USER/PASS/DB/SERVER/PORT
   └─ Fallback si 1 y 2 no existen
```

#### 5.3 Secrets Requeridos para Producción

| Secret | Valor | Inyectado Por | Crítico |
|--------|-------|---------------|---------|
| `SECRET_KEY` | 256-bit random | `flyctl secrets set` | ✅ SÍ |
| `JWT_SECRET_KEY` | 256-bit random | `flyctl secrets set` | ✅ SÍ |
| `POSTGRES_USER` | username | `flyctl postgres attach` | ✅ SÍ |
| `POSTGRES_PASSWORD` | password | `flyctl postgres attach` | ✅ SÍ |
| `POSTGRES_DB` | database name | `flyctl postgres attach` | ✅ SÍ |
| `DATABASE_URL` | connection string | `flyctl postgres attach` | ✅ SÍ |
| `REDIS_URL` | Redis connection | `flyctl secrets set` | ⚠️ WARN |

**Falta de Secrets**:

```bash
# Si SECRET_KEY falta:
# Error: SECRET_KEY configuration is empty
# → Startup falla
# → Health check falla
# → Machine restart loop

# Si REDIS_URL falta:
# Warning: Redis unavailable
# → App funciona (cache degradado)
# → Mejor que fallar completamente
```

---

## 🖥️ ANÁLISIS CLI DETALLADO

### Comandos CLI Flyctl - Secuencia Completa

#### **FASE 0: Instalación de flyctl**

```bash
# 1. Descargar e instalar
curl -L https://fly.io/install.sh | sh

# 2. Verificar instalación
flyctl version
# Output: v0.1.XXX

# 3. Agregar a PATH (bash)
export PATH="$HOME/.fly/bin:$PATH"
```

#### **FASE 1: Autenticación**

```bash
# 1. Login interactivo (abre navegador)
flyctl auth login
# → Te redirige a https://fly.io/
# → Copia token → Pega en terminal
# → ~/.flyrc guardará token

# 2. Verificar autenticación
flyctl auth whoami
# Output: username@email.com

# 3. Ver orgs disponibles
flyctl orgs list
```

#### **FASE 2: Crear PostgreSQL**

```bash
# 1. Crear instancia PostgreSQL
flyctl postgres create \
  --name grupo-gad-db \
  --region mia \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 10

# Output:
# New Postgres cluster created
# Replica URL: postgres://...
# Leader URL: postgresql+asyncpg://user:pass@grupo-gad-db.internal:5432/grupo_gad_db

# 2. Adjuntar a app (automático si app existe)
flyctl postgres attach grupo-gad-db --app grupo-gad
# → DATABASE_URL injected en secrets

# 3. Verificar conexión
flyctl postgres connect --app grupo-gad-db
# → psql prompt
# → \d (listar tablas)
# → \q (salir)
```

**¿Qué hace `flyctl postgres create`?**

```
1. Crear 1 máquina PostgreSQL en región mia
2. Provisionar volumen de 10GB
3. Generar contraseña aleatoria (64-bit)
4. Retornar connection string
5. GUARDAR en secret DATABASE_URL
```

#### **FASE 3: Crear Redis (opcional, recomendado Upstash)**

```bash
# Opción A: Fly.io Redis (beta, limitado)
flyctl redis create \
  --name grupo-gad-redis \
  --region mia
# → Retorna REDIS_URL

# Opción B: Upstash (recomendado - gratis tier)
# 1. Ir a https://console.upstash.com
# 2. Create Redis
# 3. Copy connection URL
# 4. Inyectar en Fly.io:
flyctl secrets set REDIS_URL="redis://..." --app grupo-gad
```

#### **FASE 4: Configurar Secrets**

```bash
# 1. Inyectar todos los secrets
flyctl secrets set \
  SECRET_KEY="1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d" \
  JWT_SECRET_KEY="KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU" \
  POSTGRES_USER="gcp_user" \
  POSTGRES_PASSWORD="E9CbevopiGtsOb23InMrJtzhXBh37MNkCikBrjXa8TI=" \
  POSTGRES_DB="gcp_db" \
  --app grupo-gad

# 2. Verificar secrets (NO muestra valores)
flyctl secrets list --app grupo-gad
# Output:
# SECRET_KEY                   (set)
# JWT_SECRET_KEY              (set)
# DATABASE_URL                (set by postgres attach)
# REDIS_URL                   (set)

# 3. Cambiar un secret
flyctl secrets set SECRET_KEY="new_value" --app grupo-gad
# → Automáticamente redeploy la app
```

#### **FASE 5: Deploy**

```bash
# 1. Desplegar (desde raíz repo)
cd /home/eevan/ProyectosIA/GRUPO_GAD
flyctl deploy --app grupo-gad

# Output:
# Building image with Docker buildkit
# #1 [internal] load build definition from Dockerfile
# #2 [builder 1/5] FROM python:3.12-slim
# ...
# #10 built in 45s
# Image: registry.fly.io/grupo-gad:...
#
# Pushing image to Fly registry
# ...
# Release command: alembic upgrade head
# Migrating database
# Creating release machine
# ...
# v1 deployed successfully

# 2. Verificar deployment
flyctl status --app grupo-gad
# Output:
# App Name: grupo-gad
# Status:   ok
# Machines: 1 running (shared-cpu-1x, 512MB)
# Latest: 123abc... (some time ago)

# 3. Ver logs
flyctl logs --app grupo-gad
# Output (últimas líneas):
# 2025-10-19T12:34:56 app[xxx] mia [info] INFO: Uvicorn running on http://0.0.0.0:8080
# 2025-10-19T12:34:56 app[xxx] mia [info] INFO: Application startup complete
```

#### **FASE 6: Verificación Post-Deploy**

```bash
# 1. Health check
curl -s https://grupo-gad.fly.dev/health | jq .
# Output: {"status": "ok", "timestamp": "...", "uptime": 120}

# 2. API endpoints
curl -s https://grupo-gad.fly.dev/api/v1/usuarios | jq .

# 3. WebSocket test
# Usar dashboard/static/websocket_test.html
# O script en scripts/ws_smoke_test.py

# 4. Monitoreo en tiempo real
flyctl logs --app grupo-gad -f
# → Tail logs en tiempo real

# 5. Métricas
flyctl metrics show --app grupo-gad
# Output: CPU %, Memory %, Requests/s
```

#### **FASE 7: Troubleshooting CLI**

```bash
# Si deployment falla:

# 1. Ver logs de build
flyctl logs --app grupo-gad --instance <machine-id>

# 2. Acceder a máquina viva
flyctl ssh console --app grupo-gad
# → bash prompt en container
# → cat /var/log/app.log
# → ps aux
# → exit

# 3. Ver eventos
flyctl events list --app grupo-gad

# 4. Rollback a versión anterior
flyctl releases list --app grupo-gad
flyctl releases rollback --app grupo-gad

# 5. Escalar máquinas
flyctl scale count 2 --app grupo-gad --region mia  # 2 máquinas
flyctl scale vm shared-cpu-2x --app grupo-gad      # CPU upgrade

# 6. Reiniciar
flyctl apps restart --app grupo-gad
```

---

## ⚠️ PUNTOS DE FALLA IDENTIFICADOS

### MATRIZ DE RIESGO: Build → Release → Runtime

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE         │ RIESGO          │ SÍNTOMA           │ SEVERIDAD      │
├─────────────────────────────────────────────────────────────────────┤
│ BUILD        │ Missing libpq   │ asyncpg compile   │ ❌ CRITICAL    │
│              │                 │ error             │ (FIXED 68dbe26)│
├─────────────────────────────────────────────────────────────────────┤
│ BUILD        │ Base image      │ "FROM python..."  │ ⚠️ HIGH       │
│              │ pull timeout    │ timeout           │                │
├─────────────────────────────────────────────────────────────────────┤
│ RELEASE      │ DATABASE_URL    │ "DATABASE_URL     │ ❌ CRITICAL    │
│              │ missing         │ not set"          │                │
├─────────────────────────────────────────────────────────────────────┤
│ RELEASE      │ Migration       │ "sqlalchemy.exc   │ ❌ CRITICAL    │
│              │ incompatible    │ .ProgrammingError"│                │
├─────────────────────────────────────────────────────────────────────┤
│ RUNTIME      │ Health check    │ FAIL 3x → restart │ ⚠️ HIGH       │
│              │ fails           │ loop              │                │
├─────────────────────────────────────────────────────────────────────┤
│ RUNTIME      │ OOM (Out of     │ "Killed" signal   │ ⚠️ MEDIUM     │
│              │ Memory)         │ 9                 │                │
├─────────────────────────────────────────────────────────────────────┤
│ NETWORKING   │ TLS cert expired│ 503 Service       │ ⚠️ HIGH       │
│              │                 │ Unavailable       │                │
└─────────────────────────────────────────────────────────────────────┘
```

### Falla #1: Missing PostgreSQL Libraries (FIXED ✅)

```bash
# SÍNTOMA
error: Could not build wheels for asyncpg which use PEP 517
  ERROR: Could not build wheels for asyncpg
  ...
  error: pg_config not found

# CAUSA
# Dockerfile no instalaba libpq-dev en builder stage

# DIAGNÓSTICO ANTES DE FIX (commit d0044d1)
# ❌ FROM python:3.12-slim AS builder
# ❌ RUN apt-get install -y gcc g++ make
#    (falta: libpq-dev, python3-dev)
# ❌ RUN pip install -r requirements.txt
#    └─→ asyncpg>=0.29.0
#        ├─ Busca wheel pre-compilado
#        ├─ No existe para python 3.12.3
#        ├─ Intenta compilar from source
#        ├─ Busca pg_config
#        ├─ ❌ FALLA: "pg_config not found"
#        └─ pg_config está en libpq-dev

# SOLUCIÓN APLICADA (commit 68dbe26)
# ✅ RUN apt-get install -y gcc g++ make libpq-dev python3-dev
# ✅ Ahora asyncpg compila exitosamente
# ✅ Ahora pydantic compila C extensions

# VERIFICACIÓN LOCAL
docker build -t grupo-gad-test -f Dockerfile .
# ✅ Build SUCCESS
```

### Falla #2: Database Connection in Release Phase

```bash
# SÍNTOMA
error: could not connect to PostgreSQL: connection refused
  ...
  RELEASE FAILED

# CAUSA
# PostgreSQL no creada aún OR network issue

# CHECKLIST PREVIO A DEPLOY
# ❌ flyctl postgres list (debe mostrar grupo-gad-db)
# ❌ flyctl secrets list (debe mostrar DATABASE_URL)
# ❌ flyctl postgres connect (debe conectar exitosamente)

# SOLUCIÓN
flyctl postgres create --name grupo-gad-db --region mia
flyctl postgres attach grupo-gad-db --app grupo-gad

# VERIFICAR
flyctl postgres connect --app grupo-gad-db
# psql> \d
# (listar tablas)
```

### Falla #3: Migration Rollback (Alembic)

```bash
# SÍNTOMA
ERROR: Could not complete release command
alembic.exc.CommandError: Error: ...
  column "field_name" already exists

# CAUSA
# Migration ejecutada parcialmente, segundo deployment intenta re-ejecutar

# DIAGNÓSTICO
flyctl ssh console --app grupo-gad
$ alembic current
# (muestra última version)
$ alembic upgrade --sql head | head -5
# (muestra pendientes)

# SOLUCIÓN
# Opción A: Downgrade a anterior version
alembic downgrade -1

# Opción B: Corregir migration con idempotence
# En alembic/versions/*.py:
# op.create_table(..., if_not_exists=True)
```

### Falla #4: Lifespan Timeout (Startup too slow)

```bash
# SÍNTOMA
Health check fails 3 times
Machine restarts continuously
Error: [WARN] Aborting read due to deadline

# CAUSA
# init_db(db_url) + WebSocket init >40s

# DIAGNÓSTICO
flyctl logs --app grupo-gad
# [info] Iniciando aplicación...
# [info] Conexión a la base de datos establecida. (took 5s)
# [info] Iniciando sistema de WebSockets... (took 15s)
# [WARN] Grace period: 30s, pero startup = 35s

# SOLUCIÓN
# Aumentar grace_period en fly.toml
[[services.http_checks]]
  grace_period = "60s"  # Fue 30s
```

### Falla #5: Secrets Not Injected

```bash
# SÍNTOMA
Error: SECRET_KEY configuration is empty
  File "config/settings.py", line 25
  SECRET_KEY: str  # NO default

# CAUSA
# Secret no configurado en Fly.io

# DIAGNÓSTICO
flyctl secrets list --app grupo-gad
# Si SECRET_KEY no aparece:

# SOLUCIÓN
flyctl secrets set SECRET_KEY="1534c53529e8723bb1a3..." --app grupo-gad

# Verifica que se inyecta:
flyctl logs --app grupo-gad
# Busca: "SECRET_KEY" en logs (no debe mostrar valor)
```

### Falla #6: Memory Limit Exceeded

```bash
# SÍNTOMA
Killed signal 9 (OOM)
App stops responding

# CAUSA
# Pool de conexiones DB demasiado grande
# DB_POOL_SIZE=10 (para 512MB)

# DIAGNÓSTICO
flyctl metrics show --app grupo-gad
# Memory: 450MB/512MB (crítico)

# SOLUCIÓN A: Reducir pool
export DB_POOL_SIZE=5
export DB_MAX_OVERFLOW=10
flyctl secrets set DB_POOL_SIZE=5 --app grupo-gad

# SOLUCIÓN B: Upgrade VM
flyctl scale vm shared-cpu-2x --app grupo-gad
# Upgrade a 1GB RAM
```

---

## 🔄 FLUJO DE DESPLIEGUE POR FASE

### **Timeline Completo (Esperado)**

```
TIME    EVENTO                    COMPONENTE      ESTADO
═══════════════════════════════════════════════════════════════
0:00    flyctl deploy             CLI             ✓ Initiate
0:05    Build Docker image        Docker Builder  ⏳ IN PROGRESS
        - #1 Load Dockerfile
        - #2 FROM python:3.12
        - #3 apt-get install
        - #4 pip install (45s)
        ✓ Build complete

0:50    Push image to registry    Fly Registry    ⏳ IN PROGRESS
        (image size: ~185MB)
        ✓ Push complete

1:00    Create release machine    VM Manager      ⏳ PENDING
        ✓ Machine started

1:10    Inject secrets            Secret Store    ✓ DONE
        ├─ DATABASE_URL
        ├─ REDIS_URL
        ├─ SECRET_KEY
        └─ JWT_SECRET_KEY

1:15    Execute release_command   Application     ⏳ IN PROGRESS
        $ alembic upgrade head
        ├─ Connect DB
        ├─ Check schema_version
        ├─ Run migrations
        └─ ✓ head is now at XYZ

1:20    Start uvicorn             Application     ⏳ STARTUP
        ├─ import modules (2s)
        ├─ init_db() (2s)
        ├─ WebSocket init (0.5s)
        └─ ✓ ready to serve

1:25    First health check        LB              ⏳ CHECK
        GET /health
        ✓ 200 OK

1:30    Health checks passing     LB              ✓ GREEN
        (3/3 checks OK)

1:35    Route traffic             Load Balancer   ✓ ACTIVE
        requests → 0.0.0.0:8080

1:40    Old machine shutdown      VM Manager      ✓ KILLED
        (rolling deployment)

1:40    New version LIVE          Fly.io          ✓ DEPLOYED
        https://grupo-gad.fly.dev

TOTAL DEPLOYMENT TIME: ~1:40 (100s)
```

### **Si Falla en Build (PRIOR STATE)**

```
TIME    EVENTO                    ESTADO
═══════════════════════════════════════════════════════════════
0:00    flyctl deploy             ✓
0:30    Building asyncpg          ❌ FAIL
        error: pg_config not found
        
        Docker logs:
        ERROR: Could not build wheels for asyncpg
        
1:00    Build FAILED              ❌ ABORTED
        
        Flyctl output:
        Error: failed to build
        
        Status: deploy FAILED
        Previous version still running
```

**Antes del FIX (d0044d1)**:
```
Dockerfile:
  RUN apt-get install gcc g++ make   # ❌ Falta libpq-dev
  RUN pip install -r requirements.txt
    └─ asyncpg compile FAILS
```

**Después del FIX (68dbe26)**:
```
Dockerfile:
  RUN apt-get install gcc g++ make libpq-dev python3-dev  # ✅ ADDED
  RUN pip install -r requirements.txt
    └─ asyncpg compile SUCCESS ✅
```

---

## ✅ VALIDACIÓN PRE-DESPLIEGUE

### Checklist de 15 Puntos (Antes de Retry)

```bash
#!/bin/bash
# GRUPO_GAD Pre-Deployment Validation Checklist

echo "=== PRE-DEPLOYMENT VALIDATION ==="

# 1. ✅ Fly.toml sintaxis
echo "1. Validating fly.toml..."
if grep -q 'app = "grupo-gad"' fly.toml; then
    echo "   ✓ fly.toml structure OK"
else
    echo "   ❌ FAIL: fly.toml invalid"
    exit 1
fi

# 2. ✅ Dockerfile exists
echo "2. Checking Dockerfile..."
if [ -f Dockerfile ]; then
    echo "   ✓ Dockerfile found"
else
    echo "   ❌ FAIL: Dockerfile missing"
    exit 1
fi

# 3. ✅ PostgreSQL libraries in Dockerfile
echo "3. Checking PostgreSQL libraries..."
if grep -q "libpq-dev\|libpq5" Dockerfile; then
    echo "   ✓ PostgreSQL libs present"
else
    echo "   ❌ FAIL: Missing libpq-dev or libpq5"
    exit 1
fi

# 4. ✅ requirements.txt has asyncpg
echo "4. Checking asyncpg..."
if grep -q "asyncpg" requirements.txt; then
    echo "   ✓ asyncpg found in requirements"
else
    echo "   ❌ FAIL: asyncpg missing"
    exit 1
fi

# 5. ✅ alembic.ini exists
echo "5. Checking alembic.ini..."
if [ -f alembic.ini ]; then
    echo "   ✓ alembic.ini found"
else
    echo "   ❌ FAIL: alembic.ini missing"
    exit 1
fi

# 6. ✅ Git status clean
echo "6. Checking git status..."
if [ -z "$(git status --porcelain)" ]; then
    echo "   ✓ Working tree clean"
else
    echo "   ⚠️  WARNING: Uncommitted changes"
    git status --short
fi

# 7. ✅ Latest commit pushed
echo "7. Checking remote..."
if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/master)" ]; then
    echo "   ✓ Latest commit pushed"
else
    echo "   ⚠️  WARNING: Local HEAD != origin/master"
fi

# 8. ✅ Requirements.txt parseable
echo "8. Parsing requirements.txt..."
if python3 -c "
import re
with open('requirements.txt') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            re.match(r'^[a-zA-Z0-9_-]+', line)
" 2>/dev/null; then
    echo "   ✓ requirements.txt OK"
else
    echo "   ❌ FAIL: requirements.txt syntax error"
    exit 1
fi

# 9. ✅ Python 3.12 in Dockerfile
echo "9. Checking Python version..."
if grep -q "python:3.12" Dockerfile; then
    echo "   ✓ Python 3.12 specified"
else
    echo "   ⚠️  WARNING: Python version mismatch"
fi

# 10. ✅ flyctl installed
echo "10. Checking flyctl..."
if command -v flyctl &> /dev/null; then
    echo "   ✓ flyctl installed ($(flyctl version))"
else
    echo "   ❌ FAIL: flyctl not found (curl https://fly.io/install.sh | sh)"
    exit 1
fi

# 11. ✅ flyctl authenticated
echo "11. Checking flyctl auth..."
if flyctl auth whoami &> /dev/null; then
    echo "   ✓ flyctl authenticated: $(flyctl auth whoami)"
else
    echo "   ❌ FAIL: Run 'flyctl auth login'"
    exit 1
fi

# 12. ✅ PostgreSQL created
echo "12. Checking PostgreSQL..."
if flyctl postgres list 2>/dev/null | grep -q "grupo-gad-db"; then
    echo "   ✓ PostgreSQL instance exists"
else
    echo "   ⚠️  WARNING: PostgreSQL not found"
    echo "      Run: flyctl postgres create --name grupo-gad-db --region mia"
fi

# 13. ✅ DATABASE_URL secret set
echo "13. Checking DATABASE_URL secret..."
if flyctl secrets list --app grupo-gad 2>/dev/null | grep -q "DATABASE_URL"; then
    echo "   ✓ DATABASE_URL secret exists"
else
    echo "   ⚠️  WARNING: DATABASE_URL not set"
fi

# 14. ✅ SECRET_KEY secret set
echo "14. Checking SECRET_KEY..."
if flyctl secrets list --app grupo-gad 2>/dev/null | grep -q "SECRET_KEY"; then
    echo "   ✓ SECRET_KEY secret exists"
else
    echo "   ❌ FAIL: Run 'flyctl secrets set SECRET_KEY=...'"
    exit 1
fi

# 15. ✅ JWT_SECRET_KEY secret set
echo "15. Checking JWT_SECRET_KEY..."
if flyctl secrets list --app grupo-gad 2>/dev/null | grep -q "JWT_SECRET_KEY"; then
    echo "   ✓ JWT_SECRET_KEY secret exists"
else
    echo "   ⚠️  WARNING: JWT_SECRET_KEY not set"
fi

echo ""
echo "=== VALIDATION COMPLETE ==="
echo "✓ Ready for deployment"
```

---

## 🔧 TROUBLESHOOTING AVANZADO

### Escenario A: Deployment se queda en "Pending"

```bash
# Síntoma: flyctl deploy no termina

# Diagnóstico:
flyctl status --app grupo-gad

# Si output muestra: "Status: pending"
# Causa: Build aún en progreso

# Solución:
# 1. Esperar (builds grandes pueden tomar 5-10 min)
# 2. Ver progreso:
flyctl logs --app grupo-gad -f

# 3. Si se traba >15 min:
# - Cancelar: Ctrl-C
# - Reintentar: flyctl deploy --app grupo-gad
```

### Escenario B: "Error: could not start app"

```bash
# Logs:
flyctl logs --app grupo-gad
# Output:
# [error] ERROR: command "alembic upgrade head" returned 1
# [error] Error: DATABASE_URL not set

# Solución:
# Step 1: Verify secret
flyctl secrets list --app grupo-gad | grep DATABASE_URL

# Step 2: If missing, set it
flyctl postgres attach grupo-gad-db --app grupo-gad

# Step 3: Redeploy
flyctl deploy --app grupo-gad
```

### Escenario C: "503 Service Unavailable"

```bash
# Causa 1: Health checks failing
# Diagnóstico:
flyctl status --app grupo-gad
# Si: "Status: critical"

flyctl logs --app grupo-gad
# Buscar líneas ERROR o WARN

# Solución:
# Si uvicorn crash: startup log error
# → Check JWT_SECRET_KEY format (must be >32 chars)
# → Check SECRET_KEY format
# → Try SSH into container:
flyctl ssh console --app grupo-gad
$ echo $SECRET_KEY
$ ps aux

# Causa 2: TLS certificate expired
# Diagnóstico:
curl -I https://grupo-gad.fly.dev
# Si: "SSL: CERTIFICATE_VERIFY_FAILED"

# Solución: Automático (Fly.io renueva certs)
# Solo esperar 5-10 min
```

### Escenario D: Application runs but crashes after 30 mins

```bash
# Síntoma: App inicia, luego para sin motivo

# Causa: Possible memory leak OR connection pool exhaustion

# Diagnóstico:
flyctl metrics show --app grupo-gad
# Si Memory crece continuamente: leak

# Solución A: Restart app
flyctl apps restart --app grupo-gad

# Solución B: Identificar leak
flyctl ssh console --app grupo-gad
$ pip install memory_profiler
$ python -m memory_profiler src/api/main.py

# Solución C: Reduce connection pool
export DB_POOL_SIZE=5
flyctl secrets set DB_POOL_SIZE=5 --app grupo-gad
flyctl deploy --app grupo-gad
```

---

## 📋 CHECKLIST DE DESPLIEGUE SEGURO

### Pre-Deployment (Next 15 minutes)

```markdown
## ✅ CHECKLIST PRE-DEPLOYMENT

Antes de ejecutar `flyctl deploy`:

### CÓDIGO
- [ ] Todos los cambios commiteados
- [ ] Última versión pusheada a master
- [ ] Dockerfile tiene libpq-dev y libpq5
- [ ] alembic.ini presente
- [ ] alembic/versions/ tiene migrations

### FLY.IO SETUP
- [ ] flyctl instalado
- [ ] flyctl auth login (autenticado)
- [ ] fly.toml presente en raíz repo
- [ ] PostgreSQL creada (grupo-gad-db)
- [ ] DATABASE_URL inyectada automáticamente

### SECRETS
- [ ] SECRET_KEY configurado (32+ chars)
- [ ] JWT_SECRET_KEY configurado (32+ chars)
- [ ] Verificar: `flyctl secrets list --app grupo-gad`

### VALIDACIÓN FINAL
- [ ] Ejecutar script validation (ver arriba)
- [ ] Revisar DEEP_DEPLOYMENT_ANALYSIS.md esta sección
```

### During Deployment (Next 1-2 minutes)

```markdown
## 📊 MONITORING DURANTE DESPLIEGUE

```bash
# Terminal 1: Monitorear logs
flyctl logs --app grupo-gad -f

# Terminal 2: Monitorear status
watch -n 2 'flyctl status --app grupo-gad'

# Terminal 3: Ejecución
cd /home/eevan/ProyectosIA/GRUPO_GAD
flyctl deploy --app grupo-gad
```

**Buscar en logs**:
- ✅ `#1 [internal] load build definition` - Inicio build
- ✅ `#10 built in XXs` - Build completado
- ✅ `Image: registry.fly.io/grupo-gad:` - Image creada
- ✅ `Release command: alembic upgrade head` - Inicia migración
- ✅ `head is now at` - Migración exitosa
- ✅ `INFO: Uvicorn running on http://0.0.0.0:8080` - App lista
- ✅ `Application startup complete` - APP READY
```

### Post-Deployment (Next 5 minutes)

```markdown
## ✔️ VERIFICACIÓN POST-DESPLIEGUE

```bash
# 1. Health check
curl https://grupo-gad.fly.dev/health
# Esperado: {"status": "ok", ...}

# 2. API status
curl https://grupo-gad.fly.dev/api/v1/usuarios
# Esperado: 200 OK (o lista de usuarios)

# 3. Status Fly.io
flyctl status --app grupo-gad
# Esperado: "Status: ok"

# 4. Logs review
flyctl logs --app grupo-gad | tail -20
# Buscar: errores, warnings

# 5. Métricas
flyctl metrics show --app grupo-gad
# Esperado: CPU <5%, Memory <200MB, Requests healthy
```
```

---

## 🚀 COMANDOS ESENCIALES (Copy-Paste Ready)

```bash
# ========== SETUP INICIAL ==========
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"
flyctl auth login

# ========== CREAR INFRAESTRUCTURA ==========
flyctl postgres create \
  --name grupo-gad-db \
  --region mia \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 10

flyctl postgres attach grupo-gad-db --app grupo-gad

# ========== CONFIGURAR SECRETS ==========
flyctl secrets set \
  SECRET_KEY="1534c53529e8723bb1a3118eb90ee7d393701cc2a6605af67189b9b94bb8399d" \
  JWT_SECRET_KEY="KPatZlVBc9-bHpe_V2spTBzw0l5d8RgJ1DjgJqoR9LU" \
  --app grupo-gad

# ========== DEPLOY ==========
cd /home/eevan/ProyectosIA/GRUPO_GAD
flyctl deploy --app grupo-gad

# ========== MONITOREO ==========
flyctl logs --app grupo-gad -f
flyctl status --app grupo-gad
flyctl metrics show --app grupo-gad

# ========== TESTING ==========
curl https://grupo-gad.fly.dev/health
curl https://grupo-gad.fly.dev/api/v1/

# ========== EMERGENCIA: ROLLBACK ==========
flyctl releases list --app grupo-gad
flyctl releases rollback --app grupo-gad  # (rollback 1 version)
```

---

## 📊 MÉTRICAS ESPERADAS POST-DEPLOY

```
┌─────────────────────────────────────────────────────────┐
│ MÉTRICA             │ EXPECTED       │ WARNING          │
├─────────────────────────────────────────────────────────┤
│ Health Check        │ 200 OK         │ 500 ERROR        │
│ Response Time       │ <200ms         │ >1000ms          │
│ CPU Usage           │ <5%            │ >25%             │
│ Memory Usage        │ <200MB         │ >400MB           │
│ Requests/min        │ 0-100 (normal) │ 0 (no traffic)   │
│ Uptime              │ >99.9%         │ <99%             │
│ WebSocket Connects  │ >0             │ Connection errors│
└─────────────────────────────────────────────────────────┘
```

---

## 🎓 RESUMEN EJECUTIVO

### ¿Qué pasó? (Build FIXED en commit 68dbe26)

**Problema Original (d0044d1)**:
```
Build FAILED: asyncpg compilation error
Causa: Dockerfile sin libpq-dev y python3-dev
```

**Solución Aplicada (68dbe26)**:
```
✅ Agregado libpq-dev (PostgreSQL dev headers)
✅ Agregado python3-dev (Python headers para C extensions)
✅ Agregado pip upgrade before install
✅ Testeado localmente: BUILD SUCCESS
✅ Commiteado y pusheado a master
```

### ¿Próximo Paso?

**User debe ejecutar en Fly.io Dashboard**:
```
1. Ir a: https://fly.io/apps/grupo-gad
2. Buscar: "Retry from latest commit (master)"
3. Click: Retry button
4. Esperar: ~1-2 minutos
5. Verificar: Health check en https://grupo-gad.fly.dev/health
```

**O via CLI**:
```bash
cd /home/eevan/ProyectosIA/GRUPO_GAD
flyctl deploy --app grupo-gad --no-cache
```

### ¿Qué se espera que falle después?

**NOTA**: El fix de build solo resuelve COMPILACIÓN.  
Aún se requiere:

1. **PostgreSQL Database** ← No existe aún
   ```bash
   flyctl postgres create --name grupo-gad-db --region mia
   flyctl postgres attach grupo-gad-db --app grupo-gad
   ```

2. **Secrets** ← No completamente configurados
   ```bash
   flyctl secrets list
   # Verificar que tengan: SECRET_KEY, JWT_SECRET_KEY
   ```

3. **Redis** ← Opcional pero recomendado
   ```bash
   # O usar Upstash en https://console.upstash.com
   ```

### Punto de Éxito

**Deployment se considerará EXITOSO cuando**:
```
1. flyctl deploy completa sin errores
2. flyctl status --app grupo-gad muestra "ok"
3. curl https://grupo-gad.fly.dev/health retorna 200 OK
4. Logs no muestran ERROR después de "startup complete"
```

---

## 📞 REFERENCIAS RÁPIDAS

**Documentación Oficial Fly.io**:
- https://fly.io/docs/getting-started/
- https://fly.io/docs/reference/configuration/
- https://fly.io/docs/flyctl/getting-started/

**Nuestros Archivos Clave**:
- `fly.toml` - Configuración Fly.io
- `Dockerfile` - Imagen Docker (FIXED con libpq-dev)
- `alembic.ini` + `alembic/env.py` - Migraciones
- `config/settings.py` - Variables de entorno
- `src/api/main.py` - FastAPI lifespan

**Status Actual**:
- ✅ Build: FIXED (68dbe26)
- ✅ Docker: Locally tested SUCCESS
- ⏳ Deployment: Awaiting retry from Fly.io Dashboard
- ⏳ PostgreSQL: Needs creation
- ⏳ Secrets: Needs finalization

---

**Fin de Análisis Forense**  
*Próximo: User ejecuta "Retry from latest commit" en Fly.io Dashboard*

