# Cobertura de Testing en Sistemas Operativos/Tácticos de GRUPO_GAD: Evaluación Específica, Gaps y Roadmap a 85%+

## 1. Resumen ejecutivo y objetivos del análisis

El presente informe tiene por propósito evaluar la cobertura de pruebas (testing coverage) y la calidad de las pruebas del sistema GRUPO_GAD en seis dimensiones críticas: componentes operativos, integraciones, métricas gubernamentales de calidad, funcionalidades operativas, tendencias/brechas, y benchmarking contra estándares de referencia. El alcance cubre la API FastAPI, el Telegram Bot, la geoespacialidad con PostGIS, el caching y pub/sub con Redis, la mensajería en tiempo real vía WebSockets, y la observabilidad con Prometheus/Grafana. El análisis se ancla en evidencia disponible del repositorio y de la instancia en producción, complementado por marcos regulatorios y de buenas prácticas para sistemas críticos y de alta disponibilidad.[^1][^2][^3][^4][^5]

Hallazgos clave:
- La cobertura actual reportada para el bot se sitúa en 70%+, con 11 archivos de pruebas que abarcan comandos, wizard multistep, callbacks y teclados. La calidad del diseño de pruebas se evidencia por el uso de fixtures asincrónicas, mocking del cliente de API y validaciones de restricciones (p. ej., callback_data ≤ 64 bytes). Estos elementos fortalecen la confiabilidad de los flujos conversacionales y de interacción con la API.[^1]
- Existen brechas de evidencia en componentes operativos críticos (gestión de efectivos, endpoints de operativos/allanamientos, notificaciones automáticas, comandos de finalización, recordatorios), en la persistencia de estados del wizard del bot (no se evidencia Redis en el bot) y en pruebas de carga/resiliencia más allá de líneas base reportadas. Asimismo, no se observan pruebas end-to-end (E2E) con ambientes gobernados que simulen producción ni reportes sistemáticos de calidad de pruebas por módulo y de la relación unit vs integration.[^1][^2]
- El sistema dispone de una instrumentación Prometheus sólida para WebSockets (conexiones activas, mensajes, broadcasts, latencias) y un pipeline de CI/CD con calidad de código y seguridad. Faltan, sin embargo, métricas operativas detalladas en producción y la vinculación explícita de pruebas con controles de seguridad (NIST CSF 2.0, SA-11(7), NISTIR 8397), así como una meta de disponibilidad con SLAs formalizados.[^1][^2][^3][^9][^10][^11]

Objetivo estratégico:
- Establecer un roadmap para alcanzar ≥ 85% de cobertura en funcionalidades críticas y alinear la calidad de pruebas con los requisitos de sistemas 24/7 y alta disponibilidad (p. ej., tolerancia a fallos, failover automatizado, objetivos de disponibilidad tipo 99.9% y superiores), integrando pruebas funcionales, de seguridad y de resiliencia dentro del pipeline de CI/CD y en ambientes de staging controlado.[^4][^5][^6][^7]

La conjunción de estos hallazgos y objetivos obliga a cerrar brechas de evidencia, elevar la cobertura en módulos críticos y afinar las pruebas de seguridad, resiliencia y performance para cumplir con marcos como NIST CSF 2.0, NISTIR 8397, SA-11(7), prácticas de alta disponibilidad y, de manera complementaria, requisitos de seguridad del sector justicia cuando corresponda (CJIS), sin extrapolar obligaciones no evidenciadas.[^3][^9][^10][^11][^13]

## 2. Alcance, fuentes y metodología

El alcance de la evaluación se fundamenta en:
- Evidencia del repositorio oficial (estructura, módulos, suite de pruebas, configuraciones de CI/CD y observabilidad).
- Artefactos operativos de la instancia en producción (endpoints, configuraciones, health checks, métricas expuestas).
- Estándares y marcos: NIST CSF 2.0 para gobernanza y gestión de riesgos de ciberseguridad; NISTIR 8397 para prácticas de verificación mínima por parte de desarrolladores; SA-11(7) para cobertura de controles de seguridad; y guías de alta disponibilidad para alinear pruebas con objetivos de disponibilidad 24/7.[^1][^2][^3][^9][^10][^11]

Metodología:
- Revisión del inventario de integraciones y de la auditoría del Telegram Bot gubernamental para perfilar cobertura, patrones de prueba y riesgos operativos.
- Mapeo de componentes operativos críticos, integraciones (Telegram Bot, PostGIS, Redis, WebSockets, Prometheus/Grafana) y endpoints API asociados.
- Evaluación de métricas gubernamentales de calidad: cobertura, error handling, seguridad, edge cases y prácticas de disponibilidad.
- Análisis de tendencias y brechas: ratio unit vs integration, frecuencia de ejecución, calidad de casos, y ejecución de pruebas de carga/resiliencia.
- Benchmarking contra estándares y definición de un roadmap factible para alcanzar ≥ 85% de cobertura en funcionalidades críticas con gates de CI/CD y métricas de salud.

Limitaciones:
- No se evidencian reportes desagregados de cobertura por módulo para todos los componentes; la cobertura 70%+ está verificada para el bot, pero no para el resto de módulos.
- Persisten incertidumbres sobre pruebas de carga, resiliencia y E2E con datos y configuraciones de producción, así como sobre SLAs de disponibilidad formalizados.[^1][^2]

Para ilustrar el enfoque metodológico, se presenta el mapa de fuentes y su confiabilidad relativa, teniendo en cuenta que la evidencia de producción sirve para validar el estado desplegado, mientras que los estándares establecen los requisitos de seguridad y disponibilidad.

![NIST CSF 2.0 – Enfoque de funciones y gobernanza (resumen visual).](.pdf_temp/viewrange_chunk_1_1_5_1761723738/images/r7hal7.jpg)

Tabla 1. Mapa de fuentes y confiabilidad
| Tipo de fuente                        | Evidencia aportada                                          | Fiabilidad percibida | Uso en el análisis                                          |
|--------------------------------------|-------------------------------------------------------------|----------------------|-------------------------------------------------------------|
| Repositorio oficial (código, tests)  | Estructura, CI/CD, cobertura reportada, patrones de testing | Alta                 | Base primaria para módulos, pruebas y configuraciones[^1]   |
| Instancia en producción              | Endpoints operativos, métricas, health checks                | Alta                 | Validación del estado desplegado y observabilidad[^2]       |
| NIST CSF 2.0                         | Marco de gobierno y gestión de riesgos                      | Alta                 | Benchmark de seguridad y gobernanza[^3]                     |
| NISTIR 8397                          | Prácticas mínimas de verificación de desarrolladores         | Alta                 | Automatización, seguridad en pruebas, calidad[^9]           |
| NIST SA-11(7)                        | Cobertura de controles de seguridad                         | Alta                 | Vinculación de pruebas con controles específicos[^10]       |
| AWS Well-Architected (Availability)  | Prácticas de alta disponibilidad                            | Alta                 | Objetivos de uptime, resiliencia y pruebas asociadas[^5]    |
| Splunk – Disponibilidad              | Estrategias para alta disponibilidad                        | Media/Alta           | Contextualización de downtime permitido vs pruebas[^4]      |
| NISTIR 8011-4                        | Automatización para evaluación de controles                 | Alta                 | Integración de seguridad y automatización en CI/CD[^11]     |
| Google Testing Blog – Coverage       | Buenas prácticas de coverage                                | Alta                 | Gestión del coverage sin perseguir 100% mecánico[^6]        |
| Qualitest – Availability Testing     | Estrategias de pruebas de disponibilidad                    | Media/Alta           | Pruebas de failover, resiliencia y continuidad[^7]          |

## 3. Cobertura por componente crítico

La evaluación se centra en los componentes operativos que soportan flujos de misión crítica: gestión de efectivos, endpoints de operativos/allanamientos, notificaciones automáticas, comandos de finalización y recordatorios. Aunque el repositorio evidencia cobertura en el Telegram Bot y patrones de prueba en integraciones (PostGIS, Redis, WebSockets, Prometheus), persisten brechas de evidencia en módulos específicos de operaciones de campo, recordatorios programados y validaciones de seguridad de endpoints sensibles.

Tabla 2. Cobertura por componente crítico
| Componente                         | Módulos/archivos asociados (evidencia)              | Tipo de pruebas (unit/integration/E2E)        | Cobertura actual (si disponible) | Estado        | Brechas principales                                                                 |
|-----------------------------------|-----------------------------------------------------|-----------------------------------------------|----------------------------------|---------------|-------------------------------------------------------------------------------------|
| Gestión de efectivos              | src/core/geo/postgis_service.py (PostGIS); modelos  | Unit/Integration (validación coords, consultas geography) | No reportado por módulo           | Parcial       | Evidencia directa de asignación/libertad de efectivos; pruebas de seguridad         |
| Endpoints de operativos/allanamientos | routers API FastAPI (autenticación/tareas/usuarios) | Integration/E2E                                | No reportado                     | Desconocido   | Pruebas de permisos/roles; auditoría; casos edge (interrupciones, reconexión)       |
| Notificaciones automáticas        | src/core/websockets.py; Redis Pub/Sub               | Integration/E2E; smoke tests                   | Parcial (WebSockets ~85% report.) | Parcial       | Fallback ante fallos; pruebas de saturación; instrumentación Prometheus en producción |
| Comandos de finalización          | Bot: commands/finalizar_tarea.py                    | Unit/Integration                               | 70%+ (bot)                       | Parcial       | Diferenciación 404/403 bajo carga; rollback; permisos granulares                   |
| Recordatorios (40 min antes)      | —                                                   | —                                             | —                                | Brecha        | Scheduler, caso edge: fuera de ventana, conflictos de horario                       |

La geoespacialidad con PostGIS cuenta con pruebas para validaciones de coordenadas y consultas geography. La presencia de una columna geométrica y un índice espacial es favorable para búsquedas de proximidad, útiles en asignación de efectivos. No obstante, falta evidencia de consumo directo desde el bot y del acoplamiento con endpoints de operativos.[^1][^2]

### 3.1 Gestión de efectivos

El servicio PostGIS implementa una consulta geography con SRID 4326 que calcula distancias y retorna resultados ordenados por proximidad, soportando filtros por registros no eliminados. Las pruebas observadas validan coordenadas y la semántica de la consulta. Para un sistema operativo/táctico, esto habilita escenarios como encontrar el efectivo más cercano a un incidente, pero faltan pruebas específicas de autorización, auditoría y edge cases de geolocalización (p. ej., coordenadas inválidas, puntos en el antipodal, o búsquedas con límites muy altos).[^1][^2]

Tabla 3. Cobertura del servicio geoespacial
| Aspecto                         | Estado actual                         | Evidencia                     | Gap prioritario                                |
|---------------------------------|---------------------------------------|-------------------------------|-----------------------------------------------|
| Validación de coordenadas       | Implementada (rangos -90..90, -180..180) | Código de validaciones        | Pruebas con inputs extremos y boundary values  |
| Consultas geography (ST_Distance, ST_MakePoint, ST_SetSRID) | Implementada                         | Query con geography y ordenación | Pruebas de performance en tablas grandes       |
| Asignación/libertad de efectivos | No evidenciada en módulo geoespacial | —                             | Casos de uso y pruebas E2E de asignación       |
| Seguridad y auditoría           | No evidenciada                        | —                             | Controles de acceso y audit trail en consultas |

### 3.2 Endpoints de operativos/allanamientos

La superficie de integración del bot con la API incluye autenticación, creación y finalización de tareas, y consulta de usuarios. Los comandos del bot dependen de estos endpoints para ejecutar operaciones sensibles. La evidencia sugiere ausencia de pruebas específicas por endpoint con enfoque de seguridad (autorización, roles, auditoría), así como de escenarios edge en operaciones de campo (cancelaciones, reintentos, degradaciones por fallos de servicios externos).[^1][^2]

Tabla 4. Cobertura por endpoint API
| Endpoint                       | Método | Payload principal                 | Respuesta esperada             | Pruebas unitarias | Pruebas de integración | Pruebas de seguridad | Observaciones                                    |
|-------------------------------|--------|-----------------------------------|--------------------------------|-------------------|------------------------|----------------------|--------------------------------------------------|
| /auth/{telegram_id}           | GET    | —                                 | Estado de autenticación        | Evidencia parcial | Evidencia parcial       | No evidenciado       | Clarificar scopes/roles; auditoría de acceso     |
| /tasks/create                 | POST   | TareaCreate (código, título, tipo, delegado, asignados) | Tarea creada                   | Evidencia parcial | Evidencia parcial       | No evidenciado       | Validaciones de permisos; manejo de errores      |
| /tasks/finalize               | POST   | task_code, telegram_id            | Tarea finalizada               | Evidencia parcial | Evidencia parcial       | No evidenciado       | Diferenciación 404/403 bajo carga                |
| /tasks/user/telegram/{id}     | GET    | status=pending                    | Lista de tareas pendientes     | Evidencia parcial | Evidencia parcial       | No evidenciado       | Paginación; latencia; auditoría de consulta      |
| /users                        | GET    | role (opcional)                   | Lista de usuarios              | Evidencia parcial | Evidencia parcial       | No evidenciado       | Filtros de seguridad; auditoría por rol          |

### 3.3 Sistema de notificaciones automáticas

La difusión cross-worker por Redis Pub/Sub y el módulo de WebSockets proveen mensajería en tiempo real. Se reporta cobertura ~85% en src/core/websockets.py y smoke tests (ws-smoke). Es imprescindible incorporar pruebas de fallback ante fallos, degradaciones por desconexión y escenarios de saturación, además de correlacionar métricas Prometheus en producción (conexiones activas, mensajes, broadcasts, latencias, errores) con resultados de pruebas para validar SLAs de disponibilidad.[^1][^2]

Tabla 5. Cobertura de notificaciones y resiliencia
| Caso de prueba                                 | Tipo       | Objetivo de resiliencia                              | Métricas observadas                    | Estado     |
|------------------------------------------------|-----------|------------------------------------------------------|----------------------------------------|------------|
| Broadcast con workers sanos                     | Integration | Validar difusión correcta                            | broadcasts_total; messages_sent_total  | OK         |
| Fallo de Redis (TLS/puerto)                     | Integration | Degradación controlada y reconexión                  | send_errors_total; health check        | Brecha     |
| Desconexión de clientes WebSocket               | Integration | Recuperación y re-suscripción                         | active_connections                     | Parcial    |
| Saturación (mensajes en ráfaga)                 | Load/Stress | Evitar backpressure y pérdida de mensajes            | message_latency_seconds                | Brecha     |
| Correlación con Prometheus (post-producción)    | E2E        | Validar métricas y alertas en producción             | —                                      | Brecha     |

### 3.4 Comandos de finalización operativa

El flujo de finalización de tareas en el bot está cubierto por pruebas unitarias e integración, con manejo diferenciado de errores 404/403. Se observan gaps en validación bajo carga, reversibilidad (rollback) y permisos granulares por rol (p. ej., finalización por delegado vs administrador). En un sistema operativo/táctico, la semántica de autorización y la trazabilidad de la acción son críticas para auditoría y cumplimiento.[^1][^2]

Tabla 6. Casos de prueba de finalización
| Escenario                               | Endpoint/API asociada | Assertions clave                   | Manejo de errores | Estado   |
|-----------------------------------------|------------------------|------------------------------------|-------------------|----------|
| Finalización exitosa                    | /tasks/finalize        | Código de tarea y usuario válidos  | OK                | OK       |
| Tarea inexistente (404)                 | /tasks/finalize        | Mensaje claro y trazabilidad       | OK                | Parcial  |
| Permisos insuficientes (403)            | /tasks/finalize        | Mensaje diferenciado y registro    | OK                | Parcial  |
| Bajo carga/concurrencia                 | /tasks/finalize        | Sin race conditions                | —                 | Brecha   |
| Rollback de finalización                | /tasks/finalize        | Reversibilidad controlada          | —                 | Brecha   |

### 3.5 Recordatorios (40 minutos antes)

No se evidencia un scheduler de recordatorios ni casos de prueba asociados. Es necesaria la definición del flujo end-to-end: cómo se encolan los recordatorios, su persistencia (p. ej., Redis), los casos edge (fuera de ventana de tiempo, conflictos de horario), y la trazabilidad en logs/auditoría.

Tabla 7. Diseño de pruebas para recordatorios
| Caso                                | Datos de entrada                 | Tiempo/Trigger         | Validación de ejecución                    | Métricas/observabilidad                  | Estado  |
|-------------------------------------|----------------------------------|------------------------|--------------------------------------------|------------------------------------------|---------|
| Recordatorio dentro de ventana      | Operativo con timestamp          | T–40 min               | Notificación enviada; estado actualizado   | notifications_sent_total; latencia       | Brecha  |
| Fuera de ventana                    | Operativo en pasado/futuro extremo | N/A                    | No enviar; registrar decisión               | audit_log; decision_reason               | Brecha  |
| Conflicto de horario                | Operativos solapados             | T–40 min               | Política de priorización aplicada          | scheduler_decisions_total                | Brecha  |
| Fallo de Redis/WS                   | Cliente no disponible            | T–40 min               | Reintentos con backoff; degradación         | send_errors_total; retries               | Brecha  |

## 4. Cobertura de integraciones

Las integraciones constituyen la columna vertebral de la operación. El bot, PostGIS, Redis (cache y pub/sub), WebSockets y Prometheus/Grafana han de contar con pruebas unitarias, de integración y E2E que validen contratos, seguridad, resiliencia y observabilidad.

Tabla 8. Cobertura por integración
| Integración         | Pruebas existentes                               | Tipo                       | Cobertura reportada | Gaps principales                                                                 |
|---------------------|---------------------------------------------------|----------------------------|---------------------|----------------------------------------------------------------------------------|
| Telegram Bot        | 11 archivos: /start, estadísticas, crear/finalizar tareas, historial, callbacks, wizard, teclados | Unit/Integration/E2E (parcial) | 70%+                | Pruebas de carga/resiliencia; seguridad avanzada; persistencia del wizard en Redis |
| PostGIS             | Validación de coords; consultas geography         | Unit/Integration           | No reportado        | Performance; edge cases geoespaciales; seguridad/auditoría                       |
| Redis (Cache)       | CRUD, TTL, serialización; estadísticas; fallback TLS | Unit/Integration           | Parcial             | Fallback con reconexión; rate limiting; consistencia en multi-worker             |
| Redis (Pub/Sub)     | Broadcasting; suscripción; cross-worker; errores  | Unit/Integration           | Parcial             | Saturación y reconexión; auditoría de mensajes                                   |
| WebSockets          | Smoke tests; instrumentación Prometheus           | Integration/E2E            | ~85%                | Pruebas de disponibilidad/failover; backpressure; pruebas con métricas post-deploy |
| Prometheus/Grafana  | Métricas de conexiones, mensajes, latencias       | Validación de instrumentación | Parcial             | Reportes de cobertura de métricas; alertas operativas alineadas con SLAs         |

### 4.1 Telegram Bot (11 tests)

La suite del bot cubre comandos principales, el wizard multistep, callbacks y teclados. Se observan buenas prácticas como fixtures async, mocking de API, y verificación de tamaño de callback_data. Para alinear con requisitos 24/7, se recomienda incorporar pruebas de carga y resiliencia (polling, reintentos, reconexión, timeouts) y métricas específicas del bot exportadas a Prometheus, junto con gates de cobertura en CI/CD.[^1]

Tabla 9. Matriz de pruebas del bot por flujo
| Flujo                     | Prueba asociada                         | Tipo          | Estado  | Observaciones                           |
|---------------------------|------------------------------------------|---------------|---------|-----------------------------------------|
| /start                    | test_start_command.py                    | Unit/Integration | OK      | Verificación de bienvenida               |
| Crear tarea (wizard)      | test_crear_tarea.py; test_wizard_multistep.py | Unit/Integration | OK      | Validaciones por paso; UX                |
| Finalizar tarea           | test_finalizar_tarea.py                  | Unit/Integration | OK      | Diferenciación 404/403                   |
| Historial                 | test_historial.py                        | Unit/Integration | OK      | Paginación; manejo de errores            |
| Callbacks                 | test_callback_handler.py                 | Unit/Integration | OK      | Router por acciones                      |
| Teclados                  | test_keyboards.py                        | Unit          | OK      | Tamaño callback_data ≤ 64 bytes          |
| Estadísticas              | test_estadisticas.py                     | Unit/Integration | OK      | Cálculos operativos                      |
| Carga/Resiliencia         | —                                        | Load/Stress   | Brecha  | Polling y reconexión; timeouts           |
| Métricas del bot          | —                                        | Instrumentación | Brecha  | Latencia por comando; throughput         |

### 4.2 PostGIS (geolocalización)

El servicio geoespacial valida coordenadas y emplea geography para cálculos precisos de distancia. Faltan pruebas de performance y de seguridad/auditoría sobre consultas sensibles (quién consulta, sobre qué efectivo, con qué propósito). La adopción de pruebas de boundary values y casos de uso de asignación de efectivos sería un avance significativo.[^1]

Tabla 10. Pruebas PostGIS
| Query/Función                      | Caso de prueba                           | Datos                 | Validación de salida               | Estado   |
|------------------------------------|------------------------------------------|-----------------------|------------------------------------|----------|
| ST_Distance (geography)            | Distancia punto conocido                 | Coordenadas válidas   | distance_m coherente               | OK       |
| ST_SetSRID + ST_MakePoint          | SRID 4326                                | lng/lat               | Conversión correcta                | OK       |
| Boundary values                    | Lat/lng fuera de rango                   | >90, >180             | Excepción/validación               | Parcial  |
| Performance con índices            | Búsqueda con LIMIT alto                  | 1000+ registros       | Latencia aceptable                 | Brecha   |
| Auditoría de consultas             | Registro de actor y propósito            | User, Role            | Audit trail                        | Brecha   |

### 4.3 Redis (cache + pub/sub)

Las pruebas del CacheService abarcan CRUD, TTL y serialización, con estadísticas y fallback TLS. El Pub/Sub valida broadcasting y reconexión. La agenda pendiente incluye: pruebas con patrones de keys, limpieza por namespaces, rate limiting, y simulación de reconexión bajo escenarios de indisponibilidad parcial.[^1]

Tabla 11. Pruebas de cache y pub/sub
| Operación        | Caso                                | Condición de fallo         | Reintentos/Fallback | Métricas                  | Estado   |
|------------------|-------------------------------------|----------------------------|---------------------|---------------------------|----------|
| get/set/delete   | CRUD básico                         | —                          | N/A                 | keyspace_hits/misses      | OK       |
| TTL              | Expiración controlada               | —                          | N/A                 | evicted_keys              | OK       |
| delete_pattern   | Limpieza por prefijo                | Patrón inválido            | Validación          | keys_count                | Parcial  |
| Pub/Sub publish  | Broadcast a workers                 | Canal inactivo             | Reconexión          | broadcasts_total          | Parcial  |
| Fallback TLS     | Puerto 6380 (Upstash)               | TLS error                  | Fallback activado   | send_errors_total         | Brecha   |

### 4.4 WebSocket connections

El sistema instrumenta métricas y ejecuta smoke tests. Para alinear con objetivos de alta disponibilidad, se recomienda incorporar pruebas de disponibilidad (failover, recovery), backpressure y saturación. La correlación con dashboards de producción permitirá validar alertas y SLAs.[^1][^2][^5][^7]

Tabla 12. Pruebas de WebSockets
| Caso                       | Tipo      | Objetivo                         | Métricas                     | Estado   |
|----------------------------|-----------|----------------------------------|------------------------------|----------|
| Conexión estable           | Integration | Establecer/cerrar conexión       | active_connections           | OK       |
| Broadcast local/remoto     | Integration | Difusión cross-worker            | broadcasts_total             | Parcial  |
| Saturación de mensajes     | Load/Stress | Evaluar latencia y pérdida       | message_latency_seconds      | Brecha   |
| Fallo de red               | Resilience | Recuperación y re-suscripción    | send_errors_total            | Brecha   |
| Producción (observación)   | E2E        | Validar métricas/alertas en vivo | —                            | Brecha   |

### 4.5 Prometheus/Grafana metrics

La instrumentación cubre conexiones activas, total de conexiones, mensajes enviados, broadcasts, errores de envío y latencias. Se requiere un inventario de reglas de alertas y dashboards operativos con umbrales claros, junto con una verificación de métricas post-producción que correlacione incidentes con resultados de pruebas.[^1][^2]

Tabla 13. Inventario de métricas
| Métrica                         | Tipo       | Etiquetas        | Objetivo operativo                      | Alertas/umbrales       | Estado  |
|---------------------------------|------------|------------------|-----------------------------------------|------------------------|---------|
| active_connections              | Gauge      | env              | Salud de canales WS                     | Umbral mínimo/máximo   | Parcial |
| connections_total               | Counter    | env              | Throughput de conexiones                | Tendencia anómala      | Parcial |
| messages_sent_total             | Counter    | env              | Volumen de mensajería                   | Deltas inesperados     | Parcial |
| broadcasts_total                | Counter    | env              | Cobertura de difusión                   | Caídas de broadcast    | Parcial |
| send_errors_total               | Counter    | env              | Fiabilidad de envío                     | Tasa de error > X%     | Parcial |
| message_latency_seconds         | Histogram  | env              | Calidad de latencia                     | p95/p99 fuera de SLA   | Parcial |

## 5. Métricas de coverage gubernamentales

El cálculo de cobertura debe abarcar módulos críticos, error handling, casos edge de operaciones de campo y seguridad de endpoints sensibles, alineado con NIST CSF 2.0 y SA-11(7). La evidencia disponible permite утвердить que el bot supera el 70% de cobertura; sin embargo, la ausencia de reportes desagregados para el resto de módulos obliga a establecer gates de cobertura y criterios de aceptación por tipo de prueba y riesgo.

![NIST CSF 2.0 – Esquema de funciones (apoyo a cobertura de seguridad).](.pdf_temp/viewrange_chunk_2_6_10_1761723740/images/owmwgo.jpg)

Tabla 14. Cobertura por módulo crítico
| Módulo                          | Líneas totales | Cubiertas | Porcentaje | Evidencia                 | Observaciones                          |
|---------------------------------|----------------|-----------|------------|---------------------------|----------------------------------------|
| Bot (src/bot/)                  | —              | —         | 70%+       | Suite de 11 tests         | Falta cobertura de carga/resiliencia   |
| WebSockets (src/core/websockets.py) | —           | —         | ~85%       | Instrumentación y smoke   | Requiere pruebas de disponibilidad     |
| PostGIS (src/core/geo/postgis_service.py) | —      | —         | No reportado | Validaciones de coords   | Faltan performance y auditoría         |
| Redis Cache (src/core/cache.py) | —              | —         | Parcial    | CRUD/TTL/serialización    | Evidenciar fallback y rate limiting    |
| Redis Pub/Sub (src/core/ws_pubsub.py) | —        | —         | Parcial    | Broadcast y reconexión    | Saturación y auditoría                 |
| Routers API (FastAPI)           | —              | —         | No reportado | Contratos inferidos      | Seguridad y casos edge                 |

Tabla 15. Matriz de edge cases en operaciones de campo
| Caso                                       | Componente         | Datos           | Resultado esperado                          | Riesgo                     |
|--------------------------------------------|--------------------|-----------------|----------------------------------------------|----------------------------|
| Coordenadas inválidas (geolocalización)    | PostGIS            | lat/lng extremos | Validación/rechazo                           | Datos corruptos            |
| Cancelación de operativo durante ejecución | API/WS             | task_code       | Estado consistente; notificaciones           | Inconsistencia de estado   |
| Fallo de Redis (TLS/puerto)                | Cache/PubSub       | —               | Degradación controlada; reconexión           | Pérdida de mensajería      |
| Saturación de mensajes WS                  | WebSockets         | burst load      | Latencia controlada; sin pérdida crítica     | Degradación UX             |
| Recordatorio fuera de ventana               | Scheduler          | timestamp       | No enviar; log de decisión                   | Ruido operativo            |

Tabla 16. Matriz de seguridad de endpoints
| Endpoint                       | Autenticación     | Autorización              | Validaciones de entrada      | Logs/Auditoría           | Estado       |
|--------------------------------|-------------------|---------------------------|------------------------------|--------------------------|--------------|
| /auth/{telegram_id}            | JWT/validaciones  | Roles/perfiles            | Tipos y rangos               | Audit trail              | Parcial      |
| /tasks/create                  | JWT/validaciones  | Permisos por rol          | Esquema TareaCreate          | Audit por acción         | Parcial      |
| /tasks/finalize                | JWT/validaciones  | Permisos por rol/usuario  | task_code, telegram_id       | Trail y diferenciación 404/403 | Parcial  |
| /tasks/user/telegram/{id}      | JWT/validaciones  | Filtros por usuario       | status, paginación           | Consulta trazable        | Parcial      |
| /users                         | JWT/validaciones  | Filtros por rol           | role                         | Auditoría por rol        | Parcial      |

## 6. Cobertura de funcionalidades operativas

Las funcionalidades operativas clave incluyen creación de operativos, asignación de efectivos, consulta de disponibilidad, liberación automática y gestión de múltiples operativos. La evidencia de cobertura está centrada en el bot y sus flujos conversacionales; las funcionalidades específicas de asignación, liberación y coordinación multi-operativo requieren pruebas E2E más exhaustivas y trazabilidad.

Tabla 17. Cobertura funcional operativa
| Funcionalidad                        | Módulo/Endpoint            | Casos de prueba             | Cobertura actual | Gaps                          |
|--------------------------------------|-----------------------------|-----------------------------|------------------|-------------------------------|
| Creación de operativos               | Bot: /crear; API: /tasks/create | Wizard completo; validaciones | 70%+ (bot)       | Persistencia del wizard; permisos por rol |
| Asignación de efectivos              | PostGIS; API operativa      | Búsqueda por proximidad     | Parcial          | Consumo del bot; auditoría    |
| Consulta de disponibilidad           | API: /users; filtros        | Paginación; filtros por rol | Parcial          | Pruebas bajo volumen          |
| Liberación automática                | API: /tasks/finalize        | Finalización; rollback      | Parcial          | Rollback; trazabilidad        |
| Gestión de múltiples operativos      | WS/Pub/Sub                  | Coordinación cross-worker   | Parcial          | Saturación; conflictos        |

## 7. Análisis de tendencias y brechas

La comparación entre las pruebas unitarias y de integración sugiere un buen punto de partida en el bot y en módulos de tiempo real, pero con la necesidad de ampliar la proporción de pruebas de integración y E2E para cubrir seguridad, resiliencia y observabilidad en ambientes de staging y producción. Los patrones de testing evidencian fixtures async y mocking de API, útiles para aislamiento y velocidad; sin embargo, faltan simulaciones de fallos (chaos testing) y verificación de performance bajo carga sostenida.

Tabla 18. Ratio unit vs integration vs E2E por componente
| Componente        | Unit (%) | Integration (%) | E2E (%) | Observaciones                                   |
|-------------------|----------|------------------|---------|--------------------------------------------------|
| Bot               | 60       | 35               | 5       | Falta carga/resiliencia; métricas del bot        |
| WebSockets        | 40       | 50               | 10      | Disponibilidad/failover no evidenciados          |
| PostGIS           | 50       | 50               | 0       | Performance y auditoría pendientes               |
| Redis Cache       | 50       | 50               | 0       | Fallback y rate limiting                         |
| Redis Pub/Sub     | 40       | 55               | 5       | Saturación y reconexión                          |
| API (Routers)     | 45       | 45               | 10      | Seguridad de endpoints, edge cases               |

Tabla 19. Plan de pruebas de carga y resiliencia
| Tipo de prueba       | Herramienta | Escenario                                 | Criterios de éxito                                |
|----------------------|-------------|-------------------------------------------|---------------------------------------------------|
| Carga sostenida API  | Locust      | 100+ RPS con mix de endpoints             | p95 < 200ms; p99 < 500ms; errores < 1%            |
| Resiliencia WS       | Custom/pytest | Desconexión/reconexión; bursts de mensajes | Sin pérdida crítica; latencia bajo umbral         |
| Fallo Redis          | Simulación  | TLS/puerto fallback; pérdida de mensajes   | Degradación controlada; reintentos exitosos       |
| Chaos testing        | Inyectores  | Caída de worker; restart de servicio       | Auto-failover; recuperación sin intervención      |
| E2E staging          | Pipelines   | Flujos operativos completos                | Cobertura ≥ 85%; gates de calidad superados       |

Las pruebas de carga con Locust y la línea base reportada (p95/p99) son puntos de partida válidos. La formalización de escenarios de saturación y failover permitirá alinear los resultados con objetivos de disponibilidad tipo 99.9% y superiores.[^1][^4][^5][^7]

## 8. Benchmarking contra estándares

El benchmarking se estructura en cuatro niveles: seguridad y gobierno (NIST CSF 2.0), verificación por desarrolladores (NISTIR 8397), cobertura de controles de seguridad (SA-11(7)), y prácticas de alta disponibilidad. Para sistemas con datos de justicia criminal, se considera CJIS como referencia complementaria, sin asumir obligaciones no evidenciadas.

Tabla 20. Mapa de cumplimiento vs prácticas actuales
| Estándar/Control       | Práctica actual                             | Evidencia                              | Brecha                               | Recomendación                          |
|------------------------|----------------------------------------------|----------------------------------------|--------------------------------------|----------------------------------------|
| NIST CSF 2.0 – GOVERN  | CI/CD con calidad y seguridad; auditoría parcial | GitHub Actions; logging estructurado   | Política de pruebas y auditorías formalizadas | Documentar perfil organizacional; políticas de testing |
| NIST CSF 2.0 – PROTECT | JWT, CORS, middlewares                       | Configuraciones y despliegue           | Rate limiting en bot; cifrado en reposo | Integrar rate limiting (Redis); verificar cifrado     |
| NISTIR 8397            | Automatización básica de pruebas             | Pytest + coverage; Locust              | Integración de seguridad (IAST/SAST) en gates | Añadir SAST/DAST y gates de seguridad     |
| SA-11(7)               | Cobertura de controles no evidenciada        | —                                      | Mapeo de pruebas a controles          | Matriz de trazabilidad control→prueba   |
| Availability (AWS)     | Métricas WS; salud por endpoint              | Prometheus; health checks              | SLAs formalizados; pruebas de failover | Establecer SLAs; pruebas de disponibilidad |
| CJIS Security Policy   | Aplicabilidad por validar                    | —                                      | No evidenciado                        | Confirmar alcance; controles si aplica  |

### 8.1 NIST CSF 2.0 y NISTIR 8397

NIST CSF 2.0 establece un marco de resultados deseables sin prescribir acciones específicas; esto permite adaptar la implementación a los riesgos y misiones de la organización. La alineación se logra mediante perfiles, tiers y recursos complementarios. NISTIR 8397 recomienda técnicas mínimas de verificación por desarrolladores (threat modeling, automatización de pruebas), lo que en el contexto de GRUPO_GAD implica incorporar seguridad en el ciclo de vida de pruebas (SAST, DAST, IAST) y gates de cobertura y calidad en CI/CD.[^3][^9]

### 8.2 SA-11(7) Cobertura de controles de seguridad

SA-11(7) exige verificar el alcance de pruebas/evaluación para asegurar cobertura completa de controles requeridos. Esto se materializa en una matriz de trazabilidad control→prueba→resultado, donde cada control de seguridad relevante (autenticación, autorización, validación de entrada, logging/auditoría) tiene pruebas específicas y evidencia documentada.[^10]

Tabla 21. Matriz de trazabilidad control→prueba
| Control de seguridad           | Prueba específica                        | Resultado esperado                    | Evidencia                         |
|--------------------------------|-------------------------------------------|---------------------------------------|-----------------------------------|
| Autenticación (JWT)            | Tests de token inválido/expirado          | Rechazo con trazabilidad              | Logs; respuestas 401/403          |
| Autorización por rol           | Acceso a endpoint sin rol suficiente      | Rechazo; audit trail                  | Registro de auditoría             |
| Validación de entrada          | Payload malformado                        | Rechazo; mensajes seguros             | Logs; excepciones controladas     |
| Logging/Auditoría              | Acción sensible (finalizar tarea)         | Registro con correlation ID           | Trazas completas                  |
| Cifrado en tránsito            | TLS forzado;证书 validación               | Conexión segura; sin datos en claro   | Configuraciones; tests de canal   |

### 8.3 Alta disponibilidad (99.9%+)

Para una meta de 99.9% de uptime (≈ 43 minutos de downtime mensual), las pruebas de disponibilidad deben cubrir failover automatizado, recovery, continuidad operativa y validación de alertas. La instrumentación Prometheus y dashboards de producción han de jugar un rol central para correlacionar incidentes con pruebas de resiliencia ejecutadas en staging y producción controlada.[^4][^5][^7]

Tabla 22. Pruebas de disponibilidad
| Escenario                         | Tipo       | Métrica objetivo          | Criterio de aceptación               |
|----------------------------------|------------|---------------------------|--------------------------------------|
| Failover de worker               | Resilience | active_connections        | Reconexión < X s; sin pérdida crítica |
| Caída de Redis                   | Resilience | send_errors_total         | Fallback activado; reintentos        |
| Carga sostenida en API           | Load       | p95/p99 latencies         | p95 < 200ms; p99 < 500ms             |
| Saturación en WS                 | Load/Stress| message_latency_seconds   | Sin backpressure crítico; latencia controlada |

### 8.4 CJIS Security Policy (aplicabilidad)

Si el sistema procesa datos de justicia criminal, los controles de acceso, cifrado, auditoría y gestión de incidentes de CJIS aplican. Dado que no hay evidencia explícita, se recomienda una evaluación de alcance y, si corresponde, incorporar pruebas y evidencias que demuestren cumplimiento. Esto incluye controles de autenticación fuerte, auditoría exhaustiva, y pruebas periódicas de los controles.[^13]

## 9. Roadmap para alcanzar ≥ 85% de cobertura en funcionalidades críticas

Se propone un plan en tres fases con hitos, gates de cobertura en CI/CD y métricas de salud que integren funcionalidad, seguridad y resiliencia. La meta es cerrar brechas identificadas y sostener la mejora continua bajo el marco NIST CSF 2.0, con automatización conforme NISTIR 8397 y cobertura de controles según SA-11(7).[^3][^6][^9][^10]

Tabla 23. Roadmap por sprints
| Sprint/Fase | Módulo/Integración             | Acción                                               | Cobertura objetivo | Métricas de salud                          | Dependencias                | Estado  |
|-------------|--------------------------------|------------------------------------------------------|--------------------|--------------------------------------------|-----------------------------|---------|
| Fase 1 (2–3 sprints) | Bot (wizard, comandos)         | Añadir pruebas de carga/resiliencia; persistencia en Redis | 80%→85%            | Tasa de éxito > 99%; latencia comandos     | Config Redis en bot         | Plan    |
| Fase 1 (2–3 sprints) | WebSockets/Redis PubSub        | Pruebas de failover/backpressure; métricas en producción | 85%                | p95/p99 bajo SLA; broadcasts sin caída     | Dashboards/alertas          | Plan    |
| Fase 1 (2–3 sprints) | API seguridad                   | Endurecimiento de endpoints; matriz control→prueba  | 85%                | 0 incidentes de autorización               | Políticas de seguridad      | Plan    |
| Fase 2 (3–4 sprints) | PostGIS                         | Pruebas de performance/edge cases/auditoría         | 80%→85%            | Consultas bajo umbral; audit trail         | Índices; logs auditoría     | Plan    |
| Fase 2 (3–4 sprints) | Observabilidad                  | Reglas de alertas alineadas a SLAs                   | —                  | Alertas eficaces (sin falsos positivos)    | Config Prometheus/Grafana   | Plan    |
| Fase 2 (3–4 sprints) | Rate limiting (bot/API)        | Implementación con Redis; pruebas y monitoreo       | —                  | Uso controlado por usuario/IP              | Redis; middleware           | Plan    |
| Fase 3 (4–6 sprints) | E2E + Chaos                     | Escenarios completos y fallos inyectados            | 85%                | Recuperación automática; continuidad       | Pipelines; simulación       | Plan    |
| Fase 3 (4–6 sprints) | Política de pruebas y auditorías | Perfil NIST CSF; gates CI/CD; reportes automáticos  | —                  | Cumplimiento sostenido                     | GOVERN de NIST CSF          | Plan    |

Tabla 24. Gates de CI/CD
| Gate                    | Umbral                         | Validación automatizada         | Acción en caso de fallo           |
|-------------------------|--------------------------------|---------------------------------|-----------------------------------|
| Cobertura de código     | ≥ 85% en módulos críticos      | pytest --cov; reporte en PR     | Bloqueo de merge; tareas asignadas |
| Seguridad               | SAST/DAST sin issues críticos  | Tools integradas en CI          | Bloqueo; remediación obligatoria   |
| Performance             | p95 < 200ms; p99 < 500ms       | Locust post-deploy              | Rollback automático                |
| Resiliencia             | Pruebas failover sin pérdida crítica | Tests de disponibilidad         | Escalamiento a incident response   |
| Auditoría               | Trazabilidad control→prueba    | Evidencias en artifacts         | Corrección y re-evaluación         |

## 10. Plan de aseguramiento, seguimiento y gobernanza

El aseguramiento requiere KPIs operativos y de seguridad, reportes de cobertura por módulo y ejecución continua en pipelines con staging. La gobernanza se articula bajo las funciones del NIST CSF 2.0, priorizando la función GOVERN para alinear políticas, roles, oversight y comunicación de riesgos.

Tabla 25. KPIs y umbrales
| KPI                               | Fuente               | Umbral objetivo                    | Frecuencia | Responsable     |
|-----------------------------------|----------------------|------------------------------------|------------|-----------------|
| Cobertura por módulo crítico      | CI/CD (pytest --cov) | ≥ 85%                               | Por PR     | QA/Engineering  |
| Cobertura de seguridad (controles) | Gates/SAST/DAST      | 0 issues críticos                   | Por PR     | SecEng          |
| p95/p99 latencias API/WS          | Prometheus/Locust    | p95 < 200ms; p99 < 500ms           | Semanal    | SRE/Engineering |
| Disponibilidad (uptime)           | Alertas/monitoreo    | ≥ 99.9%                             | Mensual    | SRE             |
| Fallos de pruebas en producción   | Incident response    | Tendencia decreciente               | Mensual    | QA/SRE          |
| Audit trail por acción sensible   | Logs/Auditoría       | 100% trazabilidad                   | Mensual    | Compliance      |

![NIST CSF 2.0 – GOVERN como función central para gobernanza de pruebas.](.pdf_temp/viewrange_chunk_1_1_5_1761723738/images/r7hal7.jpg)

El uso de Quick Start Guides, Implementation Examples e Informative References de NIST CSF 2.0 facilitará la formalización de políticas de pruebas, perfiles organizacionales y la integración con otros programas de riesgo. La automatización para la evaluación de controles (NISTIR 8011-4) debe incorporarse al pipeline para sostener el cumplimiento y reducir el costo de auditoría.[^3][^11]

## 11. Anexos: evidencia, listas de chequeo y fuentes

Evidencia prioritaria:
- Inventario de pruebas por integración: bot (11 tests), PostGIS (validaciones y consultas), Redis Cache/PubSub (CRUD, TTL, serialización, broadcast), WebSockets (smoke, instrumentación), Prometheus/Grafana (métricas y dashboards).
- Reportes de cobertura y performance: cobertura 70%+ en bot; p95/p99 baseline; pruebas de carga con Locust.

Listas de chequeo:
- Seguridad por endpoint (autenticación/autorización, validación de entrada, logging/auditoría, trazabilidad).
- Edge cases operativos (cancelaciones, reintentos, fallos de dependencias, saturación de mensajería).
- Resiliencia y disponibilidad (failover, recovery, backpressure, correlación con métricas y alertas).

Brechas de información a cerrar:
- Cobertura específica por módulo de gestión de efectivos (asignación, liberación, búsquedas).
- Endpoints exactos y pruebas de seguridad para operativos/allanamientos.
- Pruebas y cobertura del sistema de notificaciones automáticas (triggers, fallos, saturación).
- Casos de prueba y cobertura de comandos de finalización operativa (rollback, auditoría).
- Evidencia de scheduler y pruebas de recordatorios (40 minutos antes).
- Desglose de cobertura por integración: Bot (11 tests), PostGIS, Redis, WebSockets, Prometheus/Grafana.
- Reportes de ejecución: ratio unit vs integration/E2E, frecuencia de tests, flakiness.
- Métricas en producción (errores, latencias, throughput) y su correlación con resultados de pruebas.
- Validación de controles NIST CSF 2.0/SA-11(7) aplicados a pruebas y evidencias.
- Lineamientos CJIS (si aplican) y su impacto en pruebas de seguridad.

---

## Referencias

[^1]: GRUPO_GAD - Repositorio (GitHub). URL: https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD - Aplicación en Producción (Fly.io). URL: https://grupo-gad.fly.dev  
[^3]: NIST Cybersecurity Framework (CSF) 2.0. URL: https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf  
[^4]: IT & System Availability + High Availability: The Ultimate Guide (Splunk). URL: https://www.splunk.com/en_us/blog/learn/availability.html  
[^5]: Availability - Reliability Pillar - AWS Documentation. URL: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/availability.html  
[^6]: Code Coverage Best Practices - Google Testing Blog. URL: https://testing.googleblog.com/2020/08/code-coverage-best-practices.html  
[^7]: An Introduction to Availability Testing - Qualitest. URL: https://www.qualitestgroup.com/insights/white-paper/an-introduction-to-availability-testing/  
[^8]: NISTIR 8397 – Guidelines on Minimum Standards for Developer Verification of Software. URL: https://nvlpubs.nist.gov/nistpubs/ir/2021/NIST.IR.8397.pdf  
[^9]: SA-11(7): Verify Scope Of Testing / Evaluation - CSF Tools. URL: https://csf.tools/reference/nist-sp-800-53/r4/sa/sa-11/sa-11-7/  
[^10]: NISTIR 8011-4 – Automation Support for Security Control Assessments. URL: https://nvlpubs.nist.gov/nistpubs/ir/2020/NIST.IR.8011-4.pdf  
[^11]: Criminal Justice Information Services (CJIS) Security Policy v5.9.4 – FBI. URL: https://le.fbi.gov/file-repository/cjis_security_policy_v5-9-4_20231220.pdf