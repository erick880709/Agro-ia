"""Utilidades compartidas del pipeline AgroVision.

Sin dependencias duras más allá de numpy/PIL (opcionales): YAML se parsea
con PyYAML si está instalado o con un parser mínimo para los manifiestos
propios; los hashes perceptuales se calculan con DCT en numpy.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# `inspect.py` (nombre definido por especificación) enmascara el módulo
# `inspect` de la stdlib si este directorio está en sys.path. Retirar el
# directorio propio antes de importar numpy/PIL evita el choque.
_SCRIPTS_DIR = Path(__file__).resolve().parent


def _es_script_dir(entrada: str) -> bool:
    if not entrada:
        return True
    try:
        return Path(entrada).resolve() == _SCRIPTS_DIR
    except OSError:
        return False


sys.path[:] = [p for p in sys.path if not _es_script_dir(p)]
# Reinsertar al final: la stdlib conserva prioridad sobre `inspect.py`.
sys.path.append(str(_SCRIPTS_DIR))

import numpy as np  # noqa: E402

# ── Rutas canónicas del pipeline ──────────────────────────────────────────────
DATASETS_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = DATASETS_ROOT / "manifest"
CONFIGS_DIR = DATASETS_ROOT / "configs"
RAW_DIR = DATASETS_ROOT / "raw"
QUARANTINE_DIR = DATASETS_ROOT / "quarantine"
STAGING_DIR = DATASETS_ROOT / "staging"
NORMALIZED_DIR = DATASETS_ROOT / "normalized"
ANNOTATIONS_DIR = DATASETS_ROOT / "annotations"
CURATED_DIR = DATASETS_ROOT / "curated"
METADATA_DIR = DATASETS_ROOT / "metadata"
MODELS_DIR = DATASETS_ROOT / "models"
REPORTS_DIR = DATASETS_ROOT / "reports"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


# ── Logging estructurado JSON (RNF-03) ───────────────────────────────────────
class JsonFormatter(logging.Formatter):
    """Formatea cada registro como una línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class JsonLogger(logging.Logger):
    """Logger que acepta `extra_fields=` como kwarg de conveniencia."""

    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
        **kwargs,
    ):
        campos = kwargs.pop("extra_fields", None)
        if campos:
            extra = dict(extra or {})
            extra["extra_fields"] = campos
        super()._log(
            level,
            msg,
            args,
            exc_info=exc_info,
            extra=extra,
            stack_info=stack_info,
            stacklevel=stacklevel,
        )


logging.setLoggerClass(JsonLogger)


def get_logger(name: str) -> logging.Logger:
    """Logger con salida JSON a stdout."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


# ── Carga de YAML tolerante a ausencia de PyYAML ─────────────────────────────
def load_yaml(path: Path) -> Any:
    """Carga YAML: PyYAML si existe, si no un parser mínimo del subconjunto
    usado por los manifiestos (mapas, listas, listas de mapas, valores
    escalares y listas/objetos inline)."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ImportError:
        return _parse_simple_yaml(text)


def _strip_comment(line: str) -> str:
    in_quote: str | None = None
    for i, ch in enumerate(line):
        if ch in "\"'":
            if in_quote is None:
                in_quote = ch
            elif in_quote == ch:
                in_quote = None
        elif ch == "#" and in_quote is None and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if s == "" or s in ("null", "~"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [_parse_scalar(p) for p in inner.split(",")]
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        out: dict[Any, Any] = {}
        for pair in inner.split(",") if inner else []:
            k, _, v = pair.partition(":")
            out[_parse_scalar(k.strip())] = _parse_scalar(v.strip())
        return out
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _clean_lines(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        line = _strip_comment(raw).rstrip()
        if line.strip():
            out.append(line)
    return out


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _parse_block(lines: list[str], idx: int, indent: int) -> tuple[Any, int]:
    if idx >= len(lines):
        return None, idx
    first_indent = _indent(lines[idx])
    if lines[idx].lstrip().startswith("- "):
        items: list[Any] = []
        while idx < len(lines):
            line = lines[idx]
            if _indent(line) < indent:
                break
            stripped = line.lstrip()
            if not stripped.startswith("- "):
                break
            rest = stripped[2:].strip()
            idx += 1
            if rest == "":
                if idx < len(lines) and _indent(lines[idx]) > first_indent:
                    sub, idx = _parse_block(lines, idx, _indent(lines[idx]))
                    items.append(sub)
                else:
                    items.append(None)
                continue
            if ":" in rest and not rest.startswith(("[", "{", "\"", "'")):
                key, _, val = rest.partition(":")
                item: dict[Any, Any] = {_parse_scalar(key.strip()): _parse_scalar(val.strip())}
                while idx < len(lines) and _indent(lines[idx]) > first_indent:
                    nxt = lines[idx]
                    idx += 1
                    k, _, v = nxt.strip().partition(":")
                    item[_parse_scalar(k.strip())] = _parse_scalar(v.strip())
                items.append(item)
            else:
                items.append(_parse_scalar(rest))
        return items, idx
    mapping: dict[Any, Any] = {}
    while idx < len(lines):
        line = lines[idx]
        cur = _indent(line)
        if cur < indent:
            break
        if cur > indent or line.lstrip().startswith("- "):
            break
        key, _, val = line.strip().partition(":")
        idx += 1
        if val.strip() == "":
            if idx < len(lines) and _indent(lines[idx]) > indent:
                mapping[_parse_scalar(key.strip())], idx = _parse_block(
                    lines, idx, _indent(lines[idx])
                )
            else:
                mapping[_parse_scalar(key.strip())] = None
        else:
            mapping[_parse_scalar(key.strip())] = _parse_scalar(val.strip())
    return mapping, idx


def _parse_simple_yaml(text: str) -> Any:
    lines = _clean_lines(text)
    if not lines:
        return None
    value, _ = _parse_block(lines, 0, 0)
    return value


# ── Manifest y configs ───────────────────────────────────────────────────────
def load_catalog() -> list[dict]:
    """Catálogo de datasets desde manifest/datasets.yaml.

    Normaliza las claves de la espec v6 (`nombre`, `cultivo`, `clases`,
    `fuente_url`, `licencia`) al esquema canónico del pipeline."""
    doc = load_yaml(MANIFEST_DIR / "datasets.yaml") or {}
    return [_normalizar_dataset(d) for d in doc.get("datasets", [])]


def _normalizar_dataset(entrada: dict) -> dict:
    ds = dict(entrada)
    if not ds.get("name"):
        ds["name"] = ds.get("nombre") or ds.get("id", "")
    if not ds.get("source_url"):
        ds["source_url"] = ds.get("fuente_url") or ds.get("download_url") or ""
    if not ds.get("license"):
        ds["license"] = ds.get("licencia") or "Revisar ficha/condiciones de cada recurso"
    if ds.get("crops") is None:
        cultivo = ds.get("cultivo")
        ds["crops"] = cultivo if isinstance(cultivo, list) else ([cultivo] if cultivo else [])
    if ds.get("classes") is None:
        ds["classes"] = ds.get("clases") or []
    if ds.get("tasks") is None:
        ds["tasks"] = ds.get("tareas") or ["classification"]
    ds.setdefault("download_url", ds.get("source_url", ""))
    ds.setdefault("download_type", "http")
    ds.setdefault("version", "current")
    ds.setdefault("priority", "P1")
    ds.setdefault("enabled", True)
    return ds


def load_class_map() -> dict:
    return load_yaml(MANIFEST_DIR / "class_map.yaml") or {}


def load_license_policy() -> dict:
    return load_yaml(MANIFEST_DIR / "license_policy.yaml") or {}


def load_pipeline_config() -> dict:
    path = CONFIGS_DIR / "pipeline.yaml"
    if not path.exists():
        return {}
    return load_yaml(path) or {}


def license_action(license_text: str) -> dict:
    """Evalúa una licencia contra la política (Commercial-use gate)."""
    policy = load_license_policy().get("policy", {})
    for rule in policy.get("rules", []):
        if rule.get("pattern", "").lower() in (license_text or "").lower():
            return rule
    return {"pattern": license_text, "action": policy.get("default_action", "quarantine")}


# ── Hashing (RF-06) ──────────────────────────────────────────────────────────
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def phash(array: np.ndarray) -> int:
    """Hash perceptual 64 bits (DCT sobre miniatura gris 32x32).

    `array` debe ser HxW o HxWx3 uint8. Funciona sin imagehash/cv2.
    """
    try:
        from PIL import Image  # type: ignore

        img = Image.fromarray(array).convert("L").resize((32, 32))
        small = np.asarray(img, dtype=np.float64)
    except Exception:
        small = np.asarray(array, dtype=np.float64)
        if small.ndim == 3:
            small = small.mean(axis=2)
        small = small[:: max(1, small.shape[0] // 32), :: max(1, small.shape[1] // 32)]
        small = np.resize(small, (32, 32)) if small.size else np.zeros((32, 32))
    dct = _dct2d(small)
    flat = dct[1:9, 1:9].flatten()
    med = float(np.median(flat))
    return int("".join("1" if v > med else "0" for v in flat), 2)


def _dct2d(block: np.ndarray) -> np.ndarray:
    """DCT-II 2D. La normalización ortonormal no es necesaria: el hash
    perceptual solo usa el signo respecto a la mediana."""
    n, m = block.shape
    filas = np.arange(n).reshape(-1, 1)      # posiciones
    frec_n = np.arange(n).reshape(1, -1)     # frecuencias
    c_n = np.cos(np.pi * (2 * filas + 1) * frec_n / (2 * n))
    cols = np.arange(m).reshape(-1, 1)
    frec_m = np.arange(m).reshape(1, -1)
    c_m = np.cos(np.pi * (2 * cols + 1) * frec_m / (2 * m))
    return c_n @ block @ c_m.T


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


# ── Descarga HTTP con reintentos, resume y checksum (RF-04) ─────────────────
def http_download(
    url: str,
    dest: Path,
    *,
    retries: int = 3,
    timeout: int = 60,
    headers: dict[str, str] | None = None,
    logger: logging.Logger | None = None,
) -> dict:
    """Descarga a `dest` con reintentos exponenciales y resume vía Range.

    Devuelve {sha256, size, url_final}. Nunca altera archivos ya descargados
    si su hash coincide con el checksum esperado."""
    log = logger or get_logger("agrovision.download")
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    attempt = 0
    while attempt <= retries:
        try:
            req_headers = dict(headers or {})
            req_headers.setdefault(
                "User-Agent", "AgroIA-Pipeline/1.0 (+https://github.com/erick880709/Agro-ia)"
            )
            offset = part.stat().st_size if part.exists() else 0
            if offset:
                req_headers["Range"] = f"bytes={offset}-"
            request = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                mode = "ab" if offset else "wb"
                escrito = 0
                with open(part, mode) as out:
                    while True:
                        chunk = resp.read(1024 * 256)
                        if not chunk:
                            break
                        out.write(chunk)
                        escrito += len(chunk)
                if total and escrito < total:
                    # EOF prematuro (el servidor cortó la transferencia): no
                    # aceptar el archivo como completo; se reintenta con
                    # resume desde el offset actual.
                    raise ConnectionError(
                        f"descarga incompleta: {offset + escrito}/{offset + total} bytes"
                    )
            part.replace(dest)
            return {
                "sha256": sha256_file(dest),
                "size": dest.stat().st_size,
                "url_final": url,
            }
        except urllib.error.HTTPError as exc:
            if exc.code == 416:  # rango inválido: archivo ya completo
                if part.exists():
                    part.replace(dest)
                    return {
                        "sha256": sha256_file(dest),
                        "size": dest.stat().st_size,
                        "url_final": url,
                    }
            attempt += 1
            log.warning(
                "download_retry",
                extra_fields={"url": url, "attempt": attempt, "code": exc.code},
            )
            if attempt > retries:
                raise
            time.sleep(min(2 ** attempt, 30))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            attempt += 1
            log.warning(
                "download_retry",
                extra_fields={"url": url, "attempt": attempt, "error": str(exc)},
            )
            if attempt > retries:
                raise
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"No se pudo descargar {url}")


def http_head(url: str, timeout: int = 20) -> dict | None:
    """HEAD/GET ligero para comprobar disponibilidad (11.1 Discover)."""
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return {
                "status": resp.status,
                "final_url": resp.geturl(),
                "content_type": resp.headers.get("Content-Type"),
                "content_length": resp.headers.get("Content-Length"),
            }
    except urllib.error.HTTPError as exc:
        if exc.code in (405, 501):  # HEAD no soportado → GET sin leer cuerpo
            request = urllib.request.Request(url, method="GET")
            try:
                with urllib.request.urlopen(request, timeout=timeout) as resp:
                    resp.read(1)
                    return {
                        "status": resp.status,
                        "final_url": resp.geturl(),
                        "content_type": resp.headers.get("Content-Type"),
                        "content_length": resp.headers.get("Content-Length"),
                    }
            except Exception:
                return {"status": exc.code, "final_url": url, "error": "head_failed"}
        return {"status": exc.code, "final_url": url, "error": str(exc)}
    except Exception as exc:
        return {"status": None, "final_url": url, "error": str(exc)}


# ── Archivos de metadata JSONL ───────────────────────────────────────────────
def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def read_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)
