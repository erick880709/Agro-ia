"""Vigilancia en vivo de tramas de sensores contra la API de AgroIA.

Muestra cada trama nueva que llega a la plataforma (device_id, finca,
valores, posición del punto de muestreo y calidad) y valida que la
información sea correcta (rangos plausibles por variable).

Uso:
    .venv\\Scripts\\python.exe scripts\\vigilar_sensor.py                  # producción
    .venv\\Scripts\\python.exe scripts\\vigilar_sensor.py --local          # localhost:8000
    .venv\\Scripts\\python.exe scripts\\vigilar_sensor.py --intervalo 5    # cada 5 s
    .venv\\Scripts\\python.exe scripts\\vigilar_sensor.py --fincas <uuid1> <uuid2>

Requiere acceso admin (envía X-User-Role: admin, igual que la UI demo).
Ctrl+C para detener.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

BASE_PRODUCCION = "https://agroia-backend.onrender.com"
BASE_LOCAL = "http://localhost:8000"

# Fincas observadas por defecto: Demo Integral + finca del sensor real
FINCAS_DEFECTO = [
    "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936",
    "22222222-2222-2222-2222-222222222222",
]

# clave → (mínimo, máximo, unidad). Rango de plausibilidad para la alerta.
RANGOS = {
    "ph": (0.0, 14.0, "pH"),
    "conductividad_electrica": (0.0, 20.0, "dS/m"),
    "humedad": (0.0, 100.0, "%"),
    "humedad_ambiental": (0.0, 100.0, "%"),
    "temperatura_suelo": (-10.0, 70.0, "°C"),
    "temperatura_ambiental": (-10.0, 60.0, "°C"),
    "nitrogeno": (0.0, 4000.0, "ppm"),
    "fosforo": (0.0, 4000.0, "ppm"),
    "potasio": (0.0, 4000.0, "ppm"),
}

CLAVES_MOSTRAR = [
    "ph", "conductividad_electrica", "nitrogeno", "fosforo", "potasio",
    "humedad", "temperatura_suelo", "humedad_ambiental",
    "temperatura_ambiental", "materia_organica", "cic",
]


def _f(v):
    try:
        f = float(v)
        return f if f == f else None  # descarta NaN
    except (TypeError, ValueError):
        return None


def pedir(url: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url, headers={"X-User-Role": "admin", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def describir_valores(r: dict) -> str:
    partes = []
    for clave in CLAVES_MOSTRAR:
        v = _f(r.get(clave))
        if v is not None:
            partes.append(f"{clave}={v:g}")
    return " ".join(partes) if partes else "(sin variables)"


def describir_posicion(r: dict) -> str:
    px, py = _f(r.get("pos_x")), _f(r.get("pos_y"))
    if px is not None or py is not None:
        return f" punto=({px:g},{py:g})m"
    return ""


def validar(r: dict) -> list[str]:
    alertas = []
    for clave, (lo, hi, unidad) in RANGOS.items():
        v = _f(r.get(clave))
        if v is not None and not (lo <= v <= hi):
            alertas.append(f"{clave}={v:g} fuera de rango [{lo:g},{hi:g}] {unidad}")
    if r.get("calidad") == "npk_no_calibrado":
        alertas.append("NPK sin calibrar")
    if not any(_f(r.get(c)) is not None for c in RANGOS):
        alertas.append("trama sin variables de suelo")
    return alertas


def main() -> None:
    ap = argparse.ArgumentParser(description="Vigila tramas de sensores en vivo")
    ap.add_argument("--local", action="store_true", help="usar http://localhost:8000")
    ap.add_argument("--intervalo", type=float, default=10.0, help="segundos entre consultas")
    ap.add_argument("--fincas", nargs="*", default=None, help="UUIDs de fincas a vigilar")
    ap.add_argument("--una", action="store_true", help="una sola consulta y salir")
    args = ap.parse_args()

    base = BASE_LOCAL if args.local else BASE_PRODUCCION
    fincas = args.fincas or FINCAS_DEFECTO
    vistos: set[str] = set()
    total = 0
    alertas_total = 0
    sin_datos_desde: float | None = None

    print(f"[VIGILANCIA] {base} - fincas: {', '.join(f[:8] + '…' for f in fincas)}")
    print(f"   intervalo {args.intervalo:g} s · Ctrl+C para detener\n")

    while True:
        nuevas = 0
        try:
            for finca in fincas:
                try:
                    payload = pedir(
                        f"{base}/api/v1/iot/lecturas/{finca}?limite=5"
                    )
                except urllib.error.HTTPError as e:
                    print(f"[{time.strftime('%H:%M:%S')}] [!] finca {finca[:8]}… "
                          f"HTTP {e.code} (¿aún no desplegado?)")
                    continue
                for r in payload.get("data", []):
                    rid = r.get("id")
                    if rid in vistos:
                        continue
                    vistos.add(rid)
                    total += 1
                    nuevas += 1
                    ts = (r.get("ts") or "")[:19].replace("T", " ")
                    alertas = validar(r)
                    estado = "[OK]" if not alertas else "[!]"
                    print(
                        f"[{time.strftime('%H:%M:%S')}] {estado} "
                        f"trama #{total} · {r.get('sensor_id')} → "
                        f"finca {r.get('finca_id', finca)[:8]}…\n"
                        f"            {ts} | {describir_valores(r)}"
                        f"{describir_posicion(r)}"
                    )
                    for a in alertas:
                        alertas_total += 1
                        print(f"            [!] {a}")
            if nuevas:
                sin_datos_desde = None
            else:
                if sin_datos_desde is None:
                    sin_datos_desde = time.time()
                elif time.time() - sin_datos_desde >= 60:
                    print(f"[{time.strftime('%H:%M:%S')}] [espera] sin tramas nuevas "
                          f"en los últimos 60 s")
                    sin_datos_desde = time.time()
        except urllib.error.URLError as e:
            print(f"[{time.strftime('%H:%M:%S')}] [sin conexion]: {e.reason} "
                  f"(reintentando…)")
        except KeyboardInterrupt:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[{time.strftime('%H:%M:%S')}] [ERROR] {type(e).__name__}: {e}")

        if args.una:
            break
        try:
            time.sleep(args.intervalo)
        except KeyboardInterrupt:
            break

    print(f"\n[RESUMEN] Total tramas mostradas: {total} · alertas: {alertas_total}")
    if not args.una:
        print("   vigilancia detenida")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nvigilancia finalizada")
        sys.exit(0)
