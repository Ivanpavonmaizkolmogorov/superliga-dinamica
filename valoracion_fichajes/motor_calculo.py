import numpy as np

OFERTAS_POR_DIA = 2
NUM_DIAS_SIMULACION = 100
RANGO_OFERTA_MIN = 0.95
RANGO_OFERTA_MAX = 1.05
PASO_OFERTA = 0.01

class MotorCalculo:
    DEBUG_MODE = True
    VALOR_OBJETIVO_EXCEL = 46058

    def __init__(self, datos_jugador):
        self.nombre = datos_jugador['nombre']
        self.valor_actual = datos_jugador['valor']
        self.incremento_diario = datos_jugador['incremento']
        self.dias = np.arange(0, NUM_DIAS_SIMULACION + 2)
        self.valor_futuro = self.valor_actual + (self.dias * self.incremento_diario)

    def calcular_valoracion(self, mi_puja, dias_limite, es_compra=True):
        """
        IMPLEMENTACIÓN FINAL - ESPEJO LITERAL DE LA MATEMÁTICA Y ESCALA DEL EXCEL
        """
        
        # 1. Escalar los inputs para que coincidan con el Excel (que trabaja en miles)
        escala = 1000.0
        mi_puja_k = mi_puja / escala
        valores_futuros_escalados = self.valor_futuro / escala
        
        # 2. Definir constantes del modelo
        posibles_multiplicadores = np.round(np.arange(RANGO_OFERTA_MIN, RANGO_OFERTA_MAX + PASO_OFERTA / 2, PASO_OFERTA), 2)
        prob_por_variacion = 1 / len(posibles_multiplicadores)

        # 3. Secuencia de valores base EXACTA del modelo Excel
        valores_base = [
            valores_futuros_escalados[1],  # Oferta 1 (Jueves)
            valores_futuros_escalados[1],  # Oferta 2 (Viernes Mañana)
            valores_futuros_escalados[2]   # Oferta 3 (Viernes Tarde)
        ]
        
        # 4. Inicializar variables
        prob_supervivencia = 1.0
        valor_apuesta_total_escalado = 0.0
        beneficios_paso_calculados = []
        tabla_calculo = []

        # 5. Iterar a través de cada una de las 3 ofertas del modelo
        for i, valor_base in enumerate(valores_base):
            # Calcular el Beneficio (Qs) para cada uno de los 11 escenarios
            beneficios_de_oferta = (valor_base * posibles_multiplicadores) - mi_puja_k

            # Calcular la probabilidad de cada escenario individual (Qs * P(suceso))
            # P(suceso) = P(llegar hasta aquí) * P(de que salga este multiplicador)
            prob_suceso_individual = prob_por_variacion * prob_supervivencia

            # Calcular las tablas E(I) y E(G) para este paso
            e_ingresos_individuales = np.where(beneficios_de_oferta >= 0, beneficios_de_oferta * prob_suceso_individual, 0)
            e_gastos_individuales = np.where(beneficios_de_oferta < 0, beneficios_de_oferta * prob_suceso_individual, 0)

            # Sumar las tablas para obtener el E(I) y E(G) totales del paso
            ingreso_total_paso = np.sum(e_ingresos_individuales)
            gasto_total_paso = np.sum(e_gastos_individuales)
            
            # Aplicar la regla clave: el gasto solo cuenta en el 3er paso (i=2)
            valor_apuesta_paso = ingreso_total_paso if i < 2 else (ingreso_total_paso + gasto_total_paso)
            beneficios_paso_calculados.append(valor_apuesta_paso)
            
            # Actualizar la supervivencia para el SIGUIENTE paso (Ss = Ss-1 * qs)
            prob_exito_oferta_condicional = np.sum(beneficios_de_oferta >= 0) * prob_por_variacion
            prob_supervivencia *= (1 - prob_exito_oferta_condicional)

        # 6. El valor total es la suma de los beneficios de los 3 pasos. No hay venta forzada separada.
        valor_apuesta_total_escalado = sum(beneficios_paso_calculados)
        valor_apuesta_total = valor_apuesta_total_escalado * escala

        # --- LOG DE DEPURACIÓN FINAL ---
        if self.DEBUG_MODE:
            print("\n" + "="*80)
            print(f"--- ANÁLISIS FINAL CON PUJA: {mi_puja:,.0f} € (Lógica Espejo del Excel) ---")
            print("="*80)
            
            total_calculado_debug = 0
            objetivos_excel = [30731, 12445, 2882]
            for i, beneficio_escalado in enumerate(beneficios_paso_calculados):
                beneficio_euros = beneficio_escalado * escala
                total_calculado_debug += beneficio_euros
                objetivo = objetivos_excel[i] if i < len(objetivos_excel) else 0
                print(f"  - Paso {i+1}: {beneficio_euros:>12,.0f} €  (Objetivo Excel: {objetivo:>7,.0f} €, Dif: {beneficio_euros - objetivo:>7,.0f} €)")

            print("-"*80)
            print(f"VALOR DE APUESTA FINAL CALCULADO: {total_calculado_debug:,.0f} €")
            print(f"VALOR DE APUESTA OBJETIVO (EXCEL): {self.VALOR_OBJETIVO_EXCEL:,.0f} €")
            print(f"DIFERENCIA:                       {total_calculado_debug - self.VALOR_OBJETIVO_EXCEL:,.0f} €")
            print("="*80 + "\n")

        # Rellenar la tabla para la UI
        for i, beneficio_escalado in enumerate(beneficios_paso_calculados):
             tabla_calculo.append({
                "Oferta #": i + 1,
                "E(Beneficio) Paso": f"{beneficio_escalado * escala:,.0f} €"
            })
            
        prob_total_de_exito_acumulada = 1 - prob_supervivencia
        return {
            "valor_apuesta": valor_apuesta_total, 
            "probabilidad_beneficio": prob_total_de_exito_acumulada, 
            "tabla_calculo": tabla_calculo
        }

    def encontrar_puja_equilibrio(self, dias_limite, es_compra=True):
        original_debug_mode = self.DEBUG_MODE
        self.DEBUG_MODE = False
        puja_estimada = self.valor_actual
        for _ in range(30):
            resultados = self.calcular_valoracion(puja_estimada, dias_limite, es_compra)
            esperanza_actual = resultados['valor_apuesta']
            if abs(esperanza_actual) < 1: break
            puja_estimada += esperanza_actual
        self.DEBUG_MODE = original_debug_mode
        return int(puja_estimada)