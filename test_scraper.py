# test_scraper.py

# Importamos solo lo absolutamente necesario
from scraper import extraer_datos_mister
from gestor_datos import cargar_perfiles, guardar_perfiles

print("--- INICIANDO TEST DE SCRAPER AISLADO ---")

# Llamamos a la función que abre el navegador
datos_web = extraer_datos_mister()

if datos_web:
    print("\n--- ¡ÉXITO! EL SCRAPER HA DEVUELTO DATOS ---")
    print(f"Se han encontrado {len(datos_web)} mánagers.")
    print("Datos recibidos:")
    # Imprimimos los datos para confirmar que son correctos
    for manager in datos_web:
        print(f"  - ID: {manager['id_manager']}, Nombre: {manager['nombre_mister']}, Puntos Totales: {manager['puntos_totales']}")
    
    # Como bonus, vamos a simular la creación de perfiles aquí mismo
    print("\n--- SIMULANDO CREACIÓN DE PERFILES ---")
    perfiles = []
    for datos_manager_web in datos_web:
        perfiles.append({
            "id_manager": datos_manager_web['id_manager'], 
            "nombre_mister": datos_manager_web['nombre_mister'],
            "apodo_lema": "El Novato", 
            # ... etc
            "historial_temporada": []
        })
    
    guardar_perfiles(perfiles)
    print("¡ÉXITO! El archivo 'perfiles.json' ha sido creado correctamente.")

else:
    print("\n--- ¡FALLO! EL SCRAPER NO HA DEVUELTO DATOS ---")
    print("Revisa la salida de la consola en busca de errores de Playwright.")

print("\n--- TEST DE SCRAPER FINALIZADO ---")