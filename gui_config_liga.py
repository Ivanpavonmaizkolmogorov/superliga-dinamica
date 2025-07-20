# gui_config_liga.py

import tkinter as tk
from tkinter import font

class ConfigLigaApp:
    def __init__(self, root, num_managers):
        self.root = root
        self.num_managers = num_managers
        self.config_guardada = None

        self.root.title("Configuración de Premios de la Liga")
        self.root.geometry("600x550")
        self.root.configure(bg="#f0f0f0")

        # --- Frame para la entrada de datos ---
        input_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        input_frame.pack(fill='x', padx=10)

        tk.Label(input_frame, text="Cuota por Mánager (€):", font=("Helvetica", 12), bg="#f0f0f0").pack(side='left', padx=5)
        self.cuota_entry = tk.Entry(input_frame, font=("Helvetica", 12), width=10)
        self.cuota_entry.pack(side='left', padx=5)
        self.cuota_entry.bind("<KeyRelease>", self.calcular_premios) # Llama a calcular al escribir

        tk.Label(input_frame, text=f"({self.num_managers} Mánagers)", font=("Helvetica", 10, "italic"), bg="#f0f0f0").pack(side='left', padx=5)

        # --- Frame para mostrar el desglose de premios ---
        self.premios_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        self.premios_frame.pack(fill='both', expand=True, padx=10)
        
        # --- Botón para guardar ---
        self.save_button = tk.Button(self.root, text="Guardar Configuración", font=("Helvetica", 12, "bold"), bg="#2ecc71", fg="white", command=self.guardar_config, state="disabled")
        self.save_button.pack(pady=15)

        # Calculamos con 0 al inicio
        self.calcular_premios()

    def calcular_premios(self, event=None):
        try:
            cuota = float(self.cuota_entry.get())
            if cuota < 0: cuota = 0
        except ValueError:
            cuota = 0
        
        bote_total = cuota * self.num_managers
        
        # Porcentajes calculados
        self.porcentajes = {
            "Pareja de Oro": 0.357, "Campeón Absoluto": 0.286, "Subcampeón": 0.107,
            "Ganador Sprint 1 (J1-10)": 0.029, "Ganador Sprint 2 (J11-20)": 0.043,
            "Ganador Sprint 3 (J21-30)": 0.071, "Ganador Sprint 4 (J31-38)": 0.107
        }

        # Limpiamos el frame antes de volver a dibujar
        for widget in self.premios_frame.winfo_children():
            widget.destroy()

        title_font = font.Font(family="Helvetica", size=14, weight="bold")
        tk.Label(self.premios_frame, text=f"Bote Total Estimado: {bote_total:.2f} €", font=title_font, bg="#f0f0f0").pack(anchor='center', pady=10)

        # Mostramos cada premio
        for nombre, pct in self.porcentajes.items():
            valor = bote_total * pct
            linea = f"{nombre} ({pct*100:.1f}%): {valor:.2f} €"
            tk.Label(self.premios_frame, text=linea, font=("Helvetica", 11), bg="#f0f0f0").pack(anchor='w', padx=20)
        
        # Habilitamos el botón de guardar solo si la cuota es válida
        if cuota > 0:
            self.save_button.config(state="normal")
        else:
            self.save_button.config(state="disabled")

    def guardar_config(self):
        self.config_guardada = {
            "cuota": float(self.cuota_entry.get()),
            "num_managers": self.num_managers,
            "bote_total": float(self.cuota_entry.get()) * self.num_managers,
            "premios_pct": self.porcentajes
        }
        self.root.quit()

def configurar_liga_gui(num_managers):
    root = tk.Tk()
    app = ConfigLigaApp(root, num_managers)
    root.mainloop()
    config = app.config_guardada
    root.destroy()
    return config