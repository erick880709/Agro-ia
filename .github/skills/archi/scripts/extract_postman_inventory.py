#!/usr/bin/env python3
"""Extrae un inventario normalizado de una coleccion Postman (v2.0/v2.1).

Uso:
    python extract_postman_inventory.py <coleccion.postman_collection.json> [--format md|csv]

No agrega dependencias externas: solo usa la libreria estandar. El objetivo es
que ningun endpoint de la coleccion quede sin inventariar por omision al
redactar un `14.xx.N-Mapeo-Integracion_EXT-xx_<Sistema>.md` (ver
`references/guia-mapeo-integraciones-externas.md`).

Salida por cada request encontrado (recorre carpetas anidadas):
    Carpeta | Nombre | Metodo | URL | Tipo de auth | Tiene ejemplo de respuesta
"""

import argparse
import csv
import json
import sys

# En consolas Windows con codepage no UTF-8, imprimir tildes/guiones largos
# puede fallar o mostrarse mal. Forzamos UTF-8 en stdout/stderr cuando el
# runtime lo permite (Python 3.7+); si no, seguimos sin romper la ejecucion.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


def _auth_type(item_auth, parent_auth):
    """Devuelve el tipo de auth efectivo de un request (propio o heredado)."""
    auth = item_auth or parent_auth
    if not auth:
        return "sin auth declarada"
    if isinstance(auth, dict):
        return auth.get("type", "desconocido")
    return "desconocido"


def _resolve_url(url_field):
    """Normaliza el campo `url` de Postman, que puede ser string u objeto."""
    if url_field is None:
        return "(sin URL)"
    if isinstance(url_field, str):
        return url_field
    if isinstance(url_field, dict):
        raw = url_field.get("raw")
        if raw:
            return raw
        host = url_field.get("host") or []
        path = url_field.get("path") or []
        host_str = ".".join(host) if isinstance(host, list) else str(host)
        path_str = "/".join(path) if isinstance(path, list) else str(path)
        return f"{host_str}/{path_str}".strip("/")
    return "(URL no reconocida)"


def _walk(items, folder_path, parent_auth, rows):
    """Recorre recursivamente items/carpetas de una coleccion Postman."""
    for entry in items:
        name = entry.get("name", "(sin nombre)")
        if "item" in entry:
            # Es una carpeta: puede traer su propia auth heredable.
            folder_auth = entry.get("auth", parent_auth)
            new_path = folder_path + [name]
            _walk(entry["item"], new_path, folder_auth, rows)
            continue

        request = entry.get("request", {})
        if isinstance(request, str):
            # Formato antiguo donde `request` es solo la URL.
            method, url = "GET", request
            item_auth = None
        else:
            method = request.get("method", "?")
            url = _resolve_url(request.get("url"))
            item_auth = request.get("auth")

        has_example = bool(entry.get("response"))
        rows.append(
            {
                "carpeta": " / ".join(folder_path) if folder_path else "(raiz)",
                "nombre": name,
                "metodo": method,
                "url": url,
                "auth": _auth_type(item_auth, parent_auth),
                "tiene_ejemplo_respuesta": "si" if has_example else "no",
            }
        )


def extract(collection_path):
    with open(collection_path, "r", encoding="utf-8") as f:
        collection = json.load(f)

    if "item" not in collection:
        raise ValueError(
            "El archivo no parece una coleccion Postman valida (falta la clave 'item')."
        )

    root_auth = collection.get("auth")
    rows = []
    _walk(collection["item"], [], root_auth, rows)
    return rows


def print_markdown(rows, collection_name):
    total = len(rows)
    sin_ejemplo = sum(1 for r in rows if r["tiene_ejemplo_respuesta"] == "no")
    print(f"# Inventario Postman — {collection_name}")
    print()
    print(f"Total de requests encontrados: **{total}**. Sin ejemplo de respuesta guardado: **{sin_ejemplo}**.")
    print()
    print("| Carpeta | Nombre | Metodo | URL | Auth | Ejemplo de respuesta |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print(
            f"| {r['carpeta']} | {r['nombre']} | {r['metodo']} | `{r['url']}` "
            f"| {r['auth']} | {r['tiene_ejemplo_respuesta']} |"
        )
    print()
    print(
        "> Compara este total contra lo documentado en `14.xx.N`. Si hay una diferencia, "
        "registrala como incertidumbre (`12`) o riesgo (`21`) — no la omitas en silencio."
    )


def print_csv(rows):
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=["carpeta", "nombre", "metodo", "url", "auth", "tiene_ejemplo_respuesta"],
    )
    writer.writeheader()
    for r in rows:
        writer.writerow(r)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("collection", help="Ruta al archivo .postman_collection.json")
    parser.add_argument(
        "--format", choices=["md", "csv"], default="md", help="Formato de salida (default: md)"
    )
    args = parser.parse_args()

    try:
        rows = extract(args.collection)
    except (OSError, ValueError) as exc:
        # json.JSONDecodeError es subclase de ValueError; no hace falta listarla aparte.
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("ADVERTENCIA: no se encontro ningun request en la coleccion.", file=sys.stderr)

    if args.format == "csv":
        print_csv(rows)
    else:
        print_markdown(rows, args.collection)


if __name__ == "__main__":
    main()
