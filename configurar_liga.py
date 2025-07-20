# configurar_liga.py (Versión que guarda el valor de los premios en euros)

import json
from gestor_datos import cargar_perfiles
from gui_config_liga import configurar_liga_gui
from config import LIGA_CONFIG_JSON_PATH

def main():
    """
    Función principal para lanzar el asistente de configuración de la liga.
    Ahora guarda tanto los porcentajes como el valor calculado de cada premio.
    """
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
    config_desde_gui = configurar_liga_gui(num_managers)

    if config_desde_gui:
        # --- ¡CAMBIO CLAVE! Creamos una nueva estructura para guardar ---
        
        # Calculamos el valor en euros de cada premio
        bote_total = config_desde_gui['bote_total']
        premios_valor = {}
        # Hacemos coincidir los nombres de los premios con los que buscará generar_reporte.py
        sprints_map = {
            "Ganador Sprint 1 (J1-10)": "Ganador Sprint 1",
            "Ganador Sprint 2 (J11-20)": "Ganador Sprint 2",
            "Ganador Sprint 3 (J21-30)": "Ganador Sprint 3",
            "Ganador Sprint 4 (J31-38)": "Ganador Sprint 4",
        }

        for nombre_largo, pct in config_desde_gui['premios_pct'].items():
            nombre_corto = sprints_map.get(nombre_largo, nombre_largo)
            premios_valor[nombre_corto] = round(bote_total * pct, 2)

        # La configuración final que guardaremos en el JSON
        config_final_para_guardar = {
            "cuota": config_desde_gui['cuota'],
            "num_managers": config_desde_gui['num_managers'],
            "bote_total": bote_total,
            "premios_pct": config_desde_gui['premios_pct'],
            "premios_valor": premios_valor # <-- ¡Añadimos el nuevo diccionario!
        }

        with open(LIGA_CONFIG_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(config_final_para_guardar, f, indent=2, ensure_ascii=False)
            
        print(f"\n¡Éxito! La configuración de la liga ha sido guardada en '{LIGA_CONFIG_JSON_PATH}'.")
        print("Se ha guardado el desglose de premios en euros para facilitar los reportes.")
    else:
        print("\nConfiguración cancelada por el usuario.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
    finally:
        print("\n--- PROCESO DE CONFIGURACIÓN FINALIZADO ---")