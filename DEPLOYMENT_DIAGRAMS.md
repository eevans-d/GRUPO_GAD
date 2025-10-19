# 📊 DIAGRAMAS & FLOWCHARTS - Despliegue Fly.io

## 1. ARQUITECTURA GENERAL (Después del Despliegue)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTE                                     │
│                      (Navegador/CLI)                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/HTTPS
                             │
        ┌────────────────────▼─────────────────────┐
        │   Fly.io Load Balancer (Miami)           │
        │   - TLS Termination                      │
        │   - Port 80 → redirect HTTPS             │
        │   - Port 443 → 8080                      │
        │   - Health checks /health (15s)          │
        └────────────────────┬─────────────────────┘
                             │ :8080 internal
        ┌────────────────────▼─────────────────────┐
        │   FastAPI Container (grupo-gad)          │
        │   ├─ Uvicorn 1 worker                    │
        │   ├─ Python 3.12                         │
        │   ├─ Port: 8080                          │
        │   └─ Lifespan:                           │
        │      ├─ DB Pool (10 connections)         │
        │      ├─ WebSocket Manager                │
        │      └─ Cache Service (Redis)            │
        └────────────────────┬─────────────────────┘
                             │
        ┌────────────────────┴──────────────────┬──────────────────┐
        │                                       │                  │
        ▼                                       ▼                  ▼
   PostgreSQL                              Redis/Upstash      Metrics
   (grupo-gad-db)                          (Cache Layer)      (Prometheus)
   ├─ Database: gcp_db
   ├─ User: gcp_user
   └─ Connection Pool
```

---

## 2. FASES DE DESPLIEGUE (Timeline)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    DEPLOYMENT PHASES TIMELINE                        ║
╠═══════════════════════════════════════════════════════════════════════╣

FASE 1: BUILD (Construcción de Imagen)
┌─────────────────────────────────────────────────────────────────────┐
│ 0:00  $ flyctl deploy --app grupo-gad                              │
│       └─ CLI contact Fly.io API                                    │
│                                                                     │
│ 0:05  Docker Build Stage 1: Builder                                │
│       ├─ FROM python:3.12-slim                                     │
│       ├─ apt-get install gcc, libpq-dev, python3-dev  ✅ FIXED    │
│       ├─ pip install -r requirements.txt (45s)                     │
│       └─ (asyncpg compiles successfully now) ✅                    │
│                                                                     │
│ 0:50  Docker Build Stage 2: Runtime                                │
│       ├─ FROM python:3.12-slim                                     │
│       ├─ apt-get install curl, libpq5  ✅ FIXED                    │
│       ├─ COPY /install from builder                                │
│       ├─ COPY alembic/, config/, src/, templates/                 │
│       └─ Image ready: ~185MB                                       │
│                                                                     │
│ 1:00  ✅ BUILD COMPLETE                                            │
└─────────────────────────────────────────────────────────────────────┘

FASE 2: PUSH (Envío a Registry)
┌─────────────────────────────────────────────────────────────────────┐
│ 1:00  Push image to registry.fly.io                                │
│       ├─ Upload 185MB image                                        │
│       ├─ Register in Fly.io artifact store                         │
│       └─ Retorna: registry.fly.io/grupo-gad:build.abc123           │
│                                                                     │
│ 1:15  ✅ IMAGE PUSHED                                              │
└─────────────────────────────────────────────────────────────────────┘

FASE 3: RELEASE (Migraciones pre-deployment)
┌─────────────────────────────────────────────────────────────────────┐
│ 1:20  Spin up RELEASE MACHINE                                      │
│       ├─ Crear máquina TEMPORAL para release command               │
│       ├─ Inyectar secrets (DATABASE_URL, etc)                      │
│       ├─ Mount Dockerfile CMD → release_command                    │
│       └─ Execute: alembic upgrade head                             │
│                                                                     │
│ 1:25  $ alembic upgrade head                                       │
│       ├─ Read alembic.ini                                          │
│       ├─ Import src.api.models                                     │
│       ├─ Connect to DATABASE_URL (PostgreSQL)                      │
│       ├─ Check alembic_version table                               │
│       ├─ Run pending migrations (if any)                           │
│       └─ Return: "head is now at XYZ"                              │
│                                                                     │
│ 1:30  ✅ MIGRATIONS COMPLETE                                       │
│       Kill release machine (no longer needed)                      │
└─────────────────────────────────────────────────────────────────────┘

FASE 4: STARTUP (Arranque de Aplicación)
┌─────────────────────────────────────────────────────────────────────┐
│ 1:35  Spin up PRODUCTION MACHINE                                   │
│       ├─ new machine in mia region                                 │
│       ├─ Inyectar secrets (DATABASE_URL, REDIS_URL, etc)           │
│       └─ Mount image from registry                                 │
│                                                                     │
│ 1:40  $ CMD: uvicorn src.api.main:app ...                         │
│       ├─ 0s Import FastAPI, SQLAlchemy modules                     │
│       ├─ 1s Load settings (read env vars)                          │
│       ├─ 2s init_db(database_url)                                  │
│       │   └─ Create async_engine connection pool                   │
│       ├─ 3s await websocket_event_emitter.start()                 │
│       ├─ 4s initialize_websocket_integrator()                      │
│       ├─ 5s initialize_metrics() if enabled                        │
│       └─ READY TO SERVE (yield en lifespan)                        │
│                                                                     │
│ 1:45  ✅ APPLICATION STARTUP COMPLETE                              │
└─────────────────────────────────────────────────────────────────────┘

FASE 5: HEALTH CHECKS (Validar disponibilidad)
┌─────────────────────────────────────────────────────────────────────┐
│ 1:45  Grace period: 30s (waiting for app stability)                │
│       ├─ Health check endpoint /health is disabled during grace   │
│       └─ (prevents false failures during startup)                 │
│                                                                     │
│ 2:15  First health check attempt #1                                │
│       ├─ GET /health                                               │
│       ├─ Timeout: 10s                                              │
│       └─ Result: 200 OK ✅                                         │
│                                                                     │
│ 2:30  Health check #2: 200 OK ✅                                   │
│ 2:45  Health check #3: 200 OK ✅                                   │
│                                                                     │
│ 2:45  ✅ 3/3 CHECKS PASSED - Machine is HEALTHY                    │
└─────────────────────────────────────────────────────────────────────┘

FASE 6: ROLLING DEPLOYMENT (Cambio de tráfico)
┌─────────────────────────────────────────────────────────────────────┐
│ 2:50  Load Balancer redirects NEW requests to new machine          │
│       ├─ In-flight requests continue to OLD machine                │
│       ├─ NEW requests → NEW machine (grupo-gad v2)                 │
│       └─ Gradual traffic shift (rolling strategy)                  │
│                                                                     │
│ 3:00  All traffic on NEW machine                                   │
│       ├─ OLD machine graceful shutdown                             │
│       ├─ Send SIGINT to uvicorn                                    │
│       ├─ Close DB connections properly                             │
│       ├─ Shutdown WebSocket connections                            │
│       └─ OLD machine killed after timeout                          │
│                                                                     │
│ 3:05  ✅ DEPLOYMENT COMPLETE                                       │
│       ├─ New version LIVE: grupo-gad.fly.dev                       │
│       ├─ Traffic flowing normally                                  │
│       └─ Old machine removed from cluster                          │
└─────────────────────────────────────────────────────────────────────┘

TOTAL TIME: ~3 minutes (180 seconds)

╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 3. BUILD PHASE: MULTI-STAGE DEEP DIVE

```
┌──────────────────────────────────────────────────────────┐
│         DOCKERFILE BUILD SEQUENCE (FIXED v2)             │
└──────────────────────────────────────────────────────────┘

STAGE 1: BUILDER (Compilación - Final: 450 MB)
═════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ FROM python:3.12-slim AS builder                        │
│ ├─ Size: 140 MB                                         │
│ ├─ OS: Debian trixie (slim)                             │
│ └─ Python: 3.12.3                                       │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ ENV PYTHONDONTWRITEBYTECODE=1                           │
│ ENV PYTHONUNBUFFERED=1                                  │
│ ENV PIP_NO_CACHE_DIR=1                                  │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ RUN apt-get update && apt-get install -y               │
│   gcc g++ make          ← C compiler                    │
│   libpq-dev ✅ FIXED    ← PostgreSQL dev headers        │
│   python3-dev ✅ FIXED  ← Python dev headers            │
│                                                         │
│ Installs:                                               │
│ ├─ gcc (GNU C Compiler)                                 │
│ ├─ g++ (GNU C++ Compiler)                               │
│ ├─ make (Build tool)                                    │
│ ├─ libpq-dev (PostgreSQL client headers)                │
│ │  └─ Includes: libpq.h, pg_config, etc                │
│ └─ python3-dev (Python headers: Python.h, etc)          │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ COPY requirements.txt .                                 │
│ RUN pip install --upgrade pip                           │
│ RUN pip install --prefix=/install -r requirements.txt  │
│                                                         │
│ Compilation Process:                                    │
│ ├─ asyncpg                                              │
│ │  ├─ Searches for pre-compiled wheel                  │
│ │  ├─ If not found → compiles from source              │
│ │  ├─ Finds libpq-dev headers ✅ NOW SUCCESS           │
│ │  └─ Builds .so library (PostgreSQL bindings)         │
│ │                                                      │
│ ├─ pydantic                                             │
│ │  ├─ Fast C implementation                             │
│ │  ├─ Finds python3-dev headers ✅ NOW SUCCESS          │
│ │  └─ Builds .so for validation                        │
│ │                                                      │
│ └─ uvloop                                               │
│    ├─ High-performance event loop                       │
│    ├─ Finds gcc + make ✅                               │
│    └─ Builds libuv integration                          │
│                                                         │
│ Size after pip install: ~310 MB                         │
└─────────────────────────────────────────────────────────┘
         ▼
STAGE 1 FINAL: 450 MB (python + compilers + dev headers + wheels)
   ↓ (DISCARDED after copying installed packages)


STAGE 2: RUNTIME (Ejecución - Final: 185 MB)
═════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ FROM python:3.12-slim                                  │
│ ├─ Size: 140 MB                                         │
│ ├─ Clean slate (no compilers!)                          │
│ └─ Will COPY precompiled wheels from builder            │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ RUN apt-get install -y                                  │
│   curl           ← For health checks                    │
│   ca-certificates ← For HTTPS                           │
│   libpq5 ✅ FIXED ← PostgreSQL client library            │
│                                                         │
│ Note: NO gcc, NO libpq-dev (not needed for runtime)     │
│       Size: only 10 MB added                            │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ COPY --from=builder /install /usr/local                │
│   ├─ asycpg .so ← Precompiled PostgreSQL bindings      │
│   ├─ pydantic .so ← Precompiled validators              │
│   ├─ uvloop .so ← Precompiled event loop                │
│   ├─ fastapi, sqlalchemy, uvicorn (pure Python)        │
│   └─ All 21 packages from requirements.txt              │
│                                                         │
│ Size: 35 MB (already compiled!)                         │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ COPY alembic.ini ./                                     │
│ COPY alembic ./alembic                                  │
│ COPY config ./config                                    │
│ COPY src ./src                                          │
│ COPY dashboard ./dashboard                              │
│ COPY templates ./templates                              │
│                                                         │
│ Size: ~2 MB (application code + assets)                 │
└─────────────────────────────────────────────────────────┘
         ▼
STAGE 2 FINAL: 185 MB (140 + 10 + 35 MB)

✅ MULTI-STAGE OPTIMIZATION:
   Reduced: 450 MB (full builder) → 185 MB (runtime only)
   Saving: 265 MB = 59% reduction
```

---

## 4. DEPENDENCY COMPILATION REQUIREMENTS

```
┌──────────────────────────────────────────────────────────┐
│    C EXTENSION PACKAGES & COMPILATION REQUIREMENTS       │
└──────────────────────────────────────────────────────────┘

PACKAGE: asyncpg (PostgreSQL async driver)
┌──────────────────────────────────────────────────────────┐
│ What it does:                                            │
│   Connects Python to PostgreSQL asynchronously           │
│                                                          │
│ Compilation Requirements:                                │
│   ✅ gcc (C compiler)                                    │
│   ✅ libpq-dev (PostgreSQL headers)                      │
│   └─ Includes: libpq.h, pg_config utility               │
│                                                          │
│ Build Process:                                           │
│   1. pip searches for wheel for python-3.12-linux-x64   │
│   2. If not found → downloads source tarball             │
│   3. $ gcc -I/usr/include/postgresql ...                │
│   4. Compiles → asyncpg.cpython-312-x86_64-linux-gnu.so │
│   5. Installs .so into site-packages                     │
│                                                          │
│ If libpq-dev missing:                                    │
│   ✗ ERROR: pg_config: command not found                 │
│   ✗ ERROR: Could not build wheels for asyncpg           │
│   └─ Build FAILS immediately                             │
└──────────────────────────────────────────────────────────┘

PACKAGE: pydantic (Data validation)
┌──────────────────────────────────────────────────────────┐
│ What it does:                                            │
│   Fast data validation using Pydantic v2 C core         │
│                                                          │
│ Compilation Requirements:                                │
│   ✅ gcc (C compiler)                                    │
│   ✅ python3-dev (Python development headers)            │
│   └─ Includes: Python.h, pythonrun.h                    │
│                                                          │
│ If python3-dev missing:                                 │
│   ✗ ERROR: fatal error: Python.h: No such file          │
│   ✗ ERROR: Could not build wheels for pydantic          │
│   └─ Build FAILS during C extension compilation         │
└──────────────────────────────────────────────────────────┘

PACKAGE: uvloop (Event loop replacement)
┌──────────────────────────────────────────────────────────┐
│ What it does:                                            │
│   Drop-in replacement for asyncio (uses libuv)          │
│                                                          │
│ Compilation Requirements:                                │
│   ✅ gcc/g++ (C/C++ compiler)                            │
│   ✅ make (build tool)                                   │
│   └─ Uses: libuv library (async I/O)                    │
│                                                          │
│ If gcc/make missing:                                    │
│   ✗ ERROR: make: command not found                      │
│   ✗ ERROR: Failed to build uvloop                       │
│   └─ Build FAILS                                         │
└──────────────────────────────────────────────────────────┘

SUMMARY: BUILD REQUIREMENTS
┌──────────────────────────────────────────────────────────┐
│ Compiler Toolchain      │ For asyncpg, pydantic, uvloop │
├─────────────────────────┼──────────────────────────────┤
│ gcc/g++                 │ C/C++ compiler (REQUIRED)    │
│ make                    │ Build tool (REQUIRED)        │
│ libpq-dev               │ PostgreSQL headers (FIXED ✅) │
│ python3-dev             │ Python headers (FIXED ✅)    │
├─────────────────────────┼──────────────────────────────┤
│ BEFORE fix (d0044d1)    │ ✗ FAIL - Missing libpq-dev  │
│ AFTER fix (68dbe26)     │ ✅ SUCCESS - All present     │
└──────────────────────────┴──────────────────────────────┘
```

---

## 5. RELEASE PHASE: ALEMBIC MIGRATIONS

```
┌─────────────────────────────────────────────────────────┐
│          RELEASE_COMMAND EXECUTION FLOW                 │
│             (Before App Startup)                        │
└─────────────────────────────────────────────────────────┘

fly.toml Configuration:
┌─────────────────────────────────────────────────────────┐
│ [deploy]                                                │
│   release_command = "alembic upgrade head"              │
│   strategy = "rolling"                                  │
└─────────────────────────────────────────────────────────┘

Execution Timeline:
┌─────────────────────────────────────────────────────────┐
│ 1. Release Machine Created                              │
│    ├─ Temporary machine (exists only for this command) │
│    ├─ Same region: mia (Miami)                         │
│    └─ Image pulled from registry                       │
│                                                         │
│ 2. Secrets Injected                                     │
│    ├─ DATABASE_URL = "postgresql+asyncpg://..."        │
│    ├─ REDIS_URL = "redis://..."                        │
│    ├─ SECRET_KEY = "1534c535..."                       │
│    └─ (all 9+ secrets available)                       │
│                                                         │
│ 3. Release Command Starts                              │
│    ├─ CMD overridden: alembic upgrade head             │
│    ├─ Timeout: 30 seconds                              │
│    └─ stderr/stdout captured → logs                    │
│                                                         │
│ 4. Alembic Execution                                    │
│    │                                                    │
│    ├─ $ alembic upgrade head                           │
│    │   └─ Log: "Alembic env.py executing..."           │
│    │                                                    │
│    ├─ Read config: alembic.ini                         │
│    │   └─ sqlalchemy.url = "***" (from DATABASE_URL)  │
│    │                                                    │
│    ├─ Load metadata: src.api.models.Base.metadata      │
│    │   ├─ Import: Usuario, Efectivo, Tarea tables      │
│    │   └─ Log: "4 models detected"                     │
│    │                                                    │
│    ├─ Connect to PostgreSQL                            │
│    │   ├─ Connection string: DATABASE_URL              │
│    │   ├─ asyncpg dialect                              │
│    │   └─ Log: "Connected to database"                 │
│    │                                                    │
│    ├─ Check alembic_version table                      │
│    │   ├─ Query: SELECT version_num FROM alembic_version
│    │   ├─ If table missing: CREATE TABLE               │
│    │   └─ Log: "alembic_version table present"         │
│    │                                                    │
│    ├─ Compare current vs. target                       │
│    │   ├─ Current: version 3 (last migration)          │
│    │   ├─ Target: version 3 (head)                     │
│    │   └─ Result: "No migrations to apply" (normal)    │
│    │                                                    │
│    └─ Log: "head is now at abc123def"                  │
│                                                         │
│ 5. Release Command Exits                               │
│    ├─ Exit code: 0 (success)                           │
│    ├─ Logs available in flyctl logs                    │
│    └─ Release machine destroyed                        │
│                                                         │
│ 6. Decisions                                            │
│    ├─ If exit=0 (success)                              │
│    │  └─ Proceed: Create production machine            │
│    │                                                    │
│    └─ If exit!=0 (failure)                             │
│       ├─ ABORT deployment                              │
│       ├─ Keep previous version active                  │
│       ├─ Release machine destroyed                     │
│       └─ Logs: "release command failed"                │
└─────────────────────────────────────────────────────────┘

POTENTIAL FAILURES:

┌─────────────────────────────────────────────────────────┐
│ Failure 1: DATABASE_URL Not Set                         │
│ ────────────────────────────────────────────────────────│
│ Error: sqlalchemy.exc.ArgumentError: Could not parse   │
│        connection string                               │
│ Fix: flyctl secrets set DATABASE_URL="..." --app ...   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Failure 2: PostgreSQL Not Accessible                   │
│ ────────────────────────────────────────────────────────│
│ Error: asyncpg.TooManyConnectionsError                 │
│        Could not connect to server                     │
│ Fix: flyctl postgres create --name db --region mia     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Failure 3: Timeout (>30s)                              │
│ ────────────────────────────────────────────────────────│
│ Error: Release command timeout                         │
│ Fix: Increase grace_period in fly.toml                 │
└─────────────────────────────────────────────────────────┘
```

---

## 6. RUNTIME PHASE: APPLICATION STARTUP

```
┌─────────────────────────────────────────────────────────┐
│          UVICORN STARTUP & LIFESPAN EVENTS              │
└─────────────────────────────────────────────────────────┘

Container Startup:
┌─────────────────────────────────────────────────────────┐
│ $ CMD: uvicorn src.api.main:app \                       │
│        --host 0.0.0.0 \                                │
│        --port 8080 \                                   │
│        --workers 1 \                                   │
│        --loop uvloop                                   │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ [0] IMPORT PHASE (2-3 seconds)                          │
│ ├─ uvicorn loads src.api.main                           │
│ ├─ FastAPI module instantiation                         │
│ ├─ Import all routers                                   │
│ ├─ Load database models                                 │
│ └─ Log: "Uvicorn server process started [pid]"          │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ [1] LIFESPAN STARTUP EVENT (4-5 seconds)               │
│                                                         │
│ @asynccontextmanager                                   │
│ async def lifespan(app: FastAPI):                       │
│     # STARTUP (before yielding)                         │
│                                                         │
│     ├─ get_settings()                                   │
│     │  └─ Read environment variables                    │
│     │     ├─ SECRET_KEY=...                             │
│     │     ├─ JWT_SECRET_KEY=...                         │
│     │     ├─ DATABASE_URL=...                           │
│     │     └─ REDIS_URL=...                              │
│     │                                                   │
│     ├─ _settings.assemble_db_url()                      │
│     │  └─ Transform postgresql:// to postgresql+asyncpg://
│     │                                                   │
│     ├─ init_db(db_url)  [TIME: 2s]                      │
│     │  ├─ Create async_engine                           │
│     │  ├─ Create connection pool                        │
│     │  │  ├─ pool_size = 10                             │
│     │  │  ├─ max_overflow = 20                          │
│     │  │  ├─ pool_timeout = 30s                         │
│     │  │  └─ pool_recycle = 3600s                       │
│     │  ├─ Test connection to PostgreSQL                 │
│     │  ├─ Verify database exists                        │
│     │  └─ Log: "Conexión a la BD establecida"           │
│     │                                                   │
│     ├─ await websocket_event_emitter.start()  [TIME: 0.5s]
│     │  ├─ Initialize WebSocket manager                 │
│     │  ├─ Start event bus                               │
│     │  └─ Prepare for WS connections                    │
│     │                                                   │
│     ├─ initialize_websocket_integrator()  [TIME: 0.5s]  │
│     │  ├─ Link models to WebSocket events               │
│     │  └─ Setup model → WS broadcast                    │
│     │                                                   │
│     ├─ initialize_metrics() [TIME: 0.1s]                │
│     │  ├─ Setup Prometheus metrics                      │
│     │  ├─ Create /metrics endpoint                      │
│     │  └─ Start collecting stats                        │
│     │                                                   │
│     └─ yield  ← SERVER NOW ACCEPTS REQUESTS             │
│                                                         │
│     # SHUTDOWN (called on SIGINT/SIGTERM)              │
│     └─ cleanup handlers (see below)                     │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ [2] READY TO SERVE (Log messages)                       │
│                                                         │
│ [info] INFO: Uvicorn running on http://0.0.0.0:8080   │
│ [info] INFO: Application startup complete              │
│                                                         │
│ Now accepting HTTP requests on:                        │
│ ├─ http://0.0.0.0:8080 (internal)                      │
│ ├─ https://grupo-gad.fly.dev (external via LB)         │
│ └─ WebSocket: wss://grupo-gad.fly.dev/ws/connect      │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ [3] HEALTH CHECKS PASS (Grace period complete)         │
│                                                         │
│ GET /health                                             │
│ Response: 200 OK                                        │
│ {                                                       │
│   "status": "ok",                                      │
│   "timestamp": "2025-10-19T12:34:56Z",                 │
│   "uptime": 5.234                                      │
│ }                                                       │
│                                                         │
│ Result: MACHINE IS HEALTHY ✅                           │
└─────────────────────────────────────────────────────────┘


GRACEFUL SHUTDOWN (on SIGINT/SIGTERM):
┌─────────────────────────────────────────────────────────┐
│ Signal Handler: SIGINT (Ctrl-C or Fly.io shutdown)      │
│ └─ Uvicorn stops accepting NEW connections             │
│                                                         │
│ Graceful Shutdown Sequence (max 30s):                  │
│ ├─ [1] Wait for in-flight requests to complete         │
│ ├─ [2] lifespan finally block executes                 │
│ │       ├─ await websocket_manager.shutdown()          │
│ │       ├─ await database.dispose()                    │
│ │       └─ close connection pools                      │
│ ├─ [3] All connections closed                          │
│ └─ [4] Process exits (code 0)                          │
│                                                         │
│ If >30s: SIGKILL sent (forced shutdown)                │
└─────────────────────────────────────────────────────────┘
```

---

## 7. HEALTH CHECK FLOW

```
┌─────────────────────────────────────────────────────────┐
│              HEALTH CHECK MECHANISM                     │
└─────────────────────────────────────────────────────────┘

Configuration (fly.toml):
┌─────────────────────────────────────────────────────────┐
│ [[services.http_checks]]                                │
│   interval = "15s"        # Check every 15 seconds      │
│   timeout = "10s"         # Wait max 10s for response   │
│   grace_period = "30s"    # Wait 30s before first check │
│   restart_limit = 3       # Restart after 3 failures    │
│   method = "GET"                                        │
│   path = "/health"                                      │
│   protocol = "http"                                     │
└─────────────────────────────────────────────────────────┘

Timeline:
┌─────────────────────────────────────────────────────────┐
│ Time    Event                    Status    Action       │
├─────────────────────────────────────────────────────────┤
│ 0:00    Container starts         -         -            │
│         Application initializing                         │
│                                                         │
│ 0:30    Grace period ends        READY     Check #1     │
│         First health check sent                          │
│                                                         │
│         GET /health                                    │
│         Timeout: 10s                                    │
│         Response: 200 OK ✅                             │
│         Result: PASS (1/3)                              │
│                                                         │
│ 0:45    Health check #2          OK        PASS (2/3)   │
│         GET /health → 200 OK                            │
│                                                         │
│ 1:00    Health check #3          OK        PASS (3/3)   │
│         GET /health → 200 OK                            │
│                                                         │
│ 1:05    ✅ MACHINE HEALTHY                              │
│         All checks passed                               │
│         LB starts routing traffic                       │
│                                                         │
├─────────────────────────────────────────────────────────┤
│              IF HEALTH CHECK FAILS                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 0:45    Check #1: FAIL 😞                               │
│         GET /health → 500 ERROR                         │
│         Reason: Uvicorn not ready yet                   │
│         Action: retry in 15s                            │
│                                                         │
│ 1:00    Check #2: FAIL 😞                               │
│         GET /health → 503 SERVICE UNAVAILABLE           │
│         Reason: DB connection pool error                │
│         Action: retry in 15s                            │
│                                                         │
│ 1:15    Check #3: FAIL 😞                               │
│         GET /health → Connection Refused                │
│         Reason: Process crashed                         │
│         Action: restart_limit reached → KILL + RESTART  │
│                                                         │
│ 1:20    Container restarted                             │
│         [info] Starting application again               │
│         New check counter: 0/3                          │
│         Grace period: 30s                               │
│                                                         │
│ 1:50    Check #1 (restarted): PASS ✅                   │
│         Cycle repeats...                                │
│                                                         │
│ OR (continuous failures):                               │
│                                                         │
│ After 10+ restarts → Machine killed                     │
│ Error: "Machine crashed: health check failures"         │
│ Action: Manual investigation required                   │
│         flyctl ssh console --app grupo-gad              │
└─────────────────────────────────────────────────────────┘

Health Check Endpoint:
┌─────────────────────────────────────────────────────────┐
│ @app.get("/health")                                    │
│ async def health_check() -> dict:                      │
│     return {                                            │
│         "status": "ok",                                 │
│         "timestamp": datetime.utcnow().isoformat(),     │
│         "uptime": time.time() - app.state.start_time   │
│     }                                                   │
│                                                         │
│ Response: 200 OK (always, as long as running)          │
│                                                         │
│ Fly.io interprets:                                      │
│ ├─ 2xx (200-299) → HEALTHY ✅                           │
│ ├─ 3xx, 4xx, 5xx → UNHEALTHY ❌                         │
│ └─ Timeout → UNHEALTHY ❌                               │
└─────────────────────────────────────────────────────────┘
```

---

## 8. SECRETS INJECTION & TIMING

```
┌─────────────────────────────────────────────────────────┐
│         SECRETS LIFECYCLE IN FLY.IO                     │
└─────────────────────────────────────────────────────────┘

Stored in Fly.io:
┌─────────────────────────────────────────────────────────┐
│ flyctl secrets set \                                    │
│   SECRET_KEY="..." \                                    │
│   JWT_SECRET_KEY="..." \                                │
│   DATABASE_URL="..." \                                  │
│   --app grupo-gad                                       │
│                                                         │
│ Stored in encrypted vault:                              │
│ grupo-gad/secrets/SECRET_KEY                            │
│ grupo-gad/secrets/JWT_SECRET_KEY                        │
│ grupo-gad/secrets/DATABASE_URL                          │
│ ...                                                     │
└─────────────────────────────────────────────────────────┘

When Machine Starts:
┌─────────────────────────────────────────────────────────┐
│ 1. Fly.io provisioning orchestrator                     │
│    ├─ Select region: mia                                │
│    ├─ Allocate resources: 1 CPU, 512MB RAM              │
│    └─ Launch VM                                         │
│                                                         │
│ 2. Secrets injection (BEFORE app starts)               │
│    ├─ Fetch encrypted secrets from vault                │
│    ├─ Decrypt (using VM's ephemeral key)                │
│    ├─ Write to process environment (not disk!)          │
│    │  ├─ $SECRET_KEY                                    │
│    │  ├─ $JWT_SECRET_KEY                                │
│    │  ├─ $DATABASE_URL                                  │
│    │  └─ (ALL 9+ secrets available)                     │
│    └─ secrets are NEVER written to disk                 │
│                                                         │
│ 3. Container image mounted                              │
│    ├─ Pull from registry.fly.io                         │
│    ├─ Mount as root filesystem                          │
│    └─ (Dockerfile CMD ready to execute)                │
│                                                         │
│ 4. CMD execution with secrets                           │
│    └─ $ ENV_VARS_INJECTED CMD...                        │
│       ├─ release_command (if deploy mode)               │
│       │  $ alembic upgrade head                         │
│       │  (can read $DATABASE_URL, $REDIS_URL)           │
│       │                                                 │
│       └─ Normal CMD (uvicorn)                           │
│          $ uvicorn src.api.main:app                    │
│          (settings.py reads $SECRET_KEY)                │
└─────────────────────────────────────────────────────────┘

Application Level:
┌─────────────────────────────────────────────────────────┐
│ config/settings.py                                      │
│                                                         │
│ class Settings(BaseSettings):                           │
│     SECRET_KEY: str  # Read from $SECRET_KEY env var   │
│     JWT_SECRET_KEY: str                                 │
│     DATABASE_URL: Optional[str]                         │
│     REDIS_URL: Optional[str]                            │
│     ...                                                 │
│                                                         │
│ # Pydantic automatic .env loading:                      │
│ # Priority:                                             │
│ # 1. os.environ (injected by Fly.io) ✅ USED            │
│ # 2. .env.production file                               │
│ # 3. .env file                                          │
│                                                         │
│ settings = Settings()                                   │
│ # Now can access: settings.SECRET_KEY, etc              │
└─────────────────────────────────────────────────────────┘

Validation:
┌─────────────────────────────────────────────────────────┐
│ At startup, src/api/main.py checks:                     │
│                                                         │
│ _settings = get_settings()  # Loads from env            │
│                                                         │
│ if not db_url:                                          │
│     raise RuntimeError("DATABASE_URL no configurada")   │
│ # If missing → 💥 Startup failure                       │
│                                                         │
│ if len(settings.SECRET_KEY) < 32:                       │
│     raise ValueError("SECRET_KEY too short")            │
│ # If invalid → 💥 Startup failure                       │
└─────────────────────────────────────────────────────────┘
```

---

**Documentación completa de diagramas finalizada.**  
*Ver DEEP_DEPLOYMENT_ANALYSIS.md para análisis en texto profundo.*

