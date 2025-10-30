# Blueprint de Métricas y Objetivos de Rendimiento para Sistemas Operativos/Tácticos Gubernamentales 24/7

## Resumen ejecutivo y objetivos de performance 24/7

En entornos gubernamentales de operación continua, la fiabilidad, la latencia predecible y la trazabilidad no son atributos deseables: son condiciones de misión. Este documento establece un marco integral de métricas, Service Level Indicators (SLI), Service Level Objectives (SLO), Key Performance Indicators (KPIs) y políticas operativas orientado a la operación 24/7 del sistema GRUPO_GAD, con foco en canales críticos (API, WebSocket, Telegram Bot), datos geoespaciales (PostGIS) y dependencias (Redis). Se apoya en la plataforma de observabilidad existente (Prometheus, Alertmanager y Grafana) y en la instrumentación actual de la aplicación con prefijo ggrt_, y se alinea con despliegues en producción sobre infraestructura gestionada[^1][^2][^6].

El propósito es doble. Primero, definir objetivos explícitos, medibles y auditables para uptime, latencia, throughput, notificación y recuperación (RTO/RPO) que guíen la operación táctica y la mejora continua. Segundo, diseñar la gobernanza de métricas, la cobertura de instrumentación y el sistema de alertas para sostener dichos objetivos en un contexto de alta disponibilidad, con evidencia suficiente para auditorías y toma de decisiones basada en datos.

Se proponen objetivos operativos exigentes, consistentes con cargas gubernamentales críticas:
- Disponibilidad de servicios críticos: hasta 99.99% por dominio, con medición consolidada mensual.
- Latencia de operaciones críticas: p95 <200 ms en API y canales de tiempo real; consultas PostGIS con p95 <500 ms; comandos de Telegram respondidos en <2 s.
- Throughput agregado: ≥100 operaciones/segundo (con meta de 200 a 3–6 meses), con visibilidad de p50/p95/p99 por endpoint.
- Notificaciones operativas: entrega en <5 s (p95) y tasa de éxito >99% (con SLO >99.9% a 60–90 días).
- Recuperación: RTO <15 minutos; RPO <1 minuto (donde aplique y con soporte de streams si se requiere retención/replay).

El sistema de observabilidad actual proporciona los cimientos para esta ambición. Existe instrumentación personalizada de WebSockets (ggrt_*), scraping de exporters clave (PostgreSQL, Redis, Node, Alertmanager) y un conjunto de 20 reglas de alerta clasificadas por dominio. Se han identificado brechas relevantes (métricas HTTP de API no confirmadas, ausencia del exporter de Caddy, dashboards no versionados, placeholders en Slack) que se abordan en el roadmap propuesto, con acciones de estabilización (0–30 días), optimización (30–60 días) y resiliencia avanzada (60–90 días)[^6].

La Figura 1 ofrece un mapa de componentes críticos y superficies de medición que enmarcan el diseño de SLIs/SLOs, destacando los dominios de API, WebSocket, Bot, PostGIS y Redis, y los flujos de métricas hacia Prometheus/Grafana.

![Mapa de componentes críticos y superficies de medición (API, WS, Bot, PostGIS, Redis).](assets/diagrams/mapa_metricas_criticas.png)

Este blueprint aborda explícitamente las preguntas clave de misión: objetivos por dominio y su definición cuantitativa; SLIs/SLOs/KPIs y su gobierno; medición de resiliencia (RTO/RPO y efectividad de circuit breakers); métricas de experiencia operativa y experiencia de usuario; instrumentación necesaria para cubrir cada KPI; umbrales de alertas alineados a SLOs; capacidad para picos (≥1,000 usuarios y ≥50 operaciones concurrentes); y estrategias de benchmarking interno y externo para una operación 24/7 madura[^1][^2][^6].


## Marco conceptual y definiciones (SLI, SLO, KPI)

- Service Level Indicator (SLI): medida observable de comportamiento de un servicio (p. ej., latencia p95 de un endpoint, tasa de error, disponibilidad). Se define por dominio, con ventana temporal explícita y percentiles relevantes.
- Service Level Objective (SLO): valor objetivo que debe cumplir el SLI (p. ej., p95 <200 ms en API; disponibilidad 99.99% mensual). Los SLOs se asocian a dominios (API, WebSocket, PostGIS, Bot, Redis, proxy) y a “golden signals” (latencia, tráfico, errores, saturación)[^6].
- Key Performance Indicator (KPI): medida de resultado operativo, de negocio o de experiencia (p. ej., assignments exitosos, delivery rate de notificaciones). Pueden medirse con SLIs relacionados, pero su propósito es ejecutivo y de misión, no solo técnico.
- Disponibilidad: porcentaje de tiempo en que un servicio está operativo en una ventana (mensual). La continuidad del servicio 24/7 exige medición rigurosa con reglas de alerta y umbrales alineados a SLOs[^6].
- Latencia: distribución temporal de respuesta; se recomienda medir p50, p95 y p99 por operación crítica, conhistogramas para granularidad y alertas por percentiles.
- Throughput: volumen de operaciones por unidad de tiempo (req/s o ops/s), medido por endpoint/dominio y consolidado por clúster/región.
- Saturación: grado de uso de recursos (CPU, memoria, descriptores, pools), indicador temprano de riesgo de performance y disponibilidad.
- Resiliencia: RTO (Recovery Time Objective) y RPO (Recovery Point Objective); efectividad de circuit breakers, backpressure y degradación graceful.

Este marco se alinea con los “golden signals” y con el sistema de reglas y alertas de Prometheus/Alertmanager, favoreciendo una operación coherente, auditable y accionable[^6].


## Inventario de instrumentación existente y brechas

La plataforma actual cuenta con instrumentación y observabilidad de base:
- Métricas personalizadas con prefijo ggrt_ para WebSocket: conexiones activas, totales, mensajes, broadcasts, errores de envío, heartbeat, latencia de mensajes, usuarios activos y conexiones por rol.
- Jobs de scraping: API (10s), Prometheus, PostgreSQL, Redis, Node Exporter y Alertmanager (15s). Job de Caddy comentado (ausente).
- Reglas de alerta: 20 reglas clasificadas por dominios API, DB, Redis, Infraestructura y WebSocket, con severidades y tiempos de evaluación.
- Alertmanager: rutas por severidad/componente, agrupación e inhibiciones. Integración Slack con placeholders.

Brechas principales:
- Métricas HTTP en API no confirmadas (http_requests_total y histogramas de latencia), que alimentan reglas de error rate y latencias P95/P99.
- Ausencia de Caddy exporter y su panel.
- Dashboards de Grafana no disponibles (sin JSON versionados).
- Placeholders en Slack y secretos sin gestor formal.
- Telemetría del bot de Telegram no instrumentada (latencias, colas, errores).

Impacto: las brechas limitan la fiabilidad de alertas (especialmente API) y el triage rápido; además, impiden establecer baselines por entorno y ajustar umbrales dinámicamente. El plan de remediación se integra en el roadmap 0–30/30–60/90 días[^6].

Tabla 1. Mapa de scraping targets y puertos (API, Postgres, Redis, Node, Alertmanager, Caddy)

| job         | objetivo                  | intervalo | etiquetas                           | comentarios                         |
|-------------|---------------------------|-----------|--------------------------------------|-------------------------------------|
| prometheus  | localhost:9090            | 15s       | service=prometheus                   | Self-monitoring                     |
| api         | api:8000/metrics          | 10s       | service=fastapi, component=api       | Métricas ggrt_* y posiblemente HTTP |
| postgres    | postgres-exporter:9187    | 15s       | service=postgresql, component=database | Métricas de DB                   |
| redis       | redis-exporter:9121       | 15s       | service=redis, component=cache       | Memoria y evicciones                |
| node        | node-exporter:9100        | 15s       | service=node-exporter, component=infrastructure | Host metrics           |
| alertmanager| alertmanager:9093         | 15s       | service=alertmanager, component=alerting | Estado de Alertmanager        |
| caddy       | (comentado)               | 15s       | service=caddy, component=reverse-proxy | Exportador ausente              |

Tabla 2. Inventario de métricas ggrt_* (WebSocket) y propósito

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


## SLOs operativos por dominio

Los SLOs se definen por dominio, con SLI asociados y medición continua a través de Prometheus. Las ventanas de evaluación se fijan en 5 minutos para señales rápidas (p95/p99, tasas de error) y consolidación mensual para disponibilidad. Se emplea error budget para gestionar el riesgo y la priorización de mejoras: el presupuesto de error se define como 1 − SLO y se controla por dominio, con bloqueos operativos si se agota.

- API HTTP: disponibilidad 99.99% (consolidado mensual); p95 <200 ms, p99 <500 ms; error rate <1% (rolling 5 m); throughput ≥100 ops/s (meta 150–200 en 3–6 meses).
- WebSocket: entrega de mensajes con p95 <200 ms end-to-end; disponibilidad 99.99%; errores de envío ≤0.1% de envíos.
- Telegram Bot: respuesta de comandos en <2 s (p95); éxito de entrega ≥99%.
- PostGIS: queries críticas (nearest neighbors y geofencing) con p95 <500 ms, p99 <1000 ms; disponibilidad 99.95%.
- Redis: ops/s >10,000; disponibilidad 99.99%; latencia de operaciones get/set p95 <50 ms.
- Proxy reverso (Caddy, una vez habilitado): latencia p95 <100 ms; disponibilidad 99.99%.

Tabla 3. SLOs por dominio (API, WS, Bot, PostGIS, Redis, Proxy)

| Dominio         | SLO disponibilidad | SLO latencia                  | SLO throughput              | SLO notificaciones          | Error budget (mensual) |
|-----------------|--------------------|-------------------------------|-----------------------------|-----------------------------|------------------------|
| API HTTP        | 99.99%             | p95 <200 ms, p99 <500 ms      | ≥100 ops/s (meta 150–200)   | N/A                         | 0.01%                  |
| WebSocket       | 99.99%             | p95 <200 ms (E2E)             | N/A                         | Entrega p95 <5 s, ≥99%      | 0.01%                  |
| Telegram Bot    | 99.9%              | p95 <2 s                      | N/A                         | ≥99% entrega                | 0.1%                   |
| PostGIS         | 99.95%             | p95 <500 ms, p99 <1000 ms     | N/A                         | N/A                         | 0.05%                  |
| Redis           | 99.99%             | get/set p95 <50 ms            | >10,000 ops/s               | N/A                         | 0.01%                  |
| Proxy (Caddy)   | 99.99%             | p95 <100 ms                   | N/A                         | N/A                         | 0.01%                  |

Tabla 4. Matriz SLO → SLI → fuente métrica → regla de alerta → dashboard

| SLO                         | SLI                          | Fuente métrica                               | Regla de alerta (ejemplos)                                 | Dashboard clave                 |
|----------------------------|------------------------------|----------------------------------------------|-------------------------------------------------------------|---------------------------------|
| API p95 <200 ms            | p95 latencia por endpoint    | http_request_duration_seconds (histograma)   | HighLatencyP95, CriticalLatencyP99                          | API Latency/Throughput/Error   |
| API disponibilidad 99.99%  | up{job="api"}                | API target scrappeado                        | APIDown                                                   | API Health                     |
| WS E2E p95 <200 ms         | ggrt_message_latency_seconds | ggrt_* (histograma)                          | HighWebSocketLatency (nueva), HighWebSocketBroadcastErrors | WS Latencia/Errores/Broadcast  |
| Bot <2 s (p95)             | bot_response_latency         | Métricas bot (nueva)                         | HighBotLatency (nueva), BotDown (nueva)                    | Bot Latencia/Colas/Errores     |
| PostGIS p95 <500 ms        | query_duration_seconds       | Métricas DB/PostGIS (nueva)                  | SlowQueries, PostgreSQLDown                                | PostGIS Performance            |
| Redis >10K ops/s           | redis_connected_clients, ... | redis_exporter                               | RedisDown, RedisHighEvictionRate                           | Redis Health/Throughput        |
| Proxy p95 <100 ms          | proxy_latency_seconds        | caddy_exporter (nueva)                       | HighProxyLatency (nueva), ProxyDown (nueva)                | Proxy Latency/Throughput       |

Diseño de alertas: umbrales se fijan contra los SLOs (p. ej., HighLatencyP95 si p95 > 0.5 s durante 5 m), con severidad crítica para violaciones de SLO y agrupamiento/inhibiciones para reducir ruido (Alertmanager). Ventanas de evaluación cortas evitan impacto acumulado; repeat_interval se ajusta a severidad crítica para asegurar continuidad de notificación[^6].

![Cadena de dependencias y puntos de medición para SLOs por dominio.](assets/diagrams/slo_stack.png)


## KPIs gubernamentales

Los KPIs traducen la promesa operativa en resultados de misión y experiencia, con definiciones, fórmulas y periodicidad claras. Los KPIs operativos se calculan con SLIs relacionados; los KPIs de experiencia se obtienen de encuestas periódicas y telemetría de interacción.

Tabla 5. Catálogo de KPIs (definición, fórmula, fuente, periodicidad, propietario)

| KPI                            | Definición                                           | Fórmula                                         | Fuente de datos                     | Periodicidad | Propietario    |
|--------------------------------|------------------------------------------------------|-------------------------------------------------|-------------------------------------|-------------|----------------|
| Efectividad operativa          | Asignaciones de efectivos completadas con éxito     | assignments_exitosos / assignments_totales     | Métricas de aplicación (nuevas)     | Diario      | Operaciones    |
| Disponibilidad de efectivos    | % de activos activos disponibles                     | efectivos_activos / efectivos_registrados      | Métricas de estado de activos       | Diario      | Operaciones    |
| Eficiencia de notificaciones   | Tasa de entrega de mensajes                          | entregas_exitosas / intentos                    | Métricas Bot/WS (nuevas)            | Diario      | SRE/DevOps     |
| Precisión de geolocalización   | Error medio de ubicación                             | mean( |error_geol|)                              | Métricas PostGIS y GPS (nuevas)      | Semanal      | Backend/DB     |
| Satisfacción de usuarios       | Índice de satisfacción (operativos + comandantes)   | score encuesta (1–5) ponderado                 | Encuestas y telemetría UI           | Mensual     | Producto       |

Tabla 6. Cuadro de mando ejecutivo (visión consolidada)

| Dominio         | KPI principal                       | Estado actual | Tendencia | Riesgo |
|-----------------|-------------------------------------|---------------|-----------|--------|
| API             | Efectividad operativa               | Por definir   | N/A       | Medio  |
| WebSocket       | Eficiencia de notificaciones        | Parcial       | Estable   | Medio  |
| Bot             | Latencia de comandos                | Brecha        | N/A       | Alto   |
| PostGIS         | Precisión de geolocalización        | Parcial       | Estable   | Medio  |
| Usuarios        | Satisfacción                        | Brecha        | N/A       | Medio  |

Las métricas de notificación se relacionan con la semántica de entrega de Pub/Sub de Redis: al ser “at-most-once”, se requieren mecanismos de ACK y replay (p. ej., Streams) para alcanzar tasas de éxito superiores al 99% en canales críticos[^14][^15].


## Métricas de capacity planning

El dimensionamiento asegura que el sistema sostenga picos y crecimiento. Se definen metas y métodos de medición por componente (API, WebSocket, Redis, PostGIS, proxy), con sizing inicial a partir de límites operativos y pruebas controladas.

- Usuarios concurrentes: objetivo ≥1,000 (por entorno/región).
- Operaciones concurrentes: objetivo ≥50 simultáneas en picos operativos.
- Crecimiento de datos: tasa mensual, uso de almacenamiento y proyecciones por tabla/índice.
- Throughput de mensajes: capacidad de broadcast por canal, con métricas de reconexión y drop.
- Cobertura geográfica: área y regiones atendidas, latencia por región.

Tabla 7. Capacity sizing por componente (API, WS, Redis, DB, Proxy)

| Componente     | Parámetro clave                | Objetivo inicial           | Observaciones                                        |
|----------------|--------------------------------|----------------------------|------------------------------------------------------|
| API            | RPS sostenido                  | ≥100 (meta 150–200)        | Rate limiting y backpressure coordinados             |
| WebSocket      | Conexiones activas             | ≥1,000                     | Descriptores/ulimit y memoria por conexión           |
| Redis          | Ops/s                          | >10,000                    | Sharding/namespacing para fan‑out                    |
| PostGIS        | Queries concurrentes           | ≥50                        | Índices espaciales y timeouts                        |
| Proxy          | p95 latencia                   | <100 ms                    | Habilitar Caddy exporter                             |

Tabla 8. Plan de crecimiento trimestral y señales de alarma

| Trimestre | Usuarios concurrentes | Ops/s sostenido | Almacenamiento | Señales de alarma                    |
|-----------|------------------------|-----------------|----------------|--------------------------------------|
| T+1       | 1,000                  | 100             | +X GB          | p95 cerca del SLO, colas en crecimiento |
| T+2       | 1,500                  | 150             | +Y GB          | Evictions Redis, hot instances        |
| T+3       | 2,000                  | 200             | +Z GB          | Descriptores cercanos a ulimit        |

Tabla 9. Mapa de cobertura geográfica y latencias esperadas

| Región        | % tráfico | p95 latencia esperada | Notas                          |
|---------------|-----------|------------------------|--------------------------------|
| LatAm Primary | 70%       | <200 ms (API)          | Región primaria                |
| LatAm Sec     | 20%       | <300 ms (API)          | Considerar multi‑región        |
| Otros         | 10%       | <500 ms (API)          | WAF/CDN, edge caching          |

Pruebas de carga deben simular escenarios de 10k, 20k y 50k conexiones WebSocket, con instrumentación de reconexiones y colas, para validar límites de descriptores y memoria por instancia[^11][^18]. Métricas de infraestructura (Node Exporter) y exporters (Redis/PostgreSQL) guían la observabilidad de capacidad[^6].


## Métricas de resiliencia operativa

La resiliencia se mide por la capacidad de sostener la operación ante fallos y eventos extremos. Además de RTO/RPO, se monitoriza el desempeño de circuit breakers, backpressure, degrade graceful y mecanismos de reconexión.

- Failover/RTO: objetivo <15 minutos, medido en ejercicios y eventos reales.
- Tolerancia a pérdida de datos/RPO: objetivo <1 minuto; se recomienda Redis Streams para canales que requieran retención/replay (más allá de la semántica at‑most‑once de Pub/Sub)[^14][^16].
- Éxito de DR: objetivo ≥95% en pruebas periódicas.
- Efectividad de circuit breaker: tasa de apertura correcta, tiempo medio de recuperación y reducción de errores en cascada.
- Degradación controlada: mantenerse en funcionalidad mínima con latencia aceptable (p95) y pérdida acotada de features.

Tabla 10. Resiliencia por componente (RTO, RPO, DR, mecanismo)

| Componente   | RTO objetivo | RPO objetivo | Éxito DR (%) | Mecanismos clave                        |
|--------------|--------------|--------------|--------------|------------------------------------------|
| API          | <15 m        | <1 m         | ≥95          | Rolling deploy, health checks, CB        |
| WebSocket    | <15 m        | N/A          | ≥95          | Reconexión escalonada, backpressure      |
| Bot          | <15 m        | <1 m         | ≥95          | Retries, colas, Streams                  |
| PostGIS      | <15 m        | <1 m         | ≥95          | Replicación, backups, tuning             |
| Redis        | <15 m        | <1 m         | ≥95          | Sentinel, sharding, Streams              |
| Proxy        | <15 m        | N/A          | ≥95          | Failover upstream, exporter/alertas      |

Tabla 11. Matriz de degradación controlada y métricas

| Feature              | Umbral de degrade         | Métrica                  | SLO degrade         |
|----------------------|---------------------------|--------------------------|---------------------|
| Broadcast masivo     | Drop <1%, lat p95 <500 ms | drop_rate, p95 latencia  | Notificar en <5 s   |
| Notificaciones Bot   | Retries con backoff       | bot_retries_total        | Éxito ≥99%          |
| Consultas PostGIS    | Timeout y paginación      | slow_queries             | p95 <500 ms         |

Tabla 12. Eficacia de circuit breakers (por dependencia)

| Dependencia | Tasa apertura | Tiempo recovery | Errores evitados | Comentarios                     |
|-------------|---------------|-----------------|------------------|----------------------------------|
| DB          | Por definir   | Por definir     | Por definir      | Requiere instrumentación         |
| Redis       | Por definir   | Por definir     | Por definir      | Critical en fan‑out              |
| Bot         | Por definir   | Por definir     | Por definir      | Coordina con colas               |

La semántica de Pub/Sub exige cautela: al no garantizar retención, los flujos críticos deben evolucionar a Streams para cumplir RPO y tasas de entrega superiores[^14][^15].


## Métricas de experiencia operativa y UX

La percepción del usuario final se mide por tiempos de respuesta y estabilidad. Se recomiendan histogramas por endpoint y canal, con percentiles p50/p95/p99 y mediciones end-to-end.

- Tiempo de respuesta de comandos (UI/API/Bot): p95 <2 s para Bot; p95 <200 ms para API de comandos.
- Responsividad de UI: latencia p95 de render/interacción; tasa de timeouts de sesión.
- Velocidad de entrega de notificaciones: p95 <5 s; éxito ≥99%.
- Performance de consultas geoespaciales: p95 <500 ms; p99 <1000 ms.
- Confirmación de comandos: tiempo de ACK y reintentos.

Tabla 13. Métricas de experiencia (definición, objetivo, origen)

| Métrica                   | Objetivo       | Origen                         |
|---------------------------|----------------|--------------------------------|
| Bot response p95          | <2 s           | Métricas Bot (nuevas)          |
| API comando p95           | <200 ms        | Histogramas HTTP               |
| UI render p95             | <200 ms        | Telemetría frontend (nueva)    |
| Notificación p95          | <5 s           | Métricas Bot/WS                |
| PostGIS query p95         | <500 ms        | Métricas DB/PostGIS            |
| Comando confirmación p95  | <300 ms        | Métricas aplicación            |

Tabla 14. Mapa de journey de usuario (comandos/notificaciones) y SLIs

| Journey             | Paso clave           | SLI principal          |
|---------------------|----------------------|------------------------|
| Comando Bot         | Recepción → respuesta| bot_response_latency   |
| Notificación WS     | Publicación → entrega| message_latency_e2e    |
| Consulta geoespacial| Request → datos      | query_duration_seconds |
| Confirmación        | ACK local → servidor | command_ack_latency    |

Los heartbeats y pings/pongs en WebSockets se integran como señal de estabilidad y limpieza de “zombies”, afectando directamente la experiencia percibida[^20].


## Métricas de performance de integraciones

Las integraciones determinan la latencia y confiabilidad del sistema. Se establecen umbrales por integración y se instrumentan métricas de latencia, tasa de error y throughput.

- Telegram Bot: p95 respuesta <2 s; tasa de error <1%; éxito de entrega ≥99% (con ACKs y reintentos).
- PostGIS: p95 queries <500 ms; p99 <1000 ms; métricas de slow queries y locks.
- Redis: throughput >10,000 ops/s; latencia de get/set p95 <50 ms; hit rate de cache >90%.
- WebSocket: estabilidad de conexiones (reconexiones, send_errors, colas por cliente).
- Prometheus: confiabilidad de scraping (targets up, latencia de scrape).

Tabla 15. Catálogo de integraciones y métricas (umbral, SLI, regla)

| Integración  | Umbral                   | SLI                           | Regla de alerta (ejemplo)      |
|--------------|--------------------------|-------------------------------|---------------------------------|
| Bot          | p95 <2 s, error <1%      | bot_response_latency          | HighBotLatency, BotDown         |
| PostGIS      | p95 <500 ms              | query_duration_seconds        | SlowQueries, PostgreSQLDown     |
| Redis        | >10K ops/s, p95 <50 ms   | redis_connected_clients, ...  | RedisDown, RedisHighEvictionRate|
| WebSocket    | p95 <200 ms, send_errors | ggrt_message_latency_seconds  | HighWebSocketLatency, BroadcastErrors |
| Prometheus   | Targets up = 100%        | up{job=...}                   | TargetDown                      |

Tabla 16. Alertas por integración (umbral, severidad, canal)

| Alerta                  | Umbral                      | Severidad | Canal         |
|-------------------------|-----------------------------|-----------|---------------|
| HighBotLatency          | p95 >2 s (5 m)              | Warning   | Slack         |
| BotDown                 | up{job="bot"} == 0 (1 m)    | Critical  | Email + Slack |
| SlowQueries             | duración >1 s               | Warning   | Slack         |
| RedisDown               | up{job="redis"} == 0 (1 m)  | Critical  | Email + Slack |
| HighWebSocketLatency    | p95 >200 ms (5 m)           | Warning   | Slack         |

![Topología de integraciones y puntos de medición.](assets/diagrams/integrations_topologia.png)

Redis Pub/Sub se utiliza para broadcasting y coordinación cross‑worker; su semántica at‑most‑once se debe considerar al diseñar garantías de entrega en canales críticos[^14][^13].


## Métricas de cost effectiveness

La eficiencia se mide en términos de costo por operación y utilización de recursos, con objetivos claros y señales para optimización.

- Costo por operación: $/operación (objetivo decreciente).
- Utilización de recursos: >80% en promedio; saturación controlada (CPU/memoria/descriptores).
- Optimización de infraestructura: reducción de costos sin degradar SLOs.
- Ahorro operativo: automatización, runbooks, reducción de MTTR.
- ROI de inversiones tecnológicas: impacto en SLOs/KPIs y costos.

Tabla 17. Costo por operación y por dominio

| Dominio   | Costo/op (actual) | Costo/op (objetivo) | Comentarios                        |
|-----------|--------------------|---------------------|------------------------------------|
| API       | Por definir        | -20%                | Rate limiting + tuning             |
| WS        | Por definir        | -15%                | Backpressure + payload binario     |
| Bot       | Por definir        | -10%                | Retries optimizados                |
| PostGIS   | Por definir        | -15%                | Índices + paginación               |
| Redis     | Por definir        | -10%                | Sharding + hit rate                |

Tabla 18. Utilización de recursos y señales de optimización

| Recurso         | Utilización | Señal           | Acción sugerida                     |
|-----------------|-------------|-----------------|-------------------------------------|
| CPU             | >80%        | node_cpu        | Escalado, tuning loops              |
| Memoria         | >85%        | node_memory     | Backpressure, límites de payload    |
| Descriptores    | >80% ulimit | process_fds     | Aumentar ulimit, optimizar fd       |
| Redis ops       | >80% cap    | redis_exporter  | Sharding/namespacing                |

Tabla 19. ROI de inversiones (iniciativa → ahorro → impacto en SLOs)

| Iniciativa                   | Ahorro estimado | Impacto SLO                 |
|-----------------------------|-----------------|-----------------------------|
| Backpressure WS             | Bajo            | p95 estable, menos drops    |
| Caddy exporter              | Bajo            | Latencia proxy bajo control |
| Streams para críticas       | Medio           | Éxito entrega >99%          |
| Circuit breakers            | Medio           | Errores en cascada reducidos|


## Benchmarking y comparación

El benchmarking combina comparaciones externas (best‑in‑class) con tendencias históricas internas y pruebas controladas. El objetivo es sostener y mejorar SLOs bajo cambios de arquitectura, despliegues y picos estacionales.

- Comparación con mejores prácticas del sector público y sistemas en producción.
- Análisis relativo frente a competidores o alternativas tecnológicas.
- Tendencias históricas: latencias, throughput, disponibilidad y error budgets.
- Seguimiento de mejora con línea base por dominio.
- Establecimiento de baselines por entorno y región.

Tabla 20. Cuadro de benchmarking por dominio

| Dominio   | Línea base | Objetivo | Gap | Acción                             |
|-----------|------------|----------|-----|------------------------------------|
| API       | p95 200 ms | p95 150 ms | 50 ms | Cache dirigido + pools           |
| WS        | p95 200 ms | p95 150 ms | 50 ms | Backpressure + payload binario    |
| Bot       | p95 2 s    | p95 1.5 s | 0.5 s | Retries + colas                   |
| PostGIS   | p95 500 ms | p95 400 ms | 100 ms | Índices + paginación             |

Tabla 21. Evolución histórica y proyección (trimestral)

| Métrica     | T-1 | T0  | T+1 | T+2 | Proyección |
|-------------|-----|-----|-----|-----|------------|
| p95 API     | 220 | 200 | 180 | 160 | Tendencia descendente |
| Disponibilidad | 99.9 | 99.95 | 99.99 | 99.99 | Estabilizar |
| Throughput  | 90  | 100 | 120 | 150 | Crecimiento controlado |

La validación de mejoras debe ejecutarse mediante pruebas de carga y caos integradas a CI/CD, con observabilidad completa y alertas configuradas[^6].


## Gobernanza de métricas y calidad de datos

La calidad de la medición es el pilar de la operación 24/7. Se establecen estándares de etiquetado, cobertura mínima por componente y validación de fuentes, con gestión de secretos y alineación de reglas.

- Etiquetado consistente: evitar cardinalidad excesiva (labels como env, role).
- Cobertura mínima: exporters habilitados (Caddy incluido), endpoints /metrics operativos, jobs de scraping verificados.
- Gestión de secretos: SMTP y Slack webhook con gestor de secretos y rotación periódica.
- Versionado de dashboards JSON en repositorio para trazabilidad.
- Alineación de reglas con métricas expuestas (HTTP y WebSocket).

Tabla 22. Estándares de etiquetado por métrica (labels permitidos)

| Métrica                 | Labels permitidos | Comentario                         |
|-------------------------|-------------------|------------------------------------|
| ggrt_active_connections | [env]             | Evitar cardinalidad excesiva       |
| ggrt_role_connections   | [env, role]       | Rol necesario                      |
| http_request_duration   | [env, endpoint]   | No usar user/session               |
| redis_*                 | [env, instance]   | Instancia y entorno                |
| pg_*                    | [env, db]         | Base de datos                      |

Tabla 23. Checklist de calidad de datos

| Criterio               | Estado | Evidencia                     |
|------------------------|--------|-------------------------------|
| Fuentes confirmadas    | Parcial| HTTP métricas no confirmadas  |
| Cardinalidad controlada| OK     | Labels restringidos           |
| Scraping válido        | OK     | Jobs definidos                |
| Alertas alineadas      | Parcial| Reglas WS/HTTP sin fuente     |
| Dashboards versionados | Brecha | JSON no disponibles           |
| Secretos gestionados   | Brecha | Placeholders en Slack         |

La gobernanza se apoya en Prometheus/Alertmanager para reglas y alertas, y en repositorios versionados para configurar dashboards y reglas con trazabilidad[^6][^1].


## Roadmap de implementación y priorización

El plan de mejora se organiza en tres horizontes con entregables claros y KPIs de éxito. La priorización se orienta a cerrar brechas críticas, mejorar resiliencia y optimizar costos.

- 0–30 días (estabilización): instrumentar métricas HTTP y corregir reglas; alinear nombres de métricas WebSocket con alertas; crear dashboards mínimos viables; completar integración Slack y definir gestor de secretos; validar rutas/receivers en producción.
- 30–60 días (optimización y ampliación): habilitar Caddy exporter; afinar umbrales con baselines; introducir circuit breakers y backpressure en Redis/WS; pruebas de caos controladas; extender alertas del bot.
- 60–90 días (observabilidad avanzada y resiliencia): definir SLO/SLI por dominio; consolidar dashboards ejecutivos; automatizar runbooks y calendario de guardia; evaluar remote write para retención extendida.

Tabla 24. Plan por fases (tarea, horizonte, dueño, dependencia, métrica de éxito)

| Tarea                                           | Horizonte | Dueño        | Dependencia                         | Métrica de éxito                                 |
|-------------------------------------------------|-----------|--------------|-------------------------------------|--------------------------------------------------|
| Instrumentar métricas HTTP                      | 0–30 días | Backend/API  | Ninguna                             | Alertas de latencia/errores firing con datos     |
| Alinear reglas WebSocket                        | 0–30 días | Backend/API  | Métricas HTTP                       | Alertas WS basadas en datos reales               |
| Dashboards mínimos viables                      | 0–30 días | SRE/DevOps   | Métricas listas                     | Paneles operativos disponibles                   |
| Integración Slack + gestor de secretos          | 0–30 días | SRE/DevOps   | Acceso a Slack y gestor             | Notificaciones críticas verificadas              |
| Habilitar Caddy exporter                        | 30–60 días| SRE/DevOps   | Acceso a Caddy                      | Panel proxy operativo + alertas de latencia      |
| Afinar umbrales y baselines                     | 30–60 días| SRE/DevOps   | Dashboards disponibles              | Reducción de falsos positivos/negativos          |
| Circuit breakers + backpressure                 | 30–60 días| SRE/QA       | Umbrales afinados                   | Recuperación sin incidentes mayores              |
| Telemetría del Bot                              | 30–60 días| Backend/Bot  | Instrumentación adicional           | Alertas y panel del Bot operativo                |
| SLO/SLI y dashboards ejecutivos                 | 60–90 días| Arquitectura | Dashboards mínimos                  | SLOs documentados y aprobados                    |
| Automatizar runbooks y guardia                  | 60–90 días| Operaciones  | SLO/SLI establecidos                | Ejercicios de incident response ejecutados       |

Este roadmap es coherente con prácticas de despliegue en producción y con el sistema de reglas y alertas, favoreciendo una evolución controlada con validación continua[^1][^2][^6].


## Brechas de información (information_gaps)

- Confirmación de métricas HTTP (http_requests_total e histogramas de latencia) en la API.
- Dashboards JSON de Grafana para validación.
- Detalle de las 23 reglas de alerta (20 revisadas; 3 pendientes de detalle).
- Estado del Caddy exporter y dashboard del proxy.
- Configuración final de Slack y gestión de secretos (placeholder).
- Telemetría del bot de Telegram (latencias, colas, errores).
- Topología de Redis (managed vs autogestionado, Cluster/Sentinel, región).
- Pruebas de carga y capacidad máxima por worker (10k/20k/50k conexiones).
- Parámetros de balanceo (sticky sessions, algoritmo, timeouts) y autoscaling en Fly.io.
- Límites de OS (ulimit, descriptores) y tamaños de payload.
- Políticas de seguridad (TLS, JWT, reautenticación y renovación) para sockets y API.
- Línea base histórica consolidada de latencias p50/p95/p99, throughput y error rate.
- Casos de uso de broadcasting masivo y segmentación ciudadana para SLOs de notificación.

Estas brechas se incorporan en el plan de acción y condicionan la precisión de umbrales y objetivos, especialmente para KPIs de misión (satisfacción, precisión de geolocalización) y SLOs de notificaciones. La remediación debe priorizar métricas y dashboards mínimos viables, seguido de instrumentación avanzada de integraciones y ejercicios de DR.


## Referencias

[^1]: GRUPO_GAD - Repositorio (Inventario y configuraciones). https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD - Entorno de producción en Fly.io. https://grupo-gad.fly.dev  
[^3]: README del proyecto GRUPO_GAD. https://github.com/eevans-d/GRUPO_GAD/blob/master/README.md  
[^4]: Configuración de Fly.io - GRUPO_GAD. https://github.com/eevans-d/GRUPO_GAD/blob/master/fly.toml  
[^5]: How to Scale FastAPI WebSocket Servers Without Losing State. https://hexshift.medium.com/how-to-scale-fastapi-websocket-servers-without-losing-state-6462b43c638c  
[^6]: Prometheus - Documentación oficial. https://prometheus.io/docs/introduction/overview/  
[^10]: Redis Pub/Sub - Documentación oficial. https://redis.io/docs/latest/develop/pubsub/  
[^11]: Scaling Pub/Sub with WebSockets and Redis - Ably. https://ably.com/blog/scaling-pub-sub-with-websockets-and-redis  
[^13]: Apache Kafka - Documentación oficial. https://kafka.apache.org/documentation/  
[^14]: Redis Pub/Sub vs. Apache Kafka - The New Stack. https://thenewstack.io/redis-pub-sub-vs-apache-kafka/  
[^15]: Redis Pub/Sub in Production: Advanced Patterns and Scaling. https://www.linkedin.com/pulse/redis-pubsub-production-advanced-patterns-scaling-fenil-sonani-no7vf  
[^16]: WebSockets at Scale - Production Architecture and Best Practices. https://websocket.org/guides/websockets-at-scale/  
[^17]: MDN - Pings y Pongs (Heartbeats) en WebSockets. https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers#pings_and_pongs_the_heartbeat_of_websockets  
[^18]: Fly.io Community - Autoscaling no se activa en aplicación puramente WebSocket. https://community.fly.io/t/autoscaling-is-not-triggered-on-a-pure-websocket-application/6048