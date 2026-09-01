"""Oráculo ML en modo sombra — diagnóstico y aptitud aprendidos.

Carga los artefactos entrenados con datos simulados colombianos
(`apps/ml/models/*.joblib`). Corre en modo sombra: sus predicciones se
comparan con el sistema experto para detectar discordancias; el sistema
experto sigue siendo la fuente de verdad de las recomendaciones.

Si no hay artefactos, `predict` devuelve None y el orquestador opera
solo con reglas (comportamiento actual).
"""

from pathlib import Path
from threading import Lock

from agroia.logging import get_logger

logger = get_logger(__name__)

VARIABLES = [
    "ph", "nitrogeno", "fosforo", "potasio", "calcio", "magnesio",
    "azufre", "hierro", "manganeso", "zinc", "cobre", "boro",
    "materia_organica", "cic", "humedad", "temperatura_suelo",
    "conductividad_electrica",
]

# Caché compartida de artefactos: los joblib (~18 MB) se cargan UNA sola vez
# por proceso. Antes se cargaban en cada request (analyze/reporte/estado), lo
# que multiplicaba el uso de memoria y disparaba OOM en Render Free (512 MB).
_CACHE_LOCK = Lock()
_CACHE_ESTADO: dict[str, dict] = {}


def _dir_modelos() -> Path:
    # repo/apps/ml/models en dev y en el contenedor (/app/apps/ml/models)
    return Path(__file__).resolve().parents[3] / "ml" / "models"


def _cargar_artefactos(dir_modelos: Path) -> dict:
    """Lee modelos/medianas/promovidas del directorio (una vez por proceso)."""
    estado: dict = {"modelos": {}, "medianas": {}, "promovidas": {}}
    if not dir_modelos.exists():
        logger.info("ml_oracle_sin_artefactos", dir=str(dir_modelos))
        return estado
    try:
        import joblib
    except ImportError:
        logger.error("ml_oracle_sin_joblib")
        return estado
    for p in dir_modelos.glob("ml_*.joblib"):
        nombre = p.stem  # ej. ml_diagnostico_ph, ml_aptitud
        try:
            estado["modelos"][nombre] = joblib.load(p)
        except Exception as e:  # noqa: BLE001
            logger.warning("ml_oracle_carga_fallida", modelo=nombre, error=str(e))
    meta_path = dir_modelos / "ml_meta.json"
    if meta_path.exists():
        try:
            import json

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            estado["medianas"] = {k: float(v) for k, v in meta.get("medianas", {}).items()}
            estado["promovidas"] = {
                str(k): dict(v) if isinstance(v, dict) else {}
                for k, v in meta.get("promovidas", {}).items()
            }
        except Exception as e:  # noqa: BLE001
            logger.warning("ml_oracle_meta_fallida", error=str(e))
    logger.info(
        "ml_oracle_modelos_cargados",
        n=len(estado["modelos"]), medianas=len(estado["medianas"]),
        promovidas=len(estado["promovidas"]),
    )
    return estado


class MLOracleService:
    """Predicciones de diagnóstico (por variable) y aptitud (UC1)."""

    def __init__(self, dir_modelos: Path | None = None):
        self.dir = dir_modelos or _dir_modelos()
        self._modelos: dict[str, object] = {}
        self._medianas: dict[str, float] = {}
        self._promovidas: dict[str, dict] = {}
        self._cargados = False

    def _cargar(self) -> None:
        if self._cargados:
            return
        self._cargados = True
        clave = str(self.dir)
        estado = _CACHE_ESTADO.get(clave)
        if estado is None:
            with _CACHE_LOCK:
                estado = _CACHE_ESTADO.get(clave)
                if estado is None:
                    estado = _cargar_artefactos(self.dir)
                    _CACHE_ESTADO[clave] = estado
        self._modelos = estado["modelos"]
        self._medianas = estado["medianas"]
        self._promovidas = estado["promovidas"]

    def variables_promovidas(self) -> set[str]:
        """Variables cuyo modelo fue promovido a producción (validador activo)."""
        self._cargar()
        return set(self._promovidas.keys())

    def disponible(self) -> bool:
        self._cargar()
        return len(self._modelos) > 0

    def _features(self, soil_dict: dict, cultivo_idx: int):
        try:
            import numpy as np
        except ImportError:
            return None
        X = np.full((1, len(VARIABLES) + 1), -1.0, dtype=float)
        for j, var in enumerate(VARIABLES):
            val = soil_dict.get(var)
            if val is None:
                val = self._medianas.get(var, -1.0)
            X[0, j] = float(val)
        X[0, len(VARIABLES)] = cultivo_idx
        return X

    async def predict(self, soil_dict: dict, cultivo_id: str | None = None) -> dict | None:
        """Predicción sombra.

        Returns:
            dict con diagnóstico por variable, aptitud y confianza (media de
            probabilidades máximas), o None si no hay artefactos.
        """
        self._cargar()
        if not self._modelos:
            return None
        try:
            import numpy as np

            idx = 0 if cultivo_id is None else (abs(hash(str(cultivo_id))) % 5)
            X = self._features(soil_dict, idx)
            if X is None:
                return None
            diagnostico = {}
            confianzas = []
            for nombre, modelo in self._modelos.items():
                if not nombre.startswith("ml_diagnostico_"):
                    continue
                var = nombre[len("ml_diagnostico_"):]
                proba = modelo.predict_proba(X)[0]
                clase = modelo.classes_[int(np.argmax(proba))]
                diagnostico[var] = {
                    "estado": str(clase),
                    "confianza": round(float(proba.max()), 3),
                    "promovido": var in self._promovidas,
                }
                confianzas.append(float(proba.max()))
            aptitud = None
            conf_apt = None
            if "ml_aptitud" in self._modelos:
                m = self._modelos["ml_aptitud"]
                proba = m.predict_proba(X)[0]
                aptitud = str(m.classes_[int(np.argmax(proba))])
                conf_apt = round(float(proba.max()), 3)
                confianzas.append(float(proba.max()))
            return {
                "disponible": True,
                "cultivo": aptitud,
                "clasificacion": aptitud,
                "diagnostico": diagnostico,
                "confianza": round(float(np.mean(confianzas)), 3) if confianzas else 0.0,
                "confianza_aptitud": conf_apt,
                "promovidas": sorted(self._promovidas.keys()),
            }
        except Exception as e:  # noqa: BLE001
            logger.error("ml_oracle_inferencia_fallida", error=str(e))
            return None
