# Revisión y diagnóstico en Go

Complementa [diagnóstico y revisión](../../review-and-debugging.md). La revisión
de cumplimiento va primero y no cambia; esta lista concreta la revisión de
**calidad** para el diff Go. Clasifica por impacto observable: una preferencia
compatible con el proyecto no bloquea.

## Lista de calidad del diff

**Bloqueante** (defecto probable o riesgo de seguridad/datos)

- Error ignorado en una operación con efecto (escritura, commit, `Close` de un
  writer, `Shutdown`), o error comparado por texto.
- Goroutine sin camino de salida, `select` de larga vida sin `ctx.Done()`,
  `wg.Add` dentro de la goroutine, canal cerrado por el receptor.
- Map o estado compartido accedido sin sincronización desde varias goroutines.
- `defer rows.Close()` o `rows.Err()` ausentes; `resp.Body` sin cerrar; `cancel`
  de contexto sin llamar.
- SQL o comando de shell construido con entrada externa; secretos o PII en logs;
  `math/rand` para tokens.
- `nil` tipado devuelto como `error` o interfaz.
- Feature posterior a la directiva `go`, o directiva/toolchain subidos sin mandato.
- Archivo generado editado a mano; `go.sum` editado manualmente.

**Mayor** (mantenibilidad o contrato)

- Error devuelto sin contexto o con `%v` donde el llamador necesita `errors.Is/As`;
  log-y-return del mismo error.
- Cambio de firma exportada, sentinela o tag JSON sin evaluar consumidores.
- Interfaz definida en el productor "para mockear", o abstracción con una sola
  implementación sin necesidad de sustitución.
- Estado global mutable, `init()` con I/O, dependencia oculta en vez de
  inyectada por constructor.
- `context.Context` almacenado en un struct o no propagado a I/O.
- Servidor/cliente HTTP sin timeouts en código productivo.
- Test que no puede fallar (sin aserción relevante, `time.Sleep` como
  sincronización, resultado cacheado presentado como evidencia).
- Paquete `utils/common` nuevo o ampliado con lógica de dominio.

**Menor** (idioma y estilo, si el linter del proyecto no lo decide ya)

- Nombres no idiomáticos (`GetX`, `MAX_SIZE`, tartamudeo, `this`), iniciales
  con caja mixta (`Id`, `Url`).
- Forma antigua donde la versión permite la moderna en líneas nuevas
  ([tabla](go-modern-by-version.md)).
- Anidamiento evitable: camino feliz indentado, `else` tras `return`.
- Doc comment ausente en símbolo exportado nuevo (empieza por el nombre).

Antes de reportar, vuelve a leer cada hallazgo contra el diff y elimina los que
no puedas justificar con archivo y línea concretos.

## Diagnóstico Go dirigido por evidencia

Sigue el protocolo general (síntoma, hipótesis discriminante, experimento mínimo).
Herramientas y señales específicas:

| Síntoma | Primera observación discriminante |
|---|---|
| Panic | Leer la traza completa (`GOTRACEBACK=all` si hay goroutines); localizar el primer frame propio |
| Resultado intermitente | `go test -race -count=20 -run TestX`; `-shuffle=on` para dependencia de orden |
| Bloqueo o test colgado | `go test -timeout 30s` para obtener el volcado de goroutines; buscar canales sin emisor/receptor y locks no liberados |
| Fuga de goroutines | Volcado `/debug/pprof/goroutine?debug=2` o `runtime.NumGoroutine()` antes/después; `goleak` si existe |
| Error envuelto "perdido" | Buscar `%v` donde se esperaba `%w`, o un error reemplazado en vez de envuelto |
| `nil` inesperado en interfaz | Verificar si se devolvió un puntero tipado `nil` |
| Mutación inesperada de slice | Aliasing de `append` sobre un backing array compartido; copiar con `slices.Clone` |
| Lentitud | Medir antes de cambiar: benchmark + `pprof` CPU/mem; no optimizar por intuición |
| Depuración paso a paso | `dlv test ./pkg -- -test.run TestX` si Delve está disponible |

El toolchain de Go casi nunca es la causa. Si un error persiste tras una edición,
comprueba en este orden: la edición no corrigió la lógica; se editó el archivo,
función o paquete equivocado; existe otra llamada con el mismo defecto; el error
viene de otra ruta de código. Confirma qué se compila con
`go list -f '{{.GoFiles}}' ./pkg` y que la ejecución llega al punto con un
`t.Log` temporal. No limpies la caché (`go clean -cache`) como primera hipótesis
y usa `-count=1` para descartar resultados cacheados.

## Entrega a `code-review`

Cuando el revisor independiente esté disponible, incluye en el expediente la
directiva `go`, los comandos de la escalera ejecutados con su resultado y los
paquetes cubiertos. No le entregues esta lista como conclusión: es tu
auto-revisión; el revisor aplica su propio criterio.
