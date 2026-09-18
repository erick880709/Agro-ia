"""Pruebas del motor de cálculo AGC-COST (F1) — casos de aceptación CA-01 a CA-09.

RFP §15: con la semilla (base $100.000; tramos 1–15/$15.000, 16–30/$10.000,
31+/$7.000; dificultad 0/15/30%; sin margen/descuento/redondeo) el motor debe
producir exactamente los totales de la tabla. Tolerancia cero.
"""

from datetime import date
from decimal import Decimal

import pytest

from agroia_backend.services.costeo_motor import (
    CosteoError,
    aplicar_redondeo,
    calcular,
    calcular_escalonado,
    validar_tramos,
)

# ── Fixtures: espejo del conjunto semilla (scripts/seed_costeo.py) ──


def _tramos_escalonados() -> list[dict]:
    return [
        {"desde": "1", "hasta": "15", "valor": "15000", "modo": "marginal"},
        {"desde": "16", "hasta": "30", "valor": "10000", "modo": "marginal"},
        {"desde": "31", "hasta": None, "valor": "7000", "modo": "marginal"},
    ]


def _conjunto_semilla(
    base: str = "100000",
    tramos: list[dict] | None = None,
    dificultades: dict | None = None,
    politica: dict | None = None,
    descuentos: list[dict] | None = None,
) -> dict:
    return {
        "id": "conj-semilla",
        "nombre": "Estudio de tarifas — semilla",
        "version": 1,
        "estado": "publicado",
        "vigencia_desde": "2026-01-01",
        "vigencia_hasta": None,
        "moneda": "COP",
        "politica": politica or {
            "margen_objetivo": "0",
            "margen_minimo": "0",
            "piso_visita": "0",
            "vigencia_cotizacion_dias": 30,
            "redondeo_multiplo": "1",
            "redondeo_modo": "ninguno",
        },
        "servicios": [{
            "codigo": "muestreo_en_grilla",
            "nombre": "Muestreo de suelos en grilla",
            "unidad": "punto",
            "componentes": [
                {
                    "id": "c-base", "codigo": "tarifa_base", "nombre": "Tarifa base",
                    "tipo": "fijo", "orden": 1, "afectable_por_factores": True,
                    "config": {"valor": base},
                },
                {
                    "id": "c-puntos", "codigo": "puntos_muestreo", "nombre": "Puntos",
                    "tipo": "escalonado", "orden": 2, "afectable_por_factores": True,
                    "config": {}, "tramos": tramos if tramos is not None else _tramos_escalonados(),
                },
            ],
        }],
        "factores": [{
            "codigo": "dificultad",
            "nombre": "Dificultad del terreno",
            "aplicacion": "porcentual",
            "combinacion": "suma",
            "opciones": [
                {"codigo": "plano", "etiqueta": "Plano", "porcentaje": dificultades.get("plano", "0") if dificultades else "0"},
                {"codigo": "pendiente_moderada", "etiqueta": "Pendiente moderada",
                 "porcentaje": dificultades.get("pendiente_moderada", "15") if dificultades else "15"},
                {"codigo": "acceso_dificil", "etiqueta": "Acceso difícil",
                 "porcentaje": dificultades.get("acceso_dificil", "30") if dificultades else "30"},
            ],
        }],
        "impuestos": [{
            "codigo": "IVA", "nombre": "IVA", "porcentaje": "19",
            "base": "subtotal", "informativo": True,
        }],
        "descuentos": descuentos or [],
    }


def _contexto(area: str, puntos: int, dificultad: str | None = None, rol: str = "admin") -> dict:
    return {
        "fecha_referencia": date(2026, 9, 18),
        "area_ha": Decimal(area),
        "puntos": puntos,
        "km": Decimal("0"),
        "rol": rol,
        "departamento": "Quindío",
        "municipio": "Armenia",
    }


def _calcular(area: str, puntos: int, dificultad: str | None = None, **kwargs) -> dict:
    seleccion = {
        "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": Decimal(str(puntos))}],
        "factores": {"dificultad": dificultad} if dificultad else {},
        "descuento_pct": kwargs.get("descuento_pct"),
    }
    return calcular(_contexto(area, puntos, dificultad, kwargs.get("rol", "admin")),
                    kwargs.get("conjunto", _conjunto_semilla()), seleccion)


# ── Casos de aceptación CA-01 a CA-04 ──


@pytest.mark.parametrize("area,puntos,dificultad,total,costo_punto,costo_ha", [
    ("1", 10, "plano", "250000", "25000", "250000"),
    ("5", 8, "pendiente_moderada", "253000", "31625", "50600"),
    ("20", 20, "acceso_dificil", "487500", "24375", "24375"),
    ("50", 35, "plano", "510000", "14571", "10200"),
])
def test_casos_aceptacion_motor(area, puntos, dificultad, total, costo_punto, costo_ha):
    resultado = _calcular(area, puntos, dificultad)
    assert resultado["total_final"] == Decimal(total)
    assert resultado["indicadores"]["costo_por_punto"] == Decimal(costo_punto)
    assert resultado["indicadores"]["costo_por_ha"] == Decimal(costo_ha)


def test_ca01_desglose_linea_por_linea():
    resultado = _calcular("1", 10, "plano")
    lineas = {
        (ln["servicio_codigo"], ln["componente_codigo"]): ln
        for ln in resultado["lineas"]
    }
    assert lineas[("muestreo_en_grilla", "tarifa_base")]["valor"] == Decimal("100000")
    assert lineas[("muestreo_en_grilla", "puntos_muestreo")]["valor"] == Decimal("150000")
    assert resultado["subtotal_directo"] == Decimal("250000")
    assert resultado["subtotal_ajustado"] == Decimal("250000")
    # El IVA semilla es informativo: no suma al total.
    assert resultado["total_final"] == Decimal("250000")
    assert resultado["impuestos_informativos"][0]["valor"] == Decimal("47500.0000")
    assert resultado["impuestos_incluidos"] == []
    assert resultado["traza"]


# ── CA-05: cambiar tarifa base sin desplegar código ──

def test_ca05_cambio_tarifa_base():
    resultado = _calcular("1", 10, "plano", conjunto=_conjunto_semilla(base="120000"))
    assert resultado["total_final"] == Decimal("270000")


# ── CA-06: agregar un cuarto tramo ──

def test_ca06_cuarto_tramo():
    # El tercer tramo se cierra en 50 y el nuevo (51+) entra con $5.000.
    tramos = [
        {"desde": "1", "hasta": "15", "valor": "15000", "modo": "marginal"},
        {"desde": "16", "hasta": "30", "valor": "10000", "modo": "marginal"},
        {"desde": "31", "hasta": "50", "valor": "7000", "modo": "marginal"},
        {"desde": "51", "hasta": None, "valor": "5000", "modo": "marginal"},
    ]
    # 60 puntos: 15×15000 + 15×10000 + 20×7000 + 10×5000 = 565.000 + base 100.000
    resultado = _calcular("60", 60, None, conjunto=_conjunto_semilla(tramos=tramos))
    assert resultado["total_final"] == Decimal("665000")


# ── CA-07: determinismo / snapshot reproducible ──

def test_ca07_determinismo():
    primero = _calcular("20", 20, "acceso_dificil")
    segundo = _calcular("20", 20, "acceso_dificil")
    assert primero["total_final"] == segundo["total_final"] == Decimal("487500")
    assert primero["lineas"] == segundo["lineas"]
    assert primero["traza"] == segundo["traza"]


# ── CA-08: tramos inconsistentes ──

def test_ca08_rechaza_traslape_tramos():
    tramos = [
        {"desde": "1", "hasta": "15", "valor": "15000", "modo": "marginal"},
        {"desde": "14", "hasta": "30", "valor": "10000", "modo": "marginal"},
    ]
    with pytest.raises(CosteoError) as exc:
        _calcular("20", 20, None, conjunto=_conjunto_semilla(tramos=tramos))
    assert exc.value.code == "TRAMOS_INCONSISTENTES"
    assert "Traslape" in exc.value.message


def test_ca08_rechaza_hueco_tramos():
    tramos = [
        {"desde": "1", "hasta": "15", "valor": "15000", "modo": "marginal"},
        {"desde": "17", "hasta": None, "valor": "10000", "modo": "marginal"},
    ]
    with pytest.raises(CosteoError) as exc:
        validar_tramos(tramos)
    assert exc.value.code == "TRAMOS_INCONSISTENTES"
    assert "Hueco" in exc.value.message


# ── CA-09: descuento por encima del tope del rol ──

def test_ca09_descuento_excede_tope_agronomo():
    conjunto = _conjunto_semilla(descuentos=[{
        "codigo": "manual",
        "criterio": "manual",
        "porcentaje": "10",
        "tope_rol": {"agronomo": 5, "admin": None},
    }])
    with pytest.raises(CosteoError) as exc:
        _calcular("1", 10, "plano", conjunto=conjunto, descuento_pct=Decimal("10"), rol="agronomo")
    assert exc.value.code == "DESCUENTO_EXCEDE_TOPE"

    # El admin sin tope sí puede.
    resultado = _calcular("1", 10, "plano", conjunto=conjunto,
                          descuento_pct=Decimal("10"), rol="admin")
    assert resultado["descuento_aplicado"] == Decimal("25000.0000")
    assert resultado["total_final"] == Decimal("225000.0000")


# ── Precisión monetaria y redondeo único ──

def test_aritmetica_decimal_sin_flotante():
    resultado = _calcular("5", 8, "pendiente_moderada")
    for linea in resultado["lineas"]:
        assert isinstance(linea["valor"], Decimal)
    assert resultado["total_final"] == Decimal("253000")


def test_redondeo_unico_parametrizado():
    politica = {
        "margen_objetivo": "0",
        "margen_minimo": "0",
        "piso_visita": "0",
        "vigencia_cotizacion_dias": 30,
        "redondeo_multiplo": "1000",
        "redondeo_modo": "mitad_superior",
    }
    # 205.000 directo × 1.15 = 235.750 → redondeo a múltiplo de 1.000 → 236.000
    resultado = _calcular("5", 7, "pendiente_moderada", conjunto=_conjunto_semilla(politica=politica))
    assert resultado["total_sin_redondeo"] == Decimal("235750.0000")
    assert resultado["ajuste_redondeo"] == Decimal("250.0000")
    assert resultado["total_final"] == Decimal("236000.0000")
    assert aplicar_redondeo(Decimal("235750"), Decimal("1000"), "mitad_superior") == Decimal("236000.0000")
    assert aplicar_redondeo(Decimal("235750"), Decimal("1000"), "piso") == Decimal("235000.0000")
    assert aplicar_redondeo(Decimal("235750"), Decimal("1000"), "techo") == Decimal("236000.0000")


# ── Otros tipos de componente ──

def test_escalonado_marginal():
    filas, total = calcular_escalonado(_tramos_escalonados(), Decimal("35"))
    assert total == Decimal("410000.0000")
    assert len(filas) == 3


def test_escalonado_modo_completo():
    tramos = [
        {"desde": "1", "hasta": "15", "valor": "15000", "modo": "completo"},
        {"desde": "16", "hasta": None, "valor": "10000", "modo": "completo"},
    ]
    _, total_20 = calcular_escalonado(tramos, Decimal("20"))
    assert total_20 == Decimal("200000.0000")  # 20 × 10.000 (todo en el segundo tramo)


def test_piso_rentabilidad_advertencia():
    politica = {
        "margen_objetivo": "0",
        "margen_minimo": "0",
        "piso_visita": "300000",
        "vigencia_cotizacion_dias": 30,
        "redondeo_multiplo": "1",
        "redondeo_modo": "ninguno",
    }
    resultado = _calcular("1", 10, "plano", conjunto=_conjunto_semilla(politica=politica))
    assert any(a["codigo"] == "BAJO_PISO_RENTABILIDAD" for a in resultado["advertencias"])


def test_conjunto_no_vigente_rechazado():
    conjunto = _conjunto_semilla()
    conjunto["vigencia_hasta"] = "2025-12-31"
    with pytest.raises(CosteoError) as exc:
        _calcular("1", 10, None, conjunto=conjunto)
    assert exc.value.code == "CONJUNTO_SIN_VIGENCIA"


def test_servicio_desconocido_rechazado():
    seleccion = {"servicios": [{"codigo": "no_existe", "cantidad": Decimal("10")}],
                 "factores": {}, "descuento_pct": None}
    with pytest.raises(CosteoError) as exc:
        calcular(_contexto("1", 10), _conjunto_semilla(), seleccion)
    assert exc.value.code == "SERVICIO_NO_ENCONTRADO"
