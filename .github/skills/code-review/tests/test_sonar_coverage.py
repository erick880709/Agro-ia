"""Tests de sonar_detect.py y coverage_diff.py (solo biblioteca estándar)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import coverage_diff  # noqa: E402
import sonar_detect  # noqa: E402

DIFF = """diff --git a/src/main/java/co/bank/Fee.java b/src/main/java/co/bank/Fee.java
--- a/src/main/java/co/bank/Fee.java
+++ b/src/main/java/co/bank/Fee.java
@@ -1,3 +1,8 @@
 class Fee {
+  long apply(long v) {
+    if (v < 0) {
+      throw new IllegalArgumentException();
+    }
+    return v * 2;
+  }
 }
diff --git a/src/test/java/co/bank/FeeTest.java b/src/test/java/co/bank/FeeTest.java
--- /dev/null
+++ b/src/test/java/co/bank/FeeTest.java
@@ -0,0 +1,2 @@
+class FeeTest {
+}
diff --git a/src/main/java/co/bank/Nuevo.java b/src/main/java/co/bank/Nuevo.java
--- /dev/null
+++ b/src/main/java/co/bank/Nuevo.java
@@ -0,0 +1,2 @@
+class Nuevo {
+}
"""

JACOCO = """<?xml version="1.0"?><report name="t"><package name="co/bank"><sourcefile name="Fee.java">
<line nr="2" mi="0" ci="2" mb="0" cb="0"/>
<line nr="3" mi="0" ci="3" mb="1" cb="1"/>
<line nr="4" mi="4" ci="0" mb="0" cb="0"/>
<line nr="6" mi="0" ci="3" mb="0" cb="0"/>
</sourcefile></package></report>"""


class CoverageDiffTest(unittest.TestCase):
    def test_added_lines(self):
        files = coverage_diff.added_lines(DIFF)
        self.assertEqual(files["src/main/java/co/bank/Fee.java"], {2, 3, 4, 5, 6, 7})

    def test_jacoco_new_code(self):
        r = coverage_diff.compute(DIFF, coverage_diff.parse_jacoco(JACOCO), 80)
        fee = r["archivos"][0]
        self.assertEqual((fee["ejecutables"], fee["cubiertas"], fee["sinCubrir"]), (4, 3, [4]))
        self.assertEqual(fee["ramasParciales"], [3])
        self.assertEqual(r["cobertura"], 66.7)          # (3 líneas + 1 rama) / (4 + 2)
        self.assertFalse(r["cumple"])
        self.assertEqual(r["sinDatos"], ["src/main/java/co/bank/Nuevo.java"])  # tests excluidos, archivo sin datos listado

    def test_lcov_and_threshold_exit_code(self):
        lcov = "SF:/ci/work/src/main/java/co/bank/Fee.java\nDA:2,1\nDA:3,1\nDA:4,1\nDA:6,1\nend_of_record\n"
        with tempfile.TemporaryDirectory() as d:
            Path(d, "c.diff").write_text(DIFF, encoding="utf-8")
            Path(d, "lcov.info").write_text(lcov, encoding="utf-8")
            self.assertEqual(coverage_diff.main(["--diff-file", str(Path(d, "c.diff")), "--lcov", str(Path(d, "lcov.info")), "--threshold", "80"]), 0)
            Path(d, "lcov.info").write_text(lcov.replace("DA:4,1", "DA:4,0"), encoding="utf-8")
            self.assertEqual(coverage_diff.main(["--diff-file", str(Path(d, "c.diff")), "--lcov", str(Path(d, "lcov.info")), "--threshold", "80"]), 1)

    def test_go_profile(self):
        diff = "+++ b/pkg/fee/fee.go\n@@ -1,1 +1,3 @@\n package fee\n+func A() int { return 1 }\n+func B() int { return 2 }\n"
        prof = "mode: set\nexample.com/m/pkg/fee/fee.go:2.15,2.25 1 1\nexample.com/m/pkg/fee/fee.go:3.15,3.25 1 0\n"
        r = coverage_diff.compute(diff, coverage_diff.parse_go(prof), None)
        self.assertEqual(r["archivos"][0]["sinCubrir"], [3])
        self.assertEqual(r["cobertura"], 50.0)

    def test_invalid_input(self):
        self.assertEqual(coverage_diff.main(["--diff-file", "/no/existe.diff", "--lcov", "/no/existe"]), 2)
        with tempfile.TemporaryDirectory() as d:
            Path(d, "c.diff").write_text(DIFF, encoding="utf-8")
            self.assertEqual(coverage_diff.main(["--diff-file", str(Path(d, "c.diff"))]), 2)


class SonarDetectTest(unittest.TestCase):
    def test_scaffold_like_project(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "build.gradle").write_text(
                "plugins { id 'org.sonarqube' version '6.2.0.5505' }\nsonar {\n properties {\n"
                "  property \"sonar.projectKey\", \"nu0001_cuentas\"\n"
                "  property \"sonar.coverage.jacoco.xmlReportPaths\", \"build/reports/jacoco.xml\"\n }\n}\n"
                "jacocoTestCoverageVerification { violationRules { rule { limit { minimum = 0.85 } } } }\n", encoding="utf-8")
            (root / "azure-pipelines.yml").write_text("steps:\n- task: SonarQubePrepare@7\n", encoding="utf-8")
            r = sonar_detect.detect(root)
            self.assertTrue(r["detected"])
            self.assertFalse(r["mcpConfigured"])
            self.assertEqual(r["projectKey"], "nu0001_cuentas")
            self.assertEqual(r["localThresholds"][0]["minimum"], 85.0)
            self.assertIn("azure-pipelines", {s["kind"] for s in r["signals"]})

    def test_properties_and_mcp(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "sonar-project.properties").write_text("sonar.projectKey=web\nsonar.organization=acme\n", encoding="utf-8")
            (root / ".mcp.json").write_text(json.dumps({"mcpServers": {"sonarqube": {"args": ["sonarsource/sonarqube-mcp"]}}}), encoding="utf-8")
            r = sonar_detect.detect(root)
            self.assertEqual((r["projectKey"], r["organization"], r["mcpConfigured"]), ("web", "acme", True))

    def test_no_sonar(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "package.json").write_text('{"name": "x"}', encoding="utf-8")
            r = sonar_detect.detect(Path(d))
            self.assertFalse(r["detected"])
            self.assertEqual(sonar_detect.main([str(Path(d, "no-existe"))]), 2)


if __name__ == "__main__":
    unittest.main()
