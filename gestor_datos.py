# gestor_datos.py (Versión con la nueva función para cargar la configuración de la liga)

import json
# ¡Importante! Añadimos la nueva variable de configuración
from config import PERFILES_JSON_PATH, PAREJAS_JSON_PATH, LIGA_CONFIG_JSON_PATH

def cargar_perfiles():
    """
    Abre y carga los perfiles desde 'perfiles.json'.
    Si el archivo no existe o está vacío, devuelve una lista vacía.
    """
    try:
        with open(PERFILES_JSON_PATH, 'r', encoding='utf-8') as f:
            contenido = f.read()
            if not contenido:
                print(f"ADVERTENCIA: '{PERFILES_JSON_PATH}' está vacío. Se tratará como una lista nueva.")
                return []
            return json.loads(contenido)
    except FileNotFoundError:
        print(f"ADVERTENCIA: El archivo '{PERFILES_JSON_PATH}' no existe. Se creará uno nuevo.")
        return []
    except json.JSONDecodeError:
        print(f"ERROR FATAL: '{PERFILES_JSON_PATH}' está corrupto. No se puede continuar.")
        exit()

def guardar_perfiles(perfiles):
    """Guarda los perfiles actualizados en el archivo JSON."""
    with open(PERFILES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(perfiles, f, indent=2, ensure_ascii=False)
    print(f"INFO: Perfiles guardados correctamente en '{PERFILES_JSON_PATH}'.")

def cargar_parejas():
    """
    Abre y carga las parejas desde 'parejas.json'.
    Si el archivo no existe o está vacío, devuelve una lista vacía.
    """
    try:
        with open(PAREJAS_JSON_PATH, 'r', encoding='utf-8') as f:
            contenido = f.read()
            if not contenido:
                return []
            return json.loads(contenido)
    except FileNotFoundError:
        print(f"ADVERTENCIA: No se encontró '{PAREJAS_JSON_PATH}'.")
        return []
    except json.JSONDecodeError:
        print(f"ERROR: '{PAREJAS_JSON_PATH}' está corrupto.")
        return []

# --- ¡NUEVA FUNCIÓN AÑADIDA! ---
def cargar_config_liga():
    """
    Abre y carga la configuración de la liga desde 'liga_config.json'.
    Si el archivo no existe o está vacío, devuelve un diccionario vacío.
    """
    try:
        with open(LIGA_CONFIG_JSON_PATH, 'r', encoding='utf-8') as f:
            contenido = f.read()
            if not contenido:
                return {} # Devuelve un diccionario vacío si no hay configuración
            return json.loads(contenido)
    except FileNotFoundError:
        print(f"ADVERTENCIA: No se encontró '{LIGA_CONFIG_JSON_PATH}'. Los premios no se calcularán.")
        return {}
    except json.JSONDecodeError:
        print(f"ERROR: '{LIGA_CONFIG_JSON_PATH}' está corrupto.")
        return {}

# Añade esta función a tu archivo gestor_datos.py

def guardar_perfiles(perfiles):
    """
    Guarda la lista completa de perfiles en el archivo perfiles.json.
    """
    try:
        with open('perfiles.json', 'w', encoding='utf-8') as f:
            json.dump(perfiles, f, ensure_ascii=False, indent=4)
        print("INFO: perfiles.json guardado correctamente.")
        return True
    except Exception as e:
        print(f"ERROR: No se pudo guardar perfiles.json. Error: {e}")
        return False