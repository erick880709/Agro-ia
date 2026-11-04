#!/usr/bin/env python3
"""Ficha de sitio a partir de coordenadas (formato Google Maps) para Colombia.

Pasos: 1) interpreta y valida coordenadas, 2) resuelve altitud, 3) estima temperatura
media con las ecuaciones de Cenicafe (Chaves & Jaramillo), 4) opcionalmente consulta
SoilGrids para suelo, 5) escribe una ficha JSON reutilizable por aptitud.py.

Reglas de honestidad: el recuadro geografico NO es la frontera de Colombia; el pais solo
se confirma con geocodificacion inversa. SoilGrids es un modelo global (250 m) y no
entrega P, K, Ca, Mg ni micronutrientes. Nada aqui sustituye un analisis de suelo.

Red: usa solo biblioteca estandar. La clave de Google se lee de GOOGLE_MAPS_API_KEY y
nunca se imprime. Con --offline no se hace ninguna llamada de red.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMP_JSON = HERE.parent / "references" / "temperatura-altitud.json"

# (lat_min, lat_max, lon_min, lon_max). Aproximados; NO son la frontera.
CAJAS = {
    "continental": (-4.3, 12.7, -79.1, -66.8),
    "san_andres_providencia": (12.0, 14.8, -82.0, -79.8),
    "malpelo": (3.8, 4.2, -81.8, -81.4),
}
MARGEN_FRONTERA = 0.35  # grados cerca del borde del recuadro continental

GOOGLE_ELEV = "https://maps.googleapis.com/maps/api/elevation/json"
GOOGLE_GEO = "https://maps.googleapis.com/maps/api/geocode/json"
SOILGRIDS = "https://rest.isric.org/soilgrids/v2.0/properties/query"
SOIL_PROPS = ["phh2o", "soc", "nitrogen", "cec", "clay", "sand", "silt"]
SOIL_DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]
SOIL_THICK = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}


# ----------------------------------------------------------------- coordenadas
def _num(s):
    return float(s.replace(",", "."))


def parse_coords(texto):
    """Devuelve (lat, lon, formato). Acepta decimal, DMS de Google Maps y URLs de Maps."""
    t = texto.strip()
    m = re.search(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", t) or \
        re.search(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)", t)
    if m:
        return float(m.group(1)), float(m.group(2)), "url_google_maps"

    dms = re.findall(
        r"(\d+(?:[.,]\d+)?)\s*[°º]\s*(?:(\d+(?:[.,]\d+)?)\s*['′’]\s*)?"
        r"(?:(\d+(?:[.,]\d+)?)\s*[\"″”]\s*)?\s*([NSEWOnsewo])", t)
    if len(dms) == 2:
        vals = []
        for g, mi, se, hemi in dms:
            v = _num(g) + (_num(mi) / 60 if mi else 0) + (_num(se) / 3600 if se else 0)
            if hemi.upper() in ("S", "W", "O"):
                v = -v
            vals.append((hemi.upper(), v))
        (h1, v1), (h2, v2) = vals
        if h1 in ("N", "S") and h2 in ("E", "W", "O"):
            return v1, v2, "dms"
        if h2 in ("N", "S") and h1 in ("E", "W", "O"):
            return v2, v1, "dms"
        raise ValueError("DMS ambiguo: use un par N/S y E/O (W).")

    if ";" in t:  # separador ';' permite coma decimal
        partes = [p.strip() for p in t.split(";") if p.strip()]
        if len(partes) == 2:
            return _num(partes[0]), _num(partes[1]), "decimal"
    nums = re.findall(r"-?\d+(?:\.\d+)?", t)
    if len(nums) == 2:
        return float(nums[0]), float(nums[1]), "decimal"
    raise ValueError("No pude interpretar las coordenadas. Ejemplos: '4.5339, -75.6811' "
                     "o 4°32'02\"N 75°40'52\"W o un enlace de Google Maps.")


def _en_caja(lat, lon, caja):
    a, b, c, d = caja
    return a <= lat <= b and c <= lon <= d


def validar(lat, lon):
    msgs, sugerencias = [], []
    res = {"formato_ok": True, "en_recuadro_colombia": False, "zona_recuadro": None,
           "cerca_de_borde": False, "pais_confirmado": None, "departamento": None}
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        res["formato_ok"] = False
        msgs.append("Coordenadas fuera de rango (lat -90..90, lon -180..180).")
        return res, msgs, sugerencias
    for nombre, caja in CAJAS.items():
        if _en_caja(lat, lon, caja):
            res["en_recuadro_colombia"], res["zona_recuadro"] = True, nombre
            break
    if res["en_recuadro_colombia"]:
        if res["zona_recuadro"] == "continental":
            a, b, c, d = CAJAS["continental"]
            m = MARGEN_FRONTERA
            if lat - a < m or b - lat < m or lon - c < m or d - lon < m:
                res["cerca_de_borde"] = True
                msgs.append("Punto cerca del borde del recuadro: puede estar en un pais vecino.")
        msgs.append("El punto cae en el recuadro de Colombia, que NO es la frontera "
                    "(incluye partes de Venezuela, Ecuador, Peru, Brasil y Panama). "
                    "Confirmar el pais con geocodificacion o con el usuario.")
        return res, msgs, sugerencias
    msgs.append("El punto cae fuera del recuadro geografico de Colombia.")
    for etiqueta, (la, lo) in (("latitud y longitud invertidas", (lon, lat)),
                               ("longitud sin signo negativo (Colombia esta al oeste de Greenwich)", (lat, -lon)),
                               ("latitud con signo equivocado", (-lat, lon))):
        if any(_en_caja(la, lo, c) for c in CAJAS.values()):
            sugerencias.append({"causa_probable": etiqueta, "lat": la, "lon": lo})
    if sugerencias:
        msgs.append("Posible error de captura; ver 'correcciones_sugeridas' y confirmar con el usuario.")
    return res, msgs, sugerencias


# ------------------------------------------------------------------------ red
def http_json(url, params, timeout=20):
    q = urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(f"{url}?{q}", headers={"User-Agent": "agronomo-colombia-skill/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def google_elevation(lat, lon, key):
    d = http_json(GOOGLE_ELEV, {"locations": f"{lat},{lon}", "key": key})
    if d.get("status") != "OK" or not d.get("results"):
        raise RuntimeError(f"Elevation API status={d.get('status')}")
    return float(d["results"][0]["elevation"])


def google_geocode(lat, lon, key):
    d = http_json(GOOGLE_GEO, {"latlng": f"{lat},{lon}", "language": "es", "key": key})
    if d.get("status") != "OK":
        raise RuntimeError(f"Geocoding API status={d.get('status')}")
    pais = depto = None
    for r in d.get("results", []):
        for c in r.get("address_components", []):
            tipos = c.get("types", [])
            if "country" in tipos and not pais:
                pais = c.get("short_name")
            if "administrative_area_level_1" in tipos and not depto:
                depto = c.get("long_name")
    return pais, depto


def parse_soilgrids(d):
    """Convierte la respuesta de SoilGrids a unidades convencionales (usa d_factor)."""
    out = {}
    for capa in d.get("properties", {}).get("layers", []):
        nombre = capa.get("name")
        um = capa.get("unit_measure", {}) or {}
        f = um.get("d_factor") or 1
        unidad = um.get("target_units", "")
        por_prof = {}
        for dep in capa.get("depths", []):
            v = dep.get("values", {}) or {}
            def cv(k):
                x = v.get(k)
                return None if x is None else round(x / f, 3)
            por_prof[dep.get("label")] = {"media": cv("mean"), "q05": cv("Q0.05"), "q95": cv("Q0.95")}
        out[nombre] = {"unidad": unidad, "profundidades": por_prof}
    return out


def soilgrids(lat, lon):
    params = [("lat", lat), ("lon", lon)]
    params += [("property", p) for p in SOIL_PROPS]
    params += [("depth", d) for d in SOIL_DEPTHS]
    params += [("value", v) for v in ("mean", "Q0.05", "Q0.95")]
    return parse_soilgrids(http_json(SOILGRIDS, params, timeout=30))


def media_0_30(capa):
    num = den = 0.0
    for lab, w in SOIL_THICK.items():
        x = (capa["profundidades"].get(lab) or {}).get("media")
        if x is not None:
            num += x * w
            den += w
    return round(num / den, 3) if den else None


# ----------------------------------------------------------------------- clima
def temperatura_estimada(alt, depto, lat):
    cfg = json.loads(TEMP_JSON.read_text(encoding="utf-8"))
    regiones = cfg["regiones"]
    notas = []
    candidatas = cfg["departamento_a_regiones"].get(_norm(depto), None) if depto else None
    if not candidatas:
        candidatas = list(regiones)
        notas.append("Sin departamento: se calcula con las cuatro regiones y se reporta rango. "
                     "Indicar el departamento acota la estimacion.")
    eqs = []
    for k in candidatas:
        r = regiones[k]
        a, b = r["a"], r["b"]
        etiqueta = r["nombre"]
        if k == "andina" and depto and _norm(depto) in ("quindio", "valle del cauca", "cauca") \
                and 2 <= lat <= 5:
            rf = cfg["refinamientos"]["cuenca_cauca_2_5N"]
            if rf["alt_min"] <= alt <= rf["alt_max"]:
                a, b, etiqueta = rf["a"], rf["b"], etiqueta + " - cuenca Cauca 2-5N (refinamiento)"
        t = round(a - b * alt, 1)
        fuera = not (r["alt_min"] <= alt <= r["alt_max"])
        if fuera:
            notas.append(f"Altitud fuera del rango de ajuste de '{k}' "
                         f"({r['alt_min']}-{r['alt_max']} m): extrapolacion.")
        eqs.append({"region": k, "descripcion": etiqueta, "temp_c": t, "extrapolacion": fuera})
    temps = [e["temp_c"] for e in eqs]
    notas.append("Laderas expuestas a las grandes llanuras pueden ser ~1,5-2 C mas frias que las "
                 "interiores a igual altitud (Cenicafe). Eventos El Nino/La Nina cambian el promedio.")
    return {"regiones_candidatas": candidatas, "ecuaciones": eqs,
            "temp_media_estimada_c": round(sum(temps) / len(temps), 1),
            "rango_c": [min(temps), max(temps)], "notas": notas}


def piso_termico(t):
    if t > 24:
        return "calido"
    if t > 18:
        return "templado"
    if t > 12:
        return "frio"
    return "paramo"


# ------------------------------------------------------------------------ main
def construir_ficha(args):
    ficha = {"entrada": None, "advertencias": []}
    if args.coords:
        lat, lon, fmt = parse_coords(args.coords)
        ficha["entrada"] = {"texto": args.coords, "formato": fmt}
    elif args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
        ficha["entrada"] = {"texto": f"{lat},{lon}", "formato": "decimal"}
    else:
        raise ValueError("Indica --coords o --lat y --lon.")
    ficha["coordenadas"] = {"lat": lat, "lon": lon}

    val, msgs, sug = validar(lat, lon)
    ficha["validacion"] = val
    ficha["validacion"]["mensajes"] = msgs
    if sug:
        ficha["validacion"]["correcciones_sugeridas"] = sug

    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    online = (not args.offline) and bool(key) and val["formato_ok"]
    if not args.offline and not key:
        ficha["advertencias"].append("Sin GOOGLE_MAPS_API_KEY: no se consulto Google. "
                                     "Se usa la altitud entregada por el usuario.")

    if online:
        try:
            pais, depto = google_geocode(lat, lon, key)
            val["pais_confirmado"] = (pais == "CO")
            val["departamento"] = depto
            if pais != "CO":
                ficha["validacion"]["mensajes"].append(
                    f"Google ubica el punto en pais '{pais}', no en Colombia.")
        except Exception as e:  # noqa: BLE001
            ficha["advertencias"].append(f"Geocodificacion fallo ({type(e).__name__}).")
    if args.departamento and not val["departamento"]:
        val["departamento"] = args.departamento

    alt = None
    if args.altitud is not None:
        alt = {"valor_m": args.altitud, "fuente": "usuario"}
    elif online:
        try:
            alt = {"valor_m": round(google_elevation(lat, lon, key), 1), "fuente": "google_elevation"}
        except Exception as e:  # noqa: BLE001
            ficha["advertencias"].append(f"Elevation API fallo ({type(e).__name__}).")
    if alt is None:
        ficha["altitud"] = {"valor_m": None, "fuente": "no_disponible"}
        ficha["advertencias"].append("Sin altitud: pedirla al usuario (GPS del celular, Google Earth) "
                                     "o definir GOOGLE_MAPS_API_KEY.")
    else:
        ficha["altitud"] = alt
        if alt["valor_m"] is not None and val["formato_ok"]:
            c = temperatura_estimada(alt["valor_m"], val["departamento"], lat)
            c["piso_termico"] = piso_termico(c["temp_media_estimada_c"])
            c["_fuente"] = "Chaves & Jaramillo (Cenicafe), Avances en Recursos Hidraulicos 6, 1999"
            ficha["clima"] = c
            ficha["clima"]["precipitacion"] = ("No se estima desde coordenadas. Usar estaciones IDEAM, "
                                               "red de Cenicafe (agroclima.cenicafe.org) o dato del usuario.")

    if args.suelo and not args.offline and val["formato_ok"]:
        try:
            s = soilgrids(lat, lon)
            resumen = {}
            for p, capa in s.items():
                resumen[p] = {"unidad": capa["unidad"], "media_0_30cm": media_0_30(capa),
                              "por_profundidad": capa["profundidades"]}
            soc = resumen.get("soc", {}).get("media_0_30cm")
            if soc is not None:
                resumen["materia_organica_aprox_pct"] = round(soc / 10 * 1.724, 1)
            ficha["suelo"] = {"fuente": "SoilGrids 2.0 (ISRIC), 250 m, modelo global",
                              "datos": resumen,
                              "limites": ["Estimacion estadistica: revisar intervalo q05-q95; "
                                          "incertidumbre puede ser alta en montana tropical.",
                                          "No incluye P, K, Ca, Mg, Al ni micronutrientes.",
                                          "MO aprox. = carbono organico x 1,724 (factor convencional).",
                                          "No sustituye el analisis de suelo del lote."]}
        except Exception as e:  # noqa: BLE001
            ficha["suelo"] = {"estado": f"no disponible ({type(e).__name__})"}
    elif args.suelo:
        ficha["suelo"] = {"estado": "no consultado (modo --offline o coordenadas invalidas)"}

    ficha["advertencias"].append("Hipotesis de sitio, no diagnostico: confirmar con analisis de suelo, "
                                 "UPRA/IGAC y asistencia tecnica.")
    return ficha


def imprimir(f):
    c = f["coordenadas"]
    print(f"Coordenadas: {c['lat']:.5f}, {c['lon']:.5f}  (formato: {f['entrada']['formato']})")
    v = f["validacion"]
    estado = "OK" if v["en_recuadro_colombia"] else "REVISAR"
    pc = {True: "confirmado por Google", False: "NO es Colombia", None: "sin confirmar"}[v["pais_confirmado"]]
    print(f"Validacion: {estado} | recuadro Colombia: {v['en_recuadro_colombia']} | pais: {pc}"
          + (f" | departamento: {v['departamento']}" if v["departamento"] else ""))
    for m in v["mensajes"]:
        print(f"  - {m}")
    for s in v.get("correcciones_sugeridas", []):
        print(f"  * Quiza: {s['causa_probable']} -> {s['lat']}, {s['lon']}")
    a = f["altitud"]
    print(f"Altitud: {a['valor_m']} m ({a['fuente']})")
    if "clima" in f:
        cl = f["clima"]
        print(f"Temperatura media estimada: {cl['temp_media_estimada_c']} C "
              f"(rango {cl['rango_c'][0]}-{cl['rango_c'][1]} C) | piso termico: {cl['piso_termico']}")
        for e in cl["ecuaciones"]:
            print(f"    {e['region']:<9} {e['temp_c']} C" + ("  [extrapolacion]" if e["extrapolacion"] else ""))
        for n in cl["notas"]:
            print(f"  - {n}")
    if "suelo" in f:
        s = f["suelo"]
        if "datos" in s:
            d = s["datos"]
            print("Suelo (SoilGrids, 0-30 cm, ponderado):")
            for p in SOIL_PROPS:
                if p in d and d[p]["media_0_30cm"] is not None:
                    print(f"    {p:<9} {d[p]['media_0_30cm']} {d[p]['unidad']}")
            if "materia_organica_aprox_pct" in d:
                print(f"    MO aprox. {d['materia_organica_aprox_pct']} %")
            for l in s["limites"]:
                print(f"  - {l}")
        else:
            print(f"Suelo: {s['estado']}")
    for w in f["advertencias"]:
        print(f"AVISO: {w}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--coords", help="'4.5339, -75.6811' | DMS | enlace de Google Maps")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--altitud", type=float, help="msnm medida o conocida (prevalece sobre Google)")
    p.add_argument("--departamento", help="si no hay geocodificacion; acota la region climatica")
    p.add_argument("--suelo", action="store_true", help="consultar SoilGrids (requiere red)")
    p.add_argument("--offline", action="store_true", help="sin llamadas de red")
    p.add_argument("--salida", help="ruta del JSON de la ficha")
    a = p.parse_args()
    try:
        ficha = construir_ficha(a)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    imprimir(ficha)
    if a.salida:
        Path(a.salida).write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Ficha guardada en {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
