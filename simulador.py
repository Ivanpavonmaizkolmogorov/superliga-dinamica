# simulador.py

import random
from gestor_datos import cargar_perfiles, guardar_perfiles

def generar_datos_falsos(num_jornada_final, managers):
    """
    Modifica los perfiles de los mánagers para simular que la temporada
    ha avanzado hasta una jornada específica, generando un historial falso.
    """
    print(f"\nGenerando historial falso hasta la jornada {num_jornada_final}...")

    for manager in managers:
        # Limpiamos cualquier historial previo para empezar de cero
        manager['historial_temporada'] = []
        puntos_totales_acumulados = 0
        
        for j in range(1, num_jornada_final + 1):
            # Generamos puntos aleatorios pero realistas
            puntos_jornada_actual = random.randint(25, 85)
            puntos_totales_acumulados += puntos_jornada_actual
            
            manager['historial_temporada'].append({
                "jornada": j,
                "puntos_jornada": puntos_jornada_actual,
                "puesto": 0, # Se recalculará después
                "puntos_totales": puntos_totales_acumulados
            })

    # Recalculamos los puestos para la última jornada simulada
    managers.sort(key=lambda m: m['historial_temporada'][-1]['puntos_totales'], reverse=True)
    
    for i, manager in enumerate(managers):
        manager['historial_temporada'][-1]['puesto'] = i + 1

    print("¡Historial falso generado con éxito!")
    return managers

def main():
    """Función principal del simulador."""
    print("\n" + "="*50)
    print("--- SIMULADOR DE TEMPORADA DE LA SUPERLIGA ---")
    print("="*50)

    try:
        jornada_a_simular = int(input("Introduce el número de jornada a la que quieres 'viajar' (1-38): "))
        if not 1 <= jornada_a_simular <= 38:
            print("Error: El número de jornada debe estar entre 1 y 38.")
            return
    except ValueError:
        print("Error: Por favor, introduce un número válido.")
        return

    perfiles_actuales = cargar_perfiles()
    if not perfiles_actuales:
        print("Error: 'perfiles.json' está vacío. Ejecuta 'Crear / Actualizar Perfiles' primero.")
        return
        
    perfiles_modificados = generar_datos_falsos(jornada_a_simular, perfiles_actuales)
    guardar_perfiles(perfiles_modificados)

    print("\n¡SIMULACIÓN COMPLETADA!")
    print(f"-> Tu archivo 'perfiles.json' ahora refleja el estado de la liga en la JORNADA {jornada_a_simular}.")
    print("-> Ahora puedes usar el botón 'Procesar Nueva Jornada' para simular la JORNADA " + str(jornada_a_simular + 1) + ".")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
    finally:
        print("\n--- PROCESO DE SIMULACIÓN FINALIZADO ---")
        input("Pulsa Enter para volver al panel de control...")