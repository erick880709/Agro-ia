#!/usr/bin/env python3
"""Detecta si un repositorio usa SonarQube/SonarCloud y cómo.

Busca señales en archivos del proyecto (sonar-project.properties, plugins de
Gradle/Maven, scanners de npm, tareas de Azure Pipelines, GitHub Actions,
Jenkins y GitLab), extrae la clave de proyecto, el servidor u organización,
los reportes de cobertura que se publican a Sonar, umbrales locales de
cobertura y si ya hay un servidor MCP de SonarQube configurado.

Las señales indican que el proyecto *publica* análisis en Sonar; no prueban
que exista un análisis vigente para la revisión que se va a revisar.

Uso:
    python sonar_detect.py <repo> [--json]

Solo biblioteca estándar. No lee secretos ni hace llamadas de red.
Código de salida: 0 si el repo se pudo leer (detectado o no); 2 si la ruta no existe.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP = {".git", "node_modules", "build", "target", "dist", ".gradle", "vendor", ".venv", "venv",
        "__pycache__", ".idea", "out", "coverage", ".next"}
MAX_BYTES = 512_000

PROP = re.compile(r"^\s*(sonar\.[\w.]+)\s*[=:]\s*(.+?)\s*$", re.M)
GRADLE_PROP = re.compile(r"""property\s*\(?\s*["'](sonar\.[\w.]+)["']\s*,\s*["']([^"']+)["']""")
POM_PROP = re.compile(r"<(sonar\.[\w.]+)>([^<]+)</sonar\.[\w.]+>")
COVERAGE_KEYS = ("sonar.coverage.jacoco.xmlReportPaths", "sonar.javascript.lcov.reportPaths",
                 "sonar.typescript.lcov.reportPaths", "sonar.go.coverage.reportPaths",
                 "sonar.python.coverage.reportPaths", "sonar.cs.opencover.reportsPaths",
                 "sonar.cs.vscoveragexml.reportsPaths", "sonar.coverageReportPaths")

SIGNALS = [
    # (kind, regex, descripción, patrón de archivo)
    ("gradle-plugin", re.compile(r"""org\.sonarqube|id\s*\(?\s*["']org\.sonarqube"""), "Plugin Gradle org.sonarqube",
     re.compile(r"(^|/)(build|main|settings)\.gradle(\.kts)?$")),
    ("gradle-block", re.compile(r"^\s*(sonar|sonarqube)\s*\{", re.M), "Bloque sonar { } en Gradle",
     re.compile(r"\.gradle(\.kts)?$")),
    ("maven-plugin", re.compile(r"sonar-maven-plugin|<sonar\.projectKey>"), "Plugin o propiedades Sonar en Maven",
     re.compile(r"(^|/)pom\.xml$")),
    ("npm-scanner", re.compile(r"""["'](sonarqube-scanner|sonar-scanner|@sonar/scan)["']"""), "Scanner de Sonar en npm",
     re.compile(r"(^|/)package\.json$")),
    ("azure-pipelines", re.compile(r"(SonarQube|SonarCloud)(Prepare|Analyze|Publish)@\d|sonar-?buildbreaker", re.I),
     "Tareas Sonar en Azure Pipelines", re.compile(r"(azure-pipelines|pipeline|\.azure|\.pipelines).*\.ya?ml$|\.ya?ml$", re.I)),
    ("github-actions", re.compile(r"sonarsource/(sonarqube-scan-action|sonarcloud-github-action|sonarqube-quality-gate-action)", re.I),
     "Acción de Sonar en GitHub Actions", re.compile(r"(^|/)\.github/workflows/.*\.ya?ml$")),
    ("jenkins", re.compile(r"withSonarQubeEnv|waitForQualityGate"), "Sonar en Jenkinsfile", re.compile(r"(^|/)Jenkinsfile")),
    ("gitlab", re.compile(r"sonar-scanner|sonarsource/sonar-scanner-cli", re.I), "Sonar en GitLab CI",
     re.compile(r"(^|/)\.gitlab-ci\.ya?ml$")),
    ("dotnet-scanner", re.compile(r"dotnet-sonarscanner|SonarScanner\.MSBuild", re.I), "SonarScanner for .NET",
     re.compile(r"\.(ya?ml|sh|ps1|cmd|csproj)$|(^|/)Dockerfile", re.I)),
]
JACOCO_MIN = re.compile(r"minimum\s*=\s*(?:new\s+BigDecimal\()?\s*['\"]?(0?\.\d+|1(?:\.0+)?)", re.I)
JEST_THRESHOLD = re.compile(r"coverageThreshold", re.I)


def iter_files(root: Path):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for p in entries:
            if p.is_symlink():
                continue
            if p.is_dir():
                if p.name not in SKIP:
                    stack.append(p)
            elif p.is_file():
                yield p


def read(p: Path) -> str:
    try:
        if p.stat().st_size > MAX_BYTES:
            return ""
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect(root: Path) -> dict:
    out = {"detected": False, "signals": [], "projectKey": None, "hostUrl": None, "organization": None,
           "coverageReports": [], "localThresholds": [], "mcpConfigured": False, "properties": {}}
    props: dict[str, str] = {}
    for p in iter_files(root):
        rel = p.relative_to(root).as_posix()
        name = p.name
        if name in ("sonar-project.properties", ".sonarcloud.properties"):
            text = read(p)
            out["signals"].append({"file": rel, "kind": "properties", "detail": name})
            for k, v in PROP.findall(text):
                props.setdefault(k, v)
            continue
        if name in (".mcp.json", "mcp.json", "mcp_config.json") or rel.endswith(".vscode/mcp.json"):
            if re.search(r"sonarqube-mcp|sonarsource/sonarqube|\"sonarqube\"|sonar run mcp", read(p), re.I):
                out["mcpConfigured"] = True
                out["signals"].append({"file": rel, "kind": "mcp", "detail": "Servidor MCP de SonarQube configurado"})
            continue
        if not re.search(r"\.(gradle|kts|xml|json|ya?ml|properties|sh|ps1|cmd|csproj|js|cjs|mjs|ts)$|Jenkinsfile|Dockerfile", name):
            continue
        text = None
        for kind, rx, desc, file_rx in SIGNALS:
            if not file_rx.search(rel):
                continue
            text = read(p) if text is None else text
            if rx.search(text):
                out["signals"].append({"file": rel, "kind": kind, "detail": desc})
        if text is None:
            text = read(p) if re.search(r"\.(gradle|kts|xml|json|js|cjs|mjs|ts)$", name) else ""
        if name.endswith((".gradle", ".gradle.kts")):
            for k, v in GRADLE_PROP.findall(text):
                props.setdefault(k, v)
            if "jacoco" in text.lower():
                for m in JACOCO_MIN.findall(text):
                    val = float(m)
                    out["localThresholds"].append({"file": rel, "tool": "jacoco", "minimum": round(val * 100 if val <= 1 else val, 2)})
        elif name == "pom.xml":
            for k, v in POM_PROP.findall(text):
                props.setdefault(k, v.strip())
        elif re.search(r"(jest|vitest|karma)\.config\.|package\.json$", name) and JEST_THRESHOLD.search(text):
            out["localThresholds"].append({"file": rel, "tool": "js", "minimum": None})
    out["properties"] = props
    out["projectKey"] = props.get("sonar.projectKey")
    out["hostUrl"] = props.get("sonar.host.url")
    out["organization"] = props.get("sonar.organization")
    out["coverageReports"] = [{"key": k, "paths": props[k]} for k in COVERAGE_KEYS if k in props]
    out["detected"] = any(s["kind"] != "mcp" for s in out["signals"])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.repo)
    if not root.is_dir():
        print(f"No existe el directorio: {root}", file=sys.stderr)
        return 2
    r = detect(root)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    print(f"Sonar detectado: {'sí' if r['detected'] else 'no'} · MCP configurado: {'sí' if r['mcpConfigured'] else 'no'}")
    for k in ("projectKey", "hostUrl", "organization"):
        if r[k]:
            print(f"  {k}: {r[k]}")
    for s in r["signals"]:
        print(f"  - [{s['kind']}] {s['file']}: {s['detail']}")
    for c in r["coverageReports"]:
        print(f"  cobertura → {c['key']} = {c['paths']}")
    for t in r["localThresholds"]:
        print(f"  umbral local ({t['tool']}) en {t['file']}: {t['minimum'] if t['minimum'] is not None else 'definido'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
