#!/usr/bin/env python3
"""Triage de bases de datos para la skill dba.

Inventaría motores y drivers (manifiestos, configuración, docker-compose, IaC),
herramientas de migración y archivos de migración (opcionalmente solo los cambiados
frente a --base), y emite SEÑALES candidatas en código, SQL, NoSQL e IaC de datos más un
plan de herramientas. No se conecta a ninguna base. Las credenciales que aparezcan en
URLs de conexión se enmascaran.

Uso: python db_triage.py <repo> [--base origin/main] [--json salida.json] [--max-signals 400]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKIP = {".git", "node_modules", "vendor", "dist", "build", "target", ".gradle", ".terraform",
        ".terragrunt-cache", "__pycache__", ".venv", "venv", ".angular", "coverage", ".idea"}
EXT = {".java", ".kt", ".go", ".ts", ".js", ".py", ".sql", ".xml", ".yaml", ".yml", ".properties",
       ".gradle", ".kts", ".json", ".tf", ".hcl", ".toml", ".mod", ".env", ".prisma", ".cql"}
NAMES = {"go.mod", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", "pom.xml",
         "build.gradle", "build.gradle.kts", "package.json", "Dockerfile"}

ENGINE_MARKERS = {
    "postgresql": [r"org\.postgresql", r"r2dbc-postgresql", r"jdbc:postgresql", r"r2dbc:postgresql", r"jackc/pgx", r"lib/pq",
                   r"\bpg\b\"?\s*:", r"image:\s*\"?postgres", r"aws_rds_cluster[^\n]*", r"engine\s*=\s*\"aurora-postgresql\"",
                   r"engine\s*=\s*\"postgres\"", r"azurerm_postgresql", r"POSTGRES"],
    "oracle": [r"com\.oracle\.database\.jdbc", r"ojdbc\d*", r"jdbc:oracle", r"godror", r"go-ora", r"oracledb",
               r"engine\s*=\s*\"oracle-", r"image:\s*\"?(gvenzl/)?oracle"],
    "sqlserver": [r"mssql-jdbc", r"jdbc:sqlserver", r"go-mssqldb", r"\bmssql\b", r"engine\s*=\s*\"sqlserver-",
                  r"azurerm_mssql", r"image:\s*\"?mcr\.microsoft\.com/mssql"],
    "mysql": [r"mysql-connector", r"jdbc:mysql", r"jdbc:mariadb", r"go-sql-driver/mysql", r"engine\s*=\s*\"(aurora-)?mysql\"",
              r"image:\s*\"?(mysql|mariadb)"],
    "dynamodb": [r"software\.amazon\.awssdk:dynamodb", r"dynamodb-enhanced", r"aws-sdk-go-v2/service/dynamodb",
                 r"@aws-sdk/client-dynamodb", r"aws_dynamodb_table", r"DynamoDbEnhancedClient"],
    "mongodb": [r"spring-boot-starter-data-mongodb", r"mongodb-driver", r"go\.mongodb\.org/mongo-driver", r"\bmongoose\b",
                r"mongodb(\+srv)?://", r"aws_docdb_cluster", r"azurerm_cosmosdb"],
    "redis": [r"spring-boot-starter-data-redis", r"lettuce", r"jedis", r"go-redis", r"\bioredis\b", r"aws_elasticache",
              r"azurerm_redis", r"image:\s*\"?redis"],
    "cassandra": [r"java-driver-core", r"datastax", r"gocql", r"scylla", r"aws_keyspaces"],
    "opensearch": [r"opensearch", r"elasticsearch"],
}
MIGRATION_TOOLS = {
    "flyway": [r"flyway", r"db/migration/V\d+"], "liquibase": [r"liquibase", r"changelog"],
    "golang-migrate": [r"golang-migrate", r"\.up\.sql$"], "goose": [r"pressly/goose", r"-- \+goose"],
    "atlas": [r"ariga\.io/atlas", r"atlas\.hcl"], "prisma": [r"schema\.prisma", r"\"prisma\""],
    "alembic": [r"alembic"], "sqlc": [r"sqlc\.ya?ml"],
}


def R(id_, cat, rx, hint, exts, flags=re.I):
    return (id_, cat, re.compile(rx, flags), hint, tuple(exts))


CODE = (".java", ".kt", ".go", ".ts", ".js", ".py")
SQLF = (".sql",)
CONF = (".yaml", ".yml", ".properties")
IAC = (".tf", ".hcl")
RULES = [
    R("sql.select-star", "consulta-indice", r"\bSELECT\s+\*\s+FROM\b", "SELECT * en código: proyección explícita", CODE + SQLF),
    R("sql.offset-pagination", "consulta-indice", r"\bOFFSET\s+(\d{4,}|[:?$]\w*|\$\d)", "Paginación OFFSET: valorar keyset si es profunda", CODE + SQLF),
    R("sql.function-on-column", "consulta-indice", r"\bWHERE\b[^;\n]*\b(YEAR|MONTH|UPPER|LOWER|TRUNC|DATE|TO_CHAR|CAST|CONVERT|SUBSTR|SUBSTRING|LEFT)\s*\(\s*[a-z_]+\.?[a-z_]*\s*[,)]",
      "Función sobre columna en WHERE: no SARGable salvo índice de expresión", CODE + SQLF),
    R("sql.not-in-subquery", "consulta-indice", r"\bNOT\s+IN\s*\(\s*SELECT\b", "NOT IN con subconsulta: riesgo con NULL; usar NOT EXISTS", CODE + SQLF),
    R("sql.leading-wildcard", "consulta-indice", r"\bLIKE\s+'%[^']+", "LIKE con comodín inicial: no usa B-tree (pg_trgm / full-text)", CODE + SQLF),
    R("sql.money-float", "modelo-integridad", r"\b(monto|importe|saldo|valor|precio|amount|balance|price|total)\w*\s+(float|real|double( precision)?|money|binary_double)\b",
      "Dinero con punto flotante/MONEY", SQLF),
    R("sql.count-exists", "consulta-indice", r"\bCOUNT\s*\(\s*\*\s*\)\s*>\s*0", "COUNT(*) > 0: usar EXISTS", CODE + SQLF),
    R("sql.concat-query", "seguridad-datos", r"(createNativeQuery|createQuery|executeQuery|\.query|\.sql|Query(Row|Context)?|Exec(Context)?)\(\s*(ctx,\s*)?(\"[^\"]*\"\s*\+|fmt\.Sprintf)",
      "SQL construido por concatenación (también es tema de aegis)", CODE),
    R("jpa.eager", "consulta-indice", r"FetchType\.EAGER", "EAGER: riesgo de grafos enormes/N+1", (".java", ".kt")),
    R("jpa.find-all", "consulta-indice", r"\.findAll\(\s*\)", "findAll() sin paginación", (".java", ".kt")),
    R("jpa.ddl-auto", "migracion", r"ddl-auto\s*[:=]\s*(update|create|create-drop)", "ddl-auto modifica esquema: migraciones como fuente de verdad", CONF),
    R("jpa.open-in-view", "transaccion-concurrencia", r"open-in-view\s*[:=]\s*true", "open-in-view retiene conexiones y consultas perezosas", CONF),
    R("jpa.identity-batch", "consulta-indice", r"GenerationType\.IDENTITY", "IDENTITY deshabilita batch inserts en Hibernate (valorar secuencia)", (".java", ".kt")),
    R("r2dbc.block", "transaccion-concurrencia", r"\.block(First|Last)?\(\)", "block() en flujo reactivo", (".java", ".kt")),
    R("pool.large", "transaccion-concurrencia", r"(maximum-pool-size|maxPoolSize|max-size|SetMaxOpenConns\()\s*[:=(]?\s*(\d{3,}|[5-9]\d)",
      "Pool grande: validar contra max_connections × réplicas", CONF + CODE),
    R("go.query-no-context", "transaccion-concurrencia", r"\bdb\.(Query|QueryRow|Exec)\(", "Consulta sin Context/timeout", (".go",)),
    R("dynamo.scan", "nosql-acceso", r"\.scan\(|ScanRequest|\bScan\(|ScanInput|ScanCommand", "Scan en DynamoDB: inaceptable en ruta de usuario", CODE),
    R("mongo.where-regex", "nosql-acceso", r"\$where|\$regex\s*:\s*['\"](?!\^)", "$where o regex sin prefijo anclado: escaneo", CODE + (".json",)),
    R("mongo.auto-index", "migracion", r"auto-index-creation\s*[:=]\s*true", "Creación automática de índices en Mongo", CONF),
    R("redis.keys", "operacion-disponibilidad", r"\.keys\(\s*['\"][^'\"]*\*|\bKEYS\s+\*", "KEYS con patrón: O(N) bloqueante; usar SCAN", CODE),
    R("redis.no-ttl", "operacion-disponibilidad", r"opsForValue\(\)\.set\(\s*[^,]+,\s*[^,)]+\)", "SET sin TTL en caché", (".java", ".kt")),
    R("cql.allow-filtering", "nosql-acceso", r"ALLOW\s+FILTERING", "ALLOW FILTERING: escaneo", CODE + (".cql",)),
    R("conn.password-in-url", "seguridad-datos", r"(jdbc|r2dbc|postgres(ql)?|mysql|mongodb(\+srv)?|sqlserver|redis)://[^\s:@/]+:[^\s@/'\"]{3,}@",
      "Credenciales en URL de conexión (valor enmascarado)", CODE + CONF + (".env", ".json")),
    R("iac.no-pitr", "operacion-disponibilidad", r"point_in_time_recovery\s*\{[^}]*enabled\s*=\s*false|enabled\s*=\s*false\s*#\s*pitr", "PITR deshabilitado", IAC, re.I | re.S),
    R("iac.backup-retention-zero", "operacion-disponibilidad", r"backup_retention_period\s*=\s*[01]\b", "Retención de backups 0–1 días", IAC),
    R("iac.no-deletion-protection", "operacion-disponibilidad", r"deletion_protection(_enabled)?\s*=\s*false", "Sin protección contra borrado", IAC),
    R("iac.skip-final-snapshot", "operacion-disponibilidad", r"skip_final_snapshot\s*=\s*true", "Sin snapshot final al destruir", IAC),
    R("iac.single-az", "operacion-disponibilidad", r"multi_az\s*=\s*false", "Instancia sin Multi-AZ: validar contra RTO", IAC),
    R("iac.storage-unencrypted", "seguridad-datos", r"storage_encrypted\s*=\s*false", "Almacenamiento sin cifrado", IAC),
    R("iac.publicly-accessible", "seguridad-datos", r"publicly_accessible\s*=\s*true", "Base accesible públicamente (handoff aegis)", IAC),
]

TOOL_PLAN = {
    "postgresql": [("squawk", "squawk <migraciones>/*.sql"), ("psql", "psql \"$DATABASE_URL\" -c 'select version()'  # solo lectura, destino autorizado")],
    "oracle": [("sql", "sql -S <usuario>@<tns>  # SQLcl, solo lectura"), ("utPLSQL", "utplsql run ...")],
    "sqlserver": [("sqlcmd", "sqlcmd -S <srv> -Q \"SELECT @@VERSION\"")],
    "mysql": [("mysql", "mysql -e 'SELECT VERSION()'"), ("pt-online-schema-change", "pt-online-schema-change --dry-run ...")],
    "mongodb": [("mongosh", "mongosh \"$MONGO_URL\" --eval 'db.version()'")],
    "dynamodb": [("aws", "aws dynamodb describe-table --table-name <t>")],
    "atlas": [("atlas", "atlas migrate lint --dev-url docker://postgres/16 --latest 1")],
    "sqlfluff": [("sqlfluff", "sqlfluff lint <migraciones> --dialect <postgres|oracle|tsql|mysql>")],
}


def mask_url(s: str) -> str:
    return re.sub(r"(://[^\s:@/]+:)([^\s@/'\"]{3,})(@)", lambda m: m.group(1) + "***" + m.group(3), s)


def iter_files(root: Path) -> list[Path]:
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            p = Path(d) / f
            if p.suffix.lower() in EXT or f in NAMES or f.startswith(".env"):
                out.append(p)
    return sorted(out)


def changed(root: Path, base: str) -> set[str] | None:
    try:
        r = subprocess.run(["git", "-C", str(root), "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True, timeout=60, check=True)
        r2 = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "HEAD"], capture_output=True, text=True, timeout=60)
    except (subprocess.SubprocessError, FileNotFoundError):
        return None
    return set(r.stdout.split()) | set(r2.stdout.split())


def is_test(rel: str) -> bool:
    return bool(re.search(r"(^|/)(src/test|tests?|testdata|fixtures|__tests__)(/|$)|_test\.go$|\.spec\.ts$|Test\.java$", rel))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Triage de bases de datos (señales candidatas)")
    ap.add_argument("repo")
    ap.add_argument("--base")
    ap.add_argument("--json")
    ap.add_argument("--max-signals", type=int, default=400)
    a = ap.parse_args(argv)
    root = Path(a.repo).resolve()
    if not root.is_dir():
        print(f"error: {root} no es directorio", file=sys.stderr)
        return 2
    files = iter_files(root)
    texts: dict[str, str] = {}
    for f in files:
        try:
            if f.stat().st_size <= 1_500_000:
                texts[f.relative_to(root).as_posix()] = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass
    engines = {}
    for eng, pats in ENGINE_MARKERS.items():
        hits = sorted({rel for rel, t in texts.items() for p in pats if re.search(p, t, re.I)})
        if hits:
            engines[eng] = hits[:8]
    tools = {}
    for tool, pats in MIGRATION_TOOLS.items():
        hits = sorted({rel for rel, t in texts.items() for p in pats if re.search(p, rel, re.I) or re.search(p, t[:20000], re.I)})
        if hits:
            tools[tool] = hits[:5]
    migrations = sorted(rel for rel in texts if rel.lower().endswith(".sql") and re.search(
        r"(^|/)(db/migration|migrations?|changelog|schema|sql)(/|$)|^V\d+__|/V\d+(_\d+)*__|\.(up|down)\.sql$", rel, re.I))
    scope, ch = "full", None
    if a.base:
        ch = changed(root, a.base)
        if ch is not None:
            scope = f"diff:{a.base}"
    signals = []
    for rel, t in texts.items():
        if ch is not None and rel not in ch:
            continue
        suf = Path(rel).suffix.lower()
        for i, line in enumerate(t.splitlines(), 1):
            if len(signals) >= a.max_signals or len(line) > 4000:
                break
            for rid, cat, rx, hint, exts in RULES:
                if suf in exts and rx.search(line):
                    signals.append({"rule": rid, "category": cat, "file": rel, "line": i, "test_path": is_test(rel),
                                    "excerpt": mask_url(line.strip())[:200], "hint": hint})
        # reglas multilínea para IaC
        if suf in IAC:
            for rid, cat, rx, hint, exts in RULES:
                if rid == "iac.no-pitr" and rx.search(t) and not any(s["rule"] == rid and s["file"] == rel for s in signals):
                    ln = t[: rx.search(t).start()].count("\n") + 1
                    signals.append({"rule": rid, "category": cat, "file": rel, "line": ln, "test_path": False, "excerpt": "point_in_time_recovery deshabilitado", "hint": hint})
    changed_migrations = sorted(m for m in migrations if ch is not None and m in ch)
    plan, seen = [], set()
    keys = list(engines) + [k for k in ("atlas",) if k in tools] + (["sqlfluff"] if migrations else [])
    for k in keys:
        for tool, cmd in TOOL_PLAN.get(k, []):
            if (tool, cmd) not in seen:
                seen.add((tool, cmd))
                plan.append({"for": k, "tool": tool, "command": cmd, "installed": shutil.which(tool) is not None})
    if migrations:
        plan.insert(0, {"for": "migraciones", "tool": "migration_lint", "installed": True,
                        "command": f"python {Path(__file__).with_name('migration_lint.py')} <dir_migraciones> --engine auto" + (f" --base {a.base}" if a.base else "")})
    by = {}
    for s in signals:
        by[s["category"]] = by.get(s["category"], 0) + 1
    doc = {"schema": "dba-triage/1", "note": "Señales candidatas para análisis manual; no son observaciones.",
           "repo": str(root), "scope": scope, "engines": engines, "migration_tools": tools,
           "migrations": {"count": len(migrations), "changed": changed_migrations, "sample": migrations[-10:]},
           "signals_by_category": dict(sorted(by.items())), "truncated": len(signals) >= a.max_signals,
           "signals": signals, "tool_plan": plan}
    out = json.dumps(doc, ensure_ascii=False, indent=2)
    if a.json:
        Path(a.json).write_text(out, encoding="utf-8")
        print(f"motores={','.join(engines) or '-'} migración={','.join(tools) or '-'} migraciones={len(migrations)} "
              f"señales={len(signals)} -> {a.json}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
