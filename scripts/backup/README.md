# Scripts de Backup y Restauración

Este directorio contiene los scripts para la gestión de backups de la base de datos PostgreSQL del proyecto GRUPO_GAD.

## Scripts Disponibles

### `postgres_backup.sh`

Script para crear backups de la base de datos PostgreSQL.

**Características:**
- Generación de dumps comprimidos con formato `.sql.gz`
- Cálculo de hashes SHA-256 para verificación de integridad
- Generación de metadatos sobre el backup
- Soporte para almacenamiento local y en S3
- Retención configurable (eliminación de backups antiguos)

**Uso:**
```bash
# Uso básico
./postgres_backup.sh

# Con variables de entorno personalizadas
DB_HOST=localhost DB_PASSWORD=mysecret ./postgres_backup.sh
```

### `postgres_restore.sh`

Script para restaurar la base de datos desde un backup.

**Características:**
- Verificación de integridad mediante hash SHA-256
- Confirmación interactiva antes de sobrescribir datos
- Modo de solo verificación (--verify-only)
- Ejecución automática de migraciones post-restauración

**Uso:**
```bash
# Ver ayuda
./postgres_restore.sh

# Verificar un backup sin restaurar
./postgres_restore.sh /ruta/al/backup.sql.gz --verify-only

# Restaurar un backup
./postgres_restore.sh /ruta/al/backup.sql.gz
```

## Comandos Make

Para mayor comodidad, estos scripts pueden ejecutarse a través de comandos `make`:

```bash
# Ejecutar un backup manual
make backup

# Listar backups disponibles
make backup-list

# Verificar un backup
make backup-verify BACKUP_FILE=backups/nombre_del_backup.sql.gz

# Restaurar un backup
make backup-restore BACKUP_FILE=backups/nombre_del_backup.sql.gz

# Iniciar el servicio de backup programado
make backup-service

# Detener el servicio de backup programado
make backup-service-down
```

## Documentación

Para información detallada sobre la estrategia de backup y restauración, consulta:
- [Estrategia de Backup y Restauración](../../docs/BACKUP_RESTORE_STRATEGY.md)