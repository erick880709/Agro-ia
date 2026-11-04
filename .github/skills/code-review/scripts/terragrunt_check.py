#!/usr/bin/env python3
"""Pre-chequeo heurístico de código Terragrunt 1.x / OpenTofu y de sus pipelines.

Detecta, sin credenciales ni nube, violaciones probables de las reglas de
`references/terragrunt-iac.md` (alineadas con la skill `terragrunt-iac`):

  TG-001  mock_outputs permitidos en apply/destroy                    bloqueante
  TG-002  fuente remota sin ?ref= o apuntando a una rama              mayor (bloqueante en prod)
  TG-003  secreto o access key literal en HCL                         bloqueante
  TG-004  key/prefix de estado sin path_relative_to_include()         bloqueante
  TG-005  backend S3 sin bloqueo (use_lockfile/dynamodb_table)        mayor
  TG-006  sintaxis/comando/flag/env previo a 1.0                      mayor
  TG-007  include sin etiqueta, find_in_parent_folders() sin argumento
          o raíz llamada terragrunt.hcl                               mayor
  TG-008  atributos deprecados (skip, retryable_errors suelto,
          mock_outputs_merge_with_state, config_path a archivo)       menor
  TG-009  include/dependency/unit apuntando a una ruta inexistente    bloqueante
  TG-010  dependency sin mock_outputs                                 menor
  TG-011  skip_outputs = true                                         menor
  TG-012  función costosa en root.hcl (se ejecuta por unit al descubrir) menor
  TG-013  sin versiones pineadas (mise.toml / terragrunt_version_constraint) menor
  TG-014  .gitignore sin .terragrunt-cache/.terragrunt-stack          nit
  TG-015  hcl fmt pendiente (solo con --run-tools)                    nit
  TG-016  hcl validate falla (solo con --run-tools)                   bloqueante
  CI-001  pull_request_target en workflow de IaC                      bloqueante
  CI-002  action legada de Terragrunt (the-commons-project y forks)   mayor
  CI-003  versión 'latest' de Terragrunt/OpenTofu o action en rama    mayor
  CI-004  --filter-allow-destroy en job sin environment/aprobación    mayor
  CI-005  --queue-ignore-errors en apply                              bloqueante
  CI-006  checkout superficial con filtros Git                        mayor
  CI-007  credenciales de nube estáticas en el pipeline               mayor
  CI-008  TF_PLUGIN_CACHE_DIR manual con run --all                    menor

NO sustituye `terragrunt hcl validate`, `tofu validate`, tflint, escáneres ni un
`plan` revisado. Úsalo como pista y verifica cada hallazgo.

Uso:
    python terragrunt_check.py <repo> [--json] [--base main] [--changed-list f.txt]
                               [--prod-pattern REGEX] [--run-tools] [--force]

Salida: 0 sin hallazgos en alcance, 1 con hallazgos, 2 error o no es Terragrunt.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass

SKIP_DIRS = {".git", ".terragrunt-cache", ".terragrunt-stack", ".terraform", "node_modules", ".venv", "build"}
CI_SUFFIXES = (".yml", ".yaml", ".sh", ".bash", ".ps1", ".mk", ".envrc")
CI_NAMES = ("Makefile", "Dockerfile", "Jenkinsfile", "justfile")
RUN_CMD_FLAGS = {"--terragrunt-quiet", "--terragrunt-global-cache", "--terragrunt-no-cache"}
LEGACY_CMDS = {
    "run-all": "run --all", "plan-all": "run --all -- plan", "apply-all": "run --all -- apply",
    "destroy-all": "run --all -- destroy", "output-all": "run --all -- output",
    "validate-all": "run --all -- validate", "hclfmt": "hcl fmt", "hclvalidate": "hcl validate",
    "graph-dependencies": "dag graph", "render-json": "render --json -w",
    "terragrunt-info": "info print", "validate-inputs": "hcl validate --inputs",
}
ENV_EXCEPTIONS = {"TERRAGRUNT_DEBUG": "TG_INPUTS_DEBUG", "TERRAGRUNT_TFPATH": "TG_TF_PATH"}
SEVERITY_ORDER = {"bloqueante": 0, "mayor": 1, "menor": 2, "nit": 3}


@dataclass
class Finding:
    rule: str
    severidad: str
    archivo: str
    linea: int | None
    mensaje: str
    remedio: str
    preexistente: bool = False


# ---------------------------------------------------------------- utilidades

def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def walk(root: str):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            yield os.path.join(d, f)


def rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def strip_comment(line: str) -> str:
    out, in_str, i = [], False, 0
    while i < len(line):
        c = line[i]
        if c == '"' and (i == 0 or line[i - 1] != "\\"):
            in_str = not in_str
        if not in_str and (c == "#" or line[i:i + 2] == "//"):
            break
        out.append(c)
        i += 1
    return "".join(out)


def code_lines(text: str):
    """Itera (n, línea sin comentarios) saltando heredocs."""
    heredoc = None
    for n, raw in enumerate(text.splitlines(), 1):
        if heredoc:
            if raw.strip() == heredoc:
                heredoc = None
            continue
        m = re.search(r"<<-?\s*([A-Z_]+)\s*$", raw)
        if m:
            heredoc = m.group(1)
        yield n, strip_comment(raw)


def is_terragrunt_repo(root: str) -> bool:
    for p in walk(root):
        name = os.path.basename(p)
        if name in ("terragrunt.hcl", "terragrunt.stack.hcl", "root.hcl"):
            return True
    return False


def blocks(text: str, name: str):
    """Devuelve (línea_inicio, cuerpo) de cada bloque `name` (con o sin etiqueta)."""
    for m in re.finditer(rf'^[ \t]*{name}\b([ \t]+"[^"]*")?[ \t]*\{{', text, re.M):
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        yield text.count("\n", 0, m.start()) + 1, text[m.end():i]


# ---------------------------------------------------------------- reglas HCL

def check_hcl(root: str, path: str, text: str, prod_re: re.Pattern, f: list[Finding]):
    r = rel(root, path)
    is_prod = bool(prod_re.search(r))
    name = os.path.basename(path)
    in_catalog_unit = "values." in text  # unit/stack de catálogo: rutas relativas se resuelven al generar
    has_errors_block = re.search(r"^\s*errors\s*\{", text, re.M) is not None

    for n, line in code_lines(text):
        mm = re.search(r"mock_outputs_allowed_terraform_commands\s*=\s*\[([^\]]*)\]", line)
        if mm and re.search(r'"(apply|destroy)"', mm.group(1)):
            f.append(Finding("TG-001", "bloqueante", r, n, "mock_outputs permitidos en apply/destroy: un apply podría usar valores falsos",
                             'mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]'))
        ms = re.match(r'^\s*source\s*=\s*"([^"]+)"', line)
        if ms:
            src = ms.group(1)
            if re.match(r"(git::|git@|github\.com|gitlab\.com|bitbucket\.org|https?://|s3::|gcs::)", src):
                ref = re.search(r"[?&]ref=([^&\"]+)", src)
                sev = "bloqueante" if is_prod else "mayor"
                if not ref:
                    f.append(Finding("TG-002", sev, r, n, f"Fuente remota sin ?ref= ({src}): el despliegue cambia sin cambio de código",
                                     "Pinear a un tag semver inmutable (?ref=vX.Y.Z) o SHA"))
                elif re.fullmatch(r"(main|master|develop|dev|trunk|HEAD)", ref.group(1)):
                    f.append(Finding("TG-002", sev, r, n, f"Fuente apunta a la rama '{ref.group(1)}'",
                                     "Usar un tag inmutable (vX.Y.Z) o SHA"))
            elif src.startswith("tfr:") and "version=" not in src and not re.search(r"^\s*version\s*=", text, re.M):
                f.append(Finding("TG-002", "mayor", r, n, "Módulo de registry sin versión", "Agregar ?version=X.Y.Z o el atributo version"))
        if re.search(r"AKIA[0-9A-Z]{16}", line):
            f.append(Finding("TG-003", "bloqueante", r, n, "Posible Access Key de AWS en el código", "Eliminar, rotar y usar OIDC/roles"))
        msec = re.search(r'^\s*(\w*(password|secret|client_secret|access_key|api_key|token)\w*)\s*=\s*"([^"$]{4,})"', line, re.I)
        if msec and "{{" not in msec.group(3) and not re.search(r"(mock|fake|example|ejemplo|changeme|dummy|placeholder)", msec.group(3), re.I):
            f.append(Finding("TG-003", "bloqueante", r, n, f"Valor literal en '{msec.group(1)}'",
                             "Usar get_env(), sops_decrypt_file(), TF_VAR_* o un gestor de secretos"))
        if re.match(r"^\s*include\s*\{", line):
            f.append(Finding("TG-007", "mayor", r, n, "include sin etiqueta (deprecado; strict control bare-include)", 'include "root" { ... }'))
        if re.search(r"find_in_parent_folders\(\s*\)", line):
            f.append(Finding("TG-007", "mayor", r, n, "find_in_parent_folders() sin argumento busca terragrunt.hcl",
                             'find_in_parent_folders("root.hcl")'))
        if re.match(r"^\s*skip\s*=", line):
            f.append(Finding("TG-008", "menor", r, n, "Atributo skip deprecado", 'exclude { if = true, actions = ["all"] }'))
        if re.match(r"^\s*(retry_max_attempts|retry_sleep_interval_sec)\s*=", line) or (
                re.match(r"^\s*retryable_errors\s*=", line) and not has_errors_block):
            f.append(Finding("TG-008", "menor", r, n, "Reintentos con atributos previos a 1.0",
                             'errors { retry "x" { retryable_errors = [...], max_attempts = 3, sleep_interval_sec = 5 } }'))
        if "mock_outputs_merge_with_state" in line:
            f.append(Finding("TG-008", "menor", r, n, "mock_outputs_merge_with_state deprecado",
                             'mock_outputs_merge_strategy_with_state = "shallow"'))
        if re.search(r'config_path\s*=\s*"[^"]*\.hcl"', line):
            f.append(Finding("TG-008", "menor", r, n, "config_path apunta a un archivo (deprecado)", "Apuntar a la carpeta del unit/stack"))
        if re.match(r"^\s*skip_outputs\s*=\s*true", line):
            f.append(Finding("TG-011", "menor", r, n, "skip_outputs = true usa siempre mocks", "Quitarlo o usar locals"))
        if name == "root.hcl" and re.search(r"\b(run_cmd|get_aws_account_id|sops_decrypt_file)\(", line):
            f.append(Finding("TG-012", "menor", r, n, "Función costosa en root.hcl: se ejecuta por cada unit durante el discovery",
                             "Valor estático en account.hcl o run_cmd(\"--terragrunt-global-cache\", ...)"))
        for flag in re.findall(r"--terragrunt-[a-z-]+", line):
            if flag not in RUN_CMD_FLAGS:
                f.append(Finding("TG-006", "mayor", r, n, f"Flag previo a 1.0 {flag}", "Quitar el prefijo --terragrunt-"))

    # Estado remoto
    for start, body in blocks(text, "remote_state"):
        for n_off, line in enumerate(body.splitlines()):
            mk = re.match(r'^\s*(key|prefix)\s*=\s*(.+)$', strip_comment(line))
            if mk and not any(t in mk.group(2) for t in ("path_relative_to_include", "values.", "{{")):
                f.append(Finding("TG-004", "bloqueante", r, start + n_off, "La key/prefix del estado no usa path_relative_to_include(): varios units compartirían estado",
                                 'key = "${path_relative_to_include()}/tf.tfstate"'))
        if re.search(r'backend\s*=\s*"s3"', body) and not re.search(r"(use_lockfile|dynamodb_table)", body):
            f.append(Finding("TG-005", "mayor", r, start, "Backend S3 sin bloqueo de estado", "use_lockfile = true"))

    # Dependencias
    base_dir = os.path.dirname(path)
    for start, body in blocks(text, "dependency"):
        if "mock_outputs" not in body and "skip_outputs" not in body:
            f.append(Finding("TG-010", "menor", r, start, "dependency sin mock_outputs: plan/validate fallan si la dependencia no está aplicada",
                             'mock_outputs + mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]'))
        mp = re.search(r'config_path\s*=\s*"([^"$]+)"', body)
        if mp and not in_catalog_unit and name != "terragrunt.stack.hcl":
            target = os.path.normpath(os.path.join(base_dir, mp.group(1)))
            if not (os.path.isfile(os.path.join(target, "terragrunt.hcl")) or os.path.isfile(os.path.join(target, "terragrunt.stack.hcl"))
                    or os.path.isfile(target)):
                f.append(Finding("TG-009", "bloqueante", r, start, f"dependency apunta a '{mp.group(1)}', que no contiene un unit ni un stack",
                                 "Corregir config_path o crear el unit"))

    # Integridad del grafo de include
    for start, body in blocks(text, "include"):
        mp = re.search(r'path\s*=\s*find_in_parent_folders\("([^"]+)"\)', body)
        if mp and not in_catalog_unit:
            d, found = base_dir, False
            while True:
                parent = os.path.dirname(d)
                if parent == d:
                    break
                d = parent
                if os.path.isfile(os.path.join(d, mp.group(1))):
                    found = True
                    break
                if os.path.normpath(d) == os.path.normpath(os.path.dirname(root)):
                    break
            if not found:
                f.append(Finding("TG-009", "bloqueante", r, start, f"include busca '{mp.group(1)}' y no existe en ninguna carpeta superior",
                                 "Crear la raíz o corregir el nombre"))

    # Fuentes locales de units/stacks en stack files
    if name == "terragrunt.stack.hcl":
        for kind in ("unit", "stack"):
            for start, body in blocks(text, kind):
                ms = re.search(r'^\s*source\s*=\s*"([^"$]+)"', body, re.M)
                if ms and ms.group(1).startswith((".", "/")):
                    target = os.path.normpath(os.path.join(base_dir, ms.group(1).replace("//", "/")))
                    if not os.path.isdir(target):
                        f.append(Finding("TG-009", "bloqueante", r, start, f"{kind} con source local inexistente '{ms.group(1)}'",
                                         "Corregir la ruta (relativa al stack file) o usar una fuente versionada"))


# ---------------------------------------------------------------- reglas CI

def check_ci(root: str, path: str, text: str, f: list[Finding]):
    r = rel(root, path)
    is_workflow = "/.github/workflows/" in "/" + r or r.endswith(("azure-pipelines.yml", ".gitlab-ci.yml"))
    lines = text.splitlines()
    uses_git_filter = bool(re.search(r"--filter[ =]['\"]?[^'\"\s]*\[", text) or "--filter-affected" in text)
    for n, raw in enumerate(lines, 1):
        line = "" if raw.lstrip().startswith("#") else raw.split(" #", 1)[0]
        if not line.strip():
            continue
        tg_ctx = "terragrunt" in line or "TG_" in line or "tg_command" in line
        if tg_ctx:
            for old, new in LEGACY_CMDS.items():
                if re.search(rf"(?<![\w-]){re.escape(old)}(?![\w-])", line):
                    f.append(Finding("TG-006", "mayor", r, n, f"Comando previo a 1.0 '{old}'", f"Usar '{new}'"))
        for flag in re.findall(r"--terragrunt-[a-z-]+", line):
            if flag not in RUN_CMD_FLAGS:
                f.append(Finding("TG-006", "mayor", r, n, f"Flag previo a 1.0 {flag}", "Quitar el prefijo --terragrunt-"))
        for env in sorted(set(re.findall(r"\bTERRAGRUNT_[A-Z_]+\b", line))):
            f.append(Finding("TG-006", "mayor", r, n, f"Variable {env} ya no se lee en 1.x",
                             f"Usar {ENV_EXCEPTIONS.get(env, env.replace('TERRAGRUNT_', 'TG_', 1))}"))
        if not is_workflow:
            continue
        if re.search(r"\bpull_request_target\b", line):
            f.append(Finding("CI-001", "bloqueante", r, n, "pull_request_target ejecuta código del PR con secretos/OIDC del repo base",
                             "Usar pull_request; planes de forks sin credenciales"))
        if re.search(r"terragrunt-github-actions@", line):
            f.append(Finding("CI-002", "mayor", r, n, "Action legada (the-commons-project / forks como CloudNation): depende de reenviar comandos a terraform, eliminado en 0.88",
                             "gruntwork-io/terragrunt-action@v3 + mise.toml"))
        mu = re.search(r"uses:\s*([\w.-]+/[\w./-]+)@(master|main|latest)\b", line)
        if mu:
            f.append(Finding("CI-003", "mayor", r, n, f"Action {mu.group(1)} referenciada por rama '{mu.group(2)}'",
                             "Pinear a versión o, mejor, a SHA de commit"))
        if re.search(r"\b(tg_version|tf_version|tofu_version|tf_actions_version|tg_actions_version|terragrunt_version|terraform_version)\s*:\s*['\"]?latest", line):
            f.append(Finding("CI-003", "mayor", r, n, "Versión 'latest' de Terragrunt/OpenTofu: el pipeline cambia sin cambio de código",
                             "Pinear en mise.toml o en la entrada de la action"))
        if re.search(r"--queue-ignore-errors", line) and re.search(r"\bapply\b", line):
            f.append(Finding("CI-005", "bloqueante", r, n, "Apply ignorando errores de dependencias", "Quitar --queue-ignore-errors"))
        if re.search(r"\b(AWS_SECRET_ACCESS_KEY|ARM_CLIENT_SECRET|GOOGLE_CREDENTIALS)\b", line):
            f.append(Finding("CI-007", "mayor", r, n, "Credencial estática de nube en el pipeline", "Federación OIDC con roles plan/apply"))
        if "TF_PLUGIN_CACHE_DIR" in line:
            f.append(Finding("CI-008", "menor", r, n, "TF_PLUGIN_CACHE_DIR manual con run --all provoca condiciones de carrera",
                             "Quitarlo (auto provider cache) o --provider-cache"))
        if uses_git_filter and (re.search(r"fetch-depth:\s*1\b", line) or re.search(r"fetchDepth:\s*1\b", line)):
            f.append(Finding("CI-006", "mayor", r, n, "Checkout superficial: los filtros Git no encuentran la base",
                             "fetch-depth: 0 (plan) / 2 (apply con HEAD^)"))
    # CI-004: allow-destroy sin environment en el mismo job (GitHub) o sin deployment/environment (Azure)
    if is_workflow and "--filter-allow-destroy" in text:
        jobs = re.split(r"\n  (?=[A-Za-z0-9_-]+:\s*\n)", text)
        for chunk in jobs:
            github_style = re.search(r"^jobs:\s*$", text, re.M) is not None and "- deployment:" not in text
            env_re = r"^ {4}environment:\s*\S" if github_style else r"^\s+environment:\s*\S"
            if "--filter-allow-destroy" in chunk and not re.search(env_re, chunk, re.M):
                idx = text.find(chunk) + chunk.find("--filter-allow-destroy")
                f.append(Finding("CI-004", "mayor", r, text.count("\n", 0, idx) + 1,
                                 "--filter-allow-destroy en un job sin environment protegido: los destroys no requieren aprobación",
                                 "Mover a un job con environment con reviewers o quitar el flag"))


# ---------------------------------------------------------------- repo

def check_repo(root: str, f: list[Finding]):
    tg_files = [p for p in walk(root) if os.path.basename(p) == "terragrunt.hcl"]
    tg_dirs = {os.path.dirname(p) for p in tg_files}
    for d in sorted(tg_dirs):
        if any(o != d and o.startswith(d + os.sep) for o in tg_dirs):
            f.append(Finding("TG-007", "mayor", rel(root, os.path.join(d, "terragrunt.hcl")), None,
                             "terragrunt.hcl con units debajo: la raíz debe llamarse root.hcl",
                             'Renombrar a root.hcl y usar find_in_parent_folders("root.hcl")'))
    roots = [p for p in walk(root) if os.path.basename(p) == "root.hcl"]
    has_versions = any(os.path.exists(os.path.join(root, x)) for x in ("mise.toml", ".mise.toml", ".tool-versions"))
    if not has_versions:
        f.append(Finding("TG-013", "menor", ".", None, "Sin mise.toml/.tool-versions: versiones de Terragrunt/OpenTofu no pineadas",
                         'mise.toml con terragrunt y opentofu pineados'))
    for p in roots:
        if "terragrunt_version_constraint" not in read(p):
            f.append(Finding("TG-013", "menor", rel(root, p), None, "root.hcl sin terragrunt_version_constraint",
                             'terragrunt_version_constraint = ">= 1.2.0, < 2.0.0"'))
    gi = read(os.path.join(root, ".gitignore"))
    for pat in (".terragrunt-cache", ".terragrunt-stack"):
        if pat not in gi:
            f.append(Finding("TG-014", "nit", ".gitignore", None, f"Falta {pat}/ en .gitignore", f"Agregar {pat}/"))


def run_tools(root: str, f: list[Finding]) -> dict:
    status = {"terragrunt": shutil.which("terragrunt") is not None}
    if not status["terragrunt"]:
        return status
    fmt = subprocess.run(["terragrunt", "hcl", "fmt", "--check", "--log-level", "error", "--working-dir", root],
                         capture_output=True, text=True, timeout=300)
    for path in re.findall(r"File '([^']+)' needs formatting", fmt.stdout + fmt.stderr):
        f.append(Finding("TG-015", "nit", rel(root, path), None, "Archivo sin formatear", "terragrunt hcl fmt"))
    status["hcl_fmt"] = "passed" if fmt.returncode == 0 else "failed"
    val = subprocess.run(["terragrunt", "hcl", "validate", "--log-level", "error", "--no-color", "--working-dir", root],
                         capture_output=True, text=True, timeout=300)
    status["hcl_validate"] = "passed" if val.returncode == 0 else "failed"
    if val.returncode != 0:
        msg = [re.sub(r"\x1b\[[0-9;]*m", "", l) for l in (val.stderr or val.stdout).strip().splitlines()]
        f.append(Finding("TG-016", "bloqueante", ".", None, "terragrunt hcl validate falla: " + (msg[-1][:200] if msg else "sin detalle"),
                         "Corregir el HCL; los units de catálogo que leen values se validan desde el stack generado"))
    return status


def changed_files(root: str, base: str | None, listfile: str | None) -> set[str] | None:
    if listfile:
        return {l.strip().replace("\\", "/") for l in read(listfile).splitlines() if l.strip()}
    if base:
        try:
            outs = [subprocess.run(cmd, capture_output=True, text=True, check=True).stdout for cmd in (
                ["git", "-C", root, "diff", "--name-only", f"{base}...HEAD"],
                ["git", "-C", root, "diff", "--name-only", "HEAD"],
                ["git", "-C", root, "ls-files", "--others", "--exclude-standard"])]
            return {l.strip() for l in "".join(outs).splitlines() if l.strip()}
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise SystemExit(f"No se pudo obtener archivos cambiados con git: {exc}")
    return None


def run(root: str, force: bool = False, base: str | None = None, listfile: str | None = None,
        prod_pattern: str = r"(^|/)(prod|prd|production|produccion)(/|$)", tools: bool = False) -> dict:
    if not is_terragrunt_repo(root) and not force:
        return {"terragrunt": False, "hallazgos": [], "error": "No se encontraron terragrunt.hcl, terragrunt.stack.hcl ni root.hcl (usa --force)"}
    prod_re = re.compile(prod_pattern)
    findings: list[Finding] = []
    for p in walk(root):
        name = os.path.basename(p)
        if name.endswith(".hcl"):
            check_hcl(root, p, read(p), prod_re, findings)
        elif name.endswith(CI_SUFFIXES) or name in CI_NAMES:
            check_ci(root, p, read(p), findings)
    check_repo(root, findings)
    tool_status = run_tools(root, findings) if tools else {"ejecutadas": False}
    seen, unique = set(), []
    for x in findings:
        key = (x.rule, x.archivo, x.linea, x.mensaje)
        if key not in seen:
            seen.add(key)
            unique.append(x)
    scope = changed_files(root, base, listfile)
    if scope is not None:
        for x in unique:
            x.preexistente = x.archivo not in scope and x.archivo not in (".", ".gitignore")
    unique.sort(key=lambda x: (x.preexistente, SEVERITY_ORDER.get(x.severidad, 4), x.archivo, x.linea or 0))
    return {
        "terragrunt": True,
        "herramientas": tool_status,
        "hallazgos": [asdict(x) for x in unique],
        "nota": "Pre-chequeo heurístico. Confirmar con hcl validate, tofu validate, tflint/escáner y un plan revisado.",
    }


def to_markdown(res: dict) -> str:
    if not res.get("terragrunt"):
        return f"# Terragrunt check\n\n{res.get('error')}"
    hall = res["hallazgos"]
    out = ["# Terragrunt check", "",
           f"- Hallazgos: {len([h for h in hall if not h['preexistente']])} en alcance, "
           f"{len([h for h in hall if h['preexistente']])} preexistentes",
           f"- Herramientas: {json.dumps(res['herramientas'], ensure_ascii=False)}", ""]
    if not hall:
        out.append("Sin hallazgos heurísticos.")
    else:
        out += ["| Regla | Severidad | Archivo:línea | Mensaje | Remedio | Alcance |", "|---|---|---|---|---|---|"]
        for h in hall:
            loc = f"{h['archivo']}:{h['linea']}" if h["linea"] else h["archivo"]
            out.append(f"| {h['rule']} | {h['severidad']} | `{loc}` | {h['mensaje']} | {h['remedio']} | "
                       f"{'preexistente' if h['preexistente'] else 'cambio'} |")
    out += ["", f"_{res['nota']}_"]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--force", action="store_true", help="Analizar aunque no se detecte Terragrunt")
    ap.add_argument("--base", help="Rama/sha base para marcar preexistentes vía git")
    ap.add_argument("--changed-list", help="Archivo con rutas cambiadas (relativas al repo)")
    ap.add_argument("--prod-pattern", default=r"(^|/)(prod|prd|production|produccion)(/|$)")
    ap.add_argument("--run-tools", action="store_true", help="Ejecutar terragrunt hcl fmt --check y hcl validate si están instalados")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.repo):
        print(f"No existe el directorio {args.repo}", file=sys.stderr)
        return 2
    res = run(os.path.abspath(args.repo), args.force, args.base, args.changed_list, args.prod_pattern, args.run_tools)
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else to_markdown(res))
    if not res.get("terragrunt"):
        return 2
    return 1 if any(not h["preexistente"] for h in res["hallazgos"]) else 0


if __name__ == "__main__":
    sys.exit(main())
