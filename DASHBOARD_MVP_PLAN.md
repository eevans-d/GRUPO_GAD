# Plan Dashboard MVP

Objetivo: Reemplazar mocks por datos reales y ofrecer una vista operativa mínima con KPIs, lista/kanban y feed de notificaciones.

## Alcance (MVP)
- KPIs en tiempo real (vía WebSocket):
  - Tareas totales, activas, completadas, pendientes.
  - Efectivos activos/ocupados/disponibles.
  - Última actualización.
- Lista/Kanban de tareas:
  - Columnas: Pendiente, En progreso, Completada.
  - Orden por prioridad y fecha.
  - Filtros básicos (asignado, estado, rango fechas).
- Feed de notificaciones:
  - Últimas N notificaciones del sistema.
  - Niveles: info, warning, error.

## Fuentes de datos
- DB (SQLAlchemy async):
  - Tablas: tareas, asignaciones, efectivos, eventos.
  - Vistas/materializadas opcionales para KPIs si RPS > 30.
- WebSockets:
  - Eventos: `task_created`, `task_updated`, `task_status_changed`, `notification`.
  - Suscripciones por tópico (MVP implementado):
    - `dashboard:kpis`, `dashboard:list`, `notifications`.

## API/Backend
- Endpoints:
  - GET `/api/v1/dashboard/kpis` -> Métricas iniciales.
  - GET `/api/v1/dashboard/tasks` -> Lista paginada/filtrada.
  - GET `/api/v1/notifications` -> Últimas N.
- WS Mensajes:
  - `dashboard_update` con `topic=dashboard:kpis`.
  - `task_*` con `topic=dashboard:list`.
  - `notification/*` con `topic=notifications`.

## UI (estática inicial)
- `dashboard/static/index.html`:
  - Conectar WS (wss en prod), enviar `subscribe` a tópicos.
  - Pintar KPIs y lista.
  - Feed con autoscroll.

## Métricas y Observabilidad
- /metrics: validación de conexiones activas y broadcasts.
- Logs WS: suscripción/unsubcripción por connection_id.

## Roadmap posterior
- Auth UI (JWT/Telegram), paginación avanzada, búsqueda.
- Gráficos de rendimiento, mapa de efectivos.
- Acciones masivas y SLA/alertas configurables.

## Riesgos y mitigaciones
- Carga DB: cachear KPIs en Redis y refrescar por eventos.
- Concurrencia WS: pub/sub Redis ya integrado; validar en staging.
- CORS/Seguridad: orígenes permitidos y JWT obligatorio en prod.
