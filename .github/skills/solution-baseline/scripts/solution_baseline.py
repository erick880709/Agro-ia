#!/usr/bin/env python3
"""Deterministic helpers for the solution-baseline skill.

The CLI reads and validates local artifacts, inventories repositories, resolves
catalog candidates, compares directory trees, manages local leases, and records
idempotent run steps. It never executes an archetype or mutates remote systems.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment error
    raise SystemExit("Missing dependency PyYAML. Install scripts/requirements.txt") from exc

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError as exc:  # pragma: no cover - environment error
    raise SystemExit("Missing dependency jsonschema. Install scripts/requirements.txt") from exc

try:
    from filelock import FileLock, Timeout as FileLockTimeout
    from packaging.specifiers import InvalidSpecifier, SpecifierSet
    from packaging.version import InvalidVersion, Version
except ImportError as exc:  # pragma: no cover - environment error
    raise SystemExit("Missing dependency filelock or packaging. Install scripts/requirements.txt") from exc


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_ROOT = SKILL_ROOT / "assets" / "schemas"
ADAPTER_REGISTRY = SKILL_ROOT / "adapters" / "registry.json"
GENESIS_EQUIVALENCE_MATRIX = (
    SKILL_ROOT / "assets" / "evaluations" / "genesis-greenfield-equivalence.yaml"
)
SCOPE_POLICY = SKILL_ROOT / "assets" / "policies" / "scope-boundaries.yaml"
CONCURRENCY_POLICY = SKILL_ROOT / "assets" / "policies" / "concurrency-limits.yaml"
AGENT_NAMES = (
    "architecture-mapper",
    "archetype-curator",
    "repository-baseline-worker",
    "baseline-validator",
    "solution-baseline-orchestrator",
)
AGENT_INSTALL_RECORD = Path(".solution-baseline") / "agent-installation.json"
SCHEMAS = {
    "blueprint": SCHEMA_ROOT / "solution-blueprint.schema.json",
    "run": SCHEMA_ROOT / "run-manifest.schema.json",
    "receipt": SCHEMA_ROOT / "receipt.schema.json",
    "catalog": SCHEMA_ROOT / "catalog.schema.json",
    "result": SCHEMA_ROOT / "generator-result.schema.json",
    "adapter": SCHEMA_ROOT / "adapter-registry.schema.json",
    "requirement": SCHEMA_ROOT / "archetype-requirement.schema.json",
    "handoff": SCHEMA_ROOT / "vulcano-handoff.schema.json",
    "gap": SCHEMA_ROOT / "architecture-gap.schema.json",
    "evaluation": SCHEMA_ROOT / "skill-evaluation.schema.json",
    "observations": SCHEMA_ROOT / "routing-observations.schema.json",
    "verification": SCHEMA_ROOT / "source-verification.schema.json",
    "scope-policy": SCHEMA_ROOT / "scope-policy.schema.json",
    "concurrency-policy": SCHEMA_ROOT / "concurrency-policy.schema.json",
    "assignments": SCHEMA_ROOT / "agent-assignment.schema.json",
    "agent-installation": SCHEMA_ROOT / "agent-installation.schema.json",
}
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    "dist",
    "build",
    "bin",
    "obj",
}
APPLICATION_SUFFIXES = {
    ".cs",
    ".fs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".ts",
    ".tsx",
    ".vue",
}
MANIFEST_PATTERNS = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "*.csproj",
    "*.fsproj",
    "*.sln",
    "*.slnx",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "go.mod",
    "Cargo.toml",
    "composer.json",
    "Gemfile",
)
LEASE_SUFFIXES = {".json", ".yaml", ".yml"}


class BaselineError(RuntimeError):
    """Expected validation or safety error."""


def dag_semantic_errors(dag: Any) -> list[str]:
    if not isinstance(dag, dict):
        return ["dag: must be an object"]
    errors: list[str] = []
    nodes = dag.get("nodes", [])
    node_ids = [node.get("id") for node in nodes if isinstance(node, dict)]
    duplicates = sorted({node_id for node_id in node_ids if node_ids.count(node_id) > 1})
    if duplicates:
        errors.append(f"dag/nodes: duplicate ids {duplicates}")
    known = set(node_ids)
    graph: dict[str, list[str]] = {}
    for index, node in enumerate(nodes):
        node_id = node.get("id")
        dependencies = node.get("depends_on", [])
        unknown = sorted(set(dependencies) - known)
        if unknown:
            errors.append(f"dag/nodes/{index}/depends_on: unknown nodes {unknown}")
        if node_id in dependencies:
            errors.append(f"dag/nodes/{index}/depends_on: node cannot depend on itself")
        graph[node_id] = dependencies

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visited or node_id not in graph:
            return
        if node_id in visiting:
            errors.append(f"dag: dependency cycle includes {node_id}")
            return
        visiting.add(node_id)
        for dependency in graph[node_id]:
            visit(dependency)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in graph:
        visit(node_id)
    barriers = dag.get("barriers", [])
    barrier_ids = [barrier.get("id") for barrier in barriers if isinstance(barrier, dict)]
    duplicate_barriers = sorted(
        {barrier_id for barrier_id in barrier_ids if barrier_ids.count(barrier_id) > 1}
    )
    if duplicate_barriers:
        errors.append(f"dag/barriers: duplicate ids {duplicate_barriers}")
    for index, barrier in enumerate(barriers):
        unknown = sorted(set(barrier.get("release_nodes", [])) - known)
        if unknown:
            errors.append(f"dag/barriers/{index}/release_nodes: unknown nodes {unknown}")
    return errors


def run_manifest_cross_checks(document: dict[str, Any]) -> list[str]:
    """Cross-check DAG node / instance status against the steps that produced them.

    Independent of --strict and of the top-level run status: a node or
    instance cannot claim completed/validated unless the matching step
    actually succeeded. Without this, `dag.nodes[].status: completed` or
    `instances[].status: validated` can stand even when the recorded step
    for that repository is `partial`/`failed`/`blocked` (e.g. lint/build
    failed, zero tests) — nothing else in this module catches that unless
    the whole run is `status: completed` under `--strict`.
    """
    errors: list[str] = []
    steps = document.get("steps", [])
    if not isinstance(steps, list):
        return errors

    # A DAG node `kind` is a coarser bucket than a generator-result `operation`:
    # e.g. `kind: render` covers the whole pre-apply pipeline (metadata/inspect/
    # plan/render/diff), while `kind: apply`/`validate` map 1:1 to their
    # eponymous operation. Match against the whole family, not literal equality.
    OPERATIONS_BY_NODE_KIND = {
        "render": {"metadata", "inspect", "plan", "render", "diff"},
        "apply": {"apply", "upgrade"},
        "validate": {"validate"},
    }

    def latest_matching_step(repository_id: Any, operations: set[str]) -> dict[str, Any] | None:
        matches = [
            step for step in steps
            if isinstance(step, dict)
            and step.get("repository_id") == repository_id
            and step.get("operation") in operations
        ]
        return matches[-1] if matches else None

    dag = document.get("dag", {})
    if isinstance(dag, dict):
        for index, node in enumerate(dag.get("nodes", [])):
            if not isinstance(node, dict):
                continue
            kind = node.get("kind")
            operations = OPERATIONS_BY_NODE_KIND.get(kind)
            if operations is None or node.get("status") != "completed":
                continue
            step = latest_matching_step(node.get("repository_id"), operations)
            if step is None:
                errors.append(
                    f"dag/nodes/{index}: status=completed but no matching step "
                    f"(operation in {sorted(operations)}) was recorded for "
                    f"repository_id={node.get('repository_id')!r}"
                )
            elif step.get("status") != "succeeded":
                errors.append(
                    f"dag/nodes/{index}: status=completed but the latest matching step "
                    f"reports status={step.get('status')!r}"
                )

    for index, instance in enumerate(document.get("instances", [])):
        if not isinstance(instance, dict) or instance.get("status") != "validated":
            continue
        step = latest_matching_step(instance.get("repository_id"), {"validate"})
        if step is None:
            errors.append(
                f"instances/{index}: status=validated but no matching 'validate' step "
                f"was recorded for repository_id={instance.get('repository_id')!r}"
            )
        elif step.get("status") != "succeeded":
            errors.append(
                f"instances/{index}: status=validated but the latest matching step "
                f"reports status={step.get('status')!r}"
            )

    return errors


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def isoformat(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat().replace("+00:00", "Z")


def json_output(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))


def load_document(path: Path) -> Any:
    if not path.is_file():
        raise BaselineError(f"File does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise BaselineError(f"Cannot parse {path}: {exc}") from exc


def dump_yaml_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    os.replace(temporary, path)


def dump_document_atomic(path: Path, payload: Any) -> None:
    if path.suffix.lower() == ".json":
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
        return
    dump_yaml_atomic(path, payload)


def load_schema(kind: str) -> tuple[dict[str, Any], Path]:
    schema_path = SCHEMAS[kind]
    return json.loads(schema_path.read_text(encoding="utf-8")), schema_path


def schema_errors(kind: str, document: Any) -> list[str]:
    schema, schema_path = load_schema(kind)
    registry = Registry()
    for candidate in SCHEMA_ROOT.glob("*.json"):
        candidate_schema = json.loads(candidate.read_text(encoding="utf-8"))
        resource = Resource.from_contents(candidate_schema)
        registry = registry.with_resource(candidate.as_uri(), resource)
        if candidate_schema.get("$id"):
            registry = registry.with_resource(candidate_schema["$id"], resource)
    validator = Draft202012Validator(
        schema, registry=registry, format_checker=FormatChecker()
    )
    errors: list[str] = []
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{location}: {error.message}")
    return errors


def semantic_errors(kind: str, document: dict[str, Any], strict: bool) -> list[str]:
    errors: list[str] = []
    if not strict:
        return errors

    if kind == "blueprint":
        if not document.get("components"):
            errors.append("components: strict validation requires at least one component")
        for index, source in enumerate(document.get("sources", [])):
            if source.get("status") == "pending":
                errors.append(f"sources/{index}: pending architecture source blocks strict validation")
        for index, component in enumerate(document.get("components", [])):
            stack = component.get("stack", {})
            for field in ("runtime", "framework_version", "package_manager_version"):
                request = stack.get(field)
                if request and not request.get("resolved"):
                    errors.append(
                        f"components/{index}/stack/{field}: resolved exact version is required"
                    )
                values = [request.get("requested"), request.get("resolved")] if request else []
                if any(str(value).lower() == "latest" for value in values if value):
                    errors.append(f"components/{index}/stack/{field}: latest is forbidden")
                if request and request.get("resolved") and not is_exact_version(
                    str(request["resolved"]), request.get("scheme")
                ):
                    errors.append(
                        f"components/{index}/stack/{field}/resolved: exact version is required"
                    )
        for index, decision in enumerate(document.get("decisions", [])):
            if decision.get("status") == "pending":
                errors.append(f"decisions/{index}: pending decision blocks strict validation")

    elif kind == "run":
        if not document.get("blueprint", {}).get("sha256"):
            errors.append("blueprint/sha256: required for strict validation")
        errors.extend(dag_semantic_errors(document.get("dag")))
        seen: set[tuple[str, str, str]] = set()
        for index, step in enumerate(document.get("steps", [])):
            key = (
                step.get("repository_id", ""),
                step.get("operation", ""),
                step.get("idempotency_key", ""),
            )
            if key in seen:
                errors.append(f"steps/{index}: duplicate idempotent step {key}")
            seen.add(key)
        if document.get("status") == "completed":
            bad = [
                step for step in document.get("steps", [])
                if step.get("status") in {"failed", "blocked", "partial"}
            ]
            if bad:
                errors.append("status: completed run contains failed, blocked, or partial steps")
            open_gaps = [
                gap for gap in document.get("architecture_gaps", [])
                if gap.get("status") == "open"
            ]
            if open_gaps:
                errors.append("status: completed run contains open architecture gaps")
            unfinished_nodes = [
                node for node in document.get("dag", {}).get("nodes", [])
                if node.get("status") not in {"completed", "skipped"}
            ]
            if unfinished_nodes:
                errors.append("status: completed run contains unfinished DAG nodes")
            unfinished_barriers = [
                barrier for barrier in document.get("dag", {}).get("barriers", [])
                if barrier.get("status") != "satisfied"
            ]
            if unfinished_barriers:
                errors.append("status: completed run contains unsatisfied DAG barriers")

    elif kind == "receipt":
        digest = str(document.get("provenance", {}).get("digest", ""))
        if not re.match(r"^(?:sha256:[a-fA-F0-9]{64}|git:[a-fA-F0-9]{40,64})$", digest):
            errors.append("provenance/digest: strict validation requires an immutable sha256: or git: digest")
        for path, value, scheme in (
            ("provenance/version", document.get("provenance", {}).get("version"), None),
            (
                "generator/version",
                document.get("generator", {}).get("version"),
                document.get("generator", {}).get("version_scheme"),
            ),
        ):
            if value and not is_exact_version(str(value), scheme):
                errors.append(f"{path}: exact version is required")
        paths: set[str] = set()
        for index, ownership in enumerate(document.get("ownership", [])):
            path = ownership.get("path")
            if path in paths:
                errors.append(f"ownership/{index}: duplicate path {path}")
            paths.add(path)
        for index, validation in enumerate(document.get("validations", [])):
            if validation.get("status") == "failed":
                errors.append(f"validations/{index}: failed validation blocks strict receipt")

    elif kind == "catalog":
        seen_versions: set[tuple[str, str]] = set()
        required_exclusions = {"cicd", "iac", "containers", "cloud-provisioning", "deployment"}
        for index, archetype in enumerate(document.get("archetypes", [])):
            key = (archetype.get("family", ""), archetype.get("version", ""))
            if key in seen_versions:
                errors.append(f"archetypes/{index}: duplicate family/version {key}")
            seen_versions.add(key)
            digest = str(archetype.get("digest", ""))
            if not re.match(r"^(?:sha256:[a-fA-F0-9]{64}|git:[a-fA-F0-9]{40,64})$", digest):
                errors.append(
                    f"archetypes/{index}/digest: strict validation requires an immutable sha256: or git: digest"
                )
            compatibility = archetype.get("compatibility", {})
            for field in ("runtime", "framework_version"):
                if str(compatibility.get(field, "")).lower() == "latest":
                    errors.append(f"archetypes/{index}/compatibility/{field}: latest is forbidden")
            generator = archetype.get("generator", {})
            if not is_exact_version(
                str(generator.get("version", "")), generator.get("version_scheme")
            ):
                errors.append(f"archetypes/{index}/generator/version: exact version is required")
            missing = required_exclusions - set(archetype.get("exclusions", []))
            if missing:
                errors.append(
                    f"archetypes/{index}/exclusions: missing baseline boundaries {sorted(missing)}"
                )

    elif kind == "adapter":
        ids: set[str] = set()
        for index, adapter in enumerate(document.get("adapters", [])):
            adapter_id = adapter.get("id")
            if adapter_id in ids:
                errors.append(f"adapters/{index}: duplicate adapter id {adapter_id}")
            ids.add(adapter_id)

    elif kind == "handoff":
        workload = document.get("workload")
        ports = document.get("service", {}).get("ports", {})
        if workload in {"web", "api"} and not ports:
            errors.append("service/ports: web and api workloads must declare at least one port")
        for name, container in document.get("containers", {}).items():
            if not container.get("livenessProbe") and not container.get("readinessProbe"):
                errors.append(
                    f"containers/{name}: at least one health probe is required for strict handoff"
                )

    elif kind == "gap":
        status = document.get("status")
        if status == "resolved" and not document.get("resolution"):
            errors.append("resolution: resolved architecture gap requires a resolution")
        if status == "open" and document.get("resolution"):
            errors.append("resolution: open architecture gap cannot contain a resolution")

    elif kind == "verification":
        expected = str(document.get("expected_digest", "")).lower()
        actual = str(document.get("actual_digest", "")).lower()
        if expected != actual:
            errors.append("actual_digest: must equal expected_digest")
        try:
            material_kind, recomputed = source_material_digest(
                Path(str(document.get("material_path", ""))), expected
            )
            if material_kind != document.get("material_kind"):
                errors.append("material_kind: does not match local source material")
            if recomputed.lower() != expected:
                errors.append("expected_digest: does not match local source material")
        except BaselineError as exc:
            errors.append(f"material_path: {exc}")

    return errors


def validate(kind: str, path: Path, strict: bool = False) -> dict[str, Any]:
    document = load_document(path)
    errors = schema_errors(kind, document)
    if isinstance(document, dict):
        if kind == "run":
            errors.extend(run_manifest_cross_checks(document))
        errors.extend(semantic_errors(kind, document, strict))
    return {
        "valid": not errors,
        "kind": kind,
        "file": str(path.resolve()),
        "strict": strict,
        "errors": errors,
    }


def should_ignore(relative: str, extra_patterns: Iterable[str] = ()) -> bool:
    normalized = relative.replace("\\", "/")
    parts = normalized.split("/")
    if any(part in IGNORED_DIRS for part in parts):
        return True
    patterns = list(extra_patterns)
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def iter_files(root: Path, extra_patterns: Iterable[str] = ()) -> Iterable[Path]:
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(
            directory
            for directory in dirs
            if not should_ignore(
                (current_path / directory).relative_to(root).as_posix(), extra_patterns
            )
            and not (current_path / directory).is_symlink()
        )
        for filename in sorted(files):
            path = current_path / filename
            relative = path.relative_to(root).as_posix()
            if not path.is_symlink() and not should_ignore(relative, extra_patterns):
                yield path


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def copy_file_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def agent_source_directory(platform: str, skill_root: Path = SKILL_ROOT) -> Path:
    if platform not in {"claude", "codex"}:
        raise BaselineError(f"Unsupported agent platform: {platform}")
    resolved_skill = skill_root.resolve()
    distribution_root = resolved_skill.parents[1]
    candidates = (
        [distribution_root / "agents"]
        if platform == "claude"
        else [
            distribution_root / "assets" / "agent-adapters" / "codex",
            resolved_skill.parents[2] / ".codex" / "agents",
        ]
    )
    suffix = ".agent.md" if platform == "claude" else ".toml"
    for candidate in candidates:
        if all((candidate / f"{name}{suffix}").is_file() for name in AGENT_NAMES):
            return candidate
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise BaselineError(f"Agent sources for {platform} are incomplete; searched: {searched}")


def validate_agent_source(path: Path, platform: str, expected_name: str) -> None:
    try:
        content = path.read_text(encoding="utf-8")
        if platform == "codex":
            metadata = tomllib.loads(content)
            required = ("name", "description", "developer_instructions")
        else:
            parts = content.split("---", 2)
            if len(parts) != 3:
                raise ValueError("missing YAML frontmatter")
            metadata = yaml.safe_load(parts[1])
            required = ("name", "description")
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        missing = [field for field in required if not metadata.get(field)]
        if missing:
            raise ValueError(f"missing required fields: {', '.join(missing)}")
        if metadata.get("name") != expected_name:
            raise ValueError(f"name must be {expected_name!r}")
    except (OSError, tomllib.TOMLDecodeError, yaml.YAMLError, ValueError) as exc:
        raise BaselineError(f"Invalid {platform} agent source {path}: {exc}") from exc


def expected_agent_files(
    platform: str, project_root: Path, skill_root: Path = SKILL_ROOT
) -> list[dict[str, Any]]:
    source_root = agent_source_directory(platform, skill_root)
    destination_root = (
        project_root.resolve() / ".claude" / "agents"
        if platform == "claude"
        else project_root.resolve() / ".codex" / "agents"
    )
    suffix = ".agent.md" if platform == "claude" else ".toml"
    files: list[dict[str, Any]] = []
    for name in AGENT_NAMES:
        source = source_root / f"{name}{suffix}"
        validate_agent_source(source, platform, name)
        files.append(
            {
                "name": name,
                "source": source,
                "destination": destination_root / source.name,
                "sha256": hash_file(source),
            }
        )
    return files


def load_concurrency_policy(path: Path = CONCURRENCY_POLICY) -> dict[str, Any]:
    policy = load_document(path)
    errors = schema_errors("concurrency-policy", policy)
    if not errors:
        if policy["max_parallel_readers"] > policy["max_parallel_agents"]:
            errors.append("max_parallel_readers cannot exceed max_parallel_agents")
        if policy["max_parallel_writers"] > policy["max_parallel_agents"]:
            errors.append("max_parallel_writers cannot exceed max_parallel_agents")
        if policy["max_writers_per_repository"] > policy["max_parallel_writers"]:
            errors.append("max_writers_per_repository cannot exceed max_parallel_writers")
        if policy["max_catalog_writers"] > policy["max_parallel_writers"]:
            errors.append("max_catalog_writers cannot exceed max_parallel_writers")
    if errors:
        raise BaselineError("Invalid concurrency policy: " + "; ".join(errors))
    return policy


def codex_concurrency_status(
    project_root: Path, policy_path: Path = CONCURRENCY_POLICY
) -> dict[str, Any]:
    desired = load_concurrency_policy(policy_path)["max_parallel_agents"]
    config_path = project_root.resolve() / ".codex" / "config.toml"
    if not config_path.is_file():
        return {
            "valid": False,
            "path": str(config_path),
            "desired": desired,
            "actual": None,
            "issue": "missing",
        }
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise BaselineError(f"Invalid Codex config {config_path}: {exc}") from exc
    actual = config.get("agents", {}).get("max_concurrent_threads_per_session")
    return {
        "valid": actual == desired,
        "path": str(config_path),
        "desired": desired,
        "actual": actual,
        "issue": None if actual == desired else "missing-or-mismatched-limit",
    }


def configure_codex_concurrency(
    project_root: Path,
    policy_path: Path = CONCURRENCY_POLICY,
    force: bool = False,
) -> dict[str, Any]:
    status = codex_concurrency_status(project_root, policy_path)
    if status["valid"]:
        return {**status, "status": "unchanged"}
    config_path = Path(status["path"])
    desired = status["desired"]
    if status["actual"] is not None and not force:
        raise BaselineError(
            "Codex concurrency limit already exists with a different value; "
            "review it or repeat with --force-config"
        )
    if not config_path.exists():
        content = (
            "[agents]\n"
            "enabled = true\n"
            f"max_concurrent_threads_per_session = {desired}\n"
        )
    else:
        content = config_path.read_text(encoding="utf-8")
        header = re.search(r"(?m)^\[agents\]\s*$", content)
        if header:
            insert_at = header.end()
            next_header = re.search(r"(?m)^\[[^\n]+\]\s*$", content[insert_at:])
            section_end = insert_at + next_header.start() if next_header else len(content)
            section = content[insert_at:section_end]
            key_pattern = re.compile(
                r"(?m)^(max_concurrent_threads_per_session\s*=\s*)\d+\s*$"
            )
            if key_pattern.search(section):
                section = key_pattern.sub(rf"\g<1>{desired}", section, count=1)
                content = content[:insert_at] + section + content[section_end:]
            else:
                content = (
                    content[:insert_at]
                    + f"\nmax_concurrent_threads_per_session = {desired}"
                    + content[insert_at:]
                )
        else:
            separator = "" if not content or content.endswith("\n") else "\n"
            content += (
                separator
                + "\n[agents]\n"
                + "enabled = true\n"
                + f"max_concurrent_threads_per_session = {desired}\n"
            )
    write_text_atomic(config_path, content)
    return {**codex_concurrency_status(project_root, policy_path), "status": "configured"}


def check_agents(
    project_root: Path,
    platforms: Iterable[str],
    skill_root: Path = SKILL_ROOT,
    require_codex_runtime: bool = True,
) -> dict[str, Any]:
    if not project_root.resolve().is_dir():
        raise BaselineError(f"Project root does not exist: {project_root.resolve()}")
    platform_results: dict[str, Any] = {}
    overall_valid = True
    for platform in platforms:
        files = []
        for expected in expected_agent_files(platform, project_root, skill_root):
            destination = expected["destination"]
            actual_digest = hash_file(destination) if destination.is_file() else None
            state = (
                "installed"
                if actual_digest == expected["sha256"]
                else "modified"
                if actual_digest
                else "missing"
            )
            files.append(
                {
                    "name": expected["name"],
                    "path": str(destination),
                    "state": state,
                    "expected_sha256": expected["sha256"],
                    "actual_sha256": actual_digest,
                }
            )
        platform_valid = all(item["state"] == "installed" for item in files)
        result: dict[str, Any] = {"valid": platform_valid, "files": files}
        if platform == "codex" and require_codex_runtime:
            result["runtime"] = codex_concurrency_status(project_root)
            platform_valid = platform_valid and result["runtime"]["valid"]
            result["valid"] = platform_valid
        platform_results[platform] = result
        overall_valid = overall_valid and platform_valid
    return {
        "valid": overall_valid,
        "project_root": str(project_root.resolve()),
        "platforms": platform_results,
    }


def install_agents(
    project_root: Path,
    platforms: Iterable[str],
    skill_root: Path = SKILL_ROOT,
    force: bool = False,
    configure_runtime: bool = False,
    force_config: bool = False,
) -> dict[str, Any]:
    if not project_root.resolve().is_dir():
        raise BaselineError(f"Project root does not exist: {project_root.resolve()}")
    selected = tuple(dict.fromkeys(platforms))
    if not selected:
        raise BaselineError("Select at least one agent platform")
    planned: list[tuple[str, dict[str, Any]]] = []
    conflicts: list[str] = []
    for platform in selected:
        for expected in expected_agent_files(platform, project_root, skill_root):
            destination = expected["destination"]
            if destination.exists() and hash_file(destination) != expected["sha256"]:
                conflicts.append(str(destination))
            planned.append((platform, expected))
    if conflicts and not force:
        raise BaselineError(
            "Refusing to overwrite modified agent files: " + ", ".join(conflicts)
        )
    if configure_runtime and "codex" not in selected:
        raise BaselineError("--configure-runtime requires the codex platform")
    if force_config and not configure_runtime:
        raise BaselineError("--force-config requires --configure-runtime")
    if configure_runtime:
        runtime_status = codex_concurrency_status(project_root)
        if runtime_status["actual"] is not None and not runtime_status["valid"] and not force_config:
            raise BaselineError(
                "Codex concurrency limit conflicts with the solution-baseline policy; "
                "review it or repeat with --force-config"
            )
    record_path = project_root.resolve() / AGENT_INSTALL_RECORD
    if record_path.exists():
        existing_record = load_document(record_path)
        record_errors = schema_errors("agent-installation", existing_record)
        if record_errors or existing_record.get("skill") != "solution-baseline":
            raise BaselineError(f"Refusing to replace an unrelated installation record: {record_path}")
    installed: list[dict[str, Any]] = []
    for platform, expected in planned:
        destination = expected["destination"]
        state = "unchanged"
        if not destination.is_file() or hash_file(destination) != expected["sha256"]:
            copy_file_atomic(expected["source"], destination)
            state = "installed"
        installed.append(
            {
                "platform": platform,
                "name": expected["name"],
                "path": str(destination),
                "sha256": expected["sha256"],
                "state": state,
            }
        )
    runtime = (
        configure_codex_concurrency(project_root, force=force_config)
        if configure_runtime
        else None
    )
    record_files = [
        {
            **item,
            "path": Path(item["path"]).resolve().relative_to(project_root.resolve()).as_posix(),
        }
        for item in installed
    ]
    record_runtime = None
    if runtime:
        record_runtime = {
            **runtime,
            "path": Path(runtime["path"])
            .resolve()
            .relative_to(project_root.resolve())
            .as_posix(),
        }
    record = {
        "schema_version": 1,
        "skill": "solution-baseline",
        "installed_at": isoformat(),
        "files": record_files,
        "runtime": record_runtime,
    }
    record_errors = schema_errors("agent-installation", record)
    if record_errors:
        raise BaselineError("Invalid agent installation record: " + "; ".join(record_errors))
    dump_document_atomic(record_path, record)
    result = check_agents(
        project_root,
        selected,
        skill_root,
        require_codex_runtime=configure_runtime,
    )
    result.update({"record": str(record_path), "installed": installed, "runtime": runtime})
    return result


def git_path(root: Path, argument: str) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", argument],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    candidate = Path(result.stdout.strip())
    return (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()


def verify_workspace_isolation(
    workspace: Path, main_checkout: Path, allow_non_git: bool = False
) -> dict[str, Any]:
    workspace = workspace.resolve()
    main_checkout = main_checkout.resolve()
    errors: list[str] = []
    if not workspace.is_dir():
        errors.append("workspace does not exist or is not a directory")
    if not main_checkout.is_dir():
        errors.append("main checkout does not exist or is not a directory")
    if errors:
        return {
            "valid": False,
            "workspace": str(workspace),
            "main_checkout": str(main_checkout),
            "errors": errors,
        }
    if workspace == main_checkout:
        errors.append("workspace is the main checkout")
    if workspace.is_relative_to(main_checkout) or main_checkout.is_relative_to(workspace):
        errors.append("workspace and main checkout must not contain one another")
    workspace_top = git_path(workspace, "--show-toplevel")
    main_top = git_path(main_checkout, "--show-toplevel")
    workspace_common = git_path(workspace, "--git-common-dir")
    main_common = git_path(main_checkout, "--git-common-dir")
    isolation_kind = "directory"
    if workspace_top and main_top:
        if workspace_top == main_top:
            errors.append("workspace resolves to the main Git checkout")
        elif workspace_common and main_common and workspace_common == main_common:
            isolation_kind = "git-worktree"
        elif workspace_common and main_common:
            # Two distinct repositories with unrelated object databases (different
            # --git-common-dir) are at least as isolated as a linked worktree: no
            # shared refs, no shared working tree, nothing to accidentally collide on.
            isolation_kind = "independent-repo"
        else:
            errors.append("workspace is not a linked worktree of the main checkout")
    elif not allow_non_git:
        errors.append("workspace and main checkout must be Git worktrees of the same repository")
    return {
        "valid": not errors,
        "workspace": str(workspace),
        "main_checkout": str(main_checkout),
        "workspace_git_root": str(workspace_top) if workspace_top else None,
        "main_git_root": str(main_top) if main_top else None,
        "isolation_kind": isolation_kind,
        "errors": errors,
    }


def check_concurrency(
    assignments_path: Path, policy_path: Path = CONCURRENCY_POLICY
) -> dict[str, Any]:
    assignments = load_document(assignments_path)
    assignment_errors = schema_errors("assignments", assignments)
    if assignment_errors:
        raise BaselineError("Invalid agent assignments: " + "; ".join(assignment_errors))
    policy = load_concurrency_policy(policy_path)
    agent_ids = [item["agent_id"] for item in assignments["assignments"]]
    duplicates = sorted({agent_id for agent_id in agent_ids if agent_ids.count(agent_id) > 1})
    if duplicates:
        raise BaselineError(f"Duplicate agent assignment ids: {duplicates}")
    active = [
        item
        for item in assignments["assignments"]
        if item["status"] in {"scheduled", "running"}
    ]
    readers = [item for item in active if item["access"] == "read"]
    writers = [item for item in active if item["access"] == "write"]
    violations: list[dict[str, Any]] = []

    def enforce(code: str, actual: int, limit: int, scope: str) -> None:
        if actual > limit:
            violations.append(
                {"code": code, "scope": scope, "actual": actual, "limit": limit}
            )

    enforce("max-parallel-agents", len(active), policy["max_parallel_agents"], "global")
    enforce("max-parallel-readers", len(readers), policy["max_parallel_readers"], "global")
    enforce("max-parallel-writers", len(writers), policy["max_parallel_writers"], "global")
    repository_counts: dict[str, int] = {}
    catalog_writers = 0
    writer_workspaces: dict[str, list[str]] = {}
    for item in writers:
        workspace_key = item["workspace"].replace("\\", "/").rstrip("/").casefold()
        writer_workspaces.setdefault(workspace_key, []).append(item["agent_id"])
        if item["scope"] == "repository":
            repository_counts[item["resource"]] = repository_counts.get(item["resource"], 0) + 1
        elif item["scope"] == "catalog":
            catalog_writers += 1
    for resource, count in sorted(repository_counts.items()):
        enforce(
            "max-writers-per-repository",
            count,
            policy["max_writers_per_repository"],
            resource,
        )
    enforce(
        "max-catalog-writers",
        catalog_writers,
        policy["max_catalog_writers"],
        "catalog",
    )
    for workspace, agent_ids in sorted(writer_workspaces.items()):
        if len(agent_ids) > 1:
            violations.append(
                {
                    "code": "shared-writer-workspace",
                    "scope": workspace,
                    "actual": len(agent_ids),
                    "limit": 1,
                    "agents": sorted(agent_ids),
                }
            )
    return {
        "valid": not violations,
        "policy": str(policy_path.resolve()),
        "active": len(active),
        "readers": len(readers),
        "writers": len(writers),
        "violations": violations,
    }


def hash_tree(root: Path, extra_patterns: Iterable[str] = ()) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise BaselineError(f"Directory does not exist: {root}")
    files: dict[str, str] = {}
    aggregate = hashlib.sha256()
    for path in iter_files(root, extra_patterns):
        relative = path.relative_to(root).as_posix()
        digest = hash_file(path)
        files[relative] = digest
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii"))
        aggregate.update(b"\n")
    return {"root": str(root), "sha256": aggregate.hexdigest(), "files": files}


def source_material_digest(material_path: Path, expected_digest: str) -> tuple[str, str]:
    """Recompute an immutable digest from local, non-executed source material."""
    material_path = material_path.resolve()
    if expected_digest.startswith("sha256:"):
        if material_path.is_file():
            return "file", f"sha256:{hash_file(material_path)}"
        if material_path.is_dir():
            return "tree", f"sha256:{hash_tree(material_path)['sha256']}"
        raise BaselineError(f"Source material does not exist: {material_path}")
    if expected_digest.startswith("git:"):
        if not material_path.is_dir():
            raise BaselineError("A git digest requires a local repository directory")
        try:
            result = subprocess.run(
                ["git", "-C", str(material_path), "rev-parse", "HEAD"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise BaselineError(f"Cannot inspect git source material: {exc}") from exc
        commit = result.stdout.strip().lower()
        if result.returncode != 0 or not re.fullmatch(r"[a-f0-9]{40,64}", commit):
            raise BaselineError("Source material is not a readable git repository")
        return "git", f"git:{commit}"
    raise BaselineError("Expected digest must use sha256:<64 hex> or git:<40-64 hex>")


def verify_source_material(
    archetype_id: str,
    source: str,
    material_path: Path,
    expected_digest: str,
) -> dict[str, Any]:
    if not archetype_id.strip() or not source.strip():
        raise BaselineError("archetype-id and source are required")
    if not re.fullmatch(r"(?:sha256:[a-fA-F0-9]{64}|git:[a-fA-F0-9]{40,64})", expected_digest):
        raise BaselineError("Expected digest must be immutable and syntactically valid")
    material_kind, actual_digest = source_material_digest(material_path, expected_digest)
    if actual_digest.lower() != expected_digest.lower():
        raise BaselineError(
            f"Source digest mismatch: expected {expected_digest.lower()}, got {actual_digest.lower()}"
        )
    return {
        "schema_version": 1,
        "archetype_id": archetype_id,
        "source": source,
        "material_path": str(material_path.resolve()),
        "material_kind": material_kind,
        "expected_digest": expected_digest.lower(),
        "actual_digest": actual_digest.lower(),
        "status": "verified",
        "verified_at": isoformat(),
    }


def load_source_verifications(paths: Iterable[Path]) -> dict[tuple[str, str, str], dict[str, Any]]:
    verified: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in paths:
        document = load_document(path)
        errors = schema_errors("verification", document)
        if isinstance(document, dict):
            errors.extend(semantic_errors("verification", document, strict=True))
        if errors:
            raise BaselineError(f"Invalid source verification {path}: {'; '.join(errors)}")
        if document.get("status") != "verified":
            raise BaselineError(f"Source verification is not verified: {path}")
        key = (
            document["archetype_id"],
            document["source"],
            document["expected_digest"].lower(),
        )
        verified[key] = document
    return verified


def find_manifests(root: Path) -> list[str]:
    found: set[str] = set()
    for path in iter_files(root):
        relative = path.relative_to(root).as_posix()
        if any(fnmatch.fnmatch(path.name, pattern) for pattern in MANIFEST_PATTERNS):
            found.add(relative)
    return sorted(found)


def read_package_jsons(root: Path) -> tuple[set[str], set[str], list[str]]:
    dependencies: set[str] = set()
    scripts: set[str] = set()
    files: list[str] = []
    for path in root.rglob("package.json"):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if should_ignore(relative):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        files.append(relative)
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            dependencies.update((data.get(section) or {}).keys())
        scripts.update((data.get("scripts") or {}).keys())
    return dependencies, scripts, sorted(files)


def read_python_dependencies(root: Path) -> set[str]:
    dependencies: set[str] = set()
    candidates = list(root.rglob("pyproject.toml")) + list(root.rglob("requirements*.txt"))
    for path in candidates:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if should_ignore(relative):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in re.finditer(r"(?im)^\s*[\"']?([a-zA-Z0-9_.-]+)(?:\[[^]]+\])?\s*(?:[=<>!~]|[\"'])", text):
            dependencies.add(match.group(1).lower())
    return dependencies


def matches_file_pattern(root: Path, pattern: str) -> bool:
    return any(
        fnmatch.fnmatch(path.relative_to(root).as_posix(), pattern)
        or fnmatch.fnmatch(path.name, pattern)
        for path in iter_files(root)
    )


def detect_adapters(root: Path, dependencies: set[str]) -> list[dict[str, Any]]:
    registry = load_document(ADAPTER_REGISTRY)
    matches: list[dict[str, Any]] = []
    lowered = {dependency.lower() for dependency in dependencies}
    for adapter in registry.get("adapters", []):
        detect = adapter.get("detect", {})
        file_hits = [
            pattern for pattern in detect.get("files_any", [])
            if matches_file_pattern(root, pattern)
        ]
        dependency_hits = [
            dependency for dependency in detect.get("dependencies_any", [])
            if dependency.lower() in lowered
        ]
        content_hits: list[str] = []
        for needle in detect.get("content_any", []):
            for path in iter_files(root):
                if path.stat().st_size > 1024 * 1024:
                    continue
                try:
                    if needle in path.read_text(encoding="utf-8", errors="ignore"):
                        content_hits.append(needle)
                        break
                except OSError:
                    continue
        score = len(file_hits) + (2 * len(dependency_hits)) + len(content_hits)
        if score:
            matches.append(
                {
                    "id": adapter["id"],
                    "score": score,
                    "file_hits": file_hits,
                    "dependency_hits": dependency_hits,
                    "content_hits": content_hits,
                }
            )
    return sorted(matches, key=lambda item: (-item["score"], item["id"]))


def git_summary(root: Path) -> dict[str, Any] | None:
    try:
        inside = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return None
        branch = subprocess.run(
            ["git", "-C", str(root), "branch", "--show-current"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.splitlines()
        return {"branch": branch or None, "dirty": bool(status), "changed_entries": len(status)}
    except (OSError, subprocess.SubprocessError):
        return None


def inspect_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise BaselineError(f"Directory does not exist: {root}")
    node_dependencies, scripts, package_files = read_package_jsons(root)
    python_dependencies = read_python_dependencies(root)
    dependencies = node_dependencies | python_dependencies
    manifests = find_manifests(root)
    application_files = [
        path.relative_to(root).as_posix()
        for path in iter_files(root)
        if path.suffix.lower() in APPLICATION_SUFFIXES
        and ".claude/skills/" not in path.relative_to(root).as_posix()
    ]
    architecture_files = sorted(
        path.relative_to(root).as_posix()
        for path in root.glob("resources/architecture/**/*")
        if path.is_file()
    )
    receipt = root / ".solution-baseline" / "receipt.yaml"
    return {
        "root": str(root),
        "strategy_hint": "reconcile" if manifests or application_files else "create",
        "manifests": manifests,
        "package_files": package_files,
        "package_scripts": sorted(scripts),
        "dependencies": sorted(dependencies),
        "candidate_adapters": detect_adapters(root, dependencies),
        "application_file_count": len(application_files),
        "application_file_sample": sorted(application_files)[:50],
        "architecture_files": architecture_files,
        "receipt": {
            "path": str(receipt),
            "exists": receipt.is_file(),
            "valid": validate("receipt", receipt)["valid"] if receipt.is_file() else None,
        },
        "git": git_summary(root),
    }


def diff_trees(expected: Path, actual: Path) -> dict[str, Any]:
    expected_tree = hash_tree(expected, extra_patterns=(".solution-baseline/**",))
    actual_tree = hash_tree(actual, extra_patterns=(".solution-baseline/**",))
    expected_files = expected_tree["files"]
    actual_files = actual_tree["files"]
    added = sorted(set(expected_files) - set(actual_files))
    removed = sorted(set(actual_files) - set(expected_files))
    modified = sorted(
        path for path in set(expected_files) & set(actual_files)
        if expected_files[path] != actual_files[path]
    )
    unchanged = len(set(expected_files) & set(actual_files)) - len(modified)
    return {
        "expected_root": expected_tree["root"],
        "actual_root": actual_tree["root"],
        "expected_hash": expected_tree["sha256"],
        "actual_hash": actual_tree["sha256"],
        "summary": {
            "add": len(added),
            "modify": len(modified),
            "remove_candidate": len(removed),
            "unchanged": unchanged,
        },
        "changes": {"add": added, "modify": modified, "remove_candidate": removed},
        "warning": "remove_candidate entries require receipt ownership review; never delete project-owned files automatically",
    }


def check_drift(root: Path, receipt_path: Path) -> dict[str, Any]:
    """Verify that receipt `managed` files were not hand-edited outside the skill.

    Unlike `diff`, this does not require re-rendering the archetype: it only
    recomputes hashes for paths the receipt already classified as `managed` and
    compares them against the hash recorded at generation time. Entries without
    a recorded hash are reported as unverifiable, not as violations.
    """
    root = root.resolve()
    if not root.is_dir():
        raise BaselineError(f"Directory does not exist: {root}")
    receipt = load_document(receipt_path)
    errors = schema_errors("receipt", receipt)
    if errors:
        raise BaselineError("Invalid receipt: " + "; ".join(errors))

    violations: list[dict[str, str | None]] = []
    unverifiable: list[str] = []
    checked = 0
    for ownership in receipt.get("ownership", []):
        if ownership.get("category") != "managed":
            continue
        relative = str(ownership.get("path", "")).replace("\\", "/")
        expected = ownership.get("sha256")
        if not expected:
            unverifiable.append(relative)
            continue
        checked += 1
        target = root / relative
        if not target.is_file():
            violations.append(
                {"path": relative, "issue": "missing", "expected_sha256": expected, "actual_sha256": None}
            )
            continue
        actual = hash_file(target)
        if actual != expected:
            violations.append(
                {"path": relative, "issue": "modified", "expected_sha256": expected, "actual_sha256": actual}
            )

    return {
        "valid": not violations,
        "root": str(root),
        "receipt": str(receipt_path.resolve()),
        "checked": checked,
        "unverifiable": sorted(unverifiable),
        "violations": violations,
        "message": (
            "managed files match recorded provenance"
            if not violations
            else "managed files were modified outside solution-baseline; run reconcile/upgrade or accept drift explicitly"
        ),
    }


def gate_coverage(blueprint_path: Path, component_id: str, receipt_path: Path) -> dict[str, Any]:
    """Verify every quality gate declared for a component in the blueprint was
    actually executed and recorded in that component's receipt.

    A gate declared in `components[].quality_gates` (e.g. `boundaries-lint`,
    `typecheck`, `integration-tests-msw`) but never present in
    `receipt.validations[].id` disappears silently today — nothing flags it
    as skipped. This makes that omission an explicit, reportable finding
    instead of a gate that quietly never ran.
    """
    blueprint = load_document(blueprint_path)
    blueprint_errors = schema_errors("blueprint", blueprint)
    if blueprint_errors:
        raise BaselineError("Invalid blueprint: " + "; ".join(blueprint_errors))
    receipt = load_document(receipt_path)
    receipt_errors = schema_errors("receipt", receipt)
    if receipt_errors:
        raise BaselineError("Invalid receipt: " + "; ".join(receipt_errors))

    component = next(
        (c for c in blueprint.get("components", []) if c.get("id") == component_id), None
    )
    if component is None:
        raise BaselineError(f"Component not found in blueprint: {component_id}")

    declared = list(dict.fromkeys(component.get("quality_gates", [])))
    recorded = {
        validation.get("id")
        for validation in receipt.get("validations", [])
        if isinstance(validation, dict)
    }
    missing = [gate for gate in declared if gate not in recorded]

    return {
        "valid": not missing,
        "component_id": component_id,
        "declared_gates": declared,
        "recorded_validations": sorted(recorded),
        "missing_gates": missing,
        "message": (
            "every declared quality gate has a recorded validation"
            if not missing
            else f"declared but never executed: {missing}"
        ),
    }


def check_boundary_coverage(root: Path, discover_glob: str, declared: list[str]) -> dict[str, Any]:
    """Detect a boundary/allow-list config that drifted from real folders on disk.

    Some quality gates (e.g. CC-009 feature-folder boundaries) are commonly
    implemented as a hardcoded list of module/feature names inside a config
    file (an ESLint zones array, for example). That list has no automatic
    relationship to the folders that actually exist, so it silently stops
    covering any folder added after the list was last edited — the gate
    keeps passing, but it no longer checks the folders it was meant to
    check. This compares a declared allow-list against `discover_glob`
    (matched relative to `root`, directories only) and reports the gap in
    both directions, independent of stack or file format: the caller
    supplies the declared list (parsed however that project's config format
    requires), not this function.
    """
    root = root.resolve()
    if not root.is_dir():
        raise BaselineError(f"Directory does not exist: {root}")
    discovered = sorted(
        path.name for path in root.glob(discover_glob) if path.is_dir()
    )
    declared_set = set(declared)
    discovered_set = set(discovered)
    undeclared = sorted(discovered_set - declared_set)
    stale = sorted(declared_set - discovered_set)

    return {
        "valid": not undeclared,
        "root": str(root),
        "discover_glob": discover_glob,
        "discovered": discovered,
        "declared": sorted(declared_set),
        "undeclared": undeclared,
        "stale": stale,
        "message": (
            "every discovered folder is covered by the declared allow-list"
            if not undeclared
            else f"folders on disk are not covered by the boundary config: {undeclared}"
        ),
    }


STYLE_SOURCE_SUFFIXES = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".vue",
    ".svelte",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".html",
}
COLOR_LITERAL_RE = re.compile(
    r"(?<![&\w])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])"
    r"|\b(?:rgba?|hsla?)\("
)
PX_FONT_SIZE_RE = re.compile(r"font-?size\s*[:=]\s*[\"'`]?\s*\d+(?:\.\d+)?px", re.IGNORECASE)
MAX_REPORTED_STYLE_LITERALS = 200


def check_design_conformance(
    root: Path, blueprint_path: Path, component_id: str, solution_root: Path | None = None
) -> dict[str, Any]:
    """Verify a web/library component against its frozen design system.

    A design system is treated like a frozen contract: the tokens, component
    catalog and brand assets declared in `components[].design_system` must
    exist and match their recorded sha256, and the component code may only
    contain raw style literals (hex/rgb/hsl colors, px font sizes) inside the
    declared `style_zones` or `literal_exemptions`, up to the
    `max_literal_violations` ratchet. Paths in the declaration are resolved
    against `solution_root` (default: current directory).
    """
    blueprint = load_document(blueprint_path)
    blueprint_errors = schema_errors("blueprint", blueprint)
    if blueprint_errors:
        raise BaselineError("Invalid blueprint: " + "; ".join(blueprint_errors))
    component = next(
        (c for c in blueprint.get("components", []) if c.get("id") == component_id), None
    )
    if component is None:
        raise BaselineError(f"Component not found in blueprint: {component_id}")
    design = component.get("design_system")
    if not design:
        raise BaselineError(f"Component {component_id} declares no design_system")
    root = root.resolve()
    if not root.is_dir():
        raise BaselineError(f"Directory does not exist: {root}")
    base = (solution_root or Path.cwd()).resolve()

    declared: list[tuple[str, dict[str, Any]]] = [
        ("tokens", item) for item in design.get("tokens", [])
    ]
    for kind in ("components_catalog", "brand_assets"):
        if design.get(kind):
            declared.append((kind, design[kind]))
    artifact_checks: list[dict[str, Any]] = []
    for kind, item in declared:
        path = (base / item["path"]).resolve()
        expected = item.get("sha256")
        check: dict[str, Any] = {"kind": kind, "path": item["path"], "expected_sha256": expected}
        if not path.is_file():
            check.update(actual_sha256=None, status="missing")
        else:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            check["actual_sha256"] = actual
            if not expected:
                check["status"] = "unfrozen"
            elif actual.lower() == expected.lower():
                check["status"] = "match"
            else:
                check["status"] = "mismatch"
        artifact_checks.append(check)

    skip_patterns = list(design.get("style_zones", [])) + list(design.get("literal_exemptions", []))
    counts = {"color_literals": 0, "px_font_sizes": 0}
    literals: list[dict[str, Any]] = []
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in IGNORED_DIRS)
        for name in sorted(files):
            path = Path(current) / name
            if path.suffix.lower() not in STYLE_SOURCE_SUFFIXES:
                continue
            relative = path.relative_to(root).as_posix()
            if any(fnmatch.fnmatch(relative, pattern) for pattern in skip_patterns):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                for code, regex, key in (
                    ("color-literal", COLOR_LITERAL_RE, "color_literals"),
                    ("px-font-size", PX_FONT_SIZE_RE, "px_font_sizes"),
                ):
                    for match in regex.finditer(line):
                        counts[key] += 1
                        if len(literals) < MAX_REPORTED_STYLE_LITERALS:
                            literals.append(
                                {"path": relative, "line": number, "code": code, "match": match.group(0)}
                            )

    total = counts["color_literals"] + counts["px_font_sizes"]
    maximum = int(design.get("max_literal_violations", 0))
    frozen = bool(artifact_checks) and all(check["status"] == "match" for check in artifact_checks)
    findings: list[str] = []
    if design.get("status") != "confirmed":
        findings.append(f"design_system.status is {design.get('status')!r}, expected 'confirmed'")
    if not design.get("tokens"):
        findings.append("design_system declares no tokens")
    findings.extend(
        f"{check['kind']} {check['path']}: {check['status']}"
        for check in artifact_checks
        if check["status"] != "match"
    )
    if total > maximum:
        findings.append(
            f"{total} style literal(s) outside style_zones/literal_exemptions exceed "
            f"max_literal_violations={maximum}"
        )
    return {
        "valid": not findings,
        "component_id": component_id,
        "frozen": frozen,
        "artifact_checks": artifact_checks,
        "counts": counts,
        "max_literal_violations": maximum,
        "literal_violations": literals,
        "truncated": total > len(literals),
        "findings": findings,
        "message": (
            "component conforms to its frozen design system"
            if not findings
            else "design system is not frozen or style literals exceed the declared ratchet"
        ),
    }


def version_tuple(value: str) -> tuple[int, int, int, str]:
    match = re.match(r"^\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(.*)$", value or "")
    if not match:
        return (0, 0, 0, value or "")
    return (
        int(match.group(1)),
        int(match.group(2) or 0),
        int(match.group(3) or 0),
        match.group(4) or "",
    )


def infer_version_scheme(language: str | None) -> str:
    normalized = (language or "").strip().lower()
    if normalized in {"javascript", "typescript", "node", "nodejs"}:
        return "semver"
    if normalized == "python":
        return "pep440"
    if normalized in {"java", "kotlin", "scala"}:
        return "maven"
    if normalized in {"c#", "csharp", "f#", "fsharp", ".net", "dotnet"}:
        return "nuget"
    return "generic"


def is_exact_version(value: str | None, scheme: str | None = None) -> bool:
    if not value:
        return False
    candidate = value.strip()
    if not candidate or candidate.lower() == "latest":
        return False
    if re.search(r"[<>=^~*|,\[\](){}\s]", candidate) or re.search(
        r"(?:^|\.)[xX](?:\.|$)", candidate
    ):
        return False
    selected_scheme = (scheme or "generic").lower()
    if selected_scheme in {"semver", "nuget"}:
        return bool(
            re.fullmatch(
                r"v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?",
                candidate,
            )
        )
    if selected_scheme == "pep440":
        try:
            Version(candidate)
            return True
        except InvalidVersion:
            return False
    return bool(re.fullmatch(r"[0-9][0-9A-Za-z._+-]*", candidate))


def _pep440_compatible_match(version: str, constraint: str) -> bool:
    raw_constraint = constraint.strip()
    try:
        parsed_version = Version(version.strip())
    except InvalidVersion:
        return version.strip().lower() == raw_constraint.lower()

    wildcard = re.fullmatch(r"v?(\d+)(?:\.(\d+))?\.(?:x|\*)", raw_constraint, re.IGNORECASE)
    if wildcard:
        prefix = tuple(int(part) for part in wildcard.groups() if part is not None)
        return parsed_version.release[: len(prefix)] == prefix

    caret = re.fullmatch(r"\^\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", raw_constraint)
    if caret:
        major, minor, patch = (int(part or 0) for part in caret.groups())
        lower = Version(f"{major}.{minor}.{patch}")
        if major > 0:
            upper = Version(f"{major + 1}.0.0")
        elif minor > 0:
            upper = Version(f"0.{minor + 1}.0")
        else:
            upper = Version(f"0.0.{patch + 1}")
        return lower <= parsed_version < upper

    tilde = re.fullmatch(r"~\s*v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", raw_constraint)
    if tilde:
        major, minor, patch = (int(part or 0) for part in tilde.groups())
        lower = Version(f"{major}.{minor}.{patch}")
        upper = Version(f"{major}.{minor + 1}.0") if tilde.group(2) else Version(f"{major + 1}.0.0")
        return lower <= parsed_version < upper

    normalized = re.sub(r"(?<![<>=!~])=(?!=)", "==", raw_constraint)
    normalized = re.sub(r"\s+(?=[<>=!~])", ",", normalized)
    if re.fullmatch(r"v?\d+(?:\.\d+){0,2}(?:[-+][0-9A-Za-z.-]+)?", normalized):
        normalized = f"=={normalized}"
    try:
        return parsed_version in SpecifierSet(normalized)
    except InvalidSpecifier:
        return version.strip().lower() == raw_constraint.lower()


def _interval_match(version: str, constraint: str) -> bool:
    exact = re.fullmatch(r"\[\s*([^,\]]+)\s*\]", constraint)
    if exact:
        return _pep440_compatible_match(version, exact.group(1))
    interval = re.fullmatch(r"([\[(])\s*([^,]*)\s*,\s*([^\])}]*)\s*([\])])", constraint)
    if not interval:
        return _pep440_compatible_match(version, constraint)
    try:
        parsed = Version(version)
        lower = Version(interval.group(2)) if interval.group(2) else None
        upper = Version(interval.group(3)) if interval.group(3) else None
    except InvalidVersion:
        return False
    if lower and (parsed < lower or (parsed == lower and interval.group(1) == "(")):
        return False
    if upper and (parsed > upper or (parsed == upper and interval.group(4) == ")")):
        return False
    return True


def version_matches(
    version: str | None, constraint: str | None, scheme: str | None = None
) -> bool:
    if not constraint or not version:
        return True
    selected_scheme = (scheme or "pep440").lower()
    raw_constraint = constraint.strip()
    if selected_scheme == "semver" and "||" in raw_constraint:
        return any(
            _pep440_compatible_match(version, branch.strip())
            for branch in raw_constraint.split("||")
        )
    if selected_scheme in {"maven", "nuget"} and raw_constraint.startswith(("[", "(")):
        return _interval_match(version, raw_constraint)
    return _pep440_compatible_match(version, raw_constraint)


def resolve_catalog(
    catalog_path: Path,
    requirement_path: Path,
    verification_paths: Iterable[Path] = (),
) -> dict[str, Any]:
    catalog = load_document(catalog_path)
    requirement = load_document(requirement_path)
    errors = schema_errors("catalog", catalog)
    if isinstance(catalog, dict):
        errors.extend(semantic_errors("catalog", catalog, strict=True))
    if errors:
        raise BaselineError("Invalid catalog: " + "; ".join(errors))
    if not isinstance(requirement, dict):
        raise BaselineError("Requirement must be a YAML/JSON object")
    requirement_errors = schema_errors("requirement", requirement)
    if requirement_errors:
        raise BaselineError("Invalid requirement: " + "; ".join(requirement_errors))

    allowed_trust = set(requirement.get("allowed_trust", ["official", "approved"]))
    allowed_licenses = set(requirement.get("allowed_licenses", []))
    allowed_namespaces = set(requirement["allowed_namespaces"])
    allowed_sources = set(requirement["allowed_sources"])
    catalog_trust = catalog.get("trust", "experimental")
    catalog_namespace = catalog.get("namespace", "")
    required_exclusions = set(
        requirement.get(
            "required_exclusions",
            ["cicd", "iac", "containers", "cloud-provisioning", "deployment"],
        )
    )
    source_verifications = load_source_verifications(verification_paths)
    candidates: list[dict[str, Any]] = []

    for archetype in catalog.get("archetypes", []):
        reasons: list[str] = []
        score = 0
        compatibility = archetype.get("compatibility", {})
        capabilities = archetype.get("capabilities", {})
        permissions = archetype.get("permissions", {})
        version_scheme = (
            requirement.get("version_scheme")
            or compatibility.get("version_scheme")
            or infer_version_scheme(requirement.get("language"))
        )
        verification_key = (
            archetype["id"],
            archetype["source"],
            str(archetype["digest"]).lower(),
        )

        if catalog_trust not in allowed_trust:
            reasons.append(f"catalog trust {catalog_trust!r} is not allowed")
        if catalog_namespace not in allowed_namespaces:
            reasons.append(f"catalog namespace {catalog_namespace!r} is not allowed")
        if archetype["source"] not in allowed_sources:
            reasons.append("archetype source is not allowed")
        if verification_key not in source_verifications:
            reasons.append("source verification is required")
        if archetype["status"] == "retired":
            reasons.append("archetype is retired")
        if archetype["status"] == "deprecated" and not requirement.get("allow_deprecated"):
            reasons.append("archetype is deprecated")
        if archetype["status"] == "experimental" and not requirement.get("allow_experimental"):
            reasons.append("archetype is experimental")
        if allowed_licenses and archetype.get("license") not in allowed_licenses:
            reasons.append("license is not allowed")
        if archetype["workload"].lower() != str(requirement.get("workload", "")).lower():
            reasons.append("workload mismatch")
        else:
            score += 25
        if compatibility.get("language", "").lower() != str(requirement.get("language", "")).lower():
            reasons.append("language mismatch")
        else:
            score += 10
        if not version_matches(
            requirement.get("runtime"), compatibility.get("runtime"), version_scheme
        ):
            reasons.append("runtime mismatch")
        else:
            score += 10
        requested_framework = str(requirement.get("framework", "")).lower()
        catalog_framework = str(compatibility.get("framework", "")).lower()
        if requested_framework and catalog_framework != requested_framework:
            reasons.append("framework mismatch")
        elif requested_framework:
            score += 10
        if not version_matches(
            requirement.get("framework_version"),
            compatibility.get("framework_version"),
            version_scheme,
        ):
            reasons.append("framework version mismatch")
        elif requirement.get("framework_version"):
            score += 10
        requested_style = str(requirement.get("architecture_style", "")).lower()
        styles = {str(item).lower() for item in compatibility.get("architecture_styles", [])}
        if requested_style and requested_style not in styles:
            reasons.append("architecture style mismatch")
        elif requested_style:
            score += 15
        supported = set(capabilities.get("supported", [])) | set(capabilities.get("required", []))
        requested_capabilities = set(requirement.get("capabilities", []))
        missing_capabilities = requested_capabilities - supported
        if missing_capabilities:
            reasons.append(f"missing capabilities {sorted(missing_capabilities)}")
        else:
            score += 10
        incompatible = requested_capabilities & set(capabilities.get("incompatible", []))
        if incompatible:
            reasons.append(f"incompatible capabilities {sorted(incompatible)}")
        missing_exclusions = required_exclusions - set(archetype.get("exclusions", []))
        if missing_exclusions:
            reasons.append(f"missing required exclusions {sorted(missing_exclusions)}")
        allowed_permissions = set(requirement.get("allowed_permissions", []))
        for permission, enabled in permissions.items():
            if enabled and permission not in allowed_permissions:
                reasons.append(f"permission {permission!r} is not allowed")
        if archetype["status"] == "supported":
            score += 5

        candidates.append(
            {
                "id": archetype["id"],
                "family": archetype["family"],
                "version": archetype["version"],
                "eligible": not reasons,
                "score": score if not reasons else 0,
                "rejection_reasons": reasons,
                "source": archetype["source"],
                "digest": archetype["digest"],
                "generator": archetype["generator"],
                "source_verification": (
                    source_verifications.get(verification_key, {}).get("material_path")
                ),
            }
        )

    candidates.sort(
        key=lambda item: (
            not item["eligible"],
            -item["score"],
            tuple(-part for part in version_tuple(item["version"])[:3]),
            item["family"],
        )
    )
    selected = next((item for item in candidates if item["eligible"]), None)
    return {
        "catalog": str(catalog_path.resolve()),
        "requirement": str(requirement_path.resolve()),
        "selected": selected,
        "strategy": "reuse" if selected else "no-match",
        "candidates": candidates,
    }


def evaluate_routing(evaluation_path: Path, observations_path: Path) -> dict[str, Any]:
    evaluation = load_document(evaluation_path)
    observations = load_document(observations_path)
    evaluation_errors = schema_errors("evaluation", evaluation)
    observation_errors = schema_errors("observations", observations)
    if evaluation_errors:
        raise BaselineError("Invalid routing evaluation: " + "; ".join(evaluation_errors))
    if observation_errors:
        raise BaselineError("Invalid routing observations: " + "; ".join(observation_errors))

    expected_ids = [case["id"] for case in evaluation["cases"]]
    observed_ids = [case["id"] for case in observations["observations"]]
    duplicate_expected = sorted({case_id for case_id in expected_ids if expected_ids.count(case_id) > 1})
    duplicate_observed = sorted({case_id for case_id in observed_ids if observed_ids.count(case_id) > 1})
    if duplicate_expected or duplicate_observed:
        raise BaselineError(
            f"Routing case IDs must be unique; evaluation={duplicate_expected}, observations={duplicate_observed}"
        )
    expected = {case["id"]: case for case in evaluation["cases"]}
    observed = {case["id"]: case for case in observations["observations"]}
    failures: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    for case_id, expected_case in expected.items():
        actual = observed.get(case_id)
        reasons: list[str] = []
        if actual is None:
            reasons.append("missing observation")
        else:
            if actual["routed"] is not expected_case["should_route"]:
                reasons.append(
                    f"routed={actual['routed']} expected={expected_case['should_route']}"
                )
            required_modes = set(expected_case.get("expected_modes", []))
            actual_modes = set(actual.get("modes", []))
            if expected_case["should_route"] and not required_modes.issubset(actual_modes):
                reasons.append(f"missing expected modes {sorted(required_modes - actual_modes)}")
            if not expected_case["should_route"] and actual_modes:
                reasons.append("non-routed observation must not report modes")
        result = {"id": case_id, "passed": not reasons, "reasons": reasons}
        cases.append(result)
        if reasons:
            failures.append(result)

    for case_id in sorted(set(observed) - set(expected)):
        failure = {"id": case_id, "passed": False, "reasons": ["unexpected observation"]}
        cases.append(failure)
        failures.append(failure)

    return {
        "valid": not failures,
        "evaluation": str(evaluation_path.resolve()),
        "observations": str(observations_path.resolve()),
        "total": len(cases),
        "passed": len(cases) - len(failures),
        "failures": failures,
        "cases": cases,
        "note": "Observation-backed contract check; it does not invoke a model.",
    }


def initialize_artifacts(
    solution_id: str, solution_name: str | None, architecture_root: str, output_root: Path
) -> dict[str, Any]:
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$", solution_id):
        raise BaselineError("solution-id must contain only letters, digits, dots, underscores, or hyphens")
    output_root = output_root.resolve()
    blueprint_path = output_root / "solution-blueprint.yaml"
    run_id = f"sb-{utc_now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    run_path = output_root / "runs" / run_id / "run-manifest.yaml"
    if blueprint_path.exists():
        raise BaselineError(f"Refusing to overwrite existing blueprint: {blueprint_path}")

    blueprint = {
        "schema_version": 1,
        "solution": {
            "id": solution_id,
            "name": solution_name or solution_id,
            "description": "Architecture-derived solution baseline",
        },
        "sources": [
            {"path": architecture_root.replace("\\", "/"), "kind": "architecture", "status": "pending"}
        ],
        "catalogs": [],
        "components": [],
        "contracts": [],
        "decisions": [],
        "exclusions": [
            "cicd",
            "iac",
            "containers",
            "cloud-provisioning",
            "deployment",
        ],
    }
    dump_yaml_atomic(blueprint_path, blueprint)
    blueprint_hash = hash_file(blueprint_path)
    now = isoformat()
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "solution_id": solution_id,
        "status": "discovered",
        "created_at": now,
        "updated_at": now,
        "blueprint": {"path": blueprint_path.relative_to(output_root).as_posix(), "sha256": blueprint_hash},
        "dag": {"nodes": [], "barriers": []},
        "catalog_resolutions": [],
        "archetype_builds": [],
        "instances": [],
        "leases": [],
        "steps": [],
        "decisions": [],
        "blockers": [],
        "architecture_gaps": [],
        "handoff": {},
    }
    dump_yaml_atomic(run_path, manifest)
    return {
        "solution_id": solution_id,
        "run_id": run_id,
        "blueprint": str(blueprint_path),
        "run_manifest": str(run_path),
        "note": "Blueprint is a valid draft; add components and resolve pending evidence before strict validation",
    }


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise BaselineError(f"Invalid lease timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise BaselineError("Lease timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def validate_lease_path(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.parent.name.lower() != "leases":
        raise BaselineError("Lease files must live directly inside a directory named 'leases'")
    if resolved.suffix.lower() not in LEASE_SUFFIXES:
        raise BaselineError("Lease file must use .json, .yaml, or .yml")
    return resolved


def validate_lease_document(lease: Any) -> dict[str, Any]:
    if not isinstance(lease, dict):
        raise BaselineError("Lease document must be an object")
    if lease.get("schema_version") != 1:
        raise BaselineError("Lease schema_version must be 1")
    for field in ("owner", "resource", "lease_id", "acquired_at", "expires_at"):
        if not isinstance(lease.get(field), str) or not lease[field].strip():
            raise BaselineError(f"Lease field {field!r} must be a non-empty string")
    acquired_at = parse_time(lease["acquired_at"])
    expires_at = parse_time(lease["expires_at"])
    if expires_at <= acquired_at:
        raise BaselineError("Lease expires_at must be later than acquired_at")
    return lease


def lease_lock(path: Path) -> FileLock:
    return FileLock(str(path) + ".lock", timeout=5)


def acquire_lease(path: Path, owner: str, resource: str | None, ttl_seconds: int) -> dict[str, Any]:
    if ttl_seconds < 1:
        raise BaselineError("ttl-seconds must be positive")
    if not owner.strip():
        raise BaselineError("owner must be a non-empty string")
    path = validate_lease_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    lease = {
        "schema_version": 1,
        "owner": owner,
        "resource": resource or path.stem,
        "acquired_at": isoformat(now),
        "expires_at": isoformat(now + timedelta(seconds=ttl_seconds)),
        "lease_id": uuid.uuid4().hex,
    }
    try:
        with lease_lock(path):
            if not path.exists():
                dump_document_atomic(path, lease)
                return {"status": "acquired", "lease": lease}
            current = validate_lease_document(load_document(path))
            expired = parse_time(current["expires_at"]) <= now
            if not expired and current.get("owner") != owner:
                raise BaselineError(
                    f"Lease is held by {current.get('owner')} until {current.get('expires_at')}"
                )
            lease["recovered_from"] = current.get("lease_id")
            dump_document_atomic(path, lease)
            status = "renewed" if current.get("owner") == owner else "recovered"
            return {"status": status, "lease": lease}
    except FileLockTimeout as exc:
        raise BaselineError(f"Timed out acquiring lease lock for {path}") from exc


def lease_status(path: Path) -> dict[str, Any]:
    path = validate_lease_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lease_lock(path):
            if not path.exists():
                return {"status": "available", "file": str(path)}
            lease = validate_lease_document(load_document(path))
            expired = parse_time(lease["expires_at"]) <= utc_now()
            return {"status": "expired" if expired else "held", "file": str(path), "lease": lease}
    except FileLockTimeout as exc:
        raise BaselineError(f"Timed out reading lease lock for {path}") from exc


def release_lease(path: Path, owner: str) -> dict[str, Any]:
    path = validate_lease_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lease_lock(path):
            if not path.exists():
                return {"status": "already-available", "file": str(path)}
            lease = validate_lease_document(load_document(path))
            if lease.get("owner") != owner:
                raise BaselineError(f"Lease belongs to {lease.get('owner')}, not {owner}")
            path.unlink()
            return {"status": "released", "file": str(path), "lease_id": lease.get("lease_id")}
    except FileLockTimeout as exc:
        raise BaselineError(f"Timed out releasing lease lock for {path}") from exc


def record_step(manifest_path: Path, result_path: Path, run_status: str | None) -> dict[str, Any]:
    manifest = load_document(manifest_path)
    result = load_document(result_path)
    manifest_validation = schema_errors("run", manifest)
    result_validation = schema_errors("result", result)
    if manifest_validation:
        raise BaselineError("Invalid run manifest: " + "; ".join(manifest_validation))
    if result_validation:
        raise BaselineError("Invalid generator result: " + "; ".join(result_validation))

    logical_key = (
        result["repository_id"],
        result["operation"],
        result["idempotency_key"],
    )
    for existing in manifest.get("steps", []):
        existing_key = (
            existing["repository_id"],
            existing["operation"],
            existing["idempotency_key"],
        )
        if existing_key == logical_key:
            if existing.get("input_hash") != result.get("input_hash"):
                raise BaselineError("Idempotency key was already used with a different input hash")
            return {"status": "unchanged", "reason": "step already recorded", "key": logical_key}

    manifest.setdefault("steps", []).append(result)
    manifest["updated_at"] = isoformat()
    if run_status:
        manifest["status"] = run_status
    elif result["status"] in {"failed", "blocked"}:
        succeeded = any(step.get("status") == "succeeded" for step in manifest["steps"][:-1])
        manifest["status"] = "partial" if succeeded else "blocked"
    elif result["status"] == "partial":
        manifest["status"] = "partial"
    dump_yaml_atomic(manifest_path.resolve(), manifest)
    return {"status": "recorded", "key": logical_key, "run_status": manifest["status"]}


def audit_scope(paths: list[str]) -> dict[str, Any]:
    policy = load_document(SCOPE_POLICY)
    policy_errors = schema_errors("scope-policy", policy)
    if policy_errors:
        raise BaselineError("Invalid scope policy: " + "; ".join(policy_errors))
    forbidden_directories = set(policy["forbidden_directories"])
    forbidden_files = set(policy["forbidden_files"])
    forbidden_suffixes = set(policy["forbidden_suffixes"])
    forbidden_file_globs = tuple(policy["forbidden_file_globs"])
    forbidden_sequences = tuple(tuple(item) for item in policy["forbidden_path_sequences"])
    normalized_paths: set[str] = set()
    for raw_path in paths:
        if not raw_path.strip():
            continue
        candidate = raw_path.strip().replace("\\", "/")
        segments: list[str] = []
        escaped = False
        for segment in candidate.split("/"):
            if not segment or segment == ".":
                continue
            if segment == "..":
                if segments and not segments[-1].endswith(":"):
                    segments.pop()
                else:
                    escaped = True
                continue
            segments.append(segment)
        normalized_path = "/".join(segments)
        if escaped:
            normalized_path = f"../{normalized_path}"
        normalized_paths.add(normalized_path)
    normalized = sorted(normalized_paths)
    violations: list[dict[str, str]] = []
    for path in normalized:
        lowered = path.lower().strip("/")
        parts = tuple(part for part in lowered.split("/") if part)
        basename = parts[-1] if parts else ""
        matched: str | None = None
        if lowered.startswith("../"):
            matched = "path-traversal"
        elif any(
            parts[index:index + len(sequence)] == sequence
            for sequence in forbidden_sequences
            for index in range(len(parts) - len(sequence) + 1)
        ):
            matched = "forbidden-path-sequence"
        elif basename in forbidden_files:
            matched = f"**/{basename}"
        elif next((pattern for pattern in forbidden_file_globs if fnmatch.fnmatch(basename, pattern)), None):
            matched = next(
                pattern for pattern in forbidden_file_globs if fnmatch.fnmatch(basename, pattern)
            )
        elif any(basename.endswith(suffix) for suffix in forbidden_suffixes):
            matched = "forbidden-suffix"
        else:
            forbidden_segment = next(
                (part for part in parts if part in forbidden_directories), None
            )
            if forbidden_segment:
                matched = f"**/{forbidden_segment}/**"
        if matched:
            violations.append({"path": path, "pattern": matched})
    return {
        "valid": not violations,
        "checked": len(normalized),
        "violations": violations,
        "message": "DevOps/IaC/container/deployment paths belong to Vulcano" if violations else "scope is clean",
    }


def load_change_paths(path: Path) -> list[str]:
    if path.suffix.lower() in {".yaml", ".yml", ".json"}:
        payload = load_document(path)
        if isinstance(payload, list):
            return [str(item) for item in payload]
        if isinstance(payload, dict):
            values = payload.get("paths") or payload.get("changes") or []
            if isinstance(values, dict):
                flattened: list[str] = []
                for entries in values.values():
                    if isinstance(entries, list):
                        flattened.extend(str(item) for item in entries)
                return flattened
            return [str(item) for item in values]
        raise BaselineError("Changes document must contain a list or paths/changes object")
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_genesis_migration(
    matrix_path: Path = GENESIS_EQUIVALENCE_MATRIX,
    genesis_root: Path | None = None,
) -> dict[str, Any]:
    """Verify that Genesis is a thin alias and greenfield coverage is owned here.

    This proves contract coverage and retirement prerequisites. It deliberately
    does not claim that unpublished archetypes have passed executable golden
    project tests.
    """
    matrix_path = matrix_path.resolve()
    genesis_root = (
        genesis_root or Path.cwd() / ".claude" / "skills" / "genesis"
    ).resolve()
    errors: list[str] = []
    matrix = load_document(matrix_path)
    if not isinstance(matrix, dict):
        raise BaselineError("Genesis equivalence matrix must be an object")

    if matrix.get("legacy_skill") != "genesis":
        errors.append("legacy_skill must be genesis")
    if matrix.get("target_skill") != "solution-baseline":
        errors.append("target_skill must be solution-baseline")
    if matrix.get("equivalence_level") != "contractual":
        errors.append("equivalence_level must be contractual until archetypes are published")

    required_outcomes = set(matrix.get("required_outcomes") or [])
    expected_outcomes = {
        "manifest",
        "source-layout",
        "configuration",
        "dependency-injection",
        "error-handling",
        "logging",
        "health-or-smoke",
        "tests",
        "living-documentation",
        "receipt",
    }
    missing_outcomes = expected_outcomes - required_outcomes
    if missing_outcomes:
        errors.append(f"required_outcomes missing {sorted(missing_outcomes)}")

    required_exclusions = {
        "cicd", "iac", "containers", "cloud-provisioning", "deployment"
    }
    missing_exclusions = required_exclusions - set(matrix.get("forbidden_outcomes") or [])
    if missing_exclusions:
        errors.append(f"forbidden_outcomes missing {sorted(missing_exclusions)}")

    registry = load_document(ADAPTER_REGISTRY)
    adapters = {adapter["id"]: adapter for adapter in registry.get("adapters", [])}
    workload_results: list[dict[str, Any]] = []
    seen_workloads: set[str] = set()
    for index, workload in enumerate(matrix.get("workloads") or []):
        workload_id = str(workload.get("id", ""))
        adapter_id = str(workload.get("adapter", ""))
        workload_errors: list[str] = []
        if workload_id in seen_workloads:
            workload_errors.append("duplicate workload")
        seen_workloads.add(workload_id)
        adapter = adapters.get(adapter_id)
        if not adapter:
            workload_errors.append(f"unknown adapter {adapter_id}")
        elif workload_id not in adapter.get("workloads", []):
            workload_errors.append(f"adapter {adapter_id} does not support {workload_id}")
        evidence = workload.get("evidence") or []
        if not evidence:
            workload_errors.append("no evidence references")
        for relative in evidence:
            evidence_path = (SKILL_ROOT / str(relative)).resolve()
            try:
                evidence_path.relative_to(SKILL_ROOT.resolve())
            except ValueError:
                workload_errors.append(f"evidence escapes skill root: {relative}")
                continue
            if not evidence_path.is_file():
                workload_errors.append(f"missing evidence: {relative}")
        if workload_errors:
            errors.extend(f"workloads/{index}: {item}" for item in workload_errors)
        workload_results.append(
            {"id": workload_id, "adapter": adapter_id, "valid": not workload_errors}
        )

    expected_workloads = {"web", "api", "worker", "agent"}
    missing_workloads = expected_workloads - seen_workloads
    if missing_workloads:
        errors.append(f"workloads missing {sorted(missing_workloads)}")

    alias_path = genesis_root / "SKILL.md"
    if not alias_path.is_file():
        errors.append(f"Genesis compatibility alias is missing: {alias_path}")
    else:
        alias = alias_path.read_text(encoding="utf-8").lower()
        alias_requirements = {
            "deprecated marker": "obsoleto",
            "target skill": "solution-baseline",
            "create translation": "--mode create",
            "invocation evidence": "invocation_alias: genesis",
        }
        for label, marker in alias_requirements.items():
            if marker not in alias:
                errors.append(f"Genesis alias missing {label}: {marker}")
        if "@latest" in alias:
            errors.append("Genesis alias retains an @latest bootstrap instruction")

    gate = matrix.get("retirement_gate") or {}
    required_projects = gate.get("required_successful_projects", 2)
    successful_projects = gate.get("successful_projects", 0)
    if not isinstance(required_projects, int) or required_projects < 2:
        errors.append("retirement_gate.required_successful_projects must be at least 2")
    if not isinstance(successful_projects, int) or successful_projects < 0:
        errors.append("retirement_gate.successful_projects must be a non-negative integer")
    retirement_ready = bool(
        not errors
        and gate.get("archetypes_published") is True
        and isinstance(required_projects, int)
        and isinstance(successful_projects, int)
        and successful_projects >= required_projects
        and len(gate.get("evidence") or []) >= required_projects
    )
    return {
        "valid": not errors,
        "equivalence_level": matrix.get("equivalence_level"),
        "matrix": str(matrix_path),
        "workloads": workload_results,
        "retirement_ready": retirement_ready,
        "retirement_gate": gate,
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic local helpers for the solution-baseline skill"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate an artifact against its schema")
    validate_parser.add_argument("--kind", choices=sorted(SCHEMAS), required=True)
    validate_parser.add_argument("--file", type=Path, required=True)
    validate_parser.add_argument("--strict", action="store_true")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a repository without executing it")
    inspect_parser.add_argument("--root", type=Path, required=True)
    inspect_parser.add_argument("--output", type=Path)

    hash_parser = subparsers.add_parser("hash", help="Calculate a deterministic directory hash")
    hash_parser.add_argument("--root", type=Path, required=True)

    diff_parser = subparsers.add_parser("diff", help="Compare rendered and actual directory trees")
    diff_parser.add_argument("--expected", type=Path, required=True)
    diff_parser.add_argument("--actual", type=Path, required=True)
    diff_parser.add_argument("--output", type=Path)

    resolve_parser = subparsers.add_parser("resolve", help="Resolve a requirement against a catalog")
    resolve_parser.add_argument("--catalog", type=Path, required=True)
    resolve_parser.add_argument("--requirement", type=Path, required=True)
    resolve_parser.add_argument(
        "--verification",
        type=Path,
        action="append",
        default=[],
        help="Repeatable local source-verification artifact",
    )
    resolve_parser.add_argument("--output", type=Path)

    verify_parser = subparsers.add_parser(
        "verify-source", help="Attest local archetype material against an immutable digest"
    )
    verify_parser.add_argument("--archetype-id", required=True)
    verify_parser.add_argument("--source", required=True)
    verify_parser.add_argument("--material", type=Path, required=True)
    verify_parser.add_argument("--digest", required=True)
    verify_parser.add_argument("--output", type=Path, required=True)

    routing_parser = subparsers.add_parser(
        "evaluate-routing", help="Compare routing observations with the evaluation contract"
    )
    routing_parser.add_argument("--evaluation", type=Path, required=True)
    routing_parser.add_argument("--observations", type=Path, required=True)
    routing_parser.add_argument("--output", type=Path)

    init_parser = subparsers.add_parser("init", help="Create draft blueprint and run manifest")
    init_parser.add_argument("--solution-id", required=True)
    init_parser.add_argument("--solution-name")
    init_parser.add_argument("--architecture-root", required=True)
    init_parser.add_argument("--output-root", type=Path, required=True)

    record_parser = subparsers.add_parser("record-step", help="Atomically append an idempotent result")
    record_parser.add_argument("--manifest", type=Path, required=True)
    record_parser.add_argument("--result", type=Path, required=True)
    record_parser.add_argument(
        "--run-status",
        choices=["discovered", "planned", "rendered", "reviewed", "applying", "validating", "partial", "blocked", "completed"],
    )

    audit_parser = subparsers.add_parser("audit-scope", help="Reject DevOps/IaC paths from a baseline change set")
    audit_parser.add_argument("--changes", type=Path, required=True)

    drift_parser = subparsers.add_parser(
        "check-drift", help="Verify receipt `managed` files were not hand-edited outside the skill"
    )
    drift_parser.add_argument("--root", type=Path, required=True)
    drift_parser.add_argument(
        "--receipt", type=Path, help="Defaults to <root>/.solution-baseline/receipt.yaml"
    )

    gate_parser = subparsers.add_parser(
        "check-gate-coverage",
        help="Verify every declared quality_gate has a matching receipt validation",
    )
    gate_parser.add_argument("--blueprint", type=Path, required=True)
    gate_parser.add_argument("--component", required=True)
    gate_parser.add_argument("--receipt", type=Path, required=True)

    boundary_parser = subparsers.add_parser(
        "check-boundary-coverage",
        help="Detect folders on disk not covered by a declared boundary allow-list",
    )
    boundary_parser.add_argument("--root", type=Path, required=True)
    boundary_parser.add_argument(
        "--discover-glob",
        required=True,
        help="Glob (relative to --root) whose matching directories must be covered, e.g. src/features/*",
    )
    boundary_parser.add_argument(
        "--declared",
        action="append",
        default=[],
        help="Repeatable: a folder name already covered by the boundary config",
    )

    design_parser = subparsers.add_parser(
        "check-design-conformance",
        help="Verify a web/library component against its frozen design system",
    )
    design_parser.add_argument("--root", type=Path, required=True, help="Component repository to scan")
    design_parser.add_argument("--blueprint", type=Path, required=True)
    design_parser.add_argument("--component", required=True)
    design_parser.add_argument(
        "--solution-root",
        type=Path,
        help="Base for design_system paths; defaults to the current directory",
    )

    genesis_parser = subparsers.add_parser(
        "verify-genesis-migration",
        help="Verify Genesis alias, greenfield contract coverage, and retirement gates",
    )
    genesis_parser.add_argument("--matrix", type=Path, default=GENESIS_EQUIVALENCE_MATRIX)
    genesis_parser.add_argument(
        "--genesis-root",
        type=Path,
        help="Defaults to <current-directory>/.claude/skills/genesis",
    )

    agents_parser = subparsers.add_parser(
        "agents", help="Install or verify the packaged solution-baseline agents"
    )
    agents_subparsers = agents_parser.add_subparsers(dest="agents_command", required=True)
    agents_install_parser = agents_subparsers.add_parser("install")
    agents_install_parser.add_argument("--project-root", type=Path, required=True)
    agents_install_parser.add_argument(
        "--platform", choices=["claude", "codex"], nargs="+", default=["claude", "codex"]
    )
    agents_install_parser.add_argument("--force", action="store_true")
    agents_install_parser.add_argument("--configure-runtime", action="store_true")
    agents_install_parser.add_argument("--force-config", action="store_true")
    agents_check_parser = agents_subparsers.add_parser("check")
    agents_check_parser.add_argument("--project-root", type=Path, required=True)
    agents_check_parser.add_argument(
        "--platform", choices=["claude", "codex"], nargs="+", default=["claude", "codex"]
    )
    agents_check_parser.add_argument("--skip-runtime-check", action="store_true")

    workspace_parser = subparsers.add_parser(
        "verify-workspace", help="Fail unless a mutable agent runs outside the main checkout"
    )
    workspace_parser.add_argument("--workspace", type=Path, required=True)
    workspace_parser.add_argument("--main-checkout", type=Path, required=True)
    workspace_parser.add_argument("--allow-non-git", action="store_true")

    concurrency_parser = subparsers.add_parser(
        "check-concurrency", help="Validate a proposed or active agent assignment wave"
    )
    concurrency_parser.add_argument("--assignments", type=Path, required=True)
    concurrency_parser.add_argument("--policy", type=Path, default=CONCURRENCY_POLICY)

    lease_parser = subparsers.add_parser("lease", help="Manage a local writer lease")
    lease_subparsers = lease_parser.add_subparsers(dest="lease_command", required=True)
    acquire_parser = lease_subparsers.add_parser("acquire")
    acquire_parser.add_argument("--file", type=Path, required=True)
    acquire_parser.add_argument("--owner", required=True)
    acquire_parser.add_argument("--resource")
    acquire_parser.add_argument("--ttl-seconds", type=int, default=900)
    status_parser = lease_subparsers.add_parser("status")
    status_parser.add_argument("--file", type=Path, required=True)
    release_parser = lease_subparsers.add_parser("release")
    release_parser.add_argument("--file", type=Path, required=True)
    release_parser.add_argument("--owner", required=True)

    return parser


def write_optional_output(payload: Any, output: Path | None) -> None:
    if output:
        if output.exists():
            raise BaselineError(f"Refusing to overwrite output: {output}")
        dump_document_atomic(output.resolve(), payload)
    json_output(payload)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            payload = validate(args.kind, args.file, args.strict)
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "inspect":
            write_optional_output(inspect_repository(args.root), args.output)
            return 0
        if args.command == "hash":
            json_output(hash_tree(args.root))
            return 0
        if args.command == "diff":
            write_optional_output(diff_trees(args.expected, args.actual), args.output)
            return 0
        if args.command == "resolve":
            payload = resolve_catalog(args.catalog, args.requirement, args.verification)
            write_optional_output(payload, args.output)
            return 0 if payload["selected"] else 2
        if args.command == "verify-source":
            payload = verify_source_material(
                args.archetype_id, args.source, args.material, args.digest
            )
            write_optional_output(payload, args.output)
            return 0
        if args.command == "evaluate-routing":
            payload = evaluate_routing(args.evaluation, args.observations)
            write_optional_output(payload, args.output)
            return 0 if payload["valid"] else 1
        if args.command == "init":
            json_output(
                initialize_artifacts(
                    args.solution_id,
                    args.solution_name,
                    args.architecture_root,
                    args.output_root,
                )
            )
            return 0
        if args.command == "record-step":
            json_output(record_step(args.manifest, args.result, args.run_status))
            return 0
        if args.command == "audit-scope":
            payload = audit_scope(load_change_paths(args.changes))
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "check-drift":
            receipt_path = args.receipt or (args.root / ".solution-baseline" / "receipt.yaml")
            payload = check_drift(args.root, receipt_path)
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "check-gate-coverage":
            payload = gate_coverage(args.blueprint, args.component, args.receipt)
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "check-boundary-coverage":
            payload = check_boundary_coverage(args.root, args.discover_glob, args.declared)
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "check-design-conformance":
            payload = check_design_conformance(
                args.root, args.blueprint, args.component, args.solution_root
            )
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "verify-genesis-migration":
            payload = verify_genesis_migration(args.matrix, args.genesis_root)
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "agents":
            if args.agents_command == "install":
                payload = install_agents(
                    args.project_root,
                    args.platform,
                    force=args.force,
                    configure_runtime=args.configure_runtime,
                    force_config=args.force_config,
                )
            else:
                payload = check_agents(
                    args.project_root,
                    args.platform,
                    require_codex_runtime=not args.skip_runtime_check,
                )
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "verify-workspace":
            payload = verify_workspace_isolation(
                args.workspace, args.main_checkout, args.allow_non_git
            )
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "check-concurrency":
            payload = check_concurrency(args.assignments, args.policy)
            json_output(payload)
            return 0 if payload["valid"] else 1
        if args.command == "lease":
            if args.lease_command == "acquire":
                json_output(acquire_lease(args.file, args.owner, args.resource, args.ttl_seconds))
            elif args.lease_command == "status":
                json_output(lease_status(args.file))
            else:
                json_output(release_lease(args.file, args.owner))
            return 0
    except BaselineError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
