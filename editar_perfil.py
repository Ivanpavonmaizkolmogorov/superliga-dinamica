# Archivo: editar_perfil.py

import tkinter as tk
from tkinter import ttk, messagebox
from gestor_datos import cargar_perfiles, guardar_perfiles



# REEMPLAZA ESTA CLASE ENTERA en tu archivo editar_perfil.py

class EditorPerfilesApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Editor de Perfiles de Mánagers")
        self.master.geometry("500x400")
        self.master.configure(bg="#ecf0f1")

        self.perfiles = cargar_perfiles()
        self.nombres_managers = [p.get('nombre_mister', 'ID Desconocido') for p in self.perfiles]

        tk.Label(master, text="Selecciona un Mánager para Editar", font=("Helvetica", 14, "bold"), bg="#ecf0f1").pack(pady=10)
        
        self.lista_managers = tk.Listbox(master, font=("Consolas", 11), height=15)
        for nombre in self.nombres_managers:
            self.lista_managers.insert(tk.END, nombre)
        self.lista_managers.pack(pady=5, padx=20, fill="x", expand=True)

        btn_frame = tk.Frame(master, bg="#ecf0f1")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Editar Perfil Seleccionado", font=("Helvetica", 11, "bold"), bg="#3498db", fg="white", command=self.abrir_ventana_edicion).pack()

    def abrir_ventana_edicion(self):
        seleccion = self.lista_managers.curselection()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona un mánager de la lista.")
            return
        
        self.index_seleccionado = seleccion[0]
        perfil_seleccionado = self.perfiles[self.index_seleccionado]

        self.ventana_edicion = tk.Toplevel(self.master)
        self.ventana_edicion.title(f"Editando a: {perfil_seleccionado.get('nombre_mister')}")
        self.ventana_edicion.geometry("600x500")
        self.ventana_edicion.configure(bg="#ecf0f1")

        campos = {
            "nombre_mister": "Nombre del Míster:", "apodo_lema": "Apodo / Lema:",
            "momento_gloria": "Momento de Gloria:", "peor_desastre": "Peor Desastre:",
            "estilo_juego": "Estilo de Juego:", "rival_historico": "Rival Histórico:", # <-- Etiqueta cambiada
            "jugador_fetiche": "Jugador Fetiche:", "filosofia_fichajes": "Filosofía de Fichajes:"
        }
        
        self.entries = {}
        frame_campos = tk.Frame(self.ventana_edicion, bg="#ecf0f1", padx=15, pady=15)
        frame_campos.pack(fill="both", expand=True)

        # ## INICIO DE LA MODIFICACIÓN ##

        # Preparamos la lista de posibles rivales (todos menos el mánager actual)
        id_manager_actual = perfil_seleccionado.get('id_manager')
        self.posibles_rivales = [p for p in self.perfiles if p.get('id_manager') != id_manager_actual]
        nombres_rivales = [p.get('nombre_mister') for p in self.posibles_rivales]

        for i, (key, label_text) in enumerate(campos.items()):
            label = tk.Label(frame_campos, text=label_text, font=("Helvetica", 10), anchor="w", bg="#ecf0f1")
            label.grid(row=i, column=0, sticky="w", pady=5, padx=5)
            
            # Si el campo es 'rival_historico', creamos un ComboBox (desplegable)
            if key == 'rival_historico':
                combobox = ttk.Combobox(frame_campos, values=nombres_rivales, font=("Helvetica", 10), state="readonly")
                combobox.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                
                # Buscamos y pre-seleccionamos el rival actual
                id_rival_actual = perfil_seleccionado.get(key, 0)
                nombre_rival_actual = ""
                for rival in self.posibles_rivales:
                    if rival.get('id_manager') == id_rival_actual:
                        nombre_rival_actual = rival.get('nombre_mister')
                        break
                combobox.set(nombre_rival_actual)
                self.entries[key] = combobox # Guardamos el combobox en lugar del entry
            else:
                # Para el resto de campos, creamos un campo de texto normal
                entry = tk.Entry(frame_campos, font=("Helvetica", 10), width=60)
                entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                entry.insert(0, str(perfil_seleccionado.get(key, "")))
                self.entries[key] = entry
        
        # ## FIN DE LA MODIFICACIÓN ##
            
        frame_campos.grid_columnconfigure(1, weight=1)
        btn_guardar = tk.Button(self.ventana_edicion, text="Guardar Cambios", font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", command=self.guardar_cambios)
        btn_guardar.pack(pady=15)

    def guardar_cambios(self):
        # ## INICIO DE LA MODIFICACIÓN ##
        
        for key, widget in self.entries.items():
            if key == 'rival_historico':
                nombre_seleccionado = widget.get()
                id_rival_seleccionado = 0 # Por defecto, si no se selecciona a nadie
                for rival in self.posibles_rivales:
                    if rival.get('nombre_mister') == nombre_seleccionado:
                        id_rival_seleccionado = rival.get('id_manager')
                        break
                self.perfiles[self.index_seleccionado][key] = id_rival_seleccionado
            else:
                self.perfiles[self.index_seleccionado][key] = widget.get()

        # ## FIN DE LA MODIFICACIÓN ##

        if guardar_perfiles(self.perfiles):
            messagebox.showinfo("Éxito", "Perfil actualizado correctamente.")
            self.lista_managers.delete(self.index_seleccionado)
            self.lista_managers.insert(self.index_seleccionado, self.perfiles[self.index_seleccionado].get('nombre_mister'))
            self.ventana_edicion.destroy()
        else:
            messagebox.showerror("Error", "No se pudieron guardar los cambios en perfiles.json.")

def main():
    root = tk.Tk()
    app = EditorPerfilesApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()