"""Pruebas de la Épica E5: contexto agronómico y guía de campo."""

from datetime import datetime, timezone

from agroia_backend.services.contexto_agronomico import (
    REPLICAS_MINIMAS_POR_PUNTO,
    aplicar_contexto,
    dentro_ventana_contexto,
    guia_campo,
    profundidad_por_cultivo,
)


class TestDentroVentana:
    def test_fertilizacion_reciente(self):
        ts = datetime(2026, 11, 4, tzinfo=timezone.utc)
        assert dentro_ventana_contexto(ts, fecha_ultima_fertilizacion="2026-11-03") is True

    def test_fertilizacion_fuera_de_ventana(self):
        ts = datetime(2026, 11, 4, tzinfo=timezone.utc)
        assert dentro_ventana_contexto(ts, fecha_ultima_fertilizacion="2026-10-01") is False

    def test_riego_reciente(self):
        ts = datetime(2026, 11, 4, tzinfo=timezone.utc)
        assert dentro_ventana_contexto(ts, fecha_ultimo_riego="2026-11-04") is True

    def test_sin_contexto(self):
        ts = datetime(2026, 11, 4, tzinfo=timezone.utc)
        assert dentro_ventana_contexto(ts) is False


class TestAplicarContexto:
    def test_valida_se_degrada(self):
        estado, motivos = aplicar_contexto(
            estado="valida", motivos=[],
            ts=datetime(2026, 11, 4, tzinfo=timezone.utc),
            fecha_ultima_fertilizacion="2026-11-03",
        )
        assert estado == "valida_con_advertencia"
        assert "contexto_reciente" in motivos

    def test_no_valida_no_cambia(self):
        estado, _ = aplicar_contexto(
            estado="saturada", motivos=["ph_saturado"],
            ts=datetime(2026, 11, 4, tzinfo=timezone.utc),
            fecha_ultima_fertilizacion="2026-11-03",
        )
        assert estado == "saturada"

    def test_sin_contexto_mantiene_valida(self):
        estado, motivos = aplicar_contexto(
            estado="valida", motivos=[],
            ts=datetime(2026, 11, 4, tzinfo=timezone.utc),
        )
        assert estado == "valida"
        assert motivos == []

    def test_motivos_no_se_duplican(self):
        estado, motivos = aplicar_contexto(
            estado="valida", motivos=["contexto_reciente"],
            ts=datetime(2026, 11, 4, tzinfo=timezone.utc),
            fecha_ultima_fertilizacion="2026-11-03",
        )
        assert estado == "valida_con_advertencia"
        assert motivos.count("contexto_reciente") == 1


class TestGuiaCampo:
    def test_profundidad_por_cultivo(self):
        assert profundidad_por_cultivo("cafe") == 20
        assert profundidad_por_cultivo("frutales") == 40
        assert profundidad_por_cultivo("pastos") == 15

    def test_cultivo_desconocido_default(self):
        assert profundidad_por_cultivo("kiwi") == 20

    def test_guia_estructura(self):
        guia = guia_campo("cafe")
        assert guia["replicas_minimas_por_punto"] == REPLICAS_MINIMAS_POR_PUNTO
        assert guia["profundidad_recomendada_cm"] == 20
        assert guia["cultivo"] == "cafe"
        assert "instalacion_enterrada" in guia
