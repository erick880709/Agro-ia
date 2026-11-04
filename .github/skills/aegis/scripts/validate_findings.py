#!/usr/bin/env python3
"""Valida security-findings.json (contrato aegis-findings/1).

Uso: python validate_findings.py <security-findings.json>
Salida: 0 válido, 1 inválido (una línea por problema), 2 ilegible.
Solo biblioteca estándar.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LEVELS = ["low", "medium", "high", "critical"]
REVIEW_MAP = {"critical": "bloqueante", "high": "bloqueante", "medium": "mayor", "low": "menor"}
VERDICTS = {"confirmed", "needs_validation", "rejected"}
STATUSES = {"abierto", "aceptado", "rechazado", "diferido", "riesgo-aceptado", "corregido", "verificado", "reabierto"}
GLOBAL = {"seguro", "seguro-con-observaciones", "cambios-requeridos", "no-concluyente"}
FP_RX = re.compile(r"^[A-Za-z0-9._:/@+\-]{3,200}$")
LINE_LIKE = re.compile(r"(^|[:/])\d+($|[:/])")
SECRET_RX = re.compile(
    r"(AKIA|ASIA)[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|AIza[A-Za-z0-9_\-]{35}|sk_live_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_\-]{40,}|-----BEGIN [A-Z ]*PRIVATE KEY-----")
COMMON = {"id", "fingerprint", "verdict", "title", "location", "counterevidence", "confidence"}


def lvl(x):
    return LEVELS.index(x) if x in LEVELS else None


def check_finding(f: dict, idx: int, errs: list[str]) -> None:
    p = f"findings[{idx}]({f.get('id', '?')})"
    for k in COMMON:
        if k not in f or f[k] in (None, ""):
            errs.append(f"{p}: falta '{k}'")
    if not re.fullmatch(r"HS-\d{3,}", str(f.get("id", ""))):
        errs.append(f"{p}: id debe ser HS-NNN")
    fp = str(f.get("fingerprint", ""))
    if fp and (not FP_RX.match(fp) or LINE_LIKE.search(fp)):
        errs.append(f"{p}: fingerprint inválido o contiene número de línea")
    v = f.get("verdict")
    if v not in VERDICTS:
        errs.append(f"{p}: verdict debe ser {sorted(VERDICTS)}")
        return
    loc = f.get("location") or {}
    if not isinstance(loc, dict) or not loc.get("file") or not isinstance(loc.get("line"), int) or loc.get("line", 0) < 1:
        errs.append(f"{p}: location requiere file y line >= 1")
    if f.get("confidence") not in {"high", "medium", "low"}:
        errs.append(f"{p}: confidence inválida")
    if f.get("status") is not None and f.get("status") not in STATUSES:
        errs.append(f"{p}: status inválido")
    if v == "confirmed":
        tr = f.get("trace") or []
        if len(tr) < 2:
            errs.append(f"{p}: confirmed requiere trace con >= 2 pasos")
        else:
            kinds = [t.get("kind") for t in tr]
            if kinds[0] != "entrypoint" or kinds[-1] != "sink" or "entrypoint" in kinds[1:] or "sink" in kinds[:-1]:
                errs.append(f"{p}: trace debe empezar en entrypoint y terminar en sink")
        if not f.get("evidence"):
            errs.append(f"{p}: confirmed requiere evidence")
        sev = f.get("severity") or {}
        li, im, ov = (sev.get("likelihood") or {}), (sev.get("impact") or {}), sev.get("overall")
        if lvl(li.get("score")) is None or lvl(im.get("score")) is None or lvl(ov) is None:
            errs.append(f"{p}: severity requiere likelihood.score, impact.score y overall válidos")
        else:
            if not li.get("reason") or not im.get("reason"):
                errs.append(f"{p}: likelihood e impact requieren reason")
            if lvl(ov) > lvl(im["score"]):
                errs.append(f"{p}: overall ({ov}) supera el impacto ({im['score']})")
            rs = f.get("review_severity")
            if rs and rs != REVIEW_MAP[ov]:
                errs.append(f"{p}: review_severity '{rs}' no coincide con el mapeo de '{ov}' -> '{REVIEW_MAP[ov]}'")
        if f.get("confidence") == "high" and f.get("reproduced") is not True:
            errs.append(f"{p}: confidence high exige reproduced: true")
        if not f.get("remediation"):
            errs.append(f"{p}: confirmed requiere remediation")
    else:
        if "severity" in f:
            errs.append(f"{p}: {v} no lleva severity")
        if v == "needs_validation":
            if not f.get("blockers"):
                errs.append(f"{p}: needs_validation requiere blockers no vacío")
            if not f.get("validation_plan"):
                errs.append(f"{p}: needs_validation requiere validation_plan")
        if v == "rejected":
            r = f.get("ruled_out_by") or {}
            if not r.get("control") or not r.get("location"):
                errs.append(f"{p}: rejected requiere ruled_out_by.control y .location")


def validate(doc: dict) -> list[str]:
    errs: list[str] = []
    if doc.get("schema") != "aegis-findings/1":
        errs.append("schema debe ser 'aegis-findings/1'")
    cov = doc.get("coverage")
    if not isinstance(cov, dict) or "evaluated" not in cov:
        errs.append("coverage.evaluated es obligatorio (declara qué se evaluó)")
    findings = doc.get("findings")
    if not isinstance(findings, list):
        errs.append("findings debe ser una lista")
        findings = []
    ids, fps = set(), set()
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            errs.append(f"findings[{i}] no es objeto")
            continue
        check_finding(f, i, errs)
        if f.get("id") in ids:
            errs.append(f"id duplicado {f.get('id')}")
        ids.add(f.get("id"))
        if f.get("fingerprint") in fps:
            errs.append(f"fingerprint duplicado {f.get('fingerprint')} (agrupa en un hallazgo)")
        fps.add(f.get("fingerprint"))
    raw = json.dumps(doc, ensure_ascii=False)
    if SECRET_RX.search(raw):
        errs.append("el documento contiene un valor con forma de secreto sin enmascarar")
    gv = doc.get("verdict")
    if gv not in GLOBAL:
        errs.append(f"verdict global debe ser {sorted(GLOBAL)}")
    else:
        open_states = {None, "abierto", "aceptado", "reabierto", "diferido"}
        blocking = [f for f in findings if isinstance(f, dict) and f.get("verdict") == "confirmed"
                    and lvl((f.get("severity") or {}).get("overall")) is not None
                    and lvl(f["severity"]["overall"]) >= 1 and f.get("status") in open_states]
        if gv.startswith("seguro") and blocking:
            errs.append(f"verdict '{gv}' incompatible con hallazgos medium+ abiertos: {[f['id'] for f in blocking]}")
        not_cov = (cov or {}).get("not_covered") if isinstance(cov, dict) else None
        if gv == "seguro" and not_cov:
            errs.append("verdict 'seguro' con unidades no cubiertas: usa 'no-concluyente' o justifica fuera de alcance")
    return errs


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print("uso: validate_findings.py <security-findings.json>", file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ilegible: {e}", file=sys.stderr)
        return 2
    errs = validate(doc) if isinstance(doc, dict) else ["la raíz debe ser un objeto"]
    for e in errs:
        print(e)
    if not errs:
        print("OK")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
