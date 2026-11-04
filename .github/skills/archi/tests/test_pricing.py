"""Behavioral checks with synthetic prices; no provider calls or real budgets."""
import copy
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import validate_pricing as pricing


class PricingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.deployment = self.root / "17-Vista-de-Despliegue.md"
        self.deployment.write_text(
            "## Inventario de costos por ambiente\n\n"
            "| Ambiente | Proveedor | Recurso | Tratamiento | Justificación |\n"
            "|---|---|---|---|---|\n"
            "| dev | test | RES-shared | costed | shared fixture |\n"
            "| prod | test | RES-shared | costed | shared fixture |\n", encoding="utf-8")
        self.path = self.root / "17.4.1-Costos_Test.json"
        self.md = self.root / "17.4-Pricing_Test.md"
        self.html = self.root / "17.5-Arquitectura_Costos_Test.html"
        self.md.write_text("# Preserve narrative\n" + pricing.START + "\n" + pricing.END, encoding="utf-8")
        self.html.write_text("<!doctype html><main>" + pricing.START + "\n" + pricing.END + "</main>", encoding="utf-8")
        self.data = {
            "version": 1, "as_of": date.today().isoformat(), "currency": "USD",
            "max_price_age_days": 30, "freshness_reason": "Test only",
            "deployment": self.deployment.name, "pricing_report": self.md.name,
            "html_report": self.html.name, "environments": ["dev", "prod"],
            "items": [{"id": "COST-001", "provider": "test", "resource": "RES-shared",
                       "region": "test", "sku": "test", "meter": "input", "category": "ai",
                       "unit": "tokens", "unit_size": 1000000, "unit_price": "2",
                       "cadence": "monthly", "quantity": {"low": 1000000, "expected": 2000000, "high": 3000000},
                       "allocations": {"dev": "0.25", "prod": "0.75"}, "assumption": "synthetic fixture",
                       "evidence": {"kind": "public", "ref": "https://example.test/pricing",
                                    "checked_on": date.today().isoformat()}}]}

    def save(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")

    def test_shared_costs_and_one_time_are_not_double_counted(self):
        once = copy.deepcopy(self.data["items"][0])
        once.update(id="COST-002", cadence="one_time")
        self.data["items"].append(once)
        totals = pricing.calculate(self.data, self.root)
        self.assertEqual(totals[("test", "dev", "monthly", "expected")], Decimal("1"))
        self.assertEqual(totals[("test", "prod", "monthly", "expected")], Decimal("3"))
        self.assertEqual(sum(v for k, v in totals.items() if k[2:] == ("one_time", "expected")), Decimal("4"))

    def test_inventory_missing_environment_or_resource_fails(self):
        with self.deployment.open("a", encoding="utf-8") as stream:
            stream.write("| staging | test | RES-other | costed | missing cost |\n")
        with self.assertRaisesRegex(ValueError, "environments differ"):
            pricing.calculate(self.data, self.root)
        self.data["environments"].append("staging")
        with self.assertRaisesRegex(ValueError, "unpriced"):
            pricing.calculate(self.data, self.root)

    def test_duplicate_meter_and_item_id_fail(self):
        self.data["items"].append(copy.deepcopy(self.data["items"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate item"):
            pricing.calculate(self.data, self.root)
        self.data["items"][1]["id"] = "COST-002"
        with self.assertRaisesRegex(ValueError, "duplicate billing"):
            pricing.calculate(self.data, self.root)

    def test_exclusion_cannot_silently_keep_a_charge(self):
        self.deployment.write_text(self.deployment.read_text().replace("costed", "excluded"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "absent/excluded"):
            pricing.calculate(self.data, self.root)

    def test_bad_quantities_and_allocations_fail(self):
        original = copy.deepcopy(self.data)
        for value in (-1, "NaN", "Infinity", True):
            with self.subTest(value=value):
                self.data = copy.deepcopy(original)
                self.data["items"][0]["quantity"]["low"] = value
                with self.assertRaises(ValueError):
                    pricing.calculate(self.data, self.root)
        self.data = original
        self.data["items"][0]["allocations"]["dev"] = "0.5"
        with self.assertRaisesRegex(ValueError, "sum to 1"):
            pricing.calculate(self.data, self.root)

    def test_evidence_freshness_and_approximation_reason(self):
        evidence = self.data["items"][0]["evidence"]
        for days in (-40, 1):
            evidence["checked_on"] = (date.today() + timedelta(days=days)).isoformat()
            with self.assertRaisesRegex(ValueError, "stale or future"):
                pricing.calculate(self.data, self.root)
        evidence["checked_on"] = date.today().isoformat()
        evidence["kind"] = "approximation"
        with self.assertRaisesRegex(ValueError, "reason"):
            pricing.calculate(self.data, self.root)

    def test_observed_requires_local_evidence_and_period(self):
        evidence = self.data["items"][0]["evidence"]
        evidence.update(kind="observed", ref="17.4.2-Evidencia.md")
        with self.assertRaisesRegex(ValueError, "missing"):
            pricing.calculate(self.data, self.root)
        (self.root / evidence["ref"]).write_text("Redacted billing summary", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "period"):
            pricing.calculate(self.data, self.root)
        evidence["period"] = "Test month"
        pricing.calculate(self.data, self.root)

    def test_sync_is_idempotent_and_tampering_detected(self):
        self.save()
        pricing.check_manifest(self.path, sync=True)
        before = self.md.read_bytes(), self.html.read_bytes()
        pricing.check_manifest(self.path)
        pricing.check_manifest(self.path, sync=True)
        self.assertEqual(before, (self.md.read_bytes(), self.html.read_bytes()))
        self.assertIn("Preserve narrative", self.md.read_text())
        self.html.write_text(self.html.read_text(encoding="utf-8").replace("3.00", "9.00"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs"):
            pricing.check_manifest(self.path)

    def test_sync_validates_all_reports_before_writing(self):
        self.save()
        before = self.md.read_bytes()
        self.html.write_text("missing delimiters", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "delimiters"):
            pricing.check_manifest(self.path, sync=True)
        self.assertEqual(before, self.md.read_bytes())

    def test_path_escape_rejected(self):
        self.data["deployment"] = "../outside.md"
        with self.assertRaisesRegex(ValueError, "out-of-scope"):
            pricing.calculate(self.data, self.root)

    def test_old_pricing_requires_manifest_and_cli_failure_is_clear(self):
        self.assertTrue(any("missing structured" in e for e in pricing.validate_directory(self.root)))
        self.path.write_text("{}", encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPTS / "validate_pricing.py"), str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_coherence_integrates_cost_errors(self):
        import validate_architecture_coherence as coherence
        report = coherence.validate_directory(self.root, "B", False)
        self.assertTrue(any("missing structured" in e for e in report.errors))

    def test_multiple_providers_stay_separate_and_require_html(self):
        other = copy.deepcopy(self.data["items"][0])
        other.update(id="COST-002", provider="other", unit_price="20")
        self.data["items"].append(other)
        with self.deployment.open("a", encoding="utf-8") as stream:
            stream.write("| dev | other | RES-shared | costed | alternative |\n| prod | other | RES-shared | costed | alternative |\n")
        self.save()
        pricing.check_manifest(self.path, sync=True)
        text = self.md.read_text(encoding="utf-8")
        self.assertIn("| test | TOTAL | monthly | 2.00 | 4.00 | 6.00 |", text)
        self.assertIn("| other | TOTAL | monthly | 20.00 | 40.00 | 60.00 |", text)
        del self.data["html_report"]
        self.save()
        with self.assertRaisesRegex(ValueError, "needs html_report"):
            pricing.check_manifest(self.path)

    def test_json_precision_and_duplicate_keys(self):
        loaded = pricing.load_manifest(b'{"rate": 0.1234567890123456789}')
        self.assertEqual(loaded["rate"], Decimal("0.1234567890123456789"))
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            pricing.load_manifest(b'{"unit_price": 1, "unit_price": 100}')

    def test_all_excluded_is_explicit_not_a_silent_zero(self):
        self.deployment.write_text(self.deployment.read_text().replace("costed", "excluded"), encoding="utf-8")
        self.data["items"] = []
        self.save()
        pricing.check_manifest(self.path, sync=True)
        self.assertIn("Sin partidas", self.md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
