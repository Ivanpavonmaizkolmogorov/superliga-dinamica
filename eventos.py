# eventos.py

"""
Módulo de Detección de Eventos Narrativos.
Este módulo analiza el estado de la liga para identificar sucesos clave
que pueden ser comentados por el cronista para añadir dramatismo y contexto.
"""

# --- EVENTOS DE RIVALIDAD Y POSICIÓN EXTREMA ---

def _detectar_adelantamiento_rival(perfiles):
    """Detecta si un mánager ha adelantado a su rival histórico."""
    eventos = []
    if len(perfiles[0].get('historial_temporada', [])) < 2: return []
    perfiles_map = {p['id_manager']: p for p in perfiles}

    for perfil in perfiles:
        rival_id = perfil.get('rival_historico')
        if not rival_id or rival_id not in perfiles_map: continue
        rival_perfil = perfiles_map[rival_id]
        
        puesto_actual, puesto_anterior = perfil['historial_temporada'][-1]['puesto'], perfil['historial_temporada'][-2]['puesto']
        rival_puesto_actual, rival_puesto_anterior = rival_perfil['historial_temporada'][-1]['puesto'], rival_perfil['historial_temporada'][-2]['puesto']

        if puesto_anterior > rival_puesto_anterior and puesto_actual < rival_puesto_actual:
            eventos.append({"id_manager": perfil['id_manager'], "tipo": "ADELANTAMIENTO_VICTORIA", "contexto": {"rival_adelantado": rival_perfil['nombre_mister']}})
            eventos.append({"id_manager": rival_id, "tipo": "ADELANTAMIENTO_DERROTA", "contexto": {"adelantado_por": perfil['nombre_mister']}})
    return eventos

def _detectar_extremos_clasificacion(perfiles):
    """Detecta si un mánager ha entrado en zona de 'gloria' o 'desastre'."""
    eventos = []
    num_managers = len(perfiles)
    for perfil in perfiles:
        puesto_actual = perfil['historial_temporada'][-1]['puesto']
        if puesto_actual <= 3 and perfil.get('momento_gloria'):
            eventos.append({"id_manager": perfil['id_manager'], "tipo": "ENTRADA_GLORIA", "contexto": {"puesto": puesto_actual, "recordatorio_gloria": perfil['momento_gloria']}})
        if puesto_actual >= (num_managers - 2) and perfil.get('peor_desastre'):
            eventos.append({"id_manager": perfil['id_manager'], "tipo": "CAIDA_DESASTRE", "contexto": {"puesto": puesto_actual, "recordatorio_desastre": perfil['peor_desastre']}})
    return eventos
    
def _detectar_venganza_rival(perfiles):
    """Detecta si un mánager se ha 'vengado' de su rival tras haber sido adelantado."""
    eventos = []
    if len(perfiles[0].get('historial_temporada', [])) < 3: return []
    perfiles_map = {p['id_manager']: p for p in perfiles}

    for perfil in perfiles:
        rival_id = perfil.get('rival_historico')
        if not rival_id or rival_id not in perfiles_map: continue
        
        rival_perfil = perfiles_map[rival_id]
        historial, rival_historial = perfil['historial_temporada'], rival_perfil['historial_temporada']

        puesto_n, puesto_n1, puesto_n2 = historial[-1]['puesto'], historial[-2]['puesto'], historial[-3]['puesto']
        rival_puesto_n, rival_puesto_n1, rival_puesto_n2 = rival_historial[-1]['puesto'], rival_historial[-2]['puesto'], rival_historial[-3]['puesto']

        if puesto_n2 < rival_puesto_n2 and puesto_n1 > rival_puesto_n1 and puesto_n < rival_puesto_n:
            eventos.append({"id_manager": perfil['id_manager'], "tipo": "VENGANZA_RIVAL", "contexto": {"rival_vengado": rival_perfil['nombre_mister']}})
    return eventos
    
# --- EVENTOS DE RENDIMIENTO EN LA JORNADA ---

def _detectar_puntuaciones_notables(perfiles):
    """Detecta al MVP (mejor puntuación) y al Farolillo Rojo (peor puntuación) de la jornada."""
    eventos = []
    if not perfiles: return []
    
    puntuaciones = [p['historial_temporada'][-1]['puntos_jornada'] for p in perfiles]
    max_puntos = max(puntuaciones)
    min_puntos = min(puntuaciones)

    for perfil in perfiles:
        puntos_jornada = perfil['historial_temporada'][-1]['puntos_jornada']
        if puntos_jornada == max_puntos:
            eventos.append({"id_manager": perfil['id_manager'], "tipo": "MVP_JORNADA", "contexto": {"puntos": puntos_jornada}})
        if puntos_jornada == min_puntos:
            eventos.append({"id_manager": perfil['id_manager'], "tipo": "FAROLILLO_ROJO_JORNADA", "contexto": {"puntos": puntos_jornada}})
    return eventos

def _detectar_movimientos_clasificacion(perfiles):
    """Detecta al Cohete (mayor subida) y al Ancla (mayor bajada) de la jornada."""
    eventos = []
    if len(perfiles[0].get('historial_temporada', [])) < 2: return []
    
    movimientos = []
    for p in perfiles:
        mejora = p['historial_temporada'][-2]['puesto'] - p['historial_temporada'][-1]['puesto']
        movimientos.append({'id': p['id_manager'], 'mejora': mejora})
    
    max_mejora = max(m['mejora'] for m in movimientos) if movimientos else 0
    min_mejora = min(m['mejora'] for m in movimientos) if movimientos else 0

    if max_mejora > 0:
        for m in movimientos:
            if m['mejora'] == max_mejora:
                eventos.append({"id_manager": m['id'], "tipo": "COHETE_JORNADA", "contexto": {"puestos_subidos": max_mejora}})
    if min_mejora < 0:
        for m in movimientos:
            if m['mejora'] == min_mejora:
                eventos.append({"id_manager": m['id'], "tipo": "ANCLA_JORNADA", "contexto": {"puestos_bajados": abs(min_mejora)}})
    return eventos

# --- EVENTOS DE RACHAS Y TENDENCIAS ---
    
def _detectar_rachas_y_estancamiento(perfiles):
    """Detecta rachas positivas, negativas o estancamiento en la mediocridad."""
    eventos = []
    if len(perfiles[0].get('historial_temporada', [])) < 3: return [] 

    num_managers = len(perfiles)
    rango_medio = (5, num_managers - 4) 

    for perfil in perfiles:
        historial = perfil['historial_temporada']
        if len(historial) < 3: continue # Salta a este mánager si no tiene suficiente historia
        
        ultimos_3_puestos = [h['puesto'] for h in historial[-3:]]
        
        if all(p <= 3 for p in ultimos_3_puestos):
            eventos.append({"id_manager": perfil['id_manager'], "tipo": "RACHA_IMPARABLE", "contexto": {"puestos": ultimos_3_puestos}})
        
        if ultimos_3_puestos[0] < ultimos_3_puestos[1] < ultimos_3_puestos[2]:
             eventos.append({"id_manager": perfil['id_manager'], "tipo": "CAIDA_LIBRE", "contexto": {"puestos": ultimos_3_puestos}})

        if all(rango_medio[0] <= p <= rango_medio[1] for p in ultimos_3_puestos):
             eventos.append({"id_manager": perfil['id_manager'], "tipo": "MR_REGULARIDAD", "contexto": {"puestos": ultimos_3_puestos}})
             
    return eventos

# --- FUNCIÓN PRINCIPAL ORQUESTADORA ---

def detectar_eventos_jornada(perfiles):
    """
    Función principal que orquesta la detección de todos los eventos.
    Recibe la lista de perfiles y devuelve un diccionario de eventos por id_manager.
    """
    if not perfiles or not perfiles[0].get('historial_temporada'):
        print("ADVERTENCIA: No hay datos de perfiles o historial para detectar eventos.")
        return {}

    print("--- [DETECCIÓN DE EVENTOS] Buscando narrativas especiales...")
    
    todos_los_eventos = []
    print(" -> Detectando adelantamientos, extremos y venganzas...")
    todos_los_eventos.extend(_detectar_adelantamiento_rival(perfiles))
    todos_los_eventos.extend(_detectar_extremos_clasificacion(perfiles))
    todos_los_eventos.extend(_detectar_venganza_rival(perfiles))
    
    print(" -> Detectando puntuaciones notables...")
    todos_los_eventos.extend(_detectar_puntuaciones_notables(perfiles))
    
    print(" -> Detectando movimientos en la clasificación...")
    todos_los_eventos.extend(_detectar_movimientos_clasificacion(perfiles))
    
    print(" -> Detectando rachas y estancamientos...")
    todos_los_eventos.extend(_detectar_rachas_y_estancamiento(perfiles))
    
    if todos_los_eventos:
        print(f"INFO: Se han detectado {len(todos_los_eventos)} eventos narrativos.")
    
    eventos_por_manager = {}
    for evento in todos_los_eventos:
        manager_id = evento['id_manager']
        if manager_id not in eventos_por_manager:
            eventos_por_manager[manager_id] = []
        eventos_por_manager[manager_id].append(evento)
        
    return eventos_por_manager