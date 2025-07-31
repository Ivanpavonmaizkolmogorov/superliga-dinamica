import datetime

# --- FUNCIONES DE CÁLCULO ---

def generar_datos_ofertas(config):
    """
    Genera los datos para la tabla de ofertas.
    Devuelve las cabeceras y un diccionario con los datos.
    """
    valor_actual = config["valor_inicial"]
    incremento = config["incremento"]
    fecha_actual = datetime.datetime.strptime(config["fecha_inicio"], "%d/%m/%Y").date()
    num_dias_tabla = config["dias_a_mostrar"]
    
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    column_headers = ["Ofertas (Os)"]
    tabla_datos = {f"{m:.2f}": [] for m in multiplicadores}
    
    for dia_tabla in range(num_dias_tabla):
        num_eventos_dia = 1 if dia_tabla == 0 else 2
        for i in range(1, num_eventos_dia + 1):
            if dia_tabla == 0 and i == 1:
                valor_actual += incremento
            elif i == 2:
                valor_actual += incremento
            column_headers.append(f"{fecha_actual.strftime('%a')[:3]} {i}")
            for m in multiplicadores:
                tabla_datos[f"{m:.2f}"].append(valor_actual * m)
        fecha_actual += datetime.timedelta(days=1)
        
    return column_headers, tabla_datos

def generar_datos_exito(config, datos_ofertas):
    """
    Genera los datos para la tabla de Casos de Éxito.
    """
    puja_k = config["puja_k"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    casos_exito_datos = {f"{m:.2f}": [] for m in multiplicadores}

    for m in multiplicadores:
        key = f"{m:.2f}"
        for oferta in datos_ofertas[key]:
            # La única condición es que la oferta supere la puja
            exito = 1 if oferta >= puja_k else 0
            casos_exito_datos[key].append(exito)
            
    return casos_exito_datos

# --- FUNCIÓN DE IMPRESIÓN ---

def calcular_probabilidades(datos_exito):
    """Calcula las probabilidades ps, qs, zs y de fracaso."""
    if not datos_exito:
        return [], [], [], []

    num_ofertas_posibles = len(datos_exito)
    num_eventos = len(list(datos_exito.values())[0])

    ps_values = []
    for i in range(num_eventos):
        casos_favorables = sum(datos_exito[key][i] for key in datos_exito)
        ps = casos_favorables / num_ofertas_posibles
        ps_values.append(ps)
    
    # --- LÓGICA DE QS CORREGIDA ---
    # qs es la probabilidad de fracaso en el mismo evento s (1 - ps)
    qs_values = [1 - p for p in ps_values]

    zs_values = []
    fracaso_values = []
    prob_llegar_al_evento = 1.0

    for ps in ps_values:
        zs = prob_llegar_al_evento * ps
        zs_values.append(zs)
        prob_llegar_al_evento *= (1 - ps)
        fracaso_values.append(prob_llegar_al_evento)
        
    return ps_values, qs_values, zs_values, fracaso_values

def generar_flujo_neto(config, datos_ofertas):
    """NUEVA FUNCIÓN: Calcula el flujo neto (Oferta - Puja)."""
    puja_k = config["puja_k"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    flujo_neto_datos = {f"{m:.2f}": [] for m in multiplicadores}

    for m in multiplicadores:
        key = f"{m:.2f}"
        for oferta in datos_ofertas[key]:
            flujo_neto = oferta - puja_k
            flujo_neto_datos[key].append(flujo_neto)
    
    return flujo_neto_datos

def calcular_prob_suceso_individual(fracaso_acumulado, num_ofertas):
    """NUEVA FUNCIÓN: Calcula la probabilidad de suceso individual."""
    prob_oferta_unica = 1 / num_ofertas
    prob_suceso_individual = []
    
    # La probabilidad de llegar al primer evento es 1
    prob_llegar_al_evento_anterior = 1.0
    
    for i in range(len(fracaso_acumulado)):
        # P(Suceso en s) = P(Llegar a s) * P(Oferta individual)
        prob = prob_llegar_al_evento_anterior * prob_oferta_unica
        prob_suceso_individual.append(prob)
        # Actualizamos la prob. de llegar al SIGUIENTE evento
        prob_llegar_al_evento_anterior = fracaso_acumulado[i]
        
    return prob_suceso_individual

def calcular_ingreso_esperado(datos_flujo, datos_prob_individual):
    """NUEVA FUNCIÓN: Calcula el Ingreso Esperado E(I)."""
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    ingreso_esperado_datos = {f"{m:.2f}": [] for m in multiplicadores}
    
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, flujo in enumerate(datos_flujo[key]):
            # La condición: solo si el flujo es positivo
            if flujo > 0:
                probabilidad = datos_prob_individual[key][i]
                ingreso_esperado = probabilidad * flujo
            else:
                ingreso_esperado = 0
            ingreso_esperado_datos[key].append(ingreso_esperado)

    return ingreso_esperado_datos

def calcular_gasto_esperado(datos_flujo, datos_prob_individual):
    """NUEVA FUNCIÓN: Calcula el Gasto Esperado E(G)."""
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    gasto_esperado_datos = {f"{m:.2f}": [] for m in multiplicadores}
    num_eventos = len(datos_flujo["1.05"])
    
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, flujo in enumerate(datos_flujo[key]):
            gasto_esperado = 0
            # Las condiciones: solo en el último evento y si el flujo es negativo
            if i == (num_eventos - 1) and flujo < 0:
                probabilidad = datos_prob_individual[key][i]
                gasto_esperado = probabilidad * flujo
            
            gasto_esperado_datos[key].append(gasto_esperado)

    return gasto_esperado_datos

# --- NUEVAS FUNCIONES ESPECÍFICAS ---
def sumar_ingresos(datos_ingreso_esperado):
    """Suma los valores de cada columna de la tabla de Ingresos Esperados."""
    if not datos_ingreso_esperado:
        return []
    num_eventos = len(list(datos_ingreso_esperado.values())[0])
    suma_por_columna = [sum(datos_ingreso_esperado[key][i] for key in datos_ingreso_esperado) for i in range(num_eventos)]
    return suma_por_columna

def sumar_gastos(datos_gasto_esperado):
    """Suma los valores de cada columna de la tabla de Gastos Esperados."""
    if not datos_gasto_esperado:
        return []
    num_eventos = len(list(datos_gasto_esperado.values())[0])
    suma_por_columna = [sum(datos_gasto_esperado[key][i] for key in datos_gasto_esperado) for i in range(num_eventos)]
    return suma_por_columna


def calcular_beneficio(suma_ingresos, suma_gastos, zs, fracaso):
    """NUEVA FUNCIÓN: Calcula el beneficio esperado final."""
    beneficio_values = []
    for i in range(len(suma_ingresos)):
        # Fórmula: SUMA(E(I)) * zs + SUMA(E(G)) * fracaso
        beneficio = (suma_ingresos[i] * zs[i]) + (suma_gastos[i] * fracaso[i])
        beneficio_values.append(beneficio)
    return beneficio_values

def calcular_esperanza_matematica(datos_beneficio):
    """NUEVA FUNCIÓN: Suma el vector de beneficios para obtener el valor final."""
    return sum(datos_beneficio)

# --- FUNCIONES DE IMPRESIÓN ---
def imprimir_tabla(cabeceras, datos, titulo, label_filas):
    print(f"\n\n--- {titulo} ---")
    header_line = f"{label_filas:<12}"
    for header in cabeceras[1:]: header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    for m in multiplicadores:
        key = f"{m:.2f}"
        row_line = f"{m:<12.2f}"
        for valor in datos[key]:
            if isinstance(valor, float): row_line += f" | {valor:>15.10f}"
            else: row_line += f" | {valor:>15}"
        print(row_line)

def imprimir_probabilidades(cabeceras, ps, qs, zs, fracaso):
    print("\n\n--- TABLA DE ANÁLISIS DE PROBABILIDAD ---")
    header_line = f"{'Probabilidad':<20}"
    for header in cabeceras[1:]: header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    ps_line = f"{'ps [P(Os>=K|F)]':<20}"; qs_line = f"{'qs':<20}"
    zs_line = f"{'zs [P(Os>=K)]':<20}"; fracaso_line = f"{'P(Fracaso Acum.)':<20}"
    for p, q, z, f in zip(ps, qs, zs, fracaso):
        ps_line += f" | {p:>15.10f}"; qs_line += f" | {q:>15.10f}"
        zs_line += f" | {z:>15.10f}"; fracaso_line += f" | {f:>15.10f}"
    print(ps_line); print(qs_line); print(zs_line); print(fracaso_line)

def imprimir_suma(cabeceras, datos_suma, titulo):
    print(f"\n\n--- {titulo} ---")
    header_line = f"{'Total':<12}"
    for header in cabeceras[1:]: header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    row_line = f"{'':<12}"
    for valor in datos_suma:
        row_line += f" | {valor:>15.10f}"
    print(row_line)

# --- BLOQUE PRINCIPAL ---
if __name__ == "__main__":
    # 1. CONFIGURACIÓN DEL USUARIO
    config = {
        "valor_inicial": 9856, "incremento": 127, "puja_k": 10100,
        "fecha_inicio": "1/8/2025", "dias_solares_configurados": 5
    }
    config["dias_a_mostrar"] = config["dias_solares_configurados"] - 1

    # 2. EJECUCIÓN DE LAS FUNCIONES DE CÁLCULO
    cabeceras, datos_ofertas = generar_datos_ofertas(config)
    datos_exito = generar_datos_exito(config, datos_ofertas)
    ps, qs, zs, fracaso = calcular_probabilidades(datos_exito)
    datos_flujo_neto = generar_flujo_neto(config, datos_ofertas)
    vector_suceso_individual = calcular_prob_suceso_individual(fracaso, len(datos_exito))
    datos_suceso_individual = {f"{(1.05 - i * 0.01):.2f}": vector_suceso_individual for i in range(11)}
    datos_ingreso_esperado = calcular_ingreso_esperado(datos_flujo_neto, datos_suceso_individual)
    datos_gasto_esperado = calcular_gasto_esperado(datos_flujo_neto, datos_suceso_individual)
    suma_ingresos = sumar_ingresos(datos_ingreso_esperado)
    suma_gastos = sumar_gastos(datos_gasto_esperado)
    datos_beneficio = calcular_beneficio(suma_ingresos, suma_gastos, zs, fracaso)
    
    # Se calcula la esperanza matemática final
    esperanza_matematica = calcular_esperanza_matematica(datos_beneficio)

    # 3. IMPRESIÓN DE TODOS LOS RESULTADOS
    imprimir_tabla(cabeceras, datos_ofertas, f"TABLA DE OFERTAS ({config['dias_a_mostrar']} días)", "Ofertas (Os)")
    imprimir_tabla(cabeceras, datos_exito, "TABLA DE CASOS DE ÉXITO", "Casos exito")
    imprimir_probabilidades(cabeceras, ps, qs, zs, fracaso)
    imprimir_tabla(cabeceras, datos_flujo_neto, "TABLA DE FLUJO NETO (GANANCIA/PÉRDIDA)", "Flujo Neto")
    imprimir_tabla(cabeceras, datos_suceso_individual, "TABLA DE PROBABILIDAD DE SUCESO INDIVIDUAL", "P(Suceso Ind.)")
    imprimir_tabla(cabeceras, datos_ingreso_esperado, "TABLA DE INGRESO ESPERADO E(I)", "E(I)")
    imprimir_tabla(cabeceras, datos_gasto_esperado, "TABLA DE GASTO ESPERADO E(G)", "E(G)")
    imprimir_suma(cabeceras, suma_ingresos, "SUMA DE INGRESOS ESPERADOS")
    imprimir_suma(cabeceras, suma_gastos, "SUMA DE GASTOS ESPERADOS")
    imprimir_suma(cabeceras, datos_beneficio, "BENEFICIO ESPERADO (E(V)-s)")
    
    # Se imprime el resultado final
    print("\n\n" + "="*50)
    print(f"== ESPERANZA MATEMÁTICA DE LA COMPRA: {esperanza_matematica:>15.10f} ==")
    print("="*50)