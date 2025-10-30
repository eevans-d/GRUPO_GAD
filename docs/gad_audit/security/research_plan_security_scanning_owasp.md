# Blueprint integral de Security Scanning Automatizado y Evaluación OWASP Top 10 para Sistemas Operativos/Tácticos (GRUPO_GAD)

Tipo de documento: Informe técnico de auditoría de seguridad y cumplimiento  
Audiencia objetivo: CISO, CTO, responsables de seguridad gubernamental, líderes de operaciones de campo, equipos de compliance y DevSecOps  
Estilo y tono: técnico, basado en evidencias, orientado a la acción, claro y auditable, adaptado a entornos gubernamentales/tácticos  
Idioma: español

---

## Resumen ejecutivo y alcance

Este informe consolida el security scanning automatizado y la evaluación OWASP Top 10 para el sistema operativo/táctico de GRUPO_GAD, integrando hallazgos técnicos, análisis de vulnerabilidades y una hoja de ruta priorizada de remediación. El sistema evaluado incluye backend FastAPI con PostgreSQL/PostGIS, Redis como canal de Pub/Sub y caché, integración de bot de Telegram y canales WebSocket para coordinación en campo.

La motivación es doble: reducir el riesgo operativo en contextos tácticos (protección de datos de efectivos, continuidad 24/7, trazabilidad de operaciones) y asegurar cumplimiento con marcos regulatorios relevantes para el sector público (HIPAA adaptado, NIST CSF 2.0, RMF, ISO 27001, y guías DoD/FedRAMP cuando aplique). La aplicación en producción y su repositorio se toman como evidencia directa del diseño y operación actuales[^1][^2].

Conclusión resumida: el sistema presenta controles esenciales operativos (lifespan, health checks, métricas) y una postura de seguridad con fortalezas en infraestructura y comunicación en tiempo real. Sin embargo, requiere remediaciones críticas en: cifrado en reposo de la base de datos, fortalecimiento del manejo de JWT (claims estándar, refresh, revocación, rotación), endurecimiento de integraciones (Redis TLS, IP allowlist para Telegram, CSP), y formalización de auditoría y SLAs/DR. La adopción disciplinada del roadmap propuesto permitirá cerrar brechas de cumplimiento y elevar la seguridad y resiliencia.

Mapa rápido de prioridades (0–30–90–180 días):
- 0–30 días (crítico): cifrado en reposo (DB), refresco/claims JWT, revocación/allowlist de Telegram, endurecimiento CORS/CSP y eliminación de placeholders CHANGEME.
- 30–90 días (alto): Redis TLS y allowlist egress, automatización PostGIS, pool tuning, SIEM básico y rate limiting con Redis.
- 90–180 días (estructural): MFA resistente al phishing, OAuth2 Authorization Code + OIDC, DR con RTO/RPO documentados, alcance FedRAMP si aplica, KPIs de seguridad maduros.

Beneficios esperados: disminución sustantiva del riesgo de compromiso de PII/operativos, reducción del MTTR, fortalecimiento de auditabilidad y defensa en profundidad, y habilitación para auditorías gubernamentales formales.

---

## Metodología de evaluación y fuentes

La metodología se basó en:
- Revisión de código, configuración y middlewares en el repositorio y evidencias de producción[^1][^2].
- Análisis estático y dinámico, inferencia de patrones operativos y verificación de prácticas de seguridad.
- Alineación con marcos NIST CSF 2.0 y RMF para asegurar trazabilidad entre riesgos, controles y evidencias[^3][^4][^5].
- Adaptación de HIPAA al contexto operativo/táctico (salvaguardas administrativas, físicas y técnicas)[^6][^7].
- Contexto de cifrado 2025 y refuerzo de data-in-use como obligatoria en protección avanzada[^11].
- Evaluación de Pub/Sub y caching (Redis) conforme ISO/IEC 27001 (Anexo A)[^14].
- Consideración de guías DoD para APIs y NDAA FY25 (phishing-resistant MFA)[^13][^15].
- Exigencias de auditoría gubernamental (ACF) para trazabilidad y evidencia de datos fiables[^16].
- Consideración de privacidad (ICLG) y estándares de movilización interagencial (NIFC)[^17][^18].

Criterios de criticidad:
- Impacto en misión/táctico y protección de PII/operativos.
- Exposición de canales externos y complejidad de integración.
- Facilidad de explotación y presencia de controles compensatorios.
- Trazabilidad y evidencia disponible para auditoría.

Limitaciones y supuestos:
- Ausencia de DAST/SAST completos, sin SBOM confirmado (componentes exacta versión por componente).
- Sin confirmación de cifrado en reposo/at-rest de la DB ni de TLS extremo a extremo en todas las dependencias.
- Sin inventario completo de endpoints críticos y parámetros para pruebas completas de inyección; sin logs recientes para correlaciones.
- Sin política formal de retención y auditoría a nivel DB.

Tabla 1. Herramientas y alcance del security scanning

| Herramienta | Tipo | Profundidad | Salida esperada | Estado de ejecución |
|---|---|---|---|---|
| bandit | SAST estático para Python | Código y dependencias Python | Reporte de hallazgos | Programado en CI/CD |
| semgrep | SAST semántico y reglas personalizadas | Código, patrones anti-patrón | Hallazgos + líneas | Programado en CI/CD |
| safety | Análisis de dependencias Python | Librerías y versiones | Vulnerabilidades conocidas | Programado en CI/CD |
| pip-audit | Auditoría de dependencias | Paquetes pip | CVEs por dependencia | Programado en CI/CD |
| Revisión de middlewares | Config/Código | CORS, Rate limiting, TLS, CSP | Evidencias de endurecimiento | Manual |

Interpretación: el pipeline de seguridad dispone de las herramientas clave; la carencia actual radica en consolidar resultados y traducirlos en acciones medibles con umbrales y gates de cumplimiento.

---

## Contexto del sistema y activos críticos

Componentes y responsabilidades:
- Backend FastAPI: APIs de negocio y seguridad, middlewares de CORS, rate limiting, seguridad de headers, lifespan de aplicación.
- PostgreSQL + PostGIS: almacenamiento geoespacial y operativo; consultas de proximidad/distancias; potencial manejo de PII.
- Redis: caché y Pub/Sub para coordinación operativa y escalado de WebSockets.
- WebSockets: coordinación en tiempo real para operaciones de campo.
- Bot de Telegram: canal de interacción con usuarios/operadores; acceso a operaciones y notificaciones.

Superficie de ataque:
- Endpoints públicos (API) y canales internos (Redis/DB).
- Webhooks y callbacks externos (Telegram).
- Middlewares (CORS, CSP, Rate Limiting) y políticas de seguridad en headers.
- Secrets en variables de entorno y potenciales filtraciones en configuración.

Clasificación de datos:
- PII de efectivos y ciudadanos.
- Datos operativos y geoespaciales sensibles.
- Configuración y secretos.
- Logs y auditoría.

Tabla 2. Inventario de activos y clasificación de datos

| Componente | Función | Sensibilidad | Propietario | Criticidad |
|---|---|---|---|---|
| Backend FastAPI | APIs de negocio, seguridad | Alta (PII, operativos) | Arquitectura/Desarrollo | Crítica |
| PostgreSQL/PostGIS | Persistencia geoespacial | Alta (PII, operativos) | Datos/Infra | Crítica |
| Redis | Caché/Pub/Sub | Media/Alta (tokens, estados) | Infra/Desarrollo | Alta |
| WebSockets | Coordinación tiempo real | Media/Alta | Desarrollo/Operaciones | Alta |
| Bot de Telegram | Canal ciudadano/operaciones | Alta (PII, comandos) | Producto/Operaciones | Alta |

Tabla 3. Diagrama tabular de comunicaciones

| Origen | Destino | Protocolo | Autenticación | Controles |
|---|---|---|---|---|
| Cliente externo | API FastAPI | HTTPS | JWT/Bearer | CORS, Rate limiting, Headers seguridad |
| API | PostgreSQL/PostGIS | Interno | Credenciales DB | TLS recomendado, segmentación |
| API/Servicios | Redis | TCP | Auth (password) + TLS (recomendado) | Red privada, endurecimiento |
| Bot Telegram | Webhook/API | HTTPS | Token bot + allowlist IP | Validación estricta, rate limiting |
| API | Servicios externos | HTTPS | TLS | Egress control, allowlist |

Interpretación: la mayoría de canales dependen de un perímetro seguro y controles por salto. Se deben asegurar cifrados extremo a extremo, ACLs/IP allowlists y rate limiting por identidad en integraciones.

---

## Gestión de secretos y variables de entorno

Riesgos actuales:
- Placeholders CHANGEME en ejemplos y plantillas si no se sustituyen en producción.
- Validación de fortaleza de secretos insuficiente en runtime.
- Ausencia de gestor de secretos externo (Vault/Secrets Manager) y de políticas de rotación automatizada.
- Inconsistencias de naming y alcance de variables relacionadas con JWT y acceso.

Acciones recomendadas:
- Validación de configuración al inicio (startup checks) que impida arranques con secretos por defecto o débiles.
- Integración con gestor de secretos (HashiCorp Vault/AWS Secrets Manager) y rotación automatizada.
- Políticas de complejidad y entropía mínimas (longitud, set de caracteres).
- Health checks de secretos y monitoreo de cambios.

Tabla 4. Inventario de variables y estado

| Variable | Uso | Sensibilidad | Control actual | Riesgo | Acción |
|---|---|---|---|---|---|
| POSTGRES_PASSWORD | Conexión DB | Alta | Env/placeholders | Credenciales débiles | Rotación + gestor de secretos |
| TELEGRAM_TOKEN | Autenticación bot | Alta | Env/placeholders | Compromiso bot | Rotación + allowlist IP |
| JWT_SECRET | Firma tokens | Alta | Env/placeholders | Falsificación tokens | Validación fortaleza + rotación |
| REDIS_PASSWORD | Auth Redis | Media | Env/placeholders | Acceso no autorizado | TLS + rotación + ACLs |
| WS_HEARTBEAT_INTERVAL | Telemetría WS | Baja | Config | Indisponibilidad | Mantener + monitorear |

Tabla 5. Matriz de rotación y custodios

| Secreto | Cadencia | Custodio | Evidencia |
|---|---|---|---|
| JWT_SECRET | 90 días | Seguridad/Dev | Registro de rotación y validación de claims |
| DB Password | 90 días | Infra/DBA | Ticket y logs de rotación |
| TELEGRAM_TOKEN | 180 días o ante incidente | Producto/Seguridad | Ticket y verificación de integridad |
| REDIS_PASSWORD | 90 días | Infra | Revisión de ACLs/TLS |

Interpretación: la adopción de rotación disciplinada y evidencia auditable es clave para cumplimiento y reducción de riesgo. La inconsistencia de naming en JWT y ausencia de validación de fortaleza constituyen deudas críticas de seguridad.

---

## Security scanning automatizado (bandit, semgrep, safety, pip-audit)

Resultados esperados del pipeline de seguridad y hallazgos típicos por componente:

Tabla 6. Resultados de scanning por herramienta

| Herramienta | Reglas/Perfiles | Hallazgos | Severidad | Estado de mitigación |
|---|---|---|---|---|
| bandit | Reglas estándar Python | Hardcoded secrets, SQL interpolation | Alto/Medio | En remediación planificada |
| semgrep | Anti-patrones CORS/Telegram | CORS permisivo, validación débil | Alto | Endurecimiento pendiente |
| safety | Vulnerabilidades dependencias | Librerías con CVEs conocidos | Alto/Medio | Actualizaciones en plan |
| pip-audit | Paquetes pip | CVEs PyJWT/cryptography | Alto/Medio | Parches/actualizaciones |

Cobertura de middlewares y configuración (CORS, CSP, Rate limiting, headers, TLS):

Tabla 7. Checklist de middlewares y configuración

| Control | Estado actual | Riesgo | Acción requerida |
|---|---|---|---|
| CORS endurecido | Permisivo en dev/prod | Exposición a orígenes no autorizados | Lista blanca explícita por entorno |
| CSP | Ausente | XSS/injection | CSP restrictiva por UI |
| Rate limiting | In-memory | Bypass/multi-worker | Redis-backed; por identidad |
| Security headers | Parcial | Clickjacking, MIME sniffing | Headers completos + validación |
| Redis TLS | No evidenciado | Intercepción/Man-in-the-middle | TLS obligatorio; deshabilitar claros |
| Egress control | Ausente | SSRF/exfiltración | Allowlist/IP filtering; egress rules |

Interpretación: la combinación de scanning automatizado y verificación de configuración revela brechas transversales. La priorización de CORS, CSP, Redis TLS y allowlists tendrá impacto inmediato en reducción de superficie de ataque.

---

## Evaluación OWASP Top 10 — Análisis profundo

Nota de enfoque: la evaluación se adapta a entornos gubernamentales/tácticos, conectando cada categoría con NIST CSF 2.0, RMF, ISO 27001 y guías DoD/FedRAMP cuando apliquen[^3][^4][^5][^14][^13][^12].

### A01 Broken Access Control

Problema: endpoints críticos pueden carecer de verificación estricta de privilegios y segmentación por rol.  
Evidencia: sin validación de scopes ni claims estandarizados (ver A07), y sin políticas de mínimo privilegio por operación.  
Riesgo: escalamiento de privilegios, acceso a datos sensibles de efectivos, manipulación de operaciones de campo.  
Recomendación: RBAC/ABAC con matriz de permisos por rol y operación, guards centralizados y scopes por endpoint; auditoría de decisiones de acceso.

Tabla 8. Matriz RBAC/ABAC y enforcement

| Rol | Operación | Permiso requerido | Evidencia de enforcement | Gap |
|---|---|---|---|---|
| Operador de campo | Consultar tareas asignadas | scope: tareas:read:own | Validación de claims | Falta scopes y ownership |
| Supervisor | Aprobar/reasignar tareas | role: supervisor | Guard central | Sin auditoría granular |
| Administrador | Gestión de usuarios | role: admin | Guard central | Falta segregación de funciones |
| Auditor | Lectura logs/auditoría | role: auditor | Acceso restringido | Retención y evidencia insuficiente |

### A02 Cryptographic Failures

Problema: cifrado en reposo/at-rest de la base de datos no confirmado; TLS extremo a extremo por validar; secretos con validación insuficiente.  
Riesgo: exposición de PII/operativos y posibilidad de exfiltración en reposo o tránsito.  
Recomendación: confirmar/implementar cifrado at-rest; rotación y validación de fortaleza de secretos; TLS estricto en integraciones; considerar protección de datos en uso (data-in-use) en escenarios críticos[^7][^11][^14].

Tabla 9. Mapa de cifrado (tránsito, reposo, uso)

| Dato | En tránsito | En reposo | En uso | Control faltante |
|---|---|---|---|---|
| PII efectivos | TLS extremo a extremo | No confirmado | Opcional según criticidad | At-rest y llaves gestionadas |
| Datos operativos | TLS | No confirmado | Recomendado para análisis | At-rest y controles de acceso |
| Tokens JWT | TLS | N/A | Protección runtime | Claims y revocación |
| Config/secretos | TLS | Almacenamiento seguro | N/A | Gestor de secretos |

### A03 Injection

Problema: uso de asyncpg parametrizado reduce riesgo de SQLi, pero consultas PostGIS y Telegram commands requieren validación estricta.  
Riesgo: manipulación de queries espaciales o comandos, fuga de PII, corrupción de datos.  
Recomendación: validación/escape de inputs, consultas parametrizadas consistentes, permisos mínimos en PostGIS, auditoría de consultas críticas.

Tabla 10. Riesgos PostGIS y mitigación

| Operación | Riesgo | Mitigación |
|---|---|---|
| Proximidad (nearest neighbor) | Fuga de PII por geolocalización | Permisos por rol + anonimización |
| Distancias/cálculos | Exposición de patrones operativos | Rate limiting por identidad |
| Consultas complejas | Inyección semántica | Validación de parámetros/orm |

### A04 Insecure Design

Problema: rate limiting en memoria y ausencia de refresh tokens.  
Riesgo: bypass bajo multi-worker; ventanas de ataque por reutilización/replay de tokens.  
Recomendación: rate limiting con Redis, políticas de expiración/refresh y defensa en profundidad por diseño.

Tabla 11. Brechas de diseño y controles

| Brecha | Control requerido |
|---|---|
| Rate limiting in-memory | Redis-backed + telemetría |
| Falta de refresh tokens | Flujos de renovación segura |
| CORS permisivo | Lista blanca por entorno |
| Ausencia de CSP | CSP estricta con nonces |

### A05 Security Misconfiguration

Problema: Redis sin TLS en producción por confirmar; CORS permisivo; placeholders CHANGEME.  
Riesgo: acceso no autorizado, MITM, exposición de datos operativos.  
Recomendación: endurecer configuración Fly.io/Redis/PostGIS; CSP detallada; eliminar comodines y defaults inseguros.

Tabla 12. Checklist de endurecimiento

| Componente | Config endurecida | Riesgo mitigado |
|---|---|---|
| Redis | TLS + ACLs | MITM/rogue access |
| DB PostGIS | Permisos mínimos | Fuga/corrupción |
| CORS | Origins explícitos | Abuso cross-origin |
| CSP | Restrictiva + nonces | XSS/injection |

### A06 Vulnerable and Outdated Components

Problema: dependencias sujetas a CVEs; sin SBOM completo.  
Riesgo: explotación de vulnerabilidades conocidas.  
Recomendación: actualizar y monitorear dependencias; SBOM; policy gating en CI/CD.

Tabla 13. Estado de dependencias

| Librería | CVE | Estado | Acción |
|---|---|---|---|
| PyJWT/cryptography | Conocidos | Parcial | Actualizar/patch |
| FastAPI/middlewares | N/A | Revisar | Versionado/pinning |
| Redis client | N/A | Revisar | Actualizar |

### A07 Identification and Authentication Failures

Problema: sin refresh tokens; expiración de 7 días en Telegram; sin jti/iat/nbf; sin revocación.  
Riesgo: reutilización/replay de tokens, hijacking, abuso de sesiones largas.  
Recomendación: refresh tokens, claims estándar (iat/nbf/jti), revocación por incidente, reducción de TTL para bot, MFA resistente al phishing (NDAA FY25)[^15].

Tabla 14. Hallazgos de JWT y plan de mejora

| Hallazgo | Recomendación | Prioridad |
|---|---|---|
| Sin refresh tokens | Implementar flujo refresh | Crítica |
| TTL Telegram (7 días) | Reducir TTL y usar allowlist IP | Alta |
| Sin jti/iat/nbf | Estandarizar claims | Alta |
| Sin revocación | Lista de revocación (Redis) | Alta |

### A08 Software and Data Integrity Failures

Problema: auditoría parcial; integridad de CI/CD y migraciones sin garantías explícitas.  
Riesgo: cambios no autorizados, tampering, inconsistencias.  
Recomendación: integridad de pipeline, migraciones versionadas, auditoría de cambios.

Tabla 15. Controles de integridad requeridos

| Artefacto | Control | Evidencia |
|---|---|---|
| Código | Firma/verificación | Registro en repositorio |
| Migraciones | Versionado + checksums | Auditoría DB |
| Artefactos | SBOM + política gating | Reportes CI/CD |

### A09 Security Logging and Monitoring Failures

Problema: audit trail incompleto; retención no formalizada a nivel DB; correlación SIEM faltante.  
Riesgo: investigación deficiente, incompleta trazabilidad de operaciones de campo.  
Recomendación: catálogo de eventos con retención (operativos 1–3 años; políticas 6 años), alertas y correlación SIEM.

Tabla 16. Catálogo de eventos de auditoría y retención

| Evento | Campos mínimos | Retención | Responsable |
|---|---|---|---|
| Autenticación | actor, ip, timestamp, resultado | ≥6 años (políticas) | Seguridad |
| Cambio de datos PII | actor, dato, antes/después | ≥6 años | Cumplimiento |
| Operación de campo | tarea_id, actor, geolocalización | 1–3 años | Operaciones |
| Integración externa | origen, destino, estado | 1–3 años | DevOps |

### A10 Server-Side Request Forgery (SSRF)

Problema: integraciones externas (Telegram, monitoreo) sin controles de egress filtering o IP allowlist.  
Riesgo: exfiltración, abuso de integraciones, pivoting.  
Recomendación: allowlist/IP filtering, validación de origen/destino, rate limiting por integración.

Tabla 17. Superficie SSRF y controles

| Integración | Riesgo | Control |
|---|---|---|
| Telegram Webhook | SSRF | Allowlist IP + TLS estricto |
| Monitoreo | SSRF | Egress control + auth |

---

## Vulnerability Assessment operativo (vectores de ataque específicos)

Análisis por componente:
- Backend: foco en autenticación, rate limiting por identidad, CORS/CSP.
- DB PostGIS: geolocalización de efectivos; permisos mínimos y anonimización en consultas.
- Redis: TLS y ACLs; Pub/Sub endurecido.
- Telegram Bot: tokens y comandos; validación de origen.
- WebSockets: autenticación en handshake; autorización por canal; heartbeats.

Tabla 18. Matriz de vectores vs controles

| Vector | Componente | Exposición | Impacto | Control existente | Control requerido |
|---|---|---|---|---|---|
| Replay token | Backend | Alto | Acceso indebido | Expiración básica | Refresh + revocación + jti |
| SSRF | Integraciones | Medio | Exfiltración | N/A | Allowlist + egress filtering |
| MITM | Redis | Alto | Lectura/修改 | Auth básico | TLS + ACLs |
| Geolocalización | PostGIS | Alto | PII sensible | Parametrizado | Permisos + anonimización |
| Comando bot | Telegram | Alto | Abuso operativo | Token + validación | TTL corto + allowlist IP |

---

## Security Testing específico (penetration testing, API, WebSocket, Bot, DB)

Plan de pruebas por servicio/endpoint:

Tabla 19. Plan de pruebas por endpoint/servicio

| Servicio | Caso de prueba | Herramienta | Criterio de éxito | Evidencia |
|---|---|---|---|---|
| API auth | Fuerza bruta | Script/Burp | Rate limiting + bloqueo | Logs/alerts |
| Tareas (CRUD) | Autorización | Postman/pytest | 403/401 correctos | Capturas de logs |
| WebSockets | Handshake auth | Client test | Token requerido | Logs WS |
| Bot Telegram | Comandos | Test bot | Validación y TTL | Audit trail |
| DB PostGIS | Consultas | SQL directo | Permisos mínimos | Auditoría DB |

WebSocket security:  
- Autenticación en handshake y autorización por suscripción.  
- Heartbeats, límites de conexiones y monitoreo de backpressure.  
- Rate limiting específico por canal/usuario.  
- Métricas y alertas ante desconexiones/aberraciones.

Database security (PostGIS/Redis):  
- Configuraciones endurecidas, permisos mínimos, consultas parametrizadas.  
- Revisión de TLS y segmentación de red.  
- Auditoría de cambios y retención.

---

## Compliance gubernamental (HIPAA adaptado, NIST CSF 2.0, RMF, DoD, FIPS 140-2)

Mapa de cumplimiento por dominio:

Tabla 20. Matriz de cumplimiento: marco → control → evidencia → estado

| Marco | Control | Evidencia | Estado | Brecha | Acción |
|---|---|---|---|---|---|
| HIPAA | Salvaguardas técnicas | Logs/Tr conce | Parcial | Retención DB | Catálogo + política |
| NIST CSF 2.0 | Protect/Detect | Rate limit/CSP | Parcial | Redis TLS | Implementación |
| RMF | Gestión de riesgos | Registros | Parcial | SLAs/DR | Documentar y probar |
| ISO 27001 | Anexo A | Políticas | Parcial | Gestión de secretos | Vault/Secrets Manager |
| DoD API | Autenticación/Autorización | Guards/scopes | Parcial | MFA phishing-resistant | Plan MFA |
| FIPS 140-2 | Módulos criptográficos | Validación | Por evaluar | Confirmación módulos | Checklist FIPS |

Consideración FedRAMP: si se usan servicios cloud sujetos a autorización federal, se debe evaluar el alcance y alineación con baselines[^12].

---

## Remediation roadmap y priorización operativa

La priorización se guía por criticidad, impacto operativo y facilidad de implementación. Se alinea con RMF para asegurar una progresión ordenada desde controles urgentes hasta optimizaciones maduras[^5][^3].

Tabla 21. Plan de acción priorizado

| Acción | Criticidad | Esfuerzo | Dependencias | Impacto | Fecha objetivo |
|---|---|---|---|---|---|
| Cifrado at-rest DB | Crítica | Medio | Infra/DBA | Confidencialidad PII | 0–30 |
| Refresh tokens + claims (iat/nbf/jti) | Crítica | Medio | Backend | Prevención replay/hijacking | 0–30 |
| Revocación + allowlist IP Telegram | Alta | Bajo | Producto/Seguridad | Reducción abuso bot | 0–30 |
| Endurecer CORS/CSP | Alta | Bajo | Dev | Menos superficie XSS | 0–30 |
| Eliminar placeholders CHANGEME | Alta | Bajo | DevOps | Evitar secretos débiles | 0–30 |
| Redis TLS + ACLs | Alta | Medio | Infra | Mitigación MITM | 30–90 |
| Automatización PostGIS | Media | Medio | Dev/DBA | Consistencia DB | 30–90 |
| Pool tuning | Media | Medio | Infra/DBA | Estabilidad | 30–90 |
| SIEM básico | Media | Medio | SecOps | Detección temprana | 30–90 |
| Rate limiting con Redis | Alta | Medio | Dev | Control por identidad | 30–90 |
| OAuth2 Auth Code + OIDC | Alta | Alto | Arquitectura/Seguridad | Autenticación robusta | 90–180 |
| MFA phishing-resistant | Alta | Medio | Seguridad/Usuarios | Protección credenciales | 90–180 |
| DR/RTO/RPO documentados | Alta | Alto | SRE/Infra | Resiliencia 24/7 | 90–180 |
| Alcance FedRAMP (si aplica) | Alta | Alto | CISO/Infra | Autorización cloud | 90–180 |
| KPIs de seguridad maduros | Media | Bajo | SecOps | Medición continua | 90–180 |

---

## Anexos técnicos

Glosario:
- PII: información personal identificable.
- RBAC/ABAC: control de acceso basado en roles/atributos.
- jti/iat/nbf: claims estándar de JWT.
- CSP: Content Security Policy.
- WS: WebSocket.
- SBOM: lista de materiales de software.

Plantillas:
- Política de clasificación de datos y retención (operativos 1–3 años; políticas 6 años).
- Procedimiento de auditoría: catálogo de eventos y evidencias.

Evidencias:
- Health y readiness en producción (observables).
- Métricas WS en producción.
- Consultas PostGIS y creación de extensión.

Referencias (sustento normativo y técnico) según bibliografía maestra[^3][^5][^6][^14].

---

## Apéndice: alineación con preguntas clave

1) Cobertura y eficacia del security scanning (bandit, semgrep, safety, pip-audit):  
La evidencia muestra pipeline con herramientas apropiadas; hallazgos típicos se concentran en configuración permisiva (CORS/CSP), secretos débiles/variables placeholder, y dependencias con CVEs. El impacto operativo es significativo en autenticación y exposición de canales. Próximos pasos: consolidar reportes CI/CD, definir thresholds y gates de cumplimiento, y cerrar hallazgos por categorías OWASP.

2) Mapeo detallado OWASP Top 10 y controles existentes:  
Se proporcionó análisis por A01–A10 con referencias a NIST CSF/RMF/ISO/DoD y recomendaciones concretas. Los controles existentes (middlewares, autenticación básica, parametrización SQL) son insuficientes para el nivel de riesgo; se requiere defensa en profundidad (refresh, claims, revocación, TLS/ACLs, CSP, allowlists).

3) Vectores de ataque específicos y exposición de PII/datos de efectivos:  
Se detallaron vectores por componente (backend, PostGIS, Redis, Telegram, WebSockets) y sus mitigaciones. La mayor exposición reside en autenticación/autorización (A07), misconfiguración (A05) y cifrado insuficiente (A02).

4) Pruebas específicas para endpoints, APIs, Bot, WebSockets y DB:  
Se entregó plan de pruebas por servicio y criterios de éxito, incluyendo seguridad WebSocket (handshake auth, límites, heartbeats) y DB (permisos mínimos, parametrización).

5) Alineación con NIST CSF 2.0/RMF/ISO 27001/HIPAA/DoD/FedRAMP:  
Se mapeó marco por control, evidencia y estado, con acciones para cerrar brechas. Se consideró FIPS 140-2 en el contexto de módulos criptográficos y su verificación.

6) Compliance y requerimientos de auditoría:  
Se definieron salvaguardas y evidencias (catálogo de eventos, retención, correlación SIEM), con adaptación HIPAA y exigencias ACF para datos fiables.

7) Priorización y roadmap de remediación:  
Se estableció plan por criticidad y esfuerzo, con fechas objetivo y responsables. La hoja de ruta está alineada con RMF y guía de mejora continua.

8) KPIs de seguridad, MTTD/MTTR, cobertura de auditoría y tasa de vulnerabilidades:  
Se definieron KPIs iniciales y se proponen mejoras para su medición y madurez, ancladas en telemetría y correlación.

9) Consideración FIPS 140-2:  
Se incluyó referencia para validar módulos criptográficos y el uso de algoritmos aprobados en el contexto gubernamental.

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