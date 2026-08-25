"""Normalización de tramas IoT (ESP32/LoRaWAN) al formato canónico.

Cierra la brecha G2: convierte los nombres de campos del firmware a las
claves de `SensorReading`, aplica conversión de unidades (µS/cm → dS/m)
y factores de calibración por dispositivo.

Nota sobre `humidity`/`temperature`: se registran como **ambientales**
(telemetría del sensor, típico DHT22). Si el firmware mide suelo, debe
enviar `soil_humidity` / `soil_temperature` (se mapean a `humedad` /
`temperatura_suelo`).
"""

# ── Factor de conversión: µS/cm → dS/m ──
US_CM_A_DS_M = 1e-3

# ── Campos del firmware → claves canónicas de SensorReading ──
MAPA_CAMPOS = {
    # Inglés (firmware ESP32)
    "ph": "ph",
    "nitrogen": "nitrogeno",
    "phosphorus": "fosforo",
    "potassium": "potasio",
    "calcium": "calcio",
    "magnesium": "magnesio",
    "sulfur": "azufre",
    "iron": "hierro",
    "manganese": "manganeso",
    "zinc": "zinc",
    "copper": "cobre",
    "boron": "boro",
    "organic_matter": "materia_organica",
    "mo": "materia_organica",
    "texture": "textura",
    "humidity": "humedad_ambiental",          # HR ambiente (DHT22)
    "temperature": "temperatura_ambiental",   # °C ambiente
    "soil_humidity": "humedad",               # humedad de suelo si el firmware la distingue
    "soil_temperature": "temperatura_suelo",
    "conductivity": "conductividad_electrica",  # µS/cm → dS/m (ver normalizar_trama)
    # Aliases cortos
    "n": "nitrogeno",
    "p": "fosforo",
    "k": "potasio",
    "ca": "calcio",
    "mg": "magnesio",
    "s": "azufre",
    "fe": "hierro",
    "mn": "manganeso",
    "zn": "zinc",
    "cu": "cobre",
    "b": "boro",
    "ce": "conductividad_electrica",
    # Español (identidad, ya normalizado)
    "nitrogeno": "nitrogeno",
    "fosforo": "fosforo",
    "potasio": "potasio",
    "calcio": "calcio",
    "magnesio": "magnesio",
    "azufre": "azufre",
    "hierro": "hierro",
    "manganeso": "manganeso",
    "zinc": "zinc",
    "cobre": "cobre",
    "boro": "boro",
    "materia_organica": "materia_organica",
    "cic": "cic",
    "textura": "textura",
    "humedad": "humedad",
    "temperatura_suelo": "temperatura_suelo",
    "conductividad_electrica": "conductividad_electrica",
    "humedad_ambiental": "humedad_ambiental",
    "temperatura_ambiental": "temperatura_ambiental",
}

# Campos de telemetría que NO son variables de suelo
CAMPOS_TELEMETRIA = {"device_id", "rssi", "uptime_s", "firmware", "timestamp"}

VARIABLES_NPK = {"nitrogeno", "fosforo", "potasio"}


def normalizar_trama(raw: dict) -> tuple[dict, list[str]]:
    """Convierte una trama cruda de sensor a payload canónico.

    Args:
        raw: diccionario crudo del firmware (variables en la raíz).

    Returns:
        (payload_canonico, advertencias):
          - payload_canonico: solo claves de SensorReading.
          - advertencias: lista de códigos (ej. "npk_sin_calibrar").
    """
    payload: dict = {}
    advertencias: list[str] = []

    for clave, valor in raw.items():
        if clave in CAMPOS_TELEMETRIA or valor is None:
            continue
        canonica = MAPA_CAMPOS.get(clave)
        if canonica is None:
            # Campo desconocido: se ignora para no ensuciar el modelo
            continue

        if clave == "conductivity" and isinstance(valor, (int, float)):
            # Conversión de unidades: µS/cm → dS/m
            payload[canonica] = round(float(valor) * US_CM_A_DS_M, 4)
        elif isinstance(valor, (int, float)):
            payload[canonica] = float(valor)
        else:
            payload[canonica] = valor

    if VARIABLES_NPK & set(payload):
        advertencias.append("npk_sin_calibrar")

    return payload, advertencias


def aplicar_calibracion(payload: dict, factores: dict | None) -> dict:
    """Aplica factores de calibración NPK por dispositivo (brecha G4).

    Solo se invoca cuando el dispositivo está marcado como calibrado.
    """
    if not factores:
        return payload
    for variable, factor in factores.items():
        if variable in payload and isinstance(payload[variable], (int, float)):
            payload[variable] = round(float(payload[variable]) * float(factor), 4)
    return payload
