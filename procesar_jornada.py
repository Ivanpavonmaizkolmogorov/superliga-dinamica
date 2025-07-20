# procesar_jornada.py (Versión con GUI de Advertencia)

import tkinter as tk
from gestor_datos import cargar_perfiles, guardar_perfiles, cargar_parejas
from scraper import extraer_datos_mister
from cronista import generar_cronica
from gui_advertencia import confirmar_sin_parejas_gui # Importamos nuestra nueva función
import os

def main():
    """
    Función principal para la sincronización de una jornada.
    Ahora usa una GUI para advertir si no hay parejas.
    """
    print("\n" + "="*50)
    print("--- INICIANDO PROCESO DE SINCRONIZACIÓN DE JORNADA ---")
    print("="*50)

    try:
        print("Cargando datos locales (perfiles, parejas)...")
        perfiles = cargar_perfiles()
        parejas = cargar_parejas()
        
        if not perfiles:
            print("ERROR: No se encontró 'perfiles.json'. Ejecuta 'Crear / Actualizar Perfiles' primero.")
            return

        # --- ¡NUEVA COMPROBACIÓN DE SEGURIDAD CON GUI! ---
        if not parejas:
            # Creamos una ventana raíz invisible para la ventana emergente
            root_temp = tk.Tk()
            root_temp.withdraw()
            
            # Llamamos a nuestra función GUI para obtener la confirmación
            if not confirmar_sin_parejas_gui(root_temp):
                # Si el usuario pulsa "No", cancelamos el proceso
                root_temp.destroy()
                print("\nProceso cancelado por el usuario.")
                return
            
            # Si continúa, destruimos la ventana temporal
            root_temp.destroy()
            print("\nContinuando sin datos de parejas...")
        # --- FIN DE LA COMPROBACIÓN ---

        print("Contactando con Mister para obtener el estado actual de la liga...")
        resultado_scraper = extraer_datos_mister()
        
        # ... (El resto del código a partir de aquí es idéntico al que ya funcionaba) ...
        
        if not resultado_scraper or 'datos_managers' not in resultado_scraper:
            print("ERROR: El scraping ha fallado o no ha devuelto datos válidos."); return
        
        datos_web = resultado_scraper.get('datos_managers', [])
        jornada_web_num = resultado_scraper.get('numero_jornada', 0)

        if not datos_web:
            print("INFO: La liga no tiene mánagers en la web."); return
        
        print(f"-> La web informa sobre la Jornada {jornada_web_num}. Sincronizando datos...")
        datos_web.sort(key=lambda x: x['puntos_totales'], reverse=True)
        
        hay_cambios_reales = False
        reporte_individual_whatsapp = f"🏆 ✨ **CRÓNICA DE LA JORNADA {jornada_web_num}** ✨ 🏆\n\n"
        
        for i, datos_manager_web in enumerate(datos_web):
            puesto_actual, manager_id_web = i + 1, datos_manager_web['id_manager']
            perfil_encontrado = next((p for p in perfiles if p['id_manager'] == manager_id_web), None)
            if not perfil_encontrado:
                print(f"AVISO: Mánager '{datos_manager_web['nombre_mister']}' ignorado..."); continue

            registro_web = {"jornada": jornada_web_num, "puntos_jornada": datos_manager_web['puntos_jornada'], "puesto": puesto_actual, "puntos_totales": datos_manager_web['puntos_totales']}
            historial_local = next((h for h in perfil_encontrado['historial_temporada'] if h['jornada'] == jornada_web_num), None)
            
            if historial_local:
                if historial_local != registro_web:
                    print(f"   - Actualizando J.{jornada_web_num} para {perfil_encontrado['nombre_mister']}...")
                    historial_local.update(registro_web); hay_cambios_reales = True
            else:
                print(f"   - Añadiendo nueva J.{jornada_web_num} para {perfil_encontrado['nombre_mister']}...")
                perfil_encontrado['historial_temporada'].append(registro_web); perfil_encontrado['historial_temporada'].sort(key=lambda x: x['jornada']); hay_cambios_reales = True

            print(f"     -> Generando crónica..."); cronica = generar_cronica(perfil_encontrado, registro_web)
            
            titulo_especial = " ❄️ ¡CAMPEÓN DE INVIERNO! ❄️" if jornada_web_num == 19 and puesto_actual == 1 else ""
            reporte_individual_whatsapp += (f"**{puesto_actual}. {perfil_encontrado['nombre_mister']} ({registro_web['puntos_totales']} pts)**{titulo_especial}\n"
                                            f"*(Jornada: {registro_web['puntos_jornada']} pts)*\n"
                                            f"_{cronica}_\n\n")

        if hay_cambios_reales:
            guardar_perfiles(perfiles); print("-> ¡Cambios detectados! 'perfiles.json' ha sido actualizado.")
        else:
            print("-> No se han detectado cambios en los datos. Todo estaba ya sincronizado.")
        
        reporte_final_completo = reporte_individual_whatsapp
        
        print("\n" + "="*50); print("REPORTE PARA WHATSAPP LISTO"); print("="*50)
        print(reporte_final_completo)

    except Exception as e:
        print(f"\nERROR INESPERADO en el proceso de jornada: {e}")
    finally:
        print("\n--- PROCESO DE SINCRONIZACIÓN DE JORNADA FINALIZADO ---")

if __name__ == "__main__":
    main()