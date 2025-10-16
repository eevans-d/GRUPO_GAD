# 🚀 Checklist de Producción - GRUPO_GAD

**Fecha de actualización**: 7 de octubre de 2025  
**Versión**: 2.0  
**Estado del proyecto**: Fase 5 - Puesta en Producción

**Criterio Go:** Todos los items marcados como ✅.
**Criterio No-Go:** Cualquier item crítico marcado como ❌.
**Tiempo estimado de verificación:** 20-30 minutos.

## ✅ PRE-VALIDACIONES COMPLETADAS
- [x] **Fase 3.4**: Sistema de backup implementado y probado
- [x] **Fase 4.1-4.2**: Pipelines CI/CD funcionando
- [x] **Release check**: 129 tests pasando, 63% cobertura
- [x] **Docker build**: Imagen API construida exitosamente

## 🏗️ 1. INFRAESTRUCTURA Y SERVIDOR

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Servidor apropiado seleccionado** | | Min 4 vCPUs, 8GB RAM, 50GB SSD | ⚠️ |
| [ ] **Sistema operativo actualizado** | | Ubuntu 22.04 LTS con updates | ⚠️ |
| [ ] **Docker y Docker Compose instalados** | | `docker --version && docker compose version` | 🔴 |
| [ ] **Firewall configurado correctamente** | | Puertos 80,443 abiertos; 22 restringido | 🔴 |
| [ ] **SSH configurado de forma segura** | | Clave SSH, sin password auth | 🔴 |
| [ ] **Espacio en disco suficiente** | | Min 40GB libres para logs/backups | ⚠️ |

## 🌐 2. DNS Y CERTIFICADOS

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Dominio configurado** | | DNS A record apunta a IP del servidor | 🔴 |
| [ ] **SSL/TLS funcionando** | | `curl -I https://tudominio.com` → 200 OK | 🔴 |
| [ ] **Redirección HTTP→HTTPS** | | `curl -I http://tudominio.com` → 301/302 | ⚠️ |
| [ ] **Certificado válido por >30 días** | | `openssl s_client -connect tudominio.com:443` | ⚠️ |

## 🔐 3. SEGURIDAD Y VARIABLES DE ENTORNO

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Variables de entorno seguras** | | `env \| grep SECRET` no muestra valores | 🔴 |
| [ ] **Archivo .env.production configurado** | | Todas las vars requeridas presentes | 🔴 |
| [ ] **Contraseñas generadas seguramente** | | Min 32 chars, aleatorias | 🔴 |
| [ ] **Secret keys únicos para producción** | | No usar valores de desarrollo | 🔴 |
| [ ] **Acceso SSH restringido** | | Solo IPs autorizadas pueden conectar | ⚠️ |
| [ ] **Fail2ban configurado** | | Protección contra ataques de fuerza bruta | ⚠️ |

## 🛠️ 4. APLICACIÓN Y SERVICIOS

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Código de producción desplegado** | | Version tag específico, no main/master | 🔴 |
| [ ] **Todos los servicios UP** | | `docker compose ps` → todos UP | 🔴 |
| [ ] **Health checks responden 200** | | `curl https://tudominio.com/api/v1/health` | 🔴 |
| [ ] **Migraciones Alembic aplicadas** | | `alembic current` muestra última revisión | 🔴 |
| [ ] **Dashboard accesible** | | `https://tudominio.com` carga correctamente | ⚠️ |
| [ ] **WebSockets funcionando** | | Conexión WS exitosa desde dashboard | ⚠️ |
| [ ] **API endpoints principales** | | `/auth/login`, `/users/`, `/tasks/` funcionando | 🔴 |

## 📊 5. MONITOREO Y MÉTRICAS

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Métricas Prometheus disponibles** | | `curl https://tudominio.com/metrics` | ⚠️ |
| [ ] **Métricas detalladas funcionando** | | `curl https://tudominio.com/api/v1/metrics/prometheus` | ⚠️ |
| [ ] **Logs estructurados activos** | | `docker compose logs api` muestra JSON | ⚠️ |
| [ ] **Rate limiting funcionando** | | Gobierno rate limiting activo | ⚠️ |
| [ ] **WebSocket métricas** | | Conexiones, mensajes, broadcasts tracked | ⚠️ |

## 💾 6. BACKUP Y CONTINGENCIA

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Backup automático configurado** | | Cron jobs de backup activos | 🔴 |
| [ ] **Primer backup exitoso** | | `make backup` ejecuta sin errores | 🔴 |
| [ ] **Verificación de integridad** | | SHA-256 del backup válido | 🔴 |
| [ ] **S3 backup configurado** | | Backup sube a S3 exitosamente | ⚠️ |
| [ ] **Procedimiento de restore probado** | | `make backup-restore` funciona | 🔴 |
| [ ] **Plan de rollback documentado** | | ROLLBACK_PLAN.md actualizado | ⚠️ |

## ⚡ 7. PRUEBAS FUNCIONALES

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Smoke tests completos** | | `make smoke` ejecuta exitosamente | 🔴 |
| [ ] **WebSocket smoke test** | | `make ws-smoke` conecta y funciona | ⚠️ |
| [ ] **Autenticación funcionando** | | Login/logout/token refresh funcionando | 🔴 |
| [ ] **CRUD básico de usuarios** | | Crear, leer, actualizar usuarios | 🔴 |
| [ ] **CRUD básico de tareas** | | Crear, leer, actualizar tareas | 🔴 |
| [ ] **Endpoint de emergencia** | | `POST /tasks/emergency` funciona | ⚠️ |
| [ ] **Geolocalización PostGIS** | | Queries geo funcionando | ⚠️ |

## 🔍 8. RENDIMIENTO Y CARGA

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Tiempo de respuesta aceptable** | | Health check < 500ms | ⚠️ |
| [ ] **Uso de CPU normal** | | CPU < 70% en estado idle | ⚠️ |
| [ ] **Uso de memoria normal** | | RAM < 80% en estado idle | ⚠️ |
| [ ] **Prueba de carga básica** | | 100 requests concurrentes exitosas | ⚠️ |
| [ ] **WebSocket connections** | | Múltiples conexiones simultáneas | ⚠️ |

## 📋 9. DOCUMENTACIÓN Y PROCEDIMIENTOS

| Item | Estado | Verificación | Crítico |
| :--- | :---: | :--- | :---: |
| [ ] **Información de servidor documentada** | | IP, credenciales, contactos | 🔴 |
| [ ] **Procedimientos de emergencia** | | Rollback, restore, reinicio | 🔴 |
| [ ] **Monitoreo post-deploy** | | Plan de verificación 24h | ⚠️ |
| [ ] **Contactos de soporte** | | DevOps, admin, proveedores | ⚠️ |
| [ ] **Ventana de mantenimiento comunicada** | | Stakeholders notificados | ⚠️ |

---

## 🚦 CRITERIOS DE DECISIÓN

### ✅ GO (Proceder con deployment)
- Todos los items 🔴 marcados como completados
- Máximo 2 items ⚠️ pendientes (no críticos)
- Procedimientos de emergencia claros y probados

### ❌ NO-GO (Diferir deployment)
- Cualquier item 🔴 pendiente o fallando
- Más de 3 items ⚠️ pendientes
- Backup/restore no funcional
- Certificados SSL no válidos

---

## 📞 INFORMACIÓN DE CONTACTO

**Servidor de Producción**:
- IP: ____________________
- Dominio: ____________________
- Usuario SSH: ____________________

**Credenciales importantes** (almacenar en vault seguro):
- Database admin
- AWS/Cloud provider keys  
- SSH private keys
- Certificados SSL

---

## 🚨 COMANDOS DE EMERGENCIA

### Verificación rápida de estado
```bash
# Estado de servicios
docker compose ps

# Logs recientes
docker compose logs --tail=50 api

# Health check
curl -f https://tudominio.com/api/v1/health
```

### Rollback de emergencia
```bash
# Cambiar a versión anterior
git checkout tags/v0.9.0
docker compose down
docker compose up -d
```

### Restaurar backup
```bash
# Listar backups disponibles
make backup-list

# Restaurar más reciente
make backup-restore BACKUP_FILE=<archivo>
```

---

**✍️ Preparado por**: GitHub Copilot  
**📅 Revisado por**: __________________ (Fecha: ______)  
**✅ Aprobado para producción**: __________________ (Fecha: ______)
