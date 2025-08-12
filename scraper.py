# scraper.py (Versión "Bingo" con Inyección de JavaScript que SÍ FUNCIONABA)

from playwright.sync_api import sync_playwright, TimeoutError
from config import MISTER_URL, PLAYWRIGHT_PROFILE_PATH
import time
import re

def extraer_datos_mister():
    if not MISTER_URL: print("Error: Falta MISTER_URL_LIGA en .env"); return None

    print("Iniciando scraping con perfil DEDICADO...")
    
    with sync_playwright() as p:
        context = None
        try:
            browser_args = ['--disable-session-crashed-bubble', '--start-maximized']
            context = p.chromium.launch_persistent_context(PLAYWRIGHT_PROFILE_PATH, headless=False, channel="msedge", args=browser_args, no_viewport=True)
            page = context.pages[0] if context.pages else context.new_page()
            
            print(f"Navegando a {MISTER_URL}...")
            page.goto(MISTER_URL, timeout=40000, wait_until="load")
            
            print("Página cargada. Esperando 3 segundos...")
            time.sleep(3)

            # --- Lógica de CLIC FORZADO ---
            try:
                page.evaluate("document.querySelector('button[data-tab=\"total\"]').click()")
                print("-> Clic en 'General' forzado. Esperando 2s...")
                time.sleep(2)
            except Exception:
                # Si esto falla es porque no estamos logueados.
                pass

            # --- COMPROBACIÓN DE SESIÓN Y PAUSA PARA LOGIN MANUAL ---
            filas_managers_html = page.query_selector_all("div.panel-total ul.player-list li a.user")
            
            if not filas_managers_html:
                print("\n¡ACCIÓN REQUERIDA! Sesión no iniciada o caducada.")
                print("Por favor, inicia sesión en la ventana del navegador que se ha abierto.")
                print("La sesión se guardará en tu perfil para futuras ejecuciones.")
                print("Cuando hayas terminado, vuelve a esta consola y presiona 'Enter' para continuar...")
                input()
                
                print("Recargando la página para continuar con el scraping...")
                page.reload(wait_until="load")
                time.sleep(3) # Espera extra para que cargue todo tras el login

                # Reintentamos la búsqueda de datos tras el login manual
                filas_managers_html = page.query_selector_all("div.panel-total ul.player-list li a.user")
                if not filas_managers_html:
                    print("\nError: No se han podido encontrar los datos de mánagers incluso después de iniciar sesión.")
                    print("Asegúrate de estar en la página correcta de la clasificación de la liga.")
                    return None

            # --- SI HAY DATOS, EXTRAEMOS TODO ---
            print(f"-> ¡Éxito! {len(filas_managers_html)} mánagers encontrados. Extrayendo datos...")
            # 1. Datos Generales
            datos_generales = {}
            for fila in page.query_selector_all("div.panel-total ul.player-list li"):
                link = fila.query_selector("a.user"); points = fila.query_selector("div.points")
                if not link or not points: continue
                manager_id = link.get_attribute("href").split('/')[1]
                nombre_element = fila.query_selector("div.name")
                nombre_manager = nombre_element.inner_text().strip() if nombre_element else "N/A"
                puntos_totales = int(points.inner_text().split()[0])
                datos_generales[manager_id] = {"nombre_mister": nombre_manager, "puntos_totales": puntos_totales}

            # 2. Datos de Jornada
            page.evaluate("document.querySelector('button[data-tab=\"gameweek\"]').click()")
            time.sleep(2)
            
            datos_jornada = {}
            numero_jornada_actual = 1
            if not page.locator('div.panel-gameweek div.empty').is_visible():
                opciones = page.query_selector_all("div.panel-gameweek select option")
                if opciones:
                    ultima_opcion = opciones[-1]
                    texto_jornada = ultima_opcion.inner_text()
                    numeros = re.findall(r'\d+', texto_jornada)
                    if numeros: numero_jornada_actual = int(numeros[0])
                    page.select_option("div.panel-gameweek select", value=ultima_opcion.get_attribute("value"))
                    time.sleep(2)
                
                for fila in page.query_selector_all("div.panel-gameweek ul.player-list li"):
                    link = fila.query_selector("a.user"); points = fila.query_selector("div.points")
                    if not link or not points: continue
                    manager_id = link.get_attribute("href").split('/')[1]
                    datos_jornada[manager_id] = int(points.inner_text().split()[0])
            
            print(f"-> Última jornada detectada: {numero_jornada_actual}")

            # 3. Fusión Final
            resultado_final = []
            for manager_id, data in datos_generales.items():
                resultado_final.append({
                    "id_manager": manager_id, "nombre_mister": data["nombre_mister"],
                    "puntos_jornada": datos_jornada.get(manager_id, 0),
                    "puntos_totales": data["puntos_totales"]
                })
            
            return {"numero_jornada": numero_jornada_actual, "datos_managers": resultado_final}

        except Exception as e:
            print(f"\n--- ERROR CRÍTICO ---\n{e}"); return None
        finally:
            if context: print("Cerrando navegador..."); context.close()