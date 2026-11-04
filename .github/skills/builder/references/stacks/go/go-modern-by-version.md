# Go moderno por versión

Los modelos tienden a generar Go antiguo por frecuencia en los datos de
entrenamiento, y desconocen features posteriores a su corte. Esta tabla corrige
ambas cosas **dentro del límite de la directiva `go` del módulo**.

## Cómo aplicarla

1. Lee `go 1.N` del `go.mod` afectado. Solo son elegibles las filas con versión
   ≤ N. Una feature de lenguaje posterior no compila; una API posterior compila
   con un toolchain nuevo pero rompe en CI con el toolchain declarado (`go vet`
   la reporta mediante `stdversion` desde 1.23).
2. Aplica la forma moderna en el código que creas o modificas. No reescribas
   código existente fuera del alcance para "modernizarlo": eso es un refactor
   con su propio encargo. `gofmt`/`go vet` no hacen esa migración por ti.
3. Si el proyecto declara un linter o una convención contraria, prevalece.
4. Si la directiva es más nueva que esta tabla o dudas de una API, comprueba la
   documentación de la versión (`go doc <símbolo>` con el toolchain del proyecto)
   antes de usarla. No inventes APIs.
5. Herramientas opcionales si ya están instaladas o autorizadas: el CLI de
   `JetBrains/go-modern-guidelines` (`list --file-path <archivo>`) y los
   modernizadores de `gopls`/`go fix`. Úsalos sobre los archivos del cambio, no
   sobre todo el repositorio.

## Tabla

| Go | En lugar de | Usa |
|---|---|---|
| 1.13 | `err == ErrX`, `err.(*T)` | `errors.Is`, `errors.As` |
| 1.18 | `interface{}` | `any` |
| 1.18 | `strings.Index` + slicing manual | `strings.Cut` / `bytes.Cut` |
| 1.19 | `atomic.AddInt64(&n, 1)` | `var n atomic.Int64; n.Add(1)` (`atomic.Bool`, `atomic.Pointer[T]`) |
| 1.19 | `append(b, fmt.Sprintf(...)...)` | `fmt.Appendf(b, ...)` |
| 1.20 | Varios errores concatenados a mano o `multierr` | `errors.Join` |
| 1.20 | `HasPrefix` + `TrimPrefix` | `strings.CutPrefix` / `CutSuffix` |
| 1.20 | Cancelación sin causa | `context.WithCancelCause` + `context.Cause` |
| 1.20 | `append([]byte(nil), b...)` | `bytes.Clone` |
| 1.21 | `if a < b {...}` para mínimo/máximo | `min(a, b)`, `max(a, b)` |
| 1.21 | Bucle de búsqueda/índice | `slices.Contains`, `slices.Index`, `slices.IndexFunc` |
| 1.21 | `sort.Slice`, `sort.Strings` | `slices.Sort`, `slices.SortFunc(s, func(a, b T) int { return cmp.Compare(...) })`; estable: `slices.SortStableFunc` |
| 1.21 | Copias y borrados manuales | `slices.Clone`, `maps.Clone`, `maps.Copy`, `maps.DeleteFunc`, `clear(m)` |
| 1.21 | `slices.Max/Min/Reverse/Compact` escritos a mano | Las funciones de `slices` |
| 1.21 | `sync.Once` + closure | `sync.OnceFunc`, `sync.OnceValue`, `sync.OnceValues` |
| 1.21 | `log`, `fmt.Println` para logging operativo | `log/slog` (si el proyecto no tiene otro logger estructurado) |
| 1.21 | Detach manual de cancelación | `context.WithoutCancel`, `context.AfterFunc` |
| 1.22 | `for i := 0; i < n; i++` | `for i := range n` |
| 1.22 | `v := v` antes de un closure | Nada: variable por iteración |
| 1.22 | Cadena `if x == "" { x = def }` | `cmp.Or(x, def)` |
| 1.22 | Router externo solo por método/parámetro | `mux.HandleFunc("GET /items/{id}", h)` + `r.PathValue("id")` (si el proyecto no usa otro router) |
| 1.22 | `math/rand` | `math/rand/v2` (`rand.IntN`, `rand.N`) |
| 1.22 | `reflect.TypeOf((*T)(nil)).Elem()` | `reflect.TypeFor[T]()` |
| 1.22 | `append(append(a, b...), c...)` | `slices.Concat(a, b, c)` |
| 1.23 | Bucle para recolectar claves | `slices.Sorted(maps.Keys(m))`, `slices.Collect(it)` |
| 1.23 | Iterador propio `Next()/HasNext()` | `iter.Seq[T]` / `iter.Seq2[K,V]` con `range` |
| 1.23 | `time.NewTicker` solo para evitar fuga en GC | `time.Tick` vuelve a ser seguro si encaja |
| 1.24 | `ctx, cancel := context.WithCancel(...)` en tests | `t.Context()` (no lo uses en `t.Cleanup`) |
| 1.24 | `for i := 0; i < b.N; i++` | `for b.Loop()` |
| 1.24 | `omitempty` en `time.Time`/structs | `omitzero` (mantén `omitempty` en strings, slices, maps) |
| 1.24 | `strings.Split` solo para iterar | `strings.SplitSeq`, `strings.FieldsSeq`, `strings.Lines` |
| 1.24 | `tools.go` con imports en blanco | Directiva `tool` (`go get -tool`, `go tool x`) — solo en proyectos que ya la adopten |
| 1.24 | Validación manual de rutas bajo un directorio | `os.Root` / `os.OpenRoot` |
| 1.24 | Token aleatorio con encoding manual | `crypto/rand.Text()` |
| 1.25 | `wg.Add(1); go func(){ defer wg.Done(); ... }()` | `wg.Go(func(){ ... })` |
| 1.25 | Reloj falso propio o `time.Sleep` en tests concurrentes | `testing/synctest` (`synctest.Test`) |
| 1.26 | `var target *T; errors.As(err, &target)` | `errors.AsType[*T]` aplicado a `err`; devuelve `(target, ok)` |
| 1.26 | Helper `ptr(v)` o variable temporal para `&v` | `new(v)` con expresión |
| 1.27 | `encoding/json` en código JSON **nuevo** | `encoding/json/v2` (no migres código existente sin encargo) |
| 1.27 | `LastIndex` + slicing | `strings.CutLast` / `bytes.CutLast` |
| 1.27 | Librería UUID de terceros | Paquete `uuid` estándar (si el proyecto no tiene ya una dependencia establecida) |
| 1.27 | Copia manual de `url.URL`/`url.Values` | `URL.Clone`, `Values.Clone` |
| 1.27 | `Outer{Inner: Inner{F: v}}` | Campos promovidos en el literal: `Outer{F: v}` |

Las filas 1.26–1.27 provienen de `go-modern-guidelines` (JetBrains). Confirma con
las release notes del toolchain del proyecto antes de usarlas por primera vez.

## Sintaxis que nunca debe generarse

- `// +build` (usa `//go:build`).
- `ioutil.*` (usa `io` y `os`, desde 1.16).
- `interface{}` en código nuevo con directiva ≥ 1.18.
- `rand.Seed` en código nuevo con directiva ≥ 1.20 (el generador global se
  siembra solo).
