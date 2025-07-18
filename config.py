# config.py
import os
import getpass
from dotenv import load_dotenv

# Carga las variables del archivo .env que tienes en tu proyecto
load_dotenv()

# --- Definición de Rutas y URLs ---
# La URL de tu liga de Mister, la coge del archivo .env
MISTER_URL = os.getenv("MISTER_URL_LIGA")

# La ruta donde Edge guarda tus datos de sesión para no tener que loguearte
USER_DATA_DIR = f"C:\\Users\\{getpass.getuser()}\\AppData\\Local\\Microsoft\\Edge\\User Data"

# Los nombres de tus archivos "base de datos"
PERFILES_JSON_PATH = 'perfiles.json'
PAREJAS_JSON_PATH = 'parejas.json'

# --- Definición de Claves de API ---
# La clave para usar la IA de Gemini, la coge del archivo .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")