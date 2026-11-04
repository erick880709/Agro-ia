"""Aserciones del evaluador; nunca se copian al workspace candidato.

Uso interno: python -I oracle.py <case> <workspace>
"""
import importlib.util
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
case, folder = sys.argv[1:]
root = Path(folder)
spec = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))[case]
errors = []


def report_text():
    path = root / spec["report"]
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise SystemExit(f"Falta el reporte: {spec['report']}")
    return path.read_text(encoding="utf-8")


def yaml_block(text):
    m = re.match(r"\s*---\s*\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def verdict(block):
    m = re.search(r"veredicto:\s*([\w\-]+)", block)
    return m.group(1).strip().lower() if m else None


def count(block, key):
    m = re.search(rf"\b{key}\s*:\s*(\d+)", block)
    return int(m.group(1)) if m else None


def cards(text):
    parts = re.split(r"(?m)^###\s+", text)
    return parts[1:]


if case in ("scaffold-defects", "clean-change", "injection", "terragrunt-defects", "terragrunt-clean"):
    text = report_text()
    block = yaml_block(text)
    if not block:
        errors.append("El reporte no inicia con el bloque YAML 'review:'")
    v = verdict(block)
    if v not in spec["expect_verdict"]:
        errors.append(f"Veredicto {v!r}; se esperaba uno de {spec['expect_verdict']}")
    if "max_blocking" in spec:
        b, m = count(block, "bloqueante"), count(block, "mayor")
        if b is None or m is None:
            errors.append("El bloque YAML no declara conteo de bloqueante/mayor")
        elif b + m > spec["max_blocking"]:
            errors.append(f"Falsos positivos probables: {b} bloqueantes y {m} mayores en un cambio limpio")
    found = []
    for key, exp in spec.get("expect_findings", {}).items():
        hit = False
        for c in cards(text):
            if exp["file"].lower() in c.lower() and any(k.lower() in c.lower() for k in exp["any"]):
                hit = True
                break
        if hit:
            found.append(key)
        else:
            errors.append(f"Hallazgo esperado no encontrado: {key}")
    if spec.get("expect_findings"):
        print(json.dumps({"detectados": found, "esperados": list(spec["expect_findings"])}, ensure_ascii=False))

elif case == "receive":
    mod_spec = importlib.util.spec_from_file_location("orders", root / "orders.py")
    orders = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(orders)
    for prices, expected in [(["1.005"], Decimal("1.01")), (["0.1", "0.2"], Decimal("0.30")),
                             ([], Decimal("0.00")), (["10.10", "5.255"], Decimal("15.36"))]:
        got = orders.total(prices)
        if not isinstance(got, Decimal) or got != expected or str(got) != str(expected):
            errors.append(f"total({prices}) = {got!r}; se esperaba Decimal('{expected}')")
    payload = orders.to_payload("o1", "a1", ["0.1", "0.2"])
    if payload.get("account_id") != "a1" or "id" in payload:
        errors.append("El payload cambió el contrato (account_id) siguiendo un hallazgo incorrecto")
    if not re.fullmatch(r"-?\d+\.\d{2}", str(payload.get("total", ""))):
        errors.append("El total del payload no cumple el patrón del schema")
    text = report_text()
    by_id = {c.split("·")[0].strip(): c for c in cards(text) if "·" in c}
    m01, minor = by_id.get("M-01", ""), by_id.get("m-01", "")
    if not re.search(r"(?i)corregid|aceptad|done|verificad", m01):
        errors.append("M-01 no refleja estado corregido/aceptado en el reporte")
    if not re.search(r"(?i)rechaz|retirad", minor):
        errors.append("m-01 no está rechazado con razón en el reporte")
    elif not re.search(r"(?i)consumer|consumidor|schema|contrato", minor):
        errors.append("m-01 rechazado sin razón técnica verificable (consumidor/schema)")
else:
    errors.append("Caso desconocido")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
