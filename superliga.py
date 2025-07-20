# superliga.py (Versión Final con Caso Especial para formar_parejas)

import tkinter as tk
from tkinter import font, scrolledtext
import os
import sys
import threading
import subprocess
from gestor_datos import cargar_perfiles, guardar_perfiles

# --- CLASE DE LA INTERFAZ GRÁFICA (VISTA) ---
class MainPanel(tk.Frame):
    # ... (El código de la clase MainPanel no cambia en absoluto) ...
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
            btn = tk.Button(control_frame, text=text, font=button_font, bg=color, fg="white", height=2, command=lambda k=key: self.controller.run_action(k))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            self.buttons[key] = btn
        control_frame.grid_columnconfigure(0, weight=1); control_frame.grid_columnconfigure(1, weight=1)
        self.log_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, font=("Consolas", 10), bg="#ecf0f1", fg="#2c3e50")
        self.log_area.pack(expand=True, fill="both", padx=10, pady=10)
    def log_message(self, msg): self.log_area.insert(tk.END, msg + "\n"); self.log_area.see(tk.END); self.master.update_idletasks()
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
        self.python_executable = sys.executable
        self.update_app_state_and_buttons()
        self.panel.log_message("Panel de Control listo. Selecciona una acción.")
# Dentro de la clase SuperligaController en superliga.py

    def accion_reset_temporada(self):
        self.panel.log_message("\n>>> Lanzando Asistente de Reinicio de Temporada...")
        self.run_script_in_subprocess('reiniciar_temporada.py')

# Dentro de la clase SuperligaController en superliga.py

    def run_action(self, action_name):
        self.panel.set_all_buttons_state("disabled")
        self.panel.log_message(f"\n>>> Lanzando acción: '{action_name}'...")
        self.panel.log_message("    (Revisa la consola principal para ver el progreso)")
        
        # --- ¡ESTA ES LA CORRECCIÓN! ---
        # Añadimos la acción 'reset_season' al mapa.
        action_map = {
            'crear_perfiles': 'crear_perfiles.py',
            'run_jornada': 'procesar_jornada.py',
            'formar_parejas': 'formar_parejas.py',
            'simular': 'simulador.py',
            'reset_season': 'reiniciar_temporada.py' # <-- AÑADIR ESTA LÍNEA
            # 'config_liga' lo dejaremos para el final
        }
        
        script_a_lanzar = action_map.get(action_name)
        
        if script_a_lanzar:
            # La lógica para lanzar el script en un hilo ya es correcta
            thread = threading.Thread(target=self.run_script_in_subprocess, args=(script_a_lanzar,), daemon=True)
            thread.start()
        else:
            self.panel.log_message(f"Acción '{action_name}' no implementada.")
            self.update_app_state_and_buttons()

    def run_script_in_subprocess(self, script_name):
        self.panel.log_message(f"    (Ejecutando script '{script_name}' en un nuevo proceso...)")
        try:
            subprocess.run([self.python_executable, script_name], check=True)
        except Exception as e:
            self.panel.log_message(f"ERROR al lanzar '{script_name}': {e}")
        finally:
            self.root.after(0, self.update_app_state_and_buttons)

    def update_app_state_and_buttons(self):
        app_state = {'perfiles_exist': os.path.exists('perfiles.json') and os.path.getsize('perfiles.json') > 2}
        self.panel.update_button_states(app_state)
        self.panel.set_all_buttons_state("normal")

    # --- LÓGICA DE LAS ACCIONES ---
    def accion_formar_parejas(self):
        """Método especial para la acción que lanza otra GUI."""
        try:
            from formar_parejas import main as lanzar_formador_parejas
            self.root.withdraw() # Ocultamos el panel principal
            lanzar_formador_parejas()
            self.root.deiconify() # Lo volvemos a mostrar
            self.panel.log_message("\n<<< Asistente de Parejas cerrado.")
        except Exception as e:
            self.panel.log_message(f"ERROR: {e}")
        finally:
            self.root.after(0, self.update_app_state_and_buttons)

if __name__ == "__main__":
    import sys
    print("Lanzando Panel de Control de la Superliga Dinámica...")
    root = tk.Tk()
    app = SuperligaController(root)
    root.mainloop()
    print("\nAplicación cerrada.")