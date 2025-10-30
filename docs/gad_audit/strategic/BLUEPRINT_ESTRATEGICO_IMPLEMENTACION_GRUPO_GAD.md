# Blueprint Estratégico de Implementación para GRUPO_GAD

## 0. Portada y Resumen Ejecutivo

Este blueprint define la hoja de ruta integral para consolidar la plataforma de GRUPO_GAD como un sistema gubernamental robusto, seguro, conforme y altamente operable, con escalabilidad probada y métricas de servicio claras. El diagnóstico se basa en tres auditorías técnicas que cubren seguridad de JSON Web Tokens (JWT), integración del Telegram Bot con FastAPI y cumplimiento gubernamental del canal ciudadano[^1][^2][^3]. En conjunto, evidencian un sistema funcional con fortalezas en arquitectura base y observabilidad, pero con brechas críticas que impiden la operación en producción con garantías de seguridad, resiliencia y compliance.

En seguridad de autenticación, el sistema presenta un “Security Score” de 6.2/10. Se identifican vulnerabilidades críticas: ausencia de refresh tokens, falta de rotación automatizada de claves, inexistencia de lista de revocación, expiración de tokens del Telegram Bot demasiado larga (7 días) y ausencia de claims estándar en JWT (iat, nbf, jti), así como inconsistencias en variables de entorno (SECRET_KEY y JWT_SECRET_KEY). Estas brechas elevan el riesgo de reutilización de tokens, ataques de replay, pérdida de trazabilidad y abuso del canal, y exigen remediación inmediata[^2].

En la integración Telegram Bot ↔ FastAPI, se observa el uso de handlers asíncronos y un servicio de API sincrónico que produce bloqueos de I/O, además de estado conversacional del wizard en memoria sin persistencia (context.user_data), lo que implica pérdida de sesión ante reinicios o escalado horizontal. Se recomienda migración a webhook con verificación HMAC, cliente HTTP asíncrono (HTTPX), persistencia del wizard en Redis con TTL y circuit breaker por dependencia para evitar cascadas de fallos[^2]. Asimismo, la capa de observabilidad y métricas específicas del bot requiere fortalecimiento para detectar degradaciones y picos de latencia[^2].

En cumplimiento gubernamental, persisten vacíos relevantes: cifrado en reposo no verificado en base de datos y backups, audit trail incompleto (particularmente de operaciones del bot), rate limiting in-memory sin persistencia multi-worker y ausencia de políticas de retención, borrado seguro y controles de acceso basados en roles/atributos (RBAC/ABAC). La adopción de principios de mensajes electrónicos del sector público, alineados con marcos de cumplimiento y guías operativas, resulta necesaria para auditoría y certificación[^3][^4].

Visión a largo plazo (12–24 meses): posicionar a GRUPO_GAD como la plataforma gubernamental de referencia en seguridad, cumplimiento y resiliencia, con operación 24/7, gobernanza de datos sólida y diferenciación tecnológica basada en controles estrictos de transporte y sesión (OAuth 2.0/OpenID Connect), observabilidad end-to-end y automatización operativa.

Resultados esperados:
- Seguridad JWT: adopción de refresh tokens con rotación, claims estándar y lista de revocación (JTI) con Redis; reducción de expiración de tokens del bot a 24 horas; hardening de transporte (TLS/HSTS); validación de fortaleza de claves; orquestación de rotación con ventana de gracia multi-instancia[^1][^2][^5][^6].
- Integración Bot ↔ API: migración de polling a webhook con verificación HMAC, cliente asíncrono, circuit breaker por dependencia, colas y dead-letter queue (DLQ), y degradación controlada bajo escenarios adversos[^1][^2][^7][^8][^9].
- Compliance: verificación de cifrado en reposo en BD y backups, logging de auditoría con alcance “quién, qué, cuándo, sobre qué” y retención formal, RBAC/ABAC, política de retención y acceso mínimo; alineación con requisitos de mensajería gubernamental[^4].
- Performance y escalabilidad: definición de SLOs por operación, pruebas de carga, tuning de paginación, backpressure en el bot y escalado de instancias; instrumentación de métricas y alertas de latencia, errores y colas[^1][^2].
- Madurez operativa: automatización de despliegue y despliegue sin tiempo de inactividad, gestión de incidentes y continua mejora; consolidación de runbooks y simacros ( tabletop exercises) de DR y continuidad[^2][^7][^9][^4].

KPIs críticos:
- Seguridad: Security Score JWT ≥ 9.0/10; tiempo de revocación de token < 100 ms; rotación de claves con éxito ≥ 99.9% mensual; incidentes críticos de seguridad = 0/mes[^2].
- Integración: latencia P95 en finalizar tarea < 600 ms; P99 < 900 ms; errores de endpoints críticos < 1%; pérdidas de sesión del wizard = 0 tras reinicios; DLQ < 0.5%[^2].
- Compliance: cobertura de audit logging ≥ 95% de operaciones críticas; verificación completa de cifrado en reposo; retención y minimización de datos implementadas y auditadas[^4].
- Desempeño: cumplimiento de SLOs ≥ 99% mensual; 0 pérdidas de estado del wizard; reducción de errores 4xx/5xx ≥ 50%[^2].

Este documento establece la visión, objetivos, roadmaps, inversiones y gobernanza para alcanzar la madurez operativa y de seguridad requerida en 12–24 meses, reduciendo sustancialmente el riesgo y elevando el nivel de confianza institucional.

## 0.1 Visión y Objetivos Estratégicos

La visión se ancla en cuatro pilares: seguridad extrema (autenticación, autorización, transporte y revocación), cumplimiento normativo (cifrado, auditoría, retención, acceso mínimo), resiliencia (degradación controlada, circuit breaker, colas/DLQ) y excelencia operativa (observabilidad, automatización, DR). Los objetivos estratégicos se derivan directamente de los hallazgos de auditoría:

- Seguridad de autenticación:
  - Implementar refresh tokens con rotación y revocación basada en JTI (JWT ID).
  - Completar claims estándar (iat, nbf, jti, iss, aud) y validar fortaleza de claves (≥ 256 bits).
  - Reducir expiración de tokens del bot a 24 horas; orquestar rotación de claves con ventana de gracia.
  - Centralizar la gestión de secretos (Vault/Secrets Manager) con rotación documentada[^2].

- Integración Bot ↔ API:
  - Migrar de polling a webhook con verificación HMAC/TLS estricto; reducir latencia y mejorar autenticidad del origen.
  - Migrar el cliente de API del bot a HTTPX asíncrono; introducir circuit breaker por dependencia y DLQ para resiliencia.
  - Persistir el estado del wizard en Redis con TTL y namespace; garantizar continuidad de sesión en escalado[^2][^7][^8][^9].

- Compliance:
  - Verificar y activar cifrado en reposo en BD y backups; instrumentar audit logging integral de operaciones del bot y de negocio.
  - Establecer políticas de retención y minimización; formalizar RBAC/ABAC y separación de funciones; preparar auditoría externa[^4].

- Performance y escalabilidad:
  - Definir y medir SLOs por operación crítica; realizar pruebas de carga y tuning de paginación.
  - Implementar backpressure en el bot, límites de concurrencia por comando y escalado de instancias de bot/API/Redis[^1][^2].

- Excelencia operativa:
  - Integrar métricas específicas del bot en Prometheus/Grafana; alarmas de P95/P99, colas y errores; runbooks y simacros de DR.
  - Endurecer TLS/HSTS, pin证书 opcional, segmentación de red y gate de seguridad en CI/CD[^2][^5][^6].

Definición de metas cuantitativas:
- Seguridad: Score JWT ≥ 9.0; cobertura de refresh tokens 100%; revocación < 100 ms; rotación mensual con tasa de éxito ≥ 99.9%; incidentes críticos = 0/mes.
- Integración: P95 finalizar tarea < 600 ms; P99 < 900 ms; pérdidas de sesión wizard = 0; DLQ < 0.5%.
- Compliance: audit logging ≥ 95% de operaciones críticas; cifrado en reposo verificado en BD y backups; retención y acceso mínimo implementados.
- Operacional: cumplimiento de SLOs ≥ 99% mensual; errores 4xx/5xx reducidos ≥ 50% en 90 días; cobertura de pruebas ≥ 85% incluyendo carga/resiliencia.

Gobernanza de ejecución:
- Comité Directivo: prioridades y decisiones críticas.
- Oficina de Gestión de Proyectos (PMO): ritmo operativo y dependencias inter-áreas.
- Arquitectura, Seguridad, SRE/DevOps y Compliance: diseño e implementación end-to-end con criterios de aceptación y medición.

Este blueprint se sustenta en evidencia del repositorio oficial, el entorno productivo y guías regulatorias y técnicas de referencia[^1][^2][^4][^5][^6][^7][^8][^9][^10][^11].

## 1. Estrategia de Tecnología

La estrategia tecnológica consolida acciones para cerrar brechas de seguridad en JWT y fortalecer la integración del Telegram Bot con el backend, al tiempo que mejora la observabilidad y prepara al sistema para crecimiento sostenido. La hoja de ruta se estructura en tres horizontes (0–60, 60–90, 90–180 días) y se basa en soluciones probadas que mitigan los riesgos identificados.

### 1.1 Consolidación de Recomendaciones de JWT

La remediación de autenticación es prioritaria por su impacto transversal en seguridad y cumplimiento. Se propone:

- Implementar refresh token flow:
  - Refresh tokens con expiración moderada (30 días) y rotación en cada uso; invalidación del refresh token previo al emitir uno nuevo.
  - Persistencia de refresh tokens y su estado (activo, revocado) para auditoría y control.
  - Endpoint de revocación por usuario y por token (JTI), con respuesta de revocación en milisegundos (objetivo < 100 ms).

- Claims estándar y validación:
  - Incorporar iat (issued at), nbf (not before), jti (JWT ID único) e información de iss (issuer) y aud (audience).
  - Validar fortaleza de clave (≥ 256 bits) y normalizar variables de entorno para evitar duplicidad y confusión (SECRET_KEY vs JWT_SECRET_KEY).

- Reducción de expiración de Telegram Bot:
  - Expiración de tokens del bot de 7 días es excesiva; reducir a 24 horas como máximo, con claims estándar y JTI único para revocación.
  - Implementar re-autenticación periódica y rotación de tokens del bot (diarios o por evento).

- Lista de revocación basada en JTI:
  - Usar Redis para almacenar JTI revocado con TTL acorde a la expiración del token.
  - Validar JTI en cada solicitud para rechazar tokens revocados, con impacto mínimo en latencia.

- Automatización de rotación de claves:
  - Orquestar rotación de claves cada 90 días; mantener clave previa durante ventana de gracia (24 horas).
  - Coordinación multi-instancia para evitar inconsistencias y asegurar decodificación de tokens firmados con clave anterior durante el periodo de gracia.

- Validación de fortaleza de secretos:
  - Enforcement en runtime de longitud mínima y entropía; integración con Vault/Secrets Manager.
  - Auditoría de lecturas de secretos y escaneo automático de secretos en CI/CD.

Estas medidas son consistentes con mejores prácticas de seguridad en plataformas gubernamentales y controles de transporte y autenticación recomendados por guías técnicas[^2][^5][^6].

### 1.2 Integración Telegram Bot ↔ FastAPI

La estrategia de integración persigue menor latencia, mayor resiliencia y mejor control de flujo.

- Migración de polling a webhook:
  - Establecer webhook de Telegram con verificación HMAC a nivel de gateway/API.
  - Endurecimiento del transporte (TLS estricto, HSTS) y segmentación de red (DMZ) para aislamiento de recursos.

- Cliente HTTP asíncrono y control de concurrencia:
  - Migrar el servicio de API del bot a HTTPX (async) con timeouts robustos por operación y límites de concurrencia por comando (semáforos).
  - Reintentos con jitter para errores transitorios, y circuit breaker por dependencia (Telegram API, FastAPI, Redis) para prevenir cascadas[^7][^8][^9].

- Persistencia de estado de wizard en Redis:
  - Usar namespace “wizard:<chat_id>:<step>” con TTL por paso (10–15 minutos), limpieza automática tras confirmación/cancelación.
  - Idempotencia en operaciones de negocio (Upsert con clave operativa) para evitar duplicaciones y estados inconsistentes.

- Colas y DLQ:
  - Redis Streams para notificaciones críticas y broadcasting; DLQ para mensajes no procesables.
  - Métricas de longitud de cola y edad de mensajes; alertas cuando se superen umbrales.

Esta hoja de ruta se alinea con la evidencia del repositorio oficial (estructura del bot, handlers asíncronos, uso de Redis y observabilidad) y el entorno productivo que expone endpoints de salud y métricas[^1][^2].

Para guiar la implementación y clarificar decisiones, se presentan las siguientes tablas.

Para ilustrar la consolidación tecnológica y los riesgos mitigados, se incluye la Matriz de Recomendaciones Tecnológicas (Tabla 0). Esta tabla detalla la fuente del hallazgo, la recomendación concreta, el riesgo mitigado, el esfuerzo estimado y el impacto operativo.

Tabla 0. Matriz de Recomendaciones Tecnológicas

| Fuente de hallazgo | Recomendación | Riesgo mitigado | Esfuerzo | Impacto |
|--------------------|---------------|-----------------|----------|---------|
| Auditoría JWT (sin refresh tokens, sin JTI) | Implementar refresh tokens con rotación; JTI; claims estándar; revocación en Redis | Reutilización, replay, abuso de sesión | Alto | Alto |
| Expiración de tokens del bot (7 días) | Reducir a 24h; incorporar claims estándar; re-autenticación periódica | Abuso prolongado del canal y tokens comprometidos | Medio | Alto |
| Rotación de claves (solo documental) | Orquestación con ventana de gracia multi-instancia | Inconsistencias y caída de autenticación | Medio | Alto |
| Secret management (variables de entorno) | Centralización en Vault; validación de fortaleza; rotación documentada | Fuga de secretos; claves débiles | Medio | Alto |
| Polling en bot | Webhook con verificación HMAC y TLS estricto | Latencia alta; falta de autenticidad del origen | Medio | Alto |
| Cliente API sincrónico | Migrar a HTTPX async; timeouts robustos | Bloqueos de I/O; latencia bajo carga | Medio | Alto |
| Wizard en memoria | Persistir en Redis con TTL e idempotencia | Pérdida de sesión en escalado/reinicios | Medio | Alto |
| Falta de circuit breaker | Implementar breaker por dependencia | Cascadas de fallos; saturación | Bajo | Medio |
| Colas no evidenciadas | Redis Streams + DLQ para notificaciones/broadcasting | Pérdida de mensajes; falta de resiliencia | Medio | Alto |
| Observabilidad específica del bot | Instrumentar métricas y paneles en Prometheus/Grafana | Ceguera operativa; detección tardía | Bajo | Medio |
| Rate limiting in-memory | Persistir límites en Redis; métricas de rechazo | Bypass por multi-worker; abuso | Medio | Medio |
| TLS/HSTS no enforced | Endurecer TLS; HSTS; pinning opcional | MITM; degradación de transporte | Bajo | Medio |

Para visualizar el impacto en el tiempo, se presenta el Roadmap de Migraciones Tecnológicas por horizonte.

Tabla 1. Roadmap de Migraciones Tecnológicas (0–60, 60–90, 90–180 días)

| Horizonte | Iniciativa | Entregable | Dependencias | Riesgos | Métrica de éxito |
|-----------|------------|------------|--------------|---------|------------------|
| 0–60 días | Refresh tokens + JTI + claims estándar | Endpoints de refresh/revoke; DB/Redis de tokens | Seguridad JWT; Redis | Compatibilidad con clientes | Respuesta de revocación < 100 ms |
| 0–60 días | Reducción de expiración bot (24h) | Configuración y políticas de tokens del bot | Seguridad JWT | Impacto en UX | 0 incidentes de tokens prolongados |
| 0–60 días | Webhook con HMAC + TLS/HSTS | Gateway configurado; verificación | Platform/DevOps | Cambios en despliegue | Latencia de notificación P95 < 400 ms |
| 0–60 días | Cliente API HTTPX async | Migración y pruebas de carga | Backend | Introducción de regresiones | P95 mejorar ≥ 30% en endpoints críticos |
| 0–60 días | Rate limiting con Redis | Middleware/límites por usuario/IP/comando | Redis | Errores de cuota | Rechazos instrumentados < 1% |
| 60–90 días | Wizard en Redis (TTL, namespace) | Persistencia y limpieza automática | Redis | Saturación de keys | Pérdidas de sesión = 0 |
| 60–90 días | Colas y DLQ (Redis Streams) | Worker y DLQ; métricas | Redis | Gestión de picos | DLQ < 0.5% |
| 60–90 días | Circuit breaker por dependencia | Configuración y sondeos | Backend | Falsos positivos/negativos | Reducción de fallos ≥ 50% |
| 90–180 días | Vault/Secrets Manager + rotación | Integración en CI/CD; auditoría | Platform/Sec | Cambios culturales | Rotación OK en 100% de secretos |
| 90–180 días | Observabilidad bot (métricas/paneles) | Dashboards y alertas | SRE/Obs | Ruido de alertas | Cobertura de alertas ≥ 95% |
| 90–180 días | Pruebas de carga/resiliencia | Suite y reportes | SRE/QA | Entorno de test | Cumplimiento SLOs ≥ 99% |

Para optimizar la operación, se presenta el Inventario de Componentes y Optimizaciones.

Tabla 2. Inventario de Componentes y Optimizaciones

| Componente | Recurso | Límite actual | Optimización propuesta | Resultado esperado |
|------------|---------|---------------|------------------------|--------------------|
| Bot Telegram | Polling + handlers asíncronos | Latencia mayor; sin autenticidad de origen | Webhook + HMAC; TLS estricto | Menor latencia, mejor seguridad |
| Bot → API | Cliente sincrónico (requests) | Bloqueos I/O; timeouts no robustos | HTTPX async; timeouts; límites de concurrencia | Mejora de P95/P99; control de flujo |
| Wizard | context.user_data en memoria | Pérdida de sesión en reinicios | Persistencia en Redis con TTL | Continuidad de sesión; idempotencia |
| Redis | Cache/PubSub | Sin DLQ; métricas parciales | Streams; DLQ; métricas de colas | Resiliencia y trazabilidad |
| Observabilidad | /metrics generales | Sin métricas específicas del bot | Instrumentación de comandos/callbacks | Visibilidad operativa |
| Rate limiting | In-memory | Bypass por multi-worker | Redis; etiquetas por usuario/IP/comando | Control anti-abuso consistente |

#### 1.2.1 Refresh Tokens, JTI y Claims Estándar

El refresh token flow es el mecanismo central para continuidad de sesión segura. El diseño propuesto contempla:

- Rotación de refresh tokens:
  - Emisión de refresh token con expiración moderada (30 días).
  - Rotación en cada uso: emisión de nuevo refresh token e invalidación del anterior.
  - Persistencia de estado (activo, revocado) para trazabilidad y respuesta rápida.

- JTI y lista de revocación:
  - Asignación de jti a cada token (access y refresh).
  - Registro de jti en Redis con TTL acorde a expiración.
  - Respuesta de revocación < 100 ms mediante validación directa en middleware.

- Claims estándar:
  - Incorporación de iat (emisión), nbf (no usar antes de), jti (identificador único), iss (emisor) y aud (audiencia).
  - Validación de fortaleza de clave (≥ 256 bits) y normalización de configuración para evitar ambigüedad entre SECRET_KEY y JWT_SECRET_KEY.

La reducción de expiración de tokens del bot a 24 horas reduce la superficie de ataque y obliga a re-autenticaciones periódicas sin interrumpir la operación, siempre que se mantenga una UX con sesiones razonablemente largas para tareas gubernamentales sensibles[^2].

#### 1.2.2 Migración a Webhook y Hardening de Transporte

La migración del bot a webhook con verificación HMAC garantiza autenticidad del origen y reduce latencia de propagación frente al modelo de polling. Este cambio debe acompañarse de:

- TLS estricto y HSTS:
  - Forzar TLS 1.2+ (preferible 1.3), deshabilitar suites débiles.
  - HSTS para prevenir downgrades de protocolo.
  - Pinning opcional de certificados en clientes para mayor control.

- Segmentación de red (DMZ):
  - Aislar el gateway de webhook y exponer únicamente rutas necesarias.
  - Aplicar rate limiting en el gateway y monitorear rechaza por abuso.

Estas medidas se alinean con guías de mejores prácticas de comunicaciones móviles y endurecimiento de transporte del sector público[^5][^6].

#### 1.2.3 Cliente HTTP Asíncrono y Resiliencia

La migración a HTTPX asíncrono elimina bloqueos de event loop y mejora el throughput bajo concurrencia. El diseño de resiliencia incorpora:

- Timeouts por operación y límites de concurrencia:
  - Timeouts configurados por dependencia y comando; cancelación cooperativa de solicitudes.
  - Semáforos por comando para limitar operaciones en vuelo.

- Reintentos con jitter y circuit breaker:
  - Reintentos con backoff exponencial y jitter para errores transitorios.
  - Circuit breaker con estados cerrado/abierto/semiabierto y sondeos de recuperación; umbrales basados en latencia P95 y tasa de error[^7][^8][^9].

- Colas y DLQ:
  - Uso de Redis Streams para notificaciones y broadcasting.
  - DLQ para mensajes no procesables; reintentos diferidos.

#### 1.2.4 Persistencia del Wizard en Redis y Idempotencia

Para garantizar continuidad en escalado horizontal y reinicios:

- Persistencia de estado del wizard:
  - Namespace “wizard:<chat_id>:<step>” con TTL (10–15 minutos).
  - Limpieza automática tras confirmación/cancelación.

- Idempotencia en operaciones:
  - Claves operativas (task_id + chat_id) para evitar duplicidades.
  - “Upsert” en backend y reconciliación de diferencias.

#### 1.2.5 Observabilidad y Métricas Específicas del Bot

Instrumentación detallada y paneles:

- Métricas por comando y callback:
  - Contadores de comandos (éxito/fracaso).
  - Histogramas de latencia por callback/paso.
  - Longitud de colas y edad de mensajes.

- Dashboards y alertas:
  - Paneles de rendimiento API, WebSockets y Redis.
  - Alertas por latencia P95/P99, errores, saturación de colas y caídas de Redis.
  - Correlación por requestId y trazabilidad de operaciones[^2].

## 2. Estrategia de Seguridad

La estrategia de seguridad se centra en hardening de autenticación, transporte y control de acceso, complementada por monitoreo y respuesta ante incidentes.

### 2.1 Hardening de JWT

- Refresh token flow con rotación:
  - Emisión y rotación de refresh tokens; invalidación del anterior en cada uso.
  - Almacenamiento seguro y auditoría de operaciones de issuance/revocation.

- Claims estándar:
  - iat, nbf, jti, iss, aud para trazabilidad y control.

- Revocación de tokens:
  - Lista de revocación basada en JTI con Redis; validación de JTI en middleware.

- Validación de fortaleza de claves:
  - Exigir longitud mínima de 256 bits; validación de entropía y nombres de variables consistentes.

- Automatización de rotación con ventana de gracia:
  - Rotación cada 90 días; soporte multi-instancia con claves previas válidas durante 24 horas.

### 2.2 Endurecimiento de Transporte

- TLS estricto y HSTS:
  - TLS 1.2+ preferible 1.3; suites de cifrado fuertes; HSTS para evitar downgrades.
  - Pinning opcional de certificados en clientes críticos.

- Segmentación de red:
  - DMZ para webhook; aislamiento de recursos y rutas mínimas necesarias.
  - Rate limiting en gateway y control de origen.

Estas prácticas responden a recomendaciones de guías técnicas del sector público[^5][^6].

### 2.3 Rate Limiting con Redis

- Límites por usuario/IP/comando:
  - Sliding window o token bucket implementado en Redis para persistencia en entornos multi-worker.
  - Instrumentación de métricas de rechazo y latencia de anti-abuso.

- Protección por comando:
  - Cuotas diferenciadas para operaciones críticas (finalización de tareas, broadcasting, notificaciones).

### 2.4 Gestión de Secretos y Rotación

- Vault/Secrets Manager:
  - Centralización de secretos con acceso mínimo y auditoría de lecturas.
  - Rotación periódica y escaneo automático de secretos en CI/CD.

- Procedimientos de backup/recovery:
  - Estrategias de respaldo y recuperación de claves y configuraciones; pruebas periódicas de restauración.

### 2.5 Monitoreo y Alertas de Seguridad

- SIEM:
  - Integración de eventos de seguridad; alertas por tokens sospechosos y patrones anómalos.

- Alarmas de revocación:
  - Tiempo de respuesta de revocación < 100 ms; monitoreo de latencia y tasa de revocación.

- Trazabilidad:
  - Logging integral de operaciones de autenticación, emisión, validación y revocación de tokens.

Para guiar la ejecución, se presentan dos tablas.

Tabla 3. Plan de Implementación de Seguridad por Fase

| Fase | Iniciativa | Entregable | Dependencias | Métrica de éxito |
|------|------------|------------|--------------|------------------|
| 0–60 días | Refresh tokens + JTI + claims estándar | Flujo operativo completo | Seguridad JWT; Redis | 100% cobertura; revocación < 100 ms |
| 0–60 días | Webhook con HMAC + TLS/HSTS | Gateway operativo | Platform/DevOps | Latencia P95 notificaciones < 400 ms |
| 0–60 días | Rate limiting con Redis | Middleware y métricas | Redis | Rechazos < 1% y trazables |
| 60–90 días | Wizard en Redis | Persistencia y limpieza | Redis | Pérdidas de sesión = 0 |
| 60–90 días | Circuit breaker por dependencia | Configuración y sondeos | Backend | Fallos reducidos ≥ 50% |
| 90–180 días | Vault + rotación | Integración en CI/CD | Platform/Sec | 100% secretos rotados |
| 90–180 días | SIEM + alertas seguridad | Integración y catálogos | SRE/Sec | Alertas efectivas sin ruido |

Tabla 4. Controles de Seguridad por Capa

| Capa | Control | Estado | Evidencia | Acción correctiva |
|------|---------|--------|-----------|-------------------|
| Autenticación | Refresh tokens, JTI, claims estándar | Por implementar | Auditoría JWT | Implementar 0–60 días |
| Autorización | RBAC/ABAC por comando | Parcial | Whitelisting | Formalizar roles/permisos |
| Transporte | TLS estricto, HSTS, pinning opcional | Por endurecer | Proxy/TLS | Endurecer 0–60 días |
| Datos | Cifrado en reposo | Por verificar | BD/backups | Verificar/activar 60–90 días |
| Monitoreo | SIEM, alertas de revocación | Parcial | Logs | Integrar y afinar 90–180 días |

## 3. Estrategia de Performance y Escalabilidad

El objetivo es alcanzar y sostener SLOs por operación crítica, con pruebas de carga y resiliencia que validen la operación bajo estrés. La estrategia se sustenta en un plan de pruebas, escalado horizontal y tuning de paginación y concurrencia.

- SLOs y objetivos de latencia:
  - Finalizar tarea: P95 < 600 ms, P99 < 900 ms, disponibilidad 99.9%.
  - Crear tarea (wizard): P95 < 800 ms, P99 < 1200 ms, disponibilidad 99.9%.
  - Notificaciones 40 minutos: P95 < 400 ms, P99 < 700 ms, entrega ≥ 99% en ventanas definidas.
  - Consultas: P95 < 500 ms, P99 < 800 ms, cache hit ≥ 98%.

- Pruebas de carga y resiliencia:
  - RPS objetivo por operación; límites de error; tasa de éxito de pruebas (≥ 95%).
  - Escenarios de burst y picos sostenidos; validación de degradación controlada.

- Escalado horizontal:
  - Bot: N ≥ 2 instancias; CPU < 70%; control de concurrencia por comando.
  - API: N ≥ 2 instancias; latencia P95; pool de DB optimizado.
  - Redis: 1–2 nodos (o cluster); memoria < 75%; evicción controlada.
  - Observabilidad: uptime > 99.9%; /metrics consistente.

- Backpressure y tuning:
  - Limitación de concurrencia en el bot; colas para amortiguar bursts.
  - Afinado de paginación (page_size); caching de listados.
  - Redis Streams para picos; DLQ para mensajes no procesables.

Las tablas siguientes ilustran el plan y los objetivos de desempeño.

Tabla 5. Plan de Pruebas de Carga

| Operación | RPS objetivo | P95 | P99 | Tasa de error | Criterio de éxito |
|-----------|--------------|-----|-----|---------------|-------------------|
| Finalizar tarea | 20 | < 600 ms | < 900 ms | < 1% | 95% de escenarios |
| Crear tarea (wizard) | 15 | < 800 ms | < 1200 ms | < 1% | 95% de escenarios |
| Notificaciones | 50 notif/5 min | < 400 ms | < 700 ms | < 0.5% | 99% de entregas |
| Consultas | 50 | < 500 ms | < 800 ms | < 0.2% | 98% de cache hit |

Tabla 6. SLOs por Operación

| Operación | Latencia objetivo | Throughput | Disponibilidad | Observabilidad |
|-----------|--------------------|------------|----------------|----------------|
| Finalizar | P95 < 600 ms | ≥ 60/min | 99.9% | Latencia, errores por causa |
| Crear | P95 < 800 ms | ≥ 50/min | 99.9% | Pasos de wizard y reintentos |
| Notificación | P95 < 400 ms | ≥ 100/5 min | 99.9% | Entrega y DLQ |
| Consultas | P95 < 500 ms | — | 99.9% | Hit/miss cache y latencia |

Tabla 7. Escalabilidad Horizontal por Componente

| Componente | Instancias objetivo | Factor de escala | Límites | Dependencias |
|------------|---------------------|------------------|---------|--------------|
| Bot Telegram | N ≥ 2 | CPU > 70% | Máx. conexiones | Redis, API |
| API FastAPI | N ≥ 2 | Latencia P95 | Pool de DB | DB, Redis |
| Redis | 1–2 (cluster) | Memoria < 75% | Evicción controlada | Persistencia |
| Observabilidad | 1 | Uptime > 99.9% | /metrics | Scraping y alertas |

Estos planes se apoyan en la estructura del repositorio (cliente API, Redis, observabilidad) y en el entorno productivo que expone /health y /metrics para monitoreo continuo[^1][^2].

## 4. Estrategia de Excelencia Operacional

La excelencia operacional se centra en observabilidad, automatización y continuidad del servicio con recuperación ante desastres (DR) y continuidad de negocio (BCP).

- Observabilidad:
  - Métricas específicas del bot: contadores de comandos, histogramas de latencia por callback/paso, longitud de colas y edad de mensajes.
  - Logs estructurados con correlation IDs y trazabilidad end-to-end.
  - Dashboards por dominio (API, WebSockets, Redis) y reglas de alerta por P95/P99, tasa de error y saturación de colas.

- Automatización:
  - CI/CD con despliegue sin tiempo de inactividad; validaciones y gates de seguridad.
  - Gestión de incidentes con runbooks, escalación y post-mortems.
  - Chaoss y pruebas de resiliencia; validaciones de circuit breaker y degradación controlada[^7][^9].

- DR y BCP:
  - Backups cifrados; retención y pruebas de restauración.
  - Simacros de tabletop y ejercicios de continuidad; procedimientos de failover y reconciliación de datos.

La siguiente tabla organiza el catálogo de logs, métricas y alertas.

Tabla 8. Catálogo de Logs, Métricas y Alertas

| Tipo | Nombre | Objetivo | Umbral de alerta | Canal |
|------|--------|----------|------------------|-------|
| Métrica | bot_commands_total | Detectar errores por comando | > 5% errores/día | Slack |
| Métrica | bot_callback_latency | Control de latencia | P99 > 1200 ms | Pager |
| Métrica | bot_queue_length | Detectar saturación | > 300 por 5 min | Slack |
| Métrica | bot_retry_ops | Minimizar reintentos | > 50/h | Slack |
| Métrica | api_request_errors | Control de errores | > 3% por 5 min | Pager |
| Log | Recepción de comando | Trazabilidad | N/A | Almacenamiento 90 días |
| Log | Callback de wizard | Trazabilidad paso | N/A | Almacenamiento 90 días |
| Log | Error de API | Diagnóstico | N/A | Almacenamiento 180 días |
| Log | Notificación enviada | Auditoría | N/A | Almacenamiento 180 días |
| Log | Alerta de resiliencia | Respuesta | N/A | Almacenamiento 365 días |
| Alerta | P95 alta | Desempeño | P95 > umbral 3 min | Pager 15 min |
| Alerta | Tasa de error | Estabilidad | > 3% por 5 min | Pager 15 min |
| Alerta | Cola saturada | Backpressure | Longitud > 300 | Slack 30 min |
| Alerta | Redis down | Dependencia | Conexión fallida | Pager 5 min |
| Alerta | Reintentos excesivos | Resiliencia | > 50/h | Slack 30 min |

La instrumentación se sustenta en evidencia del entorno productivo y repositorio, complementada por marcos de resiliencia y calidad de servicio en comunicaciones tácticas[^1][^2][^9].

## 5. Estrategia de Compliance y Gobierno

La estrategia de cumplimiento se basa en verificación de cifrado en reposo, auditoría integral y políticas de retención y acceso mínimo, alineadas con requisitos de mensajería gubernamental.

- Audit logging integral:
  - Registro de operaciones de negocio y de seguridad (quién, qué, cuándo, sobre qué).
  - Protección de datos personales (PII) en logs (enmascaramiento) y correlación por usuario de Telegram y registro de tarea.

- Cifrado en reposo:
  - Verificación y activación en BD y backups; validación de impacto en rendimiento.

- Retención y minimización:
  - Políticas formales de retención (logs 90–180 días; auditoría 1–3 años; configuración mientras esté vigente).
  - Minimización de datos personales y borrado seguro a solicitud del ciudadano.

- RBAC/ABAC:
  - Separación de funciones y permisos por comando/rol; pruebas de bypass.

- Auditoría:
  - Preparación para evaluaciones internas y externas; evidencia de controles y trazabilidad, en coherencia con marcos de cumplimiento de mensajería electrónica gubernamental[^4].

La siguiente tabla resume la matriz de cumplimiento y el plan de retención.

Tabla 9. Matriz de Cumplimiento

| Control | Estado | Evidencia | Riesgo | Acción correctiva |
|---------|--------|----------|--------|-------------------|
| Cifrado en tránsito | Parcial | HTTPS/proxy | MITM si mal configurado | TLS estricto + HSTS |
| Cifrado en reposo | Por verificar | BD/backups | Exposición de datos | Verificar/activar |
| Audit logging | Parcial | Logs app | Falta trazabilidad | Implementar audit integral |
| Retención de datos | No evidenciado | Políticas | Cumplimiento | Formalizar y auditar |
| Acceso mínimo | Parcial | Roles definidos | Sobrecarga privilegios | RBAC/ABAC y pruebas |

Tabla 10. Plan de Retención y Acceso

| Tipo de dato | Retención | Base legal | Acceso | Medidas de seguridad |
|--------------|-----------|------------|--------|----------------------|
| Logs del bot | 90–180 días | Seguridad operativa | Sec/Admin | Enmascarar PII |
| Audit logs | 1–3 años | Trazabilidad | Auditoría | WORM/alcance |
| Datos de tarea | Según normativa | Misión | Operadores | Cifrado y RBAC |
| Configuración | Mientras vigente | Operación | Admin | Vault y cifrado |

La alineación con el Electronic Messaging Compliance Assessment Toolkit garantiza consistencia con requisitos regulatorios del sector público[^4].

## 6. Desarrollo de Capacidades Organizacionales

Para sostener la mejora continua, se establecen rutas de capacitación, estructura de equipos y gestión del conocimiento.

- Roles críticos:
  - Seguridad (arquitectura de autenticación, gestión de secretos y SIEM).
  - Backend (FastAPI, clientes asíncronos, idempotencia).
  - SRE/Observabilidad (métricas, alertas, DR/BCP).
  - Compliance (políticas, auditoría, retención).

- Plan de capacitación:
  - OAuth 2.0/OpenID Connect (OIDC), seguridad JWT, gestión de secretos (Vault), resiliencia (circuit breaker), gobernanza de datos.
  - Entrenamiento en operación gubernamental: mensajería, trazabilidad y cumplimiento.

- Gestión del conocimiento:
  - Runbooks de operación y respuesta a incidentes; glosario y documentación centralizada.

- Métricas de madurez:
  - Cobertura de pruebas ≥ 85% incluyendo carga/resiliencia; cumplimiento de SLOs; calidad de auditoría.

Tabla 11. Plan de Capacitación por Rol

| Rol | Competencias | Contenidos | Calendario | Métricas |
|-----|--------------|------------|------------|----------|
| Seguridad | JWT, Vault, SIEM | Refresh tokens, JTI, rotación; SIEM | 0–60 días | Score JWT ≥ 9.0; revocación < 100 ms |
| Backend | Async, HTTPX, idempotencia | Migración a HTTPX; Upsert; breaker | 0–90 días | P95 mejorar ≥ 30%; errores < 1% |
| SRE/Obs | Métricas, alertas, DR | Dashboards; reglas; simacros | 60–180 días | Alertas efectivas; DR validado |
| Compliance | Políticas, auditoría | Retención; acceso mínimo; RBAC/ABAC | 60–180 días | Auditoría sin hallazgos críticos |

El repositorio y el entorno productivo sirven como base práctica para entrenamientos y simulaciones operativas[^1][^2].

## 7. Estrategia de Posicionamiento Competitivo

La diferenciación de GRUPO_GAD se fundamenta en:

- Seguridad y cumplimiento:
  - OAuth 2.0/OIDC con refresh tokens y claims estándar, revocación basada en JTI, hardening de transporte, auditoría integral.
  - Liderazgo en cumplimiento gubernamental y trazabilidad de operaciones.

- Resiliencia:
  - Degradación controlada en escenarios adversos; circuit breaker y DLQ; calidad de servicio inspirada en comunicaciones tácticas[^9][^10][^11].

- Innovación:
  - Webhook con verificación HMAC, cliente HTTP asíncrono, observabilidad del bot, stateful wizard en Redis, SLOs por operación.

- Propuesta de valor:
  - Servicios ciudadanos con seguridad extremo a extremo, trazabilidad y confiabilidad, reduciendo riesgo institucional y mejorando la experiencia del usuario.

Tabla 12. Mapa de Diferenciación

| Capacidad | Estado actual | Estado objetivo | Evidencia | Ventaja competitiva |
|-----------|---------------|-----------------|-----------|---------------------|
| Autenticación | JWT básico, sin refresh/JTI | OAuth 2.0/OIDC con refresh, JTI, claims | Auditoría JWT | Seguridad y auditoría superiores |
| Integración bot | Polling; cliente sincrónico | Webhook HMAC; HTTPX async | Repositorio y entorno | Latencia menor; resiliencia |
| Observabilidad | /metrics generales | Métricas específicas bot | Dashboards/Slack/Pager | Detección temprana; SLOs cumplidos |
| Cumplimiento | Parcial | Integral (cifrado reposo, retención, RBAC) | Auditoría y políticas | Certificación y confianza |
| Resiliencia | Básica | Degradación controlada, breaker, DLQ | Pruebas de resiliencia | Continuidad bajo estrés |

Las guías técnicas refuerzan el enfoque de calidad de servicio y degradación controlada, y se articulan con mejores prácticas de patrones de resiliencia[^7][^9][^10][^11].

## 8. Estrategia de Inversión y Financiamiento

El enfoque financiero prioriza iniciativas críticas con impacto medible y cronograma claro.

- Inversión por fases:
  - 0–60 días: refresh tokens, JTI, claims, webhook HMAC, TLS/HSTS, HTTPX async, rate limiting con Redis.
  - 60–90 días: wizard en Redis, colas/DLQ, circuit breaker, verificación de cifrado en reposo, instrumentación específica del bot.
  - 90–180 días: Vault/rotación, pruebas de carga/resiliencia, auditoría integral y preparación de certificación.

- Estimaciones de esfuerzo:
  - Desarrollo: seguridad JWT, integración bot, observabilidad, resiliencia.
  - Infraestructura: gateway de webhook, Redis Streams, Vault/Secrets Manager, cifrado en reposo.
  - Herramientas: Prometheus/Grafana, SIEM, CI/CD y gates de seguridad.

- ROI y TCO:
  - Reducción de incidentes críticos (objetivo 0/mes), mejora de latencia P95 y cumplimiento de SLOs (≥ 99%), reducción de errores 4xx/5xx (≥ 50%).
  - Ahorro operativo por menor tiempo de respuesta a incidentes y menor riesgo de brecha de datos.

- Gobernanza de costos:
  - Priorización por riesgo e impacto; escalado por demanda; inversiones condicionales a gates de cumplimiento y desempeño.

Tabla 13. Plan de Inversión y Priorización

| Iniciativa | Fase | Esfuerzo | Dependencia | Impacto | Métrica |
|------------|------|----------|-------------|---------|---------|
| Refresh tokens + JTI + claims | 0–60 | Alto | Seguridad JWT | Alto | Revocación < 100 ms |
| Webhook HMAC + TLS/HSTS | 0–60 | Medio | Platform/DevOps | Alto | P95 notificaciones < 400 ms |
| HTTPX async + rate limiting | 0–60 | Medio | Backend/Redis | Alto | P95 mejorar ≥ 30% |
| Wizard en Redis + DLQ | 60–90 | Medio | Redis | Alto | Pérdidas de sesión = 0 |
| Circuit breaker | 60–90 | Bajo | Backend | Medio | Fallos reducidos ≥ 50% |
| Cifrado en reposo | 60–90 | Medio | DB/backups | Alto | Verificación completa |
| Vault + rotación | 90–180 | Medio | CI/CD | Alto | 100% secretos rotados |
| Pruebas de carga/resiliencia | 90–180 | Medio | SRE/QA | Alto | SLOs ≥ 99% |
| Auditoría integral | 90–180 | Medio | Compliance | Alto | Sin hallazgos críticos |

Las inversiones se alinean con el entorno productivo y el repositorio oficial como evidencia del estado actual y las necesidades de evolución[^1][^2].

## 9. Marco de Gobernanza de Implementación

La gobernanza asegura decisiones ágiles y trazables, con gestión de cambios y comunicación efectiva.

- Estructura de PMO:
  - Comité Directivo (prioridades, aprobaciones).
  - Arquitectura (diseño y estándares).
  - Seguridad (controles, auditoría).
  - SRE/DevOps (observabilidad, resiliencia, automatización).
  - Compliance (políticas, retención, auditoría).

- RACI:
  - Responsables, Aprobadores, Consultados, Informados por iniciativa y fase.

- Gestión de cambios:
  - Gates de seguridad y compliance; criterios de aceptación.
  - Documentación y trazabilidad de decisiones.

- Comunicación:
  - Rituales (planificación, revisión, retro), stakeholders (Dirección, equipos técnicos, cumplimiento).

- Éxito y optimización:
  - Revisión de KPIs y mejora continua; post-mortems; ajustes de SLOs y alertas.

Tabla 14. Matriz RACI por Iniciativa

| Iniciativa | Responsable (R) | Aprobador (A) | Consultado (C) | Informado (I) |
|------------|------------------|---------------|----------------|---------------|
| Refresh tokens + JTI | Seguridad | Comité | Backend, SRE | Compliance |
| Webhook HMAC + TLS/HSTS | Platform/DevOps | Comité | Seguridad, Arquitectura | SRE |
| HTTPX async + rate limiting | Backend | Arquitectura | Seguridad, SRE | PMO |
| Wizard en Redis + DLQ | Backend | Arquitectura | SRE, Seguridad | Compliance |
| Circuit breaker | Backend | Arquitectura | SRE | PMO |
| Cifrado en reposo | DB/Platform | Comité | Seguridad, Compliance | SRE |
| Vault + rotación | Seguridad | Comité | Platform/DevOps | PMO |
| Pruebas de carga/resiliencia | SRE/QA | Arquitectura | Backend | Dirección |
| Auditoría integral | Compliance | Comité | Seguridad, SRE | Dirección |

Este marco integra guías de resiliencia (circuit breaker) y de cumplimiento gubernamental para asegurar que las decisiones sean consistentes y auditables[^7][^4].

## 10. Plan de Ejecución por Fases (0–60, 60–90, 90–180 días) y Métricas

La ejecución se organiza en tres horizontes con entregables y dependencias claras, culminando con auditoría y preparación para certificación.

### Fase 1 (0–60 días): Críticos de seguridad y observabilidad

- Refresh tokens con rotación y revocación (JTI); claims estándar; reducción de expiración de tokens del bot a 24h.
- Webhook con verificación HMAC; TLS estricto y HSTS.
- Cliente HTTP asíncrono (HTTPX) con timeouts robustos; rate limiting con Redis por usuario/IP/comando.
- Observabilidad: métricas específicas del bot y paneles; alertas por P95/P99, errores y colas.
- Circuit breaker inicial por dependencia.

Dependencias: Seguridad JWT, Platform/DevOps, Backend, Redis.  
Riesgos: compatibilidad de clientes, cambios en despliegue.  
Métricas: revocación < 100 ms; P95 mejorar ≥ 30%; rechazos instrumentados < 1%.

### Fase 2 (60–90 días): Resiliencia operativa

- Persistencia de wizard en Redis con TTL y namespace; limpieza automática; idempotencia en operaciones de negocio.
- Colas (Redis Streams) y DLQ para notificaciones y broadcasting; métricas de longitud y edad de mensajes.
- Verificación y activación de cifrado en reposo en BD/backups; pruebas de restauración.
- SLOs por operación y pruebas de carga/resiliencia; tuning de paginación y backpressure.

Dependencias: Redis, Backend, DB/Platform, SRE/QA.  
Riesgos: saturación de keys, impacto de cifrado en rendimiento.  
Métricas: pérdidas de sesión = 0; DLQ < 0.5%; SLOs cumplidos ≥ 99%.

### Fase 3 (90–180 días): Gobierno y cumplimiento

- Vault/Secrets Manager; rotación documentada y escaneo de secretos en CI/CD.
- Pruebas de resiliencia adicionales (chaos, degradación controlada); validación de circuit breaker y recovery.
- Audit logging integral; preparación para auditoría externa y certificación gubernamental; formalización de políticas de retención y acceso mínimo (RBAC/ABAC).

Dependencias: Seguridad, Platform/DevOps, Compliance, SRE/QA.  
Riesgos: ruido de alertas SIEM; adopción cultural de Vault.  
Métricas: 100% secretos rotados; auditoría sin hallazgos críticos; cobertura de audit logging ≥ 95%.

La hoja de ruta consolidada se presenta a continuación.

Tabla 15. Hoja de Ruta Consolidada

| Fase | Iniciativa | Entregable | Responsable | Dependencias | Métrica de éxito |
|------|------------|------------|-------------|--------------|------------------|
| 0–60 | Refresh tokens + JTI | Flujo completo | Seguridad | JWT, Redis | Revocación < 100 ms |
| 0–60 | Webhook HMAC + TLS/HSTS | Gateway operativo | Platform/DevOps | Seguridad | P95 notificaciones < 400 ms |
| 0–60 | HTTPX async + rate limiting | Cliente y middleware | Backend | Redis | P95 mejorar ≥ 30% |
| 60–90 | Wizard en Redis | Persistencia | Backend | Redis | Pérdidas de sesión = 0 |
| 60–90 | Colas + DLQ | Worker/DLQ | SRE/Backend | Redis | DLQ < 0.5% |
| 60–90 | Cifrado en reposo | Verificación/activación | DB/Platform | Seguridad | Impacto validado |
| 90–180 | Vault + rotación | Integración CI/CD | Seguridad | Platform | 100% secretos rotados |
| 90–180 | Pruebas carga/resiliencia | Suite y reportes | SRE/QA | Backend | SLOs ≥ 99% |
| 90–180 | Auditoría integral | Informe y evidencias | Compliance | Seguridad/SRE | Sin hallazgos críticos |

Gates de salida por fase:
- Fase 1: Score JWT ≥ 9.0; revocación < 100 ms; webhook operativo con TLS/HSTS; P95 mejorar ≥ 30%; rate limiting con métricas.
- Fase 2: Pérdidas de sesión wizard = 0; DLQ < 0.5%; cifrado en reposo verificado; SLOs ≥ 99%; pruebas de carga aprobadas.
- Fase 3: Vault operativo; 100% secretos rotados; auditoría sin hallazgos críticos; políticas de retención y acceso mínimo formalizadas.

Riesgos transversales y mitigaciones:
- Compatibilidad de clientes con refresh tokens: pruebas de integración, flags de compatibilidad temporal.
- Rendimiento tras habilitar cifrado en reposo: pruebas de carga y tuning de índices; evaluación de impacto.
- Ruido de alertas SIEM: afinación de umbrales y reglas; revisión periódica y retroalimentación.
- Adopción cultural de Vault: capacitación y automatización; auditorías de lectura y gobernanza de accesos.

Este plan se alinea con el repositorio y el entorno productivo, y con marcos de mensajería gubernamental para asegurar que los criterios de salida se traduzcan en auditorías exitosas[^1][^2][^4].

---

## Brechas de Información

- No se ha verificado el cifrado en reposo de la base de datos y backups.
- No se evidenció persistencia del estado del wizard en Redis (context.user_data en memoria).
- Falta especificación e instrumentación de rate limiting específico por integración (cuotas por usuario/IP/comando) y su instrumentación.
- No se identificó un esquema de autorización formal para ciudadanos desde Telegram más allá de whitelisting.
- No se evidenciaron pruebas de carga específicas del bot ni SLOs operativos del bot.
- No se documentó un flujo formal de auditoría de acciones del bot más allá de logging general.
- No se detectó la implementación de refresh tokens en el flujo del bot.
- No se verificó enforcement de TLS estricto y pinning en clientes.
- No se evidenciaron métricas del bot exportadas a Prometheus.
- No se documentó un proceso formal de incident response adaptado al bot.
- No se evidenciaron contratos de API unificados y estandarizados entre servicios legacy y actuales.
- No se documentó política formal de retención de logs/auditoría ni procedimientos de backup/restore de secretos.

Estas brechas se integran en los roadmaps y gates de salida de cada fase para su cierre efectivo.

---

## Conclusión

GRUPO_GAD cuenta con una base arquitectónica sólida y una instrumentación inicial que, con las acciones propuestas, puede evolucionar hacia un sistema gubernamental de clase mundial en seguridad, cumplimiento y resiliencia. La ejecución disciplinada de este blueprint, con métricas claras y gobernanza eficaz, reducirá significativamente los riesgos identificados en las auditorías y posicionará a la organización como referente en operación gubernamental digital con estándares elevados de calidad y trazabilidad.

---

## Referencias

[^1]: GRUPO_GAD - Repositorio (GitHub). URL: https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD - Aplicación en Producción (Fly.io). URL: https://grupo-gad.fly.dev  
[^3]: Mobile Communications Best Practice Guidance - CISA (PDF). URL: https://www.cisa.gov/sites/default/files/2024-12/guidance-mobile-communications-best-practices.pdf  
[^4]: Electronic Messaging Compliance Assessment Toolkit - NARA (DOCX). URL: https://www.archives.gov/files/records-mgmt/policy/electronic-messaging-compliance-assessment-toolkit.docx  
[^5]: Circuit Breaker Pattern - Azure Architecture Center. URL: https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker  
[^6]: Circuit Breaker - Martin Fowler. URL: https://martinfowler.com/bliki/CircuitBreaker.html  
[^7]: Circuit Breaker Pattern (Design Patterns for Microservices) - Medium. URL: https://medium.com/geekculture/design-patterns-for-microservices-circuit-breaker-pattern-276249ffab33  
[^8]: Army Tactical Network Quality of Service and Graceful Degradation Concept - Cyber Defense Review. URL: https://cyberdefensereview.army.mil/CDR-Content/Articles/Article-View/Article/1134643/army-tactical-network-quality-of-service-and-graceful-degradation-concept/  
[^9]: Tactical Communications for Ground-Based Air Defense (GBAD) - Bittium (2025) (PDF). URL: https://www.bittium.com/wp-content/uploads/2025/05/Bittium-Tactical-Communications-for-Ground-Based-Air-Defense.pdf  
[^10]: Mobile Communications Best Practice Guidance - CISA (PDF). URL: https://www.cisa.gov/sites/default/files/2024-12/guidance-mobile-communications-best-practices.pdf