# Ejes de revisión

Cada sección es una pasada. Las preguntas son disparadores de búsqueda, no una
lista para copiar al reporte. Solo reporta lo que verificaste.

## A. Cumplimiento de la especificación

Revísalo primero y sin mirar la elegancia del código.

- Para cada `AC-xx`: ¿hay código que lo implementa **y** evidencia que lo
  demuestra? Marca ✅ implementado y verificado, ⚠️ parcial o no demostrado,
  ❌ ausente, — fuera de alcance de este cambio (con razón).
- Errores y escenarios negativos que la spec exige o que el dominio hace obvios
  (recurso inexistente, sin permiso, duplicado, entrada inválida).
- Comportamiento a preservar: ¿algo existente cambió sin que la spec lo pida?
  Contratos, mensajes de error, códigos HTTP, orden, side effects.
- Cableado: ¿la implementación es alcanzable desde el entrypoint real (ruta,
  bean, DI, router, listener, menú)? Un caso de uso perfecto que nadie invoca
  es un AC ❌.
- Alcance: cambios fuera del encargo (refactors oportunistas, archivos ajenos,
  formateo masivo) dificultan verificar y deben reportarse.
- Un AC ❌ es como mínimo `mayor`; `bloqueante` si es comportamiento visible
  para el usuario o un requisito de seguridad.

## B. Corrección

Pregúntate "¿qué entrada lo rompe?":

- Nulos, vacíos, límites (0, 1, máx, negativos), off-by-one, overflow, redondeo
  monetario (usa `BigDecimal`/escala explícita; nunca `double` para dinero).
- Rutas de error: excepciones tragadas, `catch` vacío, error convertido en
  éxito, fallback silencioso que oculta un invariante roto.
- Estado: mutación compartida, orden de operaciones, idempotencia ante
  reintentos, efectos parciales sin compensación.
- Concurrencia: check-then-act (TOCTOU), contadores no atómicos, caches sin
  invalidación. Ver [rendimiento y concurrencia](performance-and-concurrency.md).
- Fechas y zonas horarias, codificación, locale en parseo de números.
- Comparaciones: `==` vs `equals`, igualdad de `BigDecimal` (`compareTo`),
  enums ampliados sin `default`.

## C. Arquitectura y diseño

- ¿Sigue los patrones del repositorio o introduce uno nuevo? Si es nuevo, ¿está
  justificado por el requisito?
- Dirección de dependencias y límites de módulo. En el Scaffold de Bancolombia
  son reglas duras: ver [reglas del scaffold](clean-architecture-scaffold.md).
- ¿Lógica de una feature filtrándose a un módulo compartido/helper genérico?
- ¿Reduce complejidad o solo la reubica? Cuenta los conceptos que un lector
  debe sostener; si no baja, el refactor no mejoró nada.
- ¿Condicional nuevo injertado en un flujo ajeno? ¿Condicionales repetidos
  sobre la misma forma (falta un modelo o dispatcher)?
- Abstracciones que no se ganan su costo (interfaz con una sola implementación
  sin razón de frontera, wrapper pass-through). No exijas abstracciones que el
  proyecto no usa.
- Tipos en las fronteras: casts gratuitos, `Object`/`Map<String,Object>`
  como modelo, `Optional` como parámetro o campo.
- Archivo que crece más allá de ~1000 líneas por el cambio: sugiere
  descomponer antes de añadir.

### Remedios estructurales (nómbralos al reportar)

Reemplazar cadena de condicionales por modelo tipado o dispatcher · colapsar
ramas duplicadas · separar orquestación de lógica de negocio · mover lógica de
feature a su módulo dueño · reusar el helper canónico · hacer explícita la
frontera de tipos · eliminar wrapper pass-through · extraer helper o dividir
archivo. Prefiere el remedio que elimina piezas.

## D. Seguridad

Ver [seguridad](security.md). Siempre en rigor reforzado.

## E. Rendimiento

Ver [rendimiento y concurrencia](performance-and-concurrency.md). Cuantifica
cuando puedas ("una consulta por elemento: 200 consultas para una página de 200").

## F. Pruebas

Ver [verificación](verification.md). La pregunta clave: si invierto la
condición nueva, ¿algún test se pone rojo?

## G. Mantenibilidad

- Nombres consistentes con el proyecto y el dominio; nada de `data`, `temp`,
  `result2`, `manager` sin contexto.
- Duplicación de lógica existente: busca el helper/utilidad canónica antes de
  aceptar uno nuevo.
- Código muerto, imports sin uso, `// removed`, flags temporales, `TODO` sin
  ticket. Si el cambio deja código huérfano, lístalo y recomienda eliminarlo
  (no lo elimines tú).
- Comentarios que explican el *qué* obvio en vez del *por qué* no obvio.
- Logs: nivel adecuado, sin datos sensibles, con contexto para operar
  (IDs de correlación, no payloads completos).
- **Dependencias nuevas o actualizadas:** ¿lo resuelve el stack actual? ¿está
  mantenida, con licencia compatible y sin CVE conocidas? En upgrades: changelog
  leído, una dependencia por cambio, diff del lockfile revisado, suite verde
  antes y después. Un "bump deps" masivo sin esto es `mayor`.

## Qué no revisar a mano

Formato, orden de imports y reglas que un linter/formatter ya aplica. Si el
proyecto no tiene esa automatización y hay ruido de formato, es un único
hallazgo `nit` sugiriéndola, no veinte.
