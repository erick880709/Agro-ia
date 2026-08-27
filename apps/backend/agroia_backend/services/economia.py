"""Plan económico de fertilización (brecha económica).

Cuando el productor declara un presupuesto por hectárea, se compara el
costo del plan ideal (todas las acciones) contra el presupuesto y se
construye un **plan optimizado**:

1. Las acciones de prioridad **Crítica** (y siempre pH/CE) son obligatorias.
2. El resto se prioriza por severidad de la violación (nutriente más
   limitante primero) hasta agotar el presupuesto.
3. Las no incluidas quedan «aplazadas» con su motivo.

Los costos son estimaciones agronómicas por hectárea (COP 2026); sirven
para priorizar, no como cotización.
"""

from agroia.logging import get_logger

logger = get_logger(__name__)

# ── Costo estimado por variable (COP/ha, aproximaciones agronómicas) ──
COSTOS_VARIABLE: dict[str, float] = {
    "pH": 350_000.0,       # 1 t/ha cal dolomítica/yeso
    "CE": 0.0,             # lavado con riego (sin insumo)
    "N": 180_000.0,        # ~60 kg/ha urea fraccionada
    "P": 150_000.0,        # ~35 kg/ha DAP
    "K": 160_000.0,        # ~45 kg/ha KCl
    "MO": 200_000.0,       # 2 t/ha compost/abono
    "Ca": 120_000.0,       # enmienda cálcica
    "Mg": 100_000.0,       # sulfato de magnesio
    "S": 80_000.0,         # azufre elemental
    "Fe": 60_000.0,        # quelatos
    "Mn": 60_000.0,
    "Zn": 60_000.0,
    "Cu": 60_000.0,
    "B": 60_000.0,
    "CIC": 100_000.0,      # enmiendas orgánicas (proceso gradual)
    "humedad": 0.0,        # ajuste de riego (sin insumo directo)
    "temperatura_suelo": 0.0,
    "profundidad_suelo": 0.0,  # limitante física (enmienda estructural, se informa aparte)
    "pedregosidad": 0.0,
}

PESOS_PRIORIDAD_ECO = {"Critica": 4, "Alta": 3, "Media": 2, "Baja": 1}

VARIABLES_OBLIGATORIAS = {"pH", "CE"}


def _severidad(fila: dict) -> float:
    """Severidad de la violación: prioridad + desviación relativa al rango."""
    import re

    prioridad = str(fila.get("prioridad") or "Baja")
    peso = PESOS_PRIORIDAD_ECO.get(prioridad, 1)
    valor = fila.get("valor_actual")
    rango = str(fila.get("rango_ideal") or "")
    desv = 0.0
    try:
        if isinstance(valor, (int, float)) and rango:
            lo = hi = None
            if "≥" in rango:
                lo = float(rango.split("≥")[1].strip())
            elif "≤" in rango:
                hi = float(rango.split("≤")[1].strip())
            else:
                m = re.search(r"\[?\s*(-?[\d.]+)\s*-\s*(-?[\d.]+)", rango)
                if m:
                    lo, hi = float(m.group(1)), float(m.group(2))
            if lo is not None and valor < lo:
                desv = (lo - valor) / (abs(lo) or 1.0)
            elif hi is not None and valor > hi:
                desv = (valor - hi) / (abs(hi) or 1.0)
    except (ValueError, TypeError):
        desv = 0.0
    return peso * 10.0 + min(desv, 10.0)


def calcular_plan_economico(
    recomendaciones: list[dict],
    presupuesto_cop: float,
) -> dict:
    """Construye el plan ideal vs. el plan optimizado al presupuesto.

    Args:
        recomendaciones: filas del diagnóstico (variable, prioridad, valor,
            rango_ideal, accion, …).
        presupuesto_cop: presupuesto del productor en COP por hectárea.

    Returns:
        dict con costo_ideal, costo_plan, cobertura_pct,
        diferencia_rendimiento_pct, incluidos[], aplazados[].
    """
    filas: list[dict] = []
    for r in recomendaciones:
        variable = str(r.get("variable") or "")
        costo = COSTOS_VARIABLE.get(variable, 60_000.0)
        prioridad = str(r.get("prioridad") or "Baja")
        filas.append({
            **r,
            "costo_cop": costo,
            "obligatoria": variable in VARIABLES_OBLIGATORIAS or prioridad == "Critica",
        })

    costo_ideal = sum(f["costo_cop"] for f in filas)
    if costo_ideal <= 0 or presupuesto_cop is None or presupuesto_cop <= 0:
        return {
            "presupuesto_cop": presupuesto_cop,
            "costo_ideal": round(costo_ideal),
            "costo_plan": round(costo_ideal),
            "cobertura_pct": 100.0,
            "diferencia_rendimiento_pct": 0.0,
            "incluidos": [{"variable": f["variable"], "prioridad": f["prioridad"],
                          "costo_cop": f["costo_cop"], "motivo": None} for f in filas],
            "aplazados": [],
        }

    # 1) Obligatorias (Críticas + pH/CE) siempre van
    obligatorias = [f for f in filas if f["obligatoria"]]
    resto = sorted(
        [f for f in filas if not f["obligatoria"]],
        key=_severidad,
        reverse=True,
    )

    costo_usado = sum(f["costo_cop"] for f in obligatorias)
    incluidos = [dict(f) for f in obligatorias]
    aplazados: list[dict] = []
    for f in resto:
        if costo_usado + f["costo_cop"] <= presupuesto_cop:
            incluidos.append(dict(f))
            costo_usado += f["costo_cop"]
        else:
            aplazados.append(dict(f))

    cobertura = min(100.0, (costo_usado / costo_ideal) * 100.0) if costo_ideal else 100.0
    # Diferencia de rendimiento estimada: proporción no cubierta × 40 %
    diferencia = round(max(0.0, (1.0 - costo_usado / costo_ideal)) * 40.0, 1) if costo_ideal else 0.0

    for f in aplazados:
        f["motivo"] = "No incluida por presupuesto: se recomienda postergar o gestionar apoyo."

    logger.info(
        "plan_economico",
        costo_ideal=round(costo_ideal),
        costo_plan=round(costo_usado),
        cobertura=round(cobertura, 1),
        incluidos=len(incluidos),
        aplazados=len(aplazados),
    )
    return {
        "presupuesto_cop": presupuesto_cop,
        "costo_ideal": round(costo_ideal),
        "costo_plan": round(costo_usado),
        "cobertura_pct": round(cobertura, 1),
        "diferencia_rendimiento_pct": diferencia,
        "incluidos": [
            {"variable": f["variable"], "prioridad": f["prioridad"],
             "costo_cop": f["costo_cop"], "accion": f.get("accion")}
            for f in incluidos
        ],
        "aplazados": [
            {"variable": f["variable"], "prioridad": f["prioridad"],
             "costo_cop": f["costo_cop"], "accion": f.get("accion"), "motivo": f["motivo"]}
            for f in aplazados
        ],
    }
