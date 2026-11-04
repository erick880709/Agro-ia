#!/usr/bin/env python3
"""Valida db-findings.json / 16.00.1-Observaciones-Datos (contrato dba-findings/1).

Uso: python validate_findings.py <archivo.json> [--archi]
  --archi  exige disposición de archi y que no queden bloqueantes/mayores sin cerrar.
Salida: 0 válido, 1 inválido, 2 ilegible.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SEVERITIES = {"bloqueante", "mayor", "menor", "nit", "pregunta"}
CONFIDENCE = {"alta", "media", "baja"}
CATEGORIES = {"modelo-integridad", "consulta-indice", "transaccion-concurrencia", "migracion",
              "operacion-disponibilidad", "seguridad-datos", "costo-capacidad", "nosql-acceso", "procedimiento"}
STATUS = {"abierto", "corregido", "verificado", "reabierto", "retirado"}
DISPOSITION = {"pendiente", "incorporada", "rechazada-justificada", "riesgo-aceptado", "diferida"}
VERDICTS = {"aprobado", "aprobado-con-observaciones", "cambios-requeridos", "no-concluyente"}
FP = re.compile(r"^[A-Za-z0-9._:/@+\-]{3,200}$")
LINE_LIKE = re.compile(r"(^|[:/])\d+($|[:/])")
CRED = re.compile(r"://[^\s:@/]+:(?!\*|…)[^\s@/'\"]{3,}@|password\s*=\s*[^;\s*…\"]{4,}", re.I)
OPEN = {"abierto", "reabierto", None}


def validate(doc: dict, archi: bool = False) -> list[str]:
    e: list[str] = []
    if doc.get("schema") != "dba-findings/1":
        e.append("schema debe ser 'dba-findings/1'")
    if not doc.get("engines"):
        e.append("engines es obligatorio (motor y versión antes de opinar)")
    fs = doc.get("findings")
    if not isinstance(fs, list):
        return e + ["findings debe ser lista"]
    ids, fps = set(), set()
    for i, f in enumerate(fs):
        p = f"findings[{i}]({f.get('id', '?')})"
        if not re.fullmatch(r"DB-\d{3,}", str(f.get("id", ""))):
            e.append(f"{p}: id debe ser DB-NNN")
        if f.get("id") in ids:
            e.append(f"{p}: id duplicado")
        ids.add(f.get("id"))
        fp = str(f.get("fingerprint", ""))
        if not FP.match(fp) or LINE_LIKE.search(fp):
            e.append(f"{p}: fingerprint inválido o con número de línea")
        if fp in fps:
            e.append(f"{p}: fingerprint duplicado (agrupa en una observación)")
        fps.add(fp)
        sev = f.get("severity")
        if sev not in SEVERITIES:
            e.append(f"{p}: severity inválida")
        if f.get("category") not in CATEGORIES:
            e.append(f"{p}: category inválida")
        conf = f.get("confidence")
        if conf not in CONFIDENCE:
            e.append(f"{p}: confidence inválida")
        if not f.get("title") or not f.get("location"):
            e.append(f"{p}: requiere title y location")
        if sev in ("bloqueante", "mayor"):
            for k in ("scenario", "evidence", "remediation", "verification"):
                if not f.get(k):
                    e.append(f"{p}: {sev} requiere '{k}'")
            if conf == "baja":
                e.append(f"{p}: confianza baja no puede ser {sev} (convertir en pregunta)")
        if sev == "pregunta" and not f.get("resolution_query"):
            e.append(f"{p}: pregunta requiere resolution_query (cómo obtener el dato)")
        st = f.get("status")
        if st is not None and st not in STATUS:
            e.append(f"{p}: status inválido")
        d = f.get("disposition")
        if d is not None and d not in DISPOSITION:
            e.append(f"{p}: disposition inválida")
        if d in ("rechazada-justificada", "riesgo-aceptado") and not f.get("disposition_note"):
            e.append(f"{p}: disposition '{d}' requiere disposition_note")
        if d == "diferida" and sev in ("bloqueante", "mayor"):
            e.append(f"{p}: un {sev} no puede quedar 'diferida'")
        if archi and sev in ("bloqueante", "mayor") and st not in ("verificado", "retirado") and d in (None, "pendiente", "diferida"):
            e.append(f"{p}: {sev} sin disposición de archi (pendiente)")
    if CRED.search(json.dumps(doc, ensure_ascii=False)):
        e.append("el documento contiene credenciales sin enmascarar")
    v = doc.get("verdict")
    if v not in VERDICTS:
        e.append("verdict inválido")
    else:
        open_blocking = [f["id"] for f in fs if isinstance(f, dict) and f.get("severity") in ("bloqueante", "mayor")
                         and f.get("status") in OPEN and f.get("disposition") not in ("incorporada", "rechazada-justificada", "riesgo-aceptado")]
        if v.startswith("aprobado") and open_blocking:
            e.append(f"verdict '{v}' incompatible con bloqueantes/mayores abiertos: {open_blocking}")
    return e


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    archi = "--archi" in argv
    args = [x for x in argv if x != "--archi"]
    if len(args) != 1:
        print("uso: validate_findings.py <archivo.json> [--archi]", file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as ex:
        print(f"ilegible: {ex}", file=sys.stderr)
        return 2
    errs = validate(doc, archi) if isinstance(doc, dict) else ["raíz debe ser objeto"]
    print("\n".join(errs) if errs else "OK")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
