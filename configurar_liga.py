# configurar_liga.py (Versión sin pausa final para el Panel de Control)

import json
from gestor_datos import cargar_perfiles
from gui_config_liga import configurar_liga_gui
from config import LIGA_CONFIG_JSON_PATH

def main():
    print("\n" + "="*50)
    print("--- ASISTENTE DE CONFIGURACIÓN DE LIGA ---")
    print("="*50)

    perfiles = cargar_perfiles()
    if not perfiles:
        print("ERROR: No se puede configurar la liga sin perfiles. Ejecuta 'Crear / Actualizar Perfiles' primero.")
        return

    num_managers = len(perfiles)
    print(f"Detectados {num_managers} mánagers en 'perfiles.json'. Lanzando GUI de configuración...")
    
    # Lanzamos la GUI y esperamos a que devuelva la configuración
    config_final = configurar_liga_gui(num_managers)

    if config_final:
        with open(LIGA_CONFIG_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(config_final, f, indent=2, ensure_ascii=False)
        print(f"\n¡Éxito! La configuración de la liga ha sido guardada en '{LIGA_CONFIG_JSON_PATH}'.")
    else:
        print("\nConfiguración cancelada por el usuario.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
    finally:
        print("\n--- PROCESO DE CONFIGURACIÓN FINALIZADO ---")
        # LA LÍNEA DEL input() HA SIDO ELIMINADA PARA QUE EL PANEL PUEDA CONTINUAR