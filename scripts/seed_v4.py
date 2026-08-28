"""Datos semilla de la especificación v4 — idempotente.

- 15 cultivos nuevos (catálogo ampliado, íconos con gobernanza v4)
- Kc FAO-56 para los cultivos nuevos y café
- Variedades de café (Cenicafé)
- Reglas de rotación (leguminosas/cereales)
- Períodos de carencia de agroquímicos
- Curva de extracción de referencia para café

Uso: python scripts/seed_v4.py
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "shared"))
sys.path.insert(0, str(ROOT / "apps" / "backend"))
sys.path.insert(0, str(ROOT))

from agroia.database import async_session_factory  # noqa: E402
from sqlalchemy import select  # noqa: E402

from agroia_backend.models.checklist_bpa import PeriodoCarencia  # noqa: E402
from agroia_backend.models.compatibilidad_rotacion import CompatibilidadRotacion  # noqa: E402
from agroia_backend.models.cultivo import Cultivo  # noqa: E402
from agroia_backend.models.curva_extraccion import CurvaExtraccion  # noqa: E402
from agroia_backend.models.variedad_cultivo import VariedadCultivo  # noqa: E402

CULTIVOS_NUEVOS = [
    {
        "nombre": "Panela / Caña panelera",
        "nombre_cientifico": "Saccharum officinarum (var. panelera)",
        "icono": "custom:panela_v1",
        "descripcion": "Principal producto agrícola exclusivamente colombiano; ~200.000 ha, 350.000 familias (Fedepanela).",
        "profundidad_radicular_min_cm": 60,
        "dias_ciclo": 450,
        "kc": (0.40, 1.00, 0.75),
    },
    {
        "nombre": "Ñame",
        "nombre_cientifico": "Dioscorea alata",
        "icono": "🍠",
        "descripcion": "Tubérculo de la región Caribe (Córdoba, Sucre).",
        "profundidad_radicular_min_cm": 50,
        "dias_ciclo": 300,
        "kc": (0.50, 0.90, 0.65),
    },
    {
        "nombre": "Chontaduro",
        "nombre_cientifico": "Bactris gasipaes",
        "icono": "custom:chontaduro_v1",
        "descripcion": "Palma del Pacífico y Amazonía, fruto rico en proteína y aceite.",
        "profundidad_radicular_min_cm": 80,
        "dias_ciclo": 365,
        "kc": (0.70, 0.90, 0.80),
    },
    {
        "nombre": "Lulo",
        "nombre_cientifico": "Solanum quitoense",
        "icono": "custom:lulo_v1",
        "descripcion": "Frutal andino de clima medio; lulo de Castilla (Agrosavia).",
        "profundidad_radicular_min_cm": 40,
        "dias_ciclo": 240,
        "kc": (0.60, 0.95, 0.75),
    },
    {
        "nombre": "Mora",
        "nombre_cientifico": "Rubus glaucus",
        "icono": "🫐",
        "descripcion": "Mora de Castilla, frutal de clima frío moderado (Agrosavia).",
        "profundidad_radicular_min_cm": 45,
        "dias_ciclo": 300,
        "kc": (0.55, 0.85, 0.70),
    },
    {
        "nombre": "Guayaba",
        "nombre_cientifico": "Psidium guajava",
        "icono": "custom:guayaba_v1",
        "descripcion": "Cadena guayaba-bocadillo (Santander); Corpoica.",
        "profundidad_radicular_min_cm": 70,
        "dias_ciclo": 330,
        "kc": (0.60, 0.85, 0.75),
    },
    {
        "nombre": "Granadilla / Curuba",
        "nombre_cientifico": "Passiflora ligularis",
        "icono": "custom:granadilla_v1",
        "descripcion": "Frutales pasifloráceas de clima frío (Agrosavia).",
        "profundidad_radicular_min_cm": 50,
        "dias_ciclo": 270,
        "kc": (0.60, 0.85, 0.75),
    },
    {
        "nombre": "Arveja",
        "nombre_cientifico": "Pisum sativum",
        "icono": "🫛",
        "descripcion": "Leguminosa de clima frío (FAO/Agrosavia).",
        "profundidad_radicular_min_cm": 35,
        "dias_ciclo": 110,
        "kc": (0.50, 0.90, 0.60),
    },
    {
        "nombre": "Habichuela",
        "nombre_cientifico": "Phaseolus vulgaris",
        "icono": "custom:habichuela_v1",
        "descripcion": "Hortaliza leguminosa de Cundinamarca-Boyacá (Agrosavia).",
        "profundidad_radicular_min_cm": 35,
        "dias_ciclo": 90,
        "kc": (0.50, 0.90, 0.60),
    },
    {
        "nombre": "Ahuyama / Auyama",
        "nombre_cientifico": "Cucurbita maxima",
        "icono": "custom:ahuyama_v1",
        "descripcion": "Hortaliza de clima cálido y medio (Agrosavia).",
        "profundidad_radicular_min_cm": 45,
        "dias_ciclo": 120,
        "kc": (0.50, 0.95, 0.70),
    },
    {
        "nombre": "Fresa",
        "nombre_cientifico": "Fragaria × ananassa",
        "icono": "🍓",
        "descripcion": "Frutal de clima frío moderado (Agrosavia).",
        "profundidad_radicular_min_cm": 30,
        "dias_ciclo": 180,
        "kc": (0.40, 0.85, 0.75),
    },
    {
        "nombre": "Coco",
        "nombre_cientifico": "Cocos nucifera",
        "icono": "🥥",
        "descripcion": "Palma del Caribe y Pacífico colombiano (Agrosavia).",
        "profundidad_radicular_min_cm": 100,
        "dias_ciclo": 1200,
        "kc": (0.65, 0.95, 0.85),
    },
    {
        "nombre": "Caucho",
        "nombre_cientifico": "Hevea brasiliensis",
        "icono": "custom:caucho_v1",
        "descripcion": "Programas de sustitución de cultivos (Meta, Caquetá).",
        "profundidad_radicular_min_cm": 100,
        "dias_ciclo": 2500,
        "kc": (0.60, 0.95, 0.80),
    },
    {
        "nombre": "Fique",
        "nombre_cientifico": "Furcraea andina",
        "icono": "custom:fique_v1",
        "descripcion": "Fibra natural del Cauca, Nariño y Santander (Agrosavia).",
        "profundidad_radicular_min_cm": 60,
        "dias_ciclo": 730,
        "kc": (0.45, 0.70, 0.55),
    },
    {
        "nombre": "Quinua",
        "nombre_cientifico": "Chenopodium quinoa",
        "icono": "🌾",
        "descripcion": "Cereal andino de Nariño y Boyacá (Agrosavia).",
        "profundidad_radicular_min_cm": 40,
        "dias_ciclo": 150,
        "kc": (0.45, 0.90, 0.50),
    },
]

VARIEDADES_CAFE = [
    ("Castillo", "Resistente a roya (Hemileia vastatrix)", 1200, 2000, "exportación especial"),
    ("Caturra", "Alta productividad; susceptible a roya", 1000, 1800, "consumo interno"),
    ("Colombia", "Resistente a roya, porte bajo", 1200, 1900, "exportación"),
    ("Borbón", "Taza de alta calidad; susceptible a roya", 1200, 2000, "exportación especial"),
]

ROTACIONES = [
    ("Maíz", "Fríjol", "fijacion_n", "Leguminosa: aporta N al suelo tras un cereal exigente en nitrógeno"),
    ("Maíz", "Arveja", "fijacion_n", "Leguminosa de clima frío: repone N tras el cereal"),
    ("Arroz", "Fríjol", "fijacion_n", "Rotación arroz-leguminosa: aporta N y mejora la estructura"),
    ("Papa", "Fríjol", "fijacion_n", "Rompe ciclos de patógenos del suelo y aporta N"),
    ("Tomate", "Fríjol", "fijacion_n", "Leguminosa tras solanácea exigente: repone N y corta ciclos de plagas"),
    ("Yuca", "Fríjol", "fijacion_n", "Leguminosa tras raíz exigente en potasio: repone N"),
    ("Fríjol", "Maíz", "ruptura_plaga", "Cambio de familia botánica: rompe el ciclo de plagas de la leguminosa"),
    ("Fríjol", "Papa", "ruptura_plaga", "Alterna familia botánica: reduce inóculo de patógenos"),
]

CARENCIAS = [
    ("Urea", 0, "Fertilizante de absorción rápida; sin restricción"),
    ("DAP", 0, "Fertilizante fosfatado; sin restricción"),
    ("KCl", 0, "Fertilizante potásico; sin restricción"),
    ("Cal dolomítica", 0, "Enmienda; sin restricción"),
    ("Compost", 0, "Enmienda orgánica; sin restricción"),
    ("Mancozeb", 14, "Fungicida de contacto"),
    ("Clorpirifos", 21, "Insecticida organofosforado"),
    ("Glifosato", 7, "Herbicida sistémico"),
    ("Carbendazim", 15, "Fungicida sistémico"),
    ("Cipermetrina", 14, "Insecticida piretroide"),
]

CURVA_CAFE = [
    ("Vegetativo", "N", 20.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Floración", "N", 45.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Fructificación", "N", 75.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Cosecha", "N", 100.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Vegetativo", "K", 15.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Floración", "K", 35.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Fructificación", "K", 70.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Cosecha", "K", 100.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Vegetativo", "P", 20.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Floración", "P", 40.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Fructificación", "P", 70.0, "Cenicafé, manual del cafetero cap. 4"),
    ("Cosecha", "P", 100.0, "Cenicafé, manual del cafetero cap. 4"),
]


async def main() -> None:
    async with async_session_factory() as db:
        # 1) Cultivos nuevos
        creados = 0
        for datos in CULTIVOS_NUEVOS:
            existe = (
                await db.execute(select(Cultivo).where(Cultivo.nombre == datos["nombre"]))
            ).scalar_one_or_none()
            if existe is not None:
                if existe.icono is None:
                    existe.icono = datos["icono"]
                    creados += 1
                continue
            kc = datos.pop("kc")
            db.add(Cultivo(
                nombre=datos["nombre"],
                nombre_cientifico=datos["nombre_cientifico"],
                icono=datos["icono"],
                descripcion=datos["descripcion"],
                profundidad_radicular_min_cm=datos["profundidad_radicular_min_cm"],
                dias_ciclo=datos["dias_ciclo"],
                kc_inicial=kc[0], kc_medio=kc[1], kc_final=kc[2],
                activo=True,
            ))
            creados += 1
        await db.flush()
        print(f"cultivos nuevos: {creados}")

        # 2) Kc de café
        cafe = (
            await db.execute(select(Cultivo).where(Cultivo.nombre == "Café"))
        ).scalar_one_or_none()
        if cafe is not None and cafe.kc_medio is None:
            cafe.kc_inicial = 0.65
            cafe.kc_medio = 0.85
            cafe.kc_final = 0.75
            print("kc café asignado")

        # 3) Variedades de café
        if cafe is not None:
            existentes = {
                v.nombre_variedad
                for v in (
                    await db.execute(
                        select(VariedadCultivo).where(VariedadCultivo.cultivo_id == cafe.id)
                    )
                ).scalars().all()
            }
            for nombre, res, alt_min, alt_max, mercado in VARIEDADES_CAFE:
                if nombre in existentes:
                    continue
                db.add(VariedadCultivo(
                    cultivo_id=cafe.id,
                    nombre_variedad=nombre,
                    resistencias=res,
                    altitud_min_msnm=alt_min,
                    altitud_max_msnm=alt_max,
                    mercado_objetivo=mercado,
                    fuente="Cenicafé (FNC)",
                ))
            print("variedades café sembradas")

        # 4) Reglas de rotación
        nombres_cultivos = {
            c.nombre: c.id
            for c in (await db.execute(select(Cultivo))).scalars().all()
        }
        rot_creadas = 0
        existentes_rot = {
            (r.cultivo_actual_id, r.cultivo_siguiente_id)
            for r in (await db.execute(select(CompatibilidadRotacion))).scalars().all()
        }
        for actual, siguiente, beneficio, motivo in ROTACIONES:
            aid, sid = nombres_cultivos.get(actual), nombres_cultivos.get(siguiente)
            if aid is None or sid is None:
                continue
            if (aid, sid) in existentes_rot:
                continue
            db.add(CompatibilidadRotacion(
                cultivo_actual_id=aid, cultivo_siguiente_id=sid,
                beneficio=beneficio, motivo=motivo,
            ))
            existentes_rot.add((aid, sid))
            rot_creadas += 1
        print(f"reglas rotación: {rot_creadas}")

        # 5) Períodos de carencia
        existentes_car = {
            p.producto.lower()
            for p in (await db.execute(select(PeriodoCarencia))).scalars().all()
        }
        for producto, dias, fuente in CARENCIAS:
            if producto.lower() in existentes_car:
                continue
            db.add(PeriodoCarencia(producto=producto, dias_carencia=dias, fuente=fuente))
        print("periodos carencia sembrados")

        # 6) Curva de extracción de café
        if cafe is not None:
            existentes_cur = {
                (p.etapa_fenologica, p.nutriente)
                for p in (
                    await db.execute(
                        select(CurvaExtraccion).where(CurvaExtraccion.cultivo_id == cafe.id)
                    )
                ).scalars().all()
            }
            for etapa, nutriente, pct, fuente in CURVA_CAFE:
                if (etapa, nutriente) in existentes_cur:
                    continue
                db.add(CurvaExtraccion(
                    cultivo_id=cafe.id,
                    etapa_fenologica=etapa,
                    nutriente=nutriente,
                    pct_extraccion_acumulado=pct,
                    fuente=fuente,
                ))
            print("curva café sembrada")

        await db.commit()
    print("seed_v4 completo")


if __name__ == "__main__":
    asyncio.run(main())
