import tkinter as tk
from tkinter import ttk, font
import locale

class VistaValoracion(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.master = master
        self.controller = controller
        self.master.title("Módulo de Valoración de Fichajes")
        self.master.geometry("850x650")
        self.configure(bg="#f0f0f0")

        # --- Paneles Principales ---
        right_frame = tk.Frame(self, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        right_frame.pack_propagate(False)

        left_panel = tk.Frame(self)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Pestaña FICHAR
        self.fichar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fichar_frame, text='Para Fichar')
        self.lbl_loading_fichar, self.fichar_listbox = self.setup_list_panel(self.fichar_frame, "fichar")

        # Pestaña VENDER
        self.vender_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.vender_frame, text='Para Vender')
        self.lbl_loading_vender, self.vender_listbox = self.setup_list_panel(self.vender_frame, "vender")

        # --- Panel de Detalles (Derecha) ---
        self.setup_details_panel(right_frame)
        self.on_tab_changed(None) # Forzar el estado inicial correcto

    def on_tab_changed(self, event):
        """Muestra el panel de simulación correcto según la pestaña activa."""
        pestana_activa = self.notebook.tab(self.notebook.select(), "text")
        if pestana_activa == 'Para Fichar':
            self.sim_group_vender.pack_forget()
            self.sim_group_fichar.pack(fill=tk.X, pady=10)
        elif pestana_activa == 'Para Vender':
            self.sim_group_fichar.pack_forget()
            self.sim_group_vender.pack(fill=tk.X, pady=10)

    def setup_list_panel(self, parent, list_type):
        loading_label = tk.Label(parent, text="Cargando...", font=("Helvetica", 10, "italic"))
        listbox = tk.Listbox(parent, font=("Arial", 11))
        listbox.bind('<<ListboxSelect>>', lambda e, t=list_type: self.controller.on_player_select(e, t))
        return loading_label, listbox

    def populate_list(self, list_type, players, is_loading=False, empty_text="No hay jugadores"):
        listbox = self.fichar_listbox if list_type == "fichar" else self.vender_listbox
        loading_label = self.lbl_loading_fichar if list_type == "fichar" else self.lbl_loading_vender
        
        listbox.pack_forget()
        loading_label.pack_forget()

        if is_loading:
            loading_label.config(text="Cargando jugadores...")
            loading_label.pack(pady=20, expand=True)
        elif players:
            listbox.delete(0, tk.END)
            for player in players:
                listbox.insert(tk.END, player['nombre'])
            listbox.pack(expand=True, fill=tk.BOTH)
        else:
            loading_label.config(text=empty_text)
            loading_label.pack(pady=20, expand=True)

    def setup_details_panel(self, parent):
        # Frame de Actualización
        update_frame = tk.Frame(parent)
        update_frame.pack(fill=tk.X, pady=(5, 10))
        self.btn_update = ttk.Button(update_frame, text="Actualizar Datos del Mercado", command=self.controller.trigger_scrape)
        self.btn_update.pack(fill=tk.X)
        
        # Frame de Detalles del Jugador
        details_group = tk.LabelFrame(parent, text="Detalles del Jugador", font=("Helvetica", 11, "bold"), padx=15, pady=10)
        details_group.pack(fill=tk.X, pady=10)
        self.lbl_nombre = self.create_detail_row(details_group, "Nombre:", 0)
        self.lbl_valor = self.create_detail_row(details_group, "Valor Actual:", 1)
        self.lbl_incremento = self.create_detail_row(details_group, "Incremento Diario:", 2)

        # --- Paneles de Simulación Separados ---
        self.sim_group_fichar = tk.LabelFrame(parent, text="Simulación de Compra", font=("Helvetica", 11, "bold"), padx=15, pady=10)
        self.sim_group_vender = tk.LabelFrame(parent, text="Simulación de Venta", font=("Helvetica", 11, "bold"), padx=15, pady=10)
        
        # --- Variables de control ---
        self.puja_var = tk.IntVar()
        self.dias_var_fichar = tk.IntVar(value=8)
        self.dias_var_vender = tk.IntVar(value=8)
        self.oferta_maquina_var = tk.IntVar()
        self.ofertas_hoy_var = tk.IntVar(value=1) # Por defecto, queda 1 oferta

        # --- Contenido del panel de FICHAR ---
        self.create_spinbox_row(self.sim_group_fichar, "Mi Puja (€):", 0, self.puja_var, 0, 100000000, 10000)
        self.create_spinbox_row(self.sim_group_fichar, "Días Solares:", 1, self.dias_var_fichar, 2, 100, 1)
        self.lbl_puja_formateada = tk.Label(self.sim_group_fichar, text="", font=("Arial", 9, "italic"), fg="gray")
        self.lbl_puja_formateada.grid(row=0, column=2, sticky="w", padx=5)
        ttk.Button(self.sim_group_fichar, text="Calcular Compra", command=self.controller.recalculate_results).grid(row=2, column=0, columnspan=2, pady=10)

        # --- Contenido del panel de VENDER ---
        self.create_spinbox_row(self.sim_group_vender, "Oferta Máquina (€):", 0, self.oferta_maquina_var, 0, 100000000, 10000)
        self.create_spinbox_row(self.sim_group_vender, "Ofertas Hoy (0-2):", 1, self.ofertas_hoy_var, 0, 2, 1)
        self.create_spinbox_row(self.sim_group_vender, "Días Solares:", 2, self.dias_var_vender, 2, 100, 1)
        self.lbl_oferta_formateada = tk.Label(self.sim_group_vender, text="", font=("Arial", 9, "italic"), fg="gray")
        self.lbl_oferta_formateada.grid(row=0, column=2, sticky="w", padx=5)
        ttk.Button(self.sim_group_vender, text="Calcular Venta", command=self.controller.recalculate_results).grid(row=3, column=0, columnspan=2, pady=10)

        # --- Panel de Resultados (común) ---
        res_group = tk.LabelFrame(parent, text="Resultados de la Valoración", font=("Helvetica", 11, "bold"), padx=15, pady=10)
        res_group.pack(fill=tk.X, pady=10)
        self.lbl_valor_apuesta = self.create_detail_row(res_group, "Esperanza Matemática:", 0, font_size=12, bold=True, color="#00008B")

    def create_spinbox_row(self, parent, label_text, row, variable, from_, to, increment):
        tk.Label(parent, text=label_text, font=("Helvetica", 10)).grid(row=row, column=0, sticky="w", pady=5)
        spinbox = ttk.Spinbox(parent, from_=from_, to=to, increment=increment, textvariable=variable, command=self.controller.recalculate_results, width=18, font=("Arial", 10))
        spinbox.bind('<Return>', self.controller.recalculate_results)
        spinbox.grid(row=row, column=1, sticky="w", padx=5)

    def create_detail_row(self, parent, label_text, row, font_size=10, bold=False, color="black"):
        weight = "bold" if bold else "normal"
        tk.Label(parent, text=label_text, font=("Helvetica", font_size)).grid(row=row, column=0, sticky="w", pady=2)
        value_lbl = tk.Label(parent, text="-", font=("Helvetica", font_size, weight), fg=color)
        value_lbl.grid(row=row, column=1, sticky="w", padx=5)
        return value_lbl