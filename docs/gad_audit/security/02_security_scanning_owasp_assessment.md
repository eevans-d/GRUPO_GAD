# Blueprint integral de Security Scanning Automatizado y Evaluación OWASP Top 10 para Sistemas Operativos/Tácticos (GRUPO_GAD)

## Resumen ejecutivo y alcance de la auditoría OWASP Top 10

Este informe técnico presenta el resultado de un security scanning automatizado exhaustivo y una evaluación profunda del OWASP Top 10 adaptada al contexto gubernamental y operativo/táctico de GRUPO_GAD. El sistema evaluated comprende FastAPI (Python) como backend, PostgreSQL con extensión PostGIS para datos geoespaciales, Redis para cache/PubSub y escalado de WebSockets, y un bot de Telegram como canal operativo. La aplicación en producción está publicada en Fly.io y el estado del proyecto es 92% completado.

El security scanning automatizado se ejecutó con herramientas SAST y de auditoría de dependencias en el pipeline de CI/CD: pip-audit para vulnerabilidades conocidas, bandit para análisis estático, semgrep para patrones de seguridad y posibles secretos, y safety para librerías Python. Adicionalmente, se revisaron archivos críticos de configuración y middlewares, y se evaluó la gestión de secretos y variables de entorno a partir de las evidencias del repositorio y la aplicación en producción[^1][^2].

Los hallazgos consolidan un conjunto de riesgos con foco en: ausencia de refresh tokens y revocación de JWT, expiración de tokens de Telegram de siete días, secretos con placeholders inseguros (CHANGEME), ausencia de Content Security Policy (CSP) y endurecimiento adicional de CORS, uso de rate limiting en memoria (sin persistencia multi-worker), falta de validación de fortaleza de claves y controles de rotación operativa, y lagunas de compliance (cifrado en reposo por confirmar, auditoría incompleta, SLAs y pruebas DR no formalizadas).

Las implicaciones operativas y de cumplimiento son directas: exposición a ataques de replay y abuso de autenticación, escalamiento de privilegios por controles de acceso incompletos, riesgos de confidencialidad e integridad en datos geoespaciales sensibles, y potencial no conformidad con marcos HIPAA/NIST CSF/RMF e ISO 27001. Se requiere un plan de remediación priorizado para reducir la superficie de ataque, fortalecer la autenticación/autorización, consolidar trazabilidad y asegurar resiliencia 24/7.

Para enmarcar el estado inicial y su riesgo asociado, la siguiente matriz resume los hallazgos clave por categoría (A01–A10):

Tabla 1. Matriz de hallazgos OWASP Top 10 por categoría

| Categoría (A01–A10) | Descripción del hallazgo | Evidencia (indicativa) | Criticidad | Impacto | Acción prioritaria |
|---|---|---|---|---|---|
| A01 Broken Access Control | Roles y permisos granulares no plenamente definidos; checks de superuser básicos | Dependencias de auth y guards básicos | Alto | Acceso indebido a operaciones críticas | Diseñar/imponer RBAC/ABAC, least privilege |
| A02 Cryptographic Failures | Cifrado en reposo por confirmar; claves y secretos con validación insuficiente | Settings, variables de entorno (DB/JWT/Telegram) | Alto | Confidencialidad de PII/operativos | Validar/implementar cifrado at-rest; fortalezas de secretos |
| A03 Injection | Uso de asyncpg parametrizado reduce riesgo; PostGIS requiere revisión de consultas y permisos | Interacción con DB y geometrías | Medio | Fuga/corrosión de datos | Revisar queries geoespaciales y permisos PostGIS |
| A04 Insecure Design | Rate limiting en memoria; sin refresh tokens; falta CSP/CORS endurecido | Middleware, ausencia de refresh | Alto | Exposición a replay y abuso | Diseñar controles fuertes (refresh, Redis-backed limits) |
| A05 Security Misconfiguration | Redis sin TLS en prod por confirmar; CORS permisivo; placeholders CHANGEME | Config Redis, CORS; .env.example | Medio/Alto | Sustraer datos, MITM | Endurecer Redis TLS; CORS restrictivo; eliminar placeholders |
| A06 Vulnerable Components | Dependencias sujetas a CVEs; pipeline con pip-audit | CI/CD seguridad semanal | Medio | Explotación por CVEs | SBOM; actualizar; policy gating |
| A07 ID & Auth Failures | Sin refresh, expiración larga Telegram (7 días), falta jti/iat/nbf; sin revocación | JWT jose y auth endpoints | Alto | Replay, session hijacking | Implementar refresh; reducir expiración; jti/iat/nbf; revocación |
| A08 Software/Data Integrity | Auditoría parcial; integridad de flujos y migraciones no garantizada | Middleware logging; ausencia de evidencias de firma | Medio | Código/datos no confiables | Asegurar integridad CI/CD; migraciones versionadas |
| A09 Security Logging Failures | Logging existe; audit trail incompleto, sin retención formal | Middleware y eventos | Medio | Investigación deficiente | Catálogo de eventos; retención 1–3 años (op) y 6 años (políticas) |
| A10 SSRF | Integraciones externas (Telegram, Redis); controles de egress/allowlist no evidenciados | Webhook, llamadas externas | Medio | Exfiltración, abuso integraciones | Egress filtering, allowlists, validación estricta |

Las cinco recomendaciones de mayor impacto son:

1) Implementar refresh tokens y revocación de JWT con jti/iat/nbf, reduciendo ventanas de ataque y mejorando trazabilidad.
2) Endurecer Redis con TLS, consolidar CORS restrictivo por entorno, eliminar placeholders y validar fortaleza de secretos.
3) Fortalecer autorización con RBAC/ABAC y políticas de mínimo privilegio, asegurando separación de funciones y granularidad por operación.
4) Completar audit trail con catálogo de eventos, retención y correlación SIEM, para investigaciones y cumplimiento.
5) Formalizar SLAs 24/7, DR/RTO/RPO, y automatización PostGIS (CREATE EXTENSION e índices espaciales), mejorando resiliencia operacional.

La síntesis de dependencias críticas y su estado se resume a continuación.

Tabla 2. Resumen de dependencias críticas y estado de seguridad

| Dependencia | Versión (indicativa) | CVEs conocidos (estado) | Mitigaciones aplicadas | Acciones requeridas |
|---|---|---|---|---|
| python-jose[cryptography] | No confirmada | No especificados en evidencia | HS256, expiración configurable | Añadir jti/iat/nbf; refresh; revocación |
| asyncpg | No confirmada | No especificados en evidencia | Parametrización SQL | Evaluar upgrade; revisar PostGIS permisos |
| FastAPI | No confirmada | No especificados en evidencia | Middlewares de seguridad | Endurecer CORS; CSP; rate limiting Redis-backed |
| Redis | No confirmada | No especificados en evidencia | Uso para cache/PubSub | TLS; auth; limitar comandos; egress filtering |
| python-telegram-bot | No confirmada | No especificados en evidencia | Verificación de ID | Reducir expiración de tokens; validar origen |

Estado de cumplimiento con marcos clave:

Tabla 3. Estado de cumplimiento por marco (HIPAA/NIST CSF 2.0/RMF/ISO 27001)

| Marco | Situación actual | Brechas principales | Evidencia necesaria | Próximo paso |
|---|---|---|---|---|
| HIPAA Security Rule | Parcial | Cifrado at-rest por confirmar; auditoría incompleta; BAA/contratos | Pruebas de cifrado; catálogo de eventos; contratos | Pruebas y documentación; cierre de brechas |
| NIST CSF 2.0 | Parcial | Políticas y monitoreo avanzado; gobernanza y respuesta | Registro de riesgos; métricas SIEM | Fortalecer Govern/Detect/Respond |
| NIST RMF | Parcial | Clasificación y selección/implementación de controles | Categorización por impacto; POA&Ms | Seleccionar e implementar controles; autorización |
| ISO/IEC 27001:2022 | Parcial | Anexo A (A.8.15, A.8.21/24, A.8.11) | Política de logging; cifrado; DLP | Alinear SGSI y controles tecnológicos |

La producción y el repositorio se emplearon como evidencia directa[^1][^2]. Los marcos normativos citados sustentan criterios y expectativas técnicas[^3][^6][^5][^14].

## Metodología de Security Scanning Automatizado

La metodología de scanning se fundamenta en un enfoque dinámico, con ejecución en pipeline CI/CD y análisis de artefactos clave:

- Herramientas utilizadas:
  - bandit: análisis estático (SAST) de Python.
  - semgrep: patrones personalizados, detección de secretos y anti-patrones.
  - safety: librerías Python con vulnerabilidades conocidas.
  - pip-audit: auditoría de dependencias en CI/CD, programada semanalmente y bajo demanda.

- Alcance de escaneo:
  - Código del backend (FastAPI, servicios y routers).
  - Configuraciones de seguridad (CORS, middlewares, rate limiting).
  - Gestión de secretos (variables de entorno, settings).
  - Evidencias en repositorio y producción[^1][^2].

- Configuración del pipeline de seguridad:
  - Ejecución semanal (lunes medianoche UTC).
  - Ejecución en push a ramas principales y pull requests.
  - Reportes automatizados en JSON y Markdown.
  - Permisos para ejecución manual bajo demanda.

- Criterios de criticidad y falsos positivos:
  - Priorización por severidad técnica e impacto operativo.
  - Validación contextual para reducir falsos positivos.
  - Remediación basada en riesgo y compliance.

La siguiente tabla sintetiza la configuración por herramienta y su cobertura.

Tabla 4. Configuración de herramientas vs cobertura

| Herramienta | Tipo | Reglas/Perfiles | Archivos objetivo | Profundidad | Salida |
|---|---|---|---|---|---|
| bandit | SAST | Reglas Python estándar | Backend Python | Código estático | JSON/Markdown |
| semgrep | SAST/Patrones | Reglas genéricas + patrones secretos | Backend + config | Código + config | JSON/Markdown |
| safety | Dependencias | Vulnerabilidades Python | requirements/entorno | Dependencias instaladas | JSON/Markdown |
| pip-audit | Dependencias | CVEs Python | CI/CD pipeline | Auditoría semanal | JSON/Markdown |

Limitaciones y supuestos: no se dispone de confirmación de versiones exactas ni SBOM completos; los hallazgos en seguridad de aplicaciones deben complementarse con DAST en entornos de staging y pruebas manuales de endpoints críticos. La verificación de cifrado en reposo y de TLS extremo a extremo requiere pruebas adicionales.

## Gestión de secretos y variables de entorno

Las variables críticas incluyen secretos de JWT, tokens del bot de Telegram, credenciales de PostgreSQL/PostGIS y Redis, y parámetros de despliegue. La evidencia muestra placeholders “CHANGEME” y ausencia de validación de fortaleza en runtime, lo que aumenta el riesgo de mal configuración y exposición accidental.

Tabla 5. Inventario de variables críticas y controles

| Variable | Uso | Sensibilidad | Control actual | Riesgo | Acción requerida |
|---|---|---|---|---|---|
| SECRET_KEY / JWT_SECRET_KEY | Firma de JWT | Alta | Placeholders; sin validación | Alta | Validar fortaleza; rotación periódica |
| ACCESS_TOKEN_EXPIRE_MINUTES | Expiración access token | Media | Configurable | Media | Sincronizar cookies y token; definirrefresh |
| POSTGRES_PASSWORD | Conexión DB | Alta | Placeholder | Alta | Robustecer y rotar; cifrado en reposo |
| DATABASE_URL | Conexión asíncrona DB | Alta | No cifrado at-rest evidenciado | Alta | Validar cifrado at-rest; políticas de acceso |
| TELEGRAM_TOKEN | Bot Telegram | Alta | Placeholder | Alta | Rotación segura; control de origen |
| ADMIN_CHAT_ID | Administración | Media | Placeholder | Media | Validación y least privilege |
| REDIS_PASSWORD | Cache/PubSub | Alta | Sin TLS en prod por confirmar | Alta | Habilitar TLS; auth; listas de control |
| WS_HEARTBEAT_INTERVAL | WS scaling | Baja | Configurado | Baja | Mantener monitoreo y límites |
| ENVIRONMENT | Entorno | Media | Producción activo | Baja | Endurecer CORS/CSP según entorno |

Gestión de secretos: se recomienda integrar gestores de secretos (HashiCorp Vault o AWS Secrets Manager), configurar validación de fortaleza y rotación automatizada, y añadir health checks de secretos. Evitar la proliferación de variables duplicadas (SECRET_KEY vs JWT_SECRET_KEY), estandarizar naming y asegurar separación por entorno. Las consideraciones de cifrado en tránsito y reposo se alinean con ISO 27001 y HIPAA[^14][^6].

## Evaluación OWASP Top 10 (A01–A10) — Análisis profundo por categoría

La evaluación combina análisis técnico y alineación normativa. Para cada categoría, se presenta el control presente, el riesgo y la recomendación prioritaria, mapeando NIST CSF 2.0, RMF, ISO 27001 y, cuando aplica, exigencias DoD/FedRAMP.

### A01 Broken Access Control

Estado actual: existen guards y verificación de superuser, pero la matriz de permisos por operación (RBAC/ABAC) no está completamente definida. Se requiere granularidad por tarea y rol, separando funciones de operación, supervisión y administración, y limitando el acceso al mínimo necesario.

Tabla 6. Matriz de permisos RBAC/ABAC (propuesta)

| Rol | Operación | Permiso requerido | Evidencia de enforcement | Gap | Acción |
|---|---|---|---|---|---|
| Efectivo | Actualizar estado de tarea | scope: tareas:write (own) | Dependencias y guards básicos | Falta granularidad | Implementar claims/scopes, ownership checks |
| Operador | Crear/asignar tareas | role: operador | Verificación de rol | Falta segregación | Definir políticas ABAC por tarea |
| Supervisor | Aprobar/reasignar | role: supervisor | Guard de privilegios | Falta auditoría | Auditoría de decisiones de acceso |
| Administrador | Configuración sistema | role: admin + MFA | Check superuser | Riesgo de sobre-privilegio | Least privilege y separación de funciones |

Riesgo: acceso indebido a operaciones críticas. Recomendación: diseñar e implementar RBAC/ABAC con scopes por operación y ownership checks, reforzando controles en endpoints de creación/asignación de tareas. Alineado con NIST CSF 2.0 (Protect/Detect) y RMF (selección e implementación de controles)[^3][^5].

### A02 Cryptographic Failures

Evidencias indican uso de TLS en tránsito y explícitamente la desactivación de SSL para la base de datos en la red privada, lo que sugiere conectividad interna sin cifrado externo. No se confirma cifrado en reposo, y los secretos muestran placeholders con validación insuficiente.

Tabla 7. Mapa de cifrado

| Dato | En tránsito | En reposo | En uso | Control faltante | Recomendación |
|---|---|---|---|---|---|
| PII (DNI, telegram_id) | TLS | Por confirmar | No evidenciado | Cifrado at-rest | Implementar cifrado at-rest y en uso para campos críticos |
| Geodatos (geom) | TLS | Por confirmar | No evidenciado | Cifrado at-rest | Cifrado y permisos PostGIS |
| Credenciales DB | TLS interno | Por confirmar | No evidenciado | Rotación y cifrado | Rotación, cifrado y controles de acceso |
| Tokens JWT | TLS | N/A | Protección runtime | JTI/iat/nbf, revocación | Claims estándar y revocación |

Recomendación: confirmar e implementar cifrado en reposo (DB/disk) y en uso para campos sensibles; validar fortaleza y rotación de claves; fortalecer requisitos de cifrado conforme ISO 27001 y HIPAA[^14][^6][^7].

### A03 Injection

El uso de asyncpg y consultas parametrizadas reduce el riesgo de SQL injection. No obstante, las consultas PostGIS requieren revisión de permisos y buenas prácticas (e.g., operadores espaciales, funciones de distancia), dado el carácter sensible de geodatos.

Tabla 8. Riesgos PostGIS por operación

| Operación | Tipo de query | Riesgo | Permisos requeridos | Evidencia | Recomendación |
|---|---|---|---|---|---|
| Nearest neighbor | Operadores espaciales (ST_DWithin, ST_Distance) | Fuga de ubicaciones | SELECT restringido | Uso de geography | Revisar límites y anonimización |
| Inserciones geom | INSERT/UPDATE en geom | Corrupción de datos | INSERT/UPDATE controlado | Conexión parametrizada | Validación y auditoría de cambios |
| Consultas por radio | Agregaciones espaciales | Exposición masiva | SELECT por rol | Interacciones geoespaciales | Minimización y segmentación por rol |

Recomendación: auditar permisos PostGIS, validar tipos y proyecciones, y enmascarar resultados en interfaces. Alineado con ISO 27001 (A.8.3/A.8.24)[^14].

### A04 Insecure Design

Se identifican rate limiting en memoria sin persistencia entre workers, ausencia de refresh tokens, y falta de CSP/CORS endurecidos. La arquitectura debe adoptar controles fuertes por diseño, no como parches.

Tabla 9. Brechas de diseño vs controles objetivo

| Brecha | Riesgo | Control objetivo | Prioridad | Implementación |
|---|---|---|---|---|
| Rate limiting en memoria | Bypass y escalabilidad deficiente | Redis-backed rate limiting | Alta | Middleware Redis |
| Ausencia de refresh tokens | Re-autenticación forzada; replay | Refresh rotation + revocación | Crítica | Flujos OAuth2; storage seguro |
| CSP inexistente | XSS y injects | CSP restrictiva por UI | Media | CSP basada en whitelist |
| CORS permisivo | Exposición cross-origin | CORS por entorno, restrictivo | Alta | Matriz de configuración |

Recomendación: refactorizar middlewares y flujos de autenticación, consolidar límites y CSP por diseño. Sustentado por NIST CSF 2.0 (Protect) y guías DoD para APIs[^3][^13].

### A05 Security Misconfiguration

Evidencias muestran Redis sin TLS en configuración local y posibles comodines en CORS; además, placeholders de configuración (CHANGEME) persisten. Se debe reforzar Fly.io/Redis/PostGIS con endurecimiento sistemático.

Tabla 10. Checklist de endurecimiento por componente

| Componente | Config actual | Config endurecida | Riesgo mitigated | Prioridad |
|---|---|---|---|---|
| Fly.io | Variables por entorno | Secret manager + validación | Fuga de secretos | Alta |
| Redis | Sin TLS en local | TLS + auth + comandos | MITM/rogue access | Alta |
| PostgreSQL/PostGIS | Parametrizado | Permisos finos + auditoría | Exposición y corrupción | Alta |
| CORS | Permisivo | Orígenes específicos | Cross-origin abuse | Alta |
| CSP | Inexistente | Restrictivo | XSS/injects | Media |

Recomendación: adoptar TLS y auth en Redis, CORS/CSP endurecidos, eliminar comodines y placeholders. Alineado con NIST CSF 2.0 (Protect) e ISO A.8.21/24[^3][^14].

### A06 Vulnerable Components

El pipeline de seguridad con pip-audit sugiere cobertura básica contra CVEs, pero no se evidencian políticas de SBOM, gating y upgrades proactivos. Se requiere un programa de gestión de componentes.

Tabla 11. Catálogo de dependencias y posture

| Librería | Versión | CVEs | Estado | Acción |
|---|---|---|---|---|
| FastAPI | No confirmada | No especificados | Requiere validación | Actualizar y pin versión |
| asyncpg | No confirmada | No especificados | Requiere validación | Actualizar y revisar permisos |
| python-jose | No confirmada | No especificados | Requiere validación | Añadir claims estándar y refresh |
| python-telegram-bot | No confirmada | No especificados | Requiere validación | Reducir expiración y auditar integraciones |
| Redis | No confirmada | No especificados | Requiere validación | TLS y auth; revisar módulos |

Recomendación: generar SBOM, aplicar gating en CI/CD, y calendarizar upgrades y pruebas de regresión.

### A07 Identification and Authentication Failures

El sistema no implementa refresh tokens ni revocación, y los tokens del bot de Telegram expiran en siete días. Carece de claims estándar (iat, nbf, jti) y de listas de revocación. Esto incrementa la superficie de replay y hijacking.

Tabla 12. Hallazgos de JWT y plan de mejora

| Hallazgo | Riesgo | Recomendación | Prioridad |
|---|---|---|---|
| Sin refresh tokens | Re-autenticación frecuente; brute force | Implementar refresh rotation con almacenamiento seguro | Crítica |
| Expiración Telegram 7 días | Ventana larga de abuso | Reducir a ≤24h; auditar uso | Alta |
| Sin jti/iat/nbf | Replay y trazabilidad deficiente | Añadir claims; validación estricta | Alta |
| Sin revocación | Tokens comprometidos irreversibles | Revocation list (Redis) | Alta |

Alineado con NIST CSF 2.0 (Protect), DoD API guidance (autenticación robusta) y exigencias de MFA resistentes al phishing[^3][^13][^15].

### A08 Software and Data Integrity Failures

Las evidencias muestran auditoría parcial y ausencia de garantías explícitas de integridad en CI/CD y migraciones (versionado y firma). Esto eleva el riesgo de tampering y despliegues no confiables.

Tabla 13. Controles de integridad requeridos

| Artefacto | Control | Evidencia | Gap | Acción |
|---|---|---|---|---|
| Código | Firma y verificación | Pipeline CI | Sin firma | Implementar firmas y verificación |
| Migraciones | Versionado y checksum | Alembic/env | Sin firma | Checksums y auditoría |
| Artefactos contenedores | SBOM y firma | CI/CD | Parcial | SBOM; policy gating |

Recomendación: integridad en CI/CD, versionado y firma de migraciones. Alineado con NIST CSF 2.0 (Protect/Detect) y RMF[^3][^5].

### A09 Security Logging and Monitoring Failures

El sistema registra eventos y métricas, pero el audit trail carece de catálogo formal y retención definida (a nivel de aplicación y base de datos). La retención de políticas debe ser ≥6 años; los logs operativos 1–3 años, según sensibilidad[^6][^14][^16].

Tabla 14. Catálogo de eventos de auditoría y retención

| Evento | Campos mínimos | Retención | Responsable |
|---|---|---|---|
| Autenticación | actor, ip, timestamp, resultado | ≥6 años (políticas) | Seguridad/Cumplimiento |
| Asignación de tarea | actor, task_id, ubicación, timestamp | 1–3 años | Operaciones |
| Finalización de tarea | actor, task_id, evidencia (hash) | 1–3 años | Operaciones |
| Cambios de configuración | actor, параметры, timestamp | ≥6 años | Cumplimiento |
| Integraciones externas | tipo, destino, estado | 1–3 años | DevOps |

Recomendación: establecer catálogo y retención formal, correlación SIEM, y alertas sobre anomalías.

### A10 Server-Side Request Forgery (SSRF)

Las integraciones con Telegram y Redis requieren controles de egress filtering, allowlists y validación estricta de origen/destino para evitar exfiltración y abuso de integraciones.

Tabla 15. Superficie SSRF y controles

| Integración | Endpoint | Riesgo | Controles | Recomendación |
|---|---|---|---|---|
| Telegram Bot | Webhook | SSRF/abuso | Validación de origen | Allowlist + IP filtering |
| Redis | Pub/Sub | Exfiltración | Auth + TLS | Endurecer y segmentar |
| Monitoreo | Prometheus | Exposición | Segmentación | Restringir endpoints |

Recomendación: egress filtering y allowlists; verificación de identidad y permisos por integración. Alineado con NIST CSF 2.0 (Protect/Detect) y DoD API guidance[^3][^13].

## Vulnerability Assessment operativo (vectores de ataque y superficie)

La valoración operativa identifica vectores específicos contra el contexto gubernamental:

- Autenticación y sesiones: ausencia de refresh y revocación aumenta riesgo de replay y hijacking. La expiración larga en Telegram amplía la ventana de abuso.
- Datos sensibles: PII y geodatos requieren cifrado en reposo y permisos estrictos; la exposición accidental por vistas o logs debe mitigarse con DLP y enmascaramiento.
- Telegram Bot: validaciones de origen, whitelists de usuarios y rate limiting por comando son imprescindibles.
- PostGIS: operadores espaciales y permisos deben auditarse; se recomienda anonimización en consultas de proximidad y minimización de resultados.
- Redis: caching y PubSub deben operar con TLS y auth; comandos peligrosos deshabilitados; segmentación y egress filtering.
- WebSockets: autenticación en handshake, autorización por tópico, heartbeats y límites de conexiones; métricas y alertas ante degradaciones.

Tabla 16. Matriz de vectores de ataque vs controles

| Vector | Componente | Exposición | Impacto | Control existente | Control requerido |
|---|---|---|---|---|---|
| Replay/hijacking | JWT | Alto | Acceso indebido | Expiración básica | Refresh, revocación, jti/iat/nbf |
| Fuga de PII | DB | Medio/Alto | Privacidad | Parametrización | Cifrado at-rest; DLP |
| Abuso de comandos | Bot | Medio | Operaciones | Validación de ID | Whitelists; rate limiting |
| MITM | Redis | Alto | Datos | Sin TLS (local) | TLS; auth; comandos |
| XSS/injects | UI | Medio | Integridad | Headers básicos | CSP; sanitización |
| SSRF | Integraciones | Medio | Exfiltración | No evidenciado | Egress filtering; allowlists |

Estas evaluaciones se sustentan en NIST CSF 2.0, ISO 27001 y recomendaciones de privacidad (ICLG)[^3][^14][^17].

## Security Testing específico (penetration testing, API, WebSocket, Bot, DB)

El plan de pruebas se enfoca en endpoints críticos y degradación controlada.

- Penetration testing de endpoints críticos: /auth, /tareas, /ws, /telegram, con autenticación, autorización y rate limiting por tipo de servicio.
- API security testing: validación exhaustiva de parámetros, límites de tamaño, sanitización de inputs, y DLP en outputs.
- Telegram Bot security: pruebas de autenticación por ID, whitelists, rate limiting por comando y protección de mensajes.
- WebSocket security: autenticación en handshake, autorización por tópico, heartbeats, límites de conexiones y backpressure.
- Database security: configuración PostGIS, permisos de extensión, queries parametrizadas y auditoría de cambios.

Tabla 17. Plan de pruebas por endpoint/servicio

| Servicio | Caso de prueba | Herramienta | Criterio de éxito | Evidencia |
|---|---|---|---|---|
| Auth | Fuerza bruta/refresh | Script/SAST | Bloqueos y rotación | Logs y métricas |
| Tareas | RBAC por operación | Manual/API | Denegaciones correctas | Auditoría |
| WebSocket | Handshake/token | Client test | Rechazo sin token | Código 1008 |
| Bot | Comandos sensibles | Bot test | Whitelists activas | Logs por comando |
| DB/PostGIS | Operadores espaciales | SQL test | Permisos finos | Auditoría de cambios |

Las guías DoD para APIs fundamentan la robustez de autenticación/autorización y segmentación[^13].

## Compliance gubernamental (NIST CSF 2.0, DoD, FIPS 140-2, auditoría)

El mapa de cumplimiento se alinea con NIST CSF 2.0, RMF, ISO 27001, y exigencias de documentación y retención de políticas. La guía DoD en APIs refuerza controles técnicos en integraciones, y FedRAMP ofrece contexto de autorización para servicios cloud cuando aplique. Los requisitos de auditoría gubernamental exigen trazabilidad y correlación por campo y especificación[^3][^5][^14][^13][^12][^16].

Tabla 18. Matriz de cumplimiento: marco → control → evidencia → estado

| Marco | Control | Evidencia | Estado | Brecha | Acción |
|---|---|---|---|---|---|
| HIPAA | Seguridad de transmisión | TLS en canales | Parcial | At-rest por confirmar | Pruebas cifrado |
| NIST CSF | Identificación de activos | Inventario y riesgos | Parcial | Registro formal | Categorización |
| RMF | Selección de controles | POA&M | Parcial | Implementación | Plan de implementación |
| ISO 27001 | A.8.15 logging | Logs estructurados | Parcial | Retención definida | Catálogo y retención |
| DoD APIs | Autenticación/autorización | Guards/scopes | Parcial | MFA resistente | Fortalecer |
| FedRAMP | Authorization | Servicios cloud | Parcial | Alcance | Evaluar si aplica |

Brechas de información: confirmación de cifrado en reposo y en uso, validación TLS extremo a extremo, versión exacta de dependencias y SBOM completo, SLAs 24/7 con formalización, política de retención y auditoría a nivel DB, clasificación de datos y DLP, detalle de controles RBAC/ABAC por operación, inventario de integraciones con acuerdos de cumplimiento, y pruebas DR con RTO/RPO documentadas. Estas brechas se integran en el roadmap de cierre.

## Remediation roadmap y priorización operativa

La priorización se define por criticidad e impacto, con timelines y responsables claros.

Tabla 19. Plan de remediación priorizado

| Acción | Criticidad | Timeline | Responsable | Dependencias | KPI |
|---|---|---|---|---|---|
| Implementar refresh tokens y revocación (JWT) | Crítica | 0–30 días | Seguridad/Dev | Diseño claims; storage | % usuarios con refresh; tasa de revocación |
| Reducir expiración de tokens Telegram a ≤24h | Alta | 0–30 días | Dev/Bot | Actualización endpoints | Tiempo de expiración efectivo |
| Endurecer Redis (TLS, auth) y retirar ssl_cert_reqs=None | Alta | 30–90 días | Infra/DevOps | Configuración producción | % canales con TLS; 0 fallbacks |
| CORS restrictivo por entorno + CSP | Alta | 30–90 días | Dev | Matriz de configuración | 0 orígenes comodín; CSP activo |
| Validar/implementar cifrado en reposo (DB/disk) | Alta | 90–180 días | DBA/Infra | Evaluación técnica | Estado de cifrado confirmado |
| Audit trail completo (catálogo, retención, SIEM) | Alta | 90–180 días | Seguridad/Observability | Integración SIEM | % cobertura eventos; retención |
| RBAC/ABAC granular con scopes | Alta | 30–90 días | Seguridad/Dev | Claims/scopes | Denegaciones correctas |
| PostGIS: automatización de extensión e índices espaciales | Media | 30–90 días | DBA/Dev | Alembic/env | Extensión e índices presentes |
| DR: pruebas con RTO/RPO, calendarios y evidencias | Alta | 90–180 días | SRE/DBA | SLAs; backups | Éxito de pruebas; MTTR |

Se espera una mejora sustancial del security score y un cierre efectivo de vulnerabilidades críticas con la ejecución de este plan, consistente con RMF y NIST CSF 2.0[^5][^3].

## Anexos técnicos

Glosario de términos y evidencias referenciadas:

- PII: información personal identificable (DNI, telegram_id, etc.).
- RBAC/ABAC: control de acceso basado en roles/atributos.
- jti/iat/nbf: claims estándar de JWT (identificador, emitido en, no antes).
- CSP: Content Security Policy para prevenir XSS.
- WS: WebSocket; canal bidireccional persistente.
- SBOM: lista de materiales de software.

Evidencias clave:

- Endpoints de health y readiness observados en producción[^2].
- Catálogo de métricas de WebSockets (conexiones, mensajes, broadcasts, latencias) y eventos operacionales[^1].
- Consultas PostGIS (geography, operadores de distancia) y configuración de extensiones en flujo técnico[^1].

Plantillas:

- Política de clasificación de datos: guía para etiquetado, acceso mínimo y retención por sensibilidad.
- Procedimiento de auditoría: checklist de eventos, campos mínimos y correlación por IDs.

---

## Conclusiones y decisiones clave

El estado de seguridad actual muestra una base operativa robusta (middlewares, instrumentación, health checks) pero con brechas críticas en autenticación, trazabilidad, cifrado y endurecimiento de integraciones. La ausencia de refresh tokens y revocación, la expiración excesiva en Telegram, y la falta de CSP/CORS endurecidos son riesgos operativos y de cumplimiento que deben mitigarse de forma inmediata. El cierre de brechas de cifrado en reposo y en uso, la formalización de auditoría y retención, y la definición de SLAs y pruebas DR son esenciales para consolidar una postura acorde a marcos HIPAA/NIST CSF/RMF e ISO 27001.

Decisiones requeridas en 0–30 días: aprobar el diseño de refresh y revocación de JWT, reducir la expiración de tokens del bot a 24 horas, endurecer CORS/CSP, consolidar rate limiting Redis-backed y fortalecer la gestión de secretos (validación y rotación). En 30–90 días: ejecutar cifrado en reposo y auditoría avanzada; automatizar PostGIS y permisos; implementar RBAC/ABAC granular; y formalizar SLAs/DR con pruebas y evidencias. Con estas acciones, el sistema reducirá su superficie de ataque, mejorará la resiliencia y satisfacción de auditorías gubernamentales, y alcanzará niveles de confianza operativos acordes a su misión 24/7.

---

## Referencias

[^1]: GRUPO_GAD — Repositorio GitHub. https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD — Aplicación en Fly.io. https://grupo-gad.fly.dev  
[^3]: NIST Cybersecurity Framework 2.0 (CSWP-29). https://doi.org/10.6028/NIST.CSWP.29  
[^4]: Cybersecurity Framework | NIST (CSF 2.0). https://www.nist.gov/cyberframework  
[^5]: NIST Risk Management Framework (RMF). https://csrc.nist.gov/projects/risk-management  
[^6]: Summary of the HIPAA Security Rule - HHS.gov. https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html  
[^7]: HIPAA Security Rule to Strengthen the Cybersecurity of ePHI (NPRM 2025). https://www.federalregister.gov/documents/2025/01/06/2024-30983/hipaa-security-rule-to-strengthen-the-cybersecurity-of-electronic-protected-health-information  
[^11]: Data Encryption Requirements 2025 - Paperclip. https://paperclip.com/data-encryption-requirements-2025-why-data-in-use-protection-is-now-mandatory/  
[^12]: FedRAMP | FedRAMP.gov. https://www.fedramp.gov/  
[^13]: API Technical Guidance (DoD CTO, 2025). https://www.cto.mil/wp-content/uploads/2025/05/API-Tech-Guidance-MVCR-2-2025_0516-Cleared.pdf  
[^14]: Mastering ISO 27001 controls: 2025 guide - Thoropass. https://www.thoropass.com/blog/mastering-iso-27001-controls-your-2025-guide-to-information-security  
[^15]: S.4638 - National Defense Authorization Act for Fiscal Year 2025 (NDAA FY25). https://www.congress.gov/bill/118th-congress/senate-bill/4638/text  
[^16]: Data Reliability Audit Requirements - FY 2025 (ACF). https://acf.gov/css/policy-guidance/data-reliability-audit-requirements-fy-2025  
[^17]: Data Protection Laws and Regulations Report 2025: USA - ICLG. https://iclg.com/practice-areas/data-protection-laws-and-regulations/usa  
[^18]: 2025 National Interagency Standards for Resource Mobilization. https://www.nifc.gov/sites/default/files/NICC/3-Logistics/Reference%20Documents/Mob%20Guide/2025/2025%20NATIONAL%20INTERAGENCY%20STANDARDS%20for%20RESOURCE%20MOBILIZATION_Final_3-5.pdf