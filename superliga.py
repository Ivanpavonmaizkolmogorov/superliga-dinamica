# superliga.py (Versión Final con Errata Corregida)

import tkinter as tk
from tkinter import font, scrolledtext
import os
import threading
import queue
from gestor_datos import cargar_perfiles, guardar_perfiles
from scraper import extraer_datos_mister

# --- CLASE DE LA INTERFAZ GRÁFICA (VISTA) ---
class MainPanel(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.master = master
        self.controller = controller
        
        self.master.title("Panel de Administración - Superliga Dinámica")
        self.master.geometry("800x650")
        self.master.configure(bg="#2c3e50")

        control_frame = tk.Frame(self.master, bg="#34495e", padx=20, pady=20)
        control_frame.pack(side="top", fill="x")
        
        button_font = font.Font(family="Helvetica", size=12, weight="bold")
        
        self.buttons = {}
        button_data = {
            'crear_perfiles': ("Crear / Actualizar Perfiles", "#16a085", 0, 0),
            'run_jornada': ("Procesar Nueva Jornada", "#2980b9", 0, 1),
            'formar_parejas': ("Formar Parejas", "#8e44ad", 1, 0),
            'config_liga': ("Configuración de Liga", "#d35400", 1, 1),
            'simular': ("Simular Jornada(s)", "#27ae60", 2, 0),
            'reset_season': ("Reiniciar Temporada", "#e74c3c", 2, 1)
        }

        for key, (text, color, row, col) in button_data.items():
            btn = tk.Button(control_frame, text=text, font=button_font, bg=color, fg="white", height=2,
                            command=lambda k=key: self.controller.run_action(k))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            self.buttons[key] = btn

        # --- LÍNEA CORREGIDA ---
        control_frame.grid_columnconfigure(0, weight=1); control_frame.grid_columnconfigure(1, weight=1)
        
        self.log_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, font=("Consolas", 10), bg="#ecf0f1", fg="#2c3e50")
        self.log_area.pack(expand=True, fill="both", padx=10, pady=10)

    def log_message(self, msg):
        self.log_area.insert(tk.END, msg + "\n"); self.log_area.see(tk.END); self.master.update_idletasks()

    def set_all_buttons_state(self, state):
        for btn in self.buttons.values(): btn.config(state=state)

    def update_button_states(self, app_state):
        self.set_all_buttons_state("normal")
        if not app_state['perfiles_exist']:
            self.buttons['run_jornada'].config(state="disabled"); self.buttons['formar_parejas'].config(state="disabled")
            self.buttons['simular'].config(state="disabled"); self.buttons['reset_season'].config(state="disabled")
            self.buttons['config_liga'].config(state="disabled")

# --- CLASE CONTROLADORA (CEREBRO) ---
class SuperligaController:
    def __init__(self, root):
        self.root = root
        self.panel = MainPanel(root, self)
        self.update_app_state_and_buttons()
        self.panel.log_message("Panel de Control listo. Selecciona una acción.")
        if not os.path.exists('perfiles.json') or os.path.getsize('perfiles.json') <= 2:
            self.panel.log_message("¡Bienvenido! Pulsa 'Crear / Actualizar Perfiles' para inicializar.")

    def run_action(self, action_name):
        self.panel.set_all_buttons_state("disabled")
        action_map = {
            'crear_perfiles': self.accion_crear_perfiles,
            'formar_parejas': self.accion_formar_parejas,
            'run_jornada': lambda q: (self.panel.log_message("\n>>> 'Procesar Jornada' no implementado."), q.put("done")),
            'simular': lambda q: (self.panel.log_message("\n>>> 'Simular' no implementado."), q.put("done")),
            'config_liga': lambda q: (self.panel.log_message("\n>>> 'Config Liga' no implementado."), q.put("done")),
            'reset_season': lambda q: (self.panel.log_message("\n>>> 'Reset' no implementado."), q.put("done"))
        }
        if action_name in action_map:
            action_function = action_map[action_name]
            q = queue.Queue()
            thread = threading.Thread(target=action_function, args=(q,), daemon=True)
            thread.start()
            self.root.after(100, lambda: self.check_thread_completion(q))
        else:
            self.panel.log_message(f"Acción '{action_name}' desconocida.")
            self.update_app_state_and_buttons()

    def update_app_state_and_buttons(self):
        app_state = {'perfiles_exist': os.path.exists('perfiles.json') and os.path.getsize('perfiles.json') > 2}
        self.panel.update_button_states(app_state)

    def check_thread_completion(self, q):
        try:
            if q.get(block=False) == "done":
                self.panel.log_message("<<< Tarea finalizada.")
                self.update_app_state_and_buttons()
        except queue.Empty:
            self.root.after(100, lambda: self.check_thread_completion(q))

    # --- LÓGICA DE LAS ACCIONES ---
    def accion_crear_perfiles(self, q):
        self.panel.log_message("\n>>> INICIANDO CREACIÓN/ACTUALIZACIÓN DE PERFILES...")
        try:
            self.panel.log_message("Cargando perfiles existentes...")
            perfiles = cargar_perfiles(); manager_ids_existentes = {p['id_manager'] for p in perfiles}
            self.panel.log_message("Contactando con Mister...")
            datos_web = extraer_datos_mister()
            if datos_web is None: self.panel.log_message("ERROR: El scraping ha fallado.")
            elif not datos_web: self.panel.log_message("INFO: La liga no tiene mánagers todavía.")
            else:
                self.panel.log_message(f"-> {len(datos_web)} mánagers encontrados. Sincronizando...")
                nuevos_managers_count, perfiles_actualizados = 0, False
                for dw in datos_web:
                    if dw['id_manager'] not in manager_ids_existentes:
                        nuevos_managers_count += 1; perfiles_actualizados = True
                        self.panel.log_message(f"   - Nuevo mánager: '{dw['nombre_mister']}'.")
                        perfiles.append({"id_manager": dw['id_manager'], "nombre_mister": dw['nombre_mister'], "apodo_lema": "El Novato", "historial_temporada": []})
                if perfiles_actualizados:
                    guardar_perfiles(perfiles)
                    self.panel.log_message(f"-> ¡Perfiles guardados! Se añadieron {nuevos_managers_count} mánager(s).")
                else: self.panel.log_message("-> Los perfiles ya están al día.")
                self.panel.log_message("\n¡SINCRONIZACIÓN COMPLETADA!")
        except Exception as e: self.panel.log_message(f"\nERROR INESPERADO: {e}")
        finally: q.put("done")

    def accion_formar_parejas(self, q):
        self.panel.log_message("\n>>> Lanzando Asistente de Formación de Parejas...")
        try:
            from formar_parejas import main as lanzar_formador_parejas
            self.root.withdraw()
            lanzar_formador_parejas()
            self.root.deiconify()
            self.panel.log_message("\n<<< Asistente de Parejas cerrado.")
        except Exception as e: self.panel.log_message(f"\nERROR: {e}")
        finally: q.put("done")

if __name__ == "__main__":
    print("Lanzando Panel de Control de la Superliga Dinámica...")
    root = tk.Tk()
    app = SuperligaController(root)
    root.mainloop()
    print("\nAplicación cerrada.")