# ✏️ CORRECCIONES DETALLADAS: MANUAL GRUPO_GAD

**Documento complementario de:** ANALISIS_MANUAL_VS_PROYECTO_REAL.md  
**Propósito:** Proporcionar correcciones específicas línea por línea del manual

---

## 📝 PARTE 1: RESUMEN EJECUTIVO CORREGIDO

### ❌ VERSIÓN ORIGINAL (INCORRECTA)

> GRUPO_GAD es un sistema agéntico de inteligencia artificial diseñado para automatizar y optimizar procesos de gestión administrativa distrital, incluyendo análisis de datos geográficos, gestión documental y servicios ciudadanos. El sistema integra capacidades de procesamiento de lenguaje natural, análisis de datos PostgreSQL/PostGIS y automatización de flujos de trabajo administrativos a través de interfaces web interactivas.

### ✅ VERSIÓN CORREGIDA

> **GRUPO_GAD** es un sistema de gestión de tareas operacionales diseñado para coordinar y supervisar operaciones de seguridad y vigilancia. El sistema combina una API REST FastAPI, un bot de Telegram para personal operativo y un dashboard de monitoreo en tiempo real. Gestiona tareas de patrullaje, investigación, vigilancia e intervención, con seguimiento geoespacial mediante PostgreSQL+PostGIS, caché Redis y notificaciones en tiempo real vía WebSockets.

---

## 📝 PARTE 2: ESPECIFICACIONES DEL PROYECTO CORREGIDAS

### ❌ DESCRIPCIÓN BREVE ORIGINAL

> Sistema agéntico IA que automatiza procesos administrativos distritales mediante análisis de datos espaciales, gestión documental inteligente y atención automatizada de servicios ciudadanos.

### ✅ DESCRIPCIÓN BREVE CORREGIDA

> Sistema backend para gestión de tareas operacionales de seguridad, con API REST, Bot de Telegram y dashboard geoespacial. Coordina efectivos en campo, registra actividades y genera métricas de rendimiento operacional.

---

## 📝 PARTE 3: CAPACIDADES PRINCIPALES CORREGIDAS

### **CAPACIDAD 1: GESTIÓN GEOESPACIAL**

#### ❌ ORIGINAL
> **Análisis Geoespacial Inteligente** — Procesa y analiza datos geográficos mediante PostGIS, generando insights automáticos sobre territorios, zonas y distribución de servicios distritales.

#### ✅ CORREGIDA
> **Registro y Visualización Geoespacial** — Almacena coordenadas geográficas (lat/lon) de tareas operacionales y las visualiza en un dashboard con mapa interactivo. Permite filtrar tareas por radio de distancia desde un punto central para optimizar asignaciones.

---

### **CAPACIDAD 2: GESTIÓN DOCUMENTAL**

#### ❌ ORIGINAL
> **Gestión Documental Automatizada** — Clasifica, indexa y recupera documentos administrativos mediante procesamiento de lenguaje natural y extracción de entidades.

#### ✅ ELIMINAR COMPLETAMENTE
Esta funcionalidad **NO existe** en el proyecto. Eliminar toda la sección.

---

### **CAPACIDAD 3: GESTIÓN DE TAREAS**

#### ❌ ORIGINAL
> **Atención Ciudadana Conversacional** — Responde consultas sobre trámites, servicios y normativas distritales mediante interfaz conversacional natural.

#### ✅ CORREGIDA
> **Gestión de Tareas Operacionales vía Bot** — Bot de Telegram que permite al personal operativo:
> - Crear tareas (patrullaje, investigación, vigilancia, intervención)
> - Consultar historial de tareas asignadas
> - Finalizar tareas con reporte de resultados
> - Recibir notificaciones push de nuevas asignaciones
> - Visualizar estadísticas personales (productividad, tiempos)

---

### **CAPACIDAD 4: SEGUIMIENTO Y AUDITORÍA**

#### ❌ ORIGINAL
> **Automatización de Flujos Administrativos** — Ejecuta procesos predefinidos (validaciones, aprobaciones, notificaciones) reduciendo intervención manual.

#### ✅ CORREGIDA
> **Seguimiento Automático de Tareas** — El sistema registra automáticamente:
> - Historial completo de cambios de estado (PROGRAMMED → IN_PROGRESS → COMPLETED)
> - Usuario responsable de cada cambio
> - Timestamp preciso de cada transición
> - Motivos de cambios de estado
> - Notificaciones en tiempo real vía WebSocket y Telegram

---

### **CAPACIDAD 5: MÉTRICAS OPERACIONALES**

#### ❌ ORIGINAL
> **Generación de Reportes Inteligentes** — Crea reportes automáticos con análisis estadístico y visualizaciones basadas en datos operativos.

#### ✅ CORREGIDA
> **Estadísticas Operacionales con Caché** — Endpoints API que devuelven métricas agregadas:
> - Total de tareas por usuario (completadas, en progreso, canceladas)
> - Duración promedio de tareas por tipo y prioridad
> - Tasa de éxito (completadas vs. totales)
> - Productividad diaria (tareas/día)
> - Percentiles de duración (p25, p50, p75)
> - Caché Redis (TTL 5 min) para optimizar consultas frecuentes

---

### **CAPACIDAD 6: INTEGRACIONES**

#### ❌ ORIGINAL
> **Integración Multi-Sistema** — Conecta bases de datos legacy, APIs externas y sistemas de gestión municipal existentes.

#### ✅ CORREGIDA
> **Integración Telegram** — El sistema se integra con Telegram Bot API para notificaciones push al personal operativo. Arquitectura interna con comunicación API ↔ Bot ↔ WebSocket para sincronización en tiempo real.

---

## 📝 PARTE 4: INTEGRACIONES CORREGIDAS

### **CANALES**

#### ❌ ORIGINAL
- Interfaz web HTML/JavaScript (aplicación principal)
- Shell scripts para automatización de tareas administrativas
- API REST para integraciones externas

#### ✅ CORREGIDO
- **API REST FastAPI** (puerto 8000): `/api/v1/*` endpoints para gestión de usuarios, tareas, estadísticas
- **Bot de Telegram**: Interfaz principal para personal operativo en campo
- **WebSockets** (`/ws/connect`): Comunicación en tiempo real para notificaciones y actualizaciones de estado
- **Dashboard web simple** (`/dashboard`): Visualización de mapa con tareas y efectivos
- **Reverse Proxy Caddy**: Puerto 80/443 para acceso HTTPS

---

### **BASES DE DATOS Y ALMACENAMIENTO**

#### ❌ ORIGINAL
- PostgreSQL con extensión PostGIS (datos espaciales)
- Sistema de archivos para documentos y logs
- Makefiles para gestión de configuraciones

#### ✅ CORREGIDO
- **PostgreSQL 15 + PostGIS 3.4** (puerto 5434): Base de datos principal con soporte geoespacial
- **Redis 7.2** (puerto 6381):
  - Caché de consultas frecuentes (CacheService)
  - Pub/Sub para broadcast de WebSocket cross-workers
  - Stats de endpoints
- **Logs estructurados**: Archivos `.log` gestionados por Loguru con rotación automática
- **Makefile**: Solo para desarrollo (comandos: `make up`, `make down`, `make migrate`, `make test`)

---

### **SISTEMAS EXTERNOS**

#### ❌ ORIGINAL
- APIs de servicios municipales
- Sistemas de gestión documental legacy
- Plataformas de notificaciones ciudadanas

#### ✅ CORREGIDO
- **Telegram Bot API**: Única integración externa para envío/recepción de mensajes
- **Sistema autocontenido**: No hay integraciones con sistemas legacy o externos adicionales

---

## 📝 PARTE 5: CARACTERÍSTICAS DE COMPORTAMIENTO CORREGIDAS

### **TIEMPOS DE RESPUESTA**

#### ❌ ORIGINAL
- Consultas simples: < 2 segundos
- Análisis geoespacial: < 5 segundos
- Generación de reportes: < 10 segundos

#### ✅ CORREGIDO
- **Endpoints API sin caché**: 50-200 ms (consultas a DB)
- **Endpoints con caché Redis**: 5-10 ms (hit rate >80%)
- **Consultas geoespaciales** (`/geo/map/view`): 100-300 ms dependiendo del radio
- **WebSocket latency**: < 50 ms para mensajes broadcast
- **Smoke test objetivo**: 16/16 checks en < 30 segundos

---

### **TONO DE COMUNICACIÓN**

#### ❌ ORIGINAL
> Formal-profesional con claridad ciudadana, lenguaje administrativo accesible, empático en atención a usuarios.

#### ✅ CORREGIDO
> **Bot de Telegram:** Tono directo y operativo, uso de emojis para claridad visual (🚨 emergencias, ✅ completado, ⚠️ advertencias). Mensajes concisos optimizados para lectura en móvil en situaciones de campo.

---

### **REGISTROS QUE MANTIENE**

#### ❌ ORIGINAL
- Logs de interacciones en PostgreSQL (timestamp, usuario, acción, resultado)
- Historial de consultas y respuestas en base de datos
- Auditoría de cambios en documentos (quién, cuándo, qué)
- Métricas de rendimiento en tablas de monitoreo

#### ✅ CORREGIDO
- **Historial de estados de tareas** (tabla `historial_estados`):
  - Cada cambio de estado (PROGRAMMED → IN_PROGRESS → COMPLETED)
  - Usuario responsable, timestamp, motivo
- **Métricas agregadas** (tabla `metricas_tareas`):
  - Por tipo de tarea y prioridad
  - Total tareas, horas, promedios, percentiles, tasa de éxito
- **Logs estructurados de aplicación** (Loguru):
  - Nivel INFO/WARNING/ERROR con contexto JSON
  - Rotación: 10 MB por archivo, 7 días de retención
- **Métricas Prometheus** (endpoint `/metrics`):
  - Request count, latencies, error rates
  - Métricas de sistema (CPU, memoria, disco)

---

## 📝 PARTE 6: DATOS QUE REGISTRA - CORRECCIONES

### **ELIMINAR TABLAS FICTICIAS**

#### ❌ Tabla documentada: `interacciones_log`
**NO EXISTE.** Eliminar completamente del manual.

#### ❌ Tabla documentada: `documentos_procesados`
**NO EXISTE.** Eliminar completamente del manual.

---

### **DOCUMENTAR TABLAS REALES**

#### ✅ **Tabla 1: `usuarios`**

```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL,
    dni VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    telefono VARCHAR(20),
    telegram_id BIGINT UNIQUE,  -- ID de Telegram para notificaciones
    nivel ENUM('LEVEL_1', 'LEVEL_2', 'LEVEL_3') NOT NULL,  -- Jerarquía operacional
    hashed_password VARCHAR(255) NOT NULL,
    verificado BOOLEAN DEFAULT FALSE NOT NULL,
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    intentos_fallidos INTEGER DEFAULT 0 NOT NULL,
    bloqueado_hasta TIMESTAMP WITH TIME ZONE,  -- Bloqueo por intentos fallidos
    extra_data JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP  -- Soft delete
);
```

**Descripción:**
- Usuario del sistema (personal operativo: coordinadores y efectivos)
- Niveles jerárquicos: LEVEL_1 (supervisor), LEVEL_2 (coordinador), LEVEL_3 (efectivo)
- Vinculación con Telegram mediante `telegram_id`
- Seguridad: control de intentos fallidos y bloqueo temporal

---

#### ✅ **Tabla 2: `efectivos`**

```sql
CREATE TABLE efectivos (
    id INTEGER PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL,
    usuario_id INTEGER UNIQUE NOT NULL REFERENCES usuarios(id),
    codigo_interno VARCHAR(50) UNIQUE NOT NULL,  -- Ej: "EF-001"
    rango VARCHAR(50),  -- Ej: "Oficial", "Cabo", "Sargento"
    unidad VARCHAR(100),  -- Ej: "Unidad Norte"
    especialidad VARCHAR(100),  -- Ej: "K9", "Tránsito", "Investigación"
    estado_disponibilidad ENUM('DISPONIBLE', 'EN_TAREA', 'FUERA_SERVICIO', 'NO_DISPONIBLE') NOT NULL,
    ultima_actualizacion_estado TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metadata JSONB,
    geom GEOMETRY(POINT, 4326),  -- Ubicación actual (PostGIS) - agregado en migración posterior
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);

CREATE INDEX ix_efectivos_codigo_interno ON efectivos(codigo_interno);
CREATE INDEX ix_efectivos_estado_disponibilidad ON efectivos(estado_disponibilidad);
CREATE INDEX ix_efectivos_uuid ON efectivos(uuid);
```

**Descripción:**
- Extiende tabla `usuarios` con información operacional específica
- Estado de disponibilidad actualizado en tiempo real
- Geolocalización con PostGIS para tracking en mapa
- Relación 1:1 con usuario

---

#### ✅ **Tabla 3: `tareas`**

```sql
CREATE TABLE tareas (
    id INTEGER PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL,
    codigo VARCHAR(50) UNIQUE NOT NULL,  -- Ej: "TASK-2025-00123"
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    
    -- Clasificación
    tipo ENUM('PATRULLAJE', 'INVESTIGACION', 'VIGILANCIA', 'INTERVENCION', 
              'ADMINISTRATIVA', 'ENTRENAMIENTO') NOT NULL,
    prioridad ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL') NOT NULL DEFAULT 'MEDIUM',
    
    -- Fechas programadas vs reales
    inicio_programado TIMESTAMP WITH TIME ZONE NOT NULL,
    fin_programado TIMESTAMP WITH TIME ZONE,
    inicio_real TIMESTAMP WITH TIME ZONE,
    fin_real TIMESTAMP WITH TIME ZONE,
    tiempo_pausado INTERVAL,  -- Tiempo acumulado en pausa
    pausado_en TIMESTAMP WITH TIME ZONE,
    
    -- Estado de la tarea
    estado ENUM('PROGRAMMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'PAUSED') 
           NOT NULL DEFAULT 'PROGRAMMED',
    
    -- Asignación
    delegado_usuario_id INTEGER NOT NULL REFERENCES usuarios(id),  -- Responsable principal
    creado_por_usuario_id INTEGER NOT NULL REFERENCES usuarios(id),  -- Quién creó
    
    -- Ubicación geográfica
    ubicacion_lat NUMERIC(10, 8),
    ubicacion_lon NUMERIC(11, 8),
    ubicacion_descripcion TEXT,  -- Ej: "Av. San Martín 500, esquina Belgrano"
    
    -- Efectivos asignados (array de IDs)
    efectivos_asignados INTEGER[] DEFAULT '{}' NOT NULL,
    
    -- Métricas
    duracion_real_horas NUMERIC,  -- Calculado al finalizar
    
    -- Datos adicionales
    notas JSONB DEFAULT '{}' NOT NULL,  -- Anotaciones durante ejecución
    extra_data JSONB DEFAULT '{}' NOT NULL,  -- Datos extensibles
    
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_tareas_fechas 
        CHECK (fin_programado IS NULL OR fin_programado > inicio_programado),
    CONSTRAINT chk_tareas_fechas_reales 
        CHECK ((inicio_real IS NULL AND fin_real IS NULL) OR 
               (inicio_real IS NOT NULL AND fin_real IS NULL) OR 
               (inicio_real IS NOT NULL AND fin_real IS NOT NULL AND fin_real >= inicio_real))
);

-- Índices de performance (agregados en migración 094f640cda5e)
CREATE INDEX idx_tareas_delegado_estado_created 
    ON tareas(delegado_usuario_id, estado, created_at DESC);
CREATE INDEX idx_tareas_active 
    ON tareas(id, estado) WHERE deleted_at IS NULL;
CREATE INDEX idx_tareas_created_at 
    ON tareas(created_at DESC);
CREATE INDEX idx_tareas_estado 
    ON tareas(estado);
```

**Descripción:**
- Núcleo del sistema: registra todas las tareas operacionales
- Tipos específicos de operaciones de seguridad
- Prioridades de CRITICAL (emergencias) a LOW (administrativas)
- Seguimiento completo de tiempos programados vs reales
- Soporte para pausas (efectivo debe atender otra urgencia)
- Relación many-to-many con efectivos vía tabla `tarea_efectivos`
- Índices optimizados para consultas frecuentes (usuario + estado)

---

#### ✅ **Tabla 4: `historial_estados`**

```sql
CREATE TABLE historial_estados (
    id INTEGER PRIMARY KEY,
    tarea_id INTEGER NOT NULL REFERENCES tareas(id),
    estado_anterior ENUM('PROGRAMMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'PAUSED'),
    estado_nuevo ENUM('PROGRAMMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'PAUSED') NOT NULL,
    usuario_id INTEGER REFERENCES usuarios(id),  -- Quién hizo el cambio
    motivo TEXT,  -- Ej: "Completado sin incidentes", "Cancelado por orden superior"
    extra_data JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);
```

**Descripción:**
- Auditoría completa de cambios de estado
- Rastreable: quién cambió, cuándo, por qué
- Inmutable: solo inserts, no updates (log append-only)

---

#### ✅ **Tabla 5: `tarea_efectivos`** (Asociación many-to-many)

```sql
CREATE TABLE tarea_efectivos (
    tarea_id INTEGER NOT NULL REFERENCES tareas(id),
    efectivo_id INTEGER NOT NULL REFERENCES efectivos(id),
    PRIMARY KEY (tarea_id, efectivo_id)
);
```

**Descripción:**
- Permite asignar múltiples efectivos a una tarea (patrullajes, operativos)
- Complementa el campo `efectivos_asignados` en tareas (redundancia intencional para performance)

---

#### ✅ **Tabla 6: `metricas_tareas`**

```sql
CREATE TABLE metricas_tareas (
    id INTEGER PRIMARY KEY,
    tipo_tarea ENUM('PATRULLAJE', 'INVESTIGACION', 'VIGILANCIA', 'INTERVENCION', 
                    'ADMINISTRATIVA', 'ENTRENAMIENTO') NOT NULL,
    prioridad ENUM('LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL') NOT NULL,
    
    -- Métricas agregadas
    total_tareas INTEGER NOT NULL,
    total_horas REAL NOT NULL,
    tiempo_promedio_horas REAL,
    tasa_exito DECIMAL(5,2),  -- % completadas
    
    -- Percentiles de duración
    duracion_p25 REAL,
    duracion_p50 REAL,  -- Mediana
    duracion_p75 REAL,
    duracion_min REAL,
    duracion_max REAL,
    
    ultima_actualizacion TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);
```

**Descripción:**
- Métricas pre-agregadas para dashboards
- Actualización periódica (job nocturno o trigger)
- Consulta rápida sin agregaciones en tiempo real

---

## 📝 PARTE 7: DASHBOARD REAL

### ❌ DESCRIPCIÓN ORIGINAL (FICTICIA)

El manual describe un dashboard complejo con:
- URL: `https://gad-admin.dominio.gob/dashboard`
- KPIs: Volumen de Interacciones, Tasa de Éxito, Tiempo Medio Respuesta, % Escalado a Humano
- Gráficos: Líneas temporales, barras horizontales, donut charts
- Tabla de "Últimas Interacciones" con intents detectados
- 4 roles: Administrador General, Operador de Soporte, Analista de Datos, Auditor

### ✅ REALIDAD

**Dashboard Simple Actual:**
- **URL:** `http://localhost:8000/dashboard` (o tras Caddy)
- **Contenido:**
  - Mapa interactivo (OpenStreetMap o similar)
  - Marcadores de tareas (color según prioridad)
  - Posición de efectivos disponibles (si tienen geolocalización)
  - Panel lateral con lista de tareas activas
  - Filtros básicos: tipo de tarea, estado, prioridad
- **NO tiene:**
  - Sistema de roles diferenciados
  - KPIs complejos como "tasa de éxito de chatbot"
  - Gráficos estadísticos avanzados
  - Tabla de "interacciones" (porque no es un chatbot)

**Evidencia:**
```python
# src/api/routers/dashboard.py
@router.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
```

El template HTML es básico y consume:
- `/api/v1/geo/map/view` para obtener tareas y efectivos
- WebSocket `/ws/connect` para actualizaciones en tiempo real

---

## 📝 PARTE 8: EXPERIENCIA DE USUARIO REAL (BOT DE TELEGRAM)

### ❌ FLUJO ORIGINAL (FICTICIO)

El manual describe conversaciones ciudadano-chatbot:
```
Usuario: "Hola, quiero construir un garage en mi casa, ¿qué permiso necesito?"
Agente: "Hola, entendido. Para construir un garage necesitás un permiso de obra menor..."
```

### ✅ FLUJO REAL (BOT DE TELEGRAM PARA EFECTIVOS)

#### **Escenario 1: Crear Tarea de Patrullaje**

```
Efectivo: /crear_tarea

Bot: 📋 *Crear Nueva Tarea*
     Selecciona el tipo:
     
     [🚔 Patrullaje] [🔍 Investigación]
     [👁️ Vigilancia] [🚨 Intervención]
     [📄 Administrativa] [🎯 Entrenamiento]

Efectivo: [Toca "Patrullaje"]

Bot: Ingresa el título de la tarea:

Efectivo: Patrullaje Zona Centro

Bot: Ingresa la descripción (o /skip para omitir):

Efectivo: Recorrido rutinario por Av. San Martín y aledañas

Bot: Selecciona la prioridad:
     [🟢 Baja] [🟡 Media] [🟠 Alta] [🔴 Urgente] [⚫ Crítica]

Efectivo: [Toca "Media"]

Bot: ¿Deseas agregar ubicación?
     [📍 Enviar ubicación] [⏭️ Omitir]

Efectivo: [Envía ubicación GPS: -31.4201, -64.1888]

Bot: ✅ *Tarea Creada Exitosamente*
     
     📌 Código: TASK-2025-00456
     🚔 Tipo: Patrullaje
     📝 Título: Patrullaje Zona Centro
     🟡 Prioridad: Media
     📍 Ubicación: -31.4201, -64.1888
     👤 Asignado a: Juan Pérez (tú)
     
     [Ver en mapa] [Iniciar ahora]
```

---

#### **Escenario 2: Consultar Historial**

```
Efectivo: /historial

Bot: 📊 *Tu Historial de Tareas*
     
     🟢 *COMPLETADAS* (Últimas 5)
     
     1️⃣ TASK-2025-00450
        Patrullaje Zona Norte
        ✅ Completado 11/10/2025 18:30
        ⏱️ Duración: 2.5 horas
     
     2️⃣ TASK-2025-00443
        Vigilancia Plaza Central
        ✅ Completado 11/10/2025 14:00
        ⏱️ Duración: 3 horas
     
     3️⃣ TASK-2025-00438
        Investigación incidente Calle 9
        ✅ Completado 10/10/2025 22:15
        ⏱️ Duración: 4.5 horas
     
     🔵 *EN PROGRESO* (1)
     
     1️⃣ TASK-2025-00456
        Patrullaje Zona Centro
        ▶️ Iniciado hace 45 minutos
        [Finalizar] [Pausar]
     
     [← Anterior] [Siguiente →] [Cerrar]
```

---

#### **Escenario 3: Finalizar Tarea**

```
Efectivo: [Toca "Finalizar" en tarea activa]

Bot: 📝 *Finalizar Tarea TASK-2025-00456*
     
     Patrullaje Zona Centro
     Iniciado: 12/10/2025 14:00
     Duración: 2 horas 15 minutos
     
     Ingresa un resumen de resultados:

Efectivo: Patrullaje completado sin incidentes. Se realizó control de velocidad en Av. San Martín. 3 infracciones leves registradas.

Bot: ✅ *Tarea Finalizada*
     
     TASK-2025-00456 marcada como COMPLETADA
     Duración final: 2h 15m
     
     📈 *Tus Estadísticas Hoy*
     Total completadas: 3
     Tiempo total: 7h 45m
     Promedio: 2h 35m/tarea
     
     [Ver historial] [Nueva tarea] [Estadísticas]
```

---

#### **Escenario 4: Notificación de Asignación**

```
[Notificación push llega al efectivo]

Bot: 🚨 *Nueva Tarea Asignada*
     
     📌 TASK-2025-00458
     🔴 URGENTE - Intervención
     
     📝 Título: Alarma activada en Banco Central
     📍 Ubicación: Calle Rivadavia 234
     👤 Creado por: Coord. Martínez
     ⏰ Inicio programado: INMEDIATO
     
     ⚠️ Esta tarea requiere respuesta urgente
     
     [Aceptar y comenzar] [Ver detalles]
```

---

## 📝 PARTE 9: ENDPOINTS API REALES DOCUMENTADOS

### ✅ **ESTRUCTURA COMPLETA DE ENDPOINTS**

```
BASE URL: http://localhost:8000/api/v1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 AUTENTICACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

POST   /auth/login
Request:
{
  "username": "juan.perez",
  "password": "password123"
}
Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}

POST   /auth/logout
Headers: Authorization: Bearer {token}
Response: 200 OK

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 USUARIOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET    /users/
Query params: skip=0, limit=100
Response: Array<Usuario>

POST   /users/
Request:
{
  "dni": "12345678",
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@example.com",
  "password": "securepass",
  "nivel": "LEVEL_3",
  "telegram_id": 123456789
}

GET    /users/me
Response: Usuario actual autenticado

GET    /users/{user_id}
Response: Usuario específico

PUT    /users/{user_id}
Request: Campos a actualizar

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 TAREAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET    /tasks/
Query params:
  - estado: PROGRAMMED | IN_PROGRESS | COMPLETED | CANCELLED | PAUSED
  - tipo: PATRULLAJE | INVESTIGACION | VIGILANCIA | INTERVENCION | ADMINISTRATIVA | ENTRENAMIENTO
  - prioridad: LOW | MEDIUM | HIGH | URGENT | CRITICAL
  - delegado_usuario_id: int
  - skip: int (default 0)
  - limit: int (default 100)
Response: Array<Tarea>

POST   /tasks/
Request:
{
  "titulo": "Patrullaje Zona Centro",
  "descripcion": "Recorrido rutinario",
  "tipo": "PATRULLAJE",
  "prioridad": "MEDIUM",
  "inicio_programado": "2025-10-12T14:00:00Z",
  "delegado_usuario_id": 5,
  "ubicacion_lat": -31.4201,
  "ubicacion_lon": -64.1888
}

POST   /tasks/emergency
Request: Similar a POST /tasks/ pero con prioridad forzada a CRITICAL

GET    /tasks/{task_id}
Response: Tarea específica con relaciones

PUT    /tasks/{task_id}
Request: Campos a actualizar (ej: cambio de estado, inicio_real, fin_real)

DELETE /tasks/{task_id}
Response: Tarea marcada como eliminada (soft delete)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗺️ GEOLOCALIZACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET    /geo/map/view
Query params:
  - center_lat: float (requerido)
  - center_lng: float (requerido)
  - radius_m: int (default 10000, max 100000)
Response:
{
  "tareas": [
    {
      "id": 123,
      "titulo": "Patrullaje...",
      "lat": -31.4201,
      "lon": -64.1888,
      "prioridad": "HIGH",
      "estado": "IN_PROGRESS"
    }
  ],
  "usuarios": []  // Vacío si efectivos no tienen geolocalización
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ESTADÍSTICAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET    /stats/user/{user_id}
Query params:
  - days: int (default 30)
  - use_cache: bool (default true)
Response:
{
  "usuario_id": 5,
  "periodo_dias": 30,
  "total_tareas": 45,
  "completadas": 42,
  "en_progreso": 2,
  "canceladas": 1,
  "promedio_duracion_horas": 2.5,
  "productividad_diaria": 1.5,
  "_cache": {
    "hit": true,
    "ttl_seconds": 300
  }
}

POST   /stats/invalidate/user/{user_id}
Response: Caché invalidada para ese usuario

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 CACHÉ (Admin)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET    /cache/stats
Response: Info de Redis (memoria, keys, hit rate, etc.)

POST   /cache/invalidate/{key}
Response: Key eliminada

POST   /cache/invalidate-pattern/{pattern:path}
Example: /cache/invalidate-pattern/stats:user:*
Response: Cantidad de keys eliminadas

POST   /cache/clear
⚠️ PELIGROSO: Limpia todo el caché

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏥 HEALTH & MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET    /health
Response: {"status": "ok"}

GET    /health/detailed
Response: Estado de DB, Redis, disco, memoria

GET    /health/ready
Response: Readiness probe (K8s)

GET    /health/live
Response: Liveness probe (K8s)

GET    /health/performance
Response: Métricas de rendimiento del sistema

GET    /health/government
Response: Métricas específicas del dominio

GET    /metrics
Response: Métricas Prometheus (formato OpenMetrics)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 WEBSOCKETS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WS     /ws/connect
Headers: ?token={jwt_token} (query param)
Mensajes recibidos:
{
  "event_type": "CONNECTION_ACK" | "PING" | "NOTIFICATION" | "TASK_UPDATE",
  "data": {...},
  "timestamp": "2025-10-12T16:45:00Z"
}

GET    /ws/stats
Response:
{
  "total_messages_sent": 1234,
  "total_broadcasts": 56,
  "total_send_errors": 2,
  "last_broadcast_at": "2025-10-12T16:45:00Z",
  "connected_clients": 12
}

POST   /ws/_test/broadcast (solo dev/test)
Request: Mensaje a broadcast

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GET    /dashboard
Response: HTML template
```

---

## 📝 PARTE 10: VARIABLES DE ENTORNO REALES

### ✅ ARCHIVO `.env` COMPLETO

```bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POSTGRESQL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POSTGRES_USER=grupogad
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=grupogad_db
POSTGRES_HOST=db  # Nombre del servicio Docker
POSTGRES_PORT=5432  # Puerto interno del contenedor

# URL completa (alternativa, tiene prioridad sobre variables individuales)
DATABASE_URL=postgresql+asyncpg://grupogad:your_secure_password_here@db:5432/grupogad_db

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REDIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REDIS_HOST=redis  # Nombre del servicio Docker
REDIS_PORT=6379  # Puerto interno
REDIS_DB=0
REDIS_PASSWORD=  # Vacío por defecto, configurar en producción

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# JWT AUTHENTICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECRET_KEY=generate_a_random_secret_key_with_at_least_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TELEGRAM BOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_API_URL=https://api.telegram.org  # Opcional, usar solo si hay proxy

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE=GRUPO GAD API
API_VERSION=1.0.0
API_PREFIX=/api/v1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENVIRONMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENVIRONMENT=development  # development | production | test
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORS (solo desarrollo, ajustar en producción)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEBSOCKET (opcional, usar solo en producción si JWT es obligatorio)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WS_REQUIRE_AUTH=false  # true en producción
```

---

## 🎯 RESUMEN DE CORRECCIONES

### **Secciones a ELIMINAR completamente:**
1. ❌ Capacidad 2: Gestión Documental
2. ❌ Tabla `interacciones_log`
3. ❌ Tabla `documentos_procesados`
4. ❌ Todo el mockup de "Dashboard de Administrador" complejo
5. ❌ Ejemplos de conversaciones con ciudadanos
6. ❌ Referencias a "trámites", "certificados", "permisos de construcción"
7. ❌ Integración con "sistemas legacy" o "APIs municipales"

### **Secciones a REESCRIBIR completamente:**
1. ✅ Resumen Ejecutivo
2. ✅ Descripción breve del proyecto
3. ✅ Todas las capacidades principales (1-6)
4. ✅ Perspectiva de usuario (ciudadano → efectivo)
5. ✅ Estructura de mensajería (chatbot → bot Telegram operativo)

### **Secciones a AGREGAR (no están en el manual):**
1. ➕ Tabla `efectivos`
2. ➕ Tabla `historial_estados`
3. ➕ Tabla `tarea_efectivos`
4. ➕ Documentación del Bot de Telegram (comandos, flujos)
5. ➕ Endpoints WebSocket
6. ➕ Configuración de Redis
7. ➕ Health checks y métricas Prometheus

---

**Documento generado:** 2025-10-12  
**Próximo paso sugerido:** Crear nuevo manual desde cero basándose en estas correcciones
