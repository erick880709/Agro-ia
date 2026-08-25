"""Explicación del análisis en lenguaje de campesino (no técnico).

Convierte el resultado del motor de reglas en frases sencillas y acciones
prácticas para que cualquier persona del campo entienda qué tiene su suelo
y qué hacer en su terreno.
"""

from html import escape as esc


# ── Traducciones por variable ──
# clave: qué_es, exceso, deficit, ok (las acciones en lenguaje campesino)
_EXPLICACIONES = {
    "ph": {
        "que_es": "Qué tan 'agria' o 'amarga' está la tierra (la acidez)",
        "exceso": (
            "Su tierra está muy <b>amarga</b> (alcalina). Rebájela con yeso agrícola o abonos ácidos, "
            "regados parejos por todo el lote y mezclados con el suelo antes de sembrar."
        ),
        "deficit": (
            "Su tierra está muy <b>agria</b> (ácida). Endulcela con cal dolomita o cal agrícola "
            "al voleo, de preferencia un mes antes de sembrar, y revuelva con el suelo."
        ),
        "ok": "La acidez está en su punto: ni muy agria ni muy amarga.",
    },
    "nitrogeno": {
        "que_es": "El abono que pone verdes las hojas y hace crecer la planta",
        "exceso": "Le está echando mucho 'comida verde': rebaje el nitrógeno y no abone de más o se le vira el cultivo.",
        "deficit": (
            "A la tierra le falta 'comida verde'. Aplique abono nitrogenado (urea o gallinaza madura) "
            "en dos o tres tandas, no todo de un solo golpe."
        ),
        "ok": "El nitrógeno está bueno: las hojas tendrán con qué crecer.",
    },
    "fosforo": {
        "que_es": "El abono que hace raíces fuertes y ayuda a florecer y cargar fruto",
        "exceso": "Hay fósforo de sobra; no agregue más por ahora.",
        "deficit": (
            "A la tierra le falta fósforo. Aplique DAP o roca fosfórica en el hoyo o en banda "
            "cerca de la semilla, que es donde la planta lo aprovecha mejor."
        ),
        "ok": "El fósforo está bueno: la raíz se agarra bien.",
    },
    "potasio": {
        "que_es": "El abono que da fuerza al tallo, llena el fruto y lo pone dulce",
        "exceso": "Hay potasio de sobra; evite echar más por una temporada.",
        "deficit": (
            "A la tierra le falta potasio. Aplique KCl (cloruro de potasio) según la etapa del cultivo: "
            "poco al comienzo y más cuando esté cargando fruto."
        ),
        "ok": "El potasio está bueno: tallo firme y fruto bien lleno.",
    },
    "calcio": {
        "que_es": "El 'calcio' del suelo: evita frutos rajados y podridos",
        "exceso": "Hay calcio de sobra; no agregue más.",
        "deficit": "Aplique cal dolomita o yeso agrícola para aportar calcio a la planta.",
        "ok": "El calcio está bueno: menos fruta dañada.",
    },
    "magnesio": {
        "que_es": "Ayuda a que la hoja 'pinche' verde (clorofila)",
        "exceso": "Hay magnesio de sobra.",
        "deficit": "Aplique cal dolomita o sulfato de magnesio si ve las hojas amarillentas entre las venas.",
        "ok": "El magnesio está bueno.",
    },
    "azufre": {
        "que_es": "Mejora el sabor y ayuda a la planta a aprovechar el nitrógeno",
        "exceso": "Hay azufre de sobra.",
        "deficit": "Puede aplicar sulfato o abonos con azufre; en zonas de lluvia se lava rápido.",
        "ok": "El azufre está bueno.",
    },
    "hierro": {
        "que_es": "Evita que las hojas nuevas se pongan amarillas",
        "exceso": "Hay hierro de sobra.",
        "deficit": "Aplique quelatos de hierro si ve hojas nuevas pálidas.",
        "ok": "El hierro está bueno.",
    },
    "materia_organica": {
        "que_es": "La 'vida' del suelo: compost, hojarasca, estiércol maduro",
        "exceso": "Hay bastante materia orgánica: siga así.",
        "deficit": (
            "A la tierra le falta 'cuerpo'. Eche compost, estiércol maduro o gallinaza reposada "
            "y déjela descomponer; la tierra queda más suelta y guarda mejor el agua."
        ),
        "ok": "La materia orgánica está buena: su suelo está 'vivo'.",
    },
    "cic": {
        "que_es": "La 'despensa' del suelo: cuánta comida puede guardar para la planta",
        "exceso": "La despensa está llena.",
        "deficit": (
            "Su suelo guarda poca comida. Súmele materia orgánica y cal dolomita; "
            "así los abonos no se le pierden con la lluvia."
        ),
        "ok": "Su suelo guarda bien los abonos.",
    },
    "conductividad_electrica": {
        "que_es": "Las 'sales' del suelo: si son muchas, la tierra quema las plantas",
        "exceso": (
            "Su tierra está salada y puede quemar el cultivo. Riegue más seguido para 'lavar' las sales "
            "y use abonos en poca cantidad."
        ),
        "deficit": "Hay pocas sales; no hay problema de salinidad.",
        "ok": "Su tierra no tiene problema de sales: excelente.",
    },
    "humedad": {
        "que_es": "El agua que guarda el suelo para la planta",
        "exceso": "La tierra está muy mojada: drene o no riegue hasta que escurra, o se le pudren las raíces.",
        "deficit": (
            "A la tierra le falta agua. Riegue más seguido y ponga cobertura (mulch, hojarasca) "
            "para que el suelo no se seque tan rápido."
        ),
        "ok": "La humedad del suelo está buena.",
    },
    "temperatura_suelo": {
        "que_es": "El 'calor' de la tierra donde crecen las raíces",
        "exceso": "La tierra está muy caliente; la sombra y la cobertura ayudan a refrescarla.",
        "deficit": "La tierra está fría; si es posible siembre en época de más calor.",
        "ok": "La temperatura de la tierra está buena.",
    },
    "textura": {
        "que_es": "Qué tan suelta o pesada es la tierra",
        "exceso": "—",
        "deficit": "—",
        "ok": "La textura está bien para trabajar con azadón y para que respire la raíz.",
    },
}

_CULTIVOS_FRASES = {
    "café": "El café quiere tierra fresca y que no se encharque; con sombra y abono parejo, la mata le responde.",
    "papa": "La papa quiere tierra suelta y sin agua estancada; siembre semilla certificada y aporque a tiempo.",
    "arroz": "El arroz pide mucha agua; si su lote no tiene riego o lluvias parejas, piénselo dos veces.",
    "plátano": "El plátano aguanta y da cosecha a los 12-15 meses; pida colinos sanos y abone en corona.",
    "maíz": "El maíz se da rápido (3-4 meses); siémbrelo en hileras y deshierbe sin falta.",
    "aguacate": "El aguacate es delicado de raíz y no aguanta el agua estancada; siembre plantas injertadas.",
    "fríjol": "El fríjol abona la tierra y se da en pocos meses; bueno para rotar con maíz.",
    "tomate": "El tomate es exigente; necesita abono parejo y tutorado para que no se caiga.",
    "yuca": "La yuca es agradecida y aguanta suelos flojos; necesita poca agua.",
    "cacao": "El cacao quiere sombra y humedad pareja; en suelos frescos rinde muchos años.",
    "caña": "La caña aguanta y da cortes seguidos; necesita abono y deshierbe constante.",
}


def _clave(variable: str) -> str:
    v = (variable or "").lower().strip()
    return {
        "ph": "ph",
        "n": "nitrogeno", "nitrógeno": "nitrogeno", "nitrogeno": "nitrogeno",
        "p": "fosforo", "fósforo": "fosforo", "fosforo": "fosforo",
        "k": "potasio", "potasio": "potasio",
        "ca": "calcio", "calcio": "calcio",
        "mg": "magnesio", "magnesio": "magnesio",
        "s": "azufre", "azufre": "azufre",
        "fe": "hierro", "hierro": "hierro",
        "mo": "materia_organica", "materia orgánica": "materia_organica", "materia_organica": "materia_organica",
        "cic": "cic",
        "ce": "conductividad_electrica", "conductividad": "conductividad_electrica",
        "conductividad_electrica": "conductividad_electrica",
        "humedad": "humedad",
        "temperatura_suelo": "temperatura_suelo",
        "textura": "textura",
        "manganeso": "manganeso", "zinc": "zinc", "cobre": "cobre", "boro": "boro",
    }.get(v, v)


def _texto_variable(r: dict) -> str:
    """Explica una recomendación del motor en lenguaje campesino."""
    clave = _clave(r.get("variable"))
    info = _EXPLICACIONES.get(clave)
    estado = (r.get("estado") or "").upper()
    valor = r.get("valor_actual")
    rango = r.get("rango_ideal")

    if info:
        if estado == "EXCESO":
            accion = info["exceso"]
        elif estado == "DEFICIT":
            accion = info["deficit"]
        else:
            accion = info["ok"]
        que_es = info["que_es"]
    else:
        que_es = "Un nutriente o condición del suelo"
        if estado == "EXCESO":
            accion = "Tiene de sobra; no agregue más por ahora."
        elif estado == "DEFICIT":
            accion = f"Le falta; aplique un abono que contenga {esc(r.get('variable') or 'este nutriente')}."
        else:
            accion = "Está en buenas condiciones."

    lectura = f" Su lectura fue <b>{valor}</b>" if valor is not None else ""
    ideal = f" y lo bueno está entre {esc(str(rango))}" if rango else ""
    return (
        f'<li><b>{esc(r.get("variable"))}</b> — {esc(que_es)}.{lectura}{ideal}. '
        f'{accion}</li>'
    )


def generar_explicacion_campesina(*, uc1: dict | None, uc2: dict | None, lectura: dict | None) -> str:
    """Construye la sección 'En palabras del campo' del reporte."""
    partes = []

    # ── Resumen en cristiano ──
    if uc2:
        clas = esc(str(uc2.get("clasificacion_upra") or "sin clasificar"))
        cultivo = esc(str(uc2.get("cultivo") or "su cultivo"))
        if "no apta" in clas.lower():
            frase = f"su tierra no está cómoda para <b>{cultivo}</b>"
        elif "apta" in clas.lower():
            frase = f"su tierra se acomoda bien a <b>{cultivo}</b>"
        else:
            frase = f"su tierra se puede arreglar para <b>{cultivo}</b>"
        partes.append(f"<p class=\"ft-intro\">Hablando en plata blanca: hoy {frase}. Abajo le contamos, en el mismo idioma del campo, qué significa cada cosa y qué hacer en su terreno.</p>")

    # ── Explicación variable por variable (UC2) ──
    if uc2 and (uc2.get("recomendaciones") or []):
        items = "".join(_texto_variable(r) for r in uc2["recomendaciones"])
        partes.append(
            '<div class="ft-sub">📖 Qué significa cada medición y qué hacer</div>'
            f'<ul class="ft-list">{items}</ul>'
        )

    # ── Consejo de siembra (UC1) ──
    if uc1:
        sugerencias = uc1.get("sugerencias_cultivos") or []
        if sugerencias:
            top = sugerencias[0]
            nombre = esc(str(top.get("cultivo")))
            frase_cultivo = _CULTIVOS_FRASES.get(nombre.lower())
            linea = (
                f"Para empezar de cero, lo que mejor le va en su tierra es <b>{nombre}</b>. "
                f"{frase_cultivo or 'Según el análisis, se acomoda a las condiciones de su suelo y clima.'}"
            )
            otros = [esc(s.get("cultivo")) for s in sugerencias[1:3]]
            if otros:
                linea += f" También se podrían dar: {', '.join(otros)}."
            partes.append(f'<div class="ft-sub">🌱 Si va a sembrar de nuevo</div><p class="ft-para">{linea}</p>')

    # ── ¿Qué hago primero? ──
    if uc2 and (uc2.get("recomendaciones") or []):
        recs = sorted(uc2["recomendaciones"], key=lambda r: 0 if str(r.get("prioridad") or "").lower() == "critica" else 1)
        pasos = "".join(
            f"<li>{_texto_variable(r).replace('<li>', '').replace('</li>', '')}</li>"
            for r in recs[:4]
        )
        partes.append('<div class="ft-sub">🧺 ¿Por dónde empiezo en mi lote?</div>'
                      f'<ol class="ft-steps">{pasos}</ol>')

    # ── Nota de honestidad ──
    notas = []
    if lectura and lectura.get("calidad") == "npk_no_calibrado":
        notas.append(
            "Los números de N, P y K vienen de un aparato que <b>no está calibrado</b> con un laboratorio: "
            "no los tome al pie de la letra. El pH y las sales sí son confiables."
        )
    conf = (uc2 or {}).get("confianza") or (uc1 or {}).get("confianza") or 1.0
    if conf < 0.8:
        notas.append(
            "Este consejo lo da un sistema automático con datos incompletos; "
            "antes de gastar plata en abonos, muéstrele este informe al técnico o a la UMATA más cercana."
        )
    if notas:
        partes.append('<div class="ft-note">⚠️ Para que no se pierda: ' + " ".join(notas) + "</div>")

    if not partes:
        partes.append('<p class="ft-para">Aún no hay suficientes datos para dar una explicación sencilla. Cargue una lectura del sensor o un archivo de mediciones.</p>')

    return (
        '<section class="block field-talk">'
        '<div class="block-head"><span class="block-num">03</span>'
        '<div><div class="block-title">En palabras del campo</div>'
        '<div class="block-sub">Explicación sencilla para aplicar en su terreno</div></div></div>'
        + "".join(partes)
        + "</section>"
    )
