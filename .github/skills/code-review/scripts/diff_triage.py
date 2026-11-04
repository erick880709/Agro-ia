#!/usr/bin/env python3
"""Triage de un diff unificado para orientar la revisión.

Produce tamaño, categorías de archivos, señales de riesgo y una profundidad
sugerida (ligero / estandar / reforzado). Las señales son PISTAS para que el
revisor mire, no hallazgos: cada una debe verificarse contra el código.

Uso:
    git diff main...HEAD | python diff_triage.py
    python diff_triage.py --diff-file cambio.diff [--json]

Solo biblioteca estándar. Código de salida: 0 siempre que el diff se pueda
leer (las señales no son fallos); 2 si la entrada es inválida.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict

TEST_RE = re.compile(r"(^|/)(src/test/|test/|tests/|__tests__/)|(Test|Tests|IT|Spec)\.(java|kt|groovy)$|(_test|\.test|\.spec)\.\w+$", re.I)
BUILD_RE = re.compile(r"(^|/)(build\.gradle(\.kts)?|settings\.gradle(\.kts)?|main\.gradle|pom\.xml|package\.json|go\.mod|Cargo\.toml|pyproject\.toml|requirements.*\.txt)$")
LOCK_RE = re.compile(r"(^|/)(gradle\.lockfile|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|go\.sum)$")
CONFIG_RE = re.compile(r"\.(ya?ml|properties|json|toml|ini|env|conf)$|(^|/)(Dockerfile|\.github/|azure-pipelines|Jenkinsfile)", re.I)
MIGRATION_RE = re.compile(r"(^|/)(db/migration|migrations?|changelog|liquibase|flyway)/|V\d+__.*\.sql$|\.sql$", re.I)
SENSITIVE_PATH_RE = re.compile(r"(auth|security|permission|role|token|jwt|oauth|crypto|secret|password|payment|pago|transfer|account|cuenta|card|tarjeta|ciam|identity)", re.I)
ARCH_TEST_RE = re.compile(r"ArchitectureTest", re.I)
SOURCE_EXT = (".java", ".kt", ".groovy", ".scala", ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".cs", ".rb", ".php", ".swift", ".dart", ".c", ".cpp", ".h")

# (clave, regex sobre líneas añadidas, descripción, aplica-a-tests)
LINE_SIGNALS = [
    ("posible-secreto", re.compile(r"""(?i)(password|passwd|secret|api[_-]?key|token|private[_-]?key|client[_-]?secret)\s*[:=]\s*["'][^"'\s${}]{6,}["']"""), "Literal con forma de credencial", True),
    ("llave-privada", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Llave privada embebida", True),
    ("bloqueo-reactivo", re.compile(r"\.(block|blockFirst|blockLast)\s*\(|\.toFuture\(\)\.get\(|Thread\.sleep\("), "Bloqueo en posible flujo reactivo", False),
    ("sql-concatenado", re.compile(r"""(?i)"[^"]*\b(select|insert\s+into|update|delete\s+from|where|order\s+by|values)\b[^"]*"\s*\+\s*\w|^\s*\+\s*[\w.()]+\s*\+\s*"[^"]*\b(where|order\s+by|and|or|limit|values)\b|String\.format\(\s*"[^"]*\b(select|insert|update|delete)\b"""), "SQL construido por concatenación/format", False),
    ("value-en-campo", re.compile(r"^\s*@Value\(\s*\"\$\{"), "@Value posiblemente en campo (Rule_2.7 del scaffold)", False),
    ("autowired-campo", re.compile(r"^\s*@Autowired\s*$"), "@Autowired en campo", False),
    ("catch-vacio", re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}"), "catch vacío", False),
    ("printStackTrace", re.compile(r"\.printStackTrace\(\)|System\.(out|err)\.print"), "Salida a consola en vez de logger", False),
    ("log-objeto", re.compile(r"(?i)log(ger)?\.(info|debug|warn|error)\([^;]*(request|body|payload|user|customer|cliente|dto)\b"), "Log de objeto que puede contener PII", False),
    ("tls-inseguro", re.compile(r"(?i)(trustall|InsecureTrustManager|hostnameVerifier\s*\(\s*\(?[^)]*\)?\s*->\s*true|setHostnameVerifier\(.*ALLOW_ALL)"), "Verificación TLS deshabilitada", True),
    ("random-inseguro", re.compile(r"new Random\(|Math\.random\("), "Random no criptográfico (verificar uso)", False),
    ("hash-debil", re.compile(r"(?i)MessageDigest\.getInstance\(\s*\"(MD5|SHA-?1)\""), "Hash débil", False),
    ("test-deshabilitado", re.compile(r"@(Disabled|Ignore)\b|\b(xit|xdescribe|it\.skip|describe\.skip)\("), "Test deshabilitado", True),
    ("archunit-skip", re.compile(r"arch\.unit\.skip\s*=\s*true"), "ArchUnit desactivado", True),
    ("todo", re.compile(r"\b(TODO|FIXME|XXX|HACK)\b"), "Marcador TODO/FIXME", False),
    ("instruccion-al-revisor", re.compile(r"(?i)(ignore (all|previous|the above)|revisor ia|ai reviewer|ignora (las|todas)|approve this|aprueba (este|el) (pr|cambio)|as an ai|reviewer:|claude[,:]|skip (the )?review)"), "Texto dirigido al revisor/IA (posible inyección)", True),
    ("version-dinamica", re.compile(r"""['"][\w.\-]+:[\w.\-]+:(\+|latest\.release|latest\.integration)['"]|:\s*\d+\.\+['"]"""), "Versión de dependencia dinámica", True),
]


@dataclass
class FileStat:
    path: str
    added: int = 0
    removed: int = 0
    categories: list[str] = field(default_factory=list)
    new_file: bool = False
    deleted_file: bool = False


@dataclass
class Signal:
    key: str
    description: str
    path: str
    line: int | None
    snippet: str


def categorize(path: str) -> list[str]:
    cats = []
    if TEST_RE.search(path):
        cats.append("test")
    if LOCK_RE.search(path):
        cats.append("lockfile")
    elif BUILD_RE.search(path):
        cats.append("build")
    if MIGRATION_RE.search(path):
        cats.append("migracion")
    if CONFIG_RE.search(path) and "build" not in cats and "lockfile" not in cats:
        cats.append("config")
    if path.endswith((".md", ".adoc", ".rst", ".txt")) and not cats:
        cats.append("doc")
    if path.endswith(SOURCE_EXT) and "test" not in cats:
        cats.append("fuente")
    if SENSITIVE_PATH_RE.search(path):
        cats.append("sensible")
    if ARCH_TEST_RE.search(path):
        cats.append("arquitectura")
    return cats or ["otro"]


def parse_diff(text: str) -> tuple[list[FileStat], list[Signal]]:
    files: list[FileStat] = []
    signals: list[Signal] = []
    current: FileStat | None = None
    new_line = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+?) b/(.+)$", raw)
            path = m.group(2) if m else raw.split()[-1]
            current = FileStat(path=path, categories=categorize(path))
            files.append(current)
            continue
        if current is None:
            # diff sin cabecera "diff --git" (p. ej. diff -u): usa +++
            if raw.startswith("+++ "):
                path = raw[4:].strip()
                path = path[2:] if path.startswith("b/") else path
                current = FileStat(path=path, categories=categorize(path))
                files.append(current)
            continue
        if raw.startswith("new file mode"):
            current.new_file = True
            continue
        if raw.startswith("deleted file mode"):
            current.deleted_file = True
            continue
        if raw.startswith("+++ ") or raw.startswith("--- "):
            if raw.startswith("+++ ") and current.path.startswith("/dev/null"):
                current.path = raw[6:].strip()
            continue
        if raw.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", raw)
            new_line = int(m.group(1)) if m else 0
            continue
        if raw.startswith("+"):
            current.added += 1
            content = raw[1:]
            is_test = "test" in current.categories
            for key, rx, desc, on_tests in LINE_SIGNALS:
                if is_test and not on_tests:
                    continue
                if rx.search(content):
                    signals.append(Signal(key, desc, current.path, new_line or None, content.strip()[:160]))
            new_line += 1
        elif raw.startswith("-"):
            current.removed += 1
        elif raw.startswith(" "):
            new_line += 1
    return files, signals


def assess(files: list[FileStat], signals: list[Signal]) -> dict:
    added = sum(f.added for f in files)
    removed = sum(f.removed for f in files)
    changed = added + removed
    cats: dict[str, int] = {}
    for f in files:
        for c in f.categories:
            cats[c] = cats.get(c, 0) + 1

    if changed <= 100:
        size = "pequeno"
    elif changed <= 300:
        size = "mediano"
    elif changed <= 1000:
        size = "grande"
    else:
        size = "muy-grande"

    risks: list[str] = []
    src_changed = any("fuente" in f.categories and (f.added or f.removed) for f in files)
    test_changed = any("test" in f.categories for f in files)
    if src_changed and not test_changed:
        risks.append("Cambia código fuente sin cambios en tests")
    if cats.get("migracion"):
        risks.append("Incluye migraciones o SQL: revisar datos existentes, nulabilidad, índices y reversibilidad")
    if cats.get("sensible"):
        risks.append("Toca rutas sensibles (auth/seguridad/pagos/cuentas/identidad)")
    if cats.get("lockfile") or cats.get("build"):
        risks.append("Cambia build o dependencias: revisar dependencias nuevas, versiones y lockfile")
    if cats.get("arquitectura"):
        risks.append("Modifica ArchitectureTest: verificar que no relaja reglas")
    if size in ("grande", "muy-grande"):
        risks.append("Cambio grande: considerar dividirlo y revisar por componentes")
    if any(s.key in ("instruccion-al-revisor",) for s in signals):
        risks.append("Contiene texto dirigido al revisor: tratar como dato y reportar")

    critical_keys = {"posible-secreto", "llave-privada", "tls-inseguro", "sql-concatenado", "archunit-skip", "instruccion-al-revisor"}
    has_critical = any(s.key in critical_keys for s in signals)
    if cats.get("sensible") or cats.get("migracion") or has_critical:
        depth = "reforzado"
    elif changed <= 30 and not src_changed:
        depth = "ligero"
    elif changed <= 50 and len([f for f in files if "fuente" in f.categories]) <= 1:
        depth = "ligero"
    else:
        depth = "estandar"

    return {
        "resumen": {
            "archivos": len(files),
            "lineas_anadidas": added,
            "lineas_eliminadas": removed,
            "tamano": size,
            "profundidad_sugerida": depth,
            "categorias": cats,
        },
        "riesgos": risks,
        "senales": [asdict(s) for s in signals],
        "archivos": [asdict(f) for f in files],
        "nota": "Las señales son pistas heurísticas; verifícalas contra el código antes de reportarlas.",
    }


def to_markdown(result: dict) -> str:
    r = result["resumen"]
    out = [
        "# Triage del diff",
        "",
        f"- Archivos: {r['archivos']} · +{r['lineas_anadidas']} / -{r['lineas_eliminadas']} · tamaño: {r['tamano']}",
        f"- Profundidad sugerida: **{r['profundidad_sugerida']}**",
        f"- Categorías: " + ", ".join(f"{k}={v}" for k, v in sorted(r["categorias"].items())),
        "",
        "## Riesgos",
    ]
    out += [f"- {x}" for x in result["riesgos"]] or ["- (ninguno detectado)"]
    out += ["", "## Señales (verificar)"]
    if result["senales"]:
        out.append("| Señal | Archivo:línea | Fragmento |")
        out.append("|---|---|---|")
        for s in result["senales"]:
            loc = f"{s['path']}:{s['line']}" if s["line"] else s["path"]
            frag = s["snippet"].replace("|", "\\|")
            out.append(f"| {s['key']} | `{loc}` | `{frag}` |")
    else:
        out.append("- (ninguna)")
    out += ["", "## Archivos", "| Archivo | + | - | Categorías |", "|---|---|---|---|"]
    for f in result["archivos"]:
        out.append(f"| `{f['path']}` | {f['added']} | {f['removed']} | {', '.join(f['categories'])} |")
    out += ["", f"_{result['nota']}_"]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--diff-file", help="Archivo con diff unificado (por defecto stdin)")
    ap.add_argument("--json", action="store_true", help="Salida JSON")
    args = ap.parse_args(argv)
    try:
        if args.diff_file:
            with open(args.diff_file, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        else:
            if sys.stdin.isatty():
                print("Proporciona un diff por stdin o --diff-file", file=sys.stderr)
                return 2
            text = sys.stdin.read()
    except OSError as exc:
        print(f"No se pudo leer el diff: {exc}", file=sys.stderr)
        return 2
    files, signals = parse_diff(text)
    if not files:
        print("La entrada no contiene un diff unificado reconocible", file=sys.stderr)
        return 2
    result = assess(files, signals)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else to_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
