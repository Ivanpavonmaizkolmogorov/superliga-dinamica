# crear_perfiles.py (Versión sin pausa final)

from gestor_datos import cargar_perfiles, guardar_perfiles
from scraper import extraer_datos_mister

def main():
    print("\n" + "="*50)
    print("--- INICIANDO CREACIÓN / ACTUALIZACIÓN DE PERFILES ---")
    print("="*50)
    try:
        print("Cargando perfiles existentes...")
        perfiles = cargar_perfiles()
        manager_ids_existentes = {p['id_manager'] for p in perfiles}
        
        print("Contactando con Mister...")
        resultado_scraper = extraer_datos_mister()
        
        if not resultado_scraper:
            print("ERROR: El scraping ha fallado o no ha devuelto datos.")
            return

        datos_web = resultado_scraper.get('datos_managers', [])
        if not datos_web:
            print("INFO: La liga no tiene mánagers en la web todavía.")
            return
            
        print(f"-> {len(datos_web)} mánagers encontrados. Sincronizando...")
        nuevos_managers_count, perfiles_actualizados = 0, False
        for dw in datos_web:
            if dw['id_manager'] not in manager_ids_existentes:
                nuevos_managers_count += 1; perfiles_actualizados = True
                print(f"   - Nuevo mánager: '{dw['nombre_mister']}'. Creando perfil...")
                perfiles.append({"id_manager": dw['id_manager'], "nombre_mister": dw['nombre_mister'], "apodo_lema": "El Novato", "historial_temporada": []})
        
        if perfiles_actualizados:
            guardar_perfiles(perfiles)
            print(f"-> ¡Perfiles guardados! Se añadieron {nuevos_managers_count} mánager(s).")
        else:
            print("-> Los perfiles ya están al día.")
            
        print("\n¡SINCRONIZACIÓN COMPLETADA!")
    except Exception as e:
        print(f"ERROR INESPERADO: {e}")
    finally:
        print("\n--- PROCESO DE CREACIÓN DE PERFILES FINALIZADO ---")
        # LA LÍNEA DEL input() HA SIDO ELIMINADA

if __name__ == "__main__":
    main()