"""Asegura que las reglas agronómicas ampliadas existan en la BD.

Al arrancar la aplicación (igual que `asegurar_enums`) inserta de forma
idempotente las reglas faltantes del sistema experto:

1. 8 variables secundarias/micronutrientes (universales): Ca, Mg, S, Fe,
   Mn, Zn, Cu, B — cierran la cobertura de 9 a 17 de las 18 variables.
2. Reglas específicas (pH, N, P, K, MO) para cultivos del catálogo que
   aún no las tenían: Aguacate, Cacao, Fríjol, Tomate y Yuca.

Fuentes: UPRA, Cenicafé y literatura agronómica colombiana.
"""

import sqlalchemy as sa

from agroia.database import async_session_factory
from agroia.logging import get_logger

logger = get_logger(__name__)

# (variable, umbral_min, umbral_max, accion, prioridad, fuente) — universales
REGLAS_UNIVERSALES = [
    ("Ca", 1000.0, 4000.0,
     "Ajustar calcio: aplicar cal dolomítica si está bajo; si excede, reducir enmiendas cálcicas.",
     "Media", "UPRA"),
    ("Mg", 100.0, 500.0,
     "Ajustar magnesio: sulfato de magnesio si está bajo; si excede, vigilar antagonismo con K.",
     "Media", "Cenicafé"),
    ("S", 10.0, 40.0,
     "Ajustar azufre: azufre elemental o sulfato de amonio si está bajo.",
     "Baja", "UPRA"),
    ("Fe", 10.0, 100.0,
     "Ajustar hierro: quelato de hierro si está bajo (común en pH alto); si excede, revisar drenaje.",
     "Media", "AGROSAVIA"),
    ("Mn", 5.0, 100.0,
     "Ajustar manganeso: sulfato de manganeso si está bajo; si excede, encalar para reducir toxicidad.",
     "Baja", "AGROSAVIA"),
    ("Zn", 2.0, 20.0,
     "Ajustar zinc: sulfato de zinc si está bajo; si excede, evitar enmiendas con zinc.",
     "Media", "AGROSAVIA"),
    ("Cu", 1.0, 10.0,
     "Ajustar cobre: sulfato de cobre si está bajo; si excede (toxicidad), suspender fungicidas cúpricos.",
     "Baja", "AGROSAVIA"),
    ("B", 0.5, 2.0,
     "Ajustar boro: bórax en dosis baja si está bajo (rango estrecho); si excede, lavar con riego.",
     "Alta", "AGROSAVIA"),
]

# cultivo → lista de (variable, min, max, accion, prioridad, fuente)
REGLAS_POR_CULTIVO = {
    "Aguacate": [
        ("pH", 5.5, 6.5, "Encalar con cal dolomítica si el pH es menor a 5.5.", "Alta", "Cenicafé"),
        ("N", 80.0, 150.0, "Ajustar nitrógeno en fracciones (aguacate responde a N moderado).", "Media", "UPRA"),
        ("P", 15.0, 40.0, "Ajustar fósforo: aplicar DAP/fosfato según análisis.", "Media", "UPRA"),
        ("K", 120.0, 300.0, "Ajustar potasio: KCl o K2SO4 según análisis.", "Alta", "UPRA"),
        ("MO", 3.0, None, "Aumentar materia orgánica (compost) para retención y biología del suelo.", "Media", "AGROSAVIA"),
    ],
    "Cacao": [
        ("pH", 5.5, 7.0, "Encalar si el pH es menor a 5.5 (cacao tolera hasta 7.0).", "Alta", "Cenicafé"),
        ("N", 100.0, 250.0, "Ajustar nitrógeno: urea fraccionada según etapa del cultivo.", "Media", "UPRA"),
        ("P", 10.0, 35.0, "Ajustar fósforo: roca fosfórica en suelos ácidos.", "Media", "UPRA"),
        ("K", 150.0, 400.0, "Ajustar potasio: KCl según análisis (cloruros con precaución).", "Media", "UPRA"),
        ("MO", 3.0, None, "Mantener sombra y materia orgánica (hojarasca) para el cacao.", "Media", "AGROSAVIA"),
    ],
    "Fr\u00edjol": [
        ("pH", 5.5, 7.0, "Encalar si el pH es menor a 5.5; el fríjol es sensible a la acidez.", "Alta", "AGROSAVIA"),
        ("N", 40.0, 120.0, "Ajustar nitrógeno: el fríjol fija N pero responde a arranque (10-20 kg/ha).", "Media", "AGROSAVIA"),
        ("P", 20.0, 60.0, "Ajustar fósforo: fundamental para nodulación y floración.", "Alta", "AGROSAVIA"),
        ("K", 100.0, 250.0, "Ajustar potasio: KCl en banda al momento de la siembra.", "Media", "UPRA"),
    ],
    "Tomate": [
        ("pH", 6.0, 7.0, "Encalar si el pH es menor a 6.0 (tomate prefiere suelos neutros).", "Alta", "AGROSAVIA"),
        ("N", 120.0, 250.0, "Ajustar nitrógeno: fertirriego fraccionado en etapas.", "Alta", "UPRA"),
        ("P", 40.0, 100.0, "Ajustar fósforo: alto requerimiento en floración y cuajado.", "Media", "AGROSAVIA"),
        ("K", 200.0, 400.0, "Ajustar potasio: clave para calidad de fruto.", "Alta", "AGROSAVIA"),
        ("MO", 2.0, None, "Aumentar materia orgánica para estructura y sanidad radicular.", "Media", "AGROSAVIA"),
    ],
    "Yuca": [
        ("pH", 5.0, 7.0, "Encalar solo si el pH es menor a 5.0 (la yuca tolera acidez).", "Media", "AGROSAVIA"),
        ("N", 40.0, 120.0, "Ajustar nitrógeno: moderado; exceso reduce almidón en raíz.", "Media", "UPRA"),
        ("P", 10.0, 50.0, "Ajustar fósforo: favorece desarrollo radicular.", "Media", "UPRA"),
        ("K", 80.0, 250.0, "Ajustar potasio: alta demanda para llenado de raíces.", "Alta", "UPRA"),
    ],
}


async def asegurar_reglas() -> dict:
    """Inserta las reglas faltantes. Retorna conteos {universales, cultivos}."""
    from sqlalchemy import select

    from agroia_backend.models.cultivo import Cultivo
    from agroia_backend.models.regla_agronomica import ReglaAgronomica

    async with async_session_factory() as db:
        # Endurecer contra search_path frágil (Neon/pgBouncer): los casts de
        # enum en INSERT dependen del search_path de la transacción.
        await db.execute(sa.text("SET LOCAL search_path TO public, agroia"))

        cultivos = {
            c.nombre: c
            for c in (await db.execute(select(Cultivo))).scalars().all()
        }
        insertadas = {"universales": 0, "cultivos": 0}

        # Índice en Python de reglas existentes (evita casts `::variablesuelo`).
        existentes = (
            await db.execute(
                select(ReglaAgronomica).where(ReglaAgronomica.activa.is_(True))
            )
        ).scalars().all()

        def _variable_nombre(r) -> str:
            var = getattr(r, "variable", None)
            return str(getattr(var, "value", None) or var or "")

        def _existe(variable, umin, umax, cultivo_id) -> bool:
            for r in existentes:
                if r.cultivo_id != cultivo_id:
                    continue
                if _variable_nombre(r) != variable:
                    continue
                if (r.umbral_min is None) != (umin is None):
                    continue
                if umin is not None and abs(float(r.umbral_min) - float(umin)) > 1e-9:
                    continue
                if (r.umbral_max is None) != (umax is None):
                    continue
                if umax is not None and abs(float(r.umbral_max) - float(umax)) > 1e-9:
                    continue
                return True
            return False

        async def _insertar(variable, umin, umax, accion, prioridad, fuente, cultivo):
            if _existe(variable, umin, umax, cultivo.id if cultivo else None):
                return False
            db.add(ReglaAgronomica(
                cultivo_id=cultivo.id if cultivo else None,
                variable=variable,
                umbral_min=umin,
                umbral_max=umax,
                accion=accion,
                prioridad=prioridad,
                fuente=fuente,
                version=1,
                activa=True,
            ))
            existentes.append(
                ReglaAgronomica(
                    cultivo_id=cultivo.id if cultivo else None,
                    variable=variable,
                    umbral_min=umin,
                    umbral_max=umax,
                    activa=True,
                )
            )
            return True

        for variable, umin, umax, accion, prioridad, fuente in REGLAS_UNIVERSALES:
            if await _insertar(variable, umin, umax, accion, prioridad, fuente, None):
                insertadas["universales"] += 1

        for nombre, reglas in REGLAS_POR_CULTIVO.items():
            cultivo = cultivos.get(nombre)
            if cultivo is None:
                continue
            for variable, umin, umax, accion, prioridad, fuente in reglas:
                if await _insertar(variable, umin, umax, accion, prioridad, fuente, cultivo):
                    insertadas["cultivos"] += 1

        await db.commit()
    if insertadas["universales"] or insertadas["cultivos"]:
        logger.info("reglas_aseguradas", **insertadas)
    return insertadas
