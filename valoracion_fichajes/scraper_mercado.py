# valoracion_fichajes/scraper_mercado.py (VERSIÓN FINAL Y CORREGIDA)

print("--- Fichero scraper_mercado.py cargado por Python (v_final) ---")

import time
import re
import json
import os
from playwright.sync_api import sync_playwright, TimeoutError
from config import MISTER_URL_MERCADO, PLAYWRIGHT_PROFILE_PATH, PERFILES_JSON_PATH

# --- SELECTORES CSS (Confirmados y Corregidos) ---
PLAYER_ITEM_SELECTOR = "ul#list-on-sale > li"
PLAYER_LINK_SELECTOR = "a.player"

# En la página de detalle de UN jugador:
PLAYER_INFO_SELECTOR = "div.player-info"           # Selector de espera FIABLE
PLAYER_DETAIL_VALUE_SELECTOR = "div.item:has-text('Valor') > div.value" # Selector específico para el valor
INCREMENT_SELECTOR = "span.prev-value"             # Selector para el incremento
# ------------------------------------------------

# --- ID DE TELEGRAM DEL USUARIO PRINCIPAL ---
# Este es el identificador único y estable para tu perfil.
MY_TELEGRAM_ID = 2078045747
# ---------------------------------------------

def get_my_manager_id():
    """
    Carga los perfiles y busca el ID de Míster que corresponde
    al ID de Telegram del usuario principal.
    """
    print("DEBUG: Entrando en get_my_manager_id...")
    try:
        print(f"DEBUG: Intentando abrir el fichero: {PERFILES_JSON_PATH}")
        with open(PERFILES_JSON_PATH, 'r', encoding='utf-8') as f:
            perfiles = json.load(f)
            # --- ¡CORRECCIÓN CLAVE! ---
            # Buscamos tu perfil específico usando el ID de Telegram.
            for perfil in perfiles:
                if perfil.get('telegram_user_id') == MY_TELEGRAM_ID:
                    manager_id = perfil.get('id_manager')
                    print(f"DEBUG: Perfil encontrado por Telegram ID ({MY_TELEGRAM_ID}). Tu ID de Míster es: {manager_id}")
                    return manager_id
            
            print(f"ERROR CRÍTICO: No se encontró ningún perfil con el Telegram ID {MY_TELEGRAM_ID} en perfiles.json.")
            return None

    except FileNotFoundError:
        print(f"ERROR CRÍTICO: No se encuentra el fichero '{PERFILES_JSON_PATH}'.")
        return None
    except Exception as e:
        print(f"ERROR CRÍTICO: Fallo al leer el ID de mánager desde '{PERFILES_JSON_PATH}'. Error: {e}")
        return None

def clean_value(text_value):
    """
    Función de limpieza robusta. Elimina TODO lo que no sea un número o un signo negativo.
    """
    try:
        cleaned_text = re.sub(r'[^0-9-]', '', str(text_value))
        return int(cleaned_text) if cleaned_text else 0
    except (ValueError, TypeError):
        return 0

def extraer_jugadores_mercado():
    print("INFO: Iniciando scraper de mercado...")
    my_manager_id = get_my_manager_id()
    if not my_manager_id:
        print("ERROR: No se pudo obtener el ID de mánager. Abortando scrape.")
        return None

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
                    relative_url = player_info['url']
                    if not relative_url.startswith('/'):
                        relative_url = '/' + relative_url
                    
                    full_url = f"https://mister.mundodeportivo.com{relative_url}"
                    
                    page.goto(full_url, timeout=20000)
                    page.wait_for_selector(PLAYER_INFO_SELECTOR, timeout=15000)

                    nombre = page.locator(f"{PLAYER_INFO_SELECTOR} .name").first.inner_text()
                    apellido = page.locator(f"{PLAYER_INFO_SELECTOR} .surname").first.inner_text()
                    nombre_completo = f"{nombre} {apellido}"

                    valor_raw = page.locator(PLAYER_DETAIL_VALUE_SELECTOR).first.inner_text()
                    incremento_raw = page.locator(INCREMENT_SELECTOR).first.inner_text()
                    
                    player_data['nombre'] = nombre_completo.strip()
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


# --- Bloque para probar este script de forma aislada ---
if __name__ == '__main__':
    print("\n--- INICIANDO PRUEBA INDEPENDIENTE DEL SCRAPER ---")
    datos = extraer_jugadores_mercado()
    if datos:
        print("\n--- RESULTADO DEL SCRAPING ---")
        print(json.dumps(datos, indent=2))
        try:
            with open('valoracion_cache.json', 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            print("\n✅ PRUEBA FINALIZADA: Fichero 'valoracion_cache.json' creado/actualizado.")
        except Exception as e:
            print(f"\n❌ ERROR AL GUARDAR CACHÉ: {e}")
    else:
        print("\n❌ PRUEBA FALLIDA: El scraper no devolvió datos.")