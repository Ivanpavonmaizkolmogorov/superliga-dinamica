import os
import subprocess
import sys
import yaml

# La ruta a nuestro fichero de configuración
FILE_PATH = "comentaristas.yml"

# Contenido por defecto por si el archivo no existiera
DEFAULT_CONTENT = {
    "comentaristas": {
        "guti_haz": {
            "nombre_display": "Guti H.",
            "prompt_base": "Actúa como Guti...",
            "roles_asignados": {"premio": 20, "lider_cronica": 5}
        },
        "joaquin_pisha": {
            "nombre_display": "Joaquín 'El Pisha'",
            "prompt_base": "Actúa como Joaquín...",
            "roles_asignados": {"ultimo_lugar": 30}
        }
    }
}

def open_file_in_editor(filepath):
    """Abre un archivo en el editor de texto por defecto del sistema operativo."""
    print(f"INFO: Intentando abrir '{filepath}' en el editor por defecto...")
    try:
        if sys.platform.startswith('win'):
            os.startfile(filepath)
        elif sys.platform.startswith('darwin'):
            subprocess.run(['open', filepath])
        else:
            subprocess.run(['xdg-open', filepath])
        print("INFO: ¡Comando de apertura enviado! Revisa tu editor de texto.")
    except Exception as e:
        print(f"ERROR: No se pudo abrir el archivo automáticamente. Error: {e}")
        print(f"       Por favor, abre '{filepath}' manualmente en tu editor.")

def main():
    """Punto de entrada del script."""
    print("--- GESTOR DE CRONISTAS ---")
    
    # Si el archivo no existe, lo creamos con un contenido base
    if not os.path.exists(FILE_PATH):
        print(f"ADVERTENCIA: No se encontró '{FILE_PATH}'. Creando uno nuevo con valores por defecto.")
        try:
            with open(FILE_PATH, 'w', encoding='utf-8') as f:
                yaml.dump(DEFAULT_CONTENT, f, allow_unicode=True, sort_keys=False, indent=2)
            print("INFO: Archivo creado con éxito.")
        except Exception as e:
            print(f"ERROR: No se pudo crear el archivo de configuración. Error: {e}")
            return
            
    # Abrimos el archivo para que el usuario lo edite
    open_file_in_editor(FILE_PATH)
    
    print("\n--- INSTRUCCIONES ---")
    print("1. Edita el archivo 'comentaristas.yml' que se ha abierto.")
    print("2. Puedes añadir nuevos comentaristas, cambiar sus frases (prompt_base) o ajustar sus roles.")
    print("3. Guarda los cambios en tu editor de texto y ciérralo.")
    print("4. ¡Listo! La próxima vez que generes un reporte, usará la nueva configuración.")

if __name__ == "__main__":
    main()