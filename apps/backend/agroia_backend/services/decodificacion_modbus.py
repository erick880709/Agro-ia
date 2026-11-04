"""Decodificación fiel de los registros Modbus del sensor JXBS-3001-NPK-RS.

Sensor de suelo 7-en-1 (RS485, Modbus RTU 9600 8N1, función 0x03). Este
módulo cierra la brecha H-12 del RFP-AGROIA-003: conservar el **valor crudo**
de cada registro y escalarlo con la escala y el signo correctos (la
temperatura llega como entero de 16 bits en complemento a dos).

Registros:

| Registro | Variable            | Escala  | Unidad  | Notas                       |
|----------|---------------------|---------|---------|-----------------------------|
| 0x0006   | pH                  | 0,01    | —       | rango 3–9                   |
| 0x0012   | Humedad (VWC)       | 0,1     | %       | volumétrica, no HR          |
| 0x0013   | Temperatura         | 0,1     | °C      | entero 16 bits CON signo    |
| 0x0015   | CE                  | 1       | µS/cm   | resolución 10 µS/cm         |
| 0x001E   | N                   | 1       | mg/kg   | indicativo                  |
| 0x001F   | P                   | 1       | mg/kg   | indicativo                  |
| 0x0020   | K                   | 1       | mg/kg   | indicativo                  |
"""

from __future__ import annotations

# Conversión µS/cm → dS/m (coincide con normalizacion_iot.US_CM_A_DS_M)
US_CM_A_DS_M = 1e-3

# Variables que el sensor debe exponer para pasar la prueba de aceptación
# de variante (TT-03): pH, CE, N, P y K.
VARIABLES_ACEPTACION = ("ph", "ce_uscm", "nitrogeno", "fosforo", "potasio")

REGISTROS: dict[int, dict] = {
    0x0006: {"variable": "ph", "escala": 0.01, "unidad": "", "desc": "pH"},
    0x0012: {"variable": "humedad", "escala": 0.1, "unidad": "%", "desc": "Humedad VWC"},
    0x0013: {
        "variable": "temperatura_suelo",
        "escala": 0.1,
        "unidad": "°C",
        "desc": "Temperatura del suelo",
        "con_signo": True,
    },
    0x0015: {"variable": "ce_uscm", "escala": 1.0, "unidad": "µS/cm", "desc": "Conductividad eléctrica"},
    0x001E: {"variable": "nitrogeno", "escala": 1.0, "unidad": "mg/kg", "desc": "Nitrógeno"},
    0x001F: {"variable": "fosforo", "escala": 1.0, "unidad": "mg/kg", "desc": "Fósforo"},
    0x0020: {"variable": "potasio", "escala": 1.0, "unidad": "mg/kg", "desc": "Potasio"},
}


def _normalizar_clave_registro(clave) -> int | None:
    """Acepta claves int o str ('0x0006', '6', '0006') y devuelve el int."""
    if isinstance(clave, int):
        return clave
    if isinstance(clave, str):
        texto = clave.strip().lower()
        try:
            return int(texto, 16) if texto.startswith("0x") else int(texto)
        except ValueError:
            return None
    return None


def a_entero_con_signo(valor: int) -> int:
    """Interpreta un entero de 16 bits como con signo (complemento a dos).

    Ej. 0xFF9B → -101 (equivale a -10,1 °C con escala 0,1).
    """
    valor &= 0xFFFF
    return valor - 0x10000 if valor & 0x8000 else valor


def decodificar_registros(registros: dict) -> dict:
    """Decodifica un mapa registro→valor crudo a variables escaladas.

    Returns:
        dict keyed by variable: {
            "valor_crudo": int,
            "valor_escalado": float,
            "unidad": str,
            "desc": str,
        }
        Los registros desconocidos se ignoran; los valores None se omiten.
    """
    salida: dict = {}
    for clave, valor_crudo in registros.items():
        reg = _normalizar_clave_registro(clave)
        if reg is None or reg not in REGISTROS or valor_crudo is None:
            continue
        try:
            crudo = int(valor_crudo)
        except (TypeError, ValueError):
            continue
        info = REGISTROS[reg]
        if info.get("con_signo"):
            numerico = a_entero_con_signo(crudo)
        else:
            numerico = crudo
        salida[info["variable"]] = {
            "valor_crudo": crudo,
            "valor_escalado": round(numerico * info["escala"], 4),
            "unidad": info["unidad"],
            "desc": info["desc"],
        }
    return salida


def decodificar_para_sensor(registros: dict) -> dict:
    """Decodifica y entrega un payload compatible con SensorReading.

    Convierte la CE a dS/m (µS/cm ÷ 1000) y conserva el valor crudo por
    registro en `valor_crudo` (JSON serializable, claves en hex).
    """
    deco = decodificar_registros(registros)
    payload: dict = {}
    valor_crudo: dict = {}

    for reg, info in REGISTROS.items():
        var = deco.get(info["variable"])
        if var is None:
            continue
        clave_hex = f"0x{reg:04X}"
        valor_crudo[clave_hex] = var["valor_crudo"]

    if "ph" in deco:
        payload["ph"] = deco["ph"]["valor_escalado"]
    if "humedad" in deco:
        # VWC: se etiqueta como humedad de suelo, nunca como HR.
        payload["humedad"] = deco["humedad"]["valor_escalado"]
    if "temperatura_suelo" in deco:
        payload["temperatura_suelo"] = deco["temperatura_suelo"]["valor_escalado"]
    if "ce_uscm" in deco:
        payload["conductividad_electrica"] = round(
            deco["ce_uscm"]["valor_escalado"] * US_CM_A_DS_M, 4
        )
    for var in ("nitrogeno", "fosforo", "potasio"):
        if var in deco:
            payload[var] = deco[var]["valor_escalado"]

    if valor_crudo:
        payload["valor_crudo"] = valor_crudo

    return payload


def verificar_variante(registros: dict) -> dict:
    """Prueba de aceptación de variante (TT-03 / RF-005).

    Confirma que el equipo expone pH, CE, N, P y K antes de darlo de alta.
    """
    deco = decodificar_registros(registros)
    presentes = [v for v in VARIABLES_ACEPTACION if v in deco]
    faltantes = [v for v in VARIABLES_ACEPTACION if v not in presentes]
    return {
        "aceptado": not faltantes,
        "variables_presentes": presentes,
        "variables_faltantes": faltantes,
        "decodificadas": deco,
    }


def crc16_modbus(data: bytes) -> int:
    """CRC-16 Modbus RTU (polinomio 0xA001), valor entero.

    Se transmite en little-endian (byte bajo primero).
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def verificar_crc_trama(trama: bytes) -> bool:
    """True si la trama Modbus RTU (con CRC final) es íntegra."""
    if len(trama) < 4:
        return False
    datos, crc_recibido = trama[:-2], trama[-2:]
    crc = crc16_modbus(datos)
    return crc_recibido == bytes((crc & 0xFF, (crc >> 8) & 0xFF))


def construir_trama(dispositivo: int, registro_inicio: int, cantidad: int) -> bytes:
    """Construye una trama de lectura (función 0x03) con CRC.

    Formato: [dir] [0x03] [reg_hi] [reg_lo] [cant_hi] [cant_lo] [crc_lo] [crc_hi]
    """
    trama = bytes((
        dispositivo & 0xFF,
        0x03,
        (registro_inicio >> 8) & 0xFF,
        registro_inicio & 0xFF,
        (cantidad >> 8) & 0xFF,
        cantidad & 0xFF,
    ))
    crc = crc16_modbus(trama)
    return trama + bytes((crc & 0xFF, (crc >> 8) & 0xFF))
