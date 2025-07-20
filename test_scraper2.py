# test_scraper2.py (Para probar la creación de perfiles con el scraper unificado)

from scraper import extraer_datos_mister # <-- Importamos la función que SÍ existe
from gestor_datos import guardar_perfiles

print("--- TESTEANDO: Creación de Perfiles con el Scraper Unificado ---")

# 1. Llamamos al scraper para obtener TODOS los datos
resultado_scraper = extraer_datos_mister()

# 2. Comprobamos si el scraper funcionó y trajo datos
if resultado_scraper and resultado_scraper['datos_managers']:
    datos_web = resultado_scraper['datos_managers']
    
    print(f"\n--- ¡ÉXITO! Scraper ha devuelto {len(datos_web)} mánagers. ---")
    
    # 3. Simulamos la lógica de "Crear Perfiles": solo nos interesan los datos básicos
    print("Simulando la creación/actualización de perfiles...")
    perfiles = []
    for manager_data in datos_web:
        print(f"  - Procesando: {manager_data['nombre_mister']}")
        perfiles.append({
            "id_manager": manager_data['id_manager'], 
            "nombre_mister": manager_data['nombre_mister'],
            "apodo_lema": "El Novato", 
            # IGNORAMOS los puntos de jornada para la creación de perfiles
            "historial_temporada": [] 
        })
    
    guardar_perfiles(perfiles)
    print("\n¡ÉXITO! El archivo 'perfiles.json' de prueba ha sido creado/actualizado.")

else:
    print("\n--- ¡FALLO! El scraper no devolvió datos de mánagers. ---")
    print("Revisa la salida de la consola en busca de errores.")

print("\n--- TEST FINALIZADO ---")