# scraper.py (Versión que devuelve el número de la jornada)

from playwright.sync_api import sync_playwright, TimeoutError
from config import MISTER_URL, USER_DATA_DIR

def extraer_datos_mister():
    """
    Función de scraping que ahora devuelve un diccionario con el número
    de la jornada scrapeada y los datos de los mánagers.
    """
    if not MISTER_URL:
        print("Error: Falta MISTER_URL_LIGA en .env"); return None

    print("Iniciando scraping con la sesión de Edge...")
    
    with sync_playwright() as p:
        context = None
        try:
            context = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False, channel="msedge")
            page = context.new_page()
            
            page.goto(MISTER_URL, timeout=60000, wait_until='domcontentloaded')
            print("Página cargada.")

            # ... (Lógica de cookies sin cambios) ...
            try:
                page.click('#didomi-notice-agree-button', timeout=5000)
            except TimeoutError:
                pass # No hacer nada si no está

            # ... (Lógica de extracción de datos generales sin cambios) ...
            page.click('button[data-tab="total"]')
            selector_lista_general = 'div.panel-total ul.player-list li'
            page.wait_for_selector(selector_lista_general, state='visible', timeout=15000)
            datos_generales = {}
            for fila in page.query_selector_all(selector_lista_general):
                link = fila.query_selector("a.user")
                points = fila.query_selector("div.points")
                if not link or not points: continue
                manager_id = link.get_attribute("href").split('/')[1]
                nombre_element = link.query_selector("div.name")
                nombre_manager = nombre_element.inner_text().strip() if nombre_element else link.inner_text().strip()
                datos_generales[manager_id] = {
                    "puntos_totales": int(points.inner_text().split()[0]),
                    "nombre_mister": nombre_manager
                }

            # --- EXTRACCIÓN DEL NÚMERO DE JORNADA ---
            page.click('button[data-tab="gameweek"]')
            jornada_num = 0
            
            datos_jornada = {}
            if page.is_visible("div.panel-gameweek div.empty"):
                print("La clasificación de la jornada está vacía (pretemporada).")
            else:
                selector_dropdown = "div.panel-gameweek select"
                page.wait_for_selector(selector_dropdown, timeout=15000)
                
                opciones = page.query_selector_all(f"{selector_dropdown} option")
                if opciones:
                    # Seleccionamos la última jornada disponible
                    ultima_jornada_value = opciones[-1].get_attribute("value")
                    jornada_texto = opciones[-1].inner_text().strip()
                    page.select_option(selector_dropdown, value=ultima_jornada_value)
                    
                    # Extraemos el número de la jornada del texto (ej. "Jornada 15")
                    try:
                        jornada_num = int(jornada_texto.split()[-1])
                        print(f"Detectada Jornada activa en la web: {jornada_num}")
                    except (ValueError, IndexError):
                        print(f"ADVERTENCIA: No se pudo extraer el número de la jornada del texto '{jornada_texto}'.")

                    # ... (Lógica de extracción de puntos de la jornada sin cambios) ...
                    page.wait_for_selector('div.panel-gameweek ul.player-list li', state='visible', timeout=10000)
                    for fila in page.query_selector_all("div.panel-gameweek ul.player-list li"):
                        link = fila.query_selector("a.user")
                        points = fila.query_selector("div.points")
                        if not link or not points: continue
                        manager_id = link.get_attribute("href").split('/')[1]
                        datos_jornada[manager_id] = {"puntos_jornada": int(points.inner_text().split()[0])}

            # --- Fusión de datos (sin cambios) ---
            resultado_final = []
            for manager_id, data in datos_generales.items():
                puntos_semanales = datos_jornada.get(manager_id, {}).get("puntos_jornada", 0)
                resultado_final.append({ "id_manager": manager_id, "nombre_mister": data["nombre_mister"], "puntos_jornada": puntos_semanales, "puntos_totales": data["puntos_totales"] })
            
            print(f"Scraping completado. Datos procesados para {len(resultado_final)} mánagers.")
            
            # --- DEVOLVEMOS UN DICCIONARIO CON AMBOS DATOS ---
            return {"jornada_num": jornada_num, "datos_managers": resultado_final}
            
        except Exception as e:
            print(f"\n--- OCURRIÓ UN ERROR DURANTE EL SCRAPING ---: {e}")
            return None
        finally:
            if context:
                context.close()