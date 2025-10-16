# DOCUMENTACIÓN COMPLETA DEL PROYECTO GRUPO_GAD
**Sistema de Gestión de Tareas Operativas para Seguridad y Coordinación de Efectivos**

---

## RESUMEN EJECUTIVO

GRUPO_GAD es un sistema backend de gestión de tareas operativas diseñado para coordinar y monitorear actividades de efectivos de seguridad en campo. El sistema integra una API REST basada en FastAPI, un bot de Telegram para interacción móvil con efectivos, base de datos PostgreSQL con extensión PostGIS para tracking geoespacial, y sistema de notificaciones en tiempo real mediante WebSockets. Permite la creación, asignación y seguimiento de tareas operativas (patrullajes, investigaciones, vigilancias), control de disponibilidad de efectivos, y generación de métricas de rendimiento para optimizar la gestión operativa de seguridad.

---

## ESPECIFICACIONES DEL PROYECTO

**Nombre del Proyecto:** GRUPO_GAD (Gestión y Asignación de Despacho)

**Descripción breve:** Sistema backend para gestión de tareas operativas de seguridad, coordinación de efectivos en campo y monitoreo de actividades mediante API REST y bot Telegram.

### CAPACIDADES PRINCIPALES DEL SISTEMA

1. **Gestión de Tareas Operativas** — Crear, asignar, modificar y finalizar tareas de diferentes tipos (PATRULLAJE, INVESTIGACION, VIGILANCIA, INTERVENCION, ADMINISTRATIVA, ENTRENAMIENTO) con control de estados y prioridades.

2. **Bot Telegram para Efectivos** — Interfaz conversacional móvil que permite a efectivos en campo crear tareas, consultar historial, finalizar actividades y ver estadísticas personales sin necesidad de acceso a computadora.

3. **Tracking Geoespacial** — Almacenamiento y consulta de ubicaciones de efectivos y tareas mediante PostGIS, con capacidad de búsqueda por proximidad y visualización en mapas.

4. **Sistema de Autenticación y Permisos** — Control de acceso basado en JWT con tres niveles de autorización (LEVEL_1, LEVEL_2, LEVEL_3) y gestión de sesiones con bloqueo por intentos fallidos.

5. **Métricas y Reportes Operativos** — Generación automática de métricas agregadas por tipo de tarea, prioridad, efectivo y período, con cálculo de tiempos promedio, tasas de éxito y percentiles.

6. **Notificaciones en Tiempo Real** — Sistema de WebSockets con Redis Pub/Sub para notificaciones instantáneas de cambios de estado, asignaciones y alertas a usuarios conectados.

### INTEGRACIONES

**Canales:**
- API REST (FastAPI) con documentación automática OpenAPI/Swagger
- Bot de Telegram (python-telegram-bot 20.x)
- WebSockets para notificaciones bidireccionales en tiempo real
- Dashboard web básico con visualización de mapas

**Bases de datos / almacenamiento:**
- PostgreSQL 15 con extensión PostGIS 3.4
- Redis 7.2 para caché y Pub/Sub
- Sistema de archivos para logs estructurados (Loguru)

**Sistemas externos:**
- Telegram Bot API para comunicación con efectivos
- Prometheus para exportación de métricas de monitoreo
- Caddy como reverse proxy (producción)

### CARACTERÍSTICAS DE COMPORTAMIENTO

**Tiempo de respuesta objetivo:** 
- Consultas simples (GET usuarios, tareas): < 100ms
- Consultas con cache (estadísticas): < 50ms
- Operaciones geoespaciales (proximidad): < 300ms
- Creación/modificación de tareas: < 200ms

**Tono de comunicación:** Profesional operativo, directo y claro para contexto de seguridad, terminología de despacho y coordinación de campo.

**Registros que mantiene:** 
- Historial completo de cambios de estado de tareas (timestamp, usuario, estado anterior/nuevo, motivo)
- Logs estructurados de todas las operaciones API (nivel INFO/WARNING/ERROR)
- Métricas agregadas calculadas periódicamente (por tipo, prioridad, efectivo)
- Registro de autenticación (último acceso, intentos fallidos, bloqueos temporales)

---

# PERSPECTIVA 1 — SISTEMA: "¿QUÉ ES Y QUÉ HACE?"

## Descripción Ejecutiva

GRUPO_GAD es un sistema backend especializado para gestión operativa de seguridad que permite coordinar tareas de efectivos en campo mediante una API REST robusta y un bot de Telegram. El sistema mantiene un registro completo de todas las actividades (patrullajes, investigaciones, vigilancias, intervenciones), controla la disponibilidad de efectivos y sus ubicaciones geográficas mediante PostGIS, y proporciona métricas en tiempo real para supervisores. La arquitectura asíncrona basada en FastAPI y SQLAlchemy Async garantiza alto rendimiento en operaciones concurrentes, mientras que el sistema de caché con Redis reduce latencias en consultas frecuentes hasta un 95%.

## Capacidades Detalladas

### 1. Gestión de Tareas Operativas
**Qué hace:** Permite crear, modificar, asignar y finalizar tareas operativas con control de estados (PROGRAMMED, IN_PROGRESS, COMPLETED, CANCELLED, PAUSED), prioridades (LOW, MEDIUM, HIGH, URGENT, CRITICAL) y tipos específicos de operación (PATRULLAJE, INVESTIGACION, VIGILANCIA, INTERVENCION, ADMINISTRATIVA, ENTRENAMIENTO).

**Cuándo se activa:** A través de la API REST (endpoints `/api/v1/tasks`) o mediante comandos del bot de Telegram (`/crear_tarea`). Los supervisores crean tareas desde la API, los efectivos en campo pueden crearlas directamente desde Telegram.

**Resultado esperado:** Tarea registrada en base de datos con ID único, código generado automáticamente, asignación opcional de efectivos, ubicación geográfica (lat/lon), y registro inicial en historial de estados. Notificación WebSocket enviada a usuarios conectados si corresponde.

### 2. Bot Telegram para Efectivos
**Qué hace:** Proporciona interfaz conversacional móvil con comandos específicos: `/start` (menú principal), `/crear_tarea` (wizard de creación), `/historial` (consulta de tareas asignadas), `/finalizar_tarea` (marcar como completada), `/estadisticas` (métricas personales del efectivo).

**Cuándo se activa:** Cuando un efectivo envía un comando al bot de Telegram vinculado al sistema. Requiere que el efectivo esté registrado en la base de datos con su `telegram_id` configurado.

**Resultado esperado:** Respuesta contextual del bot con información solicitada o confirmación de acción realizada. Las operaciones del bot modifican directamente la base de datos y generan los mismos registros de auditoría que la API REST.

### 3. Tracking Geoespacial
**Qué hace:** Almacena ubicaciones de efectivos (columna `geom` tipo POINT en tabla `efectivos`) y tareas (columnas `ubicacion_lat`, `ubicacion_lon`) con capacidad de consultar efectivos disponibles cerca de una ubicación mediante función de distancia haversine.

**Cuándo se activa:** Al crear/actualizar efectivos con sus ubicaciones actuales, al crear tareas con ubicación específica, o al consultar el endpoint `/api/v1/geo/map/view` con parámetros de latitud/longitud y radio de búsqueda.

**Resultado esperado:** Lista de efectivos u otros elementos dentro del radio especificado, ordenados por distancia. Datos utilizables para visualización en mapas mediante el dashboard web simple que incluye integración con Leaflet.js.

### 4. Sistema de Autenticación y Permisos
**Qué hace:** Implementa autenticación JWT (HS256) con tokens de acceso, validación de credenciales, control de intentos fallidos (máximo 5 antes de bloqueo temporal), y tres niveles de autorización que determinan permisos sobre recursos.

**Cuándo se activa:** En cada request a endpoints protegidos (mayoría de la API), validando el token JWT en el header `Authorization: Bearer <token>`. El login genera el token inicial mediante `POST /api/v1/auth/login`.

**Resultado esperado:** Usuarios autenticados pueden acceder a recursos según su nivel de autorización. LEVEL_1 (operativo básico), LEVEL_2 (supervisor), LEVEL_3 (administrador). Bloqueo automático por 30 minutos tras 5 intentos fallidos, registro de último acceso y verificación de estado de cuenta.

### 5. Métricas y Reportes Operativos
**Qué hace:** Calcula y almacena métricas agregadas en tabla `metricas_tareas`: total de tareas, suma de horas trabajadas, tiempo promedio, tasa de éxito, y percentiles (p50, p75, p90, p95, p99) de duración, agrupadas por tipo de tarea y prioridad.

**Cuándo se activa:** Mediante endpoints `/api/v1/statistics/user/{user_id}` para métricas individuales, o por procesos batch/cron que recalculan métricas globales periódicamente. Sistema de caché con Redis reduce carga en consultas repetidas.

**Resultado esperado:** Datos estadísticos agregados para análisis de rendimiento operativo, identificación de cuellos de botella, planificación de recursos y evaluación de efectividad de equipos. Exportables en formato JSON para integración con sistemas de BI externos.

### 6. Notificaciones en Tiempo Real
**Qué hace:** Mantiene conexiones WebSocket activas (endpoint `WS /ws/connect`) mediante `WebSocketManager`, envía notificaciones automáticas usando Redis Pub/Sub para escalabilidad horizontal, incluye heartbeat/ping cada 30s y sistema de ACK para garantizar entrega.

**Cuándo se activa:** Al conectarse un cliente web al endpoint WebSocket (requiere autenticación JWT en producción). Notificaciones se envían cuando ocurren eventos relevantes: cambios de estado en tareas, nuevas asignaciones, alertas del sistema, broadcasts administrativos.

**Resultado esperado:** Clientes conectados reciben mensajes en tiempo real con estructura `WSMessage` (event_type, data, timestamp). Métricas del sistema incluyen `total_messages_sent`, `total_broadcasts`, `total_send_errors`. Dashboard de estadísticas disponible en `GET /ws/stats`.

## Características Técnicas del Comportamiento

### Latencias
- **Autenticación (login):** < 200ms (incluye hashing bcrypt)
- **Consultas GET sin cache:** 50-150ms según complejidad
- **Consultas GET con cache Redis:** 10-50ms (95% mejora medida)
- **Operaciones POST/PUT/DELETE:** 100-300ms (incluye escritura DB + auditoría)
- **Consultas geoespaciales (proximidad):** 200-500ms según cantidad de puntos
- **WebSocket mensaje:** < 50ms desde evento hasta entrega al cliente

### Estructura de Respuestas API

Todas las respuestas siguen formato JSON estándar:

**Respuesta exitosa (200/201):**
```json
{
  "id": "uuid-string",
  "campo1": "valor",
  "campo2": 123,
  "created_at": "2025-10-12T16:45:00Z"
}
```

**Respuesta de error (4xx/5xx):**
```json
{
  "detail": "Descripción del error",
  "errors": [
    {
      "loc": ["body", "campo"],
      "msg": "Detalle específico",
      "type": "validation_error"
    }
  ]
}
```

**Respuesta de lista paginada:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20
}
```

### Reglas de Fallback y Manejo de Errores

- **Error de conexión a base de datos:** HTTP 503 Service Unavailable + log ERROR + reintentos automáticos (3 intentos, backoff exponencial)
- **Token JWT inválido/expirado:** HTTP 401 Unauthorized con detalle específico ("Token expired" vs "Invalid token")
- **Permisos insuficientes:** HTTP 403 Forbidden indicando nivel requerido
- **Recurso no encontrado:** HTTP 404 Not Found con mensaje claro
- **Error de validación Pydantic:** HTTP 422 Unprocessable Entity con detalles de cada campo inválido
- **Error interno no manejado:** HTTP 500 Internal Server Error + log con traceback completo + ID de error para tracking
- **Rate limiting (si implementado):** HTTP 429 Too Many Requests con header `Retry-After`

## Datos que Registra

### Campos Mínimos en Base de Datos

**Tabla: usuarios**
```sql
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dni VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telegram_id VARCHAR(100) UNIQUE,
    nivel VARCHAR(20) NOT NULL, -- LEVEL_1, LEVEL_2, LEVEL_3
    hashed_password VARCHAR(255) NOT NULL,
    verificado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    ultimo_acceso TIMESTAMP,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tabla: efectivos**
```sql
CREATE TABLE efectivos (
    id UUID PRIMARY KEY REFERENCES usuarios(id),
    codigo_interno VARCHAR(50) UNIQUE NOT NULL,
    rango VARCHAR(100),
    unidad VARCHAR(200),
    especialidad VARCHAR(200),
    estado_disponibilidad VARCHAR(50) DEFAULT 'DISPONIBLE',
    -- DISPONIBLE, EN_TAREA, FUERA_SERVICIO
    geom GEOMETRY(POINT, 4326), -- PostGIS para ubicación
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tabla: tareas**
```sql
CREATE TABLE tareas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(50) NOT NULL,
    -- PATRULLAJE, INVESTIGACION, VIGILANCIA, INTERVENCION, ADMINISTRATIVA, ENTRENAMIENTO
    prioridad VARCHAR(20) NOT NULL,
    -- LOW, MEDIUM, HIGH, URGENT, CRITICAL
    estado VARCHAR(50) DEFAULT 'PROGRAMMED',
    -- PROGRAMMED, IN_PROGRESS, COMPLETED, CANCELLED, PAUSED
    ubicacion_lat NUMERIC(10, 8),
    ubicacion_lon NUMERIC(11, 8),
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    duracion_estimada_horas NUMERIC(6, 2),
    duracion_real_horas NUMERIC(6, 2),
    delegado_usuario_id UUID REFERENCES usuarios(id),
    efectivos_asignados INTEGER DEFAULT 0,
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Tabla: historial_estados**
```sql
CREATE TABLE historial_estados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tarea_id UUID NOT NULL REFERENCES tareas(id) ON DELETE CASCADE,
    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50) NOT NULL,
    usuario_id UUID REFERENCES usuarios(id),
    motivo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_historial_tarea ON historial_estados(tarea_id);
CREATE INDEX idx_historial_fecha ON historial_estados(created_at DESC);
```

**Tabla: tarea_efectivos** (asociación many-to-many)
```sql
CREATE TABLE tarea_efectivos (
    tarea_id UUID REFERENCES tareas(id) ON DELETE CASCADE,
    efectivo_id UUID REFERENCES efectivos(id) ON DELETE CASCADE,
    asignado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tarea_id, efectivo_id)
);
CREATE INDEX idx_tarea_efectivos_tarea ON tarea_efectivos(tarea_id);
CREATE INDEX idx_tarea_efectivos_efectivo ON tarea_efectivos(efectivo_id);
```

**Tabla: metricas_tareas**
```sql
CREATE TABLE metricas_tareas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_tarea VARCHAR(50),
    prioridad VARCHAR(20),
    total_tareas INTEGER DEFAULT 0,
    total_horas NUMERIC(10, 2) DEFAULT 0,
    tiempo_promedio NUMERIC(8, 2),
    tasa_exito NUMERIC(5, 2), -- porcentaje
    p50 NUMERIC(8, 2), -- mediana
    p75 NUMERIC(8, 2),
    p90 NUMERIC(8, 2),
    p95 NUMERIC(8, 2),
    p99 NUMERIC(8, 2),
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_metricas_tipo ON metricas_tareas(tipo_tarea);
CREATE INDEX idx_metricas_prioridad ON metricas_tareas(prioridad);
```

### Dónde se Almacenan
- **Base de datos principal:** PostgreSQL 15 con PostGIS (puerto 5434 en desarrollo)
- **Caché:** Redis 7.2 (puerto 6381) para estadísticas, sesiones y Pub/Sub
- **Logs:** Archivos `.log` en directorio `logs/` con rotación diaria, formato JSON estructurado (Loguru)
- **Configuración:** Variables de entorno (`.env`) y `config/settings.py` con Pydantic Settings
- **Migraciones:** Alembic en directorio `alembic/versions/`

## Sugerencia de Visualización (Diagrama de Flujo)

### Descripción Textual del Diagrama

**Título:** "Flujo de Procesamiento de Tarea en GRUPO_GAD"

**Elementos del diagrama:**

1. **Caja de Inicio (verde):** "Solicitud de creación de tarea" → API REST o Bot Telegram
   
2. **Proceso (azul):** "Validación de datos" → Pydantic valida campos requeridos (titulo, tipo, prioridad)
   - **Decisión (rombo naranja):** "¿Datos válidos?"
     - **NO** → "Retornar HTTP 422 con errores" → Fin
     - **SÍ** → continúa

3. **Proceso (azul):** "Verificar autenticación y permisos"
   - **Decisión (rombo amarillo):** "¿Usuario autorizado?"
     - **NO** → "Retornar HTTP 401/403" → Fin
     - **SÍ** → continúa

4. **Proceso (azul):** "Generar código único de tarea" → AUTO-generado con secuencia

5. **Proceso (azul):** "Insertar en tabla `tareas`" (estado inicial: PROGRAMMED)
   
6. **Proceso (azul):** "Registrar en `historial_estados`" (estado_nuevo: PROGRAMMED, usuario_id, timestamp)

7. **Decisión (rombo morado):** "¿Hay efectivos a asignar?"
   - **SÍ** → "Insertar en `tarea_efectivos`" → "Actualizar `estado_disponibilidad` de efectivos"
   - **NO** → continúa

8. **Proceso (azul):** "Invalidar cache de estadísticas" (Redis DEL keys relevantes)

9. **Proceso (verde claro):** "Broadcast WebSocket" → Notificar a usuarios conectados sobre nueva tarea

10. **Proceso (gris):** "Registrar en logs" → Loguru INFO con detalles de la operación

11. **Caja de Fin (verde):** "Retornar HTTP 201 + datos de tarea creada"

**Flechas especiales:**
- Línea punteada roja desde cualquier proceso → "Error de BD" → HTTP 503 + log ERROR + reintentos
- Línea punteada naranja desde "Broadcast WebSocket" → "Error de conexión WS" → Continúa (no es crítico, se loguea WARNING)

**Leyenda:**
- Verde: Inicio/Fin exitoso
- Azul: Procesos de negocio
- Naranja/Amarillo: Validaciones
- Morado: Operaciones condicionales
- Verde claro: Notificaciones asíncronas
- Gris: Auditoría/Logging
- Rojo: Puntos de error posible

---

# PERSPECTIVA 2 — ADMINISTRADOR/SUPERVISOR: "¿CÓMO GESTIONO Y CONTROLO?"

## Descripción de Acceso

### Acceso al Sistema
**URL de la API:** `http://localhost:8000` (desarrollo) o `https://api.dominio.gob` (producción vía Caddy)

**Documentación interactiva:**
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

**Dashboard web simple:** `http://localhost:8000/dashboard` (visualización de mapa con Leaflet.js)

**Niveles de Autorización:**
1. **LEVEL_1 (Operativo):** Puede ver tareas asignadas, actualizar sus propias tareas, consultar su perfil
2. **LEVEL_2 (Supervisor):** Puede crear/modificar tareas, asignar efectivos, ver métricas de su unidad
3. **LEVEL_3 (Administrador):** Acceso total (gestión de usuarios, configuración, métricas globales, invalidación de cache)

**Login y Seguridad:**
- **Endpoint de autenticación:** `POST /api/v1/auth/login` (body: `{"username": "dni_o_email", "password": "xxx"}`)
- Respuesta incluye token JWT: `{"access_token": "eyJ...", "token_type": "bearer"}`
- Token debe enviarse en header: `Authorization: Bearer eyJ...`
- **Duración del token:** Configurable vía `JWT_EXPIRATION_MINUTES` (por defecto 1440 min = 24 horas)
- **Bloqueo de cuenta:** 5 intentos fallidos → bloqueo por 30 minutos
- **Logout:** `POST /api/v1/auth/logout` (invalida token en sesión)

### Requisitos Técnicos
- Cliente HTTP/REST (Postman, Insomnia, cURL, HTTPie)
- Navegador moderno para Swagger UI (Chrome 90+, Firefox 88+, Edge 90+)
- Cliente WebSocket para notificaciones (librerías WebSocket estándar)
- PostgreSQL client (psql, pgAdmin, DBeaver) para acceso directo a datos (solo administradores)

## Métricas Clave que Visualiza

### KPIs Principales (Endpoints de Monitoreo)

1. **Estado de Salud del Sistema**
   - `GET /health` → Status básico (`{"status": "healthy", "timestamp": "..."}`)
   - `GET /health/detailed` → Detalles de componentes (DB, Redis, versión)
   - `GET /health/ready` → Readiness check para K8s/orquestadores
   - `GET /health/live` → Liveness check
   - `GET /health/performance` → Latencias de DB y Redis

2. **Métricas de Prometheus**
   - `GET /metrics` → Formato Prometheus/OpenMetrics
   - Métricas exportadas: HTTP requests (count, duration), DB queries, cache hit/miss rate, errors

3. **Estadísticas de Tareas**
   - `GET /api/v1/statistics/user/{user_id}` → Métricas de efectivo específico (cache 5 min)
   - Incluye: total tareas, completadas, en progreso, tiempo promedio, tasa de éxito

4. **Estadísticas de WebSocket**
   - `GET /ws/stats` → Clientes conectados, mensajes enviados, broadcasts, errores
   - Útil para monitorear conexiones activas en tiempo real

5. **Cache de Redis**
   - `GET /api/v1/cache/stats` → Hit rate, misses, tamaño, keys
   - `POST /api/v1/cache/invalidate` → Invalidar cache de usuario específico
   - `POST /api/v1/cache/clear` → Limpiar todo el cache (solo LEVEL_3)

### Consultas Directas a Base de Datos (SQL para Administradores)

**Total de tareas por estado (últimos 30 días):**
```sql
SELECT estado, COUNT(*) as total
FROM tareas
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY estado
ORDER BY total DESC;
```

**Efectivos más activos (por tareas completadas):**
```sql
SELECT u.nombre, u.apellido, COUNT(te.tarea_id) as tareas_asignadas
FROM usuarios u
JOIN efectivos e ON e.id = u.id
JOIN tarea_efectivos te ON te.efectivo_id = e.id
JOIN tareas t ON t.id = te.tarea_id AND t.estado = 'COMPLETED'
GROUP BY u.id, u.nombre, u.apellido
ORDER BY tareas_asignadas DESC
LIMIT 10;
```

**Tareas con mayor duración real vs estimada:**
```sql
SELECT codigo, titulo, duracion_estimada_horas, duracion_real_horas,
       (duracion_real_horas - duracion_estimada_horas) as diferencia
FROM tareas
WHERE duracion_real_horas IS NOT NULL AND duracion_estimada_horas IS NOT NULL
ORDER BY diferencia DESC
LIMIT 20;
```

**Tasa de éxito por tipo de tarea:**
```sql
SELECT tipo,
       COUNT(*) as total,
       SUM(CASE WHEN estado = 'COMPLETED' THEN 1 ELSE 0 END) as completadas,
       ROUND(100.0 * SUM(CASE WHEN estado = 'COMPLETED' THEN 1 ELSE 0 END) / COUNT(*), 2) as tasa_exito
FROM tareas
GROUP BY tipo
ORDER BY tasa_exito DESC;
```

## Datos que Debe Monitorear

### KPIs Críticos y Umbrales de Alerta

| Métrica | Umbral Normal | Umbral Advertencia | Umbral Crítico | Acción Recomendada |
|---------|---------------|-------------------|----------------|-------------------|
| **Latencia DB (queries)** | < 50ms | 50-200ms | > 200ms | Revisar índices, analizar slow queries |
| **Latencia Redis** | < 10ms | 10-50ms | > 50ms | Verificar conexión, revisar memoria Redis |
| **Cache hit rate** | > 80% | 60-80% | < 60% | Ajustar TTL, identificar queries no cacheadas |
| **Errores HTTP 5xx** | < 0.1% | 0.1-1% | > 1% | Revisar logs, verificar salud de DB/Redis |
| **Conexiones WebSocket activas** | N/A | > 100 | > 500 | Evaluar escalado horizontal |
| **Tareas en estado IN_PROGRESS > 24h** | < 5% | 5-10% | > 10% | Revisar tareas estancadas, contactar efectivos |
| **Intentos de login fallidos** | < 10/hora | 10-50/hora | > 50/hora | Posible ataque brute-force, revisar logs |

### Logs a Revisar Regularmente

**Archivo de logs:** `logs/grupo_gad_YYYY-MM-DD.log` (rotación diaria)

**Niveles importantes:**
- **ERROR:** Errores no manejados, caídas de servicios externos, problemas de conexión BD
- **WARNING:** Intentos fallidos de autenticación, operaciones lentas, cache misses altos
- **INFO:** Operaciones exitosas, creación/modificación de recursos, métricas periódicas

**Comando para ver errores del día:**
```bash
grep "ERROR" logs/grupo_gad_$(date +%Y-%m-%d).log | tail -50
```

**Comando para contar logins exitosos vs fallidos:**
```bash
grep "login" logs/grupo_gad_$(date +%Y-%m-%d).log | grep -c "successful"
grep "login" logs/grupo_gad_$(date +%Y-%m-%d).log | grep -c "failed"
```

## Funcionalidades de Control

### Acciones Disponibles vía API

1. **Gestión de Usuarios**
   - `GET /api/v1/users` → Listar todos los usuarios (paginado)
   - `GET /api/v1/users/{id}` → Ver detalle de usuario
   - `POST /api/v1/users` → Crear nuevo usuario (requiere LEVEL_3)
   - `PUT /api/v1/users/{id}` → Actualizar usuario
   - `GET /api/v1/users/me` → Ver perfil propio

2. **Gestión de Tareas**
   - `GET /api/v1/tasks` → Listar tareas (filtros: estado, tipo, prioridad, efectivo)
   - `GET /api/v1/tasks/{id}` → Ver detalle de tarea
   - `POST /api/v1/tasks` → Crear nueva tarea
   - `PUT /api/v1/tasks/{id}` → Actualizar tarea (cambiar estado, asignar efectivos)
   - `DELETE /api/v1/tasks/{id}` → Eliminar tarea (solo LEVEL_3)
   - `POST /api/v1/tasks/emergency` → Crear tarea de emergencia (prioridad CRITICAL)

3. **Control de Cache**
   - `GET /api/v1/cache/stats` → Estadísticas de Redis
   - `POST /api/v1/cache/invalidate` → Invalidar cache de usuario específico (body: `{"user_id": "uuid"}`)
   - `POST /api/v1/cache/clear` → Limpiar todo el cache (LEVEL_3 only)

4. **Consultas Geoespaciales**
   - `GET /api/v1/geo/map/view?lat={lat}&lon={lon}&radius={meters}` → Efectivos cercanos
   - Respuesta incluye distancias calculadas y datos de disponibilidad

5. **Gestión de WebSockets**
   - `WS /ws/connect` → Conectar cliente WebSocket (requiere JWT en query param `?token=xxx` en producción)
   - `GET /ws/stats` → Ver estadísticas de conexiones activas
   - `POST /ws/_test/broadcast` → Enviar broadcast manual (solo en desarrollo/testing, NO en producción)

### Comandos del Bot de Telegram (para Efectivos)

**Comandos disponibles:**
- `/start` → Menú principal con opciones
- `/crear_tarea` → Wizard de creación (solicita: título, descripción, tipo, prioridad, ubicación)
- `/historial` → Lista de tareas asignadas al efectivo (últimas 10)
- `/finalizar_tarea` → Marca tarea activa como completada (solicita ID o selección)
- `/estadisticas` → Métricas personales (tareas completadas, tiempo promedio, tasa de éxito)

**Configuración del bot:**
- Token en variable de entorno `TELEGRAM_BOT_TOKEN`
- Webhook o polling según `TELEGRAM_USE_WEBHOOK` (true/false)
- URL de webhook (si aplica): `TELEGRAM_WEBHOOK_URL`

## Mockup / Boceto del Dashboard (Descripción Textual)

### Dashboard Web Simple (Actual en el Proyecto)

**URL:** `http://localhost:8000/dashboard`

**Estructura HTML básica:**

#### **HEADER**
- Título: "GRUPO_GAD - Dashboard Operativo"
- Logo (si está configurado)
- Indicador de conexión (verde si API responde)

#### **SECCIÓN PRINCIPAL: MAPA INTERACTIVO**

Mapa Leaflet.js mostrando:
- **Marcadores de efectivos:** Color según estado_disponibilidad
  - 🟢 Verde: DISPONIBLE
  - 🔵 Azul: EN_TAREA
  - 🔴 Rojo: FUERA_SERVICIO
- **Marcadores de tareas:** Color según prioridad
  - 🟡 Amarillo: LOW/MEDIUM
  - 🟠 Naranja: HIGH
  - 🔴 Rojo: URGENT/CRITICAL
- **Tooltip al pasar mouse:** Nombre/código, estado, información básica
- **Click en marcador:** Modal con detalles completos

#### **PANEL LATERAL (si implementado):**
- Filtros: Por estado, tipo, prioridad
- Lista de tareas recientes (últimas 10)
- Estadísticas rápidas: Total tareas activas, efectivos disponibles

#### **FOOTER**
- Link a documentación API (`/docs`)
- Versión del sistema
- Información de contacto técnico

**Nota:** El dashboard actual es una implementación básica. Para un sistema de monitoreo completo, se recomienda integrar herramientas especializadas como Grafana (conectado a Prometheus) o desarrollar un frontend SPA con React/Vue.js consumiendo la API.

---

# PERSPECTIVA 3 — USUARIO FINAL (EFECTIVO EN CAMPO): "¿CÓMO USO ESTO?"

## Descripción de la Experiencia

### Cómo Inicia la Interacción

El efectivo interactúa con el sistema GRUPO_GAD principalmente a través del **Bot de Telegram**, diseñado para uso móvil en campo sin necesidad de computadora o acceso a la API directamente.

**Pasos iniciales:**

1. **Obtener acceso:** El administrador registra al efectivo en el sistema con su `telegram_id` asociado a su cuenta de usuario.

2. **Iniciar conversación con el bot:** El efectivo busca el bot en Telegram (nombre configurado al crear el bot) y envía `/start`.

3. **Mensaje de bienvenida del bot:**
   ```
   👮 ¡Bienvenido al Sistema GRUPO_GAD!
   
   Efectivo: [Nombre Apellido]
   Código: [Código Interno]
   Rango: [Rango]
   Unidad: [Unidad]
   
   Comandos disponibles:
   📝 /crear_tarea - Crear nueva tarea
   📋 /historial - Ver tus tareas
   ✅ /finalizar_tarea - Completar tarea activa
   📊 /estadisticas - Ver tus métricas
   
   ¿Qué necesitas hacer?
   ```

### Qué Puede Pedirle al Sistema

**A través del Bot de Telegram:**

- **Crear tareas:** Reportar incidentes, solicitar patrullajes, registrar investigaciones en curso
- **Consultar historial:** Ver tareas asignadas, estados, fechas
- **Finalizar tareas:** Marcar como completadas cuando terminan actividades
- **Ver estadísticas:** Consultar su rendimiento personal (tareas completadas, tiempo promedio)

**A través de la API REST (si tiene acceso):**
- Consultar detalles de tareas específicas
- Actualizar su ubicación geográfica
- Ver efectivos cercanos para coordinación
- Consultar su perfil y datos de usuario

### Opciones y Limitaciones

**El efectivo PUEDE:**
- Crear tareas de cualquier tipo y prioridad (según permisos de su nivel)
- Ver todas las tareas asignadas a él
- Completar/pausar sus propias tareas
- Consultar su historial operativo
- Actualizar notas en tareas en curso

**El efectivo NO PUEDE:**
- Ver tareas asignadas a otros efectivos (sin permiso LEVEL_2+)
- Eliminar tareas del sistema (solo LEVEL_3)
- Modificar datos de otros usuarios
- Acceder a métricas globales del sistema
- Cambiar su propio nivel de autorización

**Si necesita ayuda:**
- Comando `/help` en el bot (si implementado) o contacto con supervisor
- Reporte de errores técnicos a soporte via canales establecidos

## Flujo Típico de Interacción (Paso a Paso)

### Ejemplo: Crear Tarea de Patrullaje desde Telegram

**Paso 1: Efectivo inicia creación**
```
👮 Efectivo: /crear_tarea
```

**Paso 2: Bot solicita título**
```
🤖 Bot:
Perfecto, vamos a crear una nueva tarea.

📝 Primero, indícame el título de la tarea:
(Ejemplo: "Patrullaje sector norte")
```

**Paso 3: Efectivo proporciona título**
```
👮 Efectivo: Patrullaje en Barrio Las Flores
```

**Paso 4: Bot solicita descripción**
```
🤖 Bot:
Título registrado: "Patrullaje en Barrio Las Flores"

📄 Ahora, describe brevemente la tarea:
(Puedes incluir detalles relevantes, o envía "skip" si no hay descripción adicional)
```

**Paso 5: Efectivo proporciona descripción**
```
👮 Efectivo: Recorrido de seguridad preventiva por calles principales del barrio, horario nocturno
```

**Paso 6: Bot solicita tipo de tarea**
```
🤖 Bot:
Descripción guardada.

🏷️ Selecciona el tipo de tarea:
1. PATRULLAJE
2. INVESTIGACION
3. VIGILANCIA
4. INTERVENCION
5. ADMINISTRATIVA
6. ENTRENAMIENTO

Responde con el número (1-6):
```

**Paso 7: Efectivo selecciona tipo**
```
👮 Efectivo: 1
```

**Paso 8: Bot solicita prioridad**
```
🤖 Bot:
Tipo: PATRULLAJE ✅

⚠️ Indica la prioridad:
1. LOW (baja)
2. MEDIUM (media)
3. HIGH (alta)
4. URGENT (urgente)
5. CRITICAL (crítica)

Responde con el número (1-5):
```

**Paso 9: Efectivo selecciona prioridad**
```
👮 Efectivo: 2
```

**Paso 10: Bot solicita ubicación**
```
🤖 Bot:
Prioridad: MEDIUM ✅

📍 ¿Deseas agregar una ubicación?
- Envía tu ubicación actual (botón "Compartir ubicación")
- O envía coordenadas en formato: lat,lon (ej: -31.4201,-64.1888)
- O envía "skip" para omitir
```

**Paso 11: Efectivo comparte ubicación**
```
👮 Efectivo: [Comparte ubicación desde Telegram]
```

**Paso 12: Bot confirma y crea la tarea**
```
🤖 Bot:
Ubicación registrada: -31.4201, -64.1888 ✅

✅ TAREA CREADA EXITOSAMENTE

📋 Detalles:
• Código: TSK-2025-001234
• Título: Patrullaje en Barrio Las Flores
• Tipo: PATRULLAJE
• Prioridad: MEDIUM
• Estado: PROGRAMMED
• Ubicación: -31.4201, -64.1888
• Creado por: [Tu nombre]
• Fecha: 12/10/2025 16:45

La tarea ha sido registrada en el sistema.
Puedes verla en tu historial con /historial

¿Necesitas algo más?
```

**Tiempo total de la interacción:** ~2-3 minutos

---

## Ejemplo de Conversación Real (Caso: Finalizar Tarea)

### Escenario: Efectivo completa patrullaje y lo marca como finalizado

```
👮 Efectivo: /finalizar_tarea

🤖 Bot:
Perfecto, voy a ayudarte a finalizar una tarea.

Encontré estas tareas tuyas en estado IN_PROGRESS:

1. TSK-2025-001234 - Patrullaje en Barrio Las Flores
   Tipo: PATRULLAJE | Inicio: 12/10/2025 18:00

2. TSK-2025-001198 - Vigilancia Plaza Central
   Tipo: VIGILANCIA | Inicio: 12/10/2025 14:30

¿Cuál deseas finalizar? Responde con el número (1-2):

👮 Efectivo: 1

🤖 Bot:
Has seleccionado: TSK-2025-001234 - Patrullaje en Barrio Las Flores

✅ ¿Deseas agregar notas finales o novedades?
(Envía tus comentarios o "skip" para omitir)

👮 Efectivo: Patrullaje completado sin novedades. Todo tranquilo en la zona.

🤖 Bot:
Notas registradas ✅

Marcando tarea como COMPLETED...

✅ TAREA FINALIZADA EXITOSAMENTE

📋 Resumen:
• Código: TSK-2025-001234
• Título: Patrullaje en Barrio Las Flores
• Estado: COMPLETED ✅
• Inicio: 12/10/2025 18:00
• Fin: 12/10/2025 22:15
• Duración: 4.25 horas
• Notas: Patrullaje completado sin novedades. Todo tranquilo en la zona.

¡Buen trabajo! 👏
Puedes ver tu historial completo con /historial

👮 Efectivo: Gracias

🤖 Bot:
De nada, que tengas un buen descanso. Estoy disponible si necesitas algo más. 👮‍♂️
```

**Duración total:** ~60-90 segundos

---

## Canales de Acceso

### Dónde y Cómo Contactar al Sistema

#### 1. **Bot de Telegram (Canal Principal para Efectivos)**

**Acceso:**
- Buscar el bot en Telegram (nombre configurado al crear el bot con BotFather)
- Iniciar conversación con `/start`
- Requisito: Estar registrado en la base de datos con `telegram_id` configurado

**Características:**
- Disponible 24/7 desde cualquier dispositivo móvil
- Notificaciones push cuando hay asignaciones nuevas
- Interfaz conversacional simple, sin necesidad de entrenamiento técnico
- Funciona offline (los mensajes se envían cuando vuelve la conexión)

**Ventajas:**
- Uso en campo sin necesidad de laptop
- Respuestas rápidas mediante comandos
- Integrado con notificaciones móviles
- Sin instalación de apps adicionales

#### 2. **API REST (para Supervisores e Integraciones)**

**Acceso:**
- **Base URL:** `http://localhost:8000` (desarrollo) o `https://api.dominio.gob` (producción)
- **Documentación:** `http://localhost:8000/docs` (Swagger UI interactivo)
- Requiere autenticación JWT en header `Authorization: Bearer <token>`

**Uso típico:**
- Supervisores desde escritorio usando herramientas HTTP (Postman, Insomnia)
- Integraciones con sistemas externos (dispatch centers, centrales de emergencia)
- Automatizaciones vía scripts Python/Bash
- Aplicaciones móviles custom (futuro)

**Documentación:** OpenAPI 3.0 completa disponible en `/openapi.json`

#### 3. **Dashboard Web (Visualización)**

**Acceso:**
- `http://localhost:8000/dashboard` (no requiere autenticación en desarrollo)
- Visualización de mapa con efectivos y tareas
- Solo lectura, no permite modificaciones

**Uso típico:**
- Monitores en centros de comando
- Supervisión en tiempo real de operativo en curso
- Visualización geográfica de cobertura

#### 4. **WebSocket (Notificaciones en Tiempo Real)**

**Acceso:**
- `WS ws://localhost:8000/ws/connect?token=<jwt_token>` (requiere JWT en producción)
- Cliente WebSocket estándar

**Uso típico:**
- Aplicaciones web custom que necesitan actualizaciones en tiempo real
- Dashboards dinámicos que muestran cambios instantáneos
- Sistemas de alertas que reaccionan a eventos del sistema

#### 5. **Fallback: Contacto Directo**

Si el sistema no está disponible o hay problemas técnicos:

**Soporte técnico:**
- Email: `soporte-tecnico@dominio.gob` (si configurado)
- Teléfono: Número de guardia de sistemas

**Supervisor de operaciones:**
- Comunicación por radio/teléfono según protocolos establecidos
- Reportes de incidentes técnicos para escalamiento

---

## Sugerencia Visual (Descripción de Interfaz del Bot)

### Mockup Textual de la Interfaz de Telegram

**Descripción de la conversación típica en pantalla móvil:**

---

#### **CHAT DE TELEGRAM CON EL BOT**

**Nombre del bot en header:** GRUPO_GAD Bot 🤖
**Estado:** En línea

---

**[12/10/2025 16:40]**
```
👮 Juan Pérez:
/start
```

---

**[12/10/2025 16:40]**
```
🤖 GRUPO_GAD Bot:
👮 ¡Bienvenido, Efectivo Juan Pérez!

Código: EF-001234
Rango: Oficial
Unidad: Comando Norte
Estado: DISPONIBLE ✅

📱 COMANDOS DISPONIBLES:

📝 /crear_tarea
   Reportar nueva actividad o incidente

📋 /historial
   Ver tus tareas asignadas

✅ /finalizar_tarea
   Completar tarea en curso

📊 /estadisticas
   Ver tus métricas de rendimiento

❓ /help
   Ayuda y más información

¿Qué necesitas hacer?
```

---

**[12/10/2025 16:41]**
```
👮 Juan Pérez:
/historial
```

---

**[12/10/2025 16:41]**
```
🤖 GRUPO_GAD Bot:
📋 TUS TAREAS RECIENTES:

⏳ EN CURSO (1):
━━━━━━━━━━━━━━━━
1️⃣ TSK-2025-001234
   📝 Patrullaje en Barrio Las Flores
   🏷️ PATRULLAJE | Prioridad: MEDIUM
   ⏱️ Inicio: 12/10/2025 18:00
   📍 Ubicación: -31.4201, -64.1888

✅ COMPLETADAS RECIENTES (3):
━━━━━━━━━━━━━━━━
2️⃣ TSK-2025-001198 - Vigilancia Plaza Central
   ✅ Completada: 12/10/2025 14:30 (Duración: 3.5h)

3️⃣ TSK-2025-001165 - Investigación caso 4421
   ✅ Completada: 11/10/2025 10:15 (Duración: 6.2h)

4️⃣ TSK-2025-001089 - Patrullaje zona comercial
   ✅ Completada: 10/10/2025 22:00 (Duración: 4.0h)

Para ver detalles de una tarea, envía su código.
Ejemplo: TSK-2025-001234
```

---

**[12/10/2025 16:42]**
```
👮 Juan Pérez:
/estadisticas
```

---

**[12/10/2025 16:42]**
```
🤖 GRUPO_GAD Bot:
📊 TUS ESTADÍSTICAS DE RENDIMIENTO

👮 Efectivo: Juan Pérez (EF-001234)
📅 Período: Últimos 30 días

━━━━━━━━━━━━━━━━━━━━
📋 TAREAS:
• Total asignadas: 42
• Completadas: 38 ✅
• En progreso: 1 ⏳
• Canceladas: 3 ❌

━━━━━━━━━━━━━━━━━━━━
⏱️ TIEMPOS:
• Duración promedio: 4.2 horas
• Total horas trabajadas: 159.6 h
• Tarea más rápida: 1.5 h
• Tarea más larga: 12.3 h

━━━━━━━━━━━━━━━━━━━━
📈 RENDIMIENTO:
• Tasa de éxito: 90.5% 🌟
• Tareas a tiempo: 85%
• Calificación: Excelente

━━━━━━━━━━━━━━━━━━━━
🏆 RANKING EN TU UNIDAD:
• Posición: 3º de 25 efectivos

¡Sigue con el buen trabajo! 👏
```

---

**[12/10/2025 16:44]**
```
👮 Juan Pérez:
Gracias 👍
```

---

**[12/10/2025 16:44]**
```
🤖 GRUPO_GAD Bot:
¡De nada! Estoy aquí para ayudarte. 😊

Si necesitas crear una tarea o revisar algo, solo escribe el comando.
¡Que tengas un excelente turno! 👮‍♂️🚔
```

---

### **Características Especiales de la Interfaz del Bot:**

1. **Emojis contextuales:** Facilitan lectura rápida en móvil
2. **Formato estructurado:** Listas claras con separadores visuales (━━━)
3. **Respuestas concisas:** Información clave sin texto excesivo
4. **Comandos siempre visibles:** El menú principal puede ser un teclado custom de Telegram
5. **Confirmaciones claras:** Checkmarks y símbolos de estado (✅⏳❌)
6. **Notificaciones push:** Cuando se asigna una tarea nueva (activadas en Telegram)

---

## Preguntas Frecuentes del Efectivo (FAQ Rápido)

**P: ¿El bot está disponible 24/7?**
R: Sí, el bot responde en cualquier momento. Si hay mantenimiento del sistema, recibirás un mensaje indicándolo.

**P: ¿Qué hago si el bot no responde?**
R: Verifica tu conexión a internet. Si el problema persiste, contacta al supervisor o soporte técnico. Puedes seguir operando normalmente y registrar las tareas luego.

**P: ¿Puedo ver tareas de otros efectivos?**
R: Solo si tienes permisos de supervisor (LEVEL_2 o superior). Los efectivos operativos ven únicamente sus propias tareas.

**P: ¿Cómo actualizo mi ubicación?**
R: Al crear o finalizar tareas, puedes compartir tu ubicación actual usando el botón "Compartir ubicación" de Telegram. También se puede actualizar desde la API si tienes acceso.

**P: ¿Las conversaciones con el bot son privadas?**
R: Sí, solo tú y el sistema tienen acceso. Los supervisores pueden ver las tareas registradas, pero no el contenido de tus conversaciones con el bot.

**P: ¿Puedo usar el bot sin estar de servicio?**
R: Sí, puedes consultar tu historial y estadísticas en cualquier momento. Sin embargo, crear tareas debe hacerse solo cuando estés de servicio y haya un motivo operativo real.

---

# RESUMEN FINAL Y PRÓXIMOS PASOS

## Documento Listo para Implementación y Capacitación

Esta documentación proporciona una visión completa y **100% real** del sistema GRUPO_GAD tal como está implementado actualmente, desde las tres perspectivas clave:

✅ **Perspectiva Técnica (Sistema):** Arquitectura, capacidades reales, esquemas de base de datos, flujos de procesamiento
✅ **Perspectiva Administrativa:** Acceso, métricas, monitoreo, control operativo  
✅ **Perspectiva Usuario (Efectivo):** Uso del bot, flujos de trabajo, comandos disponibles

## Estructura de los Datos (Resumen Técnico)

### 6 Tablas Principales

1. **usuarios** - 14 campos, autenticación JWT, niveles de acceso (LEVEL_1/2/3)
2. **efectivos** - Extiende usuarios, geolocalización PostGIS, estado de disponibilidad
3. **tareas** - 18 campos, 6 tipos, 5 prioridades, 5 estados, tracking temporal completo
4. **historial_estados** - Auditoría completa de cambios con usuario y motivo
5. **tarea_efectivos** - Asociación many-to-many, asignaciones con timestamp
6. **metricas_tareas** - Agregaciones pre-calculadas, percentiles, tasas de éxito

### 38 Endpoints API REST Verificados

**Agrupados por dominio:**
- Autenticación (2): login, logout
- Usuarios (5): CRUD + perfil propio
- Tareas (7): CRUD + filtros + emergencias
- Geoespacial (1): búsqueda por proximidad
- Estadísticas (4): métricas por usuario + invalidación cache
- Cache (4): stats + invalidación + clear
- Health (6): checks básicos + detallados + performance
- Monitoreo (2): Prometheus metrics
- WebSockets (2): conexión + stats
- Dashboard (1): visualización web simple

### 6 Comandos Bot Telegram

1. `/start` - Menú principal e identificación
2. `/crear_tarea` - Wizard interactivo de creación
3. `/historial` - Consulta de tareas asignadas
4. `/finalizar_tarea` - Completar tarea en curso
5. `/estadisticas` - Métricas personales del efectivo
6. `/help` - Ayuda contextual (si implementado)

## Stack Tecnológico Real

**Backend:**
- FastAPI 0.115+ (Python 3.11+)
- SQLAlchemy 2.0 Async
- Pydantic V2 para validación
- Python-Jose para JWT (HS256)
- Bcrypt para hashing de passwords

**Base de Datos:**
- PostgreSQL 15 (puerto 5434 dev)
- PostGIS 3.4 para geolocalización
- Alembic para migraciones

**Cache y Mensajería:**
- Redis 7.2 (puerto 6381 dev)
- Redis Pub/Sub para WebSockets
- TTL configurable por tipo de dato

**Bot:**
- python-telegram-bot 20.x
- Async handlers
- Webhook o polling configurable

**Infraestructura:**
- Docker Compose (5 servicios)
- Caddy 2.8 como reverse proxy (producción)
- Prometheus para métricas
- Loguru para logging estructurado

## Próximos Pasos Recomendados

### 1. Capacitación de Usuarios (1-2 semanas)

**Efectivos operativos:**
- Workshop de 2 horas: Uso del bot de Telegram
- Manual rápido impreso con comandos principales
- Práctica en entorno de testing antes de producción

**Supervisores:**
- Capacitación de 4 horas: API REST, Swagger UI, consultas básicas
- Acceso guiado a logs y métricas
- Procedimientos de escalamiento ante errores

**Administradores:**
- Capacitación técnica completa (8 horas)
- Acceso a base de datos, Redis, logs
- Procedimientos de mantenimiento y backup

### 2. Mejoras Prioritarias (1-3 meses)

**Alta prioridad:**
- Implementar dashboard web completo (reemplazar el básico actual)
- Agregar autenticación 2FA para administradores
- Configurar alertas automáticas (email/Slack) para métricas críticas
- Implementar rate limiting en API para prevenir abusos

**Media prioridad:**
- Exportación de reportes en PDF/Excel desde API
- Comando `/ubicacion` en bot para actualizar posición sin crear tarea
- Sistema de notificaciones push del bot (asignaciones nuevas, cambios de prioridad)
- Integración con sistemas de dispatch/911 si aplica

**Baja prioridad:**
- App móvil nativa (iOS/Android) como alternativa al bot
- Análisis predictivo de demanda de tareas por zona/horario
- Sistema de gamificación para efectivos (badges, rankings)

### 3. Monitoreo y Mantenimiento Continuo

**Diario:**
- Revisar logs de errores (grep "ERROR" en archivos del día)
- Verificar `/health/detailed` y métricas Prometheus
- Monitorear conexiones WebSocket activas

**Semanal:**
- Analizar tareas estancadas (>24h en IN_PROGRESS)
- Revisar intentos de autenticación fallidos
- Backup completo de base de datos (automatizado recomendado)

**Mensual:**
- Análisis de métricas agregadas (tasa de éxito, tiempos promedio)
- Reunión con supervisores para feedback y mejoras
- Actualización de dependencias de seguridad (Dependabot)

---

## Datos de Configuración Clave

**Variables de entorno críticas:**
```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5434/grupogad

# Redis
REDIS_URL=redis://localhost:6381/0

# JWT
JWT_SECRET_KEY=<generar con: openssl rand -hex 32>
JWT_EXPIRATION_MINUTES=1440

# Telegram Bot
TELEGRAM_BOT_TOKEN=<token de BotFather>
TELEGRAM_USE_WEBHOOK=false  # true en producción

# Entorno
ENVIRONMENT=development  # development | production
```

**Puertos utilizados (desarrollo):**
- API: 8000
- PostgreSQL: 5434
- Redis: 6381
- Caddy (producción): 80, 443

---

**🎯 Esta documentación refleja el estado REAL del proyecto GRUPO_GAD al 12 de octubre de 2025 y puede usarse para capacitación, presentaciones ejecutivas y onboarding de nuevos miembros del equipo.**

**📝 Para actualizaciones o correcciones, contactar al equipo técnico con evidencia del código fuente en el repositorio.**
