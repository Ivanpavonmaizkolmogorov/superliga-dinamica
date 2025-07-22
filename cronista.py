# cronista.py (Versión con lógica de prioridad)
import yaml
import json
import random
import re
from datetime import datetime, timedelta
from config import GEMINI_API_KEY
import google.generativeai as genai

# --- INICIALIZACIÓN Y CONFIGURACIÓN ---
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("INFO: Modelo de IA Gemini configurado correctamente.")
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo configurar la API de Gemini. Error: {e}")
else:
    print("ADVERTENCIA: No se encontró GEMINI_API_KEY.")

PALABRAS_CLAVE_INTERES = [
    'ficho', 'fichaje', 'oferta', 'ofrezco', 'vendo', 'venta', 'compro', 
    'compra', 'clausula', 'clausulazo', 'mercado', 'millones', 'pasta', 
    'puja', 'pujar', 'vendido', 'paquete', 'manco', 'robo', 'tongo', 'suerte', 
    'lloron', 'malo', 'malisimo', 'gano', 'gane', 'reviento', 'paliza', 'lider',
    'lesion', 'lesionado', 'roto', 'banquillo', 'alineacion', 'tactica'
]

PERSONALIDADES = {}
try:
    with open('comentaristas.yml', 'r', encoding='utf-8') as f:
        PERSONALIDADES = yaml.safe_load(f).get('comentaristas', {})
    print(f"INFO (Cronista): Cargados {len(PERSONALIDADES)} comentaristas desde 'comentaristas.yml'.")
except FileNotFoundError:
    print("ERROR (Cronista): El archivo 'comentaristas.yml' no fue encontrado.")
except Exception as e:
    print(f"ERROR (Cronista): No se pudo leer o procesar 'comentaristas.yml'. Error: {e}")

def limpiar_nombre_para_ia(nombre):
    """ Elimina emojis y caracteres que puedan dar problemas a la IA. """
    if not isinstance(nombre, str):
        return ""
    # Mantenemos letras, números, espacios y guiones bajos/medios.
    return ''.join(c for c in nombre if c.isalnum() or c.isspace() or c in ['-', '_']).strip()
# --- FUNCIÓN CLAVE: EL SELECTOR INTELIGENTE ---

def elegir_comentarista(contexto_actual):
    if not PERSONALIDADES: return None
    candidatos = []
    pesos = []
    for key, data in PERSONALIDADES.items():
        if contexto_actual in data.get("roles_asignados", {}):
            candidatos.append(data)
            pesos.append(data["roles_asignados"][contexto_actual])
    if not candidatos: return None
    return random.choices(candidatos, weights=pesos, k=1)[0]
# --- FUNCIONES AUXILIARES PARA LA LÓGICA DE PRIORIDAD ---

def _find_root_message(message_id, declarations_map):
    current_id = message_id
    while True:
        message = declarations_map.get(current_id)
        if not message or not message.get("reply_to_message_id"): break
        parent_id = message["reply_to_message_id"]
        if parent_id not in declarations_map: break
        current_id = parent_id
    return current_id

def _group_declarations_into_threads(all_declarations):
    declarations_map = {d["message_id"]: d for d in all_declarations if d.get("message_id")}
    threads = {}
    for declaration in all_declarations:
        if not declaration.get("message_id"): continue
        root_id = _find_root_message(declaration["message_id"], declarations_map)
        if root_id not in threads: threads[root_id] = []
        threads[root_id].append(declaration)
    for root_id in threads: threads[root_id].sort(key=lambda d: d["timestamp"])
    return list(threads.values())

def _buscar_declaracion_reciente(manager_ids, todas_declaraciones, ids_ya_usadas):
    fecha_limite = datetime.now() - timedelta(days=7)
    if not isinstance(manager_ids, list): manager_ids = [manager_ids]
    for d in sorted(todas_declaraciones, key=lambda x: x['timestamp'], reverse=True):
        if d.get("telegram_user_id") in manager_ids and d.get("message_id") not in ids_ya_usadas and datetime.fromisoformat(d['timestamp']) > fecha_limite:
            return d
    return None

# --- FUNCIONES DE GENERACIÓN DE TEXTO (ACTUALIZADAS) ---

def generar_introduccion_semanal(perfiles, todas_declaraciones, jornada_actual):
    """
    PRIORIDAD ALTA: Busca conversaciones jugosas.
    DEVUELVE: una tupla (texto_generado, set_de_ids_usados)
    """
    if not gemini_model:
        return ("## 🎙️ El Vestuario Habla\n\n_El Cronista está afónico._\n", set())

    todos_los_hilos = _group_declarations_into_threads(todas_declaraciones)
    hilos_relevantes = []
    ids_usados = set()
    fecha_limite = datetime.now() - timedelta(days=7)

    for hilo in todos_los_hilos:
        actividad_reciente = any(datetime.fromisoformat(d['timestamp']) > fecha_limite for d in hilo)
        if not actividad_reciente: continue

        if any(palabra in d.get('declaracion', '').lower() for d in hilo for palabra in PALABRAS_CLAVE_INTERES):
            hilos_relevantes.append(hilo)
            for d in hilo: ids_usados.add(d['message_id'])

    if not hilos_relevantes:
        return ("## 🎙️ El Vestuario Habla\n\n_Semana de calma tensa._\n", set())

    transcripcion = ""
    for i, hilo in enumerate(hilos_relevantes):
        transcripcion += f"--- Hilo de Conversación {i+1} ---\n"
        for d in hilo:
            prefijo = "  -> (en respuesta) " if d.get("reply_to_message_id") else ""
            transcripcion += f"{prefijo}- {d['nombre_mister']}: \"{d['declaracion']}\"\n"
        transcripcion += "---\n\n"

    lider_actual = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puesto'])[0]
    prompt = f"""
    Eres el Editor Jefe de un programa deportivo. Tu misión es escribir una introducción impactante para el reporte de la Jornada {jornada_actual}.
    Te presento las conversaciones más "calientes" de la semana. Los mensajes con "->" son respuestas.
    {transcripcion}
    Dato clave: El líder actual es {lider_actual['nombre_mister']}.
    Elige la conversación más jugosa y realiza dos tareas:
    1.  **Escribe un TÍTULO DE LA JORNADA:** Una frase corta y potente.
    2.  **Escribe un PÁRRAFO DE ANÁLISIS:** Comenta el hilo más significativo.
    Tu respuesta debe tener el formato:
    TÍTULO: [Tu título aquí]
    ANÁLISIS: [Tu párrafo de análisis aquí]
    """
    try:
        print(" -> Generando introducción (Prioridad Alta)...")
        response = gemini_model.generate_content(prompt)
        titulo = "El Vestuario Habla"
        analisis = response.text
        match_titulo = re.search(r"TÍTULO: (.*)", response.text, re.IGNORECASE)
        match_analisis = re.search(r"ANÁLISIS: (.*)", response.text, re.IGNORECASE | re.DOTALL)
        if match_titulo: titulo = match_titulo.group(1).strip()
        if match_analisis: analisis = match_analisis.group(1).strip()
        return (f"## 🎙️ {titulo}\n\n_{analisis}_\n", ids_usados)
    except Exception as e:
        print(f"Error al generar la introducción de la IA: {e}")
        return ("## 🎙️ El Vestuario Habla\n\n_El Cronista tuvo problemas técnicos._\n", set())

def generar_cronica(perfil_manager, datos_actuales, nombre_rival, todas_declaraciones, ids_ya_usadas, comentarista):
    # ANTES: Tenía un prompt fijo y se llamaba en bucle.
    # AHORA: Recibe un 'comentarista' elegido una sola vez fuera del bucle para dar coherencia.
    if not gemini_model or not comentarista: return "El cronista está afónico hoy."
    
    declaracion_reciente = _buscar_declaracion_reciente(perfil_manager.get("telegram_user_id"), todas_declaraciones, ids_ya_usadas)
    ultima_declaracion = declaracion_reciente['declaracion'] if declaracion_reciente else "ha mantenido un prudente silencio esta semana."
    nombre_mister = perfil_manager.get('nombre_mister', 'Desconocido')

    prompt = (
        f"{comentarista['prompt_base']}\n\n"
        f"Analiza al mánager: {nombre_mister}\n"
        f"Puntos esta jornada: {datos_actuales.get('puntos_jornada', 0)}\n"
        f"Su última declaración: \"{ultima_declaracion}\"\n\n"
        f"Misión: Escribe una crónica breve (2-3 frases), conectando su rendimiento con su declaración."
    )
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar crónica para {nombre_mister}: {e}")
        return "El cronista se ha quedado sin palabras."

# --- OTRAS FUNCIONES DE CRONISTA (PUEDEN QUEDAR IGUAL O ADAPTARSE EN EL FUTURO) ---
# Por ahora, las funciones de Sprints y Parejas no usarán declaraciones para simplificar.
# Si en el futuro quieres añadirles contexto, seguirían el mismo patrón que 'generar_cronica'.

def generar_comentario_premio(nombre_premio, ganadores, jornada_actual, es_final):
    comentarista = elegir_comentarista('premio')
    if not gemini_model or not comentarista: return "_El cronista guarda silencio._"
    contexto = "de forma definitiva" if es_final else f"provisionalmente en la jornada {jornada_actual}"
    nombres = " y ".join([limpiar_nombre_para_ia(g) for g in ganadores])
    prompt = (f"{comentarista['prompt_base']}\n\nNarra la entrega del premio '{nombre_premio}'. El ganador es '{nombres}' y lo ha conseguido {contexto}. Comenta este logro de forma breve y memorable.")
    print(f" -> Pidiendo comentario para '{nombre_premio}' a '{comentarista['nombre_display']}'...")
    try: return f"_{gemini_model.generate_content(prompt).text.strip()}_"
    except Exception as e: print(f"ERROR en IA para Premio '{nombre_premio}': {e}"); return f"_{comentarista['nombre_display']} aplaude el logro de {nombres}._"
    

def generar_comentario_sprint(nombre_sprint, clasificacion, jornada_actual, inicio_sprint, fin_sprint):
    comentarista = elegir_comentarista('sprint_analisis')
    if not gemini_model or not clasificacion or not comentarista: return "_El cronista toma tiempos._"
    if jornada_actual >= fin_sprint: estado_sprint = "y la carrera ha finalizado"
    elif jornada_actual == inicio_sprint: estado_sprint = "y la carrera acaba de empezar"
    else: estado_sprint = "y la carrera está en pleno apogeo"
    lider = clasificacion[0]
    narrativa = f"En el sprint '{nombre_sprint}', el mánager '{limpiar_nombre_para_ia(lider['nombre'])}' va en cabeza con {lider['puntos']} puntos {estado_sprint}."
    prompt = (f"{comentarista['prompt_base']}\n\nTe resumo la situación de la carrera: {narrativa}. Genera un comentario de 2 frases.")
    print(f" -> Pidiendo análisis de sprint a '{comentarista['nombre_display']}'...")
    try:
        response = gemini_model.generate_content(prompt)
        return f"_{response.text.strip()}_"
    except Exception as e:
        print(f"ERROR en IA para Sprint: {e}"); return "_Los mánagers aprietan el acelerador._"


# En cronista.py

# En cronista.py

# En cronista.py

def generar_nombre_equipo_ia_thread(perfiles_equipo, perfiles_todos, resultado_queue):
    # ANTES: Tenía su propio prompt.
    # AHORA: Usa el selector con el contexto 'bautizo_equipo'.
    comentarista = elegir_comentarista('bautizo_equipo')
    if not gemini_model or not comentarista:
        nombre, justificacion = crear_nombre_emergencia(perfiles_equipo)
        resultado_queue.put({"nombre_equipo": nombre, "justificacion": justificacion})
        return
    
    contexto_general_liga = f"Contexto de la Liga: {len(perfiles_todos)} mánagers en total."
    descripcion_miembros = "\n".join(
        f"--- Perfil Mánager {i+1} ---\n"
        f"Nombre: {p.get('nombre_mister', 'N/A')}\n"
        f"Lema: {p.get('apodo_lema', 'N/A')}\n"
        f"Estilo: {p.get('estilo_juego', 'N/A')}\n"
        for i, p in enumerate(perfiles_equipo)
    )

    prompt = (
        f"{comentarista['prompt_base']}\n\n"
        f"{contexto_general_liga}\n"
        f"Perfiles del equipo a bautizar:\n{descripcion_miembros}\n\n"
        "Analiza la combinación de sus perfiles y crea un nombre ingenioso y una justificación creativa."
    )
    print(f" -> Pidiendo bautizo de equipo a '{comentarista['nombre_display']}'...")
    try:
        response = gemini_model.generate_content(prompt)
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        ai_json = json.loads(clean_response)
        resultado_queue.put(ai_json)
    except Exception as e:
        print(f"     -> ERROR en el hilo de la IA: {e}")
        nombre, justificacion = crear_nombre_emergencia(perfiles_equipo)
        resultado_queue.put({"nombre_equipo": nombre, "justificacion": justificacion})

def crear_nombre_emergencia(perfiles):
    nombres = [p.get('nombre_mister', 'Manager').split()[0] for p in perfiles]
    return f"{' & '.join(nombres)} United", "El cronista estaba afónico, así que fundaron su propio club."

## --- NUEVA FUNCIÓN PARA COMENTAR PREMIOS --- ##
# --- 3. COMENTARIO DE PREMIOS ---
# --- COMENTARIO DE PREMIOS (MEJORADO) ---


def generar_comentario_parejas(clasificacion):
    comentarista = elegir_comentarista('parejas_analisis')
    if not gemini_model or not clasificacion or not comentarista: return "_El cronista estudia las sinergias._"
    if len(clasificacion) > 1:
        narrativa = f"El equipo '{limpiar_nombre_para_ia(clasificacion[0]['nombre'])}' lidera con {clasificacion[0]['media']} puntos, mientras que '{limpiar_nombre_para_ia(clasificacion[1]['nombre'])}' le sigue con {clasificacion[1]['media']}."
    else:
        narrativa = f"El equipo '{limpiar_nombre_para_ia(clasificacion[0]['nombre'])}' lidera en solitario con {clasificacion[0]['media']} puntos."
    prompt = (f"{comentarista['prompt_base']}\n\nResume la situación por parejas: {narrativa}. Analiza brevemente.")
    print(f" -> Pidiendo análisis de parejas a '{comentarista['nombre_display']}'...")
    try: return f"_{gemini_model.generate_content(prompt).text.strip()}_"
    except Exception as e: print(f"ERROR en IA para Parejas: {e}"); return "_Una alianza poderosa se está forjando._"
    



# En cronista.py

# --- LISTA DE PALABRAS CLAVE (EL "RADAR DEL SALSEO") ---
# Esta lista es fundamental. Puedes y debes ampliarla con el tiempo.
# Incluye abreviaturas, jerga, etc.

# Reemplaza tu función generar_introduccion_semanal entera por esta:


    




# --- BLOQUE DE PRUEBA UNITARIA ---
# Este código solo se ejecuta si lanzamos este archivo directamente
""" if __name__ == '__main__':
    print("--- INICIANDO PRUEBA UNITARIA DE LA INTRODUCCIÓN ---")
    
    # 1. Cargamos las claves desde el .env (necesario para la IA)
    from dotenv import load_dotenv
    load_dotenv()
    
    # 2. Simulamos los datos que recibiría la función
    #    Cargamos los perfiles reales para que la prueba sea realista
    try:
        with open('perfiles.json', 'r', encoding='utf-8') as f:
            perfiles_de_prueba = json.load(f)
        jornada_de_prueba = 4 # Pon un número de jornada cualquiera
        
        # 3. Llamamos a la función que queremos probar
        introduccion = generar_introduccion_semanal(perfiles_de_prueba, jornada_de_prueba)
        
        # 4. Imprimimos el resultado
        print("\n--- RESULTADO GENERADO ---\n")
        print(introduccion)
        print("\n--- FIN DE LA PRUEBA ---")

    except FileNotFoundError:
        print("ERROR: Para probar, asegúrate de que 'perfiles.json' y 'declaraciones.json' existen en esta carpeta.")
    except Exception as e:
        print(f"La prueba ha fallado con un error: {e}") """