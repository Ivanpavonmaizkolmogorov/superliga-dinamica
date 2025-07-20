# scraper.py (Versión Final con Inyección de JavaScript)

from playwright.sync_api import sync_playwright, TimeoutError
from config import MISTER_URL, PLAYWRIGHT_PROFILE_PATH
import time

def extraer_datos_mister():
    if not MISTER_URL:
        print("Error: Falta MISTER_URL_LIGA en .env"); return None

    print("Iniciando scraping con perfil DEDICADO...")
    
    with sync_playwright() as p:
        context = None
        try:
            browser_args = ['--disable-session-crashed-bubble', '--start-maximized']
            context = p.chromium.launch_persistent_context(
                PLAYWRIGHT_PROFILE_PATH, 
                headless=False, 
                channel="msedge",
                args=browser_args,
                no_viewport=True
            )
            
            page = context.pages[0] if context.pages else context.new_page()
            
            print(f"Navegando a {MISTER_URL}...")
            page.goto(MISTER_URL, timeout=40000, wait_until="load")
            
            print("Página cargada. Esperando 3 segundos para que todo se asiente...")
            time.sleep(3)

            # --- ¡NUEVO MÉTODO DE CLIC: INYECCIÓN DE JAVASCRIPT! ---
            print("Forzando clic en 'General' mediante JavaScript...")
            try:
                # Esta línea ejecuta código JavaScript directamente en la página del navegador
                page.evaluate("document.querySelector('button[data-tab=\"total\"]').click()")
                print("-> Clic forzado enviado. Esperando 2 segundos para la reacción de la UI...")
                time.sleep(2)
            except Exception as e:
                # Este error solo debería ocurrir si no estamos logueados y el botón NO existe
                print(f"No se pudo forzar el clic (posiblemente no se ha iniciado sesión). Error: {e}")
                # Continuamos, la siguiente comprobación lo confirmará.

            # --- NUEVO MÉTODO DE COMPROBACIÓN: BUSCAR DATOS DIRECTAMENTE ---
            print("Comprobando el resultado: buscando datos de mánagers en el HTML...")
            filas_managers = page.query_selector_all("div.panel-total ul.player-list li a.user")
            
            # Si después de todo, no encontramos mánagers, ENTONCES pedimos el login.
            if not filas_managers:
                print("\n" + "="*60)
                print("¡ACCIÓN REQUERIDA! No se han encontrado datos de mánagers.")
                print("Esto puede ser porque la sesión no está iniciada o la liga está vacía.")
                print("1. En la ventana de Edge, INICIA SESIÓN con 'Recuérdame'.")
                print("2. Cierra la ventana del navegador MANUALMENTE cuando termines.")
                print("3. Vuelve a ejecutar el script.")
                print("="*60)
                page.wait_for_event('close', timeout=300000)
                return [] # Devolvemos lista vacía, que es un resultado válido.
            
            # --- SI HEMOS LLEGADO HASTA AQUÍ, ¡TENEMOS DATOS! ---
            print(f"-> ¡Éxito! {len(filas_managers)} mánagers encontrados. Extrayendo datos...")
            datos_generales = {}
            # Re-localizamos las filas completas para obtener los puntos
            for fila in page.query_selector_all("div.panel-total ul.player-list li"):
                link = fila.query_selector("a.user")
                points = fila.query_selector("div.points")
                if not link or not points: continue
                
                manager_id = link.get_attribute("href").split('/')[1]
                nombre_element = fila.query_selector("div.name")
                nombre_manager = nombre_element.inner_text().strip() if nombre_element else "Nombre no encontrado"
                puntos_totales = int(points.inner_text().split()[0])
                
                datos_generales[manager_id] = {
                    "puntos_totales": puntos_totales, "nombre_mister": nombre_manager
                }
            
            resultado_final = []
            for manager_id, data in datos_generales.items():
                resultado_final.append({
                    "id_manager": manager_id, "nombre_mister": data["nombre_mister"],
                    "puntos_jornada": 0, "puntos_totales": data["puntos_totales"]
                })
            
            print(f"Scraping completado. Datos procesados para {len(resultado_final)} mánagers.")
            return resultado_final

        except Exception as e:
            print(f"\n--- OCURRIÓ UN ERROR CRÍTICO DURANTE EL SCRAPING ---\nError: {e}")
            return None
        finally:
            if context:
                print("Cerrando el navegador..."); context.close(); print("Navegador cerrado.")