# generar_reporte.py (Versión con Sprints Completos y Crónicas Regeneradas)

import tkinter as tk
from tkinter import font, scrolledtext
from gestor_datos import cargar_perfiles, cargar_parejas
from cronista import generar_cronica # <-- Importamos al cronista

def calcular_clasificacion_parejas(perfiles, parejas):
    # ... (Esta función no cambia) ...
    if not parejas: return ""
    reporte = "\n\n---\n\n" + "⚔️ **COMPETICIÓN POR PAREJAS (MEDIA TOTAL)** ⚔️\n\n"
    clasificacion = []
    for pareja in parejas:
        puntos_totales, miembros_encontrados = 0, 0
        for manager_id in pareja['id_managers']:
            perfil = next((p for p in perfiles if p['id_manager'] == manager_id), None)
            if perfil and perfil['historial_temporada']:
                puntos_totales += perfil['historial_temporada'][-1]['puntos_totales']
                miembros_encontrados += 1
        media = puntos_totales / miembros_encontrados if miembros_encontrados > 0 else 0
        clasificacion.append({"nombre": pareja['nombre_pareja'], "media": round(media)})
    clasificacion.sort(key=lambda x: x['media'], reverse=True)
    for i, item in enumerate(clasificacion):
        reporte += f"**{i+1}. {item['nombre']}**\n*(Media Total: {item['media']} pts)*\n\n"
    return reporte

def calcular_clasificacion_sprints(perfiles, jornada_actual):
    sprints = {
        "Sprint 1 (J1-10)": (1, 10), "Sprint 2 (J11-20)": (11, 20),
        "Sprint 3 (J21-30)": (21, 30), "Sprint 4 (J31-38)": (31, 38)
    }
    reporte = ""
    for nombre, (inicio, fin) in sprints.items():
        if jornada_actual >= inicio:
            reporte += f"\n\n---\n\n" + f"🚀 **CLASIFICACIÓN {nombre.upper()}** 🚀\n\n"
            clasificacion = []
            for perfil in perfiles:
                puntos = sum(h['puntos_jornada'] for h in perfil['historial_temporada'] if inicio <= h['jornada'] <= fin)
                clasificacion.append({"nombre": perfil['nombre_mister'], "puntos": puntos})
            
            clasificacion.sort(key=lambda x: x['puntos'], reverse=True)
            # --- ¡CAMBIO CLAVE! Eliminamos el [:5] para mostrar a todos ---
            for i, item in enumerate(clasificacion):
                reporte += f"**{i+1}.** {item['nombre']} - {item['puntos']} pts\n"
    return reporte

def main():
    print("--- GENERANDO REPORTE SEMANAL ---")
    
    perfiles = cargar_perfiles()
    parejas = cargar_parejas()
    if not perfiles or not perfiles[0]['historial_temporada']:
        print("ERROR: No hay datos de ninguna jornada en 'perfiles.json'.")
        # ... (código de ventana de error sin cambios) ...
        return

    jornada_actual = perfiles[0]['historial_temporada'][-1]['jornada']
    reporte_individual = f"🏆 ✨ **CRÓNICA DE LA JORNADA {jornada_actual}** ✨ 🏆\n\n"
    
    perfiles.sort(key=lambda p: p['historial_temporada'][-1]['puesto'])
    
    # --- ¡CAMBIO CLAVE! Regeneramos las crónicas ---
    print("Regenerando crónicas con la IA... (esto puede tardar unos segundos)")
    for perfil in perfiles:
        ultimo_historial = perfil['historial_temporada'][-1]
        
        # Llamamos a la IA para obtener una crónica fresca
        print(f"  -> Generando para {perfil['nombre_mister']}...")
        cronica = generar_cronica(perfil, ultimo_historial)
        
        reporte_individual += (f"**{ultimo_historial['puesto']}. {perfil['nombre_mister']} ({ultimo_historial['puntos_totales']} pts)**\n"
                               f"*(Jornada: {ultimo_historial['puntos_jornada']} pts)*\n"
                               f"_{cronica}_\n\n")

    reporte_parejas = calcular_clasificacion_parejas(perfiles, parejas)
    reporte_sprints = calcular_clasificacion_sprints(perfiles, jornada_actual)
    
    reporte_final = reporte_individual + reporte_parejas + reporte_sprints

    # --- Creación de la Ventana de Reporte (sin cambios) ---
    root = tk.Tk(); root.title(f"Reporte de la Jornada {jornada_actual}"); root.geometry("700x800")
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10))
    text_area.pack(expand=True, fill="both", padx=10, pady=10)
    text_area.insert(tk.END, reporte_final); text_area.config(state="disabled")
    def copy_to_clipboard():
        root.clipboard_clear(); root.clipboard_append(reporte_final)
        copy_button.config(text="¡Copiado!", bg="#16a085")
        root.after(2000, lambda: copy_button.config(text="Copiar al Portapapeles", bg="#3498db"))
    button_frame = tk.Frame(root); button_frame.pack(pady=10)
    copy_button = tk.Button(button_frame, text="Copiar al Portapapeles", font=("Helvetica", 11, "bold"), bg="#3498db", fg="white", command=copy_to_clipboard)
    copy_button.pack(side="left", padx=10)
    tk.Button(button_frame, text="Cerrar", font=("Helvetica", 11), command=root.destroy).pack(side="left", padx=10)
    root.mainloop()

if __name__ == "__main__":
    try: main()
    except Exception as e: print(f"Ha ocurrido un error inesperado: {e}")
    finally: print("\n--- PROCESO DE GENERACIÓN DE REPORTE FINALIZADO ---")