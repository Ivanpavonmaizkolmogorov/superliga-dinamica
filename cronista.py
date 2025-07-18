# cronista.py (Versión Final con Nombres de Emergencia y Detección de Títulos)

import json
import random
import google.generativeai as genai
from config import GEMINI_API_KEY

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


def generar_cronica(perfil_manager, datos_actuales):
    """
    Genera una crónica personalizada para un mánager, teniendo en cuenta sus títulos.
    """
    if not gemini_model: 
        return "El cronista está afónico hoy. No hay crónica."

    nombre_mister = perfil_manager.get('nombre_mister', 'Mánager Desconocido')
    
    # --- NUEVA LÓGICA: DETECCIÓN DE TÍTULOS ---
    num_titulos = nombre_mister.count('🏆')
    contexto_titulos = f"Este mánager tiene {num_titulos} títulos en su palmarés. Tenlo en cuenta para tu comentario." if num_titulos > 0 else "Este mánager aún no ha ganado ningún título."

    prompt = f"""
    Actúa como un cronista deportivo ingenioso y con memoria, como si fueras Maldini pero con más sarcasmo.
    {contexto_titulos}

    Perfil del Mánager:
    - Nombre: {nombre_mister}
    - Apodo/Lema: {perfil_manager.get('apodo_lema', 'Sin apodo')}
    - Momento de Gloria: {perfil_manager.get('momento_gloria', 'Aún por llegar')}
    - Peor Desastre: {perfil_manager.get('peor_desastre', 'Ninguno conocido')}

    Contexto de esta semana:
    - Puntos de la jornada: {datos_actuales.get('puntos_jornada', 0)}
    - Puesto actual: {datos_actuales.get('puesto', 'N/A')}

    Escribe un comentario breve y punzante (2-3 frases) sobre su rendimiento en esta jornada, conectando con su personalidad, su historia y su palmarés. Si tiene muchos títulos y va mal, puedes ser irónico. Si no tiene títulos y va bien, puedes ser esperanzador (o cínico).
    """
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