# reiniciar_temporada.py (Versión con GUI de Confirmación)

import os
import tkinter as tk # Necesitamos tkinter para la ventana raíz
from gestor_datos import cargar_perfiles, guardar_perfiles
from gui_reset import confirmar_reinicio_gui # Importamos nuestra nueva función

def main():
    """
    Función principal para reiniciar la temporada, ahora usando una GUI para confirmar.
    """
    print("\n" + "="*50)
    print("--- ASISTENTE DE REINICIO DE TEMPORADA ---")
    print("="*50)

    # Creamos una ventana raíz invisible para que las ventanas emergentes funcionen
    root_temp = tk.Tk()
    root_temp.withdraw()

    # --- ¡CAMBIO CLAVE! ---
    # Llamamos a nuestra función GUI para obtener la confirmación
    if confirmar_reinicio_gui(root_temp):
        # El usuario ha pulsado "Sí"
        print("\nConfirmación recibida. Procediendo con el reinicio...")
        try:
            # Borrar parejas.json
            if os.path.exists('parejas.json'):
                os.remove('parejas.json')
                print("-> Archivo 'parejas.json' borrado con éxito.")
            else:
                print("-> No se encontró 'parejas.json' (no hay nada que borrar).")

            # Limpiar historial de perfiles.json
            perfiles = cargar_perfiles()
            if perfiles:
                for p in perfiles:
                    p['historial_temporada'] = []
                guardar_perfiles(perfiles)
                print("-> Historial de temporada de todos los perfiles borrado con éxito.")
            else:
                print("-> No se encontró 'perfiles.json' o está vacío.")
            
            print("\n¡TEMPORADA REINICIADA CON ÉXITO!")

        except Exception as e:
            print(f"\nHa ocurrido un error inesperado durante el reinicio: {e}")
    else:
        # El usuario ha pulsado "No" o ha cerrado la ventana
        print("\nCANCELADO. No se ha realizado ningún cambio.")

    # Destruimos la ventana temporal, ya no la necesitamos
    root_temp.destroy()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
    finally:
        print("\n--- PROCESO DE REINICIO FINALIZADO ---")
        # Ya no necesitamos el input()