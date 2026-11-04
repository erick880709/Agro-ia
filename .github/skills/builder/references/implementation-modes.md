# Modos de implementación

## Feature y extensión

Inspecciona el flujo comparable y sus puntos de extensión. Traduce reglas y
criterios al comportamiento requerido; genera únicamente las operaciones pedidas.
Un módulo nuevo puede ser CRUD, un cálculo, un workflow, una pantalla o un proceso
sin HTTP. Verifica colisiones y reusa datos de otros dominios conforme a sus límites.

En MVC/Active Record, código funcional o vertical slices conserva los mecanismos
idiomáticos. No agregues entidades separadas, puertos, servicios o repositorios por
una regla universal. En una arquitectura que sí exige esas separaciones, respétalas.
Evalúa el módulo de referencia; convenciones observadas no legitiman sus defectos.

Completa el cableado aplicable: DI, rutas, módulos, serialización, cliente, menú o
entrypoint. Si una interfaz se genera desde contrato, modifica su fuente canónica.
No agregues navegación ni operaciones de borrado si el requerimiento no las necesita.

## Bugfix

1. Obtén o construye un caso de reproducción acotado. Identifica comportamiento
   defectuoso, esperado y preservado; no cambies requisitos para coincidir con el bug.
2. Sigue el flujo real hasta la causa probable. Diferencia evidencia de hipótesis.
3. Cuando sea viable, crea o adapta una prueba que falle por el defecto en la versión
   inicial, no por un import roto o un entorno ausente. Conserva evidencia del fallo.
4. Aplica la corrección mínima y demuestra que el caso pasa y el comportamiento
   vecino relevante sigue funcionando. Evita refactors incidentales amplios.

Si no puedes reproducir el bug, registra qué se probó y qué dato falta. Puedes
continuar una investigación o un arreglo respaldado por otra evidencia, pero no
afirmes que reprodujiste/validaste el defecto ni declares cierre verificado sin base.

## Refactor

Explicita la mejora interna y el comportamiento que debe conservarse. Usa tests
existentes o caracterización focalizada para protegerlo antes de mover lógica.
Compara contratos, errores, efectos y orden cuando sean observables por consumidores.
Una nueva regla de negocio convierte esa parte en extensión: no la ocultes como
refactor. No midas éxito por cantidad de archivos movidos o capas añadidas.

## Integración, eventos, workers y agentes

Lee [contratos y datos](contracts-and-data.md). Identifica quién produce/consume,
credenciales por referencia, fallos, timeout y semántica de reintento. Un fake local
puede probar lógica; no demuestra compatibilidad real con un proveedor.

Para workers, prueba entrypoint/ciclo de vida y efectos, no solo el handler. Cuando
el requisito lo exija, cubre duplicados, ack/redelivery, cancelación y fallos parciales.
No introduzcas garantías de entrega que el transporte/persistencia no sostengan.

Para agentes, especifica resultados observables, límites de herramientas y puntos
de intervención humana. Prueba el control determinista y evalúa resultados variables
con criterios explícitos; no uses igualdad de texto como oráculo universal. Una
spec no autoriza acciones externas que el usuario no haya encargado.

## Frontend sin backend

Inspecciona componentes, diseño y contrato que ya consume. No crees un backend,
OpenAPI o modelo de persistencia porque Builder tenga un flujo fullstack. Respeta
estados de carga, error, vacío, permisos y accesibilidad relevantes a la interacción.
Verifica el comportamiento con las herramientas reales del proyecto y una revisión
visual cuando importe la presentación. Declara si la API se simuló o se ejercitó.
Si el proyecto declara un sistema de diseño, aplica
[UI con sistema de diseño](ui-with-design-system.md).

## Explore

Define hipótesis, experimento acotado y condiciones para detenerlo. Prefiere lectura
y prototipos locales aislados. Entrega hallazgos con evidencia, incertidumbres y
una propuesta implementable; identifica cualquier código experimental como tal.
No conviertas un spike en implementación aceptada ni agregues dependencias al
producto por probar una alternativa. Continúa a implementación solo si el mandato
ya la incluye y el experimento resolvió las decisiones necesarias.
