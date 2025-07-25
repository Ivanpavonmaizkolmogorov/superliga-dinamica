import json
from datetime import datetime, timedelta
import os

# --- CONFIGURACIÓN ---
ARCHIVO_DECLARACIONES = 'declaraciones.json'
# NUEVO: Archivo único para el histórico
ARCHIVO_HISTORICO = 'declaraciones_archivadas.json' 
# MODIFICADO: Aumentamos a 14 días para coincidir con el cronista
DIAS_ANTIGUEDAD_PARA_LIMPIAR = 14

def limpiar_declaraciones_antiguas():
    """
    Limpia las declaraciones antiguas moviéndolas a un archivo histórico.
    Conserva las declaraciones recientes y las que forman parte de una conversación.
    """
    print("--- Iniciando limpieza y archivado inteligente de declaraciones ---")

    try:
        with open(ARCHIVO_DECLARACIONES, 'r', encoding='utf-8') as f:
            declaraciones = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"ERROR: No se encontró el archivo '{ARCHIVO_DECLARACIONES}' o está vacío. Proceso abortado.")
        return

    if not declaraciones:
        print("No hay declaraciones que procesar.")
        return

    fecha_limite = datetime.now() - timedelta(days=DIAS_ANTIGUEDAD_PARA_LIMPIAR)
    
    # 1. Encontrar todos los mensajes que han sido respondidos para proteger hilos.
    ids_de_mensajes_respondidos = {
        dec["reply_to_message_id"] for dec in declaraciones if dec.get("reply_to_message_id") is not None
    }
    print(f"Se han identificado {len(ids_de_mensajes_respondidos)} mensajes que inician una conversación y serán protegidos.")

    # 2. Filtrar y separar declaraciones
    declaraciones_conservadas = []
    declaraciones_para_archivar = []
    
    for declaracion in declaraciones:
        es_conversacion = declaracion.get("message_id") in ids_de_mensajes_respondidos
        
        try:
            fecha_declaracion = datetime.fromisoformat(declaracion.get("timestamp", ""))
            es_reciente = fecha_declaracion > fecha_limite
        except (ValueError, TypeError):
            es_reciente = False # Si hay error en la fecha, la tratamos como antigua pero la conservamos si es conversación

        # CONSERVAR si es reciente O si es parte de una conversación
        if es_reciente or es_conversacion:
            declaraciones_conservadas.append(declaracion)
        else:
            declaraciones_para_archivar.append(declaracion)

    # 3. Guardar los resultados
    print("\n--- RESULTADOS ---")
    print(f"Total de declaraciones leídas: {len(declaraciones)}")
    print(f"Declaraciones conservadas en el archivo principal: {len(declaraciones_conservadas)}")
    print(f"Declaraciones que se moverán al archivo histórico: {len(declaraciones_para_archivar)}")

    if not declaraciones_para_archivar:
        print("No hay declaraciones antiguas que archivar. El sistema no se modificará.")
        return

    # --- NUEVA LÓGICA DE ARCHIVADO ---
    # 4. Leer el archivo histórico existente para no sobrescribirlo
    historico_existente = []
    if os.path.exists(ARCHIVO_HISTORICO):
        try:
            with open(ARCHIVO_HISTORICO, 'r', encoding='utf-8') as f:
                historico_existente = json.load(f)
        except json.JSONDecodeError:
            print(f"ADVERTENCIA: El archivo histórico '{ARCHIVO_HISTORICO}' está corrupto. Se creará uno nuevo.")
            historico_existente = []

    # 5. Combinar el histórico antiguo con las nuevas declaraciones a archivar
    historico_actualizado = historico_existente + declaraciones_para_archivar
    print(f"El archivo histórico pasará de {len(historico_existente)} a {len(historico_actualizado)} entradas.")

    # 6. Guardar ambos archivos
    # Guardar el nuevo histórico acumulado
    with open(ARCHIVO_HISTORICO, 'w', encoding='utf-8') as f:
        json.dump(historico_actualizado, f, indent=4, ensure_ascii=False)
    print(f"Se ha actualizado el archivo histórico en '{ARCHIVO_HISTORICO}'")

    # Sobrescribir el archivo de declaraciones principal solo con las conservadas
    with open(ARCHIVO_DECLARACIONES, 'w', encoding='utf-8') as f:
        json.dump(declaraciones_conservadas, f, indent=4, ensure_ascii=False)
    print(f"✅ El archivo '{ARCHIVO_DECLARACIONES}' ha sido limpiado y actualizado.")


if __name__ == "__main__":
    limpiar_declaraciones_antiguas()