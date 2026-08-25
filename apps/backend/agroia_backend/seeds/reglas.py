"""Seed data para reglas agronómicas del sistema experto (UC1 + UC2).

Fuentes: UPRA, Cenicafé, AGROSAVIA y referencias técnicas de fertilidad de
suelos tropicales. Las variables usan los valores del enum `VariableSuelo`.

⚠️ Interpretación de nutrientes: los sensores IoT reportan N/P/K en ppm
(concentración en suelo), mientras que las fichas técnicas expresan dosis
de fertilización (kg/ha). Los umbrales N/P/K de este módulo son rangos de
referencia para lecturas de sensor y deben calibrarse con análisis de
laboratorio por finca (ver la acción de cada regla).

Ejecución: vía `python load_seeds.py` (carga cultivos + reglas juntos).
"""

# ── Reglas universales (cultivo_id=NULL): aplican a todos los cultivos ──
REGLAS_UNIVERSALES = [
    {
        "variable": "pH",
        "min": 5.0,
        "max": 7.5,
        "accion": "Corregir acidez con encalado (cal dolomita) si pH < 5.0, o alcalinidad incorporando materia orgánica ácida si pH > 7.5.",
        "prioridad": "Media",
        "fuente": "UPRA - aptitud general",
    },
    {
        "variable": "MO",
        "min": 3.0,
        "max": 20.0,
        "accion": "Mantener la materia orgánica entre 3-20%: incorporar compost o abonos verdes si es baja; reducir aportes orgánicos si es excesiva.",
        "prioridad": "Baja",
        "fuente": "Referencia técnica - suelos tropicales",
    },
    {
        "variable": "CE",
        "min": None,
        "max": 2.0,
        "accion": "Conductividad eléctrica elevada: lavar el suelo con riego abundante y revisar la calidad del agua de riego.",
        "prioridad": "Alta",
        "fuente": "Referencia técnica - salinidad",
    },
    {
        "variable": "CIC",
        "min": 10.0,
        "max": 40.0,
        "accion": "CIC fuera de rango: mejorar la capacidad de intercambio incorporando materia orgánica y arcillas si es baja.",
        "prioridad": "Baja",
        "fuente": "Referencia técnica - fertilidad",
    },
    {
        "variable": "humedad",
        "min": 40.0,
        "max": 80.0,
        "accion": "Ajustar riego para mantener la humedad entre 40-80% de capacidad de campo.",
        "prioridad": "Media",
        "fuente": "Referencia técnica - riego",
    },
]

# ── Reglas por cultivo (umbrales alineados con seeds/cultivos.py) ──
REGLAS_POR_CULTIVO = {
    "Café": [
        {
            "variable": "pH",
            "min": 5.5, "max": 6.5,
            "accion": "Ajustar pH al rango 5.5-6.5: encalado dolomítico si es ácido o yeso agrícola si es alcalino.",
            "prioridad": "Critica", "fuente": "Cenicafé 2007",
        },
        {
            "variable": "N",
            "min": 200, "max": 400,
            "accion": "Nitrógeno fuera del rango objetivo (200-400): ajustar plan de fertilización nitrogenada fraccionada según Cenicafé.",
            "prioridad": "Alta", "fuente": "Cenicafé",
        },
        {
            "variable": "P",
            "min": 30, "max": 75,
            "accion": "Fósforo fuera del rango objetivo (30-75): aplicar DAP o roca fosfórica en hoyado o en banda.",
            "prioridad": "Alta", "fuente": "Cenicafé",
        },
        {
            "variable": "K",
            "min": 100, "max": 300,
            "accion": "Potasio fuera del rango objetivo (100-300): aplicar KCl según la etapa del cultivo.",
            "prioridad": "Alta", "fuente": "Cenicafé",
        },
        {
            "variable": "MO",
            "min": 8, "max": 20,
            "accion": "Materia orgánica fuera de 8-20%: incorporar pulpa de café compostada.",
            "prioridad": "Media", "fuente": "Cenicafé 2007",
        },
        {
            "variable": "humedad",
            "min": 60, "max": 80,
            "accion": "Mantener humedad entre 60-80% de capacidad de campo.",
            "prioridad": "Media", "fuente": "Wintgens 2009",
        },
        {
            "variable": "temperatura_suelo",
            "min": 18, "max": 24,
            "accion": "Temperatura de suelo fuera de 18-24°C: revisar sombrío y cobertura vegetal.",
            "prioridad": "Baja", "fuente": "Arcila et al. 2007",
        },
    ],
    "Maíz": [
        {
            "variable": "pH",
            "min": 5.5, "max": 7.0,
            "accion": "Ajustar pH al rango 5.5-7.0 con encalado o enmiendas.",
            "prioridad": "Critica", "fuente": "UPRA",
        },
        {
            "variable": "N",
            "min": 120, "max": 180,
            "accion": "Nitrógeno: plan AGROSAVIA 120-180 kg/ha (urea fraccionada en V3-V6).",
            "prioridad": "Alta", "fuente": "AGROSAVIA",
        },
        {
            "variable": "P",
            "min": 40, "max": 80,
            "accion": "Fósforo: 40-80 kg/ha P2O5 aplicado en siembra.",
            "prioridad": "Alta", "fuente": "AGROSAVIA",
        },
        {
            "variable": "K",
            "min": 60, "max": 120,
            "accion": "Potasio: 60-120 kg/ha K2O fraccionado.",
            "prioridad": "Alta", "fuente": "AGROSAVIA",
        },
    ],
    "Arroz": [
        {
            "variable": "pH",
            "min": 5.0, "max": 6.5,
            "accion": "Ajustar pH al rango 5.0-6.5 con encalado.",
            "prioridad": "Critica", "fuente": "UPRA",
        },
        {
            "variable": "N",
            "min": 100, "max": 150,
            "accion": "Nitrógeno: 100-150 kg/ha según etapa de macollamiento.",
            "prioridad": "Alta", "fuente": "AGROSAVIA",
        },
    ],
    "Plátano": [
        {
            "variable": "pH",
            "min": 5.5, "max": 7.0,
            "accion": "Ajustar pH al rango 5.5-7.0.",
            "prioridad": "Critica", "fuente": "UPRA",
        },
        {
            "variable": "K",
            "min": 300, "max": 600,
            "accion": "Potasio: 300-600 kg/ha/año K2O (cultivo muy demandante de K).",
            "prioridad": "Alta", "fuente": "AGROSAVIA",
        },
    ],
    "Papa": [
        {
            "variable": "pH",
            "min": 5.0, "max": 6.5,
            "accion": "Ajustar pH al rango 5.0-6.5.",
            "prioridad": "Critica", "fuente": "UPRA",
        },
        {
            "variable": "MO",
            "min": 5, "max": 15,
            "accion": "Materia orgánica fuera de 5-15%: incorporar compost antes de siembra.",
            "prioridad": "Media", "fuente": "AGROSAVIA",
        },
        {
            "variable": "P",
            "min": 100, "max": 200,
            "accion": "Fósforo: 100-200 kg/ha P2O5 en siembra.",
            "prioridad": "Alta", "fuente": "AGROSAVIA",
        },
    ],
}
