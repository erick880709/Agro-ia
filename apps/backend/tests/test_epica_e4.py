"""Pruebas de la Épica E4: calibración local y equivalencia (TT-08/09/10)."""

from agroia_backend.services.calibracion import (
    aplicar_calibracion_lineal,
    calibracion_vigente,
    equivalente_laboratorio,
    humedad_aplicable,
    regresion_lineal,
)


class TestRegresionLineal:
    def test_recta_exacta(self):
        # y = 2x + 1: pendiente 2, intercepto 1, R² = 1, RMSE 0, sesgo 0
        reg = regresion_lineal([1, 2, 3], [3, 5, 7])
        assert reg["pendiente"] == 2.0
        assert reg["intercepto"] == 1.0
        assert reg["n"] == 3
        assert reg["r2"] == 1.0
        assert reg["rmse"] == 0.0
        assert reg["sesgo"] == 0.0

    def test_insuficientes_puntos(self):
        assert regresion_lineal([1], [2]) is None
        assert regresion_lineal([], []) is None

    def test_varianza_cero_en_x(self):
        assert regresion_lineal([5, 5, 5], [1, 2, 3]) is None

    def test_ignora_puntos_con_none(self):
        reg = regresion_lineal([1, None, 3], [3, 999, 7])
        assert reg["n"] == 2
        assert reg["pendiente"] == 2.0


class TestEquivalenciaLaboratorio:
    def test_aplicar_lineal(self):
        assert aplicar_calibracion_lineal(10.0, 2.0, 1.0) == 21.0

    def test_calibracion_vigente(self):
        calibraciones = [
            {"variable": "potasio", "activa": True, "vigencia": None,
             "created_at": None, "pendiente": 1.5, "intercepto": 0.0},
            {"variable": "potasio", "activa": True, "vigencia": None,
             "created_at": None, "pendiente": 2.0, "intercepto": 0.0},
        ]
        cal = calibracion_vigente(
            [c for c in calibraciones if c["variable"] == "potasio"]
        )
        # Empate: max por created_at conserva el primero
        assert cal["pendiente"] == 1.5

    def test_sin_calibracion_grado_c(self):
        r = equivalente_laboratorio("potasio", 60.0, [])
        assert r["grado"] == "C"
        assert r["valor_laboratorio"] is None

    def test_con_calibracion_grado_b(self):
        calibraciones = [
            {"variable": "potasio", "activa": True, "vigencia": None,
             "created_at": None, "pendiente": 2.0, "intercepto": 0.0,
             "n": 30, "r2": 0.7, "rmse": 10.0, "sesgo": 1.0},
        ]
        r = equivalente_laboratorio("potasio", 60.0, calibraciones)
        assert r["grado"] == "B"
        assert r["valor_laboratorio"] == 120.0
        assert r["calibracion"]["r2"] == 0.7

    def test_valor_none(self):
        r = equivalente_laboratorio("potasio", None, [])
        assert r["valor_sensor"] is None
        assert r["grado"] == "C"


class TestHumedadAplicable:
    def test_suelo_normal_aplicable(self):
        assert humedad_aplicable("Franco-arcillosa", 1.0) is True

    def test_arenoso_no_aplicable(self):
        assert humedad_aplicable("arenoso", 1.0) is False

    def test_salino_no_aplicable(self):
        assert humedad_aplicable("Franca", 5.5) is False

    def test_sin_textura_aplicable(self):
        assert humedad_aplicable(None, 1.0) is True
