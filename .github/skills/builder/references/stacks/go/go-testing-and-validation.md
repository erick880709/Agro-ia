# Pruebas y validación en Go

## Descubrir comandos antes de inventarlos

Busca en este orden y usa lo que el proyecto ya define: `Makefile`/`Taskfile.yml`/
`magefile.go` (targets `test`, `lint`, `check`, `generate`), workflows de CI,
`CONTRIBUTING.md`/`README`, `.golangci.yml`. Los comandos de esta guía son el
fallback cuando el proyecto no declara otros. `go_toolkit.py discover` lista lo
encontrado.

## Escalera de validación

Ejecuta de lo barato a lo caro y detente a corregir en el primer fallo nuevo.
Acota a los paquetes afectados y sus importadores directos; amplía a `./...`
al cerrar o si el cambio toca tipos compartidos.

| Paso | Comando fallback | Cuándo |
|---|---|---|
| Formato | `gofmt -l <paquetes>` (o `goimports -l` si el proyecto lo usa) | Siempre; lista vacía = ok. No reformatees archivos ajenos al cambio |
| Análisis | `go vet <paquetes>` | Siempre |
| Build | `go build ./...` | Siempre; incluye binarios en `cmd/` |
| Tests focalizados | `go test -count=1 -run '<TestX>' <paquete>` | Por incremento |
| Tests del módulo | `go test -count=1 ./...` | Al cerrar |
| Carreras | `go test -race -count=1 <paquetes>` | Si el cambio toca goroutines, canales, estado compartido o handlers concurrentes. Requiere CGO; si no está disponible, `not_run` con razón |
| Orden | `-shuffle=on` | Si sospechas dependencia entre tests |
| Integración | `go test -tags=integration ./...` (o el tag del proyecto) | Solo con entorno aislado verificado |
| Linter | `golangci-lint run <paquetes>` | Solo si existe configuración o el proyecto lo usa en CI; no crees `.golangci.yml` en una feature |
| Módulo | `go mod tidy -diff` (≥ 1.23) o comparar `go.mod/go.sum` tras `go mod tidy` | Si cambiaron imports o dependencias |
| Vulnerabilidades | `govulncheck ./...` | Si cambian dependencias o código sensible, y la herramienta existe |
| Generado | Comando de generación del proyecto y `git diff --exit-code` sobre lo generado | Si cambió una fuente de generación |

`-count=1` evita presentar como evidencia un resultado cacheado (`(cached)`).
Registra en la evidencia la salida resumida, no el log completo.

`go_toolkit.py validate` ejecuta formato, vet, build y tests (y opcionalmente
race y linter) sobre los paquetes indicados, sin modificar archivos, y devuelve
filas de evidencia `passed/failed/not_run`. No descarga herramientas.

## Pruebas que demuestran comportamiento

- Tabla de casos con subtests nombrados (`t.Run(tt.name, ...)`), incluyendo
  límites y caminos de error, no solo el camino feliz.
- Archivo de test nombrado por el archivo fuente (`pricing.go` →
  `pricing_test.go`); `package x_test` para probar la API pública y `package x`
  solo cuando necesites internos.
- Helpers con `t.Helper()`; limpieza con `t.Cleanup`; directorios con
  `t.TempDir()`; variables de entorno con `t.Setenv` (incompatible con
  `t.Parallel`). Contexto de test: `t.Context()` con `go` ≥ 1.24, si no
  `context.WithCancel(context.Background())` + `t.Cleanup(cancel)`.
- `t.Parallel()` solo en tests realmente independientes y si el paquete ya lo
  practica; no lo añadas a tests con estado global.
- Fakes manuales en límites de I/O mediante interfaces del consumidor; mocks
  generados solo si el proyecto ya usa `mockgen`/`mockery`. Testify solo si ya
  está en `go.mod`; con testify, crea `assert.New(t)` dentro de cada subtest.
- HTTP: `httptest.NewRecorder`/`httptest.NewServer`; aserta código, cabeceras y
  cuerpo relevantes, no solo `200`.
- Comparaciones: `reflect.DeepEqual` o `go-cmp` si el proyecto lo usa, con
  mensajes `got X, want Y` que identifiquen la entrada.
- Concurrencia y tiempo: sin `time.Sleep` para "esperar" goroutines. Usa canales,
  `WaitGroup`, relojes inyectados o `testing/synctest` (estable con `go` ≥ 1.25;
  experimental en 1.24). Detección de fugas con `goleak` solo si ya está
  disponible.
- Entradas complejas o salidas grandes: `testdata/` y golden files con flag de
  actualización explícito.
- Parsers, decodificadores y validadores de entrada externa: considera un
  `FuzzX` con corpus semilla cuando el riesgo lo justifique.
- Benchmarks solo si el encargo es de rendimiento: `b.Loop()` con `go` ≥ 1.24,
  comparación con `benchstat`; una optimización sin medición no es evidencia.

## Tests de integración

Sepáralos con build tag (`//go:build integration`) o la convención del proyecto
(`testing.Short()`, carpeta dedicada). Requieren destino aislado verificado:
contenedores locales del propio proyecto o `testcontainers-go` si ya se usa.
Un fake o `httptest` demuestra lógica local, no compatibilidad con el servicio
real: declara la integración externa como pendiente.

## Comprobar que la prueba puede fallar

Para un bug, la prueba nueva debe fallar en la versión inicial por la aserción
del defecto, no por compilación. Para lógica crítica, una mutación controlada en
un workspace aislado (invertir una condición, quitar el `%w`, eliminar el
registro de idempotencia) debe hacer fallar la prueba; revierte la mutación y
registra el resultado.

## Contexto de la evidencia

Registra `go version`, directiva `go` del módulo, `GOOS/GOARCH`, `CGO_ENABLED`,
build tags y flags usados, paquetes ejecutados y la revisión o hashes validados.
Distingue fallos preexistentes (comprobados antes del cambio), regresiones y
falta de entorno (toolchain, CGO, servicio) según [validación](../../validation.md).
