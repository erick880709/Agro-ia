"""Pruebas de la Épica E8: ciclo de vida del sensor (HU-14, TT-12, TT-13)."""

from datetime import datetime, timezone

from agroia_backend.services.ciclo_vida_sensor import (
    detectar_deriva,
    proximo_mantenimiento,
    telemetria_salud,
)


class TestDetectarDeriva:
    def test_sesgo_supera_meta(self):
        r = detectar_deriva(0.5, 0.3)
        assert r["deriva"] is True
        assert r["motivo"] == "sesgo_supera_meta"

    def test_sesgo_dentro_de_meta(self):
        r = detectar_deriva(0.2, 0.3)
        assert r["deriva"] is False

    def test_sin_datos(self):
        r = detectar_deriva(None, 0.3)
        assert r["deriva"] is False
        assert r["sesgo"] is None


class TestTelemetriaSalud:
    def test_ok(self):
        r = telemetria_salud(
            voltaje_alimentacion=12.0, errores_crc=0,
            ultima_transmision="2026-11-04T06:00:00Z",
            ahora=datetime(2026, 11, 4, 7, 0, tzinfo=timezone.utc),
        )
        assert r["estado"] == "ok"
        assert r["voltaje_ok"] is True
        assert r["horas_sin_reportar"] == 1.0

    def test_voltaje_fuera_de_rango(self):
        r = telemetria_salud(
            voltaje_alimentacion=8.0, errores_crc=0, ultima_transmision=None
        )
        assert "voltaje_fuera_de_rango" in r["alertas"]

    def test_errores_crc(self):
        r = telemetria_salud(
            voltaje_alimentacion=12.0, errores_crc=5, ultima_transmision=None
        )
        assert "errores_crc" in r["alertas"]

    def test_tiempo_sin_reportar(self):
        r = telemetria_salud(
            voltaje_alimentacion=12.0, errores_crc=0,
            ultima_transmision="2026-11-02T06:00:00Z",
            ahora=datetime(2026, 11, 4, 7, 0, tzinfo=timezone.utc),
        )
        assert "tiempo_sin_reportar" in r["alertas"]
        assert r["horas_sin_reportar"] == 49.0


class TestProximoMantenimiento:
    def test_vencido(self):
        from datetime import date, timedelta
        hace_un_ano = date.today() - timedelta(days=400)
        r = proximo_mantenimiento(hace_un_ano)
        assert r["vencido"] is True

    def test_sin_mantenimiento(self):
        r = proximo_mantenimiento(None)
        assert r["proximo_mantenimiento"] is None
        assert r["vencido"] is False
