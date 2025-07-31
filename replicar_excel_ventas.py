import datetime
import locale

# --- Función de Cálculo para la Venta (CORREGIDA) ---
def generar_datos_ofertas_venta(config):
    """
    Genera la tabla de ofertas para un escenario de VENTA con la lógica DEFINITIVA.
    """
    valor_actual = config["valor_inicial"]
    incremento = config["incremento"]
    fecha_actual = datetime.datetime.strptime(config["fecha_inicio"], "%d/%m/%Y").date()
    num_dias_tabla = config["dias_a_mostrar"]
    
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    column_headers = ["Ofertas (Os)"]
    tabla_datos = {f"{m:.2f}": [] for m in multiplicadores}
    
    for dia_tabla in range(num_dias_tabla):
        num_eventos_dia = config["ofertas_por_consumir_hoy"] if dia_tabla == 0 else 2
        
        if num_eventos_dia == 0 and dia_tabla == 0:
            fecha_actual += datetime.timedelta(days=1)
            continue

        for i in range(1, num_eventos_dia + 1):
            # Lógica corregida: El valor solo sube en el segundo evento del día.
            if i == 2:
                valor_actual += incremento
                
            column_headers.append(f"{fecha_actual.strftime('%a')[:3]} {i}")
            for m in multiplicadores:
                tabla_datos[f"{m:.2f}"].append(valor_actual * m)
                
        fecha_actual += datetime.timedelta(days=1)
        
    return column_headers, tabla_datos
def generar_datos_exito(config, datos_ofertas):
    """
    NUEVA FUNCIÓN: Genera la tabla de Casos de Éxito para el escenario de VENTA.
    """
    puja_k = config["puja_k"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    casos_exito_datos = {f"{m:.2f}": [] for m in multiplicadores}
    
    # Reconstrucción interna de la lista de días para cada evento
    dias_por_evento = []
    dia_actual = 1
    eventos_en_dia = 0
    num_eventos_totales = len(list(datos_ofertas.values())[0])
    ofertas_primer_dia = config["ofertas_por_consumir_hoy"]

    for i in range(num_eventos_totales):
        dias_por_evento.append(dia_actual)
        eventos_en_dia += 1
        limite_eventos = ofertas_primer_dia if dia_actual == 1 else 2
        if eventos_en_dia >= limite_eventos:
            dia_actual += 1
            eventos_en_dia = 0

    # Se aplica la lógica de éxito
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, oferta in enumerate(datos_ofertas[key]):
            dia_actual_del_evento = dias_por_evento[i]
            # El éxito solo es posible si la oferta es rentable Y NO es el primer día
            exito = 1 if oferta >= puja_k and dia_actual_del_evento > 1 else 0
            casos_exito_datos[key].append(exito)
            
    return casos_exito_datos

def calcular_prob_suceso_individual_venta(datos_ofertas):
    """
    VERSIÓN SIMPLIFICADA para VENTA: La probabilidad individual es siempre 1/N.
    """
    num_ofertas_posibles = len(datos_ofertas)
    num_eventos = len(list(datos_ofertas.values())[0])
    
    # Para la venta, la probabilidad de cada suceso individual es la misma en cada evento.
    prob_individual = 1 / num_ofertas_posibles
    
    # Creamos un vector con este valor repetido para cada evento
    vector_suceso_individual = [prob_individual] * num_eventos
    
    # Creamos la tabla completa para imprimirla
    datos_suceso_individual = {f"{(1.05 - i * 0.01):.2f}": vector_suceso_individual for i in range(11)}
    
    return datos_suceso_individual
def generar_flujo_neto(config, datos_ofertas):
    """
    Calcula el flujo neto (Oferta de Mercado - Oferta de la Máquina).
    """
    # --- LÓGICA CORREGIDA ---
    # Usamos la oferta de la máquina en lugar de la puja original
    oferta_maquina = config["oferta_maquina"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    flujo_neto_datos = {f"{m:.2f}": [] for m in multiplicadores}

    for m in multiplicadores:
        key = f"{m:.2f}"
        for oferta in datos_ofertas[key]:
            flujo_neto_datos[key].append(oferta - oferta_maquina)
    
    return flujo_neto_datos

def calcular_gasto_esperado(datos_flujo, datos_prob_individual):
    """
    Calcula el Gasto Esperado E(G).
    """
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

def calcular_beneficio_esperado_venta(datos_gasto_esperado):
    """RENOMBRADA: Suma los gastos esperados para obtener el beneficio esperado."""
    if not datos_gasto_esperado: return []
    num_eventos = len(list(datos_gasto_esperado.values())[0])
    return [sum(datos_gasto_esperado[key][i] for key in datos_gasto_esperado) for i in range(num_eventos)]

def calcular_esperanza_matematica_venta(datos_beneficio):
    """NUEVA FUNCIÓN: Suma el beneficio y lo multiplica por -1."""
    return sum(datos_beneficio) * -1

# --- FUNCIONES DE IMPRESIÓN ---

def imprimir_tabla(cabeceras, datos, titulo, label_filas):
    print(f"\n--- {titulo} ---")
    header_line = f"{label_filas:<12}"
    for header in cabeceras[1:]:
        header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    for m in multiplicadores:
        key = f"{m:.2f}"
        row_line = f"{locale.format_string('%.2f', m, grouping=True):<12}"
        for valor in datos[key]:
            if "PROBABILIDAD" in titulo.upper() or "E(G)" in titulo.upper():
                 row_line += f" | {locale.format_string('%15.10f', valor, grouping=True)}"
            else:
                 row_line += f" | {locale.format_string('%15.2f', valor, grouping=True)}"
        print(row_line)

def imprimir_tabla_exito(cabeceras, datos, titulo, label_filas):
    print(f"\n--- {titulo} ---")
    header_line = f"{label_filas:<12}"
    for header in cabeceras[1:]:
        header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    for m in multiplicadores:
        key = f"{m:.2f}"
        row_line = f"{locale.format_string('%.2f', m, grouping=True):<12}"
        for valor in datos[key]:
            row_line += f" | {valor:>15}"
        print(row_line)

def imprimir_suma(cabeceras, datos_suma, titulo):
    """Imprime una fila de totales."""
    print(f"\n\n--- {titulo} ---")
    header_line = f"{'Total':<12}"
    for header in cabeceras[1:]:
        header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    
    row_line = f"{'':<12}"
    for valor in datos_suma:
        row_line += f" | {locale.format_string('%15.10f', valor, grouping=True)}"
    print(row_line)

# --- BLOQUE PRINCIPAL ---
if __name__ == "__main__":
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')
        except locale.Error:
            print("Advertencia: No se encontró la configuración regional española.")

    # 1. CONFIGURACIÓN
    config_venta = {
        "valor_inicial": 9729, "incremento": 127, "puja_k": 10100, 
        "fecha_inicio": "31/7/2025", "dias_solares_configurados": 4,
        "ofertas_por_consumir_hoy": 1, "oferta_maquina": 11480.7
    }
    config_venta["dias_a_mostrar"] = config_venta["dias_solares_configurados"]

    # 2. EJECUCIÓN
    cabeceras, datos_ofertas = generar_datos_ofertas_venta(config_venta)
    datos_exito = generar_datos_exito(config_venta, datos_ofertas)
    datos_suceso_individual = calcular_prob_suceso_individual_venta(datos_ofertas)
    datos_flujo_neto = generar_flujo_neto(config_venta, datos_ofertas)
    datos_gasto_esperado = calcular_gasto_esperado(datos_flujo_neto, datos_suceso_individual)
    
    datos_beneficio_venta = calcular_beneficio_esperado_venta(datos_gasto_esperado)
    esperanza_matematica = calcular_esperanza_matematica_venta(datos_beneficio_venta)

    # 3. IMPRESIÓN
    imprimir_tabla(cabeceras, datos_ofertas, f"TABLA DE OFERTAS ({config_venta['dias_a_mostrar']} días)", "Ofertas (Os)")
    imprimir_tabla_exito(cabeceras, datos_exito, "TABLA DE CASOS DE ÉXITO", "Casos exito")
    imprimir_tabla(cabeceras, datos_suceso_individual, "TABLA DE PROBABILIDAD DE SUCESO INDIVIDUAL", "P(Suceso Ind.)")
    imprimir_tabla(cabeceras, datos_flujo_neto, "TABLA DE FLUJO NETO (vs. Oferta Máquina)", "Flujo Neto")
    imprimir_tabla(cabeceras, datos_gasto_esperado, "TABLA DE GASTO ESPERADO E(G)", "E(G)")
    imprimir_suma(cabeceras, datos_beneficio_venta, "BENEFICIO ESPERADO (E(b^p)s)")
    
    print("\n\n" + "="*60)
    print(f"== ESPERANZA MATEMÁTICA DE LA VENTA: {locale.format_string('%.2f', esperanza_matematica, grouping=True)} ==")
    print("="*60)