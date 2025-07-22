import json
from datetime import datetime, timedelta
import os

# --- CONFIGURACIÓN ---
ARCHIVO_DECLARACIONES = 'declaraciones.json'
DIAS_ANTIGUEDAD_PARA_BORRAR = 7

def limpiar_declaraciones_antiguas():
    """
    Limpia las declaraciones aplicando dos reglas:
    1. Borra todo lo que tenga más de X días.
    2. EXCEPCIÓN: Conserva los mensajes antiguos si forman parte de una conversación.
    """
    print("--- Iniciando limpieza inteligente de declaraciones ---")

    try:
        with open(ARCHIVO_DECLARACIONES, 'r', encoding='utf-8') as f:
            declaraciones = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"ERROR: No se encontró el archivo '{ARCHIVO_DECLARACIONES}' o está vacío.")
        return

    fecha_limite = datetime.now() - timedelta(days=DIAS_ANTIGUEDAD_PARA_BORRAR)
    
    # 1. Encontrar todos los mensajes que han sido respondidos.
    #    Estos IDs son "sagrados" y no se deben borrar por antigüedad.
    ids_de_mensajes_respondidos = {
        dec["reply_to_message_id"] for dec in declaraciones if dec.get("reply_to_message_id") is not None
    }
    
    print(f"Se han identificado {len(ids_de_mensajes_respondidos)} mensajes que inician una conversación.")

    # 2. Filtrar la lista de declaraciones
    declaraciones_conservadas = []
    declaraciones_archivadas = []
    
    for declaracion in declaraciones:
        es_conversacion = declaracion.get("message_id") in ids_de_mensajes_respondidos
        
        try:
            fecha_declaracion = datetime.fromisoformat(declaracion.get("timestamp", ""))
            es_reciente = fecha_declaracion > fecha_limite
        except (ValueError, TypeError):
            # Si una declaración no tiene fecha o está mal formateada, la conservamos por seguridad
            declaraciones_conservadas.append(declaracion)
            continue

        # CONSERVAR si es reciente O si es parte de una conversación
        if es_reciente or es_conversacion:
            declaraciones_conservadas.append(declaracion)
        else:
            declaraciones_archivadas.append(declaracion)

    # 3. Guardar los resultados y un backup
    print("\n--- RESULTADOS ---")
    print(f"Total de declaraciones leídas: {len(declaraciones)}")
    print(f"Declaraciones conservadas: {len(declaraciones_conservadas)}")
    print(f"Declaraciones a archivar/eliminar: {len(declaraciones_archivadas)}")

    if not declaraciones_archivadas:
        print("No hay declaraciones antiguas que limpiar. El archivo no se modificará.")
        return

    # Guardar un backup de lo eliminado
    timestamp_backup = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_backup = f"backup_declaraciones_{timestamp_backup}.json"
    with open(archivo_backup, 'w', encoding='utf-8') as f:
        json.dump(declaraciones_archivadas, f, indent=4, ensure_ascii=False)
    print(f"Se ha creado un respaldo de las declaraciones eliminadas en '{archivo_backup}'")

    # Sobrescribir el archivo original
    with open(ARCHIVO_DECLARACIONES, 'w', encoding='utf-8') as f:
        json.dump(declaraciones_conservadas, f, indent=4, ensure_ascii=False)
    print(f"✅ El archivo '{ARCHIVO_DECLARACIONES}' ha sido limpiado y actualizado.")


if __name__ == "__main__":
    limpiar_declaraciones_antiguas()