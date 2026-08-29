"""Etapa Download (11.2) — descarga originales a raw/ sin alterarlos.

- Archivo temporal `.part` + resume + reintentos exponenciales + SHA-256.
- Adaptadores por `download_type`; nuevos adaptadores son plug-in (RF-02).
- Fuentes que requieren credenciales inexistentes NO se descargan (RF-03):
  quedan con estado `credenciales_faltantes` o `requiere_intervencion`.

Uso:
    python download.py [--ids DS01,DS02] [--dest raw]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from common import (
    METADATA_DIR,
    RAW_DIR,
    append_jsonl,
    get_logger,
    http_download,
    http_head,
    load_catalog,
    sha256_file,
)

log = get_logger("agrovision.download")


def _dest_dir(ds_id: str, version: str) -> Path:
    safe = str(version).replace("/", "_").strip() or "current"
    return RAW_DIR / ds_id / safe


def adapter_http(ds: dict, dest: Path) -> dict:
    url = ds.get("download_url")
    # Sanitizar nombre: quitar query string (p. ej. Zenodo "?download=1"),
    # inválido en nombres de archivo de Windows.
    nombre = url.rstrip("/").split("/")[-1].split("?")[0] or f"{ds['id']}.bin"
    if "." not in nombre.split("/")[-1]:
        # codeload y similares terminan en rama, no en archivo → usar id + .zip
        nombre = f"{ds['id']}.zip"
    out = dest / nombre
    return {"archivos": [http_download(url, out, logger=log)], "destino": dest}


def adapter_zenodo(ds: dict, dest: Path) -> dict:
    url = ds.get("download_url") or ""
    record = ds.get("source_url") or ""
    if url.endswith("?download=1") or ".zip" in url:
        return adapter_http(ds, dest)
    # Zenodo REST: /api/records/<id> → archivos
    record_id = record.rstrip("/").split("/")[-1]
    api = f"https://zenodo.org/api/records/{record_id}"
    info = http_head(api)
    if not info or info.get("status") != 200:
        return {"estado": "requiere_intervencion", "detalle": "API Zenodo no disponible"}
    # Nota: la enumeración completa de archivos requiere parsear JSON de la API.
    return {
        "estado": "requiere_intervencion",
        "detalle": f"Resuelva archivos vía Zenodo REST: {api}",
    }


def adapter_huggingface(ds: dict, dest: Path) -> dict:
    url = ds.get("download_url") or ""
    if "/resolve/" in url:
        filename = url.split("/")[-1]
        return {"archivos": [http_download(url, dest / filename, logger=log)], "destino": dest}
    # Sin archivo concreto: enumerar repo vía API de HF.
    repo = url.rstrip("/").replace("https://huggingface.co/datasets/", "")
    api = f"https://huggingface.co/api/datasets/{repo}"
    info = http_head(api)
    if not info or info.get("status") != 200:
        return {"estado": "source_unavailable", "detalle": "repo HF no accesible"}
    return {
        "estado": "requiere_intervencion",
        "detalle": f"Descargue archivos del repo HF: {api} (snapshot_download o resolve)",
    }


def adapter_kaggle(ds: dict, dest: Path) -> dict:
    kaggle_slug = ds.get("download_url", "").replace("https://www.kaggle.com/ds/", "")
    kaggle_slug = kaggle_slug.strip("/")
    cli = shutil.which("kaggle")
    if not cli:
        cli = shutil.which("kaggle.exe")
    creds_ok = bool(os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"))
    if not creds_ok and not Path.home().joinpath(".kaggle", "kaggle.json").exists():
        return {
            "estado": "credenciales_faltantes",
            "detalle": "Kaggle requiere KAGGLE_USERNAME/KAGGLE_KEY o ~/.kaggle/kaggle.json (RNF-01).",
        }
    if not cli:
        return {
            "estado": "requiere_intervencion",
            "detalle": "CLI de Kaggle no instalada: pip install kaggle y configurar credenciales.",
        }
    result = subprocess.run(
        [cli, "datasets", "download", "-d", kaggle_slug, "-p", str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"estado": "error", "detalle": result.stderr[-300:]}
    return {"estado": "ok", "destino": dest}


def adapter_git(ds: dict, dest: Path) -> dict:
    url = ds.get("download_url") or ds.get("source_url") or ""
    cli = shutil.which("git")
    if not cli:
        return {"estado": "requiere_intervencion", "detalle": "git no disponible en PATH."}
    target = dest / "repo"
    result = subprocess.run(
        [cli, "clone", "--depth", "1", url, str(target)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"estado": "error", "detalle": result.stderr[-300:]}
    return {"estado": "ok", "destino": target}


def adapter_roboflow(ds: dict, dest: Path) -> dict:
    if not os.environ.get("ROBOFLOW_API_KEY"):
        return {
            "estado": "credenciales_faltantes",
            "detalle": "Roboflow requiere ROBOFLOW_API_KEY y fijar versión antes de exportar.",
        }
    return {
        "estado": "requiere_intervencion",
        "detalle": "Seleccione y fije una versión en Roboflow y exporte COCO/YOLO manualmente.",
    }


def adapter_mendeley(ds: dict, dest: Path) -> dict:
    return {
        "estado": "requiere_intervencion",
        "detalle": "Mendeley Data requiere acceso interactivo (Download All desde el portal).",
    }


def adapter_portal(ds: dict, dest: Path) -> dict:
    return {
        "estado": "requiere_intervencion",
        "detalle": "Portal gubernamental: localizar recurso por nombre exacto y validar ficha.",
    }


ADAPTERS = {
    "http": adapter_http,
    "zenodo": adapter_zenodo,
    "huggingface": adapter_huggingface,
    "kaggle": adapter_kaggle,
    "mendeley": adapter_mendeley,
    "git": adapter_git,
    "roboflow": adapter_roboflow,
    "portal": adapter_portal,
}


def descargar(ds: dict) -> dict:
    ds_id = ds.get("id")
    version = ds.get("version") or "current"
    dest = _dest_dir(ds_id, version)
    record = {
        "dataset_id": ds_id,
        "version": version,
        "download_url": ds.get("download_url"),
        "license": ds.get("license"),
        "iniciado_en": datetime.now(timezone.utc).isoformat(),
    }
    if not ds.get("enabled", True):
        record.update(estado="deshabilitado")
        return record
    adapter = ADAPTERS.get(ds.get("download_type", "http"))
    if adapter is None:
        record.update(
            estado="error",
            detalle=f"tipo de descarga desconocido: {ds.get('download_type')}",
        )
        return record
    try:
        result = adapter(ds, dest)
    except Exception as exc:  # noqa: BLE001
        record.update(estado="error", detalle=str(exc))
        return record
    record.update(result)
    # Registrar checksum/tamaño del ZIP descargado cuando exista (RF-04).
    if result.get("archivos"):
        record["archivos"] = result["archivos"]
    if dest.exists():
        zips = list(dest.glob("*.zip"))
        if zips:
            record["checksum"] = sha256_file(zips[0])
            record["size"] = zips[0].stat().st_size
    record.setdefault("estado", "ok")
    return record


def _sanitizar_nombre(nombre: str) -> str:
    """Reemplaza caracteres inválidos en Windows y acorta componentes largos
    (rutas > MAX_PATH fallan en extracción)."""
    partes = []
    for componente in nombre.split("/"):
        for ch in '?*:<>|"':
            componente = componente.replace(ch, "_")
        componente = componente.strip()
        if not componente:
            continue
        ruta = Path(componente)
        tallo, extension = ruta.stem, ruta.suffix
        if len(tallo) > 70:
            tallo = tallo[:70]
        partes.append(tallo + extension)
    return "/".join(partes)


def extraer_zip(record: dict) -> None:
    """Extrae ZIP en staging/ (opcional, controlado por --extraer)."""
    from common import STAGING_DIR

    if record.get("estado") != "ok":
        return
    dest = _dest_dir(record["dataset_id"], record.get("version", "current"))
    for zip_path in dest.glob("*.zip"):
        out = STAGING_DIR / record["dataset_id"]
        try:
            with zipfile.ZipFile(zip_path) as zf:
                for member in zf.infolist():
                    objetivo = out / Path(_sanitizar_nombre(member.filename))
                    if member.is_dir():
                        objetivo.mkdir(parents=True, exist_ok=True)
                        continue
                    objetivo.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as origen, open(objetivo, "wb") as destino:
                        shutil.copyfileobj(origen, destino)
            record["extraido_en"] = str(out)
        except zipfile.BadZipFile as exc:
            record["extraccion"] = f"zip corrupto: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download — descarga originales a raw/.")
    parser.add_argument("--ids", default="", help="IDs separados por coma (vacíos = todos).")
    parser.add_argument("--extraer", action="store_true", help="Extrae ZIPs a staging/.")
    args = parser.parse_args()

    ids = {s.strip().upper() for s in args.ids.split(",") if s.strip()}
    salida = METADATA_DIR / "downloads.jsonl"
    resumen: dict[str, int] = {}
    for ds in load_catalog():
        if ids and ds.get("id") not in ids:
            continue
        if ds.get("download_type") in ("portal", "mendeley", "roboflow") and not ids:
            # Evita tocar portales interactivos en corridas masivas (sección 22).
            continue
        record = descargar(ds)
        if args.extraer:
            extraer_zip(record)
        append_jsonl(salida, record)
        resumen[record["estado"]] = resumen.get(record["estado"], 0) + 1
        log.info(
            "download_result",
            extra_fields={
                "dataset_id": record["dataset_id"],
                "estado": record["estado"],
                "checksum": record.get("checksum"),
            },
        )
    log.info("download_summary", extra_fields=resumen)
    print(f"Resumen download: {resumen} → {salida}")


if __name__ == "__main__":
    main()
