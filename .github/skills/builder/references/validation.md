# Validación por riesgo

## Seleccionar evidencia

Descubre comandos en manifiestos, documentación y configuración existente. Ejecuta
la suite pertinente al paquete y dependencias afectadas. No inventes nombres de
comandos ni uses éxito de compilación como sustituto de aceptación funcional.

| Cambio | Comprobaciones a considerar |
|---|---|
| Edición declarativa/trivial | Diff e inspección o validador específico; sin tests espejo |
| Bug | Reproducción que falla antes, pasa después y protege comportamiento vecino |
| Regla o cálculo | Casos representativos y límites; propiedades si hay invariantes útiles |
| API/contrato | Serialización, errores, consumidores y compatibilidad relevantes |
| Permisos | Caso autorizado y denegado; acceso a recurso ajeno y ausencia de efectos |
| Persistencia | Migración aislada, datos anteriores, constraints y consultas afectadas |
| UI | Interacción y estados relevantes, accesibilidad y revisión visual si aplica |
| Worker/integración | Ciclo de vida, comunicación y efectos en el límite real pertinente |
| Refactor | Caracterización y regresión del comportamiento preservado |
| Scaffold Clean Architecture | `validateStructure` y `ArchitectureTest` de app-service, además de las pruebas del módulo |
| Código reactivo | `StepVerifier` con `expectNext`/`expectError` y `verify*`; sin `.block()` en producción |
| Go | `gofmt -l`, `go vet`, build y `go test -count=1` focalizado; `-race` si hay concurrencia; ver [perfil Go](stacks/go/go-testing-and-validation.md) |
| Angular | Typecheck app/spec, lint si existe, `ng test --watch=false` focalizado con el runner del proyecto; `ng build` si cambian rutas, configuración o presupuestos; ver [perfil Angular](stacks/angular/angular-testing-and-validation.md) |
| Angular con APIs nuevas de `@angular/*` | `angular_toolkit.py unstable` sin hallazgos o mandato explícito para la API experimental |
| Java/Spring | Compilación y tests focalizados con el wrapper; `validateStructure`/ArchUnit si cambian módulos o paquetes; `StepVerifier` con `verify*` en reactivo; ver [perfil Java/Spring](stacks/java-spring/spring-testing-and-validation.md) |
| Idempotencia o concurrencia | Prueba con N tareas simultáneas y varias rondas; un test secuencial de duplicados no es evidencia |
| Go con dependencias nuevas | Diff de `go.mod`/`go.sum`, `go mod tidy -diff` cuando aplique y `govulncheck` si está disponible |

La tabla no exige todas las suites en cada tarea. Elige según riesgo y justifica
omisiones materiales. Para bugs o lógica nueva sin tests previos, añade una prueba
focalizada usando el runner existente o un mecanismo mínimo compatible. Si no es
viable automatizar, usa una comprobación reproducible y declara su límite; no
introduzcas todo un framework sin necesidad.

## Ejecutar y revisar

Prueba incrementos enfocados; al terminar ejecuta las comprobaciones de integración
entre componentes cambiados y los checks exigidos por el proyecto. Si pasan, amplía
solo por nuevo impacto, fallo o duda concreta. Las pruebas deben fallar por una
violación de comportamiento, no solo comprobar que existe una función o un archivo.

No asumas independencia porque código y test se generaron juntos. Contrasta casos
contra la fuente funcional y busca escenarios negativos que contradigan la
interpretación más cómoda. Para lógica crítica, una mutación controlada en un
workspace aislado puede demostrar que la prueba detecta el defecto; no es un
requisito universal. No debilites una aserción válida para obtener verde.

Registra fallos preexistentes, fallos nuevos y falta de entorno por separado. No
marques toda la tarea bloqueada si puedes continuar componentes independientes.
Un servicio real ausente puede permitir unit tests, pero no una afirmación de
integración completa. No instales ni llames servicios remotos con efectos para
evitar un `not_run` sin autorización apropiada.

## Cierre

Revisa que registros y entrypoints realmente usen la implementación y que el diff
no incluya modificaciones ajenas. Conserva criterios aceptados y enlaza resultados
según [especificación y evidencia](spec-and-evidence.md). La cobertura porcentual
es auxiliar: no demuestra cumplimiento de reglas o ausencia de regresiones.

Builder ejecuta su validación aunque exista Ranger. Para estrategia amplia, pruebas
especializadas o revisión independiente necesaria por riesgo, entrega a QA fuentes,
criterios, cambios, comandos, resultados y pendientes. No exijas Ranger instalado
para un cambio ordinario ni declares sus futuras comprobaciones como ya ejecutadas.
