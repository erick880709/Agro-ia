"""Enriquecimiento económico de UC1 — precios de cosecha y utilidad estimada.

Para cada cultivo sugerido con precio registrado en el departamento de la
finca se calcula:
- ingreso_bruto_cop_ha = rendimiento_promedio_t_ha * precio * 1000
- utilidad_estimada_cop_ha = ingreso_bruto - costo_insumos (si se conoce)
- score_ponderado = score * 0.7 + utilidad_normalizada * 0.3 (alternativa
  de orden; el ranking edáfico original se conserva).
"""

from sqlalchemy import select

from agroia_backend.models.precio_cosecha import PrecioCosecha


async def enriquecer_sugerencias(
    db, sugerencias: list[dict], departamento: str | None, costo_insumos: float | None = None
) -> list[dict]:
    """Devuelve las sugerencias con campos económicos agregados."""
    if not sugerencias or not departamento:
        for s in sugerencias:
            s.setdefault("precio_promedio_cop_kg", None)
            s.setdefault("utilidad_estimada_cop_ha", None)
        return sugerencias

    import uuid as uuid_mod

    ids = []
    for s in sugerencias:
        try:
            ids.append(uuid_mod.UUID(str(s["cultivo_id"])))
        except (KeyError, ValueError):
            pass
    if not ids:
        return sugerencias

    precios = (
        await db.execute(
            select(PrecioCosecha).where(
                PrecioCosecha.departamento == departamento.strip(),
                PrecioCosecha.cultivo_id.in_(ids),
            )
        )
    ).scalars().all()
    por_cultivo = {str(p.cultivo_id): p for p in precios}

    utilidades: list[float] = []
    for s in sugerencias:
        p = por_cultivo.get(s.get("cultivo_id"))
        s["precio_promedio_cop_kg"] = p.precio_promedio_cop_kg if p else None
        s["precio_fuente"] = p.fuente if p else None
        s["precio_fecha"] = (
            p.fecha_actualizacion.isoformat() if p and p.fecha_actualizacion else None
        )
        if p and p.rendimiento_promedio_t_ha:
            ingreso = round(float(p.rendimiento_promedio_t_ha) * float(p.precio_promedio_cop_kg) * 1000.0, 0)
            s["rendimiento_referencia_t_ha"] = float(p.rendimiento_promedio_t_ha)
            s["ingreso_bruto_cop_ha"] = ingreso
            utilidad = (
                round(ingreso - float(costo_insumos), 0) if costo_insumos is not None else None
            )
            s["utilidad_estimada_cop_ha"] = utilidad
            # Sin costos disponibles, el ranking económico usa el ingreso bruto
            utilidades.append(utilidad if utilidad is not None else ingreso)
        else:
            s["rendimiento_referencia_t_ha"] = None
            s["ingreso_bruto_cop_ha"] = None
            s["utilidad_estimada_cop_ha"] = None

    if utilidades:
        max_u, min_u = max(utilidades), min(utilidades)
        rango = (max_u - min_u) or 1.0
        for s in sugerencias:
            s.setdefault("score_ponderado", s["score"])
            valor = s.get("utilidad_estimada_cop_ha")
            if valor is None:
                valor = s.get("ingreso_bruto_cop_ha")
            if valor is None:
                continue
            utilidad_norm = (valor - min_u) / rango
            s["score_ponderado"] = round(
                float(s["score"]) * 0.7 + utilidad_norm * 30.0, 1
            )
            s["mas_rentable"] = valor == max_u
    else:
        for s in sugerencias:
            s["score_ponderado"] = s["score"]

    return sugerencias
