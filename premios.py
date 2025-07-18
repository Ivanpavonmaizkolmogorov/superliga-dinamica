# premios.py (Versión Final que NO crea archivos por defecto)
import json

def cargar_config_liga():
    """
    Intenta cargar la configuración de la liga desde config_liga.json.
    Si el archivo no existe, devuelve un diccionario vacío para que el
    programa principal sepa que debe ser creado por el usuario.
    """
    try:
        with open('config_liga.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Si no se encuentra, devolvemos un diccionario vacío.
        # NO CREAMOS NADA.
        return {}

def calcular_estado_premios(perfiles, parejas, config_liga):
    """
    Calcula el estado actual de todos los premios y devuelve un texto formateado.
    """
    # Comprobación inicial: si no hay configuración, no podemos calcular nada.
    if not config_liga:
        return ("No se ha encontrado una configuración de liga ('config_liga.json').\n\n"
                "Por favor, usa el botón 'Configuración de la Liga' en el panel principal para crearla.")

    if not perfiles or not perfiles[0].get('historial_temporada'):
        return "No hay datos de jornadas para calcular los premios. Simula o procesa una jornada primero."

    num_managers = len(perfiles)
    bote_total = num_managers * config_liga.get('cuota_inscripcion', 0.0)
    reparto = config_liga.get('reparto_premios_porcentaje', {})
    
    # Ordenamos los perfiles según su última puntuación total registrada
    perfiles_ordenados = sorted(
        perfiles, 
        key=lambda p: p['historial_temporada'][-1]['puntos_totales'] if p.get('historial_temporada') else 0,
        reverse=True
    )
    
    jornada_actual = perfiles_ordenados[0]['historial_temporada'][-1]['jornada']

    # --- Cálculo de cada premio ---
    
    # 1. Clasificación General
    ganador_general = perfiles_ordenados[0]
    segundo_general = perfiles_ordenados[1] if num_managers > 1 else {"nombre_mister": "N/A", "historial_temporada": [{"puntos_totales": 0}]}
    premio_1 = (reparto.get('1_clasificado_general', 0) / 100) * bote_total
    premio_2 = (reparto.get('2_clasificado_general', 0) / 100) * bote_total

    # 2. Campeón de Invierno
    premio_invierno = (reparto.get('campeon_invierno', 0) / 100) * bote_total
    ganador_invierno = f"(Se decide en J19)"
    try:
        if jornada_actual >= 19:
            ganador_invierno_perfil = next(p for p in perfiles if any(h['jornada'] == 19 and h['puesto'] == 1 for h in p['historial_temporada']))
            ganador_invierno = ganador_invierno_perfil['nombre_mister']
    except StopIteration:
        ganador_invierno = "No encontrado (error en datos)"

    # 3. Mejor 2ª Vuelta
    premio_2_vuelta = (reparto.get('mejor_2_vuelta', 0) / 100) * bote_total
    ganador_2_vuelta_nombre = f"(Empieza en J20)"
    if jornada_actual >= 20:
        clasif_2_vuelta = []
        for p in perfiles:
            puntos = sum(h['puntos_jornada'] for h in p['historial_temporada'] if h.get('jornada', 0) >= 20)
            clasif_2_vuelta.append({"nombre": p['nombre_mister'], "puntos": puntos})
        if clasif_2_vuelta:
            ganador_2_vuelta = sorted(clasif_2_vuelta, key=lambda x: x['puntos'], reverse=True)[0]
            ganador_2_vuelta_nombre = f"{ganador_2_vuelta['nombre']} ({ganador_2_vuelta['puntos']} pts)"

    # 4. Pareja Ganadora
    premio_parejas = (reparto.get('pareja_ganadora', 0) / 100) * bote_total
    ganador_pareja_nombre = "No hay parejas configuradas"
    if parejas:
        clasificacion_parejas = []
        for pareja in parejas:
            puntos_totales_pareja = 0
            miembros_encontrados = 0
            for manager_id in pareja['id_managers']:
                miembro = next((p for p in perfiles_ordenados if p['id_manager'] == manager_id), None)
                if miembro and miembro['historial_temporada']:
                    puntos_totales_pareja += miembro['historial_temporada'][-1]['puntos_totales']
                    miembros_encontrados += 1
            media_puntos = puntos_totales_pareja / miembros_encontrados if miembros_encontrados > 0 else 0
            clasificacion_parejas.append({"nombre": pareja['nombre_pareja'], "media": round(media_puntos)})
        
        if clasificacion_parejas:
            ganador_pareja = sorted(clasificacion_parejas, key=lambda x: x['media'], reverse=True)[0]
            ganador_pareja_nombre = f"{ganador_pareja['nombre']} (Media: {ganador_pareja['media']} pts)"

    # --- Formateo del Texto de Salida ---
    texto_premios = (
        f"--- ESTADO DE PREMIOS (Jornada {jornada_actual}) ---\n"
        f"Bote Total Acumulado: {bote_total:.2f} €\n\n"
        f"1. 1º Clasificado General ({premio_1:.2f} €):\n"
        f"   -> Actualmente: {ganador_general['nombre_mister']} ({ganador_general['historial_temporada'][-1]['puntos_totales']} pts)\n\n"
        f"2. Pareja Ganadora ({premio_parejas:.2f} €):\n"
        f"   -> Actualmente: {ganador_pareja_nombre}\n\n"
        f"3. 2º Clasificado General ({premio_2:.2f} €):\n"
        f"   -> Actualmente: {segundo_general['nombre_mister']} ({segundo_general['historial_temporada'][-1]['puntos_totales']} pts)\n\n"
        f"4. Mejor de la 2ª Vuelta ({premio_2_vuelta:.2f} €):\n"
        f"   -> Actualmente: {ganador_2_vuelta_nombre}\n\n"
        f"5. Campeón de Invierno ({premio_invierno:.2f} €):\n"
        f"   -> Ganador: {ganador_invierno}\n"
    )
    return texto_premios