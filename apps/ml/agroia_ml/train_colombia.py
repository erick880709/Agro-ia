"""Entrenamiento del modelo de recomendación y diagnóstico con datos simulados.

El sistema experto (reglas UPRA/Cenicafé/AGROSAVIA) es la fuente de verdad.
Este script:

1. Simula miles de perfiles de suelo colombianos (distribuciones agronómicas
   plausibles de las 18 variables) para cada cultivo del catálogo.
2. Etiqueta cada perfil con el propio sistema experto:
   - Diagnóstico por variable (UC2): DEFICIT / OK / EXCESO según umbrales.
   - Clasificación de aptitud (UC1): Apta / Moderadamente apta /
     Marginalmente apta / No apta según el score del motor de reglas.
3. Entrena RandomForest (uno por variable + uno de aptitud) y evalúa:
   - Holdout estratificado (accuracy, precision, recall, F1 ponderados).
   - Validación cruzada 5-fold.
   - Concordancia sobre datos REALES de sensores almacenados en la BD.
4. Aprendizaje activo (`--active-learning`): combina los datos sintéticos con
   las ETIQUETAS DORADAS (aceptaciones humanas por variable + ciclos cerrados
   con rendimiento real), pondera más las muestras reales y evalúa la
   PRECISIÓN REAL por variable sobre un holdout separado por finca.
   Las variables con precisión real ≥ 0.85 (con ≥ 5 muestras) se PROMUEVEN
   a producción de forma individual (`ml_diagnostico_<var>` activo).
5. Guarda artefactos en apps/ml/models/ y los registra en `modelos_ml`
   y `metricas_modelo` (stage STAGING o PRODUCTION por variable).

Uso:
    .venv\Scripts\python.exe -m agroia_ml.train_colombia
    .venv\Scripts\python.exe -m agroia_ml.train_colombia --registrar
    .venv\Scripts\python.exe -m agroia_ml.train_colombia --registrar --active-learning
"""

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, train_test_split

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# ── Parámetros del aprendizaje activo ──
W_GOLDEN = 10.0               # peso de cada muestra real vs. 1.0 sintética
UMBRAL_PROMOCION = 0.85       # precisión real mínima para promover una variable
MIN_GOLDEN_PROMO = 5          # muestras reales mínimas en el holdout

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODELS_DIR.mkdir(exist_ok=True)

# ── Variables canónicas y rangos plausibles de simulación (Colombia) ──
VARIABLES = [
    "ph", "nitrogeno", "fosforo", "potasio", "calcio", "magnesio",
    "azufre", "hierro", "manganeso", "zinc", "cobre", "boro",
    "materia_organica", "cic", "humedad", "temperatura_suelo",
    "conductividad_electrica",
]
RANGOS = {
    "ph": (3.5, 9.0),
    "nitrogeno": (0.0, 450.0),
    "fosforo": (0.0, 120.0),
    "potasio": (0.0, 550.0),
    "calcio": (150.0, 6500.0),
    "magnesio": (15.0, 900.0),
    "azufre": (0.5, 120.0),
    "hierro": (0.5, 350.0),
    "manganeso": (0.2, 220.0),
    "zinc": (0.1, 60.0),
    "cobre": (0.05, 25.0),
    "boro": (0.05, 6.0),
    "materia_organica": (0.0, 22.0),
    "cic": (2.0, 65.0),
    "humedad": (0.0, 60.0),
    "temperatura_suelo": (5.0, 40.0),
    "conductividad_electrica": (0.0, 20.0),
}
PESOS_PRIORIDAD = {"Critica": 30, "Alta": 20, "Media": 10, "Baja": 5}

# Cobertura de reglas por cultivo (para saber qué variables simular "cerca" del ideal)
# se calcula en tiempo real desde la BD; aquí solo los nombres para el reporte.


def clasificar_aptitud(score: float) -> str:
    if score >= 80:
        return "Apta"
    if score >= 60:
        return "Moderadamente apta"
    if score >= 40:
        return "Marginalmente apta"
    return "No apta"


def generar_muestra(rng: np.random.Generator, reglas: list[dict]) -> dict:
    """Genera un perfil de suelo sintético con valores plausibles."""
    muestra = {}
    for var, (lo, hi) in RANGOS.items():
        # mezcla de uniforme amplia + normal alrededor del centro
        if rng.random() < 0.55:
            v = rng.uniform(lo, hi)
        else:
            centro = (lo + hi) / 2.0
            sigma = (hi - lo) / 6.0
            v = rng.normal(centro, sigma)
        muestra[var] = float(np.clip(v, lo, hi))
    return muestra


def etiquetar(muestra: dict, reglas: list[dict]) -> tuple[dict, float, dict]:
    """Aplica el sistema experto: estado por variable + score + ajustes."""
    estados: dict[str, str] = {}
    penalizacion = 0.0
    ajustes: list[dict] = []
    for r in reglas:
        var = r["variable"].lower()
        clave = {
            "ph": "ph", "n": "nitrogeno", "p": "fosforo", "k": "potasio",
            "ca": "calcio", "mg": "magnesio", "s": "azufre", "fe": "hierro",
            "mn": "manganeso", "zn": "zinc", "cu": "cobre", "b": "boro",
            "mo": "materia_organica", "cic": "cic", "humedad": "humedad",
            "temperatura_suelo": "temperatura_suelo", "ce": "conductividad_electrica",
        }.get(var)
        if clave is None or clave not in muestra:
            continue
        v = muestra[clave]
        umin, umax = r["umbral_min"], r["umbral_max"]
        estado = "OK"
        if umin is not None and v < umin:
            estado = "DEFICIT"
        elif umax is not None and v > umax:
            estado = "EXCESO"
        estados[clave] = estado
        if estado != "OK":
            penalizacion += PESOS_PRIORIDAD.get(r["prioridad"], 10)
            ajustes.append({"variable": clave, "estado": estado})
    score = max(0.0, 100.0 - min(penalizacion, 100.0))
    return estados, score, {"penalizacion": penalizacion, "ajustes": ajustes}


async def cargar_reglas_y_cultivos() -> tuple[list[dict], list[dict]]:
    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.cultivo import Cultivo
    from agroia_backend.models.regla_agronomica import ReglaAgronomica

    async with async_session_factory() as db:
        reglas = (
            await db.execute(
                select(ReglaAgronomica).where(ReglaAgronomica.activa.is_(True))
            )
        ).scalars().all()
        cultivos = (
            await db.execute(
                select(Cultivo).where(Cultivo.activo.is_(True))
            )
        ).scalars().all()
    reglas_dict = [
        {
            "variable": r.variable.value,
            "umbral_min": r.umbral_min,
            "umbral_max": r.umbral_max,
            "accion": r.accion,
            "prioridad": r.prioridad.value,
            "fuente": r.fuente,
            "cultivo_id": str(r.cultivo_id) if r.cultivo_id else None,
        }
        for r in reglas
    ]
    cultivos_dict = [{"id": str(c.id), "nombre": c.nombre} for c in cultivos]
    return reglas_dict, cultivos_dict


async def cargar_datos_reales(limite: int = 400) -> list[dict]:
    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.sensor_reading import SensorReading

    async with async_session_factory() as db:
        lecturas = (
            await db.execute(
                select(SensorReading).order_by(SensorReading.ts.desc()).limit(limite)
            )
        ).scalars().all()
    muestras = []
    for r in lecturas:
        m = {}
        for var in VARIABLES:
            v = getattr(r, var, None)
            if v is not None:
                m[var] = float(v)
        if m:
            muestras.append(m)
    return muestras


def _features(muestras: list[dict], cultivo_idx: int, medianas: dict | None = None) -> np.ndarray:
    """Matriz de features; imputa valores faltantes con la mediana de la variable."""
    med = medianas or {}
    X = np.full((len(muestras), len(VARIABLES) + 1), -1.0, dtype=float)
    for i, m in enumerate(muestras):
        for j, var in enumerate(VARIABLES):
            X[i, j] = float(m.get(var, med.get(var, -1.0)))
        X[i, len(VARIABLES)] = cultivo_idx
    return X


def _particion_por_finca(
    filas: list[dict], test_frac: float = 0.5, semilla: int = RANDOM_STATE,
) -> tuple[list[dict], list[dict]]:
    """Divide las filas doradas por FINCA (sin fuga de datos entre particiones)."""
    if not filas:
        return [], []
    fincas = sorted({f["finca_id"] for f in filas})
    if len(fincas) < 2:
        # una sola finca: todo va a test (evaluación honesta, sin reentrenar)
        return [], list(filas)
    rng = np.random.default_rng(semilla)
    rng.shuffle(fincas)
    n_test_fincas = max(1, int(round(len(fincas) * test_frac)))
    test_ids = set(fincas[:n_test_fincas])
    train = [f for f in filas if f["finca_id"] not in test_ids]
    test = [f for f in filas if f["finca_id"] in test_ids]
    return train, test


def _entrenar_con_golden(X_synth, y_synth, X_golden, y_golden):
    """Reentrena combinando sintéticos + dorados (muestras reales con más peso)."""
    X = np.vstack([X_synth, X_golden])
    y = np.concatenate([y_synth, y_golden])
    pesos = np.concatenate([
        np.ones(len(y_synth)),
        np.full(len(y_golden), W_GOLDEN),
    ])
    modelo = RandomForestClassifier(
        n_estimators=120, max_depth=12, random_state=RANDOM_STATE, n_jobs=-1
    )
    modelo.fit(X, y, sample_weight=pesos)
    return modelo


def _metricas_golden(modelo, X_g, y_g) -> dict | None:
    """Métricas REALES del modelo sobre el holdout dorado (mínimo 2 clases)."""
    if X_g is None or len(y_g) < 2 or len(set(y_g)) < 2:
        return None
    y_pred = modelo.predict(X_g)
    return {
        "accuracy": round(float(accuracy_score(y_g, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_g, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_g, y_pred, average="macro", zero_division=0)), 4),
        "n": int(len(y_g)),
    }


def entrenar_y_evaluar(nombre: str, X, y, clases, con_cv: bool = False) -> dict:
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    modelo = RandomForestClassifier(
        n_estimators=120, max_depth=12, random_state=RANDOM_STATE, n_jobs=-1
    )
    modelo.fit(X_tr, y_tr)
    y_pred = modelo.predict(X_te)
    cv = None
    if con_cv:
        cv = cross_val_score(modelo, X, y, cv=5, scoring="f1_weighted")
    return {
        "nombre": nombre,
        "n": len(y),
        "accuracy": round(float(accuracy_score(y_te, y_pred)), 4),
        "precision": round(float(precision_score(y_te, y_pred, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_te, y_pred, average="weighted", zero_division=0)), 4),
        "f1": round(float(f1_score(y_te, y_pred, average="weighted", zero_division=0)), 4),
        "cv_f1_mean": round(float(cv.mean()), 4) if cv is not None else None,
        "cv_f1_std": round(float(cv.std()), 4) if cv is not None else None,
        "clases": sorted(set(y)),
        "modelo": modelo,
        "clasificacion_report": classification_report(y_te, y_pred, zero_division=0),
    }


async def main(registrar: bool = False, active_learning: bool = False) -> None:
    reglas, cultivos = await cargar_reglas_y_cultivos()
    cultivos_con_reglas = [
        c for c in cultivos
        if any(r["cultivo_id"] == c["id"] or r["cultivo_id"] is None for r in reglas)
    ]
    print(f"Reglas activas: {len(reglas)} · Cultivos: {len(cultivos)} "
          f"(con reglas: {len(cultivos_con_reglas)})")
    variables_con_regla = sorted({r["variable"].lower() for r in reglas})
    print(f"Variables con regla: {variables_con_regla}")

    rng = np.random.default_rng(RANDOM_STATE)
    N_POR_CULTIVO = 2500
    muestras: list[dict] = []  # {features, cultivo_idx, y_var, y_apt}
    for c_idx, cultivo in enumerate(cultivos_con_reglas):
        reglas_cultivo = [
            r for r in reglas
            if r["cultivo_id"] == cultivo["id"] or r["cultivo_id"] is None
        ]
        # reforzar muestras cerca del ideal para balancear clases
        for _ in range(N_POR_CULTIVO):
            m = generar_muestra(rng, reglas_cultivo)
            # con probabilidad 0.4, empujar cada variable con regla cerca del rango ideal
            if rng.random() < 0.4:
                for r in reglas_cultivo:
                    clave = {
                        "ph": "ph", "n": "nitrogeno", "p": "fosforo", "k": "potasio",
                        "ca": "calcio", "mg": "magnesio", "s": "azufre", "fe": "hierro",
                        "mn": "manganeso", "zn": "zinc", "cu": "cobre", "b": "boro",
                        "mo": "materia_organica", "cic": "cic", "humedad": "humedad",
                        "temperatura_suelo": "temperatura_suelo", "ce": "conductividad_electrica",
                    }.get(r["variable"].lower())
                    if clave is None or clave not in m:
                        continue
                    lo, hi = RANGOS[clave]
                    if r["umbral_min"] is not None and r["umbral_max"] is not None:
                        centro = (r["umbral_min"] + r["umbral_max"]) / 2.0
                        sigma = max((r["umbral_max"] - r["umbral_min"]) / 4.0, 0.01)
                    elif r["umbral_min"] is not None:
                        centro = r["umbral_min"] + (hi - r["umbral_min"]) * 0.5
                        sigma = max((hi - r["umbral_min"]) / 4.0, 0.01)
                    else:
                        centro = (lo + r["umbral_max"]) / 2.0
                        sigma = max((r["umbral_max"] - lo) / 4.0, 0.01)
                    m[clave] = float(np.clip(rng.normal(centro, sigma), lo, hi))
            estados, score, _ = etiquetar(m, reglas_cultivo)
            muestras.append({
                "m": m,
                "cultivo_idx": c_idx,
                "y_var": estados,
                "y_apt": clasificar_aptitud(score),
            })
    print(f"Muestras sintéticas generadas: {len(muestras)}")

    # ── Imputación: medianas por variable (datos faltantes de sensores) ──
    medianas: dict[str, float] = {}
    for var in VARIABLES:
        valores = [s["m"].get(var) for s in muestras if var in s["m"]]
        medianas[var] = round(float(np.median(valores)), 4) if valores else -1.0
    print(f"Medianas de imputación calculadas ({len(medianas)} variables)")

    # Enmascarar ~35% de muestras (30-60% de variables faltantes) para que el
    # modelo aprenda a predecir con datos incompletos, como los sensores reales.
    muestras_masked: list[dict] = []
    for s in muestras:
        m = dict(s["m"])
        if rng.random() < 0.35:
            n_vars = len(VARIABLES)
            k = int(rng.integers(int(n_vars * 0.3), int(n_vars * 0.6) + 1))
            for var in rng.choice(VARIABLES, size=k, replace=False):
                m.pop(var, None)
        muestras_masked.append(m)

    # ── Etiquetas doradas (Ground Truth humano) para aprendizaje activo ──
    etiquetas_golden: list[dict] = []
    ciclos_golden: list[dict] = []
    if active_learning:
        from agroia.database import async_session_factory
        from agroia_backend.services.ml_labels import cargar_etiquetas_doradas

        async with async_session_factory() as db:
            etiquetas_golden, ciclos_golden = await cargar_etiquetas_doradas(db)
    print(f"Etiquetas doradas: {len(etiquetas_golden)} aceptaciones · "
          f"{len(ciclos_golden)} ciclos cerrados (aprendizaje activo "
          f"{'ACTIVO' if active_learning else 'desactivado'})", flush=True)

    # ── Entrenar diagnóstico por variable ──
    claves_variables = {
        "ph": "ph", "n": "nitrogeno", "p": "fosforo", "k": "potasio",
        "ca": "calcio", "mg": "magnesio", "s": "azufre", "fe": "hierro",
        "mn": "manganeso", "zn": "zinc", "cu": "cobre", "b": "boro",
        "mo": "materia_organica", "cic": "cic", "humedad": "humedad",
        "temperatura_suelo": "temperatura_suelo", "ce": "conductividad_electrica",
    }
    variables_modelo = sorted({claves_variables[v] for v in variables_con_regla if v in claves_variables})
    resultados: list[dict] = []
    modelos_artefactos: dict[str, object] = {}

    X_all = _features(muestras_masked, 0, medianas)
    _ = X_all  # noqa: F841 (features sin cultivo para diagnóstico variable)
    promovidas: dict[str, dict] = {}
    for var in variables_modelo:
        X = _features(muestras_masked, 0, medianas)
        y = np.array([s["y_var"].get(var, "OK") for s in muestras])
        r = entrenar_y_evaluar(f"diagnostico_{var}", X, y, sorted(set(y)), con_cv=False)
        if "modelo" not in r:
            r.pop("clasificacion_report", None)
            resultados.append(r)
            print(f"  {r.get('nombre')}: sin modelo ({r.get('nota', 'n/d')})", flush=True)
            continue
        modelo = r.pop("modelo")
        r.pop("clasificacion_report", None)

        # ── Aprendizaje activo: reforzar con etiquetas doradas de la variable ──
        r["n_golden"] = 0
        r["precision_real"] = None
        r["f1_real"] = None
        r["promovida"] = False
        if active_learning and etiquetas_golden:
            gold_var = [f for f in etiquetas_golden if var in f["etiquetas"]]
            r["n_golden"] = len(gold_var)
            if gold_var:
                train_g, test_g = _particion_por_finca(gold_var)
                if train_g:
                    X_gt = _features([f["features"] for f in train_g], 0, medianas)
                    y_gt = np.array([f["etiquetas"][var] for f in train_g])
                    modelo = _entrenar_con_golden(X, y, X_gt, y_gt)
                m_gold = None
                if test_g:
                    X_gte = _features([f["features"] for f in test_g], 0, medianas)
                    y_gte = np.array([f["etiquetas"][var] for f in test_g])
                    m_gold = _metricas_golden(modelo, X_gte, y_gte)
                if m_gold:
                    r["precision_real"] = m_gold["precision_macro"]
                    r["f1_real"] = m_gold["f1_macro"]
                    r["accuracy_real"] = m_gold["accuracy"]
                    r["n_golden_test"] = m_gold["n"]
                    if (
                        m_gold["n"] >= MIN_GOLDEN_PROMO
                        and m_gold["precision_macro"] >= UMBRAL_PROMOCION
                    ):
                        r["promovida"] = True
                        promovidas[var] = {
                            "precision_real": m_gold["precision_macro"],
                            "f1_real": m_gold["f1_macro"],
                            "n_golden_test": m_gold["n"],
                        }
        modelos_artefactos[f"ml_diagnostico_{var}"] = modelo
        resultados.append(r)
        print(
            f"  {r.get('nombre')}: f1={r.get('f1')} acc={r.get('accuracy')} "
            f"prec={r.get('precision')} (n={r.get('n')})"
            + (f" | golden={r['n_golden']} prec_real={r['precision_real']}"
               + (" ⭐PROMOVIDA" if r["promovida"] else "")
               if active_learning else ""),
            flush=True,
        )

    if active_learning and promovidas:
        print(f"\n⭐ Variables promovidas a producción: {sorted(promovidas)}", flush=True)
    elif active_learning:
        print(
            "\nSin variables promovidas (precisión real < 0.85 o muestras "
            "doradas insuficientes): todos los modelos quedan en STAGING.",
            flush=True,
        )

    # ── Entrenar clasificador de aptitud (UC1) ──
    X_apt = _features(muestras_masked, 0, medianas)
    for i, s in enumerate(muestras):
        X_apt[i, len(VARIABLES)] = s["cultivo_idx"]
    y_apt = np.array([s["y_apt"] for s in muestras])
    r_apt = entrenar_y_evaluar("aptitud_upra", X_apt, y_apt, sorted(set(y_apt)), con_cv=True)
    if "modelo" in r_apt:
        modelos_artefactos["ml_aptitud"] = r_apt.pop("modelo")
    r_apt.pop("clasificacion_report", None)

    # ── Aprendizaje activo en aptitud: ciclos cerrados con rendimiento real ──
    concordancia_golden = None
    r_apt["promovida_aptitud"] = False
    if active_learning and ciclos_golden and "ml_aptitud" in modelos_artefactos:
        train_c, test_c = _particion_por_finca(ciclos_golden)
        if train_c:
            X_ct = _features([f["features"] for f in train_c], 0, medianas)
            y_ct = np.array([f["etiqueta_aptitud"] for f in train_c])
            modelos_artefactos["ml_aptitud"] = _entrenar_con_golden(
                X_apt, y_apt, X_ct, y_ct
            )
        if test_c:
            X_cte = _features([f["features"] for f in test_c], 0, medianas)
            y_cte = np.array([f["etiqueta_aptitud"] for f in test_c])
            m_apt_gold = _metricas_golden(modelos_artefactos["ml_aptitud"], X_cte, y_cte)
            if m_apt_gold:
                concordancia_golden = m_apt_gold["accuracy"]
                r_apt["concordancia_golden"] = concordancia_golden
                r_apt["n_golden_aptitud"] = m_apt_gold["n"]
                r_apt["promovida_aptitud"] = (
                    m_apt_gold["n"] >= MIN_GOLDEN_PROMO
                    and concordancia_golden >= UMBRAL_PROMOCION
                )
    resultados.append(r_apt)
    print(f"  {r_apt.get('nombre')}: f1={r_apt.get('f1')} acc={r_apt.get('accuracy')} "
          f"cv={r_apt.get('cv_f1_mean')}±{r_apt.get('cv_f1_std')} (n={r_apt.get('n')})"
          + (f" | concordancia_golden={concordancia_golden}" if active_learning else ""))

    # ── Evaluación con datos reales de sensores ──
    reales = await cargar_datos_reales(400)
    real_eval: list[dict] = []
    if reales and modelos_artefactos:
        for cultivo_idx, cultivo in enumerate(cultivos_con_reglas):
            reglas_cultivo = [
                r for r in reglas
                if r["cultivo_id"] == cultivo["id"] or r["cultivo_id"] is None
            ]
            X_r = _features(reales, cultivo_idx, medianas)
            # etiquetas reales del sistema experto
            y_apt_r = []
            for m in reales:
                estados, score, _ = etiquetar(m, reglas_cultivo)
                y_apt_r.append(clasificar_aptitud(score))
            if len(set(y_apt_r)) < 2:
                continue
            y_pred_r = modelos_artefactos["ml_aptitud"].predict(X_r)
            real_eval.append({
                "cultivo": cultivo["nombre"],
                "n": len(reales),
                "concordancia_aptitud": round(
                    float(accuracy_score(y_apt_r, y_pred_r)), 4
                ),
                "dist_etiquetas": {k: y_apt_r.count(k) for k in sorted(set(y_apt_r))},
            })
        print("\nEvaluación sobre datos reales del sensor (etiquetas del sistema experto):")
        for e in real_eval:
            print(f"  {e['cultivo']}: concordancia={e['concordancia_aptitud']} "
                  f"dist={e['dist_etiquetas']}")
    else:
        print("\nSin datos reales para evaluación.")

    concordancia_media = (
        round(float(np.mean([e["concordancia_aptitud"] for e in real_eval])), 4)
        if real_eval else None
    )
    print(f"\nConcordancia media en datos reales: {concordancia_media}")

    # ── Guardar artefactos ──
    meta = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "variables": VARIABLES,
        "medianas": medianas,
        "imputacion": "mediana_por_variable_sinteticos",
        "missingness_sintetico": 0.35,
        "cultivos_entrenados": [c["nombre"] for c in cultivos_con_reglas],
        "modo_entrenamiento": "activo" if active_learning else "sintetico",
        "etiquetas_doradas": {
            "aceptaciones_utiles": len(etiquetas_golden),
            "ciclos_cerrados_utiles": len(ciclos_golden),
            "peso_muestra_real": W_GOLDEN,
        },
        "promovidas": promovidas,
        "resultados": [
            {k: v for k, v in r.items() if k not in ("modelo",)}
            for r in resultados
        ],
        "evaluacion_datos_reales": real_eval,
        "concordancia_media_datos_reales": concordancia_media,
    }
    for nombre, modelo in modelos_artefactos.items():
        joblib.dump(modelo, MODELS_DIR / f"{nombre}.joblib")
    (MODELS_DIR / "ml_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nArtefactos guardados en {MODELS_DIR}")

    # ── Registrar en BD ──
    if registrar:
        # Promoción por variable: PRODUCTION solo si la precisión real supera
        # el umbral de calidad (0.85); el resto queda honestamente en STAGING.
        promover_apt = r_apt.get("promovida_aptitud") or (
            concordancia_media is not None and concordancia_media >= UMBRAL_PROMOCION
        )
        await registrar_modelos(
            resultados,
            promovidas=set(promovidas),
            promover_aptitud=bool(promover_apt),
        )
    else:
        print("(Use --registrar para guardar métricas en modelos_ml/metricas_modelo)")


async def registrar_modelos(
    resultados: list[dict],
    promovidas: set[str] | None = None,
    promover_aptitud: bool = False,
) -> None:
    from agroia.database import async_session_factory

    from agroia_backend.models.metrica_modelo import MetricaModelo
    from agroia_backend.models.modelo_ml import ModeloML, StageModelo

    promovidas = promovidas or set()
    async with async_session_factory() as db:
        for r in resultados:
            if "f1" not in r:
                continue
            es_aptitud = r["nombre"] == "aptitud_upra"
            variable = r["nombre"].removeprefix("diagnostico_")
            promovida = (not es_aptitud) and variable in promovidas
            activo = promovida or (es_aptitud and promover_aptitud)
            nombre = (
                f"RF_{r['nombre']}_colombia_activo" if activo
                else f"RF_{r['nombre']}_colombia_sintetico"
            )
            modelo = ModeloML(
                nombre=nombre,
                tipo_modelo="RandomForest",
                descripcion=(
                    "Entrenado con datos simulados + etiquetas doradas "
                    "(aceptaciones humanas y ciclos cerrados) etiquetadas por "
                    "UPRA/Cenicafé/AGROSAVIA — aprendizaje activo."
                    if activo else
                    "Entrenado con datos simulados de suelos colombianos etiquetados "
                    "por el sistema experto UPRA/Cenicafé/AGROSAVIA (imputación por medianas)."
                ),
                version=1,
                f1_score=r["f1"],
                stage=StageModelo.PRODUCTION if activo else StageModelo.STAGING,
                activo=activo,
            )
            db.add(modelo)
            await db.flush()
            for metrica, valor in (
                ("accuracy", r.get("accuracy")),
                ("precision", r.get("precision")),
                ("recall", r.get("recall")),
                ("f1", r.get("f1")),
                ("cv_f1_mean", r.get("cv_f1_mean")),
                ("precision_real", r.get("precision_real")),
                ("f1_real", r.get("f1_real")),
                ("concordancia_golden", r.get("concordancia_golden")),
            ):
                if valor is not None:
                    db.add(MetricaModelo(
                        modelo_ml_id=modelo.id, metrica=metrica, valor=valor,
                    ))
        await db.commit()
    n_prom = len(promovidas) + (1 if promover_aptitud else 0)
    print(f"Modelos y métricas registrados en la BD: {n_prom} promovido(s) a "
          f"PRODUCTION, el resto en STAGING.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--registrar", action="store_true", help="registrar en modelos_ml")
    ap.add_argument(
        "--active-learning", action="store_true",
        help="combina datos sintéticos con etiquetas doradas (aceptaciones "
             "humanas + ciclos cerrados) y promueve variables con precisión "
             "real >= 0.85",
    )
    args = ap.parse_args()
    asyncio.run(main(registrar=args.registrar, active_learning=args.active_learning))
