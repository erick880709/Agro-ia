#!/usr/bin/env python3
"""Convierte security-findings.json (aegis-findings/1) a SARIF 2.1.0.

Uso: python to_sarif.py security-findings.json -o security.sarif [--include-needs-validation]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEVEL = {"critical": "error", "high": "error", "medium": "warning", "low": "note"}
SCORE = {"critical": "9.5", "high": "8.0", "medium": "5.5", "low": "3.0"}


def convert(doc: dict, include_nv: bool = False) -> dict:
    rules, results, seen = [], [], set()
    for f in doc.get("findings", []):
        v = f.get("verdict")
        if v == "rejected" or (v == "needs_validation" and not include_nv):
            continue
        rid = f.get("cwe") or f.get("fingerprint", "aegis")
        if rid not in seen:
            seen.add(rid)
            rule = {"id": rid, "name": rid.replace("-", ""), "shortDescription": {"text": f.get("title", rid)},
                    "properties": {"tags": ["security"] + ([f["owasp_category"]] if f.get("owasp_category") else [])}}
            if v == "confirmed":
                rule["properties"]["security-severity"] = SCORE.get(f["severity"]["overall"], "5.0")
            rules.append(rule)
        loc = f.get("location", {})
        level = LEVEL.get((f.get("severity") or {}).get("overall"), "warning") if v == "confirmed" else "note"
        text = f.get("title", "")
        if f.get("remediation"):
            text += f" — Remedio: {f['remediation']}"
        if v == "needs_validation":
            text += " — Necesita validación: " + "; ".join(f.get("blockers", []))
        res = {
            "ruleId": rid, "level": level, "message": {"text": text},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": loc.get("file", "")},
                                                "region": {"startLine": int(loc.get("line", 1))}}}],
            "partialFingerprints": {"aegisFingerprint/v1": f.get("fingerprint", "")},
            "properties": {"aegisId": f.get("id"), "verdict": v, "confidence": f.get("confidence"),
                           "reviewSeverity": f.get("review_severity")},
        }
        if f.get("trace"):
            res["codeFlows"] = [{"threadFlows": [{"locations": [
                {"location": {"physicalLocation": {"artifactLocation": {"uri": t["file"]}, "region": {"startLine": int(t["line"])}},
                              "message": {"text": f"{t['kind']}: {t.get('description', '')}"}}} for t in f["trace"]]}]}]
        results.append(res)
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "aegis", "informationUri": "https://owasp.org/Top10/", "rules": rules}},
                      "results": results}]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("findings")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--include-needs-validation", action="store_true")
    a = ap.parse_args(argv)
    try:
        doc = json.loads(Path(a.findings).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ilegible: {e}", file=sys.stderr)
        return 2
    sarif = convert(doc, a.include_needs_validation)
    Path(a.output).write_text(json.dumps(sarif, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(sarif['runs'][0]['results'])} resultados -> {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
