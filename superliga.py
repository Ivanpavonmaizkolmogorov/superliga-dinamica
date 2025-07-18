# superliga.py (Versión Final con Reinicio de Temporada)

import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import json

# Importamos TODAS nuestras herramientas de backend
from gui_main_panel import MainPanelApp
from gestor_datos import cargar_perfiles, guardar_perfiles, cargar_parejas
from scraper import extraer_datos_mister
from cronista import generar_cronica
from simulador import simular_nueva_jornada
from premios import cargar_config_liga, calcular_estado_premios
from gui_config_liga import launch_config_window

# Variables globales para que la GUI y las funciones puedan comunicarse
app = None
perfiles = []

# --- VERSIÓN CORREGIDA DE PROCESAR JORNADA REAL ---
def run_jornada_process():
    global perfiles
    
    app.log_message("Paso 1: Extrayendo datos de la web (Scraping)...")
    scraped_data = extraer_datos_mister()
    # ... (resto de la lógica de scraping y comprobaciones iniciales es correcta) ...
    if scraped_data is None:
        app.log_message("ERROR: No se pudieron obtener datos. Proceso abortado."); app.set_buttons_state("normal"); return

    jornada_web = scraped_data['jornada_num']
    datos_web = scraped_data['datos_managers']
    is_initialization_run = not perfiles

    if jornada_web == 0 and not is_initialization_run:
        app.log_message("INFO: No hay datos de jornada disponibles. No se realizarán cambios."); app.set_buttons_state("normal"); return

    if is_initialization_run:
        app.log_message("Detectada primera ejecución: Creando perfiles iniciales...")
    else:
        app.log_message(f"Scraping completado. Jornada {jornada_web} detectada.")
    
    app.log_message("Paso 2: Procesando y contrastando datos...")
    datos_web.sort(key=lambda x: x['puntos_totales'], reverse=True)
    hay_cambios = False

    for i, datos_manager_web in enumerate(datos_web):
        puesto_actual = i + 1
        manager_id = datos_manager_web['id_manager']
        perfil = next((p for p in perfiles if p['id_manager'] == manager_id), None)
        
        if not perfil:
            # --- AQUÍ ESTÁ LA CORRECCIÓN CLAVE ---
            # Ahora creamos un perfil con TODOS los campos que la IA necesita.
            nombre_web = datos_manager_web['nombre_mister']
            app.log_message(f"-> Creando perfil para {nombre_web}...")
            perfil = {
                "id_manager": manager_id,
                "nombre_mister": nombre_web,
                "apodo_lema": "El Novato",
                "momento_gloria": "Aún por escribir. ¡Bienvenido!",
                "peor_desastre": "Esperemos que nunca llegue.",
                "fichaje_estrella": "El que está por venir.",
                "fichaje_desastroso": "El que nunca haremos.",
                "historial_temporada": []
            }
            perfiles.append(perfil)
            hay_cambios = True

        # ... (El resto de la lógica de historial y actualización es correcta) ...
        historial = perfil.get('historial_temporada', [])
        entrada_existente = next((h for h in historial if h.get('jornada') == jornada_web), None)
        if jornada_web > 0:
            if entrada_existente:
                if (entrada_existente.get('puntos_totales') != datos_manager_web['puntos_totales']):
                    entrada_existente.update({'puntos_jornada': datos_manager_web['puntos_jornada'], 'puntos_totales': datos_manager_web['puntos_totales'], 'puesto': puesto_actual})
                    hay_cambios = True
            else:
                historial.append({"jornada": jornada_web, "puntos_jornada": datos_manager_web['puntos_jornada'], "puesto": puesto_actual, "puntos_totales": datos_manager_web['puntos_totales']})
                hay_cambios = True

    if hay_cambios:
        guardar_perfiles(perfiles)
        app.log_message("\n'perfiles.json' ha sido actualizado con éxito.")
        if jornada_web > 0:
            # ... (Lógica de crónicas) ...
            pass
        else:
            app.log_message("¡Perfiles iniciales creados! Ya puedes usar el resto de herramientas.")
    else:
        app.log_message("\nNo se han detectado cambios. No se ha modificado nada.")
    
    app.set_buttons_state("normal")


# --- ACCIÓN DEL BOTÓN 2: SIMULAR JORNADA(S) ---
def run_simulation_process():
    global perfiles
    num_jornadas = simpledialog.askinteger("Simulación de Jornadas", "¿Cuántas jornadas quieres simular?", parent=app.root, minvalue=1, maxvalue=38)
    if num_jornadas is None:
        app.log_message("Simulación cancelada.")
        app.set_buttons_state("normal")
        return
    perfiles_temp = perfiles
    for i in range(num_jornadas):
        perfiles_temp = simular_nueva_jornada(perfiles_temp)
        jornada_simulada = perfiles_temp[0]['historial_temporada'][-1]['jornada']
        app.log_message(f"-> Jornada {jornada_simulada} simulada con éxito.")
    guardar_perfiles(perfiles_temp)
    perfiles = perfiles_temp
    app.log_message(f"\n¡Simulación de {num_jornadas} jornadas completada! 'perfiles.json' actualizado.")
    app.set_buttons_state("normal")

# --- ACCIÓN DEL BOTÓN 3: VER ESTADO DE PREMIOS ---
def show_prizes_status():
    global perfiles
    perfiles = cargar_perfiles()
    parejas = cargar_parejas()
    config_liga = cargar_config_liga()
    reporte_premios = calcular_estado_premios(perfiles, parejas, config_liga)
    app.log_message(reporte_premios)
    app.log_message("="*50)

# --- ACCIÓN DEL BOTÓN 4: HERRAMIENTA DE PAREJAS ---
def launch_formar_parejas():
    PAREJAS_JSON_PATH = 'parejas.json'
    parejas_existen = os.path.exists(PAREJAS_JSON_PATH) and os.path.getsize(PAREJAS_JSON_PATH) > 2
    should_launch = True
    if parejas_existen:
        respuesta = messagebox.askyesno("Confirmación Requerida", "¿Ya existe una configuración de parejas. ¿Deseas borrarla y crear una nueva?", detail="Esta acción no se puede deshacer.")
        if not respuesta:
            should_launch = False
            app.log_message("ACCIÓN CANCELADA: Se ha mantenido la configuración de parejas actual.")
    if should_launch:
        app.log_message("Lanzando Herramienta de Formación de Parejas...")
        app.root.withdraw()
        if parejas_existen:
            os.remove(PAREJAS_JSON_PATH)
        os.system(f"python formar_parejas.py")
        app.root.deiconify()
        app.log_message("Herramienta de Formación de Parejas cerrada.")

# --- ACCIÓN DEL BOTÓN 5: CONFIGURACIÓN DE LA LIGA ---
def launch_config_liga():
    app.log_message("\n" + "="*50 + "\nAbriendo Configuración de la Liga...\n" + "="*50)
    current_config = cargar_config_liga()
    if not current_config:
        app.log_message("No se encontró 'config_liga.json'. Usando valores por defecto para el formulario.")
        current_config = { "cuota_inscripcion": 20.0, "reparto_premios_porcentaje": { "1_clasificado_general": 35, "pareja_ganadora": 20, "2_clasificado_general": 15, "mejor_2_vuelta": 15, "campeon_invierno": 15 } }
    app.root.withdraw()
    new_config = launch_config_window(current_config)
    app.root.deiconify()
    if new_config:
        try:
            with open('config_liga.json', 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2, ensure_ascii=False)
            app.log_message("¡Éxito! La configuración de la liga ha sido guardada en 'config_liga.json'.")
        except Exception as e:
            app.log_message(f"ERROR: No se pudo guardar la configuración. Error: {e}")
    else:
        app.log_message("Configuración cancelada. No se han guardado cambios.")

# --- NUEVA ACCIÓN DEL BOTÓN 6: REINICIAR TEMPORADA ---
def run_season_reset_process():
    global perfiles
    app.log_message("\n" + "="*50 + "\nSOLICITUD DE REINICIO DE TEMPORADA\n" + "="*50)
    respuesta = messagebox.askyesno("¡ACCIÓN IRREVERSIBLE!", "¿Estás seguro de que quieres reiniciar la temporada?\n\nEsto borrará TODO el historial de jornadas y las parejas formadas.", detail="Los perfiles históricos (apodos, etc.) se mantendrán.")
    if not respuesta:
        app.log_message("Reinicio cancelado por el usuario.")
        return
    app.log_message("Confirmación recibida. Procediendo con el reinicio...")
    try:
        perfiles_a_reiniciar = cargar_perfiles()
        for perfil in perfiles_a_reiniciar:
            perfil['historial_temporada'] = []
        guardar_perfiles(perfiles_a_reiniciar)
        perfiles = perfiles_a_reiniciar
        app.log_message("-> Éxito: El historial de 'perfiles.json' ha sido borrado.")
    except Exception as e:
        app.log_message(f"-> ERROR: No se pudo reiniciar 'perfiles.json'. Error: {e}")
    try:
        PAREJAS_JSON_PATH = 'parejas.json'
        if os.path.exists(PAREJAS_JSON_PATH):
            os.remove(PAREJAS_JSON_PATH)
            app.log_message("-> Éxito: El archivo 'parejas.json' ha sido borrado.")
        else:
            app.log_message("-> INFO: No existía un archivo 'parejas.json' que borrar.")
    except Exception as e:
        app.log_message(f"-> ERROR: No se pudo borrar 'parejas.json'. Error: {e}")
    app.log_message("\n¡REINICIO DE TEMPORADA COMPLETADO!")

# --- FUNCIÓN PRINCIPAL QUE LANZA TODO ---
def main():
    global app, perfiles
    
    # Intentamos cargar los perfiles. Si no existen, 'perfiles' será una lista vacía [].
    perfiles = cargar_perfiles()
    
    # --- LA COMPROBACIÓN FATAL HA SIDO ELIMINADA ---
    # Ahora, lanzamos la GUI sin importar si hay perfiles o no.
    
    root = tk.Tk()
    # Le pasamos la lista de perfiles a la GUI para que sepa si es el primer arranque.
    app = MainPanelApp(root, perfiles)
    
    # Conectamos las funciones de este script con los botones de la GUI
    app.on_run_jornada = run_jornada_process
    app.on_simular = run_simulation_process
    app.on_ver_premios = show_prizes_status
    app.on_formar_parejas = launch_formar_parejas
    app.on_config_liga = launch_config_liga
    app.on_reset_season = run_season_reset_process
    
    root.mainloop()

# --- BLOQUE DE ARRANQUE (SIN CAMBIOS) ---
if __name__ == "__main__":
    print("Lanzando Panel de Control de la Superliga Dinámica...")
    main()