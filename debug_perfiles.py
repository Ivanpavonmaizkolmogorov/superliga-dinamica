import json
import os

print("--- INICIANDO DIAGNÓSTICO DE 'perfiles.json' ---")

# 1. Confirmar el directorio de trabajo actual
directorio_actual = os.getcwd()
print(f"Directorio actual: {directorio_actual}")

# 2. Comprobar si el archivo existe en esta ruta
ruta_archivo = os.path.join(directorio_actual, 'perfiles.json')
existe = os.path.exists(ruta_archivo)
print(f"¿Existe 'perfiles.json' en esta ruta? -> {existe}")

if not existe:
    print("\nCONCLUSIÓN: El archivo no existe en el directorio de trabajo. El problema es de ubicación.")
else:
    # 3. Si existe, intentar leerlo y comprobar su contenido
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            perfiles = json.load(f)
        print("Lectura del JSON: ¡Éxito! El archivo no está corrupto.")
        
        # 4. Analizar el contenido
        if not perfiles:
            print("\nCONCLUSIÓN: El archivo está vacío (contiene una lista '[]' vacía).")
        elif not isinstance(perfiles, list):
             print(f"\nCONCLUSIÓN: El archivo no contiene una lista, sino un tipo de dato '{type(perfiles)}'.")
        else:
            print(f"Número de perfiles encontrados: {len(perfiles)}")
            primer_perfil = perfiles[0]
            if 'historial_temporada' in primer_perfil and primer_perfil['historial_temporada']:
                print("El primer perfil contiene datos en 'historial_temporada'.")
                print("\nCONCLUSIÓN: Los datos parecen estar correctos. El error debe estar en otra parte del script principal.")
            else:
                print("El primer perfil NO contiene datos en la clave 'historial_temporada'.")
                print("\nCONCLUSIÓN: El archivo existe y tiene perfiles, pero le falta la información de las jornadas.")

    except json.JSONDecodeError as e:
        print(f"\nERROR DE FORMATO: El archivo 'perfiles.json' está mal formateado y no se puede leer. Error: {e}")
    except Exception as e:
        print(f"\nHA OCURRIDO UN ERROR INESPERADO: {e}")

print("\n--- FIN DEL DIAGNÓSTICO ---")