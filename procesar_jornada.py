# procesar_jornada.py (Versión Corregida y Optimizada)

import tkinter as tk
from gestor_datos import cargar_perfiles, guardar_perfiles, cargar_parejas, cargar_declaraciones # <-- AÑADE cargar_declaraciones
from scraper import extraer_datos_mister
# --- ¡IMPORTANTE! AÑADE ESTAS FUNCIONES DE CRONISTA ---
from cronista import generar_todas_las_cronicas, generar_introduccion_semanal, elegir_comentarista
from gui_advertencia import confirmar_sin_parejas_gui
# Probablemente necesites una función para calcular los eventos, impórtala también
# from logica_eventos import calcular_eventos 

def main():
    """
    Función principal reestructurada para ser más eficiente y compatible con la nueva lógica del cronista.
    """
    print("\n" + "="*50)
    print("--- INICIANDO PROCESO DE SINCRONIZACIÓN DE JORNADA ---")
    print("="*50)

    try:
        # --- CARGA INICIAL DE DATOS ---
        print("Cargando datos locales (perfiles, parejas, declaraciones)...")
        perfiles = cargar_perfiles()
        parejas = cargar_parejas()
        # Necesitamos las declaraciones para generar las crónicas
        declaraciones = cargar_declaraciones() 
        
        if not perfiles:
            print("ERROR: No se encontró 'perfiles.json'. Ejecuta 'Crear / Actualizar Perfiles' primero.")
            return

        # ... (Tu código para la GUI de advertencia de parejas se queda igual) ...
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
        jornada_web_num = resultado_scraper.get('numero_jornada', 0)

        if not datos_web:
            print("INFO: La liga no tiene mánagers en la web."); return
        
        print(f"-> La web informa sobre la Jornada {jornada_web_num}. Sincronizando datos...")
        datos_web.sort(key=lambda x: x['puntos_totales'], reverse=True)
        
        # =================================================================
        # FASE 1: SINCRONIZACIÓN DE PUNTOS Y PUESTOS
        # En este bucle, solo actualizamos los datos en 'perfiles.json'.
        # =================================================================
        hay_cambios_reales = False
        for i, datos_manager_web in enumerate(datos_web):
            puesto_actual = i + 1
            manager_id_web = datos_manager_web['id_manager']
            perfil_encontrado = next((p for p in perfiles if p['id_manager'] == manager_id_web), None)
            
            if not perfil_encontrado:
                continue # Ignoramos mánagers sin perfil

            registro_web = {
                "jornada": jornada_web_num, 
                "puntos_jornada": datos_manager_web['puntos_jornada'], 
                "puesto": puesto_actual, 
                "puntos_totales": datos_manager_web['puntos_totales']
            }
            historial_local = next((h for h in perfil_encontrado['historial_temporada'] if h['jornada'] == jornada_web_num), None)

            if not historial_local:
                print(f"    - Añadiendo nueva J.{jornada_web_num} para {perfil_encontrado['nombre_mister']}...")
                perfil_encontrado['historial_temporada'].append(registro_web)
                perfil_encontrado['historial_temporada'].sort(key=lambda x: x['jornada'])
                hay_cambios_reales = True
            elif historial_local != registro_web:
                print(f"    - Actualizando J.{jornada_web_num} para {perfil_encontrado['nombre_mister']}...")
                historial_local.update(registro_web)
                hay_cambios_reales = True

        # Guardamos los perfiles actualizados ANTES de generar el reporte
        if hay_cambios_reales:
            guardar_perfiles(perfiles)
            print("-> ¡Cambios detectados! 'perfiles.json' ha sido actualizado.")
        else:
            print("-> No se han detectado cambios. Todo estaba ya sincronizado.")
        
        # =================================================================
        # FASE 2: GENERACIÓN DEL REPORTE COMPLETO
        # Ahora que los datos están al día, generamos las crónicas.
        # =================================================================
        print("\nPreparando para generar el reporte de la jornada...")

        # 1. Generamos la introducción y obtenemos los IDs de declaraciones ya usadas
        print(" -> Generando introducción...")
        texto_intro, ids_usados = generar_introduccion_semanal(perfiles, declaraciones, jornada_web_num)
        
        # 2. Elegimos un comentarista para las crónicas individuales
        print(" -> Eligiendo comentarista...")
        comentarista_elegido = elegir_comentarista('analisis') # O el rol que prefieras

        # 3. Calculamos los eventos especiales (opcional, pero recomendado)
        # Aquí deberías llamar a tu función que detecta piques, rachas, etc.
        # eventos_por_manager = calcular_eventos(perfiles)
        
        # 4. ¡LA LLAMADA ÚNICA! Generamos todas las crónicas de golpe
        print(" -> Generando TODAS las crónicas con la IA...")
        todas_las_cronicas = generar_todas_las_cronicas(
            perfiles=perfiles,
            todas_declaraciones=declaraciones,
            ids_ya_usadas=ids_usados,
            comentarista=comentarista_elegido
            # eventos_por_manager=eventos_por_manager # Descomenta si calculas eventos
        )
        print(" -> ¡Crónicas generadas con éxito!")

        # 5. Construimos el texto final del reporte para WhatsApp
        reporte_final_whatsapp = f"🏆 ✨ **CRÓNICA DE LA JORNADA {jornada_web_num}** ✨ 🏆\n\n{texto_intro}"
        
        for i, datos_manager_web in enumerate(datos_web):
            puesto_actual = i + 1
            manager_id_web = datos_manager_web['id_manager']
            perfil_encontrado = next((p for p in perfiles if p['id_manager'] == manager_id_web), None)
            
            if not perfil_encontrado:
                continue

            # Buscamos la crónica pre-generada en nuestro diccionario
            cronica_manager = todas_las_cronicas.get(manager_id_web, "_El cronista no hizo comentarios sobre este mánager._")
            
            titulo_especial = " ❄️ ¡CAMPEÓN DE INVIERNO! ❄️" if jornada_web_num == 19 and puesto_actual == 1 else ""
            
            reporte_final_whatsapp += (f"**{puesto_actual}. {perfil_encontrado['nombre_mister']} ({datos_manager_web['puntos_totales']} pts)**{titulo_especial}\n"
                                        f"*(Jornada: {datos_manager_web['puntos_jornada']} pts)*\n"
                                        f"_{cronica_manager}_\n\n")

        print("\n" + "="*50); print("REPORTE PARA WHATSAPP LISTO"); print("="*50)
        print(reporte_final_whatsapp)

    except Exception as e:
        print(f"\nERROR INESPERADO en el proceso de jornada: {e}")
    finally:
        print("\n--- PROCESO DE SINCRONIZACIÓN DE JORNADA FINALIZADO ---")

if __name__ == "__main__":
    main()