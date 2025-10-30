# Readiness integral para deployment gubernamental en Fly.io: configuración, seguridad, observabilidad, DR, compliance, automatización y costos

## Resumen ejecutivo y alcance del assessment

Este informe evalúa integralmente la preparación de GRUPO_GAD para operar en un entorno gubernamental sobre Fly.io, cubriendo diez dimensiones críticas: configuración de despliegue, seguridad y hardening, desempeño y escalabilidad, monitoreo y observabilidad, recuperación ante desastres y backups, cumplimiento regulatorio, infraestructura como código y automatización, optimización de costos, pruebas de despliegue/validación, y checklist de readiness para producción. El objetivo es habilitar una decisión de go/no-go basada en evidencias, con un roadmap priorizado que cierre brechas en un horizonte de 90 días.

La metodología se apoya en el análisis de los artefactos de auditoría interna (configuraciones críticas, observabilidad y monitoreo), la revisión de documentación oficial de Fly.io y su cumplimiento (SOC 2 Type 2, ISO 27001, HIPAA BAA, GDPR DPA), y el contraste con la plataforma de producción declarada (URL de referencia). Se aplicaron criterios de evaluación alineados a misión crítica pública: seguridad por defecto ( hardening, isolate-first, minimum exposure), trazabilidad y auditoría, alta disponibilidad y recuperación rápida, escalabilidad global multi-región, control de costos y gobierno de cambios, y cumplimiento regulatorio exigible[^1][^2].

Juicio global preliminar: existen bases sólidas —multi-stage Docker, usuario no-root, health checks y métricas expuestas, monitoreo gestionado con Prometheus/Grafana, red privada 6PN con WireGuard, TLS 1.2/1.3— pero persisten brechas críticas que impiden un go-live gubernamental sin mitigaciones. La priorización inmediata debe enfocarse en: (i) confirmar y alinear métricas de aplicación HTTP y WebSocket con las reglas de Prometheus; (ii) completar la cadena de notificaciones (Alertmanager + Slack/webhooks) con gestión de secretos formalizada; (iii) habilitar observabilidad del proxy (Caddy exporter) para visibilidad del perímetro; (iv) cerrar DR con procedimientos replicados, RPO/RTO validados y pruebas de restauración; (v) completar controles de compliance (auditoría, retención, data residency) y gobernanza de acceso; y (vi) optimizar costos en la transición a multi-región con autoscaling y control presupuestario.

Las recomendaciones se organizan en un plan 0–30/30–60/90 días. El hito 0–30 días habilita un despliegue seguro y observable con alertas confiables y dashboards mínimos viables; 30–60 días expande la superficie de observación, endurece umbrales y ejecuta pruebas de caos; 60–90 días institucionaliza SLO/SLI, automatización de runbooks, guardado de métricas a largo plazo y asegura DR con restauración probada. Este enfoque está alineado con la lista de verificación oficial para pasar a producción de Fly.io y los pilares de seguridad y resiliencia de la plataforma[^1][^2].

### Alcance y limitaciones

El assessment toma como insumo tres documentos internos: (i) configuraciones críticas del sistema (entornos, Dockerfile multi-stage, fly.toml, migraciones, observabilidad y CI/CD); (ii) auditoría de integración Prometheus/Grafana/Alertmanager (reglas, scraping, rutas e inhibiciones, dashboards); y (iii) auditoría del sistema de monitoreo (instrumentación ggrt_*, exporters, health checks y operación). Se asume despliegue en producción sobre Fly.io con health checks activos, exposición de métricas en puerto dedicado, región primaria definida, y red privada de la organización (6PN) disponible.

Limitaciones e información faltante: detalle completo de las 23 reglas de alertas (20 revisadas), confirmación de métricas HTTP instrumentadas en la API, dashboards JSON de Grafana para validar cobertura operativa, configuración final de Slack/webhooks y gestor de secretos de producción, habilitación y paneles del Caddy exporter, métricas del bot de Telegram, requisitos regulatorios específicos por jurisdicción (marcos aplicables), política de retención/almacenamiento largo plazo (Thanos/Cortex) en producción, y plan formal de escalado horizontal/federación de Prometheus. Estas brechas se reflejan como “information_gaps” y se incorporan en el plan de cierre[^1][^2].

---

## 1. Deployment Configuration Readiness

El archivo de configuración de Fly.io (fly.toml) es el plano de despliegue: define cómo se construye, ejecuta y monitorea la aplicación;管控a servicios HTTP/HTTPS, health checks, recursos de VM, estrategias de despliegue, variables de entorno y exposición de métricas. La configuración observada es consistente con producción: estrategia rolling, auto_rollback, health checks HTTP y TCP redundantes, puerto de métricas dedicado y recursos dimensionados para una aplicación web API con WebSocket. El modelo de configuración admite múltiples estrategias (rolling, immediate, canary, bluegreen), alineando seguridad y tiempo de inactividad con resiliencia operativa[^3][^4][^5].

A nivel de build, el Dockerfile implementa un diseño multi-stage con base slim, usuario no-root y health check, reforzando la seguridad del contenedor y evitando privilegios innecesarios. En runtime, la sección http_service fuerza HTTPS, controla concurrencia (soft/hard limits) y define timeouts; mientras que la sección metrics expone /metrics en puerto dedicado para scraping por el servicio gestionado de métricas de Fly.io (Prometheus compatible), con cadencia de 15 segundos[^3][^6].

Para ilustrar el estado actual frente a requisitos gubernamentales, el siguiente mapa contrasta configuraciones clave.

Tabla 1. Mapa fly.toml actual vs requisitos de producción gubernamental

| Elemento                     | Estado actual                                                                 | Requisito gubernamental                                          | Gap principal                                  | Acción recomendada                                                                                  |
|-----------------------------|--------------------------------------------------------------------------------|-------------------------------------------------------------------|------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| Estrategia de despliegue    | rolling con auto_rollback                                                      | Zero-downtime y rollback seguro                                   | Ninguno                                         | Mantener; documentar estrategia alternativa (immediate) por región para emergencia[^4][^5]          |
| Health checks               | HTTP (/health) y TCP redundantes, intervalo y grace period definidos           | Chequeos robustos que detengan despliegues defectuosos            | Ninguno                                         | Añadir machine_checks de integración por endpoint crítico[^4]                                       |
| http_service                | force_https, concurrency (soft/hard), idle_timeout                             | Fuerza HTTPS, límites y timeouts endurecidos                      | Ninguno                                         | Revisar h2_backend/gRPC si aplica; ajustar response_headers para seguridad                          |
| TLS                         | versiones 1.2/1.3 con cifrados fuertes                                          | TLS moderno, validaciones estrictas                               | Ninguno                                         | Confirmar validación de certificados (tls_server_name), deshabilitar default_self_signed[^7]        |
| Métricas personalizadas     | [[metrics]] puerto 9091, path /metrics                                         | Endpoint scrapeado cada 15s; etiquetas estables                   | Ninguno                                         | Validar cardinalidad y nombres; mantener scraping gestionado[^6]                                    |
| Recursos VM                 | CPU shared, RAM 512MB                                                          | Dimensionamiento para picos + swap                                | Potencial                                       | Ajustar size/cpumem; habilitar swap y snapshot automático[^3]                                       |
| Variables de entorno        | ENVIRONMENT, ALLOW_NO_DB, ASYNC_DB_SSL, WS_*                                   | Gestión de secretos y rotación                                    | Crítico                                         | Centralizar secretos (fly secrets) y rotación; segregación por entorno[^3][^1]                      |
| Primary region              | dfw                                                                            | Multi-región, réplica cercana a usuarios                          | Medio                                           | Planificar expansión a regiones adicionales (gru, iad, lhr) con réplica DB[^8][^9]                  |
| Certificados                | flyctl certs (gestión de certificados)                                         | Automatización y vigencia                                         | Ninguno                                         | Integrar issuance/renew automatizados; monitoreo de expiración[^10]                                 |

Interpretación: el baseline de despliegue es robusto. Las áreas de mejora se concentran en gestión de secretos y expansión multi-región. La incorporación de machine_checks y swap fortalecerá resiliencia y seguridad.

### 1.1 Dockerfile y multi-stage builds

El Dockerfile observado emplea un build multi-stage con una base slim, instala dependencias de producción (incluyendo drivers de PostgreSQL), ejecuta la aplicación con Uvicorn/uvloop y define un health check. El uso de usuario no-root reduce la superficie de ataque y cumple con el principio de mínimo privilegio. Buenas prácticas adicionales incluyen: fijar versiones pin enrequirements, minimizar capas (squash si procede), y asegurar reproducibilidad entre entornos. Recomendaciones: (i) validar el entrypoint y CMD para evitar ejecución con privilegios; (ii) aprovechar build_target para segmentar etapas test/prod; (iii) escanear vulnerabilidades en CI; y (iv) fijar umbrales de calidad de imagen antes de promoción[^3].

### 1.2 Health checks y estrategia de despliegue

La estrategia rolling habilita sustitución gradual de máquinas, con health checks que actúan como guardarraíles: si una nueva versión no responde correctamente, el despliegue se detiene o se activa auto_rollback. Se recomienda complementar con checks de integración (machine_checks) por endpoint crítico (por ejemplo, autenticación, lectura/escritura DB, WebSocket handshake) para capturar fallas de interacción y evitar promociones defectuosas[^4][^5].

### 1.3 TLS y certificados

Fly.io soporta TLS 1.2 y 1.3 con cifrados fuertes y ofrece terminación TLS en el edge. La configuración permite forzar HTTPS, fijar versiones y ALPN permitidos, y controlar headers de respuesta. flyctl certs centraliza la gestión de certificados ( issuance, renovación y asociación de dominios). Recomendaciones: (i) validar servidor TLS con tls_server_name en health checks HTTPS; (ii) deshabilitar default_self_signed; (iii) automatizar renovación y monitorizar expiración; y (iv) instrumentar métricas de handshake TLS y latencia del proxy para observabilidad del perímetro[^7][^10][^6].

---

## 2. Security Hardening Deployment

La plataforma incorpora seguridad por defecto: aislamiento de hardware (micro-VMs Firecracker), red privada 6PN sobre WireGuard, terminación TLS y denegación por defecto en redes públicas. Para producción gubernamental, el hardening debe centrarse en: (i) restringir exposición pública y segmentar servicios privados; (ii) reforzar control de acceso (SSO/MFA, least privilege, tokens de alcance mínimo); (iii) implementar auditoría y logging conforme a marcos de referencia; y (iv) proteger datos en tránsito y en reposo con cifrados modernos y volúmenes cifrados[^2][^11][^12][^13][^14].

Tabla 2. Matriz de controles de seguridad en Fly.io y evidencias requeridas

| Control                                      | Evidencia operativa                                          | Riesgo mitigado                                      |
|----------------------------------------------|---------------------------------------------------------------|------------------------------------------------------|
| Aislamiento de hardware (Firecracker)        | Documentación de plataforma y pruebas de neighbors           | Escape de contenedor/VM y cruce de inquilinos        |
| Red privada 6PN WireGuard                    | Diagrama 6PN, dominios .internal, reglas de aislamiento      | Exposición interna y eavesdropping                   |
| Terminación TLS en edge                      | Config TLS (versiones/ALPN), validación certificados         | Ataques MITM, cifrados débiles                       |
| Default-deny networking                       | Asignación de IPs y verificación de servicios privados       | Superficie pública no intencionada                   |
| SSO/MFA                                       | Configuración IdP, políticas de acceso y auditoría           | Compromiso de cuentas y acceso no autorizado         |
| Tokens con mínimos privilegios                | Inventario de tokens, scopes, rotación y revocación          | Uso indebido de credenciales                         |
| Volúmenes cifrados                            | Política de cifrado en reposo, gestión de claves             | Exfiltración de datos en almacenamiento              |
| Auditoría y trazabilidad                      | Logs exportados, retención y acceso controlado               | Falta de trazabilidad y forense                      |

Interpretación: la plataforma entrega controles robustos. El éxito gubernamental depende de evidencias documentales, políticas operativas y pruebas de efectividad (por ejemplo, aislamiento y exposición).

### 2.1 Controles de plataforma

Fly.io ejecuta aplicaciones en micro-VMs con aislamiento de memoria (Firecracker), con red privada 6PN que crea una malla WireGuard IPv6 por organización, y con terminación TLS en el edge. Estos controles reducen significativamente la probabilidad de incidentes por exposición indebida, cruce de inquilinos o ataques de red. En producción, deben complementarse con validaciones periódicas (por ejemplo, pruebas de routing privado y verificación de servicios privados sin IPs públicas)[^2][^12][^7].

### 2.2 Gobierno de acceso y secretos

El acceso a producción debe operar bajo SSO/MFA y principio de mínimo privilegio. Los secretos (JWT, DB, integraciones) deben residir en el gestor de secretos de Fly.io, con rotación calendarizada y segregación por entorno/organización. Recomendaciones: (i) inventariar tokens de acceso y limitar scopes por app y región; (ii) aplicar políticas de acceso a producción mediante organizaciones separadas para staging y producción; (iii) auditar cambios de configuración y despliegue; y (iv) habilitar alertas sobre uso de secretos y accesos privilegiados[^1][^11][^3].

### 2.3 Cifrado en tránsito y reposo

TLS 1.2/1.3 y volúmenes cifrados en reposo proporcionan protección por diseño. Para cumplimiento, se recomienda: (i) validar configuraciones TLS en health checks; (ii) documentar la política de cifrado de volúmenes; (iii) habilitar HSTS en el edge si aplica; y (iv) registrar eventos de handshake TLS y errores para detección temprana de problemas del perímetro[^7][^14].

---

## 3. Performance y Scalability Deployment

La escalabilidad en Fly.io se logra mediante balanceo global, autoscaling y distribución multi-región. Fly Proxy rutea solicitudes combinando cercanía (RTT), concurrencia y límites de la aplicación; el autoscaler ajusta el número de máquinas activas en función de tráfico o métricas; y la selección de regiones permite atender usuarios en múltiples geographies con latencias consistentes[^15][^16][^8].

Tabla 3. Comparativa de estrategias de autoscaling

| Estrategia               | Descripción                                              | Escenario recomendado                                | Riesgos/consideraciones                       |
|-------------------------|----------------------------------------------------------|------------------------------------------------------|-----------------------------------------------|
| Autostop/Autostart      | Detener/arrancar Machines según demanda                  | Ahorro en horarios de baja demanda                   | Arranque en frío puede aumentar latencias      |
| Autoscaling por métrica | Escalar según métricas personalizadas (Prometheus)       | Servicios con patrones no web y colas/throughput     | Requiere instrumentación fiable                |
| Scale by region         | Ajustar count por región                                 | Multi-región con tráfico heterogéneo                 | Complejidad operativa y consistencia de datos  |
| Manual scaling          | Ajuste explícito de count/size                           | Estabilización y control fino en picos predecibles   | Menor elasticidad y riesgo de sobre/infra      |

Interpretación: combinar autostop/autostart con autoscaling por métrica entrega elasticidad y ahorro, siempre que la instrumentación de métricas (incluida la de aplicación) sea confiable[^16].

Tabla 4. Inventario de regiones relevantes y uso recomendado

| Código | Región                     | Uso recomendado                                         |
|--------|----------------------------|---------------------------------------------------------|
| dfw    | Dallas (US)                | Primaria regional, latencia centro América              |
| gru    | São Paulo (Brasil)         | Residencia/servicio Brasil, cercanía usuarios           |
| iad    | Ashburn (US)               | Este de EE.UU., redundancia y DR                        |
| lhr    | Londres (UK)               | EMEA, cercanía usuarios europeos                        |
| lax    | Los Ángeles (US)           | Oeste de EE.UU./Pacífico, baja latencia                 |
| sjc    | San José (US)              | Silicon Valley, cercanía tech ecosystem                 |

Interpretación: la estrategia multi-región debe equilibrar cercanía a usuarios, residencia de datos y replicación/consistencia de la base. PostGIS sugiere patrones de primary/replica por región con replay para consistencia eventual[^9][^8].

### 3.1 Balanceo de carga y concurrencia

El balanceo usa concurrencia y cercanía para distribuir tráfico. La aplicación debe definir soft/hard limits coherentes y probar comportamiento bajo carga, evitando sobrecarga por colas o saturación de hilos. Se recomienda: (i) instrumentar métricas de colas y latencias; (ii) habilitar circuit breakers; (iii) ajustar timeouts y retransmisiones; y (iv) validar backpressure en WebSocket[^15].

### 3.2 Autoscaling y multi-región

Para servicios web, autostop/autostart reduce costos fuera de horas; para cargas no web, autoscaling por métrica permite escalar en función de indicadores como tamaño de cola o throughput. Multi-región exige diseño de consistencia y réplica: primary por región y replay de sesiones/consultas según el patrón de lectura/escritura del servicio[^16][^9].

---

## 4. Monitoring y Observabilidad Deployment

Fly.io ofrece métricas gestionadas compatibles con Prometheus, basadas en VictoriaMetrics, y Grafana gestionado. La plataforma expone métricas nativas del proxy (fly_edge_/fly_app_), de instancias (fly_instance_), de volúmenes (fly_volume_) y de Postgres (pg_), además de scrappear métricas personalizadas de la aplicación cada 15 segundos. Integraciones de Sentry y logging están disponibles. Para operación 24/7, el diseño debe asegurar cobertura de exporters clave, dashboards validados, enrutamiento de alertas y políticas de retención/almacenamiento extendida[^6][^17].

Tabla 5. Inventario de scraping targets y roles

| Job            | Endpoint                            | Intervalo | Etiquetas                              |
|----------------|-------------------------------------|-----------|----------------------------------------|
| api            | API: Puerto de métricas /metrics    | 15s       | service=fastapi; component=api         |
| prometheus     | Prometheus: 9090                    | 15s       | service=prometheus                     |
| alertmanager   | Alertmanager: 9093                  | 15s       | service=alertmanager; component=alerting |
| postgres       | postgres-exporter: 9187             | 15s       | service=postgresql; component=database |
| redis          | redis-exporter: 9121                | 15s       | service=redis; component=cache         |
| node           | node-exporter: 9100                 | 15s       | service=node-exporter; component=infrastructure |
| caddy (propuesto) | caddy-exporter: 9180            | 15s       | service=caddy; component=reverse-proxy |

Interpretación: habilitar el Caddy exporter cerrará la brecha del perímetro, ofreciendo visibilidad de latencia y throughput del proxy. Sin él, el triage de degradaciones en el edge queda incompleto[^6].

Tabla 6. Servicios de métricas y retención

| Servicio                  | Soporte API                   | Frecuencia scrape personalizada | Etiquetas estándar             | Retención extendida            |
|---------------------------|-------------------------------|---------------------------------|--------------------------------|-------------------------------|
| Prometheus gestionado     | Mayoría de /api/v1/query, /federate | 15s                              | app, region, host, instance    | Requiere Thanos/Cortex        |
| Métricas nativas (fly_*)  | No aplica (exposición nativa) | No aplica                        | región e instancia             | Corto plazo (integrado)       |
| Postgres (pg_)            | Exporter estándar             | 15s                              | Servicio/componente            | Exportado a Prometheus        |

Interpretación: para cumplimiento y auditoría, se requiere almacenamiento a largo plazo con Thanos o Cortex, que habilita retención extendida, federación multi-Prometheus y consulta global[^18][^19].

### 4.1 Métricas personalizadas y catálogo ggrt_*

La instrumentación WebSocket con prefijo ggrt_* cubre conexiones activas, totales, mensajes enviados, broadcasts, errores de envío, heartbeat y latencia. Para alertas de API, es imprescindible instrumentar métricas HTTP (http_requests_total, histogramas de duración por endpoint y status). Se debe evitar alta cardinalidad en etiquetas y estandarizar nombres y unidades.

Tabla 7. Catálogo de métricas ggrt_* (propósito y funciones)

| Nombre                          | Tipo      | Etiquetas | Propósito                                      |
|---------------------------------|-----------|-----------|------------------------------------------------|
| ggrt_active_connections         | Gauge     | env       | Conexiones activas                             |
| ggrt_connections_total          | Counter   | env       | Total de conexiones históricas                 |
| ggrt_messages_sent_total        | Counter   | env       | Mensajes enviados                              |
| ggrt_broadcasts_total           | Counter   | env       | Broadcasts realizados                          |
| ggrt_send_errors_total          | Counter   | env       | Errores de envío                               |
| ggrt_heartbeat_last_timestamp   | Gauge     | env       | Timestamp de último heartbeat                  |
| ggrt_role_connections           | Gauge     | env,role  | Conexiones por rol                             |
| ggrt_user_active                | Gauge     | env       | Usuarios únicos con conexión activa            |
| ggrt_message_latency_seconds    | Histogram | env       | Latencia de mensajes                           |

Interpretación: la cobertura es adecuada para operación de tiempo real; la alineación de nombres y exposición con reglas evitará alertas huérfanas[^6].

### 4.2 Alerting y runbooks

La configuración de Alertmanager debe definir rutas por severidad y componente, receivers efectivos (email/Slack), agrupación e inhibiciones que reduzcan ruido. La eficacia depende de completar integraciones (Slack/webhooks) con secretos gestionados y de estandarizar plantillas y runbooks.

Tabla 8. Rutas y receivers de Alertmanager

| Route/Match                | Receiver         | Severidad/Componente | Tiempos (group_wait/repeat) |
|---------------------------|------------------|----------------------|-----------------------------|
| severity=critical         | critical-alerts  | critical             | 0s / 1h                     |
| severity=warning          | warning-alerts   | warning              | 30s / 4h                    |
| component=database        | database-team    | cualquier severidad | default                     |
| component=api             | api-team         | cualquier severidad | default                     |
| default                   | default-receiver | cualquier severidad | 10s / 4h                    |

Interpretación: la estructura es sólida; completar credenciales y validar notificación cerrará el riesgo de fallos en incidentes. Inhibiciones clave (por ejemplo, APIDown inhibiendo latencias) mejorarán señal/ruido[^20].

Tabla 9. Reglas de inhibición propuestas

| Fuente                                           | Target                               | equal    |
|--------------------------------------------------|--------------------------------------|----------|
| severity=critical, alertname=APIDown             | severity=warning, component=api      | instance |
| severity=critical, alertname=InstanceDown        | severity=warning (cualquier alerta)  | instance |

Interpretación: las inhibiciones propuestas reducen redundancia y previenen fatiga de alertas, facilitando triage y escalación[^20].

---

## 5. Disaster Recovery y Backup

Fly.io habilita snapshots diarias automáticas de volúmenes, con retención por defecto de 5 días, y capacidades de DR con LiteFS/LiteFS Cloud para bases de datos distribuidas. Un plan robusto combina snapshots con backups lógicos/export offsite, réplicas por región y restauración ensayada, alineado a objetivos RPO/RTO definidos por dominio de servicio[^21][^22][^23].

Tabla 10. Plan de DR por componente

| Componente         | Backup                       | Réplica                        | Restore                       | Prueba                    | RPO/RTO objetivo                 |
|--------------------|------------------------------|--------------------------------|-------------------------------|---------------------------|----------------------------------|
| API/App            | Imágenes versionadas         | Multi-región (machines)        | Redeploy de imagen previa     | Ejercicio por región      | RPO: 0–15m / RTO: <15m           |
| PostgreSQL/PostGIS | Snapshots + export (LiteFS)  | Replica por región             | Restauración desde snapshot   | Restore en entorno de prueba | RPO: ≤15m / RTO: <60m          |
| Volúmenes          | Snapshots diarias            | Extensión automática           | Restore de volumen            | Validación de integridad  | RPO: 24h / RTO: <60m             |
| Redis              | Config + datos (si persiste) | Replica gestionada             | Rehidratación                 | Prueba de conmutación     | RPO: ≤5m / RTO: <30m             |
| Configuración      | Control de versiones         | N/A                            | Recuperación de config        | Revisión de diffs         | RPO: 0 / RTO: inmediato          |

Interpretación: combinar snapshots con DR de LiteFS y réplicas por región cubre escenarios de fallas de host y corrupción de datos. La clave es practicar la restauración y medir tiempos reales, ajustando thresholds[^21][^22][^23].

### 5.1 Procedimientos y pruebas

Los procedimientos deben documentar: (i) restauración de volúmenes; (ii) conmutación por región (regional failover) con pruebas controladas; y (iii) validación de integridad post-restore (checksum, lectura/escritura, migraciones). Se recomienda un calendario de ejercicios trimestrales, con reporte y remediación de hallazgos[^21].

---

## 6. Compliance y Requisitos Gubernamentales

Fly.io opera bajo un marco de seguridad y cumplimiento auditable: informe SOC 2 Type 2, centros de datos con certificación ISO 27001, acuerdos BAA para HIPAA y DPA para GDPR. La plataforma ofrece SSO/MFA, aislamiento por organización, red privada WireGuard, y seguridad de plataforma documentada. Para despliegue gubernamental, se requiere mapear controles a marcos aplicables, definir auditoría y retención de logs/métricas, y demostrar gobernanza de acceso y residencia de datos por región[^24][^11][^2][^25].

Tabla 11. Matriz de marcos vs controles

| Marco        | Control/Evidencia                                 | Estado       | Acción                                                                 |
|--------------|----------------------------------------------------|--------------|-------------------------------------------------------------------------|
| SOC 2        | Informe independiente, controles de seguridad      | Disponible   | Solicitar y archivar informe; mapping de controles operativos[^24]      |
| ISO 27001    | Datacenters certificados                           | Disponible   | Confirmar localización y alcance; documentar residencia[^24]            |
| HIPAA        | BAA pre-firmado                                   | Disponible   | Firmar BAA; validar cifrado en reposo y en tránsito; logging[^25]       |
| GDPR         | DPA pre-firmado                                   | Disponible   | Firmar DPA; documentar retención y derechos del titular[^11]            |

Interpretación: el cumplimiento de plataforma facilita autorización del servicio. La implementación debe completar evidencias de operación (auditoría, retención y residencia) y gobierno de acceso (SSO/MFA, least privilege).

### 6.1 Auditoría y retención

Las políticas de retención deben cubrir métricas operativas, logs de auditoría y alertas, equilibrando análisis histórico, costos y marcos regulatorios. Para almacenamiento extendido, Thanos/Cortex permiten retención de 12–24 meses y consulta global[^18][^19].

Tabla 12. Políticas de retención por tipo de dato

| Tipo de dato           | Retención propuesta        | Marco de referencia                   |
|------------------------|----------------------------|---------------------------------------|
| Métricas operativas    | 12–24 meses (objeto)       | ISO 27001, mejores prácticas          |
| Logs de auditoría      | 12–36 meses (según marco)  | SOC 2, GDPR                           |
| Alertas                | 12–24 meses                | Trazabilidad y compliance interno     |

Interpretación: la retención debe ser aprobada por el órgano de compliance y reflejarse en contratos y documentación de seguridad.

---

## 7. Infrastructure as Code y Automatización

Fly.io soporta automatización sin Terraform (blueprints oficiales), monorepo y multi-entorno, y revisión apps efímeras por PR. Las pipelines CI/CD deben integrar seguridad (SAST/DAST, escaneo de contenedores), promoción controlada, y despliegue continuo con validaciones. La gestión multi-entorno requiere aislamiento por organización y control de acceso estricto[^26][^27][^1][^28].

Tabla 13. Pipeline CI/CD propuesto

| Etapa            | Herramienta/Práctica                  | Control de seguridad                | Evidencia                         |
|------------------|---------------------------------------|-------------------------------------|-----------------------------------|
| Build            | Docker multi-stage                    | Escaneo de vulnerabilidades         | Reporte de escaneo                |
| Test             | Unit/Integration/Contract             | Calidad y cobertura                 | Reporte de pruebas                |
| Security         | SAST/DAST                             | Políticas de gates                  | Informe de hallazgos              |
| Deploy (Staging) | flyctl deploy + health checks         | Validaciones y machine_checks       | Logs de despliegue                |
| Promote (Prod)   | GitHub Actions + flyctl               | Revisión y aprobación               | Registro de cambios               |
| Rollback         | fly deploy --image <prev>             | Ejercicio y runbook                 | Resultado de rollback             |

Interpretación: la automatización reduce errores humanos y asegura consistencia. El rollback debe practicarse periódicamente para reducir MTTR[^26][^28].

### 7.1 Gestión de secretos en CI/CD

Los secretos se inyectan en CI/CD con scopes mínimos y rotación periódica; los pipelines validan integridad y restringen exposición (por ejemplo, no persistir secretos en logs). La segregación por organización y entorno garantiza que sólo roles autorizados accedan a producción[^1][^11].

---

## 8. Cost Optimization y Resource Management

Fly.io emplea un modelo de facturación basado en uso, prorrateado por tiempo de provisión de recursos, con planes de autoscaling para optimizar costos. La herramienta de cálculo de precios ayuda a estimar escenarios; la gestión presupuestaria recomienda fijar un baseline “always-on” y activar autostop/autostart y autoscaling por métrica en cargas variables[^29][^30][^31][^16].

Tabla 14. Modelo de costos (estructura y sensibilidad)

| Componente         | Base de cálculo                   | Sensibilidad                                   | Optimización recomendada                    |
|--------------------|-----------------------------------|------------------------------------------------|---------------------------------------------|
| Compute (Machines) | vCPU/RAM preset, horas activas    | Tráfico, picos, regiones                       | Autostop/autostart, ajuste de size          |
| Volúmenes          | Tamaño GB, snapshots               | Retención, crecimiento                         | Retención optimizada, auto-extend           |
| Bandwidth          | egress/ingress                     | Multi-región, CDN                              | Compresión, caching                         |
| Métricas           | Servicio gestionado                | Retención, cardinalidad                        | Downsampling, agregación                    |
| Soporte            | Plan seleccionado                  | SLA requerido                                   | Evaluar Standard/Premium/Enterprise         |

Interpretación: las palancas de ahorro más efectivas son la elasticidad (autostop/autoscale) y el ajuste de tamaño/región, con visibilidad mediante métricas de costo y uso[^29][^31].

### 8.1 Budget y alertas de costos

Se recomienda establecer presupuestos por organización y alertas por umbral de gasto, con paneles de uso y reportes mensuales. Las acciones de ahorro incluyen downsize, autostop/autostart, y consolidación de regiones según patrones de tráfico[^31].

---

## 9. Deployment Testing y Validation

Las pruebas de despliegue deben cubrir integración y salud de endpoints, performance bajo carga en producción, seguridad (SAST/DAST, escaneo de contenedores), y UAT con trazabilidad. Los gatekeepers de despliegue incluyen health checks y machine_checks que detienen promociones defectuosas. El rollback se practica redeployando una imagen previa y usando estrategias por región para minimizar impacto[^4][^5][^32].

Tabla 15. Plan de pruebas por tipo

| Tipo                 | Objetivo                           | Métrica                   | Herramienta         | Criterio de aceptación             |
|----------------------|------------------------------------|---------------------------|---------------------|------------------------------------|
| Integración          | Salud de endpoints críticos        | % éxito, latencia         | machine_checks      | ≥99.9% éxito en ventana            |
| Performance          | Latencias P95/P99 bajo carga       | P95/P99, throughput       | Pruebas sintéticas  | P95 ≤ 500ms, P99 ≤ 2s              |
| Seguridad            | Vulnerabilidades y cumplimiento    | Hallazgos críticos        | SAST/DAST           | 0 hallazgos críticos               |
| Contenedores         | Imagen segura y pin de dependencias| CVEs, políticas           | Escaneo imágenes    | Sin CVEs altos; dependencias pin   |
| UAT                  | Validación funcional               | Casos de uso              | scripts/tests       | 100% casos críticos aprobados      |
| Rollback             | Restauración de imagen previa      | RTO                      | fly deploy --image  | RTO < 15m; sin pérdida de datos    |

Interpretación: la combinación de gatekeepers técnicos y validación operativa reduce riesgo de incidentes y acelera recuperación[^5][^32].

### 9.1 Pruebas de resiliencia

Ejercicios de caos, fallos de dependencias (Redis/DB) y conmutación por región deben ejecutarse de forma controlada, con métricas de recuperación y runbooks adjuntos. La instrumentación de métricas y alertas es clave para observar el comportamiento durante estas pruebas y derivar mejoras de arquitectura[^33].

---

## 10. Checklist de Deployment Gubernamental

La siguiente lista sintetiza los requisitos de readiness con estado y evidencia requerida.

Tabla 16. Checklist de readiness (Go/No-Go)

| Categoría          | Requisito                                           | Estado       | Evidencia                             | Responsable | Fecha objetivo |
|--------------------|------------------------------------------------------|--------------|----------------------------------------|-------------|----------------|
| Seguridad          | SSO/MFA, least privilege, tokens mínimos             | Parcial      | Políticas y auditoría de accesos       | SecOps      | 30 días        |
| Seguridad          | Gestión de secretos centralizada y rotación          | Parcial      | Inventario y rotación de secretos      | DevOps      | 30 días        |
| Seguridad          | Default-deny networking y servicios privados         | Parcial      | Inventario de IPs y verificación 6PN   | NetOps      | 15 días        |
| Networking         | TLS 1.2/1.3, validación certificados                 | Parcial      | Config TLS y health checks HTTPS       | NetOps      | 15 días        |
| Datos              | Cifrado en reposo (volúmenes)                        | Parcial      | Política de cifrado y volúmenes        | SecOps      | 30 días        |
| DR                 | Plan de DR con restauración probada                  | Parcial      | Resultados de ejercicios de restore    | SRE         | 60 días        |
| Observabilidad     | Métricas HTTP y ggrt_* alineadas con reglas          | Crítico      | Reglas y scraping validados            | Backend     | 15 días        |
| Observabilidad     | Dashboards mínimos viables                           | Crítico      | JSON de paneles y revisión técnica     | SRE         | 30 días        |
| Observabilidad     | Caddy exporter y panel de proxy                      | Medio        | Job y dashboard habilitado             | SRE         | 30 días        |
| Alertas            | Slack/webhooks y plantillas estandarizadas           | Crítico      | Prueba de entrega y runbooks           | SRE         | 30 días        |
| Compliance         | Auditoría, retención, residencia de datos            | Parcial      | Políticas y contratos (DPA/BAA/SOC2)   | Compliance  | 60 días        |
| Automatización     | CI/CD con gates y rollback probado                   | Parcial      | Pipelines y evidencia de rollback      | DevOps      | 30 días        |
| Costos             | Presupuesto y alertas de gasto                       | Parcial      | Config de budgets y panel de costos    | FinOps      | 30 días        |

Interpretación: el go/no-go depende del cierre de brechas críticas (métricas HTTP, alertas, dashboards y secretos). La evidencia y la fecha objetivo deben consolidarse en un comité de aprobación.

### 10.1 Aprobación y gobierno de cambios

El RACI operativo debe definir propietarios por dominio (API, DB, Redis, Infra, WebSocket), gates de producción y políticas de rollback. Recomendación: establecer un Change Advisory Board (CAB) con competencias de seguridad y compliance para aprobar despliegues en producción, con registro de cambios, riesgos y mitigaciones[^1].

---

## Roadmap y Prioridades

El plan por horizontes concentra esfuerzos en fiabilidad operativa y cumplimiento, asegurando el menor riesgo y el mayor valor temprano.

Tabla 17. Plan 0–30/30–60/90 días (tareas, dueños, métricas de éxito)

| Horizonte | Tarea                                                    | Dueño       | Métrica de éxito                                  |
|-----------|----------------------------------------------------------|-------------|---------------------------------------------------|
| 0–30 días | Instrumentar métricas HTTP y alinear reglas             | Backend/API | Alertas HTTP firing con datos                     |
| 0–30 días | Alinear reglas WebSocket con ggrt_*                     | Backend/API | Alertas WS con datos y sin falsos positivos       |
| 0–30 días | Dashboards mínimos viables                              | SRE         | Paneles API/WS/DB/Redis/Infra disponibles         |
| 0–30 días | Integrar Slack/webhooks y gestor de secretos            | SRE         | Notificaciones críticas verificadas                |
| 30–60 días| Habilitar Caddy exporter y dashboard proxy              | SRE         | Panel y alertas de proxy activas                  |
| 30–60 días| Afinar umbrales con baselines                           | SRE         | Reducción de falsos positivos/negativos           |
| 30–60 días| Pruebas de caos/backpressure Redis/WS                   | SRE/QA      | Recuperación sin incidentes mayores               |
| 60–90 días| Definir SLO/SLI y dashboards ejecutivos                 | Arquitectura| SLOs documentados y aprobados                     |
| 60–90 días| Automatizar runbooks y guardia                          | Operaciones | Ejercicios de incident response ejecutados        |
| 60–90 días| Retención extendida (Thanos/Cortex) y federación        | SRE         | Almacenamiento largo plazo operativo              |

Interpretación: el plan secuencia quick wins (métricas/alertas/dashboards) y consolida resiliencia (DR, SLO/SLI, retención extendida). El éxito se mide por reducción de MTTR, mejora de señal/ruido en alertas y cumplimiento probado[^6][^20].

---

## Conclusión y dictamen preliminar

La plataforma y el diseño de despliegue de GRUPO_GAD muestran fortalezas decisivas: configuración de flytoml alineada a producción, Dockerfile multi-stage con usuario no-root, health checks y métricas activas, red privada WireGuard y TLS robusto, además de una oferta de observabilidad gestionada. No obstante, el go-live gubernamental requiere cerrar brechas críticas: métricas HTTP y alineación de reglas, cadena de notificaciones con secretos formalizados, visibilidad del proxy (Caddy exporter), DR con restauración probada, y compliance operativo (auditoría/retención/residencia). Con el roadmap propuesto, el cierre puede lograrse en 90 días, garantizando seguridad, confiabilidad y cumplimiento.

Dictamen: no-go temporal hasta completar métricas HTTP, dashboards mínimos y DR probada; conditional-go si se acepta un despliegue limitado con mitigaciones y un plan de cierre explícito en 30 días.

---

## Referencias

[^1]: Lista de verificación para pasar a producción · Fly Docs. https://fly.io/docs/apps/going-to-production/
[^2]: Seguridad · Fly Docs. https://fly.io/docs/security/
[^3]: Configuración de la aplicación (fly.toml) · Fly Docs. https://fly.io/docs/reference/configuration/
[^4]: Health Checks · Fly Docs. https://fly.io/docs/reference/health-checks/
[^5]: Seamless Deployments on Fly.io · Fly Docs. https://fly.io/docs/blueprints/seamless-deployments/
[^6]: Métricas en Fly.io · Fly Docs. https://fly.io/docs/monitoring/metrics/
[^7]: Soporte TLS · Fly Docs. https://fly.io/docs/networking/tls/
[^8]: Regiones · Fly Docs. https://fly.io/docs/reference/regions/
[^9]: Aplicación multi-región y fly-replay · Fly Docs. https://fly.io/docs/blueprints/multi-region-fly-replay/
[^10]: flyctl certs · Fly Docs. https://fly.io/docs/flyctl/certs/
[^11]: Prácticas de seguridad y cumplimiento en Fly.io · Fly Docs. https://fly.io/docs/security/security-at-fly-io/
[^12]: Redes privadas (6PN) · Fly Docs. https://fly.io/docs/networking/private-networking/
[^13]: Seguridad - Fly.io. https://fly.io/security/
[^14]: Aplicaciones sanitarias en Fly · Fly Docs. https://fly.io/docs/about/healthcare/
[^15]: Balanceo de carga · Fly Docs. https://fly.io/docs/reference/load-balancing/
[^16]: Autoscaling · Fly Docs. https://fly.io/docs/reference/autoscaling/
[^17]: Monitoring · Fly Docs. https://fly.io/docs/monitoring/
[^18]: Thanos. https://thanos.io/
[^19]: Blocks Storage — Cortex Metrics. https://cortexmetrics.io/docs/blocks-storage/
[^20]: Alertmanager | Prometheus. https://prometheus.io/docs/alerting/latest/alertmanager/
[^21]: App Availability and Resiliency · Fly Docs. https://fly.io/docs/apps/app-availability/
[^22]: Disaster Recovery from LiteFS Cloud · Fly Docs. https://fly.io/docs/litefs/disaster-recovery/
[^23]: Backing up your LiteFS cluster · Fly Docs. https://fly.io/docs/litefs/backup/
[^24]: Cumplimiento - Fly.io. https://fly.io/compliance
[^25]: Modelo de responsabilidad compartida · Fly Docs. https://fly.io/docs/security/shared-responsibility/
[^26]: Building Infrastructure Automation without Terraform · Fly Docs. https://fly.io/docs/blueprints/infra-automation-without-terraform/
[^27]: Monorepo y despliegues multi-entorno · Fly Docs. https://fly.io/docs/launch/monorepo/
[^28]: CI/CD con Fly.io: Deploy distributed applications with confidence · CircleCI. https://circleci.com/blog/ci-cd-with-fly-io/
[^29]: Precios de recursos en Fly.io · Fly Docs. https://fly.io/docs/about/pricing/
[^30]: Calculadora de precios - Fly.io. https://fly.io/calculator
[^31]: Gestión de costos en Fly.io · Fly Docs. https://fly.io/docs/about/cost-management/
[^32]: Guía de rollback · Fly Docs. https://fly.io/docs/blueprints/rollback-guide/
[^33]: Prometheus vs Thanos: diferencias clave y mejores prácticas — Last9. https://last9.io/blog/prometheus-vs-thanos/
[^34]: Escalado de Prometheus: consejos y estrategias — Last9. https://last9.io/blog/scaling-prometheus-tips-tricks-and-proven-strategies/
[^35]: Conceptos de monitoreo de servicios (SLO/SLI) · Google Cloud Observability. https://docs.cloud.google.com/stackdriver/docs/solutions/slo-monitoring