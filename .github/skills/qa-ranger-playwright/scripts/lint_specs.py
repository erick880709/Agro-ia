#!/usr/bin/env python3
"""
Revisa pruebas Playwright en TypeScript o JavaScript y reporta posibles errores.
Complementa ESLint con @typescript-eslint/no-floating-promises y eslint-plugin-playwright.
No ejecuta las pruebas ni reemplaza la revisión del código.

Uso:
  python lint_specs.py <ruta> [<ruta> ...] [--json] [--incluir-pages]

Analiza *.spec.ts|js, *.test.ts|js y *.setup.ts|js (y pages/fixtures con --incluir-pages).
Reglas P1–P25 de references/11-revision-y-antipatrones.md (las marcadas "L").
Código de salida: 1 si hay hallazgos Bloqueantes.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SEV = {"Bloqueante": 0, "Mayor": 1, "Menor": 2}

WEB_FIRST = (r"toBeVisible|toBeHidden|toBeAttached|toBeEnabled|toBeDisabled|toBeEditable|toBeEmpty|toBeChecked|"
             r"toBeFocused|toBeInViewport|toHaveText|toContainText|toHaveValues?|toHaveAttribute|toHaveCount|"
             r"toHaveClass|toContainClass|toHaveCSS|toHaveId|toHaveJSProperty|toHaveRole|toHaveAccessibleName|"
             r"toHaveAccessibleDescription|toHaveAccessibleErrorMessage|toHaveURL|toHaveTitle|toHaveScreenshot|"
             r"toMatchAriaSnapshot|toBeOK|toPass")
ACTIONS = (r"click|dblclick|fill|check|uncheck|selectOption|press|pressSequentially|type|hover|tap|focus|blur|clear|"
           r"setInputFiles|dragTo|drop|goto|reload|goBack|goForward|waitForURL|setChecked|scrollIntoViewIfNeeded")
READS = r"isVisible|isHidden|isEnabled|isDisabled|isChecked|isEditable|textContent|innerText|innerHTML|inputValue|getAttribute|count|allTextContents|allInnerTexts"


class F:
    def __init__(self, file, line, rule, sev, msg, fix):
        self.file, self.line, self.rule, self.sev, self.msg, self.fix = str(file), line, rule, sev, msg, fix


def strip_comments(src: str) -> str:
    """Elimina los comentarios sin cambiar los saltos de línea ni las cadenas de texto."""
    out, i, n = [], 0, len(src)
    quote = None
    while i < n:
        c = src[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1]); i += 2; continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c; out.append(c); i += 1; continue
        if src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("\n" * src.count("\n", i, j))
            i = j
            continue
        out.append(c); i += 1
    return "".join(out)


def statement_from(lines, idx, max_lines=8):
    buf = []
    for k in range(idx, min(idx + max_lines, len(lines))):
        buf.append(lines[k])
        if lines[k].rstrip().endswith(";") or (k > idx and re.match(r"^\s*(await|const|let|test|expect|\})", lines[k + 1] if k + 1 < len(lines) else "")):
            break
    return " ".join(buf)


def find_block(text, start):
    """Busca la '}' que cierra la '{' situada en start. Usa un análisis aproximado que omite las cadenas de texto."""
    depth, i, quote = 0, start, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                i += 2; continue
            if c == quote:
                quote = None
        elif c in "'\"`":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(text) - 1


def lint(path: Path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = strip_comments(raw)
    lines = text.split("\n")
    out = []
    is_setup = bool(re.search(r"\.setup\.[jt]s$", path.name))
    is_spec = bool(re.search(r"\.(spec|test|setup)\.[jt]sx?$", path.name))

    def add(ln, rule, sev, msg, fix):
        out.append(F(path, ln, rule, sev, msg, fix))

    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if not s:
            continue
        if re.search(r"\bwaitForTimeout\s*\(", s):
            add(i, "P1", "Mayor", "Espera fija con waitForTimeout",
                "Sincronizar con una aserción web-first, waitForURL o waitForResponse")
        if re.search(rf"expect(\.soft)?\(\s*await\s+[^;]*?\.({READS})\s*\(", s):
            add(i, "P2", "Mayor", "Aserción sin reintento: expect(await locator.<lectura>())",
                "Usar la aserción web-first: await expect(locator).toBeVisible()/toHaveText()/toHaveCount()...")
        if re.match(r"^expect(\.soft|\.poll)?\(", s):
            stmt = statement_from(lines, i - 1)
            if re.search(rf"\.(not\.)?({WEB_FIRST})\s*\(", stmt) or s.startswith("expect.poll("):
                add(i, "P3", "Bloqueante", "Aserción asíncrona sin await: nunca se evalúa y el test pasa igual",
                    "Agregar await: await expect(...)...")
        m = re.match(rf"^((?:page|this\.page|[a-zA-Z_$][\w$]*)(?:\.[\w$]+|\([^()]*\))*)\.({ACTIONS})\s*\(", s)
        # La acción puede estar dentro de await Promise.all([...]) o una lista de argumentos.
        # La coma o el cierre de la lista delimitan la acción. El await externo espera su promesa.
        nxt = next((l.strip() for l in lines[i:] if l.strip()), "")
        in_list = s.rstrip().endswith(",") or nxt.startswith(("]", ")"))
        if m and not in_list and not re.match(r"^(await|return|const|let|var)\b", s):
            add(i, "P4", "Bloqueante", f"Acción sin await: {s[:70]}",
                "Agregar await (y activar @typescript-eslint/no-floating-promises)")
        if "networkidle" in s:
            add(i, "P5", "Mayor", "Sincronización con networkidle (no fiable en apps con polling)",
                "Esperar el elemento o la respuesta concreta que el test necesita")
        if re.search(r"\bforce\s*:\s*true", s):
            add(i, "P6", "Mayor", "Acción forzada ({ force: true })",
                "Esperar la condición real (overlay oculto, elemento habilitado)")
        if re.search(r"""locator\(\s*['"`](xpath=|\(?//)""", s):
            add(i, "P7", "Mayor", "Locator XPath", "Usar getByRole/getByLabel/getByText/getByTestId")
        elif re.search(r"""locator\(\s*['"`][^'"`]*(nth-child|nth-of-type|\s>\s|:nth\(|\.css-[a-z0-9]{4,}|\.sc-[a-zA-Z]{5,}|\.jss\d+)""", s):
            add(i, "P7", "Mayor", "Locator CSS estructural o con clases generadas",
                "Usar locators accesibles o getByTestId")
        if re.search(r"\.(first|last)\(\)|\.nth\(\s*\d+\s*\)", s):
            add(i, "P8", "Menor", "Uso de first()/last()/nth(): verificar que el orden sea el comportamiento probado",
                "Si es para evitar strict mode, acotar el locator con filter({ hasText }) o un contenedor")
        if re.search(r"\bpage\.\$\$?\(|\belementHandle\b|\.waitForSelector\(|"
                     r"\bpage\.(click|dblclick|fill|type|check|uncheck|hover|press|tap|focus|textContent|innerText|"
                     r"innerHTML|getAttribute|inputValue|isVisible|isEnabled|isChecked|selectOption|setInputFiles)\(\s*['\"`]", s):
            add(i, "P9", "Mayor", "API legacy de selectores (page.$, waitForSelector, page.<acción>('selector'))",
                "Usar locators: page.getByRole(...).click()")
        if re.search(r"\b(test|it|describe)(\.describe)?\.only\s*\(", s):
            add(i, "P10", "Bloqueante", ".only en el código", "Quitar .only; activar forbidOnly en CI")
        if re.search(r"""\.goto\(\s*['"`]https?://(?!localhost|127\.0\.0\.1)""", s):
            add(i, "P11", "Mayor", "URL absoluta en goto",
                "Definir baseURL en playwright.config.ts y usar rutas relativas")
        if (re.search(r"""(password|passwd|contrase(ñ|n)a|clave|secret|token|api[_-]?key)\w*\s*[:=]\s*['"`][^'"`$]{6,}['"`]""", s, re.I)
                or re.search(r"""(contrase|password|clave|\bpin\b)[^;]*\)\.fill\(\s*['"`][^'"`$]{4,}['"`]""", s, re.I)
                or re.search(r"Bearer\s+[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{10,}", s)):
            add(i, "P12", "Bloqueante", "Posible secreto/credencial literal en el código",
                "Leer de process.env (y .env no versionado / secretos del pipeline); rotar si ya se publicó")
        if re.search(r"\bpage\.pause\s*\(", s):
            add(i, "P14", "Bloqueante", "page.pause() olvidado (bloquea la ejecución en CI)", "Quitar page.pause()")
        if re.search(r"describe\.serial|mode\s*:\s*['\"]serial['\"]", s):
            add(i, "P15", "Menor", "Modo serial: los tests dependen entre sí",
                "Hacer los tests independientes, unirlos en un test con test.step, o usar { lock } (1.63+) si es contención de un recurso")
        if re.search(r"""(locator|getBy\w+)\(\s*['"`][^'"`]*:visible""", s):
            add(i, "P17", "Menor", "Pseudo-clase :visible en selector", "Usar locator(...).visible() (1.63+)")
        if re.search(r"\b(videosPath|videoSize)\b|\.ariaRef\(", s):
            add(i, "P18", "Mayor", "API eliminada en Playwright 1.60 (videosPath/videoSize/ariaRef)",
                "Usar recordVideo / ariaSnapshot")
        if re.search(r"\.catch\(\s*\(\s*\w*\s*\)\s*=>\s*(\{\s*\}|undefined|null|false|true)\s*\)", s):
            add(i, "P19", "Mayor", "Error silenciado con .catch(() => {})",
                "Dejar que falle; si algo es opcional, controlar los datos para que el estado sea determinista")
        if re.search(rf"if\s*\(\s*!?\s*await\s+[^;{{]*?\.({READS})\s*\(", s):
            add(i, "P20", "Mayor", "El test se ramifica según el estado de la UI (if await ...isVisible())",
                "Hacer el estado determinista con datos/mocks controlados; separar en dos tests")
        if is_spec and re.match(r"^let\s+\w+", line):
            add(i, "P21", "Mayor", "Variable mutable a nivel de módulo: posible estado compartido entre tests",
                "Pasar estado por fixtures; cada test debe crear lo que necesita")

    # La regla P19 busca try/catch que rodeen aserciones o acciones.
    for m in re.finditer(r"\btry\s*\{", text):
        end = find_block(text, m.end() - 1)
        body = text[m.end():end]
        if re.search(rf"expect\(|\.({ACTIONS})\(", body) and re.match(r"\s*catch", text[end + 1:end + 20]):
            add(text.count("\n", 0, m.start()) + 1, "P19", "Mayor", "try/catch alrededor de acciones/aserciones",
                "Quitar el try/catch: un fallo debe hacer fallar el test")

    # Comprueba las reglas P13, P25 y P16 en cada bloque de prueba.
    titles = {}
    test_re = re.compile(r"""\b(test|it)(?:\.(?:fixme|fail|slow))?\(\s*(['"`])(.*?)\2\s*,""")
    for m in test_re.finditer(text):
        title = m.group(3)
        ln = text.count("\n", 0, m.start()) + 1
        brace = text.find("{", text.find("=>", m.end()))
        if brace < 0:
            continue
        body = text[brace:find_block(text, brace) + 1]
        if "fixme(" in m.group(0):
            continue
        if not is_setup and not re.search(r"\bexpect\b|toHaveScreenshot|\bassert|verificar|validar|comprobar", body):
            add(ln, "P13", "Bloqueante", f"Test sin aserciones: '{title}'",
                "Agregar la aserción del resultado esperado (await expect(...))")
        clean = re.sub(r"\[[^\]]*\]|\$\{[^}]*\}", "x", title).strip()
        if len(clean) < 10 or re.match(r"(?i)^(test|prueba|caso|should work|works|deber[ií]a funcionar)\b\s*\d*$", clean):
            add(ln, "P25", "Menor", f"Título poco descriptivo: '{title}'",
                "Describir el comportamiento esperado e incluir el ID: [HU-x][CA-y] rechaza ...")
        if title in titles and "${" not in title:
            add(ln, "P25", "Menor", f"Título duplicado en el archivo (línea {titles[title]}): '{title}'",
                "Los títulos deben ser únicos (reportes, reintentos y trazabilidad)")
        titles.setdefault(title, ln)

    for m in re.finditer(r"\b(test\.)?beforeEach\(\s*async", text):
        arrow = text.find("=>", m.end())
        brace = text.find("{", arrow) if arrow >= 0 else -1
        if brace < 0:
            continue
        end = find_block(text, brace)
        body = text[brace + 1:end]
        if re.search(r"(contrase|password|clave)", body, re.I) and re.search(r"\.fill\(", body):
            add(text.count("\n", 0, m.start()) + 1, "P16", "Mayor", "Login por UI en beforeEach",
                "Autenticar una vez en un proyecto setup y reutilizar storageState (references/04)")

    return out


def main():
    # Usa UTF-8 para conservar los acentos y símbolos del reporte en Windows.
    # La salida cp1252 puede fallar al imprimir caracteres como → o ✅.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rutas", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--incluir-pages", action="store_true", help="analizar también pages/ y fixtures/")
    args = ap.parse_args()

    pat = re.compile(r"\.(spec|test|setup)\.[jt]sx?$")
    files = []
    for r in args.rutas:
        p = Path(r)
        cands = [p] if p.is_file() else sorted(p.rglob("*"))
        for f in cands:
            if not f.is_file() or "node_modules" in f.parts:
                continue
            if pat.search(f.name) or (args.incluir_pages and f.suffix in (".ts", ".js")
                                      and {"pages", "fixtures"} & set(f.parts)):
                files.append(f)
    if not files:
        sys.exit("no se encontraron specs (*.spec.ts, *.test.ts, *.setup.ts)")

    findings = []
    for f in files:
        findings += lint(f)
    findings.sort(key=lambda x: (SEV[x.sev], x.file, x.line))

    if args.json:
        print(json.dumps({"archivos": len(files), "hallazgos": [vars(f) for f in findings]}, ensure_ascii=False, indent=2))
    else:
        c = {s: sum(1 for f in findings if f.sev == s) for s in SEV}
        print(f"Playwright lint — {len(files)} archivo(s): {c['Bloqueante']} bloqueantes, {c['Mayor']} mayores, {c['Menor']} menores\n")
        for f in findings:
            print(f"[{f.sev}] {f.rule} {f.file}:{f.line} — {f.msg}\n    → {f.fix}")
    sys.exit(1 if any(f.sev == "Bloqueante" for f in findings) else 0)


if __name__ == "__main__":
    main()
