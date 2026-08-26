"""Base de Conocimiento Agronómico Especializada + herramientas de cálculo.

Equivalente al conocimiento práctico de un agrónomo con 30+ años de
experiencia en cultivos colombianos, respaldado por fuentes técnicas
(Agrosavia, Cenicafé, UPRA, ICA, IDEAM).

Regla de oro anti-alucinación: ninguna función devuelve un dato que no
tenga respaldo en esta base o en los datos reales de la finca. Cuando
falta un insumo para un cálculo, se devuelve la lista de lo que falta.
"""

# ═══════════════════════════════════════════════════════════════
# 1. CONOCIMIENTO AGRONÓMICO ESTRUCTURADO (con fuentes trazables)
# ═══════════════════════════════════════════════════════════════

FUENTES = {
    "cenicafe": "Cenicafé — FNC, guías de fertilidad de suelos cafeteros",
    "agrosavia": "Agrosavia — manuales de manejo agronómico por cultivo",
    "upra": "UPRA — zonificaciones de aptitud de cultivos",
    "ica": "ICA — normatividad y manejo fitosanitario",
    "ideam": "IDEAM — climatología y calendario de lluvias de Colombia",
    "faogan": "FAO/ganadería y agricultura — referencias generales de fertilidad",
}

# ── Suelos ──
SUELOS_KB = {
    "ph": {
        "resumen": (
            "El pH mide la acidez de la tierra: menos de 5.5 es muy ácida, "
            "entre 5.5 y 6.5 es ideal para la mayoría de cultivos colombianos, "
            "y por encima de 7.5 es alcalina."
        ),
        "efecto_cultivo": (
            "Con pH muy bajo se amarra el fósforo y se suelta el aluminio, que es "
            "tóxico para la raíz; con pH muy alto se amarran los micronutrientes "
            "(hierro, zinc, manganeso) y las hojas amarillean."
        ),
        "fuentes": [FUENTES["cenicafe"], FUENTES["agrosavia"]],
    },
    "materia_organica": {
        "resumen": (
            "La materia orgánica es la 'vida' del suelo: guarda agua, alimenta los "
            "microorganismos y suelta los nutrientes poco a poco. Debajo del 5% la "
            "tierra pierde cuerpo y se compacta."
        ),
        "fuentes": [FUENTES["agrosavia"], FUENTES["faogan"]],
    },
    "compactacion": {
        "resumen": (
            "Suelo duro = raíz sin aire ni camino. Se corrige con materia orgánica, "
            "siembra en curvas de nivel y evitando maquinaria pesada en suelo húmedo."
        ),
        "fuentes": [FUENTES["agrosavia"]],
    },
    "salinidad": {
        "resumen": (
            "Mucha sal quema las plantas. Se maneja lavando con riego, drenando bien "
            "y abonando en poca cantidad y en tandas."
        ),
        "fuentes": [FUENTES["faogan"], FUENTES["agrosavia"]],
    },
}

# ── Encalado ──
ENCALADO_KB = {
    "resumen": (
        "La cal corrige la acidez: sube el pH, neutraliza el aluminio tóxico y "
        "aporta calcio (y magnesio si es dolomita). Se aplica al voleo, "
        "incorporada al suelo, idealmente 1 a 2 meses antes de sembrar."
    ),
    "cuando": (
        "Aplique cal en seco, no en plena lluvia fuerte: la cal se lava y se pierde. "
        "Mejor en época de pocas lluvias y con el suelo no encharcado."
    ),
    "riesgo_sobreencalado": (
        "Echar cal de más es peor: sube el pH demasiado y amarra micronutrientes. "
        "Por eso la dosis se calcula con el análisis y se corrige por etapas."
    ),
    "fuentes": [FUENTES["cenicafe"], FUENTES["agrosavia"]],
}

# Factores de encalado por textura (t/ha por unidad de pH a corregir)
_FACTOR_TEXTURA_CAL = {"arena": 1.0, "limo": 1.5, "arcilla": 2.0}

# pH objetivo por cultivo (para cálculo de encalado)
_PH_OBJETIVO = {
    "café": 6.0, "cafe": 6.0, "plátano": 6.0, "platano": 6.0, "banano": 6.0,
    "papa": 6.0, "maíz": 6.0, "maiz": 6.0, "tomate": 6.5, "cebolla": 6.5,
    "flores": 6.0, "rosas": 6.0, "cítricos": 6.0, "citricos": 6.0,
    "mango": 6.0, "piña": 5.5, "pina": 5.5, "aguacate": 6.0, "yuca": 5.8,
    "arroz": 6.0, "cacao": 6.0,
}
_PH_OBJETIVO_DEFAULT = 6.0

# ── Riego ──
RIEGO_KB = {
    "frecuencia_textura": {
        "arena": ("cada 2 a 3 días", "el agua se va rápido; riegos cortos y seguidos"),
        "limo": ("cada 3 a 4 días", "retiene agua intermedia; riegos moderados"),
        "arcilla": ("cada 4 a 6 días", "retiene mucha agua; riegos espaciados y sin encharcar"),
    },
    "resumen": (
        "Riegue de mañana temprano o al caer la tarde para que el agua no se evapore. "
        "Menos agua y más seguido vale más que un solo riego abundante. El encharcamiento "
        "ahoga la raíz y trae enfermedades."
    ),
    "fuentes": [FUENTES["agrosavia"], FUENTES["faogan"]],
}

# ── Fertilización ──
FERTILIZACION_KB = {
    "npk": {
        "N": "El nitrógeno es la 'comida verde': hojas y crecimiento. Se lava fácil; aplicar en tandas.",
        "P": "El fósforo agarra raíz y ayuda a florecer y llenar fruto; va cerca de la semilla o en banda.",
        "K": "El potasio da fuerza al tallo, llena el fruto y lo pone dulce; clave al cargar fruto.",
    },
    "organico": (
        "Los abonos orgánicos (compost, estiércol maduro, gallinaza reposada) alimentan "
        "el suelo y sueltan nutrientes despacio; los químicos actúan rápido. Lo mejor es "
        "combinar: orgánico de fondo y químico en tandas."
    ),
    "foliar": (
        "La fertilización foliar sirve para corregir deficiencias puntuales "
        "(sobre todo micronutrientes); no reemplaza la abonada al suelo."
    ),
    "fuentes": [FUENTES["agrosavia"], FUENTES["cenicafe"]],
}

# Conversión ppm → kg/ha (suelo 15-20 cm): factor agronómico práctico
_PPM_A_KGHA = {"nitrogeno": 2.0, "fosforo": 2.0, "potasio": 2.0}

# ── Diagnóstico diferencial de problemas ──
DIAGNOSTICO_KB = {
    "hojas amarillas": [
        ("Deficiencia de nitrógeno", "Amarilleo parejo en hojas viejas; se corrige abonando N en tandas."),
        ("Deficiencia de hierro o zinc", "Hojas nuevas pálidas o amarillas entre venas; común con pH alto."),
        ("Exceso de agua (encharcamiento)", "Amarilleo + hojas caídas; revisar drenaje y bajar riego."),
        ("Problema de raíz (nematodos/hongos)", "Amarilleo con plantas débiles; revisar raíces y suelo."),
        ("Daño por herbicida o salinidad", "Quemazón y amarilleo en parches; revisar aplicación y sales."),
    ],
    "no crece": [
        ("Suelo compactado", "La raíz no avanza; aflojar y aportar materia orgánica."),
        ("Deficiencia de fósforo", "Planta pequeña y morada; abonar P cerca de la raíz."),
        ("Falta de agua o exceso", "Revisar humedad y drenaje."),
        ("pH fuera de rango", "Nutrientes amarrados; corregir acidez/alcalinidad."),
    ],
    "pierde hojas": [
        ("Estrés hídrico (mucha o poca agua)", "Revisar riego y pronóstico de lluvias."),
        ("Deficiencia de potasio o magnesio", "Bordes quemados o caída temprana."),
        ("Ataque de plagas o enfermedades", "Revisar envés de las hojas y tallos."),
    ],
    "suelo duro": [
        ("Compactación por pisoteo o maquinaria", "Aflojar y sembrar curvas de nivel."),
        ("Poca materia orgánica", "Aportar compost o estiércol maduro."),
    ],
}


def diagnostico_diferencial(texto: str) -> dict:
    """Diagnóstico diferencial: NO asume una sola causa; pide más datos."""
    t = (texto or "").lower()
    causas = None
    for clave, lista in DIAGNOSTICO_KB.items():
        if clave in t:
            causas = lista
            break
    if not causas:
        # búsqueda por palabra suelta (amarillas, crece, hojas, duro)
        if "amarill" in t or "amarilla" in t:
            causas = DIAGNOSTICO_KB["hojas amarillas"]
        elif "hoja" in t and ("caer" in t or "cae" in t or "pierde" in t):
            causas = DIAGNOSTICO_KB["pierde hojas"]
        elif "crec" in t or "enana" in t or "pequeña" in t or "pequena" in t:
            causas = DIAGNOSTICO_KB["no crece"]
        elif "duro" in t or "compact" in t:
            causas = DIAGNOSTICO_KB["suelo duro"]
    if not causas:
        return {"encontrado": False}
    return {
        "encontrado": True,
        "causas": [{"causa": c, "detalle": d} for c, d in causas],
        "solicitud_datos": (
            "Para afinar el diagnóstico me sirve saber: hace cuánto empezó, si afecta "
            "hojas viejas o nuevas, si hay encharcamiento, cuándo fue el último abono "
            "y la última lectura de pH del suelo."
        ),
        "fuentes": [FUENTES["agrosavia"], FUENTES["ica"]],
    }


# ═══════════════════════════════════════════════════════════════
# 2. MOTOR DE CÁLCULOS AGRONÓMICOS (herramientas del agente)
# ═══════════════════════════════════════════════════════════════

def calcular_encalado(*, ph_actual, textura, materia_organica, cultivo) -> dict:
    """Dosis orientativa de cal (t/ha). Requiere pH, textura y MO reales."""
    faltan = []
    if ph_actual is None:
        faltan.append("pH del suelo")
    if not textura:
        faltan.append("textura del suelo")
    if materia_organica is None:
        faltan.append("materia orgánica (%)")
    if faltan:
        return {"posible": False, "faltan": faltan}

    factor = _FACTOR_TEXTURA_CAL.get(str(textura).lower(), 1.5)
    ph_obj = _PH_OBJETIVO.get(str(cultivo or "").lower(), _PH_OBJETIVO_DEFAULT)
    delta = ph_obj - float(ph_actual)
    if delta <= 0:
        return {
            "posible": True,
            "dosis_t_ha": 0.0,
            "ph_actual": float(ph_actual),
            "ph_objetivo": ph_obj,
            "formula": "dosis (t/ha) = (pH objetivo − pH actual) × factor de textura × factor de materia orgánica",
            "mensaje": (
                f"Su pH ({ph_actual}) ya está en el nivel buscado para {cultivo or 'su cultivo'} "
                f"({ph_obj}); no necesita encalado por ahora."
            ),
            "confianza": "Media",
            "fuentes": ENCALADO_KB["fuentes"],
        }
    factor_mo = 1.0 if materia_organica < 5 else (1.2 if materia_organica <= 10 else 1.4)
    dosis = round(delta * factor * factor_mo, 1)
    return {
        "posible": True,
        "dosis_t_ha": dosis,
        "ph_actual": float(ph_actual),
        "ph_objetivo": ph_obj,
        "formula": "dosis (t/ha) = (pH objetivo − pH actual) × factor de textura × factor de materia orgánica",
        "mensaje": (
            f"Con pH {ph_actual}, textura {textura} y {materia_organica}% de materia orgánica, "
            f"para {cultivo or 'su cultivo'} la dosis orientativa es {dosis} t/ha de cal "
            "dolomita, al voleo e incorporada, 1 a 2 meses antes de sembrar."
        ),
        "limitaciones": (
            "Para la dosis exacta se necesitan además: CIC, aluminio intercambiable y "
            "saturación de bases (análisis de laboratorio)."
        ),
        "confianza": "Media",
        "fuentes": ENCALADO_KB["fuentes"],
    }


def calcular_fertilizante(*, recomendaciones, lectura_vals, cultivo) -> dict:
    """Estima kg/ha de N, P y K a corregir según el déficit contra el ideal."""
    if not recomendaciones:
        return {"posible": False, "faltan": ["recomendaciones del motor (rango ideal por variable)"]}
    resultados = []
    for rec in recomendaciones:
        estado = str(rec.get("estado") or "").upper()
        variable = str(rec.get("variable") or "").lower()
        if estado != "DEFICIT" or variable not in _PPM_A_KGHA:
            continue
        rango = str(rec.get("rango_ideal") or "")
        nums = [n for n in rango.replace("[", "").replace("]", "").split("-") if n.strip()]
        try:
            minimo = float(nums[0])
        except (ValueError, IndexError):
            continue
        actual = lectura_vals.get(variable)
        if actual is None:
            continue
        deficit = max(0.0, minimo - actual)
        if deficit <= 0:
            continue
        kg_ha = round(deficit * _PPM_A_KGHA[variable], 0)
        resultados.append({
            "nutriente": variable,
            "kg_ha": kg_ha,
            "nota": "aplicar fraccionado en 2-3 tandas durante el ciclo",
        })
    if not resultados:
        return {
            "posible": True,
            "mensaje": (
                "Con los datos actuales no hay un déficit claro de N, P o K que corregir. "
                "Mantenga la materia orgánica y repita el análisis."
            ),
            "fuentes": FERTILIZACION_KB["fuentes"],
        }
    return {
        "posible": True,
        "resultados": resultados,
        "cultivo": cultivo,
        "mensaje": "Dosis orientativas calculadas del déficit contra el rango ideal del motor.",
        "limitaciones": (
            "Es una guía general (factor de conversión ppm→kg/ha en los primeros 15-20 cm de "
            "suelo). El técnico puede ajustar según el análisis de laboratorio y la etapa."
        ),
        "confianza": "Media",
        "fuentes": FERTILIZACION_KB["fuentes"],
    }


def recomendar_riego(*, textura, humedad_actual, humedad_ideal, clima) -> dict:
    """Frecuencia y forma de riego según textura, humedad y clima disponible."""
    if not textura:
        return {"posible": False, "faltan": ["textura del suelo"]}
    frec, detalle = RIEGO_KB["frecuencia_textura"].get(str(textura).lower(), ("cada 3 a 4 días", "riego moderado"))
    partes = [f"Con suelo {textura}, riegue {frec} ({detalle})."]
    if humedad_actual is not None and humedad_ideal:
        partes.append(f"Su suelo está al {humedad_actual}% y lo bueno es {humedad_ideal}; ajuste el riego para acercarse a ese rango.")
    if clima:
        lluvia = clima.get("lluvia_reciente")
        if lluvia:
            partes.append(f"Hubo lluvias recientes ({lluvia}); espacie el riego y revise que el suelo no esté encharcado.")
    partes.append("Riegue de mañana temprano o al atardecer, poca agua y seguido, sin encharcar.")
    return {
        "posible": True,
        "frecuencia": frec,
        "mensaje": " ".join(partes),
        "confianza": "Media" if humedad_actual is not None else "Baja",
        "fuentes": RIEGO_KB["fuentes"],
    }


# ═══════════════════════════════════════════════════════════════
# 3. CLIMA (lo disponible, sin inventar pronósticos)
# ═══════════════════════════════════════════════════════════════

# Calendario lluvias aproximado por región colombiana (IDEAM).
# Rangos en meses numéricos (inicio, fin) para comparar con la fecha actual.
_CLIMA_REGION = {
    "andina": {"lluvias": [(3, 5), (9, 11)], "secas": [(12, 2), (6, 8)]},
    "caribe": {"lluvias": [(5, 11)], "secas": [(12, 4)]},
    "pacifico": {"lluvias": [(1, 12)], "secas": [(1, 3)]},
    "orinoquia": {"lluvias": [(4, 11)], "secas": [(12, 3)]},
    "amazonia": {"lluvias": [(1, 12)], "secas": []},
}


def _en_rango(mes: int, rangos: list[tuple[int, int]]) -> bool:
    for inicio, fin in rangos:
        if inicio <= fin:
            if inicio <= mes <= fin:
                return True
        else:  # rango que cruza el año (ej. 12→2)
            if mes >= inicio or mes <= fin:
                return True
    return False


def contexto_climatico(*, finca, lectura, fecha) -> dict:
    """Clima disponible SIN inventar: época del año + sensores ambientales.

    El pronóstico externo (IDEAM) se agrega solo si IDEAM_API_KEY está
    configurada; mientras tanto se declara explícitamente no disponible.
    """
    departamento = (finca.departamento or "").strip().lower() if finca else ""
    if "antioquia" in departamento or "quind" in departamento or "risaralda" in departamento \
       or "caldas" in departamento or "tolima" in departamento or "huila" in departamento \
       or "cundinamarca" in departamento or "boyac" in departamento or "santander" in departamento \
       or "norte de santander" in departamento:
        region = "andina"
    elif "atlántico" in departamento or "bolívar" in departamento or "magdalena" in departamento \
         or "cesar" in departamento or "guajira" in departamento or "córdoba" in departamento \
         or "sucre" in departamento:
        region = "caribe"
    elif "valle" in departamento or "cauca" in departamento or "choc" in departamento \
         or "nariño" in departamento:
        region = "pacifico"
    elif "meta" in departamento or "casanare" in departamento or "arauca" in departamento:
        region = "orinoquia"
    else:
        region = None

    mes = fecha.month if fecha else None
    epoca = None
    if region and mes:
        patrones = _CLIMA_REGION[region]
        lluvioso = _en_rango(mes, patrones["lluvias"])
        seco = _en_rango(mes, patrones["secas"])
        if lluvioso and not (patrones["secas"] and seco and lluvioso):
            epoca = "época lluviosa"
        else:
            epoca = "época seca" if seco else "época lluviosa"

    sensores = {}
    if lectura is not None:
        sensores["temperatura_ambiental"] = getattr(lectura, "temperatura_ambiental", None)
        sensores["humedad_ambiental"] = getattr(lectura, "humedad_ambiental", None)

    return {
        "ubicacion": f"{finca.municipio or ''}, {finca.departamento or ''}".strip(", ") if finca else None,
        "fecha": fecha.strftime("%Y-%m-%d") if fecha else None,
        "region_climatica": region,
        "epoca_ano": epoca,
        "sensores_ambientales": sensores,
        "pronostico": None,
        "nota_pronostico": (
            "No hay pronóstico meteorológico externo configurado (se requiere IDEAM_API_KEY). "
            "La información climática se limita a la época del año y a los sensores de la finca."
        ),
    }


def resumen_climatico(clima: dict) -> str:
    """Texto corto del clima para incluir en el contexto del chat."""
    if not clima:
        return "(Sin información climática.)"
    partes = []
    if clima.get("fecha"):
        partes.append(f"Hoy es {clima['fecha']}")
    if clima.get("epoca_ano"):
        partes.append(f"y la finca está en {clima['epoca_ano']}")
    sens = clima.get("sensores_ambientales") or {}
    if sens.get("temperatura_ambiental") is not None:
        partes.append(f"(sensor de la finca: {sens['temperatura_ambiental']} °C ambiente)")
    partes.append(clima.get("nota_pronostico") or "")
    return " ".join(partes)


def contexto_conocimiento() -> str:
    """Base de conocimiento agronómica en texto para el contexto del LLM."""
    partes = []
    for clave in ("ph", "materia_organica", "compactacion", "salinidad"):
        d = SUELOS_KB[clave]
        partes.append(f"[Suelos/{clave}] {d['resumen']} (Fuente: {d['fuentes'][0]})")
    partes.append(
        f"[Encalado] {ENCALADO_KB['resumen']} {ENCALADO_KB['cuando']} "
        f"{ENCALADO_KB['riesgo_sobreencalado']} (Fuentes: {', '.join(ENCALADO_KB['fuentes'])})"
    )
    partes.append(f"[Riego] {RIEGO_KB['resumen']} (Fuentes: {', '.join(RIEGO_KB['fuentes'])})")
    partes.append(
        "[Fertilización/NPK] " + " ".join(FERTILIZACION_KB["npk"].values())
    )
    partes.append(
        f"[Fertilización/Orgánico] {FERTILIZACION_KB['organico']} "
        f"[Fertilización/Foliar] {FERTILIZACION_KB['foliar']} "
        f"(Fuentes: {', '.join(FERTILIZACION_KB['fuentes'])})"
    )
    return "\n".join(partes)
