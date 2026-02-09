# Imports completos, incluyendo tkinter
import tkinter as tk
from tkinter import font, scrolledtext, messagebox
from gestor_datos import cargar_perfiles, cargar_parejas, cargar_config_liga
# --- CORRECCIÓN 1: Importamos las funciones necesarias del cronista ---
from limpiar_declaraciones import limpiar_declaraciones_antiguas

from cronista import (
    generar_introduccion_semanal,
    generar_todas_las_cronicas,
    generar_comentario_parejas,
    generar_comentario_sprint,
    generar_comentario_premio,
    elegir_comentarista
)
# --- IMPORTS DEL SISTEMA DE EVENTOS ---
from eventos import detectar_eventos_individuales, agrupar_eventos_por_manager, detectar_eventos_parejas

import os
import markdown
from datetime import datetime
import re
import git
import asyncio
from telegram_sender import send_telegram_message
import time
import json
import telegram

BOT_STATE_PATH = 'bot_state.json'


async def publicar_reporte_y_abrir_declaraciones(token: str, chat_id: str, jornada_actual: int, url_reporte: str) -> None:
    """
    Envía un único mensaje que anuncia el reporte y abre las declaraciones, y luego lo ancla.
    """
    print("--- [AUTOMATIZACIÓN] Publicando mensaje 2x1: Reporte y Anuncio...")
    try:
        bot = telegram.Bot(token=token)
        bot_info = await bot.get_me()
        bot_username = bot_info.username

        # 1. Desanclar el mensaje antiguo si existe
        try:
            with open(BOT_STATE_PATH, 'r') as f:
                state = json.load(f)
                old_message_id = state.get('pinned_message_id')
                if old_message_id:
                    try:
                        # NUEVO: Intentamos desanclar dentro de su propio try/except
                        await bot.unpin_chat_message(chat_id=chat_id)
                        print(f"INFO: Desanclado mensaje anterior {old_message_id}.")
                    except Exception as e:
                        # Si el mensaje no se encuentra (porque fue borrado, o no hay nada anclado),
                        # simplemente lo informamos y continuamos.
                        print(f"ADVERTENCIA: No se pudo desanclar el mensaje (puede que no existiera). Error: {e}")
        except (FileNotFoundError, json.JSONDecodeError):
            pass # No hay estado guardado, no hacemos nada

        # 2. Construir el nuevo mensaje "2 en 1" y genérico
        texto_mensaje = (
            f"📰 **¡Ya está disponible el reporte de la Jornada {jornada_actual}!**\n\n"
            f"Puedes leerlo online [pulsando aquí]({url_reporte}).\n\n"
            f"--- \n\n"
            f"🎙️ **Micrófono abierto para nuevas declaraciones.**\n\n"
            f"Mencionen a **@{bot_username}** en sus mensajes para que el Cronista les escuche."
        )
        
        # 3. Enviar el nuevo mensaje
        mensaje_enviado = await bot.send_message(chat_id=chat_id, text=texto_mensaje, parse_mode='Markdown', disable_web_page_preview=True)

        # 4. Anclar el nuevo mensaje
        await bot.pin_chat_message(chat_id=chat_id, message_id=mensaje_enviado.message_id, disable_notification=False)

        # 5. Guardar el estado del nuevo mensaje
        with open(BOT_STATE_PATH, 'w') as f:
            json.dump({'pinned_message_id': mensaje_enviado.message_id}, f)
        
        print(f"✅ ¡ÉXITO! Mensaje 2x1 publicado y anclado correctamente.")

    except Exception as e:
        print(f"❌ ERROR al publicar el mensaje 2x1 en Telegram: {e}")


def calcular_clasificacion_parejas(perfiles, parejas, jornada_actual):
    if not parejas: return ""
    titulo = f"## ⚔️ COMPETICIÓN POR PAREJAS (Jornada {jornada_actual}) ⚔️\n\n"
    
    eventos_parejas = detectar_eventos_parejas(perfiles, parejas)
    
    clasificacion = []
    for pareja in parejas:
        miembros = [p for p in perfiles if p['id_manager'] in pareja.get('id_managers', [])]
        if not miembros: continue
        puntos_totales = sum(m['historial_temporada'][-1]['puntos_totales'] for m in miembros)
        nombres_miembros = [m['nombre_mister'] for m in miembros] # <-- AÑADIMOS ESTO
        media = puntos_totales / len(miembros)
        # Y AHORA GUARDAMOS LOS NOMBRES EN LA CLASIFICACIÓN
        clasificacion.append({"nombre": pareja['nombre_pareja'], "media": round(media), "miembros": nombres_miembros})
    
    clasificacion.sort(key=lambda x: x['media'], reverse=True)
    
    clasificacion_texto = ""
    for i, item in enumerate(clasificacion):
        nombre_pareja = item['nombre'] # "La Dinastía"
        media_pareja = item['media']
        
        # --- ¡AQUÍ ESTÁ LA NUEVA LÓGICA! ---
        
        # Si la pareja tiene eventos, creamos un desplegable
        if nombre_pareja in eventos_parejas:
            # CONSTRUIMOS EL TEXTO DE LOS MIEMBROS
            texto_miembros = f" ({' & '.join(item['miembros'])})"
            # Y LO AÑADIMOS AL TÍTULO
            summary = f"<b>{i+1}. {nombre_pareja}</b>{texto_miembros} - (Media Total: {media_pareja} pts)"
            
            # Construimos el contenido del desplegable
            contenido_desplegable = ""
            for evento_texto in eventos_parejas[nombre_pareja]:
                contenido_desplegable += f"<p><em>{evento_texto}</em></p>"
            
            clasificacion_texto += f"<details><summary>{summary}</summary>{contenido_desplegable}</details>\n"
        
        # Si no hay eventos, mostramos la línea como antes (pero sin markdown extra)
        else:
            # HACEMOS LO MISMO PARA LAS LÍNEAS NORMALES
            texto_miembros = f" ({' & '.join(item['miembros'])})"
            clasificacion_texto += f"<b>{i+1}. {nombre_pareja}</b>{texto_miembros} - (Media Total: {media_pareja} pts)\n"

    return f"{titulo}{clasificacion_texto}"


def calcular_clasificacion_sprints(perfiles, jornada_actual):
    sprints = {"Sprint 1 (J1-10)": (1, 10), "Sprint 2 (J11-20)": (11, 20), "Sprint 3 (J21-30)": (21, 30), "Sprint 4 (J31-38)": (31, 38)}
    reporte_final = ""
    for nombre, (inicio, fin) in sprints.items():
        if jornada_actual >= inicio:
            titulo = f"## 🚀 CLASIFICACIÓN {nombre.upper()} 🚀\n\n"
            clasificacion = []
            
            print(f"\n--- [LOG] Verificando Cálculo de {nombre} (J{inicio}-J{fin}) ---")
            
            for perfil in perfiles:
                # Log confirmado solicitado por el usuario
                puntos_desglosados = [h['puntos_jornada'] for h in perfil['historial_temporada'] if inicio <= h['jornada'] <= fin]
                puntos = sum(puntos_desglosados)
                
                # Solo imprimimos si tiene puntos o es relevante, para no ensuciar demasiado
                if puntos > 0:
                    print(f"   > {perfil['nombre_mister']}: Suma({puntos_desglosados}) = {puntos}")
                
                clasificacion.append({"nombre": perfil['nombre_mister'], "puntos": puntos})
                
            clasificacion.sort(key=lambda x: x['puntos'], reverse=True)
            clasificacion_texto = "".join([f"**{i+1}.** {item['nombre']} - {item['puntos']} pts\n" for i, item in enumerate(clasificacion)])
            reporte_final += f"{titulo}{clasificacion_texto}\n\n---\n"
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
        for p in parejas:
            miembros = [m for m in perfiles if m['id_manager'] in p['id_managers']]
            if miembros:
                puntos_pareja = sum(m['historial_temporada'][-1]['puntos_totales'] for m in miembros)
                clasificacion_parejas.append({'ids': p['id_managers'], 'media': puntos_pareja / len(miembros)})
        if clasificacion_parejas:
            pareja_ganadora_ids = max(clasificacion_parejas, key=lambda x: x['media'])['ids']
            if len(pareja_ganadora_ids) > 0: # Añadimos una comprobación extra por seguridad
                valor_individual = premios_info.get("Pareja de Oro", 0) / len(pareja_ganadora_ids)
                for manager_id in pareja_ganadora_ids:
                    # Usamos next() con un valor por defecto (None) para que no crashee si no lo encuentra.
                    nombre_ganador = next((p['nombre_mister'] for p in perfiles if p['id_manager'] == manager_id), None)
                    
                    # Solo añadimos el premio SI hemos encontrado un nombre de ganador.
                    if nombre_ganador:
                        premios_por_manager[nombre_ganador].append(("Pareja de Oro", valor_individual))
            
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



# --- CORRECCIÓN 4: Nueva sección para los comentarios de los premios ---
# Versión final de la sección de comentarios, ahora desactivada

# En generar_reporte.py, reemplaza la función vacía por esta:

def generar_seccion_comentarios_ia(perfiles, parejas, config_liga, jornada_actual):
    """
    Genera la sección final de comentarios de la IA, "El Micrófono del Cronista",
    analizando a los líderes de las principales categorías.
    """
    print("--- [IA] Generando la sección 'Micrófono del Cronista'...")
    es_final_temporada = (jornada_actual == 38)
    reporte = "\n---\n## 🎤 EL MICRÓFONO DEL CRONISTA 🎤\n\n"
    perfiles_ordenados = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puesto'])
    
    # 1. Comentario sobre el Líder Actual
    if perfiles_ordenados:
        lider = perfiles_ordenados[0]
        # La función generar_comentario_premio viene de cronista.py
        comentario = generar_comentario_premio("Líder Actual", [lider['nombre_mister']], jornada_actual, es_final_temporada)
        reporte += f"### Sobre el Líder Actual: {lider['nombre_mister']}\n{comentario}\n\n"
        
    # 2. Comentario sobre la Pareja de Oro
    if parejas:
        clasificacion_parejas = []
        for p in parejas:
            miembros = [m for m in perfiles if m['id_manager'] in p.get('id_managers', [])]
            if miembros:
                puntos = sum(m['historial_temporada'][-1]['puntos_totales'] for m in miembros)
                clasificacion_parejas.append({'nombre': p['nombre_pareja'], 'media': puntos / len(miembros)})
        if clasificacion_parejas:
            ganadora = max(clasificacion_parejas, key=lambda x: x['media'])
            comentario = generar_comentario_premio("Pareja de Oro (Líderes)", [ganadora['nombre']], jornada_actual, es_final_temporada)
            reporte += f"### Sobre la Pareja de Oro: {ganadora['nombre']}\n{comentario}\n\n"
            
    # 3. Comentario sobre los Líderes de Sprints
    sprints_def = {"Sprint 1 (J1-10)": (1, 10), "Sprint 2 (J11-20)": (11, 20), "Sprint 3 (J21-30)": (21, 30), "Sprint 4 (J31-38)": (31, 38)}
    for nombre, (inicio, fin) in sprints_def.items():
        if jornada_actual >= inicio:
            es_final = (jornada_actual >= fin)
            lider = max(perfiles, key=lambda p: sum(h['puntos_jornada'] for h in p['historial_temporada'] if inicio <= h['jornada'] <= jornada_actual))
            comentario = generar_comentario_premio(f"Líder {nombre}", [lider['nombre_mister']], jornada_actual, es_final)
            reporte += f"### Sobre el Líder del {nombre}: {lider['nombre_mister']}\n{comentario}\n\n"
            
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

def mostrar_ventana_final(texto_clipboard, url_web):
    """
    Muestra una ventana de confirmación que SIEMPRE aparece en primer plano
    y copia el contenido al portapapeles.
    """
    try:
        # Creamos una ventana raíz invisible que nos servirá de base
        root = tk.Tk()
        root.withdraw()

        # --- INICIO DE LA MODIFICACIÓN CLAVE ---
        # Esta línea obliga a la ventana (y a sus hijas, como el messagebox)
        # a estar siempre por encima de cualquier otra aplicación.
        root.attributes('-topmost', True)
        # --- FIN DE LA MODIFICACIÓN CLAVE ---

        # Copiamos el contenido al portapapeles de forma explícita
        root.clipboard_clear()
        root.clipboard_append(texto_clipboard)
        
        mensaje_popup = (
            "¡El reporte se ha generado con éxito!\n\n"
            f"URL: {url_web}\n\n"
            "El contenido para WhatsApp ha sido copiado al portapapeles."
        )

        # Mostramos el messagebox, que heredará la propiedad 'topmost'
        messagebox.showinfo("Reporte Generado", mensaje_popup)

        # Destruimos la ventana invisible para limpiar la memoria
        root.destroy()

    except Exception as e:
        print("\n--- INFO: No se pudo mostrar la ventana final (quizás falte entorno gráfico) ---")
        print(f"URL del reporte: {url_web}")
        print("--- Contenido para WhatsApp (copiar manualmente): ---")
        print(texto_clipboard)
        print(f"Error: {e}")


def main():
    print("--- [PUNTO DE CONTROL 1] INICIANDO GENERACIÓN DE REPORTE ---")
    perfiles = cargar_perfiles()
    parejas = cargar_parejas()
    config_liga = cargar_config_liga()

    # --- INICIO DEL CHEQUEO PREVIO DE DATOS ---

    # 1. Chequeos Críticos (errores que impiden continuar)
    if not perfiles or not perfiles[0].get('historial_temporada'):
        # Usamos messagebox.showerror para errores fatales
        messagebox.showerror(
            "Error Crítico de Datos", 
            "No se han encontrado perfiles o datos de jornadas en perfiles.json.\n\nEl programa no puede continuar."
        )
        print("ERROR: Faltan datos críticos en perfiles.json. Proceso abortado.")
        return # Salida forzosa

    # 2. Chequeos de Advertencia (el usuario decide si continuar)
    advertencias = []
    if not parejas:
        advertencias.append("- El archivo de parejas ('parejas.json') está vacío. La sección de parejas no se generará.")
    if not config_liga:
        advertencias.append("- El archivo de configuración ('liga_config.json') está vacío. La sección de premios no se generará.")
    
    # Si hemos encontrado advertencias, se lo mostramos al usuario
    if advertencias:
        mensaje_advertencia = "Se han detectado los siguientes problemas:\n\n" + "\n".join(advertencias) + "\n\n¿Deseas continuar igualmente?"
        
        # Usamos messagebox.askyesno, que devuelve True (Sí) o False (No)
        continuar = messagebox.askyesno("Advertencia de Datos", mensaje_advertencia)
        
        if not continuar:
            print("--- PROCESO CANCELADO POR EL USUARIO ---")
            return # Salida limpia si el usuario pulsa "No"

    # --- FIN DEL CHEQUEO PREVIO DE DATOS ---
    print("--- [PUNTO DE CONTROL 1] INICIANDO GENERACIÓN DE REPORTE ---")
    perfiles = cargar_perfiles(); parejas = cargar_parejas(); config_liga = cargar_config_liga()
    if not perfiles or not perfiles[0].get('historial_temporada'):
        print("ERROR: No hay datos de ninguna jornada."); return
    jornada_actual = perfiles[0]['historial_temporada'][-1]['jornada']
    try:
        with open('declaraciones.json', 'r', encoding='utf-8') as f: todas_declaraciones = json.load(f)
    except Exception: todas_declaraciones = []
    print(f"--- [PUNTO DE CONTROL 2] Datos cargados para la Jornada {jornada_actual} ---")
    
    # --- CORRECCIÓN CRÍTICA DE RANGOS (PUESTOS) ---
    # Como procesar_jornada.py a veces deja el puesto en 0, lo recalculamos aquí en memoria
    # para asegurar que el reporte salga perfecto.
    print("--- [CORRECCIÓN] Recalculando puestos en memoria para evitar errores de 0...")
    # Ordenamos por puntos totales de mayor a menor
    perfiles.sort(key=lambda p: p['historial_temporada'][-1]['puntos_totales'], reverse=True)
    # Asignamos el puesto correcto (1, 2, 3...)
    for i, perfil in enumerate(perfiles):
        perfil['historial_temporada'][-1]['puesto'] = i + 1
    # -----------------------------------------------

    # --- NUEVA LÍNEA: LLAMAMOS AL DETECTOR DE EVENTOS ---
    eventos_individuales_lista = detectar_eventos_individuales(perfiles)
    eventos_por_manager = agrupar_eventos_por_manager(eventos_individuales_lista)

    declaraciones_usadas = set()
    
    # 1. INTRODUCCIÓN (1ª llamada a la IA)
    print("--- [PUNTO DE CONTROL 3] Generando Introducción...")
    introduccion_ia, ids_usados_en_intro = generar_introduccion_semanal(perfiles, todas_declaraciones, jornada_actual)
    declaraciones_usadas.update(ids_usados_en_intro)

    # 2. CRÓNICAS INDIVIDUALES (OPTIMIZADO: 2ª llamada a la IA para TODAS)
    print("--- [PUNTO DE CONTROL 4] Generando Crónicas Individuales...")
    
    # ESTA LÍNEA ES LA CLAVE: Asegura que la variable siempre exista.
    reporte_individual_texto = f"## 🏆 CRÓNICA DE LA JORNADA {jornada_actual} 🏆\n\n"
    
    perfiles.sort(key=lambda p: p['historial_temporada'][-1]['puesto'])
    comentarista_del_dia = elegir_comentarista('cronica_individual')
    cronicas_generadas = {} # Se inicializa como diccionario vacío

    if comentarista_del_dia:
        reporte_individual_texto += f"##### Análisis Individual por: *{comentarista_del_dia['nombre_display']}*\n\n"
        # Llamamos a la función que genera las crónicas
        cronicas_generadas = generar_todas_las_cronicas(
            perfiles,
            todas_declaraciones,
            declaraciones_usadas,
            comentarista_del_dia,
            eventos_por_manager
        )
    else:
        # Mensaje por si no se encuentra un comentarista
        reporte_individual_texto += "_El comité de cronistas ha decidido tomarse un descanso esta jornada._\n\n"

    # Este bucle construye el texto final de las crónicas
    for perfil in perfiles:
        ultimo_historial = perfil['historial_temporada'][-1]
        # Obtenemos la crónica generada o un texto por defecto
        cronica_texto = cronicas_generadas.get(perfil['id_manager'], "El cronista no ha emitido comentarios sobre este mánager.")
        reporte_individual_texto += f"<details><summary><b>{ultimo_historial['puesto']}. {perfil['nombre_mister']}</b> ({ultimo_historial['puntos_totales']} pts) | Jornada: {ultimo_historial['puntos_jornada']} pts</summary><p><em>{cronica_texto}</em></p></details>\n"
        
    # 3. SECCIONES RESTANTES (Ahora con mucho margen de cuota)
    reporte_parejas_texto = calcular_clasificacion_parejas(perfiles, parejas, jornada_actual)
    reporte_sprints_texto = calcular_clasificacion_sprints(perfiles, jornada_actual)
    reporte_reparto_premios_texto = calcular_reparto_premios(perfiles, parejas, config_liga, jornada_actual)
    reporte_comentarios_ia_texto = generar_seccion_comentarios_ia(perfiles, parejas, config_liga, jornada_actual)

    # 4. ENSAMBLAJE FINAL
    reporte_markdown_completo = (introduccion_ia + "\n---\n" + reporte_individual_texto + "\n---\n" + reporte_parejas_texto + "\n---\n" + reporte_sprints_texto + reporte_reparto_premios_texto + reporte_comentarios_ia_texto)
    print("\n\n--- REPORTE FINAL GENERADO ---\n"); print(reporte_markdown_completo)

    # 5. PUBLICACIÓN
    url_reporte_real = actualizar_web_historico(jornada_actual, reporte_markdown_completo)
    
    try:
        repo = git.Repo(os.getcwd())
        repo.git.add(os.path.join(os.getcwd(), 'docs'))
        if repo.index.diff("HEAD"):
            print("INFO: Detectados cambios, subiendo a GitHub...")
            repo.index.commit(f"Actualización del reporte web - J{jornada_actual}")
            repo.remote(name='origin').push()
            print("✅ ¡ÉXITO! Repositorio actualizado.")
    except Exception as e:
        print(f"❌ ERROR al subir cambios con Git: {e}")

    # Pausa para que la web de GitHub se actualice
    delay_segundos = 220 
    print(f"\n--- [PAUSA] Esperando {delay_segundos} segundos para que la web se actualice...")
    time.sleep(delay_segundos)

    # Llamamos a nuestra nueva función "2 en 1"
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_GROUP_ID") # O TELEGRAM_CHAT_ID, según tu .env
    if TOKEN and CHAT_ID:
        asyncio.run(publicar_reporte_y_abrir_declaraciones(TOKEN, CHAT_ID, jornada_actual, url_reporte_real))
    else:
        print("ADVERTENCIA: No se pudo publicar el reporte en Telegram porque falta TOKEN o GROUP_ID en .env")

    # --- NUEVO PASO AUTOMÁTICO ---
    print("\n--- [PUNTO DE CONTROL FINAL] Limpiando y archivando declaraciones antiguas...")
    limpiar_declaraciones_antiguas()
    
    reporte_final_para_clipboard = f"Enlace al reporte web: {url_reporte_real}\n\n" + reporte_markdown_completo
    mostrar_ventana_final(reporte_final_para_clipboard, url_reporte_real)
    

def limpiar_nombre_para_ia(nombre):
    """ MEJORA: Elimina emojis y caracteres que puedan dar problemas a la IA. """
    return ''.join(c for c in nombre if c.isalnum() or c.isspace()).strip()

if __name__ == "__main__":
    main()