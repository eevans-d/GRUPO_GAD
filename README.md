# GAD - Gestión de Agentes en Disponibilidad

Sistema interno para gestionar personal policial (efectivos, turnos, licencias, tareas) a través de un bot de Telegram. El sistema está diseñado para ser ágil, de bajo costo y fácil de desplegar.

## Visión General

El proyecto GAD utiliza un stack de tecnologías modernas para proporcionar una solución eficiente para la gestión de personal. La interacción principal se realiza a través de un bot de Telegram, lo que permite un acceso rápido y fácil desde cualquier lugar.

**Componentes Principales:**
*   **API Backend:** Construida con FastAPI (Python).
*   **Base de Datos:** PostgreSQL.
*   **Interfaz de Usuario:** Bot de Telegram.
*   **Automatización y Workflows:** N8N.
*   **Orquestación:** Docker Compose.

## Quickstart (Puesta en Marcha)

Sigue estos pasos para tener el sistema funcionando en tu entorno local.

### Prerrequisitos
*   Docker y Docker Compose instalados.
*   Git (opcional, para clonar el repositorio).

### 1. Configura tus Credenciales

1.  Crea un nuevo archivo llamado `.env` en la raíz del proyecto.
2.  Copia el contenido de `.env.example` y pégalo en tu nuevo archivo `.env`.
3.  **Edita el archivo `.env`** y reemplaza los valores de ejemplo (`your_bot_token`, `your_admin_chat_id`, etc.) con tus credenciales reales.

### 2. Inicia los Servicios

Abre una terminal en la raíz del proyecto y ejecuta el siguiente comando para construir e iniciar todos los contenedores en segundo plano:

```bash
docker compose up -d
```

### 3. Inicializa la Base de Datos y N8N

Espera unos 30 segundos para que la base de datos se inicie completamente. Luego, ejecuta el script de inicialización:

```bash
bash scripts/bootstrap.sh
```

### 4. Verificación Final

1.  Para confirmar que todo está en marcha, ejecuta `docker ps`. Deberías ver cuatro contenedores en estado "Up": `gad-db`, `gad-api`, `gad-bot`, y `gad-n8n`.
2.  Accede a la interfaz de N8N en tu navegador: **http://localhost:5678**.
3.  Como indica la documentación, necesitarás **activar manualmente los workflows** (W1-W4) desde la interfaz de N8N por primera vez.

¡Y eso es todo! El sistema GAD debería estar completamente funcional en tu entorno local.
