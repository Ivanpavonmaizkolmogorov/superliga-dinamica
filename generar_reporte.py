# Imports (sin cambios)
import tkinter as tk
from tkinter import font, scrolledtext
from gestor_datos import cargar_perfiles, cargar_parejas, cargar_config_liga
from cronista import generar_cronica, generar_comentario_premio
import os
import markdown
from datetime import datetime
import re
import git

# --- TUS FUNCIONES DE CÁLCULO (SIN CAMBIOS) ---
# ... (aquí van calcular_clasificacion_parejas, calcular_clasificacion_sprints, etc. No las repito para no alargar)
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
        reporte += f"### {i+1}. {item['nombre']}\n*(Media Total: {item['media']} pts)*\n\n"
    return reporte

def calcular_clasificacion_sprints(perfiles, jornada_actual):
    sprints = { "Sprint 1 (J1-10)": (1, 10), "Sprint 2 (J11-20)": (11, 20), "Sprint 3 (J21-30)": (21, 30), "Sprint 4 (J31-38)": (31, 38) }
    reporte = ""
    for nombre, (inicio, fin) in sprints.items():
        if jornada_actual >= inicio:
            reporte += f"\n\n---\n\n## 🚀 CLASIFICACIÓN {nombre.upper()} 🚀\n\n"
            clasificacion = []
            for perfil in perfiles:
                puntos = sum(h['puntos_jornada'] for h in perfil['historial_temporada'] if inicio <= h['jornada'] <= fin)
                clasificacion.append({"nombre": perfil['nombre_mister'], "puntos": puntos})
            clasificacion.sort(key=lambda x: x['puntos'], reverse=True)
            for i, item in enumerate(clasificacion): reporte += f"**{i+1}.** {item['nombre']} - {item['puntos']} pts\n"
    return reporte

def calcular_reparto_premios(perfiles, parejas, config_liga, jornada_actual):
    if not config_liga or not config_liga.get('premios_valor'): return ""
    print("Calculando reparto de premios...")
    premios_por_manager = {p['nombre_mister']: [] for p in perfiles}
    premios_info = config_liga['premios_valor']
    perfiles_ordenados = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puesto'])
    if len(perfiles_ordenados) > 0: premios_por_manager[perfiles_ordenados[0]['nombre_mister']].append(("Campeón Absoluto", premios_info.get("Campeón Absoluto", 0)))
    if len(perfiles_ordenados) > 1: premios_por_manager[perfiles_ordenados[1]['nombre_mister']].append(("Subcampeón", premios_info.get("Subcampeón", 0)))
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
    sprints = { "Ganador Sprint 1": (1, 10), "Ganador Sprint 2": (11, 20), "Ganador Sprint 3": (21, 30), "Ganador Sprint 4": (31, 38) }
    for nombre_premio, (inicio, fin) in sprints.items():
        if jornada_actual >= fin:
            ganador = max(perfiles, key=lambda p: sum(h['puntos_jornada'] for h in p['historial_temporada'] if inicio <= h['jornada'] <= fin))
            premios_por_manager[ganador['nombre_mister']].append((nombre_premio, premios_info.get(nombre_premio, 0)))
    if jornada_actual >= 19:
        lider_invierno = None
        for p in perfiles:
            historial_j19 = next((h for h in p['historial_temporada'] if h['jornada'] == 19), None)
            if historial_j19 and historial_j19['puesto'] == 1:
                lider_invierno = p; break
        if lider_invierno:
            premios_por_manager[lider_invierno['nombre_mister']].append(("Campeón de Invierno", premios_info.get("Campeón de Invierno", 0)))
    titulo = "## 💰 REPARTO FINAL DE PREMIOS 💰\n\n" if jornada_actual == 38 else "## 💰 BOTE PROVISIONAL (SI LA LIGA ACABARA HOY) 💰\n\n"
    reporte = "\n\n---\n\n" + titulo
    managers_con_premio = {m: p for m, p in premios_por_manager.items() if p}
    if not managers_con_premio:
        return reporte + "_Aún no hay ningún ganador. ¡Todo por decidir!_\n"
    managers_ordenados = sorted(managers_con_premio.items(), key=lambda item: sum(p[1] for p in item[1]), reverse=True)
    for manager, premios in managers_ordenados:
        total_ganado = sum(p[1] for p in premios)
        reporte += f"### *{manager}:* {total_ganado:.2f} €\n"
        for nombre, valor in sorted(premios):
            reporte += f"  - {nombre}: {valor:.2f} €\n"
    return reporte

def generar_seccion_comentarios_ia(perfiles, parejas, config_liga, jornada_actual):
    if not config_liga or not config_liga.get('premios_valor'): return ""
    print("Generando comentarios de la IA para los premios...")
    es_final = (jornada_actual == 38)
    reporte = "\n\n---\n\n## 🎤 EL MICRÓFONO DEL CRONISTA: ANÁLISIS DE PREMIOS 🎤\n\n"
    perfiles_ordenados = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puesto'])
    if perfiles_ordenados:
        campeon = perfiles_ordenados[0]
        nombre_premio = "Campeón de Liga" if es_final else "Líder Actual"
        comentario_campeon = generar_comentario_premio(nombre_premio, [campeon['nombre_mister']], jornada_actual, es_final)
        reporte += f"### {nombre_premio}: {campeon['nombre_mister']}\n_{comentario_campeon}_\n\n"
    if parejas:
        clasificacion_parejas = []
        for pareja in parejas:
            puntos, num_miembros = 0, 0
            for manager_id in pareja['id_managers']:
                perfil = next((p for p in perfiles if p['id_manager'] == manager_id), None)
                if perfil:
                    puntos += perfil['historial_temporada'][-1]['puntos_totales']; num_miembros += 1
            media = puntos / num_miembros if num_miembros > 0 else 0
            clasificacion_parejas.append({"nombre": pareja['nombre_pareja'], "media": media})
        if clasificacion_parejas:
            pareja_ganadora = max(clasificacion_parejas, key=lambda x: x['media'])
            nombre_premio_pareja = "Pareja de Oro (Campeones)" if es_final else "Pareja de Oro (Líderes)"
            comentario_pareja = generar_comentario_premio(nombre_premio_pareja, [pareja_ganadora['nombre']], jornada_actual, es_final)
            reporte += f"### {nombre_premio_pareja}: {pareja_ganadora['nombre']}\n_{comentario_pareja}_\n\n"
    sprints = { "Sprint 1 (J1-10)": (1, 10), "Sprint 2 (J11-20)": (11, 20), "Sprint 3 (J21-30)": (21, 30), "Sprint 4 (J31-38)": (31, 38) }
    for nombre, (inicio, fin) in sprints.items():
        if jornada_actual >= fin:
            ganador = max(perfiles, key=lambda p: sum(h['puntos_jornada'] for h in p['historial_temporada'] if inicio <= h['jornada'] <= fin))
            comentario_sprint = generar_comentario_premio(f"Ganador {nombre}", [ganador['nombre_mister']], jornada_actual, True)
            reporte += f"### Ganador {nombre}: {ganador['nombre_mister']}\n_{comentario_sprint}_\n\n"
    return reporte

# --- FUNCIONES WEB (CON CSS PROFESIONAL) ---
def obtener_temporada_actual():
    now = datetime.now()
    year = now.year
    if now.month >= 8:
        return f"{str(year)[-2:]}-{str(year+1)[-2:]}"
    else:
        return f"{str(year-1)[-2:]}-{str(year)[-2:]}"

def generar_html_completo(titulo, contenido_html, nivel_profundidad=1):
    path_css = "../" * nivel_profundidad + "style.css"
    path_home = "../" * nivel_profundidad + "index.html"
    return f"""
    <!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title><link rel="stylesheet" href="{path_css}"></head><body><div class="container">
    <h1>{titulo}</h1><div class="report-content">{contenido_html}</div><footer>
    <a href="{path_home}">Volver al Archivo de Temporadas</a><br>
    <span>Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}</span></footer></div></body></html>
    """

# REEMPLAZA ESTA FUNCIÓN ENTERA EN generar_reporte.py

def actualizar_web_historico(jornada_actual, reporte_texto):
    """
    Función principal que orquesta la creación y actualización de todos los archivos HTML.
    VERSIÓN CORREGIDA Y SIMPLIFICADA.
    """
    print("INFO: Iniciando la actualización del archivo histórico web...")
    temporada = obtener_temporada_actual()
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    path_proyecto = os.getcwd()

    # --- Rutas ---
    path_docs = os.path.join(path_proyecto, "docs")
    path_temporada = os.path.join(path_docs, temporada)
    os.makedirs(path_temporada, exist_ok=True)
    
    # --- CSS (sin cambios) ---
    path_css = os.path.join(path_docs, "style.css")
    if not os.path.exists(path_css):
        css_content = """
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Teko:wght@700&display=swap');
        body { font-family: 'Roboto', sans-serif; line-height: 1.6; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 850px; margin: 20px auto; background-color: #fff; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }
        h1 { font-family: 'Teko', sans-serif; font-size: 3.5em; color: #1a3a6b; text-align: center; padding: 20px 0; margin: 0; background-color: #eef2f7; border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom: 3px solid #d0d9e3; }
        .report-content { padding: 20px 40px; }
        h2 { font-family: 'Teko', sans-serif; font-size: 2.5em; color: #2c5ba3; border-bottom: 2px solid #2c5ba3; padding-bottom: 10px; margin-top: 40px; }
        h3 { font-family: 'Teko', sans-serif; font-size: 1.8em; color: #3e6bb0; margin-top: 25px; }
        strong { font-weight: 700; }
        em { color: #555; font-style: italic; }
        p { margin: 0 0 10px 0; }
        hr { border: 0; height: 1px; background: #ddd; margin: 40px 0; }
        ul { list-style-type: none; padding: 0; }
        li { background-color: #fff; margin: 10px 0; padding: 20px; border-radius: 8px; font-size: 1.2em; transition: all .3s ease; border: 1px solid #e8e8e8; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        li:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
        li a { text-decoration: none; color: #1a3a6b; font-weight: bold; display: block; text-align: center; }
        footer { text-align: center; padding: 20px; font-size: 0.9em; color: #777; background-color: #eef2f7; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; border-top: 1px solid #d0d9e3;}
        """
        with open(path_css, "w", encoding="utf-8") as f: f.write(css_content)
    
    # --- Lógica de Generación HTML (CORREGIDA Y SIMPLIFICADA) ---
    
    # ## SIMPLIFICADO ##: El nombre del archivo ahora es mucho más limpio.
    nombre_archivo = f"jornada-{jornada_actual}_{timestamp}.html"
    path_reporte = os.path.join(path_temporada, nombre_archivo)
    
    reporte_html = markdown.markdown(reporte_texto, extensions=['nl2br'])
    titulo_reporte = f"Reporte Jornada {jornada_actual}"
    html_final = generar_html_completo(titulo_reporte, reporte_html, nivel_profundidad=2)
    with open(path_reporte, "w", encoding="utf-8") as f: f.write(html_final)
    print(f"INFO: Guardado reporte en '{path_reporte}'")

    # ## SIMPLIFICADO ##: La forma de buscar archivos ahora es más simple y correcta.
    archivos_reporte = [f for f in os.listdir(path_temporada) if f.startswith("jornada-")]
    
    def extractor_para_sort(archivo):
        match_jornada = re.search(r'jornada-(\d+)', archivo)
        match_fecha = re.search(r'_(\d{8}-\d{6})', archivo)
        if match_jornada and match_fecha:
            return (int(match_jornada.group(1)), match_fecha.group(1))
        return (0, "")
    archivos_reporte.sort(key=extractor_para_sort, reverse=True)
    
    links_jornadas_html = []
    for archivo in archivos_reporte:
        try:
            num_jornada = re.search(r'jornada-(\d+)', archivo).group(1)
            fecha_str = re.search(r'_(\d{8}-\d{6})', archivo).group(1)
            fecha_obj = datetime.strptime(fecha_str, '%Y%m%d-%H%M%S')
            texto_del_enlace = f"Jornada {num_jornada} (Emitido: {fecha_obj.strftime('%d/%m/%Y %H:%M')})"
            links_jornadas_html.append(f'<li><a href="{archivo}">{texto_del_enlace}</a></li>')
        except AttributeError:
            print(f"ADVERTENCIA: Archivo '{archivo}' no tiene el formato esperado.")
            continue
            
    contenido_indice_temporada = "<ul>" + "".join(links_jornadas_html) + "</ul>"
    html_index_temporada = generar_html_completo(f"Histórico Temporada {temporada}", contenido_indice_temporada, nivel_profundidad=1)
    with open(os.path.join(path_temporada, "index.html"), "w", encoding="utf-8") as f: f.write(html_index_temporada)
    print(f"INFO: Actualizado el índice de la temporada {temporada}.")
    
    # --- Lógica de índice principal y URL (CORREGIDA Y SIMPLIFICADA) ---
    temporadas = sorted([d for d in os.listdir(path_docs) if os.path.isdir(os.path.join(path_docs, d))], reverse=True)
    links_temporadas = "".join([f'<li><a href="{t}/index.html">Temporada {t}</a></li>' for t in temporadas])
    html_index_principal = generar_html_completo("Archivo Histórico de la Superliga", f"<ul>{links_temporadas}</ul>", nivel_profundidad=0)
    with open(os.path.join(path_docs, "index.html"), "w", encoding="utf-8") as f: f.write(html_index_principal)
    print(f"INFO: Actualizado el índice principal de temporadas.")
    
    # ## SIMPLIFICADO ##: La construcción de la URL ahora es más directa.
    nombre_archivo_relativo = f"{temporada}/{nombre_archivo}"
    url_base = f"https://Ivanpavonmaizkolmogorov.github.io/superliga-dinamica/"
    url_reporte = url_base + nombre_archivo_relativo.replace("\\", "/")
    return url_reporte

# --- VENTANA TKINTER CON DOBLE PORTAPAPELES (SIN CAMBIOS) ---
def mostrar_ventana_final(reporte_final, url_reporte):
    root = tk.Tk()
    root.title(f"Reporte Generado y Subido a la Web")
    root.geometry("700x800")
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10))
    text_area.pack(expand=True, fill="both", padx=10, pady=10)
    text_area.insert(tk.END, reporte_final)
    text_area.config(state="disabled")
    def copy_reporte_to_clipboard():
        root.clipboard_clear(); root.clipboard_append(reporte_final)
        copy_reporte_button.config(text="¡Reporte Copiado!", bg="#16a085")
        root.after(2000, lambda: copy_reporte_button.config(text="Copiar Reporte", bg="#3498db"))
    def copy_enlace_to_clipboard():
        root.clipboard_clear(); root.clipboard_append(url_reporte)
        copy_enlace_button.config(text="¡Enlace Copiado!", bg="#16a085")
        root.after(2000, lambda: copy_enlace_button.config(text="Copiar Enlace Web", bg="#8e44ad"))
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    copy_reporte_button = tk.Button(button_frame, text="Copiar Reporte", font=("Helvetica", 11, "bold"), bg="#3498db", fg="white", command=copy_reporte_to_clipboard)
    copy_reporte_button.pack(side="left", padx=10)
    copy_enlace_button = tk.Button(button_frame, text="Copiar Enlace Web", font=("Helvetica", 11, "bold"), bg="#8e44ad", fg="white", command=copy_enlace_to_clipboard)
    copy_enlace_button.pack(side="left", padx=10)
    tk.Button(button_frame, text="Cerrar", font=("Helvetica", 11), command=root.destroy).pack(side="left", padx=10)
    root.mainloop()

# --- FUNCIÓN MAIN MODIFICADA (SIN CAMBIOS) ---
def main():
    print("--- GENERANDO REPORTE SEMANAL ---")
    perfiles = cargar_perfiles(); parejas = cargar_parejas(); config_liga = cargar_config_liga()
    if not perfiles or not perfiles[0].get('historial_temporada'):
        print("ERROR: No hay datos de ninguna jornada en 'perfiles.json'."); return
    jornada_actual = perfiles[0]['historial_temporada'][-1]['jornada']
    
    # 1. Adaptar títulos a Markdown para H2 y H3
    reporte_individual = f"## 🏆 CRÓNICA DE LA JORNADA {jornada_actual} 🏆\n\n"
    perfiles.sort(key=lambda p: p['historial_temporada'][-1]['puesto'])
    for perfil in perfiles:
        ultimo_historial = perfil['historial_temporada'][-1]
        cronica = generar_cronica(perfil, ultimo_historial)
        reporte_individual += (f"### {ultimo_historial['puesto']}. {perfil['nombre_mister']} ({ultimo_historial['puntos_totales']} pts)\n"
                               f"**Jornada:** {ultimo_historial['puntos_jornada']} pts\n\n"
                               f"_{cronica}_\n\n")

    reporte_parejas = calcular_clasificacion_parejas(perfiles, parejas, jornada_actual)
    reporte_sprints = calcular_clasificacion_sprints(perfiles, jornada_actual)
    reporte_reparto_premios = calcular_reparto_premios(perfiles, parejas, config_liga, jornada_actual)
    reporte_comentarios_ia = generar_seccion_comentarios_ia(perfiles, parejas, config_liga, jornada_actual)
    
    url_placeholder = "GENERANDO_URL..."
    reporte_texto_plano = (reporte_individual + reporte_parejas + reporte_sprints + reporte_reparto_premios + reporte_comentarios_ia)
    reporte_para_clipboard = f"Enlace al reporte web: {url_placeholder}\n\n" + reporte_texto_plano

    url_reporte_real = actualizar_web_historico(jornada_actual, reporte_texto_plano)
    
    reporte_final_actualizado = reporte_para_clipboard.replace(url_placeholder, url_reporte_real)

    try:
        repo = git.Repo(os.getcwd())
        if not repo.is_dirty(untracked_files=True):
            print("INFO: No hay cambios para subir a GitHub.")
        else:
            print("INFO: Detectados cambios, subiendo a GitHub...")
            repo.git.add(A=True) 
            repo.index.commit(f"Actualización del reporte web - J{jornada_actual}")
            repo.remote(name='origin').push()
            print("✅ ¡ÉXITO! El repositorio y la web han sido actualizados.")
    except Exception as e:
        print(f"❌ ERROR al intentar subir los cambios con Git: {e}")

    mostrar_ventana_final(reporte_final_actualizado, url_reporte_real)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ha ocurrido un error inesperado en generar_reporte: {e}")
    finally:
        print("\n--- PROCESO DE GENERACIÓN DE REPORTE FINALIZADO ---")