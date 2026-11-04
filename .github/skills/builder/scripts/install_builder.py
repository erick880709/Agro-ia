"""Install a self-contained Builder package without overwriting local edits."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile


RECEIPT = ".builder-installation.json"
DIRECTORIES = {"references", "scripts", "evaluations", "tests", "assets", "agents"}
SKIP = {"__pycache__", ".pytest_cache"}


class PackageError(ValueError):
    """The package or destination cannot be safely reconciled."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reject_links(path: Path) -> None:
    """Reject symlinks and Windows reparse points, including junctions."""
    for item in (path, *path.parents):
        if item.is_symlink():
            raise PackageError(f"Symbolic link is not supported: {item}")
        if item.exists():
            attributes = getattr(item.lstat(), "st_file_attributes", 0)
            if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                raise PackageError(f"Reparse point is not supported: {item}")


def valid_relative(name: str) -> bool:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        return False
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return name == "SKILL.md" or (len(parts) > 1 and parts[0] in DIRECTORIES)


def collect(source: Path) -> dict[str, bytes]:
    reject_links(source)
    if not source.is_dir():
        raise PackageError(f"Missing package directory: {source}")
    files: dict[str, bytes] = {}

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir()):
            if path.name in SKIP or path.suffix in {".pyc", ".pyo"}:
                continue
            reject_links(path)
            if path.is_dir():
                walk(path)
            elif path.is_file():
                files[path.relative_to(source).as_posix()] = path.read_bytes()
            else:
                raise PackageError(f"Unsupported package entry: {path}")

    entry = source / "SKILL.md"
    reject_links(entry)
    if not entry.is_file():
        raise PackageError("Package requires SKILL.md")
    files["SKILL.md"] = entry.read_bytes()
    for directory in sorted(DIRECTORIES):
        path = source / directory
        reject_links(path)
        if path.exists():
            if not path.is_dir():
                raise PackageError(f"Expected a directory: {path}")
            walk(path)
    if len({name.casefold() for name in files}) != len(files):
        raise PackageError("Package has case-insensitive filename collisions")
    for name, data in files.items():
        if not valid_relative(name):
            raise PackageError(f"Invalid package path: {name}")
        if not name.endswith(".md"):
            continue
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise PackageError(f"Markdown must be UTF-8: {name}") from error
        for link in re.findall(r"\]\(([^)]+)\)", content):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link) or link.startswith("#"):
                continue
            target = (source / PurePosixPath(name).parent / link.split("#")[0]).resolve()
            if not target.is_relative_to(source):
                raise PackageError(f"Reference escapes package: {name}: {link}")
            if target.relative_to(source).as_posix() not in files:
                raise PackageError(f"Missing bundled reference: {name}: {link}")
    return files


def read_receipt(destination: Path) -> dict[str, str]:
    path = destination / RECEIPT
    reject_links(path)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PackageError(f"Missing or invalid installation receipt: {path}") from error
    if not isinstance(receipt, dict) or receipt.get("schema_version") != 1:
        raise PackageError("Unsupported installation receipt")
    files = receipt.get("files")
    if not isinstance(files, dict) or "SKILL.md" not in files:
        raise PackageError("Receipt has no valid file inventory")
    for name, sha in files.items():
        if not valid_relative(name) or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise PackageError("Receipt contains an invalid path or hash")
    if len({name.casefold() for name in files}) != len(files):
        raise PackageError("Receipt has case-insensitive filename collisions")
    return files


def check_existing(destination: Path, recorded: dict[str, str]) -> None:
    for name, sha in recorded.items():
        path = destination / name
        reject_links(path)
        if not path.is_file() or digest(path.read_bytes()) != sha:
            raise PackageError(f"Managed file missing or locally modified: {path}")


def normalize_paths(source: Path, destination: Path) -> tuple[Path, Path]:
    source = Path(os.path.abspath(source))
    destination = Path(os.path.abspath(destination))
    reject_links(source)
    reject_links(destination)
    source, destination = source.resolve(), destination.resolve()
    if source.is_relative_to(destination) or destination.is_relative_to(source):
        raise PackageError("Source and destination must not overlap")
    if destination.exists() and not destination.is_dir():
        raise PackageError("Destination is not a directory")
    return source, destination


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    reject_links(path)
    fd, temporary = tempfile.mkstemp(prefix=".builder-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(source: Path, destination: Path, update: bool = False) -> dict:
    source, destination = normalize_paths(source, destination)
    material = collect(source)
    wanted = {name: digest(data) for name, data in sorted(material.items())}
    recorded: dict[str, str] = {}
    if (destination / RECEIPT).exists():
        recorded = read_receipt(destination)
        check_existing(destination, recorded)
        if recorded == wanted:
            return {"status": "unchanged", "files": len(wanted), "destination": str(destination)}
        if not update:
            raise PackageError("Installed package differs; use --update after reviewing the source")
        if set(recorded) - set(wanted):
            raise PackageError("Update retires managed files; use a new destination or resolve migration explicitly")
    elif destination.exists() and any(destination.iterdir()):
        raise PackageError("New installation requires an empty destination")

    # Complete preflight before writing any package file.
    for name in material:
        path = destination / name
        reject_links(path)
        for parent in path.parents:
            if parent == destination:
                break
            if parent.exists() and not parent.is_dir():
                raise PackageError(f"Destination parent is a file: {parent}")
        if name not in recorded and path.exists():
            raise PackageError(f"New package file collides with local content: {path}")
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in material.items():
        if recorded.get(name) != wanted[name]:
            write_atomic(destination / name, data)
    receipt = {"schema_version": 1, "files": wanted}
    write_atomic(destination / RECEIPT, (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    verify(source, destination)
    return {"status": "updated" if recorded else "installed", "files": len(wanted), "destination": str(destination)}


def verify(source: Path, destination: Path) -> dict:
    source, destination = normalize_paths(source, destination)
    wanted = {name: digest(data) for name, data in collect(source).items()}
    recorded = read_receipt(destination)
    check_existing(destination, recorded)
    if recorded != wanted:
        raise PackageError("Installed version does not match this source package")
    return {"status": "verified", "files": len(recorded), "destination": str(destination)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "verify"))
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    if args.action == "verify" and args.update:
        parser.error("--update only applies to install")
    source = Path(__file__).resolve().parents[1]
    try:
        result = install(source, args.destination, args.update) if args.action == "install" else verify(source, args.destination)
    except (PackageError, OSError) as error:
        print(json.dumps({"status": "error", "reason": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
