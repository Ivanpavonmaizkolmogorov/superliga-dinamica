# crear_perfiles.py (Versión con actualización de nombres)

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
        # Usaremos un único indicador para saber si hubo cambios y hay que guardar
        hubo_cambios = False
        
        for dw in datos_web:
            # CASO 1: El mánager es nuevo
            if dw['id_manager'] not in manager_ids_existentes:
                hubo_cambios = True
                print(f"  - Nuevo mánager: '{dw['nombre_mister']}'. Creando perfil...")
                perfiles.append({
                    "id_manager": dw['id_manager'], 
                    "nombre_mister": dw['nombre_mister'], 
                    "apodo_lema": "El Novato", 
                    "historial_temporada": []
                })
            # --- NUEVA LÓGICA AÑADIDA ---
            # CASO 2: El mánager ya existe, comprobamos si ha cambiado el nombre
            else:
                # Buscamos su perfil actual en nuestra lista
                for perfil in perfiles:
                    if perfil['id_manager'] == dw['id_manager']:
                        # Si el nombre de la web es diferente al que tenemos guardado...
                        if perfil['nombre_mister'] != dw['nombre_mister']:
                            nombre_antiguo = perfil['nombre_mister']
                            nombre_nuevo = dw['nombre_mister']
                            print(f"  - Actualizando nombre: '{nombre_antiguo}' -> '{nombre_nuevo}'")
                            # ...lo actualizamos.
                            perfil['nombre_mister'] = nombre_nuevo
                            hubo_cambios = True
                        # Una vez encontrado, rompemos el bucle para mayor eficiencia
                        break 
        
        # Si hubo algún cambio (o nuevos mánagers o nombres actualizados), guardamos.
        if hubo_cambios:
            guardar_perfiles(perfiles)
            print("-> ¡Perfiles guardados y actualizados!")
        else:
            print("-> Los perfiles ya están al día. No se detectaron cambios.")
            
        print("\n¡SINCRONIZACIÓN COMPLETADA!")
    except Exception as e:
        print(f"ERROR INESPERADO: {e}")
    finally:
        print("\n--- PROCESO DE CREACIÓN DE PERFILES FINALIZADO ---")

if __name__ == "__main__":
    main()