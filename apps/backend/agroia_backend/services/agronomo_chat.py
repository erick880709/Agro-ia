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
    "3. Si el usuario es campesino/cliente, usa lenguaje del campo: sencillo, "
    "coloquial, sin tecnicismos, con ejemplos prácticos ('echarle cal a la "
    "tierra', 'abonar en dos tandas').\n"
    "4. Si el usuario es agrónomo o administrador, puedes usar lenguaje técnico "
    "y citar la fuente de cada umbral (UPRA, Cenicafé, AGROSAVIA).\n"
    "5. Sé concreto y práctico: qué hacer, cuánto (según el contexto), cuándo y "
    "cómo. Da respuestas paso a paso.\n"
    "6. Responde en español colombiano, con calidez y respeto.\n"
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
    nombre = _NOMBRE_VARIABLE.get(clave, clave.replace("_", " "))
    for rec in ctx["recomendaciones"]:
        var = str(rec.get("variable") or "").lower()
        if clave == "ph" and "ph" in var:
            return (
                f"Sobre la acidez de su tierra: su lectura de pH fue "
                f"{rec.get('valor_actual')} y lo ideal es {rec.get('rango_ideal') or 'según el cultivo'}. "
                f"Estado: {rec.get('estado')}. Recomendación: {rec.get('accion')}"
            )
        if var == clave or var == clave.replace("_", ""):
            return (
                f"Sobre {nombre}: su lectura fue {rec.get('valor_actual')} "
                f"y lo ideal es {rec.get('rango_ideal') or 'según el cultivo'}. "
                f"Estado: {rec.get('estado')}. Qué hacer: {rec.get('accion')}"
            )
    # Sin recomendación específica: usar reglas (comparación por símbolo exacto)
    simbolo = _RULE_VAR.get(clave, clave).lower()
    for regla in ctx["reglas"]:
        vregla = str(getattr(regla.variable, "value", regla.variable)).lower()
        if vregla == simbolo:
            rango = (f" entre {regla.umbral_min} y {regla.umbral_max}"
                     if regla.umbral_min is not None or regla.umbral_max is not None
                     else "")
            return (
                f"Sobre {nombre}: la recomendación agronómica es mantenerlo{rango}. "
                f"{regla.accion}"
            )
    # Sin regla: reportar la lectura cruda si existe
    lectura = ctx.get("lectura") or {}
    valor = lectura.get(clave)
    if valor is not None:
        return (
            f"Sobre {nombre}: su última lectura fue {valor}. "
            "El rango ideal depende del cultivo; revise el reporte generado o "
            "consulte al técnico de su zona para interpretarlo bien."
        )
    return (
        f"Para {nombre} no tengo una lectura ni una regla específica en el contexto de "
        "esta finca. Le sugiero consultar al técnico o a la UMATA más cercana."
    )


def _respuesta_local(mensaje: str, ctx: dict) -> str:
    """Motor determinista: responde con reglas + lectura, sin LLM."""
    texto = mensaje.lower()

    # ── Saludos / cortesía ──
    if re.search(r"^(hola|buenas|buenos dias|buenos días|buenas tardes|quién eres|quien eres|hey|saludos)", texto):
        return (
            "¡Muy buenas! 👋 Soy su asesor agronómico de AgroIA. "
            "Puedo explicarle el reporte de su finca, decirle cómo abonar, qué sembrar "
            "y cómo cuidar su cultivo. Pregúnteme con confianza, por ejemplo: "
            "«¿qué abono debo aplicar?» o «¿qué me conviene sembrar?»."
        )
    if re.search(r"(gracias|muy amable|quedo atento)", texto):
        return (
            "¡Con mucho gusto! 🌱 Recuerde que este consejo es automático y que el técnico "
            "de su zona puede afinar la recomendación. ¡Que la tierra le pague bien!"
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
            linea = (
                f"Según el análisis de su suelo, lo que mejor le va es {top.get('cultivo')} "
                f"(aptitud {top.get('clasificacion') or top.get('aptitud') or '—'}). "
            )
            otros = [s.get("cultivo") for s in sugerencias[1:3]]
            if otros:
                linea += f"También se podrían dar: {', '.join(otros)}. "
            linea += "Antes de sembrar, corrija lo que el reporte marca en rojo y prepare bien el terreno."
            return linea
        return (
            "Para recomendarle qué sembrar necesito la lectura de suelo de su finca. "
            "Genere primero el reporte o cargue una lectura de sensor."
        )

    # ── Abonar / fertilizar (general) ──
    if re.search(r"(abon|fertiliz|nutri)", texto):
        recs = ctx["recomendaciones"] or []
        if not recs:
            return (
                "No tengo lecturas de suelo de esta finca para recomendar abonos. "
                "Cargue una lectura de sensor o un archivo de mediciones y con gusto le digo qué aplicar."
            )
        principales = [r for r in recs if str(r.get("estado") or "").upper() in ("DEFICIT", "EXCESO")][:4]
        if not principales:
            return ("Su suelo está bien nutrido por ahora; no es necesario abonar de más. "
                    "Mantenga la materia orgánica y haga un análisis cada 6 meses.")
        partes = ["Le cuento qué necesita su tierra:"]
        for r in principales:
            partes.append(f"• {_nombre_rec(r)}: {r.get('accion')}")
        partes.append(
            "Recuerde abonar en dos o tres tandas y no todo de un golpe, y preferir "
            "abonos orgánicos maduros cuando sea posible."
        )
        return " ".join(partes)

    # ── Reporte / explicación general ──
    if re.search(r"(reporte|explic|resum|análisis|analisis|cómo está|como esta)", texto):
        clas = ctx["clasificacion"] or "sin clasificar"
        recs = ctx["recomendaciones"] or []
        resumen = (
            f"Su suelo está clasificado como {clas}. "
            f"{'Las recomendaciones principales del reporte son: ' if recs else 'No hay recomendaciones todavía.'}"
        )
        for r in recs[:4]:
            resumen += f" • {_nombre_rec(r)}: {r.get('accion')}"
        if not recs:
            resumen += " Genere el reporte con una lectura de sensor para ver el detalle."
        return resumen

    # ── Por defecto: estado general + sugerencias ──
    recs = ctx["recomendaciones"] or []
    if recs:
        criticas = [r for r in recs if str(r.get("prioridad") or "").lower() == "critica"]
        if criticas:
            base = f"Le doy un panorama general de su suelo: lo más urgente es {_nombre_rec(criticas[0])}: {criticas[0].get('accion')} "
        else:
            base = "Le doy un panorama general de su suelo: no hay urgencias críticas. "
        base += ("Puedo responderle con detalle sobre: cómo abonar, qué sembrar, el pH, "
                 "el riego o cualquier nutriente en particular (nitrógeno, fósforo, potasio, calcio…).")
        return base
    return (
        "Todavía no tengo lecturas de suelo de esta finca para aconsejarlo. "
        "Genere primero el reporte (o cargue una lectura de sensor) y vuelva a preguntarme."
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


def contexto_resumido(ctx: dict) -> dict:
    """Extrae del contexto dict lo que necesita el motor local."""
    lectura_obj = ctx.get("lectura")
    lectura_vals = {}
    if lectura_obj is not None:
        for attr, _nombre in _VARIABLES_LECTURA:
            valor = getattr(lectura_obj, attr, None)
            if valor is not None:
                lectura_vals[attr] = valor
    return {
        "recomendaciones": ctx.get("recomendaciones") or [],
        "reglas": ctx.get("reglas") or [],
        "sugerencias": ctx.get("sugerencias") or [],
        "clasificacion": ctx.get("clasificacion"),
        "lectura": lectura_vals,
    }
