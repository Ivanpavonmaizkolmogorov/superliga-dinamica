# formar_parejas.py (Versión Final Sincronizada)

import json
import random
import os
from gestor_datos import cargar_perfiles
from gui_wizard import DraftWizardApp

PAREJAS_JSON_PATH = 'parejas.json'

def asignar_manager_impar(parejas, managers_totales):
    """Encuentra al mánager sobrante y lo asigna a una pareja para formar un trío."""
    ids_emparejados = set()
    for p in parejas:
        ids_emparejados.update(p['id_managers'])
    manager_sobrante = [m for m in managers_totales if m['id_manager'] not in ids_emparejados]
    if not manager_sobrante:
        print("INFO: Todos los mánagers han sido emparejados.")
        return parejas
    if not parejas:
        return parejas
    pareja_elegida = random.choice(parejas)
    pareja_elegida['id_managers'].append(manager_sobrante[0]['id_manager'])
    pareja_elegida['nombre_pareja'] = f"{pareja_elegida['nombre_pareja']} & Co."
    return parejas

def main():
    """
    Función principal que carga perfiles y lanza el asistente gráfico.
    """
    perfiles_completos = cargar_perfiles()
    if not perfiles_completos or len(perfiles_completos) < 2:
        print("ERROR: Se necesitan al menos 2 mánagers en 'perfiles.json' para continuar.")
        return

    # --- LLAMADA CORREGIDA Y SINCRONIZADA ---
    # La clase DraftWizardApp crea su propia ventana, solo necesita los mánagers.
    app = DraftWizardApp(perfiles_completos)
    parejas_formadas = app.run()

    if not parejas_formadas:
        print("INFO: Asistente de Draft cerrado sin formar parejas.")
        return

    parejas_finales = asignar_manager_impar(parejas_formadas, perfiles_completos)

    try:
        with open(PAREJAS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(parejas_finales, f, indent=2, ensure_ascii=False)
        print(f"INFO: Configuración de parejas guardada en '{PAREJAS_JSON_PATH}'.")
    except Exception as e:
        print(f"ERROR: No se pudo guardar el archivo de parejas. Error: {e}")

if __name__ == "__main__":
    main()