from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import os
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL") # Should be http://api:8000/api/v1
WHITELIST = set(map(int, os.getenv("WHITELIST_IDS", "").split(',')))

def get_user_auth_level(telegram_id: int):
    """Gets user authentication level from the API."""
    try:
        response = requests.get(f"{API_URL}/auth/{telegram_id}")
        if response.status_code == 200:
            return response.json().get("nivel")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not contact API for auth: {e}")
        return None

def start(update, context):
    """Sends a welcome message."""
    update.message.reply_text('Bienvenido al Bot de Gestión de Agentes (GAD).')

def crear_tarea(update, context):
    """
    Crea una nueva tarea.
    Formato: /crear <código> <título> <tipo> <id_delegado> <id_asignado1> <id_asignado2> ...
    Ejemplo: /crear TSK-01 "Patrullaje Zona Norte" patrullaje 1 2 3
    """
    user_id = update.message.from_user.id
    if user_id not in WHITELIST:
        update.message.reply_text("No estás autorizado para usar este bot.")
        return

    nivel = get_user_auth_level(user_id)
    if nivel != '3':
        update.message.reply_text("No tienes el nivel de autorización suficiente (Nivel 3 requerido).")
        return

    args = context.args
    if len(args) < 5:
        update.message.reply_text(
            "Formato incorrecto. Uso:\n"
            "/crear <código> <título> <tipo> <id_delegado> <id_asignado1> [id_asignado2]..."
        )
        return

    try:
        codigo, titulo, tipo, delegado_id, *asignados_ids_str = args
        asignados_ids = [int(id_str) for id_str in asignados_ids_str]
        
        payload = {
            "codigo": codigo,
            "titulo": titulo,
            "tipo": tipo,
            "delegado_usuario_id": int(delegado_id),
            "asignados_ids": asignados_ids,
            "nivel_solicitante": nivel
        }

        response = requests.post(f"{API_URL}/tareas", json=payload)

        if response.status_code == 201:
            update.message.reply_text(f"Tarea '{codigo}' creada exitosamente.")
        else:
            update.message.reply_text(f"Error al crear la tarea: {response.json().get('detail', 'Error desconocido')}")

    except (ValueError, TypeError):
        update.message.reply_text("Error en los argumentos. Asegúrate de que los IDs sean números.")
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed in crear_tarea: {e}")
        update.message.reply_text("Error de comunicación con el sistema. Inténtalo de nuevo más tarde.")


def finalizar_handler(update, context):
    """
    Finaliza una tarea usando una frase clave o comando.
    Ejemplo: "LISTO TSK-01" o "/finalizar TSK-01"
    """
    user_id = update.message.from_user.id
    if user_id not in WHITELIST:
        update.message.reply_text("No estás autorizado.")
        return

    msg_text = update.message.text
    
    # Extraer código de la tarea
    try:
        if msg_text.lower().startswith("listo") or msg_text.lower().startswith("/finalizar"):
            codigo_tarea = msg_text.split()[-1]
        else:
            return # No es un mensaje de finalización
    except IndexError:
        return # Mensaje vacío o mal formado

    payload = {"telegram_id": user_id}
    
    try:
        response = requests.post(f"{API_URL}/tareas/{codigo_tarea}/finalizar", json=payload)
        
        if response.status_code == 200:
            update.message.reply_text(response.json().get("status"))
        else:
            update.message.reply_text(f"Error: {response.json().get('detail', 'No se pudo finalizar la tarea.')}")

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed in finalizar_handler: {e}")
        update.message.reply_text("Error de comunicación con el sistema.")


def main():
    """Start the bot."""
    if not TOKEN or not API_URL:
        logger.critical("Error: Las variables de entorno TELEGRAM_TOKEN y API_URL deben estar definidas.")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # --- Handlers ---
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("crear", crear_tarea, pass_args=True))
    dp.add_handler(CommandHandler("finalizar", finalizar_handler))
    dp.add_handler(MessageHandler(Filters.regex(r'^(?i)listo\s+\S+'), finalizar_handler))

    # Log all errors
    dp.add_error_handler(lambda update, context: logger.warning('Update "%s" caused error "%s"', update, context.error))

    # Start the Bot
    updater.start_polling()
    logger.info("Bot iniciado y escuchando...")
    updater.idle()

if __name__ == '__main__':
    main()