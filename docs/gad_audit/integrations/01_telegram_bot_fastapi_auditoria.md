# Auditoría exhaustiva de la integración Telegram Bot + FastAPI para operaciones gubernamentales

Tipo de documento: Informe técnico de auditoría y diagnóstico operativo  
Audiencia: Equipos de arquitectura, seguridad, DevOps/SRE y liderazgo de operaciones gubernamentales  
Estilo: analítico, técnico, auditor (evidencia y trazabilidad), orientado a remediación, gobernanza y cumplimiento  
Idioma: español

## 1. Introducción y contexto operativo

Este informe audita de extremo a extremo la integración entre el Telegram Bot del sistema GRUPO_GAD y el backend FastAPI, bajo un enfoque de operación gubernamental. El objetivo es evaluar el flujo de comunicación bidireccional Telegram↔FastAPI, los patrones de sincronización operativa, el uso de asincronía y colas, la resiliencia ante fallos de red y errores del API de Telegram, la seguridad extremo a extremo, el desempeño y escalabilidad, las funcionalidades críticas, la observabilidad y las garantías de cumplimiento.

El alcance se centra en los siguientes planos:
- Arquitectónico: Topologías posibles (polling, webhook), sincronización de estado y contratos API.
- Asíncrono y de resiliencia: Patrones de concurrencia, backpressure, reintentos, circuit breaker y colas.
- Seguridad y cumplimiento: Autenticación/autorización, cifrado en tránsito, gestión de secretos, rate limiting y audit trail.
- Desempeño: Latencias y throughput en operaciones críticas, escalabilidad horizontal y uso de Redis.
- Operativo: Funcionalidades clave (crear/finalizar tareas, broadcasting, notificaciones anticipadas) y su robustez.
- Observabilidad: Métricas, logs, trazas, alertas y health checks.
- Gobierno del dato: Retención, minimización y controles de acceso.

Contexto de sistema y evidencia:
- Inventario de integraciones y arquitectura de referencia: repositorio GRUPO_GAD (python-telegram-bot, FastAPI, PostGIS, Redis, Prometheus/Grafana). [^1]
- Entorno productivo: despliegue en Fly.io (HTTPS, /health, /metrics). [^2]
- Marco de seguridad en comunicaciones móviles: guía de mejores prácticas de CISA (transporte cifrado, E2E cuando aplique, hardening y segmentación). [^3]

Supuestos y restricciones:
- El bot utiliza python-telegram-bot y se observan handlers, wizards y servicios de API. [^1]
- Existe integración con Redis (cache/pub-sub) y observabilidad con Prometheus/Grafana. [^1]
- Se dispone de endpoints FastAPI (/api/telegram_auth, /api/telegram_tasks, /api/usuarios) y esquemas Pydantic (telegram.py, usuario.py). [^1]
- La topología observada en el repositorio es polling. [^1]
- No hay evidencia documentada en el repositorio de topología por webhook con firma; por tanto, se asume como plan de refuerzo y no como estado actual.

Brechas de información (impactan el dictamen de preparación para go-live):
- No se evidencia implementación de “TAREA FINALIZADA” por voz ni flujo operativo documentado de liberación de efectivos. 
- No hay confirmación de cifrado en reposo ni políticas de retención/anonymización a nivel de base de datos/backups.
- No se observa persistencia del estado del wizard (conversación) en Redis (context.user_data en memoria). 
- Falta especificación de límites de rate limiting por integración (cuotas por usuario/IP/comando) y su instrumentación.
- No hay pruebas de carga específicas del bot (mensajes/min, bursts, colas) ni SLOs operativos.
- No se evidencia enforcement de TLS estricto ni pinning en clientes; no hay métricas del bot exportadas a Prometheus.
- No hay política formal de retención de logs/auditoría ni procedimiento de backup/restore del bot (tokens/config).

Tabla 1. Mapa de componentes y responsabilidades

| Componente | Ubicación (evidencia) | Responsabilidad principal | Tecnología | Notas operativas |
|------------|------------------------|---------------------------|------------|------------------|
| Telegram Bot | src/bot/ (repo) | Ingesta y UX del ciudadano: comandos, callbacks, wizard, teclados, orquestación con API | python-telegram-bot | Polling (repo); handlers asíncronos |
| Servicio API del Bot | services/api_service.py | Cliente hacia FastAPI para auth/tasks/usuarios | requests (sincrónico) | Requiere async y timeouts robustos |
| FastAPI Backend | app/api | Exposición de endpoints /api/telegram_* y dominio | FastAPI | Middlewares y seguridad (JWE/JWT) |
| Redis Cache/PubSub | core/cache.py, core/ws_pubsub.py | Cache y difusión cross-worker | Redis | Observabilidad y backpressure |
| Observabilidad | observability/metrics.py | Métricas y paneles | Prometheus/Grafana | /metrics en prod |
| Base de Datos | core/db + modelos | Persistencia de entidades | PostgreSQL/PostGIS | Conexiones y transacciones |
| Proxy/Ingress | Caddyfile/proxy | TLS y terminación HTTPS | Caddy | Certificados automáticos |
| Deployment | Fly.io prod | Salud, escalado, métricas | Fly | /health, /metrics, restart_policy |

## 2. Metodología y criterios de auditoría

La auditoría se realizó mediante revisión de la estructura y componentes referenciados del repositorio GRUPO_GAD, documentación de despliegue productivo en Fly.io y lineamientos de CISA. Se validaron puntos de integración bot↔FastAPI y la instrumentación de observabilidad.

Criterios de evaluación:
- Seguridad extremo a extremo (cifrado en tránsito, hardening TLS, gestión de secretos).
- Resiliencia (reintentos con backoff, circuit breaker, colas).
- Asincronía y backpressure (no bloqueo, control de recursos).
- Performance bajo carga (P95/P99, throughput, colas).
- Cumplimiento y trazabilidad (audit logging, retención, acceso mínimo).

Brechas y supuestos se listan en la introducción y condicionan recomendaciones y prioridades.

## 3. Análisis arquitectónico de la integración Telegram ↔ FastAPI

La integración examina topologías, contratos y sincronización. En el estado actual, se asume polling basado en el repositorio, con handlers asíncronos y un servicio de API sincrónico hacia FastAPI.

### 3.1 Flujo de comunicación y topologías

Polling vs Webhook:
- Estado observado: polling del Bot API con handlers registrados en python-telegram-bot. [^1]
- Ventajas del polling: simplicidad, ausencia de dependencia de conectividad entrante, facilidad de pruebas locales.
- Desventajas: mayor latencia de propagación, consumo de CPU por barrido, sensibilidad a bursts sin backpressure natural.

Topología webhook (plan recomendado):
- Establecer webhook de Telegram con firma y verificación HMAC a nivel de API Gateway (o directamente en FastAPI si se usa una ruta protegida) para asegurar autenticidad del origen y reducir latencia. 
- Ventajas: notificaciones push, menor latencia, mejor eficiencia de red y control de flujo a través del gateway.
- Endurecimiento: enforcement de TLS estricto, verificación de firma, rate limiting en el gateway, separación de redes (DMZ), aislamiento de recursos.

Tabla 2. Comparativa Polling vs Webhook

| Criterio | Polling (actual, observado) | Webhook (recomendado) |
|----------|------------------------------|-----------------------|
| Latencia | Mayor (depende del intervalo de poll) | Menor (evento push) |
| Complejidad | Baja | Media (verificación de firma, despliegue gateway) |
| Seguridad | Expuesta a polling no autenticado | Mejorable con verificación HMAC + TLS estricto |
| Costo de red | Mayor (barrido periódico) | Menor (evento) |
| Resiliencia | Menor control de bursts | Mejor con colas y backpressure del gateway |
| Observabilidad | Logs de poll y handlers | Logs de recepción, correlaciones por requestId |

Referencia a entornos productivos: /health y /metrics disponibles en Fly.io. [^2]

### 3.2 Sincronización y estado conversacional

- Estado actual: wizard en memoria (context.user_data) sin persistencia en Redis.
- Riesgo: en escalado horizontal, reinicios del bot o fallos de worker pierden estado conversacional, afectando continuidad de tareas.
- Recomendación: persistir estado del wizard en Redis (namespace “wizard:<chat_id>:<step>”) con TTL por paso (p. ej., 10–15 min) y limpieza tras confirmación/cancelación. Incluir idempotencia en operaciones (operación “Upsert” con claves operativas).

Tabla 3. Mapa de sincronización de estado

| Tipo de estado | Dónde reside | Persistencia | TTL | Observaciones |
|----------------|--------------|--------------|-----|---------------|
| Conversacional (wizard) | Memoria del bot (context.user_data) | No (evidencia) | No | Riesgo de pérdida en escalado o reinicio |
| Tareas operativas | Backend (DB) | Sí | N/A | Or truth para cambios de estado |
| Cache de usuarios | Redis | Sí | Configurable | Prefijos por dominio (“telegram:user:<id>”) |
| Difusión de eventos | Redis Pub/Sub | Sí | N/A | Cross-worker para broadcasting |
| Sesiones bot | Redis (recomendado) | Sí | Expiración definida | Recuperación ante failovers |

### 3.3 Asincronía y manejo de concurrencia

- El Bot usa handlers asíncronos de python-telegram-bot; el servicio hacia API es sincrónico (requests). [^1]
- Riesgo: Bloqueos de event loop por I/O, incremento de latencia bajo carga, saturación de workers ante bursts.
- Recomendación: Migrar el servicio API del bot a cliente asíncrono (HTTPX/httpx con asyncio) con timeouts por operación, cancelación cooperativa y límites de concurrencia por comando/callback (p. ej., semaforos). 
- Adoptar patrones “retry with jitter” y backpressure (limitar en vuelo por usuario/chat) para evitar sobrecarga del backend.

### 3.4 Resiliencia ante fallos de red/API de Telegram

Se proponen controles para degradación controlada inspirado en doctrina militar táctica: conservar funcionalidad esencial bajo restricciones de ancho de banda y latencia. [^4][^5]

- Reintentos con backoff exponencial y jitter; límites por operación.
- Circuit breaker por dependencia (API de Telegram, API de FastAPI, Redis).
- Degradación graciosa: mensajes mínimos, colas para entrega diferida, deshabilitar operaciones no críticas.
- Plan de continuidad: colas persistentes (Redis Streams) para “drain” posterior.

Tabla 4. Matriz de fallos y respuestas

| Tipo de fallo | Disparadores | Acción (reintento/backoff) | Alertas | Registro |
|---------------|--------------|-----------------------------|---------|---------|
| Timeout API Telegram | P95 > umbral | Backoff con jitter (max 3), abrir circuit breaker si persiste | Alerta al 2º intento | CorrelationId, usuario, comando |
| Error HTTP 5xx | HTTP 500/503 | Reintentos idempotentes, cambiar a cola | Pager si supera umbral | Endpoint, payload resumido |
| Error HTTP 4xx | 400/401/403 | No reintentar (salvo 429 con Retry-After) | Alerta de abuso | user_id, chat_id, causa |
| Redis no disponible | Conexión caída | Failover a cache local temporal, abrir circuito | Alerta crítica | operación afectada |
| Pérdida de red | TCP/SSL error | Pausa controlada y cola | Alerta por pérdida | Última confirmación |
| Bot reinicio | Crash/rollback | Rehidratar sesión Redis | Alerta por inestabilidad | Snapshot pre-crash |

Tabla 5. Matriz de resiliencia (QoS y degradación)

| severidad | operación afectada | estrategia | latencia objetivo | throughput mínimo | observabilidad |
|-----------|---------------------|-----------|-------------------|-------------------|----------------|
| Bajo | Historial / consulta | Cache + limitación | P95 < 500 ms | 95% aciertos cache | Hit/miss Redis |
| Medio | Crear tarea (wizard) | Reintentos + cola | P95 < 800 ms | ≥ 50 req/min | Latencia por paso |
| Alto | Finalizar tarea | Idempotencia + CB | P95 < 600 ms | ≥ 60 req/min | Errores por causa |
| Crítico | Notificación 40 min | Prioridad alta + DLQ | P95 < 400 ms | ≥ 100 notificaciones/5 min | Trazas y alertas |

### 3.5 Patrones de retry y fallback

- Reintentos con backoff exponencial y jitter para errores transitorios (timeouts, 5xx), con límites por operación y usuario.
- Circuit breaker (cerrado/abierto/semiabierto) por dependencia y por comando; permitir “half-open” con sondeos para recuperación.
- Cola temporal y DLQ (dead-letter queue) para mensajes no procesables; reintentos diferidos.

Tabla 6. Política de reintentos por operación

| Operación | Errores transitorios | Límite | Backoff | Idempotencia |
|-----------|----------------------|--------|---------|--------------|
| Finalizar tarea | 5xx/timeout | 3 | 200–800 ms + jitter | Clave: task_id + chat_id |
| Crear tarea | 5xx/timeout | 3 | 300–1200 ms + jitter | Upsert en backend |
| Notificaciones | 5xx/timeout | 5 | 500–2000 ms + jitter | MessageId único |
| Consultas | 5xx/timeout | 2 | 200–600 ms + jitter | Cache con TTL |

## 4. Seguridad en la integración Telegram

### 4.1 Autenticación y autorización

- Mecanismos base presentes: autenticación JWT/JWE en el backend y uso de listas blancas (WHITELIST_IDS/ADMIN_CHAT_ID). [^1][^2]
- Evaluación: whitelisting por usuario reduce riesgo, pero no sustituye políticas de autorización por rol/recurso; requiere pruebas de bypass y separación de privilegios.
- Recomendaciones:
  - Enforce de nivel de autorización por comando/rol (RBAC/ABAC) con auditoría de acceso.
  - Verificación adicional por hash/checksum del usuario Telegram con backend para asociar identidad técnica (telegram_id) a usuario operativo.
  - Rate limiting por usuario/IP/comando desde el gateway o middleware del bot.

Tabla 7. Controles de acceso por comando

| Comando/endpoint | Rol requerido | Verificación adicional | Auditoría | Riesgo residual |
|------------------|---------------|------------------------|-----------|-----------------|
| /finalizar_tarea | Ciudadano autorizado | Hash de usuario Telegram | Log de negocio | Medio |
| /crear_tarea | Ciudadano autorizado | Wizard completo | Log de negocio | Medio |
| /api/telegram_auth | Admin/Sistema | Token de servicio | Log de seguridad | Bajo |
| /api/telegram_tasks | Sistema | Permisos de servicio | Log técnico | Bajo |
| Broadcasting | Admin | Doble confirmación | Audit trail | Alto (si sin control) |

### 4.2 Cifrado en tránsito y protección contra MITM

- Estado actual: HTTPS con proxy (Caddy) y despliegue en Fly.io. [^2]
- Recomendaciones:
  - Forzar TLS estricto (min TLS 1.2+; preferible 1.3), deshabilitar suites débiles, habilitar HSTS.
  - Verificación de certificados en clientes; pinning opcional a largo plazo.
  - Segmentación de red (DMZ) y aislamiento de recursos para el webhook.

### 4.3 Gestión de secretos (tokens y claves)

- Evidencia: uso de TELEGRAM_TOKEN como variable de entorno. [^1]
- Recomendaciones:
  - Vault/Secrets Manager; rotación periódica; acceso mínimo y auditoría de lectura.
  - No persistir tokens en repositorios ni logs; escaneo automático de secretos en CI.

### 4.4 Rate limiting específico por integración

- Recomendado: Rate limiting por usuario/IP/comando (sliding window o token bucket).
- Persistencia en Redis para entornos multi-worker; instrumentación de métricas de rechazo y latencia de anti-abuso.

Tabla 8. Política de rate limiting

| Dimensión | Límite propuesto | Ventana | Acción al exceder | Excepciones | Observabilidad |
|-----------|-------------------|---------|-------------------|------------|----------------|
| Por usuario | 30 ops/min | 1 min | 429 + Retry-After | Admin | Contador rejections |
| Por IP | 120 ops/min | 1 min | 429 + ban temporal | N/A | Contador por IP |
| Por comando | 10 callbacks/min | 1 min | 429 | Operaciones críticas | Métrica por comando |
| Por chat | 60 mensajes/min | 1 min | Throttling | Canal oficial | Throughput por chat |

### 4.5 Endurecimiento del transporte y protección de datos

- Data minimization: guardar solo lo necesario; enmascarar datos sensibles en logs (PII).
- Control de retención en logs y auditoría; backups cifrados; políticas de borrado seguro.

## 5. Performance y escalabilidad

### 5.1 Throughput y latencia objetivo

- Definir SLOs por operación crítica (crear/finalizar tareas, notificaciones anticipadas).
- Instrumentación: histogramas de latencia, contadores de errores y colas (longitud, edad de mensajes).
- Observabilidad productiva existente en /metrics (Prometheus) y paneles (Grafana). [^2]

### 5.2 Gestión de bursts y backpressure

- Limitadores de concurrencia en el bot (semáforos por comando).
- Colas para spikes; amortiguación con Redis; degradación controlada inspirada en principios de redes tácticas (priorizar datos delay-intolerant y relajar restricciones cuando sea viable). [^4][^5]

### 5.3 Connection pooling y resource management

- Migración del servicio de API del bot a cliente asíncrono (HTTPX/httpx).
- Pooling de conexiones en FastAPI (ajustar límites por endpoint).
- Backpressure extremo a extremo: desde el Bot hacia Redis y el backend.

### 5.4 Impacto en FastAPI

- Middlewares de seguridad y límites de tamaño de payload; validación estricta de esquema con Pydantic.
- Profiling y tracing por endpoint; definición de P95/P99 y alertas sobre regresiones.

Tabla 9. Plan de pruebas de carga

| Operación | RPS objetivo | Latencia P95 | Latencia P99 | Tasa de error | Éxito de prueba |
|-----------|--------------|--------------|--------------|---------------|-----------------|
| Finalizar tarea | 20 | < 600 ms | < 900 ms | < 1% | 95% de escenarios |
| Crear tarea (wizard) | 15 | < 800 ms | < 1200 ms | < 1% | 95% de escenarios |
| Notificaciones 40 min | 50 notif/5 min | < 400 ms | < 700 ms | < 0.5% | 99% de entregas |
| Consultas | 50 | < 500 ms | < 800 ms | < 0.2% | 98% de cache hit |

Tabla 10. Escalabilidad horizontal por componente

| Componente | Instancias objetivo | Factor de escala | Límites | Dependencias |
|------------|---------------------|------------------|---------|--------------|
| Bot Telegram | N ≥ 2 | CPU > 70% | Máx. conexiones | Redis, API |
| API FastAPI | N ≥ 2 | Latencia P95 | Pool de DB | DB, Redis |
| Redis | 1–2 (cluster) | Memoria < 75% | Evicción controlada | Persistencia |
| Observabilidad | 1 | Uptime > 99.9% | /metrics | Scraping |

Tabla 11. Conexiones y recursos

| Servicio | Conexiones máx. | Pool | Timeouts | Retries |
|----------|------------------|------|----------|---------|
| Bot → API | 100 por worker | N/A | 1–3 s | 2–3 con jitter |
| API → DB | 50–100 por servicio | 10–20 | 5–10 s | N/A |
| Bot → Redis | 50 por worker | N/A | 500 ms | 1–2 |
| Webhook Gateway | 200 | N/A | 5 s | 1 |

Tabla 12. SLOs por operación crítica

| Operación | Objetivo de latencia | Throughput | Disponibilidad | Observabilidad |
|-----------|-----------------------|------------|----------------|----------------|
| Finalizar | P95 < 600 ms | ≥ 60/min | 99.9% | Latencia, errores |
| Crear | P95 < 800 ms | ≥ 50/min | 99.9% | Pasos de wizard |
| Notificación | P95 < 400 ms | ≥ 100/5 min | 99.9% | Entrega y DLQ |

## 6. Funcionalidades operativas críticas del bot

### 6.1 “TAREA FINALIZADA” y liberación de efectivos

- Estado actual: “finalizar_tarea.py” existe; no se evidencia flujo por voz ni orquestación de liberación de efectivos. [^1]
- Evaluación: riesgo si “finalización” se interpreta como operación operativa sin validación de autorización/estado.
- Recomendación: 
  - Comando operativo “TAREA FINALIZADA” con doble confirmación y verificación por backend (idempotencia).
  - Decidir si voz está habilitada; si no, restrictivo a texto con teclado inline.
  - Orquestación de “liberación de efectivo” vía endpoint /api/telegram_tasks (o endpoint específico) con auditoría de negocio.

Tabla 13. Mapa de comandos operativos

| Comando | Precondiciones | Endpoint/API | Validaciones | Riesgos | Observabilidad |
|---------|----------------|--------------|--------------|---------|----------------|
| TAREA FINALIZADA | Wizard completo, usuario autorizado | /tasks/finalize | Idempotencia (task_id+chat_id) | Uso indebido | Latencia y errores |
| Liberar efectivo | Tarea finalizada válida | /tasks/release | Estado de tarea | Inconsistencia estado | Audit trail |
| Broadcasting | Permiso admin | /broadcast | Doble confirmación | Exceso difusión | Métrica por envío |
| Notificación 40 min | Scheduler activo | /notify-40 | Prioridad alta | Pérdida de entrega | DLQ y reintentos |

### 6.2 Broadcasting de comandos operativos

- Recomendaciones:
  - Protección por roles (RBAC) y doble confirmación.
  - Colas para evitar saturación; tracking de entrega y reintentos.
  - Auditoría: quién, qué, cuándo y a qué audiencia.

### 6.3 Notificaciones 40 minutos antes

- Diseño:
  - Scheduler/worker con cola (Redis Streams).
  - Reintentos y DLQ; métricas de latencia de entrega.
  - Degradación controlada (prioridad alta, mensajería mínima) bajo congestión.

Tabla 14. Plan de notificaciones

| Trigger | Destinatarios | Plantilla | SLA | Reintentos | Observabilidad |
|---------|---------------|-----------|-----|------------|----------------|
| T-40 min | Usuario/efectivo | Texto mínimo | P95 < 400 ms | 3 con jitter | Entrega y DLQ |
| T-10 min | Usuario/efectivo | Recordatorio | P95 < 300 ms | 2 | Trazas |
| Fallo de entrega | Admin | Alerta | Inmediato | 1 | Alerta operativa |

### 6.4 Sincronización de estados operativos

- Reglas y fuentes de verdad; manejo de race conditions con locks por clave (Redis) y “Upsert” idempotente en backend.
- Reintentos y reconciliación por diferencia.

### 6.5 Wizard multi-step y escalabilidad

- Persistir estado en Redis; TTL por paso; limpieza al finalizar.
- Migrar servicio API a cliente asíncrono; backpressure para evitar sobrecarga en bursts.

## 7. Monitoreo y observabilidad

- Instrumentación: métricas del bot (contadores por comando/callback, histogramas de latencia, colas, errores), logs estructurados con correlation IDs.
- Dashboards: rendimiento API, WebSockets y Redis; alertas por errores, latencias y saturación de colas.
- Health checks específicos: bot↔API, bot↔Redis, API↔DB.

Tabla 15. Métricas clave del bot

| Métrica | Tipo | Etiquetas | Objetivo | Umbral de alerta |
|---------|------|-----------|----------|------------------|
| bot_commands_total | Counter | comando, resultado | Crecimiento estable | > 5% errores/día |
| bot_callback_latency | Histogram | callback, paso | P95 < 600 ms | P99 > 1200 ms |
| bot_queue_length | Gauge | cola | < 100 | > 300 (5 min) |
| bot_retry_ops | Counter | operación | Minimizar | > 50/h |
| api_request_errors | Counter | endpoint, código | < 1% | > 3% |

Tabla 16. Catálogo de logs de comunicación

| Evento | Nivel | Contexto | Retención | Protección de datos |
|--------|-------|----------|-----------|---------------------|
| Recepción de comando | Info | chat_id, user_id, comando | 90 días | Enmascarar PII |
| Callback de wizard | Info | chat_id, paso | 90 días | Enmascarar PII |
| Error de API | Warn/Error | endpoint, código | 180 días | No persistir payload completo |
| Notificación enviada | Info | message_id, destino | 180 días | Hash de destinatario |
| Alerta de resiliencia | Error | dependencia | 365 días | Correlación y auditoría |

Tabla 17. Reglas de alerta

| Señal | Condición | Severidad | Canal | Tiempo de respuesta |
|-------|-----------|-----------|-------|---------------------|
| P95 alta | P95 > umbral 3 min | Alta | Pager | 15 min |
| Tasa error | > 3% por 5 min | Alta | Pager | 15 min |
| Cola saturada | Longitud > 300 | Media | Slack | 30 min |
| Redis down | Conexión fallida | Crítica | Pager | 5 min |
| Reintentos excesivos | > 50/h | Media | Slack | 30 min |

Referencia: endpoints de métricas y despliegue productivo en Fly.io. [^2]

## 8. Gestión de errores y recovery

- Timeouts en API Telegram/FastAPI: límites por operación y mensajes de error accionables.
- Recuperación ante pérdida de conectividad: reintentos diferidos, colas, sincronización de estados y reintentos idempotentes.
- Circuit breaker: estados (cerrado, abierto, semiabierto) con sondeos de recuperación y métricas asociadas.
- Degradación graciosa: desactivar funciones no críticas y priorizar entrega de notificaciones/operaciones esenciales, alineado con principios tácticos. [^4][^6][^7][^8][^5]

Tabla 18. Matriz de manejo de errores

| Código/causa | Acción | Reintentos | Mensaje usuario | Auditoría | Observabilidad |
|--------------|--------|------------|-----------------|-----------|----------------|
| 408/Timeout | Backoff + jitter | 2–3 | “Reintento en curso” | CorrelationId | Latencia |
| 500/503 | Circuit breaker | N/A | “Servicio no disponible” | Endpoint | Error rate |
| 401/403 | No retry | 0 | “Sin permisos” | user_id | Security log |
| 404 | No retry | 0 | “Recurso no encontrado” | task_id | Evento |
| 429 | Retry-After | 1 | “Demasiadas solicitudes” | user/IP | Rate limit |

Tabla 19. Configuración de circuit breaker

| Dependencia | Umbral de apertura | Tiempo en abierto | Sondeos en semiabierto | Métricas |
|-------------|---------------------|--------------------|------------------------|----------|
| API Telegram | P95 > 800 ms (3 min) | 60 s | 5 requests | Fallos y latencia |
| API FastAPI | Tasa error > 3% | 30 s | 10 requests | Errores por endpoint |
| Redis | 2 fallos consecutivos | 30 s | 3 pings | Conexiones |

## 9. Cumplimiento gubernamental y auditoría

- Audit logging integral: registro de operaciones de negocio (quién, qué, cuándo, sobre qué) con trazabilidad.
- Cumplimiento de mensajería electrónica: alineamiento con requisitos de seguridad, retención y transparencia propios del sector público. [^9]
- Políticas de retención y minimización de datos personales (PII), accesos restringidos y separación de funciones.
- Backup y recuperación de configuraciones/secrets; procedimientos probados.

Tabla 20. Matriz de cumplimiento

| Control | Estado | Evidencia | Riesgo | Acción correctiva |
|---------|--------|----------|--------|-------------------|
| Cifrado en tránsito | Parcial | HTTPS en proxy | MITM si mal configurado | TLS estricto, HSTS |
| Gestión de secretos | Parcial | Variables de entorno | Exposición accidental | Vault y rotación |
| Audit trail | Parcial | Logs de app | Falta trazabilidad | Logs de negocio |
| Retención de datos | No evidenciado | N/A | Cumplimiento | Política formal |
| Acceso mínimo | Parcial | Roles definidos | Sobrecarga privilegios | RBAC/ABAC |

Tabla 21. Plan de retención y acceso

| Tipo de dato | Retención | Base legal | Acceso | Medidas de seguridad |
|--------------|-----------|------------|--------|----------------------|
| Logs de bot | 90–180 días | Seguridad operativa | Sec/Admin | Enmascarar PII |
| Audit logs | 1–3 años | Trazabilidad | Auditoría | WORM/alcance |
| Datos de tarea | Según normativa | Misión | Operadores | Cifrado y RBAC |
| Configuración | Mientras vigente | Operación | Admin | Vault y cifrado |

## 10. Conclusiones y recomendaciones priorizadas

Síntesis de hallazgos clave:
- Arquitectura: polling vigente; handlers asíncronos; servicio API sincrónico; sin persistencia de wizard en Redis.
- Seguridad: whitelisting y JWT presentes; falta enforcement de TLS estricto documentado; rate limiting por integración no evidenciado; secrets gestionados por entorno sin rotación formal.
- Performance: sin pruebas de carga específicas; sin SLOs operativos del bot; observabilidad en /metrics; falta métricas específicas del bot.
- Funcionalidades: comandos clave presentes; no hay evidencia de “TAREA FINALIZADA” por voz ni flujo de liberación de efectivos; notificaciones 40 min sin diseño operativo documentado.
- Resiliencia: sin políticas formales de retry/jitter, circuit breaker y colas; sin DLQ documentada.
- Cumplimiento: audit trail parcial; retención y minimización no evidenciadas; backups cifrados y procedimientos no probados.

Riesgos principales y impacto:
- Seguridad: exposición a MITM si TLS no es estricto; riesgo de abuso sin rate limiting; fuga de secretos por prácticas no centralizadas.
- Operativo: pérdida de estado conversacional en escalado; latencias bajo bursts; ausencia de degradación controlada.
- Cumplimiento: trazabilidad insuficiente y retención indefinida o no controlada; accesos sin “mínimo privilegio”.

Recomendaciones priorizadas (60–90–180 días) en cuatro fases:

Fase 1 (0–60 días) – Mejoras críticas de seguridad y observabilidad:
- Forzar TLS estricto en proxy/gateway y clientes; habilitar HSTS; documentar configuración.
- Instrumentar métricas específicas del bot y paneles; habilitar alertas críticas (P95/P99, errores, colas, reintentos).
- Introducir límites de rate limiting por usuario/IP/comando (Redis).
- Migrar el servicio API del bot a cliente asíncrono; añadir timeouts robustos y reintentos con jitter.
- Establecer circuit breaker por dependencia (Telegram API, FastAPI, Redis) con sondeos.

Fase 2 (60–90 días) – Resiliencia operativa:
- Persistir estado de wizard en Redis con TTL; limpieza automática y recuperación ante reinicios.
- Diseñar e implementar colas para notificaciones 40 min (Redis Streams) y broadcasting.
- Definir SLOs operativos por operación crítica (crear/finalizar tareas, notificaciones); iniciar pruebas de carga.
- Consolidar procedimientos de backup/restore y cifrado de backups; política de retención y minimización.

Fase 3 (90–120 días) – Seguridad y gobernanza:
- Centralizar secretos en Vault/Secrets Manager; rotación documentada; escaneo de secretos en CI.
- Fortalecer RBAC/ABAC por comando y rol; pruebas de bypass y auditoría de acceso.
- Diseñar y ejecutar pruebas de carga, resiliencia y chaos; validar degradación graciosa y recovery.

Fase 4 (120–180 días) – Gobierno y cumplimiento:
- Audit trail integral de negocio con WORM/alcance para registros críticos.
- Formalizar política de retención y acceso mínimo; separación de funciones.
- Revisión de cumplimiento con requisitos de mensajería gubernamental (evaluaciones internas y auditorías externas). [^9]

Tabla 22. Backlog de remediación priorizado

| Acción | Riesgo mitigado | Fase | Responsable | Dependencias | Métrica de éxito |
|--------|------------------|------|-------------|--------------|------------------|
| TLS estricto + HSTS | MITM | 1 | Sec/Platform | Proxy | 0 errores TLS |
| Métricas/alertas del bot | Ceguera operativa | 1 | SRE/Obs | /metrics | Alertas efectivas |
| Rate limiting (Redis) | Abuso | 1 | Sec/Dev | Redis | < 1% rejections |
| Cliente API async | Bloqueos | 1 | Backend | HTTPX | P95 mejora 30% |
| Circuit breaker | Cascadas | 1 | Backend | N/A | Reducción fallos 50% |
| Wizard en Redis | Pérdida estado | 2 | Backend | Redis | 0 pérdidas sesión |
| Colas y DLQ | Pérdida msg | 2 | SRE/Backend | Redis Streams | DLQ < 0.5% |
| SLOs + pruebas carga | Incertidumbre | 2–3 | SRE/QA | Entorno de test | SLOs cumplidos |
| Vault + rotación | Fuga secretos | 3 | Sec/Platform | CI/CD | Rotación OK |
| Audit trail WORM | Trazabilidad | 4 | Compliance | Logs | Auditoría OK |

Métricas de éxito:
- Reducción de errores 4xx/5xx en endpoints críticos ≥ 50%.
- P95 de finalizar tarea < 600 ms y P99 < 900 ms.
- 0 pérdidas de estado de wizard en reinicios y escalado.
- 0 incidentes de fuga de secretos; 100% cobertura de rotación.
- 0 breaches de cumplimiento (auditoría sin hallazgos críticos).

## Referencias

[^1]: GRUPO_GAD - Repositorio (GitHub). URL: https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD - Aplicación en Producción (Fly.io). URL: https://grupo-gad.fly.dev  
[^3]: Mobile Communications Best Practice Guidance - CISA (PDF). URL: https://www.cisa.gov/sites/default/files/2024-12/guidance-mobile-communications-best-practices.pdf  
[^4]: Army Tactical Network Quality of Service and Graceful Degradation Concept - Cyber Defense Review. URL: https://cyberdefensereview.army.mil/CDR-Content/Articles/Article-View/Article/1134643/army-tactical-network-quality-of-service-and-graceful-degradation-concept/  
[^5]: Tactical Communications for Ground-Based Air Defense (GBAD) - Bittium (2025) (PDF). URL: https://www.bittium.com/wp-content/uploads/2025/05/Bittium-Tactical-Communications-for-Ground-Based-Air-Defense.pdf  
[^6]: Circuit Breaker Pattern - Azure Architecture Center. URL: https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker  
[^7]: Circuit Breaker - Martin Fowler. URL: https://martinfowler.com/bliki/CircuitBreaker.html  
[^8]: Circuit Breaker Pattern (Design Patterns for Microservices) - Medium. URL: https://medium.com/geekculture/design-patterns-for-microservices-circuit-breaker-pattern-276249ffab33  
[^9]: Electronic Messaging Compliance Assessment Toolkit - NARA (DOCX). URL: https://www.archives.gov/files/records-mgmt/policy/electronic-messaging-compliance-assessment-toolkit.docx