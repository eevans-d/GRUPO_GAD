# Scorecard de Calidad de Código para Estándares Gubernamentales – GRUPO_GAD

## 1. Propósito, alcance y narrativa del scorecard gubernamental

Los sistemas que brindan servicios ciudadanos, gestionan datos sensibles y deben operar en disponibilidad continua requieren una disciplina de ingeniería que combine calidad de código, seguridad por diseño, cumplimiento normativo y confiabilidad operacional. Este scorecard establece un marco integral y accionable para evaluar la calidad del software de GRUPO_GAD con foco en estándares gubernamentales, conectando métricas técnicas con controles de cumplimiento y riesgos operativos. Su objetivo es doble: por un lado, definir una línea base de excelencia técnica alineada con prácticas reconocidas; por otro, traducir esa línea base en decisiones de gestión y auditoría, con una cadencia de medición y mejora continua que asegure resiliencia y auditabilidad en todo momento.

El alcance cubre las capas y componentes críticos del sistema: la API REST (FastAPI), el bot de Telegram, la base de datos (PostgreSQL/PostGIS), el cache (Redis), la observabilidad (Prometheus, Grafana, AlertManager), la seguridad (autenticación JWT, middlewares de seguridad, rate limiting) y los canales de tiempo real (WebSockets). El scorecard se fundamenta en el análisis de la estructura del proyecto, su baseline de seguridad, el inventario de módulos y dependencias, y los planes de despliegue y automatización disponibles. La narrativa avanza del qué (marco y criterios), al cómo (métricas y medición), y al so what (decisiones, prioridades y planes).

Para sistemas 24/7 críticos se establecen principios rectores que orientan las decisiones: resiliencia por diseño, auditabilidad completa, seguridad por defecto, y una gobernanza técnica que exija evidencia objetiva de cumplimiento y trazabilidad de controles. Este documento se alinea con lineamientos del Instituto Nacional de Estándares y Tecnología (NIST), con el marco de privacidad de la Ley de Portabilidad y Responsabilidad de Seguro Médico (HIPAA) y con los criterios del marco SOC 2 (Service Organization Control 2) tipo II, empleando sus principios de seguridad, disponibilidad, integridad del procesamiento, confidencialidad y privacidad como guía para traducir requisitos normativos en controles técnicos verificables[^1][^3][^2].

### 1.1 Definición de sistemas gubernamentales críticos

En este contexto, se consideran servicios críticos aquellos que impactan directa o indirectamente en derechos, beneficios u obligaciones de la ciudadanía, gestionan información sensible y requieren disponibilidad continua. Los atributos obligatorios incluyen: cumplimiento normativo (p. ej., HIPAA), registro inmutable de auditoría, seguridad por defecto (configuraciones seguras en todos los entornos), y operación resiliente con mecanismos de degradación gradual y recuperación ante desastres. La criticidad 24/7 implica objetivos de nivel de servicio claros: tiempo de respuesta consistente, tolerancia a fallos, manejo controlado de picos de demanda y continuidad operativa sin degradación significativa de la experiencia.

Para clarificar el impacto de la indisponibilidad y orientar prioridades de ingeniería, se clasifica la criticidad por componentes. La siguiente tabla organiza los activos principales del sistema por su criticidad, stakeholders y consecuencias de indisponibilidad, y guía el enfoque del scorecard hacia donde el riesgo operacional y de cumplimiento es mayor.

Tabla 1. Inventario de activos y criticidad 24/7

| Componente                | Criticidad | Stakeholders principales                      | Consecuencias de indisponibilidad                                         |
|--------------------------|------------|-----------------------------------------------|---------------------------------------------------------------------------|
| API REST (FastAPI)       | Crítica    | Dirección de Tecnología, ciudadanía, auditoría | Interrupción de servicios ciudadanos, incumplimiento de SLAs, riesgo de auditoría |
| Bot de Telegram          | Alta       | Atención ciudadana, soporte, operaciones       | Pérdida de canal de interacción, aumento de tickets y tiempos de respuesta            |
| Base de datos (PostGIS)  | Crítica    | DPO, seguridad, equipo de datos                | Exposición de datos sensibles, interrupciones de procesos, impacto regulatorio        |
| Cache (Redis)            | Alta       | Operaciones, SRE, equipo de performance        | Degradación de latencia, sobrecarga de BD, errores por saturación                     |
| WebSockets               | Alta       | Producto, operaciones, ciudadanía              | Pérdida de tiempo real, impacto en notificaciones y monitoreo                        |
| Observabilidad           | Alta       | SRE, auditoría, seguridad                      | Detección tardía de incidentes, falta de evidencia de auditoría                       |
| Seguridad (Auth/Headers) | Crítica    | Seguridad, cumplimiento, auditoría             | Riesgo de acceso no autorizado, incumplimiento de HIPAA/SOC 2                          |

### 1.2 Resultados esperados y uso del scorecard

El scorecard habilita decisiones de gestión técnica y de cumplimiento: priorización de remediaciones, asignación de recursos, aprobaciones de despliegue, y preparación de auditorías. Su gobierno se basa en evidencia medible: reportes de herramientas de seguridad, métricas de calidad de código, trazas de auditoría y resultados de pruebas. El proceso es iterativo: se fijan objetivos y umbrales, se mide de manera continua, se reportan hallazgos y se implementan planes de mejora con cadencia mensual y revisiones ejecutivas trimestrales. La narrativa del documento traduce cada métrica en implicaciones de riesgo y accionabilidad, evitando un enfoque puramente técnico y manteniendo el foco en el valor para la ciudadanía y la resiliencia del servicio.

## 2. Marco de estándares gubernamentales y mapeo a controles técnicos

Las expectativas regulatorias y de buenas prácticas para sistemas gubernamentales se concentran en cuatro ejes: seguridad, disponibilidad, trazabilidad y privacidad. El cumplimiento no es un estado, sino un proceso continuo de verificación y mejora. Los lineamientos de NIST proveen el armazón para la gestión de riesgos y la definición de controles; HIPAA exige protección de información de salud y privacidad; SOC 2 tipo II verifica que los controles se mantengan a lo largo del tiempo, enfocándose en seguridad, disponibilidad, integridad del procesamiento, confidencialidad y privacidad[^1][^3][^2].

La traducción de estos marcos a controles técnicos se basa en tres principios: diseño seguro por defecto, evidencia automatizable y trazabilidad de acceso y cambios. A modo de referencia, la siguiente matriz mapea marcos y requisitos a controles implementados o planificados.

Tabla 2. Matriz de mapeo normativo a controles técnicos

| Marco / Requisito                         | Control técnico propuesto                                             | Estado actual (evidencia disponible)                              |
|-------------------------------------------|------------------------------------------------------------------------|-------------------------------------------------------------------|
| NIST – Gestión de riesgos                 | Registro de riesgos, SLAs de seguridad (MTTD/MTTR), controles de acceso | Parcial (SLAs definidos; registro y dashboards en progreso)       |
| NIST – Controles de seguridad             | Auth JWT, rate limiting, security headers, CORS endurecido             | Implementado (CORS y headers presentes; gaps: CSP, rotación)      |
| HIPAA – Protección de datos               | Cifrado en tránsito, cifrado en reposo, audit trail                    | Parcial (HTTPS; cifrado en reposo por verificar; audit trail parcial) |
| HIPAA – Privacidad y acceso               | Controles de acceso basados en roles, minimización de datos            | Parcial (controles base implementados; refinamiento requerido)    |
| SOC 2 – Seguridad y disponibilidad        | Monitoreo, alertas, resiliencia, capacidad                             | Parcial (Prom/Grafana implementados; límites y capacidad por validar) |
| SOC 2 – Integridad y confidencialidad     | Trazabilidad de cambios y acceso                                       | Parcial (logging con sanitización; audit trail incompleto)        |
| SOC 2 – Privacidad                        | Políticas de retención y minimización                                  | En progreso (definición de políticas pendiente)                   |

### 2.1 Requisitos HIPAA aplicables en código

Para HIPAA, el código debe garantizar confidencialidad e integridad de la información protegida (ePHI), registro de acceso y cambios, y privacidad por diseño. Esto implica cifrado en tránsito (HTTPS), cifrado en reposo (verificación y configuración efectiva en la base de datos y respaldos), controles de acceso granulares y audit trail robusto que registre quién, qué, cuándo y desde dónde se accede a datos sensibles. La minimización de datos en estructuras y logs, la separación de responsabilidades y la validación sistemática de entradas son prácticas que reducen exposición y simplifican auditoría[^3].

### 2.2 SOC 2 Tipo II en CI/CD y operación

SOC 2 tipo II exige evidencia sostenida en el tiempo de controles de seguridad, disponibilidad e integridad. Esto se traduce en pipelines CI/CD con trazabilidad de artefactos, aprobaciones, pruebas automatizadas y control de cambios; registros de auditoría correlacionables con eventos de seguridad; alertas con SLAs definidos; y verificación periódica de capacidades y límites operativos. El scorecard consolida esta evidencia en dashboards, umbrales y reportes de auditoría con cadencia mensual[^2].

## 3. Metodología del scorecard: métricas, ponderaciones y cálculo

La metodología se basa en dimensiones ponderadas que reflejan la criticidad y el riesgo de cada área: Seguridad (30%), Calidad de Código (25%), Confiabilidad (20%), Cumplimiento (15%) y Performance/Mantenibilidad (10%). Cada dimensión se evalúa con métricas y umbrales que se adaptan a sistemas críticos 24/7. El cálculo combina estado actual inferido del baseline de seguridad, la estructura del proyecto y la observación técnica disponible; la evidencia faltante se marca como “por medir” y se prioriza su recolección en el plan de mejora.

Tabla 3. Dimensiones, métricas y ponderación

| Dimensión                 | Métricas clave                                                   | Ponderación | Umbral objetivo (sistemas críticos)                              |
|--------------------------|------------------------------------------------------------------|-------------|------------------------------------------------------------------|
| Seguridad                | OWASP Top 10 controls, MTTD/MTTR, cobertura de pruebas de seguridad | 30%         | MTTD < 5 min, MTTR < 30 min, 0 vulnerabilidades críticas         |
| Calidad de Código        | Cobertura, complejidad ciclomática, maintainability index, deuda, duplicación | 25%         | Cobertura >85%, complejidad ≤10 por función, MI >65, deuda <5%, duplicación <3% |
| Confiabilidad            | Manejo de errores, degradación, tolerancia a fallos, DR          | 20%         | Evidencia de patrones y runbooks; RPO/RTO definidos              |
| Cumplimiento             | HIPAA/SOC 2, NIST, audit trail                                   | 15%         | 100% evidencias y auditorías completas                           |
| Performance/Mantenibilidad | Latencia API p95, optimización de consultas, memoria, concurrencia, documentación, automatización | 10%         | p95 <200 ms, consultas optimizadas, memoria eficiente, doc y despliegue automatizado |

### 3.1 Dimensiones y ponderaciones

La ponderación prioriza seguridad y calidad por su impacto directo en riesgo y sostenibilidad: sin seguridad y calidad adecuadas, la confiabilidad y el cumplimiento quedan comprometidos. La dimensión de cumplimiento asegura que los controles regulatorios tengan evidencias y una ruta de auditoría clara. Performance y mantenibilidad, aunque con menor peso relativo, son críticas para la experiencia ciudadana y la eficiencia operacional.

### 3.2 Cálculo del puntaje y estados

Se definen estados cualitativos para interpretar el puntaje total: Crítico (<50), Medio (50–74) y Listo/Óptimo (≥75). La captura de datos se realiza mediante herramientas y reportes existentes (seguridad, análisis estático, pruebas, métricas), y la consolidación de la evidencia se presenta en anexos para trazabilidad.

Tabla 4. Catálogo de métricas: definición, objetivo, medición, fuente

| Métrica                         | Definición                                                  | Objetivo                                  | Método de medición                        | Fuente de evidencia                         |
|---------------------------------|-------------------------------------------------------------|-------------------------------------------|-------------------------------------------|---------------------------------------------|
| Seguridad – OWASP Top 10        | Cobertura de controles contra riesgos web más comunes       | 100% de controles clave implementados     | Revisión de controles y pruebas           | Middlewares, pruebas, reportes seguridad    |
| Seguridad – MTTD/MTTR           | Tiempo medio de detección/respuesta ante incidentes         | MTTD < 5 min; MTTR < 30 min               | Métricas y alertas de observabilidad      | Prometheus/Grafana, AlertManager            |
| Seguridad – Audit trail         | Registro de acceso y cambios en datos sensibles             | 100% cobertura en endpoints sensibles     | Instrumentación de auditoría              | Logs de aplicación y base de datos          |
| Calidad – Cobertura             | Porcentaje de líneas cubiertas por pruebas                  | >85%                                      | Reporte de cobertura                      | Herramientas de testing                     |
| Calidad – Complejidad ciclomática | Complejidad por función                                     | ≤10                                       | Análisis estático                         | Reportes de análisis                        |
| Calidad – Maintainability Index | Índice de mantenibilidad (MI)                               | >65                                       | Análisis estático                         | Reportes de análisis                        |
| Calidad – Deuda técnica         | Ratio de deuda sobre esfuerzo total                         | <5%                                       | Herramientas de deuda                     | Reportes de calidad                         |
| Calidad – Duplicación           | Porcentaje de líneas duplicadas                             | <3%                                       | Herramientas de duplicación               | Reportes de análisis                        |
| Confiabilidad – Errores         | Robustez en manejo de errores y logging                     | Patrones consistentes                     | Revisión de código y pruebas              | Código y tests                              |
| Confiabilidad – Degradación     | Degradación gradual bajo carga/incidentes                   | Implementada y probada                    | Pruebas y runbooks                        | Pruebas y documentación                     |
| Confiabilidad – Tolerancia      | Mecanismos de failover y timeouts                           | Implementados                             | Revisión de configuración y pruebas       | Configuración, pruebas                      |
| Confiabilidad – DR              | RPO/RTO y planes de recuperación                            | Definidos y ensayados                     | Runbooks y simulacros                     | Documentación de DR                         |
| Performance – API p95           | Latencia p95 de endpoints críticos                          | <200 ms                                   | Métricas de aplicación                    | Prometheus/Grafana                          |
| Performance – Consultas         | Optimización de consultas y uso de índices                  | Consultas críticas optimizadas            | Planes de ejecución y tuning              | Configuración BD, índices                   |
| Performance – Memoria           | Uso de memoria eficiente                                     | Sin leaks ni picos anómalos               | Métricas runtime                          | Observabilidad                              |
| Performance – Concurrencia      | Manejo de usuarios concurrentes                              | Sin saturación ni bloqueos                | Pruebas de carga                          | Scripts y métricas                          |
| Mantenibilidad – Documentación  | Calidad y completitud de documentación                      | Doc completa y actualizada                | Revisión documental                       | Documentación técnica                       |
| Mantenibilidad – Legibilidad    | Estándares de estilo y lectura de código                    | Guías aplicadas                           | Linting y revisiones                      | Configuración linters                       |
| Mantenibilidad – Automatización | CI/CD y despliegue automatizado                             | Pipeline y gates definidos                | Revisión CI/CD                            | Workflows y artefactos                      |
| Mantenibilidad – Monitoreo      | Integración de métricas y alertas                           | Dashboards y alertas efectivas            | Revisión de observabilidad                | Prometheus/Grafana, AlertManager            |

## 4. Scorecard consolidado y evaluación de brechas

La siguiente tabla sintetiza el estado actual, el objetivo y la brecha por dimensión, con el puntaje parcial ponderado. Donde no existe evidencia suficiente, se marca “por medir”; esto afecta el riesgo residual y se prioriza en el plan de mejora.

Tabla 5. Scorecard consolidado

| Dimensión                 | Estado actual                                  | Objetivo                         | Brecha                           | Puntaje (0–100) | Peso | Puntaje ponderado | Riesgo residual |
|--------------------------|-----------------------------------------------|----------------------------------|----------------------------------|-----------------|------|-------------------|-----------------|
| Seguridad                | Parcial (controles base; gaps de CSP/rotación) | 100% controles, MTTD/MTTR OK     | Audit trail y cifrado en reposo  | 70              | 0.30 | 21.0              | Medio-Alto      |
| Calidad de Código        | Parcial (cobertura amplia; otras métricas por medir) | Umbrales técnicos cumplidos       | Complejidad/MI/deuda/duplicación | 60              | 0.25 | 15.0              | Medio           |
| Confiabilidad            | Parcial (errores y tolerancia básicos; DR por validar) | Patrones completos y DR ensayado  | Degradación y DR evidenciados    | 55              | 0.20 | 11.0              | Medio-Alto      |
| Cumplimiento             | Parcial (HIPAA/SOC 2 en progreso)              | Evidencias completas y auditables | Políticas, cifrado, auditoría    | 50              | 0.15 | 7.5               | Alto            |
| Performance/Mantenibilidad | Parcial (métricas base; latencia p95 por medir) | p95 <200 ms, doc y automatización | Latencia, consultas, memoria     | 50              | 0.10 | 5.0               | Medio           |
| Total                    |                                               |                                  |                                  |                 |      | 59.5              | Medio-Alto      |

Interpretación: el puntaje actual sitúa al sistema en estado Medio (59.5/100), con riesgo residual medio-alto. Las brechas críticas se concentran en seguridad (audit trail, cifrado en reposo, CSP) y cumplimiento (políticas y evidencias). La calidad de código muestra fortaleza en cobertura de pruebas, pero requiere consolidar complejidad ciclomática, maintainability index, deuda y duplicación a niveles gubernamentales. La confiabilidad necesita evidencias de degradación gradual y planes de DR con simulacros, mientras que performance debe objetivar la latencia p95 y la optimización de consultas en producción.

### 4.1 Presentación de resultados

El color coding ayuda a gestionar prioridades: verde (≥75), amarillo (50–74), rojo (<50). Las áreas rojas y amarillas concentran las acciones inmediatas y de alto impacto: audit trail, cifrado en reposo, rate limiting con persistencia, adopción de CSP, cumplimiento de métricas técnicas en calidad de código, y evidencia de resiliencia (degradación y DR). Se recomienda un tablero ejecutivo con tendencias mensuales y un “compliance health” que consolide evidencias por control.

## 5. Dimensión de Seguridad (Security Scoring)

La seguridad se evalúa por controles implementados y por la evidencia de su eficacia en producción. El baseline muestra autenticación JWT robusta, middlewares de seguridad (headers, CORS, proxy), rate limiting especializado y un pipeline de auditoría de seguridad con ejecución semanal y bajo demanda. A la vez, identifica riesgos y recomendaciones que orientan el plan de mejora.

Tabla 6. Seguridad: estado y recomendaciones

| Área                      | Estado actual                                       | Riesgo principal                         | Recomendación prioritaria                                        |
|--------------------------|-----------------------------------------------------|------------------------------------------|-------------------------------------------------------------------|
| Autenticación JWT        | Implementación robusta; expiración configurable     | Falta de rotación documentada            | Refresh tokens y procedimiento de rotación con validación         |
| Secretos                 | Gestión por entorno; ejemplos con CHANGEME          | Secretos inseguros en producción         | Rotación inmediata; integración con gestor de secretos            |
| Rate limiting            | Especializado, en memoria                           | No persistente entre workers             | Migrar a Redis; monitoreo de breaches                            |
| Security headers         | Headers completos                                   | CSP no específico; headers HIPAA         | CSP endurecido; agregar headers de cumplimiento                   |
| CORS                     | Configurado por entorno                             | Permisivo en desarrollo                  | Endurecer origins; logging de violaciones                        |
| Base de datos            | Conexiones parametrizadas                           | Cifrado en reposo por verificar          | Habilitar cifrado en reposo; backup encryption                   |
| Integraciones externas   | Telegram/Redis/WebSockets                           | Tokens y TLS no validados integralmente  | Rotación de tokens; TLS en producción para Redis                 |
| Auditoría y monitoreo    | Métricas y logs con sanitización                    | Audit trail incompleto; alertas limitadas| Implementar audit trail; eventos de seguridad; SIEM              |

La adherencia a OWASP Top 10 se traduce en controles verificables: autenticación y gestión de sesiones seguras, restricciones de entrada, endurecimiento de headers, configuración CORS estricta, y protección contra ataques de tasa. Los SLAs de seguridad (MTTD y MTTR) se integran a alertas y runbooks, con responsabilidad operativa definida.

Tabla 7. SLAs de seguridad

| SLA                   | Valor objetivo | Trigger de alerta                        | Runbook asociado                         | Responsable |
|-----------------------|----------------|------------------------------------------|------------------------------------------|------------|
| MTTD (detección)      | < 5 min        | Ausencia de métricas/alertas críticas     | Alertas y dashboards de seguridad         | SRE        |
| MTTR (respuesta)      | < 30 min       | Incidente confirmado (severidad alta)     | Respuesta a incidentes y escalación       | Seguridad  |
| Cobertura pruebas sec | 100%           | Control sin test o evidencia insuficiente | Implementación de pruebas de seguridad    | DevSecOps  |
| Vulnerabilidades      | 0 críticas     | Hallazgo crítico en baseline              | Remediación inmediata y verificación      | DevSecOps  |

### 5.1 Autenticación y gestión de secretos

La autenticación basada en JSON Web Token (JWT) con `python-jose[cryptography]` está operativa con expiración configurable, flujos OAuth2 y protección de endpoints. La recomendación es introducir refresh tokens para sesiones de larga duración y formalizar la rotación de secretos con validación en startup, evitando valores por defecto y habilitando health checks de secretos. La integración con gestores de secretos (HashiCorp Vault o AWS Secrets Manager) añade una capa de control y auditoría sobre credenciales y claves, alineada con mejores prácticas.

### 5.2 Protección perimetral y datos

El rate limiting especializado requiere persistencia para entornos con múltiples workers; Redis es la opción natural. Los security headers están presentes y deben complementarse con una política de Content Security Policy (CSP) específica para la interfaz y con headers orientados a cumplimiento HIPAA. En base de datos, la verificación del cifrado en reposo y la habilitación de cifrado de respaldos son críticas para cumplir con HIPAA; en integraciones (Telegram, Redis, WebSockets) se recomienda validación de fortaleza de tokens, IP whitelisting para webhooks y TLS en producción.

## 6. Dimensión de Cumplimiento (HIPAA, SOC 2, NIST)

El cumplimiento exige evidencia verificable y sostenida en el tiempo: cifrado en tránsito y reposo, controles de acceso, audit trail, monitoreo y alertas, políticas de privacidad y continuidad. La siguiente tabla resume el estado y las acciones requeridas.

Tabla 8. Requisitos vs controles vs evidencias vs estado

| Requisito             | Control técnico                          | Evidencia disponible                   | Estado       | Acción requerida                        |
|-----------------------|------------------------------------------|----------------------------------------|--------------|-----------------------------------------|
| Cifrado en tránsito   | HTTPS y seguridad en integraciones       | Configuración y despliegue             | Parcial      | Validar TLS integral                    |
| Cifrado en reposo     | BD y respaldos cifrados                  | Por verificar                           | Crítico      | Habilitar cifrado en BD/backups         |
| Control de acceso     | Auth JWT, roles y permisos               | Middleware y dependencias              | Parcial      | Refinamiento y evidencia por endpoint   |
| Audit trail           | Registro de acceso/cambios               | Logging con sanitización               | Crítico      | Instrumentación completa                |
| Monitoreo y alertas   | Prometheus, Grafana, AlertManager        | Métricas y dashboards                   | Parcial      | Alertas específicas de seguridad        |
| Políticas HIPAA       | Privacidad y retención                   | Por documentar                          | Pendiente    | Definir y aprobar políticas             |
| SOC 2 – Evidencias    | CI/CD trazable, pruebas automatizadas    | Workflows y reportes                    | Parcial      | Consolidar artefactos y auditorías      |
| NIST – Gestión riesgos| Registro y SLAs                          | Por consolidar                          | Pendiente    | Crear registro y dashboards ejecutivos  |

### 6.1 HIPAA en código

La protección de información protegida electrónica (ePHI) requiere cifrado de datos en tránsito y en reposo, registro de acceso y cambios, y minimización de exposición en logs y estructuras de datos. Se deben separar funciones y validar entradas sistemáticamente, con políticas de retención y acceso que garanticen privacidad. El audit trail debe correlacionar eventos de aplicación y base de datos, y enlazarse con alertas para reacción rápida[^3].

### 6.2 SOC 2 Tipo II en CI/CD y operación

SOC 2 tipo II demanda evidencia continua de seguridad y disponibilidad: pipelines CI/CD con trazabilidad de artefactos, pruebas automatizadas y controles de cambio; registros de auditoría; monitoreo y alertas; y verificación periódica de capacidad y límites operativos. La consolidación de evidencias se realiza en dashboards y reportes con foco en auditoría[^2].

## 7. Dimensión de Calidad de Código

Las métricas técnicas son el núcleo de la sostenibilidad del sistema. Para sistemas críticos, los objetivos son claros: cobertura de pruebas por encima del 85%, complejidad ciclomática máxima de 10 por función, maintainability index superior a 65, ratio de deuda técnica por debajo del 5% y duplicación de código inferior al 3%. La calidad de documentación, legibilidad, automatización y monitoreo también se consideran en esta dimensión.

Tabla 9. Benchmarks y medición

| Métrica                    | Objetivo                     | Medición actual        | Estado    | Acción requerida                               |
|---------------------------|------------------------------|------------------------|-----------|-----------------------------------------------|
| Cobertura de pruebas      | >85%                         | Amplia (80+ archivos)  | Parcial   | Consolidar reportes por módulo                 |
| Complejidad ciclomática   | ≤10 por función              | Por medir              | Pendiente | Análisis estático por función                  |
| Maintainability Index     | >65                          | Por medir              | Pendiente | Análisis global por módulo                     |
| Deuda técnica             | <5%                          | Por medir              | Pendiente | Evaluación y planificación de remediación      |
| Duplicación de código     | <3%                          | Por medir              | Pendiente | Identificar y consolidar duplicaciones         |
| Documentación             | Completa y actualizada       | Extensa                | Parcial   | Inventario y checklist de completitud          |
| Estilo/legibilidad        | Guías aplicadas              | Por validar            | Pendiente | Linting y estándares de lectura                |
| Automatización CI/CD      | Pipeline con gates           | Workflows presentes    | Parcial   | Definir gates y artefactos trazables           |
| Monitoreo integrado       | Métricas y alertas           | Prom/Grafana/AlertMgr  | Parcial   | Endurecer alertas y compliance dashboard       |

### 7.1 Métricas técnicas

Se recomienda ejecutar análisis estáticos y reportes de cobertura de forma regular en CI/CD, con publicación en dashboards y verificación en pull requests. Los umbrales se configuran como gates para impedir despliegues que degraden la calidad. La trazabilidad por módulo permite focalizar esfuerzos donde el riesgo técnico y de cumplimiento es mayor.

## 8. Dimensión de Confiabilidad

La confiabilidad se sustenta en patrones de manejo de errores, degradación gradual, tolerancia a fallos y recuperación ante desastres. La evidencia requerida incluye pruebas, runbooks y simulacros. El baseline muestra health checks, logging y monitoreo; sin embargo, falta instrumentar degradación gradual y formalizar DR con objetivos RPO/RTO y evidencias de simulacros.

Tabla 10. Estrategias de resiliencia

| Riesgo                         | Mecanismo                    | Evidencia requerida              | Estado       | Acción                                                |
|--------------------------------|------------------------------|----------------------------------|-------------|-------------------------------------------------------|
| Saturación de servicios        | Rate limiting persistente    | Métricas y límites configurados  | Parcial     | Migrar a Redis y monitorear breaches                  |
| Fallas de dependencia          | Timeouts y reintentos        | Configuración y pruebas          | Parcial     | Endurecer y documentar patrones                       |
| Caída de base de datos         | Failover y replicas          | Configuración y pruebas          | Pendiente   | Habilitar y ensayar failover                          |
| Incidentes de seguridad        | Alertas y respuesta          | Runbooks y métricas              | Parcial     | Establecer MTTD/MTTR y SIEM                           |
| Pérdida de datos               | Backups cifrados             | Evidencia de cifrado y restauración | Pendiente | Habilitar cifrado y pruebas de restore                |
| Degradación por carga          | Degradación gradual          | Pruebas y estrategias            | Pendiente   | Implementar políticas de degradación                  |

### 8.1 Degradación gradual y toleración a fallos

Se deben definir modos de degradación que prioricen funciones esenciales, reduciendo funcionalidades no críticas bajo carga o incidentes. Los timeouts, reintentos, circuit breakers y bulkheads se implementan y prueban sistemáticamente. La resiliencia 24/7 exige además correlación de eventos con auditoría y respuesta a incidentes, integrando evidencia técnica y de cumplimiento.

## 9. Dimensión de Performance y Mantenibilidad

Los benchmarks de performance incluyen latencia API p95 por debajo de 200 ms para endpoints críticos, optimización de consultas (índices y planes de ejecución), uso eficiente de memoria y manejo adecuado de concurrencia. La mantenibilidad incorpora documentación, legibilidad, automatización de despliegue e integración de monitoreo.

Tabla 11. Benchmarks de performance

| Área                   | Métrica                 | Objetivo         | Medición actual | Brecha       | Prioridad |
|------------------------|-------------------------|------------------|-----------------|--------------|----------|
| API REST               | Latencia p95            | <200 ms          | Por medir       | Desconocida  | Alta     |
| Base de datos          | Consultas e índices     | Optimizadas      | Por evaluar     | Pendiente    | Alta     |
| Cache (Redis)          | Hit ratio y latencia    | Alto hit, baja latencia | Parcial    | Pendiente    | Media    |
| Memoria                | Uso y leaks             | Sin leaks        | Parcial         | Pendiente    | Media    |
| Concurrencia           | Usuarios concurrentes   | Sin saturación   | Por medir       | Desconocida  | Media    |
| Observabilidad         | Dashboards y alertas    | Completos        | Parcial         | Pendiente    | Media    |

### 9.1 Performance de consultas y datos

La optimización de consultas se apoya en índices adecuados, revisión de planes de ejecución y métricas por endpoint. En PostGIS, la seguridad y permisos deben revisarse para evitar exposición inadvertida y garantizar que operaciones geoespaciales se auditen cuando involucren datos sensibles. La instrumentación de métricas por endpoint y consulta es esencial para detectar cuellos de botella y orientar tuning.

## 10. Matriz de readiness gubernamental

La readiness sintetiza la preparación del sistema para auditorías gubernamentales, combinando cumplimiento, seguridad, confiabilidad, performance y mantenibilidad. El color coding identifica áreas en rojo que requieren acciones inmediatas.

Tabla 12. Matriz de readiness

| Área               | Criterio                          | Estado        | Evidencia                         | Próximo paso                              |
|--------------------|-----------------------------------|---------------|-----------------------------------|-------------------------------------------|
| Seguridad          | MTTD/MTTR y controles OWASP       | Amarillo      | Métricas y middlewares            | Completar audit trail y CSP               |
| Cumplimiento       | HIPAA/SOC 2/NIST                  | Rojo          | Parcial                           | Políticas, cifrado en reposo, evidencias  |
| Confiabilidad      | DR y degradación                  | Amarillo      | Health checks y logs              | Ensayos de DR y políticas de degradación  |
| Performance        | API p95 y consultas               | Amarillo      | Métricas base                     | Medir p95 y optimizar consultas           |
| Mantenibilidad     | Doc, legibilidad, CI/CD           | Amarillo      | Documentación y workflows         | Gates de calidad y artefactos trazables   |

Interpretación: la readiness actual exige un enfoque inmediato en cumplimiento y seguridad para mitigar riesgo residual y habilitar auditorías sin hallazgos críticos.

## 11. Plan de mejora y cronograma

El plan se organiza en cuatro horizontes (8 semanas) con priorización basada en riesgo e impacto regulatorio. Se asignan responsables, dependencias y entregables, y se integra el pipeline CI/CD para verificación continua.

Tabla 13. Cronograma 8 semanas

| Semana(s) | Acción                                                       | Responsable  | Entregable                                   | Dependencia                         |
|-----------|--------------------------------------------------------------|--------------|----------------------------------------------|-------------------------------------|
| 1–2       | Rotación de secretos y validación en startup                 | DevSecOps    | Procedimiento y evidencias                   | Acceso a gestores de secretos       |
| 1–2       | Verificación e implementación de cifrado en reposo (BD/backups) | Seguridad/DBA | Configuración y pruebas de cifrado            | Coordinación con infraestructura     |
| 1–2       | Implementar audit trail completo                             | DevSecOps    | Instrumentación y reportes de auditoría      | Definición de eventos y esquemas     |
| 1–2       | Configurar secretos externos (Vault/Secrets Manager)         | DevSecOps    | Integración y rotación automatizada          | Aprovisionamiento y políticas        |
| 3–4       | Migrar rate limiting a Redis                                 | SRE          | Límites persistentes y monitoreo             | Configuración Redis                  |
| 3–4       | Implementar refresh tokens para JWT                          | Backend      | Flujos y pruebas de sesión                   | Cambios en autenticación             |
| 3–4       | Endurecer CORS por entorno                                   | DevSecOps    | Configuración y logging de violaciones       | Validación de origins                |
| 3–4       | Configurar TLS/SSL integral para integraciones               | SRE          | Certificados y validaciones                  | Infraestructura y certificados       |
| 5–6       | Implementar CSP específico                                   | Frontend/DevSecOps | Política CSP y pruebas                     | Inventario de recursos               |
| 5–6       | IP whitelisting para webhooks                                | SRE          | Reglas y monitoreo                           | Configuración de red                 |
| 5–6       | Añadir monitoreo de eventos de seguridad                     | SRE          | Alertas y dashboards                         | Definición de severidades            |
| 5–6       | Backup encryption                                            | Seguridad/DBA | Configuración y pruebas de restore           | Cifrado de almacenamiento            |
| 7–8       | Optimización de middlewares de seguridad                     | DevSecOps    | Métricas y ajustes de rendimiento            | Pruebas de carga                     |
| 7–8       | Documentar procedimientos de respuesta a incidentes          | Seguridad    | Runbooks y capacitación                      | Alertas y SLAs                       |
| 7–8       | Compliance dashboard                                         | SRE/Compliance | Dashboard y reportes                         | Datos consolidados                   |
| 7–8       | Pruebas de penetración básicas                               | Seguridad    | Reporte y remediaciones                      | Coordinación y ventanas de prueba    |

Tabla 14. Backlog priorizado

| Ítem                                        | Riesgo/Impacto | Prioridad | Estado       |
|---------------------------------------------|----------------|-----------|--------------|
| Audit trail completo                        | Alto           | Crítica   | En curso     |
| Cifrado en reposo BD/backups                | Alto           | Crítica   | Pendiente    |
| Rate limiting persistente (Redis)           | Medio          | Alta      | Pendiente    |
| CSP endurecido                              | Medio          | Media     | Pendiente    |
| Refresh tokens JWT                          | Medio          | Alta      | Pendiente    |
| TLS integral (Redis, webhooks)              | Medio          | Alta      | Pendiente    |
| Políticas HIPAA y SOC 2                     | Alto           | Crítica   | Pendiente    |
| DR: RPO/RTO y simulacros                    | Alto           | Alta      | Pendiente    |
| Métricas API p95 por endpoint               | Medio          | Alta      | Pendiente    |
| Gate de calidad en CI/CD                    | Medio          | Media     | Pendiente    |

### 11.1 Hitos y verificación

Los hitos se verifican mediante evidencias: reportes, configuraciones aplicadas y pruebas. El criteria de done incluye publicación en dashboards, artefactos trazables en CI/CD y validación de auditoría.

Tabla 15. Hitos por semana

| Hito                        | Evidencia                          | Métrica de aceptación                | Responsable  |
|----------------------------|------------------------------------|--------------------------------------|--------------|
| Secretos rotados           | Registro de rotación y health check| 0 secretos por defecto en producción | DevSecOps    |
| Cifrado en reposo activo   | Config BD/backups y pruebas        | Datos cifrados y restore verificado  | Seguridad/DBA|
| Audit trail operativo      | Eventos y reportes                 | 100% endpoints sensibles con auditoría| DevSecOps    |
| Rate limiting persistente  | Métricas y límites                 | Límites aplicados y breaches alertados| SRE         |
| CSP implementado           | Política y pruebas                 | CSP sin violaciones críticas         | Frontend/DevSecOps |
| TLS integral               | Certificados y validaciones        | 100% canales con TLS                 | SRE          |
| DR ensayado                | Runbook y simulacro                | RPO/RTO cumplidos en prueba          | Seguridad/SRE|
| Compliance dashboard       | Dashboard y reportes               | Reportes mensuales auditables        | SRE/Compliance |

## 12. Gobernanza, CI/CD y auditoría continua

La gobernanza técnica define puertas de calidad y seguridad en el pipeline de integración y despliegue continuo (CI/CD). Las herramientas de auditoría de seguridad y dependencias operan con frecuencia semanal y bajo demanda, generando reportes en formatos JSON y Markdown para trazabilidad. La trazabilidad de artefactos y versiones, junto con la evidencia de auditoría, es imprescindible para auditorías HIPAA y SOC 2.

Tabla 16. Controles de CI/CD

| Control                       | Herramienta/Workflow             | Frecuencia          | Artefacto                         | Responsable |
|-------------------------------|----------------------------------|---------------------|-----------------------------------|-------------|
| Auditoría de dependencias     | Security Audit Workflow          | Semanal y bajo demanda | Reportes JSON/Markdown           | DevSecOps   |
| Análisis estático de seguridad| Bandit/pip-audit                 | En PRs y schedule   | Reportes y alertas                | DevSecOps   |
| Detección de secrets          | TruffleHog                       | En PRs y schedule   | Alertas y registros               | DevSecOps   |
| Gates de calidad              | CI/CD pipeline                   | En cada despliegue  | Artefactos trazables              | Backend/SRE |
| Observabilidad y alertas      | Prometheus/Grafana/AlertManager  | Continuo            | Dashboards y alertas              | SRE         |
| Compliance reporting          | Dashboard de cumplimiento        | Mensual             | Reporte consolidado               | Compliance  |

### 12.1 Políticas y procedimientos

Se establecen políticas de rotación de secretos, respuesta a incidentes con escalación y comunicación, y procedimientos de auditoría con conservación de evidencias. Las políticas de cumplimiento incluyen privacidad, retención, minimización y acceso, y se comunican a los equipos para asegurar adherencia.

## 13. Anexos: glosario, plantillas y fuentes

Glosario y definiciones:
- NIST (National Institute of Standards and Technology): marco de gestión de riesgos y controles de seguridad para sistemas y organizaciones.
- HIPAA (Health Insurance Portability and Accountability Act): normativa estadounidense que establece estándares de privacidad y seguridad para información de salud.
- SOC 2 (Service Organization Control 2): marco de auditoría para proveedores de servicios, enfocado en seguridad, disponibilidad, integridad del procesamiento, confidencialidad y privacidad.
- MTTD (Mean Time To Detection): tiempo medio de detección de incidentes.
- MTTR (Mean Time To Response): tiempo medio de respuesta ante incidentes.
- CSP (Content Security Policy): política de seguridad para controlar recursos cargados por el navegador.
- DR (Disaster Recovery): recuperación ante desastres, con objetivos RPO (Recovery Point Objective) y RTO (Recovery Time Objective).

Plantillas:
- Scorecard: dimensiones, métricas, estado, objetivo, brecha, acciones.
- Matriz de riesgos: riesgo, criticidad, probabilidad, impacto, score, acción.
- Matriz de mapeo normativo: marco/requisito, control, evidencia, estado.

Información faltante y supuestos:
- No se dispone de valores actuales consolidados para cobertura de código por módulo, complejidad ciclomática por función, maintainability index, ratio de deuda técnica y porcentaje de duplicación.
- Falta evidencia del cifrado de datos en reposo (base de datos y respaldos), clave gestionada por entorno y rotación documentada.
- No se presentan métricas de latencia p95 por endpoint ni perfiles de carga máxima concurrenta soportada.
- Inventario de hallazgos de seguridad con criticidad y tiempos de remediación no consolidado.
- Políticas y procedimientos específicos de HIPAA y SOC 2 (privacidad, retención, acceso, auditoría) requieren consolidación documental.
- Evidencias de pruebas de recuperación ante desastres (RPO/RTO) y simulacros no disponibles.
- Alcance y profundidad de análisis SAST/DAST e integración continua en CI/CD incomplete.
- Detalle de adopción de CSP (Content Security Policy) y validación de su eficacia no presente.
- Estado de implementación de audit trail inmutable y correlacionable por entorno requiere especificación técnica.
- Matriz de readiness completa y su scoring por área necesita validación y firma de compliance.

Referencias:
[^1]: NIST Cybersecurity Framework. https://www.nist.gov/cyberframework  
[^2]: AICPA SOC 2 Framework. https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/soc-2  
[^3]: HIPAA Security Rule. https://www.hhs.gov/hipaa/for-professionals/security/index.html

---

Este scorecard ofrece un camino práctico y medible para que GRUPO_GAD alcance y sostenga estándares gubernamentales, integrando seguridad, calidad de código, confiabilidad, cumplimiento y performance en una narrativa coherente de gestión técnica y de riesgos. La implementación disciplinada del plan propuesto permitirá reducir el riesgo residual, mejorar la experiencia ciudadana y superar auditorías con evidencia sólida y trazable.