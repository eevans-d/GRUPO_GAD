# Runbooks de Operación

Este documento proporciona guías operativas para el mantenimiento, backup, y gestión de incidentes del sistema GAD. Está basado en la sección "Pruebas y Operación" y "Contingencias" del GAD Agile Kit.

## Backup y Restore

### Backup

El backup de la base de datos PostgreSQL se realiza con `pg_dump`. Este comando se puede ejecutar manualmente o automatizar con un cronjob en el host.

**Comando de Backup:**
```bash
# Ejecutar desde el host que corre Docker
docker exec gad-db pg_dump -U <DB_USER> -d gad > backup_`date +%Y%m%d`.sql
```
*Reemplaza `<DB_USER>` con el usuario de la base de datos definido en tu `.env` (por defecto es `user`).*

### Restore

La restauración se realiza borrando la base de datos actual (si existe) y cargando el backup con `psql`.

**Comandos de Restore:**
```bash
# 1. Borrar la base de datos existente (si es necesario)
docker exec -i gad-db dropdb -U <DB_USER> gad

# 2. Crear una nueva base de datos vacía
docker exec -i gad-db createdb -U <DB_USER> gad

# 3. Restaurar desde el archivo de backup
cat backup.sql | docker exec -i gad-db psql -U <DB_USER> -d gad
```

## Gestión de Incidentes

### Pasos Iniciales

1.  **Revisar Logs:** Es el primer paso para diagnosticar cualquier problema. Revisa los logs de los contenedores relevantes.
    ```bash
    # Ver logs de la API
    docker logs gad-api

    # Ver logs del Bot
    docker logs gad-bot

    # Ver logs de N8N
    docker logs gad-n8n
    ```

2.  **Reiniciar Servicios:** Si un componente no responde, un reinicio es a menudo la solución más rápida.
    ```bash
    # Reiniciar un servicio específico (e.g., el bot)
    docker compose restart bot

    # Reiniciar todos los servicios
    docker compose restart
    ```

### Monitoreo

El estado del sistema se puede monitorear de forma básica a través del endpoint de health check de la API.

**Comando de Monitoreo:**
```bash
# Ejecutar desde el host
curl http://localhost:8000/health
```
*Se espera una respuesta `{"status": "ok"}`. Esto se puede integrar en un script de monitoreo que se ejecute cada 5 minutos.*

## Mantenimiento

*   **Rotación de Tokens:** El token del bot de Telegram (`TELEGRAM_TOKEN` en `.env`) debe ser rotado periódicamente (e.g., cada 3-6 meses) por seguridad. Después de actualizar el `.env`, reinicia el servicio del bot.
    ```bash
    docker compose restart bot
    ```
*   **Limpieza de Datos:** Para mantener el rendimiento de la base de datos, los eventos o tareas muy antiguas (>90 días) pueden ser archivados o eliminados.
    ```sql
    -- Ejemplo de query para borrar tareas finalizadas hace más de 90 días
    DELETE FROM gad.tareas WHERE estado = 'finalizada' AND fin_real < NOW() - INTERVAL '90 days';
    ```
