"""Pruebas de las herramientas de diagramación de archi (Excalidraw, interactivo, vista previa)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_interactive_diagram as bid  # noqa: E402
import render_preview as rp  # noqa: E402
import validate_excalidraw as vex  # noqa: E402

EXAMPLE_EX = ROOT / "assets" / "ejemplo-argumento-outbox.excalidraw"
EXAMPLE_SPEC = ROOT / "assets" / "ejemplo-flujos-interactivos.json"


class ExcalidrawTests(unittest.TestCase):
    def test_example_passes_strict(self):
        errs, warns, _ = vex.validate(json.loads(EXAMPLE_EX.read_text(encoding="utf-8")))
        self.assertEqual((errs, warns), ([], []))

    def test_owner_cross_check(self):
        doc = json.loads(EXAMPLE_EX.read_text(encoding="utf-8"))
        errs, _, _ = vex.validate(doc, owner_text="solo CT-01")
        self.assertTrue(any("DATA-001" in e for e in errs))

    def test_label_too_long_warns(self):
        doc = json.loads(EXAMPLE_EX.read_text(encoding="utf-8"))
        for e in doc["elements"]:
            if e["id"] == "a1_t":
                e["text"] = e["originalText"] = "etiqueta demasiado larga para este tramo corto"
        _, warns, _ = vex.validate(doc)
        self.assertTrue(any("no cabe" in w for w in warns))

    def test_self_test(self):
        self.assertEqual(vex.self_test(), 0)


class InteractiveTests(unittest.TestCase):
    def test_example_spec_valid_and_builds(self):
        spec = json.loads(EXAMPLE_SPEC.read_text(encoding="utf-8"))
        errs, warns = bid.validate(spec)
        self.assertEqual((errs, warns), ([], []))
        html = bid.build(spec)
        self.assertNotIn(bid.PLACEHOLDER, html)
        self.assertIn("window.archValidate", html)

    def test_script_injection_escaped(self):
        spec = json.loads(EXAMPLE_SPEC.read_text(encoding="utf-8"))
        spec["flows"][0]["steps"][0]["payload"] = "</script><img src=x onerror=alert(1)>"
        self.assertNotIn("</script><img", bid.build(spec))

    def test_invalid_refs(self):
        spec = json.loads(EXAMPLE_SPEC.read_text(encoding="utf-8"))
        spec["flows"][0]["steps"][0]["to"] = "CT-99"
        spec["defaultMode"] = "PROD"
        errs, _ = bid.validate(spec)
        self.assertTrue(any("CT-99" in e for e in errs) and any("defaultMode" in e for e in errs))

    def test_markdown_table(self):
        md = bid.markdown(json.loads(EXAMPLE_SPEC.read_text(encoding="utf-8")))
        self.assertIn("| # | De → A |", md)

    def test_self_test(self):
        self.assertEqual(bid.self_test(), 0)


class PreviewTests(unittest.TestCase):
    def test_renders_example_and_reference(self):
        with tempfile.TemporaryDirectory() as d:
            r1 = rp.render(rp.load_scene(EXAMPLE_EX), Path(d) / "a.png")
            r2 = rp.render(rp.load_scene(ROOT / "assets" / "drawio" / "referencia-despliegue-azure.drawio"), Path(d) / "b.png")
            self.assertEqual(r1["issues"], [])
            self.assertGreater(r2["edges"], 5)
            self.assertTrue((Path(d) / "b.png").stat().st_size > 10_000)


if __name__ == "__main__":
    unittest.main()
