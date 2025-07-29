# -----------------------------------------------------------------------------
# Bot del Cronista para la Superliga Dinámica
# -----------------------------------------------------------------------------

# --- 1. IMPORTACIONES ---
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
import unicodedata # <-- ¡NUEVA IMPORTACIÓN para quitar tildes!
import logging 



# --- 2. CONFIGURACIÓN INICIAL Y CONSTANTES ---

# --- ¡NUEVO! Configuración del Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
# --- 2. CONFIGURACIÓN INICIAL Y CONSTANTES ---

# Carga las variables de entorno (claves secretas)
load_dotenv()

# Configuración de la IA de Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("INFO: Conexión con Google Gemini establecida.")
else:
    gemini_model = None
    print("ADVERTENCIA: No se encontró GEMINI_API_KEY. Las funciones de IA estarán desactivadas.")

# Rutas a los archivos de datos
PERFILES_PATH = 'perfiles.json'
DECLARACIONES_PATH = 'declaraciones.json'

# --- ¡LISTA DE PALABRAS CLAVE MEJORADA Y AMPLIADA! ---
# Ahora todas las palabras están en minúsculas y SIN tildes.


def cargar_perfiles():
    """Carga los perfiles desde el archivo JSON de forma segura."""
    try:
        with open(PERFILES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_perfiles(perfiles):
    """Guarda la lista de perfiles actualizada en el archivo JSON."""
    with open(PERFILES_PATH, 'w', encoding='utf-8') as f:
        json.dump(perfiles, f, indent=4, ensure_ascii=False)

# --- 4. FUNCIONES DE LOS COMANDOS DEL BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mensaje de bienvenida al iniciar el bot."""
    await update.message.reply_text(
        "¡Bienvenido al Confesionario del Cronista!\n\n"
        "▫️ Usa /register para vincular tu cuenta.\n"
        "▫️ Usa /micronica para recibir un análisis personalizado.\n\n"
        "Una vez registrado, todo lo que escribas en este chat se guardará como una declaración oficial."
    )

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la lista de mánagers no registrados como botones."""
    perfiles = cargar_perfiles()
    if not perfiles:
        await update.message.reply_text("Error: No se ha podido cargar el archivo de perfiles.")
        return
    
    keyboard = []
    for perfil in perfiles:
        if "telegram_user_id" not in perfil or perfil.get("telegram_user_id") is None:
            keyboard.append([InlineKeyboardButton(perfil["nombre_mister"], callback_data=f"register_{perfil['id_manager']}")])
            
    if not keyboard:
        await update.message.reply_text("Parece que todos los mánagers ya están registrados. ¡No queda nadie por registrar!")
        return

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Por favor, selecciona tu nombre de la lista para iniciar el proceso de verificación:", reply_markup=reply_markup)

# En el archivo de tu bot (p.ej. bot_cronista.py)

# REEMPLAZA TU FUNCIÓN /micronica COMPLETA CON ESTA VERSIÓN
async def micronica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Genera una crónica personalizada para el usuario, entendiendo las menciones."""
    user = update.effective_user
    
    if not gemini_model:
        await update.message.reply_text("Lo siento, el Cronista está afónico hoy (servicio de IA no disponible).")
        return

    perfiles = cargar_perfiles()
    mi_perfil = next((p for p in perfiles if p.get('telegram_user_id') == user.id), None)

    if not mi_perfil:
        await update.message.reply_text("No estás registrado. Por favor, usa /register primero.")
        return

    # --- INICIO DE LA MEJORA ---
    mi_ultima_declaracion_texto = "No he encontrado declaraciones recientes."
    info_menciones = "" # Nueva variable para el contexto de las menciones

    try:
        with open(DECLARACIONES_PATH, 'r', encoding='utf-8') as f:
            declaraciones = json.load(f)
        
        # Buscamos el OBJETO completo de la última declaración, no solo el texto
        ultima_declaracion_obj = next((d for d in reversed(declaraciones) if d.get('telegram_user_id') == user.id), None)

        if ultima_declaracion_obj:
            mi_ultima_declaracion_texto = ultima_declaracion_obj.get('declaracion', mi_ultima_declaracion_texto)
            
            # ¡AQUÍ ESTÁ LA MAGIA! Comprobamos si hay menciones en esa declaración
            mencionados = ultima_declaracion_obj.get('mencionados', [])
            if mencionados:
                nombres_mencionados = [m['nombre_mister'] for m in mencionados]
                # Creamos el texto de contexto para la IA
                info_menciones = f"En esta declaración, el mánager se dirige o ataca a: {', '.join(nombres_mencionados)}."
                
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    # --- FIN DE LA MEJORA ---

    await update.message.reply_text("El Cronista está consultando sus notas y afilando su pluma... ✍️")
    
    # --- PROMPT MEJORADO ---
    prompt = f"""
    Eres un cronista deportivo legendario, ingenioso y con un toque de sarcasmo.
    Vas a analizar al siguiente mánager de nuestra liga fantasy:

    - Nombre del Mánager: {mi_perfil.get('nombre_mister', 'Desconocido')}
    - Su lema o apodo: {mi_perfil.get('apodo_lema', 'Sin lema conocido')}
    - Su estilo de juego: {mi_perfil.get('estilo_juego', 'Impredecible')}
    - Su última declaración a la prensa: "{mi_ultima_declaracion_texto}"
    - Contexto Adicional: "{info_menciones}"

    Misión: Escribe una crónica breve (2-3 frases), aguda y memorable sobre este mánager.
    IMPORTANTE: Si el 'Contexto Adicional' indica que ataca a otro mánager, tu crónica DEBE centrarse en ese pique. Esa es la noticia principal.
    """

    try:
        response = gemini_model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"El Cronista se ha quedado en blanco... (Error de la IA: {e})")

# --- 5. MANEJADORES DE INTERACCIONES (BOTONES Y MENSAJES) ---

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja todos los clics en los botones en línea (inline)."""
    query = update.callback_query
    await query.answer()
    callback_data = query.data
    user_id = query.from_user.id

    if callback_data.startswith("register_"):
        manager_id_seleccionado = callback_data.split("_")[1]
        perfiles = cargar_perfiles()
        nombre_mister = next((p["nombre_mister"] for p in perfiles if p["id_manager"] == manager_id_seleccionado), None)

        if not nombre_mister:
            await query.edit_message_text(text="Error: No se pudo encontrar a este mánager.")
            return

        context.user_data['selected_manager_id'] = manager_id_seleccionado
        context.user_data['selected_manager_name'] = nombre_mister
        context.user_data['verification_timestamp'] = datetime.now()
        
        keyboard = [[InlineKeyboardButton("✅ Confirmar mi Identidad", callback_data="confirm_final")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=f"Verificación iniciada para {nombre_mister}.\nRevisa tus mensajes privados para completar el registro (tienes 2 minutos).")
        
        texto_privado = (
            f"¡Hola! Has iniciado un registro para el mánager **{nombre_mister}**.\n\n"
            f"Por seguridad, es muy importante que seas tú quien confirme esta acción para evitar que alguien se registre en tu nombre.\n\n"
            f"Si eres tú, pulsa el botón de abajo para completar el proceso. (Caduca en 2 minutos)"
        )
        await context.bot.send_message(chat_id=user_id, text=texto_privado, reply_markup=reply_markup, parse_mode='Markdown')

    elif callback_data == "confirm_final":
        manager_id = context.user_data.get('selected_manager_id')
        manager_name = context.user_data.get('selected_manager_name')
        timestamp_inicio = context.user_data.get('verification_timestamp')

        if not manager_id or not timestamp_inicio:
            await query.edit_message_text(text="Ha ocurrido un error o el proceso ha caducado. Por favor, empieza de nuevo con /register.")
            return
            
        if datetime.now() - timestamp_inicio > timedelta(minutes=2):
            await query.edit_message_text(text="❌ **El tiempo de confirmación ha expirado.**\n\nPor seguridad, tienes que volver a iniciar el proceso con /register.")
            context.user_data.clear()
            return

        perfiles = cargar_perfiles()
        registro_exitoso = False
        for perfil in perfiles:
            if perfil["id_manager"] == manager_id:
                perfil["telegram_user_id"] = user_id
                registro_exitoso = True
                break
        
        if registro_exitoso:
            guardar_perfiles(perfiles)
            await query.edit_message_text(text=f"✅ ¡Verificación completada! Tu cuenta ha sido vinculada a **{manager_name}**.", parse_mode='Markdown')
        else:
            await query.edit_message_text(text="Error: No se pudo encontrar el perfil para completar el registro.")
            
        context.user_data.clear()

# En primer_test_bot.py

# En primer_test_bot.py

# En el archivo de tu bot (p.ej. bot_cronista.py)

# REEMPLAZA TU FUNCIÓN guardar_declaracion COMPLETA CON ESTA VERSIÓN
async def guardar_declaracion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Guarda un mensaje como declaración, identificando al autor y a los mánagers mencionados.
    Se activa solo cuando el mensaje contiene una mención al propio bot.
    """
    user = update.effective_user
    message = update.message
    bot_username = context.bot.username

    # Condición de activación: que mencionen al bot.
    if f"@{bot_username}" not in message.text:
        return 

    # 1. Cargar perfiles y verificar que el autor esté registrado
    perfiles = cargar_perfiles()
    perfil_autor = next((p for p in perfiles if p.get('telegram_user_id') == user.id), None)
        
    if not perfil_autor:
        logger.info(f"Mención ignorada de usuario no registrado: {user.first_name}")
        # Opcional: avisar al usuario que debe registrarse.
        # await message.reply_text("Te he oído, pero no sé quién eres. Usa /register para vincular tu cuenta.")
        return

    # 2. Identificar a los mánagers mencionados en el mensaje
    mencionados = []
    # Creamos un mapa de ID -> nombre para buscar fácilmente
    id_a_nombre = {p['telegram_user_id']: p['nombre_mister'] for p in perfiles if 'telegram_user_id' in p}

    if message.entities:
        for entity in message.entities:
            # Opción A: Mención directa con @username
            if entity.type == 'mention':
                username_mencionado = message.text[entity.offset:entity.offset + entity.length]
                # Podríamos buscar por username, pero es menos fiable. Es mejor usar text_mention.
                logger.info(f"Se usó una mención de texto ({username_mencionado}), se recomienda usar la mención que linkea al usuario.")

            # Opción B (la mejor): Mención que linkea al usuario (text_mention)
            elif entity.type == 'text_mention' and entity.user:
                id_mencionado = entity.user.id
                # Buscamos si el ID mencionado corresponde a un mánager registrado
                if id_mencionado in id_a_nombre:
                    # Evitamos añadir al propio autor o al bot si se mencionan a sí mismos
                    if id_mencionado != user.id and entity.user.username != bot_username.replace("@", ""):
                        mencionados.append({
                            "telegram_user_id": id_mencionado,
                            "nombre_mister": id_a_nombre[id_mencionado]
                        })

    # 3. Construir y guardar la declaración enriquecida
    texto_limpio = message.text.replace(f"@{bot_username}", "").strip()

    nueva_declaracion = {
        "message_id": message.message_id,
        "reply_to_message_id": message.reply_to_message.message_id if message.reply_to_message else None,
        "telegram_user_id": user.id,
        "nombre_mister": perfil_autor['nombre_mister'],
        "declaracion": texto_limpio,
        "timestamp": datetime.now().isoformat(),
        "mencionados": mencionados  # <-- ¡Aquí está la nueva información!
    }
    
    logger.info(f"✅ GUARDANDO declaración de '{perfil_autor['nombre_mister']}' mencionando a: {[m['nombre_mister'] for m in mencionados]}")

    try:
        with open(DECLARACIONES_PATH, 'r', encoding='utf-8') as f:
            declaraciones = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        declaraciones = []
        
    declaraciones.append(nueva_declaracion)
    
    with open(DECLARACIONES_PATH, 'w', encoding='utf-8') as f:
        json.dump(declaraciones, f, indent=4, ensure_ascii=False)

# --- 6. FUNCIÓN PRINCIPAL (main) ---

def main() -> None:
    """Inicia el bot y configura todos los manejadores de forma limpia."""
    
    # Carga el TOKEN desde el archivo .env
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        # Usamos logger en lugar de print para los errores críticos
        logger.critical("Error Crítico: No se encontró el TELEGRAM_TOKEN en el archivo .env")
        print("Error Crítico: No se encontró el TELEGRAM_TOKEN en el archivo .env")
        return

    # Crea la aplicación del bot
    application = Application.builder().token(TOKEN).build()
    
    # 1. Añadimos los manejadores para los COMANDOS
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("micronica", micronica))
    application.add_handler(CommandHandler("declaraciones", abrir_declaraciones)) # <-- NUEVO COMANDO

    # 2. Añadimos el manejador para los BOTONES
    application.add_handler(CallbackQueryHandler(button_callback))

    # 3. Nuestro manejador de mensajes ahora solo se activa si hay una mención.
    # Es mucho más eficiente y limpio.
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Entity("mention"), 
        guardar_declaracion
    ))
    
    # Inicia el bot
    print("Bot del Cronista iniciado. ¡Listo para la acción!")
    application.run_polling()


# Ruta para guardar el ID del mensaje anclado
BOT_STATE_PATH = 'bot_state.json'

async def abrir_declaraciones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Publica y ancla el mensaje para iniciar la recogida de declaraciones."""
    
    # (Opcional: puedes añadir aquí una comprobación para que solo los admins puedan usarlo)
    
    # 1. Desanclar el mensaje antiguo si existe
    try:
        with open(BOT_STATE_PATH, 'r') as f:
            state = json.load(f)
            old_message_id = state.get('pinned_message_id')
            if old_message_id:
                await context.bot.unpin_chat_message(chat_id=update.message.chat_id)
                print(f"INFO: Desanclado mensaje anterior {old_message_id}.")
    except (FileNotFoundError, json.JSONDecodeError):
        pass # No hay estado guardado, no hacemos nada

    # 2. Enviar el nuevo mensaje
    bot_username = context.bot.username
    texto_anuncio = (
        f"🎙️ **¡Rueda de Prensa Abierta!** 🎙️\n\n"
        f"Para que el Cronista escuche tus declaraciones para el próximo reporte, "
        f"menciona a @{bot_username} en tu mensaje.\n\n"
        f"¡La afición espera tus palabras!"
    )
    
    mensaje_enviado = await update.message.reply_text(texto_anuncio, parse_mode='Markdown')
    
    # 3. Anclar el nuevo mensaje
    await context.bot.pin_chat_message(
        chat_id=update.message.chat_id,
        message_id=mensaje_enviado.message_id,
        disable_notification=False # Notifica al grupo que se ha anclado
    )
    
    # 4. Guardar el ID del nuevo mensaje anclado
    with open(BOT_STATE_PATH, 'w') as f:
        json.dump({'pinned_message_id': mensaje_enviado.message_id}, f)
        
    print(f"INFO: Nuevo mensaje de declaraciones ({mensaje_enviado.message_id}) publicado y anclado.")


if __name__ == "__main__":
    main()
