# Contenido para el fichero: scraper_ofertas_recibidas.py

from playwright.sync_api import sync_playwright
from config import MISTER_URL_MERCADO, PLAYWRIGHT_PROFILE_PATH
import re

# --- SELECTORES DEFINITIVOS (Basados en tu HTML) ---
OFERTAS_RECIBIDAS_BTN_SELECTOR = "div.offers-received"

# Selector para cada bloque de jugador + oferta
SELECTOR_BLOQUE_OFERTA = "li.offer-wrapper"

# Dentro de un bloque, selector para el BOTÓN que contiene el nombre completo
SELECTOR_BOTON_JUGADOR = "button.btn-resale"

# Dentro de un bloque, selector para el valor de la oferta de la máquina
SELECTOR_VALOR_OFERTA = "div.amount"
# ---------------------------------------------------

def clean_value(text_value):
    try:
        cleaned_text = re.sub(r'[^0-9-]', '', str(text_value))
        return int(cleaned_text) if cleaned_text else 0
    except (ValueError, TypeError):
        return 0

def extraer_ofertas_maquina():
    """Scraper que entra a las ofertas recibidas y extrae los valores."""
    print("INFO: Iniciando scraper de ofertas de la máquina...")
    ofertas = {}

    with sync_playwright() as p:
        context = None
        try:
            context = p.chromium.launch_persistent_context(PLAYWRIGHT_PROFILE_PATH, headless=False, channel="msedge")
            page = context.new_page()

            print(f"INFO: Navegando a {MISTER_URL_MERCADO}")
            page.goto(MISTER_URL_MERCADO, timeout=60000)
            
            print("INFO: Buscando y haciendo clic en 'ofertas recibidas'...")
            page.wait_for_selector(OFERTAS_RECIBIDAS_BTN_SELECTOR, timeout=20000)
            page.click(OFERTAS_RECIBIDAS_BTN_SELECTOR)
            
            print("INFO: Esperando a que cargue la lista de ofertas...")
            page.wait_for_selector(SELECTOR_BLOQUE_OFERTA, timeout=20000)
            
            bloques_ofertas = page.query_selector_all(SELECTOR_BLOQUE_OFERTA)
            print(f"INFO: {len(bloques_ofertas)} ofertas encontradas. Extrayendo datos...")

            for bloque in bloques_ofertas:
                try:
                    # Buscamos el botón que tiene el nombre en el atributo 'data-name'
                    boton_jugador = bloque.query_selector(SELECTOR_BOTON_JUGADOR)
                    if not boton_jugador:
                        continue # Si no encontramos el botón, saltamos este jugador

                    nombre_jugador = boton_jugador.get_attribute("data-name")
                    
                    # Buscamos el valor de la oferta
                    oferta_raw = bloque.query_selector(SELECTOR_VALOR_OFERTA).inner_text()
                    valor_oferta = clean_value(oferta_raw)
                    
                    if nombre_jugador and valor_oferta > 0:
                        ofertas[nombre_jugador] = valor_oferta
                        print(f"  -> Oferta para {nombre_jugador}: {valor_oferta}")

                except Exception as e:
                    print(f"  AVISO: No se pudo procesar un bloque de oferta. Error: {e}")
            
            return ofertas

        except Exception as e:
            print(f"\n--- ERROR CRÍTICO en el scraper de ofertas recibidas ---\n{e}")
            return None
        finally:
            if context:
                print("INFO: Cerrando navegador...")
                context.close()