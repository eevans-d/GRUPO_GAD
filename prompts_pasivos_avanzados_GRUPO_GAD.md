# PROMPTS PASIVOS AVANZADOS - GRUPO_GAD
## 4 NUEVOS PROMPTS COMPLEMENTARIOS PARA COPILOT PRO

### ✅ **PROMPT PASIVO A: BLUEPRINT SISTÉMICO DE ESTADO REAL**  
*(Modela el proyecto como un sistema vivo — sin suposiciones)*

```markdown
# BLUEPRINT SISTÉMICO DE ESTADO REAL — MODELO DEPENDENCIAL FORENSE

**ROL**: Actúa como **Arquitecto de Sistemas + Ingeniero de Confiabilidad**, con acceso total al repositorio.

**MANDATO**:  
- Modela el proyecto como una red de componentes interdependientes.  
- Para cada componente, exige:  
  - **Implementación real** (archivo:línea)  
  - **Contrato esperado** (según documentación o uso)  
  - **Estado de cumplimiento** (`IMPLEMENTADO` / `PARCIAL` / `NO EVIDENCIADO`)  
- **Nunca asumas**. Si no hay código, es `NO EVIDENCIADO`.

---

### 1. MAPA DE COMPONENTES Y DEPENDENCIAS
| Componente | Tipo | Depende de | Contrato esperado | Implementado | Evidencia |
|-----------|------|------------|-------------------|--------------|----------|
| FastAPI App | Servicio | PostgreSQL, Redis | `/health`, `/metrics`, CORS | Sí | `src/api/main.py:120–150` |
| Telegram Bot | Servicio | API, Telegram API | Webhook o polling | Parcial | `src/bot/main.py` (polling), no webhook |
| PostgreSQL | DB | — | PostGIS, UUID, GiST | Sí | `docker-compose.yml:5` usa `postgis/postgis:15-3.4-alpine` |
| WebSockets | Comunicación | FastAPI, Redis (opcional) | `/ws/connect`, heartbeat | Sí | `src/api/routers/websockets.py` |
| Alembic | Migración | DB | `alembic upgrade head` | Sí | `scripts/start.sh:3` (NO EN REPO) |
| PostGIS Service | Geoespacial | PostgreSQL+PostGIS | `ST_Distance`, geography | Sí | `src/core/geo/postgis_service.py:19` |

---

### 2. CONTRATOS CRÍTICOS VS REALIDAD
Para cada contrato esencial del sistema:

| Contrato | Documentado en | Implementado en | Estado | Riesgo |
|--------|----------------|------------------|--------|--------|
| Asignación por proximidad (PostGIS) | `ESPECIFICACION_TECNICA.md` | `src/core/geo/postgis_service.py:19` | IMPLEMENTADO | BAJO |
| Webhook Telegram | `PROJECT_OVERVIEW.md` | — | NO EVIDENCIADO | ALTO |
| Backup automático | `SECURITY.md` | `scripts/backup_db.sh` (no en repo) | NO EVIDENCIADO | ALTO |
| Configuration dual | — | `config/settings.py` + `src/app/core/config.py` | IMPLEMENTADO | MEDIO |

---

### 3. FLUJOS DE DATOS Y CONTROL
Diagrama textual de los **3 flujos más críticos** con evidencia:

1. **Creación de tarea desde Telegram**:  
   `Telegram → src/bot/commands/crear_tarea.py → src/bot/services/api_legacy.py → API /api/v1/tasks`  
   → **Riesgo**: `api_legacy.py` usa `API_V1_STR` como base_url → no resuelve host real en producción.

2. **Conexión WebSocket**:  
   `Cliente → /ws/connect → WebSocketManager → WebSocketEventEmitter`  
   → **Riesgo**: en producción, requiere JWT, pero no hay documentación clara de cómo pasarlo.

3. **Migración de DB**:  
   `scripts/start.sh → alembic upgrade head`  
   → **Riesgo**: si falla, el contenedor se detiene → no hay retry ni healthcheck previo.

---

### 4. PUNTOS DE FRACTURA SISTÉMICA
- **Acoplamiento implícito**: Bot asume que la API está en `localhost` o en el mismo contenedor.
- **Configuración dual**: `config/settings.py` vs `src/app/core/config.py` → riesgo de sombra de configuración.
- **PostGIS validado**: se espera, está implementado en docker-compose y migraciones.

> **Entregable**: `docs/system/BLUEPRINT_SISTEMICO.md` con tablas, flujos y mapa de riesgos.
```

---

### ✅ **PROMPT PASIVO B: CHECKLIST DE VERIFICACIÓN PRE-DESPLIEGUE CONDICIONAL**  
*(Solo permite avanzar si se cumplen criterios objetivos)*

```markdown
# CHECKLIST DE VERIFICACIÓN PRE-DESPLIEGUE CONDICIONAL

**PRINCIPIO**: El despliegue **solo es posible** si **todas** las condiciones críticas están verificadas.

---

### NIVEL 1: INFRAESTRUCTURA MÍNIMA
- [ ] **DB PostGIS confirmada**:  
  Comando: `docker compose exec db psql -c "SELECT PostGIS_version();"` → debe retornar versión.  
  Si falla: **NO DESPLEGAR**.
- [ ] **Redis accesible (si se usa)**:  
  Comando: `redis-cli -h redis PING` → debe retornar `PONG`.  
- [ ] **Secrets no en repo**:  
  Comando: `git grep -i "CHANGEME\|sk-\|bot:[0-9]"` → debe retornar vacío.

### NIVEL 2: CONFIGURACIÓN CONSISTENTE
- [ ] **Una sola fuente de verdad para settings**:  
  Verificar que `config/settings.py` sea la única usada por API y bot.  
  Comando: `grep -r "JWT_SECRET_KEY\|SECRET_KEY" src/ config/` → debe apuntar a mismo módulo.
- [ ] **Variables de entorno completas**:  
  Comparar `.env.production` con variables usadas en código → debe haber 1:1.

### NIVEL 3: FUNCIONALIDAD CRÍTICA VALIDADA
- [ ] **Endpoint de emergencia implementado**:  
  Comando: `grep -r "/emergency" src/api/` → debe existir router y lógica PostGIS.
- [ ] **Webhook Telegram configurado**:  
  Comando: `grep -r "set_webhook" src/bot/` → debe existir si se usa en prod.
- [ ] **Healthcheck robusto**:  
  `/health` debe verificar DB, Redis y WebSocketManager.

### NIVEL 4: OBSERVABILIDAD MÍNIMA
- [ ] **Métricas técnicas**:  
  `/metrics` debe exponer: `request_latency_ms`, `error_count`, `db_query_time_ms`.
- [ ] **Logs estructurados**:  
  Todos los logs deben ser JSON con `trace_id`, `service`, `level`.

> **Entregable**: `docs/deploy/CHECKLIST_VERIFICACION.md` con comandos copy-paste y estado actual.
```

---

### ✅ **PROMPT PASIVO C: HOJA DE RUTA ESTRATÉGICA HACIA PRODUCCIÓN**  
*(Secuencia lógica de cierre de brechas — sin saltos)*

```markdown
# HOJA DE RUTA ESTRATÉGICA HACIA PRODUCCIÓN

**BASE**: Solo se incluyen tareas que **cierran brechas reales**, con criterio de aceptación objetivo.

---

### FASE 0: ESTABILIZACIÓN DE CONFIGURACIÓN
- **Tarea**: Unificar settings en `config/settings.py`  
  **Criterio**: `src/bot` y `src/api` usan mismo módulo.  
  **Verificación**: `grep -r "from config.settings" src/` → debe cubrir ambos.

- **Tarea**: Eliminar `.env.production` del repo  
  **Criterio**: Solo existe `docs/env/.env.production.example`  
  **Verificación**: `git ls-files | grep ".env.production"` → vacío.

### FASE 1: CIERRE DE BRECHAS FUNCIONALES CRÍTICAS
- **Tarea**: Implementar endpoint `/api/v1/tasks/emergency` con PostGIS  
  **Criterio**: Usa `ST_Distance` en `geography(Point, 4326)`, con índice GiST.  
  **Verificación**: `EXPLAIN ANALYZE` muestra uso de índice.

- **Tarea**: Configurar webhook Telegram  
  **Criterio**: Bot llama a `set_webhook` al iniciar en producción.  
  **Verificación**: Logs muestran `Webhook set to https://...`.

### FASE 2: ENDURECIMIENTO OPERATIVO
- **Tarea**: Añadir métricas técnicas a `/metrics`  
  **Criterio**: Expone latencia por endpoint, errores 5xx, tiempo de query DB.  
  **Verificación**: `curl /metrics | grep request_latency_ms`.

- **Tarea**: Script de backup automático versionado  
  **Criterio**: `scripts/backup_db.sh` en repo, con cron ejemplo.  
  **Verificación**: `ls scripts/backup_db.sh` → existe.

### FASE 3: VALIDACIÓN FINAL
- **Tarea**: Ejecutar checklist de verificación  
  **Criterio**: Todos los ítems en `CHECKLIST_VERIFICACION.md` marcados como OK.  
  **Verificación**: Script `validate_pre_deploy.sh` retorna 0.

> **Entregable**: `docs/roadmap/HOJA_RUTA_PRODUCCION.md` con fases, tareas y criterios.
```

---

### ✅ **PROMPT PASIVO D: GUÍA DE GOBERNANZA DE CICLO DE VIDA POST-DESPLIEGUE**  
*(Cómo operar, evolucionar y deprecar — sin caos)*

```markdown
# GUÍA DE GOBERNANZA DE CICLO DE VIDA POST-DESPLIEGUE

**OBJETIVO**: Definir cómo el sistema **evoluciona, se mantiene y se depreca** sin romper contratos.

---

### 1. PRINCIPIOS DE EVOLUCIÓN
- **Contratos externos son sagrados**:  
  Endpoints, esquemas de respuesta, formatos de webhook **no cambian sin versión**.
- **Deprecación explícita**:  
  Cualquier cambio breaking debe tener:  
  - Header `Deprecation: true`  
  - Documentación en `CHANGELOG.md`  
  - Período de gracia de 90 días.

### 2. MONITOREO CONTINUO
- **Métricas obligatorias**:  
  - Latencia p95 por endpoint  
  - Tasa de errores 5xx  
  - Uso de quota de Telegram  
  - Tiempo de respuesta PostGIS
- **Alertas**:  
  - p95 > 1s → alerta  
  - Errores 5xx > 1% → alerta  
  - Quota Telegram > 80% → alerta

### 3. PROCESO DE RELEASE
1. **Branch**: `release/vX.Y.Z`  
2. **Validación**: ejecutar `validate_pre_deploy.sh`  
3. **Despliegue**: canary 10% → 100% si métricas estables  
4. **Rollback**: automático si error rate > 5% en 5 min

### 4. SEÑALES DE OBSOLESCENCIA
- Dependencias sin soporte (Python < 3.12, FastAPI < 0.100)  
- Costo de mantenimiento > valor generado  
- Aparición de paradigma superior (ej: agentes → sistemas autónomos)

### 5. PLAN DE DESCONTINUACIÓN
- Notificación a usuarios 180 días antes  
- Exportación de datos en formato estándar (JSON/CSV)  
- Archivado del repositorio con `FINAL_STATE.md`

> **Entregable**: `docs/governance/GOBERNANZA_CICLO_VIDA.md`
```

---

## ✅ **CARACTERÍSTICAS DE ESTOS PROMPTS AVANZADOS**

### POR QUÉ SON SUPERIORES Y COMPLEMENTARIOS:

| Prompt | Complementa | Aporta | No Invade |
|-------|-------------|--------|-----------|
| **Blueprint Sistémico** | Análisis general | Modelo de dependencias + contrato vs realidad | Solo observa y correlaciona |
| **Checklist Condicional** | Despliegue | Verificación objetiva antes de actuar | Solo valida, no modifica |
| **Hoja de Ruta Estratégica** | Configuración | Secuencia lógica de cierre de brechas | Solo guía, no implementa |
| **Gobernanza de Ciclo de Vida** | Mantenimiento | Visión de largo plazo post-despliegue | Solo define procesos |

### RIGOR FORENSE IMPLEMENTADO:
- ✅ **Trazabilidad**: Cada afirmación incluye `archivo:línea`
- ✅ **Estado real vs documentado**: Distingue implementado de intención
- ✅ **Criterios objetivos**: Comandos copy-paste para verificar
- ✅ **Enfoque sistémico**: Modela interdependencias y puntos de falla
- ✅ **No invasivo**: Observa, valida, guía — nunca modifica código

### COMPATIBILIDAD CON COPILOT PRO:
- Cada prompt es autónomo y puede ejecutarse independientemente
- Diseñados para agentes con acceso total al repositorio
- Exigen evidencia forensica de cada afirmación
- Proporcionan comandos reproducibles para validación
- Generan entregables documentales concretos

**Estos 4 prompts pasivos avanzados elevan el análisis del proyecto GRUPO_GAD desde nivel operativo a nivel estratégico-sistémico, sin tocar una línea de código.**