#!/usr/bin/env python3
"""Build or verify the portable plugin from the canonical project skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = SKILL_ROOT.parents[2]
DEFAULT_PLUGIN_ROOT = REPOSITORY_ROOT / "plugins" / "solution-baseline"
EXCLUDED_NAMES = {"__pycache__", ".pytest_cache"}
EXCLUDED_RELATIVE = {"scripts/sync_plugin.py"}
AGENT_NAMES = (
    "architecture-mapper",
    "archetype-curator",
    "repository-baseline-worker",
    "baseline-validator",
    "solution-baseline-orchestrator",
)


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path, prefix: str = "") -> dict[str, str]:
    files: dict[str, str] = {}
    if not root.is_dir():
        return files
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if any(part in EXCLUDED_NAMES for part in Path(relative).parts):
            continue
        if relative in EXCLUDED_RELATIVE or path.suffix == ".pyc":
            continue
        files[f"{prefix}{relative}"] = file_digest(path)
    return files


def expected_inventory() -> dict[str, str]:
    expected = inventory(SKILL_ROOT, "skills/solution-baseline/")
    for name in AGENT_NAMES:
        claude = REPOSITORY_ROOT / ".claude" / "agents" / f"{name}.agent.md"
        codex = REPOSITORY_ROOT / ".codex" / "agents" / f"{name}.toml"
        expected[f"agents/{claude.name}"] = file_digest(claude)
        expected[f"assets/agent-adapters/codex/{codex.name}"] = file_digest(codex)
    return expected


def actual_inventory(plugin_root: Path) -> dict[str, str]:
    actual = inventory(plugin_root / "skills" / "solution-baseline", "skills/solution-baseline/")
    actual.update(inventory(plugin_root / "agents", "agents/"))
    actual.update(inventory(plugin_root / "assets" / "agent-adapters" / "codex", "assets/agent-adapters/codex/"))
    return actual


def assert_safe_target(plugin_root: Path) -> None:
    resolved = plugin_root.resolve()
    if resolved.name != "solution-baseline" or resolved.parent.name != "plugins":
        raise RuntimeError(f"Refusing unsafe plugin target: {resolved}")
    manifest = resolved / ".codex-plugin" / "plugin.json"
    if not manifest.is_file():
        raise RuntimeError(f"Plugin manifest is missing: {manifest}")


def sync(plugin_root: Path) -> None:
    assert_safe_target(plugin_root)
    targets = [
        plugin_root / "skills" / "solution-baseline",
        plugin_root / "agents",
        plugin_root / "assets" / "agent-adapters" / "codex",
        plugin_root / "assets" / "agent-adapters" / "claude",
    ]
    for target in targets:
        if target.exists():
            shutil.rmtree(target)
    shutil.copytree(
        SKILL_ROOT,
        targets[0],
        ignore=shutil.ignore_patterns("sync_plugin.py", "__pycache__", "*.pyc", ".pytest_cache"),
    )
    targets[1].mkdir(parents=True)
    targets[2].mkdir(parents=True)
    for name in AGENT_NAMES:
        shutil.copy2(
            REPOSITORY_ROOT / ".claude" / "agents" / f"{name}.agent.md", targets[1]
        )
        shutil.copy2(REPOSITORY_ROOT / ".codex" / "agents" / f"{name}.toml", targets[2])


def compare(plugin_root: Path) -> dict[str, object]:
    expected = expected_inventory()
    actual = actual_inventory(plugin_root)
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    changed = sorted(path for path in set(expected) & set(actual) if expected[path] != actual[path])
    return {
        "valid": not (missing or unexpected or changed),
        "expected_files": len(expected),
        "actual_files": len(actual),
        "missing": missing,
        "unexpected": unexpected,
        "changed": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, default=DEFAULT_PLUGIN_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        sync(args.plugin_root)
    result = compare(args.plugin_root)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
