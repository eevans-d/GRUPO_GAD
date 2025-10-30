# HIPAA Compliance Operativo para Sistemas Tácticos Gubernamentales (GRUPO_GAD)

## 0. Resumen ejecutivo y mapa de brechas

La adaptación de la Health Insurance Portability and Accountability Act (HIPAA) a sistemas operativos/tácticos gubernamentales exige extender el espíritu de la Regla de Seguridad —confidencialidad, integridad y disponibilidad— a datos operativos sensibles (no sanitarios) que, si se comprometen, pueden poner en riesgo a efectivos, operaciones y comunidad. Bajo el Notice of Proposed Rulemaking (NPRM) 2025, las entidades reguladas enfrentan un giro relevante: se elimina la histórica distinción entre especificaciones “requeridas” y “abordables”; la expectativa regulatoria es que todas sean efectivamente obligatorias, salvo excepciones explícitas, con mayor énfasis en controles técnicos modernos (MFA universal, cifrado en tránsito y en reposo, gestión de parches, segmentación de red, revisiones sistemáticas de registros, inventarios de activos y mapas de flujo de datos). Este cambio refuerza la necesidad de un programa de seguridad auditable, con evidencia verificable en artefactos operativos y contractual (Business Associate Agreements, BAAs).[^1][^3][^2]

En GRUPO_GAD, el bot de Telegram como interfaz operativa, el backend (FastAPI, PostGIS, Redis, WebSockets) y la capa de observabilidad conforman un ecosistema con arquitectura asíncrona y trazabilidad básica (logging con Loguru, métricas de WebSockets, health checks). La aplicación está desplegada y expone capacidades operativas que, correctamente reforzadas, pueden sostenerse en un entorno 24/7 de misión crítica.[^5][^6] Sin embargo, persisten brechas críticas que deben cerrarse antes del go-live: cifrado en reposo (base de datos y backups), trazabilidad completa de auditoría (quién, qué, cuándo, dónde, sobre qué recurso, desde qué canal), clasificación de datos operativos y políticas de retención, rotaciones de secretos (incluido el token del bot), segmentación y endurecimiento de TLS (evitar fallbacks inseguros en Redis), controles de integridad (hash, firmas, no repudio), pruebas de restauración de backups y procedimientos de respuesta a incidentes formalizados.

Las siguientes tablas sintetizan el estado de cumplimiento por dominio HIPAA y la priorización de riesgos operacionales.

Para contextualizar el nivel de preparación por dimensión, el siguiente scorecard integra la visión ejecutiva por componentes críticos del sistema.

Tabla 0.A. Scorecard ejecutivo por dimensión

| Dimensión                          | Estado      | Evidencia clave                                                                                 | Riesgo principal                                        | Recomendación prioritaria                                                  |
|------------------------------------|-------------|--------------------------------------------------------------------------------------------------|---------------------------------------------------------|----------------------------------------------------------------------------|
| Arquitectura del bot               | Medio       | python-telegram-bot; handlers asíncronos; ApiService sincrónico; wizard en memoria              | Estado del wizard no persistente; dependencia sincrónica| Persistir wizard en Redis; migrar ApiService a cliente asíncrono           |
| Seguridad y cumplimiento           | Medio       | JWT en API; middlewares de seguridad; whitelisting; logging Loguru                              | Cifrado en reposo no verificado; audit trail incompleto | Implementar cifrado en reposo y audit logging integral                      |
| Integración con backend            | Medio       | FastAPI; PostGIS; Redis; WebSockets                                                             | Cliente API sincrónico; WS no instrumentados            | Cliente async; instrumentación WS y validación PostGIS/Redis               |
| Observabilidad y métricas          | Medio       | Prometheus/Grafana; health checks                                                               | Falta de métricas específicas del bot                   | Instrumentación de comandos, callbacks y wizard                            |
| Escalabilidad y performance        | Medio       | Redis cache/pub-sub; paginación en listas                                                       | Rate limiting in-memory; estado en memoria              | Rate limiting con Redis; sesiones persistentes; tuning de paginación       |

Este scorecard confirma que la arquitectura y las prácticas de desarrollo son sólidas, pero requieren consolidación en seguridad y cumplimiento para operar con datos operativos sensibles en contextos gubernamentales de alta criticidad.[^5][^6]

A continuación, se presenta la priorización de riesgos operacionales en términos de criticidad, probabilidad, impacto, con acciones requeridas.

Tabla 0.B. Riesgos operacionales priorizados

| Riesgo                                      | Criticidad | Probabilidad | Impacto | Score | Acción requerida                                                             |
|---------------------------------------------|------------|--------------|---------|-------|------------------------------------------------------------------------------|
| Cifrado en reposo no verificado             | Alto       | Media        | Alto    | 8/10  | Habilitar y verificar cifrado en BD/backups; gestión de llaves               |
| Audit trail incompleto                      | Alto       | Alta         | Alto    | 9/10  | Audit logging integral (quién/qué/cuándo/dónde/sobre qué canal)              |
| Token de Telegram sin rotación              | Medio      | Media        | Medio   | 6/10  | Rotación y gestión centralizada de secretos                                  |
| Rate limiting in-memory                     | Medio      | Alta         | Medio   | 7/10  | Migrar a Redis; etiquetado por usuario/IP/operación                          |
| Cliente API sincrónico                      | Medio      | Media        | Medio   | 6/10  | Cliente asíncrono con timeouts y reintentos                                  |

Cumplimiento HIPAA (adaptado) por dominio

Tabla 0.C. Mapa de cumplimiento HIPAA → estado en GRUPO_GAD

| Dominio HIPAA                     | Estado actual (adaptado) | Gap crítico                                | Acción prioritaria                                       |
|-----------------------------------|---------------------------|--------------------------------------------|----------------------------------------------------------|
| Administrativas (gobernanza, SRA) | Parcial                   | SRA documentado y ciclo de gestión         | Formalizar SRA, RMF, capacitación y sanciones            |
| Físicas (facility/workstation)    | Parcial                   | Política formal para despliegues field     | Endurecimiento de dispositivos y controles físicos       |
| Técnicas (acceso, auditoría)      | Parcial                   | Acceso granular y auditoría integral       | MFA resistente phishing; auditoría DB; logs protegidos   |
| Seguridad de transmisión          | Parcial                   | TLS Redis/WS endurecido; sin fallbacks     | Forzar TLS 1.2+; HSTS; retirar ssl_cert_reqs=None        |
| Integridad de datos               | Parcial                   | Controles de no alteración                 | Hash/firmas; validación; recuperación verificada         |
| Disponibilidad/DR                 | Parcial                   | SLAs y pruebas DR                          | RTO/RPO; backups cifrados; pruebas de restauración       |

Narrativa de riesgos y prioridades

La exposición de PII de efectivos, datos operativos (asignaciones, estados, ubicaciones) y comunicaciones operativas por canales como Telegram, WebSockets y Redis incrementa la superficie de ataque y las exigencias de trazabilidad. Bajo el NPRM 2025, las expectativas de controles técnicos se endurecen, especialmente en autenticación (MFA resistente al phishing), cifrado en tránsito y reposo, inventarios de activos y mapas de flujo de datos, revisión periódica de registros y gestión de parches con plazos definidos.[^1][^3][^2] En un sistema de operaciones de campo, el mínimo necesario y la necesidad de saber deben traducirse en RBAC/ABAC granular, segmentación por tópicos y canales, y auditabilidad correlacionada (IDs de usuario, tarea, ubicación y evento) para investigar incidentes con fiabilidad. La priorización debe cerrar primero cifrado en reposo y auditoría end-to-end; luego, segmentación y MFA resistente al phishing; y finalmente DR con SLAs y pruebas periódicas.

## 1. Metodología de evaluación y alcance

La evaluación combinó revisión estática del código y configuración del bot y la plataforma, análisis funcional de flujos críticos (API, WebSockets, bot), verificación de capacidades operativas (lifespan, health checks, métricas) y contrastación con marcos de referencia (HIPAA, NIST CSF 2.0, RMF, ISO 27001). Se priorizaron dominios de alto impacto: datos de efectivos, operaciones de campo, sistemas de notificación en tiempo real y auditorías de acceso/modificación.[^5][^6][^4]

Los criterios de aceptación fueron: evidencia auditable (artefactos reproducibles y trazables), efectividad operativa demostrada (health checks, métricas, respuesta bajo carga) y alineación con controles (HIPAA y NIST). Se adoptó el ciclo del NIST Risk Management Framework (RMF) —preparar, categorizar, seleccionar, implementar, evaluar, autorizar y monitorear— para estructurar el plan de remediación y la operación continua.[^5]

Limitaciones y brechas de información

- Cifrado en reposo de base de datos y backups: por confirmar.
- Persistencia de estado de sesión del wizard en Redis: no evidenciada (context.user_data en memoria).
- Auditoría de acciones del bot más allá del logging: no formalizada.
- Rate limiting específico del bot alineado con política gubernamental: no evidenciado.
- Rotación y fortaleza del token de Telegram: no verificada.
- Configuraciones CSP para UI del bot: no documentadas.
- Uso directo de consultas PostGIS desde el bot: no evidenciado.
- Inventario y estado de BAAs con terceros (Telegram, Fly.io, monitoring/logging): no documentado.
- Política de retención y almacenamiento de logs/audit trail (WORM): por definir.
- Detalle de controles de acceso por rol en el flujo operativo: no formalizado.
- Pruebas de DR con RTO/RPO y evidencias: ausentes.
- Disponibilidad/custodia de datos bajo HIPAA (aplicabilidad en entorno gubernamental): por confirmar.

Estas brechas se integran en el roadmap y plan de verificación.

## 2. Marco normativo aplicable y adaptación para entornos operativos/tácticos

HIPAA (Regla de Seguridad) establece estándares para proteger la ePHI, con salvaguardas administrativas, físicas y técnicas. Aunque HIPAA atiende salud, sus principios se adaptan a sistemas tácticos gubernamentales con datos operativos sensibles, manteniendo el foco en confidencialidad, integridad, disponibilidad y trazabilidad.[^2] El NPRM 2025 endurece controles y clarifica obligaciones, eliminando la distinción “requerida/abordable” y codificando actividades críticas (inventarios de activos, mapas de flujo, revisiones sistemáticas de registros, gestión de parches y MFA).[^1][^3]

NIST CSF 2.0 provee funciones y categorías para articular controles (Govern, Identify, Protect, Detect, Respond, Recover), y RMF establece el proceso para autorizar y monitorear sistemas de información, incluyendo SP 800-53 rev. 5.2.0.[^4][^5] ISO 27001 estructura el Sistema de Gestión (cláusulas 4–10) y controles Anexo A (logging, criptografía, continuidad, cadena de suministro), útiles para sostener evidencia de cumplimiento y madurez operativa. Cuando GRUPO_GAD utilice servicios cloud sujetos a exigencias federales, FedRAMP delimita autorización y baseline, y la guía de APIs del DoD refuerza autenticación/autorización y segmentación en integraciones críticas.[^7][^8]

Adaptación de salvaguardas HIPAA a datos operativos

Tabla 2.A. Adaptación HIPAA → controles operacionales

| Salvaguarda HIPAA (esencia)           | Equivalente operativo (NIST/ISO/RMF)        | Implementación en GRUPO_GAD                                              |
|---------------------------------------|----------------------------------------------|---------------------------------------------------------------------------|
| Análisis y gestión de riesgos         | Identify/Govern; RMF preparar/seleccionar    | SRA documentado; registro de riesgos por integración y dominio            |
| Controles de auditoría                | Detect; ISO A.8.15; SP 800-53 AU-*           | Audit trail end-to-end en app y DB; correlación SIEM                      |
| Autenticación/autorización            | Protect; ISO A.8.5; NDAA FY25 (phishing-resistant) | MFA resistente al phishing; RBAC/ABAC; JWT con rotación y caducidad       |
| Seguridad de transmisión              | Protect; ISO A.8.21/8.24; SP 800-53 SC-*     | TLS en API/WS/Redis; evitar fallbacks inseguros; HSTS                     |
| Integridad de datos                   | Protect/Detect; ISO A.8.3/8.11               | Hashing/firmas; validación de entrada; DLP/enmascaramiento                |
| Disponibilidad y contingencia         | Recover; ISO A.8.13/8.14; SP 800-53 CP-*     | Backups cifrados; DR con RTO/RPO; health checks y readiness               |
| Políticas y procedimientos            | Govern; ISO cláusulas 4–10; SP 800-53 PM-*   | Políticas por dominio; evidencia de cumplimiento (retención ≥6 años)      |

Este mapeo guía la implementación y permite auditar la traducción de principios de HIPAA a controles técnicos y operacionales adecuados para datos de efectivos y operaciones de campo.[^2][^4][^5][^7][^8][^10]

## 3. HIPAA Security Rule Compliance (adaptado)

Salvaguardas administrativas

Se requiere formalizar el rol del Oficial de Seguridad, un programa de capacitación con sanciones, y un Security Risk Assessment (SRA) con gestión de riesgos y revisiones periódicas. El inventario de activos y el mapa de flujo de datos deben mantenerse actualizados (al menos cada 12 meses y ante cambios relevantes), integrando el ciclo del RMF para preparar, categorizar, seleccionar, implementar, evaluar y autorizar controles.[^1][^5]

Salvaguardas físicas

En entornos de operación de campo y despliegues remotos, las políticas deben cubrir controles de facility, seguridad de workstation y dispositivos, almacenamiento cifrado, cadena de custodia y procedimientos de recuperación.

Salvaguardas técnicas

El sistema debe implementar control de acceso único (unique user IDs), cierre de sesión automático (logoff), procedimientos de acceso de emergencia, modificación de acceso con trazabilidad, integridad de datos, auditoría, cifrado en tránsito y, bajo el NPRM y expectativas modernas, cifrado en reposo para conjuntos de datos sensibles.[^2][^1][^10]

Matriz de cumplimiento HIPAA → controles actuales

Tabla 3.A. Salvaguardas HIPAA → evidencia en GRUPO_GAD

| Salvaguarda HIPAA             | Estado        | Evidencia                            | Gap                                | Acción                                                 |
|-------------------------------|---------------|--------------------------------------|------------------------------------|--------------------------------------------------------|
| Administrativas               | Parcial       | Políticas base; roles implícitos     | SRA formal; sanciones documentadas | Formalizar SRA; programa de capacitación y sanciones   |
| Físicas                       | Parcial       | Prácticas generales                  | Políticas field-specific           | Endurecer dispositivos; controles facility             |
| Técnicas: acceso              | Parcial       | JWT; whitelisting                    | MFA resistente phishing; granularidad| MFA; RBAC/ABAC por canal y tópico                      |
| Técnicas: auditoría           | Parcial       | Logging estructurado (Loguru)        | Audit trail integral               | Auditoría en app y DB; correlación SIEM               |
| Técnicas: integridad          | Parcial       | Validaciones de wizard               | Controles de no alteración         | Hash/firmas; verificación de backups                  |
| Transmisión                   | Parcial       | HTTPS; reverse proxy                 | TLS Redis/WS endurecido            | Forzar TLS 1.2+; retirar fallbacks                    |
| Cifrado en reposo             | Brecha        | No evidenciado                       | Activación/verificación            | Cifrar BD/backups; gestión de llaves                  |

Esta matriz resalta que el andamiaje técnico está en marcha, pero faltan formalización, controles criptográficos y trazabilidad integral para sostener una auditoría regulatoria.

### 3.1 Administrative Safeguards

La responsabilidad de seguridad debe estar asignada por escrito, con un programa de capacitación y sanciones, y un SRA que documente alcance, amenazas razonablemente anticipadas, vulnerabilidades, probabilidad e impacto, niveles de riesgo, medidas de seguridad actuales y plan de mitigación. El inventario de activos y el mapa de flujo de datos (entrada/salida/externo) deben revisarse al menos anualmente y ante cambios (nuevas tecnologías, incidentes, fusiones, modificaciones legales).[^1][^5]

Plantilla de registro de riesgos

Tabla 3.1.A. Registro de riesgos (plantilla)

| Amenaza/Vulnerabilidad                         | Probabilidad | Impacto | Nivel de riesgo | Control propuesto                          | Dueño       | Fecha objetivo |
|-----------------------------------------------|--------------|---------|-----------------|--------------------------------------------|-------------|----------------|
| Exposición de PII de efectivos                | Media        | Alta    | Alta            | Cifrado en reposo; DLP; MFA                 | Seguridad   | 30–90 días     |
| Intercepción de canal WS/Redis                | Media        | Alta    | Alta            | TLS 1.2+; segmentación; HSTS                | Infra/Dev   | 30–90 días     |
| Acceso no autorizado por rol insuficiente     | Media        | Media   | Media           | RBAC/ABAC; revisiones de acceso             | Producto    | 90–180 días    |
| Ransomware en BD/backups                      | Baja–Media   | Alta    | Alta            | Backups cifrados; DR probado                | SRE/DBA     | 90–180 días    |

### 3.2 Physical Safeguards

Se deben consolidar controles de facility (accesos físicos, registro de visitantes), seguridad de workstation (dispositivos de campo con cifrado en reposo, bloqueo automático, inventario), y protección de equipos (mantenimiento, disposición segura, cadena de custodia). Estos controles aseguran la continuidad operativa y previenen extracciones físicas o manipulaciones.

Catálogo de controles físicos

Tabla 3.2.A. Controles físicos propuestos

| Control                        | Alcance                         | Evidencia requerida                         | Estado       |
|--------------------------------|----------------------------------|----------------------------------------------|-------------|
| Acceso físico a salas de servidores | DC/Sala de equipos              | Registro de accesos; CCTV                    | Pendiente   |
| Cifrado de dispositivos de campo | Laptops/tablets/smartphones     | Política; verificación de cifrado            | Pendiente   |
| Bloqueo automático de estación | Todos los dispositivos           | Configuraciones; pruebas                     | Propuesto   |
| Disposición segura de medios   | Equipos/discos                  | Procedimientos; certificados de destrucción  | Propuesto   |

### 3.3 Technical Safeguards

Controles de acceso, auditoría e integridad, y seguridad de transmisión deben ser implementados y verificados. El cifrado en tránsito es obligatorio en API/WS/Redis; el cifrado en reposo debe activarse en BD y backups. La gestión de secretos y la autenticación multifactor (MFA) resistente al phishing deben consolidarse antes del go-live.[^2][^1][^10]

Catálogo de controles técnicos

Tabla 3.3.A. Controles técnicos por estándar HIPAA

| Estándar HIPAA        | Control propuesto                               | Métrica                      | Estado       |
|-----------------------|--------------------------------------------------|------------------------------|-------------|
| Acceso único          | Unique user IDs + MFA                           | % usuarios con MFA           | Parcial      |
| Cierre de sesión      | Auto-logoff timeout                             | p95 inactividad < 15 min     | Propuesto    |
| Auditoría             | Audit trail integral (DB+app)                   | % eventos críticos con trazabilidad | Parcial  |
| Integridad            | Hash/firmas; validación de entrada              | % cambios con verificación   | Propuesto    |
| Transmisión           | TLS 1.2+; HSTS; sin fallbacks                   | % endpoints con TLS fuerte   | Parcial      |
| Reposo                | Cifrado AES-256 en BD/backups                   | % datasets cifrados          | Brecha       |

## 4. Protección de datos operativos sensibles

Clasificación y principios

Para datos de efectivos, ubicaciones geográficas, comunicaciones operativas, horarios/rutinas e información de operativos, la adaptación de HIPAA exige aplicar mínimo necesario y necesidad de saber. Aunque no se trata de ePHI sanitaria, el estándar de protección (cifrado en tránsito y reposo, DLP, auditoría, integridad, retención) se mantiene. El cifrado en reposo y en uso es cada vez más esperado bajo las actualizaciones de 2025; implementar controles robustos reduce el riesgo y la probabilidad de sanciones.[^1][^10][^11]

Matriz de clasificación de datos

Tabla 4.A. Clasificación y controles

| Clase de dato                    | Ejemplos                                 | Acceso mínimo necesario           | Controles aplicados                          |
|----------------------------------|------------------------------------------|-----------------------------------|----------------------------------------------|
| PII operativos (efectivos)       | DNI, telegram_id                         | Supervisor/Administrativo         | Cifrado reposo/tránsito; MFA; auditoría      |
| Operativos sensibles             | Estado, asignación, ubicación            | Operador/Supervisor en misión     | TLS; RBAC; DLP; logging; integridad          |
| Metadatos operativos             | Códigos de tarea, tiempos, estados       | Operador; automatizaciones        | Validación; rate limiting; protección contra tampering |
| Audit trail                      | Eventos de acceso y cambios              | Auditoría/Seguridad               | Retención (≥6 años); correlación; WORM       |

Inventario de datos sensibles y requisitos de cifrado/privacidad

Tabla 4.B. Requisitos por dataset

| Dataset                         | Sensibilidad | Cifrado tránsito | Cifrado reposo | Uso (protección)    | Retención       |
|---------------------------------|-------------|------------------|----------------|---------------------|-----------------|
| PII de efectivos                | Alta        | TLS              | Implementar/Confirmar | Enclaves (evaluar) | ≥6 años         |
| Geolocalización (efectivos)     | Alta        | TLS              | Implementar/Confirmar | Agregación por zonas | 1–3 años       |
| Tareas/asignaciones             | Media       | TLS              | Implementar/Confirmar | Idempotencia       | 1–3 años       |
| Notificaciones (eventos)        | Media       | TLS              | Implementar/Confirmar | Rate limiting       | 1–3 años       |

Estas tablas articulan la aplicación del principio de mínimo necesario y la necesidad de cifrado robusto, alineadas con expectativas actuales de HIPAA y NIST.[^10][^2]

## 5. Access Controls operativos

El sistema debe implementar unique user identification, cierre de sesión automático, procedimientos de emergencia (con trazabilidad y caducidad), y logging de modificaciones de acceso (quién, cuándo, qué cambios y aprobación). La autorización debe ser granular (RBAC/ABAC), segregada por canal y tópico, y alineada con el principio de mínimo necesario. La MFA resistente al phishing es exigible bajo las tendencias regulatorias de 2025 y la orientación de defensa para sistemas de misión.[^1][^15]

Matriz RBAC/ABAC por canal y acción

Tabla 5.A. Roles/acciones por canal

| Rol            | API (acciones)           | WS (suscripción)           | Bot (comandos)           | Botón/teclado         |
|----------------|---------------------------|----------------------------|--------------------------|-----------------------|
| Ciudadano      | Leer historial propias    | —                          | /start, /help, /historial| Menús y paginación    |
| Operador       | Crear/finalizar tareas    | ws_tareas_estado           | /crear, /finalizar       | Confirmación/selección|
| Supervisor     | Asignar efectivos         | ws_tareas_asignacion       | —                        | Edición/asignación    |
| Administrador  | Gestión de usuarios/roles | Todos (admin)              | —                        | Configuración         |

Parámetros de sesión y logoff por rol y contexto

Tabla 5.B. Session management

| Rol          | Inactividad (timeout) | Acceso de emergencia       | MFA            | Estado        |
|--------------|------------------------|----------------------------|----------------|---------------|
| Ciudadano    | 15 min                 | No aplica                  | Recomendada    | Propuesto     |
| Operador     | 10 min                 | Just-in-time, trazable     | Obligatoria    | Propuesto     |
| Supervisor   | 10 min                 | Just-in-time, trazable     | Obligatoria    | Propuesto     |
| Administrador| 5 min                  | Just-in-time, trazable     | Obligatoria    | Propuesto     |

Estas tablas vinculan autorización y gestión de sesión para reducir el riesgo de abuso de credenciales y accesos indebidos, en línea con la propuesta regulatoria y mejores prácticas técnicas.[^1][^15]

## 6. Audit Controls operativos

La auditoría debe registrar acceso a PII y a datos operativos, modificaciones de registros, interacciones del bot (quién, qué, cuándo, dónde), consultas geoespaciales, y proteger los logs (centralizados, resistentes a manipulación, WORM cuando aplique) con retención alineada a documentación (≥6 años para políticas; 1–3 años para logs operativos sensibles).[^2][^16][^9]

Catálogo de eventos operativos y campos mínimos

Tabla 6.A. Auditoría

| Evento                     | Campos mínimos                                                                 | Retención    |
|---------------------------|---------------------------------------------------------------------------------|-------------|
| Creación de tarea         | actor, rol, request_id, task_id, timestamp, canal, resultado                   | 1–3 años    |
| Asignación a efectivo     | actor, rol, task_id, assignment_id, geolocalización, timestamp, canal          | 1–3 años    |
| Inicio/fin de despliegue  | actor, task_id, geolocalización, timestamp, resultado                          | 1–3 años    |
| Finalización              | actor, task_id, timestamp, canal, evidencia adjunta (hash)                      | 1–3 años    |
| Notificación automática   | event_id, topic, timestamp, receptor (rol), estado de entrega                   | 1–3 años    |
| Login/emisión de tokens   | usuario/activo, método, timestamp, resultado, IP                                | 1–3 años    |
| Acceso a PII              | usuario/activo, recurso, acción, timestamp, autorización, IP                    | 1–3 años    |
| Cambio de permisos        | quien, que cambio, aprobador, timestamp, justificación                          | ≥6 años     |

Protección y retención de logs

Tabla 6.B. Log protection

| Control          | Alcance         | Evidencia                         | Estado       |
|------------------|-----------------|-----------------------------------|-------------|
| Centralización   | App/DB/Infra    | Pipelines; SIEM                   | Propuesto   |
| Inmutabilidad    | Logs críticos   | WORM; controles de borrado        | Propuesto   |
| Minimización     | App logs        | Políticas DLP; evitar PHI         | Propuesto   |
| Revisión         | Todos los logs  | Procedimientos y registros        | Propuesto   |

Esta sección consolida la trazabilidad “quién hizo qué, cuándo, dónde y sobre qué”, esencial para auditorías gubernamentales y fiabilidad de datos.[^16][^9]

## 7. Integridad de datos operativos

La integridad debe garantizarse con controles técnicos (hashing, firmas digitales, validación de entrada/salida, DLP) y procedimientos (validación de backups, verificación de restauración, pruebas de recuperación). Para backpressure y alta concurrencia en WebSockets, los eventos deben ser idempotentes, con mecanismos de reintento y confirmación para evitar duplicidades o pérdidas.

Matriz de integridad por clase de dato

Tabla 7.A. Controles de integridad

| Clase de dato           | Control                        | Frecuencia        | Evidencia              | Estado       |
|-------------------------|--------------------------------|-------------------|------------------------|-------------|
| PII operativos          | Hash/firmas; validación        | On-write          | Registros de verificación| Propuesto  |
| Operativos (estado)     | Idempotencia en flujos         | On-event          | Métricas de duplicados | Propuesto   |
| Geolocalización         | Validación de rango/srid       | On-query          | Logs de validación     | Propuesto   |
| Backups                 | Verificación hash y restore    | Mensual/Trimestral| Reportes de prueba     | Propuesto   |

La integridad protege contra alteración no autorizada y asegura la fiabilidad de la operación en campo, coherente con exigencias de trazabilidad y auditoría.[^2][^14]

## 8. Person o Device Authentication

La autenticación debe ser robusta para usuarios y dispositivos, con MFA resistente al phishing (NDAA FY25), tokens de corta duración, gestión centralizada de secretos (Vault/Secrets Manager), rotación documentada y timeouts de sesión razonables. La autenticación de dispositivos de campo debe asegurar canal cifrado, identidad del dispositivo y revocación ágil.[^15][^1]

Mapa de autenticación por flujo y control

Tabla 8.A. Autenticación

| Flujo                     | Factor(es)                 | Control de sesión           | Evidencia auditable         | Estado       |
|--------------------------|----------------------------|-----------------------------|-----------------------------|-------------|
| Login API                | Contraseña + MFA           | JWT corto; refresh revocable| Logs de autenticación       | Propuesto   |
| Conexión WS              | Token + MFA                | Heartbeat; expiración       | Métricas WS; logs           | Propuesto   |
| Bot Telegram             | Token del bot + verificación ID | Comandos por rol; timeouts | Logs por comando            | Propuesto   |
| Dispositivo de campo     | Certificado + MFA          | Canal TLS; revocación       | Inventario de dispositivos  | Propuesto   |

Este enfoque reduce el riesgo de credenciales comprometidas y asegura identidad resistente a ataques de phishing, conforme a tendencias de defensa nacional.[^15][^1]

## 9. Transmission Security operativa

La seguridad de transmisión debe forzar TLS 1.2+ (idealmente 1.3) en API, WebSockets y Redis, con HSTS, pinning de certificados cuando aplique, y retirada de fallbacks inseguros (por ejemplo, ssl_cert_reqs=None). Las comunicaciones del bot por Telegram deben evitar PHI o minimizar su exposición; los límites y la retención de mensajes del bot deben formalizarse con el proveedor, dada la ausencia de BAAs con plataformas de mensajería generalista.[^10][^8]

Matriz de cifrado en tránsito por canal

Tabla 9.A. Transmisión

| Canal      | Versión TLS | Suite de cifrado        | Certificados         | Estado       |
|------------|-------------|-------------------------|----------------------|-------------|
| API (HTTPS)| 1.2+/1.3    | AES-256/ECDHE           | Válidos; HSTS        | Parcial      |
| WebSockets | 1.2+/1.3    | ECDHE; forward secrecy  | Válidos              | Parcial      |
| Redis      | 1.2+/1.3    | AES-256/ECDHE           | Validación de servidor| Brecha      |
| Bot (Telegram) | TLS interno | —                       | —                    | Parcial      |

La seguridad de transmisión protege datos en movimiento y es un pilar del cumplimiento HIPAA adaptado; el endurecimiento y la verificación son cruciales.[^10][^8]

## 10. Incident Response operativo

El plan de respuesta a incidentes debe documentar roles, escalamiento, comunicación y retención de evidencias, con playbooks para escenarios (exposición de PII, compromiso de canal de Telegram, degradación WS/Redis, ransomware). La notificación de brechas bajo HIPAA aplica si existe PHI no segura: notificaciones a individuos, HHS y medios dentro de plazos (60 días) y según leyes estatales más estrictas. La propuesta de regla refuerza la obligación de planes escritos y procedimientos de reporte, y sugiere plazos más cortos (por ejemplo, restauración en 72 horas para ciertos casos).[^9][^1]

Playbooks de respuesta

Tabla 10.A. Escenarios y acciones

| Escenario                         | Detección                 | Contención           | Erradicación         | Recuperación               | Notificación                |
|-----------------------------------|---------------------------|----------------------|----------------------|----------------------------|-----------------------------|
| Exposición de PII                 | Alertas de acceso         | Revocar acceso       | Parches/config       | Restaurar servicios        | Individuos/HHS ≤60 días     |
| Compromiso de Telegram            | Logs anómalos             | Rotación de token    | Revisión de permisos | Refuerzo de autenticación  | Según impacto; ley estatal  |
| Degradación WS/Redis              | Métricas/latencias        | Fallback controlado  | Ajuste de canal      | Reintentos/idempotencia    | N/A si no PHI               |
| Ransomware en BD/backups          | Detección anti-malware    | Aislamiento          | Limpieza             | Restore probado            | Individuos/HHS según reglas |

Este marco de respuesta debe integrarse con auditorías y revisiones de registros para fortalecer la postura y cumplir con obligaciones regulatorias.[^9][^1]

## 11. Business Associate Agreements (BAAs)

Definiciones y alcance

Un Business Associate Agreement (BAA) es un contrato obligatorio bajo HIPAA entre una entidad cubierta y un tercero que accede o maneja PHI en su nombre. Las plataformas de mensajería generalista como Telegram, por defecto, no firman BAAs, por lo que su uso debe evitarse para PHI o, si se usa operativamente, debe implementarse un diseño que minimice exposición y formalizar acuerdos equivalentes con proveedores que procesen datos operativos equivalentes a PHI.[^17]

Mapa de integraciones vs obligaciones contractuales

Tabla 11.A. BAAs propuestos

| Proveedor       | Tipo de dato            | BAA requerido | Cláusulas clave                              | Dueño       | Fecha objetivo |
|-----------------|-------------------------|---------------|-----------------------------------------------|-------------|----------------|
| Telegram        | Mensajería operativa    | No (por defecto) | Minimización; retención; seguridad de canal | Legal/Compras| 0–30 días      |
| Fly.io          | Infraestructura         | Sí            | Seguridad; notificación de incidentes; subcontratistas | Legal/Compras| 30–90 días     |
| Monitoring/Logging| Telemetría/logs       | Sí            | Protección de logs; retención; auditoría      | Seguridad   | 30–90 días     |

La ausencia de BAA con mensajería generalista obliga a un diseño cuidadoso (no enviar PHI, evitar contenido sensible, enlaces autenticados), y a identificar alternativas con BAA para flujos que requieran mensajería segura.[^17]

## 12. HIPAA Risk Assessment operativo (SRA)

Metodología

El Security Risk Assessment (SRA) debe seguir la guía de HHS: definir alcance (toda la información operativa sensible creada, recibida, mantenida o transmitida), recopilar datos (inventario y flujos), identificar amenazas y vulnerabilidades razonablemente anticipadas, evaluar controles actuales, determinar probabilidad e impacto, asignar niveles de riesgo, documentar, y revisar periódicamente (al menos anual y ante cambios).[^3] La plantilla a continuación ilustra la aplicación en dominios de GRUPO_GAD.

Registro de riesgos por dominio operativo

Tabla 12.A. SRA

| Dominio                         | Amenaza/Vulnerabilidad                      | Probabilidad | Impacto | Nivel de riesgo | Control propuesto                                 | Evidencia                | Estado       |
|---------------------------------|---------------------------------------------|--------------|---------|-----------------|---------------------------------------------------|--------------------------|-------------|
| Bot/ciudadano                   | PHI en mensajes; trazabilidad incompleta    | Media        | Alta    | Alta            | Minimización; audit trail por comando             | Logs del bot             | Propuesto   |
| API/Backend                     | Acceso granular insuficiente; TLS variable  | Media        | Alta    | Alta            | RBAC/ABAC; TLS 1.2+; HSTS                         | Middlewares; certificados| Propuesto   |
| WS/Redis                        | Fallbacks inseguros; pérdida de eventos     | Media        | Media   | Media           | Forzar TLS; idempotencia; backpressure            | Métricas WS; logs        | Propuesto   |
| PostGIS                         | Consultas no instrumentadas                 | Baja–Media   | Media   | Media           | Endpoint dedicado; auditoría de consultas         | Logs DB                  | Propuesto   |
| Backups/DR                      | Restauración no verificada                  | Media        | Alta    | Alta            | Pruebas periódicas; cifrado; RTO/RPO              | Reportes de restauración | Propuesto   |

Esta SRA se alinea con el RMF y soporta la gestión continua del riesgo.[^3][^5]

## 13. Roadmap de cumplimiento y verificación

Quick wins (0–30 días)

- Consolidar matriz de configuración por entorno (CORS, hosts, proxies), retirar comodines.
- Endurecer TLS en API y retirar fallbacks inseguros en Redis.
- Implementar audit logging mínimo viable por comando y endpoint, con correlación de IDs.
- Gestionar secretos centralizadamente (rotación documentada del token del bot, credenciales API).
- Instrumentación básica de métricas del bot (comandos, callbacks, wizard).

Mediano plazo (30–90 días)

- Cifrado en reposo de BD/backups y verificación.
- RBAC/ABAC granular por canal/tópico; MFA resistente al phishing.
- Rate limiting con Redis; monitoreo y alertas.
- Segmentación de red; endurecimiento de HSTS y certificados.
- Auditoría en base de datos (triggers) y correlación con SIEM.
- Pruebas de restauración y evidencias de DR.

Largo plazo (90–180 días)

- Pruebas DR completas (RTO/RPO), calendarios y evidencias.
- Cobertura de pruebas ≥85%, incluyendo carga/sobresaturación/recuperación.
- Formalización de SLAs 24/7; planes de continuidad.
- Política de retención y almacenamiento WORM para logs críticos.
- Programa de capacitación y sanciones con evidencia.

Plan de acción priorizado

Tabla 13.A. Remediación

| Acción                                                                 | Riesgo mitigado                           | Esfuerzo | Impacto                      | Dependencias              | Fecha objetivo |
|------------------------------------------------------------------------|-------------------------------------------|----------|------------------------------|---------------------------|----------------|
| Endurecer TLS (API/WS/Redis) y retirar fallbacks                       | Intercepción y MITM                       | Medio    | Alto                         | Middlewares/Infra         | 0–30 días      |
| Audit logging mínimo viable por comando/endpoint                       | Trazabilidad insuficiente                 | Bajo     | Alto                         | App/DB                    | 0–30 días      |
| Gestión centralizada de secretos y rotación de tokens                  | Compromiso de credenciales                | Bajo     | Alto                         | Vault/Secrets Manager     | 0–30 días      |
| Cifrado en reposo (BD/backups) y verificación                          | Exposición de datos                       | Medio    | Alto                         | DBA/Infra/Dev             | 30–90 días     |
| MFA resistente al phishing; RBAC/ABAC granular                          | Acceso indebido                           | Medio    | Alto                         | IdP/Seguridad             | 30–90 días     |
| Rate limiting con Redis; instrumentación de métricas                   | Abuso y spoofing                          | Medio    | Alto                         | Redis/Monitoring          | 30–90 días     |
| Auditoría en DB y correlación SIEM                                     | Detección insuficiente                    | Medio    | Alto                         | DBA/Observability         | 30–90 días     |
| DR probado con RTO/RPO                                                 | Indisponibilidad                           | Medio    | Alto                         | SRE/DBA                   | 90–180 días    |
| Cobertura de pruebas ≥85% y carga/resiliencia                          | Defectos y fallas bajo carga              | Alto     | Medio                        | QA/Dev                    | 90–180 días    |
| SLAs 24/7 y planes de continuidad                                      | Objetivos de servicio                     | Medio    | Medio                        | Operaciones               | 90–180 días    |

Este plan se alinea con el RMF y las tendencias regulatorias, priorizando los controles con mayor reducción de riesgo para un go-live seguro.[^5][^1]

## Anexos técnicos

Glosario

- HIPAA: Regla de Seguridad que exige salvaguardas administrativas, físicas y técnicas para ePHI.
- ePHI/PII: Información de salud protegida electrónica / información personal identificable.
- NIST CSF 2.0: Marco de ciberseguridad con funciones Govern, Identify, Protect, Detect, Respond, Recover.
- RMF: Proceso de gestión de riesgos (preparar, categorizar, seleccionar, implementar, evaluar, autorizar, monitorear).
- ISO/IEC 27001:2022: Sistema de Gestión de Seguridad de la Información (SGSI) con cláusulas 4–10 y controles Anexo A.
- RBAC/ABAC: Control de acceso basado en roles / atributos.
- MFA: Autenticación multifactor.
- TLS: Transport Layer Security.
- WORM: Write Once Read Many (retención inmutable).

Plantillas

- Política de clasificación de datos operativos.
- Procedimiento de auditoría: checklist de eventos, campos y retención; correlación y verificación.
- Guía de respuesta a incidentes: roles, escalamiento, comunicación, evidencia y cierre.

Evidencias

- Health checks y readiness: observados en producción.
- Métricas WS: conexiones, mensajes, broadcasts, errores, heartbeats, latencias.
- Consultas PostGIS: uso de geography y operadores para nearest neighbor y distancias.

Referencias

[^1]: HIPAA Security Rule to Strengthen the Cybersecurity of ePHI (NPRM 2025) - Federal Register. https://www.federalregister.gov/documents/2025/01/06/2024-30983/hipaa-security-rule-to-strengthen-the-cybersecurity-of-electronic-protected-health-information  
[^2]: Summary of the HIPAA Security Rule - HHS.gov. https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html  
[^3]: Guidance on Risk Analysis - HHS.gov. https://www.hhs.gov/hipaa/for-professionals/security/guidance/guidance-risk-analysis/index.html  
[^4]: NIST Cybersecurity Framework 2.0 (CSWP-29). https://doi.org/10.6028/NIST.CSWP.29  
[^5]: NIST Risk Management Framework (RMF). https://csrc.nist.gov/projects/risk-management  
[^6]: NIST SP 800-66 Rev.2, Implementing the HIPAA Security Rule. https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-66r2.pdf  
[^7]: FedRAMP | FedRAMP.gov. https://www.fedramp.gov/  
[^8]: API Technical Guidance (DoD CTO, 2025). https://www.cto.mil/wp-content/uploads/2025/05/API-Tech-Guidance-MVCR-2-2025_0516-Cleared.pdf  
[^9]: HIPAA Breach Notification Requirements (2025) - HIPAA Journal. https://www.hipaajournal.com/hipaa-breach-notification-requirements/  
[^10]: HIPAA Encryption Requirements (2025 Update) - HIPAA Journal. https://www.hipaajournal.com/hipaa-encryption-requirements/  
[^11]: Data Encryption Requirements 2025 - Paperclip. https://paperclip.com/data-encryption-requirements-2025-why-data-in-use-protection-is-now-mandatory/  
[^12]: HIPAA Administrative Safeguards (Security Series #2) - HHS.gov. https://www.hhs.gov/sites/default/files/ocr/privacy/hipaa/administrative/securityrule/adminsafeguards.pdf  
[^13]: HIPAA Technical Safeguards (Security Series #4) - HHS.gov. https://www.hhs.gov/sites/default/files/ocr/privacy/hipaa/administrative/securityrule/techsafeguards.pdf  
[^14]: Mastering ISO 27001 controls: 2025 guide - Thoropass. https://www.thoropass.com/blog/mastering-iso-27001-controls-your-2025-guide-to-information-security  
[^15]: S.4638 - National Defense Authorization Act for Fiscal Year 2025 (NDAA FY25). https://www.congress.gov/bill/118th-congress/senate-bill/4638/text  
[^16]: Data Reliability Audit Requirements - FY 2025 (ACF). https://acf.gov/css/policy-guidance/data-reliability-audit-requirements-fy-2025  
[^17]: HIPAA-compliant analytics in 2025: Vendor selection guide - Piwik PRO. https://piwik.pro/blog/hipaa-compliant-analytics-vendor-selection-guide/  
[^18]: GRUPO_GAD - Repositorio (GitHub). https://github.com/eevans-d/GRUPO_GAD  
[^19]: GRUPO_GAD - Aplicación en Fly.io. https://grupo-gad.fly.dev

Conclusiones

GRUPO_GAD dispone de una base técnica sólida para operar en un contexto gubernamental: arquitectura asíncrona, observabilidad, resiliencia, separación de responsabilidades y trazabilidad básica. Para alcanzar un nivel de cumplimiento alineado con HIPAA adaptado y marcos NIST/ISO, se requiere cerrar brechas críticas: cifrado en reposo, auditoría integral, segmentación y endurecimiento de TLS, autenticación resistente al phishing, gestión de secretos y DR con SLAs. El roadmap propuesto prioriza controles que maximizan reducción de riesgo y facilita auditorías, en coherencia con el NPRM 2025 y las exigencias modernas de seguridad para operaciones tácticas 24/7.