# gui_advertencia.py

import tkinter as tk
from tkinter import messagebox

def confirmar_sin_parejas_gui(root):
    """
    Muestra una ventana emergente advirtiendo que no hay parejas.
    Devuelve True si el usuario pulsa 'Sí', y False si pulsa 'No' o cierra la ventana.
    """
    # Usamos messagebox.askyesno, que es perfecto para esto.
    respuesta = messagebox.askyesno(
        title="Advertencia: No hay Parejas",
        message="¡ATENCIÓN! No se ha encontrado una configuración de parejas.\n\n"
                "El reporte de la jornada se generará, pero NO INCLUIRÁ la competición por equipos.\n\n"
                "¿Deseas continuar de todas formas?",
        icon='warning', # El icono de advertencia
        parent=root # Asocia la ventana al panel principal
    )
    
    return respuesta