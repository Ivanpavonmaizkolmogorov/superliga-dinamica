# superliga.py (Versión Final con Botón de Reporte Integrado)

import tkinter as tk
from tkinter import font, scrolledtext
import os
import sys
import threading
import subprocess
from gestor_datos import cargar_perfiles
import queue

# --- CLASE DE LA INTERFAZ GRÁFICA (VISTA) ---
# REEMPLAZA ESTA CLASE ENTERA en tu archivo superliga.py

class MainPanel(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.master = master
        self.controller = controller
        self.master.title("Panel de Administración - Superliga Dinámica")
        self.master.geometry("1000x600") # Hacemos la ventana más ancha
        self.master.configure(bg="#2c3e50")

        # --- Frame para los botones (panel izquierdo) ---
        control_frame = tk.Frame(self.master, bg="#34495e", padx=15, pady=20)
        control_frame.pack(side=tk.LEFT, fill=tk.Y) # Se ancla a la izquierda y ocupa toda la altura

        # --- Frame para la consola (panel derecho) ---
        log_frame = tk.Frame(self.master, bg="#2c3e50")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True) # Ocupa el resto del espacio

        # --- Creación de los botones ---
        button_font = font.Font(family="Helvetica", size=11, weight="bold")
        self.buttons = {}
        
        # Diccionario simplificado, ya no necesita filas/columnas
        button_data = {
            'crear_perfiles': ("1. Crear / Actualizar Perfiles", "#16a085"),
            'config_liga': ("2. Configuración de Liga", "#d35400"),
            'editar_perfiles': ("3. Editar Perfiles (Cronista)", "#3498db"),
            'formar_parejas': ("4. Formar Parejas", "#8e44ad"),
            'run_jornada': ("5. Procesar Nueva Jornada", "#2980b9"),
            'generar_reporte': ("6. Generar Reporte Semanal", "#f39c12"),
            'simular': ("Simular Jornada(s)", "#27ae60"),
                       # --- AÑADE ESTA LÍNEA ---
            'limpiar_declaraciones': ("Limpiar Declaraciones", "#95a5a6"),
            'reset_season': ("Reiniciar Temporada", "#e74c3c")
        }

        for key, (text, color) in button_data.items():
            btn = tk.Button(control_frame, text=text, font=button_font, bg=color, fg="white",
                             command=lambda k=key: self.controller.run_action(k))
            # Usamos pack para apilarlos verticalmente
            btn.pack(fill=tk.X, padx=5, pady=6) 
            self.buttons[key] = btn

        # --- Creación de la consola ---
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("Consolas", 10), bg="#ecf0f1", fg="#2c3e50")
        self.log_area.pack(expand=True, fill="both", padx=10, pady=10)
        
    def log_message(self, msg): 
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.master.update_idletasks()
    
    def set_all_buttons_state(self, state):
        for btn in self.buttons.values(): 
            btn.config(state=state)
        
    def update_button_states(self, app_state):
        self.set_all_buttons_state("normal")
        if not app_state['perfiles_exist']:
            self.buttons['run_jornada'].config(state="disabled")
            self.buttons['generar_reporte'].config(state="disabled")
            self.buttons['formar_parejas'].config(state="disabled")
            self.buttons['simular'].config(state="disabled")
            self.buttons['reset_season'].config(state="disabled")
            self.buttons['config_liga'].config(state="disabled")
            self.buttons['editar_perfiles'].config(state="disabled")
# --- CLASE CONTROLADORA (CEREBRO) ---
class SuperligaController:
    def __init__(self, root):
        self.root = root
        self.panel = MainPanel(root, self)
        self.python_executable = sys.executable
        self.update_app_state_and_buttons()
        self.panel.log_message("Panel de Control listo. Selecciona una acción.")

    def run_action(self, action_name):
        self.panel.set_all_buttons_state("disabled")
        self.panel.log_message(f"\n>>> Lanzando acción: '{action_name}'...")
        
        action_map = {
            'crear_perfiles': 'crear_perfiles.py',
            'run_jornada': 'procesar_jornada.py',
            'formar_parejas': 'formar_parejas.py',
            'simular': 'simulador.py',
            'config_liga': 'configurar_liga.py',
            'reset_season': 'reiniciar_temporada.py',
            'generar_reporte': 'generar_reporte.py', # <-- CONEXIÓN DEL NUEVO BOTÓN
            # --- AÑADE ESTA LÍNEA ---
            'limpiar_declaraciones': 'limpiar_declaraciones.py'
        }
        
        script_a_lanzar = action_map.get(action_name)
        
        if action_name == 'formar_parejas':
            thread = threading.Thread(target=self.accion_formar_parejas, daemon=True); thread.start()
            return
        if action_name == 'editar_perfiles':
            thread = threading.Thread(target=self.accion_editar_perfiles, daemon=True); thread.start()
            return

        if script_a_lanzar:
            thread = threading.Thread(target=self.run_script_in_subprocess, args=(script_a_lanzar,), daemon=True)
            thread.start()
        else:
            self.panel.log_message(f"Acción '{action_name}' no implementada.")
            self.update_app_state_and_buttons()

    # ## AÑADE ESTA NUEVA FUNCIÓN a la clase SuperligaController ##
    def accion_editar_perfiles(self):
        """Método especial para lanzar el editor de perfiles."""
        try:
            from editar_perfil import main as lanzar_editor_perfiles
            self.panel.log_message("    (Abriendo editor de perfiles...)")
            self.root.withdraw()  # Ocultamos la ventana principal
            lanzar_editor_perfiles()
            self.root.deiconify() # Mostramos la ventana principal de nuevo al cerrar
            self.panel.log_message("\n<<< Editor de perfiles cerrado.")
        except Exception as e:
            self.panel.log_message(f"ERROR al lanzar 'editar_perfil.py': {e}")
        finally:
            self.root.after(0, self.update_app_state_and_buttons)

    def run_script_in_subprocess(self, script_name):
        self.panel.log_message(f"    (Ejecutando script '{script_name}' en un nuevo proceso...)")
        try:
            subprocess.run([self.python_executable, script_name], check=True)
        except Exception as e: self.panel.log_message(f"ERROR al lanzar '{script_name}': {e}")
        finally: self.root.after(0, self.update_app_state_and_buttons)

    def update_app_state_and_buttons(self):
        app_state = {'perfiles_exist': os.path.exists('perfiles.json') and os.path.getsize('perfiles.json') > 2}
        self.panel.update_button_states(app_state)
        self.panel.set_all_buttons_state("normal")

    def accion_formar_parejas(self):
        """Método especial para la acción que lanza otra GUI."""
        try:
            from formar_parejas import main as lanzar_formador_parejas
            self.root.withdraw()
            lanzar_formador_parejas()
            self.root.deiconify()
            self.panel.log_message("\n<<< Asistente de Parejas cerrado.")
        except Exception as e: self.panel.log_message(f"ERROR: {e}")
        finally: self.root.after(0, self.update_app_state_and_buttons)

if __name__ == "__main__":
    import sys
    print("Lanzando Panel de Control de la Superliga Dinámica...")
    root = tk.Tk()
    app = SuperligaController(root)
    root.mainloop()
    print("\nAplicación cerrada.")