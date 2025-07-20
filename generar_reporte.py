# generar_reporte.py (Versión Final con Título Dinámico y Campeón de Invierno)

import tkinter as tk
from tkinter import font, scrolledtext
from gestor_datos import cargar_perfiles, cargar_parejas, cargar_config_liga
from cronista import generar_cronica

def calcular_clasificacion_parejas(perfiles, parejas, jornada_actual):
    if not parejas: return ""
    
    titulo = "⚔️ **COMPETICIÓN POR PAREJAS (CLASIFICACIÓN FINAL)** ⚔️\n\n" if jornada_actual == 38 else "⚔️ **COMPETICIÓN POR PAREJAS (MEDIA TOTAL)** ⚔️\n\n"
    reporte = "\n\n---\n\n" + titulo
    
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
    # ... (Esta función no cambia) ...
    sprints = { "Sprint 1 (J1-10)": (1, 10), "Sprint 2 (J11-20)": (11, 20), "Sprint 3 (J21-30)": (21, 30), "Sprint 4 (J31-38)": (31, 38) }
    reporte = ""
    for nombre, (inicio, fin) in sprints.items():
        if jornada_actual >= inicio:
            reporte += f"\n\n---\n\n" + f"🚀 **CLASIFICACIÓN {nombre.upper()}** 🚀\n\n"
            clasificacion = []
            for perfil in perfiles:
                puntos = sum(h['puntos_jornada'] for h in perfil['historial_temporada'] if inicio <= h['jornada'] <= fin)
                clasificacion.append({"nombre": perfil['nombre_mister'], "puntos": puntos})
            clasificacion.sort(key=lambda x: x['puntos'], reverse=True)
            for i, item in enumerate(clasificacion): reporte += f"**{i+1}.** {item['nombre']} - {item['puntos']} pts\n"
    return reporte

# --- ¡FUNCIÓN CORREGIDA Y COMPLETADA! ---
def calcular_reparto_premios(perfiles, parejas, config_liga, jornada_actual):
    if not config_liga or not config_liga.get('premios_valor'): return ""

    print("Calculando reparto de premios...")
    premios_por_manager = {p['nombre_mister']: [] for p in perfiles}
    premios_info = config_liga['premios_valor']
    
    perfiles_ordenados = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puesto'])
    
    # 1. Premios Anuales (Campeón y Subcampeón)
    if len(perfiles_ordenados) > 0: premios_por_manager[perfiles_ordenados[0]['nombre_mister']].append(("Campeón Absoluto", premios_info.get("Campeón Absoluto", 0)))
    if len(perfiles_ordenados) > 1: premios_por_manager[perfiles_ordenados[1]['nombre_mister']].append(("Subcampeón", premios_info.get("Subcampeón", 0)))

    # 2. Pareja de Oro
    if parejas:
        clasificacion_parejas = []
        for pareja in parejas:
            puntos, num_miembros = 0, 0
            for manager_id in pareja['id_managers']:
                perfil = next((p for p in perfiles if p['id_manager'] == manager_id), None)
                if perfil and perfil['historial_temporada']:
                    puntos += perfil['historial_temporada'][-1]['puntos_totales']; num_miembros += 1
            media = puntos / num_miembros if num_miembros > 0 else 0
            clasificacion_parejas.append({"ids": pareja['id_managers'], "media": media})
        if clasificacion_parejas:
            pareja_ganadora = max(clasificacion_parejas, key=lambda x: x['media'])
            valor_premio_individual = premios_info.get("Pareja de Oro", 0) / len(pareja_ganadora['ids']) if pareja_ganadora['ids'] else 0
            for manager_id in pareja_ganadora['ids']:
                nombre_ganador = next(p['nombre_mister'] for p in perfiles if p['id_manager'] == manager_id)
                premios_por_manager[nombre_ganador].append(("Pareja de Oro", valor_premio_individual))
            
    # 3. Sprints (Se asignan si la jornada actual es IGUAL O POSTERIOR al final del sprint)
    sprints = { "Ganador Sprint 1": (1, 10), "Ganador Sprint 2": (11, 20), "Ganador Sprint 3": (21, 30), "Ganador Sprint 4": (31, 38) }
    for nombre_premio, (inicio, fin) in sprints.items():
        if jornada_actual >= fin: # <-- CORRECCIÓN LÓGICA
            ganador = max(perfiles, key=lambda p: sum(h['puntos_jornada'] for h in p['historial_temporada'] if inicio <= h['jornada'] <= fin))
            premios_por_manager[ganador['nombre_mister']].append((nombre_premio, premios_info.get(nombre_premio, 0)))

    # 4. Campeón de Invierno
    if jornada_actual >= 19:
        lider_invierno = None
        for p in perfiles:
            historial_j19 = next((h for h in p['historial_temporada'] if h['jornada'] == 19), None)
            if historial_j19 and historial_j19['puesto'] == 1:
                lider_invierno = p; break
        if lider_invierno:
            # Usamos el nombre del premio como está en el config para encontrar el valor
            premios_por_manager[lider_invierno['nombre_mister']].append(("Campeón de Invierno", premios_info.get("Campeón de Invierno", 0)))
    
    # --- LÓGICA DEL TÍTULO DINÁMICO ---
    titulo = "💰 **REPARTO FINAL DE PREMIOS** 💰\n\n" if jornada_actual == 38 else "💰 **BOTE PROVISIONAL (SI LA LIGA ACABARA HOY)** 💰\n\n"
    reporte = "\n\n---\n\n" + titulo
    
    managers_con_premio = {m: p for m, p in premios_por_manager.items() if p}
    if not managers_con_premio:
        return reporte + "_Aún no hay ningún ganador. ¡Todo por decidir!_\n"
        
    managers_ordenados = sorted(managers_con_premio.items(), key=lambda item: sum(p[1] for p in item[1]), reverse=True)
    for manager, premios in managers_ordenados:
        total_ganado = sum(p[1] for p in premios)
        reporte += f"*{manager}:* {total_ganado:.2f} €\n"
        for nombre, valor in sorted(premios):
            reporte += f"  - {nombre}: {valor:.2f} €\n"
    return reporte

def main():
    print("--- GENERANDO REPORTE SEMANAL ---")
    perfiles = cargar_perfiles(); parejas = cargar_parejas(); config_liga = cargar_config_liga()
    if not perfiles or not perfiles[0].get('historial_temporada'):
        print("ERROR: No hay datos de ninguna jornada en 'perfiles.json'."); return

    jornada_actual = perfiles[0]['historial_temporada'][-1]['jornada']
    reporte_individual = f"🏆 ✨ **CRÓNICA DE LA JORNADA {jornada_actual}** ✨ 🏆\n\n"
    perfiles.sort(key=lambda p: p['historial_temporada'][-1]['puesto'])
    
    print("Regenerando crónicas con la IA...")
    for perfil in perfiles:
        ultimo_historial = perfil['historial_temporada'][-1]
        print(f"  -> Generando para {perfil['nombre_mister']}...")
        cronica = generar_cronica(perfil, ultimo_historial)
        reporte_individual += (f"**{ultimo_historial['puesto']}. {perfil['nombre_mister']} ({ultimo_historial['puntos_totales']} pts)**\n"
                               f"*(Jornada: {ultimo_historial['puntos_jornada']} pts)*\n"
                               f"_{cronica}_\n\n")

    reporte_parejas = calcular_clasificacion_parejas(perfiles, parejas, jornada_actual)
    reporte_sprints = calcular_clasificacion_sprints(perfiles, jornada_actual)
    reporte_reparto_premios = calcular_reparto_premios(perfiles, parejas, config_liga, jornada_actual)
    
    reporte_final = reporte_individual + reporte_parejas + reporte_sprints + reporte_reparto_premios

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