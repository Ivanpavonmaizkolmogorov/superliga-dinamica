import numpy as np

# ==============================================================================
# PASO 0: DEFINIR LOS INPUTS EXACTOS DEL EXCEL
# ==============================================================================
VALOR_JUGADOR_INICIAL = 9856.0
INCREMENTO_DIARIO = 127.0
MI_PUJA_K = 10100.0
TOTAL_ESCENARIOS = 11


def replicar_pasos_1_a_4():
    """
    Esta función encapsula todos los pasos que ya hemos verificado.
    Devuelve los valores necesarios para los siguientes cálculos.
    """
    print("\n[Pasos 1-4 Verificados] Ejecutando cálculos base...")
    
    # Paso 1
    valor_dia_1 = VALOR_JUGADOR_INICIAL + (1 * INCREMENTO_DIARIO)
    valor_dia_2 = VALOR_JUGADOR_INICIAL + (2 * INCREMENTO_DIARIO)
    valores_base = [valor_dia_1, valor_dia_1, valor_dia_2]
    multiplicadores = np.round(np.arange(1.05, 0.94, -0.01), 2)
    tabla_ofertas = [[base * mult for base in valores_base] for mult in multiplicadores]
    
    # Paso 2
    tabla_exitos = [[1 if oferta >= MI_PUJA_K else 0 for oferta in fila] for fila in tabla_ofertas]
    
    # Paso 3
    columnas_exito = np.array(tabla_exitos).T
    ps_calculados = [np.sum(col) / TOTAL_ESCENARIOS for col in columnas_exito]
    qs_calculados = [1 - p for p in ps_calculados]
    
    # Paso 4
    Ss_calculados = []
    supervivencia_anterior = 1.0
    for i in range(len(ps_calculados)):
        Ss_actual = supervivencia_anterior * qs_calculados[i]
        Ss_calculados.append(Ss_actual)
        supervivencia_anterior = Ss_actual
        
    print("Cálculos base de probabilidad completados con éxito.")
    return Ss_calculados


def replicar_paso_intermedio_prob_acumulada(Ss):
    """
    NUEVO PASO: Calcula la probabilidad acumulada de éxito (1-Ss)
    que se encuentra en la fila 79 de tu Excel.
    """
    print("\nPASO 4.5: VERIFICACIÓN DE 'P(Os>=K) en antes de t' (Fila 79)")
    print("-" * 60)
    print("Fórmula: 1 - Ss")
    print("-" * 60)
    
    # Calculamos (1-Ss) para cada paso
    prob_acumulada_exito = [1 - s for s in Ss]
    
    # Mostramos los resultados
    headers = ["Col H (Jueves)", "Col I (Viernes)", "Col J (Viernes)"]
    print(f"{headers[0]:>15} | {headers[1]:>15} | {headers[2]:>15}")
    print("-" * 60)
    # Mostramos como porcentaje con 2 decimales, igual que en tu Excel
    print(f"{prob_acumulada_exito[0]:>14.2%} | {prob_acumulada_exito[1]:>15.2%} | {prob_acumulada_exito[2]:>15.2%}")

    # Mostramos los valores esperados del Excel
    print("\nValores de tu Excel (Fila 79):")
    print(f"{'36,36%':>15} | {'59,50%':>15} | {'81,59%':>15}")
    
    print("\n" + "="*80)
    print("POR FAVOR, VERIFICA:")
    print("1. ¿Coinciden estos porcentajes con los de tu Excel?")
    print("2. Si la respuesta es SÍ, avísame para usar este valor en el cálculo final de E(I).")
    print("="*80)


# --- Flujo Principal de Ejecución ---
if __name__ == "__main__":
    print("\n" + "="*80)
    print("--- INICIANDO LA RÉPLICA DEL EXCEL EN LA CONSOLA ---")
    print("="*80)
    
    # Ejecutamos los pasos ya validados y guardamos el resultado de Ss
    Ss_calculados = replicar_pasos_1_a_4()
    
    # Ejecutamos el nuevo paso intermedio
    replicar_paso_intermedio_prob_acumulada(Ss_calculados)