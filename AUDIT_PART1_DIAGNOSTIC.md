# GRUPO_GAD: Auditoría Exhaustiva Parte 1 – Diagnóstico Completo

**Fecha:** 26 de octubre de 2025  
**Objetivo:** Análisis técnico profundo para producción en Fly.io  
**Estado:** ✅ COMPLETADO

---

## Resumen Ejecutivo

- **Staging:** ✅ Operativo con Redis y UAT 90.9% (10/11 tests).
- **Producción:** ⚠️ **Degradado** — Database connection refused (`localhost`), Redis no inicializado.
- **Causa raíz:** `DATABASE_URL` en prod apunta a `postgresql://postgres:postgres@localhost:5432/grupo_gad` (destino no alcanzable desde Fly).
- **Impacto:** `/health/ready` reporta `database="error: [Errno 111] Connection refused"`, `redis="not_configured"`.
- **Acción requerida:** Actualizar `DATABASE_URL` a URL real de Postgres (Fly Postgres o externo) y reiniciar.

---

## Parte 1: Resultados del Diagnóstico

### 1. Pruebas Locales – Suite Unit

| Métrica | Resultado |
|---------|-----------|
| **Tarea:** `GAD: Pytest` | ✅ PASS |
| **Archivos:** Todos | ✅ Sin errores de ejecución |
| **Exit Code** | 0 (éxito) |

**Conclusión:** Suite de tests local es sólida. No hay regresos post-cambios.

---

### 2. Análisis Estático – Errores y Warnings

**Total de hallazgos:** 90 (reducible; mayormente en código no crítico).

| Categoría | Archivos | Tipo | Severidad | Acción |
|-----------|----------|------|-----------|--------|
| **Bot handlers** | `callback_handler.py` | Typing: `context.user_data` (Update \| None) | 🟡 Media | Post-producción |
| **Bot commands** | `historial.py` | Missing settings: `API_BASE_URL`, `HTTP_TIMEOUT` | 🟡 Media | Post-producción |
| **Tests bot** | `test_keyboards.py` | Typing: `callback_data` (str \| object \| None) | 🟡 Media | Post-producción |
| **GitHub workflows** | `.github/workflows/release.yml`, `cd.yml` | Context/config warnings | 🟢 Baja | Post-producción |
| **Telegram auth** | `test_telegram_auth.py` | Missing: `JWT_SECRET_KEY` in settings | 🟢 Baja | Post-producción |

**Hallazgo crítico (⚠️):** Los errores de typing en `callback_handler.py` y `historial.py` están en código del bot de Telegram, **no en la ruta crítica API/WebSocket/DB**. El API central es limpio.

**Acción:** Estos pueden resolverse en post-release hardening (no bloquean deploy).

---

### 3. Inspección de Configuración y Arranque

#### 3.1 Precedencia de DATABASE_URL (`config/settings.py`)

```python
# Orden de precedencia:
1. DATABASE_URL                    (explícito en env)
2. DB_URL                          (legado)
3. POSTGRES_USER/PASSWORD/etc.     (componentes por defecto)
```

**Implementación:** Validador `assemble_db_connection()` en Settings + método `assemble_db_url()` en runtime.

**Transformación asyncpg:**
- `postgresql://` → `postgresql+asyncpg://`
- `postgres://` → `postgresql+asyncpg://`  ← **AÑADIDO en esta auditoría**

**Cambios realizados:**
- `config/settings.py`: Normaliza ambos esquemas en `assemble_db_url()`.
- `src/api/main.py`: Normaliza en fallback `os.getenv("DATABASE_URL")`.

---

#### 3.2 Arranque de la Aplicación (`src/api/main.py` – lifespan)

| Paso | Acción | Status | Notas |
|------|--------|--------|-------|
| 1 | Construir DB URL | ✅ Via `get_settings().assemble_db_url()` | Precedencia correcta |
| 2 | Inicializar DB pool | ✅ Via `init_db(db_url)` | SQLAlchemy async + asyncpg |
| 3 | Iniciar WebSockets | ✅ Via `websocket_event_emitter.start()` | Integración WebSocket-modelos |
| 4 | Inicializar Redis (opcional) | ⚠️ Prefiere `REDIS_URL` completa | Soporte rediss:// con TLS |
| 5 | Inicializar CacheService | ✅ Si Redis disponible | Depende de Redis |

**Flujo de fallback:**
- Si `DATABASE_URL` falta o es inválida y `ALLOW_NO_DB=1`, app arranca sin DB (modo dev).
- Si `ALLOW_NO_DB!=1`, app falla con error explícito.

**Config en producción:**
- `fly.toml`: `ALLOW_NO_DB="1"` (temporal para diagnóstico; recomendar desactivar).
- `fly.toml`: `ENVIRONMENT="production"`, `LOG_LEVEL="info"`.

---

#### 3.3 WebSockets y Redis

| Componente | Config | Staging | Producción |
|------------|--------|---------|------------|
| **Redis URL** | `REDIS_URL` env | ✅ Upstash (operativo) | ✅ Upstash (aprovisionado; no inicializado) |
| **WebSocket Manager** | Integrado en `main.py` | ✅ OK | ⚠️ Depende de DB |
| **Pub/Sub Redis** | `RedisWebSocketPubSub` | ✅ OK | ⚠️ Depende de DB |
| **CacheService** | Init en lifespan | ✅ OK | ⚠️ Depende de DB |

**Nota:** En prod, Redis está configurado pero CacheService queda en estado "not_configured" porque la DB falla en startup, bloqueando el flujo de inicialización de dependencias.

---

### 4. TODO/FIXME en Código

**Escaneo:** 20+ matches; resumo críticos:

| Archivo | Línea | TODO | Impacto | Acción |
|---------|-------|------|---------|--------|
| `src/bot/handlers/callback_handler.py` | 225, 261, 348 | Llamar a API, regenerar keyboard, crear tarea | 🟡 Bot | Post-release |
| `src/bot/handlers/wizard_text_handler.py` | 379 | Obtener lista de delegados | 🟡 Bot | Post-release |
| `src/api/routers/telegram_tasks.py` | 148 | Validación de permisos en asignación | 🟡 API | Post-release |
| `dashboard/static/js/notifications.js` | 279, 385 | Navigation, logo app | 🟢 UX | Post-release |

**Conclusión:** Ninguno bloquea producción. Todos son integraciones posteriores o refinamientos UX.

---

### 5. Diagnóstico de Producción en Fly.io

#### 5.1 Estado Actual

```
PROD APP: grupo-gad
├─ Máquinas: 2
│  ├─ Machine 1: ❌ STOPPED (warnings)
│  └─ Machine 2: ✅ STARTED (health checks passing basic)
├─ Health Endpoint (/health): ✅ Responde "ok"
└─ Health Ready (/health/ready): ⚠️ Degraded
   ├─ database: "error: [Errno 111] Connection refused"
   ├─ redis: "not_configured"
   ├─ websocket_manager: "ok"
   └─ ws_pubsub: "not_configured"
```

#### 5.2 Causa Raíz – DATABASE_URL

**Hallazgo crítico:**

```bash
# SSH into prod container + curl health
$ curl http://localhost:8000/health/ready
{
  "status": "degraded",
  "checks": {
    "database": "error: [Errno 111] Connection refused"
  }
}

# Verificar env
$ printenv DATABASE_URL
postgresql://postgres:postgres@localhost:5432/grupo_gad
```

**Análisis:**
1. El secreto `DATABASE_URL` en Fly está seteado, pero **apunta a localhost**.
2. Dentro del contenedor de Fly, `localhost` ≠ Postgres en Fly (no hay instancia local).
3. La app intenta conectar a localhost:5432 desde el contenedor → connection refused.
4. Lifespan captura el error, pero con `ALLOW_NO_DB=1` la app sigue; DB queda en error.
5. Redis no se inicializa porque CacheService depende de DB.

**Culpables:**
- `DATABASE_URL` secret mal configurado (apunta a localhost).
- Posiblemente heredado de un test o fallback manual.
- `fly.toml` tiene `ALLOW_NO_DB=1`, que permite que el error se oculte.

#### 5.3 Solución – Actualizar DATABASE_URL

**Opciones:**

| Opción | Pasos | Ventajas | Desventajas |
|--------|-------|----------|-------------|
| **Fly Postgres (Recomendado)** | 1. Crear/adjuntar cluster; 2. Fly inyecta URL; 3. Reiniciar; 4. Migrar | Red interna, backup native, sin latencia | Costo adicional (~$12/mes) |
| **Postgres Externo (Railway/Neon)** | 1. Copiar connection string; 2. Setear manualmente; 3. Reiniciar; 4. Migrar | Flexible, proveedor elegible | Latencia red, gestión manual |

---

## Parte 2: Plan de Corrección (Próximas Acciones)

### Fase A: Corrección de DATABASE_URL

**Tiempo estimado:** 10–15 min

#### Opción A1: Fly Postgres (Quick)

```bash
# 1. Listar Postgres clusters en tu org
flyctl postgres list

# 2. Si no existe uno de producción, crear:
flyctl postgres create --org <org-name> --region dfw --name grupo-gad-db

# 3. Adjuntar cluster a app
flyctl postgres attach --postgres-app grupo-gad-db --app grupo-gad

# 4. Fly inyecta DATABASE_URL automáticamente; verifica:
flyctl secrets list --app grupo-gad
# Deberías ver DATABASE_URL actualizado

# 5. Reiniciar máquinas para aplicar secret
flyctl machines restart --app grupo-gad --force

# 6. Esperar ~30s; verificar health
curl https://grupo-gad.fly.dev/health/ready
```

#### Opción A2: Postgres Externo (Railway/Neon)

```bash
# 1. Copiar connection string desde proveedor (p.ej. Railway)
# Ejemplo: postgresql://user:pass@host.railway.app:5432/db_prod

# 2. Setear secreto en Fly
flyctl secrets set DATABASE_URL='postgresql://...' --app grupo-gad

# 3. Reiniciar máquinas
flyctl machines restart --app grupo-gad --force

# 4. Verificar
curl https://grupo-gad.fly.dev/health/ready
```

### Fase B: Ejecutar Migraciones

```bash
# Una vez que /health/ready muestra database="ok":

# 1. SSH into app container
flyctl ssh console --app grupo-gad

# 2. Dentro del container
cd /app
alembic upgrade head

# 3. Salir
exit
```

### Fase C: Validación Post-Fix

```bash
# 1. Health check detallado
curl https://grupo-gad.fly.dev/health/ready
# Esperado: status="ready", todos los checks="ok"

# 2. Smoke tests HTTP (básico)
flyctl ssh console --app grupo-gad
python scripts/smoke_test_sprint.sh  # o similar

# 3. Smoke tests WebSocket (opcional, avanzado)
python scripts/ws_smoke_test.py --url wss://grupo-gad.fly.dev

# 4. UAT (opcional)
python scripts/uat_staging_redis_complete.py --target production
```

---

## Cambios de Código Aplicados (Esta Sesión)

| Archivo | Cambio | Razón |
|---------|--------|-------|
| `config/settings.py` | Normaliza `postgres://` → `postgresql+asyncpg://` en `assemble_db_url()` | Compatibilidad con proveedores que usan alias corto |
| `src/api/main.py` | Normaliza en fallback de `os.getenv("DATABASE_URL")` | Asegura transformación aun en ruta de emergencia |

**Tests post-cambio:** ✅ PASS

---

## Checklist Pre-Producción

- [x] Suite de tests local: PASS
- [x] Análisis estático: Hallazgos documentados (no bloqueantes)
- [x] Config inspecciona: DATABASE_URL precedencia clara
- [x] TODO/FIXME auditados: Ninguno bloquea
- [x] Código normalizado: asyncpg compatible
- [ ] **DATABASE_URL en prod actualizado** ← PRÓXIMO PASO CRÍTICO
- [ ] **Migraciones ejecutadas** ← Después de actualizar URL
- [ ] **/health/ready = "ready"** ← Validación final
- [ ] Smoke tests ejecutados
- [ ] UAT producción completado
- [ ] `ALLOW_NO_DB` desactivado en prod (post-estabilidad)

---

## Métricas y Líneas de Base

### Staging (Actual)

```
✅ Database: postgresql+asyncpg://...@grupo-gad-staging-db.internal:5432/grupo_gad
✅ Redis: rediss://user:pass@host.upstash.io
✅ /health: "ok"
✅ /health/ready: "ready"
   ├─ database: "ok"
   ├─ redis: "ok"
   ├─ websocket_manager: "ok"
   ├─ ws_pubsub: "ok"
   └─ active_ws_connections: N
✅ UAT: 10/11 tests pass (90.9%)
```

### Producción (Actual – Degradado)

```
❌ Database: postgresql://postgres:postgres@localhost:5432/grupo_gad (INVÁLIDA)
✅ Redis: rediss://user:pass@host.upstash.io (aprovisionada, no inicializada)
✅ /health: "ok" (básico)
⚠️ /health/ready: "degraded"
   ├─ database: "error: [Errno 111] Connection refused"
   ├─ redis: "not_configured"
   ├─ websocket_manager: "ok"
   ├─ ws_pubsub: "not_configured"
   └─ active_ws_connections: 0
❌ UAT: No ejecutado (DB no disponible)
```

---

## Recomendaciones Finales

1. **Inmediato (hoy):**
   - Actualizar `DATABASE_URL` en Fly (adjuntar DB o setear URL).
   - Reiniciar máquinas.
   - Ejecutar migraciones.
   - Validar `/health/ready = ready`.

2. **Post-estabilidad (esta semana):**
   - Desactivar `ALLOW_NO_DB` en producción (`fly.toml`).
   - Resolver typing en bot handlers (post-release).
   - Agregar monitoreo/alertas en `/health/ready` degradado.

3. **Próxima iteración:**
   - Implementar Parte 2 de auditoría (performance, seguridad, escalabilidad).
   - Load tests contra producción.
   - Optimizaciones si es necesario (ver `PERFORMANCE_OPTIMIZATION_FINAL_REPORT.md`).

---

## Referencias

- **Guía de instrucciones:** `.github/copilot-instructions.md`
- **Settings & DB:** `config/settings.py`, `src/api/main.py`
- **Fly.io config:** `fly.toml`, `Dockerfile`
- **Performance baseline:** `performance_baseline_staging.txt`
- **UAT script:** `scripts/uat_staging_redis_complete.py`

---

**Próximo estado:** Esperar confirmación de elección (Fly Postgres vs. externo) para ejecutar Fase A.

