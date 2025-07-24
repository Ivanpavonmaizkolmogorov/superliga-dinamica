# eventos.py

"""
Módulo de Detección de Eventos Narrativos.
Este módulo analiza el estado de la liga para identificar sucesos clave
que pueden ser comentados por el cronista para añadir dramatismo y contexto.
"""

# --- EVENTOS DE RIVALIDAD Y POSICIÓN EXTREMA ---

def _detectar_rivalidad(perfiles):
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

def _detectar_rendimiento_semanal(perfiles):
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

def _detectar_rendimiento_semanal(perfiles):
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

def detectar_eventos_individuales(perfiles):
    """Función principal que orquesta la detección de todos los eventos individuales."""
    print(" -> Detectando eventos individuales...")
    if not perfiles or len(perfiles[0].get('historial_temporada', [])) < 2:
        print("ADVERTENCIA: No hay suficiente historial para detectar todos los eventos individuales.")
        return []

    todos_los_eventos = []
    todos_los_eventos.extend(_detectar_rachas_y_estancamiento(perfiles))
    todos_los_eventos.extend(_detectar_rivalidad(perfiles))
    todos_los_eventos.extend(_detectar_rendimiento_semanal(perfiles))

    todos_los_eventos.extend(_detectar_eventos_contextuales(perfiles))
    todos_los_eventos.extend(_detectar_duelo_rivales(perfiles))

    return todos_los_eventos

def agrupar_eventos_por_manager(todos_los_eventos):
    """Agrupa una lista de eventos en un diccionario por id_manager."""
    eventos_por_manager = {}
    for evento in todos_los_eventos:
        manager_id = evento['id_manager']
        if manager_id not in eventos_por_manager:
            eventos_por_manager[manager_id] = []
        eventos_por_manager[manager_id].append(evento)
    return eventos_por_manager

def _calcular_clasificacion_parejas_simple(perfiles, parejas, jornada_index=-1):
    """Función auxiliar para calcular la clasificación de parejas en una jornada específica."""
    clasificacion = []
    for pareja in parejas:
        miembros = [p for p in perfiles if p['id_manager'] in pareja.get('id_managers', [])]
        if not miembros: continue
        try:
            puntos_totales = sum(m['historial_temporada'][jornada_index]['puntos_totales'] for m in miembros)
            media = puntos_totales / len(miembros)
            clasificacion.append({"nombre": pareja['nombre_pareja'], "media": media})
        except IndexError:
            # Ocurre si un mánager no tiene datos para esa jornada (ej. jornada -2 en la j1)
            continue
            
    clasificacion.sort(key=lambda x: x['media'], reverse=True)
    # Devuelve un diccionario de {nombre_pareja: puesto}
    return {pareja['nombre']: i + 1 for i, pareja in enumerate(clasificacion)}
def detectar_eventos_parejas(perfiles, parejas):
    """
    Detecta eventos clave para las parejas, incluyendo Dúo Dinámico, Lastre,
    Cohete, Ancla y Polos Opuestos.
    """
    print(" -> Detectando eventos de parejas (versión avanzada)...")
    eventos_por_pareja = {}
    if not parejas or not perfiles or len(perfiles[0].get('historial_temporada', [])) < 1:
        return {}

    # --- Lógica para eventos de la jornada actual ---
    perfiles_ordenados_jornada = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puntos_jornada'], reverse=True)
    top_3_ids = {p['id_manager'] for p in perfiles_ordenados_jornada[:3]}
    bottom_3_ids = {p['id_manager'] for p in perfiles_ordenados_jornada[-3:]}

    for pareja in parejas:
        nombre_pareja = pareja['nombre_pareja']
        eventos = []
        miembros_ids = set(pareja.get('id_managers', []))
        
        # Evento: Polos Opuestos
        if len(miembros_ids.intersection(top_3_ids)) > 0 and len(miembros_ids.intersection(bottom_3_ids)) > 0:
            eventos.append("🎭 **Polos Opuestos**: ¡Un miembro en el podio de la jornada y el otro en el fango! La cara y la cruz en el mismo equipo.")

        if eventos:
            eventos_por_pareja[nombre_pareja] = eventos

    # --- Lógica para eventos de movimiento (necesitan 2 jornadas de historial) ---
    if len(perfiles[0].get('historial_temporada', [])) < 2:
        return eventos_por_pareja

    clasif_actual = _calcular_clasificacion_parejas_simple(perfiles, parejas, -1)
    clasif_anterior = _calcular_clasificacion_parejas_simple(perfiles, parejas, -2)
    
    movimientos = []
    for nombre, puesto_actual in clasif_actual.items():
        puesto_anterior = clasif_anterior.get(nombre)
        if puesto_anterior:
            movimiento = puesto_anterior - puesto_actual
            movimientos.append({"nombre": nombre, "movimiento": movimiento})

    if movimientos:
        max_subida = max(m['movimiento'] for m in movimientos) if any(m['movimiento'] > 0 for m in movimientos) else 0
        max_bajada = min(m['movimiento'] for m in movimientos) if any(m['movimiento'] < 0 for m in movimientos) else 0

        for m in movimientos:
            if max_subida > 0 and m['movimiento'] == max_subida:
                if m['nombre'] not in eventos_por_pareja: eventos_por_pareja[m['nombre']] = []
                eventos_por_pareja[m['nombre']].append(f"🚀 **Pareja Cohete**: ¡La mayor subida de la semana (+{max_subida} puestos)!")
            if max_bajada < 0 and m['movimiento'] == max_bajada:
                if m['nombre'] not in eventos_por_pareja: eventos_por_pareja[m['nombre']] = []
                eventos_por_pareja[m['nombre']].append(f"⚓ **Pareja Ancla**: ¡La peor caída de la semana ({max_bajada} puestos)!")

    return eventos_por_pareja

# En eventos.py, AÑADE estas nuevas funciones

def _detectar_eventos_contextuales(perfiles):
    """
    Detecta eventos basados en el contexto de la clasificación y el historial.
    """
    eventos = []
    if len(perfiles[0].get('historial_temporada', [])) < 1: return []

    num_managers = len(perfiles)
    mitad_tabla = num_managers / 2

    # Ordenamos los perfiles por su puntuación en la jornada para análisis
    perfiles_ordenados_jornada = sorted(perfiles, key=lambda p: p['historial_temporada'][-1]['puntos_jornada'], reverse=True)
    
    top_3_puntuaciones = [p['id_manager'] for p in perfiles_ordenados_jornada[:3]]
    bottom_3_puntuaciones = [p['id_manager'] for p in perfiles_ordenados_jornada[-3:]]

    for perfil in perfiles:
        manager_id = perfil['id_manager']
        puesto_general = perfil['historial_temporada'][-1]['puesto']
        puntos_jornada = perfil['historial_temporada'][-1]['puntos_jornada']

        # Evento: La Sorpresa de la Jornada
        if puesto_general > mitad_tabla and manager_id in top_3_puntuaciones:
            eventos.append({"id_manager": manager_id, "tipo": "SORPRESA_JORNADA", "contexto": {"puntos": puntos_jornada}})

        # Evento: Crisis en la Cima
        if puesto_general <= 3 and manager_id in bottom_3_puntuaciones:
            eventos.append({"id_manager": manager_id, "tipo": "CRISIS_EN_CIMA", "contexto": {"puntos": puntos_jornada}})

        # Evento: El Gigante Despierta
        momento_gloria = perfil.get('momento_gloria', '').lower()
        if ('campeon' in momento_gloria or 'campeón' in momento_gloria) and puesto_general > 4 and manager_id in top_3_puntuaciones:
            eventos.append({"id_manager": manager_id, "tipo": "GIGANTE_DESPIERTA", "contexto": {}})

    return eventos

def _detectar_duelo_rivales(perfiles):
    """
    Detecta si dos rivales históricos han tenido una puntuación muy similar.
    """
    eventos = []
    perfiles_map = {p['id_manager']: p for p in perfiles}
    rivales_procesados = set()

    for perfil in perfiles:
        manager_id = perfil['id_manager']
        rival_id = perfil.get('rival_historico')

        # Evitamos procesar el mismo duelo dos veces
        if not rival_id or rival_id not in perfiles_map or manager_id in rivales_procesados:
            continue

        rival_perfil = perfiles_map[rival_id]
        # Nos aseguramos de que sean rivales mutuos
        if rival_perfil.get('rival_historico') == manager_id:
            puntos_manager = perfil['historial_temporada'][-1]['puntos_jornada']
            puntos_rival = rival_perfil['historial_temporada'][-1]['puntos_jornada']

            if abs(puntos_manager - puntos_rival) <= 5: # Umbral de 5 puntos de diferencia
                contexto = {
                    "manager1_nombre": perfil['nombre_mister'], "manager1_puntos": puntos_manager,
                    "manager2_nombre": rival_perfil['nombre_mister'], "manager2_puntos": puntos_rival
                }
                eventos.append({"id_manager": manager_id, "tipo": "DUELO_RIVALES", "contexto": contexto})
                eventos.append({"id_manager": rival_id, "tipo": "DUELO_RIVALES", "contexto": contexto})
            
            # Añadimos ambos a la lista de procesados
            rivales_procesados.add(manager_id)
            rivales_procesados.add(rival_id)
            
    return eventos