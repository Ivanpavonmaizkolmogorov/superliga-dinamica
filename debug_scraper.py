
from playwright.sync_api import sync_playwright
from config import MISTER_URL, PLAYWRIGHT_PROFILE_PATH
import re

def debug_scraper():
    print(f"URL: {MISTER_URL}")
    print(f"Profile: {PLAYWRIGHT_PROFILE_PATH}")
    
    context = None
    with sync_playwright() as p:
        try:
            print("Lanzando navegador (PERFIL TEMPORAL)...")
            # Cambiamos a contexto temporal para descartar corrupción de perfil
            browser = p.chromium.launch(
                headless=True, # Headless True para mayor compatibilidad en este test
                args=['--disable-session-crashed-bubble', '--start-maximized', '--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'] 
            )
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            print("Navegando a la web...")
            page.goto(MISTER_URL, timeout=60000, wait_until="domcontentloaded")
            
            print("Clic en pestaña Jornada...")
            page.locator('button[data-tab="gameweek"]').click()
            
            # Selector original
            jornada_selector_locator = "div.gameweek-selector-inline a.btn"
            page.locator(jornada_selector_locator).first.wait_for(timeout=10000)
            
            botones = page.locator(jornada_selector_locator)
            count = botones.count()
            print(f"\n--- DEBUG JORNADAS DETECTADAS (Total: {count}) ---")
            
            for i in range(count):
                texto = botones.nth(i).inner_text()
                href = botones.nth(i).get_attribute("href")
                print(f"  [{i}]: Texto='{texto}' | Href='{href}'")
                
            print("\n----------------------------------------------")
            
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            if context:
                context.close()

if __name__ == "__main__":
    debug_scraper()
