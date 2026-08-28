"""Etapa Discover (11.1) — valida URLs, DOI, versión y términos.

Comprueba disponibilidad HTTP, resuelve DOI, evalúa la política de licencia
(Commercial-use gate) y registra resultados en metadata/discovery.jsonl.
Un fallo en una fuente NO rompe el pipeline (sección 22).

Uso:
    python discover.py [--ids DS01,DS02] [--timeout 20] [--force]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from common import (
    METADATA_DIR,
    append_jsonl,
    get_logger,
    http_head,
    license_action,
    load_catalog,
)

log = get_logger("agrovision.discover")


def resolve_doi(url: str) -> str:
    """Devuelve la URL final tras resolver un DOI (si aplica)."""
    if "doi.org" in url:
        info = http_head(url)
        if info and info.get("final_url"):
            return info["final_url"]
    return url


def discover_one(dataset: dict, timeout: int) -> dict:
    ds_id = dataset.get("id")
    check_url = dataset.get("source_url") or dataset.get("download_url") or ""
    record = {
        "dataset_id": ds_id,
        "name": dataset.get("name"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_url": check_url,
        "license": dataset.get("license"),
        "download_type": dataset.get("download_type"),
        "version": dataset.get("version"),
    }
    if not dataset.get("enabled", True):
        record.update(estado="deshabilitado", detalle="dataset deshabilitado en manifest")
        return record
    resolved = resolve_doi(check_url)
    record["resolved_url"] = resolved
    if "No identificado" in str(check_url) or "No identificado" in str(
        dataset.get("download_url") or ""
    ):
        record.update(estado="source_unavailable", detalle="repositorio único no verificable")
        return record
    if dataset.get("download_type") in ("portal", "mendeley"):
        info = http_head(resolved, timeout=timeout)
        ok = info is not None and info.get("status") in (200, 301, 302, 403)
        record.update(
            estado="portal_ok" if ok else "source_unavailable",
            detalle=(
                "portal: localizar recurso por nombre exacto y validar ficha"
                if ok
                else "portal no responde"
            ),
            http=info,
        )
        return record
    info = http_head(resolved, timeout=timeout)
    ok = info is not None and info.get("status") == 200
    record.update(
        estado="ok" if ok else "source_unavailable",
        detalle="URL responde" if ok else (info or {}).get("error", "sin respuesta"),
        http=info,
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover — valida catálogo de datasets.")
    parser.add_argument("--ids", default="", help="IDs separados por coma (vacíos = todos).")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--force", action="store_true", help="Reescribe discovery.jsonl.")
    args = parser.parse_args()

    salida = METADATA_DIR / "discovery.jsonl"
    if args.force and salida.exists():
        salida.unlink()
    ids = {s.strip().upper() for s in args.ids.split(",") if s.strip()}
    resumen: dict[str, int] = {}
    for ds in load_catalog():
        if ids and ds.get("id") not in ids:
            continue
        record = discover_one(ds, args.timeout)
        append_jsonl(salida, record)
        resumen[record["estado"]] = resumen.get(record["estado"], 0) + 1
        log.info(
            "discover_result",
            extra_fields={
                "dataset_id": record["dataset_id"],
                "estado": record["estado"],
                "license_action": license_action(ds.get("license") or "").get("action"),
            },
        )
    log.info("discover_summary", extra_fields=resumen)
    print(f"Resumen discover: {resumen} → {salida}")


if __name__ == "__main__":
    main()
