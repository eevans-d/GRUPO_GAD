# Auditoría Técnica: Escalado de WebSockets con Redis Pub/Sub en GRUPO_GAD

## Resumen ejecutivo

GRUPO_GAD opera un backbone de tiempo real sobre WebSockets con distribución multi‑worker mediante Redis Pub/Sub. La aplicación expone métricas operacionales (conexiones activas, mensajes enviados, latencias, heartbeats) y ejecuta despliegues en Fly.io con estrategia rolling, health checks HTTP/TCP y límites de concurrencia por instancia. Sobre este foundation, la presente auditoría evalúa la arquitectura WebSocket, la integración Redis Pub/Sub, las capacidades de escalado horizontal, los patrones para alertas masivas, la configuración y monitoreo en producción, y los cuellos de botella de performance, con foco en alta disponibilidad 24/7 para servicios gubernamentales críticos.

Los hallazgos clave son:

- Arquitectura WebSocket: diseño apropiado para broadcasting cross‑worker con Redis; se recomienda fortalecer el manejo de concurrencia (backpressure por conexión, heartbeats estrictos, límites de payload) y evitar operaciones bloqueantes en el bucle de eventos. Las métricas actuales permiten instrumentar capacidad y latencia; falta tracking específico de reconexiones y caídas en ventanas de reconexión masiva.[^3][^4][^5][^6][^17]
- Redis Pub/Sub: implementación con canal único (“ws_broadcast”) y reconexión automática; cumple para fan‑out y coordinación entre workers. Para alertas masivas sostenidas, se sugiere namespacing, sharding de canales y pruebas de rendimiento, además de considerar Redis Streams donde se requiera retención y replay (fuera del alcance de Pub/Sub).[^10][^11][^14][^15]
- Escalabilidad: sticky sessions en balanceo son necesarias para sockets persistentes; se debe validar sticky en Fly.io y aumentar límites de descriptores a nivel de sistema operativo. El modelo de partición por “salas/usuarios” reduce trabajo por difusión y mejora latencia p95/p99.[^1][^2][^6][^16]
- Patrones gubernamentales: se recomienda segmentar canales por criticidad y rol (“gov:alerts:critical”, “citizen:notifications”), introducir IDs de mensaje, acks y reintentos para garantizar entrega en escenarios 24/7; considerar fallback de transporte y server‑side replay ante reconexiones masivas.[^10][^11][^17]
- Configuración y despliegue (Fly.io): la configuración actual define recursos y checks; se requiere habilitar métricas detalladas de WebSockets y Redis en Prometheus/Grafana (incluyendo redis_exporter), activar alertas de latencia y saturación, y documentar límites y políticas de autoscaling para cargas puramente WebSocket.[^8][^9][^18]
- Performance y optimización: principales riesgos son memoria por conexión, límites de descriptores y burst de tráfico. Acciones prioritarias: colas por cliente con límites, heartbeats ajustados, batching, coalescing de actualizaciones, y reducción de payload con formatos binarios (MessagePack/Protobuf) donde aplique.[^5][^6][^16][^17]

El mapa de riesgos con mayor impacto incluye: indisponibilidad por pérdida de sticky sessions, saturación de Redis en fan‑out masivo sin sharding, caídas de workers que provocarán reconexión masiva y pérdida de mensajes por semantics at‑most‑once de Pub/Sub. La mitigación requiere hardening operativo, instrumentation avanzada, sharding de canales y estrategias de retransmisión.

El roadmap prioriza tres fases: 0–30 días (hardening de resiliencia y métricas); 31–60 días (sharding de canales y pruebas de carga controladas); 61–90 días (HA con Sentinel, cambios de transporte y optimización de payload). Con ello, GRUPO_GAD dispondrá de una plataforma de tiempo real gubernamental con mayor previsibilidad de latencia, tolerancia a fallos y evidencia operativa para auditoría.

## Contexto y alcance

El sistema GRUPO_GAD consolida integraciones críticas: Telegram Bot como canal ciudadano, módulo geoespacial PostGIS para proximidad de efectivos, servicios Redis (cache y Pub/Sub) para tiempo real y observabilidad Prometheus/Grafana. La solución objetivo de esta auditoría es la capa WebSocket escalable con distribución entre workers vía Redis Pub/Sub, expuesta en el entorno de producción.

El alcance abarca: arquitectura WebSocket, integración Redis Pub/Sub, balanceo y sticky sessions, patrones de broadcasting, configuración en Fly.io, monitoreo y métricas, cuellos de botella de performance y recomendaciones de mejora.

La metodología se basa en revisión de la configuración y código operativos descritos en los inventarios de integraciones y configuraciones críticas, además de guías y artículos técnicos sobre escalado de WebSockets, Redis Pub/Sub y prácticas de producción en tiempo real.[^7][^8][^9]

Limitaciones: ciertos archivos de código y configuración no fueron accesibles; el análisis operativo se apoya en descripciones de comportamiento y métricas declaradas, con sugerencias alineadas a estándares de producción y evidencia técnica sectorial.[^7][^8][^9]

## Arquitectura WebSocket en GRUPO_GAD

La arquitectura actual está diseñada para sostener conexiones persistentes y distribuir mensajes a través de múltiples workers mediante Redis. En términos funcionales, se observa:

- Handlers y managers: existe un puente de publicación/suscripción Redis que consume mensajes y los entrega a un “manager” local para broadcast. El flujo general es Worker Local → Redis → Todos los workers suscritos → Conexiones WebSocket locales.
- Protocolo y reconexión: la aplicación establece heartbeats e instrumenta métricas de “último heartbeat”. El modelo se apoya en ping/pong a nivel de aplicación para detectar conexiones vivas y limpiar recursos.
- Concurrencia: el despliegue en producción define concurrencia por instancia y usa métricas de conexiones activas y totales; la distribución de carga depende del balanceador y de sticky sessions para sockets persistentes.
- Broadcasting: se utiliza un canal único (“ws_broadcast”) para fan‑out; para alertas gubernamentales y notificaciones masivas, se sugiere introducir namespacing y sharding para reducir contención y mejorar previsibilidad de latencia.

### Handlers y managers de conexión

El patrón de integración conecta un suscriptor Redis con un “BroadcastManager” local que se encarga de entregar mensajes a las conexiones activas por worker. Este diseño desacopla el estado de difusión del ciclo de vida de cada conexión y evita memoria compartida entre procesos. A nivel de prácticas recomendadas, conviene consolidar un “Minimal Connection Manager” que gestione de forma centralizada las uniones/salidas y el broadcasting seguro, reduciendo la posibilidad de fugas de recursos en el ciclo de vida de los sockets.[^1][^2]

### Protocolo, heartbeats y limpieza

El protocolo de heartbeats es el mecanismo de control de vida de la conexión: el envío periódico de ping/pong permite detectar caídas de red o clientes inactivos, liberar memoria y evitar el envío a sockets sin consumidor. Se recomienda:

- Definir intervalos de heartbeat por criticidad del flujo (alertas gubernamentales vs notificaciones ciudadanas).
- Implementar limpieza agresiva de conexiones cerradas y contar reconexiones por ventana (tasa de “connection churn”) para anticipar avalanchas.
- Instrumentar métricas de reconexiones y errores de envío (send_errors_total), junto con latencia de mensajes, para diferenciar problemas de red, de capa de aplicación y del broker.[^17]

### Concurrencia y uso de recursos

Cada conexión WebSocket ocupa memoria por buffers y estructuras de control, y consume un descriptor de archivo a nivel de sistema operativo. El límite práctico por instancia viene dado por la combinación de memoria disponible, límites de descriptores (ulimit) y overhead del runtime. Para sostener picos de 10k+ conexiones por instancia, se requiere:

- Minimizar el tamaño de estructuras por conexión y limitar el tamaño de payload.
- Ajustar ulimit y configurar keepalive de sockets; evitar operaciones síncronas bloqueantes en el bucle principal.[^5][^6][^16]

Para ilustrar límites operativos típicos y acciones sugeridas:

Tabla 1. Límites prácticos por instancia para 10k+ conexiones y acciones recomendadas

| Factor                       | Síntoma/Restricción                                  | Acción recomendada                                  |
|-----------------------------|-------------------------------------------------------|-----------------------------------------------------|
| Descriptores de archivo     | Rechazo de nuevas conexiones al alcanzar el límite   | Aumentar ulimit; optimizar fd por conexión[^16]     |
| Memoria por conexión        | Crecimiento lineal con 10k sockets                   | Reducir buffers; limitar payload; estructuras ligeras[^5][^6] |
| Bucle de eventos            | Bloqueos por I/O síncrona                            | I/O asíncrona; mover CPU‑bound a workers externos[^2][^3]     |
| Red y heartbeats            | “Zombies” y entrega a clientes caídos                | Ping/pong periódicos; cierre y limpieza proactiva[^17]        |

La tabla resume que los límites más frecuentes derivan de descriptores y memoria; sin acciones sobre el sistema operativo y la gestión de buffers, la escalabilidad horizontal se dificulta aun con más workers.

### Broadcasting y filtrado de mensajes

El canal único simplifica el fan‑out pero puede volverse cuello de botella en alertas masivas. La introducción de “salas” o particiones por usuario, y el uso de namespacing por criticidad, reduce la iteración sobre conexiones irrelevantes. La coalescencia de actualizaciones (combinar múltiples cambios en una sola notificación) disminuye presión de envío y latencia bajo ráfagas.[^3][^4]

Tabla 2. Estrategias de broadcasting: canal único vs canales particionados

| Estrategia                 | Latencia esperada | Carga en Redis | Complejidad operativa | Caso recomendado                      |
|---------------------------|-------------------|----------------|-----------------------|---------------------------------------|
| Canal único               | Variable          | Alta en ráfagas| Baja                  | Bajo volumen; simplicidad             |
| Partición por sala/usuario| Baja p95/p99      | Distribuida    | Media                 | Alertas dirigidas; segmentación por rol |
| Namespacing por criticidad| Predecible        | Balanceada     | Media                 | Priorización de alertas gubernamentales |

El análisis indica que el particionado reduce latencia y distribuye carga, a costa de mayor disciplina operativa en la gestión de canales y suscripciones.

## Integración Redis Pub/Sub

Redis se utiliza como bus de distribución entre workers, con soporte de reconexión automática y opciones de fallback de TLS. La semántica de Redis Pub/Sub es “at‑most‑once”: si no hay suscriptores o se pierden conexiones, los mensajes se pierden; no hay replay nativo.[^11][^14] La arquitectura actual implementa:

- Publicación: los workers publican eventos en un canal compartido para difusión cross‑worker.
- Suscripción: cada worker mantiene un loop suscriptor y reenvía a su manager local para entrega a sockets.
- Configuración: parámetros de keepalive y health check; fallback de TLS para proveedores que requieren deshabilitar verificación en entornos específicos (no recomendado en producción).

Limitaciones: fan‑out sin retención; si se requiere persistencia o replay en reconexión, Redis Streams es la estructura adecuada. Para alta disponibilidad, Redis Sentinel es preferible a Cluster en cargas Pub/Sub por restricciones de comandos entre nodos.[^10][^11][^15]

Tabla 3. Semánticas: Pub/Sub vs Streams vs Kafka

| Criterio            | Redis Pub/Sub                | Redis Streams                          | Apache Kafka                          |
|---------------------|------------------------------|----------------------------------------|---------------------------------------|
| Retención           | No                           | Sí (consumidores pueden replay)        | Sí (retención configurable)           |
| Orden               | No garantizado               | Parcial (por stream y posición)        | Orden por partición                   |
| Durabilidad         | No                           | Sí (persistencia en memoria/disco)     | Alta (replicación y durability)       |
| Uso típico          | Fan‑out y baja latencia      | Colas con replay y consumo histórico   | Eventos de alto volumen y auditoría   |

La elección depende del caso: Pub/Sub para broadcasting simple y baja latencia; Streams cuando se requiere replay y retenciÃ³n; Kafka para orden, durabilidad y flujos a gran escala.[^10][^11][^14][^15]

### Bridge cross‑worker y namespacing

Para escalar, se recomienda organizar canales con jerarquías claras, por ejemplo:

- gov:alerts:critical
- citizen:notifications
- ops:system:health

El particionado por canal permite filtrado eficiente y reducción de trabajo en cada suscriptor. El sharding de canales (distribuir canales entre varias instancias lógicas) evita hot spots y mejora el throughput sostenido.[^1]

### Escalado y HA con Redis

Redis Sentinel es la opción recomendada para alta disponibilidad en Pub/Sub: facilita failover y disponibilidad sin las limitaciones de Cluster para Pub/Sub. El sharding de canales, con un esquema de hashing consistente para mapear canales a instancias, mejora la capacidad horizontal. Es crítico mantener métricas del lado cliente para detectar particiones de red, latencias anómalas y caídas del bus.[^15]

## Escalabilidad y balanceo de carga

El escalado horizontal de WebSockets requiere sticky sessions: dado que la conexión es persistente y con estado por worker, el balanceador debe enrutar siempre al mismo backend durante la vida de la conexión. El uso de hashing por IP o cookies de sticky es habitual, pero tiene restricciones con IPs dinámicas o cambios frecuentes de backends.[^1][^2][^6][^16]

La distribución de conexiones debe ser monitorizada para detectar desbalances (hot instances) y niveles de saturación por worker. Con “rooms” o particiones por usuario, el broadcasting dirigido evita iterar sobre toda la base de conexiones.

Tabla 4. Estrategias de balanceo sticky vs no‑sticky

| Estrategia   | Pros                                        | Contras                                  | Escenarios de uso                     |
|--------------|---------------------------------------------|------------------------------------------|---------------------------------------|
| Sticky       | Mantiene estado por conexión; baja latencia | Riesgo de “hot nodes”; failover complejo | WebSockets persistentes               |
| No‑sticky    | Distribución uniforme                       | Requiere estado compartido; más latencia | Tráfico corto (no WebSockets)         |

Tabla 5. Distribución de 20k conexiones en N workers: métricas a observar

| Workers | Conexiones por worker | CPU/Mem estimada | Riesgo de hot node | Métricas clave                                    |
|---------|-----------------------|------------------|--------------------|---------------------------------------------------|
| 2       | 10k                   | Alta             | Alto               | p95/p99 latencia; colas por cliente; reconexiones |
| 4       | 5k                    | Media            | Medio              | Distribución por sala/usuario; saturación Redis   |
| 8       | 2.5k                  | Baja             | Bajo               | Heartbeat errors; send_errors_total; drop rate    |

El dimensionamiento depende de límites de descriptores y memoria por instancia. La adopción de rooms y sharding reduce el trabajo de difusión y mejora la latencia en el percentil alto.[^6][^16]

### Particionado por “salas”/usuarios

El particionado reduce broadcasting indiscriminado, permite entrega dirigida y estabiliza la latencia p95/p99 al minimizar iteraciones sobre sockets irrelevantes. Se recomienda asignar usuarios a salas por rol y criticidad, y usar nombres jerárquicos para facilitar suscripción por patrón.[^3]

### Backpressure y control de flujo

El control de contrapresión por cliente evita que productores rápidos colapsen consumidores lentos. Implementar colas por conexión con tamaño máximo, descartar mensajes obsoletos y coalescer actualizaciones frecuentes son prácticas necesarias para prevenir agotamiento de memoria y維持er latencia estable bajo ráfagas.[^3][^5]

## Patrones para escenarios gubernamentales

Los servicios gubernamentales de alerta requieren prioridad por criticidad, segmentación por rol y garantías de entrega superiores. Para ello:

- Namespacing por criticidad y canal ciudadano: “gov:alerts:critical” debe tener prioridad de entrega y monitoreo específico de latencia y éxito de broadcast.
- Semántica de entrega: introducir IDs de mensaje y acks para confirmar recepción; reintentos en publisher ante ausencia de acks; server‑side replay para usuarios reconectados (uso de Redis Streams donde aplique).
- Fallback de transporte: soportar long polling u otros mecanismos cuando WebSocket no sea viable; buffers en cliente con retroceso exponencial para reconexiones.[^10][^11][^17]

Tabla 6. Requisitos debroadcasting por criticidad

| Criticidad         | Latencia objetivo | Retención | Fallback         | ACK/Reintentos | Métricas requeridas                         |
|--------------------|-------------------|-----------|------------------|----------------|---------------------------------------------|
| Crítica gubernamental | p95 < 250 ms        | Opcional (Streams) | Sí               | Sí             | Latencia, éxito de entrega, reconexiones    |
| Operativa          | p95 < 500 ms        | No        | Sí               | Opcional       | Conexiones activas, broadcasts, errores     |
| Ciudadana          | p95 < 750 ms        | No        | Sí               | No             | Mensajes enviados, latencia, rate de drop   |

El diseño debe distinguir niveles de servicio y políticas por criticidad para asegurar comportamiento predecible bajo estrés.

### Disponibilidad 24/7 y DR

Una estrategia robusta incluye:

- Reconexión escalonada y backoff exponencial en clientes para evitar avalanchas.
- Failover a nivel de broker con Sentinel y redistribución de conexiones; pruebas periódicas de conmutación.
- Observabilidad con alertas por incumplimiento de SLA de latencia y entrega, saturación de colas y picos de reconexiones.[^10]

## Configuración y deployment en Fly.io

El entorno de producción define una región primaria, estrategia rolling, health checks HTTP/TCP, límites de concurrencia, exposición de métricas y variables operativas relevantes para WebSockets:

- Health checks: HTTP cada 15s y TCP redundantes; restart_limit y auto_rollback.
- Concurrencia: límites soft/hard por instancia.
- Métricas: puerto dedicado y endpoint /metrics; Prometheus scrape de aplicación y servicios.
- Variables: intervalos de heartbeat y límites de conexiones máximas.

Para cargas puramente WebSocket, se debe validar la activación del autoscaling, ya que métricas tradicionales de CPU/latencia HTTP pueden no reflejar la carga de sockets persistentes; se recomiendan señales complementarias (conexiones activas, tasa de reconexiones, latencia de mensajes).[^8][^9][^18]

Tabla 7. Parámetros relevantes de fly.toml y su impacto

| Parámetro                       | Impacto operativo                                         |
|---------------------------------|-----------------------------------------------------------|
| primary_region                  | Latencia y proximidad a usuarios                          |
| strategy=rolling + auto_rollback| Reducción de downtime; riesgo de reconexión masiva        |
| health checks (HTTP/TCP)        | Detección temprana de fallos; estabilidad del fleet       |
| concurrency (soft/hard)         | Capacidad por instancia; riesgo de saturación             |
| metrics port/path               | Observabilidad de aplicaciones y Redis                    |
| WS_HEARTBEAT_INTERVAL           | Control de vida de conexiones; limpieza de recursos       |
| WS_MAX_CONNECTIONS              | Prevención de sobrecarga por instancia                    |

### Health checks y readiness para sockets

Se recomienda exponer un endpoint de “socket health” que verifique estado del loop, colas por cliente y latencia de publicación/suscripción Redis. Los health checks deben distinguir startup ( readiness), liveness del proceso y checks específicos de sockets.[^9]

### Métricas y exposición

Las métricas base incluyen conexiones activas, totales, mensajes enviados, broadcasts, errores de envío y latencia de mensajes. Deben añadirse métricas de reconexiones, tamaño de colas por cliente y uso de descriptores por proceso. La integración con redis_exporter es esencial para visibilidad del bus.[^9]

## Monitoreo, métricas y alertas

La observabilidad se apoya en Prometheus y Grafana, con dashboards de rendimiento de API, métricas WebSocket, estado de Redis y métricas de infraestructura. Alertas operativas incluyen uptime, latencia, saturación de recursos, conexiones Redis y memoria. La instrumentación debe registrar latencias por mensaje (histogramas), conteo de broadcasts y errores de envío por worker, facilitando diagnósticos bajo eventos de alta concurrencia.[^9]

Tabla 8. Catálogo de métricas clave (aplicación y Redis)

| Componente   | Métrica                         | Descripción                                      |
|--------------|----------------------------------|--------------------------------------------------|
| WebSockets   | active_connections               | Conexiones activas por entorno                   |
| WebSockets   | connections_total                | Total histórico de conexiones                    |
| WebSockets   | messages_sent_total              | Mensajes enviados                                |
| WebSockets   | broadcasts_total                 | Difusiones realizadas                            |
| WebSockets   | send_errors_total                | Errores de envío                                 |
| WebSockets   | message_latency_seconds          | Latencia de entrega (histograma)                 |
| WebSockets   | heartbeat_last_timestamp         | Último heartbeat por entorno                     |
| WebSockets   | role_connections                 | Conexiones por rol                               |
| Redis        | connected_clients                | Clientes conectados                              |
| Redis        | pubsub_channels                  | Canales activos                                  |
| Redis        | pubsub_patterns                  | Patrones de suscripción                          |
| Redis        | blocked_clients                  | Clientes bloqueados (suscriptores)               |
| Redis        | redis_exporter (custom)          | Métricas exportadas del servidor                 |

La completitud del catálogo es crítica para correlacionar capacidad y latencia en incidentes reales.

## Performance y optimización

Los cuellos de botella más comunes en sistemas WebSocket a gran escala son:

- Memoria por conexión y crecimiento lineal con 10k+ sockets.
- Descriptores de archivo (ulimit), que limitan conexiones concurrentes aun con memoria disponible.
- Bloqueos del bucle de eventos por operaciones síncronas.
- Ráfagas de tráfico queprovocan saturación de envío y aumento de latencia.
- Single channel fan‑out con Redis, que puede provocar hot spots bajo alertas masivas.[^5][^6][^16]

Las acciones de tuning recomendadas incluyen backpressure por cliente (colas con límites), heartbeats y limpieza de conexiones, batching y coalescencia de mensajes, reducción de tamaño de payload (MessagePack/Protobuf), y sharding de canales. En casos donde se requiera garantía de entrega y replay, migrar flujos críticos a Redis Streams; para orden y durabilidad a gran escala, considerar Kafka.[^3][^6][^11][^17]

Tabla 9. Técnicas de optimización y su impacto

| Técnica                     | Impacto esperado                                  |
|----------------------------|----------------------------------------------------|
| Backpressure por cliente   | Estabiliza memoria y latencia bajo ráfagas         |
| Heartbeats estrictos       | Reduce “zombies”; libera recursos                  |
| Batching/coalescing        | Menos llamadas al sistema; menor latencia p95/p99 |
| Payload binario            | Reducción de tamaño y CPU de serialización         |
| Sharding de canales        | Distribuye carga en Redis; evita hot spots         |
| Límite de payload          | Controla memoria por mensaje                       |

### Latencia y orden

Para ordenar mensajes en entornos distribuidos, se recomienda incluir IDs de mensaje, timestamps y lógica de descarte de obsoletos. En broadcasting de alerta, asegurar que el publisher reintente ante ausencia de acks, y que los suscriptores confirmen recepción cuando el caso de uso lo requiera.[^11]

## Evaluación de riesgos y plan de mitigación

Riesgos principales:

- Indisponibilidad por pérdida de sticky sessions o desbalance (hot instances).
- Saturación del canal único en Pub/Sub ante alertas masivas.
- Reconexión masiva por despliegues o fallos de red, con pérdida de mensajes por semantics de Pub/Sub.
- Falta de replay y retención; latencias elevadas por hot spots.

Mitigaciones:

- Hardening de balanceo y sticky sessions; monitoreo de distribución por worker.
- Introducción de namespacing y sharding de canales; Sentinel para HA de Redis.
- Implementar backpressure por cliente, heartbeats estrictos y límites de payload.
- Establecer pruebas de carga periódicas y runbooks de incidentes, incluyendo fallback de transporte y políticas de reconexión escalonada.[^1][^6][^10][^11]

Tabla 10. Matriz de riesgos

| Riesgo                                | Probabilidad | Impacto | Severidad | Mitigación principal                           |
|---------------------------------------|--------------|---------|-----------|-----------------------------------------------|
| Pérdida de sticky sessions            | Media        | Alta    | Alta      | Validar sticky; hashing por IP/cookie          |
| Saturación canal único Pub/Sub        | Alta         | Media   | Alta      | Sharding y namespacing; Sentinel               |
| Reconexión masiva                     | Media        | Alta    | Alta      | Backoff; server‑side replay; Streams           |
| Ulimit/descriptores saturados         | Media        | Media   | Media     | Aumentar ulimit; optimizar fd por conexión     |
| Falta de observabilidad específica    | Media        | Alta    | Alta      | Métricas detalladas; alertas de latencia       |

## Roadmap de implementación y KPIs

Se propone un roadmap por fases con entregables claros:

- Fase 0–30 días: incorporar métricas avanzadas (reconexiones, tamaño de colas, descriptores), activar alertas de latencia y saturación; introducir namespacing básico; validar sticky en balanceo y ajustar heartbeats por criticidad.
- Fase 31–60 días: implementar sharding de canales; ejecutar pruebas de carga con 10k, 20k y 50k conexiones; ajustar límites de payload y colas por cliente; desplegar dashboards específicos de sockets.
- Fase 61–90 días: habilitar Redis Sentinel y realizar ejercicios de failover; explorar Redis Streams para flujos que requieran replay; introducir payload binario en canales críticos; evaluar fallback de transporte.

Tabla 11. Plan por fases y criterios de aceptación

| Fase        | Entregables clave                                     | Criterios de aceptación                             |
|-------------|--------------------------------------------------------|-----------------------------------------------------|
| 0–30 días   | Métricas avanzadas; alertas; namespacing básico       | p95 latencia < 500 ms en carga nominal              |
| 31–60 días  | Sharding; pruebas de carga; límites de payload        | 0 drops por backpressure en ráfagas controladas     |
| 61–90 días  | Sentinel; Streams; payload binario; fallback transporte| Recuperación en < 60 s en failover; estabilidad p99 |

Los KPIs recomendados incluyen:

- p95/p99 de latencia de mensaje.
- Tasa de reconexión por ventana (connection churn).
- Drop rate por backpressure y tamaño de colas.
- Uso de descriptores por proceso y memoria por conexión.

Los umbrales deben fijarse con base en pruebas de carga y objetivos de SLA específicos por criticidad.[^3][^6][^17]

## Anexos

Glosario de términos:

- Fan‑out: distribución de un mensaje a múltiples destinos.
- Namespacing: organización jerárquica de canales por propósito.
- Sticky sessions: persistencia de enrutamiento a un mismo backend durante la vida de la conexión.
- Backpressure: mecanismo de control de flujo para evitar saturación del consumidor.
- HA/DR: alta disponibilidad y recuperación ante desastres.

Snippets relevantes (descriptivos):

- Publicación en canal compartido con payload serializado (JSON); suscriptor Redis que consume y reenvía a manager local; métricas de latencia y reconexión instrumentadas.[^7][^9]

Checklist de producción para WebSockets + Redis:

- Sticky sessions validadas; ulimit configurado.
- Heartbeats y limpieza de conexiones.
- Backpressure por cliente; límites de payload.
- Namespacing y sharding de canales; Sentinel operativo.
- Métricas y alertas en Prometheus/Grafana; redis_exporter desplegado.
- Runbooks de incidentes y pruebas periódicas de carga.

## Brechas de información

Se identifican vacíos de información que limitan precisión cuantitativa:

- Código fuente de handlers y managers de WebSocket no accesibles; se infieren flujos desde inventarios.
- Métricas históricas de latencia de mensajes (p95/p99), throughput y error rate no disponibles.
- Parámetros operativos de balanceo ( sticky sessions, algoritmo, timeouts) y autoscaling en Fly.io no documentados.
- Topología y configuración de Redis (managed vs autogestionado, Cluster/Sentinel, región) no especificados.
- Políticas de seguridad (TLS, JWT, reautenticación y renovación de tokens) no detalladas para sockets.
- Pruebas de carga/estrés y capacidad (máx. conexiones por worker) no reportadas.
- Estrategia de reconexión, reintentos y replay ante fallos no definida.
- Límites de OS (ulimit, file descriptors) y tamaños de payload por mensaje no establecidos.
- Casos de uso específicos de alertas masivas y segmentación de ciudadanos no detallados.

Estas brechas deben abordarse en las Fase 0–30 días mediante instrumentación y documentación operativa.

## Referencias

[^1]: How to Scale FastAPI WebSocket Servers Without Losing State. https://hexshift.medium.com/how-to-scale-fastapi-websocket-servers-without-losing-state-6462b43c638c  
[^2]: How to Handle Large Scale WebSocket Traffic with FastAPI. https://hexshift.medium.com/how-to-handle-large-scale-websocket-traffic-with-fastapi-9c841f937f39  
[^3]: 8 FastAPI WebSocket Patterns for Real-Time Calm. https://medium.com/@connect.hashblock/8-fastapi-websocket-patterns-for-real-time-calm-481107379a65  
[^4]: Scaling WebSocket Servers — Load Balancing & High Availability in Real-Time Apps. https://medium.com/@priyanshu011109/scaling-websocket-servers-load-balancing-high-availability-in-real-time-apps-388b24b9157e  
[^5]: 5 Tips for Managing 10,000+ WebSocket Connections. https://medium.com/@arunangshudas/5-tips-for-managing-10-000-websocket-connections-2fe1fcbb7e4a  
[^6]: Scaling WebSockets to Millions. https://dyte.io/blog/scaling-websockets-to-millions/  
[^7]: GRUPO_GAD - Repositorio (Inventario y configuraciones). https://github.com/eevans-d/GRUPO_GAD  
[^8]: GRUPO_GAD - Entorno de producción en Fly.io. https://grupo-gad.fly.dev  
[^9]: Prometheus - Documentación oficial. https://prometheus.io/docs/introduction/overview/  
[^10]: Scaling Pub/Sub with WebSockets and Redis - Ably. https://ably.com/blog/scaling-pub-sub-with-websockets-and-redis  
[^11]: Redis Pub/Sub - Documentación oficial. https://redis.io/docs/latest/develop/pubsub/  
[^12]: Redis Pub/Sub - Glosario oficial. https://redis.io/glossary/pub-sub/  
[^13]: Apache Kafka - Documentación oficial. https://kafka.apache.org/documentation/  
[^14]: Redis Pub/Sub vs. Apache Kafka - The New Stack. https://thenewstack.io/redis-pub-sub-vs-apache-kafka/  
[^15]: Redis Pub/Sub in Production: Advanced Patterns and Scaling. https://www.linkedin.com/pulse/redis-pubsub-production-advanced-patterns-scaling-fenil-sonani-no7vf  
[^16]: WebSockets at Scale - Production Architecture and Best Practices. https://websocket.org/guides/websockets-at-scale/  
[^17]: MDN - Pings y Pongs (Heartbeats) en WebSockets. https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers#pings_and_pongs_the_heartbeat_of_websockets  
[^18]: Fly.io Community - Autoscaling no se activa en aplicación puramente WebSocket. https://community.fly.io/t/autoscaling-is-not-triggered-on-a-pure-websocket-application/6048