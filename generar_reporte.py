# Imports completos, incluyendo tkinter
import tkinter as tk
from tkinter import font, scrolledtext
from gestor_datos import cargar_perfiles, cargar_parejas, cargar_config_liga
from cronista import generar_cronica, generar_comentario_premio, generar_comentario_parejas, generar_comentario_sprint, generar_introduccion_semanal
import os
import markdown
from datetime import datetime
import re
import git

# --- FUNCIONES DE CÁLCULO DE REPORTE (SIN CAMBIOS) ---
# En generar_reporte.py, dentro de calcular_clasificacion_parejas

# REEMPLAZA ESTA FUNCIÓN ENTERA
def calcular_clasificacion_parejas(perfiles, parejas, jornada_actual):
    if not parejas: return ""
    
    titulo = "## ⚔️ COMPETICIÓN POR PAREJAS (MEDIA TOTAL) ⚔️\n\n"
    if jornada_actual == 38:
        titulo = "## ⚔️ COMPETICIÓN POR PAREJAS (CLASIFICACIÓN FINAL) ⚔️\n\n"
    
    clasificacion_texto = ""
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
        clasificacion_texto += f"### {i+1}. {item['nombre']}\n*(Media Total: {item['media']} pts)*\n\n"
    
    # Llamada a la IA para el análisis de parejas
    print(" -> Generando comentario de IA para la clasificación de parejas...")
    comentario_ia = generar_comentario_parejas(clasificacion)
    clasificacion_texto += f"\n_{comentario_ia}_"
    
    return titulo + clasificacion_texto
# En generar_reporte.py, dentro de calcular_clasificacion_sprints

# REEMPLAZA ESTA FUNCIÓN ENTERA
# REEMPLAZA ESTA FUNCIÓN EN generar_reporte.py

def calcular_clasificacion_sprints(perfiles, jornada_actual):
    sprints = { "Sprint 1 (J1-10)": (1, 10), "Sprint 2 (J11-20)": (11, 20), "Sprint 3 (J21-30)": (21, 30), "Sprint 4 (J31-38)": (31, 38) }
    reporte_final = ""
    for nombre, (inicio, fin) in sprints.items():
        if jornada_actual >= inicio:
            titulo = f"## 🚀 CLASIFICACIÓN {nombre.upper()} 🚀\n\n"
            clasificacion_texto = ""
            clasificacion = []
            for perfil in perfiles:
                puntos = sum(h['puntos_jornada'] for h in perfil['historial_temporada'] if inicio <= h['jornada'] <= fin)
                clasificacion.append({"nombre": perfil['nombre_mister'], "puntos": puntos})
            
            clasificacion.sort(key=lambda x: x['puntos'], reverse=True)
            
            for i, item in enumerate(clasificacion): 
                clasificacion_texto += f"**{i+1}.** {item['nombre']} - {item['puntos']} pts\n"
            
            # Llamada a la IA con el contexto temporal
            print(f" -> Generando comentario de IA para {nombre}...")
            comentario_ia = generar_comentario_sprint(nombre, clasificacion, jornada_actual, inicio, fin)
            clasificacion_texto += f"\n_{comentario_ia}_"
            
            reporte_final += titulo + clasificacion_texto + "\n---\n"
    return reporte_final

# REEMPLAZA ESTA FUNCIÓN ENTERA en generar_reporte.py

# REEMPLAZA ESTA FUNCIÓN ENTERA en generar_reporte.py

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
            
    # 3. Sprints
    sprints = { "Ganador Sprint 1": (1, 10), "Ganador Sprint 2": (11, 20), "Ganador Sprint 3": (21, 30), "Ganador Sprint 4": (31, 38) }
    for nombre_premio, (inicio, fin) in sprints.items():
        if jornada_actual >= inicio:
            # ## INICIO DE LA MODIFICACIÓN ##
            
            # Decide el nombre del premio: final o provisional
            if jornada_actual >= fin:
                nombre_premio_final = nombre_premio
            else:
                nombre_premio_final = f"Líder Prov. Sprint {nombre_premio.split(' ')[2]}"
            
            # Calcula el líder actual del sprint
            lider_sprint = max(perfiles, key=lambda p: sum(h['puntos_jornada'] for h in p['historial_temporada'] if inicio <= h['jornada'] <= jornada_actual))
            
            # Asigna el premio con el nombre correcto
            premios_por_manager[lider_sprint['nombre_mister']].append((nombre_premio_final, premios_info.get(nombre_premio, 0)))

            # ## FIN DE LA MODIFICACIÓN ##

    # 4. Campeón de Invierno
    if jornada_actual >= 19:
        lider_invierno = None
        for p in perfiles:
            historial_j19 = next((h for h in p['historial_temporada'] if h['jornada'] == 19), None)
            if historial_j19 and historial_j19['puesto'] == 1:
                lider_invierno = p; break
        if lider_invierno:
            premios_por_manager[lider_invierno['nombre_mister']].append(("Campeón de Invierno", premios_info.get("Campeón de Invierno", 0)))
    
    # --- LÓGICA DEL TÍTULO DINÁMICO ---
    titulo = "## 💰 REPARTO FINAL DE PREMIOS 💰\n\n" if jornada_actual == 38 else "## 💰 BOTE PROVISIONAL 💰\n\n"
    premios_texto = ""
    managers_con_premio = {m: p for m, p in premios_por_manager.items() if p}
    if not managers_con_premio:
        return titulo + "_Aún no hay ningún ganador. ¡Todo por decidir!_\n"
        
    managers_ordenados = sorted(managers_con_premio.items(), key=lambda item: sum(p[1] for p in item[1]), reverse=True)
    for manager, premios in managers_ordenados:
        total_ganado = sum(p[1] for p in premios)
        premios_texto += f"### *{manager}:* {total_ganado:.2f} €\n"
        for nombre, valor in sorted(premios):
            premios_texto += f"  - {nombre}: {valor:.2f} €\n"
    return titulo + premios_texto

# REEMPLAZA ESTA FUNCIÓN ENTERA en generar_reporte.py

def generar_seccion_comentarios_ia(perfiles, parejas, config_liga, jornada_actual):
    if not config_liga or not config_liga.get('premios_valor'): return ""
    print("Generando comentarios de la IA para los premios...")
    es_final = (jornada_actual == 38)
    reporte = "\n\n---\n\n## 🎤 EL MICRÓFONO DEL CRONISTA 🎤\n\n"
    perfiles_ordenados = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puesto'])
    
    # 1. Comentario para el Líder General
    if perfiles_ordenados:
        campeon = perfiles_ordenados[0]
        nombre_premio = "Campeón de Liga" if es_final else "Líder Actual"
        comentario_campeon = generar_comentario_premio(nombre_premio, [campeon['nombre_mister']], jornada_actual, es_final)
        reporte += f"### {nombre_premio}: {campeon['nombre_mister']}\n_{comentario_campeon}_\n\n"
        
    # 2. Comentario para la Pareja de Oro
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
            
            # ## LÍNEA CORREGIDA ##
            comentario_pareja = generar_comentario_premio(nombre_premio_pareja, [pareja_ganadora['nombre']], jornada_actual, es_final)
            
            reporte += f"### {nombre_premio_pareja}: {pareja_ganadora['nombre']}\n_{comentario_pareja}_\n\n"
            
    # 3. Comentarios para Sprints (en curso o finalizados)
    sprints = { "Sprint 1 (J1-10)": (1, 10), "Sprint 2 (J11-20)": (11, 20), "Sprint 3 (J21-30)": (21, 30), "Sprint 4 (J31-38)": (31, 38) }
    for nombre, (inicio, fin) in sprints.items():
        # Solo comentamos si el sprint ya ha empezado
        if jornada_actual >= inicio:
            # Decide si el sprint ha terminado o está en curso
            if jornada_actual >= fin:
                nombre_premio = f"Ganador {nombre}"
                es_sprint_final = True
            else:
                # Extrae el número del sprint para el título provisional
                num_sprint = nombre.split(' ')[1]
                nombre_premio = f"Líder Prov. {num_sprint}"
                es_sprint_final = False

            # Calcula el líder actual del sprint
            lider_actual_sprint = max(perfiles, key=lambda p: sum(h['puntos_jornada'] for h in p['historial_temporada'] if inicio <= h['jornada'] <= jornada_actual))
            
            # Llama al cronista con el contexto correcto (provisional o final)
            comentario_sprint = generar_comentario_premio(nombre_premio, [lider_actual_sprint['nombre_mister']], jornada_actual, es_sprint_final)
            
            reporte += f"### {nombre_premio}: {lider_actual_sprint['nombre_mister']}\n_{comentario_sprint}_\n\n"

    return reporte

# --- FUNCIONES WEB Y DE VENTANA (SIN CAMBIOS) ---
def obtener_temporada_actual():
    now = datetime.now()
    year = now.year
    if now.month >= 8: return f"{str(year)[-2:]}-{str(year+1)[-2:]}"
    else: return f"{str(year-1)[-2:]}-{str(year)[-2:]}"

def generar_html_completo(titulo, contenido_html, nivel_profundidad=1):
    path_css = "../" * nivel_profundidad + "style.css"
    path_home = "../" * nivel_profundidad + "index.html"
    return f'<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{titulo}</title><link rel="stylesheet" href="{path_css}"></head><body><div class="container"><h1>{titulo}</h1>{contenido_html}<footer><a href="{path_home}">Volver al Archivo de Temporadas</a><br><span>Reporte generado el {datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")}</span></footer></div></body></html>'

# REEMPLAZA ESTAS DOS FUNCIONES EN generar_reporte.py

def actualizar_web_historico(jornada_actual, reporte_markdown):
    """
    Función que recibe el texto en MARKDOWN y se encarga de TODA la conversión a HTML.
    """
    print("INFO: Iniciando la actualización del archivo histórico web...")
    temporada = obtener_temporada_actual()
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    path_proyecto = os.getcwd()

    path_docs = os.path.join(path_proyecto, "docs")
    path_temporada = os.path.join(path_docs, temporada)
    os.makedirs(path_temporada, exist_ok=True)
    
    path_nojekyll = os.path.join(path_docs, ".nojekyll")
    if not os.path.exists(path_nojekyll):
        with open(path_nojekyll, 'w') as f: pass
        print("INFO: Creado archivo .nojekyll.")
        
    path_css = os.path.join(path_docs, "style.css")
    if not os.path.exists(path_css):
        css_content = """
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Teko:wght@700&display=swap');
        body { font-family: 'Roboto', sans-serif; line-height: 1.6; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 850px; margin: 20px auto; padding: 0; }
        .report-section { background-color: #ffffff; border: 1px solid #e0e4e8; border-radius: 8px; padding: 20px 30px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
        h1 { font-family: 'Teko', sans-serif; font-size: 3.5em; color: #1a3a6b; text-align: center; padding: 20px 0; margin-bottom: 20px; }
        h2 { font-family: 'Teko', sans-serif; font-size: 2.5em; color: #2c5ba3; border-bottom: 2px solid #2c5ba3; padding-bottom: 10px; margin-top: 10px; }
        h3 { font-family: 'Teko', sans-serif; font-size: 1.8em; color: #3e6bb0; margin-top: 25px; }
        strong { font-weight: 700; } em { color: #555; font-style: italic; } p { margin: 0 0 10px 0; }
        hr { border: 0; height: 1px; background: #ddd; margin: 40px 0; }
        ul { list-style-type: none; padding: 0; }
        li { background-color: #fff; margin: 10px 0; padding: 20px; border-radius: 8px; font-size: 1.2em; transition: all .3s ease; border: 1px solid #e8e8e8; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        li:hover { transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
        li a { text-decoration: none; color: #1a3a6b; font-weight: bold; display: block; text-align: center; }
        footer { text-align: center; padding: 20px; font-size: 0.9em; color: #777; background-color: #eef2f7; border-radius:10px; margin-top: 20px;}
        """
        with open(path_css, "w", encoding="utf-8") as f: f.write(css_content)
    
    # ## CORRECCIÓN CLAVE: La conversión y el enmarcado se hacen aquí, al final. ##
    secciones = reporte_markdown.split('\n---\n')
    secciones_html = [markdown.markdown(s, extensions=['nl2br']) for s in secciones]
    reporte_html_enmarcado = "".join([f'<div class="report-section">{seccion}</div>' for seccion in secciones_html if seccion.strip()])
    
    nombre_archivo_reporte = f"jornada-{jornada_actual}_{timestamp}.html"
    path_reporte = os.path.join(path_temporada, nombre_archivo_reporte)
    titulo_reporte = f"Reporte Jornada {jornada_actual}"
    html_final = generar_html_completo(titulo_reporte, reporte_html_enmarcado, nivel_profundidad=2)
    with open(path_reporte, "w", encoding="utf-8") as f: f.write(html_final)
    print(f"INFO: Guardado reporte en '{path_reporte}'")
    
    # (El resto de la lógica para actualizar índices no cambia)
    archivos_en_temporada = [f for f in os.listdir(path_temporada) if f.startswith("jornada-") and f.endswith(".html")]
    def extractor_para_sort(archivo):
        match_jornada = re.search(r'jornada-(\d+)', archivo); match_fecha = re.search(r'_(\d{8}-\d{6})', archivo)
        if match_jornada and match_fecha: return (int(match_jornada.group(1)), match_fecha.group(1))
        return (0, "")
    archivos_en_temporada.sort(key=extractor_para_sort, reverse=True)
    links_html = []
    for archivo in archivos_en_temporada:
        try:
            num_jornada = re.search(r'jornada-(\d+)', archivo).group(1); fecha_str = re.search(r'_(\d{8}-\d{6})', archivo).group(1)
            fecha_obj = datetime.strptime(fecha_str, '%Y%m%d-%H%M%S')
            texto_enlace = f"Jornada {num_jornada} (Emitido: {fecha_obj.strftime('%d/%m/%Y %H:%M')})"
            links_html.append(f'<li><a href="{archivo}">{texto_enlace}</a></li>')
        except AttributeError: continue
    contenido_indice = "<ul>" + "".join(links_html) + "</ul>"
    html_index_temporada = generar_html_completo(f"Histórico Temporada {temporada}", contenido_indice, nivel_profundidad=1)
    with open(os.path.join(path_temporada, "index.html"), "w", encoding="utf-8") as f: f.write(html_index_temporada)
    print(f"INFO: Actualizado el índice de la temporada {temporada}.")
    temporadas = sorted([d for d in os.listdir(path_docs) if os.path.isdir(os.path.join(path_docs, d))], reverse=True)
    links_temporadas = "".join([f'<li><a href="{t}/index.html">Temporada {t}</a></li>' for t in temporadas])
    html_index_principal = generar_html_completo("Archivo Histórico de la Superliga", f"<ul>{links_temporadas}</ul>", nivel_profundidad=0)
    with open(os.path.join(path_docs, "index.html"), "w", encoding="utf-8") as f: f.write(html_index_principal)
    print(f"INFO: Actualizado el índice principal de temporadas.")
    url_base = "https://Ivanpavonmaizkolmogorov.github.io/superliga-dinamica"
    url_reporte = f"{url_base}/{temporada}/{nombre_archivo_reporte}"
    return url_reporte

# REEMPLAZA ESTA FUNCIÓN en tu archivo generar_reporte.py

def main():
    print("--- GENERANDO REPORTE SEMANAL ---")
    perfiles = cargar_perfiles(); parejas = cargar_parejas(); config_liga = cargar_config_liga()
    if not perfiles or not perfiles[0].get('historial_temporada'):
        print("ERROR: No hay datos de ninguna jornada en 'perfiles.json'."); return
    jornada_actual = perfiles[0]['historial_temporada'][-1]['jornada']
    
    # --- INICIO DE LA MODIFICACIÓN ---
    
    # 1. Generamos la nueva introducción ANTES que nada
    introduccion_ia = generar_introduccion_semanal(perfiles, jornada_actual)
    
    # --- FIN DE LA MODIFICACIÓN ---


    # 1. Generar contenido del reporte en texto plano (Markdown)
    reporte_individual_texto = f"## 🏆 CRÓNICA DE LA JORNADA {jornada_actual} 🏆\n\n"
    perfiles.sort(key=lambda p: p['historial_temporada'][-1]['puesto'])
    for perfil in perfiles:
        ultimo_historial = perfil['historial_temporada'][-1]
        
        # ## INICIO DE LA MODIFICACIÓN ##
        # Buscamos el nombre del rival a partir de su ID
        nombre_del_rival = "Nadie en particular"
        id_rival = perfil.get('rival_historico')
        if id_rival:
            for p_rival in perfiles:
                if p_rival.get('id_manager') == id_rival:
                    nombre_del_rival = p_rival.get('nombre_mister')
                    break
        
        # Le pasamos el nombre del rival a la función del cronista
        cronica = generar_cronica(perfil, ultimo_historial, nombre_del_rival)
        # ## FIN DE LA MODIFICACIÓN ##

        reporte_individual_texto += (f"### {ultimo_historial['puesto']}. {perfil['nombre_mister']} ({ultimo_historial['puntos_totales']} pts)\n"
                                     f"**Jornada:** {ultimo_historial['puntos_jornada']} pts\n\n"
                                     f"_{cronica}_\n\n")

    # (El resto de la función sigue exactamente igual)
    reporte_parejas_texto = calcular_clasificacion_parejas(perfiles, parejas, jornada_actual)
    reporte_sprints_texto = calcular_clasificacion_sprints(perfiles, jornada_actual)
    reporte_reparto_premios_texto = calcular_reparto_premios(perfiles, parejas, config_liga, jornada_actual)
    reporte_comentarios_ia_texto = generar_seccion_comentarios_ia(perfiles, parejas, config_liga, jornada_actual)
    
    reporte_markdown_completo = (reporte_individual_texto + "\n---\n" + 
                                  reporte_parejas_texto + "\n---\n" + 
                                  reporte_sprints_texto + 
                                  reporte_reparto_premios_texto + "\n---\n" +
                                  reporte_comentarios_ia_texto)

    url_reporte_real, reporte_html_enmarcado, css_string = actualizar_web_historico(jornada_actual, reporte_markdown_completo)
    
    titulo_pdf = f"Reporte Superliga - Jornada {jornada_actual}"
    html_para_pdf = generar_html_completo(titulo_pdf, reporte_html_enmarcado, para_pdf=True)
    default_pdf_filename = f"Reporte_J{jornada_actual}_{datetime.now().strftime('%Y%m%d')}.pdf"

    reporte_para_whatsapp = reporte_markdown_completo
    reporte_para_whatsapp = re.sub(r'###\s*(.*?)\s*\n', r'*\1*\n', reporte_para_whatsapp)
    reporte_para_whatsapp = re.sub(r'##\s*(.*?)\s*\n', r'*\1*\n\n', reporte_para_whatsapp)
    reporte_para_whatsapp = reporte_para_whatsapp.replace('**', '*')
    reporte_para_whatsapp = reporte_para_whatsapp.replace('\n---\n', '\n')
    reporte_final_para_clipboard = f"Enlace al reporte web: {url_reporte_real}\n\n" + reporte_para_whatsapp
    
    try:
        repo = git.Repo(os.getcwd())
        
        # --- LÓGICA DE GIT MEJORADA ---

        # 1. Obtenemos la ruta completa a la carpeta 'docs'
        path_docs = os.path.join(os.getcwd(), 'docs')

        # 2. Le decimos a Git que añada SOLAMENTE esa carpeta
        #    Esto añadirá todos los archivos nuevos o modificados DENTRO de 'docs'
        repo.git.add(path_docs)

        # 3. Comprobamos si, después de añadir 'docs', hay algo para hacer commit.
        #    Esto es más seguro que usar is_dirty() al principio.
        if not repo.index.diff("HEAD"):
            print("INFO: No hay cambios en la carpeta 'docs' para subir a GitHub.")
        else:
            print("INFO: Detectados cambios en los reportes, subiendo a GitHub...")
            # 4. Hacemos el commit y el push como antes
            repo.index.commit(f"Actualización del reporte web - J{jornada_actual}")
            repo.remote(name='origin').push()
            print("✅ ¡ÉXITO! El repositorio y la web han sido actualizados.")

    except Exception as e:
        print(f"❌ ERROR al intentar subir los cambios con Git: {e}")

    mostrar_ventana_final(reporte_final_para_clipboard, url_reporte_real, html_para_pdf, css_string, default_pdf_filename)

    # 6. Mostrar la ventana final
    mostrar_ventana_final(reporte_final_para_clipboard, url_reporte_real)

def mostrar_ventana_final(reporte_para_whatsapp, url_reporte):
    root = tk.Tk()
    root.title(f"Reporte Generado y Subido a la Web")
    root.geometry("700x800")
    text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10))
    text_area.pack(expand=True, fill="both", padx=10, pady=10)
    text_area.insert(tk.END, reporte_para_whatsapp)
    text_area.config(state="disabled")
    def copy_reporte_to_clipboard():
        root.clipboard_clear(); root.clipboard_append(reporte_para_whatsapp)
        copy_reporte_button.config(text="¡Reporte Copiado!", bg="#16a085")
        root.after(2000, lambda: copy_reporte_button.config(text="Copiar Reporte", bg="#3498db"))
    def copy_enlace_to_clipboard():
        root.clipboard_clear(); root.clipboard_append(url_reporte)
        copy_enlace_button.config(text="¡Enlace Copiado!", bg="#16a085")
        root.after(2000, lambda: copy_enlace_button.config(text="Copiar Enlace Web", bg="#8e44ad"))
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    copy_reporte_button = tk.Button(button_frame, text="Copiar Reporte para WhatsApp", font=("Helvetica", 11, "bold"), bg="#25D366", fg="white", command=copy_reporte_to_clipboard)
    copy_reporte_button.pack(side="left", padx=10)
    copy_enlace_button = tk.Button(button_frame, text="Copiar Enlace Web", font=("Helvetica", 11, "bold"), bg="#8e44ad", fg="white", command=copy_enlace_to_clipboard)
    copy_enlace_button.pack(side="left", padx=10)
    tk.Button(button_frame, text="Cerrar", font=("Helvetica", 11), command=root.destroy).pack(side="left", padx=10)
    root.mainloop()

# REEMPLAZA ESTA FUNCIÓN ENTERA EN generar_reporte.py

def main():
    print("--- GENERANDO REPORTE SEMANAL ---")
    perfiles = cargar_perfiles(); parejas = cargar_parejas(); config_liga = cargar_config_liga()
    if not perfiles or not perfiles[0].get('historial_temporada'):
        print("ERROR: No hay datos de ninguna jornada en 'perfiles.json'."); return
    jornada_actual = perfiles[0]['historial_temporada'][-1]['jornada']
    
    # 1. Generar contenido del reporte en texto plano (Markdown)
    reporte_individual_texto = f"## 🏆 CRÓNICA DE LA JORNADA {jornada_actual} 🏆\n\n"
    perfiles.sort(key=lambda p: p['historial_temporada'][-1]['puesto'])
    for perfil in perfiles:
        ultimo_historial = perfil['historial_temporada'][-1]
        
        # --- INICIO DE LA NUEVA LÓGICA ---
        
        # Buscamos el nombre del rival a partir de su ID
        nombre_del_rival = "Nadie en particular" # Valor por defecto
        id_rival = perfil.get('rival_historico') # Usamos .get() por seguridad
        
        if id_rival:
            # Buscamos en toda la lista de perfiles hasta encontrar al rival
            for p_rival in perfiles:
                if p_rival.get('id_manager') == id_rival:
                    nombre_del_rival = p_rival.get('nombre_mister', 'Un rival misterioso')
                    break # Dejamos de buscar una vez encontrado
        
        # Ahora llamamos a generar_cronica con TODA la información necesaria
        cronica = generar_cronica(perfil, ultimo_historial, nombre_del_rival)
        
        # --- FIN DE LA NUEVA LÓGICA ---

        reporte_individual_texto += (f"### {ultimo_historial['puesto']}. {perfil['nombre_mister']} ({ultimo_historial['puntos_totales']} pts)\n"
                                    f"**Jornada:** {ultimo_historial['puntos_jornada']} pts\n\n"
                                    f"_{cronica}_\n\n")
        
    reporte_parejas_texto = calcular_clasificacion_parejas(perfiles, parejas, jornada_actual)
    reporte_sprints_texto = calcular_clasificacion_sprints(perfiles, jornada_actual)
    reporte_reparto_premios_texto = calcular_reparto_premios(perfiles, parejas, config_liga, jornada_actual)
    reporte_comentarios_ia_texto = generar_seccion_comentarios_ia(perfiles, parejas, config_liga, jornada_actual)
    
    # 2. Unir las secciones de Markdown para la web
    reporte_markdown_completo = (reporte_individual_texto + "\n---\n" + 
                                  reporte_parejas_texto + "\n---\n" + 
                                  reporte_sprints_texto + 
                                  reporte_reparto_premios_texto + "\n---\n" +
                                  reporte_comentarios_ia_texto)

    # 3. Convertir cada sección a HTML enmarcado para la web
    secciones_html = [markdown.markdown(s, extensions=['nl2br']) for s in reporte_markdown_completo.split('\n---\n')]
    reporte_html_enmarcado = "".join([f'<div class="report-section">{seccion}</div>' for seccion in secciones_html if seccion.strip()])
    
    # 4. Generar la web y obtener la URL real
    url_reporte_real = actualizar_web_historico(jornada_actual, reporte_html_enmarcado)
    
    # ## INICIO DE LA CORRECCIÓN PARA WHATSAPP ##
    
    # 5. Crear una versión del texto optimizada para WhatsApp
    reporte_para_whatsapp = reporte_markdown_completo
    
    # >> CORRECCIÓN: Primero se procesan los ### y LUEGO los ##
    reporte_para_whatsapp = re.sub(r'###\s*(.*?)\s*\n', r'*\1*\n', reporte_para_whatsapp)
    reporte_para_whatsapp = re.sub(r'##\s*(.*?)\s*\n', r'*\1*\n\n', reporte_para_whatsapp)

    # Convierte la negrita de Markdown a la de WhatsApp
    reporte_para_whatsapp = reporte_para_whatsapp.replace('**', '*')
    # Elimina los separadores ---
    reporte_para_whatsapp = reporte_para_whatsapp.replace('\n---\n', '\n')
    
    # 6. Crear el texto final para el portapapeles
    reporte_final_para_clipboard = f"Enlace al reporte web: {url_reporte_real}\n\n" + reporte_para_whatsapp
    
    # ## FIN DE LA CORRECCIÓN ##
    
    # 7. Subir cambios a Git
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

    # 8. Mostrar la ventana final con el texto para WhatsApp
    mostrar_ventana_final(reporte_final_para_clipboard, url_reporte_real)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Ha ocurrido un error inesperado en generar_reporte: {e}")
    finally:
        print("\n--- PROCESO DE GENERACIÓN DE REPORTE FINALIZADO ---")