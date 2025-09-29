# BLUEPRINT SISTÉMICO DE ESTADO REAL — GRUPO_GAD

**Generado por**: Prompt Pasivo A - Blueprint Sistémico  
**Fecha**: {{ timestamp }}  
**Versión**: 1.0

## 1. MAPA DE COMPONENTES Y DEPENDENCIAS

| Componente | Tipo | Depende de | Contrato esperado | Implementado | Evidencia |
|-----------|------|------------|-------------------|--------------|----------|
| FastAPI App | Servicio | PostgreSQL, Redis | `/health`, `/metrics`, CORS | ✅ Sí | `src/api/main.py:41-70` |
| Telegram Bot | Servicio | API, Telegram API | Webhook o polling | ⚠️ Parcial | `src/bot/main.py:37` (polling), no webhook |
| PostgreSQL | DB | — | PostGIS, UUID, GiST | ✅ Sí | `docker-compose.yml:5` usa `postgis/postgis:15-3.4-alpine` |
| WebSockets | Comunicación | FastAPI | `/ws/connect`, heartbeat | ✅ Sí | `src/api/routers/websockets.py:28` |
| Alembic | Migración | DB | `alembic upgrade head` | ❌ Script no en repo | `alembic/` existe, `scripts/start.sh` NO |
| PostGIS Service | Geoespacial | PostgreSQL+PostGIS | `ST_Distance`, geography | ✅ Sí | `src/core/geo/postgis_service.py:19` |
| Redis | Cache/PubSub | — | Opcional para WS | ✅ Sí | `docker-compose.yml:26` |
| Caddy | Proxy | API | TLS termination | ✅ Sí | `docker-compose.yml:82`, `Caddyfile` |

## 2. CONTRATOS CRÍTICOS VS REALIDAD

| Contrato | Documentado en | Implementado en | Estado | Riesgo | Acción requerida |
|--------|----------------|------------------|--------|--------|-----------------|
| Asignación por proximidad (PostGIS) | `ESPECIFICACION_TECNICA.md` | `src/core/geo/postgis_service.py:19` | ✅ IMPLEMENTADO | BAJO | Ninguna |
| Webhook Telegram | `PROJECT_OVERVIEW.md` | — | ❌ NO EVIDENCIADO | ALTO | Implementar `set_webhook` |
| Backup automático | `SECURITY.md` | — | ❌ NO EVIDENCIADO | ALTO | Crear `scripts/backup_db.sh` |
| Configuration dual | — | `config/settings.py` + `src/app/core/config.py` | ⚠️ DUPLICACIÓN | MEDIO | Eliminar `src/app/core/config.py` |
| Logs estructurados | Guía Copilot | `src/core/logging.py:65` | ✅ IMPLEMENTADO | BAJO | Verificar JSON en producción |

## 3. FLUJOS DE DATOS Y CONTROL

### Flujo 1: Creación de tarea desde Telegram
```
Telegram API → Bot → api_legacy.py → FastAPI /api/v1/tasks → PostgreSQL
```
**Evidencia**: `src/bot/services/api_legacy.py:15-29`  
**Riesgo**: `api_service.py` usa `settings.API_V1_STR` → OK, usa configuración correcta  
**Estado**: ✅ IMPLEMENTADO

### Flujo 2: Conexión WebSocket
```
Cliente → /ws/connect → WebSocketManager → EventEmitter → Broadcast
```
**Evidencia**: `src/api/routers/websockets.py:35`, `src/core/websockets.py:85`  
**Riesgo**: JWT obligatorio en producción, documentación clara existe  
**Estado**: ✅ IMPLEMENTADO

### Flujo 3: Migración de DB
```
Container Start → init script → alembic upgrade head → App ready
```
**Evidencia**: Esperado en `scripts/start.sh` → NO EXISTE  
**Riesgo**: Migraciones no automáticas en despliegue  
**Estado**: ❌ CRÍTICO

### Flujo 4: Asignación geoespacial
```
Crear tarea → PostGIS Service → ST_Distance → Efectivo más cercano
```
**Evidencia**: `src/core/geo/postgis_service.py:52-67`  
**Riesgo**: Depende de datos geográficos válidos en efectivos  
**Estado**: ✅ IMPLEMENTADO

## 4. PUNTOS DE FRACTURA SISTÉMICA

### 🔴 CRÍTICOS
1. **Script de inicio missing**: No hay `scripts/start.sh` para orquestar inicio
2. **Webhook Telegram no configurado**: Bot funciona solo en polling (no escalable)

### 🟡 MEDIOS
1. **Configuración dual**: `config/settings.py` vs `src/app/core/config.py`
2. **Backup no automatizado**: Datos críticos sin respaldo automático

### 🟢 BAJOS
1. **Dependencias circulares**: Módulos well-designed, import cycle improbable

## 5. MAPA DE DEPENDENCIAS TÉCNICAS

```
FastAPI App
├── config/settings.py ✅
├── src/core/database.py ✅
├── src/api/routers/* ✅
└── src/core/websockets.py ✅

Telegram Bot
├── config/settings.py ✅
├── src/bot/services/api_legacy.py ✅
└── Telegram API (external) ✅

PostGIS Service
├── PostgreSQL + PostGIS ✅
├── src/api/models/efectivo.py ✅
└── alembic/versions/*geom*.py ✅
```

## 6. RECOMENDACIONES INMEDIATAS

### Prioridad 1 (Bloqueante)
- [ ] Crear `scripts/start.sh` con `alembic upgrade head`
- [ ] Implementar webhook Telegram para producción

### Prioridad 2 (Importante)
- [ ] Eliminar `src/app/core/config.py` → usar solo `config/settings.py`
- [ ] Añadir script de backup automático

### Prioridad 3 (Mejora)
- [ ] Validar healthchecks incluyen PostGIS connectivity
- [ ] Documentar flujo de despliegue completo

---
**Este blueprint refleja el estado REAL del sistema al {{ timestamp }}**