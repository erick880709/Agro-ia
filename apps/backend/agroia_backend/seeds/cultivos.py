"""Seed data para el catálogo de cultivos de AgroIA.

Precarga ~30 cultivos: 5 prioritarios colombianos + ~25 internacionales.
Ejecutar UNA sola vez: python -m agroia_backend.seeds.cultivos
"""


# ── Cultivos prioritarios colombianos (fuente nacional, ficha completa) ──
CULTIVOS_COLOMBIA = [
    {
        "nombre": "Café",
        "nombre_cientifico": "Coffea arabica",
        "descripcion": "Principal producto agrícola de exportación de Colombia. Cultivado en el Eje Cafetero entre 1,200-1,800 msnm.",
        "icono": "☕",
        "profundidad_radicular_min_cm": 80,
        "gdd_total_requerido": 2000,
        "dias_ciclo": 270,
        "ficha": {
            "tipo_fuente": "Nacional",
            "fuente": "Cenicafé, 2007, Guía de fertilidad del suelo y nutrición del café en Colombia. FNC.",
            "umbrales": {
                "ph": {"min": 5.5, "max": 6.5, "unidad": "", "fuente": "Cenicafé 2007"},
                "temperatura": {"min": 18, "max": 24, "unidad": "°C", "fuente": "Arcila et al., 2007"},
                "humedad_suelo": {"min": 60, "max": 80, "unidad": "% capacidad de campo", "fuente": "Wintgens, 2009"},
                "altitud": {"min": 1200, "max": 1800, "unidad": "msnm", "fuente": "Cenicafé"},
                "materia_organica": {"min": 8, "max": 20, "unidad": "%", "fuente": "Cenicafé 2007"},
                "nitrogeno": {"min": 200, "max": 400, "unidad": "kg/ha/año", "fuente": "Cenicafé"},
                "fosforo": {"min": 30, "max": 75, "unidad": "kg/ha/año P₂O₅", "fuente": "Cenicafé"},
                "potasio": {"min": 100, "max": 300, "unidad": "kg/ha/año K₂O", "fuente": "Cenicafé"},
            },
            "datos_economicos": {
                "rendimiento_esperado": 1.8, "unidad_rendimiento": "ton/ha",
                "ciclo": "Perenne (cosecha anual)",
                "precio_referencia": 1200000, "unidad_precio": "COP/carga (125kg)",
            },
        },
    },
    {
        "nombre": "Maíz",
        "nombre_cientifico": "Zea mays",
        "descripcion": "Cereal básico en la dieta colombiana. Cultivado en todo el territorio nacional.",
        "icono": "🌽",
        "profundidad_radicular_min_cm": 45,
        "gdd_total_requerido": 1600,
        "dias_ciclo": 130,
        "ficha": {
            "tipo_fuente": "Nacional",
            "fuente": "UPRA, Zonificación de aptitud para maíz tecnificado. AGROSAVIA, Manual de manejo agronómico.",
            "umbrales": {
                "ph": {"min": 5.5, "max": 7.0, "unidad": "", "fuente": "UPRA"},
                "temperatura": {"min": 18, "max": 32, "unidad": "°C", "fuente": "AGROSAVIA"},
                "precipitacion": {"min": 500, "max": 1200, "unidad": "mm/ciclo", "fuente": "UPRA"},
                "nitrogeno": {"min": 120, "max": 180, "unidad": "kg/ha", "fuente": "AGROSAVIA"},
                "fosforo": {"min": 40, "max": 80, "unidad": "kg/ha P₂O₅", "fuente": "AGROSAVIA"},
                "potasio": {"min": 60, "max": 120, "unidad": "kg/ha K₂O", "fuente": "AGROSAVIA"},
            },
            "datos_economicos": {
                "rendimiento_esperado": 4.5, "unidad_rendimiento": "ton/ha",
                "ciclo": "120-150 días",
                "precio_referencia": 90000, "unidad_precio": "COP/bulto (50kg)",
            },
        },
    },
    {
        "nombre": "Arroz",
        "nombre_cientifico": "Oryza sativa",
        "descripcion": "Cereal de consumo masivo en Colombia. Principales zonas: Tolima, Meta, Casanare.",
        "icono": "🍚",
        "profundidad_radicular_min_cm": 25,
        "gdd_total_requerido": 1800,
        "dias_ciclo": 125,
        "ficha": {
            "tipo_fuente": "Nacional",
            "fuente": "UPRA, Zonificación para arroz. DANE-EVA, rendimientos municipales.",
            "umbrales": {
                "ph": {"min": 5.0, "max": 6.5, "unidad": "", "fuente": "UPRA"},
                "temperatura": {"min": 22, "max": 30, "unidad": "°C", "fuente": "FAO"},
                "precipitacion": {"min": 800, "max": 2000, "unidad": "mm/ciclo", "fuente": "UPRA"},
                "nitrogeno": {"min": 100, "max": 150, "unidad": "kg/ha", "fuente": "AGROSAVIA"},
            },
            "datos_economicos": {
                "rendimiento_esperado": 5.5, "unidad_rendimiento": "ton/ha",
                "ciclo": "110-140 días",
                "precio_referencia": 180000, "unidad_precio": "COP/carga (125kg)",
            },
        },
    },
    {
        "nombre": "Plátano",
        "nombre_cientifico": "Musa paradisiaca",
        "descripcion": "Alimento básico en Colombia. Principal productor en Urabá y Eje Cafetero.",
        "icono": "🍌",
        "profundidad_radicular_min_cm": 60,
        "gdd_total_requerido": 2100,
        "dias_ciclo": 450,
        "ficha": {
            "tipo_fuente": "Nacional",
            "fuente": "UPRA, Zonificación para plátano. AGROSAVIA.",
            "umbrales": {
                "ph": {"min": 5.5, "max": 7.0, "unidad": "", "fuente": "UPRA"},
                "temperatura": {"min": 20, "max": 30, "unidad": "°C", "fuente": "AGROSAVIA"},
                "precipitacion": {"min": 1500, "max": 2500, "unidad": "mm/año", "fuente": "UPRA"},
                "potasio": {"min": 300, "max": 600, "unidad": "kg/ha/año K₂O", "fuente": "AGROSAVIA"},
            },
            "datos_economicos": {
                "rendimiento_esperado": 12, "unidad_rendimiento": "ton/ha",
                "ciclo": "Perenne (cosecha cada 12-18 meses)",
                "precio_referencia": 60000, "unidad_precio": "COP/racimo",
            },
        },
    },
    {
        "nombre": "Papa",
        "nombre_cientifico": "Solanum tuberosum",
        "descripcion": "Tubérculo de alta producción en clima frío colombiano. Cundinamarca, Boyacá, Nariño.",
        "icono": "🥔",
        "profundidad_radicular_min_cm": 40,
        "gdd_total_requerido": 1300,
        "dias_ciclo": 135,
        "ficha": {
            "tipo_fuente": "Nacional",
            "fuente": "UPRA, Zonificación para papa. AGROSAVIA.",
            "umbrales": {
                "ph": {"min": 5.0, "max": 6.5, "unidad": "", "fuente": "UPRA"},
                "temperatura": {"min": 10, "max": 18, "unidad": "°C", "fuente": "AGROSAVIA"},
                "altitud": {"min": 2500, "max": 3500, "unidad": "msnm", "fuente": "UPRA"},
                "materia_organica": {"min": 5, "max": 15, "unidad": "%", "fuente": "AGROSAVIA"},
                "fosforo": {"min": 100, "max": 200, "unidad": "kg/ha P₂O₅", "fuente": "AGROSAVIA"},
            },
            "datos_economicos": {
                "rendimiento_esperado": 20, "unidad_rendimiento": "ton/ha",
                "ciclo": "120-150 días",
                "precio_referencia": 70000, "unidad_precio": "COP/bulto (50kg)",
            },
        },
    },
]

# ── Cultivos internacionales (FAO GAEZ) — etiqueta "datos internacionales" ──
CULTIVOS_INTERNACIONALES = [
    "Trigo", "Cebada", "Sorgo", "Soya", "Algodón", "Caña de azúcar",
    "Cacao", "Palma de aceite", "Yuca", "Fríjol", "Tomate", "Cebolla",
    "Zanahoria", "Aguacate", "Mango", "Piña", "Naranja", "Limón",
    "Mandarina", "Maracuyá", "Papaya", "Sandía", "Melón", "Uva", "Tabaco",
]

print(f"✅ Seed data listo: {len(CULTIVOS_COLOMBIA)} cultivos Colombia + {len(CULTIVOS_INTERNACIONALES)} internacionales = {len(CULTIVOS_COLOMBIA) + len(CULTIVOS_INTERNACIONALES)} total")
print("   Ejecutar desde la app con: await cargar_seed_data(db_session)")
