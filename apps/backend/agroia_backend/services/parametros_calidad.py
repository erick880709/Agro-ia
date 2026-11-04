"""Parámetros administrables de calidad (Épica E7, HU-13).

Carga y actualiza los umbrales del motor de calidad desde la tabla
`parametro_calidad_sensor`, con versionado y auditoría de cambios.
Los valores por defecto viven en `motor_calidad.UMBRALES`.
"""

from __future__ import annotations

from agroia_backend.services.motor_calidad import UMBRALES

# Claves administrables (mapeadas a UMBRALES).
CLAVES_ADMINISTRABLES = {
    "ph_min": "pH inferior (saturación)",
    "ph_max": "pH superior (saturación)",
    "ce_max_dsm": "CE máxima (saturación, dS/m)",
    "npk_max_mgkg": "N/P/K máximo (saturación, mg/kg)",
    "humedad_minima_pct": "Humedad mínima para pH/CE/NPK (%)",
    "humedad_sonda_max_pct": "Humedad ≈ 0 (sonda fuera del suelo, %)",
    "ce_sonda_max_dsm": "CE ≈ 0 (sonda fuera del suelo, dS/m)",
    "temp_min_c": "Temperatura mínima física (°C)",
    "temp_max_sensor_c": "Temperatura máxima física (°C)",
    "temp_sol_directo_c": "Alerta por sol directo (°C)",
}


def parametros_por_defecto() -> dict[str, dict]:
    """Parámetros por defecto (motor_calidad.UMBRALES) con descripción."""
    return {
        clave: {
            "valor": UMBRALES.get(clave),
            "descripcion": desc,
            "version": 1,
        }
        for clave, desc in CLAVES_ADMINISTRABLES.items()
    }


def aplicar_parametros_umbrales(override: dict[str, float] | None) -> dict:
    """Combina los umbrales por defecto con un override administrable.

    Devuelve el dict de umbrales que debe usar el motor de calidad.
    """
    umbrales = dict(UMBRALES)
    for clave, valor in (override or {}).items():
        if clave in umbrales and valor is not None:
            umbrales[clave] = float(valor)
    return umbrales


def versionar(version_actual: int) -> int:
    """Incrementa la versión de la regla al cambiar un parámetro."""
    return version_actual + 1
