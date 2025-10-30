# Testing PostGIS para Geolocalización Operativa en GRUPO_GAD: Diseño, Cobertura y Rendimiento

## 1. Introducción, alcance y contexto operativo

Este plan maestro de pruebas define cómo verificar, con rigor técnico y enfoque operativo, las funcionalidades geoespaciales basadas en PostGIS que soportan capacidades críticas del backend de GRUPO_GAD: búsqueda de efectivos cercanos, geocercas, conversión y validación de coordenadas, trazabilidad de movimientos, alertas en tiempo casi real y optimización de rutas. La ambición es doble: asegurar corrección (precisión métrica y semántica espacial) y desempeño (latencia y throughput) bajo cargas realistas, y alinear el testing con patrones de despliegue y observabilidad existentes.

El backend de GRUPO_GAD es una aplicación asíncrona construida con FastAPI y SQLAlchemy (AsyncSession), que utiliza PostgreSQL con PostGIS para cálculos de proximidad precisos mediante geography (SRID 4326), Redis para cache y Pub/Sub, y WebSockets para broadcast y heartbeat. La arquitectura se completa con observabilidad basada en Prometheus y health checks diferenciados (/health, /health/ready), además de migraciones gestionadas con Alembic. La aplicación está en producción con despliegue en Fly.io y públicamente accesible, lo que permite validar hipótesis y medir el impacto de tuning en un entorno operativo real, reforzando la trazabilidad entre código, pruebas y métricas expuestas[^1][^2].

La adopción de geography con SRID 4326 no es un detalle: habilita cálculos de distancia en metros sobre un elipsoide, lo que resulta indispensable para filtros por radio,邻居搜索 (nearest neighbor) y predicados de geocerca con tolerancias razonables. La semántica de medición y los predicados index-aware de PostGIS guían tanto el diseño de las pruebas como los patrones de consulta que deben ser estandarizados en el servicio geoespacial[^3][^4].

En este plan respondemos, de manera accionable, a las preguntas clave de negocio y tecnología: qué funciones de PostGIS deben ser probadas y cómo; qué consultas y predicados se emplean en proximity, geocercas y nearest neighbor; cómo validar uso y beneficio de índices espaciales; cómo probar transacciones (aislamiento, rollback, concurrencia) con datos espaciales; cómo integrar pruebas asíncronas con FastAPI y PostGIS; qué casos operativos (proximidad, asignación, tracking, alertas, rutas) cubren end-to-end; cómo diseñar pruebas de carga y estrés; qué métricas y alertas monitorear; qué controles de seguridad espacial incorporar; y qué plan de implementación, traceability yDefinition of Done (DoD) asegurar para alcanzar un coverage objetivo, trazable por módulo y consulta.

Brechas de información a considerar desde el inicio:
- Estado del índice espacial PostGIS en producción y ejecución completa de migraciones (histórico de CREATE EXTENSION postgis y DDL de índices).
- Volúmenes reales de datos (número de efectivos y frecuencia de updates) para calibrar datasets y tasas de llegada en pruebas de carga.
- Configuración concreta del connection pooling en producción (más allá de valores observados) para diseñar pruebas de pool exhaustion.
- Topología de despliegue y afinidades de base de datos en producción que impactan latencia y consistencia.
- Política formal de auditoría de datos geoespaciales sensibles (roles, acceso, trazabilidad).
- Especificación precisa de geocercas (críticas, tolerancias, reglas) y SLAs para alertas de entrada/salida.

Estas brechas no impiden iniciar el testing; sí requieren decisiones de calibración y supuestos documentados que se refinaran con métricas y pruebas incrementales[^1].


## 2. Metodología y taxonomía de pruebas

La metodología combina pruebas unitarias, de integración y end-to-end (E2E), complementadas con pruebas de rendimiento y de seguridad, y validadas en staging y producción. La priorización se alinea con la criticidad operativa: nearest neighbor de efectivos, geocercas con baja latencia, trazabilidad de posiciones y alertas, y rutas optimizadas. El enfoque E2E cubre desde endpoints FastAPI con AsyncSession hasta PostGIS y la capa de observabilidad.

Para el plano asíncrono, se recomiendan fixtures de pytest que gestionen create/drop de la base de test con greenlet_spawn, AsyncSession transactional y client de pruebas (httpx.AsyncClient), aplicando dependency_overrides para pruebas de integración. Este patrón evita errores de “MissingGreenlet” y asegura limpieza de entorno entre casos[^6][^7][^8]. La validación de correctness geoespacial se sustenta en la semántica de funciones y operadores PostGIS[^3][^4].

La Tabla 1 sintetiza el mapa de tipos de prueba versus objetivos, datos, criterios de aceptación, herramientas y métricas clave.

Tabla 1. Mapa de tipos de prueba vs objetivos, datos y criterios
| Tipo de prueba | Objetivos | Datos requeridos | Criterios de aceptación | Herramientas | Métricas clave |
|---|---|---|---|---|---|
| Unitarias (servicio PostGIS) | Exactitud de ST_Distance, ST_DWithin, ST_Intersects, casting a geography, verificación de SRID | Puntos sintéticos con coordenadas válidas e inválidas; casos límite cerca de antimeridiano y polos | Distancias dentro de tolerancias; manejo correcto de CRS; errores controlados | pytest, SQLAlchemy text(), EXPLAIN/ANALYZE local | Tasa de acierto, desviación máxima, tiempo por consulta |
| Integración DB (async) | Uso de índices espaciales, planes de ejecución correctos, fixtures async | Dataset mediano con índice GIST habilitado | Index scan presente donde corresponde; reducción drástica de filas examinadas | pytest, greenlet_spawn, AsyncSession | Porcentaje de consultas con index scan, filas examinadas |
| Integración FastAPI+PostGIS | Endpoints de proximidad, geocercas y tracking; validación de inputs; errores 503/422 | Peticiones con parámetros válidos e inválidos; fixtures de sesión | 200/422/503 correctos; latencia bajo SLO; contenido de respuesta correcto | httpx.AsyncClient, dependency_overrides | Latencia p50/p95/p99, tasa de error, throughput |
| E2E operativo | Proximidad, asignación, tracking, alertas geoespaciales, rutas | Secuencias de eventos (W, WS, Pub/Sub, DB) | SLA de alertas; coherencia de broadcast; consistencia de asignación | TestClient E2E, WS manager, Redis Pub/Sub | Latencia evento→alerta, entrega cross-worker, errores WS |
| Rendimiento (carga/estrés) | Latencia y throughput bajo picos; pool exhaustion; escalabilidad | Datasets grandes; patrones de consulta realistas | P95 bajo SLO; sin errores por pool; degradación controlada | Harness de carga, pg_stat_statements, EXPLAIN ANALYZE | p95/p99, CPU/IO DB, cache hit rate, lock waits |
| Seguridad espacial | Validación, sanitización, acceso y cifrado | Inputs maliciosos, roles y permisos | Rechazo de inputs inválidos; mínimo privilegio; auditoría | Triggers CHECK, constraints, tests de roles | Inyecciones bloqueadas, cobertura de reglas, logs de auditoría |

Subsecciones

### 2.1 Entorno de pruebas y gestión de datos

La estrategia de datos enfatiza datasets reproducibles y control de SRID:
- Creación de base de test con aislamiento por sesión de pruebas y limpieza posterior; uso de greenlet_spawn para operaciones síncronas de meta-create/drop. Este patrón asegura que la base de test esté lista sin romper el loop asíncrono[^6][^7][^8].
- Semillas determinísticas para datos sintéticos de puntos (efectivos y posiciones), garantizando repetibilidad y correlación entre casos de proximidad y geocercas.
- Control explícito de SRID y casting a geography cuando se calculan distancias en metros; verificación de consistencia de unidades y tipos antes de ejecutar assertions.
- Inicialización de la extensión PostGIS y del índice espacial GIST en la base de test, con validaciones automatizadas previas a la ejecución de casos espaciales (precondición de suite).

Esta aproximación permite aislar defectos del servicio geoespacial, del planificador de consultas y del código asíncrono de la API.


## 3. Testing de consultas espaciales operativas

Las consultas espaciales son el núcleo de las capacidades operativas. La cobertura debe incluir proximidad (nearest neighbor y por radio), cálculos geoespaciales (área, longitud), consultas de ubicación de efectivos, geocercas (punto-en-polígono, entrada/salida), y conversión de coordenadas. Una premisa crítica es elegir el tipo y el orden de operadores para aprovechar los índices espaciales, minimizando el cálculo exacto de distancias sobre conjuntos reducidos de candidatos[^3][^4].

La Tabla 2 mapea funciones y operadores a casos de uso, el tipo de índice esperado y el criterio de aceptación.

Tabla 2. Matriz función/operador → caso de uso → índice → criterio
| Función/Operador | Caso de uso | Índice esperado | Criterio de aceptación |
|---|---|---|---|
| <-> (KNN) | Nearest neighbor de efectivos | GIST en geom (geography) | Plan index-aware; candidatos limitados por LIMIT; latencia bajo SLO |
| ST_DWithin | Búsqueda por radio (geocerca circular) | GIST; predicado index-aware | Filtrado por caja delimitadora; cálculo exacto solo en residuo |
| ST_Intersects | Geocercas polyginales y overlay | GIST | Predicado index-aware; reducción de filas y uso de index scan |
| ST_Distance | Cálculo final de distancia | — (no index-aware) | Solo tras pre-filtro; tolerancia respecto a Haversine/OT rastrer |
| ::geography (cast) | Conversión a geography | — | Semántica de distancia en metros; coherencia de unidades |
| ST_SetSRID/ST_MakePoint | Construcción de puntos | — | SRID correcto (4326); consistencia con casos límite |

Tabla 3. Consultas PostGIS utilizadas (semántica y uso)
| Función/Operador | Propósito | Resultado esperado |
|---|---|---|
| ST_SetSRID(.., 4326) | Fijar sistema de coordenadas | Punto con SRID 4326 |
| ST_MakePoint(lng, lat) | Crear punto geográfico | Geometría POINT |
| ::geography | Casting a geography | Cálculo preciso de distancia (metros) |
| ST_Distance(..) | Distancia entre geometrías | Distancia en metros ( geography ) |
| geom <-> point::geography | Ordenación por nearest neighbor | Orden eficiente para LIMIT |

Subsecciones

### 3.1 Proximidad y nearest neighbor

La estrategia estándar para nearest neighbor se basa en el operador <-> con casting a geography y un LIMIT razonable, asegurando un plan index-aware que evita escaneos completos. La semántica de orden por <-> permite al optimizador usar el índice GIST y presentar los K vecinos más cercanos con excelente rendimiento; el cálculo final de distancia puede realizarse con ST_Distance si se requiere el valor exacto en el result set[^9][^3].

Es esencial validar casos límite: antimeridiano (longitudes cercanas a ±180°), proximidad a polos y puntos muy cercanos versus muy lejanos. En datasets heterogéneos, confirmaremos que el orden es consistente con distancias calculadas por ST_Distance y que la latencia bajo carga se mantiene dentro de los objetivos de servicio.

### 3.2 Geocercas operativas

Las geocercas pueden ser circulares (ST_DWithin) o polyginales (ST_Intersects). Para rendimiento y correctness, el patrón recomendado es usar predicados index-aware: ST_DWithin internamente utiliza el operador de caja delimitadora (&&) con expansión, permitiendo al índice reducir el conjunto antes del cálculo final de distancia; ST_Intersects usa el índice para el pre-filtro de bounding boxes y solo entonces evalúa la intersección real[^3]. Las pruebas verifican tolerancia (por ejemplo, 25–50 m) y semántica de pertenencia (entrada/salida), además de latencia de alertas.

### 3.3 Conversión de coordenadas y validación de inputs

La validación de coordenadas debe rejectsar latitud fuera de [-90, 90] y longitud fuera de [-180, 180]. El casting explícito a geography con SRID 4326 garantiza la semántica de medición en metros. Recomendamos constraints CHECK en la tabla de efectivos para asegurar SRID y tipo geométrico (POINT), y triggers para sanitización automática de coordenadas ilegales, reforzando seguridad y calidad de datos[^12][^4][^13]. Casos límite incluyen puntos exactamente en el antimeridiano y polos, donde la proyección y la geodesia pueden producir comportamientos sutiles; las pruebas deben confirmar que la distancia y los predicados se comportan según lo esperado.


## 4. Testing de índices espaciales y optimización

El índice espacial GIST sobre geography/geometry es el principal acelerador de consultas espaciales, basado en R-tree. Su uso se activa con operadores de caja delimitadora (&&) y con operadores y funciones index-aware (<->, ST_DWithin, ST_Intersects). Las pruebas deben verificar que los planes de ejecución usan index scan en los escenarios apropiados, y que la reducción de filas examinadas se traduce en mejoras sustanciales de latencia y CPU[^10][^11][^3].

Buenas prácticas a validar:
- Orden de condiciones en el WHERE que favorezca el predicado espacial index-aware antes de funciones no index-aware (por ejemplo, ST_Distance).
- Análisis y actualización de estadísticas (ANALYZE) después de cargas masivas para que el optimizador elija planes correctos.
- Consideración de tipos de índice alternativos (BRIN) para tablas grandes con datos muy ordenados y baja selectividad, donde el costo de GIST sea prohibitivo, siempre respaldado por EXPLAIN y benchmarks[^10].

La Tabla 4 resume riesgos típicos y estrategias de mitigación.

Tabla 4. Riesgos de índices espaciales y mitigaciones
| Riesgo | Síntoma | Mitigación |
|---|---|---|
| Ausencia de índice GIST | Escaneos completos; latencia alta | Crear GIST sobre geom/geog; verificar uso en EXPLAIN |
| Predicados no index-aware (ST_Distance en WHERE) | CPU alta; tiempo excesivo | Reemplazar por ST_DWithin; ordenar con <-> |
| Estadísticas desactualizadas | Planes subóptimos | Ejecutar ANALYZE post-ingesta; vacuum selectivo |
| Over-indexing | Escrituras lentas; mantenimiento caro | Revisar índices por caso de uso; eliminar redundantes |
| Datos dispersos (selectividad baja) | Index scan aún costoso | Evaluar BRIN; particionar; aumentar selectividad |

### 4.1 Mantenimiento e integridad de índices

Se recomienda un plan periódico de mantenimiento: VACUUM/ANALYZE para actualizar estadísticas y mantener la salud de índices, verificación de integridad (ausencia de corruption), y pruebas de reconstrucción bajo ventanas de mantenimiento controladas. En contextos de ingesta continua, automatizar ANALYZE y monitorear bloat del índice. La coherencia de índices debe formar parte del checklist de despliegue y de pruebas post-migración[^4].


## 5. Testing de transacciones geoespaciales y concurrencia

La corrección en escenarios concurrentes depende de elegir el nivel de aislamiento adecuado y comprender sus implicancias. PostgreSQL implementa Read Committed, Repeatable Read y Serializable (Serializable Snapshot Isolation, SSI). Para operaciones geoespaciales, el diseño transaccional debe prevenir phantom reads, nonrepeatable reads y anomalías de serialización que podrían conducir a asignaciones inconsistentes de efectivos o alertas erróneas[^15][^16][^17].

Casos de prueba:
- Asignación concurrente de un efectivo a una tarea (SELECT FOR UPDATE) para evitar que dos transacciones creen asignaciones duplicadas o choquen al mismo recurso.
- Inserción de posiciones de tracking bajo Repeatable Read para evitar lecturas no repetibles y mantener consistencia de secuencias de puntos.
- Transacciones largas que actualizan geometrías (por ejemplo, geocercas) y cómo se comportan los predicados espaciales; medir la latencia y el impacto en bloqueo y visibilidad.

La Tabla 5 resume niveles de aislamiento, riesgos mitigados y riesgos residuales en operaciones geoespaciales.

Tabla 5. Aislamiento de transacciones → riesgos mitigados → residuales
| Nivel | Anomalías mitigadas | Riesgos residuales |
|---|---|---|
| Read Committed | Dirty reads | Phantom reads; nonrepeatable reads |
| Repeatable Read | Dirty reads; nonrepeatable reads | Phantom reads; posibles serialization anomalies |
| Serializable | Dirty reads; nonrepeatable; phantoms; anomalías SSI | Costo de coordinación; posibles abortos por conflictos |

### 5.1 Rollback y consistencia de datos espaciales

Las pruebas deben cubrir operaciones de inserción/actualización de geometrías que fracasan (por ejemplo, geometría inválida o SRID inconsistente) y confirmar que el rollback deja el índice y las tablas en estado consistente. Se recomienda verificar constraints de validez (CHECK de SRID y tipo), triggers de validación, y que las operaciones de geocerca no generen artefactos en índices ni en estadísticas si la transacción se revierte[^4].


## 6. Testing de integración FastAPI + PostGIS

El servicio geoespacial valida el dialecto y devuelve 503 si PostGIS no está disponible. Las pruebas de integración deben ejercer este comportamiento, además del correcto manejo de connection pooling, retries con Tenacity y circuit breaker, y condiciones de timeout. La estrategia de testing usa AsyncSession, fixtures asíncronas y dependency_overrides, con verificación explícita de 422 (validación), 503 (extensión indisponible) y 5xx (fallos de DB). Se validan además escenarios con y sin Redis (degradación controlada), incluyendo Pub/Sub y WebSockets broadcast[^6][^7][^8][^1].

La Tabla 6 resume la cobertura de endpoints críticos.

Tabla 6. Endpoints geoespaciales críticos → casos → errores esperados → latencia SLO
| Endpoint | Casos de prueba | Errores esperados | Latencia SLO |
|---|---|---|---|
| /geo/nearest | KNN con y sin índice; casos límite | 422 si coords inválidas; 503 si PostGIS caído | p95 < 150 ms (dataset mediano) |
| /geo/geofence | ST_DWithin/ST_Intersects; tolerancia | 422 si payload inválido; 503 si DB no disponible | p95 < 200 ms |
| /geo/track | Inserción de puntos; secuencia temporal | 5xx en conflictos; timeout si pool saturado | p95 < 100 ms por inserción |
| /geo/routes | ST_Intersects overlay; longitud total | 422 si parámetros fuera de rango | p95 < 500 ms |

### 6.1 Pruebas de conexión y pool

La resiliencia del pool se valida con escenarios de exhaustion (simulación de conexiones concurrentes), confirmando que los timeouts se manejan y que los reintentos y circuit breaker evitan cascadas de fallo. Las pruebas deben registrar métricas de espera por conexión y latencias bajo carga, además de verificar que el reciclaje de conexiones (pool_recycle) evita staleness[^1].


## 7. Testing operativo específico

Los casos operativos E2E deben demostrar que la proximidad, asignación, tracking, alertas geoespaciales y optimización de rutas funcionan con la latencia esperada y la semántica correcta. La Tabla 7 define una matriz de cobertura operativa.

Tabla 7. Escenario operativo → datos → predicados → resultado → SLO latencia
| Escenario | Datos | Predicados/funciones | Resultado esperado | SLO latencia |
|---|---|---|---|---|
| Proximidad de efectivos | Puntos de efectivos; consulta (lat, lng) | <->, LIMIT; ST_Distance para valor | Lista de K efectivos ordenados; distancia en metros | p95 < 150 ms |
| Asignación por ubicación | Tareas y efectivos | ST_Within/Intersects; políticas | Efectivo asignado dentro de geocerca | p95 < 200 ms |
| Tracking de movimientos | Secuencia de puntos (tiempo) | Orden temporal; validación | Trayectoria consistente; sin gaps | p95 < 100 ms por inserción |
| Alertas geoespaciales | Geocercas críticas | ST_Intersects/DWithin | Evento de alerta entregado | < 1 s evento→notificación |
| Optimización de rutas | Calles y polígonos | ST_Intersects, ST_Length | Longitud y overlay correctos | p95 < 500 ms |

### 7.1 Proximidad de efectivos

Las pruebas validan el orden de resultados y la distancia precisa en metros. Se compara ST_Distance con aproximaciones (Haversine) solo para establecer tolerancias en la UI; en DB siempre se exige semántica geography con SRID 4326. Se verifica el uso del operador <-> con LIMIT para garantizar index scan y evitar cálculos exhaustivos sobre toda la tabla[^3].


## 8. Performance testing de PostGIS

El diseño de pruebas de carga y estrés debe cubrir consultas complejas con predicados index-aware y medir latencias p50/p95/p99, throughput, CPU, IO y lock waits. Se exploran escenarios de picos concurrentes (por ejemplo, durante eventos públicos), y escalabilidad con datasets masivos. Inspirados en experiencias comparativas, se asume que consultas grandes sin pre-filtro por índice pueden ser CPU-bound y degradar significativamente el tiempo de respuesta; por ello, la narrativa de pruebas se centra en reproducibilidad, tuning y monitoreo continuo[^19][^18][^11].

La Tabla 8 define escenarios de carga y las métricas esperadas.

Tabla 8. Escenarios de carga → dataset → consultas → métricas → umbrales
| Escenario | Dataset | Consultas | Métricas | Umbrales |
|---|---|---|---|---|
| Nearest neighbor (K=5–20) | 10k–1M efectivos | <->, LIMIT; ST_Distance en residuo | Latencia p95/p99; CPU DB; filas examinadas | p95 < 150 ms; index scan |
| Geocercas circulares | 100k puntos | ST_DWithin con radio 200–500 m | Latencia; index hit ratio | p95 < 200 ms; index hit > 90% |
| Overlay y longitud | 250k segmentos | ST_Intersects; ST_Length | CPU; IO; tiempo total | p95 < 500 ms; sin swap |
| Tracking masivo | 1M inserciones | Inserciones async; índices | Throughput; lock waits | > 5k ins/s; waits < 1% |
| Estrés concurrente | 50–200 sesiones | Mezcla de escenarios | Timeouts; circuit breaker | Sin 5xx por pool; degradación controlada |

### 8.1 Profiling y EXPLAIN

Se adoptará un ciclo de profiling sistemático: ejecución de EXPLAIN (ANALYZE) sobre consultas objetivo, interpretación de index scans, buffers y tiempos, tuning del orden de predicados, y verificación de mejoras en métricas. Se sugiere registrar planes antes y después del tuning para evidenciar impacto y evitar regresiones[^11].


## 9. Testing de seguridad espacial

La superficie de ataque en datos geoespaciales incluye coordenadas inválidas, entradas mal formadas y abuso de consultas costosas. Las pruebas de seguridad deben validar restricciones y sanitización, acceso por roles y auditoría de operaciones sensibles. Recomendamos constraints CHECK para rango de coordenadas y SRID, triggers para sanitización automática y denial de inserciones fuera de dominio, y verificación de políticas de mínimo privilegio (RLS) sobre tablas de posiciones y geocercas[^13][^12][^4].

La Tabla 9 mapea controles de seguridad y criterios de prueba.

Tabla 9. Controles de seguridad → ubicación → método de prueba → criterio
| Control | Ubicación | Método de prueba | Criterio |
|---|---|---|---|
| Validación de coords | API/servicio | Envío de lat/lng inválidos | 422 con mensajes claros |
| Sanitización | DB (trigger/CHECK) | Inserción de valores fuera de rango | Rechazo; log de auditoría |
| Mínimo privilegio | Roles/RLS | Acceso con roles no autorizados | Denegación; registro |
| Rate limiting | Middleware | Peticiones masivas geoespaciales | Throttling; 429 |
| Métricas seguras | /metrics | Acceso anónimo/protegido | No exposición de datos sensibles |

### 9.1 Validación y sanitización de coordenadas

Las pruebas deben simular inyecciones de coordenadas ilegales y verificar rechazo seguro. Se recomienda un trigger a nivel de tabla que imponga el dominio [-90,90] y [-180,180] y rechace registros fuera de SRID 4326 para tablas operativas de efectivos y posiciones. Las pruebas incorporan casos límite como antimeridiano y polos para asegurar que la sanitización no rompe la semántica espacial[^13].


## 10. Observabilidad, métricas y alertas para testing

El sistema expone métricas y health checks que deben integrarse a la narrativa de pruebas: latencias de endpoints geoespaciales, tasas de error, conexiones WS, broadcasts y comportamiento del pool de DB. Los dashboards deben correlacionar índices espaciales con latencia y throughput, y las alertas deben cubrir disponibilité, lentitud y saturación. Las pruebas verifican la instrumentación (contadores, gauges, histogramas) y su exposición en /metrics, además de la semántica de /health/ready y degradaciones controladas[^1].

La Tabla 10 presenta un catálogo de métricas relevantes para este plan.

Tabla 10. Métricas → fuente → etiquetas → umbral → uso
| Métrica | Fuente | Etiquetas | Umbral | Uso |
|---|---|---|---|---|
| Latencia p95 endpoints geo | API/Prom | endpoint, env | < 150–200 ms | SLO de proximidad/geocercas |
| Throughput consultas espaciales | DB/Prom | query_type, env | > X req/s | Capacidad operativa |
| Conexiones DB en uso | DB exporter | env | < 80% pool | Evitar exhaustion |
| Index usage (spatial) | pg_stat_statements | env | > 90% index-aware | Validar tuning |
| WS broadcasts totales | App/Prom | env | Tendencia estable | Coherencia cross-worker |
| Errores WS (send_errors) | App/Prom | env | ~0 | Calidad de entrega |
| Cache hit rate | Redis exporter | env | > 85% | Eficiencia de lectura |

### 10.1 Integración de pruebas y observabilidad

Se propone instrumentar harness de pruebas para registrar latencias, errores y eventos clave, correlacionarlos con health y métricas, y generar reportes post-ejecución. Este enfoque cerrará el ciclo de verificación: de la especificación y el código a los dashboards y alertas, con evidencia empírica de cumplimiento.


## 11. Plan de implementación y cronograma

El plan de implementación se estructura por fases con entregables claros y criterios de salida. Se prioriza quick wins en configuración y validación de PostGIS, luego tuning de performance y seguridad, y finalmente cobertura avanzada y compliance.

Quick wins (0–30 días):
- Validación de PostGIS y creación automatizada de índice espacial en migraciones; health check bloqueante en ausencia de extensión.
- Endurecimiento de CORS y políticas de rate limiting; verificación de métricas sensibles en /metrics.
- Estandarización de health/ready con dependencias requeridas vs opcionales.

Mediano plazo (30–90 días):
- Tuning de pool por entorno; pruebas de estrés con escenarios realistas; ajustes en predicados y orden de consultas.
- Retiro de fallbacks TLS inseguros de Redis en producción; consolidación de configuraciones multi-entorno.
- Cobertura de pruebas hacia 85% en módulos geoespaciales y WS.

Largo plazo (90–180 días):
- Auditoría y compliance: correlación de logs, retención, cobertura de auditoría de acceso a datos sensibles.
- Pruebas sistemáticas de carga continua; documentación de políticas de gestión de secretos y operación.

La Tabla 11 detalla el cronograma y la Definition of Done por fase.

Tabla 11. Fases → tareas → entregables → responsable → Definition of Done
| Fase | Tareas | Entregables | Responsable | DoD |
|---|---|---|---|---|
| 0–30 | PostGIS+índice; health/ready; CORS | Migration automatizada; endpoint de health robusto | Backend/DevOps | 100% tests unitarios geo pasan; health bloquea sin PostGIS |
| 30–90 | Pool tuning; estrés; TLS Redis | Informe de carga; configuración endurecida | Backend/DBA/DevOps | p95 bajo SLO; 0 fallbacks inseguros |
| 90–180 | Auditoría; cobertura 85%; runbooks | Políticas y trazabilidad; dashboards | SecOps/DBA/QA | Auditoría activa; cobertura ≥ 85%; alertas configuradas |

### 11.1 Estrategia de datos de prueba

Se generarán datasets sintéticos con puntos distribuidos (uniformes y clusterizados) y casos límite (antimeridiano, polos). Para escalabilidad, se prevé dataset grande en staging con tamaño gradual (10k→1M) y tiempo de preparación controlado, midiendo impacto en índice y planificador. Se garantizará reproducibilidad mediante semillas y scripts de carga, y limpieza post-ejecución[^1].


## 12. Traceability, riesgos y Definition of Done

La matriz de trazabilidad alinea requisitos, casos de prueba, datos, criterios y resultados esperados. Los riesgos se clasifican por severidad y probabilidad, con mitigaciones y planes de contingencia. La Definition of Done para geolocalización operativa incluye cobertura, precisión, latencia, disponibilidad, seguridad y observabilidad.

La Tabla 12 resume la matriz de trazabilidad y la Tabla 13 el registro de riesgos.

Tabla 12. Matriz de trazabilidad
| Requisito | Caso de prueba | Datos | Criterio | Resultado esperado |
|---|---|---|---|---|
| Nearest neighbor | KNN con <-> y LIMIT | 10k puntos | p95 < 150 ms; orden correcto | Lista con distancias exactas |
| Geocerca circular | ST_DWithin radio 200 m | 100k puntos | Index scan; p95 < 200 ms | Alertas sin falsos negativos |
| Geocerca poligonal | ST_Intersects | Polígonos + puntos | Predicado index-aware | Pertenencia correcta |
| Tracking | Inserción secuencial | 1M puntos | Sin pérdida; consistencia | Trayectoria ínteg ra |
| Rutas | Overlay+longitud | 250k segmentos | p95 < 500 ms | Métrica de longitud exacta |

Tabla 13. Registro de riesgos
| Riesgo | Severidad | Probabilidad | Mitigación | Responsable | Estado |
|---|---|---|---|---|---|
| Índice GIST ausente en prod | Alta | Media | Migration gated; health check | DBA/DevOps | Pendiente |
| Pool exhaustion | Alta | Media | Tuning; circuit breaker; tests | Backend/DevOps | En curso |
| Inputs ilegales | Alta | Media | CHECK+triggers; validación API | Backend/SecOps | Planificado |
| Estadísticas desactualizadas | Media | Media | ANALYZE/VACUUM automatizado | DBA | En curso |
| Fallback TLS Redis | Alta | Baja | Endurecimiento TLS; eliminar fallback | DevOps | En curso |


## Referencias

[^1]: GRUPO_GAD — Aplicación en Fly.io. https://grupo-gad.fly.dev  
[^2]: Repositorio GRUPO_GAD — GitHub. https://github.com/eevans-d/GRUPO_GAD  
[^3]: PostGIS Documentation: Chapter 5. Spatial Queries. https://postgis.net/docs/using_postgis_query.html  
[^4]: PostGIS Documentation: Chapter 4. Data Management. https://postgis.net/docs/using_postgis_dbmanagement.html  
[^5]: PostGIS Manual (PDF). https://postgis.net/stuff/postgis-3.5-en.pdf  
[^6]: How to use PostgreSQL test database in async FastAPI tests? (Stack Overflow). https://stackoverflow.com/questions/70752806/how-to-use-postgresql-test-database-in-async-fastapi-tests  
[^7]: Developing and Testing an Asynchronous API with FastAPI and Pytest (TestDriven.io). https://testdriven.io/blog/fastapi-crud/  
[^8]: Testing FastAPI with async database session (DEV Community). https://dev.to/whchi/testing-fastapi-with-async-database-session-1b5d  
[^9]: A Deep Dive into PostGIS Nearest Neighbor Search (Crunchy Data). https://www.crunchydata.com/blog/a-deep-dive-into-postgis-nearest-neighbor-search  
[^10]: Spatial Indexing — Introduction to PostGIS (Workshop). http://postgis.net/workshops/postgis-intro/indexing.html  
[^11]: PostGIS Performance: Indexing and EXPLAIN (Crunchy Data). https://www.crunchydata.com/blog/postgis-performance-indexing-and-explain  
[^12]: Using PostGIS: Data Management and Queries (Manual 1.4). https://postgis.net/docs/manual-1.4/ch04.html  
[^13]: Auto-Sanitizing illegal PostGIS WGS84 (lat, lon) coordinates (GIS Stack Exchange). https://gis.stackexchange.com/questions/149223/auto-sanitizing-illegal-postgis-wgs84-lat-lon-coordinates  
[^14]: How do I perform a proximity search with PostGIS? (GIS Stack Exchange). https://gis.stackexchange.com/questions/21903/how-do-i-perform-a-proximity-search-with-postgis  
[^15]: PostgreSQL Documentation: Transaction Isolation. https://www.postgresql.org/docs/current/transaction-iso.html  
[^16]: Transaction Isolation in Postgres (Medium). https://medium.com/@darora8/transaction-isolation-in-postgres-ec4d34a65462  
[^17]: Database Concurrency in PostgreSQL (Simple Talk). https://www.red-gate.com/simple-talk/databases/postgresql/database-concurrency-in-postgresql/  
[^18]: postgis-performance — OSGeo Gitea. https://gitea.osgeo.org/postgis/postgis-performance  
[^19]: Geospatial Query Performance Test of Presto and PostGIS (Medium). https://uprush.medium.com/geospatial-query-performance-test-of-presto-and-postgis-d9bf2825e56a