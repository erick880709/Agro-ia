#!/usr/bin/env python3
"""Linter de migraciones SQL para la skill dba.

Detecta DDL/DML riesgoso por motor (bloqueos, reescrituras, operaciones destructivas,
NOT NULL sin estrategia, índices sin modo en línea) y, con --base, migraciones ya
versionadas que fueron MODIFICADAS (nunca se edita una migración aplicada).

Los resultados son candidatos: la severidad final depende del volumen real y la versión.

Uso:
    python migration_lint.py <archivo|directorio>... [--engine auto|postgresql|oracle|sqlserver|mysql]
                             [--base origin/main] [--json salida.json]
Salida: 0 sin hallazgos ALTA, 1 con hallazgos ALTA, 2 error de uso.
Solo biblioteca estándar; no se conecta a ninguna base.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MIGRATION_HINT = re.compile(
    r"(^|/)(db/migration|migrations?|changelog|changelogs|liquibase|flyway|sql/migrations?|schema)(/|$)"
    r"|^V\d+(_\d+)*__.+\.sql$|^\d{3,}_.+\.(up|down)\.sql$|^\d+_.+\.sql$",
    re.IGNORECASE,
)


def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), sql, flags=re.S)
    return re.sub(r"--[^\n]*", "", sql)


def statements(sql: str) -> list[tuple[int, str]]:
    """Divide por ';' (y por GO/ '/' en línea propia) conservando la línea de inicio."""
    clean = strip_comments(sql)
    out, buf, start, line = [], [], None, 1
    for raw in clean.splitlines(keepends=True):
        if re.fullmatch(r"\s*(GO|/)\s*", raw, re.I):
            if buf and "".join(buf).strip():
                out.append((start, "".join(buf)))
            buf, start = [], None
            line += 1
            continue
        parts = raw.split(";")
        for i, part in enumerate(parts):
            if part.strip() and start is None:
                start = line
            buf.append(part)
            if i < len(parts) - 1:
                if "".join(buf).strip():
                    out.append((start, "".join(buf)))
                buf, start = [], None
        line += 1
    if buf and "".join(buf).strip():
        out.append((start or 1, "".join(buf)))
    return [(ln, " ".join(s.split())) for ln, s in out]


def detect_engine(text: str, path: Path) -> str:
    """Contenido primero (más fiable); la ruta solo como desempate."""
    t = text.lower()
    if re.search(r"\bconcurrently\b|\bjsonb\b|\btimestamptz\b|\bplpgsql\b|\bbigserial\b|\bserial\b|::\w+|uuid_generate_v4|gen_random_uuid"
                 r"|without time zone|using\s+(btree|gin|gist|brin|hash)\b|\boids\s*=|\bbytea\b|\bnot valid\b", t):
        return "postgresql"
    if re.search(r"\bvarchar2\b|\bnumber\s*\(|\bsysdate\b|\bnvl\(|\bexecute immediate\b|\bnovalidate\b|\btablespace\b.*\bstorage\s*\(", t):
        return "oracle"
    if re.search(r"\bnvarchar\b|\bidentity\s*\(|^\s*go\s*$|\bdatetime2\b|\[dbo\]|\bnewid\(\)|\bnonclustered\b", t, re.M):
        return "sqlserver"
    if re.search(r"\bauto_increment\b|\bengine\s*=\s*innodb\b|`\w+`|\balgorithm\s*=", t):
        return "mysql"
    p = path.as_posix().lower()
    for eng, keys in (("postgresql", ("postgres", "/pg/")), ("oracle", ("oracle", "/ora/")),
                      ("sqlserver", ("sqlserver", "mssql", "/tsql/")), ("mysql", ("mysql", "mariadb"))):
        if any(k in p for k in keys):
            return eng
    return "unknown"


Finding = dict


def add(fs: list, rule: str, sev: str, path: str, line: int, msg: str, fix: str, stmt: str) -> None:
    fs.append({"rule": rule, "severity": sev, "file": path, "line": line, "message": msg,
               "fix": fix, "statement": stmt[:200]})


def lint_statement(eng: str, path: str, line: int, s: str, fs: list, ctx: dict) -> None:
    u = s.upper()
    m_ct = re.match(r"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?([\w.\"\[\]`]+)", u)
    if m_ct:
        ctx.setdefault("created", set()).add(m_ct.group(2).strip('"[]`').split(".")[-1])
    m_ix = re.match(r"CREATE\s+(UNIQUE\s+|BITMAP\s+)?(NONCLUSTERED\s+|CLUSTERED\s+)?INDEX\b.*?\bON\s+(ONLY\s+)?([\w.\"\[\]`]+)", u)
    new_table_index = bool(m_ix and m_ix.group(4).strip('"[]`').split(".")[-1] in ctx.get("created", set()))
    # --- universales ---------------------------------------------------------------
    if re.match(r"DROP\s+(TABLE|DATABASE|SCHEMA|COLLECTION)\b", u):
        add(fs, "MIG-ALL-001", "ALTA", path, line, "Operación destructiva (DROP)",
            "Solo en fase contract tras confirmar que ninguna versión de la app la usa; respaldo/PITR verificado antes", s)
    if re.match(r"ALTER\s+TABLE\b.*\bDROP\s+(COLUMN\b|(?!CONSTRAINT|INDEX|PARTITION|DEFAULT|NOT\b|IDENTITY|EXPRESSION|PRIMARY|FOREIGN|CHECK|KEY\b)\w)", u):
        add(fs, "MIG-ALL-002", "ALTA", path, line, "Eliminación de columna",
            "Expand/contract: dejar de usarla en release N, eliminar en N+1; respaldo si contiene datos", s)
    if re.match(r"TRUNCATE\b", u):
        add(fs, "MIG-ALL-003", "ALTA", path, line, "TRUNCATE en migración", "Justificar y respaldar; nunca sobre datos de negocio", s)
    if re.match(r"(DELETE\s+FROM|UPDATE)\s+[\w.\"\[\]`]+(\s+SET\s+.+)?$", u) and " WHERE " not in f" {u} ":
        add(fs, "MIG-ALL-004", "ALTA", path, line, "DELETE/UPDATE sin WHERE",
            "Acotar con WHERE y ejecutar por lotes fuera de la migración DDL si es masivo", s)
    if re.search(r"\bRENAME\s+(COLUMN|TO)\b|\bSP_RENAME\b", u):
        add(fs, "MIG-ALL-005", "ALTA", path, line, "Renombrado incompatible con la versión anterior de la app",
            "Expand/contract: columna nueva + doble escritura + backfill + retiro posterior", s)
    if re.match(r"(UPDATE|DELETE|INSERT\s+INTO\s+\S+\s+SELECT)\b", u):
        ctx["dml"] = True
    if re.match(r"(CREATE|ALTER|DROP)\b", u):
        ctx["ddl"] = True
    # --- PostgreSQL ------------------------------------------------------------------
    if eng == "postgresql":
        if not new_table_index and re.match(r"CREATE\s+(UNIQUE\s+)?INDEX\b", u) and "CONCURRENTLY" not in u:
            add(fs, "MIG-PG-001", "ALTA", path, line, "CREATE INDEX sin CONCURRENTLY bloquea escrituras",
                "CREATE INDEX CONCURRENTLY en script no transaccional; verificar pg_index.indisvalid", s)
        if re.match(r"REINDEX\b", u) and "CONCURRENTLY" not in u:
            add(fs, "MIG-PG-002", "ALTA", path, line, "REINDEX sin CONCURRENTLY", "REINDEX ... CONCURRENTLY [PG12+]", s)
        if re.search(r"\bALTER\s+COLUMN\s+\S+\s+(SET\s+DATA\s+)?TYPE\b", u):
            add(fs, "MIG-PG-003", "ALTA", path, line, "Cambio de tipo: reescritura con ACCESS EXCLUSIVE",
                "Columna nueva + backfill + swap (salvo cambio binario-compatible verificado)", s)
        if re.search(r"\bALTER\s+COLUMN\s+\S+\s+SET\s+NOT\s+NULL\b", u):
            add(fs, "MIG-PG-004", "MEDIA", path, line, "SET NOT NULL escanea la tabla con ACCESS EXCLUSIVE",
                "ADD CONSTRAINT ck CHECK (col IS NOT NULL) NOT VALID; VALIDATE CONSTRAINT; luego SET NOT NULL [PG12+]", s)
        if re.search(r"\bADD\s+(CONSTRAINT\s+\S+\s+)?(FOREIGN\s+KEY|CHECK)\b", u) and "NOT VALID" not in u and "CREATE TABLE" not in u:
            add(fs, "MIG-PG-005", "MEDIA", path, line, "FK/CHECK sin NOT VALID valida toda la tabla bajo bloqueo",
                "ADD CONSTRAINT ... NOT VALID y VALIDATE CONSTRAINT en paso separado", s)
        if re.search(r"\bADD\s+COLUMN\b.*\bNOT\s+NULL\b", u) and "DEFAULT" not in u and not u.startswith("CREATE"):
            add(fs, "MIG-PG-006", "ALTA", path, line, "ADD COLUMN NOT NULL sin DEFAULT falla con filas existentes",
                "Añadir nullable + backfill + NOT NULL, o DEFAULT constante (metadato desde PG11)", s)
        if re.search(r"\bADD\s+COLUMN\b.*\bDEFAULT\s+(NOW\(\)|CLOCK_TIMESTAMP\(\)|RANDOM\(\)|GEN_RANDOM_UUID\(\)|UUID_GENERATE_V4\(\))", u):
            add(fs, "MIG-PG-007", "ALTA", path, line, "DEFAULT volátil en ADD COLUMN reescribe la tabla",
                "Añadir sin default, backfill por lotes y luego SET DEFAULT", s)
        if re.match(r"(VACUUM\s+FULL|CLUSTER|LOCK\s+TABLE)\b", u):
            add(fs, "MIG-PG-008", "ALTA", path, line, "Operación con bloqueo exclusivo prolongado", "pg_repack o ventana aprobada", s)
        if re.match(r"(ALTER\s+TABLE|CREATE\s+INDEX|DROP|ALTER\s+INDEX)\b", u):
            ctx["pg_needs_lock_timeout"] = True
        if re.match(r"SET\s+(LOCAL\s+)?LOCK_TIMEOUT\b", u):
            ctx["pg_has_lock_timeout"] = True
        if "CONCURRENTLY" in u:
            ctx["concurrently"] = True
    # --- Oracle ----------------------------------------------------------------------
    if eng == "oracle":
        if not new_table_index and re.match(r"CREATE\s+(UNIQUE\s+|BITMAP\s+)?INDEX\b", u) and " ONLINE" not in f" {u}":
            add(fs, "MIG-ORA-001", "MEDIA", path, line, "CREATE INDEX sin ONLINE bloquea DML (EE)",
                "CREATE INDEX ... ONLINE (Enterprise Edition)", s)
        if re.search(r"\bMODIFY\s*\(?\s*\S+\s+(NUMBER|VARCHAR2|CHAR|DATE|TIMESTAMP)", u):
            add(fs, "MIG-ORA-002", "MEDIA", path, line, "Cambio de tipo/longitud de columna",
                "Ampliar es seguro; reducir o cambiar tipo requiere columna nueva o DBMS_REDEFINITION", s)
        if re.search(r"\bMOVE\b", u) and "ONLINE" not in u and u.startswith("ALTER TABLE"):
            add(fs, "MIG-ORA-003", "ALTA", path, line, "ALTER TABLE MOVE sin ONLINE bloquea e invalida índices",
                "MOVE ONLINE (12.2+) y reconstrucción/validación de índices", s)
        if re.search(r"\bADD\s*\(?\s*\S+\s+\w+(\(\d+(,\d+)?\))?\s+NOT\s+NULL\b", u) and "DEFAULT" not in u:
            add(fs, "MIG-ORA-004", "ALTA", path, line, "ADD columna NOT NULL sin DEFAULT falla con filas",
                "DEFAULT ... NOT NULL (metadato) o nullable + backfill + NOT NULL", s)
        if re.search(r"\bADD\s+CONSTRAINT\b.*\bFOREIGN\s+KEY\b", u) and "NOVALIDATE" not in u:
            add(fs, "MIG-ORA-005", "MEDIA", path, line, "FK validada en línea sobre tabla existente",
                "ENABLE NOVALIDATE y luego VALIDATE; crear índice en la columna FK", s)
    # --- SQL Server ------------------------------------------------------------------
    if eng == "sqlserver":
        if not new_table_index and re.match(r"CREATE\s+(UNIQUE\s+)?(NONCLUSTERED\s+|CLUSTERED\s+)?INDEX\b", u) and "ONLINE" not in u:
            add(fs, "MIG-MSS-001", "MEDIA", path, line, "CREATE INDEX sin ONLINE = ON",
                "WITH (ONLINE = ON[, RESUMABLE = ON]) en ediciones que lo soportan", s)
        if re.search(r"\bALTER\s+COLUMN\b", u):
            add(fs, "MIG-MSS-002", "ALTA", path, line, "ALTER COLUMN puede reescribir la tabla y bloquear",
                "Columna nueva + backfill + swap, o ventana aprobada", s)
        if re.search(r"\bWITH\s+NOCHECK\s+ADD\b", u):
            add(fs, "MIG-MSS-003", "MEDIA", path, line, "Restricción WITH NOCHECK queda no confiable",
                "Validar después con ALTER TABLE ... WITH CHECK CHECK CONSTRAINT", s)
    # --- MySQL -----------------------------------------------------------------------
    if eng == "mysql":
        if re.match(r"ALTER\s+TABLE\b", u) and "ALGORITHM" not in u:
            add(fs, "MIG-MY-001", "MEDIA", path, line, "ALTER TABLE sin ALGORITHM/LOCK explícitos puede copiar la tabla",
                "ALGORITHM=INSTANT|INPLACE, LOCK=NONE (falla si no es posible); gh-ost/pt-osc en tablas grandes", s)
        if not new_table_index and re.match(r"CREATE\s+(UNIQUE\s+)?INDEX\b", u) and "ALGORITHM" not in u:
            add(fs, "MIG-MY-002", "BAJA", path, line, "CREATE INDEX sin ALGORITHM/LOCK explícitos",
                "ALGORITHM=INPLACE, LOCK=NONE", s)
    # --- tipos peligrosos (todos) ----------------------------------------------------
    if re.match(r"(CREATE\s+TABLE|ALTER\s+TABLE)\b", u) and re.search(
            r"\b(MONTO|IMPORTE|SALDO|VALOR|PRECIO|AMOUNT|BALANCE|PRICE|TOTAL)\w*\s+(FLOAT|REAL|DOUBLE(\s+PRECISION)?|MONEY|BINARY_DOUBLE|BINARY_FLOAT)\b", u):
        add(fs, "MIG-ALL-006", "ALTA", path, line, "Importe monetario con tipo de punto flotante/MONEY",
            "NUMERIC/DECIMAL/NUMBER(p,s) con moneda explícita", s)
    if eng == "postgresql" and re.match(r"(CREATE|ALTER)\s+TABLE\b", u) and "WITHOUT TIME ZONE" not in u \
            and re.search(r"\bTIMESTAMP(\s*\(\d\))?(?!\s+WITH\s+TIME\s+ZONE)\b", u):
        add(fs, "MIG-PG-009", "BAJA", path, line, "timestamp sin zona para instantes",
            "timestamptz para instantes; timestamp solo para fecha/hora 'de pared' deliberada", s)


LOCK_ONLY_RULES = {"MIG-PG-001", "MIG-PG-002", "MIG-PG-004", "MIG-PG-005", "MIG-PG-008", "MIG-PG-010", "MIG-PG-011",
                   "MIG-ORA-001", "MIG-ORA-003", "MIG-ORA-005", "MIG-MSS-001", "MIG-MSS-003", "MIG-MY-001", "MIG-MY-002",
                   "MIG-ALL-007"}


def lint_file(path: Path, engine: str, rel: str, new_database: bool = False) -> tuple[str, list]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    eng = detect_engine(text, path) if engine == "auto" else engine
    fs: list = []
    ctx: dict = {}
    for line, s in statements(text):
        lint_statement(eng, rel, line, s, fs, ctx)
    if eng == "postgresql" and ctx.get("pg_needs_lock_timeout") and not ctx.get("pg_has_lock_timeout"):
        add(fs, "MIG-PG-010", "BAJA", rel, 1, "DDL sin lock_timeout: puede encolar a todos detrás",
            "SET lock_timeout = '5s' al inicio (o configurarlo en la herramienta)", "")
    if ctx.get("ddl") and ctx.get("dml"):
        add(fs, "MIG-ALL-007", "MEDIA", rel, 1, "DDL y DML masivo en la misma migración",
            "Separar: DDL rápido en migración, backfill por lotes en paso/job aparte", "")
    if eng == "postgresql" and ctx.get("concurrently"):
        real = [st for _, st in statements(text) if not re.match(r"SET\s", st, re.I)]
        if len(real) > 1:
            add(fs, "MIG-PG-011", "MEDIA", rel, 1, "CONCURRENTLY junto a otras sentencias: no puede ejecutarse en transacción",
                "Script propio sin transacción (Flyway executeInTransaction=false; Liquibase runInTransaction=false)", "")
    if new_database:
        fs = [f for f in fs if f["rule"] not in LOCK_ONLY_RULES]
    return eng, fs


def modified_applied(root: Path, base: str, files: list[Path]) -> list:
    out = []
    try:
        res = subprocess.run(["git", "-C", str(root), "diff", "--name-status", f"{base}...HEAD"],
                             capture_output=True, text=True, timeout=60, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        return out
    for row in res.stdout.splitlines():
        parts = row.split("\t")
        if len(parts) >= 2 and parts[0][0] in ("M", "R", "D"):
            name = parts[-1] if parts[0][0] != "D" else parts[1]
            if MIGRATION_HINT.search(name) and name.lower().endswith((".sql", ".xml", ".yaml", ".yml")):
                out.append({"rule": "MIG-ALL-008", "severity": "ALTA", "file": name, "line": 1,
                            "message": f"Migración existente modificada ({parts[0]}) respecto a {base}",
                            "fix": "Nunca editar migraciones aplicadas: crear una nueva que corrija", "statement": ""})
    return out


def collect(paths: list[str]) -> list[tuple[Path, Path]]:
    out = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            for f in sorted(pp.rglob("*.sql")):
                if ".git" not in f.parts and "node_modules" not in f.parts:
                    out.append((f, pp))
        elif pp.is_file():
            out.append((pp, pp.parent))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Linter de migraciones SQL (candidatos)")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--engine", default="auto", choices=["auto", "postgresql", "oracle", "sqlserver", "mysql"])
    ap.add_argument("--base", help="rama/commit base para detectar migraciones aplicadas modificadas")
    ap.add_argument("--repo", help="raíz del repositorio git (por defecto, el primer path si es directorio)")
    ap.add_argument("--new-database", action="store_true",
                    help="esquema inicial sobre base vacía (carga inicial/migración de datos): omite reglas de bloqueo")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    files = collect(a.paths)
    if not files:
        print("error: no se encontraron archivos .sql", file=sys.stderr)
        return 2
    results, engines = [], {}
    for f, root in files:
        rel = f.relative_to(root).as_posix() if f.is_relative_to(root) else f.as_posix()
        eng, fs = lint_file(f, a.engine, rel, a.new_database)
        engines[rel] = eng
        results.extend(fs)
    if a.base:
        repo = Path(a.repo or (a.paths[0] if Path(a.paths[0]).is_dir() else ".")).resolve()
        results.extend(modified_applied(repo, a.base, [f for f, _ in files]))
    summary = {s: sum(1 for r in results if r["severity"] == s) for s in ("ALTA", "MEDIA", "BAJA")}
    doc = {"schema": "dba-migration-lint/1",
           "note": "Candidatos: confirmar con volumen real, versión y edición del motor.",
           "engines": engines, "summary": summary, "findings": results}
    if a.json:
        Path(a.json).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in results:
        print(f"[{r['severity']}] {r['file']}:{r['line']} {r['rule']} — {r['message']}\n    Cambio: {r['fix']}")
    print(f"Resumen: {summary} · motores: {sorted(set(engines.values()))}")
    return 1 if summary["ALTA"] else 0


if __name__ == "__main__":
    sys.exit(main())
