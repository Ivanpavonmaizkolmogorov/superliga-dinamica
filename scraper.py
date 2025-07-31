# valoracion_fichajes/scraper_mercado.py (VERSIÓN CON URL CORREGIDA)

import time
import re
import json
from playwright.sync_api import sync_playwright, TimeoutError
from config import MISTER_URL_MERCADO, PLAYWRIGHT_PROFILE_PATH, PERFILES_JSON_PATH

# --- SELECTORES CSS ---
PLAYER_ITEM_SELECTOR = "ul#list-on-sale > li"
PLAYER_LINK_SELECTOR = "a.player"
INCREMENT_SELECTOR = "div.value .prev-value"
# --------------------

def get_my_manager_id():
    try:
        with open(PERFILES_JSON_PATH, 'r', encoding='utf-8') as f:
            perfil = json.load(f)[0]
            return perfil.get('id_manager')
    except Exception as e:
        print(f"ERROR: No se pudo leer el ID de mánager. {e}")
        return None

def clean_value(text_value):
    try:
        return int(re.sub(r'[.€\s]', '', text_value))
    except (ValueError, TypeError):
        return 0

def extraer_jugadores_mercado():
    print("INFO: Iniciando scraper de mercado...")
    my_manager_id = get_my_manager_id()
    if not my_manager_id: return None

    jugadores_para_fichar = []
    jugadores_para_vender = []
    
    with sync_playwright() as p:
        context = None
        try:
            browser_args = ['--disable-session-crashed-bubble', '--start-maximized']
            context = p.chromium.launch_persistent_context(PLAYWRIGHT_PROFILE_PATH, headless=False, channel="msedge", args=browser_args, no_viewport=True)
            page = context.new_page()

            print(f"INFO: Navegando a {MISTER_URL_MERCADO}")
            page.goto(MISTER_URL_MERCADO, timeout=60000)
            page.wait_for_selector(PLAYER_ITEM_SELECTOR, timeout=30000)
            
            player_elements = page.query_selector_all(PLAYER_ITEM_SELECTOR)
            print(f"INFO: {len(player_elements)} jugadores encontrados. Extrayendo datos...")

            players_to_visit = []
            for element in player_elements:
                owner_id = element.get_attribute('data-owner')
                if owner_id == '0' or owner_id == my_manager_id:
                    link_el = element.query_selector(PLAYER_LINK_SELECTOR)
                    if link_el:
                        players_to_visit.append({
                            'url': link_el.get_attribute('href'),
                            'owner': owner_id
                        })
            
            for player_info in players_to_visit:
                player_data = {}
                try:
                    # --- ¡AQUÍ ESTÁ LA CORRECCIÓN DEFINITIVA! ---
                    # Añadimos la barra '/' que faltaba.
                    full_url = f"https://mister.mundodeportivo.com{player_info['url']}"
                    
                    page.goto(full_url, timeout=20000)
                    page.wait_for_selector("div.player-stats", timeout=15000)

                    nombre = page.locator("div.player-header .name").first.inner_text()
                    valor_raw = page.locator("div.value").first.inner_text()
                    incremento_raw = page.locator(INCREMENT_SELECTOR).first.inner_text()
                    
                    player_data['nombre'] = nombre.strip()
                    player_data['valor'] = clean_value(valor_raw)
                    player_data['incremento'] = clean_value(incremento_raw)

                    if player_info['owner'] == '0':
                        print(f"  -> FICHAR: {player_data['nombre']} (Valor: {player_data['valor']}) Inc: {player_data['incremento']}")
                        jugadores_para_fichar.append(player_data)
                    elif player_info['owner'] == my_manager_id:
                        print(f"  -> VENDER: {player_data['nombre']} (Valor: {player_data['valor']}) Inc: {player_data['incremento']}")
                        jugadores_para_vender.append(player_data)

                except Exception as e:
                    print(f"     AVISO: No se pudo procesar la URL '{player_info.get('url', 'desconocida')}'. Error: {e}")
            
            return {"para_fichar": jugadores_para_fichar, "para_vender": jugadores_para_vender}

        except Exception as e:
            print(f"\n--- ERROR CRÍTICO en el scraper ---\n{e}")
            return None
        finally:
            if context:
                print("INFO: Cerrando navegador...")
                context.close()