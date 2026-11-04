#!/usr/bin/env python3
"""
Revisa archivos .feature de Karate y reporta patrones que pueden causar errores.
No ejecuta las pruebas. Los hallazgos requieren revisar el contexto del código.

Uso:
  python lint_features.py <ruta> [<ruta> ...] [--linea v1|v2] [--json] [--max-pasos 40]

Detecta (IDs alineados con references/10-arquitectura-de-suite.md):
  A1  URL absoluta escrita directamente en url/path
  A2  posible secreto en texto plano
  A3  login dentro del escenario (en vez de callSingle)
  A4  esperas fijas (Thread.sleep, delay(), karate.pause) como sincronización
  A5  escenario con request HTTP sin 'status' o sin 'match'
  A6  escenario que solo valida status (sin match)
  A11 objeto literal con identificador sin '#()' (Karate lo interpreta como texto)
  A12 @parallel=false en proyecto v2 (se ignora en silencio)
  A13 archivo .feature reutilizable sin @ignore ni escenarios ejecutables propios
  A14 print de response/request completos
  A16 nombre de escenario genérico o vacío
  A17 SQL construido por concatenación
  A20 escenario demasiado largo

Código de salida: 1 si hay hallazgos Bloqueantes, 0 en otro caso.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SEV_ORDER = {"Bloqueante": 0, "Mayor": 1, "Menor": 2}

STEP_RE = re.compile(r"^\s*(\*|Given|When|Then|And|But)\s+(.*)$")
SCENARIO_RE = re.compile(r"^\s*(Scenario Outline|Scenario|Escenario|Esquema del escenario)\s*:\s*(.*)$")
BACKGROUND_RE = re.compile(r"^\s*(Background|Antecedentes)\s*:")
EXAMPLES_RE = re.compile(r"^\s*(Examples|Ejemplos)\s*:")
FEATURE_RE = re.compile(r"^\s*(Feature|Característica)\s*:")
TAG_LINE_RE = re.compile(r"^\s*@")

SECRET_RE = re.compile(
    r"""(?ix)
    (password|passwd|clave|contrasena|contraseña|secret|client_secret|clientsecret|api[_-]?key|apikey|token)
    \s*[:=]\s*['"]([^'"#][^'"]{5,})['"]
    """)
BEARER_LITERAL_RE = re.compile(r"Bearer\s+[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{10,}")
URL_RE = re.compile(r"""^(url|path)\s+['"]https?://""", re.I)
URL_ANY_RE = re.compile(r"""['"]https?://(?!localhost|127\.0\.0\.1)[^'"]+['"]""")
WAIT_RE = re.compile(r"(Thread\.sleep|java\.lang\.Thread\.sleep|\bdelay\(\s*\d{3,}|karate\.pause\(\s*\d{3,})")
PRINT_FULL_RE = re.compile(r"^print\s+(response|request|responseHeaders)\s*$")
SQL_CONCAT_RE = re.compile(r"""(?i)['"]\s*(select|update|delete|insert)\b[^'"]*['"]\s*\+""")
SQL_CONCAT2_RE = re.compile(r"""(?i)\b(where|and|values|set)\b[^'"]*=\s*['"]?\s*\+\s*\w""")
GENERIC_NAME_RE = re.compile(r"(?i)^(test|prueba|caso|scenario|escenario)?\s*\d*$|^(validar|probar|test)\s+(servicio|api|endpoint)$")
# Detecta valores sin comillas en objetos: { id: id } o { id: response.id }.
# La regla A11 comprueba si necesitan la expresión de Karate #().
UNQUOTED_ID_RE = re.compile(r"[{,]\s*['\"]?[\w-]+['\"]?\s*:\s*([A-Za-z_$][\w$]*(?:\.[\w$\[\]]+)*)\s*(?=[,}])")
JSON_KEYWORDS = {"true", "false", "null"}


class Finding:
    def __init__(self, file, line, rule, sev, msg, fix):
        self.file, self.line, self.rule, self.sev, self.msg, self.fix = str(file), line, rule, sev, msg, fix

    def as_dict(self):
        return self.__dict__


def is_object_literal_step(text):
    """Identifica pasos cuyo objeto '{...}' se interpreta como JSON de Karate."""
    m = re.match(r"^(def\s+\w+\s*=|request|match\s+.+?(==|contains)|set\s+\S+\s*=|configure\s+\w+\s*=)\s*(\{.*\})\s*$", text)
    if m:
        return m.group(3)
    m = re.match(r"^.*\b(call|callonce)\s+read\([^)]*\)\s*(\{.*\})\s*$", text)
    if m:
        return m.group(2)
    return None


def lint_file(path: Path, linea: str, max_pasos: int):
    findings = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    feature_tags = set()
    scenarios = []          # Cada escenario guarda nombre, línea, pasos con su línea y etiquetas.
    current = None
    pending_tags = set()
    in_docstring = False
    in_examples = False
    seen_feature = False

    for i, raw in enumerate(lines, start=1):
        s = raw.strip()
        if s.startswith('"""'):
            in_docstring = not in_docstring
            if current is not None:
                current["doc_lines"].append(i)
            continue
        if in_docstring:
            if current is not None:
                current["doc"].append((i, s))
            # Busca también posibles secretos en los bloques de texto de Karate.
            check_secret(findings, path, i, s)
            continue
        if not s or s.startswith("#"):
            continue
        if TAG_LINE_RE.match(s):
            tags = set(re.findall(r"@[\w=\-.:*/]+", s))
            if not seen_feature:
                feature_tags |= tags
            else:
                pending_tags |= tags
            continue
        if FEATURE_RE.match(s):
            seen_feature = True
            continue
        if BACKGROUND_RE.match(s):
            current = {"name": "Background", "line": i, "steps": [], "tags": set(), "bg": True, "doc": [], "doc_lines": []}
            scenarios.append(current)
            in_examples = False
            continue
        m = SCENARIO_RE.match(s)
        if m:
            current = {"name": m.group(2).strip(), "line": i, "steps": [], "tags": pending_tags,
                       "bg": False, "outline": "Outline" in m.group(1) or "Esquema" in m.group(1),
                       "doc": [], "doc_lines": []}
            pending_tags = set()
            scenarios.append(current)
            in_examples = False
            continue
        if EXAMPLES_RE.match(s):
            in_examples = True
            # Una etiqueta @ignore antes de Examples pertenece a esa tabla.
            # Consumirla aquí evita tratar el siguiente escenario como auxiliar y omitir la regla A5.
            pending_tags = set()
            continue
        if s.startswith("|"):
            continue
        sm = STEP_RE.match(raw)
        if sm and current is not None and not in_examples:
            current["steps"].append((i, sm.group(2).strip()))

    all_tags = feature_tags
    # ---------- reglas por paso ----------
    for sc in scenarios:
        for ln, text in sc["steps"]:
            if URL_RE.match(text) or (text.lower().startswith("url ") and URL_ANY_RE.search(text)):
                findings.append(Finding(path, ln, "A1", "Mayor", "URL hardcodeada en la feature",
                                        "Definir la URL por ambiente en karate-config.js y usar `url baseUrl`"))
            check_secret(findings, path, ln, text)
            if WAIT_RE.search(text):
                findings.append(Finding(path, ln, "A4", "Mayor", f"Espera fija: `{text[:60]}`",
                                        "Usar `retry until` (API) o `waitFor*` / `retry()` (UI)"))
            if PRINT_FULL_RE.match(text):
                findings.append(Finding(path, ln, "A14", "Mayor", "print de payload completo (posibles datos sensibles en reportes)",
                                        "Imprimir solo identificadores y configurar masking (configure logging / logModifier)"))
            if SQL_CONCAT_RE.search(text) or (re.search(r"(?i)\b(select|update|delete|insert)\b", text) and SQL_CONCAT2_RE.search(text)):
                findings.append(Finding(path, ln, "A17", "Bloqueante", "SQL construido por concatenación",
                                        "Usar consultas parametrizadas: db.readRow('... WHERE ID = ?', id)"))
            obj = is_object_literal_step(text)
            if obj:
                for val in UNQUOTED_ID_RE.findall(obj):
                    if val in JSON_KEYWORDS or re.fullmatch(r"-?\d+(\.\d+)?", val):
                        continue
                    findings.append(Finding(path, ln, "A11", "Mayor",
                                            f"`{val}` sin comillas dentro de JSON de Karate se lee como el string '{val}', no como variable",
                                            f"Usar '#({val})' o envolver el objeto en paréntesis: ({obj})"))
                    break

        # ---------- reglas por escenario ----------
        if sc["bg"]:
            continue
        texts = [t for _, t in sc["steps"]]
        has_method = any(re.match(r"^method\s+\w+", t) for t in texts)
        has_status = any(re.match(r"^status\s+", t) or "responseStatus" in t for t in texts)
        expects_2xx = any(re.match(r"^status\s+(2\d\d|<)", t) for t in texts)
        has_match = any(t.startswith("match ") or t.startswith("assert ") or "karate.match(" in t
                        or "karate.expect(" in t or t.startswith("retry until") for t in texts)
        is_ui = any(re.match(r"^(driver\b|click\(|input\(|waitFor)", t) for t in texts)
        effective_tags = sc["tags"] | feature_tags
        is_helper = "@ignore" in effective_tags or "@setup" in effective_tags
        is_mock = bool(re.search(r"pathMatches\(|methodIs\(|requestPath|^$", sc["name"])) and not sc["name"] == ""

        if has_method and not is_helper and not is_mock:
            if not has_status and not has_match:
                findings.append(Finding(path, sc["line"], "A5", "Bloqueante",
                                        f"Escenario '{sc['name'] or '(sin nombre)'}' hace requests sin validar status ni respuesta (no prueba nada)",
                                        "Agregar `Then status <código>` y `And match response == <esquema>` después de cada `method`"))
            elif not has_status:
                findings.append(Finding(path, sc["line"], "A5", "Bloqueante",
                                        f"Escenario '{sc['name'] or '(sin nombre)'}' hace requests sin validar `status`",
                                        "Agregar `Then status <código>` después de cada `method`"))
            elif not has_match and expects_2xx:
                findings.append(Finding(path, sc["line"], "A6", "Mayor",
                                        f"Escenario '{sc['name'] or '(sin nombre)'}' solo valida status, no el cuerpo de la respuesta",
                                        "Agregar `match response == read('schemas/<entidad>.json')` u otra aserción"))
        if not is_helper and any(re.match(r"""^path\s+['"][^'"]*(login|auth|token|oauth)""", t, re.I) for t in texts):
            findings.append(Finding(path, sc["line"], "A3", "Mayor",
                                    f"Escenario '{sc['name'] or '(sin nombre)'}' se autentica por su cuenta",
                                    "Obtener el token una vez por suite con karate.callSingle en karate-config.js "
                                    "(salvo que el escenario pruebe el propio login)"))
        if not is_helper and not is_mock and not sc["steps"] == []:
            name = re.sub(r"\[[^\]]*\]", "", sc["name"]).strip()
            name = re.sub(r"<[^>]+>|\$\{[^}]+\}", "x", name)
            if not name or GENERIC_NAME_RE.match(name) or len(name) < 8:
                findings.append(Finding(path, sc["line"], "A16", "Menor",
                                        f"Nombre de escenario poco descriptivo: '{sc['name']}'",
                                        "Describir el comportamiento esperado e incluir ID: [HU-x][CA-y] rechaza ..."))
        if len(sc["steps"]) > max_pasos and not is_ui:
            findings.append(Finding(path, sc["line"], "A20", "Menor",
                                    f"Escenario con {len(sc['steps'])} pasos (> {max_pasos})",
                                    "Dividir por comportamiento o extraer helpers con call read()"))

    # ---------- reglas por archivo ----------
    if linea == "v2":
        for i, raw in enumerate(lines, start=1):
            if "@parallel=false" in raw and not raw.strip().startswith("#"):
                findings.append(Finding(path, i, "A12", "Mayor", "@parallel=false se ignora en silencio en Karate v2",
                                        "Reemplazar por @lock=<nombre> (o @lock=* para exclusión total)"))

    if "@ignore" not in feature_tags and path.resolve() in CALLED_FILES and executable_count(scenarios) > 0:
        findings.append(Finding(path, 1, "A13", "Menor",
                                "Feature invocada con call/callonce desde otra feature pero sin @ignore: también se ejecuta sola en la suite",
                                "Si es solo un helper, agregar @ignore antes de `Feature:`; si además es una prueba en sí misma, ignorar este aviso"))
    elif "@ignore" not in feature_tags and any("__arg" in t for sc in scenarios for _, t in sc["steps"]):
        findings.append(Finding(path, 1, "A13", "Mayor",
                                "Usa __arg (espera ser llamada) pero no tiene @ignore",
                                "Agregar @ignore en la línea anterior a `Feature:`"))
    return findings


CALLED_FILES = set()
CALL_RE = re.compile(r"""(?:call|callonce|callSingle\(|karate\.call\()\s*\(?\s*(?:read\()?\s*['"]([^'"@][^'"]*\.feature)['"]""")


def executable_count(scenarios):
    return sum(1 for sc in scenarios if not sc["bg"])


def collect_calls(files, roots):
    """Localiza archivos .feature referenciados con call read('...') para comprobar la regla A13."""
    for f in files:
        for m in CALL_RE.finditer(f.read_text(encoding="utf-8", errors="replace")):
            ref = m.group(1)
            if ref.startswith("classpath:"):
                rel = ref[len("classpath:"):]
                for r in roots:
                    for cand in r.rglob(Path(rel).name):
                        if str(cand).replace("\\", "/").endswith(rel):
                            CALLED_FILES.add(cand.resolve())
            else:
                ref = ref.replace("this:", "")
                CALLED_FILES.add((f.parent / ref).resolve())


def check_secret(findings, path, ln, text):
    m = SECRET_RE.search(text)
    if m and not re.search(r"#\(|karate\.|java\.lang\.System|properties\[", m.group(0)):
        findings.append(Finding(path, ln, "A2", "Bloqueante", f"Posible secreto en texto plano ({m.group(1)})",
                                "Leer de variable de entorno o -D en karate-config.js; rotar la credencial si ya se publicó"))
    elif BEARER_LITERAL_RE.search(text):
        findings.append(Finding(path, ln, "A2", "Bloqueante", "Token Bearer literal en la feature",
                                "Obtener el token con karate.callSingle en karate-config.js"))


def main():
    # Usa UTF-8 para conservar los acentos y símbolos del reporte en Windows.
    # La salida cp1252 puede fallar al imprimir caracteres como → o ✅.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rutas", nargs="+")
    ap.add_argument("--linea", choices=["v1", "v2", "auto"], default="auto",
                    help="línea de Karate; auto la detecta por pom.xml/build.gradle cercano")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-pasos", type=int, default=40)
    args = ap.parse_args()

    files = []
    for r in args.rutas:
        p = Path(r)
        if p.is_dir():
            files += sorted(p.rglob("*.feature"))
        elif p.suffix == ".feature":
            files.append(p)
    if not files:
        sys.exit("no se encontraron archivos .feature")

    linea = args.linea if args.linea != "auto" else detect_line(files[0])
    collect_calls(files, [Path(r) for r in args.rutas if Path(r).is_dir()] or [files[0].parent])
    findings = []
    for f in files:
        findings += lint_file(f, linea, args.max_pasos)
    findings.sort(key=lambda x: (SEV_ORDER[x.sev], x.file, x.line))

    if args.json:
        print(json.dumps({"linea": linea, "archivos": len(files), "hallazgos": [f.as_dict() for f in findings]},
                         ensure_ascii=False, indent=2))
    else:
        counts = {s: sum(1 for f in findings if f.sev == s) for s in SEV_ORDER}
        print(f"Karate lint — línea {linea} — {len(files)} archivo(s): "
              f"{counts['Bloqueante']} bloqueantes, {counts['Mayor']} mayores, {counts['Menor']} menores\n")
        for f in findings:
            print(f"[{f.sev}] {f.rule} {f.file}:{f.line} — {f.msg}\n    → {f.fix}")
    sys.exit(1 if any(f.sev == "Bloqueante" for f in findings) else 0)


def detect_line(start: Path) -> str:
    for d in [start.resolve().parent, *start.resolve().parents]:
        for name in ("pom.xml", "build.gradle", "build.gradle.kts"):
            b = d / name
            if b.exists():
                t = b.read_text(encoding="utf-8", errors="replace")
                if "karate-junit6" in t or re.search(r"karate[.\-]version[^0-9]*2\.", t):
                    return "v2"
                if "karate-junit5" in t or "karate-core" in t:
                    return "v1"
        if (d / "karate-pom.json").exists() or (d / "karate-boot.js").exists():
            return "v2"
    return "v2"


if __name__ == "__main__":
    main()
