
import json

def verificar_sprint_2():
    try:
        with open('perfiles.json', 'r') as f:
            perfiles = json.load(f)
    except FileNotFoundError:
        print("Error: No se encuentra perfiles.json")
        return

    print("--- VERIFICACIÓN DE SPRINT 2 (J11 - J20) ---")
    print(f"{'Nombre':<25} | {'J11':<4} | {'J12':<4} | {'J13':<4} | {'TOTAL SPRINT':<12}")
    print("-" * 65)

    sprint_data = []

    for perfil in perfiles:
        nombre = perfil['nombre_mister']
        historial = perfil['historial_temporada']
        
        # Filtrar jornadas del Sprint 2
        puntos_sprint = 0
        detalles_jornadas = {}
        
        for h in historial:
            j = h['jornada']
            if 11 <= j <= 20:
                puntos_sprint += h['puntos_jornada']
                detalles_jornadas[j] = h['puntos_jornada']
        
        sprint_data.append({
            'nombre': nombre,
            'total': puntos_sprint,
            'j11': detalles_jornadas.get(11, 0),
            'j12': detalles_jornadas.get(12, 0),
            'j13': detalles_jornadas.get(13, 0)
        })

    # Ordenar por total de sprint descendente
    sprint_data.sort(key=lambda x: x['total'], reverse=True)

    for d in sprint_data:
        print(f"{d['nombre']:<25} | {d['j11']:<4} | {d['j12']:<4} | {d['j13']:<4} | {d['total']:<12}")

    print("\n--- CHEQUEO DE INTEGRIDAD DE HISTORIAL ---")
    print("Verificando si puntos_totales es consistente...")
    
    problemas_detectados = False
    for perfil in perfiles:
        historial = perfil['historial_temporada']
        # Chequear si todos los puntos totales son iguales (síntoma del bug)
        totales = [h['puntos_totales'] for h in historial]
        if len(set(totales)) == 1 and len(totales) > 1:
            print(f"ALERTA: {perfil['nombre_mister']} tiene el historial de totales PLANO: {totales[0]}")
            problemas_detectados = True
            
    if not problemas_detectados:
        print("No se detectaron problemas obvios de historial plano (¿ya se arregló?).")
    else:
        print("CONFIRMADO: El historial de 'puntos_totales' está corrompido (plano), pero 'puntos_jornada' parece preservarse.")

if __name__ == "__main__":
    verificar_sprint_2()
