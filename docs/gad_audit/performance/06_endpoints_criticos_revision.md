# Revisión Manual Exhaustiva de Endpoints Críticos del Sistema Operativo GRUPO_GAD

Auditoría técnica y assessment de cumplimiento para operaciones de campo — 29 de octubre de 2025

## Resumen ejecutivo y alcance

Este informe presenta una revisión técnica exhaustiva de los endpoints críticos del sistema operativo GRUPO_GAD, con foco en su funcionalidad operativa, seguridad, cumplimiento y desempeño bajo escenarios de misión crítica. El análisis se circunscribe a evidencias verificables del código fuente del backend (routers y servicios), la integración con Telegram Bot, el servicio geoespacial PostGIS, la capa de caché y Pub/Sub sobre Redis, y el stack de observabilidad Prometheus/Grafana; complementariamente, se consideran las configuraciones de despliegue y las capacidades de WebSockets para notificaciones en tiempo real.[^1][^2]

El sistema se encuentra en producción (92% completado), soportando operaciones gubernamentales con despliegue en Fly.io, reverse proxy con HTTPS automático, base de datos PostgreSQL con extensión PostGIS, y un bot de Telegram como canal ciudadano. Las capacidades críticas identificadas abarcan: gestión de tareas y un endpoint de emergencia con asignación automática del efectivo más cercano; funciones de geolocalización basadas en geography y SRID 4326; un router de WebSockets con autenticación JWT opcional en desarrollo y obligatoria en producción; un router de métricas para Prometheus; y controles de rate limiting gubernamental en middleware, además de operaciones de caché.[^1][^2]

Principales hallazgos:

- Gestión operativa: endpoints CRUD de tareas, invalidación de caché y un endpoint de emergencia que busca el efectivo más cercano con PostGIS y emite una respuesta con distancia en metros. Falta el módulo explícito de asignación de horarios por operativo.[^1]
- Notificaciones: las notificaciones en tiempo real se soportan mediante WebSockets y difusión cross-worker vía Redis Pub/Sub. No se evidencian endpoints de recordatorios programados a T-40 minutos ni confirmaciones de recepción con semántica robusta.[^1]
- Telegram Bot: comandos de creación, finalización y consulta; flujos de wizard en memoria; uso de un cliente HTTP sincrónico; integración con endpoints de tareas y autenticación; y ausencia de persistencia del estado del wizard en Redis.[^1]
- Geolocalización: servicio PostGIS robusto, con validaciones de coordenadas y uso de geography para precisión. El dashboard expone tareas con geocercas aproximadas vía Haversine; persiste un mock de efectivos con estados y ubicaciones en Buenos Aires.[^1]
- Monitoreo: endpoint /metrics integrado con Prometheus; health checks múltiples (básico, detallado, readiness, liveness y “government-grade”); instrumentación de WebSockets; y 23 reglas de alerta en la configuración de monitoreo.[^1]
- Seguridad y compliance: autenticación JWT con cookies HttpOnly; middleware de rate limiting in-memory (no adecuado para multi-worker); audit logging parcial; cifrado en tránsito garantizado por reverse proxy; cifrado en reposo por verificar; gestión de secretos vía variables de entorno.[^1][^2]
- Performance y escalabilidad: patrones de invalidación de caché; difusión WebSocket vía Pub/Sub; limitaciones del cliente HTTP sincrónico del bot y del rate limiter in-memory; necesidad de benchmarks y pruebas de carga para p95/p99.[^1]

Este documento prioriza recomendaciones operativas para cerrar brechas, con un plan de acción por fases orientado al go-live en un entorno gubernamental crítico.[^1][^2]

## Metodología y fuentes de evidencia

La revisión se realizó mediante lectura dirigida del código de routers y servicios críticos, y correlación con artefactos de configuración y despliegue. Los criterios de evaluación consideraron funcionalidad operativa, seguridad y compliance, desempeño, trazabilidad y escalabilidad.

- Endpoints y routers analizados: tasks (incluyendo /emergency), geo (incluyendo map view y mock de efectivos), websockets (auth, stats, broadcast de prueba), auth (login/logout con JWT y cookies), metrics (Prometheus), cache (stats e invalidación), health (múltiples probes y métricas de performance), y telegram_tasks (creación, finalización y consulta de tareas).[^1]
- Artefactos de configuración y observabilidad: middleware de rate limiting gubernamental, configuración de Prometheus/Grafana con 23 reglas de alerta, servicio PostGIS con dialecto y geography, CacheService y Redis Pub/Sub para WebSockets.[^1]
- Alcance: se evaluó la superficie de endpoints y su interacción con la operación de campo, analizando validaciones, manejo de errores, instrumentación, dependencias externas y riesgos operacionales.[^1]

El análisis se limita por la ausencia de datos de producción en vivo (p95/p99, throughput, uso de Redis en multi-worker), y por falta de verificación directa de cifrado en reposo, persistencia del wizard del bot en Redis y orquestación de recordatorios T-40 minutos.

Para situar las fuentes y su confiabilidad, se presenta el inventario utilizado.

Tabla 1. Inventario de fuentes y artefactos analizados

| Fuente/Componente                 | Propósito                                       | Confiabilidad para auditoría |
|----------------------------------|--------------------------------------------------|------------------------------|
| Repositorio GRUPO_GAD (código)   | Evidencia primaria de endpoints y lógica         | Alta                         |
| Inventario de integraciones      | Contexto de PostGIS, Redis, Telegram y monitoreo | Alta                         |
| Auditoría del Telegram Bot       | Detalle de flujos, riesgos y recomendaciones     | Alta                         |
| Configuraciones críticas         | Middleware, Prometheus, reglas de alerta         | Alta                         |
| Aplicación en producción         | Validación operacional de despliegue             | Media (sin métricas en vivo) |

La combinación de estas fuentes permite trazar hallazgos y recomendaciones respaldados por implementación real y artefactos operativos.[^1]

## Mapa general de endpoints críticos

La superficie de endpoints analizada abarca routers que soportan operaciones de campo y operación gubernamental cotidiana. El control de acceso se realiza con autenticación basada en JWT y, en el caso de WebSockets, con validación opcional en desarrollo y obligatoria en producción. La autorización operativa por rol no está explicitada en todos los endpoints de creación/asignación, constituyendo un área a fortalecer.

Tabla 2. Catálogo de endpoints críticos

| Método | Ruta                                | Propósito                                       | Dependencias                 | Auth requerida |
|--------|-------------------------------------|-------------------------------------------------|------------------------------|----------------|
| GET    | /tasks/                             | Listar tareas                                   | CRUD tareas, DB              | Sí (JWT)       |
| POST   | /tasks/                             | Crear tarea                                     | CRUD tareas, Cache           | Sí (JWT)       |
| GET    | /tasks/{task_id}                    | Obtener tarea por ID                            | CRUD tareas, DB              | Sí (JWT)       |
| PUT    | /tasks/{task_id}                    | Actualizar tarea                                | CRUD tareas, Cache           | Sí (JWT)       |
| DELETE | /tasks/{task_id}                    | Eliminar tarea                                  | CRUD tareas, Cache           | Sí (JWT)       |
| POST   | /tasks/emergency                    | Emergencia y asignación nearest efectivo        | PostGIS, DB, Cache           | Sí (JWT)       |
| GET    | /geo/map/view                       | Vista de mapa (tareas) con radio aproximado     | DB, Haversine                | Sí (JWT)       |
| GET    | /geo/efectivos/mock                 | Efectivos simulados                             | Mock data                    | Sí (JWT)       |
| WS     | /ws/connect                         | Conexión WebSocket con JWT opcional (prod: req.)| WebSocketManager, Redis Pub/Sub| Token (opt/dev)|
| GET    | /ws/stats                           | Estadísticas de WebSockets                      | WebSocketManager             | No/Consultar   |
| POST   | /ws/_test/broadcast                 | Broadcast de prueba (solo no-prod)              | WebSocketManager             | Restringida    |
| GET    | /metrics/prometheus                 | Métricas para Prometheus                        | Instrumentación Prometheus   | No             |
| GET    | /health                             | Health básico                                   | —                            | No             |
| GET    | /health/detailed                    | Health detallado con checks de DB               | DB                           | No             |
| GET    | /health/ready                       | Readiness probe                                 | DB                           | No             |
| GET    | /health/live                        | Liveness probe                                  | —                            | No             |
| GET    | /health/performance                 | Métricas de performance de endpoints y DB       | DB, middleware               | No             |
| GET    | /health/government                  | Health “gubernamental” compuesto                | DB, Redis, WS, sistema       | No             |
| GET    | /cache/stats                        | Estadísticas de caché                           | Redis                        | No             |
| POST   | /cache/invalidate/{key}             | Invalidar key específica                        | Redis                        | No             |
| POST   | /cache/invalidate-pattern/{pattern} | Invalidar patrón de keys                        | Redis                        | No             |
| POST   | /cache/clear                        | Limpiar caché (prefijo “gad:”)                  | Redis                        | No             |
| POST   | /auth/login                         | Login y emisión de JWT (cookie HttpOnly)        | Auth service, DB             | No             |
| POST   | /auth/logout                        | Logout y eliminación de cookie                  | —                            | No             |
| POST   | /telegram/tasks/create              | Crear tarea desde bot                           | DB, WebSocket (alerta urgente)| No             |
| POST   | /telegram/tasks/finalize            | Finalizar tarea por código desde bot            | DB, WebSocket (notificación) | No             |
| GET    | /telegram/tasks/user/{telegram_id}  | Tareas del usuario (por telegram_id)            | DB                           | No             |
| GET    | /telegram/tasks/code/{codigo}       | Detalle de tarea por código                     | DB                           | No             |

Este mapa revela dos patrones operativos: la gestión de tareas con invalidación de caché y un caso de emergencia que combina geolocalización PostGIS con auditoría de negocio; y una capa de notificaciones en tiempo real sobre WebSockets, con difusión cross-worker y un endpoint de métricas alineado a Prometheus.[^1]

## Endpoints de gestión operativa

La gestión de tareas constituye el núcleo operativo. El router de tareas expone CRUD con invalidación de caché sobre patrones y keys específicas; además, el endpoint de emergencia (/tasks/emergency) valida coordenadas, busca el efectivo más cercano y retorna la distancia en metros, emitiendo eventos de auditoría para los casos de éxito, no disponibilidad y errores inesperados.[^1]

Tabla 3. Inventario de endpoints operativos

| Método | Ruta               | Función principal                         | Validaciones clave                         | Dependencias             | Observaciones                          |
|--------|--------------------|-------------------------------------------|--------------------------------------------|--------------------------|----------------------------------------|
| GET    | /tasks/            | Listar tareas                              | skip, limit                                 | DB, CRUD                 | Paginación                             |
| POST   | /tasks/            | Crear tarea                                | Esquema TareaCreate                         | DB, Cache                | Invalida patrones “tasks:list:*”, “stats:user:*” |
| GET    | /tasks/{task_id}   | Obtener tarea por ID                       | task_id existente                           | DB                       | 404 si no existe                       |
| PUT    | /tasks/{task_id}   | Actualizar tarea                           | task_id existente                           | DB, Cache                | Invalida cache por task_id             |
| DELETE | /tasks/{task_id}   | Eliminar tarea                             | task_id existente                           | DB, Cache                | Invalida cache por task_id             |
| POST   | /tasks/emergency   | Emergencia y asignación nearest efectivo   | lat [-90,90], lng [-180,180]                | DB, PostGIS, Cache       | Log de auditoría; 404/503/500 manejo   |

Tabla 4. Flujo de creación/asignación

| Paso | Validación/Operación                         | Servicio       | Evento de auditoría                 | Puntos de fallo                   |
|------|----------------------------------------------|----------------|-------------------------------------|-----------------------------------|
| 1    | Validar esquema TareaCreate                   | API/CRUD       | —                                   | Datos inválidos                   |
| 2    | Crear tarea en DB                             | DB             | “task_created” (implícito)          | Error de DB                       |
| 3    | Invalidar caché por patrón y/o key específica | Cache          | “cache_invalidated”                 | Fallo de Redis/no bloqueo         |
| 4    | Retornar tarea creada                         | API            | —                                   | —                                 |

Tabla 5. Flujo de emergencia

| Paso | Validación/Operación                                 | Servicio     | Respuesta                                   | Manejo de errores                   |
|------|--------------------------------------------------------|--------------|---------------------------------------------|-------------------------------------|
| 1    | Validar lat/lng                                       | API          | —                                           | ValueError/HTTP 400                 |
| 2    | Verificar dialecto PostgreSQL/PostGIS                 | DB           | —                                           | HTTP 503 si no PostGIS              |
| 3    | Query nearest efectivo (geography, SRID 4326)         | PostGIS      | assigned_efectivo_id, distance_m            | HTTP 503 en fallo de consulta       |
| 4    | Si no hay efectivos con geom                          | —            | —                                           | HTTP 404 y log “EMERGENCY_NO_EFECTIVOS” |
| 5    | Log de “EMERGENCY_CREATED”                            | Audit        | status “assigned”                           | —                                   |
| 6    | Invalida caché relacionado                            | Cache        | —                                           | No bloquea respuesta                |
| 7    | Errores inesperados                                   | —            | —                                           | HTTP 500 y log “EMERGENCY_ERROR”    |

### Creación de operativos/allanamientos

La creación de tareas se realiza mediante un esquema con validaciones de negocio. El proceso invalida automáticamente caches que puedan quedar desactualizados (estadísticas de usuario y listados de tareas), manteniendo consistencia entre lecturas y escrituras. Este patrón es adecuado para cargas operativas moderadas; bajo volúmenes altos, se recomienda complementar con TTL y estrategias de refresco escalonado para evitar thundering herd en invalidaciones amplias.[^1]

### Asignación de efectivos

El endpoint de emergencia utiliza la función PostGIS para encontrar el efectivo más cercano, retornando distancia en metros y registrando auditoría por cada evento (creación exitosa, ausencia de efectivos y errores). Este patrón garantiza trazabilidad de asignaciones en campo y soporta decisiones de despacho. Persiste la necesidad de extender la lógica a una asignación formal de horarios y disponibilidades por operativo, que no está evidenciada en el código actual.[^1]

### Consulta de disponibilidad

La vista de mapa del dashboard expone tareas dentro de un radio especificado, filtrando por coordenadas y calculando distancia mediante una aproximación Haversine; los efectivos reales no están presentes y se suplen con un mock que genera estados (patrullando, en base, respondiendo, en tránsito, disponible) y ubicaciones simuladas en Buenos Aires. Esta dualidad es funcional para desarrollo y testing, pero debe ser sustituida por datos reales de ubicación de efectivos para operaciones de campo.[^1]

### Gestión de horarios

No se identificaron endpoints explícitos de gestión de horarios o turnos por efectivo. Se recomienda implementar un módulo dedicado con validaciones de solapamientos, zonas horarias y reglas de descanso, y su integración con la asignación de operativos para garantizar cobertura y cumplimiento normativo.

Tabla 6. Endpoints de horarios (propuestos)

| Método | Ruta                   | Función                              | Validaciones                               | Dependencias            |
|--------|------------------------|--------------------------------------|--------------------------------------------|-------------------------|
| GET    | /schedules/            | Listar horarios                      | filtros por operativo/fecha                | DB                      |
| POST   | /schedules/            | Crear horario                         | fechas, turnos, no solapamiento            | DB, reglas de negocio   |
| PUT    | /schedules/{id}        | Actualizar horario                    | existence, reglas de solapamiento          | DB                      |
| DELETE | /schedules/{id}        | Eliminar horario                      | existence                                   | DB                      |
| GET    | /schedules/efectivo/{id}| Consultar horarios por efectivo      | operativo_id                                | DB                      |

## Endpoints de notificaciones y recordatorios

El sistema soporta notificaciones en tiempo real mediante WebSockets y difusión cross-worker con Redis Pub/Sub. Se identifican eventos de alerta (tareas urgentes creadas desde el bot) y notificaciones de finalización. No se evidencian endpoints específicos para recordatorios programados a T-40 minutos ni confirmaciones de recepción con persistencia y auditoría.[^1]

Tabla 7. Matriz de notificaciones

| Evento                          | Origen                           | Endpoint/Evento              | Destinatarios                 | Canal                        | Estado/Auditoría            |
|---------------------------------|----------------------------------|------------------------------|-------------------------------|------------------------------|-----------------------------|
| Tarea urgente creada            | Bot (wizard)                     | WS broadcast (ALERT)         | Dashboards/admin              | WebSocket + Redis Pub/Sub    | Sin ack persistente         |
| Tarea finalizada                | Bot (comando)                    | WS broadcast (NOTIFICATION)  | Dashboards/admin              | WebSocket + Redis Pub/Sub    | Sin ack persistente         |
| Health “government” degradado   | API (health)                     | HTTP 503 (detalle)           | Monitoreo/LB                  | HTTP                         | Logs                        |
| Métricas actualizadas           | API (/metrics)                   | Prometheus scrape            | Prometheus                    | HTTP (/metrics)              | Instrumentación             |
| Recordatorio T-40               | —                                | —                            | Efectivos                     | —                            | Gap                         |
| Confirmación de recepción       | —                                | —                            | Operador/CRM                  | —                            | Gap                         |

Se recomienda introducir endpoints de recordatorios programados (cron/job) y un flujo de confirmación de recepción con persistencia y correlación de auditoría, evitando dependencias locales en memoria y elevando la resiliencia en despliegues horizontales.[^1]

## Endpoints del Telegram Bot

El bot, construido sobre python-telegram-bot, expone comandos de creación, finalización y consulta; utiliza un wizard multistep y un cliente HTTP sincrónico para interactuar con el backend. La integración se realiza con endpoints de tareas y autenticación; no se evidencia persistencia del estado del wizard en Redis.[^1]

Tabla 8. Comandos del bot y endpoints

| Comando        | Endpoint backend                       | Payload principal                 | Respuesta                    | Manejo de errores              |
|----------------|-----------------------------------------|-----------------------------------|------------------------------|--------------------------------|
| /crear         | POST /telegram/tasks/create             | codigo, titulo, tipo, prioridad   | task_id, codigo, created_at  | Validación usuario/tarea       |
| /finalizar     | POST /telegram/tasks/finalize           | codigo, telegram_id               | success, finalized_at        | 404 si no existe; estado previo|
| /historial     | GET /telegram/tasks/user/{telegram_id}  | telegram_id                       | estadísticas y resúmenes     | Usuario no encontrado          |
| /start         | —                                       | —                                 | Menú principal               | —                              |
| /help          | —                                       | —                                 | Ayuda contextual             | —                              |

Tabla 9. Flujo de wizard (wizard_text_handler)

| Paso | Validación                         | Transición                   | Controles de UI                    |
|------|------------------------------------|------------------------------|------------------------------------|
| 1    | Selección de tipo de tarea         | Avanzar al paso 2            | Teclado de tipos                   |
| 2    | Código (longitud 3–20)             | Avanzar si válido            | Texto + volver                     |
| 3    | Título (10–100 caracteres)         | Avanzar si válido            | Texto                              |
| 4    | Delegado (ID numérico)             | Avanzar si válido            | Texto                              |
| 5    | Asignados (lista no vacía)         | Avanzar si válido            | Selección múltiple                 |
| 6    | Confirmación (resumen visual)      | Crear/Editar/Cancelar        | Teclado de confirmación            |

Riesgos y brechas:

- Cliente HTTP sincrónico del bot: introduce bloqueos de I/O y limita throughput bajo carga; se recomienda migrar a cliente asíncrono.[^1]
- Estado del wizard en memoria: se pierde ante reinicios o escalado horizontal; se recomienda persistencia en Redis con TTL y namespace.[^1]
- Confirmaciones y auditoría: las notificaciones carecen de ack persistente; se recomienda registrar confirmaciones en DB con correlación de auditoría.[^1]

## Endpoints de geolocalización (PostGIS y afines)

El servicio PostGIS implementa una búsqueda de efectivos cercanos con tipo geography y SRID 4326, validando coordenadas y retornando distancia en metros. La vista de mapa del dashboard utiliza un filtro de radio y un cálculo aproximado (Haversine) para seleccionar tareas con coordenadas; el router de efectivos mock ofrece ubicaciones y estados simulados útiles para desarrollo.[^1]

Tabla 10. Inventario geoespacial

| Método | Ruta                 | Parámetros                            | Fórmula/Cálculo            | Retorno                                   |
|--------|----------------------|---------------------------------------|----------------------------|-------------------------------------------|
| —      | find_nearest_efectivo| lat, lng, limit                       | ST_Distance (geography), SRID 4326 | [{efectivo_id, distance_m}]               |
| GET    | /geo/map/view        | center_lat, center_lng, radius_m      | Haversine aproximado       | {usuarios: [], tareas: [{lat, lng, ...}]} |
| GET    | /geo/efectivos/mock  | center_lat, center_lng, radius_m, count| Haversine + simulación     | {usuarios: [{...}], metadata: {...}}      |

Tabla 11. PostGIS: funciones y seguridad

| Función                 | Propósito                                | Validación de entrada     | Manejo de errores      |
|-------------------------|-------------------------------------------|---------------------------|------------------------|
| ST_SetSRID              | Establece SRID en geometría               | Coordenadas rangos        | 503 si no PostGIS      |
| ST_MakePoint            | Crea punto geográfico                     | lng/lat                   | 503 en fallo consulta  |
| ST_Distance             | Distancia entre geometrías (geography)    | geoms no nulos            | 503 en fallo consulta  |
| ORDER BY geom <-> ...   | Ordena por proximidad                     | limit > 0                 | 503 en fallo consulta  |

La precisión de distance_m se apoya en el tipo geography y en un ordenamiento por proximidad que favorece performance; no obstante, bajo volúmenes elevados o grids dispersos, se recomienda verificar índices espaciales y patrones de consulta para evitar degradación.[^1]

## Endpoints de monitoreo y observabilidad

La capa de observabilidad se compone de un endpoint de métricas Prometheus, varios health checks con distintos fines y una instrumentación de WebSockets que alimenta métricas de conexiones, mensajes y errores. Se registran 23 reglas de alerta en la configuración de monitoreo; sin embargo, no se dispone de evidencia directa de su activación en producción ni de paneles de Grafana con datos reales en vivo.[^1]

Tabla 12. Catálogo de health checks

| Endpoint                   | Propósito                              | Checks incluidos                            | Status/Respuestas         |
|---------------------------|-----------------------------------------|---------------------------------------------|---------------------------|
| /health                   | Basic LB compatibility                  | “status: ok”                                 | 200                       |
| /health/detailed          | Detailed system status                  | DB, circuit breaker, tiempo de respuesta     | 200/503                   |
| /health/ready             | Readiness probe                         | DB conectividad                               | 200/503                   |
| /health/live              | Liveness probe                          | “status: alive”                               | 200                       |
| /health/performance       | Performance metrics                     | Query tracker, slowest endpoints, DB insights| 200                       |
| /health/government        | Gubernamental composite health          | DB, Redis, WS, recursos, Telegram             | 200/503                   |

Tabla 13. Métricas Prometheus (ejemplos)

| Métrica                          | Tipo       | Etiquetas                | Fuente                     |
|----------------------------------|------------|--------------------------|----------------------------|
| active_connections               | Gauge      | env                      | WebSocketManager           |
| connections_total                | Counter    | env                      | WebSocketManager           |
| messages_sent_total              | Counter    | env                      | WebSocketManager           |
| broadcasts_total                 | Counter    | env                      | WebSocketManager           |
| send_errors_total                | Counter    | env                      | WebSocketManager           |
| heartbeat_last_timestamp         | Gauge      | env                      | WebSocketManager           |
| role_connections                 | Gauge      | env, role                | WebSocketManager           |
| user_active                      | Gauge      | env                      | WebSocketManager           |
| message_latency_seconds          | Histogram  | env                      | Instrumentación dedicada   |

La actualización de métricas se realiza desde el estado del WebSocketManager y expone buckets de latencia que facilitan la observación de p95/p99. Se recomienda alinear alertas con estas métricas y complementar con latencias por endpoint crítico.[^1]

## Seguridad y compliance

La autenticación se implementa mediante JWT emitido en login y almacenado en cookie HttpOnly con atributos secure y samesite estrictos; el logout elimina la cookie. El middleware de rate limiting aplica límites diferenciados, aunque en memoria, lo que limita su eficacia en despliegues multi-worker. El cifrado en tránsito se garantiza por el reverse proxy con HTTPS automático; el cifrado en reposo no está verificado y requiere activación y pruebas. La gestión de secretos se realiza por variables de entorno y rotación, reforzada por escaneos en CI/CD.[^1][^2]

Tabla 14. Controles de seguridad por endpoint

| Endpoint                 | AuthN/AuthZ                         | Rate limiting                 | Cifrado tránsito         | Cifrado reposo         | Audit logging                         |
|--------------------------|-------------------------------------|-------------------------------|--------------------------|------------------------|---------------------------------------|
| /tasks/*                 | JWT + cookies                       | In-memory (no multi-worker)   | HTTPS via proxy          | Por verificar          | Parcial (eventos de tarea)            |
| /tasks/emergency         | JWT + cookies                       | In-memory                     | HTTPS via proxy          | Por verificar          | Sí (éxito/404/500)                    |
| /geo/*                   | JWT (varía por uso)                 | In-memory                     | HTTPS via proxy          | Por verificar          | No evidenciado                         |
| /ws/connect              | JWT opcional (prod obligatorio)     | WS handshake (10/min)         | HTTPS via proxy          | N/A                    | Logs de conexión/desconexión          |
| /metrics                 | No auth                             | N/A                           | HTTPS via proxy          | N/A                    | N/A                                   |
| /health/*                | No auth                             | N/A                           | HTTPS via proxy          | N/A                    | N/A                                   |
| /cache/*                 | No auth                             | N/A                           | HTTPS via proxy          | N/A                    | Operaciones (invalidación/clear)      |
| /auth/*                  | No auth (login/logout)              | N/A                           | HTTPS via proxy          | N/A                    | Eventos de autenticación              |
| /telegram/tasks/*        | No auth (bot)                       | N/A                           | HTTPS via proxy          | Por verificar          | Parcial (creación/finalización)       |

Tabla 15. Matriz de riesgos de seguridad priorizados

| Riesgo                                      | Criticidad | Probabilidad | Impacto | Score | Acción requerida                                    |
|---------------------------------------------|------------|--------------|---------|-------|-----------------------------------------------------|
| Rate limiting in-memory (multi-worker)      | Medio      | Alta         | Medio   | 7/10  | Migrar a Redis-backed rate limiting                |
| Cliente API del bot sincrónico              | Medio      | Media        | Medio   | 6/10  | Migrar a cliente HTTP asíncrono                     |
| Cifrado en reposo no verificado             | Alto       | Media        | Alto    | 8/10  | Activar y verificar cifrado en BD/backups           |
| Audit trail incompleto                      | Alto       | Alta         | Alto    | 9/10  | Implementar audit logging integral                  |
| Token Telegram sin rotación documentada     | Medio      | Media        | Medio   | 6/10  | Rotación y gestión de secretos centralizada         |

Estas brechas deben atenderse antes del go-live en un entorno gubernamental, particularmente las relacionadas con cifrado en reposo, auditoría y la persistencia de flujos críticos del bot.[^1][^2]

## Performance y escalabilidad

El sistema implementa invalidación de caché y difusión de eventos WebSocket vía Redis Pub/Sub, lo que sienta bases de escalabilidad horizontal. Persisten cuellos de botella: el cliente HTTP sincrónico del bot y el middleware de rate limiting en memoria, que no se sincroniza entre múltiples workers. No se dispone de métricas operativas en producción; por ello, se recomienda ejecutar benchmarks y pruebas de carga con enfoque en p95/p99.[^1]

Tabla 16. Patrones de escalado y riesgos

| Componente             | Recurso/Patrón        | Límite actual                           | Riesgo                                | Optimización propuesta                         |
|------------------------|-----------------------|------------------------------------------|---------------------------------------|------------------------------------------------|
| WebSockets             | Redis Pub/Sub         | Fallback TLS; cross-worker broadcast     | Degradación si Redis falla            | Health checks; circuit breakers; métricas      |
| Caché Redis            | CacheService          | TTL configurable; prefijos               | Invalidación amplia (thundering herd) | TTL por clave; refresco escalonado             |
| Bot API cliente        | requests sincrónico   | Bloqueo por I/O                          | Throughput limitado                   | Cliente asíncrono con timeouts y reintentos    |
| Rate limiting          | In-memory             | No compartido entre workers              | Bypass de límites                     | Redis-backed rate limiting                     |
| Geolocalización        | PostGIS geography     | SRID 4326; orden por proximidad          | Degradación sin índices adecuados     | Verificación de índices; tuning de consultas   |

Tabla 17. Plan de pruebas de carga (propuesto)

| Endpoint/Componente    | Métrica objetivo            | Escenario                       | Herramienta | Umbral de aceptación         |
|------------------------|-----------------------------|---------------------------------|-------------|------------------------------|
| /tasks/emergency       | p95/p99 latencia            | Pico de emergencias             | HTTP load   | p95 < 500ms; p99 < 1000ms    |
| /ws/connect            | Conexiones concurrentes     | 1k–10k conexiones               | WS load     | <1% fallos handshake         |
| /geo/map/view          | p95 latencia                | Mapa con radio amplio           | HTTP load   | p95 < 700ms                  |
| /cache/*               | Hit rate / invalidación     | Operaciones masivas             | Redis tools | Hit rate > 85%; invalidación <200ms |
| /metrics               | scrape time                 | Alta frecuencia de scrape       | Prometheus  | Scrape < 200ms               |

Estos umbrales son propuestos y deben adaptarse según SLAs gubernamentales acordados y capacidades reales de infraestructura.[^1]

## Recomendaciones específicas para operaciones de campo

- Asignación de operativos: incorporar un módulo de gestión de horarios/turnos con validaciones de solapamiento y reglas de descanso; disparar asignación por proximidad PostGIS con tie-breaks por disponibilidad y carga de trabajo.[^1]
- Recordatorios T-40 minutos: implementar un programador (cron) que consulte ventanas de inicio de operativo y envíe notificaciones por WebSocket, complementadas por mensajería en el canal del bot; registrar confirmación de recepción con persistencia.[^1]
- Integración Telegram Bot: migrar el ApiService a un cliente HTTP asíncrono, persistir el estado del wizard en Redis con TTL y namespace, y reforzar la autorización/ trazabilidad para operaciones sensibles.[^1]
- Seguridad y compliance: activar cifrado en reposo en BD y backups; centralizar gestión de secretos (Vault/Secrets Manager) con rotación documentada; instrumentar audit logging integral; migrar rate limiting a Redis y añadir métricas por usuario/IP.[^1][^2]

Tabla 18. Plan de acción por fases

| Fase | Acción                                                                                  | Riesgo mitigado                               | Esfuerzo | Impacto                      |
|------|------------------------------------------------------------------------------------------|-----------------------------------------------|----------|------------------------------|
| 1    | Migrar ApiService a cliente asíncrono                                                    | Bloqueos de I/O; timeouts                     | Medio    | Alto                         |
| 1    | Persistir wizard en Redis (TTL, namespace, limpieza)                                     | Pérdida de estado; resiliencia                | Medio    | Alto                         |
| 1    | Implementar audit logging integral                                                       | Trazabilidad insuficiente                     | Medio    | Alto                         |
| 1    | Activar/verificar cifrado en reposo (BD/backups)                                         | Exposición de datos                           | Medio    | Alto                         |
| 2    | Redis-backed rate limiting con métricas                                                  | Bypass en multi-worker                        | Medio    | Alto                         |
| 2    | Gestión centralizada de secretos (Vault/Secrets Manager), rotación documentada           | Compromiso de credenciales                    | Medio    | Alto                         |
| 2    | Instrumentación Prometheus/Grafana específica para bot y endpoints críticos              | Falta de visibilidad operativa                | Bajo     | Medio                        |
| 3    | Módulo de horarios/turnos integrado con asignación por proximidad                        | Cobertura operativa insuficiente              | Medio    | Alto                         |
| 3    | Recordatorios T-40 con confirmación de recepción persistente                             | Brecha de notificaciones                      | Medio    | Alto                         |
| 3    | Unificar contratos de API (retirar api_legacy), documentar endpoints                     | Inconsistencias/deuda técnica                 | Bajo     | Medio                        |
| 3    | Endurecer TLS y verificar certificados (Redis/API)                                       | Riesgos de tránsito                           | Bajo     | Medio                        |

## Brechas de información

Persisten vacíos relevantes que impactan la evaluación final y el go-live:

- No se identificaron endpoints explícitos de recordatorios automáticos a T-40 minutos; el sistema solo muestra notificaciones en tiempo real por WebSocket y Telegram.[^1]
- Falta evidencia de persistencia de estado del wizard en Redis; el bot mantiene el estado en memoria (context.user_data).[^1]
- No se dispone de métricas operativas en producción (p95/p99, throughput); el endpoint /metrics existe, pero no hay datos en vivo presentados.[^1]
- No se identificó un esquema formal de autorización por operativo (rol/permiso) para endpoints de creación/asignación; se asume autenticación general.[^1]
- No se verificó el cifrado en reposo de la base de datos ni de backups.[^1]
- No hay evidencia de endpoints de geocercas operativas más allá de filtros por radio aproximado.[^1]
- No se evidenció rate limiting basado en Redis para multi-worker; el middleware actual es in-memory.[^1]
- No se identificó un endpoint de liberación automática de efectivos post-finalización.[^1]
- No se dispone de documentación operativa de SLAs de performance y alertas en tiempo real.[^1]

El plan de remediación propuesto integra cierre de estas brechas en fases, con foco en seguridad, persistencia y trazabilidad.

## Anexos técnicos

Tabla 19. Endpoints consolidados

| Método | Ruta                                | Respuesta/Evento                             | Auth         | Notas operativas                                   |
|--------|-------------------------------------|-----------------------------------------------|--------------|----------------------------------------------------|
| GET    | /tasks/                             | Lista de tareas                               | JWT          | Paginación                                         |
| POST   | /tasks/                             | Tarea creada                                  | JWT          | Invalida patrones de caché                         |
| GET    | /tasks/{task_id}                    | Tarea                                         | JWT          | 404 si no existe                                   |
| PUT    | /tasks/{task_id}                    | Tarea actualizada                             | JWT          | Invalida cache por task_id                         |
| DELETE | /tasks/{task_id}                    | Tarea eliminada                               | JWT          | Invalida cache por task_id                         |
| POST   | /tasks/emergency                    | assigned_efectivo_id, distance_m, status     | JWT          | PostGIS; auditoría; manejo 404/503/500             |
| GET    | /geo/map/view                       | {usuarios: [], tareas: [...]}                 | JWT          | Haversine; radio                                   |
| GET    | /geo/efectivos/mock                 | {usuarios: [...], metadata: {...}}            | JWT          | Mock de estados y ubicaciones                      |
| WS     | /ws/connect                         | Conexión, mensajes, suscripciones             | Token (opt/dev)| JWT obligatorio en producción                      |
| GET    | /ws/stats                           | Estadísticas WS                               | —            | Métricas en tiempo real                            |
| POST   | /ws/_test/broadcast                 | Broadcast de prueba                           | Restringida  | No-prod                                            |
| GET    | /metrics/prometheus                 | Métricas Prometheus                           | —            | Scrape cada 10s (config)                           |
| GET    | /health                             | {status: ok}                                  | —            | Compatibilidad LB                                  |
| GET    | /health/detailed                    | Checks DB, circuit breaker, response_time     | —            | 503 si DB error                                    |
| GET    | /health/ready                       | {status: ready/not_ready}                     | —            | Readiness                                          |
| GET    | /health/live                        | {status: alive}                               | —            | Liveness                                           |
| GET    | /health/performance                 | Métricas de performance                       | —            | Slow queries; endpoints más lentos                 |
| GET    | /health/government                  | Estado compuesto                              | —            | 503 si unhealthy                                   |
| GET    | /cache/stats                        | Estadísticas Redis                            | —            | Hit/miss; evictions                                |
| POST   | /cache/invalidate/{key}             | Confirmación de eliminación                   | —            | Precaución                                         |
| POST   | /cache/invalidate-pattern/{pattern} | Conteo de eliminados                          | —            | Patrones “stats:user:*”, “tasks:list:*”            |
| POST   | /cache/clear                        | Confirmación de limpieza                      | —            | Irreversible                                       |
| POST   | /auth/login                         | Token (cookie HttpOnly)                       | —            | Logs de autenticación                              |
| POST   | /auth/logout                        | {status: logged_out}                          | —            | Elimina cookie                                     |
| POST   | /telegram/tasks/create              | task_id, codigo, created_at                   | —            | Alerta WS si urgente                               |
| POST   | /telegram/tasks/finalize            | success, finalized_at                         | —            | Notificación WS                                    |
| GET    | /telegram/tasks/user/{telegram_id}  | estadísticas y resúmenes                      | —            | Usuario debe existir                               |
| GET    | /telegram/tasks/code/{codigo}       | detalle de tarea                              | —            | 404 si no existe                                   |

Tabla 20. Reglas de alertas (resumen cualitativo)

| Categoría                 | Umbral (cualitativo)             | Canal de notificación     | Impacto ciudadano               |
|---------------------------|----------------------------------|---------------------------|---------------------------------|
| Disponibilidad            | Caída de servicio/health 503     | Alertmanager/Grafana      | Alto                            |
| Latencia endpoints        | p95 fuera de SLA                 | Alertmanager/Grafana      | Medio/Alto según endpoint       |
| DB (conexiones/lentitud)  | Conexiones altas/consultas lentas| Alertmanager/Grafana      | Alto                            |
| Redis                     | Fallas de conexión/memoria       | Alertmanager/Grafana      | Medio                           |
| WebSockets                | Fallos de envío/conexiones       | Alertmanager/Grafana      | Medio                           |
| Seguridad                 | Intentos no autorizados          | Alertmanager/Grafana      | Alto                            |

La correspondencia exacta de las 23 reglas requiere revisión detallada del archivo de configuración de alertas.[^1]

## Referencias

[^1]: GRUPO_GAD - Repositorio (GitHub). URL: https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD - Aplicación en Producción (Fly.io). URL: https://grupo-gad.fly.dev

---

Este informe consolida una revisión exhaustiva y accionable de la superficie de endpoints críticos de GRUPO_GAD, con foco en operaciones de campo, seguridad y cumplimiento gubernamental. Las recomendaciones propuestas abordan los vacíos identificados y refuerzan la resiliencia y trazabilidad necesarias para entornos de misión crítica.[^1][^2]