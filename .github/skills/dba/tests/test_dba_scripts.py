"""Pruebas deterministas de los scripts de la skill dba (solo biblioteca estándar)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import db_triage  # noqa: E402
import migration_lint  # noqa: E402
import validate_findings  # noqa: E402

PWD = "S3cr" + "etoProd99"


def w(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def rules_of(path: Path, engine="auto") -> set[str]:
    _, fs = migration_lint.lint_file(path, engine, path.name)
    return {f["rule"] for f in fs}


class MigrationLintTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.r = Path(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def test_postgres_risky(self):
        p = w(self.r, "V2__x.sql", """
            CREATE INDEX ix_mov_cuenta ON movimientos (cuenta_id);
            ALTER TABLE movimientos ALTER COLUMN monto TYPE numeric(18,2);
            ALTER TABLE cuenta ADD COLUMN estado text NOT NULL;
            ALTER TABLE cuenta ADD CONSTRAINT fk_cli FOREIGN KEY (cliente_id) REFERENCES cliente(id);
            ALTER TABLE cuenta RENAME COLUMN nombre TO alias;
            ALTER TABLE cuenta ALTER COLUMN alias SET NOT NULL;
            DELETE FROM auditoria;
            CREATE TABLE pago (id bigint PRIMARY KEY, monto float, creado timestamp);
        """)
        got = rules_of(p, "postgresql")
        for r in ["MIG-PG-001", "MIG-PG-003", "MIG-PG-006", "MIG-PG-005", "MIG-ALL-005", "MIG-PG-004",
                  "MIG-ALL-004", "MIG-ALL-006", "MIG-PG-009", "MIG-PG-010", "MIG-ALL-007"]:
            self.assertIn(r, got, r)

    def test_postgres_safe(self):
        p = w(self.r, "V3__ok.sql", """
            SET lock_timeout = '5s';
            ALTER TABLE cuenta ADD COLUMN canal text;
            ALTER TABLE cuenta ADD CONSTRAINT fk_cli FOREIGN KEY (cliente_id) REFERENCES cliente(id) NOT VALID;
            ALTER TABLE cuenta ALTER COLUMN estado DROP NOT NULL;
            CREATE TABLE pago (id bigint PRIMARY KEY, monto numeric(18,2) NOT NULL, creado timestamptz NOT NULL);
        """)
        self.assertEqual(rules_of(p, "postgresql"), set())

    def test_concurrently_alone_ok_but_mixed_flagged(self):
        a = w(self.r, "V4__idx.sql", "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix ON t (c);")
        self.assertEqual(rules_of(a, "postgresql") - {"MIG-PG-010"}, set())
        b = w(self.r, "V5__mix.sql", "CREATE INDEX CONCURRENTLY ix ON t (c);\nALTER TABLE t ADD COLUMN d text;")
        self.assertIn("MIG-PG-011", rules_of(b, "postgresql"))

    def test_oracle(self):
        p = w(self.r, "V6__ora.sql", """
            CREATE INDEX ix_mov ON movimientos (cuenta_id);
            ALTER TABLE cuenta ADD (estado VARCHAR2(10) NOT NULL);
            ALTER TABLE cuenta MOVE TABLESPACE datos;
            ALTER TABLE cuenta ADD (canal VARCHAR2(10) DEFAULT 'WEB' NOT NULL);
        """)
        got = rules_of(p, "oracle")
        self.assertTrue({"MIG-ORA-001", "MIG-ORA-004", "MIG-ORA-003"} <= got, got)

    def test_sqlserver_and_mysql(self):
        s = w(self.r, "V7__mss.sql", "CREATE NONCLUSTERED INDEX ix ON dbo.t (c)\nGO\nALTER TABLE dbo.t ALTER COLUMN c BIGINT\nGO\n")
        self.assertTrue({"MIG-MSS-001", "MIG-MSS-002"} <= rules_of(s, "sqlserver"))
        m = w(self.r, "V8__my.sql", "ALTER TABLE t ADD COLUMN c INT;\nALTER TABLE t ADD COLUMN d INT, ALGORITHM=INSTANT;")
        fs = migration_lint.lint_file(m, "mysql", "V8")[1]
        self.assertEqual([f["line"] for f in fs if f["rule"] == "MIG-MY-001"], [1])

    def test_engine_detection(self):
        self.assertEqual(migration_lint.detect_engine("create table t (a jsonb)", Path("x.sql")), "postgresql")
        self.assertEqual(migration_lint.detect_engine("create table t (a varchar2(10))", Path("x.sql")), "oracle")
        self.assertEqual(migration_lint.detect_engine("create table t (a nvarchar(10))", Path("x.sql")), "sqlserver")

    @unittest.skipUnless(shutil.which("git"), "git requerido")
    def test_modified_applied_migration(self):
        g = lambda *a: subprocess.run(["git", "-C", str(self.r), *a], check=True, capture_output=True)
        g("init", "-q", "-b", "main")
        g("config", "user.email", "t@t"); g("config", "user.name", "t")
        w(self.r, "db/migration/V1__init.sql", "CREATE TABLE t (id bigint PRIMARY KEY);\n")
        g("add", "."); g("commit", "-qm", "init")
        g("checkout", "-qb", "feature")
        w(self.r, "db/migration/V1__init.sql", "CREATE TABLE t (id bigint PRIMARY KEY, x text);\n")
        g("commit", "-qam", "edit applied")
        out = migration_lint.modified_applied(self.r, "main", [])
        self.assertEqual([o["rule"] for o in out], ["MIG-ALL-008"])


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        r = self.r = Path(self.t.name)
        w(r, "build.gradle", "implementation 'org.postgresql:postgresql'\nimplementation 'org.flywaydb:flyway-core'\n"
                             "implementation 'software.amazon.awssdk:dynamodb-enhanced'\n")
        w(r, "src/main/resources/db/migration/V1__init.sql", "CREATE TABLE pago (id bigint, monto float);\n")
        w(r, "src/main/resources/application.yaml",
          f"spring:\n  datasource:\n    url: jdbc:postgresql://app:{PWD}@db:5432/x\n  jpa:\n    hibernate:\n      ddl-auto: update\n    open-in-view: true\n")
        w(r, "src/main/java/x/Repo.java", "class R { @OneToMany(fetch = FetchType.EAGER) List<M> m; void f(){ repo.findAll(); table.scan(); } }\n")
        w(r, "infra/rds.tf", 'resource "aws_db_instance" "x" {\n  engine = "postgres"\n  skip_final_snapshot = true\n  backup_retention_period = 0\n  multi_az = false\n}\n')
        self.out = r / "o.json"
        self.assertEqual(db_triage.main([str(r), "--json", str(self.out)]), 0)
        self.doc = json.loads(self.out.read_text(encoding="utf-8"))
        self.rules = {s["rule"] for s in self.doc["signals"]}

    def tearDown(self):
        self.t.cleanup()

    def test_engines_and_tools(self):
        self.assertIn("postgresql", self.doc["engines"])
        self.assertIn("dynamodb", self.doc["engines"])
        self.assertIn("flyway", self.doc["migration_tools"])
        self.assertEqual(self.doc["migrations"]["count"], 1)
        self.assertEqual(self.doc["tool_plan"][0]["tool"], "migration_lint")

    def test_signals(self):
        exp = {"jpa.ddl-auto", "jpa.open-in-view", "jpa.eager", "jpa.find-all", "dynamo.scan", "sql.money-float",
               "conn.password-in-url", "iac.skip-final-snapshot", "iac.backup-retention-zero", "iac.single-az"}
        self.assertTrue(exp <= self.rules, exp - self.rules)

    def test_password_masked(self):
        self.assertNotIn(PWD, self.out.read_text(encoding="utf-8"))


def doc() -> dict:
    return {"schema": "dba-findings/1", "engines": [{"engine": "postgresql", "version": "16"}],
            "findings": [{"id": "DB-001", "fingerprint": "migration:mov:index", "category": "migracion",
                          "severity": "bloqueante", "confidence": "media", "title": "x",
                          "location": {"file": "V1.sql", "line": 1}, "scenario": "80M", "evidence": "lint",
                          "remediation": "concurrently", "verification": "indisvalid", "status": "abierto"},
                         {"id": "DB-002", "fingerprint": "q:size", "category": "costo-capacidad", "severity": "pregunta",
                          "confidence": "media", "title": "tamaño", "location": {"file": "16.03.md", "line": 4},
                          "resolution_query": "SELECT count(*) ..."}],
            "verdict": "cambios-requeridos"}


class ValidatorTests(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(validate_findings.validate(doc()), [])

    def test_missing_fields(self):
        d = doc(); del d["findings"][0]["verification"]
        self.assertTrue(any("verification" in e for e in validate_findings.validate(d)))

    def test_low_confidence_blocker(self):
        d = doc(); d["findings"][0]["confidence"] = "baja"
        self.assertTrue(any("confianza baja" in e for e in validate_findings.validate(d)))

    def test_question_needs_query(self):
        d = doc(); del d["findings"][1]["resolution_query"]
        self.assertTrue(any("resolution_query" in e for e in validate_findings.validate(d)))

    def test_approved_with_open_blocker(self):
        d = doc(); d["verdict"] = "aprobado"
        self.assertTrue(any("incompatible" in e for e in validate_findings.validate(d)))

    def test_archi_disposition(self):
        d = doc()
        self.assertTrue(any("disposición" in e for e in validate_findings.validate(d, archi=True)))
        d["findings"][0]["disposition"] = "incorporada"
        self.assertEqual(validate_findings.validate(d, archi=True), [])
        d["findings"][0]["disposition"] = "riesgo-aceptado"
        self.assertTrue(any("disposition_note" in e for e in validate_findings.validate(d, archi=True)))
        d["findings"][0]["disposition"] = "diferida"
        self.assertTrue(any("diferida" in e for e in validate_findings.validate(d, archi=True)))

    def test_credentials(self):
        d = doc(); d["findings"][0]["evidence"] = f"jdbc:postgresql://app:{PWD}@db/x"
        self.assertTrue(any("credenciales" in e for e in validate_findings.validate(d)))

    def test_engines_required(self):
        d = doc(); d["engines"] = []
        self.assertTrue(any("engines" in e for e in validate_findings.validate(d)))


if __name__ == "__main__":
    unittest.main()


class LintPrecisionTests(unittest.TestCase):
    def test_index_on_table_created_in_same_file_is_ok(self):
        with tempfile.TemporaryDirectory() as d:
            p = w(Path(d), "V9__new.sql", "CREATE TABLE pago (id bigint PRIMARY KEY, cuenta_id bigint NOT NULL);\n"
                                           "CREATE INDEX ix_pago_cuenta ON pago (cuenta_id);\n")
            self.assertNotIn("MIG-PG-001", rules_of(p, "postgresql"))

    def test_content_beats_path(self):
        self.assertEqual(migration_lint.detect_engine("create table t (id uuid default uuid_generate_v4())",
                                                      Path("sqlserver-to-pg/target/t.sql")), "postgresql")
