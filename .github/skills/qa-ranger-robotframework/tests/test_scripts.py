"""Pruebas de los scripts de qa-ranger-robotframework (sin dependencias; dry run si robotframework está instalado).

Ejecutar: python -m unittest discover -s .claude/skills/qa-ranger-robotframework/tests -p "test_*.py"
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
PY = sys.executable
TIENE_RF = importlib.util.find_spec("robot") is not None

OUTPUT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<robot generator="Robot 7.5 (Python 3.12.3 on linux)" generated="2026-10-27T10:00:00.000000" rpa="false" schemaversion="5">
<suite id="s1" name="Tests">
<suite id="s1-s1" name="Aceptacion">
<test id="s1-s1-t1" name="TC-01 [critical] La tabla existe">
<tag>TC-01</tag>
<status status="PASS" start="2026-10-27T10:00:00.000000" elapsed="0.100"/>
</test>
<test id="s1-s1-t2" name="Valor de referencia">
<tag>TC-02</tag><tag>high</tag>
<status status="{estado}" start="2026-10-27T10:00:01.000000" elapsed="0.200">Wrong query result</status>
</test>
<test id="s1-s1-t3" name="Sin identidad">
<status status="PASS" start="2026-10-27T10:00:02.000000" elapsed="0.050"/>
</test>
</suite>
</suite>
</robot>
"""


def run(*args, cwd=None):
    return subprocess.run([PY, *map(str, args)], capture_output=True, text=True, cwd=cwd)


class LintTest(unittest.TestCase):
    def test_suite_mala_tiene_bloqueantes_y_reglas_esperadas(self):
        r = run(SCRIPTS / "lint_robot.py", SKILL / "evals/files/suite-mala", "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        reglas = {h["rule"] for h in json.loads(r.stdout)["hallazgos"]}
        for regla in ("R1", "R2", "R4", "R6", "R7", "R8", "R9", "R11", "R12", "R13", "R14", "R17",
                      "R19", "R21", "R24", "R25", "R26", "R28"):
            self.assertIn(regla, reglas)

    def test_resource_del_wiki_heredado(self):
        r = run(SCRIPTS / "lint_robot.py", SKILL / "evals/files/connection_database.resource", "--json")
        reglas = {h["rule"] for h in json.loads(r.stdout)["hallazgos"]}
        self.assertTrue({"R2", "R13", "R29", "R21"} <= reglas, reglas)

    def test_template_rows_no_exigen_asercion_en_el_test(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "t.robot").write_text(
                "*** Settings ***\nTest Template    Rechazar Monto\n\n*** Test Cases ***    MONTO\n"
                "TC-11 [high] Cero    0\n\n*** Keywords ***\nRechazar Monto\n    [Arguments]    ${m}\n"
                "    Should Be True    ${m} <= 0\n", encoding="utf-8")
            r = run(SCRIPTS / "lint_robot.py", d, "--json")
            self.assertEqual(r.returncode, 0, r.stdout)


class ScaffoldTest(unittest.TestCase):
    def test_todos_los_perfiles_generan_sin_placeholders_y_pasan_el_lint(self):
        with tempfile.TemporaryDirectory() as d:
            casos = [("api", []), ("web-browser", ["--ci", "ambos"]), ("web-selenium", []),
                     ("db", ["--motor", "sqlite"]), ("db", ["--motor", "oracle"]), ("db-release", ["--motor", "db2"])]
            for i, (perfil, extra) in enumerate(casos):
                nombre = f"p{i}-{perfil}"
                r = run(SCRIPTS / "scaffold.py", "--nombre", nombre, "--perfil", perfil, "--salida", d, *extra)
                self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
                raiz = Path(d, nombre)
                rutas = ["acceptance_test"] if perfil == "db-release" else ["tests", "resources"]
                lint = run(raiz / "tools/lint_robot.py", *[raiz / x for x in rutas], "--rf", "5" if perfil == "db-release" else "7")
                self.assertEqual(lint.returncode, 0, f"{perfil}: {lint.stdout}")
                self.assertTrue((raiz / "ejecutar.sh").stat().st_mode & 0o100)

    def test_db_release_rechaza_sqlite(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(SCRIPTS / "scaffold.py", "--nombre", "x", "--perfil", "db-release", "--motor", "sqlite", "--salida", d)
            self.assertNotEqual(r.returncode, 0)

    @unittest.skipUnless(TIENE_RF, "robotframework no instalado")
    def test_dry_run_de_perfiles_sin_navegador(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, DB_NAME=str(Path(d, "x.db")), QA_API_TOKEN="t")
            for perfil, extra in (("api", []), ("db", ["--motor", "sqlite"])):
                run(SCRIPTS / "scaffold.py", "--nombre", perfil, "--perfil", perfil, "--salida", d, *extra)
                r = subprocess.run([PY, "-m", "robot", "--dryrun", "--output", "NONE", "--report", "NONE", "--log", "NONE",
                                    "--variablefile", "variables/qa.py", "tests"], cwd=Path(d, perfil),
                                   capture_output=True, text=True, env=env)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class CtrfTest(unittest.TestCase):
    def test_identidad_reintentos_y_adjuntos_reales(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "resources/qa/test-results/run-1"
            out.mkdir(parents=True)
            (out / "output.xml").write_text(OUTPUT_XML.replace("{estado}", "FAIL"), encoding="utf-8")
            (out / "rerun1.xml").write_text(OUTPUT_XML.replace("{estado}", "PASS"), encoding="utf-8")
            for intento in ("attempt-0", "attempt-1"):
                carpeta = out / "TC-02" / intento
                carpeta.mkdir(parents=True)
                (carpeta / "screenshot.png").write_bytes(b"png")
                (carpeta / "trace.zip").write_bytes(b"zip")
            r = run(SCRIPTS / "ctrf_from_robot.py", "--output", out / "output.xml", "--output", out / "rerun1.xml",
                    "--out", root / "ctrf.json", "--evidencia", out, "--proyecto", "chromium", "--project-root", root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Sin identidad", r.stderr)
            ctrf = json.loads((root / "ctrf.json").read_text(encoding="utf-8"))
            tests = {t["name"]: t for t in ctrf["results"]["tests"]}
            self.assertIn("TC-01 [critical] La tabla existe", tests)
            tc2 = tests["TC-02 [high] Valor de referencia"]
            self.assertEqual((tc2["status"], tc2["retries"], tc2["flaky"], tc2["browser"]), ("passed", 1, True, "chromium"))
            nombres = sorted(a["name"] for a in tc2["attachments"])
            self.assertEqual(nombres, ["attempt-0/screenshot", "attempt-0/trace", "screenshot", "trace"])
            self.assertTrue(all(not a["path"].startswith("/") for a in tc2["attachments"]))
            self.assertNotIn("attachments", tests["TC-01 [critical] La tabla existe"])
            self.assertEqual(ctrf["results"]["summary"]["tests"], 3)

    def test_rtm(self):
        with tempfile.TemporaryDirectory() as d:
            xml = Path(d, "output.xml")
            xml.write_text(OUTPUT_XML.replace("{estado}", "PASS").replace("La tabla existe", "[HU-1][CA-2] La tabla existe"), encoding="utf-8")
            r = run(SCRIPTS / "rtm_from_robot.py", xml)
            self.assertIn("| HU-1 | CA-2 | ✅ PASA |", r.stdout)
            self.assertIn("Sin trazabilidad: 2", r.stdout)


if __name__ == "__main__":
    unittest.main()
