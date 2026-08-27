"""Orquestador híbrido de recomendaciones — ML + Reglas.

Coordina el pipeline completo: recibe solicitud → consulta datos →
invoca modelos ML → aplica reglas → detecta discordancia → ensambla respuesta.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from agroia.errors import InsufficientDataError
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
    fenologia_ajustada: str | None = None


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
        if soil_data is None or not soil_data.has_sufficient_data:
            missing = soil_data.missing_blocking if soil_data else ["ph", "nitrogeno", "fosforo", "potasio"]
            logger.warning("insufficient_data", finca_id=request.finca_id, missing=missing)
            raise InsufficientDataError(missing)

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
        advertencia_datos = " ".join(advertencias_datos) or None

        # ── Paso 2: Ramificación por caso de uso ──
        npk_no_calibrado = soil_data.calidad == "npk_no_calibrado"
        if request.cultivo_id is None:
            # UC1: no hay cultivo sembrado → recomendar qué sembrar
            return await self._recomendar_cultivos(
                request.finca_id, soil_dict, t_start, advertencia_datos,
                finca_ctx, npk_no_calibrado,
            )

        # UC2: hay cultivo sembrado → diagnosticar qué falta/sobra
        return await self._analizar_cultivo(
            request, soil_dict, t_start, advertencia_datos, finca_ctx,
            npk_no_calibrado,
        )

    async def _cargar_contexto_finca(self, finca_id: str) -> dict:
        """Datos agronómicos de la finca: validación de laboratorio, fenología…"""
        from sqlalchemy import select

        from agroia_backend.models.finca import Finca

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
        return {
            "validacion_laboratorio": bool(finca.validacion_laboratorio),
            "cultivo_sembrado": finca.cultivo_sembrado,
            "edad_anos": finca.edad_anos,
            "etapa_fenologica": finca.etapa_fenologica,
            "pendiente_pct": finca.pendiente_pct,
            "drenaje": finca.drenaje,
            "historial_agronomico": finca.historial_agronomico,
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
    ) -> tuple[float, float, str, list[str]]:
        """Confianza real: cobertura de datos + confiabilidad del sensor + respaldos.

        Returns:
            (confianza_real, confianza_final, estado_validacion, faltantes_fertilidad)
        """
        faltantes = [v for v in VARIABLES_FERTILIDAD if v not in soil_dict]
        factor_fertilidad = max(0.6, 1.0 - 0.04 * len(faltantes))
        factor_sensor = 0.9 if npk_sin_calibrar else 1.0
        confianza_real = round(confianza_base * factor_fertilidad * factor_sensor, 3)
        # Cada aceptación humana suma +0.02 de confianza (máx +0.10)
        confianza_final = round(
            min(0.99, confianza_real + min(0.10, 0.02 * respaldos)), 3
        )

        nombre_l = (cultivo_nombre or "").lower()
        if nombre_l in CULTIVOS_SENSIBLES_TEXTURA and "textura" not in soil_dict:
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
    ) -> "RecommendationResult":
        """UC1: puntúa todos los cultivos y recomienda los más aptos."""
        if self.aptitud is None:
            raise RuntimeError("AptitudService no configurado en el orquestador")

        sugerencias = await self.aptitud.recommend_crops(soil_dict, top_n=5)
        top = sugerencias[0] if sugerencias else None

        cultivo = top["cultivo"] if top else "No determinado"
        clasificacion = top["clasificacion"] if top else "No apta"
        confianza = top["confianza"] if top else 0.0
        recomendaciones = top.get("ajustes", []) if top else []
        finca_ctx = finca_ctx or {}

        npk_sin_calibrar = bool(npk_no_calibrado)
        for r in recomendaciones:
            if r.get("variable") in VARIABLES_NPK_SENSOR:
                npk_sin_calibrar = True
        respaldos = await self._respaldos(
            finca_id, top.get("cultivo_id") if top else None
        )
        confianza_real, confianza_final, estado_validacion, faltantes = (
            self._ajustar_confianza(
                confianza, soil_dict, npk_sin_calibrar, respaldos, cultivo
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
        )

    async def _analizar_cultivo(
        self,
        request: RecommendationRequest,
        soil_dict: dict,
        t_start: datetime,
        advertencia_datos: str | None = None,
        finca_ctx: dict | None = None,
        npk_no_calibrado: bool = False,
    ) -> "RecommendationResult":
        """UC2: evalúa el suelo contra las reglas del cultivo sembrado."""
        from sqlalchemy import select

        from agroia_backend.models.cultivo import Cultivo
        from agroia_backend.models.regla_agronomica import ReglaAgronomica

        # ── Nombre del cultivo objetivo ──
        nombre_cultivo = request.cultivo_id
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
        rango_ph_cultivo = None
        try:
            rango_ph_cultivo = (
                await self.db.execute(
                    select(ReglaAgronomica).where(
                        ReglaAgronomica.cultivo_id == uuid.UUID(str(request.cultivo_id)),
                        ReglaAgronomica.variable == "PH",
                        ReglaAgronomica.activa.is_(True),
                    ).limit(1)
                )
            ).scalar_one_or_none()
        except (ValueError, TypeError):
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

        # ── Confianza en función del cumplimiento de reglas ──
        penalizacion = len(rules_result.violations) * 0.20 + len(rules_result.warnings) * 0.05
        confianza = round(max(0.05, min(0.99, 1.0 - penalizacion)), 3)

        respaldos = await self._respaldos(request.finca_id, request.cultivo_id)
        confianza_real, confianza_final, estado_validacion, faltantes = (
            self._ajustar_confianza(
                confianza, soil_dict, npk_sin_calibrar, respaldos,
                str(nombre_cultivo),
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
            fenologia_ajustada=fenologia_ajustada,
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
