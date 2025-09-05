import tkinter as tk
from tkinter import messagebox, font
import threading
import json
import os
import locale
import queue # <-- CAMBIO: Necesario para comunicar hilos

# Se mantienen las importaciones de tu proyecto
from .gui_valoracion import VistaValoracion
from .motor_calculo import MotorCalculo
from .scraper_ofertas_recibidas import extraer_ofertas_maquina
from .scraper_mercado import extraer_jugadores_mercado
from .bot_pujas import realizar_pujas

CACHE_FILE = 'valoracion_cache.json'

class ValoracionController:
    # --- TU CLASE CONTROLLER SE QUEDA EXACTAMENTE IGUAL ---
    # No es necesario pegar aquí todo el código, solo asegúrate de que
    # tu clase ValoracionController (la que ya tienes) esté aquí.
    # El único cambio que haremos será en la función main() de abajo.
    def __init__(self, root):
        self.root = root
        try:
            locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        except locale.Error:
            try: locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')
            except locale.Error: print("Advertencia: No se encontró la configuración regional española.")
        
        self.view = VistaValoracion(root, self)
        self.view.pack(expand=True, fill=tk.BOTH)
        self.jugadores_mercado = {}
        self.motores_calculo = {}
        self.current_player = None
        self.current_type = None
        
        self.datos_originales_fichar = []
        self.datos_originales_vender = []
        self.sort_state = {}
        
        # <-- CAMBIO: Ya no llamamos a load_data_from_cache() aquí.
        # Los datos se pasarán desde fuera después de la carga inicial.

    def initialize_with_data(self, data):
        """
        <-- CAMBIO: Nueva función para iniciar el controlador con datos ya cargados.
        """
        if data:
            self.jugadores_mercado = data
            self.preparar_y_poblar_tablas()
        else:
            messagebox.showinfo("Caché Vacío", "No se encontraron datos. Pulsa 'Actualizar' para cargar la información del mercado.")

    def trigger_fetch_machine_offer(self):
        """Lanza el scraper de ofertas recibidas para todos los jugadores."""
        self.view.btn_get_offer.config(state="disabled", text="Buscando...")
        threading.Thread(target=self.fetch_and_update_all_offers, daemon=True).start()

    def fetch_and_update_all_offers(self):
        """Ejecuta el scraper y pasa los resultados a la función de actualización."""
        ofertas = extraer_ofertas_maquina()
        self.root.after(0, self.on_fetch_all_offers_complete, ofertas)

    def on_fetch_all_offers_complete(self, ofertas):
        """
        Recibe todas las ofertas, actualiza los datos en memoria, recalcula
        y refresca la tabla de venta por completo.
        """
        self.view.btn_get_offer.config(state="normal", text="Actualizar Ofertas de la Máquina para TODOS")
        if ofertas is None:
            messagebox.showerror("Error", "No se pudieron obtener las ofertas de la máquina.")
            return
        if not ofertas:
            messagebox.showinfo("Info", "No se encontraron nuevas ofertas de la máquina.")
            return

        print("INFO: Actualizando tabla de venta con nuevas ofertas...")
        
        # Recorremos la lista de datos original y la actualizamos
        for i, player_row in enumerate(self.datos_originales_vender):
            nombre_jugador = player_row[0]
            if nombre_jugador in ofertas:
                print(f"  -> Actualizando oferta para {nombre_jugador}")
                # El índice 3 corresponde a 'Oferta Máquina'
                self.datos_originales_vender[i][3] = ofertas[nombre_jugador]

        # Ahora, recalculamos toda la lista de datos con la información actualizada
        datos_vender_recalculados = []
        dias_defecto = self.view.dias_global_var.get()
        for j_row in self.datos_originales_vender:
            nombre = j_row[0]
            motor = self.motores_calculo[nombre]
            config = {
                "oferta_maquina": j_row[3], # Usamos la oferta actualizada
                "ofertas_hoy": j_row[4],
                "dias_solares": dias_defecto # Usamos los días globales
            }
            resultado = motor.analizar_venta(config)
            equilibrio = motor.encontrar_puja_equilibrio(dias_defecto, "vender")
            margen = equilibrio - j_row[3]
            
            # Reconstruimos la fila
            datos_vender_recalculados.append([
                nombre, j_row[1], j_row[2], j_row[3], j_row[4], dias_defecto,
                resultado['esperanza_matematica'], equilibrio, margen
            ])
        
        # Guardamos los datos actualizados y repoblamos la tabla
        self.datos_originales_vender = datos_vender_recalculados.copy()
        
        headers_vender = {
            "id": ("nombre", "valor", "inc", "oferta_maq", "ofertas_hoy", "dias", "em", "equilibrio", "margen"), 
            "display": ["Nombre", "Valor", "Inc.", "Oferta Máquina", "Ofertas Hoy", "Días", "Esp. Matemática", "Oferta Equilibrio", "Margen"]
        }
        self.view.poblar_tabla("vender", {"headers_id": headers_vender["id"], "headers_display": headers_vender["display"], "data": self.datos_originales_vender})
        messagebox.showinfo("Éxito", f"Tabla de venta actualizada con {len(ofertas)} oferta(s) encontrada(s).")

    def trigger_auto_bid(self):
        """Prepara los datos y lanza el bot de pujas SOLO para los jugadores seleccionados."""
        
        # 1. Obtener las filas seleccionadas de la tabla de fichar
        tree = self.view.tree_fichar
        selected_items = tree.selection()

        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona uno o más jugadores de la tabla para pujar.")
            return

        # 2. Recopilar datos SOLO de las filas seleccionadas
        pujas_a_realizar = []
        for item_id in selected_items:
            valores_fila = tree.item(item_id, 'values')
            try:
                nombre = valores_fila[0]
                # La Puja de Equilibrio está en la penúltima columna
                puja_equilibrio = int(str(valores_fila[-2]).replace('.', '').replace(',', '.'))
                pujas_a_realizar.append({"nombre": nombre, "puja": puja_equilibrio})
            except (IndexError, ValueError):
                continue
        
        if not pujas_a_realizar:
            messagebox.showerror("Error", "No se pudieron leer los datos de los jugadores seleccionados.")
            return

        # 3. Pedir confirmación al usuario
        mensaje = "Se va a intentar pujar por los siguientes jugadores con su puja de equilibrio:\n\n"
        for p in pujas_a_realizar:
            mensaje += f"- {p['nombre']}: {p['puja']:,} €\n"
        mensaje += "\n¿Deseas continuar?"
        
        if messagebox.askyesno("Confirmar Pujas Automáticas", mensaje):
            self.view.btn_auto_bid.config(state="disabled", text="Pujando...")
            # 4. Lanzar el bot en un hilo
            threading.Thread(target=self.run_auto_bid, args=(pujas_a_realizar,), daemon=True).start()
            
    def run_auto_bid(self, pujas_a_realizar):
        """Ejecuta el bot y gestiona el resultado."""
        resultado = realizar_pujas(pujas_a_realizar)
        self.root.after(0, self.on_auto_bid_complete, resultado)

    def on_auto_bid_complete(self, resultado):
        """Callback que se ejecuta cuando el bot de pujas termina."""
        self.view.btn_auto_bid.config(state="normal", text="Realizar TODAS las Pujas de Equilibrio")
        if resultado and resultado.get("exito"):
            messagebox.showinfo("Proceso Finalizado", resultado.get("mensaje", "Las pujas se han completado."))
        else:
            messagebox.showerror("Error en el Bot", resultado.get("mensaje", "Ocurrió un error durante el proceso de puja."))


    def load_data_from_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.jugadores_mercado = json.load(f)
                self.preparar_y_poblar_tablas()
                return
            except Exception as e: print(f"Error cargando caché: {e}")
        messagebox.showinfo("Caché Vacío", "Pulsa 'Actualizar' para cargar la información.")

    def trigger_scrape(self):
        self.view.btn_update.config(state="disabled", text="Actualizando...")
        threading.Thread(target=self.scrape_and_save_to_cache, daemon=True).start()

    def scrape_and_save_to_cache(self):
        self.jugadores_mercado = extraer_jugadores_mercado()
        if self.jugadores_mercado:
            try:
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.jugadores_mercado, f, indent=2, ensure_ascii=False)
            except Exception: pass
        self.root.after(0, self.preparar_y_poblar_tablas)

    def preparar_y_poblar_tablas(self):
        self.view.btn_update.config(state="normal", text="Actualizar Datos del Mercado")
        if not self.jugadores_mercado: return

        self.motores_calculo.clear()
        jugadores_fichar = self.jugadores_mercado.get('para_fichar', [])
        jugadores_vender = self.jugadores_mercado.get('para_vender', [])
        for jugador in jugadores_fichar + jugadores_vender:
            self.motores_calculo[jugador['nombre']] = MotorCalculo(jugador)

        headers_fichar = {"id": ("nombre", "valor", "inc", "puja", "dias", "em", "equilibrio", "margen"), "display": ["Nombre", "Valor", "Inc.", "Mi Puja", "Días", "Esp. Matemática", "Puja Equilibrio", "Margen"]}
        datos_fichar = []
        dias_defecto = self.view.dias_global_var.get()
        for j in jugadores_fichar:
            motor = self.motores_calculo[j['nombre']]
            config = {"puja_k": j['valor'], "dias_solares": dias_defecto}
            resultado = motor.analizar_compra(config)
            equilibrio = motor.encontrar_puja_equilibrio(dias_defecto, "fichar")
            margen = equilibrio - j['valor']
            datos_fichar.append([j['nombre'], j['valor'], j['incremento'], j['valor'], dias_defecto, resultado['esperanza_matematica'], equilibrio, margen])
        self.datos_originales_fichar = datos_fichar.copy()
        self.view.poblar_tabla("fichar", {"headers_id": headers_fichar["id"], "headers_display": headers_fichar["display"], "data": datos_fichar})

        headers_vender = {"id": ("nombre", "valor", "inc", "oferta_maq", "ofertas_hoy", "dias", "em", "equilibrio", "margen"), "display": ["Nombre", "Valor", "Inc.", "Oferta Máquina", "Ofertas Hoy", "Días", "Esp. Matemática", "Oferta Equilibrio", "Margen"]}
        datos_vender = []
        for j in jugadores_vender:
            motor = self.motores_calculo[j['nombre']]
            config = {"oferta_maquina": j['valor'], "ofertas_hoy": 1, "dias_solares": dias_defecto}
            resultado = motor.analizar_venta(config)
            equilibrio = motor.encontrar_puja_equilibrio(dias_defecto, "vender")
            margen = equilibrio - j['valor']
            datos_vender.append([j['nombre'], j['valor'], j['incremento'], j['valor'], 1, dias_defecto, resultado['esperanza_matematica'], equilibrio, margen])
        self.datos_originales_vender = datos_vender.copy()
        self.view.poblar_tabla("vender", {"headers_id": headers_vender["id"], "headers_display": headers_vender["display"], "data": datos_vender})

    def on_header_click(self, col_id, tipo_tabla):
        estado_actual = self.sort_state.get(col_id, None)
        if estado_actual == 'asc': nuevo_estado = 'desc'
        elif estado_actual == 'desc': nuevo_estado = None
        else: nuevo_estado = 'asc'
        
        self.sort_state.clear()
        if nuevo_estado: self.sort_state[col_id] = nuevo_estado

        if tipo_tabla == "fichar":
            datos_a_ordenar = self.datos_originales_fichar.copy()
            headers = {"id": ("nombre", "valor", "inc", "puja", "dias", "em", "equilibrio", "margen"), "display": ["Nombre", "Valor", "Inc.", "Mi Puja", "Días", "Esp. Matemática", "Puja Equilibrio", "Margen"]}
        else:
            datos_a_ordenar = self.datos_originales_vender.copy()
            headers = {"id": ("nombre", "valor", "inc", "oferta_maq", "ofertas_hoy", "dias", "em", "equilibrio", "margen"), "display": ["Nombre", "Valor", "Inc.", "Oferta Máquina", "Ofertas Hoy", "Días", "Esp. Matemática", "Oferta Equilibrio", "Margen"]}

        if nuevo_estado:
            col_index = headers["id"].index(col_id)
            def sort_key(row):
                val = row[col_index]
                if isinstance(val, str) and val.strip() != row[0]:
                    try: return float(val)
                    except ValueError: return val
                return val
            datos_ordenados = sorted(datos_a_ordenar, key=sort_key, reverse=(nuevo_estado == 'desc'))
            self.view.poblar_tabla(tipo_tabla, {"headers_id": headers["id"], "headers_display": headers["display"], "data": datos_ordenados})
        else:
            self.view.poblar_tabla(tipo_tabla, {"headers_id": headers["id"], "headers_display": headers["display"], "data": datos_a_ordenar})

    def on_player_select(self, event, list_type):
        tree = self.view.tree_fichar if list_type == "fichar" else self.view.tree_vender
        selection = tree.selection()
        if not selection: return
        
        item_id = selection[0]
        item_values = tree.item(item_id, 'values')
        nombre_jugador = item_values[0]
        
        self.current_type = list_type
        lista_completa = self.jugadores_mercado.get('para_fichar' if list_type == 'fichar' else 'para_vender', [])
        self.current_player = next((p for p in lista_completa if p['nombre'] == nombre_jugador), None)

        if self.current_player:
            self.view.lbl_nombre.config(text=self.current_player['nombre'])
            self.view.set_active_panel(list_type)
            
            def to_int(value_str):
                try: return int(float(str(value_str).replace('.', '').replace(',', '.')))
                except (ValueError, TypeError): return 0

            if list_type == 'fichar':
                self.view.puja_var.set(to_int(item_values[3]))
                self.view.dias_var.set(to_int(item_values[4]))
            else:
                self.view.oferta_maquina_var.set(to_int(item_values[3]))
                self.view.ofertas_hoy_var.set(to_int(item_values[4]))
                self.view.dias_var.set(to_int(item_values[5]))
            
            self.recalculate_results()

    def recalculate_results(self, event=None):
        if not self.current_player: return
        motor = self.motores_calculo.get(self.current_player['nombre'])
        if not motor: return
        tree = self.view.tree_fichar if self.current_type == 'fichar' else self.view.tree_vender
        item_id = self.current_player['nombre']
        
        try:
            current_values = list(tree.item(item_id)['values'])
            if self.current_type == 'fichar':
                puja = self.view.puja_var.get()
                dias = self.view.dias_var.get()
                config_usuario = {"puja_k": puja, "dias_solares": dias}
                resultado = motor.analizar_compra(config_usuario)
                valor_equilibrio = motor.encontrar_puja_equilibrio(dias, self.current_type)
                margen = valor_equilibrio - puja
                current_values[3] = locale.format_string('%d', puja, grouping=True)
                current_values[4] = dias
                current_values[5] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                current_values[6] = locale.format_string('%d', valor_equilibrio, grouping=True)
                current_values[7] = locale.format_string('%d', margen, grouping=True)
            else: # vender
                oferta_maq = self.view.oferta_maquina_var.get()
                ofertas_hoy = self.view.ofertas_hoy_var.get()
                dias = self.view.dias_var.get()
                config_usuario = {"oferta_maquina": oferta_maq, "ofertas_hoy": ofertas_hoy, "dias_solares": dias}
                resultado = motor.analizar_venta(config_usuario)
                valor_equilibrio = motor.encontrar_puja_equilibrio(dias, self.current_type)
                margen = valor_equilibrio - oferta_maq
                current_values[3] = locale.format_string('%d', oferta_maq, grouping=True)
                current_values[4] = ofertas_hoy
                current_values[5] = dias
                current_values[6] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                current_values[7] = locale.format_string('%d', valor_equilibrio, grouping=True)
                current_values[8] = locale.format_string('%d', margen, grouping=True)

            esperanza_formateada = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.view.lbl_valor_apuesta.config(text=f"{esperanza_formateada} €")
            self.view.lbl_equilibrio_valor.config(text=f"{locale.format_string('%d', valor_equilibrio, grouping=True)} €")
            tree.item(item_id, values=tuple(current_values))
        except (tk.TclError, ValueError, IndexError) as e:
            print(f"Error al recalcular: {e}")

    def recalculate_all_rows(self):
        self.root.config(cursor="watch")
        tipo_tabla = "fichar" if self.view.notebook.tab(self.view.notebook.select(), "text") == 'Para Fichar' else "vender"
        tree = self.view.tree_fichar if tipo_tabla == "fichar" else self.view.tree_vender
        nuevos_dias = self.view.dias_global_var.get()

        for item_id in tree.get_children():
            try:
                motor = self.motores_calculo.get(item_id)
                if not motor: continue
                current_values = list(tree.item(item_id, 'values'))
                def to_int(value_str):
                    try: return int(float(str(value_str).replace('.', '').replace(',', '.')))
                    except (ValueError, TypeError): return 0
                if tipo_tabla == "fichar":
                    puja = to_int(current_values[3])
                    config = {"puja_k": puja, "dias_solares": nuevos_dias}
                    resultado = motor.analizar_compra(config)
                    equilibrio = motor.encontrar_puja_equilibrio(nuevos_dias, tipo_tabla)
                    margen = equilibrio - puja
                    current_values[4] = nuevos_dias
                    current_values[5] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    current_values[6] = locale.format_string('%d', equilibrio, grouping=True)
                    current_values[7] = locale.format_string('%d', margen, grouping=True)
                else: # vender
                    oferta_maq = to_int(current_values[3])
                    ofertas_hoy = to_int(current_values[4])
                    config = {"oferta_maquina": oferta_maq, "ofertas_hoy": ofertas_hoy, "dias_solares": nuevos_dias}
                    resultado = motor.analizar_venta(config)
                    equilibrio = motor.encontrar_puja_equilibrio(nuevos_dias, tipo_tabla)
                    margen = equilibrio - oferta_maq
                    current_values[5] = nuevos_dias
                    current_values[6] = f"{resultado['esperanza_matematica']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    current_values[7] = locale.format_string('%d', equilibrio, grouping=True)
                    current_values[8] = locale.format_string('%d', margen, grouping=True)
                tree.item(item_id, values=tuple(current_values))
            except Exception as e:
                print(f"Error recalculando fila para {item_id}: {e}")
        self.root.config(cursor="")
        
# --- FIN DE LA CLASE VALORACION CONTROLLER ---


def main():
    """
    <-- CAMBIO: Esta es la nueva función principal que orquesta todo.
    """
    # 1. Crear una ventana raíz principal, pero mantenerla oculta por ahora.
    root = tk.Tk()
    root.withdraw()

    # 2. Crear una ventana secundaria (Toplevel) para el mensaje de carga.
    loading_window = tk.Toplevel(root)
    loading_window.title("Cargando...")
    loading_window.resizable(False, False)
    # Centrar la ventana de carga
    root.update_idletasks()
    x = root.winfo_screenwidth() // 2 - 150
    y = root.winfo_screenheight() // 2 - 50
    loading_window.geometry(f'300x100+{x}+{y}')
    
    # Mensaje dentro de la ventana de carga
    loading_font = font.Font(family="Helvetica", size=10)
    tk.Label(loading_window, text="\nBuscando datos del mercado...\nPor favor, espera.", font=loading_font).pack(pady=10)
    
    # <-- CAMBIO CLAVE PARA LINUX: Forzar la actualización de la GUI
    loading_window.update()


    # 3. Crear una cola para la comunicación entre hilos
    result_queue = queue.Queue()

    # 4. Función que se ejecutará en el hilo secundario (el scraper)
    def run_scrape_in_thread():
        print("INFO (hilo): Iniciando scraping de mercado...")
        # Primero, intenta cargar desde el caché
        datos = None
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                print("INFO (hilo): Datos cargados desde la caché.")
            except Exception as e:
                print(f"AVISO (hilo): No se pudo leer la caché ({e}), se procederá a scrapear.")
                datos = None
        
        # Si no hay caché, ejecuta el scraper
        if not datos:
            datos = extraer_jugadores_mercado()
            if datos:
                # Guarda los nuevos datos en la caché para la próxima vez
                try:
                    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(datos, f, indent=2, ensure_ascii=False)
                    print("INFO (hilo): Nuevos datos guardados en caché.")
                except Exception as e:
                    print(f"AVISO (hilo): No se pudo guardar la caché: {e}")

        result_queue.put(datos) # Pone el resultado en la cola

    # 5. Función que revisa periódicamente si el hilo ha terminado
    def check_for_result():
        try:
            # Intenta obtener el resultado de la cola sin bloquear la app
            scraped_data = result_queue.get(block=False)
            
            # Si llegamos aquí, el hilo ha terminado.
            loading_window.destroy() # Cierra la ventana de "cargando"
            
            # Muestra la ventana principal que estaba oculta
            root.deiconify()
            
            # Crea el controlador principal y lo inicia con los datos recién obtenidos
            app = ValoracionController(root)
            app.initialize_with_data(scraped_data)

        except queue.Empty:
            # Si la cola está vacía, el hilo aún está trabajando.
            # Vuelve a llamar a esta misma función después de 100ms.
            root.after(100, check_for_result)

    # 6. Iniciar el hilo del scraper
    threading.Thread(target=run_scrape_in_thread, daemon=True).start()
    
    # 7. Iniciar el primer chequeo de la cola
    root.after(100, check_for_result)

    # 8. Iniciar el bucle principal de la aplicación
    root.mainloop()


if __name__ == '__main__':
    main()
