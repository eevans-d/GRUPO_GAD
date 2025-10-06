# Checklist de Despliegue a Producción

**Criterio Go:** Todos los items marcados como OK.
**Criterio No-Go:** Cualquier item crítico marcado como KO.
**Tiempo estimado de verificación:** 15-20 minutos.

---

### 1. Criterios Técnicos

| Item | Estado Esperado | Verificación |
| :--- | :--- | :--- |
| [ ] **Health checks responden 200** | `OK` | `curl -s -o /dev/null -w "%{http_code}" https://your-domain.com/api/v1/health/` |
| [ ] **Migraciones Alembic aplicadas** | `OK` | `alembic current` muestra la última revisión |
| [ ] **Backups automáticos funcionando** | `OK` | Verificar logs del script de backup |
| [ ] **Variables de entorno sensibles** | `OK` | `env | grep SECRET` no muestra valores |
| [ ] **Logs en nivel INFO** | `OK` | Revisar `docker logs` del contenedor |
| [ ] **Bot en modo webhook** | `OK` | `getWebhookInfo` confirma la URL |
| [ ] **Dashboard accesible con SSL** | `OK` | `https://your-domain.com/dashboard` carga sin warnings |
| [ ] **/tasks/emergency operativo** | `OK` | `POST /tasks/emergency` crea una tarea |

---

### 2. Criterios Funcionales

| Item | Estado Esperado | Verificación |
| :--- | :--- | :--- |
| [ ] **Smoke tests pasan 100%** | `OK` | Ejecutar `scripts/smoke_staging.sh` contra producción |
| [ ] **/admin/telegram/send probado** | `OK` | `POST` envía mensaje de prueba a un canal |
| [ ] **Geolocalización PostGIS funcional** | `OK` | Crear/consultar tarea con ubicación |
| [ ] **WebSocket dashboard conecta** | `OK` | El dashboard recibe actualizaciones en tiempo real |
| [ ] **Métricas Prometheus disponibles** | `OK` | `curl /api/v1/metrics/prometheus` devuelve datos |
| [ ] **Grafana conectado** | `OK` | Panel de Grafana muestra datos recientes |

---

### 3. Criterios de Contingencia

| Item | Estado Esperado | Verificación |
| :--- | :--- | :--- |
| [ ] **Plan de rollback documentado** | `OK` | El documento `ROLLBACK_PLAN.md` existe y es claro |
| [ ] **Backup pre-deploy disponible** | `OK` | Archivo de backup reciente en `backups/` |
| [ ] **Ventana de mantenimiento comunicada**| `OK` | Notificación enviada a usuarios/stakeholders |
| [ ] **Contactos de soporte identificados** | `OK` | Lista de contactos de emergencia disponible |
