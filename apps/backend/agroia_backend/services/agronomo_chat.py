"""Asesor agronómico conversacional de AgroIA.

Actúa como un experto agrónomo con 30+ años de experiencia en cultivos
colombianos (plátano, café, papa, tomate, cebolla, flores, rosas, cítricos,
mango, piña, etc.).

Modos:
  - LLM (OpenAI): si `OPENAI_API_KEY` está configurada, la respuesta la
    genera el modelo con un prompt de sistema de experto + contexto real
    de la finca (lectura de suelo, reglas, ficha técnica, análisis).
  - Experto local: sin API key, un motor determinista responde con las
    reglas del sistema experto y la lectura de suelo, en lenguaje claro.

Principio rector: el modelo NUNCA inventa; solo responde con la
información del contexto (lectura + reglas + ficha técnica + análisis).
"""

import re

from agroia.config import get_settings
from agroia.logging import get_logger

from agroia_backend.services.agronomo_kb import (
    calcular_encalado,
    calcular_fertilizante,
    diagnostico_diferencial,
    recomendar_riego,
)

settings = get_settings()
logger = get_logger(__name__)

MAX_HISTORIAL = 6  # mensajes previos que se envían al LLM

# ── Prompt de sistema: experto agrónomo colombiano ──
PROMPT_SISTEMA_EXPERTO = (
    "Eres Don Gabriel, un agrónomo colombiano con más de 30 años de experiencia "
    "recorriendo fincas de Colombia. Eres experto en cultivos colombianos: "
    "plátano, café, papa, tomate, cebolla, flores, rosas, cítricos, mango, piña, "
    "maíz, arroz, aguacate, yuca, cacao, caña y hortalizas. "
    "Trabajas para AgroIA y ayudas a campesinos, agrónomos y administradores a "
    "entender el análisis de suelo de su finca y a decidir cómo abonar, sembrar "
    "y cuidar sus cultivos.\n\n"
    "REGLAS ESTRICTAS:\n"
    "1. Responde SOLO con la información del CONTEXTO proporcionado "
    "(lectura de suelo, reglas agronómicas, ficha técnica y análisis).\n"
    "2. NUNCA inventes valores, umbrales ni dosis. Si el contexto no tiene el "
    "dato, dilo con honestidad y sugiere consultar al técnico o a la UMATA.\n"
    "3. Sé DETALLADO y práctico: explica el qué, el porqué, el cómo y el cuándo. "
    "Da pasos numerados y consejos de cómo se hace en el campo.\n"
    "4. Lenguaje según la persona: con campesinos y trabajadores de finca usa "
    "palabras sencillas del campo (evita 'ppm', 'conductividad eléctrica', "
    "'CIC'; di 'la medida de cuánto nutriente hay', 'las sales de la tierra', "
    "'la despensa del suelo') y explica cada término la primera vez. Con "
    "agrónomos o administradores puedes incluir números y unidades.\n"
    "5. Sé concreto: qué hacer, cuánto (según el contexto), cuándo y cómo, "
    "paso a paso.\n"
    "6. Responde en español colombiano, con calidez, respeto y ejemplos "
    "cercanos al campo.\n"
    "7. Al final de respuestas técnicas, recuerda que el análisis es automático "
    "y que el técnico de confianza puede afinar la recomendación."
)

# ── Construcción de contexto ──

_VARIABLES_LECTURA = [
    ("ph", "pH"), ("nitrogeno", "Nitrógeno (N)"), ("fosforo", "Fósforo (P)"),
    ("potasio", "Potasio (K)"), ("calcio", "Calcio (Ca)"), ("magnesio", "Magnesio (Mg)"),
    ("azufre", "Azufre (S)"), ("hierro", "Hierro (Fe)"), ("manganeso", "Manganeso (Mn)"),
    ("zinc", "Zinc (Zn)"), ("cobre", "Cobre (Cu)"), ("boro", "Boro (B)"),
    ("materia_organica", "Materia orgánica (%)"), ("cic", "CIC"),
    ("humedad", "Humedad (%)"), ("temperatura_suelo", "Temperatura del suelo (°C)"),
    ("conductividad_electrica", "Conductividad eléctrica (dS/m)"),
    ("humedad_ambiental", "Humedad ambiental (%)"),
    ("temperatura_ambiental", "Temperatura ambiental (°C)"),
]

# Nombres amigables de variable → clave interna
_ALIAS_VARIABLE = {
    "ph": "ph", "acidez": "ph", "acido": "ph", "ácido": "ph", "ácida": "ph",
    "alcalin": "ph", "amarga": "ph", "agria": "ph", "agrio": "ph",
    "nitrogeno": "nitrogeno", "nitrógeno": "nitrogeno", "urea": "nitrogeno",
    "fosforo": "fosforo", "fósforo": "fosforo", "dap": "fosforo",
    "potasio": "potasio", "cloruro de potasio": "potasio", "kcl": "potasio",
    "calcio": "calcio", "magnesio": "magnesio", "azufre": "azufre",
    "hierro": "hierro", "manganeso": "manganeso", "zinc": "zinc",
    "cobre": "cobre", "boro": "boro",
    "materia organica": "materia_organica", "materia orgánica": "materia_organica",
    "compost": "materia_organica", "gallinaza": "materia_organica", "estiércol": "materia_organica",
    "estiercol": "materia_organica",
    "cic": "cic", "despensa": "cic",
    "humedad": "humedad", "riego": "humedad", "regar": "humedad", "agua": "humedad",
    "conductividad": "conductividad_electrica", "sales": "conductividad_electrica",
    "salado": "conductividad_electrica", "salada": "conductividad_electrica",
    "textura": "textura",
}


def _vars_lectura(lectura) -> str:
    """Convierte una lectura en texto plano para el contexto del modelo."""
    if lectura is None:
        return "(La finca no tiene lecturas de suelo todavía.)"
    lineas = []
    for attr, nombre in _VARIABLES_LECTURA:
        valor = getattr(lectura, attr, None)
        if valor is not None:
            lineas.append(f"- {nombre}: {valor}")
    textura = getattr(lectura, "textura", None)
    if textura and "Textura" not in " ".join(lineas):
        lineas.append(f"- Textura: {textura}")
    ts = getattr(lectura, "ts", None)
    if ts:
        lineas.append(f"- Fecha de la lectura: {ts:%Y-%m-%d %H:%M}")
    return "\n".join(lineas)


def _reglas_texto(reglas) -> str:
    """Reglas agronómicas aplicables (universales + del cultivo)."""
    if not reglas:
        return "(Sin reglas agronómicas cargadas.)"
    lineas = []
    for r in reglas:
        rango = f" entre {r.umbral_min} y {r.umbral_max}" if (
            r.umbral_min is not None or r.umbral_max is not None
        ) else ""
        variable = getattr(r.variable, "value", str(r.variable))
        prioridad = getattr(r.prioridad, "value", str(r.prioridad))
        lineas.append(
            f"- [{variable}{rango}] ({prioridad}, fuente: {r.fuente}): {r.accion}"
        )
    return "\n".join(lineas)


def _ficha_texto(ficha) -> str:
    """Ficha técnica del cultivo en texto plano."""
    if ficha is None:
        return "(Sin ficha técnica del cultivo.)"
    lineas = [f"Fuente: {ficha.fuente}"]
    umbrales = ficha.umbrales or {}
    if isinstance(umbrales, dict):
        for var, datos in umbrales.items():
            if isinstance(datos, dict):
                mini = datos.get("min")
                maxi = datos.get("max")
                unidad = datos.get("unidad") or ""
                fuente = datos.get("fuente") or ""
                if mini is not None or maxi is not None:
                    lineas.append(
                        f"- {var}: ideal entre {mini} y {maxi} {unidad}".strip()
                        + (f" (fuente: {fuente})" if fuente else "")
                    )
    economicos = ficha.datos_economicos or {}
    if isinstance(economicos, dict):
        extras = [
            f"{k.replace('_', ' ')}: {v}"
            for k, v in economicos.items() if v is not None
        ]
        lineas.extend(extras[:6])
    return "\n".join(lineas)


def _analisis_texto(result) -> str:
    """Resultado del motor (clasificación + recomendaciones) en texto plano."""
    if result is None:
        return "(Análisis no disponible.)"
    lineas = [
        f"Clasificación UPRA: {result.clasificacion_upra}",
        f"Confianza: {result.confianza}",
    ]
    for rec in (result.recomendaciones or [])[:12]:
        rango = rec.get("rango_ideal") or ""
        lineas.append(
            f"- {rec.get('variable')}: estado {rec.get('estado')}, "
            f"valor actual {rec.get('valor_actual')}"
            + (f", ideal {rango}" if rango else "")
            + f". Acción: {rec.get('accion')}"
        )
    return "\n".join(lineas)


async def construir_contexto(
    *,
    rol: str,
    finca,
    lectura,
    cultivo,
    ficha,
    reglas,
    analisis,
) -> str:
    """Construye el contexto completo (texto plano) para el LLM."""
    rol_txt = {
        "admin": "administrador de la plataforma",
        "agronomo": "agrónomo profesional",
        "cliente": "campesino dueño de la finca",
    }.get((rol or "").lower(), "usuario")
    partes = [
        f"USUARIO: {rol_txt}.",
        f"FINCA: {finca.nombre}, municipio {finca.municipio or 'N/D'} "
        f"({finca.departamento or 'N/D'}), altitud {finca.altitud_msnm or 'N/D'} msnm, "
        f"área {finca.area_hectareas or 'N/D'} ha.",
        "LECTURA DE SUELO MÁS RECIENTE:",
        _vars_lectura(lectura),
        "REGLAS AGRONÓMICAS APLICABLES:",
        _reglas_texto(reglas),
    ]
    if cultivo is not None:
        partes.append(f"CULTIVO: {cultivo.nombre}"
                      + (f" ({cultivo.nombre_cientifico})" if cultivo.nombre_cientifico else ""))
        partes.append("FICHA TÉCNICA DEL CULTIVO:")
        partes.append(_ficha_texto(ficha))
    partes.append("ANÁLISIS DEL MOTOR AGROIA:")
    partes.append(_analisis_texto(analisis))
    return "\n\n".join(partes)


# ── Motor experto local (fallback sin API key) ──

# Nombres amigables de variable para mostrar al usuario
_NOMBRE_VARIABLE = {
    "ph": "el pH (acidez)", "nitrogeno": "el nitrógeno", "fosforo": "el fósforo",
    "potasio": "el potasio", "calcio": "el calcio", "magnesio": "el magnesio",
    "azufre": "el azufre", "hierro": "el hierro", "manganeso": "el manganeso",
    "zinc": "el zinc", "cobre": "el cobre", "boro": "el boro",
    "materia_organica": "la materia orgánica", "cic": "la CIC (capacidad de intercambio)",
    "humedad": "la humedad/riego", "conductividad_electrica": "las sales del suelo",
    "textura": "la textura",
}

# clave interna → símbolo usado por el motor y las reglas (VariableSuelo)
_RULE_VAR = {
    "ph": "pH", "nitrogeno": "N", "fosforo": "P", "potasio": "K",
    "calcio": "Ca", "magnesio": "Mg", "azufre": "S", "hierro": "Fe",
    "manganeso": "Mn", "zinc": "Zn", "cobre": "Cu", "boro": "B",
    "materia_organica": "MO", "cic": "CIC", "humedad": "humedad",
    "temperatura_suelo": "temperatura_suelo", "conductividad_electrica": "CE",
    "textura": "textura",
}

# símbolo del motor ("P", "K") → clave interna
_VAR_MOTOR = {simbolo.lower(): clave for clave, simbolo in _RULE_VAR.items()}

# Explicación sencilla por variable: (nombre, qué_es)
_DETALLE_VARIABLE = {
    "ph": ("la acidez de la tierra",
           "El pH dice si la tierra está 'agria' (ácida) o 'amarga' (alcalina). "
           "Las plantas comen bien cuando la tierra no está ni muy agria ni muy amarga."),
    "nitrogeno": ("el nitrógeno, la 'comida verde'",
                  "El nitrógeno es el abono que pone verdes las hojas y hace crecer la planta."),
    "fosforo": ("el fósforo",
                "El fósforo es el que agarra la raíz, ayuda a florecer y a llenar bien el fruto."),
    "potasio": ("el potasio",
                "El potasio da fuerza al tallo, llena el fruto y lo pone dulce."),
    "calcio": ("el calcio", "El calcio evita que el fruto se raje o se pudra por la punta."),
    "magnesio": ("el magnesio", "El magnesio ayuda a que las hojas se pinten de un verde parejo."),
    "azufre": ("el azufre", "El azufre mejora el sabor y ayuda a la planta a aprovechar el abono."),
    "hierro": ("el hierro", "El hierro evita que las hojas nuevas nazcan amarillas."),
    "manganeso": ("el manganeso", "El manganeso es un ayudante en pequeñitas cantidades para que la planta respire bien."),
    "zinc": ("el zinc", "El zinc ayuda a que la planta crezca pareja y no se enane."),
    "cobre": ("el cobre", "El cobre ayuda a la planta en cantidades muy pequeñas."),
    "boro": ("el boro", "El boro ayuda a que cuaje la flor y no se caiga."),
    "materia_organica": ("la materia orgánica, la 'vida' del suelo",
                         "La materia orgánica es el compost, la hojarasca y el estiércol maduro: "
                         "es la comida que mantiene viva la tierra."),
    "cic": ("la CIC, la 'despensa' del suelo",
            "La CIC es la despensa de la tierra: cuánta comida puede guardar para la planta sin que se la lleve la lluvia."),
    "humedad": ("la humedad, el agua de la tierra",
                "La humedad dice si la tierra tiene suficiente agua para que la planta beba."),
    "conductividad_electrica": ("las sales de la tierra",
                                "Este número dice cuánta sal tiene la tierra; si hay mucha, quema las plantas."),
    "textura": ("la textura, lo suelta o apretada que está la tierra",
                "La textura dice si la tierra es arenosa (suelta), limosa o arcillosa (apretada)."),
}

# Consejos prácticos por estado (para dar el 'cómo y cuándo')
_COMO_CUANDO = {
    "DEFICIT": ("Aplíquelo en dos o tres tandas y no todo de un solo golpe, repartido por todo el lote, "
                "de preferencia cuando empiecen las lluvias o después de un riego."),
    "EXCESO": ("No le eche más por ahora; deje descansar la tierra una temporada y, si son sales, "
               "riegue seguido para lavarlas poco a poco."),
    "OK": ("Está en su punto: manténgalo así con abonos orgánicos maduros y un análisis cada 6 meses."),
}

# Consejos específicos por variable (más precisos que el genérico)
_COMO_CUANDO_VAR = {
    "humedad": {
        "DEFICIT": ("Riegue de mañana temprano o al caer la tarde, poca agua y seguido, "
                    "sin encharcar; el riego por goteo rinde más."),
        "EXCESO": ("Deje de regar unos días, revise que el suelo drene bien y evite el encharcamiento."),
    },
    "ph": {
        "DEFICIT": ("Si la tierra está agria (ácida), endulcela con cal dolomita o cal agrícola al voleo, "
                    "de preferencia un mes antes de sembrar, y revuélvala con el suelo."),
        "EXCESO": ("Si la tierra está amarga (alcalina), rebájela con yeso agrícola o abonos ácidos, "
                   "repartidos parejos y mezclados con el suelo."),
    },
    "conductividad_electrica": {
        "EXCESO": ("Riegue seguido para lavar las sales poco a poco y use los abonos en poca cantidad."),
    },
    "materia_organica": {
        "DEFICIT": ("Eche compost, estiércol maduro o gallinaza reposada y déjela descomponer; "
                    "la tierra queda más suelta y guarda mejor el agua."),
    },
}


def _consejo_estado(clave: str, estado: str) -> str:
    """Consejo de 'cómo y cuándo' específico por variable, con genérico de respaldo."""
    especifico = _COMO_CUANDO_VAR.get(clave, {}).get(estado)
    return especifico or _COMO_CUANDO.get(estado, "")


def _accion_sin_duplicado(nombre: str, accion: str | None) -> str:
    """Quita la palabra repetida cuando la acción empieza con el nombre
    (p. ej. nombre 'el fósforo' y acción 'Fósforo: 100-200 kg/ha...')."""
    a = (accion or "").strip()
    if not a or ":" not in a:
        return a
    cabeza = a.split(":", 1)[0].strip().lower()
    palabras_nombre = set(re.findall(r"[a-záéíóúñ]+", (nombre or "").lower()))
    if cabeza in palabras_nombre:
        return a.split(":", 1)[1].strip()
    return a


def _nombre_rec(rec: dict) -> str:
    """Nombre amigable para una recomendación del motor (variable 'P' → 'el fósforo')."""
    var = str(rec.get("variable") or "").lower().strip()
    clave = _VAR_MOTOR.get(var, var)
    return _NOMBRE_VARIABLE.get(clave, rec.get("variable"))


def _alias_detectado(texto: str) -> str | None:
    """Detecta la variable preguntada; prioriza los alias más largos y exige
    palabra completa para los cortos (p, k, n, ca, ...)."""
    for alias in sorted(_ALIAS_VARIABLE, key=len, reverse=True):
        if len(alias) <= 2:
            if re.search(rf"\b{re.escape(alias)}\b", texto):
                return _ALIAS_VARIABLE[alias]
        elif alias in texto:
            return _ALIAS_VARIABLE[alias]
    return None


def _respuesta_variable(mensaje: str, ctx: dict) -> str | None:
    """Responde sobre una variable específica detectada en el mensaje."""
    texto = mensaje.lower()
    clave = _alias_detectado(texto)
    if clave is None:
        return None
    detalle = _DETALLE_VARIABLE.get(clave)
    nombre = detalle[0] if detalle else _NOMBRE_VARIABLE.get(clave, clave.replace("_", " "))
    que_es = detalle[1] if detalle else ""
    rol = (ctx.get("rol") or "cliente").lower()
    sencillo = rol == "cliente"

    for rec in ctx["recomendaciones"]:
        var = str(rec.get("variable") or "").lower()
        if clave == "ph" and "ph" in var:
            rec = dict(rec)
            rec["variable"] = "ph"
            break
        if var == clave or var == clave.replace("_", ""):
            break
    else:
        rec = None

    # Sin recomendación específica: buscar regla equivalente
    if rec is None:
        simbolo = _RULE_VAR.get(clave, clave).lower()
        for regla in ctx["reglas"]:
            vregla = str(getattr(regla.variable, "value", regla.variable)).lower()
            if vregla == simbolo:
                rango = (f" entre {regla.umbral_min} y {regla.umbral_max}"
                         if regla.umbral_min is not None or regla.umbral_max is not None
                         else "")
                lectura = ctx.get("lectura") or {}
                valor = lectura.get(clave)
                partes = []
                if sencillo and que_es:
                    partes.append(que_es)
                if valor is not None:
                    partes.append(f"Su tierra marcó {valor}.")
                partes.append(
                    f"Lo bueno es mantenerlo{rango}. "
                    f"Recomendación: {regla.accion}"
                )
                return " ".join(partes)
        lectura = ctx.get("lectura") or {}
        valor = lectura.get(clave)
        if valor is not None:
            base = que_es + " " if sencillo and que_es else f"Sobre {nombre}: "
            return (
                f"{base}Su última lectura fue {valor}. "
                "El rango ideal depende del cultivo; revise el reporte generado o "
                "consulte al técnico de su zona para interpretarlo bien."
            )
        return (
            f"Para {nombre} no tengo una lectura ni una regla específica en el contexto de "
            "esta finca. Le sugiero consultar al técnico o a la UMATA más cercana."
        )

    # ── Hay recomendación del motor: respuesta detallada ──
    estado = str(rec.get("estado") or "").upper()
    valor = rec.get("valor_actual")
    rango = rec.get("rango_ideal")
    accion = _accion_sin_duplicado(nombre, rec.get("accion"))
    como = _consejo_estado(clave, estado)

    partes = []
    if sencillo and que_es:
        partes.append(que_es)
    if estado == "DEFICIT":
        partes.append(f"A su tierra le está faltando {nombre}: la lectura fue {valor} y lo bueno está {rango}.")
    elif estado == "EXCESO":
        partes.append(f"Su tierra tiene {nombre} de más: la lectura fue {valor} y lo bueno está {rango}.")
    else:
        partes.append(f"{nombre.title()} está bien: la lectura fue {valor} y lo bueno está {rango}.")
    if accion:
        partes.append(f"Qué hacer: {accion}.")
    if como:
        partes.append(f"Cómo y cuándo: {como}")
    if sencillo:
        partes.append(
            "Si no está seguro de las cantidades, muéstrele este análisis al técnico o a la "
            "UMATA de su zona; con gusto le ayudan a calcular la dosis justa para su lote."
        )
    else:
        partes.append(
            "Recuerde que la dosis exacta depende del cultivo y de la etapa; este análisis "
            "es una guía y el técnico de confianza puede afinarla."
        )
    return " ".join(partes)


def _respuesta_local(mensaje: str, ctx: dict) -> str:
    """Motor determinista: responde con reglas + lectura, sin LLM."""
    texto = mensaje.lower()
    rol = (ctx.get("rol") or "cliente").lower()

    # ── Saludos / cortesía ──
    if re.search(r"^(hola|buenas|buenos dias|buenos días|buenas tardes|quién eres|quien eres|hey|saludos)", texto):
        return (
            "¡Muy buenas! 👋 Soy su asesor agronómico de AgroIA y estoy aquí para ayudarle "
            "con su finca, hablando claro y sin enredos. Puedo explicarle el reporte del suelo, "
            "decirle qué abono echar, qué conviene sembrar, cuánto regar y cómo cuidar su "
            "cultivo paso a paso. Pregúnteme con confianza, por ejemplo: "
            "«¿qué abono debo aplicar?», «¿qué me conviene sembrar?» o «¿cómo está mi tierra?»."
        )
    if re.search(r"(gracias|muy amable|quedo atento)", texto):
        return (
            "¡Con mucho gusto! 🌱 Aquí estaré para lo que necesite. Recuerde que este consejo "
            "es automático y que el técnico o la UMATA de su zona pueden afinar la recomendación. "
            "¡Que la tierra le pague bien!"
        )

    # ── Pregunta por una variable específica ──
    respuesta = _respuesta_variable(mensaje, ctx)
    if respuesta:
        return respuesta

    # ── Siembra ──
    if re.search(r"(sembrar|siembra|plantar|cultivar|qué me conviene|que me conviene)", texto):
        sugerencias = ctx["sugerencias"] or []
        if sugerencias:
            top = sugerencias[0]
            nombre = top.get("cultivo")
            otros = [s.get("cultivo") for s in sugerencias[1:3]]
            partes = [
                f"Según el análisis de su suelo, lo que mejor le va es {nombre}. "
                + (f"También se podrían dar: {', '.join(otros)}. " if otros else ""),
                "Para que le vaya bien, le recomiendo este orden:",
                "1. Corrija primero lo que el reporte marca en rojo (el pH o el nutriente que esté fallando).",
                "2. Prepare bien el terreno: una pasada de arado o azadón, saque piedras y terrones grandes.",
                "3. Siembre con semilla o plántula sana, en el tiempo de lluvias o asegurando riego.",
                "4. Abone en tandas pequeñas durante el crecimiento, no todo de un golpe.",
            ]
            if rol != "cliente":
                partes.append(
                    f"Para más precisión, revise la ficha técnica del {nombre} en el catálogo: "
                    "allí están los umbrales y las fuentes (UPRA/Cenicafé/AGROSAVIA)."
                )
            return " ".join(partes)
        return (
            "Para recomendarle qué sembrar necesito la lectura de suelo de su finca. "
            "Genere primero el reporte o cargue una lectura de sensor, y con gusto le digo "
            "qué cultivo se acomoda mejor a su tierra."
        )

    # ── Abonar / fertilizar (general) ──
    if re.search(r"(abon|fertiliz|nutri)", texto):
        recs = ctx["recomendaciones"] or []
        if not recs:
            return (
                "No tengo lecturas de suelo de esta finca para recomendarle abonos. "
                "Cargue una lectura de sensor o un archivo de mediciones, y con gusto le digo "
                "qué necesita su tierra y cómo aplicarlo."
            )
        principales = [r for r in recs if str(r.get("estado") or "").upper() in ("DEFICIT", "EXCESO")][:4]
        if not principales:
            return (
                "Su suelo está bien nutrido por ahora; no es necesario abonar de más, porque "
                "echar abono de sobra también daña. Siga así: mantenga la materia orgánica "
                "(compost o estiércol maduro) y repita el análisis cada 6 meses."
            )
        partes = ["Le cuento qué necesita su tierra y cómo ayudarla:"]
        for i, r in enumerate(principales, 1):
            nombre = _nombre_rec(r)
            var = str(r.get("variable") or "").lower().strip()
            clave = _VAR_MOTOR.get(var, var)
            estado = str(r.get("estado") or "").upper()
            como = _consejo_estado(clave, estado)
            accion = _accion_sin_duplicado(nombre, r.get("accion"))
            partes.append(f"{i}. {nombre.title()}: {accion}. {como}")
        partes.append(
            "Consejo general: el abono rinde más repartido en dos o tres tandas que todo de "
            "un solo golpe, y siempre pegado a la zona de la raíz o al voleo antes de un riego."
        )
        if rol == "cliente":
            partes.append(
                "Si le quedan dudas con las cantidades, lleve este análisis a la UMATA o a la "
                "agropecuaria de confianza y allá le calculan la dosis exacta para su lote."
            )
        return " ".join(partes)

    # ── Reporte / explicación general ──
    if re.search(r"(reporte|explic|resum|análisis|analisis|cómo está|como esta)", texto):
        clas = ctx["clasificacion"] or "sin clasificar"
        recs = ctx["recomendaciones"] or []
        if rol == "cliente":
            if "no apta" in clas.lower():
                resumen = (
                    f"Hablando claro: hoy su tierra no está cómoda para ese cultivo ({clas}). "
                )
            elif "apta" in clas.lower():
                resumen = (
                    f"Le tengo buenas noticias: su tierra se acomoda bien al cultivo ({clas}). "
                )
            else:
                resumen = f"Su tierra se puede arreglar para ese cultivo ({clas}). "
        else:
            resumen = f"El motor clasificó el suelo como {clas}. "
        if recs:
            resumen += "Esto es lo más importante del reporte: "
            for r in recs[:3]:
                resumen += f" {_nombre_rec(r).title()}: {r.get('accion')}."
            resumen += (
                " En el reporte completo verá el mapa de calor del lote, que le muestra en "
                "colores dónde está bien y dónde hay que corregir, y la sección «En palabras "
                "del campo» con la explicación sencilla de cada medición."
            )
        else:
            resumen += " Genere el reporte con una lectura de sensor para ver el detalle."
        return resumen

    # ── Por defecto: estado general + sugerencias ──
    recs = ctx["recomendaciones"] or []
    if recs:
        criticas = [r for r in recs if str(r.get("prioridad") or "").lower() == "critica"]
        if criticas:
            base = (
                f"Le doy un panorama general de su suelo. Lo primero que le recomiendo atender "
                f"es {_nombre_rec(criticas[0])}: {criticas[0].get('accion')} "
            )
        else:
            base = "Le doy un panorama general de su suelo: no hay urgencias críticas, vamos bien. "
        base += (
            "Si quiere, puedo contarle con detalle: cómo abonar, qué sembrar, cómo está la "
            "acidez (el pH), el riego, o cualquier nutriente en particular (nitrógeno, fósforo, "
            "potasio, calcio…). Solo dígame de cuál quiere saber."
        )
        return base
    return (
        "Todavía no tengo lecturas de suelo de esta finca para aconsejarlo. "
        "Genere primero el reporte (o cargue una lectura de sensor) y vuelva a preguntarme: "
        "aquí estaré para explicarle todo paso a paso."
    )


# ── Orquestador ──

async def consultar_experto(*, mensaje: str, historial: list[dict], contexto: str, rol: str) -> dict:
    """Consulta al LLM (OpenAI) si hay API key; si no, motor local."""
    key = settings.openai_api_key or ""
    if not key or key == "sk-your-key-here":
        return {"respuesta": None, "modo": "local"}

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=key)

        mensajes = [{"role": "system", "content": PROMPT_SISTEMA_EXPERTO}]
        for m in (historial or [])[-MAX_HISTORIAL:]:
            rol_msg = m.get("rol") or "user"
            contenido = m.get("contenido") or ""
            if rol_msg in ("user", "assistant") and contenido:
                mensajes.append({"role": rol_msg, "content": contenido})
        mensajes.append({
            "role": "user",
            "content": (
                "CONTEXTO DE LA FINCA (fuente única de verdad, no inventes datos):\n"
                f"{contexto}\n\n"
                f"PREGUNTA DEL USUARIO ({rol}):\n{mensaje}"
            ),
        })

        response = await client.chat.completions.create(
            model=settings.openai_model or "gpt-4o-mini",
            messages=mensajes,
            max_tokens=700,
            temperature=0.3,
        )
        return {
            "respuesta": response.choices[0].message.content,
            "modo": "llm",
        }
    except Exception as e:  # pragma: no cover — red de OpenAI
        logger.error("openai_chat_error", error=str(e))
        return {"respuesta": None, "modo": "local"}


# ═══════════════════════════════════════════════════════════════
# Orquestador agronómico (capa especializada sobre el motor local)
# ═══════════════════════════════════════════════════════════════

def _rango_variable(recs: list[dict], clave: str) -> str | None:
    for r in recs:
        var = str(r.get("variable") or "").lower().strip()
        clave_motor = _VAR_MOTOR.get(var, var)
        if clave_motor == clave and r.get("rango_ideal"):
            return str(r.get("rango_ideal"))
    return None


def _fundamentar(
    *,
    recomendacion: str,
    por_que: str,
    datos: list[str],
    fuentes: list[str],
    confianza: str,
    falta: str | None = None,
    sencillo: bool = False,
) -> str:
    """Formatea una respuesta fundamentada (qué, por qué, datos, fuentes, falta, confianza)."""
    partes = [recomendacion, por_que]
    if datos:
        partes.append("Datos que utilicé: " + " · ".join(datos) + ".")
    if fuentes:
        partes.append("Fuentes: " + " · ".join(fuentes) + ".")
    if falta:
        partes.append(falta)
    if sencillo:
        partes.append(f"Mi confianza en esta respuesta es {confianza.lower()}.")
    else:
        partes.append(f"Confianza: {confianza}.")
    return " ".join(partes)


def _respuesta_clima(mensaje: str, ctx: dict) -> str:
    """Preguntas de clima/época: responde con lo disponible, sin inventar."""
    clima = ctx.get("clima") or {}
    rol = (ctx.get("rol") or "cliente").lower()
    sencillo = rol == "cliente"
    partes = []
    if clima.get("fecha"):
        partes.append(f"Hoy es {clima['fecha']}.")
    if clima.get("epoca_ano"):
        partes.append(f"Su finca está en {clima['epoca_ano']}.")
    sens = clima.get("sensores_ambientales") or {}
    if sens.get("temperatura_ambiental") is not None:
        partes.append(
            f"El sensor de la finca marca {sens['temperatura_ambiental']} °C de temperatura ambiente."
        )
    texto = mensaje.lower()
    if re.search(r"(fertiliz|abon|cal\b|encal)", texto):
        partes.append(
            "Para aplicar cal o abono, espere a que el suelo no esté encharcado: "
            "en plena lluvia fuerte la cal se lava y el abono se pierde."
        )
    if re.search(r"(regar|riego|agua)", texto):
        partes.append(
            "Si hay lluvias, espacie el riego y revise que el suelo drene; "
            "más vale poca agua y seguido que encharcar."
        )
    partes.append(clima.get("nota_pronostico") or "")
    return _fundamentar(
        recomendacion=" ".join(partes),
        por_que=(
            "Uso la época del año de la zona y los sensores de su finca; "
            "no invento pronósticos si no hay fuente externa."
        ),
        datos=[str(d) for d in (clima.get("fecha"), clima.get("epoca_ano")) if d],
        fuentes=["IDEAM — calendario climático de Colombia (referencia general)"],
        confianza="Media" if clima.get("epoca_ano") else "Baja",
        falta=(
            "Para un pronóstico real de lluvia se necesita conectar la fuente externa (IDEAM_API_KEY)."
            if clima.get("nota_pronostico") else None
        ),
        sencillo=sencillo,
    )


def _respuesta_porque_cultivo(ctx: dict) -> str:
    """Explica POR QUÉ el motor recomendó el cultivo, con los datos reales."""
    rol = (ctx.get("rol") or "cliente").lower()
    sencillo = rol == "cliente"
    sugerencias = ctx.get("sugerencias") or []
    lectura = ctx.get("lectura") or {}
    if not sugerencias:
        return (
            "Todavía no tengo la recomendación del motor para explicarle el porqué. "
            "Genere el reporte o el análisis y vuelva a preguntarme."
        )
    top = sugerencias[0]
    cultivo = top.get("cultivo")
    clasificacion = top.get("clasificacion") or top.get("aptitud")
    score = top.get("score")
    datos = [f"cultivo recomendado: {cultivo}"]
    if lectura.get("ph") is not None:
        datos.append(f"pH del suelo: {lectura['ph']}")
    if lectura.get("materia_organica") is not None:
        datos.append(f"materia orgánica: {lectura['materia_organica']}%")
    if lectura.get("humedad") is not None:
        datos.append(f"humedad: {lectura['humedad']}%")

    por_que = (
        f"El motor comparó su suelo con los umbrales que {cultivo} necesita y encontró "
        f"aptitud {clasificacion or 'favorable'}"
        + (f" (puntaje {score:.1f})" if score is not None else "")
        + ". "
    )
    ph = lectura.get("ph")
    if ph is not None:
        if 5.5 <= ph <= 6.5:
            por_que += "Su pH está en la franja que este cultivo prefiere. "
        elif ph < 5.5:
            por_que += "El pH está agrio, pero se puede corregir con cal antes de sembrar. "
        else:
            por_que += "El pH está alto; hay que manejarlo para que el cultivo coma bien. "
    mo = lectura.get("materia_organica")
    if mo is not None:
        por_que += f"La materia orgánica ({mo}%) " + ("le da buena base al suelo." if mo >= 5 else "está baja, pero se mejora con compost antes de sembrar. ")
    return _fundamentar(
        recomendacion=f"Le recomendamos {cultivo} con base en el análisis de SU finca.",
        por_que=por_que,
        datos=datos,
        fuentes=["UPRA — aptitud por suelo y clima", "Cenicafé/Agrosavia — umbrales del cultivo"],
        confianza="Media",
        falta=(
            "Para afinar, me faltan datos climáticos del sitio (IDEAM) y la altitud exacta del lote."
            if sencillo else
            "Para mayor precisión faltan: clima local (IDEAM), variedad y etapa del cultivo."
        ),
        sencillo=sencillo,
    )


def respuesta_orquestada(mensaje: str, ctx: dict) -> dict:
    """Orquestador agronómico: intención → herramientas → respuesta fundamentada.

    Devuelve {respuesta, fuentes, confianza, datos_utilizados, falta}.
    Si la pregunta no encaja en una intención especializada, delega en el
    motor conversacional general.
    """
    texto = mensaje.lower()
    lectura = ctx.get("lectura") or {}
    recs = ctx.get("recomendaciones") or []
    cultivo = ctx.get("cultivo") or None
    rol = (ctx.get("rol") or "cliente").lower()
    sencillo = rol == "cliente"

    vacio = {"respuesta": None, "fuentes": [], "confianza": None, "datos_utilizados": [], "falta": None}

    # ── 1) Cálculo de encalado ──
    if (re.search(r"\bcal\b", texto) and re.search(r"(cuánta|cuanta|cantidad|dosis|necesito|aplicar|cuánto|cuanto|echar)", texto)) \
       or re.search(r"encala", texto):
        r = calcular_encalado(
            ph_actual=lectura.get("ph"),
            textura=lectura.get("textura"),
            materia_organica=lectura.get("materia_organica"),
            cultivo=cultivo,
        )
        if not r["posible"]:
            return {**vacio, "respuesta": (
                f"No puedo calcular la dosis de cal con los datos actuales. Me falta: "
                f"{', '.join(r['faltan'])}. Haga un análisis de suelo completo (pH, textura "
                "y materia orgánica) y vuelva a preguntarme."
            ), "falta": r["faltan"]}
        datos = [
            f"pH: {r.get('ph_actual')}",
            f"pH objetivo: {r.get('ph_objetivo')}",
            f"cultivo: {cultivo}",
        ]
        return {
            "respuesta": _fundamentar(
                recomendacion=r.get("mensaje") or "",
                por_que=r.get("formula") or "La dosis se calcula según el pH actual, la textura y la materia orgánica.",
                datos=datos,
                fuentes=r.get("fuentes") or [],
                confianza=r.get("confianza", "Media"),
                falta=r.get("limitaciones"),
                sencillo=sencillo,
            ),
            "fuentes": r.get("fuentes") or [],
            "confianza": r.get("confianza", "Media"),
            "datos_utilizados": datos,
            "falta": r.get("limitaciones"),
        }

    # ── 2) Cálculo de fertilizante ──
    if re.search(r"(cuánto|cuanto|cantidad|dosis|cuántos|cuantos)\b.{0,30}\b(fertilizante|abono|urea|dap|kcl|npk|gallinaza|compost)", texto):
        r = calcular_fertilizante(recomendaciones=recs, lectura_vals=lectura, cultivo=cultivo)
        if not r["posible"]:
            return {**vacio, "respuesta": (
                "No puedo calcular la dosis de fertilizante todavía. Me falta: "
                f"{', '.join(r['faltan'])}. Genere primero el análisis del cultivo."
            ), "falta": r["faltan"]}
        resumen = r.get("mensaje", "")
        if r.get("resultados"):
            resumen += " " + " ".join(
                f"{item['nutriente']}: {item['kg_ha']} kg/ha ({item['nota']})."
                for item in r["resultados"]
            )
        datos = [f"cultivo: {cultivo}"] + [f"{i['nutriente']} ideal vs actual" for i in r.get("resultados", [])]
        return {
            "respuesta": _fundamentar(
                recomendacion=resumen,
                por_que="La dosis sale de la diferencia entre su lectura y el rango ideal que define el motor para el cultivo.",
                datos=datos,
                fuentes=r.get("fuentes", []),
                confianza=r.get("confianza", "Media"),
                falta=r.get("limitaciones"),
                sencillo=sencillo,
            ),
            "fuentes": r.get("fuentes", []),
            "confianza": r.get("confianza", "Media"),
            "datos_utilizados": datos,
            "falta": r.get("limitaciones"),
        }

    # ── 3) Riego ──
    if re.search(r"(cada cuánto|cada cuanto|frecuencia|cuánta agua|cuanta agua|cuánto riego|cuanto riego|cómo riego|como riego|regar)", texto):
        r = recomendar_riego(
            textura=lectura.get("textura"),
            humedad_actual=lectura.get("humedad"),
            humedad_ideal=_rango_variable(recs, "humedad"),
            clima=ctx.get("clima"),
        )
        if not r["posible"]:
            return {**vacio, "respuesta": (
                f"Para recomendarle riego con precisión me falta: {', '.join(r['faltan'])}."
            ), "falta": r["faltan"]}
        datos = [f"textura: {lectura.get('textura')}", f"humedad: {lectura.get('humedad')}%"]
        return {
            "respuesta": _fundamentar(
                recomendacion=r["mensaje"],
                por_que="La frecuencia depende de qué tan rápido suelta el agua cada tipo de suelo y de la humedad actual.",
                datos=datos,
                fuentes=r.get("fuentes", []),
                confianza=r.get("confianza", "Media"),
                falta=None if r.get("confianza") != "Baja" else "Sin lectura de humedad la recomendación es general.",
                sencillo=sencillo,
            ),
            "fuentes": r.get("fuentes", []),
            "confianza": r.get("confianza", "Media"),
            "datos_utilizados": datos,
        }

    # ── 4) Clima / época ──
    if re.search(r"(lluvia|clima|pronóstico|pronostico|esta semana|próxima semana|proxima semana|época|epoca del año|temporada)", texto):
        return {
            "respuesta": _respuesta_clima(mensaje, ctx),
            "fuentes": ["IDEAM — calendario climático de Colombia (referencia general)"],
            "confianza": "Media" if (ctx.get("clima") or {}).get("epoca_ano") else "Baja",
            "datos_utilizados": [],
        }

    # ── 5) Diagnóstico de problemas ──
    diag = diagnostico_diferencial(texto)
    if diag.get("encontrado"):
        causas = "\n".join(
            f"{i}. {c['causa']}: {c['detalle']}"
            for i, c in enumerate(diag["causas"], 1)
        )
        return {
            "respuesta": _fundamentar(
                recomendacion=(
                    "Hay varias causas posibles; no me apresuro a culpar una sola:\n" + causas
                ),
                por_que=(
                    "Un mismo síntoma puede venir de nutrición, agua, pH o enfermedades; "
                    "por eso comparo las posibilidades y pido más pistas."
                ),
                datos=[],
                fuentes=diag["fuentes"],
                confianza="Baja",
                falta=diag["solicitud_datos"],
                sencillo=sencillo,
            ),
            "fuentes": diag["fuentes"],
            "confianza": "Baja",
            "datos_utilizados": [],
            "falta": diag["solicitud_datos"],
        }

    # ── 6) ¿Por qué este cultivo? ──
    if re.search(r"(por qué|porque|por que).{0,25}(recomiend|ese cultivo|café|cafe|plátano|platano|papa|este cultivo)", texto):
        return {
            "respuesta": _respuesta_porque_cultivo(ctx),
            "fuentes": ["UPRA — aptitud por suelo y clima", "Cenicafé/Agrosavia — umbrales del cultivo"],
            "confianza": "Media",
            "datos_utilizados": [],
        }

    # ── 7) Conversacional general (motor detallado existente) ──
    return {
        "respuesta": _respuesta_local(mensaje, ctx),
        "fuentes": ["UPRA/Cenicafé/Agrosavia — reglas del motor"],
        "confianza": "Alta" if recs else "Baja",
        "datos_utilizados": [],
    }


def contexto_resumido(ctx: dict) -> dict:
    """Extrae del contexto dict lo que necesita el motor local."""
    lectura_obj = ctx.get("lectura")
    lectura_vals = {}
    if lectura_obj is not None:
        for attr, _nombre in _VARIABLES_LECTURA:
            valor = getattr(lectura_obj, attr, None)
            if valor is not None:
                lectura_vals[attr] = valor
        textura = getattr(lectura_obj, "textura", None)
        if textura is not None:
            lectura_vals["textura"] = getattr(textura, "value", str(textura))
    return {
        "recomendaciones": ctx.get("recomendaciones") or [],
        "reglas": ctx.get("reglas") or [],
        "sugerencias": ctx.get("sugerencias") or [],
        "clasificacion": ctx.get("clasificacion"),
        "lectura": lectura_vals,
        "rol": ctx.get("rol") or "cliente",
        "clima": ctx.get("clima") or {},
        "cultivo": ctx.get("cultivo"),
    }
