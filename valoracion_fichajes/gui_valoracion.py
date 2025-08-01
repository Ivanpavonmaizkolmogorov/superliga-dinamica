import tkinter as tk
from tkinter import ttk
import locale

class VistaValoracion(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.master = master
        self.controller = controller
        self.master.title("Módulo de Valoración de Fichajes")
        self.master.geometry("1200x700")
        self.configure(bg="#f0f0f0")

        # --- Paneles Principales ---
        self.right_frame = tk.Frame(self, width=350)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        self.right_frame.pack_propagate(False)

        left_panel = tk.Frame(self)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.btn_update = ttk.Button(left_panel, text="Actualizar Datos del Mercado", command=self.controller.trigger_scrape)
        self.btn_update.pack(fill=tk.X, pady=(0, 10))

        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Pestaña FICHAR
        self.fichar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fichar_frame, text='Para Fichar')
        self.tree_fichar = self.crear_tabla(self.fichar_frame, "fichar")

        # Pestaña VENDER
        self.vender_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.vender_frame, text='Para Vender')
        self.tree_vender = self.crear_tabla(self.vender_frame, "vender")
        
        self.setup_details_panel()
        self.on_tab_changed(None)

    def on_tab_changed(self, event):
        """Muestra el panel de simulación correcto según la pestaña activa."""
        pestana_activa = self.notebook.tab(self.notebook.select(), "text")
        if pestana_activa == 'Para Fichar':
            self.vender_params_frame.pack_forget()
            self.fichar_params_frame.pack(fill=tk.X, pady=10)
        elif pestana_activa == 'Para Vender':
            self.fichar_params_frame.pack_forget()
            self.vender_params_frame.pack(fill=tk.X, pady=10)

    def crear_tabla(self, parent, tipo_tabla):
        """Crea un Treeview para mostrar los datos."""
        columnas = ("nombre", "valor", "inc", "puja", "dias", "em")
        if tipo_tabla == "vender":
            columnas = ("nombre", "valor", "inc", "oferta_maq", "ofertas_hoy", "dias", "em")

        tree = ttk.Treeview(parent, columns=columnas, show="headings")
        tree.bind('<<TreeviewSelect>>', lambda e, t=tipo_tabla: self.controller.on_player_select(e, t))
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        return tree

    def poblar_tabla(self, tipo_tabla, datos_tabla):
        """Rellena la tabla Treeview."""
        tree = self.tree_fichar if tipo_tabla == "fichar" else self.tree_vender
        
        for i in tree.get_children():
            tree.delete(i)
        
        tree["columns"] = datos_tabla['headers_id']
        for i, header_text in enumerate(datos_tabla['headers_display']):
            tree.heading(datos_tabla['headers_id'][i], text=header_text, anchor='w')
            ancho = 160 if i == 0 else (140 if i == (len(datos_tabla['headers_id']) - 1) else 80)
            tree.column(datos_tabla['headers_id'][i], width=ancho, anchor="w")

        for row in datos_tabla['data']:
            formatted_row = [row[0]] + [
                locale.format_string("%d", v, grouping=True) if isinstance(v, (int)) else f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                for v in row[1:]
            ]
            tree.insert("", "end", values=tuple(formatted_row), iid=row[0])

    def setup_details_panel(self):
        details_group = tk.LabelFrame(self.right_frame, text="Detalles del Jugador", padx=15, pady=10)
        details_group.pack(fill=tk.X, pady=10)
        self.lbl_nombre = self.create_detail_row(details_group, "Nombre:", 0)
        
        self.puja_var = tk.IntVar()
        self.dias_var = tk.IntVar(value=8)
        self.oferta_maquina_var = tk.IntVar()
        self.ofertas_hoy_var = tk.IntVar(value=1)

        self.fichar_params_frame = tk.LabelFrame(self.right_frame, text="Parámetros de Compra", padx=15, pady=10)
        self.create_spinbox_row(self.fichar_params_frame, "Mi Puja (€):", 0, self.puja_var, 0, 1e8, 10000)
        self.create_spinbox_row(self.fichar_params_frame, "Días Solares:", 1, self.dias_var, 2, 100, 1)

        self.vender_params_frame = tk.LabelFrame(self.right_frame, text="Parámetros de Venta", padx=15, pady=10)
        self.create_spinbox_row(self.vender_params_frame, "Oferta Máquina (€):", 0, self.oferta_maquina_var, 0, 1e8, 10000)
        self.create_spinbox_row(self.vender_params_frame, "Ofertas Hoy (0-2):", 1, self.ofertas_hoy_var, 0, 2, 1)
        self.create_spinbox_row(self.vender_params_frame, "Días Solares:", 2, self.dias_var, 2, 100, 1)
        
        res_group = tk.LabelFrame(self.right_frame, text="Resultado del Análisis", padx=15, pady=10)
        res_group.pack(fill=tk.X, pady=10)
        self.lbl_equilibrio_valor = self.create_detail_row(res_group, "Puja/Oferta de Equilibrio:", 0, font_size=10, bold=True, color="#00008B")
        self.lbl_valor_apuesta = self.create_detail_row(res_group, "Esperanza Matemática:", 1, font_size=12, bold=True, color="#006400")
        
    def create_spinbox_row(self, parent, label_text, row, variable, from_, to, increment):
        tk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", pady=5)
        spinbox = ttk.Spinbox(parent, from_=from_, to=to, increment=increment, textvariable=variable, command=self.controller.recalculate_results, width=15)
        spinbox.bind('<Return>', self.controller.recalculate_results)
        spinbox.grid(row=row, column=1, sticky="w", padx=5)

    def create_detail_row(self, parent, label_text, row, font_size=10, bold=False, color="black"):
        weight = "bold" if bold else "normal"
        tk.Label(parent, text=label_text, font=("Helvetica", font_size)).grid(row=row, column=0, sticky="w", pady=2)
        value_lbl = tk.Label(parent, text="-", font=("Helvetica", font_size, weight), fg=color)
        value_lbl.grid(row=row, column=1, sticky="w", padx=5)
        return value_lbl

    def set_active_panel(self, tipo_tabla):
        if tipo_tabla == "fichar":
            self.vender_params_frame.pack_forget()
            self.fichar_params_frame.pack(fill=tk.X, pady=10)
        else:
            self.fichar_params_frame.pack_forget()
            self.vender_params_frame.pack(fill=tk.X, pady=10)