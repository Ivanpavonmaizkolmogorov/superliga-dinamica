
import json
import shutil
import os

def reparar_historial():
    archivo = 'perfiles.json'
    backup = 'perfiles_backup_corrupto.json'
    
    if os.path.exists(archivo):
        shutil.copy(archivo, backup)
        print(f"Backup creado: {backup}")
    else:
        print("No se encuentra perfiles.json")
        return

    with open(archivo, 'r') as f:
        perfiles = json.load(f)

    print("--- INICIANDO REPARACIÓN DE HISTORIAL ---")
    
    cambios_totales = 0
    
    for perfil in perfiles:
        print(f"Procesando: {perfil['nombre_mister']}...")
        historial = perfil['historial_temporada']
        
        # Ordenar por jornada para asegurar la suma correcta
        historial.sort(key=lambda x: x['jornada'])
        
        acumulado = 0
        for h in historial:
            puntos_jornada = h['puntos_jornada']
            acumulado += puntos_jornada
            
            if h.get('puntos_totales') != acumulado:
                # print(f"  - J.{h['jornada']}: Corrigiendo TOTAL {h.get('puntos_totales')} -> {acumulado}")
                h['puntos_totales'] = acumulado
                cambios_totales += 1
                
        print(f"  -> Total calculado final: {acumulado}")

    with open(archivo, 'w') as f:
        json.dump(perfiles, f, indent=4, ensure_ascii=False)
        
    print(f"\nREPARACIÓN COMPLETADA. Se corrigieron {cambios_totales} registros.")

if __name__ == "__main__":
    reparar_historial()
