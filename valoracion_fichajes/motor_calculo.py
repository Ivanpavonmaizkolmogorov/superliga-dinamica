import datetime

# --- MOTOR DE CÁLCULO UNIFICADO Y FINAL ---

class MotorCalculo:
    def __init__(self, datos_jugador):
        self.datos_jugador = datos_jugador
    
    # --- MÉTODO PRINCIPAL PARA ANÁLISIS DE COMPRA ---
    def analizar_compra(self, config_usuario):
        config = self._crear_config_compra(config_usuario)
        
        # Secuencia de cálculo para la compra
        cabeceras, datos_ofertas = _generar_datos_ofertas_compra(config)
        datos_exito = _generar_datos_exito_compra(config, datos_ofertas)
        ps, qs, zs, fracaso = _calcular_probabilidades(datos_exito)
        datos_flujo_neto = _generar_flujo_neto_compra(config, datos_ofertas)
        vector_suceso_individual = _calcular_prob_suceso_individual(fracaso, len(datos_exito))
        datos_suceso_individual = {f"{(1.05 - i * 0.01):.2f}": vector_suceso_individual for i in range(11)}
        datos_ingreso_esperado = _calcular_ingreso_esperado(datos_flujo_neto, datos_suceso_individual)
        datos_gasto_esperado = _calcular_gasto_esperado(datos_flujo_neto, datos_suceso_individual)
        suma_ingresos = _sumar_ingresos(datos_ingreso_esperado)
        suma_gastos = _sumar_gastos(datos_gasto_esperado)
        datos_beneficio = _calcular_beneficio(suma_ingresos, suma_gastos, zs, fracaso)
        esperanza_matematica = sum(datos_beneficio)
        
        return {"esperanza_matematica": esperanza_matematica}

    # --- MÉTODO PRINCIPAL PARA ANÁLISIS DE VENTA (VALIDADO) ---
    def analizar_venta(self, config_usuario):
        config = self._crear_config_venta(config_usuario)

        # Secuencia de cálculo completa y validada para la venta
        cabeceras, datos_ofertas = _generar_datos_ofertas_venta(config)
        datos_exito = _generar_datos_exito_venta(config, datos_ofertas)
        ps, qs, zs, fracaso = _calcular_probabilidades(datos_exito)
        datos_flujo_neto = _generar_flujo_neto_venta(config, datos_ofertas)
        vector_suceso_individual = _calcular_prob_suceso_individual(fracaso, len(datos_exito))
        datos_suceso_individual = {f"{(1.05 - i * 0.01):.2f}": vector_suceso_individual for i in range(11)}
        datos_ingreso_esperado = _calcular_ingreso_esperado(datos_flujo_neto, datos_suceso_individual)
        datos_gasto_esperado = _calcular_gasto_esperado(datos_flujo_neto, datos_suceso_individual)
        suma_ingresos = _sumar_ingresos(datos_ingreso_esperado)
        suma_gastos = _sumar_gastos(datos_gasto_esperado)
        datos_beneficio = _calcular_beneficio(suma_ingresos, suma_gastos, zs, fracaso)
        esperanza_matematica = -sum(datos_beneficio)

        return {"esperanza_matematica": esperanza_matematica}
    def encontrar_puja_equilibrio(self, config_usuario, tipo_analisis):
        """
        Este método ahora actúa como un distribuidor: llama a la función correcta
        dependiendo de si es una compra o una venta.
        """
        if tipo_analisis == "fichar":
            return self._encontrar_puja_equilibrio_compra(config_usuario)
        elif tipo_analisis == "vender":
            return self._encontrar_oferta_equilibrio_venta(config_usuario)
        return 0
    # --- Métodos privados para búsqueda de equilibrio ---
    def _encontrar_puja_equilibrio_compra(self, config_usuario):
        """Encuentra el equilibrio para una COMPRA (método iterativo simple)."""
        puja_estimada = self.datos_jugador.get('valor', 0)
        for _ in range(25):
            config_usuario['puja_k'] = puja_estimada
            resultados = self.analizar_compra(config_usuario)
            esperanza_actual = resultados['esperanza_matematica']
            if abs(esperanza_actual) < 1: break
            puja_estimada += esperanza_actual
        return int(puja_estimada)

    def _encontrar_oferta_equilibrio_venta(self, config_usuario):
        """Encuentra el equilibrio para una VENTA (método de bisección, más estable)."""
        limite_inferior = self.datos_jugador.get('valor', 0)
        limite_superior = limite_inferior * 2
        
        config_test = config_usuario.copy()
        config_test['oferta_maquina'] = limite_inferior
        try:
            esperanza_inferior = self.analizar_venta(config_test)['esperanza_matematica']
        except (IndexError, TypeError):
            return int(limite_inferior)

        for _ in range(25):
            oferta_media = (limite_inferior + limite_superior) / 2
            if abs(limite_superior - limite_inferior) < 1: break
            
            config_usuario['oferta_maquina'] = oferta_media
            esperanza_actual = self.analizar_venta(config_usuario)['esperanza_matematica']
            
            if abs(esperanza_actual) < 1:
                return int(oferta_media)
            
            # Lógica de bisección para ajustar los límites
            if (esperanza_inferior > 0 and esperanza_actual > 0) or \
               (esperanza_inferior < 0 and esperanza_actual < 0):
                limite_inferior = oferta_media
            else:
                limite_superior = oferta_media
                
        return int(limite_superior)
    # --- Métodos privados para crear las configuraciones ---
    def _crear_config_compra(self, config_usuario):
        config = {
            "valor_inicial": self.datos_jugador['valor'], "incremento": self.datos_jugador['incremento'],
            "puja_k": config_usuario['puja_k'], "fecha_inicio": datetime.date.today().strftime("%d/%m/%Y"),
            "dias_solares_configurados": config_usuario['dias_solares']
        }
        config["dias_a_mostrar"] = config["dias_solares_configurados"] - 1
        return config

    def _crear_config_venta(self, config_usuario):
        config = {
            "valor_inicial": self.datos_jugador['valor'], "incremento": self.datos_jugador['incremento'],
            "puja_k": self.datos_jugador['valor'], # Para el flujo vs compra original
            "fecha_inicio": datetime.date.today().strftime("%d/%m/%Y"),
            "dias_solares_configurados": config_usuario['dias_solares'],
            "ofertas_por_consumir_hoy": config_usuario.get("ofertas_hoy", 2),
            "oferta_maquina": config_usuario['oferta_maquina']
        }
        config["dias_a_mostrar"] = config["dias_solares_configurados"]
        return config


# --- FUNCIONES DE CÁLCULO GENÉRICas ---
def _calcular_probabilidades(datos_exito):
    if not datos_exito or not any(datos_exito.values()) or len(list(datos_exito.values())[0]) == 0: return [], [], [], []
    num_ofertas_posibles = len(datos_exito); num_eventos = len(list(datos_exito.values())[0])
    ps_values = [sum(datos_exito[key][i] for key in datos_exito) / num_ofertas_posibles for i in range(num_eventos)]
    qs_values = [1 - p for p in ps_values]; zs_values, fracaso_values, prob_llegar_al_evento = [], [], 1.0
    for ps in ps_values:
        zs_values.append(prob_llegar_al_evento * ps); prob_llegar_al_evento *= (1 - ps); fracaso_values.append(prob_llegar_al_evento)
    return ps_values, qs_values, zs_values, fracaso_values

def _calcular_prob_suceso_individual(fracaso_acumulado, num_ofertas):
    if not fracaso_acumulado: return []
    prob_oferta_unica = 1 / num_ofertas; prob_suceso_individual, prob_llegar_al_evento_anterior = [], 1.0
    for i in range(len(fracaso_acumulado)):
        prob_suceso_individual.append(prob_llegar_al_evento_anterior * prob_oferta_unica); prob_llegar_al_evento_anterior = fracaso_acumulado[i]
    return prob_suceso_individual

def _calcular_ingreso_esperado(datos_flujo, datos_prob_individual):
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]; ingreso_esperado_datos = {f"{m:.2f}": [] for m in multiplicadores}
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, flujo in enumerate(datos_flujo[key]): ingreso_esperado_datos[key].append(datos_prob_individual[key][i] * flujo if flujo > 0 else 0)
    return ingreso_esperado_datos

def _calcular_gasto_esperado(datos_flujo, datos_prob_individual):
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]; gasto_esperado_datos = {f"{m:.2f}": [] for m in multiplicadores}
    num_eventos = len(datos_flujo["1.05"])
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, flujo in enumerate(datos_flujo[key]):
            gasto_esperado = 0
            if i == (num_eventos - 1) and flujo < 0: gasto_esperado = datos_prob_individual[key][i] * flujo
            gasto_esperado_datos[key].append(gasto_esperado)
    return gasto_esperado_datos

def _sumar_ingresos(datos_ingreso_esperado):
    if not datos_ingreso_esperado: return []
    num_eventos = len(list(datos_ingreso_esperado.values())[0])
    return [sum(datos_ingreso_esperado[key][i] for key in datos_ingreso_esperado) for i in range(num_eventos)]

def _sumar_gastos(datos_gasto_esperado):
    if not datos_gasto_esperado: return []
    num_eventos = len(list(datos_gasto_esperado.values())[0])
    return [sum(datos_gasto_esperado[key][i] for key in datos_gasto_esperado) for i in range(num_eventos)]

def _calcular_beneficio(suma_ingresos, suma_gastos, zs, fracaso):
    beneficio_values = []
    for i in range(len(suma_ingresos)): beneficio_values.append((suma_ingresos[i] * zs[i]) + (suma_gastos[i] * fracaso[i]))
    return beneficio_values

# --- FUNCIONES ESPECÍFICAS DE COMPRA ---
def _generar_datos_ofertas_compra(config):
    valor_actual = config["valor_inicial"]; incremento = config["incremento"]
    fecha_actual = datetime.datetime.strptime(config["fecha_inicio"], "%d/%m/%Y").date()
    num_dias_tabla = config["dias_a_mostrar"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    column_headers = ["Ofertas (Os)"]; tabla_datos = {f"{m:.2f}": [] for m in multiplicadores}
    for dia_tabla in range(num_dias_tabla):
        num_eventos_dia = 1 if dia_tabla == 0 else 2
        for i in range(1, num_eventos_dia + 1):
            if dia_tabla == 0 and i == 1: valor_actual += incremento
            elif i == 2: valor_actual += incremento
            column_headers.append(f"{fecha_actual.strftime('%a')[:3]} {i}")
            for m in multiplicadores: tabla_datos[f"{m:.2f}"].append(valor_actual * m)
        fecha_actual += datetime.timedelta(days=1)
    return column_headers, tabla_datos

def _generar_datos_exito_compra(config, datos_ofertas):
    puja_k = config["puja_k"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    casos_exito_datos = {f"{m:.2f}": [] for m in multiplicadores}
    for m in multiplicadores:
        for oferta in datos_ofertas[f"{m:.2f}"]: casos_exito_datos[f"{m:.2f}"].append(1 if oferta >= puja_k else 0)
    return casos_exito_datos
    
def _generar_flujo_neto_compra(config, datos_ofertas):
    puja_k = config["puja_k"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    flujo_neto_datos = {f"{m:.2f}": [] for m in multiplicadores}
    for m in multiplicadores:
        for oferta in datos_ofertas[f"{m:.2f}"]: flujo_neto_datos[f"{m:.2f}"].append(oferta - puja_k)
    return flujo_neto_datos

# --- FUNCIONES ESPECÍFICAS DE VENTA ---
def _generar_datos_ofertas_venta(config):
    valor_actual = config["valor_inicial"]; incremento = config["incremento"]
    if config["ofertas_por_consumir_hoy"] == 1: valor_actual -= incremento
    fecha_actual = datetime.datetime.strptime(config["fecha_inicio"], "%d/%m/%Y").date()
    num_dias_tabla = config["dias_a_mostrar"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    column_headers = ["Ofertas (Os)"]; tabla_datos = {f"{m:.2f}": [] for m in multiplicadores}
    for dia_tabla in range(num_dias_tabla):
        num_eventos_dia = config["ofertas_por_consumir_hoy"] if dia_tabla == 0 else 2
        if num_eventos_dia == 0 and dia_tabla == 0: fecha_actual += datetime.timedelta(days=1); continue
        for i in range(1, num_eventos_dia + 1):
            if i == 2: valor_actual += incremento
            column_headers.append(f"{fecha_actual.strftime('%a')[:3]} {i}")
            for m in multiplicadores: tabla_datos[f"{m:.2f}"].append(valor_actual * m)
        fecha_actual += datetime.timedelta(days=1)
    return column_headers, tabla_datos

def _generar_datos_exito_venta(config, datos_ofertas):
    umbral_exito = config["oferta_maquina"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    casos_exito_datos = {f"{m:.2f}": [] for m in multiplicadores}; dias_por_evento = []; dia_actual = 1
    eventos_en_dia = 0; num_eventos_totales = len(list(datos_ofertas.values())[0])
    ofertas_primer_dia = config["ofertas_por_consumir_hoy"]
    for i in range(num_eventos_totales):
        dias_por_evento.append(dia_actual); eventos_en_dia += 1
        limite_eventos = ofertas_primer_dia if dia_actual == 1 else 2
        if eventos_en_dia >= limite_eventos: dia_actual += 1; eventos_en_dia = 0
    for m in multiplicadores:
        key = f"{m:.2f}"
        for i, oferta in enumerate(datos_ofertas[key]):
            dia_actual_del_evento = dias_por_evento[i]
            casos_exito_datos[key].append(1 if oferta >= umbral_exito and dia_actual_del_evento > 1 else 0)
    return casos_exito_datos

def _generar_flujo_neto_venta(config, datos_ofertas):
    oferta_maquina = config["oferta_maquina"]
    multiplicadores = [1.05 - i * 0.01 for i in range(11)]
    flujo_neto_datos = {f"{m:.2f}": [] for m in multiplicadores}
    for m in multiplicadores:
        for oferta in datos_ofertas[f"{m:.2f}"]: flujo_neto_datos[f"{m:.2f}"].append(oferta - oferta_maquina)
    return flujo_neto_datos