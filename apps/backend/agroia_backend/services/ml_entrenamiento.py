"""Aprendizaje automático con etiquetas de laboratorio (Épica E9: TT-14/15).

- TT-14: los modelos se entrenan/evalúan **solo** con pares sensor–laboratorio
  (nunca con salidas de reglas aplicadas al mismo sensor), incluyendo las
  covariables de contexto (humedad, temperatura, CE) y la incertidumbre.
- TT-15: el rendimiento se reporta por variable, grado de evidencia y unidad
  de suelo; el modelo permanece en **modo sombra** hasta cumplir las metas.
"""

from __future__ import annotations

from agroia_backend.services.calibracion import regresion_lineal

# Metas por variable (RT-034, propuesta de partida). Si no se cumplen, la
# variable permanece en grado C (indicativa).
METAS = {
    "ph": {"tipo": "sesgo_rmse", "sesgo": 0.3, "rmse": 0.4},
    "humedad": {"tipo": "rmse", "rmse": 5.0},
    "conductividad_electrica": {"tipo": "r2", "r2": 0.8},
    "nitrogeno": {"tipo": "r2", "r2": 0.6},
    "fosforo": {"tipo": "r2", "r2": 0.6},
    "potasio": {"tipo": "r2", "r2": 0.6},
}

# Covariables de contexto que acompañan a cada par (TT-14).
COVARIABLES_CONTEXTO = ("humedad", "temperatura_suelo", "conductividad_electrica")


def cumple_meta(variable: str, metricas: dict | None) -> bool:
    """True si las métricas de la variable cumplen la meta de RT-034."""
    if not metricas:
        return False
    meta = METAS.get(variable)
    if meta is None:
        return False
    tipo = meta["tipo"]
    if tipo == "sesgo_rmse":
        sesgo = metricas.get("sesgo")
        rmse = metricas.get("rmse")
        if sesgo is None or rmse is None:
            return False
        return abs(sesgo) <= meta["sesgo"] and rmse <= meta["rmse"]
    if tipo == "rmse":
        rmse = metricas.get("rmse")
        return rmse is not None and rmse <= meta["rmse"]
    if tipo == "r2":
        r2 = metricas.get("r2")
        return r2 is not None and r2 >= meta["r2"]
    return False


def evaluar_variable(valor_sensor: list[float], valor_laboratorio: list[float]) -> dict | None:
    """Métricas de rendimiento (R², RMSE, sesgo, n) de una variable."""
    return regresion_lineal(valor_sensor, valor_laboratorio)


def reporte_rendimiento(pares: list[dict]) -> dict:
    """TT-15: rendimiento por variable (y opcional unidad de suelo).

    `pares`: lista de {variable, unidad_suelo, valor_sensor, valor_laboratorio}.
    """
    grupos: dict[str, dict] = {}
    for p in pares:
        variable = p.get("variable")
        if variable is None:
            continue
        clave = (variable, p.get("unidad_suelo"))
        grupos.setdefault(clave, {"xs": [], "ys": []})
        grupos[clave]["xs"].append(p["valor_sensor"])
        grupos[clave]["ys"].append(p["valor_laboratorio"])

    salida = []
    for (variable, unidad), datos in grupos.items():
        metricas = evaluar_variable(datos["xs"], datos["ys"])
        cumple = cumple_meta(variable, metricas)
        n = metricas["n"] if metricas else 0
        n_suficiente = n >= 30
        # Grado resultante: B si cumple meta con n suficiente, C si no.
        grado = "B" if (cumple and n_suficiente) else "C"
        salida.append({
            "variable": variable,
            "unidad_suelo": unidad,
            "n": n,
            "r2": metricas["r2"] if metricas else None,
            "rmse": metricas["rmse"] if metricas else None,
            "sesgo": metricas["sesgo"] if metricas else None,
            "cumple_meta": cumple,
            "grado": grado,
            # Modo sombra hasta cumplir meta Y tener n suficiente.
            "modo_sombra": not (cumple and n_suficiente),
        })
    return {"por_variable": salida, "total_variables": len(salida)}


def modo_sombra(reporte: dict) -> bool:
    """True mientras alguna variable no cumpla su meta (TT-15)."""
    filas = reporte.get("por_variable", [])
    return any(f["modo_sombra"] for f in filas)


def validar_sin_circularidad(etiquetas_origen: str) -> bool:
    """TT-14: solo se aceptan etiquetas de laboratorio, nunca de reglas."""
    return etiquetas_origen == "laboratorio"
