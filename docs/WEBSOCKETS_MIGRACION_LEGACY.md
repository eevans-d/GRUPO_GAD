## Plan de Migración Fuera de `websockets.legacy`

Estado actual:
- Warnings de deprecación reportados en tests: `websockets.legacy`, `WebSocketServerProtocol` y segundo argumento de `ws_handler`.
- Funcionalidad estable. Modo "Barco Anclado": no se modifica runtime ahora; solo planificación.

Objetivo:
Eliminar warnings antes del corte de soporte (>= versión 14.x estable) garantizando compatibilidad.

Fases:
1. Inventario
   - [ ] Identificar puntos de uso directo de API legacy (principalmente en pruebas E2E).
   - [ ] Verificar versión instalada de `websockets` y changelog.
2. Sustitución en pruebas
   - [ ] Reemplazar import `from websockets.asyncio.client import connect as ws_connect` por API recomendada (si cambia nombre en futuras versiones).
   - [ ] Ajustar manejo de handshake y pings con nuevas señales (si difieren).
3. Servidor (si aplica)
   - [ ] Confirmar que Uvicorn ya está usando implementación moderna y no wrappers que emitirán warnings futuros.
4. Endurecimiento de compatibilidad
   - [ ] Añadir test que falla si aparece warning de categoría DeprecationWarning relacionado a websockets (marcarlo opcional en CI primero).
5. Observabilidad
   - [ ] Capturar métricas de latencia de primer ACK tras migración para verificar no impacta.
6. Documentación
   - [ ] Actualizar `WEBSOCKET_SYSTEM_STATUS.md` removiendo referencia a warnings y agregando fecha de migración.

Riesgos y Mitigaciones:
- Cambio en semántica de cierre -> Añadir prueba explícita de cierre limpio.
- Diferencias en manejo de subprotocolos -> No usamos subprotocolos actualmente (riesgo bajo).
- Heartbeat/pings duplicados -> Validar no se envían PING redundantes.

Rollback Plan:
- Mantener rama `feature/websocket-modern-api` hasta validación completa.
- Si surgen desconexiones inesperadas, revertir merge y conservar compatibilidad legacy durante un ciclo adicional.

Checklist de Criterios de Hecho:
- [ ] Sin DeprecationWarnings en suite.
- [ ] Todas las pruebas E2E siguen verdes.
- [ ] Métricas de broadcast y send estables (+/- 5%).
- [ ] Documentación actualizada.

Fecha de elaboración: 2025-09-25
Responsable: Equipo Backend
Estado: PLANIFICADO