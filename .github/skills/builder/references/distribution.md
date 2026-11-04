# Distribución y mantenimiento

## Instalar un paquete autocontenido

El directorio que contiene el `SKILL.md` canónico, sus referencias, scripts y
evaluaciones es la unidad de distribución. La entrada `.agents/skills/builder`
de este repositorio es únicamente un wrapper de desarrollo. No la distribuyas sola.

Usa Python 3.11+; el instalador y las comprobaciones del paquete solo requieren
la biblioteca estándar. Desde cualquier directorio:

```text
python <skill-root>/scripts/install_builder.py install --destination <proyecto>/.agents/skills/builder
python <skill-root>/scripts/install_builder.py verify --destination <proyecto>/.agents/skills/builder
```

Para Claude Code cambia el destino por `<proyecto>/.claude/skills/builder`. Puedes
instalar ambas entradas si utilizas ambas plataformas; serán copias instaladas de
la misma fuente, verificables por hashes. Edita el paquete fuente, no cada copia.
No copies datos de una evaluación ejecutada ni información de un proyecto cliente.

El instalador verifica referencias locales, rechaza enlaces simbólicos/junctions
y destinos superpuestos con la fuente. Una instalación nueva requiere un destino
vacío o inexistente. Una repetición idéntica no cambia archivos. Para actualizar:

```text
python <skill-root>/scripts/install_builder.py install --destination <destino> --update
```

La actualización compara cada archivo gestionado con el hash registrado. Si hay
ediciones locales, faltantes o colisiones con archivos ajenos, se detiene antes de
aplicar el cambio. No ofrece `--force`. Conserva archivos ajenos que no colisionan;
no elimina archivos retirados por una nueva versión: requiere resolver esa migración
explícitamente. No es una transacción de varios repositorios ni un actualizador remoto.
Las escrituras son atómicas por archivo, no por paquete: si hay una interrupción
o fallo de disco, `verify` lo detecta y no se repara sobrescribiendo a ciegas; conserva
el destino para revisión o instala en uno nuevo.

`verify` compara la copia con su registro de instalación y con la fuente desde la
que se invoca. El registro detecta drift, no prueba autenticidad de un proveedor:
obtén el paquete de una fuente confiable. Ningún hook, agente o permiso global se
instala ni se habilita automáticamente.

Para distribución reusable en Codex y ChatGPT, usa preferentemente el plugin
`plugins/builder`; contiene una copia autocontenida del skill y metadata de interfaz.
El instalador sigue siendo la vía local/offline y la fuente canónica continúa en
`.claude/skills/builder`. Después de modificarla, actualiza la copia del plugin con
el mismo instalador y valida ambos paquetes; no edites las dos implementaciones.

## Validación del paquete

```text
python -m unittest discover -s <skill-root>/tests -p "test_*.py" -v
```

Esto verifica instalador, herramientas de evaluación y `go_toolkit.py`. Los tests
que ejecutan Go real (`test_go_cases.py` y un caso de `test_go_toolkit.py`) se
omiten si no hay toolchain Go; el resto corre solo con Python.

`scripts/angular_toolkit.py` (`discover`, `api-status`, `unstable`, `validate`)
es parte del perfil Angular: solo lee `node_modules` existentes y ejecuta
binarios locales; nunca `npm install` ni `npx`. Los tests que ejecutan Angular real
(`test_angular_cases.py`) se omiten sin Node y `BUILDER_ANGULAR_DEPS`.

`scripts/spring_toolkit.py` (`discover`, `class-status`, `validate`) es parte del
perfil Java/Spring: solo lee los jars ya presentes en las cachés locales y ejecuta
el wrapper del proyecto; nunca Gradle/Maven globales ni actualizaciones. Los tests
Java (`test_java_cases.py`) se omiten sin JDK o sin el jar standalone de JUnit.

`scripts/go_toolkit.py` (`discover`, `validate`) es parte del perfil Go: no
requiere dependencias, no escribe en el proyecto y no instala herramientas. Los
perfiles de stack viven en `references/stacks/<stack>/` y se distribuyen dentro
del mismo paquete; añadir un stack no requiere cambiar el instalador. Para medir decisiones de un
agente sigue [evaluación conductual](behavioral-evaluation.md); no confundas tests
del arnés con ejecuciones del modelo. Conserva resultados fuera del paquete fuente.

## Agente, hooks y metadatos opcionales

La selección implícita continúa habilitada y el skill puede ejecutarse sin un agente.
Cuando se prefiera una identidad explícita, usa `plugins/builder/agents/builder.agent.md`
como contrato canónico. El agente debe cargar el skill; no copies en él todo el flujo.
`agents/openai.yaml` sigue siendo metadato de interfaz, no un agente.

Los adaptadores de proyecto viven en `.claude/agents/builder.agent.md`,
`.github/agents/builder.agent.md`, `.codex/agents/builder.toml` y
`.kiro/agents/builder.json`. Cada uno referencia la instalación local del skill y
delimita herramientas y salida sin fijar modelos ni ampliar permisos por defecto.
Instala también una copia autocontenida del skill en el directorio que descubre cada
runtime: `.claude/skills`, `.github/skills`, `.agents/skills` o `.kiro/skills`.

Un hook solo se justifica para un control repetitivo concreto. Primero implementa
y prueba el comando de control; después configura alcance y eventos en la plataforma.
Prefiere controles deterministas, salida breve, timeout y ausencia de efectos
remotos. Un hook de cierre debe distinguir pendientes de bloqueos y evitar bucles.
La confianza/aprobación del runtime se conserva; no se configura un bypass. No
ejecutes toda la suite después de cada edición ni hagas autorreparación silenciosa.
