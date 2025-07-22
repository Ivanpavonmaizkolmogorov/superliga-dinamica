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

# En telegram_sender.py

# En telegram_sender.py

async def send_telegram_message(message_text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("ERROR en telegram_sender: Faltan variables en .env")
        return False

    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        
        # Simplemente enviamos el texto tal cual lo recibimos
        await bot.send_message(
            chat_id=CHAT_ID, 
            text=message_text, 
            parse_mode=ParseMode.MARKDOWN
        )

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