"""Pruebas de la Épica E7: presentación de reportes, salud y parámetros."""

from agroia_backend.services.parametros_calidad import (
    aplicar_parametros_umbrales,
    parametros_por_defecto,
)
from agroia_backend.services.presentacion_reportes import (
    insignia_calidad,
    insignia_grado,
    resumen_una_linea,
    serie_con_incertidumbre,
)
from agroia_backend.services.salud_sensores import calcular_salud


class TestInsignias:
    def test_insignia_grado(self):
        assert insignia_grado("A")["etiqueta"] == "Laboratorio"
        assert insignia_grado("C")["color"] == "amarillo"
        assert insignia_grado(None) is None
        assert insignia_grado("Z") is None

    def test_insignia_calidad(self):
        assert insignia_calidad("valida")["icono"] == "✅"
        assert insignia_calidad("saturada")["color"] == "rojo"
        assert insignia_calidad(None)["etiqueta"] == "Previa a la regla de calidad"


class TestResumenUnaLinea:
    def test_confiable(self):
        r = resumen_una_linea({"ph": {"grado": "A"}})
        assert r["resumen"] == "confiable"

    def test_indicativo(self):
        r = resumen_una_linea({"potasio": {"grado": "C"}})
        assert r["resumen"] == "indicativo"

    def test_sin_datos(self):
        r = resumen_una_linea({})
        assert r["resumen"] == "sin datos"

    def test_excluida_gana(self):
        r = resumen_una_linea({"ph": {"grado": "A"}}, ["saturada"])
        assert r["resumen"] == "sin datos confiables"


class TestSerieConIncertidumbre:
    def test_banda_y_excluidos(self):
        lecturas = [
            {"ts": "2026-11-04T10:00:00Z", "valor": 6.5, "incertidumbre": 0.17,
             "calidad": "valida"},
            {"ts": "2026-11-04T11:00:00Z", "valor": 9.0, "incertidumbre": 0.17,
             "calidad": "saturada"},
        ]
        serie = serie_con_incertidumbre(lecturas)
        assert serie["banda_incertidumbre"] is True
        assert serie["puntos"][0]["excluida"] is False
        assert serie["puntos"][1]["excluida"] is True

    def test_eventos_pasados(self):
        serie = serie_con_incertidumbre([], [{"tipo": "riego", "fecha": "2026-11-03"}])
        assert serie["eventos"][0]["tipo"] == "riego"


class TestSaludSensores:
    def test_saludable(self):
        s = calcular_salud(
            ultima_lectura="2026-11-04T10:00:00Z",
            total_lecturas=100, lecturas_validas=95,
            sesgo_calibracion=0.1, meta_sesgo=0.3,
        )
        assert s["estado_salud"] == "saludable"
        assert s["tasa_lecturas_validas"] == 0.95

    def test_baja_calidad(self):
        s = calcular_salud(
            ultima_lectura="2026-11-04T10:00:00Z",
            total_lecturas=100, lecturas_validas=50,
        )
        assert s["estado_salud"] == "baja_calidad"

    def test_deriva(self):
        s = calcular_salud(
            ultima_lectura="2026-11-04T10:00:00Z",
            total_lecturas=100, lecturas_validas=95,
            sesgo_calibracion=0.5, meta_sesgo=0.3,
        )
        assert s["estado_salud"] == "deriva"
        assert s["deriva"]["supera_meta"] is True

    def test_sin_datos(self):
        s = calcular_salud(ultima_lectura=None, total_lecturas=0, lecturas_validas=0)
        assert s["estado_salud"] == "sin_datos"


class TestParametrosCalidad:
    def test_por_defecto(self):
        params = parametros_por_defecto()
        assert params["ph_min"]["valor"] == 3.0
        assert params["ce_max_dsm"]["valor"] == 10.0

    def test_aplicar_override(self):
        umbrales = aplicar_parametros_umbrales({"ph_min": 3.5})
        assert umbrales["ph_min"] == 3.5
        assert umbrales["ph_max"] == 9.0  # sin tocar

    def test_override_clave_desconocida_ignorada(self):
        umbrales = aplicar_parametros_umbrales({"no_existe": 99.0})
        assert "no_existe" not in umbrales
