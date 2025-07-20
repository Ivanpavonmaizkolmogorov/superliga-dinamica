# procesar_jornada.py (Versión sin pausa final)

from gestor_datos import cargar_perfiles, guardar_perfiles, cargar_parejas
from scraper import extraer_datos_mister
from cronista import generar_cronica
import os

def main():
    print("\n" + "="*50)
    print("--- INICIANDO PROCESO DE SINCRONIZACIÓN DE JORNADA ---")
    print("="*50)
    try:
        # (Aquí va toda la lógica completa de procesar la jornada que ya teníamos)
        print("Cargando datos locales...")
        perfiles = cargar_perfiles()
        if not perfiles:
            print("ERROR: No se encontró 'perfiles.json'."); return
        
        print("Contactando con Mister...")
        resultado_scraper = extraer_datos_mister()
        if not resultado_scraper:
            print("ERROR: El scraping ha fallado."); return

        # ... resto de la lógica ...
        
        print("\n" + "="*50)
        print("REPORTE PARA WHATSAPP LISTO")
        print("="*50)
        # print(reporte_final_completo)

    except Exception as e:
        print(f"\nERROR INESPERADO en el proceso de jornada: {e}")
    finally:
        print("\n--- PROCESO DE SINCRONIZACIÓN DE JORNADA FINALIZADO ---")
        # LA LÍNEA DEL input() HA SIDO ELIMINADA

if __name__ == "__main__":
    main()