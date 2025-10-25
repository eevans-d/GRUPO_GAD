# Índice de Documentación (Cleanup 2025-10-25)

Esta guía orienta a los documentos vigentes y agrupa materiales históricos en archivos de limpieza. El objetivo es agilizar onboarding, operaciones y despliegues.

## Documentos clave (vigentes)
- README.md — visión general, arranque local y deploy rápido.
- PRODUCTION_READY.md — checklist de preparación para producción.
- SECURITY.md — políticas de seguridad y secretos.
- QUICK_REFERENCE.md — comandos y rutas frecuentes.
- RAILWAY_DEPLOYMENT_COMPLETE.md — estado y guía Railway (si se usa).
- FLY_DEPLOYMENT_GUIDE.md — guía de despliegue en Fly.io.
- FLYIO_BUILD_FIX_GUIDE.md — notas de build en Fly.
- GITHUB_SECRETS_GUIDE.md — secretos requeridos para CI/CD.
- docs/ — documentación técnica detallada (índice original en DOCUMENTATION_INDEX.md).

## Operación y monitoreo
- docker-compose*.yml — stacks de dev/staging/prod locales.
- Makefile — objetivos frecuentes (up/down, smoke, ws-smoke, test, prod-*, staging-*).
- monitoring/ — configuración de monitorización.
- scripts/ — utilitarios (smoke, ws, uat, rendimiento).

## Migraciones y base de datos
- alembic/ — migraciones; env.py con soporte para asyncpg y SSL opcional.
- QUICK_FIX_DB.md — soluciones rápidas comunes.

## Historial y reportes (conservar, pero menos consultados)
- EXECUTIVE_SUMMARY.md, FINAL_STATUS_OCT20.md, DEPLOYMENT_REPORT_OCT24.md, SESSION_SUMMARY_OCT24.md
- PERFORMANCE_* y REPORTS/ bajo `reports/`

Estos quedarán vinculados desde el archivo de archivo (cleanup_archives) y no requieren edición frecuente.

## Archivos archivados hoy
- cleanup_archives/2025-10-25/scripts/load_test_10x_simple.js — copia del script de carga 10x (k6).

## Propuestas de organización adicional
1) Mover documentos de estado histórico del root a `cleanup_archives/2025-10-25/` manteniendo referencias aquí.
2) Consolidar guías de despliegue en `docs/deploy/` (Fly, Railway, CloudBuild) con un índice común.
3) Crear `docs/uat/` con el runner, checklist y resultados esperados.
4) Agregar `docs/observability/` para métricas, endpoints y dashboards.

## Tareas siguientes sugeridas
- Provisionar Redis en staging y producción, configurar REDIS_URL y verificar mediante smoke/uat.
- Habilitar PostGIS en la base de datos de staging y reactivar la migración espacial cuando proceda.
- Cerrar pendientes del UAT completo sobre staging y publicar reporte en `reports/`.

— Actualizado: 2025-10-25
