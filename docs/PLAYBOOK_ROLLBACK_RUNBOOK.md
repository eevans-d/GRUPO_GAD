# Playbook – Runbook de Rollback (<10 min)

Objetivo: Asegurar reversibilidad rápida y confiable de cada release.

## Principios
- Rollback practicado antes de producción (simulación en staging).
- Scripts idempotentes (revertible aunque se invoquen dos veces).
- Minimizar input manual.

## Checklist Pre-Release (Validar Reversibilidad)
- [ ] Tag de la versión anterior existente y desplegable.
- [ ] Backups/migraciones: snapshot DB antes de cambios irreversibles.
- [ ] Feature flags listos para apagar nueva funcionalidad.
- [ ] Health checks verificados (baseline estable).

## Procedimiento Base (Ejemplo Docker / Compose)
1. Marcar release actual: `VERSION_ACTUAL=$(git rev-parse --short HEAD)`.
2. Seleccionar tag estable anterior: `git checkout <tag_estable>`.
3. Rebuild imágenes (si aplica) con cache mínimo.
4. Aplicar rollback infra: `docker compose -f docker/docker-compose.prod.yml pull && docker compose -f docker/docker-compose.prod.yml up -d api`.
5. Verificar health endpoint `/health` y métricas.
6. Validar logs sin errores críticos 5 minutos.
7. Registrar en changelog: rollback ejecutado (timestamp, responsable, causa).

## Migraciones de Base de Datos
| Tipo | Estrategia Rollback |
|------|---------------------|
| Add Column Nullable | Drop column (si seguro) o dejar inerte |
| Add Column NOT NULL con data | Requiere script reverso + backup |
| Rename Column | Operar via rename reversible o vista intermedia |
| Drop Column | Evitar en releases rápidos (irreversible) |

## Feature Flags
- Mantener lista de flags nuevos y su estado esperado tras rollback.
- Automatizar revert a estado anterior (`flags_snapshot.json`).

## Verificación Post-Rollback
- [ ] Errores 5xx dentro de umbral basal.
- [ ] Latencias p95 ≈ baseline.
- [ ] Métricas de negocio primarias sin caída abrupta.
- [ ] Flags en estado esperado.
- [ ] Usuarios clave confirman funcionalidad base.

## Registro Estructurado
| Campo | Ejemplo |
|-------|---------|
| Timestamp | 2025-09-26T04:15Z |
| Versión Revertida | 1.3.2 |
| Commit Actual | a1b2c3d |
| Responsable | userX |
| Motivo | Error en cálculo métricas real-time |
| Tiempo Ejecución | 7m 30s |
| Resultado | Exitoso |
| Acciones Correctivas | Añadir test e2e de métrica |

## Anti-Patrones
- Rollback improvisado sin ensayo.
- Cambios irreversibles sin plan B (DROP column sin backup).
- Falta de logging al ejecutar reversión.

---
Mantener este runbook sincronizado con infraestructura real.
