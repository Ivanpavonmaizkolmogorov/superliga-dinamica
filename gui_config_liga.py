# gui_config_liga.py
import tkinter as tk
from tkinter import font, messagebox
import json

class ConfigLigaApp:
    def __init__(self, root, current_config):
        self.root = root
        self.result_config = None # Aquí guardaremos la nueva configuración

        self.root.title("Configuración de la Liga")
        self.root.geometry("450x500")
        self.root.configure(bg="#f0f0f0")
        
        main_frame = tk.Frame(root, padx=20, pady=20, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True)

        title_font = font.Font(family="Helvetica", size=14, weight="bold")
        label_font = font.Font(family="Helvetica", size=11)
        
        # --- Campo para la Cuota de Inscripción ---
        tk.Label(main_frame, text="Cuota de Inscripción por Mánager (€):", font=label_font, bg="#f0f0f0").pack(anchor="w", pady=(0, 5))
        self.cuota_var = tk.DoubleVar(value=current_config.get('cuota_inscripcion', 0.0))
        tk.Entry(main_frame, textvariable=self.cuota_var, font=label_font).pack(fill="x", pady=(0, 15))

        # --- Campos para los Porcentajes de Premios ---
        tk.Label(main_frame, text="Reparto de Premios (%):", font=title_font, bg="#f0f0f0").pack(anchor="w", pady=(10, 5))
        
        self.vars_premios = {}
        premios = current_config.get('reparto_premios_porcentaje', {})
        
        for key, name in [
            ("1_clasificado_general", "1º Clasificado General"),
            ("pareja_ganadora", "Pareja Ganadora"),
            ("2_clasificado_general", "2º Clasificado General"),
            ("mejor_2_vuelta", "Mejor de la 2ª Vuelta"),
            ("campeon_invierno", "Campeón de Invierno")
        ]:
            frame = tk.Frame(main_frame, bg="#f0f0f0")
            frame.pack(fill="x", pady=4)
            tk.Label(frame, text=f"{name}:", font=label_font, bg="#f0f0f0", width=22, anchor="w").pack(side="left")
            var = tk.IntVar(value=premios.get(key, 0))
            self.vars_premios[key] = var
            tk.Entry(frame, textvariable=var, font=label_font, width=5).pack(side="left")
            tk.Label(frame, text="%", font=label_font, bg="#f0f0f0").pack(side="left", padx=5)

        # --- Botón de Guardar ---
        save_button = tk.Button(main_frame, text="Guardar Configuración", command=self.save_config, font=("Helvetica", 12, "bold"), bg="#2ecc71", fg="white")
        save_button.pack(pady=20)
        
    def save_config(self):
        """Valida los datos y guarda la configuración."""
        # Validación: la suma de porcentajes debe ser 100
        total_porcentaje = sum(var.get() for var in self.vars_premios.values())
        if total_porcentaje != 100:
            messagebox.showerror("Error de Validación", f"La suma de los porcentajes de los premios debe ser 100, pero actualmente es {total_porcentaje}%.")
            return

        # Si la validación es correcta, construimos el diccionario de configuración
        self.result_config = {
            "cuota_inscripcion": self.cuota_var.get(),
            "reparto_premios_porcentaje": {key: var.get() for key, var in self.vars_premios.items()}
        }
        
        self.root.quit()

def launch_config_window(current_config):
    """Lanza la ventana de configuración y devuelve la nueva configuración."""
    root = tk.Tk()
    app = ConfigLigaApp(root, current_config)
    root.mainloop()
    
    new_config = app.result_config
    root.destroy()
    return new_config