"""Orquestador híbrido de recomendaciones — ML + Reglas.

Coordina el pipeline completo: recibe solicitud → consulta datos →
invoca modelos ML → aplica reglas → detecta discordancia → ensambla respuesta.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from agroia.logging import get_logger

logger = get_logger(__name__)

# ── Días hábiles para SLA de discordancia ──
SLA_DISCORDANCIA_DIAS = 10

# ── Variables de fertilidad necesarias para una recomendación sólida ──
VARIABLES_FERTILIDAD = [
    "materia_organica", "cic", "calcio", "magnesio", "azufre",
    "hierro", "manganeso", "zinc", "cobre", "boro",
]

# Cultivos sensibles a drenaje/aireación radicular (requieren textura)
CULTIVOS_SENSIBLES_TEXTURA = {
    "aguacate", "cacao", "mango", "naranja", "limón", "mandarina",
    "palma de aceite",
}

# Variables que el sensor NPK mide sin validación de laboratorio
VARIABLES_NPK_SENSOR = {"N", "P", "K"}

# Plan ejecutable por variable: fuente y frecuencia sugeridas
PLAN_FERTILIZACION = {
    "N": {"fuente": "Urea (46% N) o sulfato de amonio (21% N)", "frecuencia": "Fraccionar en 2–3 aplicaciones según la etapa del cultivo"},
    "P": {"fuente": "DAP (18-46-0) o roca fosfórica en suelos ácidos", "frecuencia": "Aplicar al hoyado o en banda a la siembra"},
    "K": {"fuente": "KCl (60% K₂O) o sulfato de potasio (50% K₂O)", "frecuencia": "En banda o fertirriego según la etapa del cultivo"},
    "pH": {"fuente": "Cal dolomítica (suelo ácido) o yeso agrícola (suelo alcalino)", "frecuencia": "Incorporar 15–30 días antes de la siembra"},
    "MO": {"fuente": "Compost, gallinaza compostada o abonos verdes", "frecuencia": "Incorporar 2–4 t/ha por ciclo de cultivo"},
    "Ca": {"fuente": "Cal dolomítica o yeso agrícola", "frecuencia": "Incorporar en presiembra; evitar exceso en suelos calcáreos"},
    "Mg": {"fuente": "Sulfato de magnesio o cal dolomítica", "frecuencia": "Aplicación única por ciclo; vigilar antagonismo con K"},
    "S": {"fuente": "Azufre elemental o sulfato de amonio", "frecuencia": "Incorporar en presiembra"},
    "Fe": {"fuente": "Quelato de hierro (EDDHA en pH alto)", "frecuencia": "Aplicaciones foliares o al suelo según severidad"},
    "Mn": {"fuente": "Sulfato de manganeso", "frecuencia": "Foliar o al suelo; encalar si hay toxicidad por exceso"},
    "Zn": {"fuente": "Sulfato de zinc", "frecuencia": "Al suelo en presiembra o foliar en floración"},
    "Cu": {"fuente": "Sulfato de cobre (con precaución)", "frecuencia": "Solo ante deficiencia confirmada; dosis baja"},
    "B": {"fuente": "Bórax o ácido bórico", "frecuencia": "Dosis baja y precisa (rango estrecho de toxicidad)"},
    "CE": {"fuente": "Riego de lavado con agua de buena calidad", "frecuencia": "2–3 riegos profundos; verificar drenaje"},
    "humedad": {"fuente": "Riego programado según capacidad de campo", "frecuencia": "Ajustar turnos de riego; revisar sensor de humedad"},
    "temperatura_suelo": {"fuente": "Sombrío, cobertura vegetal o mulch", "frecuencia": "Mantener cobertura; reducir laboreo"},
    "CIC": {"fuente": "Enmiendas orgánicas + encalado", "frecuencia": "Proceso gradual (meses); monitorear anualmente"},
}

# Ajustes de manejo según etapa fenológica (cuando el cultivo ya está sembrado)
AJUSTES_ETAPA = {
    "vegetativa": "Priorizar nitrógeno y riego regular para crecimiento de follaje.",
    "floración": "Reducir nitrógeno, priorizar fósforo y boro; mantener humedad estable.",
    "fructificación": "Priorizar potasio y calcio para calidad de fruto; evitar estrés hídrico.",
    "cosecha": "Suspender aplicaciones cerca de cosecha; respetar periodos de carencia.",
}


@dataclass
class RecommendationRequest:
    """Solicitud de análisis de aptitud."""
    finca_id: str
    cultivo_id: str | None = None
    tenant_id: str | None = None
    presupuesto_cop: float | None = None  # presupuesto de fertilización ($/ha)


@dataclass
class RecommendationResult:
    """Resultado completo del pipeline de recomendación."""
    cultivo: str
    clasificacion_upra: str
    confianza: float
    recomendaciones: list[dict] = field(default_factory=list)
    justificacion: dict = field(default_factory=dict)
    advertencia: str | None = None
    discordancia: dict | None = None
    tiempo_respuesta_ms: float = 0.0
    sugerencias_cultivos: list[dict] = field(default_factory=list)
    modo: str = "analizar_cultivo"
    # ── Confianza real, validación y feedback humano (2026-08-27) ──
    confianza_real: float = 0.0
    estado_validacion: str = "pendiente_validacion"
    respaldos: int = 0
    variables_faltantes_fertilidad: list[str] = field(default_factory=list)
    variables_faltantes_esenciales: list[str] = field(default_factory=list)
    fenologia_ajustada: str | None = None
    plan_economico: dict | None = None


class RecommendationOrchestrator:
    """Orquesta el pipeline completo de recomendación."""

    def __init__(
        self,
        db_session,
        soil_adapter=None,
        ml_service=None,
        rules_engine=None,
        justification_service=None,
        aptitud_service=None,
    ):
        self.db = db_session
        self.soil = soil_adapter
        self.ml = ml_service
        self.rules = rules_engine
        self.justification = justification_service
        self.aptitud = aptitud_service

    async def analyze(self, request: RecommendationRequest) -> RecommendationResult:
        """Ejecuta el pipeline completo de recomendación.

        Args:
            request: Solicitud con finca_id y cultivo_id opcional

        Returns:
            RecommendationResult con la recomendación completa

        Raises:
            InsufficientDataError: si faltan variables bloqueantes
        """
        t_start = datetime.utcnow()

        # ── Paso 1: Obtener datos de suelo ──
        soil_data = await self.soil.get_latest(request.finca_id)
        if soil_data is None:
            # Sin ninguna lectura: NO se bloquea. Se entrega una
            # recomendación preliminar con los parámetros esenciales
            # faltantes y el requisito de aval de un agrónomo.
            return await self._recomendacion_sin_datos(request, t_start)

        soil_dict = soil_data.to_dict()
        logger.info("soil_data_loaded", finca_id=request.finca_id, vars=len(soil_dict))

        # ── Contexto agronómico de la finca (validación lab, fenología…) ──
        finca_ctx = await self._cargar_contexto_finca(request.finca_id)

        # ── Advertencias de calidad de datos (brechas G3/G4) ──
        advertencias_datos = []
        if soil_data.calidad == "npk_no_calibrado":
            advertencias_datos.append(
                "⚠️ Lecturas NPK sin calibrar: valide con análisis de laboratorio "
                "antes de aplicar fertilizantes."
            )
        if soil_data.missing_non_blocking:
            advertencias_datos.append(
                "⚠️ Recomendación parcial: faltan variables ("
                + ", ".join(soil_data.missing_non_blocking) + ")."
            )
        if soil_data.missing_blocking:
            advertencias_datos.append(
                "⚠️ Faltan parámetros esenciales ("
                + ", ".join(soil_data.missing_blocking)
                + "): la recomendación no tiene el 100% de certeza y requiere "
                "el aval de un agrónomo."
            )
        advertencia_datos = " ".join(advertencias_datos) or None

        # ── Paso 2: Ramificación por caso de uso ──
        npk_no_calibrado = soil_data.calidad == "npk_no_calibrado"
        if request.cultivo_id is None:
            # UC1: no hay cultivo sembrado → recomendar qué sembrar
            return await self._recomendar_cultivos(
                request.finca_id, soil_dict, t_start, advertencia_datos,
                finca_ctx, npk_no_calibrado, request.presupuesto_cop,
                missing_esenciales=soil_data.missing_blocking,
            )

        # UC2: hay cultivo sembrado → diagnosticar qué falta/sobra
        return await self._analizar_cultivo(
            request, soil_dict, t_start, advertencia_datos, finca_ctx,
            npk_no_calibrado, missing_esenciales=soil_data.missing_blocking,
        )

    async def _cargar_contexto_finca(self, finca_id: str) -> dict:
        """Datos agronómicos de la finca: validación de laboratorio, fenología,
        tipo de riego y características físicas del lote principal."""
        from sqlalchemy import select

        from agroia_backend.models.finca import Finca
        from agroia_backend.models.lote import Lote

        try:
            finca = (
                await self.db.execute(
                    select(Finca).where(Finca.id == finca_id)
                )
            ).scalar_one_or_none()
        except Exception as e:  # noqa: BLE001 — finca_id no UUID
            logger.warning("finca_ctx_no_resuelta", finca_id=finca_id, error=str(e))
            return {}
        if finca is None:
            return {}
        lote = None
        try:
            lote_obj = (
                await self.db.execute(
                    select(Lote).where(
                        Lote.finca_id == finca.id, Lote.activo.is_(True)
                    ).order_by(Lote.created_at).limit(1)
                )
            ).scalars().first()
            if lote_obj is not None:
                lote = {
                    "profundidad_suelo_cm": lote_obj.profundidad_suelo_cm,
                    "pedregosidad": (
                        lote_obj.pedregosidad.value if lote_obj.pedregosidad else None
                    ),
                }
        except Exception as e:  # noqa: BLE001
            logger.warning("lote_ctx_no_resuelto", error=str(e))
        return {
            "validacion_laboratorio": bool(finca.validacion_laboratorio),
            "cultivo_sembrado": finca.cultivo_sembrado,
            "edad_anos": finca.edad_anos,
            "etapa_fenologica": finca.etapa_fenologica,
            "pendiente_pct": finca.pendiente_pct,
            "drenaje": finca.drenaje,
            "historial_agronomico": finca.historial_agronomico,
            "tipo_riego": finca.tipo_riego.value if finca.tipo_riego else None,
            "latitud": finca.latitud,
            "longitud": finca.longitud,
            "lote": lote,
        }

    async def _respaldos(self, finca_id: str, cultivo_id: str | None = None) -> int:
        """Número de aceptaciones humanas registradas (feedback al modelo)."""
        import uuid as uuid_mod

        from sqlalchemy import func, select

        from agroia_backend.models.aceptacion_recomendacion import AceptacionRecomendacion

        try:
            stmt = select(func.count(AceptacionRecomendacion.id)).where(
                AceptacionRecomendacion.finca_id == uuid_mod.UUID(finca_id)
            )
            if cultivo_id:
                stmt = stmt.where(
                    AceptacionRecomendacion.cultivo_id == uuid_mod.UUID(cultivo_id)
                )
            return int((await self.db.execute(stmt)).scalar_one() or 0)
        except Exception as e:  # noqa: BLE001
            logger.warning("respaldos_no_disponibles", error=str(e))
            return 0

    def _ajustar_confianza(
        self,
        confianza_base: float,
        soil_dict: dict,
        npk_sin_calibrar: bool,
        respaldos: int,
        cultivo_nombre: str | None = None,
        missing_esenciales: list[str] | None = None,
    ) -> tuple[float, float, str, list[str]]:
        """Confianza real: cobertura de datos + confiabilidad del sensor + respaldos.

        Returns:
            (confianza_real, confianza_final, estado_validacion, faltantes_fertilidad)
        """
        faltantes = [v for v in VARIABLES_FERTILIDAD if v not in soil_dict]
        factor_fertilidad = max(0.6, 1.0 - 0.04 * len(faltantes))
        factor_sensor = 0.9 if npk_sin_calibrar else 1.0
        missing_esenciales = missing_esenciales or []
        # Cada parámetro esencial faltante reduce la confianza real
        factor_esenciales = max(0.55, 1.0 - 0.15 * len(missing_esenciales))
        confianza_real = round(
            confianza_base * factor_fertilidad * factor_sensor * factor_esenciales,
            3,
        )
        # Cada aceptación humana suma +0.02 de confianza (máx +0.10)
        confianza_final = round(
            min(0.99, confianza_real + min(0.10, 0.02 * respaldos)), 3
        )

        nombre_l = (cultivo_nombre or "").lower()
        if missing_esenciales:
            # Sin parámetros esenciales: requiere aval de un agrónomo
            estado = "pendiente_validacion"
        elif nombre_l in CULTIVOS_SENSIBLES_TEXTURA and "textura" not in soil_dict:
            estado = "sujeta a confirmación de textura"
        elif confianza_final < 0.80:
            estado = "pendiente_validacion"
        elif faltantes:
            estado = "preliminar"
        else:
            estado = "validada"
        return confianza_real, confianza_final, estado, faltantes

    def _plan_ejecutable(self, variable: str, validacion_lab: bool) -> dict:
        """Plan de acción por variable: fuente, frecuencia y dosis."""
        base = PLAN_FERTILIZACION.get(variable)
        if base is None:
            return {
                "fuente": None,
                "frecuencia": None,
                "dosis": "Dosis a definir por técnico agrónomo tras análisis de laboratorio",
            }
        if validacion_lab and variable in {"N", "P", "K", "pH", "MO"}:
            dosis = "Según resultados de laboratorio y requerimiento del cultivo"
        else:
            dosis = "Dosis a definir por técnico agrónomo tras análisis de laboratorio"
        return {
            "fuente": base["fuente"],
            "frecuencia": base["frecuencia"],
            "dosis": dosis,
        }

    async def _recomendar_cultivos(
        self,
        finca_id: str,
        soil_dict: dict,
        t_start: datetime,
        advertencia_datos: str | None = None,
        finca_ctx: dict | None = None,
        npk_no_calibrado: bool = False,
        presupuesto_cop: float | None = None,
        missing_esenciales: list[str] | None = None,
    ) -> "RecommendationResult":
        """UC1: puntúa todos los cultivos y recomienda los más aptos."""
        if self.aptitud is None:
            raise RuntimeError("AptitudService no configurado en el orquestador")

        finca_ctx = finca_ctx or {}
        sugerencias = await self.aptitud.recommend_crops(
            soil_dict, top_n=5, lote=finca_ctx.get("lote")
        )

        # ── Riego de secano: priorizar cultivos resistentes a sequía ──
        tipo_riego = (finca_ctx.get("tipo_riego") or "").lower()
        advertencia_secano = None
        if tipo_riego == "secano":
            from agroia_backend.services.aptitud import CULTIVOS_RESISTENTES_SEQUIA

            for s in sugerencias:
                if s["cultivo"].lower() in CULTIVOS_RESISTENTES_SEQUIA:
                    s["score"] = round(min(100.0, float(s["score"]) + 8.0), 1)
                    s["nota_secano"] = (
                        "Riego de secano: cultivo resistente a sequía (+8)."
                    )
            sugerencias.sort(
                key=lambda s: (s["score"], s.get("reglas_especificas", 0)),
                reverse=True,
            )
            advertencia_secano = (
                "💧 La finca es de secano: se priorizaron los cultivos resistentes "
                "a sequía (+8 puntos). Si la precipitación es baja, considere "
                "reservorios o riego complementario."
            )

        top = sugerencias[0] if sugerencias else None

        cultivo = top["cultivo"] if top else "No determinado"
        clasificacion = top["clasificacion"] if top else "No apta"
        confianza = top["confianza"] if top else 0.0
        recomendaciones = top.get("ajustes", []) if top else []
        finca_ctx = finca_ctx or {}

        npk_sin_calibrar = bool(npk_no_calibrado)
        missing_esenciales = missing_esenciales or []
        respaldos = await self._respaldos(
            finca_id, top.get("cultivo_id") if top else None
        )
        confianza_real, confianza_final, estado_validacion, faltantes = (
            self._ajustar_confianza(
                confianza, soil_dict, npk_sin_calibrar, respaldos, cultivo,
                missing_esenciales,
            )
        )
        if estado_validacion == "sujeta a confirmación de textura":
            clasificacion = f"{clasificacion} (sujeta a confirmación de textura)"
        elif estado_validacion == "pendiente_validacion":
            clasificacion = f"{clasificacion} (pendiente de validación técnica)"
        elif estado_validacion == "preliminar":
            clasificacion = f"{clasificacion} (preliminar)"

        advertencia = None
        if not sugerencias:
            advertencia = (
                "⚠️ No hay cultivos evaluables: verifique que las reglas agronómicas "
                "estén cargadas (python load_seeds.py)."
            )
        elif confianza_final < 0.80:
            advertencia = (
                "⚠️ Esta recomendación tiene baja confianza y será revisada por un "
                "técnico agrónomo."
            )
        if advertencia_secano:
            advertencia = self._combinar_advertencias(advertencia, advertencia_secano)
        if faltantes:
            advertencia = self._combinar_advertencias(
                advertencia,
                "⚠️ Faltan variables de fertilidad ("
                + ", ".join(faltantes)
                + "): la clasificación es preliminar.",
            )
        if estado_validacion == "sujeta a confirmación de textura":
            advertencia = self._combinar_advertencias(
                advertencia,
                "⚠️ Sin dato de textura para un cultivo sensible al drenaje: "
                "recomendación sujeta a confirmación de textura (riesgo de "
                "asfixia radicular/pudrición).",
            )
        advertencia = self._combinar_advertencias(advertencia, advertencia_datos)

        # ── Plan económico de fertilización (brecha económica) ──
        plan_economico = None
        if presupuesto_cop is not None:
            from agroia_backend.services.economia import calcular_plan_economico

            plan_economico = calcular_plan_economico(
                recomendaciones, float(presupuesto_cop)
            )
            if plan_economico["aplazados"]:
                advertencia = self._combinar_advertencias(
                    advertencia,
                    "💰 El presupuesto no cubre todo el plan ideal: "
                    f"{len(plan_economico['aplazados'])} acción(es) aplazada(s) "
                    f"(cobertura {plan_economico['cobertura_pct']}%).",
                )

        justificacion = {
            "resumen": f"Recomendación sin siembra previa: {cultivo} ({clasificacion}).",
            "variables_analizadas": len(soil_dict),
            "cultivos_evaluados": len(sugerencias),
            "confianza": confianza_final,
            "confianza_real": confianza_real,
            "respaldos_expertos": respaldos,
        }

        elapsed_ms = (datetime.utcnow() - t_start).total_seconds() * 1000
        return RecommendationResult(
            cultivo=cultivo,
            clasificacion_upra=clasificacion,
            confianza=confianza_final,
            recomendaciones=recomendaciones,
            justificacion=justificacion,
            advertencia=advertencia,
            discordancia=None,
            tiempo_respuesta_ms=elapsed_ms,
            sugerencias_cultivos=sugerencias,
            modo="recomendar_cultivos",
            confianza_real=confianza_real,
            estado_validacion=estado_validacion,
            respaldos=respaldos,
            variables_faltantes_fertilidad=faltantes,
            variables_faltantes_esenciales=missing_esenciales,
            plan_economico=plan_economico,
        )

    async def _analizar_cultivo(
        self,
        request: RecommendationRequest,
        soil_dict: dict,
        t_start: datetime,
        advertencia_datos: str | None = None,
        finca_ctx: dict | None = None,
        npk_no_calibrado: bool = False,
        missing_esenciales: list[str] | None = None,
    ) -> "RecommendationResult":
        """UC2: evalúa el suelo contra las reglas del cultivo sembrado."""
        from sqlalchemy import select

        from agroia_backend.models.cultivo import Cultivo
        from agroia_backend.models.regla_agronomica import ReglaAgronomica

        # ── Nombre del cultivo objetivo ──
        nombre_cultivo = request.cultivo_id
        cultivo_obj = None
        try:
            cultivo_uuid = uuid.UUID(str(request.cultivo_id))
            cultivo_obj = (
                await self.db.execute(
                    select(Cultivo).where(Cultivo.id == cultivo_uuid)
                )
            ).scalar_one_or_none()
            if cultivo_obj is not None:
                nombre_cultivo = cultivo_obj.nombre
        except ValueError:
            pass  # cultivo_id no es UUID válido; se usa tal cual

        # ── Rango ideal de pH del cultivo (para contextualizar la lectura) ──
        # Se filtra en Python para no emitir casts de enum (`::variablesuelo`),
        # que dependen del search_path de la conexión (frágil en Neon/pgBouncer).
        rango_ph_cultivo = None
        try:
            reglas_cultivo = (
                await self.db.execute(
                    select(ReglaAgronomica).where(
                        ReglaAgronomica.cultivo_id == uuid.UUID(str(request.cultivo_id)),
                        ReglaAgronomica.activa.is_(True),
                    )
                )
            ).scalars().all()
            rango_ph_cultivo = next(
                (
                    r for r in reglas_cultivo
                    if getattr(r.variable, "value", r.variable) in ("PH", "pH")
                ),
                None,
            )
        except Exception as e:  # noqa: BLE001 — degrada a sin contexto
            logger.warning("rango_ph_no_resuelto", error=str(e))
            rango_ph_cultivo = None

        # ── ML Inference (modo sombra; no afecta la respuesta si falla) ──
        ml_result = None
        if self.ml:
            try:
                ml_result = await self.ml.predict(soil_dict, request.cultivo_id)
                logger.info(
                    "ml_prediction",
                    cultivo=ml_result.get("cultivo"),
                    confianza=ml_result.get("confianza"),
                )
            except Exception as e:
                logger.error("ml_inference_failed", error=str(e))

        # ── Reglas agronómicas ──
        rules_result = await self.rules.evaluate(soil_dict, request.cultivo_id)
        logger.info(
            "rules_result",
            status=rules_result.status,
            violations=len(rules_result.violations),
            warnings=len(rules_result.warnings),
        )

        # ── Detección de discordancia ML vs reglas (solo si ML activo) ──
        discordancia = None
        if ml_result and rules_result.is_blocked:
            cultivo_ml = ml_result.get("cultivo", "desconocido")
            discordancia = {
                "tipo": "ml_vs_reglas",
                "cultivo_ml": cultivo_ml,
                "confianza_ml": ml_result.get("confianza", 0),
                "regla_bloqueante": (
                    rules_result.violations[0].accion
                    if rules_result.violations else "N/A"
                ),
                "sla_vencimiento": (
                    datetime.utcnow() + timedelta(days=SLA_DISCORDANCIA_DIAS)
                ).isoformat(),
            }
            logger.warning("discordance_detected", **discordancia)

        # ── Clasificación UPRA a partir del resultado de reglas ──
        if rules_result.is_blocked:
            clasificacion = "No apta"
        elif rules_result.has_violations:
            clasificacion = "Moderadamente apta"
        else:
            clasificacion = "Apta"

        # ── Recomendaciones de qué falta / qué sobra ──
        finca_ctx = finca_ctx or {}
        validacion_lab = bool(finca_ctx.get("validacion_laboratorio"))
        npk_sin_calibrar = bool(npk_no_calibrado)
        recomendaciones = []
        for v in rules_result.violations + rules_result.warnings:
            estado = self._clasificar_estado(v)
            es_npk = v.variable in VARIABLES_NPK_SENSOR
            condicional = es_npk and not validacion_lab
            if condicional:
                npk_sin_calibrar = True
                accion = f"{v.accion} — condicional a confirmación de laboratorio"
            else:
                accion = v.accion
            fila = {
                "variable": v.variable,
                "estado": estado,
                "valor_actual": v.valor_actual,
                "rango_ideal": self._formatear_rango(v),
                "accion": accion,
                "prioridad": v.prioridad,
                "fuente": v.fuente,
                "confiabilidad": (
                    "Validado en laboratorio" if validacion_lab
                    else ("Calibrado de fábrica" if not es_npk else "Sin validar")
                ),
                "condicional": condicional,
                "plan": self._plan_ejecutable(v.variable, validacion_lab),
            }
            # Contextualizar pH: escala general + rango óptimo del cultivo
            if v.variable == "pH" and v.valor_actual is not None:
                ph = float(v.valor_actual)
                etiqueta = "ácido" if ph < 6.5 else ("alcalino" if ph > 7.5 else "neutro")
                if rango_ph_cultivo is not None and rango_ph_cultivo.umbral_min is not None \
                        and rango_ph_cultivo.umbral_max is not None:
                    dentro = (
                        rango_ph_cultivo.umbral_min <= ph <= rango_ph_cultivo.umbral_max
                    )
                    fila["contexto"] = (
                        f"pH {ph:g} — {etiqueta} en escala general, pero "
                        f"{'dentro' if dentro else 'fuera'} del rango óptimo para "
                        f"{nombre_cultivo} "
                        f"[{rango_ph_cultivo.umbral_min:g}–{rango_ph_cultivo.umbral_max:g}]"
                    )
                else:
                    fila["contexto"] = (
                        f"pH {ph:g} — {etiqueta} en escala general (sin rango "
                        f"óptimo configurado para {nombre_cultivo})."
                    )
            recomendaciones.append(fila)

        # ── Parámetros esenciales faltantes: filas explícitas (aval) ──
        missing_esenciales = missing_esenciales or []
        for var in missing_esenciales:
            recomendaciones.append({
                "variable": var,
                "estado": "SIN DATO",
                "valor_actual": None,
                "rango_ideal": "Por definir",
                "accion": (
                    f"Falta el parámetro esencial '{var}': suminístrelo para "
                    "una recomendación certera."
                ),
                "prioridad": "Alta",
                "fuente": "AgroIA — calidad de datos",
                "confiabilidad": "Sin dato",
                "condicional": False,
                "plan": self._plan_ejecutable(var, False),
            })

        # ── Confianza en función del cumplimiento de reglas ──
        penalizacion = len(rules_result.violations) * 0.20 + len(rules_result.warnings) * 0.05
        confianza = round(max(0.05, min(0.99, 1.0 - penalizacion)), 3)

        respaldos = await self._respaldos(request.finca_id, request.cultivo_id)
        confianza_real, confianza_final, estado_validacion, faltantes = (
            self._ajustar_confianza(
                confianza, soil_dict, npk_sin_calibrar, respaldos,
                str(nombre_cultivo), missing_esenciales,
            )
        )

        fenologia_ajustada = None
        etapa = (finca_ctx.get("etapa_fenologica") or "").strip().lower()
        if etapa:
            nota = AJUSTES_ETAPA.get(etapa)
            if nota:
                fenologia_ajustada = (
                    f"Etapa {finca_ctx.get('etapa_fenologica')}"
                    + (
                        f" (edad ~{finca_ctx.get('edad_anos')} años)"
                        if finca_ctx.get("edad_anos") else ""
                    )
                    + f": {nota}"
                )

        # ── Fisiología: GDD acumulado (IDEAM) vs. requerido para madurez ──
        gdd_nota = await self._gdd_faltante(cultivo_obj, finca_ctx)
        if gdd_nota:
            fenologia_ajustada = (
                fenologia_ajustada + " " + gdd_nota
                if fenologia_ajustada else gdd_nota
            )

        # ── Clasificación con estado de validación ──
        if estado_validacion == "sujeta a confirmación de textura":
            clasificacion = f"{clasificacion} (sujeta a confirmación de textura)"
        elif estado_validacion == "pendiente_validacion":
            clasificacion = f"{clasificacion} (pendiente de validación técnica)"
        elif estado_validacion == "preliminar":
            clasificacion = f"{clasificacion} (preliminar)"

        advertencia = None
        if rules_result.applied_rules == 0:
            advertencia = (
                "⚠️ No hay reglas agronómicas configuradas para este cultivo. "
                "Ejecute python load_seeds.py."
            )
        elif confianza_final < 0.80:
            advertencia = (
                "⚠️ Esta recomendación tiene baja confianza y será revisada por un "
                "técnico agrónomo."
            )
        if faltantes:
            advertencia = self._combinar_advertencias(
                advertencia,
                "⚠️ Faltan variables de fertilidad ("
                + ", ".join(faltantes)
                + "): la clasificación es preliminar y la confianza se redujo.",
            )
        if estado_validacion == "sujeta a confirmación de textura":
            advertencia = self._combinar_advertencias(
                advertencia,
                "⚠️ Sin dato de textura para un cultivo sensible al drenaje: "
                "recomendación sujeta a confirmación de textura (riesgo de "
                "asfixia radicular/pudrición).",
            )
        advertencia = self._combinar_advertencias(advertencia, advertencia_datos)

        # ── Plan económico de fertilización (brecha económica) ──
        plan_economico = None
        if request.presupuesto_cop is not None:
            from agroia_backend.services.economia import calcular_plan_economico

            plan_economico = calcular_plan_economico(
                recomendaciones, float(request.presupuesto_cop)
            )
            if plan_economico["aplazados"]:
                advertencia = self._combinar_advertencias(
                    advertencia,
                    "💰 El presupuesto no cubre todo el plan ideal: "
                    f"{len(plan_economico['aplazados'])} acción(es) aplazada(s) "
                    f"(cobertura {plan_economico['cobertura_pct']}%).",
                )

        recs_deficit = [r for r in recomendaciones if r["estado"] == "DEFICIT"]
        recs_exceso = [r for r in recomendaciones if r["estado"] == "EXCESO"]
        justificacion = {
            "resumen": (
                f"Análisis de aptitud para {nombre_cultivo}: clasificación {clasificacion}."
            ),
            "variables_analizadas": len(soil_dict),
            "reglas_aplicadas": rules_result.applied_rules,
            "faltantes": len(recs_deficit),
            "excesos": len(recs_exceso),
            "confianza": confianza_final,
            "confianza_real": confianza_real,
            "respaldos_expertos": respaldos,
        }

        elapsed_ms = (datetime.utcnow() - t_start).total_seconds() * 1000
        return RecommendationResult(
            cultivo=nombre_cultivo,
            clasificacion_upra=clasificacion,
            confianza=confianza_final,
            recomendaciones=recomendaciones,
            justificacion=justificacion,
            advertencia=advertencia,
            discordancia=discordancia,
            tiempo_respuesta_ms=elapsed_ms,
            sugerencias_cultivos=[],
            modo="analizar_cultivo",
            confianza_real=confianza_real,
            estado_validacion=estado_validacion,
            respaldos=respaldos,
            variables_faltantes_fertilidad=faltantes,
            variables_faltantes_esenciales=missing_esenciales,
            fenologia_ajustada=fenologia_ajustada,
            plan_economico=plan_economico,
        )

    async def _recomendacion_sin_datos(
        self,
        request: RecommendationRequest,
        t_start: datetime,
    ) -> RecommendationResult:
        """Recomendación preliminar cuando la finca NO tiene lecturas.

        No se bloquea la generación: se entrega una recomendación genérica
        con confianza mínima, los parámetros esenciales faltantes y el
        requisito de aval de un agrónomo.
        """
        esenciales = ["ph", "nitrogeno", "fosforo", "potasio"]
        aviso = (
            "⚠️ La finca no tiene lecturas de suelo. Esta recomendación es "
            "preliminar y NO tiene el 100% de certeza: requiere el aval de un "
            "agrónomo. Complete los parámetros esenciales (ph, nitrógeno, "
            "fósforo, potasio) para una recomendación certera."
        )
        finca_ctx = await self._cargar_contexto_finca(request.finca_id)
        elapsed_ms = (datetime.utcnow() - t_start).total_seconds() * 1000

        if request.cultivo_id is None:
            # UC1 sin datos: catálogo prioritario como ranking preliminar
            sugerencias: list[dict] = []
            evaluables: list = []
            if self.aptitud is not None:
                try:
                    evaluables = await self.aptitud._cultivos_evaluables()
                except Exception as e:  # noqa: BLE001
                    logger.warning("aptitud_no_disponible_sin_datos", error=str(e))
            prioridad = ["Café", "Maíz", "Arroz", "Plátano", "Papa"]
            evaluables.sort(
                key=lambda t: prioridad.index(t[0].nombre)
                if t[0].nombre in prioridad else len(prioridad)
            )
            for cultivo, n_reglas in evaluables[:5]:
                sugerencias.append({
                    "cultivo_id": str(cultivo.id),
                    "cultivo": cultivo.nombre,
                    "icono": cultivo.icono,
                    "score": 50.0,
                    "confianza": 0.05,
                    "clasificacion": "Preliminar",
                    "reglas_especificas": n_reglas,
                    "ajustes": [{
                        "variable": "datos_suelo",
                        "estado": "SIN DATO",
                        "valor_actual": None,
                        "rango_ideal": "Lecturas de suelo",
                        "accion": (
                            "Sin lecturas de suelo: suministre ph, nitrógeno, "
                            "fósforo y potasio para evaluar la aptitud real."
                        ),
                        "prioridad": "Alta",
                        "fuente": "AgroIA — calidad de datos",
                    }],
                })
            top = sugerencias[0] if sugerencias else None
            return RecommendationResult(
                cultivo=top["cultivo"] if top else "No determinado",
                clasificacion_upra="Preliminar",
                confianza=0.05,
                recomendaciones=[],
                justificacion={
                    "resumen": (
                        "Recomendación preliminar SIN lecturas de suelo: complete "
                        "los parámetros esenciales y vuelva a analizar para "
                        "obtener un resultado certero."
                    ),
                    "variables_analizadas": 0,
                    "cultivos_evaluados": len(sugerencias),
                    "confianza": 0.05,
                    "confianza_real": 0.05,
                    "respaldos_expertos": 0,
                },
                advertencia=aviso,
                tiempo_respuesta_ms=elapsed_ms,
                sugerencias_cultivos=sugerencias,
                modo="recomendar_cultivos",
                confianza_real=0.05,
                estado_validacion="pendiente_validacion",
                respaldos=0,
                variables_faltantes_esenciales=esenciales,
            )

        # UC2 sin datos: filas por parámetro esencial faltante
        cultivo_nombre = finca_ctx.get("cultivo_sembrado") or request.cultivo_id
        recomendaciones = [{
            "variable": var,
            "estado": "SIN DATO",
            "valor_actual": None,
            "rango_ideal": "Por definir",
            "accion": (
                f"Falta el parámetro esencial '{var}': suminístrelo para "
                "evaluar el cultivo con certeza."
            ),
            "prioridad": "Alta",
            "fuente": "AgroIA — calidad de datos",
            "confiabilidad": "Sin dato",
            "condicional": False,
            "plan": self._plan_ejecutable(var, False),
        } for var in esenciales]
        return RecommendationResult(
            cultivo=str(cultivo_nombre or "No determinado"),
            clasificacion_upra="Preliminar",
            confianza=0.05,
            recomendaciones=recomendaciones,
            justificacion={
                "resumen": (
                    "Diagnóstico preliminar SIN lecturas de suelo: la "
                    "recomendación no tiene el 100% de certeza y requiere "
                    "aval de un agrónomo."
                ),
                "variables_analizadas": 0,
                "reglas_aplicadas": 0,
                "faltantes": len(esenciales),
                "excesos": 0,
                "confianza": 0.05,
                "confianza_real": 0.05,
                "respaldos_expertos": 0,
            },
            advertencia=aviso,
            tiempo_respuesta_ms=elapsed_ms,
            sugerencias_cultivos=[],
            modo="analizar_cultivo",
            confianza_real=0.05,
            estado_validacion="pendiente_validacion",
            respaldos=0,
            variables_faltantes_esenciales=esenciales,
        )

    @staticmethod
    def _clasificar_estado(v) -> str:
        """Clasifica una violación como DEFICIT, EXCESO o DESCONOCIDO."""
        if v.valor_actual is None:
            return "DESCONOCIDO"
        if v.umbral_min is not None and v.valor_actual < v.umbral_min:
            return "DEFICIT"
        if v.umbral_max is not None and v.valor_actual > v.umbral_max:
            return "EXCESO"
        return "DESCONOCIDO"

    async def _gdd_faltante(self, cultivo, finca_ctx: dict) -> str | None:
        """Estima el GDD acumulado con IDEAM y lo compara con lo requerido.

        GDD diario = máx(0, T_promedio − 10 °C). Los días transcurridos del
        ciclo se estiman a partir de la etapa fenológica registrada en la
        finca (vegetativa 35 %, floración 55 %, fructificación 80 %,
        cosecha 100 %) sobre `dias_ciclo` de la fisiología del cultivo.
        """
        if cultivo is None:
            return None
        gdd_requerido = getattr(cultivo, "gdd_total_requerido", None)
        if not gdd_requerido:
            return None
        dias_ciclo = getattr(cultivo, "dias_ciclo", None) or 120
        lat = finca_ctx.get("latitud")
        lon = finca_ctx.get("longitud")
        if lat is None or lon is None:
            return None
        etapa = (finca_ctx.get("etapa_fenologica") or "").strip().lower()
        progreso = {
            "vegetativa": 0.35,
            "floración": 0.55,
            "floracion": 0.55,
            "fructificación": 0.80,
            "fructificacion": 0.80,
            "cosecha": 1.0,
        }.get(etapa)
        if progreso is None:
            return None
        try:
            from agroia_backend.services.external_apis import (
                fetch_ideam_climate_offline,
            )

            clima = await fetch_ideam_climate_offline(float(lat), float(lon))
            t_prom = float(clima.get("temperatura_promedio") or 0)
        except Exception as e:  # noqa: BLE001 — IDEAM no disponible
            logger.warning("gdd_no_disponible", error=str(e))
            return None
        gdd_diario = max(0.0, t_prom - 10.0)
        gdd_acumulado = gdd_diario * (progreso * dias_ciclo)
        faltante = int(gdd_requerido) - gdd_acumulado
        if faltante <= 0 or etapa == "cosecha":
            return None
        return (
            f"⏳ Faltan ~{int(faltante)} GDD para cosecha, optimice riego "
            f"(GDD acumulado ~{int(gdd_acumulado)} de {int(gdd_requerido)} "
            f"según IDEAM)."
        )

    @staticmethod
    def _combinar_advertencias(
        principal: str | None, datos: str | None
    ) -> str | None:
        """Combina la advertencia del análisis con las de calidad de datos."""
        if principal and datos:
            return f"{principal} {datos}"
        return principal or datos

    @staticmethod
    def _formatear_rango(v) -> str:
        if v.umbral_min is not None and v.umbral_max is not None:
            return f"[{v.umbral_min} - {v.umbral_max}]"
        if v.umbral_min is not None:
            return f"≥ {v.umbral_min}"
        if v.umbral_max is not None:
            return f"≤ {v.umbral_max}"
        return "—"
