"""Siembra idempotente de datos v4 (catálogo ampliado, Kc, variedades, rotación, carencias, curvas).

Usado por `scripts/seed_v4.py` (local) y por `POST /api/v1/admin/v4/sembrar` (producción).
"""

from sqlalchemy import select

from agroia_backend.models.checklist_bpa import PeriodoCarencia
from agroia_backend.models.compatibilidad_rotacion import CompatibilidadRotacion
from agroia_backend.models.cultivo import Cultivo
from agroia_backend.models.curva_extraccion import CurvaExtraccion
from agroia_backend.models.variedad_cultivo import VariedadCultivo

CULTIVOS_NUEVOS = [
    {"nombre": "Panela / Caña panelera", "nombre_cientifico": "Saccharum officinarum (var. panelera)",
     "icono": "🟫",
     "descripcion": "Principal producto agrícola exclusivamente colombiano; ~200.000 ha, 350.000 familias (Fedepanela).",
     "profundidad_radicular_min_cm": 60, "dias_ciclo": 450, "kc": (0.40, 1.00, 0.75)},
    {"nombre": "Ñame", "nombre_cientifico": "Dioscorea alata", "icono": "🍠",
     "descripcion": "Tubérculo de la región Caribe (Córdoba, Sucre).",
     "profundidad_radicular_min_cm": 50, "dias_ciclo": 300, "kc": (0.50, 0.90, 0.65)},
    {"nombre": "Chontaduro", "nombre_cientifico": "Bactris gasipaes", "icono": "🌴",
     "descripcion": "Palma del Pacífico y Amazonía, fruto rico en proteína y aceite.",
     "profundidad_radicular_min_cm": 80, "dias_ciclo": 365, "kc": (0.70, 0.90, 0.80)},
    {"nombre": "Lulo", "nombre_cientifico": "Solanum quitoense", "icono": "🍊",
     "descripcion": "Frutal andino de clima medio; lulo de Castilla (Agrosavia).",
     "profundidad_radicular_min_cm": 40, "dias_ciclo": 240, "kc": (0.60, 0.95, 0.75)},
    {"nombre": "Mora", "nombre_cientifico": "Rubus glaucus", "icono": "🫐",
     "descripcion": "Mora de Castilla, frutal de clima frío moderado (Agrosavia).",
     "profundidad_radicular_min_cm": 45, "dias_ciclo": 300, "kc": (0.55, 0.85, 0.70)},
    {"nombre": "Guayaba", "nombre_cientifico": "Psidium guajava", "icono": "🍐",
     "descripcion": "Cadena guayaba-bocadillo (Santander); Corpoica.",
     "profundidad_radicular_min_cm": 70, "dias_ciclo": 330, "kc": (0.60, 0.85, 0.75)},
    {"nombre": "Granadilla / Curuba", "nombre_cientifico": "Passiflora ligularis", "icono": "🟠",
     "descripcion": "Frutales pasifloráceas de clima frío (Agrosavia).",
     "profundidad_radicular_min_cm": 50, "dias_ciclo": 270, "kc": (0.60, 0.85, 0.75)},
    {"nombre": "Arveja", "nombre_cientifico": "Pisum sativum", "icono": "🫛",
     "descripcion": "Leguminosa de clima frío (FAO/Agrosavia).",
     "profundidad_radicular_min_cm": 35, "dias_ciclo": 110, "kc": (0.50, 0.90, 0.60)},
    {"nombre": "Habichuela", "nombre_cientifico": "Phaseolus vulgaris", "icono": "🥬",
     "descripcion": "Hortaliza leguminosa de Cundinamarca-Boyacá (Agrosavia).",
     "profundidad_radicular_min_cm": 35, "dias_ciclo": 90, "kc": (0.50, 0.90, 0.60)},
    {"nombre": "Ahuyama / Auyama", "nombre_cientifico": "Cucurbita maxima", "icono": "🟧",
     "descripcion": "Hortaliza de clima cálido y medio (Agrosavia).",
     "profundidad_radicular_min_cm": 45, "dias_ciclo": 120, "kc": (0.50, 0.95, 0.70)},
    {"nombre": "Fresa", "nombre_cientifico": "Fragaria × ananassa", "icono": "🍓",
     "descripcion": "Frutal de clima frío moderado (Agrosavia).",
     "profundidad_radicular_min_cm": 30, "dias_ciclo": 180, "kc": (0.40, 0.85, 0.75)},
    {"nombre": "Coco", "nombre_cientifico": "Cocos nucifera", "icono": "🥥",
     "descripcion": "Palma del Caribe y Pacífico colombiano (Agrosavia).",
     "profundidad_radicular_min_cm": 100, "dias_ciclo": 1200, "kc": (0.65, 0.95, 0.85)},
    {"nombre": "Caucho", "nombre_cientifico": "Hevea brasiliensis", "icono": "🌳",
     "descripcion": "Programas de sustitución de cultivos (Meta, Caquetá).",
     "profundidad_radicular_min_cm": 100, "dias_ciclo": 2500, "kc": (0.60, 0.95, 0.80)},
    {"nombre": "Fique", "nombre_cientifico": "Furcraea andina", "icono": "🌵",
     "descripcion": "Fibra natural del Cauca, Nariño y Santander (Agrosavia).",
     "profundidad_radicular_min_cm": 60, "dias_ciclo": 730, "kc": (0.45, 0.70, 0.55)},
    {"nombre": "Quinua", "nombre_cientifico": "Chenopodium quinoa", "icono": "🌾",
     "descripcion": "Cereal andino de Nariño y Boyacá (Agrosavia).",
     "profundidad_radicular_min_cm": 40, "dias_ciclo": 150, "kc": (0.45, 0.90, 0.50)},
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
    ("Vegetativo", "N", 20.0), ("Floración", "N", 45.0), ("Fructificación", "N", 75.0), ("Cosecha", "N", 100.0),
    ("Vegetativo", "K", 15.0), ("Floración", "K", 35.0), ("Fructificación", "K", 70.0), ("Cosecha", "K", 100.0),
    ("Vegetativo", "P", 20.0), ("Floración", "P", 40.0), ("Fructificación", "P", 70.0), ("Cosecha", "P", 100.0),
]

FUENTE_CENICAFE = "Cenicafé, manual del cafetero cap. 4"


async def sembrar_v4(db) -> dict:
    """Siembra idempotente de todos los datos estáticos de la especificación v4."""
    resumen = {}

    for datos in CULTIVOS_NUEVOS:
        existe = (
            await db.execute(select(Cultivo).where(Cultivo.nombre == datos["nombre"]))
        ).scalar_one_or_none()
        if existe is not None:
            # Repara íconos 'custom:*' previos con el emoji representativo
            if not existe.icono or str(existe.icono).startswith("custom:"):
                existe.icono = datos["icono"]
            continue
        kc = datos["kc"]
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
    await db.flush()
    resumen["cultivos"] = len(CULTIVOS_NUEVOS)

    cafe = (
        await db.execute(select(Cultivo).where(Cultivo.nombre == "Café"))
    ).scalar_one_or_none()
    if cafe is not None:
        if cafe.kc_medio is None:
            cafe.kc_inicial = 0.65
            cafe.kc_medio = 0.85
            cafe.kc_final = 0.75

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
                cultivo_id=cafe.id, nombre_variedad=nombre, resistencias=res,
                altitud_min_msnm=alt_min, altitud_max_msnm=alt_max,
                mercado_objetivo=mercado, fuente="Cenicafé (FNC)",
            ))
        resumen["variedades_cafe"] = len(VARIEDADES_CAFE)

        existentes_cur = {
            (p.etapa_fenologica, p.nutriente)
            for p in (
                await db.execute(
                    select(CurvaExtraccion).where(CurvaExtraccion.cultivo_id == cafe.id)
                )
            ).scalars().all()
        }
        for etapa, nutriente, pct in CURVA_CAFE:
            if (etapa, nutriente) in existentes_cur:
                continue
            db.add(CurvaExtraccion(
                cultivo_id=cafe.id, etapa_fenologica=etapa, nutriente=nutriente,
                pct_extraccion_acumulado=pct, fuente=FUENTE_CENICAFE,
            ))
        resumen["curva_cafe"] = len(CURVA_CAFE)

    nombres_cultivos = {
        c.nombre: c.id for c in (await db.execute(select(Cultivo))).scalars().all()
    }
    existentes_rot = {
        (r.cultivo_actual_id, r.cultivo_siguiente_id)
        for r in (await db.execute(select(CompatibilidadRotacion))).scalars().all()
    }
    for actual, siguiente, beneficio, motivo in ROTACIONES:
        aid, sid = nombres_cultivos.get(actual), nombres_cultivos.get(siguiente)
        if aid is None or sid is None or (aid, sid) in existentes_rot:
            continue
        db.add(CompatibilidadRotacion(
            cultivo_actual_id=aid, cultivo_siguiente_id=sid,
            beneficio=beneficio, motivo=motivo,
        ))
        existentes_rot.add((aid, sid))
    resumen["rotaciones"] = len(ROTACIONES)

    existentes_car = {
        p.producto.lower() for p in (await db.execute(select(PeriodoCarencia))).scalars().all()
    }
    for producto, dias, fuente in CARENCIAS:
        if producto.lower() in existentes_car:
            continue
        db.add(PeriodoCarencia(producto=producto, dias_carencia=dias, fuente=fuente))
    resumen["carencias"] = len(CARENCIAS)

    await db.commit()
    return resumen
