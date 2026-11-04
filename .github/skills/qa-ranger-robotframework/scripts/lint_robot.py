#!/usr/bin/env python3
"""
Linter de antipatrones para suites Robot Framework (.robot / .resource).

Uso:
  python lint_robot.py <ruta> [<ruta> ...] [--json] [--rf 7] [--sin-trazabilidad]

No requiere Robot Framework instalado: usa un parser propio del formato de
espacios (2+ espacios, tabulador o formato con barras). Reglas R1–R29 de
resources/10-revision-y-antipatrones.md (las marcadas "L").

  --rf N               Versión mayor de Robot Framework del proyecto (por defecto 7).
                       Con --rf 6 no se sugiere VAR (requiere RF 7.0).
  --sin-trazabilidad   No exige ID de caso y prioridad en el nombre (R7); úsalo
                       solo para suites que no forman parte de un plan QA.

Código de salida: 1 si hay hallazgos Bloqueantes (sirve como gate de CI).
Complementa, no sustituye, a `robot --dryrun` y a Robocop.
"""
import argparse
import json
import re
import signal
import sys
from pathlib import Path

SEV = {"Bloqueante": 0, "Mayor": 1, "Menor": 2}
EXCLUIR = {".git", ".venv", "venv", "node_modules", "results", "resultados", "__pycache__", "output"}
SECCION = re.compile(r"^\*+\s*(settings?|variables?|test cases?|tasks?|keywords?|comments?)\s*\**\s*$", re.I)
SEP = re.compile(r" {2,}|\t+|\s+\|\s+")
CASO_ID = re.compile(r"^(TC|SEC|FRAUD|API|A11Y|UT|PERF)-\d+\b")
PRIORIDAD = re.compile(r"\[(critical|high|medium|low)\]", re.I)
PRIO_TAG = {"critical", "high", "medium", "low"}
CONTROL = {"FOR", "END", "IF", "ELSE", "ELSE IF", "WHILE", "TRY", "EXCEPT", "FINALLY", "BREAK",
           "CONTINUE", "RETURN", "VAR", "GROUP", "IN", "IN RANGE", "IN ENUMERATE", "IN ZIP"}
BDD = re.compile(r"^(given|when|then|and|but)\s+", re.I)
# Palabras clave que verifican un resultado (librerías estándar y habituales).
ASERCION = re.compile(
    r"^(should\b|.*\bshould (be|contain|not|match|exist|start|end)\b|check (row count|query result|if (not )?exists)|"
    r"table must exist|row count is|status should be|request should be|wait until (element|page|location|title|keyword)|"
    r"wait for (elements state|condition|response|request|load state|function)|"
    r"(element|page|title|location|checkbox|list|textfield|textarea|frame|alert|radio button|table)\b.*\bshould\b|"
    r"get (text|title|url|element count|attribute|property|checkbox state|element states|style|classes|value|selected options|browser catalog)\b|"
    r"validate|fail|pass execution if|verify|expect|assert|run keyword and expect error|"
    r"dictionary should|list should|lists should|dictionaries should|output should|file should|directory should|"
    r"variable should|keyword should|length should)",
    re.I)
OPERADOR = {"==", "!=", "<", ">", "<=", ">=", "contains", "not contains", "equal", "equals", "should be",
            "should not be", "starts", "should start with", "ends", "should end with", "matches", "validate",
            "then", "inequal", "*=", "^=", "$=", "!=", "evaluate"}
SQL_KW = {"query", "execute sql string", "check row count", "check query result", "row count",
          "check if exists in database", "check if not exists in database", "row count is 0",
          "row count is equal to x", "row count is greater than x", "row count is less than x"}
OS_ENV = {"USER", "USERNAME", "HOME", "PATH", "HOSTNAME", "SHELL", "PWD", "LANG", "TMP", "TEMP", "LOGNAME", "HOST"}
LOCALIZADOR = re.compile(r"^(id|name|css|xpath|role|text|data|class|tag|link|partial link|dom|accessibility_id)\s*[:=]|^//|^\(//|^#|^\.", re.I)
SECRETO = re.compile(r"(password|passwd|contrase(ñ|n)a|clave|secret|token|api_?key|db_password)", re.I)


class F:
    def __init__(self, file, line, rule, sev, msg, fix):
        self.file, self.line, self.rule, self.sev, self.msg, self.fix = str(file), line, rule, sev, msg, fix


def norm(name: str) -> str:
    return re.sub(r"[\s_]+", "", name).lower()


def cells_of(line: str):
    """Divide una línea en celdas; corta comentarios no escapados."""
    if line.lstrip().startswith("|"):
        line = line.strip().strip("|")
    raw = SEP.split(line.rstrip("\n"))
    out = []
    for c in raw:
        if c.startswith("#"):
            break
        out.append(c)
    return out


class Paso:
    def __init__(self, line, cells):
        self.line, self.cells = line, cells

    @property
    def keyword(self):
        """Nombre de la keyword llamada (sin asignaciones ni prefijo BDD), o el control."""
        cs = [c for c in self.cells if c]
        while cs and re.fullmatch(r"[$@&]\{[^}]+\}\s*=?", cs[0]):
            cs = cs[1:]
        if not cs:
            return ""
        return BDD.sub("", cs[0]) if not cs[0].startswith("[") else cs[0]

    @property
    def args(self):
        cs = [c for c in self.cells if c]
        while cs and re.fullmatch(r"[$@&]\{[^}]+\}\s*=?", cs[0]):
            cs = cs[1:]
        return cs[1:]

    @property
    def asigna(self):
        return bool(self.cells and re.fullmatch(r"[$@&]\{[^}]+\}\s*=?", self.cells[0]))


class Bloque:
    def __init__(self, kind, name, line):
        self.kind, self.name, self.line, self.pasos, self.settings = kind, name, line, [], {}


class Archivo:
    def __init__(self, path: Path):
        self.path = path
        self.settings, self.variables, self.bloques = [], [], []
        self.parse(path.read_text(encoding="utf-8", errors="replace").split("\n"))

    def parse(self, lines):
        seccion, actual, prev = None, None, None
        for i, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            m = SECCION.match(line.strip())
            if m:
                s = m.group(1).lower()
                seccion = ("settings" if s.startswith("setting") else "variables" if s.startswith("variable")
                           else "tests" if s.startswith(("test", "task")) else "keywords" if s.startswith("keyword")
                           else "comments")
                actual, prev = None, None
                continue
            if seccion in (None, "comments"):
                continue
            indent = bool(re.match(r"^(\s|\|\s+\|)", line))
            cells = cells_of(line)
            if line.lstrip().startswith("#") or not any(c.strip() for c in cells):
                continue
            if indent:
                cells = [c.strip() for c in cells if c.strip() != ""] if not line.lstrip().startswith("|") else [c.strip() for c in cells[1:]]
            else:
                cells = [c.strip() for c in cells]
            if cells and cells[0] == "...":
                if prev is not None:
                    prev.cells.extend(c for c in cells[1:] if c)
                continue
            if seccion == "settings":
                prev = Paso(i, [c for c in cells if c]); self.settings.append(prev); continue
            if seccion == "variables":
                prev = Paso(i, [c for c in cells if c]); self.variables.append(prev); continue
            if not indent:
                actual = Bloque("test" if seccion == "tests" else "keyword", cells[0], i)
                self.bloques.append(actual)
                resto = [c for c in cells[1:] if c]
                prev = None
                if resto and actual:
                    prev = Paso(i, resto); actual.pasos.append(prev)
                continue
            if actual is None:
                continue
            cells = [c for c in cells if c]
            if not cells:
                continue
            if re.fullmatch(r"\[[A-Za-z ]+\]", cells[0]):
                actual.settings[cells[0].lower()] = Paso(i, cells)
                prev = actual.settings[cells[0].lower()]
                continue
            prev = Paso(i, cells)
            actual.pasos.append(prev)

    def setting(self, name):
        return [s for s in self.settings if s.cells and norm(s.cells[0]) == norm(name)]

    @property
    def template(self):
        return bool(self.setting("Test Template") or self.setting("Task Template"))


def keyword_regex(name: str):
    """Convierte un nombre con argumentos embebidos en regex normalizado."""
    parts = re.split(r"\$\{[^}]+\}", name)
    return re.compile("^" + ".+?".join(re.escape(norm(p)) for p in parts) + "$")


def construir_indice(archivos):
    """Mapea keywords de usuario a si verifican algo (directa o transitivamente)."""
    defs = []
    for a in archivos:
        for b in a.bloques:
            if b.kind == "keyword":
                defs.append((keyword_regex(b.name), b))
    cache = {}

    def buscar(nombre):
        n = norm(nombre)
        for rx, b in defs:
            if rx.match(n):
                return b
        return None

    def verifica(b, pila=()):
        if id(b) in cache:
            return cache[id(b)]
        if id(b) in pila:
            return False
        r = False
        for p in b.pasos:
            if paso_verifica(p, lambda k: verifica_nombre(k, pila + (id(b),))):
                r = True
                break
        cache[id(b)] = r
        return r

    def verifica_nombre(nombre, pila=()):
        b = buscar(nombre)
        return bool(b and verifica(b, pila))

    return buscar, verifica_nombre


def paso_verifica(p: Paso, verifica_nombre) -> bool:
    k = p.keyword
    if not k or k.upper() in CONTROL:
        # Las ramas de un IF/FOR quedan como pasos propios; el control en sí no verifica.
        return False
    if ASERCION.match(k):
        if re.match(r"^get ", k, re.I):
            return any(a.strip().lower() in OPERADOR for a in p.args)
        return True
    if re.match(r"run keyword and ignore error$", k, re.I):
        return False  # el fallo se descarta: no acredita verificación
    if re.match(r"run keyword( and return status)?$|wait until keyword succeeds|repeat keyword", k, re.I):
        inner = [a for a in p.args if not re.fullmatch(r"\d+x?|\d+(\.\d+)?\s*(s|sec|seconds?|ms|min)", a, re.I)]
        return bool(inner) and (bool(ASERCION.match(inner[0])) or verifica_nombre(inner[0]))
    return verifica_nombre(k)


def lint_archivo(a: Archivo, verifica_nombre, opts):
    out = []
    add = lambda ln, r, s, m, f: out.append(F(a.path, ln, r, s, m, f))
    es_suite = a.path.suffix == ".robot"
    texto = a.path.read_text(encoding="utf-8", errors="replace")

    # Encabezados en singular / legados (R2)
    for i, line in enumerate(texto.split("\n"), start=1):
        m = re.match(r"^\*+\s*(Setting|Variable|Test Case|Keyword|Task)\s*\**\s*$", line.strip(), re.I)
        if m:
            add(i, "R2", "Mayor", f"Encabezado en singular '{line.strip()}' (obsoleto desde RF 6.0)",
                "Usar *** Settings *** / *** Test Cases *** / *** Keywords *** (plural)")

    # Settings
    librerias = {}
    for s in a.settings:
        k = norm(s.cells[0]) if s.cells else ""
        if k in ("forcetags", "defaulttags"):
            add(s.line, "R2", "Mayor", f"'{s.cells[0]}' es sintaxis heredada",
                "Test Tags en Settings y [Tags]    -tag para excluir (RF 6.0+)")
        if k == "library" and len(s.cells) > 1:
            lib = s.cells[1]
            librerias[lib] = s
            if any(c.upper() == "WITH NAME" for c in s.cells):
                add(s.line, "R2", "Mayor", "'WITH NAME' es heredado", "Usar AS (RF 6.0+)")
            if lib == "SeleniumLibrary":
                for c in s.cells[2:]:
                    m = re.match(r"implicit_wait\s*=\s*([\d.]+)", c)
                    if m and float(m.group(1)) > 0:
                        add(s.line, "R8", "Mayor", "SeleniumLibrary con implicit_wait > 0",
                            "implicit_wait=0s y esperas explícitas Wait Until ...")
            if lib == "DatabaseLibrary" and not any(re.match(r"log_query_results\s*=\s*(False|\$\{False\})", c, re.I) for c in s.cells[2:]):
                add(s.line, "R22", "Menor", "DatabaseLibrary registra las filas consultadas en log.html",
                    "log_query_results=False (o Set Logging Query Results) si hay datos personales/financieros")
    if "Browser" in librerias and "SeleniumLibrary" in librerias:
        add(librerias["Browser"].line, "R26", "Mayor", "Browser y SeleniumLibrary importadas en la misma suite",
            "Una librería web por suite; separar o migrar (resources/14)")

    # Variables con secretos literales (R4)
    for v in a.variables:
        if len(v.cells) >= 2 and SECRETO.search(v.cells[0]) and not re.search(r"[$%&@]\{", " ".join(v.cells[1:])) \
                and v.cells[1] not in ("${EMPTY}", "None", "${NONE}") and len(v.cells[1]) >= 4 \
                and not LOCALIZADOR.match(v.cells[1]):
            add(v.line, "R4", "Bloqueante", f"Secreto literal en Variables: {v.cells[0]}",
                "Leer de variable de entorno %{NOMBRE} o del vault del pipeline; rotar si ya se publicó")

    # R21 / R29 variables de entorno en la sección Variables
    tiene_guarda = "verificarvariablesdeentorno" in norm(texto)
    for v in a.variables:
        for env in re.findall(r"%\{([A-Za-z_][A-Za-z0-9_]*)", " ".join(v.cells[1:])):
            if env.upper() in OS_ENV and not tiene_guarda:
                add(v.line, "R21", "Menor", f"%{{{env}}} coincide con una variable del sistema operativo",
                    "Si el pipeline no inyecta el valor, Robot usa el del agente sin fallar: validar con una keyword de guarda (resources/08 §4)")
            if env != env.upper():
                add(v.line, "R29", "Mayor", f"%{{{env}}} en minúscula: en agentes Linux Azure DevOps la expone como %{{{env.upper()}}}",
                    f"Usar %{{{env.upper()}}} (resources/08 §2)")

    usa_template = a.template
    vistos = {}
    for b in a.bloques:
        if b.kind == "test":
            nombre = b.name
            n = norm(nombre)
            if n in vistos:
                add(b.line, "R25", "Mayor", f"Nombre de test duplicado: '{nombre}'", "Nombres únicos por suite (RF los renombra y rompe la trazabilidad)")
            vistos[n] = b
            # R7 trazabilidad
            if not opts.sin_trazabilidad:
                tags = [t.lower() for t in (b.settings.get("[tags]").cells[1:] if b.settings.get("[tags]") else [])]
                suite_tags = [t.lower() for s in a.setting("Test Tags") for t in s.cells[1:]]
                tiene_id = bool(CASO_ID.match(nombre)) or any(CASO_ID.match(t.upper()) for t in tags)
                tiene_prio = bool(PRIORIDAD.search(nombre)) or any(t in PRIO_TAG for t in tags + suite_tags)
                if not (tiene_id and tiene_prio):
                    falta = " y ".join(x for x, ok in (("ID de caso", tiene_id), ("prioridad", tiene_prio)) if not ok)
                    add(b.line, "R7", "Mayor", f"Test sin {falta} verificable: '{nombre}'",
                        "Nombre 'TC-01 [critical] comportamiento' (prefijos TC/SEC/FRAUD/API/A11Y/UT/PERF)")
            # R6 sin aserción (no aplica a suites con template: la keyword plantilla verifica)
            plantilla = b.settings.get("[template]")
            if not usa_template and not plantilla and b.pasos:
                if not any(paso_verifica(p, verifica_nombre) for p in b.pasos) and \
                        not (b.settings.get("[teardown]") and paso_verifica(Paso(0, b.settings["[teardown]"].cells[1:]), verifica_nombre)):
                    add(b.line, "R6", "Bloqueante", f"Test sin verificación del resultado: '{nombre}'",
                        "Afirmar el resultado esperado (Should…, Check Row Count, getter con operador, Status Should Be)")
            # R15 lógica en el cuerpo del test
            if not usa_template and not plantilla:
                for p in b.pasos:
                    if p.keyword.upper() in ("FOR", "WHILE", "IF", "TRY"):
                        add(p.line, "R15", "Menor", f"{p.keyword.upper()} dentro del cuerpo del test oculta la intención",
                            "Mover la lógica a una keyword de usuario")
                        break
            # R19 estado compartido entre tests
            for p in b.pasos:
                k = norm(p.keyword)
                if k in ("setsuitevariable", "setglobalvariable") or (p.keyword.upper() == "VAR" and any(
                        re.match(r"scope\s*=\s*(suite|suites|global)", c, re.I) for c in p.args)):
                    add(p.line, "R19", "Mayor", "El test publica estado para otros tests (orden implícito)",
                        "Cada test prepara sus datos; compartir solo en Suite Setup")
            for s in ("[tags]",):
                st = b.settings.get(s)
                if st and any(t.lower() in ("robot:skip", "robot:exclude") for t in st.cells[1:]) and not b.settings.get("[documentation]"):
                    add(st.line, "R20", "Menor", "Test omitido/excluido sin motivo documentado",
                        "Agregar [Documentation] con motivo y ticket (BUG-123)")
        else:
            if b.settings.get("[return]"):
                add(b.settings["[return]"].line, "R2", "Mayor", "[Return] es heredado (obsoleto en RF 7)",
                    "Usar RETURN (RF 5.0+)")

        for p in b.pasos:
            lint_paso(p, add, opts, b)
    return out


def lint_paso(p: Paso, add, opts, b):
    k = p.keyword
    nk = norm(k)
    args = p.args
    texto = " ".join(p.cells)
    if nk == "sleep":
        add(p.line, "R1", "Mayor", "Sleep (espera fija)",
            "Esperar una condición: Wait For Elements State / Wait Until … / retry_timeout / Wait Until Keyword Succeeds")
    if nk in ("runkeywordif", "runkeywordunless"):
        add(p.line, "R2", "Mayor", f"'{k}' es heredado", "IF / ELSE en línea o en bloque (RF 4.0+)")
    if nk in ("exitforloop", "exitforloopif", "continueforloop", "continueforloopif", "returnfromkeyword", "returnfromkeywordif"):
        add(p.line, "R2", "Mayor", f"'{k}' es heredado", "BREAK / CONTINUE / RETURN (RF 5.0+)")
    if opts.rf >= 7 and nk in ("setsuitevariable", "settestvariable", "setglobalvariable", "setlocalvariable", "createlist", "createdictionary", "catenate"):
        add(p.line, "R3", "Menor", f"'{k}' tiene forma moderna", "VAR … [scope=TEST|SUITE|GLOBAL] (RF 7.0+)")
    # R4 secretos literales en llamadas
    if nk in ("inputpassword", "fillsecret", "inputtext", "filltext", "typetext") and len(args) >= 2:
        if SECRETO.search(args[0]) and not re.search(r"[$%]\{", args[1]) and not args[1].startswith("$") and len(args[1]) >= 4:
            add(p.line, "R4", "Bloqueante", "Credencial literal escrita en un campo", "Leer de %{VARIABLE} / secreto del pipeline")
    if nk in ("connecttodatabase",) and args:
        nombrados = {c.split("=", 1)[0].strip(): c.split("=", 1)[1] for c in args if re.match(r"^\w+\s*=", c)}
        posicionales = [c for c in args if not re.match(r"^\w+\s*=", c)]
        clave = nombrados.get("db_password") or nombrados.get("dbPassword") or (posicionales[3] if len(posicionales) > 3 else None)
        if clave and not re.search(r"[$%]\{", clave) and clave.lower() not in ("none",):
            add(p.line, "R4", "Bloqueante", "Contraseña literal en Connect To Database",
                "Pasar %{PASSWORD} (o la variable del pipeline) — nunca el valor")
    for env in re.findall(r"%\{([A-Za-z_][A-Za-z0-9_]*)", texto):
        if env.upper() in OS_ENV and nk in ("connecttodatabase", "createsession", "inputtext", "filltext", "inputpassword", "fillsecret") or \
                (env.upper() in OS_ENV and b.kind == "keyword" and SECRETO.search(b.name + " database conexion connection")):
            add(p.line, "R21", "Menor", f"%{{{env}}} coincide con una variable del sistema operativo",
                "Si el pipeline no inyecta el valor, Robot usa el del agente sin fallar: validar con una keyword de guarda (resources/08 §4)")
    for env in re.findall(r"%\{([A-Za-z_][A-Za-z0-9_]*)", texto):
        if env != env.upper():
            add(p.line, "R29", "Mayor", f"%{{{env}}} en minúscula: en agentes Linux Azure DevOps la expone como %{{{env.upper()}}}",
                f"Usar %{{{env.upper()}}} (resources/08 §2)")
    if nk == "log" and args and re.search(r"\$\{[^}]*(pass|clave|secret|token)[^}]*\}|%\{(PASSWORD|.*TOKEN.*|.*SECRET.*)\}", args[0], re.I):
        add(p.line, "R28", "Bloqueante", "Se registra un secreto en el log", "No registrar secretos; usar Secret (RF 7.4) o enmascarar")
    # R5 URL absoluta
    if nk in ("newpage", "goto", "openbrowser", "createsession", "get", "post", "put", "delete", "patch") and args:
        url = args[1] if nk == "createsession" and len(args) > 1 else args[0]
        if re.match(r"https?://(?!localhost|127\.0\.0\.1)", url):
            add(p.line, "R5", "Mayor", f"URL absoluta en el paso: {url[:60]}", "URL base en variables por ambiente (variables/<env>.py)")
    # R8 implícitas
    if nk == "setseleniumimplicitwait" and args and not re.match(r"^0(\s|s|$)", args[0]):
        add(p.line, "R8", "Mayor", "Espera implícita > 0", "implicit_wait=0s y esperas explícitas")
    # R9 JS para interactuar
    if nk in ("executejavascript", "evaluatejavascript") and re.search(r"\.click\(\)|\.value\s*=", texto):
        add(p.line, "R9", "Mayor", "Clic/escritura vía JavaScript (salta la verificación de interactuabilidad)",
            "Esperar el elemento y resolver el overlay; JS solo como último recurso documentado")
    # R10 WebElements almacenados
    if nk in ("getwebelement", "getwebelements") and p.asigna:
        add(p.line, "R10", "Menor", "WebElement guardado en variable (StaleElementReference tras re-render)",
            "Pasar el localizador y buscar el elemento en el momento")
    # R11 / R12 SQL
    if nk in {norm(x) for x in SQL_KW} and args:
        sql = args[0]
        if re.search(r"\$\{[^}]+\}", sql) and not any(a.startswith("parameters=") for a in args):
            add(p.line, "R11", "Mayor", "SQL con variables interpoladas", "Usar parameters=${params} (placeholders del driver: %s, :1, ?)")
    if nk in ("executesqlstring", "executesqlscript", "query") and args:
        sql = args[0].upper()
        if re.search(r"\b(DROP|TRUNCATE)\b", sql) or re.search(r"\bDELETE\s+FROM\s+\S+\s*;?\s*$", sql) or re.search(r"\bUPDATE\s+\S+\s+SET\b(?!.*\bWHERE\b)", sql):
            add(p.line, "R12", "Bloqueante", "SQL destructivo sin filtro en una suite de aceptación",
                "Solo lectura contra ambientes compartidos; datos propios con limpieza acotada por ID")
    if nk == "deleteallrowsfromtable":
        add(p.line, "R12", "Bloqueante", "Delete All Rows From Table en una suite de aceptación",
            "Borrar solo los datos creados por el test (WHERE id = …)")
    # R14 errores tragados
    if nk == "runkeywordandignoreerror" and not p.asigna:
        add(p.line, "R14", "Mayor", "Run Keyword And Ignore Error sin usar el resultado (traga fallos)",
            "Dejar fallar o usar TRY/EXCEPT con intención explícita")
    if p.keyword.upper() == "EXCEPT" and b is not None:
        idx = b.pasos.index(p)
        if idx + 1 < len(b.pasos) and norm(b.pasos[idx + 1].keyword) in ("nooperation", "pass"):
            add(p.line, "R14", "Mayor", "EXCEPT que no hace nada (traga fallos)", "Manejar el error o dejar fallar")
    # R16 Open Browser
    if nk == "openbrowser":
        if len([a for a in args if "=" not in a]) < 2 and not any(a.startswith("browser=") for a in args):
            add(p.line, "R16", "Mayor", "Open Browser sin navegador (por defecto abre Firefox)", "Pasar ${BROWSER} explícito")
        if any(a in ("headless_chrome", "headless_firefox", "headlessedge") for a in args):
            add(p.line, "R16", "Mayor", "Nombre de navegador inválido", "headlesschrome / headlessfirefox; Edge headless vía options")
    # R17 TLS
    if nk == "createsession" and not any(a.startswith("verify=") for a in args):
        add(p.line, "R17", "Mayor", "Create Session sin verify (por defecto NO verifica TLS)", "verify=${True} o la ruta del bundle CA corporativo")
    if nk == "createsession" and any(re.match(r"verify=\$\{?false\}?", a, re.I) for a in args):
        add(p.line, "R17", "Mayor", "Create Session con verify=False", "Verificar TLS; usar el bundle CA corporativo si hay proxy")
    # R18 reintentar acciones no idempotentes
    if nk == "waituntilkeywordsucceeds" and len(args) >= 3 and re.search(r"click|submit|post|enviar|transfer|execute sql", args[2], re.I):
        add(p.line, "R18", "Mayor", "Reintento de una acción no idempotente (puede duplicar operaciones)",
            "Reintentar solo verificaciones; esperar el estado antes de actuar")
    # R23 password con Fill Text / Input Text
    if nk in ("filltext", "inputtext") and args and re.search(r"pass|clave|contrase", args[0], re.I):
        add(p.line, "R23", "Menor", "Contraseña escrita con un keyword que la registra en el log",
            "Fill Secret (Browser) / Input Password (SeleniumLibrary)")
    # R24 XPath absoluto o posicional
    for loc in args[:1]:
        xp = re.sub(r"^xpath[:=]", "", loc)
        if (loc.startswith(("xpath:", "xpath=", "//", "/html", "(//")) and
                (xp.startswith("/html") or re.match(r"^/[a-z]", xp) or re.search(r"\]\[\d+\]|/[a-z]+\[\d+\]", xp))):
            add(p.line, "R24", "Mayor", f"XPath absoluto o posicional: {loc[:60]}",
                "id/data-testid/CSS semántico o XPath por texto (normalize-space)")
    # R27 rutas absolutas
    if re.search(r"(?<![\w$%&@{])([A-Za-z]:\\\\|[A-Za-z]:\\|/home/|/Users/)", texto):
        add(p.line, "R27", "Menor", "Ruta absoluta de una máquina", "Usar ${CURDIR}/${EXECDIR} o variables")


def lint_proyecto(archivos):
    """Reglas que necesitan ver todo el proyecto (R13)."""
    out = []
    conecta, desconecta, abre, cierra = None, False, None, False
    for a in archivos:
        for p in [p for b in a.bloques for p in b.pasos] + a.settings:
            k = norm(p.keyword if isinstance(p, Paso) else "")
            todo = " ".join(norm(c) for c in p.cells)
            if k == "connecttodatabase" and conecta is None:
                conecta = (a.path, p.line)
            if "disconnectfromdatabase" in todo or "disconnectfromalldatabases" in todo:
                desconecta = True
            if k == "openbrowser" and abre is None:
                abre = (a.path, p.line)
            if "closebrowser" in todo or "closeallbrowsers" in todo:
                cierra = True
    if conecta and not desconecta:
        out.append(F(conecta[0], conecta[1], "R13", "Mayor", "Se conecta a la base de datos y nunca se desconecta",
                     "Disconnect From Database en Suite/Test Teardown"))
    if abre and not cierra:
        out.append(F(abre[0], abre[1], "R13", "Mayor", "Se abre un navegador y nunca se cierra",
                     "Close All Browsers en Suite Teardown"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rutas", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--rf", type=int, default=7)
    ap.add_argument("--sin-trazabilidad", action="store_true")
    opts = ap.parse_args()
    files = []
    for r in opts.rutas:
        p = Path(r)
        cands = [p] if p.is_file() else sorted(p.rglob("*"))
        files += [f for f in cands if f.is_file() and f.suffix in (".robot", ".resource") and not (EXCLUIR & set(f.parts))]
    if not files:
        sys.exit("no se encontraron archivos .robot o .resource")
    archivos = [Archivo(f) for f in files]
    _, verifica_nombre = construir_indice(archivos)
    findings = [x for a in archivos for x in lint_archivo(a, verifica_nombre, opts)] + lint_proyecto(archivos)
    findings.sort(key=lambda x: (SEV[x.sev], x.file, x.line))
    if opts.json:
        print(json.dumps({"archivos": len(files), "hallazgos": [vars(f) for f in findings]}, ensure_ascii=False, indent=2))
    else:
        c = {s: sum(1 for f in findings if f.sev == s) for s in SEV}
        print(f"Robot lint — {len(files)} archivo(s): {c['Bloqueante']} bloqueantes, {c['Mayor']} mayores, {c['Menor']} menores\n")
        for f in findings:
            print(f"[{f.sev}] {f.rule} {f.file}:{f.line} — {f.msg}\n    → {f.fix}")
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        pass
    sys.exit(1 if any(f.sev == "Bloqueante" for f in findings) else 0)


if __name__ == "__main__":
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # salida limpia con | head
    main()
