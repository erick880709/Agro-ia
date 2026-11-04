# Errores, contexto y concurrencia en Go

## Errores

1. Comprueba todo error devuelto. Descartarlo con `_` requiere una razón visible
   (por ejemplo, `Close` de un reader de solo lectura ya consumido).
2. Envuelve con contexto de la operación: `fmt.Errorf("loading account %s: %w", id, err)`.
   Mensajes en minúscula, sin puntuación final, describiendo qué se intentaba.
3. `%w` conserva la cadena para `errors.Is/As`; usa `%v` en un límite donde no
   quieras exponer el error interno como parte de tu contrato.
4. Inspección: `errors.Is` para sentinelas, `errors.As` para tipos;
   `errors.AsType[T]` solo con directiva `go` ≥ 1.26. Nunca `err == ErrX` ni
   comparación de `err.Error()` contra un texto.
5. Sentinela (`var ErrNotFound = errors.New("not found")`) para condiciones
   esperadas que el llamador ramifica; tipo de error para transportar datos.
   Crear, renombrar o dejar de devolver un sentinela exportado es cambio de contrato.
6. Regla de manejo único: un error se registra **o** se devuelve, no ambos. Se
   registra en el límite (handler, worker loop, `main`), se propaga en el resto.
7. `errors.Join` (≥ 1.20) para errores independientes (validación múltiple,
   cierre de varios recursos), no para encadenar contexto.
8. `panic` solo para invariantes de programación imposibles o `MustX` en
   inicialización con valores literales. Recupera (`recover`) únicamente en
   límites de goroutine/servidor para no tumbar el proceso, registrando y
   convirtiendo a error.
9. Traduce errores en el límite: un handler HTTP/gRPC mapea errores de dominio a
   códigos (`404`, `codes.NotFound`) sin filtrar detalles internos al cliente.
10. Sin valores mágicos en banda (`-1`, `""`, `nil` con significado): usa
    `(valor, ok bool)` o `(valor, error)`.

## `context.Context`

- Primer parámetro (`ctx context.Context`) de toda función que haga I/O, espere o
  lance trabajo; nunca guardado en un struct ni `nil` (usa `context.TODO()` si no
  hay contexto disponible y regístralo como deuda).
- Propaga el contexto recibido; no crees `context.Background()` a mitad de una
  petición. Usa las variantes `...Context` (`QueryContext`, `NewRequestWithContext`).
- Todo `WithCancel/WithTimeout/WithDeadline` lleva `defer cancel()`.
- Trabajo que debe sobrevivir a la petición: `context.WithoutCancel(ctx)` (≥ 1.21)
  más su propio timeout y un dueño que lo espere.
- Valores en contexto solo para datos con alcance de petición transversales
  (request ID, trazas, identidad autenticada), con clave de tipo no exportado.
  Nunca dependencias, configuración ni parámetros opcionales.
- Respeta cancelación en bucles largos: comprueba `ctx.Err()` o `ctx.Done()`.

## Goroutines y sincronización

Antes de lanzar una goroutine responde: ¿cómo termina?, ¿quién la espera?,
¿cómo se le señala parar?, ¿quién cierra cada canal?, ¿hace falta concurrencia
o basta código síncrono? Si no puedes responder, no la lances.

| Necesidad | Usa |
|---|---|
| Esperar tareas sin error | `sync.WaitGroup` (`wg.Go` con `go` ≥ 1.25; antes `Add` antes del `go` y `defer Done`) |
| Esperar y propagar primer error, cancelar hermanas | `errgroup.WithContext` |
| Limitar concurrencia | `errgroup.Group.SetLimit(n)` o semáforo existente; no pools rígidos a mano |
| Estado compartido simple | `sync.Mutex`/`RWMutex` con secciones críticas cortas, sin I/O dentro |
| Contadores/flags | Atómicos tipados (`atomic.Int64`, `atomic.Bool`, ≥ 1.19) |
| Inicialización perezosa | `sync.Once`, `sync.OnceValue`/`OnceFunc` (≥ 1.21) |
| Deduplicar llamadas concurrentes | `singleflight` si el proyecto lo usa o lo justifica |

- Solo el emisor cierra un canal; declara dirección (`<-chan`, `chan<-`) en
  firmas. Canales sin buffer por defecto; un buffer necesita razón.
- Todo `select` de larga vida incluye `case <-ctx.Done():`.
- No uses `time.After` dentro de un bucle de larga vida; usa `time.NewTimer`/`Reset`
  o un `Ticker` con `Stop`.
- Un map compartido sin sincronización provoca un fallo fatal en concurrencia,
  no solo datos corruptos.
- Las variables de bucle son por iteración desde 1.22: no añadas `v := v` si la
  directiva es ≥ 1.22; con < 1.22 sí son necesarias al capturar en closures.

## Workers y consumidores

Separa ciclo de vida (`Start(ctx)`/`Run(ctx) error`, `Stop`/`Shutdown(ctx)`) del
handler de un mensaje. Define idempotencia en el límite que la garantiza (clave
única en DB, registro de IDs procesados con sincronización), ack/nack y
reintentos según [contratos y datos](../../contracts-and-data.md). Un worker que
recibe tras `Stop` debe rechazar de forma observable, no ignorar en silencio.

## HTTP

- Servidor productivo con `http.Server` y timeouts (`ReadHeaderTimeout` como
  mínimo, más `ReadTimeout`/`WriteTimeout`/`IdleTimeout` según la operación); no
  `http.ListenAndServe` desnudo en código nuevo.
- Apagado ordenado: `signal.NotifyContext` + `srv.Shutdown(ctxConTimeout)` con un
  contexto nuevo (el de señal ya está cancelado).
- Cliente: `http.Client` con `Timeout` o contexto con deadline; nunca
  `http.DefaultClient` sin límite para dependencias externas. Cierra siempre
  `resp.Body` (y drénalo si reutilizas conexiones).
- Limita el tamaño de cuerpos de entrada (`http.MaxBytesReader`) y valida antes
  de usar. Middleware es `func(http.Handler) http.Handler`; sigue el router que
  el proyecto ya usa.

## Base de datos

- Consultas parametrizadas siempre; nunca concatenar entrada en SQL.
- `defer rows.Close()` y comprobar `rows.Err()` tras iterar; `sql.ErrNoRows`
  mapeado a un error de dominio.
- Transacciones: `tx, err := db.BeginTx(ctx, opts)`; `defer tx.Rollback()`
  (inofensivo tras `Commit`); `Commit` con error comprobado.
- Columnas nulas con `sql.Null*` o punteros según el patrón del proyecto.
- Usa el mecanismo del proyecto (`database/sql`, `pgx`, `sqlc`, `gorm`, `sqlx`) y
  su herramienta de migraciones; aplica la sección de persistencia de
  [contratos y datos](../../contracts-and-data.md) antes de ejecutar migraciones.

## Logging y seguridad

- `*slog.Logger` (o el logger del proyecto) inyectado como dependencia; mensajes
  estáticos y atributos clave-valor; niveles coherentes. No `fmt.Println` ni
  `log.Printf` para logging operativo en código nuevo si el proyecto ya tiene
  logger estructurado.
- Nunca registres secretos, tokens, PII ni el cuerpo completo de peticiones.
- `crypto/rand` para tokens y claves; `math/rand/v2` solo para no seguridad.
- Rutas de archivos de entrada: limita a una raíz (`os.Root` con ≥ 1.24, o
  validación equivalente) contra path traversal. Comandos externos con
  `exec.CommandContext` y argumentos separados, nunca `sh -c` con entrada.
- Comparación de secretos con `subtle.ConstantTimeCompare`.
