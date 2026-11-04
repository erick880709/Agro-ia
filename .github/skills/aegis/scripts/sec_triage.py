#!/usr/bin/env python3
"""Triage de seguridad determinista para Aegis.

Detecta stacks, recorre los archivos (o solo los cambiados frente a una rama base) y
emite SEÑALES candidatas por categoría más un plan de herramientas. Las señales son
pistas para el análisis manual: NO son hallazgos. Los valores que parecen secretos se
enmascaran siempre (primeros/últimos 4 caracteres).

Uso:
    python sec_triage.py <repo> [--base origin/main] [--json salida.json] [--max-signals 400]

Solo biblioteca estándar. No ejecuta código del repositorio analizado.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "vendor", "third_party", "dist", "build", "target", "out",
    ".gradle", ".idea", ".terragrunt-cache", ".terraform", ".terragrunt-stack",
    "__pycache__", ".venv", "venv", ".angular", "coverage",
}
TEXT_EXT = {
    ".java", ".kt", ".go", ".ts", ".js", ".mjs", ".cjs", ".html", ".py", ".yaml", ".yml",
    ".properties", ".json", ".tf", ".hcl", ".xml", ".gradle", ".kts", ".env", ".sh",
    ".ps1", ".toml", ".md", ".sql", ".conf", ".ini",
}
TEXT_NAMES = {"Dockerfile", "Containerfile", "Jenkinsfile", ".env", "Makefile", "go.mod", "go.work"}
MAX_FILE_BYTES = 1_500_000
TEST_PATH = re.compile(
    r"(^|/)(src/test|tests?|__tests__|spec|testdata|fixtures|__mocks__)(/|$)"
    r"|_test\.go$|\.spec\.ts$|\.test\.[jt]sx?$|Test\.java$|Tests\.java$|IT\.java$"
)

# --- Secretos (alta confianza por prefijo). El valor se enmascara. -------------------
SECRET_PATTERNS = [
    ("aws-access-key", re.compile(r"\b((?:AKIA|ASIA)[A-Z0-9]{16})\b")),
    ("github-token", re.compile(r"\b((?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,})\b")),
    ("slack-token", re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,})\b")),
    ("google-api-key", re.compile(r"\b(AIza[A-Za-z0-9_\-]{35})\b")),
    ("stripe-live", re.compile(r"\b((?:sk|rk)_live_[A-Za-z0-9]{20,})\b")),
    ("anthropic-key", re.compile(r"\b(sk-ant-[A-Za-z0-9_\-]{40,})\b")),
    ("openai-key", re.compile(r"\b(sk-(?:proj-)?[A-Za-z0-9_\-]{32,})\b")),
    ("private-key", re.compile(r"(-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----)")),
    ("azure-conn-string", re.compile(r"(AccountKey=[A-Za-z0-9+/=]{40,})")),
    ("jdbc-password", re.compile(r"(?i)(jdbc:[a-z0-9]+://[^\s\"']*password=[^&\s\"';]{4,})")),
    ("generic-assignment", re.compile(
        r"(?i)\b(?:password|passwd|pwd|secret|client_secret|api[_-]?key|access[_-]?key|token)\b"
        r"\s*[:=]\s*[\"']([^\"'\s${}<>]{8,})[\"']")),
]
PLACEHOLDER = re.compile(r"(?i)(changeme|example|dummy|placeholder|your[_-]|xxx+|<.+>|\*{3,}|test|fake|sample|redacted|^__.*__$)")


def mask(value: str) -> str:
    v = value.strip()
    if len(v) <= 10:
        return v[:2] + "…" + "*" * 4
    return f"{v[:4]}…{v[-4:]}"


@dataclass
class Rule:
    id: str
    category: str
    pattern: re.Pattern
    hint: str
    exts: tuple[str, ...] = ()
    names: tuple[str, ...] = ()


def R(id_, cat, rx, hint, exts=(), names=(), flags=0):
    return Rule(id_, cat, re.compile(rx, flags), hint, tuple(exts), tuple(names))


JAVA = (".java", ".kt")
GO = (".go",)
TS = (".ts", ".js", ".mjs", ".html")
CONF = (".yaml", ".yml", ".properties")
IAC = (".tf", ".hcl")
WF = (".yml", ".yaml")

RULES: list[Rule] = [
    # Java / Spring
    R("java.permitall-broad", "authz", r"(pathMatchers|requestMatchers|antMatchers)\([^)]*\"/\*\*\"[^)]*\)\s*\.permitAll|anyExchange\(\)\s*\.permitAll|anyRequest\(\)\s*\.permitAll",
      "Regla de permitAll amplia: confirma qué rutas quedan sin autenticación", JAVA),
    R("java.csrf-disabled", "config", r"csrf\(\s*(?:AbstractHttpConfigurer::disable|c\s*->\s*c\.disable\(\)|ServerHttpSecurity\.CsrfSpec::disable)|\.csrf\(\)\s*\.disable\(\)",
      "CSRF deshabilitado: aceptable solo en API stateless sin cookies de sesión", JAVA),
    R("java.sql-concat", "injection", r"(createNativeQuery|createQuery|executeQuery|execute|queryForList|queryForObject|\.sql)\(\s*\"[^\"]*\"\s*\+",
      "Consulta construida por concatenación: verifica parametrización", JAVA),
    R("java.sql-format", "injection", r"String\.format\(\s*\"\s*(SELECT|UPDATE|DELETE|INSERT)", "SQL con String.format", JAVA, flags=re.I),
    R("java.spel-parse", "injection", r"parseExpression\(", "SpEL dinámico: ¿la expresión viene de entrada?", JAVA),
    R("java.runtime-exec", "injection", r"Runtime\.getRuntime\(\)\.exec\(|new ProcessBuilder\(", "Ejecución de comandos del SO", JAVA),
    R("java.deser", "deserialization", r"new ObjectInputStream\(|activateDefaultTyping\(|enableDefaultTyping\(|JsonTypeInfo\.Id\.CLASS",
      "Deserialización potencialmente insegura", JAVA),
    R("java.xxe", "injection", r"DocumentBuilderFactory\.newInstance\(|SAXParserFactory\.newInstance\(|XMLInputFactory\.newInstance\(",
      "Parser XML: verifica que DTD/entidades externas estén deshabilitadas", JAVA),
    R("java.trust-all", "crypto", r"TrustAllCerts|InsecureTrustManagerFactory|X509TrustManager\s*\(\)\s*\{|hostnameVerifier\s*\(\s*\(\s*\w*\s*,\s*\w*\s*\)\s*->\s*true",
      "Verificación TLS deshabilitada", JAVA),
    R("java.weak-hash", "crypto", r"MessageDigest\.getInstance\(\s*\"(MD5|SHA-?1)\"|Cipher\.getInstance\(\s*\"(DES|DESede|[^\"]*ECB)",
      "Algoritmo criptográfico débil", JAVA),
    R("java.insecure-random", "crypto", r"new Random\(|Math\.random\(", "PRNG no criptográfico: ¿se usa para tokens/OTP?", JAVA),
    R("java.lombok-tostring", "logging", r"@Data\b|@ToString\b(?!\.Exclude)", "toString generado: revisa PII/secretos en logs", JAVA),
    R("java.log-object", "logging", r"log(?:ger)?\.(info|debug|warn|error)\([^;]*\{\}[^;]*(request|req|body|dto|entity|token|user)\b",
      "Log de objeto de request/entidad: posible PII", JAVA, flags=re.I),
    R("java.security-context-reactive", "authz", r"SecurityContextHolder\.getContext\(", "SecurityContextHolder en código reactivo devuelve vacío", JAVA),
    R("java.webclient-dynamic", "ssrf", r"WebClient\.create\(\s*[a-z]\w*|\.uri\(\s*[a-z]\w*\s*\)|restTemplate\.\w+\(\s*[a-z]\w*",
      "Cliente HTTP con URL variable: ¿proviene de entrada? (SSRF)", JAVA),
    R("java.mcp-security-off", "agentic", r"enable-security\s*=\s*false|enableSecurity\s*=\s*false|enable-audit\s*=\s*false",
      "MCP del Scaffold sin seguridad/auditoría", JAVA + CONF + (".gradle",)),
    # Configuración Spring
    R("conf.actuator-all", "config", r"exposure\.include\s*[:=]\s*[\"']?\*|^\s*include\s*:\s*[\"']?\*[\"']?\s*$", "Actuator expone todos los endpoints", CONF),
    R("conf.stacktrace", "config", r"include-stacktrace\s*[:=]\s*always|include-message\s*[:=]\s*always", "Errores verbosos al cliente", CONF),
    R("conf.cors-star", "config", r"allowed-origin(s|-patterns)?\s*[:=]\s*[\"']?\*|allowedOrigin(s|Patterns)\(\s*\"\*\"", "CORS comodín", CONF + JAVA),
    # Go
    R("go.insecure-skip-verify", "crypto", r"InsecureSkipVerify\s*:\s*true", "TLS sin verificación", GO),
    R("go.math-rand", "crypto", r"\"math/rand(/v2)?\"", "math/rand importado: ¿se usa para secretos?", GO),
    R("go.sql-sprintf", "injection", r"\.(Query|QueryRow|Exec|QueryContext|ExecContext|Raw|Where)\(\s*(ctx,\s*)?fmt\.Sprintf", "SQL con fmt.Sprintf", GO),
    R("go.exec-shell", "injection", r"exec\.Command(Context)?\([^)]*\"(sh|bash|cmd|powershell)\"", "Comando vía shell", GO),
    R("go.weak-hash", "crypto", r"\"crypto/(md5|sha1|des|rc4)\"", "Primitiva criptográfica débil importada", GO),
    R("go.server-no-timeout", "dos", r"http\.ListenAndServe(TLS)?\(", "Servidor sin timeouts explícitos (Slowloris)", GO),
    R("go.template-html", "xss", r"template\.HTML\(", "template.HTML anula el escape", GO),
    R("go.jwt-unverified", "authn", r"ParseUnverified\(", "JWT parseado sin verificar firma", GO),
    # Angular / TS
    R("ng.bypass-trust", "xss", r"bypassSecurityTrust(Html|Url|ResourceUrl|Script|Style)\(", "Bypass del sanitizador de Angular", TS),
    R("ng.innerhtml-dom", "xss", r"\.innerHTML\s*=|insertAdjacentHTML\(|document\.write\(|setProperty\([^)]*['\"]innerHTML['\"]", "Sink DOM directo", TS),
    R("ng.token-storage", "authn", r"localStorage\.setItem\([^)]*(token|jwt|access|refresh)", "Token en localStorage", TS, flags=re.I),
    R("ts.eval", "injection", r"\beval\(|new Function\(", "Evaluación dinámica de código", TS),
    R("ts.math-random", "crypto", r"Math\.random\(\)", "PRNG no criptográfico", TS),
    R("ng.client-secret", "secrets", r"client_?secret\s*[:=]", "Client secret en código de SPA (cliente público)", TS, flags=re.I),
    # IaC
    R("iac.open-cidr", "network", r"(cidr_blocks|source_address_prefix(es)?|source_ranges|ipv6_cidr_blocks)\s*=\s*[\[\"]*\s*\"(0\.0\.0\.0/0|::/0|\*|Internet)\"",
      "Ingreso abierto a Internet: revisa puertos", IAC),
    R("iac.iam-wildcard", "iam", r"\"Action\"\s*:\s*\"\*\"|actions\s*=\s*\[\s*\"\*\"\s*\]|\"Resource\"\s*:\s*\"\*\"", "IAM con comodín", IAC + (".json",)),
    R("iac.public-acl", "exposure", r"acl\s*=\s*\"public-read(-write)?\"|allow_blob_public_access\s*=\s*true|publicly_accessible\s*=\s*true|\"allUsers\"|\"allAuthenticatedUsers\"",
      "Recurso público", IAC),
    R("iac.encryption-off", "crypto", r"(encrypted|storage_encrypted|enable_encryption|encryption_enabled)\s*=\s*false", "Cifrado deshabilitado", IAC),
    R("iac.unpinned-source", "supply-chain", r"source\s*=\s*\"(?:git::|git@|https?://|github\.com/|bitbucket\.org/)(?![^\"]*\?ref=(?!main\b|master\b|develop\b))[^\"]*\"", "Fuente remota de módulo sin pinear (sin ref o ref a rama)", IAC),
    R("iac.mock-apply", "iac", r"mock_outputs_allowed_terraform_commands\s*=\s*\[[^\]]*\"(apply|destroy)\"", "Mocks permitidos en apply/destroy", IAC),
    R("iac.oidc-wildcard", "iam", r"token\.actions\.githubusercontent\.com:sub[^\n]*repo:[^:\"]+/\*|\"repo:[^\"]*\*\"", "Confianza OIDC con comodín de repo/rama", IAC + (".json",)),
    R("iac.sensitive-output", "secrets", r"output\s+\"[^\"]*(password|secret|token|key)[^\"]*\"", "Output con nombre sensible: ¿sensitive = true?", IAC, flags=re.I),
    # Workflows
    R("wf.pr-target", "cicd", r"pull_request_target", "pull_request_target: ¿se hace checkout/ejecución del código del PR con secretos?", WF),
    R("wf.expr-injection", "cicd", r"\$\{\{\s*github\.event\.(issue\.title|issue\.body|pull_request\.title|pull_request\.body|comment\.body|review\.body|head_commit\.message|pull_request\.head\.ref)|\$\{\{\s*github\.head_ref",
      "Expresión controlada por terceros: peligrosa en run:/prompts", WF),
    R("wf.unpinned-action", "supply-chain", r"uses:\s*(?!\./)(?!docker://)[\w.\-]+/[\w.\-/]+@(?![0-9a-f]{40}\b)[\w.\-]+", "Action sin pinear por SHA", WF),
    R("wf.write-all", "cicd", r"permissions:\s*write-all", "Token con todos los permisos", WF),
    R("wf.agent-unsafe", "agentic", r"dangerously-skip-permissions|danger-full-access|--yolo|Bash\(\*\)|allowed_non_write_users:\s*[\"']?\*",
      "Agente de IA con sandbox/permisos debilitados", WF + (".json",)),
    R("ado.fork-secrets", "cicd", r"persistCredentials:\s*true", "Credenciales persistidas en checkout", WF),
    # Contenedores / K8s
    R("docker.latest", "supply-chain", r"^FROM\s+[^\s@]+(:latest)?\s*($|AS)", "Imagen base sin digest (o con latest): pinear por @sha256 en prod", (), ("Dockerfile", "Containerfile"), re.M | re.I),
    R("docker.curl-sh", "supply-chain", r"curl[^|\n]*\|\s*(ba)?sh|wget[^|\n]*\|\s*(ba)?sh", "Descarga y ejecuta sin verificar", (".sh",), ("Dockerfile", "Containerfile")),
    R("docker.secret-env", "secrets", r"^(ENV|ARG)\s+\w*(PASSWORD|SECRET|TOKEN|API_KEY)\w*", "Secreto en ARG/ENV (queda en capas)", (), ("Dockerfile", "Containerfile"), re.M | re.I),
    R("k8s.privileged", "container", r"privileged:\s*true|hostNetwork:\s*true|hostPID:\s*true|allowPrivilegeEscalation:\s*true", "Pod privilegiado", WF),
    # LLM / agentic en código
    R("llm.output-exec", "agentic", r"(\beval|\bexec|execSync|Runtime\.getRuntime\(\)\.exec|subprocess\.\w+|os\.system)\([^)]*\b(completion|llm\w*|model_?output|ai_?response|choices\[0\]|message\.content|content\[0\]\.text)", "Salida de LLM hacia ejecución", TS + JAVA + GO + (".py",), flags=re.I),
    R("llm.prompt-concat", "agentic", r"(system|prompt)\w*\s*[+:=]+\s*[^;\n]*\+\s*(user|input|request|body|query)\w*", "Prompt construido concatenando entrada", TS + JAVA + GO + (".py",), flags=re.I),
    R("text.hidden-unicode", "agentic", r"[\u200b-\u200f\u2060-\u2064\U000e0000-\U000e007f]", "Unicode invisible (posible instrucción oculta)", (".md", ".yaml", ".yml", ".json", ".txt")),
    R("text.reviewer-injection", "agentic", r"(?i)(ignore (all |previous |prior )?(instructions|rules)|approve this (pr|change|pull request)|as an ai (reviewer|assistant)[^.\n]{0,40}(approve|ignore))",
      "Texto dirigido a un revisor/IA: tratar como dato y reportar"),
]

TOOL_PLAN = {
    "java": [("semgrep", "semgrep scan --config p/security-audit --config p/secrets --config p/java --config p/spring --sarif -o semgrep.sarif"),
             ("dependency-check", "dependency-check.sh --scan . --format JSON --out dc-report"),
             ("osv-scanner", "osv-scanner scan -r .")],
    "go": [("govulncheck", "govulncheck ./..."), ("gosec", "gosec -fmt sarif -out gosec.sarif ./..."),
           ("semgrep", "semgrep scan --config p/security-audit --config p/secrets --config p/golang --sarif -o semgrep.sarif")],
    "angular": [("npm", "npm audit --omit=dev --json > npm-audit.json"), ("osv-scanner", "osv-scanner scan -L package-lock.json"),
                ("semgrep", "semgrep scan --config p/security-audit --config p/secrets --config p/typescript --sarif -o semgrep.sarif")],
    "node": [("npm", "npm audit --omit=dev --json > npm-audit.json"), ("osv-scanner", "osv-scanner scan -r .")],
    "terraform": [("checkov", "checkov -d . --framework terraform --output sarif --output-file-path ."), ("trivy", "trivy config --format sarif -o trivy-iac.sarif .")],
    "terragrunt": [("tg_lint", "python <terragrunt-iac>/scripts/tg_lint.py ."), ("terragrunt", "terragrunt hcl validate")],
    "github-actions": [("zizmor", "zizmor --format sarif .github/workflows > zizmor.sarif"), ("actionlint", "actionlint")],
    "azure-pipelines": [("checkov", "checkov -d . --framework azure_pipelines")],
    "docker": [("hadolint", "hadolint Dockerfile"), ("trivy", "trivy config Dockerfile")],
    "kubernetes": [("trivy", "trivy config k8s/"), ("kubesec", "kubesec scan <manifest.yaml>")],
    "secrets": [("gitleaks", "gitleaks git --redact -r gitleaks.json")],
}


def detect_stacks(root: Path, files: list[Path]) -> list[str]:
    names = {f.name for f in files}
    rels = [f.relative_to(root).as_posix() for f in files]
    stacks = set()
    if names & {"pom.xml", "build.gradle", "build.gradle.kts"}:
        stacks.add("java")
    if "gradle.properties" in names and any("domain/usecase" in r for r in rels):
        stacks.add("scaffold-bancolombia")
    if "go.mod" in names:
        stacks.add("go")
    if "angular.json" in names:
        stacks.add("angular")
    elif "package.json" in names:
        stacks.add("node")
    if any(r.endswith(".tf") for r in rels):
        stacks.add("terraform")
    if any(n in names for n in ("terragrunt.hcl", "root.hcl", "terragrunt.stack.hcl")):
        stacks.add("terragrunt")
    if any(r.startswith(".github/workflows/") for r in rels):
        stacks.add("github-actions")
    if any(n in names for n in ("azure-pipelines.yml", "azure-pipelines.yaml")) or any("azure-pipelines" in r for r in rels):
        stacks.add("azure-pipelines")
    if names & {"Dockerfile", "Containerfile"}:
        stacks.add("docker")
    if any(r.endswith((".yaml", ".yml")) and _looks_k8s(root / r) for r in rels[:2000]):
        stacks.add("kubernetes")
    return sorted(stacks)


def _looks_k8s(p: Path) -> bool:
    try:
        head = p.read_text(encoding="utf-8", errors="ignore")[:2000]
    except OSError:
        return False
    return "apiVersion:" in head and "kind:" in head


def iter_files(root: Path) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in TEXT_EXT or fn in TEXT_NAMES or fn.startswith(".env"):
                out.append(p)
    return sorted(out)


def changed_files(root: Path, base: str) -> list[Path] | None:
    try:
        res = subprocess.run(["git", "-C", str(root), "diff", "--name-only", f"{base}...HEAD"],
                             capture_output=True, text=True, timeout=60, check=True)
        unstaged = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "HEAD"],
                                  capture_output=True, text=True, timeout=60)
    except (subprocess.SubprocessError, FileNotFoundError):
        return None
    names = set(res.stdout.split()) | set(unstaged.stdout.split())
    return sorted(root / n for n in names if (root / n).is_file())


def rule_applies(rule: Rule, path: Path) -> bool:
    if not rule.exts and not rule.names:
        return True
    return path.suffix.lower() in rule.exts or path.name in rule.names


def scan_file(root: Path, path: Path, max_left: int) -> list[dict]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return []
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    rel = path.relative_to(root).as_posix()
    is_test = bool(TEST_PATH.search(rel))
    signals: list[dict] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        if len(signals) >= max_left:
            break
        if len(line) > 4000:
            continue
        for sid, rx in SECRET_PATTERNS:
            m = rx.search(line)
            if not m:
                continue
            val = m.group(1)
            if sid == "generic-assignment" and PLACEHOLDER.search(val):
                continue
            signals.append({"rule": f"secret.{sid}", "category": "secrets", "file": rel, "line": i,
                            "excerpt": f"valor enmascarado: {mask(val)}", "test_path": is_test,
                            "hint": "Posible secreto: verificar validez SIN usarlo; rotación si es real (aplica también en tests)"})
            break
        for rule in RULES:
            if not rule_applies(rule, path):
                continue
            if rule.pattern.search(line):
                excerpt = line.strip()
                for _, rx in SECRET_PATTERNS:
                    excerpt = rx.sub(lambda mm: mm.group(0).replace(mm.group(1), mask(mm.group(1))), excerpt)
                signals.append({"rule": rule.id, "category": rule.category, "file": rel, "line": i,
                                "excerpt": excerpt[:220], "test_path": is_test, "hint": rule.hint})
    return signals


def build_plan(stacks: list[str]) -> list[dict]:
    plan, seen = [], set()
    for st in stacks + ["secrets"]:
        for tool, cmd in TOOL_PLAN.get(st, []):
            key = (tool, cmd)
            if key in seen:
                continue
            seen.add(key)
            binary = "dependency-check.sh" if tool == "dependency-check" else ("python3" if tool == "tg_lint" else tool)
            plan.append({"stack": st, "tool": tool, "command": cmd, "installed": shutil.which(binary) is not None})
    return plan


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Triage de seguridad (señales candidatas, no hallazgos)")
    ap.add_argument("repo")
    ap.add_argument("--base", help="rama/commit base para limitar a archivos cambiados")
    ap.add_argument("--json", help="ruta del JSON de salida")
    ap.add_argument("--max-signals", type=int, default=400)
    args = ap.parse_args(argv)

    root = Path(args.repo).resolve()
    if not root.is_dir():
        print(f"error: {root} no es un directorio", file=sys.stderr)
        return 2
    all_files = iter_files(root)
    stacks = detect_stacks(root, all_files)
    scope = "full"
    files = all_files
    if args.base:
        ch = changed_files(root, args.base)
        if ch is None:
            print("aviso: no se pudo calcular el diff; se analiza el repositorio completo", file=sys.stderr)
        else:
            scope = f"diff:{args.base}"
            files = [f for f in ch if f in set(all_files)]

    signals: list[dict] = []
    for f in files:
        left = args.max_signals - len(signals)
        if left <= 0:
            break
        signals.extend(scan_file(root, f, left))

    by_cat: dict[str, int] = {}
    for s in signals:
        by_cat[s["category"]] = by_cat.get(s["category"], 0) + 1
    high_risk = sorted({s["category"] for s in signals} & {"authz", "authn", "crypto", "secrets", "injection", "iam", "cicd", "agentic", "deserialization", "ssrf"})
    result = {
        "schema": "aegis-triage/1",
        "note": "Señales candidatas para análisis manual. No son hallazgos ni veredictos.",
        "repo": str(root), "scope": scope, "files_scanned": len(files),
        "stacks": stacks, "signals_by_category": dict(sorted(by_cat.items())),
        "high_risk_categories": high_risk,
        "truncated": len(signals) >= args.max_signals,
        "signals": signals, "tool_plan": build_plan(stacks),
    }
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json:
        Path(args.json).write_text(out, encoding="utf-8")
        print(f"stacks={','.join(stacks) or '-'} archivos={len(files)} señales={len(signals)} "
              f"riesgo_alto={','.join(high_risk) or '-'} -> {args.json}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
