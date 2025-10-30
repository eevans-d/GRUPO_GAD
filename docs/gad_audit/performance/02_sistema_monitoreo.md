# Auditoría Profunda del Sistema de Monitoreo de GRUPO_GAD (Prometheus + Grafana)

Fecha: 29 de octubre de 2025  
Proyecto: Sistema de Gestión Administrativa Gubernamental  
Alcance: Evaluación técnica del monitoreo en producción, cobertura de alertas, dashboards y recomendaciones de mejora  
URL de producción: https://grupo-gad.fly.dev

---

## 1. Resumen ejecutivo

GRUPO_GAD opera en un contexto gubernamental que exige disponibilidad continua, trazabilidad exhaustiva y respuesta ante incidentes严苛. La plataforma de observabilidad implementada cubre los pilares esenciales: instrumentación de métricas de aplicación y WebSocket en el backend FastAPI, scraping periódico por Prometheus, gestión y enrutamiento de alertas con Alertmanager, y visualización en Grafana. La configuración base es sólida y está bien pensada para un servicio 24/7, con prácticas alineadas a un entorno de producción.

El sistema expone métricas personalizadas (prefijo ggrt_) para conexiones, mensajes y latencias de WebSocket; consume métricas de infraestructura (Node Exporter) y de servicios (PostgreSQL y Redis vía exporters), y enruta alertas críticas hacia correo y potencialmente Slack, con agrupación y tiempos de espera parametrizados. Sin embargo, la auditoría evidencia brechas que deben abordarse para cumplir estándares de misión crítica: dependencia de métricas HTTP no confirmadas en la aplicación (http_requests_total y histogramas de latencia), cobertura parcial de exporters clave (Caddy exporter ausente pese a existir proxy reverso), ausencia de dashboards JSON de Grafana para validación, y configuración incompleta o pendiente de revisión de integraciones externas (Slack, Webhook genérico) junto con secretos que requieren gestión formal.

Las recomendaciones se priorizan en tres horizontes: 0–30 días, enfoque en remediación inmediata para alertas y métricas HTTP, rollout y validación de dashboards mínimos viables, y endurecimiento de Alertmanager; 30–60 días, expansión de exporters (Caddy, si aplica), afinado de thresholds según líneas base y tests de caos controlando Redis; 60–90 días, telemetría avanzada en el bot de Telegram, SLOs por dominio (API, WebSocket, PostGIS), y automatización de los ejercicios de respuesta a incidentes con runbooks.

Para situar el panorama de criticidad, el siguiente mapa resume los hallazgos y su impacto operativo.

Tabla 1. Mapa de hallazgos vs impacto y prioridad

| Hallazgo                                                                 | Impacto                                                                                              | Prioridad |
|--------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------|
| Dependencia de métricas HTTP no confirmadas en aplicación (http_requests_total, histogramas) | Alertas de error rate y latencia (HighErrorRate, HighLatencyP95, CriticalLatencyP99) sin fuente clara | Crítica   |
| Ausencia de dashboards JSON de Grafana validados                          | Visualización y troubleshooting de servicio 24/7 incompletos                                          | Alta      |
| Caddy exporter comentado (prometheus.yml) y dashboard no visible          | Observabilidad del proxy reverso faltante                                                             | Media     |
| Integración Slack y webhook genérico con placeholders                     | Enrutamiento de alertas críticas puede fallar en producción                                           | Alta      |
| Mantenimiento de credenciales (SMTP password, Slack webhook URL) sin gestor | Riesgo de fuga/rotación tardía y notificaciones no confiables                                          | Alta      |
| Umbrales estáticos en infraestructura sin baseline por entorno            | Riesgo de falsos positivos/negativos; tuning insuficiente                                             | Media     |
| Reglas WebSocket con nombres no alineados a métricas expuestas            | Alertas WebSocket potencialmente firing con datos ausentes                                            | Alta      |

Interpretación: la criticidad se concentra en la fiabilidad de las métricas HTTP que alimentan alertas de disponibilidad y rendimiento de la API, y en la ausencia de dashboards mínimos viables que habiliten triage efectivo. La remediación temprana de estas áreas impacta directamente la reducción del MTTR y la confianza operativa.

## 2. Alcance, fuentes y metodología

El alcance de esta auditoría cubre: (i) instrumentación de métricas en la aplicación FastAPI y el subsistema WebSocket; (ii) reglas de alertas Prometheus y su categorización; (iii) configuración de scraping y targets; (iv) enrutamiento y gestión de alertas en Alertmanager; (v) provisioning y datasource de Grafana; (vi) integración operativa con Fly.io (health checks, puertos de métricas); y (vii) evaluación de cobertura para componentes críticos 24/7 (FastAPI, Telegram Bot, Redis Pub/Sub, WebSockets, PostgreSQL/PostGIS).

La metodología consistió en revisar la instrumentación de métricas de observabilidad (con prefijo ggrt_), la configuración de Prometheus (prometheus.yml), las reglas de alertas (alerts.yml), la configuración de Alertmanager (alertmanager.yml) y el datasource de Grafana (datasources/prometheus.yml). Además, se analizó la integración de producción (fly.toml) y la definición de servicios del entorno de desarrollo (docker-compose.yml), para entender el despliegue y los health checks.

Para ilustrar la cobertura del análisis por componente, se presenta el inventario revisado.

Tabla 2. Inventario de archivos revisados

| Archivo/Componente                                 | Rol en observabilidad                                         | Hallazgos clave                                                                 |
|----------------------------------------------------|----------------------------------------------------------------|----------------------------------------------------------------------------------|
| observability/metrics.py                           | Instrumentación de métricas WebSocket (ggrt_*)                | Gauge/Counter/Histogram definidos;buckets de latencia establecidos               |
| monitoring/prometheus/prometheus.yml               | Scrape jobs y evaluación de reglas                            | Jobs para API/Postgres/Redis/Node/Prometheus/Alertmanager; Caddy comentado       |
| monitoring/prometheus/alerts.yml                   | Reglas de alerta por dominio                                  | 20 reglas catalogadas; dependencias de métricas HTTP no confirmadas              |
| monitoring/alertmanager/alertmanager.yml           | Rutas, receivers, agrupamiento, inhibiciones                  | SMTP configurado; Slack con placeholder; rutas por severidad/componente          |
| monitoring/grafana/provisioning/datasources/prometheus.yml | Datasource Grafana                                            | Prometheus como fuente por defecto, intervalación 15s                            |
| fly.toml                                           | Health checks, puerto de métricas, región y recursos          | /health y /metrics expuestos; estrategia rolling; métricas en 9091               |
| docker-compose.yml                                 | Orquestación local (db, redis, api, bot, caddy)               | Health checks locales; dependencia api-bot; Caddy como proxy                     |

Limitaciones: no se dispone del detalle de las 23 reglas de alertas, de dashboards JSON de Grafana, ni confirmación de métricas HTTP instrumentadas en la API; el Caddy exporter no está habilitado y su dashboard no es visible; la configuración de Slack en Alertmanager contiene placeholders; el gestor de secretos en producción no está documentado. Estas brechas se reflejan como “information_gaps” en el documento.

## 3. Arquitectura de monitoreo y flujos de datos

El flujo de observabilidad parte de la aplicación FastAPI y el subsistema WebSocket que instrumentan métricas con el prefijo ggrt_, expuesta en el endpoint /metrics. Prometheus scrappea estos y otros targets (PostgreSQL, Redis, Node Exporter, Alertmanager) con intervalos definidos (15s global; 10s para API). Las alertas se evalúan cada 15s según evaluation_interval y se enrutan mediante Alertmanager a múltiples receivers (correo, Slack), con agrupación e inhibiciones para reducir ruido y evitar notificaciones redundantes. Grafana utiliza Prometheus como datasource para construir dashboards de seguimiento operativo.

En el entorno de producción, la aplicación se despliega con health checks HTTP en /health y un puerto de métricas 9091. Los contenedores de desarrollo incluyen servicios dependientes (db, redis, api, bot, caddy) y health checks, garantizando que el bot se inicie sólo cuando la API esté saludable.

Para clarificar el mapa de scraping, se resume a continuación.

Tabla 3. Mapa de scraping targets

| job        | endpoint                    | intervalo | etiquetas                       |
|------------|-----------------------------|-----------|----------------------------------|
| prometheus | localhost:9090              | 15s       | service=prometheus               |
| api        | api:8000/metrics            | 10s       | service=fastapi; component=api   |
| postgres   | postgres-exporter:9187      | 15s       | service=postgresql; component=database |
| redis      | redis-exporter:9121         | 15s       | service=redis; component=cache   |
| node       | node-exporter:9100          | 15s       | service=node-exporter; component=infrastructure |
| alertmanager | alertmanager:9093         | 15s       | service=alertmanager; component=alerting |
| caddy (comentado) | caddy-exporter:9180   | 15s       | service=caddy; component=reverse-proxy |

Interpretación: el conjunto de jobs cubre la mayoría de superficies críticas. La omisión del Caddy exporter limita la visibilidad del proxy reverso, componente que influye en disponibilidad y latencia percibida por los usuarios.

### 3.1 Componentes y responsabilidades

- observability/metrics.py: define métricas personalizadas con prefijo ggrt_ para WebSocket (conexiones activas, totales, mensajes enviados, broadcasts, errores de envío, heartbeat y latencia), expone funciones para instrumentación y actualización masiva.
- monitoring/prometheus/prometheus.yml: configura scrape_interval global y por job (API a 10s), evaluation_interval, external_labels del clúster, y carga reglas desde alerts.yml.
- monitoring/prometheus/alerts.yml: agrupa reglas por dominios (API, DB, Redis, Infraestructura, WebSocket), define expresiones y severidades.
- monitoring/alertmanager/alertmanager.yml: establece rutas por severidad y componente, receivers de correo y Slack, agrupación e inhibiciones.
- monitoring/grafana/provisioning/datasources/prometheus.yml: define Prometheus como datasource por defecto y parámetros de consulta (intervalo, timeout, método HTTP).
- fly.toml: especifica health checks, puerto de métricas, región primaria y estrategia de despliegue, con variables que influyen en observabilidad y resiliencia.

### 3.2 Endpoints y puertos de métricas

La aplicación expone /metrics en el servicio API (puerto 8000 en desarrollo). En producción, el puerto de métricas indicado es 9091. Los exporters de PostgreSQL y Redis usan puertos 9187 y 9121, respectivamente, y Node Exporter el 9100. Alertmanager escucha en 9093.

Tabla 4. Inventario de puertos/servicios de métricas

| Servicio/Target    | Puerto  | Protocolo | Función                           |
|--------------------|---------|-----------|-----------------------------------|
| API (FastAPI)      | 8000 (dev), 9091 (prod metrics) | HTTP       | Exposición de /metrics (ggrt_*)   |
| postgres-exporter  | 9187    | HTTP       | Métricas de PostgreSQL            |
| redis-exporter     | 9121    | HTTP       | Métricas de Redis                 |
| node-exporter      | 9100    | HTTP       | Métricas de host (CPU, memoria, disco) |
| alertmanager       | 9093    | HTTP       | Gestión y enrutamiento de alertas |
| prometheus         | 9090    | HTTP       | Scraping y evaluación de reglas   |

Interpretación: la asignación de puertos facilita la segmentación de responsabilidades. En producción, la separación del puerto de métricas (9091) ayuda a exponer sólo lo necesario para scraping sin interferir con el tráfico de negocio.

## 4. Métricas personalizadas de aplicación (FastAPI/WebSocket)

La instrumentación cubre el ciclo de vida de conexiones WebSocket y la mensajería asociada: conexiones activas (Gauge), total de conexiones y mensajes (Counter), broadcasts y errores de envío (Counter), timestamp del último heartbeat (Gauge), latencia de mensajes (Histogram), usuarios activos (Gauge) y conexiones por rol (Gauge). Las etiquetas se restringen a “env” y “role”, evitando cardinalidad excesiva.

Tabla 5. Catálogo de métricas personalizadas (ggrt_*)

| Nombre                              | Tipo      | Etiquetas               | Descripción                                                   | Funciones de instrumentación                         |
|-------------------------------------|-----------|-------------------------|---------------------------------------------------------------|------------------------------------------------------|
| ggrt_active_connections             | Gauge     | [env]                   | Conexiones WebSocket activas                                  | connection_established, connection_closed, update_all_metrics_from_manager |
| ggrt_connections_total              | Counter   | [env]                   | Total histórico de conexiones aceptadas                       | connection_established                               |
| ggrt_messages_sent_total            | Counter   | [env]                   | Mensajes enviados (unicast + broadcast)                       | message_sent                                         |
| ggrt_broadcasts_total               | Counter   | [env]                   | Total de eventos broadcast realizados                         | message_sent(is_broadcast=True)                      |
| ggrt_send_errors_total              | Counter   | [env]                   | Total de errores al enviar mensajes WebSocket                 | send_error                                           |
| ggrt_heartbeat_last_timestamp       | Gauge     | [env]                   | Timestamp del último ciclo heartbeat completado               | heartbeat_completed, update_all_metrics_from_manager |
| ggrt_role_connections               | Gauge     | [env, role]             | Conexiones WebSocket activas por rol                          | connection_established/closed (con role), update_all_metrics_from_manager |
| ggrt_user_active                    | Gauge     | [env]                   | Usuarios únicos con al menos una conexión activa              | update_user_count, update_all_metrics_from_manager   |
| ggrt_message_latency_seconds        | Histogram | [env]                   | Latencia de mensajes WebSocket (segundos), buckets definidos  | record_message_latency                               |

Buckets de latencia recomendados y su propósito operativo:

Tabla 6. Buckets de histograma de latencia

| Buckets (s)                     | Propósito de observabilidad                                                    |
|---------------------------------|--------------------------------------------------------------------------------|
| 0.001, 0.005, 0.01              | Medición de latencias muy bajas (red local, operaciones triviales)            |
| 0.025, 0.05                     | Latencias bajas en condiciones normales de carga                               |
| 0.1, 0.25                       | Latencias moderadas; detección temprana de colas o contención                  |
| 0.5, 1.0                        | Latencias altas; potenciales cuellos de botella o congestión                   |
| 2.5, 5.0                        | Latencias críticas; incidentes severos o fallas de dependencias                |

Interpretación: la cobertura de métricas es adecuada para medir el “pulso” del subsistema WebSocket, con buena granularidad en latencias. El diseño evita cardinalidad excesiva al limitar etiquetas, una buena práctica en entornos gubernamentales con cargas sostenidas.

### 4.1 Métricas por dominio de negocio

- Usuarios y roles: user_active y role_connections permiten entender la distribución de acceso por perfil, relevante para priorizar soporte y capacity planning.
- WebSockets: active_connections, connections_total, broadcasts_total y send_errors_total facilitan observar estabilidad del canal de tiempo real, vital para operaciones críticas 24/7.

## 5. Reglas de alertas Prometheus (cobertura y clasificación)

La configuración define 20 reglas agrupadas en cinco dominios: API (disponibilidad, errores HTTP, latencias P95/P99), Base de datos (conexiones, queries lentas, uso de disco), Redis (disponibilidad, memoria, evicciones), Infraestructura (CPU, memoria, disco), y WebSocket (conexiones altas, errores de broadcast). Esta clasificación soporta una operación estructurada y resiliente.

Tabla 7. Listado consolidado de reglas (20)

| Nombre                     | Dominio          | Expresión (resumen)                                              | For       | Severidad | Componente   |
|---------------------------|------------------|------------------------------------------------------------------|-----------|-----------|--------------|
| APIDown                   | API              | up{job="api"} == 0                                               | 1m        | critical  | api          |
| HighErrorRate             | API              | rate(http_requests_total{5xx})/rate(http_requests_total) > 5%    | 5m        | warning   | api          |
| HighLatencyP95            | API              | P95 de http_request_duration_seconds_bucket > 0.5s               | 5m        | warning   | api          |
| CriticalLatencyP99        | API              | P99 de http_request_duration_seconds_bucket > 2s                 | 2m        | critical  | api          |
| PostgreSQLDown            | Database         | up{job="postgres"} == 0                                          | 1m        | critical  | database     |
| TooManyConnections        | Database         | pg_stat_activity_count > 80                                      | 5m        | warning   | database     |
| SlowQueries               | Database         | pg_stat_activity_max_tx_duration > 60s                           | 2m        | warning   | database     |
| HighDatabaseDiskUsage     | Database         | (pg_database_size_bytes / fs_size) * 100 > 80                    | 5m        | warning   | database     |
| RedisDown                 | Redis            | up{job="redis"} == 0                                             | 1m        | critical  | cache        |
| RedisMemoryHigh           | Redis            | redis_memory_used_bytes/max_bytes * 100 > 90                     | 5m        | warning   | cache        |
| RedisHighEvictionRate     | Redis            | rate(redis_evicted_keys_total[5m]) > 100                         | 5m        | warning   | cache        |
| HighCPUUsage              | Infraestructura  | 100 - avg(rate(node_cpu_idle[5m]))*100 > 80                      | 5m        | warning   | infrastructure |
| HighMemoryUsage           | Infraestructura  | (1 - MemAvailable/MemTotal)*100 > 85                             | 5m        | warning   | infrastructure |
| CriticalMemoryUsage       | Infraestructura  | (1 - MemAvailable/MemTotal)*100 > 95                             | 2m        | critical  | infrastructure |
| DiskSpaceLow              | Infraestructura  | (avail/size)*100 < 15                                            | 5m        | warning   | infrastructure |
| DiskSpaceCritical         | Infraestructura  | (avail/size)*100 < 5                                             | 2m        | critical  | infrastructure |
| HighWebSocketConnections  | WebSocket        | websocket_connections_active > 1000                              | 5m        | warning   | websocket    |
| HighWebSocketBroadcastErrors | WebSocket     | rate(websocket_broadcast_errors_total[5m]) > 10                  | 5m        | warning   | websocket    |

Interpretación: las reglas cubren necesidades operativas esenciales. Sin embargo, varias expresiones dependen de métricas HTTP cuya presencia en la aplicación no está confirmada (http_requests_total y histogramas de duración). Adicionalmente, las reglas WebSocket requieren métricas con nombres específicos que deben estar instrumentadas y scrappeadas correctamente.

### 5.1 API Health & Availability

- APIDown: utiliza up{job="api"}, cubre disponibilidad básica.
- HighErrorRate: se apoya en http_requests_total con etiqueta status=~"5.." y tasas en 5 minutos; requiere validación de instrumentación.
- Latencias P95/P99: utilizan histogramas de http_request_duration_seconds_bucket; si la métrica no existe, las reglas no dispararán correctamente.

### 5.2 Database Health

- PostgreSQLDown: consulta up{job="postgres"}, dependiente del exporter.
- TooManyConnections y SlowQueries: requieren métricas del exporter de PostgreSQL (pg_stat_activity_count, pg_stat_activity_max_tx_duration).
- HighDatabaseDiskUsage: combina tamaños de base de datos con filesystem; exige selección de mountpoint correcto.

### 5.3 Redis Health

- RedisDown, RedisMemoryHigh, RedisHighEvictionRate: dependen de métricas del redis-exporter y límites de memoria configurados.

### 5.4 Infraestructura (Host)

- CPU, memoria y disco: métricas de Node Exporter, con thresholds estáticos para entornos gubernamentales; se recomienda establecer baselines por región/tenant.

### 5.5 WebSocket Health

- HighWebSocketConnections y HighWebSocketBroadcastErrors: requieren métricas específicas (websocket_connections_active y websocket_broadcast_errors_total). Estas no figuran en la instrumentación revisada, que utiliza prefijos ggrt_*; es necesario alinear nombres y exposición para que las alertas funcionen.

## 6. Scraping targets y configuración de Prometheus

El archivo prometheus.yml define external_labels del clúster (grupo_gad_production, production), evaluation_interval y scrape_interval globales (15s), y el job de la API con scrape_interval de 10s, que es adecuado para observar cambios rápidos en un servicio gubernamental. Se incluyen jobs para Prometheus self-monitoring, PostgreSQL, Redis, Node Exporter y Alertmanager. El job de Caddy exporter está comentado, por lo que las métricas del proxy reverso no están actualmente scrapeadas.

Tabla 8. Resumen de scrape jobs

| job         | objetivo                  | intervalo | labels                           | comentarios                         |
|-------------|---------------------------|-----------|----------------------------------|-------------------------------------|
| prometheus  | localhost:9090            | 15s       | service=prometheus               | Self-monitoring                     |
| api         | api:8000/metrics          | 10s       | service=fastapi, component=api   | Métricas ggrt_* y posiblemente HTTP |
| postgres    | postgres-exporter:9187    | 15s       | service=postgresql, component=database | Métricas de DB                 |
| redis       | redis-exporter:9121       | 15s       | service=redis, component=cache   | Memoria y evicciones                |
| node        | node-exporter:9100        | 15s       | service=node-exporter, component=infrastructure | Host metrics           |
| alertmanager| alertmanager:9093         | 15s       | service=alertmanager, component=alerting | Estado de Alertmanager        |
| caddy       | (comentado)               | 15s       | service=caddy, component=reverse-proxy | Exportador ausente              |

Interpretación: el baseline de scraping es coherente y frecuente para la API. La ausencia del Caddy exporter es una oportunidad de mejora para visibilidad end-to-end, especialmente para eventos HTTPS y latencias del proxy.

## 7. Alertmanager: enrutamiento, agrupación e inhibiciones

Alertmanager configura tiempos de agrupamiento y resolución coherentes con respuesta a incidentes: group_wait 10s (default), group_interval 5m, repeat_interval 4h (1h para severidad crítica), y resolve_timeout 5m. El enrutamiento separa críticos (email + Slack) y warnings (Slack), además de rutas específicas para componentes (database, api). Las inhibiciones propuestas evitan notificaciones redundantes (ej. latencia cuando la API está caída).

Tabla 9. Routes y receivers

| Route/Match                | Receiver         | Severidad/Componente | Tiempos (group_wait, repeat)        |
|---------------------------|------------------|----------------------|-------------------------------------|
| severity=critical         | critical-alerts  | critical             | 0s, 1h                              |
| severity=warning          | warning-alerts   | warning              | 30s, 4h                             |
| component=database        | database-team    | cualquier severidad | default                              |
| component=api             | api-team         | cualquier severidad | default                              |
| default                   | default-receiver | cualquier severidad | 10s, 4h                             |

Tabla 10. Inhibition rules

| Fuente                               | Target                              | equal        |
|--------------------------------------|-------------------------------------|--------------|
| severity=critical, alertname=APIDown | severity=warning, component=api     | [instance]   |
| severity=critical, alertname=InstanceDown | severity=warning (cualquier alerta) | [instance]   |

Interpretación: el diseño reduce ruido y prioriza alertas críticas. La configuración de Slack utiliza placeholders; es imprescindible completar la URL del webhook y validar el canal en producción. La gestión de credenciales (SMTP y Slack) requiere formalizar el proceso con un gestor de secretos.

## 8. Dashboards de Grafana y visualización

La configuración del datasource apunta a Prometheus como fuente por defecto, con timeInterval de 15s y queryTimeout de 60s, adecuados para consultas frecuentes y tiempos de espera razonables. El proveedor de dashboards define una carpeta “GRUPO_GAD” y un path estándar; no se dispone de dashboards JSON para validar paneles clave. Se recomienda contar con un set mínimo que soporte operaciones 24/7: API (latencias P50/P95/P99, throughput, error rate), WebSocket (conexiones activas, mensajes, errores, latencias), Redis (memoria, evicciones, hit rate), PostgreSQL/PostGIS (conexiones, queries lentas, tamaño de DB), e Infraestructura (CPU, memoria, disco).

Tabla 11. Plantilla de panel por dominio

| Panel                     | Métricas origen                       | IntervaloSuggested | Umbrales de visualización               |
|---------------------------|---------------------------------------|--------------------|-----------------------------------------|
| API Latency P95/P99       | http_request_duration_seconds_bucket  | 15s                | P95 > 0.5s (warning), P99 > 2s (critical) |
| API Error Rate            | http_requests_total{5xx}              | 15s                | > 5% en 5m (warning)                    |
| WebSocket Conexiones Activas | ggrt_active_connections              | 15s                | > 1000 (warning)                        |
| WebSocket Errores de Envío | ggrt_send_errors_total                | 15s                | Tendencia al alza en 5m                 |
| Redis Memoria             | redis_memory_used_bytes/max_bytes     | 15s                | > 90% (warning)                         |
| PostgreSQL Conexiones     | pg_stat_activity_count                | 15s                | > 80 (warning)                          |
| Infraestructura CPU       | node_cpu_seconds_total (idle)         | 15s                | > 80% usage (warning)                   |

Interpretación: un set mínimo de dashboards, alineado con las reglas de alertas, mejora el triage y la comunicación en incidentes, especialmente para equipos de guardia y dirección.

## 9. Evaluación de cobertura por componente crítico 24/7

La cobertura actual es adecuada en infraestructura y servicios base (PostgreSQL, Redis, Node, Alertmanager). Persisten brechas en métricas de aplicación HTTP (API) y observabilidad del proxy reverso (Caddy), además de componentes dependientes de métricas que no están explícitamente confirmadas (Telegram Bot, PostGIS en dashboards y alertas específicas).

Tabla 12. Matriz de cobertura

| Componente                   | Métricas disponibles                      | Reglas asociadas                        | Dashboards requeridos                     | Estado         |
|-----------------------------|-------------------------------------------|-----------------------------------------|-------------------------------------------|----------------|
| API FastAPI                 | ggrt_* (WebSocket), métricas HTTP no confirmadas | APIDown, HighErrorRate, latencias P95/P99 | API latency/throughput/error rate         | Parcial        |
| WebSockets                  | ggrt_active_connections, etc.             | HighWebSocketConnections, BroadcastErrors | Conexiones/mensajes/latencia/errores      | Parcial        |
| Redis Pub/Sub               | redis-exporter                            | RedisDown/MemoryHigh/EvictionRate       | Memoria/evicciones/hit rate               | Completo       |
| Telegram Bot                | No métricas explícitas                    | N/A                                      | Errores/colas/mensajería                  | Brecha         |
| PostgreSQL/PostGIS          | postgres-exporter                         | PostgreSQLDown/Connections/SlowQueries/Disk | Conexiones/queries/tamaño DB             | Completo       |
| Infraestructura (CPU/mem/disco) | node-exporter                          | CPU/Memoria/Disco                        | Panel host básico                         | Completo       |
| Proxy reverso (Caddy)       | exporter ausente                          | N/A                                      | Latencia/tasa HTTPS                       | Brecha         |

Interpretación: completar la instrumentación HTTP en la API, habilitar el Caddy exporter y definir dashboards mínimos viables elevará la cobertura a niveles apropiados para operación gubernamental continua.

## 10. Integración con Fly.io y operación en producción

La configuración de despliegue define health checks HTTP cada 15s en /health, un puerto de métricas 9091 y una estrategia de rolling updates con auto_rollback para evitar downtime. La región primaria es cercana a Latinoamérica, adecuada para latencias hacia usuarios gubernamentales. Las variables de entorno relevantes incluyen límites y heartbeat para WebSockets (WS_MAX_CONNECTIONS, WS_HEARTBEAT_INTERVAL) que impactan la observabilidad de conexiones.

Tabla 13. Mapa de health checks y métricas en Fly.io

| Servicio     | Endpoint/Port       | Intervalo | Finalidad                         | Relación con alertas            |
|--------------|---------------------|-----------|-----------------------------------|---------------------------------|
| API          | /health (HTTP), /metrics (9091) | 15s       | Disponibilidad y exposición de métricas | Fundamento para APIDown y métricas HTTP |
| Proxy (Caddy)| N/A (no monitoreado) | N/A       | HTTPS/TLS y enrutamiento          | Requiere exporter para visibilidad |
| Prometheus   | 9090                | 15s       | Evaluación y scraping             | Evalúa reglas y dispara alertas |
| Alertmanager | 9093                | 15s       | Gestión de alertas                | Rutas y receivers operan        |

Interpretación: el setup en Fly.io es consistente con prácticas modernas de despliegue sin downtime. La próxima madurez pasa por asegurar el exporter de Caddy y consolidar dashboards en producción para una operación 24/7 robusta.

## 11. Riesgos, brechas y deuda técnica

El principal riesgo es la inconsistencia entre las reglas de alertas y las métricas efectivamente expuestas, en particular las métricas HTTP requeridas por reglas de la API y las reglas WebSocket que dependen de nombres no presentes en la instrumentación actual. La ausencia de dashboards limita el triage rápido y puede aumentar el MTTR. Además, secretos gestionados de forma manual presentan riesgo de seguridad y disponibilidad en notificaciones.

Tabla 14. Registro de riesgos

| Riesgo                                                    | Evidencia                                | Impacto                  | Probabilidad | Mitigación propuesta                                                    | Prioridad |
|-----------------------------------------------------------|------------------------------------------|--------------------------|--------------|-------------------------------------------------------------------------|-----------|
| Métricas HTTP ausentes en aplicación                     | Reglas HighErrorRate y latencias         | Alertas no fiables       | Alta         | Instrumentar http_requests_total y histogramas; validar scraping        | Crítica   |
| Reglas WebSocket con nombres no expuestos                 | Alertas usan nombres distintos a ggrt_*  | Alertas firing sin datos | Alta         | Alinear nombres o adaptar reglas a métricas ggrt_*                      | Alta      |
| Caddy exporter ausente                                   | Job comentado                            | Sin visibilidad proxy    | Media        | Habilitar caddy-exporter y dashboard correspondiente                    | Media     |
| Dashboards no disponibles                                 | Sin JSON visibles                        | Triage limitado          | Alta         | Crear dashboards mínimos viables (API/WebSocket/Redis/PostGIS/Infra)    | Alta      |
| Slack y secretos sin gestor                               | Placeholders y credenciales sueltas      | Notificaciones fallidas  | Alta         | Completar integración Slack; gestor de secretos; rotación periódica     | Alta      |
| Umbrales estáticos sin baseline                           | Thresholds fijos por entorno             | Falsos positivos/negativos | Media     | Establecer baselines y ajustar thresholds por carga y región            | Media     |

Interpretación: la mitigación de estos riesgos debe orquestarse en el plan de 90 días, priorizando instrumentación de HTTP y dashboards mínimos viables.

## 12. Recomendaciones y roadmap de mejora (0–30 / 30–60 / 60–90 días)

0–30 días (estabilización):
- Confirmar e instrumentar métricas HTTP necesarias (http_requests_total, status codes, histogramas de duración). Sin estas, las alertas de error rate y latencia carecen de fuente.
- Alinear reglas WebSocket con métricas ggrt_* o exponer métricas con nombres referenciados en las alertas (websocket_connections_active, websocket_broadcast_errors_total).
- Crear dashboards mínimos viables: API (latencia P95/P99, throughput, error rate), WebSocket (conexiones, mensajes, errores), Redis (memoria, evicciones), PostgreSQL (conexiones, queries lentas), Infraestructura (CPU, memoria, disco).
- Completar y probar integración Slack y definir gestión formal de secretos (SMTP, Slack webhook, API keys).
- Validar rutas y receievers de Alertmanager en entorno productivo; ejecutar ejercicios de notificación.

30–60 días (optimización y ampliación):
- Habilitar Caddy exporter y el job en Prometheus; construir dashboard de proxy con latencia y throughput HTTPS.
- Afinar umbrales con baselines de carga (por ejemplo, percentiles de latencia por endpoint crítico, evict keys/s en Redis según patrón de uso).
- Introducir circuit breakers y backpressure en Redis Pub/Sub y WebSocket; pruebas de caos controladas (desconexión Redis, saturación de conexiones).
- Extender alertas específicas para Telegram Bot (errores, latencia de notificaciones, colas).

60–90 días (observabilidad avanzada y resiliencia):
- Definir SLOs y SLIs por dominio (API: disponibilidad 99.9%, P95 < 500ms; WebSocket: entrega < 250ms P95; PostGIS: queries < 200ms P95 en endpoints críticos).
- Consolidar dashboards ejecutivos y operativos; incorporar métricas de cumplimiento y auditoría.
- Automatizar runbooks de incidentes con vínculos entre paneles de Grafana y alertas; establecer calendario de guardia y rotación.
- Remote write hacia almacenamiento de largo plazo si se requiere retención extendida y análisis de tendencias.

Tabla 15. Plan de acción priorizado

| Tarea                                                   | Horizonte | Dueño        | Dependencia                         | Métrica de éxito                                 |
|---------------------------------------------------------|-----------|--------------|-------------------------------------|--------------------------------------------------|
| Instrumentar métricas HTTP y validar scraping           | 0–30 días | Backend/API  | Ninguna                             | Alertas HighErrorRate y latencias firing con datos |
| Alinear reglas WebSocket con métricas ggrt_*            | 0–30 días | Backend/API  | Métricas HTTP                       | Alertas WS basadas en datos reales               |
| Crear dashboards mínimos viables                        | 0–30 días | SRE/DevOps   | Métricas listas                     | Paneles operativos disponibles en Grafana        |
| Completar integración Slack y gestor de secretos        | 0–30 días | SRE/DevOps   | Acceso a Slack y gestor de secretos | Notificaciones críticas en Slack verificadas     |
| Habilitar Caddy exporter y dashboard proxy              | 30–60 días| SRE/DevOps   | Acceso a Caddy                      | Panel de proxy operativo y alertas de latencia   |
| Afinar umbrales y baselines                             | 30–60 días| SRE/DevOps   | Dashboards disponibles              | Reducción de falsos positivos/negativos          |
| Pruebas de caos y backpressure en Redis/WebSocket       | 30–60 días| SRE/QA       | Umbrales afinados                   | Recuperación sin incidentes mayores              |
| Telemetría del Bot (errores, colas, latencias)          | 30–60 días| Backend/Bot  | Instrumentación adicional           | Alertas y panel del Bot operativo                |
| Definir SLO/SLI y dashboards ejecutivos                 | 60–90 días| Arquitectura | Dashboards mínimos                  | SLOs documentados y aprobados                    |
| Automatizar runbooks y calendario de guardia            | 60–90 días| Operaciones  | SLO/SLI establecidos                | Ejercicios de incident response ejecutados       |

Interpretación: el roadmap prioriza primero la confiabilidad de métricas y la visualización mínima para operar, luego amplía la superficie observada y, finalmente, introduce prácticas avanzadas de gestión de servicio (SLO/SLI, automatización de incidentes).

## 13. Anexos técnicos

Para facilitar la implementación, se incluyen fragmentos de configuración de referencia.

Fragmento de relabel del job de API (prometheus.yml):
```yaml
- job_name: 'api'
  scrape_interval: 10s
  metrics_path: '/metrics'
  static_configs:
    - targets: ['api:8000']
      labels:
        service: 'fastapi'
        component: 'api'
  relabel_configs:
    - source_labels: [__address__]
      target_label: instance
      replacement: 'grupo_gad_api'
```

Rutas de Alertmanager por severidad y componente (alertmanager.yml):
```yaml
route:
  receiver: 'default-receiver'
  group_by: ['alertname', 'component', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 0s
      repeat_interval: 1h
    - match:
        severity: warning
      receiver: 'warning-alerts'
      group_wait: 30s
      repeat_interval: 4h
    - match:
        component: database
      receiver: 'database-team'
    - match:
        component: api
      receiver: 'api-team'
```

Ejemplo de Gauge y Counter con etiqueta de entorno (observability/metrics.py):
```python
from prometheus_client import Counter, Gauge, Histogram

ENV_LABEL = "env"
METRIC_PREFIX = "ggrt_"

active_connections = Gauge(
    f"{METRIC_PREFIX}active_connections",
    "Número actual de conexiones WebSocket activas",
    [ENV_LABEL]
)

connections_total = Counter(
    f"{METRIC_PREFIX}connections_total",
    "Total histórico de conexiones WebSocket aceptadas",
    [ENV_LABEL]
)

message_latency = Histogram(
    f"{METRIC_PREFIX}message_latency_seconds",
    "Latencia de mensajes WebSocket (segundos)",
    [ENV_LABEL],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)
```

Interpretación: estos fragmentos ilustran cómo profundizar la instrumentación, estandarizar el etiquetado y organizar el enrutamiento de alertas, con un enfoque pragmático que facilita la adopción en equipos de backend y SRE.

---

Notas finales sobre brechas de información: esta auditoría se basó en la configuración disponible; no se disposó de dashboards JSON de Grafana, confirmación de métricas HTTP en la API, ni detalle completo de las 23 reglas (se revisaron 20). La integración de Slack y gestión de secretos requiere ajustes para producción. Estas brechas están reflejadas en los riesgos y recomendaciones y deben abordarse de manera prioritaria.