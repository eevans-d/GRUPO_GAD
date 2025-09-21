# Rotación de secretos - GRUPO_GAD

Este documento describe los pasos recomendados para rotar y revocar credenciales que estaban expuestas en el repositorio (por ejemplo: `.env.production`).

1) Preparación
   - Asegúrate de tener un backup del repositorio: `scripts/prepare_repo_backup.sh` ya creado.
   - Notifica al equipo: coordina ventana de mantenimiento.

2) Rotar secretos en proveedores
   - Base de datos: crear nueva contraseña de DB y actualizar usuarios/roles según proveedor (RDS/Managed DB o contenedor PostgreSQL).
   - JWT/SECRET_KEY: generar nuevo secreto con entropía mínima de 32 bytes (ej: `openssl rand -hex 32`).
   - Telegram: revocar y crear un nuevo bot token si es necesario.
   - Otros servicios: rotar claves API en sus respectivos paneles.

3) Actualizar entornos
   - Actualiza variables de entorno en staging/production (.env en servidores, secrets manager, orchestrator).
   - No commitees `.env.production` con valores reales.

4) Limpiar historial Git (opcional, destructivo)
   - Clona espejo: `git clone --mirror <repo> repo-mirror.git`
   - Usar `git-filter-repo` (recomendado): `git filter-repo --invert-paths --paths .env.production`
   - Alternativa BFG: `bfg --delete-files .env.production repo-mirror.git`
   - Empuja forzado: `git push --force --all` y `git push --force --tags`
   - Aviso: todos los colaboradores deberán reclonar o resetear sus clones.

5) Post-rotación
   - Verifica que la aplicación en staging/prod arranca con las nuevas credenciales.
   - Revocar tokens antiguos en proveedores cuando corresponda.
   - Actualiza `docs/GUARDRAILS_REGISTRY.md` con timestamp y ruta de backup.

6) Checklist mínimo
   - [ ] Backup creado
   - [ ] Credenciales rotadas en proveedor
   - [ ] Entornos actualizados
   - [ ] Historial limpiado (si aplica)
   - [ ] Equipo notificado

Notas: Este flujo es operador-driven. No ejecutes la limpieza destructiva sin coordinación y backups.
