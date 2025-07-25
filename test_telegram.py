import os
import telegram
import asyncio
from dotenv import load_dotenv

# Carga las variables desde tu archivo .env
load_dotenv()

# Lee el token y el chat_id
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_GROUP_ID")

async def test_telegram():
    print("--- INICIANDO TEST DE CONEXIÓN A TELEGRAM ---")
    
    # Imprimimos los valores para verificarlos (solo los últimos 6 del token por seguridad)
    print(f"Usando TOKEN que termina en: ...{TOKEN[-6:] if TOKEN else 'N/A'}")
    print(f"Usando CHAT_ID: {CHAT_ID}")

    if not TOKEN or not CHAT_ID:
        print("\nError Crítico: No se encontraron TELEGRAM_TOKEN o TELEGRAM_GROUP_ID en el archivo .env")
        return

    try:
        bot = telegram.Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text="¡Hola! Esta es una prueba de conexión desde el script de diagnóstico.")
        print("\n✅ ¡ÉXITO! El mensaje de prueba se ha enviado correctamente a tu grupo.")
    except Exception as e:
        print(f"\n❌ ERROR: No se pudo enviar el mensaje. Razón: {e}")
        print("\n--- POSIBLES CAUSAS DEL ERROR ---")
        print("1. Revisa el archivo .env: ¿Es el TOKEN el que corresponde a 'Cronista de Pruebas'?")
        print("2. Revisa el archivo .env: ¿Es el CHAT_ID correcto? (¡No olvides el guion '-' al principio!).")
        print("3. Vuelve a comprobar en Telegram que el bot 'Cronista de Pruebas' sigue siendo administrador en el grupo.")

if __name__ == "__main__":
    # Esta línea es necesaria en Windows para evitar un error con asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_telegram())