# simulador.py (Versión con GUI)

import random
import tkinter as tk # Necesitamos tkinter para crear una ventana raíz oculta
from gestor_datos import cargar_perfiles, guardar_perfiles
from gui_simulador import pedir_jornada_gui # Importamos nuestra nueva función

def generar_datos_falsos(num_jornada_final, managers):
    # ... (Esta función no cambia en absoluto) ...
    print(f"\nGenerando historial falso hasta la jornada {num_jornada_final}...")
    for manager in managers:
        manager['historial_temporada'] = []
        puntos_totales_acumulados = 0
        for j in range(1, num_jornada_final + 1):
            puntos_jornada_actual = random.randint(25, 85)
            puntos_totales_acumulados += puntos_jornada_actual
            manager['historial_temporada'].append({
                "jornada": j, "puntos_jornada": puntos_jornada_actual,
                "puesto": 0, "puntos_totales": puntos_totales_acumulados
            })
    managers.sort(key=lambda m: m['historial_temporada'][-1]['puntos_totales'], reverse=True)
    for i, manager in enumerate(managers):
        manager['historial_temporada'][-1]['puesto'] = i + 1
    print("¡Historial falso generado con éxito!")
    return managers

def main():
    """Función principal del simulador, ahora usando una GUI."""
    print("\n" + "="*50)
    print("--- SIMULADOR DE TEMPORADA DE LA SUPERLIGA ---")
    print("="*50)

    # --- ¡CAMBIO CLAVE! ---
    # Creamos una ventana raíz invisible para que las ventanas emergentes funcionen
    root_temp = tk.Tk()
    root_temp.withdraw()

    # Llamamos a nuestra función GUI para preguntar la jornada
    jornada_a_simular = pedir_jornada_gui(root_temp)
    
    # Destruimos la ventana temporal, ya no la necesitamos
    root_temp.destroy()
    
    # Si el usuario canceló, la función devuelve None y salimos
    if jornada_a_simular is None:
        print("Simulación cancelada por el usuario.")
        return

    print(f"-> Viajando a la jornada: {jornada_a_simular}")
    
    perfiles_actuales = cargar_perfiles()
    if not perfiles_actuales:
        print("Error: 'perfiles.json' está vacío. Ejecuta 'Crear / Actualizar Perfiles' primero.")
        return
        
    perfiles_modificados = generar_datos_falsos(jornada_a_simular, perfiles_actuales)
    guardar_perfiles(perfiles_modificados)

    print("\n¡SIMULACIÓN COMPLETADA!")
    print(f"-> Tu archivo 'perfiles.json' ahora refleja el estado de la liga en la JORNADA {jornada_a_simular}.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
    finally:
        print("\n--- PROCESO DE SIMULACIÓN FINALIZADO ---")
        # Ya no necesitamos el input() porque la interacción fue en la GUI