# Compliance para Sistemas Operativos/Tácticos (HIPAA adaptado) en GRUPO_GAD

## 1. Propósito, alcance y contexto operativo

El propósito de este informe es evaluar el cumplimiento específico de los sistemas operativos y tácticos de GRUPO_GAD bajo un marco de control adaptado de la Health Insurance Portability and Accountability Act (HIPAA), complementado con el NIST Cybersecurity Framework 2.0 (CSF 2.0), el NIST Risk Management Framework (RMF), ISO/IEC 27001:2022 y, cuando aplique, lineamientos FedRAMP para servicios en la nube utilizados por el sector público. La evaluación está centrada en dominios de alto impacto: gestión de efectivos, operaciones de campo críticas, sistemas de notificación automática (incluyendo WebSockets y bots) y el manejo de datos operativos sensibles, con especial atención a su trazabilidad y resiliencia 24/7.

El alcance abarca el backend (FastAPI, PostgreSQL con PostGIS, Redis para cache/PubSub), los canales de comunicación de campo, la exposición de APIs y WebSockets, el bot de Telegram como interfaz operativa, y el plano de observabilidad (Prometheus/Grafana). La evaluación se realiza con base en evidencias técnicas del repositorio y la aplicación en producción[^1][^2], y los hallazgos se enmarcan en funciones y categorías del NIST CSF 2.0 (Govern, Identify, Protect, Detect, Respond, Recover)[^3], en los siete pasos del RMF[^5] y en la estructura de salvaguardas de HIPAA (administrativas, físicas y técnicas)[^6][^7]. La guía de APIs del DoD (CTO) se utiliza para sustentar exigencias técnicas de autenticación/autorización, segmentación y protección de datos en integraciones y flujos de misión[^13].

Este documento reconoce brechas de información que deben atenderse para consolidar una posición de cumplimiento robusta: confirmación del estado de PostGIS en producción, evidencia de cifrado en reposo y en uso (data-in-use), especificación de SLAs 24/7, política de retención de logs y auditoría a nivel de base de datos, clasificación de datos y uso de DLP/anonimización, detalle de controles de acceso por rol en el flujo operativo, inventario de integraciones con acuerdos de cumplimiento, y pruebas de DR (RTO/RPO) en escenarios críticos. Estas brechas son explicitadas en la sección de conclusiones y en el roadmap de cierre.

## 2. Metodología de evaluación y criterios de aceptación

La metodología aplicada integra revisión estática del código y configuración, análisis funcional de flujos críticos (API, WebSockets, bot), verificación de capacidades operativas (lifespan, health checks, métricas) y contrastación con marcos de referencia. El criterio de aceptación se fundamenta en tres pilares: efectividad operativa demostrada, alineación con controles y evidencia auditable. La evaluación privilegia:

- La adecuación del análisis y gestión de riesgos (HIPAA Security Rule), traducidos en controles mitigadores concretos.
- La trazabilidad end-to-end de operaciones críticas (creación, asignación, despliegue, finalización de tareas, y notificación).
- La robustez de autenticación/autorización y la seguridad de transmisión y almacenamiento de datos operativos.
- La disponibilidad y resiliencia del sistema ante fallos y en escenarios de estrés operacional.

Se aplican mapeos de NIST CSF 2.0 para ubicar las funciones y categorías relevantes por dominio operativo[^3][^4], y se utiliza el RMF como proceso para preparar, categorizar, seleccionar, implementar, evaluar, autorizar y monitorear los controles, incluyendo la actualización al release 5.2.0 de los controles NIST SP 800-53[^5]. En materia de autenticación resistente al phishing y prácticas de Zero Trust, se consideran las señales recientes de la normativa de defensa (NDAA FY25) para orientar requisitos en entornos de alta criticidad[^15].

Para ilustrar el enfoque, el siguiente mapa sintetiza la correspondencia entre dominios operativos y funciones NIST CSF 2.0:

Tabla 1. Mapa de dominios operativos vs funciones NIST CSF 2.0

| Dominio operativo                           | Govern (Gobernar) | Identify (Identificar) | Protect (Proteger) | Detect (Detectar) | Respond (Responder) | Recover (Recuperar) |
|---------------------------------------------|-------------------|------------------------|--------------------|-------------------|---------------------|---------------------|
| Gestión de efectivos                        | Políticas, roles, responsabilidades; inventario de activos y datos; alineación regulatoria | Clasificación de datos y perfiles de riesgo por rol | Cifrado, control de acceso, segmentación | Monitoreo de accesos y anomalías | Respuesta a incidentes y revocación | Restauración de servicios y datos operativos |
| Operaciones de campo críticas               | SOPs, separación de ambientes, contingencias | Identificación de procesos críticos y dependencias | Autenticación/autorización, integridad y protección de canales | Alertas, correlación de eventos | Ejecutar playbooks, escalamiento | Ensayos DR, restauración selectiva |
| Sistemas de notificación automática (WS/Bot)| Políticas de publicación, verificación de identidad y consentimiento | Inventario de canales y tipos de mensajes | Seguridad de transmisión, mínimos privilegios en publicación | Fallos de envío, degradaciones y backpressure | Fallback y degradación controlada | Reprocesamiento, reintentos y recuperación |

El valor de este mapa reside en que permite vincular cada función y categoría del marco con obligaciones operativas concretas y con evidencias esperadas en auditoría. Así, Govern y Identify soportan la definición de la postura de seguridad y la gestión de riesgos; Protect, Detect y Respond articulan controles técnicos y operativos para prevenir, descubrir y reaccionar ante eventos; Recover cierra el ciclo con la continuidad y restauración efectiva.

## 3. Marco normativo aplicable y adaptación para entornos operativos/tácticos

La Regla de Seguridad de HIPAA establece estándares nacionales para proteger la ePHI, con flexibilidad y neutralidad tecnológica, pero con exigencias claras: asegurar confidencialidad, integridad y disponibilidad; proteger contra amenazas y usos indebidos; y asegurar el cumplimiento de la fuerza laboral[^6]. La propuesta de actualización de 2025 refuerza el carácter obligatorio de controles y medidas de ciberseguridad, alineando expectativas con prácticas modernas de defensa[^7]. En entornos gubernamentales y de operaciones tácticas, estas salvaguardas se adaptan de salud a datos operativos sensibles, preservando principios equivalentes de mínimo necesario, necesidad de saber, trazabilidad y resiliencia.

NIST CSF 2.0 y el RMF proveen el armazón para gobernanza y gestión de riesgo: perfilado, categorización, selección de controles, implementación y evaluación continua, y autorización de operación basada en riesgo[^3][^5]. ISO/IEC 27001:2022 aporta la estructura de Sistema de Gestión de Seguridad de la Información (SGSI), con cláusulas 4–10 (contexto, liderazgo, planificación, soporte, operación, evaluación y mejora) y controles Anexo A (organizativos, personal, físicos y tecnológicos), que incluyen logging, monitoreo, criptografía, continuidad y cadena de suministro[^14]. Cuando GRUPO_GAD utilice servicios cloud sujetos a exigencias federales, FedRAMP constituye el marco de autorización a considerar (categorización de impacto, controles y nivel de baseline), reforzado por guías de APIs del DoD que exigen autenticación robusta, autorización granular, segmentación y protección de datos en integraciones críticas[^12][^13].

Para operacionalizar esta adaptación, se propone el siguiente mapeo de salvaguardas HIPAA a controles aplicables en entornos no sanitarios:

Tabla 2. Adaptación HIPAA → controles aplicables (NIST CSF/RMF/ISO 27001)

| Salvaguarda HIPAA (esencia)                                   | Equivalente en NIST CSF/RMF/ISO 27001                               | Implementación propuesta en GRUPO_GAD                                  |
|---------------------------------------------------------------|---------------------------------------------------------------------|-------------------------------------------------------------------------|
| Análisis y gestión de riesgos                                 | CSF: Identify/Govern; RMF: Preparar/Categorizar/Seleccionar         | Registro de riesgos por dominio operativo y por integración             |
| Controles de auditoría y trazabilidad                         | CSF: Detect; ISO A.8.15 logging; SP 800-53 AU-*                     | Audit trail end-to-end en aplicación y DB; correlación en SIEM          |
| Autenticación y autorización                                  | CSF: Protect; ISO A.8.5; SP 800-53 AC-*; NDAA FY25 (phishing-resistant) | MFA resistente al phishing; RBAC/ABAC; JWT con rotación y caducidad     |
| Seguridad de transmisión                                      | CSF: Protect; ISO A.8.21/8.24; SP 800-53 SC-*                       | TLS en todos los canales; WS seguro; evitar fallbacks inseguros en Redis |
| Integridad de datos                                           | CSF: Protect/Detect; ISO A.8.3/8.11                                 | Hashing y verificación; controles de no alteración; DLP y enmascaramiento |
| Disponibilidad y contingencia                                 | CSF: Recover; ISO A.8.13/8.14; SP 800-53 CP-*                       | Backups verificados; DR con RTO/RPO; health checks y readiness          |
| Políticas, procedimientos y documentación                     | CSF: Govern; ISO cláusulas 4–10; SP 800-53 PM-*                     | Políticas por dominio y evidencia de cumplimiento (6 años)              |

Este mapeo permite alinear un marco sanitario con exigencias técnicas y operativas de sistemas tácticos, manteniendo el espíritu de HIPAA (confidencialidad, integridad y disponibilidad) sin requerir ePHI, sino aplicándolo a datos operativos de efectivos, tareas, geolocalización y notificaciones.

## 4. Evaluación por dominio operativo

El análisis por dominio integra arquitectura, flujos de datos, seguridad y disponibilidad, contrastando con el marco normativo y con evidencias del repositorio y producción[^1][^2]. A continuación se presentan los hallazgos y exigencias de cumplimiento para cada dominio.

### 4.1 Gestión de efectivos

La gestión de efectivos se apoya en entidades Usuario y Efectivo, con relaciones a Tarea. La autenticación vía Telegram y emisión/verificación de JWT permiten el control de acceso y la trazabilidad de acciones. En este dominio, el principio de mínimo necesario implica separar vistas y operaciones por rol (ciudadano, operador, supervisor, administrador), de modo que la visualización de datos personales (por ejemplo, DNI, estado de disponibilidad, ubicación) se limite a lo estrictamente requerido para ejecutar la tarea.

La clasificación de datos debe distinguir: identificadores personales (DNI, telegram_id), datos operativos (estado, asignación, ubicación), metadatos de tarea (códigos, tiempos, estados) y registros de auditoría (quién, qué, cuándo, dónde). En reposo, deben cifrarse los identificadores personales y la información sensible de operativos; en tránsito, todos los canales; y en uso, se recomienda evaluar mecanismos de protección (por ejemplo, enclaves o crypto absolutes para campos críticos), aun cuando las evidencias actuales no confirman su implementación.

El acceso debe estar gobernado por una matriz RBAC/ABAC que considere atributos de rol, contexto operativo y sensibilidad del dato. Se propone:

Tabla 3. Matriz de clasificación de datos vs controles

| Clasificación de dato           | Ejemplos                                    | Acceso mínimo necesario                        | Controles aplicables                                      |
|---------------------------------|---------------------------------------------|-----------------------------------------------|-----------------------------------------------------------|
| Personal identificable (PII)    | DNI, telegram_id                            | Supervisor/Administrativo según necesidad      | Cifrado en reposo y tránsito; MFA; auditoría de accesos    |
| Operativo sensible              | Estado, asignación, ubicación               | Operador/Supervisor en misión                  | TLS; RBAC; DLP; integridad; logging de accesos/modificaciones |
| Metadatos operativos            | Códigos de tarea, tiempos, estados          | Operador, automatizaciones                     | Rate limiting; validación de entrada; protección contra tampering |
| Audit trail                     | Eventos de acceso y cambios                 | Auditoría y Cumplimiento                       | Retención (≥6 años); correlación; no repudio              |

La evidencia de autenticación y manejo de sesiones mediante JWT está presente en el repositorio y producción[^1][^2]. No obstante, la confirmación de cifrado en reposo y en uso, así como una política formal de clasificación, constituyen brechas que deben cerrarse para consolidar cumplimiento.

### 4.2 Operaciones de campo críticas

Las operaciones de campo abarcan la creación, asignación, despliegue y finalización de tareas, incluidas las comunicaciones en tiempo real por WebSockets. La trazabilidad exige un audit trail end-to-end con correlación por IDs y timestamps sincronizados, abarcando desde el evento de creación hasta la notificación de finalización.

Para ilustrar el control, la siguiente tabla mapea eventos críticos y campos de auditoría esperados:

Tabla 4. Eventos críticos de campo → campos de auditoría

| Evento crítico                    | Actor (usuario/efectivo/rol) | ID correlación (request/evento) | Ubicación (si aplica) | Hora (UTC) | Estado antes/después | Método canal | Resultado | Comentarios |
|----------------------------------|-------------------------------|----------------------------------|-----------------------|------------|----------------------|--------------|-----------|-------------|
| Creación de tarea                | Operador/Supervisor           | request_id, task_id              | —                     | timestamp  | —/Creada             | API/WS       | Éxito/Fallo| Evidencia  |
| Asignación a efectivo            | Supervisor                    | task_id, assignment_id           | geocoordenadas        | timestamp  | Sin asignar/Asignado | API/WS       | Éxito/Fallo| Evidencia  |
| Inicio de despliegue             | Efectivo                      | task_id, user_id                 | ubicación de inicio   | timestamp  | Asignada/En curso    | WS           | Éxito/Fallo| Evidencia  |
| Finalización de tarea            | Efectivo/Operador             | task_id                          | ubicación de fin      | timestamp  | En curso/Finalizada  | WS/API       | Éxito/Fallo| Evidencia  |
| Notificación de finalización     | Sistema                       | task_id, notification_id         | —                     | timestamp  | —/Notificada         | WS/Bot       | Éxito/Fallo| Evidencia  |

La seguridad de transmisión debe ser consistente (TLS) en todos los canales y el sistema debe ejecutar monitoreo activo para detectar anomalías (intentos de acceso no autorizado, errores repetidos, degradaciones). El logging estructurado debe permitir correlacionar eventos con mínima fricción y con retención adecuada.

### 4.3 Sistemas de notificación automática

Las notificaciones por WebSockets y Telegram Bot permiten coordinación operativa en tiempo real. El sistema instrumenta métricas de WebSockets (conexiones activas, mensajes, broadcasts, errores, heartbeats, latencias) y publica eventos de estado, asignaciones y finalización[^1][^2]. Debe garantizarse autenticación del cliente al conectarse, autorización para suscripción por tópicos o canales y seguridad de transmisión. Los mecanismos de degradación controlada (fallback local cuando Redis Pub/Sub no está disponible) son convenientes para resiliencia, pero deben operar sin reducir la seguridad del canal ni la integridad del mensaje.

La política de publicación/suscripción debe contemplar permisos por canal, rate limiting en eventos y backpressure en picos. Se propone:

Tabla 5. Catálogo de eventos de notificación → campos de auditoría

| Tipo de evento            | Channel/Topic             | Suscriptor (rol)       | Permisos (pub/sub)      | Garantías de entrega      | Retención        |
|---------------------------|---------------------------|------------------------|-------------------------|---------------------------|------------------|
| Asignación de tarea       | ws_tareas_asignacion      | Operador/Supervisor    | pub: sistema; sub: roles| Reintento y confirmación  | 1–3 años (operativo) |
| Cambio de estado          | ws_tareas_estado          | Efectivo/Operador      | pub: sistema; sub: roles| At-least-once con idempotencia | 1–3 años (operativo) |
| Finalización              | ws_tareas_finalizacion    | Operador/Supervisor    | pub: sistema; sub: roles| Exactly-once o idempotente | 1–3 años (operativo) |
| Mensajes de bot           | bot_telegram              | Ciudadano/Operador     | pub: bot; sub: usuario  | Confirmación bot          | 1–3 años (operativo) |

La integración con el bot de Telegram debe respetar verificación de identidad y minimizar la exposición de datos sensibles en mensajes, privilegiando referencias y enlaces internos autenticados.

### 4.4 Manejo de datos operativos

Los tipos de datos incluyen PII de efectivos, datos operativos de tareas y geolocalización. Las salvaguardas técnicas deben abarcar cifrado en tránsito y en reposo, control de acceso y auditoría. ISO A.8.24 (uso de criptografía), A.8.3 (restricción de acceso a la información), A.8.11 (enmascaramiento de datos) y A.8.15 (registro/logging) son controles de referencia directa[^14]. HIPAA exige mecanismos de control de acceso, controles de auditoría, integridad y seguridad de transmisión[^6].

Tabla 6. Matriz de datos operativos → salvaguardas

| Tipo de dato                | Cifrado en tránsito | Cifrado en reposo | DLP/Enmascaramiento | Auditoría | Retención | Observaciones                  |
|----------------------------|---------------------|-------------------|---------------------|-----------|-----------|-------------------------------|
| PII (DNI, telegram_id)     | TLS obligatorio     | Confirmar/Implementar | Enmascarar en vistas | Accesos/cambios | ≥6 años   | Política formal de clasificación |
| Geolocalización (geom)     | TLS obligatorio     | Confirmar/Implementar | Agregación por zonas | Accesos y consultas | 1–3 años | Minimizar exposición             |
| Estado/Asignación          | TLS obligatorio     | Confirmar/Implementar | DLP en logs         | Modificaciones     | 1–3 años | Idempotencia en flujos           |
| Metadatos de tareas        | TLS obligatorio     | Confirmar/Implementar | —                   | Lecturas/escrituras | 1–3 años | —                               |

La evidencia actual no confirma cifrado en reposo ni protección de data-in-use; por tanto, cerrar estas brechas es crítico para cumplir con expectativas de HIPAA, ISO y NIST.

## 5. Protección de datos operativos (PII y operativos sensibles)

Los principios de mínimo necesario y necesidad de saber deben articular el acceso por rol y por tarea. La minimización reduce la exposición, y la separación por sensibilidad evita que un rol accede a más de lo imprescindible para su función. El cifrado debe abarcar tránsito (TLS en API/WS/Redis), reposo (cifrado de base de datos/archivos, gestión de llaves) y uso (protección de memoria y enclaves para operaciones críticas), aun cuando el marco HIPAA histórico no lo expresaba como “requerido” sino como “direccionable”, las actualizaciones de 2025 apuntalan su exigencia práctica[^7][^11]. La gestión de llaves requiere rotación periódica y control de acceso (mínimo privilegio), con separación de funciones entre quienes administran llaves y quienes operan la plataforma.

En anonimización y pseudonimización, se debe adoptar enmascaramiento en vistas no operativas, tokenización para integraciones, y agregación por zonas o radios en analítica. ISO A.8.11 exige medidas de enmascaramiento y prevención de fugas de datos, que deben incorporarse en diseños de interfaz, reportes y extracciones[^14].

Tabla 7. Inventario de datos sensibles → requisitos de cifrado y privacidad

| Dataset                       | Sensibilidad | Cifrado tránsito | Cifrado reposo | Uso (protección) | Acceso | Retención | Controles complementarios |
|------------------------------|-------------|------------------|----------------|------------------|--------|-----------|---------------------------|
| PII de efectivos             | Alta        | TLS              | Implementar/Confirmar | Evaluar enclaves  | RBAC/ABAC | ≥6 años  | DLP; auditoría avanzada    |
| Geolocalización (efectivos)  | Media–Alta  | TLS              | Implementar/Confirmar | Agregación        | Rol/Tarea | 1–3 años | Minimización por diseño     |
| Tareas y asignaciones        | Media       | TLS              | Implementar/Confirmar | —                | Rol/Tarea | 1–3 años | Integridad y no repudio     |
| Notificaciones (eventos)     | Media       | TLS              | Implementar/Confirmar | —                | Rol       | 1–3 años | Idempotencia; rate limiting |

## 6. Audit trails operativos

Las operaciones críticas de campo requieren auditoría técnica alineada con HIPAA (controles de auditoría), ISO A.8.15 (logging) y exigencias de evidencia del gobierno federal (por ejemplo, requisitos de auditoría de confiabilidad de datos, que demandan correspondencias de especificación en tablas/campos)[^6][^14][^16]. La trazabilidad de asignaciones y comandos de finalización debe registrar quién, qué, cuándo, dónde y desde qué canal, con correlación consistente de IDs y timestamp sincronizado (por ejemplo, NTP). La retención mínima para documentación de políticas y procedimientos es de seis años; para logs operativos, se recomienda 1–3 años según sensibilidad y necesidad operacional, con almacenamiento que garantice integridad y no repudio (WORM, cuando aplique).

Tabla 8. Catálogo de eventos operativos → campos mínimos de auditoría y retención

| Evento                         | Campos mínimos                                                                 | Retención sugerida | Observaciones                                       |
|--------------------------------|---------------------------------------------------------------------------------|--------------------|-----------------------------------------------------|
| Creación de tarea              | actor, rol, request_id, task_id, timestamp, canal, resultado                    | 1–3 años           | Correlación con métricas y health checks             |
| Asignación de efectivo         | actor, rol, task_id, assignment_id, geolocalización, timestamp, canal, resultado| 1–3 años           | Validación de ubicación para trazabilidad            |
| Inicio/fin de despliegue       | actor, task_id, geolocalización inicio/fin, timestamp, resultado                | 1–3 años           | Integridad de eventos de campo                       |
| Finalización de tarea          | actor, task_id, timestamp, canal, evidencia adjunta (hash)                      | 1–3 años           | Idempotencia; evitar duplicidades                    |
| Notificación automática        | event_id, topic, timestamp, receptor (rol), estado de entrega                   | 1–3 años           | Garantías de entrega y reintentos                    |

La consolidación de estos audit trails fortalece la capacidad de auditoría, facilita la investigación de incidentes y demuestra fiabilidad de datos, tal como demandan guías de auditoría gubernamentales[^16].

## 7. Seguridad operativa (comunicaciones, autenticación, autorización, monitoreo)

Las comunicaciones deben operar exclusivamente sobre TLS; se deben retirar fallbacks inseguros (por ejemplo, configuraciones tipo ssl_cert_reqs=None en Redis), documentar excepciones con fecha de caducidad y evitar su persistencia en producción. La autenticación multifactor (MFA) y la resistencia al phishing son exigencias crecientes; la orientación del NDAA 2025 subraya priorizar autenticación resistente al phishing, especialmente en sistemas de misión[^15]. La autorización granular debe combinar Control de Acceso Basado en Roles (RBAC) y Atributos (ABAC), con segregación de funciones y separación de ambientes.

El monitoreo continuo incluye inventario de activos, vulnerabilidades, configuraciones y verificación de políticas. ISO A.8.16 (actividades de monitoreo) y A.8.8 (gestión de vulnerabilidades técnicas) son referencias clave[^14]. La guía de APIs del DoD refuerza requisitos de autenticación/autorización y segmentación en integraciones y flujos entre sistemas[^13].

Tabla 9. Mapa de autenticación/autorización → flujos y controles

| Flujo                        | Control de autenticación          | Control de autorización              | Controles complementarios                      | Evidencia auditable                      |
|-----------------------------|-----------------------------------|--------------------------------------|-----------------------------------------------|------------------------------------------|
| Login emisión/verificación  | JWT + MFA resistente al phishing  | RBAC por rol                         | Rate limiting; headers de seguridad; CORS      | Logs de autenticación y decisiones de acceso |
| Conexión WebSocket          | Token en handshake + MFA          | Suscripción por tópico/rol           | Heartbeat; validación de topics; TLS           | Métricas WS; logs de suscripción          |
| Bot Telegram                | Token del bot + verificación ID   | Comandos por rol                     | Validación de entrada; protección de mensajes  | Logs por comando y respuesta              |
| API de tareas               | JWT + MFA                         | RBAC/ABAC por tarea y operación      | Límite de tamaño; DLP; integridad              | Trazas por endpoint y cambios de estado   |

## 8. Disponibilidad y resiliencia (SLA 24/7, recuperación, DR, continuidad)

Las exigencias de operación 24/7 requieren establecer SLAs formales (disponibilidad, latencia, MTTR) y procedimientos de failover y conmutación (fly.io y alternativas). Los backups deben ser periódicos, verificados, con restauraciones probadas y documentadas; la continuidad operacional se apoya en pruebas de DR que definan RTO/RPO por dominio crítico[^5]. La degradación controlada (por ejemplo, broadcast local cuando Redis Pub/Sub no está disponible) es útil, pero debe estar acotada y ser transparente.

La guía interagencial de movilización de recursos (2025) orienta estándares de coordinación y disponibilidad para respuesta operacional en contextos críticos, proporcionando criterios de preparación y mobilización que se reflejan en las expectativas técnicas del sistema[^18].

Tabla 10. Matriz de SLA/DR

| Servicio/Dependencia         | SLA (disponibilidad/latencia)        | RTO/RPO                   | Pruebas programadas        | Evidencias                 | Responsable         |
|------------------------------|--------------------------------------|---------------------------|----------------------------|---------------------------|---------------------|
| API FastAPI                  | 99.9% / p95 < 200 ms                 | RTO 15 min / RPO 5 min    | Trimestral (failover)      | Health checks; dashboards | SRE/Operaciones     |
| WebSockets                   | 99.9% / heartbeat < 30s              | RTO 15 min / RPO 5 min    | Mensual (degradación)      | Métricas WS; logs         | SRE/Dev             |
| Redis (Cache/PubSub)         | 99.9% / < 10 ms ops                  | RTO 15 min / RPO 5 min    | Trimestral                  | Logs; métricas exporter   | SRE/Infra           |
| PostgreSQL + PostGIS         | 99.9% / consultas críticas < 100 ms  | RTO 30 min / RPO 10 min   | Semestral (restauración)   | Backup; PITR              | DBA/SRE             |
| Bot Telegram                 | 99.9% / < 2 s respuesta              | RTO 30 min / RPO 10 min   | Trimestral                  | Logs bot; alertas         | Producto/Dev        |

Las evidencias actuales muestran instrumentación y health checks robustos, pero no establecen SLAs, RTO/RPO ni calendarios de pruebas DR; establecerlos es indispensable para auditoría y resiliencia.

## 9. Cumplimiento regulatorio y documentación

La alineación con HIPAA exige análisis y gestión de riesgos, políticas, procedimientos, capacitación y contratos con asociados (BAA, equivalentes) cuando corresponda[^6][^7]. En la esfera federal, el cumplimiento de NIST CSF/RMF (con SP 800-53 rev. 5.2.0) y, cuando aplique, FedRAMP, delimitan el perímetro de autorización y los controles requeridos para operar servicios cloud en contexto gubernamental[^3][^5][^12]. La documentación de políticas y procedimientos debe tener una retención mínima de seis años y estar disponible para auditores y responsables de implementación[^6].

Los derechos y prácticas de privacidad bajo la normativa estadounidense (por ejemplo, ICLG 2025) deben contemplarse en avisos y procedimientos de acceso/corrección, y en la gestión de incidentes y notificaciones, según corresponda[^17]. La matriz siguiente ilustra el mapeo entre obligaciones y evidencia:

Tabla 11. Matriz de cumplimiento: obligación → control/evidencia

| Obligación                               | Control/Política                         | Evidencia                           | Estado (actual)          | Dueño            |
|------------------------------------------|------------------------------------------|-------------------------------------|--------------------------|------------------|
| Análisis y gestión de riesgos            | Registro de riesgos por dominio          | Documentos, revisiones periódicas   | Brecha (formalización)   | CISO/Seguridad   |
| Políticas y procedimientos               | Políticas por área                       | Repositorio; control de versiones   | Parcial                  | Cumplimiento     |
| Capacitación y sanciones                 | Programa de formación y disciplina       | Registros de capacitación           | Brecha                   | RR.HH./Seguridad |
| Contratos/Acuerdos con terceros          | BAA/Contratos equivalentes               | Firmas; cláusulas de seguridad      | Brecha (inventario)      | Legal/Compras    |
| Documentación (≥6 años)                  | Control de información documentada       | Logs, políticas, procedimientos     | Parcial                  | Cumplimiento     |

El cierre de estas brechas es imprescindible para una auditoría formal y para sostener el cumplimiento continuo.

## 10. Gobernanza operativa

La gobernanza operativa articula políticas de manejo de datos, procedimientos de acceso y autorización, procesos de respuesta a incidentes y programas de formación y concienciación. ISO 27001 (cláusulas 4–10) establece el sistema de gestión (contexto, liderazgo, planificación, soporte, operación, evaluación y mejora), y Anexo A provee controles organizativos, de personal, físicos y tecnológicos que sustentan la disciplina operativa[^14]. HIPAA demanda asignar responsabilidad de seguridad, asegurar formación y aplicar sanciones por violaciones[^6].

Tabla 12. Roles y responsabilidades de gobernanza

| Rol                       | Responsabilidades clave                                          | Procesos principales                  | KPI/Indicadores                      |
|---------------------------|------------------------------------------------------------------|---------------------------------------|--------------------------------------|
| Oficial de Seguridad (CISO)| Políticas, gestión de riesgos, monitoreo                         | RMF, auditorías, mejora continua      | Riesgos mitigados; hallazgos cerrados |
| DPO/Privacidad            | Clasificación de datos, avisos, derechos                         | Evaluación de impacto; respuesta a derechos | Incidentes de privacidad             |
| Operaciones/SRE           | Disponibilidad, alertas, DR                                       | Health checks; failover; DR            | MTTR; disponibilidad                 |
| Desarrollo                | Controles técnicos, integración segura                            | SDLC; pruebas de seguridad            | Defectos de seguridad; cobertura     |
| Cumplimiento              | Evidencias, acuerdos, retención                                   | Auditorías; contratos; documentación  | Cumplimiento de plazos               |
| RR.HH.                    | Formación y disciplina                                            | Capacitación; sanciones               | % de personal formado                |

## 11. Roadmap de remediación y cierre de brechas

Las prioridades se han definido por riesgo e impacto operativo, alineando quick wins (0–30 días), mediano plazo (30–90 días) y largo plazo (90–180 días). El enfoque se alinea con RMF para preparar, seleccionar, implementar, evaluar y monitorear los controles[^5].

Tabla 13. Plan de acción priorizado

| Acción                                                                 | Prioridad | Esfuerzo | Dependencias              | Impacto en riesgo/compliance                  | Fecha objetivo |
|------------------------------------------------------------------------|----------|----------|---------------------------|-----------------------------------------------|---------------|
| Consolidar matriz de configuración por entorno (CORS, hosts, proxies) | Alta     | Bajo     | Settings                  | Reducción de exposición accidental             | 0–30 días     |
| Endurecer CORS y retirar comodines                                     | Alta     | Bajo     | Middleware                | Menor superficie de ataque                     | 0–30 días     |
| Readiness con dependencias requeridas vs opcionales                    | Alta     | Medio    | Endpoints/lifespan        | Claridad operativa y disponibilidad            | 0–30 días     |
| Automatizar CREATE EXTENSION postgis y índice espacial                 | Alta     | Medio    | Alembic/env.py            | Correctness geoespacial consistente            | 30–90 días    |
| Endurecer TLS de Redis y retirar ssl_cert_reqs=None                    | Alta     | Medio    | Core/cache, ws_pubsub     | Seguridad de transporte y cumplimiento         | 30–90 días    |
| Pool tuning por entorno                                                | Media    | Medio    | Core/database             | Estabilidad bajo carga                         | 30–90 días    |
| Cifrado en reposo (DB/disk) y en uso (campos críticos)                 | Alta     | Medio    | DB/Infra/Dev              | Protección de PII y operativos                 | 90–180 días   |
| Auditoría y trazabilidad mejorada (DB triggers, correlación SIEM)      | Media    | Medio    | Observability/DBA         | Cumplimiento y respuesta a incidentes          | 90–180 días   |
| Pruebas DR (RTO/RPO), calendarios y evidencias                         | Alta     | Medio    | SRE/DBA                   | Resiliencia y continuidad                      | 90–180 días   |
| Cobertura de pruebas ≥85% y carga sistemática                          | Media    | Alto     | QA/Dev                    | Calidad y confianza en despliegues             | 90–180 días   |

Este roadmap integra tanto la dimensión técnica (cifrado, TLS, PostGIS) como la de gobernanza y resiliencia (SLAs, DR, auditoría), y se acompaña de métricas de seguimiento para verificar eficacia.

## 12. Anexos técnicos

Glosario de términos:
- HIPAA: Ley que establece estándares de protección de información de salud; su Regla de Seguridad exige salvaguardas administrativas, físicas y técnicas.
- NIST CSF 2.0: Marco de ciberseguridad con funciones Govern, Identify, Protect, Detect, Respond y Recover.
- RMF: Proceso de gestión de riesgos en siete pasos para autorizar y monitorear sistemas.
- ISO/IEC 27001:2022: Estándar de SGSI con cláusulas 4–10 y controles Anexo A.
- ePHI/PII: Información de salud protegida electrónica / información personal identificable.
- RBAC/ABAC: Control de acceso basado en roles / basado en atributos.
- MFA: Autenticación multifactor.
- TLS: Transport Layer Security.

Plantillas:
- Política de clasificación de datos: guía para etiquetado, acceso mínimo y controles por sensibilidad.
- Procedimiento de auditoría: checklist de eventos, campos y retención, con instrucciones de correlación y verificación.

Evidencias:
- Endpoints de health y readiness: observaciones en producción y métricas asociadas[^2].
- Catálogo de métricas: conexiones WS, mensajes, broadcasts, latencias y errores[^1].
- Consultas PostGIS: uso de geography y operadores para nearest neighbor y distancias[^1].

## Conclusiones y estado de brechas

GRUPO_GAD presenta fundamentos sólidos en arquitectura asíncrona, observabilidad, resiliencia y separación de responsabilidades, con instrumentación y health checks útiles para operación 24/7[^1][^2]. No obstante, la adaptación de HIPAA a entornos operativos/tácticos exige cerrar brechas críticas: cifrado en reposo y en uso; clasificación de datos y DLP/anonimización; política formal de auditoría y retención a nivel de base de datos; SLAs y pruebas DR con RTO/RPO; autenticación resistente al phishing y autorización granular por canal/tópico; y la formalización de la matriz RBAC/ABAC en el flujo operativo. Estas brechas son consistentes con los hallazgos y con la orientación de marcos NIST, ISO y del NDAA, y su cierre debe abordarse con el roadmap propuesto.

En síntesis, la consolidación del cumplimiento requiere completar la dimensión de protección de datos y trazabilidad, endurecer la seguridad de transmisión y autenticación, y formalizar SLAs y DR. Con estas medidas, GRUPO_GAD alcanzará una postura de cumplimiento alineada con HIPAA adaptado, NIST CSF/RMF e ISO 27001, con capacidad de auditoría y resiliencia acorde a sistemas operativos/tácticos 24/7.

---

## Referencias

[^1]: Repositorio GRUPO_GAD — GitHub. https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD — Aplicación en Fly.io. https://grupo-gad.fly.dev  
[^3]: NIST Cybersecurity Framework 2.0 (CSWP-29). https://doi.org/10.6028/NIST.CSWP.29  
[^4]: Cybersecurity Framework | NIST (CSF 2.0). https://www.nist.gov/cyberframework  
[^5]: NIST Risk Management Framework (RMF). https://csrc.nist.gov/projects/risk-management  
[^6]: Summary of the HIPAA Security Rule - HHS.gov. https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html  
[^7]: HIPAA Security Rule to Strengthen the Cybersecurity of ePHI (NPRM 2025). https://www.federalregister.gov/documents/2025/01/06/2024-30983/hipaa-security-rule-to-strengthen-the-cybersecurity-of-electronic-protected-health-information  
[^8]: HIPAA Updates and Changes in 2025 - HIPAA Journal. https://www.hipaajournal.com/hipaa-updates-hipaa-changes/  
[^9]: HIPAA Compliance in 2025: What's Changing & Why It Matters - Compass ITC. https://www.compassitc.com/blog/hipaa-compliance-in-2025-whats-changing-why-it-matters  
[^10]: HIPAA Encryption Requirements - 2025 Update - HIPAA Journal. https://www.hipaajournal.com/hipaa-encryption-requirements/  
[^11]: Data Encryption Requirements 2025 - Paperclip. https://paperclip.com/data-encryption-requirements-2025-why-data-in-use-protection-is-now-mandatory/  
[^12]: FedRAMP | FedRAMP.gov. https://www.fedramp.gov/  
[^13]: API Technical Guidance (DoD CTO, 2025). https://www.cto.mil/wp-content/uploads/2025/05/API-Tech-Guidance-MVCR-2-2025_0516-Cleared.pdf  
[^14]: Mastering ISO 27001 controls: 2025 guide - Thoropass. https://www.thoropass.com/blog/mastering-iso-27001-controls-your-2025-guide-to-information-security  
[^15]: S.4638 - National Defense Authorization Act for Fiscal Year 2025 (NDAA FY25). https://www.congress.gov/bill/118th-congress/senate-bill/4638/text  
[^16]: Data Reliability Audit Requirements - FY 2025 (ACF). https://acf.gov/css/policy-guidance/data-reliability-audit-requirements-fy-2025  
[^17]: Data Protection Laws and Regulations Report 2025: USA - ICLG. https://iclg.com/practice-areas/data-protection-laws-and-regulations/usa  
[^18]: 2025 National Interagency Standards for Resource Mobilization. https://www.nifc.gov/sites/default/files/NICC/3-Logistics/Reference%20Documents/Mob%20Guide/2025/2025%20NATIONAL%20INTERAGENCY%20STANDARDS%20for%20RESOURCE%20MOBILIZATION_Final_3-5.pdf