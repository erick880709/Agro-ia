#!/usr/bin/env python3
"""Harness offline para evaluar la skill code-review. Ejecuta candidatos solo en entornos desechables.

Comandos:
    list
    prepare <caso> <workspace-inexistente>
    check   <caso> <workspace>
    prepare-routing <destino.json>
    check-routing   <observaciones.json>

`prepare` construye el workspace (base + cambio). Si hay git, crea `main` con
la base y `feature` con el cambio, para que el candidato revise
`git diff main...feature`. Escribe el encargo en TASK.md (excluido de git).
`check` compara archivos protegidos por hash (la revisión es de solo lectura)
y ejecuta el oráculo externo en un subproceso aislado.

Códigos de salida: 0 aprobado, 1 fallos observados, 2 entrada inválida.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
EVAL = SKILL_ROOT / "evaluations"
FIX = EVAL / "fixtures"


def cases() -> dict:
    return json.loads((EVAL / "cases.json").read_text(encoding="utf-8"))


def safe_workspace(value: str, must_exist: bool) -> Path:
    raw = Path(value).absolute()
    for part in (raw, *raw.parents):
        if part.is_symlink():
            raise ValueError("El workspace y sus ancestros no deben ser enlaces")
    resolved = raw.resolve()
    if resolved == SKILL_ROOT or SKILL_ROOT in resolved.parents or resolved in SKILL_ROOT.parents:
        raise ValueError("El workspace no debe solaparse con el paquete de la skill")
    if must_exist and not resolved.is_dir():
        raise ValueError("El workspace no existe")
    if not must_exist and resolved.exists():
        raise ValueError("El workspace debe no existir; nunca se sobrescribe")
    return resolved


def git(ws: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(ws), *args], check=True, capture_output=True, text=True)


def has_git() -> bool:
    return shutil.which("git") is not None


def prepare(case: str, workspace: str) -> dict:
    cs = cases()
    if case not in cs:
        raise ValueError(f"Caso desconocido: {case}")
    spec = cs[case]
    ws = safe_workspace(workspace, must_exist=False)
    base, overlay = spec.get("base"), spec["overlay"]
    if base:
        shutil.copytree(FIX / base, ws)
        if has_git():
            git(ws, "init", "-q", "-b", "main")
            git(ws, "config", "user.email", "eval@local")
            git(ws, "config", "user.name", "eval")
            git(ws, "add", "-A")
            git(ws, "commit", "-q", "-m", "base")
            git(ws, "checkout", "-q", "-b", "feature")
        shutil.copytree(FIX / overlay, ws, dirs_exist_ok=True)
        if has_git():
            git(ws, "add", "-A")
            git(ws, "commit", "-q", "-m", f"cambio {case}")
    else:
        shutil.copytree(FIX / overlay, ws)
    (ws / "TASK.md").write_text(spec["prompt"] + "\n", encoding="utf-8")
    if (ws / ".git").is_dir():
        with (ws / ".git" / "info" / "exclude").open("a", encoding="utf-8") as fh:
            fh.write("TASK.md\n")
    return {"case": case, "workspace": str(ws), "git": (ws / ".git").is_dir()}


def source_of(spec: dict, rel: str) -> Path:
    candidate = FIX / spec["overlay"] / rel
    if candidate.is_file():
        return candidate
    return FIX / spec["base"] / rel


def check(case: str, workspace: str) -> dict:
    cs = cases()
    if case not in cs:
        raise ValueError(f"Caso desconocido: {case}")
    spec = cs[case]
    ws = safe_workspace(workspace, must_exist=True)
    failures: list[str] = []
    for rel in spec.get("protected", []):
        src, cand = source_of(spec, rel), ws / rel
        if not cand.is_file() or cand.is_symlink() or \
                hashlib.sha256(src.read_bytes()).digest() != hashlib.sha256(cand.read_bytes()).digest():
            failures.append(f"Archivo protegido modificado o ausente: {rel}")
    run = subprocess.run([sys.executable, "-I", str(EVAL / "oracle.py"), case, str(ws)],
                         cwd=EVAL, capture_output=True, text=True, timeout=30)
    detail = run.stdout.strip()
    if run.returncode:
        failures += [l for l in (run.stderr or run.stdout).strip().splitlines() if l]
    out = {"case": case, "passed": not failures, "failures": failures}
    if detail:
        try:
            out["detalle"] = json.loads(detail.splitlines()[-1])
        except json.JSONDecodeError:
            out["detalle"] = detail
    return out


def prepare_routing(dest: str) -> dict:
    with Path(dest).open("x", encoding="utf-8") as fh:
        json.dump(json.loads((EVAL / "routing" / "prompts.json").read_text(encoding="utf-8")), fh, ensure_ascii=False, indent=2)
    return {"prompts": dest}


def check_routing(obs_path: str) -> dict:
    expected = json.loads((EVAL / "routing" / "expected.json").read_text(encoding="utf-8"))
    obs = json.loads(Path(obs_path).read_text(encoding="utf-8"))
    if not isinstance(obs, list):
        raise ValueError("Las observaciones deben ser un array JSON")
    seen: dict[str, dict] = {}
    for row in obs:
        rid = row.get("id")
        if rid not in expected or rid in seen:
            raise ValueError(f"ID desconocido o duplicado: {rid}")
        if not str(row.get("evidence", "")).strip():
            raise ValueError(f"Evidencia vacía en {rid}")
        seen[rid] = row
    missing = sorted(set(expected) - set(seen))
    if missing:
        raise ValueError(f"Faltan observaciones: {missing}")
    tp = fp = tn = fn = 0
    wrong = []
    for rid, should in expected.items():
        selected = "code-review" in seen[rid].get("selected_skills", [])
        if should and selected:
            tp += 1
        elif should:
            fn += 1; wrong.append(rid)
        elif selected:
            fp += 1; wrong.append(rid)
        else:
            tn += 1
    return {"positivos_acertados": tp, "falsos_negativos": fn, "negativos_acertados": tn,
            "falsos_positivos": fp, "errores": wrong, "passed": not wrong}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("prepare"); p.add_argument("case"); p.add_argument("workspace")
    c = sub.add_parser("check"); c.add_argument("case"); c.add_argument("workspace")
    r = sub.add_parser("prepare-routing"); r.add_argument("dest")
    k = sub.add_parser("check-routing"); k.add_argument("observations")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "list":
            res = {name: v["prompt"] for name, v in cases().items()}
        elif args.cmd == "prepare":
            res = prepare(args.case, args.workspace)
        elif args.cmd == "check":
            res = check(args.case, args.workspace)
        elif args.cmd == "prepare-routing":
            res = prepare_routing(args.dest)
        else:
            res = check_routing(args.observations)
    except (ValueError, FileExistsError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("passed", True) else 1


if __name__ == "__main__":
    sys.exit(main())
