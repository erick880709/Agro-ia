#!/usr/bin/env python3
"""tg_lint — análisis estático de repos Terragrunt (complementa `terragrunt hcl fmt/validate`).

Detecta sintaxis legada (0.x), riesgos de seguridad y malas prácticas descritas en
resources/09-migracion-0x-a-1x.md y resources/11-checklist-revision.md.

Uso:
    python tg_lint.py <ruta> [--json] [--prod-pattern prod] [--no-fmt]
Código de salida: 1 si hay hallazgos ALTA, 0 en otro caso.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

SKIP_DIRS = {".git", ".terragrunt-cache", ".terragrunt-stack", ".terraform", "node_modules", ".venv"}
HCL_EXT = (".hcl",)
CI_FILES = (".yml", ".yaml", ".sh", ".bash", ".mk", ".ps1", ".envrc", ".env")
CI_NAMES = ("Makefile", "Dockerfile", "Jenkinsfile", "justfile", "Taskfile.yml")

LEGACY_CMDS = {
    "run-all": "run --all", "plan-all": "run --all -- plan", "apply-all": "run --all -- apply",
    "destroy-all": "run --all -- destroy", "output-all": "run --all -- output",
    "validate-all": "run --all -- validate", "hclfmt": "hcl fmt", "hclvalidate": "hcl validate",
    "graph-dependencies": "dag graph", "render-json": "render --json -w",
    "terragrunt-info": "info print", "validate-inputs": "hcl validate --inputs",
    "spin-up": "run --all -- apply", "tear-down": "run --all -- destroy",
}
RUN_CMD_FLAGS = {"--terragrunt-quiet", "--terragrunt-global-cache", "--terragrunt-no-cache"}
ENV_EXCEPTIONS = {"TERRAGRUNT_DEBUG": "TG_INPUTS_DEBUG", "TERRAGRUNT_TFPATH": "TG_TF_PATH"}

findings = []


def add(sev, path, line, rule, msg, fix):
    findings.append({"severidad": sev, "archivo": path, "linea": line, "regla": rule, "mensaje": msg, "cambio": fix})


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            yield os.path.join(d, f)


def strip_comment(line):
    # Quita comentarios # y // fuera de strings (aproximación suficiente para lint).
    out, in_str = [], False
    i = 0
    while i < len(line):
        c = line[i]
        if c == '"' and (i == 0 or line[i - 1] != "\\"):
            in_str = not in_str
        if not in_str and (c == "#" or line[i:i + 2] == "//"):
            # "//" dentro de fuentes git va siempre en string; fuera de string es comentario
            break
        out.append(c)
        i += 1
    return "".join(out)


def lint_hcl(path, rel, text, prod_re):
    lines = text.splitlines()
    is_prod = bool(prod_re.search(rel))
    has_errors_block = re.search(r"^\s*errors\s*\{", text, re.M) is not None
    in_heredoc = None
    for n, raw in enumerate(lines, 1):
        if in_heredoc:
            if raw.strip() == in_heredoc:
                in_heredoc = None
            continue
        m = re.search(r"<<-?\s*([A-Z_]+)\s*$", raw)
        line = strip_comment(raw)
        if m:
            in_heredoc = m.group(1)

        # --- ALTA ---
        mm = re.search(r"mock_outputs_allowed_terraform_commands\s*=\s*\[([^\]]*)\]", line)
        if mm and re.search(r'"(apply|destroy)"', mm.group(1)):
            add("ALTA", rel, n, "mock-en-apply", "Se permiten mock_outputs en apply/destroy.",
                'mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]')

        ms = re.search(r'^\s*source\s*=\s*"([^"]+)"', line)
        if ms:
            src = ms.group(1)
            remote = re.match(r"(git::|git@|github\.com|gitlab\.com|bitbucket\.org|https?://|s3::|gcs::)", src)
            if src.startswith("tfr:"):
                if "version=" not in src and not re.search(r"^\s*version\s*=", text, re.M):
                    add("ALTA" if is_prod else "MEDIA", rel, n, "registry-sin-version",
                        "Módulo de registry sin versión.", "Agregar ?version=X.Y.Z o el atributo version")
            elif remote:
                ref = re.search(r"[?&]ref=([^&\"]+)", src)
                if not ref:
                    add("ALTA" if is_prod else "MEDIA", rel, n, "fuente-sin-pinear",
                        f"Fuente remota sin ?ref= ({src}).", "Pinear a un tag semver: ?ref=vX.Y.Z")
                elif re.fullmatch(r"(main|master|develop|dev|HEAD|trunk)", ref.group(1)):
                    add("ALTA" if is_prod else "MEDIA", rel, n, "fuente-en-rama",
                        f"Fuente apunta a la rama '{ref.group(1)}'.", "Usar un tag inmutable (vX.Y.Z) o SHA")

        if re.search(r"AKIA[0-9A-Z]{16}", raw):
            add("ALTA", rel, n, "secreto-aws", "Posible Access Key de AWS en el código.", "Eliminar y rotar; usar OIDC/roles")
        msec = re.search(r'^\s*(\w*(password|secret|client_secret|access_key|api_key|token)\w*)\s*=\s*"([^"$]{4,})"', line, re.I)
        if msec and not re.search(r"(mock|fake|example|ejemplo|changeme|todo|dummy)", msec.group(3), re.I):
            add("ALTA", rel, n, "secreto-literal", f"Valor literal en '{msec.group(1)}'.",
                "Usar get_env(), sops_decrypt_file(), TF_VAR_* o un gestor de secretos")

        # --- MEDIA ---
        if re.match(r"^\s*include\s*\{", line):
            add("MEDIA", rel, n, "include-sin-etiqueta", "include sin etiqueta (deprecado).", 'include "root" { ... }')
        if re.search(r"find_in_parent_folders\(\s*\)", line):
            add("MEDIA", rel, n, "find-sin-argumento", "find_in_parent_folders() busca terragrunt.hcl por defecto.",
                'find_in_parent_folders("root.hcl")')
        if re.match(r"^\s*skip\s*=", line):
            add("MEDIA", rel, n, "skip-deprecado", "Atributo skip deprecado.", 'exclude { if = true, actions = ["all"] }')
        if re.match(r"^\s*(retry_max_attempts|retry_sleep_interval_sec)\s*=", line) or (
                re.match(r"^\s*retryable_errors\s*=", line) and not has_errors_block):
            add("MEDIA", rel, n, "retry-deprecado", "Reintentos con atributos legados.",
                'errors { retry "x" { retryable_errors = [...], max_attempts = 3, sleep_interval_sec = 5 } }')
        if "mock_outputs_merge_with_state" in line:
            add("MEDIA", rel, n, "merge-with-state", "mock_outputs_merge_with_state deprecado.",
                'mock_outputs_merge_strategy_with_state = "shallow"')
        if re.search(r'config_path\s*=\s*"[^"]*\.hcl"', line):
            add("MEDIA", rel, n, "config-path-archivo", "config_path apunta a un archivo (deprecado).", "Apuntar a la carpeta")
        if re.match(r"^\s*skip_outputs\s*=\s*true", line):
            add("MEDIA", rel, n, "skip-outputs", "skip_outputs = true usa siempre mocks.", "Usar locals o quitar skip_outputs")
        if re.search(r"\b(run_cmd|get_aws_account_id|sops_decrypt_file)\(", line) and os.path.basename(path) == "root.hcl":
            add("MEDIA", rel, n, "costoso-en-discovery",
                "Función costosa en root.hcl: se ejecuta por cada unit durante el discovery.",
                "Mover a account.hcl con valor estático o cachear (run_cmd --terragrunt-global-cache)")
        if re.search(r"--terragrunt-[a-z-]+", line):
            for flag in re.findall(r"--terragrunt-[a-z-]+", line):
                if flag not in RUN_CMD_FLAGS:
                    add("MEDIA", rel, n, "flag-legado", f"Flag legado {flag} en HCL.", "Quitar prefijo --terragrunt- (ver 09)")

    if re.search(r"^\s*remote_state\s*\{", text, re.M):
        for n, raw in enumerate(lines, 1):
            mk = re.match(r'^\s*(key|prefix)\s*=\s*(.+)$', strip_comment(raw))
            if mk and "path_relative_to_include" not in mk.group(2) and "values." not in mk.group(2):
                add("ALTA", rel, n, "key-estado-fija",
                    "La key/prefix del estado no usa path_relative_to_include(): varios units podrían compartir estado.",
                    'key = "${path_relative_to_include()}/tf.tfstate"')
        if re.search(r'backend\s*=\s*"s3"', text) and not re.search(r"(use_lockfile|dynamodb_table)", text):
            add("ALTA", rel, 0, "s3-sin-lock", "Backend S3 sin bloqueo.", "use_lockfile = true")


def lint_ci(rel, text):
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0] if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        if "terragrunt" in line or "TG_" in line or "tg_command" in line:
            for old, new in LEGACY_CMDS.items():
                if re.search(rf"(?<![\w-]){re.escape(old)}(?![\w-])", line):
                    add("MEDIA", rel, n, "comando-legado", f"Comando legado '{old}'.", f"Usar '{new}'")
        for flag in re.findall(r"--terragrunt-[a-z-]+", line):
            if flag not in RUN_CMD_FLAGS:
                add("MEDIA", rel, n, "flag-legado", f"Flag legado {flag}.", "Quitar prefijo --terragrunt- (ver 09)")
        for env in set(re.findall(r"\bTERRAGRUNT_[A-Z_]+\b", line)):
            add("MEDIA", rel, n, "env-legada", f"Variable {env} ya no se lee.",
                f"Usar {ENV_EXCEPTIONS.get(env, env.replace('TERRAGRUNT_', 'TG_', 1))}")
        if "TF_PLUGIN_CACHE_DIR" in line:
            add("MEDIA", rel, n, "plugin-cache-manual",
                "TF_PLUGIN_CACHE_DIR manual con run --all provoca condiciones de carrera.",
                "Quitarlo (auto provider cache) o usar --provider-cache")
        if re.search(r"the-commons-project/terragrunt-github-actions", line):
            add("MEDIA", rel, n, "action-legada", "Action legada basada en Docker.", "gruntwork-io/terragrunt-action@v3 + mise.toml")
        if re.search(r"gruntwork-io/terragrunt-action@v[12]\b", line):
            add("BAJA", rel, n, "action-version", "terragrunt-action antigua.", "gruntwork-io/terragrunt-action@v3")
        if "pull_request_target" in line:
            add("ALTA", rel, n, "pull-request-target",
                "pull_request_target ejecuta código del PR con secretos/OIDC del repo base.", "Usar pull_request")
        if re.search(r"--queue-ignore-errors", line) and "apply" in line:
            add("ALTA", rel, n, "ignore-errors-apply", "Apply ignorando errores de dependencias.", "Quitar --queue-ignore-errors")
        if "fetch-depth: 1" in line or re.search(r"fetchDepth:\s*1\b", line):
            add("BAJA", rel, n, "fetch-depth",
                "Checkout superficial: los filtros Git necesitan historia.", "fetch-depth: 0 (plan) / 2 (apply con HEAD^)")


def lint_repo(root):
    rootrel = lambda p: os.path.relpath(p, root)
    # raíz llamada terragrunt.hcl: un terragrunt.hcl con descendientes terragrunt.hcl
    tg_files = [p for p in walk(root) if os.path.basename(p) == "terragrunt.hcl"]
    tg_dirs = {os.path.dirname(p) for p in tg_files}
    for d in tg_dirs:
        if any(o != d and o.startswith(d + os.sep) for o in tg_dirs):
            add("MEDIA", rootrel(os.path.join(d, "terragrunt.hcl")), 0, "raiz-terragrunt-hcl",
                "terragrunt.hcl con units debajo: la raíz debe llamarse root.hcl.",
                'Renombrar a root.hcl y usar find_in_parent_folders("root.hcl")')
    if not any(os.path.exists(os.path.join(root, f)) for f in ("mise.toml", ".mise.toml", ".tool-versions")):
        add("MEDIA", ".", 0, "sin-versiones-pineadas", "No hay mise.toml/.tool-versions.",
            'Crear mise.toml con terragrunt = "1.2.1" y opentofu = "1.13.1"')
    roots = [p for p in walk(root) if os.path.basename(p) == "root.hcl"]
    for r in roots:
        if "terragrunt_version_constraint" not in open(r, encoding="utf-8", errors="ignore").read():
            add("BAJA", rootrel(r), 0, "sin-version-constraint", "root.hcl sin terragrunt_version_constraint.",
                'terragrunt_version_constraint = ">= 1.2.0, < 2.0.0"')
    gi = os.path.join(root, ".gitignore")
    if tg_files or roots:
        content = open(gi, encoding="utf-8", errors="ignore").read() if os.path.exists(gi) else ""
        for pat in (".terragrunt-cache", ".terragrunt-stack"):
            if pat not in content:
                add("BAJA", ".gitignore", 0, "gitignore", f"Falta {pat}/ en .gitignore.", f"Agregar {pat}/")
    has_catalog = any(os.path.isdir(os.path.join(root, d)) for d in ("catalog", "units", "modules"))
    has_live_stacks = any(os.path.basename(p) == "terragrunt.stack.hcl" for p in walk(root))
    if has_catalog and has_live_stacks and os.path.isdir(os.path.join(root, "catalog")):
        add("BAJA", ".", 0, "monorepo-catalogo",
            "Monorepo con catalog/: los filtros Git pueden intentar generar stacks del catálogo.",
            'En CI usa --filter "(./live)...[base...HEAD]" (ver resources/05)')


def run_fmt(root):
    if not shutil.which("terragrunt"):
        return
    try:
        r = subprocess.run(["terragrunt", "hcl", "fmt", "--check", "--log-level", "error", "--working-dir", root],
                           capture_output=True, text=True, timeout=120)
    except Exception:
        return
    for f in re.findall(r"File '([^']+)' needs formatting", r.stdout + r.stderr):
        add("BAJA", os.path.relpath(f, root), 0, "hcl-fmt", "Archivo sin formatear.", "terragrunt hcl fmt")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ruta")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--prod-pattern", default=r"(^|/)(prod|prd|production|produccion)(/|$)")
    ap.add_argument("--no-fmt", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.ruta)
    prod_re = re.compile(a.prod_pattern)

    for p in walk(root):
        rel = os.path.relpath(p, root)
        name = os.path.basename(p)
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        if name.endswith(HCL_EXT):
            lint_hcl(p, rel, text, prod_re)
        elif name.endswith(CI_FILES) or name in CI_NAMES:
            lint_ci(rel, text)
    lint_repo(root)
    if not a.no_fmt:
        run_fmt(root)

    order = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    findings.sort(key=lambda f: (order[f["severidad"]], f["archivo"], f["linea"]))
    if a.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        if not findings:
            print("tg_lint: sin hallazgos ✔")
        for f in findings:
            loc = f"{f['archivo']}:{f['linea']}" if f["linea"] else f["archivo"]
            print(f"[{f['severidad']}] {loc} — {f['mensaje']} ({f['regla']})\n    → {f['cambio']}")
        c = {s: sum(1 for f in findings if f["severidad"] == s) for s in order}
        print(f"\nResumen: ALTA={c['ALTA']} MEDIA={c['MEDIA']} BAJA={c['BAJA']}")
    sys.exit(1 if any(f["severidad"] == "ALTA" for f in findings) else 0)


if __name__ == "__main__":
    main()
