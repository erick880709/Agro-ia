# Perfil de seguridad Go

Complementa los perfiles Go de builder. La directiva `go` de `go.mod` limita las APIs
disponibles (p. ej. `crypto/rand.Text()` desde 1.24, `os.Root` desde 1.24,
`filepath.IsLocal` desde 1.20): no recomiendes una API posterior a la directiva sin
señalar la actualización.

## Tabla de contenido

1. Herramientas propias del ecosistema
2. HTTP y autenticación
3. Inyección y archivos
4. Criptografía y aleatoriedad
5. Concurrencia y recursos
6. Errores y logging

## 1. Herramientas propias del ecosistema

- `govulncheck ./...`: reporta CVE solo si la función vulnerable es **alcanzable** desde
  el código; prioriza sus hallazgos sobre listados por versión.
- `gosec ./...` y Semgrep `p/golang`: candidatos (alto ruido en G104/G304; verifica).
- `go vet` y `staticcheck` detectan usos incorrectos que también son de seguridad
  (copias de `sync.Mutex`, `printf` con formato de entrada).

## 2. HTTP y autenticación

- `http.ListenAndServe` / `http.Server{}` sin `ReadHeaderTimeout`, `ReadTimeout`,
  `WriteTimeout`, `IdleTimeout` → Slowloris (CWE-400). Sin `http.MaxBytesReader` en
  cuerpos → consumo sin límite (API4).
- Middlewares de auth registrados en un sub-router pero no en otro; rutas nuevas
  añadidas al `mux` raíz fuera del grupo protegido.
- JWT (`golang-jwt/jwt/v5`): `jwt.Parse` con `keyFunc` que no verifica
  `token.Method` (confusión de algoritmo) o sin `jwt.WithValidMethods`,
  `jwt.WithAudience`, `jwt.WithIssuer`; `ParseUnverified` en rutas de decisión.
- `tls.Config{InsecureSkipVerify: true}` fuera de tests aislados → bloqueante;
  `MinVersion` < TLS 1.2.
- CORS manual con `Access-Control-Allow-Origin` reflejando `Origin` + credenciales.
- Cookies sin `HttpOnly`, `Secure`, `SameSite`.

## 3. Inyección y archivos

- `db.Query(fmt.Sprintf(...))`, `db.Exec("..."+x)` → usa placeholders (`$1`, `?`).
  ORMs: `gorm.Raw`/`Where(string)` con concatenación.
- `exec.Command("sh", "-c", input)` o `exec.Command(input, ...)`: lista blanca del binario
  y argumentos separados; nunca shell.
- `filepath.Join(base, userInput)` no confina: usa `filepath.IsLocal`, o `os.Root`
  (1.24+), o verificación de prefijo tras `filepath.Clean` y resolución de symlinks.
- `text/template` para HTML (no escapa) en vez de `html/template`; `template.HTML(input)`
  anula el escape.
- Descompresión (zip/tar) sin validar rutas (*zip slip*) ni tamaño total (bomba).
- `encoding/gob` o `yaml.Unmarshal` en tipos con efectos sobre entrada no confiable;
  `json.Decoder` sin `DisallowUnknownFields` cuando el contrato lo exige (mass assignment).

## 4. Criptografía y aleatoriedad

- `math/rand` o `math/rand/v2` para tokens, OTP, nonces → `crypto/rand`
  (`rand.Text()` en 1.24+).
- Comparación de tokens/MAC con `==` o `bytes.Equal` → `subtle.ConstantTimeCompare` /
  `hmac.Equal`.
- `crypto/md5`, `crypto/sha1`, `crypto/des` para seguridad; AES-GCM con nonce fijo o
  contador reutilizado; llaves en el binario.
- Contraseñas: `golang.org/x/crypto/argon2` o `bcrypt`, nunca SHA-256 simple.

## 5. Concurrencia y recursos

- Carreras sobre saldos, cupos, contadores de intentos (TOCTOU): `go test -race` y
  revisión de la transacción en BD (`SELECT ... FOR UPDATE`, condición en `UPDATE`).
- Goroutines por request sin límite ni `context` con timeout → agotamiento.
- `panic` en handler sin `recover` en servidores que no lo ponen por defecto (frameworks
  propios, workers): un request tumba el proceso (disponibilidad high si es sin auth).

## 6. Errores y logging

- `if err != nil { return nil }` en verificación de firma/autorización → fail-open.
- `log.Printf("%+v", req)` o `slog` con structs que contienen tokens/PII; implementa
  `LogValue()` (`slog.LogValuer`) para redactar.
- Errores internos (`err.Error()`) devueltos al cliente con detalles de BD o rutas.
