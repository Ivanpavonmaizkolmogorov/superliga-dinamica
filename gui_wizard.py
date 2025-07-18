# gui_wizard.py (Versión Completa, Final y Sincronizada)

import tkinter as tk
from tkinter import font, messagebox
import threading
import queue

class DraftWizardApp:
    def __init__(self, managers):
        # El constructor crea su propia ventana raíz (root)
        self.root = tk.Tk()
        self.root.title("Asistente de Draft - Superliga Dinámica")
        self.root.geometry("650x600")
        self.root.configure(bg="#f0f0f0")

        self.managers = list(managers)
        # Creamos un mapa de ID -> Nombre para usarlo fácilmente en el resumen
        self.manager_map = {m['id_manager']: m['nombre_mister'] for m in self.managers}
        
        # Variables de estado del proceso
        self.ranked_managers = []
        self.final_pairs = []
        self.capitanes = []
        self.elegibles = []
        self.current_captain_index = 0

        # Contenedor principal que cambiará de contenido para cada "página"
        self.container = tk.Frame(self.root, bg="#f0f0f0")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        # Lanzamos la primera página del asistente
        self.setup_ranking_page()

    def run(self):
        """Inicia el bucle principal de la GUI y devuelve el resultado al final."""
        self.root.mainloop()
        return self.final_pairs

    def clear_container(self):
        """Limpia el frame contenedor para mostrar una nueva página."""
        # Destruimos los widgets de botones de la raíz también por si acaso
        for widget in self.root.winfo_children():
            if widget != self.container:
                widget.destroy()
        for widget in self.container.winfo_children():
            widget.destroy()

    # --- PÁGINA 1: RANKING ---
    def setup_ranking_page(self):
        self.clear_container()
        posicion = len(self.ranked_managers) + 1
        
        title_font = font.Font(family="Helvetica", size=14, weight="bold")
        tk.Label(self.container, text=f"Paso 1: Asigna la {posicion}ª Posición", font=title_font, bg="#f0f0f0").pack(pady=20)

        unranked = [m for m in self.managers if m not in self.ranked_managers]
        for manager in unranked:
            tk.Button(self.container, text=manager['nombre_mister'], command=lambda m=manager: self.select_rank(m)).pack(pady=5, padx=20, fill='x')

    def select_rank(self, manager):
        self.ranked_managers.append(manager)
        if len(self.ranked_managers) == len(self.managers):
            self.prepare_draft()
        else:
            self.setup_ranking_page()

    # --- TRANSICIÓN A DRAFT ---
    def prepare_draft(self):
        mitad = len(self.ranked_managers) // 2
        self.capitanes = self.ranked_managers[:mitad]
        self.elegibles = self.ranked_managers[mitad:]
        self.setup_draft_page()

    # --- PÁGINA 2: DRAFT ---
    def setup_draft_page(self):
        self.clear_container()
        if self.current_captain_index >= len(self.capitanes) or not self.elegibles:
            self.setup_summary_page()
            return

        capitan = self.capitanes[self.current_captain_index]
        
        capitan_font = font.Font(family="Arial", size=16, weight="bold")
        tk.Label(self.container, text=f"Paso 2: Turno de {capitan['nombre_mister']}", font=capitan_font, bg="#f0f0f0").pack(pady=20)
        tk.Label(self.container, text="Selecciona una pareja:", bg="#f0f0f0").pack(pady=5)

        for manager in self.elegibles:
            tk.Button(self.container, text=manager['nombre_mister'], command=lambda c=capitan, e=manager: self.select_draft_pick(c, e)).pack(pady=5, padx=20, fill='x')

    def select_draft_pick(self, capitan, elegido):
        self.setup_loading_page(capitan, elegido)

    # --- PÁGINA 3: CARGA Y LLAMADA A IA ---
    def setup_loading_page(self, capitan, elegido):
        self.clear_container()
        loading_font = font.Font(family="Helvetica", size=14)
        tk.Label(self.container, text="Contactando al Cronista Virtual...", font=loading_font, bg="#f0f0f0").pack(pady=50)
        tk.Label(self.container, text="Bautizando al nuevo equipo...", bg="#f0f0f0").pack()
        self.root.update()
        
        self.resultado_queue = queue.Queue()
        self.thread_ia = threading.Thread(
            target=self.call_ia_in_thread, 
            args=([capitan, elegido], self.resultado_queue)
        )
        self.thread_ia.start()
        self.root.after(100, self.check_ia_thread, capitan, elegido)

    def call_ia_in_thread(self, perfiles_equipo, q):
        from cronista import generar_nombre_equipo_ia_thread
        generar_nombre_equipo_ia_thread(perfiles_equipo, q)

    def check_ia_thread(self, capitan, elegido):
        if self.thread_ia.is_alive():
            self.root.after(100, self.check_ia_thread, capitan, elegido)
        else:
            info_equipo_ia = self.resultado_queue.get()
            nombre_pareja = info_equipo_ia.get('nombre_equipo', 'Equipo Sin Nombre')
            justificacion_pareja = info_equipo_ia.get('justificacion', 'Sin justificación.')
            
            self.final_pairs.append({
                "nombre_pareja": nombre_pareja,
                "id_managers": [capitan['id_manager'], elegido['id_manager']],
                "justificacion": justificacion_pareja
            })

            self.elegibles.remove(elegido)
            self.current_captain_index += 1
            self.setup_draft_page()
            
    # --- PÁGINA 4: RESUMEN FINAL ---
    def setup_summary_page(self):
        self.clear_container()
        
        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        tk.Label(self.container, text="¡Draft Completado! Equipos Formados:", font=title_font, bg="#f0f0f0").pack(pady=15)

        canvas = tk.Canvas(self.container, bg="#f0f0f0", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        team_name_font = font.Font(family="Helvetica", size=12, weight="bold")
        members_font = font.Font(family="Helvetica", size=10)
        just_font = font.Font(family="Helvetica", size=9, slant="italic")

        for i, pair in enumerate(self.final_pairs):
            team_frame = tk.LabelFrame(scrollable_frame, text=f"Equipo {i+1}", padx=10, pady=10, bg="#e9e9e9")
            team_frame.pack(pady=8, padx=10, fill='x')

            tk.Label(team_frame, text=pair['nombre_pareja'], font=team_name_font, bg="#e9e9e9").pack(anchor='w')
            
            nombres_miembros = " y ".join([self.manager_map[mid] for mid in pair['id_managers']])
            tk.Label(team_frame, text=f"Miembros: {nombres_miembros}", font=members_font, bg="#e9e9e9").pack(anchor='w')
            
            tk.Label(team_frame, text=f"Justificación: \"{pair['justificacion']}\"", font=just_font, wraplength=500, justify="left", bg="#e9e9e9").pack(anchor='w')
        
        # Frame para los botones de acción finales, fuera del área de scroll
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=10)
        
        copy_button = tk.Button(button_frame, text="Copiar para WhatsApp", command=lambda: self.copy_summary_to_clipboard(copy_button), font=("Helvetica", 11), bg="#3498db", fg="white")
        copy_button.pack(side="left", padx=10)

        finish_button = tk.Button(button_frame, text="Finalizar y Guardar", command=self.root.quit, font=("Helvetica", 11, "bold"), bg="#2ecc71", fg="white")
        finish_button.pack(side="left", padx=10)

    def format_summary_for_whatsapp(self):
        lines = ["🏆 *¡Equipos Finales del Draft de la Superliga!* 🏆\n"]
        for pair in self.final_pairs:
            lines.append(f"*{pair['nombre_pareja']}*")
            nombres_miembros = " y ".join([self.manager_map[mid] for mid in pair['id_managers']])
            lines.append(f"Miembros: {nombres_miembros}")
            lines.append(f"_{pair['justificacion']}_")
            lines.append("")
        return "\n".join(lines)

    def copy_summary_to_clipboard(self, button):
        summary_text = self.format_summary_for_whatsapp()
        self.root.clipboard_clear()
        self.root.clipboard_append(summary_text)
        original_text = button.cget("text"); original_bg = button.cget("bg")
        button.config(text="¡Copiado!", bg="#16a085", state="disabled")
        self.root.after(2000, lambda: button.config(text=original_text, bg=original_bg, state="normal"))