# scraper.py (Versión 8 - Definitiva)

from playwright.sync_api import sync_playwright, TimeoutError
from config import MISTER_URL, PLAYWRIGHT_PROFILE_PATH
import time
import re
import random

def escape_js_string(s):
    return s.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

def extraer_datos_mister():
    if not MISTER_URL:
        print("Error: Falta MISTER_URL en .env")
        return None

    print("Iniciando scraping (Versión 8 - Definitiva) con perfil DEDICADO...")

    with sync_playwright() as p:
        context = None
        try:
            browser_args = ['--disable-session-crashed-bubble', '--start-maximized']
            context = p.chromium.launch_persistent_context(
                PLAYWRIGHT_PROFILE_PATH,
                headless=False,
                args=browser_args,
                no_viewport=True,
                slow_mo=50
            )
            page = context.pages[0] if context.pages else context.new_page()

            print(f"Navegando a {MISTER_URL}...")
            page.goto(MISTER_URL, timeout=60000, wait_until="domcontentloaded")

            try:
                cookie_button = page.locator('button:has-text("ACEPTAR")').or_(page.locator('button:has-text("CONSENTIR")'))
                cookie_button.click(timeout=5000)
                print("-> Banner de cookies aceptado.")
                time.sleep(random.uniform(1, 2))
            except TimeoutError:
                print("-> No se encontró el banner de cookies o ya estaba aceptado.")
            except Exception as e:
                print(f"-> Error menor al cerrar cookies: {e}")

            print("\nAccediendo a la pestaña de Jornada para obtener datos históricos...")
            page.locator('button[data-tab="gameweek"]').click()
            
            jornada_selector_locator = "div.gameweek-selector-inline a.btn"
            list_selector = "div.panel-gameweek ul.player-list"
            
            page.locator(jornada_selector_locator).first.wait_for(timeout=20000)
            
            # --- LÓGICA CLAVE PARA FORZAR LA CARGA DE J1 ---
            print("-> Forzando la carga correcta de la Jornada 1...")
            jornada_buttons = page.locator(jornada_selector_locator)
            if jornada_buttons.count() > 1:
                jornada_buttons.nth(1).click() # Clic en J2
                page.locator(list_selector + " li").first.wait_for(timeout=10000) # Espera a que cargue J2
                time.sleep(0.5)
                jornada_buttons.nth(0).click() # Clic de vuelta en J1
                page.locator(list_selector + " li").first.wait_for(timeout=10000) # Espera a que cargue J1
                time.sleep(0.5)
                print("-> ¡Jornada 1 cargada correctamente!")
            # --- FIN DE LA LÓGICA CLAVE ---

            num_jornadas = page.locator(jornada_selector_locator).count()
            print(f"-> Detectadas {num_jornadas} jornadas en la web. Extrayendo datos de cada una...")

            datos_por_jornada = {}
            
            for i in range(num_jornadas):
                jornada_button = page.locator(jornada_selector_locator).nth(i)
                
                texto_jornada = jornada_button.inner_text()
                numeros = re.findall(r'\d+', texto_jornada)
                if not numeros: continue
                
                num_jornada_actual = int(numeros[0])
                print(f"   - Procesando Jornada {num_jornada_actual}...")

                try:
                    # Como ya hemos forzado la carga de J1, solo hacemos clic para el resto
                    if i > 0:
                        old_html = page.locator(list_selector).inner_html(timeout=10000)
                        old_html_escaped = escape_js_string(old_html)
                        jornada_button.click()
                        page.wait_for_function(
                            f"""() => document.querySelector('{list_selector}').innerHTML !== `{old_html_escaped}`""",
                            timeout=15000
                        )
                
                except TimeoutError as te:
                    print(f"     -> ¡ERROR! Timeout procesando la J.{num_jornada_actual}. Saltando esta jornada.")
                    continue
                
                time.sleep(0.5)

                datos_jornada_actual = {}
                filas_jugadores = page.query_selector_all(list_selector + " li")

                for fila in filas_jugadores:
                    link = fila.query_selector("a.user")
                    points = fila.query_selector("div.points")
                    if not link or not points: continue
                    
                    try:
                        manager_id = link.get_attribute("href").split('/')[1]
                        puntos_jornada = int(points.inner_text().strip().split()[0])
                        datos_jornada_actual[manager_id] = puntos_jornada
                    except (IndexError, ValueError):
                        continue
                
                datos_por_jornada[num_jornada_actual] = datos_jornada_actual

            print("\nAccediendo a la pestaña 'General' para obtener los totales...")
            page.locator('button[data-tab="total"]').click()
            page.locator("div.panel-total ul.player-list li a.user").first.wait_for(timeout=10000)
            datos_generales = {}
            for fila in page.query_selector_all("div.panel-total ul.player-list li"):
                link = fila.query_selector("a.user")
                points = fila.query_selector("div.points")
                if not link or not points: continue
                manager_id = link.get_attribute("href").split('/')[1]
                nombre_element = fila.query_selector("div.name")
                nombre_manager = nombre_element.inner_text().strip() if nombre_element else "N/A"
                puntos_totales = int(points.inner_text().strip().split()[0])
                datos_generales[manager_id] = {"nombre_mister": nombre_manager, "puntos_totales": puntos_totales}
            print("-> Fusionando todos los datos recopilados...")
            resultado_final = []
            for manager_id, data_general in datos_generales.items():
                historial_web = []
                for num_jornada, datos_jornada in datos_por_jornada.items():
                    puntos_en_jornada = datos_jornada.get(manager_id, 0)
                    historial_web.append({"jornada": num_jornada, "puntos_jornada": puntos_en_jornada})
                resultado_final.append({
                    "id_manager": manager_id,
                    "nombre_mister": data_general["nombre_mister"],
                    "puntos_totales": data_general["puntos_totales"],
                    "historial_web": sorted(historial_web, key=lambda x: x['jornada'])
                })
            return {"datos_managers": resultado_final}
        except TimeoutError as e:
            print(f"\n--- ERROR CRÍTICO DE TIMEOUT ---\nDetalles: {e}")
            return None
        except Exception as e:
            print(f"\n--- ERROR CRÍTICO INESPERADO ---\n{e}")
            return None
        finally:
            if context:
                print("Cerrando navegador...")
                context.close()