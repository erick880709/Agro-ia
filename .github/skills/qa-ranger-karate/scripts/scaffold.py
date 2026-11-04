#!/usr/bin/env python3
"""
Genera los archivos de un proyecto de pruebas Karate.
Antes de ejecutarlo, configura los ambientes, las credenciales y las pruebas del servicio.

Uso:
  python scaffold.py --nombre pagos-api-tests --linea v2 --build maven \
      --dominios pagos,clientes --salida ./out [--group com.empresa.qa] \
      [--karate-version 2.1.3] [--recurso pagos]

Líneas soportadas:
  v2 + maven   -> karate-junit6, Java 21
  v1 + maven   -> karate-junit5, Java 17
  v1 + gradle  -> karate-junit5, Java 17
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TPL = SKILL_DIR / "templates"

DEFAULT_VERSIONS = {"v2": "2.1.3", "v1": "1.5.2"}
JAVA = {"v2": "21", "v1": "17"}


def render(text: str, ctx: dict) -> str:
    for k, v in ctx.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_tpl(rel: str) -> str:
    return (TPL / rel).read_text(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nombre", required=True, help="artifactId / nombre del proyecto (kebab-case)")
    ap.add_argument("--linea", choices=["v1", "v2"], default="v2")
    ap.add_argument("--build", choices=["maven", "gradle"], default="maven")
    ap.add_argument("--dominios", default="api", help="lista separada por comas, p.ej. pagos,clientes")
    ap.add_argument("--group", default="com.empresa.qa")
    ap.add_argument("--karate-version", default=None)
    ap.add_argument("--recurso", default=None, help="segmento de path del recurso de ejemplo (default: el dominio)")
    ap.add_argument("--threads", default="5")
    ap.add_argument("--salida", default=".")
    args = ap.parse_args()

    if args.linea == "v2" and args.build == "gradle":
        sys.exit("v2 + gradle no tiene plantilla: usa maven para v2, o adapta build.gradle "
                 "(karate-junit6 + junit-jupiter, Java 21) a partir de templates/gradle-v1.")

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.nombre):
        sys.exit("--nombre debe ser kebab-case (minúsculas, números y guiones)")

    dominios = [d.strip() for d in args.dominios.split(",") if d.strip()]
    for d in dominios:
        if not re.fullmatch(r"[a-z][a-z0-9]*", d):
            sys.exit(f"dominio inválido '{d}': usar minúsculas sin guiones (es un paquete Java)")

    version = args.karate_version or DEFAULT_VERSIONS[args.linea]
    java = JAVA[args.linea]
    root = Path(args.salida).resolve() / args.nombre
    if root.exists() and any(root.iterdir()):
        sys.exit(f"{root} ya existe y no está vacío")

    variant = f"{args.build}-{args.linea}"
    base_ctx = {
        "GROUP_ID": args.group,
        "ARTIFACT_ID": args.nombre,
        "KARATE_VERSION": version,
        "JAVA_VERSION": java,
        "PROYECTO": args.nombre,
        "LINEA": args.linea,
        "BUILD": "Maven" if args.build == "maven" else "Gradle",
        "THREADS": args.threads,
    }
    test = root / "src/test/java"

    # Copia la configuración de Maven o Gradle seleccionada.
    if args.build == "maven":
        write(root / "pom.xml", render(read_tpl(f"{variant}/pom.xml"), base_ctx))
    else:
        write(root / "build.gradle", render(read_tpl(f"{variant}/build.gradle"), base_ctx))
        write(root / "settings.gradle", render(read_tpl(f"{variant}/settings.gradle"), base_ctx))

    # Copia el ejecutor general de pruebas y los recursos compartidos.
    suite = read_tpl(f"{variant}/SuiteTest.java").replace(".parallel(5)", f".parallel({args.threads})")
    write(test / "SuiteTest.java", suite)
    write(test / "karate-config.js", read_tpl("common/karate-config.js"))
    write(test / "logback-test.xml", read_tpl("common/logback-test.xml"))
    write(test / "qa/QaEvidence.java", read_tpl("common/QaEvidence.java"))
    write(test / "common/auth.feature", read_tpl("common/auth.feature"))
    write(test / "common/headers.js", read_tpl("common/headers.js"))
    write(test / "common/schemas/error.json", read_tpl("common/error.json"))

    # Genera los archivos de pruebas para cada dominio solicitado.
    for d in dominios:
        ctx = dict(base_ctx, DOMAIN=d, DOMAIN_CLASS=d[0].upper() + d[1:],
                   RESOURCE_PATH=args.recurso or d)
        write(test / d / f"{ctx['DOMAIN_CLASS']}Runner.java", render(read_tpl(f"{variant}/DomainRunner.java"), ctx))
        write(test / d / f"consultar-{d}.feature", render(read_tpl("common/ejemplo.feature"), ctx))
        write(test / d / "schemas/recurso.json", read_tpl("common/recurso.json"))
        (test / d / "data").mkdir(parents=True, exist_ok=True)
        (test / d / "data/.gitkeep").write_text("")

    # Copia archivos de apoyo del proyecto.
    pipeline = render(read_tpl("common/azure-pipelines.yml"), base_ctx)
    if args.build == "gradle":
        pipeline = re.sub(r"  - task: Maven@4.*?(?=\n  - publish)", GRADLE_TASK.rstrip("\n"), pipeline, flags=re.S)
    write(root / "azure-pipelines.yml", pipeline)
    write(root / ".gitignore", read_tpl("common/gitignore"))
    write(root / f"Linea_Base_{args.nombre}.md", render(read_tpl("common/Linea_Base_TEMPLATE.md"), base_ctx))
    write(root / "README.md", README.format(nombre=args.nombre, linea=args.linea, version=version, java=java,
                                            cmd=("mvn test" if args.build == "maven" else "./gradlew test")))

    print(f"Proyecto generado en {root}")
    for p in sorted(root.rglob("*")):
        if p.is_file():
            print("  " + str(p.relative_to(root)))
    print("\nSiguiente: reemplazar los placeholders {{BASE_URL_*}} / {{TOKEN_URL_*}} en karate-config.js")
    # Azure DevOps usa expresiones ${{ parameters.* }} en azure-pipelines.yml.
    # Solo las claves {{MAYUSCULAS}} indican valores pendientes de la plantilla.
    leftover = [str(p.relative_to(root)) for p in root.rglob("*")
                if p.is_file() and re.search(r"\{\{[A-Z0-9_]+\}\}", p.read_text(encoding="utf-8"))]
    if leftover:
        print("Archivos con placeholders pendientes: " + ", ".join(leftover))
    if args.build == "gradle":
        print("Pendiente: generar el wrapper con `gradle wrapper` (gradlew); el README y el pipeline lo usan.")


GRADLE_TASK = """  - task: Gradle@3
    displayName: Karate ${{ parameters.ambiente }} ${{ parameters.tags }}
    inputs:
      gradleWrapperFile: gradlew
      tasks: test
      options: '-Dkarate.env=${{ parameters.ambiente }} "-Dkarate.options=--tags ${{ parameters.tags }}"'
      publishJUnitResults: true
      testResultsFiles: 'resources/qa/reports/**/karate-reports/**/*.xml'
    env:
      QA_RUN_ID: azure-$(Build.BuildId)-$(System.JobAttempt)
      CLIENT_ID: $(CLIENT_ID)
      CLIENT_SECRET: $(CLIENT_SECRET)
"""

README = """# {nombre}

Pruebas automatizadas con Karate {version} (línea {linea}, Java {java}).

## Ejecutar
```bash
export CLIENT_ID=... CLIENT_SECRET=...
{cmd} -Dkarate.env=qa
{cmd} -Dkarate.env=qa -Dkarate.options="--tags @smoke"
{cmd} -Dkarate.env=qa -Dkarate.options="classpath:<dominio>/<archivo>.feature:LINEA"
```
Sin autenticación: agregar `-Dauth=false`.

Reporte: `resources/qa/reports/<runId>/karate-reports/karate-summary.html`.
El runner muestra el directorio resuelto; `QA_RUN_ID` permite usar el ID del host.

## Estructura
- `src/test/java/karate-config.js` — ambientes y token (una vez por suite)
- `src/test/java/common/` — helpers `@ignore`, headers y esquemas compartidos
- `src/test/java/<dominio>/` — features, `schemas/`, `data/` y runner para el IDE
- `SuiteTest.java` — runner único de CI (paralelo)
- `Linea_Base_{nombre}.md` — memoria del proyecto (convenciones, ambientes, cobertura, decisiones)
"""

if __name__ == "__main__":
    main()
