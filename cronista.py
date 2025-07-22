# cronista.py (Versión con lógica de prioridad)

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
    for root_id in threads:
        threads[root_id].sort(key=lambda d: d["timestamp"])
    return list(threads.values())

def _buscar_declaracion_reciente(manager_ids, todas_declaraciones, ids_ya_usadas):
    """Busca la declaración más reciente de una lista de mánagers, evitando las ya usadas."""
    fecha_limite = datetime.now() - timedelta(days=7)
    
    if not isinstance(manager_ids, list):
        manager_ids = [manager_ids]

    for d in sorted(todas_declaraciones, key=lambda x: x['timestamp'], reverse=True):
        if d.get("telegram_user_id") in manager_ids and \
           d.get("message_id") not in ids_ya_usadas and \
           datetime.fromisoformat(d['timestamp']) > fecha_limite:
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

def generar_cronica(perfil_manager, datos_actuales, nombre_rival, todas_declaraciones, ids_ya_usadas):
    """
    PRIORIDAD BAJA: Busca la última declaración disponible para un mánager.
    NOTA: La firma ha cambiado para recibir el contexto completo.
    """
    if not gemini_model: return "El cronista está afónico hoy."
    
    declaracion_reciente = _buscar_declaracion_reciente(
        perfil_manager.get("telegram_user_id"), 
        todas_declaraciones, 
        ids_ya_usadas
    )
    
    ultima_declaracion = declaracion_reciente['declaracion'] if declaracion_reciente else "ha mantenido un prudente silencio esta semana."

    nombre_mister = perfil_manager.get('nombre_mister', 'Mánager Desconocido')
    prompt = f"""
    Actúa como un cronista deportivo legendario y sarcástico.
    Analiza al mánager:
    - Nombre: {nombre_mister}
    - Puntos esta jornada: {datos_actuales.get('puntos_jornada', 0)}
    - Su última declaración disponible fue: "{ultima_declaracion}"

    Misión: Escribe una crónica breve (2-3 frases). Conecta su rendimiento con su última declaración.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar crónica para {nombre_mister}: {e}")
        return "El cronista se ha quedado sin palabras."

# --- OTRAS FUNCIONES DE CRONISTA (PUEDEN QUEDAR IGUAL O ADAPTARSE EN EL FUTURO) ---
# Por ahora, las funciones de Sprints y Parejas no usarán declaraciones para simplificar.
# Si en el futuro quieres añadirles contexto, seguirían el mismo patrón que 'generar_cronica'.

def generar_comentario_parejas(clasificacion):
    # Esta función se mantiene simple por ahora
    if not gemini_model: return "El cronista está estudiando las sinergias."
    # ... (código original de generar_comentario_parejas)
    top_parejas_texto = ""
    for i, pareja in enumerate(clasificacion[:3]):
        nombre = pareja.get('nombre', 'Pareja Desconocida')
        media = pareja.get('media', 0)
        top_parejas_texto += f"- Posición {i+1}: {nombre} (Media: {media} pts)\n"
    prompt = f"""Actúa como un analista experto. Te doy el top 3 de parejas. Analiza la situación brevemente (2-3 frases). {top_parejas_texto}"""
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar comentario de parejas: {e}")
        return "Una alianza poderosa se está forjando."

def generar_comentario_sprint(nombre_sprint, clasificacion, jornada_actual, inicio_sprint, fin_sprint):
    # Esta función se mantiene simple por ahora
    if not gemini_model: return "El cronista está tomando tiempos."
    # ... (código original de generar_comentario_sprint)
    estado_sprint = ... # Tu lógica para determinar el estado
    top_managers_texto = ""
    for i, manager in enumerate(clasificacion[:3]):
        nombre = manager.get('nombre', 'Mánager Desconocido')
        puntos = manager.get('puntos', 0)
        top_managers_texto += f"- Posición {i+1}: {nombre} ({puntos} pts)\n"
    prompt = f"""Actúa como comentarista de F1. Analiza el sprint '{nombre_sprint}'. Estado: {estado_sprint}. Clasificación: {top_managers_texto}."""
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar comentario de sprint: {e}")
        return "Los mánagers aprietan el acelerador."

# ... (El resto de tus funciones como crear_nombre_emergencia, etc., van aquí sin cambios)


# En cronista.py

# En cronista.py

# En cronista.py

def generar_nombre_equipo_ia_thread(perfiles_equipo, perfiles_todos, resultado_queue):
    """
    Genera el nombre del equipo, AHORA con los nuevos campos del perfil y
    con contexto sobre los títulos de toda la liga.
    """
    if not gemini_model:
        nombre, justificacion = crear_nombre_emergencia(perfiles_equipo)
        resultado_queue.put({"nombre_equipo": nombre, "justificacion": justificacion})
        return

    # --- 1. CÁLCULO DEL CONTEXTO GENERAL DE LA LIGA ---
    total_managers = len(perfiles_todos)
    managers_con_titulos = 0
    max_titulos = 0
    manager_mas_laureado = "Nadie"

    for perfil in perfiles_todos:
        nombre = perfil.get('nombre_mister', '')
        num_titulos = nombre.count('🏆')
        if num_titulos > 0:
            managers_con_titulos += 1
        if num_titulos > max_titulos:
            max_titulos = num_titulos
            manager_mas_laureado = nombre

    contexto_general_liga = (
        f"Contexto General de la Liga:\n"
        f"- Total de mánagers: {total_managers}.\n"
        f"- Mánagers que han ganado algún título: {managers_con_titulos}.\n"
        f"- El mánager más laureado es {manager_mas_laureado} con {max_titulos} títulos.\n"
    )

    # --- 2. PREPARACIÓN DE PERFILES INDIVIDUALES (CON LOS NUEVOS CAMPOS) ---
    descripcion_miembros = ""
    titulos_totales_pareja = 0
    for i, perfil in enumerate(perfiles_equipo):
        nombre = perfil.get('nombre_mister', 'Mánager Desconocido')
        num_titulos = nombre.count('🏆')
        titulos_totales_pareja += num_titulos
        
        descripcion_miembros += (
            f"\n--- Perfil del Mánager {i+1} ---\n"
            f"Nombre: {nombre} (Ha ganado {num_titulos} títulos)\n"
            f"Lema: {perfil.get('apodo_lema', 'Sin apodo')}\n"
            f"Estilo de Juego: {perfil.get('estilo_juego', 'No definido')}\n"
            f"Filosofía de Fichajes: {perfil.get('filosofia_fichajes', 'Impredecible')}\n"
            f"Jugador Fetiche: {perfil.get('jugador_fetiche', 'No tiene')}\n"
            f"Momento de Gloria: {perfil.get('momento_gloria', 'Aún por llegar')}\n"
            f"Peor Desastre: {perfil.get('peor_desastre', 'Ninguno conocido')}\n"
        )

    contexto_titulos_equipo = f"En total, este equipo acumula {titulos_totales_pareja} títulos entre sus miembros."

    # --- 3. CONSTRUCCIÓN DEL PROMPT MEJORADO ---
    prompt = f"""
    Actúa como un experto en marketing deportivo. Tu tarea es bautizar a un nuevo equipo de una liga fantasy.

    {contexto_general_liga}
    A continuación, te doy los perfiles completos de los mánagers que forman este equipo.
    {descripcion_miembros}
    
    {contexto_titulos_equipo}
    Analiza la combinación de sus características (estilos, filosofías, lemas, etc.) y su palmarés COMPARÁNDOLO con el contexto general de la liga. 
    - Si sus títulos son significativos para la liga, resáltalo.
    - Si son aspirantes sin títulos en una liga con pocos campeones, enfócalo en su ambición.
    Crea un nombre de equipo ingenioso y una justificación que demuestre que entiendes su estatus dentro de la competición.
    
    Tu respuesta DEBE ser únicamente un objeto JSON con el siguiente formato:
    {{
      "nombre_equipo": "El Nombre Que Inventes",
      "justificacion": "Una explicación breve y creativa de por qué elegiste ese nombre, usando el contexto general."
    }}
    """
    
    print("     -> Pidiendo a la IA que bautice a este equipo (con contexto)...")
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
    """
    Crea un nombre de equipo único combinando los nombres de los mánagers.
    """
    nombres = []
    for perfil in perfiles:
        primer_nombre = perfil.get('nombre_mister', 'Manager').split()[0]
        # Limpiamos el nombre de posibles emojis para que sea más legible
        nombre_limpio = ''.join(c for c in primer_nombre if c.isalnum())
        nombres.append(nombre_limpio if nombre_limpio else "Míster")
    
    nombre_base = " y ".join(nombres)
    sufijo = random.choice(["United", "FC", "Team", "CF", "Racing"])
    
    nombre_final = f"{nombre_base} {sufijo}"
    justificacion = "El cronista estaba afónico, así que los mánagers fundaron su propio club de emergencia."
    
    return nombre_final, justificacion
# Pega esto al final de tu archivo cronista.py

## --- NUEVA FUNCIÓN PARA COMENTAR PREMIOS --- ##
def generar_comentario_premio(nombre_premio, ganadores, jornada_actual, es_final):
    """
    Genera un comentario del cronista sobre un premio específico y sus ganadores.

    Args:
        nombre_premio (str): El nombre del premio (e.g., "Pareja de Oro").
        ganadores (list): Una lista con los nombres de los mánagers ganadores.
        jornada_actual (int): La jornada actual de la liga.
        es_final (bool): True si el premio es definitivo (fin de liga o sprint).
    """
    global gemini_model # Es buena práctica asegurarse de que la variable global está accesible
    if not gemini_model:
        return "El cronista guarda silencio, impresionado por la hazaña."

    # Adaptar el tono si el premio es definitivo o provisional
    contexto_temporal = "Este es el veredicto final. ¡Ya no hay vuelta atrás!" if es_final else f"En la jornada {jornada_actual}, esta es la situación, pero todo puede cambiar."
    
    # Formatear la lista de ganadores para el prompt
    nombres_ganadores = " y ".join(ganadores)

    prompt = f"""
    Actúa como un cronista deportivo legendario, analizando el cuadro de honor de una liga fantasy.
    
    Premio en disputa: "{nombre_premio}"
    Ganador(es) actuales: {nombres_ganadores}
    Contexto: {contexto_temporal}

    Escribe un comentario muy breve (1-2 frases ingeniosas) sobre este logro. 
    - Si es un premio final, habla de su legado, de cómo serán recordados. Sé épico o sarcástico.
    - Si es provisional, comenta sobre si podrán mantener la posición, la presión que sienten o si es un espejismo.
    
    Sé directo y memorable.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar comentario para el premio {nombre_premio}: {e}")
        return f"El cronista se ha quedado sin palabras ante el logro de {nombres_ganadores}."
# Pega estas dos nuevas funciones al final de tu archivo cronista.py

def generar_comentario_parejas(clasificacion):
    """
    Genera un comentario analizando la clasificación por parejas.
    Recibe la lista completa de la clasificación.
    """
    global gemini_model
    if not gemini_model or not clasificacion:
        return "El cronista está estudiando las sinergias de los equipos."

    # Preparamos los datos del top 3 para la IA
    top_parejas_texto = ""
    for i, pareja in enumerate(clasificacion[:3]): # Tomamos el top 3
        nombre = pareja.get('nombre', 'Pareja Desconocida')
        media = pareja.get('media', 0)
        top_parejas_texto += f"- Posición {i+1}: {nombre} (Media: {media} pts)\n"

    prompt = f"""
    Actúa como un analista deportivo experto en química de equipo y estrategia, como si fueras Axel Torres.
    Te proporciono el top 3 de la clasificación por parejas de una liga fantasy.

    Clasificación actual:
    {top_parejas_texto}

    Analiza la situación. Tu comentario debe ser breve (2-3 frases) y con carácter.
    - Si la diferencia de puntos entre el primero y el segundo es pequeña, habla de la intensa rivalidad y la tensión.
    - Si el líder tiene una gran ventaja, comenta sobre su aplastante dominio y si alguien podrá alcanzarles.
    - Menciona por su nombre al menos a los dos primeros equipos.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar comentario de parejas: {e}")
        return "Una alianza poderosa se está forjando, pero el cronista aún no descifra cuál."

# REEMPLAZA ESTA FUNCIÓN EN cronista.py

def generar_comentario_sprint(nombre_sprint, clasificacion, jornada_actual, inicio_sprint, fin_sprint):
    """
    Genera un comentario analizando la clasificación de un sprint.
    Ahora es consciente del progreso del sprint.
    """
    global gemini_model
    if not gemini_model or not clasificacion:
        return "El cronista está tomando tiempos para ver quién es el más rápido."

    # Determinar el estado del sprint
    if jornada_actual >= fin_sprint:
        estado_sprint = f"Ha finalizado en la jornada {jornada_actual}. ¡Este es el resultado definitivo!"
    elif jornada_actual == inicio_sprint:
        estado_sprint = f"Acaba de comenzar en la jornada {jornada_actual}. ¡Se apaga el semáforo!"
    else:
        estado_sprint = f"Está en curso en la jornada {jornada_actual} de un total de {fin_sprint - inicio_sprint + 1} jornadas."

    top_managers_texto = ""
    for i, manager in enumerate(clasificacion[:3]):
        nombre = manager.get('nombre', 'Mánager Desconocido')
        puntos = manager.get('puntos', 0)
        top_managers_texto += f"- Posición {i+1}: {nombre} ({puntos} pts)\n"

    prompt = f"""
    Actúa como un comentarista de Fórmula 1, analizando una carrera corta (un sprint). Eres rápido, incisivo y te fijas en el estado de forma.
    Te proporciono el top 3 de la clasificación del sprint "{nombre_sprint}".

    Estado del Sprint: {estado_sprint}

    Clasificación actual del Sprint:
    {top_managers_texto}

    Genera un comentario de 2 frases sobre la situación:
    - Si acaba de empezar, habla de quién ha salido mejor y quiénes son los primeros líderes.
    - Si está en curso, analiza quién mantiene el ritmo y si hay posibles remontadas.
    - Si ha finalizado, felicita al ganador y comenta sobre su rendimiento en este tramo.
    Sé siempre consciente del contexto (si ha terminado o no) para no dar un veredicto final antes de tiempo.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar comentario de sprint: {e}")
        return "Los mánagers aprietan el acelerador, pero el cronista aún no tiene claro quién ganará la carrera."

# En cronista.py

# --- LISTA DE PALABRAS CLAVE (EL "RADAR DEL SALSEO") ---
# Esta lista es fundamental. Puedes y debes ampliarla con el tiempo.
# Incluye abreviaturas, jerga, etc.

# Reemplaza tu función generar_introduccion_semanal entera por esta:

def generar_introduccion_semanal(perfiles, todas_declaraciones, jornada_actual):
    """
    PRIORIDAD ALTA: Busca conversaciones jugosas.
    DEVUELVE: una tupla (texto_generado, set_de_ids_usados)
    """
    if not gemini_model:
        return ("## 🎙️ El Vestuario Habla\n\n_El Cronista está afónico._\n", set())

    # Ya no necesita leer el archivo, recibe 'todas_declaraciones' como argumento
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

def _find_root_message(message_id, declarations_map):
    """Navega hacia atrás en una conversación para encontrar el mensaje raíz."""
    current_id = message_id
    while True:
        message = declarations_map.get(current_id)
        if not message or not message.get("reply_to_message_id"):
            break
        parent_id = message["reply_to_message_id"]
        if parent_id not in declarations_map:
            break
        current_id = parent_id
    return current_id

def _group_declarations_into_threads(all_declarations):
    """Agrupa una lista de declaraciones en hilos de conversación."""
    declarations_map = {d["message_id"]: d for d in all_declarations if d.get("message_id")}
    threads = {}
    for declaration in all_declarations:
        if not declaration.get("message_id"):
            continue
        root_id = _find_root_message(declaration["message_id"], declarations_map)
        if root_id not in threads:
            threads[root_id] = []
        threads[root_id].append(declaration)
    for root_id in threads:
        threads[root_id].sort(key=lambda d: d["timestamp"])
    return list(threads.values())

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