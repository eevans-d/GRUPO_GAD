# Estrategia de Backup y Restauración para GRUPO_GAD

Este documento describe la estrategia de backup y restauración para la base de datos PostgreSQL del proyecto GRUPO_GAD.

## Resumen

La estrategia implementa:
- **Backups programados** dos veces al día (1:00 AM y 1:30 PM)
- **Respaldo local** con retención configurable (por defecto 7 días)
- **Respaldo en la nube** (opcional) en Amazon S3 con retención configurable (por defecto 30 días)
- **Verificación de integridad** mediante hashes SHA-256
- **Metadatos** para cada backup con información relevante
- **Procedimiento de restauración** documentado y probado

## Componentes

### 1. Scripts de Backup y Restauración

Se han desarrollado dos scripts principales:

- **`postgres_backup.sh`**: Realiza el backup de la base de datos, calcula el hash para verificación de integridad, almacena metadatos y opcionalmente sube el backup a S3.
- **`postgres_restore.sh`**: Restaura la base de datos a partir de un backup, verificando previamente su integridad mediante el hash SHA-256.

### 2. Servicio de Backup Programado

Se ha implementado un servicio Docker (`docker-compose.backup.yml`) que ejecuta los backups de forma programada mediante cron.

## Configuración

### Variables de Entorno

Los scripts utilizan las siguientes variables de entorno (con valores por defecto):

```
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_NAME=grupogad
DB_PASSWORD=<requerido>
BACKUP_DIR=/backups
RETENTION_DAYS=7
S3_BUCKET=<opcional>
S3_PREFIX=grupogad/backups/
S3_RETENTION_DAYS=30
```

Para AWS S3, también son necesarias:
```
AWS_ACCESS_KEY_ID=<requerido para S3>
AWS_SECRET_ACCESS_KEY=<requerido para S3>
AWS_DEFAULT_REGION=us-east-1
```

## Procedimientos

### Cómo ejecutar un backup manual

```bash
# Usando make (recomendado)
make backup

# Con Docker Compose
docker-compose -f docker-compose.backup.yml run --rm backup bash /scripts/postgres_backup.sh

# Localmente (requiere acceso directo a la base de datos)
DB_HOST=localhost DB_PASSWORD=your_password ./scripts/backup/postgres_backup.sh
```

### Cómo configurar backups programados

1. Asegúrate de que las variables de entorno estén configuradas correctamente en tu `.env` o archivo de variables de entorno.
2. Ejecuta el servicio de backup:
```bash
# Usando make (recomendado)
make backup-service

# O directamente con Docker Compose
docker-compose -f docker-compose.backup.yml up -d
```

### Cómo verificar un backup existente

```bash
# Ver lista de backups disponibles
make backup-list

# Verificar un backup específico usando make
make backup-verify BACKUP_FILE=backups/postgres_grupogad_20251006T120000Z.sql.gz

# O directamente con el script
./scripts/backup/postgres_restore.sh /ruta/al/backup.sql.gz --verify-only
```

### Cómo restaurar un backup

> ⚠️ **ADVERTENCIA**: Este procedimiento sobrescribirá todos los datos actuales en la base de datos destino.

```bash
# Ver lista de backups disponibles
make backup-list

# Restaurar un backup usando make (recomendado)
make backup-restore BACKUP_FILE=backups/postgres_grupogad_20251006T120000Z.sql.gz

# Con Docker Compose
docker-compose -f docker-compose.backup.yml run --rm backup bash /scripts/postgres_restore.sh /backups/nombre_del_backup.sql.gz

# Localmente
DB_HOST=localhost DB_PASSWORD=your_password ./scripts/backup/postgres_restore.sh /ruta/al/backup.sql.gz
```

## Monitoreo y Mantenimiento

### Logs

Los logs de backup se almacenan en:
- Backups programados: `/backups/cron.log`
- Cada backup individual: `/backups/backup_[timestamp].log`
- Cada restauración: `/backups/restore_[timestamp].log`

### Rotación de Backups

- Los backups locales se eliminan automáticamente después de `RETENTION_DAYS` días (por defecto 7).
- Los backups en S3 se eliminan después de `S3_RETENTION_DAYS` días (por defecto 30).

## Escenario de Recuperación ante Desastres

### Pasos para recuperación completa

1. Instala PostgreSQL o despliega el contenedor de la base de datos.
2. Localiza el backup más reciente (local o en S3).
3. Ejecuta el script de restauración:
   ```bash
   ./scripts/backup/postgres_restore.sh /ruta/al/backup.sql.gz
   ```
4. Verifica la integridad de los datos restaurados.
5. Ejecuta las migraciones de Alembic si es necesario:
   ```bash
   alembic upgrade head
   ```
6. Reinicia los servicios que dependen de la base de datos.

## Pruebas y Validación

La estrategia de backup y restauración debe probarse regularmente para garantizar su eficacia. Se recomienda:

1. Realizar una restauración de prueba mensualmente en un entorno de staging.
2. Documentar los resultados de las pruebas.
3. Ajustar el procedimiento según sea necesario.

## Consideraciones para Producción

- En un entorno de producción, es altamente recomendable configurar el almacenamiento en S3 o un servicio similar.
- Considerar el cifrado de backups para datos sensibles.
- Mantener copias en múltiples regiones geográficas para mayor seguridad.

---

Última actualización: 2025-10-06