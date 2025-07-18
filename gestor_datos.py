# gestor_datos.py
import json
from config import PERFILES_JSON_PATH, PAREJAS_JSON_PATH

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

# --- ESTA ES LA FUNCIÓN QUE FALTABA ---
def cargar_parejas():
    """
    Abre y carga las parejas desde 'parejas.json'.
    Si el archivo no existe o está vacío, devuelve una lista vacía.
    """
    try:
        with open(PAREJAS_JSON_PATH, 'r', encoding='utf-8') as f:
            contenido = f.read()
            if not contenido:
                # Si el archivo está vacío, no es un error, simplemente no hay parejas.
                return []
            return json.loads(contenido)
    except FileNotFoundError:
        print(f"ADVERTENCIA: No se encontró '{PAREJAS_JSON_PATH}'. La clasificación por parejas no se generará.")
        return []
    except json.JSONDecodeError:
        print(f"ERROR: '{PAREJAS_JSON_PATH}' está corrupto. La clasificación por parejas no se generará.")
        return []
