# valoracion_fichajes/lanzador_valoracion.py
import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
from .gui_valoracion import VistaValoracion
from .scraper_mercado import extraer_jugadores_mercado
from .motor_calculo import MotorCalculo

CACHE_FILE = 'valoracion_cache.json'

class ValoracionController:
    # ... (el __init__ y las funciones de scrapeo y carga no cambian) ...
    def __init__(self, root):
        self.root = root
        self.view = VistaValoracion(root, self)
        self.view.pack(expand=True, fill=tk.BOTH)
        self.jugadores_para_fichar = []
        self.jugadores_para_vender = []
        self.motores_calculo = {}
        self.current_player_motor = None
        self.load_data_from_cache()

    def load_data_from_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    datos_mercado = json.load(f)
                self.actualizar_gui_con_datos(datos_mercado)
                return
            except Exception: pass
        messagebox.showinfo("Caché Vacío", "Pulsa 'Actualizar' para cargar la información.")
        self.actualizar_gui_con_datos(None)

    def trigger_scrape(self):
        self.view.btn_update.config(state="disabled", text="Actualizando...")
        self.view.populate_list('fichar', [], is_loading=True)
        self.view.populate_list('vender', [], is_loading=True)
        thread = threading.Thread(target=self.scrape_and_save_to_cache, daemon=True)
        thread.start()

    def scrape_and_save_to_cache(self):
        datos_mercado = extraer_jugadores_mercado()
        if datos_mercado:
            try:
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(datos_mercado, f, indent=2, ensure_ascii=False)
            except Exception: pass
        self.root.after(0, self.actualizar_gui_con_datos, datos_mercado)

    def actualizar_gui_con_datos(self, datos_mercado):
        self.view.btn_update.config(state="normal", text="Actualizar Datos del Mercado")
        if datos_mercado is None:
            self.view.populate_list('fichar', [], is_loading=False, empty_text="Pulsa 'Actualizar'")
            self.view.populate_list('vender', [], is_loading=False, empty_text="Pulsa 'Actualizar'")
            return
        self.jugadores_para_fichar = datos_mercado.get('para_fichar', [])
        self.jugadores_para_vender = datos_mercado.get('para_vender', [])
        self.view.populate_list('fichar', self.jugadores_para_fichar)
        self.view.populate_list('vender', self.jugadores_para_vender)
        self.motores_calculo.clear()
        for jugador in self.jugadores_para_fichar + self.jugadores_para_vender:
            self.motores_calculo[jugador['nombre']] = MotorCalculo(jugador)
    
    def on_player_select(self, event, list_type):
        listbox = self.view.fichar_listbox if list_type == "fichar" else self.view.vender_listbox
        lista_jugadores = self.jugadores_para_fichar if list_type == "fichar" else self.jugadores_para_vender
        selected_indices = listbox.curselection()
        if not selected_indices: return
        nombre = listbox.get(selected_indices[0])
        jugador_data = next((p for p in lista_jugadores if p['nombre'] == nombre), None)
        if jugador_data:
            self.current_player_motor = self.motores_calculo.get(nombre)
            if not self.current_player_motor: return
            self.view.lbl_nombre.config(text=jugador_data['nombre'])
            self.view.lbl_valor.config(text=f"{jugador_data['valor']:,} €")
            self.view.lbl_incremento.config(text=f"{jugador_data['incremento']:,} € / día")
            dias_por_defecto = self.view.dias_var.get()
            puja_equilibrio = self.current_player_motor.encontrar_puja_equilibrio(dias_por_defecto)
            self.view.puja_var.set(puja_equilibrio)
            self.recalculate_results()

    def recalculate_results(self, event=None):
        if not self.current_player_motor: return
        try:
            mi_puja = self.view.puja_var.get()
            dias_limite = self.view.dias_var.get()
        except tk.TclError: return

        self.view.lbl_puja_formateada.config(text=f"({mi_puja:,})")
        resultados = self.current_player_motor.calcular_valoracion(mi_puja, dias_limite)
        
        # --- ¡CAMBIO CLAVE! IMPRIMIMOS LA TABLA DE CÁLCULO ---
        print("\n--- TABLA DE CÁLCULO GENERADA POR PYTHON ---")
        # Imprime la cabecera
        if resultados['tabla_calculo']:
            headers = resultados['tabla_calculo'][0].keys()
            print(" | ".join(f"{h:<25}" for h in headers))
            print("-" * 150)
            # Imprime las filas
            for row in resultados['tabla_calculo']:
                print(" | ".join(f"{str(v):<25}" for v in row.values()))
        print("--- FIN DE LA TABLA ---")
        
        probabilidad = resultados['probabilidad_beneficio']
        valor_apuesta = resultados['valor_apuesta']
        
        self.view.lbl_probabilidad.config(text=f"{probabilidad:.2%}")
        self.view.lbl_valor_apuesta.config(text=f"{int(valor_apuesta):,} €")
    
    def on_calculate_press(self):
        self.recalculate_results()

def main():
    root = tk.Tk()
    app = ValoracionController(root)
    root.mainloop()

if __name__ == '__main__':
    main()