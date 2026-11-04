"""Pruebas de la Épica E9: aprendizaje automático con etiquetas de laboratorio."""

from agroia_backend.services.ml_entrenamiento import (
    cumple_meta,
    evaluar_variable,
    modo_sombra,
    reporte_rendimiento,
    validar_sin_circularidad,
)


class TestCumpleMeta:
    def test_ph_cumple(self):
        assert cumple_meta("ph", {"sesgo": 0.2, "rmse": 0.3}) is True

    def test_ph_no_cumple_por_rmse(self):
        assert cumple_meta("ph", {"sesgo": 0.2, "rmse": 0.5}) is False

    def test_ce_cumple_r2(self):
        assert cumple_meta("conductividad_electrica", {"r2": 0.85}) is True

    def test_npk_no_cumple_r2(self):
        assert cumple_meta("nitrogeno", {"r2": 0.4}) is False

    def test_sin_metricas(self):
        assert cumple_meta("ph", None) is False


class TestEvaluarVariable:
    def test_regresion_exacta(self):
        # y = 2x + 1
        m = evaluar_variable([1, 2, 3], [3, 5, 7])
        assert m["r2"] == 1.0
        assert m["rmse"] == 0.0
        assert m["n"] == 3

    def test_insuficientes(self):
        assert evaluar_variable([1], [2]) is None


class TestReporteRendimiento:
    def test_por_variable_y_unidad(self):
        pares = [
            {"variable": "ph", "unidad_suelo": "andisol",
             "valor_sensor": 6.0, "valor_laboratorio": 6.2},
            {"variable": "ph", "unidad_suelo": "andisol",
             "valor_sensor": 6.5, "valor_laboratorio": 6.7},
            {"variable": "ph", "unidad_suelo": "oxisol",
             "valor_sensor": 5.0, "valor_laboratorio": 5.1},
            {"variable": "ph", "unidad_suelo": "oxisol",
             "valor_sensor": 5.5, "valor_laboratorio": 5.6},
        ]
        reporte = reporte_rendimiento(pares)
        filas = reporte["por_variable"]
        assert len(filas) == 2  # andisol + oxisol
        for f in filas:
            assert f["variable"] == "ph"
            assert f["cumple_meta"] is True  # pendiente 1, intercepto ~0.2
            assert f["grado"] == "C"  # n=2 < 30 → aún en sombra

    def test_modo_sombra(self):
        pares = [
            {"variable": "nitrogeno", "unidad_suelo": None,
             "valor_sensor": 1.0, "valor_laboratorio": 3.0},
            {"variable": "nitrogeno", "unidad_suelo": None,
             "valor_sensor": 2.0, "valor_laboratorio": 5.0},
        ]
        reporte = reporte_rendimiento(pares)
        assert modo_sombra(reporte) is True


class TestSinCircularidad:
    def test_solo_laboratorio(self):
        assert validar_sin_circularidad("laboratorio") is True
        assert validar_sin_circularidad("reglas") is False
        assert validar_sin_circularidad("sensor") is False
