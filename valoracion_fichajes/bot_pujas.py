from playwright.sync_api import sync_playwright
from config import MISTER_URL_MERCADO, PLAYWRIGHT_PROFILE_PATH
import time
import re

# --- SELECTORES ---
SELECTOR_BOTON_PUJAR = "button.btn-bid"
SELECTOR_INPUT_PUJA = "#input-tel"
SELECTOR_BOTON_ENVIAR = "#btn-send"
# --------------------

def clean_value(text_value):
    """Limpia un valor monetario para convertirlo en entero."""
    try:
        cleaned_text = re.sub(r'[^0-9-]', '', str(text_value))
        return int(cleaned_text) if cleaned_text else 0
    except (ValueError, TypeError):
        return 0

# Dentro de tu fichero bot_pujas.py

def realizar_pujas(pujas_a_realizar: list[dict]):
    """
    Automatiza el proceso de realizar pujas por una lista de jugadores.
    """
    print("INFO: Iniciando bot de pujas...")
    if not pujas_a_realizar:
        print("AVISO: No hay pujas para realizar.")
        return {"exito": True, "mensaje": "No había pujas en la lista."}

    with sync_playwright() as p:
        context = None
        try:
            context = p.chromium.launch_persistent_context(PLAYWRIGHT_PROFILE_PATH, headless=False, channel="msedge")
            page = context.new_page()

            print(f"INFO: Navegando a {MISTER_URL_MERCADO}")
            page.goto(MISTER_URL_MERCADO, timeout=60000)
            
            # --- LÍNEA CLAVE AÑADIDA ---
            # Forzamos al script a esperar a que el contenedor de la lista de jugadores esté presente
            print("INFO: Esperando a que la lista de jugadores del mercado cargue completamente...")
            page.wait_for_selector("ul#list-on-sale", timeout=20000)
            print("INFO: Lista de jugadores cargada.")
            # ---------------------------
            
            for puja_info in pujas_a_realizar:
                nombre_jugador = puja_info['nombre']
                valor_puja = puja_info['puja']
                print(f"\nProcesando a: {nombre_jugador} con puja de {valor_puja:,.0f} €")

                try:
                    # Usamos un selector que busca un li que contenga el apellido para ser más preciso
                    apellido = nombre_jugador.split()[-1]
                    player_container = page.locator(f"li:has-text('{apellido}')").first
                    
                    if not player_container.is_visible():
                        print(f"  AVISO: No se encontró a {nombre_jugador} visible en el mercado.")
                        continue
                    
                    boton_pujar = player_container.locator(SELECTOR_BOTON_PUJAR).first
                    print(f"  -> Jugador encontrado. Haciendo clic en el botón de pujar...")
                    boton_pujar.click()
                    
                    page.wait_for_selector(SELECTOR_INPUT_PUJA, timeout=10000)
                    print(f"  -> Pop-up abierto. Introduciendo puja...")
                    
                    page.fill(SELECTOR_INPUT_PUJA, str(valor_puja))
                    time.sleep(0.5)
                    page.click(SELECTOR_BOTON_ENVIAR)
                    print(f"  -> Puja por {nombre_jugador} realizada con éxito.")
                    
                    page.wait_for_load_state('networkidle', timeout=10000)
                    time.sleep(1)

                except Exception as e:
                    print(f"  ERROR: No se pudo completar la puja por {nombre_jugador}. Error: {e}")
                    page.reload(wait_until="networkidle")
            
            return {"exito": True, "mensaje": "Proceso de pujas finalizado."}

        except Exception as e:
            error_msg = f"--- ERROR CRÍTICO en el bot de pujas ---\n{e}"
            print(error_msg)
            return {"exito": False, "mensaje": str(e)}
        finally:
            if context:
                print("INFO: Cerrando navegador...")
                context.close()