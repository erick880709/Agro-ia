#!/usr/bin/env python3
"""Validate cost evidence, deployment coverage and reproducible report blocks (stdlib).

Does not query providers or certify commercial rates. --sync-reports changes only
the explicitly delimited pricing blocks after the manifest passes validation.
"""
from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import html
import json
from pathlib import Path
import re

START = "<!-- archi-pricing:start -->"
END = "<!-- archi-pricing:end -->"
SCENARIOS = ("low", "expected", "high")
CADENCES = ("monthly", "one_time")


def number(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid decimal") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("expected finite nonnegative number")
    return result


def required_text(obj, key):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing text: {key}")
    if any(c in value for c in "|\r\n<>"):
        raise ValueError(f"unsafe table text: {key}")
    return value


def money(value):
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def load_manifest(raw):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(raw.decode("utf-8-sig"), parse_float=Decimal, object_pairs_hook=unique_keys)


def inventory(path):
    """Read the dedicated inventory section in 17, independent of the cost manifest."""
    text = path.read_text(encoding="utf-8-sig")
    section = re.search(r"^## Inventario de costos por ambiente\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not section:
        raise ValueError("17 lacks '## Inventario de costos por ambiente'")
    rows = []
    for line in section[1].splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            raise ValueError("inventory needs Ambiente | Proveedor | Recurso | Tratamiento | Justificación")
        if cells[0] == "Ambiente" or re.fullmatch(r"[-: ]+", cells[0]):
            continue
        env, provider, resource, treatment, reason = cells
        if not all(cells) or treatment not in ("costed", "excluded"):
            raise ValueError("invalid inventory row")
        rows.append((env, provider, resource, treatment, reason))
    if not rows or len({r[:3] for r in rows}) != len(rows):
        raise ValueError("empty or duplicate deployment inventory")
    return rows


def local_file(root, ref):
    path = (root / ref).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"missing or out-of-scope file: {ref}")
    return path


def calculate(manifest, root, today=None):
    """Return exact allocated totals or fail closed on invalid/incomplete evidence."""
    today = today or date.today()
    if type(manifest.get("version")) is not int or manifest["version"] != 1:
        raise ValueError("unsupported version")
    as_of = date.fromisoformat(required_text(manifest, "as_of"))
    age = manifest.get("max_price_age_days")
    if type(age) is not int or not 1 <= age <= 366:
        raise ValueError("max_price_age_days must be 1..366")
    if not 0 <= (today - as_of).days <= age:
        raise ValueError("estimate date is future or stale")
    currency = required_text(manifest, "currency")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("currency must be a three-letter code")
    required_text(manifest, "freshness_reason")
    environments = manifest.get("environments")
    if not isinstance(environments, list) or not environments or not all(isinstance(e, str) and e for e in environments):
        raise ValueError("environments must be nonempty strings")
    if len(set(environments)) != len(environments):
        raise ValueError("duplicate environments")
    for env in environments:
        required_text({"environment": env}, "environment")
        if env == "TOTAL":
            raise ValueError("TOTAL is reserved for report aggregates")
    deployment = local_file(root, required_text(manifest, "deployment"))
    rows = inventory(deployment)
    if {r[0] for r in rows} != set(environments):
        raise ValueError("environments differ from deployment inventory")
    expected = {r[:3] for r in rows if r[3] == "costed"}
    covered, seen_ids, meters = set(), set(), set()
    totals = {}
    items = manifest.get("items")
    if not isinstance(items, list) or (not items and expected):
        raise ValueError("items must cover costed inventory")
    for item in items:
        fields = {k: required_text(item, k) for k in (
            "id", "provider", "resource", "region", "sku", "meter", "unit",
            "cadence", "assumption", "category",
        )}
        if fields["id"] in seen_ids:
            raise ValueError("duplicate item id")
        seen_ids.add(fields["id"])
        if fields["cadence"] not in CADENCES:
            raise ValueError("invalid cadence")
        price, unit_size = number(item["unit_price"]), number(item["unit_size"])
        if unit_size == 0:
            raise ValueError("unit_size must be positive")
        quantities = item["quantity"]
        if set(quantities) != set(SCENARIOS):
            raise ValueError("quantity needs low, expected, high")
        quantities = {s: number(quantities[s]) for s in SCENARIOS}
        if not quantities["low"] <= quantities["expected"] <= quantities["high"]:
            raise ValueError("scenario quantities must be ordered")
        evidence = item["evidence"]
        kind = required_text(evidence, "kind")
        if kind not in ("public", "contractual", "observed", "approximation"):
            raise ValueError("invalid evidence kind")
        ref = required_text(evidence, "ref")
        checked = date.fromisoformat(required_text(evidence, "checked_on"))
        if checked > as_of or not 0 <= (today - checked).days <= age:
            raise ValueError(f"stale or future evidence: {fields['id']}")
        if kind in ("public", "approximation"):
            if not re.match(r"https?://[^/\s]+", ref):
                raise ValueError("public/approximate rate needs source URL")
        else:
            # Store a redacted evidence summary under architecture, never raw billing secrets.
            local_file(root, ref)
            required_text(evidence, "period")
        if kind == "approximation":
            required_text(evidence, "reason")
        allocations = item["allocations"]
        if not isinstance(allocations, dict) or not allocations or not set(allocations) <= set(environments):
            raise ValueError("unknown or empty environment allocations")
        fractions = {e: number(v) for e, v in allocations.items()}
        if any(v == 0 for v in fractions.values()) or sum(fractions.values()) != 1:
            raise ValueError("allocation fractions must be positive and sum to 1")
        for env, fraction in fractions.items():
            key = (env, fields["provider"], fields["resource"])
            if key not in expected:
                raise ValueError(f"item absent/excluded in deployment: {key}")
            covered.add(key)
            meter = key + (fields["region"], fields["sku"], fields["meter"], fields["cadence"])
            if meter in meters:
                raise ValueError(f"duplicate billing meter: {meter}")
            meters.add(meter)
            for scenario, quantity in quantities.items():
                total_key = (fields["provider"], env, fields["cadence"], scenario)
                totals[total_key] = totals.get(total_key, Decimal(0)) + quantity * price / unit_size * fraction
    if expected != covered:
        raise ValueError(f"unpriced deployment resources: {sorted(expected - covered)}")
    return totals


def report_block(manifest, totals, digest, is_html=False):
    rows = []
    providers = sorted({item["provider"] for item in manifest["items"]})
    for provider in providers:
        for cadence in CADENCES:
            for env in manifest["environments"] + ["TOTAL"]:
                values = [sum((totals.get((provider, e, cadence, s), Decimal(0)) for e in manifest["environments"]), Decimal(0))
                          if env == "TOTAL" else totals.get((provider, env, cadence, s), Decimal(0)) for s in SCENARIOS]
                rows.append([provider, env, cadence] + [money(v) for v in values])
    headers = ["Proveedor", "Ambiente", "Periodicidad", "Mínimo", "Esperado", "Alto"]
    note = f"{manifest['currency']} · {manifest['as_of']} · SHA-256 {digest}. Estimación; validación aritmética, no certificación de tarifas."
    if not providers:
        note += " Sin partidas: todos los recursos están excluidos con justificación en 17; revisar alcance antes de interpretar costo cero."
    if is_html:
        body = "<p>" + html.escape(note) + "</p>\n<table>\n<thead><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in headers) + "</tr></thead>\n<tbody>\n"
        body += "\n".join("<tr>" + "".join(f"<td>{html.escape(v)}</td>" for v in row) + "</tr>" for row in rows)
        body += "\n</tbody></table>"
    else:
        body = note + "\n\n| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n"
        body += "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return START + "\n" + body + "\n" + END


def check_manifest(path, sync=False):
    raw = path.read_bytes()
    manifest = load_manifest(raw)
    totals = calculate(manifest, path.parent)
    digest = hashlib.sha256(raw).hexdigest()
    reports = [local_file(path.parent, required_text(manifest, "pricing_report"))]
    if reports[0].suffix != ".md":
        raise ValueError("pricing_report must be Markdown")
    if len({i["provider"] for i in manifest["items"]}) > 1 and not manifest.get("html_report"):
        raise ValueError("multi-provider estimate needs html_report")
    if manifest.get("html_report"):
        reports.append(local_file(path.parent, required_text(manifest, "html_report")))
        if reports[-1].suffix != ".html":
            raise ValueError("html_report must be HTML")
    updates = []
    for report in reports:
        text = report.read_text(encoding="utf-8-sig")
        if text.count(START) != 1 or text.count(END) != 1 or text.index(START) >= text.index(END):
            raise ValueError(f"missing/duplicate report delimiters: {report.name}")
        block = report_block(manifest, totals, digest, report.suffix == ".html")
        current = text[text.index(START):text.index(END) + len(END)]
        if current != block and not sync:
            raise ValueError(f"report differs from cost manifest: {report.name}")
        updates.append((report, text.replace(current, block)))
    if sync:
        for report, text in updates:
            report.write_text(text, encoding="utf-8")
    return totals


def validate_directory(directory):
    errors = []
    manifests = list(directory.glob("17.4.1-Costos_*.json"))
    reports = list(directory.glob("17.4-Pricing_*.md"))
    for report in reports:
        name = report.name.replace("17.4-Pricing_", "17.4.1-Costos_").replace(".md", ".json")
        if not (directory / name).is_file():
            errors.append(f"{report.name}: missing structured cost manifest {name}")
    for path in manifests:
        try:
            data = load_manifest(path.read_bytes())
            expected = path.name.replace("17.4.1-Costos_", "17.4-Pricing_").replace(".json", ".md")
            if data.get("pricing_report") != expected:
                raise ValueError("manifest pricing_report must match its project filename")
            check_manifest(path)
        except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
            errors.append(f"{path.name}: {exc}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--sync-reports", action="store_true")
    args = parser.parse_args()
    try:
        totals = check_manifest(args.manifest, args.sync_reports)
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(f"OK: {len(totals)} totals checked; commercial price verification remains external")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
