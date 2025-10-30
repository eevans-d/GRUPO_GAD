# Auditoría Integral de la Integración Prometheus + Grafana + Alertmanager para Monitoreo Operativo 24/7 en GRUPO_GAD

## Resumen ejecutivo

GRUPO_GAD requiere un monitoreo operativo 24/7 alineado con estándares de misión crítica en el sector público: disponibilidad sostenida, trazabilidad exhaustiva y reducción del tiempo medio de recuperación (MTTR). La revisión integral del stack de observabilidad —Prometheus, Alertmanager y Grafana— confirma una base sólida orientada a producción, con instrumentación personalizada para WebSocket (prefijo ggrt_), scraping periódica y reglas de alertas por dominio. No obstante, existen brechas críticas que comprometen la fiabilidad operativa: ausencia de métricas HTTP confirmadas en la API para reglas de error rate y latencias (P95/P99), discrepancias entre nombres de métricas de WebSocket en reglas y los efectivamente instrumentados (ggrt_*), falta de dashboards JSON validados, Caddy exporter comentado (sin visibilidad del proxy), e integraciones de notificación con placeholders (Slack y webhooks). Además, la retención y el escalado horizontal del monitoreo no están definidos, lo que limita el horizonte de análisis y la resiliencia del sistema.

Esta auditoría identifica hallazgos con impacto directo en disponibilidad, seguridad y compliance, y propone un plan de remediación por horizontes (0–30/30–60/60–90 días) para alcanzar la excelencia operativa. La estrategia prioriza la confiabilidad de métricas HTTP, la alineación de alertas con la instrumentación, el despliegue de dashboards mínimos viables, el endurecimiento de Alertmanager y la adopción de almacenamiento de largo plazo con capacidades de consulta global. La implementación de SLOs (Service Level Objectives) y SLIs (Service Level Indicators) institucionaliza objetivos cuantificables de fiabilidad por dominio (API, WebSocket, PostGIS), informando la operación y la mejora continua[^10][^11].

Para situar el panorama, el siguiente mapa sintetiza hallazgos, impacto operativo y prioridad de intervención.

Tabla 1. Mapa de hallazgos vs impacto y prioridad

| Hallazgo                                                                 | Impacto                                                                                              | Prioridad |
|--------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------|
| Métricas HTTP no confirmadas en la API (http_requests_total y histogramas) | Alertas de error rate y latencia sin fuente fiable; riesgo de incidentes no detectados               | Crítica   |
| Desalineación entre reglas WebSocket y métricas ggrt_*                   | Alertas que no disparan o disparan con datos ausentes; diagnóstico y triage ineficaces               | Alta      |
| Dashboards JSON no disponibles                                           | Triage lento; baja visibilidad de percentiles y tasas clave                                           | Alta      |
| Caddy exporter comentado (sin proxy metrics)                             | Sin visibilidad del proxy HTTPS; ceguera ante cuellos de botella en el perímetro                      | Media     |
| Slack y webhooks con placeholders; gestión de secretos no formalizada    | Riesgo de fallos de notificación en incidentes; exposición de credenciales                            | Alta      |
| Umbrales estáticos sin baseline por entorno                              | Falsos positivos/negativos; fatiga de alertas                                                          | Media     |
| Retención y escalado horizontal no definidos                             | Límite en análisis histórico; resiliencia insuficiente ante crecimiento                               | Media     |

Interpretación: la criticidad se concentra en la cadena de métricas de aplicación (HTTP) y en la consistencia entre instrumentación y alertas. Remediarlas tempranamente mejora directamente el MTTR y la confianza operativa.

## Alcance, fuentes y metodología

La evaluación abarca la instrumentación de métricas en FastAPI y WebSocket, reglas de alertas en Prometheus (23+ objetivo), configuración de scraping y service discovery, enrutamiento y gestión de alertas en Alertmanager, visualización y aprovisionamiento en Grafana, e integración con Fly.io para despliegue, health checks y métricas. Se revisaron archivos clave de observabilidad y configuración: instrumentación ggrt_*, prometheus.yml, alerts.yml, alertmanager.yml y datasource de Grafana, además del entorno de producción (fly.toml) y orquestación local (docker-compose.yml).

La metodología consistió en mapear flujos de observabilidad desde endpoints de métricas hasta paneles y notificaciones, validar consistencia entre nombres de métricas y reglas, inventariar targets de scraping, revisar la estructura de rutas y receivers de Alertmanager, y contrastar paneles propuestos con necesidades operativas. Las limitaciones principales fueron: falta de dashboards JSON para validación, ausencia de confirmación de métricas HTTP instrumentadas, detalle incompleto de las 23 reglas (20 revisadas), Caddy exporter comentado y placeholders en integraciones de Slack/webhooks. Las brechas se reflejan como information_gaps y se priorizan en el roadmap.

Tabla 2. Inventario de archivos revisados y rol en observabilidad

| Archivo/Componente                                 | Rol en observabilidad                                         | Hallazgos clave                                                                 |
|----------------------------------------------------|----------------------------------------------------------------|----------------------------------------------------------------------------------|
| observability/metrics.py                           | Métricas WebSocket ggrt_*                                      | Gauge/Counter/Histogram definidos; buckets de latencia establecidos              |
| monitoring/prometheus/prometheus.yml               | Scrape jobs y evaluación de reglas                             | Jobs para API/Postgres/Redis/Node/Prometheus/Alertmanager; Caddy comentado       |
| monitoring/prometheus/alerts.yml                   | Reglas de alerta por dominio                                   | 20 reglas catalogadas; dependencias de métricas HTTP no confirmadas              |
| monitoring/alertmanager/alertmanager.yml           | Rutas, receivers, agrupamiento e inhibiciones                  | SMTP configurado; Slack con placeholder; rutas por severidad/componente          |
| monitoring/grafana/provisioning/datasources/prometheus.yml | Datasource Grafana                                    | Prometheus como fuente; intervalación de consulta adecuada                        |
| fly.toml                                           | Health checks, puerto de métricas, región y recursos          | /health y /metrics expuestos; estrategia rolling; métricas en 9091               |
| docker-compose.yml                                 | Orquestación local y health checks                             | Servicios dependientes; Caddy como proxy                                         |

## Arquitectura de monitoreo integral

El flujo de observabilidad es lineal y coherente: la aplicación FastAPI y el subsistema WebSocket exponen métricas personalizadas (ggrt_*) en /metrics; Prometheus scrappea estos y otros targets con intervalos definidos; las reglas de alerta se evalúan a intervalos configurados; Alertmanager enruta notificaciones a receivers (correo, Slack) con agrupación e inhibiciones; Grafana visualiza a partir de Prometheus, habilitando triage y seguimiento operativo. En producción, el entorno de despliegue asegura health checks en /health y separación del puerto de métricas, alineando visibilidad y seguridad[^1][^6].

Para ilustrar el mapa de scraping y sus intervalos, se presenta la tabla siguiente.

Tabla 3. Mapa de scraping targets y etiquetas

| job          | endpoint                    | intervalo | etiquetas                              |
|--------------|-----------------------------|-----------|----------------------------------------|
| prometheus   | localhost:9090              | 15s       | service=prometheus                     |
| api          | api:8000/metrics            | 10s       | service=fastapi; component=api         |
| postgres     | postgres-exporter:9187      | 15s       | service=postgresql; component=database |
| redis        | redis-exporter:9121         | 15s       | service=redis; component=cache         |
| node         | node-exporter:9100          | 15s       | service=node-exporter; component=infrastructure |
| alertmanager | alertmanager:9093           | 15s       | service=alertmanager; component=alerting |
| caddy        | caddy-exporter:9180 (comentado) | 15s   | service=caddy; component=reverse-proxy |

La arquitectura de scraping es suficiente para servicios principales. La omisión del Caddy exporter reduce visibilidad del perímetro HTTPS y latencias del proxy, un área recomendada para mejora.

### Configuración de Prometheus: reglas, evaluación y service discovery

Prometheus está configurado con scrape_interval global de 15s, evaluation_interval de 15s y un scrape_interval específico de 10s para la API. Esta diferencia favorece sensibilidad a cambios rápidos en la API. Las reglas están organizadas por dominios —API, Base de datos, Redis, Infraestructura y WebSocket— y usan cláusulas `for` para tolerancia en parte de los casos. Se evidencian dependencias de métricas HTTP que no están confirmadas en la aplicación y nombres de métricas WebSocket no alineados con ggrt_*, lo que introduce riesgo en el disparo y la semántica de alertas[^1][^7].

Tabla 4. Parámetros de evaluación y scraping

| Parámetro                    | Valor           | Propósito operativo                              |
|-----------------------------|-----------------|--------------------------------------------------|
| scrape_interval (global)    | 15s             | Balance entre frescura y carga                   |
| evaluation_interval         | 15s             | Frecuencia de evaluación de reglas               |
| scrape_interval (API)       | 10s             | Mayor sensibilidad en servicio crítico           |
| external_labels             | production/cluster | Identificación de entorno y clúster           |

Interpretación: la configuración es consistente con un servicio 24/7, con sensibilidad reforzada en la API. La alineación entre instrumentación y reglas es clave para confiabilidad.

### Service discovery y target management

La gestión de targets se apoya principalmente en static_configs en desarrollo y en endpoints explícitos. Para escalar hacia múltiples instancias y regiones, se recomienda integrar métodos de discovery compatibles con el entorno (por ejemplo, Consul, Kubernetes SD o cloud discovery), preservando etiquetado homogéneo y relabeling consistente para mantener trazabilidad en rutas de alertas y paneles. Un esquema de etiquetas estable (service, component, env, region) facilita agrupación y diagnóstico.

Tabla 5. Inventario de endpoints y puertos de métricas

| Servicio/Target    | Puerto          | Protocolo | Función                                 |
|--------------------|-----------------|-----------|------------------------------------------|
| API (FastAPI)      | 8000 (dev), 9091 (prod metrics) | HTTP      | Exposición de /metrics (ggrt_*)         |
| postgres-exporter  | 9187            | HTTP      | Métricas de PostgreSQL                   |
| redis-exporter     | 9121            | HTTP      | Métricas de Redis                        |
| node-exporter      | 9100            | HTTP      | Métricas de host (CPU, memoria, disco)   |
| alertmanager       | 9093            | HTTP      | Gestión y enrutamiento de alertas        |
| prometheus         | 9090            | HTTP      | Scraping y evaluación de reglas          |

Interpretación: la separación de puertos y endpoints favorece segmentación de responsabilidades y control de exposición. El puerto de métricas dedicado en producción reduce riesgo de interferencia con tráfico de negocio.

### Storage strategy y retention policies

Prometheus, por diseño, retiene datos a corto plazo. Para cumplir retención extendida y análisis de tendencias —especialmente relevante en contextos gubernamentales— se recomiendan soluciones de almacenamiento a largo plazo y consulta global como Thanos o Cortex[^8][^9]. Thanos ofrece compacidad con object storage, deduplicación entre instancias, y un modelo de consulta que integra múltiples Prometheus (federación). Cortex aporta blocks storage y retención configurable por periodo. La elección debe considerar coste, operación, retención por dominio y requisitos de compliance.

Tabla 6. Comparativa de almacenamiento a largo plazo

| Solución   | Capacidades clave                                 | Retención y coste                       | Operación y escalabilidad                            |
|------------|----------------------------------------------------|-----------------------------------------|------------------------------------------------------|
| Thanos     | Object storage, deduplicación, query global, federación | Retención ilimitada con almacenamiento de objetos; coste en capacidad y egress | Alta disponibilidad; integración con S3/GCS/Azure; escalado por federation/sharding |
| Cortex     | Blocks storage, sharding, query distribuida        | Retención configurada por TSDB; coste por bloques y storage backend | Alta disponibilidad; operación más compleja; escalado horizontal nativo            |

Interpretación: para GRUPO_GAD, Thanos resulta pragmático si se prioriza federación entre regiones y compatibilidad con object storage ya adoptado. Cortex es apropiado si se requiere un enfoque de bloques y sharding desde el inicio. En ambos casos, se obtiene retención extendida y consulta global, indispensables para análisis histórico y auditorías.

### Horizontal scaling para Prometheus

El escalado de Prometheus requiere un plan explícito por fases. La primera es escalado vertical —más CPU, memoria y almacenamiento— para absorber crecimiento. En segunda, federación entre Prometheus regionales y sharding por dominio o servicio. Finalmente, la adopción de Thanos/Cortex para almacenamiento de largo plazo y alta disponibilidad, con deduplicación y consulta global[^8]. Este escalado disminuye riesgo de saturación, mejora resiliencia y mantiene tiempos de consulta aceptables.

Tabla 7. Estrategias de escalado y escenarios

| Estrategia                     | Descripción                                   | Escenario recomendado                       | Riesgos/consideraciones              |
|-------------------------------|-----------------------------------------------|---------------------------------------------|--------------------------------------|
| Escalado vertical             | Incremento de recursos de un Prometheus       | Crecimiento moderado de series              | Límites prácticos de memoria/CPU     |
| Federación                    | Prometheus global agrega de shards regionales | Multi-región, dominios con independencia    | Complejidad de queries y etiquetado  |
| Sharding por servicio/dominio | División de targets entre instancias          | Alta cardinalidad y carga por dominio       | Balance y orquestación de shards     |
| Thanos/Cortex                 | Almacenamiento y consulta global              | Retención larga, HA, consulta histórica     | Coste de almacenamiento y operación  |

Interpretación: un roadmap de escalado por etapas reduce interrupciones y asegura que la arquitectura evolucione conforme a demanda y retención.

## Grafana dashboards operativos

La visualización es el pilar del triage y la comunicación durante incidentes. El datasource de Grafana está configurado con Prometheus, con parámetros de consulta adecuados (intervalación y timeout). Falta, sin embargo, la provisión de dashboards JSON validados, pieza esencial para operación 24/7. Se recomienda un set mínimo alineado con reglas y SLIs: API (latencias P50/P95/P99, throughput, error rate), WebSocket (conexiones activas, mensajes, errores, latencias), Redis (memoria, evicciones, hit rate), PostGIS/PostgreSQL (conexiones, queries lentas, tamaño de DB), Infraestructura (CPU, memoria, disco). El rendimiento del dashboard depende de consultas eficientes (uso de `rate` en contadores, histogramas para percentiles), intervalación adecuada y caching.

Tabla 8. Plantilla de panel por dominio y umbrales operativos

| Panel                     | Métricas origen                               | Interval Suggested | Umbrales de visualización                 |
|---------------------------|-----------------------------------------------|--------------------|-------------------------------------------|
| API Latency P95/P99       | http_request_duration_seconds_bucket          | 15s                | P95 > 0.5s (warning), P99 > 2s (critical) |
| API Error Rate            | http_requests_total{5xx}                      | 15s                | > 5% en 5m (warning)                      |
| WebSocket Conexiones Activas | ggrt_active_connections                   | 15s                | > 1000 (warning)                          |
| WebSocket Errores de Envío | ggrt_send_errors_total                       | 15s                | Tendencia al alza en 5m                   |
| Redis Memoria             | redis_memory_used_bytes/max_bytes             | 15s                | > 90% (warning)                           |
| PostgreSQL Conexiones     | pg_stat_activity_count                        | 15s                | > 80 (warning)                            |
| Infraestructura CPU       | node_cpu_seconds_total (idle)                 | 15s                | > 80% usage (warning)                     |

Interpretación: paneles con percentiles y tasas ancladas en alertas facilitan correlación visual, disminuyendo tiempo de diagnóstico.

### Gestión de usuarios y control de acceso (RBAC)

El control de acceso basado en roles (RBAC) en Grafana permite granularidad en permisos, asignando roles fijos y personalizados por equipo y carpeta/dashboard. Es clave limitar el rol Viewer para evitar consultas no autorizadas a fuentes de datos y segmentar organizaciones cuando sea necesario. La integración con SSO (SAML/OAuth/LDAP) y aprovisionamiento SCIM facilita gobernanza y cumplimiento, especialmente en entornos públicos. Las políticas deben incluir cifrado de secretos de la base de datos y auditoría de eventos[^3][^4][^5].

Tabla 9. Matriz de roles y permisos

| Rol                    | Permisos clave                                   | Recursos controlados                   | Restricciones recomendadas                     |
|------------------------|---------------------------------------------------|----------------------------------------|-----------------------------------------------|
| Administrador Grafana  | Configuración, usuarios, roles, datasource        | Servidor, organizaciones, plugins      | Acceso controlado; auditoría obligatoria       |
| Administrador Organización | Paneles, carpetas, datasource               | Organización específica                | Segregación por dominio operativo              |
| Editor                 | Crear/editar paneles y carpetas                  | Dashboards, anotaciones                | Sin permisos de administración                 |
| Viewer                 | Ver paneles y anotaciones                        | Dashboards                             | Limitar consulta de datasource; sin acceso anónimo |
| Rol personalizado      | Permisos granulares por acción/ámbito            | Según definición (alertas, data sources) | Aprovisionamiento con RBAC/API                 |

Interpretación: RBAC minimiza exposición de datos y asegura que cada equipo gestione sólo sus recursos, clave en compliance gubernamental.

### Integración de alerting en Grafana

Grafana Alerting puede coexistir con Alertmanager de Prometheus. Se recomienda alinear templates, runbooks y severidades para evitar divergencias y fatiga de alertas, y aprovechar rutas y escalaciones centralizadas para coordinar respuesta. La correlación entre paneles y alertas reduce MTTR al vincular métricas con contexto operativo[^17].

Tabla 10. Mapa de integración de alertas

| Origen de alerta        | Ruta principal                 | Canal        | Escalación           | Runbook asociado        |
|-------------------------|--------------------------------|--------------|----------------------|-------------------------|
| Prometheus (Reglas)     | Alertmanager (severidad/componente) | Email/Slack  | Crit -> on-call      | Panel + anotaciones     |
| Grafana Alerting        | Interna -> Integración externa | Email/Slack  | Según políticas       | Panel integrado         |
| Fly.io (Health checks)  | Notificación plataforma        | Email/Webhook| Según nivel de impacto| Enlace a health history |

Interpretación: estandarizar plantillas y referencias a runbooks en ambas capas mejora la efectividad y reduce confusión.

## Métricas operativas específicas

La instrumentación de WebSocket con prefijo ggrt_* es adecuada para medir el ciclo de vida de conexiones, mensajería y latencias. Se recomienda extender a métricas HTTP en la API (contadores por método/status, histogramas de duración) para soportar reglas de error rate y latencias P95/P99. El catálogo debe evitar alta cardinalidad —con etiquetas limitadas y estables— y seguir convenciones de nombres (minúsculas, `_total` para contadores, unidades base como `_seconds`, `_bytes`)[^1].

Tabla 11. Catálogo de métricas ggrt_* y propósito

| Nombre                              | Tipo      | Etiquetas               | Descripción                                                   | Funciones de instrumentación                         |
|-------------------------------------|-----------|-------------------------|---------------------------------------------------------------|------------------------------------------------------|
| ggrt_active_connections             | Gauge     | [env]                   | Conexiones WebSocket activas                                  | connection_established, connection_closed            |
| ggrt_connections_total              | Counter   | [env]                   | Total histórico de conexiones                                 | connection_established                               |
| ggrt_messages_sent_total            | Counter   | [env]                   | Mensajes enviados (unicast + broadcast)                       | message_sent                                         |
| ggrt_broadcasts_total               | Counter   | [env]                   | Eventos broadcast realizados                                  | message_sent(is_broadcast=True)                      |
| ggrt_send_errors_total              | Counter   | [env]                   | Errores de envío                                              | send_error                                           |
| ggrt_heartbeat_last_timestamp       | Gauge     | [env]                   | Timestamp del último heartbeat                                | heartbeat_completed                                  |
| ggrt_role_connections               | Gauge     | [env, role]             | Conexiones por rol                                            | connection_established/closed (con role)             |
| ggrt_user_active                    | Gauge     | [env]                   | Usuarios únicos con conexión activa                           | update_user_count                                    |
| ggrt_message_latency_seconds        | Histogram | [env]                   | Latencia de mensajes (buckets definidos)                      | record_message_latency                               |

Interpretación: el diseño evita cardinalidad excesiva y cubre indicadores clave para operación de tiempo real.

Tabla 12. Buckets de latencia y propósito

| Buckets (s)                 | Propósito de observabilidad                                        |
|-----------------------------|---------------------------------------------------------------------|
| 0.001, 0.005, 0.01          | Latencias muy bajas (red local, operaciones triviales)             |
| 0.025, 0.05                 | Latencias bajas en condiciones normales                             |
| 0.1, 0.25                   | Latencias moderadas; detección temprana de colas                    |
| 0.5, 1.0                    | Latencias altas; potenciales cuellos de botella                     |
| 2.5, 5.0                    | Latencias críticas; incidentes severos o fallas de dependencias     |

Interpretación: buckets alineados con percentiles operativos permiten alertas y paneles más significativos.

### Métricas de efectividad operativa

La medición de eficacia del centro de operaciones debe incluir: tasa de notificación entregada, tiempo de acknowledgement (TTA), y tasa de incidentes resueltos dentro del objetivo (MTTR frente a SLO). Estas métricas permiten evaluar la capacidad de respuesta y ajustar procesos y rutas de alerta.

Tabla 13. Métricas de efectividad y definición

| Métrica                      | Definición operativa                                        | Fuente de datos                         |
|-----------------------------|--------------------------------------------------------------|-----------------------------------------|
| Notificación entregada      | % de alertas entregadas con éxito                           | Alertmanager (delivery logs)            |
| Tiempo de acknowledgment    | Mediana/percentil del tiempo hasta ACK                      | Integración on-call/Slack               |
| Incidentes resueltos        | % de incidentes cerrados dentro del objetivo definido       | Panel de incidentes/SLO tracking        |
| Fatiga de alertas           | Alertas por unidad de tiempo por receptor                   | Alertmanager + panel Grafana            |

Interpretación: la mejora de efectividad depende tanto de rutas y templates como de disciplina operativa y governance.

## Alertmanager y notificaciones

La configuración de Alertmanager define rutas por severidad y componente, con receivers de email y Slack, agrupación e inhibiciones. Los parámetros temporales (group_wait, group_interval, repeat_interval) están alineados a mitigación de ruido, y se recomienda validar en producción. Falta la integración efectiva de Slack y webhook genérico (placeholders), y la formalización de escalaciones críticas, especialmente en horarios fuera de guardia y fines de semana. Las mejores prácticas incluyen rutas con `continue` cuando múltiples equipos deben participar, y estandarización de plantillas con enlaces a runbooks[^2][^6][^7][^17].

Tabla 14. Routes y receivers

| Route/Match                | Receiver         | Severidad/Componente | Tiempos (group_wait, repeat)        |
|---------------------------|------------------|----------------------|-------------------------------------|
| severity=critical         | critical-alerts  | critical             | 0s, 1h                              |
| severity=warning          | warning-alerts   | warning              | 30s, 4h                             |
| component=database        | database-team    | cualquier severidad | default                              |
| component=api             | api-team         | cualquier severidad | default                              |
| default                   | default-receiver | cualquier severidad | 10s, 4h                             |

Interpretación: la estructura de rutas prioriza críticos y segmenta por componente, útil para operación 24/7.

Tabla 15. Inhibition rules

| Fuente                               | Target                              | equal        |
|--------------------------------------|-------------------------------------|--------------|
| severity=critical, alertname=APIDown | severity=warning, component=api     | [instance]   |
| severity=critical, alertname=InstanceDown | severity=warning (cualquier alerta) | [instance]   |

Interpretación: inhibiciones reducen ruido al suprimir alertas secundarias cuando un evento crítico ocurre.

## Alertas gubernamentales críticas

Las alertas prioritarias cubren disponibilidad de API, error rate y latencias, PostGIS/PostgreSQL (conexiones, queries lentas, uso de disco), Redis (disponibilidad, memoria, evicciones), e Infraestructura (CPU, memoria, disco). Se proponen métricas de disponibilidad de efectivos en turnos y degradaciones de performance, además de reglas para incidentes de seguridad y violaciones de compliance. La instrumentación de métricas HTTP y la alineación de nombres de WebSocket con ggrt_* son prerequisitos para que estas alertas funcionen con datos reales[^6].

Tabla 16. Matriz de criticidad y respuesta

| Componente         | Alerta                      | Severidad | Respuesta requerida                         | Runbook                       |
|--------------------|-----------------------------|-----------|----------------------------------------------|-------------------------------|
| API                | APIDown                     | critical  | Escalar a on-call; rollback si necesario     | API-down                      |
| API                | HighErrorRate               | warning   | Analizar endpoints; verificar dependencias   | Error-rate                    |
| API                | CriticalLatencyP99          | critical  | Mitigar colas; escala; fallback              | Latency-critical              |
| PostgreSQL/PostGIS | PostgreSQLDown              | critical  | Failover/rehidratación; validar exporter     | DB-down                       |
| PostgreSQL/PostGIS | SlowQueries                 | warning   | Identificar queries; индексación            | Slow-queries                  |
| Redis              | RedisDown                   | critical  | Reinicio; validar exporter                   | Redis-down                    |
| Infraestructura    | DiskSpaceCritical           | critical  | Limpieza/escala; protección de datos         | Disk-critical                 |
| Seguridad          | AuthFailureSpike            | warning   | Revisar intentos; bloqueo; auditoría         | Security-incident             |
| Compliance         | AuditLogMissing             | critical  | Restaurar logging; investigar brecha         | Compliance-violation          |

Interpretación: la respuesta debe ser consistente y documentada en runbooks, enlazados desde las notificaciones.

## Security y compliance

La seguridad de Grafana debe incluir RBAC granular, cifrado de secretos de base de datos (con KMS o Vault), auditoría de la instancia y exportación de logs de uso. Se recomienda desactivar acceso anónimo, limitar permisos de consulta del rol Viewer, configurar whitelist para proxies de datasource y firewall rules, y operar detrás de proxy con CORS endurecido[^5]. Para compliance, se requieren políticas de retención, logging y acceso a métricas alineadas con marcos de referencia (ISO 27001, SOC 2, GDPR, y opciones FedRAMP para sector público). La retención extendida exige almacenamiento a largo plazo, y los controles de acceso deben limitar quién consulta y exporta datos.

Tabla 17. Matriz de controles de seguridad

| Control                           | Evidencia de configuración            | Riesgo mitigado                               |
|-----------------------------------|---------------------------------------|-----------------------------------------------|
| RBAC granular                     | Roles fijos y personalizados          | Acceso indebido a dashboards y datasource     |
| Cifrado de secretos               | Integración con KMS/Vault             | Exposición de credenciales                    |
| Auditoría de instancia            | Registro de eventos y export logs     | Falta de trazabilidad                         |
| Limitación de Viewer              | Restricción de consultas              | Filtración de datos por usuarios no autorizados|
| Proxy/firewall                    | Whitelist y reglas de firewall        | Acceso a servicios internos                   |
| CORS endurecido                   | Encabezados sin comodines             | Cross-origin mal configurado                  |

Interpretación: estos controles reducen superficie de ataque y alinean la operación con exigencias de cumplimiento.

Tabla 18. Políticas de retención y cumplimiento

| Tipo de dato        | Retención propuesta        | Marco de referencia                      |
|---------------------|----------------------------|------------------------------------------|
| Métricas operativas | 12–24 meses (objeto)       | ISO 27001, buenas prácticas              |
| Logs de auditoría   | 12–36 meses (según marco)  | SOC 2, GDPR                              |
| Alertas             | 12–24 meses                | Cumplimiento interno y trazabilidad      |

Interpretación: la retención debe equilibrar análisis histórico, coste y requisitos regulatorios.

## Performance y scalability

El rendimiento de Prometheus depende de la eficiencia de consultas PromQL, del volumen de series temporales (cardinalidad) y del diseño de almacenamiento. Las mejores prácticas incluyen: convenciones de nombres, evitar etiquetas de alta cardinalidad, usar contadores para tasas de error, delimitar selectores de etiquetas, y adoptar retención larga con Thanos/Cortex cuando sea necesario[^1][^8]. En Grafana, optimizar consultas y intervalación mejora tiempos de carga; caching de consultas frecuentes ayuda en dashboards con alta demanda.

Tabla 19. Guía de optimización de queries

| Patrón                          | Recomendación                                   | Impacto esperado                         |
|---------------------------------|-------------------------------------------------|-------------------------------------------|
| Cálculo de tasas                | Usar `rate()` en contadores                     | Alertas y paneles más estables            |
| Percentiles                     | Histogramas con buckets adecuados               | Latencias representativas                 |
| Selectores delimitados          | Etiquetas explícitas (servicio/componente)      | Menos colisiones de métricas              |
| Manejo de métricas faltantes    | Inicialización y uso de `or` en PromQL          | Consistencia en alertas                   |

Interpretación: estas prácticas previenen OOM y mejoran rendimiento y confiabilidad.

Tabla 20. Comparativa Thanos vs Cortex

| Solución | Ventajas                                 | Consideraciones de coste/operación                |
|----------|-------------------------------------------|---------------------------------------------------|
| Thanos   | Federación, deduplicación, object storage | Coste en almacenamiento; arquitectura distribuida |
| Cortex   | Blocks storage, sharding, HA              | Complejidad operativa; tuning de almacenamiento   |

Interpretación: la selección depende del modelo operativo y la necesidad de federación vs sharding.

### Planificación de capacidad

La planificación debe estimar series temporales por exporter, tasa de scrape, retención local vs remota y recursos (CPU, memoria, almacenamiento) del monitoring. Con crecimiento sostenido o alta cardinalidad, se recomienda sharding por dominio y federación. Thanos/Cortex añaden almacenamiento de objetos con coste por capacidad y egress, debiendo presupuestarse.

Tabla 21. Estimación de recursos

| Parámetro                         | Estimación base                    | Criterio de escalado                         |
|----------------------------------|------------------------------------|----------------------------------------------|
| Series por exporter              | 5k–50k (según dominio)             | Cardinalidad de etiquetas                     |
| Tasa de scrape                   | 15s global; 10s API                | Ajuste por criticidad                         |
| Retención local (Prometheus)     | 15–30 días                         | Transición a almacenamiento extendido         |
| Retención remota (objeto)        | 12–24 meses                        | Requisitos de compliance y análisis           |
| CPU/memoria                      | Vertical hasta umbral; luego sharding | Monitoreo de rendimiento y OOM               |
| Almacenamiento                   | Local + objeto                     | Costes y egress                               |

Interpretación: el dimensionamiento debe revisarse trimestralmente y ajustarse por tendencias.

## Operational procedures

La operación del stack requiere estrategias de backup y recuperación para métricas (snapshots y WAL en caso de uso de TSDB con componentes adicionales), procedimientos de mantenimiento y upgrades con ventanas coordinadas, guías de troubleshooting específicas por componente y calendario de guardia. La documentación de runbooks enlazados desde alertas acelera respuesta.

Tabla 22. Plan de mantenimiento

| Actividad                | Frecuencia | Responsable | Precauciones                            | Rollback                        |
|--------------------------|------------|-------------|------------------------------------------|---------------------------------|
| Actualización Prometheus | Trimestral | SRE/DevOps  | Backup config y reglas; ventana de bajo tráfico | Reversión a versión estable     |
| Actualización Grafana    | Trimestral | SRE/DevOps  | Backup dashboards; RBAC y datasource     | Reversión a versión estable     |
| Actualización Alertmanager | Trimestral | SRE/DevOps  | Backup rutas y templates                 | Reversión a versión estable     |
| Limpieza de retención    | Mensual    | SRE         | Validar políticas y costes               | Restaurar snapshots             |

Interpretación: la disciplina de mantenimiento evita degradaciones y facilita auditoría.

Tabla 23. Troubleshooting guides

| Síntoma                              | Causas probables                           | Pasos de diagnóstico                       | Herramientas                  |
|--------------------------------------|--------------------------------------------|--------------------------------------------|-------------------------------|
| Latencias elevadas en API            | Contención, colapso de dependencias        | Consultar percentiles; analizar endpoints  | Grafana, PromQL               |
| Alertas HTTP sin datos               | Métricas no expuestas                      | Validar instrumentación y scraping         | /metrics, prometheus.yml      |
| Alta evicción en Redis               | Memoria insuficiente; claves expiradas     | Revisar uso y evicciones                   | redis-exporter                |
| Panel lento                          | Queries ineficientes; alta cardinalidad    | Optimizar consultas; revisar etiquetas     | Grafana, PromQL               |

Interpretación: guías específicas estandarizan respuestas y reducen errores.

## Integración con Fly.io

La configuración de despliegue en Fly.io define health checks HTTP cada 15s en /health, puerto de métricas 9091 y estrategia rolling con auto_rollback. Las métricas del puerto 9091 permiten scraping dedicado. Se recomienda habilitar el Caddy exporter para observar el proxy (latencia y throughput HTTPS), y correlacionar métricas de plataforma con métricas de aplicación para diagnóstico end-to-end[^12][^13].

Tabla 24. Mapa de health checks y métricas

| Servicio     | Endpoint/Port                 | Intervalo | Finalidad                              | Relación con alertas           |
|--------------|-------------------------------|-----------|----------------------------------------|--------------------------------|
| API          | /health (HTTP), /metrics (9091)| 15s       | Disponibilidad y exposición de métricas| Fundamento para APIDown        |
| Proxy (Caddy)| Exporter 9180 (propuesto)     | 15s       | Latencia y tasa HTTPS                  | Alertas de proxy               |
| Prometheus   | 9090                          | 15s       | Evaluación y scraping                  | Evaluación de reglas           |
| Alertmanager | 9093                          | 15s       | Gestión de alertas                     | Rutas y receivers              |

Interpretación: el uso combinado de health checks y métricas favorece detección temprana y despliegue sin interrupciones.

### Correlación entre métricas de app e infraestructura

Las dependencias críticas (FastAPI ↔ PostGIS/Redis ↔ Caddy) deben reflejarse en alertas con inhibition para evitar ruido y guiar triage. Por ejemplo, alertas de latencia en API se inhiben si APIDown está activa. La correlación permite identificar cuellos de botella en el perímetro (proxy), en servicios de datos (DB/Redis) o en la aplicación, acelerando el diagnóstico.

Tabla 25. Matriz de correlación

| Componente     | Dependencia              | Señal primaria            | Señal secundaria                   | Acción recomendada                   |
|----------------|--------------------------|---------------------------|------------------------------------|--------------------------------------|
| API            | Caddy (proxy)            | Latencia API              | Latencia proxy (caddy_exporter)    | Mitigar proxy; revisar TLS/HTTP      |
| API            | PostgreSQL/PostGIS       | Error rate                | Conexiones DB/queries lentas       | Optimizar queries; índices           |
| WebSocket      | Redis (pub/sub)          | Errores de envío          | Evicciones memoria Redis            | Revisar capacidad; backpressure      |
| Infraestructura| Node (host)              | CPU/memoria               | Latencia de servicio               | Escala; ajuste de recursos           |

Interpretación: la correlación estructurada reduce hipótesis y tiempo de resolución.

## Recomendaciones y roadmap (0–30 / 30–60 / 60–90 días)

El plan se estructura para cerrar brechas críticas y fortalecer la operación 24/7:

- 0–30 días (estabilización):
  - Confirmar e instrumentar métricas HTTP necesarias (http_requests_total, histogramas de duración).
  - Alinear reglas WebSocket con métricas ggrt_* o exponer métricas con nombres referenciados.
  - Crear dashboards mínimos viables (API/WebSocket/Redis/PostgreSQL/Infraestructura).
  - Completar integración Slack y formalizar gestión de secretos (SMTP, Slack webhook, API keys).
  - Validar rutas y receivers de Alertmanager en producción; ejecutar pruebas de notificación.
- 30–60 días (optimización y ampliación):
  - Habilitar Caddy exporter y dashboard de proxy; incorporar alertas de latencia/tasa HTTPS.
  - Afinar umbrales con baselines por entorno/región; reducir falsos positivos.
  - Introducir circuit breakers y backpressure en Redis/WebSocket; pruebas de caos controladas.
  - Extender alertas para Telegram Bot (errores, latencia de notificaciones, colas).
- 60–90 días (observabilidad avanzada y resiliencia):
  - Definir SLOs/SLIs por dominio (API: disponibilidad 99.9%, P95 < 500ms; WebSocket: entrega < 250ms P95; PostGIS: queries < 200ms P95).
  - Consolidar dashboards ejecutivos y operativos; incluir métricas de cumplimiento y auditoría.
  - Automatizar runbooks y calendario de guardia; ejercicios de respuesta a incidentes.
  - Evaluar almacenamiento a largo plazo (Thanos/Cortex) y plan de federación/sharding si es necesario.

Tabla 26. Plan de acción priorizado

| Tarea                                                   | Horizonte | Dueño        | Dependencia                         | Métrica de éxito                                 |
|---------------------------------------------------------|-----------|--------------|-------------------------------------|--------------------------------------------------|
| Instrumentar métricas HTTP y validar scraping           | 0–30 días | Backend/API  | Ninguna                             | Alertas HTTP firing con datos                    |
| Alinear reglas WebSocket con métricas ggrt_*            | 0–30 días | Backend/API  | Métricas HTTP                       | Alertas WS basadas en datos reales               |
| Crear dashboards mínimos viables                        | 0–30 días | SRE/DevOps   | Métricas listas                     | Paneles operativos disponibles en Grafana        |
| Completar integración Slack y gestor de secretos        | 0–30 días | SRE/DevOps   | Acceso a Slack y gestor de secretos | Notificaciones críticas en Slack verificadas     |
| Habilitar Caddy exporter y dashboard proxy              | 30–60 días| SRE/DevOps   | Acceso a Caddy                      | Panel de proxy operativo y alertas               |
| Afinar umbrales y baselines                             | 30–60 días| SRE/DevOps   | Dashboards disponibles              | Reducción de falsos positivos/negativos          |
| Pruebas de caos y backpressure en Redis/WebSocket       | 30–60 días| SRE/QA       | Umbrales afinados                   | Recuperación sin incidentes mayores              |
| Telemetría del Bot (errores, colas, latencias)          | 30–60 días| Backend/Bot  | Instrumentación adicional           | Alertas y panel del Bot operativo                |
| Definir SLO/SLI y dashboards ejecutivos                 | 60–90 días| Arquitectura | Dashboards mínimos                  | SLOs documentados y aprobados                    |
| Automatizar runbooks y calendario de guardia            | 60–90 días| Operaciones  | SLO/SLI establecidos                | Ejercicios de incident response ejecutados       |

Interpretación: el roadmap prioriza confiabilidad y visualización mínima al inicio, luego amplía superficie observada y consolida prácticas avanzadas de gestión de servicio.

## Brechas de información (information_gaps)

- Detalle completo de las 23 reglas de alertas (20 revisadas).
- Confirmación de métricas HTTP instrumentadas en la API (http_requests_total, histogramas).
- Dashboards JSON de Grafana para validación de cobertura y rendimiento.
- Configuración final de Slack y webhooks (placeholders presentes).
- Gestor de secretos utilizado en producción y políticas de rotación.
- Habilitación y dashboards del Caddy exporter (comentado).
- Métricas específicas del bot de Telegram y su scraping.
- Requisitos regulatorios específicos (jurisdicción, marcos de cumplimiento).
- Política de retención y almacenamiento a largo plazo (Thanos/Cortex) en producción.
- Plan formal de escalado horizontal y federación.

## Referencias

[^1]: Prometheus Best Practices: 8 Dos and Don'ts — Better Stack. https://betterstack.com/community/guides/monitoring/prometheus-best-practices/
[^2]: Alertmanager | Prometheus. https://prometheus.io/docs/alerting/latest/alertmanager/
[^3]: Role-based access control (RBAC) — Grafana documentation. https://grafana.com/docs/grafana/latest/administration/roles-and-permissions/access-control/
[^4]: Security Compliance | Grafana Labs. https://grafana.com/legal/security-compliance/
[^5]: Configure security | Grafana documentation. https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/
[^6]: Configuration — Alertmanager (Prometheus). https://prometheus.io/docs/alerting/latest/configuration/
[^7]: Effective Alerting with Prometheus Alertmanager — Better Stack. https://betterstack.com/community/guides/monitoring/prometheus-alertmanager/
[^8]: Thanos — Highly available Prometheus setup with long term storage. https://thanos.io/
[^9]: Blocks Storage — Cortex Metrics. https://cortexmetrics.io/docs/blocks-storage/
[^10]: Concepts in service monitoring | Google Cloud Observability (SLO/SLI). https://docs.cloud.google.com/stackdriver/docs/solutions/slo-monitoring
[^11]: What is a Service Level Objective (SLO)? — IBM. https://www.ibm.com/think/topics/service-level-objective
[^12]: Health Checks · Fly Docs. https://fly.io/docs/reference/health-checks/
[^13]: Metrics on Fly.io · Fly Docs. https://fly.io/docs/monitoring/metrics/
[^14]: Prometheus vs Thanos: Key Differences & Best Practices — Last9. https://last9.io/blog/prometheus-vs-thanos/
[^15]: Scaling Prometheus: Handling Large-Scale Deployments — Medium. https://medium.com/@platform.engineers/scaling-prometheus-handling-large-scale-deployments-ec130e0b7ba8
[^16]: Scaling Prometheus: Tips, Tricks, and Proven Strategies — Last9. https://last9.io/blog/scaling-prometheus-tips-tricks-and-proven-strategies/
[^17]: Alert escalation and routing | Grafana Cloud documentation. https://grafana.com/docs/grafana-cloud/alerting-and-irm/irm/configure/escalation-routing/