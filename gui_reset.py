# gui_reset.py

import tkinter as tk
from tkinter import messagebox

def confirmar_reinicio_gui(root):
    """
    Muestra una ventana emergente de advertencia para confirmar el reinicio.
    Devuelve True si el usuario pulsa 'Sí', y False si pulsa 'No' o cierra la ventana.
    """
    # Usamos messagebox, una herramienta de Tkinter perfecta para diálogos de confirmación.
    # El icono de "warning" y los botones "yesno" vienen predefinidos.
    respuesta = messagebox.askyesno(
        title="Confirmación de Reinicio de Temporada",
        message="¡ADVERTENCIA! Esta acción es IRREVERSIBLE.\n\n"
                "Se borrará TODA la información de las parejas y el historial de TODAS las jornadas.\n\n"
                "¿Estás completamente seguro de que quieres reiniciar la temporada?",
        icon='warning',
        parent=root # Asocia la ventana al panel principal
    )
    
    # askyesno devuelve True si se pulsa "Sí" y False si se pulsa "No".
    return respuesta