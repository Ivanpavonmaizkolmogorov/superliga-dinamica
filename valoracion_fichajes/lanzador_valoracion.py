import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import locale
from .gui_valoracion import VistaValoracion
from .motor_calculo import MotorCalculo
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
        self.jugadores_mercado = {}
        self.motores_calculo = {}
        self.current_player = None
        self.current_type = None
        
        self.datos_originales_fichar = []
        self.datos_originales_vender = []
        self.sort_state = {}
        
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

        headers_fichar = {"id": ("nombre", "valor", "inc", "puja", "dias", "em", "equilibrio", "margen"), "display": ["Nombre", "Valor", "Inc.", "Mi Puja", "Días", "Esp. Matemática", "Puja Equilibrio", "Margen"]}
        datos_fichar = []
        dias_defecto = self.view.dias_global_var.get()
        for j in jugadores_fichar:
            motor = self.motores_calculo[j['nombre']]
            config = {"puja_k": j['valor'], "dias_solares": dias_defecto}
            resultado = motor.analizar_compra(config)
            equilibrio = motor.encontrar_puja_equilibrio(dias_defecto, "fichar")
            margen = equilibrio - j['valor']
            datos_fichar.append([j['nombre'], j['valor'], j['incremento'], j['valor'], dias_defecto, resultado['esperanza_matematica'], equilibrio, margen])
        self.datos_originales_fichar = datos_fichar.copy()
        self.view.poblar_tabla("fichar", {"headers_id": headers_fichar["id"], "headers_display": headers_fichar["display"], "data": datos_fichar})

        headers_vender = {"id": ("nombre", "valor", "inc", "oferta_maq", "ofertas_hoy", "dias", "em", "equilibrio", "margen"), "display": ["Nombre", "Valor", "Inc.", "Oferta Máquina", "Ofertas Hoy", "Días", "Esp. Matemática", "Oferta Equilibrio", "Margen"]}
        datos_vender = []
        for j in jugadores_vender:
            motor = self.motores_calculo[j['nombre']]
            config = {"oferta_maquina": j['valor'], "ofertas_hoy": 1, "dias_solares": dias_defecto}
            resultado = motor.analizar_venta(config)
            equilibrio = motor.encontrar_puja_equilibrio(dias_defecto, "vender")
            margen = equilibrio - j['valor']
            datos_vender.append([j['nombre'], j['valor'], j['incremento'], j['valor'], 1, dias_defecto, resultado['esperanza_matematica'], equilibrio, margen])
        self.datos_originales_vender = datos_vender.copy()
        self.view.poblar_tabla("vender", {"headers_id": headers_vender["id"], "headers_display": headers_vender["display"], "data": datos_vender})

    def on_header_click(self, col_id, tipo_tabla):
        estado_actual = self.sort_state.get(col_id, None)
        if estado_actual == 'asc': nuevo_estado = 'desc'
        elif estado_actual == 'desc': nuevo_estado = None
        else: nuevo_estado = 'asc'
        
        self.sort_state.clear()
        if nuevo_estado: self.sort_state[col_id] = nuevo_estado

        if tipo_tabla == "fichar":
            datos_a_ordenar = self.datos_originales_fichar.copy()
            headers = {"id": ("nombre", "valor", "inc", "puja", "dias", "em", "equilibrio", "margen"), "display": ["Nombre", "Valor", "Inc.", "Mi Puja", "Días", "Esp. Matemática", "Puja Equilibrio", "Margen"]}
        else:
            datos_a_ordenar = self.datos_originales_vender.copy()
            headers = {"id": ("nombre", "valor", "inc", "oferta_maq", "ofertas_hoy", "dias", "em", "equilibrio", "margen"), "display": ["Nombre", "Valor", "Inc.", "Oferta Máquina", "Ofertas Hoy", "Días", "Esp. Matemática", "Oferta Equilibrio", "Margen"]}

        if nuevo_estado:
            col_index = headers["id"].index(col_id)
            def sort_key(row):
                val = row[col_index]
                if isinstance(val, str) and val.strip() != row[0]:
                    try: return float(val)
                    except ValueError: return val
                return val
            datos_ordenados = sorted(datos_a_ordenar, key=sort_key, reverse=(nuevo_estado == 'desc'))
            self.view.poblar_tabla(tipo_tabla, {"headers_id": headers["id"], "headers_display": headers["display"], "data": datos_ordenados})
        else:
            self.view.poblar_tabla(tipo_tabla, {"headers_id": headers["id"], "headers_display": headers["display"], "data": datos_a_ordenar})

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
                try: return int(float(str(value_str).replace('.', '').replace(',', '.')))
                except (ValueError, TypeError): return 0

            if list_type == 'fichar':
                self.view.puja_var.set(to_int(item_values[3]))
                self.view.dias_var.set(to_int(item_values[4]))
            else:
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
            if self.current_type == 'fichar':
                puja = self.view.puja_var.get()
                dias = self.view.dias_var.get()
                config_usuario = {"puja_k": puja, "dias_solares": dias}
                resultado = motor.analizar_compra(config_usuario)
                valor_equilibrio = motor.encontrar_puja_equilibrio(dias, self.current_type)
                margen = valor_equilibrio - puja
                current_values[3] = locale.format_string('%d', puja, grouping=True)
                current_values[4] = dias
                current_values[5] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                current_values[6] = locale.format_string('%d', valor_equilibrio, grouping=True)
                current_values[7] = locale.format_string('%d', margen, grouping=True)
            else: # vender
                oferta_maq = self.view.oferta_maquina_var.get()
                ofertas_hoy = self.view.ofertas_hoy_var.get()
                dias = self.view.dias_var.get()
                config_usuario = {"oferta_maquina": oferta_maq, "ofertas_hoy": ofertas_hoy, "dias_solares": dias}
                resultado = motor.analizar_venta(config_usuario)
                valor_equilibrio = motor.encontrar_puja_equilibrio(dias, self.current_type)
                margen = valor_equilibrio - oferta_maq
                current_values[3] = locale.format_string('%d', oferta_maq, grouping=True)
                current_values[4] = ofertas_hoy
                current_values[5] = dias
                current_values[6] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                current_values[7] = locale.format_string('%d', valor_equilibrio, grouping=True)
                current_values[8] = locale.format_string('%d', margen, grouping=True)

            esperanza_formateada = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.view.lbl_valor_apuesta.config(text=f"{esperanza_formateada} €")
            self.view.lbl_equilibrio_valor.config(text=f"{locale.format_string('%d', valor_equilibrio, grouping=True)} €")
            tree.item(item_id, values=tuple(current_values))
        except (tk.TclError, ValueError, IndexError) as e:
            print(f"Error al recalcular: {e}")

    def recalculate_all_rows(self):
        self.root.config(cursor="watch")
        tipo_tabla = "fichar" if self.view.notebook.tab(self.view.notebook.select(), "text") == 'Para Fichar' else "vender"
        tree = self.view.tree_fichar if tipo_tabla == "fichar" else self.view.tree_vender
        nuevos_dias = self.view.dias_global_var.get()

        for item_id in tree.get_children():
            try:
                motor = self.motores_calculo.get(item_id)
                if not motor: continue
                current_values = list(tree.item(item_id, 'values'))
                def to_int(value_str):
                    try: return int(float(str(value_str).replace('.', '').replace(',', '.')))
                    except (ValueError, TypeError): return 0
                if tipo_tabla == "fichar":
                    puja = to_int(current_values[3])
                    config = {"puja_k": puja, "dias_solares": nuevos_dias}
                    resultado = motor.analizar_compra(config)
                    equilibrio = motor.encontrar_puja_equilibrio(nuevos_dias, tipo_tabla)
                    margen = equilibrio - puja
                    current_values[4] = nuevos_dias
                    current_values[5] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    current_values[6] = locale.format_string('%d', equilibrio, grouping=True)
                    current_values[7] = locale.format_string('%d', margen, grouping=True)
                else: # vender
                    oferta_maq = to_int(current_values[3])
                    ofertas_hoy = to_int(current_values[4])
                    config = {"oferta_maquina": oferta_maq, "ofertas_hoy": ofertas_hoy, "dias_solares": nuevos_dias}
                    resultado = motor.analizar_venta(config)
                    equilibrio = motor.encontrar_puja_equilibrio(nuevos_dias, tipo_tabla)
                    margen = equilibrio - oferta_maq
                    current_values[5] = nuevos_dias
                    current_values[6] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    current_values[7] = locale.format_string('%d', equilibrio, grouping=True)
                    current_values[8] = locale.format_string('%d', margen, grouping=True)
                tree.item(item_id, values=tuple(current_values))
            except Exception as e:
                print(f"Error recalculando fila para {item_id}: {e}")
        self.root.config(cursor="")
        
def main():
    root = tk.Tk()
    app = ValoracionController(root)
    root.mainloop()

if __name__ == '__main__':
    main()