#!/usr/bin/env python3
"""Pre-chequeo heurístico de reglas del Scaffold Clean Architecture (Bancolombia).

Detecta, sin compilar, violaciones probables de:
  DEP-1  model sin dependencias de proyecto ni externas no whitelisted
  DEP-2  usecase depende únicamente de :model
  DEP-3  infraestructura no depende de :app-service
  DEP-4  imports de infraestructura/frameworks en model o usecase
  DEP-5  anotaciones de persistencia en model
  MAIN   `public static void main` fuera de app-service
  R2.2   sufijos prohibidos en clases de dominio (dto, request, response)
  R2.4   nombres de tecnología en clases de dominio
  R2.7f  nombres de tecnología en campos de dominio
  R2.5   atributos no final en use cases
  R2.7b  beans con atributos no final / @Value o @Autowired en campo
  R1.5   clientes AWS síncronos en proyecto reactivo
  RX     bloqueo (.block, Thread.sleep) en código de producción reactivo
  SKIP   arch.unit.skip=true

NO sustituye `./gradlew validateStructure` ni `ArchitectureTest`, que son la
fuente autoritativa. Úsalo como pista y verifica cada hallazgo.

Uso:
    python scaffold_check.py <repo> [--json] [--base main] [--changed-list archivos.txt]

Con --base o --changed-list, los hallazgos en archivos no cambiados se marcan
preexistente=true y no afectan el código de salida.

Salida: 0 sin hallazgos en alcance, 1 con hallazgos, 2 error o no es scaffold
(usa --force para analizar igualmente).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict

DEFAULT_SUFFIXES = ["dto", "request", "response"]
DEFAULT_TECH = ["rabbit", "sqs", "sns", "ibm", "dynamo", "aws", "mysql", "postgres", "redis", "mongo",
                "rsocket", "r2dbc", "http", "kms", "s3", "graphql", "kafka"]
INFRA_IMPORTS = ["org.springframework", "jakarta.persistence", "javax.persistence", "software.amazon",
                 "jakarta.servlet", "javax.servlet", "org.apache.kafka", "com.rabbitmq", "java.sql",
                 "org.hibernate", "com.mongodb", "io.r2dbc", "jakarta.jms", "javax.jms", "com.ibm.mq"]
PERSISTENCE_ANN = re.compile(r"@(Entity|Table|Document|DynamoDbBean|Column|Id\b|GeneratedValue|MappedSuperclass)\b")
BEAN_ANN = re.compile(r"@(Component|Service|Repository|Configuration|RestController|Controller)\b")
SYNC_AWS = re.compile(r"\b(S3Client|KmsClient|DynamoDbClient|SqsClient|SnsClient|SecretsManagerClient|CognitoIdentityProviderClient|SesClient|LambdaClient)\b")
BLOCKING = re.compile(r"\.(block|blockFirst|blockLast)\s*\(|\.toFuture\(\)\s*\.get\(|Thread\.sleep\(")
PROJECT_DEP = re.compile(r"^\s*(implementation|api|compileOnly|runtimeOnly|compile)\s*\(?\s*project\(\s*['\"]:([\w\-.]+)['\"]\s*\)", re.M)
EXTERNAL_DEP = re.compile(r"^\s*(implementation|api|compile)\s*\(?\s*(platform\()?\s*['\"]([\w.\-]+):([\w.\-]+)(:[^'\"]*)?['\"]", re.M)
SKIP_DIRS = {"build", ".gradle", ".git", "node_modules", "out", "bin", ".idea"}


@dataclass
class Finding:
    rule: str
    severidad: str
    archivo: str
    linea: int | None
    mensaje: str
    preexistente: bool = False


# ---------------------------------------------------------------- utilidades

def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def walk(root: str, suffix: str):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith(suffix):
                yield os.path.join(d, f)


def load_props(root: str) -> dict[str, str]:
    p = os.path.join(root, "gradle.properties")
    props: dict[str, str] = {}
    if os.path.isfile(p):
        for line in read(p).splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()
    return props


def whitelist(root: str) -> list[str]:
    out: list[str] = []
    for name in ("build.gradle", "main.gradle", "build.gradle.kts"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            m = re.search(r"whitelistedDependencies\s*=\s*['\"]([^'\"]*)['\"]", read(p))
            if m:
                out += [x.strip() for x in m.group(1).split(",") if x.strip()]
    return out


def is_scaffold(root: str, props: dict[str, str]) -> bool:
    has_dirs = os.path.isdir(os.path.join(root, "domain", "model")) and os.path.isdir(os.path.join(root, "domain", "usecase"))
    has_app = os.path.isdir(os.path.join(root, "applications", "app-service"))
    return has_dirs and (has_app or "package" in props)


def module_kind(relpath: str) -> str:
    if relpath.startswith("domain/model/"):
        return "model"
    if relpath.startswith("domain/usecase/"):
        return "usecase"
    if relpath.startswith("applications/app-service/"):
        return "app"
    if relpath.startswith("infrastructure/"):
        return "infra"
    return "otro"


def is_main_source(relpath: str) -> bool:
    return "/src/main/" in relpath


def strip_comments_and_strings(src: str) -> str:
    """Reemplaza comentarios y contenido de strings por espacios conservando saltos de línea."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            while i < n and src[i] != "\n":
                out.append(" "); i += 1
        elif c == "/" and nxt == "*":
            while i < n and not (src[i] == "*" and i + 1 < n and src[i + 1] == "/"):
                out.append("\n" if src[i] == "\n" else " "); i += 1
            out.append("  "); i += 2
        elif c == '"' and src[i:i + 3] == '"""':
            out.append('"""'); i += 3
            while i < n and src[i:i + 3] != '"""':
                out.append("\n" if src[i] == "\n" else " "); i += 1
            out.append('"""'); i += 3
        elif c in ('"', "'"):
            q = c; out.append(q); i += 1
            while i < n and src[i] != q:
                if src[i] == "\\":
                    out.append(" "); i += 1
                out.append("\n" if i < n and src[i] == "\n" else " "); i += 1
            out.append(q); i += 1
        else:
            out.append(c); i += 1
    return "".join(out)


ANNOT = re.compile(r"@[\w.]+(\s*\([^()]*(\([^()]*\)[^()]*)*\))?")
DECL = re.compile(r"\b(class|interface|record|enum)\s+([A-Za-z_]\w*)")


def java_structure(src: str):
    """Devuelve (clases, campos) del archivo.

    clases: [(nombre, tipo, linea, anotaciones_previas)]
    campos: [(clase, nombre, linea, modificadores:set, anotaciones:str)] solo de clases (no interfaces/enums/records).
    """
    clean = strip_comments_and_strings(src)
    classes = []
    fields = []
    stack: list[tuple[str, str]] = []  # (nombre, tipo) por nivel de llave de tipo
    depth_kinds: list[str] = []        # 'type' o 'block' por cada '{'
    buf: list[str] = []
    buf_line = 1
    line = 1
    paren = 0
    pending_type: tuple[str, str, int] | None = None
    i = 0
    n = len(clean)
    while i < n:
        c = clean[i]
        if c == "\n":
            line += 1
        if c == "(":
            paren += 1
        elif c == ")":
            paren = max(0, paren - 1)
        if paren == 0 and c == "{":
            text = "".join(buf)
            m = None
            for m in DECL.finditer(text):
                pass
            if m and not re.search(r"\bnew\s+\w", text[m.start():]) and (not depth_kinds or depth_kinds[-1] == "type"):
                kind, name = m.group(1), m.group(2)
                ann = " ".join(a.group(0) for a in ANNOT.finditer(text[:m.start()]))
                decl_line = buf_line + text[:m.start()].count("\n")
                classes.append((name, kind, decl_line, ann))
                stack.append((name, kind))
                depth_kinds.append("type")
            else:
                depth_kinds.append("block")
            buf = []; buf_line = line
        elif paren == 0 and c == "}":
            if depth_kinds:
                k = depth_kinds.pop()
                if k == "type" and stack:
                    stack.pop()
            buf = []; buf_line = line
        elif paren == 0 and c == ";":
            text = "".join(buf)
            if depth_kinds and depth_kinds[-1] == "type" and stack and stack[-1][1] == "class":
                anns = " ".join(a.group(0) for a in ANNOT.finditer(text))
                body = ANNOT.sub(" ", text)
                lhs = body.split("=", 1)[0]
                if "(" not in lhs and lhs.strip() and not re.match(r"^\s*(package|import|return|throw)\b", lhs):
                    toks = re.findall(r"[A-Za-z_]\w*", lhs)
                    mods = {t for t in toks if t in ("final", "static", "private", "protected", "public", "transient", "volatile")}
                    rest = [t for t in toks if t not in mods]
                    if len(rest) >= 2:
                        first_nonblank = len(text) - len(text.lstrip())
                        fline = buf_line + text[:first_nonblank].count("\n")
                        # localizar la línea del nombre del campo
                        name = rest[-1]
                        idx = text.find(name, len(text) - len(text.lstrip()))
                        if idx >= 0:
                            fline = buf_line + text[:idx].count("\n")
                        fields.append((stack[-1][0], name, fline, mods, anns))
            buf = []; buf_line = line
        else:
            if not buf and c in " \t\n\r":
                buf_line = line if c != "\n" else line
            else:
                if not buf:
                    buf_line = line
                buf.append(c)
        i += 1
    return classes, fields


def line_of(src: str, idx: int) -> int:
    return src.count("\n", 0, idx) + 1


# ---------------------------------------------------------------- reglas

def check_gradle(root: str, wl: list[str], findings: list[Finding]):
    for path in walk(root, ".gradle"):
        r = rel(root, path)
        if not r.endswith("build.gradle"):
            continue
        kind = module_kind(r)
        if kind == "otro":
            continue
        txt = read(path)
        for m in PROJECT_DEP.finditer(txt):
            dep = m.group(2)
            ln = line_of(txt, m.start())
            if kind == "model":
                findings.append(Finding("DEP-1", "bloqueante", r, ln, f"model no debe depender de ningún módulo (depende de :{dep})"))
            elif kind == "usecase" and dep != "model":
                findings.append(Finding("DEP-2", "bloqueante", r, ln, f"usecase solo puede depender de :model (depende de :{dep})"))
            elif kind == "infra" and dep == "app-service":
                findings.append(Finding("DEP-3", "bloqueante", r, ln, "infraestructura no debe depender de :app-service"))
        if kind in ("model", "usecase"):
            for m in EXTERNAL_DEP.finditer(txt):
                artifact = m.group(4)
                coord = f"{m.group(3)}:{artifact}"
                if any(w and (w == artifact or w == coord or w in coord) for w in wl):
                    continue
                ln = line_of(txt, m.start())
                rule = "DEP-1" if kind == "model" else "DEP-2"
                findings.append(Finding(rule, "bloqueante", r, ln,
                                        f"{kind} declara dependencia externa {coord}; validateStructure la rechazará salvo whitelist"))


def check_java(root: str, reactive: bool, suffixes: list[str], tech: list[str], findings: list[Finding]):
    for path in walk(root, ".java"):
        r = rel(root, path)
        kind = module_kind(r)
        if kind == "otro" or not is_main_source(r):
            continue
        src = read(path)
        clean = strip_comments_and_strings(src)
        classes, fields = java_structure(src)
        class_kind = {name: k for name, k, _, _ in classes}
        class_ann = {name: a for name, _, _, a in classes}

        if kind in ("model", "usecase"):
            for m in re.finditer(r"^\s*import\s+(static\s+)?([\w.]+)", clean, re.M):
                imp = m.group(2)
                if any(imp.startswith(p) for p in INFRA_IMPORTS):
                    findings.append(Finding("DEP-4", "bloqueante", r, line_of(clean, m.start()),
                                            f"{kind} importa {imp}: dependencia de infraestructura en el dominio"))
            for name, k, ln, _ in classes:
                low = name.lower()
                for s in suffixes:
                    if low.endswith(s):
                        findings.append(Finding("R2.2", "bloqueante", r, ln, f"Clase de dominio '{name}' con sufijo técnico '{s}'"))
                        break
                for t in tech:
                    if t in low:
                        findings.append(Finding("R2.4", "bloqueante", r, ln, f"Clase de dominio '{name}' contiene nombre de tecnología '{t}'"))
                        break
            for cls, fname, ln, mods, anns in fields:
                low = fname.lower()
                for t in tech:
                    if t in low:
                        findings.append(Finding("R2.7f", "bloqueante", r, ln, f"Campo de dominio '{cls}.{fname}' contiene nombre de tecnología '{t}'"))
                        break
        if kind == "model":
            for m in PERSISTENCE_ANN.finditer(clean):
                findings.append(Finding("DEP-5", "bloqueante", r, line_of(clean, m.start()),
                                        f"Anotación de persistencia {m.group(0)} en model: va en el driven adapter"))
        if kind == "usecase":
            for cls, fname, ln, mods, anns in fields:
                if class_kind.get(cls) == "class" and "final" not in mods:
                    findings.append(Finding("R2.5", "bloqueante", r, ln, f"Use case '{cls}' con atributo no final '{fname}' (estado mutable compartido)"))
        if kind in ("infra", "app"):
            for cls, fname, ln, mods, anns in fields:
                if "@Value(" in anns.replace(" ", "") or re.search(r"@Value\s*\(", anns):
                    findings.append(Finding("R2.7b", "bloqueante", r, ln, f"@Value en campo '{cls}.{fname}': inyectar por constructor con campo final"))
                elif "@Autowired" in anns:
                    findings.append(Finding("R2.7b", "bloqueante", r, ln, f"@Autowired en campo '{cls}.{fname}': usar inyección por constructor"))
                elif BEAN_ANN.search(class_ann.get(cls, "")) and "final" not in mods and "static" not in mods:
                    findings.append(Finding("R2.7b", "bloqueante", r, ln, f"Bean '{cls}' con atributo no final '{fname}'"))
        if kind != "app":
            m = re.search(r"public\s+static\s+void\s+main\s*\(", clean)
            if m:
                findings.append(Finding("MAIN", "mayor", r, line_of(clean, m.start()), "Solo app-service debe tener método main"))
        if reactive:
            for m in SYNC_AWS.finditer(clean):
                findings.append(Finding("R1.5", "mayor", r, line_of(clean, m.start()),
                                        f"Cliente AWS síncrono {m.group(1)} en proyecto reactivo: usar *AsyncClient con Mono.fromFuture"))
            for m in BLOCKING.finditer(clean):
                findings.append(Finding("RX", "mayor", r, line_of(clean, m.start()),
                                        f"Operación bloqueante '{m.group(0).strip()}' en código de producción reactivo"))


def changed_files(root: str, base: str | None, listfile: str | None) -> set[str] | None:
    if listfile:
        return {l.strip().replace("\\", "/") for l in read(listfile).splitlines() if l.strip()}
    if base:
        try:
            out = subprocess.run(["git", "-C", root, "diff", "--name-only", f"{base}...HEAD"], capture_output=True, text=True, check=True).stdout
            out2 = subprocess.run(["git", "-C", root, "diff", "--name-only", "HEAD"], capture_output=True, text=True, check=True).stdout
            out3 = subprocess.run(["git", "-C", root, "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True, check=True).stdout
            return {l.strip() for l in (out + out2 + out3).splitlines() if l.strip()}
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise SystemExit(f"No se pudo obtener archivos cambiados con git: {exc}")
    return None


def run(root: str, force: bool = False, base: str | None = None, listfile: str | None = None) -> dict:
    props = load_props(root)
    if not is_scaffold(root, props) and not force:
        return {"scaffold": False, "hallazgos": [], "error": "No parece un proyecto Scaffold Clean Architecture (usa --force)"}
    reactive = props.get("reactive", "").lower() == "true"
    suffixes = [s.strip().lower() for s in props.get("arch.unit.forbiddenDomainSuffixes", ",".join(DEFAULT_SUFFIXES)).split(",") if s.strip()]
    tech = [s.strip().lower() for s in props.get("arch.unit.forbiddenDomainClassNames", ",".join(DEFAULT_TECH)).split(",") if s.strip()]
    findings: list[Finding] = []
    if props.get("arch.unit.skip", "").lower() == "true":
        gp = read(os.path.join(root, "gradle.properties"))
        idx = gp.find("arch.unit.skip")
        findings.append(Finding("SKIP", "bloqueante", "gradle.properties", line_of(gp, idx), "arch.unit.skip=true desactiva todas las reglas ArchUnit"))
    check_gradle(root, whitelist(root), findings)
    check_java(root, reactive, suffixes, tech, findings)
    scope = changed_files(root, base, listfile)
    if scope is not None:
        for f in findings:
            f.preexistente = f.archivo not in scope
    findings.sort(key=lambda f: (f.preexistente, {"bloqueante": 0, "mayor": 1, "menor": 2}.get(f.severidad, 3), f.archivo, f.linea or 0))
    return {
        "scaffold": True,
        "reactive": reactive,
        "package": props.get("package"),
        "hallazgos": [asdict(f) for f in findings],
        "nota": "Pre-chequeo heurístico. Confirmar con ./gradlew validateStructure y ArchitectureTest.",
    }


def to_markdown(res: dict) -> str:
    if not res.get("scaffold"):
        return f"# Scaffold check\n\n{res.get('error')}"
    out = ["# Scaffold check", "",
           f"- Paquete: `{res.get('package')}` · reactivo: {res.get('reactive')}",
           f"- Hallazgos: {len([h for h in res['hallazgos'] if not h['preexistente']])} en alcance, "
           f"{len([h for h in res['hallazgos'] if h['preexistente']])} preexistentes", ""]
    if not res["hallazgos"]:
        out.append("Sin hallazgos heurísticos.")
    else:
        out += ["| Regla | Severidad | Archivo:línea | Mensaje | Alcance |", "|---|---|---|---|---|"]
        for h in res["hallazgos"]:
            out.append(f"| {h['rule']} | {h['severidad']} | `{h['archivo']}:{h['linea']}` | {h['mensaje']} | {'preexistente' if h['preexistente'] else 'cambio'} |")
    out += ["", f"_{res['nota']}_"]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--force", action="store_true", help="Analizar aunque no se detecte el scaffold")
    ap.add_argument("--base", help="Rama/sha base para marcar preexistentes vía git")
    ap.add_argument("--changed-list", help="Archivo con rutas cambiadas (una por línea, relativas al repo)")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.repo):
        print(f"No existe el directorio {args.repo}", file=sys.stderr)
        return 2
    res = run(os.path.abspath(args.repo), args.force, args.base, args.changed_list)
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else to_markdown(res))
    if not res.get("scaffold"):
        return 2
    return 1 if any(not h["preexistente"] for h in res["hallazgos"]) else 0


if __name__ == "__main__":
    sys.exit(main())
