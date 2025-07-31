import datetime
import locale

# --- FUNCIONES DE CÁLCULO ---

def generar_datos_ofertas_venta(config):
    """
    Genera la tabla de ofertas para un escenario de VENTA.
    """
    valor_actual = config["valor_inicial"]
    incremento = config["incremento"]
    
    # AJUSTE: Si solo queda 1 oferta, el valor inicial ya ha sido incrementado.
    # Se revierte para establecer el valor base correcto para el día.
    if config["ofertas_por_consumir_hoy"] == 1:
        valor_actual -= incremento

    fecha_actual = datetime.datetime.strptime(config["fecha_inicio"], "%d/%m/%Y").date()
    num_dias_tabla = config["dias_a_mostrar"]
    
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    column_headers = ["Ofertas (Os)"]
    tabla_datos = {f"{m:.2f}": [] for m in multiplicadores}
    
    for dia_tabla in range(num_dias_tabla):
        num_eventos_dia = config["ofertas_por_consumir_hoy"] if dia_tabla == 0 else 2
        
        # Si no hay ofertas el primer día, se salta
        if num_eventos_dia == 0 and dia_tabla == 0:
            fecha_actual += datetime.timedelta(days=1)
            continue

        for i in range(1, num_eventos_dia + 1):
            # Lógica final: El valor solo sube en el segundo evento del día.
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
    umbral_exito = config["oferta_maquina"]
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
            # El éxito solo es posible si la oferta supera el umbral Y NO es el primer día
            exito = 1 if oferta >= umbral_exito and dia_actual_del_evento > 1 else 0
            casos_exito_datos[key].append(exito)
            
    return casos_exito_datos

def calcular_probabilidades(datos_exito):
    """
    NUEVO: Calcula el modelo de probabilidad completo (ps, qs, zs, fracaso).
    """
    if not datos_exito or not any(datos_exito.values()): return [], [], [], []
    num_ofertas_posibles = len(datos_exito)
    num_eventos = len(list(datos_exito.values())[0])

    ps_values = [sum(datos_exito[key][i] for key in datos_exito) / num_ofertas_posibles for i in range(num_eventos)]
    qs_values = [1 - p for p in ps_values]
    zs_values, fracaso_values, prob_llegar_al_evento = [], [], 1.0

    for ps in ps_values:
        zs_values.append(prob_llegar_al_evento * ps)
        prob_llegar_al_evento *= (1 - ps)
        fracaso_values.append(prob_llegar_al_evento)
        
    return ps_values, qs_values, zs_values, fracaso_values
def calcular_prob_suceso_individual(fracaso_acumulado, num_ofertas):
    """Calcula la probabilidad de suceso individual usando el fracaso acumulado."""
    prob_oferta_unica = 1 / num_ofertas
    prob_suceso_individual = []
    prob_llegar_al_evento_anterior = 1.0
    
    for i in range(len(fracaso_acumulado)):
        prob_suceso_individual.append(prob_llegar_al_evento_anterior * prob_oferta_unica)
        prob_llegar_al_evento_anterior = fracaso_acumulado[i]
        
    datos_suceso_individual = {f"{(1.05 - i * 0.01):.2f}": prob_suceso_individual for i in range(11)}
    
    return datos_suceso_individual

def generar_flujo_neto(config, datos_ofertas):
    """Calcula el flujo neto (Oferta de Mercado - Oferta de la Máquina)."""
    oferta_maquina = config["oferta_maquina"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    flujo_neto_datos = {f"{m:.2f}": [] for m in multiplicadores}

    for m in multiplicadores:
        key = f"{m:.2f}"
        for oferta in datos_ofertas[key]:
            # El cálculo ya no redondea
            flujo_neto_datos[key].append(oferta - oferta_maquina)
    
    return flujo_neto_datos

def calcular_ingreso_esperado(datos_flujo, datos_prob_individual):
    """NUEVO: Calcula el Ingreso Esperado E(I)."""
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    ingreso_esperado_datos = {f"{m:.2f}": [] for m in multiplicadores}
    
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, flujo in enumerate(datos_flujo[key]):
            if flujo > 0:
                ingreso_esperado = datos_prob_individual[key][i] * flujo
            else:
                ingreso_esperado = 0
            ingreso_esperado_datos[key].append(ingreso_esperado)

    return ingreso_esperado_datos

def calcular_gasto_esperado(datos_flujo, datos_prob_individual):
    """NUEVO: Calcula el Gasto Esperado E(G)."""
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    gasto_esperado_datos = {f"{m:.2f}": [] for m in multiplicadores}
    num_eventos = len(datos_flujo["1.05"])
    
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, flujo in enumerate(datos_flujo[key]):
            gasto_esperado = 0
            if i == (num_eventos - 1) and flujo < 0:
                probabilidad = datos_prob_individual[key][i]
                gasto_esperado = probabilidad * flujo
            gasto_esperado_datos[key].append(gasto_esperado)

    return gasto_esperado_datos
def calcular_ingreso_esperado(datos_flujo, datos_prob_individual):
    """Calcula el Ingreso Esperado E(I)."""
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    ingreso_esperado_datos = {f"{m:.2f}": [] for m in multiplicadores}
    
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, flujo in enumerate(datos_flujo[key]):
            if flujo > 0:
                ingreso_esperado = datos_prob_individual[key][i] * flujo
            else:
                ingreso_esperado = 0
            ingreso_esperado_datos[key].append(ingreso_esperado)

    return ingreso_esperado_datos

def calcular_gasto_esperado(datos_flujo, datos_prob_individual):
    """Calcula el Gasto Esperado E(G)."""
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    gasto_esperado_datos = {f"{m:.2f}": [] for m in multiplicadores}
    num_eventos = len(datos_flujo["1.05"])
    
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, flujo in enumerate(datos_flujo[key]):
            gasto_esperado = 0
            if i == (num_eventos - 1) and flujo < 0:
                probabilidad = datos_prob_individual[key][i]
                gasto_esperado = probabilidad * flujo
            gasto_esperado_datos[key].append(gasto_esperado)

    return gasto_esperado_datos

def sumar_ingresos(datos_ingreso_esperado):
    """NUEVO: Suma los valores de la tabla de Ingresos Esperados por columna."""
    if not datos_ingreso_esperado: return []
    num_eventos = len(list(datos_ingreso_esperado.values())[0])
    return [sum(datos_ingreso_esperado[key][i] for key in datos_ingreso_esperado) for i in range(num_eventos)]

def sumar_gastos(datos_gasto_esperado):
    """NUEVO: Suma los valores de la tabla de Gastos Esperados por columna."""
    if not datos_gasto_esperado: return []
    num_eventos = len(list(datos_gasto_esperado.values())[0])
    return [sum(datos_gasto_esperado[key][i] for key in datos_gasto_esperado) for i in range(num_eventos)]
def calcular_beneficio(suma_ingresos, suma_gastos, zs, fracaso):
    """NUEVO: Calcula el beneficio esperado final."""
    beneficio_values = []
    for i in range(len(suma_ingresos)):
        # Fórmula: SUMA(E(I)) * zs + SUMA(E(G)) * fracaso
        beneficio = (suma_ingresos[i] * zs[i]) + (suma_gastos[i] * fracaso[i])
        beneficio_values.append(beneficio)
    return beneficio_values
def calcular_esperanza_matematica_venta(datos_beneficio):
    """NUEVO: Suma el vector de beneficios y multiplica por -1."""
    return sum(datos_beneficio) * -1

# --- FUNCIONES DE IMPRESIÓN ---

def imprimir_tabla(cabeceras, datos, titulo, label_filas):
    print(f"\n--- {titulo} ---")
    header_line = f"{label_filas:<12}"
    for header in cabeceras[1:]: header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    for m in multiplicadores:
        key = f"{m:.2f}"
        row_line = f"{locale.format_string('%.2f', m, grouping=True):<12}"
        for valor in datos[key]:
            if "PROBABILIDAD" in titulo.upper() or "E(I)" in titulo.upper() or "E(G)" in titulo.upper():
                 row_line += f" | {locale.format_string('%15.10f', valor, grouping=True)}"
            else:
                 row_line += f" | {locale.format_string('%15.2f', valor, grouping=True)}"
        print(row_line)

def imprimir_tabla_exito(cabeceras, datos, titulo, label_filas):
    print(f"\n--- {titulo} ---")
    header_line = f"{label_filas:<12}"
    for header in cabeceras[1:]: header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    for m in multiplicadores:
        key = f"{m:.2f}"
        row_line = f"{locale.format_string('%.2f', m, grouping=True):<12}"
        for valor in datos[key]:
            row_line += f" | {valor:>15}"
        print(row_line)

def imprimir_probabilidades(cabeceras, ps, qs, zs, fracaso):
    print("\n\n--- TABLA DE ANÁLISIS DE PROBABILIDAD ---")
    header_line = f"{'Probabilidad':<20}"
    for header in cabeceras[1:]: header_line += f" | {header:>15}"
    print(header_line); print("-" * len(header_line))
    ps_line = f"{'ps [P(Os>=K|F)]':<20}"; qs_line = f"{'qs':<20}"
    zs_line = f"{'zs [P(Os>=K)]':<20}"; fracaso_line = f"{'P(Fracaso Acum.)':<20}"
    for p, q, z, f in zip(ps, qs, zs, fracaso):
        ps_line += f" | {locale.format_string('%15.10f', p, grouping=True)}"; qs_line += f" | {locale.format_string('%15.10f', q, grouping=True)}"
        zs_line += f" | {locale.format_string('%15.10f', z, grouping=True)}"; fracaso_line += f" | {locale.format_string('%15.10f', f, grouping=True)}"
    print(ps_line); print(qs_line); print(zs_line); print(fracaso_line)

def imprimir_suma(cabeceras, datos_suma, titulo):
    """Imprime una fila de totales."""
    print(f"\n\n--- {titulo} ---")
    header_line = f"{'Total':<12}"
    for header in cabeceras[1:]: header_line += f" | {header:>15}"
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
        "valor_inicial": 13059, "incremento": 36, "puja_k": 10100,
        "fecha_inicio": "31/7/2025", "dias_solares_configurados": 4,
        "ofertas_por_consumir_hoy": 1, "oferta_maquina": 13059
    }
    config_venta["dias_a_mostrar"] = config_venta["dias_solares_configurados"]

    # 2. EJECUCIÓN
    cabeceras, datos_ofertas = generar_datos_ofertas_venta(config_venta)
    datos_exito = generar_datos_exito(config_venta, datos_ofertas)
    ps, qs, zs, fracaso = calcular_probabilidades(datos_exito)
    datos_suceso_individual = calcular_prob_suceso_individual(fracaso, len(datos_exito))
    datos_flujo_neto = generar_flujo_neto(config_venta, datos_ofertas)
    datos_ingreso_esperado = calcular_ingreso_esperado(datos_flujo_neto, datos_suceso_individual)
    datos_gasto_esperado = calcular_gasto_esperado(datos_flujo_neto, datos_suceso_individual)
    suma_ingresos = sumar_ingresos(datos_ingreso_esperado)
    suma_gastos = sumar_gastos(datos_gasto_esperado)
    datos_beneficio = calcular_beneficio(suma_ingresos, suma_gastos, zs, fracaso)
    esperanza_matematica = calcular_esperanza_matematica_venta(datos_beneficio)
    
    # 3. IMPRESIÓN
    imprimir_tabla(cabeceras, datos_ofertas, f"TABLA DE OFERTAS ({config_venta['dias_a_mostrar']} días)", "Ofertas (Os)")
    imprimir_tabla_exito(cabeceras, datos_exito, "TABLA DE CASOS DE ÉXITO (vs Oferta Máquina)", "Casos exito")
    imprimir_probabilidades(cabeceras, ps, qs, zs, fracaso)
    imprimir_tabla(cabeceras, datos_suceso_individual, "TABLA DE PROBABILIDAD DE SUCESO INDIVIDUAL", "P(Suceso Ind.)")
    imprimir_tabla(cabeceras, datos_flujo_neto, "TABLA DE FLUJO NETO (vs. Oferta Máquina)", "Flujo Neto")
    imprimir_tabla(cabeceras, datos_ingreso_esperado, "TABLA DE INGRESO ESPERADO E(I)", "E(I)")
    imprimir_tabla(cabeceras, datos_gasto_esperado, "TABLA DE GASTO ESPERADO E(G)", "E(G)")
    imprimir_suma(cabeceras, suma_ingresos, "SUMA DE INGRESOS ESPERADOS")
    imprimir_suma(cabeceras, suma_gastos, "SUMA DE GASTOS ESPERADOS")
    imprimir_suma(cabeceras, datos_beneficio, "BENEFICIO ESPERADO (E(V)-s)")

    print("\n\n" + "="*60)
    print(f"== ESPERANZA MATEMÁTICA DE LA VENTA: {locale.format_string('%.2f', esperanza_matematica, grouping=True)} ==")
    print("="*60)