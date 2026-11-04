"""Pruebas del motor de calidad del dato (Épica E2: TT-04/TT-05, HU-02)."""

from agroia_backend.services.motor_calidad import (
    CALIDAD_BAJO_LIMITE,
    CALIDAD_ESTIMADO_SIG,
    CALIDAD_FUERA_RANGO,
    CALIDAD_HUMEDAD_INSUFICIENTE,
    CALIDAD_INVALIDADA,
    CALIDAD_NO_CALIBRADA,
    CALIDAD_SATURADA,
    CALIDAD_SONDA_FUERA,
    CALIDAD_VALIDA,
    CALIDAD_VALIDA_CON_ADVERTENCIA,
    clasificar_lectura,
    es_lectura_valida_para_analisis,
    resumir_calidad,
)


class TestEstadosBasicos:
    def test_valida_sin_npk(self):
        estado, motivos = clasificar_lectura(
            ph=6.5, conductividad_electrica=0.5, humedad=30.0
        )
        assert estado == CALIDAD_VALIDA
        assert motivos == []

    def test_valida_con_npk_calibrado(self):
        estado, motivos = clasificar_lectura(
            ph=6.5, conductividad_electrica=0.5, humedad=30.0,
            nitrogeno=10.0, fosforo=5.0, potasio=20.0, npk_calibrado=True,
        )
        assert estado == CALIDAD_VALIDA

    def test_no_calibrada_por_npk_sin_calibrar(self):
        estado, motivos = clasificar_lectura(
            ph=6.5, conductividad_electrica=0.5, humedad=30.0,
            nitrogeno=10.0, fosforo=5.0, potasio=20.0, npk_calibrado=False,
        )
        assert estado == CALIDAD_NO_CALIBRADA
        assert "npk_sin_calibrar" in motivos


class TestSaturacionSimetrica:
    def test_ph_superior_saturado(self):
        estado, motivos = clasificar_lectura(ph=9.0)
        assert estado == CALIDAD_SATURADA
        assert "ph_saturado" in motivos

    def test_ph_inferior_saturado(self):
        estado, _ = clasificar_lectura(ph=3.0)
        assert estado == CALIDAD_SATURADA

    def test_ce_saturada(self):
        estado, motivos = clasificar_lectura(conductividad_electrica=10.0)
        assert estado == CALIDAD_SATURADA
        assert "ce_saturada" in motivos

    def test_npk_saturado(self):
        estado, motivos = clasificar_lectura(potasio=2000.0)
        assert estado == CALIDAD_SATURADA
        assert "potasio_saturado" in motivos

    def test_saturacion_gana_a_bajo_limite(self):
        # pH 9,0 (saturada) + CE 0 (bajo límite) → saturada (más severa)
        estado, _ = clasificar_lectura(ph=9.0, conductividad_electrica=0.0)
        assert estado == CALIDAD_SATURADA


class TestBajoLimiteDeteccion:
    def test_ce_cero_se_conserva(self):
        estado, motivos = clasificar_lectura(ph=6.5, conductividad_electrica=0.0)
        assert estado == CALIDAD_BAJO_LIMITE
        assert "ce_bajo_limite" in motivos
        assert es_lectura_valida_para_analisis(estado) is True  # no se descarta

    def test_npk_cero_se_conserva(self):
        estado, motivos = clasificar_lectura(ph=6.5, nitrogeno=0.0)
        assert estado == CALIDAD_BAJO_LIMITE
        assert "nitrogeno_bajo_limite" in motivos


class TestContextoMedicion:
    def test_sonda_fuera_de_suelo(self):
        estado, motivos = clasificar_lectura(
            humedad=0.0, conductividad_electrica=0.0
        )
        assert estado == CALIDAD_SONDA_FUERA
        assert "sonda_fuera_de_suelo" in motivos

    def test_humedad_insuficiente(self):
        estado, motivos = clasificar_lectura(ph=6.5, humedad=5.0)
        assert estado == CALIDAD_HUMEDAD_INSUFICIENTE
        assert "humedad_insuficiente" in motivos

    def test_temperatura_fuera_de_rango(self):
        estado, motivos = clasificar_lectura(temperatura_suelo=-50.0)
        assert estado == CALIDAD_FUERA_RANGO
        assert "temperatura_fuera_rango" in motivos

    def test_temperatura_sol_directo_advertencia(self):
        estado, motivos = clasificar_lectura(
            ph=6.5, conductividad_electrica=0.5, humedad=30.0,
            temperatura_suelo=46.0,
        )
        assert estado == CALIDAD_VALIDA_CON_ADVERTENCIA
        assert "temperatura_sol_directo" in motivos


class TestCoordenadaYFuente:
    def test_coordenada_defecto_invalidada(self):
        estado, motivos = clasificar_lectura(
            ph=6.5, pos_x=-1698.64, pos_y=6614.3
        )
        assert estado == CALIDAD_INVALIDADA
        assert "coordenada_defecto" in motivos

    def test_fuente_sig(self):
        estado, motivos = clasificar_lectura(ph=6.5, fuente_sig=True)
        assert estado == CALIDAD_ESTIMADO_SIG
        assert "origen_sig" in motivos


class TestValidezParaAnalisis:
    def test_valida_es_analizable(self):
        assert es_lectura_valida_para_analisis("valida") is True
        assert es_lectura_valida_para_analisis("no_calibrada") is True
        assert es_lectura_valida_para_analisis("bajo_limite_deteccion") is True

    def test_invalidas_no_analizables(self):
        for estado in ("saturada", "fuera_de_rango", "sonda_fuera_de_suelo",
                       "humedad_insuficiente", "invalidada", "estimado_sig"):
            assert es_lectura_valida_para_analisis(estado) is False, estado

    def test_none_es_analizable(self):
        # lecturas previas a la regla de calidad
        assert es_lectura_valida_para_analisis(None) is True


class TestResumenTransparencia:
    def _lectura(self, estado, motivos):
        return {"id": estado, "calidad": estado, "motivos_calidad": motivos}

    def test_n_de_m_validas(self):
        lecturas = [
            self._lectura("valida", []),
            self._lectura("valida", []),
            self._lectura("no_calibrada", ["npk_sin_calibrar"]),
            self._lectura("saturada", ["ph_saturado"]),
            self._lectura("saturada", ["ph_saturado"]),
        ]
        resumen = resumir_calidad(lecturas)
        assert resumen["total"] == 5
        assert resumen["validas"] == 3
        assert resumen["excluidas"] == 2
        assert resumen["por_estado"]["saturada"] == 2
        assert resumen["por_motivo"]["ph_saturado"] == 2
