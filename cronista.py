# cronista.py (Versión con lógica de prioridad)
import yaml
import json
import random
import re
from datetime import datetime, timedelta
from config import GEMINI_API_KEY
import google.generativeai as genai
import time

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
    # --- Mercado y Fichajes ---
    'ficho', 'fichaje', 'fichajazo', 'oferta', 'ofrezco', 'ofrecen', 'vendo', 
    'venta', 'vender', 'compro', 'compra', 'clausula', 'clausulazo', 'mercado', 
    'millones', 'pasta', 'kilos', 'dinero', 'puja', 'pujar', 'vendido', 
    'negociar', 'negociación', 'traspaso', 'interesa', 'robar', 'roba', 'robarme',

    # --- Críticas, Piques y Burlas ---
    'paquete', 'paquetón', 'manco', 'mantas', 'tronco', 'cono', 'robo', 'tongo', 
    'trampa', 'tramposo', 'suerte', 'potra', 'chiripa', 'flor', 'suertudo', 
    'lloron', 'llorica', 'llorando', 'malo', 'malisimo', 'ridículo', 'pechofrío',
    'humo', 'vendehumo', 'cagón', 'palmero',

    # --- Resultados y Clasificación ---
    'gano', 'gane', 'ganar', 'reviento', 'paliza', ' repaso', 'goleada', 
    'humillación', 'lider', 'líder', 'campeón', 'podio', 'remontada', 'farolillo', 
    'colista', 'último', 'palmar', 'palmo', 'pierdo', 'perder', 'fracaso', 
    'victoria', 'derrota', 'empaque', 'ascenso', 'descenso',

    # --- Jugadores, Lesiones y Alineaciones ---
    'lesion', 'lesionado', 'roto', 'tocado', 'duda', 'no juega', 'banquillo', 
    'suplente', 'alineacion', 'alineación', 'once', 'indebida', 'tactica', 
    'táctica', 'sistema', 'rotación', 'rotaciones', 'pufo', 'chollo', 'revelación',
    'bluff', 'defensa', 'delantero', 'portero',

    # --- Estrategia y General ---
    'ahorrar', 'guardando', 'deuda', 'positivo', 'negativo', 'arriesgar', 
    'apostar', 'apuesto', 'reto', 'jugón', 'máquina', 'abuso'
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


# --- NUEVA FUNCIÓN AUXILIAR PARA LAS DECLARACIONES ---
def _preparar_ultimas_declaraciones(todas_declaraciones):
    """
    Procesa la lista completa de declaraciones y devuelve un diccionario
    mapeando cada id_manager a su última declaración.
    """
    declaraciones_por_manager = {}
    # Ordenamos de más reciente a más antiguo para procesar eficientemente
    for d in sorted(todas_declaraciones, key=lambda x: x.get('timestamp', ''), reverse=True):
        manager_id = d.get("telegram_user_id")
        # Si el manager ya tiene una declaración, no la sobrescribimos,
        # porque ya hemos guardado la más reciente gracias al ordenamiento.
        if manager_id and manager_id not in declaraciones_por_manager:
            declaraciones_por_manager[manager_id] = d['declaracion']
    return declaraciones_por_manager

# --- NUEVA FUNCIÓN OPTIMIZADA PARA CRÓNICAS ---
# En cronista.py

# En cronista.py

def generar_todas_las_cronicas(perfiles, todas_declaraciones, ids_ya_usadas, comentarista, eventos_por_manager={}):
    """Pide a la IA que genere TODAS las crónicas en una sola llamada, reaccionando a eventos."""
    if not gemini_model or not comentarista: 
        return {}

    # La función _preparar_ultimas_declaraciones que creamos antes es muy útil aquí
    ultimas_declaraciones = _preparar_ultimas_declaraciones(todas_declaraciones)

    datos_texto = ""
    # CORRECCIÓN 1: Toda la lógica debe ir DENTRO de este bucle
    for perfil in perfiles:
        ultimo_historial = perfil['historial_temporada'][-1]

  
        # Esta es la instrucción que mejor genera el tipo de crónica que te gustó
        # Esta es la nueva instrucción que fomenta el análisis en lugar de la pregunta direc
        # ta
        declaracion = "Este mánager hace dias que no declara. Cronista, analiza su resultado. Especula sobre las posibles causas de su rendimiento o haz una afirmación contundente sobre su situación actual en la liga."

        
        manager_telegram_id = perfil.get("telegram_user_id")
        if manager_telegram_id:
            # Usamos el diccionario pre-procesado para una búsqueda instantánea
            declaracion = ultimas_declaraciones.get(manager_telegram_id, "ha mantenido un prudente silencio.")

        # Lógica para buscar los eventos (ahora indentada correctamente)
        contexto_extra = ""
        # CORRECCIÓN 2: Buscamos eventos usando la llave correcta -> perfil['id_manager']
        eventos_del_manager = eventos_por_manager.get(perfil['id_manager'], [])
        
        for evento in eventos_del_manager:
            # Eventos de Rivalidad, Extremos y Venganza
            if evento['tipo'] == 'ADELANTAMIENTO_VICTORIA':
                contexto_extra += f"¡Momento clave! Has adelantado a tu rival histórico, {evento['contexto']['rival_adelantado']}. El honor está en juego. "
            elif evento['tipo'] == 'ADELANTAMIENTO_DERROTA':
                contexto_extra += f"¡Dura derrota! Tu rival histórico, {evento['contexto']['adelantado_por']}, te ha adelantado. La humillación es palpable. "
            elif evento['tipo'] == 'VENGANZA_RIVAL':
                contexto_extra += f"¡La venganza se sirve fría! Tras ser adelantado, has recuperado tu honor y tu puesto frente a tu archienemigo, {evento['contexto']['rival_vengado']}. ¡El golpe moral es doble! "
            elif evento['tipo'] == 'ENTRADA_GLORIA':
                contexto_extra += f"Estás en el Olimpo (Puesto {evento['contexto']['puesto']}). ¿Recuerdas tu momento de gloria? '{evento['contexto']['recordatorio_gloria']}'. "
            elif evento['tipo'] == 'CAIDA_DESASTRE':
                contexto_extra += f"Estás en el abismo (Puesto {evento['contexto']['puesto']}). ¿Se repite tu peor desastre? '{evento['contexto']['recordatorio_desastre']}'. "

            # Eventos de Puntuación de la Jornada
            elif evento['tipo'] == 'MVP_JORNADA':
                contexto_extra += f"¡El MVP de la jornada! Has logrado la máxima puntuación con {evento['contexto']['puntos']} puntos. ¡Impresionante! "
            elif evento['tipo'] == 'FAROLILLO_ROJO_JORNADA':
                contexto_extra += f"Semana difícil. Has sido el farolillo rojo con la puntuación más baja ({evento['contexto']['puntos']} pts). Toca reflexionar. "

            # Eventos de Movimiento en la Clasificación
            elif evento['tipo'] == 'COHETE_JORNADA':
                contexto_extra += f"¡El cohete de la semana! Has protagonizado la mayor subida, escalando {evento['contexto']['puestos_subidos']} puestos de golpe. "
            elif evento['tipo'] == 'ANCLA_JORNADA':
                contexto_extra += f"¡Semana para olvidar! Has sufrido la peor caída, desplomándote {evento['contexto']['puestos_bajados']} puestos. "

            # Eventos de Rachas y Tendencias
            elif evento['tipo'] == 'RACHA_IMPARABLE':
                contexto_extra += f"¡Estás imparable! Llevas 3 semanas seguidas en el podio. Eres el rival a batir. "
            elif evento['tipo'] == 'CAIDA_LIBRE':
                contexto_extra += f"¡En caída libre! Tercera semana consecutiva perdiendo posiciones. Las alarmas están encendidas. "
            elif evento['tipo'] == 'MR_REGULARIDAD':
                contexto_extra += f"Abonado a la zona tibia. Una jornada más en la cómoda mediocridad de la tabla. ¿Estrategia o falta de ambición? "
            
            # --- AÑADE ESTOS NUEVOS ELIF ---
            elif evento['tipo'] == 'DUELO_RIVALES':
                contexto_extra += f"¡Duelo de alta tensión! Lucha fraticida contra su rival histórico, {evento['contexto']['manager2_nombre']}, decidida por la mínima. "
            elif evento['tipo'] == 'SORPRESA_JORNADA':
                contexto_extra += "¡La sorpresa de la jornada! Viniendo desde abajo, se ha colado en el podio de puntuaciones. "
            elif evento['tipo'] == 'CRISIS_EN_CIMA':
                contexto_extra += "¡Crisis en la cima! Estando en el Top 3, ha cosechado una de las peores puntuaciones de la semana. "
            elif evento['tipo'] == 'GIGANTE_DESPIERTA':
                contexto_extra += "¡El gigante dormido ha despertado! Un ex-campeón vuelve por sus fueros con una puntuación estelar. "

        # Construcción del texto para el prompt (ahora indentado correctamente)
        datos_texto += (
            f"ID_MANAGER: {perfil['id_manager']}\n"
            f"NOMBRE: {limpiar_nombre_para_ia(perfil['nombre_mister'])}\n"
            f"PUNTOS: {ultimo_historial['puntos_jornada']}\n"
            f"DECLARACION: \"{declaracion}\"\n"
            f"CONTEXTO_EXTRA: \"{contexto_extra.strip()}\"\n" 
            "---\n"
        )
    
    # Esta parte (la construcción del prompt y la llamada a la IA) ya estaba bien
    DELIMITADOR = "|||---|||"
    prompt = (
        f"{comentarista['prompt_base']}\n\n"
        f"Tu tarea es escribir una crónica (4-5 frases) para CADA UNO de los siguientes mánagers. "
        f"Conecta sus PUNTOS con su DECLARACION. "
        f"Si existe un 'CONTEXTO_EXTRA', DEBES centrar tu crónica en ese evento dramático, es la noticia más importante. Si está vacío, ignóralo. "
        f"Debes escribir una crónica para cada uno en el mismo orden que te los doy, "
        f"y separar CADA crónica de la siguiente con el delimitador exacto: {DELIMITADOR}\n\n"
        f"LISTA DE MÁNAGERS:\n{datos_texto}"
    )

    print(f" -> Pidiendo LOTE de {len(perfiles)} crónicas a '{comentarista['nombre_display']}'...")
    
    try:
        response = gemini_model.generate_content(prompt)
        cronicas_separadas = response.text.split(DELIMITADOR)
        if len(cronicas_separadas) >= len(perfiles):
            # CORRECCIÓN 3: El diccionario devuelto DEBE usar 'id_manager' como llave
            return {perfiles[i]['id_manager']: cronicas_separadas[i].strip() for i in range(len(perfiles))}
        else:
            print(f"ADVERTENCIA: La IA devolvió {len(cronicas_separadas)} crónicas en lugar de {len(perfiles)}."); 
            return {}
    except Exception as e:
        print(f"❌❌ ERROR en la llamada a la IA para LOTE de Crónicas: {e} ❌❌")
        return {}


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
    """
    Navega hacia atrás en un hilo de respuestas para encontrar el mensaje original.
    """
    current_id = message_id
    while True:
        message = declarations_map.get(current_id)
        # Si no hay mensaje o no es una respuesta, hemos encontrado el origen.
        if not message or not message.get("reply_to_message_id"):
            break
        parent_id = message["reply_to_message_id"]
        # Si el mensaje al que responde no está en nuestras declaraciones, paramos.
        if parent_id not in declarations_map:
            break
        current_id = parent_id
    return current_id

def _group_declarations_into_threads(all_declarations):
    """
    Agrupa todas las declaraciones en hilos de conversación.
    Devuelve una lista de hilos, donde cada hilo es una lista de declaraciones.
    """
    # Creamos un mapa para acceder a cualquier mensaje por su ID rápidamente.
    declarations_map = {d["message_id"]: d for d in all_declarations if d.get("message_id")}
    
    threads = {}
    for declaration in all_declarations:
        if not declaration.get("message_id"): continue
        
        # Para cada declaración, encontramos la raíz de su conversación.
        root_id = _find_root_message(declaration["message_id"], declarations_map)
        
        # Agrupamos la declaración en el hilo correspondiente a su raíz.
        if root_id not in threads:
            threads[root_id] = []
        threads[root_id].append(declaration)
        
    # Ordenamos cada hilo por fecha para que la conversación tenga sentido.
    for root_id in threads:
        threads[root_id].sort(key=lambda d: d.get("timestamp", ""))
        
    return list(threads.values())

def _buscar_declaracion_reciente(manager_ids, todas_declaraciones, ids_ya_usadas):
    fecha_limite = datetime.now() - timedelta(days=21)
    if not isinstance(manager_ids, list): manager_ids = [manager_ids]
    for d in sorted(todas_declaraciones, key=lambda x: x['timestamp'], reverse=True):
        if d.get("telegram_user_id") in manager_ids and d.get("message_id") not in ids_ya_usadas and datetime.fromisoformat(d['timestamp']) > fecha_limite:
            return d
    return None

# --- FUNCIONES DE GENERACIÓN DE TEXTO (ACTUALIZADAS) ---

# En cronista.py, reemplaza generar_introduccion_semanal por esta versión

def generar_introduccion_semanal(perfiles, todas_declaraciones, jornada_actual):
    """
    Genera la introducción de la semana.
    PRIORIDAD 1: Busca el "debate de la semana" (hilos con respuestas).
    PRIORIDAD 2: Si no hay debates, busca la declaración individual más jugosa.
    """
    if not gemini_model or not todas_declaraciones:
        mensaje_proactivo = (
            "¡El vestuario ha enmudecido! Ni un solo rumor, ni un pique, ni una queja esta semana. "
            "El Cronista necesita material para la crónica. Para que vuestras opiniones salgan aquí, "
            "¡mencionad a `@SuperligaCronistaBot` en vuestros mensajes y dadle salseo a la liga!"
        )
        return (f"## 🎙️ El Micrófono Abierto\n\n_{mensaje_proactivo}_\n", set())

    fecha_limite = datetime.now() - timedelta(days=21)
    declaraciones_recientes = [d for d in todas_declaraciones if datetime.fromisoformat(d.get('timestamp', '')) > fecha_limite]
    if not declaraciones_recientes:
        mensaje_proactivo = (
            "¡El vestuario ha enmudecido! Ni un solo rumor, ni un pique, ni una queja esta semana. "
            "El Cronista necesita material para la crónica. Para que vuestras opiniones salgan aquí, "
            "¡mencionad a `@SuperligaCronistaBot` en vuestros mensajes y dadle salseo a la liga!"
        )
        return (f"## 🎙️ El Micrófono Abierto\n\n_{mensaje_proactivo}_\n", set())
    # --- PRIORIDAD 1: BUSCAR DEBATES ---
    todos_los_hilos = _group_declarations_into_threads(declaraciones_recientes)
    hilos_relevantes = [hilo for hilo in todos_los_hilos if len(hilo) > 1]

    if hilos_relevantes:
        print("INFO (Intro): Encontrado debate de la semana. Analizando...")
        hilo_estrella = max(hilos_relevantes, key=len)
        transcripcion = ""
        ids_usados = set()
        for d in hilo_estrella:
            prefijo = "  -> Responde: " if d.get("reply_to_message_id") else ""
            transcripcion += f"{prefijo}{d['nombre_mister']}: \"{d['declaracion']}\"\n"
            ids_usados.add(d['message_id'])
        
        texto_prompt = f"El debate más caliente ha sido el siguiente:\n\n--- TRANSCRIPCIÓN ---\n{transcripcion}-------------------\n\nAnaliza este pique."
    
    # --- PRIORIDAD 2: SI NO HAY DEBATES, BUSCAR LA MEJOR DECLARACIÓN INDIVIDUAL ---
    else:
        print("INFO (Intro): No se encontraron debates. Buscando la declaración individual más relevante por palabras clave...")

        if not declaraciones_recientes:
            return ("## 🎙️ El Vestuario Habla\n\n_Semana de silencio total en el vestuario._\n", set())

        # Puntuamos cada declaración reciente usando nuestra nueva función
        declaraciones_puntuadas = [
            (d, _calcular_puntuacion_declaracion(d.get('declaracion', ''), PALABRAS_CLAVE_INTERES))
            for d in declaraciones_recientes
        ]

        # Obtenemos la puntuación máxima encontrada
        max_puntuacion = max(p[1] for p in declaraciones_puntuadas)

        # Si la mejor puntuación es mayor que 0, significa que hemos encontrado "salseo"
        if max_puntuacion > 0:
            print(f"INFO (Intro): Encontrada declaración con salseo (puntuación: {max_puntuacion}).")
            # Elegimos la declaración con la máxima puntuación
            declaracion_estrella = max(declaraciones_puntuadas, key=lambda item: item[1])[0]
        else:
            # Si ninguna declaración tiene palabras clave, como plan B, elegimos la más larga
            print("INFO (Intro): No hay salseo. Se elige la declaración más larga como plan B.")
            declaracion_estrella = max(declaraciones_recientes, key=lambda d: len(d.get('declaracion', '')))

        transcripcion = f"{declaracion_estrella['nombre_mister']} ha declarado: \"{declaracion_estrella['declaracion']}\""
        ids_usados = {declaracion_estrella['message_id']}
        texto_prompt = f"La declaración más destacada de la semana ha sido la siguiente:\n\n{transcripcion}\n\nAnaliza esta declaración."
    # --- Construcción del prompt final (común para ambos casos) ---
    lider_actual = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puesto'])[0]
    prompt = f"""
    Eres el Editor Jefe de un programa deportivo. Tu misión es escribir una introducción impactante para el reporte de la Jornada {jornada_actual}.
    {texto_prompt}
    Dato clave: El líder actual es {lider_actual['nombre_mister']}.

    Tu tarea es doble:
    1.  **Escribe un TÍTULO DE LA JORNADA:** Una frase corta y potente.
    2.  **Escribe un PÁRRAFO DE ANÁLISIS:** Comenta la situación (el debate o la declaración), y qué significa para la liga.

    Formato de respuesta:
    TÍTULO: [Tu título aquí]
    ANÁLISIS: [Tu párrafo de análisis aquí]
    """
    
    try:
        # (El resto de la función para llamar a la IA y procesar la respuesta es igual)
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



# --- OTRAS FUNCIONES DE CRONISTA (PUEDEN QUEDAR IGUAL O ADAPTARSE EN EL FUTURO) ---
# Por ahora, las funciones de Sprints y Parejas no usarán declaraciones para simplificar.
# Si en el futuro quieres añadirles contexto, seguirían el mismo patrón que 'generar_cronica'.

def generar_comentario_premio(nombre_premio, ganadores, jornada_actual, es_final):
    time.sleep(1)
    comentarista = elegir_comentarista('premio')
    if not gemini_model or not comentarista: return "_El cronista guarda silencio._"
    contexto = "de forma definitiva" if es_final else f"provisionalmente en la jornada {jornada_actual}"
    nombres = " y ".join([limpiar_nombre_para_ia(g) for g in ganadores])
    prompt = (f"{comentarista['prompt_base']}\n\nNarra la entrega del premio '{nombre_premio}'. El ganador es '{nombres}' y lo ha conseguido {contexto}. Comenta este logro de forma breve y memorable.")
    print(f" -> Pidiendo comentario para '{nombre_premio}' a '{comentarista['nombre_display']}'...")
    try: return f"_{gemini_model.generate_content(prompt).text.strip()}_"
    except Exception as e: print(f"ERROR en IA para Premio '{nombre_premio}': {e}"); return f"_{comentarista['nombre_display']} aplaude el logro de {nombres}._"
    

def generar_comentario_sprint(nombre_sprint, clasificacion, jornada_actual, inicio_sprint, fin_sprint):
    time.sleep(1)
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


def _calcular_puntuacion_declaracion(declaracion_texto, palabras_clave):
    """
    Calcula una puntuación de 'interés' para una declaración contando
    cuántas palabras clave contiene.
    """
    if not declaracion_texto: return 0
    puntuacion = 0
    # Convertimos el texto a minúsculas para que la búsqueda no distinga mayúsculas/minúsculas
    texto_minusculas = declaracion_texto.lower()
    for palabra in palabras_clave:
        # Buscamos cada palabra clave en el texto
        if palabra.lower() in texto_minusculas:
            puntuacion += 1
    return puntuacion

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
    time.sleep(0.5)
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