# Auditoría Técnica y de Cumplimiento del Telegram Bot Gubernamental en GRUPO_GAD

## Resumen Ejecutivo

Este informe presenta una auditoría técnica y de cumplimiento del canal ciudadano basado en Telegram Bot dentro de GRUPO_GAD. El objetivo es evaluar, con enfoque de producción gubernamental, la arquitectura del bot, sus funcionalidades y flujos críticos, el nivel de cumplimiento y seguridad, la integración con el backend (FastAPI, PostGIS, Redis y WebSockets), la escalabilidad y la calidad de pruebas. El análisis se fundamenta en evidencia extraída del repositorio oficial del proyecto y de artefactos operativos relacionados, complementado por el inventario de integraciones y la línea base de seguridad previamente establecidos.[^1][^2]

A nivel de arquitectura, el bot adopta python-telegram-bot con un diseño modular que separa comandos, handlers, servicios de API y utilidades de interfaz (inline keyboards). La comunicación con el backend se apoya en endpoints expuestos por FastAPI y utiliza un servicio de API sincrónico basado en requests para operaciones de tareas y usuarios. La gestión del estado conversacional del wizard se implementa en memoria (context.user_data), sin persistencia explícita en Redis. La interfaz de usuario prioriza teclados inline con callbacks y patrones de paginación. El logging utiliza Loguru con rotación y retención definidas. Las pruebas unitarias y de integración reportan cobertura del 70%+ y validan aspectos clave del wizard, teclados y flujos básicos.[^1][^2]

No obstante, el diseño actual presenta riesgos y brechas que deben abordarse antes del go-live en un entorno crítico. Entre las debilidades más relevantes: uso de requests (sincrónico) en el servicio de API del bot; ausencia de persistencia de sesión del wizard en Redis; carencia de cifrado en reposo verificado para datos ciudadanos; y un audit trail insuficiente para cumplimiento gubernamental. La autorización de ciudadanos descansa en variables y prácticas de lista blanca (WHITELIST_IDS) sin evidencias de un flujo formal de autenticación/autorización adaptado al canal Telegram.[^2]

Las recomendaciones priorizadas se orientan a: migrar el servicio de API del bot a un cliente asíncrono; persistir el estado del wizard en Redis con TTL y namespaces; fortalecer la seguridad con rate limiting basado en Redis, rotación/gestión de secretos en Vault/Secrets Manager y endurecimiento de TLS; completar el compliance con un audit trail integral y cifrado en reposo; y elevar la cobertura de pruebas por encima del 85%, incorporando tests de carga y resiliencia.

Para sintetizar el nivel de preparación por dimensión, la siguiente tabla presenta un scorecard ejecutivo:

Tabla 1. Scorecard ejecutivo por dimensión

| Dimensión                    | Estado | Evidencia clave                                                                 | Riesgo principal                                         | Recomendación prioritaria                                     |
|-----------------------------|--------|----------------------------------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------------|
| Arquitectura                | Medio  | Estructura modular, routing por callbacks, wizard en memoria, logging con Loguru | Estado de wizard no persistente; dependencia sincrónica  | Persistir wizard en Redis; migrar ApiService a cliente async   |
| Funcionalidades             | Medio  | Menú principal, creación y finalización de tareas, historial, ayuda              | Inconsistencias de integración (API legacy vs nueva)     | Unificar endpoints y estandarizar contratos                   |
| Seguridad y Compliance      | Medio  | JWT en API, middlewares de seguridad, whitelisting                               | Cifrado en reposo no verificado; audit trail incompleto  | Implementar cifrado en reposo y audit logging integral        |
| Integración con Backend     | Medio  | Endpoints FastAPI; PostGIS y Redis disponibles                                   | Cliente API sincrónico; WebSockets no instrumentados     | Cliente async, instrumentación WS y validación PostGIS/Redis  |
| Escalabilidad y Performance | Medio  | Redis cache/pub-sub; Observabilidad Prometheus/Grafana                           | Estado en memoria limita horizontal; rate limiting local | Rate limiting con Redis, benchmarks, afinado de paginación    |
| Calidad y Pruebas           | Alto   | 11 archivos de test; 70%+ cobertura                                              | Pruebas de carga/resiliencia no evidenciadas             | Elevar a 85%+, incluir carga/sobresaturación/recuperación     |

En conjunto, el sistema demuestra preparación y buenas prácticas, pero requiere cerrar brechas de seguridad, persistencia y cumplimiento antes de su uso en un contexto gubernamental de misión crítica.[^1][^2]

## Metodología y Alcance

La auditoría se realizó mediante revisión dirigida del código del bot y artefactos de configuración, complementada con la lectura del inventario de integraciones y de la línea base de seguridad. Se priorizaron los componentes con mayor impacto en cumplimiento, trazabilidad y escalabilidad: comandos del bot, handlers (incluido el wizard multistep), servicios de API, teclados inline y patrones de callback. A nivel de backend, se examinó la interacción con FastAPI y servicios geoespaciales (PostGIS), así como el uso de Redis para cache y pub/sub con WebSockets.[^1][^2]

Los criterios de evaluación incluyeron: seguridad de datos personales, auditabilidad de acciones, separación de responsabilidades, observabilidad y gobernanza de cambios. Se consideraron, además, restricciones gubernamentales de cumplimiento, la criticidad de disponibilidad y la necesidad de trazabilidad exhaustiva. Las principales limitaciones del análisis fueron: ausencia de métricas operativas en producción; falta de verificación directa de cifrado en reposo; y carencia de evidencia de pruebas de carga y resiliencia. Estos vacíos se reconocen como gaps y se abordan en las recomendaciones.

## Arquitectura del Telegram Bot

El bot está construido sobre python-telegram-bot con una separación nítida entre punto de entrada, handlers, servicios de integración y utilidades. Esta modularidad favorece el mantenimiento y la evolución, aunque la comunicación sincrónica con la API y la gestión del estado del wizard en memoria constituyen riesgos para escalabilidad y consistencia en despliegues horizontales.[^1]

Tabla 2. Mapa de componentes del bot

| Directorio/Archivo                 | Responsabilidad principal                                     | Dependencias destacadas                       | Notas de implementación                                                                 |
|-----------------------------------|---------------------------------------------------------------|-----------------------------------------------|------------------------------------------------------------------------------------------|
| src/bot/main.py                   | Punto de entrada, inicialización de Application y logging     | python-telegram-bot, Loguru, settings         | run_polling, validación de TELEGRAM_TOKEN, registro de handlers                         |
| src/bot/commands/*                | Handlers de comandos (/start, /help, /crear, /finalizar, etc) | ApiService, KeyboardFactory                    | Comandos con parsing y ayuda contextual                                                  |
| src/bot/handlers/*                | Procesamiento de callbacks y wizard de texto                  | KeyboardFactory, wizard_text_handler           | Router por callbacks con patrón {action}:{entity}:{id}; wizard multistep                |
| src/bot/handlers/messages/*       | Manejo general de mensajes                                    | —                                             | Punto de extensión para flujos no conversacionales                                       |
| src/bot/services/api_service.py   | Cliente HTTP sincrónico hacia FastAPI                         | requests, endpoints /auth, /tasks, /users      | Autenticación Bearer opcional; manejo de errores y timeouts                              |
| src/bot/utils/keyboards.py        | Factory de inline keyboards                                   | InlineKeyboardButton/Markup                    | Patrones de paginación, confirmación, selección de usuarios                             |
| src/bot/utils/emojis.py           | Emojis semánticos                                             | —                                             | Mejora de UX con consistencia visual                                                     |

### Punto de Entrada y Bootstrap

El arranque valida la presencia del TELEGRAM_TOKEN y crea la Application de python-telegram-bot. Se registra un conjunto de handlers y se inicia el bucle de polling. La configuración de logging con Loguru direciona la salida a consola con formato coloreado y a un archivo con rotación y retención definidas, aportando trazabilidad operacional.[^1]

### Registro de Handlers y Routing

El registro consolida comandos, callback queries y el manejador de texto del wizard. El router de callbacks interpreta cadenas con formato {action}:{entity}:{id}, lo que simplifica el mapeo de acciones a funciones específicas. El flujo de creación de tareas se articula en un wizard de seis pasos, con estado mantenido en context.user_data y validaciones de entrada por paso. Este diseño permite una experiencia guiada y reduce errores de captura, aunque depende de la memoria local del proceso.[^1]

Tabla 3. Catálogo de callbacks por acción/entidad

| Prefijo de acción | Entidad             | Ejemplo de callback_data             | Función/handler asociado                     | Comentario funcional                                |
|-------------------|---------------------|--------------------------------------|----------------------------------------------|-----------------------------------------------------|
| menu              | main/crear/finalizar/tareas/ayuda | menu:crear:start                      | handle_menu_action                           | Navegación del menú principal y submenús            |
| crear             | tipo/delegado/asignado/confirm/cancel | crear:tipo:OPERATIVO                   | handle_crear_action                          | Wizard de creación paso a paso                      |
| finalizar         | list/select/confirm/cancel         | finalizar:select:T001                 | handle_finalizar_action                      | Selección y confirmación de tareas a finalizar      |
| page              | <número>                              | page:1                                | handle_pagination_action                     | Paginación en listas de tareas                      |

### Wizards Multi-Step

El wizard estructura la creación de tareas en seis etapas: selección del tipo, ingreso de código, título, delegado, asignados y confirmación. Cada paso aplica validaciones específicas (longitud, formato, obligatoriedad) y utiliza ayuda contextual y barras de progreso. El estado se guarda en context.user_data, con limpieza al confirmar o cancelar. Esta aproximación ofrece buena UX, pero carece de persistencia fuera del proceso, lo que limita la resiliencia y la continuidad en escenarios de reinicio o escalado horizontal.[^1]

Tabla 4. Mapa de pasos del wizard

| Paso | Validaciones clave                                | Transición                                  | Controles de UI                              |
|------|----------------------------------------------------|---------------------------------------------|----------------------------------------------|
| 1    | Selección de tipo de tarea                        | Avanzar al paso 2                           | Teclado de tipos                             |
| 2    | Código: longitud 3–20 caracteres                  | Avanzar al paso 3 si válido                 | Solicitud de texto + botón “Volver”          |
| 3    | Título: 10–100 caracteres                         | Avanzar al paso 4 si válido                 | Solicitud de texto                           |
| 4    | Delegado: ID numérico                             | Avanzar al paso 5 si válido                 | Solicitud de texto                           |
| 5    | Asignados: lista de IDs numéricos (no vacía)      | Avanzar al paso 6 si válido                 | Solicitud de texto                           |
| 6    | Confirmación de datos (resumen visual)            | Creación/Edición/Cancelar                   | Teclado de confirmación                      |

### Teclados Inline y UX

El KeyboardFactory produce teclados consistentes con emojis semánticos y patrones de callback predecibles. La paginación en listas evita mensajes excesivamente largos y mejora la navegación; los teclados de confirmación ofrecen rutas claras para crear, editar o cancelar. En pruebas se valida que el tamaño de callback_data cumple el límite de 64 bytes, evitando rechazos de Telegram.[^1]

Tabla 5. Inventario de teclados

| Nombre                  | Propósito                         | Estructura de filas                              | Uso en flujos                         |
|------------------------|-----------------------------------|--------------------------------------------------|---------------------------------------|
| main_menu              | Navegación principal              | 5 botones (crear, completar, tareas, ayuda)      | /start, retorno desde submenús        |
| task_types             | Selección de tipo de tarea        | 3 tipos + cancelar                               | Paso 1 del wizard                     |
| task_confirmation      | Confirmación de creación          | [Sí, Crear / Revisar y Editar] + [Cancelar]      | Paso 6 del wizard                     |
| confirmation           | Confirmación genérica             | [Sí/No]                                          | Finalización de tareas                |
| back_button            | Retroceso                         | 1 botón                                          |通用, retorno a menú                   |
| paginated_list         | Lista con navegación              | items + [Anterior/Siguiente] + volver            | Historial, tareas pendientes          |
| user_selector          | Selección de usuario              | Lista de usuarios + cancelar                     | Selector de delegado/asignados        |
| multi_select_users     | Selección múltiple                | checkboxes + [Continuar] + cancelar              | Asignados                             |

### Servicio de API y Legacy

El servicio de API del bot utiliza requests (sincrónico), con métodos para crear y finalizar tareas, consultar tareas pendientes por telegram_id y obtener usuarios por rol. Se observa una inconsistencia de nombres de parámetro en el constructor (base_url vs api_url) y la presencia de api_legacy, lo que sugiere deuda técnica que conviene resolver mediante unificación de contratos y migración a un cliente asíncrono alineado con FastAPI. Los endpoints inferidos incluyen autenticación y operaciones de tareas/usuarios.[^1]

Tabla 6. Endpoints consumidos por el bot

| Método HTTP | Ruta                               | Payload principal                       | Respuesta esperada           | Manejo de errores            |
|-------------|------------------------------------|-----------------------------------------|------------------------------|------------------------------|
| GET         | /auth/{telegram_id}                | —                                       | nivel de autenticación       | Excepción RequestException   |
| POST        | /tasks/create                      | TareaCreate (codigo, título, tipo, etc.)| Tarea creada                 | response.raise_for_status    |
| POST        | /tasks/finalize                    | task_code, telegram_id                  | Tarea finalizada             | Diferenciación 404/403       |
| GET         | /tasks/user/telegram/{telegram_id} | status=pending                          | Lista de tareas pendientes   | Retorna lista vacía en error |
| GET         | /users                             | role (opcional)                         | Lista de usuarios            | Retorna lista vacía en error |

### Logging y Observabilidad del Bot

El bot adopta Loguru con salida a consola y archivo, incluyendo rotación, retención, colas y diagnóstico. Esta configuración favorece la trazabilidad en producción y facilita la correlación con métricas de plataforma (Prometheus) y paneles (Grafana). Sin embargo, no se evidencian métricas específicas del bot exportadas a Prometheus; se recomienda instrumentación dedicada para comandos, callbacks y wizard (latencia, throughput, errores), con etiquetas por entorno y por usuario/rol donde aplique.[^1][^2]

## Funcionalidades Gubernamentales

El catálogo de funcionalidades abarca la interacción ciudadana para la creación, finalización y consulta de tareas, con ayudas contextuales y navegación por menús. La integración con datos gubernamentales se produce a través de endpoints de la API, con validaciones en el wizard y uso de teclados para guiar la experiencia. Las consultas geoespaciales están disponibles en el backend mediante PostGIS, si bien no se observa consumo directo desde el bot; la autorización se apoya en prácticas de whitelisting y autenticación general de la plataforma.[^1][^2]

Tabla 7. Catálogo de comandos

| Comando        | Propósito                         | Validaciones principales                  | Endpoint/API asociado                | Manejo de errores                     |
|----------------|-----------------------------------|-------------------------------------------|--------------------------------------|---------------------------------------|
| /start         | Bienvenida y menú principal       | update.message no nulo                    | —                                    | N/A                                   |
| /help          | Ayuda general y contextual        | Detecta wizard activo                     | —                                    | N/A                                   |
| /crear         | Crear tarea (texto)               | Args length ≥ 5, tipos válidos            | /tasks/create                        | Excepciones por parsing y API         |
| /finalizar     | Finalizar tarea (texto)           | Args length = 1                           | /tasks/finalize                      | Diferenciación 404/403                |
| /historial     | Historial del usuario             | Filtros válidas (todas/activas/finalizadas)| /tasks/user/telegram/{telegram_id}   | Mensaje de error genérico             |

Tabla 8. Flujos ciudadanos clave

| Caso de uso                   | Pasos principales                                 | Puntos de validación                   | Riesgos                                 |
|------------------------------|----------------------------------------------------|----------------------------------------|-----------------------------------------|
| Crear tarea (wizard)         | Tipo → código → título → delegado → asignados → confirmación | Código 3–20; título 10–100; IDs numéricos | Estado en memoria; inputs no verificados por API |
| Finalizar tarea              | Lista paginada → selección → confirmación         | Código de tarea existente               | Permisos; tarea no encontrada            |
| Consultar historial          | Filtro → listado paginado                         | Filtro válido                            | Latencia; volumen de datos               |

### Servicios Ciudadanos

El menú principal facilita el acceso a creación, finalización y consultas. La creación guiada minimiza errores de captura mediante validaciones y feedback visual; la finalización asegura que el usuario confirme la acción. El historial, con filtros y paginación, proporciona visibilidad del estado de las tareas. Las ayudas contextuales por paso del wizard mejoran la comprensión y la eficiencia del flujo.[^1]

### Integración con Datos Gubernamentales

El bot llama a endpoints de autenticación, tareas y usuarios. Se emplea TareaCreate como esquema para la creación. Las validaciones del wizard reducen la probabilidad de errores en backend, si bien falta consistencia en contratos entre servicios y el uso de api_legacy sugiere necesidad de unificación de la interfaz.[^1]

### Consulta Geoespacial

El backend expone PostGIS con una función principal para búsqueda de efectivos cercanos (find_nearest_efectivo), validando coordenadas y utilizando tipos geography para cálculos precisos. Se implements con asyncpg y un query que ordena por distancia con ST_Distance. No se evidencia el consumo directo de esta capacidad desde el bot, lo que representa una oportunidad de ampliar la utilidad geoespacial en el canal ciudadano.[^2]

### Autorización para Ciudadanos

La autorización se apoya en variables de entorno como WHITELIST_IDS y ADMIN_CHAT_ID, junto con autenticación JWT en la API. Falta un flujo claro de verificación de identidad y permisos específicos desde el bot a endpoints de autorización; esto debe formalizarse para cumplir estándares gubernamentales de control de acceso y trazabilidad.[^2]

## Seguridad y Compliance

El tratamiento de datos personales del ciudadano (identificadores de Telegram, atributos de tareas) debe alinearse con principios de minimización, propósito y seguridad. La plataforma cuenta con prácticas de seguridad base (JWT, middlewares, CORS), pero persisten brechas relevantes: cifrado en reposo no verificado, audit trail incompleto para acciones del bot, token de Telegram sin rotación documentada y rate limiting in-memory con límites gubernamentales no instrumentados en el bot. Además, el uso de requests sin validación explícita de TLS y la ausencia de persistencia de sesión dificultan controles de seguridad y cumplimiento.[^1][^2]

Tabla 9. Matriz de cumplimiento

| Control                         | Estado actual                                     | Evidencia                                 | Riesgo                                    | Recomendación                                    |
|--------------------------------|---------------------------------------------------|-------------------------------------------|-------------------------------------------|--------------------------------------------------|
| Cifrado en tránsito            | Implementado (HTTPS/Reverse proxy)                | Middlewares, despliegue en producción     | Bajo                                      | Mantener y reforzar TLS                          |
| Cifrado en reposo              | Por verificar                                     | No evidenciado en inventario              | Alto                                      | Habilitar cifrado en BD y backups                |
| Audit trail                    | Parcial                                           | Logging estructurado, sin eventos de negocio | Alto                                      | Implementar audit logging por acción             |
| Gestión de secretos            | Variables de entorno con rotación                 | CI/CD y configuración por entorno         | Medio                                     | Vault/Secrets Manager; rotación documentada      |
| Rate limiting                  | In-memory con política gubernamental              | Middleware de la API                      | Medio                                     | Migrar a Redis para multi-worker                 |
| Autorización ciudadana         | Prácticas de whitelisting                          | Variables WHITELIST_IDS/ADMIN_CHAT_ID     | Alto                                      | Flujo de authz formal y trazable                 |

Tabla 10. Riesgos de seguridad priorizados

| Riesgo                                  | Criticidad | Probabilidad | Impacto | Score | Acción requerida                                      |
|-----------------------------------------|------------|--------------|---------|-------|-------------------------------------------------------|
| Cifrado en reposo no verificado         | Alto       | Media        | Alto    | 8/10  | Implementar y verificar cifrado en BD y backups       |
| Audit trail incompleto                  | Alto       | Alta         | Alto    | 9/10  | Audit logging integral de acciones del bot            |
| Token de Telegram sin rotación          | Medio      | Media        | Medio   | 6/10  | Rotación y gestión de secretos centralizada           |
| Rate limiting in-memory                 | Medio      | Alta         | Medio   | 7/10  | Migrar a Redis; monitoreo de límites                  |
| Cliente API sincrónico                  | Medio      | Media        | Medio   | 6/10  | Migrar a cliente async con timeouts robustos          |

### Datos Ciudadanos y Minimización

Los identificadores de Telegram y los datos capturados por el wizard deben limitarse a lo estrictamente necesario para el propósito gubernamental, con políticas de retención y anonimización cuando corresponda. Es indispensable establecer un ciclo de vida de datos y mecanismos de borrado a solicitud del ciudadano, en coherencia con la normativa aplicable.[^2]

### Cifrado y Protección de Datos

El cifrado en tránsito se considera implementado, pero el cifrado en reposo requiere verificación y activación explícita en la base de datos y en los backups. El transporte hacia la API debe forzar HTTPS con validación de certificados. Se recomienda un proceso de evaluación y prueba para confirmar el estado de cifrado en reposo y su impacto en rendimiento.[^2]

### Logs de Auditoría

Se requiere un audit trail detallado que capture quién hizo qué, cuándo y sobre qué entidad, con correlación al usuario de Telegram y al registro de la tarea. La trazabilidad debe abarcar creación, modificación, finalización y consultas, integrándose con la observabilidad y alertas de seguridad.[^2]

## Integración con Backend

La integración con FastAPI se materializa a través de un servicio de API del bot que utiliza requests. Esta decisión, aunque funcional, es inconsistente con el paradigma asíncrono del resto del stack y puede limitar el throughput bajo carga. Redis se emplea para cache y pub/sub con WebSockets, mientras que el estado del wizard no se persiste, lo que impide recuperación tras reinicios o balanceo. La capa de observabilidad está disponible mediante Prometheus/Grafana, con necesidad de instrumentar métricas específicas del bot.[^1][^2]

Tabla 11. Mapa de integración

| Origen (bot)         | Destino (servicio) | Protocolo | Método/Endpoint                  | Payload/Query                      | Manejo de errores                    |
|----------------------|--------------------|-----------|----------------------------------|------------------------------------|--------------------------------------|
| ApiService           | FastAPI            | HTTP      | /auth/{telegram_id}              | —                                  | RequestException                     |
| ApiService           | FastAPI            | HTTP      | /tasks/create                    | TareaCreate                        | response.raise_for_status            |
| ApiService           | FastAPI            | HTTP      | /tasks/finalize                  | task_code, telegram_id             | Diferenciación 404/403               |
| ApiService           | FastAPI            | HTTP      | /tasks/user/telegram/{telegram_id}| status=pending                    | Lista vacía en error                 |
| RedisWebSocketPubSub | Redis              | Redis     | publish/subscribe                | message_dict (JSON)                | Reconexión y fallback TLS            |
| CacheService         | Redis              | Redis     | get/set/delete/clear/stats       | key/value (JSON)                   | Hit/miss y métricas                  |

### FastAPI

Los endpoints de autenticación, tareas y usuarios constituyen la superficie de integración. Los esquemas Tarea/TareaCreate son el contrato de datos principal. Se recomienda formalizar y documentar estos contratos (incluyendo códigos de error y semántica de permisos) y migrar el cliente del bot a un cliente HTTP asíncrono con timeouts y reintentos robustos.[^1]

### PostGIS

La función find_nearest_efectivo opera sobre geografía con SRID 4326 y retorna distancia en metros, aplicando ordenación por proximidad. Es una base sólida para servicios de localización de efectivos; el bot puede beneficiarse de un endpoint específico para consultar la ubicación más cercana y desplegar casos de uso como asignación de tareas por proximidad.[^2]

### Redis (Cache y Pub/Sub)

El CacheService ofrece serialización JSON, TTL y prefijos, con estadísticas de hit/miss y reconexión configurable. El RedisWebSocketPubSub realiza difusión cross-worker con reconexión y fallback TLS, útil para escalado de WebSockets. La estrategia de fallback a puerto 6380 para proveedores cloud debe acompañarse de políticas de seguridad adecuadas y verificación de cifrado en tránsito.[^2]

### WebSockets

La integración via Redis Pub/Sub permite sincronizar mensajes entre workers y clientes. La observabilidad debe incluir métricas de conexiones activas, latencias y errores de envío; la instrumentación en el bot puede beneficiarse de reportes de callbacks procesados, pasos de wizard completados y éxito/fracaso de llamadas a la API.[^2]

## Escalabilidad y Performance

El bot utiliza polling y handlers asíncronos en python-telegram-bot, pero el servicio de API sincrónico introduce un cuello de botella potencial. La paginación en listas es una buena práctica, aunque el estado en memoria del wizard puede perderse al escalar horizontalmente. El middleware de rate limiting gubernamental existe en la API; falta su aplicación explícita en el bot y su persistencia con Redis para entornos multi-worker.[^1][^2]

Tabla 12. Patrones de escalado

| Componente            | Recurso/Patrón        | Límite actual                           | Riesgo                                | Optimización propuesta                                  |
|-----------------------|-----------------------|------------------------------------------|---------------------------------------|---------------------------------------------------------|
| Bot polling           | Async handlers        | No evidenciado límite de throughput      | Bloqueos por I/O sincrónica           | Cliente API async; backoff; reintentos                  |
| Wizard state          | context.user_data     | En memoria, sin persistencia             | Pérdida por reinicios/balanceo        | Persistir en Redis con TTL y namespace                  |
| Listas paginadas      | Inline keyboards      | Page size fijo (p. ej., 5)               | UX lenta con volumen alto             | Afinar page_size; cache de listados                     |
| Rate limiting         | Middleware API        | In-memory (no evidenciado en bot)        | Spoofing por múltiples workers        | Rate limiting con Redis; etiquetas por usuario/IP       |

### Múltiples Usuarios y Carga

Se requiere validar el throughput bajo carga, especialmente en flujos de wizard y callbacks con llamadas a API. Es recomendable instrumentar métricas por comando y por callback, y evaluar el rendimiento del servicio de API del bot bajo concurrencia elevada. La persistencia del wizard en Redis permitirá que sesiones activas sobrevivan a reinicios o escalado horizontal.[^1]

### Recovery y Errores

El manejo de errores en el callback de finalización diferencia 404 y 403 para ofrecer mensajes más claros, lo cual es una buena práctica. Se sugiere adoptar un patrón uniforme de gestión de errores en todos los flujos del bot, con trazabilidad por correlation ID y respuestas degradadas cuando servicios externos fallen.[^1]

### Rate Limiting

Los límites gubernamentales definidos en la API deben aplicarse al bot, con persistencia en Redis y métricas asociadas. Es crítico evitar el bypass por múltiples workers y garantizar que las cuotas se contabilicen por usuario/IP y tipo de operación (comandos, callbacks, wizard).[^2]

## Testing y Calidad

El bot cuenta con una suite de 11 archivos de test y cobertura reportada del 70%+. Las pruebas cubren /start, teclados, wizard multistep, callbacks y finalización de tareas, con fixtures asíncronos y mocking de API. Se verifica el límite de 64 bytes en callback_data, lo que demuestra atención a restricciones de Telegram. Para elevar la calidad, se recomienda incorporar pruebas de carga y resiliencia, así como tests de integración con un entorno de staging que simule producción.[^1]

Tabla 13. Matriz de cobertura de pruebas

| Módulo/Funcionalidad       | Archivo(s) de test                           | Tipo de prueba                    | Estado        | Gap principal                            |
|----------------------------|----------------------------------------------|-----------------------------------|---------------|------------------------------------------|
| /start                     | test_start_command.py                        | Unit/integration                  | OK            | Casos de error avanzados                 |
| Keyboards                  | test_keyboards.py                            | Unit                              | OK            | Validación de UX bajo paginación         |
| Wizard multistep           | test_wizard_multistep.py                     | Unit/integration                  | OK            | Persistencia y recuperación de estado    |
| Callback handler           | test_callback_handler.py                     | Unit/integration                  | OK            | Pruebas de router con datos inválidos    |
| Finalizar tarea            | test_finalizar_tarea.py                      | Unit/integration                  | OK            | Simulación de 404/403 bajo carga         |
| Historial                  | test_historial.py                            | Unit/integration                  | OK            | Paginación bajo volumen alto             |

## Conclusiones y Recomendaciones Priorizadas

El bot muestra una arquitectura moderna y una experiencia de usuario cuidada, con un wizard robusto y una interfaz basada en teclados inline. La separación de responsabilidades y el logging estructurado son puntos a favor. Sin embargo, para operar en un entorno gubernamental crítico, se requieren mejoras sustanciales en seguridad, persistencia de sesión y cumplimiento. La migración a cliente asíncrono y la persistencia del wizard en Redis son cambios arquitectónicos de alto impacto que elevan la escalabilidad y la resiliencia. En seguridad, el audit trail y el cifrado en reposo son indispensables para una auditoría exitosa; la gestión centralizada de secretos y el rate limiting con Redis reducen el riesgo operativo.[^1][^2]

Tabla 14. Plan de remediación por fases

| Fase  | Acción                                                                                  | Riesgo mitigado                               | Esfuerzo | Impacto                      |
|-------|------------------------------------------------------------------------------------------|-----------------------------------------------|----------|------------------------------|
| 1     | Migrar ApiService a cliente asíncrono con timeouts y reintentos                          | Cuellos de botella y timeouts                 | Medio    | Alto                         |
| 1     | Persistir wizard en Redis (TTL, namespace, limpieza)                                     | Pérdida de estado y falta de resiliencia      | Medio    | Alto                         |
| 1     | Implementar audit logging integral por acción (quién/qué/cuándo/sobre qué)               | Trazabilidad insuficiente                     | Medio    | Alto                         |
| 1     | Activar y verificar cifrado en reposo (BD/backups)                                       | Exposición de datos                           | Medio    | Alto                         |
| 2     | Rate limiting con Redis, monitoreo y alertas                                             | Abuso y spoofing en multi-worker              | Medio    | Alto                         |
| 2     | Gestión centralizada de secretos (Vault/Secrets Manager), rotación documentada           | Compromiso de credenciales                    | Medio    | Alto                         |
| 2     | Instrumentación de métricas del bot en Prometheus/Grafana                                | Falta de visibilidad operativa                | Bajo     | Medio                        |
| 3     | Unificar contratos de API (retirar api_legacy) y documentar endpoints                    | Inconsistencias y deuda técnica               | Bajo     | Medio                        |
| 3     | Endurecer TLS y verificar certificados (Redis/API)                                       | Ataques MITM                                  | Bajo     | Medio                        |
| 3     | CSP específico y headers adicionales de compliance                                       | Riesgos de cliente                            | Bajo     | Medio                        |

Las fases 1 y 2 deben ejecutarse antes del go-live; la fase 3 consolida la madurez operativa y la mantenibilidad. La adopción de estas medidas permitirá alcanzar el nivel de cumplimiento y seguridad exigido por un sistema gubernamental, con una base arquitectónica preparada para escalar y soportar la demanda ciudadana.

## Brechas de Información Identificadas

- No se localizó la confirmación de la cantidad total de archivos de comandos (se infiere ≥6; el inventario menciona 25+ sin evidencia de todo el catálogo).  
- No se evidenció consumo directo de consultas PostGIS desde el bot.  
- No se identificó un esquema de autorización formal para ciudadanos desde Telegram más allá del uso de WHITELIST_IDS.  
- No se verificó el cifrado en reposo de la base de datos.  
- No se evidenció la persistencia de estado de sesión del wizard en Redis (context.user_data se usa en memoria).  
- No se documentó un flujo formal de auditoría de acciones del bot más allá de logging.  
- No se verificó rate limiting específico del bot alineado con la política gubernamental.  
- No se evidenció el uso de WebSockets desde el bot, más allá de su existencia en la plataforma.  
- No se detectó la implementación de refresh tokens en el flujo del bot.  
- No se verificó la configuración de CSP específica para la UI del bot.  
- No se evidenció la verificación de fortaleza/rotación del token de Telegram más allá de la variable de entorno.  
- No se documentó un proceso formal de incident response adaptado al bot.

Estas brechas se integran en el plan de acción y se abordan mediante las recomendaciones propuestas.

## Referencias

[^1]: GRUPO_GAD - Repositorio (GitHub). URL: https://github.com/eevans-d/GRUPO_GAD  
[^2]: GRUPO_GAD - Aplicación en Producción (Fly.io). URL: https://grupo-gad.fly.dev