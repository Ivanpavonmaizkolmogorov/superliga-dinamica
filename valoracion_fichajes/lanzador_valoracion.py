import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import locale
from .gui_valoracion import VistaValoracion
from .motor_calculo import MotorCalculo
# --- LÍNEA AÑADIDA ---
from .scraper_mercado import extraer_jugadores_mercado

CACHE_FILE = 'valoracion_cache.json'

class ValoracionController:
    def __init__(self, root):
        self.root = root
        try:
            locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        except locale.Error:
            try: locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')
            except locale.Error: print("Advertencia: No se encontró la configuración regional española.")
        
        self.view = VistaValoracion(root, self)
        self.view.pack(expand=True, fill=tk.BOTH)
        self.jugadores_mercado = []
        self.motores_calculo = {}
        self.current_player = None
        self.current_type = None
        self.load_data_from_cache()

    def load_data_from_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.jugadores_mercado = json.load(f)
                self.preparar_y_poblar_tablas()
                return
            except Exception as e: print(f"Error cargando caché: {e}")
        messagebox.showinfo("Caché Vacío", "Pulsa 'Actualizar' para cargar la información.")

    def trigger_scrape(self):
        self.view.btn_update.config(state="disabled", text="Actualizando...")
        threading.Thread(target=self.scrape_and_save_to_cache, daemon=True).start()

    def scrape_and_save_to_cache(self):
        # Esta llamada ahora funcionará gracias al import
        self.jugadores_mercado = extraer_jugadores_mercado()
        if self.jugadores_mercado:
            try:
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.jugadores_mercado, f, indent=2, ensure_ascii=False)
            except Exception: pass
        self.root.after(0, self.preparar_y_poblar_tablas)

    def preparar_y_poblar_tablas(self):
        self.view.btn_update.config(state="normal", text="Actualizar Datos del Mercado")
        if not self.jugadores_mercado: return

        self.motores_calculo.clear()
        jugadores_fichar = self.jugadores_mercado.get('para_fichar', [])
        jugadores_vender = self.jugadores_mercado.get('para_vender', [])
        for jugador in jugadores_fichar + jugadores_vender:
            self.motores_calculo[jugador['nombre']] = MotorCalculo(jugador)

        headers_fichar = {"id": ("nombre", "valor", "inc", "puja", "dias", "em", "equilibrio"), "display": ["Nombre", "Valor", "Inc.", "Mi Puja", "Días", "Esp. Matemática", "Puja Equilibrio"]}
        datos_fichar = []
        for j in jugadores_fichar:
            motor = self.motores_calculo[j['nombre']]
            config_inicial = {"puja_k": j['valor'], "dias_solares": 8}
            resultado = motor.analizar_compra(config_inicial)
            equilibrio = motor.encontrar_puja_equilibrio(config_inicial, "fichar")
            datos_fichar.append([j['nombre'], j['valor'], j['incremento'], j['valor'], 8, resultado['esperanza_matematica'], equilibrio])
        self.view.poblar_tabla("fichar", {"headers_id": headers_fichar["id"], "headers_display": headers_fichar["display"], "data": datos_fichar})

        headers_vender = {"id": ("nombre", "valor", "inc", "oferta_maq", "ofertas_hoy", "dias", "em", "equilibrio"), "display": ["Nombre", "Valor", "Inc.", "Oferta Máquina", "Ofertas Hoy", "Días", "Esp. Matemática", "Oferta Equilibrio"]}
        datos_vender = []
        for j in jugadores_vender:
            motor = self.motores_calculo[j['nombre']]
            config_inicial = {"oferta_maquina": j['valor'], "ofertas_hoy": 1, "dias_solares": 8}
            resultado = motor.analizar_venta(config_inicial)
            equilibrio = motor.encontrar_puja_equilibrio(config_inicial, "vender")
            datos_vender.append([j['nombre'], j['valor'], j['incremento'], j['valor'], 1, 8, resultado['esperanza_matematica'], equilibrio])
        self.view.poblar_tabla("vender", {"headers_id": headers_vender["id"], "headers_display": headers_vender["display"], "data": datos_vender})

    def on_player_select(self, event, list_type):
        tree = self.view.tree_fichar if list_type == "fichar" else self.view.tree_vender
        selection = tree.selection()
        if not selection: return
        
        item_id = selection[0]
        item_values = tree.item(item_id, 'values')
        nombre_jugador = item_values[0]
        
        self.current_type = list_type
        lista_completa = self.jugadores_mercado.get('para_fichar' if list_type == 'fichar' else 'para_vender', [])
        self.current_player = next((p for p in lista_completa if p['nombre'] == nombre_jugador), None)

        if self.current_player:
            self.view.lbl_nombre.config(text=self.current_player['nombre'])
            self.view.set_active_panel(list_type)
            
            def to_int(value_str):
                return int(float(str(value_str).replace('.', '').replace(',', '.')))

            if list_type == 'fichar':
                self.view.puja_var.set(to_int(item_values[3]))
                self.view.dias_var.set(to_int(item_values[4]))
            else: # vender
                self.view.oferta_maquina_var.set(to_int(item_values[3]))
                self.view.ofertas_hoy_var.set(to_int(item_values[4]))
                self.view.dias_var.set(to_int(item_values[5]))
            
            self.recalculate_results()

    def recalculate_results(self, event=None):
        if not self.current_player: return
        
        motor = self.motores_calculo.get(self.current_player['nombre'])
        if not motor: return
        
        tree = self.view.tree_fichar if self.current_type == 'fichar' else self.view.tree_vender
        item_id = self.current_player['nombre']
        
        try:
            current_values = list(tree.item(item_id)['values'])
            config_usuario = {}
            valor_equilibrio = 0
            
            if self.current_type == 'fichar':
                puja = self.view.puja_var.get()
                dias = self.view.dias_var.get()
                config_usuario = {"puja_k": puja, "dias_solares": dias}
                resultado = motor.analizar_compra(config_usuario)
                valor_equilibrio = motor.encontrar_puja_equilibrio(config_usuario, self.current_type)
                
                current_values[3] = locale.format_string('%d', puja, grouping=True)
                current_values[4] = dias
                current_values[5] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                current_values[6] = locale.format_string('%d', valor_equilibrio, grouping=True)
                
            else: # vender
                oferta_maq = self.view.oferta_maquina_var.get()
                ofertas_hoy = self.view.ofertas_hoy_var.get()
                dias = self.view.dias_var.get()
                config_usuario = {"oferta_maquina": oferta_maq, "ofertas_hoy": ofertas_hoy, "dias_solares": dias}
                resultado = motor.analizar_venta(config_usuario)
                valor_equilibrio = motor.encontrar_puja_equilibrio(config_usuario, self.current_type)
                
                current_values[3] = locale.format_string('%d', oferta_maq, grouping=True)
                current_values[4] = ofertas_hoy
                current_values[5] = dias
                current_values[6] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                current_values[7] = locale.format_string('%d', valor_equilibrio, grouping=True)

            esperanza_formateada = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.view.lbl_valor_apuesta.config(text=f"{esperanza_formateada} €")
            self.view.lbl_equilibrio_valor.config(text=f"{locale.format_string('%d', valor_equilibrio, grouping=True)} €")

            tree.item(item_id, values=tuple(current_values))
        
        except (tk.TclError, ValueError, IndexError) as e:
            print(f"Error al recalcular: {e}")

def main():
    root = tk.Tk()
    app = ValoracionController(root)
    root.mainloop()

if __name__ == '__main__':
    main()