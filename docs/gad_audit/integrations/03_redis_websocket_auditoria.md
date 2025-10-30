# Auditoría integral de la integración Redis (Cache + Pub/Sub) + WebSocket en GRUPO_GAD

## Resumen ejecutivo y alcance

GRUPO_GAD opera un backbone de tiempo real sobre WebSockets con distribución multi‑worker mediante Redis, y utiliza Redis también como caché distribuido. La plataforma complementa este backbone con observabilidad en Prometheus/Grafana y prácticas de despliegue en Fly.io. Sobre esa base, esta auditoría examina la arquitectura dual de Redis (caché y Pub/Sub), el intercambio de mensajes entre workers por Pub/Sub, las garantías de entrega y orden, la gestión de reconexiones, los límites de rendimiento en escenarios con 10k–50k conexiones, y la estrategia de seguridad, monitoreo y resiliencia. El enfoque es doble: validación del diseño actual y hoja de ruta para elevar la fiabilidad, el rendimiento y la gobernanza.

Hallazgos clave y prioridades:

- Sticky sessions son imprescindibles para WebSockets persistentes; la pérdida de adherencia o la falta de afinidad causa reconexiones y potenciales pérdidas de mensajes en Pub/Sub. Validar y reforzar el enrutamiento sticky y su telemetría es prioritario.[^1]
- Redis Pub/Sub ofrece baja latencia y fan‑out simple, pero su semántica es at‑most‑once. Para alertas gubernamentales críticas, se requieren garantías superiores (ACKs, IDs de mensaje, reintentos) y, cuando sea necesario, retención/replay con Redis Streams.[^5]
- El canal único “ws_broadcast” simplifica la operación, pero no escala en eventos masivos sostenidos. Introducir namespacing y sharding de canales por criticidad y rol reduce contención y estabiliza latencia p95/p99.[^5]
- La separación de concerns entre caché y Pub/Sub debe reflejarse en distintas políticas de conexión: pooling/multiplexing para caché; conexiones dedicadas (no multiplexadas) para suscripciones Pub/Sub, por su semántica de bloqueo y lifecycle propio.[^2]
- Sentinel es el mecanismo preferible para alta disponibilidad en flujos Pub/Sub; Redis Cluster aporta sharding para datos, pero su soporte de Pub/Sub tiene limitaciones de comandos entre nodos que impactan fan‑out y suscripción cruzada.[^4][^5]

La hoja de ruta por fases (0–30/31–60/61–90 días) propone quick wins en métricas y namespacing, sharding y pruebas de carga, y consolidación de HA (Sentinel), seguridad TLS/ACLs y migración selectiva a Streams en flujos que requieran retención y replay. Con ello, se espera mejorar latencia p95/p99 en broadcasting, reducir pérdidas por reconexión y reforzar la capacidad de auditoría y cumplimiento.

Limitaciones e information gaps: la auditoría se apoya en la documentación pública y el inventario de integraciones; no se dispone de métricas históricas completas (p95/p99), topología operativa detallada de Redis (gestionado vs autogestionado, Cluster/Sentinel), ni de parámetros de balanceo y autoscaling en Fly.io específicos para WebSockets. Estas brechas se señalan en cada sección y se integran en el plan 0–30 días para su cierre controlado.

## Metodología, fuentes y contexto del sistema

El análisis se apoya en la revisión de inventarios y configuraciones operativas declaradas de GRUPO_GAD, y en documentación técnica de Redis, patrones de escalado de WebSockets y guías de observabilidad. Se contrastan prácticas observadas con recomendaciones de producción, poniendo foco en: separación de responsabilidades de Redis, garantías de entrega de Pub/Sub, seguridad y resiliencia, y operación bajo alta concurrencia.

Fuentes primarias de referencia:
- Inventario de integraciones del sistema y prácticas declaradas de observabilidad (métricas base, dashboards).
- Documentación oficial de Redis sobre clientes, pooling y multiplexing, Sentinel y Cluster.[^2][^3][^4]
- Patrones de escalado WebSocket con Redis Pub/Sub y guías de producción.[^5][^1]
- Prometheus/Grafana para métricas y alerting, y exposición de métricas en Redis Enterprise.[^6][^7][^8][^9]

Información no disponible y su impacto:
- Métricas históricas p95/p99, reconexión por ventanas y saturación por worker: limita la calibración de SLAs y umbrales de alerta; se requiere instrumentación adicional (histogramas, contadores de reconexión).
- Topología Redis operativa (gestionado vs autogestionado, Cluster/Sentinel, región, latencias entre AZs): condiciona el diseño de HA y el failover; se define un plan de discovery.
- Políticas de sticky sessions, algoritmo del balanceador, timeouts y estrategia de autoscaling para cargas WebSocket en Fly.io: imprescindible para evitar hot nodes y reconexión masiva; se documenta gap y plan de validación.

## Arquitectura dual de Redis (Cache + Pub/Sub): separación de concerns y HA

Redis выполняет две роли diferentes en la plataforma: cache y bus de Pub/Sub. La arquitectura debe separar explícitamente sus modelos de datos, latencias objetivo, semánticas de entrega, requisitos de HA y políticas de conexión.

- Caché distribuido: opera con claves/valores, TTLs y patrones de invalidación. Objetivo: latencia baja con alta tasa de aciertos y control de evicciones.
- Pub/Sub cross‑worker: opera con canales y suscripciones, sin retención nativa. Objetivo: difusión con la menor latencia posible entre workers, con ack/retry gestionados por la aplicación cuando se requiera.

La separación se refleja en:
- Claves vs canales: espacios de nombres y convenciones diferenciadas (por ejemplo, prefijos “cache:” y “pubsub:”).
- Requisitos de HA: Sentinel para Pub/Sub; Cluster para sharding de datos en caché si la capacidad lo requiere.[^4][^5]
- Políticas de conexión: pooling/multiplexing para caché; conexiones dedicadas para Pub/Sub por su semántica de bloqueo.[^2][^10]

Para ilustrar las diferencias de diseño:

Tabla 1. Comparativa funcional: Caché vs Pub/Sub

| Dimensión            | Caché (KV, TTL)                                   | Pub/Sub (canales)                                              |
|----------------------|----------------------------------------------------|----------------------------------------------------------------|
| Propósito            | Reducir latencia de lectura/escritura              | Difusión cross‑worker                                          |
| Modelo de datos      | Claves con TTL, estructuras simples                | Publicación/suscripción en canales                             |
| Semántica de entrega | Lecturas consistentes (según TTL/evicción)         | At‑most‑once; sin retención nativa[^5]                         |
| Latencia esperada    | Milisegundos (single digit)                        | Milisegundos; fan‑out entre workers                            |
| Persistencia         | Opcional (RDB/AOF/hibrida)                         | No persistente; mensajes no se retienen                        |
| HA                   | Sentinel (single instance) o Cluster (sharding)    | Sentinel preferible; Cluster con limitaciones para Pub/Sub[^5] |

### Connection management para ambos usos

El cliente Redis debe gestionar conexiones de forma diferenciada:

- Caché: usar pooling o multiplexing. Multiplexing comparte una conexión, combina comandos en pipeline y reduce RTT; no soporta comandos de bloqueo (como BLPOP) que paralizan la conexión para otros consumidores.[^2]
- Pub/Sub: usar conexiones dedicadas. La suscripción mantiene un loop y puede bloquear la conexión; multiplexar con comandos de bloqueo no es seguro. Algunos clientes intentionally bypass pooling para Pub/Sub, evitando reutilizar conexiones que están en estado de suscripción.[^10]

Directivas operativas:
- Diferenciar pools (caché) de conexiones de suscripción.
- Health checks específicos: ping para pool; latencia de suscripción y reconexión automática para Pub/Sub.
- Circuit breaker y backoff exponencial en suscriptores para evitar tormentas de reconexión.

Tabla 2. Patrones de conexión recomendados

| Uso             | Patrón          | Soporte de clientes | Precauciones                                    |
|-----------------|------------------|---------------------|-------------------------------------------------|
| Caché           | Pooling          | Amplio              | Dimensionar min/max conexiones                  |
| Caché           | Multiplexing     | Amplio              | Evitar comandos de bloqueo (BLPOP, etc.)[^2]    |
| Pub/Sub         | Conexión dedicada| Amplio              | No multiplexar; reconexión y backoff            |
| Pub/Sub en Go   | Pool no seguro   | go‑redis issue      | Pub/Sub intencionalmente no usa pool[^10]       |

### HA y topologías: Sentinel vs Cluster

- Sentinel proporciona HA para instancias únicas (no en Cluster): monitoreo, failover y proveedor de configuración para clientes. Requiere al menos tres Sentinels en dominios de fallo independientes y configuración de quorum.[^4]
- Redis Cluster aporta sharding (16384 slots) y HA por master‑réplica, con limitaciones para Pub/Sub: comandos multi‑slot y distribución entre nodos no aplican trivialmente a canales, y el fan‑out puede quedar confinado al nodo local según comandos y topología. En la práctica, Sentinel se prefiere para Pub/Sub; Cluster es idóneo para escalar datos del caché.[^3][^5]

Tabla 3. Sentinel vs Cluster por caso de uso

| Caso de uso             | Sentinel                         | Cluster                                      |
|-------------------------|----------------------------------|----------------------------------------------|
| Pub/Sub                 | Recomendado (HA y failover)      | Limitado; comandos Pub/Sub entre nodos[^5]   |
| Caché (sharding datos)  | Posible (single instance)        | Recomendado (slots y sharding)[^3]           |
| Replicación             | Asíncrona (mejora con WAIT)      | Asíncrona; redirección de clientes[^3]       |
| Descubrimiento cliente  | Vía Sentinel                     | Mapa de slots                                |

## Estrategias de caché operativas

El caché de datos operativos (por ejemplo, entidades y agregaciones frecuentes) se rige por patrones de invalidación y TTL por clase de dato. La clave es equilibrar frescura, tasa de aciertos y costo de recálculo.

- Invalidación basada en tiempo (TTL): simple y efectiva para datos semi‑estáticos; ajustar por tipo de contenido (más corto para dinámico, más largo para estático).[^11][^12]
- Invalidación basada en eventos: cambios de estado disparan invalidación (por ejemplo, invalidación por dependencia o grupo). Útil para mantener consistencia en actualizaciones frecuentes.[^11]
- Write‑through / write‑behind: actualizar la fuente y la caché en el mismo flujo (write‑through) o diferir escritura (write‑behind), con trade‑offs en consistencia y latencia.[^12]
- Evitar “overcaching”: datos que cambian a alta frecuencia y requieren consistencia estricta no deben residir en caché largos periodos; fijar TTLs cortos y preferir invalidación por evento.[^11][^12]
- Hot keys y big keys: detectar y corregir; dividir estructuras grandes y monitorear accesos para evitar skew.[^13]

Tabla 4. Matriz de TTL sugerido por tipo de dato

| Tipo de dato                         | TTL sugerido          | Invalidación recomendada                 | Observaciones                                    |
|--------------------------------------|-----------------------|-------------------------------------------|--------------------------------------------------|
| Metadatos y catálogos                | 6–24 h                | Event‑driven por despliegue               | Estables; invalidar en releases                  |
| Agregaciones operativas (hourly)     | 15–60 min             | Event‑driven por actualización            | Evitar staleness en ventanas críticas            |
| Perfiles y configuraciones usuario   | 5–15 min              | TTL corto + write‑through                 | Cambios frecuentes; precisión prioritaria        |
| Resultados de proximidad/geoespacial | 2–5 min               | TTL + invalidación por evento (movimiento)| Freshness para decisiones en campo               |
| Listas de salas/roles                | 30–120 min            | Event‑driven por cambios de rol           | Menos volátil; coherencia razonable              |

Tabla 5. Riesgos por “hot/big keys” y mitigaciones

| Riesgo                            | Señal                                     | Mitigación                                           |
|-----------------------------------|-------------------------------------------|------------------------------------------------------|
| Hot key (picos de acceso)         | Monitoreo de comandos, skew de ops/s      | Particionar key; caching distribuido;hash tags[^13] |
| Big key (estructuras grandes)     | redis-cli --bigkeys, latencia de HGETALL  | Dividir en claves menores; controlar rangos[^13]    |
| Expiración masiva                 | Picos de evicciones, latencia creciente   | TTL escalonado; evitar expiración sincrónica[^13]   |

### Warm‑up de caché para operaciones críticas

Las rutas críticas (por ejemplo, proximidad de efectivos) deben precalcularse y cargarse antes del arranque o tras recuperación de fallos (rehidratación), conmedición del impacto en tiempo de arranque y verificación de integridad. Usar RDB/AOF según política de recuperación definida y el tiempo objetivo de rehidratación.[^14]

## Pub/Sub operativo para WebSockets

Redis Pub/Sub es el bridge cross‑worker para broadcasting de eventos hacia múltiples instancias de servidor. El canal único “ws_broadcast” facilita el fan‑out, pero en alertas masivas sostenidas introduce contención y latencias impredecibles. Se recomiendan:

- Namespacing por criticidad y rol (ej., “gov:alerts:critical”, “citizen:notifications”, “ops:system:health”).
- Sharding de canales mediante hashing consistente a nivel de aplicación para distribuir la carga entre múltiples shards lógicos (instancias Redis), mitigando hot spots.[^5]
- Semántica de entrega: Pub/Sub es at‑most‑once. Cuando la entrega garantizada sea necesaria, la aplicación debe instrumentar IDs de mensaje, acks y reintentos, y considerar Redis Streams para retención y replay en reconexiones masivas.[^15][^5][^20]

Tabla 6. Pub/Sub vs Streams vs Kafka

| Criterio         | Redis Pub/Sub                 | Redis Streams                          | Apache Kafka                           |
|------------------|-------------------------------|----------------------------------------|----------------------------------------|
| Retención        | No                            | Sí (replay por posición)               | Sí (por partición, configurable)       |
| Orden            | No garantizado                | Parcial (por stream y posición)        | Orden por partición                    |
| Durabilidad      | No                            | Sí (persistencia AOF/RDB/Streams)      | Alta (replicación y durability)        |
| Uso típico       | Fan‑out baja latencia         | Colas con replay y consumo histórico   | Eventos de alto volumen y auditoría    |

Tabla 7. Matriz de entrega/acks/reintentos vs caso de uso

| Caso de uso                               | Requisito                         | Recomendación                                        |
|-------------------------------------------|-----------------------------------|------------------------------------------------------|
| Notificación ciudadana                    | Baja latencia, mejor esfuerzo     | Pub/Sub con nombrespacing, sin retención             |
| Alerta gubernamental crítica              | Garantía de entrega               | IDs + ACK/retry; Server‑side replay (Streams)[^15]   |
| Coordinación operativa entre servicios    | Retención y auditoría             | Redis Streams o Kafka según volumen/escala[^20]      |

#### Manejo de disconnections y reconexiones

El suscriptor debe implementar reconexión con backoff exponencial y limpieza del estado (reasignación de canales, validación de suscripciones activas). En el cliente WebSocket, aplicar heartbeats (ping/pong) y backoff para evitar avalanchas de reconexión.[^16][^5]

## Integración WebSocket + Redis: broadcasting, routing y failover

El flujo Worker Local → Redis → Todos los workers → Conexiones WebSocket locales debe evitar operaciones bloqueantes en el bucle de eventos y aplicar backpressure por cliente (colas con límites y descarte de obsoletos). La pérdida de sticky sessions y los desbalances por worker (hot nodes) incrementan latencia y drop rate; el dimensionamiento de descriptores (ulimit) y buffers por conexión define la capacidad por instancia.[^1][^17]

Estrategias:
- Partición por “salas/usuarios”: reduce la iteración irrelevante y estabiliza p95/p99.
- Sticky sessions: validar persistencia de enrutamiento y su telemetría.[^1]
- Routing por criticidad y sharding de canales: balancea el fan‑out y evita hotspots.
- Failover en Redis: Sentinel con descubrimiento del master para clientes; tiempos de failover deben ser transparentes a la sesión WebSocket.[^4]

Tabla 8. Escenarios de balanceo: sticky vs no‑sticky

| Escenario                  | Ventajas                              | Riesgos                                  | Métricas clave                                     |
|---------------------------|---------------------------------------|------------------------------------------|----------------------------------------------------|
| Sticky                    | Estado por conexión, baja latencia    | Hot nodes; failover más complejo         | Distribución por worker; p95/p99 latencia[^1]      |
| No‑sticky                 | Distribución uniforme                 | Requiere estado compartido               | Latencia promedio; varianza entre workers          |

Tabla 9. Rutas de mensaje y garantías

| Ruta                                | Semántica                      | Garantías aplicadas                           |
|-------------------------------------|--------------------------------|-----------------------------------------------|
| Worker → Redis → Workers → Clientes | Pub/Sub at‑most‑once           | IDs/ACK/retry a nivel aplicación              |
| Reconexión masiva                   | Pub/Sub + retry                | Backoff + replay (Streams si se requiere)[^15]|

#### Sticky sessions y distribución de carga

En WebSockets persistentes, el balanceador debe mantener la afinidad durante la vida de la conexión. El hashing por IP o cookies sticky son prácticas comunes; hay que monitorear la distribución para detectar hot nodes y actuar (rebalanceo o ajuste de pesos).[^1]

## Seguridad en la integración Redis

La seguridad debe cubrir cifrado, autenticación, control de acceso, red y auditoría:

- TLS mutuo (client authentication) y禁用 protocolos obsoletos. En redes de producción, habilitar TLS para cliente‑servidor y replicación; gestionar certificados y rotación.[^18][^19]
- ACLs (Access Control Lists) para granularidad de permisos por usuario/rol; deshabilitar comandos peligrosos y evitar exposición directa a internet.[^19]
- Firewalling y segmentación: restringir puertos y orígenes; usar binding de interfaces y modos protegidos en Redis.[^19]
- Protección de datos en caché: TTL y clasificarlos por sensibilidad; revisar retención en logs y trazabilidad con correlation IDs.[^6]

Tabla 10. Matriz de controles de seguridad

| Capa               | Control                              | Objetivo                                          |
|--------------------|--------------------------------------|---------------------------------------------------|
| Transporte         | TLS 1.2+, mTLS                       | Cifrado en tránsito; autenticación mutua[^18]     |
| Acceso             | ACLs por usuario/rol                 | Principio de menor privilegio[^19]                |
| Red                | Firewalling y binding                | Reducir superficie de exposición[^19]             |
| Datos              | TTL y clasificación de claves        | Minimizar retención de datos sensibles            |
| Auditoría          | Logs correlacionados                 | Trazabilidad y cumplimiento                       |

#### Auditoría y cumplimiento

Instrumentar auditoría en flujos críticos: publicar/consumir mensajes, accesos a claves sensibles, operaciones de administración (failover, reconfigure). Mantener logs estructurados con correlation IDs y retention alineado a requisitos gubernamentales.[^6]

## Performance y escalabilidad

Medir throughput y latencia end‑to‑end (cache hit/miss vs acceso directo a base de datos) y optimizar memoria, conexiones y uso de CPU:

- Memoria y conexiones: más conexiones aumentan consumo de memoria; ajustar pool y límites de descriptores; evitar evicciones masivas que disparan latencia.[^13][^21][^22]
- Pipelining y batching: reducir RTT y llamadas al sistema al agrupar comandos.[^13]
- Tamaño de payload y formatos: preferir formatos binarios (MessagePack/Protobuf) donde aplique para reducir CPU y ancho de banda.[^5]

Tabla 11. Catálogo de KPIs de performance

| KPI                               | Descripción                                  | Fuente/medición                    |
|-----------------------------------|----------------------------------------------|------------------------------------|
| Latencia p95/p99 de mensaje       | Broadcasting y entrega por WebSocket         | Histograma de latencia[^6]         |
| Throughput Redis (ops/s)          | Comandos por segundo por uso (cache/Pub/Sub) | Métricas de servidor               |
| Cache hit/miss ratio              | Por categoría de dato                         | Métricas de aplicación y exporter  |
| Conexiones activas Redis          | Por tipo (pool, suscriptores)                 | INFO clients / exporter[^8]        |
| Evicciones y expiraciones         | Eventos por ventana                           | Métricas de memoria/persistencia   |
| Reconexiones por ventana          | Tasa de connection churn                      | Métricas de aplicación             |

Tabla 12. Impacto de técnicas de optimización

| Técnica                    | Impacto esperado                                   |
|---------------------------|-----------------------------------------------------|
| Pipelining                | Menor latencia acumulada; mayor throughput[^13]     |
| Backpressure por cliente  | Estabilidad de memoria; reducción de drops          |
| Heartbeats estrictos      | Menos “zombies”; limpieza proactiva de recursos[^16]|
| Payload binario           | Menor CPU y tamaño; mejora de p95/p99               |
| Sharding de canales       | Distribución de carga; evita hot spots              |

#### Backpressure y control de flujo

Para evitar avalanchas de envío en picos, el sistema debe aplicar colas por cliente con tamaño máximo, descarte de obsoletos y coalescencia de actualizaciones. El diseño previene agotamiento de memoria y mantiene latencia estable bajo ráfagas.[^1]

## Monitoreo y observabilidad

La observabilidad debe cubrir Redis y WebSockets, con dashboards y alertas específicas:

- Métricas Redis: connected_clients, pubsub_channels, pubsub_patterns, blocked_clients, memoria y slowlog; integrar redis_exporter y dashboards de Grafana.[^7][^8][^9]
- Métricas WebSockets: active_connections, messages_sent_total, broadcasts_total, send_errors_total, message_latency_seconds (histograma), heartbeat_last_timestamp, role_connections; Prometheus como fuente y Grafana para visualización.[^6]

Tabla 13. Catálogo de métricas: Redis

| Métrica               | Descripción                                |
|-----------------------|--------------------------------------------|
| connected_clients     | Clientes conectados                        |
| pubsub_channels       | Canales activos                            |
| pubsub_patterns       | Patrones de suscripción                    |
| blocked_clients       | Clientes bloqueados (suscriptores)         |
| memory_used           | Memoria usada                              |
| slowlog_len           | Longitud del slow log                      |

Tabla 14. Métricas de aplicación WebSocket y alertas

| Métrica                         | Umbral sugerido (inicial)       | Acción                                    |
|---------------------------------|----------------------------------|-------------------------------------------|
| message_latency_seconds p95     | > 500 ms                         | Alertar; investigar sharding/payload      |
| broadcasts_total                | Spike atípico                    | Validar diseño de canales                 |
| send_errors_total               | > 1% de mensajes                 | Revisar backpressure y buffers            |
| connection_churn_rate           | > 5% por minuto                  | Revisar heartbeats y sticky               |
| role_connections imbalance      | Desbalance > 20%                 | Rebalanceo de workers                     |

#### Latencia y orden

Incluir IDs de mensaje y timestamps por evento para ordenar y descartar duplicados/obsoletos. En casos críticos, esperar ACK del consumidor o de la capa de entrega, con reintentos controlados por la aplicación.[^11]

## Disaster recovery y resiliencia

Diseñar persistencia, backups y pruebas de failover:

- Persistencia RDB/AOF/híbrida: RDB ofrece snapshots compactos y reinicios rápidos; AOF registra cada escritura y, con política everysec, balancea rendimiento y durabilidad. La combinación es común en producción.[^14]
- Backups: RDB horarias/diarias y transferencia fuera del datacenter (por ejemplo, S3 cifrado). En Redis 7+, AOF en multipart con manifest, considerar estrategias para copiar sin bloquear reescrituras.[^14]
- Failover: pruebas periódicas con Sentinel; documentar tiempos y procedimientos. Redis Cluster permite failover manual y reubicación de slots, con consideraciones en clientes conscientes del cluster.[^4][^3]

Tabla 15. Matriz de persistencia y backup

| Estrategia           | Ventajas                                | Desventajas                              | Caso de uso                                  |
|----------------------|-----------------------------------------|-------------------------------------------|----------------------------------------------|
| RDB                  | Compacto; rápido reinicio               | Pérdida de últimos minutos                | DR y archive; caché con recálculo viable[^14]|
| AOF (everysec)       | Durable; menor pérdida de datos         | Archivo más grande; posibles picos        | Flujos con necesidad de durabilidad[^14]     |
| Híbrida (RDB+AOF)    | Balance entre rapidez y durabilidad     | Complejidad operativa                      | Producción con requisitos mixtos             |

#### Procedimientos de recovery

- Restauración con RDB: sustituir dump.rdb y reiniciar; verificar integridad y tiempos.[^14]
- Reparación de AOF truncado/corrupto: redis-check-aof; considerar pérdida a partir de la corrupción; auditoría post‑restauración.[^14]

Pruebas de DR deben incluir validación de tamaño y hash de backups, alertas en caso de fallo de transferencia y ejecución de ejercicios de failover Sentinel con observación de latencia y estabilidad del bus.

## Procedimientos operacionales

La operación estable de Redis y la capa WebSocket requiere runbooks y disciplina en mantenimiento, capacity planning y despliegue:

- Mantenimiento: actualizaciones sin downtime (failover manual en Cluster, rolling en workers), tuning de parámetros críticos, revisión de slowlog y hotkeys.[^13][^3]
- Capacity planning: conexiones máximas por worker, memoria por conexión, límites OS (ulimit), número de shards; dimensionamiento por objetivos de p95/p99.[^1][^22]
- Despliegues: validación de sticky sessions, health checks específicos de sockets, readiness y liveness diferenciados.[^1]
- Troubleshooting: guías para hotkeys, latencia de red, skew de shards y evicciones masivas.[^13]

Tabla 16. Runbooks operativos

| Incidente                       | Diagnóstico                                      | Acción                                                         |
|---------------------------------|--------------------------------------------------|----------------------------------------------------------------|
| Latencia alta p95/p99           | Histogramas y slowlog                            | Pipelining; reducir payload; sharding; backpressure[^13]       |
| Reconexión masiva               | Métricas de churn y heartbeat                    | Revisar sticky; backoff; reintentos; Sentinel failover[^4]     |
| Evicciones y expiraciones masivas| Memoria; política de evicción; TTL               | Incrementar memoria; ajustar TTL; escalonar expiraciones[^13]  |
| Shard caliente                  | Monitoreo de ops/s; big/hot keys                 | Re‑shard; dividir claves; controlar rangos[^13]                |

#### Capacity planning para 10k–50k conexiones

Dimensionar conexiones y descriptores por instancia, limitar payload y buffers, y diseñar distribución por salas/usuarios para evitar broadcasting indiscriminado. La separación reduce iteración sobre sockets irrelevantes y mejora latencia en percentiles altos.[^1][^22]

Tabla 17. Escenarios de distribución

| Conexiones totales | Workers | Conexiones por worker | CPU/Mem estimada | Riesgo de hot node | Observaciones clave                          |
|--------------------|---------|-----------------------|------------------|--------------------|---------------------------------------------|
| 10k                | 2       | 5k                    | Alta             | Alto               | Validar ulimit; buffers y payload            |
| 20k                | 4       | 5k                    | Media            | Medio              | Partición por salas; métricas por worker     |
| 50k                | 8       | ~6.25k                | Alta             | Medio              | Sharding de canales; backpressure efectivo   |

## Cumplimiento gubernamental y gobernanza

Políticas de seguridad:
- JWT y rotación periódica; TLS 1.2+ en todos los canales; ACLs para acceso granular; firewalling y segmentación de red.[^18][^19]
Auditoría:
- Trazabilidad end‑to‑end con correlation IDs; logs estructurados; retención conforme a regulación; reportes operativos en Grafana con alertas de SLA.

Tabla 18. Mapa de cumplimiento

| Control                      | Evidencia operativa                          | Métrica/alerta asociada                  |
|-----------------------------|----------------------------------------------|------------------------------------------|
| TLS 1.2+ y mTLS             | Configuración y certificados                  | Alertas por expiración de certificados   |
| ACLs por rol/usuario        | Listas y permisos                             | Auditoría de accesos                     |
| Auditoría de Pub/Sub        | Logs de publicar/consumir                     | Reportes de entrega y retries            |
| SLA de latencia             | Dashboards p95/p99                            | Alertas por incumplimiento               |

## Roadmap y KPIs

Fase 0–30 días:
- Instrumentar métricas avanzadas (reconexiones, colas por cliente, descriptores), activar alertas de latencia y saturación; introducir namespacing básico; validar sticky sessions; ajustar heartbeats por criticidad.[^6][^1]

Fase 31–60 días:
- Implementar sharding de canales; ejecutar pruebas de carga en 10k/20k/50k conexiones; optimizar payload (binario donde aplique) y límites por cliente; dashboards específicos de sockets.[^5][^17]

Fase 61–90 días:
- Habilitar Redis Sentinel y realizar ejercicios de failover; migrar flujos que requieran retención/replay a Redis Streams; evaluar fallback de transporte (long polling); consolidar TLS/ACLs.[^4][^20]

Tabla 19. Entregables por fase y criterios de aceptación

| Fase        | Entregables clave                           | Criterios de aceptación                            |
|-------------|---------------------------------------------|----------------------------------------------------|
| 0–30 días   | Métricas/alerting; namespacing básico       | p95 < 500 ms en carga nominal                      |
| 31–60 días  | Sharding; pruebas de carga; payload binario | 0 drops por backpressure en ráfagas controladas    |
| 61–90 días  | Sentinel; Streams; TLS/ACLs                 | Recuperación < 60 s en failover; estabilidad p99   |

KPIs:
- p95/p99 de latencia de mensaje.
- Tasa de reconexión por ventana (connection churn).
- Drop rate por backpressure y tamaño de colas.
- Uso de descriptores por proceso y memoria por conexión.[^6][^1][^22]

---

## Referencias

[^1]: WebSockets at Scale - Production Architecture and Best Practices. https://websocket.org/guides/websockets-at-scale/  
[^2]: Connection pools and multiplexing | Docs - Redis. https://redis.io/docs/latest/develop/clients/pools-and-muxing/  
[^3]: Scale with Redis Cluster | Docs. https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/  
[^4]: High availability with Redis Sentinel | Docs. https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/  
[^5]: Scaling Pub/Sub with WebSockets and Redis - Ably Realtime. https://ably.com/blog/scaling-pub-sub-with-websockets-and-redis  
[^6]: Prometheus - Documentación oficial. https://prometheus.io/docs/introduction/overview/  
[^7]: Prometheus and Grafana with Redis Enterprise Software | Docs. https://redis.io/docs/latest/integrate/prometheus-with-redis-enterprise/  
[^8]: Redis monitoring made easy | Grafana Labs. https://grafana.com/solutions/redis/monitor/  
[^9]: Configure Redis exporter to generate Prometheus metrics - Grafana. https://grafana.com/docs/grafana-cloud/knowledge-graph/enable-prom-metrics-collection/data-stores/redis/  
[^10]: Pubsub Connection Pooling · Issue #785 · redis/go-redis. https://github.com/go-redis/redis/issues/785  
[^11]: Cache Invalidation - Redis Glossary. https://redis.io/glossary/cache-invalidation/  
[^12]: Caching Best Practices | AWS. https://aws.amazon.com/caching/best-practices/  
[^13]: Performance Tuning Best Practices - Redis. https://redis.io/kb/doc/1mebipyp1e/performance-tuning-best-practices  
[^14]: Redis persistence | Docs. https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/  
[^15]: Redis Pub/Sub - Documentación oficial. https://redis.io/docs/latest/develop/pubsub/  
[^16]: MDN - Pings y Pongs (Heartbeats) en WebSockets. https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers#pings_and_pongs_the_heartbeat_of_websockets  
[^17]: Scaling WebSockets to Millions. https://dyte.io/blog/scaling-websockets-to-millions/  
[^18]: Enable TLS | Docs - Redis Enterprise. https://redis.io/docs/latest/operate/rs/security/encryption/tls/enable-tls/  
[^19]: Redis security | Docs. https://redis.io/docs/latest/operate/oss_and_stack/management/security/  
[^20]: Microservices Communication with Redis Streams. https://redis.io/learn/howtos/solutions/microservices/interservice-communication  
[^21]: Memory optimization | Docs - Redis. https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/  
[^22]: Redis Memory & Performance Optimization - DragonflyDB. https://www.dragonflydb.io/guides/redis-memory-and-performance-optimization