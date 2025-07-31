import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import locale
from .gui_valoracion import VistaValoracion
from .scraper_mercado import extraer_jugadores_mercado
from .motor_calculo import MotorCalculo

CACHE_FILE = 'valoracion_cache.json'

class ValoracionController:
    def __init__(self, root):
        self.root = root
        try:
            locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')
            except locale.Error:
                print("Advertencia: No se encontró la configuración regional española.")
        
        self.view = VistaValoracion(root, self)
        self.view.pack(expand=True, fill=tk.BOTH)
        self.jugadores_para_fichar = []
        self.jugadores_para_vender = []
        self.motores_calculo = {}
        self.current_player_motor = None
        self.load_data_from_cache()

    def load_data_from_cache(self):
        # (Sin cambios)
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
        # (Sin cambios)
        self.view.btn_update.config(state="disabled", text="Actualizando...")
        self.view.populate_list('fichar', [], is_loading=True)
        self.view.populate_list('vender', [], is_loading=True)
        thread = threading.Thread(target=self.scrape_and_save_to_cache, daemon=True)
        thread.start()

    def scrape_and_save_to_cache(self):
        # (Sin cambios)
        datos_mercado = extraer_jugadores_mercado()
        if datos_mercado:
            try:
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(datos_mercado, f, indent=2, ensure_ascii=False)
            except Exception: pass
        self.root.after(0, self.actualizar_gui_con_datos, datos_mercado)

    def actualizar_gui_con_datos(self, datos_mercado):
        # (Sin cambios)
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
            
            self.view.lbl_nombre.config(text=f"{jugador_data['nombre']}")
            self.view.lbl_valor.config(text=f"{locale.format_string('%d', jugador_data['valor'], grouping=True)} €")
            self.view.lbl_incremento.config(text=f"{locale.format_string('%d', jugador_data['incremento'], grouping=True)} € / día")
            
            # Establecer valores por defecto en los campos de simulación
            if list_type == 'fichar':
                 self.view.puja_var.set(jugador_data['valor'])
            elif list_type == 'vender':
                 self.view.oferta_maquina_var.set(jugador_data['valor'])
            
            self.recalculate_results()

    def recalculate_results(self, event=None):
        if not self.current_player_motor: return
        
        pestana_activa = self.view.notebook.tab(self.view.notebook.select(), "text")
        
        try:
            if pestana_activa == 'Para Fichar':
                mi_puja = self.view.puja_var.get()
                dias_limite = self.view.dias_var_fichar.get()
                self.view.lbl_puja_formateada.config(text=f"({locale.format_string('%d', mi_puja, grouping=True)})")
                
                config_usuario = {"puja_k": mi_puja, "dias_solares": dias_limite}
                resultados = self.current_player_motor.analizar_compra(config_usuario)

            elif pestana_activa == 'Para Vender':
                oferta_maq = self.view.oferta_maquina_var.get()
                ofertas_hoy = self.view.ofertas_hoy_var.get()
                dias_limite = self.view.dias_var_vender.get()
                self.view.lbl_oferta_formateada.config(text=f"({locale.format_string('%d', oferta_maq, grouping=True)})")

                config_usuario = {
                    "oferta_maquina": oferta_maq, 
                    "dias_solares": dias_limite,
                    "ofertas_hoy": ofertas_hoy
                }
                resultados = self.current_player_motor.analizar_venta(config_usuario)

            else:
                return # No hacer nada si no hay pestaña activa
        
        except tk.TclError:
            return # Evitar error si el campo está vacío

        # Actualizar la GUI con el resultado final
        esperanza = resultados['esperanza_matematica']
        self.view.lbl_valor_apuesta.config(text=f"{locale.format_string('%.2f', esperanza, grouping=True)} €")

def main():
    root = tk.Tk()
    app = ValoracionController(root)
    root.mainloop()

if __name__ == '__main__':
    main()