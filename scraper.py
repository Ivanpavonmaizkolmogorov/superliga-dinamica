# scraper.py (Versión Multi-Jornada Robusta)

from playwright.sync_api import sync_playwright, TimeoutError
from config import MISTER_URL, PLAYWRIGHT_PROFILE_PATH
import time
import re
import random

def extraer_datos_mister():
    if not MISTER_URL:
        print("Error: Falta MISTER_URL en .env")
        return None

    print("Iniciando scraping MULTI-JORNADA con perfil DEDICADO...")

    with sync_playwright() as p:
        context = None
        try:
            # ... (Toda la configuración inicial del navegador es la misma y está bien) ...
            browser_args = ['--disable-session-crashed-bubble', '--start-maximized']
            context = p.chromium.launch_persistent_context(
                PLAYWRIGHT_PROFILE_PATH,
                headless=False,
                channel="msedge",
                args=browser_args,
                no_viewport=True,
                slow_mo=50
            )
            page = context.pages[0] if context.pages else context.new_page()

            print(f"Navegando a {MISTER_URL}...")
            # AHORA
            page.goto(MISTER_URL, timeout=60000, wait_until="domcontentloaded")

            # ... (La lógica para aceptar cookies es la misma y está bien) ...
            try:
                cookie_button = page.locator('button:has-text("ACEPTAR")').or_(page.locator('button:has-text("CONSENTIR")'))
                cookie_button.click(timeout=5000)
                print("-> Banner de cookies aceptado.")
                time.sleep(random.uniform(1, 2))
            except TimeoutError:
                print("-> No se encontró el banner de cookies o ya estaba aceptado.")
            except Exception as e:
                print(f"-> Error menor al cerrar cookies: {e}")

            # =========================================================================
            # INICIO DE LA NUEVA LÓGICA DE SCRAPING
            # =========================================================================

            # --- 1. EXTRACCIÓN DE PUNTOS POR JORNADA (LA PARTE MÁS IMPORTANTE) ---
            print("\nAccediendo a la pestaña de Jornada para obtener datos históricos...")
            page.locator('button[data-tab="gameweek"]').click()
            
            # Esperamos a que los botones de las jornadas (J1, J2, etc.) sean visibles
            jornada_selector_locator = "div.gameweek-selector-inline a.btn"
            page.locator(jornada_selector_locator).first.wait_for(timeout=15000)
            
            # Obtenemos el número total de botones de jornada
            num_jornadas = page.locator(jornada_selector_locator).count()
            print(f"-> Detectadas {num_jornadas} jornadas en la web. Extrayendo datos de cada una...")

            datos_por_jornada = {} # Estructura para guardar: {1: {manager_id: puntos}, 2: {manager_id: puntos}}

            for i in range(num_jornadas):
                # Volvemos a localizar los botones en cada iteración para evitar errores de "stale element"
                # ya que la página se refresca al hacer clic.
                jornada_button = page.locator(jornada_selector_locator).nth(i)
                
                texto_jornada = jornada_button.inner_text()
                numeros = re.findall(r'\d+', texto_jornada)
                if not numeros:
                    continue # Ignoramos si un botón no tiene número
                
                num_jornada_actual = int(numeros[0])
                # AHORA (DENTRO DEL BUCLE for)
                print(f"   - Procesando Jornada {num_jornada_actual}...")

                # ESPERA PRECISA: Hacemos clic y esperamos la respuesta de la red que contiene los datos de la clasificación.
                # Esto es mucho más fiable que esperar a que la red se quede "inactiva".
                with page.expect_response(lambda response: "standings" in response.url and response.status == 200, timeout=15000):
                    jornada_button.click()

                # No necesitamos más esperas aquí, la línea anterior ya garantiza que los datos cargaron.

                datos_jornada_actual = {}
                for fila in page.query_selector_all("div.panel-gameweek ul.player-list li"):
                    link = fila.query_selector("a.user")
                    points = fila.query_selector("div.points")
                    if not link or not points:
                        continue
                    
                    manager_id = link.get_attribute("href").split('/')[1]
                    puntos_jornada = int(points.inner_text().strip().split()[0])
                    datos_jornada_actual[manager_id] = puntos_jornada
                
                datos_por_jornada[num_jornada_actual] = datos_jornada_actual

            # --- 2. EXTRACCIÓN DE DATOS GENERALES (PUNTOS TOTALES Y NOMBRES) ---
            print("\nAccediendo a la pestaña 'General' para obtener los totales...")
            page.locator('button[data-tab="total"]').click()
            page.locator("div.panel-total ul.player-list li a.user").first.wait_for(timeout=10000)

            datos_generales = {}
            for fila in page.query_selector_all("div.panel-total ul.player-list li"):
                link = fila.query_selector("a.user")
                points = fila.query_selector("div.points")
                if not link or not points:
                    continue
                
                manager_id = link.get_attribute("href").split('/')[1]
                nombre_element = fila.query_selector("div.name")
                nombre_manager = nombre_element.inner_text().strip() if nombre_element else "N/A"
                puntos_totales = int(points.inner_text().strip().split()[0])
                
                datos_generales[manager_id] = {
                    "nombre_mister": nombre_manager,
                    "puntos_totales": puntos_totales
                }

            # --- 3. FUSIÓN FINAL DE TODOS LOS DATOS ---
            print("-> Fusionando todos los datos recopilados...")
            resultado_final = []
            
            for manager_id, data_general in datos_generales.items():
                historial_web = []
                for num_jornada, datos_jornada in datos_por_jornada.items():
                    puntos_en_jornada = datos_jornada.get(manager_id, 0)
                    historial_web.append({
                        "jornada": num_jornada,
                        "puntos_jornada": puntos_en_jornada
                    })

                resultado_final.append({
                    "id_manager": manager_id,
                    "nombre_mister": data_general["nombre_mister"],
                    "puntos_totales": data_general["puntos_totales"],
                    "historial_web": sorted(historial_web, key=lambda x: x['jornada']) # <--- NUEVA ESTRUCTURA
                })

            # La estructura de retorno ahora es diferente, no devuelve un único número de jornada
            return {"datos_managers": resultado_final}

        except TimeoutError as e:
            print(f"\n--- ERROR CRÍTICO DE TIMEOUT ---\nEl elemento esperado no apareció a tiempo.\nDetalles: {e}")
            return None
        except Exception as e:
            print(f"\n--- ERROR CRÍTICO INESPERADO ---\n{e}")
            return None
        finally:
            if context:
                print("Cerrando navegador...")
                context.close()