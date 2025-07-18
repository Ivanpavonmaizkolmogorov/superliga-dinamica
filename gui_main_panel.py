# gui_main_panel.py (Versión Final con UX Mejorada)

import tkinter as tk
from tkinter import font, scrolledtext

# --- Clase para crear Tooltips (pequeños textos de ayuda) ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, background="#FFFFE0", relief="solid", borderwidth=1, font=("Arial", 10))
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = None


class MainPanelApp:
    def __init__(self, root, app_state):
        self.root = root
        self.root.title("Panel de Administración - Superliga Dinámica")
        self.root.geometry("800x650")
        self.root.configure(bg="#2c3e50")

        self.on_run_jornada, self.on_formar_parejas, self.on_simular, self.on_ver_premios, self.on_config_liga, self.on_reset_season = [None]*6

        # --- Frame Principal ---
        control_frame = tk.Frame(root, bg="#34495e", padx=20, pady=20)
        control_frame.pack(side="top", fill="x")
        
        button_font = font.Font(family="Helvetica", size=12, weight="bold")
        
        # --- NUEVO ORDEN LÓGICO DE BOTONES ---
        # Fila 1: Acciones Principales y de Configuración
        self.btn_run_jornada = tk.Button(control_frame, text="Procesar Jornada", command=self.run_jornada_action, font=button_font, bg="#2980b9", fg="white", height=2)
        self.btn_run_jornada.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ToolTip(self.btn_run_jornada, "Escanea la web de Mister para crear/actualizar perfiles y jornadas.")

        self.btn_config_liga = tk.Button(control_frame, text="Configuración de Liga", command=self.run_config_liga_action, font=button_font, bg="#d35400", fg="white", height=2)
        self.btn_config_liga.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ToolTip(self.btn_config_liga, "Define la cuota y el reparto de premios. (Configurar una vez por temporada)")

        # Fila 2: Herramientas de Temporada
        self.btn_formar_parejas = tk.Button(control_frame, text="Formar Parejas", command=self.run_formar_parejas_action, font=button_font, bg="#8e44ad", fg="white", height=2)
        self.btn_formar_parejas.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ToolTip(self.btn_formar_parejas, "Lanza el asistente de Draft para crear los equipos. (Usar una vez por temporada)")

        self.btn_ver_premios = tk.Button(control_frame, text="Ver Estado de Premios", command=self.run_ver_premios_action, font=button_font, bg="#f39c12", fg="white", height=2)
        self.btn_ver_premios.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ToolTip(self.btn_ver_premios, "Muestra el estado actual de los premios según la última jornada procesada.")
        
        # Fila 3: Herramientas de Prueba y Peligrosas
        self.btn_simular = tk.Button(control_frame, text="Simular Jornada(s)", command=self.run_simular_action, font=button_font, bg="#27ae60", fg="white", height=2)
        self.btn_simular.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        ToolTip(self.btn_simular, "Avanza la temporada con datos falsos para hacer pruebas.")

        self.btn_reset_season = tk.Button(control_frame, text="Reiniciar Temporada", command=self.run_reset_season_action, font=button_font, bg="#e74c3c", fg="white", height=2)
        self.btn_reset_season.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ToolTip(self.btn_reset_season, "¡CUIDADO! Borra el historial de la temporada y las parejas.")

        control_frame.grid_columnconfigure(0, weight=1); control_frame.grid_columnconfigure(1, weight=1)

        # Área de logs
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10), bg="#ecf0f1", fg="#2c3e50")
        self.log_area.pack(expand=True, fill="both", padx=10, pady=10)
        
        # --- Lógica de Estado Inicial ---
        self.update_button_states(app_state)
        if not app_state['perfiles_exist']:
            self.log_message("¡Bienvenido! No se ha encontrado 'perfiles.json'.\nPulsa 'Procesar Jornada' para inicializar el sistema.")
        else:
            self.log_message("Bienvenido al Panel de Administración.")

    def update_button_states(self, app_state):
        """Activa o desactiva los botones según el estado de la aplicación."""
        # El botón de procesar jornada siempre está activo
        self.btn_run_jornada.config(state="normal")
        
        # El resto de botones dependen de si los perfiles existen
        state_if_profiles_exist = "normal" if app_state['perfiles_exist'] else "disabled"
        self.btn_config_liga.config(state=state_if_profiles_exist)
        self.btn_formar_parejas.config(state=state_if_profiles_exist)
        self.btn_simular.config(state=state_if_profiles_exist)
        self.btn_reset_season.config(state=state_if_profiles_exist)

        # El botón de ver premios necesita perfiles Y configuración
        state_ver_premios = "normal" if app_state['perfiles_exist'] and app_state['config_exist'] else "disabled"
        self.btn_ver_premios.config(state=state_ver_premios)
        
    def log_message(self, msg):
        self.log_area.insert(tk.END, msg + "\n"); self.log_area.see(tk.END); self.root.update_idletasks()

    def set_all_buttons_state(self, state):
        self.btn_run_jornada.config(state=state); self.btn_formar_parejas.config(state=state)
        self.btn_simular.config(state=state); self.btn_ver_premios.config(state=state)
        self.btn_config_liga.config(state=state); self.btn_reset_season.config(state=state)

    def run_jornada_action(self):
        if self.on_run_jornada: self.set_all_buttons_state("disabled"); self.on_run_jornada()
    def run_formar_parejas_action(self):
        if self.on_formar_parejas: self.set_all_buttons_state("disabled"); self.on_formar_parejas()
    def run_simular_action(self):
        if self.on_simular: self.set_all_buttons_state("disabled"); self.on_simular()
    def run_ver_premios_action(self):
        if self.on_ver_premios: self.set_all_buttons_state("disabled"); self.on_ver_premios()
    def run_config_liga_action(self):
        if self.on_config_liga: self.set_all_buttons_state("disabled"); self.on_config_liga()
    def run_reset_season_action(self):
        if self.on_reset_season: self.set_all_buttons_state("disabled"); self.on_reset_season()