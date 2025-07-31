import numpy as np
import pandas as pd

# ==============================================================================
# PASO 0: INPUTS EXACTOS DEL EXCEL
# ==============================================================================
VALOR_JUGADOR_INICIAL = 9856.0
INCREMENTO_DIARIO = 127.0
MI_PUJA_K = 10100.0
TOTAL_ESCENARIOS = 11.0

def calcular_y_verificar_probabilidades():
    """
    Esta función se centra única y exclusivamente en replicar la tabla
    de probabilidades de tu Excel (ps, qs, zs, Ss).
    """
    print("\n" + "="*80)
    print("--- REPLICANDO LA TABLA DE PROBABILIDADES DEL EXCEL ---")
    print("="*80)

    # --- Cálculos Base (ya verificados) ---
    valor_dia_1 = VALOR_JUGADOR_INICIAL + (1 * INCREMENTO_DIARIO)
    valor_dia_2 = VALOR_JUGADOR_INICIAL + (2 * INCREMENTO_DIARIO)
    valores_base = [valor_dia_1, valor_dia_1, valor_dia_2]
    multiplicadores = np.round(np.arange(1.05, 0.94, -0.01), 2)
    
    tabla_ofertas = np.array([[base * mult for base in valores_base] for mult in multiplicadores])
    tabla_exitos = np.where(tabla_ofertas >= MI_PUJA_K, 1, 0)
    
    # --- CÁLCULO DE LAS 4 FILAS DE PROBABILIDAD ---
    
    # ps y qs
    ps = np.sum(tabla_exitos, axis=0) / TOTAL_ESCENARIOS
    qs = 1 - ps
    
    # zs y Ss
    zs_calculados = []
    Ss_calculados = []
    prob_supervivencia_anterior = 1.0 # Partimos de S(0) = 1
    
    print("Desglose del cálculo de 'zs' y 'Ss':")
    for i in range(len(ps)):
        print(f"\n--- Columna #{i+1} ---")
        # Calculamos zs
        zs_actual = ps[i] * prob_supervivencia_anterior
        zs_calculados.append(zs_actual)
        print(f"  zs = ps * Ss-1 = {ps[i]:.10f} * {prob_supervivencia_anterior:.10f} = {zs_actual:.10f}")
        
        # Calculamos Ss (que tu Excel llama "probabilidad de fracaso en oferta s-ésima")
        # Y que también es la supervivencia para el siguiente paso
        Ss_actual = qs[i] * prob_supervivencia_anterior
        Ss_calculados.append(Ss_actual)
        print(f"  Ss = qs * Ss-1 = {qs[i]:.10f} * {prob_supervivencia_anterior:.10f} = {Ss_actual:.10f}")

        # Actualizamos la supervivencia para la siguiente iteración
        prob_supervivencia_anterior = Ss_actual
        
    # --- TABLA DE RESULTADOS FINAL ---
    print("\n" + "="*80)
    print("TABLA DE PROBABILIDADES FINAL (comparar con tu Excel)")
    print("="*80)
    
    df = pd.DataFrame({
        'Probabilidad': ['ps', 'qs', 'zs', 'Ss'],
        'Columna H': [ps[0], qs[0], zs_calculados[0], Ss_calculados[0]],
        'Columna I': [ps[1], qs[1], zs_calculados[1], Ss_calculados[1]],
        'Columna J': [ps[2], qs[2], zs_calculados[2], Ss_calculados[2]]
    })
    
    print(df.to_string(index=False))
    print("\n" + "="*80)
    print("POR FAVOR, VERIFICA ESTA TABLA:")
    print("¿Coinciden estos 4 valores para cada columna con los de tu Excel?")
    print("Si la respuesta es SÍ, usaremos ESTOS MISMOS números para el cálculo final del beneficio.")
    print("="*80)

# --- Flujo Principal de Ejecución ---
if __name__ == "__main__":
    calcular_y_verificar_probabilidades()