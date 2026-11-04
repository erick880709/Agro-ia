# Interoperabilidad con expedientes SDD

Usa esta guía solo cuando el repositorio ya tenga OpenSpec o Spec Kit. Sus artefactos
son fuentes del proyecto; Builder no instala la herramienta, crea un expediente
paralelo ni ejecuta transiciones de cierre sin que el encargo las incluya.

## OpenSpec

Identifica la carpeta del cambio activo y su configuración antes de editar. Usa la
propuesta como intención y alcance, las delta specs como comportamiento que cambia,
el diseño como decisiones técnicas y las tareas como plan. Conserva los IDs y la
semántica `ADDED`, `MODIFIED` y `REMOVED`; una casilla no sustituye evidencia.

Durante implementación actualiza el artefacto cuya premisa cambió y reconcilia los
dependientes. Ejecuta la validación local disponible para el cambio. `sync` modifica
specs vigentes y `archive` cierra/mueve el expediente: ejecútalos solo si forman
parte de la entrega autorizada y sus precondiciones se cumplen. Reportar que el
código terminó no equivale a haber sincronizado o archivado.

## Spec Kit

Trata `spec.md` como comportamiento del cambio, el plan como enfoque y `tasks.md`
como descomposición. Lee la constitución y otros guardrails vigentes como
restricciones, contrastándolos con fuentes reales del repositorio. Preserva IDs y
carpeta de feature; no documentes retrospectivamente todo el sistema para resolver
un cambio acotado.

Antes de implementar, comprueba contradicciones materiales entre spec, plan y
tareas. Después compara implementación y evidencia con esos artefactos y registra
gaps concretos. Si el proyecto usa comandos de análisis o convergencia, ejecútalos
cuando correspondan a la entrega; tareas añadidas por convergencia vuelven a ser
trabajo pendiente, no una razón para declarar cierre prematuro.

## Conflictos y cierre

Si código, contrato y expediente discrepan, aplica las reglas de ownership y fuentes
de Builder. No edites la spec para legitimar una implementación. Al cerrar, actualiza
solo la fuente vigente que corresponda al modelo de persistencia elegido por el
proyecto: histórico, contrato vivo o reconciliación bidireccional. Registra comando,
resultado y revisión; nunca infieras una transición porque una carpeta exista.
