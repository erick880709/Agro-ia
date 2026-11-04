# Especificación y evidencia del cambio

## Fuentes y ubicación

Usa primero el issue, spec o expediente existente, sea Markdown, OpenSpec, Spec
Kit u otro formato. No inicialices otra herramienta SDD por defecto. Un texto de
usuario suficientemente concreto es una fuente válida. Al leer una subtarea,
consulta el padre si es accesible y necesario para interpretar el alcance.

Si hay que conservar una copia local de un issue, registra ID/URL, revisión o
fecha de consulta y campos pertinentes. No sobrescribas anotaciones locales ni
guardes secretos o adjuntos innecesarios. Leer un issue no autoriza comentarlo,
cambiar su estado o marcar sus criterios remotamente; eso solo procede con la
preferencia de cierre aceptada al conectar el tablero ([tablero de trabajo por
MCP](work-tracking-mcp.md)).

Para estándar/reforzado sin ubicación establecida, usa `docs/changes/<id>/` como
fallback local: `spec.md`, y `plan.md`/`evidence.md` si el volumen o la reanudación
justifican separarlos. Si se usa `code-review`, su reporte vive en la misma carpeta
como `review.md`. No crees una carpeta por cada edición trivial. IDs recibidos
de fuentes se normalizan como un nombre de carpeta, nunca como rutas ejecutables.

## Contenido mínimo

Registra lo necesario para que otra sesión implemente o revise el mismo cambio:

| Información | Qué debe dejar claro |
|---|---|
| Identidad y fuente | ID estable, intención, referencias y revisiones disponibles |
| Modo y rigor | Alcance afectado y razón del nivel elegido |
| Estado observado | Flujo actual relevante y evidencia; no inventario global |
| Comportamiento deseado | Actores, precondiciones, resultados y errores relevantes |
| Aceptación | IDs estables como AC-01, con escenarios comprobables |
| Preservación | Comportamiento/contratos existentes que el cambio debe conservar |
| Restricciones | Arquitectura, seguridad, datos, compatibilidad y UX pertinentes |
| Pendientes | Distinguir hecho, inferencia, propuesta y decisión pendiente |
| Validación | Comprobación por criterio o conjunto relacionado |

La spec describe qué debe pasar; el plan explica cómo. Usa ejemplos Given/When/Then
o prosa precisa según el proyecto; no exijas una sintaxis para aceptar requisitos.
No conviertas un nombre de clase, una operación CRUD o una tabla en requisito sin
fuente. Si un criterio ya existe, reutiliza su ID.

Un plan útil identifica enfoque, tareas, dependencias, rutas o zonas afectadas y
comandos de validación descubiertos. Solo incluye alternativas, orden de migración
o rollback/compensación si ese cambio los necesita. No define arquitectura global.

## Evidencia

Para cada criterio relevante registra la comprobación y su resultado real. Puede
haber varias pruebas por criterio o una prueba que cubra varios; no fuerces tests
que copien la estructura del código.

| Campo | Contenido |
|---|---|
| Criterio | ID(s) del comportamiento o restricción |
| Comprobación | Test/archivo y comando, o procedimiento manual reproducible |
| Resultado | `passed`, `failed`, `not_run`, `blocked` o `not_applicable` con razón |
| Evidencia | Resumen observable y enlace a salida pertinente, sin secretos |
| Contexto | Runtime/configuración relevante y revisión del código validado |

En un árbol con cambios sin commit, HEAD por sí solo no identifica la revisión:
añade diff o hashes de los archivos pertinentes. No necesitas guardar toda la
salida de comandos ni crear un manifest nuevo si el repositorio ya conserva esto.
Una inspección puede validar una edición declarativa sencilla; una regla de negocio
requiere evidencia de comportamiento. Distingue prueba con fake de integración real.
"Revisión manual" no es evidencia de comportamiento para una regla, un permiso o
un cálculo; un test que no puede fallar (sin aserciones, o un publisher reactivo
creado y nunca verificado) tampoco.

## Evolución y cierre

Mantén el expediente histórico del cambio y actualiza las especificaciones vigentes
que realmente afecte. Conserva una sola fuente por contrato. No reescribas requisitos
para justificar el código: explica la discrepancia y corrige la implementación,
la prueba o una decisión autorizada según su causa.

Las decisiones resueltas por el usuario se conservan entre sesiones; no las vuelvas
a preguntar sin información que cambie su validez. Las fuentes o contratos que
cambian invalidan solo el análisis y evidencia dependientes. Un criterio excluido
necesita una razón de alcance válida, no un `not_applicable` para ocultar un fallo.
