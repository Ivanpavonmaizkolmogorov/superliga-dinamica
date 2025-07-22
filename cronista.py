# cronista.py (Versión Final con Nombres de Emergencia y Detección de Títulos)

import json
import random
import google.generativeai as genai
from config import GEMINI_API_KEY
import re
from datetime import datetime, timedelta # <-- ¡AQUÍ ESTÁ LA SOLUCIÓN!


# --- INICIALIZACIÓN DEL MODELO DE IA ---
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("INFO: Modelo de IA Gemini configurado correctamente.")
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo configurar la API de Gemini. Error: {e}")
else:
    print("ADVERTENCIA: No se encontró GEMINI_API_KEY. Las crónicas no se generarán.")




# REEMPLAZA ESTA FUNCIÓN en tu archivo cronista.py

# Asegúrate de que tienes 'import json' al principio de tu archivo cronista.py
import json

# ... (resto de tus importaciones y la configuración de gemini_model) ...

def generar_cronica(perfil_manager, datos_actuales, nombre_rival="Nadie en particular"):
    """
    Genera una crónica personalizada para un mánager, usando un perfil enriquecido
    y AHORA también sus últimas declaraciones de Telegram.
    """
    if not gemini_model: 
        return "El cronista está afónico hoy. No hay crónica."

    # --- INICIO DE LA MODIFICACIÓN: LEER DECLARACIONES.JSON ---
    
    ultima_declaracion = "Este mánager ha optado por un prudente silencio esta semana."
    telegram_user_id = perfil_manager.get("telegram_user_id")

    if telegram_user_id:
        try:
            with open('declaraciones.json', 'r', encoding='utf-8') as f:
                declaraciones = json.load(f)
            
            # Buscamos la última declaración de este usuario específico recorriendo la lista al revés
            for declaracion in reversed(declaraciones):
                if declaracion.get("telegram_user_id") == telegram_user_id:
                    ultima_declaracion = declaracion["declaracion"]
                    break
        except (FileNotFoundError, json.JSONDecodeError):
            # Si el archivo no existe o está vacío, no hacemos nada y usamos el mensaje por defecto.
            pass
            
    # --- FIN DE LA MODIFICACIÓN ---

    nombre_mister = perfil_manager.get('nombre_mister', 'Mánager Desconocido')
    
    num_titulos = nombre_mister.count('🏆')
    contexto_titulos = f"Tiene {num_titulos} títulos en su palmarés." if num_titulos > 0 else "Aún no ha ganado ningún título."

    estilo = perfil_manager.get('estilo_juego') or "No definido"
    fetiche = perfil_manager.get('jugador_fetiche') or "No tiene"
    fichajes = perfil_manager.get('filosofia_fichajes') or "Impredecible"

    # --- INICIO DE LA MODIFICACIÓN: PROMPT MEJORADO ---

    prompt = f"""
    Actúa como un cronista deportivo legendario, ingenioso y con memoria (estilo Maldini o Axel Torres). Tienes acceso a todo: datos, perfiles y las declaraciones del vestuario (el chat de la liga).
    
    Aquí tienes la ficha completa del mánager sobre el que vas a comentar:
    - Nombre: {nombre_mister}
    - Palmarés: {contexto_titulos}
    - Lema: {perfil_manager.get('apodo_lema') or "Sin lema conocido"}
    - Su Estilo de Juego: {estilo}
    - Su Jugador Fetiche: {fetiche}
    - Su Filosofía de Fichajes: {fichajes}
    - Su Rival Histórico: {nombre_rival}
    - Momento de Gloria recordado: {perfil_manager.get('momento_gloria') or "Aún por llegar"}
    - Peor Desastre recordado: {perfil_manager.get('peor_desastre') or "Prefiere no recordarlo"}

    Datos de esta jornada:
    - Puntos conseguidos: {datos_actuales.get('puntos_jornada', 0)}
    - Posición actual en la liga: {datos_actuales.get('puesto', 'N/A')}

    DECLARACIÓN MÁS RECIENTE DEL MÁNAGER (obtenida del chat de la liga):
    - "{ultima_declaracion}"

    Misión: Escribe un comentario breve y punzante (2-3 frases) sobre su rendimiento.
    Debes CONECTAR OBLIGATORIAMENTE los datos de la jornada con algún dato de su ficha personal O, preferiblemente, con su última declaración.
    - Si su declaración fue arrogante y pinchó, resáltalo. ("Sus palabras prometían un huracán, pero en el campo solo vimos una llovizna de 40 puntos").
    - Si se quejó de un jugador y ese jugador le dio puntos, sé irónico. ("Parece que el 'paquete' del que hablaba sí sabía cómo encontrar la red").
    - Si su filosofía es "tirar de cartera" y en el chat dijo que "el dinero no da la felicidad", pero ganó, comenta la ironía.
    Sé creativo, específico y memorable.
    """
    
    # --- FIN DE LA MODIFICACIÓN ---

    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar crónica para {nombre_mister}: {e}")
        return "El cronista se ha quedado sin palabras por alguna razón..."


def generar_nombre_equipo_ia_thread(perfiles_equipo, resultado_queue):
    """
    Genera el nombre del equipo. Si la IA falla, crea un nombre de emergencia único.
    Ahora también informa a la IA sobre los títulos de los mánagers.
    """
    if not gemini_model:
        nombre, justificacion = crear_nombre_emergencia(perfiles_equipo)
        resultado_queue.put({"nombre_equipo": nombre, "justificacion": justificacion})
        return

    descripcion_miembros = ""
    titulos_totales = 0
    for i, perfil in enumerate(perfiles_equipo):
        nombre = perfil.get('nombre_mister', 'Mánager Desconocido')
        num_titulos = nombre.count('🏆')
        titulos_totales += num_titulos
        
        descripcion_miembros += (
            f"\n--- Perfil del Mánager {i+1} ---\n"
            f"Nombre: {nombre} (Ha ganado {num_titulos} títulos)\n"
            f"Lema: {perfil.get('apodo_lema', 'Sin apodo')}\n"
            f"Momento de Gloria: {perfil.get('momento_gloria', 'Aún por llegar')}\n"
            f"Peor Desastre: {perfil.get('peor_desastre', 'Ninguno conocido')}\n"
        )

    contexto_titulos_equipo = f"En total, este equipo acumula {titulos_totales} títulos entre sus miembros."

    prompt = f"""
    Actúa como un experto en marketing deportivo y un periodista creativo. Tu tarea es bautizar a un nuevo equipo de una liga fantasy.
    
    A continuación, te doy los perfiles de los mánagers que forman este equipo.
    {descripcion_miembros}
    
    {contexto_titulos_equipo}
    Analiza sus perfiles, nombres y, sobre todo, su palmarés combinado. Basándote en la combinación de sus características, crea un nombre de equipo que sea ingenioso, potente o divertido y que haga referencia a su experiencia (o a la falta de ella).
    
    Tu respuesta DEBE ser únicamente un objeto JSON con el siguiente formato:
    {{
      "nombre_equipo": "El Nombre Que Inventes",
      "justificacion": "Una explicación breve y creativa de por qué elegiste ese nombre, conectando las características y los títulos de los mánagers."
    }}
    """
    
    print("    -> Pidiendo a la IA que bautice a este equipo... (hilo en ejecución)")
    try:
        response = gemini_model.generate_content(prompt)
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        ai_json = json.loads(clean_response)
        resultado_queue.put(ai_json)
    except Exception as e:
        print(f"    -> ERROR en el hilo de la IA: {e}")
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

def generar_introduccion_semanal(perfiles, jornada_actual):
    """
    Genera una introducción semanal, agrupando las declaraciones en conversaciones
    para darle un contexto más rico a la IA.
    """
    if not gemini_model:
        return ""

    # --- 1. CARGAR Y AGRUPAR DECLARACIONES EN HILOS DE CONVERSACIÓN ---
    try:
        with open('declaraciones.json', 'r', encoding='utf-8') as f:
            todas_las_declaraciones = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "## 🎙️ El Vestuario Habla\n\n_Semana de reflexión en la liga. Silencio en los banquillos._\n"

    # Usamos la nueva función para agrupar todo en hilos
    todos_los_hilos = _group_declarations_into_threads(todas_las_declaraciones)
    
    # --- 2. FILTRAR HILOS RELEVANTES DE LA ÚLTIMA SEMANA ---
    hilos_relevantes = []
    fecha_limite = datetime.now() - timedelta(days=7)

    for hilo in todos_los_hilos:
        hilo_es_relevante = False
        actividad_reciente = False
        
        for declaracion in hilo:
            # Comprobamos si alguna declaración del hilo es reciente
            if datetime.fromisoformat(declaracion['timestamp']) > fecha_limite:
                actividad_reciente = True
            
            # Comprobamos si alguna declaración tiene palabras clave
            texto_declaracion = declaracion.get('declaracion', '').lower()
            if any(palabra in texto_declaracion for palabra in PALABRAS_CLAVE_INTERES):
                hilo_es_relevante = True

        if hilo_es_relevante and actividad_reciente:
            hilos_relevantes.append(hilo)

    if not hilos_relevantes:
        return "## 🎙️ El Vestuario Habla\n\n_Semana de calma tensa. Nadie ha querido mostrar sus cartas._\n"

    # --- 3. PREPARAR LA TRANSCRIPCIÓN CON FORMATO DE CONVERSACIÓN ---
    transcripcion = ""
    for i, hilo in enumerate(hilos_relevantes):
        transcripcion += f"--- Hilo de Conversación {i+1} ---\n"
        for d in hilo:
            # Determinamos si es una respuesta para añadir contexto visual
            prefijo = "  -> (en respuesta) " if d.get("reply_to_message_id") else ""
            transcripcion += f"{prefijo}- {d['nombre_mister']}: \"{d['declaracion']}\"\n"
        transcripcion += "---\n\n"

    # --- 4. CONSTRUCCIÓN DEL PROMPT MEJORADO PARA LA IA ---
    lider_actual = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puesto'])[0]
    
    prompt = f"""
    Eres el Editor Jefe de un programa deportivo sobre una liga fantasy. Eres agudo y experto en detectar "salseo".
    Tu misión es escribir una introducción impactante para el reporte de la Jornada {jornada_actual}.

    A continuación, te presento las conversaciones más "calientes" de la semana, agrupadas en hilos. Los mensajes con "->" son respuestas a otros.
    {transcripcion}
    Dato clave: El líder actual es {lider_actual['nombre_mister']}.

    Analiza estas conversaciones. No comentes cada una, elige la más jugosa (un pique, una negociación, una queja que quedó en nada...).
    Realiza estas dos tareas:
    1.  **Escribe un TÍTULO DE LA JORNADA:** Una frase corta y potente que resuma el drama o la polémica principal.
    2.  **Escribe un PÁRRAFO DE ANÁLISIS:** Comenta el hilo más significativo. Explica la interacción entre los mánagers.

    Tu respuesta debe tener el formato exacto:
    TÍTULO: [Tu título aquí]
    ANÁLISIS: [Tu párrafo de análisis aquí]
    """
    
    try:
        print(" -> Generando introducción de la IA con contexto de conversaciones...")
        response = gemini_model.generate_content(prompt)
        
        # Procesamos la respuesta (tu código de regex para TÍTULO/ANÁLISIS ya es correcto)
        titulo = "El Vestuario Habla"
        analisis = response.text
        match_titulo = re.search(r"TÍTULO: (.*)", response.text, re.IGNORECASE)
        match_analisis = re.search(r"ANÁLISIS: (.*)", response.text, re.IGNORECASE | re.DOTALL)
        if match_titulo:
            titulo = match_titulo.group(1).strip()
        if match_analisis:
            analisis = match_analisis.group(1).strip()
        return f"## 🎙️ {titulo}\n\n_{analisis}_\n"
    except Exception as e:
        print(f"Error al generar la introducción de la IA: {e}")
        return ""

# En: cronista.py

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