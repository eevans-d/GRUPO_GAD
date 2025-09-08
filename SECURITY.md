# SECURITY.md — Política mínima de seguridad y rotación de secretos

Este archivo describe pasos rápidos para la rotación de secretos, reporte de vulnerabilidades
y contactos recomendados.

1) Rotación de secretos expuestos
- Si una credencial se ha confirmado en el repositorio, rotarla inmediatamente:
  - Generar nueva contraseña/clave.
  - Actualizar el secret en GitHub (Settings > Secrets) con el nombre correspondiente.
  - Invalidar la credencial anterior (por ejemplo, generar nueva contraseña en la BD o revocar token).
  - Auditar logs y despliegues recientes por actividad sospechosa.

2) Lista de secretos recomendados (nombres en GitHub Secrets)
- POSTGRES_PASSWORD
- POSTGRES_USER
- POSTGRES_DB
- DATABASE_URL
- SECRET_KEY
- TELEGRAM_TOKEN
- DOCKER_USERNAME
- DOCKER_PASSWORD

3) Respuesta a incidentes rápidas
- Contener: eliminar accesos temporales o rotar credenciales inmediatamente.
- Notificar: responsable de seguridad y propietario del repo.
- Analizar logs: verificar accesos anómalos y puntos de despliegue.
- Restaurar: desplegar con credenciales rotadas y monitorizar.

4) Herramientas recomendadas
- pip-audit, gitleaks, semgrep, pre-commit hooks

5) Contactos (rellenar en CONTRIBUTING.md)
- Owner: @your-github-username
- Infra/DB: equipo-infra@example.com
- Seguridad: security@example.com

Mantener este archivo con la versión mínima; para procesos y runbooks largos, referenciar la documentación de la organización.
