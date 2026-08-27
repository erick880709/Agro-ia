"""Oráculo ML en modo sombra — diagnóstico y aptitud aprendidos.

Carga los artefactos entrenados con datos simulados colombianos
(`apps/ml/models/*.joblib`). Corre en modo sombra: sus predicciones se
comparan con el sistema experto para detectar discordancias; el sistema
experto sigue siendo la fuente de verdad de las recomendaciones.

Si no hay artefactos, `predict` devuelve None y el orquestador opera
solo con reglas (comportamiento actual).
"""

from pathlib import Path

from agroia.logging import get_logger

logger = get_logger(__name__)

VARIABLES = [
    "ph", "nitrogeno", "fosforo", "potasio", "calcio", "magnesio",
    "azufre", "hierro", "manganeso", "zinc", "cobre", "boro",
    "materia_organica", "cic", "humedad", "temperatura_suelo",
    "conductividad_electrica",
]


def _dir_modelos() -> Path:
    # repo/apps/ml/models en dev y en el contenedor (/app/apps/ml/models)
    return Path(__file__).resolve().parents[3] / "ml" / "models"


class MLOracleService:
    """Predicciones de diagnóstico (por variable) y aptitud (UC1)."""

    def __init__(self, dir_modelos: Path | None = None):
        self.dir = dir_modelos or _dir_modelos()
        self._modelos: dict[str, object] = {}
        self._medianas: dict[str, float] = {}
        self._cargados = False

    def _cargar(self) -> None:
        if self._cargados:
            return
        self._cargados = True
        if not self.dir.exists():
            logger.info("ml_oracle_sin_artefactos", dir=str(self.dir))
            return
        try:
            import joblib
        except ImportError:
            logger.error("ml_oracle_sin_joblib")
            return
        for p in self.dir.glob("ml_*.joblib"):
            nombre = p.stem  # ej. ml_diagnostico_ph, ml_aptitud
            try:
                self._modelos[nombre] = joblib.load(p)
            except Exception as e:  # noqa: BLE001
                logger.warning("ml_oracle_carga_fallida", modelo=nombre, error=str(e))
        meta_path = self.dir / "ml_meta.json"
        if meta_path.exists():
            try:
                import json

                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                self._medianas = {k: float(v) for k, v in meta.get("medianas", {}).items()}
            except Exception as e:  # noqa: BLE001
                logger.warning("ml_oracle_meta_fallida", error=str(e))
        logger.info("ml_oracle_modelos_cargados", n=len(self._modelos), medianas=len(self._medianas))

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
            }
        except Exception as e:  # noqa: BLE001
            logger.error("ml_oracle_inferencia_fallida", error=str(e))
            return None
