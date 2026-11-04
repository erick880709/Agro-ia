#!/usr/bin/env python3
"""
Linter de planes JMeter (.jmx): estructura, propiedades y antipatrones de rendimiento.

Uso:
  python lint_jmx.py plan.jmx [otro.jmx ...] [--json]

- Verifica cada propiedad contra el catálogo extraído del código fuente de JMeter 5.6.3
  (scripts/data/jmx_catalogo.json). Una propiedad desconocida se carga en silencio y no hace nada.
- Reglas J1–J25 de resources/10-revision-y-antipatrones.md (las marcadas "L").
Código de salida: 1 si hay hallazgos Bloqueantes.
"""
import argparse
import difflib
import json
import re
import signal
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CAT = json.loads((Path(__file__).parent / "data" / "jmx_catalogo.json").read_text(encoding="utf-8"))
CLASES, COMUNES, ALIAS = CAT["clases"], set(CAT["_propiedades_comunes"]), CAT["_alias_nucleo"]
SEV = {"Bloqueante": 0, "Mayor": 1, "Menor": 2}
PROP_TAGS = {"stringProp", "boolProp", "intProp", "longProp", "doubleProp", "floatProp", "collectionProp", "elementProp", "objProp"}
VISUALIZADORES = {"ViewResultsFullVisualizer", "SummaryReport", "StatVisualizer", "GraphVisualizer", "TableVisualizer",
                  "RespTimeGraphVisualizer", "StatGraphVisualizer", "AssertionVisualizer", "ComparisonVisualizer"}
SAMPLERS = re.compile(r"(Sampler|SamplerProxy)$")
ASSERCIONES = re.compile(r"Assertion$")
# aserciones que NO validan que la respuesta sea correcta (no cuentan para J11)
NO_FUNCIONALES = {"DurationAssertion", "SizeAssertion"}
TIMERS = re.compile(r"(Timer)$")
THREAD_GROUPS = {"ThreadGroup", "OpenModelThreadGroup", "SetupThreadGroup", "PostThreadGroup"}
SECRETO_JSON = re.compile(r'"(password|passwd|clave|contrase(?:ñ|n)a|secret|client_secret|token|api_?key)"\s*:\s*"([^"$]{4,})"', re.I)


class F:
    def __init__(self, file, donde, rule, sev, msg, fix):
        self.file, self.donde, self.rule, self.sev, self.msg, self.fix = str(file), donde, rule, sev, msg, fix


def props(el):
    return {c.get("name"): c for c in el if c.tag in PROP_TAGS and c.get("name") is not None}


def val(el, nombre, defecto=""):
    p = props(el).get(nombre)
    return (p.text or "").strip() if p is not None and p.tag in ("stringProp", "boolProp", "intProp", "longProp") else defecto


def efectivo(v):
    """Valor efectivo si nadie pasa la propiedad: ${__P(x,defecto)} -> defecto."""
    m = re.fullmatch(r"\$\{__P\(\s*[\w.]+\s*,\s*([^)]*)\)\}", v.strip())
    return m.group(1).strip() if m else v


def enabled(el):
    return el.get("enabled", "true") != "false"


def nombre(el):
    return f'{el.get("testclass")} "{el.get("testname", "")}"'


def lint(path: Path):
    out = []
    add = lambda d, r, s, m, f: out.append(F(path, d, r, s, m, f))
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        add("archivo", "J21", "Bloqueante", f"XML inválido: {e}", "Regenerar el plan desde la GUI o la plantilla")
        return out
    if root.tag != "jmeterTestPlan":
        add("archivo", "J21", "Bloqueante", "La raíz no es <jmeterTestPlan>", "No es un plan JMeter válido")
        return out

    # J21: cada elemento de un hashTree debe ir seguido de su hashTree
    def check_tree(ht, ruta):
        hijos = list(ht)
        i = 0
        while i < len(hijos):
            e = hijos[i]
            if e.tag == "hashTree":
                add(ruta, "J21", "Bloqueante", "hashTree sin elemento previo (árbol desbalanceado)", "Revisar la estructura")
                i += 1
                continue
            if i + 1 >= len(hijos) or hijos[i + 1].tag != "hashTree":
                add(nombre(e), "J21", "Bloqueante", "Elemento sin su <hashTree> a continuación", "Agregar <hashTree/> tras el elemento")
                i += 1
                continue
            check_tree(hijos[i + 1], nombre(e))
            i += 2
    raiz = root.find("hashTree")
    if raiz is None:
        add("archivo", "J21", "Bloqueante", "Falta el hashTree raíz", "Plan corrupto")
        return out
    check_tree(raiz, "raíz")

    todos = [e for e in root.iter() if e.get("testclass")]
    activos = [e for e in todos if enabled(e)]
    clases_activas = [e.get("testclass") for e in activos]

    # J1: propiedades desconocidas
    verificadas = 0
    for e in todos:
        tc = e.get("testclass")
        conocidas = CLASES.get(tc)
        if conocidas is None:
            continue
        validas = set(conocidas) | COMUNES
        for n, p in props(e).items():
            verificadas += 1
            if n in validas or n == "":
                continue
            if len(conocidas) < 4:      # cobertura baja del catálogo: no afirmar
                continue
            sug = difflib.get_close_matches(n, list(validas), n=1, cutoff=0.75)
            extra = f" ¿Quisiste decir `{sug[0]}`?" if sug else ""
            if n == "Assertion.test_strings":
                extra = " La propiedad real es `Asserion.test_strings` (errata histórica de JMeter: no corregir)."
            add(nombre(e), "J1", "Bloqueante", f"Propiedad desconocida `{n}` para {tc}: JMeter la ignora en silencio.{extra}",
                "Usar el nombre del catálogo (scripts/data/jmx_catalogo.json)")

    # J25: elementos fuera del núcleo
    for e in activos:
        tc = e.get("testclass")
        if tc not in ALIAS and tc not in CLASES:
            add(nombre(e), "J25", "Menor", f"Elemento no reconocido como núcleo de JMeter 5.6.3 (plugin o clase personalizada): {tc}",
                "Declarar plugin y versión en la Línea Base e instalarlo en todos los generadores")

    for e in activos:
        tc, gui = e.get("testclass"), e.get("guiclass", "")
        # J2 listeners
        if tc == "ResultCollector":
            sev = "Mayor" if gui in VISUALIZADORES else "Menor"
            add(nombre(e), "J2", sev, f"Listener habilitado ({gui}) en el plan: consume CPU/memoria del generador",
                "Deshabilitarlo; escribir resultados con -l resultados.jtl")
        # J3 BeanShell
        if tc.startswith("BeanShell"):
            add(nombre(e), "J3", "Mayor", "BeanShell: lento y sin caché de compilación", "Reemplazar por JSR223 + Groovy")
        # J4/J5 JSR223
        if tc.startswith("JSR223"):
            lang = val(e, "scriptLanguage").lower()
            if lang and lang != "groovy":
                add(nombre(e), "J5", "Menor", f"JSR223 con lenguaje '{lang}'", "Usar groovy")
            if val(e, "cacheKey").lower() not in ("true",) and not val(e, "filename"):
                add(nombre(e), "J4", "Mayor", "JSR223 sin caché de compilación (cacheKey≠true)", "cacheKey=true")
            if "${" in val(e, "script"):
                add(nombre(e), "J4", "Mayor", "JSR223 con ${...} dentro del script: invalida la caché y es inseguro",
                    'Usar vars.get("x") / props.get("x")')
        # J6 host literal
        if tc == "HTTPSamplerProxy":
            dom = val(e, "HTTPSampler.domain")
            if dom and "${" not in dom:
                add(nombre(e), "J6", "Mayor", f"Host literal en el sampler: {dom}", "Vaciar y definirlo en HTTP Request Defaults con ${__P(host,...)}")
            if val(e, "HTTPSampler.image_parser") == "true":
                add(nombre(e), "J17", "Menor", "Descarga de recursos embebidos activada", "Desactivar en pruebas de API (image_parser=false)")
        # J7/J10 thread groups
        if tc == "ThreadGroup":
            n, r, d = val(e, "ThreadGroup.num_threads"), val(e, "ThreadGroup.ramp_time"), val(e, "ThreadGroup.duration")
            for etiqueta, v in (("usuarios", n), ("rampa", r)):
                if v and "${" not in v:
                    add(nombre(e), "J7", "Mayor", f"{etiqueta} literal ({v}): el plan no sirve para otros ambientes/cargas",
                        f"${{__P({etiqueta},1)}} y pasarlo con -J o -q")
            sched = val(e, "ThreadGroup.scheduler") == "true"
            lc = props(e).get("ThreadGroup.main_controller")
            loops = val(lc, "LoopController.loops") if lc is not None else ""
            forever = (val(lc, "LoopController.continue_forever") == "true" and loops in ("-1", "")) if lc is not None else False
            if not sched and (efectivo(loops) == "-1" or forever):
                add(nombre(e), "J10", "Mayor", "Iteraciones infinitas sin duración: la prueba no termina sola",
                    "ThreadGroup.scheduler=true + ThreadGroup.duration=${__P(duracion,...)}")
            if sched and d and "${" not in d:
                add(nombre(e), "J7", "Mayor", f"duración literal ({d}s)", "${__P(duracion,60)}")
            if r.isdigit() and n.isdigit() and int(r) == 0 and int(n) > 10:
                add(nombre(e), "J10", "Mayor", f"{n} hilos con rampa 0: arranque en pico irreal", "Rampa proporcional a los hilos")
        # J12 extractores sin default
        if tc == "JSONPostProcessor" and not val(e, "JSONPostProcessor.defaultValues"):
            add(nombre(e), "J12", "Menor", "JSON Extractor sin valor por defecto", "defaultValues=NO_ENCONTRADO_<var> + validación")
        if tc == "RegexExtractor" and not val(e, "RegexExtractor.default"):
            add(nombre(e), "J12", "Menor", "Regex Extractor sin valor por defecto", "RegexExtractor.default=NO_ENCONTRADO_<var>")
        if tc == "BoundaryExtractor" and not val(e, "BoundaryExtractor.default"):
            add(nombre(e), "J12", "Menor", "Boundary Extractor sin valor por defecto", "BoundaryExtractor.default=NO_ENCONTRADO_<var>")
        # J14 CSV absoluto
        if tc == "CSVDataSet":
            fn = val(e, "filename")
            if re.match(r"^(/|[A-Za-z]:[\\/])", fn):
                add(nombre(e), "J14", "Mayor", f"CSV con ruta absoluta: {fn}", "Ruta relativa al .jmx o ${__P(datos,...)}")
        # J16 debug
        if tc in ("DebugSampler", "DebugPostProcessor"):
            add(nombre(e), "J16", "Menor", "Elemento de depuración habilitado", "Deshabilitar en pruebas de carga")
        # J19
        if tc == "DurationAssertion":
            add(nombre(e), "J19", "Menor", "Duration Assertion: mezcla SLA con errores funcionales",
                "Validar el SLA sobre percentiles agregados (analizar_jtl.py)")

    # J15 secretos
    for e in activos:
        for p in e.iter():
            if p.tag != "stringProp":
                continue
            n, v = p.get("name", ""), (p.text or "")
            if "${" in v and not SECRETO_JSON.search(v):
                continue
            m = SECRETO_JSON.search(v)
            hdr = n == "Header.value" and re.match(r"^(Bearer|Basic)\s+[A-Za-z0-9._\-+/=]{8,}$", v.strip())
            literal = re.search(r"(password|passwd|clave|secret|token|api_?key)$", n, re.I) and v.strip() and "${" not in v
            if m or hdr or literal:
                add(nombre(e), "J15", "Bloqueante", "Credencial/secreto literal dentro del .jmx",
                    "Usar ${__P(clave)} o datos del CSV y pasar secretos desde el pipeline (-Jclave=$SECRETO)")
                break

    # J8 timeouts
    if any(c == "HTTPSamplerProxy" for c in clases_activas):
        def tiene_timeout(e):
            return val(e, "HTTPSampler.connect_timeout") and val(e, "HTTPSampler.response_timeout")
        if not any(e.get("testclass") in ("ConfigTestElement", "HTTPSamplerProxy") and tiene_timeout(e) for e in activos):
            add("plan", "J8", "Mayor", "Sin timeouts de conexión/respuesta: un servidor colgado bloquea hilos indefinidamente",
                "HTTP Request Defaults: connect_timeout y response_timeout")
        if "CookieManager" not in clases_activas:
            add("plan", "J13", "Menor", "Sin HTTP Cookie Manager", "Agregarlo si la aplicación usa sesión/cookies")
    # J9 timers
    if any(c in THREAD_GROUPS for c in clases_activas) and not any(TIMERS.search(c) for c in clases_activas):
        add("plan", "J9", "Mayor", "Ningún timer: sin think time ni control de ritmo la carga no representa usuarios reales",
            "Uniform/Gaussian Random Timer (reflexión) y/o Precise Throughput Timer (ritmo)")
    # J18 transacciones
    n_samplers = sum(1 for c in clases_activas if SAMPLERS.search(c))
    if n_samplers > 2 and "TransactionController" not in clases_activas:
        add("plan", "J18", "Menor", f"{n_samplers} samplers sin Transaction Controllers", "Agrupar por paso de negocio")

    # J11 samplers sin aserción en su alcance
    def recorrer(ht, heredada):
        hijos = list(ht)
        pares = [(hijos[i], hijos[i + 1] if i + 1 < len(hijos) and hijos[i + 1].tag == "hashTree" else None)
                 for i in range(len(hijos)) if hijos[i].tag != "hashTree"]
        es_funcional = lambda x: ASSERCIONES.search(x.get("testclass", "")) and x.get("testclass") not in NO_FUNCIONALES and enabled(x)
        nivel = heredada or any(es_funcional(e) for e, _ in pares)
        for e, sub in pares:
            if not enabled(e):
                continue
            tc = e.get("testclass", "")
            if SAMPLERS.search(tc) and tc not in ("DebugSampler",):
                propia = sub is not None and any(es_funcional(x) for x in sub if x.tag != "hashTree")
                if not (nivel or propia):
                    add(nombre(e), "J11", "Mayor", "Sampler sin aserciones en su alcance: una respuesta de error cuenta como éxito",
                        "Response Assertion (código) + marcador de éxito")
            if sub is not None:
                recorrer(sub, nivel)
    recorrer(raiz, False)

    # J20 deshabilitados
    desh = [e for e in todos if not enabled(e)]
    if desh:
        add("plan", "J20", "Menor", f"{len(desh)} elemento(s) deshabilitado(s): " + ", ".join(nombre(e) for e in desh[:4]) + ("..." if len(desh) > 4 else ""),
            "Eliminar lo que no se usa o documentar por qué se conserva")
    lint.verificadas = verificadas
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("planes", nargs="+")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    files = [f for r in a.planes for f in ([Path(r)] if Path(r).is_file() else sorted(Path(r).rglob("*.jmx")))]
    if not files:
        sys.exit("no se encontraron archivos .jmx")
    todos, total_props = [], 0
    for f in files:
        todos += lint(f)
        total_props += getattr(lint, "verificadas", 0)
    todos.sort(key=lambda x: (SEV[x.sev], x.file, x.rule))
    if a.json:
        print(json.dumps({"archivos": len(files), "propiedades_verificadas": total_props,
                          "hallazgos": [vars(x) for x in todos]}, ensure_ascii=False, indent=2))
    else:
        c = {s: sum(1 for x in todos if x.sev == s) for s in SEV}
        print(f"JMeter lint — {len(files)} plan(es), {total_props} propiedades verificadas contra el catálogo 5.6.3: "
              f"{c['Bloqueante']} bloqueantes, {c['Mayor']} mayores, {c['Menor']} menores\n")
        for x in todos:
            print(f"[{x.sev}] {x.rule} {Path(x.file).name} · {x.donde}\n    {x.msg}\n    → {x.fix}")
    sys.exit(1 if any(x.sev == "Bloqueante" for x in todos) else 0)


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
