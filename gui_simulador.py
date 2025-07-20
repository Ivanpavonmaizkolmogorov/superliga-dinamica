# gui_simulador.py

import tkinter as tk
from tkinter import simpledialog, messagebox

def pedir_jornada_gui(root):
    """
    Muestra una ventana emergente para preguntar al usuario a qué jornada quiere viajar.
    Devuelve el número de jornada como un entero, o None si el usuario cancela.
    """
    # Usamos simpledialog, que es una herramienta de Tkinter perfecta para esto.
    # El bucle es para asegurar que el usuario introduce un número válido.
    while True:
        jornada_str = simpledialog.askstring(
            "Simulador de Temporada", 
            "Introduce el número de jornada a la que quieres viajar (1-38):",
            parent=root # Esto asocia la ventana emergente a la principal
        )

        # Si el usuario pulsa "Cancelar" o cierra la ventana, devuelve None
        if jornada_str is None:
            return None

        # Si pulsa "Aceptar", intentamos convertir el texto a número
        try:
            jornada_num = int(jornada_str)
            if 1 <= jornada_num <= 38:
                return jornada_num # Si es válido, lo devolvemos
            else:
                # Si el número está fuera de rango, mostramos un error
                messagebox.showerror("Error", "El número de jornada debe estar entre 1 y 38.", parent=root)
        except (ValueError, TypeError):
            # Si no introduce un número, mostramos un error
            messagebox.showerror("Error", "Por favor, introduce un número válido.", parent=root)