# config.py (Versión Final y Correcta con Perfil Dedicado)

import os
from dotenv import load_dotenv

# Carga las variables del archivo .env que tienes en tu proyecto
load_dotenv()


# --- RUTAS Y URLS ---

# La URL de tu liga de Mister, la coge del archivo .env
MISTER_URL = os.getenv("MISTER_URL_LIGA")

# --- ¡ESTA ES LA LÍNEA CLAVE Y CORRECTA! ---
# Define una ruta para una nueva carpeta de perfil DENTRO de tu proyecto.
# Esto evita conflictos con tu perfil de usuario de Windows y hace el proyecto autónomo.
PLAYWRIGHT_PROFILE_PATH = os.path.join(os.getcwd(), 'playwright_edge_profile')

# Los nombres de tus archivos "base de datos"
PERFILES_JSON_PATH = 'perfiles.json'
PAREJAS_JSON_PATH = 'parejas.json'
LIGA_CONFIG_JSON_PATH = 'liga_config.json'


# --- CLAVES DE API ---

# La clave para usar la IA de Gemini, la coge del archivo .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")