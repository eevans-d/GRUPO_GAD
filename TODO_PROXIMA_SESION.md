# 📋 TODO - Próxima Sesión

## 🔴 Prioridad Alta (Hacer Primero)

### 1. Validación End-to-End de Nuevos Comandos
**Estimado:** 30-45 min

- [ ] Configurar entorno de desarrollo con `make up`
- [ ] Verificar que el bot se conecta correctamente
- [ ] Probar comando `/historial` en Telegram
  - [ ] Sin argumentos (todas las tareas)
  - [ ] Con filtro `activas`
  - [ ] Con filtro `finalizadas`
  - [ ] Navegación con botones ◀️ ▶️
- [ ] Probar comando `/estadisticas` en Telegram
  - [ ] Verificar métricas se calculan correctamente
  - [ ] Validar barras de progreso se muestran bien
  - [ ] Comprobar emojis y formato
- [ ] Documentar cualquier issue encontrado

**Criterios de éxito:**
- ✅ Ambos comandos responden sin errores
- ✅ Paginación funciona correctamente
- ✅ Filtros aplican los cambios esperados
- ✅ Métricas son precisas

---

### 2. Ejecutar Suite Completa de Tests
**Estimado:** 20-30 min

- [ ] Configurar entorno Python con dependencias
  ```bash
  # Si usas poetry
  poetry install
  poetry shell
  
  # O con pip
  pip install -r requirements.txt
  ```
- [ ] Ejecutar todos los tests
  ```bash
  make test
  # o
  python -m pytest -v
  ```
- [ ] Ejecutar tests específicos del bot
  ```bash
  python -m pytest tests/bot/ -v
  ```
- [ ] Revisar cobertura
  ```bash
  make test-cov
  ```
- [ ] Corregir tests que fallen (si los hay)

**Criterios de éxito:**
- ✅ Todos los tests pasan
- ✅ Cobertura ≥ 80% en código nuevo
- ✅ No hay warnings críticos

---

### 3. Revisar Logs y Métricas
**Estimado:** 15-20 min

- [ ] Verificar logs del bot no muestran errores
  ```bash
  docker logs -f gad_bot_dev
  ```
- [ ] Revisar logs de la API
  ```bash
  make logs-api
  ```
- [ ] Comprobar métricas en `/metrics`
  ```bash
  curl http://localhost:8000/metrics
  ```
- [ ] Validar no hay memory leaks ni warnings de performance

**Criterios de éxito:**
- ✅ No hay errores en logs
- ✅ Métricas se reportan correctamente
- ✅ Performance es aceptable

---

## 🟡 Prioridad Media (Importante pero No Urgente)

### 4. Optimización de Queries del Historial
**Estimado:** 45-60 min

**Objetivo:** Mejorar performance de consultas de historial

**Tareas:**
- [ ] Analizar queries generadas por `get_user_tasks()`
- [ ] Identificar si faltan índices en DB
- [ ] Agregar índices si necesario:
  ```sql
  CREATE INDEX idx_tasks_user_id ON tasks(user_id);
  CREATE INDEX idx_tasks_estado ON tasks(estado);
  CREATE INDEX idx_tasks_created_at ON tasks(created_at);
  ```
- [ ] Ejecutar `EXPLAIN ANALYZE` en queries críticas
- [ ] Documentar optimizaciones aplicadas

**Resultado esperado:** Queries ≤ 50ms para listas de hasta 1000 tareas

---

### 5. Implementar Caché para Estadísticas
**Estimado:** 60-90 min

**Objetivo:** Reducir carga en DB para cálculos de estadísticas

**Implementación:**
```python
# En estadisticas.py
from redis import Redis
import json

async def _get_cached_stats(user_id: int, redis_client: Redis) -> dict | None:
    key = f"stats:user:{user_id}"
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None

async def _cache_stats(user_id: int, stats: dict, redis_client: Redis, ttl: int = 300):
    key = f"stats:user:{user_id}"
    redis_client.setex(key, ttl, json.dumps(stats))
```

**Tareas:**
- [ ] Agregar cliente Redis a estadisticas.py
- [ ] Implementar funciones de caché
- [ ] Actualizar handler para usar caché
- [ ] Invalidar caché cuando se crean/finalizan tareas
- [ ] Agregar tests para lógica de caché
- [ ] Documentar TTL y estrategia de invalidación

**Resultado esperado:** Response time ≤ 100ms con caché, mejora de ~70%

---

### 6. Tests de Integración E2E
**Estimado:** 90-120 min

**Objetivo:** Validar flujo completo usuario → bot → API → DB

**Casos de prueba:**
```python
# tests/integration/test_bot_e2e.py

@pytest.mark.integration
async def test_historial_flow_completo():
    """Test flujo completo de historial."""
    # 1. Crear tareas de prueba en DB
    # 2. Simular comando /historial desde bot
    # 3. Verificar respuesta contiene tareas
    # 4. Simular click en botón "Siguiente"
    # 5. Verificar paginación funciona
    # 6. Cleanup

@pytest.mark.integration  
async def test_estadisticas_calculo_correcto():
    """Test cálculo de estadísticas es preciso."""
    # 1. Crear dataset conocido en DB
    # 2. Ejecutar comando /estadisticas
    # 3. Parsear respuesta y validar números
    # 4. Verificar cálculos manuales coinciden
    # 5. Cleanup
```

**Tareas:**
- [ ] Crear `tests/integration/test_bot_e2e.py`
- [ ] Implementar helpers para simular updates de Telegram
- [ ] Agregar fixtures para datos de prueba
- [ ] Ejecutar y validar tests pasan
- [ ] Documentar setup necesario para tests E2E

---

## 🟢 Prioridad Baja (Nice to Have)

### 7. Implementar Comando `/editar_tarea`
**Estimado:** 120-180 min

**Estado:** Diseño completo disponible en `docs/bot/FEATURES_BONUS.md`

**Pasos de implementación:**
1. Crear `src/bot/commands/editar_tarea.py`
2. Implementar wizard de edición:
   - Listar tareas del usuario
   - Permitir seleccionar una
   - Mostrar campos editables
   - Confirmar cambios
3. Agregar validaciones de permisos
4. Implementar auditoría de cambios
5. Registrar handler en `handlers/__init__.py`
6. Crear tests en `tests/bot/test_editar_tarea.py`
7. Actualizar documentación

**Consideraciones:**
- Solo permitir editar tareas propias
- Log de cambios en tabla `task_audit`
- Validar campos antes de guardar
- Cancelar sin guardar debe ser fácil

---

### 8. Expandir Métricas del Dashboard
**Estimado:** 60-90 min

**Nuevas métricas a agregar en `/estadisticas`:**

```python
# Métricas adicionales
- Racha actual (días consecutivos con tareas completadas)
- Mejor racha histórica
- Día de la semana más productivo
- Hora del día más productiva
- Comparativa vs promedio de equipo
- Ranking entre usuarios (opcional)
```

**Implementación:**
- [ ] Agregar nuevos cálculos en `_calculate_statistics()`
- [ ] Actualizar formato en `_format_statistics()`
- [ ] Agregar nuevos emojis y visualizaciones
- [ ] Tests para nuevas métricas
- [ ] Actualizar documentación

---

### 9. Internacionalización (i18n)
**Estimado:** 180-240 min

**Objetivo:** Soportar múltiples idiomas en el bot

**Implementación:**
```python
# i18n/es.json
{
  "commands.historial.title": "📋 Historial de Tareas",
  "commands.historial.empty": "No tienes tareas {filter}",
  "commands.estadisticas.title": "📊 Mis Estadísticas"
}

# i18n/en.json
{
  "commands.historial.title": "📋 Task History",
  "commands.historial.empty": "You don't have {filter} tasks",
  "commands.estadisticas.title": "📊 My Statistics"
}
```

**Tareas:**
- [ ] Crear estructura de carpetas `i18n/`
- [ ] Extraer todos los strings a archivos de traducción
- [ ] Implementar sistema de detección de idioma
- [ ] Actualizar comandos para usar traducciones
- [ ] Agregar comando `/idioma` para cambiar idioma
- [ ] Tests para diferentes idiomas
- [ ] Documentar sistema de i18n

---

## 🔮 Backlog Futuro (Ideas para Explorar)

### Sistema de Notificaciones Proactivas
**Concepto:** Bot envía notificaciones automáticas

**Casos de uso:**
- Tareas próximas a vencer (24h antes)
- Tareas vencidas sin completar
- Resumen diario/semanal automático
- Celebración de hitos (10 tareas completadas, etc.)

**Complejidad:** Alta (requiere job scheduler)

---

### Reportes Periódicos Automáticos
**Concepto:** Informes automáticos por email/Telegram

**Tipos de reportes:**
- Reporte semanal personal
- Reporte mensual del equipo
- Comparativa de productividad
- Trends y análisis

**Complejidad:** Media-Alta

---

### Integración Multi-Plataforma
**Concepto:** Expandir más allá de Telegram

**Plataformas objetivo:**
- Slack
- Discord  
- Microsoft Teams
- WhatsApp Business API

**Complejidad:** Alta (cada plataforma es diferente)

---

### Dashboard Web Complementario
**Concepto:** Interfaz web responsive para móvil/desktop

**Features:**
- Visualización de métricas avanzadas
- Gráficos interactivos (Chart.js)
- Gestión completa de tareas
- Reportes exportables (PDF/Excel)

**Complejidad:** Muy Alta (proyecto independiente)

---

## 📝 Notas Importantes

### Antes de Empezar Mañana
1. ☕ Café/té listo
2. 🎧 Playlist de concentración preparada
3. 📱 Notificaciones silenciadas
4. 📋 Este TODO abierto en pantalla secundaria

### Recordatorios
- **Commits frecuentes:** Commit cada feature pequeña completada
- **Branch por feature:** Crear branches para cambios grandes
- **Tests primero:** Red → Green → Refactor
- **Documentar mientras:** No dejar docs para el final

### Enlaces Útiles
- [Documentación Telegram Bot API](https://core.telegram.org/bots/api)
- [Python-telegram-bot v20.x Docs](https://docs.python-telegram-bot.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

---

## ✅ Template de Checklist de Sesión

**Al inicio de sesión:**
- [ ] Pull latest changes from master
- [ ] Verificar que tests existentes pasan
- [ ] Levantar entorno con `make up`
- [ ] Verificar servicios healthy
- [ ] Revisar issues pendientes en GitHub (si aplica)

**Durante desarrollo:**
- [ ] Commits pequeños y frecuentes
- [ ] Tests para cada feature nueva
- [ ] Documentar funciones complejas
- [ ] Verificar que lint pasa (`make lint`)

**Al final de sesión:**
- [ ] Ejecutar suite completa de tests
- [ ] Push de todos los commits
- [ ] Actualizar este TODO con progreso
- [ ] Crear RESUMEN_JORNADA_YYYYMMDD.md
- [ ] Commit y push de documentación

---

## 📊 Métricas de Progreso

### Opción 7 - Features Bonus
```
Estado actual: ▰▰▰▰▰▰▰▰▰▰ 100%

✅ Implementación base     [100%]
✅ Tests unitarios         [100%]
✅ Documentación           [100%]
✅ Integración handlers    [100%]
🔄 Validación E2E          [  0%] ← PRÓXIMO
🔄 Optimización            [  0%]
📋 Feature opcional        [  0%] (editar_tarea)
```

### Plan General (7 Opciones)
```
✅ Opción 1: Testing Manual         [100%]
✅ Opción 2: Merge a Master         [100%]
✅ Opción 3: Revisión de Código     [100%]
✅ Opción 4: Deploy a Producción    [100%]
✅ Opción 5: Análisis y Métricas    [100%]
✅ Opción 6: Mejorar UX             [100%]
✅ Opción 7: Features Bonus         [100%]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 TOTAL:                           [100%]
```

---

## 🎯 Objetivos de la Próxima Sesión

### Mínimos Indispensables
1. ✅ Validación E2E funcional
2. ✅ Tests pasando al 100%
3. ✅ No hay errores en logs

### Ideales
4. ⭐ Optimización de queries implementada
5. ⭐ Caché de estadísticas funcionando
6. ⭐ Tests de integración E2E creados

### Stretch Goals (Si Hay Tiempo)
7. 🌟 Comando /editar_tarea implementado
8. 🌟 Métricas expandidas en dashboard
9. 🌟 Primera versión de i18n

---

**🚀 ¡Listo para continuar mañana!**

*Última actualización: 11 Octubre 2025 - Post Opción 7*  
*Siguiente revisión: Inicio de próxima sesión*
