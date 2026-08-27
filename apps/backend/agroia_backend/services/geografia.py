"""Geografía y validación de fincas (Colombia).

Fuente de verdad del catálogo departamento → municipios (espejo de
`apps/frontend-web/departamentos.js`) y de la cadena de validación que se
ejecuta al guardar una finca:

    1. ¿Departamento existe?
    2. ¿Municipio pertenece al departamento?
    3. ¿Coordenadas válidas?
    4. ¿Coordenadas coinciden aproximadamente con el municipio?
    5. ¿Área razonable?
    6. ¿Ubicación con precisión aceptable?
    7. ✅ FINCA CREADA

También calcula área/perímetro de un polígono GeoJSON (proyección
equirectangular, suficiente para predios).
"""
import math

from agroia.logging import get_logger

logger = get_logger(__name__)

# ── Catálogo departamento → municipios (espejo de departamentos.js) ──
CATALOGO: dict[str, list[str]] = {
    "Amazonas": ["Leticia", "Puerto Nariño"],
    "Antioquia": ["Medellín", "Abejorral", "Andes", "Apartadó", "Bello", "Caucasia", "Chigorodó", "Envigado", "Itagüí", "La Ceja", "Marinilla", "Rionegro", "Santa Fe de Antioquia", "Sonsón", "Turbo", "Urrao", "Yarumal"],
    "Arauca": ["Arauca", "Saravena", "Tame"],
    "Atlántico": ["Barranquilla", "Baranoa", "Malambo", "Puerto Colombia", "Sabanalarga", "Soledad"],
    "Bogotá D.C.": ["Bogotá"],
    "Bolívar": ["Cartagena", "Carmen de Bolívar", "Magangué", "Mompox", "San Juan Nepomuceno", "Turbaco"],
    "Boyacá": ["Tunja", "Chiquinquirá", "Duitama", "Garagoa", "Moniquirá", "Paipa", "Puerto Boyacá", "Sogamoso", "Villa de Leyva"],
    "Caldas": ["Manizales", "Aguadas", "Anserma", "Chinchiná", "La Dorada", "Neira", "Riosucio", "Salamina", "Villamaría"],
    "Caquetá": ["Florencia", "El Doncello", "San Vicente del Caguán"],
    "Casanare": ["Yopal", "Aguazul", "Monterrey", "Paz de Ariporo", "Villanueva"],
    "Cauca": ["Popayán", "El Tambo", "Guapi", "Miranda", "Santander de Quilichao", "Silvia", "Timbío"],
    "Cesar": ["Valledupar", "Aguachica", "Bosconia", "Chiriguaná", "Curumaní"],
    "Chocó": ["Quibdó", "Acandí", "Istmina", "Nuquí"],
    "Córdoba": ["Montería", "Cereté", "Chinú", "Lorica", "Montelíbano", "Planeta Rica", "Sahagún"],
    "Cundinamarca": ["Fusagasugá", "Anapoima", "Chía", "Choachí", "Facatativá", "Girardot", "La Mesa", "Mosquera", "Pacho", "Soacha", "Ubaté", "Villeta", "Zipaquirá"],
    "Guainía": ["Inírida"],
    "Guaviare": ["San José del Guaviare"],
    "Huila": ["Neiva", "Garzón", "Gigante", "La Plata", "Palermo", "Pitalito", "San Agustín", "Timaná"],
    "La Guajira": ["Riohacha", "Albania", "Dibulla", "Maicao", "San Juan del Cesar", "Uribia"],
    "Magdalena": ["Santa Marta", "Ciénaga", "El Banco", "Fundación", "Plato"],
    "Meta": ["Villavicencio", "Acacías", "Cumaral", "Granada", "Puerto López", "Restrepo", "San Martín"],
    "Nariño": ["Pasto", "Ipiales", "La Unión", "Sandoná", "Tumaco", "Túquerres"],
    "Norte de Santander": ["Cúcuta", "Chinácota", "Los Patios", "Ocaña", "Pamplona", "Villa del Rosario"],
    "Putumayo": ["Mocoa", "Orito", "Puerto Asís", "Sibundoy", "Valle del Guamuez"],
    "Quindío": ["Armenia", "Buenavista", "Calarcá", "Circasia", "Córdoba", "Filandia", "Génova", "La Tebaida", "Montenegro", "Pijao", "Quimbaya", "Salento"],
    "Risaralda": ["Pereira", "Apía", "Belén de Umbría", "Dosquebradas", "La Virginia", "Marsella", "Mistrató", "Santa Rosa de Cabal", "Santuario"],
    "San Andrés y Providencia": ["San Andrés", "Providencia"],
    "Santander": ["Bucaramanga", "Barichara", "Barrancabermeja", "Floridablanca", "Girón", "Málaga", "Piedecuesta", "San Gil", "San Vicente de Chucurí", "Socorro", "Vélez"],
    "Sucre": ["Sincelejo", "Corozal", "Ovejas", "San Marcos", "Sincé", "Tolú"],
    "Tolima": ["Ibagué", "Chaparral", "El Espinal", "Honda", "Líbano", "Mariquita", "Melgar", "Purificación", "Rovira"],
    "Valle del Cauca": ["Cali", "Buenaventura", "Buga", "Caicedonia", "Cartago", "El Cerrito", "Jamundí", "Palmira", "Pradera", "Roldanillo", "Sevilla", "Tuluá", "Yumbo"],
    "Vaupés": ["Mitú"],
    "Vichada": ["Puerto Carreño"],
}

# ── Centroides aproximados (lat, lng) para verificación de proximidad ──
CENTROIDES: dict[str, tuple[float, float]] = {
    # Capitales y ciudades principales
    "Leticia": (-4.2153, -69.9406), "Medellín": (6.2442, -75.5812),
    "Arauca": (7.0847, -70.7580), "Barranquilla": (10.9685, -74.7813),
    "Bogotá": (4.7110, -74.0721), "Cartagena": (10.3910, -75.4794),
    "Tunja": (5.5446, -73.3584), "Manizales": (5.0703, -75.5138),
    "Florencia": (1.6144, -75.6062), "Yopal": (5.3378, -72.3959),
    "Popayán": (2.4448, -76.6147), "Valledupar": (10.4631, -73.2532),
    "Quibdó": (5.6947, -76.6610), "Montería": (8.7479, -75.8814),
    "Fusagasugá": (4.3452, -74.3618), "Girardot": (4.3035, -74.8020),
    "Inírida": (3.8683, -67.9239), "San José del Guaviare": (2.5679, -72.6450),
    "Neiva": (2.9273, -75.2819), "Pitalito": (1.8537, -76.0507),
    "Garzón": (2.1960, -75.6278), "San Agustín": (1.8790, -76.2685),
    "Riohacha": (11.5444, -72.9072), "Maicao": (11.3784, -72.2414),
    "Santa Marta": (11.2408, -74.1990), "Villavicencio": (4.1420, -73.6266),
    "Acacías": (3.9869, -73.7581), "Pasto": (1.2136, -77.2811),
    "Ipiales": (0.8252, -77.6398), "Tumaco": (1.8067, -78.7647),
    "Cúcuta": (7.8939, -72.5078), "Ocaña": (8.2377, -73.3560),
    "Pamplona": (7.3761, -72.6479), "Mocoa": (1.1520, -76.6466),
    # Eje cafetero (zona demo)
    "Armenia": (4.5339, -75.6811), "Calarcá": (4.5306, -75.6408),
    "Circasia": (4.6191, -75.6359), "Filandia": (4.6741, -75.6597),
    "La Tebaida": (4.4550, -75.7891), "Montenegro": (4.5664, -75.7512),
    "Quimbaya": (4.6230, -75.7624), "Salento": (4.6375, -75.5705),
    "Buenavista": (4.3590, -75.7400), "Génova": (4.3160, -75.7700),
    "Pijao": (4.3320, -75.7060), "Córdoba": (4.3920, -75.6880),
    "Pereira": (4.8133, -75.6961), "Dosquebradas": (4.8360, -75.6670),
    "Santa Rosa de Cabal": (4.8680, -75.6210), "Marsella": (4.9370, -75.7390),
    "Chinchiná": (4.9825, -75.6036), "Salamina": (5.4080, -75.4890),
    "Aguadas": (5.6100, -75.4540), "Villamaría": (5.0450, -75.5150),
    "Anserma": (5.2390, -75.7830), "Riosucio": (5.4220, -75.7030),
    # Tolima / Huila / Cundinamarca (zona demo)
    "Ibagué": (4.4389, -75.2322), "El Espinal": (4.1480, -74.8840),
    "Melgar": (4.2030, -74.6410), "Honda": (5.1950, -74.7370),
    "Mariquita": (5.1970, -74.8900), "Líbano": (4.9210, -75.0620),
    "Chaparral": (3.7240, -75.4830), "Purificación": (3.8590, -74.9310),
    "La Plata": (2.3910, -75.8900), "Gigante": (2.3850, -75.5450),
    "Timaná": (1.9700, -75.9340), "Zipaquirá": (5.0229, -74.0048),
    "Soacha": (4.5870, -74.2210), "Facatativá": (4.8140, -74.3550),
    "Chía": (4.8600, -74.0580), "Mosquera": (4.7050, -74.2300),
    "La Mesa": (4.6300, -74.4630), "Anapoima": (4.5500, -74.5390),
    "Villeta": (5.0130, -74.4730), "Ubaté": (5.3100, -73.8170),
    # Valle / Cauca / otros
    "Cali": (3.4516, -76.5320), "Palmira": (3.5390, -76.3030),
    "Buga": (3.9020, -76.2980), "Tuluá": (4.0840, -76.2000),
    "Cartago": (4.7460, -75.9120), "Caicedonia": (4.3320, -75.8270),
    "Sevilla": (4.2680, -75.9360), "Buenaventura": (3.8830, -77.0310),
    "Jamundí": (3.2610, -76.5400), "Santander de Quilichao": (3.0100, -76.4860),
    "Bucaramanga": (7.1193, -73.1227), "Floridablanca": (7.0622, -73.0860),
    "Girón": (7.0680, -73.1700), "Piedecuesta": (6.9890, -73.0500),
    "Barrancabermeja": (7.0653, -73.8547), "San Gil": (6.5550, -73.1330),
    "Málaga": (6.6990, -72.7320), "Barichara": (6.6360, -73.2250),
    "Socorro": (6.4690, -73.2620), "Vélez": (6.0130, -73.6730),
    "Duitama": (5.8265, -73.0201), "Sogamoso": (5.7169, -72.9339),
    "Paipa": (5.7800, -73.1170), "Chiquinquirá": (5.6140, -73.8170),
    "Villa de Leyva": (5.6330, -73.5230), "Sincelejo": (9.3047, -75.3978),
    "Corozal": (9.3160, -75.2940), "Tolú": (9.5250, -75.5810),
    "San Andrés": (12.5847, -81.7006), "Mitú": (1.2530, -70.2360),
    "Puerto Carreño": (6.1850, -67.4920), "Aguachica": (8.3120, -73.6170),
    "Lorica": (9.2322, -75.8143), "Cereté": (8.8850, -75.7930),
    "Montelíbano": (7.9800, -75.4210), "Planeta Rica": (8.4110, -75.5840),
    "Sahagún": (8.9490, -75.4410), "Chinú": (9.1080, -75.3980),
    "Ciénaga": (11.0063, -74.2476), "Fundación": (10.5200, -74.1840),
    "El Banco": (8.9970, -73.9750), "Plato": (9.7920, -74.7830),
    "Soledad": (10.9177, -74.7646), "Malambo": (10.8590, -74.7740),
    "Sabanalarga": (10.6300, -74.9210), "Puerto Colombia": (10.9910, -74.9550),
    "Baranoa": (10.7960, -74.9170), "Istmina": (5.1610, -76.6840),
    "Nuquí": (5.7100, -77.2700), "Guapi": (2.5680, -77.8600),
    "Rionegro": (6.1553, -75.3740), "Apartadó": (7.8846, -76.6259),
    "Turbo": (8.0913, -76.7267), "Bello": (6.3380, -75.5620),
    "Envigado": (6.1760, -75.5870), "Itagüí": (6.1660, -75.6130),
    "La Ceja": (6.0310, -75.4330), "Marinilla": (6.1740, -75.3360),
    "Yarumal": (6.9630, -75.4170), "Abejorral": (5.7880, -75.4270),
    "Saravena": (6.9530, -71.8700), "Tame": (6.4600, -71.7300),
    "Paz de Ariporo": (5.8800, -71.8930), "Aguazul": (5.1720, -72.5460),
    "Monterrey": (4.8780, -72.8980), "Villanueva": (4.6090, -72.9300),
    "Mompox": (9.2420, -74.4240), "Carmen de Bolívar": (9.7170, -75.1210),
    "Uribia": (11.7140, -72.2660), "Dibulla": (11.2720, -73.3100),
    "San Juan del Cesar": (10.7690, -73.0030), "Albania": (11.1600, -72.5930),
    "La Unión": (1.6040, -77.1300), "Sandoná": (1.2860, -77.4680),
    "Túquerres": (1.0870, -77.6180), "Orito": (0.6670, -76.8730),
    "Puerto Asís": (0.5050, -76.5000), "Sibundoy": (1.2030, -76.9190),
    "Valle del Guamuez": (0.4520, -76.9260), "Los Patios": (7.8380, -72.5130),
    "Chinácota": (7.6080, -72.6050), "Villa del Rosario": (7.8350, -72.4740),
    "Curumaní": (9.2000, -73.5430), "Bosconia": (9.9680, -73.8890),
    "Chiriguaná": (9.3620, -73.6040), "San Marcos": (8.6610, -75.1290),
    "Sincé": (9.2430, -75.1470), "Ovejas": (9.5310, -75.2260),
    "San Vicente de Chucurí": (6.8800, -73.4100),
}

# ── Constantes de validación ──
RADIO_MUNICIPIO_KM = 50.0       # tolerancia coordenadas ↔ municipio
AREA_MIN_HA = 0.01
AREA_MAX_HA = 100_000.0
PRECISION_MAX_M = 100.0         # >100 m → rechazo
PRECISION_WARN_M = 50.0         # 50–100 m → advertencia
R_TIERRA_M = 6_371_000.0


# ── Utilidades geométricas ──

def distancia_haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia en metros entre dos puntos (fórmula de Haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R_TIERRA_M * math.asin(math.sqrt(a))


def _proyectar(lat: float, lng: float, lat0: float) -> tuple[float, float]:
    """Proyección equirectangular centrada en lat0 (metros)."""
    x = lng * math.cos(math.radians(lat0)) * 111_320.0
    y = lat * 110_574.0
    return x, y


def calcular_geometria_geojson(geometria: dict | None) -> tuple[float | None, float | None]:
    """Área (ha) y perímetro (m) de un polígono GeoJSON.

    Acepta `{"type": "Polygon", "coordinates": [[[lng, lat], …]]}`.
    Retorna (area_ha, perimetro_m) o (None, None) si no hay anillo válido.
    """
    if not geometria or geometria.get("type") not in ("Polygon", "polygon"):
        return None, None
    anillos = geometria.get("coordinates") or []
    if not anillos:
        return None, None
    # Tolerar anillo plano [[lng,lat], …] además de [[[lng,lat], …]]
    if len(anillos) >= 3 and anillos[0] and not isinstance(anillos[0][0], (list, tuple)):
        anillos = [anillos]
    if not anillos[0] or len(anillos[0]) < 3:
        return None, None
    anillo = anillos[0]
    puntos = [(float(p[1]), float(p[0])) for p in anillo if len(p) >= 2]  # (lat, lng)
    if len(puntos) < 3:
        return None, None
    lat0 = sum(p[0] for p in puntos) / len(puntos)
    xy = [_proyectar(lat, lng, lat0) for lat, lng in puntos]
    # Área por fórmula de Gauss (shoelace)
    area_m2 = 0.0
    for i in range(len(xy)):
        x1, y1 = xy[i]
        x2, y2 = xy[(i + 1) % len(xy)]
        area_m2 += x1 * y2 - x2 * y1
    area_m2 = abs(area_m2) / 2.0
    # Perímetro por Haversine (cierra el anillo si no está cerrado)
    perimetro = 0.0
    for i in range(len(puntos)):
        p1 = puntos[i]
        p2 = puntos[(i + 1) % len(puntos)]
        perimetro += distancia_haversine_m(p1[0], p1[1], p2[0], p2[1])
    return round(area_m2 / 10_000.0, 4), round(perimetro, 1)


# ── Cadena de validación al guardar finca ──

def validar_creacion_finca(
    departamento: str | None,
    municipio: str | None,
    lat: float | None,
    lng: float | None,
    area_ha: float | None,
    precision_m: float | None,
) -> tuple[list[dict], list[str], list[str]]:
    """Ejecuta la cadena de validación de la finca.

    Returns:
        (pasos, errores, advertencias): cada paso es
        {paso, estado: ok|error|warn, mensaje}.
    """
    pasos: list[dict] = []
    errores: list[str] = []
    advertencias: list[str] = []

    dep = (departamento or "").strip()
    mun = (municipio or "").strip()

    # 1. ¿Departamento existe?
    if dep not in CATALOGO:
        pasos.append({"paso": 1, "estado": "error",
                      "mensaje": f"El departamento '{dep}' no existe en el catálogo de Colombia."})
        errores.append("DEPARTAMENTO_INVALIDO")
    else:
        pasos.append({"paso": 1, "estado": "ok", "mensaje": f"Departamento '{dep}' válido."})

        # 2. ¿Municipio pertenece al departamento?
        if mun and mun not in CATALOGO[dep]:
            pasos.append({"paso": 2, "estado": "error",
                          "mensaje": f"El municipio '{mun}' no pertenece al departamento '{dep}'."})
            errores.append("MUNICIPIO_NO_PERTENECE")
        elif mun:
            pasos.append({"paso": 2, "estado": "ok",
                          "mensaje": f"Municipio '{mun}' pertenece a '{dep}'."})
        else:
            pasos.append({"paso": 2, "estado": "warn",
                          "mensaje": "No se indicó municipio."})
            advertencias.append("MUNICIPIO_SIN_REGISTRAR")

    # 3. ¿Coordenadas válidas?
    if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        pasos.append({"paso": 3, "estado": "error",
                      "mensaje": "Coordenadas inválidas o fuera de rango WGS84."})
        errores.append("COORDENADAS_INVALIDAS")
    else:
        pasos.append({"paso": 3, "estado": "ok",
                      "mensaje": f"Coordenadas válidas ({lat:g}, {lng:g})."})

        # 4. ¿Coordenadas coinciden aproximadamente con el municipio?
        if mun and mun in CENTROIDES:
            c_lat, c_lng = CENTROIDES[mun]
            dist_km = distancia_haversine_m(lat, lng, c_lat, c_lng) / 1000.0
            if dist_km > RADIO_MUNICIPIO_KM:
                pasos.append({"paso": 4, "estado": "error",
                              "mensaje": (f"Las coordenadas están a {dist_km:.0f} km del centro de "
                                          f"'{mun}': no coinciden con el municipio declarado.")})
                errores.append("COORDENADAS_FUERA_MUNICIPIO")
            else:
                pasos.append({"paso": 4, "estado": "ok",
                              "mensaje": (f"Coordenadas a {dist_km:.1f} km del centro de "
                                          f"'{mun}' (dentro del umbral de {RADIO_MUNICIPIO_KM:.0f} km).")})
        else:
            pasos.append({"paso": 4, "estado": "warn",
                          "mensaje": "Municipio sin centroide en el catálogo: no se pudo verificar la proximidad."})
            advertencias.append("PROXIMIDAD_NO_VERIFICADA")

    # 5. ¿Área razonable?
    if area_ha is None:
        pasos.append({"paso": 5, "estado": "warn",
                      "mensaje": "No se declaró área; se podrá completar después."})
        advertencias.append("AREA_SIN_DECLARAR")
    elif not (AREA_MIN_HA <= area_ha <= AREA_MAX_HA):
        pasos.append({"paso": 5, "estado": "error",
                      "mensaje": (f"Área declarada {area_ha:g} ha fuera del rango razonable "
                                  f"({AREA_MIN_HA:g}–{AREA_MAX_HA:g} ha).")})
        errores.append("AREA_NO_RAZONABLE")
    else:
        pasos.append({"paso": 5, "estado": "ok",
                      "mensaje": f"Área declarada {area_ha:g} ha dentro del rango razonable."})

    # 6. ¿Ubicación con precisión aceptable?
    if precision_m is None:
        pasos.append({"paso": 6, "estado": "ok",
                      "mensaje": "Sin dato de precisión (fuente manual/enlace): se acepta."})
    elif precision_m > PRECISION_MAX_M:
        pasos.append({"paso": 6, "estado": "error",
                      "mensaje": f"Precisión GPS de {precision_m:g} m es insuficiente (máx. {PRECISION_MAX_M:g} m)."})
        errores.append("PRECISION_INSUFICIENTE")
    elif precision_m > PRECISION_WARN_M:
        pasos.append({"paso": 6, "estado": "warn",
                      "mensaje": f"Precisión GPS de {precision_m:g} m es aceptable pero mejorable (≤ {PRECISION_WARN_M:g} m ideal)."})
        advertencias.append("PRECISION_MEDIA")
    else:
        pasos.append({"paso": 6, "estado": "ok",
                      "mensaje": f"Precisión GPS de ±{precision_m:g} m aceptable."})

    return pasos, errores, advertencias
