# Perfil Go

Capa específica de stack para Builder. No reemplaza el flujo de `SKILL.md`: lo
concreta cuando el componente afectado es Go. Las invariantes del skill siguen
mandando; en particular, las convenciones observadas del proyecto y el mandato del
usuario prevalecen sobre cualquier preferencia idiomática de esta guía.

## Activación

Aplica este perfil a cada componente con `go.mod` (o incluido en un `go.work`)
que el cambio toque. En monorepos, aplícalo solo a los módulos Go afectados.

Antes de editar, ejecuta el descubrimiento estático (no compila ni descarga nada):

```text
python <skill-root>/scripts/go_toolkit.py discover <ruta-del-modulo>
```

El JSON devuelve, sin ejecutar Go: módulo, directiva `go`, `toolchain`, `go.work`,
dependencias de test/DI/logging relevantes, configuración de golangci-lint,
targets de Makefile/Taskfile, directivas `//go:generate`, build tags y
workflows de CI. Si el script no está disponible, obtén lo mismo leyendo esos
archivos. No lo uses como sustituto de inspeccionar el código afectado.

## Versión objetivo: la directiva `go` manda

1. La línea `go 1.N` del `go.mod` del módulo afectado es la versión de lenguaje
   y de API objetivo. El toolchain local puede ser más nuevo: eso no habilita
   features posteriores. `toolchain goX` solo indica el toolchain preferido.
2. No uses una feature de lenguaje o de librería estándar posterior a la
   directiva. Consulta [Go moderno por versión](go-modern-by-version.md).
3. No subas la directiva `go` ni el `toolchain` para poder usar una feature: es
   una decisión con impacto en CI, imágenes y consumidores. Regístrala como
   decisión pendiente salvo mandato explícito.
4. Dentro de lo permitido por la versión, escribe Go moderno en las líneas que
   crees o modifiques. No migres código vecino que no forma parte del encargo:
   eso es un `refactor` aparte (invariante 3 de alcance del diff).
5. Si el proyecto fija estilo con `.golangci.yml`, `revive`, `gocritic` u otros
   linters, su configuración prevalece sobre esta guía.

## Mapa de lectura por tipo de cambio

Lee solo lo que el cambio necesita:

| Necesidad del cambio | Guía |
|---|---|
| Ubicar código nuevo, paquetes, interfaces, constructores, DI, genéricos | [Diseño e idiomas](go-design-and-idioms.md) |
| Errores, `context`, goroutines, HTTP, base de datos, logging | [Errores, contexto y concurrencia](go-errors-context-concurrency.md) |
| Pruebas, comandos de validación, evidencia | [Pruebas y validación Go](go-testing-and-validation.md) |
| Elegir idioma según la directiva `go` | [Go moderno por versión](go-modern-by-version.md) |
| Revisión de calidad, diagnóstico de bugs Go | [Revisión y diagnóstico Go](go-review-and-debugging.md) |

## Superposición sobre el flujo de Builder

| Paso de Builder | Qué añade el perfil Go |
|---|---|
| 1. Descubrir | `discover`; leer `go.mod`/`go.work`, `Makefile`, `.golangci.yml`, CI y generadores; ubicar el `main`/entrypoint y el cableado real (constructores, `wire`, `fx`, `do`) |
| 2. Especificar | Declarar en la spec la versión objetivo y los contratos Go públicos afectados (firmas exportadas, errores sentinela, tipos de error, tags JSON) |
| 3. Diseñar | Elegir la ubicación respetando el layout existente; definir interfaces del lado consumidor solo si hay una necesidad real |
| 4. Implementar | Cambiar la fuente de lo generado (`.proto`, `sqlc`, mocks, `wire`) y regenerar con el comando del proyecto |
| 5. Validar | Escalera: formato → `go vet` → build → tests focalizados → `-race` cuando haya concurrencia → linter configurado → `govulncheck` si cambian dependencias |
| 6. Entregar | Registrar versión de Go, `GOOS/GOARCH`, `CGO_ENABLED`, flags y paquetes validados como contexto de la evidencia |

## Límites del perfil

- No crea proyectos Go nuevos, layouts globales ni `go.work`: eso es baseline o
  arquitectura. Para un repositorio sin módulo de referencia aplica
  [fronteras y fuentes](../../boundaries-and-sources.md).
- No existe un Scaffold Clean Architecture de Bancolombia para Go (el plugin
  Gradle es Java). No traslades a Go sus tareas (`gm`, `guc`, `gda`, `gep`),
  ArchUnit ni reglas de nombres; si el repositorio Go tiene su propia
  convención por capas, respétala tal como está.
- Las bibliotecas Go de Bancolombia (`reactive-commons-go`, `commons-mq-go`,
  `secrets-manager-go`) se declaran en alfa en sus repositorios. Si el proyecto
  ya las usa, sigue su API; introducirlas en un componente productivo es una
  decisión arquitectónica, no un detalle local.
- No instales herramientas (`golangci-lint`, `govulncheck`, `gotests`, CLIs de
  guías) sin mandato; si faltan, registra la comprobación como `not_run` con razón.

## Fuentes destiladas

Pautas sintetizadas y adaptadas al flujo de Builder a partir de: Effective Go,
Go Code Review Comments, Google Go Style Guide, Uber Go Style Guide,
`samber/cc-skills-golang`, `spf13/go-skills`, `cxuu/golang-skills` y
`JetBrains/go-modern-guidelines`. Cuando estas fuentes discrepan (por ejemplo,
layout plano frente a capas limpias) la evidencia del repositorio decide.
