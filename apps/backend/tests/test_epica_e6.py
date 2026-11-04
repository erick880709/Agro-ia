"""Pruebas de la Épica E6: grados de evidencia y cobertura (TT-11, HU-08/09)."""

from agroia_backend.services.grados_evidencia import (
    GRADO_A,
    GRADO_B,
    GRADO_C,
    GRADO_D,
    cobertura_variables,
    grados_por_variable,
    grado_laboratorio,
    grado_sensor,
    laboratorio_vigente,
    puede_dosificar,
    recomendar_muestreo,
)


class TestLaboratorioVigente:
    def test_reciente(self):
        assert laboratorio_vigente("2026-11-01") is True

    def test_antiguo(self):
        assert laboratorio_vigente("2020-01-01") is False

    def test_none(self):
        assert laboratorio_vigente(None) is False


class TestGrados:
    def test_grado_laboratorio(self):
        assert grado_laboratorio("2026-11-01") == GRADO_A
        assert grado_laboratorio("2020-01-01") is None

    def test_grado_sensor(self):
        assert grado_sensor(calibrada=True, cumple_metas=True) == GRADO_B
        assert grado_sensor(calibrada=True, cumple_metas=False) == GRADO_C
        assert grado_sensor(calibrada=False) == GRADO_C

    def test_puede_dosificar(self):
        assert puede_dosificar(GRADO_A) is True
        assert puede_dosificar(GRADO_B) is True
        assert puede_dosificar(GRADO_A, GRADO_B) is True
        assert puede_dosificar(GRADO_A, GRADO_C) is False
        assert puede_dosificar(GRADO_D) is False


class TestGradosPorVariable:
    def test_laboratorio_tiene_prioridad(self):
        grados = grados_por_variable(
            soil_vars={"ph", "potasio"},
            lab_variables={"ph"},
            npk_calibrado=False,
        )
        assert grados["ph"]["grado"] == GRADO_A
        assert grados["potasio"]["grado"] == GRADO_C

    def test_sensor_calibrado_es_b(self):
        grados = grados_por_variable(
            soil_vars={"potasio"},
            npk_calibrado=True,
            npk_cumple_metas=True,
        )
        assert grados["potasio"]["grado"] == GRADO_B

    def test_sig_es_d(self):
        grados = grados_por_variable(
            soil_vars={"materia_organica"},
            estimaciones_sig=["materia_organica"],
        )
        assert grados["materia_organica"]["grado"] == GRADO_D

    def test_no_sensor_no_sig_es_modelo(self):
        grados = grados_por_variable(soil_vars={"calcio"})
        assert grados["calcio"]["grado"] == GRADO_D
        assert grados["calcio"]["fuente"] == "modelo"


class TestCobertura:
    def test_variables_no_medidas(self):
        cobertura = cobertura_variables(soil_vars={"ph", "potasio"})
        no_medidas = {v["variable"] for v in cobertura["variables_no_medidas"]}
        assert "materia_organica" in no_medidas
        assert "cic" in no_medidas
        assert "calcio" in no_medidas

    def test_laboratorio_cubre_la_variable(self):
        cobertura = cobertura_variables(
            soil_vars={"ph"},
            lab_variables={"materia_organica"},
        )
        mo = next(v for v in cobertura["variables_no_medidas"]
                  if v["variable"] == "materia_organica")
        assert mo["fuente"] == "laboratorio"

    def test_sig_cubre_la_variable(self):
        cobertura = cobertura_variables(
            soil_vars={"ph"},
            estimaciones_sig=["materia_organica"],
        )
        mo = next(v for v in cobertura["variables_no_medidas"]
                  if v["variable"] == "materia_organica")
        assert mo["fuente"] == "SIG (IGAC/UPRA)"


class TestRecomendarMuestreo:
    def test_recomienda_por_grado_c(self):
        r = recomendar_muestreo(grados={"potasio": {"grado": "C"}})
        assert r["recomienda_muestreo"] is True
        assert "potasio" in r["variables_prioritarias"]

    def test_recomienda_por_frontera(self):
        r = recomendar_muestreo(grados={}, hay_frontera=True)
        assert r["recomienda_muestreo"] is True
        assert r["motivo"] == "frontera"

    def test_no_recomienda_sin_motivo(self):
        r = recomendar_muestreo(grados={"ph": {"grado": "A"}})
        assert r["recomienda_muestreo"] is False
