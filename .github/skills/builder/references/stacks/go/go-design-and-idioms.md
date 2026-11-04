# Diseño e idiomas Go

## Respetar el layout existente

Ubica el código siguiendo el módulo de referencia del proyecto, no un layout
ideal. Se encuentran tres familias válidas; ninguna se impone a otra:

| Layout observado | Señales | Cómo extender |
|---|---|---|
| Plano / paquetes por dominio | `main.go` en raíz o `cmd/x`, paquetes `billing/`, `jobs/`, `auth/` | Añade al paquete del dominio; crea paquete nuevo solo si el dominio se describe en una frase y no conoce a los demás |
| `cmd/` + `internal/` | `cmd/<bin>/main.go` mínimo, lógica en `internal/<dominio>` | `main` solo cablea; lógica nueva en `internal/` junto a su dominio |
| Capas limpias / hexagonal | `entity`/`domain`, `usecase`, `port`, `adapter`, `infrastructure` | Respeta la regla de dependencias hacia adentro; puertos definidos por el caso de uso; adaptadores implementan |

Reglas comunes a cualquier layout:

- No crees `utils`, `common`, `helpers`, `misc`, `models` genéricos: son síntoma
  de ownership difuso. Si ya existen, no los amplíes con lógica de dominio nueva.
- No introduzcas capas, puertos o un contenedor DI que el proyecto no use
  (invariante 6). Tampoco aplanes una arquitectura por capas existente.
- Un ciclo de imports indica una frontera incorrecta: resuélvelo moviendo el tipo
  compartido al paquete que lo posee o definiendo una interfaz en el consumidor,
  no fusionando paquetes ni creando un paquete `common`.
- `internal/` es una restricción del compilador para importadores externos. En
  binarios es opcional; en librerías protege API no pública. No muevas código
  público a `internal/` (ruptura para consumidores).

## Paquetes y nombres

- Nombre de paquete corto, minúsculas, singular, sin `_` ni mayúsculas,
  coincidente con el directorio. Evita tartamudeo: `order.Service`, no
  `order.OrderService`.
- `MixedCaps`; iniciales con caja uniforme (`ID`, `URL`, `HTTP`: `userID`,
  `ServeHTTP`). Sin `GetX` para getters: `Name()`; setter `SetName()`.
- Receptor corto y consistente (`c *Client`), nunca `this`/`self`.
- Errores: variables `ErrNotFound`, tipos `NotFoundError`.
- Interfaces de un método: verbo + `er` cuando sea natural (`Reader`, `Notifier`).
- Archivos `snake_case.go`; tests `<archivo>_test.go`.

## Interfaces

1. Empieza por tipos concretos. Introduce una interfaz cuando un consumidor
   necesite sustituir implementaciones (incluido un fake de prueba en un límite
   de I/O real).
2. Defínela en el paquete que la consume, pequeña (1–3 métodos), con solo los
   métodos que ese consumidor usa. El productor devuelve un struct concreto.
3. Acepta interfaces, devuelve structs. Para entradas genéricas usa las del
   estándar (`io.Reader`, `io.Writer`, `fs.FS`, `http.Handler`).
4. Verificación en compilación cuando un tipo debe satisfacer una interfaz
   importante: `var _ Notifier = (*SMTPNotifier)(nil)`.
5. No crees una interfaz "para mockear" en el lado productor ni un
   `Repository[T]` genérico con polimorfismo estilo Java.
6. Una interfaz con valor `nil` tipado no es `nil`: no devuelvas `*MyErr(nil)`
   como `error`.

## Tipos, constructores y estado

- Haz útil el valor cero cuando sea posible (`sync.Mutex`, `bytes.Buffer`). Si no
  es posible, exige un constructor `NewX` que valide y devuelva `(*X, error)`
  cuando la construcción puede fallar.
- Opciones: struct de configuración para pocos campos estables; *functional
  options* (`type Option func(*Server)`, `WithTimeout(...)`) cuando la API crece
  y los defaults importan. Sigue el patrón que ya usa el paquete.
- Inyecta dependencias por constructor. Sin estado global mutable ni `init()`
  con efectos (abrir DB, leer env, registrar handlers). `init()` solo para
  registros declarativos sin I/O si el proyecto ya lo hace.
- Receptores: puntero si muta, contiene `sync.*`, o el struct es grande; valor
  para tipos pequeños inmutables. No mezcles en el mismo tipo.
- No copies structs que contengan `sync.Mutex` (lo detecta `go vet copylocks`).
- Copia defensivamente slices y maps recibidos o devueltos cuando el llamador
  pueda mutarlos y el tipo prometa encapsulación (`slices.Clone`, `maps.Clone`).
- Enums: tipo con `iota` empezando en un valor inválido explícito o `Unknown`
  cuando el cero no deba significar un estado válido; `String()` si se muestra.
- Tiempo: `time.Duration` y `time.Time`, nunca `int` con unidades implícitas.
  Dinero: tipo decimal del proyecto o enteros en unidad mínima; nunca `float64`
  para importes salvo que el contrato existente lo imponga (regístralo).

## Genéricos

Úsalos para el mismo algoritmo sobre varios tipos concretos (`Map`, `Min`,
contenedores). Restricciones con significado (`comparable`, `cmp.Ordered`,
interfaces de métodos). No los uses para jerarquías, servicios o repositorios
genéricos, ni `any` como "aún no sé el tipo". Generaliza cuando exista
duplicación real, no por anticipación. Antes de escribir un helper, comprueba
`slices`, `maps`, `cmp` según la versión objetivo.

## Dependencias

- Biblioteca estándar primero: `net/http` (patrones de método y ruta desde 1.22),
  `log/slog` (1.21), `slices`/`maps`/`cmp` (1.21), `errors.Join` (1.20).
- Si el proyecto ya usa un framework (gin, echo, chi, fiber, cobra, viper, fx,
  wire, testify, sqlc, gorm), síguelo; no lo sustituyas por la librería estándar
  dentro de una feature.
- Añadir un módulo nuevo es una decisión con superficie de seguridad y licencia:
  justifícalo frente a la alternativa estándar, usa `go get modulo@version`
  explícito, revisa el diff de `go.mod`/`go.sum` y, si cambian dependencias,
  ejecuta `govulncheck` cuando esté disponible.
- No edites `go.sum` a mano ni borres entradas para "limpiar". `go mod tidy`
  solo cuando el cambio altera imports, y revisa que no arrastre upgrades ajenos.
- Herramientas de desarrollo: respeta el mecanismo existente (`tool` en
  `go.mod` desde 1.24, `tools.go` con imports en blanco, Makefile). No migres
  entre ellos dentro de una feature.

## APIs públicas y compatibilidad

En un módulo consumido por otros (librería, SDK, `pkg/`), una firma exportada es
contrato: cambiar parámetros, tipos de retorno, campos exportados, errores
sentinela, tags JSON o comportamiento de valor cero puede romper consumidores.
Aplica [contratos y datos](../../contracts-and-data.md). Prefiere añadir una
función o una opción nueva antes que cambiar una firma; respeta la ruta `/vN` del
módulo para cambios mayores y no la inventes sin decisión.

## Código generado

Identifica la fuente: `.proto` (+ `buf`/`protoc`), `sqlc.yaml`, `//go:generate`
(`mockgen`, `stringer`, `enumer`), `wire.go` (`//go:build wireinject`), OpenAPI
(`oapi-codegen`). Modifica la fuente y ejecuta el comando del proyecto; nunca
parches `*.pb.go`, `wire_gen.go`, `*_mock.go` o archivos con
`// Code generated ... DO NOT EDIT.` como sustituto. Si el generador no está
disponible, entrega el cambio de fuente con la regeneración como `not_run`.
