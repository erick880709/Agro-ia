from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import solution_baseline as sb  # noqa: E402


class SolutionBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create_genesis_alias(self) -> Path:
        genesis = self.root / "genesis"
        genesis.mkdir(exist_ok=True)
        (genesis / "SKILL.md").write_text(
            """---
name: genesis
description: Alias obsoleto de compatibilidad.
---
Usa solution-baseline --mode create.
Registra invocation_alias: genesis.
""",
            encoding="utf-8",
        )
        return genesis

    def test_bundled_templates_and_registry_validate(self) -> None:
        templates = sb.SKILL_ROOT / "assets" / "templates"
        cases = {
            "blueprint": templates / "solution-blueprint.template.yaml",
            "run": templates / "run-manifest.template.yaml",
            "receipt": templates / "receipt.template.yaml",
            "catalog": templates / "catalog.template.yaml",
            "result": templates / "generator-result.template.yaml",
            "requirement": templates / "archetype-requirement.template.yaml",
            "adapter": sb.ADAPTER_REGISTRY,
            "handoff": templates / "vulcano-handoff.template.yaml",
            "gap": templates / "architecture-gap.template.yaml",
            "evaluation": sb.SKILL_ROOT / "assets" / "evaluations" / "skill-routing.yaml",
            "verification": templates / "source-verification.template.yaml",
            "scope-policy": sb.SCOPE_POLICY,
            "concurrency-policy": sb.CONCURRENCY_POLICY,
            "assignments": templates / "agent-assignments.template.yaml",
        }
        for kind, path in cases.items():
            with self.subTest(kind=kind):
                result = sb.validate(kind, path)
                self.assertTrue(result["valid"], result["errors"])

    def test_strict_blueprint_requires_component_and_resolved_versions(self) -> None:
        blueprint = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "solution-blueprint.template.yaml"
        )
        path = self.root / "blueprint.yaml"
        sb.dump_yaml_atomic(path, blueprint)
        result = sb.validate("blueprint", path, strict=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("resolved exact version" in item for item in result["errors"]))

    def test_strict_blueprint_rejects_resolved_version_ranges(self) -> None:
        blueprint = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "solution-blueprint.template.yaml"
        )
        blueprint["sources"][0]["status"] = "confirmed"
        blueprint["components"][0]["stack"]["runtime"] = {
            "requested": ">=24 <25",
            "resolved": ">=24 <25",
            "scheme": "semver",
        }
        path = self.root / "blueprint-range.yaml"
        sb.dump_yaml_atomic(path, blueprint)
        result = sb.validate("blueprint", path, strict=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("exact version" in item for item in result["errors"]))

    def test_strict_catalog_rejects_placeholder_digest(self) -> None:
        catalog = sb.SKILL_ROOT / "assets" / "templates" / "catalog.template.yaml"
        result = sb.validate("catalog", catalog, strict=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("immutable sha256" in item for item in result["errors"]))

    def test_strict_handoff_requires_health_probe_and_ports_for_api(self) -> None:
        handoff = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "vulcano-handoff.template.yaml"
        )
        del handoff["service"]["ports"]
        handoff["containers"]["app"] = {"variables": {}}
        path = self.root / "handoff.yaml"
        sb.dump_yaml_atomic(path, handoff)
        result = sb.validate("handoff", path, strict=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("must declare at least one port" in item for item in result["errors"]))
        self.assertTrue(any("health probe is required" in item for item in result["errors"]))

    def test_init_creates_valid_draft_and_refuses_overwrite(self) -> None:
        output = self.root / "resources" / ".solution-baseline"
        result = sb.initialize_artifacts("demo", "Demo", "resources/architecture", output)
        blueprint = Path(result["blueprint"])
        manifest = Path(result["run_manifest"])
        self.assertTrue(sb.validate("blueprint", blueprint)["valid"])
        self.assertTrue(sb.validate("run", manifest)["valid"])
        with self.assertRaises(sb.BaselineError):
            sb.initialize_artifacts("demo", "Demo", "resources/architecture", output)

    def test_inspect_detects_react_vite_as_brownfield(self) -> None:
        (self.root / "src").mkdir()
        (self.root / "src" / "App.tsx").write_text("export const App = () => null;", encoding="utf-8")
        (self.root / "package.json").write_text(
            json.dumps(
                {
                    "dependencies": {"react": "18.3.1"},
                    "devDependencies": {"vite": "8.2.0"},
                    "scripts": {"build": "vite build"},
                }
            ),
            encoding="utf-8",
        )
        result = sb.inspect_repository(self.root)
        self.assertEqual("reconcile", result["strategy_hint"])
        self.assertEqual("react-vite", result["candidate_adapters"][0]["id"])

    def test_hash_ignores_dependencies_and_diff_is_stable(self) -> None:
        expected = self.root / "expected"
        actual = self.root / "actual"
        (expected / "src").mkdir(parents=True)
        (actual / "src").mkdir(parents=True)
        (expected / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
        (actual / "src" / "a.py").write_text("a = 2\n", encoding="utf-8")
        (expected / "src" / "b.py").write_text("b = 1\n", encoding="utf-8")
        (actual / "node_modules").mkdir()
        (actual / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")
        result = sb.diff_trees(expected, actual)
        self.assertEqual(["src/b.py"], result["changes"]["add"])
        self.assertEqual(["src/a.py"], result["changes"]["modify"])
        self.assertEqual([], result["changes"]["remove_candidate"])

    def test_check_drift_passes_for_matching_managed_files(self) -> None:
        (self.root / "src").mkdir()
        kept = self.root / "src" / "kept.py"
        kept.write_text("value = 1\n", encoding="utf-8")

        receipt = sb.load_document(sb.SKILL_ROOT / "assets" / "templates" / "receipt.template.yaml")
        receipt["ownership"] = [
            {"path": "src/kept.py", "category": "managed", "sha256": sb.hash_file(kept)},
        ]
        receipt_path = self.root / ".solution-baseline" / "receipt.yaml"
        sb.dump_yaml_atomic(receipt_path, receipt)

        result = sb.check_drift(self.root, receipt_path)
        self.assertTrue(result["valid"])
        self.assertEqual(1, result["checked"])
        self.assertEqual([], result["violations"])

    def test_check_drift_flags_modified_and_missing_managed_files(self) -> None:
        (self.root / "src").mkdir()
        changed = self.root / "src" / "changed.py"
        changed.write_text("value = 1\n", encoding="utf-8")
        removed = self.root / "src" / "removed.py"
        removed.write_text("value = 1\n", encoding="utf-8")

        receipt = sb.load_document(sb.SKILL_ROOT / "assets" / "templates" / "receipt.template.yaml")
        receipt["ownership"] = [
            {"path": "src/changed.py", "category": "managed", "sha256": sb.hash_file(changed)},
            {"path": "src/removed.py", "category": "managed", "sha256": sb.hash_file(removed)},
            {"path": "src/untracked.py", "category": "managed"},
            {"path": "src/edits-allowed.py", "category": "project_owned"},
        ]
        receipt_path = self.root / ".solution-baseline" / "receipt.yaml"
        sb.dump_yaml_atomic(receipt_path, receipt)

        changed.write_text("value = 2\n", encoding="utf-8")
        removed.unlink()

        result = sb.check_drift(self.root, receipt_path)
        self.assertFalse(result["valid"])
        self.assertEqual(2, result["checked"])
        self.assertEqual(["src/untracked.py"], result["unverifiable"])
        issues = {violation["path"]: violation["issue"] for violation in result["violations"]}
        self.assertEqual({"src/changed.py": "modified", "src/removed.py": "missing"}, issues)

    def test_gate_coverage_flags_a_declared_gate_that_was_never_recorded(self) -> None:
        blueprint = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "solution-blueprint.template.yaml"
        )
        blueprint_path = self.root / "blueprint.yaml"
        sb.dump_yaml_atomic(blueprint_path, blueprint)

        receipt = sb.load_document(sb.SKILL_ROOT / "assets" / "templates" / "receipt.template.yaml")
        receipt["validations"] = [{"id": "build", "status": "passed", "evidence": "ok"}]
        receipt_path = self.root / ".solution-baseline" / "receipt.yaml"
        sb.dump_yaml_atomic(receipt_path, receipt)

        result = sb.gate_coverage(blueprint_path, "example-api", receipt_path)
        self.assertFalse(result["valid"])
        self.assertEqual(["unit-tests"], result["missing_gates"])

        receipt["validations"].append({"id": "unit-tests", "status": "passed", "evidence": "ok"})
        sb.dump_yaml_atomic(receipt_path, receipt)
        result = sb.gate_coverage(blueprint_path, "example-api", receipt_path)
        self.assertTrue(result["valid"], result["missing_gates"])

    def test_boundary_coverage_flags_a_folder_missing_from_the_allow_list(self) -> None:
        features = self.root / "src" / "features"
        for name in ("vacancies", "candidates", "candidatePortal"):
            (features / name).mkdir(parents=True)

        result = sb.check_boundary_coverage(
            self.root, "src/features/*", ["vacancies", "candidates"]
        )
        self.assertFalse(result["valid"])
        self.assertEqual(["candidatePortal"], result["undeclared"])

        result = sb.check_boundary_coverage(
            self.root, "src/features/*", ["vacancies", "candidates", "candidatePortal"]
        )
        self.assertTrue(result["valid"], result["undeclared"])

    def test_catalog_resolution_applies_security_gates(self) -> None:
        catalog = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "catalog.template.yaml"
        )
        material = self.root / "verified-archetype"
        material.mkdir()
        (material / "template.txt").write_text("trusted template\n", encoding="utf-8")
        digest = "sha256:" + sb.hash_tree(material)["sha256"]
        catalog["archetypes"][0]["digest"] = digest
        catalog_path = self.root / "catalog.yaml"
        sb.dump_yaml_atomic(catalog_path, catalog)
        requirement_path = self.root / "requirement.yaml"
        requirement_path.write_text(
            yaml.safe_dump(
                {
                    "workload": "api",
                    "language": "python",
                    "runtime": "3.12.10",
                    "framework": "fastapi",
                    "architecture_style": "modular",
                    "capabilities": ["typed-openapi"],
                    "allowed_namespaces": ["example-org"],
                    "allowed_sources": [catalog["archetypes"][0]["source"]],
                    "allowed_licenses": ["Internal"],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        verification = sb.verify_source_material(
            catalog["archetypes"][0]["id"],
            catalog["archetypes"][0]["source"],
            material,
            digest,
        )
        verification_path = self.root / "verification.yaml"
        sb.dump_yaml_atomic(verification_path, verification)
        result = sb.resolve_catalog(catalog_path, requirement_path, [verification_path])
        self.assertIsNotNone(result["selected"])
        self.assertEqual("ps-api-python-fastapi-modular", result["selected"]["family"])

        unverified = sb.resolve_catalog(catalog_path, requirement_path)
        self.assertIsNone(unverified["selected"])
        self.assertIn(
            "source verification is required",
            unverified["candidates"][0]["rejection_reasons"],
        )

        forged = copy.deepcopy(verification)
        forged["expected_digest"] = "sha256:" + ("a" * 64)
        forged_path = self.root / "forged-verification.yaml"
        sb.dump_yaml_atomic(forged_path, forged)
        forged_validation = sb.validate("verification", forged_path, strict=True)
        self.assertFalse(forged_validation["valid"])
        self.assertTrue(any("must equal expected_digest" in item for item in forged_validation["errors"]))

        unsafe_catalog = copy.deepcopy(catalog)
        unsafe_catalog["archetypes"][0]["permissions"]["hooks"] = True
        unsafe_path = self.root / "unsafe-catalog.yaml"
        sb.dump_yaml_atomic(unsafe_path, unsafe_catalog)
        unsafe = sb.resolve_catalog(unsafe_path, requirement_path, [verification_path])
        self.assertIsNone(unsafe["selected"])
        self.assertTrue(
            any("permission 'hooks'" in reason for reason in unsafe["candidates"][0]["rejection_reasons"])
        )

        foreign_catalog = copy.deepcopy(catalog)
        foreign_catalog["archetypes"][0]["source"] = "https://unapproved.example/archetype.git"
        foreign_path = self.root / "foreign-catalog.yaml"
        sb.dump_yaml_atomic(foreign_path, foreign_catalog)
        foreign = sb.resolve_catalog(foreign_path, requirement_path, [verification_path])
        self.assertIsNone(foreign["selected"])
        self.assertIn("archetype source is not allowed", foreign["candidates"][0]["rejection_reasons"])

        (material / "template.txt").write_text("tampered\n", encoding="utf-8")
        with self.assertRaises(sb.BaselineError):
            sb.resolve_catalog(catalog_path, requirement_path, [verification_path])

    def test_catalog_resolver_rejects_placeholder_digest(self) -> None:
        catalog_path = sb.SKILL_ROOT / "assets" / "templates" / "catalog.template.yaml"
        requirement_path = sb.SKILL_ROOT / "assets" / "templates" / "archetype-requirement.template.yaml"
        with self.assertRaises(sb.BaselineError):
            sb.resolve_catalog(catalog_path, requirement_path)

    def test_version_constraints_follow_semver_caret_zero_rules(self) -> None:
        self.assertTrue(sb.version_matches("0.2.9", "^0.2.3"))
        self.assertFalse(sb.version_matches("0.3.0", "^0.2.3"))
        self.assertFalse(sb.version_matches("0.9.0", "^0.2.3"))
        self.assertTrue(sb.version_matches("3.12.10", ">=3.12 <3.13"))
        self.assertFalse(sb.version_matches("3.13.0", ">=3.12 <3.13"))

    def test_version_constraints_support_multiple_ecosystems(self) -> None:
        self.assertTrue(sb.version_matches("20.1.0", ">=18 <19 || >=20 <21", "semver"))
        self.assertFalse(sb.version_matches("19.0.0", ">=18 <19 || >=20 <21", "semver"))
        self.assertTrue(sb.version_matches("3.3.0", "[3.0,4.0)", "maven"))
        self.assertFalse(sb.version_matches("4.0.0", "[3.0,4.0)", "maven"))
        self.assertTrue(sb.version_matches("8.0.1", "[8.0.0,9.0.0)", "nuget"))

    def test_run_dag_rejects_unknown_dependencies_and_cycles(self) -> None:
        manifest = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "run-manifest.template.yaml"
        )
        manifest["blueprint"]["sha256"] = "a" * 64
        manifest["dag"]["nodes"] = [
            {"id": "api", "kind": "render", "status": "pending", "depends_on": ["missing"]},
        ]
        path = self.root / "unknown-dag.yaml"
        sb.dump_yaml_atomic(path, manifest)
        result = sb.validate("run", path, strict=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown nodes" in item for item in result["errors"]))

        manifest["dag"]["nodes"] = [
            {"id": "api", "kind": "render", "status": "pending", "depends_on": ["web"]},
            {"id": "web", "kind": "render", "status": "pending", "depends_on": ["api"]},
        ]
        path = self.root / "cyclic-dag.yaml"
        sb.dump_yaml_atomic(path, manifest)
        result = sb.validate("run", path, strict=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("dependency cycle" in item for item in result["errors"]))

    def make_validate_step(self, repository_id: str, status: str) -> dict:
        return {
            "operation": "validate",
            "status": status,
            "repository_id": repository_id,
            "idempotency_key": f"{repository_id}-validate-001",
            "artifacts": [],
            "decisions": [],
            "warnings": [],
            "evidence": [],
            "next_steps": [],
            "agent_context": {"mode": "validate"},
        }

    def test_completed_node_requires_a_succeeded_matching_step(self) -> None:
        manifest = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "run-manifest.template.yaml"
        )
        manifest["dag"]["nodes"] = [
            {
                "id": "validate-web",
                "kind": "validate",
                "repository_id": "web",
                "status": "completed",
                "depends_on": [],
            }
        ]
        manifest["steps"] = [self.make_validate_step("web", "partial")]
        path = self.root / "node-vs-step-mismatch.yaml"
        sb.dump_yaml_atomic(path, manifest)
        result = sb.validate("run", path)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("dag/nodes/0" in item and "status='partial'" in item for item in result["errors"])
        )

        manifest["steps"] = [self.make_validate_step("web", "succeeded")]
        sb.dump_yaml_atomic(path, manifest)
        result = sb.validate("run", path)
        self.assertTrue(result["valid"], result["errors"])

    def test_validated_instance_requires_a_succeeded_matching_step(self) -> None:
        manifest = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "run-manifest.template.yaml"
        )
        manifest["instances"] = [
            {
                "repository_id": "web",
                "path": "apps/web",
                "mode": "reconcile",
                "status": "validated",
            }
        ]
        manifest["steps"] = [self.make_validate_step("web", "partial")]
        path = self.root / "instance-vs-step-mismatch.yaml"
        sb.dump_yaml_atomic(path, manifest)
        result = sb.validate("run", path)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("instances/0" in item and "status='partial'" in item for item in result["errors"])
        )

        manifest["steps"] = [self.make_validate_step("web", "succeeded")]
        sb.dump_yaml_atomic(path, manifest)
        result = sb.validate("run", path)
        self.assertTrue(result["valid"], result["errors"])

    def test_completed_run_requires_finished_dag(self) -> None:
        manifest = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "run-manifest.template.yaml"
        )
        manifest["status"] = "completed"
        manifest["blueprint"]["sha256"] = "a" * 64
        manifest["dag"]["nodes"] = [
            {"id": "api", "kind": "render", "status": "running", "depends_on": []},
        ]
        manifest["dag"]["barriers"] = [
            {
                "id": "review",
                "kind": "review-approved",
                "status": "pending",
                "release_nodes": ["api"],
            }
        ]
        path = self.root / "unfinished-dag.yaml"
        sb.dump_yaml_atomic(path, manifest)
        result = sb.validate("run", path, strict=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unfinished DAG" in item for item in result["errors"]))
        self.assertTrue(any("unsatisfied DAG barriers" in item for item in result["errors"]))

    def test_lease_enforces_owner(self) -> None:
        lease_path = self.root / "leases" / "repo.json"
        acquired = sb.acquire_lease(lease_path, "worker-a", "repo", 60)
        self.assertEqual("acquired", acquired["status"])
        with self.assertRaises(sb.BaselineError):
            sb.acquire_lease(lease_path, "worker-b", "repo", 60)
        with self.assertRaises(sb.BaselineError):
            sb.release_lease(lease_path, "worker-b")
        released = sb.release_lease(lease_path, "worker-a")
        self.assertEqual("released", released["status"])

    def test_lease_restricts_path_and_rejects_untrusted_document(self) -> None:
        with self.assertRaises(sb.BaselineError):
            sb.acquire_lease(self.root / "arbitrary.json", "worker-a", "repo", 60)
        lease_path = self.root / "leases" / "malformed.json"
        lease_path.parent.mkdir()
        lease_path.write_text('{"owner":"worker-a"}', encoding="utf-8")
        with self.assertRaises(sb.BaselineError):
            sb.release_lease(lease_path, "worker-a")
        self.assertTrue(lease_path.exists())

    def test_record_step_is_idempotent_and_rejects_key_reuse(self) -> None:
        output = self.root / ".solution-baseline"
        init = sb.initialize_artifacts("demo", "Demo", "resources/architecture", output)
        manifest_path = Path(init["run_manifest"])
        input_hash = hashlib.sha256(b"input").hexdigest()
        result = {
            "operation": "inspect",
            "status": "succeeded",
            "repository_id": "web",
            "idempotency_key": "web-inspect-1",
            "input_hash": input_hash,
            "artifacts": [],
            "decisions": [],
            "warnings": [],
            "evidence": [],
            "next_steps": ["plan"],
            "agent_context": {"mode": "reconcile"},
        }
        result_path = self.root / "result.yaml"
        sb.dump_yaml_atomic(result_path, result)
        self.assertEqual("recorded", sb.record_step(manifest_path, result_path, None)["status"])
        self.assertEqual("unchanged", sb.record_step(manifest_path, result_path, None)["status"])

        result["input_hash"] = hashlib.sha256(b"different").hexdigest()
        sb.dump_yaml_atomic(result_path, result)
        with self.assertRaises(sb.BaselineError):
            sb.record_step(manifest_path, result_path, None)

    def test_scope_audit_blocks_vulcano_owned_paths(self) -> None:
        clean = sb.audit_scope(["src/app.ts", "resources/design/api.md"])
        self.assertTrue(clean["valid"])
        blocked = sb.audit_scope(["src/app.ts", "infra/main.tf", ".github/workflows/ci.yml"])
        self.assertFalse(blocked["valid"])
        self.assertEqual(2, len(blocked["violations"]))

    def test_scope_audit_blocks_nested_case_insensitive_and_absolute_paths(self) -> None:
        blocked = sb.audit_scope(
            [
                "apps/api/.github/workflows/ci.yml",
                "apps/api/Dockerfile",
                "services/api/AZURE-PIPELINES.yml",
                "D:\\work\\repo\\nested\\infra\\main.bicep",
            ]
        )
        self.assertFalse(blocked["valid"])
        self.assertEqual(4, len(blocked["violations"]))

    def test_scope_audit_covers_extended_delivery_and_iac_paths(self) -> None:
        blocked = sb.audit_scope(
            [
                "infra/main.bicep",
                ".circleci/config.yml",
                "Containerfile",
                "platform/Pulumi.yaml",
                "bitbucket-pipelines.yml",
                "../../outside.txt",
            ]
        )
        self.assertFalse(blocked["valid"])
        self.assertEqual(6, len(blocked["violations"]))

    def test_routing_evaluation_uses_observed_results(self) -> None:
        evaluation_path = sb.SKILL_ROOT / "assets" / "evaluations" / "skill-routing.yaml"
        evaluation = sb.load_document(evaluation_path)
        observations = {
            "schema_version": 1,
            "skill": "solution-baseline",
            "observations": [
                {
                    "id": case["id"],
                    "routed": case["should_route"],
                    "modes": case.get("expected_modes", []) if case["should_route"] else [],
                    "evidence": "Recorded by external forward-test harness",
                }
                for case in evaluation["cases"]
            ],
        }
        observations_path = self.root / "routing-observations.yaml"
        sb.dump_yaml_atomic(observations_path, observations)
        result = sb.evaluate_routing(evaluation_path, observations_path)
        self.assertTrue(result["valid"], result["failures"])

        observations["observations"][0]["routed"] = not observations["observations"][0]["routed"]
        sb.dump_yaml_atomic(observations_path, observations)
        result = sb.evaluate_routing(evaluation_path, observations_path)
        self.assertFalse(result["valid"])
        self.assertEqual(1, len(result["failures"]))

    def test_completed_run_cannot_contain_open_architecture_gap(self) -> None:
        manifest = sb.load_document(
            sb.SKILL_ROOT / "assets" / "templates" / "run-manifest.template.yaml"
        )
        manifest["status"] = "completed"
        manifest["blueprint"]["sha256"] = "a" * 64
        manifest["architecture_gaps"] = [
            sb.load_document(
                sb.SKILL_ROOT / "assets" / "templates" / "architecture-gap.template.yaml"
            )
        ]
        path = self.root / "run.yaml"
        sb.dump_yaml_atomic(path, manifest)
        result = sb.validate("run", path, strict=True)
        self.assertFalse(result["valid"])
        self.assertTrue(any("open architecture gaps" in item for item in result["errors"]))

    def test_genesis_migration_has_greenfield_contract_equivalence(self) -> None:
        result = sb.verify_genesis_migration(genesis_root=self.create_genesis_alias())
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual("contractual", result["equivalence_level"])
        self.assertEqual(
            {"web", "api", "worker", "agent"},
            {workload["id"] for workload in result["workloads"]},
        )
        self.assertTrue(all(workload["valid"] for workload in result["workloads"]))

    def test_genesis_is_not_retired_before_adoption_gate(self) -> None:
        result = sb.verify_genesis_migration(genesis_root=self.create_genesis_alias())
        self.assertFalse(result["retirement_ready"])
        self.assertFalse(result["retirement_gate"]["archetypes_published"])
        self.assertGreaterEqual(result["retirement_gate"]["required_successful_projects"], 2)

    def test_skill_commands_do_not_depend_on_project_claude_path(self) -> None:
        offenders = []
        for path in sb.SKILL_ROOT.rglob("*.md"):
            if "python .claude/skills/solution-baseline" in path.read_text(encoding="utf-8"):
                offenders.append(path.relative_to(sb.SKILL_ROOT).as_posix())
        self.assertEqual([], offenders)

    def test_agent_installation_is_portable_and_detects_drift(self) -> None:
        distribution = self.root / "distribution"
        skill_root = distribution / "skills" / "solution-baseline"
        claude_sources = distribution / "agents"
        codex_sources = distribution / "assets" / "agent-adapters" / "codex"
        claude_sources.mkdir(parents=True)
        codex_sources.mkdir(parents=True)
        skill_root.mkdir(parents=True)
        for name in sb.AGENT_NAMES:
            shutil.copy2(
                sb.agent_source_directory("claude") / f"{name}.agent.md",
                claude_sources / f"{name}.agent.md",
            )
            shutil.copy2(
                sb.agent_source_directory("codex") / f"{name}.toml",
                codex_sources / f"{name}.toml",
            )
        project = self.root / "consumer"
        project.mkdir()
        result = sb.install_agents(
            project,
            ["codex", "claude"],
            skill_root=skill_root,
            configure_runtime=True,
        )
        self.assertTrue(result["valid"])
        self.assertEqual(10, len(result["installed"]))
        record_path = project / ".solution-baseline" / "agent-installation.json"
        self.assertTrue(record_path.is_file())
        self.assertTrue(sb.validate("agent-installation", record_path)["valid"])
        record = sb.load_document(record_path)
        self.assertTrue(all(not Path(item["path"]).is_absolute() for item in record["files"]))
        self.assertFalse(Path(record["runtime"]["path"]).is_absolute())
        runtime = sb.codex_concurrency_status(project)
        self.assertTrue(runtime["valid"])

        modified = project / ".codex" / "agents" / "architecture-mapper.toml"
        modified.write_text(modified.read_text(encoding="utf-8") + "\n# local edit\n", encoding="utf-8")
        check = sb.check_agents(project, ["codex"], skill_root=skill_root)
        self.assertFalse(check["valid"])
        with self.assertRaises(sb.BaselineError):
            sb.install_agents(project, ["codex"], skill_root=skill_root)

    def test_codex_concurrency_configuration_preserves_existing_content(self) -> None:
        config = self.root / ".codex" / "config.toml"
        config.parent.mkdir()
        config.write_text("[features]\nexample = true\n", encoding="utf-8")
        result = sb.configure_codex_concurrency(self.root)
        self.assertTrue(result["valid"])
        content = config.read_text(encoding="utf-8")
        self.assertIn("[features]", content)
        self.assertIn("max_concurrent_threads_per_session = 4", content)

        config.write_text(
            "[other]\nmax_concurrent_threads_per_session = 9\n", encoding="utf-8"
        )
        isolated = sb.configure_codex_concurrency(self.root)
        self.assertTrue(isolated["valid"])
        isolated_content = config.read_text(encoding="utf-8")
        self.assertIn("[other]\nmax_concurrent_threads_per_session = 9", isolated_content)
        self.assertIn("[agents]\nenabled = true\nmax_concurrent_threads_per_session = 4", isolated_content)

        config.write_text(
            "[agents]\nmax_concurrent_threads_per_session = 8\n", encoding="utf-8"
        )
        with self.assertRaises(sb.BaselineError):
            sb.configure_codex_concurrency(self.root)
        forced = sb.configure_codex_concurrency(self.root, force=True)
        self.assertTrue(forced["valid"])

    def test_workspace_verification_requires_linked_worktree(self) -> None:
        main = self.root / "main"
        worktree = self.root / "worktree"
        main.mkdir()
        subprocess.run(["git", "init", str(main)], check=True, capture_output=True)
        (main / "README.md").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(main), "add", "README.md"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(main),
                "-c",
                "user.name=Solution Baseline Test",
                "-c",
                "user.email=solution-baseline@example.invalid",
                "commit",
                "-m",
                "initial",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(main), "worktree", "add", "--detach", str(worktree)],
            check=True,
            capture_output=True,
        )
        self.assertTrue(sb.verify_workspace_isolation(worktree, main)["valid"])
        self.assertFalse(sb.verify_workspace_isolation(main, main)["valid"])

    def test_concurrency_policy_blocks_writer_collisions_and_over_capacity(self) -> None:
        assignments = {
            "schema_version": 1,
            "assignments": [
                {
                    "agent_id": "worker-a",
                    "role": "repository-baseline-worker",
                    "access": "write",
                    "scope": "repository",
                    "resource": "apps/web",
                    "workspace": "../worktrees/web-a",
                    "status": "running",
                },
                {
                    "agent_id": "validator-a",
                    "role": "baseline-validator",
                    "access": "write",
                    "scope": "repository",
                    "resource": "apps/web",
                    "workspace": "../worktrees/web-b",
                    "status": "scheduled",
                },
            ],
        }
        path = self.root / "assignments.yaml"
        sb.dump_yaml_atomic(path, assignments)
        result = sb.check_concurrency(path)
        self.assertFalse(result["valid"])
        self.assertIn(
            "max-writers-per-repository",
            {violation["code"] for violation in result["violations"]},
        )

        assignments["assignments"] = [
            {
                "agent_id": f"mapper-{index}",
                "role": "architecture-mapper",
                "access": "read",
                "scope": "repository",
                "resource": f"repo-{index}",
                "status": "running",
            }
            for index in range(5)
        ]
        sb.dump_yaml_atomic(path, assignments)
        result = sb.check_concurrency(path)
        codes = {violation["code"] for violation in result["violations"]}
        self.assertIn("max-parallel-agents", codes)
        self.assertIn("max-parallel-readers", codes)

    def write_design_blueprint(self, design: dict | None) -> Path:
        component = {
            "id": "web",
            "requirement": "ARQ-001",
            "workload": "web",
            "repository": {"id": "web", "path": "apps/web"},
            "strategy": "create",
            "stack": {"language": "typescript", "runtime": {"intent": "stable"}},
        }
        if design is not None:
            component["design_system"] = design
        path = self.root / "blueprint.yaml"
        sb.dump_yaml_atomic(
            path,
            {
                "schema_version": 1,
                "solution": {"id": "demo", "name": "Demo"},
                "sources": [{"path": "design", "kind": "design-system", "status": "confirmed"}],
                "components": [component],
            },
        )
        return path

    def test_design_conformance_requires_frozen_tokens_and_no_literals_outside_zones(self) -> None:
        tokens = self.root / "design" / "brand.tokens.json"
        tokens.parent.mkdir(parents=True)
        tokens.write_text('{"color": {}}\n', encoding="utf-8")
        digest = hashlib.sha256(tokens.read_bytes()).hexdigest()
        app = self.root / "apps" / "web"
        (app / "src" / "design-system").mkdir(parents=True)
        (app / "src" / "design-system" / "theme.ts").write_text(
            "export const brand = '#1b6ec2';\n", encoding="utf-8"
        )
        page = app / "src" / "Page.tsx"
        page.write_text(
            "const s = { color: '#c93333', fontSize: '13px' };\nconst anchor = '#main-content';\n",
            encoding="utf-8",
        )
        design = {
            "source": "design",
            "status": "confirmed",
            "tokens": [{"path": "design/brand.tokens.json", "sha256": digest}],
            "style_zones": ["src/design-system/*"],
        }
        blueprint = self.write_design_blueprint(design)
        result = sb.check_design_conformance(app, blueprint, "web", self.root)
        self.assertFalse(result["valid"])
        self.assertTrue(result["frozen"])
        self.assertEqual({"color_literals": 1, "px_font_sizes": 1}, result["counts"])
        self.assertEqual({"src/Page.tsx"}, {item["path"] for item in result["literal_violations"]})

        page.write_text("export const s = {};\n", encoding="utf-8")
        self.assertTrue(sb.check_design_conformance(app, blueprint, "web", self.root)["valid"])

        tokens.write_text('{"color": {"changed": true}}\n', encoding="utf-8")
        drifted = sb.check_design_conformance(app, blueprint, "web", self.root)
        self.assertFalse(drifted["valid"])
        self.assertEqual("mismatch", drifted["artifact_checks"][0]["status"])

    def test_design_conformance_ratchet_status_and_missing_declaration(self) -> None:
        tokens = self.root / "brand.tokens.json"
        tokens.write_text("{}\n", encoding="utf-8")
        digest = hashlib.sha256(tokens.read_bytes()).hexdigest()
        app = self.root / "apps" / "web"
        (app / "src").mkdir(parents=True)
        (app / "src" / "Legacy.tsx").write_text(
            "const a = '#ffffff';\nconst b = 'rgb(0, 0, 0)';\n", encoding="utf-8"
        )
        design = {
            "source": ".",
            "status": "confirmed",
            "tokens": [{"path": "brand.tokens.json", "sha256": digest}],
            "max_literal_violations": 2,
        }
        self.assertTrue(
            sb.check_design_conformance(app, self.write_design_blueprint(design), "web", self.root)["valid"]
        )
        design["max_literal_violations"] = 1
        self.assertFalse(
            sb.check_design_conformance(app, self.write_design_blueprint(design), "web", self.root)["valid"]
        )

        unfrozen = {"source": ".", "status": "inferred", "tokens": [{"path": "brand.tokens.json"}]}
        result = sb.check_design_conformance(app, self.write_design_blueprint(unfrozen), "web", self.root)
        self.assertFalse(result["valid"])
        self.assertFalse(result["frozen"])
        self.assertEqual("unfrozen", result["artifact_checks"][0]["status"])

        with self.assertRaises(sb.BaselineError):
            sb.check_design_conformance(app, self.write_design_blueprint(None), "web", self.root)


if __name__ == "__main__":
    unittest.main()
