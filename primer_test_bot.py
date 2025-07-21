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


# --- 3. FUNCIONES DE AYUDA (MANEJO DE ARCHIVOS) ---

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

async def micronica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Genera una crónica personalizada para el usuario."""
    user = update.effective_user
    
    if not gemini_model:
        await update.message.reply_text("Lo siento, el Cronista está afónico hoy (servicio de IA no disponible).")
        return

    perfiles = cargar_perfiles()
    mi_perfil = next((p for p in perfiles if p.get('telegram_user_id') == user.id), None)

    if not mi_perfil:
        await update.message.reply_text("No estás registrado. Por favor, usa /register primero.")
        return

    mi_ultima_declaracion = "No he encontrado declaraciones recientes."
    try:
        with open(DECLARACIONES_PATH, 'r', encoding='utf-8') as f:
            declaraciones = json.load(f)
        for declaracion in reversed(declaraciones):
            if declaracion.get('telegram_user_id') == user.id:
                mi_ultima_declaracion = declaracion['declaracion']
                break
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    await update.message.reply_text("El Cronista está consultando sus notas y afilando su pluma... ✍️")
    
    prompt = f"""
    Eres un cronista deportivo legendario, ingenioso y con un toque de sarcasmo.
    Vas a analizar al siguiente mánager de nuestra liga fantasy:

    - Nombre del Mánager: {mi_perfil.get('nombre_mister', 'Desconocido')}
    - Su lema o apodo: {mi_perfil.get('apodo_lema', 'Sin lema conocido')}
    - Su estilo de juego: {mi_perfil.get('estilo_juego', 'Impredecible')}
    - Su última declaración a la prensa: "{mi_ultima_declaracion}"

    Misión: Escribe una crónica breve (2-3 frases), aguda y memorable sobre este mánager.
    Conecta su estilo o su apodo con su última declaración. Sé creativo y punzante. No seas genérico.
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

async def guardar_declaracion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Guarda cualquier mensaje de texto como una declaración oficial si el usuario está registrado."""
    user = update.effective_user
    perfiles = cargar_perfiles()
    nombre_mister_registrado = next((p['nombre_mister'] for p in perfiles if p.get('telegram_user_id') == user.id), None)
    
    if not nombre_mister_registrado:
        await update.message.reply_text("No estás registrado. Por favor, usa /register para vincular tu cuenta primero.")
        return
    
    texto_recibido = update.message.text
    print(f"Guardando declaración de {nombre_mister_registrado}: '{texto_recibido}'")

    nueva_declaracion = { "telegram_user_id": user.id, "nombre_mister": nombre_mister_registrado, "declaracion": texto_recibido, "timestamp": datetime.now().isoformat()}
    
    try:
        with open(DECLARACIONES_PATH, 'r', encoding='utf-8') as f:
            declaraciones = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        declaraciones = []
        
    declaraciones.append(nueva_declaracion)
    
    with open(DECLARACIONES_PATH, 'w', encoding='utf-8') as f:
        json.dump(declaraciones, f, indent=4, ensure_ascii=False)
        
    await update.message.reply_text('📝 ¡Declaración registrada!')

# --- 6. FUNCIÓN PRINCIPAL (main) ---

def main() -> None:
    """Inicia el bot y configura todos los manejadores."""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error Crítico: No se encontró el TELEGRAM_TOKEN en el archivo .env")
        return

    application = Application.builder().token(TOKEN).build()
    
    # Añadimos los manejadores para los comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("micronica", micronica))
    
    # Añadimos el manejador para los botones
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Añadimos el manejador para los mensajes de texto (debe ser el último)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_declaracion))
    
    print("Bot del Cronista iniciado. ¡Listo para la acción!")
    application.run_polling()

if __name__ == "__main__":
    main()