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

# --- FUNCIÓN DE AYUDA PARA NORMALIZAR TEXTO ---
def normalizar_texto(texto: str) -> str:
    """Convierte un texto a minúsculas y le quita las tildes."""
    # Transforma a una forma donde los acentos son caracteres separados
    nfkd_form = unicodedata.normalize('NFD', texto.lower())
    # Devuelve solo los caracteres que no son acentos
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

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
PALABRAS_CLAVE_INTERES = [
    # --- 1. Bravuconadas / Venirse Arriba ---
    'abusica', 'abuson', 'arrasar', 'arraso', 'bisho', 'bisha', 'campeon', 
    'el mejor', 'er puto amo', 'estoy que me salgo', 'facil', 'fasi', 'ganamos', 
    'ganao', 'ganar', 'ganare', 'gane', 'gano', 'imparable', 'invencible', 
    'lide', 'lider', 'liderato', 'maki', 'makina', 'maquina', 'maquinaria', 
    'maquinon', 'mejor', 'nadie me gana', 'os gano', 'os reviento', 'paliza', 
    'paseito', 'paseo', 'rey', 'repaso', 'reviento', 'sobrao', 'sobrado', 
    'ta chupao', 'victoria', 

    # --- 2. Quejas / Polémicas / Lloriqueos ---
    'amañao', 'amañado', 'arbitraje', 'arbitro', 'cherra', 'chiripa', 'chorra', 
    'churre', 'comprao', 'comprado', 'er var', 'excusa', 'guensa', 'injusticia', 
    'injusto', 'llorando', 'llorar', 'llorera', 'llorica', 'lloron', 'me cago en', 
    'mierda', 'no veas', 'potra', 'puta', 'robao', 'robado', 'robaron', 'robo', 
    'suerte', 'tiene cohone', 'tongo', 'trampa', 'var', 'vaya tela', 'verguensa', 
    'verguenza',

    # --- 3. Insultos / Piques / "Trash Talk" ---
    'acabao', 'acabado', 'bcazas', 'bocazas', 'cenutrio', 'cerdaca', 'cerda', 
    'cerdo', 'cerdon', 'cojo', 'cono', 'eres malisimo', 'esmayao', 'fantasma', 
    'horrible', 'humo', 'illo', 'jartible', 'malaje', 'malo', 'malisimo', 'manco', 
    'manta', 'matao', 'merluso', 'muerto', 'pa casa', 'pa tu casa', 'paquete de', 
    'paquete', 'paqueton', 'papafrita', 'pejcao', 'penoso', 'petardo', 'porcon', 
    'puerca', 'remando', 'remar', 'retirate', 'sieso', 'tieso', 'tuercebotas', 
    'vendemotos',

    # --- 4. Mercado / Fichajes / Los Tacos ---
    'birlar', 'clausula', 'clausulazo', 'compro', 'dinero', 'fichado', 'fichaje', 
    'fichao', 'fichar', 'levantar', 'mercado', 'millones', 'pasta', 'pelas', 
    'puja', 'pujar', 'robar jugador', 'soltar la gallina', 'vendido', 'vendo', 
    'vender', 

    # --- 5. Táctica / El Equipo ---
    'alineacion', 'banquillazo', 'banquillo', 'chupar banquillo', 'dique seco', 
    'equipo', 'equipaso', 'equipucho', 'formacion', 'jugadores', 'lesion', 
    'lesionao', 'lesionado', 'mister', 'planteamiento', 'roto', 'tactica'
]
MIN_MESSAGE_LENGTH = 7 # Longitud mínima de un mensaje para ser considerado
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

# En primer_test_bot.py

# En primer_test_bot.py

# REEMPLAZA TU FUNCIÓN guardar_declaracion COMPLETA CON ESTA VERSIÓN
async def guardar_declaracion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Guarda mensajes de texto si cumplen los criterios de relevancia,
    verificando la identidad del usuario ANTES de proceder.
    """
    user = update.effective_user
    texto_recibido = update.message.text
    
    timestamp_log = datetime.now().strftime('%H:%M:%S.%f')
    print(f"\n[{timestamp_log}] MENSAJE RECIBIDO de '{user.first_name}': '{texto_recibido}'")

    # --- 1. VERIFICACIÓN DE IDENTIDAD ---
    # Es lo primero que hacemos. Si no sabemos quién es, no seguimos.
    perfiles = cargar_perfiles()
    nombre_mister_registrado = None
    
    for perfil in perfiles:
        if perfil.get('telegram_user_id') == user.id:
            nombre_mister_registrado = perfil['nombre_mister']
            break
            
    if not nombre_mister_registrado:
        print(f"[{timestamp_log}] INFO: Mensaje ignorado (el usuario '{user.first_name}' no está registrado).")
        return # Detenemos la función aquí.

    # --- 2. FILTRADO DE CONTENIDO ---
    # Solo si el usuario está registrado, nos molestamos en analizar su mensaje.
    texto_normalizado = normalizar_texto(texto_recibido)

    if not any(palabra in texto_normalizado for palabra in PALABRAS_CLAVE_INTERES):
        print(f"[{timestamp_log}] INFO: Mensaje de '{nombre_mister_registrado}' ignorado (no relevante).")
        return

    if len(texto_recibido) < MIN_MESSAGE_LENGTH:
        print(f"[{timestamp_log}] INFO: Mensaje de '{nombre_mister_registrado}' ignorado (demasiado corto).")
        return


    # --- 3. GUARDADO EN JSON ---
    # Si hemos llegado hasta aquí, el mensaje es válido y el usuario está verificado.
    print(f"[{timestamp_log}] ✅ GUARDANDO declaración de '{nombre_mister_registrado}': '{texto_recibido}'")

    # La parte clave es la creación del diccionario que se va a guardar
    message = update.message

    nueva_declaracion = {
    "message_id": message.message_id,
    "reply_to_message_id": message.reply_to_message.message_id if message.reply_to_message else None,
    
    "telegram_user_id": message.from_user.id,
    # V ↓↓↓ ESTA ES LA LÍNEA A CORREGIR ↓↓↓ V
    "nombre_mister": nombre_mister_registrado, 
    # ^ ↑↑↑ ESTA ES LA LÍNEA A CORREGIR ↑↑↑ ^
    "declaracion": message.text,
    "timestamp": datetime.now().isoformat()
}
    
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
    
    # 2. Añadimos el manejador para los BOTONES
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # 3. Añadimos UN ÚNICO manejador para los MENSAJES DE TEXTO
    #    Este debe ser el último manejador de mensajes que añadas.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_declaracion))
    
    # Inicia el bot
    print("Bot del Cronista iniciado. ¡Listo para la acción!")
    application.run_polling()

if __name__ == "__main__":
    main()
