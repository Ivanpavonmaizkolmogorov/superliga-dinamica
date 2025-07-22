# telegram_sender.py

import os
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Cargamos las variables de entorno para obtener el token y el ID del chat
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_GROUP_ID") # Usaremos una nueva variable de entorno

# En telegram_sender.py

async def send_telegram_message(message_text):
    """
    Envía un mensaje de texto a Telegram, saneando caracteres problemáticos
    para el formato Markdown.
    """
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("ERROR en telegram_sender: Faltan TELEGRAM_TOKEN o TELEGRAM_GROUP_ID en .env")
        return False

    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        
        # --- INICIO DE LA MODIFICACIÓN: SANEAR EL TEXTO ---
        # Reemplazamos los caracteres que más problemas dan en Markdown V1 de Telegram.
        # Un guion bajo suelto es el culpable más común. Lo reemplazamos por un espacio.
        # Hacemos esto para evitar que nombres como "raul_piru_" rompan el formato.
        texto_saneado = message_text.replace('_', ' ')
        # --- FIN DE LA MODIFICACIÓN ---

        max_len = 4096
        if len(texto_saneado) <= max_len:
            await bot.send_message(chat_id=CHAT_ID, text=texto_saneado, parse_mode=ParseMode.MARKDOWN)
        else:
            print("INFO: El mensaje es muy largo, se enviará en varias partes.")
            parts = [texto_saneado[i:i+max_len] for i in range(0, len(texto_saneado), max_len)]
            for part in parts:
                await bot.send_message(chat_id=CHAT_ID, text=part, parse_mode=ParseMode.MARKDOWN)
                await asyncio.sleep(1)

        print("-> Mensaje enviado a Telegram con éxito.")
        return True
    except Exception as e:
        print(f"ERROR en telegram_sender: No se pudo enviar el mensaje. {e}")
        return False

# Esta parte permite probar el script directamente
if __name__ == '__main__':
    # Para probar, ejecuta: python telegram_sender.py
    test_message = "Esta es una *prueba* de envío desde el script `telegram_sender.py`."
    print("Iniciando prueba de envío...")
    asyncio.run(send_telegram_message(test_message))