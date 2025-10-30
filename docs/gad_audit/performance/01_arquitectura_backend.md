# Auditoría Técnica de la Arquitectura Backend de GRUPO_GAD (FastAPI + PostGIS)

## Resumen ejecutivo

Esta auditoría examina la arquitectura backend del sistema GRUPO_GAD —una plataforma gubernamental de gestión administrativa— construida sobre FastAPI, SQLAlchemy (AsyncSession), PostgreSQL con PostGIS y Redis. El alcance incluye el ciclo de vida de arranque y apagado (lifespan), routers y middlewares, dependencias y seguridad, patrones asíncronos, diseño y operación de WebSockets, uso de Redis para cache y Pub/Sub, configuración de base de datos y migraciones, así como observabilidad mediante métricas Prometheus y endpoints de salud.

La fotografía actual refleja un sistema production-ready con capacidades críticas para operación 24/7: despliegue en Fly.io con estrategia rolling y health checks, proxy reverso con HTTPS automático, pipeline de CI/CD con análisis de seguridad, y un stack de monitoreo con Prometheus, Alertmanager y Grafana. En el plano arquitectónico, destacan la modularidad del código (routers, core y servicios geoespaciales), la separación entre API, bot y dashboard, y la incorporación de mecanismos de resiliencia (retry y circuit breaker en acceso a base de datos, fallback de TLS en Redis, degradación controlada ante ausencia de servicios opcionales). Todo ello está documentado y observado en producción, con una URL pública activa y trazable[^1][^2].

Fortalezas observadas:
- Diseño modular y separación de responsabilidades (API FastAPI, bot de Telegram, core de cache/websockets, observabilidad).
- Seguridad por defecto: headers de seguridad, CORS configurable, rate limiting, y manejo centralizado de secretos.
- Resiliencia operacional: retry con Tenacity, circuit breaker de base de datos, degradación controlada de cache/Redis/WS en caso de indisponibilidad.
- Observabilidad y operación: health checks, endpoint /metrics, Prometheus con reglas de alertas y dashboards Grafana.
- Diseño asíncrono end-to-end: AsyncSession, asyncpg, WebSockets, Redis asíncrono y métricas instrumentadas.

Debilidades y riesgos:
- Variabilidad de configuración cross-entorno (CORS, ALLOWED_HOSTS, TLS/SSL en Redis) con riesgo de exposición accidental si no se estandariza.
- Inicialización de recursos globales en lifespan con dependencia implícita de orden (por ejemplo, cache y pubsub), sensible a errores de entorno.
- Dependencia de migraciones manuales para habilitar PostGIS (CREATE EXTENSION postgis; y DDL de índices), lo que introduce riesgo de inconsistencia en despliegues.
- Casos de fallback TLS en Redis con ssl_cert_reqs=None que deben limitarse a entornos controlados y con expiración de uso.

Impacto: Con las mitigaciones propuestas —matriz de configuración por entorno, endurecimiento CORS, validación operativa de PostGIS, endurecimiento TLS de Redis, consolidación del startup y health checks por dependencias— el sistema alcanzará un perfil de cumplimiento y operación de alta disponibilidad más homogéneo, con menor superficie de riesgo y mejores garantías de continuidad de servicio.

## Metodología y fuentes

La metodología combinó revisión estática del código y configuración, análisis funcional de flujos (API, WebSockets y Bot), y verificación de capacidades operativas (lifespan, health checks, métricas y alertas). Se priorizaron componentes que influyen en seguridad, disponibilidad y correctness geoespacial.

Fuentes principales:
- Código fuente del backend: routers, middlewares, servicios de base de datos, cache, WebSockets y geoespacial, observabilidad.
- Configuraciones de despliegue y operación: Fly.io, Docker Compose, Alembic, Prometheus.
- Pruebas unitarias, de integración y End-to-End para validar flujos críticos (por ejemplo, WebSockets).

Inventario de integraciones gubernamentales:
- Bot de Telegram: interfaz ciudadana y flujos conversacionales.
- PostGIS: servicio geoespacial con SRID 4326 y consultas geography.
- Redis: cache y Pub/Sub para broadcast cross-worker de WebSockets.
- Prometheus/Grafana: métricas, alertas y dashboards.

## Arquitectura lógica de alto nivel

La arquitectura se organiza en cuatro dominios funcionales y un plano transversal de observabilidad:

- API FastAPI: expone endpoints REST y WebSocket, aplica middlewares (CORS, seguridad, rate limiting, logging, límites de tamaño), registra métricas y ofrece health checks. Conecta con PostgreSQL mediante AsyncSession y con Redis para cache y pubsub.
- Bot de Telegram: integra autenticación y operaciones relacionadas con tareas a través de routers dedicados. Opera asíncronamente, independiente de la API, consumiendo servicios backend cuando corresponde.
- Core de servicios compartidos: define el acceso a base de datos (engine, sessionmaker, retry y circuit breaker), el servicio de cache (TTL, serialización, estadísticas) y la lógica de WebSockets (manager, heartbeat, broadcast por usuario/rol/tópico, puente Redis Pub/Sub).
- Geoespacial (PostGIS): servicio dedicado que valida el dialecto PostgreSQL y ejecuta consultas geography para proximidad con ST_Distance y ordenación por operador <->.
- Observabilidad: métricas Prometheus instrumentadas para WebSockets y operación, endpoint /metrics y reglas de alertas; integración con health checks.

Para visualizar la separación de concerns y flujos, el siguiente mapa sintetiza responsabilidades y puntos de integración.

Tabla 1. Mapa de componentes y responsabilidades

| Componente                    | Responsabilidades principales                                                                                 | Integraciones clave                                   |
|------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| API FastAPI                  | Routers REST y WebSocket; middlewares; lifespan; seguridad; health; métricas                                   | PostgreSQL (asyncpg), Redis (cache y Pub/Sub)         |
| Bot de Telegram              | Comandos y handlers; autenticación; operaciones citizens/tareas                                                | API REST para usuarios/tareas; configuración central  |
| Core DB                      | Engine y AsyncSessionFactory; retry; circuit breaker; pool; SSL                                                | PostgreSQL (via SQLAlchemy async)                     |
| Core Cache                   | Servicio Redis (conexión, TTL, prefijos, stats); DI global                                                     | Redis asíncrono; métricas internas                    |
| WebSocket Manager            | Conexiones activas; routing por usuario/rol; heartbeat; broadcast local; integración con Pub/Sub              | Redis Pub/Sub; métricas Prometheus                    |
| Geoespacial (PostGIS)        | Validación de dialecto; consultas geography (SRID 4326); nearest neighbor                                      | PostgreSQL/PostGIS; SQLAlchemy async                  |
| Observabilidad (Prometheus)  | Métricas WS; endpoint /metrics; actualización de stats; etiquetas por entorno                                  | FastAPI; WS manager; Prometheus scrape                |
| Alembic (migraciones)        | Versionado de esquema; support async/sync; SSL configurable                                                    | PostgreSQL/PostGIS                                    |
| Monitoreo (Prom/Grafana)     | Scraping; alertas; dashboards                                                                                  | API y servicios; exporters                            |

Subsecciones:

### Componentes y responsabilidades

El punto de entrada de la API configura el lifespan de la aplicación, donde se inicializa el motor de base de datos, se arman los middlewares de seguridad y CORS, se activa el sistema de WebSockets (incluido Pub/Sub y CacheService si están disponibles), y se inicializa la instrumentación de métricas. El sistema expone health checks de readiness que validan base de datos, Redis, WebSocket Manager y Pub/Sub, devolviendo 200 si todo está “ok” o “not_configured”, y 503 en caso de fallos.

Los routers cubren dominios como geolocalización (geo), autenticación por Telegram, usuarios y tareas, estadísticas, métricas y un router de WebSockets que gestiona handshake, autenticación y loop de mensajes. El router de geoespacial provee una vista de mapa que, por ahora, utiliza distancias aproximadas (Haversine) cuando las entidades de tareas cuentan con latitud/longitud; el servicio PostGIS, en paralelo, habilita búsquedas precisas de “nearest efectivo” cuando el motor y la extensión están disponibles.

El servicio de WebSockets mantiene las conexiones por usuario/rol, aplica heartbeat, realiza broadcasts por tópicos, y se integra con Redis Pub/Sub para broadcast cross-worker, permitiendo escalar horizontalmente manteniendo coherencia de eventos en múltiples instancias.

### Flujos de datos y eventos

El flujo típico de una petición REST comienza con middlewares (CORS, seguridad, rate limiting, logging, límites de cuerpo) y se apoya en dependencias (por ejemplo, usuario actual, sesión de base de datos y, cuando aplica, servicio de cache). Los endpoints que interactúan con datos geoespaciales invocan el servicio PostGIS con AsyncSession y una consulta text() que utiliza geography y operadores espaciales para calcular distancias y ordenar resultados.

El flujo de WebSocket —handshake, autenticación opcional en producción, suscripciones por evento— converge en el manager, que mantiene las conexiones, ejecuta heartbeats y distribuye mensajes por usuario, rol o tópico. Cuando el Pub/Sub de Redis está activo, el broadcast se publica en un canal y se redistribuye a los workers suscritos, habilitando escalabilidad horizontal. Si Redis no está disponible, el sistema continúa operando con broadcast local, degradando capacidades de coordinación cross-worker sin comprometer la funcionalidad básica del endpoint de salud.

## Estructura arquitectónica de módulos (src/, app/, routers, middleware, core)

La jerarquía de módulos evidencia un diseño claro:
- src/api: routers (auth, geo, telegram_auth, telegram_tasks, usuarios, websockets, health, metrics), dependencies, middleware personalizado (rate limiting y emisor de eventos WS), servicios y modelos.
- src/core: database (engine, AsyncSessionFactory, retry, circuit breaker), cache (CacheService con Redis asíncrono, TTL, prefijos y estadísticas), websockets (manager, eventos, heartbeat, métricas), ws_pubsub (puente Redis), logging y performance.
- src/observability: métricas Prometheus instrumentadas para conexiones y mensajes WS.
- alembic: migraciones (async/sync), configuración del entorno (validación de URLs, SSL, pool) y scripts de versión.

Tabla 2. Inventario de routers y responsabilidades

| Router                 | Propósito                                  | Dependencias relevantes                     |
|------------------------|---------------------------------------------|---------------------------------------------|
| auth                   | Autenticación y emisión de JWT              | settings, security, usuarios                |
| geo                    | Vista de mapa y datos espaciales            | DB async, servicio PostGIS                  |
| telegram_auth          | Autenticación de usuarios vía Telegram      | DB async, JWT                               |
| telegram_tasks         | Operaciones de tareas desde el bot          | DB async                                    |
| usuarios               | Gestión de usuarios                         | DB async                                    |
| websockets             | Endpoint WS, stats y pruebas de broadcast   | WS manager, JWT                             |
| health                 | Health checks simples                       | DB, Redis, WS Manager, Pub/Sub              |
| metrics                | Exposición de métricas Prometheus           | Métricas instrumentadas                     |
| statistics             | Estadísticas operativas                     | DB async                                    |
| cache                  | Operaciones de cache (opcional)             | CacheService                                |

Tabla 3. Middlewares aplicados

| Middleware                                 | Propósito                                          | Orden lógico          |
|--------------------------------------------|----------------------------------------------------|-----------------------|
| ProxyHeadersMiddleware                      | Reconocer X-Forwarded-* detrás de proxy            | Antes de seguridad    |
| Security headers                           | X-Frame-Options, CSP, Referrer-Policy, etc.        | Post-CORS             |
| Max body size                              | Mitigar DoS multipart (10 MiB)                     | Post-security headers |
| CORS                                       | Control de orígenes permitidos                     | Post-security headers |
| Rate limiting gubernamental                | Protección DoS para servicios ciudadanos           | Post-CORS             |
| Logging                                    | Registro estructurado de requests/responses        | Último en cadena      |

### Routers y servicios

La composición de routers abarca dominios funcionales críticos para la operación gubernamental:
- Autenticación y autorización (auth) habilitando issuance de tokens JWT y controles de acceso.
- Gestión de usuarios y tareas, incluyendo endpoints expuestos para consumo del bot y del dashboard.
- Geoespacial con dos vías: vista de mapa basada en distancias aproximadas y el servicio PostGIS para nearest neighbor con precisión de geography.
- WebSockets con endpoint de conexión, manejo de autenticación, suscripciones, heartbeat y stats.

El router de geoespacial demuestra una integración mixta: mientras el servicio PostGIS ofrece exactitud geodesica, la vista de mapa de dashboard recurre a una aproximación de Haversine cuando no se dispone de geometrías en efectivos o cuando se prioriza la rapidez para filtros por radio. Esta estrategia híbrida es pragmática y funcionalmente consistente con el estado de modelado actual.

### Middleware y seguridad

Los middlewares de seguridad agregan headers robustos (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy), con una política de Content Security Policy mínima para rutas bajo /api/. Se añade un límite de tamaño de cuerpo para mitigar vectores de DoS por cargas voluminosas. El middleware CORS es configurable por entorno, con endurecimiento en producción mediante orígenes explícitos. Se incorpora rate limiting “gubernamental” para protección de servicios ciudadanos, con capacidad de habilitación/deshabilitación por configuración.

## Dependency Injection y configuración (FastAPI, DB, Cache, Settings, Seguridad)

La aplicación define dependencias HTTP claras:
- Usuario actual (autenticado y activo).
- Superusuario para endpoints administrativos.
- Sesión de base de datos (AsyncSession) con reintentos y circuito de protección.

La gestión de recursos compartidos se realiza mediante objetos en el estado de la aplicación (por ejemplo, cache_service y ws_pubsub), inicializados durante el lifespan y expuestos para health checks.

Tabla 4. Mapa de dependencias FastAPI

| Dependencia             | Scopo            | Tipo (sync/async) | Recurso asociado         | Error handling                           |
|-------------------------|------------------|-------------------|--------------------------|------------------------------------------|
| get_current_user        | por request      | async             | Token JWT, DB            | 403 si credenciales inválidas            |
| get_current_active_user | por request      | async             | Usuario en BD            | 400 si usuario inactivo                  |
| get_current_active_superuser | por request | async             | Usuario en BD            | 400 si no tiene privilegios              |
| get_db_session          | por request      | async             | AsyncSession             | retry + circuit breaker (runtime)        |
| get_cache_service       | por request      | async             | CacheService (Redis)     | RuntimeError si no inicializado          |

Tabla 5. Parámetros clave de DB y efecto

| Parámetro         | Valor (por defecto/observado) | Efecto operacional                                                             |
|-------------------|-------------------------------|---------------------------------------------------------------------------------|
| pool_size         | 10                            | Concurrencia base de conexiones en pool                                         |
| max_overflow      | 20                            | Capacidad adicional en picos                                                    |
| pool_timeout      | 30                            | Tiempo máximo para obtener conexión del pool                                    |
| pool_recycle      | 3600                          | Reciclaje de conexiones para evitarstaleness                                    |
| pool_pre_ping     | True                          | Verificación de salud de conexiones antes de usarlas                            |
| isolation_level   | READ_COMMITTED                | Balance entre consistencia y concurrencia                                       |
| query_cache_size  | 1200                          | Cache de queries compiladas                                                     |
| SSL (asyncpg)     | configurable (deshabilitable) | Control de TLS por entorno (redes privadas vs públicas)                         |

### Dependencias HTTP y DB

Las dependencias HTTP recuperan y validan tokens JWT, resuelven el usuario desde base de datos y aplican políticas de acceso (activo y superusuario). La dependencia de base de datos utiliza una AsyncSessionFactory con retry (exponencial, hasta 3 intentos) y circuit breaker que se abre tras cinco fallos, con ventana de reset configurable. La sesión se cierra en finally, asegurando liberación de recursos incluso bajo error. Este patrón es adecuado para resiliencia operativa ante intermitencias de red o picos de latencia.

### Recursos compartidos y ciclo de vida

El lifespan orquesta:
- Inicialización de DB (con normalización a asyncpg).
- Startup del sistema de WebSockets y del integrador de eventos.
- Inicialización opcional de Redis (cache y Pub/Sub) con lógica de fallback TLS para ciertos proveedores, y sanitización de URL para evitar exposición de credenciales en logs.
- Inicialización de métricas Prometheus (si están disponibles).

El shutdown realiza la secuencia inversa: detiene la integración WS, cierra CacheService y Pub/Sub, y dispone del motor async de base de datos. Si Redis no está configurado, el sistema lo refleja en health checks y logs, degradando capacidades de cache y broadcast cross-worker sin bloquear la API.

## Patrones Async/Await y concurrencia

La arquitectura adopta async/await de forma consistente:
- Endpoints y servicios de negocio utilizan AsyncSession y consultas con await.
- El servicio PostGIS ejecuta queries text() con parámetros y devuelve resultados transformados a tipos Python, validando el dialecto postgresql antes de operar.
- El bot de Telegram opera asíncronamente con el framework de python-telegram-bot y servicios REST del backend.
- WebSockets emplean asyncio para manejo de conexiones, heartbeats, broadcasting y loop de suscripción Redis.

Tabla 6. Puntos de concurrencia y resiliencia

| Componente               | Tipo de concurrencia        | Riesgo principal                      | Patrón de mitigación                                      |
|-------------------------|-----------------------------|--------------------------------------|-----------------------------------------------------------|
| API/DB (asyncpg)        | I/O bound                   | Latencia transitoria, pool exhaustion| Retry exponencial + circuit breaker + pool tuning         |
| PostGIS                 | I/O bound espacial          | Extensión no habilitada              | Validación de dialecto + 503 controlado                   |
| WS Manager              | Conexiones persistentes     | Heartbeat y timeouts                 | Heartbeat loop; cancelación limpia; metrics               |
| Redis Cache/PubSub      | I/O asíncrono               | TLS/handshake, fallas de red         | Fallback TLS, reconexión, degrade local, logs estructurados|
| Métricas Prometheus     | Instrumentación en proceso  | Sobrecarga mínima                    | Histogramas y contadores de bajo costo                    |

### DB y PostGIS asíncrono

El acceso a base de datos configura pool_pre_ping, aislamiento READ_COMMITTED y recycle horario para minimizar problemas de staleness. El servicio geoespacial valida que el dialecto sea PostgreSQL; de lo contrario, devuelve un error 503 con detalle explicativo. Las consultas utilizan geography con SRID 4326 y se apoyan en ST_SetSRID, ST_MakePoint, ST_Distance y el operador <-> para nearest neighbor. Este diseño está alineado con las mejores prácticas de cálculos de distancia y ordenamiento espacial eficiente.

### WebSockets y Pub/Sub

El WebSocketManager mantiene conexiones activas, métricas de mensajes y errores, y un loop de heartbeat que envía pings a intervalos regulares. Se integra con Redis Pub/Sub para broadcast cross-worker, y suelta eventos (evita republique de mensajes de control) en la ruta local. En entornos con proveedores Redis que fuerzan TLS, existe mitigación temporal con ssl_cert_reqs=None, que debe ser cuidadosamente controlada. El sistema se adapta a la ausencia de Redis con degrade local sin pérdida de servicio de la API.

## Base de datos y geoespacial (PostgreSQL + PostGIS)

El modelo relacional define un esquema gubernamental con entidades clave:
- Usuario: identifica ciudadanos/efectivos con telegram_id único y nivel de autenticación.
- Efectivo: extensión operativa de usuario con estado de disponibilidad y relaciones a tareas.
- Tarea: entidad central con código único, tipo, estados, tiempos programados y reales, delegado y asignados (vínculo many-to-many con efectivos).

Tabla 7. Resumen de entidades y relaciones

| Entidad  | Claves principales                      | Relaciones                                           |
|----------|------------------------------------------|------------------------------------------------------|
| Usuario  | id (PK), telegram_id (único), nivel      | 1:1 con Efectivo; 1:N con Tarea (delegado)           |
| Efectivo | id (PK), dni (único), estado_disponibilidad | N:M con Tarea (vía tabla de asignaciones)        |
| Tarea    | id (PK), código (único), estado          | N:M con Efectivo; N:1 con Usuario (delegado)         |

La migración de geoespacial añade una columna geom a la tabla de efectivos, aunque el script actual está marcado como “skipped” y requiere ejecución manual de CREATE EXTENSION postgis; ALTER TABLE … ADD COLUMN geom geography(POINT,4326); y CREATE INDEX ix_efectivos_geom_gist USING GIST (geom). Esta dependencia manual introduce un riesgo operativo en despliegue; se recomienda automatizar con un migration step verificado y gated.

Tabla 8. Consultas PostGIS utilizadas

| Función/Operador         | Propósito                              | Resultado esperado                   |
|--------------------------|----------------------------------------|--------------------------------------|
| ST_SetSRID(.., 4326)     | Fijar sistema de coordenadas           | Punto con SRID 4326                  |
| ST_MakePoint(lng, lat)   | Crear punto geográfico                 | Geometría_POINT                      |
| ::geography              | Casting a geography                    | Cálculo preciso de distancia (metros)|
| ST_Distance(..)          | Distancia entre geometrías             | Distancia en metros                  |
| geom <-> point::geography| Ordenación por nearest neighbor        | Orden eficiente para LIMIT           |

### Modelo de datos y migraciones

Las migraciones con Alembic están bien configuradas para entornos async/sync, con selección de URL desde múltiples fuentes y control de SSL. El circuito de upgrades/downgrades es claro, pero la habilitación de PostGIS depende de ejecución manual. Se sugiere incorporar una migración que verifique la presencia de la extensión y, en caso de ausencia, falle de forma controlada o realice la creación con privilegios adecuados, dejando atrás laskipped y añadiendo un índice espacial.

### Servicio geoespacial

El servicio find_nearest_efectivo valida coordenadas y dialecto, luego ejecuta una consulta con parámetros y devuelve una lista de diccionarios con identificador de efectivo y distancia en metros. Los errores de consulta se traducen en respuestas 503 con detalle contextualizado. En endpoints de dashboard que aún no modelan geometrías para usuarios/efectivos, se recurre a distancias aproximadas por Haversine para filtrar tareas dentro de un radio, con un mapeo explícito de prioridad a etiquetas esperadas por el frontend.

## Seguridad, compliance y auditoría

El backend añade headers de seguridad a todas las respuestas, controla CORS por entorno y limita el tamaño de cuerpo de peticiones. Se incorpora rate limiting con capacidad de apagado en desarrollo. La autenticación se realiza mediante JWT; los tokens pueden emitirse para usuarios autenticados vía Telegram y se verifican en endpoints dedicados. El manejo de secretos se apoya en variables de entorno y configuración centralizada, con prácticas alineadas a despliegue gubernamental.

Tabla 9. Matriz de controles de seguridad

| Control                         | Ubicación/Componente          | Estado (producción)      | Recomendación de endurecimiento          |
|--------------------------------|-------------------------------|--------------------------|------------------------------------------|
| Security headers               | Middleware HTTP               | Activo                   | Mantener CSP mínima; revisar por rutas   |
| CORS                           | CORSMiddleware                | Configurable por entorno | Orígenes explícitos; evitar “*”          |
| Rate limiting                  | Middleware gubernamental      | Activo                   | Afinar límites por endpoint              |
| JWT auth                       | Dependencies y routers        | Activo                   | Rotación de secretos; tiempos de expiración|
| Health/ready                   | Endpoints dedicados           | Activo                   | Incluir checks de dependencias opcionales|
| Métricas /metrics              | Endpoint dedicado             | Activo                   | Asegurar que no exponga datos sensibles  |

### Gestión de secretos y CORS

La configuración centralizada admite orígenes permitidos y hosts confiables; en producción, se exige una política explícita sin comodines. Se recomienda una matriz de configuración por entorno que incluya dominios, proxies confiables, y políticas CORS específicas por router o dominio.

### Auditoría y trazabilidad

El logging estructurado por request incluye metadatos clave (método, path, cliente, user-agent), y errores registran duración y contexto. Los health checks ofrecen una vista operativa de dependencias, y el endpoint /metrics expone texto plano compatible con Prometheus. Para consolidar compliance, conviene definir una política de auditoría que incluya correlación de IDs, retención de logs por ventanas definidas, y cobertura de auditoría de acceso a datos sensibles.

## Observabilidad y monitoreo

La observabilidad se apoya en un conjunto de métricas instrumentadas para WebSockets (conexiones activas, totales, mensajes, broadcasts, errores), endpoint /metrics, health checks (/health, /health/ready), y una configuración de scraping y alertas en Prometheus.

Tabla 10. Catálogo de métricas

| Métrica (tipo)                    | Descripción                                         | Etiquetas            | Fuente de actualización               |
|----------------------------------|-----------------------------------------------------|----------------------|---------------------------------------|
| active_connections (Gauge)       | Conexiones WS activas                                | entorno              | Al conectar/desconectar               |
| connections_total (Counter)      | Total histórico de conexiones                        | entorno              | connection_established                 |
| messages_sent_total (Counter)    | Mensajes enviados                                    | entorno              | message_sent                           |
| broadcasts_total (Counter)       | Broadcasts realizados                                | entorno              | message_sent (is_broadcast=True)       |
| send_errors_total (Counter)      | Errores de envío                                     | entorno              | send_error                             |
| heartbeat_last_timestamp (Gauge) | Último heartbeat                                     | entorno              | heartbeat_completed                    |
| message_latency_seconds (Histogram)| Latencia de mensajes                                | entorno              | Observación en envío                   |

La configuración de scraping abarca la aplicación, base de datos (postgres-exporter), Redis (redis-exporter), Node Exporter y Alertmanager. Las reglas de alertas cubren disponibilidad, latencia y recursos, entre otros.

### Alertas y dashboards

Las alertas operativas priorizan:
- Uptime de servicios y latencia de endpoints críticos.
- Recursos de infraestructura (CPU, memoria, disco).
- Condiciones de base de datos (conexiones, slow queries) y Redis (conexión y memoria).

Los dashboards en Grafana visualizan performance de API, métricas de WebSockets y performance de base de datos, facilitando diagnóstico proactivo.

## Despliegue y operación

El despliegue en Fly.io adopta estrategia rolling, health checks regulares y límites de recursos, con métricas expuestas en un puerto dedicado. Docker Compose orquesta servicios en desarrollo: PostgreSQL/PostGIS, Redis, API, bot y proxy Caddy con HTTPS automático. Alembic gestiona migraciones, con soporte de URLs y SSL; scripts de operación abarcan despliegues, health checks, monitoreo y rollback.

Tabla 11. Resumen de configuración Fly.io

| Parámetro                 | Valor                       | Implicación operacional                               |
|--------------------------|-----------------------------|--------------------------------------------------------|
| primary_region           | dfw                         | Proximidad a Latinoamérica                             |
| strategy                 | rolling                     | Zero-downtime                                          |
| auto_rollback            | true                        | Reversión ante fallos de health check                  |
| kill_signal/timeout      | SIGINT / 30s                | Terminación graceful                                   |
| concurrency              | 800 soft / 1000 hard        | Capacidad de manejo de requests                        |
| health checks            | HTTP /health cada 15s       | Disponibilidad y readiness                             |
| metrics                  | port 9091, /metrics         | Scraping Prometheus                                    |
| WS_HEARTBEAT_INTERVAL    | 30                          | Keepalive en WS                                        |
| WS_MAX_CONNECTIONS       | 10000                       | Capacidad WS por instancia                             |

Tabla 12. Servicios Docker Compose y puertos

| Servicio | Imagen/Versión              | Puerto | Healthcheck           | Dependencias             |
|----------|-----------------------------|--------|-----------------------|--------------------------|
| db       | PostgreSQL + PostGIS        | 5434   | Integrado (compose)   | —                        |
| redis    | Redis                       | 6381   | —                     | —                        |
| api      | Build Dockerfile.api        | 8000   | /health → /metrics    | db, redis                |
| bot      | Build Dockerfile.bot        | —      | —                     | api                      |
| caddy    | Caddy 2.8                   | 80/443 | —                     | api                      |

### Health checks y readiness

Los endpoints /health y /health/ready diferencian estados “ok”, “degraded” y “not_configured”. /health expone información básica de entorno y uptime, mientras /health/ready verifica conexión a base de datos (con auto-inicialización de motor si fuera necesario), estado de Redis (si está habilitado), conexiones WS y Pub/Sub. Es recomendable hacer que este readiness sea bloqueante en despliegues con dependencias obligatorias, y no bloqueante cuando se permite operación sin Redis o sin DB en entornos de prueba.

## Evaluación de fortalezas y debilidades

Fortalezas:
- Modularidad y separación clara de responsabilidades: API, bot, core, observabilidad.
- Seguridad por defecto y configuración centralizada con controles transversales (headers, CORS, rate limiting).
- Resiliencia y robustez: retry, circuit breaker, degrade controlado de cache/Pub/Sub/WS.
- Observabilidad production-ready con métricas, health checks y alertas.
- Diseño asíncrono consistente con buen soporte de concurrencia y escalabilidad.

Debilidades:
- Dependencias manuales para PostGIS (DDL/índices) que pueden generar divergencias entre entornos.
- Fallback TLS de Redis con deshabilitación de verificación de certificado, útil temporalmente pero riesgoso si persiste en producción.
- Variabilidad y potencial fragilidad de inicialización en lifespan, especialmente al combinar recursos globales (cache/pubsub) con distintos proveedores y variables de entorno.

## Recomendaciones arquitectónicas priorizadas

Quick wins (0–30 días):
- Consolidar una matriz de configuración por entorno para CORS, ALLOWED_HOSTS, TRUSTED_PROXY_HOSTS, rate limiting, y TLS/SSL. Eliminar comodines y orígenes no necesarios.
- Endurecer CORS en producción y evitar el uso de “*” salvo entornos de prueba controlados.
- Estandarizar health checks y su semántica de readiness con lista explícita de dependencias requeridas vs opcionales.

Mediano plazo (30–90 días):
- Automatizar la habilitación de PostGIS y la creación del índice espacial en migraciones, asegurando que la extensión esté presente con un plan de creación seguro y controlado.
- Refinar límites de pool por entorno y cargas esperadas, y validar impactos en rendimiento con pruebas de estrés.
- Estandarizar TLS de Redis en todos los entornos y retirar el fallback insecure; ajustar la configuración de proveedores de manera compatible.

Largo plazo (90–180 días):
- Endurecer auditoría y compliance: correlación de logs por request, retención por política, y cobertura de auditoría de acceso a datos sensibles.
- Completar cobertura de pruebas hacia el objetivo de 85% y realizar pruebas de carga sistemáticas sobre endpoints críticos (REST y WS).
- Documentar políticas de gestión de secretos y su rotación operativa en el runbook de producción.

Tabla 13. Plan de mejoras

| Acción                                                         | Prioridad | Esfuerzo | Dependencia             | Impacto en riesgo/performance                    |
|----------------------------------------------------------------|----------|----------|-------------------------|--------------------------------------------------|
| Matriz de configuración por entorno (CORS, hosts, proxies)     | Alta     | Bajo     | settings                | Reducción de exposición accidental               |
| Endurecer CORS en producción                                   | Alta     | Bajo     | middleware              | Menor superficie de ataque                       |
| Readiness con dependencias requeridas vs opcionales            | Alta     | Medio    | endpoints, lifespan     | Mejor disponibilidad y claridad operativa        |
| Automatizar CREATE EXTENSION postgis y índice espacial         | Alta     | Medio    | alembic/env.py          | Correctness geoespacial consistente              |
| Ajustar TLS de Redis y retirar ssl_cert_reqs=None              | Alta     | Medio    | core/cache, ws_pubsub   | Seguridad de transporte y cumplimiento           |
| Pool tuning por entorno                                        | Media    | Medio    | core/database           | Performance y estabilidad bajo carga            |
| Auditoría y trazabilidad mejorada                              | Media    | Medio    | observability           | Cumplimiento y respuesta a incidentes            |
| Cobertura de pruebas 85% y carga sistemática                   | Media    | Alto     | tests                   | Calidad y confianza en despliegues               |
| Documentación y rotación de secretos                           | Media    | Bajo     | operaciones             | Seguridad y gobernanza                           |

## Apéndices

### Diagrama textual de arquitectura

- API FastAPI
  - Middlewares: ProxyHeaders, Security headers, Max body size, CORS, Rate limiting, Logging.
  - Lifespan: init DB (asyncpg), init WebSockets, init Redis (Cache + Pub/Sub), init métricas Prometheus.
  - Routers: auth, geo, telegram_auth, telegram_tasks, usuarios, websockets, health, metrics, statistics.
- Bot de Telegram
  - Handlers y comandos; integración con API (usuarios/tareas).
- Core
  - database: engine, AsyncSessionFactory, retry, circuit breaker.
  - cache: CacheService (Redis), stats, TTL, prefijos.
  - websockets: manager, eventos, heartbeat, metrics bridge.
  - ws_pubsub: Redis Pub/Sub bridge (cross-worker broadcast).
- Geoespacial
  - postgis_service: validación de dialecto, consultas geography (ST_Distance, <->).
- Observabilidad
  - metrics.py: contadores y histogramas; /metrics; actualización desde manager y health endpoints.

### Ejemplo de consulta PostGIS

```sql
SELECT 
    id as efectivo_id,
    ST_Distance(
        geom, 
        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
    ) AS distance_m
FROM efectivos 
WHERE geom IS NOT NULL 
    AND deleted_at IS NULL
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
LIMIT :limit;
```

### Checklist de despliegue y pruebas

- Verificar variables de entorno críticas (DB, Redis, JWT, CORS, hosts confiables).
- Ejecutar migraciones con Alembic y validar habilitación de PostGIS y creación de índice espacial.
- Comprobar health checks (/health y /health/ready) y revisar logs de startup.
- Validar rate limiting y políticas CORS por entorno.
- Probar WebSockets (handshake, suscripciones, heartbeat) y métricas.
- Confirmar scraping de Prometheus y presencia de alertas.

### Catálogo de endpoints críticos y roles de acceso

- Autenticación y usuarios: emisión/verificación de JWT; gestión de usuarios.
- Telegram auth: autenticación de ciudadanos vía telegram_id.
- Tareas: creación, consulta y actualización; integración con bot.
- Geo: vista de mapa y nearest neighbor (PostGIS).
- WebSockets: conexión, stats y pruebas de broadcast.
- Health y metrics: verificación operativa y observabilidad.

## Brechas de información identificadas

- No hay evidencia directa de todos los middlewares personalizados más allá de rate limiting y emisor de eventos WebSocket; otros podrían existir y no estar visibles en los fragmentos revisados.
- Algunos routers (por ejemplo, users, tasks, statistics) no fueron leídos en detalle; es posible que contengan dependencias o patrones adicionales.
- El estado exacto del índice espacial PostGIS en producción y si la migración completa fue aplicada manualmente permanece不确定.
- Configuraciones de usuarios/roles a nivel de base de datos más allá del uso de JWT no están descritas con granularidad.
- No se observa una política explícita de auditoría en base de datos (triggers/tablas de auditoría) más allá del logging de aplicación.
- No se dispone de métricas de rendimiento reales de producción (latencias, throughput, saturación de pool); solo la instrumentación y configuración.
- No hay confirmación de los límites de rate limiting ni su almacenamiento (memoria/Redis).
- Parámetros finos de despliegue multi-región en Fly.io (replicación de DB, affinities) más allá de fly.toml no están documentados.

## Referencias

[^1]: Repositorio GRUPO_GAD — GitHub. https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD — Aplicación en Fly.io. https://grupo-gad.fly.dev