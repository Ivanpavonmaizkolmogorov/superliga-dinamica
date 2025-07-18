# simulador.py
import random
import copy

def generar_puntos_jornada_falsos(perfiles):
    """
    Genera una lista de puntos de jornada falsos, uno por cada mánager,
    con una ligera variación para que no todos saquen lo mismo.
    """
    puntos_falsos = []
    for _ in perfiles:
        # Simula una puntuación realista para una jornada de fantasy (entre 30 y 90)
        puntos_falsos.append(random.randint(30, 90))
    return puntos_falsos

def simular_nueva_jornada(perfiles):
    """
    Toma una lista de perfiles, les añade una nueva jornada simulada con puntos
    aleatorios, recalcula los totales y los puestos, y devuelve los perfiles actualizados.
    """
    # Usamos deepcopy para asegurar que no modificamos la lista original accidentalmente
    perfiles_simulados = copy.deepcopy(perfiles)
    
    puntos_jornada_falsos = generar_puntos_jornada_falsos(perfiles_simulados)
    
    # Primero, asignamos los puntos falsos y actualizamos los totales de cada mánager
    for i, perfil in enumerate(perfiles_simulados):
        puntos_jornada = puntos_jornada_falsos[i]
        
        if perfil.get('historial_temporada'):
            # Si ya hay historial, calculamos la nueva jornada y los puntos totales
            ultima_jornada_historial = perfil['historial_temporada'][-1]
            jornada_actual = ultima_jornada_historial.get('jornada', 0) + 1
            puntos_totales_actuales = ultima_jornada_historial.get('puntos_totales', 0) + puntos_jornada
        else:
            # Si es la primera jornada para este mánager
            jornada_actual = 1
            puntos_totales_actuales = puntos_jornada
            perfil['historial_temporada'] = [] # Aseguramos que la lista exista
            
        # Añadimos la nueva entrada al historial (el puesto aún es provisional)
        perfil['historial_temporada'].append({
            "jornada": jornada_actual,
            "puntos_jornada": puntos_jornada,
            "puesto": 0, # El puesto se recalculará a continuación
            "puntos_totales": puntos_totales_actuales
        })

    # Segundo, una vez todos los totales están actualizados, ordenamos la lista completa
    # para determinar los puestos correctos en esta nueva jornada.
    perfiles_simulados.sort(
        key=lambda p: p['historial_temporada'][-1]['puntos_totales'], 
        reverse=True
    )
    
    # Finalmente, actualizamos el puesto de cada mánager en su última entrada del historial
    for i, perfil in enumerate(perfiles_simulados):
        perfil['historial_temporada'][-1]['puesto'] = i + 1
        
    return perfiles_simulados