# Especificación Técnica: GRUPO GAD

**Versión:** 1.0
**Fecha:** 2025-09-23
**Estado:** Documento Base Consolidado

## 1. Resumen del Proyecto

### 1.1. Objetivo
El proyecto `GRUPO_GAD` es una plataforma de software integral diseñada para la gestión de operaciones de seguridad, tareas y usuarios. El sistema combina un backend de API robusto, una base de datos geoespacial, una interfaz de bot de Telegram y un dashboard administrativo para proporcionar un control centralizado y en tiempo real de las operaciones.

### 1.2. Stack Tecnológico Principal
- **Backend:** Python 3.12+ con **FastAPI**.
- **Base de Datos:** **PostgreSQL** con la extensión **PostGIS** para capacidades geoespaciales.
- **ORM:** **SQLAlchemy** en modo asíncrono.
- **Migraciones de BD:** **Alembic**.
- **Interfaz de Chat:** Bot de **Telegram** (`python-telegram-bot`).
- **Caché:** **Redis** para sesiones y datos de acceso frecuente.
- **Proxy Inverso y Servidor Web:** **Caddy**.
- **Gestión de Dependencias:** **Poetry**.
- **Contenerización:** **Docker** y Docker Compose.

## 2. Arquitectura del Sistema

La arquitectura es un monorepo que orquesta cinco servicios principales a través de Docker Compose, diseñados para trabajar en conjunto:

1.  **`api` (Servicio Principal):** El núcleo del sistema. Una API RESTful en FastAPI que expone endpoints para la gestión de usuarios, tareas, proyectos y datos geoespaciales. También sirve el dashboard administrativo.
2.  **`db` (Base de Datos):** Una instancia de PostgreSQL + PostGIS que persiste todos los datos de la aplicación. Su esquema es gestionado por Alembic.
3.  **`redis` (Caché):** Un servidor Redis utilizado para cacheo de datos, mejorando el rendimiento y la velocidad de respuesta.
4.  **`bot` (Interfaz de Chat):** Un bot de Telegram que actúa como una interfaz para que los usuarios interactúen con la API, permitiendo la creación y gestión de tareas desde el chat.
5.  **`caddy` (Proxy Inverso):** Actúa como el punto de entrada al sistema, gestionando el tráfico HTTP, enrutándolo a la API y manejando automáticamente los certificados SSL/TLS en producción.

## 3. Funcionalidad Principal

### 3.1. Gestión de Entidades (API RESTful)
El sistema proporciona endpoints CRUD (Crear, Leer, Actualizar, Eliminar) completos para las siguientes entidades:
- **Usuarios:** Gestión de altas, bajas y modificaciones de usuarios del sistema.
- **Tareas:** Creación, asignación, actualización y eliminación de tareas operativas.
- **Proyectos y Clientes:** Estructuras para organizar tareas y usuarios.

### 3.2. Interacción con Bot de Telegram
El bot permite a los usuarios realizar operaciones clave de forma remota:
- **/start:** Inicia la interacción y da la bienvenida.
- **/crear:** Permite crear una nueva tarea directamente desde un mensaje de chat.
- **/finalizar:** Permite marcar una tarea como completada.

### 3.3. Dashboard Administrativo
Una interfaz web (SPA) servida por la API que proporciona una vista de solo lectura del estado de las tareas y los efectivos, permitiendo el monitoreo de las operaciones en tiempo real.

### 3.4. Capacidades Geoespaciales
Gracias a PostGIS, el sistema puede almacenar y consultar datos de geolocalización, sentando las bases para funcionalidades de mapas, seguimiento de efectivos y asignación de tareas por proximidad.

## 4. API Endpoints Clave

- **Autenticación:**
  - `POST /auth/login`: Intercambia credenciales de usuario por un token de acceso JWT.
- **Usuarios:**
  - `GET /users/`: Lista todos los usuarios.
  - `POST /users/`: Crea un nuevo usuario (requiere permisos de superusuario).
  - `GET /users/me`: Devuelve los datos del usuario autenticado.
- **Tareas:**
  - `GET /tasks/`: Lista todas las tareas.
  - `POST /tasks/`: Crea una nueva tarea.
  - `PUT /tasks/{task_id}`: Actualiza una tarea existente.
  - `DELETE /tasks/{task_id}`: Elimina una tarea.
- **Sistema:**
  - `GET /health`: Endpoint de health check que devuelve `{"status": "ok"}`.

## 5. Autenticación y Seguridad

- **Autenticación:** Se basa en el estándar **OAuth2 con tokens JWT**. El acceso a los endpoints protegidos requiere un `Bearer token` en la cabecera `Authorization`.
- **Autorización:** El sistema diferencia entre usuarios regulares y superusuarios, restringiendo el acceso a endpoints críticos (ej. creación de usuarios) solo a administradores.
- **Contraseñas:** Se almacenan hasheadas de forma segura utilizando la librería `passlib`.
- **Validación de Datos:** Se utiliza **Pydantic** en todos los endpoints para una validación robusta de los datos de entrada, previniendo ataques de inyección y asegurando la integridad de los datos.

## 6. Configuración y Despliegue

- **Configuración:** El sistema se configura a través de variables de entorno definidas en un archivo `.env`. Un `.env.example` sirve como plantilla.
- **Variables Críticas:**
  - `DATABASE_URL`: La cadena de conexión a la base de datos PostgreSQL.
  - `TELEGRAM_BOT_TOKEN`: El token secreto para operar el bot de Telegram.
  - `SECRET_KEY`: Clave para la firma de los tokens JWT.
- **Despliegue (Docker):** El método recomendado para el despliegue es a través de Docker Compose, utilizando el archivo `docker-compose.yml` que orquesta los 5 servicios. Se proporciona un `docker-compose.prod.yml` para configuraciones específicas de producción.

## 7. Pruebas y Calidad de Código

- **Pruebas:** El proyecto incluye una suite de tests (`pytest`) que cubren la funcionalidad de la API y la lógica de negocio.
- **Calidad de Código:** Se utilizan herramientas de análisis estático como `ruff` (linter) y `mypy` (type checker) para asegurar la calidad y consistencia del código.
- **CI/CD:** El repositorio está configurado con GitHub Actions para ejecutar automáticamente los chequeos de calidad y las pruebas en cada cambio, asegurando la estabilidad de la base de código.
