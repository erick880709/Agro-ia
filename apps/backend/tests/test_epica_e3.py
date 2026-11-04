"""Pruebas de la Épica E3: incertidumbre, banda de frontera y agregación."""

from math import sqrt

from agroia_backend.services.agregacion_robusta import (
    MINIMO_PUNTOS_MAPA,
    agregar_lote,
    agregar_punto,
    mediana_robusta,
    puede_generar_mapa,
)
from agroia_backend.services.banda_frontera import (
    CLASE_CUMPLE,
    CLASE_FRONTERA,
    CLASE_NO_CUMPLE,
    clasificar_frente_a_umbral,
    combinar_umbrales,
)
from agroia_backend.services.incertidumbre import (
    exactitud,
    formatear_valor,
    incertidumbre_estandar,
    incertidumbres_lectura,
)


# ───────────────────────── TT-06 · Incertidumbre ─────────────────────────

class TestExactitud:
    def test_ph(self):
        assert exactitud("ph") == 0.3

    def test_npk_40(self):
        assert exactitud("nitrogeno") == 40.0
        assert exactitud("fosforo") == 40.0
        assert exactitud("potasio") == 40.0

    def test_humedad_por_tramo(self):
        assert exactitud("humedad", 30.0) == 3.0
        assert exactitud("humedad", 53.0) == 3.0
        assert exactitud("humedad", 60.0) == 5.0

    def test_ce_sin_exactitud_declarada(self):
        assert exactitud("conductividad_electrica") is None

    def test_variable_desconocida(self):
        assert exactitud("calcio") is None


class TestIncertidumbreEstandar:
    def test_ph_rectangular(self):
        assert incertidumbre_estandar("ph") == round(0.3 / sqrt(3), 4)

    def test_npk_rectangular(self):
        assert incertidumbre_estandar("nitrogeno") == round(40.0 / sqrt(3), 4)

    def test_ce_sin_incertidumbre(self):
        assert incertidumbre_estandar("conductividad_electrica") is None

    def test_lectura_mapea_solo_variables_medidas(self):
        payload = {
            "ph": 6.5,
            "humedad": 30.0,
            "nitrogeno": 10.0,
            "textura": "Arcilla",          # no numérica: se ignora
            "valor_crudo": {"0x0006": 650},
        }
        resultado = incertidumbres_lectura(payload)
        assert set(resultado) == {"ph", "humedad", "nitrogeno"}
        assert resultado["ph"] == round(0.3 / sqrt(3), 4)


class TestFormatearValor:
    def test_ph_redondeo_a_decima(self):
        f = formatear_valor("ph", 5.42)
        assert f["redondeado"] == 5.4
        assert f["incertidumbre"] == round(0.3 / sqrt(3), 4)

    def test_npk_redondeo_a_decenas(self):
        f = formatear_valor("nitrogeno", 134.0)
        assert f["redondeado"] == 130.0

    def test_ce_sin_incertidumbre(self):
        f = formatear_valor("conductividad_electrica", 0.426)
        assert f["redondeado"] == 0.43
        assert f["incertidumbre"] is None


# ───────────────────────── TT-07 · Banda de frontera ─────────────────────────

class TestClasificarFrenteAUmbral:
    def test_frontera_ph_ejemplo_rfp(self):
        # RF-012: pH 5,4 contra umbral 5,5 (exactitud ±0,3)
        r = clasificar_frente_a_umbral(5.4, 5.5, exactitud_var=0.3, direccion="max")
        assert r["clase"] == CLASE_FRONTERA
        assert r["probabilidad_cumple"] == round(0.4 / 0.6, 4)  # 0.6667

    def test_cumple_claro(self):
        r = clasificar_frente_a_umbral(5.0, 5.5, exactitud_var=0.3, direccion="max")
        assert r["clase"] == CLASE_CUMPLE
        assert r["probabilidad_cumple"] == 1.0

    def test_no_cumple_claro(self):
        r = clasificar_frente_a_umbral(6.0, 5.5, exactitud_var=0.3, direccion="max")
        assert r["clase"] == CLASE_NO_CUMPLE
        assert r["probabilidad_cumple"] == 0.0

    def test_direccion_min(self):
        # valor 5,2 contra umbral mínimo 5,0 (debe ser ≥ 5,0)
        r = clasificar_frente_a_umbral(5.2, 5.0, exactitud_var=0.3, direccion="min")
        assert r["clase"] == CLASE_FRONTERA
        assert r["probabilidad_cumple"] == round(0.5 / 0.6, 4)  # 0.8333

    def test_sin_exactitud_determinista(self):
        r = clasificar_frente_a_umbral(6.0, 5.5, exactitud_var=None, direccion="max")
        assert r["clase"] == CLASE_NO_CUMPLE

    def test_valor_o_umbral_none(self):
        r = clasificar_frente_a_umbral(None, 5.5, exactitud_var=0.3, direccion="max")
        assert r["clase"] is None


class TestCombinarUmbrales:
    def test_todos_cumplen(self):
        r = combinar_umbrales([
            {"clase": CLASE_CUMPLE, "probabilidad_cumple": 1.0, "margen": -0.2},
            {"clase": CLASE_CUMPLE, "probabilidad_cumple": 1.0, "margen": -0.5},
        ])
        assert r["clase"] == CLASE_CUMPLE

    def test_alguno_no_cumple(self):
        r = combinar_umbrales([
            {"clase": CLASE_CUMPLE, "probabilidad_cumple": 1.0, "margen": None},
            {"clase": CLASE_NO_CUMPLE, "probabilidad_cumple": 0.0, "margen": None},
        ])
        assert r["clase"] == CLASE_NO_CUMPLE

    def test_frontera_probabilidad_conjunta(self):
        r = combinar_umbrales([
            {"clase": CLASE_CUMPLE, "probabilidad_cumple": 1.0, "margen": None},
            {"clase": CLASE_FRONTERA, "probabilidad_cumple": 0.8, "margen": None},
        ])
        assert r["clase"] == CLASE_FRONTERA
        assert r["probabilidad_cumple"] == round(0.8, 4)


# ───────────────────────── TT-07 · Agregación robusta ─────────────────────────

class TestAgregacion:
    def test_mediana_robusta(self):
        assert mediana_robusta([1.0, 2.0, 100.0]) == 2.0

    def test_mediana_con_nulos(self):
        assert mediana_robusta([None, 3.0, 1.0, None]) == 2.0

    def test_agregar_punto(self):
        r = agregar_punto([7.1, 7.2, 7.3])
        assert r["mediana"] == 7.2
        assert r["replicas"] == 3

    def test_agregar_lote(self):
        r = agregar_lote([6.5, 6.8, 7.0, 7.4])
        assert r["mediana"] == 6.9
        assert r["n_puntos"] == 4
        assert r["iqr"] is not None and r["iqr"] > 0

    def test_minimo_puntos_mapa(self):
        assert MINIMO_PUNTOS_MAPA == 3
        assert puede_generar_mapa(2) is False
        assert puede_generar_mapa(3) is True
