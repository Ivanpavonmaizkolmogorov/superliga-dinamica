# procesar_jornada.py (Versión FINAL y compatible con scraper multi-jornada)

import tkinter as tk
from gestor_datos import cargar_perfiles, guardar_perfiles, cargar_parejas, cargar_declaraciones
from scraper import extraer_datos_mister
from cronista import generar_todas_las_cronicas, generar_introduccion_semanal, elegir_comentarista
from gui_advertencia import confirmar_sin_parejas_gui

def main():
    """
    Función principal reestructurada para ser más eficiente y compatible con la nueva lógica del cronista y el scraper multi-jornada.
    """
    print("\n" + "="*50)
    print("--- INICIANDO PROCESO DE SINCRONIZACIÓN DE JORNADA ---")
    print("="*50)

    try:
        # --- CARGA INICIAL DE DATOS ---
        print("Cargando datos locales (perfiles, parejas, declaraciones)...")
        perfiles = cargar_perfiles()
        parejas = cargar_parejas()
        declaraciones = cargar_declaraciones()
        
        if not perfiles:
            print("ERROR: No se encontró 'perfiles.json'. Ejecuta 'Crear / Actualizar Perfiles' primero.")
            return

        # ... (GUI de advertencia de parejas se queda igual) ...
        if not parejas:
            root_temp = tk.Tk()
            root_temp.withdraw()
            if not confirmar_sin_parejas_gui(root_temp):
                root_temp.destroy()
                print("\nProceso cancelado por el usuario.")
                return
            root_temp.destroy()
            print("\nContinuando sin datos de parejas...")
        
        # --- EXTRACCIÓN DE DATOS DE LA WEB ---
        print("Contactando con Mister para obtener el estado actual de la liga...")
        resultado_scraper = extraer_datos_mister()
        
        if not resultado_scraper or 'datos_managers' not in resultado_scraper:
            print("ERROR: El scraping ha fallado o no ha devuelto datos válidos."); return
        
        datos_web = resultado_scraper.get('datos_managers', [])

        if not datos_web:
            print("INFO: La liga no tiene mánagers en la web."); return
        
        # <--- CAMBIO 1: Calculamos la última jornada a partir de los datos recibidos
        # Esto reemplaza a `jornada_web_num = resultado_scraper.get('numero_jornada', 0)`
        ultima_jornada_web = max([h['jornada'] for m in datos_web for h in m.get('historial_web', [])] or [0])
        
        print(f"-> La última jornada detectada en la web es la {ultima_jornada_web}. Sincronizando datos...")
        datos_web.sort(key=lambda x: x['puntos_totales'], reverse=True)
        
        # =================================================================
        # FASE 1: SINCRONIZACIÓN DE PUNTOS Y PUESTOS (LÓGICA COMPLETAMENTE NUEVA)
        # =================================================================
        hay_cambios_reales = False
        
        for i, datos_manager_web in enumerate(datos_web):
            puesto_actual = i + 1
            manager_id_web = datos_manager_web['id_manager']
            perfil_local = next((p for p in perfiles if p['id_manager'] == manager_id_web), None)
            
            if not perfil_local:
                continue

            # Iteramos sobre CADA jornada que nos ha devuelto el scraper para este mánager
            for registro_jornada_web in datos_manager_web.get('historial_web', []):
                jornada_num = registro_jornada_web['jornada']
                
                # Creamos el registro completo con los datos de esa jornada y los totales/puesto actuales
                registro_web_completo = {
                    "jornada": jornada_num,
                    "puntos_jornada": registro_jornada_web['puntos_jornada'],
                    "puesto": puesto_actual,
                    "puntos_totales": datos_manager_web['puntos_totales']
                }

                historial_local = next((h for h in perfil_local['historial_temporada'] if h['jornada'] == jornada_num), None)

                if not historial_local:
                    print(f"    - Añadiendo NUEVA J.{jornada_num} para {perfil_local['nombre_mister']}...")
                    perfil_local['historial_temporada'].append(registro_web_completo)
                    hay_cambios_reales = True
                elif historial_local != registro_web_completo:
                    print(f"    - Actualizando datos en J.{jornada_num} para {perfil_local['nombre_mister']}...")
                    historial_local.update(registro_web_completo)
                    hay_cambios_reales = True
            
            # Ordenamos el historial del perfil local una sola vez si ha habido cambios
            if any(registro_jornada_web for registro_jornada_web in datos_manager_web.get('historial_web', [])):
                 perfil_local['historial_temporada'].sort(key=lambda x: x['jornada'])

        # Guardamos los perfiles actualizados ANTES de generar el reporte
        if hay_cambios_reales:
            guardar_perfiles(perfiles)
            print("-> ¡Cambios detectados! 'perfiles.json' ha sido actualizado.")
        else:
            print("-> No se han detectado cambios. Todo estaba ya sincronizado.")
        
        # =================================================================
        # FASE 2: GENERACIÓN DEL REPORTE COMPLETO
        # =================================================================
        print("\nPreparando para generar el reporte de la jornada...")

        # 1. Generamos la introducción
        print(" -> Generando introducción...")
        # <--- CAMBIO 2: Usamos la variable `ultima_jornada_web`
        texto_intro, ids_usados = generar_introduccion_semanal(perfiles, declaraciones, ultima_jornada_web)
        
        # 2. Elegimos un comentarista
        print(" -> Eligiendo comentarista...")
        comentarista_elegido = elegir_comentarista('analisis')

        # 4. Generamos todas las crónicas de golpe
        print(" -> Generando TODAS las crónicas con la IA...")
        todas_las_cronicas = generar_todas_las_cronicas(
            perfiles=perfiles,
            todas_declaraciones=declaraciones,
            ids_ya_usadas=ids_usados,
            comentarista=comentarista_elegido
        )
        print(" -> ¡Crónicas generadas con éxito!")

        # 5. Construimos el texto final del reporte para WhatsApp
        # <--- CAMBIO 3: Usamos `ultima_jornada_web` en el título
        reporte_final_whatsapp = f"🏆 ✨ **CRÓNICA DE LA JORNADA {ultima_jornada_web}** ✨ 🏆\n\n{texto_intro}"
        
        for i, datos_manager_web in enumerate(datos_web):
            puesto_actual = i + 1
            manager_id_web = datos_manager_web['id_manager']
            perfil_encontrado = next((p for p in perfiles if p['id_manager'] == manager_id_web), None)
            
            if not perfil_encontrado:
                continue

            cronica_manager = todas_las_cronicas.get(manager_id_web, "_El cronista no hizo comentarios sobre este mánager._")
            
            # <--- CAMBIO 4: Usamos `ultima_jornada_web` para el título de invierno
            titulo_especial = " ❄️ ¡CAMPEÓN DE INVIERNO! ❄️" if ultima_jornada_web == 19 and puesto_actual == 1 else ""
            
            # <--- CAMBIO 5: Lógica para obtener los puntos de la última jornada (LA CORRECCIÓN DEL KEYERROR)
            # Buscamos en el historial local (que ya está actualizado) los datos de la última jornada.
            datos_jornada_actual = next((h for h in perfil_encontrado['historial_temporada'] if h['jornada'] == ultima_jornada_web), None)
            puntos_de_la_jornada = datos_jornada_actual['puntos_jornada'] if datos_jornada_actual else 'N/A'

            reporte_final_whatsapp += (f"**{puesto_actual}. {perfil_encontrado['nombre_mister']} ({datos_manager_web['puntos_totales']} pts)**{titulo_especial}\n"
                                     f"*(Jornada: {puntos_de_la_jornada} pts)*\n" # <-- Usamos la variable segura
                                     f"_{cronica_manager}_\n\n")

        print("\n" + "="*50); print("REPORTE PARA WHATSAPP LISTO"); print("="*50)
        print(reporte_final_whatsapp)

    except Exception as e:
        print(f"\nERROR INESPERADO en el proceso de jornada: {e}")
    finally:
        print("\n--- PROCESO DE SINCRONIZACIÓN DE JORNADA FINALIZADO ---")

if __name__ == "__main__":
    main()