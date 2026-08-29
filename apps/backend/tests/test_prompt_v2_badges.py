"""Reglas RQ-14/RQ-15 del prompt-sistema-agroia-v2 aplicadas a badges/reportes."""

from agroia_backend.services.reportes_html import (
    _UMBRAL_APROBACION_EXPERTOS,
    _badge_confianza_reducida,
    _badge_estado_final,
    _respaldo_html,
)


def test_respaldo_html_neutro_bajo_umbral():
    for n in (1, 2):
        html = _respaldo_html(n)
        assert "✅" not in html
        assert "en proceso de validación" in html


def test_respaldo_html_aprobacion_con_consenso():
    html = _respaldo_html(_UMBRAL_APROBACION_EXPERTOS)
    assert "✅" in html
    assert "Aprobación de expertos" in html


def test_respaldo_html_vacio_sin_respaldos():
    assert _respaldo_html(0) == ""


def test_badge_confianza_reducida():
    assert "CONFIANZA REDUCIDA" in _badge_confianza_reducida(0.57)
    assert _badge_confianza_reducida(0.90) == ""
    assert "CONFIANZA REDUCIDA" in _badge_confianza_reducida(None)


def test_badge_estado_final_nunca_apta_lisa_bajo_umbral():
    html = _badge_estado_final("Apta", "pendiente_validacion")
    assert "APTA" not in html
    assert "PENDIENTE DE VALIDACIÓN TÉCNICA" in html
