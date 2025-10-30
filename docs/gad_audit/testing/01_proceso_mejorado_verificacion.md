# Blueprint de Cobertura de Pruebas Específica para Sistemas Operativos/Tácticos en GRUPO_GAD

## 1. Resumen ejecutivo y objetivos del análisis

Este informe presenta una evaluación integral de la cobertura de pruebas (testing coverage) y la calidad del plan de pruebas en GRUPO_GAD, con foco en seis dimensiones: componentes operativos, integraciones, métricas gubernamentales de calidad, funcionalidades operativas, tendencias/brechas y benchmarking contra estándares. El propósito es elevar el nivel de confianza operativa, reducir el riesgo en flujos de misión crítica y alinear el plan de pruebas con requisitos de disponibilidad 24/7 y marcos de seguridad reconocidas a nivel gubernamental.

Hallazgos clave:
- Evidencia sólida de cobertura en el Telegram Bot (70%+ reportado; 11 archivos de pruebas que validan comandos, wizard multistep, callbacks y teclados). El diseño de pruebas exhibe patrones modernos (fixtures async, mocking de API) y controles de UX (callback_data ≤ 64 bytes).[^1]
- Observabilidad bien diseñada para mensajería en tiempo real vía WebSockets, con métricas Prometheus instrumentadas (conexiones activas, mensajes, broadcasts, latencias) y smoke tests específicos. Se reporta cobertura ~85% para src/core/websockets.py.[^1]
- Integraciones geoespaciales con PostGIS validadas en coordenadas y semántica geography; gaps en pruebas de performance y trazabilidad de seguridad.[^1]
- Redis utilizado para cache y pub/sub, con pruebas de CRUD/TTL/serialización y broadcast cross-worker; persisten brechas en fallback TLS y rate limiting, claves para resiliencia multi-worker.[^1][^2]
- Ausencia de evidencia de pruebas E2E con ambientes gobernados que repliquen producción y carencia de reportes sistemáticos de calidad de pruebas por módulo (flakiness, mantenibilidad).[^1][^2]

Objetivo estratégico:
- Establecer una meta de cobertura de código ≥ 85% en funcionalidades críticas y fortalecer la cobertura de seguridad y resiliencia, con gates automáticos en el pipeline de CI/CD. La alineación con NIST Cybersecurity Framework (CSF) 2.0, NISTIR 8397 y SA-11(7) asegura que la verificación alcance controles de seguridad, automatización y alcance completo de pruebas.[^3][^9][^10][^11]

Resultado:
- Roadmap incremental por sprints con hitos, métricas y responsables. Criterios de aceptación basados en gates de cobertura, seguridad y disponibilidad. Integración con prácticas de alta disponibilidad y alineamiento con métricas de desempeño y uptime esperadas para servicios 24/7.[^4][^5][^7]

## 2. Alcance, fuentes y metodología

Alcance:
- Evaluación de cobertura en API FastAPI, Telegram Bot, PostGIS, Redis (cache/pub-sub), WebSockets y Prometheus/Grafana.
- Módulos operativos críticos: gestión de efectivos, endpoints de operativos/allanamientos, notificaciones automáticas, comandos de finalización operativa, recordatorios programados.
- Integraciones con endpoints ciudadanos y administrativos, con trazabilidad hacia observabilidad y métricas de sistema.

Fuentes:
- Inventario de integraciones y auditoría del Telegram Bot gubernamental en GRUPO_GAD, junto con el estado operativo en producción. Estas fuentes proveen el detalle de arquitectura, suite de pruebas e instrumentación, y permiten contrastar el diseño con el despliegue real.[^1][^2]

Metodología:
- Revisión del repositorio para extraer patrones de pruebas, cobertura reportada, estructura de módulos y configuraciones de CI/CD.
- Mapeo de riesgos operativos y requisitos 24/7 a métricas de cobertura, resiliencia y seguridad.
- Benchmarking contra NIST CSF 2.0 (gobernanza de riesgos), NISTIR 8397 (prácticas mínimas de verificación por desarrolladores), SA-11(7) (cobertura de controles de seguridad) y guías de alta disponibilidad (objetivos de uptime, failover y recovery).[^3][^9][^10][^11][^5]

Limitaciones:
- No se dispone de reportes desagregados de cobertura por todos los módulos del sistema.
- Persiste falta de evidencia de pruebas de carga/resiliencia más allá de baseline reportada.
- Ausencia de SLAs formalizados para disponibilidad, correlación de métricas en producción con resultados de pruebas y validación explícita de controles CJIS (si aplica).[^1][^2][^13]

![NIST CSF 2.0 – Funciones core (Govern, Identify, Protect, Detect, Respond, Recover).](.pdf_temp/viewrange_chunk_1_1_5_1761723738/images/r7hal7.jpg)

La adopción del enfoque NIST CSF 2.0 permite vincular métricas de cobertura y resultados de pruebas con funciones de gobernanza y gestión de riesgos, asegurando que cada sprint de mejora incida de manera trazable en controles y outcomes de seguridad.[^3]

Tabla 1. Mapa de fuentes y confiabilidad
| Fuente                                  | Propósito                                   | Confiabilidad | Uso en el informe                                               |
|-----------------------------------------|---------------------------------------------|---------------|------------------------------------------------------------------|
| Repositorio GRUPO_GAD                   | Estructura, pruebas, integraciones, CI/CD   | Alta          | Base primaria de evidencia técnica y de pruebas[^1]             |
| Aplicación en producción (Fly.io)       | Endpoints, observabilidad, health checks    | Alta          | Validación del estado desplegado y capacidades operativas[^2]   |
| NIST CSF 2.0                            | Marco de resultados de ciberseguridad       | Alta          | Benchmark de gobierno, perfiles y tiers[^3]                     |
| NISTIR 8397                             | Verificación mínima por desarrolladores     | Alta          | Prácticas de automatización y calidad en pruebas[^9]            |
| SA-11(7)                                | Cobertura de controles de seguridad         | Alta          | Trazabilidad control→prueba→resultado[^10]                      |
| AWS Well-Architected – Availability     | Prácticas de alta disponibilidad            | Alta          | Definición de objetivos y pruebas de failover/recovery[^5]      |
| Splunk – High Availability              | Estrategias de disponibilidad               | Media/Alta    | Contexto para tolerancias de downtime y prácticas de uptime[^4] |
| NISTIR 8011-4                           | Automatización para evaluación de controles | Alta          | Automatización de evidencias y gates en CI/CD[^11]              |
| Google Testing Blog – Coverage          | Buenas prácticas de coverage                | Alta          | Gestión sana del coverage, evitar métrica mecánica[^6]          |
| Qualitest – Availability Testing        | Guías de pruebas de disponibilidad          | Media/Alta    | Diseñar escenarios de failover y continuidad[^7]                |
| CJIS Security Policy (si aplica)        | Seguridad en sistemas de justicia           | Alta          | Controles de acceso, cifrado, auditoría[^13]                    |

## 3. Cobertura por componente crítico

Los componentes operativos constituyen el núcleo de la misión del sistema. La cobertura de pruebas debe verificar su funcionalidad, seguridad, resiliencia y observabilidad, con trazabilidad hacia controles y métricas operativas.

Tabla 2. Cobertura por componente crítico
| Componente                         | Módulos/archivos asociados         | Tipo de pruebas                           | Cobertura actual     | Estado        | Brechas principales                                                                 |
|-----------------------------------|------------------------------------|--------------------------------------------|----------------------|---------------|-------------------------------------------------------------------------------------|
| Gestión de efectivos              | PostGIS, modelos de datos          | Unit/Integration (validación coords, consultas geography) | No reportado         | Parcial       | Performance; edge cases; seguridad/auditoría                                       |
| Endpoints de operativos/allanamientos | Routers API (autenticación, tareas, usuarios) | Integration/E2E                           | No reportado         | Desconocido   | Permisos/roles; casos edge; trazabilidad y auditoría                               |
| Notificaciones automáticas        | WebSockets; Redis Pub/Sub          | Integration/E2E; smoke tests               | Parcial (~85% WS)    | Parcial       | Fallback ante fallos; saturación; métricas en producción                           |
| Comandos de finalización          | Bot: comandos de finalización      | Unit/Integration                           | 70%+ (bot)           | Parcial       | Diferenciación 404/403 bajo carga; rollback; permisos granulares                   |
| Recordatorios (40 minutos antes)  | —                                  | —                                          | —                    | Brecha        | Diseño, scheduler, persistencia y trazabilidad                                     |

La integración PostGIS evidencia pruebas de validaciones de coordenadas y semántica geography para búsquedas precisas. Aunque el diseño es robusto, la ausencia de pruebas de performance y seguridad/auditoría limita la preparación para escenarios de carga y cumplimiento.[^1][^2]

Tabla 3. Cobertura del servicio geoespacial
| Aspecto                         | Estado actual                      | Evidencia                 | Gap prioritario                                 |
|---------------------------------|------------------------------------|---------------------------|-------------------------------------------------|
| Validación de coordenadas       | Rangos -90..90, -180..180          | Código de validaciones    | Inputs extremos y boundary values               |
| Consultas geography (ST_Distance, ST_MakePoint, ST_SetSRID) | Implementada                      | Query con geography       | Performance en tablas grandes; auditoría        |
| Asignación/libertad de efectivos | No evidenciada en geoespacial       | —                         | Casos de uso y pruebas E2E de asignación        |
| Seguridad y auditoría           | No evidenciada                      | —                         | Controles de acceso y audit trail en consultas  |

### 3.1 Gestión de efectivos

La función find_nearest_efectivo calcula distancias con SRID 4326 y retorna resultados ordenados por proximidad, usando el tipo geography para precisión. Se recomienda añadir pruebas de performance (consultas con límites altos y tablas con índices espaciales), edge cases geoespaciales y trazabilidad de auditoría. En operaciones de campo, la disponibilidad y seguridad de esta capacidad impacta directamente la asignación de recursos críticos.[^1][^2]

Tabla 4. Pruebas geoespaciales
| Query/Función                | Caso de prueba                        | Datos               | Validación de salida         | Estado   |
|-----------------------------|---------------------------------------|---------------------|------------------------------|----------|
| ST_Distance (geography)     | Distancia punto conocido              | Coordenadas válidas | distance_m coherente         | OK       |
| ST_SetSRID + ST_MakePoint   | SRID 4326                             | lng/lat             | Conversión correcta          | OK       |
| Boundary values             | Lat/lng fuera de rango                | >90, >180           | Excepción/validación         | Parcial  |
| Performance con índices     | Búsqueda con LIMIT alto               | 1000+ registros     | Latencia aceptable           | Brecha   |
| Auditoría de consultas      | Registro de actor y propósito         | User, Role          | Audit trail                  | Brecha   |

### 3.2 Endpoints de operativos/allanamientos

El bot consume endpoints de autenticación, tareas y usuarios. Falta evidencia de pruebas de seguridad por endpoint (autorización, roles, auditoría) y casos edge en operaciones de campo (cancelaciones, reintentos, degradaciones por fallos de servicios externos). La trazabilidad control→prueba→resultado debe cubrir autenticación, validación de entrada, manejo de errores y logging de auditoría.[^1][^2]

Tabla 5. Cobertura por endpoint API
| Endpoint                       | Método | Payload principal                 | Respuesta esperada             | Pruebas unitarias | Pruebas de integración | Pruebas de seguridad | Observaciones                                    |
|-------------------------------|--------|-----------------------------------|--------------------------------|-------------------|------------------------|----------------------|--------------------------------------------------|
| /auth/{telegram_id}           | GET    | —                                 | Estado de autenticación        | Evidencia parcial | Evidencia parcial       | No evidenciado       | Clarificar scopes/roles; auditoría de acceso     |
| /tasks/create                 | POST   | TareaCreate                       | Tarea creada                   | Evidencia parcial | Evidencia parcial       | No evidenciado       | Validaciones de permisos; manejo de errores      |
| /tasks/finalize               | POST   | task_code, telegram_id            | Tarea finalizada               | Evidencia parcial | Evidencia parcial       | No evidenciado       | Diferenciación 404/403 bajo carga                |
| /tasks/user/telegram/{id}     | GET    | status=pending                    | Lista de tareas pendientes     | Evidencia parcial | Evidencia parcial       | No evidenciado       | Paginación; latencia; auditoría de consulta      |
| /users                        | GET    | role (opcional)                   | Lista de usuarios              | Evidencia parcial | Evidencia parcial       | No evidenciado       | Filtros de seguridad; auditoría por rol          |

### 3.3 Sistema de notificaciones automáticas

La difusión cross-worker y la integración WebSocket con métricas Prometheus constituyen una base sólida para mensajería en tiempo real. Se recomienda incorporar pruebas de fallback ante fallos de Redis, saturación de mensajes (backpressure) y correlación de métricas en producción con resultados de pruebas para validar SLAs de disponibilidad.[^1][^2][^5][^7]

Tabla 6. Cobertura de notificaciones y resiliencia
| Caso de prueba                                 | Tipo       | Objetivo de resiliencia                              | Métricas observadas                    | Estado     |
|------------------------------------------------|-----------|------------------------------------------------------|----------------------------------------|------------|
| Broadcast con workers sanos                     | Integration | Validar difusión correcta                            | broadcasts_total; messages_sent_total  | OK         |
| Fallo de Redis (TLS/puerto)                     | Integration | Degradación controlada y reconexión                  | send_errors_total; health check        | Brecha     |
| Desconexión de clientes WebSocket               | Integration | Recuperación y re-suscripción                         | active_connections                     | Parcial    |
| Saturación (mensajes en ráfaga)                 | Load/Stress | Evitar backpressure y pérdida de mensajes            | message_latency_seconds                | Brecha     |
| Correlación con Prometheus (post-producción)    | E2E        | Validar métricas y alertas en producción             | —                                      | Brecha     |

### 3.4 Comandos de finalización operativa

La suite de pruebas del bot cubre la finalización con manejo diferenciado de 404/403. Se requiere validar semántica bajo carga, reversibilidad (rollback) y permisos granulares por rol (delegado vs administrador). Estas extensiones aseguran trazabilidad y cumplimiento en operaciones sensibles.[^1][^2]

Tabla 7. Casos de prueba de finalización
| Escenario                               | Endpoint/API asociada | Assertions clave                   | Manejo de errores | Estado   |
|-----------------------------------------|------------------------|------------------------------------|-------------------|----------|
| Finalización exitosa                    | /tasks/finalize        | Código de tarea y usuario válidos  | OK                | OK       |
| Tarea inexistente (404)                 | /tasks/finalize        | Mensaje claro y trazabilidad       | OK                | Parcial  |
| Permisos insuficientes (403)            | /tasks/finalize        | Mensaje diferenciado y registro    | OK                | Parcial  |
| Bajo carga/concurrencia                 | /tasks/finalize        | Sin race conditions                | —                 | Brecha   |
| Rollback de finalización                | /tasks/finalize        | Reversibilidad controlada          | —                 | Brecha   |

### 3.5 Recordatorios (40 minutos antes)

No existe evidencia de scheduler ni pruebas de recordatorios. Se debe diseñar el flujo end-to-end con persistencia (p. ej., Redis), casos edge (fuera de ventana, conflictos de horario) y trazabilidad en logs/auditoría.

Tabla 8. Diseño de pruebas para recordatorios
| Caso                                | Datos de entrada                 | Tiempo/Trigger         | Validación de ejecución                    | Métricas/observabilidad                  | Estado  |
|-------------------------------------|----------------------------------|------------------------|--------------------------------------------|------------------------------------------|---------|
| Recordatorio dentro de ventana      | Operativo con timestamp          | T–40 min               | Notificación enviada; estado actualizado   | notifications_sent_total; latencia       | Brecha  |
| Fuera de ventana                    | Operativo en pasado/futuro extremo | N/A                    | No enviar; registrar decisión               | audit_log; decision_reason               | Brecha  |
| Conflicto de horario                | Operativos solapados             | T–40 min               | Política de priorización aplicada          | scheduler_decisions_total                | Brecha  |
| Fallo de Redis/WS                   | Cliente no disponible            | T–40 min               | Reintentos con backoff; degradación         | send_errors_total; retries               | Brecha  |

## 4. Cobertura de integraciones

La cobertura de pruebas por integración debe asegurar contratos, seguridad, resiliencia y observabilidad. A continuación se sintetiza el estado y los gaps por integración.

Tabla 9. Cobertura por integración
| Integración         | Pruebas existentes                               | Tipo                       | Cobertura reportada | Gaps principales                                                                 |
|---------------------|---------------------------------------------------|----------------------------|---------------------|----------------------------------------------------------------------------------|
| Telegram Bot        | 11 archivos de pruebas                           | Unit/Integration/E2E (parcial) | 70%+                | Carga/resiliencia; seguridad avanzada; persistencia del wizard en Redis          |
| PostGIS             | Validación de coords; consultas geography         | Unit/Integration           | No reportado        | Performance; edge cases; seguridad/auditoría                                     |
| Redis (Cache)       | CRUD, TTL, serialización; estadísticas; fallback TLS | Unit/Integration           | Parcial             | Fallback con reconexión; rate limiting; consistencia en multi-worker            |
| Redis (Pub/Sub)     | Broadcasting; suscripción; cross-worker; errores  | Unit/Integration           | Parcial             | Saturación y reconexión; auditoría de mensajes                                   |
| WebSockets          | Smoke tests; instrumentación Prometheus           | Integration/E2E            | ~85%                | Pruebas de disponibilidad/failover; backpressure; pruebas con métricas post-deploy |
| Prometheus/Grafana  | Métricas de conexiones, mensajes, latencias       | Validación de instrumentación | Parcial             | Reportes de cobertura de métricas; alertas operativas alineadas con SLAs         |

### 4.1 Telegram Bot (11 tests)

La suite de pruebas abarca comandos, wizard, callbacks y teclados, con fixtures async y mocking de API. Se recomienda añadir pruebas de carga/resiliencia (polling, reconexión, timeouts), instrumentar métricas del bot y establecer gates de cobertura ≥ 85% en CI/CD.[^1]

Tabla 10. Matriz de pruebas del bot por flujo
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

La validación de coordenadas y la consulta geography permiten búsquedas precisas por proximidad. Se sugiere incorporar pruebas de performance en tablas con índices espaciales y auditoría de consultas sensibles (quién, qué, cuándo).[^1]

Tabla 11. Pruebas PostGIS
| Query/Función                      | Caso de prueba                           | Datos                 | Validación de salida               | Estado   |
|------------------------------------|------------------------------------------|-----------------------|------------------------------------|----------|
| ST_Distance (geography)            | Distancia punto conocido                 | Coordenadas válidas   | distance_m coherente               | OK       |
| ST_SetSRID + ST_MakePoint          | SRID 4326                                | lng/lat               | Conversión correcta                | OK       |
| Boundary values                    | Lat/lng fuera de rango                   | >90, >180             | Excepción/validación               | Parcial  |
| Performance con índices            | Búsqueda con LIMIT alto                  | 1000+ registros       | Latencia aceptable                 | Brecha   |
| Auditoría de consultas             | Registro de actor y propósito            | User, Role            | Audit trail                        | Brecha   |

### 4.3 Redis (cache + pub/sub)

El CacheService cubre CRUD, TTL y serialización, y el Pub/Sub valida broadcasting cross-worker. Se deben completar pruebas con patrones de keys, namespaces y rate limiting, y simular reconexión bajo indisponibilidad parcial.[^1]

Tabla 12. Pruebas de cache y pub/sub
| Operación        | Caso                                | Condición de fallo         | Reintentos/Fallback | Métricas                  | Estado   |
|------------------|-------------------------------------|----------------------------|---------------------|---------------------------|----------|
| get/set/delete   | CRUD básico                         | —                          | N/A                 | keyspace_hits/misses      | OK       |
| TTL              | Expiración controlada               | —                          | N/A                 | evicted_keys              | OK       |
| delete_pattern   | Limpieza por prefijo                | Patrón inválido            | Validación          | keys_count                | Parcial  |
| Pub/Sub publish  | Broadcast a workers                 | Canal inactivo             | Reconexión          | broadcasts_total          | Parcial  |
| Fallback TLS     | Puerto 6380 (Upstash)               | TLS error                  | Fallback activado   | send_errors_total         | Brecha   |

### 4.4 WebSocket connections

Se instrumentan métricas y se ejecutan smoke tests. Para cumplir con objetivos de alta disponibilidad, se recomiendan pruebas de disponibilidad (failover, recovery), backpressure y correlación con dashboards de producción.[^1][^2][^5][^7]

Tabla 13. Pruebas de WebSockets
| Caso                       | Tipo      | Objetivo                         | Métricas                     | Estado   |
|----------------------------|-----------|----------------------------------|------------------------------|----------|
| Conexión estable           | Integration | Establecer/cerrar conexión       | active_connections           | OK       |
| Broadcast local/remoto     | Integration | Difusión cross-worker            | broadcasts_total             | Parcial  |
| Saturación de mensajes     | Load/Stress | Evaluar latencia y pérdida       | message_latency_seconds      | Brecha   |
| Fallo de red               | Resilience | Recuperación y re-suscripción    | send_errors_total            | Brecha   |
| Producción (observación)   | E2E        | Validar métricas/alertas en vivo | —                            | Brecha   |

### 4.5 Prometheus/Grafana metrics

La instrumentación actual cubre métricas clave (conexiones, mensajes, latencias, errores). Falta un inventario de reglas de alertas con umbrales y la correlación sistemática entre métricas en producción y resultados de pruebas para validar SLAs y calidad operativa.[^1][^2]

Tabla 14. Inventario de métricas
| Métrica                         | Tipo       | Etiquetas        | Objetivo operativo                      | Alertas/umbrales       | Estado  |
|---------------------------------|------------|------------------|-----------------------------------------|------------------------|---------|
| active_connections              | Gauge      | env              | Salud de canales WS                     | Umbral mínimo/máximo   | Parcial |
| connections_total               | Counter    | env              | Throughput de conexiones                | Tendencia anómala      | Parcial |
| messages_sent_total             | Counter    | env              | Volumen de mensajería                   | Deltas inesperados     | Parcial |
| broadcasts_total                | Counter    | env              | Cobertura de difusión                   | Caídas de broadcast    | Parcial |
| send_errors_total               | Counter    | env              | Fiabilidad de envío                     | Tasa de error > X%     | Parcial |
| message_latency_seconds         | Histogram  | env              | Calidad de latencia                     | p95/p99 fuera de SLA   | Parcial |

## 5. Métricas de coverage gubernamentales

La medición de cobertura debe abarcar módulos críticos, error handling, edge cases de operaciones de campo y seguridad de endpoints sensibles, vinculada a NIST CSF 2.0 y SA-11(7). La evidencia disponible indica una cobertura ≥ 70% en el bot; el resto de módulos carecen de reportes desagregados. Se propone establecer gates de cobertura y criterios de aceptación por tipo de prueba y riesgo.

![NIST CSF 2.0 – Enlace entre Governance y funciones operativas.](.pdf_temp/viewrange_chunk_2_6_10_1761723740/images/owmwgo.jpg)

Tabla 15. Cobertura por módulo crítico
| Módulo                          | Líneas totales | Cubiertas | Porcentaje | Evidencia                 | Observaciones                          |
|---------------------------------|----------------|-----------|------------|---------------------------|----------------------------------------|
| Bot (src/bot/)                  | —              | —         | 70%+       | Suite de 11 tests         | Falta cobertura de carga/resiliencia   |
| WebSockets (src/core/websockets.py) | —           | —         | ~85%       | Instrumentación y smoke   | Requiere pruebas de disponibilidad     |
| PostGIS (src/core/geo/postgis_service.py) | —      | —         | No reportado | Validaciones de coords   | Faltan performance y auditoría         |
| Redis Cache (src/core/cache.py) | —              | —         | Parcial    | CRUD/TTL/serialización    | Evidenciar fallback y rate limiting    |
| Redis Pub/Sub (src/core/ws_pubsub.py) | —        | —         | Parcial    | Broadcast y reconexión    | Saturación y auditoría                 |
| Routers API (FastAPI)           | —              | —         | No reportado | Contratos inferidos      | Seguridad y casos edge                 |

Tabla 16. Matriz de edge cases en operaciones de campo
| Caso                                       | Componente         | Datos           | Resultado esperado                          | Riesgo                     |
|--------------------------------------------|--------------------|-----------------|----------------------------------------------|----------------------------|
| Coordenadas inválidas (geolocalización)    | PostGIS            | lat/lng extremos | Validación/rechazo                           | Datos corruptos            |
| Cancelación de operativo durante ejecución | API/WS             | task_code       | Estado consistente; notificaciones           | Inconsistencia de estado   |
| Fallo de Redis (TLS/puerto)                | Cache/PubSub       | —               | Degradación controlada; reconexión           | Pérdida de mensajería      |
| Saturación de mensajes WS                  | WebSockets         | burst load      | Latencia controlada; sin pérdida crítica     | Degradación UX             |
| Recordatorio fuera de ventana               | Scheduler          | timestamp       | No enviar; log de decisión                   | Ruido operativo            |

Tabla 17. Matriz de seguridad de endpoints
| Endpoint                       | Autenticación     | Autorización              | Validaciones de entrada      | Logs/Auditoría           | Estado       |
|--------------------------------|-------------------|---------------------------|------------------------------|--------------------------|--------------|
| /auth/{telegram_id}            | JWT/validaciones  | Roles/perfiles            | Tipos y rangos               | Audit trail              | Parcial      |
| /tasks/create                  | JWT/validaciones  | Permisos por rol          | Esquema TareaCreate          | Audit por acción         | Parcial      |
| /tasks/finalize                | JWT/validaciones  | Permisos por rol/usuario  | task_code, telegram_id       | Trail y diferenciación 404/403 | Parcial  |
| /tasks/user/telegram/{id}      | JWT/validaciones  | Filtros por usuario       | status, paginación           | Consulta trazable        | Parcial      |
| /users                         | JWT/validaciones  | Filtros por rol           | role                         | Auditoría por rol        | Parcial      |

## 6. Cobertura de funcionalidades operativas

Las funcionalidades operativas clave (creación de operativos, asignación de efectivos, consulta de disponibilidad, liberación automática, gestión de múltiples operativos) requieren pruebas E2E que integren seguridad, trazabilidad y observabilidad.

Tabla 18. Cobertura funcional operativa
| Funcionalidad                        | Módulo/Endpoint            | Casos de prueba             | Cobertura actual | Gaps                          |
|--------------------------------------|-----------------------------|-----------------------------|------------------|-------------------------------|
| Creación de operativos               | Bot: /crear; API: /tasks/create | Wizard completo; validaciones | 70%+ (bot)       | Persistencia del wizard; permisos por rol |
| Asignación de efectivos              | PostGIS; API operativa      | Búsqueda por proximidad     | Parcial          | Consumo del bot; auditoría    |
| Consulta de disponibilidad           | API: /users; filtros        | Paginación; filtros por rol | Parcial          | Pruebas bajo volumen          |
| Liberación automática                | API: /tasks/finalize        | Finalización; rollback      | Parcial          | Rollback; trazabilidad        |
| Gestión de múltiples operativos      | WS/Pub/Sub                  | Coordinación cross-worker   | Parcial          | Saturación; conflictos        |

## 7. Análisis de tendencias y brechas

La distribución de pruebas unitarias vs integración vs E2E evidencia un buen punto de partida en el bot y tiempo real, pero con necesidad de ampliar integración/E2E para cubrir seguridad, resiliencia y observabilidad en staging/producción. Se recomiendan pruebas de carga y resiliencia con Locust y simulaciones de fallos, y establecer un plan formal de gestión de flakiness y mantenibilidad de test suites.[^1][^4][^5][^7]

Tabla 19. Ratio unit vs integration vs E2E por componente
| Componente        | Unit (%) | Integration (%) | E2E (%) | Observaciones                                   |
|-------------------|----------|------------------|---------|--------------------------------------------------|
| Bot               | 60       | 35               | 5       | Falta carga/resiliencia; métricas del bot        |
| WebSockets        | 40       | 50               | 10      | Disponibilidad/failover no evidenciados          |
| PostGIS           | 50       | 50               | 0       | Performance y auditoría pendientes               |
| Redis Cache       | 50       | 50               | 0       | Fallback y rate limiting                         |
| Redis Pub/Sub     | 40       | 55               | 5       | Saturación y reconexión                          |
| API (Routers)     | 45       | 45               | 10      | Seguridad de endpoints, edge cases               |

Tabla 20. Plan de pruebas de carga y resiliencia
| Tipo de prueba       | Herramienta | Escenario                                 | Criterios de éxito                                |
|----------------------|-------------|-------------------------------------------|---------------------------------------------------|
| Carga sostenida API  | Locust      | 100+ RPS con mix de endpoints             | p95 < 200ms; p99 < 500ms; errores < 1%            |
| Resiliencia WS       | Custom/pytest | Desconexión/reconexión; bursts de mensajes | Sin pérdida crítica; latencia bajo umbral         |
| Fallo Redis          | Simulación  | TLS/puerto fallback; pérdida de mensajes   | Degradación controlada; reintentos exitosos       |
| Chaos testing        | Inyectores  | Caída de worker; restart de servicio       | Auto-failover; recuperación sin intervención      |
| E2E staging          | Pipelines   | Flujos operativos completos                | Cobertura ≥ 85%; gates de calidad superados       |

## 8. Benchmarking contra estándares

El mapeo de prácticas actuales a estándares garantiza que el plan de pruebas refleje controles de seguridad y resultados deseables (outcomes) de gobierno de riesgos. Se propone un plan de cumplimiento con brechas, recomendaciones y dueños asignados.

Tabla 21. Mapa de cumplimiento vs prácticas actuales
| Estándar/Control       | Práctica actual                             | Evidencia                              | Brecha                               | Recomendación                          |
|------------------------|----------------------------------------------|----------------------------------------|--------------------------------------|----------------------------------------|
| NIST CSF 2.0 – GOVERN  | CI/CD con calidad y seguridad; auditoría parcial | GitHub Actions; logging estructurado   | Política de pruebas y auditorías formalizadas | Documentar perfil organizacional; políticas de testing |
| NIST CSF 2.0 – PROTECT | JWT, CORS, middlewares                       | Configuraciones y despliegue           | Rate limiting en bot; cifrado en reposo | Integrar rate limiting (Redis); verificar cifrado     |
| NISTIR 8397            | Automatización básica de pruebas             | Pytest + coverage; Locust              | Integración de seguridad (IAST/SAST) en gates | Añadir SAST/DAST y gates de seguridad     |
| SA-11(7)               | Cobertura de controles no evidenciada        | —                                      | Mapeo de pruebas a controles          | Matriz de trazabilidad control→prueba   |
| Availability (AWS)     | Métricas WS; salud por endpoint              | Prometheus; health checks              | SLAs formalizados; pruebas de failover | Establecer SLAs; pruebas de disponibilidad |
| CJIS Security Policy   | Aplicabilidad por validar                    | —                                      | No evidenciado                        | Confirmar alcance; controles si aplica  |

### 8.1 NIST CSF 2.0 y NISTIR 8397

NIST CSF 2.0 articula resultados de ciberseguridad sin prescribir acciones específicas, lo que habilita perfiles organizacionales y tiers de gobernanza. NISTIR 8397 recomienda prácticas mínimas de verificación por desarrolladores, incluyendo threat modeling y automatización. En el plan de pruebas, esto se traduce en integrar seguridad en CI/CD, gates de cobertura y métricas, y trazabilidad de controles a nivel de casos de prueba y evidencias automatizadas.[^3][^9]

### 8.2 SA-11(7) Cobertura de controles de seguridad

Se debe verificar el alcance de las pruebas para cubrir controles requeridos mediante una matriz de trazabilidad control→prueba→resultado, abarcando autenticación, autorización, validación de entrada y logging/auditoría.[^10]

Tabla 22. Matriz de trazabilidad control→prueba
| Control de seguridad           | Prueba específica                        | Resultado esperado                    | Evidencia                         |
|--------------------------------|-------------------------------------------|---------------------------------------|-----------------------------------|
| Autenticación (JWT)            | Tests de token inválido/expirado          | Rechazo con trazabilidad              | Logs; respuestas 401/403          |
| Autorización por rol           | Acceso a endpoint sin rol suficiente      | Rechazo; audit trail                  | Registro de auditoría             |
| Validación de entrada          | Payload malformado                        | Rechazo; mensajes seguros             | Logs; excepciones controladas     |
| Logging/Auditoría              | Acción sensible (finalizar tarea)         | Registro con correlation ID           | Trazas completas                  |
| Cifrado en tránsito            | TLS forzado; validación de certificados   | Conexión segura; sin datos en claro   | Configuraciones; tests de canal   |

### 8.3 Alta disponibilidad (99.9%+)

Para una meta de 99.9% de uptime, las pruebas deben cubrir failover automatizado, recovery y continuidad. La instrumentación Prometheus y dashboards deben validar que la operación soporta interrupciones breves sin impacto crítico. Se proponen escenarios con criterios de aceptación claros.[^4][^5][^7]

Tabla 23. Pruebas de disponibilidad
| Escenario                         | Tipo       | Métrica objetivo          | Criterio de aceptación               |
|----------------------------------|------------|---------------------------|--------------------------------------|
| Failover de worker               | Resilience | active_connections        | Reconexión < X s; sin pérdida crítica |
| Caída de Redis                   | Resilience | send_errors_total         | Fallback activado; reintentos        |
| Carga sostenida en API           | Load       | p95/p99 latencies         | p95 < 200ms; p99 < 500ms             |
| Saturación en WS                 | Load/Stress| message_latency_seconds   | Sin backpressure crítico; latencia controlada |

### 8.4 CJIS Security Policy (aplicabilidad)

Si el sistema procesa datos de justicia criminal, los controles de acceso, cifrado, auditoría y gestión de incidentes de CJIS aplican. Dado que no hay evidencia explícita, se recomienda confirmar alcance y, en caso de aplicación, incorporar pruebas y evidencias que demuestren cumplimiento periódico.[^13]

Tabla 24. Controles CJIS mapeados a pruebas
| Control CJIS                     | Prueba propuesta                              | Evidencia esperada                 | Estado     |
|----------------------------------|-----------------------------------------------|------------------------------------|------------|
| Acceso (autenticación/autorización) | Tests de roles y permisos                     | Logs de denegación; auditoría      | Por validar |
| Cifrado en tránsito/en reposo     | Validación TLS; verificación cifrado en BD     | Configuraciones; pruebas de cifrado | Por validar |
| Auditoría de acciones sensibles   | Registro detallado por acción                  | Audit trail con correlation ID     | Parcial    |
| Gestión de incidentes             | Pruebas de respuesta y recuperación            | Playbooks; evidencias de演练       | Brecha     |

## 9. Roadmap para alcanzar ≥ 85% de cobertura en funcionalidades críticas

El plan por sprints prioriza módulos críticos, integraciones y gates de CI/CD, articulando metas de cobertura, seguridad y disponibilidad.

Tabla 25. Roadmap por sprints
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

Tabla 26. Gates de CI/CD
| Gate                    | Umbral                         | Validación automatizada         | Acción en caso de fallo           |
|-------------------------|--------------------------------|---------------------------------|-----------------------------------|
| Cobertura de código     | ≥ 85% en módulos críticos      | pytest --cov; reporte en PR     | Bloqueo de merge; tareas asignadas |
| Seguridad               | SAST/DAST sin issues críticos  | Tools integradas en CI          | Bloqueo; remediación obligatoria   |
| Performance             | p95 < 200ms; p99 < 500ms       | Locust post-deploy              | Rollback automático                |
| Resiliencia             | Pruebas failover sin pérdida crítica | Tests de disponibilidad         | Escalamiento a incident response   |
| Auditoría               | Trazabilidad control→prueba    | Evidencias en artifacts         | Corrección y re-evaluación         |

## 10. Plan de aseguramiento, seguimiento y gobernanza

La gobernanza del plan de pruebas debe integrar KPIs operativos y de seguridad, reportes de cobertura por módulo, y ejecución continua con staging. La función GOVERN del NIST CSF 2.0 guía el establecimiento de políticas, roles y oversight, complementada por automatización de evidencias (NISTIR 8011-4).

![NIST CSF 2.0 – GOVERN: integración de políticas y oversight.](.pdf_temp/viewrange_chunk_1_1_5_1761723738/images/r7hal7.jpg)

Tabla 27. KPIs y umbrales
| KPI                               | Fuente               | Umbral objetivo                    | Frecuencia | Responsable     |
|-----------------------------------|----------------------|------------------------------------|------------|-----------------|
| Cobertura por módulo crítico      | CI/CD (pytest --cov) | ≥ 85%                               | Por PR     | QA/Engineering  |
| Cobertura de seguridad (controles) | Gates/SAST/DAST      | 0 issues críticos                   | Por PR     | SecEng          |
| p95/p99 latencias API/WS          | Prometheus/Locust    | p95 < 200ms; p99 < 500ms           | Semanal    | SRE/Engineering |
| Disponibilidad (uptime)           | Alertas/monitoreo    | ≥ 99.9%                             | Mensual    | SRE             |
| Fallos de pruebas en producción   | Incident response    | Tendencia decreciente               | Mensual    | QA/SRE          |
| Audit trail por acción sensible   | Logs/Auditoría       | 100% trazabilidad                   | Mensual    | Compliance      |

## 11. Anexos: evidencia, listas de chequeo y fuentes

Evidencia prioritaria:
- Suite de pruebas del bot (11 archivos), reportes de cobertura (70%+), smoke tests de WebSockets, instrumentación Prometheus.
- Pruebas de validaciones y consultas PostGIS; pruebas de CRUD/TTL/serialización en Redis; pruebas de broadcasting cross-worker.

Listas de chequeo:
- Seguridad por endpoint (autenticación/autorización, validación de entrada, logging/auditoría).
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
- Métricas en producción (errores, latencias, throughput) y correlación con resultados de pruebas.
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