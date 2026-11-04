#!/usr/bin/env python3
"""
Linter de antipatrones para suites Selenium en Java y Python.

Uso:
  python lint_selenium.py <ruta> [<ruta> ...] [--json]

Analiza *.java y *.py (excluye target/, build/, .venv/, node_modules/).
Reglas S1–S25 de resources/10-revision-y-antipatrones.md (las marcadas "L").
Código de salida: 1 si hay hallazgos Bloqueantes.
"""
import argparse
import signal
import json
import re
import sys
from pathlib import Path

SEV = {"Bloqueante": 0, "Mayor": 1, "Menor": 2}
EXCLUIR = {"target", "build", ".venv", "venv", "node_modules", ".git", "__pycache__"}


class F:
    def __init__(self, file, line, rule, sev, msg, fix):
        self.file, self.line, self.rule, self.sev, self.msg, self.fix = str(file), line, rule, sev, msg, fix


def strip_comments(src: str, lang: str) -> str:
    """Quita comentarios conservando líneas y strings (aprox. suficiente para lint)."""
    out, i, n, quote = [], 0, len(src), None
    while i < n:
        c = src[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1]); i += 2; continue
            if src.startswith(quote, i):
                out.append(quote[1:]); i += len(quote); quote = None; continue
            i += 1; continue
        if lang == "py" and (src.startswith('"""', i) or src.startswith("'''", i)):
            quote = src[i:i + 3]; out.append(quote); i += 3; continue
        if c in "'\"":
            quote = c; out.append(c); i += 1; continue
        if lang == "java" and src.startswith("//", i) or lang == "py" and c == "#":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if lang == "java" and src.startswith("/*", i):
            j = src.find("*/", i + 2); j = n if j < 0 else j + 2
            out.append("\n" * src.count("\n", i, j)); i = j; continue
        out.append(c); i += 1
    return "".join(out)


def block_end(text, brace):
    depth, i = 0, brace
    while i < len(text):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0: return i
        i += 1
    return len(text) - 1


def lint(path: Path):
    lang = "java" if path.suffix == ".java" else "py"
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = strip_comments(raw, lang)
    lines = text.split("\n")
    out = []
    add = lambda ln, r, s, m, f: out.append(F(path, ln, r, s, m, f))
    es_test = bool(re.search(r"(Test|Tests|IT)\.java$|^test_.*\.py$|_test\.py$", path.name))
    es_page = "pages" in path.parts or re.search(r"Page\.java$|_page\.py$", path.name)

    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if not s:
            continue
        # S1 esperas fijas
        if re.search(r"\bThread\.sleep\s*\(|\btime\.sleep\s*\(|\bsleep\s*\(\s*\d", s):
            add(i, "S1", "Mayor", "Espera fija (sleep)", "Esperar una condición con WebDriverWait/ExpectedConditions")
        # S2 implícitas
        m = re.search(r"implicitlyWait\s*\(\s*(Duration\.of\w+\(\s*(\d+)|(\d+))", s) or re.search(r"implicitly_wait\s*\(\s*(\d+(\.\d+)?)", s)
        if m:
            num = next((g for g in m.groups()[1:] if g), m.group(1))
            try:
                if float(re.sub(r"[^\d.]", "", num) or 0) > 0:
                    add(i, "S2", "Mayor", "Espera implícita > 0 (se mezcla con las explícitas y da tiempos impredecibles)",
                        "implicitlyWait(Duration.ZERO) / implicitly_wait(0) y solo esperas explícitas")
            except ValueError:
                pass
        # S3 XPath absoluto / posicional
        for xp in re.findall(r"""(?:By\.xpath\(|By\.XPATH\s*,|xpath\s*=)\s*["'](.+?)["']""", s):
            if xp.startswith("/html") or re.match(r"^/[a-z]", xp) or re.search(r"\[\d+\]", xp) and not re.search(r"td\[\d+\]\[normalize", xp):
                if not re.search(r"normalize-space|@id|@name|@data-|text\(\)|contains\(", xp) or xp.startswith("/html") or re.search(r"^\(.*\)\[\d+\]$", xp):
                    add(i, "S3", "Mayor", f"XPath absoluto o posicional: {xp[:60]}",
                        "Usar id/name/data-testid, CSS semántico o XPath por texto/etiqueta")
        # S4 clases generadas
        if re.search(r"""(css-[a-z0-9]{5,}|\bsc-[a-zA-Z]{5,}|\bjss\d+|ng-tns-c\d+|mat-input-\d+|ember\d{2,})""", s) and re.search(r"By\.|By\.CSS|By\.ID|By\.XPATH|\(By", s):
            add(i, "S4", "Mayor", "Localizador con clase/id autogenerado", "Atributo estable (data-testid) acordado con desarrollo")
        # S5 PageFactory
        if re.search(r"@FindBy\b|PageFactory\.initElements|@FindAll|@FindBys", s):
            add(i, "S5", "Menor", "PageFactory/@FindBy (proxies perezosos, más StaleElementReference)",
                "Campos By y búsqueda en el momento (resources/03 §5)")
        # S6 driver estático / compartido
        if lang == "java" and re.search(r"\bstatic\s+(?!final\s+ThreadLocal)(final\s+)?(WebDriver|RemoteWebDriver|ChromeDriver)\s+\w+\s*(;|=)", s):
            add(i, "S6", "Bloqueante", "WebDriver estático compartido: rompe la ejecución paralela y el aislamiento",
                "ThreadLocal<WebDriver> y un driver por test")
        if lang == "py" and re.search(r"@pytest\.fixture\(\s*scope\s*=\s*['\"](session|module|package)['\"]", s):
            nxt = " ".join(lines[i:i + 3])
            if re.search(r"def\s+\w*(driver|browser|navegador)\w*\s*\(", nxt):
                add(i, "S6", "Bloqueante", "Fixture de driver con alcance de sesión/módulo: tests comparten navegador",
                    "Alcance function (un navegador por test)")
        # S8 JS para clic / escritura
        if re.search(r"""execute_?[sS]cript\s*\(\s*("[^"]*(\.click\(\)|\.value\s*=)|'[^']*(\.click\(\)|\.value\s*=))""", s):
            add(i, "S8", "Mayor", "Clic/escritura vía JavaScript (salta la validación de interactuabilidad)",
                "Esperar elementToBeClickable y resolver lo que intercepta el clic")
        # S9 secretos
        if re.search(r"""(password|passwd|contrase(ñ|n)a|clave|secret|token|api_?key)\w*\s*[:=]\s*["'][^"'${}]{6,}["']""", s, re.I) \
                or re.search(r"""(By\.(name|id)\(\s*"(password|clave|contrasena)"\)\)\.sendKeys\(\s*"[^"]{4,}"\))""", s, re.I) \
                or re.search(r"""\(By\.(NAME|ID),\s*["'](password|clave)["']\)\)?\.send_keys\(\s*["'][^"']{4,}["']""", s, re.I):
            add(i, "S9", "Bloqueante", "Posible credencial/secreto literal en el código",
                "Leer de variables de entorno / vault; rotar si ya se publicó")
        # S10 URL absoluta
        if re.search(r"""\.(get|navigate\(\)\.to)\(\s*["']https?://(?!localhost|127\.0\.0\.1)""", s):
            add(i, "S10", "Mayor", "URL absoluta en driver.get", "Base URL desde configuración por ambiente")
        # S11 API Selenium 3
        if re.search(r"\.findElements?By(Id|Name|XPath|CssSelector|ClassName|TagName|LinkText)\s*\(|\bfind_elements?_by_\w+\s*\(|DesiredCapabilities\.(chrome|firefox|edge)\(\)|new\s+WebDriverWait\s*\(\s*\w+\s*,\s*\d+\s*\)|implicitlyWait\s*\(\s*\d+\s*,\s*TimeUnit|executable_path\s*=", s):
            add(i, "S11", "Bloqueante", "API de Selenium 3 (eliminada o deprecada en Selenium 4)",
                "Migrar a By/find_element(By.X), Options y Duration (resources/12 §1)")
        # S12 driver manual
        if re.search(r"""System\.setProperty\(\s*"webdriver\.(chrome|gecko|edge)\.driver"|WebDriverManager\.\w+\(\)""", s):
            add(i, "S12", "Menor", "Ruta de driver manual / WebDriverManager", "Selenium Manager (resources/01 §3)")
        # S13 excepciones tragadas
        if re.search(r"catch\s*\(\s*(final\s+)?(Exception|Throwable|WebDriverException|NoSuchElementException|TimeoutException)\s+\w+\s*\)\s*\{\s*(\}|//)", s) \
                or re.search(r"^except(\s+\w+(\s+as\s+\w+)?)?\s*:\s*pass\s*$", s):
            add(i, "S13", "Mayor", "Excepción tragada (el test sigue aunque algo falle)", "Dejar fallar o manejar con intención explícita")
        if lang == "py" and re.match(r"^except(\s+\w+(\s+as\s+\w+)?)?\s*:\s*$", s) and i < len(lines) and lines[i].strip() == "pass":
            add(i, "S13", "Mayor", "Excepción tragada (except: pass)", "Dejar fallar o manejar con intención explícita")
        # S15 aserciones pobres
        if re.search(r"assert(True|False)\s*\(\s*[^,;]*\.(equals|contains)\(", s):
            add(i, "S15", "Menor", "assertTrue(x.equals(y)): mensaje de fallo pobre", "assertThat(x).isEqualTo(y) / contains(...)")
        # S16 findElement en tests
        if es_test and not es_page and re.search(r"\b(driver|getDriver\(\))\.(findElements?|find_elements?)\s*\(", s):
            add(i, "S16", "Menor", "driver.findElement dentro del test", "Encapsular en un page object")
        # S17 aserciones en page objects
        if es_page and re.search(r"\b(assert(Equals|True|False|That|NotNull)|Assertions\.|assert\s+\w)", s):
            add(i, "S17", "Menor", "Aserción dentro de un page object", "Devolver el dato y afirmar en el test")
        # S19 orden
        if re.search(r"@Order\s*\(|@TestMethodOrder|dependsOnMethods\s*=|priority\s*=\s*\d|@pytest\.mark\.order|@pytest\.mark\.dependency", s):
            add(i, "S19", "Mayor", "Orden/dependencia entre tests", "Tests independientes con datos propios")
        # S20 deshabilitados sin motivo
        if re.search(r"@Disabled\s*$|@Disabled\(\s*\)|enabled\s*=\s*false|@Ignore\s*$|@pytest\.mark\.skip\s*$|@pytest\.mark\.skip\(\s*\)", s):
            add(i, "S20", "Menor", "Test deshabilitado sin motivo", "Agregar motivo y ticket: @Disabled(\"BUG-123: ...\")")
        # S21 reintentos
        if re.search(r"IRetryAnalyzer|retryAnalyzer\s*=|@RepeatedIfExceptionsTest|@pytest\.mark\.flaky|reruns\s*=", s):
            add(i, "S21", "Mayor", "Reintentos automáticos: pueden ocultar inestabilidad", "Investigar la causa (resources/07); reportar los que pasan al reintento")

    # S7 quit
    if lang == "java":
        if re.search(r"new\s+(Chrome|Firefox|Edge|Safari|RemoteWeb)Driver\s*\(", text) and not re.search(r"\.quit\(\)", text):
            add(1, "S7", "Mayor", "Se crea un WebDriver pero no hay quit() en el archivo (sesiones huérfanas)",
                "quit() en @AfterEach/@AfterMethod (o en la fábrica de drivers)")
    else:
        if re.search(r"webdriver\.(Chrome|Firefox|Edge|Remote)\s*\(", text) and not re.search(r"\.quit\(\)", text):
            add(1, "S7", "Mayor", "Se crea un WebDriver pero no hay quit() en el archivo", "yield driver; driver.quit() en la fixture")

    # S14 / S25 por test
    if lang == "java":
        for m in re.finditer(r"@(Test|ParameterizedTest)\b[^{;]*?\b(void)\s+(\w+)\s*\([^)]*\)[^{]*\{", text, re.S):
            name = m.group(3)
            ln = text.count("\n", 0, m.start(3)) + 1
            body = text[m.end() - 1:block_end(text, m.end() - 1)]
            if not re.search(r"\bassert|\bverify|\bexpect|should|Assertions|assertThat|fail\(", body):
                add(ln, "S14", "Bloqueante", f"Test sin aserciones: {name}()", "Afirmar el resultado esperado")
            ventana = text[max(0, m.start() - 400):m.start(3)]
            tiene_dn = "@DisplayName" in ventana.split("}")[-1] or "description" in ventana.split("}")[-1]
            if re.fullmatch(r"(test|prueba)\d*|test[A-Z]\w*\d+", name) and not tiene_dn:
                add(ln, "S25", "Menor", f"Nombre genérico sin trazabilidad: {name}()",
                    "@DisplayName(\"[HU-x][CA-y] comportamiento esperado\")")
    else:
        for m in re.finditer(r"^def\s+(test\w*)\s*\(", text, re.M):
            name = m.group(1)
            ln = text.count("\n", 0, m.start()) + 1
            nxt = re.search(r"^(def |class |@)", text[m.end():], re.M)
            body = text[m.end(): m.end() + (nxt.start() if nxt else len(text))]
            if not re.search(r"\bassert\b|pytest\.raises|expect\(|\.should", body):
                add(ln, "S14", "Bloqueante", f"Test sin aserciones: {name}()", "Agregar assert del resultado esperado")
            if re.fullmatch(r"test_?\d+|test_?(caso|prueba|login|ui)\d*", name):
                add(ln, "S25", "Menor", f"Nombre genérico sin trazabilidad: {name}()",
                    "test_hu245_ca1_<comportamiento> + docstring [HU-245][CA-1]")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rutas", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    files = []
    for r in a.rutas:
        p = Path(r)
        cands = [p] if p.is_file() else sorted(p.rglob("*"))
        for f in cands:
            if f.is_file() and f.suffix in (".java", ".py") and not (EXCLUIR & set(f.parts)) and f.name != "conftest.py" or (f.is_file() and f.name == "conftest.py"):
                if f.suffix in (".java", ".py") and not (EXCLUIR & set(f.parts)):
                    files.append(f)
    if not files:
        sys.exit("no se encontraron archivos .java o .py")
    findings = [x for f in files for x in lint(f)]
    findings.sort(key=lambda x: (SEV[x.sev], x.file, x.line))
    if a.json:
        print(json.dumps({"archivos": len(files), "hallazgos": [vars(f) for f in findings]}, ensure_ascii=False, indent=2))
    else:
        c = {s: sum(1 for f in findings if f.sev == s) for s in SEV}
        print(f"Selenium lint — {len(files)} archivo(s): {c['Bloqueante']} bloqueantes, {c['Mayor']} mayores, {c['Menor']} menores\n")
        for f in findings:
            print(f"[{f.sev}] {f.rule} {f.file}:{f.line} — {f.msg}\n    → {f.fix}")
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        pass
    sys.exit(1 if any(f.sev == "Bloqueante" for f in findings) else 0)


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # salida limpia con | head
    main()
