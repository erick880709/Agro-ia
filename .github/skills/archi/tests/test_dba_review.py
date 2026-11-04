"""Pruebas de la integración de la revisión experta de datos (`dba`) en el validador."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_architecture_coherence as v  # noqa: E402


def run(files: dict[str, str]) -> v.Report:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        docs = {}
        for name, text in files.items():
            (root / name).write_text(text, encoding="utf-8")
            if name.endswith(".md"):
                docs[root / name] = text
        report = v.Report()
        v.validate_expert_data_review(root, docs, report)
        return report


def obs(**kw) -> str:
    f = {"id": "DB-001", "severity": "bloqueante", "status": "abierto"}
    f.update(kw)
    return json.dumps({"schema": "dba-findings/1", "findings": [f], "verdict": "cambios-requeridos"})


class ExpertDataReviewTests(unittest.TestCase):
    def test_pending_blocker_fails(self):
        r = run({"16.00.1-Observaciones-Datos_X.json": obs(disposition="pendiente")})
        self.assertTrue(any("sin disposición" in e for e in r.errors))

    def test_deferred_major_fails(self):
        r = run({"16.00.1-Observaciones-Datos_X.json": obs(severity="mayor", disposition="diferida")})
        self.assertTrue(r.errors)

    def test_incorporated_cited_passes(self):
        r = run({"16.00.1-Observaciones-Datos_X.json": obs(disposition="incorporada"),
                 "16.01-Modelo-de-Datos_CT-01_API.md": "monto numeric(18,2) (DB-001)",
                 "16.00-Revision-Experta-Datos_X.md": "# rev"})
        self.assertEqual(r.errors, [])
        self.assertEqual(r.warnings, [])

    def test_risk_requires_note_and_21(self):
        r = run({"16.00.1-Observaciones-Datos_X.json": obs(disposition="riesgo-aceptado")})
        self.assertTrue(any("disposition_note" in e for e in r.errors))
        self.assertTrue(any("21-" in w for w in r.warnings))

    def test_models_without_review_warn_unless_declared(self):
        r = run({"16.01-Modelo-de-Datos_CT-01_API.md": "x", "16-Modelo-de-Datos.md": "# Datos"})
        self.assertTrue(r.warnings)
        r2 = run({"16.01-Modelo-de-Datos_CT-01_API.md": "x",
                  "16-Modelo-de-Datos.md": "Revisión experta de datos: No disponible — sin skill"})
        self.assertEqual(r2.warnings, [])


if __name__ == "__main__":
    unittest.main()
