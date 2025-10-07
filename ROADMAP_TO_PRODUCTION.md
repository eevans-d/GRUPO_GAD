# Hoja de Ruta a Producción: Proyecto GRUPO GAD

**Fecha de Creación:** 16 de Septiembre de 2025
**Versión:** 1.0

## 1. Situación Actual y Análisis del Sistema

Este documento describe el estado actual del proyecto `GRUPO_GAD` y define los pasos necesarios para llevarlo a un estado de producción estable y mantenible.

### 1.1. Arquitectura del Sistema

Tras un análisis exhaustivo del código fuente y los archivos de configuración, se ha determinado que la arquitectura se compone de los siguientes cinco (5) servicios:

1.  **`api` (Servicio Principal):**
    *   **Tecnología:** API RESTful basada en **FastAPI** (Python).
    *   **Servidor WSGI/ASGI:** `Gunicorn` con workers de `Uvicorn`.
    *   **Función:** Expone los endpoints para la gestión de usuarios, tareas y otras entidades del sistema. Sirve el dashboard administrativo.

2.  **`db` (Base de Datos):**
    *   **Tecnología:** **PostgreSQL** con la extensión **PostGIS** para capacidades geoespaciales.
    *   **Migraciones:** Gestionadas por **Alembic**. El esquema se mantiene actualizado mediante scripts.
    *   **Inicialización:** Un script (`init_postgis.sql`) asegura que las extensiones necesarias (`postgis`, `pgcrypto`) estén activadas.

3.  **`redis` (Caché en Memoria):**
    *   **Tecnología:** **Redis**.
    *   **Función:** Utilizado para cacheo de sesiones, datos de acceso frecuente y potencialmente para colas de tareas.

4.  **`bot` (Interfaz de Chat):**
    *   **Tecnología:** Bot de **Telegram**.
    *   **Función:** Interactúa con la `api` para permitir a los usuarios realizar operaciones (ej. crear tareas) desde Telegram.

5.  **`caddy` (Proxy Inverso y Servidor Web):**
    *   **Tecnología:** **Caddy**.
    *   **Función:** Actúa como punto de entrada único al sistema. Gestiona el tráfico, lo dirige a la `api`, y maneja automáticamente los certificados SSL/TLS en un entorno de producción. Su configuración (`Caddyfile`) ya existe pero no estaba integrada.

### 1.2. Estado del Proyecto

*   **Positivo:**
    *   La base del código es sólida y bien estructurada.
    *   El uso de FastAPI, Pydantic y SQLAlchemy es moderno y robusto.
    *   La contenerización (Docker) está bien encaminada con un `Dockerfile` seguro.
    *   Existen pruebas unitarias y de integración, con una configuración de cobertura de código.
    *   Se han realizado auditorías estáticas de seguridad y dependencias.
    *   Existe un dashboard administrativo básico.

*   **Bloqueo Crítico (Resuelto en este plan):**
    *   El archivo `docker-compose.yml` era inadecuado, impidiendo levantar el entorno completo para realizar pruebas dinámicas.
    *   El archivo `docker-compose.prod.yml` estaba vacío.
    *   El proxy inverso `caddy` no estaba integrado en la orquestación de contenedores.

## 2. Plan de Acción: Checklist Hacia la Producción

Este checklist detalla las fases y tareas requeridas para pasar del estado actual a un despliegue en producción y su posterior mantenimiento.

---

### ☑️ **Fase 1: Estabilización del Entorno Local (Desbloqueo)**

*   [x] **1.1. Analizar la arquitectura completa del sistema.**
*   [ ] **1.2. Reconstruir `docker-compose.yml`:** Crear un archivo que orqueste correctamente los 5 servicios (`api`, `db`, `redis`, `bot`, `caddy`) para desarrollo local.
*   [ ] **1.3. Reconstruir `docker-compose.prod.yml`:** Crear un archivo de overlay para producción que configure el entorno para alto rendimiento y seguridad.
*   [ ] **1.4. Ejecutar Auditoría Dinámica:** Con el entorno funcionando, realizar `curl` a los endpoints de la API y `docker exec` a la base de datos para validar el comportamiento en tiempo de ejecución.
*   [ ] **1.5. Generar Informe Final de Cumplimiento:** Documentar los resultados de la auditoría dinámica.

### ☐ **Fase 2: Pruebas y Calidad de Código**

*   [ ] **2.1. Aumentar Cobertura de Pruebas:** Analizar el informe de `pytest-cov` y añadir pruebas unitarias y de integración para alcanzar una cobertura > 90%.
    *   [ ] Pruebas para todos los endpoints de la API (casos de éxito y error).
    *   [ ] Pruebas para la lógica de negocio en los servicios.
    *   [ ] Pruebas para los casos borde y de seguridad (ej. inyección de dependencias, permisos).
*   [ ] **2.2. Refinar Pruebas de Integración:** Asegurar que las pruebas de integración limpien y restauren el estado de la base de datos correctamente entre ejecuciones.
*   [ ] **2.3. Implementar Pruebas de Carga (Opcional pero Recomendado):** Usar herramientas como `locust` para simular carga en la API y detectar cuellos de botella.

### ☐ **Fase 3: Preparación para Producción (Hardening)**

*   [ ] **3.1. Gestión de Secretos:**
    *   [ ] Centralizar la gestión de secretos (contraseñas de BD, tokens) usando una solución como **HashiCorp Vault** o el gestor de secretos del proveedor cloud (ej. AWS Secrets Manager, GCP Secret Manager).
    *   [ ] Eliminar cualquier secreto hardcodeado que pudiera quedar.
*   [ ] **3.2. Logging Estructurado:**
    *   [ ] Configurar Gunicorn/Uvicorn para que emita logs en formato **JSON**. Esto facilita la ingesta y análisis por parte de sistemas de monitoreo como Datadog, Splunk o el stack ELK.
*   [x] **3.3. Monitoreo y Alertas:**
    *   [x] **Métricas:** Exponer métricas detalladas en formato **Prometheus** (más allá del uptime actual). Incluir latencia de requests, número de errores, etc.
    *   [ ] **Dashboard de Monitoreo:** Configurar un dashboard (ej. en **Grafana**) que consuma las métricas de Prometheus para visualizar la salud del sistema en tiempo real.
    *   [ ] **Alertas:** Configurar alertas (ej. con Alertmanager de Prometheus) para notificar sobre fallos críticos (ej. API caída, uso de CPU > 90%).
*   [x] **3.4. Estrategia de Backup y Restauración:**
    *   [x] Automatizar backups periódicos de la base de datos PostgreSQL (implementado con scripts y Docker).
    *   [x] Almacenar los backups en un lugar seguro y externo (soporte para S3 implementado).
    *   [x] Documentar y **probar** el procedimiento de restauración a partir de un backup (ver `docs/BACKUP_RESTORE_STRATEGY.md`).

### ☑️ **Fase 4: Despliegue Continuo (CI/CD)**

*   [x] **4.1. Pipeline de Integración Continua (CI):**
    *   [x] Configurar un pipeline (en GitHub Actions) que se dispare en cada `push` o `pull request`.
    *   [x] El pipeline ejecuta:
        *   Linter (`ruff`) y type checker (`mypy`).
        *   Todas las pruebas (`pytest`) con cobertura.
        *   Construcción de imágenes Docker para validar el build.
        *   Tests E2E en branches principales.
*   [x] **4.2. Pipeline de Despliegue Continuo (CD):**
    *   [x] Configurar pipeline que tras un merge a la rama principal (`main`):
        *   Construye y etiqueta las imágenes Docker de producción.
        *   Sube las imágenes a GitHub Container Registry.
        *   Despliega automáticamente en **staging** para validación.
    *   [x] Implementar estrategia de despliegue a **producción** con aprobación manual.
    *   [x] Incluir pipeline de release management con versionado semántico.

### ☐ **Fase 5: Puesta en Producción (Go-Live)**

*   [x] **5.1. Configuración de Infraestructura:**
    *   [x] Creación de script para provisionar los servidores (`scripts/setup_production_server.sh`).
    *   [x] Documentar configuración de la red, firewalls y grupos de seguridad.
*   [x] **5.2. Configuración de DNS:** 
    *   [x] Documentación completa para configuración DNS en `docs/DNS_CONFIGURATION_GUIDE.md`.
    *   [ ] Apuntar el dominio público del servicio a la IP del servidor de producción.
*   [ ] **5.3. Despliegue Inicial:**
    *   [ ] Cargar los secretos de producción en el entorno.
    *   [ ] Ejecutar `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`.
    *   [ ] Verificar que todos los servicios están saludables.
*   [x] **5.4. Migración de Datos:** 
    *   [x] Script de migración inicial implementado (`scripts/initial_data_migration.py`).
    *   [x] Datos base creados en `data/migration/`.
    *   [ ] Ejecutar migración en producción.

### ☑️ **Fase 6: Post-Producción (Mantenimiento y Fine-Tuning)**

*   [x] **6.1. Verificación Post-Despliegue:**
    *   [x] Script de verificación automática implementado (`scripts/post_deployment_verification.sh`).
    *   [x] Validación de servicios, conectividad, DNS y SSL.
    *   [x] Verificación de métricas y logs de sistema.
    *   [ ] Ejecutar verificación en entorno de producción.
*   [x] **6.2. Sistema de Monitoreo y Alertas:**
    *   [x] Configuración completa de alertas documentada (`docs/MONITORING_ALERTING_GUIDE.md`).
    *   [x] Definición de métricas críticas y umbrales de alerta.
    *   [x] Configuración de Alertmanager con múltiples canales de notificación.
    *   [x] Dashboards de Grafana especificados para overview, infraestructura y aplicación.
    *   [ ] Implementar configuración de alertas en producción.
*   [x] **6.3. Plan de Rotación de Secretos:**
    *   [x] Inventario completo de secretos documentado (`docs/SECURITY_ROTATION_PLAN.md`).
    *   [x] Scripts de rotación automática para diferentes tipos de credenciales.
    *   [x] Políticas de seguridad y auditorías programáticas implementadas.
    *   [x] Plan de respuesta a incidentes de seguridad definido.
    *   [ ] Activar rotación automática en producción.
*   [x] **6.4. Sistema de Feedback y Mejora Continua:**
    *   [x] Canales múltiples de recopilación de feedback implementados (`docs/FEEDBACK_IMPROVEMENT_PLAN.md`).
    *   [x] Sistema de análisis automático de sentimientos y clasificación.
    *   [x] Dashboard de métricas de feedback y KPIs definidos.
    *   [x] Proceso de mejora continua semanal automatizado.
    *   [x] Integración con herramientas de gestión de tickets y notificaciones.
    *   [ ] Desplegar sistema de feedback en producción.
