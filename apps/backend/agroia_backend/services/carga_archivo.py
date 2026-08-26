"""Parser de archivos CSV/TXT/JSON con mediciones de sensores (carga manual).

Cubre el caso de pérdida de conexión con los sensores: el usuario exporta
las mediciones a un archivo y la aplicación las lee, normaliza y persiste
igual que una trama en vivo.
"""

import json

from agroia.logging import get_logger

logger = get_logger(__name__)


def _es_flotante(texto: str) -> float | None:
    """Convierte texto a float aceptando decimal español (7,1) e inglés (7.1)."""
    t = (texto or "").strip()
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        try:
            return float(t.replace(",", "."))
        except ValueError:
            return None


def _normalizar_clave(clave: str) -> str:
    clave = clave.strip().lower()
    clave = clave.replace(" ", "_")
    clave = clave.replace("(", "").replace(")", "")
    clave = clave.replace("°", "")
    clave = clave.replace("-", "_")
    return clave


def _pares_a_frame(pares: list[tuple[str, str]]) -> dict:
    frame: dict = {}
    for clave, valor in pares:
        clave = _normalizar_clave(clave)
        if not clave:
            continue
        num = _es_flotante(valor)
        frame[clave] = num if num is not None else str(valor).strip()
    return frame


def _extraer_device_id(pares: list[tuple[str, str]]) -> str | None:
    for clave, valor in pares:
        if _normalizar_clave(clave) in ("device_id", "deviceid", "id_dispositivo"):
            return str(valor).strip() or None
    return None


def _parsear_csv(texto: str) -> tuple[list[dict], str | None]:
    import csv
    import io

    # Delimitador: ';' si predomina sobre ','
    sep = ";" if texto.count(";") > texto.count(",") else ","
    reader = csv.reader(io.StringIO(texto), delimiter=sep)
    filas = [
        [c.strip() for c in f]
        for f in reader
        if any(c.strip() for c in f)
    ]
    if not filas:
        raise ValueError("El archivo CSV no tiene filas con datos.")

    # Forma ancha: cabecera de variables + una o varias filas de datos.
    # Con varias filas se interpreta como muestreo en cuadrícula (x, y + variables).
    if len(filas[0]) > 2:
        cabecera = filas[0]
        frames = []
        for fila_datos in filas[1:]:
            pares = [
                (cabecera[i], fila_datos[i])
                for i in range(min(len(cabecera), len(fila_datos)))
            ]
            frames.append(_pares_a_frame(pares))
        device = _extraer_device_id([(c, "") for c in cabecera])
        return frames, device

    # Forma pares: variable,valor (una o varias filas)
    pares = [(f[0], f[1]) if len(f) > 1 else (f[0], "") for f in filas]
    return [_pares_a_frame(pares)], _extraer_device_id(pares)


def _parsear_txt(texto: str) -> tuple[list[dict], str | None]:
    pares = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or linea.startswith("//"):
            continue
        for sep in ("=", ":", "\t"):
            if sep in linea:
                clave, _, valor = linea.partition(sep)
                pares.append((clave.strip(), valor.strip()))
                break
    if not pares:
        raise ValueError("El archivo TXT no tiene pares clave=valor reconocibles.")
    return [_pares_a_frame(pares)], _extraer_device_id(pares)


def parsear_archivo_sensor(contenido: str) -> tuple[list[dict], str | None, str]:
    """Detecta el formato del archivo y devuelve la(s) trama(s) cruda(s).

    Args:
        contenido: texto decodificado del archivo.

    Returns:
        (frames, device_id_archivo, formato) donde formato ∈ {"json","csv","txt"}
        y `frames` es una lista (una trama por muestra; los archivos con
        varias filas/objetos representan el muestreo en cuadrícula del lote).
    """
    texto = contenido.strip()
    if not texto:
        raise ValueError("El archivo está vacío.")

    if texto.startswith("{") or texto.startswith("["):
        data = json.loads(texto)
        if isinstance(data, list):
            if not data:
                raise ValueError("El JSON está vacío.")
            frames = [
                {_normalizar_clave(str(k)): v for k, v in item.items()}
                for item in data if isinstance(item, dict)
            ]
            if not frames:
                raise ValueError("El JSON debe ser una lista de objetos con variables del sensor.")
            return frames, frames[0].get("device_id"), "json"
        if not isinstance(data, dict):
            raise ValueError("El JSON debe ser un objeto con variables del sensor.")
        frame = {_normalizar_clave(str(k)): v for k, v in data.items()}
        return [frame], frame.get("device_id"), "json"

    if "," in texto or ";" in texto:
        frames, device = _parsear_csv(texto)
        return frames, device, "csv"

    frames, device = _parsear_txt(texto)
    return frames, device, "txt"


def decodificar_contenido(raw: bytes) -> str:
    """Decodifica bytes del archivo con varios encodings tolerantes."""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")
